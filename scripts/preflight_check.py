#!/usr/bin/env python3
"""Preflight checks before publishing the public skill repository."""

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN_PATH_PARTS = {
    "corpus",
    "private-corpus",
    "raw_html",
    "markdown",
}

SECRET_PATTERNS = [
    re.compile(r"token=\d+"),
    re.compile(r"tempkey=", re.I),
    re.compile(r"cookie", re.I),
    re.compile(r"/Users/[^\\s)]+"),
    re.compile(r"mp_token_[0-9]+"),
]


def fail(message):
    print(f"[FAIL] {message}")
    return False


def ok(message):
    print(f"[OK] {message}")
    return True


def check_required_files():
    required = [
        "SKILL.md",
        "README.md",
        "agents/openai.yaml",
        "references/cognitive-os.md",
        "references/expression-dna.md",
        "references/interaction-protocol.md",
        "references/robot-spec.md",
        "references/evaluation-report.md",
        "references/style-audit-rubric.md",
        "references/productization-runbook.md",
        "evals/tasks.jsonl",
        "evals/outputs/write_technical_hype.md",
        "evals/outputs/career_reply_age.md",
        "evals/outputs/rewrite_ai_smell.md",
        "evals/outputs/reboot_low_point.md",
        "evals/outputs/title_set.md",
        "scripts/build_robot_prompt.py",
        "scripts/private_retriever.py",
        "scripts/record_feedback.py",
        "scripts/style_eval.py",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    return ok("required files present") if not missing else fail(f"missing files: {missing}")


def check_no_private_files():
    bad = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file() and any(part in FORBIDDEN_PATH_PARTS for part in path.parts):
            bad.append(str(path.relative_to(ROOT)))
        if path.suffix.lower() == ".html":
            bad.append(str(path.relative_to(ROOT)))
    return ok("no private corpus files") if not bad else fail(f"private files found: {bad[:20]}")


def check_no_secret_text():
    hits = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.name == "preflight_check.py":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pat in SECRET_PATTERNS:
            if pat.search(text):
                # Safety docs intentionally name forbidden examples.
                if path.name in {"boundaries.md", "productization-runbook.md"} and pat.pattern.lower() in {"cookie", "tempkey="}:
                    continue
                hits.append(f"{path.relative_to(ROOT)}:{pat.pattern}")
    return ok("no secret-like text") if not hits else fail(f"secret-like text found: {hits[:20]}")


def check_evals():
    path = ROOT / "evals" / "tasks.jsonl"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        rows.append(json.loads(line))
    modes = {r["mode"] for r in rows}
    if len(rows) < 5:
        return fail("expected at least 5 eval tasks")
    if not {"write", "conversation", "rewrite", "reboot", "titles"}.issubset(modes):
        return fail(f"missing eval modes: {modes}")
    return ok("eval suite covers core modes")


def main():
    checks = [
        check_required_files(),
        check_no_private_files(),
        check_no_secret_text(),
        check_evals(),
    ]
    if all(checks):
        print("[OK] preflight passed")
        return 0
    print("[FAIL] preflight failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
