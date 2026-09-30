# v2.0 工作区与数据格式

面向需要理解或维护本地状态的使用者。`workspace/` 是运行后创建的私有目录，不是发行物；本页只展示合成结构。

```text
workspace/
  catalog.json
  novels/<id>/
    book.yaml
    state.json
    START-HERE.md
    版本记录/revisions.json
    版本记录/content/
    决策记录/
    外部操作记录/
  wechat/<id>/
  corpus/
  archives/
  acceptance/
```

`init` 只创建索引、作品元数据、空版本清单、状态及入口文件。章节正文、素材、人物时间线、语料、迁移归档等按使用过程增加，不会自动预填。迁移作品的目录名可以不同于 ID，通过 catalog 映射。

## 作品目录与元数据

```json
{"schema_version":1,"projects":[{"id":"my-novel","title":"我的小说","type":"novel","path":"novels/my-novel","aliases":[]}]}
```

作品定位精确匹配 `id`、`title` 或 `aliases`，必须恰好命中一个作品。路径相对所选工作区。新 ID 为小写字母开头的字母、数字、连字符组合。

`book.yaml` 实际以 JSON 编码，属于 YAML 的兼容子集；当前工具用 JSON 解析器读取，不接受任意 YAML 语法。文章也沿用这个文件名。

```json
{"schema_version":1,"id":"my-novel","title":"我的小说","type":"novel","chapters":[{"id":"ch01","title":"第一章"}]}
```

`set-chapters` 接收章节数组，要求唯一 ID 和标题，不能移除已有登记版本所属的章节。

## 版本记录

以下为结构示意，不是可伪造作者确认的输入：

```json
{
  "id":"chapter-draft-1","kind":"text","version":"0.1","status":"draft",
  "chapter_id":"ch01","parent_plan_id":"chapter-plan-approved-1","based_on":null,
  "path":"版本记录/content/chapter-draft-1.md","sha256":"<文件SHA-256>"
}
```

- `kind`：`book_plan`、`chapter_plan`、`text`、`review`。
- `status`：`draft`、`accepted`、`baseline`、`historical`。`baseline` 是可追溯旧稿，不表示符合当前方案。
- `parent_plan_id`：方案继承；`based_on`：同类型、同章节的前序版本。
- `accepted`：还需非空 `decision_path`。新登记条目同时记录 `decision_sha256`；部分迁移历史沿用已有决定文件。
- 正文和决定文件不可覆盖。清单按登记顺序推导现行条目，不按版本字符串排序。

小说正文定稿需要同章已确认方案；章方案需要已确认全书方案。`state.json` 是缓存，可重建。`next_action` 选择首个缺少确认正文的已配置章节；没有已配置章节时为 `null`，不等于全书内容已完成。

## 两种语料清单

| 格式 | 生产者 | 消费方式 |
|---|---|---|
| `manifest.json`，JSON 数组 | `fetch_wechat_articles.py` 或迁移整理 | `private_retriever.py` |
| `manifest.jsonl`，逐行记录 | `ingest_corpus.py` | 后续人工审阅或宿主自建检索；不能直接传给现有 retriever |

文章记录包含 `id`（推荐）、`title`、`url`、`publish_time`、`word_count`、`markdown`。相对 Markdown 路径以清单父目录解析，旧绝对路径仍兼容但不便搬迁。`word_count <= 0` 的记录不会被检索器当作正文；标签或空文件不能伪装成已读取素材。

导入 JSONL 包含 `source_id`、`source_type`、`text_path`、`text_hash` 等字段。两种格式字段不同，v2.0 没有自动转换器；如需接入，要先明确映射并核验正文路径与哈希。

## 档案与外部记录

迁移清单、原始副本、校验回执放在 `archives/`；源绝对路径只存在私人迁移记录中。当前作品的内容路径采用相对路径，搬迁后仍可恢复进度。

外部操作包含服务、账号别名、动作、选定版本、远端 ID、预读指纹、状态与证据引用。账号授权值不属于工作区数据。远端差异保存后再按具体任务处理，不能自动覆盖本地定稿。

已登记文件不可直接改写。文件锁和原子替换减少并发覆盖风险，但并非跨目录数据库事务；中断后的未登记文件应先核验，再决定是否重试登记。
