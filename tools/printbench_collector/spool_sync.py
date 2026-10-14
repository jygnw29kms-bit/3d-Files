from __future__ import annotations
import json, sqlite3
from pathlib import Path
from typing import Any
import requests
import collector
import ams_control

ROOT=Path(__file__).resolve().parent
TOKEN_FILE=ROOT/'.spool-admin-token'
BASE='https://www.dezender.de/3d-druck/spool-api.php'
ZERO={'','0','0000000000000000','00000000000000000000000000000000'}

def ensure_schema(db:sqlite3.Connection)->None:
    db.executescript('''
    CREATE TABLE IF NOT EXISTS spool_inventory(
      spool_id TEXT PRIMARY KEY,
      display_name TEXT,
      vendor TEXT,
      material TEXT,
      color_name TEXT,
      color_hex TEXT,
      filament_profile TEXT,
      remaining_g REAL,
      initial_net_g REAL,
      spool_tare_g REAL,
      purchase_price_eur REAL,
      nozzle_temp_min REAL,
      nozzle_temp_max REAL,
      dry_temp_c REAL,
      dry_duration_h REAL,
      last_dried_at TEXT,
      status TEXT,
      ams_id INTEGER,
      ams_slot INTEGER,
      nfc_uid TEXT,
      nfc_tag_type TEXT,
      server_updated_at TEXT,
      synced_at TEXT NOT NULL,
      raw_json TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_spool_inventory_uid ON spool_inventory(nfc_uid);
    CREATE TABLE IF NOT EXISTS ams_spool_matches(
      id INTEGER PRIMARY KEY,
      ts TEXT NOT NULL,
      ams_id TEXT,
      slot_id TEXT,
      source_field TEXT NOT NULL,
      observed_uid TEXT NOT NULL,
      spool_id TEXT,
      matched INTEGER NOT NULL,
      UNIQUE(ts,ams_id,slot_id,source_field,observed_uid)
    );
    CREATE TABLE IF NOT EXISTS ams_action_proposals(
      id INTEGER PRIMARY KEY,
      created_at TEXT NOT NULL,
      ams_id TEXT NOT NULL,
      slot_id TEXT NOT NULL,
      spool_id TEXT NOT NULL,
      status TEXT NOT NULL,
      reason TEXT,
      payload_json TEXT,
      UNIQUE(ams_id,slot_id,spool_id,status)
    );
    CREATE INDEX IF NOT EXISTS idx_ams_spool_matches_slot ON ams_spool_matches(ams_id,slot_id,id);
    ''')
    db.commit()

def _token()->str:
    if not TOKEN_FILE.is_file():raise RuntimeError('missing local spool admin token')
    token=TOKEN_FILE.read_text(encoding='utf-8').strip()
    if not token:raise RuntimeError('empty local spool admin token')
    return token

def _headers()->dict:
    return {'X-PRINTBENCH-ADMIN':_token(),'User-Agent':'PRINTBENCH-SpoolSync/1.0'}

def _norm_uid(v:Any)->str:
    s=''.join(c for c in str(v or '').upper() if c in '0123456789ABCDEF')
    return ':'.join(s[i:i+2] for i in range(0,len(s),2)) if s else ''

def sync(db:sqlite3.Connection,timeout=10)->dict:
    ensure_schema(db)
    public=requests.get(BASE,params={'action':'list'},headers={'User-Agent':'PRINTBENCH-SpoolSync/1.0'},timeout=timeout)
    public.raise_for_status(); listing=public.json(); ids=[str(x.get('id')) for x in listing.get('spools',[]) if x.get('id')]
    seen=[]; now=collector.now_iso()
    for sid in ids:
        r=requests.get(BASE,params={'action':'detail','id':sid},headers=_headers(),timeout=timeout);r.raise_for_status(); detail=r.json().get('spool') or {}
        uid=_norm_uid(detail.get('nfc_uid'))
        vals=(sid,detail.get('display_name'),detail.get('vendor'),detail.get('material'),detail.get('color_name'),detail.get('color_hex'),detail.get('filament_profile'),detail.get('remaining_g'),detail.get('initial_net_g'),detail.get('spool_tare_g'),detail.get('purchase_price_eur'),detail.get('nozzle_temp_min'),detail.get('nozzle_temp_max'),detail.get('dry_temp_c'),detail.get('dry_duration_h'),detail.get('last_dried_at'),detail.get('status'),detail.get('ams_id'),detail.get('ams_slot'),uid or None,detail.get('nfc_tag_type'),detail.get('updated_at'),now,json.dumps(detail,ensure_ascii=False,separators=(',',':')))
        db.execute('''INSERT INTO spool_inventory(spool_id,display_name,vendor,material,color_name,color_hex,filament_profile,remaining_g,initial_net_g,spool_tare_g,purchase_price_eur,nozzle_temp_min,nozzle_temp_max,dry_temp_c,dry_duration_h,last_dried_at,status,ams_id,ams_slot,nfc_uid,nfc_tag_type,server_updated_at,synced_at,raw_json)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(spool_id) DO UPDATE SET display_name=excluded.display_name,vendor=excluded.vendor,material=excluded.material,color_name=excluded.color_name,color_hex=excluded.color_hex,filament_profile=excluded.filament_profile,remaining_g=excluded.remaining_g,initial_net_g=excluded.initial_net_g,spool_tare_g=excluded.spool_tare_g,purchase_price_eur=excluded.purchase_price_eur,nozzle_temp_min=excluded.nozzle_temp_min,nozzle_temp_max=excluded.nozzle_temp_max,dry_temp_c=excluded.dry_temp_c,dry_duration_h=excluded.dry_duration_h,last_dried_at=excluded.last_dried_at,status=excluded.status,ams_id=excluded.ams_id,ams_slot=excluded.ams_slot,nfc_uid=excluded.nfc_uid,nfc_tag_type=excluded.nfc_tag_type,server_updated_at=excluded.server_updated_at,synced_at=excluded.synced_at,raw_json=excluded.raw_json''',vals)
        seen.append(sid)
    if seen:
        q=','.join('?' for _ in seen);db.execute(f'DELETE FROM spool_inventory WHERE spool_id NOT IN ({q})',seen)
    else:db.execute('DELETE FROM spool_inventory')
    db.commit();return {'count':len(seen),'nfc_bound':db.execute("SELECT COUNT(*) FROM spool_inventory WHERE nfc_uid IS NOT NULL AND nfc_uid<>''").fetchone()[0],'synced_at':now}

