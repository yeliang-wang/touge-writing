---
name: touge-writing
description: 为头哥的写作任务选择公众号文章或长篇小说工作流，复用作者风格；兼容原有交流、复盘、产品问答与内容交付请求。
---

# 头哥写作 · v2.4.2

从用户的作品和任务开始，按需读取一个入口：

| 请求 | 入口 |
|---|---|
| 公众号、推文、单篇文章、文章改写 | [.agents/skills/touge-wechat-writing/SKILL.md](.agents/skills/touge-wechat-writing/SKILL.md) |
| 小说、写书、连载、篇章方案、章节修改 | [.agents/skills/touge-novel-writing/SKILL.md](.agents/skills/touge-novel-writing/SKILL.md) |
| 像不像作者、风格审稿 | [作者能力](shared/author-expression/PROFILE.md)及对应文体评价标准 |
| PPT、讲稿、内容交付包 | [原内容交付方法](references/content-deck-playbook.md) |
| 职业、技术、组织交流 | [交流方法](references/conversation-persona.md) |
| 复盘、低谷与状态重启 | [复盘方法](references/reboot-protocol.md) |
| 产品经理问答 | [产品问答方法](references/product-manager-capability.md) |
| 接入其他 Agent | [嵌入约定](references/agent-integration-spec.md) |

作品名称与旧专家别名在本轮明确工作区的 `catalog.json` 解析。推荐 `~/.touge-writing/workspace`，每次命令显式传入 `--workspace`；旧 CLI 默认值不变。首次切换检查旧目录，遵守已确认迁移去向，不自动回退或合并。使用者没有指定作品且存在多个候选时，先澄清作品，不混合人物与事实。

作者资料只有一份：[PROFILE.md](shared/author-expression/PROFILE.md)。作品存放在私有 workspace。Codex 提供文件与 MCP 工具，Skill 只规定方法和使用约定。已确认的正文及历史方案保留原样，后续修改产生新版本。

`touge-writing` 是公共能力项目；统一私有工作区可命名为 `touge-writing-workspace`，同时保存多部小说和公众号单篇。按 catalog 中的作品 ID 路由，不把工作区仓库名称当作唯一作品。跨作品素材使用仍须明确范围。

原有命令见 [docs/GUIDE](docs/GUIDE)；外部服务使用说明见 [docs/external-services/adding-service.md](docs/external-services/adding-service.md)。

方法使用 [13 项原子能力](capabilities/README.md)；有状态任务按 [运行记录](docs/runs.md)固定版本，既有辅助入口与命令保留。

写作与审阅先恢复作品的规则入口和明确继承，阅读全文后再确定本轮适用项；方案说明落点，写后按规则记录证据、缺口与例外。具体格式见 [规则执行](docs/rules.md)。快照不证明理解，候选保存与任务完成不证明稿件合格；accepted 仍需实际作者决定。小型修改可用轻量核对，不为了规则检查强制创建 run。

合作或存储迁移时读 [合作流程](docs/collaboration.md)。公共能力仓库与私有作品仓库独立；贡献者从共同提交在本地副本写作，只提交选定候选包。主编顺序登记，个人运行链不合并，PR 合并不等于 accepted。腾讯文档为可选导入/导出与历史入口。

扩写、节奏修改和初稿确认按当前请求分别处理。新材料必须有依据，段落随动作和认识变化组织；篇幅统计不替代通读。未改正文的初稿确认绑定既有版本与哈希，不重复登记或自动转为 accepted。详见对应 Skill 与[规则执行](docs/rules.md)。
