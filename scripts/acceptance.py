#!/usr/bin/env python3
"""Run local checks and inspect real private migration, behavior and MCP evidence."""
import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from workspace_lib import read_json, write_json, scoped_path, digest
from migrate_workspace import verify
from writing_workspace import validate, context, resolve_project, derive_state
from export_author_profile import export
from backup_workspace import inventory

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition: raise ValueError(message)


def payload(path):
    rpc = read_json(path)
    require(not rpc.get('error'), 'JSON-RPC error')
    r = rpc['result']; require(not r.get('isError'), 'MCP tool error')
    result = r.get('structuredContent') or json.loads(next(x['text'] for x in r['content'] if x['type'] == 'text'))
    require(not result.get('error'), 'MCP business error')
    return result


def run(workspace):
    workspace = Path(workspace).resolve(); evidence = workspace / 'acceptance'; evidence.mkdir(parents=True, exist_ok=True)
    config = read_json(ROOT / 'configs/acceptance.json')
    results = []
    def check(name, function):
        try:
            detail = function()
            results.append({'id': name, 'status': 'passed', 'detail': detail})
        except (Exception, SystemExit) as exc:
            results.append({'id': name, 'status': 'failed', 'detail': str(exc)})
        print(name + ': ' + results[-1]['status'], flush=True)

    def command(args, log):
        proc = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
        from workspace_lib import atomic_text
        atomic_text(evidence / log, proc.stdout + proc.stderr)
        require(proc.returncode == 0, 'See acceptance/' + log)
        return {'log': log, 'exit_code': proc.returncode}

    check('unit_tests', lambda: command(['-m', 'unittest', 'discover', '-s', 'tests', '-v'], 'unit-tests.txt'))
    check('public_boundary', lambda: command(['scripts/preflight_check.py'], 'preflight.txt'))

    def source_migration():
        receipt = read_json(workspace / 'archives/migration-receipt.json')
        errors = verify(receipt, workspace, check_sources=True)
        require(not errors, 'Source/archive mismatches: ' + str(len(errors)))
        require(receipt['files'] == len(receipt['entries']) > 0, 'Invalid receipt count')
        return {'files': receipt['files'], 'originals_unchanged': True, 'sha256_verified': True}
    check('migration_integrity', source_migration)

    def curation():
        entries = read_json(workspace / 'archives/curation-receipt.json')['entries']
        for r in entries:
            require(digest(scoped_path(workspace, r['source'])) == r['sha256'] == digest(scoped_path(workspace, r['destination'])), 'Curated copy differs')
        return {'byte_preserving_copies': len(entries)}
    check('curation_integrity', curation)

    def corpus():
        rows = read_json(workspace/'corpus/manifest.json')
        require(len({r['id'] for r in rows}) == len(rows), 'Duplicate corpus IDs')
        originals = {p.name:p for p in (workspace/'archives/author-corpus/original').rglob('*.md')}
        for r in rows:
            p=scoped_path(workspace/'corpus',r['markdown'])
            require(p.name in originals and digest(p)==digest(originals[p.name]), 'Changed/missing corpus body')
        require(len(rows)==352 and sum(r.get('word_count',0)>0 for r in rows)==341, 'Migration corpus coverage changed')
        require(bool(read_json(workspace/'corpus/coverage.json')), 'Missing coverage disclosure')
        return {'indexed_articles':len(rows),'usable_bodies':341,'preexisting_empty_bodies':11}
    check('corpus_integrity', corpus)

    def writing_state():
        catalog=read_json(workspace/'catalog.json')
        for item in catalog['projects']:
            project=scoped_path(workspace,item['path']); require(not validate(project),'Invalid versions: '+item['id'])
            require(read_json(project/'state.json')==derive_state(project),'Stale state cache: '+item['id'])
        book=resolve_project(workspace,'black-forest');ctx=context(book)
        require(ctx['state']['book_plan']=='book-plan-1.2','Wrong active book plan')
        require(ctx['state']['next_action']=={'chapter_id':'ch02','action':'review_chapter_plan'},'Wrong next stage')
        rows={r['id']:r for r in read_json(book/'版本记录/revisions.json')['revisions']}
        require(rows['prologue-plan-0.2']['parent_plan_id']=='book-plan-1.2','Prologue inheritance changed')
        require(rows['ch01-plan-0.5']['parent_plan_id']=='book-plan-1.1','Chapter 1 historical inheritance changed')
        require(rows['prologue-text-1.0']['status']==rows['ch01-text-1.0']['status']=='accepted','Accepted baseline lost')
        # Recover the saved workflow state; editorial findings are not release criteria.
        return {'registered_versions':len(rows),'next_action':ctx['state']['next_action'],'historical_inheritance_preserved':True}
    check('writing_state_and_inheritance', writing_state)

    def profile():
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'author.zip';result=export(ROOT/'shared/author-expression',output)
            with zipfile.ZipFile(output) as z:
                require(len(z.namelist())==8,'Unexpected package contents')
            return {'files':result['files'],'sha256':result['sha256']}
    check('shareable_author_profile', profile)

    def contexts():
        from build_agent_context import SCENARIO_FILES
        with tempfile.TemporaryDirectory() as tmp:
            for scenario in SCENARIO_FILES:
                output=Path(tmp)/(scenario+'.md')
                proc=subprocess.run([sys.executable,str(ROOT/'scripts/build_agent_context.py'),'--scenario',scenario,'--out',str(output)],capture_output=True,text=True)
                require(proc.returncode==0 and output.stat().st_size>100,'Context build failed: '+scenario)
            # A real retrieval using private source bodies, not a fixture.
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/private_retriever.py'),'--manifest',str(workspace/'corpus/manifest.json'),'--query','技术人 职业选择','--top-k','3'],capture_output=True,text=True)
            require(proc.returncode==0,'Private retrieval failed');hits=json.loads(proc.stdout)['results']
            require(len(hits)==3 and all(h.get('source_id') and Path(h['markdown_path']).is_file() for h in hits),'Retrieval lacks provenance')
            proc=subprocess.run([sys.executable,str(ROOT/'scripts/build_robot_prompt.py'),'--mode','wechat_public_article','--topic','技术人 职业选择','--manifest',str(workspace/'corpus/manifest.json'),'--out',str(Path(tmp)/'prompt.md')],capture_output=True,text=True)
            require(proc.returncode==0,'WeChat prompt build failed')
            return {'context_scenarios':len(SCENARIO_FILES),'grounded_hits':len(hits),'wechat_prompt_built':True}
    check('context_and_retrieval', contexts)

    def skills():
        receipt=read_json(evidence/'skill-validation.json')
        require(len(receipt['skills'])==3,'Missing skill validation')
        for r in receipt['skills']:
            require(r['exit_code']==0 and digest(scoped_path(ROOT,r['file']))==r['sha256'],'Skill changed or failed validator')
        return {'validated_skills':3,'validator':receipt['validator']}
    check('skill_structure', skills)

    def behavior():
        r=read_json(evidence/'behavior.json')
        require(r['source']=='independent_agent_forward_test' and len(r['cases'])==2,'Missing independent cases')
        require(r['routing_and_stage_passed'] and r['factual_boundaries_passed'] and not r['unresolved_engineering_defects'],'Behavior review failed')
        for item in r['artifacts']:require(digest(scoped_path(workspace,item['path']))==item['sha256'],'Changed behavior evidence')
        return {'cases':r['cases'],'scope':'routing, saved stage and source-use boundaries only',
                'manuscript_editorial_review_required':False,'artifact_count':len(r['artifacts'])}
    check('independent_writing_behavior', behavior)

    def tencent():
        folder=evidence/'tencent-docs';summary=read_json(folder/'live-summary.json')
        require(summary['source']=='live_mcp' and summary['readback_matches'],'Missing live summary')
        require(payload(folder/'account.json').get('user_id'),'No authenticated account')
        require(len(payload(folder/'existing-plan.json')['content'])>100,'No real existing Word read')
        created=payload(folder/'create-response.json')['data'];edited=payload(folder/'test-edit.json')['data']
        require(created['file_id']==summary['target_file_id'],'Wrong created document')
        require(created['version']!=edited['version'],'No document version increment')
        require(payload(folder/'test-structure-before.json')['data']['nodes'],'No pre-write structure read')
        before=payload(folder/'test-read-before.json')['content'];after=payload(folder/'test-read-after.json')['content']
        require('TOUGE-V2-ACCEPTANCE-20260930' in before and '验收状态：初始版本。' in before,'Wrong acceptance content')
        require(after==before.replace('验收状态：初始版本。','验收状态：已完成真实修改与回读。'),'Full readback differs')
        cloud=read_json(scoped_path(workspace,summary['cloud_inventory']))
        all_ids={n['node_id'] for f in cloud['folders'] for n in f['response'].get('children',[]) if n['node_type']!='wiki_folder'}
        rows=cloud['documents'];require(all_ids=={r['node_id'] for r in rows},'Cloud inventory not fully read')
        for r in rows:
            require(r['status']=='read_verified' and digest(scoped_path(workspace,r['path']))==r['sha256'],'Missing/changed cloud snapshot')
            require(payload(scoped_path(workspace,r['receipt']))['content']==scoped_path(workspace,r['path']).read_text(),'Snapshot differs from MCP receipt')
        require(any(r['doc_type']=='excel' for r in rows),'No existing directory sheet read')
        operation=read_json(scoped_path(workspace,summary['ledger_operation_path']))
        require(operation['status']=='verified' and operation['remote_id']==summary['target_file_id'],'Live operation ledger not verified')
        project=scoped_path(workspace,summary['ledger_project'])
        require(not validate(project),'Ledger revision invalid')
        event=operation['events'][-1];receipt_path=scoped_path(project,event['evidence'])
        require(digest(receipt_path)==event['sha256'],'Live operation evidence changed')
        receipt=read_json(receipt_path)
        require(receipt['source']=='live_mcp' and receipt['readback_matches'],'Invalid ledger evidence')
        require(receipt['local_sha256']==operation['local_sha256'],'Wrong ledger revision')
        require(payload(folder/'ledger-read-after.json')['content']==receipt['readback_content'],'Ledger readback mismatch')
        require(__import__('hashlib').sha256(receipt['readback_content'].encode()).hexdigest()==operation['local_sha256'],'Readback differs from selected local revision')
        return {'live_actions':summary['verified_actions'],'document_count':len(rows),'space_directories':len({f['parent_id'] for f in cloud['folders']}),'test_document':summary['target_url'],'originals_modified':False}
    check('tencent_docs_live', tencent)

    def backup_restore():
        r=read_json(evidence/'backup-restore.json')
        require(r['verified_restore'],'No verified restore')
        require(digest(r['archive'])==r['sha256'],'Backup archive changed')
        import tarfile
        with tarfile.open(r['archive'],'r:gz') as z:manifest=json.load(z.extractfile('backup-manifest.json'))
        require(inventory(Path(r['destination']))==manifest['files'],'Restored workspace differs from backup')
        restored=Path(r['destination'])
        book=resolve_project(restored,'black-forest')
        require(not validate(book) and context(book)['state']['next_action']['chapter_id']=='ch02','Restored writing state unusable')
        return {'files':r['files'],'source_bytes':r['source_bytes'],'archive_sha256':r['sha256'],'restored_resume_passed':True}
    check('backup_restore', backup_restore)
    expected={r['id'] for r in config['required_checks']}
    require(expected=={r['id'] for r in results},'Acceptance criteria and runner differ')
    passed=sum(r['status']=='passed' for r in results)
    report={'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),'version':(ROOT/'VERSION').read_text().strip(),
            'passed':passed,'total':len(results),'all_in_scope_passed':passed==len(results),'results':results,
            'excluded_by_user':config['excluded_by_user'],'scope_notes':config['scope_notes']}
    write_json(evidence/'report.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,default=Path('workspace'))
    a=p.parse_args();r=run(a.workspace);print('Acceptance: %s/%s in-scope checks passed' % (r['passed'],r['total']))
    raise SystemExit(0 if r['all_in_scope_passed'] else 1)


if __name__=='__main__': main()
