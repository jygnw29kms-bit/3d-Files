from pathlib import Path
import json, sqlite3, sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'printbench_collector'))
import reader_serial
import spool_sync


def valid_message(**overrides):
    obj={'version':1,'reader_id':'esp32-ams','ams_id':'0','slot_id':3,'uid':'04A1B2C3D4E5F6','tag_type':'ntag216','payload':{'format':'opentag3d'}}
    obj.update(overrides)
    return json.dumps(obj,separators=(',',':'))


def test_parse_reader_message():
    m=reader_serial.parse_message(valid_message())
    assert m['slot_id']=='3'
    assert m['uid']=='04:A1:B2:C3:D4:E5:F6'
    assert m['tag_type']=='ntag216'


def test_reject_bad_version_and_slot():
    with pytest.raises(ValueError):reader_serial.parse_message(valid_message(version=2))
    with pytest.raises(ValueError):reader_serial.parse_message(valid_message(slot_id=4))


def test_reject_oversized_message():
    with pytest.raises(ValueError):reader_serial.parse_message(b'{' + b'x'*5000 + b'}')


def test_process_message_matches_inventory_without_uid_in_event():
    db=sqlite3.connect(':memory:')
    db.execute('CREATE TABLE events(id INTEGER PRIMARY KEY, ts TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL)')
    spool_sync.ensure_schema(db)
    db.execute("INSERT INTO spool_inventory(spool_id,nfc_uid,synced_at,raw_json) VALUES('S1','04:A1:B2:C3:D4:E5:F6','x','{}')")
    db.commit()
    out=reader_serial.process_message(db,valid_message())
    assert out['matched'] is True and out['spool_id']=='S1'
    assert 'uid' not in out
    event=db.execute('SELECT payload FROM events ORDER BY id DESC LIMIT 1').fetchone()[0]
    assert '04:A1' not in event
