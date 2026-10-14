from __future__ import annotations
import json, os, re, sqlite3,  time
from datetime import datetime, timezone
from pathlib import Path
import paho.mqtt.client as mqtt
import bambu_tls

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'printbench.db'
_PI_BAMBU_CONF = Path('/etc/printbench/bambu.json')
BAMBU_CONF = Path(os.environ.get('PRINTBENCH_BAMBU_CONFIG', '')) if os.environ.get('PRINTBENCH_BAMBU_CONFIG') else (_PI_BAMBU_CONF if _PI_BAMBU_CONF.is_file() else (Path.home() / 'AppData' / 'Roaming' / 'BambuStudio' / 'BambuStudio.conf'))
BAMBU_TEMP = Path(os.environ.get('PRINTBENCH_SLICER_TEMP', '')) if os.environ.get('PRINTBENCH_SLICER_TEMP') else (Path(os.environ.get('LOCALAPPDATA', '')) / 'Temp' / 'bamboo_model')
P2S_HOST = os.environ.get('PRINTBENCH_P2S_HOST', '192.168.178.110').strip() or '192.168.178.110'


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_local_bambu_identity():
    raw = BAMBU_CONF.read_text(encoding='utf-8', errors='ignore')
    data, _ = json.JSONDecoder().raw_decode(raw.lstrip('\ufeff \\t\\r\\n'))
    if isinstance(data, dict) and data.get('serial') and data.get('access_code') and isinstance(data.get('access_code'), str):
        return str(data['serial']).strip(), str(data['access_code']).strip()
    access = data.get('access_code') or {}
    if isinstance(access, dict) and access:
        serial, code = next(iter(access.items()))
        return str(serial).strip(), str(code).strip()
    raise RuntimeError(f'No usable Bambu LAN identity in {BAMBU_CONF}')


