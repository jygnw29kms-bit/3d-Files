from __future__ import annotations
import copy
import hashlib
import ipaddress
import json
import socket
import ssl
import threading
import time
import uuid
import paho.mqtt.client as mqtt


def printer_ip(value):
    address = ipaddress.ip_address(value)
    if not address.is_private or address.is_unspecified or address.is_multicast:
        raise ValueError('Drucker-IP muss eine private LAN-/VPN-Adresse sein')
    return str(address)


def certificate_fingerprint(host):
    host = printer_ip(host)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    with socket.create_connection((host, 8883), timeout=5) as raw:
        with context.wrap_socket(raw, server_hostname=host) as tls:
            return hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest()


class PinnedTLS(ssl.SSLContext):
    def __new__(cls, fingerprint):
        return super().__new__(cls, ssl.PROTOCOL_TLS_CLIENT)

    def __init__(self, fingerprint):
        self.fingerprint = fingerprint
        self.check_hostname = False
        self.verify_mode = ssl.CERT_NONE
        self.minimum_version = ssl.TLSVersion.TLSv1_2

    def wrap_socket(self, *args, **kwargs):
        tls = super().wrap_socket(*args, **kwargs)
        if hashlib.sha256(tls.getpeercert(binary_form=True)).hexdigest() != self.fingerprint:
            tls.close()
            raise ssl.SSLCertVerificationError('Printer certificate changed')
        return tls


def deep_merge(target, update):
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict): deep_merge(target[key], value)
        else: target[key] = copy.deepcopy(value)


def public_ams(raw):
    # Explicit field list: no serial numbers, RFID identities or access codes in a web copy.
    units = []
    for unit in raw.get('ams', []) if isinstance(raw.get('ams'), list) else []:
        trays = []
        for tray in unit.get('tray', []):
            trays.append({key: tray.get(key) for key in ('id', 'tray_type', 'tray_color', 'remain', 'nozzle_temp_min', 'nozzle_temp_max')})
        units.append({**{key: unit.get(key) for key in ('id', 'temp', 'humidity', 'humidity_raw', 'dry_time')}, 'trays': trays})
    return {'units': units, 'tray_now': raw.get('tray_now'), 'tray_tar': raw.get('tray_tar'), 'ams_exist_bits': raw.get('ams_exist_bits')}


class Printer:
    def __init__(self, store, clock=time.time):
        self.store, self.clock = store, clock
        self.lock = threading.RLock()
        self.client = None
        self.connected = False
        self.report = {}
        self.last_report = 0
        self.last_record = 0
        self.error = None
        self.generation = 0

    def connect(self):
        self.disconnect()
        cfg = self.store.config()
        host = printer_ip(cfg.get('printer_host', ''))
        serial = cfg.get('printer_serial', '')
        code = self.store.secret('printer-access')
        pin = cfg.get('printer_fingerprint', '')
        if not serial or not code or len(pin) != 64:
            raise ValueError('IP, Seriennummer, Zugangscode und bestätigtes Zertifikat erforderlich')
        with self.lock:
            self.report = {}; self.last_report = 0; self.error = None
            self.generation += 1
            generation = self.generation
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, protocol=mqtt.MQTTv311)
        client.username_pw_set('bblp', code)
        client.tls_set_context(PinnedTLS(pin))

        def connected(c, _u, _f, reason, _p):
            if generation != self.generation: return
            self.connected = not reason.is_failure
            if self.connected:
                c.subscribe(f'device/{serial}/report')
                c.publish(f'device/{serial}/request', json.dumps({'pushing': {'sequence_id': '0', 'command': 'pushall'}}))
            else: self.error = 'Drucker verweigert MQTT-Anmeldung'

        def disconnected(*_args):
            if generation == self.generation: self.connected = False

        def message(_c, _u, msg):
            if generation != self.generation: return
            try:
                packet = json.loads(msg.payload)
                if isinstance(packet.get('print'), dict): self.ingest(packet['print'])
            except (ValueError, TypeError): self.error = 'Ungültige Druckermeldung'

        client.on_connect, client.on_disconnect, client.on_message = connected, disconnected, message
        self.client = client
        try:
            client.connect(host, 8883, 30)
            client.loop_start()
        except Exception:
            self.client = None
            self.error = 'Drucker nicht erreichbar oder Zertifikat stimmt nicht überein'
            raise ValueError(self.error)

    def disconnect(self):
        self.generation += 1
        client, self.client = self.client, None
        self.connected = False
        if client:
            client.disconnect()
            client.loop_stop()

    def ingest(self, report):
        with self.lock:
            deep_merge(self.report, report)
            self.last_report = self.clock()
            if self.last_report - self.last_record >= 5:
                self.store.record(self.last_report, self.snapshot())
                self.last_record = self.last_report

    def snapshot(self):
        with self.lock:
            raw = self.report
            live = {key: raw.get(key) for key in ('gcode_state', 'mc_percent', 'mc_remaining_time', 'layer_num', 'total_layer_num', 'nozzle_temper', 'nozzle_target_temper', 'bed_temper', 'bed_target_temper', 'chamber_temper', 'spd_lvl', 'spd_mag', 'wifi_signal', 'print_error')}
            online = self.connected and bool(self.last_report) and self.clock() - self.last_report < 20
            return {'online': online, 'connected': self.connected, 'observed_at': self.last_report, 'live': live, 'ams': public_ams(raw.get('ams', {})), 'error': self.error, 'source': 'P2S LAN MQTT', 'command_support': 'firmware-dependent; hardware validation pending'}

    def command(self, action, value=None, remote=False):
        snapshot = self.snapshot()
        if not snapshot['online'] or not self.client: raise ValueError('Keine frischen Druckerdaten; Steuerung gesperrt')
        if remote and action not in ('pause', 'resume', 'stop', 'speed', 'light'):
            raise ValueError('Dieser Befehl ist für Fernsteuerung nicht freigegeben')
        sequence = uuid.uuid4().hex[:10]
        printing = str(snapshot['live'].get('gcode_state', '')).upper()
        if action in ('pause', 'stop') and printing not in ('RUNNING', 'PRINTING', 'PAUSE', 'PAUSED', 'PREPARE'):
            raise ValueError('Drucker meldet keinen steuerbaren laufenden Druck')
        if action == 'resume' and printing not in ('PAUSE', 'PAUSED'):
            raise ValueError('Drucker ist nicht pausiert')
        if action in ('pause', 'resume', 'stop'):
            payload = {'print': {'sequence_id': sequence, 'command': action, 'param': ''}}
        elif action == 'speed':
            if type(value) is not int or value not in (1, 2, 3, 4): raise ValueError('Geschwindigkeitsstufe 1–4 erforderlich')
            payload = {'print': {'sequence_id': sequence, 'command': 'print_speed', 'param': str(value)}}
        elif action == 'light':
            if type(value) is not bool: raise ValueError('Licht benötigt true/false')
            payload = {'system': {'sequence_id': sequence, 'command': 'ledctrl', 'led_node': 'chamber_light', 'led_mode': 'on' if value else 'off', 'led_on_time': 500, 'led_off_time': 500, 'loop_times': 0, 'interval_time': 0}}
        else:
            raise ValueError('Nicht unterstützter Befehl')
        info = self.client.publish(f"device/{self.store.config()['printer_serial']}/request", json.dumps(payload), qos=1)
        if info.rc != mqtt.MQTT_ERR_SUCCESS: raise ValueError('Befehl konnte nicht übertragen werden')
        return {'status': 'published', 'action': action, 'sequence_id': sequence, 'note': 'Übertragen; keine bestätigte Ausführung durch den Drucker'}
