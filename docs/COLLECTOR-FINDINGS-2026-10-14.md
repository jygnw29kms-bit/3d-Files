# PRINTBENCH Collector findings — 2026-10-14

## Bambu Lab P2S chamber temperature

The P2S does expose its chamber temperature over LAN MQTT, but not only through the legacy `print.chamber_temper` field.

Verified live on the project P2S:

- `print.device.ctc.info.temp` = chamber temperature in °C
- `print.info.temp` currently mirrors the same value and can be used as an additional fallback
- observed value: 26 °C, matching the printer display exactly

Collector normalization therefore resolves chamber temperature in this order:

1. `print.chamber_temper`
2. `print.device.ctc.info.temp`
3. `print.info.temp`

This keeps compatibility with older Bambu MQTT payloads while supporting the P2S payload shape.

## Live web telemetry incident

The frozen public live feed was caused by two independent configuration/runtime issues:

- the Pi had no local `.push-token`, so HTTPS ingestion could not authenticate;
- `/etc/printbench/collector.env` had `PRINTBENCH_WEB_PUSH=0`, disabling automatic web pushes.

After restoring the existing token and enabling `PRINTBENCH_WEB_PUSH=1`, HTTPS ingestion resumed successfully. The live feed then reported the chamber value correctly and continued updating automatically.

## Collector hardening

The collector now isolates tasks that can block network I/O:

- web push runs in its own worker thread on a 5-second cadence;
- spool synchronization runs in a separate worker with its own database connection;
- long-range preview data is sampled at SQL query time instead of loading every telemetry row before downsampling.

This prevents spool API latency or a growing telemetry database from freezing public live telemetry.

## AMS 2 Pro drying telemetry

A live drying cycle was verified while the AMS 2 Pro heater was physically running. The collector exposed:

- `ams.drying = true`
- actual AMS temperature: 44.5 °C
- configured drying temperature: 45 °C
- configured profile: PLA
- configured duration: 12 h
- `dry_time = 695` as the current raw drying-time value
- humidity level: 2
- `humidity_raw = 23`

The 44.5 °C measured value tracking a 45 °C target confirms that the AMS temperature and drying-state telemetry are live and useful for profile validation and drying-history logging. The collector should preserve the raw `dry_time` value until its exact unit/semantics are independently verified.
## Operational note

The push token remains a local secret and must not be committed. A provisioned Pi needs the existing `.push-token` installed locally for HTTPS ingestion to work.
