# v2.0 安装与首次初始化

面向首次使用者。目标是取得完整公共项目，并在自己的机器上创建一份独立作品。

## 环境

- 核心命令：macOS 或 Linux、Python 3.9+，使用标准库。文件锁依赖 `fcntl`；当前不声明原生 Windows 支持。
- Git：克隆、公共边界检查和发行构建需要它。
- Codex：加载项目中的 Skill，执行写作和外部工具；Python 脚本不自行调用模型。
- 可选文章抓取：`lxml`。
- 可选 PPT 生成：`Pillow`。当前生成器还使用 macOS 的 `STHeiti Medium.ttc` 和 `Arial Unicode.ttf` 字体路径；Linux 核心工具可用不代表 PPT 渲染环境已满足。

可选依赖可安装到自行管理的虚拟环境中：`python3 -m pip install Pillow lxml`。只有使用对应功能时才需要它们。

## 获取完整项目

```bash
git clone --branch v2.0.0 https://github.com/yeliang-wang/touge-writing-reboot-skill.git
cd touge-writing-reboot-skill
python3 --version
```

也可下载 Release 的完整源代码包并解压。代码包不包含 Git 元数据，`preflight_check.py` 需要在 Git checkout 中运行。版本标签 checkout 适合固定使用；贡献修改时从它创建自己的分支。

在 Codex 中打开这个目录。两项 Skill 位于 `.agents/skills/`，依赖同仓库的 `shared/`、`scripts/`、`references/` 和 `templates/`。不要只复制单个 Skill 子目录并期待全部功能可用。若使用其他宿主，可生成上下文包，见[Agent 集成](../references/agent-integration-spec.md)。

## 创建本地工作区

安装只取得公共能力文件，不创建作者的作品副本。下面命令首次创建 `workspace/`、`catalog.json` 和示例小说；已有工作区会保留，重复作品 ID 会被拒绝。

```bash
python3 scripts/writing_workspace.py init --id my-novel --title "我的小说" --type novel
python3 scripts/writing_workspace.py init --id first-article --title "第一篇文章" --type wechat
python3 scripts/writing_workspace.py resume --project my-novel
python3 scripts/writing_workspace.py validate --project first-article
```

成功信号：`workspace/catalog.json` 包含两条作品记录；小说尚无全书方案和章节，文章校验返回空 `errors`。空作品没有待续章节是正常状态，随后由写作任务建立方案。

默认路径相对于运行命令时的当前目录。自选位置时把 `--workspace /path/to/private-workspace` 放在 `init`、`resume` 等子命令之前，并在后续命令中使用同一路径。Skill 默认约定项目根目录下的 `workspace/`；更换位置时向执行宿主明确该路径。

## 按需连接外部服务

本地创建作品不依赖 MCP。需要腾讯文档时，按[连接说明](external-services/tencent-docs.md)在自己的宿主中授权。公众号按[接入约定](external-services/wechat.md)选择服务与账号。本项目不随安装附带任何人的连接、凭据或云端文档。

已有私人数据的使用者，按[迁移指南](migration-v2.md)导入或从备份恢复；不要用新初始化结果覆盖旧工作区。
