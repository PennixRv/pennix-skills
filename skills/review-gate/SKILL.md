---
name: review-gate
description: Check whether a major or critical candidate has a genuinely independent Trellis counter-review before acceptance.
---

This Skill consumes the report contract shipped with the `evidence-report` Skill. Install both
Skills from the same `pennix-skills` revision before using this gate.

For a required second view, run:

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/pennix-skills/review-gate/scripts/check_gate.py" \
  --primary <primary-report.json> --counter <counter-report.json> --risk major
```

The reports must be complete, belong to the same task and batch, use the same exact scope, come from different instances, use
different review lenses, link the counter report to the primary result, and use different evidence IDs. The reports may cite
the same source file or URL when both reviewers independently inspect it; the evidence records and claims must remain separate. `passed`
means only that the relationship is structurally sufficient; the main session still verifies the evidence and chooses whether to
accept a candidate. `insufficient_independent_review` blocks promotion and must be recorded with a bounded next action.

Do not create a second batch state machine, reuse one report under two identities, or treat two workers with the same evidence as
independent review.
