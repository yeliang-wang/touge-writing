#!/usr/bin/env python3
"""File-based writing task records. Content acceptance remains in revisions.json."""
import argparse
import json
from pathlib import Path
from workspace_lib import read_json, scoped_path, digest, write_json, immutable_copy, locked
from material_index import identifier, fingerprint, immutable_json
from capability_catalog import resolve, ROOT

STAGES = {'plan', 'draft', 'review', 'revise', 'paused', 'completed'}


def paths(project, run_id):
    return scoped_path(project, 'runs/' + identifier(run_id))


def events(project):
    folder = scoped_path(project, 'lifecycle/events')
    rows, operations = [], set()
    for path in sorted(folder.glob('*.json')):
        row = read_json(path)
        if row.get('schema_version') != 1 or row['sequence'] != len(rows) + 1:
            raise ValueError('Unsupported/broken lifecycle event sequence')
        key = (row['run_id'], row['operation_id'])
        if key in operations or row['previous'] != (fingerprint(rows[-1]) if rows else None):
            raise ValueError('Changed/duplicate lifecycle event')
        identifier(row['run_id']); identifier(row['operation_id']); operations.add(key)
        if row.get('payload_sha256') != fingerprint(row['payload']):
            raise ValueError('Lifecycle payload changed')
        rows.append(row)
    return rows


def operation(project, run_id, op_id, payload):
    identifier(op_id)
    for row in events(project):
        if (row['run_id'], row['operation_id']) == (run_id, op_id):
            if row['payload_sha256'] != fingerprint(payload):
                raise ValueError('Operation ID reused with different input')
            return row
    return None


def append_event(project, run_id, op_id, payload):
    old = operation(project, run_id, op_id, payload)
    if old:
        return old
    prior = events(project)
    row = {'schema_version': 1, 'sequence': len(prior) + 1, 'run_id': run_id,
           'operation_id': identifier(op_id), 'payload': payload,
           'payload_sha256': fingerprint(payload), 'previous': fingerprint(prior[-1]) if prior else None}
    immutable_json(scoped_path(project, 'lifecycle/events/%08d.json' % row['sequence']), row)
    write_json(project / 'lifecycle/state.json', derive(project))
    return row


def derive(project):
    runs, active = {}, None
    for e in events(project):
        rid, data = e['run_id'], e['payload']; action = data['action']
        if action == 'start':
            runs[rid] = {'run_id': rid, 'stage': data['stage'], 'mode': data['mode'],
                         'target': data.get('target'), 'artifacts': [], 'registered_versions': [],
                         'resolved_issues': []}
            active = rid
        elif rid not in runs:
            raise ValueError('Run event lacks start event')
        elif action == 'stage':
            runs[rid]['stage'] = data['stage']
            if data['stage'] == 'completed' and active == rid:
                active = None
        elif action == 'activate':
            active = rid
        elif action == 'artifact':
            runs[rid]['artifacts'].append(data['artifact'])
        elif action == 'register':
            if data['revision_id'] not in runs[rid]['registered_versions']:
                runs[rid]['registered_versions'].append(data['revision_id'])
        elif action == 'resolve_issue':
            runs[rid]['resolved_issues'].append(data['issue_id'])
        else:
            raise ValueError('Unknown lifecycle action')
    return {'schema_version': 1, 'active_run': active, 'runs': runs}


def load(project, run_id):
    row = read_json(paths(project, run_id) / 'run.json')
    if row.get('schema_version') != 1 or row['id'] != run_id:
        raise ValueError('Unsupported/mismatched run schema')
    if fingerprint(row['request']) != row['request_sha256']:
        raise ValueError('Run request changed')
    for pin in row['pins']:
        snapshot = scoped_path(paths(project, run_id), pin['snapshot'])
        if snapshot.is_symlink() or digest(snapshot) != pin['sha256']:
            raise ValueError('Run snapshot missing/changed: ' + pin['label'])
    if row.get('rule_context'):
        from writing_rules import check_context
        check_context(row['rule_context'])
        if row['rule_context'].get('enabled'):
            pinned = {p['source']: p['sha256'] for p in row['pins'] if p['origin'] == 'project'}
            for dependency in [row['rule_context']['manifest'], *row['rule_context']['files']]:
                if pinned.get(dependency['path']) != dependency['sha256']:
                    raise ValueError('Rule context does not match its frozen input: ' + dependency['path'])
    return row


