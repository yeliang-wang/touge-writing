# 头哥写作与人格 Reboot Skill

这是一个面向个人写作、交流机器人和 reboot 型人格蒸馏的公开仓库骨架。它参考了 `zhangxuefeng-skill`、`nuwa-skill` 这类 persona distill 项目的结构，但目标不是复刻某个公众人物，而是把一个长期写作者的公开表达沉淀为可执行的写作与交流系统。

## 当前语料快照

- 公众号发表记录：370 条
- 标准公开文章链接：352 篇
- 已提取可用正文：341 篇
- 覆盖时间：2017-2024
- 私有正文语料规模：约 101.5 万中文字符
- 注意：本仓库不发布全文语料。公开内容只包含提炼后的风格规则、工作流、边界说明和工具脚本。

## 能力目标

1. 写作机器人：根据主题生成接近作者风格的长文、短评、口播稿、标题和二稿。
2. 交流机器人：以作者常见判断方式回应职业、技术、组织、创业、个人状态类问题。
3. Reboot 模块：重建作者的价值判断、表达边界、反应模式和自我校准机制。
4. 风格审计：判断一段文字哪里不像作者，哪里 AI 味太重，如何改。

## 目录

```text
.
├── SKILL.md
├── references/
│   ├── cognitive-os.md
│   ├── expression-dna.md
│   ├── interaction-protocol.md
│   ├── style-audit-rubric.md
│   ├── distillation-report.md
│   ├── style-dna.md
│   ├── title-patterns.md
│   ├── article-playbooks.md
│   ├── conversation-persona.md
│   ├── reboot-protocol.md
│   ├── boundaries.md
│   └── corpus-summary.md
├── prompts/
│   ├── writing.md
│   ├── conversation.md
│   └── style-audit.md
└── scripts/
    └── fetch_wechat_articles.py
```

## 使用方式

在 Codex 中可作为 skill 使用：

```text
请使用 $touge-writing-reboot-skill，把这个主题写成一篇我的风格文章
```

也可以作为通用 prompt/agent 知识库，把 `SKILL.md` 和 `references/` 接入自己的机器人。

## 蒸馏层次

- `cognitive-os.md`：判断循环、价值坐标、主题簇。
- `expression-dna.md`：标题、开头、短语、段落运动和语气机制。
- `interaction-protocol.md`：写作机器人、交流机器人和 reboot 模式的路由协议。
- `style-audit-rubric.md`：用 15 分制检查一段输出是否贴近风格系统。
- `distillation-report.md`：从私有语料中提取出的总体结论。

## 公开边界

不要把原始全文语料、后台索引、阅读数据、私密经历细节直接提交到公开仓库。若需要示例，优先使用合成示例、短片段、或已经明确可公开复用的文章链接。
