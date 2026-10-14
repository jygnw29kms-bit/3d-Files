from __future__ import annotations
import json, ssl, threading, time
from pathlib import Path
from typing import Any
import paho.mqtt.client as mqtt
import collector

ROOT=Path(__file__).resolve().parent
CONFIG=ROOT/'ams_control.json'
DEFAULT_IDS={
    'PLA':'GFL99','PETG':'GFG99','TPU':'GFU99','PVA':'GFS99','PLA-CF':'GFL98',
    'PC':'GFC99','PA':'GFN99','PA-CF':'GFN98','ASA':'GFB98','ABS':'GFB99'
}

def load_config():
    data={'schema':1,'write_enabled':False,'command_timeout_sec':8,'generic_filament_ids':dict(DEFAULT_IDS)}
    try:
        raw=json.loads(CONFIG.read_text(encoding='utf-8'))
        if isinstance(raw,dict):
            ids=dict(DEFAULT_IDS); ids.update(raw.get('generic_filament_ids') or {})
            data.update(raw); data['generic_filament_ids']=ids
    except Exception: pass
    return data

def _idx(v,name):
    try:n=int(v)
    except Exception:raise ValueError(f'{name} must be integer 0..3')
    if not 0<=n<=3:raise ValueError(f'{name} must be 0..3')
    return n

def normalize_color(v):
    s=str(v or '').strip().lstrip('#').upper()
    if len(s)==6:s+='FF'
    if len(s)!=8 or any(c not in '0123456789ABCDEF' for c in s):raise ValueError('color must be RRGGBB or RRGGBBAA')
    return s[:6]+'FF'

def generic_filament_id(material):
    m=str(material or '').strip().upper()
    return (load_config().get('generic_filament_ids') or {}).get(m)

def build_rfid_read(ams_id,slot_id,sequence_id=None):
    return {'print':{'sequence_id':str(sequence_id or int(time.time()*1000)),'command':'ams_get_rfid','ams_id':_idx(ams_id,'ams_id'),'slot_id':_idx(slot_id,'slot_id')}}

def build_filament_setting(ams_id,tray_id,material,color,nozzle_temp_min,nozzle_temp_max,tray_info_idx=None,sequence_id=None):
    mat=str(material or '').strip().upper()
    if not mat:raise ValueError('material required')
    info=str(tray_info_idx or generic_filament_id(mat) or '').strip()
    if not info:raise ValueError(f'no verified generic tray_info_idx for {mat}; provide one explicitly')
    lo=int(float(nozzle_temp_min)); hi=int(float(nozzle_temp_max))
    if not 0<=lo<=400 or not 0<=hi<=400 or lo>hi:raise ValueError('invalid nozzle temperature range')
    return {'print':{
        'sequence_id':str(sequence_id or int(time.time()*1000)),
        'command':'ams_filament_setting','ams_id':_idx(ams_id,'ams_id'),'tray_id':_idx(tray_id,'tray_id'),
        'tray_info_idx':info,'tray_color':normalize_color(color),'nozzle_temp_min':lo,'nozzle_temp_max':hi,'tray_type':mat
    }}

def send(command:dict,apply=False,timeout=None):
    cfg=load_config(); payload=json.loads(json.dumps(command))
    if not apply:return {'ok':True,'dry_run':True,'payload':payload}
    if not cfg.get('write_enabled',False):raise RuntimeError('AMS writes are disabled in ams_control.json')
    serial,code=collector.load_local_bambu_identity(); req=f'device/{serial}/request'; report=f'device/{serial}/report'
    wanted=str(payload.get('print',{}).get('sequence_id','')); event=threading.Event(); answer={}
    client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,protocol=mqtt.MQTTv311)
    client.username_pw_set('bblp',code); client.tls_set(cert_reqs=ssl.CERT_NONE); client.tls_insecure_set(True)
    def on_connect(c,u,flags,reason,props):
        if getattr(reason,'is_failure',False):return
        c.subscribe(report); c.publish(req,json.dumps(payload,separators=(',',':')))
    def on_message(c,u,m):
        try:
            raw=json.loads(m.payload.decode('utf-8','ignore')); p=raw.get('print') if isinstance(raw,dict) else None
            if isinstance(p,dict) and (str(p.get('sequence_id',''))==wanted or str(p.get('sequenceId',''))==wanted):answer.update(raw);event.set()
        except Exception:pass
    client.on_connect=on_connect;client.on_message=on_message
    wait=float(timeout or cfg.get('command_timeout_sec',8));client.connect(collector.P2S_HOST,8883,keepalive=20);client.loop_start()
    try:
        if not event.wait(wait):return {'ok':False,'dry_run':False,'timeout':True,'payload':payload}
        return {'ok':True,'dry_run':False,'payload':payload,'response':answer}
    finally:
        client.loop_stop()
        try:client.disconnect()
        except Exception:pass