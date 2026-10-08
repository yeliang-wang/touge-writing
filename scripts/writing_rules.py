#!/usr/bin/env python3
"""Resolve a work's explicit rules and check review records, never literary quality."""
import argparse
import json
import re
from pathlib import Path
from workspace_lib import read_json, scoped_path, digest
from material_index import fingerprint

MODES = {'trial', 'plan', 'draft', 'revise', 'review', 'title', 'deliver'}
STATUSES = {'satisfied', 'partial', 'unmet', 'not_applicable', 'needs_verification'}
SHA = re.compile(r'[0-9a-f]{64}')
ANCHOR = re.compile(r'<a\s+(?:id|name)=[\"\']([^\"\']+)[\"\']\s*>\s*</a>', re.I)


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(label + ' must be a nonempty string')
    return value


def _path(project, relative):
    _text(relative, 'Rule path')
    if Path(relative).as_posix() != relative or relative == '.':
        raise ValueError('Rule paths must be canonical relative paths')
    path = scoped_path(project, relative)
    if path.is_symlink() or not path.is_file():
        raise ValueError('Rule dependency missing or not a regular file: ' + relative)
    return path


def _anchor(path, anchor):
    _text(anchor, 'Rule anchor')
    if anchor.startswith('#'):
        raise ValueError('Rule anchors omit the # prefix')
    if ANCHOR.findall(path.read_text(encoding='utf-8')).count(anchor) != 1:
        raise ValueError('Rule anchor must occur exactly once: ' + str(path) + '#' + anchor)


def resolve_rules(project, target=None, mode=None):
    """Validate the complete manifest, then select only this task's rules."""
    project = Path(project)
    meta = read_json(project / 'book.yaml')
    if 'rules_manifest' not in meta:
        return {'enabled': False, 'project_id': meta['id'],
                'notice': 'Rules manifest not enabled; legacy rule loading remains manual.'}
    if mode is not None and mode not in MODES:
        raise ValueError('Unknown rules mode')
    targets = {c['id'] for c in meta.get('chapters', [])} | ({'book'} if meta['type'] == 'novel' else {'article'})
    target = target or ('book' if meta['type'] == 'novel' else 'article')
    if target not in targets:
        raise ValueError('Unknown rules target')
    manifest_path = _path(project, meta['rules_manifest'])
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 1 or manifest.get('project_id') != meta['id']:
        raise ValueError('Unsupported rules manifest or different project')
    _text(manifest.get('id'), 'Rules manifest ID')
    if not isinstance(manifest.get('files'), list) or not manifest['files']:
        raise ValueError('Rules manifest needs dependency files')
    files = {}
    for row in manifest['files']:
        if not isinstance(row, dict):
            raise ValueError('Invalid rules dependency')
        path = _path(project, row.get('path'))
        if row['path'] in files or row['path'] == meta['rules_manifest']:
            raise ValueError('Duplicate/self-referencing rules dependency')
        _text(row.get('role'), 'Rules dependency role')
        if not isinstance(row.get('sha256'), str) or not SHA.fullmatch(row['sha256']) or digest(path) != row['sha256']:
            raise ValueError('Rule dependency hash mismatch: ' + row['path'])
        files[row['path']] = dict(row)
    if meta.get('rules_file') and meta['rules_file'] not in files:
        raise ValueError('Human rules_file entry must be a hashed manifest dependency')
    rules, seen = [], set()
    if not isinstance(manifest.get('rules'), list):
        raise ValueError('Rules manifest needs a rules array')
    for row in manifest['rules']:
        if not isinstance(row, dict):
            raise ValueError('Invalid rule entry')
        rid = _text(row.get('id'), 'Rule ID')
        if rid in seen:
            raise ValueError('Duplicate rule ID: ' + rid)
        seen.add(rid)
        if row.get('path') not in files:
            raise ValueError('Rule body must be a declared dependency: ' + rid)
        _anchor(_path(project, row['path']), row.get('anchor'))
        if row.get('kind') not in {'required', 'guidance'} or row.get('check') not in {'semantic', 'mechanical'}:
            raise ValueError('Unknown rule kind/check: ' + rid)
        for key, allowed in [('targets', targets), ('modes', MODES)]:
            values = row.get(key)
            if (not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values)
                    or len(set(values)) != len(values) or not set(values).issubset(allowed | {'*'})
                    or ('*' in values and len(values) != 1)):
                raise ValueError('Invalid rule ' + key + ': ' + rid)
        if not isinstance(row.get('sources'), list):
            raise ValueError('Rule sources must be an array: ' + rid)
        for source in row['sources']:
            if not isinstance(source, dict) or source.get('path') not in files:
                raise ValueError('Rule source must be a declared dependency: ' + rid)
            if 'anchor' in source:
                _anchor(_path(project, source['path']), source['anchor'])
        if ('*' in row['targets'] or target in row['targets']) and (mode is None or '*' in row['modes'] or mode in row['modes']):
            rules.append(dict(row))
    result = {'enabled': True, 'schema_version': 1, 'project_id': meta['id'],
              'target': target, 'mode': mode,
              'manifest': {'id': manifest['id'], 'path': meta['rules_manifest'], 'sha256': digest(manifest_path)},
              'files': list(files.values()), 'rules': rules}
    result['rule_set_sha256'] = fingerprint(result)
    return result


