---
name: pennix-decision-gates
description: Decide when a complex task needs user input, batch independent planning questions, and return material implementation ambiguity to the Trellis planning gate.
metadata:
  short-description: Govern interactive planning decisions
---

# Pennix Decision Gates

Use this Skill for every Trellis planning gate (`clarify`, `research`, `plan`,
`plan-check`, or `grill-me`) when a choice may change scope, owner, safety
boundary, public behavior, data, deployment, cost, or acceptance criteria. It
does not perform deployment and does not create a second task lifecycle.

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

## Decision Chain State

At the start of planning, inspect the task evidence and create a decision
inventory in the active Trellis PRD or research artifact. Each node records an
id, owner, question, options, recommendation, evidence, dependencies, impact,
and revisit condition. Mark nodes `open`, `answered`, `blocked`, or `sealed`;
facts that the repository or approved sources can answer are closed by the
agent and are not user questions.

The planning artifact is the durable state. Do not keep the decision graph only
in the conversation, runtime state, Codex configuration, or a parallel ledger.

## Frontier And Rounds

At each round, calculate the frontier: unresolved user-owned nodes whose
dependencies are sealed. Ask all independent frontier nodes in one native
request, with at most three questions. If only one independent node is ready,
ask one; batching is conditional, not a quota. Do not ask a dependent node
early. Keep execution approval separate from design decisions.

After the user answers, end the round. On the next turn, read the answers,
record every selected option and rationale in the active PRD/research artifact,
recheck evidence and downstream dependencies, and recalculate the frontier.
Do not ask the next round before the previous answers are durable.

When the frontier becomes empty, run a conflict audit across scope, ownership,
security, compatibility, rollout, rollback, cost, and acceptance. If any two
sealed decisions conflict, mark the affected nodes `blocked`, explain the
conflict, and ask a new conflict-resolution question. Repeat the
answer-record-frontier-audit cycle until no conflict remains.

Only then write the final seal: all nodes are `sealed`, the conflict audit is
clean, `prd.md`, `design.md`, and `implement.md` agree, and implementation has
no user-owned ambiguity. Stop at the Trellis planning approval boundary;
implementation starts only after the normal task approval.

Call the current session's native `request_user_input` directly when it is
available. Do not detect or replace it through `functions.exec`, nested
`tools.*`, `ALL_TOOLS`, shell, or MCP. Correct a schema error at most once;
host refusal, cancellation, timeout, or genuine unavailability may use a
plain-text fallback, but the unanswered decision still stops the turn. Never
silently choose the recommendation.

After asking, stop the turn. The next turn must read and persist the answers
before writing new questions, applying, committing, archiving, or advancing a
dependent gate.

## During Implementation

Use sealed task/spec decisions for ordinary implementation choices. For a
local reversible choice, continue and record the decision. For a material
unresolved ambiguity, do not open a popup during implementation or apply:
record `decision-needed`, run `task.py replan <task> "<reason>"`, and return to
the Trellis planning/design step. Continue implementation only after the new
frontier is answered, conflict-audited, and sealed. If evidence disproves the
approach, preserve the retracted conclusion and the reason in task history.

Never edit `task.json.status` by hand. If the installed Trellis runtime lacks
the controlled `replan` transition, stop at the planning boundary and report
the runtime gap instead of opening a popup or silently choosing.

## Decision Record

For each material decision, retain: question, options, selected option,
recommendation, rationale, impact, evidence, and the condition that would
justify revisiting it. Keep this record in the current Trellis task; do not
create a parallel ledger in Codex configuration or runtime state.
