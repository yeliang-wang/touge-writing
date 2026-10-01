# v2.1 实现范围

本版本延续 v2.0 文件模型，并新增以下可检验模块；发布是否通过以验收报告为准。

| 方案落点 | 实现 |
|---|---|
| 13 项方法及显式版本 | capabilities/registry.json、capability_catalog.py |
| 两类写作入口与阶段定义 | .agents/skills 下的 Skill、lifecycle 与 recipes |
| 多格式来源、读取范围、使用映射 | material_index.py，private_retriever.py 兼容入口 |
| 任务、输入快照、候选与恢复 | writing_run.py；writing_workspace.py resume 展示当前任务 |
| 内容登记唯一权威 | 既有 revisions.json；历史继承与接受依据不变 |
| 公开上下文按需加载 | build_agent_context.py --phase/--capability |
| 质量与兼容验证 | tests、evals/v2.1、acceptance.py 的公共／私人模式 |
| 发行可核验 | build_release.py、独立作者包、公共链接检查 |

不提供数据库服务、MCP 运行时或自动发布；不保证哈希相同的模型输出逐字重现。迁移与作品内容审阅分开，具体规则分流和源文件完整性回执留在私人 workspace。
