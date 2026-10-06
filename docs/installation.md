# 安装与首次初始化 · v2.3.1

需要 macOS/Linux、Python 3.9+；核心使用标准库，单机文件锁依赖 fcntl，未声明原生 Windows 支持。Git 用于能力更新和可选私有作品协作；GitHub CLI 可选，GitHub MCP 不必需。Codex 执行写作与 MCP。可选抓取使用 lxml；旧 PPT 生成使用 Pillow 和 macOS 字体，按需安装，不是写作核心依赖。

## 取得完整能力项目

可以克隆项目，或从 [Releases](https://github.com/yeliang-wang/touge-writing/releases) 选择实际已发布的完整能力 ZIP。克隆默认分支可能包含尚未发布的改动；需要固定版本时选择已存在的对应标签，不将本页标题作为发布证明。

```bash
git clone https://github.com/yeliang-wang/touge-writing.git
cd touge-writing
python3 scripts/acceptance.py --public-only
```

官方构建包含 release-manifest.json，可在没有 Git 的解压目录运行 preflight；GitHub 自动 source archive 不含该生成清单，应在 Git checkout 做发布边界检查。完整 ZIP 里的兼容链接展开为普通文件。

在 Codex 打开完整项目。不要只复制 `.agents/skills/` 的某一个子目录：它依赖 shared、capabilities、scripts、references、templates。本仓库不修改全局技能列表。其他宿主可用 build_agent_context.py 导出公共方法。

## 创建自己的作品

推荐位置为 `~/.touge-writing/workspace/`，与可升级的公共项目分开。首次 init 自动创建必要目录和索引，无需另外运行 setup。

```bash
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" init --id demo --title "我的文章" --type wechat
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" resume --project demo
```

init 创建 catalog、作品元数据、空内容登记、派生状态和 START-HERE，没有个人素材或虚构示例作品。小说使用 `--type novel`，用 set-chapters 增加稳定章 ID。重复 ID 或标题被拒绝，已有作品不会覆盖；如果已有作品未登记或索引损坏，应先修复索引，不能用空索引掩盖原作品。

resume 的 workspace 和 project_path 字段显示本次实际路径。成功时应能看到创建的作品及其初始阶段。随后用 `$touge-wechat-writing` 或 `$touge-novel-writing` 提出写作请求。继续已有作品不需要重新 init。

## 路径与旧版兼容

新版 Skill 和文档显式传 `--workspace`。要使用自己的其他目录，将上述路径整体替换，并在任务中告诉宿主；后续素材、run、外部操作和备份使用同一个位置。

脚本省略参数时仍以当前终端目录下的 `workspace` 为默认值。没有全局配置、环境变量优先级或自动跨目录查找；目标无效时先核对路径，不切换另一份同名作品。`--workspace` 必须放在 writing_workspace.py 和 writing_run.py 的子命令前。例子在项目根运行；从其他目录执行时使用脚本绝对路径及同一个明确工作区。

**已有 v2.1 或更早作品先读 [迁移](migration-v2.2.md)。** 若推荐位置尚未建立而旧项目内已有 catalog，先沿用旧目录或完成迁移，不初始化一份新的空工作区。迁移后保留旧副本，并只向选定的新目录写入。

## 使用已有私有作品仓库

先取得完整能力项目，再将获准访问的私有工作区仓库克隆到另一个独立目录，例如 `touge-writing-workspace`。一个工作区可以容纳多部小说和公众号单篇。对该目录使用同一个显式 `--workspace`，通过 catalog 中的稳定 ID 恢复作品；不要重新 init 已有作品。可以在工作区 README 中记录配套能力版本，帮助协作者使用一致的方法。

私有仓库不会自动获得公共能力代码，也无需将代码复制进 workspace。日常更新分别在各自仓库执行；将本地旧资料首次入库前按 [v2.3 迁移](migration-v2.3.md) 清点范围、完整备份、核对源文档和克隆恢复。

从旧公共项目名称升级时，按 [v2.3.1 更名说明](rename-v2.3.1.md) 更新 remote、本地路径及当前使用入口；历史方案与运行快照保留原名，不为更名重建作品。

## 连接和协作

本地写作不依赖外部连接。腾讯文档按 [配置说明](external-services/tencent-docs.md) 授权，微信公众号按 [能力约定](external-services/wechat.md) 接入；凭据保存在宿主，不在聊天、公共项目或 workspace 中保存。

合作者各自安装完整能力项目，并取得获准的私有作品仓库。共同版本保存在 Git，个人运行在独立本地过程副本；通过候选包与主编顺序登记协作。[合作指南](collaboration.md) 明确具体流程。腾讯文档用于可选导入、审稿和导出，不是写作或定稿存储的前提。私人文件及备份没有应用层加密；GitHub Private 是访问控制，也不是只有作者持钥的端到端加密。
