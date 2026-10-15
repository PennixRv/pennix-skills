from pathlib import Path
import re
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class FastCtxRoutingContractTest(unittest.TestCase):
    def test_referenced_skills_are_available_in_the_collection(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        references = set(re.findall(r"\$(pennix-[a-z0-9-]+)", content))
        self.assertTrue(references)
        for name in references:
            with self.subTest(skill=name):
                self.assertTrue((SKILL.parents[1] / name / "SKILL.md").is_file())

    def test_delegated_recovery_contract_is_resolvable(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        links = re.findall(r"\]\(([^)]+)\)", content)
        self.assertTrue(links)
        for link in links:
            with self.subTest(link=link):
                target = (SKILL.parent / link).resolve()
                self.assertTrue(target.is_relative_to(SKILL.parents[1].resolve()))
                self.assertTrue(target.is_file())

    def test_fastctx_parameter_identifiers_remain_documented(self) -> None:
        content = SKILL.read_text(encoding="utf-8")
        identifiers = set(re.findall(r"`([^`]+)`", content))
        self.assertTrue({"file_path", "path", "pattern", "command", "cwd",
                         "timeout_ms", "login_shell", "encoding"}.issubset(identifiers))


if __name__ == "__main__":
    unittest.main()
