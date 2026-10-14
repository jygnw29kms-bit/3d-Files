from __future__ import annotations
import os, signal, time
from pathlib import Path
import av
import collector

ROOT=Path(__file__).resolve().parent
RUNTIME=Path(os.environ.get('PRINTBENCH_CAMERA_RUNTIME',ROOT/'runtime'/'camera'))
SNAPSHOT=RUNTIME/'latest.jpg'
TMP=RUNTIME/'latest.tmp.jpg'
VIEWER_MARK=RUNTIME/'viewer.active'
STOP=False


def _stop(*_):
    global STOP
    STOP=True


def camera_url()->str:
    _,code=collector.load_local_bambu_identity()
    return f'rtsps://bblp:{code}@{collector.P2S_HOST}:322/streaming/live/1'


def viewer_active(max_age=4.0)->bool:
    try:return VIEWER_MARK.is_file() and time.time()-VIEWER_MARK.stat().st_mtime<max_age
    except Exception:return False


def _jpeg_bytes(frame)->bytes:
    codec=av.CodecContext.create('mjpeg','w');codec.width=frame.width;codec.height=frame.height;codec.pix_fmt='yuvj420p';codec.open()
    src=frame.reformat(format='yuvj420p')
    return b''.join(bytes(p) for p in [*codec.encode(src),*codec.encode(None)])


def _write_frame(frame)->int:
    RUNTIME.mkdir(parents=True,exist_ok=True)
    raw=_jpeg_bytes(frame)
    if len(raw)<5000 or not raw.startswith(b'\xff\xd8'):raise RuntimeError('invalid JPEG frame')
    TMP.write_bytes(raw);TMP.replace(SNAPSHOT);return len(raw)


def capture_once()->int:
    with av.open(camera_url(),options={'rtsp_transport':'tcp'},timeout=12) as container:
        stream=container.streams.video[0]
        try:stream.codec_context.skip_frame='NONKEY'
        except Exception:pass
        for frame in container.decode(stream):return _write_frame(frame)
    raise RuntimeError('camera returned no frame')


def stream_while_viewed(interval:float)->None:
    with av.open(camera_url(),options={'rtsp_transport':'tcp'},timeout=12) as container:
        stream=container.streams.video[0]
        try:stream.codec_context.skip_frame='NONKEY'
        except Exception:pass
        last=0.0
        for frame in container.decode(stream):
            if STOP or not viewer_active():return
            now=time.monotonic()
            if now-last>=interval:_write_frame(frame);last=now
        if not STOP:raise RuntimeError('camera stream ended')


def _sleep(seconds:float)->None:
    end=time.monotonic()+seconds
    while not STOP and time.monotonic()<end:time.sleep(min(.5,end-time.monotonic()))


def run_forever(active_interval=1.0,idle_interval=60.0)->None:
    signal.signal(signal.SIGTERM,_stop);signal.signal(signal.SIGINT,_stop)
    failures=0;last_idle=0.0
    while not STOP:
        try:
            if viewer_active():
                stream_while_viewed(active_interval);failures=0;continue
            now=time.monotonic()
            if not SNAPSHOT.exists() or now-last_idle>=idle_interval:
                capture_once();last_idle=time.monotonic();failures=0
            _sleep(1.0)
        except Exception as exc:
            failures+=1
            print(f'[PRINTBENCH CAMERA] capture failed ({type(exc).__name__}); retry {failures}',flush=True)
            _sleep(min(30.0,max(2.0,2.0*failures)))


if __name__=='__main__':
    run_forever(max(.5,float(os.environ.get('PRINTBENCH_CAMERA_INTERVAL','1.0'))),max(10.0,float(os.environ.get('PRINTBENCH_CAMERA_IDLE_INTERVAL','60.0'))))
