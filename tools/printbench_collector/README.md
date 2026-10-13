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
