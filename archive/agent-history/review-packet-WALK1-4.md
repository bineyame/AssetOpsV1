# Review packet: WALK1-4 (Kobo reports the midday solar-check readings)

Branch `task/WALK1-4-kobo-solar-readings` from main `362dc4fe6`. Spec: `AssetOpsV1-plan2/.agent/build-sheet-WALK1.md`
§6 WALK1-4, Addendum 4 (D-W1-7..9), Addendum 5 (D-W1-10..13), §8 register R681-R684. Phase 1:
`.agent/WALK1-4-phase-1-handoff.md`. USER_REVIEW: none for this slice. The owner walkthrough resumes after G2.

## Outcome delivered

Grow MG-1 opportunity → driver: spare solar → evidence: charge request, available and used solar, declared margins.
Kobo publishes the charge request (model v6, publication v5) under roles-4 from commissioning. The noon solar check
now gives ELIGIBLE on the sunny days. The S board leads with "25–31 kW of daytime solar unused", and S−1 shows the
priced sales day (42.08 USD).

## Files materially changed (phase 2; phase 1 is in the handoff)

- `backend/assetops_backend/mini_depth/store.py`: `HourRows.row_bindings`. These are the as-accepted binding revisions
  of the candidate rows, read by id whatever their set's `superseded_at` (D-W1-10).
- `backend/assetops_backend/mini_depth/inputs.py`: each row is judged under its own binding. The binding must have the
  same role and asset and be in force at `source_time`. The pinned roles-4 set must also bind the same role and asset
  at that time. Lineage: `HourInputs.binding_set_revision_ids` = the pinned set plus the as-accepted sets used, sorted,
  and it goes into the digest basis.
- `backend/assetops_backend/mini_depth/projection.py`: the revision and `basis.binding_set_revision_ids` use that lineage.
- `simulator/.../packs/mini_grid.py` `resolve_v6`: the charge request is measured at `@{plant.battery}` (D-W1-11).
- `backend/assetops_backend/runs/profiles.py`: publication v5 sends `pv-inverter-controller/ac-power` every 5 min
  (D-W1-12). v4 is untouched.
- `tools/demo_combined_finish.py`: WK-2 is replaced by WK-2a (S−1) and WK-2b (S) (D-W1-13).
  `tools/demo-combined-evidence.mjs` adds the capture key `kobo-board-S-minus-1`.
- `tools/walk1_4_identity_gate.sh`: fixes the cost-check query. Before, `#-`/`-` precedence made it fail on both builds
  ("operator is not unique"), so phase 1's "identical" was vacuous for that section. The query now also leaves out
  `evidence_ids` and `basis_sha256`, which are run-specific ids.
- Tests:
  - `backend/tests/test_walk1_4_mini_binding_lineage.py` (new): split set selected plus lineage of both sets; other asset
    skipped; old binding not in force skipped; Postgres `read_hour_rows` returns the binding of a superseded set.
  - `host/tests/test_mini_grid_v6.py`: `@battery`, plus a new check that v5 differs from v4 only in the PV output
    cadence.
- `.agent/mock-departure-register.md`: R681-R684.

## Acceptance (Addendum 5)

| Item | Status | Evidence |
| --- | --- | --- |
| D-W1-10 own as-accepted binding, four conditions, lineage | met | New tests pass. Non-vacuous: with the rule reverted to `by_id` only, the split-set test fails. With the pinned-set condition removed, the other-asset test fails. Both reverted with `git checkout`. In the build, 7 of 10 noon renewable revisions and 66/165 fuel, 66/165 service and 70/170 backup revisions list two sets. |
| `test_w402_*` and mini projection regression unchanged | met | all `test_w402_*` files unmodified: 173 passed (see Checks) |
| D-W1-11 `@{plant.battery}`, test updated | met | `test_mini_grid_v6.py` 4 passed; the non-empty positive-step guard is kept |
| D-W1-12 PV output every 5 min in v5 only | met | new test: v4 ac-power is 15 min, v5 is 5 min, and that is the only difference |
| D-W1-13 WK-2a/WK-2b and capture key | met | finish 21/21 (below) |
| Identity gate rerun | met: IDENTICAL | table below |

