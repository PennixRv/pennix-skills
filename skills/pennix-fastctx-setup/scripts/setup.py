#!/usr/bin/env python3
"""Deploy Pennix FastCtx from a pinned GitHub Release."""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path


DEFAULT_REPOSITORY = "PennixRv/fastctx"
TAG_PATTERN = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
PENNIX_BEGIN = "<!-- pennix-fastctx:begin -->"
PENNIX_END = "<!-- pennix-fastctx:end -->"
PENNIX_MARKER = """<!-- pennix-fastctx:begin -->
## FastCtx Routing

- 涉及 FastCtx 的本地文件、命令或 job 路由，必须使用 `$pennix-fastctx-routing`；已有专用原生协议时优先使用该协议。
<!-- pennix-fastctx:end -->
"""
FASTCTX_BEGIN = "<!-- fastctx:begin -->"
FASTCTX_END = "<!-- fastctx:end -->"


class SetupError(RuntimeError):
    """A safe deployment precondition was not met."""


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def installed_binary() -> Path:
    name = "fastctx.exe" if os.name == "nt" else "fastctx"
    return Path.home() / ".fastctx" / "bin" / name


def release_asset() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    machine = {"amd64": "x86_64", "x86_64": "x86_64", "arm64": "aarch64", "aarch64": "aarch64"}.get(machine, machine)
    triples = {
        ("linux", "x86_64"): "x86_64-unknown-linux-gnu",
        ("linux", "aarch64"): "aarch64-unknown-linux-gnu",
        ("darwin", "x86_64"): "x86_64-apple-darwin",
        ("darwin", "aarch64"): "aarch64-apple-darwin",
        ("windows", "x86_64"): "x86_64-pc-windows-msvc",
        ("windows", "aarch64"): "aarch64-pc-windows-msvc",
    }
    try:
        triple = triples[(system, machine)]
    except KeyError as error:
        raise SetupError(f"Unsupported release platform: {system}/{machine}") from error
    return f"fastctx-{triple}.{'zip' if system == 'windows' else 'tar.gz'}"


