# coding: utf-8
"""External workspaces and collaboration records; all materials are synthetic.

The conflict case tests the local receipt recorder only. It makes no MCP call
and cannot establish remote compare-and-swap or concurrent editing support.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from external_operations import prepare, record_result
from workspace_lib import digest, read_json, write_json
from writing_workspace import add_revision, context, init_project, set_chapters, validate


class V22Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.cwd_a = self.root / 'checkout-a'
        self.cwd_b = self.root / 'checkout-b'
        self.cwd_a.mkdir()
        self.cwd_b.mkdir()

    def cli(self, *args, cwd=None, success=True):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts/writing_workspace.py'), *map(str, args)],
            cwd=cwd or self.cwd_a, capture_output=True, text=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def inventory(self, root):
        return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*')
                if p.is_file() and p.name != '.writing.lock'}

    def file(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def accepted_novel(self, workspace):
        project = init_project(workspace, 'shared-novel', '合成合作小说', 'novel')
        set_chapters(project, [{'id': 'ch01', 'title': '合成第一章'}])
        source = self.file('fixtures/original.md', '合成原稿：两人约定在周五检查修好的钟。\n')
        decision = self.file('fixtures/original-decision.md',
                             'Synthetic fixture only: both fictional authors accept the initial plan and text.\n')
        add_revision(project, source, 'book-1', 'book_plan', '1', 'accepted', decision_file=decision)
        add_revision(project, source, 'plan-1', 'chapter_plan', '1', 'accepted',
                     'ch01', 'book-1', decision_file=decision)
        accepted = add_revision(project, source, 'text-1', 'text', '1', 'accepted',
                                'ch01', 'plan-1', decision_file=decision)
        return project, accepted

    def test_external_workspace_is_stable_across_checkout_directories(self):
        workspace = self.root / 'private-home/workspace'
        created = self.cli('--workspace', workspace, 'init', '--id', 'first',
                           '--title', '合成小说', '--type', 'novel')
        expected = workspace / 'novels/first'
        self.assertEqual(Path(created), expected)
        state_before = (expected / 'state.json').read_bytes()
        first = self.cli('--workspace', workspace, 'resume', '--project', 'first')
        second = self.cli('--workspace', workspace, 'resume', '--project', 'first', cwd=self.cwd_b)
        self.assertEqual(first, second)
        self.assertEqual(first['workspace'], str(workspace))
        self.assertEqual(first['project_path'], str(expected))
        self.assertEqual(first['state'], read_json(expected / 'state.json'))
        self.assertEqual((expected / 'state.json').read_bytes(), state_before)
        self.assertFalse((self.cwd_a / 'workspace').exists())
        self.assertFalse((self.cwd_b / 'workspace').exists())

    def test_explicit_user_path_expands_without_changing_home_environment(self):
        workspace = self.root / 'private-user/workspace'
        # A temporary path expressed relative to the real home tests expansion
        # without substituting HOME or writing into the real personal workspace.
        user_path = '~/' + os.path.relpath(workspace, Path.home())
        created = self.cli('--workspace', user_path, 'init', '--id', 'article',
                           '--title', '合成文章', '--type', 'wechat')
        self.assertEqual(Path(created), workspace / 'wechat/article')
        resumed = self.cli('--workspace', user_path, 'resume', '--project', 'article', cwd=self.cwd_b)
        self.assertEqual(resumed['workspace'], str(workspace))
        self.assertFalse((self.cwd_a / '~').exists())

    def test_legacy_default_remains_relative_to_current_directory(self):
        created = self.cli('init', '--id', 'legacy', '--title', '旧命令合成作品', '--type', 'novel')
        self.assertEqual(Path(created), self.cwd_a / 'workspace/novels/legacy')
        resumed = self.cli('resume', '--project', 'legacy')
        self.assertEqual(resumed['workspace'], str(self.cwd_a / 'workspace'))
        self.assertFalse((self.cwd_b / 'workspace').exists())

    def test_missing_explicit_workspace_does_not_create_or_fall_back(self):
        self.cli('init', '--id', 'same-name', '--title', '本地已存在', '--type', 'novel')
        fallback_before = self.inventory(self.cwd_a / 'workspace')
        missing = self.root / 'missing/workspace'
        self.cli('--workspace', missing, 'resume', '--project', 'same-name', success=False)
        self.assertFalse(missing.parent.exists())
        self.assertEqual(self.inventory(self.cwd_a / 'workspace'), fallback_before)

    def test_init_rejects_missing_broken_or_incomplete_catalog_without_hiding_work(self):
        scenarios = {
            'missing': None,
            'broken-json': b'{not valid json',
            'wrong-shape': b'{"schema_version":1,"projects":{}}',
            'empty-catalog': b'{"schema_version":1,"projects":[]}',
        }
        for name, catalog in scenarios.items():
            for kind in ['novels', 'wechat']:
                with self.subTest(catalog=name, kind=kind):
                    workspace = self.root / name / kind
                    original = workspace / kind / 'existing/private.md'
                    original.parent.mkdir(parents=True)
                    original.write_text('合成已有作品，绝不能由空索引掩盖。', encoding='utf-8')
                    if catalog is not None:
                        (workspace / 'catalog.json').write_bytes(catalog)
                    before = self.inventory(workspace)
                    self.cli('--workspace', workspace, 'init', '--id', 'new',
                             '--title', '新作品', '--type', 'novel', success=False)
                    self.assertEqual(self.inventory(workspace), before)
                    self.assertFalse((workspace / 'novels/new').exists())

    def test_repeated_init_and_unregistered_neighbor_preserve_existing_files(self):
        workspace = self.root / 'workspace'
        project = init_project(workspace, 'first', '第一部合成作品', 'novel')
        (project / 'START-HERE.md').write_text('合成用户自定义说明。', encoding='utf-8')
        before = self.inventory(workspace)
        self.cli('--workspace', workspace, 'init', '--id', 'first',
                 '--title', '第一部合成作品', '--type', 'novel', success=False)
        self.assertEqual(self.inventory(workspace), before)
        orphan = workspace / 'wechat/unregistered/private.md'
        orphan.parent.mkdir(parents=True)
        orphan.write_text('合成未登记稿件。', encoding='utf-8')
        before = self.inventory(workspace)
        self.cli('--workspace', workspace, 'init', '--id', 'second',
                 '--title', '第二部合成作品', '--type', 'novel', success=False)
        self.assertEqual(self.inventory(workspace), before)

    def test_wechat_can_start_with_text_without_mandatory_plan_acceptance(self):
        project = init_project(self.root / 'workspace', 'article', '合成公众号文章', 'wechat')
        # Assert the generated user guidance, never the implementation source.
        guidance = (project / 'START-HERE.md').read_text(encoding='utf-8')
        self.assertIn('直接成稿', guidance)
        self.assertNotIn('建立并确认全书及章节方案', guidance)
        text = self.file('article.md', '合成单篇正文：先记录观察，再决定下一次尝试。\n')
        decision = self.file('article-decision.md', 'Synthetic fixture: author accepts this single article.\n')
        row = add_revision(project, text, 'article-1', 'text', '1', 'accepted', decision_file=decision)
        result = context(project)
        self.assertIsNone(result['state']['book_plan'])
        self.assertEqual(result['state']['chapters'], [])
        self.assertEqual(result['state']['latest_text'], row['id'])
        self.assertEqual(validate(project), [])

    def test_collaborators_import_only_selected_confirmed_text_with_real_fixture_decision(self):
        project_a, old_a = self.accepted_novel(self.root / 'author-a/workspace')
        project_b, old_b = self.accepted_novel(self.root / 'author-b/workspace')
        private_marker = b'SYNTHETIC_AUTHOR_A_UNSHARED_MATERIAL'
        (project_a / 'private-source.md').write_bytes(private_marker)
        other_before = self.inventory(project_b)
        shared = self.file('shared/confirmed.md', '合成共同稿：他们先停下钟摆，才取出卡住的齿轮。\n')
        decision = self.file('shared/decision.md',
                             'Synthetic fixture only: both fictional authors approve confirmed.md for ch01, version 2.\n')
        for project, old in [(project_a, old_a), (project_b, old_b)]:
            before = self.inventory(project)
            with self.assertRaises(ValueError):
                add_revision(project, shared, 'text-2', 'text', '2', 'accepted',
                             'ch01', 'plan-1', 'text-1')
            self.assertEqual(self.inventory(project), before)
            if project == project_a:
                self.assertEqual(self.inventory(project_b), other_before)
            row = add_revision(project, shared, 'text-2', 'text', '2', 'accepted',
                               'ch01', 'plan-1', 'text-1', decision)
            self.assertEqual(digest(project / old['path']), old['sha256'])
            self.assertEqual(digest(project / row['decision_path']), digest(decision))
            self.assertEqual(context(project, 'ch01')['state']['chapters'][0]['accepted_text'], 'text-2')
            self.assertEqual(validate(project), [])
        self.assertFalse((project_b / 'private-source.md').exists())
        self.assertTrue(all(private_marker not in body for body in self.inventory(project_b).values()))
        self.assertEqual(len(read_json(project_b / '版本记录/revisions.json')['revisions']), 4)

    def test_simulated_remote_change_records_conflict_without_accepting_or_replacing_text(self):
        project, accepted = self.accepted_novel(self.root / 'workspace')
        manifest_before = (project / '版本记录/revisions.json').read_bytes()
        state_before = (project / 'state.json').read_bytes()
        operation = prepare(project, 'synthetic-docs', 'synthetic-author', 'update',
                            accepted['id'], 'synthetic-document', 'synthetic-base-v1')
        evidence = self.root / 'synthetic-conflict.json'
        # The existing recorder accepts host-shaped receipts. This fixture is
        # explicitly synthetic, not a live Tencent Docs acceptance receipt.
        write_json(evidence, {
            'source': 'live_mcp', 'service': 'synthetic-docs',
            'operation_id': operation['operation_id'], 'account_alias': 'synthetic-author',
            'local_sha256': accepted['sha256'], 'remote_id': 'synthetic-document',
            'readback_matches': False,
            'response': {'test_fixture': True, 'network_called': False,
                         'expected_base': 'synthetic-base-v1', 'observed_base': 'synthetic-base-v2',
                         'write_performed': False},
        })
        result = record_result(project, operation['operation_id'], 'conflict', evidence)
        self.assertEqual(result['status'], 'conflict')
        stored = read_json(project / result['events'][-1]['evidence'])
        self.assertFalse(stored['response']['write_performed'])
        self.assertEqual((project / '版本记录/revisions.json').read_bytes(), manifest_before)
        self.assertEqual((project / 'state.json').read_bytes(), state_before)
        self.assertEqual(digest(project / accepted['path']), accepted['sha256'])
        retry = prepare(project, 'synthetic-docs', 'synthetic-author', 'update',
                        accepted['id'], 'synthetic-document', 'synthetic-base-v1')
        self.assertTrue(retry['retry_requires_reconciliation'])


if __name__ == '__main__':
    unittest.main()
