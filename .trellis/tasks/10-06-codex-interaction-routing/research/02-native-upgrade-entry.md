# Native upgrade entry correction

Old installed lifecycle plus a staged new catalog was rejected with catalog template revision is invalid: codex-agents. Catalog validation checks adjacent templates; a new catalog cannot be injected into an older entry. The live collection was not replaced. Restored old AGENTS blocks through the old native install, then old native uninstall, validated staging's own native replace-staged, and installed new AGENTS through the new entry.

The staged entry prepares all post-install actions before atomic replacement and performs no later template read; its normal return confirms the transition. No cache/receipt bypass or adapter rewrite. Update lifecycle's existing recipe to call the validated staged entry and handle changed AGENTS blocks through old/new native owners. Final full collection installation will include this corrected recipe.
