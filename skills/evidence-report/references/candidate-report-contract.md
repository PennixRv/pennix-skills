# Candidate Report Contract

A worker returns exactly one final channel message in this form:

```text
<CANDIDATE_REPORT>
{ ...one JSON object... }
</CANDIDATE_REPORT>
```

The coordinator extracts only one wrapper after the request's send event. It validates that object as schema version `3` before using
any claim.

## Required Fields

```json
{
  "schema_version": 3,
  "result_id": "stable-result-id",
  "task_id": "assigned-task",
  "batch_id": "assigned-batch",
  "role_id": "assigned-role",
  "instance_id": "assigned-instance",
  "status": "complete",
  "scope": ["assigned scope item"],
  "lens": "assigned independent lens",
  "evidence_method": "assigned evidence method",
  "evidence": [
    {
      "id": "e1",
      "kind": "file",
      "locator": "precise location",
      "claim": "what it establishes",
      "verified": true
    }
  ],
  "findings": [
    {
      "severity": "major",
      "claim": "candidate conclusion",
      "impact": "why it matters",
      "reproduce": "local verification route",
      "evidence_ids": ["e1"]
    }
  ]
}
```

`complete` needs at least one evidence entry. A report may contain no findings when the assigned investigation found none. Optional
narrative fields are only for actual observations, uncertainties, recommendations, tool summaries, errors, or a counter-review link.

## Counter Reports

An independently assigned counter report also includes all of the following fields:

```json
{
  "review_round": 1,
  "review_of": ["primary-result-id"],
  "review_relation": "independent",
  "review_verdict": "supports",
  "evidence_refs": ["e1"],
  "coverage": "complete"
}
```

The counter's required `lens` is its own assigned lens. `review-gate` compares it directly with the primary report lens; it does not
infer independence from labels, worker names, or a repeated evidence identifier.
