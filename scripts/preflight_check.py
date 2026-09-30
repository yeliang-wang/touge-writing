#!/usr/bin/env python3
"""Preflight checks before publishing the public skill repository."""

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN_PATH_PARTS = {'corpus', 'private-corpus', 'raw_html', 'markdown', '.venv', '__pycache__'}
PRIVATE_ROOTS = {'workspace', 'work', 'outputs', 'dist'}
SECRET_PATTERNS = [
    re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    re.compile(r"(?:token=\d+|tempkey=[A-Za-z0-9]|mp_token_\d+)", re.I),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?:Authorization|access_token|appsecret|api_key)\s*[:=]\s*[\"']?(?:Bearer )?[A-Za-z0-9_./+=-]{24,}", re.I),
]


def git_paths(root, *args):
    import subprocess
    return subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z', *args]).decode().split('\0')[:-1]


def audit_public(root=ROOT):
    """Check the index AND public working candidates, including force-added files."""
    import subprocess
    root = Path(root).resolve()
    indexed = set(git_paths(root, '--cached'))
    paths = indexed | set(git_paths(root, '--others', '--exclude-standard'))
    errors = []
    for rel in sorted(paths):
        path = root / rel
        if Path(rel).parts[0] in PRIVATE_ROOTS or any(x in FORBIDDEN_PATH_PARTS for x in Path(rel).parts) or path.suffix.lower() in {'.html', '.docx', '.pdf', '.sqlite'} or (path.name.startswith('.env') and path.name != '.env.example'):
            errors.append('private path in public candidates: ' + rel)
            continue
        if path.is_symlink():
            target = path.resolve()
            if not target.is_relative_to(root) or target.relative_to(root).parts[0] in PRIVATE_ROOTS or any(x in FORBIDDEN_PATH_PARTS for x in target.relative_to(root).parts) or not target.is_file():
                errors.append('unsafe public symlink: ' + rel)
                continue
        bodies = []
        if path.is_file(): bodies.append(('working', path.read_bytes()))
        if rel in indexed:
            bodies.append(('index', subprocess.check_output(['git', '-C', str(root), 'show', ':' + rel])))
        for source, body in bodies:
            text = body.decode('utf-8', errors='replace')
            if any(p.search(text) for p in SECRET_PATTERNS):
                errors.append('sensitive text in ' + source + ': ' + rel)
    return errors


def fail(message):
    print(f"[FAIL] {message}")
    return False


def ok(message):
    print(f"[OK] {message}")
    return True


def check_required_files():
    required = [
        "SKILL.md",
        "AGENTS.md",
        "VERSION",
        ".agents/skills/touge-wechat-writing/SKILL.md",
        ".agents/skills/touge-novel-writing/SKILL.md",
        "shared/author-expression/manifest.json",
        "scripts/backup_workspace.py",
        "scripts/acceptance.py",
        "scripts/export_author_profile.py",
        "README.md",
        "agents/openai.yaml",
        "references/cognitive-os.md",
        "references/expression-dna.md",
        "references/interaction-protocol.md",
        "references/agent-integration-spec.md",
        "references/evolution-spec.md",
        "references/product-manager-capability.md",
        "references/content-deck-playbook.md",
        "references/wechat-public-account-playbook.md",
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
        "evals/outputs/product_qa_missing_context.md",
        "docs/GUIDE",
        "configs/capabilities.json",
        "configs/corpus-sources.example.json",
        "scripts/ingest_corpus.py",
        "scripts/build_agent_context.py",
        "scripts/build_robot_prompt.py",
        "scripts/build_content_deck.py",
        "scripts/private_retriever.py",
        "scripts/record_feedback.py",
        "scripts/style_eval.py",
    ]
    missing = [p for p in required if not (ROOT / p).exists()]
    return ok("required files present") if not missing else fail(f"missing files: {missing}")


def check_public_boundary():
    errors = audit_public()
    return ok('index and public candidates contain no private paths or secret patterns') if not errors else fail('; '.join(errors[:20]))


def check_evals():
    path = ROOT / "evals" / "tasks.jsonl"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        rows.append(json.loads(line))
    modes = {r["mode"] for r in rows}
    if len(rows) < 5:
        return fail("expected at least 5 eval tasks")
    required_modes = {
        "write",
        "conversation",
        "rewrite",
        "reboot",
        "titles",
        "product_qa",
        "content_deck",
        "wechat_public_article",
        "novel_plan",
        "chapter_review",
        "novel_audit",
    }
    if not required_modes.issubset(modes):
        return fail(f"missing eval modes: {modes}")
    return ok("eval suite covers core modes")


def check_capabilities():
    path = ROOT / "configs" / "capabilities.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    seen = set()
    missing = []
    for capability in data.get("capabilities", []):
        cap_id = capability.get("id")
        if not cap_id:
            return fail("capability without id")
        if cap_id in seen:
            return fail(f"duplicate capability id: {cap_id}")
        seen.add(cap_id)
        for ref in capability.get("required_references", []):
            if not (ROOT / ref).exists():
                missing.append(f"{cap_id}:{ref}")
    return ok("capability registry valid") if not missing else fail(f"capability references missing: {missing}")


def main():
    checks = [
        check_required_files(),
        check_public_boundary(),
        check_evals(),
        check_capabilities(),
    ]
    if all(checks):
        print("[OK] preflight passed")
        return 0
    print("[FAIL] preflight failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())
