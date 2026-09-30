#!/usr/bin/env python3
"""Report mechanically detectable prose issues; never claim factual verification."""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def check(text, repeat_window=12, dash_limit=None):
    if repeat_window < 4:
        raise ValueError('Repeat window must be at least 4')
    # Exclude explicit Markdown metadata blocks, not story paragraphs.
    body = '\n'.join(line for line in text.splitlines() if not line.startswith(('#', '>')))
    chars = re.findall(r'[\u4e00-\u9fff]', body)
    normalized = ''.join(chars)
    windows = defaultdict(list)
    for i in range(max(0, len(normalized) - repeat_window + 1)):
        windows[normalized[i:i+repeat_window]].append(i)
    repeats = [{'text': k, 'positions': v} for k, v in windows.items() if len(v) > 1]
    leaks = []
    for i, line in enumerate(text.splitlines(), 1):
        # Headings and quoted passages can also contain outline terminology.
        # Findings are review clues, including possible metadata false positives.
        for marker in ['幕一', '幕二', '幕三', '幕四', '幕五', '幕六', '楔子', '收束', '配套方案', '工作区']:
            if marker in line: leaks.append({'line': i, 'marker': marker})
    density = body.count('——') / len(chars) * 100 if chars else 0
    return {'chinese_characters': len(chars), 'dash_density_per_100': round(density, 4),
            'dash_limit_exceeded': dash_limit is not None and density > dash_limit,
            'repeated_windows': repeats, 'structural_word_findings': leaks,
            'facts_verified': False, 'meaning': '机械扫描线索，需按作品约定审阅；不代表事实或文学质量验收。'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path); p.add_argument('--repeat-window', type=int, default=12)
    p.add_argument('--dash-limit', type=float); p.add_argument('--out', type=Path)
    a = p.parse_args(); result = check(a.file.read_text(), a.repeat_window, a.dash_limit)
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if a.out:
        from workspace_lib import atomic_text
        atomic_text(a.out, output)
    else: print(output)


if __name__ == '__main__':
    main()
