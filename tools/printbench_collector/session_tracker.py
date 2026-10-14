from __future__ import annotations

import json
from datetime import datetime, timezone


ACTIVE_STATES = {
    'RUNNING', 'PAUSE', 'PAUSED', 'PREPARE', 'PREPARING', 'SLICING',
    'PRINTING', 'HEATING', 'BED_LEVELING', 'CALIBRATING'
}
SUCCESS_STATES = {'FINISH', 'FINISHED', 'COMPLETED', 'COMPLETE'}
FAIL_STATES = {'FAILED', 'FAIL', 'ERROR'}
CANCEL_STATES = {'CANCELLED', 'CANCELED', 'ABORTED', 'STOPPED'}
IDLE_STATES = {'IDLE'}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _state(v):
    return str(v or '').strip().upper()


def ensure_schema(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS print_sessions(
      id INTEGER PRIMARY KEY,
      started_at TEXT NOT NULL,
      ended_at TEXT,
      state TEXT NOT NULL DEFAULT 'printing',
      outcome TEXT,
      start_progress REAL,
      end_progress REAL,
      max_progress REAL,
      start_layer INTEGER,
      end_layer INTEGER,
      max_layer INTEGER,
      slicer_job_id INTEGER,
      origin_path TEXT,
      filament_type TEXT,
      filament_vendor TEXT,
      filament_profile TEXT,
      planned_filament_g REAL,
      planned_filament_m REAL,
      planned_time_sec INTEGER,
      actual_time_sec INTEGER,
      final_print_state TEXT,
      fail_reason TEXT,
      media_key TEXT,
      slicer_json TEXT,
      FOREIGN KEY(slicer_job_id) REFERENCES slicer_jobs(id)
    );
    CREATE INDEX IF NOT EXISTS idx_print_sessions_started ON print_sessions(started_at);
    CREATE INDEX IF NOT EXISTS idx_print_sessions_state ON print_sessions(state);
    ''')
    db.commit()


def _latest_slicer(db):
    row = db.execute('''
      SELECT id,origin_path,filament_type,filament_vendor,filament_profile,
             filament_g,filament_m,total_time_sec,raw_json
      FROM slicer_jobs ORDER BY id DESC LIMIT 1
    ''').fetchone()
    if not row:
        return None
    keys = ['id','origin_path','filament_type','filament_vendor','filament_profile',
            'filament_g','filament_m','total_time_sec','raw_json']
    return dict(zip(keys, row))


def _open_session(db):
    row = db.execute('''
      SELECT id,started_at,max_progress,max_layer FROM print_sessions
      WHERE ended_at IS NULL ORDER BY id DESC LIMIT 1
    ''').fetchone()
    if not row:
        return None
    return {'id': row[0], 'started_at': row[1], 'max_progress': row[2], 'max_layer': row[3]}


def _start(db, report):
    slicer = _latest_slicer(db) or {}
    ts = report.get('ts') or now_iso()
    progress = _num(report.get('progress'))
    layer = _int(report.get('layer_current'))
    media_key = ts.replace(':', '-').replace('+', '_').replace('.', '-')
    db.execute('''
      INSERT INTO print_sessions(
        started_at,state,start_progress,max_progress,start_layer,max_layer,
        slicer_job_id,origin_path,filament_type,filament_vendor,filament_profile,
        planned_filament_g,planned_filament_m,planned_time_sec,media_key,slicer_json
      ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
      ts, 'printing', progress, progress, layer, layer,
      slicer.get('id'), slicer.get('origin_path'), slicer.get('filament_type'),
      slicer.get('filament_vendor'), slicer.get('filament_profile'),
      slicer.get('filament_g'), slicer.get('filament_m'), slicer.get('total_time_sec'),
      media_key, slicer.get('raw_json') or json.dumps(slicer, ensure_ascii=False)
    ))
    db.execute('INSERT INTO events(ts,kind,payload) VALUES(?,?,?)', (
      ts, 'print_session_started', json.dumps({'origin_path': slicer.get('origin_path')}, ensure_ascii=False)
    ))
    db.commit()


def _finish(db, session, report, outcome):
    ts = report.get('ts') or now_iso()
    progress = _num(report.get('progress'))
    layer = _int(report.get('layer_current'))
    started = _parse_iso(session.get('started_at'))
    ended = _parse_iso(ts)
    actual = max(0, int((ended - started).total_seconds())) if started and ended else None
    state = _state(report.get('print_state'))
    fail_reason = report.get('fail_reason') or report.get('print_error')
    db.execute('''
      UPDATE print_sessions SET ended_at=?,state='finished',outcome=?,end_progress=?,
        max_progress=MAX(COALESCE(max_progress,0),COALESCE(?,0)),end_layer=?,
        max_layer=MAX(COALESCE(max_layer,0),COALESCE(?,0)),actual_time_sec=?,
        final_print_state=?,fail_reason=? WHERE id=?
    ''', (ts, outcome, progress, progress, layer, layer, actual, state, fail_reason, session['id']))
    db.execute('INSERT INTO events(ts,kind,payload) VALUES(?,?,?)', (
      ts, 'print_session_finished', json.dumps({'id': session['id'], 'outcome': outcome, 'state': state}, ensure_ascii=False)
    ))
    db.commit()


def _update(db, session, report):
    progress = _num(report.get('progress'))
    layer = _int(report.get('layer_current'))
    db.execute('''
      UPDATE print_sessions SET
        max_progress=MAX(COALESCE(max_progress,0),COALESCE(?,0)),
        max_layer=MAX(COALESCE(max_layer,0),COALESCE(?,0))
      WHERE id=?
    ''', (progress, layer, session['id']))
    db.commit()


def observe(db, report):
    """Observe one normalized MQTT report and maintain a durable print session."""
    ensure_schema(db)
    state = _state(report.get('print_state'))
    progress = _num(report.get('progress'))
    session = _open_session(db)

    active = state in ACTIVE_STATES or (progress is not None and 0 < progress < 100 and state not in FAIL_STATES | CANCEL_STATES)
    if session is None:
        if active:
            _start(db, report)
        return

    _update(db, session, report)

    if state in SUCCESS_STATES or (progress is not None and progress >= 99.9):
        _finish(db, session, report, 'success')
    elif state in FAIL_STATES:
        _finish(db, session, report, 'failed')
    elif state in CANCEL_STATES:
        _finish(db, session, report, 'cancelled')
    elif state in IDLE_STATES and (session.get('max_progress') or 0) > 0:
        # A return to IDLE without a 100% report is treated as interrupted.
        _finish(db, session, report, 'interrupted')


def _num(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _int(v):
    try:
        return int(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _parse_iso(v):
    try:
        return datetime.fromisoformat(str(v).replace('Z', '+00:00'))
    except Exception:
        return None
