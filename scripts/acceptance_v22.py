"""v2.2 checks: explicit external workspace, independent collaborators, immutable migration."""
import json
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from acceptance import ROOT, require, run_legacy
from acceptance_v21 import textual_evidence, private_migration
from workspace_lib import read_json, write_json, atomic_text, digest, scoped_path


def clean_install():
    from build_release import build, distribution_directory
    from export_author_profile import export
    from build_agent_context import SCENARIO_FILES
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve(); package = tmp/'public.zip'; build(package)
        with zipfile.ZipFile(package) as archive:
            members = [Path(n).parts[1:] for n in archive.namelist()]
            require(all(p and p[0] not in {'workspace', 'work', 'dist', 'outputs'} for p in members), 'Private root in release')
            archive.extractall(tmp/'install')
        installed = tmp/'install'/distribution_directory((ROOT/'VERSION').read_text().strip())
        private = tmp/'private work'; other_cwd = tmp/'another cwd'; other_cwd.mkdir()
        script = str(installed/'scripts/writing_workspace.py')
        count = 0
        def command(args, cwd=installed):
            nonlocal count
            p = subprocess.run([sys.executable,*args],cwd=cwd,capture_output=True,text=True)
            require(p.returncode == 0, 'Clean install failed: '+str(args)+'\n'+p.stderr+p.stdout)
            count += 1
            return p.stdout
        command(['scripts/preflight_check.py'])
        require(not (installed/'workspace').exists(), 'Private workspace shipped')
        for kind in ['novel','wechat']:
            command([script,'--workspace',str(private),'init','--id',kind,'--title','Synthetic '+kind,'--type',kind],other_cwd)
            resume = json.loads(command([script,'--workspace',str(private),'resume','--project',kind]))
            require(resume['workspace'] == str(private) and Path(resume['project_path']).is_relative_to(private), 'Wrong workspace selected')
        require(not (installed/'workspace').exists() and not (other_cwd/'workspace').exists(), 'Explicit path leaked into cwd')
        command([script,'init','--id','legacy','--title','Legacy','--type','wechat'])
        command([script,'resume','--project','legacy'])
        require((installed/'workspace/catalog.json').exists(), 'Legacy default changed')
        for scenario in SCENARIO_FILES:
            command(['scripts/build_agent_context.py','--scenario',scenario,'--out',str(tmp/(scenario+'.md'))])
        for kind in ['wechat','novel']:
            for phase in ['plan','draft','review','revise','title']:
                command(['scripts/build_agent_context.py','--scenario',kind,'--phase',phase,'--out',str(tmp/'phase.md')])
        profile = export(installed/'shared/author-expression',tmp/'author.zip')
        return {'commands':count,'package_sha256':digest(package),'external_workspace':True,
                'legacy_default_preserved':True,'author_profile_files':profile['files']}


def collaboration_evidence():
    folder = ROOT/'evals/v2.2'; report = read_json(folder/'review.json')
    require(report.get('source') == 'independent_agent_forward_test_with_parent_review', 'Missing behavioral review')
    require(report.get('live_cloud_tested') is False and report.get('author_approval_claimed') is False, 'Incorrect evidence scope')
    context_ref = report['evaluated_context']
    context_path = scoped_path(folder,context_ref['path'])
    require(digest(context_path)==context_ref['sha256'], 'Evaluated context record changed')
    for row in read_json(context_path)['files']:
        require(digest(scoped_path(ROOT,row['path']))==row['sha256'], 'Behavior context changed; repeat affected evaluation')
    expected = {'novel-shared-baseline-conflict','wechat-confirmed-import'}
    require(len(report['cases']) == len(expected) and {r['id'] for r in report['cases']} == expected, 'Missing/duplicate collaborative cases')
    for row in report['cases']:
        require(row['status'] == 'passed' and row['observations'], 'Unresolved behavioral case')
        require({'input','transcript','result'} <= {r.get('role') for r in row['artifacts']}, 'Missing actual collaboration artifacts')
        for item in row['artifacts']:
            require(digest(scoped_path(folder,item['path'])) == item['sha256'], 'Changed collaboration artifact')
    return {'cases':len(report['cases']),'live_cloud_tested':False,'report_sha256':digest(folder/'review.json')}


