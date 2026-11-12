"""Lossless handoff storage; lifecycle and Task authority remain in their owners."""

from __future__ import annotations

import hashlib
import itertools
import json
import os
import re
import shutil
import stat
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from workflow_contracts import ContractError

MANIFEST = "storage-manifest.json"
LIFECYCLE = "lifecycle.jsonl"
JOURNAL = "retention-events.jsonl"
OWNERSHIP_INTENT = "ownership-intent.json"
CONTROLS = {LIFECYCLE, JOURNAL, OWNERSHIP_INTENT}
PRIMARY = {"session-handoff.json", "session-handoff-history.jsonl", "session-handoff-prompt.md"}
MAX_MEMBERS = 128
# Disk/expansion budget, independent of the 192 MiB streaming memory gate.
MAX_EXPANDED_BYTES = 4 * 1024 * 1024 * 1024
CHUNK = 256 * 1024


def safe_path(root: Path, path: Path) -> Path:
    try:
        parts = path.relative_to(root).parts
    except ValueError as exc:
        raise ContractError("handoff storage path is outside project") from exc
    if any(part in {".", ".."} for part in parts):
        raise ContractError("handoff storage path is not canonical")
    cursor = root
    for part in parts:
        cursor /= part
        if cursor.is_symlink():
            raise ContractError("handoff storage path contains a symlink")
    return path


