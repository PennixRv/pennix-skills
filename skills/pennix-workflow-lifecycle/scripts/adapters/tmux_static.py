"""Manage the Pennix-owned tmux baseline block and its private receipt."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from . import codex_static


BEGIN = "# >>> pennix-workflow-lifecycle:tmux-config:v1 >>>"
END = "# <<< pennix-workflow-lifecycle:tmux-config:v1 <<<"
TEMPLATE_NAME = "tmux.conf.install"
RECEIPT_SCHEMA = 1
RECEIPT_RELATIVE = Path("pennix-workflow-lifecycle") / "static-assets" / "tmux-config.json"
REVISION_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class TmuxStaticError(RuntimeError):
    """Raised when tmux static state is unsafe to inspect or change."""


def target_path(home_directory: Path | None = None) -> Path:
    return (home_directory or Path.home()) / ".tmux.conf"


def receipt_path(codex_home: Path) -> Path:
    return codex_home / RECEIPT_RELATIVE


def _assert_regular(path: Path, mode: int | None = None) -> None:
    try:
        codex_static.assert_no_symlink_ancestor(path)
    except codex_static.StaticError as error:
        raise TmuxStaticError(str(error)) from error
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise TmuxStaticError(f"cannot safely inspect tmux path: {path}") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise TmuxStaticError(f"refusing unsafe tmux path: {path}")
    if mode is not None and metadata.st_mode & 0o777 != mode:
        raise TmuxStaticError(f"refusing unsafe tmux receipt mode: {path}")


def _read_target(path: Path) -> bytes:
    _assert_regular(path)
    if not path.exists():
        return b""
    try:
        return path.read_bytes()
    except (OSError, UnicodeDecodeError) as error:
        raise TmuxStaticError(f"cannot safely read tmux config: {path}") from error


def _read_receipt(path: Path) -> tuple[str, dict[str, Any] | None]:
    try:
        _assert_regular(path, 0o600)
    except TmuxStaticError:
        return "blocked", None
    if not path.exists():
        return "missing", None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "invalid", None
    if not isinstance(value, dict):
        return "invalid", None
    required = {"schema", "asset", "target", "template_revision", "block_digest"}
    if set(value) != required:
        return "invalid", None
    if (
        value["schema"] != RECEIPT_SCHEMA
        or value["asset"] != "tmux-config"
        or value["target"] != "HOME/.tmux.conf"
        or not isinstance(value["template_revision"], str)
        or not REVISION_RE.fullmatch(value["template_revision"])
        or not isinstance(value["block_digest"], str)
        or not DIGEST_RE.fullmatch(value["block_digest"])
    ):
        return "invalid", None
    return "match", value


def _template_body() -> str:
    try:
        body = codex_static.template(TEMPLATE_NAME).replace("\r\n", "\n").strip("\n")
    except codex_static.StaticError as error:
        raise TmuxStaticError(str(error)) from error
    if not body or any(not line.strip() for line in body.split("\n")):
        raise TmuxStaticError("tmux lifecycle template is empty or malformed")
    return body


def _without_digest(revision: str, body: str) -> str:
    return "\n".join((BEGIN, f"# template-revision: {revision}", body, END))


def _block(revision: str, body: str) -> tuple[str, str]:
    without_digest = _without_digest(revision, body)
    digest = "sha256:" + hashlib.sha256(without_digest.encode("utf-8")).hexdigest()
    return "\n".join((BEGIN, f"# template-revision: {revision}", f"# block-digest: {digest}", body, END)), digest


def _extract_block(contents: bytes) -> tuple[str, int, int] | None:
    begin = BEGIN.encode("utf-8")
    end = END.encode("utf-8")
    begin_count = contents.count(begin)
    end_count = contents.count(end)
    if begin_count == 0 and end_count == 0:
        return None
    if begin_count != 1 or end_count != 1:
        raise TmuxStaticError("tmux managed block markers are duplicated")
    start = contents.index(begin)
    finish = contents.index(end, start)
    if finish < start or (start and contents[start - 1:start] != b"\n"):
        raise TmuxStaticError("tmux managed block does not start on a line")
    after = finish + len(end)
    if after < len(contents) and contents[after:after + 1] not in {b"\n", b"\r"}:
        raise TmuxStaticError("tmux managed block does not end on a line")
    try:
        block = contents[start:after].decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as error:
        raise TmuxStaticError("tmux config is not valid UTF-8") from error
    return block, start, after


def _parse_block(block: str) -> tuple[str, str, str]:
    lines = block.split("\n")
    if len(lines) < 5 or lines[0] != BEGIN or lines[-1] != END:
        raise TmuxStaticError("tmux managed block is incomplete")
    revision_prefix = "# template-revision: "
    digest_prefix = "# block-digest: "
    if not lines[1].startswith(revision_prefix) or not lines[2].startswith(digest_prefix):
        raise TmuxStaticError("tmux managed block metadata is missing")
    revision = lines[1][len(revision_prefix):]
    digest = lines[2][len(digest_prefix):]
    if not REVISION_RE.fullmatch(revision) or not DIGEST_RE.fullmatch(digest):
        raise TmuxStaticError("tmux managed block metadata is invalid")
    body = "\n".join(lines[3:-1])
    calculated = "sha256:" + hashlib.sha256(_without_digest(revision, body).encode("utf-8")).hexdigest()
    if calculated != digest:
        raise TmuxStaticError("tmux managed block digest does not match")
    return revision, digest, body


def _receipt_value(revision: str, digest: str) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "asset": "tmux-config",
        "target": "HOME/.tmux.conf",
        "template_revision": revision,
        "block_digest": digest,
    }


def _write_receipt(path: Path, value: dict[str, Any]) -> None:
    try:
        codex_static.assert_no_symlink_ancestor(path)
    except codex_static.StaticError as error:
        raise TmuxStaticError(str(error)) from error
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise TmuxStaticError("tmux receipt directory is unsafe")
    os.chmod(path.parent, 0o700)
    _assert_regular(path)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _remove_receipt(path: Path) -> None:
    state, _ = _read_receipt(path)
    if state == "missing":
        return
    if state != "match":
        raise TmuxStaticError("refusing to remove an unsafe tmux receipt")
    path.unlink()


def _dependency_available() -> None:
    if not shutil.which("tmux"):
        raise TmuxStaticError("tmux dependency is unavailable")


def inspect(codex_home: Path, home_directory: Path | None, revision: str) -> dict[str, Any]:
    _dependency_available()
    path = target_path(home_directory)
    contents = _read_target(path)
    block_info = _extract_block(contents)
    receipt_state, receipt = _read_receipt(receipt_path(codex_home))
    if block_info is None:
        if receipt_state == "missing":
            return {"state": "absent", "target": str(path), "receipt": receipt_state}
        return {"state": "blocked", "target": str(path), "receipt": receipt_state, "reason": "orphaned receipt"}
    try:
        block, start, finish = block_info
        block_revision, block_digest, body = _parse_block(block)
    except TmuxStaticError as error:
        return {"state": "drifted", "target": str(path), "receipt": receipt_state, "reason": str(error)}
    if receipt_state != "match" or receipt is None:
        return {"state": "blocked", "target": str(path), "receipt": receipt_state, "reason": "receipt is unavailable"}
    if receipt["template_revision"] != block_revision or receipt["block_digest"] != block_digest:
        return {"state": "drifted", "target": str(path), "receipt": receipt_state, "reason": "receipt does not match block"}
    body_now = _template_body()
    expected_block, expected_digest = _block(revision, body_now)
    actual_block = contents[start:finish].decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if block_revision == revision and actual_block == expected_block and block_digest == expected_digest:
        state = "current"
    else:
        state = "upgrade-available"
    return {
        "state": state,
        "target": str(path),
        "receipt": receipt_state,
        "template_revision": block_revision,
        "block_digest": block_digest,
    }


def _append_block(contents: bytes, block: str) -> bytes:
    suffix = b"\n" if contents and not contents.endswith((b"\n", b"\r")) else b""
    return contents + suffix + block.encode("utf-8") + b"\n"


def _replace_block(contents: bytes, block_info: tuple[str, int, int], block: str) -> bytes:
    _, start, finish = block_info
    return contents[:start] + block.encode("utf-8") + contents[finish:]


def _remove_block(contents: bytes, block_info: tuple[str, int, int]) -> bytes:
    _, start, finish = block_info
    if contents[finish:finish + 2] == b"\r\n":
        finish += 2
    elif contents[finish:finish + 1] in {b"\n", b"\r"}:
        finish += 1
    return contents[:start] + contents[finish:]


def _write_target(path: Path, contents: bytes) -> None:
    try:
        codex_static.assert_no_symlink_ancestor(path)
    except codex_static.StaticError as error:
        raise TmuxStaticError(str(error)) from error
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode if path.exists() else 0o600
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode & 0o777)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def operate(codex_home: Path, home_directory: Path | None, revision: str, operation: str) -> str:
    _dependency_available()
    path = target_path(home_directory)
    contents = _read_target(path)
    block_info = _extract_block(contents)
    receipt_file = receipt_path(codex_home)
    current = inspect(codex_home, home_directory, revision)
    state = current["state"]
    if operation == "verify":
        if state == "current":
            return "no-op"
        raise TmuxStaticError(f"tmux config is {state}")
    if operation in {"install", "configure"}:
        if state == "current":
            return "no-op"
        if state == "absent":
            body = _template_body()
            block, digest = _block(revision, body)
            _write_target(path, _append_block(contents, block))
            _write_receipt(receipt_file, _receipt_value(revision, digest))
            return "changed"
        if state == "upgrade-available":
            raise TmuxStaticError("tmux config upgrade is available; use upgrade")
        raise TmuxStaticError(f"refusing {state} tmux config")
    if operation == "upgrade":
        if state == "current":
            return "no-op"
        if state != "upgrade-available" or block_info is None:
            reason = current.get("reason")
            raise TmuxStaticError(f"refusing {state} tmux config upgrade" + (f": {reason}" if reason else ""))
        body = _template_body()
        block, digest = _block(revision, body)
        _write_target(path, _replace_block(contents, block_info, block))
        _write_receipt(receipt_file, _receipt_value(revision, digest))
        return "changed"
    if operation == "uninstall":
        if state == "absent":
            return "no-op"
        if state == "blocked" and current.get("reason") == "orphaned receipt" and block_info is None:
            _remove_receipt(receipt_file)
            return "changed"
        if state not in {"current", "upgrade-available"} or block_info is None:
            reason = current.get("reason")
            raise TmuxStaticError(f"refusing {state} tmux config uninstall" + (f": {reason}" if reason else ""))
        _write_target(path, _remove_block(contents, block_info))
        _remove_receipt(receipt_file)
        return "changed"
    raise TmuxStaticError(f"unsupported tmux static operation: {operation}")
