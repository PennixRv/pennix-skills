import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

SCRIPT = Path(__file__).parents[1] / 'scripts' / 'codex.py'
spec = importlib.util.spec_from_file_location('pennix_cognee_launcher', SCRIPT)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)
from cognee_client import canonical_project_root


class CodexLauncherTest(unittest.TestCase):
    def test_registered_project_gets_native_override_without_inherited_secrets(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            config = home / '.cognee' / '.env'
            config.parent.mkdir()
            config.write_text('COGNEE_MANAGED_ENDPOINT=true\nCOGNEE_SHARED_AGENT_MEMORY=false\n')
            config.chmod(0o600)
            with (
                mock.patch.object(launcher.Path, 'home', return_value=home),
                mock.patch.object(launcher.CogneeClient, 'for_project', return_value=SimpleNamespace(project='project-memory')),
                mock.patch.object(launcher.shutil, 'which', return_value='/usr/bin/codex'),
                mock.patch.object(launcher.os, 'execvpe') as execute,
                mock.patch.dict(os.environ, {'COGNEE_API_KEY': 'inherited', 'COGNEE_PLUGIN_DATASET': 'wrong'}),
            ):
                launcher.main(['--version'])
            _, args, env = execute.call_args.args
            self.assertEqual(args[1:4], ['--no-daemon', '-c', 'plugins."cognee@cognee".enabled=true'])
            self.assertEqual(env['COGNEE_PLUGIN_DATASET'], 'project-memory')
            self.assertEqual(env['COGNEE_PLUGIN_IDENTITY'], 'false')
            self.assertNotIn('COGNEE_API_KEY', env)

    def test_unbound_resume_disables_memory_and_cd_selects_actual_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            with (
                mock.patch.object(launcher.shutil, 'which', return_value='/usr/bin/codex'),
                mock.patch.object(launcher.os, 'execvpe') as execute,
                mock.patch.object(launcher, '_registered_dataset') as registered,
            ):
                launcher.main(['resume'])
                registered.assert_not_called()
                self.assertIn('plugins."cognee@cognee".enabled=false', execute.call_args.args[1])
            self.assertEqual(launcher._launch_root(['--cd', temporary]), Path(temporary))

    def test_worktree_and_subdirectory_share_identity_but_nested_repo_does_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'main'
            root.mkdir()
            def git(*args):
                subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True)
            git('init')
            git('-c', 'user.email=test@example.test', '-c', 'user.name=Test', 'commit', '--allow-empty', '-m', 'fixture')
            worktree = root.parent / 'worktree'
            git('worktree', 'add', '-b', 'fixture', str(worktree))
            self.assertEqual(canonical_project_root(worktree), root)
            sub = worktree / 'sub'
            sub.mkdir()
            self.assertEqual(canonical_project_root(sub), root)
            subprocess.run(['git', '-C', str(sub), 'init'], check=True, capture_output=True)
            self.assertEqual(canonical_project_root(sub), sub)


if __name__ == '__main__':
    unittest.main()
