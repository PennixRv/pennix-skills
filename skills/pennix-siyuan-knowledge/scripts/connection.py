#!/usr/bin/env python3
"""Manage the private SiYuan connection record without contacting SiYuan."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

from mcp_headers import ConnectionError, connection_path, read_connection, validate


def receipt_path() -> Path:
    return connection_path().with_name(".pennix-lifecycle.json")


def digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def read_receipt() -> dict | None:
    path = receipt_path()
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.getuid():
            raise ConnectionError("unsafe lifecycle receipt")
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError, UnicodeError) as error:
        raise ConnectionError("invalid lifecycle receipt") from error
    if (not isinstance(value, dict) or value.get("schema") != 2 or value.get("owner") != "pennix-siyuan-knowledge"
            or not isinstance(value.get("digest"), str) or not isinstance(value.get("desired_digest"), str)):
        raise ConnectionError("invalid lifecycle receipt")
    return value


def write_private(path: Path, value: dict) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = path.parent
    current = parent
    while current != current.parent:
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ConnectionError("unsafe connection directory")
        current = current.parent
    parent_info = parent.lstat()
    if parent_info.st_uid != os.getuid() or stat.S_IMODE(parent_info.st_mode) != 0o700:
        raise ConnectionError("unsafe connection directory")
    if path.is_symlink() or (path.exists() and (not path.is_file() or stat.S_IMODE(path.stat().st_mode) != 0o600)):
        raise ConnectionError("unsafe connection target")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary).chmod(0o600)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def restore_private(path: Path, content: bytes | None) -> None:
    if content is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    parent = path.parent
    current = parent
    while current != current.parent:
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ConnectionError("unsafe connection directory")
        current = current.parent
    parent_info = parent.lstat()
    if parent_info.st_uid != os.getuid() or stat.S_IMODE(parent_info.st_mode) != 0o700:
        raise ConnectionError("unsafe connection directory")
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.restore.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary).chmod(0o600)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def inspect(input_value: dict | None = None) -> dict:
    input_value = input_value or {}
    path = connection_path()
    if not path.exists() and not path.is_symlink():
        return {"state": "missing", "owned": False, "detail": "SiYuan connection is absent"}
    try:
        value = read_connection(path)
    except FileNotFoundError:
        return {"state": "missing", "owned": False, "detail": "SiYuan connection is absent"}
    except (OSError, ValueError, UnicodeError, ConnectionError):
        return {"state": "invalid", "owned": False, "detail": "SiYuan connection is invalid"}
    receipt = read_receipt()
    if receipt is None:
        canonical = json.dumps({"target": "siyuan", "values": {"url": value["url"], "default_notebook": value["default_notebook"]},
                                "secrets": {"api_token": value["api_token"]}}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        same = input_value.get("desired_digest") == hashlib.sha256(canonical).hexdigest()
        return {"state": "adoptable" if same else "external", "owned": False,
                "detail": "SiYuan connection exists without lifecycle ownership"}
    if receipt["digest"] != digest(path):
        return {"state": "invalid", "owned": True, "detail": "SiYuan connection changed outside lifecycle ownership"}
    current = receipt["digest"] == digest(path) and (
        not input_value.get("desired_digest") or receipt["desired_digest"] == input_value["desired_digest"]
    )
    return {"state": "current" if current else "drifted", "owned": True, "detail": "SiYuan connection matches lifecycle receipt" if current else "SiYuan connection drifted"}


def configure(input_value: dict) -> dict:
    if input_value.get("target") != "siyuan" or not isinstance(input_value.get("values"), dict) or not isinstance(input_value.get("secrets"), dict):
        raise ConnectionError("SiYuan lifecycle input is invalid")
    if not isinstance(input_value.get("desired_digest"), str):
        raise ConnectionError("SiYuan lifecycle input is incomplete")
    canonical = json.dumps({key: input_value[key] for key in ("target", "values", "secrets")},
                           ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(canonical).hexdigest() != input_value["desired_digest"]:
        raise ConnectionError("SiYuan lifecycle desired digest is invalid")
    before = inspect(input_value)
    if before["state"] == "current":
        return before
    if before["state"] in {"external", "invalid"} or before["state"] == "adoptable" and input_value.get("adopt_existing") is not True:
        raise ConnectionError(f"SiYuan owner state {before['state']} cannot be taken over")
    values, secrets = input_value["values"], input_value["secrets"]
    record = {"schema": 1, "url": values.get("url"), "api_token": secrets.get("api_token"), "default_notebook": values.get("default_notebook")}
    if any(not isinstance(record[key], str) or not record[key].strip() for key in ("url", "api_token", "default_notebook")):
        raise ConnectionError("SiYuan lifecycle fields are incomplete")
    validate(record)
    path = connection_path()
    before_connection = path.read_bytes() if path.exists() else None
    before_receipt = receipt_path().read_bytes() if receipt_path().exists() else None
    try:
        if before["state"] != "adoptable":
            write_private(path, record)
        write_private(receipt_path(), {"schema": 2, "owner": "pennix-siyuan-knowledge", "digest": digest(path), "desired_digest": input_value["desired_digest"]})
    except BaseException as error:
        try:
            restore_private(path, before_connection)
            restore_private(receipt_path(), before_receipt)
        except BaseException as rollback:
            raise ConnectionError("SiYuan lifecycle write failed and rollback failed") from rollback
        raise ConnectionError("SiYuan lifecycle write failed and was rolled back") from error
    return {"state": "current", "owned": True, "detail": "SiYuan connection configured without handshake"}


def unconfigure() -> dict:
    before = inspect()
    if before["state"] == "missing":
        return {"state": "absent", "owned": False, "detail": "SiYuan connection is absent"}
    if not before["owned"] or before["state"] != "current":
        raise ConnectionError("SiYuan lifecycle ownership is missing or drifted")
    path = connection_path()
    receipt = receipt_path()
    before_connection = path.read_bytes()
    before_receipt = receipt.read_bytes()
    try:
        path.unlink()
        receipt.unlink()
    except BaseException as error:
        try:
            restore_private(path, before_connection)
            restore_private(receipt, before_receipt)
        except BaseException as rollback:
            raise ConnectionError("SiYuan lifecycle removal failed and rollback failed") from rollback
        raise ConnectionError("SiYuan lifecycle removal failed and was rolled back") from error
    return {"state": "absent", "owned": False, "detail": "SiYuan connection removed"}


def main() -> int:
    try:
        input_value = json.load(sys.stdin)
        if len(sys.argv) != 4 or sys.argv[1] != "lifecycle" or sys.argv[3] != "--json":
            raise ConnectionError("usage: connection.py lifecycle <configure|inspect|unconfigure> --json")
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
