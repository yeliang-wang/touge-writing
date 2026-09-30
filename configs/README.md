# v2.0 配置与声明

这些文件描述公共能力和示例结构，不持有真实凭据，不会自动安装服务。

| 文件 | 版本/格式 | 用途 |
|---|---|---|
| [capabilities.json](capabilities.json) | schema 2.0 | 两项主能力、共享作者入口和旧辅助能力 |
| [external-services.example.yaml](external-services.example.yaml) | schema 1，JSON 编码的 YAML 子集 | MCP 服务所需能力与 v2.0 验收范围 |
| [corpus-sources.example.json](corpus-sources.example.json) | schema 1.0 | 私人材料来源、允许用途与占位路径 |
| [acceptance.json](acceptance.json) | schema 1 | 本次 v2.0 迁移发布的12组必需检查及明确排除项 |

能力记录至少声明 id、display_name、description、modes、required_references。`primary_capabilities` 为 wechat_writing 与 novel_writing；旧 writing 入口通过 alias_of 保留兼容。此映射是配置声明，宿主按 Skill 路由处理，不是动态插件加载器。

`modes` 不是全部 Python CLI 的共同枚举。`build_robot_prompt.py` 和 `build_agent_context.py` 只接受各自 parser 已实现的选项，见[命令参考](../docs/cli.md)。

真实语料路径放在本地工作区或调用参数中，真实账号连接放在宿主配置中。修改能力后同时更新所引用的方法、合成评测与文档，运行 preflight 检查重复 ID 和缺失引用。
