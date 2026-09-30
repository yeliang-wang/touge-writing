# v2.0 提示词辅助文件

这些文件提供人工使用的任务输入结构，不替代 Skill 路由或版本管理。

- [writing.md](writing.md)：公众号文章、改稿、标题等单篇任务。
- [conversation.md](conversation.md)：交流、判断与复盘辅助任务。
- [style-audit.md](style-audit.md)：先辨识文体，再审阅表达。

小说任务优先读取小说 Skill 和作品上下文，不直接套用公众号文章结构。`build_robot_prompt.py` 按自己的模式映射读取 references；它不会自动加载本目录所有文件。完整参数见[命令参考](../docs/cli.md)。
