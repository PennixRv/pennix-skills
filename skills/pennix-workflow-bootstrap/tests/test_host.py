from __future__ import annotations

import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

import host


class HostTests(unittest.TestCase):
    def detect(self, os_release: str, kernel: str, version: str = "") -> dict[str, object]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "os-release").write_text(os_release, encoding="utf-8")
            (root / "osrelease").write_text(kernel, encoding="utf-8")
            (root / "version").write_text(version, encoding="utf-8")
            return host.detect_host(
                root / "os-release",
                root / "osrelease",
                root / "version",
                which=lambda name: f"/usr/bin/{name}" if name in {"pacman", "yay", "npm"} else None,
            )

    def test_native_arch_uses_pacman_for_official_packages(self) -> None:
        detected = self.detect("ID=arch\n", "6.18.1-arch1-1\n")
        self.assertTrue(detected["supported"])
        self.assertEqual(detected["environment"], "native")
        self.assertEqual(detected["installers"]["official"], "pacman")
        self.assertEqual(detected["installers"]["aur"], "yay")
        self.assertEqual(detected["installers"]["npm"], "npm")

    def test_wsl2_arch_is_supported(self) -> None:
        detected = self.detect(
            "ID=arch\n",
            "6.18.33.2-microsoft-standard-WSL2\n",
            "Linux version 6.18.33.2-microsoft-standard-WSL2\n",
        )
        self.assertTrue(detected["supported"])
        self.assertEqual(detected["environment"], "wsl")
        self.assertEqual(detected["wsl_version"], "2")

    def test_aur_prefers_yay_and_falls_back_to_paru(self) -> None:
        self.assertEqual(host.select_installer("aur", {"yay": True, "paru": True}), "yay")
        self.assertEqual(host.select_installer("aur", {"yay": False, "paru": True}), "paru")
        self.assertIsNone(host.select_installer("aur", {"yay": False, "paru": False}))

    def test_package_commands_preserve_owner_confirmation(self) -> None:
        self.assertEqual(
            host.package_install_command("pacman", "openai-codex"),
            ["sudo", "pacman", "-S", "--needed", "openai-codex"],
        )
        self.assertEqual(
            host.package_install_command("yay", "codegraph-bin"),
            ["yay", "-S", "--needed", "codegraph-bin"],
        )
        self.assertEqual(
            host.package_install_command("npm", "@example/fixture@1.2.3", "https://registry.npmjs.org/"),
            [
                "npm",
                "install",
                "--global",
                "--ignore-scripts",
                "--include=optional",
                "--registry",
                "https://registry.npmjs.org/",
                "@example/fixture@1.2.3",
            ],
        )

    def test_non_arch_and_unknown_wsl_are_blocked(self) -> None:
        non_arch = self.detect("ID=ubuntu\n", "6.1.0-generic\n")
        self.assertFalse(non_arch["supported"])
        unknown_wsl = self.detect("ID=arch\n", "4.4.0-Microsoft\n")
        self.assertFalse(unknown_wsl["supported"])


if __name__ == "__main__":
    unittest.main()
