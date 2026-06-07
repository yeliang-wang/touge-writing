# Robot Spec

## Product Name

头哥侃码 Writing/Reboot Robot

## Jobs To Be Done

- Draft essays in the author's public writing style.
- Rewrite generic drafts into a sharper, more grounded voice.
- Answer career, technical leadership, organization, entrepreneurship, and personal reboot questions.
- Audit whether a draft matches the style system.
- Provide an installable context contract for an external AI Agent.
- Support registered custom capabilities such as product-manager Q&A.

## Inputs

```json
{
  "mode": "write | rewrite | diagnose | conversation | reboot | audit | titles | product_qa",
  "topic": "string",
  "user_context": "optional string",
  "draft": "optional string",
  "sharpness": "low | medium | high",
  "retrieval": {
    "enabled": true,
    "top_k": 5
  }
}
```

## Internal Context

Always available:

- `SKILL.md`
- `references/cognitive-os.md`
- `references/expression-dna.md`
- `references/interaction-protocol.md`
- `references/agent-integration-spec.md`
- `references/evolution-spec.md`
- `references/boundaries.md`
- `configs/capabilities.json`

Mode-specific:

- write: `article-playbooks.md`, `title-patterns.md`
- conversation: `conversation-persona.md`
- reboot: `reboot-protocol.md`
- audit: `style-audit-rubric.md`
- product_qa: `product-manager-capability.md`

Optional private grounding:

- Top 3-5 results from `scripts/private_retriever.py`

## Output Contract

### Write

```json
{
  "title_options": ["..."],
  "draft": "...",
  "style_self_audit": {
    "position": "...",
    "cost_or_tradeoff": "...",
    "risk": "..."
  }
}
```

### Conversation

```json
{
  "diagnosis": "...",
  "tradeoff": "...",
  "reply": "...",
  "next_actions": ["..."]
}
```

### Agent Reply

```json
{
  "reply_type": "answer | draft | ask_clarification | handoff | reject",
  "mode": "conversation | write | rewrite | reboot | audit | titles",
  "text": "...",
  "confidence": 0.82,
  "need_human_review": false,
  "risk_tags": ["..."],
  "audit_note": "..."
}
```

### Product Q&A

```json
{
  "question_reframe": "...",
  "known_facts": ["..."],
  "missing_facts": ["..."],
  "tradeoff": "...",
  "recommendation": "...",
  "next_actions": ["..."],
  "need_human_review": false
}
```

### Audit

```json
{
  "verdict": "unlike | partial | close | strong_match",
  "problems": ["..."],
  "rewrite_plan": ["..."],
  "revised_text": "..."
}
```

## Quality Gates

- No fabricated autobiography.
- No raw corpus quotation beyond short, user-approved snippets.
- Style score >= 11/15 for publishable drafts.
- For `high` sharpness, the target must be an idea, system, behavior, or public claim, not a vulnerable person.
- High-stakes factual claims require source verification outside this skill.

## Human Preference Loop

Every accepted/rejected output should be logged as:

```json
{
  "task_id": "...",
  "mode": "...",
  "prompt": "...",
  "output_path": "...",
  "owner_score": 1,
  "owner_notes": "哪里像，哪里不像",
  "revision_rule": "需要写回哪条规则"
}
```

Accepted learnings should be folded back into:

- `expression-dna.md`
- `interaction-protocol.md`
- `style-audit-rubric.md`
- `boundaries.md`
