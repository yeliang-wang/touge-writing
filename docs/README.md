# v2.0 文档导航

适用于 `VERSION` 为 2.0.0 的代码。本文档描述现有功能；示例中的作品、输入和路径均为示例，不包含作者的私人工作区。

| 读者目标 | 文档 |
|---|---|
| 安装并建立第一份作品 | [安装与初始化](installation.md) |
| 写公众号文章或小说 | [使用指南](GUIDE) |
| 理解边界和模块协作 | [架构](architecture.md) |
| 理解作品、语料和版本格式 | [工作区数据](workspace.md) |
| 查询脚本参数、输出与限制 | [命令参考](cli.md) |
| 使用交流、Reboot、PPT 等功能 | [辅助能力](auxiliary-guide.md) |
| 迁移旧专家与历史资产 | [迁移指南](migration-v2.md) |
| 连接腾讯文档或公众号 | [外部服务](external-services/README.md) |
| 修改代码或贡献文档 | [开发指南](development.md) |
| 理解 v2.0 的验收证据 | [测试与验收](testing.md) |
| 构建公开包并发布 | [发布流程](releasing.md) |
| 核对本次交付边界 | [实施范围](implementation-plan.md) |

## 模块入口

[两个写作 Skill](../.agents/skills/README.md) · [作者能力](../shared/author-expression/README.md) · [脚本](../scripts/README.md) · [配置](../configs/README.md) · [模板](../templates/README.md) · [提示词](../prompts/README.md) · [参考资料](../references/README.md) · [评测](../evals/README.md) · [测试](../tests/README.md) · [界面元数据](../agents/README.md)

作者表达资料、蒸馏统计和历史合成样例属于能力资料，不是软件版本号。作者能力包独立版本为 1.0.0；它可被 v2.0 工作台复用。私人迁移报告只保存在本机 `workspace/acceptance/`。
