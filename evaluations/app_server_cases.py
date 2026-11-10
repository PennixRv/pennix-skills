"""Bounded native app-server transport for the existing evaluation runner."""
import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path

import run_codex_cases as driver


class AppServer:
    def __init__(self, workspace, codex_home, provider_args, trace, error):
        self.trace, self.events, self.sequence = trace, [], 0
        self.messages = queue.Queue()
        environment = {**os.environ, "CODEX_HOME": str(codex_home)}
        self.process = subprocess.Popen(
            ["codex", "app-server", "-c", "agents.enabled=false",
             "-c", "features.default_mode_request_user_input=true", *provider_args],
            cwd=workspace, env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=error, text=True, start_new_session=True)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        try:
            size = 0
            for line in self.process.stdout:
                size += len(line.encode())
                if size > driver.MAX_TRACE_BYTES:
                    raise ValueError("trace_limit")
                self.trace.write(line)
                self.trace.flush()
                self.messages.put(json.loads(line))
        except (ValueError, OSError) as error:
            self.messages.put(error)
        finally:
            self.messages.put(EOFError("app_server_exited"))

    def send(self, value):
        self.process.stdin.write(json.dumps(value, ensure_ascii=False) + "\n")
        self.process.stdin.flush()

    def next(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("app_server_timeout")
        try:
            message = self.messages.get(timeout=remaining)
        except queue.Empty as error:
            raise TimeoutError("app_server_timeout") from error
        if isinstance(message, BaseException):
            raise message
        self.events.append(message)
        return message

    def rpc(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + driver.TIMEOUT_SECONDS
        while True:
            message = self.next(deadline)
            if "method" not in message and message.get("id") == request_id:
                if "error" in message:
                    raise ValueError("native_rpc_error:" + json.dumps(message["error"]))
                return message["result"]
            if "id" in message and "method" in message:
                raise ValueError("unexpected_server_request:" + message["method"])

    def wait(self, method, offset=0):
        deadline = time.monotonic() + driver.TIMEOUT_SECONDS
        for message in self.events[offset:]:
            if message.get("method") == method:
                return message
        while True:
            message = self.next(deadline)
            if message.get("method") == method:
                return message

    def close(self):
        driver.stop_process(self.process)
        self.reader.join(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()


def answer_request(message, answer):
    params = message.get("params", {})
    questions = params.get("questions")
    if not isinstance(params.get("isBlocking"), bool) or not isinstance(questions, list) or not questions:
        raise ValueError("invalid_native_question")
    answers = {}
    for question in questions:
        if (not isinstance(question, dict) or not isinstance(question.get("id"), str)
                or question.get("isSecret") is True):
            raise ValueError("unsafe_native_question")
        answers[question["id"]] = {"answers": [answer]}
    return {"id": message["id"], "result": {"answers": answers}}


def reserve_extra_turn(reserve, kind):
    if reserve is None or reserve(kind) is None:
        raise ValueError("native_interaction_requires_budget")


def observe(events):
    result = {"host_blocking_requests": 0, "host_nonblocking_requests": 0, "question_answers": 0,
              "question_tool_calls": None,
              "command_items": 0, "mcp_items": 0, "completed_turns": 0,
              "compaction_observed": False, "turn_failed": False,
              "skill_declarations": [], "skill_path_observations": [], "execution_identity": None}
    for number, event in enumerate(events, 1):
        method, params = event.get("method"), event.get("params", {})
        if method == "item/tool/requestUserInput":
            # Default-mode request_user_input also has isBlocking=false in Codex.
            field = "host_blocking_requests" if params.get("isBlocking") is True else "host_nonblocking_requests"
            result[field] += 1
        elif method == "evaluation/questionTools":
            result["question_tool_calls"] = params
        elif method == "evaluation/executionIdentity":
            result["execution_identity"] = params
        elif method == "evaluation/questionAnswered":
            result["question_answers"] += 1
        elif method == "evaluation/skillDeclarations":
            result["skill_declarations"] = params
        elif method == "thread/compacted":
            result["compaction_observed"] = True
        elif method == "item/completed":
            item = params.get("item", {})
            kind = item.get("type")
            result["command_items"] += kind == "commandExecution"
            result["mcp_items"] += kind == "mcpToolCall"
            result["compaction_observed"] |= kind == "contextCompaction"
            if kind == "commandExecution":
                result["skill_path_observations"].extend(driver.skill_observations({
                    "type": "command_execution", "command": item.get("command"),
                    "exit_code": item.get("exitCode"), "aggregated_output": item.get("aggregatedOutput")}, number))
        elif method == "turn/completed":
            result["completed_turns"] += 1
            result["turn_failed"] |= params.get("turn", {}).get("status") != "completed"
    return result

def question_tools(path, codex_home, thread_id, turn_id):
    path = Path(path).resolve(strict=True)
    if not path.is_relative_to((Path(codex_home) / "sessions").resolve()):
        raise ValueError("unsafe_rollout_path")
    if path.stat().st_size > driver.MAX_TRACE_BYTES:
        raise ValueError("trace_limit")
    counts = {"request_user_input": 0, "request_user_input_async": 0}
    identity, current = False, None
    with path.open() as stream:
        for line in stream:
            event = json.loads(line)
            payload = event.get("payload", {})
            if event.get("type") == "session_meta":
                identity = payload.get("id") == thread_id
            elif event.get("type") == "turn_context":
                current = payload.get("turn_id")
            elif (current == turn_id and event.get("type") == "response_item"
                  and payload.get("type") == "function_call" and payload.get("name") in counts):
                counts[payload["name"]] += 1
    if not identity:
        raise ValueError("rollout_identity_mismatch")
    return counts


def execution_identity(path, codex_home, thread_id, turn_id):
    # Use the native rollout, never infer execution settings from an evaluation label.
    question_tools(path, codex_home, thread_id, turn_id)
    result, provider = None, None
    with Path(path).open() as stream:
        for line in stream:
            event = json.loads(line)
            payload = event.get("payload", {})
            if event.get("type") == "session_meta":
                provider = payload.get("model_provider")
            if event.get("type") == "turn_context" and payload.get("turn_id") == turn_id:
                result = {key: payload.get(key) for key in ("model", "model_provider", "effort")}
    if result is not None and result["model_provider"] is None:
        result["model_provider"] = provider
    return result


def collect(case, workspace, trace_path, error_path, codex_home, provider_args,
            *, resume_thread=None, compact=False, reserve_model_turn=None):
    app = None
    thread_id = None
    try:
        with trace_path.open("x", encoding="utf-8") as trace, error_path.open("x") as error:
            app = AppServer(workspace, codex_home, provider_args, trace, error)
            app.rpc("initialize", {"clientInfo": {"name": "pennix-skill-evaluation", "version": "1"},
                                   "capabilities": {"experimentalApi": True}})
            app.send({"method": "initialized"})
            listing = app.rpc("skills/list", {"cwds": [str(workspace)], "forceReload": True})
            declared = []
            for entry in listing["data"]:
                if entry.get("errors"):
                    raise ValueError("native_skill_discovery_errors")
                declared.extend({key: skill[key] for key in ("name", "path", "scope")} for skill in entry["skills"])
            marker = {"method": "evaluation/skillDeclarations", "params": declared}
            trace.write(json.dumps(marker, ensure_ascii=False) + "\n")
            app.events.append(marker)
            policy = driver.case_policy(case, workspace)
            params = {"cwd": str(workspace), "approvalPolicy": "never", "sandbox": "read-only"}
            if resume_thread:
                started = app.rpc("thread/resume", {**params, "threadId": resume_thread})
            else:
                started = app.rpc("thread/start", params)
            thread_id = started["thread"]["id"]
            if compact:
                if not resume_thread:
                    raise ValueError("compaction_requires_existing_thread")
                reserve_extra_turn(reserve_model_turn, "compact")
                offset = len(app.events)
                app.rpc("thread/compact/start", {"threadId": thread_id})
                app.wait("turn/completed", offset)
            offset = len(app.events)
            turn = app.rpc("turn/start", {"threadId": thread_id,
                                  "sandboxPolicy": policy,
                                  "input": [{"type": "text", "text": driver.case_prompt(case, workspace)}]})
            deadline = time.monotonic() + driver.TIMEOUT_SECONDS
            cursor = offset
            while True:
                message = app.events[cursor] if cursor < len(app.events) else app.next(deadline)
                cursor += 1
                method = message.get("method")
                if "id" in message and method:
                    if method != "item/tool/requestUserInput" or not case.get("answer"):
                        raise ValueError("unexpected_server_request:" + method)
                    response = answer_request(message, case["answer"])
                    reserve_extra_turn(reserve_model_turn, "question-answer")
                    app.send(response)
                    marker = {"method": "evaluation/questionAnswered", "params": {}}
                    trace.write(json.dumps(marker) + "\n")
                    app.events.insert(cursor, marker)
                elif method == "turn/completed":
                    failed = message.get("params", {}).get("turn", {}).get("status") != "completed"
                    counts = question_tools(started["thread"]["path"], codex_home, thread_id, turn["turn"]["id"])
                    marker = {"method": "evaluation/questionTools", "params": counts}
                    trace.write(json.dumps(marker) + "\n")
                    app.events.append(marker)
                    marker = {"method": "evaluation/executionIdentity", "params": execution_identity(
                        started["thread"]["path"], codex_home, thread_id, turn["turn"]["id"])}
                    trace.write(json.dumps(marker) + "\n")
                    app.events.append(marker)
                    return ("native_failure" if failed else "completed"), thread_id, observe(app.events)
    except (TimeoutError, ValueError, OSError, EOFError) as error:
        with error_path.open("a") as stream:
            stream.write(type(error).__name__ + ": " + str(error) + "\n")
        return "native_failure", thread_id, observe(app.events if app else [])
    finally:
        if app:
            app.close()
