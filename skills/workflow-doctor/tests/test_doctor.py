from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "doctor.py"


class WorkflowDoctorTests(unittest.TestCase):
    def make_project(self, root: Path) -> None:
        (root / ".trellis/scripts").mkdir(parents=True)
        (root / ".trellis/workflow.md").write_text("# Workflow\n", encoding="utf-8")
        (root / ".trellis/scripts/task.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        (root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")
        (root / ".agents/skills/trellis-start").mkdir(parents=True)
        (root / ".agents/skills/trellis-start/SKILL.md").write_text(
            "---\nname: trellis-start\ndescription: Test Skill.\n---\n",
            encoding="utf-8",
        )

    def run_doctor(self, root: Path) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--project-root", str(root)],
            capture_output=True,
            text=True,
            check=False,
        )
        return result, json.loads(result.stdout)

    def test_reports_healthy_project_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow-doctor-") as temporary:
            root = Path(temporary)
            self.make_project(root)

            result, payload = self.run_doctor(root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["malformed_project_skill_dirs"], [])
            self.assertEqual(payload["trellis"]["status"], "missing")
            self.assertFalse(payload["trellis_checkout_required"])
            self.assertFalse(payload["mutated"])

    def test_optional_non_git_checkout_does_not_degrade_consumer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow-doctor-") as temporary:
            root = Path(temporary)
            self.make_project(root)
            (root / "Trellis/packages/cli").mkdir(parents=True)
            (root / "Trellis/packages/cli/package.json").write_text('{"name":"@pennixrv/trellis"}\n')
            result, payload = self.run_doctor(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["package_scope"], "@pennixrv/trellis")
            self.assertEqual(payload["trellis"]["status"], "unavailable")

    def test_missing_required_generated_asset_is_degraded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow-doctor-") as temporary:
            root = Path(temporary)
            self.make_project(root)
            (root / ".trellis/scripts/task.py").unlink()
            result, payload = self.run_doctor(root)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["status"], "degraded")

    def test_reports_project_skill_directory_without_skill_markdown(self) -> None:
        with tempfile.TemporaryDirectory(prefix="workflow-doctor-") as temporary:
            root = Path(temporary)
            self.make_project(root)
            (root / ".agents/skills/trellis-document-governance/scripts").mkdir(parents=True)

            result, payload = self.run_doctor(root)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["status"], "degraded")
            self.assertEqual(
                payload["malformed_project_skill_dirs"],
                [".agents/skills/trellis-document-governance"],
            )
            self.assertFalse(payload["mutated"])


if __name__ == "__main__":
    unittest.main()
