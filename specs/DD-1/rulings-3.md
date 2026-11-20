## DD1a2-R2: G1 failed on "0 L" on the `steady-before` night: accept the measured litre, and say so (Architect, Claude, 2026-11-07)

- Input: `.agent/DD-1a2-handoff.md` at `215984add`, `.agent/DD-1a2-g1.json`, `.agent/DD-1a2-g1-control.json`, `.agent/owner-dd1a2-answers-2026-11-07.md`. The owner chose the 06:00 start and to write the "before".

### The report, checked

| Claim | Result |
|---|---|
| 0.973 L, generator 04:00-06:00 | **Confirmed**, probe `B-early` in `kobo-night-handover-v1.json:546-571`: start 45.26 %, end 299.03 L, 30.0 %, RUNNING. |
| G0 states (89.47 / 48.42, 86.32 / 45.26) | **Confirmed** in the same file. |
| 3 NECESSARY intervals, 0 Findings; control finds 2 | **Confirmed** in the two JSON files. |
| Money 0 rows on both | **Confirmed.** Money is unmeasured on this path. |
| 3.167 kWh "in evidence" | **Not in `DD-1a2-g1.json`.** That file predates the builder's fuel-field change. It has no `generator_kwh`, and its `fuel_used_l` reads 0 on every day, including S-12, which is the vacuous figure the builder later removed. **That file must not be cited for litres.** The 3.167 is unverified here, though it is consistent with 0.973 L. Regenerate it (below). |
| 7 days, about 6.8 L | The 7 days match the v3 table. 6.8 L is 7 × one probe, not measured as a sum. |

### 1. Option: **(a), keep the 7 nights as measured.** G1 stays recorded as a fail on that line, accepted by this ruling.

- **This does not redefine the gate.** The packet records: "G1: FAIL on 0 L for `steady-before`; accepted, DD1a2-R2". DD1a2-R said a G1 fail would likely mean the days cannot be full. That prediction does not apply: every join is STOPPED, the interval is NECESSARY, and there are 0 Findings. The only thing false is the "0 L" sentence, so the sentence changes, not the day.
- **(b) is rejected, and the bound stays at 0.5 pp.** A 48 % start after a day measured ending at 45.26 % is a declared value, picked because it removes the fuel. That is exactly what R2 forbids ("measured handover, never chosen"), and the bound exists to catch it. I see no honest reading of a 2.74 pp step here. `check_full_day_chains` is unchanged.
- **Branch B is rejected.** It is the route for days that cannot be full, and these can. The owner chose "write a 'before'".
- **The frozen pattern stays frozen.** The cause is the authored afternoon load, and it is not revisited now that a result is known.
- **Regenerate G1 (required, with handoff step 1).** Rerun through `host/tests/test_dd1a2_registered_kobo.py` with the current report and overwrite `.agent/DD-1a2-g1.json`. It must show `generator_kwh` per day and, for the 04:00-06:00 night, clinic and residential delivered equal requested (R3 check 1: nothing unserved; the battery sits at its reserve).
  - **Pass:** NECESSARY, 0 Findings, nothing unserved, litres as the probe. If the litre figure differs, `BEFORE_NIGHT_DISCLOSURE` takes the measured figure and the build continues.
  - **Fail (a Finding, a Candidate or Cannot-determine minute, or any unserved load):** stop and the Architect rules. No value changes.

### What the screen and the demo say

- **Screen: no new copy, and no litre figure is added.** No fuel signal reaches evidence on this Site (the builder's note, consistent with G1's signal list), so nothing shows these litres as a reading. The day's Cost row reads `COST_NO_MONEY`, "No fuel cost estimated for this day", because that row prices only time beyond need, from a Finding. Read from code: `mini.py:477`; confirm the shown text in F-THREADS. The night's source line already says it, through `BEFORE_NIGHT_DISCLOSURE`: "...the generator delivers energy and this night uses about 1 L of fuel."
- **Demo script, if asked:** "On the days before the mill change, the evening ends with the battery a little lower, so the generator comes on from about 4am and uses about a litre. It was needed, so no problem is raised and no extra cost is estimated."
- **Do not say** "the mill change saved a litre a day". The drop from about 1 L to 0 comes from the pattern we authored and the 06:00 start, not from a measured saving. **Do not say** "about 0 litres" of these 7 days.

### 2. Owner: **informed, no question; the build does not wait.**

The owner's choice was between about 0 L and about 22 L, and about 1 L on 7 days does not change which is better. The only other routes are a chosen number or losing "Target met". Line for the coordinator to send, with the right to overrule:

> "A correction to what we told you about normal days on the Kobo example. Most run about 0 litres before dawn, but the 7 days before the mill change use about 1 litre each, because the generator comes on from 4am. It was needed, so no problem is raised and no extra cost is shown, and the night's explanation says so. We kept the measured figure instead of changing the numbers. We also said money stays the same: that isn't proven yet. It gets checked on a test build and again on the final rehearsal, and we'll tell you before the full build if it differs. The new full days do add their own mill sales figures, which is expected. Tell us if you'd like this handled differently."

### 3. Money: proved in two named places, neither left vacuous

- **Why it is expected to hold (read from code, not proof).** A fuel consequence comes only from a Finding's Candidate span (`financials/fuel_cost.py:284-311`, `NO_CANDIDATE_TIME`), so a day with 0 Findings has nothing to price.
- **G2 (`MONEY-A`, DD-1a2).** After each build (`mill3`, `story-only`), run the same worker the prepare's ticks use (`--consequence-items`, `demo_combined.py:66`) until nothing is pending, then report the rows per local day.
  - **Non-vacuity:** the `story-only` control must give rows or a stated priced result for S-14 and S-7. If it gives none, the check is vacuous: say so in the packet, and do not claim it.
  - **Pass:** S-14 and S-7 equal between the builds, and no fuel-consequence row on any steady, `steady-before` or mill day.
  - **Fail (a row differs, or one lands on a steady day):** stop and the Architect rules.
  - **If it needs more than the worker call and the price seed the child already has (`demo_combined_kobo.py:138`):** do not build more here. Report it unproved in the packet, and `MONEY-B` carries it.
- **DD-1b2 F-THREADS (`MONEY-B`, always, on the whole build).**
  - Every Kobo fuel-consequence row traces to a Finding on a story day, and none lies on a steady day.
  - The Cost headline on one `steady-before` day and one `steady` day is reported as shown.
  - Each Grow figure reproduces from its rows (R12 item 2), which means the new full days' figures are stated, not assumed. Finish row WK-2a's S-1 figure (42.08 USD, `demo_combined_finish.py:527`) must stay equal, since S-1 is byte-equal.
  - **If MONEY-B differs from what the owner was told, they hear it before E3.**
- **Standing, +0, lane 1 (CH6b3-R2 in `build-sheet-CH-6.md`, once merged):** F-THREADS also reports every shown Kobo row state and fails on PRODUCER_NOT_SETTLED or a PARTIAL board.

### 4. `test_demo_combined_postgres.py:198`: **no change.**

