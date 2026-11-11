# Align Trellis setup and component routing

## Goal

Pin the released Pennix Trellis workflow version and keep workflow component commands outside context-mode aggregation.

## Requirements

- Advance the default Pennix Trellis workflow source pin to the released
  immutable Marketplace `v0.6.24` tag.
- Clarify that Trellis, handoff, Channel, Skills, Git mutation, installation,
  and other workflow component calls remain direct rather than being collected
  by context-mode.
- Preserve context-mode's narrow role for genuinely unbounded local textual
  output and explicitly requested direct API response analysis.
- Preserve Grok-first external retrieval with one Tavily Hikari fallback and
  leave handoff schema and RecoveryBrief ownership unchanged.
- Review automatic Skill selection for the Pennix entry points. Widen only
  natural-language intent descriptions for setup and cross-component routing;
  keep formal handoff, installation, and Hook registration explicitly gated.

## Acceptance Criteria

- [x] Setup examples/defaults resolve `codex-subnode-channel` from `v0.6.24`.
- [x] The routing Skill draws the direct-component boundary without an
  unnecessary per-tool blacklist or new coordination mechanism.
- [x] Existing focused validation passes and the pushed collection installs
  atomically through its current installer.
- [x] Setup and routing remain normally implicitly discoverable without an
  added dispatcher, while high-impact Skills retain their explicit boundaries.

## Constraints

- Do not add a user-level RecoveryBrief coordinator, alter the handoff schema,
  access context-mode storage, or take responsibility for Trellis workflow
  lifecycle.

## Verification

- `python3 /home/penn/.codex/skills/.system/skill-creator/scripts/quick_validate.py`
  passed for both changed Skills.
- The collection's native installer `--check` validated all 10 Skills from
  this source checkout.
- Fresh `trellis init --codex --yes --workflow codex-subnode-channel
  --workflow-source gh:PennixRv/marketplace#v0.6.24` created the managed
  project assets, including the bundled research-record Skill, without a
  `.new` workflow file. Existing-project workflow selection remains subject to
  Trellis's native local-edit protection.