## Identity gate: polish (`assetops_polish_full_test`, S=10-30, read-only) vs walk1e (`assetops_walk1e_test`, S=10-31, code ba62fac10)

Sorted `tools/walk1_4_identity_gate.sh` output, 40 lines each. `diff` is empty.

| Gated value | Polish | Walk1e (after D-W1-10..12) |
| --- | --- | --- |
| Verification verdict | VERIFIED, TARGET_AND_GUARDRAILS_PASS | same |
| Window figures (both windows) | feeder 15 kWh, PV available 48 kWh, unserved critical 0, below reserve 0 s | same |
| Target | baseline 3600 s → later 0 s candidate | same |
| Cost check | MODELLED_NO_IMPROVEMENT, change_per_demand_kwh 0/0, intervention cost 0 USD | same |
| Dispatch S−28,−21,−3,−1 | NECESSARY 455 min | same |
| Dispatch S−14,−7,S | CANDIDATE_AVOIDABLE 200 avoidable / 30 unclear | same |
| Dispatch S+1 | COMPLETE | same |
| Consequences S−14, S−7, S | POTENTIAL_FUEL_COST PRICED 0.00 USD (×2 each) | same |
| Finish | 17/17 CO plus WK | 21/21 (17 CO/SP plus WK-1, WK-2a, WK-2b, WK-3) |

The fallback (trial runs on v5/publication v4) was not needed.

## Spare-solar results (noon hour, Africa/Addis_Ababa; actual values, nothing tuned)

| Day | Date | Decision | Used kW | Capability kW | Headroom kW | Constraints | Sets in lineage |
| --- | --- | --- | ---: | --- | --- | --- | ---: |
| S−28 | 10-03 | EXCLUDED | 42 | 3–9 | 0 | HEADROOM_NON_POSITIVE, CHARGE_OBLIGATION_ACTIVE | 2 |
| S−21 | 10-10 | EXCLUDED | 42 | 3–9 | 0 | same | 2 |
| S−14 | 10-17 | **ELIGIBLE** | 15 | 45–51 | 25–31 | none | 2 |
| S−7 | 10-24 | **ELIGIBLE** | 15 | 45–51 | 25–31 | none | 2 |
| S−4 | 10-27 | LIMITED | n/a | n/a | n/a | no readings: not a story day | 1 |
| S−3 | 10-28 | EXCLUDED | 42 | 3–9 | 0 | HEADROOM_NON_POSITIVE, CHARGE_OBLIGATION_ACTIVE | 2 |
| S−2 | 10-29 | LIMITED | n/a | n/a | n/a | no readings: not a story day | 1 |
| S−1 | 10-30 | EXCLUDED | 42 | 3–9 | 0 | HEADROOM_NON_POSITIVE, CHARGE_OBLIGATION_ACTIVE | 2 |
| S | 10-31 | **ELIGIBLE** | 15 | 45–51 | 25–31 | none | 2 |
| S+1 | 11-01 | **ELIGIBLE** | 15 | 45–51 | 25–31 | none | 1 |

On every story day coverage is 3600/3600 s with source_count 5. The result matches Addendum 5's forecast: spare solar
on S−14, S−7, S and S+1, and none on the cloudy days.

## Finish (`var/polish_walk1e/check.json`): 21 pass, 0 fail, 0 skipped

- WK-2a (S−1): headline "estimated productive-use sales", 42.08 USD (low = high), sales line "168.3 kWh used by Grain
  mill in 8 measured hours", price "Declared at 0.25 USD per kWh".
- WK-2b (S): no money; headline "25–31 kW of daytime solar unused"; sales line "0 kWh used by Grain mill in 8 measured
  hours"; state OPPORTUNITY (superseded by Fix round 1: after merging WALK1-3b the state is the MG-1 verdict).

## Kobo contributor texts the depth domains now feed (walk1e build, S−14..S+1)

There is no before baseline with the current code. Polish is at migration 0039 and predates WALK1-3, and phase 1's
build was overwritten. Before WALK1-4, Kobo had no roles-4 set, so these lines had no depth input.

- Grow "Productive use": "Spare solar on 1 of 1 well-observed day" (S−14, S−7, S, S+1); "Spare solar on 0 of 1
  well-observed day" (S−3, S−1); otherwise `SOLAR_NOT_READ`.
