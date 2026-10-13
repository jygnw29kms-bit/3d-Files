from __future__ import annotations
import json, time
from pathlib import Path
import requests
import export_preview

ROOT = Path(__file__).resolve().parent
TOKEN_FILE = ROOT / '.push-token'
DATA_FILE = ROOT / 'preview' / 'data.json'
URL = 'https://www.dezender.de/3d-druck/ingest.php'


def push_once(timeout=8):
    if not TOKEN_FILE.exists():
        raise RuntimeError('missing local push token')
    export_preview.main()
    payload = json.loads(DATA_FILE.read_text(encoding='utf-8'))
    token = TOKEN_FILE.read_text(encoding='utf-8').strip()
    r = requests.post(URL, json=payload, headers={'X-PRINTBENCH-TOKEN': token, 'User-Agent': 'PRINTBENCH-Collector/1.0'}, timeout=timeout)
    r.raise_for_status()
    return r.json()

if __name__ == '__main__':
    print(push_once())
