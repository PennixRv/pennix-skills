# Web Retrieval Fallback Routing Audit

Date: 2026-09-06 (Asia/Shanghai)

## Scope

The requested behavior is a user-level workflow policy: prefer tvly-hikari for ordinary external retrieval,
then use Codex native web retrieval when Hikari is unavailable. The actual source target is this
pennix-skills repository; the installed collection at /home/penn/.codex/skills/pennix-skills/ is a deployment
copy and must not be edited directly.

## Verified Current Behavior

- skills/tavily-hikari/SKILL.md prefers Hikari but says its failure handling must not silently switch to another
  provider. Its only exception is a route required by higher-priority instructions.
- skills/pennix-workflow-routing/SKILL.md routes current external retrieval to tavily-hikari and repeats the
  blanket prohibition on substitute providers.
- Both files therefore lack an autonomous fallback policy. Their current behavior is consistent with each other
  but inconsistent with the user's 2026-09-06 explicit workflow requirement.
- The existing Hikari diagnosis established that 554 Response Timeout by EdgeOne can be intermittent: four
  earlier bounded searches failed, while one later one-shot bounded search succeeded. It is inappropriate to add
  retry loops, configuration changes, or health probing merely to hide that condition.

## Adopted Policy

1. Use Hikari first for ordinary web search, known-page retrieval, and multi-source research.
2. On one terminal availability failure from a correctly formed Hikari operation, use the current session's Codex
   native web retrieval tool as the sole fallback for the same bounded request.
3. Locally correctable invocation errors are not availability failures. Correct the invocation before fallback.
4. Preserve the user/task/system source constraints, request bounds, and external-evidence verification rules.
   Do not expose token/configuration values, retry in a loop, mutate Hikari, or add a third provider.
5. Do not pretend native web retrieval has Hikari's map/crawl/research semantics. Reduce those cases to the
   smallest search and page-reading sequence needed for the request.

## Evidence Locations

- skills/tavily-hikari/SKILL.md, Boundary and Execution And Evidence sections.
- skills/pennix-workflow-routing/SKILL.md, decision-order table and output section.
- Root-project record: ../.trellis/tasks/09-05-agents-md-practice-reference/research/
  tavily-hikari-timeout-investigation-20260905.md (the root task's recorded Hikari timeout evidence).

## Project Skill Layout Investigation

- Official Codex documentation, [Build skills](https://learn.chatgpt.com/docs/build-skills), states that repository
  Skills are discovered from `.agents/skills` between the current directory and repository root. Its `.codex/config.toml`
  setting is only a user-level Skill enable/disable mechanism; it does not relocate repository Skill discovery.
- The installed Trellis 0.6.18 Codex configurator (`/usr/lib/node_modules/@pennixrv/trellis/dist/configurators/codex.js`)
  writes workflow Skills to `.agents/skills`, creates `.codex/agents`, config, and Hooks as Codex-specific assets, and
  only ensures an empty `.codex/skills` directory for user-owned custom Skills. The initializer has no option that
  changes the workflow Skill root.
- The generated `.trellis/config.yaml` controls `codex.dispatch_mode`; it does not control the Skill path. This
  repository now explicitly sets `codex.dispatch_mode: inline` so task execution and verification remain in the main
  session, as required by the current workflow contract.

Decision: retain `.agents/skills` as the repository-owned, Codex-native shared Skill location. Do not duplicate or
move Trellis workflow Skills into `.codex/skills`.

## Spec Synchronization

No separate `.trellis/spec` rule is added. This task changes a user Skill's executable routing contract rather than
a repository API or implementation convention; `skills/tavily-hikari/SKILL.md` and
`skills/pennix-workflow-routing/SKILL.md` are the single durable sources for the behavior. Duplicating the policy in
a generic bootstrap spec would create a second source that can drift.

## Next Action

After the user approves the final plan, revise only the two ownership files, run pure-policy structural checks and
the collection installer check, then install the explicit local source checkout so a new Codex session discovers
the updated Skills.
