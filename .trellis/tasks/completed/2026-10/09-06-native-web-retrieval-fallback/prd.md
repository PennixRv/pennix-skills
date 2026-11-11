# Add native web retrieval fallback

## Goal

Prefer Tavily Hikari and use Codex native web retrieval after one confirmed Hikari failure.

## Confirmed Facts

- skills/tavily-hikari/SKILL.md currently prefers tvly-hikari but directs every command, quota,
  timeout, and malformed-response failure to stop rather than switch providers.
- skills/pennix-workflow-routing/SKILL.md selects tavily-hikari for current web retrieval and separately
  prohibits a substitute provider. The two files are therefore consistent but do not provide the requested
  fallback.
- A 2026-09-06 one-shot Hikari request succeeded after prior EdgeOne 554 responses. The failure mode is
  intermittent, so a fallback must not add retry loops or change Hikari configuration.

## Requirements

1. Ordinary current web search, page retrieval, and multi-source research must first use tavily-hikari.
2. A single correctly formed Hikari operation that fails because the source is unavailable, including an
   upstream/network error, quota response, timeout, unavailable prerequisite, or malformed response, must
   route the same bounded request to Codex native web retrieval in the current session.
3. Invocation/usage errors that can be corrected locally, such as an unsupported CLI option, must be corrected
   before deciding Hikari is unavailable; they do not trigger fallback by themselves.
4. Fallback must not loop, alter Hikari configuration, expose tokens/configuration, or run in parallel with a
   still-pending Hikari request. It must preserve explicit source, freshness, privacy, and scope constraints.
5. Native web retrieval is a bounded substitute for search and known-page reading. It must not claim to emulate
   Hikari-specific map, crawl, or research; those operations degrade only to the necessary bounded search plus
   page reads.
6. When fallback is used, make the route change visible in the response without reproducing sensitive failure
   details. If the native tool is unavailable too, report the retrieval gap rather than selecting a third provider.
7. A user, task, or system instruction that requires a specific retrieval tool or source remains higher priority
   than this default.

## Out Of Scope

- Hikari service, CLI wrapper, endpoint, token, quota, timeout, retry, or deployment changes.
- A new provider abstraction, automatic health probe, background retry, provider rotation, or persistent
  availability state.
- Changes to /home/penn/.codex/AGENTS.md, Trellis lifecycle behavior, or external-web result persistence.

## Acceptance Criteria

- [ ] tavily-hikari names Codex native web retrieval as the sole fallback after one confirmed availability
  failure and preserves the no-loop/no-reconfiguration/token-safety constraints.
- [ ] pennix-workflow-routing routes ordinary external retrieval to Hikari first and specifies the same
  fallback, scope, and terminal behavior.
- [ ] Both Skills distinguish correctable local invocation errors from source unavailability and retain higher
  priority tool/source requirements.
- [ ] The source collection passes the installer check; after the user-approved deployment, the installed copies
  match the changed source and no user configuration or token is modified.

## Open Questions

None. The user specified the preferred source, the fallback tool, and the required failure behavior.
