# 小说协作演练结果

结论：本场景通过。独立执行 Agent 按当前 Skill 恢复指定工作区，交付可读的新片段，并在共享待审稿发生变化时保留本地候选、停止准备覆盖。

`synthetic=true`。未调用网络、真实 MCP 或真实账号；没有真实作者接受，不代表真实双人腾讯文档并发已经验证。

## 实际观察

- 先冻结 10 份输入，再通过真实 CLI 建立两份同名 `ferry` 作品；每条命令显式指定 workspace，执行目录另在两份目录之外。
- 甲方恢复结果指向 `case-a`，已读完整 book-v1、night-plan-v1、night-text-v1。章方案继承 book-v1，正文继承 night-plan-v1。
- 新片段 `night-candidate-v2` 登记为 draft，基于 night-text-v1，绑定 night-plan-v1。甲方 accepted 仍为 night-text-v1；乙方仍只有原来的三项已确认记录。
- 写前快照从“先喊一声”变为“是否先用灯示意”，哈希也改变。独立候选在重读之前已写成；没有把后来看到的建议伪称为其创作来源。差异和待汇总说明分别保存，未准备任何真实外部写入。
- 四段动作推进了船返回近岸、检查绳身和重新绑紧的状态；结束于重新出发之前。没有新乘客、死亡、真实私人经历或两位合作者的私人标记。本文只据合成方案核对任务范围，不作文学质量总评。
- 两方实际 `validate` 返回空错误；各自私人标记只在自己的合成 workspace 出现，已确认文件的 SHA-256 均匹配。冻结输入复核未变。

## 缺陷和边界

本场景没有发现阻断缺陷。冲突判断由 Agent 读取两个快照并交付差异实现，不是 CLI 或远端服务提供的原子比较交换。没有模拟或宣称消除预读之后的并发窗口；也没有伪造 `live_mcp` 回执。本片段的接受与最终汇总仍需青禾在合成场景后续作决定。

## 证据

`inputs/frozen.json`、`transcript.json`、`candidate.md`、`conflict.md`、`cloud-change.diff`、`evidence/observed-state.json` 和两方实际登记副本。`artifacts.json` 提供逐文件 SHA-256；父代理须另行核查，不以本结论替代其 review。
