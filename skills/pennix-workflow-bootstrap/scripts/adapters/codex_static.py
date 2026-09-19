"""Materialize and verify the bootstrap-owned Codex static templates."""

from __future__ import annotations

import hashlib
import os
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import urlparse


SEED_MARKER = "# pennix-workflow-bootstrap:seed-config"
ROOT_BEGIN = "# pennix-workflow-bootstrap:install-root:begin"
ROOT_END = "# pennix-workflow-bootstrap:install-root:end"
FEATURE_BEGIN = "# pennix-workflow-bootstrap:install-features:begin"
FEATURE_END = "# pennix-workflow-bootstrap:install-features:end"
TEMPLATE_ROOT = Path(__file__).resolve().parents[2] / "templates"


class StaticError(RuntimeError):
    """Raised when a bootstrap static file is unsafe to change."""


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


def template(name: str) -> str:
    path = TEMPLATE_ROOT / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise StaticError(f"bootstrap template is unavailable: {path}") from error


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
        raise StaticError("bootstrap config has no valid OpenAI base_url") from error
    if not isinstance(value, str):
        raise StaticError("bootstrap config base_url is not a string")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or any(ord(char) < 32 for char in value):
        raise StaticError("bootstrap config base_url is invalid")
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
        raise StaticError(f"refusing {state_name} bootstrap config: {path}")
    after = install_config(_base_url(before))
    write(path, after)
    if config_state(read(path)) != "current":
        raise StaticError(f"bootstrap config verification failed: {path}")
    return before, after


def template_state(path: Path, template_name: str = "AGENTS.md.install") -> str:
    contents = read(path)
    if not contents:
        return "absent" if not path.exists() else "drifted"
    return "current" if contents == template(template_name) else "drifted"


def apply_template(path: Path, template_name: str = "AGENTS.md.install") -> tuple[str, str]:
    before = read(path)
    state_name = template_state(path, template_name)
    if state_name == "current":
        return before, before
    if state_name != "absent":
        raise StaticError(f"refusing {state_name} bootstrap template: {path}")
    after = template(template_name)
    write(path, after)
    if template_state(path, template_name) != "current":
        raise StaticError(f"bootstrap template verification failed: {path}")
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
