---
name: touge-wechat-writing
description: 创作、改写和审阅头哥风格的微信公众号单篇文章，管理文章版本、素材与发布准备；用于公众号、推文、单篇文章任务。
---

# 公众号写作（短篇、单篇）

项目根目录为本文件向上三级目录。先读 [作者能力](../../../shared/author-expression/PROFILE.md)，按任务读 [公众号方法](../../../references/wechat-public-account-playbook.md)；标题任务另读 [标题方法](../../../references/title-patterns.md)。

明确主题、读者、要表达的判断及已有素材，按需确定结构再写作；用户已明确要求直接成稿时，不额外增加固定审批阶段。已有稿优先保留作者观点和有辨识度的表达。

## 资料与版本
使用 `workspace/catalog.json` 识别文章。新文章可用 `python3 scripts/writing_workspace.py init --id <稳定英文标识> --title <标题> --type wechat` 建立独立目录。

需要历史文章时，运行 `python3 scripts/private_retriever.py --manifest workspace/corpus/manifest.json --query <主题> --top-k 5`，从返回来源继续阅读相关原文。没有正文的记录不能被当作已阅读来源。书稿改编需要明确记录源章节；未经要求不改源书稿。

草稿与定稿分别保存，使用 [文章模板](../../../templates/wechat-article.md)。通过 `writing_workspace.py add-revision` 注册版本。`accepted` 版本必须关联实际作者确认记录；不替作者写“已确认”。

## 写作与审稿
正文使用可编辑 Markdown。按任务提供标题、摘要、正文及必要的来源说明。检查观点成立、例子有依据、语气自然、段落适合阅读。风格词库是参考，不机械堆词。为未提供的私人经历保留待补位置，不当作事实编写。

审稿明确保留项、问题位置与修改理由。排版 HTML、配图和平台字段是按需生成的派生产物，不能覆盖创作源稿。

## 外部服务
需要草稿箱、素材上传、发文时读 [公众号服务说明](../../../docs/external-services/wechat.md)；需要云端协作时读 [腾讯文档说明](../../../docs/external-services/tencent-docs.md)。Codex 连接并调用 MCP，Skill 不启动独立服务。v2.0 的公众号服务只建立能力，尚未进行真实账号验收。

本地定稿、同步草稿和公开发布是不同动作。沿用已明确的账号、稿件版本和操作授权；如果版本或目的地改变，则重新明确对象。平台返回“提交成功”不等于“已发布”。
