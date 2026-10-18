import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/pennix-siyuan-knowledge/scripts"))
import connection


class ConnectionTests(unittest.TestCase):
    def test_write_private_rejects_broken_target_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "connection.json"
            target.symlink_to(root / "missing")
            with self.assertRaises(connection.ConnectionError):
                connection.write_private(target, {"schema": 1})
            self.assertTrue(target.is_symlink())


if __name__ == "__main__":
    unittest.main()
