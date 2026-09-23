"""Materialize and verify lifecycle-owned Codex static templates."""

from __future__ import annotations

import hashlib
import os
import stat
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import urlparse


SEED_MARKER = "# pennix-workflow-lifecycle:seed-config"
ROOT_BEGIN = "# pennix-workflow-lifecycle:install-root:begin"
ROOT_END = "# pennix-workflow-lifecycle:install-root:end"
FEATURE_BEGIN = "# pennix-workflow-lifecycle:install-features:begin"
FEATURE_END = "# pennix-workflow-lifecycle:install-features:end"
AGENTS_BLOCKS = (
    (
        "pennix-workflow-lifecycle",
        "<!-- pennix-workflow-lifecycle:begin -->",
        "<!-- pennix-workflow-lifecycle:end -->",
    ),
    (
        "pennix-fastctx",
        "<!-- pennix-fastctx:begin -->",
        "<!-- pennix-fastctx:end -->",
    ),
)
TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "templates"


class StaticError(RuntimeError):
    """Raised when a lifecycle static file is unsafe to change."""


def assert_no_symlink_ancestor(path: Path) -> None:
    """Reject a static target reached through any symbolic link."""

    current = path.absolute()
    while True:
        try:
            if current.is_symlink():
                raise StaticError(f"refusing symbolic-link static path: {current}")
        except OSError as error:
            raise StaticError(f"cannot safely inspect static path: {current}") from error
        if current == current.parent:
            return
        current = current.parent


def read(path: Path) -> str:
    assert_no_symlink_ancestor(path)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise StaticError(f"cannot safely read static file: {path}") from error


def auth_state(codex_home: Path) -> str:
    """Return redacted native-auth readiness without reading credential values."""
    auth = codex_home / "auth.json"
    try:
        assert_no_symlink_ancestor(auth)
        metadata = auth.lstat()
    except FileNotFoundError:
        return "not-configured"
    except OSError:
        return "unknown"
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o077:
        return "blocked"
    try:
        if metadata.st_size == 0:
            return "not-configured"
        auth.read_bytes()
    except OSError:
        return "unknown"
    return "ready"


def template(name: str) -> str:
    path = TEMPLATE_ROOT / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise StaticError(f"lifecycle template is unavailable: {path}") from error


def _section(contents: str, begin: str, end: str) -> str:
    if contents.count(begin) != 1 or contents.count(end) != 1:
        raise StaticError(f"config template has invalid section markers: {begin}")
    start = contents.index(begin) + len(begin)
    finish = contents.index(end, start)
    return contents[start:finish].strip("\n")


def install_config_sections() -> tuple[str, str]:
    contents = template("config.toml.install")
    return (
        _section(contents, ROOT_BEGIN, ROOT_END),
        _section(contents, FEATURE_BEGIN, FEATURE_END),
    )


def _replace_section(contents: str, begin: str, end: str, replacement: str) -> str:
    _section(contents, begin, end)
    start = contents.index(begin) + len(begin)
    finish = contents.index(end, start)
    return contents[:start] + "\n" + replacement + "\n" + contents[finish:]


def _base_url(contents: str) -> str:
    try:
        provider = tomllib.loads(contents)["model_providers"]["OpenAI"]
        value = provider["base_url"]
    except (KeyError, TypeError, tomllib.TOMLDecodeError) as error:
        raise StaticError("lifecycle config has no valid OpenAI base_url") from error
    if not isinstance(value, str):
        raise StaticError("lifecycle config base_url is not a string")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or any(ord(char) < 32 for char in value):
        raise StaticError("lifecycle config base_url is invalid")
    return value


def _toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def seed_config(base_url: str) -> str:
    return template("config.toml.seed").replace("{{PENNIX_BASE_URL}}", _toml_string(base_url))


def install_config(base_url: str) -> str:
    root, features = install_config_sections()
    contents = seed_config(base_url)
    contents = _replace_section(contents, ROOT_BEGIN, ROOT_END, root)
    return _replace_section(contents, FEATURE_BEGIN, FEATURE_END, features)


def config_state(contents: str) -> str:
    if not contents:
        return "absent"
    if contents.count(SEED_MARKER) != 1:
        return "drifted"
    try:
        base_url = _base_url(contents)
    except StaticError:
        return "drifted"
    if contents == seed_config(base_url):
        return "seeded"
    try:
        installed = install_config(base_url)
    except StaticError:
        return "drifted"
    if contents == installed:
        return "current"
    return "drifted"


