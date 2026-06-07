# Evolution Spec

This repository supports continuous evolution through private corpus ingestion, distilled rule updates, capability registration, and evaluation. Raw private material should stay outside the public repository.

## Evolution Loop

```text
new source
-> normalize into private evolution corpus
-> retrieve or sample representative records
-> mine stable patterns
-> update references or capability config
-> add eval tasks
-> run preflight and style checks
-> owner review
```

Do not treat every new message as a permanent rule. Stable behavior must appear repeatedly or be explicitly approved by the owner.

## Corpus Source Types

Supported source categories:

- `wechat_article`: public article exports and article metadata.
- `wecom_chat`: Enterprise WeChat IM export.
- `feishu_chat`: Feishu IM export.
- `product_doc`: product documentation, PRD, FAQ, support notes, architecture docs.
- `meeting_note`: meeting summary or decision record.
- `feedback`: owner feedback on generated outputs.
- `draft`: unpublished draft or edited article.

Private source material should be normalized into a private directory such as:

```text
/path/to/private/evolution-corpus/
├── manifest.jsonl
└── documents/
```

The public repo should contain only schemas, scripts, aggregate findings, and owner-approved distilled rules.

## Normalized Corpus Record

Every ingested item should become a JSON object:

```json
{
  "id": "stable-record-id",
  "source_id": "wecom_im_export",
  "source_type": "wecom_chat",
  "visibility": "private",
  "title": "optional title",
  "speaker": "owner | user | customer | teammate | unknown",
  "timestamp": "optional ISO-8601 time",
  "tags": ["im_chat", "career_qa"],
  "text_path": "documents/stable-record-id.md",
  "text_hash": "sha256",
  "char_count": 1200,
  "allowed_uses": ["conversation_style", "private_retrieval"],
  "forbidden_uses": ["public_commit_raw_text"]
}
```

## Capability Registry

Capabilities are registered in `configs/capabilities.json`.

Each capability should define:

- `id`: stable machine-readable name.
- `display_name`: human-facing capability name.
- `description`: what job it performs.
- `modes`: runtime modes this capability can route to.
- `required_references`: files the Agent should load for this capability.
- `optional_corpus_tags`: private corpus tags that can improve grounding.

When adding a capability such as "某某产品的产品经理", do not hard-code the product into `SKILL.md`. Add a capability entry, add a reference file if the behavior is general, and keep product-specific facts in private product docs.

## Product Manager Capability Pattern

For a product-manager capability, split responsibilities:

```text
skill layer:
  - product judgment style
  - question routing
  - tradeoff and prioritization framework
  - answer contract

private knowledge layer:
  - product docs
  - customer feedback
  - roadmap
  - pricing or commercial rules
  - support and incident history

host Agent:
  - retrieval
  - permission
  - source citation
  - human handoff
```

The skill may teach the Agent how to reason like the owner. It should not pretend to know a product roadmap unless the Agent retrieves it from a production knowledge source.

## IM Chat Ingestion Rules

IM exports are useful for conversation style and knowledge Q&A, but they are also high risk.

Before using IM data:

- Remove account tokens, mobile numbers, emails, addresses, and private identifiers.
- Separate owner messages from other people's messages.
- Keep raw exports in a private directory.
- Use third-party messages only for intent and context, not for public examples.
- Do not commit raw chat records to this repository.
- Prefer distilled patterns such as "how the owner rejects vague questions" over copied dialogue.

## Distillation Targets

After enough new corpus is collected, update the smallest relevant file:

- New conversation behavior: `references/conversation-persona.md`
- New writing pattern: `references/expression-dna.md` or `references/article-playbooks.md`
- New safety boundary: `references/boundaries.md`
- New product role capability: `references/product-manager-capability.md`
- New runtime mode or output contract: `references/robot-spec.md`
- New Agent integration requirement: `references/agent-integration-spec.md`

## Evaluation Gate

Every capability should have eval tasks before it is treated as production-ready.

Minimum gate:

- 5 representative tasks for the capability.
- 2 rejection or handoff cases.
- 3 owner-reviewed outputs.
- No raw private text in public eval files.
- Clear rule for when retrieval is required.

## Public Commit Rule

Allowed in the public repository:

- schemas
- scripts
- aggregate counts
- distilled rules
- synthetic examples
- owner-approved public links

Not allowed:

- raw IM exports
- private article bodies
- customer names
- credentials
- private roadmap facts
- unapproved third-party conversation excerpts
