from __future__ import annotations
import json, math, os, sqlite3, ssl, threading, time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import paho.mqtt.client as mqtt
import collector
import bambu_tls
import ams_control

_LOCK = threading.Lock()
_LAST_SEND = 0.0
AUDIT_FILE = Path(os.environ.get('PRINTBENCH_CONTROL_AUDIT', '/var/lib/printbench/control-audit.jsonl'))

@dataclass(frozen=True)
class CommandSpec:
    name: str
    risk: str
    protocol_status: str
    builder: Callable[[dict, str], dict]
    verifier: Callable[[sqlite3.Connection, dict], bool] | None
    policy: str = 'writes'
    qos: int = 0
    min_interval: float = 1.0


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None: return default
    return str(raw).strip().lower() in {'1','true','yes','on','enabled'}


def _db_open_readonly() -> sqlite3.Connection:
    db = sqlite3.connect(f'file:{collector.DB}?mode=ro', uri=True, timeout=2)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def _latest(db: sqlite3.Connection) -> dict:
    row=db.execute('''SELECT ts,print_state,speed_level,speed_mag,nozzle_c,nozzle_target_c,bed_c,bed_target_c,
                      chamber_c,fan_part,fan_aux,fan_chamber,ams_json,ipcam_json,raw_json
                      FROM telemetry ORDER BY id DESC LIMIT 1''').fetchone()
    return dict(row) if row else {}


def _state_fresh(state: dict, max_age: float = 45.0) -> bool:
    try:return (datetime.now(timezone.utc)-datetime.fromisoformat(state['ts'])).total_seconds()<=max_age
    except Exception:return False


def _simple_print(command: str):
    def build(args: dict, seq: str) -> dict:
        if args: raise ValueError(f'{command} takes no arguments')
        return {'print':{'sequence_id':seq,'command':command,'param':''}}
    return build


def _speed(args,seq):
    level=int(args.get('level'))
    if level not in (1,2,3,4): raise ValueError('level must be 1..4')
    return {'print':{'sequence_id':seq,'command':'print_speed','param':str(level)}}


def _light(args,seq):
    mode=str(args.get('mode','')).lower()
    if mode not in {'on','off'}: raise ValueError('mode must be on or off')
    return {'system':{'sequence_id':seq,'command':'ledctrl','led_node':'chamber_light','led_mode':mode,
                      'led_on_time':500,'led_off_time':500,'loop_times':1,'interval_time':1000}}


def _fan(args,seq):
    fan=int(args.get('fan')); speed=int(args.get('speed'))
    if fan not in (0,1,2): raise ValueError('fan must be 0..2')
    if not 0<=speed<=255: raise ValueError('speed must be 0..255')
    return {'print':{'sequence_id':seq,'command':'set_fan','fan_index':fan,'speed':speed}}


def _nozzle(args,seq):
    temp=int(args.get('temp')); extruder=int(args.get('extruder',0))
    if extruder!=0: raise ValueError('P2S supports extruder 0 only')
    if not 0<=temp<=300: raise ValueError('nozzle temp must be 0..300 C')
    return {'print':{'sequence_id':seq,'command':'set_nozzle_temp','extruder_index':0,'target_temp':temp}}


def _bed(args,seq):
    temp=int(args.get('temp'))
    if not 0<=temp<=120: raise ValueError('bed temp must be 0..120 C')
    return {'print':{'sequence_id':seq,'command':'set_bed_temp','temp':temp}}


def _chamber(args,seq):
    temp=int(args.get('temp'))
    if temp!=0 and not 35<=temp<=65: raise ValueError('chamber temp must be 0 or 35..65 C')
    return {'print':{'sequence_id':seq,'command':'set_ctt','ctt_val':temp}}


def _camera_toggle(command):
    def build(args,seq):
        enabled=args.get('enabled')
        if not isinstance(enabled,bool): raise ValueError('enabled must be boolean')
        return {'camera':{'sequence_id':seq,'command':command,'control':'enable' if enabled else 'disable'}}
    return build


def _camera_resolution(args,seq):
    resolution=str(args.get('resolution','')).lower()
    if resolution not in {'720p','1080p'}: raise ValueError('resolution must be 720p or 1080p')
    return {'camera':{'sequence_id':seq,'command':'ipcam_resolution_set','resolution':resolution}}


