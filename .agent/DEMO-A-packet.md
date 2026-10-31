# DEMO-A review packet (combined three-Site dataset on the DEMO-SPARSE calendar)

Task `tasks/DEMO-A-combined-dataset.md` · branch `task/DEMO-A-combined-dataset` · worktree `AssetOpsV1-demo3`.
Contract: `AssetOpsV1-plan2/.agent/build-sheet-DEMO-SPARSE.md` (rev 1 + Addenda 1-3) over `build-sheet-DEMO-COMBINED.md`.
Build history: `.agent/DEMO-A-phase-handoff.md`. Probe: `.agent/DEMO-SPARSE-trial-probe.md`.

## Outcome

`python tools/demo_combined.py --db <db> --work <dir> prepare` builds KOBO-001, COLD-LAB-001 and EV-LAB-001 on one story
clock (this build S = 2026-10-29, DB now 2026-10-31) from `backend/conversions/demo-story-days-v1.json`
(8 Kobo runs + 1 missing day, 3 cold nights, 2 EV Tuesdays; all registered Lab runs), then objectives, the S2 Evidence
comparison, two ticks, the Performance comparison and the self-check (`tools/demo_combined_finish.py`, 17 rows).
**Self-check on the final build: 16 pass, 1 fail (CO-6).** CO-6 fails on a product gap, not on the build (below).

**Kept DB for the reviewer and DEMO-B: `assetops_demo3_full_test` / `var/demo3_full`, built at `20f83276b`**
(code tree copied at HEAD; later commits are `.agent`/`tasks`/`.ai` only). Drop with the tool's `drop`.

## Files materially changed (whole slice)

`tools/demo_combined.py`, `demo_combined_kobo.py`, `demo_combined_cold.py`, `demo_combined_ev.py`,
`demo_combined_finish.py`, `demo_story_days.py`; `backend/conversions/demo-story-days-v1.json`,
`demo-combined-story-v1.json`; `backend/tests/test_demo_story_days.py` (19, fast), `test_demo_combined_postgres.py` (slow,
19 collected); `backend/TESTING.md` (slow-tier list); `.agent/mock-departure-register.md`.

## Self-check table (final build `20f83276b`, read at build time, 12:29 UTC)

| Row | Result | Read |
|---|---|---|
| CO-1 (re-premised, Addendum 3 r2) | pass | Cost NEEDS_ATTENTION with the Finding; `must_not_harm` null; Action not linked on the Cost row; ACT-000001 in Cost `earlier`; R552 open |
| CO-2 | pass | overview CURRENT; index CURRENT |
| CO-3 | pass | MODELLED_NO_IMPROVEMENT; "Modelled change after the trial · not realised savings: no lower cost per kWh ..." |
| CO-5/SP-1 | pass | ON_TRACK (MG-2 OBJECTIVE_MET) |
| CO-5/SP-2 | pass | cold Protect on the S-7 night |
| SP-3 | pass | "Not available yet · 24 of 31 days have no assessed readings", g = 24 |
| SP-4 | pass | PARTIAL; S-10 UNASSESSED; S-3 not a gap; S-14/S-7/S Findings in rows |
| SP-5 | pass | S-21 overcast: generator time, no Finding episode |
| SP-6 | pass | trial (a): window 06:00, MODELLED_NO_IMPROVEMENT 0 / 0 USD |
| CO-6 | **fail** | `('PENDING', 'PARTIAL')`: Portfolio week status PENDING, not UNKNOWN (cause below) |
| CO-6b | pass | day S: status PENDING (recorded), Kobo coverage CURRENT, cold LATEST_EVENT, EV PERIOD |
| CO-7, CO-8, CO-9, CO-11, CO-12 | pass | |
| CO-10 | pass | Kobo PLAN_DUE_SOON; EV CONNECTOR_OUT_OF_SERVICE, PLAN_OVERDUE, CHARGER_FAULT_OVERDUE_INSPECTION |
| SP-7 | build test only (mutates) | not reached this run (fixture stopped, below) |

