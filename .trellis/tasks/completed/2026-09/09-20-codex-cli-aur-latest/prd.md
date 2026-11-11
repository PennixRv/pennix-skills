# Codex CLI tracks AUR latest

## Goal

将 seed 和 lifecycle 的 `codex-cli` 安装策略统一为 AUR `openai-codex-bin` 当次可用候选版本。移除该组件的静态 `approved_version`；由 catalog 仅声明 `repository-latest` 版本策略。seed 必须使用 AUR helper，lifecycle 的 `discover`、`install`、`upgrade` 和 `verify` 必须以当次 AUR 候选与实际安装版本比较。

## Requirements

- `codex-cli` 是唯一采用动态策略的组件；其他组件继续由 catalog 中的固定 `approved_version` 约束。
- `repository-latest` 只能用于 AUR package，且不得同时包含 `approved_version`。
- seed 的目标包为 `openai-codex-bin`；已有 `yay` 优先、`paru` 次之。两者缺失时，seed 可通过 `pacman` 安装 AUR 构建前置，从 AUR 检出并构建 `yay`，再继续安装目标包。
- 仍拒绝覆盖现有 Codex config/auth，仍拒绝未授权的 `openai-codex` 包所有者迁移，且不输出 API key。
- 不改变 project initialization、其他 package manager 选择、或任意其他组件的版本策略。

## Acceptance Criteria

- [x] catalog 明确 `codex-cli` 为 `repository-latest`，无静态版本；非法的动态 catalog 组合被拒绝。
- [x] `probe_component`、`discover`、`verify` 和 package action 对动态组件使用当前 AUR candidate；candidate 无法获取时安全阻止写操作。
- [x] seed 查询并安装 `openai-codex-bin`，不再使用官方 `openai-codex`；缺失 helper 的 bootstrap 和既有 helper 路径均有测试。
- [x] 全部 lifecycle 定向单元测试、Shell 语法检查和干净 checkout collection source check 通过。
- [x] 修改已通过独立组件提交推送；根仓库只记录提交与验收结果。

## Evidence

- `bash -n skills/pennix-workflow-lifecycle/scripts/seed-arch.sh`
- `python3 -m unittest discover -s skills/pennix-workflow-lifecycle/tests -p 'test_*.py'` (`79` tests passed)
- CI-equivalent per-file Python test invocation passed for every `skills/**/tests/test_*.py` file.
- `python3 skills/pennix-workflow-lifecycle/scripts/adapters/skills_install.py --source "$PWD" --check` validated `10` Skills from a clean checkout.
- `git diff --check`
- `.github/workflows/verify.yml` 的 collection check 已从退役的 `pennix-workflow-bootstrap` 路径改为当前 lifecycle adapter；将在干净 checkout 上按 CI 命令验证。
- Component commit `7f7d4c1` (`feat: track Codex CLI from AUR latest`) fast-forwarded and pushed to `origin/main`.
- Anonymous raw `main` seed was fetched over HTTPS and confirmed to contain `openai-codex-bin`, `select_aur_helper`, and `bootstrap_yay`.
- Root `node scripts/run-workflow-integration.mjs --full-local` exited `0`, including the Pennix Skills collection check.

## Notes

- Keep `prd.md` focused on requirements, constraints, and acceptance criteria.
- Lightweight tasks can remain PRD-only.
- For complex tasks, add `design.md` for technical design and `implement.md` for execution planning before `task.py start`.