def verify(project, run_id, root=ROOT):
    row = load(project, run_id); state = derive(project)
    if run_id not in state['runs']:
        raise ValueError('Run prepared but not started; repeat start with original request')
    start_event = next(e for e in events(project) if e['run_id'] == run_id and e['payload']['action'] == 'start')
    if start_event['payload']['manifest_sha256'] != digest(paths(project, run_id) / 'run.json'):
        raise ValueError('Run manifest changed since start')
    drift = []
    for pin in row['pins']:
        base = root if pin['origin'] == 'public' else project
        path = scoped_path(base, pin['source'])
        if not path.is_file() or digest(path) != pin['sha256']:
            drift.append({'label': pin['label'], 'origin': pin['origin'], 'snapshot_usable': True})
    for artifact in state['runs'][run_id]['artifacts']:
        if digest(scoped_path(paths(project, run_id), artifact['path'])) != artifact['sha256']:
            raise ValueError('Run artifact changed')
    for e in events(project):
        if e['run_id'] == run_id and e['payload']['action'] == 'resolve_issue':
            if digest(scoped_path(project, e['payload']['decision_ref'])) != e['payload']['sha256']:
                raise ValueError('Issue decision changed')
    return {'run': row, 'state': state['runs'][run_id], 'drift': drift,
            'reproduction': 'Locked inputs support audit, not deterministic model regeneration'}


def validate_request(project, request, root):
    from writing_workspace import validate
    if validate(project):
        raise ValueError('Invalid content versions')
    if request.get('schema_version') != 1:
        raise ValueError('Unsupported run request schema')
    identifier(request['id'])
    meta = read_json(project / 'book.yaml')
    if not request.get('task') or not request.get('authorization_refs'):
        raise ValueError('Task and actual request/authorization references required')
    if request['mode'] not in {'trial', 'plan', 'draft', 'revise', 'review', 'title', 'deliver'}:
        raise ValueError('Unknown run mode')
    if request['stage'] not in STAGES - {'completed'}:
        raise ValueError('Invalid starting stage')
    if meta['type'] == 'novel' and request.get('target') not in {c['id'] for c in meta['chapters']} | {'book'}:
        raise ValueError('Unknown stable chapter ID')
    if meta['type'] == 'wechat' and request.get('target') not in {None, 'article'}:
        raise ValueError('Article target required')
    policy = request['fiction_policy']
    if policy.get('mode') not in {'source-based', 'reconstruction', 'fiction'}:
        raise ValueError('An explicit fact/fiction contract is required')
    if policy['mode'] != 'source-based' and (not policy.get('scope') or not policy.get('authorization_ref')):
        raise ValueError('Fiction requires scoped authorization, not a global assumption')
    for issue in request.get('open_issues', []):
        identifier(issue['id'])
        if not issue.get('impact') or not isinstance(issue.get('blocks_completion'), bool):
            raise ValueError('Issues need explicit impact and blocking scope')
    rows = resolve(request.get('capabilities', []), meta['type'], root)
    public = [r['path'] for r in rows]
    skill = '.agents/skills/touge-%s-writing/' % ('novel' if meta['type'] == 'novel' else 'wechat')
    public += [skill + 'SKILL.md', skill + 'references/lifecycle.json']
    profile = read_json(root / 'shared/author-expression/manifest.json')
    # Include reviewed author-pack files via its own allowlist, independently versioned.
    for item in profile['files']:
        relative = item if isinstance(item, str) else item['path']
        if isinstance(item, dict) and digest(scoped_path(root / 'shared/author-expression', relative)) != item['sha256']:
            raise ValueError('Author profile changed without versioned manifest')
        public.append('shared/author-expression/' + relative)
    public.append('shared/author-expression/manifest.json')
    return meta, public, profile


