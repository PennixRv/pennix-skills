# Implementation

1. Replace the repository policy that forbids a fixed workflow selection with
   the narrower Pennix-default policy.
2. Update the existing Skill only; keep its description discriminating and its
   body limited to intent routing, native commands, and observable checks.
3. Validate the Skill with the bundled validator and run an isolated real CLI
   smoke test against the published tag.
4. Commit, push, and use the existing explicit Pennix installer to deploy the
   checked-out collection. Compare installed and source Skill contents.
