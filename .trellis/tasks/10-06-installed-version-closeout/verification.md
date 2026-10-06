# Verification

2026-10-06。

- source catalog最小3行pin同步；原有test_lifecycle.py唯一beta30预期同步beta31，运行行为未改变。
- 既有lifecycle/collection安全回归：初轮130项唯一失败为旧beta30预期；修正后130项全部通过（5.512s）。
- source native集合校验：11项exact match；JSON catalog加载成功。git diff --check通过。
- Codex native marketplace add首次拒绝已存在different source；复核后native remove ponytail / add --ref v4.13.0成功。native owner适配器验证matching-ref，HEAD=08e952d7a8057a57ce561ff1330d093fd92eec67，已装plugin4.13.0 enabled。openai-api-curated原登记保持。没有手工修改缓存，没有降级/新增插件。
- 发布/安装/全量verify：待本工作提交推送后执行，结果按实际补充。