- Protect "Service delivery": "Delivered power measured; demand not measured" on story days; otherwise "Not available
  yet · delivered power not read for this hour".
- Protect "Backup readiness": "No backup event in this window" (honest: no outage in the story).
- Optimize "Fuel": "No complete fuel balance yet" stays, because Kobo has no fuel-level reading.

## Register rows

R681 (D4) headline from the measured headroom, 25–31 kW against the mock's 18–20. R682 (D5) "Spare solar on N of M
well-observed day" over the board day only, open until WALK1-5. R683 (D2) the headline follows the day: sales on S−1,
spare solar on S. R684 (D2) "Delivered power measured; demand not measured" (mock "Delivered load measured; demand not").

## Checks

- Prepare: `prep.py` (scratchpad wrapper; DB_RE widened to `assetops_walk1e_test` only) `--db assetops_walk1e_test
  --work var/polish_walk1e prepare`, code ba62fac10. Prepared in 1305.5 s (cap 3120); 510 mini jobs; EXIT 0.
- Backend scoped (`tools/run-host-tests.ps1`, base `assetops_test`): all `test_w402_*.py` plus
  `test_walk1_4_mini_binding_lineage.py`, `test_s2_registered_resolution.py`, `test_s2_publication_lab_api.py` and
  `test_demo_combined_finish_co1.py` (21 files): **173 passed**, 992 s.
- Host (`run-host-tests.ps1`): `test_mini_grid_v6.py`, `test_t027_commit_ingestion.py`, `test_t028_dispatch_finding.py`
  and `test_s6_verification_replay.py`: **33 passed**, 574 s.
- `tools/check-all.ps1 -Python <plan2 venv>`: **All 12 guards passed**. `frontend/node_modules` is a junction to
  plan2's (untracked).
- Non-vacuous proofs of the new D-W1-10 tests, recorded under Acceptance.

## Known deviations

- None against Addendum 5.
- The gate script fix changes the gate's own query. It does not change gated data, and the polish side was rerun with
  the fixed query.

## Residual risk

- Boards go UNKNOWN (MG-1 `PRODUCER_NOT_SETTLED`) about 5 minutes after the last scheduler tick: the schedule
  heartbeat is stale after 300 s and the Site visit after 900 s (`scheduling/health.py:47-49`), which makes the
  overview not CURRENT (`scheduling/upstream.py:179-182`, `site_outcomes/mini.py:382-388`). Not caused by this slice.
  `serve` ticks every 120 s and keeps boards fresh; G2 captures and finish reruns must run under `serve` or right
  after a tick. The finish already asserts overview CURRENT (`demo_combined_finish.py:186`).
- The full backend suite (full tier) has not run here. It is held for the coordinator's quiet-machine run.

## User-review focus

None for this slice. G2: the S board's spare-solar headline and the S−1 capture (`kobo-board-S-minus-1`).

## Fix round 1

- M1: merged main 635654bf0. Conflicts resolved by keeping both sides: `tools/demo_combined_finish.py` (WK-1, WK-2a,
  WK-2b, WK-3, WK-4 all present), the register (R681-R684 and R690-R693), `.ai/CODE_STATE.md`.
  WK-2b updated for outcome-status/3: S has no money; headline matches "N-M kW of daytime solar unused" (expect
  25-31); sales line starts "0 kWh used by Grain mill"; state in ON_TRACK/WATCH/UNKNOWN (never OPPORTUNITY) with
  `potential` set. It agrees with WK-4 (same board, same row). No prepare was run: the coordinator's G2 integrated
  prepare is the end-to-end proof (finish expected 22+, identity gate rerun); S and S-1 Grow rows are recorded there.
- L1: residual-risk text corrected here and in CODE_STATE (5 min staleness, serve keeps fresh; cwd note removed).
  No tool change (finish already refuses on a non-CURRENT overview); thresholds untouched.
- L2: `test_pinned_binding_starting_after_the_reading_is_skipped` added. With the `_in_force(p, r[3])` term removed
  from `inputs.py` the test fails; restored, it passes.
- L3: `inputs.py` doc comment corrected. L4: R684 now cites `v70/index.html:334`.
