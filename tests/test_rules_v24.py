"""Work-scoped rule loading/coverage checks use synthetic data, not real manuscripts."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from workspace_lib import write_json, read_json, digest
from writing_workspace import init_project, set_chapters, add_revision, context, validate
from writing_rules import resolve_rules, validate_review
import writing_run as runs


class RulesV24Test(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.workspace = self.root / 'workspace'
        self.project = init_project(self.workspace, 'test-novel', '合成书', 'novel')
        set_chapters(self.project, [{'id': 'ch01', 'title': '第一节'}, {'id': 'ch02', 'title': '第二节'}])
        self.source = self.project / 'candidate.md'; self.source.write_text('合成候选：修好空表后，演示仍未完成。\n')
        self.decision = self.project / 'decision.md'; self.decision.write_text('合成测试的明确作者决定。\n')
        self.request = {'schema_version': 1, 'id': 'run-1', 'task': '审阅合成候选',
                        'authorization_refs': ['synthetic-request'], 'target': 'ch02', 'mode': 'review',
                        'stage': 'review', 'fiction_policy': {'mode': 'source-based'},
                        'capabilities': ['editorial-review@1.0.0'], 'inputs': [], 'open_issues': []}

    def enable(self):
        body = self.project / 'rules.md'
        body.write_text('<a id="background"></a>\n背景解释选择。\n\n<a id="reflection"></a>\n回望保留疑问。\n')
        source = self.project / 'reference.md'; source.write_text('<a id="observation"></a>\n方法观察，非强制配额。\n')
        self.manifest = {'schema_version': 1, 'id': 'rules-r1', 'project_id': 'test-novel',
                         'files': [{'path': 'rules.md', 'sha256': digest(body), 'role': 'rules'},
                                   {'path': 'reference.md', 'sha256': digest(source), 'role': 'source'}],
                         'rules': [{'id': 'background', 'path': 'rules.md', 'anchor': 'background',
                                    'kind': 'required', 'targets': ['*'], 'modes': ['*'], 'check': 'semantic',
                                    'sources': [{'path': 'reference.md', 'anchor': 'observation'}]},
                                   {'id': 'reflection', 'path': 'rules.md', 'anchor': 'reflection',
                                    'kind': 'guidance', 'targets': ['ch02'], 'modes': ['draft', 'review'],
                                    'check': 'semantic', 'sources': []}]}
        write_json(self.project / 'rules.json', self.manifest)
        meta = read_json(self.project / 'book.yaml'); meta['rules_manifest'] = 'rules.json'; meta['rules_file'] = 'rules.md'
        write_json(self.project / 'book.yaml', meta)
        return resolve_rules(self.project, 'ch02', 'review')

    def review(self, rules, status='satisfied', artifact_id='draft-1', sha=None):
        sha = sha or digest(self.source)
        return {'scope': '合成正文第一段', 'task_result': 'completed',
                'manuscript_result': 'meets_rules' if status == 'satisfied' else 'needs_revision',
                'result': 'pass' if status == 'satisfied' else 'needs_revision',
                'findings': [{'location': '第一段', 'observation': '具体审阅意见'}], 'unresolved_blockers': [],
                'rule_set_sha256': rules['rule_set_sha256'], 'artifacts': [{'id': artifact_id, 'sha256': sha}],
                'rule_coverage': [{'rule_id': rule['id'], 'status': status, 'reason': '审阅者对具体段落的判断',
                                   'evidence': [{'artifact_id': artifact_id, 'sha256': sha, 'location': '第一段'}]}
                                  for rule in rules['rules']]}

    def save_review(self, review):
        path = self.project / 'review.json'; write_json(path, review); return path

    def test_legacy_workspace_is_compatible_and_warns(self):
        self.assertFalse(resolve_rules(self.project)['enabled'])
        self.assertIn('legacy', context(self.project)['rule_context']['notice'].lower())
        add_revision(self.project, self.source, 'draft-1', 'text', '1', 'draft', 'ch02')
        self.assertEqual(validate(self.project), [])

    def test_explicit_empty_manifest_is_not_legacy_fallback(self):
        for invalid in ['', None, False]:
            with self.subTest(value=invalid):
                meta = read_json(self.project / 'book.yaml'); meta['rules_manifest'] = invalid
                write_json(self.project / 'book.yaml', meta)
                with self.assertRaises(ValueError): resolve_rules(self.project)

    def test_resolution_scopes_and_read_paths(self):
        self.enable()
        self.assertEqual([r['id'] for r in resolve_rules(self.project, 'ch01', 'draft')['rules']], ['background'])
        self.assertEqual([r['id'] for r in resolve_rules(self.project, 'ch02', 'plan')['rules']], ['background'])
        selected = context(self.project, 'ch02', 'review')
        self.assertEqual(len(selected['rule_context']['rules']), 2)
        self.assertEqual(len(selected['rules_read_full_text']), 3)
        self.assertTrue(all(r['read_state'] == 'not_attested' for r in selected['rules_read_full_text']))

    def test_manifest_path_scope_hash_and_anchor_fail_closed(self):
        self.enable(); baseline = copy.deepcopy(self.manifest)
        variants = []
        for path in ['../candidate.md', '/tmp/candidate.md', 'missing.md']:
            changed = copy.deepcopy(baseline); changed['files'][0]['path'] = path; variants.append(changed)
        changed = copy.deepcopy(baseline); changed['files'][0]['sha256'] = '0' * 64; variants.append(changed)
        changed = copy.deepcopy(baseline); changed['rules'][0]['anchor'] = 'absent'; variants.append(changed)
        changed = copy.deepcopy(baseline); changed['rules'][0]['sources'][0]['anchor'] = 'absent'; variants.append(changed)
        changed = copy.deepcopy(baseline); changed['rules'][0]['sources'][0]['path'] = 'candidate.md'; variants.append(changed)
        changed = copy.deepcopy(baseline); changed['project_id'] = 'another-work'; variants.append(changed)
        changed = copy.deepcopy(baseline); changed['rules'][0]['targets'] = ['ch99']; variants.append(changed)
        for manifest in variants:
            with self.subTest(manifest=manifest):
                write_json(self.project / 'rules.json', manifest)
                with self.assertRaises((ValueError, OSError)): resolve_rules(self.project, 'ch02', 'review')

    def test_duplicate_anchor_and_symlink_escape_rejected(self):
        self.enable()
        body = self.project / 'rules.md'; body.write_text(body.read_text() + '<a id="background"></a>\n')
        self.manifest['files'][0]['sha256'] = digest(body); write_json(self.project / 'rules.json', self.manifest)
        with self.assertRaises(ValueError): resolve_rules(self.project, 'ch02', 'review')
        body.unlink(); body.symlink_to(self.source)
        self.manifest['files'][0]['sha256'] = digest(body); write_json(self.project / 'rules.json', self.manifest)
        with self.assertRaises(ValueError): resolve_rules(self.project, 'ch02', 'review')

    def test_human_rule_entry_is_also_validated_and_pinned(self):
        self.enable()
        entry = self.project / 'entry.md'; entry.write_text('从这里读规则。\n')
        meta = read_json(self.project / 'book.yaml'); meta['rules_file'] = 'entry.md'; write_json(self.project / 'book.yaml', meta)
        with self.assertRaises(ValueError): resolve_rules(self.project, 'ch02', 'review')
        self.manifest['files'].append({'path': 'entry.md', 'sha256': digest(entry), 'role': 'entry'})
        write_json(self.project / 'rules.json', self.manifest)
        run = runs.start(self.project, self.request)
        self.assertIn('entry.md', {p['source'] for p in run['run']['pins']})
        entry.write_text('入口被偷偷改变。\n')
        with self.assertRaises(ValueError): resolve_rules(self.project, 'ch02', 'review')

    def test_missing_duplicate_and_wrong_hash_rule_coverage_rejected(self):
        rules = self.enable(); review = self.review(rules); artifacts = review['artifacts']
        mutations = []
        changed = copy.deepcopy(review); changed['rule_coverage'].pop(); mutations.append(changed)
        changed = copy.deepcopy(review); changed['rule_coverage'].append(changed['rule_coverage'][0]); mutations.append(changed)
        changed = copy.deepcopy(review); changed['rule_coverage'][0]['evidence'][0]['sha256'] = '0' * 64; mutations.append(changed)
        changed = copy.deepcopy(review); changed['rule_coverage'][0]['evidence'][0]['location'] = ''; mutations.append(changed)
        changed = copy.deepcopy(review); changed['rule_set_sha256'] = '0' * 64; mutations.append(changed)
        changed = copy.deepcopy(review); changed['rule_coverage'][0]['status'] = 'not_applicable'; mutations.append(changed)
        for changed in mutations:
            with self.subTest(review=changed):
                with self.assertRaises(ValueError): validate_review(rules, changed, artifacts)
        review['rule_coverage'][0].update(status='not_applicable', basis='本次明确只改标点，约束不涉及此处')
        self.assertTrue(validate_review(rules, review, artifacts)['coverage_complete'])

    def test_literary_judgment_remains_separate_from_completion_and_acceptance(self):
        rules = self.enable(); review = self.review(rules, 'partial')
        result = validate_review(rules, review, review['artifacts'], require_completed=True)
        self.assertEqual(result['task_result'], 'completed')
        self.assertEqual(result['manuscript_result'], 'needs_revision')
        self.assertEqual(result['author_acceptance'], 'not_determined')
        review['manuscript_result'] = 'meets_rules'
        with self.assertRaises(ValueError): validate_review(rules, review, review['artifacts'])

    def test_direct_registration_requires_exact_review_but_allows_incomplete_candidate(self):
        self.enable()
        with self.assertRaises(ValueError): add_revision(self.project, self.source, 'new-1', 'text', '1', 'draft', 'ch02')
        rules = resolve_rules(self.project, 'ch02', 'draft'); review = self.review(rules, 'needs_verification')
        review['task_result'] = 'in_progress'
        row = add_revision(self.project, self.source, 'new-1', 'text', '1', 'draft', 'ch02', rules_review=self.save_review(review))
        self.assertIn('rule_review', row); self.assertEqual(validate(self.project), [])
        self.source.write_text('候选已变更\n')
        with self.assertRaises(ValueError): add_revision(self.project, self.source, 'new-2', 'text', '2', 'draft', 'ch02', rules_review=self.save_review(review))
        with self.assertRaises(ValueError): add_revision(self.project, self.source, 'fake', 'text', '1', 'draft', 'ch02', rules_mode='title', rules_review=self.save_review(review))

    def test_rule_review_receipt_is_immutable_and_does_not_replace_author_decision(self):
        self.enable(); rules = resolve_rules(self.project, 'ch02', 'draft'); review = self.save_review(self.review(rules))
        with self.assertRaises(ValueError): add_revision(self.project, self.source, 'fake', 'text', '1', 'accepted', 'ch02', rules_review=review)
        row = add_revision(self.project, self.source, 'new-1', 'text', '1', 'draft', 'ch02', rules_review=review)
        (self.project / row['rule_review']['path']).write_text('{}')
        self.assertTrue(any('changed rule review' in e for e in validate(self.project)))

    def test_new_run_pins_rule_dependencies_and_resumes_despite_current_drift(self):
        self.enable(); result = runs.start(self.project, self.request)
        pinned = {p['source'] for p in result['run']['pins']}
        self.assertTrue({'rules.json', 'rules.md', 'reference.md'}.issubset(pinned))
        (self.project / 'rules.md').write_text('已变化且不应偷偷取代快照\n')
        self.assertTrue(runs.verify(self.project, 'run-1')['drift'])
        restored = context(self.project)
        self.assertEqual(restored['rule_context'], result['run']['rule_context'])
        self.assertTrue(all('/runs/run-1/inputs/' in p['path'] for p in restored['rules_read_full_text']))
        with self.assertRaises(ValueError): resolve_rules(self.project, 'ch02', 'review')

    def test_old_run_stays_legacy_after_workspace_opt_in(self):
        result = runs.start(self.project, self.request)
        self.assertNotIn('rule_context', result['run'])
        self.enable(); restored = context(self.project)
        self.assertFalse(restored['rule_context']['enabled'])
        runs.add_artifact(self.project, 'run-1', 'text', self.source, 'draft-1')
        runs.register(self.project, 'run-1', 'register', 'draft-1', {'revision_id': 'old-run-draft', 'kind': 'text', 'version': '1', 'status': 'draft', 'chapter_id': 'ch02'})
        self.assertEqual(validate(self.project), [])

    def test_review_task_can_complete_needs_revision_without_accepting_text(self):
        self.enable(); started = runs.start(self.project, self.request)
        runs.add_artifact(self.project, 'run-1', 'text', self.source, 'draft-1')
        before = (self.project / '版本记录/revisions.json').read_bytes()
        review = self.review(started['run']['rule_context'], 'unmet')
        runs.add_artifact(self.project, 'run-1', 'review', self.save_review(review), 'review-1', 'review')
        runs.change_stage(self.project, 'run-1', 'done', 'completed', '已交付有定位的审阅意见', 'review-1')
        self.assertEqual(runs.derive(self.project)['runs']['run-1']['stage'], 'completed')
        self.assertEqual((self.project / '版本记录/revisions.json').read_bytes(), before)

    def test_run_registration_is_guarded_and_keeps_pinned_rules_after_drift(self):
        self.request['mode'] = 'draft'
        self.enable(); started = runs.start(self.project, self.request)
        runs.add_artifact(self.project, 'run-1', 'text', self.source, 'draft-1')
        revision = {'revision_id': 'new-1', 'kind': 'text', 'version': '1', 'status': 'draft', 'chapter_id': 'ch02'}
        with self.assertRaises(ValueError): runs.register(self.project, 'run-1', 'register', 'draft-1', revision)
        review = self.review(started['run']['rule_context'], 'partial')
        runs.add_artifact(self.project, 'run-1', 'review', self.save_review(review), 'review-1', 'review')
        (self.project / 'rules.md').write_text('现行规则变化\n')
        revision['review_id'] = 'review-1'
        with patch('writing_run.append_event', side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError): runs.register(self.project, 'run-1', 'register', 'draft-1', revision)
        runs.register(self.project, 'run-1', 'register', 'draft-1', revision)
        runs.register(self.project, 'run-1', 'register', 'draft-1', revision)
        self.assertEqual(validate(self.project), [])
        self.assertEqual(runs.derive(self.project)['runs']['run-1']['registered_versions'], ['new-1'])

    def test_review_or_title_run_cannot_bypass_writing_rules_to_register_text(self):
        self.enable()
        for mode in ['review', 'title']:
            request = dict(self.request, id=mode, mode=mode)
            started = runs.start(self.project, request)
            runs.add_artifact(self.project, mode, 'text', self.source, 'draft-1')
            review = self.review(started['run']['rule_context'])
            runs.add_artifact(self.project, mode, 'review', self.save_review(review), 'review-1', 'review')
            revision = {'revision_id': mode + '-text', 'kind': 'text', 'version': '1', 'status': 'draft',
                        'chapter_id': 'ch02', 'review_id': 'review-1'}
            with self.assertRaises(ValueError): runs.register(self.project, mode, 'register', 'draft-1', revision)

    def test_chapter_plan_run_cannot_register_book_plan_under_chapter_rules(self):
        self.enable(); self.request.update(mode='plan', stage='plan')
        started = runs.start(self.project, self.request)
        runs.add_artifact(self.project, 'run-1', 'plan', self.source, 'plan-1', 'plan')
        review = self.review(started['run']['rule_context'], artifact_id='plan-1')
        runs.add_artifact(self.project, 'run-1', 'review', self.save_review(review), 'review-1', 'review')
        revision = {'revision_id': 'bad-book', 'kind': 'book_plan', 'version': '1', 'status': 'accepted',
                    'chapter_id': 'ch02', 'review_id': 'review-1', 'decision_file': 'decision.md'}
        before = (self.project / '版本记录/revisions.json').read_bytes()
        with self.assertRaises(ValueError): runs.register(self.project, 'run-1', 'register', 'plan-1', revision)
        with self.assertRaises(ValueError):
            add_revision(self.project, self.source, 'bad-direct', 'book_plan', '1', 'accepted', 'ch02',
                         decision_file=self.decision, rules_review=self.save_review(review))
        self.assertEqual((self.project / '版本记录/revisions.json').read_bytes(), before)

    def test_book_target_registers_book_plan_but_not_chapter_text(self):
        self.enable(); self.request.update(target='book', mode='plan', stage='plan')
        started = runs.start(self.project, self.request)
        runs.add_artifact(self.project, 'run-1', 'plan', self.source, 'plan-1', 'plan')
        review = self.review(started['run']['rule_context'], artifact_id='plan-1')
        runs.add_artifact(self.project, 'run-1', 'review', self.save_review(review), 'review-1', 'review')
        revision = {'revision_id': 'book-1', 'kind': 'book_plan', 'version': '1', 'status': 'accepted',
                    'review_id': 'review-1', 'decision_file': 'decision.md'}
        runs.register(self.project, 'run-1', 'register', 'plan-1', revision)
        self.assertEqual(validate(self.project), [])
        runs.add_artifact(self.project, 'run-1', 'text', self.source, 'draft-1')
        with self.assertRaises(ValueError):
            runs.register(self.project, 'run-1', 'wrong-text', 'draft-1',
                          {'revision_id': 'bad-text', 'kind': 'text', 'version': '1', 'status': 'draft', 'chapter_id': 'ch02'})

    def test_new_scope_checks_do_not_rewrite_or_reject_legacy_registered_history(self):
        # An old malformed book-plan scope is evidence; new writes must not reproduce it.
        records = read_json(self.project / '版本记录/revisions.json')
        records['revisions'].append({'id': 'old-book', 'kind': 'book_plan', 'version': '1', 'status': 'accepted',
                                     'chapter_id': 'ch02', 'path': 'candidate.md', 'sha256': digest(self.source),
                                     'decision_path': 'decision.md', 'decision_sha256': digest(self.decision)})
        write_json(self.project / '版本记录/revisions.json', records)
        before = (self.project / '版本记录/revisions.json').read_bytes()
        self.enable(); self.assertEqual(validate(self.project), [])
        self.assertEqual((self.project / '版本记录/revisions.json').read_bytes(), before)
        with self.assertRaises(ValueError): add_revision(self.project, self.source, 'new', 'text', '1', 'draft')
        article = init_project(self.workspace, 'article', '合成短文', 'wechat')
        add_revision(article, self.source, 'article-1', 'text', '1', 'draft')
        with self.assertRaises(ValueError): add_revision(article, self.source, 'article-book', 'book_plan', '1', 'draft')

    def test_each_reviewed_manuscript_needs_each_rule_evidence_before_registration(self):
        self.enable(); self.request['mode'] = 'draft'
        started = runs.start(self.project, self.request)
        runs.add_artifact(self.project, 'run-1', 'first', self.source, 'draft-1')
        second = self.project / 'second.md'; second.write_text('另一份候选有不同的判断。\n')
        runs.add_artifact(self.project, 'run-1', 'second', second, 'draft-2')
        review = self.review(started['run']['rule_context'])
        review['artifacts'].append({'id': 'draft-2', 'sha256': digest(second)})
        with self.assertRaises(ValueError): validate_review(started['run']['rule_context'], review, review['artifacts'])
        runs.add_artifact(self.project, 'run-1', 'bad-review', self.save_review(review), 'bad-review', 'review')
        revision = {'revision_id': 'second-1', 'kind': 'text', 'version': '1', 'status': 'draft',
                    'chapter_id': 'ch02', 'review_id': 'bad-review'}
        with self.assertRaises(ValueError): runs.register(self.project, 'run-1', 'register-bad', 'draft-2', revision)
        for row in review['rule_coverage']:
            row['evidence'].append({'artifact_id': 'draft-2', 'sha256': digest(second), 'location': '另一候选第一段'})
        self.assertTrue(validate_review(started['run']['rule_context'], review, review['artifacts'])['coverage_complete'])
        runs.add_artifact(self.project, 'run-1', 'good-review', self.save_review(review), 'good-review', 'review')
        revision['review_id'] = 'good-review'
        runs.register(self.project, 'run-1', 'register-good', 'draft-2', revision)
        self.assertEqual(validate(self.project), [])

    def test_historical_inheritance_is_never_rebased(self):
        add_revision(self.project, self.source, 'book-1', 'book_plan', '1', 'accepted', decision_file=self.decision)
        add_revision(self.project, self.source, 'plan-1', 'chapter_plan', '1', 'accepted', 'ch02', 'book-1', decision_file=self.decision)
        add_revision(self.project, self.source, 'book-2', 'book_plan', '2', 'accepted', decision_file=self.decision)
        before = (self.project / '版本记录/revisions.json').read_bytes(); self.enable()
        restored = context(self.project, 'ch02', 'review')
        self.assertTrue(any(r['id'] == 'book-1' and r['role'] == 'historical_inheritance' for r in restored['read_full_text']))
        self.assertEqual((self.project / '版本记录/revisions.json').read_bytes(), before)

    def test_other_project_rules_never_satisfy_current_review(self):
        rules = self.enable(); review = self.review(rules)
        other = init_project(self.workspace, 'second', '第二本书', 'novel')
        set_chapters(other, [{'id': 'ch02', 'title': '第二节'}])
        for name in ['rules.json', 'rules.md', 'reference.md']:
            (other / name).write_bytes((self.project / name).read_bytes())
        manifest = read_json(other / 'rules.json'); manifest['project_id'] = 'second'; write_json(other / 'rules.json', manifest)
        meta = read_json(other / 'book.yaml'); meta['rules_manifest'] = 'rules.json'; write_json(other / 'book.yaml', meta)
        foreign_rules = resolve_rules(other, 'ch02', 'review')
        with self.assertRaises(ValueError): validate_review(foreign_rules, review, review['artifacts'])

    def test_lightweight_cli_checks_actual_artifact(self):
        rules = self.enable(); review = self.save_review(self.review(rules))
        artifacts = self.project / 'artifacts.json'
        write_json(artifacts, [{'id': 'draft-1', 'path': 'candidate.md', 'sha256': digest(self.source)}])
        command = [sys.executable, str(ROOT / 'scripts/writing_rules.py'), '--workspace', str(self.workspace), '--project', 'test-novel',
                   'review', '--target', 'ch02', '--mode', 'review', '--review', str(review), '--artifacts', str(artifacts)]
        success = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(success.returncode, 0, success.stderr)
        self.assertTrue(json.loads(success.stdout)['coverage_complete'])
        self.source.write_text('已经换稿\n')
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
