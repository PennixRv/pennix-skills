# Deployment Design v1

Update skills/pennix-workflow-lifecycle/references/component-versions.json only after Trellis paired core/CLI and CCH official Release are independently verified. Add the narrowly required deployment/verification explanation under existing lifecycle references: history is relation metadata since activation, not retained Channel logs or a task-scoped worker count.

Use existing lifecycle discover and Trellis upgrade/verify, project-update ownership, native CCH install/doctor and system skill-installer immutable git staging/replace-staged. Do not implement another CCH installer or state ledger.

Seven consumers: root and root/Trellis, root/pennix-skills, root/cch-codex-tmux-status, /home/penn/devel/Trellis, /home/penn/devel/fastctx, /home/penn/devel/windsurf-code-search. Keep chosen workflows, custom config/tasks/specs/secrets. The second Trellis checkout only fast-forwards released source.

User landing points: complete ~/.codex/skills/pennix-skills collection and relevant owner-managed AGENTS/config/Hook assets; no-change assets need verification, not forced rewrites. CCH packages at ~/.npm-global and /usr plus its managed runtime must match.

Baseline main d1d89172b001bed86805ffa5a5f54daa6093cf4e. No new runtime protocol; publish consumption is a verified source commit and immutable install, not an invented package release. Rollback through owner-native installs to the baseline pins/source while preserving user/runtime data.
