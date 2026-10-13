from __future__ import annotations
import ftplib, re, socket, ssl
from pathlib import Path
import requests
import collector, server_transport

ROOT=Path(__file__).resolve().parent
LOCAL=ROOT/'media'/'native'
TOKEN_FILE=ROOT/'.push-token'
INGEST='https://www.dezender.de/3d-druck/media-ingest.php'
VIDEO_RE=re.compile(r'^video_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.mp4$')
THUMB_RE=re.compile(r'^video_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(?:_mini)?\.jpg$')

class ImplicitFTP_TLS(ftplib.FTP_TLS):
    def ntransfercmd(self, cmd, rest=None):
        conn,size=ftplib.FTP.ntransfercmd(self,cmd,rest)
        if self._prot_p:
            conn=self.context.wrap_socket(conn,server_hostname=self.host,session=self.sock.session)
        return conn,size
    def connect(self,host='',port=0,timeout=-999,source_address=None):
        if host:self.host=host
        if port:self.port=port
        if timeout != -999:self.timeout=timeout
        self.source_address=source_address
        self.sock=socket.create_connection((self.host,self.port),self.timeout,source_address=self.source_address)
        self.af=self.sock.family; self.sock=self.context.wrap_socket(self.sock,server_hostname=self.host)
        self.file=self.sock.makefile('r',encoding=self.encoding); self.welcome=self.getresp(); return self.welcome

def open_ftp():
    _,code=collector.load_local_bambu_identity(); ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    f=ImplicitFTP_TLS(context=ctx); f.connect(collector.P2S_HOST,990,timeout=8); f.login('bblp',code); f.voidcmd('TYPE I'); f.prot_p(); f.set_pasv(True); return f

def parse_list(rows):
    out=[]
    for row in rows:
        m=re.match(r'^[-dl][rwx-]{9}\s+\d+\s+\S+\s+\S+\s+(\d+)\s+\w+\s+\d+\s+[0-9:]{4,5}\s+(.+)$',row)
        if m:out.append((m.group(2).strip(),int(m.group(1))))
    return out

def list_dir(f,path):
    f.cwd(path); rows=[]; f.retrlines('LIST',rows.append); return parse_list(rows)

def download(f,remote,local,size):
    local.parent.mkdir(parents=True,exist_ok=True)
    if local.exists() and local.stat().st_size==size:return False
    tmp=local.with_suffix(local.suffix+'.tmp')
    with tmp.open('wb') as out:f.retrbinary('RETR '+remote,out.write,blocksize=262144)
    tmp.replace(local); return True

def upload_http(path,kind):
    token=TOKEN_FILE.read_text(encoding='utf-8').strip(); mime='video/mp4' if kind=='native_video' else 'image/jpeg'
    with path.open('rb') as f:r=requests.post(INGEST,params={'kind':kind,'name':path.name},data=f,headers={'X-PRINTBENCH-TOKEN':token,'Content-Type':mime,'User-Agent':'PRINTBENCH-NativeMedia/1.0'},timeout=90)
    r.raise_for_status(); return r.json()

def upload(path,kind):
    try:return upload_http(path,kind)
    except Exception as he:
        if server_transport.available():
            try:
                server_transport.put_file_atomic(path,'media/native/'+path.name,timeout=120); return {'ok':True,'transport':'ssh'}
            except Exception as se:raise RuntimeError(f'https={he}; ssh={se}')
        raise

def sync_native():
    LOCAL.mkdir(parents=True,exist_ok=True); f=open_ftp(); changed=[]; uploaded=[]
    try:
        videos=[x for x in list_dir(f,'/timelapse') if VIDEO_RE.match(x[0])]
        thumbs=[x for x in list_dir(f,'/timelapse/thumbnail') if THUMB_RE.match(x[0])]
        for name,size in videos:
            p=LOCAL/name
            if download(f,'/timelapse/'+name,p,size):changed.append(name)
        for name,size in thumbs:
            p=LOCAL/name
            if download(f,'/timelapse/thumbnail/'+name,p,size):changed.append(name)
    finally:
        try:f.quit()
        except Exception:
            try:f.close()
            except Exception:pass
    for p in sorted(LOCAL.iterdir()):
        if not p.is_file():continue
        marker=p.with_suffix(p.suffix+'.uploaded')
        sig=f'{p.stat().st_size}:{int(p.stat().st_mtime)}'
        if marker.exists() and marker.read_text(encoding='ascii',errors='ignore')==sig:continue
        kind='native_video' if p.suffix.lower()=='.mp4' else 'native_thumb'
        upload(p,kind); marker.write_text(sig,encoding='ascii'); uploaded.append(p.name)
    return {'videos':len(videos),'thumbs':len(thumbs),'downloaded':changed,'uploaded':uploaded}

if __name__=='__main__':print(sync_native())
