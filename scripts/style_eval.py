#!/usr/bin/env python3
"""Heuristic style gate for Touge writing outputs.

This is not a model judge. It is a deterministic smoke test that catches common
failures: generic AI prose, no stance, no concrete cost, and weak endings.
"""

import argparse
import json
import re
from pathlib import Path


STANCE_MARKERS = [
    "别扯", "醒醒", "放屁", "恕我直言", "说真的", "很遗憾", "抱歉",
    "对不起", "问题是", "这玩意", "不是", "而是", "从来都不是",
    "别傻", "别说", "想多了",
]

CONCRETE_MARKERS = [
    "成本", "代价", "责任", "风险", "故障", "团队", "项目", "老板", "HR",
    "业务", "系统", "公司", "面试", "晋升", "裁员", "客户", "架构", "数据",
]

ANTI_HYPE_MARKERS = [
    "网红", "热词", "趋势", "风口", "伪命题", "骗局", "标签", "口号",
    "跳大神", "装B", "忽悠", "鸡汤", "玄学",
]

AI_SMELL = [
    "随着时代的发展", "在当今社会", "总而言之", "综上所述", "毋庸置疑",
    "赋能", "抓手", "闭环", "生态", "全方位", "多维度", "深度融合",
]

ENDING_MARKERS = ["建议", "记住", "别", "不要", "先", "学会", "尝试", "停止", "开始"]


def count_any(text, markers):
    return sum(text.count(m) for m in markers)


def score_position(text):
    count = count_any(text, STANCE_MARKERS)
    if count >= 5:
        return 3
    if count >= 2:
        return 2
    if count == 1 or "？" in text[:160] or "?" in text[:160]:
        return 1
    return 0


def score_concrete_cost(text):
    count = count_any(text, CONCRETE_MARKERS)
    digit = bool(re.search(r"\d", text))
    if count >= 8 and digit:
        return 3
    if count >= 5:
        return 2
    if count >= 2:
        return 1
    return 0


def score_anti_hype(text):
    count = count_any(text, ANTI_HYPE_MARKERS)
    if count >= 3:
        return 3
    if count >= 1 and count_any(text, STANCE_MARKERS) >= 2:
        return 2
    if count >= 1:
        return 1
    return 0


def score_voice(text):
    stance = count_any(text, STANCE_MARKERS)
    ai = count_any(text, AI_SMELL)
    colloquial = count_any(text, ["你", "我", "咱", "哥们", "这事", "这类人", "别"])
    if ai >= 3:
        return 0
    if stance >= 4 and colloquial >= 8:
        return 3
    if stance >= 2 and colloquial >= 4:
        return 2
    if stance >= 1 or colloquial >= 3:
        return 1
    return 0


def score_ending(text):
    tail = text[-320:]
    count = count_any(tail, ENDING_MARKERS)
    if count >= 3 and not any(x in tail for x in ["综上所述", "总而言之"]):
        return 3
    if count >= 1:
        return 2
    if "？" in tail or "?" in tail:
        return 1
    return 0


def verdict(total):
    if total >= 14:
        return "strong_match"
    if total >= 11:
        return "close"
    if total >= 6:
        return "partial"
    return "unlike"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Text or Markdown draft to evaluate")
    args = parser.parse_args()
    text = Path(args.file).read_text(encoding="utf-8")
    scores = {
        "position": score_position(text),
        "concrete_cost": score_concrete_cost(text),
        "anti_hype": score_anti_hype(text),
        "voice_texture": score_voice(text),
        "ending": score_ending(text),
    }
    total = sum(scores.values())
    smells = [m for m in AI_SMELL if m in text]
    print(json.dumps({
        "total": total,
        "verdict": verdict(total),
        "scores": scores,
        "ai_smell_markers": smells,
        "pass": total >= 11 and not smells,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
