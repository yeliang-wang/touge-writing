# 写作运行记录 · v2.3

run 保存一次作者任务的方法、输入和结果。`版本记录/revisions.json` 仍是正文及方案 accepted 状态的唯一依据。宿主生成文字、执行审读和持有作者授权；脚本不会调用模型或自动确认文学质量。

## 开始与恢复

本页演示已用 init 创建、ID 为 demo 的公众号作品；小说任务另用稳定章 ID。所有命令显式使用同一个 workspace，继续已有作品无需重新 init。先将下面的 request.json、draft.md 和 review.json 保存为私人任务文件，使用时传入实际路径；这些命令展示一次已有输入的运行流程，不会替你生成正文和审读。复制 [请求模板](../templates/run-request.json)，填写真实任务和引用，所有私有输入使用作品目录内相对路径及 SHA-256。capabilities 必须写 `ID@版本`，不能浮动到 latest。

```bash
python3 scripts/writing_run.py --workspace "$HOME/.touge-writing/workspace" --project demo start --request request.json
python3 scripts/writing_run.py --workspace "$HOME/.touge-writing/workspace" --project demo resume
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" resume --project demo
```

`start` 锁定所选能力、Skill、生命周期定义、作者表达包以及明确列入的作品输入。复制为 run 内不可变快照。工具同时自动固定作品元数据、内容登记、当前全书方案及目标和相邻章的现行方案／文本；任务额外材料仍需显式列入 inputs。引用全文时把实际源文件列入 inputs；清单本身的快照不等于锁定清单中全部正文。model/configuration 不可得时记 unknown。摘要由宿主阅读后填写，脚本绑定其输入哈希，不自动认证理解。

章级 target 是已登记章节 ID；全书是 book；公众号是 article。inputs 应包含本轮实际继承的方案、当前文本、必要邻文和素材／映射。授权引用来自用户真实请求或已有决定；fiction_policy 中 scope 是本轮允许小说化的范围。open_issues 每项说明 impact 与 blocks_completion：局部未决不必阻断无关试写。

## 产物、审稿、阶段

```bash
python3 scripts/writing_run.py --workspace "$HOME/.touge-writing/workspace" --project demo artifact --run article-001 --operation-id save-text --source draft.md --id draft-1 --role text
python3 scripts/writing_run.py --workspace "$HOME/.touge-writing/workspace" --project demo stage --run article-001 --operation-id to-review --stage review --reason '已交付待审正文'
python3 scripts/writing_run.py --workspace "$HOME/.touge-writing/workspace" --project demo artifact --run article-001 --operation-id save-review --source review.json --id review-1 --role review
python3 scripts/writing_run.py --workspace "$HOME/.touge-writing/workspace" --project demo stage --run article-001 --operation-id finish --stage completed --reason '本次任务已交付并审读' --review-id review-1
```

review.json 参见 [模板](../templates/run-review.json)：scope、findings、result、unresolved_blockers、被审产物的 ID 与哈希。程序检查记录完整性和阻塞事项；评审文字必须由宿主实际阅读后填写。需要修订则 review → revise → review，增加新的产物 ID，保留失败稿与旧审稿。计划任务可 plan → review → completed；没有要求先写正文。完成不代表作者审美认可或平台发布。

## 采纳与幂等恢复

`register --artifact-id draft-1 --revision revision.json` 复用现有内容登记；revision.json 字段见 [CLI](cli.md)。本次 run 的产物只能登记到其章节范围。accepted 仍需作品内实际作者决定文件；脚本不能判断该记录是否真由作者作出，执行宿主须保证真实性。

同 run 同 operation-id 同输入重试返回已有记录；换输入报冲突。产物已复制但事件未落盘时核对哈希后继续。内容版本已登记而 run 事件未落盘时核对版本、正文、父方案和决定，补齐引用，避免第二份定稿。准备好的 start 中断可用原 request 重试。多个文件不具数据库事务保证。

`verify --run ID` 检查快照、产物和事件；对当前源的变化报告 drift，旧快照仍可审计，不自动换方法。`rebuild` 从事件重建 lifecycle/state.json；`writing_workspace.py rebuild-state` 从正文登记重建 state.json。`activate --run ID --operation-id ID` 显式恢复仍未完成的任务。完成任务的新修订应另开 run。

`resolve-issue --run ID --operation-id ID --issue-id ID --decision-ref 决策记录/resolve.md` 引用实际解决依据，不能凭检查通过把待核事实升级为真。

公共上下文导出只读公共文件。run 含私人作品与授权信息，不进入公共能力发行。迁移时可按范围保留既有历史，但新的个人运行过程默认只留本地。

## 合作输入

合作约定、本轮共同提交、方案、基准正文和确认依据均属于作品输入。按需将获准快照列入 inputs，不要无记录地更换正在执行任务的基准。

Git 协作时，在共同版本的独立本地过程副本中 start。正式贡献分支保持干净，只接收经选择的候选包；不要在其中生成个人 run、lifecycle 或 add-revision 结果。将产物作为 package 的明确输入即可，不能将整个过程副本同步回正式仓库。

事件链含顺序编号和前序校验，同一基准分叉的两条链不能按行合并、重新编号或重算校验后当作一条真实历史。主编核对候选包后在正式 workspace 顺序开启自己的 run 或直接 add-revision；候选来源作为输入引用。run completed、PR 合并和导入云端最新稿都不自动 accepted。详见 [合作流程](collaboration.md)。
