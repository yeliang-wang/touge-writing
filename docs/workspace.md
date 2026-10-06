# 私人作品与内容版本 · v2.3

公共项目交付方法和模板，workspace 保存私人创作实例。workspace 可以单机使用，或作为独立私有 Git 仓库；不放入公共能力仓库。推荐位置为 `~/.touge-writing/workspace/`，通过现有 `--workspace` 显式传入。下文的 workspace 均指本次选定目录；旧 CLI 省略参数仍使用当前终端目录下的 workspace。

```text
~/.touge-writing/
  workspace/
    catalog.json
    README.md                       私有仓库入口，建仓时补充
    contributions/                  Git 协作候选包，按需创建
    corpus/                         明确授权的私人素材库，可选
    knowledge/                      私人候选方法，可选
    novels/<id>/ 或 wechat/<id>/
      START-HERE.md
      book.yaml                     JSON 编码的兼容元数据
      版本记录/revisions.json         内容与继承的唯一登记
      版本记录/content/               不可覆盖版本
      决策记录/                       实际作者决定
      state.json                    从内容登记派生
      materials/                    读取证明和映射，按需创建
      runs/<id>/                    方法、输入快照、产物
      lifecycle/events/             顺序执行事件
      lifecycle/state.json          从事件派生
      外部操作记录/                  远端对象与去密钥回执
    archives/ reviews/              导入原件、历史与私人审阅，可选
  backups/                          备份在 workspace 之外
```

新建时只创建索引、元数据、空内容登记、派生状态和 START-HERE，可选目录按需建立。迁入的旧作品可以继续使用原中文目录结构；实际文件位置以 catalog 和 revisions 中的登记为准。

## 索引与文件格式

以下仅展示格式，初始化由工具完成，不应把示例索引覆盖到已有资料上：

```json
{
  "schema_version": 1,
  "projects": [
    {"id": "demo", "title": "我的小说", "type": "novel", "path": "novels/demo", "aliases": []}
  ]
}
```

id 是稳定身份，path 是 workspace 内相对路径；type 为 novel 或 wechat。同名和别名必须可明确解析。`book.yaml` 虽沿用扩展名，内容实际是 JSON：

```json
{
  "schema_version": 1,
  "id": "demo",
  "title": "我的小说",
  "type": "novel",
  "chapters": [{"id": "scene-a", "title": "第一场"}]
}
```

空内容登记为 `{"schema_version":1,"revisions":[]}`。通过 [add-revision](cli.md) 追加文本和方案，工具保存内容哈希、版本、继承与实际决定。不要直接手改 state 来把作品改成定稿。

来源、已接受文本、历史方案不可覆盖；修改新建版本。历史继承保持原事实，章方案不静默跟随新全书方案。accepted 需要实际作者决定，baseline 只表示已有可追溯旧稿，不保证符合现行方案。

## 当前任务与当前内容

resume 返回实际工作区位置、已确认规划、正文版本与节选、active_task、规则和未决事项位置。执行宿主继续读相关全文；节选不标全文已读，摘要仅在绑定内容哈希时用于恢复。指定章优先，其次活跃 run，再使用旧 next_action 建议。旧定稿的新修订不改变旧 accepted；新稿获得作者确认后再追加 accepted 版本。

章节 ID 是身份，列表排序和标题是展示；set-chapters 可调整顺序，但不能删除有历史版本的章节。材料清单里同号旧章不是当前章的自动别名，使用 [映射](materials.md) 显式表达。

## 素材、合作与隐私

JSON 数组与 JSONL 清单都可交给 material_index.py 或 private_retriever.py，保留旧文件。只搜索明确选择的清单；新作品不默认读取旧作品。allowed_uses/forbidden_uses 返回给宿主作使用约束，可读取不等于可公开。

作者表达包可以独立导出；作品反馈先进入私人 knowledge 候选，经去事实抽象、合成验证和明确 review 后才能进入公共能力新版本。人物、时间、配额、书名和未公开事实不因此共享。

私有仓库按作品或相同权限团队划分，在 [合作约定](../templates/collaboration.md) 中明确共享清单、正式分支、主编和确认权限。Git 成员可读取整个已上传范围及历史；不能靠目录划分实现按章保密。各人基于共同提交持有本地过程副本，候选包交回干净贡献分支；正式登记由主编顺序维护。个人运行链不合并，PR 合并不自动 accepted。[合作流程](collaboration.md)

工作区和备份均无应用层加密；需加密时使用系统磁盘加密或加密卷，`--workspace` 指向相应目录。GitHub 私有仓库、腾讯文档访问权限与本地存储加密是不同边界；本项目没有实现只有作者持钥的端到端加密。

## 备份与更新

backup_workspace.py 完整保留索引、历史和文件；归档放在 workspace 之外。恢复只到不存在的新目录，逐文件核验后采用。`.writing.lock` 是瞬时锁文件，不作为作品内容备份。更新公共能力项目不复制、重建或删除私人工作区。Git 只保存明确入库的内容，完整个人档案需单独备份。[私有 Git 迁移](migration-v2.3.md) · [旧外置迁移](migration-v2.2.md)


## 私有 Git 纳入范围

首次入库审阅文件内容及引用依赖，建立与实际共享范围一致的 `.gitignore`。可以纳入作品方案、各版正文、必要素材、历史决定、正式 revisions 与候选包。未选入的完整个人语料、大型历史归档、原始服务响应、临时文件、宿主配置及凭据继续留在独立私人存储。已跟踪文件不会因为新增忽略规则而从历史消失。

个人运行链默认不加入协作提交。迁移所保留的既有 run/历史属于已选档案；后续贡献者不能以其为理由上传自己的分叉事件链。不得为了让 clone 通过验证而伪造遗失事件、改写历史哈希或删除源文档。有效任务所需的缺失材料应补入获准内容或明确其本地读取方式。