**CO-6 measured value and cause.** The rest of CO-6 holds (3 Sites, `objective_site_count` 3, cold/EV LATEST_EVENT, Kobo
coverage UNKNOWN by the all-days rule). The overall status is PENDING because the cold money window is withheld
(`estate/financials.py:227`, `_pending_guard` -> `estate/portfolio.py:76`): 8 `cold_consequence_work` rows on COLD-LAB-001
with 0 attempts and 0 `cold_consequence_revision`. FIX-S4-DOMAIN removed the s4 crash (every Site head now IDLE,
`SKIPPED_UNCHANGED_FENCE`, no failure), but the tick's consequence stage runs only the mini `build_recompute_worker`
(`scheduling/stages.py:186-198`); no runtime path runs `ColdConsequenceWorker` (`build_cold_consequence_worker` is called
only by `test_w204_*`). So the fourth implementer's cause ("s4 crash stops the drain") was incomplete. Not fixed here:
it is a product decision (wire a cold drain into the tick, or run the worker as a build step). Row not weakened.

## Probe results (trial)

| Try | Precondition | Lever | Finding on S | Verification | Taken |
|---|---|---|---|---|---|
| (a) `kobo-mini-grid-reserve-trial` 06:00 (U1 P3) | - | - | yes | VERIFIED ACT-000001 | **yes**: MODELLED_NO_IMPROVEMENT, 0 USD |
| (d) `reserve-matters` v1 04:00, try 1 (SCN U3) | S-1 no run | first ON 03:05, AT_RESERVE 04:50 | yes, 07:05-11:00 | freeze 409 `VERIFICATION_BASELINE_NOT_SELECTED` (2026-10-28) | no |
| (d) try 2, normal S-1 (Addendum 3 r3) | S-1 selected (NECESSARY, ON 03:25) | as try 1 | yes | freeze 409 `VERIFICATION_BASELINE_UNSUPPORTED`: 04:00-05:00 INCONCLUSIVE, `OPEN_BOUND` from 03:05 | no |

Try 2 also recorded: origin revision (rev 1 OPENED) != day S's shown revision (rev 2 BASIS_REFRESHED). No further tries.

## Sheet deviations

1. Kobo kinds (U1 P1): overcast uses `kobo-s3-dispatch-necessary-run` (daytime-overcast refused the 8 h interval; the 720-min
   v2 is BLOCKED `INITIAL_VALUE_NOT_RESOLVED`); degraded = first-half delivery (degraded-evidence refused under v4).
2. Trial stays (a) 06:00, 0 USD (R617).
3. EV days on the Tuesday on or before the listed day (ev-charger/1 publishes Tuesdays only): fault 10-27, normal 10-20 (R619);
   Portfolio and `links` read the week S-6d..S+1d (Addendum 1 (a)).
4. EV `fault` kind uses `ev-interrupted` v1, not `ev-fault.yaml` (which faults before any session: no Finding).
5. Calendar gained `S-1d normal` (Addendum 3 r3); SP-3 g = 24.
6. **New this round (`20f83276b`): late Kobo delivery `D+2d 12:30`, not the sheet's `D+2d 12:00`.** With S-1 on the calendar,
   the late S-3 day and S-1 shared 2026-10-28 12:00; `_publish_and_accept` counts acceptance by `received_at`, so the first
   rebuild failed at S-1 with `(1164, 2072, 0, 0, 0)`. `validate` now refuses `DUPLICATE_RECEIVED_AT` (test
   `test_duplicate_received_at`, shown failing with the check disabled, then reverted).
7. CO-1 re-premised until the owner rules on Finding-revision lineage (Addendum 3 r2; R552 open).
8. Cold attestation instant pinned to the day's setup instant (`ShiftedChain.attest` used wall time -> CLOCK_UNATTESTED).

## Register

