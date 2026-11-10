#!/usr/bin/env python3
"""本任务的串行原生 Codex 行为采集；结果必须人工核验，原始轨迹只留 /tmp。"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import signal
import stat
import subprocess
import tempfile
import time
import tomllib

CASES = Path(__file__).with_name("skill-cases.json")
MAX_TRACE_BYTES = 8 * 1024 * 1024
TIMEOUT_SECONDS = 300
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.:/-]{1,100}$")
SKILL_PATH = re.compile(r"(?<![\w./~-])((?:~/|/)?(?:[\w.-]+/)+SKILL\.md)(?![\w.-])")
SAFETY = """这是已授权的只读 Skill 行为测试，不是实现或检查 worker。
使用实际已安装 Skill 和真正可用工具；不要伪造工具、结果、用户答复或会话身份。
仅允许读取 Skill/必要 reference、读取当前 fixture 和查询 CLI help。
不得安装、配置、更新项目、创建交接、写知识、发网络/provider 请求或读取秘密。
如果原请求需要这些动作，先读取适用入口并指出必要条件，停在动作之前。
当前目录是无秘密临时 fixture；不要扫描其他项目或历史会话。不要更换模型或绕过信任。
请实际读取应加载的 Skill，不以口头声明代替。最后说明已观察事实、能力缺失和停止点。
测试请求：
"""


def load_cases(path=CASES):
    raw = path.read_bytes()
    data = json.loads(raw)
    cases = data["cases"]
    ids = [case["id"] for case in cases]
    if data["schema_version"] != 1 or data["model_turn_limit"] != 100:
        raise ValueError("invalid_case_contract")
    if not cases or len(set(ids)) != len(cases):
        raise ValueError("invalid_case_coverage")
    for case in cases:
        if not case["prompt"] or not case["expected"] or not SAFE_NAME.fullmatch(case["id"]):
            raise ValueError("invalid_case")
    return data, hashlib.sha256(raw).hexdigest()


def private_output(path):
    path = Path(path)
    if not path.is_absolute() or Path(tempfile.gettempdir()) not in path.parents:
        raise ValueError("output_must_be_temporary")
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError("unsafe_output_path")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    stat = path.stat()
    if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
        raise ValueError("output_must_be_private")
    return path


def reserve_turn(output, digest, phase, case_id, retry=False):
    path = output / "budget.json"
    if path.is_symlink():
        raise ValueError("unsafe_budget")
    state = json.loads(path.read_text()) if path.exists() else {
        "schema_version": 1, "fixture_sha256": digest, "attempts": []
    }
    if state["schema_version"] != 1 or state["fixture_sha256"] != digest:
        raise ValueError("budget_fixture_mismatch")
    attempts = state["attempts"]
    if len(attempts) >= 100:
        raise ValueError("model_turn_budget_exhausted")
    if not retry and any(x["phase"] == phase and x["case_id"] == case_id for x in attempts):
        return None
    number = len(attempts) + 1
    attempts.append({"number": number, "phase": phase, "case_id": case_id})
    temporary = output / "budget.next.json"
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary, path)
    return number


def provider_options(provider_home):
    """Reuse public provider settings and the existing owner auth command, never auth files."""
    home = Path(provider_home)
    if not home.is_absolute() or home.is_symlink():
        raise ValueError("invalid_provider_home")
    config = tomllib.loads((home / ".codex/config.toml").read_text())
    name, model = config.get("model_provider"), config.get("model")
    provider = config.get("model_providers", {}).get(name, {})
    owner = home / ".local/bin/pennix"
    secrets = home / ".config/pennix/secrets.toml"
    release = home / ".local/share/pennix-lifecycle/releases"
    if (not isinstance(name, str) or not SAFE_NAME.fullmatch(name)
            or not isinstance(model, str) or not SAFE_NAME.fullmatch(model)
            or not isinstance(provider.get("base_url"), str)
            or not owner.resolve(strict=True).is_relative_to(release.resolve(strict=True))
            or not secrets.is_file() or secrets.is_symlink()):
        raise ValueError("provider_owner_unavailable")
    # Explicit native CLI overrides are process-local; the owner reads its secret at runtime.
    selected = {"model": model, "model_provider": name,
                f"model_providers.{name}.name": provider.get("name", name),
                f"model_providers.{name}.base_url": provider["base_url"],
                f"model_providers.{name}.wire_api": "responses",
                f"model_providers.{name}.requires_openai_auth": False,
                f"model_providers.{name}.auth.command": str(owner),
                f"model_providers.{name}.auth.args": ["secrets", "codex-token", "--secrets-file", str(secrets)]}
    return [part for key, value in selected.items() for part in ("-c", key + "=" + json.dumps(value, ensure_ascii=False))]


def command(workspace, provider_args=()):
    return ["codex", "exec", "--json", "--sandbox", "read-only",
            "--skip-git-repo-check", "--color", "never", "--cd", str(workspace),
            "-c", 'approval_policy="never"', "-c", "agents.enabled=false", *provider_args, "-"]


def stop_process(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=5)


def source_identity(codex_home, revision, *, user_home=None):
    home = Path(codex_home)
    if not home.is_absolute() or home.is_symlink() or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("invalid_evaluation_source")
    user = Path(user_home) if user_home is not None else Path.home()
    root = user / ".agents/skills/pennix-skills"
    if not user.is_absolute() or any(parent.is_symlink() for parent in (root, *root.parents)):
        raise ValueError("unsafe_evaluation_source")
    receipt_path = root.parent / ".pennix-skills.receipt.json"
    if root.is_symlink() or receipt_path.is_symlink():
        raise ValueError("unsafe_evaluation_source")
    receipt = json.loads(receipt_path.read_bytes())
    if (receipt.get("schema") != 1 or receipt.get("destination") != root.name
            or receipt.get("target") != str(root)
            or receipt.get("source") != {"repo": "PennixRv/pennix-skills", "ref": revision, "manifest": "collection.json"}
            or not isinstance(receipt.get("manifest", {}).get("skills"), dict)):
        raise ValueError("evaluation_source_mismatch")
    digest = hashlib.sha256()
    for item in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        relative = item.relative_to(root)
        info = item.lstat()
        if (not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))
                or info.st_uid != os.getuid() or info.st_mode & 0o022):
            raise ValueError("unsafe_evaluation_source")
        if "__pycache__" in relative.parts or item.suffix == ".pyc":
            continue
        if item.is_dir():
            digest.update(f"D\0{relative.as_posix()}\0".encode())
        else:
            digest.update(f"F\0{relative.as_posix()}\0{info.st_mode & 0o111:o}\0".encode())
            with item.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    digest.update(chunk)
    if digest.hexdigest() != receipt.get("digest"):
        raise ValueError("evaluation_source_drift")
    return {"codex_home": str(home), "collection_target": str(root), "collection_commit": revision, "collection_digest": digest.hexdigest()}


def collect(case, workspace, stdout, stderr, codex_home=None, provider_args=()):
    started = time.monotonic()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        environment = dict(os.environ)
        if codex_home is not None:
            environment["CODEX_HOME"] = str(codex_home)
        process = subprocess.Popen(command(workspace, provider_args), stdin=subprocess.PIPE, env=environment,
                                   stdout=out, stderr=err, start_new_session=True)
        try:
            process.stdin.write((SAFETY + case["prompt"]).encode("utf-8"))
            process.stdin.close()
            while process.poll() is None:
                if time.monotonic() - started > TIMEOUT_SECONDS:
                    stop_process(process)
                    return "timeout"
                if stdout.stat().st_size + stderr.stat().st_size > MAX_TRACE_BYTES:
                    stop_process(process)
                    return "trace_limit"
                time.sleep(0.2)
            return "completed" if process.returncode == 0 else "native_failure"
        except BaseException:
            stop_process(process)
            raise


def skill_observations(item, event_number):
    # shortcut: attribute only single-file cat; extend when a real trace needs another reader.
    tool = item.get("type")
    text = item.get("command", "") if tool == "command_execution" else json.dumps(item.get("arguments", {}))
    if not isinstance(text, str):
        return []
    paths = list(dict.fromkeys(SKILL_PATH.findall(text)))
    outcome = "unknown"
    if tool == "command_execution":
        lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        try:
            argv = list(lexer)
        except ValueError:
            argv = []
        if len(argv) == 3 and Path(argv[0]).name in ("bash", "zsh", "sh") and argv[1] in ("-lc", "-c"):
            lexer = shlex.shlex(argv[2], posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            lexer.commenters = ""
            try:
                argv = list(lexer)
            except ValueError:
                argv = []
        if argv[:2] == ["cat", "--"]:
            argv = ["cat", *argv[2:]]
        if len(argv) == 2 and argv[0] == "cat" and paths == [argv[1]]:
            exit_code = item.get("exit_code")
            if type(exit_code) is int and exit_code != 0:
                outcome = "failed"
            elif (type(exit_code) is int and exit_code == 0
                  and isinstance(item.get("aggregated_output"), str) and item["aggregated_output"]):
                outcome = "read"
    return [{"event": event_number, "path": value, "skill": Path(value).parent.name,
             "tool": tool, "outcome": outcome} for value in paths]


def summarize(path, native_status):
    result = {"native_status": native_status, "verdict": "review_needed",
              "events": 0, "tool_actions": [], "skill_read_candidates": [],
              "skill_path_observations": [],
              "actual_model": None, "usage": None}
    skills = set()
    with path.open("rb") as stream:
        while line := stream.readline(2 * 1024 * 1024 + 1):
            if len(line) > 2 * 1024 * 1024:
                result["verdict"] = "blocked_oversized_event"
                break
            try:
                event = json.loads(line)
            except (ValueError, UnicodeError):
                result["verdict"] = "blocked_invalid_event"
                continue
            if not isinstance(event, dict):
                result["verdict"] = "blocked_invalid_event"
                continue
            result["events"] += 1
            model = event.get("model")
            if isinstance(model, str) and SAFE_NAME.fullmatch(model):
                result["actual_model"] = model
            if event.get("type") == "turn.completed":
                usage = event.get("usage", {})
                result["usage"] = {key: value for key, value in usage.items()
                                   if key in ("input_tokens", "cached_input_tokens", "output_tokens")
                                   and type(value) is int and value >= 0}
            if event.get("type") != "item.completed":
                continue
            item = event.get("item", {})
            if not isinstance(item, dict):
                result["verdict"] = "blocked_invalid_event"
                continue
            if item.get("type") in ("command_execution", "mcp_tool_call"):
                observations = skill_observations(item, result["events"])
                result["skill_path_observations"].extend(observations)
                skills.update(x["skill"] for x in observations)
            if item.get("type") == "command_execution":
                text = item.get("command", "")
                if not isinstance(text, str):
                    text = ""
                owner = "native_cli" if any(x in text for x in ("task.py", "trellis ", "grok-search", "tvly-hikari", "windsurf-code-search")) else "host_shell"
                result["tool_actions"].append({"type": "command_execution", "owner": owner,
                                               "exit_code": item.get("exit_code")})
            elif item.get("type") == "mcp_tool_call":
                server, tool = item.get("server"), item.get("tool")
                if isinstance(server, str) and isinstance(tool, str) and SAFE_NAME.fullmatch(server) and SAFE_NAME.fullmatch(tool):
                    result["tool_actions"].append({"type": "mcp_tool_call", "server": server, "tool": tool,
                                                   "status": item.get("status")})
    result["skill_read_candidates"] = sorted(skills)
    result["skill_read_counts"] = {
        outcome: sum(item["outcome"] == outcome for item in result["skill_path_observations"])
        for outcome in ("read", "failed", "unknown")
    }
    if native_status != "completed":
        result["verdict"] = "blocked_native_execution"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--codex-home", required=True, help="宿主配置根；共享用户集合按当前 HOME 核验，不从配置根选择版本")
    parser.add_argument("--collection-commit", required=True, help="必须与 owner receipt 和实际内容吻合的完整提交")
    parser.add_argument("--provider-home", required=True, help="现有 Lifecycle owner 与公开 provider 配置所在的用户目录；不复制认证")
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--retry", action="store_true")
    parser.add_argument("--host", choices=("exec", "app-server"), default="exec")
    parser.add_argument("--resume-thread", help="app-server 原生线程 ID；不接受替换历史")
    parser.add_argument("--compact", action="store_true", help="先真实压缩 resume 的线程")
    args = parser.parse_args()
    if (args.resume_thread or args.compact) and args.host != "app-server":
        parser.error("resume/compact require app-server")
    os.umask(0o077)
    identity = source_identity(args.codex_home, args.collection_commit)
    provider_args = provider_options(args.provider_home)
    data, digest = load_cases()
    chosen = [case for case in data["cases"] if not args.case_ids or case["id"] in args.case_ids]
    if not chosen or (args.case_ids and set(args.case_ids) - {x["id"] for x in chosen}):
        raise ValueError("unknown_case")
    if args.retry and not args.case_ids:
        raise ValueError("retry_requires_specific_cases")
    output = private_output(args.output_dir)
    with (output / "run.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        workspace = output / "fixture"
        if workspace.is_symlink():
            raise ValueError("unsafe_fixture")
        workspace.mkdir(exist_ok=True, mode=0o700)
        fixtures = {"fixture.txt": "routing-marker\nsecond line\n",
                    "notes.md": "仅在来源校验成功时继续。失败时停止，不能宣称全面健康。\n错误原文：FC_PATH_INVALID\n",
                    "template.md": "# Implementation Plan\n\n## Preconditions\n\n仅在用户明确批准后实施。\n\n`execution_class = planned`\n",
                    "long.txt": "Unicode 中文 routing-marker\n" * 1000}
        for name, text in fixtures.items():
            target = workspace / name
            if target.is_symlink():
                raise ValueError("unsafe_fixture")
            if target.exists() and target.read_text() != text:
                raise ValueError("fixture_changed")
            if not target.exists():
                target.write_text(text)
        for case in chosen:
            number = reserve_turn(output, digest, args.phase, case["id"], args.retry)
            if number is None:
                continue
            stem = f"{number:03d}-{args.phase}-{case['id']}"
            trace, error = output / (stem + ".jsonl"), output / (stem + ".stderr")
            if source_identity(args.codex_home, args.collection_commit) != identity:
                raise ValueError("evaluation_source_changed")
            if args.host == "app-server":
                import app_server_cases
                status, thread_id, observations = app_server_cases.collect(
                    case, workspace, trace, error, args.codex_home, provider_args,
                    resume_thread=args.resume_thread, compact=args.compact)
                evidence = {"native_thread_id": thread_id, "interaction": observations,
                            "verdict": "needs_review" if status == "completed" else "blocked_native_execution"}
            else:
                status = collect(case, workspace, trace, error, args.codex_home, provider_args)
                evidence = summarize(trace, status)
            result = {"case_id": case["id"], "phase": args.phase, "turn_number": number,
                       "fixture_sha256": digest, "host": "codex-" + args.host + "-isolated-read-only",
                       "source": identity, **evidence}
            agents = Path(args.codex_home) / "AGENTS.md"
            result["agents_sha256"] = hashlib.sha256(agents.read_bytes()).hexdigest() if agents.is_file() else None
            (output / (stem + ".summary.json")).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if status != "completed":
                break


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({"status": "blocked", "category": type(error).__name__}), flush=True)
        raise SystemExit(1)
