# v2.4.2 独立 Skill 前向行为评估

三个新合成请求均完成，行为结果 passed。小说和公众号的稿件结论均为 needs_revision；审阅任务完成不等于正文合格。登记案例的文学质量 not_assessed，实际完成 draft 登记与恢复。

本轮由产品实现之外的 Agent 执行，按当前两份 Skill 及 editorial-review@1.0.2 阅读、操作和审阅；请求与素材由该评估 Agent 新构造，语义判断为 self_review，非盲测或第二位文学评审。没有读取真实私人工作区、改动真实稿件或复用旧版本的合成产物。

| 案例 | 原始请求 | 实际交付与主要证据 |
|---|---|---|
| novel-review-scope | [合写回忆录审阅请求](inputs/novel-request.md) | [审阅全文](workspace/novels/back-door/outputs/review.md) · [分句口径与比例](workspace/novels/back-door/outputs/scene-comparison.json) · [规则审阅](workspace/novels/back-door/outputs/rule-review.json) |
| wechat-body-scope | [公众号统计审阅请求](inputs/wechat-request.md) | [统计与审阅全文](workspace/wechat/kept-paper/outputs/review.md) · [explicit 统计](evidence/wechat-draft-explicit.json) · [本次重跑 legacy](evidence/wechat-draft-legacy.json) |
| registration-recovery | [登记与恢复请求](inputs/registration-request.md) | [实际恢复说明](workspace/wechat/borrowed-tape/outputs/recovery-review.md) · [登记追加对账](evidence/borrowed-tape/registration-reconciliation.json) · [最终 verify](evidence/borrowed-tape/verify-final.json) |

小说比较读取了两篇完整的短章，并将叙述者乔宁、素材整理者苏禾、执笔者陈岚、确认权限及尚未确定的正式署名分开。现稿正文 453 汉字，参考稿 260 汉字；按已说明的语义分类，现场分别为 147/453 和 150/260，未将铺垫和事后后果全部算作现场。审阅指出动机断言与摘记冲突、末尾重复和过满保证，给出位置、收益和损失；没有擅自改稿。

公众号正文选择 L7–L17 并排除 L11 编务段，含正文引用 40 字，总计 290 汉字。本次 legacy 得 322，原因包括漏引文又计入元数据；未将重跑结果说成排版人那次未知统计。工作标记扫描仍保留全文结果，但命中的两处属于编务，未当成正文泄漏。零逐字重复窗口没有掩盖实际语义重复。

登记案例使用真正的 run register 追加唯一 article-draft-0.2 draft，随后执行 verify、run resume、workspace resume 和 validate。旧条目、旧正文、run 清单、既有事件及全部快照哈希不变；新增条目、候选哈希和实际注册事件一致。verify 仍报告 revisions.json 源漂移，已据证据解释为正常追加，没有改写快照消除 drift，没有概括为所有漂移都可忽略。最终任务 completed，最新正文仍为 v0.2 draft。

[transcript.jsonl](transcript.jsonl) 保存实际 CLI 参数、退出码及输出；路径中的本机评估根和公共根分别如实替换为 `<EVAL>`、`<PUBLIC>`，明确属于路径脱敏，未改变统计、状态、哈希或行为结论。工作区是本目录下临时用途的隔离合成 workspace，每条工作区命令显式传相同 `--workspace`。未操作网络、发布或真实多人协作。

原输入及审阅稿保护见 [前后核验](protected-files-verification.json)。[起始文件绑定](evaluated-files-start.json) 与 [最终文件绑定](evaluated-files-final.json) 一致，覆盖两 Skill、关键脚本和配置要求的全部指导。结果由 [result.json](result.json) 绑定全部选入证据 SHA；哈希只证明版本和完整性，不证明理解、事实真伪或作者接受。

这是选定证据包，不是完整 workspace 备份。run 输入快照已在本地实际生成、核验，公共方法快照不重复分发在 `runs/*/inputs/` 中；run 清单保留来源与 SHA，实际 verify 回执保留。包中不含缓存和锁文件，不能仅凭此包重放完整 run。

限制：只检验本次三项请求；语义分类存在已说明的边界，不设通用比例门槛。未模拟中断故障、真实多账户、真实作者接受或外部服务操作。未执行公共整体验收或发布验证，D01–D06 由主任务另行完成。所有材料为合成设定，real_manuscripts_modified=false，author_approval_claimed=false。
