import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import collection


class CollectionTests(unittest.TestCase):
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
