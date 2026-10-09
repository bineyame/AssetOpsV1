# S2-01c phase 1 — design choices the packet and decisions do not fix

Implementer, 2026-10-09. Each item was built with the stated fail-closed default; none blocks phase 2. Architect may overturn any of them cheaply (all are local to `gateway/` and the new contract).

## Q1 — Disk-pressure provenance on the wire

AC3 says never claim actual hardware pressure from an injected case. `GatewayDiagnosticsV1` (technical design 3) has only `disk_pressure: OK|WARN|STOP`.
Options: (a) keep the recorded wire; provenance (`MEASURED|INJECTED_FAULT_FIXTURE|UNMEASURABLE`) lives in the local read only; (b) add a `disk_pressure_provenance` field to V1 (a contract amendment).
**Built: (a).** The wire states the gateway's operative state (it really refuses acquisition at STOP); the gateway is registered `SIMULATED`, and Lab shows provenance. S2-02 must not present a central STOP from a SIMULATED gateway as hardware pressure.

## Q2 — What STOP refuses

AC3: STOP refuses new acquisition before sequence assignment.
**Built:** `admit`/`admit_texts` refuse the whole call with `DISK_PRESSURE_STOP` before any write (no envelope, sequence, hold or contact row; replays included). `seal` and diagnostic emission still run (they are not acquisition and move retained evidence toward upload). A probe that fails is STOP, labelled `UNMEASURABLE`. Alternative: also refuse sealing at STOP.

## Q3 — Emission identity and cadence

"Retries and restart return the same identity and bytes."
**Built:** at most one diagnostic per declared cadence slot (`floor(observed_unix / cadence)`, `UNIQUE(gateway, epoch, slot)`); an emission inside an occupied slot returns the stored row. A clock earlier than the last slot refuses (`CLOCK_BEHIND`). The serve process ticks at `min(15 s, cadence/2)`. Default config: cadence 60 s, WARN below 1 GiB free, STOP below 256 MiB, frozen at provisioning (a different later declaration refuses `DIAGNOSTIC_CONFIG_FIXED`).

## Q4 — Queue and mapping-error definitions

**Built:** `queue_count` = envelopes in `STAGED|READY|IN_FLIGHT` (Lab `STAGED` envelopes are local, undelivered); oldest age from their `created_at`. Holds are not queued; `mapping_error_count` = distinct `mapping_hold` rows (all hold kinds). The local read adds the breakdown: sealed pending batches/envelopes, unbatched, held, active seal refusals, dead letters.

## Q5 — Source contact

Per the amended AC3: recorded (gateway real UTC, not `source_time`) once a report resolves to a permitted source, whether then admitted, replayed or held; provenance `OBSERVED_SIMULATED_REPORT` on a SIMULATED gateway. Never-heard sources are `null`.