def migration(workspace):
    from backup_workspace import inventory
    from writing_workspace import resolve_project,context,validate
    receipt = read_json(workspace/'acceptance-v2.2/migration.json')
    require(Path(receipt['destination']).resolve() == workspace.resolve(), 'Receipt belongs to another target')
    require(receipt['source_retained'] and receipt['source_files_unchanged'], 'Source not preserved')
    rows = receipt['original_files']; source = Path(receipt['source'])
    require(inventory(source) == rows, 'Original workspace changed since migration')
    for r in rows:
        path = scoped_path(workspace,r['path'])
        require(path.is_file() and path.stat().st_size == r['bytes'] and digest(path) == r['sha256'], 'Changed migrated member: '+r['path'])
    backup = receipt['backup']
    require(backup['verified_restore'] and digest(backup['archive']) == backup['sha256'], 'Migration backup/restore invalid')
    import tarfile
    with tarfile.open(backup['archive'], 'r:gz') as archive:
        manifest = json.load(archive.extractfile('backup-manifest.json'))
    require(manifest['files'] == rows, 'Backup does not contain the complete original workspace')
    book = resolve_project(workspace,'black-forest')
    require(not validate(book) and context(book)['state'] == receipt['source_state'], 'Recovered book state differs')
    require(receipt['source_state'] == receipt['destination_state'], 'Migration state mismatch')
    old_report = read_json(workspace/'acceptance-v2.1/report.json')
    require(old_report['all_in_scope_passed'], 'Historical v2.1 release was incomplete')
    original_v21 = private_migration(workspace)
    classification = read_json(workspace/'acceptance-v2.2/reference-classification.json')
    require(classification['migration_sha256'] == digest(workspace/'acceptance-v2.2/migration.json'), 'Reference classification is stale')
    updates = {r['path']:r for r in classification.get('public_dependency_updates',[])}
    from preflight_check import public_paths
    public_files = {(ROOT/p).resolve() for p in public_paths()}
    for path, row in receipt['external_references'].items():
        if row['kind'] != 'file':
            continue
        current = Path(path)
        if path in updates:
            update = updates[path]
            require(current.resolve() in public_files and digest(update['preserved_snapshot']) == row['sha256'], 'Missing original public dependency snapshot')
            require(digest(current) == update['current_sha256'], 'Updated public dependency changed again')
        else:
            require(current.is_file() and digest(current) == row['sha256'], 'Retained external evidence changed: '+path)
    # Run the complete published v2.1 script set, not old CLI against new helpers.
    import tarfile
    rollback = read_json(workspace/'acceptance-v2.2/rollback-code.json')
    require(rollback['version'] == '2.1.0' and digest(rollback['archive']) == rollback['sha256'], 'Rollback code changed')
    with tempfile.TemporaryDirectory() as tmp:
        old = Path(tmp).resolve()
        with tarfile.open(rollback['archive']) as archive:
            # Published compatibility symlinks are expanded to ordinary files.
            # Never create links from an evidence archive on the host filesystem.
            for member in archive.getmembers():
                target = scoped_path(old, member.name)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                source_member = member
                if member.issym():
                    source = (old/Path(member.name).parent/member.linkname).resolve()
                    require(source.is_relative_to(old), 'Rollback link escapes archive')
                    source_member = archive.getmember(source.relative_to(old).as_posix())
                require(source_member.isfile(), 'Unsafe rollback member')
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(source_member) as stream:
                    target.write_bytes(stream.read())
        require((old/'VERSION').read_text().strip() == '2.1.0', 'Wrong rollback version')
        for action in ['validate','resume']:
            p = subprocess.run([sys.executable,str(old/'scripts/writing_workspace.py'),'--workspace',str(workspace),action,'--project','black-forest'],
                               cwd=old,capture_output=True,text=True)
            require(p.returncode == 0, 'v2.1 rollback read failed: '+p.stderr)
    missing = {p for p,r in receipt['external_references'].items() if r['kind']=='historical_unavailable'}
    require(missing == set(classification['historical_temporary_files']) | set(classification['protocol_relative_urls']), 'Unclassified old reference')
    return {'files':len(rows),'novel_files':receipt['novel_original_files'],
            'source_retained':True,'external_references':len(receipt['external_references']),
            'public_dependency_updates_with_preserved_snapshots':len(updates),
            'historical_temporary_refs':len(classification['historical_temporary_files']),
            'protocol_relative_urls':len(classification['protocol_relative_urls']),
            'v21_cli_reads_relocated_schema':True,'legacy_integrity':original_v21}


