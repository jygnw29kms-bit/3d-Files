from __future__ import annotations
import json, shutil, sqlite3, subprocess, threading, time
from datetime import datetime, timezone
from pathlib import Path
import requests
import collector

ROOT=Path(__file__).resolve().parent
MEDIA=ROOT/'media'
FRAMES=MEDIA/'timelapse_frames'
TOKEN_FILE=ROOT/'.push-token'
INGEST='https://www.dezender.de/3d-druck/media-ingest.php'
ACTIVE_STATES={'RUNNING','PRINTING','PREPARE','SLICING','PAUSE','PAUSED'}
STOP_STATES={'FINISH','FAILED','CANCEL','CANCELED','IDLE'}

def now_tag(): return datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
def media_url():
    _,code=collector.load_local_bambu_identity()
    return 'rtsps://bblp:'+code+'@'+collector.P2S_HOST+':322/streaming/live/1'

def post_file(path:Path,kind:str,timeout=30):
    if not path.exists() or path.stat().st_size<1024 or not TOKEN_FILE.exists(): return None
    token=TOKEN_FILE.read_text(encoding='utf-8').strip()
    ctype='image/jpeg' if path.suffix.lower() in ('.jpg','.jpeg') else 'video/mp4'
    with path.open('rb') as f:
        r=requests.post(INGEST,params={'kind':kind},data=f,headers={'X-PRINTBENCH-TOKEN':token,'Content-Type':ctype,'User-Agent':'PRINTBENCH-Media/1.0'},timeout=timeout)
    r.raise_for_status(); return r.json()

def latest_state():
    try:
        db=sqlite3.connect(collector.DB); r=db.execute('select print_state,progress,layer_current,layer_total,ts from telemetry where print_state is not null order by id desc limit 1').fetchone(); db.close()
        return {'state':str(r[0] or '').upper(),'progress':r[1],'layer':r[2],'layer_total':r[3],'ts':r[4]} if r else {}
    except Exception: return {}

def start_ffmpeg():
    MEDIA.mkdir(parents=True,exist_ok=True)
    url=media_url(); snap=MEDIA/'latest.jpg'; pattern=str(MEDIA/'live-%d.mp4')
    cmd=['ffmpeg','-hide_banner','-loglevel','warning','-rtsp_transport','tcp','-tls_verify','0','-i',url,
         '-map','0:v:0','-vf','fps=1/2','-q:v','3','-update','1','-y',str(snap),
         '-map','0:v:0','-an','-c:v','copy','-f','segment','-segment_time','30','-reset_timestamps','1','-segment_wrap','3','-segment_format','mp4',pattern]
    return subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def newest_closed_clip():
    fs=sorted(MEDIA.glob('live-*.mp4'),key=lambda p:p.stat().st_mtime,reverse=True)
    now=time.time()
    for p in fs:
        if p.stat().st_size>100000 and now-p.stat().st_mtime>2: return p
    return None

def active_session_dir():
    marker=MEDIA/'active-session.txt'
    if marker.exists():
        p=Path(marker.read_text(encoding='utf-8').strip())
        if p.exists(): return p
    p=FRAMES/now_tag(); p.mkdir(parents=True,exist_ok=True); marker.parent.mkdir(parents=True,exist_ok=True); marker.write_text(str(p),encoding='utf-8'); return p

def clear_session_marker():
    try:(MEDIA/'active-session.txt').unlink()
    except FileNotFoundError: pass

def add_timelapse_frame(snap:Path):
    if not snap.exists() or snap.stat().st_size<5000:return None
    d=active_session_dir(); n=len(list(d.glob('frame-*.jpg')))+1; dst=d/f'frame-{n:06d}.jpg'; shutil.copy2(snap,dst); return dst

def finalize_timelapse():
    marker=MEDIA/'active-session.txt'
    if not marker.exists(): return None
    d=Path(marker.read_text(encoding='utf-8').strip())
    frames=sorted(d.glob('frame-*.jpg')) if d.exists() else []
    clear_session_marker()
    if len(frames)<3:return None
    out=MEDIA/f'timelapse-{d.name}.mp4'
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-framerate','12','-i',str(d/'frame-%06d.jpg'),'-c:v','libx264','-preset','veryfast','-crf','22','-pix_fmt','yuv420p','-movflags','+faststart','-y',str(out)]
    r=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=180)
    if r.returncode==0 and out.exists() and out.stat().st_size>10000:
        post_file(out,'timelapse',timeout=120); return out
    return None

def run_forever(stop_event:threading.Event|None=None):
    stop_event=stop_event or threading.Event(); proc=None; last_snap_push=0.; last_clip_mtime=0.; last_frame=0.; was_active=False; last_restart=0.
    while not stop_event.wait(1):
        now=time.time()
        if proc is None or proc.poll() is not None:
            if now-last_restart<5: continue
            last_restart=now
            try: proc=start_ffmpeg(); print('[PRINTBENCH] MEDIA ffmpeg started',flush=True)
            except Exception as e: print('[PRINTBENCH] MEDIA start warning:',e,flush=True); continue
        snap=MEDIA/'latest.jpg'
        if snap.exists() and snap.stat().st_size>5000 and now-last_snap_push>=5:
            try: post_file(snap,'snapshot',timeout=15); last_snap_push=now
            except Exception as e:
                if int(now)%30<2: print('[PRINTBENCH] MEDIA snapshot warning:',e,flush=True)
        clip=newest_closed_clip()
        if clip and clip.stat().st_mtime>last_clip_mtime:
            try: post_file(clip,'clip',timeout=60); last_clip_mtime=clip.stat().st_mtime; print('[PRINTBENCH] MEDIA clip pushed',flush=True)
            except Exception as e: print('[PRINTBENCH] MEDIA clip warning:',e,flush=True)
        st=latest_state(); state=st.get('state',''); active=(state in ACTIVE_STATES) or (state not in STOP_STATES and (st.get('progress') or 0)>0 and (st.get('progress') or 0)<100)
        if active and now-last_frame>=15:
            try: add_timelapse_frame(snap); last_frame=now
            except Exception as e: print('[PRINTBENCH] MEDIA frame warning:',e,flush=True)
        if was_active and not active and state in STOP_STATES:
            try:
                t=finalize_timelapse()
                if t: print('[PRINTBENCH] MEDIA timelapse ready '+t.name,flush=True)
            except Exception as e: print('[PRINTBENCH] MEDIA timelapse warning:',e,flush=True)
        was_active=active
    if proc and proc.poll() is None:
        try: proc.terminate(); proc.wait(timeout=5)
        except Exception:
            try: proc.kill()
            except Exception: pass

if __name__=='__main__': run_forever()
