# S2-01c phase 2 handoff — selectable delay and fault fixtures

Branch `task/S2-01c-gateway-diagnostics-faults`. Phase 2 complete (AC4, the phase-2 half of AC3/AC5, Architect Q4 correction). Design defaults: `.agent/S2-01c-questions-2.md` (Q1-Q5, fail-closed; none blocks phase 3).

## What landed

- **Q4 (answers-2).** `service.py` `MAPPING_ERROR_KINDS` (~62); `_health` counts only those hold kinds for `mapping_error_count`; `held_reports` keeps all. Test adds a `CONFLICTING_REPORT` hold that must not count.
- **Gateway clock.** Ledger schema 4 `publication_clock(lab_run_ref PK, instant, updated_at)`, forward-only/never-deleted triggers (`ledger.py` `MIGRATION_4`). `service.py`: `advance_publication_clock` (~448; SIMULATED only, `PUBLICATION_CLOCK_BACKWARD`, same instant idempotent `advanced:false`), `_publication_instant` (~433, `NO_PUBLICATION_CLOCK` before writes), `admit`/`admit_texts(publication_clock=GATEWAY_UTC|RUN_VIRTUAL)`; `_admit_in` (~565) stamps V3 `published_at` from the run clock while `created_at`, `sequence_state.updated_at`, contact stay real UTC.
- **IPC** (`ipc.py`): ops `advance_publication_clock {lab_run_ref, instant}`, `admit_at_run_clock {snapshot_sha256, lab_run_ref, reports}` (`admit` unchanged, real UTC), `inject_fault {fault: DISK_PRESSURE|CLOCK_OFFSET, value|null}`.
- **Profile/scenario.** `PublicationProfile.publication_clock` (`profiles.py` ~627, default `GATEWAY_UTC`); `REGISTERED_KOBO_PUBLICATION_PROFILE_V2` (~1826) = v1 + `battery-soc-publication-delay`, `RUN_VIRTUAL`, in `PUBLICATION_PROFILES`. Shipped `config/scenarios/kobo-daytime-delayed-publication.yaml` v1 = kobo-daytime v2 + two SOC delay windows (240-250, 705-720).
- **Host.** `host/publication_schedule.py`: Lab-private per-run JSON (`var/publication-schedules`, beside an injected Stage root), clock, world reached/complete, each delayed report (key, source, scheduled release, event id, exact public text, state, release clock, message ID). `lab_execution.py`: `LabSession.publication_clock`; `_stage_registered` routes `RUN_VIRTUAL` to `_stage_registered_virtual` (~2495), others keep the S2-01b delay refusal; `_release` (~2555) persists schedule before the gateway call; `advance_publication(run, instant)` (~2577) returns `{schedule, publication_refused}`; `publication_schedule`, `gateway_diagnostics` (~2627/2632). New Lab refusal kinds in `contracts/.../lab_projection.py`: `PUBLICATION_CLOCK_NOT_SUPPORTED|_BACKWARD|_AHEAD_OF_WORLD|_SCHEDULE_UNREADABLE|PUBLICATION_INSTANT_INVALID`.
- **Publisher** (`gateway_publication.py`): `keyed_reports`, `publish_at_run_clock` (~128), `_admit` maps `DISK_PRESSURE_STOP` to `PublicationRefused("DISK_PRESSURE_STOP")`, `diagnostics()` → `AVAILABLE|GATEWAY_UNAVAILABLE` (never a zero queue), `inject_fault`.
- **Manifest.** `host/fixtures/gateway-fault-scenarios.v1.json`: run setup, public expectations (293 envelopes, 0 holds), delayed cases, fault controls (link loss, WARN, STOP, clock offset), private oracle (windows, scheduled releases).

## Tests (actual results)

- `pytest gateway/tests`: 125 passed (new `test_gateway_publication_clock.py` 9; process test +1 for the new ops; counters test adds a non-mapping hold).
- `pytest host/tests/test_registered_publication_delay.py host/tests/test_registered_kobo_resolution.py host/tests/test_registered_gateway_publication.py`: 26 passed (delay file 7 after the manifest additions; old v1 delay-refusal regression unchanged and passing).
- Full `pytest host/tests backend/tests` (at `4be1988`): 7 failed, 2249 passed, 31 skipped (680 s). All 7 were pinned catalogs the slice must extend, fixed in `cc7279e` (Lab port surface allowlist: `advance_publication`, `gateway_diagnostics`, `publication_schedule`) and `87496a7` (shipped-scenario fingerprint/count/never-shipped-as-v1 lists, the T026 precedent). After the fixes: `test_lab_execution.py -k no_commit_or_release` 1 passed; `test_scenario_fingerprints.py test_run_binds_scenario_to_site.py` 49 passed. Only test files changed after the full run, so it was not repeated.
- `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed. Frontend untouched (no vitest/tsc/build).
- Non-vacuity (mutate committed tree, run, `git checkout --`): `created_at` from `published_at` → 1 failed; backward check removed → 1 failed; virtual stamp ignored → 3 failed; mapping-error narrowing reverted → 1 failed; host schedules nothing (all immediate) → 3 failed; release ignores due instant → 3 failed; AHEAD_OF_WORLD check removed → 2 failed.
- Pinned scenario fingerprint `('kobo-daytime-delayed-publication', 1)`: `130e42fc…e9ad`. No central receipt, server `received_at`, AcceptedEvidence or Site history write anywhere in the phase.

## Phase 3 needs

- Backend `simulator_lab_api.py` + `execution_ports.py`: routes for `advance_publication` (POST, body `{instant}`), the schedule read (pending/released with source, scheduled and actual `published_at` from the Stage envelope, each labelled by clock domain), `gateway_diagnostics` (local; label MEASURED/INJECTED/UNMEASURABLE, current vs last emitted, contact = `OBSERVED_SIMULATED_REPORT`), and `outbox_state` in `registered_stage_payload` (phase-1 carry). Frontend vocabulary for the five new Lab refusal kinds if the client enumerates them (`runPlayback.ts` maps unknown to REFUSED).
- Whether fault injection gets a Lab control or stays fixture-only (packet AC5 does not require a UI control).
- F2/F3 per packet.

## Risks

- Q3: run setup's interval rule means no report is pending after the world run; post-end advancement is proven but releases nothing.
- Explicit advancement after a host restart releases only scheduled delayed reports, not an undelayed series a failed step never admitted (Q5).
- A seal refusal after admission leaves the delayed report PENDING in the schedule until the next advance/step re-drives it (it then reads ALREADY_ADMITTED and is marked released).
