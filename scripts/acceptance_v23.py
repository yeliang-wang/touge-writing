"""v2.3 acceptance: scoped private Git workspaces and truthful evidence boundaries."""
import json
import hashlib
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from acceptance import ROOT, require
from workspace_lib import read_json, write_json, atomic_text, digest, scoped_path


GIT_CASES = {'initial-clone', 'candidate-integration', 'stale-baseline',
             'package-tampering', 'concurrent-official-write', 'recovery-clone'}
SKILLS = {'SKILL.md': 'touge-writing',
          '.agents/skills/touge-novel-writing/SKILL.md': 'touge-novel-writing',
          '.agents/skills/touge-wechat-writing/SKILL.md': 'touge-wechat-writing'}


def evidence_suffix(root=ROOT):
    """Preserve the original v2.3 receipt folder; isolate every patch release."""
    version = (Path(root) / 'VERSION').read_text().strip()
    require(re.fullmatch(r'2\.3\.(?:0|[1-9][0-9]*)', version), 'Expected a v2.3 release version')
    return 'v2.3' if version == '2.3.0' else 'v' + version


def receipt_directory(workspace, root=ROOT):
    return Path(workspace) / ('acceptance-' + evidence_suffix(root))


def output_directory(workspace, public_only=False, root=ROOT):
    if public_only:
        return Path(root) / 'work' / ('acceptance-public-' + evidence_suffix(root))
    return receipt_directory(workspace, root)


def acceptance_config(root=ROOT):
    config = read_json(Path(root) / 'configs/acceptance-v2.3.json')
    rows = config.get('checks', [])
    require(len(rows) == 10 and {r.get('id') for r in rows} == {'C%02d' % n for n in range(1, 11)},
            'v2.3 requires exactly ten unique acceptance checks')
    require({r['id'] for r in rows if r.get('private_required')} == {'C08', 'C09', 'C10'}, 'Private acceptance scope changed')
    return config


def checked_rows(root, rows, path_field='path'):
    require(isinstance(rows, list) and rows, 'Missing file inventory')
    seen = set()
    for row in rows:
        relative = row[path_field]
        require(relative not in seen, 'Duplicate inventory member: ' + relative)
        seen.add(relative)
        path = scoped_path(root, relative)
        require(path.is_file() and not path.is_symlink(), 'Missing/non-regular inventory member: ' + relative)
        require(digest(path) == row['sha256'], 'File hash differs: ' + relative)
        if 'bytes' in row:
            require(path.stat().st_size == row['bytes'], 'File size differs: ' + relative)
    return len(seen)


