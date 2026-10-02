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
from urllib.parse import parse_qs, urlsplit


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "agentmemory.py"
SPEC = importlib.util.spec_from_file_location("agentmemory", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
agentmemory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agentmemory)


class AgentMemoryTests(unittest.TestCase):
    def test_unknown_post_reconciles_second_page_without_repeating_write(self) -> None:
        content = agentmemory.handoff_content("handoff-1", "capsule", "fact")

        class InterruptedClient(agentmemory.AgentMemoryClient):
            posts = 0
            total = 101

            def _request(self, method, path, body=None):
                if method == "POST":
                    self.posts += 1
                    raise agentmemory.AgentMemoryError("response lost after commit")
                offset = int(parse_qs(urlsplit(path).query)["offset"][0])
                records = [{"id": "other", "content": "other"}] * 100 if offset == 0 else [{"id": "mem-1", "content": content, "type": "workflow", "project": "project"}]
                return {"memories": records, "total": self.total, "offset": offset}

        client = InterruptedClient("http://example.invalid", "token", "project")
        self.assertEqual(client.retain_handoff("handoff-1", "capsule", "fact")["memory_id"], "mem-1")
        self.assertEqual(client.retain_handoff("handoff-1", "capsule", "fact", reconcile_only=True)["memory_id"], "mem-1")
        self.assertEqual(client.posts, 1)
        client.total = 1000
        with self.assertRaises(agentmemory.AgentMemoryError):
            client.retain_handoff("handoff-1", "capsule", "fact", reconcile_only=True)
        self.assertEqual(client.posts, 1)

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
                    "total": 1,
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
