# Review packet: DIESEL-K6b, the fuel after-check (`fuel-residual-within-band-1`)

- Task: build sheet DIESEL-1 §9m.1 and §9m.4 (ruling DIESEL-1-R3m), plus §9m2 (the request link's fuel address).
- Branch `task/DIESEL-K6b-fuel-verification`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k6b`, from main `9d7641f9a`
  (K6a merged at `bda3c666e`, migration 0057; K6b adds no migration).
- DB: `assetops_k6_test` only (pg_harness clones). No prepare, tick or full suite.
- USER_REVIEW_REQUIRED: no (Kisiwa is opt-in until K7-F; the page joins the K8 all-26 recapture).

## Commits

| Commit | What |
|---|---|
| `d25f95ccb` | First commit: the mill path pins (`tests/fixtures/k6b_mill_pins.json`) captured on unchanged mill code, with the L2 item-5 comparison |
| `aa7020754` | The family, service methods, store context, composition, API route, FUEL_FINDING/FUEL_VERDICT Refs, chain Ref fix, board entry, request link, page, client, frame, route, KIS-5/KIS-10, L0 and frontend tests |
| (see report) | L2 tests 1-4, packet |

## Pre-flight answers (no code first; nothing here needed the Architect)

- (a) Verification store builder: `actions/composition.py:40` `build_action_store` (`PostgresActionStore`). Production
  clock: `actions/service.py:76` `utc_now` (`read_scope.clock()`), the ActionService default (`:245`).
- (b) `action_api.py:236` builds `VerificationService(service)` from the ActionService; `service.verification_ports` comes
  from `actions/composition.py` `verification_ports`. K6b takes the "existing one gains the ports" branch: the three
  fuel ports are added there, built lazily (`_Lazy`), so no existing route's wire changes (no existing method reads
  them). `build_fuel_verification_service(url, test_clock=)` is added for tests and story time.
- (c) Validators fed by `refs.KINDS`: `tests/test_ch5a2_refs.py:21` (fixture kinds == KINDS) over
  `frontend/src/shell/__fixtures__/route-refs.json`, and `frontend/src/shell/__tests__/routeRefs.test.ts:15` (the
  sorted kind list). `test/linkRefs.ts` parses hrefs back to Refs. No JSON schema of Refs exists.
- (d) The case's SITE_VISIT records: `work/adapters/postgres_global_read.py:134` `GlobalReadTx.case_operational_records`
  through `work/composition.py:88` `build_global_work_read(...).snapshot(...)`. `actions/composition.py` may import
  `work.composition` (composition to composition; `configuration-persistence.ps1` rule 1 keeps adapters to their own
  composition). Wired as a third port, `VerificationPorts.site_visits`.
- (e) `actions` -> `fuel_balance` imports: no dependency-direction rule covers them (`tools/checks/dependency-direction.ps1`
  constrains simulator, evidence and site_overview only); `check_chain_structure.py` (a) is not touched. No S-b3.
- (f) `chain/lifecycle.py:74` `measures_for` returns `()` for a mechanism without `clean_day_measures`, and
  `complete_days` returns an empty set for no measures (`:293`): an `UNEXPLAINED_FUEL` thread never closes by clean
  days but nothing raises. `plan_lifecycle` does not key on the mechanism. No S-b6.
- (g) No golden compares `_SITE_ACTIONS` row dicts: `site_chain.actions_of` / `opportunity_actions` copy named keys;
  `test_wd1m_mill_source_postgres.py:243-248` compares two reads of the same statement. The new key is inert.

## Outcome delivered

- `B/actions/fuel_verification.py` (pure): `later_nights`, `complete`, `passes`, `assess`, `plan_row`, `outcome_rows`,
  `fuel_summary_wire`, `used_dates`, the literals verbatim, `FuelResidual`; registered last in `verification_families`.
- `VerificationService.freeze_fuel_plan` / `evaluate_fuel_plan` / `fuel_summary`; `PostgresActionStore.fuel_plan_context`
  / `freeze_fuel_plan` with `FUEL_PLAN_COLUMNS`; the mill methods, `DOMAIN_PLAN_COLUMNS` and the mill wire unchanged.
- `GET /api/sites/{site}/domain-work/actions/{id}/fuel-verification`; Ref kinds `FUEL_FINDING` (K5's text, verbatim)
  and `FUEL_VERDICT`; `_SITE_ACTIONS.action_domain`; `action_wire_ref` gives a fuel Action `FUEL_VERDICT` (the K6a
  residual is closed: no ACTION Ref to a missing W1 page); `work/site_index.py` fuel link
  `/sites/{site}/domain-actions/{aid}/fuel-verification` when lineage is present (§9m2).
- Kisiwa Assure "Verified results" entry (`FuelVerdictFact`, `site_chain.fuel_verdict_actions`); `_verified_values`
  untouched (signature pinned by an L0 test).
- `F/sites/SiteFuelResidualVerification.tsx`, `F/sites/fuelVerificationClient.ts`, `SiteFuelVerificationFrame`, the route.
- KIS-5 and KIS-10 (`tools/demo_combined_rows.py` `kis5`/`kis10`, wired in `tools/demo_combined_finish.py` after KIS-4).

## Mock to new (MOCK DEVIATIONs)

| Id | v69 | Fuel page / board |
|---|---|---|
| MD-FUEL-K6-1 | `:501` one target with guardrails, metric rows | one target, no guardrails; the table lists nights |
| MD-FUEL-K6-2 | `:500` target change, reserve breaches, critical service, final outcome | nights checked, fuel accounted for, tank sensor, final outcome; no money card |
| MD-FUEL-K6-3 | "Provisional target pass" badge | not shown; "Not checked yet" / the not-judged text |
| MD-FUEL-K6-4 | "Outcome evidence" prose and example button | the server's sentence and the fixed H1 line |
| MD-FUEL-K6-5 | Assure entries open their Action | the fuel entry opens its verdict page (FUEL_VERDICT); no value line |

## Acceptance (criterion by criterion): see the report section filled in at the end of this file.
