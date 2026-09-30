# v2.0 命令参考

所有示例从项目根目录运行。路径占位符必须替换为自己的私人文件；文中命令不会替代作者确认或外部服务授权。核心环境与可选依赖见[安装说明](installation.md)。

## 作品命令

入口为 `python3 scripts/writing_workspace.py`。全局参数 `--workspace` 默认为当前目录的 `workspace`，应放在子命令前。

| 子命令 | 必需参数 | 可选参数与结果 |
|---|---|---|
| `init` | `--id --title --type` | type 为 `novel` 或 `wechat`；建立独立作品 |
| `set-chapters` | `--project --file` | file 为带唯一 id/title 的章节 JSON 数组 |
| `resume` | `--project` | `--chapter` 指定章节；返回状态及需读取的全文路径 |
| `validate` | `--project` | 校验哈希、版本关系与确认依据；错误时非零退出 |
| `rebuild-state` | `--project` | 校验后从版本记录重建 state.json |
| `search` | `--project --query` | `--history` 加入登记历史；返回最多5条命中 |
| `add-revision` | `--project --source --id --kind --version --status` | `--chapter --parent-plan --based-on --decision-file` 按版本关系使用 |

`--project` 接受 catalog 中的 ID、标题或别名。新版本 ID 可包含字母、数字、点、下划线和连字符，必须以字母或数字开头；已使用 ID 不可重复。

合成小说的最小结构设置：

```bash
python3 scripts/writing_workspace.py init --id sample-book --title "示例小说" --type novel
python3 -c 'import json; from pathlib import Path; Path("workspace/sample-chapters.json").write_text(json.dumps([{"id":"ch01","title":"第一章"}], ensure_ascii=False))'
python3 scripts/writing_workspace.py set-chapters --project sample-book --file workspace/sample-chapters.json
python3 scripts/writing_workspace.py resume --project sample-book --chapter ch01
```

实际登记示例需先准备对应源文件和真实决定：

```bash
python3 scripts/writing_workspace.py add-revision --project sample-book --source /path/to/book-plan.md --id bp1 --kind book_plan --version 1.0 --status accepted --decision-file /path/to/author-decision.md
python3 scripts/writing_workspace.py add-revision --project sample-book --source /path/to/chapter-plan.md --id cp1-draft --kind chapter_plan --version 0.1 --status draft --chapter ch01 --parent-plan bp1
```

`kind` 为 book_plan/chapter_plan/text/review；`status` 为 draft/accepted/baseline/historical。新章方案要求已确认全书方案；小说正文定稿要求同章已确认章方案。确认草案时创建新的 accepted 条目，用 `--based-on` 指向草案，不能手工改写旧记录。

## 检索与提示词

| 脚本 | 参数与行为 |
|---|---|
| `private_retriever.py` | 必需 `--manifest --query`；`--top-k` 默认5；读文章 JSON 数组，返回 source_id、标题、URL、正文路径、分数和片段 |
| `build_robot_prompt.py` | 必需 `--mode --topic`；可选 `--manifest --top-k --draft --out`；只组装上下文，不调用模型 |
| `build_agent_context.py` | 可选 `--scenario --channel --agent-name --out`；无 out 时写标准输出 |

Prompt 模式：`write`、`rewrite`、`conversation`、`reboot`、`audit`、`titles`、`wechat_public_article`。能力注册表中的其他模式是 Skill 路由语义，不代表该 CLI 接受同名参数。

Agent 场景：`all`（默认）、`wechat`、`novel`、`writing`、`qa`、`audit`、`product_pm`、`evolution`。channel 为 `generic`（默认）、`feishu`、`wecom`、`docs`，仅改变集成说明，不建立对应连接。

```bash
python3 scripts/build_agent_context.py --scenario novel --out /tmp/touge-novel-context.md
python3 scripts/build_robot_prompt.py --mode wechat_public_article --topic "如何判断学习成本" --out /tmp/touge-article-prompt.md
python3 scripts/private_retriever.py --manifest /path/to/private/manifest.json --query "职业选择" --top-k 3
```

提供 `--out` 时先保证其父目录存在。组装结果可包含私人检索片段，应存入私人目录，不能直接作为公共发行物。

## 检查工具

```bash
python3 scripts/manuscript_check.py /path/to/draft.md --repeat-window 12 --dash-limit 1.5 --out /path/to/private/check.json
python3 scripts/style_eval.py /path/to/article.md
```

`manuscript_check.py` 的重复窗口至少4个中文字符，默认12；破折号阈值是每百中文字的数量，仅指定后才判断超限。字数/重复统计排除 `#` 和 `>` 开头行；结构词检查包含这些行，因此元信息可能产生待判断的命中。`facts_verified` 始终为 false。

`style_eval.py` 输出5个维度各0—3分，机械 `pass` 为总分至少11且没有命中的 AI 套话。它使用关键词启发式，不是作者偏好模型；退出成功只表示脚本运行完成。该阈值不适用于所有小说。

