# Design

`grok-search` is a direct Skill package, not a wrapper service. The upstream
Node package stays intact so it can be audited and updated against its source.
Pennix changes its default extra-source count from six to one. The existing
upstream allocation then makes the normal configured path one Tavily result
and zero Firecrawl results.

The collection installer already stages all Skills and atomically replaces its
destination. Run the upstream package's production dependency install in that
stage before the replacement. No global executable is necessary because the
Skill calls its local scripts with Node.

The Skill entrypoint carries the actual local routing decision: search uses
Grok plus one Tavily extra; page reads select `tavily` only after Hikari's
operation is proven, otherwise `direct`; site mapping selects `tavily` when
available or `direct`. A confirmed Grok availability failure permits one
direct call through `tavily-hikari`; bad local invocation does not.

No secret-bearing configuration is generated. The later user setup writes
Grok and Hikari values outside this source repository.
