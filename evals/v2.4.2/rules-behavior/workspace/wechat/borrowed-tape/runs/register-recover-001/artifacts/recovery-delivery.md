# 《借出去的卷尺》登记与恢复结果

已把现有候选逐字登记为 article-draft-0.2 / v0.2，状态为 draft，based_on 指向 article-draft-0.1。没有改正文，没有建立 accepted 或作者接受决定。候选和登记正文的实际 SHA-256 均为 `1261ec6189d890315e779aa0bcd257768b90de8f20b56ea716e83a3d62a80b10`。

登记前有 1 条正文记录，登记后有 2 条。原 v0.1 条目逐字段不变、原正文哈希不变；唯一新增条目的项目、article 范围、版本、状态、前版和 SHA 均符合本次合成请求。存在一条相应 register 事件，事件中的 revision_id、artifact_id 和 SHA 与新增条目相符，未用直接手改登记文件代替登记。

实际依次调用 register、verify、run resume、workspace resume、validate。workspace 恢复的 latest_text 为 article-draft-0.2；当时 active run 仍是原登记任务的 review 阶段，固定输入里保留 v0.1 的旧基准。当前内容和当前任务的历史输入是两个视图，不能把最新正文覆盖进旧输入。

verify 唯一报告的是 project 来源“版本记录/revisions.json”的 drift，snapshot_usable=true。逐一对账后可解释为这次正常追加：所有旧条目未变，新增行恰有一条且有真实登记事件；所有锁定快照、run 清单与旧正文仍匹配起始哈希。没有正文、规则或方法的其他漂移。因此它不等于快照损坏，也不表示所有 drift 都可自动忽略，更不表示最新稿已获批准。

登记前的 pre-registration-review.json 如实记录尚未完成登记/恢复，task_result=in_progress；没有回填成完成。现在另存完成记录并结束这次任务，原审阅、快照和旧事件不改。后续若要改稿，从 v0.2 另开新任务；这次完成不自动启动下一轮。

本任务只要求登记与恢复，稿件文学质量 not_assessed。对原版和候选的差异只用于核对选定版本，未据此宣称候选更好。权限来自合成操作请求，不代表真人作者审美采纳。未发生网络同步、多人并发或中断故障恢复；这些不在本次测试范围。
