# Connection and index ownership

The optional lifecycle target `siyuan-connection` configures the user's native
`siyuan` Streamable HTTP MCP entry. It does not deploy a kernel or enable a
mandatory knowledge backend. Run lifecycle discover first, then configure that
one target from the operator's own terminal. The API Token is read with terminal
echo disabled, never from chat, argv, environment, or NAS configuration copying.

Private owner record:
`${XDG_CONFIG_HOME:-~/.config}/pennix-siyuan/connection.json`, directory 0700,
file 0600. It contains schema 1, `url`, `api_token`, and `default_notebook`.
Native `http_headers_helper` reads it on connection and emits the Authorization
header directly to Codex; the helper has no HTTP, capture, or note-write logic.
Only its `--metadata` mode is suitable for diagnostics. Credentials stay outside
Git. `required=false` allows normal project work without the knowledge server.

Configuration verification means local owner/config integrity, not a successful
server handshake. Reconnect native MCP after configuration and verify actual
tools/version/notebook; a session with an old tool directory may need restart.
Token rotation updates the private record; do not print helper output to check it.

NAS and other SiYuan clients are independent kernels/workspaces. S3 stores sync
objects, not a central MCP or shared SQL database. AI/model/MCP configuration is
kernel-local; confirm that each affected client is intentionally configured.
Use the NAS kernel for workflow knowledge and the client's normal S3 sync for
human clients. This skill does not reconfigure client sync.

Before semantic reads/writes, set and verify native `data/.siyuan/embeddingignore`
for the selected notebook, then rebuild derived vectors through native settings.
Rules depend on the upstream matcher and real notebook ID; verify both. For the
matching upstream gitignore implementation, exclude all paths and explicitly
reinclude the selected notebook's descendants. Never call a query that can
read another notebook before scope is verified. Rebuild removes old derived
vectors; it cannot retract content already sent to providers. Preserve the
user-selected embedding dimensions/rerank endpoint. Index maintenance is a
kernel-owner action, not MCP SQL or a direct database edit.
