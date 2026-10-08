#!/usr/bin/env python3
"""Create, resume, retrieve and version file-based writing projects."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from workspace_lib import scoped_path, read_json, write_json, digest, immutable_copy, atomic_text, locked
from private_retriever import tokenize, cosine, best_snippets


def load_catalog(workspace):
    catalog = read_json(Path(workspace) / 'catalog.json')
    if not isinstance(catalog, dict) or catalog.get('schema_version') != 1:
        raise ValueError('Unsupported workspace catalog schema')
    projects = catalog.get('projects')
    if not isinstance(projects, list):
        raise ValueError('Workspace catalog projects must be an array')
    ids, paths = set(), set()
    for row in projects:
        if not isinstance(row, dict) or any(not isinstance(row.get(k), str) or not row[k].strip()
                                           for k in ['id', 'title', 'path']):
            raise ValueError('Invalid project in workspace catalog')
        if row.get('type') not in {'novel', 'wechat'} or not isinstance(row.get('aliases', []), list) or any(not isinstance(x, str) for x in row.get('aliases', [])):
            raise ValueError('Invalid project type or aliases')
        path = scoped_path(workspace, row['path']).resolve()
        if row['id'] in ids or path in paths:
            raise ValueError('Duplicate project ID/path in workspace catalog')
        ids.add(row['id']); paths.add(path)
    return catalog


def resolve_project(workspace, name):
    workspace = Path(workspace).expanduser().resolve()
    catalog = load_catalog(workspace)
    matches = [x for x in catalog['projects'] if name in [x['id'], x['title'], *x.get('aliases', [])]]
    if len(matches) != 1:
        raise ValueError('Select exactly one known project')
    return scoped_path(workspace, matches[0]['path'])


def derive_state(project):
    meta = read_json(project / 'book.yaml')  # JSON is also valid YAML; no runtime dependency.
    manifest = read_json(project / '版本记录/revisions.json')
    if meta.get('schema_version') != 1 or manifest.get('schema_version') != 1:
        raise ValueError('Unsupported content schema; upgrade the tool before writing')
    records = manifest['revisions']
    plans = [r for r in records if r['kind'] == 'book_plan' and r['status'] == 'accepted']
    result = {'schema_version': 1, 'project_id': meta['id'], 'title': meta['title'],
              'book_plan': plans[-1]['id'] if plans else None, 'chapters': [], 'next_action': None}
    for chapter in meta.get('chapters', []):
        rows = [r for r in records if r.get('chapter_id') == chapter['id']]
        chapter_plans = [r for r in rows if r['kind'] == 'chapter_plan' and r['status'] == 'accepted']
        accepted = [r for r in rows if r['kind'] == 'text' and r['status'] == 'accepted']
        texts = [r for r in rows if r['kind'] == 'text' and r['status'] in ('accepted', 'baseline', 'draft')]
        item = dict(chapter, plan=chapter_plans[-1]['id'] if chapter_plans else None,
                    accepted_text=accepted[-1]['id'] if accepted else None,
                    latest_text=texts[-1]['id'] if texts else None)
        result['chapters'].append(item)
        if not accepted and result['next_action'] is None:
            result['next_action'] = {'chapter_id': chapter['id'],
                                     'action': 'draft' if chapter_plans else 'review_chapter_plan'}
    if meta['type'] == 'wechat':
        texts = [r for r in records if r['kind'] == 'text' and r['status'] in ('draft', 'baseline', 'accepted')]
        result['latest_text'] = texts[-1]['id'] if texts else None
    return result


def validate(project):
    problems = []
    manifest = read_json(project / '版本记录/revisions.json')
    if manifest.get('schema_version') != 1 or read_json(project / 'book.yaml').get('schema_version') != 1:
        return ['Unsupported content schema; refusing mutation']
    records = manifest['revisions']
    by_id = {r['id']: r for r in records}
    if len(by_id) != len(records):
        problems.append('duplicate revision IDs')
    meta = read_json(project / 'book.yaml')
    chapters = {c['id'] for c in meta.get('chapters', [])}
    seen = set()
    for r in records:
        try:
            if r['kind'] not in {'book_plan', 'chapter_plan', 'text', 'review'} or r['status'] not in {'draft', 'accepted', 'baseline', 'historical'}:
                problems.append('invalid revision kind/status: ' + r['id'])
            p = scoped_path(project, r['path'])
            if not p.is_file() or digest(p) != r['sha256']:
                problems.append('content mismatch: ' + r['id'])
            if r.get('chapter_id') and r['chapter_id'] not in chapters:
                problems.append('unknown chapter: ' + r['id'])
            parent_id = r.get('parent_plan_id')
            parent = by_id.get(parent_id)
            if r['kind'] == 'chapter_plan' and (r['status'] == 'accepted' or parent_id):
                if not parent or parent['kind'] != 'book_plan' or parent['status'] != 'accepted':
                    problems.append('missing accepted book plan: ' + r['id'])
            if r['kind'] == 'text' and r['status'] == 'accepted' and meta['type'] == 'novel':
                if not parent or parent['kind'] != 'chapter_plan' or parent.get('chapter_id') != r.get('chapter_id') or parent['status'] != 'accepted':
                    problems.append('invalid chapter inheritance: ' + r['id'])
            for relation in ['based_on', 'parent_plan_id']:
                if r.get(relation) and r[relation] not in seen:
                    problems.append('missing or non-prior ' + relation + ': ' + r['id'])
            if r.get('based_on') in by_id:
                previous = by_id[r['based_on']]
                if previous['kind'] != r['kind'] or previous.get('chapter_id') != r.get('chapter_id'):
                    problems.append('predecessor belongs to different kind/chapter: ' + r['id'])
            if r['status'] == 'accepted':
                decision = scoped_path(project, r.get('decision_path', ''))
                if not r.get('decision_path') or not decision.is_file() or not decision.read_text().strip():
                    problems.append('missing acceptance evidence: ' + r['id'])
                elif r.get('decision_sha256') and digest(decision) != r['decision_sha256']:
                    problems.append('changed acceptance evidence: ' + r['id'])
            if r.get('rule_review'):
                from writing_rules import validate_review
                receipt_ref = r['rule_review']
                receipt_path = scoped_path(project, receipt_ref['path'])
                if digest(receipt_path) != receipt_ref['sha256']:
                    problems.append('changed rule review: ' + r['id'])
                else:
                    receipt = read_json(receipt_path)
                    if receipt['context']['project_id'] != meta['id'] or receipt['context']['rule_set_sha256'] != receipt_ref['rule_set_sha256']:
                        problems.append('rule review belongs to different work/rules: ' + r['id'])
                    validate_review(receipt['context'], receipt['review'], receipt['review']['artifacts'])
                    if r['sha256'] not in {a['sha256'] for a in receipt['review']['artifacts']}:
                        problems.append('rule review does not cover revision: ' + r['id'])
        except (ValueError, OSError) as exc:
            problems.append(r['id'] + ': ' + str(exc))
        seen.add(r['id'])
    return problems


def context(project, chapter_id=None, mode=None):
    problems = validate(project)
    if problems:
        raise ValueError('; '.join(problems))
    state = derive_state(project)
    by_id = {r['id']: r for r in read_json(project / '版本记录/revisions.json')['revisions']}
    selected = []
    def add(rid, role):
        if rid and rid not in [x['id'] for x in selected]:
            selected.append(dict(by_id[rid], role=role))
    add(state.get('book_plan'), 'current_book_plan')
    from writing_run import active_context
    active = active_context(project)
    current_target = active['state']['target'] if active else None
    target = chapter_id or (current_target if current_target not in {'book', 'article'} else None)
    if not target and not active:
        target = (state.get('next_action') or {}).get('chapter_id')
    chapters = state['chapters']
    if target:
        indexes = [i for i, c in enumerate(chapters) if c['id'] == target]
        if not indexes:
            raise ValueError('Unknown chapter. Valid chapter IDs: ' + ', '.join(c['id'] for c in chapters))
        i = indexes[0]
        for j in range(max(0, i - 1), min(len(chapters), i + 2)):
            c = chapters[j]
            if j == i:
                add(c['plan'], 'chapter_plan')
                if c['plan']:
                    add(by_id[c['plan']].get('parent_plan_id'), 'historical_inheritance')
                if c['accepted_text'] != c['latest_text']:
                    add(c['accepted_text'], 'accepted_text')
            add(c['latest_text'] if j == i else c['accepted_text'] or c['latest_text'], 'target_text' if j == i else 'neighbor_text')
    if state.get('latest_text'):
        add(state['latest_text'], 'article_text')
    from writing_rules import resolve_rules, reading_paths
    same_task = active and (target or current_target) == current_target and (mode is None or mode == active['run']['request']['mode'])
    if same_task:
        rules = active['run'].get('rule_context', {'enabled': False, 'project_id': state['project_id'],
                'notice': 'Legacy run retains its original rules; start a new run to use an enabled manifest.'})
        from writing_run import paths
        rule_reads = reading_paths(project, rules, active['run']['pins'], paths(project, active['run']['id']))
    else:
        rules = resolve_rules(project, target, mode)
        rule_reads = reading_paths(project, rules)
    meta = read_json(project / 'book.yaml')
    rules_file = scoped_path(project, meta.get('rules_file', '全书方案/有效规则.md'))
    return {'state': state, 'selected_chapter': target, 'active_task': active,
            'task_precedence': 'Explicit chapter selection, then active task, then legacy next_action. Content acceptance is unchanged.',
            'material_maps': [str(p) for p in sorted((project / 'materials/maps').glob('*.json'))],
            'read_full_text': [{'id': r['id'], 'role': r['role'], 'path': str(scoped_path(project, r['path'])),
                                'status': r['status'], 'version': r['version'], 'sha256': r['sha256'],
                                'excerpt': scoped_path(project, r['path']).read_text(encoding='utf-8')[:600],
                                'excerpt_is_full_read': False} for r in selected],
            'rules_path': str(rules_file) if rules_file.exists() else None,
            'rule_context': rules, 'rules_read_full_text': rule_reads,
            'open_issues_path': str(project / '决策记录/open-issues.json') if (project / '决策记录/open-issues.json').exists() else None}


def retrieve(project, query, include_history=False, top_k=5):
    records = read_json(project / '版本记录/revisions.json')['revisions']
    if not include_history:
        state = derive_state(project)
        ids = {state.get('book_plan'), state.get('latest_text')}
        for c in state['chapters']:
            ids.update([c['plan'], c['accepted_text'], c['latest_text']])
        records = [r for r in records if r['id'] in ids]
    results = []
    q = Counter(tokenize(query))
    for r in records:
        p = scoped_path(project, r['path'])
        if digest(p) != r['sha256']:
            raise ValueError('Changed revision: ' + r['id'])
        text = p.read_text(encoding='utf-8')
        score = cosine(q, Counter(tokenize(text)))
        if score:
            results.append({'id': r['id'], 'path': r['path'], 'status': r['status'],
                            'score': round(score, 5), 'snippets': best_snippets(text, set(q))})
    return sorted(results, key=lambda x: -x['score'])[:top_k]


def validate_new_revision_scope(meta, kind, chapter_id, target=None):
    """Validate new writes without reinterpreting already registered history."""
    chapters = {c['id'] for c in meta.get('chapters', [])}
    if chapter_id is not None and (meta['type'] != 'novel' or chapter_id not in chapters):
        raise ValueError('Chapter scope is only valid for a known novel chapter')
    if kind == 'book_plan':
        if meta['type'] != 'novel' or chapter_id is not None or target not in {None, 'book'}:
            raise ValueError('Book plan requires a novel book target without chapter_id')
    elif kind == 'chapter_plan' or (kind == 'text' and meta['type'] == 'novel'):
        if meta['type'] != 'novel' or chapter_id not in chapters or (target is not None and target != chapter_id):
            raise ValueError('Novel text/chapter plan requires its exact chapter target')
    elif meta['type'] == 'wechat':
        if chapter_id is not None or target not in {None, 'article'}:
            raise ValueError('WeChat content requires an article target without chapter_id')
    elif kind == 'review' and target is not None:
        if (target == 'book' and chapter_id is not None) or (target != 'book' and target != chapter_id):
            raise ValueError('Review registration must match its book/chapter target')


@locked
def add_revision(project, source, revision_id, kind, version, status, chapter_id=None,
                 parent_plan_id=None, based_on=None, decision_file=None, rules_review=None,
                 rules_mode=None, _rules_context=None, _rules_artifacts=None):
    if kind not in {'book_plan', 'chapter_plan', 'text', 'review'} or status not in {'draft', 'accepted', 'baseline', 'historical'}:
        raise ValueError('Unsupported revision kind or status')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', revision_id):
        raise ValueError('Invalid revision ID')
    problems = validate(project)
    if problems:
        raise ValueError('; '.join(problems))
    manifest = read_json(project / '版本记录/revisions.json')
    if any(r['id'] == revision_id for r in manifest['revisions']):
        raise ValueError('Revision already exists; create a new version')
    row = {'id': revision_id, 'kind': kind, 'version': version, 'status': status,
           'chapter_id': chapter_id, 'parent_plan_id': parent_plan_id, 'based_on': based_on,
           'path': '版本记录/content/' + revision_id + '.md', 'sha256': digest(source)}
    if status == 'accepted':
        if not decision_file or not Path(decision_file).read_text().strip():
            raise ValueError('Accepted versions require the actual author decision record')
        row['decision_path'] = '决策记录/' + revision_id + '.md'
        row['decision_sha256'] = digest(decision_file)
    by_id = {r['id']: r for r in manifest['revisions']}
    if kind == 'chapter_plan' and (parent_plan_id not in by_id or by_id[parent_plan_id]['kind'] != 'book_plan' or by_id[parent_plan_id]['status'] != 'accepted'):
        raise ValueError('Chapter plan must inherit an accepted book plan')
    if kind == 'text' and status == 'accepted' and read_json(project / 'book.yaml')['type'] == 'novel':
        parent = by_id.get(parent_plan_id, {})
        if parent.get('kind') != 'chapter_plan' or parent.get('chapter_id') != chapter_id or parent.get('status') != 'accepted':
            raise ValueError('Accepted text must inherit its accepted chapter plan')
    if based_on and based_on not in by_id:
        raise ValueError('Unknown predecessor')
    if based_on and (by_id[based_on]['kind'] != kind or by_id[based_on].get('chapter_id') != chapter_id):
        raise ValueError('Predecessor belongs to another kind/chapter')
    if parent_plan_id and parent_plan_id not in by_id:
        raise ValueError('Unknown parent plan')
    meta = read_json(project / 'book.yaml')
    validate_new_revision_scope(meta, kind, chapter_id)
    if chapter_id and chapter_id not in {c['id'] for c in meta.get('chapters', [])}:
        raise ValueError('Unknown chapter')
    if kind == 'chapter_plan' and not chapter_id:
        raise ValueError('Chapter plan needs a chapter ID')
    if kind != 'review':
        from writing_rules import resolve_rules, validate_review
        from material_index import immutable_json
        target = chapter_id or ('book' if meta['type'] == 'novel' else 'article')
        mode = rules_mode or ('plan' if kind in {'book_plan', 'chapter_plan'} else 'revise' if based_on else 'draft')
        if _rules_context is None and ((kind == 'text' and mode not in {'draft', 'revise', 'trial', 'deliver'})
                or (kind in {'book_plan', 'chapter_plan'} and mode not in {'plan', 'revise'})):
            raise ValueError('Rules mode does not match registered content kind')
        rule_context = _rules_context if _rules_context is not None else resolve_rules(project, target, mode)
        if rule_context.get('enabled'):
            if rule_context['project_id'] != meta['id'] or rule_context['target'] != target:
                raise ValueError('Rule review belongs to another work/chapter')
            if not rules_review:
                raise ValueError('Enabled rules require a matching lightweight/run rule review before registration')
            review = read_json(rules_review)
            artifacts = _rules_artifacts
            if artifacts is None:
                artifacts = [a for a in review.get('artifacts', []) if isinstance(a, dict) and a.get('sha256') == row['sha256']]
                if len(artifacts) != 1:
                    raise ValueError('Lightweight review must identify this exact content version once')
            validate_review(rule_context, review, artifacts)
            if row['sha256'] not in {a['sha256'] for a in review['artifacts']}:
                raise ValueError('Rule review does not cover the registered content')
            relative = '版本记录/rule-reviews/' + revision_id + '.json'
            receipt = {'schema_version': 1, 'context': rule_context, 'review': review}
            immutable_json(scoped_path(project, relative), receipt)
            row['rule_review'] = {'path': relative, 'sha256': digest(scoped_path(project, relative)),
                                  'rule_set_sha256': rule_context['rule_set_sha256']}
    immutable_copy(source, scoped_path(project, row['path']), row['sha256'])
    if decision_file and status == 'accepted':
        immutable_copy(decision_file, scoped_path(project, row['decision_path']))
    manifest['revisions'].append(row)
    write_json(project / '版本记录/revisions.json', manifest)
    write_json(project / 'state.json', derive_state(project))
    return row


@locked
def init_project(workspace, project_id, title, project_type):
    if project_type not in {'wechat', 'novel'} or not title.strip():
        raise ValueError('Valid project type and title required')
    if not re.fullmatch(r'[a-z][a-z0-9-]*', project_id):
        raise ValueError('Use a stable lowercase project ID')
    catalog_path = Path(workspace) / 'catalog.json'
    catalog = load_catalog(workspace) if catalog_path.exists() else {'schema_version': 1, 'projects': []}
    registered = {scoped_path(workspace, p['path']).resolve() for p in catalog['projects']}
    # Do not hide an existing work behind a new or incomplete catalog.
    for folder in ['novels', 'wechat']:
        parent = Path(workspace) / folder
        if parent.is_dir():
            for existing in parent.iterdir():
                if existing.is_dir() and not existing.name.startswith('.') and existing.resolve() not in registered:
                    raise ValueError('Existing unregistered project; restore/reconcile catalog before init: ' + existing.name)
    if any(project_id == p['id'] or title in [p['title'], *p.get('aliases', [])] for p in catalog['projects']):
        raise ValueError('Project already exists')
    relative = ('novels/' if project_type == 'novel' else 'wechat/') + project_id
    project = scoped_path(workspace, relative)
    project.mkdir(parents=True, exist_ok=False)
    write_json(project / 'book.yaml', {'schema_version': 1, 'id': project_id, 'title': title, 'type': project_type, 'chapters': []})
    write_json(project / '版本记录/revisions.json', {'schema_version': 1, 'revisions': []})
    write_json(project / 'state.json', derive_state(project))
    opening = ('先明确本作品目标，建立并确认全书及章节方案。' if project_type == 'novel'
               else '根据本次请求直接成稿、修改或审阅；仅在任务需要时先讨论提纲。')
    atomic_text(project / 'START-HERE.md', '# ' + title + '\n\n' + opening + '人物、事实和虚构授权仅属于本作品。\n')
    catalog['projects'].append({'id': project_id, 'title': title, 'type': project_type, 'path': relative, 'aliases': []})
    write_json(catalog_path, catalog)
    return project


@locked
def set_chapters(project, chapters):
    problems = validate(project)
    if problems:
        raise ValueError('; '.join(problems))
    meta = read_json(project / 'book.yaml')
    if meta['type'] != 'novel' or not isinstance(chapters, list):
        raise ValueError('Chapters must be an array for a novel')
    ids = [c.get('id', '') for c in chapters]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', x) for x in ids) or any(not c.get('title') for c in chapters):
        raise ValueError('Unique chapter IDs and titles required')
    used = {r['chapter_id'] for r in read_json(project / '版本记录/revisions.json')['revisions'] if r.get('chapter_id')}
    if not used.issubset(ids):
        raise ValueError('Cannot remove chapters with registered versions')
    meta['chapters'] = chapters
    write_json(project / 'book.yaml', meta)
    write_json(project / 'state.json', derive_state(project))
    return meta


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path, default=Path('workspace'))
    subs = p.add_subparsers(dest='command', required=True)
    for command in ['resume', 'validate', 'rebuild-state', 'search', 'add-revision', 'set-chapters']:
        s = subs.add_parser(command); s.add_argument('--project', required=True)
        if command == 'resume':
            s.add_argument('--chapter'); s.add_argument('--mode')
        if command == 'set-chapters': s.add_argument('--file', type=Path, required=True)
        if command == 'search':
            s.add_argument('--query', required=True); s.add_argument('--history', action='store_true')
        if command == 'add-revision':
            for name in ['source', 'id', 'kind', 'version', 'status']: s.add_argument('--' + name, required=True)
            for name in ['chapter', 'parent-plan', 'based-on', 'decision-file', 'rules-review', 'rules-mode']: s.add_argument('--' + name)
    s = subs.add_parser('init'); s.add_argument('--id', required=True); s.add_argument('--title', required=True)
    s.add_argument('--type', choices=['wechat', 'novel'], required=True)
    a = p.parse_args()
    a.workspace = a.workspace.expanduser().resolve()
    if a.command == 'init':
        result = str(init_project(a.workspace, a.id, a.title, a.type))
    else:
        project = resolve_project(a.workspace, a.project)
        if a.command == 'resume':
            result = dict(context(project, a.chapter, a.mode), workspace=str(a.workspace), project_path=str(project))
        elif a.command == 'set-chapters': result = set_chapters(project, read_json(a.file))
        elif a.command == 'validate':
            result = {'errors': validate(project)}
            if result['errors']: print(json.dumps(result, ensure_ascii=False)); raise SystemExit(1)
        elif a.command == 'rebuild-state':
            errors = validate(project)
            if errors: raise ValueError('; '.join(errors))
            result = derive_state(project); write_json(project / 'state.json', result)
        elif a.command == 'search': result = retrieve(project, a.query, a.history)
        else: result = add_revision(project, a.source, a.id, a.kind, a.version, a.status, a.chapter, a.parent_plan, a.based_on, a.decision_file, a.rules_review, a.rules_mode)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit('Error: ' + str(exc))
