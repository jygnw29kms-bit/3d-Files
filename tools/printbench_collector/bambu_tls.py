from __future__ import annotations
import hashlib, os, socket, ssl
from pathlib import Path

DEFAULT_PIN=Path('/etc/printbench/p2s-cert.pem')

def pin_path()->Path:
    return Path(os.environ.get('PRINTBENCH_P2S_CERT',str(DEFAULT_PIN)))

def fetch_leaf_pem(host:str,port:int=8883,timeout:float=6.0)->tuple[str,str]:
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE
    raw=socket.create_connection((host,int(port)),timeout=timeout)
    try:
        with ctx.wrap_socket(raw,server_hostname=host) as s:
            der=s.getpeercert(binary_form=True)
    finally:
        try:raw.close()
        except Exception:pass
    if not der:raise RuntimeError('printer returned no TLS certificate')
    return ssl.DER_cert_to_PEM_cert(der),hashlib.sha256(der).hexdigest()

def write_pin(host:str,out:Path|None=None)->dict:
    out=Path(out or pin_path());pem,sha=fetch_leaf_pem(host)
    out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.with_name(out.name+'.tmp');tmp.write_text(pem,encoding='ascii');os.chmod(tmp,0o640);tmp.replace(out)
    return {'path':str(out),'sha256':sha}

def mqtt_context()->ssl.SSLContext:
    pin=pin_path()
    if not pin.is_file():
        if os.environ.get('PRINTBENCH_TLS_ALLOW_UNPINNED','').strip().lower() in {'1','true','yes','on'}:
            ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT);ctx.check_hostname=False;ctx.verify_mode=ssl.CERT_NONE;return ctx
        raise RuntimeError(f'P2S TLS pin missing: {pin}')
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname=False
    ctx.verify_mode=ssl.CERT_REQUIRED
    ctx.verify_flags|=getattr(ssl,'VERIFY_X509_PARTIAL_CHAIN',0)
    ctx.load_verify_locations(cafile=str(pin))
    return ctx
