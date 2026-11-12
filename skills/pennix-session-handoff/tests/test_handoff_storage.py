"""Lossless ZIP and storage trust-boundary regressions (synthetic private data)."""

import hashlib
import json
import shutil
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import handoff_storage as storage


class StorageTests(unittest.TestCase):
    identifier = "20261112T034906500836Z"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = storage.package_directory(self.root, self.identifier)
        self.directory.mkdir(parents=True)
        self.originals = {
            "session-handoff.json": b'{"schema_version":12}',
            "session-handoff-history.jsonl": ('{"text":"中文😀"}\n' * 1000).encode(),
            "session-handoff-prompt.md": "恢复现场，不执行后续动作\n".encode(),
            "lifecycle.jsonl": b'{"original":"receipt"}\n',
        }
        for name, data in self.originals.items():
            (self.directory / name).write_bytes(data)
        self.archive = storage.zip_path(self.root, self.identifier)

    def write(self):
        return storage.write(self.archive, self.identifier, storage.sources(self.root, self.identifier), self.root)

    def test_every_original_byte_survives_zip_and_transparent_read(self):
        manifest = self.write()
        self.assertEqual(set(manifest["members"]), set(self.originals))
        self.assertTrue(self.directory.is_dir(), "archive never deletes the expanded source")
        for name, data in self.originals.items():
            self.assertEqual(manifest["members"][name]["sha256"], hashlib.sha256(data).hexdigest())
        shutil.rmtree(self.directory)
        with storage.open_package(self.root, self.identifier) as (directory, kind):
            self.assertEqual(kind, "zip")
            for name, data in self.originals.items():
                self.assertEqual((directory / name).read_bytes(), data)
            private = directory
        self.assertFalse(private.exists())
        self.assertEqual(self.archive.stat().st_mode & 0o777, 0o600)

    def test_control_extension_does_not_change_content_identity(self):
        first = self.write()
        (self.directory / storage.LIFECYCLE).write_bytes(b'next receipt\n')
        second = self.write()
        self.assertEqual(first["content_digest"], second["content_digest"])
        self.assertNotEqual(first["members"][storage.LIFECYCLE], second["members"][storage.LIFECYCLE])

    def test_unknown_member_symlink_and_preview_drift_are_protected(self):
        before = storage.snapshot(self.root, self.identifier)
        (self.directory / "unknown").write_text("keep me")
        with self.assertRaisesRegex(storage.ContractError, "unknown"):
            storage.sources(self.root, self.identifier)
        (self.directory / "unknown").unlink()
        (self.directory / "session-handoff-prompt.md").write_text("changed")
        with self.assertRaisesRegex(storage.ContractError, "changed"):
            storage.unchanged(self.root, self.identifier, before)
        target = self.directory / "session-handoff-history.jsonl"
        target.unlink()
        target.symlink_to(self.directory / "session-handoff.json")
        with self.assertRaisesRegex(storage.ContractError, "symlink"):
            storage.sources(self.root, self.identifier)

    def test_zip_traversal_duplicate_symlink_hash_and_budget_rejected(self):
        self.write()
        original = self.archive.read_bytes()
        for name in ("../outside", "/absolute", "legacy/../outside", "legacy/./x", "legacy\\x", "unknown"):
            with self.subTest(name=name):
                self.archive.write_bytes(original)
                with zipfile.ZipFile(self.archive, "a") as archive:
                    archive.writestr(name, b"untrusted")
                with self.assertRaises(storage.ContractError):
                    storage.verify(self.archive, self.identifier)
        self.archive.write_bytes(original)
        with zipfile.ZipFile(self.archive, "a") as archive:
            info = zipfile.ZipInfo("legacy/link")
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, "../outside")
        with self.assertRaises(storage.ContractError):
            storage.verify(self.archive, self.identifier)
        self.archive.write_bytes(original)
        with mock.patch.object(storage, "MAX_EXPANDED_BYTES", 1):
            with self.assertRaisesRegex(storage.ContractError, "budget"):
                storage.verify(self.archive, self.identifier)
        self.archive.write_bytes(original)
        with zipfile.ZipFile(self.archive, "a") as archive:
            archive.writestr("session-handoff.json", b"different")
        with self.assertRaisesRegex(storage.ContractError, "member set"):
            storage.verify(self.archive, self.identifier)

    def test_content_tamper_and_wrong_identity_are_rejected(self):
        manifest = self.write()
        with zipfile.ZipFile(self.archive) as archive:
            data = {name: archive.read(name) for name in archive.namelist()}
        data["session-handoff.json"] = b"tampered"
        with zipfile.ZipFile(self.archive, "w") as archive:
            for name, raw in data.items():
                archive.writestr(name, raw)
        with self.assertRaises(storage.ContractError):
            storage.verify(self.archive, self.identifier)
        self.write()
        with self.assertRaisesRegex(storage.ContractError, "identity"):
            storage.verify(self.archive, "20261112T034906500837Z")
        self.assertEqual(manifest["handoff_id"], self.identifier)

    def test_known_legacy_archive_is_preserved_without_rewriting(self):
        legacy = self.root / ".trellis/.runtime/handoff-archive" / self.identifier
        legacy.mkdir(parents=True)
        for name in storage.PRIMARY:
            (legacy / name).write_bytes(self.originals[name])
        shutil.rmtree(self.directory)
        manifest = self.write()
        for name in storage.PRIMARY:
            self.assertIn("legacy/handoff-archive/" + name, manifest["members"])
            self.assertEqual((legacy / name).read_bytes(), self.originals[name])
        with self.assertRaisesRegex(storage.ContractError, "identifier"):
            storage.package_directory(self.root, "../other")

    def test_operation_manifest_must_match_the_preserved_journal(self):
        operation = {"action": "archive", "status": "committed"}
        storage.append_operation(self.directory / storage.JOURNAL, self.identifier, operation)
        with self.assertRaisesRegex(storage.ContractError, "retention proof"):
            self.write()
        storage.write(self.archive, self.identifier, storage.sources(self.root, self.identifier), self.root, operation=operation)
        self.assertEqual(storage.verify(self.archive, self.identifier)["operation"], operation)


if __name__ == "__main__":
    unittest.main()
