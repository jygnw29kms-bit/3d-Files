from __future__ import annotations
import argparse, json, time
from pathlib import Path
from typing import Any
import collector
import external_tag
import reader_contract

MAX_LINE_BYTES=4096
PROTOCOL_VERSION=1


def parse_message(raw:bytes|str)->dict[str,Any]:
    if isinstance(raw,bytes):
        if len(raw)>MAX_LINE_BYTES:raise ValueError('reader message too large')
        text=raw.decode('utf-8','strict')
    else:
        text=str(raw)
        if len(text.encode('utf-8'))>MAX_LINE_BYTES:raise ValueError('reader message too large')
    obj=json.loads(text)
    if not isinstance(obj,dict):raise ValueError('reader message must be object')
    if int(obj.get('version',0))!=PROTOCOL_VERSION:raise ValueError('unsupported reader protocol version')
    payload=obj.get('payload') if isinstance(obj.get('payload'),dict) else {}
    if len(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8'))>2048:raise ValueError('reader payload too large')
    checked=reader_contract.validate(reader_contract.TagObservation(
        str(obj.get('reader_id') or 'esp32-reader'),str(obj.get('ams_id') or '0'),str(obj.get('slot_id','')),
        str(obj.get('uid','')),str(obj.get('tag_type') or 'unknown'),payload))
    return {'version':PROTOCOL_VERSION,'reader_id':checked.reader_id,'ams_id':checked.ams_id,'slot_id':checked.slot_id,
            'uid':checked.uid,'tag_type':checked.tag_type,'payload':checked.payload}


def process_message(db,raw:bytes|str)->dict[str,Any]:
    m=parse_message(raw)
    return external_tag.observe(db,uid=m['uid'],ams_id=m['ams_id'],slot_id=m['slot_id'],reader_id=m['reader_id'],tag_type=m['tag_type'],parsed=m['payload'])


def run_forever(port:str,baud:int=115200)->None:
    try:import serial
    except Exception as exc:raise RuntimeError('python3-serial is required for reader_serial') from exc
    while True:
        try:
            with serial.Serial(port,baudrate=baud,timeout=2,write_timeout=2) as dev:
                print(f'[PRINTBENCH READER] connected port={Path(port).name} baud={baud}',flush=True)
                db=collector.db_open()
                try:
                    while True:
                        raw=dev.readline(MAX_LINE_BYTES+1)
                        if not raw:continue
                        try:
                            result=process_message(db,raw.rstrip(b'\r\n'))
                            print(f"[PRINTBENCH READER] slot={int(result['slot_id'])+1} matched={str(result['matched']).lower()} spool={result.get('spool_id') or '-'}",flush=True)
                        except Exception as exc:
                            print(f'[PRINTBENCH READER] rejected {type(exc).__name__}',flush=True)
                finally:db.close()
        except KeyboardInterrupt:raise
        except Exception as exc:
            print(f'[PRINTBENCH READER] transport unavailable ({type(exc).__name__}); retry',flush=True)
            time.sleep(3)


def main()->None:
    p=argparse.ArgumentParser(description='PRINTBENCH external NFC reader serial bridge')
    p.add_argument('--port',default='/dev/ttyACM0');p.add_argument('--baud',type=int,default=115200)
    a=p.parse_args();run_forever(a.port,a.baud)


if __name__=='__main__':main()