- Line 198 reads the same default file that the test's prepare uses (`demo_combined.py:343`; that test file passes no `--days`), so the listed and resolved days agree on v3. EV's new `S-14d` fits the assertions by reading: the same count, the ruled weekday, and within the 7 days before the listed date. Not run.
- **Prove that part now without the barred test (+0):** L0 in `test_demo_story_days.py` resolves v3 on 7 consecutive values of S and applies the same weekday assertions.
- **The real consequence is cost, not line 198.** That test's fixture now prepares the whole of v3, about the same cost as E3. **DD-1b2 states how E2 runs it:** against the one E3 build, or pinned by `--days` to a shorter list. Any finish row it then breaks is DD-1b2's to fix. No change in DD-1a2.

### Size

**+0. DD-1a2 stays 2.25, DD-1 10.5.** All of this is inside existing G1, G2 and F-THREADS acceptance. Nothing goes to the backlog. SCOPE-1: both money checks are demo-critical, because the owner was told money stays the same.

### Handoff

Regenerate G1, then continue the handoff's order: R25 probe, L2 add-day, G2 with MONEY-A, the L0 above, the packet. The handoff's "Next" items otherwise stand.

## DD1a2-R3: review H1: the live day after the trial is `normal`, not `steady`; two owner corrections (Architect, Claude, 2026-11-07)

- Input: `.agent/review-DD-1a2.md` at `42a5d6ad6`. This is this Architect's last ruling in the lane. Nothing was run for it; the measurements are the reviewer's.

### 1. H1: **no product change. ST-7's live day is `normal` on S+2, and `add-day` refuses `steady` on that date by name.**

- **Reviewer's cause: confirmed in code.** `_day_states` applies the equal-facts rule only when given a `facts_window` (`actions/verification.py:553`), and later pins have none (per the review, `:702` and `:1093-1095`). `kobo-night-early` on S+2 starts S+1 21:00Z, inside S+1's UTC day, so S+1's selected run changes and `:564` reports "moved". Nothing re-binds it, so it never recovers.
- **What the demo needs (plan `client-demo-plan.html:592`, `:829`).** ST-7 is the closing step: one new day arrives and the board re-assesses on the next tick. With E3 on the session day minus 1, the day added is **S+2**. So the plan's own date is the failing date, and **option (b) alone fails**: S+3 needs the demo at least 2 days after the prepare, with S+2 reading no data. The open client date does not matter for this ruling: S+2 is the next free day on any session date at least one day after the prepare.
- **Why `normal`.** The reviewer measured it with the real chain: VERIFIED on all 3 ticks after the add. It is the existing `add-day` kind that ST-7 was built on, it needs no new scenario, and FILL-1's "named event kinds" already cover it. The added day reads partly checked, like S-1, S+0 and S+1 right beside it. **This reverses my Q8.3 reason** ("a live normal day should read like its 13 neighbours"): a "Verified" result staying true outranks a fully checked closing day. Its generator is needed throughout, and no Finding is expected (not measured here; the board check below reads it).
- **Rejected.**
  - **(a) Later pins get the equal-facts rule: not for this demo, backlog BL-26.** It is the honest fix for a real continuous Site, and it is small. But it changes what can keep an outcome VERIFIED, on the defended path behind the story's main verdict: a wrong facts comparison would hold "Verified" when readings really moved, and that error is silent. The demo does not need that risk.
  - **(c) `steady` 06-18 only:** a new untested kind that gives the same partly checked result as `normal`.
- **`steady` stays as built** for a live day from S+3 on (reviewer: VERIFIED on all 3 ticks with S+2 empty) and the `steady-before-first` fill of S-10. The R25 gate result stands for those days.

**Fix, for a fresh Sonnet builder (`task/DD-1a2-b22-day-list`).**
1. `tools/demo_story_days.py` `plan_add_day`: after the offset is resolved, if `site == "kobo"`, the kind has a `complement`, and the offset equals the `trial-after` entry's offset + 1 in `current`, raise `StoryDaysError("FULL_DAY_AFTER_TRIAL", ...)`. Message: "a full day here starts its night inside the trial's later day and takes the trial off Verified; use --kind normal (DD1a2-R3)". It must fire before any provisioning.
2. L0, `backend/tests/test_demo_story_days.py`: `steady` on S+2 refused with that code; `normal` on S+2 planned as one run; `steady` on S+3 planned as three runs. Mutation: remove the check and the first assertion fails.
3. L2, `host/tests/test_dd1a2_registered_kobo.py`, own `*_test` DB, about 5 min: the child's trial chain on S+0 and S+1; `plan_add_runs` and the child's `add_day` with `normal` on S+2; the prepare's tick 3 times. ACT-K1 reads VERIFIED through `VerificationService.current_state` before the add and after the ticks. Fail: stop and report.
4. Packet: correct `:18` (R25 plus L0 did not cover this), and correct `:46` to "price 1.25 USD, quantity 0 L: the generator delivers no power in the Candidate span". List H1's closure, and carry the script lines below under "Owed to DS-1".
5. Guards V, A, W, and the scoped story-day tests. A fresh Claude reviewer verifies H1's closure only.

**Owed to DD-1b2 / EX-1 (+0):** on a clone of the whole build, after the live `normal` add and its tick, read the board: Assure count, trial line and the Action's words unchanged, no new Finding. The reviewer's probe was two story days, read at the service.

**Plan, for the coordinator:** `:829` gains "the live step uses `normal` (DD1a2-R3)".

### 2. The two owner corrections: **informed, no question; the build does not wait.**

**(i) "A line on screen says so" was wrong, and that error was mine.** The text reaches only the Lab scenario pages, not the client screens where the jump shows.
- **The script explains it now (+0).** A note on the board's battery chart would be new copy on a shared screen, outside the mock-up, for a jump the owner has not yet seen. It goes on the walkthrough list as the owner's call, once they see it on screen.
- **It does not reopen their choice.** The alternative was about 22 litres a day and a problem raised on most days. The missing line does not make that better. The owner may still overrule.
- **Script:** "Each full example day starts at 6 am from a set battery level, so the line steps up there and the generator stops. Days aren't carried over; this is example data."

**(ii) MONEY-A shows no new cost rows, not "the same money".**
- **The price seed is not the cause (packet `:46` is wrong).** The rows carry 1.25 USD and 0 L. The trial Findings' generator delivers no power in the Candidate span and idle fuel isn't modelled, so 0 USD is computed. This is **already-decided behaviour, not a new defect**: `COST_ZERO`, "No fuel cost estimated: the generator was on but delivered no measured power" (`mini.py:64-65`, POLISH §1.1, R626 owner Q1), with idle fuel in BL-16.
- **Stated plainly: on the Kobo build the generator problem carries no fuel money figure.** The non-zero Kobo money is the Grow sales: WK-2a's 42.08 USD on S-1, and the new full days' own figures.
- **MONEY-B covers the non-zero money, confirmed:** each Grow figure reproduces from its rows, and WK-2a stays 42.08 USD (R2 §3). Add one assertion, +0: the fuel-consequence rows on S-14 and S-7 are PRICED with quantity 0, reported as such, so nobody reads them later as proof of equal non-zero money.

**Lines for the coordinator to send:**

