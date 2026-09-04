---
name: tavily-hikari
description: Use the Hikari-backed tvly-hikari CLI for current web search, URL extraction, bounded site mapping or crawling, and multi-source research; 在需要互联网检索或网页内容时使用。 Do not use for local repository lookup, Fast Context semantic code candidates, or a route that requires a specific official source or tool.
metadata:
  short-description: Hikari-backed Tavily web retrieval
---

# Tavily Hikari

Use the configured `tvly-hikari` CLI for current external information. It routes official Tavily CLI
operations through the user's Hikari endpoint and returns structured results. Prefer it over generic web
search for ordinary online retrieval, while preserving any system, user, or task requirement to use a
specific official source or tool.

## Boundary

- Use `tvly-hikari ... --json` for agent-readable results. Cite the returned source URLs when external
  facts support the answer, and locally verify any result that will affect project, task, or Git facts.
- Hikari access tokens begin with `th-`; they are not Tavily API keys. Never request, print, copy, commit,
  or reconfigure a token. Do not read the Hikari config file. `tvly-hikari config show` is permitted only
  for a user-requested, masked diagnostic.
- This Skill does not install or upgrade `tvly`, configure Hikari, enable MCP, add Hooks, or start a
  provider-specific fallback. If `tvly-hikari doctor` reports an unavailable prerequisite, report the
  bounded diagnostic and stop that retrieval path.
- Hikari is a third-party service. Search queries, target URLs, and the configured access token are sent
  to its endpoint. Keep queries and targets relevant to the user's request; do not submit secrets, local
  paths, private documents, or unrelated personal data. Do not set `--client-name` automatically: it can
  disclose a user, project, or agent identity.
- Do not use this Skill for local files, literals, logs, repository history, symbols, task state, or
  ambiguous legacy code-location candidates. Keep Fast Context in its existing, narrower role for the
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

## Execution And Evidence

- Run `tvly-hikari doctor` only after a CLI or configuration-related failure, or when the user asks to
  diagnose readiness. It is not a per-task or per-query preflight. Its output can include masked
  configuration fields; never relay those fields in messages or task artifacts.
- Keep normal results in the current request. Pass `-o` or `--output-dir` only when the user asks for a
  reusable artifact or an approved task path requires it; do not write retrieval output into a project by
  default.
- Treat search, extract, map, crawl, and research output as external evidence. Preserve source URLs, date
  context, scope, and material uncertainty in any conclusion. For task-relevant research, record verified
  findings through `trellis-research-record`; raw result dumps and token-bearing configuration never enter
  task artifacts.
- A command error, quota response, timeout, or malformed response means this source is unavailable. Do not
  retry in a loop, reinterpret the failure as a factual result, alter configuration, or silently switch to
  another provider. Follow a route explicitly required by higher-priority instructions, or report the
  unavailable retrieval path.
