---
name: evidence-report
description: Validate a Trellis worker's candidate evidence report before the main session reviews it; use for structured report files, not ordinary notes.
---

# Evidence Report

Use the executable validator on a report assigned by the Trellis runtime:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/evidence-report/scripts/validate_report.py" <report.json> \
  --task <task-id> --batch <batch-id> --instance <instance-id>
```

Pass every assigned scope item with repeated `--scope` flags. The validator requires the report to preserve that list exactly,
checks the bounded JSON shape, evidence references, finding references, UTF-8, file size, and obvious credential markers, and
prints only a bounded summary. A non-zero result keeps the report a candidate failure; it does not authorize a retry or acceptance.

The report's identity, assigned scope, evidence, and findings are required. Narrative fields such as `observations`,
`uncertainties`, `recommendations`, and `tool_summary` are optional; omit them when they add no information instead of filling a
template with boilerplate. The main session must locally verify evidence locations and conclusions before writing task, Issue, or
Git facts. This Skill does not read runtime ledgers, control Trellis workers, or decide whether a finding is true.
