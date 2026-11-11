# 新增 Trellis 项目更新 Skill

## Goal

实现面向任意 Trellis 项目的可重入更新 Skill：调用原生 Trellis 更新协议，锁定工作流来源，保护项目修改，完成验证并纳入发布安装清单。

## Requirements

- Add a single `pennix-trellis-project-update` Skill for maintaining an existing Trellis-managed project.
- Follow the current Pennix Trellis beta workflow and current fork CLI behavior, not a generic or copied updater.
- Keep native Trellis ownership, preserve project modifications, separate generated-asset updates from workflow selection, and make workflow source/ref/template and overwrite/migration decisions explicit.
- Make repeated runs safe and leave no silent branch/source switching, global installation, credential handling, runtime-state mutation, or second update protocol.
- Publish on `main` and support complete staged reinstall through the existing Pennix collection contract.

## Acceptance Criteria

- [ ] The Skill is valid and discoverable, and its trigger excludes system installation and read-only diagnosis.
- [ ] It uses the real native command paths and conflict flags of Trellis `0.7.0-beta.10`.
- [ ] It preserves the selected current workflow, including the latest Pennix inline/subnode/evidence contract, unless an explicit workflow decision says otherwise.
- [ ] It has focused contract coverage and passes the repository's validation/test commands.
- [ ] The source branch is clean and pushed; the installed collection is staged, receipt-validated, and verified.

## Notes

- Implementation target is this repository only. The root repository receives coordination evidence, not component source.
- The requested release and reinstall are part of this task's completion boundary.
