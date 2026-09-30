# 作者能力模块 · 工作台 v2.0

本模块由公众号与小说 Skill 共同读取。入口是 [PROFILE.md](PROFILE.md)，独立包版本和哈希记录在 [manifest.json](manifest.json)，当前包版本为1.0.0。

| 文件 | 使用目的 |
|---|---|
| [judgment.md](judgment.md) | 判断方式、现实代价、立场形成 |
| [language.md](language.md) | 语气、句式节奏和表达偏好 |
| [lexicon.yaml](lexicon.yaml) | 习惯性用词及来源观察，不设使用配额 |
| [rubric.md](rubric.md) | 跨文体审阅原则 |
| [wechat-rubric.md](wechat-rubric.md) | 公众号评价维度，不能直接作为小说及格线 |
| [expression-evidence.md](expression-evidence.md) | 原有蒸馏统计和短例证 |

公众号用判断与论证组织内容；小说把声音落实到叙事距离、行动、对话和回望。复用声音不等于复用作者经历，也不把某本书的角色、年代或标点配额提升为全局规则。

## 独立分享

```bash
python3 scripts/export_author_profile.py --out dist/touge-author-expression-1.0.0.zip
```

在仓库根目录运行。包中只有清单允许的7份内容文件及 manifest，共8份；本 README、原始文章、书稿、回执和密钥均不在包内。固定内容产生可复现 ZIP，任何哈希变化都会阻止未经更新的导出。

本模块可作为其他宿主的风格资料；导入者先读 PROFILE，再按文体选择评价原则。它不是可执行 MCP 插件，也不自带私人语料检索服务。

## 更新

具体反馈先归属作品，稳定规则才考虑进入共享能力。记录证据、适用范围与作者决定；更新内容时同步独立版本和文件哈希，并复查导出器允许清单。作者统计是既有快照，本次文档升级不重新计算或改写来源证据。