def release_base(repository: str, version: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise SetupError("Repository must be an owner/name GitHub repository.")
    if not TAG_PATTERN.fullmatch(version):
        raise SetupError("Version must be an explicit release tag such as v0.2.7.")
    return f"https://github.com/{repository}/releases/download/{version}"


def marker_state(contents: str, begin: str, end: str, exact: str | None = None) -> str:
    begins = contents.count(begin)
    ends = contents.count(end)
    if not begins and not ends:
        return "absent"
    if begins != 1 or ends != 1:
        return "malformed"
    start = contents.index(begin)
    finish = contents.index(end, start) + len(end)
    block = contents[start:finish]
    if exact is not None and block != exact.rstrip("\n"):
        return "drifted"
    return "current"


def agents_path(codex_home: Path) -> Path:
    return codex_home / "AGENTS.md"


def read_agents(path: Path) -> str:
    if path.is_symlink():
        raise SetupError(f"Refusing to modify symbolic-link AGENTS file: {path}")
    try:
        return path.read_text(encoding="utf-8") if path.exists() else ""
    except UnicodeDecodeError as error:
        raise SetupError(f"Cannot safely read {path}: expected UTF-8 text.") from error


def write_agents(path: Path, contents: str) -> None:
    if path.is_symlink():
        raise SetupError(f"Refusing to modify symbolic-link AGENTS file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode if path.exists() else None
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(contents)
    if mode is not None:
        temporary.chmod(mode)
    os.replace(temporary, path)


def apply_pennix_marker(path: Path) -> None:
    contents = read_agents(path)
    state = marker_state(contents, PENNIX_BEGIN, PENNIX_END, PENNIX_MARKER)
    if state == "current":
        return
    if state != "absent":
        raise SetupError(f"Refusing to replace {state} Pennix FastCtx guidance in {path}.")
    if contents and not contents.endswith("\n"):
        raise SetupError(f"Refusing to append to {path}: add a final newline first.")
    write_agents(path, contents + PENNIX_MARKER)
    if marker_state(read_agents(path), PENNIX_BEGIN, PENNIX_END, PENNIX_MARKER) != "current":
        raise SetupError(f"Pennix dispatcher verification failed for {path}.")


def remove_pennix_marker(path: Path) -> None:
    contents = read_agents(path)
    state = marker_state(contents, PENNIX_BEGIN, PENNIX_END, PENNIX_MARKER)
    if state == "absent":
        return
    if state != "current":
        raise SetupError(f"Refusing to remove {state} Pennix FastCtx guidance in {path}.")
    start = contents.index(PENNIX_BEGIN)
    finish = contents.index(PENNIX_END, start) + len(PENNIX_END)
    if contents[finish:finish + 1] == "\n":
        finish += 1
    write_agents(path, contents[:start] + contents[finish:])


def download(url: str, destination: Path) -> None:
    try:
        with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except OSError as error:
        raise SetupError(f"Cannot download release asset: {url}") from error


def expected_sha256(checksums: Path, asset: str) -> str:
    for line in checksums.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == asset and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            return parts[0].lower()
    raise SetupError(f"SHA256SUMS does not list {asset}.")


def extract_binary(archive: Path, destination: Path) -> None:
    executable = "fastctx.exe" if archive.suffix == ".zip" else "fastctx"
    if archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as bundle:
            candidates = [item for item in bundle.infolist() if Path(item.filename).name == executable and not item.is_dir()]
            if len(candidates) != 1:
                raise SetupError("Release archive must contain exactly one FastCtx binary.")
            with bundle.open(candidates[0]) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
    else:
        with tarfile.open(archive, "r:gz") as bundle:
            candidates = [item for item in bundle.getmembers() if Path(item.name).name == executable and item.isfile()]
            if len(candidates) != 1:
                raise SetupError("Release archive must contain exactly one FastCtx binary.")
            source = bundle.extractfile(candidates[0])
            if source is None:
                raise SetupError("Cannot extract FastCtx binary from release archive.")
            with source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)
    destination.chmod(destination.stat().st_mode | 0o111)


def run_fastctx(binary: Path, *arguments: str) -> None:
    result = subprocess.run([str(binary), *arguments], check=False)
    if result.returncode:
        raise SetupError(f"FastCtx command failed ({result.returncode}): {' '.join(arguments)}")


def print_plan(args: argparse.Namespace) -> None:
    asset = release_asset()
    base = release_base(args.repository, args.version)
    print(f"Release: {args.repository} {args.version}")
    print(f"Asset: {asset}")
    print(f"Archive: {base}/{asset}")
    print(f"Checksum: {base}/SHA256SUMS")
    print(f"Codex home: {args.codex_home}")
    print("Changes: install FastCtx without managed guidance, then add the Pennix dispatcher marker.")


def run_apply(args: argparse.Namespace) -> None:
    if not args.yes:
        raise SetupError("apply requires --yes after doctor and plan review.")
    asset = release_asset()
    base = release_base(args.repository, args.version)
    agent_file = agents_path(args.codex_home)
    legacy_state = marker_state(read_agents(agent_file), FASTCTX_BEGIN, FASTCTX_END)
    if legacy_state != "absent" and not (Path.home() / ".fastctx" / "config.toml").is_file():
        raise SetupError("Existing FastCtx guidance has no matching local receipt; remove it with its owner first.")
    with tempfile.TemporaryDirectory(prefix="pennix-fastctx-") as temporary:
        temporary_path = Path(temporary)
        archive = temporary_path / asset
        checksums = temporary_path / "SHA256SUMS"
        binary = temporary_path / ("fastctx.exe" if os.name == "nt" else "fastctx")
        download(f"{base}/{asset}", archive)
        download(f"{base}/SHA256SUMS", checksums)
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
        if actual != expected_sha256(checksums, asset):
            raise SetupError(f"SHA256 mismatch for {asset}.")
        extract_binary(archive, binary)
        if legacy_state != "absent":
            run_fastctx(binary, "guidance", "remove", "--codex-home", str(args.codex_home), "--yes")
            if marker_state(read_agents(agent_file), FASTCTX_BEGIN, FASTCTX_END) != "absent":
                raise SetupError("FastCtx guidance remains after its owner attempted removal.")
        run_fastctx(binary, "apply", "--guidance", "none", "--codex-home", str(args.codex_home), "--yes")
    apply_pennix_marker(agent_file)
    print("Pennix FastCtx deployment completed.")


def run_doctor(args: argparse.Namespace) -> None:
    contents = read_agents(agents_path(args.codex_home))
    print(f"Pennix dispatcher: {marker_state(contents, PENNIX_BEGIN, PENNIX_END, PENNIX_MARKER)}")
    print(f"FastCtx marker: {marker_state(contents, FASTCTX_BEGIN, FASTCTX_END)}")
    binary = installed_binary()
    if binary.is_file():
        run_fastctx(binary, "--version")
    else:
        print("Installed FastCtx: absent")


def run_rollback(args: argparse.Namespace) -> None:
    if not args.yes:
        raise SetupError("rollback requires --yes.")
    binary = installed_binary()
    if not binary.is_file():
        raise SetupError(f"Installed FastCtx binary is missing: {binary}")
    remove_pennix_marker(agents_path(args.codex_home))
    run_fastctx(binary, "guidance", "apply", "--codex-home", str(args.codex_home), "--yes")
    print("Pennix FastCtx dispatcher removed; FastCtx managed guidance restored.")


def add_codex_home(argument_parser: argparse.ArgumentParser) -> None:
    argument_parser.add_argument("--codex-home", type=Path, default=default_codex_home())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    doctor = subcommands.add_parser("doctor")
    add_codex_home(doctor)
    plan = subcommands.add_parser("plan")
    add_codex_home(plan)
    plan.add_argument("--version", required=True)
    plan.add_argument("--repository", default=DEFAULT_REPOSITORY)
    apply = subcommands.add_parser("apply")
    add_codex_home(apply)
    apply.add_argument("--version", required=True)
    apply.add_argument("--repository", default=DEFAULT_REPOSITORY)
    apply.add_argument("--yes", action="store_true")
    rollback = subcommands.add_parser("rollback")
    add_codex_home(rollback)
    rollback.add_argument("--yes", action="store_true")
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        args.codex_home = args.codex_home.expanduser()
        if args.command == "doctor":
            run_doctor(args)
        elif args.command == "plan":
            print_plan(args)
        elif args.command == "apply":
            run_apply(args)
        else:
            run_rollback(args)
    except SetupError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
