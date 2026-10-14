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
## 2026-10-14 — Continued engineering: costs, AMS control, private spool sync, free iPhone NFC

### Historical cost snapshots
- Added `costing.py` + versioned `cost_config.json`.
- Every finished print session freezes the rates used at that time: material €/kg, electricity €/kWh, machine €/h, margin, estimated kWh, material/electricity/machine/self cost and sale price.
- Explicitly marked energy as estimated until a real power meter is connected.
- Current defaults: 18.99 €/kg, 0.40 €/kWh, 0.65 €/h, 20% margin, 0.20 kW average + 0.10 kWh startup estimate.
- Synthetic cost/session tests passed. Live payload now exposes the public cost configuration and history renders session cost snapshots.
- Commit: `bb22de5`.

### Spool lifecycle + filament database
- Spool cards now support remaining-weight updates and recording a drying timestamp.
- An NFC deep-link (`?spool=PB-...#spools`) highlights and scrolls to the matching spool.
- Spool creation reads `Druckkosten-Rechner/data/filaments.json` for vendor suggestions, materials and €/kg proposal scaled to spool weight; manual price always wins.
- No unverified nozzle/drying values are invented from the price database.
- Commits: `81b9e14`, `ab8dc47`.

### Private spool inventory sync / UID matching
- Collector syncs protected spool detail data into local SQLite every 5 minutes using the local admin token.
- New local tables: `spool_inventory`, `ams_spool_matches`.
- AMS `tag_uid`/`tray_uuid` observations are matched locally to PRINTBENCH spool UIDs; matches/unmatched states are local events only.
- Raw UID/private spool data remain excluded from web payloads.
- Commit: `de96848`.

### AMS control layer — fail closed
- Added `ams_control.py`, `ams_control.json`, `ams_cli.py`.
- Verified payload builders for `ams_get_rfid` and `ams_filament_setting`.
- Generic material IDs currently mapped for PLA/PETG/TPU/PVA/PLA-CF/PC/PA/PA-CF/ASA/ABS.
- All commands are dry-run by default. Real writes are hard-disabled with `write_enabled=false` until the NTAG216 hardware test proves UID detection and slot mapping.
- `--apply` currently fails cleanly instead of touching the AMS.
- Commit: `047d401`.

### iOS signing reality + free fallback
- Native companion builds successfully as an unsigned device IPA in GitHub macOS/Xcode CI.
- Important: free Apple-ID sideloading cannot be assumed to grant the Core NFC custom entitlement. The native app is retained but is not the only production path.
- Added a zero-paid-account fallback around the free App Store app NFC21 Tools:
  1. PRINTBENCH creates one signed 15-minute QR.
  2. Normal iPhone camera opens `spool-write.php`.
  3. Page shows the stable PRINTBENCH URL to write to NTAG216.
  4. NFC21 Tools writes the URL and reads the physical UID/serial.
  5. User pastes the UID into the same signed PRINTBENCH page.
  6. Server validates the signed claim and binds UID to the spool with duplicate/rebind protection.
- The same QR remains consumable by the native companion where Core NFC entitlement is available.
- `spool-write.php` and legacy `spool-claim.php` both fail closed for expired/invalid claims.
- Live tests: spool list 200; invalid spool-write claim 403; invalid legacy claim 403; manager exposes NFC21 fallback.
- Commit: `dc7561f`.

### Current native IPA artifact
- GitHub build run #4 succeeded for `dc7561f`.
- Latest local artifact: `ios/PrintbenchNFC/dist/PRINTBENCH-NFC-unsigned.ipa`.
- SHA-256 verified against generated checksum: `3039d56795b1c1199c661cf7b46d8379a7b44d7ebe27bf8dedc8e461ed0c1276`.
- IPA remains unsigned by design for Sideloadly/AltStore re-signing; NFC entitlement availability must be runtime-tested after signing.

### Real hardware gate before enabling AMS writes
1. Create first real spool in PRINTBENCH.
2. Generate signed QR.
3. Program an existing NTAG216 using NFC21 fallback (or native companion if entitlement works).
4. Verify UID is bound server-side and appears in local `spool_inventory` after sync.
5. Put tagged spool into AMS 2 Pro and trigger a normal RFID re-read.
6. Compare against stored baseline using `python tools/printbench_collector/rfid_status.py --limit 40` and inspect `ams_spool_matches`.
7. If AMS exposes a matching non-zero UID, connect `UID -> spool -> ams_filament_setting`, still with safety checks for slot/material/printer state.
8. Only after a controlled dry-run and one confirmed hardware test consider `write_enabled=true`.
9. If AMS does not expose NTAG UID, proceed with the planned bus-level V2 capture instead of guessing.
## 2026-10-14 — PRINTBENCH Raspberry Pi Bridge image 1.0.0

- Built a dedicated flashable Raspberry Pi OS Lite 64-bit image from the official 2026-10-06 image.
- Final file (local, intentionally not committed): `pi-image/PRINTBENCH-Pi-Bridge-1.0.0-arm64.img.xz`.
- Compressed size: 708,381,824 bytes; SHA-256 `062DFE68E250EBE0E349D07B100F523C7EA72E5C613FDCD009639D4FB05E71CB`.
- Uncompressed image SHA-256 `D82C1F37769000B11E2A49AA98DD80F954613D755CC3DC9EA4349623344F2B49`.
- Full decompression verification passed: decompressed `.xz` hash exactly matches the `.img` hash.
- Hostname `printbench-pi`, mDNS `printbench-pi.local`, SSH user `printbench`.
- Password SSH and root SSH are disabled; a dedicated Ed25519 public key is embedded. The private key exists only in the local ignored `pi-image/keys/` directory.
- First boot expects Ethernet/DHCP and provisions SSH, avahi/mDNS, nftables, diagnostics packages, ffmpeg, MQTT tools, I2C/SPI tools, Python environment and systemd units.
- Collector bootstrap archive is checksummed and pinned to collector commit `c530ffa`.
- Debian 13 native packages `python3-paho-mqtt`, `python3-watchdog`, `python3-requests` are used through a system-site-packages venv; pip is fallback only.
- Collector remains fail-closed before pairing: no `/etc/printbench/bambu.json` means no collector start.
- Pi defaults to local diagnostics only: media worker OFF, slicer scan OFF, web push OFF, spool sync OFF. These are enabled only after controlled configuration.
- Helper commands after boot: `printbench-status`, `sudo printbench-pair`, `journalctl -u printbench-collector.service -f`.
- Build scripts/docs committed under `pi-image/`; raw images, keys, generated cloud-init files and base image are ignored.
- Relevant commits: `c530ffa` (portable secure collector config), `e30be2b` (Pi image build system), `89375e0` (Debian ARM64 dependency hardening).
