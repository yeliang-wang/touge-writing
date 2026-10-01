# 确定性文件工具 · v2.1

writing_workspace 管内容与继承；material_index 适配素材清单并记录映射；writing_run 管任务、快照和恢复；capability_catalog 解析显式方法版本。它们使用标准库及 workspace_lib，不调用模型。

private_retriever 保留旧命令并支持两种清单；build_agent_context 增加按阶段加载公共方法。manuscript_check 只产出文字卫生线索。backup_workspace、export_author_profile、build_release 分别处理私人备份、作者包和完整公共发行。acceptance 区分公共自检、v2.0 回归和 v2.1 检查。

旧抓取、摄入、提示构建、内容交付、反馈和风格扫描脚本保持辅助用途；external_operations 只记账，configure_tencent_docs 只配置宿主。

[CLI](../docs/cli.md) · [运行](../docs/runs.md) · [辅助功能](../docs/auxiliary-guide.md)
