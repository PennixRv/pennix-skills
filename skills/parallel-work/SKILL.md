---
name: parallel-work
description: Prepare a bounded independent Trellis candidate-work request for analysis, design, audit, review, or verification without taking over worker lifecycle.
---

# Parallel Work

Use this only when independent candidate work has evidence value. Candidate roles can cover analysis, design critique, audit, review, or verification; keep ordinary single-lens work in the main session.

1. Confirm the active task and define a non-empty, exact scope, question, lens, evidence method, and role.
2. For a major or critical conclusion, define a primary and a counter lens before dispatch; do not call the counter a review until
   it is bound to the primary report.
3. Validate a request description with `scripts/build_request.py`, then use the current Trellis fork's documented channel API.
   Trellis owns spawn, event order, wait continuation, deadlines, cancellation, and cleanup.
4. For an already-spawned worker, establish one native wait continuation before sending a prompt that can complete quickly, then resume that same continuation. Do not poll, create a second waiter, or inspect runtime state through this Skill. Set an explicit `--idle-timeout` when setup can delay the first send.
5. Workers may read any task-relevant project or external material, but write only their assigned report. The main session verifies and promotes candidate results.

This Skill does not implement workers, own a batch ledger, restrict read paths, add provider-specific behavior, expand worker write authority, or promote reports.
