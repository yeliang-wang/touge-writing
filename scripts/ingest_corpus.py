#!/usr/bin/env python3
"""Normalize private corpus sources into an evolution-corpus manifest.

This script creates private training/retrieval material outside the public repo.
It does not distill rules by itself; it gives later retrieval and review a stable
input format.
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SUPPORTED_SOURCE_TYPES = {
    "wechat_article",
    "wecom_chat",
    "feishu_chat",
    "product_doc",
    "meeting_note",
    "feedback",
    "draft",
}

PII_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"(token|cookie|secret|password|passwd|tempkey)\s*[:=]", re.I),
]


def fail(message):
    print(f"[FAIL] {message}", file=sys.stderr)
    return 1


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def slugify(value):
    value = re.sub(r"\s+", "-", value.strip().lower())
    value = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff._-]+", "-", value)
    return value.strip("-")[:80] or "record"


def read_text_file(path):
    return path.read_text(encoding="utf-8", errors="ignore").strip()


def iter_text_records(input_path):
    if input_path.is_dir():
        for path in sorted(input_path.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
                text = read_text_file(path)
                if text:
                    yield {"title": path.stem, "text": text, "source_path": str(path)}
        return

    suffix = input_path.suffix.lower()
    if suffix in {".md", ".txt"}:
        text = read_text_file(input_path)
        if text:
            yield {"title": input_path.stem, "text": text, "source_path": str(input_path)}
    elif suffix == ".jsonl":
        for idx, line in enumerate(input_path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            text = str(row.get("text") or row.get("content") or row.get("message") or "").strip()
            if text:
                yield {
                    "title": row.get("title") or row.get("conversation_id") or f"{input_path.stem}-{idx}",
                    "text": text,
                    "speaker": row.get("speaker") or row.get("sender") or "unknown",
                    "timestamp": row.get("timestamp") or row.get("time"),
                    "source_path": str(input_path),
                    "metadata": row,
                }
    elif suffix == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8", errors="ignore"))
        rows = data if isinstance(data, list) else data.get("records") or data.get("messages") or data.get("items") or []
        for idx, row in enumerate(rows, start=1):
            text = str(row.get("text") or row.get("content") or row.get("message") or "").strip()
            if text:
                yield {
                    "title": row.get("title") or row.get("conversation_id") or f"{input_path.stem}-{idx}",
                    "text": text,
                    "speaker": row.get("speaker") or row.get("sender") or "unknown",
                    "timestamp": row.get("timestamp") or row.get("time"),
                    "source_path": str(input_path),
                    "metadata": row,
                }
    elif suffix == ".csv":
        with input_path.open(newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, start=1):
                text = str(row.get("text") or row.get("content") or row.get("message") or "").strip()
                if text:
                    yield {
                        "title": row.get("title") or row.get("conversation_id") or f"{input_path.stem}-{idx}",
                        "text": text,
                        "speaker": row.get("speaker") or row.get("sender") or "unknown",
                        "timestamp": row.get("timestamp") or row.get("time"),
                        "source_path": str(input_path),
                        "metadata": row,
                    }
    else:
        raise ValueError(f"unsupported input type: {input_path}")


def redact_text(text):
    redacted = text
    for pattern in PII_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-type", required=True, choices=sorted(SUPPORTED_SOURCE_TYPES))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--input", required=True, help="File or directory to ingest")
    parser.add_argument("--out-dir", required=True, help="Private output directory")
    parser.add_argument("--visibility", choices=["private", "public_derived"], default="private")
    parser.add_argument("--tag", action="append", default=[], help="Additional tag; can be repeated")
    parser.add_argument("--redact", action="store_true", help="Redact common phone/email/secret patterns")
    args = parser.parse_args()

    input_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    if not input_path.exists():
        return fail(f"input not found: {input_path}")

    docs_dir = out_dir / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.jsonl"

    records = []
    now = datetime.now(timezone.utc).isoformat()
    for idx, item in enumerate(iter_text_records(input_path), start=1):
        text = item["text"]
        if args.redact:
            text = redact_text(text)
        text_hash = sha256_text(text)
        record_id = f"{slugify(args.source_id)}-{idx:06d}-{text_hash[:10]}"
        text_rel = Path("documents") / f"{record_id}.md"
        (out_dir / text_rel).write_text(text + "\n", encoding="utf-8")
        tags = sorted(set([args.source_type, *args.tag]))
        record = {
            "id": record_id,
            "source_id": args.source_id,
            "source_type": args.source_type,
            "visibility": args.visibility,
            "title": item.get("title") or record_id,
            "speaker": item.get("speaker") or "unknown",
            "timestamp": item.get("timestamp"),
            "tags": tags,
            "text_path": str(text_rel),
            "text_hash": text_hash,
            "char_count": len(text),
            "allowed_uses": ["private_retrieval", "distillation_review"],
            "forbidden_uses": ["public_commit_raw_text"],
            "ingested_at": now,
            "source_path": item.get("source_path"),
        }
        records.append(record)

    with manifest_path.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(json.dumps({
        "ok": len(records),
        "out_dir": str(out_dir),
        "manifest": str(manifest_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
