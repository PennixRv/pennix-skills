# Pennix Cognee adaptation design

Use the existing lifecycle/configuration/handoff owners. Add one small Cognee client module and one launcher/ingress implementation only where existing AgentMemory adapters cannot be reused. The client talks to the official HTTP API and treats the dataset UUID as proof authority. It never opens Cognee storage directly.

Project registration uses the canonical Git common root, a stable slug/hash dataset name, a private service dataset UUID, and a principal binding. Missing or ambiguous registration disables memory and reports the reason. The launcher loads private `~/.cognee/.env` and `~/.config/cognee/projects.json`, then invokes native `codex --no-daemon` with an ephemeral config override; it must not modify a shared daemon or bypass hook trust.

The official plugin remains unchanged and globally disabled. The launcher enables it only for the registered root. Handoff exact proof uses dataset listing, unique metadata/digest match, and the native raw endpoint. Recall enhancement is a thin ASGI route inside the official API process, reusing official auth and recall serialization while adding the SDK retriever flags; no second database process, fork, monkeypatch, or custom retrieval algorithm.

All active old adapters are deleted only after the new client is installed and live acceptance passes.