def git_collaboration_evidence(root=ROOT):
    root = Path(root); folder = root / 'evals/v2.3/git-collaboration'; evidence = folder / 'evidence'
    protocol = read_json(folder / 'protocol.json'); report = read_json(evidence / 'result.json')
    require(protocol.get('source') == report.get('source') == 'independent_agent_forward_test', 'Missing independent execution identity')
    require(report.get('all_in_scope_passed') is True and report.get('same_host_local_git_only') is True, 'Git evaluation failed or overclaims scope')
    for key in ['live_github_accounts_tested', 'live_cloud_tested', 'real_author_approval_claimed']:
        require(report.get(key) is False, 'Incorrect evaluation scope: ' + key)
    for rows in [protocol['cases'], report['cases']]:
        require(len(rows) == len(GIT_CASES) and {r['id'] for r in rows} == GIT_CASES, 'Missing/duplicate Git evaluation cases')
    cases = {r['id']: r for r in report['cases']}
    for row in cases.values():
        require(row['status'] == 'passed' and row.get('observations'), 'Git case lacks a passed observation')
    evaluated = report.get('evaluated_files', [])
    required_code = {'scripts/git_collaboration.py', 'scripts/writing_workspace.py', 'scripts/writing_run.py',
                     'scripts/workspace_lib.py', 'evals/v2.3/git-collaboration/protocol.json',
                     'evals/v2.3/git-collaboration/run_evaluation.py'}
    require({r['path'] for r in evaluated} == required_code, 'Missing evaluated code/criteria hashes')
    checked_rows(root, evaluated)
    artifacts = report.get('artifacts', [])
    required_artifacts = {'transcript.json', 'official-inventory.json', 'accepted-state.json'}
    require({r['path'] for r in artifacts} == required_artifacts, 'Missing actual Git evaluation receipts')
    checked_rows(evidence, artifacts)
    transcript = read_json(evidence / 'transcript.json')
    require(isinstance(transcript, list) and len(transcript) >= 20, 'No substantial command transcript')
    require(all(isinstance(r.get('argv'), list) and r['argv'] and isinstance(r.get('exit_code'), int)
                and isinstance(r.get('stdout'), str) and isinstance(r.get('stderr'), str) for r in transcript), 'Invalid command receipts')
    successful = [r['argv'] for r in transcript if r['exit_code'] == 0]
    require(any(a[0] == 'git' and 'init' in a and '--bare' in a for a in successful), 'No actual bare repository initialization')
    require(sum(a[0] == 'git' and 'clone' in a for a in successful) >= 3, 'Editor/contributor/recovery clones missing')
    for script, action in [('git_collaboration.py', 'package'), ('git_collaboration.py', 'verify'),
                           ('writing_run.py', 'start'), ('writing_run.py', 'register'),
                           ('writing_workspace.py', 'add-revision')]:
        require(any(any(x.endswith('/' + script) for x in a) and action in a for a in successful), 'Missing actual CLI execution: ' + script + ' ' + action)
    failures = [r for r in transcript if r['exit_code'] != 0]
    for reason in ['checksum/size mismatch', 'differs from the declared base commit']:
        require(any(reason in r['stderr'] for r in failures), 'Expected rejection not observed: ' + reason)
    for layer in ['unstaged', 'staged', 'committed']:
        require(any('guard' in r['argv'] and re.search(r': ' + layer + r' [A-Z?]\b', r['stderr']) for r in failures),
                'Expected exact Git change layer rejection not observed: ' + layer)
    concurrency = cases['concurrent-official-write']['observations']
    require(all(concurrency.get(k) is True for k in ['real_writing_commands_executed',
                'unstaged_staged_and_committed_changes_rejected', 'valid_package_cannot_conceal_official_changes',
                'same_event_sequence_has_different_hashes', 'editor_official_files_unchanged']), 'Incomplete actual concurrency evidence')
    require(cases['candidate-integration']['observations'].get('verified_on_review_branch_before_main_merge') is True,
            'Candidate was not verified before main merge')
    state = read_json(evidence / 'accepted-state.json'); inventory = read_json(evidence / 'official-inventory.json')
    accepted = cases['recovery-clone']['observations']['accepted_text']
    require(state['chapters'][0]['accepted_text'] == accepted, 'Recovered accepted state differs')
    require(isinstance(inventory, dict) and inventory and all(isinstance(p, str) and isinstance(h, str)
            and re.fullmatch(r'[0-9a-f]{64}', h) for p, h in inventory.items()), 'Invalid/empty recovered file inventory')
    for relative in inventory:
        scoped_path(evidence, relative)
    initial = cases['initial-clone']['observations']['accepted_text']
    versions = {initial, accepted, state['book_plan'], state['chapters'][0]['plan']}
    required_inventory = {'book.yaml', 'state.json', '版本记录/revisions.json', 'lifecycle/state.json'}
    required_inventory.update('版本记录/content/' + ident + '.md' for ident in versions)
    require(required_inventory <= set(inventory), 'Recovered inventory omits content registry, state, ancestry or old text')
    event_paths = sorted(p for p in inventory if p.startswith('lifecycle/events/'))
    require(len(event_paths) >= 4 and event_paths == ['lifecycle/events/%08d.json' % n for n in range(1, len(event_paths) + 1)],
            'Recovered inventory omits the complete sequential lifecycle')
    verified_runs = []
    for row in transcript:
        args = row['argv']
        if row['exit_code'] == 0 and 'verify' in args and any(a.endswith('/writing_run.py') for a in args):
            verified_runs.append(json.loads(row['stdout']))
    require(verified_runs, 'No actual lifecycle verification receipt')
    for verified in verified_runs:
        run = verified['run']; prefix = 'runs/' + run['id'] + '/'
        # Registering the accepted text legitimately changes the live registry;
        # its pinned pre-registration copy must remain usable and hash-verified.
        permitted_drift = [{'label': '版本记录/revisions.json', 'origin': 'project', 'snapshot_usable': True}]
        require(verified.get('drift') in [[], permitted_drift]
                and accepted in verified.get('state', {}).get('registered_versions', []),
                'Actual lifecycle verification did not confirm the accepted registration or has unrelated input drift')
        require(isinstance(run.get('pins'), list) and run['pins'], 'Actual lifecycle verification has no locked inputs')
        require(prefix + 'run.json' in inventory, 'Recovered inventory omits verified run manifest')
        for pin in run['pins']:
            require(inventory.get(prefix + pin['snapshot']) == pin['sha256'], 'Recovered inventory omits/changes a locked run input')
    require(inventory.get('版本记录/content/' + accepted + '.md') == cases['recovery-clone']['observations']['accepted_sha256']
            == cases['candidate-integration']['observations']['candidate_sha256'], 'Recovered candidate hash differs')
    return {'cases': len(cases), 'commands': len(transcript), 'expected_rejections': len(failures),
            'same_host_local_git_only': True, 'live_github_accounts_tested': False,
            'report_sha256': digest(evidence / 'result.json')}


