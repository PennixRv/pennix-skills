from __future__ import annotations

import os
import pty
import select
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "seed-arch.sh"


class SeedTests(unittest.TestCase):
    def fake_commands(self, root: Path, *, curl_fixture: Path | None = None, curl_log: Path | None = None) -> tuple[Path, Path]:
        fake_bin = root / "bin"
        fake_bin.mkdir()
        (fake_bin / "pacman").write_text(
            "#!/usr/bin/env bash\n"
            f"printf '%s\\n' \"$*\" >> {root / 'pacman.log'}\n"
            "if [[ \"$1\" == -Si ]]; then echo 'Version        : 0.154.0-1'; exit 0; fi\n"
            "if [[ \"$1\" == -Qq ]]; then exit 1; fi\n"
            "if [[ \"$1\" == -Syu ]]; then exit 0; fi\n"
            "exit 1\n",
            encoding="utf-8",
        )
        (fake_bin / "sudo").write_text("#!/usr/bin/env bash\nexec \"$@\"\n", encoding="utf-8")
        (fake_bin / "codex").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        for command in ("pacman", "sudo", "codex"):
            (fake_bin / command).chmod(0o700)
        if curl_fixture is not None:
            assert curl_log is not None
            (fake_bin / "curl").write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "output=\n"
                "url=\n"
                "while (($#)); do\n"
                "  if [[ \"$1\" == -o ]]; then output=$2; shift 2; continue; fi\n"
                "  url=$1\n"
                "  shift\n"
                "done\n"
                f"printf '%s\\n' \"$url\" >> {curl_log}\n"
                "case \"$url\" in\n"
                "  */config.toml.seed) cp \"$SEED_FIXTURE/config.toml.seed\" \"$output\" ;;\n"
                "  */auth.json.seed) cp \"$SEED_FIXTURE/auth.json.seed\" \"$output\" ;;\n"
                "  *) exit 22 ;;\n"
                "esac\n",
                encoding="utf-8",
            )
            (fake_bin / "curl").chmod(0o700)
        return fake_bin, root / "pacman.log"

    def environment(self, root: Path, fake_bin: Path) -> dict[str, str]:
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
        return environment

    def run_piped_seed(self, environment: dict[str, str], answers: tuple[bytes, bytes]) -> tuple[int, bytes]:
        command = f"cat {shlex.quote(str(SCRIPT))} | bash"
        pid, master = pty.fork()
        if pid == 0:
            os.execvpe("bash", ["bash", "-c", command], environment)
        os.write(master, answers[0])
        output = bytearray()
        secret_sent = False
        deadline = time.monotonic() + 10
        status = None
        eof = False
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    output.extend(os.read(master, 4096))
                except OSError:
                    eof = True
                    break
            if not secret_sent and b"API key (hidden): " in output:
                os.write(master, answers[1])
                secret_sent = True
            waited, result = os.waitpid(pid, os.WNOHANG)
            if waited == pid:
                status = os.waitstatus_to_exitcode(result)
                break
        if status is None and eof:
            _, result = os.waitpid(pid, 0)
            status = os.waitstatus_to_exitcode(result)
        if status is None:
            os.kill(pid, 9)
            os.waitpid(pid, 0)
            self.fail("piped seed timed out: " + output.decode(errors="replace"))
        os.close(master)
        return status, bytes(output)

    def test_shell_syntax(self) -> None:
        result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_fresh_seed_writes_no_secret_to_output_or_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_bin, _ = self.fake_commands(root)
            environment = self.environment(root, fake_bin)
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

    def test_remote_pipe_seed_fetches_only_templates_and_reads_tty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture"
            fixture.mkdir()
            for name in ("config.toml.seed", "auth.json.seed"):
                shutil.copy(SCRIPT.parent.parent / "templates" / name, fixture / name)
            curl_log = root / "curl.log"
            fake_bin, _ = self.fake_commands(root, curl_fixture=fixture, curl_log=curl_log)
            environment = self.environment(root, fake_bin)
            environment.update(
                {
                    "SEED_FIXTURE": str(fixture),
                }
            )
            status, output = self.run_piped_seed(
                environment,
                (b"https://api.example.test/v1\n", b"remote-secret\n"),
            )
            rendered = output.decode(errors="replace")
            self.assertEqual(status, 0, rendered)
            self.assertNotIn("remote-secret", rendered)
            self.assertEqual(
                curl_log.read_text(encoding="utf-8").splitlines(),
                [
                    "https://raw.githubusercontent.com/PennixRv/pennix-skills/main/skills/pennix-workflow-lifecycle/templates/config.toml.seed",
                    "https://raw.githubusercontent.com/PennixRv/pennix-skills/main/skills/pennix-workflow-lifecycle/templates/auth.json.seed",
                ],
            )
            config = (root / "home" / ".codex" / "config.toml").read_text(encoding="utf-8")
            self.assertIn('base_url = "https://api.example.test/v1"', config)
            self.assertNotIn("remote-secret", config)

    def test_remote_pipe_without_tty_fails_before_package_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fixture = root / "fixture"
            fixture.mkdir()
            for name in ("config.toml.seed", "auth.json.seed"):
                shutil.copy(SCRIPT.parent.parent / "templates" / name, fixture / name)
            curl_log = root / "curl.log"
            fake_bin, pacman_log = self.fake_commands(root, curl_fixture=fixture, curl_log=curl_log)
            environment = self.environment(root, fake_bin)
            environment.update({"SEED_FIXTURE": str(fixture)})
            command = f"cat {shlex.quote(str(SCRIPT))} | bash"
            result = subprocess.run(["bash", "-c", command], capture_output=True, text=True, env=environment, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("control terminal", result.stderr)
            self.assertNotIn("-Syu", pacman_log.read_text(encoding="utf-8"))
            self.assertFalse((root / "home" / ".codex" / "config.toml").exists())

    def test_remote_template_download_failure_fails_before_package_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            fake_bin, pacman_log = self.fake_commands(root)
            curl = fake_bin / "curl"
            curl.write_text("#!/usr/bin/env bash\nexit 22\n", encoding="utf-8")
            curl.chmod(0o700)
            environment = self.environment(root, fake_bin)
            result = subprocess.run(
                ["bash", "-c", f"cat {shlex.quote(str(SCRIPT))} | bash"],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot download the remote Codex template", result.stderr)
            self.assertNotIn("-Syu", pacman_log.read_text(encoding="utf-8"))

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

    def test_symlinked_codex_home_is_rejected_before_package_install(self) -> None:
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
            real_home = root / "real-home"
            real_home.mkdir()
            codex_home = root / "codex-link"
            codex_home.symlink_to(real_home, target_is_directory=True)
            environment = os.environ.copy()
            environment.update(
                {
                    "PATH": f"{fake_bin}:{environment['PATH']}",
                    "HOME": str(root / "home"),
                    "CODEX_HOME": str(codex_home),
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
            self.assertIn("symbolic link", result.stderr)
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
