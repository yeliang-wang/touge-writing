#!/usr/bin/env python3
"""Build an installable context package for embedding this skill into an AI Agent."""

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

BASE_FILES = [
    "SKILL.md",
    "references/robot-spec.md",
    "references/agent-integration-spec.md",
    "references/evolution-spec.md",
    "references/cognitive-os.md",
    "references/interaction-protocol.md",
    "references/boundaries.md",
    "configs/capabilities.json",
]

SCENARIO_FILES = {
    "all": [
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
    args = parser.parse_args()

    paths = unique_paths(BASE_FILES + SCENARIO_FILES[args.scenario])

    sections = [
        "# touge-writing-reboot-skill Agent Context",
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
