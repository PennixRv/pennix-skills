# Design

The root coordination task seals the cross-component architecture. This repository implements
only its Pennix Skill guidance and regression contracts:

- `pennix-workflow-routing` owns admission and cross-component owner/transport selection.
- `pennix-fastctx-routing` defines FastCtx's owner-first boundary and ordinary local default.
- `grok-search` states its executable's native launch ownership and the bounded post-hoc result
  analysis exception.
- `pennix-decision-gates` consumes the caller's classification; it does not create a second task
  lifecycle or classify every simple implementation as a gate.

No runtime enforcement is claimed. Existing Python static-contract test directories and the
current CI test discovery are reused. Lifecycle and Trellis remain their own owners and are not
modified by this component task.
