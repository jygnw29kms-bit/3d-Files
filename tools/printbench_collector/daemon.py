from __future__ import annotations
import json, os, signal, socket, ssl, threading, time
import paho.mqtt.client as mqtt
import collector
import push_live
import media_worker
import session_tracker
import ams_rfid_diag
import spool_sync
import device_info

STOP = threading.Event()
LOCK_SOCKET = None

def _env_enabled(name: str, default: bool = True) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() not in {'0','false','no','off','disabled'}


def acquire_singleton():
    global LOCK_SOCKET
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', 47651))
        s.listen(1)
        LOCK_SOCKET = s
        return True
    except OSError:
        s.close()
        return False


def main():
    if not acquire_singleton():
        print('[PRINTBENCH] Collector already running; exiting', flush=True)
        return
    db = collector.db_open()
    session_tracker.ensure_schema(db)
    ams_rfid_diag.ensure_schema(db)
    spool_sync.ensure_schema(db)
    device_info.ensure_schema(db)
    serial, code = collector.load_local_bambu_identity()
    topic_report = f'device/{serial}/report'
    topic_req = f'device/{serial}/request'
    state = {'connected': False, 'messages': 0, 'last_ingest': 0.0}

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
    client.username_pw_set('bblp', code)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)

    def on_connect(c, u, flags, reason, props):
        ok = not getattr(reason, 'is_failure', False)
        state['connected'] = ok
        if ok:
            c.subscribe(f'device/{serial}/#')
            c.publish(topic_req, json.dumps({'pushing': {'sequence_id': '0', 'command': 'pushall'}}))
            c.publish(topic_req, json.dumps(device_info.build_version_request(int(time.time()*1000))))
            state['last_version_request'] = time.time()
            print('[PRINTBENCH] MQTT connected', flush=True)
        else:
            print('[PRINTBENCH] MQTT connect failed', flush=True)

    def on_disconnect(c, u, flags, reason, props):
        state['connected'] = False
        if not STOP.is_set():
            print('[PRINTBENCH] MQTT disconnected; retrying', flush=True)

    def on_message(c, u, m):
        try:
            raw = json.loads(m.payload.decode('utf-8', 'ignore'))
            collector.save_raw_mqtt(db, m.topic, raw)
            ts=collector.now_iso()
            ams_rfid_diag.observe(db, raw, ts)
            spool_sync.observe_ams(db, raw, ts)
            nmods=device_info.observe(db, raw, ts)
            if nmods:
                print(f'[PRINTBENCH] DEVICE INFO updated modules={nmods}', flush=True)
            p = raw.get('print') if isinstance(raw, dict) else None
            if isinstance(p, dict) and any(k in p for k in ('gcode_state','mc_percent','nozzle_temper','bed_temper','spd_mag','ams')):
                n = collector.save_report(db, raw)
                session_tracker.observe(db, n)
                state['messages'] += 1
                if state['messages'] % 12 == 1:
                    print('[PRINTBENCH] LIVE ' + json.dumps({
                        'state': n.get('print_state'), 'progress': n.get('progress'),
                        'layer': [n.get('layer_current'), n.get('layer_total')],
                        'remaining_min': n.get('remaining_min'), 'nozzle_c': n.get('nozzle_c'),
                        'bed_c': n.get('bed_c')
                    }, ensure_ascii=False), flush=True)
        except Exception as e:
            db.execute('INSERT INTO events(ts,kind,payload) VALUES(?,?,?)',
                       (collector.now_iso(), 'mqtt_parse_error', json.dumps({'error': str(e)})))
            db.commit()

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    def stop(*_):
        STOP.set()
    signal.signal(signal.SIGINT, stop)
    try:
        signal.signal(signal.SIGTERM, stop)
    except Exception:
        pass

    if _env_enabled('PRINTBENCH_SLICER_SCAN', True):
        collector.ingest_latest_slicer(db)
    client.connect(collector.P2S_HOST, 8883, keepalive=30)
    client.loop_start()
    print('[PRINTBENCH] Collector started', flush=True)
    if _env_enabled('PRINTBENCH_MEDIA_WORKER', True):
        media_thread = threading.Thread(target=media_worker.run_forever, args=(STOP,), daemon=True, name='printbench-media')
        media_thread.start()
        print('[PRINTBENCH] Media worker started', flush=True)
    else:
        print('[PRINTBENCH] Media worker disabled', flush=True)

    def web_push_loop():
        while not STOP.is_set():
            try:
                result = push_live.push_once()
                print('[PRINTBENCH] WEB PUSH OK ' + json.dumps(result, ensure_ascii=False), flush=True)
            except Exception as e:
                print('[PRINTBENCH] web push warning:', str(e), flush=True)
            STOP.wait(5)

    if _env_enabled('PRINTBENCH_WEB_PUSH', True):
        threading.Thread(target=web_push_loop, daemon=True, name='printbench-web-push').start()
        print('[PRINTBENCH] Web push worker started', flush=True)

    last_slice = 0.0
    last_push = 0.0
    last_spool_sync = 0.0
    state.setdefault('last_version_request',0.0)
    spool_sync_state = {'running': False}

    def run_spool_sync():
        spool_sync_state['running'] = True
        sync_db = None
        try:
            sync_db = collector.db_open()
            spool_sync.ensure_schema(sync_db)
            info = spool_sync.sync(sync_db)
            print('[PRINTBENCH] SPOOL SYNC ' + json.dumps(info, ensure_ascii=False), flush=True)
        except Exception as e:
            print('[PRINTBENCH] spool sync warning:', str(e), flush=True)
        finally:
            if sync_db is not None:
                try: sync_db.close()
                except Exception: pass
            spool_sync_state['running'] = False

    while not STOP.wait(1):
        now = time.time()
        if _env_enabled('PRINTBENCH_SLICER_SCAN', True) and now - last_slice >= 15:
            try:
                collector.ingest_latest_slicer(db)
            except Exception as e:
                print('[PRINTBENCH] slicer ingest warning:', str(e), flush=True)
            last_slice = now
        if state['connected'] and now - last_push >= 60:
            client.publish(topic_req, json.dumps({'pushing': {'sequence_id': str(int(now)), 'command': 'pushall'}}))
            last_push = now
        if state['connected'] and now - state.get('last_version_request',0.0) >= 21600:
            client.publish(topic_req, json.dumps(device_info.build_version_request(int(now*1000))))
            state['last_version_request']=now
        if _env_enabled('PRINTBENCH_SPOOL_SYNC', True) and now - last_spool_sync >= 300 and not spool_sync_state['running']:
            threading.Thread(target=run_spool_sync, daemon=True, name='printbench-spool-sync').start()
            last_spool_sync=now
    client.loop_stop()
    try: client.disconnect()
    except Exception: pass
    db.close()
    print('[PRINTBENCH] Collector stopped', flush=True)


if __name__ == '__main__':
    main()
