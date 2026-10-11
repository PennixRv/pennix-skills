#!/usr/bin/env python3
"""本任务的串行原生 Codex 行为采集；结果必须人工核验，原始轨迹只留 /tmp。"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

CASES = Path(__file__).with_name("skill-cases.json")
MAX_TRACE_BYTES = 8 * 1024 * 1024
TIMEOUT_SECONDS = 300
SAFE_NAME = re.compile(r"^[A-Za-z0-9_.:/-]{1,100}$")
SKILL_PATH = re.compile(r"skills/(?:pennix-skills/)?([a-z0-9-]+)/SKILL\.md")
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
    if len(cases) != 44 or len(set(ids)) != 44:
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


def command(workspace):
    return ["codex", "exec", "--json", "--ephemeral", "--sandbox", "read-only",
            "--skip-git-repo-check", "--color", "never", "--cd", str(workspace),
            "-c", 'approval_policy="never"', "-c", "agents.enabled=false", "-"]


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


def collect(case, workspace, stdout, stderr):
    started = time.monotonic()
    with stdout.open("xb") as out, stderr.open("xb") as err:
        process = subprocess.Popen(command(workspace), stdin=subprocess.PIPE,
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


def summarize(path, native_status):
    result = {"native_status": native_status, "verdict": "review_needed",
              "events": 0, "tool_actions": [], "skill_read_candidates": [],
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
            if item.get("type") == "command_execution":
                text = item.get("command", "")
                skills.update(SKILL_PATH.findall(text))
                owner = "native_cli" if any(x in text for x in ("task.py", "trellis ", "grok-search", "tvly-hikari", "windsurf-code-search")) else "host_shell"
                result["tool_actions"].append({"type": "command_execution", "owner": owner,
                                               "exit_code": item.get("exit_code")})
            elif item.get("type") == "mcp_tool_call":
                server, tool = item.get("server"), item.get("tool")
                if isinstance(server, str) and isinstance(tool, str) and SAFE_NAME.fullmatch(server) and SAFE_NAME.fullmatch(tool):
                    result["tool_actions"].append({"type": "mcp_tool_call", "server": server, "tool": tool,
                                                   "status": item.get("status")})
                skills.update(SKILL_PATH.findall(json.dumps(item.get("arguments", {}))))
    result["skill_read_candidates"] = sorted(skills)
    if native_status != "completed":
        result["verdict"] = "blocked_native_execution"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--case", action="append", dest="case_ids")
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
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
            status = collect(case, workspace, trace, error)
            result = {"case_id": case["id"], "phase": args.phase, "turn_number": number,
                      "fixture_sha256": digest, "host": "codex-exec-ephemeral-read-only",
                      **summarize(trace, status)}
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
