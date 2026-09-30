#!/usr/bin/env python3
"""Regression tests for the native AgentMemory handoff boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "agentmemory.py"
SPEC = importlib.util.spec_from_file_location("agentmemory", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
agentmemory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agentmemory)


class FakeClient:
    project = "codex-workflow-optimization"

    def __init__(self) -> None:
        self.retained: tuple[str, str, str] | None = None
        self.read: tuple[str, str, str] | None = None

    def retain_handoff(self, handoff_id: str, capsule: str, key_fact: str) -> dict[str, str]:
        self.retained = (handoff_id, capsule, key_fact)
        content = f"Pennix formal handoff {handoff_id}.\nVerified key fact: {key_fact}\n\n{capsule}"
        return {"memory_id": "mem-1", "content": content, "content_sha256": "b" * 64, "project": self.project}

    def verify_retrieval(self, memory_id: str, content: str, handoff_id: str) -> int:
        self.read = (memory_id, content, handoff_id)
        return 1


class AgentMemoryTests(unittest.TestCase):
    def test_complete_handoff_uses_one_client_and_returns_exact_read_proof(self) -> None:
        client = FakeClient()
        original = agentmemory.AgentMemoryClient.__dict__["for_project"]
        agentmemory.AgentMemoryClient.for_project = classmethod(lambda cls, _root: client)
        try:
            with tempfile.TemporaryDirectory() as directory:
                result = agentmemory.complete_handoff(Path(directory), "20260928T000000000000Z", "capsule", "fact")
        finally:
            agentmemory.AgentMemoryClient.for_project = original
        self.assertEqual(client.retained, ("20260928T000000000000Z", "capsule", "fact"))
        self.assertEqual(client.read[0], "mem-1")
        self.assertEqual(result["retrieval_count"], 1)
        self.assertEqual(result["project"], client.project)
        self.assertNotIn("content", result)

    def test_http_contract_proves_write_and_exact_project_content_read(self) -> None:
        requests: list[tuple[str, dict[str, object] | None, str | None]] = []
        content = "Pennix formal handoff handoff-1.\nVerified key fact: fact\n\ncapsule"

        class Handler(BaseHTTPRequestHandler):
            def _respond(self, value: dict[str, object]) -> None:
                body = json.dumps(value).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                requests.append((self.path, body, self.headers.get("Authorization")))
                self._respond({"success": True, "memory": {"id": "mem-1"}})

            def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
                requests.append((self.path, None, self.headers.get("Authorization")))
                self._respond({"memory": {"id": "mem-1", "project": "project", "type": "workflow", "content": content}})

            def log_message(self, _format: str, *_args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = agentmemory.AgentMemoryClient(f"http://127.0.0.1:{server.server_port}", "test-token", "project")
            retained = client.retain_handoff("handoff-1", "capsule", "fact")
            self.assertEqual(client.verify_retrieval(retained["memory_id"], retained["content"], "handoff-1"), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(len(requests), 2)
        self.assertTrue(all(request[2] == "Bearer test-token" for request in requests))
        self.assertEqual(requests[0][0], "/agentmemory/remember")
        self.assertEqual(requests[1][0], "/agentmemory/memories/mem-1")
        self.assertEqual(requests[0][1]["project"], "project")
        self.assertEqual(requests[0][1]["type"], "workflow")

    def test_verify_retrieval_falls_back_to_bounded_exact_list(self) -> None:
        class BrokenByIdClient(agentmemory.AgentMemoryClient):
            def _request(self, method: str, path: str, body: object = None) -> dict[str, object]:
                if path == "/agentmemory/memories/mem-1":
                    raise agentmemory.AgentMemoryError("by-id unavailable")
                return {
                    "memories": [
                        {
                            "id": "mem-1",
                            "project": "project",
                            "type": "workflow",
                            "content": "Pennix formal handoff handoff-1.\n\n\ncapsule",
                        }
                    ]
                }

        client = BrokenByIdClient("http://example.invalid", "token", "project")
        self.assertEqual(
            client.verify_retrieval("mem-1", "Pennix formal handoff handoff-1.\n\n\ncapsule", "handoff-1"),
            1,
        )


if __name__ == "__main__":
    unittest.main()
