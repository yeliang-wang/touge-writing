#!/usr/bin/env python3
"""Build an installable context package for embedding this skill into an AI Agent."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BASE_FILES = [
    "SKILL.md",
    "shared/author-expression/PROFILE.md",
    "shared/author-expression/rubric.md",
    "shared/author-expression/language.md",
    "shared/author-expression/lexicon.yaml",
    "references/robot-spec.md",
    "references/agent-integration-spec.md",
    "references/evolution-spec.md",
    "references/cognitive-os.md",
    "references/interaction-protocol.md",
    "references/boundaries.md",
    "configs/capabilities.json",
]

SCENARIO_FILES = {
    "wechat": [".agents/skills/touge-wechat-writing/SKILL.md", "references/wechat-public-account-playbook.md", "references/article-playbooks.md", "references/title-patterns.md", "shared/author-expression/wechat-rubric.md", "docs/external-services/wechat.md"],
    "novel": [".agents/skills/touge-novel-writing/SKILL.md", ".agents/skills/touge-novel-writing/references/workflow.md", "templates/book-plan.md", "templates/chapter-plan.md", "docs/external-services/tencent-docs.md"],
    "all": [
        ".agents/skills/touge-wechat-writing/SKILL.md",
        ".agents/skills/touge-novel-writing/SKILL.md",
        ".agents/skills/touge-novel-writing/references/workflow.md",
        "references/wechat-public-account-playbook.md",
        "docs/external-services/tencent-docs.md",
        "docs/external-services/wechat.md",
        "references/expression-dna.md",
        "references/article-playbooks.md",
        "references/title-patterns.md",
        "references/conversation-persona.md",
        "references/reboot-protocol.md",
        "references/style-audit-rubric.md",
        "references/productization-runbook.md",
        "references/product-manager-capability.md",
    ],
    "writing": [
        "references/expression-dna.md",
        "references/article-playbooks.md",
        "references/title-patterns.md",
        "references/style-audit-rubric.md",
    ],
    "qa": [
        "references/conversation-persona.md",
        "references/reboot-protocol.md",
        "references/style-audit-rubric.md",
    ],
    "audit": [
        "references/expression-dna.md",
        "references/style-audit-rubric.md",
    ],
    "product_pm": [
        "references/conversation-persona.md",
        "references/product-manager-capability.md",
        "references/style-audit-rubric.md",
    ],
    "evolution": [
        "references/evolution-spec.md",
        "references/productization-runbook.md",
        "configs/corpus-sources.example.json",
    ],
}

CHANNEL_NOTES = {
    "generic": "Use the unified inbound and reply envelopes. Keep channel logic outside the skill.",
    "feishu": "Use Feishu only as a ChannelAdapter. Normalize events before the Agent calls the skill.",
    "wecom": "Use WeCom only as a ChannelAdapter. Keep external-contact boundaries auditable.",
    "docs": "Use the document platform as a destination adapter after draft generation and review.",
}


def read_file(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def unique_paths(paths):
    seen = set()
    result = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            result.append(path)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=sorted(SCENARIO_FILES), default="all")
    parser.add_argument("--channel", choices=sorted(CHANNEL_NOTES), default="generic")
    parser.add_argument("--agent-name", default="touge-writing-agent")
    parser.add_argument("--out", help="Write context to file instead of stdout")
    parser.add_argument("--capability", action="append", default=[], help="Explicit method ID@version; repeat as needed")
    parser.add_argument("--phase", choices=['plan', 'draft', 'review', 'revise', 'title'])
    args = parser.parse_args()

    paths = unique_paths(BASE_FILES + SCENARIO_FILES[args.scenario])
    from capability_catalog import resolve
    kind = args.scenario if args.scenario in {'wechat', 'novel'} else None
    selected = list(args.capability)
    if args.phase:
        if not kind:
            parser.error('--phase requires --scenario wechat or novel')
        recipes = json.loads(read_file('.agents/skills/touge-' + kind + '-writing/references/recipes.json'))
        selected += recipes[args.phase]
    paths += [r['path'] for r in resolve(list(dict.fromkeys(selected)), kind)]
    paths = unique_paths(paths)

    sections = [
        "# touge-writing Agent Context",
        "",
        f"Agent name: {args.agent_name}",
        f"Scenario: {args.scenario}",
        f"Channel: {args.channel}",
        "",
        "## Integration Rule",
        CHANNEL_NOTES[args.channel],
        "",
        "The skill is installed as Agent context. It is not the service runtime. The Agent owns model calls, channel adapters, permissions, audit logs, and human handoff.",
        "",
        "## Loaded Files",
        "\n".join(f"- `{path}`" for path in paths),
    ]

    for path in paths:
        sections.extend([
            "",
            f"## File: {path}",
            "",
            read_file(path).strip(),
        ])

    output = "\n".join(sections).strip() + "\n"
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
