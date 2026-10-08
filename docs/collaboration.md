# 合作写作 · v2.4

公开能力项目 `touge-writing` 与私人工作区独立维护。一个 `touge-writing-workspace` 可以保存多部小说与公众号单篇，单人可以独享。邀请协作者进入该仓库会允许其读取整个仓库的文件与 Git 历史；只共享部分作品时，为获准范围建立独立仓库，不依靠目录名称隔离权限。

## 约定共享资料与主编

将 [合作约定模板](../templates/collaboration.md) 填写后放在私人作品的决策记录中，明确作品 ID、共同方案、正式分支、主编、确认权限和允许分享的材料。主编顺序维护正式内容登记，其他人交付候选包。

| 保存位置 | 内容 |
|---|---|
| 公共能力仓库 | Skills、作者表达抽象、方法、模板、脚本与合成验证 |
| 私有作品仓库 | 选定作品、方案、正文、必要素材、历史、作者决定、正式内容登记、候选包 |
| 各人本地过程副本 | 个人 run、lifecycle、临时材料与未选入的候选 |
| 独立私人备份 | 完整原 workspace、未共享语料、大型归档及必要操作证据 |

源材料可读不等于可分享；只读范围与小说化权限继续有效。私有仓库不保存宿主凭据。目录规则只决定哪些文件入库，不是按章节授权的访问控制；写权限成员仍有能力绕过本地检查，因此需要实际审阅和适用的仓库保护设置。

## 从共同基准到候选包

1. **取得基准。** 更新私人仓库的正式分支，记录完整提交 SHA。读取当前作品索引、方案、正文和合作约定。分支名、最新时间及标题不能代替具体内容版本。
2. **隔离个人运行。** 从共同提交建立独立本地副本，并对整个写作任务使用该副本的 `--workspace`。若使用 run 或 add-revision，不在待提交候选的干净工作树中执行；个人生成的内容登记与事件链只留在过程副本。
3. **选入候选。** 在基于同一提交的干净贡献分支中，用 `git_collaboration.py package` 将已选正文和审稿复制为 `contributions/<id>/`。包内清单记录共同 Git 提交、作品登记与选用内容哈希。不要把过程副本整个复制回正式仓库。
4. **检查与提交。** 运行 `guard --base <共同提交>`，检查本分支、索引和工作树的变化只有完整的新候选包。查看实际差异，再提交分支或 PR。私人历史、凭据或不相关素材不能因文件选入成功就上传。
5. **主编审阅。** 先获取并核对远端正式分支的最新状态，再在最新正式版本上运行 `verify --package contributions/<id>`。如果方案、内容登记或正文已偏离包的基准，先保留差异并重新协商，不能把旧输入的结果自动当成当前稿。
6. **顺序登记。** 主编按实际审阅结果使用 `writing_workspace.py add-revision` 或自己的 `writing_run.py register` 登记新 draft。只有实际有权确认者明确接受该精确版本，才引用该决定登记 accepted。小说继承已确认章方案的要求不变。

主编整合时可以新建自己的 run，并把候选包列为输入。其他人的完整 run 与 lifecycle 不是可接续事件，不能用 Git 行合并、重新编号或改校验值拼接；这会伪造执行历史。

## 命令示例

在能力项目根执行。以下假定私有仓库已经有 `demo` 作品和 `scene-a` 章，候选文件与审稿已经在过程副本生成；使用前替换示例目录和基准提交。

```bash
python3 scripts/git_collaboration.py --workspace /path/to/private-workspace package --project demo --chapter scene-a --base <完整提交SHA> --file /path/to/local-process/draft.md --review /path/to/local-process/review.md --id scene-a-candidate-1
python3 scripts/git_collaboration.py --workspace /path/to/private-workspace guard --base <完整提交SHA>
python3 scripts/git_collaboration.py --workspace /path/to/private-workspace verify --package contributions/scene-a-candidate-1 --base <此次审阅确认的共同基准SHA>
```

`package` 只创建候选包；不会执行 Git commit、push、PR 或内容登记。需要多个候选文件可重复 `--file`。公众号使用 `--chapter article`，全书使用 `--chapter book`。传入的 workspace 必须本身是独立 Git 根，不能指向公共能力仓库的子目录。guard/verify 只读取本地 Git，不执行 fetch，也不能发现尚未拉取的远端提交。主编应先获取远端状态，verify 时用 `--base` 明确本次已核对的共同基准。参数详见 [CLI](cli.md)。

## 冲突、确认与恢复

候选包的通过只证明所检查文件、引用和基准符合约定，不证明文字正确、来源授权有效或作者已经接受。PR 可以合并一个待审包，accepted 仍由 `版本记录/revisions.json` 和实际决定确定。正式登记采用一个主编顺序写入，避免两人各自生成互不相容的版本历史。

如果远端比预期更改了，先获取并审查差异，不强制推送覆盖。自己的未提交文件先完整保存，不为通过 guard 删除过程记录。新基准需要重新阅读和审阅，按新提交生成另一个候选包；保留旧包的身份和历史。Git 拉取和克隆恢复共同内容，本地未入库文件须通过独立备份恢复。

## 腾讯文档与隐私

腾讯文档可以继续用于获准的资料导入、外部审稿、导出阅读或历史存档；选择 Git 作为正式存储后，在作品约定中明确哪个仓库是共同来源，不再维护第二份自动定稿入口。导入云端编辑先保存快照和差异，再按同一审阅与登记过程处理。[连接说明](external-services/tencent-docs.md)

Git/GitHub CLI 已能完成上述版本协作，不要求 GitHub MCP。GitHub Private 是访问控制，不是只有作者持钥的端到端加密；对平台也不可见的内容需要另行选择合适的存储。工作区和备份没有应用层加密。

合成双克隆演练用于验证基准、候选边界、冲突和登记行为。它不代表真实协作者账号已邀请或多账号并发验收。[验证范围](testing.md)
