from pathlib import Path
import re
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class WorkflowRoutingContractTest(unittest.TestCase):
    # Static integrity only; routing behavior requires actual tool-call evidence.
    def test_routing_parameter_identifiers_remain_available(self) -> None:
        identifiers = set(re.findall(r"`([a-z_]+)`", SKILL.read_text(encoding="utf-8")))
        self.assertFalse({
            "work_domain", "delivery_mode", "execution_class", "decision_frontier",
            "approval_mode", "owner", "allowed_transport", "state_writer",
            "exit_conditions", "replan_trigger",
        } - identifiers)

    def test_named_collection_skills_exist(self) -> None:
        names = set(re.findall(r"\$(pennix-[a-z0-9-]+)", SKILL.read_text(encoding="utf-8")))
        self.assertTrue(names)
        for name in names:
            with self.subTest(skill=name):
                self.assertTrue((SKILL.parents[1] / name / "SKILL.md").is_file())

    def test_relative_links_resolve_from_the_loaded_skill_directory(self) -> None:
        links = re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", SKILL.read_text(encoding="utf-8"))
        targets = []
        for link in links:
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link):
                continue
            with self.subTest(link=link):
                target = (SKILL.parent / link).resolve()
                self.assertTrue(target.is_file())
                targets.append(target)
        self.assertIn((SKILL.parents[1] / "pennix-context-mode-integration/SKILL.md").resolve(), targets)
        self.assertIn((SKILL.parent / "references/knowledge-promotion.md").resolve(), targets)


if __name__ == "__main__":
    unittest.main()