@locked
def start(project, request, root=ROOT):
    root = Path(root); meta, public, profile = validate_request(project, request, root)
    run_id = request['id']; folder = paths(project, run_id); manifest = folder / 'run.json'
    if manifest.exists():
        row = load(project, run_id)
        if row['request_sha256'] != fingerprint(request):
            raise ValueError('Run ID reused with different request')
    else:
        pins = []
        from writing_workspace import derive_state
        state = derive_state(project)
        records = read_json(project / '版本记录/revisions.json')['revisions']
        by_id = {r['id']: r for r in records}
        selected = {state.get('book_plan'), state.get('latest_text')}
        chapters = state['chapters']
        target = request.get('target')
        for i, chapter in enumerate(chapters):
            if chapter['id'] == target:
                for c in chapters[max(0, i-1):i+2]:
                    selected.update([c['plan'], c['accepted_text'], c['latest_text']])
        for rid in list(selected):
            if rid in by_id:
                selected.add(by_id[rid].get('parent_plan_id'))
        automatic = ['book.yaml', '版本记录/revisions.json'] + [r['path'] for r in records if r['id'] in selected]
        from writing_rules import resolve_rules
        rule_context = resolve_rules(project, target, request['mode'])
        if rule_context['enabled']:
            automatic += [rule_context['manifest']['path']] + [f['path'] for f in rule_context['files']]
        inputs = list(request.get('inputs', []))
        for relative in automatic:
            if relative not in {i['path'] for i in inputs}:
                inputs.append({'path': relative, 'sha256': digest(scoped_path(project, relative))})
        for origin, base, entries in [('public', root, [{'path': p} for p in dict.fromkeys(public)]),
                                      ('project', project, inputs)]:
            for item in entries:
                source = scoped_path(base, item['path']); sha = digest(source)
                if origin == 'project' and item.get('sha256') != sha:
                    raise ValueError('Inputs must pin the actual content hash')
                destination = 'inputs/%03d%s' % (len(pins), source.suffix or '.txt')
                immutable_copy(source, scoped_path(folder, destination), sha)
                pins.append({'label': item.get('label', item['path']), 'origin': origin,
                             'source': item['path'], 'snapshot': destination, 'sha256': sha,
                             'summary': item.get('summary'), 'summary_basis_sha256': sha if item.get('summary') else None})
        row = {'schema_version': 1, 'id': run_id, 'request': request,
               'request_sha256': fingerprint(request), 'pins': pins,
               'author_profile_version': profile['version'],
               'model': request.get('model', {'id': 'unknown', 'configuration': 'unknown'})}
        # Only new, enabled runs adopt this protocol. Historical runs keep their own semantics.
        if rule_context['enabled']:
            row['rule_context'] = rule_context
        immutable_json(manifest, row)
    append_event(project, run_id, 'start', {'action': 'start', 'request_sha256': row['request_sha256'],
                 'mode': request['mode'], 'target': request.get('target'), 'stage': request['stage'],
                 'manifest_sha256': digest(manifest)})
    return verify(project, run_id, root)


@locked
def add_artifact(project, run_id, op_id, source, artifact_id, role='text'):
    folder = paths(project, run_id); load(project, run_id); identifier(artifact_id)
    if role not in {'text', 'plan', 'review', 'sources', 'diff', 'delivery'}:
        raise ValueError('Unknown artifact role')
    source = Path(source)
    artifact = {'id': artifact_id, 'path': 'artifacts/' + artifact_id + (source.suffix or '.txt'),
                'sha256': digest(source), 'role': role}
    payload = {'action': 'artifact', 'artifact': artifact}
    old = operation(project, run_id, op_id, payload)
    if old:
        verify(project, run_id); return old
    state = derive(project)['runs'][run_id]
    if state['stage'] == 'completed' or any(a['id'] == artifact_id for a in state['artifacts']):
        raise ValueError('Completed run or duplicate artifact identity; create another version')
    immutable_copy(source, scoped_path(folder, artifact['path']), artifact['sha256'])
    return append_event(project, run_id, op_id, payload)


