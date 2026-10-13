# PRINTBENCH Checkpoint — 2026-10-13

## Live system
- Public UI: `https://www.dezender.de/3d-druck/`
- Source repository: `jygnw29kms-bit/3d-Files`
- Printer: Bambu Lab P2S with AMS 2 Pro
- Collector: `tools/printbench_collector/daemon.py`
- Telemetry DB: local SQLite `printbench.db` (runtime only, not committed)

## Implemented
- Live MQTT telemetry with freshness/offline detection.
- Real time ranges: LIVE / 24H / 7D / 30D with downsampled charts and full-sample statistics.
- Full AMS slot status and drying information without publishing raw RFID/UUID secrets.
- Real P2S camera via local RTSPS: H.264, 1920x1080, 30 FPS.
- Live JPEG snapshots pushed to the public site.
- Rolling live MP4 clip pipeline.
- Automatic PRINTBENCH timelapse frame capture during print jobs.
- Native Bambu timelapse discovery and read-only FTPS sync from printer storage.
- Native P2S media found: 8 MP4 timelapses + 16 thumbnail images.
- Native media synced to the public media archive.
- Media UI includes live snapshot, live video, PRINTBENCH timelapse and Bambu native timelapse archive.

## Printer interfaces confirmed
- MQTT/TLS: 8883
- RTSPS camera: 322
- Implicit FTPS: 990, requires TLS session reuse on the data connection
- Native timelapse path: `/timelapse`
- Native thumbnails: `/timelapse/thumbnail`

## Security / transport
- Printer stays LAN-only; no printer credentials are exposed publicly.
- Server ingest endpoints use an existing push token.
- A dedicated local Ed25519 server fallback key exists outside the repository.
- HTTPS is preferred; SSH transport exists as fallback.
- On 2026-10-13 the collector public IP was falsely blocked by Plesk ModSecurity fail2ban during transport tests. It was unbanned and added to the running jail ignore list. Recheck persistence after server reboot/config reload.

## Current code checkpoints
- `d62962e` Sync and display native P2S timelapses
- `71dcc33` Harden PRINTBENCH live media transport
- `5d850ac` Fix media endpoint PHP encoding
- `7d1a31c` Add live camera video and automatic timelapse pipeline

## Next priorities
1. Verify rolling MP4 segments after single-worker cleanup with `ffprobe`; previous corrupt segments were caused by duplicate FFmpeg test processes writing the same files.
2. Make fail2ban ignore for the collector persistent in server configuration, not only runtime.
3. Add job-linked media metadata: print name, slicer profile, material, duration, success/failure and costs per timelapse.
4. Build completed-print history from telemetry state transitions and slicer jobs.
5. Add energy/time/material totals and trend statistics per day/week/month.
6. Add native media lazy loading, filtering and direct in-page playback.
7. Add retention policy and storage accounting for generated media and printer USB storage.

## Shutdown/restart behavior
- The live camera/media collector runs on the Windows PC. When the PC is off, the public site keeps the most recently uploaded snapshot/video/timelapses but cannot receive new camera or MQTT data.
- After Windows startup, start `tools/printbench_collector/daemon.py` again if autostart has not yet been configured.
