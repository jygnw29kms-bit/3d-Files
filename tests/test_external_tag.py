from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'printbench_collector'))
import sqlite3
import external_tag
import spool_sync


def test_external_tag_match():
    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE events(id INTEGER PRIMARY KEY, ts TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL)')
    spool_sync.ensure_schema(db)
    db.execute("INSERT INTO spool_inventory(spool_id,nfc_uid,synced_at,raw_json) VALUES('S1','04:A1:B2:C3:D4:E5:F6','x','{}')")
    db.commit()
    out=external_tag.observe(db,uid='04A1B2C3D4E5F6',ams_id=0,slot_id=3,reader_id='test',tag_type='ntag216',ts='2026-10-14T00:00:00+00:00')
    assert out['matched'] is True and out['spool_id']=='S1'
    assert 'uid' not in out
    row=db.execute('SELECT uid,matched,spool_id FROM external_tag_observations').fetchone()
    assert tuple(row)==('04:A1:B2:C3:D4:E5:F6',1,'S1')

