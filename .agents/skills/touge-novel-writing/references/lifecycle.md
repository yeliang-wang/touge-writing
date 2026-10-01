# 生命周期 · v2.1

[阶段定义](lifecycle.json)版本为 1.0.0；其文件也随 run 锁定。它是宿主执行约定，不是独立工作流服务。

`plan → draft → review → revise → review → completed` 是常见路径。按实际任务可从 draft、review 或 revise 开始；暂停后可回到所需阶段。小说有全书与章节两层，全书 run 目标为 book，章级 run 使用已登记 ID；公众号目标为 article。计划型任务在 plan → review → completed 即可交付，不必生成正文。

完成一次 run 只表示本次任务交付完成。片段试写不推进整章，正文 accepted 仅由内容登记和实际作者决定建立。正在修订已有定稿时，旧定稿持续有效。不能把“稿件已交付”当作作者审美认可。

详见项目根 docs/runs.md。记录任务与授权引用、范围、所用方案与素材哈希、事实／虚构约定、能力版本、参数、未决项及影响范围。主持写作的 Codex 阅读这些材料并产出正文；脚本只保存并检查文件状态。