def historical_v22(root=ROOT):
    root = Path(root); folder = root / 'evals/v2.2'; report = read_json(folder / 'review.json')
    require(report.get('source') == 'independent_agent_forward_test_with_parent_review', 'Missing historical v2.2 review')
    require(report.get('live_cloud_tested') is False and report.get('author_approval_claimed') is False, 'Historical report overclaims scope')
    context = report['evaluated_context']
    require(digest(scoped_path(folder, context['path'])) == context['sha256'], 'Historical context descriptor changed')
    require(read_json(scoped_path(folder, context['path'])).get('files'), 'Empty historical context')
    expected = {'novel-shared-baseline-conflict', 'wechat-confirmed-import'}
    require(len(report['cases']) == 2 and {r['id'] for r in report['cases']} == expected, 'Missing historical v2.2 cases')
    count = 0
    for case in report['cases']:
        require(case['status'] == 'passed' and case.get('observations') and not case.get('unresolved_blockers'), 'Historical case unresolved')
        require({'input', 'transcript', 'result'} <= {r.get('role') for r in case['artifacts']}, 'Missing historical execution artifacts')
        count += checked_rows(folder, case['artifacts'])
    return {'cases': 2, 'artifacts': count, 'scope': 'historical artifact integrity only',
            'current_skill_behavior_retested': False, 'report_sha256': digest(folder / 'review.json')}


def historical_evidence():
    from acceptance_v21 import textual_evidence
    config = read_json(ROOT / 'configs/acceptance-v2.3.json')['historical_evidence']
    require(digest(ROOT / 'evals/v2.1/results/review.json') == config['v21_review_sha256'], 'Historical v2.1 report changed')
    require(digest(ROOT / 'evals/v2.2/review.json') == config['v22_review_sha256'], 'Historical v2.2 report changed')
    return {'v21': textual_evidence(), 'v22': historical_v22(), 'scope': 'historical evidence, not a new writing-quality trial'}


