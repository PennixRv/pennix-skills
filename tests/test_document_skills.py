"""Offline provenance and isolated LibreOffice behavior for the four imports."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
NAMES = ("docx", "pdf", "pptx", "xlsx")


class DocumentSkillsTests(unittest.TestCase):
    def test_complete_upstream_files_and_unchanged_bytes(self):
        for name in NAMES:
            with self.subTest(skill=name):
                root = ROOT / "skills" / name
                source = dict(line.split("  ", 1)[::-1] for line in
                              (root / "upstream-files.sha256").read_text().splitlines())
                adapted = {"SKILL.md"}
                added = {"UPSTREAM.md", "upstream-files.sha256"}
                if name != "pdf":
                    adapted.add("scripts/office/soffice.py")
                if name in {"pdf", "pptx"}:
                    added.add("THIRD_PARTY_NOTICES.md")
                actual = {str(p.relative_to(root)) for p in root.rglob("*")
                          if p.is_file() and "__pycache__" not in p.parts}
                self.assertEqual(actual, set(source) | added)
                for path, digest in source.items():
                    if path not in adapted:
                        self.assertEqual(hashlib.sha256((root / path).read_bytes()).hexdigest(), digest, path)
                self.assertEqual(hashlib.sha256((root / "LICENSE.txt").read_bytes()).hexdigest(),
                                 "58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd")

    def test_soffice_profile_lifetime_and_failure_are_preserved(self):
        for name in ("docx", "pptx", "xlsx"):
            spec = importlib.util.spec_from_file_location(
                "document_soffice_" + name, ROOT / "skills" / name / "scripts/office/soffice.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            profiles = []

            def run(command, **kwargs):
                self.assertEqual(command[0], "soffice")
                uri = command[1].split("=", 1)[1]
                profile = Path(unquote(urlsplit(uri).path))
                profiles.append(profile)
                self.assertIn("MacroSecurityLevel", (profile / "user/registrymodifications.xcu").read_text())
                self.assertEqual(kwargs["env"]["SAL_USE_VCLPLUGIN"], "svp")
                self.assertNotIn("LD_PRELOAD", kwargs["env"])
                return subprocess.CompletedProcess(command, 7)

            with patch.dict(module.os.environ, {}, clear=True), patch.object(module.subprocess, "run", side_effect=run):
                self.assertEqual(module.run_soffice(["--headless", "--convert-to", "pdf", "input.docx"]).returncode, 7)
            self.assertFalse(profiles[0].exists())


if __name__ == "__main__":
    unittest.main()
