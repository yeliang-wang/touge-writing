# 写作原子能力 · v2.4.1

13 项独立方法覆盖任务约定、素材发现、来源映射、结构、场景、衔接、回望、背景、连续性、标题、作者声音、文字卫生与审稿。它们提供可复用的写作判断，不保存作品事实、不执行模型调用、不决定定稿。

[registry.json](registry.json)登记 ID、版本、用途、路径与哈希；每项正文在 `<ID>/<版本>/CAPABILITY.md`。卡片包含输入、输出、完成条件、失败处理及合成正反例。发布后的版本不可原地覆盖；改方法需新增版本和更新引用。

```bash
python3 scripts/capability_catalog.py --select scene-design@1.0.1 editorial-review@1.0.1 --kind novel
python3 scripts/build_agent_context.py --scenario novel --phase draft --out context.md
```

公众号与小说 Skill 提供可选组合，任务只取需要的方法。作品的具体方案、人物、配额和授权属于私人 workspace。作者表达包独立版本为 1.0.0；本产品版本与方法版本各自演进。运行时锁定见 [run 说明](../docs/runs.md)，能力完成后的实际文字评测见 [evals](../evals/README.md)。

v2.4.1 保留 13 个独立方法，注册表共 16 个版本条目。场景、回望和审稿新增 1.0.1，补充有据扩写、自然分段、读者收获及初稿确认边界；其 1.0.0 继续可用，历史 run 不追随新组合。具体字数、分段配额、收获点数与书中事实不进入公共方法。
