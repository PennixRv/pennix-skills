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
LEGACY_AGENTS_DIGESTS = frozenset({
    "96307dbfbc9effe504748080008f8b250e4ae94b5a526325d58b00a8d7e49202",
})
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
        with auth.open("rb"):
            pass
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


def _contains_values(observed: object, expected: object) -> bool:
    if not isinstance(observed, dict) or not isinstance(expected, dict):
        return observed == expected
    return all(key in observed and _contains_values(observed[key], value) for key, value in expected.items())


def config_state(contents: str) -> str:
    if not contents:
        return "absent"
    try:
        base_url = _base_url(contents)
    except StaticError:
        return "drifted"
    if contents.count(SEED_MARKER) != 1:
        try:
            observed = tomllib.loads(contents)
            expected = tomllib.loads(install_config(base_url))
        except (StaticError, tomllib.TOMLDecodeError):
            return "drifted"
        return "compatible" if _contains_values(observed, expected) else "drifted"
    if contents == seed_config(base_url):
        return "seeded"
    try:
        installed = install_config(base_url)
    except StaticError:
        return "drifted"
    if contents == installed:
        return "current"
    try:
        observed = tomllib.loads(contents)
        expected = tomllib.loads(installed)
    except tomllib.TOMLDecodeError:
        return "drifted"
    if _contains_values(observed, expected):
        return "compatible"
    return "drifted"


def apply_config(path: Path) -> tuple[str, str]:
    before = read(path)
    state_name = config_state(before)
    if state_name in {"current", "compatible"}:
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
    if state_name in {"seeded", "compatible"}:
        return before, before
    if state_name != "current":
        raise StaticError(f"refusing {state_name} lifecycle config: {path}")
    after = seed_config(_base_url(before))
    write(path, after)
    if config_state(read(path)) != "seeded":
        raise StaticError(f"lifecycle config uninstall verification failed: {path}")
    return before, after


def template_state(path: Path, template_name: str = "AGENTS.md.install") -> str:
    assert_no_symlink_ancestor(path)
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return "absent"
    except OSError as error:
        raise StaticError(f"cannot safely inspect lifecycle template: {path}") from error
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o022:
        raise StaticError(f"unsafe lifecycle template permissions: {path}")
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise StaticError(f"unsafe lifecycle template owner: {path}")
    try:
        contents = path.read_bytes()
        contents.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise StaticError(f"cannot safely read lifecycle template: {path}") from error
    if contents == template(template_name).encode("utf-8"):
        return "current"
    if template_name == "AGENTS.md.install" and hashlib.sha256(contents).hexdigest() in LEGACY_AGENTS_DIGESTS:
        return "legacy"
    return "drifted"


def effective_agents(path: Path) -> dict[str, str]:
    """Report this instruction directory's effective source without exposing text."""
    for candidate in (path.with_name("AGENTS.override.md"), path):
        try:
            contents = read(candidate)
        except StaticError:
            return {"status": "unknown", "path": str(candidate)}
        if contents.strip():
            return {
                "status": "active" if candidate == path else "shadowed",
                "path": str(candidate),
            }
    return {"status": "absent", "path": str(path)}


def remove_template(path: Path, template_name: str = "AGENTS.md.install") -> tuple[str, str]:
    state_name = template_state(path, template_name)
    if state_name == "absent":
        return "", ""
    if state_name not in {"current", "legacy"}:
        raise StaticError(f"refusing {state_name} lifecycle template: {path}")
    before = read(path)
    path.unlink()
    return before, ""


def apply_template(path: Path, template_name: str = "AGENTS.md.install") -> tuple[str, str]:
    state_name = template_state(path, template_name)
    before = read(path)
    if state_name == "current":
        return before, before
    if state_name not in {"absent", "legacy"}:
        raise StaticError(f"refusing {state_name} lifecycle template: {path}")
    after = template(template_name)
    if not after.strip():
        raise StaticError("lifecycle template candidate is empty")
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
