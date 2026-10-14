import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("inspect_chain", Path(__file__).parents[1] / "scripts/inspect_chain.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ChainTests(unittest.TestCase):
    def test_nested_override_empty_fallback_and_user_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            user, root = base / "user", base / "project"
            cwd = root / "nested" / "leaf"
            user.mkdir()
            cwd.mkdir(parents=True)
            (user / "AGENTS.md").write_text("user")
            (root / "AGENTS.md").write_text("root")
            (root / "nested/AGENTS.override.md").write_text("override")
            (root / "nested/AGENTS.md").write_text("shadowed")
            (cwd / "AGENTS.override.md").write_text(" \n")
            (cwd / "TEAM.md").write_text("fallback")
            result = module.inspect_chain(cwd, user, root, ("TEAM.md", "SECOND.md"), config_confirmed=True)
            self.assertEqual([Path(x["path"]).name for x in result["layers"]],
                             ["AGENTS.md", "AGENTS.md", "AGENTS.override.md", "TEAM.md"])
            self.assertEqual(result["layers"][2]["shadowed"], [str(root / "nested/AGENTS.md")])
            self.assertFalse(result["host_loaded"])

    def test_budget_utf8_and_exact_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("规则", encoding="utf8")
            for budget, truncated in [(0, True), (5, True), (6, False)]:
                result = module.inspect_chain(root, root / "missing", max_bytes=budget)
                self.assertEqual(result["layers"][1]["truncated"], truncated)
                self.assertEqual(result["status"], "unknown")
            self.assertEqual((root / "AGENTS.md").read_text(), "规则")

    def test_unreadable_and_no_project_root_do_not_guess_parents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cwd = root / "nested"
            cwd.mkdir()
            (root / "AGENTS.md").write_text("not selected")
            (cwd / "AGENTS.override.md").write_bytes(b"\xff")
            result = module.inspect_chain(cwd, root / "user", config_confirmed=True)
            self.assertEqual(len(result["layers"]), 2)
            self.assertEqual(result["layers"][1]["status"], "unknown")
            self.assertEqual(result["status"], "unknown")

    def test_invalid_roots_and_fallback_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                module.inspect_chain(root, root, root / "elsewhere")
            with self.assertRaises(ValueError):
                module.inspect_chain(root, root, fallbacks=("../AGENTS.md",))


if __name__ == "__main__":
    unittest.main()
