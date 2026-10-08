"""Acceptance evidence must fail closed. All copied evidence is public/synthetic."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import acceptance_v23 as acceptance
from backup_workspace import create, restore, inventory
from workspace_lib import digest, read_json, write_json
from writing_workspace import init_project, set_chapters, add_revision, derive_state


class AcceptanceV23Test(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        # Historical v2.3 checks run against their version context, not the current product version.
        legacy = self.root / 'legacy-runtime'
        legacy.mkdir()
        (legacy / 'VERSION').write_text('2.3.1\n')
        original = acceptance.evidence_suffix
        patcher = patch.object(acceptance, 'evidence_suffix',
                               side_effect=lambda root=ROOT: original(legacy if Path(root) == ROOT else root))
        patcher.start(); self.addCleanup(patcher.stop)

    def public_git_evidence(self):
        folder = self.root / 'evals/v2.3/git-collaboration'
        shutil.copytree(ROOT / 'evals/v2.3/git-collaboration', folder)
        report = read_json(folder / 'evidence/result.json')
        for row in report['evaluated_files']:
            target = self.root / row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            frozen = ROOT / 'evals/v2.3/git-collaboration/source-snapshot' / row['path']
            shutil.copyfile(frozen if frozen.exists() else ROOT / row['path'], target)
        return folder / 'evidence'

    def repin(self, evidence, name):
        report = read_json(evidence / 'result.json')
        for row in report['artifacts']:
            if row['path'] == name:
                row['sha256'] = digest(evidence / name)
        write_json(evidence / 'result.json', report)

    def test_actual_git_evidence_passes_but_staged_rejection_cannot_be_replaced_by_unstaged(self):
        evidence = self.public_git_evidence()
        self.assertEqual(acceptance.git_collaboration_evidence(self.root)['cases'], 6)
        transcript = read_json(evidence / 'transcript.json')
        transcript = [r for r in transcript if ': staged ' not in r['stderr']]
        write_json(evidence / 'transcript.json', transcript)
        self.repin(evidence, 'transcript.json')
        with self.assertRaisesRegex(ValueError, 'exact Git change layer.*staged'):
            acceptance.git_collaboration_evidence(self.root)

    def test_hash_repinning_cannot_hide_truncated_recovery_inventory(self):
        evidence = self.public_git_evidence()
        inventory_path = evidence / 'official-inventory.json'
        hashes = read_json(inventory_path)
        write_json(inventory_path, {'版本记录/content/text-2.md': hashes['版本记录/content/text-2.md']})
        self.repin(evidence, 'official-inventory.json')
        with self.assertRaisesRegex(ValueError, 'omits content registry'):
            acceptance.git_collaboration_evidence(self.root)

    def test_empty_pins_do_not_count_as_input_integrity_proof(self):
        evidence = self.public_git_evidence()
        transcript = read_json(evidence / 'transcript.json')
        for row in transcript:
            if row['exit_code'] == 0 and 'verify' in row['argv'] and any(a.endswith('/writing_run.py') for a in row['argv']):
                result = json.loads(row['stdout']); result['run']['pins'] = []
                row['stdout'] = json.dumps(result)
        write_json(evidence / 'transcript.json', transcript)
        self.repin(evidence, 'transcript.json')
        with self.assertRaisesRegex(ValueError, 'no locked inputs'):
            acceptance.git_collaboration_evidence(self.root)

    def test_changed_evaluated_code_requires_repeat_evaluation(self):
        self.public_git_evidence()
        path = self.root / 'scripts/git_collaboration.py'
        path.write_text(path.read_text() + '\n# Synthetic changed implementation\n')
        with self.assertRaisesRegex(ValueError, 'File hash differs'):
            acceptance.git_collaboration_evidence(self.root)

    def test_historical_v22_integrity_does_not_claim_current_skill_execution(self):
        shutil.copytree(ROOT / 'evals/v2.2', self.root / 'evals/v2.2')
        current_skill = self.root / '.agents/skills/touge-novel-writing/SKILL.md'
        current_skill.parent.mkdir(parents=True)
        current_skill.write_text('Synthetic newer Skill, not the old evaluated instructions.\n')
        result = acceptance.historical_v22(self.root)
        self.assertFalse(result['current_skill_behavior_retested'])
        old_candidate = self.root / 'evals/v2.2/novel-shared-baseline-conflict/candidate.md'
        old_candidate.write_text('Changed historical synthetic candidate.\n')
        with self.assertRaisesRegex(ValueError, 'File hash differs'):
            acceptance.historical_v22(self.root)

    def test_duplicate_acceptance_ids_and_private_scope_removal_fail_closed(self):
        config = read_json(ROOT / 'configs/acceptance-v2.3.json')
        path = self.root / 'configs/acceptance-v2.3.json'
        write_json(path, config)
        self.assertEqual(len(acceptance.acceptance_config(self.root)['checks']), 10)
        config['checks'].append(dict(config['checks'][0])); write_json(path, config)
        with self.assertRaisesRegex(ValueError, 'ten unique'):
            acceptance.acceptance_config(self.root)
        config['checks'].pop(); config['checks'][-1]['private_required'] = False; write_json(path, config)
        with self.assertRaisesRegex(ValueError, 'Private acceptance scope'):
            acceptance.acceptance_config(self.root)

    def test_patch_evidence_is_isolated_and_initial_release_keeps_legacy_directory(self):
        version = self.root / 'VERSION'
        workspace = self.root / 'workspace'
        old_report = workspace / 'acceptance-v2.3/report.json'
        write_json(old_report, {'version': '2.3.0', 'historical': True})
        old_hash = digest(old_report)
        for value, suffix in [('2.3.0', 'v2.3'), ('2.3.1', 'v2.3.1'), ('2.3.12', 'v2.3.12')]:
            with self.subTest(version=value):
                version.write_text(value + '\n')
                self.assertEqual(acceptance.receipt_directory(workspace, self.root), workspace / ('acceptance-' + suffix))
                self.assertEqual(acceptance.output_directory(workspace, True, self.root),
                                 self.root / 'work' / ('acceptance-public-' + suffix))
        self.assertEqual(digest(old_report), old_hash)
        for invalid in ['2.3.01', '2.4.0', '../../outside']:
            version.write_text(invalid)
            with self.assertRaisesRegex(ValueError, 'release version'):
                acceptance.output_directory(workspace, root=self.root)

    def synthetic_migration(self):
        source, destination = self.root / 'owner-workspace', self.root / 'shared-workspace'
        project = init_project(source, 'synthetic-clock', '合成修钟小说', 'novel')
        set_chapters(project, [{'id': 'ch01', 'title': '合成第一章'}])
        source_text = self.root / 'synthetic-text.md'; source_text.write_text('合成材料：他们约好周五修钟。\n')
        decision = self.root / 'synthetic-decision.md'; decision.write_text('SYNTHETIC FIXTURE: fictional authors approve.\n')
        for ident, kind, kwargs in [
            ('book-1', 'book_plan', {}),
            ('plan-1', 'chapter_plan', {'chapter_id': 'ch01', 'parent_plan_id': 'book-1'}),
            ('text-1', 'text', {'chapter_id': 'ch01', 'parent_plan_id': 'plan-1'}),
        ]:
            add_revision(project, source_text, ident, kind, '1', 'accepted', decision_file=decision, **kwargs)
        (source / 'owner-only.md').write_text('Synthetic unshared material.\n')
        body = source / 'corpus/bodies/source-1.md'; body.parent.mkdir(parents=True); body.write_text('合成修钟来源。\n')
        write_json(source / 'corpus/manifest.json', [{'id': 'source-1', 'markdown': 'bodies/source-1.md'}])
        originals = inventory(source)
        backup_path = self.root / 'backup.tar.gz'; create(source, backup_path)
        backup = restore(backup_path, self.root / 'restored')
        selected = []
        navigation = 'novels/synthetic-clock/START-HERE.md'
        for row in originals:
            if row['path'] == 'owner-only.md':
                continue
            target = row['path']; entry = dict(row, source_path=row['path'])
            if target == navigation:
                target = 'archives/cutover-baseline/START-HERE.md'
                entry.update(path=target, current_entry=navigation)
            path = destination / target; path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / row['path'], path); selected.append(entry)
        (destination / navigation).write_text('Synthetic current navigation to the shared project.\n')
        receipt = {'schema_version': 1, 'source': str(source), 'destination': str(destination),
                   'source_retained': True, 'source_original_inventory': originals, 'selected_files': selected,
                   'selected_source_ids': ['source-1'], 'backup': backup, 'source_state': derive_state(project),
                   'source_registry_sha256': digest(project / '版本记录/revisions.json')}
        write_json(acceptance.receipt_directory(destination) / 'migration.json', receipt)
        (source / 'MIGRATED.md').write_text('Synthetic new pointer; original files remain unchanged.\n')
        return source, destination

    def test_migration_allows_new_pointer_and_archived_navigation_but_checks_every_original(self):
        source, destination = self.synthetic_migration()
        self.assertTrue(acceptance.migration(destination)['full_backup_restore_verified'])
        self.assertFalse((destination / 'owner-only.md').exists())
        (source / 'owner-only.md').write_text('Unexpected modification of an unshared original.\n')
        with self.assertRaisesRegex(ValueError, 'File hash differs'):
            acceptance.migration(destination)

    def test_selected_material_ids_must_match_real_manifest(self):
        _, destination = self.synthetic_migration()
        path = acceptance.receipt_directory(destination) / 'migration.json'; receipt = read_json(path)
        receipt['selected_source_ids'] = ['invented-source']; write_json(path, receipt)
        with self.assertRaisesRegex(ValueError, 'actual corpus manifest'):
            acceptance.migration(destination)

    def test_public_repository_receipt_is_rejected_before_network_read(self):
        receipt = {'repo': {'nameWithOwner': 'synthetic/clock', 'url': 'https://github.com/synthetic/clock',
                            'isPrivate': False, 'visibility': 'PUBLIC'}, 'commit': 'a' * 40}
        write_json(acceptance.receipt_directory(self.root) / 'git-remote.json', receipt)
        with patch.object(acceptance.subprocess, 'run') as network:
            with self.assertRaisesRegex(ValueError, 'private repository'):
                acceptance.private_git_evidence(self.root)
            network.assert_not_called()


if __name__ == '__main__':
    unittest.main()
