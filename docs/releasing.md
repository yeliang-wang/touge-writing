# v2.2 发行流程

发布完整公共能力包和独立作者表达包。私人 workspace、备份、评估原始会话、实际合作约定和外部回执不分发。

先核对 VERSION、CHANGELOG、README、模块文档及目标标签；运行公共测试和维护者完整验收。检查 Git 候选与暂存区，获取远端状态，不覆盖他人的提交。GitHub 自动源码包与本项目完整包不同：完整包包含 release-manifest.json 和展开的兼容链接。

```bash
python3 scripts/build_release.py --out dist/touge-writing-reboot-skill-2.2.0.zip
python3 scripts/export_author_profile.py --out dist/v2.2.0/touge-author-expression-1.0.0.zip
```

build_release 从经过公共边界检查的 Git 候选文件构建，固定 ZIP 时间戳，拒绝覆盖旧输出。最终发行前必须提交并确保候选与提交一致。每个成员在 release-manifest 中有 SHA-256；整个资产另算 SHA-256。作者表达规则未变化则版本保持 1.0.0，可使用新输出路径，不能覆盖历史资产。

在临时目录解压，确认初始没有私人 workspace，运行 preflight、公共自检及外部临时目录中的合成小说和文章初始化。另在隔离目录回归不带 --workspace 的旧 CLI 行为；不得为测试创建或修改用户真实作品。[验收范围](testing.md)

正式发布的提交、v2.2.0 标签、Release 和完整包内容须一致。发行说明包括外部私人工作区推荐、旧默认兼容、一次性迁移、各自 workspace 的腾讯文档合作方式，以及没有自动双向同步或应用层加密的边界。腾讯文档明确历史证据复用范围，微信公众号明确未实测；合成合作演练不称为真实多人并发验证。只报告实际完成的结果，不上传私人验收报告或真实云端 ID。

推送后核对默认分支、标签和资产列表；下载资产比对 SHA-256。已经公开的 v2.0、v2.1 标签、资产和历史报告不静默替换，修复用新版本或明确更正。产品发布完成后不自动开始真实小说的下一章。
