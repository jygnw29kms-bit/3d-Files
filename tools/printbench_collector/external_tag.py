from __future__ import annotations
import argparse, json, sqlite3
from typing import Any
import collector
import spool_sync


def ensure_schema(db:sqlite3.Connection)->None:
    spool_sync.ensure_schema(db)
    db.executescript('''
    CREATE TABLE IF NOT EXISTS external_tag_observations(
      id INTEGER PRIMARY KEY,
      ts TEXT NOT NULL,
      reader_id TEXT NOT NULL,
      ams_id TEXT NOT NULL,
      slot_id TEXT NOT NULL,
      uid TEXT NOT NULL,
      tag_type TEXT,
      payload_json TEXT,
      spool_id TEXT,
      matched INTEGER NOT NULL,
      UNIQUE(ts,reader_id,ams_id,slot_id,uid)
    );
    CREATE INDEX IF NOT EXISTS idx_external_tag_slot ON external_tag_observations(ams_id,slot_id,id);
    ''')
    db.commit()


def observe(db:sqlite3.Connection, *, uid:Any, ams_id:Any, slot_id:Any, reader_id='external-nfc', tag_type='ntag', parsed:dict|None=None, ts:str|None=None)->dict:
    ensure_schema(db)
    ts=ts or collector.now_iso()
    norm=spool_sync._norm_uid(uid)
    if not norm or norm.replace(':','') in spool_sync.ZERO:
        raise ValueError('non-zero NFC UID required')
    match=spool_sync.match_uid(db,norm)
    spool_id=match.get('spool_id') if match else None
    proposal=spool_sync.store_proposal(db,ts,ams_id,slot_id,match) if match else None
    payload=json.dumps(parsed or {},ensure_ascii=False,separators=(',',':'))
    db.execute('INSERT OR IGNORE INTO external_tag_observations(ts,reader_id,ams_id,slot_id,uid,tag_type,payload_json,spool_id,matched) VALUES(?,?,?,?,?,?,?,?,?)',
               (ts,str(reader_id),str(ams_id),str(slot_id),norm,str(tag_type or ''),payload,spool_id,1 if match else 0))
    db.execute('INSERT INTO events(ts,kind,payload) VALUES(?,?,?)',
               (ts,'external_tag_match' if match else 'external_tag_unmatched',json.dumps({'reader_id':reader_id,'ams_id':str(ams_id),'slot_id':str(slot_id),'uid':norm,'tag_type':tag_type,'spool_id':spool_id},ensure_ascii=False)))
    db.commit()
    return {'ts':ts,'reader_id':str(reader_id),'ams_id':str(ams_id),'slot_id':str(slot_id),'uid':norm,'tag_type':str(tag_type or ''),'matched':bool(match),'spool_id':spool_id,'proposal':proposal}


def main()->None:
    p=argparse.ArgumentParser(description='Ingest an external NFC/NTAG observation into PRINTBENCH.')
    p.add_argument('--uid',required=True)
    p.add_argument('--ams-id',default='0')
    p.add_argument('--slot-id',required=True)
    p.add_argument('--reader-id',default='external-nfc')
    p.add_argument('--tag-type',default='ntag')
    p.add_argument('--payload-json')
    a=p.parse_args()
    parsed=json.loads(a.payload_json) if a.payload_json else {}
    db=collector.db_open()
    try:
        print(json.dumps(observe(db,uid=a.uid,ams_id=a.ams_id,slot_id=a.slot_id,reader_id=a.reader_id,tag_type=a.tag_type,parsed=parsed),ensure_ascii=False,indent=2))
    finally:
        db.close()

if __name__=='__main__':
    main()
