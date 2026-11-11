# Design

The existing installer already discovers each direct `skills/<name>/` folder
and atomically replaces the deployed collection root. No installer code change
is required: deleting the retired folder and adding the new folder is enough
to remove and add the deployed Skills together.

`pennix-trellis-setup` is a thin user-level routing entry. Native Trellis
continues to own initialization, managed `AGENTS.md` merging, template update,
and workflow selection. The task-recording instruction moves to the Trellis
bundled layer because it is meaningful only after a project has Trellis task
state.
