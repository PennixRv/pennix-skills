from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "seed-arch.sh"


class SeedTests(unittest.TestCase):
    def test_shell_syntax(self) -> None:
        result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fresh_seed_writes_no_secret_to_output_or_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            (fake_bin / "pacman").write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$1\" == -Si ]]; then echo 'Version        : 0.154.0-1'; exit 0; fi\n"
                "if [[ \"$1\" == -Syu ]]; then exit 0; fi\n"
                "exit 1\n",
                encoding="utf-8",
            )
            (fake_bin / "sudo").write_text("#!/usr/bin/env bash\nexec \"$@\"\n", encoding="utf-8")
            (fake_bin / "codex").write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$1\" == login || \"$1\" == features ]]; then exit 99; fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            for command in ("pacman", "sudo", "codex"):
                (fake_bin / command).chmod(0o700)

            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "HOME": str(root / "home"),
                    "XDG_CONFIG_HOME": str(root / "config"),
                    "CODEX_HOME": str(root / "home" / ".codex"),
                    "SHELL": "/bin/bash",
                }
            )
            input_data = "https://api.example.test/v1\nsuper-secret-value\n"
            result = subprocess.run(
                ["bash", str(SCRIPT)],
                input=input_data,
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("super-secret-value", result.stdout)
            self.assertIn("安装 Pennix Skills", result.stdout)
            self.assertNotIn("Stage 1", result.stdout)
            config = (root / "home" / ".codex" / "config.toml").read_text(encoding="utf-8")
            self.assertIn('base_url = "https://api.example.test/v1"', config)
            self.assertIn('cli_auth_credentials_store = "file"', config)
            self.assertIn('requires_openai_auth = true', config)
            self.assertNotIn("env_key", config)
            self.assertNotIn("super-secret-value", config)
            auth_file = root / "home" / ".codex" / "auth.json"
            self.assertIn("super-secret-value", auth_file.read_text(encoding="utf-8"))
            self.assertEqual(auth_file.stat().st_mode & 0o777, 0o600)

    def test_existing_config_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            pacman_log = root / "pacman.log"
            (fake_bin / "pacman").write_text(
                "#!/usr/bin/env bash\n"
                f"printf '%s\\n' \"$*\" >> {pacman_log}\n"
                "if [[ \"$1\" == -Si ]]; then echo 'Version : 0.154.0-1'; exit 0; fi\n"
                "exit 1\n",
                encoding="utf-8",
            )
            (fake_bin / "sudo").write_text("#!/usr/bin/env bash\nexec \"$@\"\n", encoding="utf-8")
            for command in ("pacman", "sudo"):
                (fake_bin / command).chmod(0o700)
            codex_home = root / "home" / ".codex"
            codex_home.mkdir(parents=True)
            config = codex_home / "config.toml"
            config.write_text("model_provider = \"existing\"\n", encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "HOME": str(root / "home"),
                    "XDG_CONFIG_HOME": str(root / "config"),
                    "CODEX_HOME": str(codex_home),
                    "SHELL": "/bin/bash",
                }
            )
            result = subprocess.run(
                ["bash", str(SCRIPT)],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(config.read_text(encoding="utf-8"), "model_provider = \"existing\"\n")
            self.assertFalse(pacman_log.exists())

    def test_conflicting_codex_package_is_rejected_before_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            pacman_log = root / "pacman.log"
            (fake_bin / "pacman").write_text(
                "#!/usr/bin/env bash\n"
                f"printf '%s\\n' \"$*\" >> {pacman_log}\n"
                "if [[ \"$1\" == -Qq && \"$2\" == openai-codex-bin ]]; then exit 0; fi\n"
                "exit 1\n",
                encoding="utf-8",
            )
            (fake_bin / "pacman").chmod(0o700)
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "HOME": str(root / "home"),
                    "XDG_CONFIG_HOME": str(root / "config"),
                    "CODEX_HOME": str(root / "home" / ".codex"),
                    "SHELL": "/bin/bash",
                }
            )
            result = subprocess.run(
                ["bash", str(SCRIPT)],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("openai-codex-bin", result.stderr)
            self.assertEqual(pacman_log.read_text(encoding="utf-8").splitlines(), ["-Qq openai-codex-bin"])

    def test_existing_auth_cache_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            pacman_log = root / "pacman.log"
            (fake_bin / "pacman").write_text(
                "#!/usr/bin/env bash\n"
                f"printf '%s\\n' \"$*\" >> {pacman_log}\n"
                "exit 1\n",
                encoding="utf-8",
            )
            (fake_bin / "pacman").chmod(0o700)
            codex_home = root / "home" / ".codex"
            codex_home.mkdir(parents=True)
            auth_file = codex_home / "auth.json"
            auth_file.write_text('{"existing":true}\n', encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "HOME": str(root / "home"),
                    "XDG_CONFIG_HOME": str(root / "config"),
                    "CODEX_HOME": str(codex_home),
                    "SHELL": "/bin/bash",
                }
            )
            result = subprocess.run(
                ["bash", str(SCRIPT)],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("auth.json", result.stderr)
            self.assertEqual(auth_file.read_text(encoding="utf-8"), '{"existing":true}\n')
            self.assertFalse(pacman_log.exists())

    def test_zsh_caller_uses_bash_shebang(self) -> None:
        if shutil.which("zsh") is None:
            self.skipTest("zsh is not installed")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / "home" / ".codex"
            codex_home.mkdir(parents=True)
            config = codex_home / "config.toml"
            config.write_text("model_provider = \"existing\"\n", encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "HOME": str(root / "home"),
                    "CODEX_HOME": str(codex_home),
                }
            )
            result = subprocess.run(
                ["zsh", "-c", 'exec "$1"', "seed-arch.sh", str(SCRIPT)],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("existing Codex config", result.stderr)
            self.assertEqual(config.read_text(encoding="utf-8"), "model_provider = \"existing\"\n")


if __name__ == "__main__":
    unittest.main()
