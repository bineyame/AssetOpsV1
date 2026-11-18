# DD-1a2 pre-flight: questions for the lane-2 Architect

Builder, 2026-11-06, branch `task/DD-1a2-b22-day-list` at `9b1c53ae3`. No repo code changed. **Stopped: Q1 and Q2 are stop-level; Q3-Q8 change the list.**

**Evidence used.** Sheet rulings and code at the cited lines. The chain measurements are from a scratch script, **in memory, on the template Site** (`probe_kobo_nights.template_draft`, mini-grid v6, 5 min). They are not yet registered-Site results; R3 found the two equal for probes S and O, and step G0 below re-measures. Findings and grades were not measured.

**Not read.** `.agent/review-DD-1a1.md` is not on this branch; it exists only in the `AssetOpsV1-plan2` checkout, which my brief says not to touch. I worked from the brief's restatement of its lines 25-29, 109-110, 119. If those lines hold more than the four required items, tell me.

## Measured: steady 00:00-24:00 days, chained (R15)

| Day shape (template Site) | Start | 24:00 end | Generator (local) | Fuel/day | SoC 06 / 18 / 20 |
|---|---|---|---|---|---|
| Steady, `kobo-daytime` windows + night windows, 8 days | 48.42 %, 300 L, STOPPED | **48.42 %, STOPPED, every day** | **05:10-12:15 every day** | **22.35 L** | 31.6 / 89.5 / 69.5 |
| Pre-change candidate (Q2 option A), 3 days | 48.42 %, 300 L, STOPPED | 45.26 %, STOPPED | 05:10-12:15, then 04:00-12:15 | 7.1, then 9.0 L | 30.0 / 86.3 / 66.3 |
| `kobo-daytime-larger-mill` windows, 3 days | 48.42 %, 300 L, STOPPED | 30.0 %, **RUNNING** | 05:10-24:00, then 00:05-24:00 | 46-57 L | fails the join rule |

