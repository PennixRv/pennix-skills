# Design

## Ownership

`pennix-workflow-lifecycle` owns only its profile and static receipt records. The live Skills collection owns its sibling collection receipt. Credentials remain in their existing owner-specific paths and are never copied into lifecycle state.

## State layout

```text
${XDG_STATE_HOME:-~/.local/state}/pennix-workflow-lifecycle/
  homes/<sha256(normalized-resolved-CODEX_HOME)>/
    profile.json
    static-assets/tmux-config.json
```

All lifecycle directories are `0700`, managed files are `0600`, and symlink ancestors, foreign owners, unsafe modes, unknown entries, invalid JSON, and conflicting destinations block state operations.

## Reconcile

The explicit state component reads only the legacy allow-list:

```text
CODEX_HOME/pennix-workflow-lifecycle/profile.json
CODEX_HOME/pennix-workflow-lifecycle/static-assets/tmux-config.json
```

It validates all source and destination records before writing. Each copied file uses a same-directory temporary file, `fsync`, `chmod 0600`, and `replace`; the old record is removed only after all writes and reads verify. Unknown files and any error preserve the legacy tree. There is no recursive cleanup operation.

## Staging

Discovery scans only direct children of the Skills destination whose names start with `.pennix-skills-stage`. It reports names and `unknown` status, never contents or absolute paths. No age, PID, process, content, or provenance inference is made.
