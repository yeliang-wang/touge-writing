# 安装与首次初始化 · v2.1

需要 macOS/Linux、Python 3.9+；核心使用标准库，单机文件锁依赖 fcntl，未声明原生 Windows 支持。Git 用于克隆与发布；Codex 执行写作与 MCP。可选抓取使用 lxml；旧 PPT 生成使用 Pillow 和 macOS 字体，按需安装，不是写作核心依赖。

```bash
git clone --branch v2.1.0 https://github.com/yeliang-wang/touge-writing-reboot-skill.git
cd touge-writing-reboot-skill
python3 scripts/acceptance.py --public-only
python3 scripts/writing_workspace.py init --id demo --title "我的文章" --type wechat
python3 scripts/writing_workspace.py resume --project demo
```

也可下载完整能力 ZIP。官方构建包含 release-manifest.json，可在没有 Git 的解压目录运行 preflight；GitHub 自动 source archive 不含该生成清单，应在 Git checkout 做发布边界检查。完整 ZIP 里的兼容链接展开为普通文件。

在 Codex 打开完整项目。不要只复制 `.agents/skills/` 的某一个子目录：它依赖 shared、capabilities、scripts、references、templates。已有宿主如何发现项目技能以该宿主配置为准；本仓库不修改全局技能列表。其他宿主可用 build_agent_context.py 导出公共方法。

workspace 安装后才创建。上述 init 创建 catalog、文章元数据、空内容登记和派生状态，没有个人素材。全书使用 --type novel；用 set-chapters 增加稳定章 ID。重复 ID 会被拒绝，已有作品不会覆盖。

默认 workspace 相对当前终端目录。指定其他位置时：`python3 scripts/writing_workspace.py --workspace /path/to/private-workspace resume --project demo`。全局 --workspace 必须放在子命令前；给 Codex 同样的路径。运行脚本必须位于项目根，或使用实际绝对脚本路径。

本地写作不依赖外部连接。腾讯文档按 [配置说明](external-services/tencent-docs.md)授权，微信公众号按 [能力约定](external-services/wechat.md)接入；不在聊天中提交密钥。已有数据按 [迁移](migration-v2.1.md)在副本核验后继续。