**Probe cost.** 1.0-1.5 s per day in memory (measured). Expect about 1 to 2 minutes for a whole chain on the registered Site, most of it the one fixture build (estimate, from `test_dd1a1_registered_kobo.py`'s module fixture; not timed).

Three facts follow. The join rule passes on steady days: SoC reaches a fixed point, because the 90 % stop resets it. R13's 0 starts from 06:00 to 20:00 also passes. But each next file differs, because fuel falls 22.35 L a day.

## Q1 (stop-level). Steady days run the generator 7 hours and burn 22 L, not what the owner was told

R3's owner question said the generator "delivers almost nothing before sunrise", 0 L, "changes no story figure" (`owner-kobo-nights-2026-11-06.md`). That held because the 06:00 story reset ended the run. R15's 00-24 run has no reset, so the 90 % stop policy holds the generator on until 12:15. So every steady day gets a 7 h run overlapping the sun, and possibly a CANDIDATE_AVOIDABLE interval and Finding (`analytics/dispatch.py:40`, unmeasured). That would break R13's "MG-2 counts, Findings and money equal" and muddy ACT-K1's problem with about 13 extra days.

- **(a) Keep R15.** Physically continuous and tells a true story, but costs about 22 L a day and may add a Finding a day. Needs one file per chain position, because fuel differs (up to 6 on this list), an early-night file per predecessor fuel for a mill day, and add-day files for repeats.
- **(b) Steady day shaped like the mill day:** `kobo-night-early` + a 06:00 declared start + rest-of-day. All files are constant (300 L), no morning run, 0 L, matches what the owner approved. But the battery chart steps about +24 pp and the generator stops by itself at 06:00 on every steady day. R14 bound that seam on steady days, and R15 chose 00-24 to avoid it, so this reverses R15 for steady days. Three runs a day, the 123 s/day DD-0c assumed.

**Recommendation.** Run gate G1 first (below): one registered steady 00-24 day, reporting intervals, classes, Findings and money, about 5 minutes. No Finding and no shown money change: (a). Otherwise (b), with the owner told in plain words, since either answer differs from what they approved. Please rule on both branches now so I do not come back.

## Q2 (stop-level). MILL-3 cannot pass as specified: steady days already run the mill at midday

`kobo-steady-day` and `kobo-mill-midday` have **identical** mill windows, both verbatim `kobo-daytime` v2 (0, 15, 18, 10, 12, 0 kW from 06:00; 110 kWh by the windows, not measured through the product). R12 assumed steady days run "the pre-change mill window"; there is none. So with steady baseline and mill later days, `verification_families.assess` (`:277`) gets equal means, and `10*x >= 11*x` is false: **INEFFECTIVE TARGET_MISS on a client screen**, by construction. Placement cannot fix it, and R12 says never to tune.

- **A. A derived pre-change steady profile for days before the Action.** Mill per window from existing parents: 0 at 06-14 (`kobo-mini-grid-reserve-trial`), then 18 at 14-16 and 3 at 16-18 (`kobo-mini-grid-evening`). Days after the Action run the `kobo-daytime` windows. By windows: 42 → 110 kWh, +162 %. Passes the join rule (table). Caveats: the composition is my choice of parents, so the margin is not a neutral measurement (OD-P13 "no value chosen to reach a result"), total milled energy is not conserved, and R2's "diffs against its parent" no longer holds for that file. +0.25 est.
- **B. No verdict.** Same profile everywhere, E placed late so later days are not yet there: the screen shows "Not judged yet". Loses "Target met" (CH-9b). But it means choosing the placement to avoid a verdict, close to what R12 forbids.
- **C. `kobo-daytime-larger-mill` as later days:** rejected by data, RUNNING at 24:00 (table).
- **D. Accept "Target missed" as shown:** a false statement about a demo Action; not recommended.

**Recommendation: A, as an owner question,** since R12 calls this owner-visible. Plain wording: "Before the mill Action, the example days need the mill running in a different pattern, or the check can't show any change. We'd use the late-afternoon pattern from another example day, so the check would read about 160 % up. OK, or show 'not judged yet' instead?"

## Q3. Placement of `mill-midday` (depends on Q2)

The rule (`verification_families.py:13-16`): the effective day is in neither window; baseline is the last 3 COMPLETE days; later is the first 3 COMPLETE, within 14 days, skipping non-COMPLETE days. Fixed days in the window: S-14, S-7, S-3, S-1, S+0, S+1 story-only; S-10 `missing`.

**Recommendation: E = S-9.** Baseline S-13, S-12, S-11; later S-8, S-6, S-5 (S-7 skipped by grade). It sits inside the B-16 fallback, so it survives Q6. Other days: S-20 to S-15 pre-change steady; S-4 and S-2 see Q4.

## Q4. `LATE_IN_STREAM` refuses the list

`demo_story_days.py:296` (R8): a `late` day may not join a multi-day stream. S-3 is `late`, so steady days on S-4 or S-2 raise it, and R8 says stop. **Recommendation: leave S-4 and S-2 unbuilt** (they read NO_DATA, nothing else moves), and report it. The later days are untouched. Moving S-3 is not an option. Consequence: the plan's "story week reads 7 of 7" (`client-demo-plan.html:781`) is already false under R16; the row needs correcting.

## Q5. Cold has no steady day left

R14 withdrew Cold tiling and "a Cold steady day is a story-only day or left out". `cold-steady` no longer exists, and DD0c-R Q3 dropped 24 h. A `cold-normal` day repeats its excursion Finding (R14: every Cold day carries the failure or excursion), and any built S-2 hits `BUILT_DAY_AFTER_DEGRADED` (`:299`, Cold S-3 is `degraded`).

**Recommendation: left out.** Cold stays v1's 3 days. It saves about 19 x 115 s = 36 min on E3, and DD-1b2's "Cold 3 days with one 24 h steady" becomes "3 story days". The plan's R1 row needs amending. Alternative, if the board must not look sparse: re-derive a 65-min `cold-steady` for story-only days, which also needs a gap around S-3.

## Q6. Reconciliation: 16 days against `[S-20d, S+1d]`: settled, no ruling needed unless you disagree

`owner-build-time-2026-11-06.md` is conditional: "keep B-22; if the DD-1b2 rehearsal measures the whole prepare over 3 h, fall back to B-16." The plan rows (`:781-787`) agree. I build B-22; Q3 keeps the Grow block inside `[S-14d, S+1d]` so the fallback only drops days. S-28 and S-21 stay as story days outside the window (R1, R2).

## Q7. The after-overcast night pair (R2, +0.25) has no legal place

Probe O is RUNNING at 20:00, and O-late and O-early are RUNNING at 24:00 and 06:00 (`kobo-night-handover-v1.json`); the overcast day is N-chain and R16 story-only. So the pair breaks R15's STOPPED bound at each cut. **Recommendation: withdraw it,** as R2's own fallback ("presents less") allows: no night generator cost is shown. DD-1a2 2.0 → 1.75 before any Q2 addition.

**HELD files, under Q7 and Q1:**
- `kobo-night-*-after-overcast`, `kobo-steady-afternoon`, `kobo-steady-dusk`, `kobo-night-late`: **remove**; no design uses them. `rest_document` builds its night from the `NIGHTS` table, not the file. Tests to edit: `test_dd1a1_registered_kobo.py:40-44`, `test_dd1a1_stream_probe.py:88`.
- `kobo-steady-day`: remove under Q1 (a); under Q1 (b) re-probe and un-hold.

## Q8. Rules I need stated

1. **Steady day after a story-only or missing day.** R15 says "the previous day's measured 24:00 state", but such a day has none: its data stops at 14:00. **Recommendation:** a fresh declared start (48/300/STOPPED, the Probe S state `kobo-night-early` already carries), reported, with no bound. There is a real data gap there.
2. **What "story-only" means for a steady day whose 24:00 is RUNNING (R16).** It has no story. **Recommendation:** the 06-18 run alone, partly checked. Not expected on the list by the table; relevant to add-day (item 3).
3. **ST-7 add-day after S+1.** The Foundation then holds the 25 % reserve, and no probe exists for a steady day on it; the kind carries the post-Action profile with a fresh start. **Recommendation:** gate it on an R25 registered probe. If it fails, keep the day addable but say partly checked by item 2. Under Q1 (b) add-day must also expand three runs (`plan_add_day` now takes one).
4. **Degraded guard.** Today's `DEGRADED_DAY_HELD` (`:163`) fires only if the kind has a `complement`, so on this list it is vacuous. R10 says "no `degraded` day". **Recommendation:** refuse any Kobo `degraded` entry and add-day regardless of complement, only `DEGRADED_PROBE` passing; update `test_demo_story_days.py:461-475`. Cold's S-3 `degraded` (`cold-missing-probe`, not an outage cut) stays allowed. Confirm that reading.
5. **MILL-3 dry run without a prepare.** It needs grades and `productive_kwh`, which need a build, and my brief bars demo prepare. **Recommendation:** the Kobo child only, on my own `*_test` DB, for S-14 to S-5 (10 days, about 20 min plus drain), then `assess()` called directly with E, because the story-time Action is DD-1b. It includes S-14, so it also shows whether its Findings survive a next-day steady run in the same UTC window (the R14 mixed-run question, on Kobo). Confirm this is allowed.

## Reconciled, nothing to rule

- **R4 vs mill placement:** v2 already points the kind at derived `kobo-mill-midday` (READY on v6, `test_dd1a1_registered_kobo.py:114`). Its joins are STOPPED at 18:00 and 24:00.
- **Guard extension (brief).** `check_full_day` (`:130`) is keyed by story scenario. I add list-level checks in `resolve`: every complement member and every steady file must have a `full_days` entry with STOPPED joins, and its declared start must match the previous built day's recorded 24:00 within R15's bound (0.5 pp, 0.5 L), unless Q8.1 applies. Proven by mutation.
- **EV:** add `S-14d normal`. `weekday_offset` always lands it in `[S-20d, S-14d]`, giving 3 Tuesdays. A 4th (S+1 when S is a Monday) is reported, never moved. The EV kinds stay 08:00-09:00 inside R1's 08-16 calendar.
- **S-10 `missing`:** the existing v1 entry stays. BL-10 backlogged only new ones and their checks.
- **Default:** v3 becomes `DEFAULT_FILE`, as `demo_story_days.py:25` plans. FILL-1's five refusals exist (`plan_add_day:354-391`); I add the steady kinds and a test that `DAY_HAS_EVIDENCE` fires before provisioning (Q4 at sheet `:154`).

## Build gates once ruled (own `*_test` DBs, one heavy job at a time)

- **G0:** the chain on the registered Site, recorded in `full_days`.
- **G1:** one steady day through `add-day` (L2) with Findings, intervals and money. This is the Q1 decision.
- **G2:** the MILL-3 dry run (Q8.5). Fewer than 3 COMPLETE days on a side, or not VERIFIED, is an R12 stop, reported and never tuned.

## Sizes

Base 2.0. Q7 −0.25. Q2 A +0.25 (not added by me: Architect to rule, demo-critical if "Target met" stays). Q1 (b) adds no files but moves add-day to three runs, est. +0.25.
