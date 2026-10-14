from pathlib import Path
import sqlite3,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"/"printbench_collector"))
import device_info


def test_version_request_is_read_only_info_command():
    assert device_info.build_version_request(12)=={"info":{"sequence_id":"12","command":"get_version"}}


def test_version_observation_sanitizes_serials():
    db=sqlite3.connect(":memory:")
    device_info.ensure_schema(db)
    raw={"info":{"command":"get_version","sequence_id":"1","module":[
        {"name":"ota","hw_ver":"N/A","sw_ver":"01.02.00.00","sn":"PRIVATE-SERIAL"},
        {"name":"mc","hw_ver":"MC06","sw_ver":"03.00.85.33","sn":"PRIVATE-MODULE"}]}}
    assert device_info.observe(db,raw,"2026-10-14T00:00:00+00:00")==2
    rows=device_info.summary(db)
    assert rows[0]["name"]=="ota" and rows[0]["sw_ver"]=="01.02.00.00"
    cols=[r[1] for r in db.execute("PRAGMA table_info(device_modules)")]
    assert "sn" not in cols
    dump=" ".join(str(x) for row in db.execute("SELECT * FROM device_modules") for x in row)
    assert "PRIVATE-SERIAL" not in dump and "PRIVATE-MODULE" not in dump