def skill_metadata(root=ROOT):
    result = []
    for relative, expected_name in SKILLS.items():
        path = scoped_path(root, relative); text = path.read_text(encoding='utf-8')
        require(text.startswith('---\n') and '\n---\n' in text[4:], 'Skill lacks YAML frontmatter: ' + relative)
        metadata = text[4:].split('\n---\n', 1)[0]
        fields = {}
        for line in metadata.splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            require(':' in line and not line.startswith((' ', '\t')), 'Expected scalar Skill metadata: ' + relative)
            key, value = line.split(':', 1)
            require(key not in fields, 'Duplicate Skill metadata key: ' + relative)
            fields[key] = value.strip().strip('\"\'')
        require(fields.get('name') == expected_name and re.fullmatch(r'[a-z0-9-]{1,64}', expected_name), 'Wrong Skill name: ' + relative)
        description = fields.get('description', '')
        require(0 < len(description) <= 1024 and '<' not in description and '>' not in description, 'Invalid Skill description: ' + relative)
        result.append({'path': relative, 'name': expected_name, 'sha256': digest(path)})
    return result


def documentation():
    from preflight_check import link_errors
    config = read_json(ROOT / 'configs/acceptance-v2.3.json')
    require((ROOT / 'VERSION').read_text().strip() == config['version'], 'Version/config mismatch')
    errors = link_errors()
    require(not errors, 'Broken local documentation links: ' + '; '.join(errors[:10]))
    return {'version': config['version'], 'local_links': 'verified', 'skills': skill_metadata()}


def clean_install():
    from acceptance_v22 import clean_install as previous_install
    from build_release import build, distribution_directory
    result = previous_install()
    with tempfile.TemporaryDirectory() as temporary:
        temporary = Path(temporary); archive = temporary / 'public.zip'; build(archive)
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(temporary / 'install')
        installed = temporary / 'install' / distribution_directory((ROOT / 'VERSION').read_text().strip())
        process = subprocess.run([sys.executable, str(installed / 'scripts/git_collaboration.py'), '--help'],
                                 cwd=temporary, capture_output=True, text=True)
        require(process.returncode == 0 and all(x in process.stdout for x in ['package', 'guard', 'verify']), 'Installed Git collaboration CLI unavailable')
        require(digest(archive) == result['package_sha256'], 'Public package changed during clean install')
    return dict(result, installed_git_collaboration_cli=True)


def shared_methods():
    from capability_catalog import catalog
    from export_author_profile import export
    require(len({row['id'] for row in catalog()['capabilities']}) == 13, 'Method registry changed')
    with tempfile.TemporaryDirectory() as temporary:
        result = export(ROOT / 'shared/author-expression', Path(temporary) / 'author.zip')
    require(result['sha256'] == 'aea0138e25a141295214cd3b47ef17324d1ff30ab03d27d78af9685cec67ebcb', 'Author package changed without a new version')
    return {'methods': 13, 'author_profile': '1.0.0', 'sha256': result['sha256']}


