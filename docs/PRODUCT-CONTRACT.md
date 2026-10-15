# 135er-PRINTBENCH Product Contract

## Product definition

135er-PRINTBENCH is the complete Windows desktop application for the target printer family. It is based on the OrcaSlicer 2.4.2 engine, but it is installed and used as one self-contained PRINTBENCH application. **Bambu Studio is not required.** The desktop application owns slicing, printer discovery/connection, telemetry collection, AMS 2 Pro state, camera, device control, print submission, profiles, diagnostics, print history and calibration workflows.

## Hardware scope

PRINTBENCH targets one hardware family only: **Bambu Lab P2S with AMS 2 Pro**. Orca identifies the P2S as `model_id=N7`. Supported nozzle diameters are 0.2, 0.4, 0.6 and 0.8 mm; 0.4 mm is the PRINTBENCH default. The normal product UI must not expose arbitrary printer creation or unrelated vendor families.

## Native desktop contract

`Device -> PRINTBENCH` is a **native wxWidgets surface inside the Orca application**. The binding design source of truth is `docs/design/PRINTBENCH_FINAL_MASTER.webp` plus `docs/design/PRINTBENCH_FINAL_MASTER.md`. The final desktop UI must not embed the browser dashboard through a WebView.

The desktop collector is native and local to the application. It should reuse Orca's existing Bambu LAN `MachineObject` / `DeviceManager` model wherever practical and add PRINTBENCH-specific normalization, capability validation, history and diagnostics around it. The P2S is queried directly from the Windows PC over the trusted LAN. A Raspberry Pi is **not required** for desktop operation.

## Optional companion services

The existing Pi implementation remains optional for always-on/mobile/browser access, experimentation and external hardware such as spool readers. It is not a prerequisite for the Windows application and must not become a hidden dependency of native desktop telemetry or control.

## Control safety

Printer writes remain capability-gated and fail-closed. A command is successful only after the application receives a valid response and/or independently observes the requested post-state. Raw generic MQTT command entry points must not be exposed in the product UI.

## Orca boundary

The pinned baseline is OrcaSlicer 2.4.2 (`v2.4.2`, tag SHA `8500fcdccaa10b5099ac20d252af3a7c560046f1`). Upstream-near code is preferred, but native core changes are explicitly allowed where required to make PRINTBENCH a coherent single desktop product. PRINTBENCH-specific classes must remain clearly named and isolated to simplify future upstream rebases.

## Verification

Run `python tools/validate_product_contract.py`. The validator checks the pinned Orca version, P2S model ID, supported nozzle set and required P2S machine profiles. The Windows Release build must also compile the native PRINTBENCH Device surface.
