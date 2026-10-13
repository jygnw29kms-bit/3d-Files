from __future__ import annotations
import json, sqlite3
from pathlib import Path

DB = Path(__file__).with_name('printbench.db')

def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    t = db.execute('SELECT * FROM telemetry ORDER BY id DESC LIMIT 1').fetchone()
    j = db.execute('SELECT * FROM slicer_jobs ORDER BY id DESC LIMIT 1').fetchone()
    counts = db.execute('SELECT COUNT(*) AS n FROM telemetry').fetchone()['n']
    print('PRINTBENCH STATUS')
    print('telemetry_samples=', counts)
    if t:
        print('live=', json.dumps({
            'ts': t['ts'], 'state': t['print_state'], 'progress': t['progress'],
            'remaining_min': t['remaining_min'], 'layer_current': t['layer_current'],
            'layer_total': t['layer_total'], 'nozzle_c': t['nozzle_c'],
            'bed_c': t['bed_c'], 'wifi_rssi': t['wifi_rssi'], 'speed_level': t['speed_level']
        }, ensure_ascii=False))
        try:
            ams = json.loads(t['ams_json'] or 'null')
            if isinstance(ams, dict):
                units = ams.get('ams') or []
                a0 = units[0] if units else {}
                trays = a0.get('tray') or []
                active = str(ams.get('tray_now'))
                tray = next((x for x in trays if str(x.get('id')) == active), {})
                print('ams=', json.dumps({
                    'unit': a0.get('id'), 'temp_c': a0.get('temp'),
                    'humidity': a0.get('humidity'), 'humidity_raw': a0.get('humidity_raw'),
                    'active_slot': ams.get('tray_now'), 'material': tray.get('tray_type'),
                    'color': tray.get('tray_color'), 'remain': tray.get('remain'),
                    'tag_uid_present': bool(tray.get('tag_uid') and set(tray.get('tag_uid')) != {'0'})
                }, ensure_ascii=False))
        except Exception:
            pass
    if j:
        print('slicer=', json.dumps({
            'slicer': j['slicer'], 'model_time_sec': j['model_time_sec'],
            'total_time_sec': j['total_time_sec'], 'layers': j['layer_count'],
            'filament_g': j['filament_g'], 'filament_m': j['filament_m'],
            'material': j['filament_type'], 'vendor': j['filament_vendor'],
            'layer_height': j['layer_height'], 'infill_percent': j['infill_percent'],
            'infill_pattern': j['infill_pattern'], 'wall_loops': j['wall_loops']
        }, ensure_ascii=False))
    db.close()

if __name__ == '__main__':
    main()
