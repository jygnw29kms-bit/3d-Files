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
API_PREFIX='/api/v1'


def dbconn():
    con=sqlite3.connect(f'file:{DB}?mode=ro', uri=True, timeout=2)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA query_only=ON')
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
        if not r: return {'online':False,'reason':'no_telemetry'}
        out={k:r[k] for k in r.keys() if k not in ('ams_json','ipcam_json','hms_json')}
        ams=safe_json(r['ams_json'],{}) or {}; unit=(ams.get('ams') or [{}])[0]
        slots=[]
        for t in unit.get('tray',[]) or []:
            slots.append({'id':str(t.get('id','')),'state':t.get('state'),'material':t.get('tray_type') or '',
              'color':t.get('tray_color') or '','remain':t.get('remain'),'source':'printer_report'})
        out['ams']={'temp_c':unit.get('temp'),'humidity':unit.get('humidity'),'humidity_raw':unit.get('humidity_raw'),
          'active_slot':ams.get('tray_now'),'tray_exist_bits':ams.get('tray_exist_bits'),'slots':slots,
          'dry_time':unit.get('dry_time',0),'dry_setting':unit.get('dry_setting') or {}}
        ip=safe_json(r['ipcam_json'],{}) or {}
        out['camera']={'printer_liveview':bool(ip.get('liveview_preview')),'browser_bridge':False,
          'recording':ip.get('ipcam_record')=='enable','timelapse':ip.get('timelapse')=='enable','resolution':ip.get('resolution')}
        hms=safe_json(r['hms_json'],[]) or []; out['hms_count']=len(hms) if isinstance(hms,list) else 0
        try: age=(datetime.now(timezone.utc)-datetime.fromisoformat(r['ts'])).total_seconds()
        except Exception: age=9999
        out['online']=age < 45; out['age_sec']=round(age,1)
        return out


def history(hours=24, limit=240):
    hours=max(1,min(int(hours),24*30)); limit=max(20,min(int(limit),500))
    cutoff=(datetime.now(timezone.utc)-timedelta(hours=hours)).isoformat()
    with dbconn() as db:
        rows=db.execute('''SELECT ts,progress,nozzle_c,nozzle_target_c,bed_c,bed_target_c,chamber_c,wifi_rssi
                           FROM telemetry WHERE ts>=? ORDER BY id''',(cutoff,)).fetchall()
    data=[dict(x) for x in rows]
    if len(data)>limit:
        step=(len(data)-1)/(limit-1); data=[data[round(i*step)] for i in range(limit)]
    return {'hours':hours,'points':data,'source_points':len(rows)}


def sessions(limit=20):
    with dbconn() as db:
        rows=db.execute('''SELECT id,started_at,ended_at,state,outcome,max_progress,max_layer,filament_type,
          filament_vendor,planned_filament_g,actual_time_sec,self_cost_eur,sale_price_eur,energy_is_estimated
          FROM print_sessions ORDER BY id DESC LIMIT ?''',(max(1,min(int(limit),50)),)).fetchall()
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
        d=dict(r); uid=d.pop('tag_uid',None); uuid=d.pop('tray_uuid',None)
        d['uid_exposed']=False
        d['uid_nonzero_observed']=uid not in (None,'','0000000000000000')
        d['uuid_nonzero_observed']=uuid not in (None,'','00000000000000000000000000000000')
        # P2S reports are partial/transient; do not present these bits as physical ground truth.
        d['confidence']='reported' if d.get('read_done') else 'transient'
        out.append(d)
    return out


def spools():
    with dbconn() as db:
        rows=db.execute('''SELECT spool_id,display_name,vendor,material,color_name,color_hex,filament_profile,
          remaining_g,initial_net_g,purchase_price_eur,nozzle_temp_min,nozzle_temp_max,dry_temp_c,dry_duration_h,
          last_dried_at,status,ams_id,ams_slot,nfc_tag_type,server_updated_at,synced_at FROM spool_inventory
          ORDER BY COALESCE(display_name,spool_id)''').fetchall()
        matches=db.execute('SELECT COUNT(*) FROM ams_spool_matches WHERE matched=1').fetchone()[0]
        proposals=db.execute("SELECT COUNT(*) FROM ams_action_proposals WHERE status='pending'").fetchone()[0]
    return {'items':[dict(x) for x in rows],'matched_count':matches,'pending_proposals':proposals,'uid_exposed':False}


def system_info():
    def cmd(args):
        try:return subprocess.check_output(args,text=True,stderr=subprocess.DEVNULL,timeout=1).strip()
        except Exception:return None
    temp=None
    try: temp=round(int(Path('/sys/class/thermal/thermal_zone0/temp').read_text())/1000,1)
    except Exception: pass
    disk=None
    try:
        st=os.statvfs('/'); disk={'total_gb':round(st.f_blocks*st.f_frsize/1e9,1),'free_gb':round(st.f_bavail*st.f_frsize/1e9,1)}
    except Exception: pass
    uptime=None
    try: uptime=int(float(Path('/proc/uptime').read_text().split()[0]))
    except Exception: pass
    return {'hostname':socket.gethostname(),'pi_temp_c':temp,'collector':cmd(['systemctl','is-active','printbench-collector.service']) or 'unknown',
      'ui':'active','uptime_sec':uptime,'disk':disk,'time':datetime.now(timezone.utc).isoformat()}


def capabilities():
    return {'api':'v1','read_only':True,'printer':'P2S','material_system':'AMS 2 Pro','features':{
      'telemetry':True,'history':True,'sessions':True,'ams_status':True,'rfid_diagnostics':True,
      'spool_inventory':True,'camera_browser_bridge':False,'ams_writes':False,'raw_uid_browser':False}}

class Handler(SimpleHTTPRequestHandler):
    server_version='PRINTBENCH'
    sys_version=''
    def end_headers(self):
        self.send_header('X-Content-Type-Options','nosniff'); self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer'); self.send_header('Permissions-Policy','camera=(), microphone=(), geolocation=()')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()
    def list_directory(self,path): self.send_error(403); return None
    def _json(self,obj,status=200):
        raw=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        u=urlparse(self.path)
        if u.path.startswith('/api/'):
            try:
                q=parse_qs(u.query); path=u.path
                # Backward compatibility for first UI build.
                if path.startswith('/api/') and not path.startswith(API_PREFIX+'/'): path=API_PREFIX+path[4:]
                if path==API_PREFIX+'/live': return self._json(latest_payload())
                if path==API_PREFIX+'/history': return self._json(history(q.get('hours',['24'])[0],q.get('limit',['240'])[0]))
                if path==API_PREFIX+'/sessions': return self._json(sessions(q.get('limit',['20'])[0]))
                if path==API_PREFIX+'/rfid': return self._json(rfid_summary())
                if path==API_PREFIX+'/spools': return self._json(spools())
                if path==API_PREFIX+'/system': return self._json(system_info())
                if path==API_PREFIX+'/capabilities': return self._json(capabilities())
                return self._json({'error':'not_found'},404)
            except Exception:
                return self._json({'error':'internal'},500)
        return super().do_GET()
    def log_message(self,*args): pass

if __name__=='__main__':
    os.chdir(STATIC); host=os.environ.get('PRINTBENCH_UI_HOST','0.0.0.0'); port=int(os.environ.get('PRINTBENCH_UI_PORT','8080'))
    print(f'[PRINTBENCH UI] http://{host}:{port}/',flush=True)
    ThreadingHTTPServer((host,port),Handler).serve_forever()
