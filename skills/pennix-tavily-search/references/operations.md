# Tavily Hikari 操作
通过 `tvly-hikari` 使用以下命令，不要手动设置 `TAVILY_API_KEY`。包装器将配置的 Hikari 来源映射到 `/api/tavily`，把 Hikari 访问令牌交给该门面，并由 Hikari 执行配额、审计日志和上游密钥池路由。
所有示例使用 `--json`。除非用户要求保存产物，否则将输出留在当前请求中。命令也可能提供 `--client-name` 用于下游请求归因；不要自动设置，因为它可能向第三方服务泄露用户、项目或 Agent 身份。
## 搜索

没有具体页面可读时使用搜索。

```bash
tvly-hikari search "current agent protocol changes" --json
tvly-hikari search "current agent protocol changes" \
  --depth advanced --max-results 8 --time-range month --topic news --json
tvly-hikari search "official API migration guide" \
  --include-domains example.com --exclude-domains forum.example.net --json
```

只选择相关控制项：

- `--depth ultra-fast|fast|basic|advanced` 和 `--max-results 0..20` 平衡覆盖范围与成本。
- `--topic general|news|finance`、`--time-range day|week|month|year`、`--start-date` 和 `--end-date` 表示时效限制。
- `--include-domains` 和 `--exclude-domains` 限定来源。已知直接官方 URL 时，优先使用该 URL 并 extract。
- `--include-answer`、`--include-images`、`--include-raw-content markdown|text` 和 `--chunks-per-source` 会增大响应；只有明显改善任务时才请求。

## 提取

已知一个或多个相关公共 URL 时使用 extract。确认每个 URL 都与请求直接相关；不要提取私有、无关或包含凭据的页面。

```bash
tvly-hikari extract https://example.com/article --json
tvly-hikari extract https://example.com/article \
  --query "migration steps" --chunks-per-source 3 --extract-depth advanced --format markdown --json
```

`--query` 会重新排序内容；`--chunks-per-source 1..5` 需要同时提供它。需要时使用 `--extract-depth basic|advanced`、`--format markdown|text`、`--include-images` 和 `--timeout 1..60`。只有用户要求或任务批准时才使用 `-o`。

## 映射

已知规范文档或网站根目录、但需要先发现其下 URL 时使用 map。

```bash
tvly-hikari map https://example.com/docs --json
tvly-hikari map https://example.com/docs \
  --instructions "Find API reference and migration guides" \
  --select-paths "/docs/.*" --max-depth 2 --limit 100 --no-external --json
```

使用 `--max-depth 1..5`、`--max-breadth`、`--limit`、`--select-paths`、`--exclude-paths`、`--select-domains` 和 `--exclude-domains` 明确范围。除非请求需要站外链接，否则传入 `--no-external`；`--allow-external` 会有意扩展目标范围。映射结果是下一条命令的候选，不是最终事实答案。

## 爬取

只有需要读取限定网站区域的多个页面时才使用 crawl。运行前定义起始 URL、较小的 `--limit`、所需深度或广度，并在网站范围不够窄时设置路径或域名过滤。

```bash
tvly-hikari crawl https://example.com/docs \
  --max-depth 2 --max-breadth 10 --limit 20 \
  --select-paths "/docs/.*" --no-external --json
```

命令还支持 `--instructions`、`--chunks-per-source`、`--extract-depth`、`--format`、`--include-images`、`--allow-external / --no-external`、`--timeout 10..150` 和输出控制。除非需要跨域链接，否则传入 `--no-external`。`--output-dir` 每页写入一个 Markdown 文件，只适用于明确要求或任务批准的产物目录。默认不要全站爬取。

## 调研

无法通过限定搜索和提取回答的多来源综合使用 research。问题应简洁包含范围、时间段、地域和来源限制。

```bash
tvly-hikari research "Compare current agent protocol support in official documentation" \
  --model auto --citation-format numbered --json
```

`--model mini|pro|auto`、`--stream`、`--output-schema`、`--citation-format`、`--poll-interval` 和 `--timeout` 控制官方调研请求。普通命令会等待限定结果；若有意使用 `--no-wait` 启动，仅在用户仍需要结果时使用官方单次后续命令：

```bash
tvly-hikari research status <request-id> --json
tvly-hikari research poll <request-id> --json
```

不要围绕这些命令实现手动轮询。只有任务批准需要产物时才使用 `-o` 保存，并保留引用、核验重要主张。

## 诊断与服务边界

只有 CLI 或配置错误后，或用户明确要求诊断就绪性时，才运行 `tvly-hikari doctor`。它检查本地包装器、配置和兼容的官方 CLI，但可能显示掩码配置字段；不要在消息或任务资产中重复这些字段。除非用户明确要求掩码诊断，否则不要运行 `tvly-hikari config show`。这两个命令都不核验来源事实，也不能替代实际检索。Hikari 请求使用配置的 `/api/tavily` 门面；令牌配额、审计日志和上游 API 密钥选择由 Hikari 服务负责。

## 与上游对齐

本参考合并 Tavily Hikari `best-practices`、`cli`、`search`、`extract`、`map`、`crawl` 和 `research` Skills 中各操作的说明。这是有意合并：七者共享一个已配置 CLI、令牌边界、JSON 输出约定和 Hikari 服务合同。`tavily-hikari` 入口只增加工作流路由、限定输出、来源核验和任务记录规则。

上游来源：

- <https://github.com/IvanLi-CN/tavily-hikari/tree/main/skills>
- <https://github.com/tavily-ai/tavily-cli>