> "Two corrections and one change on the Kobo example. First, we told you a line on screen explains the 6am battery jump. That was wrong: it only appears on an internal page. For now the presenter explains it, and you can decide whether it needs a line on screen when you walk through it. The 22-litre alternative isn't any better because of this, so we've kept your choice, but tell us if you see it differently. Second, the money check so far shows only that no new fuel cost appears. The generator problem days show no fuel cost at all, as you decided earlier, because the generator delivers no power in those hours. The real money figures are the mill sales, and those get checked on the final rehearsal before the full build. Third, the day added live at the end of the demo will be an ordinary generator day that reads 'partly checked', like the days right beside it. A fully checked day on that date would knock the trial off 'Verified', so the tool now refuses it."

### 3. Three revisions vs one: **confirmed, a script line; no separate walkthrough item.**
Finding counts, claim, minutes, thread counts and money are unaffected, and "Assessment updated; amount unchanged" is true. This answers the packet's question: accepted as expected. The cause is the reviewer's inference, not stored. The walkthrough will see it in passing.
**Script, if asked:** "The next day's readings overlap that day's window, so the system re-checked it. The result didn't change."

### Size and scope (SCOPE-1)
**+0. DD-1a2 stays 2.25, DD-1 10.5.** The refusal, its L0 and the L2 check are demo-critical: without them the closing step can take the story's main result off "Verified". **BL-26 (backlog, 0.5 est.):** later pins with the equal-facts rule. Only a continuous real Site needs it, and the demo avoids the date. BL-23 to BL-26 are free in this worktree and on main's list. Lane 1 may collide, so the second merge renumbers.

### Handoff
The fresh builder takes "Fix" items 1-5. A stop goes to a **new** lane-2 Architect, which reads this section, R2 and `.agent/review-DD-1a2.md`.

## DD1b1-R: rulings on the DD-1b1 pre-flight (Architect, Claude, 2026-11-07)

Binding checked: Claude (`.ai/ROLE_CONFIG.md` in this worktree, owner 2026-10-27). Input: `.agent/DD-1b1-preflight.md` at `74d092b24`. Nothing built or run; "read, not run" marks what the build must prove. **Where this differs from R6, R7, CH9b1-R2 or CH-9b `:187`, this section wins.**

**In one view**

| Q | Ruling |
|---|---|
| Q1 | (a). Cold and EV workers run on a story clock, on every prepare day. Add-day stays on wall time |
| Q2 | One rule per day: worker `received_at` + 5 min, work store + 6 min, Action + 10 min. The builder's single clock and EV 09:15 are refused |
| Q3 | (a) for ACT-003, and **ACT-002 also reads "Action agreed"**. R6's "APPLIED" is corrected |
| Q4 | (a). No migration, one L2 pin |
| Q5 | Owner **DD-1b2**, +0.75, with an order correction |
| Q6 | Refusal as recommended, on the seam that stays. The probe is not a demo prepare. `coh3_pairs` shares COH-3's own loop |
| Q7 | Objectives: one instant. **Publication seam goes to backlog (BL-30).** R6 overrides R645; owner informed |

**Size: DD-1b1 stays 1.25. DD-1b2 1.5 → 2.25. DD-1 10.5 → 11.25. Lane 2 remaining (DD-1b1, DD-1b2, CH-5d1): 3.75 → 4.5.** No owner question. **The build does not wait.**

### Builder's claims, checked

| Claim | Result |
|---|---|
| Finding pin needs a revision and selection known by `command_now` | Right. `finding_revision` is "created by `command_now`" (`postgres_domain_intent.py:85`), and the mill's `opportunity_revision_selected` is the same (`:120-128`) |
| Workers default to wall time | Right (`test_w206 :78-81`, `test_w203 :78`) |
| `select_exact` may not follow the clock | **Settled: it does.** `_project` passes `self.clock()` to `ev_persist` (`assessment_worker.py:333-334`) and `selected_at` is that value (`postgres_assessment_store.py:803`). Only `select_exact`'s own worker needs the clock |
| Triggers already pass `decided` | Right (`0025 :365,371,378,438`, `0029 :258`). A fresh read of `assetops_polish_full_test`: `cold_chain`, `ev_charging`, `mini_*` and `dispatch` `available_at` are story dates; only `mini_opportunity` (4 rows) is 2026-11-02 |
| EV "decision seam = `received_at`" (Q7) and worker "`received_at` + 5" meaning 09:10 (Q1/Q2) | **Wrong for EV.** The day's `received_at` is 09:30 (`demo-story-days-v3.json`); the decisions are 09:00 and 09:05 (`test_w205b :113-114`). See Q2 |
| ACT-002 carries APPLIED | **True only with the builder's single clock, and then the screen is wrong.** See Q3 |
| No tool records the mill Action | Right. But an owner was already named, twice and inconsistently. See Q5 |

### Q1. **(a).** Demo-critical; R6 cannot be met without it.

- **Cold (`demo_combined_cold.run_day`):** when the story clock is on, swap `P.run` so `produce` calls `test_w203_cold_replay_postgres.run(built, clock=lambda: worker_at)`. It applies to every Cold day built by `build`.
- **EV (`demo_combined_ev.run_day`):** call `run_worker(built, build_ev_assessment_worker(url, clock=lambda: worker_at))`, and swap `test_w206_ev_store_postgres.build_ev_assessment_worker` process-locally so `select_exact` gets the same clock. Dispose the worker yourself; `run_worker` disposes only its own.
- **All prepare days, not only the failure and fault days.** A story-dated S+0 beside a build-dated earlier occurrence would order one thread's causes across two clocks.
- **`add_day` passes the story clock off.** Its `received_at` is DB now, so + 5 min would stamp a selection in the future and hide it from live reads. Add-day stays byte-unchanged.
- **Standalone w502 and w504 are unchanged.**
- **Stop, do not patch, if** `P.enqueue_window` fires on a built day (its job has `available_at = now()`, so a story clock never leases it), or if `doc["blocked"]` is non-null after the failure day.
- This changes `created_at` and `selected_at` on those rows from build to story time. That is the intent: CH-6b2's "cause known after the evidence cutoff" stops applying to them. Any finish row or capture this moves is DD-1b2's.

### Q2. **One rule for both Sites, from the day's own `received_at`.**

| Step | Instant | Cold S+0 | EV fault Tuesday |
|---|---|---|---|
| Evidence decided | existing | 17:05 | 09:00, 09:05 |
| `received_at` | existing | 17:05 | 09:30 |
| `worker_at` | `received_at` + 5 min | 17:10 | 09:35 |
| Work store clock (cases, records, events, visits, plans) | `received_at` + 6 min, then + 1 s per command | 17:11:00 | 09:36:00 |
| Action `raised_at`, then domain store clock (Action, links, intent) | `received_at` + 10 min, then + 1 s per command | 17:15:00 | 09:40:00 |

