# Source and host delivery evidence

Approved root task `10-04-cognee-memory-base-removal`, main-session delivery.
Temporary native retirement commits: 34f5c2f (138 tests), 430178e (139), be00042
(140). Completed project/config/profile/plugin/marketplace removal before
deleting the adapters. Orphan hook state and plugin cache were removed through
their owners; no manual cache edits. Other host configuration remains intact.

The current source deletes the dedicated skill, deployment assets, client,
ingress, plugin adapter, configuration targets and catalog entries. Routing and
guidance use local task/files and owner protocols. New handoff schema 9 uses
the local path. Schema 8 core/prompt/receipt are read-only audit inputs; no
remote writer, admission, ownership or retention mutation remains for them.

Catalog removal from an installed Skills tree is accepted only with the prior
private integrity receipt and valid Skill entries. A modified or unknown tree
is refused; the regression verifies preservation on rejection.

Windsurf source guidance was fixed in its own task and pushed at
9409047e167873ab7de49cb45884cc5dd4907321. No CLI behavior changed. Its official
consumer-package builder supplies the exact 18-file npm-pack snapshot, SHA-256
ca41841e856d5880f154df8623be37b75bebefd67f7b1220dff3048d40b333bd.
The collection provenance pins this source, without claiming a new npm CLI
release. Source offline tests 114/114, 18-file provenance and pack checks passed.

Final source checks passed again: lifecycle 127 tests, local handoff 26 tests,
Skill validation, and `git diff --check`. The historical schema-8 extension is
opaque and receives generic read-only status; active source no longer names or
interprets a retired product. Trellis beta.29 is published by successful Actions
run `37180148626`.

The immutable Pennix source commit `3148e18b0d7b1dc5437594abb0091b544319efda`
was pushed and used as the exact input to the official installer staging flow.
Native `replace-staged` completed with `status=changed`; fresh component verify
reports `match`, no missing Skills, no staging candidates, and no failures or
advisories. The installed handoff suite passes 26/26 tests, and an active-content
scan of the installed collection finds no retired base/provider entities.

All seven project roots have been natively updated and verified. The root task
records overall acceptance; this owner task is ready to archive after its
acceptance checklist. Historical task records and Git history remain unchanged.
