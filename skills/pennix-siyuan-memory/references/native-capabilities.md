# Native capability use

Use the current native MCP tool catalog as the capability and argument
authority. Upstream kernels can expose document/block reads and edits,
full-text/semantic search, SQL, outlines/references, attributes, notebook and
document organization, assets, import/export, history, internal Agent Skills,
and system/network management. Presence in the catalog does not authorize a
side effect. Preserve native exposure instead of inventing a parallel API.

For SQL, use scoped read queries for the question; SQL is not the normal writer.
For blocks, preserve native IDs and reference syntax. For attachments, distinguish
an asset URL, a local Codex file, and a path on the kernel server. Import/export
paths are server-side where the schema says so; do not pretend a desktop path
exists in the NAS container. Docker may lack desktop document converters.
Report that native limitation rather than install a converter by implication.

Internal SiYuan Skills run in the SiYuan Agent environment, with its workspace
and resource paths. Native list/load can expose them as source evidence. Native
install/save/remove/rename are explicit management actions. Reading a remote
Skill never installs it into Codex, executes its scripts, or makes it trusted.
Codex/Pennix Skills are maintained and published by their source owner and the
system skill installer. The two collections have distinct locations and owners.

History restoration, deletion, notebook administration, remote URL fetches,
network/system functions and Skill installation need relevant explicit intent
and a known target. Do not test destructive administration on real notes.
Use native export and restore when requested; export success is not proof that
all attachments or formats round-trip. Verify the requested observable result.
