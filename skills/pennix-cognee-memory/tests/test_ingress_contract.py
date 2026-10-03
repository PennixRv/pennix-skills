import ast
import unittest
from pathlib import Path


SOURCE = Path(__file__).parents[1] / "scripts" / "cognee_recall_ingress.py"


class IngressContractTest(unittest.TestCase):
    def test_overlay_keeps_official_route_contract_and_enables_approved_options(self):
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        assignments = {
            node.targets[0].id: node.value
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        }
        self.assertEqual(
            ast.literal_eval(assignments["RETRIEVER_SPECIFIC_CONFIG"]),
            {
                "include_global_context_index": True,
                "use_truth_weight": True,
                "include_external_metadata": True,
            },
        )
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('EXPECTED_COGNEE_VERSION = "1.6.2"', source)
        self.assertIn("retriever_specific_config=RETRIEVER_SPECIFIC_CONFIG", source)
        self.assertIn('getattr(route, "path", None) == "/api/v1/recall"', source)
        self.assertIn('app.include_router(router, prefix="/api/v1/recall"', source)


if __name__ == "__main__":
    unittest.main()
