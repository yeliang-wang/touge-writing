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
- Produce content packages that include an article, WPS-compatible PPTX, and Markdown talk script.

## Inputs

```json
{
  "mode": "write | rewrite | diagnose | conversation | reboot | audit | titles | product_qa | content_deck",
  "topic": "string",
  "user_context": "optional string",
  "draft": "optional string",
  "output_formats": ["article_md", "slide_plan_json", "pptx", "speaker_md"],
  "deck": {
    "slides": 8,
    "audience": "optional string",
    "scenario": "internal sharing | public talk | courseware | product explainer",
    "needs_files": true
  },
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
- content_deck: `content-deck-playbook.md`, `article-playbooks.md`, `style-dna.md`

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

### Content Deck

```json
{
  "title_options": ["..."],
  "article_markdown": "optional full article",
  "slide_plan": {
    "title": "...",
    "audience": "...",
    "scenario": "...",
    "slides": [
      {
        "title": "...",
        "subtitle": "...",
        "kind": "cover | claim | contrast | bullets | sequence | architecture | lifecycle | summary",
        "points": ["..."],
        "talk": "One natural oral paragraph in the author's style."
      }
    ],
    "takeaways": ["..."]
  },
  "files": {
    "pptx": "optional path",
    "speaker_markdown": "optional path",
    "contact_sheet": "optional path",
    "manifest": "optional path"
  },
  "style_self_audit": {
    "position": "...",
    "cost_or_tradeoff": "...",
    "generic_slide_risk": "..."
  }
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
- Content decks must preserve the argument spine; do not turn sharp judgment into generic training bullets.

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
