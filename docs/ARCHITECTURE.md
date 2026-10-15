# 135er-PRINTBENCH Architecture

## Desktop-first product

135er-PRINTBENCH is one Windows application built on the OrcaSlicer 2.4.2 engine. The Windows application is the primary runtime and directly owns the complete P2S + AMS 2 Pro workflow. Bambu Studio is not part of the required stack.

## Native components

1. **Orca slicing engine** — model preparation, slicing, profiles, print preparation and G-code generation.
2. **PRINTBENCH native Device UI** — wxWidgets implementation of the binding FINAL-MASTER under `Device -> PRINTBENCH`.
3. **PRINTBENCH native collector** — normalized desktop state built from Orca's native `DeviceManager` / `MachineObject` Bambu LAN model.
4. **PRINTBENCH control layer** — capability-gated printer, AMS, camera and print commands with post-state verification.
5. **Desktop session/history store** — print sessions, diagnostics, spool/material observations and local statistics.
6. **Optional companion services** — Pi/mobile/browser and external reader paths; useful but not required for desktop operation.

## Primary data flow

`P2S / AMS 2 Pro -> Orca native Bambu LAN transport -> MachineObject / DeviceCore -> PrintbenchCollector -> PrintbenchNativePanel`

Printer writes flow in the opposite direction through validated native control objects and must never expose a raw MQTT command console in the product UI.

## FINAL-MASTER UI contract

The desktop visual source of truth is:

- `docs/design/PRINTBENCH_FINAL_MASTER.webp`
- `docs/design/PRINTBENCH_FINAL_MASTER.md`

The native implementation keeps the same information hierarchy: PRINTBENCH navigation, P2S + AMS hero, printer status, live camera, current print, live temperatures, AMS slots, device status, recent prints and system/actions. Replacing a WebView with wxWidgets does not permit a visual redesign.

## Desktop credentials and trust boundary

P2S LAN credentials remain local to the Windows application/profile and are never committed to Git. The desktop application talks to the printer only over the trusted LAN. Cloud access is not required for normal local operation. Printer state and credentials must not be pushed through a browser or remote bridge merely to render the desktop Device page.

## Optional Pi/mobile path

The existing Pi collector, browser UI, camera bridge and external reader support remain available as an optional companion for always-on/mobile use. This path is deliberately secondary:

`P2S / AMS 2 Pro -> optional Pi services -> browser/mobile`

A missing/offline Pi must have no effect on native desktop slicing, telemetry or printer control.

## Collector strategy

PRINTBENCH does not duplicate the Bambu transport unnecessarily. Where Orca already exposes reliable native state, `PrintbenchCollector` reads and normalizes that state. P2S/AMS 2 Pro fields missing from upstream Orca are added at the DeviceCore/collector boundary. This prevents competing MQTT sessions and keeps the fork maintainable.

## Security rules

- no credentials, tokens or raw RFID/NFC UIDs in Git;
- no generic raw MQTT write endpoint in the native UI;
- state-changing commands are capability-checked and fail-closed;
- command success requires response/state validation, not publish success alone;
- optional browser/mobile services remain isolated from desktop credentials wherever possible.
