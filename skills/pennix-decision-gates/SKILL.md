---
name: pennix-decision-gates
description: Decide when a complex task needs user input, batch independent planning questions, and return material implementation ambiguity to the Trellis planning gate.
metadata:
  short-description: Govern interactive planning decisions
---

# Pennix Decision Gates

Use this Skill for Trellis `clarify`, `research`, `plan`, `plan-check`, or an
explicit `grill-me` gate when more than one reasonable choice may change the
scope, owner, safety boundary, public behavior, data, deployment, cost, or
acceptance criteria. It does not perform deployment and does not create a
second task lifecycle.

## Decide Whether To Ask

Do not ask when an existing task, spec, sealed decision, or project convention
covers the choice, or when the choice is local, reversible, testable, and does
not change an external contract. Record the local choice in the current task
when it may help later work.

Ask when the unresolved choice has multiple reasonable options and changes a
material boundary. Present concrete mutually exclusive options, mark one
recommendation, and explain the consequence of each option.

## Batch Questions

Build the dependency order before asking:

- Put only independent decisions from the same planning gate in one request.
- Keep the batch within the current host's question limit, currently 1–3.
- Give every question a stable id, concise header, and distinct options.
- Split questions when one answer changes another question's options, scope,
  risk, owner, validation path, or next action.
- Keep execution authorization separate from design decisions.

Call the current session's native `request_user_input` directly when it is
available. Do not detect or replace it through `functions.exec`, nested
`tools.*`, `ALL_TOOLS`, shell, or MCP. Correct a schema error at most once;
host refusal, cancellation, timeout, or genuine unavailability may use a
plain-text fallback, but the unanswered decision still stops the turn. Never
silently choose the recommendation.

After asking, stop the turn. The next turn must read the answers before
writing, applying, committing, archiving, or advancing the dependent gate.

## During Implementation

Use sealed task/spec decisions for ordinary implementation choices. For a
local reversible choice, continue and record the decision. For a material
unresolved ambiguity, do not open a popup during implementation or apply:
record `decision-needed`, restore the smallest safe state if necessary, return
to the Trellis planning/design step, and continue only after the decision is
sealed. If evidence disproves the approach, use the same smallest-state
rollback and preserve the retracted conclusion in the task history.

Trellis supports this as a workflow return to an earlier planning step. If the
local CLI does not provide a controlled `replan` or `reopen` transition, do
not edit `task.json.status` by hand; keep the task facts honest and follow the
available planning/continue route.

## Decision Record

For each material decision, retain: question, options, selected option,
recommendation, rationale, impact, evidence, and the condition that would
justify revisiting it. Keep this record in the current Trellis task; do not
create a parallel ledger in Codex configuration or runtime state.
