from __future__ import annotations
import argparse, json
import collector, ams_rfid_diag

p=argparse.ArgumentParser(description='Local PRINTBENCH AMS/RFID diagnostics; never uploads UID data.')
p.add_argument('--limit',type=int,default=40)
a=p.parse_args()
db=collector.db_open(); ams_rfid_diag.ensure_schema(db)
print(json.dumps(ams_rfid_diag.recent(db,a.limit),ensure_ascii=False,indent=2))
db.close()