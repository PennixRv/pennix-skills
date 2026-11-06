#!/usr/bin/env python3
"""Exercise current-thread rollout discovery through the real CLI."""

import json
import os
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import closing
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/handoff.py"


class ResolveRolloutTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="handoff-resolver-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / ".trellis").mkdir()
        self.home = self.root / "Codex home #测试"
        self.home.mkdir()
        self.database = self.home / "state_5.sqlite"
        self.session = "current-thread"
        self.path = self.home / "sessions/2026/11/04/rollout-2026-11-04T14-39-06-current-thread.jsonl"
        self.path.parent.mkdir(parents=True)
        self.path.write_text(json.dumps({"type": "session_meta", "payload": {"id": self.session}}) + "\n")
        with closing(sqlite3.connect(self.database)) as database, database:
            database.execute("CREATE TABLE threads (id TEXT, rollout_path TEXT)")
            database.execute("INSERT INTO threads VALUES (?, ?)", (self.session, str(self.path)))

    def run_cli(self, **changes):
        env = {**os.environ, "CODEX_HOME": str(self.home), "CODEX_THREAD_ID": self.session}
        for key, value in changes.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return subprocess.run(
            ["python3", str(SCRIPT), "--project-root", str(self.root), "resolve-rollout"],
            env=env, text=True, capture_output=True, check=False,
        )

    def assert_rejected(self, **changes):
        result = self.run_cli(**changes)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["operation"], "resolve-rollout")
        self.assertEqual(receipt["status"], "recovery_required")
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.root / ".trellis/session-handoffs").exists())

    def test_cross_day_and_archived_paths_come_from_metadata_without_writes(self):
        for archived in (False, True):
            with self.subTest(archived=archived):
                if archived:
                    destination = self.home / "archived_sessions" / self.path.name
                    destination.parent.mkdir()
                    self.path.rename(destination)
                    self.path = destination
                    with closing(sqlite3.connect(self.database)) as database, database:
                        database.execute("UPDATE threads SET rollout_path = ?", (str(destination),))
                before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
                result = self.run_cli()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                receipt = json.loads(result.stdout)
                self.assertEqual(receipt["status"], "ready")
                self.assertEqual(receipt["rollout"], {"path": str(self.path), "session_id": self.session})
                self.assertEqual(receipt["source"], "codex-state-5")
                after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
                self.assertEqual(before, after)

    def test_missing_identity_and_exact_lookup_miss_are_rejected(self):
        for value in (None, "", "other-thread", "' OR 1=1 --"):
            with self.subTest(identity=value):
                self.assert_rejected(CODEX_THREAD_ID=value)

    def test_missing_database_does_not_create_one(self):
        self.database.unlink()
        self.assert_rejected()
        self.assertFalse(self.database.exists())

    def test_unsupported_schema_and_non_unique_match_are_rejected(self):
        with closing(sqlite3.connect(self.database)) as database, database:
            database.execute("INSERT INTO threads SELECT * FROM threads")
        self.assert_rejected()
        with closing(sqlite3.connect(self.database)) as database, database:
            database.execute("DROP TABLE threads")
        self.assert_rejected()

    def test_missing_relative_and_symbolic_rollout_paths_are_rejected(self):
        for value in (str(self.home / "missing.jsonl"), "relative.jsonl"):
            with closing(sqlite3.connect(self.database)) as database, database:
                database.execute("UPDATE threads SET rollout_path = ?", (value,))
            self.assert_rejected()
        alias = self.home / "alias.jsonl"
        alias.symlink_to(self.path)
        with closing(sqlite3.connect(self.database)) as database, database:
            database.execute("UPDATE threads SET rollout_path = ?", (str(alias),))
        self.assert_rejected()

    def test_wrong_or_invalid_first_record_is_rejected_without_echoing_it(self):
        for value in (
            {"type": "session_meta", "payload": {"id": "other-thread"}},
            {"type": "event_msg", "payload": {"id": self.session}},
            {"type": "session_meta", "payload": []},
            [],
        ):
            with self.subTest(record=value):
                self.path.write_text(json.dumps(value) + "\n")
                self.assert_rejected()
        self.path.write_text("private message body, not metadata\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("private message body", result.stdout + result.stderr)

    def test_symbolic_database_is_rejected(self):
        actual = self.home / "actual.sqlite"
        self.database.rename(actual)
        self.database.symlink_to(actual)
        self.assert_rejected()


if __name__ == "__main__":
    unittest.main()
