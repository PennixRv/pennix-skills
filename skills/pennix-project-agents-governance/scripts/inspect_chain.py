"""Read-only Codex instruction candidates; never claims host loading."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def inspect_chain(cwd: Path, codex_home: Path, project_root: Path | None = None,
                  fallbacks: tuple[str, ...] = (), max_bytes: int = 32768,
                  config_confirmed: bool = False) -> dict:
    if max_bytes < 0:
        raise ValueError("max_bytes must be nonnegative")
    for name in fallbacks:
        if not name or name in {".", ".."} or Path(name).name != name or "\\" in name:
            raise ValueError("fallback must be a single filename")
    cwd = cwd.absolute()
    root = project_root.absolute() if project_root is not None else cwd
    if not cwd.is_dir() or not root.is_dir():
        raise ValueError("cwd and project root must be existing directories")
    try:
        relative = cwd.relative_to(root)
    except ValueError as error:
        raise ValueError("cwd must be inside project root") from error
    directories = [root]
    for part in relative.parts:
        directories.append(directories[-1] / part)
    layers = []
    remaining = max_bytes
    included = False
    unknown = not config_confirmed
    for scope, directory, names in [("user", codex_home.absolute(), ("AGENTS.override.md", "AGENTS.md")),
                                    *(("project", d, tuple(dict.fromkeys(("AGENTS.override.md", "AGENTS.md", *fallbacks)))) for d in directories)]:
        layer = {"scope": scope, "directory": str(directory), "status": "absent", "candidates": []}
        for name in names:
            file = directory / name
            try:
                data = file.read_bytes()
                text = data.decode("utf-8")
            except FileNotFoundError:
                layer["candidates"].append({"path": str(file), "status": "absent"})
                continue
            except (OSError, UnicodeError):
                layer.update(status="unknown", path=str(file), reason="unreadable-or-invalid-utf8")
                unknown = True
                break
            if not text.strip():
                layer["candidates"].append({"path": str(file), "status": "empty"})
                continue
            separator = 2 if included else 0
            admitted = min(len(data), max(0, remaining - separator))
            remaining = max(0, remaining - separator - admitted)
            included = included or admitted > 0
            layer.update(status="candidate", path=str(file), bytes=len(data), budgeted_bytes=admitted,
                         truncated=admitted < len(data),
                         symlink=any(p.is_symlink() for p in (file, *file.parents)),
                         shadowed=[str(directory / n) for n in names[names.index(name) + 1:] if (directory / n).exists()])
            break
        layers.append(layer)
    return {"status": "unknown" if unknown else "candidate", "host_loaded": False,
            "configuration": "confirmed-by-caller" if config_confirmed else "unknown",
            "budget_basis": "raw-bytes-with-blank-line-separators; host rendering may differ",
            "max_bytes": max_bytes, "remaining_bytes": remaining, "layers": layers}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--fallback", action="append", default=[])
    parser.add_argument("--max-bytes", type=int, default=32768)
    parser.add_argument("--config-confirmed", action="store_true")
    args = parser.parse_args()
    try:
        result = inspect_chain(args.cwd, args.codex_home, args.project_root, tuple(args.fallback), args.max_bytes, args.config_confirmed)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
