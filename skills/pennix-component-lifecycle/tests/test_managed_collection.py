from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import lifecycle


class ManagedCollectionTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.value = json.loads(lifecycle.DEFAULT_CATALOG.read_text())
        self.value["configuration_targets"] = []
        self.value["components"] = {
            key: value for key, value in self.value["components"].items() if value["delivery"] == "collection"
        }
        base = self.value["components"]["pennix-skills"]["collection_contract"]
        base.update(skills=["pennix-base"], bootstrap_skill="pennix-base", materialized={}, commands={})
        base["source"] = {"repo": "PennixRv/fixture", "ref": "main", "paths": ["skills/pennix-base"]}
        self.pin = "a" * 40
        self.extra = self.value["components"]["pennix-skills-extra"]
        self.extra["collection_contract"]["source"]["ref"] = self.pin
        self.catalog_path = self.root / "catalog.json"
        self.save_catalog()
        self.host_home = self.root / "host"
        scripts = self.host_home / "skills/.system/skill-installer/scripts"
        scripts.mkdir(parents=True)
        self.helper = scripts / "install-skill-from-github.py"
        self.helper.write_text("# Fixture helper\n")
        self.helper.with_name("github_utils.py").write_text("# Fixture dependency\n")
        self.args = SimpleNamespace(
            catalog=self.catalog_path, codex_home=self.root / "target", destination=None,
            component="pennix-skills-extra", command="install", yes=True,
        )
        self.destination = self.args.codex_home / "skills/pennix-skills-extra"
        self.base = self.args.codex_home / "skills/pennix-skills"
        self.make_skill(self.base, "pennix-base", "existing")
        adapter = lifecycle.skills_install
        receipt = adapter._write_receipt(self.base, adapter.collection_digest(self.base))
        os.replace(receipt, adapter.receipt_path(self.base))
        for patcher in (
            patch.object(lifecycle, "DEFAULT_CATALOG", self.catalog_path),
            patch.object(adapter, "codex_home", return_value=self.host_home),
            patch.object(lifecycle.host, "detect_host", return_value={"supported": True, "installers": {}}),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        downloader = patch.object(lifecycle.subprocess, "run", side_effect=self.download)
        self.downloader = downloader.start()
        self.addCleanup(downloader.stop)

    def save_catalog(self) -> dict:
        self.catalog_path.write_text(json.dumps(self.value))
        return lifecycle.load_catalog(self.catalog_path)

    def make_skill(self, destination: Path, name: str, revision: str) -> None:
        skill = destination / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(f"---\nname: {name}\ndescription: Fixture.\n---\n\n{revision}\n")
        (skill / "LICENSE").write_text("Fixture notice\n")
        (skill / "UPSTREAM.md").write_text("Fixture provenance\n")

    def download(self, argv: list[str], **kwargs) -> subprocess.CompletedProcess:
        source = self.extra["collection_contract"]["source"]
        destination = Path(argv[argv.index("--dest") + 1])
        self.assertEqual(argv, [
            sys.executable, str(self.helper), "--repo", source["repo"], "--ref", source["ref"],
            "--path", *source["paths"], "--dest", str(destination), "--method", "download",
        ])
        self.assertEqual(kwargs["cwd"], self.helper.parent)
        self.assertTrue(destination.name.startswith(".pennix-skills-extra-stage-"))
        self.assertEqual(destination.parent, self.destination.parent)
        for name in self.extra["collection_contract"]["skills"]:
            self.make_skill(destination, name, source["ref"])
        return subprocess.CompletedProcess(argv, 0, "", "")

    def perform(self, operation: str) -> str:
        self.args.command = operation
        with contextlib.redirect_stdout(io.StringIO()):
            return lifecycle.run_lifecycle(self.args, self.save_catalog())

    def snapshot(self, destination: Path) -> tuple:
        paths = [destination, *sorted(destination.rglob("*")), lifecycle.skills_install.receipt_path(destination)]
        return tuple((str(path), stat.S_IMODE(path.stat().st_mode), path.stat().st_uid,
                      path.read_bytes() if path.is_file() else None) for path in paths)

    def test_install_verify_and_same_pin_upgrade_preserve_native_collection(self) -> None:
        before = self.snapshot(self.base)
        self.assertEqual(self.perform("install"), "changed")
        source = lifecycle.collection_source_identity(self.extra)
        receipt = lifecycle.skills_install.collection_receipt(self.destination)
        self.assertEqual(receipt["schema"], 3)
        self.assertEqual(receipt["source"], source)
        inventory = lifecycle.discover(self.args, self.save_catalog())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lifecycle.verify_inventory(self.args, self.save_catalog(), inventory), [])
        self.assertEqual(inventory["components"]["pennix-skills-extra"]["status"], "match")
        self.assertEqual(self.perform("upgrade"), "no-op")
        self.assertEqual(self.downloader.call_count, 1)
        with self.assertRaisesRegex(lifecycle.BootstrapError, "absent"):
            self.perform("install")
        self.assertEqual(self.snapshot(self.base), before)

    def test_complete_old_pin_can_upgrade_and_return_to_reviewed_pin(self) -> None:
        self.perform("install")
        before = self.snapshot(self.base)
        for pin in ["b" * 40, self.pin]:
            self.extra["collection_contract"]["source"]["ref"] = pin
            self.assertEqual(lifecycle.probe_component(self.extra, self.args.codex_home)[0], "upgrade-available")
            self.assertEqual(self.perform("upgrade"), "changed")
            self.assertEqual(lifecycle.probe_component(self.extra, self.args.codex_home), ("match", pin))
            self.assertEqual(self.snapshot(self.base), before)

    def test_partial_download_does_not_touch_active_collections(self) -> None:
        self.perform("install")
        before = self.snapshot(self.destination), self.snapshot(self.base)
        self.extra["collection_contract"]["source"]["ref"] = "b" * 40

        def partial(argv, **kwargs):
            destination = Path(argv[argv.index("--dest") + 1])
            self.make_skill(destination, "codebase-design", "partial")
            return subprocess.CompletedProcess(argv, 1, "", "fixture download failed")

        self.downloader.side_effect = partial
        with self.assertRaisesRegex(lifecycle.BootstrapError, "fixture download failed"):
            self.perform("upgrade")
        self.assertEqual((self.snapshot(self.destination), self.snapshot(self.base)), before)
        self.assertEqual(lifecycle.staging_candidates(None, self.args.codex_home), [])

    def test_support_admission_failures_keep_trees_receipts_and_modes(self) -> None:
        self.perform("install")
        before = self.snapshot(self.destination), self.snapshot(self.base)
        self.extra["collection_contract"]["source"]["ref"] = "b" * 40
        for fault in ("license", "provenance", "missing", "escape", "unknown", "symlink"):
            with self.subTest(fault=fault):
                def broken(argv, **kwargs):
                    result = self.download(argv, **kwargs)
                    staging = Path(argv[argv.index("--dest") + 1])
                    skill = staging / "codebase-design"
                    if fault == "license":
                        (skill / "LICENSE").unlink()
                    elif fault == "provenance":
                        (skill / "UPSTREAM.md").unlink()
                    elif fault == "missing":
                        (skill / "SKILL.md").unlink()
                    elif fault == "escape":
                        (skill / "bad.md").write_text("[outside](../../catalog.json)")
                    elif fault == "unknown":
                        (skill / "bad.md").write_text("Use `$unregistered-method`.")
                    else:
                        (skill / "bad.md").symlink_to(self.catalog_path)
                    return result

                self.downloader.side_effect = broken
                with self.assertRaises(lifecycle.BootstrapError):
                    self.perform("upgrade")
                self.assertEqual((self.snapshot(self.destination), self.snapshot(self.base)), before)
                self.assertEqual(lifecycle.staging_candidates(None, self.args.codex_home), [])

    def test_receipt_and_cutover_failures_roll_back_both_owned_artifacts(self) -> None:
        self.perform("install")
        before = self.snapshot(self.destination), self.snapshot(self.base)
        self.extra["collection_contract"]["source"]["ref"] = "b" * 40
        with patch.object(lifecycle.skills_install, "_write_receipt", side_effect=OSError("receipt write failure")):
            with self.assertRaisesRegex(lifecycle.BootstrapError, "receipt write failure"):
                self.perform("upgrade")
        self.assertEqual((self.snapshot(self.destination), self.snapshot(self.base)), before)
        for failing_target in (self.destination, lifecycle.skills_install.receipt_path(self.destination)):
            with self.subTest(target=failing_target):
                original = os.replace
                failed = False

                def fail_once(source, target):
                    nonlocal failed
                    if Path(target) == failing_target and not failed:
                        failed = True
                        raise OSError("fixture cutover failure")
                    return original(source, target)

                with patch.object(lifecycle.skills_install.os, "replace", side_effect=fail_once):
                    with self.assertRaisesRegex(lifecycle.BootstrapError, "fixture cutover failure"):
                        self.perform("upgrade")
                self.assertTrue(failed)
                self.assertEqual((self.snapshot(self.destination), self.snapshot(self.base)), before)
                self.assertEqual(lifecycle.staging_candidates(None, self.args.codex_home), [])

    def test_unknown_drifted_and_unsafe_receipts_are_never_adopted(self) -> None:
        self.perform("install")
        receipt_path = lifecycle.skills_install.receipt_path(self.destination)
        receipt = json.loads(receipt_path.read_text())
        before = self.snapshot(self.base)
        for fault in ("repo", "ref", "names", "schema", "float-schema", "public", "content"):
            with self.subTest(fault=fault):
                changed = deepcopy(receipt)
                if fault == "repo":
                    changed["source"]["repo"] = "Other/fixture"
                elif fault == "ref":
                    changed["source"]["ref"] = "main"
                elif fault == "names":
                    changed["source"]["skills"] = ["unknown"]
                elif fault == "schema":
                    changed.pop("source")
                    changed["schema"] = 2
                elif fault == "float-schema":
                    changed["schema"] = 3.0
                receipt_path.write_text(json.dumps(changed))
                os.chmod(receipt_path, 0o644 if fault == "public" else 0o600)
                if fault == "content":
                    (self.destination / "extra.txt").write_text("unowned")
                self.assertEqual(lifecycle.probe_component(self.extra, self.args.codex_home)[0], "drifted")
                for operation in ("upgrade", "uninstall"):
                    with self.assertRaises(lifecycle.BootstrapError):
                        self.perform(operation)
                self.assertTrue(self.destination.exists())
                self.assertEqual(self.snapshot(self.base), before)
                if fault == "content":
                    (self.destination / "extra.txt").unlink()
        receipt_path.write_text(json.dumps(receipt))
        os.chmod(receipt_path, 0o600)
        receipt_path.unlink()
        with self.assertRaises(lifecycle.BootstrapError):
            self.perform("upgrade")

    def test_uninstall_each_collection_preserves_the_other(self) -> None:
        self.perform("install")
        base = self.snapshot(self.base)
        self.extra["collection_contract"]["source"]["ref"] = "b" * 40
        self.assertEqual(self.perform("uninstall"), "changed")
        self.assertFalse(self.destination.exists())
        self.assertFalse(lifecycle.skills_install.receipt_path(self.destination).exists())
        self.assertEqual(self.snapshot(self.base), base)
        self.perform("install")
        extra = self.snapshot(self.destination)
        self.args.component = "pennix-skills"
        self.assertEqual(self.perform("uninstall"), "changed")
        self.assertEqual(self.snapshot(self.destination), extra)

    def test_destination_catalog_and_missing_upgrade_refuse_before_download(self) -> None:
        with self.assertRaisesRegex(lifecycle.BootstrapError, "missing"):
            self.perform("upgrade")
        self.args.destination = str(self.base)
        with self.assertRaisesRegex(lifecycle.BootstrapError, "destination overrides"):
            self.perform("install")
        self.args.destination = None
        self.args.catalog = self.root / "caller-catalog.json"
        with self.assertRaisesRegex(lifecycle.BootstrapError, "catalog overrides"):
            self.perform("install")
        self.assertFalse(self.destination.exists())
        self.downloader.assert_not_called()

    def test_orphaned_receipt_is_not_adopted_or_removed(self) -> None:
        before = self.snapshot(self.base)
        receipt = lifecycle.skills_install.receipt_path(self.destination)
        receipt.write_text("unknown receipt\n")
        os.chmod(receipt, 0o600)
        for operation in ("install", "upgrade", "uninstall"):
            with self.assertRaises(lifecycle.BootstrapError):
                self.perform(operation)
            self.assertEqual(receipt.read_text(), "unknown receipt\n")
            self.assertEqual(self.snapshot(self.base), before)
        self.downloader.assert_not_called()

    def test_download_timeout_and_spawn_failure_preserve_active_version(self) -> None:
        self.perform("install")
        before = self.snapshot(self.destination), self.snapshot(self.base)
        self.extra["collection_contract"]["source"]["ref"] = "b" * 40
        for error in (subprocess.TimeoutExpired("fixture", 120), OSError("native helper spawn failure")):
            with self.subTest(error=type(error).__name__):
                self.downloader.side_effect = error
                with self.assertRaises(lifecycle.BootstrapError):
                    self.perform("upgrade")
                self.assertEqual((self.snapshot(self.destination), self.snapshot(self.base)), before)
                self.assertEqual(lifecycle.staging_candidates(None, self.args.codex_home), [])

    def test_target_helper_cannot_replace_missing_host_helper(self) -> None:
        target = self.args.codex_home / "skills/.system/skill-installer/scripts"
        target.mkdir(parents=True)
        (target / "install-skill-from-github.py").write_text("# Untrusted target helper\n")
        (target / "github_utils.py").write_text("# Untrusted target dependency\n")
        self.helper.unlink()
        with self.assertRaisesRegex(lifecycle.BootstrapError, "host system installer contract unavailable"):
            self.perform("install")
        self.assertFalse(self.destination.exists())
        self.downloader.assert_not_called()

    def test_helper_comes_from_host_and_requires_safe_package_files(self) -> None:
        self.assertEqual(lifecycle.host_skill_installer(), self.helper)
        for path in (self.helper, self.helper.with_name("github_utils.py"), self.helper.parent):
            previous = stat.S_IMODE(path.stat().st_mode)
            os.chmod(path, previous | 0o020)
            with self.assertRaisesRegex(lifecycle.BootstrapError, "untrusted"):
                lifecycle.host_skill_installer()
            os.chmod(path, previous)
        self.helper.with_name("github_utils.py").unlink()
        with self.assertRaisesRegex(lifecycle.BootstrapError, "unavailable"):
            self.perform("install")
        self.assertFalse(self.destination.exists())
        self.downloader.assert_not_called()

    def test_catalog_rejects_ambiguous_or_unapproved_managed_contracts(self) -> None:
        original = deepcopy(self.value)
        for fault in ("duplicate", "overlap", "directory", "repo", "floating", "escape", "bucket", "adapter", "action", "bootstrap", "commands"):
            with self.subTest(fault=fault):
                self.value = deepcopy(original)
                extra = self.value["components"]["pennix-skills-extra"]
                contract = extra["collection_contract"]
                if fault == "duplicate":
                    contract["skills"].append(contract["skills"][0])
                elif fault == "overlap":
                    contract["skills"].append("pennix-base")
                    contract["source"]["paths"].append("skills/engineering/pennix-base")
                elif fault == "directory":
                    contract["directory"] = "pennix-skills"
                elif fault == "repo":
                    contract["source"]["repo"] = "Other/fixture"
                elif fault == "floating":
                    contract["source"]["ref"] = "main"
                elif fault == "escape":
                    contract["source"]["paths"][0] = "../diagnosing-bugs"
                elif fault == "bucket":
                    contract["source"]["paths"][0] = "skills/misc/diagnosing-bugs"
                elif fault == "adapter":
                    extra["adapter"] = "unknown"
                elif fault == "action":
                    extra["actions"]["install"] = "native-owner"
                elif fault == "bootstrap":
                    contract["bootstrap_skill"] = contract["skills"][0]
                else:
                    contract["commands"] = deepcopy(lifecycle.skills_install.MANAGED_COMMANDS)
                with self.assertRaises(lifecycle.BootstrapError):
                    self.save_catalog()
        self.catalog_path.write_text('{"schema":2,"schema":2,"components":{}}')
        with self.assertRaisesRegex(lifecycle.BootstrapError, "duplicate key"):
            lifecycle.load_catalog(self.catalog_path)


if __name__ == "__main__":
    unittest.main()
