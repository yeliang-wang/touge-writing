# v2.1 发行流程

发布完整公共能力包和独立作者表达包。私人 workspace、备份、评估原始会话和外部回执不分发。

先核对 VERSION、CHANGELOG、文档及目标标签；运行公共测试和维护者完整验收。检查 Git 候选与暂存区，获取远端状态，不覆盖他人的提交。GitHub 自动源码包与本项目完整包不同：完整包含 release-manifest.json 和展开的兼容链接。

```bash
python3 scripts/build_release.py --out dist/touge-writing-reboot-skill-2.1.0.zip
python3 scripts/export_author_profile.py --out dist/touge-author-expression-1.0.0.zip
```

build_release 从经过公共边界检查的 Git 候选文件构建，固定 ZIP 时间戳，拒绝覆盖旧输出。最终发行前必须提交并确保候选与提交一致。每个成员在 release-manifest 中有 SHA-256；整个资产另算 SHA-256。在临时目录解压，确认初始没有 workspace，运行 preflight、公共自检及创建合成作品。

正式发布的提交、v2.1.0 标签、Release、完整包内容须一致。说明两类写作、13 项方法、运行恢复、本地 workspace，以及公众号未实测和腾讯既有证据复用范围。不要上传私人 acceptance/report 或云端对象 ID。

推送后核对默认分支、标签和资产列表；下载资产比对 SHA-256。已经公开的标签与资产不静默替换，修复用新版本或明确更正。产品发布完成后不自动开始真实小说的下一章。
