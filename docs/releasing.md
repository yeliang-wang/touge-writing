# v2.0 发布流程

面向有仓库发布权限的维护者。发布对象为公共能力代码、技术文档和作者能力包；私人工作区使用独立备份分发。

## 前置检查

1. 确认 `VERSION`、变更记录、文档及预期标签一致。
2. 获取远端状态，审阅待发布 diff；不覆盖其他人的新提交或重写远端历史。
3. 运行单元测试、preflight 和完整 acceptance。后者依赖私人证据，执行结果不能上传原始回执。
4. 在不含 workspace 的公共快照中检查链接、上下文导出和首次初始化；使用合成作品。
5. 审阅暂存文件，确保 workspace、work、outputs、dist、私人语料及账号配置不在 Git 树中。

## 构建与发布

提交审阅后的公开文件，再基于该提交创建版本标签。只构建 Git 中的文件，例如：

```bash
git archive --format=tar.gz --prefix=touge-writing-reboot-skill-2.0.0/ --output=dist/touge-writing-reboot-skill-2.0.0.tar.gz HEAD
python3 scripts/export_author_profile.py --out dist/touge-author-expression-1.0.0.zip
```

先建立 `dist/`。导出器拒绝覆盖旧 ZIP，重复构建使用新的输出位置或核对既有文件。完整包中的相对符号链接指向仓库内共享资料；确认解压工具保留它们。作者包是8个普通文件的独立 ZIP。

列出每个包的成员，确认没有私人目录和绝对链接，再计算 SHA-256。包内初始不存在 workspace；在临时解压目录运行 `init` 后才会出现本地工作区。

推送提交和对应标签，使用明确的发布说明和上述公开资产创建 GitHub Release。说明必须写清：两类写作、独立作者能力、workspace 本地创建、MCP 外部连接，以及公众号不做真实验证的范围。不能上传本机 acceptance/report.json、云端回执或私人备份。

## 发布后核对

- 远端默认分支、标签和 Release 指向预期提交。
- Release 为正式版本，资产名称、大小和 SHA-256 正确。
- 下载资产与本地受检包一致，仓库工作树保持干净。
- 发布凭证在本机保存；不以书稿内容审阅作为发布后必须执行的步骤。

若验证失败，保留错误证据并修正；已公开标签和资产不能在未说明的情况下静默替换。后续修复应使用明确的新版本或更正流程。
