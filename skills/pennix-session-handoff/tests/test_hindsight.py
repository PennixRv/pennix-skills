#!/usr/bin/env python3
"""Regression tests for the native Hindsight handoff boundary."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


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

    def verify_readback(self, document_id: str, handoff_id: str) -> int:
        self.read = (document_id, handoff_id)
        return 1


class HindsightTests(unittest.TestCase):
    def test_complete_handoff_uses_one_client_and_returns_readback_proof(self) -> None:
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
        self.assertEqual(result["readback_count"], 1)
        self.assertEqual(result["bank_id"], client.bank_id)


if __name__ == "__main__":
    unittest.main()
