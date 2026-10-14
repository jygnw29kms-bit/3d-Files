from __future__ import annotations
import argparse,json
from pathlib import Path
import bambu_tls

def main()->int:
    p=argparse.ArgumentParser(description='Pin the current P2S MQTT leaf certificate during explicit local pairing.')
    p.add_argument('--host',required=True)
    p.add_argument('--out',default=str(bambu_tls.pin_path()))
    ns=p.parse_args()
    info=bambu_tls.write_pin(ns.host,Path(ns.out))
    print(json.dumps({'ok':True,'sha256':info['sha256'],'path':info['path']},separators=(',',':')))
    return 0

if __name__=='__main__':raise SystemExit(main())
