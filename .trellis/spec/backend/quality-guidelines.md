# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

<!--
Document your project's quality standards here.

Questions to answer:
- What patterns are forbidden?
- What linting rules do you enforce?
- What are your testing requirements?
- What code review standards apply?
-->

(To be filled by the team)

---

## Forbidden Patterns

<!-- Patterns that should never be used and why -->

(To be filled by the team)

---

## Required Patterns

### Skill collection deployment boundary

- The repository checkout is the source of truth. The installed collection is
  a replaceable delivery copy and must not become an edit location.
- `pennix-skills-install` defaults to
  `${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills`, but callers may pass an
  explicit `--dest` ending in `skills/pennix-skills` for a host-selected
  discovery root. `PENNIX_SKILLS_ROOT` is a caller convention for reusing that
  selected collection root in direct Skill commands; the installer does not
  scan for roots or persist host-wide discovery state.
- Changes to this boundary require tests for the unchanged default, an
  explicit host-selected root, invalid destinations, and atomic replacement.

---

## Testing Requirements

<!-- What level of testing is expected -->

(To be filled by the team)

---

## Code Review Checklist

<!-- What reviewers should check -->

(To be filled by the team)
