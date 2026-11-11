from pathlib import Path
import re
import unittest


SKILL = Path(__file__).parents[1] / "SKILL.md"


class GovernanceReferencesTest(unittest.TestCase):
    # Document integrity only; native writer behavior belongs to composition tests.
    def test_operation_reference_and_owner_navigation_resolve(self):
        pending = [SKILL]
        visited = set()
        while pending:
            document = pending.pop()
            if document in visited:
                continue
            visited.add(document)
            content = document.read_text(encoding="utf-8")
            for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", content):
                if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link):
                    continue
                target = (document.parent / link).resolve()
                with self.subTest(document=document, link=link):
                    self.assertTrue(target.is_file())
                if target.is_relative_to(SKILL.parent.resolve()):
                    pending.append(target)
            for name in re.findall(r"\$(pennix-[a-z0-9-]+)", content):
                with self.subTest(document=document, owner=name):
                    self.assertTrue((SKILL.parent.parent / name / "SKILL.md").is_file())
        self.assertIn((SKILL.parent / "references/project-operations.md").resolve(), visited)


if __name__ == "__main__":
    unittest.main()