- R535 **open**: estate exists, CO-6 fails on the cold drain (cause recorded in the row).
- R552 **open**: CO-1 lineage with the owner; on this build ACT-000001 is in Cost `earlier` but not linked/Must-not-harm.
- R569 **resolved** (CO-10 passes). R595 resolved earlier by IDX-GAPS.
- R615, R616, R618, R619 standing. R617 standing, now records both (d) tries.

## Live-demo cautions (runbook)

1. **Staleness after build time is inherent.** The schedule heartbeat threshold is 300 s: 25 min after the build's last tick
   the same DB read 14/17 (CO-2 overview `STALE_PROJECTION` `SCHEDULE_STOPPED`/`SITE_VISIT_STALE`, heartbeat age 1477 s;
   CO-5/SP-1 MG-2 UNKNOWN `PRODUCER_NOT_SETTLED`; CO-6). One `demo_combined.py ... tick` restored 16/17 at once. A demo DB
   read hours later is presentable only after `serve` (ticks every 120 s) or a `tick`; **start `serve` before showing**.
   This is the product telling the truth about a stopped scheduler, not a build defect.
2. `add-day --assess-now`: assessment is Site-wide, so it also assesses earlier pending live days; a pending live day turns
   other one-day windows `STALE_PROJECTION` until assessed. Add live days only with `serve` running, and show the day after
   the next tick.

## Demo-script note

Open the Portfolio on the week (`links` prints it). Lead with each Site's four outcome cells: Kobo's from day S, GreenHarvest's
and Depot's from their latest events. Kobo's weekly evidence reads Unknown because most days that week have no assessed
readings: present it as a pilot ask ("a gateway that reports every day turns this into a weekly verdict"). Click into Kobo
(day S, gap line "Not available yet · 24 of 31 days ..."). Do not lead with the Portfolio on day S (Depot reads Unknown).
Until the cold drain is decided, the Portfolio headline reads "pending", not "unknown": say the cold room's money is still
being worked out, or avoid the headline.

## Checks run

- `test_demo_story_days.py`: 19 passed (at `20f83276b`). check-all 11/11 at `feec73b2f` (merge of main `15eed62c8`) and at `40711db43` (closeout).
- Full prepare `assetops_demo3_full_test` at `feec73b2f`: exit 1 at 678 s (deviation 6). At `20f83276b`: 1105 s (tool wall cap 3120 s; brief cap 49 min):
  kobo 844.5 s (8 runs), cold 59.6 s, ev 66.8 s, setup + finish ~134 s; self-check 16/1.
- Slow build test `backend/tests/test_demo_combined_postgres.py -m slow` at `210db8187` (code = `20f83276b`), fresh DB
  `assetops_demo3_t7dc6be7_test` (dropped by the fixture): 1143 s, JUnit tests 19, failures 0, **errors 19**, skipped 0. The
  module fixture's `prepare` raised `SELF-CHECK FAILED` (its in-process self-check: 16 pass, 1 fail CO-6, read right after the
  build), so every row errored at setup. Same result as the kept build; CO-2/SP-1 pass when read at build time.
