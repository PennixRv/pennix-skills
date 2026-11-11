# Verification

2026-10-06。

- source catalog最小3行pin同步；原有test_lifecycle.py唯一beta30预期同步beta31，运行行为未改变。
- 既有lifecycle/collection安全回归：初轮130项唯一失败为旧beta30预期；修正后130项全部通过（5.512s）。
- source native集合校验：11项exact match；JSON catalog加载成功。git diff --check通过。
- Codex native marketplace add首次拒绝已存在different source；复核后native remove ponytail / add --ref v4.13.0成功。native owner适配器验证matching-ref，HEAD=08e952d7a8057a57ce561ff1330d093fd92eec67，已装plugin4.13.0 enabled。openai-api-curated原登记保持。没有手工修改缓存，没有降级/新增插件。
- 功能/source发行提交f6d6afa378548c7f40e665af62a3a253f3182bc4已推送origin/main；首次网络连接超时，随后只读远端确认旧HEAD，限时重试成功；installer前ls-remote再次确认远端OID。
- system skill-installer --method git --ref该不可变OID、catalog唯一11项paths、全新同级staging全部成功。native validate_staged_collection match；134个受跟踪文件字节一致，7个可执行文件权限保留。
- native lifecycle replace-staged changed，grok-search-runtime依合同安装；npm报告同一项既有undici high，根原任务已记录其来源/边界，本轮不改独立上游依赖或自动audit fix。
- 已安装集合full verify：2026-10-06T02:32:21.327107Z，14项component全部match，scope full，failures/advisories空，staging none；siyuan-connection enabled/configured保持。配置认证/trust未编辑。
- 根offline runner8/8 passed；native SiYuan system.version3.8.6、Penn metadata匹配，plugin/ref适配器matching-ref，其他marketplace不变。
- 最后按native task归档与journal收敛，不发行新Trellis/npm版本，不创建分支。
