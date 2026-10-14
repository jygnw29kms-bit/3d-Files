from __future__ import annotations
import hashlib, json, sqlite3
from typing import Any

ZERO_UIDS={'','0','0000000000000000','00000000000000000000000000000000'}


def ensure_schema(db: sqlite3.Connection) -> None:
    db.executescript('''
    CREATE TABLE IF NOT EXISTS ams_rfid_observations(
      id INTEGER PRIMARY KEY,
      ts TEXT NOT NULL,
      ams_id TEXT,
      slot_id TEXT,
      tray_present INTEGER,
      reading INTEGER,
      read_done INTEGER,
      is_bambu INTEGER,
      rfid_status TEXT,
      tray_state TEXT,
      tag_uid TEXT,
      tray_uuid TEXT,
      tray_info_idx TEXT,
      tray_type TEXT,
      tray_color TEXT,
      snapshot_hash TEXT NOT NULL,
      raw_ams_json TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_ams_rfid_obs_ts ON ams_rfid_observations(ts);
    CREATE INDEX IF NOT EXISTS idx_ams_rfid_obs_slot ON ams_rfid_observations(ams_id,slot_id,id);
    ''')
    db.commit()


def _bit(value: Any, slot: int) -> int:
    try: return 1 if (int(value) & (1 << slot)) else 0
    except Exception: return 0


def _clean(value: Any) -> str | None:
    if value is None: return None
    return str(value)


def _snapshot(top: dict, unit: dict, tray: dict) -> dict:
    slot=int(tray.get('id',0) or 0)
    return {
        'ams_id': _clean(unit.get('id')),
        'slot_id': _clean(tray.get('id')),
        'tray_present': _bit(top.get('tray_exist_bits'),slot),
        'reading': _bit(top.get('tray_reading_bits'),slot),
        'read_done': _bit(top.get('tray_read_done_bits'),slot),
        'is_bambu': _bit(top.get('tray_is_bbl_bits'),slot),
        'rfid_status': _clean(top.get('ams_rfid_status')),
        'tray_state': _clean(tray.get('state')),
        'tag_uid': _clean(tray.get('tag_uid')),
        'tray_uuid': _clean(tray.get('tray_uuid')),
        'tray_info_idx': _clean(tray.get('tray_info_idx')),
        'tray_type': _clean(tray.get('tray_type')),
        'tray_color': _clean(tray.get('tray_color')),
    }


def observe(db: sqlite3.Connection, raw: dict, ts: str) -> int:
    p=raw.get('print') if isinstance(raw,dict) else None
    top=p.get('ams') if isinstance(p,dict) else None
    if not isinstance(top,dict): return 0
    units=top.get('ams') or []
    if not isinstance(units,list): return 0
    added=0
    for unit in units:
        if not isinstance(unit,dict): continue
        trays=unit.get('tray') or []
        if not isinstance(trays,list): continue
        for tray in trays:
            if not isinstance(tray,dict): continue
            snap=_snapshot(top,unit,tray)
            key=json.dumps(snap,sort_keys=True,separators=(',',':'),ensure_ascii=False)
            digest=hashlib.sha256(key.encode('utf-8')).hexdigest()
            last=db.execute('SELECT snapshot_hash FROM ams_rfid_observations WHERE ams_id IS ? AND slot_id IS ? ORDER BY id DESC LIMIT 1',(snap['ams_id'],snap['slot_id'])).fetchone()
            if last and last[0]==digest: continue
            db.execute('''INSERT INTO ams_rfid_observations(
                ts,ams_id,slot_id,tray_present,reading,read_done,is_bambu,rfid_status,tray_state,
                tag_uid,tray_uuid,tray_info_idx,tray_type,tray_color,snapshot_hash,raw_ams_json
              ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
                ts,snap['ams_id'],snap['slot_id'],snap['tray_present'],snap['reading'],snap['read_done'],snap['is_bambu'],
                snap['rfid_status'],snap['tray_state'],snap['tag_uid'],snap['tray_uuid'],snap['tray_info_idx'],snap['tray_type'],
                snap['tray_color'],digest,json.dumps(top,ensure_ascii=False,separators=(',',':'))))
            added+=1
    if added: db.commit()
    return added


def recent(db: sqlite3.Connection, limit: int=40) -> list[dict]:
    db.row_factory=sqlite3.Row
    rows=db.execute('''SELECT ts,ams_id,slot_id,tray_present,reading,read_done,is_bambu,rfid_status,tray_state,
        tag_uid,tray_uuid,tray_info_idx,tray_type,tray_color
        FROM ams_rfid_observations ORDER BY id DESC LIMIT ?''',(max(1,min(500,limit)),)).fetchall()
    out=[]
    for r in rows:
        d=dict(r)
        d['tag_uid_nonzero']=str(d.get('tag_uid') or '') not in ZERO_UIDS
        d['tray_uuid_nonzero']=str(d.get('tray_uuid') or '') not in ZERO_UIDS
        out.append(d)
    return out