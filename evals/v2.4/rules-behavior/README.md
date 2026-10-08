# v2.4 独立合成任务行为评估

本记录是独立评估Agent依照当前两套Skill实际执行的前向任务，不是盲测，也不是只填结构化文件。案例、人物、正文、材料缺口和“作者请求”全为本次合成；没有读取或修改私人作品。模型对自己本轮交付的语义核对按self_review记录，独立性指评估Agent独立于产品实现工作，不代表第二名文学评审。

## 实际交付

- **小说只审阅**：[输入请求](workspace/novels/night-archive/inputs/request.md)、[原章](workspace/novels/night-archive/inputs/chapter.md)、[前章](workspace/novels/night-archive/inputs/neighbor.md)、[材料与缺口](workspace/novels/night-archive/inputs/materials.md)、[实际审阅](workspace/novels/night-archive/outputs/review.md)。审阅定位钥匙持有路径、签字断言、跨章主题重复和背景功能；给出保留项、收益与代价，没有改稿。任务completed，稿件needs_revision；表单缺失只影响签字判断。
- **公众号单句小改**：[输入请求](workspace/wechat/meeting-note/inputs/request.md)、[原文](workspace/wechat/meeting-note/inputs/article.md)、[候选全文](workspace/wechat/meeting-note/outputs/candidate.md)、[交付](workspace/wechat/meeting-note/outputs/delivery.md)、[实际差异](workspace/wechat/meeting-note/outputs/change.diff)。只替换正文第5行一句，把空泛口号改为负责人和第一版时间；标题、前后段及犹疑句逐字保留，无完整run和提纲审批。候选meets_rules限于本篇四项要求，不表示整篇结构最优。

[小说覆盖](workspace/novels/night-archive/outputs/rule-review.json)和[公众号覆盖](workspace/wechat/meeting-note/outputs/rule-review.json)均含实际文字判断、产物哈希与位置；CLI通过只说明绑定完整，语义结论由Agent阅读全文后给出。小说机械扫描无告警，仍识别出多项内容问题，不能用零告警替代审阅。

## 执行与边界

[命令回执](transcript.jsonl)保留实际init、baseline登记、resume、规则resolve、run start/artifact/stage/verify、机械扫描与逐项规则review输出。`<EVAL>`代表本次临时合成评估根，`<PUBLIC>`代表公开能力根；本机绝对路径已替换。

评估初期实现方修复了登记边界；[最终复核](final-verification.json)记录在代码冻结后对实际任务重放原run请求与同一完成操作、重跑两项规则review及workspace validate。无不确定操作的二次派发，无新正文登记。最终绑定代码见[result.json](result.json)的evaluated_files。

保留了合成源文件、实际产物、run清单、事件和回执。为避免重复归档公开方法文件，未复制run的inputs快照目录；其原始来源及哈希保留于run清单与执行回执。本目录是选定评估证据包，不是完整workspace备份。

未执行旧版本run恢复或规则版本漂移实验，不将当前run的resume称为旧契约验收。未测试真实作者审美批准、真实文学质量、真实账号发布、全书质量或真人多账户协作。两项任务只证明当前合成范围的遵从；没有accepted版本，未宣称作者批准。