def migration(workspace):
    from backup_workspace import inventory
    from writing_workspace import resolve_project, validate, derive_state
    workspace = Path(workspace).resolve(); receipt = read_json(receipt_directory(workspace) / 'migration.json')
    require(Path(receipt['destination']).resolve() == workspace, 'Migration receipt belongs to another target')
    source = Path(receipt['source']).resolve()
    require(source != workspace and receipt.get('source_retained') is True, 'Original workspace must be retained separately')
    # New navigation notes are allowed; every original file must still match.
    originals = receipt['source_original_inventory']; checked_rows(source, originals)
    selected = receipt['selected_files']; checked_rows(workspace, selected)
    source_map = {r['path']: r for r in originals}
    for row in selected:
        original = source_map.get(row['source_path'])
        require(original and original['sha256'] == row['sha256'] and original['bytes'] == row['bytes'], 'Selected copy lacks original provenance')
        if row.get('current_entry'):
            require(scoped_path(workspace, row['current_entry']).is_file(), 'Missing replacement navigation entry')
    backup = receipt['backup']; archive = Path(backup['archive'])
    require(backup.get('verified_restore') is True and digest(archive) == backup['sha256'], 'Unverified/changed migration backup')
    with tarfile.open(archive, 'r:gz') as bundle:
        manifest = json.load(bundle.extractfile('backup-manifest.json'))
    require(manifest['files'] == originals, 'Full backup differs from original inventory')
    require(inventory(Path(backup['destination'])) == originals, 'Actual restored backup differs from originals')
    project_id = receipt['source_state']['project_id']; project = resolve_project(workspace, project_id)
    original_project = resolve_project(source, project_id)
    require(not validate(project) and not validate(original_project), 'Migrated/original content registry invalid')
    require(digest(project / '版本记录/revisions.json') == digest(original_project / '版本记录/revisions.json')
            == receipt['source_registry_sha256'], 'Registered content changed during migration')
    require(derive_state(project) == receipt['source_state'] == derive_state(original_project), 'Accepted state or inheritance changed')
    ids = receipt['selected_source_ids']
    require(isinstance(ids, list) and ids and len(set(ids)) == len(ids), 'Missing/duplicate selected material IDs')
    corpus = read_json(workspace / 'corpus/manifest.json')
    require(isinstance(corpus, list) and len(corpus) == len(ids) and {str(r['id']) for r in corpus} == set(ids),
            'Selected material IDs differ from the actual corpus manifest')
    copies = {r['path']: r for r in selected}
    for material in corpus:
        body = scoped_path(workspace / 'corpus', material['markdown'])
        copied = copies.get(body.relative_to(workspace).as_posix())
        require(copied and digest(body) == copied['sha256'] and body.stat().st_size == copied['bytes'],
                'Selected corpus body lacks a verified byte-preserving source copy')
    return {'original_files_verified': len(originals), 'scoped_copies_verified': len(selected),
            'selected_sources': len(ids), 'full_backup_restore_verified': True,
            'originals_retained': True, 'accepted_state_unchanged': True, 'new_source_navigation_allowed': True}


def receipt_file(workspace, entry, allow_absolute=False):
    reference = Path(entry['path'])
    if reference.is_absolute():
        require(allow_absolute, 'Expected a workspace-relative receipt')
        path = reference
    else:
        path = scoped_path(workspace, reference)
    require(path.is_file() and not path.is_symlink() and digest(path) == entry['sha256'], 'Missing/changed external evidence file')
    return path


def mcp_payload(receipt):
    require(not receipt.get('error'), 'JSON-RPC error in external receipt')
    result = receipt.get('result', receipt.get('response', receipt))
    require(not result.get('isError'), 'MCP error in external receipt')
    payload = result.get('structuredContent')
    if payload is None:
        payload = json.loads(next(r['text'] for r in result['content'] if r.get('type') == 'text'))
    require(isinstance(payload, dict) and not payload.get('error'), 'Business error in external receipt')
    return payload


