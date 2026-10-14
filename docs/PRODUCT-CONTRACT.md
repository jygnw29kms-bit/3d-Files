# PRINTBENCH Studio Product Contract

## Hardware scope

PRINTBENCH Studio targets one hardware family only: **Bambu Lab P2S with AMS 2 Pro**. OrcaSlicer identifies the P2S as `model_id=N7`. Supported nozzle diameters are 0.2, 0.4, 0.6 and 0.8 mm; 0.4 mm is the PRINTBENCH default. The normal product UI must not expose arbitrary printer creation or unrelated vendor families.

## Orca boundary

`app/orcaslicer/` is treated as upstream engine code. The pinned baseline is OrcaSlicer 2.4.2 (`v2.4.2`, tag SHA `8500fcdccaa10b5099ac20d252af3a7c560046f1`). PRINTBENCH changes should prefer adapters, services and configuration outside the Orca C++ core. Core patches are allowed only when a product requirement cannot be implemented safely at the boundary and must be documented separately.

The upstream Python plugin system is documented for nightly builds/releases newer than 2.4.2. PRINTBENCH therefore does not depend on that plugin API while pinned to 2.4.2, but the architecture is intentionally compatible with migrating integration code into plugins later.

## Local bridge contract

The Pi bridge is the local machine integration layer. It may read P2S telemetry, AMS status, camera data, print sessions and local spool metadata. Browser-facing APIs must sanitize credentials, raw RFID UIDs and private transport details.

AMS state-changing commands are fail-closed by default. Read/diagnostic operations and state-changing operations remain separate code paths.

## Verification

Run `python tools/validate_product_contract.py`. The validator checks the pinned Orca version, P2S model ID, supported nozzle set and required P2S machine profiles.
