#!/usr/bin/env python3
"""Export only the reviewed, hashed author-expression allowlist (no workspace)."""
import argparse
import json
import re
import zipfile
from pathlib import Path
from workspace_lib import digest, scoped_path, read_json

ROOT = Path(__file__).resolve().parents[1]
PROFILE_FILES = {'PROFILE.md', 'judgment.md', 'language.md', 'expression-evidence.md',
                 'lexicon.yaml', 'rubric.md', 'wechat-rubric.md'}


def export(profile, output):
    profile, output = Path(profile), Path(output)
    manifest = read_json(profile / 'manifest.json')
    files = manifest['files']
    if len(files) != len(PROFILE_FILES) or {x['path'] for x in files} != PROFILE_FILES:
        raise ValueError('Profile file allowlist changed; review before export')
    if not re.fullmatch(r'[a-z0-9-]+', manifest['id']) or not re.fullmatch(r'\d+\.\d+\.\d+', manifest['version']):
        raise ValueError('Invalid profile ID/version')
    payload = {}
    for row in files:
        source = scoped_path(profile, row['path'])
        if source.is_symlink() or digest(source) != row['sha256']:
            raise ValueError('Changed profile file: ' + row['path'])
        payload[row['path']] = source.read_bytes()
    payload['manifest.json'] = (profile / 'manifest.json').read_bytes()
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = manifest['id'] + '-author-expression-' + manifest['version'] + '/'
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for name, body in sorted(payload.items()):
            entry = zipfile.ZipInfo(prefix + name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            z.writestr(entry, body)
    return {'files': len(payload), 'sha256': digest(output), 'path': str(output)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', type=Path, default=ROOT/'shared/author-expression');p.add_argument('--out', type=Path, required=True)
    a=p.parse_args();print(json.dumps(export(a.profile, a.out), ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
