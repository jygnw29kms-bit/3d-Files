# PRINTBENCH Checkpoint — 2026-10-14

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
- Durable real print-session tracking from MQTT state transitions.
- Completed prints are classified as success / failed / cancelled / interrupted.
- Each print session is linked to the latest matching slicer job, including material, planned filament and planned duration.
- Successful completed prints automatically archive the final live-camera JPEG.
- The final live-camera image filename is stored directly on the print session and exported with the public live payload.
- Public media ingest now accepts authenticated `final_image` JPEG uploads with bounded archive retention.

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
- `484e48b` Capture final live camera image for completed prints
- `5b1bf43` Export final live camera image with print sessions
- `b16e5d9` Store final live camera image per print session
- `51cdbbf` Publish real print sessions with live data
- `96036f5` Track real print sessions from MQTT state
- `44d52bd` Add completed print session tracking
- `d62962e` Sync and display native P2S timelapses
- `71dcc33` Harden PRINTBENCH live media transport
- `5d850ac` Fix media endpoint PHP encoding
- `7d1a31c` Add live camera video and automatic timelapse pipeline

## Next priorities
1. On the next Windows/collector start, let the schema migration create `print_sessions` and `final_image`, then validate the first real completed print end-to-end.
2. Update the public history UI to render real `print_sessions` cards/rows with final live-camera image as the primary completed-print image and slicer preview only as fallback/additional detail.
3. Add cost snapshot fields per session so historical prices do not change when current filament/electricity rates change.
4. Add energy/time/material totals and trend statistics per day/week/month.
5. Verify rolling MP4 segments with `ffprobe` after single-worker cleanup.
6. Make fail2ban ignore for the collector persistent in server configuration, not only runtime.
7. Add native media lazy loading, filtering and direct in-page playback.
8. Add retention policy and storage accounting for generated media and printer USB storage.

## Shutdown/restart behavior
- The live camera/media collector runs on the Windows PC. When the PC is off, the public site keeps the most recently uploaded snapshot/video/timelapses/final images but cannot receive new camera or MQTT data.
- After Windows startup, start `tools/printbench_collector/daemon.py` again if autostart has not yet been configured.

## 2026-10-14 — Spool Manager / NFC / AMS V2 engineering

### Production state
- PRINTBENCH web now has `09 SPULEN` with a real spool inventory and create flow.
- Spool writes require a local admin token; public inventory is sanitized and never exposes NFC UID.
- NFC onboarding QR uses a short-lived (15 min) HMAC-signed claim URL.
- UID binding rejects duplicate UIDs and refuses silent rebinding to another physical tag.
- Mutable spool data stays server-side; NTAG carries only stable PRINTBENCH identity data.
- Spool database/claim secret prefer Plesk private storage outside the webroot; fallback runtime files are web-denied.
- QR generation is bundled into `spool-manager.js`; no external QR service/runtime dependency.
- Live smoke tests: index 200, spool list 200, unauthenticated admin 403, invalid claim 403, private runtime probe 403.

### iOS companion
- Native `PRINTBENCH NFC` companion uses Core NFC + camera QR scanner.
- NTAG216 flow: scan signed QR -> write NDEF -> read back -> obtain physical UID -> POST UID to signed claim endpoint.
- GitHub macOS CI builds an unsigned device IPA for Sideloadly/AltStore; no paid Apple Developer account required for build.
- First compiler issue was fixed; CI run #2 succeeded and produced `PRINTBENCH-NFC-unsigned-IPA`.
- Verified downloaded IPA SHA-256 against its generated checksum.
- NFC tag's normal URL now opens PRINTBENCH directly at `index.php?spool=<ID>#spools`.

### AMS V2 diagnostics
- Added local-only `ams_rfid_observations` SQLite table plus `rfid_status.py`.
- Recorder captures only AMS/RFID state changes locally; raw UID/tray UUID are never added to the public web payload.
- Baseline on AMS 0 / slot 2: present=1, read_done=1, is_bambu=1, tray_info_idx=GFL99, material=PLA, while tag_uid/tray_uuid are still zero values.
- This baseline is ready for the real NTAG216 insert/re-read experiment.

### Print-session/media hardening
- Explicit FAILED/CANCEL states now take precedence over 99.9/100% progress.
- Synthetic tests passed: FAILED@100 -> failed; CANCEL@100 -> cancelled; FINISHED@100 -> success.
- Final live-camera image is only linked to a fresh successful session without an image.
- Final-image HTTPS failure has an SSH fallback.
- Timelapse finalization is isolated from final-image errors and always gets its own completion attempt.
- Completion state sets now cover FINISHED/COMPLETED/ERROR/CANCELLED/ABORTED/etc.

### Relevant commits
- `a0bdb6b` secure spool manager + NFC claim flow
- `6a563d6` private spool storage + unsigned IPA CI
- `34bce74` Core NFC build fix
- `1594b50` bundle QR engine into spool manager
- `848668e` local AMS RFID transition diagnostics
- `ecaf642` harden print completion media/session outcomes
- `fe881dc` stable NFC URL opens PRINTBENCH spool manager

### Next real-hardware gate
1. Create the first real spool in PRINTBENCH.
2. Scan its generated QR with the companion and write one existing NTAG216 sticker.
3. Verify server UID binding.
4. Put that tagged spool in AMS 2 Pro and trigger/read normal AMS detection.
5. Compare `tray_reading_bits`, `tray_read_done_bits`, `ams_rfid_status`, `tag_uid`, `tray_uuid` and slot state against the captured baseline.
6. If AMS exposes the NTAG UID anywhere, wire automatic `UID -> spool -> AMS slot setting`; otherwise proceed to bus-level V2 capture.