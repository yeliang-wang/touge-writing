"""v2.4 rules acceptance, preserving earlier release evidence."""
import importlib.util
import json
import re
import zipfile
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from acceptance import ROOT, require
from workspace_lib import read_json, write_json, atomic_text, digest, scoped_path


def config(root=ROOT):
    data = read_json(Path(root) / 'configs/acceptance-v2.4.json')
    rows = data['checks']
    require(len(rows) == 6 and {r['id'] for r in rows} == {'D%02d' % i for i in range(1, 7)}, 'Expected six distinct v2.4 checks')
    require({r['id'] for r in rows if r.get('private_required')} == {'D04', 'D06'}, 'Private checks must remain scoped')
    require(data['version'] == (Path(root) / 'VERSION').read_text().strip(), 'Version/config mismatch')
    return data


def independent_behavior(root=ROOT):
    root = Path(root); folder = root / 'evals/v2.4/rules-behavior'
    receipt = read_json(folder / 'result.json')
    require(receipt.get('source') == 'independent_agent_forward_test', 'Independent execution missing')
    require(receipt.get('all_in_scope_passed') is True, 'Behavior evaluation did not pass')
    cases = receipt['cases']
    require(len(cases) >= 2 and len({r['id'] for r in cases}) == len(cases), 'Distinct behavioral cases required')
    require(all(r.get('status') == 'passed' and r.get('observations') for r in cases), 'Behavioral observations missing')
    rows = receipt.get('artifacts', [])
    require(rows and len({r['path'] for r in rows}) == len(rows), 'Artifact inventory missing/duplicated')
    for row in rows:
        require(digest(scoped_path(folder, row['path'])) == row['sha256'], 'Behavior artifact changed')
    pins = receipt.get('evaluated_files', [])
    required = {'.agents/skills/touge-novel-writing/SKILL.md', '.agents/skills/touge-wechat-writing/SKILL.md',
                'scripts/writing_rules.py', 'scripts/writing_workspace.py', 'scripts/writing_run.py'}
    require(required <= {r['path'] for r in pins}, 'Evaluated implementation identity missing')
    for row in pins:
        require(digest(scoped_path(root, row['path'])) == row['sha256'], 'Behavior evaluated an older implementation: ' + row['path'])
    require(receipt.get('real_manuscripts_modified') is False and receipt.get('author_approval_claimed') is False,
            'Behavior scope overclaimed')
    return {'cases': len(cases), 'artifacts': len(rows), 'source': receipt['source'], 'literary_acceptance': False}


def private_rules(workspace, output):
    from writing_workspace import resolve_project, validate
    from writing_rules import resolve_rules
    before = read_json(output / 'protected-before.json')
    require(before.get('files'), 'Upgrade baseline inventory missing')
    for relative, expected in before['files'].items():
        require(digest(scoped_path(workspace, relative)) == expected, 'Protected content changed: ' + relative)
    catalog = read_json(workspace / 'catalog.json')
    summaries = []
    for item in catalog['projects']:
        project = resolve_project(workspace, item['id'])
        require(not validate(project), 'Invalid private content registry')
        meta = read_json(project / 'book.yaml')
        targets = [c['id'] for c in meta.get('chapters', [])] or ['article']
        for target in targets:
            resolved = resolve_rules(project, target, 'review')
            require(resolved.get('enabled') is True, 'Private work lacks enabled rules')
        summaries.append({'project_id': item['id'], 'targets_checked': len(targets)})
    with tempfile.TemporaryDirectory(prefix='touge-v24-offline-') as temp:
        clone = Path(temp) / 'workspace'
        shutil.copytree(workspace, clone, ignore=shutil.ignore_patterns('.git', 'acceptance*', '.writing.lock', '__pycache__'))
        for item in catalog['projects']:
            project = resolve_project(clone, item['id'])
            require(not validate(project), 'Offline copy content invalid')
            meta = read_json(project / 'book.yaml')
            for target in [c['id'] for c in meta.get('chapters', [])] or ['article']:
                resolve_rules(project, target, 'review')
    return {'protected_files': len(before['files']), 'projects': summaries, 'offline_rule_resolution': True,
            'manuscript_review_performed': False, 'historical_inheritance_unchanged': True}


def _external(argv):
    process = subprocess.run(argv, capture_output=True, text=True)
    require(process.returncode == 0, 'Remote verification failed: ' + ' '.join(argv[:3]))
    return process.stdout


def _github_slug(url):
    match = re.fullmatch(r'(?:https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?', url.strip())
    require(match, 'Publication requires an actual GitHub origin')
    return match.group(1)


