#!/usr/bin/env python3
"""Create and verify portable private workspace backups; restore to a new directory."""
import argparse
import io
import json
import os
import shutil
import tarfile
import tempfile
from pathlib import Path
from workspace_lib import digest, scoped_path, read_json, write_json, write_lock


def inventory(root):
    rows = []
    for p in sorted(Path(root).rglob('*')):
        if p.is_symlink():
            raise ValueError('Workspace backups do not follow symlinks')
        if p.is_file() and p.name != '.writing.lock':
            rows.append({'path': p.relative_to(root).as_posix(), 'sha256': digest(p), 'bytes': p.stat().st_size})
    return rows


def create(workspace, output):
    workspace, output = Path(workspace).resolve(), Path(output).resolve()
    if not workspace.is_dir() or output.is_relative_to(workspace):
        raise ValueError('Backup must be outside the existing workspace')
    output.parent.mkdir(parents=True, exist_ok=True)
    with write_lock(workspace):
        rows = inventory(workspace)
        with output.open('xb') as stream:
            os.chmod(output, 0o600)
            with tarfile.open(fileobj=stream, mode='w:gz', compresslevel=1) as archive:
                manifest = json.dumps({'schema_version': 1, 'files': rows}, ensure_ascii=False).encode()
                info = tarfile.TarInfo('backup-manifest.json'); info.size = len(manifest); info.mode = 0o600
                archive.addfile(info, io.BytesIO(manifest))
                for row in rows:
                    archive.add(scoped_path(workspace, row['path']), arcname='workspace/' + row['path'], recursive=False)
        if inventory(workspace) != rows:
            output.unlink()
            raise ValueError('Workspace changed during backup; take a new snapshot')
    receipt = {'schema_version': 1, 'archive': str(output), 'sha256': digest(output), 'files': len(rows),
               'source_bytes': sum(r['bytes'] for r in rows), 'verified_restore': False}
    write_json(str(output) + '.json', receipt)
    return receipt


def restore(archive_path, destination):
    archive_path, destination = Path(archive_path), Path(destination).resolve()
    if destination.exists():
        raise ValueError('Restore target must not already exist')
    receipt = read_json(str(archive_path) + '.json')
    if digest(archive_path) != receipt['sha256']:
        raise ValueError('Backup checksum mismatch')
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.touge-restore-', dir=destination.parent))
    try:
        with tarfile.open(archive_path, 'r:gz') as archive:
            members = archive.getmembers()
            names = [m.name for m in members]
            if len(names) != len(set(names)) or any(not m.isfile() for m in members):
                raise ValueError('Backup contains duplicate/non-file entries')
            for member in members:
                scoped_path(temp, member.name)
            manifest = json.load(archive.extractfile('backup-manifest.json'))
            expected = {r['path']: r for r in manifest['files']}
            if len(expected) != len(manifest['files']) or set(names) != {'backup-manifest.json', *('workspace/' + p for p in expected)}:
                raise ValueError('Backup manifest does not match archive')
            for rel, row in expected.items():
                target = scoped_path(temp, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile('workspace/' + rel) as src, target.open('xb') as out:
                    os.chmod(target, 0o600); shutil.copyfileobj(src, out)
                if digest(target) != row['sha256'] or target.stat().st_size != row['bytes']:
                    raise ValueError('Restored file checksum mismatch')
        os.rename(temp, destination)
    finally:
        if temp.exists(): shutil.rmtree(temp)
    result = dict(receipt, verified_restore=True, destination=str(destination))
    write_json(str(archive_path) + '.restore.json', result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('create'); s.add_argument('--workspace', type=Path, default=Path('workspace')); s.add_argument('--out', type=Path, required=True)
    s = sub.add_parser('restore'); s.add_argument('--archive', type=Path, required=True); s.add_argument('--destination', type=Path, required=True)
    a = p.parse_args(); result = create(a.workspace, a.out) if a.command == 'create' else restore(a.archive, a.destination)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
