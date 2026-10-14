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

## Windows: nur Druckerdaten, keine Kamera-Verarbeitung

`pythonw.exe daemon.py` überträgt weiter Druckerdaten. Der Windows-Collector lädt
keinen Medienworker und startet kein FFmpeg, auch nicht bei einer vorhandenen
Kamera-Freigabe. SSH-Kindprozesse starten mit CREATE_NO_WINDOW. Der Elternprozess
muss im Autostart über `pythonw.exe` statt CMD oder `python.exe` laufen.

### Bestehenden PC aktualisieren

Collector beenden, die aktualisierten Python-Dateien aus diesem Ordner in den
vorhandenen Collector-Ordner kopieren und den bisherigen Autostart mit
`pythonw.exe daemon.py` wieder starten. Lokale Zugangsdaten, `.push-token`,
Datenbank und Medien behalten. Keinen zweiten Collector parallel starten.
Ein vorhandener alter FFmpeg-Prozess muss beim Wechsel einmal beendet werden.
Diese Änderung installiert nichts automatisch auf einem entfernten Windows-PC.

## Kamera auf dem Pi / Linux-Server

Der Medienworker ist ausschließlich per `python daemon.py --server-media` auf
Linux aktivierbar. Er benötigt Python, die requirements.txt-Abhängigkeiten und
FFmpeg. Empfohlen ist der Pi im Drucker-Heimnetz. Ein externer Webserver braucht
eine funktionierende private VPN-Route zum Drucker. Keine Druckerports öffentlich
freigeben. Eine Website im Browser ersetzt diesen Hintergrunddienst nicht.

Server-Konfiguration:

- `PRINTBENCH_PRINTER_HOST`: erreichbare Drucker-IP im Heimnetz/VPN.
- `PRINTBENCH_PRINTER_CREDENTIALS_FILE`: Pfad zu einer nur für den Dienst lesbaren
  JSON-Datei mit `serial` und `access_code` (Dateirechte 0600). Nicht in Git speichern.
- `.push-token` im Collector-Ordner: vorhandener Medien-/Telemetrie-Ingest-Token,
  ebenfalls 0600; dieser wird ausschließlich für die HTTPS-Übertragung verwendet.

Auf dem Server: `python camera_control.py on --minutes 30` aktiviert die
Kameraverarbeitung für 30 Minuten; `python camera_control.py off` beendet sie.
Maximal 480 Minuten pro Freigabe. Ohne Freigabe startet kein FFmpeg. Die VBS-Dateien
sind für diese Server-Variante nicht erforderlich. Ein laufender Upload kann das
Beenden kurz verzögern. Zeitraffer und Abschlussbilder entstehen nur während der
Freigabe. Die Website zeigt hochgeladene Bilder/Videos; vorhandene Bilder sind
außerhalb der Freigabe nicht live.

Der Server-Collector kann auch die Telemetrie übernehmen. Dann den PC-Collector
abschalten, damit zwei Datenquellen sich nicht gegenseitig überschreiben. Lokale
Bambu-Studio-Slicer-Metadaten vom PC sind ohne zusätzliche Übertragung auf dem
Server nicht verfügbar. Die Migration erfordert Serverzugriff, Druckerzugang und
eine überprüfte Netzwerkroute; sie ist durch Bereitstellen des Codes nicht erledigt.

`deploy/printbench-media.service` enthält eine systemd-Vorlage für einen dedizierten
Benutzer `printbench`, ein Checkout unter `/opt/printbench` und dessen `.venv`.
Vor Aktivierung müssen diese Pfade und `/etc/printbench/server.env` eingerichtet
werden. Die Environment-Datei enthält ausschließlich Host und Dateipfad der
Druckerzugänge; die eigentliche JSON-Datei muss der Dienst lesen dürfen.
Kamera-Freigaben als Dienstbenutzer im selben Collector-Ordner ausführen.
FFmpeg muss auf diesem Server installiert sein, auf dem Windows-PC nicht.