- `-Tier all` on the combined tree: not run (merge gate, coordinator's go).

## Residual risk / review focus

- CO-6 and the merge gate need a ruling on the cold consequence drain (product) before the build test can go green.
- The build test fixture aborts on any self-check fail, so rows report as setup errors rather than individually.
- `_fence` revision count spans every domain (FIX-S4-DOMAIN open item): harmless re-plan.

## Final round (2026-10-31, after main `c8702bb2b`)

- **Merge** `44e54dce0` (main `c8702bb2b`: COV-PARTIAL, LINK-LINEAGE, FIX-COLD-DRAIN on top of IDX-GAPS, SCN,
  FIX-S4-DOMAIN, FIX-W301, FIX-W401). Conflicts only in `.ai/ACTIVE_CONTEXT.md`, `.ai/CODE_STATE.md` and the register;
  both sides kept (R613 main's resolved form; R552 this branch's text with main's status).
- **CO-1 restored** (`79dda4ea0`, LINK-LINEAGE §5): `must_not_harm.href` holds ACT-000001's
  `/verification?event_id=`; ACT-000001 on the Cost row; `outside == []`; MG-2 branch recorded and asserted.
- **CO-6 re-derived** (`79dda4ea0`, COV-PARTIAL §6): Kobo week `PARTIAL` with the `days` block (gaps = the computed
  unassessed days, `checked = 7 - g`, `DAYS_CHECKED` text, suffix iff `withheld`); status in {PARTIAL, UNKNOWN} and
  not CURRENT; Kobo's day-S Finding in `rows` unless withheld. CO-6b gains `days.gaps == []`.
- **Kept DB rebuilt**: `assetops_demo3_full_test` / `var/demo3_full`, code `79dda4ea0`, prepare 797.6 s
  (kobo 567.2 s, cold 43.2 s, ev 48.9 s). **Self-check 17 pass, 0 fail, 0 skipped.**
  - CO-1: Cost NEEDS_ATTENTION; MG-2 `OBJECTIVE_MISSED` (branch Needs attention); Must-not-harm href
    `/sites/KOBO-001/actions/<id>/verification?event_id=<id>`; `r552: resolved: refresh lineage`.
  - CO-6: status **PARTIAL**; Kobo PARTIAL/RECENT/COMPLETE/SETTLED, `3 of 7 days checked · 4 days not available yet`,
    gaps 10-23, 10-24, 10-25, 10-27 (`NO_ASSESSED_SELECTION`), not withheld, Finding in rows; cold and EV coverage
    CURRENT/SETTLED (money no longer pending; DB: 8 `cold_consequence_work`, 1 `cold_consequence_revision`).
  - CO-6b: status UNKNOWN; Kobo CURRENT, cold LATEST_EVENT, EV PERIOD (no event on S), as Addendum 2 records.
- **Build-test harness fix** (`362cfe5cf`): the first build-test run (832 s) failed 8 rows that
  the prepare's own self-check passed. Causes: (1) rows read through `lab_app` in the pytest process, whose file stores
  resolve under this worktree's `REPO_ROOT`, not the private tree's (Kobo reads 409 `AWAITING_EVIDENCE_MIGRATION` /
  `PERFORMANCE_CUTOVER_CLOSED`); (2) the fixture called `Demo.prepare()` directly and left `.busy` held, so SP-7's
  `add-day` refused. Fix: rows assert a fresh `finish check` run as a child in the private tree; SP-7 reads through a
  new `finish get` child; the fixture releases `.busy` as `main` does. No assertion was changed.
- **Slow build test** `tools\run-host-tests.ps1 -- backend/tests/test_demo_combined_postgres.py -m slow` at
  `362cfe5cf`, DB `assetops_demo3_t<run>_test` (dropped): 942 s wall, JUnit tests 19,
  failures 1, errors 0, skipped 0. All 17 check rows and `test_self_check_ran_in_prepare` pass.
  **SP-7 fails, not adjusted:** the add-day refusal and the late-day gap-to-assessed parts pass; the rebuild
  comparison fails on EV only. Expected: the same `(site, offset, kind)` per day on a later S. Actual (S 10-29 ->
  10-30): EV `('ev', -9, 'normal')` -> `('ev', -10, 'normal')` and `('ev', -2, 'fault')` -> `('ev', -3, 'fault')`, the
  EV dates staying on Tuesdays 10-20 / 10-27; every Kobo and cold `(offset, kind)` is unchanged. Cause: Addendum 1 (a)
  (EV on the Tuesday on or before the listed day, R619) makes EV offsets depend on S's weekday, which SP-7's
  "every date moved by the rebuild's S" text predates. Needs an Architect ruling (compare EV by listed day, or accept).
- **check-all** at `362cfe5cf`: 11/11 passed.
- **`-Tier all`: not run.** Stopped per the brief on the SP-7 mismatch; it gates on the ruling.
- **Register (not closed here):** R552 would now pass (CO-1 original assertions hold). R535 would now pass (the
  three-domain estate reads with cold/EV money settled and the week PARTIAL, not PENDING). Rows left as they are.