def _ams_rfid(args,seq):
    ams_id=int(args.get('ams_id',0)); slot=int(args.get('slot_id'))
    if not 0<=ams_id<=3 or not 0<=slot<=3: raise ValueError('AMS/slot must be 0..3')
    return {'print':{'sequence_id':seq,'command':'ams_get_rfid','ams_id':ams_id,'slot_id':slot}}


def _ams_control(args,seq):
    action=str(args.get('action','')).lower()
    if action not in {'resume','reset','pause','done','abort'}: raise ValueError('invalid AMS action')
    return {'print':{'sequence_id':seq,'command':'ams_control','param':action}}


def _ams_stop_dry(args,seq):
    if args: raise ValueError('ams.stop_drying takes no arguments')
    return {'print':{'sequence_id':seq,'command':'auto_stop_ams_dry'}}


def _ams_filament_setting(args,seq):
    required=('ams_id','slot_id','material','color','nozzle_temp_min','nozzle_temp_max')
    missing=[x for x in required if x not in args]
    if missing: raise ValueError('missing: '+','.join(missing))
    payload=ams_control.build_filament_setting(args['ams_id'],args['slot_id'],args['material'],args['color'],
                                               args['nozzle_temp_min'],args['nozzle_temp_max'],args.get('tray_info_idx'),seq)
    p=payload['print']; p['slot_id']=p.pop('tray_id'); p['tray_id']=p['slot_id']; p['setting_id']=str(args.get('setting_id') or '')
    return payload


def _ams_change(args,seq):
    load=args.get('load')
    if not isinstance(load,bool): raise ValueError('load must be boolean')
    ams_id=int(args.get('ams_id',0)); slot=int(args.get('slot_id',0)); old=int(args.get('old_temp',0)); new=int(args.get('new_temp',0))
    if not 0<=ams_id<=3 or not 0<=slot<=3: raise ValueError('AMS/slot must be 0..3')
    if not 0<=old<=300 or not 0<=new<=300: raise ValueError('temperature out of range')
    tray=ams_id*4+slot
    return {'print':{'sequence_id':seq,'command':'ams_change_filament','curr_temp':old,'tar_temp':new,'ams_id':ams_id,
                     'target':tray if load else 255,'slot_id':slot if load else 255}}


def _verify_pause(db,args): return str(_latest(db).get('print_state') or '').upper() in {'PAUSE','PAUSED'}
def _verify_resume(db,args): return str(_latest(db).get('print_state') or '').upper() in {'RUNNING','PREPARE','PRINTING'}
def _verify_stop(db,args): return str(_latest(db).get('print_state') or '').upper() not in {'RUNNING','PREPARE','PRINTING','PAUSE','PAUSED'}

def _verify_speed(db,args):
    state=_latest(db); wanted=str(int(args['level']))
    if str(state.get('speed_level'))==wanted:return True
    expected={'1':50,'2':100,'3':124,'4':166}.get(wanted)
    try:return int(float(state.get('speed_mag')))==expected
    except Exception:return False

def _verify_light(db,args):
    try:
        report=json.loads(_latest(db).get('raw_json') or '{}').get('print',{}).get('lights_report') or []
        want=str(args.get('mode','')).lower()
        return any(isinstance(x,dict) and x.get('node')=='chamber_light' and str(x.get('mode','')).lower()==want for x in report)
    except Exception:return False
def _verify_fan(db,args):
    state=_latest(db); raw={0:state.get('fan_part'),1:state.get('fan_aux'),2:state.get('fan_chamber')}.get(int(args['fan']))
    try:
        value=float(raw); reported=round(math.floor(value/1.5)*25.5) if value<=20 else round(value)
        return abs(reported-int(args['speed']))<=26
    except Exception:return False

def _verify_nozzle(db,args):
    v=_latest(db).get('nozzle_target_c')
    try:return abs(float(v)-int(args['temp']))<=1
    except Exception:return False

def _verify_bed(db,args):
    v=_latest(db).get('bed_target_c')
    try:return abs(float(v)-int(args['temp']))<=1
    except Exception:return False

