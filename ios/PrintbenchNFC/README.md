# PRINTBENCH NFC Companion

Native iPhone companion for PRINTBENCH spool tags.

## Why native iOS?
Safari/iOS does not expose Web NFC, so a PWA cannot write NTAG216 tags. This app uses Apple's Core NFC API.

## Target flow
1. Create or open a spool in PRINTBENCH.
2. PRINTBENCH shows a signed QR code for the spool.
3. Scan the QR with this app.
4. Hold the iPhone against the NTAG216 sticker.
5. App writes a compact NDEF record and reads it back for verification.
6. App captures the physical tag UID. The backend will bind this immutable UID to the PRINTBENCH spool record.
7. Future AMS V2 integration can map a UID observed on the AMS RFID path directly to this spool.

## Tag contents
The NFC tag intentionally stores only stable identity data:
- schema version
- PRINTBENCH spool ID
- canonical PRINTBENCH spool URL

Mutable information remains in PRINTBENCH:
- remaining filament / weight
- vendor and material metadata
- color
- price and cost history
- drying history
- calibration/profile data
- AMS slot assignment
- print history

This avoids stale data on the physical tag and makes the tag UID the long-term hardware identity.

## QR payload
Preferred server-generated payload is JSON:

```json
{
  "version": 1,
  "spoolId": "PB-000001",
  "displayName": "KINGROON HS-PLA Schwarz",
  "material": "PLA",
  "vendor": "KINGROON",
  "colorHex": "#111111",
  "claimURL": "https://www.dezender.de/3d-druck/spool/?spool=PB-000001&sig=...",
  "signature": "..."
}
```

The app also accepts a PRINTBENCH URL containing `spool=` and optional `sig=` query parameters.

## Build
The project is described by `project.yml` for XcodeGen.

```bash
brew install xcodegen
cd ios/PrintbenchNFC
xcodegen generate
open PrintbenchNFC.xcodeproj
```

Enable automatic signing for the iPhone development team and build to a physical iPhone. NFC cannot be validated in the iOS Simulator.

## Security direction
The QR signature must be verified by the PRINTBENCH backend before a tag UID is bound to a spool. Do not put printer access credentials, MQTT credentials, API secrets, prices, customer data, or mutable inventory state on the NFC tag.
