# v2.2 实现范围

本版本沿用 v2.1 的写作方法、内容登记和 lifecycle，集中解决私人工作区与公共代码分离，以及按合作约定交换稿件。发布结果以实际验收报告为准。

| 方案落点 | 实现 |
|---|---|
| 推荐外部私人目录 | 两项 Skill、根路由及文档显式传 --workspace；不增加全局配置 |
| 旧 CLI 兼容 | 省略参数仍用当前终端目录下 workspace |
| 创建与恢复 | 沿用 writing_workspace.py init/resume；防止已有未登记作品被空索引掩盖 |
| 当前定位可见 | resume 返回本次 workspace 和 project_path |
| 全量迁移与回滚 | backup_workspace.py、迁移清单和本版私人验收；旧源和历史回执保留 |
| 轻量合作 | templates/collaboration.md、docs/collaboration.md 和 Skill 流程 |
| 外部共享 | 腾讯文档由宿主连接；读基准、汇总候选、实际确认、私有操作回执 |
| 文档与格式 | README、安装、workspace 字段、CLI、模块说明和迁移指南同步 |
| 验收 | configs/acceptance-v2.2.json；公共 B01–B07，完整 B01–B10 |
| 发布 | 完整能力 ZIP、独立 1.0.0 作者包及公开边界检查 |

13 项原子能力、素材多对多映射、输入快照和恢复规则继续有效。方法卡、作者包和作品方案没有内容变化时不随产品升级升版。

不新增 setup/status、环境变量优先级、workspace 共享、自动双向同步、多人自动合并或应用层加密。单机锁不承担云端并发控制，腾讯文档最新编辑不替代作者确认。真实作品迁移只核验完整性与恢复，不重写或审阅内容。

[v2.2 迁移](migration-v2.2.md) · [合作](collaboration.md) · [架构](architecture.md) · [验收](testing.md)
