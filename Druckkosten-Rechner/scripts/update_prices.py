#!/usr/bin/env python3
import json,re,sys
from pathlib import Path
from datetime import datetime,timezone
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data'/'filaments.json'
MATERIALS=['pla','pla+','petg','abs','asa','tpu']
ALIASES={'sunlu':'SUNLU','jayo':'JAYO','esun':'eSUN','geeetech':'GEEETECH','anycubic':'Anycubic','elegoo':'Elegoo','bambu lab':'Bambu Lab','polymaker':'Polymaker','prusament':'Prusament','extrudr':'Extrudr','fiberlogy':'Fiberlogy','creality':'Creality','kingroon':'KINGROON'}
HEADERS={'User-Agent':'3d-Files-price-updater/1.0 (+https://github.com/jygnw29kms-bit/3d-Files)'}

def norm_price(text):
    m=re.search(r'(\d{1,3}(?:[.,]\d{1,2})?)\s*€\s*/\s*kg',text,re.I)
    return float(m.group(1).replace(',','.')) if m else None

def fetch_material(material):
    url='https://spulenheld.de/deals/'+material.replace('+','plus')
    r=requests.get(url,headers=HEADERS,timeout=25);r.raise_for_status()
    soup=BeautifulSoup(r.text,'html.parser')
    candidates=[]
    # Server-rendered cards/headings are intentionally parsed loosely so minor layout changes do not break everything.
    for node in soup.find_all(['article','li','div']):
        txt=' '.join(node.stripped_strings)
        p=norm_price(txt)
        if p is None or p<3 or p>100: continue
        low=txt.lower();brand=None
        for token,canonical in ALIASES.items():
            if token in low: brand=canonical;break
        if brand: candidates.append((brand,p,url))
    best={}
    for brand,p,url in candidates:
        if brand not in best or p<best[brand][0]:best[brand]=(p,url)
    return best

def main():
    data=json.loads(DB.read_text(encoding='utf-8'))
    by_brand={b['name']:b for b in data['brands']}
    observed=[]
    for m in MATERIALS:
        key=m.upper().replace('PLUS','+')
        try: found=fetch_material(m)
        except Exception as e:
            print(f'WARN {m}: {e}',file=sys.stderr);continue
        for brand,(price,url) in found.items():
            if brand in by_brand:
                by_brand[brand]['materials'][key]=round(price,2)
                observed.append({'brand':brand,'material':key,'eur_per_kg':round(price,2),'source':'Spulenheld','url':url})
    data['updated']=datetime.now(timezone.utc).isoformat(timespec='seconds')
    data['market_observations']=observed
    DB.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'updated {len(observed)} brand/material prices')

if __name__=='__main__': main()
