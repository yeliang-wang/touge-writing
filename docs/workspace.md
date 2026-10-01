# 本地作品与内容版本 · v2.1

公共项目交付方法，workspace 保存实例。目录在首次 init 后建立，也可放在仓库外。默认结构：

```text
workspace/
  catalog.json
  corpus/                         明确授权的私人素材库，可选
  knowledge/                      私人候选方法，可选
  novels/<id>/ 或 wechat/<id>/
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
  archives/ reviews/              导入原件、历史与私人审阅
```

新建不会强制所有可选目录。来源、已接受文本、历史方案不可覆盖；修改新建版本。历史继承保持原事实，章方案不静默跟随新全书方案。accepted 需要实际作者决定，baseline 只表示已有可追溯旧稿，不保证符合现行方案。

## 当前任务与当前内容

resume 返回已确认规划、实际正文版本与节选、active_task、规则和未决事项位置。执行宿主继续读相关全文；节选不标全文已读，摘要仅在绑定内容哈希时用于恢复。指定章优先，其次活跃 run，再使用旧 next_action 建议。旧定稿的新修订不改变旧 accepted；新稿获得作者确认后再追加 accepted 版本。

章节 ID 是身份，列表排序和标题是展示；set-chapters 可调整顺序，但不能删除有历史版本的章节。材料清单里同号旧章不是当前章的自动别名，使用 [映射](materials.md)显式表达。

## 素材、方法与隐私

JSON 数组与 JSONL 清单现在都可交给 material_index.py 或 private_retriever.py，保留旧文件。只搜索明确选择的清单；新作品不默认读取旧作品。新素材的 allowed_uses/forbidden_uses 返回给宿主作使用约束，不把可读取当作可公开。

作者表达包可以独立导出；作品反馈先进入私人 knowledge 候选，经去事实抽象、合成验证和明确 review 后才能进入公共能力新版本。人物、时间、配额、书名和未公开事实不因此共享。

备份使用 backup_workspace.py，完整保留索引、历史和文件；归档在 workspace 之外。恢复只到不存在的新目录，先核验再采用。[迁移与回滚](migration-v2.1.md)
