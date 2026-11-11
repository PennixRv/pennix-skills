# Integrate Grok Search Retrieval Skill

## Goal

Add `grok-search` to the direct Pennix user Skill collection as a vendored,
runnable Node package. It is the ordinary external-retrieval route after the
user supplies its connection configuration. Keep the upstream Responses
protocol and its scripts; make only the local routing changes needed to use
one self-hosted Tavily supplementary result and no accidental Firecrawl or
native Codex-search fallback.

## Scope And Ownership

- Modification target: this `pennix-skills` repository.
- Vendor upstream `BlueOcean223/grok-search` commit
  `8e82629c93cb5f2031e2b6ad2db99aeb223cbdd9` under `skills/grok-search/`,
  excluding only `.git` and generated dependencies.
- Set the vendored default extra-source count to one. With a configured
  Tavily-compatible endpoint, that allocation is Tavily-only; the Pennix
  instructions must not ask for a higher extra count or the automatic fetch
  provider.
- Install `undici` into the staging collection with `npm ci --omit=dev
  --ignore-scripts` before replacing the user collection. A failed install
  must retain the previous collection.
- Revise `tavily-hikari` and `pennix-workflow-routing` to make Grok the
  normal route, direct self-hosted Hikari the one bounded availability
  fallback, and neither public Hikari nor Codex native search a fallback.

## Constraints

- Do not add a global CLI, provider abstraction, credentials, runtime output,
  or configuration file containing secrets.
- Preserve upstream tests and add only focused checks for Pennix-specific
  default/installer behavior.
- Do not promise that Hikari's `extract` or `map` facade works before the
  deployed service is tested with a user-provided account pool.

## Acceptance Criteria

- [x] The vendored Skill has the recorded upstream revision, license,
      package metadata, scripts, tests, docs, and a concise `UPSTREAM.md`.
- [x] Its default extra result is one, and the documented normal route cannot
      invoke Firecrawl or Codex native search.
- [x] The installer installs Node production dependencies in staging and
      retains the old destination if that step fails.
- [x] The two existing routing Skills identify `grok-search` as default and
      self-hosted `tavily-hikari` as an explicit single fallback.
- [x] Source tests, Skill validation, installer dry check, and a staged
      installation pass without credentials.
