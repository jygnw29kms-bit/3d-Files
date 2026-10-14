from __future__ import annotations
import os, posixpath, shlex, subprocess
from pathlib import Path
import quiet_process

SSH_HOST = '87.106.119.187'
SSH_USER = 'root'
SSH_PORT = 22
SSH_KEY = Path.home() / '.ssh' / 'printbench_server'
REMOTE_ROOT = '/var/www/vhosts/dezender.de/httpdocs/3d-druck/runtime'


def available() -> bool:
    return SSH_KEY.is_file()


def _ssh_cmd(remote_command: str) -> list[str]:
    return [
        'ssh', '-i', str(SSH_KEY), '-p', str(SSH_PORT),
        '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=accept-new',
        '-o', 'ConnectTimeout=5', f'{SSH_USER}@{SSH_HOST}', remote_command,
    ]


def exec_remote(command: str, timeout: int = 15) -> None:
    r = subprocess.run(_ssh_cmd(command), stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, timeout=timeout, **quiet_process.options())
    if r.returncode:
        raise RuntimeError(f'ssh exit {r.returncode}')


def put_file_atomic(local_path: Path, relative_path: str, timeout: int = 60, mode: str = '0644') -> None:
    local_path = Path(local_path)
    if not available():
        raise RuntimeError('server ssh key unavailable')
    remote = posixpath.join(REMOTE_ROOT, relative_path.replace('\\', '/').lstrip('/'))
    parent = posixpath.dirname(remote)
    tmp = remote + f'.tmp-{os.getpid()}'
    q = shlex.quote
    remote_cmd = f'umask 022; mkdir -p {q(parent)}; cat > {q(tmp)} && mv -f {q(tmp)} {q(remote)} && chmod {mode} {q(remote)}'
    with local_path.open('rb') as src:
        r = subprocess.run(_ssh_cmd(remote_cmd), stdin=src, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE, timeout=timeout, **quiet_process.options())
    if r.returncode:
        raise RuntimeError(f'ssh upload exit {r.returncode}')


def put_bytes_atomic(data: bytes, relative_path: str, timeout: int = 30, mode: str = '0644') -> None:
    if not available():
        raise RuntimeError('server ssh key unavailable')
    remote = posixpath.join(REMOTE_ROOT, relative_path.replace('\\', '/').lstrip('/'))
    parent = posixpath.dirname(remote)
    tmp = remote + f'.tmp-{os.getpid()}'
    q = shlex.quote
    remote_cmd = f'umask 022; mkdir -p {q(parent)}; cat > {q(tmp)} && mv -f {q(tmp)} {q(remote)} && chmod {mode} {q(remote)}'
    r = subprocess.run(_ssh_cmd(remote_cmd), input=data, stdout=subprocess.DEVNULL,
                       stderr=subprocess.PIPE, timeout=timeout, **quiet_process.options())
    if r.returncode:
        raise RuntimeError(f'ssh upload exit {r.returncode}')
