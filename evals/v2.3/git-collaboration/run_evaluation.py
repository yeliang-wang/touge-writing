#!/usr/bin/env python3
"""Exercise the real CLI with independent local Git clones and synthetic prose."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PROJECT = 'clock-story'
PROJECT_PATH = 'novels/' + PROJECT


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def evaluate(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    transcript, cases = [], []
    with tempfile.TemporaryDirectory(prefix='touge-v23-git-eval-') as temporary:
        arena = Path(temporary).resolve()
        editor, contributor, recovery = (arena / n for n in ('editor', 'contributor', 'recovery'))
        bare, fixtures = arena / 'shared.git', arena / 'fixtures'
        fixtures.mkdir()

        def clean(value):
            return str(value).replace(str(arena), '<EVAL>').replace(str(ROOT), '<PUBLIC>')

        def command(args, cwd=None, success=True):
            proc = subprocess.run(list(map(str, args)), cwd=cwd or arena, capture_output=True, text=True)
            transcript.append({'argv': [clean(a) for a in args], 'cwd': clean(cwd or arena),
                               'exit_code': proc.returncode, 'stdout': clean(proc.stdout),
                               'stderr': clean(proc.stderr)})
            if (proc.returncode == 0) != success:
                raise AssertionError('Unexpected command outcome: ' + clean(args) + '\n' + clean(proc.stdout + proc.stderr))
            return proc.stdout

        def git(workspace, *args, success=True):
            return command(['git', '-C', workspace, *args], success=success)

        def cli(script, workspace, *args, success=True):
            return command([sys.executable, ROOT / 'scripts' / script, '--workspace', workspace, *args], success=success)

        def writing(workspace, action, *args, success=True):
            return cli('writing_workspace.py', workspace, action, '--project', PROJECT, *args, success=success)

        def run(workspace, action, *args, success=True):
            return cli('writing_run.py', workspace, '--project', PROJECT, action, *args, success=success)

        def collaboration(workspace, action, *args, success=True):
            return cli('git_collaboration.py', workspace, action, *args, success=success)

        def fixture(name, body):
            path = fixtures / name
            path.write_text(body, encoding='utf-8')
            return path

        def request(name):
            path = fixtures / (name + '.json')
            save(path, {'schema_version': 1, 'id': name, 'task': 'Synthetic clock-story evaluation',
                        'authorization_refs': ['Synthetic test protocol; not real author approval'],
                        'target': 'ch01', 'mode': 'revise', 'stage': 'revise',
                        'fiction_policy': {'mode': 'fiction', 'scope': 'Synthetic clock-story only',
                                           'authorization_ref': 'Synthetic evaluation fixture'},
                        'capabilities': ['editorial-review@1.0.0'], 'inputs': [],
                        'open_issues': [], 'model': {'id': 'synthetic-cli-fixture', 'configuration': 'no LLM call'}})
            return path

        def official_snapshot(workspace):
            project = workspace / PROJECT_PATH
            return {p.relative_to(project).as_posix(): sha(p) for p in project.rglob('*')
                    if p.is_file() and p.name != '.writing.lock'}

        def accepted_state(workspace):
            data = json.loads(writing(workspace, 'resume', '--chapter', 'ch01'))
            return data['state']

        def checkpoint(ident, detail):
            cases.append({'id': ident, 'status': 'passed', 'observations': detail})

        command(['git', 'init', '--bare', '--initial-branch=main', bare])
        command(['git', 'clone', bare, editor])
        for key, value in [('user.name', 'Synthetic Editor'), ('user.email', 'editor@example.invalid')]:
            git(editor, 'config', key, value)
        (editor / '.gitignore').write_text('.writing.lock\n**/.writing.lock\n.DS_Store\n', encoding='utf-8')
        cli('writing_workspace.py', editor, 'init', '--id', PROJECT, '--title', '合成修钟小说', '--type', 'novel')
        chapter_path = fixtures / 'chapters.json'
        save(chapter_path, [{'id': 'ch01', 'title': '合成第一章'}])
        writing(editor, 'set-chapters', '--file', chapter_path)
        base_text = fixture('baseline.md', '合成原稿：两人约定周五检查旧钟。他们先停下钟摆，再取出卡住的齿轮。\n')
        decision = fixture('baseline-decision.md', 'SYNTHETIC FIXTURE ONLY. The fictional authors approve the synthetic initial plan and text.\n')
        for ident, kind, extra in [
            ('book-1', 'book_plan', []),
            ('plan-1', 'chapter_plan', ['--chapter', 'ch01', '--parent-plan', 'book-1']),
            ('text-1', 'text', ['--chapter', 'ch01', '--parent-plan', 'plan-1']),
        ]:
            writing(editor, 'add-revision', '--source', base_text, '--id', ident, '--kind', kind,
                    '--version', '1', '--status', 'accepted', '--decision-file', decision, *extra)
        run(editor, 'start', '--request', request('initial-run'))
        git(editor, 'add', '.')
        git(editor, 'commit', '-m', 'Synthetic accepted baseline')
        base = git(editor, 'rev-parse', 'HEAD').strip()
        git(editor, 'push', '-u', 'origin', 'main')
        command(['git', 'clone', bare, contributor])
        for key, value in [('user.name', 'Synthetic Contributor'), ('user.email', 'contributor@example.invalid')]:
            git(contributor, 'config', key, value)
        assert official_snapshot(editor) == official_snapshot(contributor)
        assert accepted_state(contributor)['chapters'][0]['accepted_text'] == 'text-1'
        checkpoint('initial-clone', {'base_commit': base, 'registered_content_and_lifecycle_identical': True,
                                     'accepted_text': 'text-1'})

        git(contributor, 'switch', '-c', 'candidate/clock-revision')
        candidate = fixture('candidate.md', '合成候选稿：旧钟停在三点。他先扶稳钟摆，她才从齿轮间抽出断裂的铜丝。两人约好周五再来检查。\n')
        review = fixture('review.md', '合成审阅：先后动作现在清楚；保留周五复查，避免把一次启动写成永久修复。\n')
        collaboration(contributor, 'package', '--project', PROJECT, '--chapter', 'ch01', '--base', base,
                      '--file', candidate, '--review', review, '--id', 'clock-candidate')
        package_rel = 'contributions/clock-candidate'
        package = contributor / package_rel
        assert package.is_dir(), 'Expected documented contributions package'
        collaboration(contributor, 'guard', '--base', base)
        git(contributor, 'add', package_rel)
        git(contributor, 'commit', '-m', 'Synthetic candidate and review')
        candidate_commit = git(contributor, 'rev-parse', 'HEAD').strip()
        collaboration(contributor, 'guard', '--base', base)
        git(contributor, 'push', '-u', 'origin', 'candidate/clock-revision')
        git(editor, 'fetch', 'origin', 'candidate/clock-revision')
        git(editor, 'switch', '-c', 'review/clock-candidate', 'origin/candidate/clock-revision')
        collaboration(editor, 'verify', '--package', package_rel, '--base', base)
        package_files = [p for p in (editor / package_rel).rglob('*') if p.is_file()]
        member = next(p for p in package_files if sha(p) == sha(candidate))
        originals = official_snapshot(editor)
        before = member.read_bytes()
        member.write_bytes(before + b'\nSYNTHETIC TAMPERING\n')
        collaboration(editor, 'verify', '--package', package_rel, '--base', base, success=False)
        assert official_snapshot(editor) == originals
        member.write_bytes(before)
        collaboration(editor, 'verify', '--package', package_rel, '--base', base)
        checkpoint('package-tampering', {'altered_member_detected': True, 'official_files_unchanged': True})

        git(editor, 'switch', 'main')
        git(editor, 'merge', '--ff-only', 'review/clock-candidate')
        accepted_decision = editor / PROJECT_PATH / 'decisions/integrated.md'
        accepted_decision.parent.mkdir(parents=True, exist_ok=True)
        accepted_decision.write_text('SYNTHETIC FIXTURE ONLY: the fictional authors accept this clock candidate for ch01, version 2.\n', encoding='utf-8')
        run(editor, 'start', '--request', request('editor-integration'))
        run(editor, 'artifact', '--run', 'editor-integration', '--operation-id', 'attach-candidate',
            '--source', member, '--id', 'integrated-text', '--role', 'text')
        revision = fixtures / 'integrated-revision.json'
        save(revision, {'revision_id': 'text-2', 'kind': 'text', 'version': '2', 'status': 'accepted',
                        'chapter_id': 'ch01', 'parent_plan_id': 'plan-1', 'based_on': 'text-1',
                        'decision_file': 'decisions/integrated.md'})
        run(editor, 'register', '--run', 'editor-integration', '--operation-id', 'register-accepted',
            '--artifact-id', 'integrated-text', '--revision', revision)
        writing(editor, 'validate')
        run(editor, 'verify', '--run', 'editor-integration')
        assert accepted_state(editor)['chapters'][0]['accepted_text'] == 'text-2'
        git(editor, 'add', '.')
        git(editor, 'commit', '-m', 'Synthetic editor acceptance and sequential registration')
        integrated_commit = git(editor, 'rev-parse', 'HEAD').strip()
        git(editor, 'push', 'origin', 'main')
        checkpoint('candidate-integration', {'candidate_commit': candidate_commit,
                    'integrated_commit': integrated_commit, 'candidate_sha256': sha(candidate),
                    'review_sha256': sha(review), 'accepted_text': 'text-2',
                    'verified_on_review_branch_before_main_merge': True,
                    'author_decision_is_synthetic': True, 'registry_and_lifecycle_verified': True})
        before_stale = official_snapshot(editor)
        collaboration(editor, 'verify', '--package', package_rel, '--base', base, success=False)
        assert official_snapshot(editor) == before_stale
        checkpoint('stale-baseline', {'old_base_commit': base, 'new_commit': integrated_commit,
                                    'rejected_without_official_changes': True})

        git(contributor, 'switch', '-c', 'unsafe/local-run', candidate_commit)
        collaboration(contributor, 'verify', '--package', package_rel, '--base', base)
        run(contributor, 'start', '--request', request('contributor-local-run'))
        writing(contributor, 'add-revision', '--source', candidate, '--id', 'local-text-2', '--kind', 'text',
                '--version', '2-local', '--status', 'draft', '--chapter', 'ch01', '--parent-plan', 'plan-1', '--based-on', 'text-1')
        collaboration(contributor, 'guard', '--base', base, success=False)
        git(contributor, 'add', '.')
        collaboration(contributor, 'guard', '--base', base, success=False)
        git(contributor, 'commit', '-m', 'Synthetic unsafe local official-state edits')
        collaboration(contributor, 'guard', '--base', base, success=False)
        collaboration(contributor, 'verify', '--package', package_rel, '--base', base, success=False)
        assert official_snapshot(editor) == before_stale
        competing = 'lifecycle/events/00000002.json'
        assert (editor / PROJECT_PATH / competing).is_file()
        assert (contributor / PROJECT_PATH / competing).is_file()
        assert sha(editor / PROJECT_PATH / competing) != sha(contributor / PROJECT_PATH / competing)
        checkpoint('concurrent-official-write', {'real_writing_commands_executed': True,
                    'unstaged_staged_and_committed_changes_rejected': True,
                    'valid_package_cannot_conceal_official_changes': True,
                    'same_event_sequence_has_different_hashes': True,
                    'editor_official_files_unchanged': True,
                    'scope': 'submission guard, not a local-command authorization system'})

        command(['git', 'clone', bare, recovery])
        writing(recovery, 'validate')
        run(recovery, 'verify', '--run', 'editor-integration')
        recovered = accepted_state(recovery)
        assert recovered == accepted_state(editor)
        assert official_snapshot(recovery) == official_snapshot(editor)
        restored = recovery / PROJECT_PATH / '版本记录/content/text-2.md'
        assert sha(restored) == sha(candidate)
        checkpoint('recovery-clone', {'restored_commit': git(recovery, 'rev-parse', 'HEAD').strip(),
                    'accepted_text': 'text-2', 'accepted_sha256': sha(restored),
                    'all_official_file_hashes_match': True, 'state_and_ancestry_match': True})
        save(output / 'official-inventory.json', official_snapshot(recovery))
        save(output / 'accepted-state.json', recovered)
    save(output / 'transcript.json', transcript)
    expected = {c['id'] for c in json.loads((HERE / 'protocol.json').read_text())['cases']}
    assert {c['id'] for c in cases} == expected
    evaluated = ['scripts/git_collaboration.py', 'scripts/writing_workspace.py',
                 'scripts/writing_run.py', 'scripts/workspace_lib.py',
                 'evals/v2.3/git-collaboration/protocol.json',
                 'evals/v2.3/git-collaboration/run_evaluation.py']
    report = {'schema_version': 1, 'source': 'independent_agent_forward_test',
              'all_in_scope_passed': True, 'same_host_local_git_only': True,
              'live_github_accounts_tested': False, 'live_cloud_tested': False,
              'real_author_approval_claimed': False, 'cases': cases,
              'evaluated_files': [{'path': p, 'sha256': sha(ROOT / p)} for p in evaluated],
              'artifacts': [{'path': name, 'sha256': sha(output / name)}
                            for name in ['transcript.json', 'official-inventory.json', 'accepted-state.json']]}
    save(output / 'result.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'evidence')
    args = parser.parse_args()
    report = evaluate(args.out)
    print(json.dumps({'all_in_scope_passed': report['all_in_scope_passed'], 'cases': len(report['cases'])}))