def publication_evidence(workspace, output):
    receipt = read_json(output / 'publication.json')
    for name in ['public', 'private']:
        row = receipt[name]; clone = Path(row['clone'])
        require(clone.is_dir(), 'Missing actual recovery clone')
        head = subprocess.check_output(['git', '-C', str(clone), 'rev-parse', 'HEAD'], text=True).strip()
        origin = _external(['git', '-C', str(clone), 'remote', 'get-url', 'origin']).strip()
        slug = _github_slug(origin)
        live = json.loads(_external(['gh', 'repo', 'view', slug, '--json', 'nameWithOwner,visibility,defaultBranchRef']))
        require(live['nameWithOwner'].lower() == slug.lower(), 'GitHub repository identity differs')
        require(live['visibility'] == ('PRIVATE' if name == 'private' else 'PUBLIC'), 'Live GitHub visibility differs')
        branch = live['defaultBranchRef']['name']
        live_ref = _external(['git', '-C', str(clone), 'ls-remote', 'origin', 'refs/heads/' + branch]).split()
        require(len(live_ref) == 2 and live_ref[0] == head, 'Live GitHub branch differs')
        row['verified_repository'] = slug
        require(head == row['commit'], 'Clone commit differs')
        require(not subprocess.check_output(['git', '-C', str(clone), 'status', '--porcelain'], text=True).strip(), 'Clone is dirty')
        current = ROOT if name == 'public' else workspace
        require(_github_slug(_external(['git', '-C', str(current), 'remote', 'get-url', 'origin']).strip()) == slug, 'Local origin differs from recovery clone')
        require(subprocess.check_output(['git', '-C', str(current), 'rev-parse', 'HEAD'], text=True).strip() == head,
                'Publication receipt is stale')
        require(not subprocess.check_output(['git', '-C', str(current), 'status', '--porcelain'], text=True).strip(), 'Published checkout has changes')
        tracked = subprocess.check_output(['git', '-C', str(clone), 'ls-files', '-z']).decode().split('\0')[:-1]
        require(row.get('tracked_files') and set(tracked) == set(row['tracked_files']), 'Publication inventory incomplete')
        for relative, sha in row['tracked_files'].items():
            require(digest(scoped_path(clone, relative)) == sha == digest(scoped_path(current, relative)), 'Clone file differs')
        require(row['remote_head'] == head, 'Remote ref differs')
    require(receipt['private']['visibility'] == 'PRIVATE', 'Private workspace visibility not verified')
    asset = receipt['release_asset']
    require(digest(asset['download']) == asset['sha256'] == digest(asset['built']), 'Downloaded release asset differs')
    require(receipt['tag_commit'] == receipt['public']['commit'], 'Release tag differs')
    version = (ROOT / 'VERSION').read_text().strip(); tag = 'v' + version
    public_repo = receipt['public']['verified_repository']
    release = json.loads(_external(['gh', 'release', 'view', tag, '--repo', public_repo, '--json', 'url,tagName,isDraft,assets']))
    require(not release['isDraft'] and release['tagName'] == tag and release['url'] == receipt['release_url'], 'Live release identity differs')
    remote_tags = _external(['git', '-C', str(ROOT), 'ls-remote', 'origin', 'refs/tags/' + tag, 'refs/tags/' + tag + '^{}'])
    tags = {line.split()[1]: line.split()[0] for line in remote_tags.splitlines()}
    require(tags.get('refs/tags/' + tag + '^{}', tags.get('refs/tags/' + tag)) == receipt['public']['commit'], 'Live release tag commit differs')
    asset_name = 'touge-writing-' + version + '.zip'
    require(sum(a['name'] == asset_name for a in release['assets']) == 1, 'Missing/duplicate GitHub release asset')
    with tempfile.TemporaryDirectory(prefix='touge-release-readback-') as temp:
        _external(['gh', 'release', 'download', tag, '--repo', public_repo, '--pattern', asset_name, '--dir', temp])
        actual = Path(temp) / asset_name
        require(digest(actual) == asset['sha256'], 'Fresh remote release download differs')
        with zipfile.ZipFile(actual) as zipped:
            prefix = 'touge-writing-' + version + '/'
            manifest = json.loads(zipped.read(prefix + 'release-manifest.json'))
            require(manifest['version'] == version and manifest['workspace_included'] is False, 'Release manifest scope/version differs')
            listed = manifest['files']
            require(len({r['path'] for r in listed}) == len(listed), 'Duplicate release manifest entries')
            require(set(zipped.namelist()) == {prefix + r['path'] for r in listed} | {prefix + 'release-manifest.json'}, 'Release ZIP membership differs')
            import hashlib
            for member in listed:
                require(hashlib.sha256(zipped.read(prefix + member['path'])).hexdigest() == member['sha256'], 'Remote ZIP member hash differs')
                require(digest(scoped_path(ROOT, member['path'])) == member['sha256'], 'Remote asset differs from published source')
    from writing_workspace import validate, resolve_project
    from writing_rules import resolve_rules
    private_clone = Path(receipt['private']['clone'])
    for row in read_json(private_clone / 'catalog.json')['projects']:
        project = resolve_project(private_clone, row['id']); require(not validate(project), 'Remote clone content invalid')
        meta = read_json(project / 'book.yaml')
        for target in [c['id'] for c in meta.get('chapters', [])] or ['article']:
            resolve_rules(project, target, 'review')
    return {'public_commit': receipt['public']['commit'], 'private_commit': receipt['private']['commit'],
            'release_url': receipt['release_url'], 'asset_sha256': asset['sha256'], 'recovery_clones_verified': True}