def tencent_evidence(workspace, expected_documents=31):
    workspace = Path(workspace); receipt = read_json(receipt_directory(workspace) / 'tencent-read.json')
    require(receipt.get('source') == 'live_host_mcp' and receipt.get('recorded_at'), 'Missing current live MCP read provenance')
    require(receipt.get('wechat_live') == 'excluded_by_authorized_scope', 'WeChat live scope changed')
    require(receipt.get('write_scope') == 'historical_evidence_only; no new cloud write during storage cutover', 'Historical writes must not be claimed as new')
    inventory = read_json(receipt_file(workspace, receipt['inventory']))
    nodes = inventory['nodes']; by_id = {r['node_id']: r for r in nodes}
    require(len(by_id) == len(nodes) and nodes, 'Missing/duplicate remote inventory nodes')
    folders = {r['node_id'] for r in nodes if r['node_type'] == 'wiki_folder'}
    documents = {r['node_id'] for r in nodes if r['node_type'] == 'wiki_file'}
    require(len(documents) == expected_documents and len(folders) + len(documents) == len(nodes), 'Unexpected remote inventory coverage')
    pages, discovered = {}, set()
    for row in inventory['records']:
        payload = mcp_payload(row['response']); children = payload['children']
        require(isinstance(children, list) and isinstance(payload.get('has_next'), bool), 'Malformed remote inventory page')
        pages.setdefault(row['parent_id'], []).append((row['num'], payload['has_next']))
        for child in children:
            require(child['node_id'] in by_id and child['node_type'] == by_id[child['node_id']]['node_type'], 'Inventory page/node mismatch')
            discovered.add(child['node_id'])
    require(set(pages) == {None, *folders} and discovered == set(by_id), 'Remote folder inventory was not completely traversed')
    for rows in pages.values():
        ordered = sorted(rows)
        require([n for n, _ in ordered] == list(range(len(ordered))) and all(more for _, more in ordered[:-1])
                and ordered[-1][1] is False, 'Remote inventory pagination incomplete')
    rows = receipt['records']
    require(len(rows) == expected_documents and {r['id'] for r in rows} == documents, 'Missing/duplicate current document reads')
    matches = 0
    for row in rows:
        text_path = receipt_file(workspace, row['content']); response = read_json(receipt_file(workspace, row['response']))
        require(response.get('node', {}).get('node_id') == row['id'], 'Current read belongs to another document')
        payload = mcp_payload(response)
        require(isinstance(payload.get('content'), str) and payload['content'] == text_path.read_text(encoding='utf-8'), 'Current document snapshot differs from live read receipt')
        if row['comparison'] == 'exact_match':
            old = receipt_file(workspace, row['historical'])
            require(digest(old) == digest(text_path), 'Historical/current comparison differs')
            matches += 1
        else:
            require(row['comparison'] == 'new_snapshot' and not row.get('historical'), 'Unresolved document comparison')
    expected_protocols = read_json(ROOT / 'configs/acceptance-v2.3.json')['unchanged_external_protocols']
    protocols = receipt['unchanged_protocol_files']
    require(len(protocols) == len(expected_protocols) and {r['path']: r['sha256'] for r in protocols} == expected_protocols,
            'Historical external protocol hashes changed')
    checked_rows(ROOT, protocols)
    history = receipt['historical_write']
    expected_history = {'ledger-receipt.json', 'ledger-read-after.json', 'ledger-edit.json',
                        'ledger-structure-before.json', 'ledger-request.md'}
    require(set(history) == expected_history, 'Incomplete historical write/readback evidence')
    paths = {name: receipt_file(workspace, entry, allow_absolute=True) for name, entry in history.items()}
    ledger = read_json(paths['ledger-receipt.json'])
    require(ledger.get('source') == 'live_mcp' and ledger.get('readback_matches') is True and ledger.get('remote_id'), 'Invalid historical live write ledger')
    readback = mcp_payload(read_json(paths['ledger-read-after.json']))['content']
    require(readback == ledger['readback_content'] == paths['ledger-request.md'].read_text(encoding='utf-8'), 'Historical write/readback content differs')
    require(hashlib.sha256(readback.encode()).hexdigest() == ledger['local_sha256'], 'Historical local content hash differs')
    edited = mcp_payload(read_json(paths['ledger-edit.json']))['data']
    before = mcp_payload(read_json(paths['ledger-structure-before.json']))['data']
    require(before.get('nodes') and edited.get('version') and before.get('version') != edited['version'], 'No historical pre-read/version-changing write')
    require(ledger['response']['data']['version'] == edited['version'], 'Historical ledger refers to another edit')
    return {'current_live_documents': len(rows), 'historical_exact_matches': matches,
            'new_snapshots': len(rows) - matches, 'folder_pages': len(inventory['records']),
            'unchanged_protocols': len(protocols), 'write_evidence': 'historical live receipts revalidated',
            'new_cloud_write_tested': False, 'wechat_live': 'excluded_by_authorized_scope'}


