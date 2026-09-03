---
name: workflow-doctor
description: Diagnose the local Trellis fork, project Skills, top-level workflow files, and migration residue without changing state.
---

# Workflow Doctor

Run the read-only diagnostic from the project root:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/workflow-doctor/scripts/doctor.py" --project-root .
```

The output is a bounded JSON summary of required project files, the local Trellis checkout, package identity, and any
legacy profile path that still exists. `degraded` is diagnostic information, not permission to silently repair or install
anything. Inspect the reported files in the owning repository and choose the next task explicitly.

This Skill does not probe providers, alter Codex configuration, stop workers, install packages, delete Plugin caches, or write task
facts. It must not be used as a replacement for Trellis's own channel lifecycle commands.
