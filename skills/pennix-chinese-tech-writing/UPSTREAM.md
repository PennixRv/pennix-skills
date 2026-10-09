# Source and adaptation

- Upstream: [Fenng/Tech-Doc-Style-Chinese](https://github.com/Fenng/Tech-Doc-Style-Chinese).
- Reviewed commit: `b119d01c9bb7cd132b3c62fafdff34227c4410d1`.
- Original Skill name: `tech-doc-style-chinese`.
- License: MIT, Copyright (c) 2026 Fenng; the full notice is retained in [LICENSE](LICENSE).

`PennixRv/pennix-skills` maintains this adapted Skill as `pennix-chinese-tech-writing`. It is not an automatically synchronized upstream snapshot or a separate fork repository.

The four references derive from the fixed commit. Terminology guidance adapts quote and reader-address defaults, explains precise component names and customary English technical terms, and replaces the upstream paragraph-rewrite command with the native semantic-edit protocol. The entry is shortened and scoped to all Chinese technical content, including workflow rules, Trellis assets and SiYuan notes; it grants no persistence or lifecycle authority. The project-override reference remains an example, not an installed project policy.

`scripts/lint_copy_rules.py` and `tests/test_lint_copy_rules.py` retain upstream behavior. The standard-library helper is read-only; warnings and style advice require human review. Its upstream quote-style advice does not override this collection's usual Chinese quotation marks. The writable `unwrap_md_paragraphs.py`, upstream CI, and structural word-count tests are not imported.

For a future update, review upstream changes against this commit, preserve the license and local interface boundaries, test the read-only helper, and update this provenance record. Do not overwrite the adapted entry or project defaults automatically.
