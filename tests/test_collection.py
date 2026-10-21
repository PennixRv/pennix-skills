from copy import deepcopy
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import collection


class CollectionTests(unittest.TestCase):
    def test_sources_validates_manifest_before_members_are_materialized(self):
        source = {
            "repo": "example/skill", "ref": "a" * 40, "commit": "a" * 40,
            "name": "example-skill", "snapshot": "archive",
        }
        manifest = {
            "schema": 1, "name": "pennix-skills",
            "skills": {"example-skill": {"path": "skills/example-skill", "license": None}},
            "commands": {}, "materialized": {"example-skill": source},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "collection.json").write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(collection, "ROOT", root), patch.object(sys, "argv", ["collection.py", "sources"]):
                output = StringIO()
                with redirect_stdout(output):
                    self.assertEqual(collection.main(), 0)
                self.assertEqual(json.loads(output.getvalue()), manifest["materialized"])
                manifest["materialized"]["example-skill"]["ref"] = "main"
                (root / "collection.json").write_text(json.dumps(manifest), encoding="utf-8")
                with redirect_stderr(StringIO()):
                    self.assertEqual(collection.main(), 1)

    def test_invalid_shapes_and_materialization_inputs_fail_with_contract_errors(self):
        source = {
            "repo": "example/skill", "ref": "a" * 40, "commit": "a" * 40,
            "name": "example-skill", "snapshot": "archive", "post_install": [],
        }
        manifest = {
            "schema": 1, "name": "pennix-skills",
            "skills": {"example-skill": {"path": "skills/example-skill", "license": None}},
            "commands": {}, "materialized": {"example-skill": source},
        }
        invalid = [None, [], {**manifest, "schema": True}, {**manifest, "skills": {}},
                   {**manifest, "commands": []}, {**manifest, "materialized": []}]
        for field, value in (("repo", None), ("ref", []), ("ref", "main"),
                             ("commit", "b" * 40), ("name", "other-skill"),
                             ("snapshot", []), ("post_install", ["arbitrary-script"]),
                             ("unexpected", True)):
            item = deepcopy(manifest)
            item["materialized"]["example-skill"][field] = value
            invalid.append(item)
        for path in ("other/example-skill", "skills/../example-skill", "/example-skill"):
            item = deepcopy(manifest)
            item["skills"]["example-skill"]["path"] = path
            invalid.append(item)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for item in invalid:
                with self.subTest(manifest=item):
                    (root / "collection.json").write_text(json.dumps(item), encoding="utf-8")
                    with patch.object(collection, "ROOT", root), self.assertRaises(collection.ContractError):
                        collection.load_manifest()

    def test_duplicate_json_and_yaml_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "collection.json").write_text('{"schema": 1, "schema": 1}', encoding="utf-8")
            with patch.object(collection, "ROOT", root), self.assertRaisesRegex(collection.ContractError, "duplicate JSON"):
                collection.load_manifest()
        with self.assertRaisesRegex(collection.ContractError, "duplicate YAML"):
            collection.yaml.load("name: first\nname: second\n", Loader=collection.UniqueLoader)

    def test_nested_source_path_and_member_relative_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = root / "skills/example-skill"
            (member / "bin").mkdir(parents=True)
            (member / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: test\n---\n", encoding="utf-8"
            )
            command = member / "bin/example"
            command.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            command.chmod(0o755)
            manifest = {
                "schema": 1,
                "name": "pennix-skills",
                "skills": {"example-skill": {"path": "skills/example-skill", "license": None}},
                "commands": {"example": "example-skill/bin/example"},
                "materialized": {},
            }
            (root / "collection.json").write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(collection, "ROOT", root):
                collection.verify()
                (root / "skills/unlisted.txt").write_text("unexpected", encoding="utf-8")
                with self.assertRaisesRegex(collection.ContractError, "top-level"):
                    collection.verify()
                (root / "skills/unlisted.txt").unlink()
                (member / "external").symlink_to(root / "collection.json")
                with self.assertRaisesRegex(collection.ContractError, "symbolic link"):
                    collection.verify()

    def test_command_must_use_installed_member_relative_path(self):
        manifest = {
            "schema": 1,
            "name": "pennix-skills",
            "skills": {"example-skill": {"path": "skills/example-skill", "license": None}},
            "commands": {"example": "skills/example-skill/bin/example"},
            "materialized": {},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "collection.json").write_text(json.dumps(manifest), encoding="utf-8")
            with patch.object(collection, "ROOT", root), self.assertRaises(collection.ContractError):
                collection.load_manifest()


if __name__ == "__main__":
    unittest.main()
