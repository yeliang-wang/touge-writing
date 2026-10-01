"""v2.1 public self-check and private release acceptance, with separated evidence."""
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from workspace_lib import read_json, write_json, digest, scoped_path, atomic_text
from acceptance import ROOT, require, run_legacy


def textual_evidence():
    folder = ROOT / 'evals/v2.1'
    protocol = read_json(folder / 'protocol.json')
    for row in protocol['criteria_files']:
        require(digest(scoped_path(folder, row['path'])) == row['sha256'], 'Frozen task changed')
    report = read_json(folder / 'results/review.json')
    require(report.get('schema_version') == 1 and report.get('relationship_disclosure'), 'Review relationship missing')
    require(report.get('author_aesthetic_approval') == 'not_claimed', 'Do not forge author approval')
    require(set(protocol['cases']) == {r['id'] for r in report['cases']} and len(report['cases']) == 6, 'Six actual cases required')
    for case in report['cases']:
        task = read_json(folder / 'cases' / case['id'] / 'task.json')
        require(case['status'] == 'pass' and len(case['criteria']) == len(task['criteria']), 'Unresolved case: ' + case['id'])
        require(not case.get('unresolved_blockers') and case.get('scope'), 'Missing scope or unresolved blocker')
        for criterion, original in zip(case['criteria'], task['criteria']):
            require(criterion.get('criterion') == original and criterion.get('status') == 'pass' and criterion.get('evidence'), 'Criterion lacks actual textual evidence')
        require(case.get('artifacts'), 'No actual artifacts')
        has_text = False
        for item in case['artifacts']:
            path = scoped_path(folder, item['path'])
            require(path.is_file() and digest(path) == item['sha256'], 'Changed writing evidence')
            if item['role'] == 'text':
                require(len(path.read_text().strip()) > 100, 'No substantial prose')
                has_text = True
        require(has_text, 'Editor notes alone cannot satisfy prose task')
    return {'cases': 6, 'method': 'Human-readable host textual review; script checks evidence integrity only',
            'relationship': report['relationship_disclosure'], 'review_sha256': digest(folder / 'results/review.json')}


def clean_install():
    from build_release import build
    from export_author_profile import export
    from build_agent_context import SCENARIO_FILES
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); package = tmp / 'product.zip'; build(package)
        with zipfile.ZipFile(package) as archive:
            require(not any('/workspace/' in n or '/work/' in n for n in archive.namelist()), 'Private folder in release')
            archive.extractall(tmp / 'install')
        installed = tmp / 'install' / ('touge-writing-reboot-skill-' + (ROOT / 'VERSION').read_text().strip())
        require(not (installed / 'workspace').exists(), 'Package includes workspace')
        commands = [['scripts/preflight_check.py'],
                    ['scripts/writing_workspace.py', 'init', '--id', 'fresh-novel', '--title', '合成小说', '--type', 'novel'],
                    ['scripts/writing_workspace.py', 'init', '--id', 'fresh-article', '--title', '合成文章', '--type', 'wechat'],
                    ['scripts/writing_workspace.py', 'resume', '--project', 'fresh-novel'],
                    ['scripts/writing_workspace.py', 'validate', '--project', 'fresh-article']]
        commands += [['scripts/build_agent_context.py', '--scenario', scenario, '--out', str(tmp / (scenario + '.md'))] for scenario in SCENARIO_FILES]
        commands += [['scripts/build_agent_context.py', '--scenario', kind, '--phase', phase, '--out', str(tmp/'method-context.md')]
                     for kind in ['wechat','novel'] for phase in ['plan','draft','review','revise','title']]
        for args in commands:
            proc = subprocess.run([sys.executable, *args], cwd=installed, capture_output=True, text=True)
            require(proc.returncode == 0, 'Clean install command failed: ' + str(args) + '\n' + proc.stderr + proc.stdout)
        profile = export(ROOT / 'shared/author-expression', tmp / 'author.zip')
        return {'clean_install_commands': len(commands), 'package_sha256': digest(package),
                'author_profile_files': profile['files'], 'initial_workspace_absent': True}


