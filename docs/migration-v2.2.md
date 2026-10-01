# 迁移到独立私人工作区 · v2.2

面向已有本地 workspace 的用户。目标是将完整私人资料迁到项目之外，继续使用原作品、方案、正文和历史；不是重建作品或重写书稿。推荐目标为 `~/.touge-writing/workspace/`，自定义位置仍通过已有 `--workspace` 指定。

v2.2 保留旧 CLI 默认值，不传参数仍访问当前终端目录下的 workspace。新版 Skill 和文档显式使用推荐位置或本次指定位置，没有新增配置文件、setup/status 命令或自动迁移守护进程。若不迁移，继续显式传入旧目录即可。

## 迁移前

暂停源工作区的写入，确定源目录和一个尚不存在的目标目录。不要在目标中先 init；不要将两份同名作品目录直接合并。确认备份空间充足，盘点素材清单、云端回执和历史报告引用的其他文件。

完整迁移包含 catalog、全部作品、私人语料、WorkBuddy 导入原件、镜像、过程版本、方案、review 和验收资料。若某些附件本来就在 workspace 之外，它们不会被工作区备份自动包含，需记录所在位置并继续保留。外部链接上的云端原件仍在原服务。

## 备份与恢复

在旧能力项目根目录运行以下命令。示例源目录是该项目内的 workspace；实际位置不同则替换 `--workspace`。每次备份使用新的文件名，工具拒绝覆盖已有归档。

```bash
python3 scripts/backup_workspace.py create \
  --workspace "$PWD/workspace" \
  --out "$HOME/.touge-writing/backups/pre-v2.2.0.tar.gz"

python3 scripts/backup_workspace.py restore \
  --archive "$HOME/.touge-writing/backups/pre-v2.2.0.tar.gz" \
  --destination "$HOME/.touge-writing/workspace"
```

create 记录文件路径、字节数和 SHA-256，并检查备份前后清单一致。restore 验证归档与逐文件哈希，拒绝恢复到已有目录。它不删除源目录，`.writing.lock` 不作为作品内容备份。归档及相邻 JSON 回执一起保留，恢复需要该回执。压缩归档没有应用层加密，应放在符合资料要求的存储位置。

## 核验与切换

1. 核对源、目标文件清单及哈希。新增迁移和验收报告单列，不混入原件比较。
2. 逐作品运行 validate 和 resume，核对作品身份、已确认方案、独立章方案、历史继承及当前任务。更换为 catalog 中的实际作品 ID：

```bash
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" validate --project YOUR_PROJECT_ID
python3 scripts/writing_workspace.py --workspace "$HOME/.touge-writing/workspace" resume --project YOUR_PROJECT_ID
```

3. 核对实际使用的素材清单和 run 输入。新位置的 workspace 和 project_path 应指向目标，历史版本内容及任务阶段应保持原样。
4. 盘点旧绝对路径：历史来源地址与回执原样保留；仍依赖原位置的附件保持可访问并列入迁移报告。不批量替换历史文件中的路径，不用新记录覆盖旧证据。以后若确需搬迁外部附件，另作有哈希依据的迁移。
5. 验证成功后，告知宿主从新目录继续任务。后续 workspace、run、素材和备份命令都显式使用新位置。保留源目录作为迁移副本，并停止向其写入。

恢复保存的章评审阶段只证明状态恢复，不开始审稿、续写或重新确认全书方案。旧章方案不会改为继承最新全书方案。

## 验收报告和旧证据

维护者完整验收使用：

```bash
python3 scripts/acceptance.py --workspace "$HOME/.touge-writing/workspace"
```

v2.2 报告保存到所选 workspace 的 acceptance-v2.2，v2.0 acceptance 与 v2.1 acceptance-v2.1 原样保留。完整维护者检查依赖该次发布的私人迁移和外部证据，普通用户不需要取得维护者书稿；自行迁移以全量恢复、作品校验和自己的素材引用可用性为依据，公共能力自检使用 `--public-only`。

腾讯文档回执随本地资料迁移，账号凭据继续由宿主管理。未变更协议核验历史回执，并注明证据年份与范围；不将迁移成功称为本次重新联网验证。

## 回滚与后续更新

切换后尚未产生新内容时，可显式指定源目录恢复使用。已经产生新内容时，先备份新目录并核对差异，不能直接切回旧副本而遗失新版本。归档恢复始终使用另一个不存在的目录，验证后再采用。

后续升级只更新公共能力项目。私人工作区保持原位置；新作品的初始化、多人合作和云端交付分别按 [安装](installation.md)、[合作](collaboration.md) 和 [外部服务](external-services/README.md) 执行。

早期 WorkBuddy 导入与 v2.1 方法迁移说明保留为历史：[v2.0](migration-v2.md)、[v2.1](migration-v2.1.md)。其旧命令、报告位置和验收数量属于对应版本。
