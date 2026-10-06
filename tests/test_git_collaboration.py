"""Private Git collaboration checks, using temporary synthetic works only."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from git_collaboration import guard, package, verify
from workspace_lib import digest, read_json, write_json
from writing_workspace import add_revision, derive_state, init_project, set_chapters, validate


class GitCollaborationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / 'private-repository'
        self.project = init_project(self.workspace, 'synthetic-book', '合成小说', 'novel')
        set_chapters(self.project, [{'id': 'ch01', 'title': '合成章'}])
        self.source = self.root / 'candidate.md'
        self.source.write_text('合成原稿：钟修好了，他们约好明天再来。\n', encoding='utf-8')
        self.decision = self.root / 'decision.md'
        self.decision.write_text('Synthetic fixture: the fictional author accepts the original plan and text.\n')
        add_revision(self.project, self.source, 'book-1', 'book_plan', '1', 'accepted', decision_file=self.decision)
        add_revision(self.project, self.source, 'plan-1', 'chapter_plan', '1', 'accepted',
                     'ch01', 'book-1', decision_file=self.decision)
        self.accepted = add_revision(self.project, self.source, 'text-1', 'text', '1', 'accepted',
                                     'ch01', 'plan-1', decision_file=self.decision)
        (self.workspace / '.gitignore').write_text('.writing.lock\n', encoding='utf-8')
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Writer')
        self.git('config', 'user.email', 'synthetic@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.commit('Initial synthetic registered content')
        self.base = self.git('rev-parse', 'HEAD').strip()
        self.source.write_text('合成候选：他们先停下钟摆，再取出卡住的齿轮。\n', encoding='utf-8')

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.workspace), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def commit(self, message):
        self.git('add', '.')
        self.git('commit', '-m', message)

    def create(self, **options):
        return package(self.workspace, 'synthetic-book', 'ch01', self.base,
                       [self.source], package_id='candidate-01', **options)

    def protected_inventory(self):
        return {str(path.relative_to(self.workspace)): digest(path)
                for path in self.project.rglob('*') if path.is_file() and path.name != '.writing.lock'}

    def resign_manifest(self, update):
        path = self.workspace / 'contributions/candidate-01/manifest.json'
        data = read_json(path)
        update(data)
        write_json(path, data)
        path.with_name('manifest.sha256').write_text(digest(path) + '\n')

    def test_package_and_verification_preserve_all_registered_content_and_acceptance(self):
        before = self.protected_inventory()
        review = self.root / 'review.md'
        review.write_text('Synthetic review: explain why the character stopped the clock.\n')
        result = self.create(reviews=[review])
        self.assertFalse(result['content_registered'])
        self.assertFalse(result['content_accepted'])
        manifest = read_json(self.workspace / result['package'] / 'manifest.json')
        self.assertEqual(manifest['project_id'], 'synthetic-book')
        self.assertEqual(manifest['chapter_id'], 'ch01')
        self.assertEqual(manifest['base_commit'], self.base)
        self.assertEqual({row['role'] for row in manifest['files']}, {'candidate', 'review'})
        self.assertEqual({row['id'] for row in manifest['baseline']['selected_versions']},
                         {'book-1', 'plan-1', 'text-1'})
        self.assertEqual(guard(self.workspace, self.base)['packages'], ['candidate-01'])
        checked = verify(self.workspace, result['package'], self.base)
        self.assertTrue(checked['ok'])
        self.assertFalse(checked['content_accepted'])
        self.commit('Submit candidate package for editorial review')
        self.assertTrue(verify(self.workspace, result['package'], self.base)['ok'])
        self.assertEqual(self.protected_inventory(), before)
        self.assertEqual(derive_state(self.project)['chapters'][0]['accepted_text'], 'text-1')
        self.assertEqual(validate(self.project), [])

    def test_review_only_and_wechat_article_need_no_chapter_plan(self):
        article = init_project(self.workspace, 'synthetic-article', '合成文章', 'wechat')
        add_revision(article, self.source, 'article-1', 'text', '1', 'draft')
        self.commit('Add a synthetic article')
        base = self.git('rev-parse', 'HEAD').strip()
        result = package(self.workspace, 'synthetic-article', 'article', base,
                         reviews=[self.source], package_id='review-only')
        checked = verify(self.workspace, result['package'], base)
        self.assertTrue(checked['ok'])
        self.assertEqual(checked['files'][0]['role'], 'review')
        self.assertEqual(checked['baseline']['selected_versions'][0]['id'], 'article-1')

    def test_package_id_is_immutable(self):
        self.create()
        before = (self.workspace / 'contributions/candidate-01/manifest.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.create()
        self.assertEqual((self.workspace / 'contributions/candidate-01/manifest.json').read_bytes(), before)

    def test_payload_tampering_and_undeclared_files_are_rejected(self):
        result = self.create()
        path = self.workspace / result['package'] / result['files'][0]['path']
        original = path.read_bytes()
        path.write_bytes(b'tampered candidate')
        with self.assertRaisesRegex(ValueError, 'checksum/size'):
            verify(self.workspace, result['package'])
        path.write_bytes(original)
        (path.parent / 'not-declared.md').write_text('undeclared')
        with self.assertRaisesRegex(ValueError, 'Undeclared'):
            guard(self.workspace, self.base)

    def test_manifest_tampering_and_forged_base_are_rejected(self):
        result = self.create()
        path = self.workspace / result['package'] / 'manifest.json'
        original = path.read_bytes()
        path.write_bytes(original + b'\n')
        with self.assertRaisesRegex(ValueError, 'manifest checksum'):
            verify(self.workspace, result['package'])
        path.write_bytes(original)
        self.resign_manifest(lambda manifest: manifest['baseline']['selected_versions'][0].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, 'baseline/selected'):
            verify(self.workspace, result['package'])

    def test_path_traversal_is_rejected_even_with_recomputed_manifest_checksum(self):
        self.create()
        self.resign_manifest(lambda manifest: manifest['files'][0].update(path='files/../../decision.md'))
        with self.assertRaisesRegex(ValueError, 'without traversal'):
            verify(self.workspace, 'contributions/candidate-01')
        with self.assertRaisesRegex(ValueError, 'Expected contributions'):
            verify(self.workspace, '../private-repository/contributions/candidate-01')

    def test_symlink_payload_and_symlink_package_are_rejected(self):
        result = self.create()
        path = self.workspace / result['package'] / result['files'][0]['path']
        path.unlink()
        path.symlink_to(self.source)
        with self.assertRaisesRegex(ValueError, 'Symlinks|escapes selected workspace'):
            verify(self.workspace, result['package'])
        path.unlink()
        path.write_bytes(self.source.read_bytes())
        directory = path.parent.parent
        moved = self.root / 'moved-package'
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'regular directory|escapes selected workspace'):
            verify(self.workspace, result['package'])

    def test_untracked_official_file_and_modified_configuration_are_rejected(self):
        self.create()
        unexpected = self.project / '正文-new.md'
        unexpected.write_text('unregistered official path')
        with self.assertRaisesRegex(ValueError, 'Protected workspace change'):
            guard(self.workspace, self.base)
        unexpected.unlink()
        (self.workspace / '.gitignore').write_text('.writing.lock\n*.json\n')
        with self.assertRaisesRegex(ValueError, 'Protected workspace change'):
            verify(self.workspace, 'contributions/candidate-01')

    def test_staged_mutation_cannot_be_hidden_by_restoring_working_copy(self):
        self.create()
        path = self.project / 'state.json'
        original = path.read_bytes()
        path.write_bytes(b'{"synthetic_tamper":true}\n')
        self.git('add', str(path))
        path.write_bytes(original)
        with self.assertRaisesRegex(ValueError, 'staged M'):
            guard(self.workspace, self.base)

    def test_editor_rejects_registration_drift_without_touching_existing_accepted_versions(self):
        result = self.create()
        self.commit('Propose candidate')
        add_revision(self.project, self.source, 'text-2', 'text', '2', 'accepted',
                     'ch01', 'plan-1', 'text-1', self.decision)
        self.commit('Synthetic editor accepts a different current version')
        before = self.protected_inventory()
        with self.assertRaisesRegex(ValueError, 'differs from the declared base'):
            verify(self.workspace, result['package'])
        self.assertEqual(self.protected_inventory(), before)
        self.assertEqual(derive_state(self.project)['chapters'][0]['accepted_text'], 'text-2')
        self.assertEqual(digest(self.project / self.accepted['path']), self.accepted['sha256'])

    def test_editor_rejects_good_package_with_committed_lifecycle_mutation(self):
        result = self.create()
        self.commit('Propose candidate')
        lifecycle = self.project / 'runs/lifecycle/events.jsonl'
        lifecycle.parent.mkdir(parents=True)
        lifecycle.write_text('{"synthetic_concurrent_chain":true}\n')
        self.commit('Contributor incorrectly commits a local lifecycle chain')
        before = self.protected_inventory()
        with self.assertRaisesRegex(ValueError, 'Protected workspace change'):
            verify(self.workspace, result['package'])
        self.assertEqual(self.protected_inventory(), before)

    def test_completed_package_does_not_replace_required_author_decision(self):
        result = self.create()
        candidate = self.workspace / result['package'] / result['files'][0]['path']
        before = self.protected_inventory()
        with self.assertRaisesRegex(ValueError, 'actual author decision'):
            add_revision(self.project, candidate, 'text-2', 'text', '2', 'accepted',
                         'ch01', 'plan-1', 'text-1')
        self.assertEqual(self.protected_inventory(), before)
        self.assertFalse(verify(self.workspace, result['package'])['content_accepted'])

    def test_reviewer_selected_base_must_match_package(self):
        result = self.create()
        self.commit('Propose candidate')
        with self.assertRaisesRegex(ValueError, 'reviewer-selected'):
            verify(self.workspace, result['package'], self.git('rev-parse', 'HEAD').strip())

    def test_cli_requires_explicit_workspace_and_unknown_target_fails_without_artifacts(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/git_collaboration.py'),
                                 'guard', '--base', self.base], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('--workspace', result.stderr)
        with self.assertRaisesRegex(ValueError, 'Unknown stable chapter'):
            package(self.workspace, 'synthetic-book', 'no-such-chapter', self.base, [self.source])
        self.assertFalse((self.workspace / 'contributions').exists())


if __name__ == '__main__':
    unittest.main()
