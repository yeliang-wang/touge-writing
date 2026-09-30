# 迁移到 v2.0

面向已有旧专家、私人语料或写作项目的使用者。目标是保存全部已有资产，并建立可恢复的本地作品状态。迁移不审批书稿内容。

## 与旧入口的变化

- 写作分为公众号单篇与长篇小说两个 Skill，共享 `shared/author-expression/`。
- `workspace/` 成为本地私人作品目录，安装时不携带作者数据。
- 根 Skill、旧 `write/rewrite` 等提示词模式及辅助能力保留；旧风格路径通过仓库内符号链接指向共享资料。
- 过去依赖特定宿主命令或“云端唯一副本”的规则需在迁移中明确替换；不能把旧内部代理凭据带入新宿主。
- 历史章方案继续指向原全书版本，不因迁移自动继承最新版本。

## 迁移流程

1. 备份旧项目和未提交改动，停止对来源的并发编辑。
2. 在私人目录建立冻结清单，逐文件记录来源、目标相对路径与 SHA-256。
3. 使用 `migrate_workspace.py` 原样复制到本地档案，校验源和目标。重复执行只接受相同内容，拒绝覆盖不同文件。
4. 依据已有明确决定建立 `catalog.json`、作品元数据和版本清单。脚本负责复制与校验，不自动从旧对话推断作者批准。
5. 核验当前状态、历史继承与已保存的工作阶段。原资料缺失和迁移丢失分别记录。
6. 如有云端资产，通过新授权读取目录和文档；保存完整快照与差异，不自动覆盖定稿。
7. 创建全量私人备份，恢复到新目录并验证文件及进度。

清单结构示意，实际路径和哈希必须现场生成：

```json
{"schema_version":1,"migration_id":"migration-example","entries":[{"source":"/path/to/original/file.md","destination":"archives/original/file.md","sha256":"<实际SHA-256>","source_id":"legacy-project"}]}
```

```bash
python3 scripts/migrate_workspace.py --plan /path/to/private/migration-plan.json --workspace workspace
python3 scripts/migrate_workspace.py --workspace workspace --verify --check-sources
```

跨机器后源路径可能不存在；此时目标归档校验仍可运行，`--check-sources` 只用于原源文件仍可访问的环境。

## 恢复与回退

```bash
python3 scripts/backup_workspace.py create --workspace workspace --out /path/to/private-backups/workspace.tar.gz
python3 scripts/backup_workspace.py restore --archive /path/to/private-backups/workspace.tar.gz --destination /path/to/restored-workspace
```

保留归档旁的 `.json` 校验凭证。恢复目标必须不存在，脚本逐文件校验且拒绝路径穿越、链接与已有目录覆盖。回退使用验证过的独立恢复目录，不删除迁移来源，不覆盖现有工作区。

## v2.0 首次迁移验证

首次私有迁移核对了1,623个源文件、47份工作副本、36条登记版本及352条语料索引；另读取35份腾讯文档。详细路径、作品状态、来源缺口和回执保存在本机，公共发行物只保留方法和汇总。

升级验收检查这些资产能否完整保存和恢复。真实书稿的事实、情节及章节方案审阅属于发布后的独立使用任务，不是发布条件。新行为评测使用合成资料。
