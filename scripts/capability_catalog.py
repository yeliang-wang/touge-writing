#!/usr/bin/env python3
"""Resolve public versioned methods; scripts validate identities, not prose quality."""
import argparse
import json
import re
from pathlib import Path
from workspace_lib import read_json, scoped_path, digest

ROOT = Path(__file__).resolve().parents[1]


def catalog(root=ROOT):
    root = Path(root)
    data = read_json(root / 'capabilities/registry.json')
    if data.get('schema_version') != 1:
        raise ValueError('Unsupported capability registry schema')
    keys = set()
    for item in data['capabilities']:
        key = (item['id'], item['version'])
        if key in keys or not re.fullmatch(r'[a-z][a-z0-9-]*', item['id']):
            raise ValueError('Duplicate/invalid capability identity')
        if not re.fullmatch(r'\d+\.\d+\.\d+', item['version']):
            raise ValueError('A released capability needs an explicit semantic version')
        keys.add(key)
        path = scoped_path(root, item['path'])
        expected = 'capabilities/%s/%s/CAPABILITY.md' % key
        if item['path'] != expected or path.is_symlink() or digest(path) != item['sha256']:
            raise ValueError('Missing/changed capability: ' + item['id'])
        if not item.get('applies_to') or not set(item['applies_to']) <= {'wechat', 'novel'}:
            raise ValueError('Invalid capability scope')
    return data


def resolve(specs, kind=None, root=ROOT):
    rows = catalog(root)['capabilities']
    result = []
    for spec in specs:
        parts = spec.split('@')
        if len(parts) != 2:
            raise ValueError('Pin a version explicitly: capability-id@1.0.0')
        found = [r for r in rows if (r['id'], r['version']) == tuple(parts)]
        if len(found) != 1 or (kind and kind not in found[0]['applies_to']):
            raise ValueError('Unknown/inapplicable capability: ' + spec)
        if found[0] in result:
            raise ValueError('Duplicate selected capability')
        result.append(found[0])
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--select', nargs='*')
    p.add_argument('--kind', choices=['wechat', 'novel'])
    a = p.parse_args()
    print(json.dumps(resolve(a.select, a.kind) if a.select is not None else catalog(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit('Error: ' + str(exc))
