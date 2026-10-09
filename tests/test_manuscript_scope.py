"""Synthetic body scopes distinguish literary quotations from excluded notes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from manuscript_check import check


class ManuscriptScopeTest(unittest.TestCase):
    def test_legacy_default_preserves_original_count_and_repeat_boundaries(self):
        text = '# 标题\n> 引文——不入旧统计\n春风\n\n细雨\n春风细雨\n'
        actual = check(text, repeat_window=4)
        self.assertEqual(actual, check(text, repeat_window=4, body_policy='legacy'))
        self.assertEqual(actual['chinese_characters'], 8)
        self.assertEqual(actual['dash_density_per_100'], 0)
        self.assertEqual(actual['repeated_windows'], [{'text': '春风细雨', 'positions': [0, 4]}])
        self.assertEqual(actual['body_scope']['repeated_window_scope'], 'concatenated_body')

    def test_selected_quotes_count_but_title_and_editor_note_do_not(self):
        text = '# 标题\n> 编辑说明：尚在工作区。\n> “风还没停——。”\n\n他合上窗。\n'
        result = check(text, body_policy='explicit', body_ranges=[(1, 5)], exclude_ranges=[(1, 2)], dash_limit=10)
        self.assertEqual(result['chinese_characters'], 8)
        self.assertEqual(result['dash_density_per_100'], 12.5)
        self.assertTrue(result['dash_limit_exceeded'])
        self.assertEqual(result['body_scope']['retained_ranges'], [[3, 5]])
        self.assertEqual(result['body_scope']['input_text_sha256'], hashlib.sha256(text.encode()).hexdigest())
        self.assertFalse(result['facts_verified'])
        self.assertEqual(result['structural_word_findings'], [{'line': 2, 'marker': '工作区'}])
        self.assertEqual(result['structural_word_findings_scope'], 'full_text')
        # Explicit means caller-selected body, not an implicit Markdown parser.
        selected_title = check(text, body_policy='explicit', body_ranges=[(1, 1)])
        self.assertEqual(selected_title['chinese_characters'], 2)

    def test_ranges_union_without_double_counting_and_exclusions_share_scope(self):
        text = '甲乙丙丁\n排除——说明\n甲乙丙丁\n无关——末尾\n'
        result = check(text, repeat_window=4, body_policy='explicit',
                       body_ranges=[(3, 3), (1, 3), (1, 2)], exclude_ranges=[(2, 2), (2, 2)])
        self.assertEqual(result['chinese_characters'], 8)
        self.assertEqual(result['dash_density_per_100'], 0)
        self.assertEqual(result['repeated_windows'], [{'text': '甲乙丙丁', 'positions': [0, 4]}])
        self.assertEqual(result['body_scope']['body_ranges'], [[1, 3]])
        self.assertEqual(result['body_scope']['exclude_ranges'], [[2, 2]])
        self.assertEqual(result['body_scope']['retained_ranges'], [[1, 1], [3, 3]])

    def test_explicit_repeat_windows_do_not_bridge_paragraphs_or_omitted_lines(self):
        for separator in ['', '>', '编辑说明']:
            with self.subTest(separator=separator):
                text = '春风\n' + separator + '\n细雨\n\n春风细雨\n'
                excluded = [(2, 2)] if separator == '编辑说明' else None
                result = check(text, repeat_window=4, body_policy='explicit',
                               body_ranges=[(1, 5)], exclude_ranges=excluded)
                self.assertEqual(result['chinese_characters'], 8)
                self.assertEqual(result['repeated_windows'], [])
        separate = check('春风\n忽略\n细雨\n\n春风细雨', repeat_window=4,
                         body_policy='explicit', body_ranges=[(1, 1), (3, 5)])
        self.assertEqual(separate['repeated_windows'], [])
        # A soft line break within the same retained paragraph may form a window.
        soft = check('春风\n细雨\n\n春风细雨', repeat_window=4,
                     body_policy='explicit', body_ranges=[(1, 4)])
        self.assertEqual(soft['repeated_windows'], [{'text': '春风细雨', 'positions': [0, 4]}])

    def test_invalid_or_ambiguous_scope_is_rejected(self):
        invalid = [
            {'body_policy': 'unknown'},
            {'body_ranges': [(1, 1)]},
            {'exclude_ranges': []},
            {'body_policy': 'explicit'},
            {'body_policy': 'explicit', 'body_ranges': []},
            {'body_policy': 'explicit', 'body_ranges': [(0, 1)]},
            {'body_policy': 'explicit', 'body_ranges': [(2, 1)]},
            {'body_policy': 'explicit', 'body_ranges': [(1, 4)]},
            {'body_policy': 'explicit', 'body_ranges': [(True, 1)]},
            {'body_policy': 'explicit', 'body_ranges': [(1.0, 2)]},
            {'body_policy': 'explicit', 'body_ranges': [(1,)]},
            {'body_policy': 'explicit', 'body_ranges': '1:2'},
            {'body_policy': 'explicit', 'body_ranges': [(1, 1)], 'exclude_ranges': [(2, 2)]},
            {'body_policy': 'explicit', 'body_ranges': [(1, 2)], 'exclude_ranges': [(1, 2)]},
            {'body_policy': 'explicit', 'body_ranges': [(1, 2)], 'exclude_ranges': [(2, 4)]},
        ]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                check('第一行\n第二行\n第三行', **kwargs)
        self.assertEqual(check('')['chinese_characters'], 0)

    def test_cli_scope_hash_and_invalid_range_do_not_create_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'synthetic.md'
            source.write_bytes('# 标题\r\n> 叙事引文\r\n编辑说明\r\n正文结束\r\n'.encode())
            output = Path(directory) / 'result.json'
            command = [sys.executable, str(ROOT/'scripts/manuscript_check.py'), str(source),
                       '--body-policy', 'explicit', '--body-range', '1:4',
                       '--exclude-range', '1:1', '--exclude-range', '3:3', '--out', str(output)]
            completed = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report['chinese_characters'], 8)
            self.assertEqual(report['body_scope']['input_text_sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
            for malformed in ['0:2', '4:3', '1:99', '1-2']:
                invalid_output = Path(directory) / ('invalid-' + malformed.replace(':', '-') + '.json')
                rejected = subprocess.run([sys.executable, str(ROOT/'scripts/manuscript_check.py'), str(source),
                                           '--body-policy', 'explicit', '--body-range', malformed,
                                           '--out', str(invalid_output)], capture_output=True, text=True)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertFalse(invalid_output.exists())


if __name__ == '__main__':
    unittest.main()
