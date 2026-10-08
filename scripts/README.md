# 确定性文件工具 · v2.4.1

writing_workspace 管内容与继承；material_index 适配素材清单并记录映射；writing_run 管任务、快照和恢复；capability_catalog 解析显式方法版本。它们使用标准库及 workspace_lib，不调用模型。

新版用法显式传 `--workspace "$HOME/.touge-writing/workspace"` 或本次指定路径。writing_workspace、writing_run 和 external_operations 的该参数位于子命令前；backup_workspace create 的参数位于子命令后。旧命令不传参数仍保留当前终端目录下的 workspace 默认值，不增加全局配置。

init 创建作品，拒绝覆盖及用新空索引掩盖已有未登记作品；resume 显示实际工作区与作品路径。私人素材工具使用明确清单或 project-path，不能自动搜索另一份同名作品。

private_retriever 保留旧命令并支持两种清单；build_agent_context 支持按阶段加载公共方法。manuscript_check 只产出文字卫生线索。backup_workspace、export_author_profile、build_release 分别处理私人备份、作者包和完整公共发行。acceptance 区分公共自检、本版完整检查和历史回归；v2.4 单独统计 D01–D06，公共结果与维护者私有验收分别保存；旧 v2.3 及更早证据不覆盖。

git_collaboration 在独立 Git workspace 中创建候选包并检查提交边界、输入基准及内容哈希，不创建远端或 PR、不替代访问控制、不自动登记 accepted。个人 run/lifecycle 留在本地过程副本，主编顺序使用原内容工具整合。[协作命令](../docs/cli.md)

旧抓取、摄入、提示构建、内容交付、反馈和风格扫描脚本保持辅助用途。external_operations 只记账，configure_tencent_docs 只配置宿主；合作时仍由宿主预读、核对变化、提交、回读，脚本不实现多人自动正文合并。工作区和备份无应用层加密。

[CLI](../docs/cli.md) · [运行](../docs/runs.md) · [迁移](../docs/migration-v2.3.md) · [合作](../docs/collaboration.md) · [辅助功能](../docs/auxiliary-guide.md)

writing_rules 解析作品 rules_file 与可选 rules_manifest，按目标／任务类型检查引用完整性与审阅覆盖。规则 Markdown 是正文单源；工具不认证已阅读、不判断文学质量。新 run 固定规则上下文，直接登记可保存轻量审阅。见 [规则执行](../docs/rules.md)。

本轮补丁的范围与兼容说明见 [v2.4.1 升级说明](../docs/upgrade-v2.4.1.md)。方法按 ID 与显式版本解析；能力数量按独立 ID 统计。验收按 VERSION 使用独立配置、行为证据及输出，保留既有版本记录。
