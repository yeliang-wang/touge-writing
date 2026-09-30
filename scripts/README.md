# v2.0 文件工具

本目录提供可独立运行的 Python CLI。核心工具使用标准库，适用于 macOS/Linux；不调用模型，也不建立 MCP 服务。所有参数见[命令参考](../docs/cli.md)。

| 工具组 | 文件 | 职责 |
|---|---|---|
| 作品与文件 | writing_workspace.py、workspace_lib.py | 初始化、定位、版本登记、历史继承、状态恢复、写锁和不可覆盖复制 |
| 迁移与恢复 | migrate_workspace.py、backup_workspace.py | 冻结清单复制、哈希校验、完整备份与独立恢复 |
| 来源检索 | private_retriever.py | 对文章 JSON 数组清单做词频/余弦检索 |
| 资料导入 | ingest_corpus.py、fetch_wechat_articles.py | 私有 JSONL 整理；可选公开文章链接抓取 |
| 上下文 | build_agent_context.py、build_robot_prompt.py | 将方法和可选检索结果组成宿主输入，不执行生成 |
| 检查 | manuscript_check.py、style_eval.py | 结构/重复提示与公众号风格启发式评分 |
| 外部连接配套 | configure_tencent_docs.py、external_operations.py | 宿主配置辅助和私人操作凭证；实际调用由宿主执行 |
| 交付与分享 | export_author_profile.py、build_content_deck.py | 作者规则包；可选 PPT 与讲稿 |
| 反馈与验证 | record_feedback.py、preflight_check.py、acceptance.py | 私人反馈、公共边界与本次完整迁移验收 |

`writing_workspace.py` 使用命令执行目录下的 workspace，或显式 `--workspace`。不要从任意目录运行相对脚本路径。输入文件、输出目录和副作用范围由调用者提供。

缺少作品、来源变化、重复版本或确认依据不足时应处理错误，不能删除校验逻辑或改旧稿来取得成功输出。工具的机械检查不代替作者内容决定。

[数据格式](../docs/workspace.md) · [测试](../docs/testing.md) · [开发](../docs/development.md)
