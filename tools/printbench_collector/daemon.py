from __future__ import annotations
import json, signal, socket, ssl, threading, time
import paho.mqtt.client as mqtt
import collector
import push_live
import media_worker

STOP = threading.Event()
LOCK_SOCKET = None


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
            p = raw.get('print') if isinstance(raw, dict) else None
            if isinstance(p, dict) and any(k in p for k in ('gcode_state','mc_percent','nozzle_temper','bed_temper','spd_mag','ams')):
                n = collector.save_report(db, raw)
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

    collector.ingest_latest_slicer(db)
    client.connect(collector.P2S_HOST, 8883, keepalive=30)
    client.loop_start()
    print('[PRINTBENCH] Collector started', flush=True)
    media_thread = threading.Thread(target=media_worker.run_forever, args=(STOP,), daemon=True, name='printbench-media')
    media_thread.start()
    print('[PRINTBENCH] Media worker started', flush=True)

    last_slice = 0.0
    last_push = 0.0
    last_web_push = 0.0
    while not STOP.wait(1):
        now = time.time()
        if now - last_slice >= 15:
            try:
                collector.ingest_latest_slicer(db)
            except Exception as e:
                print('[PRINTBENCH] slicer ingest warning:', str(e), flush=True)
            last_slice = now
        if state['connected'] and now - last_push >= 60:
            client.publish(topic_req, json.dumps({'pushing': {'sequence_id': str(int(now)), 'command': 'pushall'}}))
            last_push = now
        if now - last_web_push >= 5:
            try:
                result = push_live.push_once()
                if int(now) % 30 < 5:
                    print('[PRINTBENCH] WEB PUSH OK ' + json.dumps(result, ensure_ascii=False), flush=True)
            except Exception as e:
                print('[PRINTBENCH] web push warning:', str(e), flush=True)
            last_web_push = now

    client.loop_stop()
    try: client.disconnect()
    except Exception: pass
    db.close()
    print('[PRINTBENCH] Collector stopped', flush=True)


if __name__ == '__main__':
    main()