def private_migration(workspace):
    from backup_workspace import inventory
    from writing_workspace import resolve_project, validate, context
    evidence = workspace / 'acceptance-v2.1'
    baseline = read_json(evidence / 'baseline.json')
    book = resolve_project(workspace, 'black-forest')
    for item in baseline['novel_files']:
        require(digest(scoped_path(book, item['path'])) == item['sha256'], 'Original novel asset changed')
    extraction = read_json(evidence / 'method-extraction.json')
    require(len(extraction['rules']) == 36 and len(extraction['references']) == 7 and len(extraction['chapter_plans']) == 2, 'Incomplete method disposition')
    for row in extraction['sources']:
        require(digest(scoped_path(workspace,row['path'])) == row['sha256'], 'Extraction source changed')
    for row in extraction['rules']:
        require(row.get('kept_private') and row.get('disposition'), 'Unclassified rule')
    restore = read_json(evidence / 'upgrade-restore.json')
    require(restore['verified_restore'] and digest(restore['archive']) == restore['sha256'], 'No verified upgrade backup')
    import tarfile
    with tarfile.open(restore['archive'], 'r:gz') as archive:
        manifest = json.load(archive.extractfile('backup-manifest.json'))
    require(inventory(Path(restore['destination'])) == manifest['files'], 'Restored backup differs')
    regression = read_json(evidence / 'rollback.json')
    require(regression['v20_read_exit_code'] == 0 and regression['v21_read_exit_code'] == 0 and regression['original_files_unchanged'], 'Rollback smoke failed')
    for row in regression['artifacts']:
        require(digest(Path(row['path'])) == row['sha256'], 'Rollback evidence changed')
    require(not validate(book), 'Current novel registry invalid')
    return {'unchanged_novel_files': len(baseline['novel_files']), 'backup_files': restore['files'],
            'classified_rules': 36, 'reference_methods': 7, 'chapter_plan_inheritances_preserved': 2,
            'next_action': context(book)['state']['next_action'], 'rollback': 'v2.0 reads v2.1 extended copy'}


def actual_runs(workspace):
    from writing_run import verify
    receipt = read_json(workspace/'acceptance-v2.1/v21-behavior.json')
    require(receipt['source']=='independent_agent_forward_test_with_parent_reread' and len(receipt['cases'])==6, 'Missing new independent execution evidence')
    require(digest(receipt['report_path'])==receipt['report_sha256'], 'Independent report changed')
    parent=receipt['parent_review'];require(digest(scoped_path(ROOT,parent['path']))==parent['sha256'], 'Parent review changed')
    for case in receipt['cases']:
        manifest=Path(case['run_manifest']); project=manifest.parents[2]
        checked=verify(project,manifest.parent.name)
        require(checked['state']['stage']=='completed' and not checked['drift'], 'Writing run incomplete/drifted')
        require(checked['state']['registered_versions']==[], 'Synthetic trial must not fabricate manuscript acceptance')
        final=Path(case['final_text'])
        require(any(a['role']=='text' and a['sha256']==digest(final) for a in checked['state']['artifacts']), 'Final text not in actual run')
    return {'actual_runs':6,'acceptance_fabricated':False,'external_operations':False}


