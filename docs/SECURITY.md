# PRINTBENCH Security Model

## Secrets

Printer LAN credentials live only in `/etc/printbench/bambu.json` on the Pi or the user's local Bambu configuration. They must never be committed, returned by browser APIs, embedded in URLs shown to clients or written to logs. SSH private keys and web admin tokens are also local-only.

## Network

The P2S is not exposed to the internet. Pi SSH and the Pi UI are LAN-only. The current UI firewall rule is limited to `192.168.178.0/24` on TCP 8080. Printer MQTT/RTSPS/FTPS connections are initiated from trusted local components.

## Browser API

The Pi UI is read-only. SQLite is opened with URI `mode=ro` and `PRAGMA query_only=ON`. Browser endpoints expose selected/sanitized fields only. Raw MQTT payloads, LAN credentials and complete NFC/RFID UIDs are excluded. CSP, frame denial, no-referrer and restrictive Permissions-Policy headers are sent on responses.

## Camera

`printbench-camera.service` reads RTSPS using the printer credential only inside the service process. It writes a volatile JPEG to `/run/printbench-camera`. The HTTP service exposes a same-origin JPEG/MJPEG bridge without exposing the RTSPS URL or credential. Viewer activity is signalled through a volatile marker in `/run`; MJPEG clients are bounded and runtime files disappear on reboot.

## RFID / NTAG

Raw tag identifiers are private local identifiers, not authentication credentials. They may be stored in the local inventory/matching database where required, but are not exposed to browser clients. An NFC UID alone must never authorize an AMS write or privileged operation.

## Writes

AMS write commands are disabled by default. Read-only RFID scan requests are distinct from material-setting commands. Any future write workflow must validate slot, material, temperature range and current machine state and require an explicit enablement boundary.

## USB serial reader

The optional external reader accepts bounded JSON Lines over a local USB serial device. Messages are versioned, size-limited and validated before local matching. Raw UIDs are never copied into browser responses or event payloads, and reader observations cannot directly authorize AMS writes.

## Control engine

The normal LAN browser remains read-only. A state-changing `POST /api/v1/control/...` surface exists only for the embedded PRINTBENCH/Orca client and requires a 64-hex `X-API-Key` checked with constant-time comparison. The Pi-side token is stored outside the repository at `/etc/printbench/control.token` (root:printbench, mode 0640); the matching desktop token stays in the local Orca data directory and is never committed. Missing or malformed tokens fail closed.

Commands are whitelist-only, validated and fail closed by default. `PRINTBENCH_CONTROL_WRITES=1` is required globally; destructive, thermal and AMS actions additionally require their own policy switches, and destructive actions require explicit confirmation. There is no raw MQTT or arbitrary G-code endpoint. Observable commands are not considered successful merely because MQTT publish/ack succeeded: their reported post-state must match within the verification window. The standalone `control_cli.py` uses the same command engine and policies.

## Printer TLS

P2S MQTT uses a certificate pinned during explicit local pairing. The pin is stored at `/etc/printbench/p2s-cert.pem` and loaded as the local trust anchor. Missing pins fail closed. `PRINTBENCH_TLS_ALLOW_UNPINNED=1` exists only as an explicit recovery/diagnostic escape hatch and must not be enabled in the normal installation.
