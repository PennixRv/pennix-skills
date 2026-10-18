#!/usr/bin/env python3
"""Own the local Hikari connection record without contacting the service."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


class ConnectionError(RuntimeError):
    """A local Hikari connection cannot be safely inspected or changed."""


TOKEN = re.compile(r"^th-[A-Za-z0-9]{4}-(?:[A-Za-z0-9]{12}|[A-Za-z0-9]{24})$")


def config_path() -> Path:
    configured = os.environ.get("TAVILY_HIKARI_CONFIG_FILE")
    if configured:
        path = Path(configured)
    else:
        directory = os.environ.get("TAVILY_HIKARI_CONFIG_DIR")
        if directory:
            path = Path(directory) / "config.json"
        else:
            base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
            path = base / "tavily-hikari-cli" / "config.json"
    if not path.is_absolute():
        raise ConnectionError("Hikari configuration path must be absolute")
    return path


def receipt_path(path: Path | None = None) -> Path:
    path = config_path() if path is None else path
    return path.with_name(f".{path.name}.pennix-lifecycle.json")


def _environment_override() -> dict[str, object] | None:
    if "TAVILY_HIKARI_BASE_URL" in os.environ or "TAVILY_HIKARI_TOKEN" in os.environ:
        return {
            "state": "environment-override",
            "owned": False,
            "detail": "Hikari environment overrides hide the lifecycle-owned file",
        }
    return None


def _assert_parent(path: Path, create: bool = False) -> None:
    parent = path.parent
    if create:
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        current = parent
        while current != current.parent:
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise ConnectionError("unsafe Hikari configuration directory")
            current = current.parent
        info = parent.lstat()
    except FileNotFoundError:
        if create:
            raise ConnectionError("Hikari configuration directory could not be created") from None
        raise
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise ConnectionError("unsafe Hikari configuration directory")


def _read_private(path: Path, *, missing_ok: bool = True) -> bytes | None:
    try:
        _assert_parent(path)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise ConnectionError("Hikari configuration directory is missing") from None
    try:
        info = path.lstat()
    except FileNotFoundError:
        if missing_ok:
            return None
        raise ConnectionError("Hikari file is missing") from None
    if (stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600
            or info.st_size > 65536):
        raise ConnectionError("unsafe Hikari configuration file")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        current = os.fstat(descriptor)
        if (not stat.S_ISREG(current.st_mode) or current.st_uid != os.getuid()
                or stat.S_IMODE(current.st_mode) != 0o600 or current.st_size > 65536):
            raise ConnectionError("unsafe Hikari configuration file")
        with os.fdopen(descriptor, "rb") as handle:
            descriptor = -1
            content = handle.read(65537)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > 65536:
        raise ConnectionError("oversized Hikari configuration file")
    return content


def _write_private(path: Path, content: bytes) -> None:
    _assert_parent(path, create=True)
    if path.is_symlink():
        raise ConnectionError("unsafe Hikari configuration file")
    if path.exists():
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise ConnectionError("unsafe Hikari configuration file")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary).chmod(0o600)
        os.replace(temporary, path)
        path.chmod(0o600)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _restore(path: Path, content: bytes | None) -> None:
    if content is None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return
    _write_private(path, content)


def _normalise_url(value: object) -> str:
    if not isinstance(value, str) or not value or any(ord(char) <= 32 or ord(char) > 126 for char in value):
        raise ConnectionError("Hikari base URL is invalid")
    value = value.rstrip("/")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ConnectionError("Hikari base URL is invalid") from None
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or parsed.path not in {"", "/"}
            or port == 0):
        raise ConnectionError("Hikari base URL is invalid")
    return value


def _validate_config(value: object) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"baseUrl", "token"}:
        raise ConnectionError("Hikari configuration is invalid")
    base_url = _normalise_url(value["baseUrl"])
    token = value["token"]
    if not isinstance(token, str) or not TOKEN.fullmatch(token):
        raise ConnectionError("Hikari configuration is invalid")
    return {"baseUrl": base_url, "token": token}


def _read_config(path: Path) -> tuple[dict[str, str], bytes]:
    content = _read_private(path, missing_ok=False)
    try:
        value = json.loads(content)
    except (TypeError, ValueError, UnicodeError) as error:
        raise ConnectionError("Hikari configuration is invalid") from error
    return _validate_config(value), content


def _read_receipt(path: Path) -> tuple[dict[str, str], bytes] | None:
    content = _read_private(path)
    if content is None:
        return None
    try:
        value = json.loads(content)
    except (TypeError, ValueError, UnicodeError) as error:
        raise ConnectionError("Hikari lifecycle receipt is invalid") from error
    if (not isinstance(value, dict) or set(value) != {"schema", "owner", "config_digest", "desired_digest"}
            or value.get("schema") != 1 or value.get("owner") != "pennix-tavily-search"
            or any(not isinstance(value.get(key), str) or not re.fullmatch(r"[0-9a-f]{64}", value[key])
                   for key in ("config_digest", "desired_digest"))):
        raise ConnectionError("Hikari lifecycle receipt is invalid")
    return value, content


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def desired_digest(target: str, values: dict[str, str], secrets: dict[str, str]) -> str:
    canonical = json.dumps(
        {"target": target, "values": values, "secrets": secrets},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _digest(canonical)


def inspect(input_value: dict | None = None) -> dict[str, object]:
    override = _environment_override()
    if override:
        return override
    path = config_path()
    receipt = receipt_path(path)
    try:
        config_content = _read_private(path)
        receipt_value = _read_receipt(receipt)
    except (ConnectionError, OSError):
        return {"state": "invalid", "owned": False, "detail": "Hikari local connection is invalid"}
    if config_content is None and receipt_value is None:
        return {"state": "absent", "owned": False, "detail": "Hikari local connection is absent"}
    if config_content is None:
        return {"state": "external", "owned": False, "detail": "Hikari local connection is not lifecycle-owned"}
    try:
        existing = _validate_config(json.loads(config_content))
    except (ConnectionError, ValueError, UnicodeError):
        return {"state": "invalid", "owned": False, "detail": "Hikari local connection is invalid"}
    if receipt_value is None:
        matches = (input_value or {}).get("desired_digest") == desired_digest(
            "hikari", {"base_url": existing["baseUrl"]}, {"token": existing["token"]})
        return {"state": "adoptable" if matches else "external", "owned": False,
                "detail": "Hikari local connection is not lifecycle-owned"}
    receipt_data = receipt_value[0]
    if receipt_data["config_digest"] != _digest(config_content):
        return {"state": "external", "owned": False, "detail": "Hikari local connection drifted outside lifecycle ownership"}
    desired = (input_value or {}).get("desired_digest")
    if desired is not None and desired != receipt_data["desired_digest"]:
        return {"state": "drifted", "owned": True, "detail": "Hikari desired connection differs from lifecycle receipt"}
    return {"state": "current", "owned": True, "detail": "Hikari local connection matches lifecycle receipt"}


def configure(input_value: dict) -> dict[str, object]:
    if (input_value.get("target") != "hikari" or not isinstance(input_value.get("values"), dict)
            or not isinstance(input_value.get("secrets"), dict)
            or not isinstance(input_value.get("desired_digest"), str)):
        raise ConnectionError("Hikari lifecycle input is invalid")
    raw_base_url = input_value["values"].get("base_url")
    base_url = _normalise_url(raw_base_url)
    token = input_value["secrets"].get("token")
    if not isinstance(token, str) or not TOKEN.fullmatch(token):
        raise ConnectionError("Hikari lifecycle input is invalid")
    expected_digest = desired_digest("hikari", {"base_url": raw_base_url}, {"token": token})
    if input_value["desired_digest"] != expected_digest:
        raise ConnectionError("Hikari lifecycle digest is invalid")
    before = inspect(input_value)
    if before["state"] == "current":
        return before
    if before["state"] in {"external", "invalid", "environment-override"} or before["state"] == "adoptable" and input_value.get("adopt_existing") is not True:
        raise ConnectionError(f"Hikari owner state {before['state']} cannot be taken over")
    path = config_path()
    receipt = receipt_path(path)
    before_config = _read_private(path)
    before_receipt = _read_private(receipt)
    config = json.dumps({"baseUrl": base_url, "token": token}, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    if before["state"] == "adoptable":
        config = before_config
    receipt_value = {
        "schema": 1,
        "owner": "pennix-tavily-search",
        "config_digest": _digest(config),
        "desired_digest": input_value["desired_digest"],
    }
    receipt_content = json.dumps(receipt_value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    try:
        _write_private(path, config)
        _write_private(receipt, receipt_content)
    except BaseException as error:
        try:
            _restore(path, before_config)
            _restore(receipt, before_receipt)
        except BaseException as rollback:
            raise ConnectionError("Hikari lifecycle write failed and rollback failed") from rollback
        raise ConnectionError("Hikari lifecycle write failed and was rolled back") from error
    return {"state": "current", "owned": True, "detail": "Hikari local connection configured without service handshake"}


def unconfigure() -> dict[str, object]:
    before = inspect()
    if before["state"] == "absent":
        return {"state": "absent", "owned": False, "detail": "Hikari local connection is absent"}
    if before["state"] != "current" or not before["owned"]:
        raise ConnectionError("Hikari lifecycle ownership is missing or drifted")
    path = config_path()
    receipt = receipt_path(path)
    before_config = _read_private(path, missing_ok=False)
    before_receipt = _read_private(receipt, missing_ok=False)
    try:
        path.unlink()
        receipt.unlink()
    except BaseException as error:
        try:
            _restore(path, before_config)
            _restore(receipt, before_receipt)
        except BaseException as rollback:
            raise ConnectionError("Hikari lifecycle removal failed and rollback failed") from rollback
        raise ConnectionError("Hikari lifecycle removal failed and was rolled back") from error
    return {"state": "absent", "owned": False, "detail": "Hikari local connection removed"}


def main() -> int:
    try:
        if len(sys.argv) != 4 or sys.argv[1] != "lifecycle" or sys.argv[3] != "--json":
            raise ConnectionError("usage: connection.py lifecycle <configure|inspect|unconfigure> --json")
        input_value = json.load(sys.stdin)
        action = sys.argv[2]
        result = inspect(input_value) if action == "inspect" else configure(input_value) if action == "configure" else unconfigure() if action == "unconfigure" else None
        if result is None:
            raise ConnectionError("usage: connection.py lifecycle <configure|inspect|unconfigure> --json")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ConnectionError, OSError, ValueError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
