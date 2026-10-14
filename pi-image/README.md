# PRINTBENCH Pi Bridge Image

Reproduzierbares Raspberry-Pi-OS-Lite-64-bit-Image für PRINTBENCH Studio, P2S und AMS 2 Pro.

## Versionen

Das bereits gebaute und vollständig verifizierte Artefakt bleibt **1.0.0**:

`PRINTBENCH-Pi-Bridge-1.0.0-arm64.img.xz`

Seine Bytegrößen und SHA256-Werte bleiben unverändert in `manifest.json` dokumentiert. Der aktuelle Image-Quellstand ist **1.1.0-dev** und ergänzt die lokale Pi-UI, die credential-sichere Kamera-Bridge und deren Abhängigkeiten. Ein neues Release-Manifest wird erst erzeugt, wenn daraus tatsächlich ein neues Image gebaut und vollständig verifiziert wurde.

Basis: Raspberry Pi OS Lite 64-bit, Referenz 2026-10-06.
Ziel: 64-bit Raspberry-Pi-Boards, die vom Upstream-Image unterstützt werden. 8 GB sind das Minimum; 16 GB oder mehr werden empfohlen.

## First boot

1. Verifiziertes `.img.xz` mit Raspberry Pi Imager über **Use custom** schreiben.
2. Keine zusätzlichen Raspberry-Pi-Imager-OS-Anpassungen anwenden; Cloud-init ist bereits enthalten.
3. Ethernet vor dem ersten Start verbinden.
4. Für den ersten Boot inklusive Paketinstallation etwa 5–15 Minuten einplanen.
5. Hostname: `printbench-pi`; mDNS: `printbench-pi.local`.
6. SSH-Passwortlogin und Root-SSH sind deaktiviert; Zugriff erfolgt per Schlüssel.
7. Danach `sudo printbench-pair` ausführen, um P2S-IP, Seriennummer und LAN-Access-Code lokal einzutragen.

## Dienste im 1.1.0-dev-Quellstand

- `printbench-collector.service` – MQTT-Telemetrie, AMS-/Sessiondaten
- `printbench-ui.service` – lokale read-only HMI auf TCP 8080
- `printbench-camera.service` – adaptive RTSPS/MJPEG-Bridge über PyAV
- `printbench-reader.service` – optionaler USB-Serial-NFC-Reader (erst nach Hardware-Verifikation aktivieren)
- `printbench-collector.path` – startet den Collector nach vorhandenem Pairing

Die UI darf vor dem Pairing laufen und zeigt dann Offline-/Diagnosestatus. Collector und Kamera benötigen `/etc/printbench/bambu.json`. Kamera-Snapshots liegen ausschließlich flüchtig unter `/run/printbench-camera`.

## Security

- SSH ausschließlich per Public Key; Root- und Passwortlogin deaktiviert.
- nftables Input-Policy `drop`.
- SSH nur aus privaten Netzen; Pi-UI TCP 8080 im aktuellen Zielnetz `192.168.178.0/24`.
- Keine P2S-Zugangsdaten, Web-Tokens, privaten SSH-Schlüssel oder rohen RFID-UIDs im Image-Quellrepo.
- Die Browser-API ist read-only und gibt keine Printer-Credentials aus.
- Die Kamera nutzt PyAV im selben Prozess; der credential-haltige RTSPS-URI wird nicht als Child-Process-Argument exponiert.
- AMS-Schreibzugriffe bleiben standardmäßig deaktiviert.

## Reproduzierbarer Bootstrap

`python build_bootstrap.py` erstellt `printbench-collector.tar.gz` aus dem aktuellen Collector-Quellbaum, schließt Runtime/Secrets/Caches aus, berechnet SHA256 und trägt Commit/Hash in `printbench-firstboot.sh` ein. Das Archiv ist ein Buildartefakt und bleibt Git-ignored.

Vor einem Image-Build müssen mindestens folgende Prüfungen erfolgreich sein:

```bash
bash -n printbench-firstboot.sh
python ../tools/validate_product_contract.py
```

## Pakete

Neben SSH/Avahi/nftables/Python sind u. a. `python3-paho-mqtt`, `python3-watchdog`, `python3-requests`, `python3-av`, `python3-spidev`, `python3-gpiozero`, ffmpeg, sqlite3 und Diagnosewerkzeuge vorgesehen. `python3-av` wird von der Kamera-Bridge verwendet; `python3-serial` ist für den optionalen ESP32/USB-NFC-Reader vorgesehen. ffmpeg bleibt für Medienanalyse/Kompatibilitätswerkzeuge verfügbar.

## Nützliche Befehle

```bash
printbench-status
sudo printbench-pair
systemctl status printbench-collector.service
systemctl status printbench-ui.service
systemctl status printbench-camera.service
journalctl -u printbench-collector.service -f
```

## Hardwarevorbereitung

I2C und SPI werden für externe RFID-/NTAG-Reader und spätere Diagnosepfade aktiviert. Serielle Einstellungen werden erst geändert, wenn ein konkret validierter Hardwarepfad dies erfordert.

## Lokal/Buildartefakte

Nicht committen: `.img`, `.img.xz`, SHA-Dateien, generierte private SSH-Schlüssel, erzeugtes Cloud-init `user-data`, offizielle Raspberry-Pi-Basisimages, `printbench-collector.tar.gz`, Runtime-Datenbanken oder Credentials.