def run(workspace, public_only=False):
    workspace = Path(workspace).expanduser().resolve(); cfg = config()
    output = ROOT / 'work/acceptance-public-v2.4.0' if public_only else workspace / 'acceptance-v2.4.0'
    output.mkdir(parents=True, exist_ok=True); results = []
    def command(args, filename):
        p = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
        atomic_text(output / filename, p.stdout + p.stderr)
        require(p.returncode == 0, 'See ' + str(output / filename))
        return {'log': filename, 'exit_code': 0}
    def check(ident, fn):
        try: row = {'id': ident, 'status': 'passed', 'detail': fn()}
        except (Exception, SystemExit) as exc: row = {'id': ident, 'status': 'failed', 'detail': str(exc)}
        results.append(row); print(ident + ': ' + row['status'], flush=True)
    def basic():
        from acceptance_v23 import skill_metadata
        from preflight_check import link_errors
        unit = command(['-m', 'unittest', 'discover', '-s', 'tests', '-v'], 'unit-tests.txt')
        boundary = command(['scripts/preflight_check.py'], 'preflight.txt')
        require(not link_errors(), 'Broken public documentation links')
        return {'tests': unit, 'boundary': boundary, 'skills': skill_metadata()}
    def install():
        from acceptance_v23 import clean_install, shared_methods
        return {'clean_install': clean_install(), 'shared_methods': shared_methods()}
    def behavior():
        from acceptance_v23 import historical_evidence, git_collaboration_evidence
        log = command(['evals/v2.3/git-collaboration/run_evaluation.py', '--out', str(output / 'git-current')], 'git-current.txt')
        with tempfile.TemporaryDirectory() as temp:
            mirror = Path(temp); folder = mirror / 'evals/v2.3/git-collaboration'
            shutil.copytree(output / 'git-current', folder / 'evidence')
            result = read_json(output / 'git-current/result.json')
            for row in result['evaluated_files']:
                dest = mirror / row['path']; dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / row['path'], dest)
            git_result = git_collaboration_evidence(mirror)
        protocols = read_json(ROOT / 'configs/acceptance-v2.3.json')['unchanged_external_protocols']
        for path, sha in protocols.items():
            require(digest(scoped_path(ROOT, path)) == sha, 'External protocol changed; affected live checks required')
        return {'current_git_cli': git_result, 'execution': log, 'historical_integrity': historical_evidence(),
                'external_protocols_unchanged': protocols, 'new_live_mcp_checks': False,
                'rules_regression': command(['-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_rules_v24.py', '-v'], 'rules-tests.txt')}
    check('D01', basic); check('D02', install); check('D03', behavior)
    if not public_only: check('D04', lambda: private_rules(workspace, output))
    check('D05', independent_behavior)
    if not public_only: check('D06', lambda: publication_evidence(workspace, output))
    expected = {r['id'] for r in cfg['checks'] if not public_only or not r.get('private_required')}
    require({r['id'] for r in results} == expected, 'Acceptance scope differs')
    passed = sum(r['status'] == 'passed' for r in results)
    report = {'schema_version': 1, 'version': cfg['version'], 'checked_at': datetime.now(timezone.utc).isoformat(),
              'mode': 'public_self_check' if public_only else 'full_release_acceptance', 'passed': passed, 'total': len(results),
              'all_in_scope_passed': passed == len(results), 'full_release_claim': not public_only and passed == len(results),
              'results': results, 'excluded_by_user': cfg['excluded_by_user'], 'limitations': cfg['limitations']}
    write_json(output / 'report.json', report); return report
