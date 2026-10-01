# 从 v2.0 升级到 v2.1

这是兼容性增量升级，已有 book.yaml、catalog.json、内容登记和文件路径保持 schema 1。无需移动正文、重写方案或改变历史继承；新 materials/runs/lifecycle 仅在使用时添加。

1. 冻结当前公开代码版本，在 workspace 外创建完整备份。
2. 恢复到一个新目录，逐文件检查哈希；不要直接覆盖唯一工作区。
3. 更新公共包，在副本运行 validate 与 resume，核对已接受计划、正文、下一步及旧章方案父版本。
4. 用合成作品验证新能力。真实书稿的内容审阅是另一个写作任务，不能被升级自动触发。
5. 后续写作第一次需要时新增 run，锁定当前材料、方法和任务。旧推演可记为历史导入／阶段未知，不能倒填成“当时运行了正式 v2.1”。

```bash
python3 scripts/backup_workspace.py create --workspace workspace --out work/backups/before-v21.tar.gz
python3 scripts/backup_workspace.py restore --archive work/backups/before-v21.tar.gz --destination work/restores/before-v21
python3 scripts/writing_workspace.py --workspace work/restores/before-v21 validate --project demo
```

规则分流：可复用方法进入经审阅的公共能力；文体选择进入相应 Skill；人物、年份、比例、题记、感悟落点和具体审批约定留在作品；旧宿主命令保留历史，当前服务协议另按宿主工具执行。每项提炼记录原路径、哈希、去向和保留部分；旧文件不删除。

JSON 与 JSONL 可直接只读适配，不必重抓语料。旧正文绝对路径必须在明确选择的清单目录内；跨目录旧数据需显式重新定基准或独立清单。来源读过和事实已核实不能由迁移补造。

回滚在副本切回 v2.0 公共代码，旧内容登记仍可 validate/resume。新扩展文件保留，旧工具不需要理解它们。新版本开始的新内容仍遵守旧格式；未知未来格式拒绝写入。备份和历史 release 不替换。

早期从其他宿主导入另见 [v2.0 迁移入口](migration-v2.md)。
