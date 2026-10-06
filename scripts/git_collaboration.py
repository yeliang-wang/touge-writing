#!/usr/bin/env python3
"""Package and review Git contributions without merging or accepting content.

Use an independent private workspace Git repository. A contributor may only add
immutable contribution packages; the designated editor uses the existing
writing_workspace.py add-revision command after review and an actual decision.
These checks are a workflow guard, not GitHub access control or a signature.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from workspace_lib import digest, read_json, scoped_path
from writing_workspace import derive_state, resolve_project, validate


PACKAGE_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}')
COMMIT_ID = re.compile(r'[a-f0-9]{40}|[a-f0-9]{64}')


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _git(workspace, *args):
    result = subprocess.run(['git', '-C', str(workspace), *args], capture_output=True)
    if result.returncode:
        raise ValueError('Git command failed: ' + result.stderr.decode('utf-8', 'replace').strip())
    return result.stdout


def _workspace(workspace):
    workspace = Path(workspace).expanduser().resolve()
    root = Path(os.fsdecode(_git(workspace, 'rev-parse', '--show-toplevel')).strip()).resolve()
    if root != workspace:
        raise ValueError('Select the independent workspace Git root, not a subdirectory of another repository')
    if _git(workspace, 'rev-parse', '--is-bare-repository').strip() != b'false':
        raise ValueError('A workspace working tree is required')
    return workspace


def _commit(workspace, reference):
    if not reference or reference.startswith('-'):
        raise ValueError('An explicit common base commit is required')
    commit = _git(workspace, 'rev-parse', '--verify', '--end-of-options', reference + '^{commit}').decode().strip()
    if not COMMIT_ID.fullmatch(commit):
        raise ValueError('Invalid Git commit')
    if subprocess.run(['git', '-C', str(workspace), 'merge-base', '--is-ancestor', commit, 'HEAD'],
                      capture_output=True).returncode:
        raise ValueError('Base commit must be an ancestor of the current branch')
    return commit


def _regular(root, relative):
    """Reject every symlink component, even when it resolves inside the root."""
    relative = PurePosixPath(relative)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ValueError('Expected a relative path without traversal')
    path = scoped_path(root, str(relative))
    cursor = Path(root)
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError('Symlinks are not supported in collaboration inputs: ' + str(relative))
    if not path.is_file():
        raise ValueError('Missing regular file: ' + str(relative))
    return path


def _changed(workspace, base):
    changes = []
    # Check each layer separately: a local reversal must not hide a staged or
    # committed mutation that could otherwise be pushed independently.
    for layer, args in [
        ('committed', [base, 'HEAD']),
        ('staged', ['--cached', 'HEAD']),
        ('unstaged', []),
    ]:
        fields = _git(workspace, 'diff', '--no-ext-diff', '--name-status', '--no-renames', '-z', *args, '--').split(b'\0')
        fields = fields[:-1] if fields[-1] == b'' else fields
        if len(fields) % 2:
            raise ValueError('Unexpected Git diff output')
        for index in range(0, len(fields), 2):
            changes.append((layer, fields[index].decode(), os.fsdecode(fields[index + 1])))
    for path in _git(workspace, 'ls-files', '--others', '--exclude-standard', '-z').split(b'\0'):
        if path:
            changes.append(('untracked', 'A', os.fsdecode(path)))
    return changes


def _boundary(workspace, base):
    packages, changed_paths = set(), set()
    for layer, status, relative in _changed(workspace, base):
        parts = PurePosixPath(relative).parts
        if status != 'A' or len(parts) < 3 or parts[0] != 'contributions' or not PACKAGE_ID.fullmatch(parts[1]):
            raise ValueError('Protected workspace change or base drift; contributor changes must only add packages: '
                             + layer + ' ' + status + ' ' + relative)
        _regular(workspace, relative)
        packages.add('/'.join(parts[:2]))
        changed_paths.add(relative)
    return packages, changed_paths


def _baseline(workspace, project_id, chapter_id, base):
    project = resolve_project(workspace, project_id)
    meta = read_json(project / 'book.yaml')
    if meta['id'] != project_id:
        raise ValueError('Use the stable project ID rather than its title or alias')
    problems = validate(project)
    if problems:
        raise ValueError('Invalid content registration: ' + '; '.join(problems))
    state = derive_state(project)
    if chapter_id == 'article':
        if meta['type'] != 'wechat':
            raise ValueError('The article target requires a WeChat project')
        chapter = None
    elif chapter_id == 'book':
        if meta['type'] != 'novel':
            raise ValueError('The book target requires a novel project')
        chapter = None
    else:
        chapter = next((c for c in state['chapters'] if c['id'] == chapter_id), None)
        if not chapter:
            raise ValueError('Unknown stable chapter ID')
    project_relative = project.relative_to(workspace).as_posix()
    protected = {}
    for relative in ['catalog.json', project_relative + '/book.yaml', project_relative + '/版本记录/revisions.json']:
        local = _regular(workspace, relative)
        saved = _git(workspace, 'show', base + ':' + relative)
        if saved != local.read_bytes():
            raise ValueError('Registration/configuration differs from the declared base commit: ' + relative)
        protected[relative] = _sha(saved)
    rows = read_json(project / '版本记录/revisions.json')['revisions']
    by_id = {row['id']: row for row in rows}
    choices = [('book_plan', state.get('book_plan'))]
    if chapter:
        choices += [('chapter_plan', chapter.get('plan')),
                    ('accepted_text', chapter.get('accepted_text')),
                    ('latest_text', chapter.get('latest_text'))]
        plan = by_id.get(chapter.get('plan'), {})
        choices.append(('inherited_book_plan', plan.get('parent_plan_id')))
    elif chapter_id == 'article':
        accepted = [r['id'] for r in rows if r['kind'] == 'text' and r['status'] == 'accepted']
        choices += [('accepted_text', accepted[-1] if accepted else None),
                    ('latest_text', state.get('latest_text'))]
    selected = []
    for role, revision_id in choices:
        if revision_id:
            row = by_id[revision_id]
            relative = project_relative + '/' + row['path']
            if _sha(_git(workspace, 'show', base + ':' + relative)) != row['sha256']:
                raise ValueError('Registered content differs from the base commit: ' + revision_id)
            selected.append({'role': role, **{key: row.get(key) for key in
                             ['id', 'kind', 'status', 'path', 'sha256', 'parent_plan_id', 'based_on']}})
    tree = _git(workspace, 'ls-tree', '-r', '-z', base, '--', project_relative + '/')
    return project_relative, {'registration_files': protected,
                              'project_tree_sha256': _sha(tree), 'selected_versions': selected}


def _package_path(workspace, relative):
    parts = PurePosixPath(relative).parts
    if len(parts) != 2 or parts[0] != 'contributions' or not PACKAGE_ID.fullmatch(parts[1]):
        raise ValueError('Expected contributions/<unique-id>')
    path = scoped_path(workspace, relative)
    if path.is_symlink() or path.parent.is_symlink() or not path.is_dir():
        raise ValueError('Contribution package must be a regular directory')
    return path


def _verify_package(workspace, relative, expected_base=None):
    path = _package_path(workspace, relative)
    manifest_path = _regular(path, 'manifest.json')
    seal = _regular(path, 'manifest.sha256').read_text(encoding='ascii').strip()
    if not re.fullmatch(r'[a-f0-9]{64}', seal) or seal != digest(manifest_path):
        raise ValueError('Contribution manifest checksum mismatch')
    manifest = read_json(manifest_path)
    expected_keys = {'schema_version', 'package_id', 'created_at', 'project_id', 'chapter_id',
                     'project_path', 'base_commit', 'baseline', 'files', 'acceptance'}
    if not isinstance(manifest, dict) or set(manifest) != expected_keys or manifest['schema_version'] != 1:
        raise ValueError('Unsupported contribution manifest schema')
    if manifest['package_id'] != path.name or manifest['acceptance'] != 'candidate_only':
        raise ValueError('A contribution is a candidate only; it cannot grant acceptance')
    if not isinstance(manifest['base_commit'], str) or not COMMIT_ID.fullmatch(manifest['base_commit']):
        raise ValueError('Manifest needs an exact base commit')
    base = _commit(workspace, manifest['base_commit'])
    if expected_base and base != expected_base:
        raise ValueError('Contribution base differs from the reviewer-selected base commit')
    project_relative, baseline = _baseline(workspace, manifest['project_id'], manifest['chapter_id'], base)
    if manifest['project_path'] != project_relative or manifest['baseline'] != baseline:
        raise ValueError('Contribution baseline/selected versions do not match the registered base')
    if not isinstance(manifest['files'], list) or not manifest['files']:
        raise ValueError('A contribution must contain a candidate or review file')
    declared = {'manifest.json', 'manifest.sha256'}
    for row in manifest['files']:
        if not isinstance(row, dict) or set(row) != {'path', 'role', 'sha256', 'bytes'}:
            raise ValueError('Invalid contribution file record')
        relative_file = row['path']
        if not isinstance(relative_file, str):
            raise ValueError('Invalid contribution file path')
        parts = PurePosixPath(relative_file).parts
        if len(parts) != 2 or parts[0] != 'files' or '..' in parts or relative_file in declared:
            raise ValueError('Candidate paths must be unique files/<name> paths without traversal')
        if row['role'] not in {'candidate', 'review'}:
            raise ValueError('Invalid contribution role')
        candidate = _regular(path, relative_file)
        if digest(candidate) != row['sha256'] or candidate.stat().st_size != row['bytes']:
            raise ValueError('Contribution file checksum/size mismatch: ' + relative_file)
        candidate.read_text(encoding='utf-8')
        declared.add(relative_file)
    actual = set()
    for item in path.rglob('*'):
        if item.is_symlink():
            raise ValueError('Symlinks are forbidden in a contribution')
        if item.is_file():
            actual.add(item.relative_to(path).as_posix())
        elif not item.is_dir():
            raise ValueError('Special files are forbidden in a contribution')
    if actual != declared:
        raise ValueError('Undeclared or missing contribution files')
    return manifest, {relative + '/' + item for item in declared}


def guard(workspace, base):
    workspace = _workspace(workspace)
    base = _commit(workspace, base)
    packages, changed_paths = _boundary(workspace, base)
    verified = []
    for relative in sorted(packages):
        manifest, declared = _verify_package(workspace, relative, base)
        if not declared.issubset(changed_paths):
            raise ValueError('Every file of a new package must be included in the proposed changes')
        verified.append(manifest['package_id'])
    return {'ok': True, 'base_commit': base, 'packages': verified,
            'changed_paths': sorted(changed_paths), 'accepted_content_changed': False,
            'scope': 'Local Git boundary and integrity checks; not remote access control or author approval.'}


def verify(workspace, package, base=None):
    workspace = _workspace(workspace)
    expected = _commit(workspace, base) if base else None
    manifest, _ = _verify_package(workspace, package, expected)
    # Editors independently check the whole proposed change set. Merely
    # handing over a good package cannot conceal a modified registration chain.
    guard_result = guard(workspace, manifest['base_commit'])
    return {'ok': True, 'package': package, 'project_id': manifest['project_id'],
            'chapter_id': manifest['chapter_id'], 'base_commit': manifest['base_commit'],
            'files': manifest['files'], 'baseline': manifest['baseline'],
            'guard': guard_result, 'content_registered': False, 'content_accepted': False,
            'next_step': 'The designated editor reviews the candidate and uses writing_workspace.py add-revision. '
                         'Accepted status requires the actual author decision; no merge or registration was performed.'}


def package(workspace, project_id, chapter_id, base, files=(), reviews=(), package_id=None):
    workspace = _workspace(workspace)
    base = _commit(workspace, base)
    guard(workspace, base)
    project_relative, baseline = _baseline(workspace, project_id, chapter_id, base)
    sources = [(Path(source).expanduser(), role) for role, group in
               [('candidate', files), ('review', reviews)] for source in group]
    if not sources:
        raise ValueError('Select at least one --file or --review')
    package_id = package_id or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-') + uuid.uuid4().hex[:12]
    if not PACKAGE_ID.fullmatch(package_id):
        raise ValueError('Invalid unique package ID')
    parent = workspace / 'contributions'
    if parent.is_symlink():
        raise ValueError('The contributions directory cannot be a symlink')
    target = parent / package_id
    if target.exists() or target.is_symlink():
        raise ValueError('Contribution ID already exists; create another immutable package')
    payloads = []
    for index, (source, role) in enumerate(sources, 1):
        if source.is_symlink() or not source.is_file():
            raise ValueError('Candidate sources must be regular UTF-8 files')
        content = source.read_bytes()
        content.decode('utf-8')
        name = str(index).zfill(3) + '-' + source.name
        payloads.append((name, role, content))
    parent.mkdir(exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.contribution-staging-', dir=workspace))
    try:
        (staging / 'files').mkdir()
        rows = []
        for name, role, content in payloads:
            relative = 'files/' + name
            (staging / relative).write_bytes(content)
            rows.append({'path': relative, 'role': role, 'sha256': _sha(content), 'bytes': len(content)})
        manifest = {'schema_version': 1, 'package_id': package_id,
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'project_id': project_id, 'chapter_id': chapter_id,
                    'project_path': project_relative, 'base_commit': base,
                    'baseline': baseline, 'files': rows, 'acceptance': 'candidate_only'}
        data = _json_bytes(manifest)
        (staging / 'manifest.json').write_bytes(data)
        (staging / 'manifest.sha256').write_text(_sha(data) + '\n', encoding='ascii')
        # No global content registry, lifecycle or author decision is mutated.
        # The staging directory is either renamed whole or removed on failure.
        if target.exists():
            raise ValueError('Contribution ID was concurrently created')
        staging.rename(target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {'ok': True, 'package': 'contributions/' + package_id,
            'base_commit': base, 'manifest_sha256': _sha(data),
            'files': rows, 'content_registered': False, 'content_accepted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    commands = parser.add_subparsers(dest='command', required=True)
    command = commands.add_parser('package', help='Create an immutable candidate/review package')
    for name in ['project', 'chapter', 'base']:
        command.add_argument('--' + name, required=True)
    command.add_argument('--file', type=Path, action='append', default=[])
    command.add_argument('--review', type=Path, action='append', default=[])
    command.add_argument('--id')
    command = commands.add_parser('guard', help='Reject contributor changes outside complete new packages')
    command.add_argument('--base', required=True)
    command = commands.add_parser('verify', help='Editor verification; never registers or accepts content')
    command.add_argument('--package', required=True)
    command.add_argument('--base')
    args = parser.parse_args()
    if args.command == 'package':
        result = package(args.workspace, args.project, args.chapter, args.base, args.file, args.review, args.id)
    elif args.command == 'guard':
        result = guard(args.workspace, args.base)
    else:
        result = verify(args.workspace, args.package, args.base)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError, UnicodeError) as exc:
        raise SystemExit('Error: ' + str(exc))
