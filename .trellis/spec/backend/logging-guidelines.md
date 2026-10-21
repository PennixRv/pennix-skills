# Logging Guidelines

> How logging is done in this project.

---

## Overview

<!--
Document your project's logging conventions here.

Questions to answer:
- What logging library do you use?
- What are the log levels and when to use each?
- What should be logged?
- What should NOT be logged (PII, secrets)?
-->

(To be filled by the team)

---

## Log Levels

<!-- When to use each level: debug, info, warn, error -->

(To be filled by the team)

---

## Structured Logging

<!-- Log format, required fields -->

(To be filled by the team)

---

## What to Log

<!-- Important events to log -->

(To be filled by the team)

---

## What NOT to Log

<!-- Sensitive data, PII, secrets -->

(To be filled by the team)

## Native Evaluation Evidence

### Scope / Trigger

Changes to `evaluations/run_codex_cases.py` must preserve the distinction between a path mention, a file read attempt, and its observable result.

### Signatures

`summarize(path, native_status)` reads native JSONL and returns a review-only summary. `skill_observations(item, event_number)` projects attributable file access without executing or rewriting commands.

### Contracts

`skill_path_observations` is ordered and contains `event`, `path`, `skill`, `tool`, and `outcome` (`read`, `failed`, `unknown`). Preserve project, collection and relative path levels. `skill_read_counts` counts these outcomes separately per observed path; `skill_read_candidates` remains a compatibility list of names, not proof of reading. Neither a `read` receipt nor a count proves complete output or agent consumption. Do not persist raw commands, messages, output bodies, credentials or session files in summaries or Git.

### Validation & Error Matrix

| Evidence | Outcome |
| --- | --- |
| Single-file `cat`, integer exit 0, nonempty string output | `read`; does not prove complete output or agent consumption |
| Single-file `cat`, nonzero integer exit | `failed` |
| Compound command, mention, MCP argument, missing or malformed output | `unknown` |
| Native process failure or malformed JSONL | Preserve the existing blocked verdict; never claim a pass |

### Good / Base / Bad Cases

Good: a failed flattened path followed by a successful nested path produces two ordered observations. Base: a single project Skill read retains its full path. Bad: a completed model turn with no observable read cannot satisfy behavior acceptance. Native `--ephemeral` runs do not create rollout files; a hook requiring that provenance may deny all reads even when the process exits successfully.

### Required Tests

Run `python3 -B -m unittest discover -s evaluations -p test_run_codex_cases.py -v`. Assert failure preservation, full project/main/extra/expanded-alias/relative paths, and unknown results for unconfirmed access. Validate actual host behavior separately from synthetic events; do not freeze path guidance by matching Chinese sentences.

### Wrong vs Correct

Wrong: treat `skill_read_candidates` or native exit 0 as successful loading. Correct: review ordered path observations and host-specific evidence, keeping missing reads and first failures visible.
