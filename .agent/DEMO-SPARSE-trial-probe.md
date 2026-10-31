# DEMO-SPARSE U1 probe: kind compatibility, episode edges, trial hour, back-dating

Build sheet `AssetOpsV1-plan2/.agent/build-sheet-DEMO-SPARSE.md` §3 U1. Choice rules fixed before measuring (sheet U1;
no saving is a selection input). Branch `task/DEMO-A-combined-dataset`, trees from `git archive HEAD` at `967e02200`
(P1) / `099027249` (P4 re-timed, P3); DB now 2026-10-31, S = 2026-10-29. Scratch probe scripts (not committed): a
driver making the tree + `assetops_demo3_probe<k>_test`, and a child that imports Kobo, configures, publishes price v1,
then per candidate drafts (`RunSetupService`, the `rp._draft` body without its READY assert), publishes through a real
gateway, accepts (S2), assesses (S3) and matches (S4) at received + 5 min, and reads `assessment_revision` /
`finding_revision` for the day. Every candidate: mini-grid v5, registered-kobo-publication v4, seed `20260929`,
interval D 03:00-11:00, received D 12:00, `foundation_known_at` D-1d 12:00, epoch `day-<n>`.

## P1 kinds (all rows)

| Kind | Candidate | Day | Draft | Dispatch interval (first_on-last_on) | Avoidable (candidate) / necessary / indeterminate min | Binding constraints | Finding (episode UTC) | Matches meaning |
|---|---|---|---|---|---|---|---|---|
| normal | `kobo-s3-dispatch-necessary-run` v1 | 10-14 | READY | 03:25-11:00 NECESSARY | 0 / 455 / 0 | AT/NEAR_RESERVE from 03:25 | none | **yes (taken)** |
| normal | `kobo-mini-grid-stop-60` v1 | 10-15 | READY | 03:45-07:10 CANDIDATE_AVOIDABLE | 125 / 80 / 0 | AT/NEAR_RESERVE from 03:45 | 05:05-07:10 (125 min) | no (Finding) |
| normal | `kobo-mini-grid-evening` v1 | 10-16 | READY | 06:20-11:00 NECESSARY | 0 / 280 / 0 | AT/NEAR_RESERVE from 06:20 | none | yes (not needed: first candidate matched) |
| overcast | `kobo-daytime-overcast` v2 | 10-17 | **REFUSED** `RunSetupRefused`: "Entry irradiance-5 is placed at 480 minutes and the interval covers 480 ... Choose an interval that covers the whole scenario." | - | - | - | - | no |
| overcast | `kobo-s3-dispatch-necessary-run` v1 (alternative) | 10-14 (row 1) | READY | 03:25-11:00 NECESSARY | 0 / 455 / 0 | AT/NEAR_RESERVE | none | **yes (taken)**: generator ran 455 min, no Finding |
| overuse | `kobo-mini-grid-reserve-trial` v1 | 10-18 | READY | 04:05-07:55 CANDIDATE_AVOIDABLE | 200 / 0 / 30 | none | 04:35-07:55 (200 min) | **yes (taken)** |
| overuse | `kobo-mini-grid-prolonged` v1 | 10-19 | READY | 03:45-09:15 CANDIDATE_AVOIDABLE | 250 / 80 / 0 | AT/NEAR_RESERVE from 03:45 | 05:05-09:15 (250 min) | yes (not needed) |
| degraded | `kobo-mini-grid-degraded-evidence` v1 | 10-20 | **REFUSED** `RunSetupRefused`: "holds battery-pcs-controller/state-of-charge for 10 minutes in soc-publication-delay, and that path publishes every 5 minutes under registered-kobo-publication version 4 ... Declare a hold no longer than the cadence." | - | - | - | - | no |
| degraded | alternative: first half of the sealed batches only (gateway outage) | - | built in U4 (`add-day` only; no prepared Kobo degraded day) | | | | | taken |

