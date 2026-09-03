---
name: evidence-report
description: Define, extract, and validate a Trellis worker's structured candidate evidence report before the main session reviews it.
---

# Evidence Report

Candidate workers return one `<CANDIDATE_REPORT>` JSON wrapper in their final channel message. They preserve the exact assigned
`task_id`, `batch_id`, `role_id`, `instance_id`, `scope`, `lens`, and `evidence_method`; they do not write project files or accept
facts. The coordinator captures that one wrapper after the send event's `seq`:

```bash
trellis channel messages <channel> --raw > <events.jsonl>
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/evidence-report/scripts/extract_channel_report.py" \
  --events <events.jsonl> --worker <worker> --after-seq <send-seq> --output <report.json>
```

Then use the executable validator:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/evidence-report/scripts/validate_report.py" <report.json> \
  --task <task-id> --batch <batch-id> --instance <instance-id> --role <role-id> \
  --lens <assigned-lens> --evidence-method <assigned-evidence-method>
```

Pass every assigned scope item with repeated `--scope` flags. The v3 validator requires the report to preserve all assigned identity,
scope, lens, and evidence-method fields exactly; it checks the bounded JSON shape, evidence references, finding references, UTF-8,
file size, and obvious credential markers, and prints only a bounded summary. A non-zero result keeps the report a candidate failure;
it does not authorize a retry or acceptance.

The report's identity, assigned scope, evidence, and findings are required. Narrative fields such as `observations`,
`uncertainties`, `recommendations`, and `tool_summary` are optional; omit them when they add no information instead of filling a
template with boilerplate. The main session must locally verify evidence locations and conclusions before writing task, Issue, or
Git facts. For the complete report shape, read [the candidate report contract](references/candidate-report-contract.md). This Skill
does not read runtime ledgers, control Trellis workers, or decide whether a finding is true.
