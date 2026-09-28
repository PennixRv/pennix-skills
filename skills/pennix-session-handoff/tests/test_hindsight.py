#!/usr/bin/env python3
"""Regression tests for the native Hindsight handoff boundary."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hindsight.py"
SPEC = importlib.util.spec_from_file_location("hindsight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
hindsight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hindsight)


class FakeClient:
    bank_id = "pennix-project-" + "a" * 24

    def __init__(self) -> None:
        self.retained: tuple[str, str, str] | None = None
        self.waited: str | None = None
        self.read: tuple[str, str] | None = None

    def retain_handoff(self, handoff_id: str, capsule: str, key_fact: str) -> dict[str, str]:
        self.retained = (handoff_id, capsule, key_fact)
        return {
            "document_id": "pennix-handoff-" + handoff_id,
            "operation_id": "operation-1",
            "content_sha256": "b" * 64,
        }

    def wait_operation(self, operation_id: str) -> str:
        self.waited = operation_id
        return "completed"

    def verify_retrieval(self, document_id: str, handoff_id: str) -> int:
        self.read = (document_id, handoff_id)
        return 1


class HindsightTests(unittest.TestCase):
    def test_complete_handoff_uses_one_client_and_returns_retrieval_proof(self) -> None:
        client = FakeClient()
        original = hindsight.HindsightClient.__dict__["for_project"]
        hindsight.HindsightClient.for_project = classmethod(lambda cls, _root: client)
        try:
            with tempfile.TemporaryDirectory() as directory:
                result = hindsight.complete_handoff(Path(directory), "20260928T000000000000Z", "capsule", "fact")
        finally:
            hindsight.HindsightClient.for_project = original
        self.assertEqual(client.retained, ("20260928T000000000000Z", "capsule", "fact"))
        self.assertEqual(client.waited, "operation-1")
        self.assertEqual(client.read, ("pennix-handoff-20260928T000000000000Z", "20260928T000000000000Z"))
        self.assertEqual(result["operation_status"], "completed")
        self.assertEqual(result["retrieval_count"], 1)
        self.assertEqual(result["bank_id"], client.bank_id)

    def test_http_contract_proves_write_operation_and_same_document_retrieval(self) -> None:
        requests: list[tuple[str, dict[str, object] | None, str | None]] = []

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
                if self.path.endswith("/memories"):
                    self._respond({"operation_id": body["operation_id"]})
                    return
                handoff_id = body["query"]
                self._respond({
                    "results": [{
                        "document_id": "pennix-handoff-" + handoff_id,
                        "metadata": {"handoff_id": handoff_id},
                        "text": "retrieved handoff fact",
                    }],
                })

            def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
                requests.append((self.path, None, self.headers.get("Authorization")))
                self._respond({"status": "completed"})

            def log_message(self, _format: str, *_args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = hindsight.HindsightClient(
                f"http://127.0.0.1:{server.server_port}",
                "test-token",
                "pennix-project-" + "a" * 24,
            )
            with patch.object(hindsight.time, "sleep", return_value=None):
                retained = client.retain_handoff("handoff-1", "capsule", "fact")
                self.assertEqual(client.wait_operation(retained["operation_id"]), "completed")
                self.assertEqual(client.verify_retrieval(retained["document_id"], "handoff-1"), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(len(requests), 3)
        self.assertTrue(all(request[2] == "Bearer test-token" for request in requests))
        self.assertEqual(requests[0][0], "/v1/default/banks/pennix-project-" + "a" * 24 + "/memories")
        self.assertEqual(requests[1][0], requests[0][0].replace("/memories", "/operations/" + retained["operation_id"]))
        self.assertEqual(requests[2][0], requests[0][0] + "/recall")

    def test_retrieval_and_operation_failures_never_pass_as_proof(self) -> None:
        client = hindsight.HindsightClient(
            "http://127.0.0.1:1",
            "test-token",
            "pennix-project-" + "a" * 24,
        )
        with patch.object(client, "_request", return_value={
            "results": [{"document_id": "other", "metadata": {"handoff_id": "other"}, "text": "fact"}],
        }):
            with self.assertRaises(hindsight.HindsightError):
                client.verify_retrieval("pennix-handoff-handoff-1", "handoff-1")
        with patch.object(client, "_request", return_value={"status": "failed"}):
            with self.assertRaises(hindsight.HindsightError):
                client.wait_operation("operation-1")
        with self.assertRaises(hindsight.HindsightError):
            client.wait_operation("operation-1", timeout_seconds=0)


if __name__ == "__main__":
    unittest.main()
