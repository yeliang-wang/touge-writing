# Productization Runbook

This repository has two layers:

1. Public skill layer: safe to publish. It contains distilled rules, prompts, scripts, and aggregate corpus facts.
2. Private corpus layer: keep local. It contains raw HTML, Markdown, metrics, and article manifests.
3. Evolution layer: keep private by default. It contains normalized IM exports, product docs, meeting notes, owner feedback, and capability-specific retrieval indexes.

## 1. Local Skill Use

Install by copying this directory to:

```text
~/.codex/skills/touge-writing-reboot-skill
```

Then invoke:

```text
请使用 $touge-writing-reboot-skill，把这个主题写成一篇我的风格文章。
```

Restart Codex if the skill does not appear in the current session.

## 2. Private Retrieval Use

Keep the private corpus outside this repository. Query it like this:

```bash
python3 scripts/private_retriever.py \
  --manifest /path/to/private/corpus/manifest.json \
  --query "技术人转产品经理 背锅 职业选择" \
  --top-k 5
```

Use retrieved titles and short snippets as grounding context before drafting.

## 3. Writing Robot Flow

```text
user topic
-> retrieve 3-5 related private articles
-> load cognitive-os + expression-dna + article-playbooks
-> draft
-> run style audit rubric
-> revise until score >= 11/15
-> return draft + title options + self-audit notes
```

Build a model-ready prompt:

```bash
python3 scripts/build_robot_prompt.py \
  --mode write \
  --topic "AI Agent 平台突然又火了，企业是不是都该立刻上" \
  --manifest /path/to/private/corpus/manifest.json \
  --out /tmp/touge-prompt.md
```

## 4. Conversation Robot Flow

```text
user question
-> classify mode: diagnose / reboot / rewrite / write / audit
-> load interaction-protocol
-> optionally retrieve related corpus entries
-> answer with diagnosis, tradeoff, and next action
```

## 5. External Agent Embedding

Generate a context package for the target Agent:

```bash
python3 scripts/build_agent_context.py \
  --scenario qa \
  --channel feishu \
  --agent-name touge-internal-qa-agent \
  --out /tmp/touge-agent-context.md
```

The target Agent should load the generated context as system/developer instructions or as a pinned knowledge file. The Agent, not this skill, owns:

- model calls
- Feishu, WeCom, web, or document adapters
- credentials and permissions
- conversation state and memory
- audit logs and human handoff

For channel integration, use the contract in `references/agent-integration-spec.md`.

## 6. Continuous Corpus Ingestion

Normalize new private material before using it for retrieval or distillation:

```bash
python3 scripts/ingest_corpus.py \
  --source-type wecom_chat \
  --source-id wecom_im_export \
  --input /path/to/private/wecom/export.jsonl \
  --out-dir /path/to/private/evolution-corpus \
  --tag im_chat \
  --tag product_qa \
  --redact
```

The output manifest is private. Use it to retrieve, review, and mine patterns. Only owner-approved distilled rules should be folded back into this repository.

## 7. Capability Extension

Register new capabilities in `configs/capabilities.json`.

Minimum extension workflow:

```text
define capability
-> add or reuse reference files
-> define corpus tags
-> add eval tasks
-> run preflight
-> owner reviews sample outputs
-> widen runtime usage
```

For product-manager Q&A, use `references/product-manager-capability.md` and keep product facts in private product documents.

## 8. Release Checklist

- `python3 scripts/preflight_check.py` passes.
- No raw corpus files are committed.
- No account token, cookie, temporary key, or local private path is committed.
- `evals/tasks.jsonl` has at least five product scenarios.
- `scripts/build_agent_context.py --scenario all --channel generic` can generate an Agent context package.
- `configs/capabilities.json` is valid JSON and every registered reference exists.
- `configs/corpus-sources.example.json` contains examples only, not real private paths.
- A human owner has reviewed 10 generated outputs and marked at least 8 as acceptable.
- Public bot surfaces disclose that this is an AI persona system, not the real person.

## 9. Feedback Loop

Record owner feedback outside the public repository:

```bash
python3 scripts/record_feedback.py \
  --log /path/to/private/feedback.jsonl \
  --task-id write_technical_hype \
  --mode write \
  --prompt "AI Agent 平台突然又火了..." \
  --output /path/to/generated.md \
  --score 4 \
  --notes "像，但结尾太软" \
  --revision-rule "结尾要给边界和停止项"
```

Fold stable revision rules back into references after review.

## 10. Current Non-Automatable Gate

The final quality gate requires the author to score real outputs. Without that human preference loop, the system can be product-ready as a package, but not honestly called a 100% faithful writing/persona robot.
