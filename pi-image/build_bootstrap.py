from __future__ import annotations
import hashlib, re, subprocess, tarfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'tools'/'printbench_collector'
ARCHIVE=HERE/'printbench-collector.tar.gz'
FIRSTBOOT=HERE/'printbench-firstboot.sh'

EXCLUDE_NAMES={'printbench.db','.spool-admin-token','.push-token'}
EXCLUDE_PARTS={'__pycache__','runtime','media','preview'}


def include(path:Path)->bool:
    rel=path.relative_to(SOURCE)
    if path.name in EXCLUDE_NAMES or any(part in EXCLUDE_PARTS for part in rel.parts):return False
    if path.suffix in {'.pyc','.log'}:return False
    return True


def git_head()->str:
    return subprocess.check_output(['git','-C',str(ROOT),'rev-parse','--short=12','HEAD'],text=True).strip()


def assert_clean()->None:
    status=subprocess.check_output(['git','-C',str(ROOT),'status','--porcelain','--untracked-files=all'],text=True)
    if status.strip():
        raise SystemExit('refusing bootstrap build from dirty worktree; commit or stash changes first')


def main()->None:
    assert_clean()
    with tarfile.open(ARCHIVE,'w:gz',compresslevel=9) as tf:
        for path in sorted(SOURCE.rglob('*')):
            if path.is_file() and include(path):
                tf.add(path,arcname=(Path('tools/printbench_collector')/path.relative_to(SOURCE)).as_posix())
    sha=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest().upper();commit=git_head()
    text=FIRSTBOOT.read_text(encoding='utf-8')
    text,n1=re.subn(r'^COLLECTOR_COMMIT="[^"]*"',f'COLLECTOR_COMMIT="{commit}"',text,count=1,flags=re.M)
    text,n2=re.subn(r'^COLLECTOR_SHA="[A-Fa-f0-9]+"',f'COLLECTOR_SHA="{sha}"',text,count=1,flags=re.M)
    if n1!=1 or n2!=1:raise SystemExit('could not update firstboot bootstrap metadata')
    FIRSTBOOT.write_text(text,encoding='utf-8',newline='\n')
    print(f'archive={ARCHIVE.name}')
    print(f'bytes={ARCHIVE.stat().st_size}')
    print(f'sha256={sha}')
    print(f'collector_commit={commit}')


if __name__=='__main__':main()
