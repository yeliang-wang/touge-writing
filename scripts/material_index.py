#!/usr/bin/env python3
"""Explicitly scoped source discovery and immutable work-local usage maps."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from workspace_lib import read_json, scoped_path, digest, write_json, atomic_text, locked
from private_retriever import tokenize, cosine, best_snippets


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', value):
        raise ValueError('Invalid stable ID')
    return value


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def immutable_json(path, data):
    path = Path(path)
    if path.exists():
        if read_json(path) != data:
            raise ValueError('Immutable record conflicts: ' + str(path))
    else:
        write_json(path, data)


def normalize(manifest):
    """Read both historical formats without modifying either. Empty bodies stay visible."""
    manifest = Path(manifest).resolve()
    text = manifest.read_text(encoding='utf-8')
    if text.lstrip().startswith('['):
        rows = json.loads(text)
    else:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    result, ids = [], set()
    for r in rows:
        sid = str(r['id'])  # JSONL source_id is a collection, NOT document identity.
        if sid in ids:
            raise ValueError('Duplicate source ID: ' + sid)
        ids.add(sid)
        field = 'text_path' if 'text_path' in r else 'markdown'
        raw = Path(r[field])
        if raw.is_absolute():
            try:
                raw = raw.relative_to(manifest.parent)
            except ValueError as exc:
                raise ValueError('Body outside explicitly selected corpus; copy or explicitly rebase manifest') from exc
        path = scoped_path(manifest.parent, raw)
        if path.is_symlink() or not path.is_file():
            raise ValueError('Missing/non-regular source: ' + sid)
        body = path.read_text(encoding='utf-8')
        if r.get('text_hash'):
            # ingest_corpus hashes stripped text, then writes exactly one added newline.
            original = body[:-1] if body.endswith('\n') else body
            if hashlib.sha256(original.encode()).hexdigest() != r['text_hash']:
                raise ValueError('JSONL source hash mismatch: ' + sid)
        if r.get('sha256') and digest(path) != r['sha256']:
            raise ValueError('Source hash mismatch: ' + sid)
        result.append({'source_id': sid, 'collection_id': r.get('source_id'),
                       'manifest': str(manifest), 'manifest_sha256': digest(manifest),
                       'path': str(path), 'sha256': digest(path), 'title': r.get('title', ''),
                       'url': r.get('url'), 'publish_time': r.get('publish_time', r.get('timestamp')),
                       'word_count': r.get('word_count', r.get('char_count', len(body.strip()))),
                       'tags': r.get('tags', []), 'aliases': r.get('aliases', []),
                       'allowed_uses': r.get('allowed_uses'), 'forbidden_uses': r.get('forbidden_uses', []),
                       'available': bool(body.strip()) and r.get('word_count', 1) > 0,
                       'read_state': 'not_attested', 'facts_verified': False})
    return result


def search(manifest, query, top_k=5):
    tokens = tokenize(query); q = Counter(tokens); results = []
    for item in normalize(manifest):
        if not item['available']:
            continue
        body = Path(item['path']).read_text(encoding='utf-8')
        terms = ' '.join(item['tags'] + item['aliases'])
        score = cosine(q, Counter(tokenize(item['title'] + '\n' + terms + '\n' + body)))
        if score:
            results.append({**item, 'markdown_path': item['path'], 'score': round(score, 4),
                            'snippets': best_snippets(body, set(tokens)), 'read_state': 'search_hit'})
    return sorted(results, key=lambda r: (-r['score'], r['source_id']))[:max(0, top_k)]


def read_source(manifest, source_id, start=1, end=None):
    matches = [r for r in normalize(manifest) if r['source_id'] == source_id]
    if len(matches) != 1 or not matches[0]['available']:
        raise ValueError('Unknown or empty source')
    row = matches[0]; lines = Path(row['path']).read_text(encoding='utf-8').splitlines()
    end = len(lines) if end is None else end
    if start < 1 or end < start or end > len(lines):
        raise ValueError('Invalid read range')
    return {**row, 'start_line': start, 'end_line': end, 'total_lines': len(lines),
            'content': '\n'.join(lines[start-1:end]), 'read_state': 'delivered_to_host',
            'full_text_delivered': start == 1 and end == len(lines)}


@locked
def attest_read(project, record_id, delivery, host_record, summary):
    """Attestation names an actual host reading record, never a fact-verification flag."""
    identifier(record_id)
    if not host_record.strip() or not summary.strip() or delivery.get('read_state') != 'delivered_to_host':
        raise ValueError('Actual host read reference and source-specific summary required')
    fresh = read_source(delivery['manifest'], delivery['source_id'], delivery['start_line'], delivery['end_line'])
    if fresh != delivery:
        raise ValueError('Delivered source/range changed; read again')
    row = {k: v for k, v in delivery.items() if k != 'content'}
    row.update({'id': record_id, 'schema_version': 1, 'host_record': host_record,
                'summary': summary, 'read_state': 'host_attested', 'facts_verified': False})
    immutable_json(scoped_path(project, 'materials/reads/' + record_id + '.json'), row)
    return row


def validate_mapping(project, data):
    from writing_workspace import validate
    if validate(project):
        raise ValueError('Invalid content registry')
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported material mapping schema')
    identifier(data['id'])
    meta = read_json(project / 'book.yaml')
    chapters = {r['id'] for r in meta.get('chapters', [])}
    revisions = {r['id']: r for r in read_json(project / '版本记录/revisions.json')['revisions']}
    sources, units = {}, {}
    for source in data['sources']:
        key = source['key']; identifier(key)
        if key in sources:
            raise ValueError('Duplicate source version key')
        # A caller explicitly opts into each manifest; no global or cross-work scan.
        found = [r for r in normalize(source['manifest']) if r['source_id'] == source['source_id']]
        if len(found) != 1 or found[0]['sha256'] != source['sha256']:
            raise ValueError('Missing/changed source version')
        sources[key] = found[0]
    for unit in data['units']:
        identifier(unit['id'])
        if unit['id'] in units or not unit.get('label'):
            raise ValueError('Duplicate/incomplete event or theme unit')
        if unit['status'] not in {'supported', 'conflicting', 'inferred', 'fictional', 'unknown'}:
            raise ValueError('Unknown evidence status')
        if unit['status'] == 'conflicting' and not unit.get('open_issue'):
            raise ValueError('Conflicting unit needs issue and impact')
        if unit['status'] == 'fictional' and not unit.get('authorization_ref'):
            raise ValueError('Fictional unit needs scoped authorization reference')
        if unit['status'] == 'supported' and not unit.get('anchors'):
            raise ValueError('Supported unit needs evidence anchors')
        for anchor in unit.get('anchors', []):
            source = sources.get(anchor['source_key'])
            if not source:
                raise ValueError('Unknown source version')
            lines = Path(source['path']).read_text(encoding='utf-8').splitlines()
            start, end = anchor['start_line'], anchor['end_line']
            if start < 1 or end < start or end > len(lines) or not anchor['quote'] or anchor['quote'] not in '\n'.join(lines[start-1:end]):
                raise ValueError('Stale/incorrect source anchor')
        units[unit['id']] = unit
    for usage in data['usages']:
        if usage['unit_id'] not in units or usage.get('role') not in {'main_scene', 'echo', 'background', 'argument', 'transition'}:
            raise ValueError('Unknown unit or usage role')
        if meta['type'] == 'novel' and usage.get('chapter_id') not in chapters:
            raise ValueError('Use registered chapter identity, not imported display number')
        for field in ['plan_id', 'content_id']:
            if usage.get(field):
                r = revisions.get(usage[field])
                kinds = {'book_plan', 'chapter_plan'} if field == 'plan_id' else {'text'}
                if not r or r['kind'] not in kinds or (r.get('chapter_id') and r['chapter_id'] != usage.get('chapter_id')):
                    raise ValueError('Usage refers to wrong content/plan identity')
    return data


@locked
def register_mapping(project, data):
    validate_mapping(project, data)
    if data.get('based_on'):
        previous = scoped_path(project, 'materials/maps/' + identifier(data['based_on']) + '.json')
        if not previous.is_file() or data['based_on'] == data['id']:
            raise ValueError('Mapping must refer to an existing prior version')
    immutable_json(scoped_path(project, 'materials/maps/' + data['id'] + '.json'), data)
    return data


def relations(project, mapping_id, unit_id=None, chapter_id=None):
    project = Path(project)
    data = read_json(scoped_path(project, 'materials/maps/' + identifier(mapping_id) + '.json'))
    validate_mapping(project, data)
    uses = [r for r in data['usages'] if (not unit_id or r['unit_id'] == unit_id)
            and (not chapter_id or r.get('chapter_id') == chapter_id)]
    ids = {r['unit_id'] for r in uses}
    units = [r for r in data['units'] if r['id'] in ids]
    keys = {a['source_key'] for r in units for a in r.get('anchors', [])}
    return {'mapping_id': mapping_id, 'units': units, 'usages': uses,
            'sources': [s for s in data['sources'] if s['key'] in keys],
            'chapter_identity_changed': False}


def main():
    p = argparse.ArgumentParser(description=__doc__); s = p.add_subparsers(dest='command', required=True)
    for cmd in ['index', 'search', 'read']:
        x = s.add_parser(cmd); x.add_argument('--manifest', type=Path, required=True)
        if cmd == 'search':
            x.add_argument('--query', required=True); x.add_argument('--top-k', type=int, default=5)
        if cmd == 'read':
            x.add_argument('--source-id', required=True); x.add_argument('--start', type=int, default=1); x.add_argument('--end', type=int)
    x = s.add_parser('map'); x.add_argument('--project-path', type=Path, required=True); x.add_argument('--file', type=Path, required=True)
    x = s.add_parser('attest-read'); x.add_argument('--project-path', type=Path, required=True)
    for name in ['id', 'delivery', 'host-record', 'summary']: x.add_argument('--' + name, required=True)
    x = s.add_parser('relations'); x.add_argument('--project-path', type=Path, required=True)
    x.add_argument('--mapping', required=True); x.add_argument('--unit'); x.add_argument('--chapter')
    a = p.parse_args()
    if a.command == 'index': result = normalize(a.manifest)
    elif a.command == 'search': result = search(a.manifest, a.query, a.top_k)
    elif a.command == 'read': result = read_source(a.manifest, a.source_id, a.start, a.end)
    elif a.command == 'map': result = register_mapping(a.project_path, read_json(a.file))
    elif a.command == 'relations': result = relations(a.project_path, a.mapping, a.unit, a.chapter)
    else: result = attest_read(a.project_path, a.id, read_json(a.delivery), a.host_record, a.summary)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError) as exc:
        raise SystemExit('Error: ' + str(exc))