def fingerprint(path: Path, *, content: bool = True) -> list:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ContractError("handoff storage member must be a regular file")
    result = [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]
    if content:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(CHUNK), b""):
                digest.update(chunk)
        if fingerprint(path, content=False) != result:
            raise ContractError("handoff storage member changed during inspection")
        result.append(digest.hexdigest())
    return result


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _unique_fields(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ContractError("storage JSON contains duplicate fields")
        result[name] = value
    return result


def historical_identity(path: Path) -> dict:
    """Project only small top-level identity fields, never materialize history arrays.

    This verifies the selected fields, not historical schema/admission semantics.
    """
    selected = {"schema_version", "kind", "handoff_id", "project", "work_context"}
    result = {}
    with path.open("r", encoding="utf-8", newline="") as source:
        chunks = iter(lambda: source.read(64 * 1024), "")
        characters = (char for chunk in chunks for char in chunk)
        def take():
            return next(characters, "")
        def nonspace():
            char = take()
            while char and char.isspace():
                char = take()
            return char
        if nonspace() != "{":
            raise ContractError("historical core identity is not an object")
        char = nonspace()
        seen = set()
        while char != "}":
            if char != '"':
                raise ContractError("historical top-level key is invalid")
            key, escaped = ['"'], False
            while True:
                char = take()
                if not char or len(key) > 64 * 1024:
                    raise ContractError("historical identity key exceeds budget")
                key.append(char)
                if char == '"' and not escaped:
                    break
                escaped = char == "\\" and not escaped
            name = json.loads("".join(key))
            if name in seen:
                raise ContractError("historical core has duplicate top-level fields")
            seen.add(name)
            if len(seen) > 128:
                raise ContractError("historical top-level field budget exceeded")
            if nonspace() != ":":
                raise ContractError("historical identity separator is invalid")
            char = nonspace()
            value, depth, quoted, escaped = [], 0, False, False
            while char:
                if not quoted and depth == 0 and char in ",}":
                    break
                if name in selected:
                    if len(value) >= 256 * 1024:
                        raise ContractError("historical identity projection exceeds budget")
                    value.append(char)
                if quoted:
                    if char == '"' and not escaped:
                        quoted = False
                    escaped = char == "\\" and not escaped
                elif char == '"':
                    quoted = True
                elif char in "[{":
                    depth += 1
                elif char in "]}":
                    depth -= 1
                    if depth < 0:
                        raise ContractError("historical identity nesting is invalid")
                char = take()
            if not char or quoted or depth:
                raise ContractError("historical core is incomplete")
            if name in selected:
                try:
                    result[name] = json.loads("".join(value), object_pairs_hook=_unique_fields)
                except (ValueError, RecursionError) as exc:
                    raise ContractError("historical identity value is invalid") from exc
            if char == "}":
                break
            char = nonspace()
        if nonspace():
            raise ContractError("historical core has trailing data")
    return result


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_record(path: Path, value: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=".ownership-intent-", delete=False) as handle:
            temporary = Path(handle.name)
            os.chmod(temporary, 0o600)
            json.dump(value, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


@contextmanager
def lock(root: Path):
    path = safe_path(root, root / ".trellis/.runtime/handoff.lock")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        import fcntl
        descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, "a+b") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ContractError("handoff lock must be a regular file")
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            yield
    except ImportError as exc:
        raise ContractError("handoff fixed lock is unavailable") from exc


def package_directory(root: Path, identifier: str) -> Path:
    if not re.fullmatch(r"\d{8}T\d{12}Z", identifier):
        raise ContractError("handoff storage identifier is invalid")
    return safe_path(root, root / ".trellis/session-handoffs" / identifier)


def zip_path(root: Path, identifier: str) -> Path:
    return package_directory(root, identifier).with_suffix(".zip")


def _name(name: str) -> str:
    path = PurePosixPath(name)
    if not name or "\\" in name or path.is_absolute() or any(p in {".", ".."} for p in name.split("/")):
        raise ContractError("ZIP member path is unsafe")
    if path.as_posix() != name or name.endswith("/"):
        raise ContractError("ZIP member path is not canonical")
    if name not in PRIMARY | CONTROLS | {MANIFEST} and not name.startswith("legacy/"):
        raise ContractError("ZIP contains an unknown member")
    return name


def sources(root: Path, identifier: str, *, validate: bool = True) -> dict[str, Path]:
    """Only explicit owner families; unknown package members block this object."""
    result: dict[str, Path] = {}
    directory = package_directory(root, identifier)
    if directory.exists():
        if not directory.is_dir():
            raise ContractError("handoff package is not a directory")
        for member in directory.iterdir():
            if member.name == "legacy" and member.is_dir() and not member.is_symlink():
                entries = list(itertools.islice(member.rglob("*"), MAX_MEMBERS + 1))
                if len(entries) > MAX_MEMBERS:
                    raise ContractError("expanded legacy member budget exceeded")
                for entry in entries:
                    safe_path(root, entry)
                    if entry.is_dir():
                        continue
                    result[entry.relative_to(directory).as_posix()] = entry
                continue
            if member.name not in PRIMARY | CONTROLS:
                raise ContractError("handoff package contains unknown assets")
            safe_path(root, member)
            result[member.name] = member
    legacy_receipt = safe_path(root, root / ".trellis/.runtime/handoff-lifecycle" / (identifier + ".jsonl"))
    if legacy_receipt.exists():
        result["legacy/handoff-lifecycle/" + legacy_receipt.name] = legacy_receipt
        if LIFECYCLE not in result:
            result[LIFECYCLE] = legacy_receipt
    archive = safe_path(root, root / ".trellis/.runtime/handoff-archive" / identifier)
    if archive.exists():
        if not archive.is_dir():
            raise ContractError("legacy handoff archive is not a directory")
        for member in archive.iterdir():
            if member.name not in PRIMARY:
                raise ContractError("legacy handoff archive contains unknown assets")
            result["legacy/handoff-archive/" + member.name] = safe_path(root, member)
            if member.name not in result:
                result[member.name] = member
    ownership = safe_path(root, root / ".trellis/.runtime/handoff-ownership")
    if ownership.exists():
        directories = list(itertools.islice(ownership.iterdir(), 2049))
        if len(directories) > 2048:
            raise ContractError("legacy ownership association scan exceeds budget")
        for directory in directories:
            safe_path(root, directory)
            if not directory.is_dir():
                raise ContractError("legacy ownership layout is unknown")
            record = safe_path(root, directory / (identifier + ".json"))
            if record.exists():
                if validate:
                    before = fingerprint(record)
                    if before[2] > 256 * 1024:
                        raise ContractError("legacy ownership record exceeds budget")
                    value = json.loads(record.read_text(encoding="utf-8"))
                    if not isinstance(value, dict) or value.get("handoff_id") != identifier:
                        raise ContractError("legacy ownership record identity differs")
                result["legacy/handoff-ownership/" + directory.name + "/" + record.name] = record
    if "session-handoff.json" not in result and not zip_path(root, identifier).exists():
        raise ContractError("handoff core is unavailable")
    if len(result) >= MAX_MEMBERS:
        raise ContractError("handoff storage member budget exceeded")
    return dict(sorted(result.items()))


def snapshot(root: Path, identifier: str) -> dict:
    members = sources(root, identifier)
    files = {name: fingerprint(path) for name, path in members.items()}
    for name in PRIMARY:
        legacy = "legacy/handoff-archive/" + name
        if name in files and legacy in files and files[name][-1] != files[legacy][-1]:
            raise ContractError("legacy and expanded original bytes differ")
    legacy_receipt = "legacy/handoff-lifecycle/" + identifier + ".jsonl"
    if LIFECYCLE in members and legacy_receipt in members and not is_prefix(members[legacy_receipt], members[LIFECYCLE]):
        raise ContractError("legacy and current lifecycle records diverge")
    if sum(item[2] for item in files.values()) > MAX_EXPANDED_BYTES:
        raise ContractError("handoff storage expansion budget exceeded")
    archive = zip_path(root, identifier)
    if archive.exists():
        manifest = verify(archive, identifier)
        for name, record in files.items():
            if name.startswith("legacy/") and members[name].is_relative_to(package_directory(root, identifier)):
                if manifest["members"].get(name, {}).get("sha256") != record[-1]:
                    raise ContractError("expanded legacy evidence differs from verified ZIP")
    return {"files": files, "zip": fingerprint(archive) if archive.exists() else None}


def unchanged(root: Path, identifier: str, expected: dict) -> None:
    current = sources(root, identifier, validate=False)
    if set(current) != set(expected["files"]):
        raise ContractError("handoff members changed after preview")
    for name, path in current.items():
        if fingerprint(path, content=False) != expected["files"][name][:5]:
            raise ContractError("handoff member changed after preview")
    archive = zip_path(root, identifier)
    actual = fingerprint(archive, content=False) if archive.exists() else None
    previous = expected["zip"][:5] if expected["zip"] is not None else None
    if actual != previous:
        raise ContractError("handoff ZIP changed after preview")


def verify(path: Path, identifier: str) -> dict:
    fingerprint(path, content=False)
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            names = [_name(entry.filename) for entry in entries]
            if len(names) > MAX_MEMBERS or len(set(names)) != len(names) or MANIFEST not in names:
                raise ContractError("ZIP member set is invalid")
            if sum(entry.file_size for entry in entries) > MAX_EXPANDED_BYTES:
                raise ContractError("ZIP expansion budget exceeded")
            for entry in entries:
                mode = entry.external_attr >> 16
                if entry.flag_bits & 1 or (mode and stat.S_IFMT(mode) not in {0, stat.S_IFREG}):
                    raise ContractError("ZIP member type or encryption is unsupported")
            info = archive.getinfo(MANIFEST)
            if info.file_size > 256 * 1024:
                raise ContractError("ZIP manifest exceeds budget")
            manifest = json.loads(archive.read(MANIFEST), object_pairs_hook=_unique_fields)
            if not isinstance(manifest, dict) or set(manifest) != {"storage_version", "handoff_id", "members", "content_digest", "qualification", "operation", "lifecycle"}:
                raise ContractError("ZIP manifest schema is invalid")
            if manifest["storage_version"] != 1 or isinstance(manifest["storage_version"], bool) or manifest["handoff_id"] != identifier:
                raise ContractError("ZIP manifest identity is invalid")
            members = manifest["members"]
            if not all(isinstance(manifest[key], dict) for key in ("qualification", "operation", "lifecycle")):
                raise ContractError("ZIP storage evidence is invalid")
            if not isinstance(members, dict) or set(members) != set(names) - {MANIFEST} or "session-handoff.json" not in members:
                raise ContractError("ZIP manifest member set differs")
            for name, record in members.items():
                if not isinstance(record, dict) or set(record) != {"bytes", "sha256", "role", "source"}:
                    raise ContractError("ZIP member record is invalid")
                if type(record["bytes"]) is not int or record["bytes"] != archive.getinfo(name).file_size:
                    raise ContractError("ZIP member length differs")
                role = "control" if name in CONTROLS else "legacy" if name.startswith("legacy/") else "original"
                if record["role"] != role or not isinstance(record["source"], str) or PurePosixPath(record["source"]).is_absolute() or ".." in PurePosixPath(record["source"]).parts:
                    raise ContractError("ZIP member association is invalid")
                hasher = hashlib.sha256()
                with archive.open(name) as member:
                    for chunk in iter(lambda: member.read(CHUNK), b""):
                        hasher.update(chunk)
                if hasher.hexdigest() != record["sha256"]:
                    raise ContractError("ZIP member SHA-256 differs")
            identity = {name: [record["bytes"], record["sha256"]] for name, record in members.items() if name not in CONTROLS}
            if digest(identity) != manifest["content_digest"]:
                raise ContractError("ZIP content identity differs")
            if manifest["lifecycle"].get("output_sha256") != members.get(LIFECYCLE, {}).get("sha256"):
                raise ContractError("ZIP output lifecycle digest differs")
            if JOURNAL in members:
                with archive.open(JOURNAL) as journal:
                    if _last_operation(journal, identifier) != manifest["operation"]:
                        raise ContractError("ZIP operation differs from its retention proof")
            elif manifest["operation"] != {"action": "snapshot", "status": "verified"}:
                raise ContractError("ZIP operation has no retention proof")
            return manifest
    except (zipfile.BadZipFile, KeyError, ValueError, TypeError, RuntimeError, NotImplementedError) as exc:
        if isinstance(exc, ContractError):
            raise
        raise ContractError("handoff ZIP is invalid") from exc


def write(path: Path, identifier: str, members: dict[str, Path], root: Path, *, qualification=None, operation=None, input_lifecycle_digest=None, source_locations=None) -> dict:
    if len(members) >= MAX_MEMBERS or sum(fingerprint(source, content=False)[2] for source in members.values()) > MAX_EXPANDED_BYTES:
        raise ContractError("handoff ZIP construction budget exceeded")
    manifest = {"storage_version": 1, "handoff_id": identifier, "members": {}, "content_digest": "", "qualification": qualification or {"kind": "storage_only", "basis": []}, "operation": operation or {"action": "snapshot", "status": "verified"}, "lifecycle": {"input_sha256": input_lifecycle_digest, "output_sha256": None}}
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as archive:
        for name, source in sorted(members.items()):
            _name(name)
            before = fingerprint(source, content=False)
            hasher, count = hashlib.sha256(), 0
            info = zipfile.ZipInfo(name)
            info.compress_type, info.external_attr = zipfile.ZIP_DEFLATED, (stat.S_IFREG | 0o600) << 16
            with source.open("rb") as handle, archive.open(info, "w", force_zip64=True) as target:
                for chunk in iter(lambda: handle.read(CHUNK), b""):
                    count += len(chunk)
                    hasher.update(chunk)
                    target.write(chunk)
            if before != fingerprint(source, content=False):
                raise ContractError("handoff member changed during compression")
            manifest["members"][name] = {
                "bytes": count, "sha256": hasher.hexdigest(),
                "role": "control" if name in CONTROLS else "legacy" if name.startswith("legacy/") else "original",
                "source": (source_locations or {}).get(name, source.relative_to(root).as_posix() if source.is_relative_to(root) else name),
            }
        manifest["content_digest"] = digest({name: [record["bytes"], record["sha256"]] for name, record in manifest["members"].items() if name not in CONTROLS})
        manifest["lifecycle"]["output_sha256"] = manifest["members"].get(LIFECYCLE, {}).get("sha256")
        archive.writestr(MANIFEST, json.dumps(manifest, sort_keys=True))
    os.chmod(path, 0o600)
    with path.open("rb") as handle:
        os.fsync(handle.fileno())
    return verify(path, identifier)


def extract(path: Path, identifier: str, destination: Path) -> dict:
    manifest = verify(path, identifier)
    before = fingerprint(path, content=False)
    with zipfile.ZipFile(path) as archive:
        for name in manifest["members"]:
            target = destination / name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with archive.open(name) as source, target.open("xb") as output:
                os.chmod(target, 0o600)
                shutil.copyfileobj(source, output, CHUNK)
                output.flush()
                os.fsync(output.fileno())
            if fingerprint(target)[-1] != manifest["members"][name]["sha256"]:
                raise ContractError("extracted ZIP member differs")
    if before != fingerprint(path, content=False):
        raise ContractError("handoff ZIP changed during extraction")
    return manifest


@contextmanager
def open_package(root: Path, identifier: str):
    directory = package_directory(root, identifier)
    archive = zip_path(root, identifier)
    if directory.exists():
        if not directory.is_dir():
            raise ContractError("handoff package is not a directory")
        if archive.exists():
            with tempfile.TemporaryDirectory(prefix="pennix-handoff-read-") as temporary:
                private = Path(temporary)
                manifest = extract(archive, identifier, private)
                originals = {name for name in manifest["members"] if name in PRIMARY}
                current = {member.name for member in directory.iterdir() if member.name in PRIMARY}
                if originals != current:
                    raise ContractError("expanded and ZIP original member sets differ")
                for name in originals:
                    safe_path(root, directory / name)
                    if fingerprint(directory / name)[-1] != manifest["members"][name]["sha256"]:
                        raise ContractError("expanded and ZIP original bytes differ")
                for name in CONTROLS:
                    left, right = directory / name, private / name
                    if left.exists() and right.exists():
                        if is_prefix(left, right):
                            continue
                        if not is_prefix(right, left):
                            raise ContractError("expanded and ZIP control records diverge")
                    if left.exists():
                        shutil.copyfile(left, right)
                        os.chmod(right, 0o600)
                yield private, "zip_committed"
                return
        yield directory, "plain"
        return
    if archive.exists():
        with tempfile.TemporaryDirectory(prefix="pennix-handoff-read-") as temporary:
            private = Path(temporary)
            extract(archive, identifier, private)
            yield private, "zip"
        return
    archive = safe_path(root, root / ".trellis/.runtime/handoff-archive" / identifier)
    if not archive.is_dir():
        raise ContractError("handoff package is unavailable")
    for member in archive.iterdir():
        if member.name not in PRIMARY:
            raise ContractError("legacy handoff archive contains unknown assets")
        safe_path(root, member)
        fingerprint(member, content=False)
    yield archive, "legacy_archive"


def is_prefix(prefix: Path, full: Path) -> bool:
    fingerprint(prefix, content=False)
    fingerprint(full, content=False)
    with prefix.open("rb") as left, full.open("rb") as right:
        for chunk in iter(lambda: left.read(CHUNK), b""):
            if right.read(len(chunk)) != chunk:
                return False
    return True


def append_operation(path: Path, identifier: str, operation: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        os.chmod(path, 0o600)
        handle.write(json.dumps({"storage_version": 1, "handoff_id": identifier, "operation": operation}, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def last_operation(path: Path, identifier: str) -> dict | None:
    if not path.exists():
        return None
    fingerprint(path, content=False)
    with path.open("rb") as handle:
        return _last_operation(handle, identifier)


def _last_operation(handle, identifier: str) -> dict | None:
    last = None
    while raw := handle.readline(8 * 1024 * 1024 + 1):
        if len(raw) > 8 * 1024 * 1024 or not raw.endswith(b"\n"):
            raise ContractError("retention proof record exceeds budget or is incomplete")
        try:
            event = json.loads(raw, object_pairs_hook=_unique_fields)
        except (ValueError, RecursionError) as exc:
            raise ContractError("retention proof is malformed") from exc
        if not isinstance(event, dict) or set(event) != {"storage_version", "handoff_id", "operation"} or type(event["storage_version"]) is not int or event["storage_version"] != 1 or event["handoff_id"] != identifier or not isinstance(event["operation"], dict):
            raise ContractError("retention proof identity is invalid")
        last = event["operation"]
    return last
