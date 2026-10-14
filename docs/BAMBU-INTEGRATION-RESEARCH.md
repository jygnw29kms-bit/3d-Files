# PRINTBENCH Bambu Integration Research

Date: 2026-10-14
Scope: private, local use by the owner only. Not intended for public redistribution.

## Objective

Integrate Bambu Lab P2S + AMS 2 Pro as a first-class device inside PRINTBENCH Studio / OrcaSlicer with live telemetry, camera, files, AMS state, drying state and controlled write actions.

## Projects evaluated

### 1. ClusterM/open-bamboo-networking

Usefulness: VERY HIGH

- Clean-room drop-in replacement for the proprietary `bambu_networking` plugin.
- Implements the same C ABI used by Bambu Studio / OrcaSlicer.
- Explicit OrcaSlicer support and primarily P2S-tested.
- Covers LAN MQTT, printing, file transfer, camera paths, device status and optional cloud paths.
- Best reference for the Orca/Bambu networking boundary.

Caution: cloud/non-Developer-Mode paths include credential/signing complexity. Do not make leaked or third-party signing material a mandatory dependency.

### 2. greghesp/ha-bambulab

Usefulness: VERY HIGH

- Mature MQTT command catalogue and detailed telemetry/state handling.
- Implements light, fan, speed, print control, AMS operations and filament settings.
- Large issue history exposes firmware regressions quickly.
- P2S/AMS 2 Pro reports prove that command publication and actual physical success can diverge.

Use it as a reference for command payloads, capability detection, state verification and firmware compatibility.

### 3. OpenBambuAPI

Usefulness: VERY HIGH

- Detailed MQTT protocol reference.
- Documents local TLS/8883, `bblp` authentication, request/report topics and `sequence_id` correlation.
- Best protocol-level reference for request/response envelopes and field names.

### 4. BambuTools/bambulabs_api

Usefulness: HIGH

- Clean higher-level Python API around monitoring/control.
- Useful design reference for reconnects, camera/file operations and a stable API above raw MQTT.

### 5. BambuTagger-AMS / OpenSpool-style projects

Usefulness: HIGH for spool integration, LOW as slicer core

- Confirms external RC522/NTAG readers mapped to AMS slots are practical.
- Useful reader/slot-mapping ideas.
- NFC UID must never authorize printer writes.

### 6. mqtt-bambu and similar bridges

Usefulness: MEDIUM

- Good normalization/reconnect/state-merge examples.
- Reinforces our bridge/API architecture.

### 7. beambam / signed-MQTT experiments

Usefulness: RESEARCH ONLY

- Useful to track newer signed-MQTT restrictions.
- Do not make leaked certificates, extracted signing keys or account-token recovery part of the default path.
- Private use relaxes redistribution/licensing constraints, but not the security risk of importing opaque credentials or bypass mechanisms.

## Resulting architecture

Keep three boundaries:

1. Orca / PRINTBENCH UI
2. PRINTBENCH Device API / Pi bridge
3. Bambu LAN MQTT + RTSPS + file transport

The Orca UI must not know printer credentials, raw MQTT topics or camera credentials.

## Device API responsibilities

- normalized live state
- printer/AMS capability model
- command whitelist and validation
- state preconditions
- sequence-id generation and response correlation
- post-command state verification
- rate limiting
- audit/event logging
- firmware/model compatibility matrix

## Capability model

Each capability is one of:
- supported_verified
- supported_unverified
- unsupported
- blocked_by_firmware
- disabled_by_policy

Initial write groups:
- print.pause / resume / stop
- printer.light / speed_mode / fan / temperature
- print.skip_object
- ams.load_unload / filament_setting / drying

Read capabilities remain independent from writes.

## Command safety model

All writes remain disabled unless explicitly enabled locally.

Before sending validate printer freshness, exact P2S model, firmware/capability state, fixed command whitelist, bounded numeric values, AMS/slot IDs, machine-state preconditions and absence of a conflicting in-flight command.

During sending use a unique sequence ID, bounded timeout and no arbitrary raw-MQTT UI endpoint.

After sending, success requires a matching positive response plus agreeing post-state, or independently verified post-state. Publish success alone is never enough. This specifically addresses observed P2S/AMS cases where MQTT accepts a command but the physical action does not happen.

## Security decisions

- LAN-first; no internet exposure of the P2S.
- Credentials remain local on Pi/desktop.
- UI receives only sanitized Device API data.
- Raw MQTT and complete NFC/RFID identifiers stay private diagnostics.
- Separate read/write code paths.
- No generic `send_raw_mqtt` endpoint.
- No cloud credentials in logs.
- No mandatory leaked signing material.
- Camera credentials stay inside the bridge process.
- Thermal/destructive commands use stricter ranges/state validation than light/pause operations.

## Private-use note

This installation is intended only for the owner's private use and is not distributed. That makes local GPL/AGPL evaluation and modification significantly simpler. Still keep upstream attribution and source provenance so future maintenance remains auditable.

## Recommended implementation order

1. Finish normalized Device API and capability endpoint.
2. Add command transaction engine with dry-run default.
3. Implement low-risk controls first: light, pause, resume, speed mode.
4. Add stop with explicit desktop confirmation.
5. Add AMS load/unload and filament settings with post-state validation.
6. Add AMS drying only after verifying the exact installed P2S firmware command flow.
7. Integrate camera and file browser into the Orca Device panel.
8. Patch Orca-specific gaps such as current-print thumbnail/state routing.
9. Add compatibility tests using sanitized MQTT fixtures and an emulator/mock broker.

## Decision

PRINTBENCH should not become a thin copy of Bambu Studio. The strongest design is an Orca-based slicer with its own local, testable and fail-closed Bambu Device API. `open-bamboo-networking` is the best ABI reference; `ha-bambulab` and `OpenBambuAPI` are the best command/protocol references; our Pi bridge remains the security and compatibility boundary.

## TLS hardening target

Current collector code still uses permissive local TLS for MQTT. That is acceptable only as a temporary compatibility mode.

Target state for P2S LAN transports:
- trust the Bambu printer CA/leaf where available;
- bind the certificate identity to the expected printer serial (`CN=<serial>`);
- because the printer is reached by IP and may not present an IP SAN, use explicit SNI/serial validation or a pinned device leaf;
- support TOFU/pinned leaf only as a controlled local bootstrap mechanism;
- store the pinned certificate locally and never in browser responses;
- expose a diagnostic mismatch error instead of silently falling back to insecure TLS;
- keep an explicit emergency/debug `skip_verify` switch, default off once pinning is provisioned.

This follows the stronger approach documented by OpenBambuAPI/open-bamboo-networking and avoids leaving `CERT_NONE` as the permanent security model.