def _verify_chamber(db,args):
    try:
        p=json.loads(_latest(db).get('raw_json') or '{}').get('print',{})
        v=p.get('ctt_val')
        if v is None:v=((p.get('device') or {}).get('ctc') or {}).get('target')
        if v is None:v=p.get('chamber_target_temper')
        return v is not None and int(float(v))==int(args['temp'])
    except Exception:return False

def _verify_camera_record(db,args):
    try:return (json.loads(_latest(db).get('ipcam_json') or '{}').get('ipcam_record')=='enable')==bool(args['enabled'])
    except Exception:return False

def _verify_camera_timelapse(db,args):
    try:return (json.loads(_latest(db).get('ipcam_json') or '{}').get('timelapse')=='enable')==bool(args['enabled'])
    except Exception:return False

def _verify_camera_resolution(db,args):
    try:return str(json.loads(_latest(db).get('ipcam_json') or '{}').get('resolution','')).lower()==str(args['resolution']).lower()
    except Exception:return False

def _verify_ams_dry_stopped(db,args):
    try:
        unit=(json.loads(_latest(db).get('ams_json') or '{}').get('ams') or [{}])[0]
        return int(unit.get('dry_time') or 0)<=0
    except Exception:return False

def _verify_ams_filament(db,args):
    try:
        top=json.loads(_latest(db).get('ams_json') or '{}'); unit=next(x for x in (top.get('ams') or []) if int(x.get('id',-1))==int(args['ams_id']))
        tray=next(x for x in (unit.get('tray') or []) if int(x.get('id',-1))==int(args['slot_id']))
        return str(tray.get('tray_type','')).upper()==str(args['material']).upper() and str(tray.get('tray_color','')).upper().startswith(str(args['color']).lstrip('#').upper()[:6])
    except Exception:return False

SPECS={
 'print.pause':CommandSpec('print.pause','low','supported_unverified',_simple_print('pause'),_verify_pause,qos=1),
 'print.resume':CommandSpec('print.resume','low','supported_unverified',_simple_print('resume'),_verify_resume,qos=1),
 'print.stop':CommandSpec('print.stop','destructive','supported_unverified',_simple_print('stop'),_verify_stop,'destructive',qos=1),
 'printer.speed':CommandSpec('printer.speed','low','supported_unverified',_speed,_verify_speed),
 'printer.light':CommandSpec('printer.light','low','supported_verified',_light,_verify_light),
 'printer.fan':CommandSpec('printer.fan','medium','supported_unverified',_fan,_verify_fan),
 'printer.nozzle_temp':CommandSpec('printer.nozzle_temp','thermal','supported_verified',_nozzle,_verify_nozzle,'thermal',qos=1),
 'printer.bed_temp':CommandSpec('printer.bed_temp','thermal','supported_verified',_bed,_verify_bed,'thermal'),
 'printer.chamber_temp':CommandSpec('printer.chamber_temp','thermal','supported_unverified',_chamber,_verify_chamber,'thermal',qos=1),
 'camera.recording':CommandSpec('camera.recording','low','supported_verified',_camera_toggle('ipcam_record_set'),_verify_camera_record),
 'camera.timelapse':CommandSpec('camera.timelapse','low','supported_verified',_camera_toggle('ipcam_timelapse'),_verify_camera_timelapse),
 'camera.resolution':CommandSpec('camera.resolution','low','supported_verified',_camera_resolution,_verify_camera_resolution),
 'ams.rfid_read':CommandSpec('ams.rfid_read','read','supported_verified',_ams_rfid,None,'writes'),
 'ams.control':CommandSpec('ams.control','medium','supported_unverified',_ams_control,None,'ams'),
 'ams.stop_drying':CommandSpec('ams.stop_drying','medium','supported_unverified',_ams_stop_dry,_verify_ams_dry_stopped,'ams'),
 'ams.filament_setting':CommandSpec('ams.filament_setting','medium','supported_unverified',_ams_filament_setting,_verify_ams_filament,'ams'),
 'ams.change_filament':CommandSpec('ams.change_filament','mechanical','supported_unverified',_ams_change,None,'ams'),
}