def run(workspace, public_only=False):
    workspace = Path(workspace).expanduser().resolve()
    output = ROOT/'work/acceptance-public-v2.2' if public_only else workspace/'acceptance-v2.2'
    output.mkdir(parents=True,exist_ok=True)
    config = read_json(ROOT/'configs/acceptance-v2.2.json'); results = []
    def check(ident, fn):
        try: row = {'id':ident,'status':'passed','detail':fn()}
        except (Exception,SystemExit) as exc: row = {'id':ident,'status':'failed','detail':str(exc)}
        results.append(row); print(ident+': '+row['status'],flush=True); return row
    def command(args, filename):
        p = subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True)
        atomic_text(output/filename,p.stdout+p.stderr)
        require(p.returncode == 0,'See '+str(output/filename))
        return {'log':filename,'exit_code':0}
    check('B01',lambda:command(['-m','unittest','discover','-s','tests','-v'],'unit-tests.txt'))
    check('B02',lambda:command(['scripts/preflight_check.py'],'preflight.txt'))
    check('B03',clean_install)
    def methods():
        from capability_catalog import catalog
        from export_author_profile import export
        require(len({row['id'] for row in catalog()['capabilities']}) == 13,'Method registry changed')
        with tempfile.TemporaryDirectory() as tmp:
            result = export(ROOT/'shared/author-expression',Path(tmp)/'author.zip')
        require(result['sha256']=='aea0138e25a141295214cd3b47ef17324d1ff30ab03d27d78af9685cec67ebcb','Author package changed without new version')
        return {'methods':13,'author_profile':'1.0.0','sha256':result['sha256']}
    check('B04',methods)
    check('B05',collaboration_evidence)
    check('B06',textual_evidence)
    def documentation():
        from preflight_check import link_errors
        require((ROOT/'VERSION').read_text().strip()==config['version'],'Version mismatch')
        require(not link_errors(),'Broken documentation links')
        return {'version':config['version'],'links':'verified'}
    check('B07',documentation)
    if not public_only:
        check('B08',lambda:migration(workspace))
        def legacy():
            result = run_legacy(workspace,output/'legacy-regression',output/'skill-validation.json')
            require(result['all_in_scope_passed'],'Legacy evidence failed; see separate regression report')
            return {'passed':result['passed'],'total':result['total'],'tencent_evidence':'historical live receipts revalidated'}
        check('B09',legacy)
        def external():
            record = read_json(workspace/'acceptance-v2.1/external-scope.json')
            protocols = record['unchanged_protocol_files']
            require(len(protocols)==2 and {r['path'] for r in protocols} == {'scripts/configure_tencent_docs.py','scripts/external_operations.py'}, 'Missing/duplicate external protocol files')
            for row in protocols:
                require(digest(scoped_path(ROOT,row['path'])) == row['sha256'],'External protocol changed; needs live validation')
            receipt = read_json(output/'skill-validation.json')
            require(len(receipt['skills'])==3 and {r['file'] for r in receipt['skills']} == {'SKILL.md','.agents/skills/touge-wechat-writing/SKILL.md','.agents/skills/touge-novel-writing/SKILL.md'},'Missing/duplicate Skill checks')
            for row in receipt['skills']:
                require(row['exit_code']==0 and digest(scoped_path(ROOT,row['file']))==row['sha256'],'Changed/unvalidated Skill')
            return {'new_live_test':False,'unchanged_protocols':len(record['unchanged_protocol_files']),
                    'skills':3,'wechat_live':'excluded_by_user','multi_account_merge':'not_claimed'}
        check('B10',external)
    expected = {r['id'] for r in config['checks'] if not public_only or not r.get('private_required')}
    require(expected == {r['id'] for r in results},'Acceptance criteria differ from runner')
    passed = sum(r['status']=='passed' for r in results)
    report = {'schema_version':1,'version':config['version'],'checked_at':datetime.now(timezone.utc).isoformat(),
              'mode':'public_self_check' if public_only else 'full_release_acceptance','passed':passed,'total':len(results),
              'all_in_scope_passed':passed==len(results),'full_release_claim':not public_only and passed==len(results),
              'results':results,'excluded_by_user':config['excluded_by_user'],'limitations':config['limitations']}
    write_json(output/'report.json',report)
    return report
