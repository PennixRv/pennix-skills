# Design

`pennix-trellis-setup` is a user-preference router, not an initializer. It
selects one published Trellis workflow profile and invokes the native CLI.

For a new project, a request that does not name a different workflow means:

```text
trellis init --codex --yes --workflow codex-subnode-channel \
  --workflow-source gh:PennixRv/marketplace#v0.6.22
```

For an existing project, the same default becomes a `.new` workflow candidate
after listing the pinned source. This preserves the native ownership rule for
non-native workflow files. Refresh-only requests remain `trellis update`
operations and do not switch workflow.

The Skill reports Hook prerequisites but never edits `config.toml`, Hook trust,
or the user's global `AGENTS.md`.
