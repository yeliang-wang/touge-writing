# CLI 参考 · v2.4

在项目根运行，核心 Python 3.9+。`--help` 显示当前参数，所有路径使用自己的本地目录。脚本不调用模型、不自动连接账号。下例显式使用推荐外部工作区；自定义时替换全部相关路径。脚本省略 --workspace 仍沿用当前终端目录下的 workspace，没有全局配置或自动回退。

## 内容与章身份

```bash
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" init --id demo --title "合成小说" --type novel
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" set-chapters --project demo --file chapters.json
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" resume --project demo --chapter scene-a
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" validate --project demo
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" rebuild-state --project demo
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" search --project demo --query "事件关键词"
```

以下 chapters.json、draft.md、request.json 等为需自行准备的私人输入示例；实际任务保存到所选 workspace 并传入相应路径，不把真实稿件保存进公共源。resume 返回 workspace 与 project_path，可确认正在操作哪个目录。

chapters.json 为 `[{"id":"scene-a","title":"第一场"}]`。search 默认现行内容，加 --history 包括历史；不会搜索其他作品。

```bash
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" add-revision --project demo --source draft.md --id scene-a-draft-1 --kind text --version 0.1 --status draft --chapter scene-a
```

kind：book_plan/chapter_plan/text/review；status：draft/accepted/baseline/historical。chapter_plan 用 --parent-plan 指向已接受全书方案，小说 accepted text 指向同章已接受章方案。--based-on 指同类同章前版本。accepted 必须带 --decision-file 实际作者决定；工具复制留档，不替作者作决定。

有适用规则的新稿登记增加 `--rules-review review.json --rules-mode draft`，保存实际审阅与规则上下文；允许登记候选不等于宣布满足规则。历史记录不追溯补造证据。

## 作品规则

```bash
python3 scripts/writing_rules.py --workspace "$HOME/.touge-writing/workspace" --project demo resolve --target scene-a --mode draft
python3 scripts/writing_rules.py --workspace "$HOME/.touge-writing/workspace" --project demo check --target scene-a --mode draft
python3 scripts/writing_rules.py --workspace "$HOME/.touge-writing/workspace" --project demo review --target scene-a --mode draft --review review.json --artifacts artifacts.json
```

`--target` 使用稳定章节 ID、book 或 article；`--mode` 按实际 trial/plan/draft/revise/review/title/deliver 选择。artifacts 文件列出作品内相对 path、产物 id 和实际 sha256。解析和检查不会代替读取正文或文学审阅，完整字段见 [规则执行](rules.md)。

## 素材与能力

```bash
python3 scripts/material_index.py search --manifest "$HOME/.touge-writing/workspace/corpus/manifest.jsonl" --query "事件 别名"
python3 scripts/material_index.py read --manifest "$HOME/.touge-writing/workspace/corpus/manifest.jsonl" --source-id source-1
python3 scripts/material_index.py map --project-path "$HOME/.touge-writing/workspace/novels/demo" --file mapping.json
python3 scripts/capability_catalog.py --select scene-design@1.0.0 --kind novel
python3 scripts/build_agent_context.py --scenario novel --phase review --out context.md
```

material_index 的 index/read/attest-read 详见 [素材](materials.md)。build_agent_context 支持旧 scenario/channel 参数和重复 --capability ID@版本；--phase 仅对 novel/wechat 选择公共组合，不包含私人作品。

## 运行与审稿

[run 使用示例](runs.md)覆盖 start/resume/artifact/stage/verify/register/rebuild/activate/resolve-issue。全局 --workspace、--project 位于子命令前。register 的 revision.json 示例：

```json
{"revision_id":"scene-a-draft-1","kind":"text","version":"0.1","status":"draft","chapter_id":"scene-a"}
```

可增加 parent_plan_id、based_on、decision_file；后者是作品内相对路径。规则审阅以 `review_id` 引用已保存的 run 审阅产物。source 由选定 run 产物固定，不能再指定别的文件。每次写入给稳定 operation-id，重试沿用，输入改变则换新操作。

```bash
python3 scripts/manuscript_check.py draft.md --out scan.json
```

只检查文字数量、逐字重复和标点/工作标记等线索。可选 --dash-limit 来自具体作品，不是公共审美配额。

## 私有 Git 候选协作

workspace 必须自身是独立 Git 根。命令不创建远端仓库、不推送、不创建 PR，也不自动登记或接受正文。以下示例中的提交 SHA、作品与文件须已存在：

```bash
python3 scripts/git_collaboration.py --workspace /path/to/private-workspace package --project demo --chapter scene-a --base <完整提交SHA> --file /path/to/local-process/draft.md --review /path/to/local-process/review.md --id candidate-1
python3 scripts/git_collaboration.py --workspace /path/to/private-workspace guard --base <完整提交SHA>
python3 scripts/git_collaboration.py --workspace /path/to/private-workspace verify --package contributions/candidate-1 --base <此次审阅确认的共同基准SHA>
```

`--file` 可重复，`--review` 可与正文同时或单独提供；至少选入一份内容。`--chapter article` 表示公众号，`book` 表示全书，其余值使用稳定章 ID。package 创建 `contributions/<id>/manifest.json` 与 `files/`，固定基准提交、登记文件哈希、相关方案和正文版本。manifest.sha256 用于完整性检查，不是作者身份签名。

guard 检查相对共同基准的分支、索引及工作树，允许完整的新候选包，拒绝修改正式登记、事件链或其他正式文件。verify 同时检查包完整性、当前基准及整个贡献变更集；可显式传 `--base` 核对期望基准。若基准变化，重新阅读并生成新包，不修改旧包绕过漂移检查。工具只读本地 Git，不执行 fetch，未拉取的远端变化不会被检测；主编须先取得并核对正式分支，再指定已确认基准。

主编整合沿用 add-revision，或在自己的 run 中 register；没有自动 integrate/accept 命令。贡献者个人运行在另一个本地过程副本，不能将其登记和链文件提交回正式分支。[完整流程](collaboration.md)

## 外部记录、备份与发行

external_operations.py 的 prepare/record 对已有作品和远端操作记账，参数以 --help 为准。它不执行网络调用，不保证服务幂等；submitted/unknown 要先对账再重试。[外部服务](external-services/README.md)

```bash
python3 scripts/backup_workspace.py create --workspace "$HOME/.touge-writing/workspace" --out "$HOME/.touge-writing/backups/snapshot.tar.gz"
python3 scripts/backup_workspace.py restore --archive "$HOME/.touge-writing/backups/snapshot.tar.gz" --destination "$HOME/.touge-writing/restores/snapshot"
python3 scripts/export_author_profile.py --out dist/touge-author-expression-1.0.0.zip
python3 scripts/build_release.py --out dist/touge-writing-2.4.1.zip
python3 scripts/acceptance.py --public-only
python3 scripts/acceptance.py --workspace "$HOME/.touge-writing/workspace"
```

备份没有应用层加密，需采用符合资料要求的存储。备份目录不能位于被备份目录内，恢复目标必须不存在。发行输出不能覆盖旧资产。普通使用者运行 public-only；维护者完整验收需要私人迁移和外部证据。[测试说明](testing.md)
