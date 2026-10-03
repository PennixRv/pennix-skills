# Cognee deployment overlay

Build this overlay from the `pennix-cognee-memory` directory after the official
Cognee `v1.6.2` backend image is available locally:

```bash
docker build \
  --build-arg BASE_IMAGE=pennix-cognee-backend:1.6.2-ba3631f \
  -f deployment/Dockerfile.overlay \
  -t pennix-cognee-backend:1.6.2-pennix \
  .
```

The overlay copies only the Pennix ASGI ingress. The official Cognee source,
package, entrypoint migrations, UI, storage engines, auth, and worker count
remain owned by the upstream image.

The official UI image copies public assets without changing their build-context
permissions. If the context was extracted under a private NAS umask, build the
`Dockerfile.ui-permissions` layer over the pinned official UI image to grant
read/traverse access to public assets. It changes no UI source and still runs
as `nextjs`; pin the resulting image ID in the private compose owner.

The public reverse proxy must route both `/api/v1/` and the exact `/health`
path to the backend. The official plugin gates registration and session sync
on `/health`; routing that path to the UI leaves capture buffered even when
authenticated API calls work. Keep UI `/api/runtime-config` on the UI service.

For the current CCH OpenAI-compatible route, configure the supported upstream
`STRUCTURED_OUTPUT_FRAMEWORK=instructor` and `LLM_INSTRUCTOR_MODE=json_mode`.
The native schema path's `SessionTurnAnalysis` uses `oneOf`; the upstream rejects
it and CCH wraps that 400 as 503, preventing Cognee's native schema fallback.
JSON mode keeps upstream Pydantic validation and the full improve pipeline
without modifying Cognee source. Preserve `LLM_ARGS` reasoning effort and use
CCH usage accounting when a structured response does not expose token counts.

The fixed upstream 30-second connection test can time out on a reasoning model.
After separate real LLM and embedding probes pass, set the supported
`COGNEE_SKIP_CONNECTION_TEST=true` and retain real pipeline verification.
The Pennix synchronous phase-close improve waits up to 1200 seconds: the live
full nine-stage run took 474 seconds, beyond the plugin's 420-second submission
budget. Ordinary client calls and the immutable official plugin budgets stay
separate; a timeout or incomplete stage remains a visible failure.
