# v2.2 辅助能力

主能力为公众号写作与小说写作。本页说明保留的辅助场景及实际实现边界，不承诺额外的在线服务。

| 场景 | 方法入口 | 工具支持 |
|---|---|---|
| 职业、技术、组织交流 | [交流方法](../references/conversation-persona.md) | Prompt conversation；Agent 场景 qa |
| 复盘、低谷与状态重启 | [Reboot](../references/reboot-protocol.md) | Prompt reboot |
| 产品问答 | [产品判断方法](../references/product-manager-capability.md) | Agent 场景 product_pm；事实由宿主取得 |
| PPT 与逐页讲稿 | [内容交付包](../references/content-deck-playbook.md) | build_content_deck.py |
| 旧文章改稿、标题、审稿 | [交互协议](../references/interaction-protocol.md) | Prompt rewrite/titles/audit |

根 Skill 根据请求选择这些方法。复用作者声音不意味着虚构作者经历，也不允许把小说角色资料带入产品问答。

## 上下文与提示词

```bash
python3 scripts/build_agent_context.py --scenario qa --channel generic --out /tmp/touge-qa.md
python3 scripts/build_agent_context.py --scenario product_pm --out /tmp/touge-product-context.md
python3 scripts/build_robot_prompt.py --mode conversation --topic "如何衡量转岗成本" --out /tmp/touge-conversation.md
```

这些命令只输出可供宿主读取的文本，不启动聊天机器人。`--channel feishu/wecom/docs` 只加入连接职责说明；本项目没有附带飞书、企微或石墨的服务端适配器。

## 内容交付包

先形成论点、听众与逐页结构，再提供 `slide-plan.json`。生成器使用 Pillow 渲染图片，并将整页图片装入 PPTX；可编辑源是 JSON、文章和讲稿，不是 PPT 内独立文字形状。环境和文件格式见[功能说明](../references/content-deck-playbook.md)。

## 接入其他宿主

宿主负责模型调用、读取私人资料、连接外部工具、权限、结果查询和用户交互。本项目提供方法与文件约定。需要外部系统的 HTTP API、消息收发或长期运行时，由集成者另行实现，不能把文档示例视为已实现接口。

## 与新写作能力的关系

旧辅助入口保留，阶段选择参数 --phase 只用于 novel/wechat。交流、产品问答不创建小说生命周期；公众号与小说任务则转到两项 Skill，按需读取公共能力卡。公共上下文导出不携带私人作品或 run。