def private_git_evidence(workspace):
    workspace = Path(workspace); receipt = read_json(receipt_directory(workspace) / 'git-remote.json')
    repo = receipt['repo']; name = repo['nameWithOwner']; url = repo['url']; commit = receipt['commit']
    require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', name) and url == 'https://github.com/' + name,
            'Expected a canonical GitHub repository identity without credentials')
    require(repo.get('isPrivate') is True and repo.get('visibility') == 'PRIVATE', 'Receipt does not identify a private repository')
    require(re.fullmatch(r'[0-9a-f]{40,64}', commit) and receipt.get('clone_verified') is True, 'Missing successful clone/commit evidence')
    require(isinstance(receipt.get('collaborators_invited'), list), 'Missing collaborator disclosure')
    # Read only safe repository metadata; no credentials, collaborator invites or remote writes.
    process = subprocess.run(['gh', 'repo', 'view', name, '--json', 'nameWithOwner,url,isPrivate,visibility'], capture_output=True, text=True)
    require(process.returncode == 0, 'Cannot revalidate current private GitHub repository visibility')
    current = json.loads(process.stdout)
    require(current.get('nameWithOwner') == name and current.get('url') == url and current.get('isPrivate') is True
            and current.get('visibility') == 'PRIVATE', 'Live repository identity/visibility differs')
    remote = subprocess.run(['git', 'ls-remote', '--exit-code', url, 'HEAD'], capture_output=True, text=True)
    require(remote.returncode == 0 and remote.stdout.strip().split() == [commit, 'HEAD'], 'Remote HEAD differs from the verified clone commit')
    clone = Path(receipt['clone_path']).resolve()
    require(clone.is_dir() and clone != workspace.resolve(), 'Independent recovery clone missing')
    for checkout in [workspace.resolve(), clone]:
        top = subprocess.run(['git', '-C', str(checkout), 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        require(top.returncode == 0 and Path(top.stdout.strip()).resolve() == checkout, 'Workspace/clone is not its own Git root')
        head = subprocess.run(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], capture_output=True, text=True)
        require(head.returncode == 0 and head.stdout.strip() == commit, 'Workspace/clone HEAD differs')
        origin = subprocess.run(['git', '-C', str(checkout), 'remote', 'get-url', 'origin'], capture_output=True, text=True)
        require(origin.returncode == 0 and origin.stdout.strip() in {url, url + '.git', 'git@github.com:' + name + '.git'},
                'Workspace/clone origin differs from the verified repository')
        status = subprocess.run(['git', '-C', str(checkout), 'status', '--porcelain', '--untracked-files=all'], capture_output=True, text=True)
        require(status.returncode == 0 and not status.stdout.strip(), 'Workspace/clone has uncommitted or untracked changes')
    tree = subprocess.run(['git', '-C', str(clone), 'ls-tree', '-r', '-z', commit], capture_output=True)
    require(tree.returncode == 0, 'Cannot read recovery clone tree')
    objects = []
    for entry in tree.stdout.split(b'\0')[:-1]:
        metadata, raw_path = entry.split(b'\t', 1); mode, kind, oid = metadata.decode().split()
        require(kind == 'blob' and mode in {'100644', '100755'}, 'Committed tree contains links or unsupported object types')
        objects.append((raw_path.decode(), oid))
    members = {p for p, _ in objects}; rows = receipt['files']
    require(len(members) == len(rows) and members == {r['path'] for r in rows}, 'Recovery receipt does not cover the full committed tree')
    checked_rows(clone, rows)
    checked_rows(workspace, rows)
    blobs = subprocess.run(['git', '-C', str(clone), 'cat-file', '--batch'],
                           input=('\n'.join(oid for _, oid in objects) + '\n').encode(), capture_output=True)
    require(blobs.returncode == 0, 'Cannot read committed content objects')
    by_path = {r['path']: r for r in rows}; offset = 0
    for relative, oid in objects:
        end = blobs.stdout.find(b'\n', offset)
        header = blobs.stdout[offset:end].decode().split()
        require(end >= offset and len(header) == 3 and header[:2] == [oid, 'blob'], 'Malformed committed content response')
        size = int(header[2]); body = blobs.stdout[end + 1:end + 1 + size]
        require(len(body) == size and hashlib.sha256(body).hexdigest() == by_path[relative]['sha256']
                and size == by_path[relative]['bytes'], 'Recovery receipt differs from committed Git blob: ' + relative)
        offset = end + 1 + size
        require(blobs.stdout[offset:offset + 1] == b'\n', 'Malformed committed content delimiter')
        offset += 1
    require(offset == len(blobs.stdout), 'Unexpected trailing committed content')
    from writing_workspace import resolve_project, validate, derive_state
    migration_receipt = read_json(receipt_directory(workspace) / 'migration.json')
    project = resolve_project(clone, migration_receipt['source_state']['project_id'])
    require(not validate(project) and derive_state(project) == migration_receipt['source_state'], 'Cloned accepted state/ancestry differs')
    require(digest(project / '版本记录/revisions.json') == migration_receipt['source_registry_sha256'], 'Cloned registered versions differ')
    return {'visibility': 'PRIVATE', 'live_visibility_revalidated': True, 'remote_head_matches': True,
            'commit': commit, 'cloned_files_verified': len(rows), 'accepted_state_unchanged': True,
            'committed_blob_hashes_verified': True, 'workspace_and_clone_clean': True,
            'collaborators_invited': len(receipt['collaborators_invited']), 'two_github_accounts_tested': False}


def run(workspace, public_only=False):
    workspace = Path(workspace).expanduser().resolve()
    output = output_directory(workspace, public_only)
    output.mkdir(parents=True, exist_ok=True)
    config = acceptance_config(); results = []
    def check(ident, function):
        try:
            row = {'id': ident, 'status': 'passed', 'detail': function()}
        except (Exception, SystemExit) as exc:
            row = {'id': ident, 'status': 'failed', 'detail': str(exc)}
        results.append(row); print(ident + ': ' + row['status'], flush=True)
    def command(args, filename):
        process = subprocess.run([sys.executable, *args], cwd=ROOT, capture_output=True, text=True)
        atomic_text(output / filename, process.stdout + process.stderr)
        require(process.returncode == 0, 'See ' + str(output / filename))
        return {'log': filename, 'exit_code': 0}
    check('C01', lambda: command(['-m', 'unittest', 'discover', '-s', 'tests', '-v'], 'unit-tests.txt'))
    check('C02', lambda: command(['scripts/preflight_check.py'], 'preflight.txt'))
    check('C03', clean_install)
    check('C04', shared_methods)
    check('C05', git_collaboration_evidence)
    check('C06', historical_evidence)
    check('C07', documentation)
    if not public_only:
        check('C08', lambda: migration(workspace))
        check('C09', lambda: tencent_evidence(workspace))
        check('C10', lambda: private_git_evidence(workspace))
    expected = {r['id'] for r in config['checks'] if not public_only or not r.get('private_required')}
    require(expected == {r['id'] for r in results}, 'Acceptance criteria and runner differ')
    passed = sum(r['status'] == 'passed' for r in results)
    report = {'schema_version': 1, 'version': config['version'], 'checked_at': datetime.now(timezone.utc).isoformat(),
              'mode': 'public_self_check' if public_only else 'full_release_acceptance',
              'passed': passed, 'total': len(results), 'all_in_scope_passed': passed == len(results),
              'full_release_claim': not public_only and passed == len(results), 'results': results,
              'excluded_by_user': config['excluded_by_user'], 'limitations': config['limitations']}
    write_json(output / 'report.json', report)
    return report
