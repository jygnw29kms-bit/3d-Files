from __future__ import annotations
import sqlite3
from typing import Any


def ensure_schema(db: sqlite3.Connection) -> None:
    db.executescript("""
    CREATE TABLE IF NOT EXISTS device_modules(
      name TEXT PRIMARY KEY,
      hw_ver TEXT,
      sw_ver TEXT,
      updated_at TEXT NOT NULL
    );
    """)
    db.commit()


def build_version_request(sequence_id: Any) -> dict:
    return {"info":{"sequence_id":str(sequence_id),"command":"get_version"}}


def observe(db: sqlite3.Connection, raw: Any, ts: str) -> int:
    if not isinstance(raw,dict): return 0
    info=raw.get("info")
    if not isinstance(info,dict) or info.get("command")!="get_version": return 0
    modules=info.get("module")
    if not isinstance(modules,list): return 0
    count=0
    for item in modules:
        if not isinstance(item,dict): continue
        name=str(item.get("name") or "").strip()[:64]
        if not name: continue
        hw=str(item.get("hw_ver") or "").strip()[:64]
        sw=str(item.get("sw_ver") or "").strip()[:96]
        db.execute("""INSERT INTO device_modules(name,hw_ver,sw_ver,updated_at) VALUES(?,?,?,?)
          ON CONFLICT(name) DO UPDATE SET hw_ver=excluded.hw_ver,sw_ver=excluded.sw_ver,updated_at=excluded.updated_at""",
          (name,hw,sw,ts))
        count+=1
    if count: db.commit()
    return count


def summary(db: sqlite3.Connection) -> list[dict]:
    ensure_schema(db)
    rows=db.execute("SELECT name,hw_ver,sw_ver,updated_at FROM device_modules ORDER BY CASE name WHEN 'ota' THEN 0 ELSE 1 END,name").fetchall()
    keys=("name","hw_ver","sw_ver","updated_at")
    return [dict(zip(keys,row)) for row in rows]
