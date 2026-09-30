---
name: touge-novel-writing
description: 规划、续写、修改和审阅长篇小说或连载作品，管理全书与章节方案继承、人物时间线和历史版本；用于写书、小说、章节任务。
---

# 小说写作（长篇、连载）

项目根目录为本文件向上三级目录。先读 [作者能力](../../../shared/author-expression/PROFILE.md)，再按 `workspace/catalog.json` 识别作品。书名、角色、配额、具体虚构权限都属于该作品，不作为其他小说默认设定。

## 恢复作品
运行 `python3 scripts/writing_workspace.py resume --project <作品ID或别名>`；指定章节时加 `--chapter <章节ID>`。读取返回的全书方案、当前章方案与正文、邻章正文、有效规则和未决事项，再读取作品 `START-HERE.md`、`book.yaml`、人物与时间线资料。

`baseline` 仅表示可追溯旧正文，不表示它符合最新方案。已有章节方案继承历史全书版本时保留原关系；本次调整如需升级继承，在新方案中明确差异。不要用文件日期或版本号外观代替作者决定。

## 章节工作
读 [小说工作流](references/workflow.md)，需要新方案时用 [章节方案模板](../../../templates/chapter-plan.md)。遵守本作品已确认的 review/draft 阶段；已有授权继续有效。方案审阅期间，只交付方案，不顺带改写正文或其他章节。

确认方案后新建正文版本。保留当前作品事实、叙事视角、人物状态及来源；新增设定先作为候选记录。真实经历、公共史实和获得授权的虚构范围分别处理，不把一章的授权泛化到全书。

审稿兼顾场景、语言、动机、章节连续性、事实和作者声音；保护应保留的句子与节奏。机器检查只报告可检测问题，事实核对必须阅读来源。通用检查用 `python3 scripts/manuscript_check.py <正文文件>`；书籍专属阈值由该书规则提供。

## 保存与交付
正文、计划、审稿分开保存。通过 `writing_workspace.py add-revision` 注册新版本和实际确认依据；已登记历史正文保持不变。`state.json` 可从版本记录重建。

按 [腾讯文档说明](../../../docs/external-services/tencent-docs.md) 使用外部服务。云端操作记录属于作品；MCP 仅负责连接。断网时继续本地写作，并明确未同步状态。

新增小说使用 `writing_workspace.py init --type novel`，然后建立该书独立的全书方案、章节配置与人物资料，不能复制另一部小说的事实作为默认设定。
