# PRINTBENCH Bambu Integration Research

Date: 2026-10-14
Status: verified engineering notes for PRINTBENCH Studio.

## Objective

Integrate Bambu Lab P2S + AMS 2 Pro as a first-class device in PRINTBENCH Studio while keeping printer credentials and Bambu-specific transport details behind a local Device API / Pi bridge boundary.

## Verified upstream references

### ClusterM/open-bamboo-networking

Repository: https://github.com/ClusterM/open-bamboo-networking

- AGPL-3.0 open-source replacement for the proprietary `bambu_networking` plugin.
- Bambu Studio and Orca Slicer consume the same documented C ABI.
- Orca Slicer is supported from 2.3.2 with client-specific install conventions and known differences.
- Its documentation explicitly calls out Orca-specific gaps such as the current-print thumbnail path.
- The project author states that P2S is a primary real-world test target.

Engineering use: ABI and networking-boundary reference. Do not copy opaque credentials or make cloud/signing paths a mandatory PRINTBENCH dependency.

### Doridian/OpenBambuAPI

Repository: https://github.com/Doridian/OpenBambuAPI

- Documents local MQTT request/report envelopes, `sequence_id` correlation and `info.get_version`.
- `info.get_version` returns module entries containing `name`, `hw_ver`, `sw_ver` and serial fields.

Engineering use: protocol-field reference. PRINTBENCH intentionally persists only module name, hardware version, software version and timestamp; serial fields are discarded.

### greghesp/ha-bambulab

Repository: https://github.com/greghesp/ha-bambulab

- Mature local MQTT implementation and useful compatibility history.
- Issue/release history documents P2S firmware-specific transport regressions and command/state edge cases.
- A reported P2S 01.02.00.00 case required TLS 1.2 because TLS 1.3 ClientHello did not complete.

Important local verification: the PRINTBENCH P2S also reports OTA `01.02.00.00`, but a direct probe on this exact unit negotiated TLS 1.3 with `TLS_AES_256_GCM_SHA384`. Therefore PRINTBENCH must not hard-code a TLS-1.2 cap solely from the firmware version. Capability/transport behavior must be measured per installation and treated as compatibility data.

### VID-PRO/BambuTagger-AMS

Repository: https://github.com/VID-PRO/BambuTagger-AMS

- Demonstrates a practical four-slot external tag architecture using one ESP32 and four RC522 readers on shared SPI.
- Supports NTAG-based formats in addition to Bambu-format tags and maps readers to AMS slots.
- Confirms that external tag acquisition can be separated from printer-side AMS tray synchronization.

Engineering use: hardware-topology reference. PRINTBENCH uses a stricter security boundary: reader observations travel over local USB CDC JSONL to the Pi, and a UID can identify a spool but can never authorize a printer write.

### BambuTools/bambulabs_api

Repository: https://github.com/BambuTools/bambulabs_api

Engineering use: secondary Python API reference for reconnect, monitoring and higher-level abstraction patterns. It is not the authoritative PRINTBENCH protocol source.

## Measured local P2S compatibility

The following facts were measured on the actual PRINTBENCH P2S through read-only local operations:

- Printer model scope: P2S / Orca model `N7`.
- MQTT over TCP 8883 is operational on the trusted LAN.
- Read-only `info.get_version` succeeds.
- OTA software version: `01.02.00.00`.
- Sanitized module inventory contains seven module names with hardware/software versions.
- Direct TLS negotiation on MQTT port 8883 succeeded with TLS 1.3 and cipher `TLS_AES_256_GCM_SHA384`.
- RTSPS camera input is operational and is bridged locally to same-origin JPEG/MJPEG without exposing the credential-bearing URI.
- Stock AMS report/MQTT behavior does not expose a useful non-zero UID for the tested generic NTAG216 tag.

These are installation measurements, not claims that every P2S or firmware build behaves identically.

## Resulting architecture

Maintain three explicit trust boundaries:

1. PRINTBENCH Studio / Orca user interface.
2. PRINTBENCH Device API and Pi bridge.
3. Bambu-specific LAN transports (MQTT, RTSPS and file transport where verified).

The desktop/UI layer must not receive printer credentials, raw MQTT topics, raw RFID/NFC UIDs or credential-bearing camera URLs.

## Device API responsibilities

- normalized live state
- printer/AMS capability model
- sanitized firmware/module inventory
- command whitelist and validation
- state preconditions
- request sequence IDs and response correlation
- post-command state verification
- bounded rate limiting
- audit/event logging
- firmware/model compatibility observations

Capability state should distinguish at least `supported_verified`, `supported_unverified`, `unsupported`, `blocked_by_firmware` and `disabled_by_policy`.

## Write safety model

All state-changing commands remain disabled unless explicitly enabled locally. There is no generic raw-MQTT browser endpoint.

Before a future command is sent, PRINTBENCH must validate fresh telemetry, exact P2S product scope, command whitelist, numeric bounds, AMS/slot IDs where relevant, machine-state preconditions and the absence of a conflicting command transaction.

A transport publish or positive response is not sufficient proof of physical success. Where a state transition can be observed, command completion must require a correlated response and/or agreeing post-state within a bounded timeout.

## External tag path

Open spool tags are intentionally independent from stock AMS RFID:

`NTAG -> RC522 -> ESP32 -> USB CDC JSONL -> reader_serial.py -> validation -> local spool match -> proposal`

The reader service remains disabled until physical hardware is connected and its USB identity has been measured. A stable udev rule must be generated from the actual board VID/PID/serial rather than guessed.

## Orca integration decision

OrcaSlicer 2.4.2 is the current pinned engine. PRINTBENCH keeps the C++ patch surface small: product branding, P2S-only selection and removal of irrelevant generic-printer UI. Device integration remains outside the Orca core wherever possible.

Orca's newer Python plugin system is documented for nightlies/releases newer than 2.4.2. PRINTBENCH 2.4.2 therefore must not depend on that API, but future migration should move suitable integration into explicit plugin capabilities once the project upgrades beyond the pinned baseline.

## Implementation order

1. Keep normalized read-only Device API and firmware/capability reporting fully verified.
2. Add a fail-closed command transaction engine with dry-run default and no raw-MQTT passthrough.
3. Add low-risk command definitions only after payloads and post-state are verified against the installed P2S firmware.
4. Add destructive/thermal/AMS writes only with stricter validation and explicit local enablement.
5. Integrate Device API status into PRINTBENCH Studio while keeping credentials in the bridge.
6. Add sanitized MQTT fixtures/mock tests before expanding write support.

## Decision

PRINTBENCH Studio should not be a cosmetic Bambu Studio clone. Orca remains the slicing engine; PRINTBENCH owns a local, testable, fail-closed Device API. Bambu-specific protocol knowledge is isolated behind that boundary, while open spool identification remains an independent acquisition path.
