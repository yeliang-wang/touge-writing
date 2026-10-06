#!/usr/bin/env python3
"""Build a deterministic public ZIP from audited Git candidates; no private work."""
import argparse
import json
import zipfile
from pathlib import Path
from workspace_lib import digest
from preflight_check import ROOT, audit_public, public_paths


def distribution_directory(version):
    """Canonical extracted directory for current public releases."""
    return 'touge-writing-' + version


def build(output, root=ROOT):
    root = Path(root); output = Path(output)
    errors = audit_public(root)
    if errors:
        raise ValueError('; '.join(errors))
    if output.exists():
        raise ValueError('Refusing to replace an existing release asset')
    version = (root / 'VERSION').read_text().strip()
    rows, contents = [], {}
    for relative in public_paths(root):
        path = root / relative
        if not path.is_file():
            continue
        # Public in-tree compatibility symlinks become portable ordinary files.
        contents[relative] = path.read_bytes()
        rows.append({'path': relative, 'sha256': digest(path)})
    manifest = {'schema_version': 1, 'version': version, 'files': rows,
                'workspace_included': False, 'author_profile_version': '1.0.0'}
    contents['release-manifest.json'] = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = distribution_directory(version) + '/'
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for relative, body in sorted(contents.items()):
            info = zipfile.ZipInfo(prefix + relative, (2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, body)
    return {'version': version, 'files': len(contents), 'sha256': digest(output), 'path': str(output)}


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(); print(json.dumps(build(a.out), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        raise SystemExit('Error: ' + str(exc))
