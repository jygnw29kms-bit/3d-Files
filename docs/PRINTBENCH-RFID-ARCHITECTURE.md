# PRINTBENCH RFID Architecture

## Decision

PRINTBENCH treats Bambu AMS RFID and open NFC tags as two separate identity sources.

### Native AMS path
- Keep the stock AMS/P2S path read-only for observation and genuine Bambu spools.
- `ams_get_rfid` may be issued actively because it is a read request.
- `ams_filament_setting` remains blocked unless write access is explicitly enabled.
- Native MQTT observations are stored by `ams_rfid_diag.py`.

### Open NFC path
- NTAG215/216 is handled by an independent reader, not by pretending to be a Bambu tag.
- A reader reports UID + optional parsed metadata to `external_tag.py`.
- The UID is matched against the private PRINTBENCH spool inventory.
- A matched spool produces the same guarded `ams_filament_setting` proposal used by native matching.
- No proprietary Bambu keys/signatures are needed for PRINTBENCH tags.

## Why

Real P2S + AMS 2 Pro tests on 2026-10-14 showed that Slot 4 performs RFID read cycles for an ordinary spool both with and without an NTAG216 attached. In both cases MQTT exposed zero UID/UUID and no valid Bambu tag result. Therefore the stock AMS firmware cannot be relied on as the identity transport for open NTAG216 tags.

Community implementations validate the external-reader approach. BambuTagger-AMS uses four RC522 readers, recognizes NTAG-based standards, and synchronizes tray data to Bambu printers over MQTT. OpenTag3D explicitly supports NTAG215/216.

## Preferred hardware path

For the existing PRINTBENCH Pi bridge, use four RC522 readers on the Pi SPI bus, one per AMS slot. MOSI/MISO/SCK are shared; each reader gets its own chip-select and reset GPIO. This mirrors the proven BambuTagger topology while keeping identity and inventory logic on the Pi.

The Pi image enables SPI and includes `python3-spidev` and `python3-gpiozero` for this path.

## Test tag

`tools/ntag_test/` contains a deterministic NTAG216 NDEF test payload. It is intentionally not a Bambu tag clone. Use it for reader bring-up, UID binding, trace searching and end-to-end slot matching.

## Safety

- Raw NFC UID stays local/private.
- Public APIs expose only binding state, never raw UID.
- Bambu write commands remain opt-in and disabled by default.
- External tag metadata is advisory until matched to a local inventory record.
- Printer access code and SSH private keys never enter Git.