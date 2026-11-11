# 实施计划：远程 seed

1. [x] 检查当前 seed helper，提取模板解析、prompt、写入和 cleanup 的最小共享路径。
2. [x] 实现 local/remote asset resolver；remote mode 通过固定 raw HTTPS URL 获取两个模板，不执行下载代码。
3. [x] 实现 remote/pipe prompt fd：优先 `/dev/tty`，无 TTY 明确失败；保留本地测试输入路径。
4. [x] 增加测试：remote templates、pipe prompt、no tty、download failure、existing files、secret non-disclosure、
   local regression。
5. [x] 更新 README 和 SKILL.md，固定远程入口、Stage 0 结束条件、后续 lifecycle 入口和不负责的项目初始化。
6. [x] 运行 bash/Python/diff checks，提交 source task；不在本任务中直接推送 main，交由根任务完成快进发布。

## Verification

```bash
bash -n skills/pennix-workflow-lifecycle/scripts/seed-arch.sh
python3 -m unittest discover -s skills/pennix-workflow-lifecycle/tests -p 'test_*.py'
git diff --check
```

## Verification record

- `bash -n skills/pennix-workflow-lifecycle/scripts/seed-arch.sh`: passed。
- `python3 -m unittest discover -s skills/pennix-workflow-lifecycle/tests -p 'test_*.py'`: 74 tests passed。
- 远程 fixture 验证只获取两个静态模板；无 TTY 和下载失败均在 `pacman -Syu` 前失败；本地入口、幂等拒写和 secret non-disclosure 回归通过。
- `references/component-versions.json` 未修改，仍是组件版本和 ref 的唯一事实源。
