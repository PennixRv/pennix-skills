# Tavily Hikari Operations

Use these commands through `tvly-hikari`, never by setting `TAVILY_API_KEY` manually. The wrapper maps the
configured Hikari origin to `/api/tavily`, supplies the configured Hikari access token to that facade, and
lets Hikari enforce quota, audit logging, and upstream key-pool routing.

All examples use `--json`. Keep output in the request unless the user has requested a saved artifact.
Commands may also expose `--client-name` for downstream request attribution. Do not set it automatically:
it can reveal a user, project, or agent identity to the third-party service.

## Search

Use search when there is no specific page to read.

```bash
tvly-hikari search "current agent protocol changes" --json
tvly-hikari search "current agent protocol changes" \
  --depth advanced --max-results 8 --time-range month --topic news --json
tvly-hikari search "official API migration guide" \
  --include-domains example.com --exclude-domains forum.example.net --json
```

Choose only relevant controls:

- `--depth ultra-fast|fast|basic|advanced` and `--max-results 0..20` balance coverage and cost.
- `--topic general|news|finance`, `--time-range day|week|month|year`, `--start-date`, and `--end-date`
  express freshness constraints.
- `--include-domains` and `--exclude-domains` constrain sources. Prefer a direct official URL plus extract
  when one is already known.
- `--include-answer`, `--include-images`, `--include-raw-content markdown|text`, and
  `--chunks-per-source` increase response size. Request them only when they materially improve the task.

## Extract

Use extract for one or more known, relevant public URLs. Confirm that each URL is specific to the request;
do not extract private, unrelated, or credential-bearing pages.

```bash
tvly-hikari extract https://example.com/article --json
tvly-hikari extract https://example.com/article \
  --query "migration steps" --chunks-per-source 3 --extract-depth advanced --format markdown --json
```

`--query` reranks content; `--chunks-per-source 1..5` requires it. `--extract-depth basic|advanced`,
`--format markdown|text`, `--include-images`, and `--timeout 1..60` are available when needed. Use `-o`
only for a user-requested or approved output file.

## Map

Use map to discover URLs below a canonical documentation or site root before deciding what to extract or
crawl.

```bash
tvly-hikari map https://example.com/docs --json
tvly-hikari map https://example.com/docs \
  --instructions "Find API reference and migration guides" \
  --select-paths "/docs/.*" --max-depth 2 --limit 100 --no-external --json
```

Keep scope explicit with `--max-depth 1..5`, `--max-breadth`, `--limit`, `--select-paths`,
`--exclude-paths`, `--select-domains`, and `--exclude-domains`. Pass `--no-external` unless the request
needs links outside the selected site; `--allow-external` deliberately expands the target surface. Map
results are candidates for the next command, not the final factual answer.

## Crawl

Use crawl only when multiple pages from a bounded public site section are needed. Before running it, define
the starting URL, a small `--limit`, the needed depth/breadth, and path or domain filters where the site is
not already narrow.

```bash
tvly-hikari crawl https://example.com/docs \
  --max-depth 2 --max-breadth 10 --limit 20 \
  --select-paths "/docs/.*" --no-external --json
```

The command also supports `--instructions`, `--chunks-per-source`, `--extract-depth`, `--format`,
`--include-images`, `--allow-external / --no-external`, `--timeout 10..150`, and output controls. Pass
`--no-external` unless cross-domain links are needed. `--output-dir` writes one Markdown file per page and
is appropriate only for an explicitly requested or task-approved artifact directory. Do not default to
whole-site crawling.

## Research

Use research for a multi-source synthesis that cannot be answered by a bounded search plus extract. Write a
concise question including the desired scope, time period, geography, and source constraints.

```bash
tvly-hikari research "Compare current agent protocol support in official documentation" \
  --model auto --citation-format numbered --json
```

`--model mini|pro|auto`, `--stream`, `--output-schema`, `--citation-format`, `--poll-interval`, and
`--timeout` control the official research request. The normal command waits for its bounded result. If a
request was deliberately started with `--no-wait`, use the official single follow-up command only when the
user still wants the result:

```bash
tvly-hikari research status <request-id> --json
tvly-hikari research poll <request-id> --json
```

Do not implement manual status polling around these commands. Save research output with `-o` only when an
approved artifact is needed, then retain citations and verify material claims against the cited sources.

## Diagnostics And Service Boundary

Run `tvly-hikari doctor` only after a CLI/configuration error or an explicit user request to diagnose
readiness. It checks the local wrapper, configuration, and compatible official CLI, but can display masked
configuration fields; do not repeat those fields in messages or task artifacts. Do not run
`tvly-hikari config show` unless the user explicitly asks for that masked diagnostic. Neither command
validates source truth or replaces a real retrieval. Hikari requests use the configured `/api/tavily`
facade; Hikari's service, not this Skill, owns token quota, audit logs, and upstream API-key selection.

## Upstream Alignment

This reference consolidates the operation-specific guidance from Tavily Hikari's `best-practices`, `cli`,
`search`, `extract`, `map`, `crawl`, and `research` Skills. The consolidation is intentional: all seven
share one configured CLI, token boundary, JSON output convention, and Hikari service contract. The Pennix
entrypoint adds only workflow-specific routing, bounded output, source verification, and task-recording
rules.

Upstream sources:

- <https://github.com/IvanLi-CN/tavily-hikari/tree/main/skills>
- <https://github.com/tavily-ai/tavily-cli>
