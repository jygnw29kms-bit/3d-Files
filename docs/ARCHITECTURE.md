# PRINTBENCH Studio Architecture

## Components

1. **Desktop slicer** — OrcaSlicer 2.4.2 engine plus PRINTBENCH product restrictions and integration.
2. **Pi bridge** — always-on local service that communicates with the P2S over LAN MQTT/RTSPS and stores sanitized operational data in SQLite.
3. **Pi UI** — LAN-only read-only engineering/HMI interface on port 8080.
4. **Spool layer** — generic spool inventory with optional external NTAG identification; Bambu RFID reports are a separate source and are not treated as universal UID readers.
5. **Calibration/data** — printer/material calibration artifacts and cost/material datasets.

## Data flow

`P2S/AMS2Pro -> collector -> SQLite -> /api/v1 -> Pi UI / PRINTBENCH Studio`

Camera flow is isolated from telemetry:

`P2S RTSPS:322 -> printbench-camera.service -> /run/printbench-camera/latest.jpg -> Pi UI`

The browser never receives the RTSPS URL or LAN access code. The camera runtime directory is volatile under `/run`.

## Trust boundaries

- `/etc/printbench/bambu.json`: private Pi-only printer identity/credential source.
- `printbench.db`: local operational database; browser reads only selected fields through the API.
- Raw MQTT payloads and RFID UIDs are diagnostic/private data and are not exposed by browser endpoints.
- Printer writes are disabled by default and must not be coupled to UI read endpoints.

## Media state

RTSPS input is validated at 1920x1080 H.264/30 fps. The Pi keeps a low-duty-cycle idle snapshot and switches to a bounded MJPEG bridge only while a browser viewer is active; the browser never connects to RTSPS directly. Native timelapse FTPS on port 990 is currently not enabled in the Pi UI because TCP accepts connections but the TLS handshake currently stalls on the tested printer/firmware. The system intentionally avoids retry loops until that path is understood.

## External reader path

Open spool tags use a separate acquisition boundary: ESP32 + up to 4 RC522 -> USB CDC JSONL -> reader_serial.py -> external_tag -> spool match/proposal. Reader input never directly executes a printer write. See docs/READER-PROTOCOL.md.