def capabilities()->dict:
    policies={'writes':_env_bool('PRINTBENCH_CONTROL_WRITES',False),'destructive':_env_bool('PRINTBENCH_CONTROL_DESTRUCTIVE',False),
              'thermal':_env_bool('PRINTBENCH_CONTROL_THERMAL',False),'ams':_env_bool('PRINTBENCH_CONTROL_AMS',False)}
    out={}
    for name,s in SPECS.items():
        enabled=policies['writes'] and policies.get(s.policy,True)
        out[name]={'protocol_status':s.protocol_status,'status':s.protocol_status if enabled else 'disabled_by_policy','risk':s.risk,
                   'enabled':enabled,'post_state_verifier':s.verifier is not None}
    return out


def preview(name,args=None):
    s=SPECS.get(name)
    if not s:raise ValueError('unsupported command')
    payload=s.builder(dict(args or {}),'PREVIEW');cap=capabilities()[name]
    return {'name':name,'risk':s.risk,'status':cap['status'],'enabled':cap['enabled'],'post_state_verifier':s.verifier is not None,'payload':payload}


def _audit(kind,payload):
    blocked={'access_code','token','password','uid','serial','sn'}
    safe={k:v for k,v in payload.items() if str(k).lower() not in blocked}
    rec={'ts':collector.now_iso(),'kind':kind,'payload':safe}
    try:
        AUDIT_FILE.parent.mkdir(parents=True,exist_ok=True)
        with AUDIT_FILE.open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False,separators=(',',':'))+'\n')
        try:os.chmod(AUDIT_FILE,0o600)
        except Exception:pass
    except Exception as e:raise RuntimeError(f'control audit unavailable: {e}')


def _find_sequence(raw:Any,seq:str):
    if not isinstance(raw,dict):return None
    for value in raw.values():
        if isinstance(value,dict) and str(value.get('sequence_id',value.get('sequenceId','')))==seq:return value
    return None


def execute(name,args=None,confirm=False,timeout=8.0,verify_timeout=12.0):
    global _LAST_SEND
    spec=SPECS.get(name)
    if not spec:raise ValueError('unsupported command')
    args=dict(args or {});seq=str(int(time.time()*1000));payload=spec.builder(args,seq);cap=capabilities()[name]
    if not cap['enabled']:raise PermissionError(f'{name} disabled by local policy')
    if spec.risk=='destructive' and not confirm:raise PermissionError('explicit confirmation required')
    db=_db_open_readonly();state=_latest(db)
    if not _state_fresh(state):db.close();raise RuntimeError('printer telemetry is stale')
    with _LOCK:
        delay=max(0.0,spec.min_interval-(time.monotonic()-_LAST_SEND))
        if delay:time.sleep(delay)
        serial,code=collector.load_local_bambu_identity();req,report=f'device/{serial}/request',f'device/{serial}/report';event=threading.Event();answer={}
        client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,protocol=mqtt.MQTTv311);client.username_pw_set('bblp',code)
        client.tls_set_context(bambu_tls.mqtt_context())
        def on_connect(c,u,flags,reason,props):
            if getattr(reason,'is_failure',False):return
            c.subscribe(report);c.publish(req,json.dumps(payload,separators=(',',':')),qos=spec.qos)
        def on_message(c,u,m):
            try:
                raw=json.loads(m.payload.decode('utf-8','ignore'));matched=_find_sequence(raw,seq)
                if matched is not None:answer.update(matched);event.set()
            except Exception:pass
        client.on_connect=on_connect;client.on_message=on_message;_audit('control_requested',{'name':name,'args':args,'sequence_id':seq,'risk':spec.risk})
        client.connect(collector.P2S_HOST,8883,keepalive=20);client.loop_start()
        try:got=event.wait(max(1.0,min(float(timeout),20.0)))
        finally:
            client.loop_stop()
            try:client.disconnect()
            except Exception:pass
        _LAST_SEND=time.monotonic()
    word=str(answer.get('result','')).lower();positive=bool(got and word not in {'fail','failed','error'});verified=False
    if spec.verifier:
        end=time.monotonic()+max(1.0,min(float(verify_timeout),30.0))
        while time.monotonic()<end:
            if spec.verifier(db,args):verified=True;break
            time.sleep(.5)
    ok=bool(verified if spec.verifier else positive)
    result={'ok':ok,'name':name,'sequence_id':seq,'response_received':bool(got),'response_positive':positive,'post_state_verified':verified,
            'verification':'post_state' if verified else ('response_only' if positive else 'unverified'),'protocol_status':spec.protocol_status}
    _audit('control_result',result);db.close();return result
