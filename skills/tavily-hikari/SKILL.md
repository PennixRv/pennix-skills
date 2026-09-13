---
name: tavily-hikari
description: Use the self-hosted Hikari-backed tvly-hikari CLI for Tavily-specific search, URL extraction, bounded mapping/crawling, or the one direct fallback after Grok Search is unavailable. Do not use for local repository lookup, ordinary Grok-first retrieval, or a route that requires a specific official source or tool.
metadata:
  short-description: Hikari-backed Tavily web retrieval
---

# Tavily Hikari

Use the configured `tvly-hikari` CLI only for Tavily-specific operations or a
confirmed single fallback from `grok-search`. It routes official Tavily CLI
operations through the user's self-hosted Hikari endpoint and returns
structured results. Ordinary online retrieval starts with `grok-search`.

The configured endpoint must be the user's self-hosted Hikari deployment.
Until that configuration exists, treat this route as unavailable; do not use a
pre-existing public Hikari endpoint.

## Boundary

- Use `tvly-hikari ... --json` for agent-readable results. Cite the returned source URLs when external
  facts support the answer, and locally verify any result that will affect project, task, or Git facts.
- Hikari access tokens begin with `th-`; they are not Tavily API keys. Never request, print, copy, commit,
  or reconfigure a token. Do not read the Hikari config file. `tvly-hikari config show` is permitted only
  for a user-requested, masked diagnostic.
- This Skill does not install or upgrade `tvly`, configure Hikari, enable MCP,
  add Hooks, or start another external provider. It does not fall back to
  public Hikari, Firecrawl, or Codex native web retrieval.
- Hikari is a third-party service. Search queries, target URLs, and the configured access token are sent
  to its endpoint. Keep queries and targets relevant to the user's request; do not submit secrets, local
  paths, private documents, or unrelated personal data. Do not set `--client-name` automatically: it can
  disclose a user, project, or agent identity.
- Do not use this Skill for local files, literals, logs, repository history, symbols, task state, or
  ambiguous legacy code-location candidates. Keep Windsurf Code Search in its existing, narrower role for the
  latter after local retrieval and CodeGraph are insufficient.

## Select An Operation

1. **Search**: no specific URL is known. Shape a narrow query, then add only the needed freshness, domain,
   topic, depth, or result-count controls.
2. **Extract**: one or more relevant public URLs are already known. Use the extracted text as evidence, not
   as an unverified conclusion.
3. **Map**: a site or documentation root is known but the relevant pages are not. Feed only useful URLs
   into a later extract or bounded crawl.
4. **Crawl**: multiple pages from a bounded public site section are needed. Define start URL and limits
   before running it; broad site-wide crawling is not a default.
5. **Research**: a multi-source synthesis is needed. State scope, time period, geography, and source
   constraints before requesting it.

Read [the operation reference](references/operations.md) before using map, crawl, or research, and whenever
the basic search/extract command needs option selection, saved output, or failure handling.

## Failure Boundary

- A correctly formed operation that returns an upstream/network error, quota
  response, timeout, unavailable prerequisite, source-caused command failure,
  or malformed response is unavailable for that request.
- Correct an unsupported option, missing argument, or malformed local command
  first. It does not authorize a provider change.
- Do not retry, parallel-run, alter Hikari configuration, or select another
  provider. Report the bounded retrieval gap. A system, user, or task
  instruction requiring a specific source/tool remains higher priority.

## Execution And Evidence

- Run `tvly-hikari doctor` only after a CLI or configuration-related failure, or when the user asks to
  diagnose readiness. It is not a per-task or per-query preflight. Its output can include masked
  configuration fields; never relay those fields in messages or task artifacts.
- Keep normal results in the current request. Pass `-o` or `--output-dir` only when the user asks for a
  reusable artifact or an approved task path requires it; do not write retrieval output into a project by
  default.
- Treat search, extract, map, crawl, and research output as external evidence. Preserve source URLs, date
  context, scope, and material uncertainty in any conclusion. In an initialized Trellis project, use its
  bundled `trellis-research-record` for verified task-relevant findings; raw result dumps and token-bearing
  configuration never enter task artifacts.
- Treat an availability failure as an operational diagnostic, not a factual
  result. Do not hide it with retries, configuration changes, or provider
  rotation.
