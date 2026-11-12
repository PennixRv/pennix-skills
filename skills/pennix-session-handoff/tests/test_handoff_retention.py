"""Native exact retention, historical reads and failure recovery."""

import json
import fcntl
import shutil
import unittest
from pathlib import Path
from unittest import mock

import test_handoff as fixtures

handoff = fixtures.handoff
storage = handoff.storage


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.HandoffTests()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.make_git_root()
        self.addCleanup(shutil.rmtree, self.root)
        result = self.fixture.run_cli(self.root, "write", "--request", str(self.fixture.make_request(self.root)), "--explicit-user-request")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.relative = self.fixture.handoff_path_from(result.stdout)
        self.core = self.root / self.relative
        self.identifier = self.core.parent.name
        self.core.with_name("session-handoff-prompt.md").write_text("完整提示😀\r\n", newline="")
        handoff.lifecycle_prepare(self.root, self.relative, "core_only")
        handoff.lifecycle_seal(self.root, self.relative, explicit=True)
        handoff._append_event(self.root, self.identifier, "admit", {"source": "boundary_sealed", "target": "reconciled", "retention": "archive_eligible"}, ["target=session:target"])
        self.originals = {p.name: p.read_bytes() for p in self.core.parent.iterdir()}

    def preview(self, action):
        return handoff.lifecycle_retention(self.root, action, self.relative, self.identifier)[1]

    def execute(self, action):
        preview = self.preview(action)
        self.assertTrue(preview["eligible"], preview["blockers"])
        return handoff.lifecycle_retention(self.root, action, self.relative, self.identifier, preview["digest"])[1]

    def test_id_only_is_preview_stale_digest_is_rejected_and_roundtrip_is_lossless(self):
        first = self.preview("archive")
        self.assertEqual(first["status"], "preview")
        self.assertFalse(storage.zip_path(self.root, self.identifier).exists())
        prompt = self.core.with_name("session-handoff-prompt.md")
        prompt.write_bytes(prompt.read_bytes() + b"changed\n")
        with self.assertRaisesRegex(handoff.ContractError, "preview changed"):
            handoff.lifecycle_retention(self.root, "archive", self.relative, self.identifier, first["digest"])
        prompt.write_bytes(self.originals[prompt.name])
        self.execute("archive")
        self.assertTrue(self.core.exists())
        self.assertEqual(self.execute("archive")["status"], "idempotent")
        self.execute("purge")
        self.assertFalse(self.core.exists())
        result = self.fixture.run_cli(self.root, "validate", "--handoff", self.relative)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for view in ("core", "history", "prompt"):
            offset, parts = 0, []
            while True:
                page = handoff.read_view(self.root, self.relative, view, offset, 11)
                parts.append(page["text"])
                if page["complete"]:
                    break
                offset = page["next_offset"]
            if view == "prompt":
                self.assertEqual("".join(parts).encode(), self.originals[prompt.name])
        self.execute("restore")
        for name, raw in self.originals.items():
            actual = (self.core.parent / name).read_bytes()
            self.assertTrue(actual.startswith(raw) if name == storage.LIFECYCLE else actual == raw)
        self.assertTrue(storage.zip_path(self.root, self.identifier).exists())
        with mock.patch.object(handoff, "_ownership_call") as native:
            with self.assertRaisesRegex(handoff.ContractError, "archived"):
                handoff.ownership_operation(self.root, "claim", self.relative, explicit=True, expected_generation=0)
            native.assert_not_called()

    def test_archive_failure_before_publication_preserves_source_and_no_committed_result(self):
        with mock.patch.object(handoff, "_publish_storage", side_effect=OSError("injected before publication")):
            with self.assertRaises(OSError):
                self.execute("archive")
        self.assertFalse(storage.zip_path(self.root, self.identifier).exists())
        self.assertEqual({p.name: p.read_bytes() for p in self.core.parent.iterdir()}, self.originals)

    def test_archive_commit_survives_mirror_failure_and_repairs_exact_prefix(self):
        native = handoff.os.replace
        def fail_mirror(source, destination):
            if Path(destination) == self.core.parent / storage.LIFECYCLE:
                raise OSError("injected mirror failure")
            return native(source, destination)
        with mock.patch.object(handoff.os, "replace", side_effect=fail_mirror):
            with self.assertRaises(OSError):
                self.execute("archive")
        self.assertTrue(storage.zip_path(self.root, self.identifier).is_file())
        inspection = handoff.inspect_handoff(self.root, self.relative)
        self.assertEqual(inspection["historical_lifecycle"]["state"]["retention"], "archived")
        self.execute("archive")
        self.assertEqual(handoff._state(handoff._read_events(self.core.parent / storage.LIFECYCLE, self.identifier))["retention"], "archived")

    def test_legacy_embedded_history_is_readonly_and_never_upgraded_for_storage(self):
        payload = json.loads(self.core.read_text())
        payload["schema_version"] = 9
        payload["conversation"] = {"original": "中文😀" * 1000}
        self.core.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        original = self.core.read_bytes()
        read = handoff.read_view(self.root, self.relative, "core", 0, 100000)
        self.assertFalse(read["admission_eligible"])
        self.assertEqual(read["text"].encode(), original)
        inspection = handoff.inspect_handoff(self.root, self.relative)
        self.assertEqual(inspection["qualification"]["kind"], "historical_readonly")
        self.execute("archive")
        self.execute("purge")
        self.assertEqual(handoff.read_view(self.root, self.relative, "core", 0, 100000)["text"].encode(), original)
        result = self.fixture.run_cli(self.root, "validate", "--handoff", self.relative)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_historical_retention_observes_native_ownership_without_current_phase_projection(self):
        payload = json.loads(self.core.read_text())
        payload["schema_version"] = 9
        payload["work_context"]["task"] = {"id": "old-task", "path": ".trellis/tasks/old-task"}
        self.core.write_text(json.dumps(payload))
        (self.root / ".trellis/scripts/task.py").write_text(
            "import json, pathlib, sys\n"
            "assert sys.argv[1:3] == ['transfer', 'status']\n"
            "if '--include-current' in sys.argv:\n"
            "    print(json.dumps({'code': 'TASK_CONTINUITY_WITHHELD', 'reason': 'task phase classification or route is invalid'}))\n"
            "    raise SystemExit(1)\n"
            "value = json.loads(pathlib.Path('native-observation.json').read_text())\n"
            "print(json.dumps(value))\n"
            "raise SystemExit(1 if value['status'] == 'unknown' else 0)\n"
        )
        for observation, eligible in (
            ({"status": "absent"}, True),
            ({"status": "claimed", "package_id": self.identifier}, False),
            ({"status": "unknown", "reason": "ownership unreadable"}, False),
        ):
            with self.subTest(observation=observation):
                (self.root / "native-observation.json").write_text(json.dumps(observation))
                result = handoff.inspect_handoff(self.root, self.relative)
                self.assertEqual(result["qualification"]["eligible"], eligible, result)
                self.assertEqual(result["current_task_observation"]["status"], observation["status"])

    def test_purge_rename_delete_and_final_publication_failures_retain_exact_recovery(self):
        self.execute("archive")
        with mock.patch.object(handoff.os, "rename", side_effect=OSError("injected rename failure")):
            with self.assertRaises(OSError):
                self.execute("purge")
        self.assertTrue(self.core.is_file())
        self.assertEqual(storage.verify(storage.zip_path(self.root, self.identifier), self.identifier)["operation"]["status"], "intent")
        with mock.patch.object(handoff, "_purge_tombstone", side_effect=OSError("injected removal failure")):
            with self.assertRaisesRegex(handoff.ContractError, "intent retained"):
                self.execute("purge")
        self.assertFalse(self.core.exists())
        self.assertIsNotNone(self.preview("purge")["tombstone"])
        native = handoff._publish_storage
        calls = 0
        def fail_completion(candidate, archive):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected completion publication failure")
            return native(candidate, archive)
        with mock.patch.object(handoff, "_publish_storage", side_effect=fail_completion):
            with self.assertRaisesRegex(handoff.ContractError, "intent retained"):
                self.execute("purge")
        self.assertFalse(self.core.parent.exists())
        self.assertEqual(storage.verify(storage.zip_path(self.root, self.identifier), self.identifier)["operation"]["status"], "intent")
        self.execute("purge")
        self.assertEqual(storage.verify(storage.zip_path(self.root, self.identifier), self.identifier)["operation"]["status"], "complete")

    def test_partial_tombstone_delete_can_restore_then_finish_original_and_new_sources(self):
        self.execute("archive")
        native_unlink, calls = Path.unlink, 0
        def partial_delete(path, *args, **kwargs):
            nonlocal calls
            if ".purge-" in str(path):
                calls += 1
                if calls == 2:
                    raise OSError("injected partial deletion")
            return native_unlink(path, *args, **kwargs)
        with mock.patch.object(Path, "unlink", partial_delete):
            with self.assertRaisesRegex(handoff.ContractError, "intent retained"):
                self.execute("purge")
        old_tombstone = self.preview("restore")["recovery_intent"]["tombstone"]
        self.assertTrue((self.root / old_tombstone).is_dir())
        self.execute("restore")
        self.assertTrue(self.core.is_file())
        self.assertTrue((self.root / old_tombstone).is_dir())
        preview = self.preview("purge")
        self.assertEqual(preview["pending_tombstones"][0]["path"], old_tombstone)
        self.execute("purge")
        self.assertFalse(self.core.parent.exists())
        self.assertFalse((self.root / old_tombstone).exists())

    def test_restore_publication_failure_never_changes_retained_zip(self):
        self.execute("archive")
        self.execute("purge")
        archive = storage.zip_path(self.root, self.identifier)
        before = archive.read_bytes()
        with mock.patch.object(handoff.os, "rename", side_effect=OSError("injected restore failure")):
            with self.assertRaises(OSError):
                self.execute("restore")
        self.assertEqual(archive.read_bytes(), before)
        self.assertFalse(self.core.parent.exists())
        self.execute("restore")
        self.assertEqual(archive.read_bytes(), before)

    def test_unknown_tombstone_member_blocks_exit_without_losing_archive(self):
        self.execute("archive")
        with mock.patch.object(handoff, "_purge_tombstone", side_effect=OSError("pause exit")):
            with self.assertRaises(handoff.ContractError):
                self.execute("purge")
        tombstone = self.root / self.preview("purge")["recovery_intent"]["tombstone"]
        (tombstone / "user-note.txt").write_text("preserve")
        with self.assertRaisesRegex(handoff.ContractError, "intent retained"):
            self.execute("purge")
        self.assertEqual((tombstone / "user-note.txt").read_text(), "preserve")
        storage.verify(storage.zip_path(self.root, self.identifier), self.identifier)

    def test_native_ownership_commit_is_reconciled_without_repeating_task_mutation(self):
        root = self.fixture.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        written = self.fixture.run_cli(root, "write", "--request", str(self.fixture.make_request(root)), "--explicit-user-request")
        relative = self.fixture.handoff_path_from(written.stdout)
        core, identifier = root / relative, Path(relative).parent.name
        handoff.lifecycle_prepare(root, relative, "core_only")
        state = {"status": "absent", "generation": 0}
        mutations = []
        def native(_root, operation, *_args, **_kwargs):
            with (root / ".trellis/.runtime/handoff.lock").open("a+b") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            if operation != "status":
                mutations.append(operation)
                state.update(status="quiescing", generation=1, package_id=identifier, package_digest=storage.fingerprint(core)[-1], source_session_id="source", continuity_digest="c" * 64)
            return dict(state)
        intent = core.parent / storage.OWNERSHIP_INTENT
        with mock.patch.object(handoff, "_ownership_call", side_effect=native):
            with mock.patch.object(handoff, "_ownership_event", side_effect=OSError("injected receipt failure")):
                with self.assertRaises(OSError):
                    handoff.ownership_operation(root, "quiesce", relative, explicit=True)
            self.assertTrue(intent.is_file())
            self.assertFalse(handoff.inspect_handoff(root, relative)["qualification"]["eligible"])
            result = handoff.ownership_operation(root, "quiesce", relative, explicit=True)
        self.assertEqual(result["ownership"]["status"], "quiescing")
        self.assertEqual(mutations, ["quiesce"])
        self.assertFalse(intent.exists())

    def test_definite_native_refusal_does_not_leave_a_false_operation_blocker(self):
        root = self.fixture.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        written = self.fixture.run_cli(root, "write", "--request", str(self.fixture.make_request(root)), "--explicit-user-request")
        relative = self.fixture.handoff_path_from(written.stdout)
        core = root / relative
        handoff.lifecycle_prepare(root, relative, "core_only")
        receipt = handoff._lifecycle_path(root, core.parent.name)
        before = receipt.read_bytes()
        def native(_root, operation, *_args, **_kwargs):
            if operation != "status":
                raise handoff.ContractError("native CAS rejected the stale generation")
            return {"status": "absent", "generation": 0}
        with mock.patch.object(handoff, "_ownership_call", side_effect=native):
            with self.assertRaisesRegex(handoff.ContractError, "CAS rejected"):
                handoff.ownership_operation(root, "quiesce", relative, explicit=True)
        self.assertFalse((core.parent / storage.OWNERSHIP_INTENT).exists())
        self.assertEqual(receipt.read_bytes(), before)

    def test_release_receipt_failure_recovers_from_native_absence_and_direct_pointer(self):
        root = self.fixture.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        written = self.fixture.run_cli(root, "write", "--request", str(self.fixture.make_request(root)), "--explicit-user-request")
        relative = self.fixture.handoff_path_from(written.stdout)
        core = root / relative
        handoff.lifecycle_prepare(root, relative, "core_only")
        state = {"status": "sealed", "generation": 2}
        mutations = []
        def native(_root, operation, *_args, **_kwargs):
            if operation != "status":
                mutations.append(operation)
                state.update(status="absent", generation=0)
                return {"status": "released", "generation": 2}
            return dict(state)
        with mock.patch.object(handoff, "_ownership_call", side_effect=native):
            with mock.patch.object(handoff, "_ownership_event", side_effect=OSError("receipt failure")):
                with self.assertRaises(OSError):
                    handoff.ownership_operation(root, "release", relative, explicit=True, expected_generation=2)
            result = handoff.ownership_operation(root, "release", relative, explicit=True, expected_generation=2)
        self.assertEqual(result["ownership"]["status"], "release_observed")
        self.assertEqual(mutations, ["release"])
        self.assertFalse((core.parent / storage.OWNERSHIP_INTENT).exists())

    def test_current_prompt_is_validated_before_retention(self):
        self.core.with_name("session-handoff-prompt.md").write_bytes(b"\xff")
        with self.assertRaisesRegex(handoff.ContractError, "prompt is unreadable"):
            self.preview("archive")
        self.assertFalse(storage.zip_path(self.root, self.identifier).exists())

    def test_only_native_recovery_history_can_fence_a_previous_claim_intent(self):
        root = self.fixture.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        written = self.fixture.run_cli(root, "write", "--request", str(self.fixture.make_request(root)), "--explicit-user-request")
        relative = self.fixture.handoff_path_from(written.stdout)
        core, identifier = root / relative, Path(relative).parent.name
        handoff.lifecycle_prepare(root, relative, "core_only")
        intent_path = core.parent / storage.OWNERSHIP_INTENT
        package_digest = storage.fingerprint(core)[-1]
        intent = {"schema_version": 1, "kind": "pennix-handoff-ownership-intent", "handoff_id": identifier, "operation": "claim", "session": "previous-target", "package_digest": package_digest, "expected_generation": 2, "expected_continuity_digest": None, "native_before_digest": "a" * 64, "receipt_fingerprint": storage.fingerprint(handoff._lifecycle_path(root, identifier), content=False)}
        storage.atomic_record(intent_path, intent)
        state = {"status": "ready", "generation": 4, "package_id": identifier, "package_digest": package_digest, "continuity_digest": "c" * 64}
        mutations = []
        def native(_root, operation, *_args, **_kwargs):
            if operation != "status":
                mutations.append(operation)
                return {**state, "status": "claimed", "generation": 5, "target_session_id": "source"}
            return dict(state)
        with mock.patch.object(handoff, "_ownership_call", side_effect=native):
            with self.assertRaisesRegex(handoff.ContractError, "requires recovery"):
                handoff.ownership_operation(root, "claim", relative, explicit=True, expected_generation=4)
            self.assertTrue(intent_path.exists())
            self.assertEqual(mutations, [])
            state["recovery_history"] = [{"generation": 3, "status": "claimed", "target_session_id": "previous-target", "requested_by": "source", "reason": "explicit native recovery"}]
            result = handoff.ownership_operation(root, "claim", relative, explicit=True, expected_generation=4)
        self.assertEqual(result["ownership"]["generation"], 5)
        self.assertEqual(mutations, ["claim"])
        self.assertFalse(intent_path.exists())


if __name__ == "__main__":
    unittest.main()
