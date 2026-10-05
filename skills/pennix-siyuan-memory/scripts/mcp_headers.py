#!/usr/bin/env python3
"""Supply private headers to Codex's native HTTP MCP transport; no networking."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from urllib.parse import urlsplit


class ConnectionError(RuntimeError):
    """Only fixed, redacted messages are exposed to callers."""


def connection_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    if not base.is_absolute():
        raise ConnectionError("configuration path must be absolute")
    return base / "pennix-siyuan" / "connection.json"


def validate(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != {"schema", "url", "api_token", "default_notebook"} or value["schema"] != 1:
        raise ConnectionError("invalid connection record")
    if any(not isinstance(value[key], str) for key in ("url", "api_token", "default_notebook")):
        raise ConnectionError("invalid connection record")
    try:
        url = urlsplit(value["url"])
        port = url.port
    except ValueError:
        raise ConnectionError("invalid MCP URL") from None
    if (url.scheme != "https" or not url.hostname or url.username is not None or url.password is not None
            or url.query or url.fragment or url.path != "/mcp" or port == 0
            or any(ord(char) <= 32 or ord(char) > 126 for char in value["url"])):
        raise ConnectionError("invalid MCP URL")
    token = value["api_token"]
    if not token or len(token) > 8192 or any(ord(char) <= 32 or ord(char) > 126 for char in token):
        raise ConnectionError("invalid API Token")
    if not re.fullmatch(r"\d{14}-[a-z0-9]{7}", value["default_notebook"]):
        raise ConnectionError("invalid notebook ID")
    return value


def read_connection(path: Path | None = None) -> dict:
    path = connection_path() if path is None else path
    current = path.absolute()
    while current != current.parent:
        if current.is_symlink():
            raise ConnectionError("unsafe connection path")
        current = current.parent
    try:
        parent = path.parent.stat()
        if not stat.S_ISDIR(parent.st_mode) or stat.S_IMODE(parent.st_mode) != 0o700 or parent.st_uid != os.getuid():
            raise ConnectionError("unsafe connection directory")
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.getuid() or info.st_size > 65536:
                raise ConnectionError("unsafe connection file")
            with os.fdopen(descriptor, "rb") as handle:
                descriptor = -1
                content = handle.read(65537)
            if len(content) > 65536:
                raise ConnectionError("oversized connection file")
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        return validate(json.loads(content))
    except (OSError, ValueError):
        raise ConnectionError("connection record unavailable or invalid") from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", action="store_true", help="emit nonsecret connection metadata only")
    args = parser.parse_args()
    try:
        value = read_connection()
    except ConnectionError as error:
        print(str(error), file=sys.stderr)
        return 2
    output = {key: value[key] for key in ("url", "default_notebook")} if args.metadata else {"Authorization": "Token " + value["api_token"]}
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
