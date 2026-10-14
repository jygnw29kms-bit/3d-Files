# PRINTBENCH Collector

Local telemetry collector for the Bambu Lab P2S / AMS 2 Pro.

## Data sources
- Bambu Studio temp workspace: planned slicer metadata from current `.gcode` / `_temp_*.config`
- P2S local MQTT over TLS on port 8883: actual live printer and AMS telemetry

## Security
- No LAN access code or printer serial is stored in the repository.
- Bambu credentials are read only at runtime from the local Bambu Studio configuration.
- The SQLite database is local and excluded by `.gitignore`.
- No printer MQTT port is exposed to the Internet.

## Files
- `collector.py` one-shot ingest/test
- `daemon.py` continuous telemetry collector
- `status.py` local status summary
- `printbench.db` local SQLite database (ignored)

## Run
```powershell
python daemon.py
python status.py
```

Windows autostart is configured through the current user's Startup folder and launches `daemon.py` hidden via `pythonw.exe`.

## Kamera nur bei Bedarf (Windows)

Der Collector überträgt MQTT-Druckerdaten weiterhin dauerhaft. FFmpeg bleibt
standardmäßig aus; Druckerstatus braucht kein FFmpeg. SSH- und FFmpeg-Kindprozesse
starten unter Windows ohne Konsolenfenster. Der Collector selbst muss weiterhin
über `pythonw.exe` statt `python.exe` gestartet werden.

- `camera-on.vbs` doppelklicken: Kamera für 30 Minuten freigeben.
- `camera-off.vbs` doppelklicken: Kamera wieder ausschalten.
- Alternativ: `python camera_control.py on --minutes 120` (maximal 480 Minuten).
- `python camera_control.py status` zeigt die lokale Freigabe.

Die Freigabe läuft automatisch ab. Der Medienworker beendet FFmpeg beim nächsten
Durchlauf; ein laufender Upload kann das kurz verzögern. Zeitraffer und Abschlussbilder
werden nur während der Kamerafreigabe erstellt. Bereits hochgeladene Bilder auf der
Website können weiterhin sichtbar sein und sind außerhalb der Freigabe nicht live.
Für eine gesamte Druckaufzeichnung muss die Freigabe den Druck abdecken.

### Bestehenden PC aktualisieren

Collector beenden, die Python-Dateien und Kamera-VBS-Dateien aus diesem Ordner in
den vorhandenen Collector-Ordner kopieren und den bisherigen Autostart mit
`pythonw.exe daemon.py` wieder starten. Lokale Zugangsdaten, `.push-token`,
Datenbank und Medien behalten. Keinen zweiten Collector parallel starten.
Ein vorhandener alter FFmpeg-Prozess muss beim Wechsel einmal beendet werden.
Diese Änderung installiert nichts automatisch auf einem entfernten Windows-PC.
