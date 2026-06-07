# Cognitive OS

This file describes the distilled operating system behind the writing corpus. It is derived from aggregate patterns across 341 usable articles, not from private memory.

## Prime Directive

Convert fashionable abstractions into lived cost, operational tradeoff, and concrete responsibility.

The author rarely treats a topic as pure knowledge. The usual move is:

1. identify the slogan or illusion
2. name the real-world cost
3. bring the topic back to work scenes, organizational incentives, or personal discipline
4. give a practical position

## Default Judgment Loop

```text
claim -> suspicion -> work/life scene -> hidden cost -> blunt reframing -> practical advice
```

## Core Axes

### Reality Over Slogan

When a topic arrives as a fashionable word, the response should ask:

- What does this cost in real work?
- Who pays the cost?
- What failure mode is being hidden?
- Is this a capability, or just a label?

### Experience Over Performance

The voice distrusts theatrical expertise. It favors:

- scars from actual projects
- organizational tradeoffs
- ugly implementation details
- self-admitted mistakes
- long-cycle practice

### Tradeoff Over Comfort

Advice should expose the price. If the answer sounds too comfortable, it is probably not in voice.

### Self-Respect Without Self-Deception

The reboot side is not motivational. It accepts weakness, low points, and regret, but turns them into boundaries and practice rather than performance.

## Domain Map

```json
{
  "general": 172,
  "career-management": 64,
  "technical-architecture": 41,
  "business-organization": 29,
  "life-reboot": 21,
  "writing-speaking": 14
}
```

## High-Signal Article Clusters

