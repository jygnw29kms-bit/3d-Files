from __future__ import annotations
import json, sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'printbench.db'
OUT = ROOT / 'preview' / 'data.json'

def rowdict(cur, row):
    return {d[0]: row[i] for i, d in enumerate(cur.description)}

def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    live = db.execute('''SELECT ts,print_state,progress,remaining_min,layer_current,layer_total,
        nozzle_c,nozzle_target_c,bed_c,bed_target_c,chamber_c,wifi_rssi,speed_level,ams_json
        FROM telemetry ORDER BY id DESC LIMIT 1''').fetchone()
    if not live:
        raise SystemExit('No telemetry available')

    history = db.execute('''SELECT ts,progress,remaining_min,layer_current,layer_total,
        nozzle_c,nozzle_target_c,bed_c,bed_target_c,chamber_c,wifi_rssi,speed_level
        FROM telemetry ORDER BY id DESC LIMIT 360''').fetchall()[::-1]

    slicer = db.execute('''SELECT detected_at,origin_path,slicer,model_time_sec,total_time_sec,layer_count,
        filament_g,filament_m,filament_type,filament_vendor,filament_profile,density,diameter,
        nozzle_diameter,nozzle_type,layer_height,infill_percent,infill_pattern,wall_loops,bed_type
        FROM slicer_jobs ORDER BY id DESC LIMIT 1''').fetchone()
    slicer_data = dict(slicer) if slicer else {}
    if slicer_data.get('origin_path'):
        slicer_data['origin_path'] = Path(slicer_data['origin_path']).name

    ams_raw = json.loads(live['ams_json']) if live['ams_json'] else {}
    unit = (ams_raw.get('ams') or [{}])[0]
    active = str(ams_raw.get('tray_now', ''))
    tray = next((t for t in unit.get('tray', []) if str(t.get('id')) == active), {})

    ams = {
        'unit': unit.get('id'),
        'active_slot': active,
        'temp_c': float(unit['temp']) if str(unit.get('temp','')).replace('.','',1).isdigit() else None,
        'humidity_level': unit.get('humidity'),
        'humidity_raw': float(unit['humidity_raw']) if str(unit.get('humidity_raw','')).replace('.','',1).isdigit() else None,
        'material': tray.get('tray_type'),
        'color': tray.get('tray_color'),
        'remain': tray.get('remain'),
        'tag_uid_present': bool(tray.get('tag_uid') and tray.get('tag_uid') != '0000000000000000'),
        'drying': bool(unit.get('dry_time', 0) and unit.get('dry_time', 0) > 0),
        'dry_time': unit.get('dry_time', 0),
    }

    stats_row = db.execute('''SELECT COUNT(*) samples,
        MIN(nozzle_c) nozzle_min, MAX(nozzle_c) nozzle_max, AVG(nozzle_c) nozzle_avg,
        MIN(bed_c) bed_min, MAX(bed_c) bed_max, AVG(bed_c) bed_avg,
        MIN(progress) progress_min, MAX(progress) progress_max,
        MIN(ts) first_ts, MAX(ts) last_ts
        FROM telemetry''').fetchone()
    recent_jobs = db.execute('''SELECT detected_at,origin_path,slicer,total_time_sec,layer_count,
        filament_g,filament_m,filament_type,filament_vendor,filament_profile,layer_height,
        infill_percent,infill_pattern,wall_loops,bed_type
        FROM slicer_jobs ORDER BY id DESC LIMIT 12''').fetchall()
    jobs = []
    for row in recent_jobs:
        item = dict(row)
        if item.get('origin_path'):
            item['origin_path'] = Path(item['origin_path']).name
        jobs.append(item)

    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'source': 'PRINTBENCH Collector / P2S LAN MQTT + Bambu Studio',
        'live': {k: live[k] for k in live.keys() if k != 'ams_json'},
        'ams': ams,
        'slicer': slicer_data,
        'history': [dict(r) for r in history],
        'sample_count': db.execute('SELECT COUNT(*) FROM telemetry').fetchone()[0],
        'stats': dict(stats_row),
        'jobs': jobs,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'PREVIEW_DATA_OK samples={len(history)} total={payload["sample_count"]}')

if __name__ == '__main__':
    main()