## 外部操作记录

`external_operations.py` 接收全局 `--workspace`（默认 workspace）和必需 `--project`，放在子命令前。它不调用 MCP。

```bash
python3 scripts/external_operations.py --project first-article prepare --service tencent-docs --account personal --action create --revision article-draft-1
```

`prepare` 必需 `--service --account --action --revision`；可选 `--remote-id --base-fingerprint`。当 action 为 `update` 时两者都必需。操作 ID 根据服务、账号、动作、本地版本/哈希、目标和预读指纹生成；重复意图返回 `retry_requires_reconciliation`。

`record` 必需 `--operation --status --evidence`，可选 `--remote-id`。状态允许 submitted/verified/failed/unknown/conflict。证据 JSON 至少有 source=live_mcp、service、operation_id、account_alias；verified 还要求 local_sha256 对应选定稿、remote_id 对应目标、readback_matches=true 和非空 response。调用宿主必须提供真实回执，不能按字段模板编造成功。

verified 回执保持不可变。超时后先查远端，不凭本地记录重新发送。平台版本条件或冲突检测由宿主实际调用完成，本地记录器不自动执行它们。

## 作者能力导出

```bash
python3 scripts/export_author_profile.py --out dist/touge-author-expression-1.0.0.zip
```

可选 `--profile` 指向能力目录，默认为仓库共享作者能力。导出器核对固定7份内容文件的清单与哈希，加上 manifest 共8份文件；拒绝未审阅清单、内容变化及覆盖已存在 ZIP。同版本同内容导出可复现。README 和私人工作区不会进入此包。

## 迁移、备份与恢复

```bash
python3 scripts/migrate_workspace.py --plan /path/to/private/migration-plan.json --workspace workspace
python3 scripts/migrate_workspace.py --workspace workspace --verify --check-sources
python3 scripts/backup_workspace.py create --workspace workspace --out /path/to/backups/writing.tar.gz
python3 scripts/backup_workspace.py restore --archive /path/to/backups/writing.tar.gz --destination /path/to/restored-workspace
```

迁移要求冻结清单和原来源仍可访问；`--verify` 可只校验目标，`--check-sources` 追加原件校验。备份输出必须在工作区外，归档旁产生 `.json` 凭证；恢复后产生 `.restore.json`。恢复拒绝覆盖现有目录，并逐文件验证内容。

## 私人资料导入与反馈

```bash
python3 scripts/ingest_corpus.py --source-type product_doc --source-id sample-docs --input /path/to/private/input --out-dir /path/to/private/normalized --tag product_qa --redact
python3 scripts/record_feedback.py --log /path/to/private/feedback.jsonl --task-id sample --mode write --prompt "示例任务" --output /path/to/private/draft.md --score 4 --notes "观点清楚" --revision-rule "保留具体代价"
```

导入支持 wechat_article/wecom_chat/feishu_chat/product_doc/meeting_note/feedback/draft。输入可为 Markdown、文本、JSON、JSONL、CSV 或含 Markdown/文本的目录。`--visibility` 默认为 private；`--tag` 可重复。清单追加到 JSONL，正文按 ID 写入 documents；这不是不可变版本库，保留原资料并避免把重复导入当迁移归档。`--redact` 是有限的模式替换，不保证彻底匿名化。输出 JSONL 不能直接传给文章检索器。

反馈分数为1—5。记录器只保存反馈及输出路径，不判断规则是否足够稳定，也不自动把反馈升级为作者规则。

`fetch_wechat_articles.py` 是可选公开链接抓取器，需要 `lxml`；参数为 `--index-json --out-dir`，可选 `--limit`（默认0，不限）和 `--sleep`（默认0.6秒）。输入对象的 records 中选取 record_type=article_standard 且有 standard_url 的记录。它不连接公众号后台，不构成公众号 MCP 验收，网页不可读时不能声称已取得正文。

## 平台配置、PPT 与发布检查

- `configure_tencent_docs.py`：无参数，在本机终端隐藏输入授权值，写入宿主配置；已存在同名配置时退出，不覆盖。详见[腾讯文档](external-services/tencent-docs.md)。
- `build_content_deck.py`：`--plan --out` 必需，可选 `--slug --estimate-only`。格式和输出见[PPT 功能](../references/content-deck-playbook.md)。
- `preflight_check.py`：检查公共文件、Git 索引、引用与评测覆盖；必须在 Git checkout 中运行。
- `acceptance.py --workspace workspace`：本次迁移的完整发布验收，需私人证据；不能在无私人数据的公共克隆中证明原迁移已完成。

参数拼写以脚本 `--help` 为准。未知作品、缺失来源、重复 ID、哈希冲突或缺少作者确认时，先处理具体错误，不通过改写清单伪造通过。