- **Two clocks, not one.** They are the two existing seams: `PostgresWorkStore(test_db_clock_override=)` and `PostgresDomainIntentStore(test_db_clock_override=)`. Why is Q3. The work store still validates Finding links against the worker's selection.
- **Assert in the child:** the last work-store instant < the Action instant. Stop if not.
- **EV 09:15 is refused.** It precedes the day's own `received_at`, and it needs a Site-specific rule. All instants above are after the evidence.
- **`occurred_at` values do not move** (Cold 16:11-16:42; visits and plans). Story reading: the visit happened during the failure and was logged once the readings were in; the follow-up was agreed minutes later. No screen or script claims the gap.
- **`raised_at` hook.** In `tools/w502_cold_work_walkthrough.py` `BUILD`, in the `DEMO_NARRATIVES` pattern: `raised = globals().get("DEMO_ACTION_AT") or k0.known_at + step`. The child sets `DEMO_ACTION_AT` and swaps `test_w502_domain_intent_postgres.now_utc` to the domain clock before the `exec`; the first read returns the Action instant, so `raised <= db_now` holds. EV: swap `W._db_now` to the same clock. Restore every swap, as `_restore` does.
- Swaps of `work.composition.build_work_store` and `build_domain_intent_store` stay process-local and in the children. Composition still passes nothing.

### Q3. **(a) for ACT-003. ACT-002 also ends ACTION_IN_HAND ("Action agreed"). No new story content.**

R6 says "with their APPLIED and case causes". Everything about what the client sees says otherwise:
- plan `:811`: "ACT-002 reads 'Action agreed'. EV: the same with ACT-003"; ST-4 and ST-5 (`:589-590`): "in hand"; `build-sheet-CH-3.md:20`: both ACTION_IN_HAND; MD-0 ACT-E1;
- mock `:336` shows the Action "Open", and `:604-610`: "Activity completed", "Witnessed auto-start test: Missing", "Completion proves the inspection happened";
- the record itself says "witnessed automatic-start test remains required" (`w502` BUILD).

**What the builder's single clock would do (read, not run).** `cause_order` is known-time order (`lifecycle.py:186`). The Action at 17:15:00, then COMPLETE recorded after it, gives ACCEPTED then APPLIED, so CHANGE_APPLIED effective S+0 from the 16:42 `occurred_at`. The S+0 board would then read "Change made", for work done before the Action existed, on an Action whose own record says it is not done. `outcomes/status.py:75` stops counting an applied primary signal, so the row can lose Needs attention, and `claims.py:35` stops counting the thread as disrupting. Story cutoffs hide this today only because the causes are build-dated (`review-packet-CH-3.md:329-333`, listed there "for the DD-1 inventory"). R6 would have exposed it.

**The fix is the record order; no product change.** With Q2's clocks, COMPLETE is known at 17:11, after the thread's OPEN (17:10) and before ACCEPTED (17:15):
- APPLIED is judged from OPEN and skipped `ILLEGAL_TRANSITION`; ACCEPTED then gives ACTION_IN_HAND;
- on a rerun the same cause is `BEFORE_HEAD`, so a rerun writes nothing (`lifecycle.py:252-266`).

That is also the true rule: a completion before the Action cannot be the Action's change.

**Kept:** WR COMPLETED on Maintenance and on the Action detail, the case link, the intent basis, and the third-visit notice, untouched.

**R6 and the acceptance now read:** ACT-002 and ACT-003 are recorded at story time. ACT-002 keeps its linked case, and its COMPLETE is recorded at story time and applies no change. Both threads read ACTION_IN_HAND on their day.

