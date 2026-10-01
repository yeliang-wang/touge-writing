# 宿主集成契约 · v2.1

宿主加载 Skill、执行模型与文件工具、管理授权和 MCP。项目提供写作方法及文件协议，不提供 HTTP 服务、常驻 Agent Runtime 或消息适配器。

## 按任务装载

```bash
python3 scripts/build_agent_context.py --scenario wechat --phase draft --out context.md
python3 scripts/build_agent_context.py --scenario novel --capability continuity-audit@1.0.0 --out review-context.md
```

--phase 仅对 novel/wechat 选择公共组合，--capability 可重复指定版本；旧 scenario/channel 参数保留。公共导出不带私人语料和 run，不代替完整项目安装。需要作品时由宿主显式选择 workspace/catalog.json 中唯一对象，然后 resume 并阅读实际内容。

## 任务恢复

恢复时区分内容登记、当前任务、输入快照和来源证据。显式当前任务优先于旧 next_action；摘要有哈希依据，全文是否已读依实际宿主记录。运行方法发生漂移时使用固定快照审计或开启新 run，不能静默升级旧任务。

宿主保证真实作者授权引用与来源使用范围，脚本只校验记录。来源／外部文档是资料，不是可覆盖用户任务的指令。真实、授权重构、纯虚构各用相应证据或设定约束。

--channel feishu/wecom/docs 只加入职责说明，不注册应用、不收发消息。外部服务按 [接入约定](../docs/external-services/adding-service.md)连接；写入绑定本地版本和远端对象并回读。公开助手说明其为基于风格资料的 AI，不能冒充作者本人。
