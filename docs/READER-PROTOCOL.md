# PRINTBENCH External Reader Protocol v1

PRINTBENCH separates tag acquisition from spool logic. The recommended hardware path is one ESP32 controlling up to four RC522 readers over shared SPI. The ESP32 is connected to the Pi by USB CDC serial; the Pi remains responsible for validation, spool matching and any later AMS action proposal.

## Transport

Default device: `/dev/ttyACM0`, 115200 baud, UTF-8 JSON Lines. One observation is one JSON object followed by `\n`. The service is optional and disabled until reader hardware is installed.

The serial transport is intentionally preferred over Wi-Fi for the first hardware revision: no additional listener/firewall rule, no reader credentials, deterministic USB topology and no dependency on a third-party MFRC522 Python module on the Pi.

## Message schema

```json
{"version":1,"reader_id":"esp32-ams","ams_id":"0","slot_id":3,"uid":"04A1B2C3D4E5F6","tag_type":"ntag216","payload":{"format":"opentag3d"}}
```

Required semantics:

- `version`: exactly `1`.
- `reader_id`: stable reader identifier, 1–64 characters.
- `ams_id`: logical AMS identifier; current product scope uses `0`.
- `slot_id`: zero-based slot, exactly `0..3` for AMS 2 Pro.
- `uid`: non-zero NFC UID. Separators are accepted and normalized locally.
- `tag_type`: `ntag`, `ntag213`, `ntag215`, `ntag216`, `mifare_ultralight` or `unknown`.
- `payload`: optional parsed metadata object. Maximum serialized payload is 2048 bytes.

Maximum complete line size is 4096 bytes. Invalid UTF-8, malformed JSON, bad protocol version, zero/invalid UID, unsupported tag type, out-of-range slot or oversized payload is rejected.

## Privacy and trust

The raw UID is a local identifier, not an authentication factor. It may be used locally to match a spool but is never returned by the browser API and is omitted from event payloads/log messages. Reader input never directly executes an AMS command. A valid match can only create a validated `ready` or `blocked` proposal; AMS writes remain disabled by default.

## Service

`printbench-reader.service` runs `reader_serial.py`. It is installed by the Pi image but not enabled automatically because the USB device path cannot be validated before hardware exists. `/etc/printbench/reader.env` can override:

```text
PRINTBENCH_READER_PORT=/dev/ttyACM0
PRINTBENCH_READER_BAUD=115200
```

Once the hardware is connected and verified:

```bash
sudo systemctl enable --now printbench-reader.service
systemctl status printbench-reader.service
```

The production design should later add a udev rule based on the actual ESP32 USB VID/PID/serial so the reader receives a stable `/dev/printbench-reader` symlink. That rule must be derived from the purchased board rather than guessed in advance.
