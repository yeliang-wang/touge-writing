#!/usr/bin/env python3
"""Copy a frozen private inventory into a workspace, without changing sources.

Plan schema: {schema_version:1, migration_id:str, entries:[{source:absolute,
destination:relative, sha256:str, source_id:str}]}.
Keep the plan and report private: they contain source paths.
"""
import argparse
from pathlib import Path
from workspace_lib import immutable_copy, read_json, scoped_path, write_json, digest


def migrate(plan, workspace):
    workspace = Path(workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True, mode=0o700)
    if plan.get('schema_version') != 1 or not plan.get('entries'):
        raise ValueError('Unsupported or empty inventory')
    destinations = set()
    # Validate the complete inventory before copying any file.
    for item in plan['entries']:
        dest = scoped_path(workspace, item['destination'])
        if str(dest) in destinations:
            raise ValueError('Duplicate inventory destination')
        destinations.add(str(dest))
        source = Path(item['source'])
        if source.is_symlink() or not source.is_file() or digest(source) != item['sha256']:
            raise ValueError('Source differs from frozen inventory: ' + str(source))
        if dest.exists() and digest(dest) != item['sha256']:
            raise ValueError('Destination already contains different content: ' + str(dest))
    receipts = []
    for item in plan['entries']:
        sha = immutable_copy(item['source'], scoped_path(workspace, item['destination']), item['sha256'])
        receipts.append(dict(item, verified_sha256=sha))
    result = {'schema_version': 1, 'migration_id': plan['migration_id'],
              'files': len(receipts), 'entries': receipts, 'status': 'verified'}
    write_json(workspace / 'archives' / 'migration-receipt.json', result)
    return result


def verify(receipt, workspace, check_sources=False):
    errors = []
    for item in receipt['entries']:
        p = scoped_path(workspace, item['destination'])
        if not p.is_file() or digest(p) != item['sha256']:
            errors.append(item['destination'])
        if check_sources:
            p = Path(item['source'])
            if not p.is_file() or digest(p) != item['sha256']:
                errors.append('source:' + item['source'])
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path)
    p.add_argument('--workspace', type=Path, default=Path('workspace'))
    p.add_argument('--verify', action='store_true')
    p.add_argument('--check-sources', action='store_true')
    args = p.parse_args()
    if args.verify:
        receipt = read_json(args.workspace / 'archives/migration-receipt.json')
        errors = verify(receipt, args.workspace, args.check_sources)
        print('Migration files: %s; mismatches: %s' % (receipt['files'], len(errors)))
        if errors:
            raise SystemExit('\n'.join(errors))
    else:
        if not args.plan:
            p.error('--plan required for migration')
        result = migrate(read_json(args.plan), args.workspace)
        print('Verified %s files' % result['files'])


if __name__ == '__main__':
    main()