def match_uid(db:sqlite3.Connection,uid:Any):
    ensure_schema(db); n=_norm_uid(uid)
    if not n or n.replace(':','') in ZERO:return None
    db.row_factory=sqlite3.Row
    row=db.execute('SELECT * FROM spool_inventory WHERE UPPER(REPLACE(nfc_uid,\':\',\'\'))=? LIMIT 1',(n.replace(':',''),)).fetchone()
    return dict(row) if row else None


def build_proposal(match:dict,ams_id,slot_id):
    missing=[]
    material=str(match.get('material') or '').strip().upper()
    color=match.get('color_hex')
    lo=match.get('nozzle_temp_min'); hi=match.get('nozzle_temp_max')
    if not material:missing.append('material')
    if not color:missing.append('color')
    if lo is None:missing.append('nozzle_temp_min')
    if hi is None:missing.append('nozzle_temp_max')
    if missing:return {'status':'blocked','reason':'missing:'+','.join(missing),'payload':None}
    try:
        payload=ams_control.build_filament_setting(ams_id,slot_id,material,color,lo,hi)
        return {'status':'ready','reason':None,'payload':payload}
    except Exception as e:
        return {'status':'blocked','reason':str(e),'payload':None}


def store_proposal(db:sqlite3.Connection,ts:str,ams_id,slot_id,match:dict):
    proposal=build_proposal(match,ams_id,slot_id)
    db.execute("DELETE FROM ams_action_proposals WHERE ams_id=? AND slot_id=? AND status IN ('ready','blocked')",(str(ams_id),str(slot_id)))
    db.execute('INSERT INTO ams_action_proposals(created_at,ams_id,slot_id,spool_id,status,reason,payload_json) VALUES(?,?,?,?,?,?,?)',(
        ts,str(ams_id),str(slot_id),str(match.get('spool_id')),proposal['status'],proposal['reason'],json.dumps(proposal['payload'],ensure_ascii=False,separators=(',',':')) if proposal['payload'] else None))
    return proposal

def observe_ams(db:sqlite3.Connection,raw:dict,ts:str)->list[dict]:
    ensure_schema(db);p=raw.get('print') if isinstance(raw,dict) else None; top=p.get('ams') if isinstance(p,dict) else None
    if not isinstance(top,dict):return []
    found=[]
    for unit in top.get('ams') or []:
        if not isinstance(unit,dict):continue
        aid=str(unit.get('id',''))
        for tray in unit.get('tray') or []:
            if not isinstance(tray,dict):continue
            slot=str(tray.get('id',''))
            for field in ('tag_uid','tray_uuid'):
                raw_uid=str(tray.get(field) or '')
                compact=''.join(c for c in raw_uid.upper() if c in '0123456789ABCDEF')
                if not compact or compact in ZERO:continue
                uid=_norm_uid(raw_uid);match=match_uid(db,uid);spool_id=match.get('spool_id') if match else None
                proposal=store_proposal(db,ts,aid,slot,match) if match else None
                last=db.execute('SELECT observed_uid,spool_id,matched FROM ams_spool_matches WHERE ams_id=? AND slot_id=? AND source_field=? ORDER BY id DESC LIMIT 1',(aid,slot,field)).fetchone()
                state=(uid,spool_id,1 if match else 0)
                if last and tuple(last)==state:continue
                db.execute('INSERT INTO ams_spool_matches(ts,ams_id,slot_id,source_field,observed_uid,spool_id,matched) VALUES(?,?,?,?,?,?,?)',(ts,aid,slot,field,uid,spool_id,1 if match else 0))
                db.execute('INSERT INTO events(ts,kind,payload) VALUES(?,?,?)',(ts,'ams_spool_match' if match else 'ams_uid_unmatched',json.dumps({'ams_id':aid,'slot_id':slot,'source_field':field,'spool_id':spool_id},ensure_ascii=False)))
                found.append({'ams_id':aid,'slot_id':slot,'source_field':field,'spool_id':spool_id,'matched':bool(match),'proposal':proposal})
    if found:db.commit()
    return found