#!/usr/bin/env python3
"""Package, memory and secret-boundary regressions for schema 11."""

import json
import copy
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import test_handoff as fixtures

handoff = fixtures.handoff


class StreamingHandoffTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.HandoffTests()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.make_git_root()
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, rollout=None):
        result = self.fixture.run_cli(self.root, "write", "--request", str(self.fixture.make_request(self.root, rollout)), "--explicit-user-request")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.core = self.root / self.fixture.handoff_path_from(result.stdout)
        return json.loads(self.core.read_text())

    def test_history_is_bound_and_not_embedded_in_core(self):
        payload = self.write()
        self.assertEqual(payload["schema_version"], 11)
        self.assertNotIn("conversation", payload)
        history = self.core.with_name("session-handoff-history.jsonl")
        self.assertTrue(history.is_file())
        self.assertEqual(payload["history"]["path"], history.name)
        history.write_bytes(history.read_bytes() + b"{}\n")
        result = self.fixture.run_cli(self.root, "validate", "--handoff", str(self.core.relative_to(self.root)))
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)

    def test_quoted_secrets_reject_request_and_preserve_history_context(self):
        rollout = self.root / "secret.jsonl"
        secret = "xai-" + "a" * 28
        text = 'before {"token":"' + secret + '"} after 中文'
        rollout.write_text(json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": text}}, ensure_ascii=False) + "\n")
        self.write(rollout)
        history = self.core.with_name("session-handoff-history.jsonl").read_text()
        self.assertNotIn(secret, history)
        self.assertIn("before", history)
        self.assertIn("after 中文", history)
        request = self.fixture.make_request(self.root, capsule=text)
        result = self.fixture.run_cli(self.root, "write", "--request", str(request), "--explicit-user-request")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(secret, result.stdout + result.stderr)

    def test_semantic_corruption_fails_before_every_dependent_entry(self):
        original = self.write()
        records = self.fixture.history_records(self.core)
        relative = str(self.core.relative_to(self.root))
        candidate = next(i for i, r in enumerate(records) if r["type"] == "candidate")
        timeline = next(i for i, r in enumerate(records) if r["type"] == "timeline")
        span = next(i for i, r in enumerate(records) if r["type"] == "omission")
        mutations = [
            (candidate, ("event_index",), True),
            (candidate, ("kind",), "reasoning"),
            (candidate, ("source", "byte_end"), original["source"]["rollout"]["capture_end"] + 1),
            (candidate, ("source", "line"), False),
            (timeline, ("event_index",), 999),
            (timeline, ("topic_key",), "wrong"),
            (timeline, ("state",), "accepted"),
            (timeline, ("repeat_count",), 2),
            (timeline, ("supersedes_event_index",), 1),
            (span, ("bytes",), "bad"),
        ]
        entries = [("validate",), ("read", "--view", "core"), ("prepare",), ("status",), ("ownership", "status"),
                   ("retention", "archive", "--confirm-handoff-id", original["handoff_id"])]
        for index, path, value in mutations:
            with self.subTest(path=path, value=value):
                changed = copy.deepcopy(records)
                target = changed[index]["value"]
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                self.fixture.rewrite_history(self.core, copy.deepcopy(original), changed)
                for entry in entries:
                    result = self.fixture.run_cli(self.root, *entry, "--handoff", relative)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                renderer = fixtures.SKILL / "scripts/render_handoff_prompt.py"
                result = subprocess.run([sys.executable, str(renderer), "--project-root", str(self.root), "--handoff", relative], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertFalse(self.core.with_name("session-handoff-prompt.md").exists())
        self.assertFalse((self.root / handoff.LIFECYCLE_RUNTIME).exists())

    def test_history_missing_symlink_and_noncanonical_lines_are_rejected(self):
        self.write()
        history = self.core.with_name(handoff.HISTORY_NAME)
        data = history.read_bytes()
        history.unlink()
        relative = str(self.core.relative_to(self.root))
        self.assertEqual(self.fixture.run_cli(self.root, "validate", "--handoff", relative).returncode, 2)
        outside = self.root / "outside.jsonl"
        outside.write_bytes(data)
        history.symlink_to(outside)
        self.assertEqual(self.fixture.run_cli(self.root, "validate", "--handoff", relative).returncode, 2)
        history.unlink()
        for invalid in (data[:-1], b"{}\n", data.replace(b'{"type":', b'{ "type":', 1), b"\xff\n"):
            history.write_bytes(invalid)
            result = self.fixture.run_cli(self.root, "validate", "--handoff", relative)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_value_scanning_handles_nested_quoted_escaped_secrets_and_prose(self):
        from workflow_contracts import contains_secret, redact_text, load_json_file
        for prefix in ("sk-", "th-", "xai-"):
            secret = prefix + "z" * 24
            values = [{"token": secret}, {"nested": [{"api_key": secret}]}, json.dumps({"token": secret}), json.dumps(json.dumps({"token": secret})),
                      '{"token":"' + secret.replace("z", r"\u007a") + '"}', "Bearer " + secret,
                      "-----BEGIN RSA PRIVATE KEY-----\nbody\n-----END RSA PRIVATE KEY-----",
                      'before {"token":"' + secret.replace("z", r"\u007a") + '"} after']
            for value in values:
                with self.subTest(prefix=prefix, value_type=type(value).__name__):
                    self.assertTrue(contains_secret(value))
                    request = self.root / "reject.json"
                    request.write_text(json.dumps({"value": value}))
                    with self.assertRaises(handoff.ContractError):
                        load_json_file(request)
                    if isinstance(value, str):
                        self.assertFalse(contains_secret(redact_text(value)))
        for text in ("配置 token，不读取其值。", "xai 服务暂不可用", "api_key: placeholder", "token=null", "password is private"):
            self.assertFalse(contains_secret(text))
            self.assertEqual(redact_text(text), text)

    def test_failed_publication_leaves_no_ready_partial_package(self):
        request = handoff._request(self.root, self.fixture.make_request(self.root))
        identifier = handoff._handoff_id()
        history = self.root / "generated.jsonl"
        payload = handoff.build(self.root, request, identifier, history)
        destination = handoff._destination(self.root, create_id=identifier)[1]
        with mock.patch.object(handoff.os, "rename", side_effect=OSError("injected publication failure")):
            with self.assertRaises(OSError):
                handoff._atomic_json(destination, payload, history)
        self.assertFalse(destination.parent.exists())
        self.assertEqual(list(destination.parent.parent.iterdir()), [])
        with mock.patch.object(handoff.sqlite3, "connect", side_effect=handoff.sqlite3.OperationalError("injected index failure")):
            with self.assertRaises(handoff.sqlite3.Error):
                handoff.build(self.root, request, identifier, self.root / "second.jsonl")
        self.assertFalse(destination.parent.exists())

    def test_restore_failure_preserves_previous_directory_and_receipt_scan_is_streaming(self):
        self.write()
        relative = str(self.core.relative_to(self.root))
        self.core.with_name("session-handoff-prompt.md").write_text("prompt\n")
        handoff.lifecycle_prepare(self.root, relative, "core_only")
        handoff.lifecycle_seal(self.root, relative, explicit=True)
        archive = self.root / handoff.ARCHIVE_RUNTIME / self.core.parent.name
        handoff._archive_copy(self.root, self.core.parent.name, self.core)
        before = {p.name: p.read_bytes() for p in self.core.parent.iterdir()}
        native_rename = handoff.os.rename
        def fail_publish(source, destination):
            if ".restore-" in str(source):
                raise OSError("injected restore failure")
            return native_rename(source, destination)
        with mock.patch.object(handoff.os, "rename", side_effect=fail_publish):
            with self.assertRaises(OSError):
                handoff._restore_package(self.root, archive, self.core.parent, self.core.parent.name)
        self.assertEqual({p.name: p.read_bytes() for p in self.core.parent.iterdir()}, before)
        with mock.patch.object(Path, "read_text", side_effect=AssertionError("whole-file receipt read")):
            events = handoff._read_events(handoff._lifecycle_path(self.root, self.core.parent.name), self.core.parent.name)
            self.assertEqual(handoff._state(events)["source"], "boundary_sealed")
            self.assertEqual(len(list(events)), 2)

    def test_failed_restore_rollback_keeps_previous_package_backup(self):
        self.write()
        relative = str(self.core.relative_to(self.root))
        self.core.with_name("session-handoff-prompt.md").write_text("prompt\n")
        handoff.lifecycle_prepare(self.root, relative, "core_only")
        handoff.lifecycle_seal(self.root, relative, explicit=True)
        archive = self.root / handoff.ARCHIVE_RUNTIME / self.core.parent.name
        handoff._archive_copy(self.root, self.core.parent.name, self.core)
        before = {p.name: p.read_bytes() for p in self.core.parent.iterdir()}
        native_rename = handoff.os.rename

        def fail_publish_and_rollback(source, destination):
            if ".restore-" in str(source) or (".backup-" in str(source) and destination == self.core.parent):
                raise OSError("injected restore and rollback failure")
            return native_rename(source, destination)

        with mock.patch.object(handoff.os, "rename", side_effect=fail_publish_and_rollback):
            with self.assertRaisesRegex(handoff.ContractError, "previous package preserved"):
                handoff._restore_package(self.root, archive, self.core.parent, self.core.parent.name)
        self.assertFalse(self.core.parent.exists())
        backups = list(self.core.parent.parent.glob(".*.backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual({p.name: p.read_bytes() for p in backups[0].iterdir()}, before)

    def test_purge_rename_or_receipt_failure_restores_the_entire_package(self):
        payload = self.write()
        relative, identifier = str(self.core.relative_to(self.root)), payload["handoff_id"]
        self.core.with_name("session-handoff-prompt.md").write_text("prompt\n")
        handoff.lifecycle_prepare(self.root, relative, "core_only")
        handoff.lifecycle_seal(self.root, relative, explicit=True)
        handoff._append_event(self.root, identifier, "admit", {"source": "boundary_sealed", "target": "reconciled", "retention": "archive_eligible"}, ["target=session:target"])
        handoff.lifecycle_retention(self.root, "archive", relative, identifier)
        before = {p.name: p.read_bytes() for p in self.core.parent.iterdir()}
        native_append = handoff._append_event
        def fail_receipt(root, handoff_id, event_type, *args):
            if event_type == "purge":
                raise OSError("injected purge receipt failure")
            return native_append(root, handoff_id, event_type, *args)
        for target, error in (("rename", OSError("injected purge rename failure")), ("_append_event", fail_receipt)):
            with self.subTest(target=target):
                owner = handoff.os if target == "rename" else handoff
                with mock.patch.object(owner, target, side_effect=error):
                    expected = OSError if target == "rename" else handoff.ContractError
                    with self.assertRaises(expected):
                        handoff.lifecycle_retention(self.root, "purge", relative, identifier)
                self.assertEqual({p.name: p.read_bytes() for p in self.core.parent.iterdir()}, before)
        native_rmtree = handoff.shutil.rmtree
        failed_once = False

        def fail_purge_delete(path, *args, **kwargs):
            nonlocal failed_once
            if ".purge-" in str(path) and not failed_once:
                failed_once = True
                raise OSError("injected purge removal failure")
            return native_rmtree(path, *args, **kwargs)

        with mock.patch.object(handoff.shutil, "rmtree", side_effect=fail_purge_delete):
            with self.assertRaisesRegex(handoff.ContractError, "package restored"):
                handoff.lifecycle_retention(self.root, "purge", relative, identifier)
        self.assertEqual({p.name: p.read_bytes() for p in self.core.parent.iterdir()}, before)
        events = handoff._read_events(handoff._lifecycle_path(self.root, identifier), identifier)
        self.assertEqual(handoff._state(events)["retention"], "archived")
        self.assertFalse(any(event["event_type"] == "purge" for event in events))
        handoff.lifecycle_retention(self.root, "purge", relative, identifier)
        self.assertFalse(self.core.parent.exists())

    def test_coverage_cannot_hide_missing_records_or_records_after_partial_tail(self):
        rollout = self.root / "empty-message.jsonl"
        rollout.write_text(json.dumps({"type": "response_item", "payload": {"type": "message", "role": "user", "content": []}}) + "\n")
        original = self.write(rollout)
        records = self.fixture.history_records(self.core)
        self.assertEqual(records[0]["value"], {"category": "excluded", "name": "empty_public_message", "count": 1})
        changed = copy.deepcopy(original)
        changed["source"]["rollout"]["record_count"] += 1
        changed["history"]["capture"]["record_count"] += 1
        self.fixture.rewrite_history(self.core, changed, records)
        self.assertEqual(self.fixture.run_cli(self.root, "validate", "--handoff", str(self.core.relative_to(self.root))).returncode, 2)
        rollout = self.fixture.make_rollout()
        with rollout.open("ab") as handle:
            handle.write(b'{"partial":')
        original = self.write(rollout)
        records = self.fixture.history_records(self.core)
        partial = next(r for r in records if r["type"] == "omission" and r["value"]["kind"] == "trailing_partial_record")
        records.remove(partial)
        records.insert(0, partial)
        self.fixture.rewrite_history(self.core, original, records)
        self.assertEqual(self.fixture.run_cli(self.root, "validate", "--handoff", str(self.core.relative_to(self.root))).returncode, 2)

    @unittest.skipUnless(os.environ.get("PENNIX_HANDOFF_RESOURCE_GATE") == "1", "explicit 192 MiB resource gate")
    def test_resource_gate_all_scales_and_long_unicode_record(self):
        metrics = []
        limit = 192 * 1024 * 1024
        worker = (
            "import json,resource,runpy,sys,pathlib\n"
            f"resource.setrlimit(resource.RLIMIT_AS,({limit},{limit}))\n"
            "sys.argv=sys.argv[1:]\n"
            "sys.path.insert(0,str(pathlib.Path(sys.argv[0]).parent))\n"
            "try:runpy.run_path(sys.argv[0],run_name='__main__')\n"
            "finally:print('RESOURCE_METRICS '+json.dumps({'rss_kib':max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)}),file=sys.stderr)\n"
        )
        for scale in (1000, 10000, 100000, "8MiB"):
            scratch = self.root / "scratch"
            scratch.mkdir(exist_ok=True)
            rollout = self.root / "resource.jsonl"
            with rollout.open("w", encoding="utf-8") as handle:
                n = 1 if scale == "8MiB" else scale
                for i in range(n):
                    message = "汉😀" * (8 * 1024 * 1024 // 7) if scale == "8MiB" else "批准 `topic-%d` " % i + "x" * 960
                    handle.write(json.dumps({"type": "event_msg", "payload": {"type": "user_message", "message": message}}, ensure_ascii=False) + "\n")
            request = self.fixture.make_request(self.root, rollout)
            def run(script, *args, target="source"):
                started, peak = time.monotonic(), 0
                with tempfile.NamedTemporaryFile("w+", dir=scratch) as out, tempfile.NamedTemporaryFile("w+", dir=scratch) as err, subprocess.Popen([sys.executable, "-c", worker, str(script), "--project-root", str(self.root), *args], stdout=out, stderr=err, env={**os.environ, "FIXTURE_TARGET": target, "TMPDIR": str(scratch)}) as process:
                    while process.poll() is None:
                        try:
                            total = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
                        except FileNotFoundError:
                            continue
                        peak = max(peak, total)
                        if peak >= 1024 * 1024 * 1024 or time.monotonic() - started > 180:
                            process.kill()
                            self.fail("resource operation exceeded disk or time budget")
                        time.sleep(0.05)
                    out.seek(0)
                    err.seek(0)
                    stdout, stderr = out.read(), err.read()
                self.assertEqual(process.returncode, 0, stdout[-1000:] + stderr[-1000:])
                measure = json.loads(next(line.removeprefix("RESOURCE_METRICS ") for line in stderr.splitlines() if line.startswith("RESOURCE_METRICS ")))
                self.assertLess(measure["rss_kib"], limit // 1024)
                measure.update(scale=scale, operation=script.stem + ":" + args[0], peak_temporary_bytes=peak, elapsed_seconds=round(time.monotonic() - started, 3), exit_code=process.returncode)
                metrics.append(measure)
                print(json.dumps(measure), flush=True)
                return json.loads(stdout) if script == fixtures.SCRIPT else None
            written = run(fixtures.SCRIPT, "write", "--request", str(request), "--explicit-user-request")
            relative, identifier = written["handoff_path"], written["handoff_id"]
            core = self.root / relative
            payload = json.loads(core.read_text())
            self.assertEqual(payload["history"]["counts"]["candidate"], n)
            run(fixtures.SCRIPT, "validate", "--handoff", relative)
            run(fixtures.SCRIPT, "read", "--handoff", relative, "--view", "core")
            run(fixtures.SCRIPT, "read", "--handoff", relative, "--view", "history", "--offset", str(max(0, payload["history"]["characters"] - 4096)))
            run(fixtures.SCRIPT, "read", "--handoff", relative, "--view", "history", "--event-index", str(n))
            run(fixtures.SKILL / "scripts/render_handoff_prompt.py", "--handoff", relative)
            run(fixtures.SCRIPT, "prepare", "--handoff", relative)
            run(fixtures.SCRIPT, "seal", "--handoff", relative, "--explicit-user-request")
            attestation = self.root / "resource-attestation.json"
            attestation.write_text(json.dumps({"target_source": "session:target", "core_view_read": True, "prompt_read": True, "trellis_started": True, "facts_reconciled": True, "action_authorized": False, "task_disposition": "none", "task_path": None, "continuation_status": "absent", "history_read": "full", "history_refs": [{"event_index": None, "offset": 0, "next_offset": payload["history"]["characters"]}]}))
            run(fixtures.SCRIPT, "admit", "--handoff", relative, "--attestation", str(attestation.relative_to(self.root)), target="target")
            if scale == 100000:
                receipt = handoff._lifecycle_path(self.root, identifier)
                event = list(handoff._read_events(receipt, identifier))[-1]
                event.update(event_type="finalize", evidence_refs=["resource=" + "x" * 960])
                with receipt.open("a", encoding="utf-8") as handle:
                    for _ in range(n):
                        handle.write(json.dumps(event) + "\n")
            run(fixtures.SCRIPT, "status", "--handoff", relative)
            run(fixtures.SCRIPT, "retention", "archive", "--handoff", relative, "--confirm-handoff-id", identifier)
            run(fixtures.SCRIPT, "retention", "purge", "--handoff", relative, "--confirm-handoff-id", identifier)
            run(fixtures.SCRIPT, "retention", "restore", "--handoff", relative, "--confirm-handoff-id", identifier)
            run(fixtures.SCRIPT, "status", "--handoff", relative)
            task = self.root / ".trellis/tasks/resource"
            task.mkdir(parents=True, exist_ok=True)
            (task / "task.json").write_text(json.dumps({"id": "resource-task", "status": "in_progress"}))
            task_script = self.root / ".trellis/scripts/task.py"
            original_script = task_script.read_text()
            task_script.write_text("import json,sys\nif 'ownership' in sys.argv:\n print(json.dumps({'status':'ready','core_digest':sys.argv[sys.argv.index('--core-digest')+1]}))\nelse:\n print(json.dumps({'current_task':{'id':'resource-task','dir':'.trellis/tasks/resource','status':'in_progress'},'source':'direct','session_source':'session:source'}))\n")
            try:
                task_written = run(fixtures.SCRIPT, "write", "--request", str(request), "--explicit-user-request")
                ownership = run(fixtures.SCRIPT, "ownership", "status", "--handoff", task_written["handoff_path"])
                self.assertEqual(ownership["ownership"]["status"], "ready")
                self.assertEqual(ownership["ownership"]["core_digest"], handoff._ownership_core_digest(self.root / task_written["handoff_path"]))
            finally:
                task_script.write_text(original_script)
            total = sum(p.stat().st_size for p in self.root.rglob("*") if p.is_file())
            self.assertLess(total, 1024 * 1024 * 1024)
            metrics.append({"scale": scale, "temporary_bytes": total, "core_bytes": core.stat().st_size})
            shutil.rmtree(self.root / handoff.HANDOFFS)
            shutil.rmtree(self.root / handoff.ARCHIVE_RUNTIME)
            shutil.rmtree(self.root / handoff.LIFECYCLE_RUNTIME)
        Path("/tmp/pennix-handoff-resource-results.json").write_text(json.dumps(metrics, indent=2) + "\n")


if __name__ == "__main__":
    unittest.main()