@locked
def change_stage(project, run_id, op_id, stage, reason, review_id=None):
    if stage not in STAGES or not reason.strip():
        raise ValueError('Known stage and reason required')
    payload = {'action': 'stage', 'stage': stage, 'reason': reason, 'review_id': review_id}
    old = operation(project, run_id, op_id, payload)
    if old:
        verify(project, run_id); return old
    checked = verify(project, run_id); state = checked['state']
    definition = next(p for p in checked['run']['pins'] if p['source'].endswith('references/lifecycle.json'))
    lifecycle = read_json(scoped_path(paths(project, run_id), definition['snapshot']))
    if lifecycle.get('schema_version') != 1 or stage not in lifecycle['transitions'].get(state['stage'], []):
        raise ValueError('Illegal lifecycle transition')
    if stage == 'completed':
        request = checked['run']['request']
        unresolved = [i for i in request.get('open_issues', []) if i['blocks_completion'] and i['id'] not in state['resolved_issues']]
        if unresolved:
            raise ValueError('Issues still block this task scope')
        reviews = [a for a in state['artifacts'] if a['id'] == review_id and a['role'] == 'review']
        if len(reviews) != 1:
            raise ValueError('Completion needs an actual review artifact')
        review = read_json(scoped_path(paths(project, run_id), reviews[0]['path']))
        texts = {a['id']: a for a in state['artifacts'] if a['role'] != 'review'}
        if checked['run'].get('rule_context', {}).get('enabled'):
            from writing_rules import validate_review
            validate_review(checked['run']['rule_context'], review, list(texts.values()), require_completed=True)
        else:
            if (review.get('result') != 'pass' or not review.get('findings') or not review.get('scope')
                    or review.get('unresolved_blockers') != [] or not review.get('artifacts')):
                raise ValueError('Review is incomplete or unresolved')
            for ref in review['artifacts']:
                if ref.get('id') not in texts or texts[ref['id']]['sha256'] != ref.get('sha256'):
                    raise ValueError('Review does not cover immutable output versions')
        # This checks the record's structure. The host must actually read/review the text.
    return append_event(project, run_id, op_id, payload)


@locked
def resolve_issue(project, run_id, op_id, issue_id, decision_ref):
    row = load(project, run_id)
    if issue_id not in {i['id'] for i in row['request'].get('open_issues', [])}:
        raise ValueError('Unknown issue')
    decision = scoped_path(project, decision_ref)
    if not decision.read_text().strip():
        raise ValueError('Actual scoped resolution record required')
    return append_event(project, run_id, op_id, {'action': 'resolve_issue', 'issue_id': issue_id,
                        'decision_ref': decision_ref, 'sha256': digest(decision)})


@locked
def register(project, run_id, op_id, artifact_id, revision):
    """Recover both copy-before-registry and registry-before-event interruptions."""
    from writing_workspace import add_revision, derive_state, validate, validate_new_revision_scope
    checked = verify(project, run_id); state = checked['state']
    artifacts = [a for a in state['artifacts'] if a['id'] == artifact_id]
    if len(artifacts) != 1:
        raise ValueError('Unknown run artifact')
    if 'source' in revision:
        raise ValueError('Source is fixed by the selected run artifact')
    source = scoped_path(paths(project, run_id), artifacts[0]['path'])
    revision = dict(revision)
    if any(k.startswith('_') for k in revision) or 'rules_review' in revision or 'rules_mode' in revision:
        raise ValueError('Run rule evidence is selected by review_id, not caller-supplied rule context')
    review_id = revision.pop('review_id', None)
    target = checked['run']['request'].get('target')
    if target not in {None, 'article', 'book'} and revision.get('chapter_id') != target:
        raise ValueError('Run registration cannot change its chapter scope')
    if artifacts[0]['role'] != ('plan' if revision.get('kind') in {'chapter_plan', 'book_plan'} else revision.get('kind')):
        raise ValueError('Artifact role does not match content kind')
    if revision.get('decision_file'):
        revision['decision_file'] = str(scoped_path(project, revision['decision_file']))
    payload = {'action': 'register', 'revision_id': revision['revision_id'], 'artifact_id': artifact_id,
               'sha256': digest(source), 'revision': revision,
               'decision_sha256': digest(revision['decision_file']) if revision.get('decision_file') else None}
    rule_context = checked['run'].get('rule_context', {'enabled': False})
    if rule_context.get('enabled'):
        validate_new_revision_scope(read_json(project / 'book.yaml'), revision.get('kind'), revision.get('chapter_id'), target)
    rule_review = None
    rule_artifacts = [a for a in state['artifacts'] if a['role'] != 'review']
    if rule_context.get('enabled') and revision.get('kind') != 'review':
        mode = checked['run']['request']['mode']
        if ((revision.get('kind') == 'text' and mode not in {'draft', 'revise', 'trial', 'deliver'})
                or (revision.get('kind') in {'book_plan', 'chapter_plan'} and mode not in {'plan', 'revise'})):
            raise ValueError('Run mode cannot register this content kind; start the authorized writing/plan task')
        reviews = [a for a in state['artifacts'] if a['id'] == review_id and a['role'] == 'review']
        if len(reviews) != 1:
            raise ValueError('Rule-enabled registration requires an exact review_id artifact')
        rule_review = scoped_path(paths(project, run_id), reviews[0]['path'])
        from writing_rules import validate_review
        review = read_json(rule_review)
        validate_review(rule_context, review, rule_artifacts)
        if not any(a['id'] == artifact_id and a['sha256'] == digest(source) for a in review['artifacts']):
            raise ValueError('Rule review does not cover the registered artifact')
        payload['review_id'] = review_id
    old = operation(project, run_id, op_id, payload)
    if old:
        if validate(project): raise ValueError('Registered content changed')
        return old
    records = read_json(project / '版本记录/revisions.json')['revisions']
    existing = next((r for r in records if r['id'] == revision['revision_id']), None)
    if existing:
        expected = {'id': revision['revision_id'], 'kind': revision['kind'], 'version': revision['version'],
                    'status': revision['status'], 'sha256': digest(source),
                    **{k: revision[k] for k in ['chapter_id', 'parent_plan_id', 'based_on'] if revision.get(k)}}
        if any(existing.get(k) != v for k, v in expected.items()) or any(existing.get(k) != revision.get(k) for k in ['chapter_id', 'parent_plan_id', 'based_on']):
            raise ValueError('Existing revision conflicts with retry')
        if existing.get('decision_sha256') != payload['decision_sha256'] or validate(project):
            raise ValueError('Existing acceptance decision differs or registry invalid')
        write_json(project / 'state.json', derive_state(project))
    else:
        # Already holding the same project lock; call the wrapped operation once.
        add_revision.__wrapped__(project, source, **revision, rules_review=rule_review,
                                 _rules_context=rule_context, _rules_artifacts=rule_artifacts)
    return append_event(project, run_id, op_id, payload)