def db_open():
    db = sqlite3.connect(DB, check_same_thread=False)
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS slicer_jobs(
      id INTEGER PRIMARY KEY, detected_at TEXT NOT NULL, source_path TEXT UNIQUE,
      origin_path TEXT, slicer TEXT, model_time_sec INTEGER, total_time_sec INTEGER,
      layer_count INTEGER, filament_g REAL, filament_m REAL, filament_type TEXT,
      filament_vendor TEXT, filament_profile TEXT, density REAL, diameter REAL,
      nozzle_diameter REAL, nozzle_type TEXT, layer_height REAL, infill_percent REAL,
      infill_pattern TEXT, wall_loops INTEGER, bed_type TEXT, raw_json TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS telemetry(
      id INTEGER PRIMARY KEY, ts TEXT NOT NULL, print_state TEXT, progress REAL,
      remaining_min REAL, layer_current INTEGER, layer_total INTEGER,
      nozzle_c REAL, nozzle_target_c REAL, bed_c REAL, bed_target_c REAL,
      chamber_c REAL, wifi_rssi REAL, speed_level TEXT, ams_json TEXT, raw_json TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry(ts);
    CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, ts TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS mqtt_raw(
      id INTEGER PRIMARY KEY, ts TEXT NOT NULL, topic TEXT NOT NULL,
      command TEXT, payload TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_mqtt_raw_ts ON mqtt_raw(ts);
    CREATE INDEX IF NOT EXISTS idx_mqtt_raw_command ON mqtt_raw(command);
    ''')
    cols={r[1] for r in db.execute('PRAGMA table_info(telemetry)').fetchall()}
    migrations={
      'speed_mag':'REAL','fan_part':'REAL','fan_aux':'REAL','fan_chamber':'REAL','fan_heatbreak':'REAL',
      'print_stage':'TEXT','print_sub_stage':'TEXT','ipcam_json':'TEXT','hms_json':'TEXT',
      'print_error':'TEXT','fail_reason':'TEXT'
    }
    for name,typ in migrations.items():
        if name not in cols:
            db.execute(f'ALTER TABLE telemetry ADD COLUMN {name} {typ}')
    db.commit()
    return db


def _first(pattern, text, cast=str):
    m = re.search(pattern, text, re.I | re.M)
    if not m: return None
    try: return cast(m.group(1).strip())
    except Exception: return None


def _hms_seconds(s):
    if not s: return None
    h = _first(r'(\d+)h', s, int) or 0
    m = _first(r'(\d+)m', s, int) or 0
    sec = _first(r'(\d+)s', s, int) or 0
    return h*3600 + m*60 + sec


def parse_gcode(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    head = text[:250000]
    times = re.search(r'model printing time:\s*([^;\r\n]+);\s*total estimated time:\s*([^;\r\n]+)', head, re.I)
    d = {
      'source_path': str(path), 'slicer': _first(r'^;\s*(BambuStudio[^\r\n]*)', head),
      'model_time_sec': _hms_seconds(times.group(1)) if times else None,
      'total_time_sec': _hms_seconds(times.group(2)) if times else None,
      'layer_count': _first(r'total layer number:\s*(\d+)', head, int),
      'filament_g': _first(r'total filament weight \[g\]\s*:\s*([0-9.]+)', head, float),
      'filament_m': None, 'density': _first(r'filament_density:\s*([0-9.]+)', head, float),
      'diameter': _first(r'filament_diameter:\s*([0-9.]+)', head, float),
      'bed_type': _first(r'curr_bed_type\s*=\s*([^;\r\n]+)', text),
    }
    mm = _first(r'total filament length \[mm\]\s*:\s*([0-9.]+)', head, float)
    if mm is not None: d['filament_m'] = mm / 1000.0
    return d, text


def newest_workspace():
    if not BAMBU_TEMP.exists(): return None
    candidates = [p for p in BAMBU_TEMP.rglob('*') if p.is_dir() and (p / 'Metadata').is_dir()]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def ingest_latest_slicer(db):
    ws = newest_workspace()
    if not ws: return None
    gcodes = sorted((ws / 'Metadata').glob('*.gcode'), key=lambda p:p.stat().st_mtime, reverse=True)
    if not gcodes: return None
    d, full = parse_gcode(gcodes[0])
    origin = ws / 'origin.txt'
    d['origin_path'] = origin.read_text(encoding='utf-8', errors='ignore').strip() if origin.exists() else None
    configs = sorted(ws.glob('_temp_*.config'), key=lambda p:p.stat().st_mtime, reverse=True)
    config_texts = [(cp, cp.read_text(encoding='utf-8', errors='ignore')) for cp in configs[:6]]
    preferred = next((txt for _, txt in config_texts if re.search(r'"filament_vendor"\s*:\s*\[?\s*"KINGROON"', txt, re.I)), None)
    ctext = preferred or ('\n'.join(txt for _, txt in config_texts))
    d.update({
      'filament_type': _first(r'"filament_type"\s*:\s*\[?\s*"([^"]+)', ctext),
      'filament_vendor': _first(r'"filament_vendor"\s*:\s*\[?\s*"([^"]+)', ctext),
      'filament_profile': _first(r'"filament_settings_id"\s*:\s*\[?\s*"([^"]+)"', ctext),
      'nozzle_diameter': _first(r'"nozzle_diameter"\s*:\s*\[?\s*"?([0-9.]+)', ctext, float),
      'nozzle_type': _first(r'"nozzle_type"\s*:\s*"([^"]+)', ctext),
      'layer_height': _first(r'"layer_height"\s*:\s*"?([0-9.]+)', ctext, float),
      'infill_percent': _first(r'"sparse_infill_density"\s*:\s*"?([0-9.]+)', ctext, float),
      'infill_pattern': _first(r'"sparse_infill_pattern"\s*:\s*"([^"]+)', ctext),
      'wall_loops': _first(r'"wall_loops"\s*:\s*"?(\d+)', ctext, int),
    })
    payload = json.dumps(d, ensure_ascii=False)
    cols = ['source_path','origin_path','slicer','model_time_sec','total_time_sec','layer_count','filament_g','filament_m','filament_type','filament_vendor','filament_profile','density','diameter','nozzle_diameter','nozzle_type','layer_height','infill_percent','infill_pattern','wall_loops','bed_type']
    vals = [d.get(c) for c in cols]
    db.execute(f"INSERT OR REPLACE INTO slicer_jobs(detected_at,{','.join(cols)},raw_json) VALUES (? ,{','.join('?' for _ in cols)},?)", [now_iso(),*vals,payload])
    db.commit(); return d


def pick(d, *paths):
    for path in paths:
        cur=d
        ok=True
        for k in path.split('.'):
            if not isinstance(cur,dict) or k not in cur: ok=False; break
            cur=cur[k]
        if ok: return cur
    return None


def normalize_report(msg):
    p = msg.get('print', msg)
    ams = p.get('ams') if isinstance(p,dict) else None
    return {
      'ts': now_iso(), 'print_state': pick(p,'gcode_state','print_state'),
      'progress': pick(p,'mc_percent','progress'), 'remaining_min': pick(p,'mc_remaining_time'),
      'layer_current': pick(p,'layer_num'), 'layer_total': pick(p,'total_layer_num'),
      'nozzle_c': pick(p,'nozzle_temper'), 'nozzle_target_c': pick(p,'nozzle_target_temper'),
      'bed_c': pick(p,'bed_temper'), 'bed_target_c': pick(p,'bed_target_temper'),
      'chamber_c': pick(p,'chamber_temper','device.ctc.info.temp','info.temp'), 'wifi_rssi': pick(p,'wifi_signal'),
      'speed_level': pick(p,'spd_lvl'), 'speed_mag': pick(p,'spd_mag'),
      'fan_part': pick(p,'cooling_fan_speed'), 'fan_aux': pick(p,'big_fan1_speed'),
      'fan_chamber': pick(p,'big_fan2_speed'), 'fan_heatbreak': pick(p,'heatbreak_fan_speed'),
      'print_stage': pick(p,'mc_print_stage'), 'print_sub_stage': pick(p,'mc_print_sub_stage'),
      'ipcam': pick(p,'ipcam'), 'hms': pick(p,'hms'), 'print_error': pick(p,'print_error'),
      'fail_reason': pick(p,'fail_reason'), 'ams': ams
    }


def _mqtt_command(raw):
    if not isinstance(raw, dict): return None
    for section in ('print','pushing','info','system'):
        obj = raw.get(section)
        if isinstance(obj, dict) and obj.get('command') is not None:
            return str(obj.get('command'))
    if raw.get('command') is not None:
        return str(raw.get('command'))
    return None

def save_raw_mqtt(db, topic, raw):
    db.execute('INSERT INTO mqtt_raw(ts,topic,command,payload) VALUES(?,?,?,?)', (now_iso(), str(topic), _mqtt_command(raw), json.dumps(raw,ensure_ascii=False)))
    db.commit()

def save_report(db, raw):
    n=normalize_report(raw)
    db.execute('''INSERT INTO telemetry(ts,print_state,progress,remaining_min,layer_current,layer_total,nozzle_c,nozzle_target_c,bed_c,bed_target_c,chamber_c,wifi_rssi,speed_level,ams_json,raw_json,speed_mag,fan_part,fan_aux,fan_chamber,fan_heatbreak,print_stage,print_sub_stage,ipcam_json,hms_json,print_error,fail_reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
      (n['ts'],n['print_state'],n['progress'],n['remaining_min'],n['layer_current'],n['layer_total'],n['nozzle_c'],n['nozzle_target_c'],n['bed_c'],n['bed_target_c'],n['chamber_c'],n['wifi_rssi'],str(n['speed_level']) if n['speed_level'] is not None else None,json.dumps(n['ams'],ensure_ascii=False),json.dumps(raw,ensure_ascii=False),n['speed_mag'],n['fan_part'],n['fan_aux'],n['fan_chamber'],n['fan_heatbreak'],str(n['print_stage']) if n['print_stage'] is not None else None,str(n['print_sub_stage']) if n['print_sub_stage'] is not None else None,json.dumps(n['ipcam'],ensure_ascii=False),json.dumps(n['hms'],ensure_ascii=False),str(n['print_error']) if n['print_error'] is not None else None,str(n['fail_reason']) if n['fail_reason'] is not None else None))
    db.commit(); return n


def run_mqtt(db, seconds=20):
    serial, code = load_local_bambu_identity()
    topic_report=f'device/{serial}/report'; topic_req=f'device/{serial}/request'
    state={'connected':False,'messages':0,'last':None}
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
    client.username_pw_set('bblp', code)
    client.tls_set_context(bambu_tls.mqtt_context())
    def on_connect(c,u,flags,reason,props):
        if not getattr(reason, 'is_failure', False):
            state['connected']=True; c.subscribe(topic_report)
            c.publish(topic_req,json.dumps({'pushing':{'sequence_id':'0','command':'pushall'}}))
    def on_message(c,u,m):
        try:
            raw=json.loads(m.payload.decode('utf-8','ignore')); state['last']=save_report(db,raw); state['messages']+=1
        except Exception as e:
            db.execute('INSERT INTO events(ts,kind,payload) VALUES(?,?,?)',(now_iso(),'mqtt_parse_error',json.dumps({'error':str(e)}))); db.commit()
    client.on_connect=on_connect; client.on_message=on_message
    client.connect(P2S_HOST,8883,keepalive=30); client.loop_start()
    deadline=time.time()+seconds
    while time.time()<deadline and state['messages']<3: time.sleep(.25)
    client.loop_stop(); client.disconnect(); return state


def main():
    db=db_open(); planned=ingest_latest_slicer(db)
    if planned:
        print('SLICER_OK', json.dumps({k:planned.get(k) for k in ['slicer','model_time_sec','total_time_sec','layer_count','filament_g','filament_m','filament_type','filament_vendor','layer_height','infill_percent','infill_pattern','wall_loops']}, ensure_ascii=False))
    else: print('SLICER_NONE')
    st=run_mqtt(db,20)
    safe={'connected':st['connected'],'messages':st['messages'],'last':st['last']}
    print('MQTT_RESULT',json.dumps(safe,ensure_ascii=False,default=str))
    print('DB',DB)

if __name__=='__main__': main()
