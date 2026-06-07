#!/usr/bin/env python3
"""Append owner feedback for generated robot outputs.

Store feedback outside the public repo by default. Commit only anonymized rules
after reviewing them.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, help="Private JSONL feedback log path")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", required=True, help="Path to generated output")
    parser.add_argument("--score", required=True, type=int, choices=range(1, 6))
    parser.add_argument("--notes", required=True)
    parser.add_argument("--revision-rule", default="")
    args = parser.parse_args()

    output_path = Path(args.output)
    row = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "task_id": args.task_id,
        "mode": args.mode,
        "prompt": args.prompt,
        "output_path": str(output_path),
        "owner_score": args.score,
        "owner_notes": args.notes,
        "revision_rule": args.revision_rule,
    }
    log_path = Path(args.log)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps({"ok": True, "log": str(log_path), "record": row}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
