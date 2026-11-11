# Technical Design

## Boundaries

The repository has two separately owned behavior changes:

1. `pennix-agent-output-quality` owns content coverage, proportional detail, emphasis, structure, relation-driven tables and Mermaid diagrams, and semantic output review.
2. `pennix-decision-grill` owns the planning review gate and unresolved user tradeoffs. It does not depend on the new output Skill and does not replace Trellis lifecycle commands.

`pennix-chinese-tech-writing` remains the language and fidelity owner. `pennix-workflow-routing` receives one minimal composition mapping. `pennix-component-lifecycle` remains the collection owner and receives only the required catalog entry. No user rules, Trellis workflow source, FastCtx route, plugin, model evaluator, or runtime service changes are in scope.

## Source Targets

| Target | Change | Boundary |
| --- | --- | --- |
| `skills/pennix-agent-output-quality/SKILL.md` | New automatic Skill entry | Output-quality behavior only; simple facts use a short path |
| `skills/pennix-agent-output-quality/references/agent-output-quality.md` | Conditional detailed guidance and examples | Loaded for complex delivery or visual/review choices |
| `skills/pennix-agent-output-quality/UPSTREAM.md` | Fixed sources, licenses, and local adaptation | Methods only; no copied upstream runtime or restricted assets |
| `skills/pennix-workflow-routing/SKILL.md` | One routing table row | Composition only; no second state machine |
| `skills/pennix-decision-grill/SKILL.md` | Planning review gate | Review before final plan display/approval; existing approval contract remains authoritative |
| Related contract tests | Assert new routing and gate invariants | No wording-only mirror test for every line |
| `component-versions.json` | Add name and exact source path | Existing native installer contract remains unchanged |

## Review Gate

The gate checks goal/requirement coverage, actual targets and owners, existing contracts, scope, decisions, acceptance and validation, release/install impact, risks, rollback, completion, stopping point, and whether the approval object is legible. It classifies findings as evidence/contract defects, user-owned tradeoffs, known limitations, or pass. Direct corrections and user answers cause the affected plan to be reread and reviewed again. Only a pass reaches the existing final plan display and approval question.

The gate does not add a status, task ledger, Channel protocol, or authorization mechanism. A material change to an already sealed plan returns to the native Trellis planning and reseal path.

## Delivery Constraints

The collection is installed by Codex's system `$skill-installer`; the catalog is the only source of its declared member paths. No installation copy is edited directly. The current expression policy adopts tables and Mermaid flow/sequence/state diagrams when the relation benefits; Gantt diagrams and the two researched Mermaid add-ons remain out of scope.
