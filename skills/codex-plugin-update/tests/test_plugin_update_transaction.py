#!/usr/bin/env python3
"""Integration tests for the recoverable Codex plugin update transaction."""

from __future__ import annotations

import json
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


TOOL = Path(__file__).parents[1] / "scripts" / "plugin-update-transaction.py"
PLUGIN = "fixture-plugin@fixture-marketplace"
OLD_VERSION = "1.0.0"
TARGET_VERSION = "2.0.0"

SPEC = importlib.util.spec_from_file_location("plugin_update_transaction", TOOL)
assert SPEC is not None and SPEC.loader is not None
TRANSACTION_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRANSACTION_MODULE)


def write(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    if executable:
        path.chmod(0o755)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result.stdout


class PluginUpdateTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="plugin-update-transaction-")
        self.temp_root = Path(self.temporary.name)
        self.codex_home = self.temp_root / "codex-home"
        self.project_root = self.temp_root / "project"
        self.bin_root = self.temp_root / "bin"
        self.state_path = self.temp_root / "plugin-state.json"
        self.task_state_path = self.project_root / ".trellis" / ".runtime-task.json"
        self.codex_home.mkdir(mode=0o700)
        self.project_root.mkdir()
        self.bin_root.mkdir()
        self._create_codex_home()
        self._create_project()
        self._write_plugin_state(OLD_VERSION)
        self._write_hook(OLD_VERSION)
        self.environment = os.environ.copy()
        self.environment.update(
            {
                "CODEX_HOME": str(self.codex_home),
                "CODEX_THREAD_ID": "fixture-thread-old",
                "FAKE_PLUGIN_STATE": str(self.state_path),
                "FAKE_TARGET_VERSION": TARGET_VERSION,
                "PATH": f"{self.bin_root}{os.pathsep}{self.environment.get('PATH', '')}",
            }
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _create_codex_home(self) -> None:
        write(
            self.codex_home / ".gitignore",
            """
            /plugins/
            /.local-backup/
            /.tmp/
            """,
        )
        write(self.codex_home / "AGENTS.md", "# fixture Codex home\n")
        write(self.codex_home / "hooks.json", '{"hooks": {}}\n')
        write(
            self.codex_home / "skills/codex-plugin-update/scripts/plugin-update-transaction.py",
            "# fixture transaction tool\n",
        )
        write(
            self.bin_root / "codex",
            r"""
            #!/usr/bin/env python3
            import json
            import hashlib
            import os
            import shutil
            import sys
            from pathlib import Path

            state_path = Path(os.environ["FAKE_PLUGIN_STATE"])
            codex_home = Path(os.environ["CODEX_HOME"])
            state = json.loads(state_path.read_text(encoding="utf-8"))
            marketplace_root = codex_home / ".tmp/marketplaces/fixture-marketplace"

            if sys.argv[1:] == ["app-server", "--stdio"]:
                for line in sys.stdin:
                    request = json.loads(line)
                    if "id" not in request:
                        continue
                    method = request.get("method")
                    if method == "initialize":
                        result = {
                            "userAgent": "fixture-app-server",
                            "platformFamily": "unix",
                            "platformOs": "linux",
                        }
                    elif method == "hooks/list":
                        version = state["version"]
                        current_hash = "sha256:" + hashlib.sha256(version.encode()).hexdigest()
                        result = {"data": [{"hooks": [{
                            "pluginId": "fixture-plugin@fixture-marketplace",
                            "eventName": "preToolUse",
                            "enabled": True,
                            "trustStatus": (
                                "untrusted"
                                if os.environ.get("FAKE_HOOK_RUNTIME_MODE") == "untrusted"
                                or os.environ.get("FAKE_UNTRUSTED_VERSION") == version
                                else "trusted"
                            ),
                            "currentHash": current_hash,
                        }]}]}
                    else:
                        print(json.dumps({
                            "jsonrpc": "2.0",
                            "id": request["id"],
                            "error": {"code": -32601, "message": "unknown method"},
                        }), flush=True)
                        continue
                    print(json.dumps({
                        "jsonrpc": "2.0",
                        "id": request["id"],
                        "result": result,
                    }), flush=True)
                raise SystemExit(0)

            if sys.argv[1:] == ["plugin", "list", "--json"]:
                print(json.dumps({"installed": [{
                    "pluginId": "fixture-plugin@fixture-marketplace",
                    "name": "fixture-plugin",
                    "marketplaceName": "fixture-marketplace",
                    "version": state["version"],
                    "installed": True,
                    "enabled": state.get("enabled", True),
                }], "available": []}))
                raise SystemExit(0)

            if sys.argv[1:] == ["mcp", "list", "--json"]:
                version = state["version"]
                cache = (
                    codex_home
                    / "plugins/cache/fixture-marketplace/fixture-plugin"
                    / version
                )
                print(json.dumps([{
                    "name": "fixture-mcp",
                    "enabled": True,
                    "transport": {
                        "type": "stdio",
                        "command": "/usr/bin/sleep",
                        "args": ["120"],
                        "cwd": str(cache),
                        "env": {"IGNORED_SECRET": "must-not-be-copied"},
                        "env_vars": [],
                    },
                }]))
                raise SystemExit(0)

            if sys.argv[1:] == ["plugin", "marketplace", "list", "--json"]:
                source_type = os.environ.get("FAKE_MARKETPLACE_TYPE", "git")
                marketplace = {
                    "name": "fixture-marketplace",
                    "root": str(marketplace_root),
                }
                if source_type != "builtin":
                    marketplace["marketplaceSource"] = {
                        "sourceType": source_type,
                        "source": (
                            "https://example.invalid/fixture.git"
                            if source_type == "git"
                            else str(marketplace_root)
                        ),
                    }
                print(json.dumps({"marketplaces": [marketplace]}))
                raise SystemExit(0)

            if sys.argv[1:] == [
                "plugin", "marketplace", "upgrade", "fixture-marketplace", "--json"
            ]:
                mode = os.environ.get("FAKE_REFRESH_MODE")
                if mode == "fail-before-change":
                    print("fixture refresh failure", file=sys.stderr)
                    raise SystemExit(19)
                if mode == "output-too-large":
                    print("x" * (2 * 1024 * 1024 + 1))
                    raise SystemExit(0)
                if mode == "invalid-json":
                    print("not-json")
                    raise SystemExit(0)
                state["refreshed"] = True
                state_path.write_text(json.dumps(state), encoding="utf-8")
                print(json.dumps({"name": "fixture-marketplace", "updated": True}))
                raise SystemExit(0)

            if sys.argv[1:] == [
                "plugin", "add", "fixture-plugin@fixture-marketplace", "--json"
            ]:
                if (
                    os.environ.get("FAKE_MARKETPLACE_TYPE", "git") == "git"
                    and state.get("refreshed") is not True
                ):
                    print("marketplace was not refreshed", file=sys.stderr)
                    raise SystemExit(18)
                if os.environ.get("FAKE_INSTALL_MODE") == "fail-before-change":
                    print("fixture install failure", file=sys.stderr)
                    raise SystemExit(17)
                if os.environ.get("FAKE_INSTALL_MODE") == "output-too-large":
                    print("x" * (2 * 1024 * 1024 + 1))
                    raise SystemExit(0)
                target = (
                    "3.0.0"
                    if os.environ.get("FAKE_INSTALL_MODE") == "wrong-version"
                    else os.environ["FAKE_TARGET_VERSION"]
                )
                cache = codex_home / "plugins/cache/fixture-marketplace/fixture-plugin"
                shutil.rmtree(cache, ignore_errors=True)
                if os.environ.get("FAKE_INSTALL_MODE") != "success-missing-hook":
                    hook = cache / target / "hooks/hooks.json"
                    hook.parent.mkdir(parents=True)
                    hook.write_text('{"hooks":{"PreToolUse":[]}}\n', encoding="utf-8")
                if os.environ.get("FAKE_MCP_ENABLED") == "1":
                    mcp = cache / target / ".codex-plugin/mcp.json"
                    mcp.parent.mkdir(parents=True, exist_ok=True)
                    mcp.write_text(json.dumps({"mcpServers": {"fixture-mcp": {
                        "command": "/usr/bin/sleep",
                        "args": ["120"],
                        "cwd": ".",
                    }}}), encoding="utf-8")
                state["version"] = target
                state_path.write_text(json.dumps(state), encoding="utf-8")
                print(json.dumps({
                    "pluginId": "fixture-plugin@fixture-marketplace",
                    "version": target,
                }))
                raise SystemExit(0)

            print("unsupported fake codex invocation", file=sys.stderr)
            raise SystemExit(2)
            """,
            executable=True,
        )
        marketplace_root = self.codex_home / ".tmp/marketplaces/fixture-marketplace"
        marketplace_root.mkdir(parents=True)
        write(marketplace_root / "marketplace.json", '{"name":"fixture"}\n')
        git(marketplace_root, "init", "-q")
        git(marketplace_root, "config", "user.name", "Fixture")
        git(marketplace_root, "config", "user.email", "fixture@example.invalid")
        git(marketplace_root, "add", "marketplace.json")
        git(marketplace_root, "commit", "-qm", "fixture marketplace")
        git(self.codex_home, "init", "-q")
        git(self.codex_home, "config", "user.name", "Fixture")
        git(self.codex_home, "config", "user.email", "fixture@example.invalid")
        git(
            self.codex_home,
            "add",
            ".gitignore",
            "AGENTS.md",
            "hooks.json",
            "skills/codex-plugin-update/scripts/plugin-update-transaction.py",
        )
        git(self.codex_home, "commit", "-qm", "fixture codex home")

    def _create_project(self) -> None:
        write(
            self.project_root / ".gitignore",
            """
            /.trellis/.runtime-task.json
            /.trellis/.runtime/
            """,
        )
        write(
            self.project_root / ".trellis/scripts/task.py",
            """
            #!/usr/bin/env python3
            import json
            from pathlib import Path
            print(json.dumps({
                "current_task": json.loads(
                    (Path(__file__).parents[1] / ".runtime-task.json").read_text(encoding="utf-8")
                )
            }))
            """,
            executable=True,
        )
        self._write_task("in_progress")
        write(self.project_root / "README.md", "fixture project\n")
        git(self.project_root, "init", "-q")
        git(self.project_root, "config", "user.name", "Fixture")
        git(self.project_root, "config", "user.email", "fixture@example.invalid")
        git(self.project_root, "add", ".gitignore", ".trellis", "README.md")
        git(self.project_root, "commit", "-qm", "fixture project")

    def _write_task(self, status: str, task_id: str = "fixture-task") -> None:
        self.task_state_path.parent.mkdir(parents=True, exist_ok=True)
        self.task_state_path.write_text(
            json.dumps(
                {
                    "dir": ".trellis/tasks/fixture-task",
                    "id": task_id,
                    "status": status,
                }
            ),
            encoding="utf-8",
        )

    def _write_plugin_state(self, version: str, *, enabled: bool = True) -> None:
        self.state_path.write_text(
            json.dumps({"version": version, "enabled": enabled, "refreshed": False}),
            encoding="utf-8",
        )

    def _write_hook(self, version: str) -> None:
        hook = (
            self.codex_home
            / "plugins/cache/fixture-marketplace/fixture-plugin"
            / version
            / "hooks/hooks.json"
        )
        write(hook, '{"hooks":{"PreToolUse":[]}}\n')

    def _write_mcp_manifest(self, version: str, *, command: str = "/usr/bin/node") -> Path:
        cache = (
            self.codex_home
            / "plugins/cache/fixture-marketplace/fixture-plugin"
            / version
        )
        write(
            cache / ".codex-plugin/mcp.json",
            json.dumps(
                {
                    "mcpServers": {
                        "fixture-mcp": {
                            "command": command,
                            "args": ["server.js"],
                            "cwd": ".",
                            "env": {"IGNORED_SECRET": "must-not-be-copied"},
                        }
                    }
                }
            ),
        )
        return cache

    def _start_mcp_process(self, cwd: Path) -> subprocess.Popen[bytes]:
        return subprocess.Popen(
            ["/usr/bin/sleep", "120"],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop_process(self, process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)

    def _write_proc_process(
        self,
        proc_root: Path,
        pid: int,
        parent_pid: int,
        *,
        cwd: str,
        executable: str = "/usr/bin/node",
    ) -> None:
        process_root = proc_root / str(pid)
        process_root.mkdir(parents=True)
        fields = ["S", str(parent_pid), *(["0"] * 18)]
        write(process_root / "stat", f"{pid} (fixture-mcp) {' '.join(fields)}\n")
        write(process_root / "comm", "node-MainThread\n")
        (process_root / "cwd").symlink_to(cwd)
        (process_root / "exe").symlink_to(executable)

    def run_tool(
        self,
        *arguments: str,
        thread: str | None = None,
        expect_success: bool = True,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object] | None]:
        environment = self.environment.copy()
        if thread is not None:
            environment["CODEX_THREAD_ID"] = thread
        result = subprocess.run(
            [sys.executable, str(TOOL), *arguments],
            cwd=self.project_root,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if expect_success and result.returncode != 0:
            self.fail(f"tool failed: {result.stderr}")
        if not expect_success and result.returncode == 0:
            self.fail(f"tool unexpectedly passed: {result.stdout}")
        payload = json.loads(result.stdout) if result.stdout.strip() else None
        return result, payload

    def prepare(self, *, preserve_process_identity: bool = False) -> str:
        _, payload = self.run_tool(
            "prepare",
            "--plugin",
            PLUGIN,
            "--target-version",
            TARGET_VERSION,
            "--project-root",
            str(self.project_root),
        )
        assert payload is not None
        transaction_id = str(payload["transaction_id"])
        if not preserve_process_identity:
            transaction = self.transaction_payload(transaction_id)
            transaction.pop("origin_process", None)
            self.rewrite_transaction(transaction_id, transaction)
        return transaction_id

    def transaction_payload(self, transaction_id: str) -> dict[str, object]:
        path = (
            self.codex_home
            / ".local-backup/plugin-update-transactions"
            / transaction_id
            / "transaction.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def rewrite_transaction(self, transaction_id: str, payload: dict[str, object]) -> None:
        path = (
            self.codex_home
            / ".local-backup/plugin-update-transactions"
            / transaction_id
            / "transaction.json"
        )
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_prepare_install_recover_requires_new_session(self) -> None:
        transaction_id = self.prepare()
        _, status = self.run_tool("status", "--transaction", transaction_id)
        self.assertEqual(status["effective_state"], "prepared")

        _, installed = self.run_tool("install", "--transaction", transaction_id)
        self.assertEqual(installed["state"], "restart_required")
        self.assertEqual(installed["action_required"], "restart_codex_now")
        transaction_after_install = self.transaction_payload(transaction_id)
        self.assertEqual(
            transaction_after_install["marketplace_after_refresh"]["source_type"],
            "git",
        )
        self.assertTrue(json.loads(self.state_path.read_text())["refreshed"])
        self.assertFalse(
            (
                self.codex_home
                / "plugins/cache/fixture-marketplace/fixture-plugin"
                / OLD_VERSION
            ).exists()
        )

        result, _ = self.run_tool(
            "recover", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("newly started Codex process", result.stderr)
        _, recovered = self.run_tool(
            "recover", "--transaction", transaction_id, thread="fixture-thread-new"
        )
        self.assertEqual(recovered["state"], "completed")
        transaction = json.dumps(self.transaction_payload(transaction_id))
        self.assertNotIn("fixture-thread-old", transaction)
        self.assertNotIn("fixture-thread-new", transaction)

    def test_git_marketplace_refresh_failure_requires_restart(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_REFRESH_MODE"] = "fail-before-change"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("marketplace refresh failed", result.stderr)
        self.assertIn("restart Codex now", result.stderr)
        self.assertEqual(
            self.transaction_payload(transaction_id)["state"], "refresh_failed"
        )
        _, recovered = self.run_tool(
            "recover", "--transaction", transaction_id, thread="fixture-thread-new"
        )
        self.assertEqual(recovered["state"], "failed_safe")

    def test_git_marketplace_refresh_uncertain_output_requires_restart(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_REFRESH_MODE"] = "output-too-large"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("without a reliable result", result.stderr)
        self.assertEqual(
            self.transaction_payload(transaction_id)["state"], "refresh_failed"
        )

    def test_git_marketplace_invalid_json_recovers_failed_safe(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_REFRESH_MODE"] = "invalid-json"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("could not be verified", result.stderr)
        self.assertEqual(
            self.transaction_payload(transaction_id)["state"], "recovery_required"
        )
        _, recovered = self.run_tool(
            "recover", "--transaction", transaction_id, thread="fixture-thread-new"
        )
        self.assertEqual(recovered["state"], "failed_safe")

    def test_local_marketplace_skips_refresh(self) -> None:
        self.environment["FAKE_MARKETPLACE_TYPE"] = "local"
        transaction_id = self.prepare()
        _, installed = self.run_tool("install", "--transaction", transaction_id)
        self.assertEqual(installed["state"], "restart_required")
        transaction = self.transaction_payload(transaction_id)
        self.assertEqual(
            transaction["marketplace_after_refresh"]["source_type"], "local"
        )
        self.assertFalse(json.loads(self.state_path.read_text())["refreshed"])

    def test_successful_add_with_wrong_installed_version_requires_recovery(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_INSTALL_MODE"] = "wrong-version"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("post-install verification failed", result.stderr)
        transaction = self.transaction_payload(transaction_id)
        self.assertEqual(transaction["state"], "recovery_required")
        self.assertEqual(
            transaction["failure"]["kind"], "post_install_verification_failed"
        )

    def test_install_rejects_marketplace_source_drift_before_refresh(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_MARKETPLACE_TYPE"] = "local"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("marketplace snapshot changed", result.stderr)
        self.assertEqual(self.transaction_payload(transaction_id)["state"], "prepared")

    def test_mcp_process_snapshot_accepts_unique_stable_cwd_without_copying_env(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        proc_root = self.temp_root / "proc-stable"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=str(cache))
        inventory = [
            {
                "name": "fixture-mcp",
                "enabled": True,
                "transport": {
                    "type": "stdio",
                    "command": "node",
                    "cwd": str(cache),
                    "env": {"IGNORED_SECRET": "must-not-be-copied"},
                },
            }
        ]
        snapshot = TRANSACTION_MODULE.mcp_runtime_snapshot(
            self.codex_home,
            "fixture-plugin",
            "fixture-marketplace",
            OLD_VERSION,
            proc_root=proc_root,
            codex_pid=100,
            inventory=inventory,
        )
        self.assertEqual(snapshot["status"], "verified")
        self.assertEqual(snapshot["servers"][0]["actual_cwd"], str(cache))
        self.assertNotIn("IGNORED_SECRET", json.dumps(snapshot))
        self.assertNotIn("must-not-be-copied", json.dumps(snapshot))

    def test_mcp_process_snapshot_rejects_deleted_cwd(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        proc_root = self.temp_root / "proc-deleted"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=f"{cache} (deleted)")
        inventory = [{
            "name": "fixture-mcp",
            "enabled": True,
            "transport": {"type": "stdio", "command": "node", "cwd": str(cache)},
        }]
        with self.assertRaisesRegex(
            TRANSACTION_MODULE.TransactionError, "MCP cwd is deleted"
        ):
            TRANSACTION_MODULE.mcp_runtime_snapshot(
                self.codex_home,
                "fixture-plugin",
                "fixture-marketplace",
                OLD_VERSION,
                proc_root=proc_root,
                codex_pid=100,
                inventory=inventory,
            )

    def test_mcp_process_snapshot_allows_deleted_cwd_for_rebaseline(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        proc_root = self.temp_root / "proc-deleted-rebaseline"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=f"{cache} (deleted)")
        inventory = [{
            "name": "fixture-mcp",
            "enabled": True,
            "transport": {"type": "stdio", "command": "node", "cwd": str(cache)},
        }]
        snapshot = TRANSACTION_MODULE.mcp_runtime_snapshot(
            self.codex_home,
            "fixture-plugin",
            "fixture-marketplace",
            OLD_VERSION,
            proc_root=proc_root,
            codex_pid=100,
            inventory=inventory,
            allow_deleted_cwd=True,
        )
        self.assertEqual(snapshot, {
            "status": "degraded",
            "count": 1,
            "servers": [],
            "degraded_reason": "deleted_cwd",
        })

    def test_mcp_process_snapshot_accepts_matching_deleted_backup_for_recovery(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        backup = (
            cache.parent.parent
            / "plugin-backup-abc123"
            / cache.parent.name
            / cache.name
        )
        proc_root = self.temp_root / "proc-current-release-backup"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=f"{backup} (deleted)")
        inventory = [{
            "name": "fixture-mcp",
            "enabled": True,
            "transport": {"type": "stdio", "command": "node", "cwd": str(cache)},
        }]
        snapshot = TRANSACTION_MODULE.mcp_runtime_snapshot(
            self.codex_home,
            "fixture-plugin",
            "fixture-marketplace",
            OLD_VERSION,
            proc_root=proc_root,
            codex_pid=100,
            inventory=inventory,
            allow_matching_deleted_backup=True,
        )
        self.assertEqual(snapshot, {
            "status": "verified",
            "count": 1,
            "servers": [{
                "name": "fixture-mcp",
                "command_basename": "node",
                "declared_cwd": str(cache),
                "runtime_cwd_kind": "current_release_deleted_backup",
            }],
        })

    def test_mcp_process_snapshot_rejects_deleted_backup_for_wrong_release(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        backup = (
            cache.parent.parent
            / "plugin-backup-abc123"
            / cache.parent.name
            / TARGET_VERSION
        )
        proc_root = self.temp_root / "proc-wrong-release-backup"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=f"{backup} (deleted)")
        inventory = [{
            "name": "fixture-mcp",
            "enabled": True,
            "transport": {"type": "stdio", "command": "node", "cwd": str(cache)},
        }]
        with self.assertRaisesRegex(
            TRANSACTION_MODULE.TransactionError, "MCP cwd is deleted"
        ):
            TRANSACTION_MODULE.mcp_runtime_snapshot(
                self.codex_home,
                "fixture-plugin",
                "fixture-marketplace",
                OLD_VERSION,
                proc_root=proc_root,
                codex_pid=100,
                inventory=inventory,
                allow_matching_deleted_backup=True,
            )

    def test_mcp_process_snapshot_rejects_deleted_backup_for_wrong_parent(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        backup = (
            cache.parent.parent.parent
            / "other-marketplace"
            / "plugin-backup-abc123"
            / cache.parent.name
            / cache.name
        )
        proc_root = self.temp_root / "proc-wrong-parent-backup"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=f"{backup} (deleted)")
        inventory = [{
            "name": "fixture-mcp",
            "enabled": True,
            "transport": {"type": "stdio", "command": "node", "cwd": str(cache)},
        }]
        with self.assertRaisesRegex(
            TRANSACTION_MODULE.TransactionError, "MCP cwd is deleted"
        ):
            TRANSACTION_MODULE.mcp_runtime_snapshot(
                self.codex_home,
                "fixture-plugin",
                "fixture-marketplace",
                OLD_VERSION,
                proc_root=proc_root,
                codex_pid=100,
                inventory=inventory,
                allow_matching_deleted_backup=True,
            )

    def test_mcp_process_snapshot_rejects_regular_deleted_cwd_with_backup_allowance(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        proc_root = self.temp_root / "proc-regular-deleted"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=f"{cache} (deleted)")
        inventory = [{
            "name": "fixture-mcp",
            "enabled": True,
            "transport": {"type": "stdio", "command": "node", "cwd": str(cache)},
        }]
        with self.assertRaisesRegex(
            TRANSACTION_MODULE.TransactionError, "MCP cwd is deleted"
        ):
            TRANSACTION_MODULE.mcp_runtime_snapshot(
                self.codex_home,
                "fixture-plugin",
                "fixture-marketplace",
                OLD_VERSION,
                proc_root=proc_root,
                codex_pid=100,
                inventory=inventory,
                allow_matching_deleted_backup=True,
            )

    def test_mcp_process_snapshot_rejects_wrong_version_cwd(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        wrong_cache = cache.parent / TARGET_VERSION
        wrong_cache.mkdir()
        proc_root = self.temp_root / "proc-wrong-version"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=str(wrong_cache))
        inventory = [{
            "name": "fixture-mcp",
            "enabled": True,
            "transport": {"type": "stdio", "command": "node", "cwd": str(cache)},
        }]
        with self.assertRaisesRegex(
            TRANSACTION_MODULE.TransactionError, "does not match installed version"
        ):
            TRANSACTION_MODULE.mcp_runtime_snapshot(
                self.codex_home,
                "fixture-plugin",
                "fixture-marketplace",
                OLD_VERSION,
                proc_root=proc_root,
                codex_pid=100,
                inventory=inventory,
            )

    def test_mcp_process_snapshot_rejects_ambiguous_processes(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        proc_root = self.temp_root / "proc-ambiguous"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=str(cache))
        self._write_proc_process(proc_root, 102, 100, cwd=str(cache))
        inventory = [{
            "name": "fixture-mcp",
            "enabled": True,
            "transport": {"type": "stdio", "command": "node", "cwd": str(cache)},
        }]
        with self.assertRaisesRegex(
            TRANSACTION_MODULE.TransactionError, "not uniquely identifiable"
        ):
            TRANSACTION_MODULE.mcp_runtime_snapshot(
                self.codex_home,
                "fixture-plugin",
                "fixture-marketplace",
                OLD_VERSION,
                proc_root=proc_root,
                codex_pid=100,
                inventory=inventory,
            )

    def test_mcp_process_snapshot_rejects_process_reuse_across_servers(self) -> None:
        cache = self._write_mcp_manifest(OLD_VERSION)
        proc_root = self.temp_root / "proc-reused"
        proc_root.mkdir()
        self._write_proc_process(proc_root, 101, 100, cwd=str(cache))
        contract = {
            "command_basename": "node",
            "declared_cwd": str(cache),
            "plugin_family_root": str(cache.parent),
        }
        with self.assertRaisesRegex(
            TRANSACTION_MODULE.TransactionError, "shared across declarations"
        ):
            TRANSACTION_MODULE.verify_mcp_processes(
                [
                    {"name": "fixture-mcp-a", **contract},
                    {"name": "fixture-mcp-b", **contract},
                ],
                proc_root,
                100,
            )

    def test_transaction_recover_accepts_restarted_target_mcp(self) -> None:
        self.environment["FAKE_MCP_ENABLED"] = "1"
        old_cache = self._write_mcp_manifest(OLD_VERSION, command="/usr/bin/sleep")
        old_process = self._start_mcp_process(old_cache)
        new_process: subprocess.Popen[bytes] | None = None
        try:
            transaction_id = self.prepare()
            self.run_tool("install", "--transaction", transaction_id)
            self._stop_process(old_process)
            target_cache = (
                self.codex_home
                / "plugins/cache/fixture-marketplace/fixture-plugin"
                / TARGET_VERSION
            )
            new_process = self._start_mcp_process(target_cache)
            _, recovered = self.run_tool(
                "recover", "--transaction", transaction_id, thread="fixture-thread-new"
            )
            self.assertEqual(recovered["state"], "completed")
            transaction = self.transaction_payload(transaction_id)
            self.assertEqual(transaction["recovered"]["mcp"]["status"], "verified")
        finally:
            self._stop_process(old_process)
            if new_process is not None:
                self._stop_process(new_process)

    def test_transaction_recover_accepts_matching_deleted_target_backup(self) -> None:
        self.environment["FAKE_MCP_ENABLED"] = "1"
        old_cache = self._write_mcp_manifest(OLD_VERSION, command="/usr/bin/sleep")
        old_process = self._start_mcp_process(old_cache)
        new_process: subprocess.Popen[bytes] | None = None
        try:
            transaction_id = self.prepare()
            self.run_tool("install", "--transaction", transaction_id)
            self._stop_process(old_process)
            target_cache = (
                self.codex_home
                / "plugins/cache/fixture-marketplace/fixture-plugin"
                / TARGET_VERSION
            )
            backup_root = target_cache.parent.parent / "plugin-backup-abc123"
            backup = backup_root / target_cache.parent.name / target_cache.name
            backup.mkdir(parents=True)
            new_process = self._start_mcp_process(backup)
            shutil.rmtree(backup_root)
            _, recovered = self.run_tool(
                "recover", "--transaction", transaction_id, thread="fixture-thread-new"
            )
            self.assertEqual(recovered["state"], "completed")
            transaction = self.transaction_payload(transaction_id)
            self.assertEqual(transaction["recovered"]["mcp"], {
                "status": "verified",
                "count": 1,
                "servers": [{
                    "name": "fixture-mcp",
                    "command_basename": "sleep",
                    "declared_cwd": str(target_cache),
                    "runtime_cwd_kind": "current_release_deleted_backup",
                }],
            })
        finally:
            self._stop_process(old_process)
            if new_process is not None:
                self._stop_process(new_process)

    def test_transaction_recover_rejects_deleted_old_mcp_cwd(self) -> None:
        self.environment["FAKE_MCP_ENABLED"] = "1"
        old_cache = self._write_mcp_manifest(OLD_VERSION, command="/usr/bin/sleep")
        old_process = self._start_mcp_process(old_cache)
        try:
            transaction_id = self.prepare()
            self.run_tool("install", "--transaction", transaction_id)
            result, _ = self.run_tool(
                "recover",
                "--transaction",
                transaction_id,
                thread="fixture-thread-new",
                expect_success=False,
            )
            self.assertIn("MCP cwd is deleted", result.stderr)
            self.assertEqual(
                self.transaction_payload(transaction_id)["state"], "recovery_required"
            )
        finally:
            self._stop_process(old_process)

    def test_same_thread_can_prove_restart_with_new_codex_process(self) -> None:
        payload = {
            "origin_session_digest": "sha256:" + "a" * 64,
            "origin_process": {
                "boot_id_digest": "sha256:" + "b" * 64,
                "pid": 100,
                "start_ticks": 1000,
                "started_at_epoch": 100.0,
            },
            "install_finished_at": "1970-01-01T00:03:20Z",
        }
        current = {
            "boot_id_digest": "sha256:" + "b" * 64,
            "pid": 101,
            "start_ticks": 2000,
            "started_at_epoch": 201.0,
        }
        self.assertTrue(
            TRANSACTION_MODULE.restart_proven(payload, payload["origin_session_digest"], current)
        )

    def test_prepare_records_codex_process_identity_when_available(self) -> None:
        transaction_id = self.prepare(preserve_process_identity=True)
        transaction = self.transaction_payload(transaction_id)
        current = TRANSACTION_MODULE.codex_process_identity()
        if current is None:
            self.assertNotIn("origin_process", transaction)
        else:
            self.assertEqual(transaction["origin_process"], current)

    def test_same_or_preinstall_codex_process_does_not_prove_restart(self) -> None:
        payload = {
            "origin_session_digest": "sha256:" + "a" * 64,
            "origin_process": {
                "boot_id_digest": "sha256:" + "b" * 64,
                "pid": 100,
                "start_ticks": 1000,
                "started_at_epoch": 100.0,
            },
            "install_finished_at": "1970-01-01T00:03:20Z",
        }
        self.assertFalse(
            TRANSACTION_MODULE.restart_proven(
                payload, payload["origin_session_digest"], payload["origin_process"]
            )
        )
        stale = dict(payload["origin_process"], pid=101, start_ticks=2000, started_at_epoch=199.0)
        self.assertFalse(
            TRANSACTION_MODULE.restart_proven(payload, payload["origin_session_digest"], stale)
        )

    def test_recover_allows_committed_transaction_tool_self_repair(self) -> None:
        transaction_id = self.prepare()
        self.run_tool("install", "--transaction", transaction_id)
        write(
            self.codex_home / "skills/codex-plugin-update/scripts/plugin-update-transaction.py",
            "# transaction recovery repair\n",
        )
        git(
            self.codex_home,
            "add",
            "skills/codex-plugin-update/scripts/plugin-update-transaction.py",
        )
        git(self.codex_home, "commit", "-qm", "repair transaction tool")
        _, recovered = self.run_tool(
            "recover", "--transaction", transaction_id, thread="fixture-thread-new"
        )
        self.assertEqual(recovered["state"], "completed")

    def test_recover_rejects_unrelated_committed_codex_change(self) -> None:
        transaction_id = self.prepare()
        self.run_tool("install", "--transaction", transaction_id)
        write(self.codex_home / "unrelated.txt", "unexpected\n")
        git(self.codex_home, "add", "unrelated.txt")
        git(self.codex_home, "commit", "-qm", "unrelated change")
        result, _ = self.run_tool(
            "recover",
            "--transaction",
            transaction_id,
            thread="fixture-thread-new",
            expect_success=False,
        )
        self.assertIn("CODEX_HOME Git snapshot changed", result.stderr)

    def test_finalize_recovery_closes_target_install_after_historical_drift(self) -> None:
        transaction_id = self.prepare()
        self.run_tool("install", "--transaction", transaction_id)
        write(self.project_root / "README.md", "changed after restart\n")
        git(self.project_root, "add", "README.md")
        git(self.project_root, "commit", "-qm", "continue project work")
        self.run_tool(
            "recover",
            "--transaction",
            transaction_id,
            thread="fixture-thread-new",
            expect_success=False,
        )
        _, finalized = self.run_tool(
            "finalize-recovery",
            "--transaction",
            transaction_id,
            "--project-root",
            str(self.project_root),
            "--confirm-historical-drift",
            thread="fixture-thread-new",
        )
        self.assertEqual(finalized["state"], "failed_safe")
        self.assertTrue(finalized["target_installed"])
        transaction = self.transaction_payload(transaction_id)
        self.assertEqual(transaction["state"], "failed_safe")
        self.assertIn("project Git snapshot changed", transaction["finalization"]["historical_drift"])

        # The closed historical transaction no longer blocks an unrelated update.
        _, prepared = self.run_tool(
            "prepare",
            "--plugin",
            PLUGIN,
            "--target-version",
            "3.0.0",
            "--project-root",
            str(self.project_root),
            thread="fixture-thread-new",
        )
        self.assertEqual(prepared["state"], "prepared")
        self.run_tool("abort", "--transaction", prepared["transaction_id"], thread="fixture-thread-new")

    def test_finalize_recovery_requires_explicit_confirmation(self) -> None:
        transaction_id = self.prepare()
        self.run_tool("install", "--transaction", transaction_id)
        write(self.project_root / "README.md", "changed\n")
        git(self.project_root, "add", "README.md")
        git(self.project_root, "commit", "-qm", "continue project work")
        self.run_tool(
            "recover",
            "--transaction",
            transaction_id,
            thread="fixture-thread-new",
            expect_success=False,
        )
        result, _ = self.run_tool(
            "finalize-recovery",
            "--transaction",
            transaction_id,
            "--project-root",
            str(self.project_root),
            thread="fixture-thread-new",
            expect_success=False,
        )
        self.assertIn("required", result.stderr)
        self.assertEqual(self.transaction_payload(transaction_id)["state"], "recovery_required")

    def test_prepare_rejects_duplicate_active_transaction(self) -> None:
        first = self.prepare()
        result, _ = self.run_tool(
            "prepare",
            "--plugin",
            PLUGIN,
            "--target-version",
            TARGET_VERSION,
            "--project-root",
            str(self.project_root),
            expect_success=False,
        )
        self.assertIn(first, result.stderr)

    def test_prepare_records_untrusted_old_hook_for_preloaded_target_trust(self) -> None:
        self.environment["FAKE_UNTRUSTED_VERSION"] = OLD_VERSION
        transaction_id = self.prepare()
        payload = self.transaction_payload(transaction_id)
        runtime_hooks = payload["snapshot"]["runtime_hook"]["hooks"]
        self.assertEqual({item["trust_status"] for item in runtime_hooks}, {"untrusted"})
        _, installed = self.run_tool("install", "--transaction", transaction_id)
        self.assertEqual(installed["state"], "restart_required")

    def test_install_rejects_runtime_hook_drift(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_HOOK_RUNTIME_MODE"] = "untrusted"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("runtime Hook state changed", result.stderr)

    def test_install_rejects_project_git_drift(self) -> None:
        transaction_id = self.prepare()
        write(self.project_root / "README.md", "changed\n")
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("project Git snapshot changed", result.stderr)
        self.assertEqual(self.transaction_payload(transaction_id)["state"], "prepared")

    def test_prepare_allows_a_dirty_project_but_records_the_exact_snapshot(self) -> None:
        write(self.project_root / "README.md", "uncommitted task work\n")

        transaction_id = self.prepare()

        snapshot = self.transaction_payload(transaction_id)["snapshot"]
        assert isinstance(snapshot, dict)
        project_git = snapshot["project_git"]
        assert isinstance(project_git, dict)
        self.assertFalse(project_git["clean"])
        self.assertNotEqual(project_git["status_digest"], "")

    def test_install_rejects_codex_git_drift(self) -> None:
        transaction_id = self.prepare()
        write(self.codex_home / "hooks.json", '{"hooks": {"changed": []}}\n')
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("CODEX_HOME Git snapshot changed", result.stderr)

    def test_install_rejects_task_drift(self) -> None:
        transaction_id = self.prepare()
        self._write_task("planning", task_id="other-task")
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("current Trellis task changed", result.stderr)

    def test_expired_transaction_cannot_install(self) -> None:
        transaction_id = self.prepare()
        payload = self.transaction_payload(transaction_id)
        payload["expires_at"] = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        ).isoformat()
        self.rewrite_transaction(transaction_id, payload)
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("expired", result.stderr)
        self.assertEqual(self.transaction_payload(transaction_id)["state"], "expired")

    def test_recover_records_version_mismatch(self) -> None:
        transaction_id = self.prepare()
        self.run_tool("install", "--transaction", transaction_id)
        self._write_plugin_state("3.0.0")
        self._write_hook("3.0.0")
        result, _ = self.run_tool(
            "recover",
            "--transaction",
            transaction_id,
            thread="fixture-thread-new",
            expect_success=False,
        )
        self.assertIn("does not match target", result.stderr)
        self.assertEqual(
            self.transaction_payload(transaction_id)["state"], "recovery_required"
        )

    def test_failed_install_requires_restart_and_recovers_safe_old_version(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_INSTALL_MODE"] = "fail-before-change"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("restart Codex now", result.stderr)
        self.assertEqual(self.transaction_payload(transaction_id)["state"], "install_failed")

        _, recovered = self.run_tool(
            "recover", "--transaction", transaction_id, thread="fixture-thread-new"
        )
        self.assertEqual(recovered["state"], "failed_safe")
        self.assertFalse(recovered["target_installed"])
        self.assertEqual(recovered["installed_version"], OLD_VERSION)

    def test_install_output_overflow_requires_restart_and_recovery(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_INSTALL_MODE"] = "output-too-large"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("without a reliable result", result.stderr)
        self.assertEqual(self.transaction_payload(transaction_id)["state"], "install_failed")

    def test_post_install_hook_failure_requires_restart_and_recovery(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_INSTALL_MODE"] = "success-missing-hook"
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("post-install verification failed", result.stderr)
        self.assertIn("restart Codex now", result.stderr)
        self.assertEqual(
            self.transaction_payload(transaction_id)["state"], "recovery_required"
        )

    def test_corrupt_transaction_fails_without_traceback(self) -> None:
        transaction_id = self.prepare()
        payload = self.transaction_payload(transaction_id)
        del payload["snapshot"]["task"]
        self.rewrite_transaction(transaction_id, payload)
        result, _ = self.run_tool(
            "status", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("snapshot task is missing", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_failed_safe_does_not_hide_project_drift(self) -> None:
        transaction_id = self.prepare()
        self.environment["FAKE_INSTALL_MODE"] = "fail-before-change"
        self.run_tool("install", "--transaction", transaction_id, expect_success=False)
        write(self.project_root / "README.md", "changed after install failure\n")
        result, _ = self.run_tool(
            "recover",
            "--transaction",
            transaction_id,
            thread="fixture-thread-new",
            expect_success=False,
        )
        self.assertIn("project Git snapshot changed", result.stderr)
        self.assertEqual(
            self.transaction_payload(transaction_id)["state"], "recovery_required"
        )

    def test_abort_only_changes_prepared_transaction(self) -> None:
        transaction_id = self.prepare()
        _, payload = self.run_tool("abort", "--transaction", transaction_id)
        self.assertEqual(payload["state"], "aborted")
        result, _ = self.run_tool(
            "install", "--transaction", transaction_id, expect_success=False
        )
        self.assertIn("not prepared", result.stderr)


if __name__ == "__main__":
    unittest.main()
