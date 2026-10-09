---
name: workflow-doctor
description: Diagnose an initialized Trellis project's generated assets, Skills and migration residue without changing state; a local fork checkout is optional.
---

# Workflow Doctor

Run the read-only diagnostic from the project root:

```bash
python3 "${PENNIX_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills}/workflow-doctor/scripts/doctor.py" --project-root .
```

The output separates required generated project assets from optional local Trellis source-checkout and package information.
A normal consumer does not need a `Trellis/` checkout. `degraded` is diagnostic information, not permission to silently repair or install
anything. Inspect the reported files in the owning repository and choose the next task explicitly.

This Skill does not probe providers, alter Codex configuration, stop workers, install packages, delete Plugin caches, or write task
facts. It must not be used as a replacement for Trellis's own channel lifecycle commands.
