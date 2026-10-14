from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import requests
import export_preview, server_transport, session_export
ROOT=Path(__file__).resolve().parent
TOKEN_FILE=ROOT/'.push-token'; DATA_FILE=ROOT/'preview'/'data.json'; URL='https://www.dezender.de/3d-druck/ingest.php'
def _ssh_push(payload):
    p=dict(payload); p['received_at']=datetime.now(timezone.utc).isoformat(); data=json.dumps(p,ensure_ascii=False,separators=(',',':')).encode('utf-8'); server_transport.put_bytes_atomic(data,'live.json',timeout=20); return {'ok':True,'received_at':p['received_at'],'transport':'ssh'}
def _https_push(payload,timeout=8):
    if not TOKEN_FILE.exists(): raise RuntimeError('missing local push token')
    token=TOKEN_FILE.read_text(encoding='utf-8').strip(); r=requests.post(URL,json=payload,headers={'X-PRINTBENCH-TOKEN':token,'User-Agent':'PRINTBENCH-Collector/1.2'},timeout=timeout); r.raise_for_status(); out=r.json(); out['transport']='https'; return out
def push_once(timeout=8):
    export_preview.main(); payload=json.loads(DATA_FILE.read_text(encoding='utf-8'))
    payload.update(session_export.snapshot())
    try:
        return _https_push(payload,timeout)
    except Exception as he:
        if server_transport.available():
            try:return _ssh_push(payload)
            except Exception as se: raise RuntimeError(f'https={he}; ssh={se}')
        raise
if __name__=='__main__': print(push_once())
