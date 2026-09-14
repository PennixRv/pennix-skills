---
name: grok-search
description: Use for current external information or a known public URL when Grok Responses web search is configured. It is the default Pennix web-retrieval path; do not use for local repository lookup, stable offline knowledge, or a request that requires another specified source/tool.
metadata:
  short-description: Grok-first web retrieval with one Hikari Tavily source
---

# Grok Search

Use the vendored Node scripts through their absolute Skill path. The Pennix
installer installs their local production dependency; do not run global `npm`
installs or create a provider wrapper.

## Normal Route

- An unknown URL or current fact: run `scripts/search.js "query"`. The Pennix
  default is Grok-only (`--extra` is `0`), so no supplementary provider starts
  implicitly. Add an explicit `--extra N` only when independent sources are
  needed; that phase starts after the Grok request and remains observable.
- A known public URL: use `scripts/fetch.js --provider tavily URL` only after
  the deployed Hikari `/extract` operation has been verified. Until then use
  `--provider direct`; never use `--provider auto` or `firecrawl` in the
  Pennix route.
- Site discovery: use `scripts/map.js --provider tavily URL` only after its
  Hikari operation is verified; otherwise use `--provider direct`.
- Add source filters, X search, output expansion, or a larger extra count only
  when the request needs them. Do not run map, fetch, and search as a default
  chain.

All scripts emit one JSON object. Check `error`, `diagnostics.provider_attempts`,
and the returned source URLs before using external facts. `degraded: true`
means the answer is raw Tavily source output after an explicit Grok quota
failure, not a Grok synthesis.

## Availability Boundary

Correct a malformed local command before changing routes. A confirmed Grok
availability, network, quota, or source failure permits exactly one bounded
direct operation through `$tavily-hikari`; state that the answer used the
Tavily route. Do not retry in a loop, use public Hikari, Firecrawl Keyless, or
Codex native web search. If self-hosted Hikari is not configured or that direct
operation is unavailable, report the retrieval gap.

The user configures `GROK_API_URL`, `GROK_API_KEY`, provider/model settings,
and Hikari-compatible `TAVILY_API_URL`/`TAVILY_API_KEY` outside this Skill.
Never read, print, commit, or copy those values. Read [UPSTREAM.md](UPSTREAM.md)
before updating the vendored code; read `references/planning.md` only for
multi-part research.
