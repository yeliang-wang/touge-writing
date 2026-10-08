# v2.4.1 独立 Agent 前向行为评估

本次三项合成请求均已交付，结果为 passed。执行者是产品实现之外的 Agent；语义审阅为同一执行 Agent 的 self_review。测试输入由主任务提供，不是盲测，也不表示真人作者批准。所有故事、人物和正文均为合成材料，真实私人工作区未读、未改。

本目录是选定合成证据包，不是完整 workspace 备份。实际命令显式使用 `<EVAL>/workspace`；`<PUBLIC>` 指公共仓库根，`<EVAL>` 指本目录。回执中的机器绝对路径已替换，正文与登记文件的实际字节未替换。没有改动公共 Skill、方法或实现代码，没有 commit、push 或外部发布。

| 案例 | 可读交付 | 差异与审阅 | 结果 |
|---|---|---|---|
| novel-expansion | [最终候选全文](workspace/novels/night-catalog/outputs/candidate-v2.md) | [原稿到候选差异](workspace/novels/night-catalog/outputs/final-change.diff) · [语义自审](workspace/novels/night-catalog/outputs/review-final.md) · [材料映射](workspace/novels/night-catalog/outputs/source-map.md) | passed |
| wechat-rhythm | [候选全文](workspace/wechat/risk-table/outputs/candidate.md) | [差异](workspace/wechat/risk-table/outputs/change.diff) · [轻量自审](workspace/wechat/risk-table/outputs/review-final.md) | passed |
| draft-confirmation | [当前清单](workspace/wechat/rain-shelter/当前清单.md) | [阶段决定](workspace/wechat/rain-shelter/决策记录/draft-milestone-article-draft-1.0.md) · [前后核验](evidence/rain-shelter/confirmation-verification.json) · [执行说明](workspace/wechat/rain-shelter/outputs/review-confirmation.md) | passed |

小说补足工作量习惯、系统缺项、铅笔记录、当夜留未决及次日核对的后果；没有补对白、分钟数或责任人，保留主体与事件顺序。结尾两点收获是这份请求的具体要求，不是公共章节模板。原稿的“当夜补好位置”按补充材料改为“当夜留待复核，次日补备注”。邻章只提供末尾节选，本轮只核对这个节选的衔接。

小说不是一次生成就宣布合格。首稿 [candidate.md](workspace/novels/night-catalog/outputs/candidate.md) 的机械扫描未发现告警，实际自审仍发现两处把未提供的后续做法说成事实；[首轮审阅](workspace/novels/night-catalog/outputs/review-v1.json) 保留 needs_revision，后续 [v1→v2 差异](workspace/novels/night-catalog/outputs/revision-v1-v2.diff) 删除这些断言。最终只完成 run，没有登记候选。

公众号候选只删除两句重复说理，按周会、会后、次日、现在回望分段。其余非空白文字与原稿一致，指定尾句逐字保留；没有扩写事实、强插编号教程或建立完整 run。小说与公众号的正式正文登记前后均为空。

确认案例先用现有 CLI 建立唯一 article-draft-1.0 / v1.0 draft，再读取实际登记和正文，保存绑定该 ID 与 SHA-256 的“初稿完成，待精修”合成决定。正文与 revisions.json 字节未变，登记数量仍为 1，状态仍是 draft；当前清单计 81 个汉字、2 段。当前 CLI 没有里程碑专用命令，此次由宿主依 Skill 保存决定和清单，未伪造 CLI 功能或作者 accepted。内容质量为 not_assessed。

实际调用见 [transcript.jsonl](transcript.jsonl)，原输入保护见 [protected-files-verification.json](protected-files-verification.json)。[统计](descriptive-statistics.json) 仅描述变化，不参与文学质量判定。公共 Skill、方法、配置及关键脚本的评估前后哈希一致，见 [起始清单](evaluated-files-start.json) 和 [最终清单](evaluated-files-final.json)。

## 限制

- 这是三项指定合成任务的前向执行与自审，不是第二位文学评审、盲测、真人读者测试或全部能力矩阵。
- 输入来源可追溯不等于真实历史核实；作者后来可能不喜欢候选。本轮 author_approval_claimed=false。
- 小说 run 的完整输入快照在本地真实生成并通过 verify；选定证据包不分发 `runs/*/inputs/` 公共方法副本，保留 run 清单里的路径与哈希、事件及实际 verify 回执。仅凭此包不能重放完整 run。
- 只确认合成初稿阶段，没有精修其正文。未进行公众号账号、腾讯文档、Runtime 或其他外部服务操作。
- 初始 shell 沙箱因预配置的符号链接可写根而未能创建进程，随后在已授权合成范围内使用提升执行；没有因此改动宿主配置。

[result.json](result.json) 将所有选入证据的实际 SHA-256 与当前被评估文件绑定；结果清单自身不自引用。旧 v2.4 仅供格式参考，未复用其候选、判断或执行产物。
