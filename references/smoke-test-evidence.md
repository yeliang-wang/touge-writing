# Smoke Test Evidence

## Private Retrieval

Command:

```bash
python3 scripts/private_retriever.py \
  --manifest /path/to/private/corpus/manifest.json \
  --query "技术人转产品经理 背锅 职业选择" \
  --top-k 5
```

Result shape:

- Retrieved `从互联网程序员到云厂商产品经理：过去一年，他都经历了什么？`
- Retrieved `真实经历：整整一年了，他是这样从程序员转型做产品经理的`
- Retrieved `做架构师不好么？做什么产品经理`
- Retrieved `怎样才算成功转型 “乙方产品经理”？避免陷入这20个误区`

This proves the private grounding path can find thematically related old articles without committing the private corpus.

## Style Gate Negative Case

Input:

```text
随着时代的发展，技术人员需要不断提升综合能力，以适应复杂多变的市场环境。总而言之，我们要打造多维度能力闭环，实现个人价值增长。
```

Result:

```json
{
  "total": 0,
  "verdict": "unlike",
  "pass": false,
  "ai_smell_markers": ["随着时代的发展", "总而言之", "闭环", "多维度"]
}
```

## Style Gate Positive Case

Input topic:

```text
技术人转产品经理不是逃离代码，而是换一种方式背锅。
```

Result:

```json
{
  "total": 11,
  "verdict": "close",
  "pass": true
}
```

This is only a deterministic smoke test. The final 1.0 gate still requires the owner to review real outputs.