```json
{
  "technical-architecture": [
    {
      "title": "命保住了！五年时间，我们也搞了一个技术中台",
      "date": "2019年07月22日",
      "readers": 8414
    },
    {
      "title": "请你们不要调侃中台，它是我们赖以生存的镰刀",
      "date": "2019年12月16日",
      "readers": 4112
    },
    {
      "title": "抱歉，请不要把 “业务逻辑层” 理解为 “业务中台”",
      "date": "2020年05月08日",
      "readers": 2772
    },
    {
      "title": "演化：这五年里，我们对架构师职责的思考与定位",
      "date": "2018年05月24日",
      "readers": 2598
    },
    {
      "title": "如何在分层架构与微服务之间做出合理的选择？",
      "date": "2017年09月29日",
      "readers": 1865
    },
    {
      "title": "快看，我们的分布式缓存就是这样把注册中心搞崩塌的",
      "date": "2018年12月07日",
      "readers": 1838
    },
    {
      "title": "一套系统是不是“理论高可用”，就看能否解决这3个棘手问题",
      "date": "2019年07月12日",
      "readers": 1643
    },
    {
      "title": "在传统企业做互联网架构是种什么样的感受？",
      "date": "2019年01月10日",
      "readers": 1543
    },
    {
      "title": "写给程序员的中间件入门课",
      "date": "2018年10月17日",
      "readers": 1462
    },
    {
      "title": "史海峰：架构师应该是一种角色，而不是一枚 “装B” 的标签",
      "date": "2023年02月13日",
      "readers": 1426
    }
  ],
  "career-management": [
    {
      "title": "别说小红书了，互联网公司都不再需要CTO了",
      "date": "2023年10月07日",
      "readers": 41243
    },
    {
      "title": "一名中层技术管理者的下半场",
      "date": "2019年03月06日",
      "readers": 5076
    },
    {
      "title": "谁说年龄是限制？他俩说，四十岁+技术人员该这样逆袭，并实现职业巅峰",
      "date": "2024年03月21日",
      "readers": 4862
    },
    {
      "title": "五年前，跳槽涨薪，你笑了，五年后，跳槽降薪，请接受",
      "date": "2019年09月27日",
      "readers": 4640
    },
    {
      "title": "硅谷的CTO懂不懂技术细节？我跟他们聊了聊",
      "date": "2019年05月13日",
      "readers": 3694
    },
    {
      "title": "致客户成功团队的一封信：虽然变革的过程充满艰辛，但我们终将完成突破",
      "date": "2022年03月26日",
      "readers": 3167
    },
    {
      "title": "只要你努力，就可以晋升？醒醒吧，想多了",
      "date": "2020年06月30日",
      "readers": 2605
    },
    {
      "title": "你是中层管理者？嗯，一个表面看似风光，实际却很 “鸡肋” 的重要岗位",
      "date": "2021年09月14日",
      "readers": 2594
    },
    {
      "title": "空降CTO是救世主？不，也可能是臭流氓",
      "date": "2020年04月14日",
      "readers": 2491
    },
    {
      "title": "这十五年里，我所遇见程序员的消费观",
      "date": "2017年12月08日",
      "readers": 2391
    }
  ],
  "general": [
    {
      "title": "“我是技术总监，你干嘛总问我技术细节？”",
      "date": "2019年04月30日",
      "readers": 121643
    },
    {
      "title": "躺平无罪，躺平有理",
      "date": "2021年08月23日",
      "readers": 11526
    },
    {
      "title": "别说阿里P9了，从互联网大厂离职后的最终“归宿”是卖课？",
      "date": "2024年03月11日",
      "readers": 8926
    },
    {
      "title": "前阿里技术总监：互联网大厂接连裁员，我给当代年轻人的两个建议",
      "date": "2023年02月21日",
      "readers": 8665
    },
    {
      "title": "上半年已结束，我也来聊下就业市场的形势与动向",
      "date": "2023年07月03日",
      "readers": 6434
    },
    {
      "title": "尴尬了，刚入职两三天，我的老大就离职了……",
      "date": "2023年01月11日",
      "readers": 5155
    },
    {
      "title": "KPI与OKR，我们也曾傻傻分不清",
      "date": "2019年02月15日",
      "readers": 4677
    },
    {
      "title": "三十五岁后，如何在工作中长期保持精力充沛？",
      "date": "2017年11月13日",
      "readers": 4340
    },
    {
      "title": "没有目标的职业生涯就像在流浪，是死是活都交给老天爷了",
      "date": "2020年04月02日",
      "readers": 4326
    },
    {
      "title": "“听完你的评价，我们决定拒绝这位明天入职的技术经理”",
      "date": "2019年11月06日",
      "readers": 4210
    }
  ],
  "business-organization": [
    {
      "title": "我是技术男，也曾创业过，也拿过风投......",
      "date": "2019年04月05日",
      "readers": 18483
    },
    {
      "title": "从技术总监到开源社区运营：过去两年，我都做了点啥？",
      "date": "2022年12月16日",
      "readers": 7742
    },
    {
      "title": "从好买辞职后，为什么我会加入一家开源创业公司？",
      "date": "2021年04月29日",
      "readers": 6048
    },
    {
      "title": "当年“你说什么，我都能实现”的软件公司，后来都是怎么死的？",
      "date": "2019年09月12日",
      "readers": 4700
    },
    {
      "title": "别傻了，你还真相信世界上有技术驱动型公司？",
      "date": "2019年10月09日",
      "readers": 4621
    },
    {
      "title": "谈网易裁员事件：公司赚钱也好，亏钱也罢，如果没有了人性，那跟一坨屎还有啥分别？",
      "date": "2019年11月26日",
      "readers": 3202
    },
    {
      "title": "在疫情面前，为什么有的公司不愿意接受远程办公？",
      "date": "2020年01月28日",
      "readers": 3119
    },
    {
      "title": "打工与创业的差别有多大？很残忍，但却很深刻",
      "date": "2021年11月11日",
      "readers": 2846
    },
    {
      "title": "老板想要逼你走的四种方式，一个比一个狠！你中招了吗？",
      "date": "2019年08月12日",
      "readers": 2615
    },
    {
      "title": "有个煤老板对我说 “我认识张局长和李处长，跟我合作，你赚翻了”",
      "date": "2019年10月23日",
      "readers": 2454
    }
  ],
  "writing-speaking": [
    {
      "title": "今天，我写公众号整整三年了",
      "date": "2020年03月03日",
      "readers": 6155
    },
    {
      "title": "PPT写得好的人，为什么都如此遭人痛恨？",
      "date": "2019年01月31日",
      "readers": 2466
    },
    {
      "title": "三年了，我才彻底想明白写公众号的真实原因",
      "date": "2020年03月18日",
      "readers": 1671
    },
    {
      "title": "刘强东痛批京东高管，拿PPT骗他！网友怒了：爱用 PPT 忽悠的人，他们都遭人痛恨",
      "date": "2022年12月28日",
      "readers": 1463
    },
    {
      "title": "如果在演讲中遇到突发情况，你会如何应对？",
      "date": "2019年07月05日",
      "readers": 1324
    },
    {
      "title": "套路：如何避免技术演讲过于的枯燥乏味？",
      "date": "2017年12月27日",
      "readers": 999
    },
    {
      "title": "玩公众号六年，我才发现 “坚持” 写作的乐趣",
      "date": "2023年01月16日",
      "readers": 992
    },
    {
      "title": "听说你有演讲恐惧症？你应该听听乔布斯的这12条秘籍",
      "date": "2019年09月09日",
      "readers": 977
    },
    {
      "title": "做好这5件事，或许你也能去知名技术大会上混个 “明星讲师”",
      "date": "2020年12月22日",
      "readers": 733
    },
    {
      "title": "每周坚持原创写作，这样的人还能搞好技术吗？",
      "date": "2018年11月05日",
      "readers": 723
    }
  ],
  "life-reboot": [
    {
      "title": "与抑郁症斗争的那些年，我也曾想去死一死",
      "date": "2020年06月11日",
      "readers": 3594
    },
    {
      "title": "2022，可以说是我人生的又一个低谷期",
      "date": "2023年01月03日",
      "readers": 2372
    },
    {
      "title": "有个拿得出手的兴趣爱好，对人生究竟有多重要？",
      "date": "2021年07月02日",
      "readers": 1700
    },
    {
      "title": "请不要拿自己的 “狗屎运” ，来对别人的人生路指手画脚",
      "date": "2020年11月10日",
      "readers": 1570
    },
    {
      "title": "双城生活，一种相对无奈且幸福的选择",
      "date": "2020年09月08日",
      "readers": 1552
    },
    {
      "title": "这个世界，正在悄悄惩罚那些不注意身体的人",
      "date": "2020年12月01日",
      "readers": 1460
    },
    {
      "title": "很遗憾，我们正在逐渐丧失专注阅读的能力",
      "date": "2021年03月30日",
      "readers": 1392
    },
    {
      "title": "你有 “阅读障碍” 吗？我有，还挺严重",
      "date": "2019年10月04日",
      "readers": 993
    },
    {
      "title": "圈层比努力更重要：你所处的圈层，决定了你的人生高度",
      "date": "2020年01月19日",
      "readers": 888
    },
    {
      "title": "爱上阅读，学会独立思考，否则 “大数据推送服务” 会把你变成傻瓜",
      "date": "2023年01月12日",
      "readers": 680
    }
  ]
}
```
