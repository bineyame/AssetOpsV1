# W2-05a review packet (EV Foundation)

Branch `task/W2-05a-ev-foundation`. Spec: `.agent/W2-05a-build-spec.md` (`D-2026-10-18-w2-05-buildspec`); rulings Q1-Q8, QA-QP and the run-7 wording closure applied (see `.agent/W2-05a-phase-handoff.md`). Not merged to main.

## Commits
1 `2d8b323d` vocabulary, parser, typed schedule, validator; QC/QD `932ad981`; 2 `880384d3` EV roles, v4 matrix, binding publication, fixture; 3 `5a7b46c6` selected API; QH-QL `ca3ef6ab`; 4 `ee8b92d7` three UI routes + captures (then QM-QP, ev-sld compaction, run-7 wording); merge of main (W2-04 `0023`) `5df0b94e`; 5 `334c7c70` migration `0024_w2_ev_config` and tests.

## Spec conformance
- Q7: `0024_w2_ev_config`, `down_revision = 0023_w2_cold_consequence`, created after 0023 merged. Adds only the partial index `accepted_evidence_ev_measurement (site_id, session_id, connector_id, source_time, id) WHERE family='MEASUREMENT' AND measurement='INTERVAL_DELTA'`. Foundation history and the 0020 family CHECK untouched; no new configuration table. Downgrade refuses while any EV interval-delta exists (nothing deleted), then drops the index.
- Tests `backend/tests/test_w205a_ev_migration.py` (3): upgrade shape + family CHECK kept + no config table; downgrade drops only the index and re-upgrade restores it; refusal with an EV measurement (rolled back, row count unchanged). Non-vacuous: removing the refusal call made the refusal test fail (`DID NOT RAISE`), reverted.
- Existing tests updated: head references 0023 -> 0024 in s1/s2/s4/s405/w200/w201/w203/w204 files; `test_w200` 0020 case 2 (accepted interval delta) now expects 0024's refusal first (0024 sits above 0020), so the 0020 interval-delta refusal branch is no longer reachable by that case; the event, conflict and cold-job cases still prove 0020's refusal.
- Properties/carriers, parser/render bytes, vocabulary, API, three routes: commits 1-4 (handoff).
- No EV SQL writer outside Foundation/binding store; no accepted-evidence insert in 05a.

## Captures (`.agent/W2-05a-evidence/index.html`, `evidence.json`)
9 pairs x 1440/390 (foundation, readiness, sld x stocked / missing-role / empty), 108/108 claims at commit 4; ev-sld stocked and empty recaptured after run 6/7 (ev-sld-missing-role not recaptured; parts table unchanged in kind). 403/503 are jsdom-tested only. The ev-lab binding set is recorded with a timestamp five minutes in the future (run 7 note: wait five minutes before capture or bindings read as zero).
Merge from main re-check: changes to shared UI were `ui/Badge.tsx` (optional `className`, no change when omitted), `App.tsx`/`SiteDetailFrame.tsx` cold wiring, `panelStructure.ts`, `productVocabulary.json` (append). None alters EV markup or styling, so EV captures were not recaptured; the full vitest suite (including the evFoundation panel-structure tests) passes on the merged tree.

## Panel heights at 1440 (app / mock, limit 1.3x)
foundation 1.22 / 1.22; readiness table 1.15 (missing-role 1.31, extra Site-import row; QO rule), gateway 1.24 (1.17 missing-role); sld diagram 0.87; sld parts table 1.29 (370/287). The missing-role readiness 1.31 is marginally over 1.3x and is a recorded value, not a new decision.

## Checks at head `334c7c70` (code unchanged afterwards)
- `tools/check-all.ps1`: 10/10 guards passed (includes architecture, dependency registry, screen ledger).
- `tools/writer_guard_probes.py`: NOT completed. 143 probes at ~70 s each; the full run was stopped after ~50 min and a `--seam` run after ~10 min (both stopped; tree restored clean). Observed outputs were all CAUGHT before stopping. Commit 5 adds no writer, so the unrun remainder is unverified.
- Frontend `npm.cmd test`: 87 files, 2250 passed, 0 failed. (An earlier run concurrent with the probes had 1 failure from load; the isolated rerun is clean.) `tsc --noEmit` exit 0.
- Backend full real-Postgres suite, `-n 2 --dist loadfile`, Postgres 127.0.0.1:55432 (private `w205a5_test`, dropped): 2944 tests in 1605 s (26:45), JUnit failures 1, errors 0, skipped 0. The one failure, `test_runs_api.py::...PropertylessFoundation::test_the_shipped_scenario_blocks_only_on_the_values_this_site_lacks`, was `FileNotFoundError` for the gitignored `var/sites/mg-001.yaml`, absent in this worktree (environment, not code). After copying that ignored file from the main checkout the whole `test_runs_api.py` passes (28). No second full suite was run.
- Host suite, serial after backend: 708 passed, JUnit failures 0, errors 0, skipped 0, 553 s.

## Decisions
No implementer decisions were taken in commit 5. The migration follows the spec text; the partial-index predicate (`family='MEASUREMENT' AND measurement='INTERVAL_DELTA'`) is the spec's "EV measurement" read literally and is flagged for Reviewer confirmation.

## Residual risk
writer_guard_probes unrun to completion; backend full-suite zero-failed rests on one environmental failure fixed by rerunning one file; missing-role readiness 1.31x.

## Run 8 fix round (review r1; rulings in build spec "Run 8 rulings")

Code head: see the final commit of this branch; code last changed in `W2-05a Run 8: widen EV SLD viewBox`.

