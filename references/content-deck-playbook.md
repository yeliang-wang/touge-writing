# v2.3 内容交付包

这是保留的辅助功能：把主题或已有文章转成逐页论点、讲稿和按需生成的 PPTX。它不改变公众号与小说两项主能力，也不自动发布内容。

## 内容组织

先明确听众、场景和要支持的判断。每页承载一个论点，具体事实来自任务材料；讲稿承接理由、代价和例子。文章可以作为来源，但不能把全文切成无逻辑的页面。

共享作者能力用于表达和判断，不能凭空增加个人经历、产品指标或客户案例。需要示例而无真实资料时明确使用合成例子。

## 生成器输入

`build_content_deck.py` 接收 JSON 计划。下面是可运行的合成最小示例：

```json
{
  "title":"示例分享",
  "audience":"工程团队",
  "article_markdown":"可选文章正文",
  "slides":[
    {"title":"先识别成本","subtitle":"选择工具前先明确任务","kind":"cover","talk":"这是一段合成讲稿，用于验证生成器输入。"},
    {"title":"看见代价","kind":"bullets","points":["维护成本","协作成本"],"talk":"分别考虑维护和协作的代价，再决定是否采用。"}
  ],
  "takeaways":["先明确任务，再比较代价"]
}
```

每页提供 title 和 talk；kind 支持 cover、claim、contrast、bullets、quote、architecture、modules、sequence、lifecycle、summary 等渲染分支。图形可使用 nodes/edges，流程可使用 steps；节点包含 id/label/note，连线包含 from/to/label。具体渲染以脚本为准，不是任意图形 DSL。

## 运行与环境

需要 Pillow 以及当前脚本使用的 macOS 中文字体路径；核心 Python 工具的 Linux 支持不代表这个渲染器跨平台字体已配置。

```bash
python3 scripts/build_content_deck.py --plan /path/to/slide-plan.json --out /path/to/private/deck --slug sample
python3 scripts/build_content_deck.py --plan /path/to/slide-plan.json --out /path/to/private/deck --estimate-only
```

输出包含 output 下的 PPTX、逐页 Markdown 讲稿、可选文章和 build-manifest.json，以及 preview 下的逐页 PNG 和 contact-sheet.png。用独立目录保存新版本，避免覆盖旧交付物。

PPTX 以整页 PNG 作为页面内容，不能把它描述成全部文字形状可编辑的原生演示稿。可编辑源是 JSON、Markdown 文章和讲稿。estimate-only 仅估算时长，不渲染页面，也不证明画面质量。

## 使用时验收

生成实际演示稿后核对页面内容、文字完整性、可读性和讲稿顺序；真实事实按来源检查。升级测试只使用合成内容，不借此重写私人作品。其他模式和参数见[辅助指南](../docs/auxiliary-guide.md)与[命令参考](../docs/cli.md)。

## v2.1 版本与写作来源

从已有文章或小说改编时引用明确内容版本；生成 PPT 和讲稿不修改源稿、不把交付完成登记成原文定稿。多轮产物可作为关联 run 的 delivery 文件保存，但此生成器本身不管理生命周期，也不调用外部发布服务。
