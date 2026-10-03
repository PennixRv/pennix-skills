#!/usr/bin/env python3
"""Regression tests for the native Cognee handoff boundary."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "cognee.py"
SPEC = importlib.util.spec_from_file_location("cognee", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
cognee = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cognee)


class CogneeTests(unittest.TestCase):
    def test_unknown_post_reconciles_without_repeating_write(self) -> None:
        content = cognee.handoff_content("handoff-1", "capsule", "fact")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()

        class InterruptedClient(cognee.CogneeClient):
            posts = 0

            def _multipart(self, fields, raw_text):
                self.posts += 1
                raise cognee.CogneeError("response lost after commit")

            def _request(self, method, path, body=None):
                self.assertEqual(method, "GET")
                offset = int(parse_qs(urlsplit(path).query)["offset"][0])
                records = [{"id": f"other-{index}"} for index in range(1000)] if offset == 0 else [
                    {"id": "data-1", "externalMetadata": {"pennix_content_sha256": digest}}
                ]
                return records

            def assertEqual(self, first, second):
                if first != second:
                    raise AssertionError((first, second))

        client = InterruptedClient("http://example.invalid", "token", "project", dataset_id="dataset-1")
        self.assertEqual(client.retain_handoff("handoff-1", "capsule", "fact")["data_id"], "data-1")
        self.assertEqual(client.retain_handoff("handoff-1", "capsule", "fact", reconcile_only=True)["data_id"], "data-1")
        self.assertEqual(client.posts, 1)

    def test_http_contract_proves_write_cognify_and_exact_raw_read(self) -> None:
        requests: list[tuple[str, bytes | None, str | None]] = []
        content = cognee.handoff_content("handoff-1", "capsule", "fact")

        class Handler(BaseHTTPRequestHandler):
            def _respond_json(self, value: object) -> None:
                body = json.dumps(value).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length)
                requests.append((self.path, body, self.headers.get("X-Api-Key")))
                if self.path == "/api/v1/cognify":
                    self._respond_json({"status": "completed"})
                else:
                    self._respond_json({"pipeline_run_id": "run-1", "status": "completed"})

            def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
                requests.append((self.path, None, self.headers.get("X-Api-Key")))
                if self.path == "/api/v1/datasets":
                    self._respond_json([{"id": "dataset-1", "name": "project"}])
                elif self.path.startswith("/api/v1/datasets/dataset-1/data?"):
                    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
                    self._respond_json([{"id": "data-1", "externalMetadata": {"pennix_content_sha256": digest}}])
                elif self.path == "/api/v1/datasets/dataset-1/data/data-1/raw":
                    body = content.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(404)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = cognee.CogneeClient(f"http://127.0.0.1:{server.server_port}", "test-token", "project")
            retained = client.retain_handoff("handoff-1", "capsule", "fact")
            self.assertEqual(retained["data_id"], "data-1")
            self.assertEqual(client.verify_retrieval(retained["data_id"], retained["content"], "handoff-1"), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        self.assertEqual(len(requests), 6)
        self.assertTrue(all(request[2] == "test-token" for request in requests))
        self.assertEqual(requests[0][0], "/api/v1/add")
        self.assertIn(b"name=\"datasetName\"", requests[0][1])
        self.assertIn(b"name=\"external_metadata\"", requests[0][1])
        self.assertEqual(requests[1][0], "/api/v1/datasets")
        self.assertEqual(requests[2][0], "/api/v1/cognify")
        self.assertEqual(requests[3][0], "/api/v1/datasets/dataset-1/data?limit=1000&offset=0")
        self.assertEqual(requests[4][0], "/api/v1/datasets/dataset-1/data/data-1/raw")
        self.assertEqual(requests[5][0], "/api/v1/datasets/dataset-1/data?limit=1000&offset=0")


if __name__ == "__main__":
    unittest.main()