Consequence: `normal` and `overcast` resolve to the same registered scenario (its own text: "An overcast morning with
heavy demand"); S-28 and S-21 carry the same run on two days. No beat is dropped (R617 not added for P1).
The overcast scenario's refusal is the sheet's fixed 8-hour interval; a longer interval was not tried (the sheet
allows only the listed alternative).

### P1 re-run: overcast on the longer interval (SCN sheet "Overcast", 2026-10-31)

Day-list change only (`build-sheet-SCN-kobo-reserve.md` Consumption): `kobo-daytime-overcast` v2, interval D 03:00-15:00
(720 min), received D 16:00, mini-grid v5, publication v4, scenario file untouched. Run through the real child:
`prepare --sites kobo --no-finish --days <scratch copy of the day list with only this overcast row at S-21d plus the
trial pair>` on `assetops_demo3_probe5_test`, tree `git archive` of `c81b062d8`, DB now 2026-10-31, day 2026-10-08.

| Kind | Candidate | Day | Draft | Dispatch | Finding | Matches meaning |
|---|---|---|---|---|---|---|
| overcast | `kobo-daytime-overcast` v2, D 03:00-15:00 | 10-08 | **BLOCKED** `INITIAL_VALUE_NOT_RESOLVED` x2: "Model profile mini-grid version 5 needs fuel-tank-volume@fuel-tank initialized at run start, and this scenario states no value for it ..." and the same for `generator-state@generator` | - | - | no |

The 720-minute interval cleared the earlier interval refusal; the scenario states no run-start value for the fuel
tank or the generator, which mini-grid v5 requires. Not READY, so by the SCN rule overcast keeps the already-taken
`kobo-s3-dispatch-necessary-run` v1 (no further fallback); the day list is unchanged.

## P2 episode edges

Every Finding episode in P1 lies inside [00:20, 23:40] UTC of its day: 05:05-07:10, 04:35-07:55 (the
reserve-trial / F-104 shape), 05:05-09:15. **Pass**; F-104's shape (04:35-07:55) passes.

## P4 back-dating

- Import at S-29 10:00 (2026-09-30T10:00Z) and convert at S-29 11:00: **accepted** (no refusal).
- Unmodified `pub.configure` (knowledge clock 2026-10-07 11:40, fixture dates 10-01 / 10-02 / 10-12), S-28 run
  (`kobo-s3-dispatch-necessary-run`, 2026-10-01): **draft BLOCKED** `INITIAL_VALUE_NOT_RESOLVED` for
  `generator-rated-power`, `generator-start-soc-threshold`, `generator-stop-soc-threshold` ("the foundation of site
  KOBO-001 declares no generator-rated-power"): the Foundation known at S-29 12:00 has no generator values.
- Re-timed configuration (Q1 ruling, `configure_at`: properties + roles-2 effective 09-30 11:10, roles-3 11:20,
  recorded 11:30), same S-28 run: **READY**, delivered, NECESSARY 03:25-11:00, 0 / 455 / 0 min, no Finding -
  identical to P1 row 1 on 10-14. Price v1 recorded 2026-09-30 12:00 through the A0 seam: accepted.
- Stop rule does not fire (the refusal is the fixed-date configuration that the Q1 ruling replaces).

## P3 trial hour

| Candidate | Lever evidence (generator start, binding constraint) | F-104 on S | Verification | Cost check | Nominal / upper USD |
|---|---|---|---|---|---|
| (a) window 06:00, `kobo-mini-grid-reserve-trial` (DEMO-A U3 build `dd08df077`, S = 10-29; not rerun) | start 04:05; no segment bound by `BATTERY_AT_RESERVE`/`NEAR_RESERVE` (P1 row 10-18: binding constraints `[]`) | yes (episode 04:35-07:55) | VERIFIED `TARGET_AND_GUARDRAILS_PASS` | `MODELLED_NO_IMPROVEMENT` | 0 / 0 |
| (b) earliest whole hour in [03:00, 10:00] with a reserve-bound generator start in the baseline run | **none**: the reserve-trial baseline has no reserve-bound segment at any time (P1 10-18; same seed, profiles and 30 % reserve as the trial baseline; forcings are run-offset based) | (yes) | not run: no hour qualifies | - | - |
| (c) `kobo-mini-grid-evening` both runs, window at its first reserve-bound hour = **06:00** (P1 10-16: first reserve-bound segment 06:20, `BATTERY_NEAR_RESERVE`) | start 06:20 `BATTERY_NEAR_RESERVE` (chain DB `assetops_demo3_probe3_test`, S = 10-29: same) | **no**: dispatch on S is NECESSARY 06:20-11:00, 0 / 280 / 0 min, no Finding; the chain stops at the Finding lookup (`KeyError '2026-10-29'`, `h.findings()`) | not reached | - | - |

**Choice (rule fixed before measuring; savings not an input):** (b) shows no lever; (c) shows the lever but loses
F-104 on S. Neither satisfies "shows the lever, keeps F-104 on S and VERIFIES", so **(a): window 06:00, scenario
`kobo-mini-grid-reserve-trial`**. Its result is shown as calculated: `MODELLED_NO_IMPROVEMENT`, 0 USD ("no modelled
improvement"). `trial.window_hour` stays `06:00`; no `trial.scenario_id`. The hour does not change and no beat is
dropped, so R617 is not added (sheet §7).

Stop rules: P2 passes for F-104; P4 does not refuse under the ruled configuration; the tick rule is checked on the
first full `prepare` (U3 self-check).

### P3 candidate (d): `kobo-mini-grid-reserve-matters` v1 at 04:00 UTC (SCN U3, 2026-10-31)

Run through the real Kobo child: `demo_combined.py --db assetops_demo3_probe4_test --work var/demo3_probe4 prepare
--sites kobo --no-finish --days <scratch copy of demo-story-days-v1.json: Kobo days = the trial pair only,
trial.scenario_id = kobo-mini-grid-reserve-matters v1, window_hour 04:00>`, branch head `cc39a96e2` (main `0a2075037`
merged), DB now 2026-10-31, S = 2026-10-29. 97 s, exit 1 at the plan freeze. The scenario was chosen before running
by SCN Addendum 1 (H = 04:00-05:00 UTC); no value was changed after the run.

| Column | Result |
|---|---|
| Lever evidence (baseline, S) | generator first ON 03:05 (`BATTERY_NEAR_RESERVE`), NECESSARY `BATTERY_AT_RESERVE` from 04:50; binding constraints `[BATTERY_AT_RESERVE, BATTERY_NEAR_RESERVE]`; portions 235 candidate / 240 necessary / 0 indeterminate min. SOC at start 34 % and 2.95 kWh in H are the SCN kernel values (`.agent/SCN-packet.md`), not re-read from the chain DB |
| Finding on S | yes: `15ff2315-72aa-448e-92ca-c032fe264236` SUPPORTED CANDIDATE_AVOIDABLE, episode 07:05-11:00 (235 min); accepted as ACT through the real Action API, applied (reserve 25 %) |
| Verification | **not reached**: plan freeze refused 409 `VERIFICATION_BASELINE_NOT_SELECTED` "Every UTC day covering the baseline needs a final S3 dispatch selection." days `["2026-10-28"]`. A window starting before 06:00 also needs the previous UTC day's selection (`actions/verification.py:86-93` `required_days`, the S3 6 h read bracket); S-1 has no run in the story calendar (nor in this probe) |
| Cost check, USD | not reached (no plan, no outcome) |
| Safeguard checks | not reached |

**Choice (rule fixed before measuring; savings not an input):** (d) shows the lever and has a Finding on S but does
not VERIFY, so it is not taken. The trial stays (a): window 06:00, `kobo-mini-grid-reserve-trial`,
`MODELLED_NO_IMPROVEMENT` 0 USD, shown as "no modelled improvement". `demo-story-days-v1.json` is unchanged. R617 added.
For the Architect, information only: a 04:00 trial would need an assessed Kobo run on S-1 (and S, for the later
window) in the day list; no such day was added here, since the day list is the Architect's.
Scratch DB `assetops_demo3_probe4_test` and `var/demo3_probe4` dropped after recording.
