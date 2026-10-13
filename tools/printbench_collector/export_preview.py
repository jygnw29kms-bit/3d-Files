from __future__ import annotations
import json, os, re, sqlite3
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parent;DB=ROOT/'printbench.db';OUT=ROOT/'preview'/'data.json';BAMBU_TEMP=Path(os.environ.get('LOCALAPPDATA',''))/'Temp'/'bamboo_model'
def cfg_value(text,key,cast=float):
    m=re.search(r'"'+re.escape(key)+r'"\s*:\s*(?:\[\s*)?"?([0-9.]+)',text,re.I)
    if not m:return None
    try:return cast(m.group(1))
    except:return None
def slicer_speeds():
    if not BAMBU_TEMP.exists():return {}
    cfgs=sorted(BAMBU_TEMP.rglob('_temp_*.config'),key=lambda p:p.stat().st_mtime,reverse=True)[:8]
    texts=[p.read_text(encoding='utf-8',errors='ignore') for p in cfgs]
    all_text='\n'.join(texts)
    filament_text=next((t for t in texts if 'KINGROON' in t),all_text)
    return {'outer_wall':cfg_value(all_text,'outer_wall_speed'),'inner_wall':cfg_value(all_text,'inner_wall_speed'),'infill':cfg_value(all_text,'sparse_infill_speed'),'travel':cfg_value(all_text,'travel_speed'),'max_volumetric':cfg_value(filament_text,'filament_max_volumetric_speed')}
def main():
    db=sqlite3.connect(DB);db.row_factory=sqlite3.Row
    live=db.execute('''SELECT ts,print_state,progress,remaining_min,layer_current,layer_total,nozzle_c,nozzle_target_c,bed_c,bed_target_c,chamber_c,wifi_rssi,speed_level,speed_mag,fan_part,fan_aux,fan_chamber,fan_heatbreak,print_stage,print_sub_stage,ipcam_json,hms_json,print_error,fail_reason,ams_json FROM telemetry WHERE print_state IS NOT NULL OR nozzle_c IS NOT NULL OR progress IS NOT NULL OR speed_mag IS NOT NULL ORDER BY id DESC LIMIT 1''').fetchone()
    if not live:raise SystemExit('No telemetry available')
    history=db.execute('''SELECT ts,progress,remaining_min,layer_current,layer_total,nozzle_c,nozzle_target_c,bed_c,bed_target_c,chamber_c,wifi_rssi,speed_level FROM telemetry ORDER BY id DESC LIMIT 360''').fetchall()[::-1]
    slicer=db.execute('''SELECT detected_at,origin_path,slicer,model_time_sec,total_time_sec,layer_count,filament_g,filament_m,filament_type,filament_vendor,filament_profile,density,diameter,nozzle_diameter,nozzle_type,layer_height,infill_percent,infill_pattern,wall_loops,bed_type FROM slicer_jobs ORDER BY id DESC LIMIT 1''').fetchone();slicer_data=dict(slicer) if slicer else {}
    if slicer_data.get('origin_path'):slicer_data['origin_path']=Path(slicer_data['origin_path']).name
    slicer_data['speeds']=slicer_speeds()
    ams_raw=json.loads(live['ams_json']) if live['ams_json'] else {};unit=(ams_raw.get('ams') or [{}])[0];active_raw=str(ams_raw.get('tray_now',''));active=None if active_raw in ('','255','-1') else active_raw;tray=next((t for t in unit.get('tray',[]) if str(t.get('id'))==str(active)),{})
    ams={'unit':unit.get('id'),'active_slot':active,'temp_c':float(unit['temp']) if str(unit.get('temp','')).replace('.','',1).isdigit() else None,'humidity_level':unit.get('humidity'),'humidity_raw':float(unit['humidity_raw']) if str(unit.get('humidity_raw','')).replace('.','',1).isdigit() else None,'material':tray.get('tray_type'),'color':tray.get('tray_color'),'remain':tray.get('remain'),'tag_uid_present':bool(tray.get('tag_uid') and tray.get('tag_uid')!='0000000000000000'),'drying':bool(unit.get('dry_time',0) and unit.get('dry_time',0)>0),'dry_time':unit.get('dry_time',0)}
    ipcam=json.loads(live['ipcam_json']) if live['ipcam_json'] else {};hms=json.loads(live['hms_json']) if live['hms_json'] else []
    live_safe={k:live[k] for k in live.keys() if k not in ('ams_json','ipcam_json','hms_json')};live_safe['camera']={'liveview':bool(ipcam.get('liveview_preview')),'resolution':ipcam.get('resolution'),'recording':ipcam.get('ipcam_record')=='enable'};live_safe['hms_count']=len(hms) if isinstance(hms,list) else 0
    stats=db.execute('''SELECT COUNT(*) samples,MIN(nozzle_c) nozzle_min,MAX(nozzle_c) nozzle_max,AVG(nozzle_c) nozzle_avg,MIN(bed_c) bed_min,MAX(bed_c) bed_max,AVG(bed_c) bed_avg,MIN(progress) progress_min,MAX(progress) progress_max,MIN(ts) first_ts,MAX(ts) last_ts FROM telemetry''').fetchone()
    rows=db.execute('''SELECT detected_at,origin_path,slicer,total_time_sec,layer_count,filament_g,filament_m,filament_type,filament_vendor,filament_profile,layer_height,infill_percent,infill_pattern,wall_loops,bed_type FROM slicer_jobs ORDER BY id DESC LIMIT 12''').fetchall();jobs=[]
    for r in rows:
        x=dict(r);x['origin_path']=Path(x['origin_path']).name if x.get('origin_path') else None;jobs.append(x)
    payload={'generated_at':datetime.now(timezone.utc).isoformat(),'source':'PRINTBENCH Collector / P2S LAN MQTT + Bambu Studio','live':live_safe,'ams':ams,'slicer':slicer_data,'history':[dict(r) for r in history],'sample_count':db.execute('SELECT COUNT(*) FROM telemetry').fetchone()[0],'stats':dict(stats),'jobs':jobs}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8');print(f'PREVIEW_DATA_OK samples={len(history)} total={payload["sample_count"]}')
if __name__=='__main__':main()