Class: demo-critical (a false "Change made" on a client screen), +0. **Backlog BL-31:** a real later "Change made" for Cold and EV (Q3(b), and MD-0's ACT-C1 pattern). It is new shown content, and no script line needs it. Change made is shown on Kobo and the mill.

### Q4. **(a). No migration, no trigger edit.**

- L2, own `*_test` DB: for one EV and one mini row, `available_at = created_at = decided_at` with the ledger's decision override set; DB time with it unset.
- R7's third item is withdrawn. R7's aim, "studies carry story time", is not reached through this seam.
- Opportunity studies stay a declared R4 build-time fact (BL-32), **except the one study the mill Action pins**, which is DD-1b2's (Q5).

### Q5. **Owner: DD-1b2. Demo-critical, +0.75.**

The record: CH9b1-R2 names DD-1b2 ("recorded before R8 step 1", +0); `build-sheet-CH-9b.md:187` says "DD-1b1 calls" the freeze; CH9b3-R Q9 and Q11 say "DD-1b". **CH9b1-R2 stands as the owner. `:187`'s "DD-1b1" is corrected to DD-1b2.** The +0 was wrong: no part of this exists, as the builder found. Without it, ST-3's Grow story, F-THREADS and MILL-3 have nothing to read. DD-1b1 builds none of it and adds no stub.

DD-1b2 gets this at **+0.75** (its pre-flight confirms the seams; all read, not run):
1. **One step, `tools/demo_combined_mill.py`, run by the parent as a child. It must run after all three Site children.** `next_action_no` is the shared `action_code_seq` (`postgres_domain_intent.py:118`), so running it inside the Kobo child would take ACT-000002 and renumber Cold and EV against ST-4 and ST-5. It takes the next code after them.
2. **It must run after backfill step `a` and before `b,c,d`, which corrects CH9b1-R2's "before R8 step 1".** The freeze chooses baseline days from snapshot rows (`test_ch9b2_midday_plan_postgres.py` `_snap`; the DD-1a2 dry run also runs step `a` first), and step `a` builds those. The mill Action is then linked by step `c`.
3. **The story-dated study (Q4(b), this one only):** the study for the days before S-9, in process, with the existing `test_clock_override`, `test_lease_clock` and worker clock. The instant is after the last built day before `mill-midday`. So `opportunity_revision_selected` holds at the Action's `command_now`.
4. **The record, in story time, in Action-first order:** Action, case, record, COMPLETE before S-9's midday, link, `freeze_domain_plan`, then `evaluate_domain_plan` over the later days. Unlike ACT-002, here ACCEPTED must be known before COMPLETE, so that it reaches CHANGE_APPLIED. F-THREADS and MILL-3 assert this as already ruled.

### Q6. **Refusal as recommended. The probe is allowed. `coh3_pairs` shares the loop.**

**Refusal.**
- New `backend/assetops_backend/prepare_clock.py`: `require_prepare_database(url)`. The database name comes from `sqlalchemy.engine.make_url`, against `^assetops_polish_.*$|^.*_test$`. Otherwise it raises `PrepareClockRefused` with code `PREPARE_CLOCK_REFUSED`, naming the database. Composition never imports it.
- `PostgresObjectiveStore(url, *, test_recorded_clock_override=None)` calls it at construction when the override is set. The SQL fragment is literally `clock_timestamp()` when unset, `:recorded_at` when set.
- The children call it where they switch the story clock on. Existing `test_*` overrides are not edited.
- L0: `assetops_polish_x` and `foo_test` pass; `assetops`, `assetops_polish` and `assetops_demo3_x` refuse; a refused construction opens no connection. L0: with the override unset, the statement text contains `clock_timestamp()` and no new parameter.

**`coh3_pairs(bundle)`.** One generator beside `coh3_action_on_board`, yielding `(site_code, day, action_id, finding_id, linked)` for the pairs passing its existing condition. `coh3_action_on_board` is rewritten over it, so the count cannot drift from the rule; its findings stay identical. `test_chain_coherence.py`: a pair linked, a pair not linked (finding), and an Action after the window (no pair). Mutation: invert the window test and a test fails.

**The probe, `tools/dd1b1_coh3_probe.py`: confirmed, not a "demo prepare", on the DD1a2-R Q8.5 terms.**
- **Allowed:** the children's `run_day` for Cold's `failure` day and EV's `fault` day only, on the builder's own `pg_harness.fresh_database()`; `backfill --steps a,b,c,d`; at most 3 ticks; the board and index reads; `chain_coherence.collect`.
- **Barred:** the `tools/demo_combined.py prepare` parent; finish rows; Kobo; any `assetops_polish_*` or `assetops_demo3_*` DB; the full-prepare test.
- Machine idle, one heavy job, `tools/keep-awake-during-tests.ps1`. **Cap 20 min; past it, stop and report.**
- **Report to `.agent/DD-1b1-coh3-probe.json`. Pass means all of:**
  - `coh3_pairs` ≥ 1 for COLD-LAB-001 and for EV-LAB-001, with 0 COH-3 findings;
  - both Actions' `raised_at` and `recorded_at`, COMPLETE's `recorded_at` and each Finding's `created_at` at the Q2 instants (the +1 s steps allowed);
  - the Cold start-failure and EV interruption threads ACTION_IN_HAND; ACT-002's APPLIED appears in lifecycle `skipped`; a further tick writes no thread event;
  - each S+0 board's `in_hand` lists the Action; the Cold Protect row is `NEEDS_ATTENTION`;
  - WR COMPLETED, and `doc["blocked"]` null.
- **Fail:** stop and report. Never change the product, a clock or a threshold to pass it. A real COH-3 finding, or CHANGE_APPLIED on Cold, comes back to this Architect.

**Scoped checks:** the above; `test_demo_story_days.py`; `test_ch1b_*`; `test_s6_verification_replay*`; `tools/checks/test_chain_coherence.py`; guards A, W, N, V, M. Not `test_demo_combined_*`, not the suites. F-COH3 on the whole build stays in DD-1b2.

### Q7. **Objectives: one instant. Publication: backlog. R645: overridden.**

**Objective seam, demo-critical.** A past-cutoff read must show the target that existed, or the same day's verdict differs by read (`current(known_at)`, `postgres_objective_store.py:167-171`).
- **All fixture lines at one instant: `ev.install_at` + `TARIFF_AFTER_INSTALL`, which is S-26d 07:00**, the first moment all three Sites exist. It is a fixed value from existing facts. The per-Site offsets and "MG-1 alone" are refused: `declare_objective fixture` is one call with one store, and mixed dates on one board help nobody.
- New `tools/demo_declare_objectives.py <url> <file> <iso>`, calling `declare_objective.main(["fixture", "--file", file], store=PostgresObjectiveStore(url, test_recorded_clock_override=...))`. `demo_combined.finish` calls it through `self.py` at the same place, under the same guard, with the same stdout, so `objectives.json` is unchanged in shape.
- Assert the instant is earlier than the first built day's start across the Sites; stop if not.
- L2: set: `recorded_at` is the instant, a `known_at` read before it shows none and after it shows the line. Unset: DB time, and a live read is unchanged.

**Publication seam: not built. Backlog BL-30.** Nothing shown or cut off reads this date: `source_provenance.py:6` reads no date; the ledger's other uses are `ORDER BY p.recorded_at` inside one run (`postgres_evidence_ledger.py:1096-1100`) and an idempotent replay. It fails the SCOPE-1 test, and it would need a third seam and an EV-specific value. It stays a declared build-time fact. This reduces R7. **Build check:** grep routes for `evidence_publication`'s `recorded_at`; if any response carries it to a client, stop and report.

**R645: R6 overrides it. Confirmed, and it is not an owner question.** R645 was a recorded data reading, "Backdating is refused: the Finding revisions are recorded at build time", and Q1 removes that cause. The change goes toward what the owner was told (plan ST-5 "ACT-003 is visible as in hand", MA-1 M6, mock `cold` and `ev` rows), and the owner's walkthrough of this dataset has not happened.
- The builder updates the comment at `demo_combined_ev.py:162-164` and the docstring's "raised at DB now", and marks register row R645 closed by DD-1b1 in `.agent/mock-departure-register.md`.
- `POLISH-runbook.md` line 49 is history. The script line is DS-1's. Finish rows and captures expecting the old state are DD-1b2's.

### Scope and size (SCOPE-1)

| Item | Class | Reason | Size |
|---|---|---|---|
| Cold/EV worker story clock (Q1) | demo-critical | R6 is refused without it | +0.25 |
| Two-clock record order (Q2, Q3) | demo-critical | Keeps a false "Change made" off the screen | +0 |
| Trigger work replaced by one L2 pin (Q4) | removal | Premise was wrong | −0.125 |
| Publication seam (Q7) | backlog, **BL-30** | No reader of the date | −0.125 |
| Probe, `coh3_pairs`, refusal helper | demo-critical | Inside R6/R7 acceptance | +0 |
| Mill Action step and its study (Q5) | demo-critical, **DD-1b2** | ST-3, F-THREADS, MILL-3 have nothing to read otherwise | +0.75 on DD-1b2 |
| Later "Change made" for Cold and EV | backlog, **BL-31** | New shown content | 0.5 est. |
| Other opportunity studies at story time | backlog, **BL-32** | No shown date, Action or cutoff needs them | 0.25 est. |

**DD-1b1 acceptance, replacing line 117 (with SCOPE-1):** ACT-002 and ACT-003 recorded at story time per Q2, both threads ACTION_IN_HAND; ACT-002's case linked with COMPLETE recorded and no change applied; COH-3 evaluates at least one pair per Cold and EV board, proved by the Q6 probe; the objective override refused outside `assetops_polish_*` / `*_test`, and the children's clocks behind the same check; unset leaves product behaviour byte-unchanged (L0 text, L2 reads); add-day unchanged; the Q4 pin; R645 closed.

**Owed to DD-1b2 (+0 beyond Q5):** `expected-threads.json` and F-THREADS expect ACT-002 and ACT-003 "Action agreed"; `expected-today.json` I-09 reconcile; finish rows and E2 effects of story-dated Cold and EV rows; the Protect "Why?" now naming both Cold threads.

**Plan, for the coordinator:** DD-1b1 1.25 with R7 reduced; DD-1b2 2.25 (mill step, Q5); DD-1 11.25; lane 2 remaining 4.5; the R6 phrase at the handoff's `:58` and `:227` is corrected by Q3. Plan `:811` and ST-4/ST-5 stand as written.

### Owner, informed (no decision; the build does not wait)
- "The GreenHarvest and Depot actions now show on their failure-day boards as 'Action agreed', as the plan says. The GreenHarvest inspection shows as completed and the witnessed start test as still to do. We won't show 'Change made' there, because that inspection happened before the action was agreed."
- "Recording the mill action was never built, and the last data step now includes it: 0.75 more, for 4.5 left on this lane. Without it the Grow story has nothing to verify."

### Handoff
The builder resumes on `task/DD-1b1-story-time-actions`: Q6's helper and L0s; Q1 and Q2's child swaps and the BUILD hook; `coh3_pairs`; Q7's objective seam and tool; Q4's pin; the probe; scoped checks; the R645 records; packet. Stops come back to this Architect. Own review.

## DD1b1-R2: the Q6 probe failed; one read fix, whole-day links, per-Site objective instants (Architect, Claude, 2026-11-07)

Input: `.agent/DD-1b1-coh3-probe.json`, `.agent/review-packet-DD-1b1.md` at `131f18e86`, the probe's bundle, and the code. **This section wins over DD1b1-R where they differ.** The misses were this Architect's, not the builder's: DD1b1-R Q6 expected a pair without tracing the board's read windows, Q7 did not check Kobo's first day, and "reads Action agreed" named the wrong screen. The builder stopped correctly and tuned nothing.

**Size: DD-1b1 1.25 → 1.5 (+0.25, demo-critical: ST-4 and ST-5 cannot be shown truthfully without it). DD-1 11.5. Lane 2 remaining on the DD1b1-R basis: 4.5 → 4.75.** No owner question. **The build resumes; it does not wait.**

### 1. What the client must see, and why no window reaches it today

**Requirement (ST-4, ST-5, MA-1 M6, mock `:336`).** On the story-day board the client sees, together: the Finding; Protect at Needs attention; the Action under "Already in hand", state **"Open"**, with no "outside this view" suffix. "Action agreed" is the thread's word, on the Site chain (`chain_site` carries it; the board bundle has none). The board's "Open" is the mock's own badge and `board.py:865`. So plan `:811` is met on the chain, not by the board row. No label changes.

**What the demo opens.** `story_links` (`demo_combined.py:237-262`): Cold `/sites/COLD-LAB-001?from=16:00&to=17:05`, EV `/sites/EV-LAB-001/ev?from=08:00&to=09:00`, each the day's event window. The finish rows read the same (`Ctx.window`). **The COH-3 collector reads something else for Cold**: the Site-local day (`day_windows`).

**Why no window works (code; EV and Cold's local day are also observed in the probe).** The Action index selects `raised_at` in `[lo, hi)` (`postgres_domain_action_index.py:74-77`), and the composers call it with their `hi`.
- **Event found in the window:** `compose` passes `read_hi` = the event's end as `hi` (`read.py:384-389`), whatever was requested. An Action follows its evidence, so `raised_at` ≥ `hi` always. The Finding shows and the Action never does. The week link has the same defect.
- **No event found:** Findings are read over a window with no selection. The Action lists, as "outside this view", and the Finding does not.

**S1 answered: `received_at` was not the wrong anchor.** No instant after the evidence can pass, and the board's `known_at` is not what excludes the Action. Moving the Action inside the event is **refused**: it would claim the Action before its Finding existed. **Q2's instants stand unchanged**, proved by the probe.

**Options**

| | Change | Client sees | Cost |
|---|---|---|---|
| **A. Ruled** | The board's Action read runs to the **requested** window's end; Cold and EV story links open the whole UTC day | Finding and Action together; Needs attention; the lead names the event's own time (CH6b1-R5). An event-only window still lists no Action | +0.25 |
| B | In hand reads by thread, whatever the date | The same, and also on event-only windows and on boards before the Action | About +0.5 and a new as-known rule. Not demo-critical; BL-38 |
| C | Drop COH-3 for these boards; no product change | Finding and no Action on the board; the Action only on Work › Actions; "Action agreed" on the chain. R645 stays. ST-4 and ST-5 are false and the plan and owner line change | 0, but it presents less than was told |

**Why A is right beyond the demo.** On any real Site an Action follows its event, so today a week board can never list it. CH6b1-R3 already says the board's window stays the requested one; only this read drifted to the event. Nothing outside the requested window is read.

### 2. The build (A), and the corrected values

**Product, one read.** `read.py` `compose` passes `actions_to=hi` to the composer when `event` is not None. `cold.compose` and `ev.compose` take `actions_to: datetime | None = None` and call `ports.domain_actions(work_lo, actions_to or hi)`. With no event the call is unchanged. Plans, incidents and visits keep `hi`. Mini is untouched.

**S1, S2 windows, by rule: a Cold or EV story day's board is its whole UTC day, `[00:00Z, next 00:00Z)`.** It is the existing no-event form in `story_links`, and the only day form the estate read accepts (`estate/scope.py:108-110`).
- Probe days: EV `2026-11-03T00:00Z` to `2026-11-04T00:00Z`, containing 08:00-09:00 and the Action at 09:40; Cold `2026-11-05T00:00Z` to `2026-11-06T00:00Z`, containing 16:00-17:05 and 17:15.
- `story_links`: every Cold and EV dated day uses it (labels keep their kind), and `LINK_FORMS` stands.
- `chain_coherence.day_windows`: Cold and EV `from`/`to` are that day, `estate` the same. Kobo is unchanged. COH-3's rule is unchanged, `created <= to`.
- **Refused:** a local-day Cold link. It falls back (`EstateRefusal`) unless the estate rule is widened, and BL-20's rule stands.
- `demo_combined_finish.Ctx.window` is **not** changed here. Rows that need the Action move to the day window in DD-1b2.

**S3, by rule: each Site's lines at that Site's own first declared knowledge instant. This reverses Q7's "one instant".** That Q7 reason was wrong: `declare_objective fixture` already takes `--site`, and one date per Site is not mixed dates on a board.

| Site | Rule | Value | First built day |
|---|---|---|---|
| KOBO-001 | `price_recorded_at` (install + 1 h) | S-29d 12:00 | S-28d |
| COLD-LAB-001 | `install_at` + `TARIFF_AFTER_INSTALL` | S-26d 06:30 | S-7d |
| EV-LAB-001 | `install_at` + `TARIFF_AFTER_INSTALL` (its tariff instant) | S-26d 07:00 | S-14d, moved to its Tuesday |

- `objectives_instant` becomes `objectives_instants(story) -> {site_code: instant}`, asserting per Site that the instant is before that Site's first built day, else `OBJECTIVES_INSTANT_CONFLICT`.
- `demo_declare_objectives.py <url> <file> <site> <iso>` is called once per Site through `self.py`; `objectives.json` holds all the lines in the same shape. Update the L0s.

### 3. The control: **no story-clock-off run. Read the same database three ways, inside the re-probe.**

A story-off run costs another build and a new flag, and it proves less. On the one story-clock DB, read Cold's board over:
1. the UTC day;
2. the event window `[16:00, 17:05)`;
3. the local day `[21:00Z, 21:00Z)`, for the record.

**The attribution is (2).** Its `known_at` stays 17:05 and the Finding is 17:10. Finding shown: the window was the cause and `known_at` is cleared (leading reading now: the logged `EstateRefusal`; a build-dated Finding was also after 17:05 and shown on this window in the finish rows; EV shows a 09:35 Finding at `known_at` 09:00). **Finding absent on (1) and (2): the story clock hid it. Stop and return here; only then is the story-off control named.**

### 4. R645: **the reversal stands, conditional on the re-probe.** Keep the register row open until it passes; then close it and correct the `demo_combined_ev.py` comment.

**Corrected owner line, replacing the one sent:** "Correction to what I told you: this isn't proved yet. A retest is coming, after a small fix. Boards stopped looking at the end of the event, so an action agreed afterwards never appeared. With the fix, each GreenHarvest and Depot story-day link opens the whole day and shows the problem together with its action, marked 'Open'. 'Action agreed' appears on the Site's chain, not on the board row. The GreenHarvest inspection still shows completed, with the witnessed test still to do. No decision needed."

### 5. The re-probe, the cheapest honest proof

The same `tools/dd1b1_coh3_probe.py` on its own routed `*_test` DB, Q6's terms and bars. **1 tick instead of 3** (0 thread events are proved, and DD-1b2 repeats it on the whole build). About 3 min, cap 20.

**Pass, all of:**
- UTC-day boards: `coh3_pairs` ≥ 1 for each Site, 0 COH-3 findings; Protect `NEEDS_ATTENTION`; the Finding in `issues`; the Protect row's `in_hand` lists the Action, state "Open", no suffix;
- `chain_site` for each day carries "Action agreed";
- event-window boards: the Finding shown, and the Action **not** listed (recorded as the rule);
- every instant and state check that already passed;
- `objectives_instants` resolved on real v3 passes all three Sites, with no prepare.

Any other result: stop and report.

**New tests.** L0 for both composers: event inside a wider window: Action after the event and inside the window listed; Action after the requested end not listed; no event: arguments unchanged. Mutation: drop `actions_to` and a test fails. `test_demo_combined_links.py` and `test_chain_coherence.py` for the day form.

**Then, as the handoff lists:** mutation proofs, `test_ch1b_*`, `test_s6_verification_replay*`, add `test_ch6b1*` and `test_ch6b2*`, guards A, W, N, V, M. `demo_declare_objectives.py` per Site runs end to end on the probe DB, for that part only. Add-day stays by construction, and its run is DD-1b2's.

### 6. Scope

| Item | Class | Reason | Size |
|---|---|---|---|
| `actions_to`, day links, collector, per-Site objectives | demo-critical | ST-4 and ST-5; a full prepare stops at finish without S3 | +0.25 |
| Board in hand by thread, for any window (B) | backlog, **BL-38** | Day and week links show the Action; exact-window reads are not in the script | 0.5 est. |

**Owed to DD-1b2 (+0):** finish rows needing the Action read the day window; any in-app link carrying an exact event window that the script follows is listed and either avoided or stated; COH rules on the new Cold and EV day windows reconciled with `expected-today.json`.

**Plan, for the coordinator:** DD-1b1 1.5; DD-1 11.5; lane 2 remaining +0.25; plan `:811`'s "reads 'Action agreed'" is the chain, and the board reads "Open".

## DD1b1-R3: the re-probe failed because R2's own read fix asked for 32 days; the read is refused and swallowed (Architect, Claude, 2026-11-07)

Input: `.agent/DD-1b1-coh3-probe-r2.json`, `.agent/DD-1b1-handoff.md` at `1f0602661`, the re-probe's stored bundle, and the code. **This section wins over R2 where they differ. No size change: DD-1b1 stays 1.5. No owner question now. The build resumes; it does not wait, and the §5 fallback is decided now.**

**The miss was this Architect's.** R2 widened the Action read's upper end and left the lower end on the event. The R2 L0s used fake ports, so nothing met the real parser.

### 0. What was measured, not read

**Run on this commit, against the real parser** (`work/domain_action_index.parse_index_request`):

| Read | From | To | Result |
|---|---|---|---|
| R2, EV UTC day | 2026-10-03T09:00Z (`event_hi` − 31 d) | 2026-11-04T00:00Z | **REFUSED `INVALID_WINDOW`** |
| R2, Cold UTC day | 2026-10-05T17:05Z | 2026-11-06T00:00Z | **REFUSED `INVALID_WINDOW`** |
| A', EV | 2026-10-04T00:00Z (`actions_to` − 31 d) | 2026-11-04T00:00Z | accepted, `known_at` None |
| A', Cold | 2026-10-06T00:00Z | 2026-11-06T00:00Z | accepted, `known_at` None |

**Stored re-probe bundle:** both UTC-day boards have `read_state: PARTIAL`, the mark of a swallowed read (`read.py:10`). The bundle does not name which read failed, and the re-probe below will show whether another one does. **No further measurement is needed before the fix**; the re-probe is the end-to-end proof.

**The builder's hypothesis (`recorded_at <= :k` with `k` = event end) is refuted by the same probe.** The Cold local-day read has window `known_at` 17:05 and still lists the Action recorded at 17:15. The board's Action read does not take the board's cutoff: `_domain_actions(site, known_at)` passes only the **request's** `known_at`, here none, so `k` = `read_at` (`read.py:211-219`; `domain_action_index.py:400`). The stored `action_index` rows confirm `known_at` = read time. On this point R2 stands: the board's `known_at` does not exclude the Action.

### 1. The trace, story link to row

`GET /sites/{code}?from&to` → `board()` → `compose()` → `event_window` (a whole UTC day is accepted; a local day raises `EstateRefusal` and falls back) → `composer(lo=event_lo, hi=event_hi, actions_to=requested_hi)` → `reads.pages("domain_action_index", ...)` → `assemble` → `with_threads` → the row builder.

**An Action lists under "Already in hand" only if all of these hold** (rows 7 to 9 are read, not run, on this path):

| # | Condition | Where | UTC day under R2 |
|---|---|---|---|
| 1 | The window is valid: `to − from ≤ 31 d` | `parse_index_request:94` | **FAILS.** `Reads.call` swallows it: `action_rows` None, no Actions, `PARTIAL` |
| 2 | `raised_at` in `[from, to)` | `actions_in_window` | not reached |
| 3 | `recorded_at ≤ k`; `k` = the request's `known_at`, else read time | same; `:400` | not reached; would pass |
| 4 | `origin_opportunity_id IS NULL` | same | would pass |
| 5 | A non-null `title` | `cold.py` (B-Q21), EV alike | would pass |
| 6 | A non-null origin Finding | `board.py:841` | would pass |
| 7 | Not an Earlier result: `is_domain`, and not `_earlier_segment` | `board.py:852-854, 974` | would pass, one segment |
| 8 | `a.open`, always True for a domain Action | `cold.domain_action` | would pass |
| 9 | `cat in move_cats` of the origin's roles | `board.py:850, 865` | Protect, from the row's issues |

**How it links.** `origin = by_id.get(origin_finding_id)`, else a Finding on the same thread (`:844-847`), else the suffix "linked finding outside this view". With the Finding on the board there is no suffix. COH-3's link is any `in_hand`, `earlier` or `issues` href containing the Action id (`_board_hrefs`); `action_ref(view="verification")` carries it.

**Why ACT-001 shows on Cold.** It **is** the story Action. The probe builds no Kobo, so the shared `action_code_seq` gives Cold 000001 and EV 000002; a full build gives 000002 and 000003. On the local day no event resolves, so `actions_to` is None, the read spans exactly 31 d, condition 1 passes and the Action lists. Findings are read over a window with no selection, so it takes the suffix and Protect is UNKNOWN. That also settles R2's S2: the window was the cause, as the re-probe's event-window read showed (the Finding at 17:10 shown at `known_at` 17:05).

### 2. `k`: what it is, and why an Action after it is truthful

- **Deliberate, and it bounds evidence only.** The board's `window.known_at` is the overview's evidence cutoff (`board_cutoff`, `site_cutoff`; CH-5a1 R7). `lifecycle_cutoff` (CH6b2-R2, `chain/read.py:39-43`) says so: "R7's evidence cutoff bounds evidence only; a Finding is known after the evidence it assesses". So the board claims: **these readings were judged as of `k`, and the workflow is as known at the request's cutoff, else now.**
- **Readers.** `window.known_at` on the wire; the thread lookup's `known_at=cutoff, visible_at=request`; per-Site cutoffs in `estate/index.py:156`. Actions and lifecycle take the request's cutoff. Kobo takes the request's cutoff only (`site_cutoff` mini branch). CO-1 reads Kobo's board and is not on this path.
- **What protects a past read is unchanged.** With a request `known_at` before 17:15, `recorded_at ≤ k` still hides the Action, correctly.
- **A' does not touch `k`, its consumers, or any known-time rule.** An Action agreed after the event, inside the requested window, is a fact as of now, and its `raised_at` is shown truthfully.

### 3. Ruling: **A'**, a one-line correction of R2, with a decided fallback

| | Client on the story-day link | Size | Risk this late |
|---|---|---|---|
| **A' (ruled)** | Finding, Needs attention, the Action "Open" under Already in hand, no suffix; "Action agreed" on the chain | +0 | Low. The cause was executed; one bound moves |
| B by thread (BL-38) | The same, also on exact-window boards and on boards before the Action | 0.5 est. | A new as-known rule, on a board two rulings have already misjudged. It stays in the backlog |
| C drop COH-3 on these boards | Finding and Needs attention, no Action on the board; the Action on Work › Actions and the chain. ST-4 and ST-5 change | about −0.25 | Low build risk, but it presents less than the owner was told |

**Why not C or B, weighed against two misses.** Both misses were reasoning about a path nobody had run. This cause is executed, with the bundle's `PARTIAL` as independent evidence and the local-day read as a control. C would retreat from a one-line bug in a read that also hides real Actions on week boards, at the price of an owner question and a script change.

**The edit, in both `cold.compose` and `ev.compose`.** Both bounds of the Action read come from one end:
```python
actions_hi = actions_to or hi
action_rows = reads.pages("domain_action_index", ports.domain_actions, actions_hi - WORK_WINDOW, actions_hi)
```
Plans, incidents and visits keep `work_lo` and `hi`.

**Regression surface, by construction:**
- **Kobo: none.** The mini branch returns before this code (`read.py:370-377`); `mini.compose` is not edited; the Action index service and `k` are not edited. No Kobo build for this; `test_s6_verification_replay*` stays in the scoped list.
- **Exact event window (finish rows on Cold and EV):** `event` equals the request, so `actions_hi = hi`, and the read is byte-equal to before R2.
- **No event:** `actions_to` None, byte-equal.
- **Wider window with an event (day, week, month, Portfolio's `board_summary`):** Actions raised after the event and inside the window now list. That is the intended change. Actions older than 31 d before the window's end drop out, the rule every other board has. `facts.actions` feeds in hand, Earlier and the thread lookup; a thread's state does not come from it.
- **Today's R2 commit is worse than before R2:** every Cold and EV board with an event inside a wider window is `PARTIAL`, week boards included. **Do not merge without this line.**
- **Main at `f7c045bee`:** no change under `site_outcomes`, `work` or `chain/lookup.py` since the merge base (checked by diff). CH-6b3's edits are `chain/claims.py`, `vocabulary.py` and `why.py`, none on this read. CH6b3-R2 concerns `PARTIAL` boards, so a further reason to clear it. Merge main **after** the re-probe passes, then rerun the scoped tests.

### 4. Tests and the re-probe

**L0 (new; real parser, no fake on this seam).** For Cold and EV: ports whose `domain_actions` calls the real `parse_index_request`.
- Event inside a UTC day: the read is accepted; an Action after the event and inside the day listed; `domain_action_index` not in the failed reads.
- An Action after the requested end: not listed.
- Exact window: the same arguments as `hi − 31 d, hi`.
- **Mutation:** restore `work_lo` as the lower bound and the test fails with the read refused.

**Fix two probe checks first; both judged the wrong thing.**
- `in_hand_open_no_suffix` requires **all** rows "Open", but PM rows are "Overdue". Judge only the row whose text begins with the Action's own code: present, state exactly "Open".
- `event_window.action_not_listed` requires an empty `in_hand`. Judge only that the Action's code is absent.

**Re-probe:** the same tool, own routed DB, Q6's terms and bars, 1 tick, about 3 min, cap 20. **Pass, all of:**
- every R2 §5 check, as corrected above;
- `coh3_pairs` ≥ 1 per Site, **all linked**, 0 COH-3 findings;
- **new:** record `read_state` for the UTC-day and event-window boards on each Site, and the failed read names through a `Reads` log line or in-process hook in the probe only. `domain_action_index` is in neither. The UTC-day value equals the event-window value. If either is still `PARTIAL`, report which read failed; a read other than this one is reported, and does not itself fail the probe;
- a week board (`board_summary.week`) for each Site lists the Action.

**Then:** close R645 and correct the comment; mutation proofs; `test_ch1b_*`, `test_s6_verification_replay*`, `test_ch6b1*`, `test_ch6b2*`; guards A, W, N, V, M; merge main; rerun those scoped tests; packet.

### 5. If this re-probe fails on the Action: **stop trying at the board. No third read fix.**

The builder stops and reports. The coordinator then sends this question without waiting for another ruling:

> **Owner question.** "We tried to show each GreenHarvest and Depot problem together with its agreed action on the same board, and the test failed. I recommend the board shows the problem and marks it Needs attention, and the action appears on the Site's chain as 'Action agreed' and on the Actions list, one click away. That keeps the story honest and gets the demo built now. You lose seeing both on one screen; the script would say 'the action is here'. The alternative is about half a unit more to rework how boards find actions, late, on a screen we've already misjudged twice. The rest of the build can continue while you decide."

**On C, what stays:** the story clocks, instants, ACTION_IN_HAND, Cold's skipped APPLIED, per-Site objectives, the probe and `coh3_pairs`. **What is reverted:** `actions_to` (as committed it causes `PARTIAL`), the whole-day `story_links` and `day_windows`. COH-3 stays on Kobo; on Cold and EV it records the unlinked pairs as an expected, disclosed departure. R645 stays open, reworded. ST-4 and ST-5 change to "on the chain and the Actions list".

**On A', all of R2's commits stay.**

### 6. Scope and what is owed

| Item | Class | Reason | Size |
|---|---|---|---|
| A' bound, real-parser L0, two probe check fixes | demo-critical | ST-4 and ST-5; and it undoes R2's `PARTIAL` boards | +0, inside R2's +0.25 |

**R2 §6, updated, owed to DD-1b2 (+0):**
- finish rows needing the Action read the day window;
- **new:** a finish assertion that `domain_action_index` is not a failed read on Cold and EV story-day and week boards, since `Reads.call` hides a refusal silently;
- any in-app link carrying an exact event window that the script follows is listed and either avoided or stated (the exact window lists no Action, by rule);
- COH rules on the new Cold and EV day windows reconciled with `expected-today.json`.

**Backlog: no new row.** `Reads.call` swallowing a refusal is by design (B.3, a failed read never refuses the board), and the finish assertion covers the demo.

**Owner.** The R2 line stands, since a retest was already promised. Nothing further until the re-probe reports; do not say it is fixed yet.

