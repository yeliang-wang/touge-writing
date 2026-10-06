# 更名与统一工作区 · v2.3.1

适用于已有安装的使用者。公共项目由 `touge-writing-reboot-skill` 更名为 `touge-writing`，根 Skill 的显式调用改为 `$touge-writing`。两项写作 Skill 继续使用 `$touge-wechat-writing` 和 `$touge-novel-writing`。

私有工作区推荐采用 `touge-writing-workspace` 这类统一名称。它可以同时保存多部小说和公众号单篇，每个作品在 `catalog.json` 中有独立 ID 与目录。更名不会初始化新作品、修改方案继承、改变稿件状态或把未选入的私人档案自动上传。

## 更新已有能力项目

先查看本地工作树，保留尚未提交的修改；不要为更名覆盖已有目录。以下示例在公共项目根运行：

```bash
git status --short
git remote set-url origin https://github.com/yeliang-wang/touge-writing.git
git fetch origin --tags
```

已有 SSH 配置可继续使用 `git@github.com:yeliang-wang/touge-writing.git`。按实际分支与本地改动取得新版本；目录如需同名，可在退出当前目录并确认目标不存在后重命名为 `touge-writing`。在 Codex 重新打开新目录，更新当前脚本绝对路径、宿主已保存的项目入口或已安装的根 Skill 引用。旧目录的符号链接可以临时兼容本机历史入口，不属于安装必需项。

新下载的完整包名为 `touge-writing-2.3.1.zip`，解压根目录为 `touge-writing-2.3.1/`。历史发行包不重打包、不替换。作者表达包继续为 1.0.0。

## 工作区路径与权限

公共项目和私有工作区是独立 Git 根。已存在的工作区只更改仓库身份、本地目录和当前导航中的路径；`catalog.json` 里的作品 ID、相对路径和登记内容无需随仓库改名。私有 remote 使用该工作区实际所属账号，不能改成公共能力项目的 remote。

后续命令始终显式传入重命名后的 `--workspace`。新增小说使用 `init --type novel`，新增公众号单篇使用 `init --type wechat`；已有作品使用 `resume --project <稳定ID>`。目录格式和命令见 [workspace](workspace.md) 与 [CLI](cli.md)。

统一私有仓库可以先由一人独享。仓库成员能读取其中全部文件和历史；若未来只允许同事合作某部作品，为那个访问范围建立独立仓库。更名不自动邀请协作者。

## 验证与历史保留

更名后核对两边的 remote 和 GitHub 可见性，用新路径恢复已有作品并验证登记；重新克隆私有仓库，比对跟踪文件。公共项目执行以下自检：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/preflight_check.py
python3 scripts/acceptance.py --public-only
```

维护者按 [完整验收](testing.md) 验证现存迁移、备份和更名后的私有远端。v2.3.1 结果单独保存；原始写作快照、历史方案、回执、标签及旧验收报告保留当时的名称和哈希。本次核对既有腾讯文档归档，未因更名重新执行云端读写。

遇到路径问题时先修复当前入口或 remote，再以原作品 ID 恢复；不初始化空 workspace 替代旧资料，也不批量替换历史文件中的旧路径。
