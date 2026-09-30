# 头哥写作工作台 · v2.0

在 Codex 中写公众号文章和长篇小说，共享从头哥公众号历史文章中蒸馏的判断方式、表达风格与习惯性用词。项目提供两类写作 Skill、可独立分享的作者能力，以及管理本地作品的文件工具。

| 能力 | 入口 | 用途 |
|---|---|---|
| 公众号写作（短篇、单篇） | [touge-wechat-writing](.agents/skills/touge-wechat-writing/README.md) | 选题、素材、结构、成稿、修改、审稿与发布准备 |
| 小说写作（长篇、连载） | [touge-novel-writing](.agents/skills/touge-novel-writing/README.md) | 全书与章节方案、版本继承、叙事连续性和进度恢复 |
| 共享作者能力 | [author-expression](shared/author-expression/README.md) | 判断方式、语言偏好、词库及不同文体的评价原则 |

旧入口 `touge-writing-reboot-skill` 保留路由，以及交流、Reboot、产品问答和内容交付包等[辅助能力](docs/auxiliary-guide.md)。

## 安装并创建本地作品

核心工具需要 macOS 或 Linux、Python 3.9+；Git 用于克隆与发布检查。PPT 和文章抓取的可选依赖见[安装说明](docs/installation.md)。

```bash
git clone --branch v2.0.0 https://github.com/yeliang-wang/touge-writing-reboot-skill.git
cd touge-writing-reboot-skill
python3 scripts/writing_workspace.py init --id my-novel --title "我的小说" --type novel
python3 scripts/writing_workspace.py resume --project my-novel
```

在 Codex 打开完整项目，可使用 `$touge-novel-writing` 或 `$touge-wechat-writing`，例如“为我的小说建立全书方案”或“根据这些材料写一篇公众号文章”。这些是安装后的使用任务，产品升级不会自动审阅已有书稿。

**`workspace/` 不随仓库或 Release 分发。** 首次初始化会在本机创建作品目录与索引；已有作品通过私人迁移或备份恢复导入。安装不会自带作者原始语料、私人小说或账号连接。

## 架构与数据边界

```text
Codex 执行任务
  ├─ 共享作者能力 + 公众号 Skill / 小说 Skill
  ├─ 本地文件工具 → 私有 workspace
  └─ 宿主 MCP 连接 → 微信公众号 / 腾讯文档 / 其他外部服务
```

MCP 是外部服务连接能力。写作方法保存在 Skill 中，作品和版本状态保存在本地；本项目不提供独立 Agent 服务或 MCP 插件运行框架。详见[架构说明](docs/architecture.md)。

公开文件包括方法、模板、脚本、技术文档和经审阅的风格抽象。正文、素材、镜像、过程记录、备份及云端回执保持私有；授权密钥由宿主管理。

## 外部服务

- [腾讯文档](docs/external-services/tencent-docs.md)：v2.0 已完成目标账号的真实读取、受控 Word 创建与更新、回读及操作记录验证。每次新安装需配置自己的连接。
- [微信公众号](docs/external-services/wechat.md)：v2.0 建立能力与接入约定，按确认范围不做真实账号验证。服务实现与权限需在后续实际接入时确认。
- [扩展其他服务](docs/external-services/adding-service.md)：接入宿主工具，补充能力说明与结果查询方式，复用本地操作记录。

## 分享与验证

作者能力来自既有的 370 条发表记录、352 条文章链接和 341 篇可用正文。公开包只包含蒸馏结果，统计为既有快照，不随安装自动更新。

```bash
python3 scripts/export_author_profile.py --out dist/touge-author-expression-1.0.0.zip
python3 -m unittest discover -s tests -v
python3 scripts/preflight_check.py
```

v2.0 的完整发布验收还要求迁移、独立行为及外部服务证据，不能用本地单元测试代替。[验收说明](docs/testing.md)区分公共可复现检查与私人迁移验收。

[文档导航](docs/README.md) · [安装](docs/installation.md) · [使用指南](docs/GUIDE) · [命令参考](docs/cli.md) · [迁移](docs/migration-v2.md) · [发布流程](docs/releasing.md) · [变更记录](CHANGELOG.md)