| Finding | Fix | Proof |
|---|---|---|
| H1 | `EvSingleLineDiagram`: three fixed feeder slots (Feeder 1 CB/Charger 1, Feeder 2 CB/Charger 2, Feeder 3 CB/Depot auxiliary); empty slot 2 reads `Charger 2 · Not declared`, `Rating not declared · No connector declared`; more than one extra charger folds into slot 2 as `Additional chargers` with names listed; rail fixed `Connector 1`, `Connector 2`, `Site meter`, `Billing system` by declared charger/connector order (asset-ID tie break), undeclared positions say `Not declared`; viewBox widened 1000 to 1090 after the capture showed slot-2/auxiliary text clipped | `evFoundation.test.tsx` (stocked, missing-feed, zero-charger, three-charger, reversed bindings) |
| M1 | Financials, Assumptions, Health > Data sources (header action and footer) use `UnavailableLinkEntry`; Site model, Single line diagram, Evidence links stay live | new test: labels, non-navigation, no mini-grid hrefs in panels, live links, stocked and missing-role |
| M2 | `validate_bindings`: `BINDING_EV_CONNECTOR_NOT_DECLARED` (empty binding index, exact message) when any covering revision has no `EV_CONNECTOR` | Postgres tests: empty, Site-import-only, overlap with a connector-free revision (no binding revision written); valid set still publishes |
| M3 | `_ev_connector` docstring corrected; parser, 0020 CHECK and 0024 unchanged | `test_source_envelope_v4.py`: null-correlated `interval mean` and `state point` accepted, either nonnull ID refused (`CORRELATION_INVALID`) |
| M4 | `install_ev_lab` publishes at the install clock; no +5 min | Postgres test: recorded_at = install clock, snapshot readable at once, later Foundation revision allowed, reinstall writes no extra binding revision |
| L1 | accepted as bounded exception (missing-role readiness 1.31x earlier; now panel 1 is 359/313 = 1.15, gateway 1.21 missing-role); 390 px viewed, no clipping | captures |
| L2 | `IN_PAGE_UNAVAILABLE_STATUS` exemption decision/reason names the W2-05a placements | check-all missing-claim scan passes (39 tagged, 10 baselined) |
| L3 | `UNIT_RANGES` adds `s` 0..86400 and `kWh` 0..1e8 | vocabulary tests (boundaries inclusive, 1e300, inf, nan, negative refused); Postgres: 1e300 clock bound refuses `EV_CONFIGURATION_INVALID` and writes no revision |
| L4 | part cell ends `Load manager · Not declared`; `power sharing` text deleted | stocked and missing-feed assertions |

Heights at 1440 (app / mock): foundation 1.22 / 1.22; readiness panel 1 1.15, gateway 1.27 (1.21 missing-role); sld diagram 539/552 = 0.98 (three feeder slots now drawn), parts table 370/287 = 1.29. Recaptured all 9 pairs at 1440/390 (108/108 claims, stocked `at=2026-10-06`, missing-role `2026-10-08`, empty `2026-09-01`); viewed ev-sld stocked/missing-role/empty and ev-readiness missing-role/stocked at 390. Private DB `w205r8cap_test` seeded by `install_ev_lab` plus one gap revision; no wait needed (M4); DB dropped, servers (9734/6134/CDP 9735) stopped. Capture app URLs are `/sites/EV-LAB-001/foundation[/readiness|/sld]`.

Checks: frontend `npm.cmd test` 87 files, 2252 passed; `tsc --noEmit` 0; `tools/check-all.ps1` 10/10. Backend focused (vocabulary + EV Foundation Postgres) green; gateway v4 file 66 passed. Full real-Postgres backend suite at the final code revision, `-n 2 --dist loadfile`, private `w205r8_test` (dropped): 2960 passed, JUnit failures 0, errors 0, skipped 0, 1609 s. `var/sites/mg-001.yaml` was present and was deleted afterwards. Host suite not run: no host code changed.

Writer-guard probes: WAIVED per the Run 8 ruling (no rule-8 guard, SQL writer or accepted-evidence write path changed). This is a waiver, not a pass; 05b keeps its own gate.

Open points: (1) the ruling calls `UnavailableLinkEntry` "focusable", but the existing component (and `expectUnavailableEntry`) is deliberately not a tab stop; I kept the component unchanged. (2) The M2 mutation proof (disable the check, watch the new tests fail) was blocked by the permission classifier, so non-vacuity of the M2 tests is not demonstrated by mutation; they assert the code, empty binding index, and unchanged binding-set list. (3) L4 missing-feed copy is `Not declared; Load manager · Not declared`.

## Run 8 confirmations (r2)

| Item | Result | Proof |
|---|---|---|
| M1 | `UnavailableLinkEntry` unchanged; visible `{label} · Not available yet`, `aria-label` `{label}, Not available yet`, no tabIndex/link/handler | `evFoundation.test.tsx` readiness test: visible text, aria-label, no tabindex/focusables, click does not change location, plus the shared `expectUnavailableEntry` checklist |
| L4 | missing-feed cell is exactly `Grid supply · Not declared; Load manager · Not declared`; declared-feed cell still ends `Load manager · Not declared` | assertions at stocked (line ~485) and missing-feed (line ~623) |
| H1 | viewBox `0 0 1090 396` ratified; no change | confirmed in `SiteSingleLineDiagram.tsx` |
| Recapture | not needed: missing-role fixture declares the feed asset (limit null), so its cell is unchanged; the L4 string only renders for a feed with no asset, which is not a captured state | no servers or DB used |

Checks: frontend vitest 87 files / 2269 tests passed; tsc --noEmit clean; check-all 10/10 guards passed.
