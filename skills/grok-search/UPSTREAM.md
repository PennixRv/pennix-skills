# Upstream Provenance

Vendored from <https://github.com/BlueOcean223/grok-search> at
`8e82629c93cb5f2031e2b6ad2db99aeb223cbdd9` (2026-08-16), under its included
MIT `LICENSE`.

The package keeps the upstream scripts, tests, documentation, configuration
example, lockfile, and package metadata. Pennix changes the default external
source count to `1`, aligns the configuration example, usage text, diagnostics,
and test fixture with that route, and does not report Firecrawl when it was not
allocated. It also removes two no-behavior whitespace errors so the vendored
tree passes repository whitespace checks. The local `SKILL.md` is the Pennix routing contract: ordinary
requests use Grok plus one self-hosted Tavily result, and do not invoke
Firecrawl or Codex native web search. Upstream README material still describes
optional upstream provider capabilities; it is not the default Pennix route.
