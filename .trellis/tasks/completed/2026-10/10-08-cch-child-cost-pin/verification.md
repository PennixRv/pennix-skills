# 质量门与发布依赖

- 唯一catalog CCH approved_version改0.1.44，native-owner安装策略不变，没有新增重复版本表。
- lifecycle unittest136 passed（5.452s），isolated fixtures均自行清理，故障注入负例输出不是实际部署失败。
- CCH官方Release v0.1.44/源码8208b760bc8df9e94ebb851489ace667cd62af7e、CI37679857891 success。集合重装与安装副本验收后追加。

- Pennix source `dc77084469771c6ffc9993a76e1d346b50bdd39e`普通push成功；system skill-installer --method git按catalog完整11 entries安装不可变commit到staging，exact collection/frontmatter/executable seed校验通过，static templates字节未变。
- staged原生replace-staged成功，安装集合receipt完整性match；新的scoped pennix-skills和cch-status verify均match且failures/advisories为空。CCH两个npm落点及managed runtime均0.1.44，配置/凭据/tmux外文不变。
- 本轮staging成功消费、无遗留，没有直接修改installed collection、receipt或私有配置。本任务是main上的direct catalog消费维护，无PR，native archive显式跳过PR分支验证。
