# WP1 执行记录

原生规划 revision 1 已按根任务同一真实批准 seal/approve/start；本次直接在 main 交付，未创建 PR，归档时使用原生 --skip-branch-validation，不伪造分支元数据。

四项已从 anthropics/skills@2c5958ecac7cee2b583967a2c4981d0f4a75c579 官方归档提取，共 182 个原始文件。各目录保留 LICENSE.txt、完整原始文件摘要及 UPSTREAM.md；本地改动限于 SKILL.md 和三个 soffice.py。上游根第三方声明已核对，Pillow 的 HPND 节保留在实际使用它的 PDF/PPTX 目录；未复制字体、FFmpeg 或 imageio 发行资产。

已完成中文发现、默认只读、公式/缓存区分、PDF 引用与空页示例、运行时 owner、唯一渲染目录和无 shim 的临时 profile。保留上游创建编辑方法；extra、全局规则和 Trellis 本体未变。

主集合 verify 为 19 Skills、2 commands；集合测试 15 项及评估驱动 19 项通过。新增来源/许可/LibreOffice 行为测试 2 项通过。五个文档发现用例复用原生评估入口，仅运行四格式及一个相邻反例；实际运行留待正式安装后由根任务执行。显式 smoke 脚本生成非敏感样例，包含正文表格、页序备注、公式缓存、中文 OCR、渲染和旧格式转换；不将尚未执行记为通过。

规范已在 backend/quality-guidelines.md 增补来源导入、只读和运行时合同。根只读组合初次 10/11 通过，唯一失败为尚未正式发布安装的 release alignment，符合当前实施断点，须在最终安装后重跑。

CI 所有 11 个逐 Skill 测试文件均已执行，共 108 项（其中 1 skipped）；初次发现 routing 测试只计算既有 scenario-positive，已补入四项 document-positive 的实际覆盖，重跑通过。新导入上游保留的原始文件包含空白告警；完整 staged diff --check 因这些原始字节返回 2，本地语义文件检查通过，不为消除告警改写已固定上游。
