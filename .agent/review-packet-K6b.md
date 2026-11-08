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
| `9f647dd95` | L2 tests 1-4 |
| `aea425856` | Register row R709, the vocabulary scan joins the K6b literals, the page test's settle helper, packet draft |
| (last) | Packet completed |

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

## Verdicts with the rendered literals (L0 and L2)

| State | Headline | Sentence / text |
|---|---|---|
| VERIFIED (L2 1_2, L0 3) | Fuel stayed accounted for | "On 3 fully checked nights after the change, the fuel in the tank matched the generator's modelled use and the recorded deliveries within the stated margin, and the tank sensor sent readings all night." |
| INEFFECTIVE, gap (L2 2) | Target not met | "On the night of {d Mon}, after the change, the tank sensor did not send readings all night." (row "No readings for 90 min", "Sensor gap") |
| INEFFECTIVE, band (L0 3) | Target not met | "On the night of {d Mon}, after the change, the fuel in the tank did not match the generator's modelled use and the recorded deliveries within the stated margin." |
| INCONCLUSIVE (L0 3) | Could not conclude | "Only 2 of 3 fully checked nights after the change in the 14 nights allowed, so no verdict is given" |
| NOT_JUDGED (L2 1_2) | Not judged yet | "Not judged yet: only 2 of 3 fully checked nights after the change" (no outcome row) |
| NO_PLAN (L0 5) | No verification plan yet | cards 2-3 "Not checked yet" |

Every state carries `fixed_line` = H1 verbatim; `value` and `cost_check` are null; no wire key matches
`amount|price|currency|money` (L0 5, L2 3, frontend all five states).

## Acceptance

| Item | Status | Evidence |
|---|---|---|
| Family (choice by grade, exact band, gap, four verdicts) | met | L0 1-3; mutations below |
| `build_fuel_verification_service`; freeze / evaluate / summary; 404/409/503 codes | met | L2 1_2, 1 refusals, 1_3, 2 |
| `effective_from` = first COMPLETE `occurred_at` | met | L2 1_2; KIS-10 at E3 |
| Literals verbatim, H1 fixed line | met | L0 4; `test_out_b2_vocabulary.py` scans `fv.LITERALS` |
| H2 (no value, no money key, no money import, `_verified_values` untouched) | met | L0 5, 7 |
| Page, route, FUEL_VERDICT, API route | met | `fuelVerification.test.tsx` 13, `routeRefs.test.ts`, L2 3 |
| `_SITE_ACTIONS.action_domain`; `action_wire_ref` FUEL_VERDICT (K6a residual closed) | met | L0 8; L2 4 |
| Kisiwa Assure entry, out of `_verified_values` | met | L0 7; MD-FUEL-K6-5 comment in `mini.py` |
| §9m2 request link | met | L0 8, K6a L0 flipped, K6a L2 green |
| KIS-5, KIS-10 | written; L0 self-tests (1 pass + 6 / 9 fail bodies); run at E3 | L0 9 |
| Mill byte-equal | met | L2 5 vs first-commit pins; ch9b2/ch9b3/mv1/mb1/pv1/wd1m green |
| Kobo / Cold / EV unchanged | met | ch5a1/ch5a2/ch6/ch6b2 board contracts green; `fuel_verdict_actions` keys on FUEL_BALANCE |
| Layout evidence | not run | no persisted K6b dataset to `serve` (L2 data lives in dropped pg_harness clones); K8's all-26 recapture adds the page |

## Checks run (final revision)

- L0: `test_k6b_fuel_verification_rules.py` 38 passed; with vocabulary / origin readers / refs / K6a L0: 129 passed;
  `test_out_b2_vocabulary.py` 4 passed with the K6b literals.
- Adjacent non-DB (16 files): green except `test_out_b1_board.py::test_board_imports_only_outcomes_and_stdlib`,
  **pre-existing on main** (main's `board.py` already imports `chain.vocabulary`; K6b adds no import).
- L2 on `assetops_k6_test`: `test_k6b_fuel_verification_postgres.py` 6 passed (~21 s).
- Adjacent Postgres and golden contracts (18 files, 6 min 54 s): 277 passed, 6 failed, all
  `test_w301_estate_golden_postgres.py` (`$.summary.claims` gains `count.opportunities` "Not known yet"). Not a K6b path
  (claims / opportunities untouched); judged pre-existing, **not re-run on main** (no clean main checkout here).
- Frontend: `fuelVerification.test.tsx` 13 passed (x3 after the settle fix), `routeRefs.test.ts` 63,
  `millVerification.test.tsx` 10; `tsc --noEmit` clean.
- Guards: `check-architecture`, `check-agent-workflow`, `check-navigation-truthfulness` passed; `check-all.ps1 -Python
  <plan2 .venv>`: all 17 passed.
- Non-vacuous proofs (committed code mutated, run, `git checkout --`): `<` -> `<=` in `later_nights`; choice filtered on
  `passes`; a 1e-5 L tolerance; the site_index fuel branch disabled; `fuel` added to `_verified_values`. 9 named
  failures (L0 + K6a L0), reverted clean.

## Known deviations (S-b4 technically triggered; each forced by a spec item)

1. Files outside the list: `route-refs.json`, `routeRefs.test.ts` (KINDS validators); `test/linkRefs.ts` (the spec's
   round-trip); `test_ch9b1_origin_readers.py` (classify the new reader: `fuel_verification.py` both/7,
   `verification.py` 5->8, `postgres_action_store.py` 15->19); `test_k6a_fuel_action_origin.py` (§9m2 flip);
   `.agent/mock-departure-register.md` R709 (guard 12 needs a registered id; may collide with K5's numbering).
2. `VerificationPorts.site_visits` (third port, PRE-FLIGHT (d)); `fuel_plan_context` also returns the origin claim's
   window id and the Site code, and reads the plan only with `rule_id = fuel-...`.
3. `fuel_verification.py` imports `chain.refs` (stdlib-only) for the wire's Refs.
4. `fuel_summary_wire(..., site_visit=)`; the Activity panel is omitted when `activity` is null and the Owner cell when
   `owner_label` is null (no invented gap words).
5. FUEL_FINDING items copied verbatim from K5's `418cd75ec`; the second to merge takes main's copy.

## Residual risk

- KIS-5/KIS-10 DB plumbing in `demo_combined_finish.py` is untested until a Kisiwa dataset exists (E3).
- `complete()` reads `terms["unknown_slots"]` as specified; an assessed window lacking it would raise.
- The lazily built global work read behind `site_visits` is never disposed.
