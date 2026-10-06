# 同步当前 CodeGraph 与 Ponytail 固定版本

## Goal

在 Pennix 唯一源码 owner 同步当前实际版本，再提交推送、按不可变提交安装完整集合。根协调任务为 `../.trellis/tasks/10-05-siyuan-knowledge-workflow-design`。本任务只收敛末轮发现的 catalog 漂移，不新增功能或依赖。

## Requirements

- 用户已授权完成全量更新与收尾；2026-10-06 再明确要求直接收尾。main 主会话 inline 实施，不建分支。
- CodeGraph CLI/原生包分别为 1.6.2 / codegraph-bin 1.6.2-1，当前 AUR candidate 一致；catalog approved_version 从1.6.1改为1.6.2。
- Ponytail已安装4.13.0；catalog approved_version/ref从4.12.0/v4.12.0改为4.13.0/v4.13.0。上游标签由git ls-remote核验为08e952d7a8057a57ce561ff1330d093fd92eec67；本机marketplace仍e15862b（旧4.12.0）。仅通过Codex原生marketplace add --ref刷新、必要时原生remove/add重登记这一来源；其他marketplace与插件保持。不手工修改缓存或编造tag。
- 最小源码差异为component-versions.json的两个版本和一个ref，以及既有catalog测试中仍固定beta30的过时预期同步到已经发布/安装的beta31。初轮130项检查唯一失败是该旧预期；仅更新原断言，不新增测试或改运行逻辑。运行既有lifecycle/collection检查。修改前读取owner规则及适用spec。
- 源码提交推送后，system skill-installer用不可变source OID、catalog唯一11项path及git方式暂存；验证frontmatter/seed执行位/集合，再native lifecycle replace-staged。全量verify须14项match且无failures；保留配置、私有receipt与可选SiYuan连接。
- Marketplace刷新失败则保留/恢复原生登记及原安装插件，不通过raw git操作修复。集合替换失败遵守native原子回滚，不修改消费副本。发生真实合同/权限/owner变化则replan。

## Acceptance Criteria

- [x] A1：两个版本和标签来源已核验，最小catalog修改及既有检查通过。
- [ ] A2：源码main提交推送；原生marketplace匹配v4.13.0及已安装4.13.0，其他登记不变。
- [ ] A3：不可变源的完整11项集合安装，全量verify14项match、无failures；根组合门禁通过。
- [ ] A4：receipt与源码/安装固定点记录，任务原生归档、journal和Git clean/同步。

## Planning Seal

2026-10-06 closed/sealed。实际目标、3行修改、原生登记/安装路径、失败回滚与验收固定；已有用户授权覆盖普通版本同步。轻量任务PRD-only足够，不需要设计新机制。执行先native validate/start，再作安装及源修改。
