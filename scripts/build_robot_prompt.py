#!/usr/bin/env python3
"""Build a model-ready prompt from public skill references and optional private retrieval."""

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MODE_REFS = {
    "write": ["cognitive-os.md", "expression-dna.md", "article-playbooks.md", "title-patterns.md", "boundaries.md"],
    "rewrite": ["cognitive-os.md", "expression-dna.md", "interaction-protocol.md", "style-audit-rubric.md", "boundaries.md"],
    "conversation": ["cognitive-os.md", "interaction-protocol.md", "conversation-persona.md", "boundaries.md"],
    "reboot": ["cognitive-os.md", "interaction-protocol.md", "reboot-protocol.md", "boundaries.md"],
    "audit": ["expression-dna.md", "style-audit-rubric.md", "boundaries.md"],
    "titles": ["expression-dna.md", "title-patterns.md", "style-audit-rubric.md", "boundaries.md"],
}


def read_ref(name):
    return (ROOT / "references" / name).read_text(encoding="utf-8")


def retrieve(manifest, query, top_k):
    if not manifest:
        return None
    cmd = [
        "python3",
        str(ROOT / "scripts" / "private_retriever.py"),
        "--manifest",
        manifest,
        "--query",
        query,
        "--top-k",
        str(top_k),
    ]
    return json.loads(subprocess.check_output(cmd, text=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=sorted(MODE_REFS))
    parser.add_argument("--topic", required=True)
    parser.add_argument("--manifest", help="Optional private corpus manifest")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--draft", help="Optional draft file for rewrite/audit")
    parser.add_argument("--out", help="Write prompt to file instead of stdout")
    args = parser.parse_args()

    refs = MODE_REFS[args.mode]
    retrieval = retrieve(args.manifest, args.topic, args.top_k)
    draft = Path(args.draft).read_text(encoding="utf-8") if args.draft else ""

    sections = [
        "# 头哥侃码 Writing/Reboot Robot Prompt",
        f"Mode: {args.mode}",
        f"Task: {args.topic}",
        "",
        "## Operating References",
    ]
    for ref in refs:
        sections.extend([f"### {ref}", read_ref(ref)])

    if retrieval:
        compact = []
        for item in retrieval["results"]:
            compact.append({
                "title": item["title"],
                "publish_time": item["publish_time"],
                "score": item["score"],
                "snippets": item["snippets"],
            })
        sections.extend(["## Private Corpus Grounding", json.dumps(compact, ensure_ascii=False, indent=2)])

    if draft:
        sections.extend(["## User Draft", draft])

    sections.extend([
        "## Required Output",
        "Follow references/robot-spec.md conceptually: preserve facts, avoid fabricated autobiography, and run a style self-audit before finalizing.",
    ])

    output = "\n\n".join(sections).strip() + "\n"
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
