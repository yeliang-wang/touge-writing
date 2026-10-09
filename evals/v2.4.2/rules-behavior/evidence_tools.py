"""Capture actual synthetic evaluation operations; no prose grading automation."""
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
EVAL=Path(__file__).resolve().parent
PUBLIC=EVAL.parents[2]
WORKSPACE=EVAL/'workspace'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(s):return str(s).replace(str(EVAL),'<EVAL>').replace(str(PUBLIC),'<PUBLIC>')
def write(p,s):
    p=Path(p)
    if not p.is_relative_to(EVAL):raise ValueError('Evaluation writes only')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def save(p,x):write(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def log(kind,**data):
    with (EVAL/'transcript.jsonl').open('a') as f:f.write(clean(json.dumps({'time':datetime.now(timezone.utc).isoformat(),'kind':kind,**data},ensure_ascii=False))+'\n')
def cli(script,args,out=None):
    argv=[sys.executable,str(PUBLIC/'scripts'/script),*map(str,args)]
    result=subprocess.run(argv,cwd=PUBLIC,capture_output=True,text=True)
    log('actual_cli',argv=argv,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr)
    if out:write(EVAL/out,clean(result.stdout))
    if result.returncode:raise RuntimeError(clean(result.stderr))
    return json.loads(result.stdout)
def ws(*args,out=None):return cli('writing_workspace.py',['--workspace',WORKSPACE,*args],out)
def run(pid,*args,out=None):return cli('writing_run.py',['--workspace',WORKSPACE,'--project',pid,*args],out)
def rules(pid,*args,out=None):return cli('writing_rules.py',['--workspace',WORKSPACE,'--project',pid,*args],out)
def snapshot(paths,out):save(EVAL/out,[{'path':p.relative_to(EVAL).as_posix(),'sha256':sha(p)} for p in paths])
