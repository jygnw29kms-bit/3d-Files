from __future__ import annotations
import argparse,json
import ams_control

p=argparse.ArgumentParser(description='PRINTBENCH AMS control. Dry-run by default; writes require config opt-in.')
sub=p.add_subparsers(dest='cmd',required=True)
r=sub.add_parser('read-rfid');r.add_argument('ams_id',type=int);r.add_argument('slot_id',type=int);r.add_argument('--apply',action='store_true')
f=sub.add_parser('set-filament');f.add_argument('ams_id',type=int);f.add_argument('slot_id',type=int);f.add_argument('--material',required=True);f.add_argument('--color',required=True);f.add_argument('--min-temp',type=int,required=True);f.add_argument('--max-temp',type=int,required=True);f.add_argument('--tray-info-idx');f.add_argument('--apply',action='store_true')
a=p.parse_args()
if a.cmd=='read-rfid': payload=ams_control.build_rfid_read(a.ams_id,a.slot_id)
else: payload=ams_control.build_filament_setting(a.ams_id,a.slot_id,a.material,a.color,a.min_temp,a.max_temp,a.tray_info_idx)
try:
    result=ams_control.send(payload,apply=a.apply)
    print(json.dumps(result,ensure_ascii=False,indent=2))
except Exception as e:
    print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False,indent=2))
    raise SystemExit(2)