# 135er-PRINTBENCH

135er-PRINTBENCH is a private Windows 3D-printing application based on OrcaSlicer and deliberately scoped to **Bambu Lab P2S + AMS 2 Pro**. It is intended to replace the need for a separate Bambu Studio installation on the target PC: slicing, printer connection, live telemetry, AMS, camera, printer control, profiles, diagnostics and print workflows live in one application.

## Product scope

- Printer: Bambu Lab P2S (`model_id=N7`)
- Material system: AMS 2 Pro
- Nozzles: 0.2 / 0.4 / 0.6 / 0.8 mm; default 0.4 mm
- Default build plate: Textured PEI Plate
- Orca baseline: 2.4.2, upstream tag `v2.4.2`
- Desktop operation: direct local LAN connection from PRINTBENCH to the P2S
- Bambu Studio: **not required**
- Raspberry Pi: optional companion only, not a desktop dependency
- Cloud: not required for normal local machine operation

The machine-readable contract is `config/product-contract.json`. Validate it with `python tools/validate_product_contract.py`.

## Native Desktop architecture

The binding desktop Device screen is a native wxWidgets implementation under `Device -> PRINTBENCH`; it must follow `docs/design/PRINTBENCH_FINAL_MASTER.webp` and `docs/design/PRINTBENCH_FINAL_MASTER.md`.

The native data path is:

`P2S / AMS 2 Pro -> Orca Bambu LAN transport -> MachineObject / DeviceCore -> PrintbenchCollector -> PrintbenchNativePanel`

PRINTBENCH reuses Orca's native Bambu device model instead of routing the desktop GUI through a browser/Pi bridge. PRINTBENCH-specific normalization and capabilities are kept in clearly named classes for maintainability.

## Optional companion path

`tools/printbench_collector/` and `pi-image/` remain useful for optional always-on browser/mobile access, experiments, camera bridging and external spool readers. The Windows app must continue to work if the Pi is absent or offline.

## Repository layout

- `app/orcaslicer/` - OrcaSlicer 2.4.2 engine plus native PRINTBENCH integration
- `app/orcaslicer/src/slic3r/GUI/PrintbenchCollector.*` - native normalized P2S/AMS state
- `app/orcaslicer/src/slic3r/GUI/PrintbenchNativePanel.*` - native FINAL-MASTER Device surface
- `tools/printbench_collector/` - optional Pi/browser companion collector
- `config/` - product contract and configuration
- `docs/` - architecture, security, design and hardware/protocol documentation
- `pi-image/` - optional Raspberry Pi companion image source
- `Druckkosten-Rechner/` - filament/cost logic and data

## Verification status

- Product contract validates P2S `N7` and all four supported nozzle profiles
- Windows Orca/PRINTBENCH Release build is reproducible through `tools/build_printbench_orca.ps1`
- Native PRINTBENCH Device/collector integration is being built and verified against the real P2S + AMS 2 Pro
- The previous Pi/browser UI remains available as an optional companion and reference implementation

## Security principles

P2S LAN access codes, tokens, private SSH keys and raw NFC/RFID UIDs must not be committed. State-changing operations remain separated from read/diagnostic state and must be capability-validated. A command is not considered successful merely because a transport publish succeeded.

## License

The embedded OrcaSlicer source is licensed under GNU AGPL-3.0. Third-party components retain their own terms; see `THIRD_PARTY_NOTICES.md`.
