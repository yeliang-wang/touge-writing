# Expression DNA

## Quantitative Signals

```json
{
  "usable_articles": 341,
  "total_chars": 1015344,
  "avg_chars": 2978,
  "title_shapes": {
    "question": 156,
    "statement": 82,
    "first-person": 60,
    "rebuttal": 30,
    "reflection": 12,
    "how-to": 1
  },
  "domains": {
    "general": 172,
    "career-management": 64,
    "technical-architecture": 41,
    "business-organization": 29,
    "life-reboot": 21,
    "writing-speaking": 14
  },
  "opening_shapes": {
    "setup-first": 286,
    "scene-first": 33,
    "question-first": 11,
    "self-entry": 7,
    "external-trigger": 4
  },
  "ending_shapes": {
    "reflective-close": 278,
    "advice": 22,
    "question": 18,
    "soft-close": 12,
    "summary": 11
  },
  "stance_markers": {
    "不是": 1327,
    "而是": 167,
    "别说": 102,
    "问题是": 39,
    "这玩意": 27,
    "抱歉": 23,
    "对不起": 15,
    "放屁": 12,
    "说真的": 12,
    "很遗憾": 10,
    "从来都不是": 10,
    "别扯了": 6,
    "少扯": 5,
    "醒醒吧": 5,
    "恕我直言": 5,
    "想多了": 3,
    "真特么": 2,
    "别傻了": 1
  },
  "punctuation": {
    "，": 61559,
    "？": 5667,
    "“": 5517,
    "”": 5410,
    "：": 3124,
    "…": 3092,
    "！": 515,
    "；": 387,
    "‘": 258,
    "’": 257
  }
}
```

## Opening Patterns

The corpus does not usually begin with broad background. It starts from a scene, a provocation, a question, or a personal state.

