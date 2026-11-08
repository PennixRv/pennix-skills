# 组件实施设计

## 实施依据

完整设计与用户授权由根任务保存：`../.trellis/tasks/in_progress/11-08-native-questioning-agents-optimization/design.md`、`implementation-approval.md`。用户已批准完整 revision `4ad9ae36246d6169eac079ef4102fe99231e7684beaf7e4849a0db402d605183`。本组件仅落实其中 Skills 内容及评估，不修改 Lifecycle 模板或安装副本。

## 范围与取舍

主工作树 main，原生代理未暴露，inline 实施。只改 decision-grill、routing、Tavily 及必要引用和评估。现有来源身份、预算记录、结果摘要和认证 helper 复用；新增小型 app-server 客户端只承担真实协议往返，不封装宿主工具。

## 验证与交付

先检查合同和 collection，再测试真实问答协议及固定来源模型行为。固定源码提交推送后由根任务经 Lifecycle owner 物化，真实评估摘要可后续追加提交；失败不篡改旧证据。发布安装归 Lifecycle，原始 traces 不提交。

## 唯一停止点

本组件修改验证、固定来源交付及原生收尾完成，根任务完成实际安装和组合验收。必需模型或原生协议行为未验证则不声明修复完成。
