#!/usr/bin/env python3
"""Regression tests for the Pennix session-handoff helper."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/handoff.py"
SPEC = importlib.util.spec_from_file_location("handoff", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


class HandoffTests(unittest.TestCase):
    def make_root(self, task_dir: str | None = None) -> Path:
        root = Path(tempfile.mkdtemp(prefix="pennix-session-handoff-"))
        (root / ".trellis/scripts").mkdir(parents=True)
        selected = "None" if task_dir is None else repr({"id": "fixture-task", "dir": task_dir, "status": "in_progress"})
        (root / ".trellis/scripts/task.py").write_text("import json\nprint(json.dumps({'current_task': " + selected + "}))\n", encoding="utf-8")
        return root

    def make_git_root(self, *, with_task: bool = False) -> Path:
        root = self.make_root(".trellis/tasks/demo" if with_task else None)
        (root / "evidence.md").write_text("verified fixture\n", encoding="utf-8")
        if with_task:
            task_dir = root / ".trellis/tasks/demo"
            task_dir.mkdir(parents=True)
            (task_dir / "prd.md").write_text("continue fixture\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        return root

    def make_rollout(self) -> Path:
        handle = tempfile.NamedTemporaryFile("wb", suffix=".jsonl", delete=False)
        path = Path(handle.name)
        records = [
            {"type": "event_msg", "timestamp": "2026-09-04T01:00:00Z", "payload": {"type": "user_message", "message": "审查 `pennix-session-handoff`，不要复制 rollout。"}},
            {"type": "response_item", "timestamp": "2026-09-04T01:00:01Z", "payload": {"type": "reasoning", "encrypted_content": "must not enter handoff"}},
            {"type": "compacted", "timestamp": "2026-09-04T01:00:01Z", "payload": {"type": "compacted", "replacement_history": ["must not be expanded"]}},
            {"type": "event_msg", "timestamp": "2026-09-04T01:00:02Z", "payload": {"type": "agent_message", "message": "已完成本地核验，下一步运行测试。"}},
            {"type": "response_item", "timestamp": "2026-09-04T01:00:03Z", "payload": {"type": "function_call", "name": "shell", "call_id": "call-1", "arguments": "hidden"}},
            {"type": "response_item", "timestamp": "2026-09-04T01:00:04Z", "payload": {"type": "function_call_output", "call_id": "call-1", "output": "passed"}},
            {"type": "event_msg", "timestamp": "2026-09-04T01:00:05Z", "payload": {"type": "user_message", "message": "`pennix-session-handoff` 已确认，继续提交。"}},
            {"type": "event_msg", "timestamp": "2026-09-04T01:00:06Z", "payload": {"type": "user_message", "message": "token th-abcdefghijklmnopqrstuvwx 不应出现在交接中。"}},
        ]
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n")
            if record is records[1]:
                handle.write(b"\0" * 16 + b"\n")
        handle.close()
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def run_cli(self, root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["python3", str(SCRIPT), "--project-root", str(root), *arguments], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)

    def make_request(self, root: Path, rollout: Path | None = None, capsule: str = "") -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        request = Path(handle.name)
        json.dump({
            "session_label": "fixture handoff", "facts": ["fixture task and Git state were checked"],
            "evidence_paths": ["evidence.md"], "next_action": "continue the fixture task", "blockers": [], "risks": [],
            "validation": [{"command": "fixture check", "result": "passed"}],
            "rollout": {"path": str(rollout or self.make_rollout()), "session_id": "fixture-session"},
            "memory_projection": {"semantic_capsule": capsule, "local": [], "archive_refs": [], "openviking": []},
        }, handle, ensure_ascii=False)
        handle.write("\n")
        handle.close()
        self.addCleanup(request.unlink, missing_ok=True)
        return request

    @staticmethod
    def handoff_path_from(stdout: str) -> str:
        return json.loads(stdout)["handoff_path"]

    def test_task_symlink_is_rejected_before_resolve(self) -> None:
        root = self.make_root(".trellis/tasks/link")
        try:
            real = root / ".trellis/tasks/real"
            real.mkdir(parents=True)
            (real / "prd.md").write_text("fixture\n", encoding="utf-8")
            (root / ".trellis/tasks/link").symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(handoff.ContractError, "symbolic path"):
                handoff._task_snapshot(root)
        finally:
            shutil.rmtree(root)

    def test_cli_requires_explicit_request_before_writing(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        request = self.make_request(root)
        result = self.run_cli(root, "write", "--request", str(request))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('"status": "recovery_required"', result.stdout)
        self.assertFalse((root / handoff.HANDOFFS).exists())

    def test_cli_write_validate_and_rollout_candidates(self) -> None:
        root = self.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        destination = root / relative
        self.assertRegex(relative, r"^\.trellis/session-handoffs/\d{8}T\d{12}Z/session-handoff\.json$")
        self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(destination.parent.stat().st_mode), 0o700)
        payload = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 6)
        self.assertNotIn("integrity", payload)
        self.assertEqual(payload["handoff_id"], Path(relative).parts[-2])
        self.assertTrue(any(item["kind"] == "user" for item in payload["conversation"]["candidates"]))
        self.assertEqual([item["state"] for item in payload["conversation"]["timeline"]], ["corrected", "accepted"])
        self.assertEqual(payload["conversation"]["timeline"][1]["supersedes_event_index"], 1)
        self.assertEqual(payload["conversation"]["coverage"]["omissions"][0]["kind"], "nul_padding_record")
        self.assertEqual(payload["conversation"]["coverage"]["excluded"]["compacted"], 1)
        self.assertEqual(len(payload["conversation"]["coverage"]["compacted_spans"]), 1)
        self.assertNotIn("must not enter handoff", json.dumps(payload, ensure_ascii=False))
        self.assertNotIn("th-abcdefghijklmnopqrstuvwx", json.dumps(payload, ensure_ascii=False))
        validated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(json.loads(validated.stdout)["status"], "ready")

    def test_observation_preserves_distinct_proof_references(self) -> None:
        normalized = handoff.validate_observation({
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary-proof"},
            "source_session": {"status": "verified", "identity": "source-session"},
            "capsule": {"status": "verified", "proof_ref": "capsule-proof"},
            "archive": {"status": "verified", "proof_ref": "archive-proof"},
            "task": {"status": "completed", "completion_artifact": "task-proof"},
            "memory": {"status": "verified", "proof_ref": "memory-proof"},
        })
        self.assertEqual(normalized["boundary"]["proof_ref"], "boundary-proof")
        self.assertEqual(normalized["capsule"]["proof_ref"], "capsule-proof")
        self.assertEqual(normalized["archive"]["proof_ref"], "archive-proof")
        self.assertEqual(normalized["memory"]["proof_ref"], "memory-proof")

    def test_required_source_mode_blocks_admission_until_source_is_ready(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        (root / ".trellis/scripts/task.py").write_text(
            "import json\nprint(json.dumps({'current_task': None, 'source': 'session:target'}))\n",
            encoding="utf-8",
        )
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative, "--mode", "archive_required").returncode, 0)
        package = root / Path(relative).parent
        (package / "session-handoff-prompt.md").write_text("handoff prompt\n", encoding="utf-8")
        observation = root / ".trellis/.runtime/observation.json"
        observation.parent.mkdir(parents=True, exist_ok=True)
        proof = {
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary-proof"},
            "source_session": {"status": "verified", "identity": "wrong-session"},
            "capsule": {"status": "verified", "proof_ref": "capsule-proof"},
            "archive": {"status": "verified", "proof_ref": "archive-proof"},
            "task": {"status": "completed", "completion_artifact": "task-proof"},
            "memory": {"status": "verified", "proof_ref": "memory-proof"},
        }
        observation.write_text(json.dumps(proof), encoding="utf-8")
        self.assertEqual(self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root))).returncode, 0)
        attestation = root / ".trellis/.runtime/attestation.json"
        attestation.write_text(json.dumps({
            "target_source": "session:target", "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        blocked = handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertEqual(blocked[1]["state"]["target"], "blocked")
        self.assertEqual(blocked[1]["state"]["retention"], "none")

        proof["source_session"]["identity"] = "fixture-session"
        observation.write_text(json.dumps(proof), encoding="utf-8")
        self.assertEqual(self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root))).returncode, 0)
        admitted = handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertEqual(admitted[1]["status"], "recorded")
        self.assertEqual(admitted[1]["state"]["target"], "reconciled")
        self.assertEqual(admitted[1]["state"]["retention"], "archive_eligible")

    def test_rollout_append_after_capture_remains_ready(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        relative = self.handoff_path_from(written.stdout)
        with rollout.open("ab") as handle:
            handle.write(b'{"type":"event_msg","payload":{"type":"task_complete"}}\n')
        validated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(json.loads(validated.stdout)["status"], "ready")

    def test_semantic_capsule_is_preserved_without_truncation(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        task_script = root / ".trellis/scripts/task.py"
        task_script.write_text("import json, os\nprint(json.dumps({'current_task': None, 'source': 'session:' + os.environ.get('FIXTURE_TARGET', 'target')}))\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture source"], check=True)
        capsule = "目标与已否决方案：" + ("语义现场 " * 5000)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, capsule=capsule)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        self.assertEqual(payload["memory_projection"]["semantic_capsule"], capsule)
        (root / relative).with_name("session-handoff-prompt.md").write_text("prompt\n", encoding="utf-8")
        prepared = self.run_cli(root, "prepare", "--handoff", relative)
        self.assertEqual(prepared.returncode, 0, prepared.stderr)

        attestation = root / ".trellis/.runtime/attestation.json"
        attestation.parent.mkdir(parents=True, exist_ok=True)
        attestation.write_text(json.dumps({
            "target_source": "session:target", "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        admitted = handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertEqual(admitted[1]["status"], "recorded")

        attestation.write_text(json.dumps({
            "target_source": "session:other", "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        os.environ["FIXTURE_TARGET"] = "other"
        self.addCleanup(os.environ.pop, "FIXTURE_TARGET", None)
        with self.assertRaisesRegex(handoff.ContractError, "already been consumed"):
            handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))

        os.environ["FIXTURE_TARGET"] = "target"
        attestation.write_text(json.dumps({
            "target_source": "session:target", "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        repeated = handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertEqual(repeated[1]["status"], "idempotent")

    def test_new_core_has_no_snapshot_or_projection_limits(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = root / "large-rollout.jsonl"
        rollout.write_text(
            "".join(
                json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": "决定 `item-%d`" % index}}, ensure_ascii=False) + "\n"
                for index in range(600)
            ),
            encoding="utf-8",
        )
        request_path = self.make_request(root, rollout, capsule="现场 " * 5000)
        request = json.loads(request_path.read_text(encoding="utf-8"))
        request["facts"] = ["fact-%d" % index for index in range(64)]
        request["validation"] = [{"command": "check-%d" % index, "result": "ok"} for index in range(24)]
        request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
        written = self.run_cli(root, "write", "--request", str(request_path), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
        self.assertEqual(len(payload["conversation"]["candidates"]), 600)
        self.assertEqual(len(payload["verified"]["facts"]), 64)
        self.assertNotIn("integrity", payload)
        self.assertNotIn("sha256", json.dumps(payload))
        self.assertEqual(json.loads(self.run_cli(root, "validate", "--handoff", relative).stdout)["status"], "ready")
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative).returncode, 0)
        receipt = (root / handoff.LIFECYCLE_RUNTIME / (Path(relative).parts[-2] + ".jsonl")).read_text(encoding="utf-8")
        self.assertNotIn("digest", receipt)

    def test_legacy_digest_fields_do_not_block_validation(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        core = root / relative
        payload = json.loads(core.read_text(encoding="utf-8"))
        payload["schema_version"] = 5
        payload["project"]["identity_digest"] = "sha256:legacy"
        payload["source"]["evidence"] = [{"path": "evidence.md", "bytes": 1, "sha256": "sha256:legacy"}]
        payload["source"]["rollout"].update({"device": 1, "inode": 2, "prefix_sha256": "sha256:legacy"})
        payload["integrity"] = {"payload_digest": "sha256:legacy", "source_digest": "sha256:legacy"}
        core.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        validated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(json.loads(validated.stdout)["status"], "ready")

    def test_admit_requires_paired_assets_and_retries_after_incomplete_intake(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        (root / ".trellis/scripts/task.py").write_text(
            "import json\nprint(json.dumps({'current_task': None, 'source': 'session:target'}))\n",
            encoding="utf-8",
        )
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative).returncode, 0)
        attestation = root / ".trellis/.runtime/attestation.json"
        attestation.parent.mkdir(parents=True, exist_ok=True)
        attestation.write_text(json.dumps({
            "target_source": "session:target", "prompt_read": False,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        with self.assertRaisesRegex(handoff.ContractError, "paired handoff prompt"):
            handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        handoff_id = Path(relative).parts[-2]
        self.assertEqual(sum(event["target_status"] == "reconciled" for event in handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)), 0)

        (root / relative).with_name("session-handoff-prompt.md").write_text("prompt\n", encoding="utf-8")
        self.assertEqual(handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))[1]["state"]["target"], "blocked")
        attestation.write_text(json.dumps({
            "target_source": "session:target", "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        self.assertEqual(handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))[1]["status"], "recorded")
        self.assertEqual(sum(event["target_status"] == "reconciled" for event in handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)), 1)

    def test_rollout_prefix_mutation_and_evidence_drift_are_reconciled_by_target(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        written = self.run_cli(root, "write", "--request", str(self.make_request(root, rollout)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        relative = self.handoff_path_from(written.stdout)
        raw = rollout.read_bytes()
        rollout.write_bytes(b" " + raw[1:])
        mutated = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(json.loads(mutated.stdout)["status"], "ready")

        written = self.run_cli(root, "write", "--request", str(self.make_request(root, self.make_rollout())), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stdout + written.stderr)
        relative = self.handoff_path_from(written.stdout)
        (root / "evidence.md").write_text("changed\n", encoding="utf-8")
        drifted = self.run_cli(root, "validate", "--handoff", relative)
        self.assertEqual(json.loads(drifted.stdout)["status"], "ready")

    def test_old_fixed_path_is_not_a_valid_package(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        result = self.run_cli(root, "validate", "--handoff", ".trellis/session-handoff.json")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timestamped handoff package", json.loads(result.stdout)["reason"])

    def test_lifecycle_archive_purge_restore_and_session_provenance(self) -> None:
        root = self.make_root()
        self.addCleanup(shutil.rmtree, root)
        (root / "evidence.md").write_text("verified fixture\n", encoding="utf-8")
        (root / ".trellis/scripts/task.py").write_text(
            "import json\nprint(json.dumps({'current_task': None, 'source': 'session:target-session'}))\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Fixture"], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        rollout = self.make_rollout()
        request = self.make_request(root, rollout)
        written = self.run_cli(root, "write", "--request", str(request), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        handoff_id = Path(relative).parts[-2]
        package = root / Path(relative).parent

        prepare = self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only")
        self.assertEqual(prepare.returncode, 0, prepare.stderr)
        self.assertEqual(json.loads(prepare.stdout)["status"], "recorded")
        repeated = self.run_cli(root, "prepare", "--handoff", relative, "--mode", "core_only")
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(json.loads(repeated.stdout)["status"], "idempotent")

        observation = package / "observation.json"
        observation.write_text(json.dumps({
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "local-boundary"},
            "source_session": {"status": "verified", "identity": "source-session"},
            "capsule": {"status": "verified", "proof_ref": "local-capsule"},
            "archive": {"status": "verified", "proof_ref": "local-archive"},
            "task": {"status": "completed", "completion_artifact": "task-complete"},
            "memory": {"status": "verified", "proof_ref": "local-memory"},
        }), encoding="utf-8")
        finalized = self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root)))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        self.assertEqual(json.loads(finalized.stdout)["status"], "recorded")
        attestation = package / "attestation.json"
        attestation.write_text(json.dumps({
            "target_source": "session:target-session", "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        (package / "session-handoff-prompt.md").write_text("handoff prompt\n", encoding="utf-8")
        admitted = self.run_cli(root, "admit", "--handoff", relative, "--attestation", str(attestation.relative_to(root)))
        self.assertEqual(admitted.returncode, 0, admitted.stderr)
        self.assertEqual(json.loads(admitted.stdout)["status"], "recorded")
        prompt = package / "session-handoff-prompt.md"

        prompt.unlink()
        missing_canonical_prompt = self.run_cli(root, "retention", "archive", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertNotEqual(missing_canonical_prompt.returncode, 0)
        self.assertEqual(json.loads(self.run_cli(root, "status", "--handoff", relative).stdout)["state"]["retention"], "archive_eligible")
        archive = root / handoff.ARCHIVE_RUNTIME / handoff_id
        self.assertFalse(archive.exists())
        prompt.write_text("handoff prompt\n", encoding="utf-8")

        archived = self.run_cli(root, "retention", "archive", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(archived.returncode, 0, archived.stderr)
        self.assertEqual({path.name for path in archive.iterdir()}, {"session-handoff.json", "session-handoff-prompt.md"})

        core = root / relative
        purged = self.run_cli(root, "retention", "purge", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(purged.returncode, 0, purged.stderr)
        self.assertFalse(core.exists())
        self.assertFalse(prompt.exists())
        self.assertTrue((root / "evidence.md").exists())

        archived_prompt = archive / "session-handoff-prompt.md"
        archived_prompt.unlink()
        events_before = handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)
        incomplete_status = self.run_cli(root, "status", "--handoff", relative)
        self.assertNotEqual(incomplete_status.returncode, 0)
        incomplete_restore = self.run_cli(root, "retention", "restore", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertNotEqual(incomplete_restore.returncode, 0)
        self.assertEqual(handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id), events_before)
        archived_prompt.write_text("handoff prompt\n", encoding="utf-8")

        restored = self.run_cli(root, "retention", "restore", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(restored.returncode, 0, restored.stderr)
        self.assertTrue(core.is_file())
        self.assertTrue(prompt.is_file())
        status = self.run_cli(root, "status", "--handoff", relative)
        self.assertEqual(status.returncode, 0, status.stderr)
        self.assertEqual(json.loads(status.stdout)["status"], "ready")
        reopened = self.run_cli(root, "retention", "reopen", "--handoff", relative, "--confirm-handoff-id", handoff_id)
        self.assertEqual(reopened.returncode, 0, reopened.stderr)

    def test_lifecycle_rejects_source_session_reuse_and_serializes_idempotence(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        rollout = self.make_rollout()
        request = self.make_request(root, rollout)
        written = self.run_cli(root, "write", "--request", str(request), "--explicit-user-request")
        relative = self.handoff_path_from(written.stdout)
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: handoff.lifecycle_prepare(root, relative, "core_only"), range(2)))
        self.assertEqual({result[1]["status"] for result in results}, {"recorded", "idempotent"})
        handoff_id = Path(relative).parts[-2]
        (root / relative).with_name("session-handoff-prompt.md").write_text("handoff prompt\n", encoding="utf-8")
        attestation = root / ".trellis/.runtime" / "attestation.json"
        attestation.parent.mkdir(parents=True, exist_ok=True)
        attestation.write_text(json.dumps({
            "target_source": "session:fixture-session", "prompt_read": True,
            "trellis_started": True, "facts_reconciled": True, "action_authorized": False,
            "task_disposition": "none", "task_path": None, "continuation_status": "absent",
        }), encoding="utf-8")
        with self.assertRaisesRegex(handoff.ContractError, "source session id"):
            handoff.lifecycle_admit(root, relative, str(attestation.relative_to(root)))
        self.assertTrue(handoff_id)

    def test_receipt_lock_allows_only_one_reconciled_admit_target(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        handoff_id, _, _ = handoff._core(root, relative)
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative).returncode, 0)

        desired = {"source": "prepared", "target": "reconciled", "retention": "archive_eligible"}

        def admit(target: str) -> str:
            try:
                return handoff._append_event(
                    root, handoff_id, "admit", desired, ["target=session:" + target],
                )["status"]
            except handoff.ContractError:
                return "rejected"

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(admit, ["target-a", "target-b"]))

        self.assertEqual(sorted(outcomes), ["recorded", "rejected"])
        events = handoff._read_events(handoff._lifecycle_path(root, handoff_id), handoff_id)
        self.assertEqual(sum(event["event_type"] == "admit" and event["target_status"] == "reconciled" for event in events), 1)

    def test_archive_mode_requires_matching_source_session_provenance(self) -> None:
        root = self.make_git_root()
        self.addCleanup(shutil.rmtree, root)
        written = self.run_cli(root, "write", "--request", str(self.make_request(root)), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative, "--mode", "archive_required").returncode, 0)
        observation = root / ".trellis/.runtime" / "observation.json"
        observation.parent.mkdir(parents=True, exist_ok=True)
        proof = {
            "availability": "available",
            "boundary": {"status": "sealed", "proof_ref": "boundary"},
            "source_session": {"status": "verified", "identity": "wrong-session"},
            "capsule": {"status": "verified", "proof_ref": "local-capsule"},
            "archive": {"status": "verified", "proof_ref": "local-archive"},
            "task": {"status": "completed", "completion_artifact": "complete"},
            "memory": {"status": "verified", "proof_ref": "local-memory"},
        }
        observation.write_text(json.dumps(proof), encoding="utf-8")
        pending = self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root)))
        self.assertEqual(pending.returncode, 0, pending.stderr)
        self.assertEqual(json.loads(pending.stdout)["state"]["source"], "pending")
        proof["source_session"]["identity"] = "fixture-session"
        observation.write_text(json.dumps(proof), encoding="utf-8")
        finalized = self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root)))
        self.assertEqual(finalized.returncode, 0, finalized.stderr)
        self.assertEqual(json.loads(finalized.stdout)["state"]["source"], "archive_verified")
        proof["archive"]["proof_ref"] = None
        observation.write_text(json.dumps(proof), encoding="utf-8")
        weaker = self.run_cli(root, "finalize", "--handoff", relative, "--observation", str(observation.relative_to(root)))
        self.assertEqual(weaker.returncode, 0, weaker.stderr)
        self.assertEqual(json.loads(weaker.stdout)["state"]["source"], "archive_verified")

    def test_ownership_adapter_keeps_core_immutable_and_records_distinct_receipts(self) -> None:
        root = self.make_git_root(with_task=True)
        self.addCleanup(shutil.rmtree, root)
        task_script = root / ".trellis/scripts/task.py"
        task_script.write_text(
            "import json, os, sys\n"
            "args = sys.argv[1:]\n"
            "target = os.environ.get('TRELLIS_CONTEXT_ID') == 'target'\n"
            "task = None if target else {'id': 'fixture-task', 'dir': '.trellis/tasks/demo', 'status': 'in_progress'}\n"
            "if args == ['current', '--json']:\n"
            "    print(json.dumps({'current_task': task, 'source': 'session:' + ('target' if target else 'source')}))\n"
            "elif args and args[0] == 'ownership':\n"
            "    op = args[1]\n"
            "    with open('.trellis/.runtime/ownership-args.jsonl', 'a', encoding='utf-8') as handle:\n"
            "        handle.write(json.dumps(args) + '\\n')\n"
            "    if op == 'status':\n"
            "        print(json.dumps({'status': 'archived', 'generation': 7, 'record_digest': 'sha256:' + 'a' * 64}))\n"
            "        raise SystemExit(0)\n"
            "    generations = {'quiesce': 0, 'seal': 1, 'retire': 3, 'claim': 5, 'consume': 6, 'archive': 7}\n"
            "    statuses = {'quiesce': 'quiescing', 'seal': 'sealed', 'retire': 'ready', 'claim': 'claimed', 'consume': 'consumed', 'archive': 'archived'}\n"
            "    print(json.dumps({'status': statuses[op], 'generation': generations.get(op, 5), 'record_digest': 'sha256:' + 'a' * 64}))\n"
            "else:\n"
            "    raise SystemExit(2)\n",
            encoding="utf-8",
        )
        rollout = self.make_rollout()
        request = self.make_request(root, rollout)
        written = self.run_cli(root, "write", "--request", str(request), "--explicit-user-request")
        self.assertEqual(written.returncode, 0, written.stderr)
        relative = self.handoff_path_from(written.stdout)
        before = (root / relative).read_bytes()
        handoff_id = Path(relative).parts[-2]

        self.assertEqual(self.run_cli(root, "prepare", "--handoff", relative).returncode, 0)
        self.assertEqual(handoff.ownership_operation(root, "quiesce", relative, explicit=True)["ownership"]["status"], "quiescing")
        self.assertEqual(handoff.ownership_operation(root, "seal", relative, explicit=True, expected_generation=0)["ownership"]["status"], "sealed")
        self.assertEqual(handoff.ownership_operation(root, "retire", relative, explicit=True, expected_generation=1)["ownership"]["generation"], 3)

        os.environ["TRELLIS_CONTEXT_ID"] = "target"
        self.addCleanup(os.environ.pop, "TRELLIS_CONTEXT_ID", None)
        claimed = handoff.ownership_operation(root, "claim", relative, explicit=True, expected_generation=3)
        repeated = handoff.ownership_operation(root, "claim", relative, explicit=True, expected_generation=3)
        self.assertEqual(claimed["ownership"]["status"], "claimed")
        self.assertEqual(repeated["lifecycle"]["status"], "idempotent")
        self.assertEqual(handoff.ownership_operation(root, "consume", relative, explicit=True, expected_generation=5)["ownership"]["status"], "consumed")
        self.assertEqual(handoff.ownership_operation(root, "archive", relative, explicit=True, expected_generation=6)["ownership"]["status"], "archived")
        self.assertEqual(handoff.ownership_operation(root, "status", relative, explicit=False)["ownership"]["status"], "archived")
        self.assertEqual((root / relative).read_bytes(), before)
        events = (root / handoff.LIFECYCLE_RUNTIME / (handoff_id + ".jsonl")).read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum('"event_type": "ownership_claim"' in line for line in events), 1)


if __name__ == "__main__":
    unittest.main()