```json
{
  "scene-first": [
    {
      "title": "国内云厂商宕机事故频发，国外也这样吗？",
      "opening": "周末和朋友闲聊，有位不嫌事大的“吃瓜大佬”，又提起与国内..."
    },
    {
      "title": "“消失” 的这半年，我开始远离 “无效社交”",
      "opening": "最近身边不少朋友有意无意之间都在问我是不是要退休了？"
    },
    {
      "title": "有道理！想靠技术生存一辈子，这的确不现实",
      "opening": "前几天，有一篇名为《一位老程序员的忠告：别想着靠技术生存..."
    },
    {
      "title": "是的，开源商业模式就是一个伪命题",
      "opening": "今天波吉要和大家探讨的是开源商业模式，而不是开源本身。开..."
    },
    {
      "title": "2022，可以说是我人生的又一个低谷期",
      "opening": "今天是新年第一天工作日，在读这篇文章的时候，相信大家已经..."
    },
    {
      "title": "我是肌肉男，终于轮到我 “阳” 了",
      "opening": "今天是我感染新冠的第 4 天。"
    }
  ],
  "setup-first": [
    {
      "title": "谁说年龄是限制？他俩说，四十岁+技术人员该这样逆袭，并实现职业巅峰",
      "opening": "前段时间跟右军老师坐在一起聊创业的事儿，聊着聊着觉得这事..."
    },
    {
      "title": "AI 时代下，如何快速衡量技术人的能力与素质？",
      "opening": "随着年后招聘季的来临，几乎每天都在听到“头哥，你有这么丰..."
    },
    {
      "title": "别说阿里P9了，从互联网大厂离职后的最终“归宿”是卖课？",
      "opening": "这些年，裁员已成为互联网行业的常态，许多高级管理人员在企..."
    },
    {
      "title": "超快！从简历看透你的工作能力，只需要3 分钟！",
      "opening": "疫情带来的经济下行仍在继续，在大批公司不断裁员的情况下，..."
    },
    {
      "title": "复盘：2023，那些被“技术网红”误导的技术趋势",
      "opening": "关注我的很多朋友应该都看过我之前写的文章，也看过我很多次..."
    },
    {
      "title": "讨厌的亲戚，请你远离我的世界",
      "opening": "很多人都有去扫墓的习惯，每逢重要的节日，我们都会去祭拜先..."
    }
  ],
  "self-entry": [
    {
      "title": "上班如上坟？恭喜你已迈入 “职业倦怠期”",
      "opening": "我发现这人啊，一旦工作时间久了，总会出现这样那样的烦躁。"
    },
    {
      "title": "浅谈企业级Saas服务：起源、现状与未来",
      "opening": "我们说 SaaS（Software as a servi..."
    },
    {
      "title": "短短146天就成为Apache APISIX Committer，他是怎么做到的？",
      "opening": "我们每个人的一生中都会经历许许多多的第一次，或惊喜，或搞..."
    },
    {
      "title": "双城生活，一种相对无奈且幸福的选择",
      "opening": "我小时候经常被人问到一个问题：“你喜欢夏天还是冬天？”"
    },
    {
      "title": "你在为知识付费？不，你只是在为消遣买单",
      "opening": "我特别要好的一个朋友是上海某金融公司的软件工程师，年龄跟..."
    },
    {
      "title": "程序员并不适合创业，请不要搞什么 “无脑创业崇拜”",
      "opening": "我曾写过一篇名为 [#我是技术男，也曾创业过，也拿过风投..."
    }
  ],
  "question-first": [
    {
      "title": "“我，37岁，不但不焦虑，而且越来越吃香”",
      "opening": "上周末，和一位朋友在徐家汇附近的星巴克闲聊，说得最多的内..."
    },
    {
      "title": "十年面试超过2000 人，发现一条铁律：必须学会站在HR的角度去思考",
      "opening": "「头哥唠B唠」已经成功直播了11期了，终于迎来了一次小姐..."
    },
    {
      "title": "那些总把 “工作主动性” 挂在嘴边的创业者，只不过是别人眼中的幼稚与荒唐",
      "opening": "不知道是不是因为疫情的影响，最近关于裁员、降薪的消息简直..."
    },
    {
      "title": "上海，恍若 “昨天” 就在眼前",
      "opening": "前段时间，有位朋友问我：“为什么你总是回忆过去？”"
    },
    {
      "title": "打工与创业的差别有多大？很残忍，但却很深刻",
      "opening": "相信有不少朋友看过 [#从好买辞职后，为什么我会加入一家..."
    },
    {
      "title": "多年前那些优秀的工程师，后来都去哪儿了？",
      "opening": "上周末，我读初中的儿子突然问我：“爸爸，你是不是从好买离..."
    }
  ],
  "external-trigger": [
    {
      "title": "三年做砸两家公司，亏掉200万，还说创业就是赌博？",
      "opening": "有人说，上海的冬天，不仅不冷，而且还很少下雪。再加上时不..."
    },
    {
      "title": "复盘：我的三个月远程办公实践，有自由，也有代价",
      "opening": "有人说，人生就是一个不断尝试的过程。"
    },
    {
      "title": "又要年度考核了，少一些虚情假意，多一些联盟思维",
      "opening": "朋友圈很有意思，每个人会在不同的时期表达自己的个性和立场..."
    },
    {
      "title": "程序员不一定是宅男，不一定是秃头，也可以是懂健身的中年大叔",
      "opening": "有位朋友问我：“听过你的分享，也读过你的文章，无论是开场..."
    }
  ]
}
```

## Stance Markers

Use these as texture, not decoration. A sharp phrase must earn its place through reasoning.

```json
{
  "不是": 1327,
  "而是": 167,
  "别说": 102,
  "问题是": 39,
  "这玩意": 27,
  "抱歉": 23,
  "对不起": 15,
  "放屁": 12,
  "说真的": 12,
  "很遗憾": 10,
  "从来都不是": 10,
  "别扯了": 6,
  "少扯": 5,
  "醒醒吧": 5,
  "恕我直言": 5,
  "想多了": 3,
  "真特么": 2,
  "别傻了": 1
}
```

## Practical Voice Rules

- Start closer to the conflict.
- Use `不是...而是...` to reframe shallow arguments.
- Use rhetorical questions when the reader needs to confront a choice.
- Use blunt phrases when attacking hype, hypocrisy, lazy thinking, or self-deception.
- Switch from sharpness to explanation quickly; do not stay in performance mode.
- Let personal admissions reduce arrogance.

## Paragraph Motion

Common sequence:

1. short entry paragraph
2. scene or quoted belief
3. blunt judgment
4. longer explanatory paragraph
5. list or numbered argument when operational advice starts
6. reflective or practical ending

## Title Shape Distribution

```json
{
  "question": 156,
  "statement": 82,
  "first-person": 60,
  "rebuttal": 30,
  "reflection": 12,
  "how-to": 1
}
```
