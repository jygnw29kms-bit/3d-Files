from __future__ import annotations
import json, os, sqlite3, socket, subprocess
from datetime import datetime, timezone, timedelta
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT=Path(__file__).resolve().parent
COLLECTOR=ROOT.parent
DB=COLLECTOR/'printbench.db'
STATIC=ROOT/'static'


def dbconn():
    con=sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=2)
    con.row_factory=sqlite3.Row
    return con


def safe_json(v, default=None):
    if not v: return default
    try: return json.loads(v)
    except Exception: return default


def latest_payload():
    with dbconn() as db:
        r=db.execute('''SELECT ts,print_state,progress,remaining_min,layer_current,layer_total,
          nozzle_c,nozzle_target_c,bed_c,bed_target_c,chamber_c,wifi_rssi,speed_level,speed_mag,
          fan_part,fan_aux,fan_chamber,fan_heatbreak,print_stage,print_sub_stage,print_error,fail_reason,
          ams_json,ipcam_json,hms_json FROM telemetry ORDER BY id DESC LIMIT 1''').fetchone()
        if not r: return {'online':False}
        out={k:r[k] for k in r.keys() if k not in ('ams_json','ipcam_json','hms_json')}
        ams=safe_json(r['ams_json'],{}) or {}
        unit=(ams.get('ams') or [{}])[0]
        slots=[]
        for t in unit.get('tray',[]) or []:
            slots.append({
                'id':str(t.get('id','')),
                'state':t.get('state'),
                'material':t.get('tray_type') or '',
                'color':t.get('tray_color') or '',
                'remain':t.get('remain'),
                'is_bambu': bool(t.get('tag_uid') and t.get('tag_uid')!='0000000000000000')
            })
        out['ams']={
            'temp_c':unit.get('temp'),'humidity':unit.get('humidity'),'humidity_raw':unit.get('humidity_raw'),
            'active_slot':ams.get('tray_now'),'tray_exist_bits':ams.get('tray_exist_bits'),'slots':slots,
            'dry_time':unit.get('dry_time',0),'dry_setting':unit.get('dry_setting') or {}
        }
        ip=safe_json(r['ipcam_json'],{}) or {}
        out['camera']={'liveview':bool(ip.get('liveview_preview')),'recording':ip.get('ipcam_record')=='enable','timelapse':ip.get('timelapse')=='enable','resolution':ip.get('resolution')}
        hms=safe_json(r['hms_json'],[]) or []
        out['hms_count']=len(hms) if isinstance(hms,list) else 0
        try:
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(r['ts'])).total_seconds()
        except Exception: age=9999
        out['online']=age < 45
        out['age_sec']=round(age,1)
        return out


def history(hours=24, limit=240):
    hours=max(1,min(int(hours),24*30)); limit=max(20,min(int(limit),500))
    cutoff=(datetime.now(timezone.utc)-timedelta(hours=hours)).isoformat()
    with dbconn() as db:
        rows=db.execute('''SELECT ts,progress,nozzle_c,nozzle_target_c,bed_c,bed_target_c,chamber_c,wifi_rssi
                           FROM telemetry WHERE ts>=? ORDER BY id''',(cutoff,)).fetchall()
    data=[dict(x) for x in rows]
    if len(data)>limit:
        step=(len(data)-1)/(limit-1)
        data=[data[round(i*step)] for i in range(limit)]
    return {'hours':hours,'points':data}


def sessions(limit=10):
    with dbconn() as db:
        rows=db.execute('''SELECT id,started_at,ended_at,state,outcome,max_progress,max_layer,filament_type,
          filament_vendor,planned_filament_g,actual_time_sec,self_cost_eur,sale_price_eur,energy_is_estimated
          FROM print_sessions ORDER BY id DESC LIMIT ?''',(max(1,min(int(limit),30)),)).fetchall()
    return [dict(x) for x in rows]


def rfid_summary():
    with dbconn() as db:
        rows=db.execute('''SELECT o.ams_id,o.slot_id,o.ts,o.tray_present,o.reading,o.read_done,o.is_bambu,
          o.tray_state,o.tray_info_idx,o.tray_type,o.tray_color,o.tag_uid,o.tray_uuid
          FROM ams_rfid_observations o JOIN (
            SELECT ams_id,slot_id,MAX(id) id FROM ams_rfid_observations GROUP BY ams_id,slot_id
          ) x ON x.id=o.id ORDER BY CAST(o.slot_id AS INTEGER)''').fetchall()
    out=[]
    for r in rows:
        d=dict(r)
        d['tag_uid_present']=bool(d.pop('tag_uid',None) not in (None,'','0000000000000000'))
        d['tray_uuid_present']=bool(d.pop('tray_uuid',None) not in (None,'','00000000000000000000000000000000'))
        out.append(d)
    return out


def system_info():
    def cmd(args):
        try:return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=1).strip()
        except Exception:return None
    temp=None
    try: temp=round(int(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000,1)
    except Exception: pass
    return {'hostname':socket.gethostname(),'pi_temp_c':temp,'collector':cmd(['systemctl','is-active','printbench-collector.service']) or 'unknown','time':datetime.now(timezone.utc).isoformat()}

class Handler(SimpleHTTPRequestHandler):
    def _json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        u=urlparse(self.path)
        if u.path.startswith('/api/'):
            try:
                q=parse_qs(u.query)
                if u.path=='/api/live': return self._json(latest_payload())
                if u.path=='/api/history': return self._json(history(q.get('hours',['24'])[0],q.get('limit',['240'])[0]))
                if u.path=='/api/sessions': return self._json(sessions(q.get('limit',['10'])[0]))
                if u.path=='/api/rfid': return self._json(rfid_summary())
                if u.path=='/api/system': return self._json(system_info())
                return self._json({'error':'not_found'},404)
            except Exception as e:
                return self._json({'error':'internal','detail':str(e)[:160]},500)
        return super().do_GET()
    def log_message(self,*args): pass

if __name__=='__main__':
    os.chdir(STATIC)
    host=os.environ.get('PRINTBENCH_UI_HOST','0.0.0.0'); port=int(os.environ.get('PRINTBENCH_UI_PORT','8080'))
    print(f'[PRINTBENCH UI] http://{host}:{port}/',flush=True)
    ThreadingHTTPServer((host,port),Handler).serve_forever()