def run(workspace, public_only=False):
    workspace = Path(workspace).resolve()
    output = ROOT / 'work/acceptance-public-v2.1' if public_only else workspace / 'acceptance-v2.1'
    output.mkdir(parents=True, exist_ok=True)
    results = []; config = read_json(ROOT / 'configs/acceptance-v2.1.json')
    def check(name, function):
        try:
            detail = function(); row = {'id': name, 'status': 'passed', 'detail': detail}
        except (Exception, SystemExit) as exc:
            row = {'id': name, 'status': 'failed', 'detail': str(exc)}
        results.append(row); print(name + ': ' + row['status'], flush=True); return row
    def command(args, log):
        p = subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True)
        atomic_text(output/log,p.stdout+p.stderr);require(p.returncode==0,'See '+str(output/log))
        return {'log':log,'exit_code':p.returncode}
    legacy = None
    if not public_only:
        legacy = run_legacy(workspace, output/'legacy-regression', output/'skill-validation.json')
        write_json(output/'legacy-summary.json',legacy)
    def tests():
        if legacy:
            row=next(r for r in legacy['results'] if r['id']=='unit_tests')
            require(row['status']=='passed','Legacy/current tests failed');return row['detail']
        return command(['-m','unittest','discover','-s','tests','-v'],'unit-tests.txt')
    unit = check('A01',tests)
    def boundary():
        command(['scripts/preflight_check.py'],'preflight.txt')
        return clean_install()
    install = check('A02',boundary)
    def tested(names):
        require(unit['status']=='passed','Unit suite not passed')
        log=(output/'legacy-regression/unit-tests.txt') if legacy else output/'unit-tests.txt'
        text=log.read_text()
        for name in names:require(name+' (' in text and 'FAIL:' + name not in text,'Missing behavior case: '+name)
        return {'behavior_tests':names,'log':str(log.relative_to(output))}
    check('A03',lambda:tested(['test_both_manifest_formats_and_document_identity','test_search_and_delivery_are_not_read_or_fact_confirmation']))
    check('A04',lambda:tested(['test_mapping_many_to_many_without_relabeling_chapters']))
    def fiction():
        tested(['test_fiction_scope_and_schema_are_explicit','test_unrelated_issue_allows_trial_but_blocking_issue_needs_evidence'])
        return textual_evidence()
    check('A05',fiction)
    def writing_outputs():
        detail=textual_evidence()
        if not public_only:detail.update(actual_runs(workspace))
        return detail
    check('A06',writing_outputs)
    check('A07',textual_evidence)
    check('A08',lambda:tested(['test_trial_completion_never_accepts_manuscript','test_active_task_overrides_legacy_next_chapter_and_pins_actual_content','test_existing_accepted_text_survives_new_revision_run']))
    check('A09',lambda:tested(['test_artifact_copy_before_event_recovers_once','test_registration_after_content_commit_recovers_missing_event','test_input_drift_and_snapshot_tampering','test_public_definition_drift_keeps_pinned_version','test_historical_plan_inheritance_and_next_action']))
    if not public_only:
        check('A10',lambda:private_migration(workspace))
    check('A11',lambda:tested(['test_second_book_and_article_do_not_inherit_private_facts']))
    if not public_only:
        def external():
            require(legacy['all_in_scope_passed'],'Legacy migration/external regression not fully passed')
            record=read_json(output/'external-scope.json')
            require(record['mode']=='reused_verified_v2.0_evidence' and not record['new_live_test'],'Incorrect external scope')
            for row in record['unchanged_protocol_files']:
                require(digest(scoped_path(ROOT,row['path']))==row['sha256'],'MCP implementation changed; revalidate affected operations')
            return {'tencent_docs':'Existing live read/write/readback receipts revalidated, not newly tested',
                    'wechat':'documented_not_live_tested; explicitly excluded','protocol_files':len(record['unchanged_protocol_files'])}
        check('A12',external)
    def documentation():
        require(install['status']=='passed','Clean package/commands failed')
        require((ROOT/'VERSION').read_text().strip()==config['version'],'Version/config mismatch')
        from preflight_check import link_errors
        require(not link_errors(),'Broken documentation links')
        return {'version':config['version'],'clean_install':install['detail'],'links':'all public local paths resolved'}
    check('A13',documentation)
    expected={r['id'] for r in config['checks'] if not public_only or not r.get('private_required')}
    require(expected=={r['id'] for r in results},'Acceptance criteria/runner differ')
    passed=sum(r['status']=='passed' for r in results)
    report={'schema_version':1,'version':config['version'],'checked_at':datetime.now(timezone.utc).isoformat(),
            'mode':'public_self_check' if public_only else 'full_release_acceptance',
            'passed':passed,'total':len(results),'all_in_scope_passed':passed==len(results),
            'results':results,'excluded_by_user':config['excluded_by_user'],
            'limitations':config['limitations'],'full_release_claim':not public_only and passed==len(results)}
    write_json(output/'report.json',report)
    return report
