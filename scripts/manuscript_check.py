#!/usr/bin/env python3
"""Report mechanically detectable prose issues; never claim factual verification."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


def _line_ranges(value, total_lines, label):
    """Validate closed, 1-based ranges and merge overlaps without double counting."""
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError(label + ' must be an array of line-range pairs')
    ranges = []
    for pair in value:
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(label + ' needs START:END pairs')
        start, end = pair
        if type(start) is not int or type(end) is not int:
            raise ValueError(label + ' boundaries must be integers')
        if start < 1 or end < start or end > total_lines:
            raise ValueError(label + ' is outside the document or reversed')
        ranges.append((start, end))
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def _numbers(ranges):
    return {number for start, end in ranges for number in range(start, end + 1)}


def _compress(numbers):
    ranges = []
    for number in sorted(numbers):
        if ranges and number == ranges[-1][1] + 1:
            ranges[-1][1] = number
        else:
            ranges.append([number, number])
    return ranges


def _scope(text, body_policy, body_ranges, exclude_ranges):
    lines = text.splitlines()
    if body_policy == 'legacy':
        if body_ranges is not None or exclude_ranges is not None:
            raise ValueError('Line ranges require body_policy=explicit')
        # Reproduce the original heuristic exactly, including its quote exclusion.
        selected = {i for i, line in enumerate(lines, 1) if not line.startswith(('#', '>'))}
        ranges = [[1, len(lines)]] if lines else []
        exclusions = _compress(set(range(1, len(lines) + 1)) - selected)
        boundary = 'concatenated_body'
    elif body_policy == 'explicit':
        ranges = _line_ranges(body_ranges, len(lines), 'Body range')
        if not ranges:
            raise ValueError('Explicit policy requires at least one body range')
        exclusions = _line_ranges(exclude_ranges, len(lines), 'Exclude range')
        selected = _numbers(ranges)
        excluded = _numbers(exclusions)
        if not excluded <= selected:
            raise ValueError('Exclude ranges must be within selected body ranges')
        selected -= excluded
        if not selected:
            raise ValueError('Explicit body selection is empty after exclusions')
        boundary = 'within_retained_paragraphs'
    else:
        raise ValueError('Unknown body policy; choose legacy or explicit')
    body = '\n'.join(lines[i-1] for i in sorted(selected))
    report = {'policy': body_policy, 'line_numbering': '1-based, inclusive',
              'input_text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
              'total_lines': len(lines), 'body_ranges': ranges, 'exclude_ranges': exclusions,
              'retained_ranges': _compress(selected), 'repeated_window_scope': boundary,
              'repeat_position_unit': '0-based Han-character offset in retained body',
              'interpretation': ('Legacy excludes every line starting with # or >; no semantic classification.'
                                 if body_policy == 'legacy' else
                                 'Only the selected ranges define body; headings, notes and quotations are not auto-classified.')}
    return lines, selected, body, report


def _paragraphs(lines, selected):
    """Do not create repeat windows across blank paragraphs or omitted lines."""
    paragraph = []
    previous = None
    for number in sorted(selected):
        line = lines[number-1]
        blank = not line.strip() or re.fullmatch(r'\s*(?:>\s*)+', line) is not None
        if blank or (previous is not None and number != previous + 1):
            if paragraph:
                yield '\n'.join(paragraph)
                paragraph = []
        if not blank:
            paragraph.append(line)
        previous = number
    if paragraph:
        yield '\n'.join(paragraph)


def check(text, repeat_window=12, dash_limit=None, *, body_policy='legacy',
          body_ranges=None, exclude_ranges=None):
    if repeat_window < 4:
        raise ValueError('Repeat window must be at least 4')
    lines, selected, body, scope = _scope(text, body_policy, body_ranges, exclude_ranges)
    chars = re.findall(r'[\u4e00-\u9fff]', body)
    windows = defaultdict(list)
    parts = [body] if body_policy == 'legacy' else _paragraphs(lines, selected)
    offset = 0
    for part in parts:
        normalized = ''.join(re.findall(r'[\u4e00-\u9fff]', part))
        for i in range(max(0, len(normalized) - repeat_window + 1)):
            windows[normalized[i:i+repeat_window]].append(offset + i)
        offset += len(normalized)
    repeats = [{'text': k, 'positions': v} for k, v in windows.items() if len(v) > 1]
    leaks = []
    for i, line in enumerate(lines, 1):
        # These are full-document clues, including metadata false positives.
        for marker in ['幕一', '幕二', '幕三', '幕四', '幕五', '幕六', '楔子', '收束', '配套方案', '工作区']:
            if marker in line:
                leaks.append({'line': i, 'marker': marker})
    density = body.count('——') / len(chars) * 100 if chars else 0
    return {'chinese_characters': len(chars), 'dash_density_per_100': round(density, 4),
            'dash_limit_exceeded': dash_limit is not None and density > dash_limit,
            'repeated_windows': repeats, 'structural_word_findings': leaks,
            'body_scope': scope, 'structural_word_findings_scope': 'full_text',
            'facts_verified': False, 'meaning': '机械扫描线索，需按作品约定审阅；不代表事实或文学质量验收。'}


def _cli_range(value):
    if not re.fullmatch(r'[0-9]+:[0-9]+', value):
        raise argparse.ArgumentTypeError('Use START:END, with 1-based inclusive line numbers')
    return tuple(map(int, value.split(':')))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    p.add_argument('--repeat-window', type=int, default=12)
    p.add_argument('--dash-limit', type=float)
    p.add_argument('--out', type=Path)
    p.add_argument('--body-policy', choices=['legacy', 'explicit'], default='legacy',
                   help='legacy reproduces old counting; explicit uses only supplied line ranges')
    p.add_argument('--body-range', action='append', type=_cli_range,
                   help='Selected body START:END; repeatable, required for explicit policy')
    p.add_argument('--exclude-range', action='append', type=_cli_range,
                   help='Excluded title/note/etc. START:END within selected body; repeatable')
    a = p.parse_args()
    try:
        # Decode without newline rewriting so the reported text hash binds input bytes.
        text = a.file.read_bytes().decode('utf-8')
        result = check(text, a.repeat_window, a.dash_limit, body_policy=a.body_policy,
                       body_ranges=a.body_range, exclude_ranges=a.exclude_range)
    except (ValueError, OSError) as exc:
        p.error(str(exc))
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if a.out:
        from workspace_lib import atomic_text
        atomic_text(a.out, output)
    else:
        print(output)


if __name__ == '__main__':
    main()