@locked
def activate(project, run_id, op_id):
    checked = verify(project, run_id)
    if checked['state']['stage'] == 'completed':
        raise ValueError('Completed runs stay historical; create a new revision run')
    return append_event(project, run_id, op_id, {'action': 'activate'})


def active_context(project):
    state = derive(project); active = state['active_run']
    return verify(project, active) if active else None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, default=Path('workspace')); p.add_argument('--project', required=True)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('start'); s.add_argument('--request', type=Path, required=True)
    sub.add_parser('resume'); sub.add_parser('rebuild')
    for cmd in ['verify', 'artifact', 'stage', 'register', 'activate', 'resolve-issue']:
        s = sub.add_parser(cmd); s.add_argument('--run', required=True)
        if cmd != 'verify': s.add_argument('--operation-id', required=True)
        if cmd == 'artifact':
            s.add_argument('--source', type=Path, required=True); s.add_argument('--id', required=True); s.add_argument('--role', default='text')
        if cmd == 'stage':
            s.add_argument('--stage', required=True); s.add_argument('--reason', required=True); s.add_argument('--review-id')
        if cmd == 'register':
            s.add_argument('--artifact-id', required=True); s.add_argument('--revision', type=Path, required=True)
        if cmd == 'resolve-issue':
            s.add_argument('--issue-id', required=True); s.add_argument('--decision-ref', required=True)
    a = p.parse_args()
    from writing_workspace import resolve_project
    project = resolve_project(a.workspace, a.project)
    if a.command == 'start': result = start(project, read_json(a.request))
    elif a.command == 'resume': result = active_context(project)
    elif a.command == 'rebuild':
        from workspace_lib import write_lock
        with write_lock(project):
            result = derive(project); write_json(project / 'lifecycle/state.json', result)
    elif a.command == 'verify': result = verify(project, a.run)
    elif a.command == 'artifact': result = add_artifact(project, a.run, a.operation_id, a.source, a.id, a.role)
    elif a.command == 'stage': result = change_stage(project, a.run, a.operation_id, a.stage, a.reason, a.review_id)
    elif a.command == 'register': result = register(project, a.run, a.operation_id, a.artifact_id, read_json(a.revision))
    elif a.command == 'activate': result = activate(project, a.run, a.operation_id)
    else: result = resolve_issue(project, a.run, a.operation_id, a.issue_id, a.decision_ref)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        raise SystemExit('Error: ' + str(exc))
