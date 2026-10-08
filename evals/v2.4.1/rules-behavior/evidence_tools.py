"""Local evidence helpers; does not generate prose or judge literary quality."""
import hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
EVAL = Path(__file__).resolve().parent
PUBLIC = EVAL.parents[2]
WORKSPACE = EVAL / 'workspace'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def clean(text):
    return str(text).replace(str(EVAL), '<EVAL>').replace(str(PUBLIC), '<PUBLIC>')

def write(path, content):
    path = Path(path)
    if not path.is_relative_to(EVAL):
        raise ValueError('Evaluation writes are confined to this evidence directory')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')

def save(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def receipt(kind, **data):
    row = {'recorded_at': datetime.now(timezone.utc).isoformat(), 'kind': kind, **data}
    with (EVAL / 'transcript.jsonl').open('a', encoding='utf-8') as f:
        f.write(clean(json.dumps(row, ensure_ascii=False)) + '\n')

def cli(script, args, output=None):
    command = [sys.executable, str(PUBLIC / 'scripts' / script), *map(str, args)]
    p = subprocess.run(command, cwd=PUBLIC, text=True, capture_output=True)
    receipt('actual_cli', argv=command, exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)
    if output:
        write(EVAL / output, clean(p.stdout))
    if p.returncode:
        raise RuntimeError(clean(p.stderr or p.stdout))
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return p.stdout

def ws(*args, output=None):
    return cli('writing_workspace.py', ['--workspace', WORKSPACE, *args], output)

def rules(project, *args, output=None):
    return cli('writing_rules.py', ['--workspace', WORKSPACE, '--project', project, *args], output)

def run(project, *args, output=None):
    return cli('writing_run.py', ['--workspace', WORKSPACE, '--project', project, *args], output)

def snapshot(paths, dest):
    rows = [{'path': p.relative_to(EVAL).as_posix(), 'sha256': sha(p)} for p in paths]
    save(EVAL / dest, rows)
    return rows