def apply_config(path: Path) -> tuple[str, str]:
    before = read(path)
    state_name = config_state(before)
    if state_name == "current":
        return before, before
    if state_name != "seeded":
        raise StaticError(f"refusing {state_name} lifecycle config: {path}")
    after = install_config(_base_url(before))
    write(path, after)
    if config_state(read(path)) != "current":
        raise StaticError(f"lifecycle config verification failed: {path}")
    return before, after


def remove_config_sections(path: Path) -> tuple[str, str]:
    before = read(path)
    state_name = config_state(before)
    if state_name == "seeded":
        return before, before
    if state_name != "current":
        raise StaticError(f"refusing {state_name} lifecycle config: {path}")
    after = seed_config(_base_url(before))
    write(path, after)
    if config_state(read(path)) != "seeded":
        raise StaticError(f"lifecycle config uninstall verification failed: {path}")
    return before, after


def template_state(path: Path, template_name: str = "AGENTS.md.install") -> str:
    contents = read(path)
    if not contents:
        return "absent" if not path.exists() else "drifted"
    expected = template(template_name)
    present = 0
    for name, begin, end in AGENTS_BLOCKS:
        observed = _agent_block(contents, begin, end)
        expected_block = _agent_block(expected, begin, end)
        if observed is None:
            continue
        present += 1
        if observed != expected_block:
            raise StaticError(f"lifecycle AGENTS block is drifted: {name}")
    return "current" if present == len(AGENTS_BLOCKS) else "partial"


def _agent_block(contents: str, begin: str, end: str) -> str | None:
    begin_count = contents.count(begin)
    end_count = contents.count(end)
    if begin_count != end_count or begin_count > 1:
        raise StaticError(f"lifecycle AGENTS markers are invalid: {begin}")
    if begin_count == 0:
        return None
    start = contents.index(begin)
    try:
        finish = contents.index(end, start) + len(end)
    except ValueError as error:
        raise StaticError(f"lifecycle AGENTS markers are out of order: {begin}") from error
    if finish < start:
        raise StaticError(f"lifecycle AGENTS markers are out of order: {begin}")
    return contents[start:finish]


def _agent_missing_blocks(contents: str, expected: str) -> list[str]:
    missing: list[str] = []
    for name, begin, end in AGENTS_BLOCKS:
        observed = _agent_block(contents, begin, end)
        if observed is None:
            missing.append(_agent_block(expected, begin, end) or "")
    return [block for block in missing if block]


def _append_agent_blocks(contents: str, blocks: list[str]) -> str:
    after = contents
    for block in blocks:
        if after and not after.endswith("\n"):
            after += "\n"
        if after and not after.endswith("\n\n"):
            after += "\n"
        after += block + "\n"
    return after


def remove_template(path: Path, template_name: str = "AGENTS.md.install") -> tuple[str, str]:
    before = read(path)
    state_name = template_state(path, template_name)
    if state_name in {"absent", "partial"} and not any(
        _agent_block(before, begin, end) is not None for _, begin, end in AGENTS_BLOCKS
    ):
        return before, before
    if state_name not in {"current", "partial"}:
        raise StaticError(f"refusing {state_name} lifecycle template: {path}")
    after = before
    for _, begin, end in AGENTS_BLOCKS:
        block = _agent_block(after, begin, end)
        if block is None:
            continue
        start = after.index(block)
        finish = start + len(block)
        if after[finish : finish + 2] == "\n\n":
            finish += 2
        elif after[finish : finish + 1] == "\n":
            finish += 1
        after = after[:start] + after[finish:]
    write(path, after)
    return before, after


def apply_template(path: Path, template_name: str = "AGENTS.md.install") -> tuple[str, str]:
    before = read(path)
    state_name = template_state(path, template_name)
    if state_name == "current":
        return before, before
    expected = template(template_name)
    if state_name == "partial":
        after = _append_agent_blocks(before, _agent_missing_blocks(before, expected))
    elif state_name == "absent":
        after = expected
    else:
        raise StaticError(f"refusing {state_name} lifecycle template: {path}")
    write(path, after)
    if template_state(path, template_name) != "current":
        raise StaticError(f"lifecycle template verification failed: {path}")
    return before, after


def digest(contents: str) -> str:
    return hashlib.sha256(contents.encode("utf-8")).hexdigest()


def write(path: Path, contents: str) -> None:
    assert_no_symlink_ancestor(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode if path.exists() else 0o600
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(contents)
    os.chmod(temporary, mode & 0o777)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
