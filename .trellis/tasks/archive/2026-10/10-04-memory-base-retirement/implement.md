# Owner execution

1. Test and commit the native retirement fix while the old catalog is available.
2. Execute exact project unregister and plugin/configuration uninstall; native inventory readback.
3. Remove active integration, convert handoff contracts and update routing/catalog/tests.
4. Run lifecycle and handoff regression suites, inspect diff, commit and push `main`.
5. Use system skill-installer staging/native collection replacement; verify source/installed integrity and report to root task.

User approval covers these steps through the sealed root task. Static rollback is a source revert; no automatic restoration of the retired service or credentials.