def check_context(context):
    """Check an immutable resolved context without substituting today's rules."""
    if not context.get('enabled'):
        return
    basis = {k: v for k, v in context.items() if k != 'rule_set_sha256'}
    if fingerprint(basis) != context.get('rule_set_sha256'):
        raise ValueError('Resolved rule context changed')


def reading_paths(project, context, pins=None, run_folder=None):
    if not context.get('enabled'):
        return []
    paths = [context['manifest'], *context['files']]
    if pins is not None:
        snapshots = {p['source']: p for p in pins if p['origin'] == 'project'}
        return [{'source': f['path'], 'path': str(scoped_path(run_folder, snapshots[f['path']]['snapshot'])),
                 'sha256': f['sha256'], 'read_state': 'not_attested'} for f in paths]
    return [{'source': f['path'], 'path': str(scoped_path(project, f['path'])),
             'sha256': f['sha256'], 'read_state': 'not_attested'} for f in paths]


def validate_review(context, review, artifacts, require_completed=False):
    """Check exact artifact versions and rule coverage, not truth or prose merit."""
    check_context(context)
    if not context.get('enabled'):
        raise ValueError('Rule review validation needs an enabled rule context')
    if not isinstance(review, dict) or review.get('rule_set_sha256') != context['rule_set_sha256']:
        raise ValueError('Review does not match the resolved rule set')
    if review.get('task_result') not in {'completed', 'in_progress'}:
        raise ValueError('Review needs a separate task_result')
    if require_completed and (review['task_result'] != 'completed' or review.get('unresolved_blockers') != []):
        raise ValueError('Task review is incomplete or has unresolved task blockers')
    if review.get('manuscript_result') not in {'meets_rules', 'needs_revision', 'not_assessed'}:
        raise ValueError('Review needs a separate manuscript_result')
    if not review.get('scope') or not review.get('findings'):
        raise ValueError('Review needs actual scope and findings')
    known = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not artifact.get('id') or artifact['id'] in known:
            raise ValueError('Duplicate/invalid reviewable artifact')
        if not isinstance(artifact.get('sha256'), str) or not SHA.fullmatch(artifact['sha256']):
            raise ValueError('Invalid reviewable artifact hash')
        known[artifact['id']] = artifact['sha256']
    covered = {}
    refs = review.get('artifacts')
    if not isinstance(refs, list) or not refs:
        raise ValueError('Review needs immutable artifact references')
    for ref in refs:
        if not isinstance(ref, dict) or ref.get('id') not in known or known[ref['id']] != ref.get('sha256') or ref['id'] in covered:
            raise ValueError('Review artifact version mismatch/duplicate')
        covered[ref['id']] = ref['sha256']
    rows = review.get('rule_coverage')
    if not isinstance(rows, list):
        raise ValueError('Review needs rule_coverage')
    expected = {r['id']: r for r in context['rules']}
    seen = set()
    required_unmet = []
    for row in rows:
        if not isinstance(row, dict) or row.get('rule_id') not in expected or row['rule_id'] in seen:
            raise ValueError('Unknown/duplicate review rule')
        rid = row['rule_id']; seen.add(rid)
        if row.get('status') not in STATUSES:
            raise ValueError('Unknown coverage status: ' + rid)
        _text(row.get('reason'), 'Rule review reason')
        if row['status'] == 'not_applicable':
            _text(row.get('basis'), 'Not-applicable basis')
        evidence = row.get('evidence')
        if not isinstance(evidence, list) or not evidence:
            raise ValueError('Every rule needs artifact evidence/location: ' + rid)
        evidenced = set()
        for item in evidence:
            if not isinstance(item, dict) or item.get('artifact_id') not in covered or covered[item['artifact_id']] != item.get('sha256'):
                raise ValueError('Rule evidence does not match the reviewed artifact: ' + rid)
            _text(item.get('location'), 'Rule evidence location')
            evidenced.add(item['artifact_id'])
        if evidenced != set(covered):
            raise ValueError('Rule evidence must cover every reviewed artifact: ' + rid)
        if expected[rid]['kind'] == 'required' and row['status'] not in {'satisfied', 'not_applicable'}:
            required_unmet.append(rid)
    if seen != set(expected):
        raise ValueError('Missing applicable rule coverage: ' + ', '.join(sorted(set(expected) - seen)))
    if required_unmet and review['manuscript_result'] == 'meets_rules':
        raise ValueError('Manuscript cannot meet rules with unresolved required rules')
    return {'coverage_complete': True, 'task_result': review['task_result'],
            'manuscript_result': review['manuscript_result'], 'required_unmet': required_unmet,
            'author_acceptance': 'not_determined',
            'limits': 'Record/hash checks only; semantic judgments and actual reading remain the reviewer responsibility.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--project', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['resolve', 'check', 'review']:
        command = sub.add_parser(name)
        command.add_argument('--target')
        command.add_argument('--mode', choices=sorted(MODES))
        if name == 'review':
            command.add_argument('--review', type=Path, required=True)
            command.add_argument('--artifacts', type=Path, required=True)
    args = parser.parse_args()
    from writing_workspace import resolve_project
    project = resolve_project(args.workspace, args.project)
    context = resolve_rules(project, args.target, args.mode)
    if args.command == 'review':
        artifacts = read_json(args.artifacts)
        for artifact in artifacts:
            if digest(_path(project, artifact.get('path'))) != artifact.get('sha256'):
                raise ValueError('Actual review artifact changed')
        result = validate_review(context, read_json(args.review), artifacts)
    else:
        result = dict(context, read_full_text=reading_paths(project, context))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit('Error: ' + str(exc))
