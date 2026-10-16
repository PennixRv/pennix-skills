# 来源与适配

本 Skill 是 `PennixRv/pennix-skills` 的本地综合适配，不是任何单一上游 Skill 的复制或自动同步快照。只采用下列来源中可迁移的方法事实；没有导入上游正文、脚本、图片、模板或评审运行时。

| 来源 | 固定提交 | 许可 | 本地采用 |
| --- | --- | --- | --- |
| [obra/superpowers verification-before-completion](https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/verification-before-completion/SKILL.md) | `bb92a77741419a4ab5f06e711a283343f1ada0c3` | MIT | 将完成断言与对应证据分开核验；不强制每条消息重跑全部检查 |
| [softaworks/agent-toolkit writing-clearly-and-concisely](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/writing-clearly-and-concisely/SKILL.md) | `3027f20f3181758385a1bb8c022d4041dfb4de84` | MIT | 采用一段一事、具体措辞、相关内容相邻和删除无贡献文字的方法 |
| [promptfoo llm-rubric](https://github.com/promptfoo/promptfoo/blob/132a2d38b1b0adc953b0db650f950d573bc113c4/site/docs/configuration/expected-outputs/model-graded/llm-rubric.md) | `132a2d38b1b0adc953b0db650f950d573bc113c4` | MIT | 采用按具体问题定义人工复核要求、保留理由和分开通过条件的方法；不引入评审模型 |
| [google/styleguide Markdown style](https://github.com/google/styleguide/blob/e257cb5e9247f7c55bec142c726ee47f6ff58720/docguide/style.md) | `e257cb5e9247f7c55bec142c726ee47f6ff58720` | CC BY 3.0 Unported | 采用链接、表格和视觉元素服务阅读目的的载体原则；不搬入 Gitiles 专属格式 |
| [github/awesome-copilot Markdown accessibility](https://github.com/github/awesome-copilot/blob/cb64ad12e32737ae764becd6885462e9b4c7cb00/instructions/markdown-accessibility.instructions.md) | `cb64ad12e32737ae764becd6885462e9b4c7cb00` | MIT | 采用明确链接、文字可读和重要信息不只依赖视觉装饰的检查 |
| [softaworks/agent-toolkit mermaid-diagrams](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/mermaid-diagrams/SKILL.md) | `3027f20f3181758385a1bb8c022d4041dfb4de84` | MIT | 采用按关系选择图型、单图聚焦和渐进参考的方法；不安装 CLI 或承诺宿主全语法支持 |
| [Mermaid documentation](https://github.com/mermaid-js/mermaid/tree/e28fbd9ded0a07ba9569e51be4764c1ad4daa8f6/packages/mermaid/src/docs) | `e28fbd9ded0a07ba9569e51be4764c1ad4daa8f6` | MIT | 采用流程、时序、状态和时间排期的概念区分；不以该版本文档证明 Paseo 当前 runtime 的完整能力 |

本地适配保留用户级中文技术写作 Skill 的语言、术语、保真和排版职责，保留 `pennix-decision-grill` 与 Trellis 对用户取舍、批准和生命周期的所有权。该 Skill 不控制任务状态、工具调用、安装、发布、凭据或持久化，也不引入模型评分器。

后续更新先重新核验固定提交、许可和方法边界，再修改本文件与入口；不得把新来源的流行度、宣传效果或宿主单次渲染结果写成质量证明。
