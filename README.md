# 头哥侃码写作与人格 Reboot Skill

这是一个面向个人写作、交流机器人和 reboot 型人格蒸馏的公开 skill 仓库。它把“头哥侃码”的长期公开表达沉淀为可执行的写作、交流、风格审计和 Agent 嵌入能力。

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
5. Agent 嵌入：把 skill 安装到外部 AI Agent 中，通过飞书、企业微信、石墨文档等系统完成问答、草稿和知识协作。
6. 持续进化：接入新的私有语料源和自定义能力，让 skill 从写作/交流扩展到产品经理问答、产品知识问答等场景。

## 目录

```text
.
├── SKILL.md
├── docs/
│   └── GUIDE
├── configs/
│   ├── capabilities.json
│   └── corpus-sources.example.json
├── references/
│   ├── cognitive-os.md
│   ├── expression-dna.md
│   ├── interaction-protocol.md
│   ├── agent-integration-spec.md
│   ├── evolution-spec.md
│   ├── product-manager-capability.md
│   ├── style-audit-rubric.md
│   ├── distillation-report.md
│   ├── robot-spec.md
│   ├── productization-runbook.md
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
    ├── fetch_wechat_articles.py
    ├── ingest_corpus.py
    ├── build_robot_prompt.py
    ├── build_agent_context.py
    ├── private_retriever.py
    ├── record_feedback.py
    └── style_eval.py
```

## 使用方式

在 Codex 中可作为 skill 使用：

```text
请使用 $touge-writing-reboot-skill，把这个主题写成一篇我的风格文章
```

也可以作为通用 prompt/agent 知识库，把 `SKILL.md` 和 `references/` 接入自己的机器人。

如果要安装到外部 AI Agent 中，先生成一个 Agent 上下文包：

```bash
python3 scripts/build_agent_context.py \
  --scenario qa \
  --channel feishu \
  --out /tmp/touge-agent-context.md
```

外部 Agent 负责模型调用、权限、审计、飞书/企业微信连接和人工接管；本 skill 负责提供风格、判断协议、输出契约和边界。

## 蒸馏层次

- `cognitive-os.md`：判断循环、价值坐标、主题簇。
- `expression-dna.md`：标题、开头、短语、段落运动和语气机制。
- `interaction-protocol.md`：写作机器人、交流机器人和 reboot 模式的路由协议。
- `agent-integration-spec.md`：把 skill 嵌入外部 AI Agent、IM 通道和知识问答场景的产品契约。
- `evolution-spec.md`：持续接入新语料、能力注册、评测和公开边界的演进协议。
- `product-manager-capability.md`：面向具体产品/业务系统的产品经理问答能力模板。
- `style-audit-rubric.md`：用 15 分制检查一段输出是否贴近风格系统。
- `distillation-report.md`：从私有语料中提取出的总体结论。
- `robot-spec.md`：写作/交流/reboot 机器人输入输出契约。
- `productization-runbook.md`：本地运行、私有检索、评测和发布检查流程。

## 用户指南

完整场景指南见 [`docs/GUIDE`](docs/GUIDE)，包括：

- 在 Codex 中作为 `$touge-writing-reboot-skill` 使用。
- 安装到外部 AI Agent，连接飞书或企业微信。
- 把输出写入石墨文档指定目录。
- 将“头哥侃码 Reboot”包装成服务。
- 私有语料、评测、人工反馈和发布检查。

## 持续进化入口

新的语料源不要直接提交到公开仓库。先在私有目录里规范化：

```bash
python3 scripts/ingest_corpus.py \
  --source-type wecom_chat \
  --source-id wecom_im_export \
  --input /path/to/private/wecom/export.jsonl \
  --out-dir /path/to/private/evolution-corpus \
  --tag im_chat \
  --tag product_qa \
  --redact
```

新的能力先注册到 `configs/capabilities.json`，再补对应的 `references/*.md` 和 eval 任务。比如“某某产品的产品经理能力”应该接入产品文档、客户反馈和会话语料，但产品事实留在私有知识库，公开仓库只保留能力框架和边界。

## 私有语料检索

公开仓库不包含全文语料，但可以在本机连接私有语料：

```bash
python3 scripts/private_retriever.py \
  --manifest /path/to/private/corpus/manifest.json \
  --query "技术人转产品经理 背锅 职业选择" \
  --top-k 5
```

## 机器人 Prompt 组装

```bash
python3 scripts/build_robot_prompt.py \
  --mode write \
  --topic "AI Agent 平台突然又火了，企业是不是都该立刻上" \
  --manifest /path/to/private/corpus/manifest.json \
  --out /tmp/touge-prompt.md
```

## 风格闸门

生成草稿后可以用离线评分器做一次基础检查：

```bash
python3 scripts/style_eval.py draft.md
```

评分器只是产品化烟测，不替代作者本人判断。

## 发布前检查

上传 GitHub 前运行：

```bash
python3 scripts/preflight_check.py
```

它会检查必需文件、私有语料泄漏、敏感文本和 eval 任务覆盖。

## 公开边界

不要把原始全文语料、后台索引、阅读数据、私密经历细节直接提交到公开仓库。若需要示例，优先使用合成示例、短片段、或已经明确可公开复用的文章链接。
