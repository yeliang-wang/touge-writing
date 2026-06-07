# Agent Integration Spec

This document defines how to install or embed `touge-writing-reboot-skill` into an external AI Agent. The skill is a capability package, not a standalone service.

## Boundary

The skill owns:

- Style rules, worldview, expression mechanics, and reboot protocol.
- Mode routing hints for writing, rewriting, Q&A, self-reflection, titles, and style audit.
- Prompt assembly references and output contracts.
- Safety, authenticity, and private-corpus boundaries.

The external Agent owns:

- Model provider selection and API calls.
- Conversation state, memory, permissions, audit logs, and human handoff.
- Channel adapters such as Feishu, WeCom, Slack, web chat, or document systems.
- Tool execution, private retrieval, rate limits, deployment, and observability.

## Reference Architecture

```text
Feishu / WeCom / Web / Docs
-> Channel Adapter
-> AI Agent Runtime
-> touge-writing-reboot-skill context
-> optional private corpus retriever
-> policy, audit, and human handoff
-> Channel Adapter
```

Keep channel logic provider-neutral. Use a shared IM boundary first, then implement provider-specific adapters.

```text
ChannelAdapter
  - FeishuAdapter
  - WeComAdapter
  - WebAdapter
  - DocumentAdapter
```

Do not put Feishu-only concepts into the core skill or the core Agent contract.

## Installable Context Package

An Agent should load these files as system or developer context:

- `SKILL.md`
- `references/robot-spec.md`
- `references/agent-integration-spec.md`
- `references/cognitive-os.md`
- `references/interaction-protocol.md`
- `references/boundaries.md`

Scenario-specific references:

- writing: `expression-dna.md`, `article-playbooks.md`, `title-patterns.md`
- Q&A: `conversation-persona.md`, `reboot-protocol.md`
- style audit: `style-audit-rubric.md`
- product operations: `productization-runbook.md`

Use `scripts/build_agent_context.py` to produce a compact installable context file for the target Agent.

## Unified Inbound Envelope

Channel adapters should normalize incoming messages before they reach the Agent.

```json
{
  "channel": "feishu",
  "conversation_id": "chat-id-or-thread-id",
  "sender_id": "user-id",
  "sender_role": "owner | trusted_user | external_user | unknown",
  "text": "用户原始问题",
  "attachments": [],
  "timestamp": "2026-06-07T10:00:00+08:00",
  "metadata": {
    "tenant_id": "optional",
    "message_id": "optional",
    "reply_to": "optional"
  }
}
```

## Unified Reply Envelope

The Agent should produce a normalized reply before the channel adapter sends it.

```json
{
  "reply_type": "answer | draft | ask_clarification | handoff | reject",
  "mode": "conversation | write | rewrite | reboot | audit | titles",
  "text": "面向用户的回复",
  "confidence": 0.82,
  "need_human_review": false,
  "risk_tags": ["career_advice"],
  "audit_note": "为什么可以自动回复，或为什么需要人工接管"
}
```

## Mode Routing

Default routing:

- Question about career, technology direction, architecture, organization, or entrepreneurship: `conversation`
- Request to draft an article, speech, reply, post, or long-form opinion: `write`
- Request to improve an existing draft: `rewrite`
- Request about personal low point, reset, stuck state, or self-calibration: `reboot`
- Request to judge whether text sounds like 头哥侃码: `audit`
- Request for headlines or naming: `titles`

When the user asks for factual, legal, medical, financial, or current-events claims, the Agent must verify sources outside this skill before answering.

## Automation Levels

Use explicit automation levels when connecting to live channels.

```text
L1 Draft only
Agent generates a draft. Human confirms before sending.

L2 Guarded auto-reply
Agent auto-replies only to low-risk known scenarios. High-risk cases become handoff.

L3 Stable automation
Agent can answer approved recurring scenarios automatically with logs, metrics, and rollback.
```

Recommended default: L1 for writing, L2 for low-risk internal Q&A, no L3 until real acceptance data exists.

## Feishu Adapter

Feishu integration should stay outside this repository. The adapter should:

- Receive Feishu events and convert them to the unified inbound envelope.
- Preserve thread or chat identity as `conversation_id`.
- Attach sender role from the Agent's permission system.
- Send normalized replies back to Feishu.
- Support human handoff by tagging the owner or routing to a review chat.

## WeCom Adapter

WeCom integration should follow the same contract:

- Convert WeCom callback events to the unified inbound envelope.
- Avoid WeCom-specific fields in the skill context.
- Send replies only after Agent policy allows it.
- Keep customer, employee, and external-contact boundaries auditable.

## Document Destination

For document-first workflows such as writing to a Shimo directory, treat the document platform as a destination adapter:

```text
User request
-> Agent generates draft with this skill
-> human review or policy approval
-> DocumentAdapter writes to target directory
-> Agent returns document link and audit note
```

The skill should not store document credentials. The Agent or destination adapter owns credentials and permissions.

## Minimum Production Checklist

- The Agent can load the generated context package.
- Channel adapters use the unified inbound and reply envelopes.
- Private corpus retrieval is optional and never exposed verbatim.
- L1/L2/L3 automation level is configured per scenario.
- Human handoff exists for high-risk or low-confidence cases.
- Every live reply is logged with input, mode, output, confidence, and handoff decision.
- The owner has reviewed enough real outputs before widening automation.
