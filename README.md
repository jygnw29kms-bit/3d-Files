# PRINTBENCH Studio

PRINTBENCH Studio is a local 3D-printing application based on OrcaSlicer and deliberately scoped to **Bambu Lab P2S + AMS 2 Pro**. The repository contains the desktop slicer, Raspberry Pi bridge, local machine UI, spool/NTAG logic, telemetry, print history, cost analysis, calibration artifacts and project documentation.

## Product scope

- Printer: Bambu Lab P2S (`model_id=N7`)
- Material system: AMS 2 Pro
- Nozzles: 0.2 / 0.4 / 0.6 / 0.8 mm; default 0.4 mm
- Default build plate: Textured PEI Plate
- Orca baseline: 2.4.2, upstream tag `v2.4.2`
- Pi bridge: local telemetry, adaptive camera, RFID/NTAG, spool and session data
- Open-tag path: ESP32/RC522 over a versioned USB-serial contract; reader service disabled until hardware is validated
- Cloud is not required for local machine operation
- AMS state-changing writes are disabled by default
- Raw RFID/NFC UIDs are never exposed to browser clients or committed to Git

The machine-readable contract is `config/product-contract.json`. Validate it with `python tools/validate_product_contract.py`.

## Architecture

`app/orcaslicer/` contains the deliberately upstream-near OrcaSlicer engine. PRINTBENCH-specific behavior should live outside the C++ core whenever practical and connect through explicit adapters and services. The Pi communicates with the P2S only on the trusted LAN and exposes sanitized data to the desktop application and Pi UI.

The current Pi UI is available on the trusted LAN at `http://192.168.178.80:8080/`. It is read-only and provides live telemetry, AMS state, RFID diagnostics, spool state, print history, bridge diagnostics and the locally bridged P2S camera feed.

## Repository layout

- `app/orcaslicer/` - OrcaSlicer 2.4.2 engine baseline
- `tools/printbench_collector/` - P2S/AMS collector, Pi services, camera and reader bridge
- `config/` - product contract and configuration
- `docs/` - architecture, security and hardware/protocol documentation
- `pi-image/` - reproducible Raspberry Pi bridge image source
- `ios/` - NFC helper application
- `Druckkosten-Rechner/` - filament/cost logic and data
- `LST-Clips/`, `LST-Klammer/` - project print parts

## Verification status

- Product contract validated against Orca 2.4.2, P2S `N7` and all four supported P2S nozzle profiles
- Reader/NTAG contract and external-tag pipeline covered by unit tests
- Pi UI plus JPEG/MJPEG camera bridge verified against the real P2S and Pi on the LAN
- systemd units verified on the real Pi with `systemd-analyze verify`
- Reader service remains disabled until physical reader hardware is installed and validated
- Full Windows build of the Orca C++ fork remains pending because the current development PC does not have CMake/MSBuild in PATH

## Security principles

P2S LAN access codes, tokens, private SSH keys and raw NFC/RFID UIDs must not be committed. The Pi UI is restricted to the trusted target LAN. Printer writes are separated from read/diagnostic operations and require explicit enablement. Browser clients never receive the credential-bearing RTSPS URL or raw MQTT payloads.

## License

The embedded OrcaSlicer source is licensed under GNU AGPL-3.0. Combined distribution must comply with the corresponding license obligations. Third-party assets and optional proprietary networking components retain their own terms; see `THIRD_PARTY_NOTICES.md`.
