# Design

Keep the existing single-file lifecycle and native-owner adapters. The minimal
change is to make the existing probe and package operation paths understand the
catalog's declared replacement packages:

1. Parse the last version token from command output.
2. Read global npm inventory once per probe and report the package actually
   installed (`name` or a declared `replaces` entry).
3. Add a catalog `replaces` field for known owner migrations. During an
   explicit package install/upgrade, remove only a declared replacement through
   its matching native owner before installing the target. Refuse unknown
   package owners and unmanaged executable shadows.
4. Report package candidates during discovery without applying them.
5. Accept `configure`; reuse the current static adapter and keep native-owner
   configuration blocked.

No rollback database, daemon, second catalog, remote execution, or generic
package-manager abstraction is added.
