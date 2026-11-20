## DD1b2-R9: P0's COH-2 stop and two notes (Architect, Claude, 2026-11-07)

Input: the coordinator's relay of the P0 builder's report (prepare 226 s, exit 0, at `f4454f2d5`; R8 fixes at `78f3b1c7f`). **READ** = code, cited. I ran nothing.

### 1. COH-2 on Cold and EV: a known product gap, so it gets a named expectation

**The cause is in the product, and it is already known (READ).**
- The Portfolio joins a Finding row to its Action through `select_action_scope`. That reads Actions only on Sites whose domain is mini-grid (`estate/index.py:193-195`). Cold and EV domain Actions never reach the join (`estate/portfolio.py:259, 279-281`), so their Portfolio rows read `action_id` null, which shows as "No action agreed yet".
- COH-2 takes Actions from both the estate index and every domain `action_index` (`tools/checks/chain_coherence.py:337-353`). It is right to flag the mismatch. The tool is not wrong.
- It is the known item: `coordinator-handoff.md:30` ("Cold/EV Portfolio rows 'No action agreed yet' against ST-4/5 'in hand'"), and R6 O5 already reports it ("Cold/EV 'No action agreed yet', reported"). BL-39 is a different item (the landing link).

**Ruling: a named COH-2 expectation, built the way COH-17's was. No product change now.**
- In `demo_combined_rows.coh_split`, a COH-2 finding is **allowed** only if all three hold:
  - its `site_code` is COLD-LAB-001 or EV-LAB-001;
  - its evidence files name `action_index.<that site>`, so the Action came from a domain index, never the estate index;
  - its subject is an Action id that `cold.json`/`ev.json` records (ACT-002/003).
- Reason text: "Portfolio does not join domain-Site Actions (estate/index.py:193); known, DS-1 covers it; BL-47".
- COH-2 on KOBO-001, or on any other Action, stays a fault. F-COH's output lists the allowed entries, one per estate window per Action.
- **L0:** the allowed case; Kobo COH-2 must fail; a Cold COH-2 whose Action came from the estate index must fail; an unknown Action id must fail.
- **Proof on P0:** commit, copy the changed tool files into P0's `tree/tools/`, and rerun only `check` in the tree form (§3). The pass condition: COH-2 is allowed on Cold and EV, and no new fault appears. Then the freeze applies.
- **BL-47 (new, free):** "The Portfolio joins Cold and EV domain Actions to their Finding rows (`select_action_scope` reads domain `action_index` for non-mini Sites), so a Cold/EV row reads 'Action agreed' as ST-4/5 do." Source: this ruling. Nothing shown is false without it: the row says no action is joined, and the story-day boards list the Action. Estimated 0.5. Not demo-critical. **No owner decision is needed.** The owner already holds this item on the walkthrough list. DS-1 keeps opening Cold and EV from the story-day links.

### 2. `tick --until-drained` with a high `mini_deferred`: covered, no change

- READ: `add-day --assess-now` on Kobo sets `assess: build` (`tools/demo_combined.py:710-711`) and runs `drain_mini()` before it returns (`:724-725`). The prepare runs `drain_mini()` before each drain (`:515`, `:546`). P0's past-2N failure came from `--no-finish`, which skips both. After `drain_mini`, P0 drained in one tick (MEASURED, relayed).
- **The drain does not call `drain_mini`.** The R8 drain is ruled as tick-only (R7 Q3), and the live path is already covered.
- **The DS-1 line gains one clause:** "Never run `tick --until-drained` after an add made without `--assess-now`." EX-1 measures the covered path.

### 3. Step 7 runs every served read in the tree form: confirmed, and it amends R6 §6

- `check` and every served read in step 7 (the after tool, `perf_budget --story`, the O8/O10/O11 reads) run the way `Demo.py` runs a child:
  - cwd `var/demo3_dd1b2/tree/backend/tests`;
  - `PYTHONPATH` set to the tree's nine parts (`demo_combined.py:297-299`);
  - `DATABASE_URL` set to the build's URL;
  - the tool path inside `tree/tools/`.
  
  The worktree form lacks `tree/var/sites/kobo-001.yaml` (copied at `:401-403`) and gives false 409s. This replaces "`python tools/demo_combined_finish.py check <url> <work>`" in R6 §6 step 7 and in the handoff.
- **A tool fixed in step 7** is committed in the worktree, then copied into `tree/tools/`. The packet names each copied file and its commit. Never copy backend code into the tree. A backend fault is an R6 §7 stop.

### Size and owner

§1 adds 0.05 (one pure function plus L0s). §2 and §3 add nothing. **DD-1b2b has 1.05 left; lane 2 has 2.05.** BL-47 is in the backlog and not counted. **Owner:** nothing new.

## DD1b2-R10: the rehearsal's 12 self-check failures, the recurrence result, and going on (Architect, Claude, 2026-11-07)

Binding checked: Claude (`.ai/ROLE_CONFIG.md:9`). Input: `.agent/DD-1b2b-rehearsal-handoff.md` (`716e86c3b`), `var/demo3_dd1b2/check.json`, the kept DB `assetops_demo3_dd1b2_test`. **MEASURED** = my own reads on the kept build: GETs in the tree form (R9 §3) and read-only SQL (`default_transaction_read_only`). Scripts and output are in the session scratchpad (`r10_reads*.py`, `r10_db.py`, `r10_out.json`). **READ** = code, cited. I ran no prepare, no build, no tick and no suite, and I wrote nothing to the DB.

### 0. Summary

**No row found a product fault that blocks the demo. Nothing needs a second prepare.** 11 of the 12 failures are our own rows. Ten assert things that were true before the CH-era product rules, or on the v2 day list. One reads a field the wire documents as empty. F-CAL is a crash. The v2 build (`AssetOpsV1-demo3/var/demo3_full`, code `e2df244c2`) passed the older rows. It predates CH-1a (24 h calendar grading), CH-3 (the one fully-checked-day rule), CH-5a1 (Site-local board day) and CH-6a3 (Grow figures come from the earnings claim), and its list had no night runs. P0 classed these rows as "absent data" from their error text without tracing them (`DD-1b2b-p0.json`, "not each traced"). That is why they show up only now. Two copy gaps a client can see go to the backlog (BL-48) with DS-1 lines. **The thread recurs** (§2), which matches R7's "Recurs" row, so it is not a stop.

### 1. Per row: cause and fix

Classes: (a) a check or tool fault; (b) a data or authoring fault; (c) a product fault; (d) a known or accepted gap.

| Row | Cause | Class | Fix (in `tools/demo_combined_finish.py` / `tools/demo_combined_rows.py`) |
|---|---|---|---|
| **F-COH** (4× COH-10) | MEASURED: the mill thread `6002bf66…` has two occurrences, OPP-000001 (10-17) and OPP-000002 (10-31), on one thread id. The served surfaces agree with each other. `build_expected_threads` lists only `mill.json`'s study (`demo_combined_rows.py:58-60`), so COH-10 expects 1 (`chain_coherence.py:826-836`). This is the recurrence R6 O4 anticipated, which our expectation did not carry | (a) | `build_expected_threads` takes the Kobo headroom opportunities **from stored rows, not served bodies**: every `mini_opportunity` of KOBO-001 whose latest `mini_opportunity_revision.result->>'eligible_days'` ≥ 1, ordered by `last_day`. `_coh` reads them with psycopg through `ctx.url`, as MILL-3 does. MEASURED now: {OPP-000001, OPP-000002} = 2, the served count. L0: no stored second study gives 1; a second study with eligible ≥ 1 gives 2; a study with 0 eligible is not added. **After the fix, if the stored count ≠ the served occurrences, or COH-10 fires: stop**, with no edit |
| **CO-5/SP-1** | S-28 = 10-08, a story-only run from 03:00 to 11:00Z on Kobo's 24 h calendar (CH-1a), so the reading is not complete. MG-2 is AT_MOST 0 with value 0. `judge` gives NOT_JUDGED without a complete window (`outcomes/objectives.py:119`), which maps to UNKNOWN / OBJECTIVE_NOT_JUDGED (`outcomes/status.py:96-97`). The row's no-Finding branch expects ON_TRACK, which held under the pre-CH rules (v2: OBJECTIVE_MET) | (a) | Restated (this ruling authorizes it). No-Finding branch: state ∈ {ON_TRACK, UNKNOWN}. Every UNKNOWN outcome must carry reason **OBJECTIVE_NOT_JUDGED**. PRODUCER_NOT_SETTLED, OBJECTIVES_NOT_READ or any other UNKNOWN reason **fails**. Record the outcomes. Shared pure helper `unknown_only_not_judged(outcomes)`, with a must-fail L0 on PRODUCER_NOT_SETTLED |
| **CO-5/SP-2** | Same rule. The Cold `normal` run is 16:00 to 17:05Z (days.json) on the 24 h calendar, so CC-1 and CC-6 are NOT_JUDGED. CC-5 has no declared objective, the same as v2 | (a) | Same helper: UNKNOWN only with OBJECTIVE_NOT_JUDGED; NO_OBJECTIVE only with NO_OBJECTIVE_DECLARED |
| **WK-4** | MEASURED on S: November 1-5 has 0 complete, 3 partial (11-02, 11-04, 11-05, all story-only 8 h runs) and 2 no-data days (11-01, 11-03). `judge_month` returns NOT_JUDGED with no checked day (`objectives.py:134`). The text is `MG1_NO_DAY` "sales not recorded" (`chain/vocabulary.py:268, 336-337`; ruled in CH6a2-R Q5). The row knows only "too early to judge" and on/behind pace | (a); the wording a client sees is BL-48 | Add a third branch, "no fully checked day this month": state UNKNOWN, `nodes.kpi.days.complete == 0`, and the line ends "sales not recorded". Everything else as now |
| **CO-6** | It fails at `demo_combined_finish.py:441`. The Kobo summary window starts `2026-11-04T21:00:00Z`, the Site-local midnight (CH-5a1 R6, local board day). The row compares it with UTC midnight `iso(S)`. Every assertion before `:441` passed | (a) | Compare with S's Site-local day start (`_kobo_zone`). The `cells == board` line after it has not yet run on this build; a failure there is classed at the rerun |
| **SP-4** | The finding index works on **UTC days** (`analytics/finding_index.py:235`). UTC 10-26 holds the 10-27 night run, which starts at 21:00Z, so it is CURRENT and not a gap. MEASURED: the served gap set (10-06, 10-07, 10-09..10-14, 11-01, 11-03, all NOT_CURRENT) is exactly the set of UTC days in [S-30, S+1) with no built run window. The chain grades local 10-26 NO_DATA. The board's local gap list includes S-10, and SP-3 passes. The v2 list had no night runs, so S-10 was a UTC gap there | (a) | Replace the S-10 assertion with: the served NOT_CURRENT gap days == `expected_index_gaps(days, lo, hi)`, a pure helper (the UTC days with no run `[start, end)` touching them). Keep "S-3 not a gap" and the Findings check. L0: v3-shaped days give the measured set; a missing day with no adjacent night run is a gap |
| **WK-1** | The EV fault run is 08:00 to 09:00Z (days.json), 1 h of the Tuesday 08:00-16:00 session. MEASURED: `charging_delivered` reads "Not known yet · 0 of 1 day checked · 1 with too little data, not counted", so there is no `headline_money` (CH-6a3 ONE-SOURCE). The headline still reads "estimated charging income", because `site_outcomes/ev.py:229` sets it from "tariff declared" alone | (a) for the row; the headline with no figure is a minor (c), BL-48 | Restated: when the earnings claim counts no checked day, `headline_money` is absent and the `charging_delivered` line starts "Not known yet". **Money shown on a day with too little data fails.** Report the headline as shown |
| **WK-2b** | The tool reads `grow["potential"]`, which is the top chip and is None on S. MEASURED: `grow["nodes"]["potential"]["text"]` = "No potential found yet". Every other WK-2b assertion holds on the measured row (no money; the headline is not the kW pattern; sales "0 kWh used by Grain mill in 8 measured hours") | (a) | `potential_text` reads `nodes.potential.text` first. L0 uses the measured row shape |
| **WK-2c** | Same field. The chip is `{"label": "Opportunity", "text": "Productive-use headroom"}`. MEASURED: `nodes.potential.text` equals `LIMITED_TEXT`, and `value`/`days_line` are null. The pinned study is LIMITED with 5 eligible days (SQL) | (a) | Take the sentence from `nodes.potential`, and apply the kW and money bars to **both** the node and the chip. L0 |
| **WK-6** | MEASURED: the S+1 Productive-use link covers 11-01T21Z..11-06T21Z, and the listing finds OPP-000004 (11-02..11-06). That passes. Then `day_rows[].mini_revision_id` is not on the wire: day rows now carry `hours[]` (mini-opportunity/2), and OPP-000001 also returns `[]`. The S+1 study has 0 eligible days anyway, because the v3 November days are 8 h runs | (a) | Restated. (1) Report the S+1 study: code, `eligible_days` (0) and status. (2) Run the tariff check on the **mill study** (`mill.json` `study.opportunity_id`): `eligible_days == 5`, `valid_at` = its `last_day` at Site-local 12:00, and the selection PRICED at 0.25 USD per kWh. The per-row pin is dropped |
| **F-CAL** | `demo_combined_finish.py:719`: `first` calls `at(d["start"])` for the `missing` day, whose start is null. The `built` set filters before it evaluates, so only `first` crashes | (a) | `first` skips days with no `start`. R8 B2's rule stands. **If a no-run local day before today reads anything other than NO_DATA: stop**, with no edit |
| **F-THREADS** | `:773` asserts that the chain Action's `verification` is VERIFIED. `chain/site_chain.py:126, 142` documents it as None for a domain intent. MEASURED: on ACT-000004 `verification` is null and `ref` is `DOMAIN_VERDICT`, which is correct (O1 works). The rest of the row has never run on this build | (a) | Assert `verification is None` on the chain wire, and that the DOMAIN_VERDICT page (`/api/sites/KOBO-001/domain-work/actions/{id}/verification`, MILL-3's read) reads VERIFIED. A further failure at the rerun is classed then. A board `read_state` or PRODUCER_NOT_SETTLED fault is product: **stop** |

**No row is edited to pass.** Every restatement keeps a must-fail case (an unsettled or failed read, money on a day with too little data, a stored-vs-served mismatch, a no-run day not reading NO_DATA).

### 2. The recurrence (R7's table, MEASURED)

| Study (SQL `mini_opportunity` + revision) | Window | Status | Eligible days |
|---|---|---|---|
| OPP-000001 (mill, pinned) | 10-17..10-21 | LIMITED | 5 |
| **OPP-000002, ends S-1** | 10-31..11-04 | UNKNOWN | **1** |
| OPP-000003, ends S | 11-01..11-05 | UNKNOWN | 0 |
| OPP-000004, ends S+1 | 11-02..11-06 | UNKNOWN | 0 |

Thread events: OPEN 10-17; ACTION_IN_HAND 10-26; CHANGE_APPLIED 10-27; RESOLVED_MONITORING 10-27; **RECURRED, effective 2026-10-31 (S-5)**, cause OCCURRENCE, from OPP-000002.

- **Result: Recurs** (R7, first row). The source is the S-1 study, and its effective day is after S-9 (10-27). The S-1 study is queued, so the "not queued" stop does not apply. The S-3 study (ending 11-02) is not queued, as R6 §1 predicted, and is reported only.
- Why: 10-31 is the only fully covered day in that window, and it still had spare midday solar after the change. R4's "about 22 after" says the same, and O14 measures it.
- Then: Q7's "recurs" column; the COH-17 entry is owed only if it fires; Portfolio Grow counts the mill thread as open; Assure is unchanged. O8 (4) and (5) confirm the last two at step 7. **The "Seen again" lines stay in DS-1.**

### 3. Go on with the kept DB: yes. No second prepare is needed.

The data is complete: both drains passed, the mill is VERIFIED 42.00 → 110.00, the wall time was 3585 s, and minimum free RAM was 3.07 GB. Every fix is in `tools/`. Order:

1. Fix the rows in §1, with L0s in `backend/tests/test_demo_combined_finish_rows.py` (scoped pytest of that file only). Commit with Write/Edit only.
2. Copy `tools/demo_combined_finish.py` and `tools/demo_combined_rows.py` into `var/demo3_dd1b2/tree/tools/`. The packet names both files and the commit.
3. Rerun `check` once in the tree form (R9 §3; about 12 min).
4. Then step 7's remaining reads (O8, O10, O11, O13-O17, the after tool), step 8 (clone + EX-1, after 11:00Z) and step 9, as R6, R7 and R8 have them.

**Stops back to me (DB kept):** any stop already named in §1; a COH finding other than COH-17 on the mill thread or R9's COH-2; a rerun failure that classes as product.

A second prepare would be needed only if a product fault needs backend code changed before the demo build. Nothing found here is one. Even then it would go to the owner first and would not happen in DD-1b2b.

### 4. Demo-critical vs backlog (SCOPE-1)

- **Demo-critical, in DD-1b2b now:** the §1 row fixes, because the self-check gates E3, and the DS-1 lines below.
- **BL-48 (new, next free).** "Grow lines with no fully checked day. (1) Kobo MG-1 at month start reads 'sales not recorded' when the month has no fully checked day (`vocabulary.py:268`). Say instead that no fully checked day this month is counted yet. (2) The EV Grow headline 'estimated charging income' shows when the tariff is declared but no figure can be shown (`ev.py:229`). Fall back to a no-figure headline." Source: this ruling. Nothing shown is false: the contributors say "Not known yet" and "0 kWh used". It is not demo-critical, because DS-1 covers it. Estimated 0.15. It is added to the owner's walkthrough list, and no decision is needed.
- **DS-1 lines (the coordinator carries them, +0):**
  - On S's Kobo board: "It's the start of a new month and none of November's example days is fully checked yet, so the monthly sales goal isn't judged yet."
  - On the Depot fault day: "Charging income isn't worked out for the fault day: too little charging data came in." **Do not say** a charging-income figure for that day.

### 5. Owner (information, no decision; R6 §5 and R7 triggers)

- B-16 is not triggered (3585 s of 10800). The low-memory line is not triggered (3.07 GB, never under 2 GB). The litre line (O15) is decided at step 7.
- Plain words: "The full rehearsal finished in about an hour of the three allowed, and memory stayed safe. The mill result reads as planned: target met, midday use up from 42 to 110 kWh a day. After the change, the system still saw spare solar on 31 October, so the solar opportunity now shows 'Seen again'. That is true on this example data: even with the mill at midday, some solar went unused. The 12 failed checks were our own checking scripts expecting older data or reading the wrong field. They are being fixed and rerun on the same build, so no second full run is needed. Two wording items are added to your walkthrough list: on 5 November the monthly sales line says 'sales not recorded' because no full November day is checked yet, and the Depot's income line on the fault day names an estimate it cannot show."

### 6. Size

Spent since R9: step 6 (0.25), R8's C1/C2/B/P0 (0.25) and R9 §1 (0.05). New here: the row fixes, L0s and one rerun, **+0.2**. **DD-1b2b has 0.7 left:** R10 fixes 0.2, the step-7 after tool and reads 0.25, step 8 0.1, step 9 0.15. **Lane 2 remaining: 0.7 + CH-5d1's 1.0 = 1.7.** BL-48 is in the backlog and not counted.

Process note: an "absent data" class given from error text alone hid ten stale rows until the one run. From now on, a P0-style partial build traces each excused row to a line before it is excused.

## DD1b2-R11: CO-2 at the rerun, EX-1's changed boards, and what is still owed (Architect, Claude, 2026-11-07)

Binding checked: Claude (`.ai/ROLE_CONFIG.md:9`). Input: `.agent/review-packet-DD-1b2b.md` (`70ddfa655`), `var/demo3_dd1b2/after.json`, `var/demo3_dd1b2c/ex1.json`, commits `8ae1d0814` and `411817ae8`. **MEASURED** = my own reads, with scripts in the session scratchpad (`r11_boards.py`, `r11_sum.py`, `r11_why_partial.py`, `r11_gate.py`, `r11_dump.py`, `r11_clone.py`, output `r11_dd1b2.json` / `r11_dd1b2c.json`). **READ** = code, cited. I ran no prepare, build, tick or suite, and I wrote no domain row. Disclosed writes: (1) my tree-form GETs on `dd1b2` and `dd1b2c` hit or stored `chain_response` rows (the response cache; a GET stores on a miss, `chain/response_store.py:183`), as R10's reads did; the diffs in §2 used `ASSETOPS_RESPONSE_STORE=compose`, which stores nothing. (2) A scratch clone `assetops_r11a_test` (TEMPLATE of `dd1b2`, no open sessions) took worktree-form reads and was then dropped.

### 1. CO-2: the build's age, confirmed. Under `serve` it should pass, but E3 measures that

- **Cause (READ, confirmed):** the overview reads STALE_PROJECTION when the schedule heartbeat is over 300 s old (`scheduling/health.py:48, 87, 98`). The heartbeat is written only when a tick completes (`scheduling/adapters/postgres_schedule_store.py:166`). Nothing has ticked `dd1b2` since the prepare. CO-2 passed in the rehearsal's own self-check, which runs right after the finish ticks. **It is not a product fault, and the row is not edited.** A CO-2 rerun is valid only within 5 minutes of a completed tick. The packet records the row as "passed at build; age-dependent at rerun".
- **Demo day (READ):** `serve` runs a schedule loop: tick, Performance comparison, pre-build, then 120 s of sleep, and it prints "ready:" after the first tick (`tools/demo_combined.py:20-22, 58, 800-808`). So a served demo DB is ticked continuously. **One open risk (computed, not measured):** the gap between two completed ticks is about tick + pre-build + 120 s. On the EX-1 logs that is about 85 + 105 + 120 = 310 s (`var/demo3_dd1b2c/logs/39-42`; the pre-build ran 15:45:04 → 15:46:49 local). That is just over the product's 300 s threshold, which assumes one-minute ticks (`health.py:48`). An idle loop tick is probably shorter, but nobody has measured it.
- **E3 step (new):** with `serve` running on the E3 build, read `/overview` `schedule.heartbeat_age_seconds` every 30 s for 15 minutes, including once during the live add and `tick --until-drained`, and rerun CO-2 once. **Pass:** the maximum age is ≤ 240 s and the overview never reads STALE_PROJECTION. **Otherwise:** set `TICK_EVERY_SECONDS = 60` in `tools/demo_combined.py` and remeasure. That is pre-authorised here: it is the demo loop's cadence, not a shown or measured value. In the same step, record whether `tick --until-drained` beside the serve loop hits a lock timeout (`lock_timeout_ms` 5000, `scheduling/run.py:88`). If it does, stop and bring it back to me, because the DS-1 add-day line would change.
- **DS-1 line (new):** "Start the demo with `serve` and wait for 'ready:'. Leave it running the whole time. If a Site page says its figures are being reassessed, wait about two minutes for the next update before showing it."

### 2. EX-1: "before" was a degraded read; the live add changes nothing on the S and S+1 boards

**Cause 1: the "before" read was not taken in the tree form (MEASURED).** I read the Kobo S and S+1 boards in the worktree form (cwd and `PYTHONPATH` in the worktree) on `assetops_r11a_test`, a fresh TEMPLATE clone of `dd1b2` with no add. EX-1's `summarise` gives exactly the `before` in `ex1.json`: `cost_lines` is `["ACT-001"]` (it is the Protect row's "Earlier" item), there are no Findings, Assure is UNKNOWN, and `read_state` is PARTIAL. In the tree form, the same data gives `read_state` AVAILABLE, the Finding on Cost and on Protect, and the trial line. So `demo_combined_ex1.py` read through a process whose backend composes over the worktree's own `var/` and not the build's (R9 §3's hazard), and `summarise` never checked `read_state`. The `after` read in the same process showed the full board. That is most likely a hit on the body that the tree-form pre-build stored after the tick (READ, `response_store.py:140-168`; not measured, and moot once the tool reads in the tree form).

**Cause 2: the clone's own S2 gate makes every clone board PARTIAL (MEASURED).** A fresh tree-form compose on `dd1b2c` fails one port, `source`, with `AwaitingComparison`: "The newest comparison record was made in another environment". The S2 comparison is bound to the database name and to the local store root (`evidence/legacy_comparison.py:83-103, 254-257`), and a TEMPLATE clone with a copied folder changes both. MEASURED with `r11_gate.py`: on `dd1b2`, the environment, the root and the legacy-inventory digest all match the report. On `dd1b2c` **after the add**, the digest is unchanged (`sha256:3e6ad354…`, an empty legacy set), but the environment and the root differ. **So the live add does not close the gate. The clone does.** On the demo DB, which the prepare compared itself (`demo_combined.py:541-543`), the gate stays open after a live add.

**Does the live add change the S/S+1 boards? No (MEASURED).** `dd1b2` (no add) and `dd1b2c` (add + tick), both composed fresh in the tree form: every item list (issues, in hand, earlier, options), every Finding id and every text are identical on S and S+1. Every difference in the diff comes from the `source` port failing on the clone: `read_state` PARTIAL, row reasons PRODUCER_NOT_SETTLED, states UNKNOWN, the Cost fuel line "Not known yet", and the readiness line "Not available yet · this record could not be loaded". **No new Finding, no changed Action words, no changed trial line, no changed Assure headline.** R6 O9's condition holds on content. Its proof, a valid before/after read on one clone, is owed (§4 B1).

**"Listed twice" is not a fault.** Finding `fcb15cac` is on Cost as the open primary signal, and on Protect as "Generator may have been on longer than needed · checked here as a safeguard". That is the must-not-harm listing CO-1 asserts. `summarise` collects across all rows, so the same id shows twice. The rehearsal DB shows the same pair with no add.

**Presenter-facing: acceptable**, with two script/E3 lines:
- **E3/E2 line (new):** "Present only from the database the prepare built, served from its own work folder. Never present from a TEMPLATE clone or a copied folder unless `python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001` is rerun there in the tree form. Otherwise every Kobo board reads 'could not be loaded' and Unknown." The same step goes first on E2's clone of the E3 build (R7 Q12), before `test_demo_combined_postgres`.
- **DS-1 add-day line (R6 §3), numbers filled in:** "…It takes about five minutes on the rehearsal machine (add about 65 s, tick until drained about 200 s)." The add changes nothing already on the story-day boards. The new day shows as its own day.

### 3. Item 3: owed, moved, dropped

| Item | Ruling | Reason |
|---|---|---|
| **O10** `delivered_days` on the real build | **Owed now** (B2) | A read of a few minutes. R6 replaced the seeded L2 with it. EX-1's add not being refused proves only half of it |
| **O13** "Target met" | **API stand-in now; browser moves to E3.** R7 Q11's stand-in is met by MILL-3 (VERIFIED 42.00 → 110.00) and F-THREADS (the DOMAIN_VERDICT page reads VERIFIED), both passing on the rerun. The packet names them as O13's stand-in. The screenshot of Work → Maintenance → the mill row → "Target met" is taken in the E3 dress rehearsal | The route and the page have their own vitest (`routeRefs`, `millVerification`). The browser adds proof of the click path only, and E3 walks it anyway |
| **O16** fuel-row trace, S-14/S-7 PRICED quantity 0, Cost headline on one `steady-before` and one `steady` day, WK-2a 42.08 | **Owed now** (B3), timeboxed to 0.1, stored rows plus one GET | Money is shown to clients (R8 kept it). A differing figure goes to the owner before E3 (R6 O16) |
| **O17** sampler during step 7 | **Dropped for step 7.** The rehearsal's minimum free RAM (3.07 GB) and wall time (3585 s) stand (R10 §5). Step 7 has no heavy job. E3 runs its own sampler | Nothing left to measure here |
| **Mutation proofs** on the restated rows | **Dropped as a separate step.** Each restated row has a must-fail L0 (21 passed, R10 §1's rule). The reviewer checks that each must-fail case exists and fails for the named reason | A second proof of the same thing |
| **O11** from the handoff | **Accepted**, but the packet cites the logs themselves (`var/demo3_dd1b2/logs/*-prebuild.log`) and their non-200 count, not the handoff | Evidence by path |
| **O15** litres | Closed as not recomputable (packet). The DS-1 generator line keeps "about 15 minutes" with no litre figure (R8 A). No owner line | No fuel signal on this Site |
| **O14** | Closed: "about 96 / about 22" may be quoted | Matches |
| **O18** | **Owed** (B4): it is not in the packet. Add `mill` 20 and `drain` 340 (drain-1 278.4 + drain-2 58.3 = 336.7, rounded up to 10 s) to `EXPECTED_SECONDS`, unchanged otherwise | R6 O18 |

### 4. Builder round before the review (Sonnet, about 0.2)

- **B1. EX-1 tool fix and one rerun.** In `tools/demo_combined_ex1.py`:
  - (a) Refuse to run unless `assetops_backend.__file__` resolves under `<work>/tree`. The docstring gives the tree-form command (R9 §3).
  - (b) Before the first read, run `python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001` as a tree-form child (the same `Demo.py` path the prepare uses), then assert that S's `read_state` is AVAILABLE. If it is not, stop.
  - (c) Compare the S and S+1 boards as their whole `rows` plus `read_state`, not by text filters. Findings are compared as a set per row.
  - (d) L0s: the guard refuses the worktree form; the compare flags a `read_state` change and a new item.
  - Rerun once on a fresh clone `assetops_demo3_dd1b2d_test` with `var/demo3_dd1b2d` (TEMPLATE of `dd1b2` with no open sessions, plus a folder copy), after 11:00Z.
  - **Pass:** both reads AVAILABLE; the rows identical. Record any difference, but it fails only on R6 O9's items (Assure count or headline, trial line, Action words, a new Finding). Record the add and tick seconds.
  - Then drop `dd1b2c` and `var/demo3_dd1b2c`. Put both EX-1 runs' `ex1.json` in `.agent/DD-1b2b-rehearsal.json`, the first marked "invalid read form (R11 §2)".
- **B2. O10** on `dd1b2`, read only, tree form. Pass as R6 O10.
- **B3. O16** on `dd1b2`, read only. Pass as R6 O16.
- **B4. O18** (§3). Commit.
- **B5. Packet update:** CO-2 per §1; EX-1 per §2 with the rerun; the §3 table; this ruling's lines. Write/Edit only, one commit. No tick on `dd1b2`.

**Then the fresh Opus review.** Not now: the review's main live-add claim needs B1's valid read, and B1-B4 are short. Keep `dd1b2` and `dd1b2d` until the verdict.

### 5. Backlog (SCOPE-1)

- **BL-49 (next free; BL-48 is R10's):** "Demo tooling: a `demo_combined.py clone` command that makes a TEMPLATE clone and its folder copy, then reruns the S2 comparison there, so a copied demo DB never reads 'could not be loaded' (`legacy_comparison.py:254-257`)." Not demo-critical: the E3 line forbids presenting from a copy, and B1 reruns the comparison by hand. 0.1 est.
- No product fault was found, so there is no product BL.

### 6. Owner (information, no decision)

"The rehearsal results hold up. Three practical points for demo day, no decision needed. (1) We must present from the demo build itself, not from a copy of it. A copy shows 'could not be loaded' on the Kobo pages, and the run sheet now says this. (2) The demo server keeps its regular update loop running while we present. Otherwise a Site page says its figures are being reassessed. We'll confirm the loop keeps up during the final dress rehearsal. (3) The live 'add a day' step takes about five minutes and changes nothing already shown on the story days."

### 7. Size

Spent since R10: the row fixes and rerun (0.2), the after tool and reads (0.2), step 8 (0.1) and the packet (0.05), 0.55 in all. New here: B1-B5, **+0.2**. **DD-1b2b has 0.35 left:** builder round 0.2, then the review and step-9 close 0.15. Its total is 2.25 + 0.05 + 0.2 + 0.2 = 2.7. **Lane 2 remaining: 0.35 + CH-5d1's 1.0 = 1.35.** BL-49 is in the backlog and not counted.

## DD1b2-R12: the second gate on a copy (Performance comparison), from R11 B1(b)'s stop (Architect, Claude, 2026-11-07)

Input: the coordinator's relay of the B1 stop. On `dd1b2d` the S2 comparison rerun PASSED (`var/demo3_dd1b2d/logs/36-ex1-s2-comparison.log`), but S still read PARTIAL. The ports `dispatch` and `chain_findings` failed with "performance gate closed: … made for another tenant or environment". Commits `6f7021d78`, `a749fa346`, `8f2e164d3`. **READ** = code, cited. I ran nothing. R11 §2 named only the S2 gate. The S2 failure hid this second gate, because the `source` port failed first.

**Gates bound to the environment (READ, complete list).** Only two places in non-test backend code call `environment_identity`: the S2 gate (`main.py:430-436` → `evidence/legacy_comparison.py:231-257`, bound to the DB name and the store root) and the Performance gate (`main.py:401-411` → `analytics/performance_comparison.py:219-252`, bound to tenant, DB name, model version and legacy-claims digest, and to the live lineage). `evidence_migration.py:125` and `performance_migration.py:59` are the two writers of those reports. Nothing else in the product compares a stored record with the active DB or store. Cached rows (`chain_response`) are keyed by watermark and `code_version`, not by environment. **So there is no third gate of this kind.** One related fact (READ, `performance_comparison.py:244-251`): the Performance gate also closes when a tick reselects revisions that the comparison classified ("rerun it"). That is why the prepare, `tick --until-drained` and the serve loop all run the Performance comparison after every tick (`tools/demo_combined.py:579-594`). The live-add path is already covered.

| Q | Ruling |
|---|---|
| **(a)** | **Yes.** The EX-1 pre-read step runs, as tree-form children through the same `Demo.py` path: (1) the S2 comparison (already built), then (2) `python -m assetops_backend.performance_migration run --tenant demo --site KOBO-001`. **Kobo only**, as the prepare does (`demo_combined.py:588`). The order is **S2 first, then Performance**, matching the prepare's order (S2 in `finish`, Performance after the ticks). Then assert that S reads AVAILABLE as before; if it does not, stop and report the failed ports. Add one line to the tool's docstring; no new L0 is needed beyond B1's (the call is a fixed child list). Commit before the retry |
| **(b)** | **Retry on `dd1b2d`.** The `chain_response` rows from the failed reads are keyed by the watermark W (DB watermark plus file-state term F, `response_store.py:117-131`). A new Performance report moves F (`demo_combined.py:580-581`), so those rows no longer match. The `before` read either composes fresh or hits only a body stored under the new W, and the AVAILABLE assert catches anything else. No add or tick has run on `dd1b2d`, so it is still a clean copy of `dd1b2` plus the two comparison reports. The packet declares those writes (two reports, plus the stale `chain_response` rows) |
| **(c)** | **Yes, the line changes.** It now reads: "Present only from the database the prepare built, served from its own work folder. On any TEMPLATE clone or copied folder, first run in the tree form `python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001`, then `python -m assetops_backend.performance_migration run --tenant demo --site KOBO-001`. Then check that the Kobo S board reads `read_state` AVAILABLE before using it. Otherwise every Kobo board reads 'could not be loaded' and Unknown." It applies to E2's copy of the E3 build too (R7 Q12). The DS-1 presenter lines do not change |
| **(d)** | **Right in substance; one wording fix.** Cite both gates: replace "(`evidence/legacy_comparison.py:254-257`)" with "(`evidence/legacy_comparison.py:254-257`; `analytics/performance_comparison.py:227-228`)", and make the parenthesis read "then reruns the S2 comparison and then the Performance comparison (Kobo) there, and checks that the Kobo board reads AVAILABLE". The source column gains "and DD1b2-R12". Still 0.1 est. |
| **(e)** | **Still 0.35.** The Performance rerun is one child call inside B1's 0.2. Lane 2 stays at 1.35 |

**Owner:** nothing new. R11 §6 item (1) already covers it, and the wording stays plain.

## DD1b2-R13: closing the DD-1b2b review (M1, M2, L1-L4) (Architect, Claude, 2026-11-07)

Binding checked: Claude (`.ai/ROLE_CONFIG.md:9`). Input: `.agent/review-DD-1b2b.md` (`851c94f3d`, verdict FIX), the packet, R6-R12. **READ** = code, cited. I ran nothing and wrote no DB row.

### 1. M1: the COH-17 allowance, narrowed to the real recurrence shape

**The reviewer's proposed key is wrong; the narrowing is right (READ).** The mill-recurrence COH-17 is not a Kobo-Site finding. It is the estate check L3, emitted with `site_code` None: "`{n}` distinct Verified threads in the table, claim `{m}`" (`tools/checks/chain_coherence.py:1282-1286`). The D14 precedent this ruling copies is exactly that shape: `site_code: null`, `window` week or month, `subject: "L3"` (`build-sheet-CH-6.md:1159-1162`). A `site_code == "KOBO-001"` key would never match it and would turn a true recurrence into a fault.

**Rule (`tools/demo_combined_rows.coh_split`).** A COH-17 finding is allowed **only if all** hold:
- `recurs` is True (R10 §2, stored rows);
- `site_code` is None, `window` ∈ {`week`, `month`}, `subject == "L3"`;
- `detail` parses as `"<n> distinct Verified threads in the table, claim <m>"` with `n - m == 1` (the one mill thread: its older row reads Verified, the claim reads RECURRED);
- at most **one** allowed COH-17 per window; a second on the same window is a fault.

An allowed entry carries `reason`: "mill recurrence: an older row reads Verified, the thread now reads RECURRED (CH6b3-R4)" and `owner`: "BL-07" (`:1559`). Everything else, including every "lacks … body" and "window is not the requested one" finding, is a fault.

**Must-fail L0s** in `backend/tests/test_demo_combined_finish_rows.py` (the allowed case first, then each fails):
1. allowed: L3, week, `n - m == 1`, recurs → allowed with the reason and owner;
2. recurs False, same finding;
3. L3 on window `S`;
4. L3 on week with `n - m == 2`;
5. site-less COH-17 subject `summary` ("a stamped bundle lacks the summary body");
6. site-less COH-17 subject `window` (the `/estate/chain` window fault);
7. COH-17 with `site_code` KOBO-001 (a V2 row) on week;
8. two L3 findings on month: the second is a fault.

No `check` rerun: `allowed_coh17` is `[]` on this build (`var/demo3_dd1b2/check.json`), so the stored F-COH result does not change. E3's self-check runs the narrowed rule.

### 2. M2: every owed item without a closure

The after tool is extended once (§5 B2). It runs read-only in the tree form (R9 §3), with `ASSETOPS_RESPONSE_STORE=compose` so the GETs store nothing (R11's method). E3 reruns the same tool on the E3 build at **E3.2** (§4), so each (i) below is checked again on the real build.

| Item | Decision | How, and pass |
|---|---|---|
| O8 clone half (2)-(5), S+2 | **(i) now, on `dd1b2d`** | The after tool with S+2 added to its day offsets: the study ending S+2 (queued, status, eligible), the mill thread's events, the Grow and Assure rows on S+2's board, the Portfolio week and month counts. **Pass:** R7's result is still "Recurs" from OPP-000002, no WITHDRAWN or CLOSED, no RECURRED effective on S+2, Assure unchanged, Portfolio Grow counts the mill thread open. Anything else comes back to me, because the DS-1 line "the add changes nothing already shown" depends on it |
| O8 (6), COH-17 after the S+2 add | **(ii) E3.3** | The post-add `check` rerun that R11 §1 already orders for CO-2. F-COH must pass under §1's rule |
| O12, the Grow contributor on S-8 and S-5 | **(i) now, on `dd1b2`** | Record the Kobo Grow row's `nodes` (potential text and every contributor text) on S-8 and S-5. **Pass:** the potential reads "No potential found yet" and a contributor shows spare solar seen. If not, R6 §4's L6 line comes back to me before DS-1 |
| O19, how E2 runs `test_demo_combined_postgres` | **Closed by this ruling** (statement, no read) | "E2 runs `test_demo_combined_postgres` on a TEMPLATE clone of the E3 build, with the DB named by env. On that clone it first runs R12 (c)'s two comparison reruns in the tree form and checks that the Kobo S board reads AVAILABLE. The env var and the fixture branch are written at E2, when they first run (DD1b2-R Q12)." The packet carries this text |
| F-THREADS: earnings recompute | **Closed by citation** | WK-2a 42.08 USD = 168.3 kWh × 0.25 (`check.json`; packet O16) |
| F-THREADS: ONE-SOURCE | **Closed by citation** for EV (WK-1, no money with no checked day, `check.json`); Kobo goes with the next row | |
| F-THREADS: "Why?" price line | **(i) now, on `dd1b2`** | Read the Kobo Grow "Why?" for the pinned mill study (S-11). Assert that any price shown equals the stored selection price (0.25 USD per kWh), and that any money shown equals kWh × price at 2 dp. If it shows no money (LIMITED), assert none and record it |
| F-THREADS: links with an explicit `known_at` | **(ii) E3.2** | Report only. The after tool lists them on the E3 build; the E3 packet carries the list |
| F-THREADS: Portfolio plain landing for Cold and EV | **(ii) E3.2** | Report only, stated in the E3 packet (DS-1 opens Cold and EV from the story-day links, R9 §1) |
| F-THREADS: Protect "Why?" names both Cold threads | **(i) now, on `dd1b2`** | Assert both Cold thread ids (`cold.json`) appear in the Cold Protect "Why?" on the window holding Cold's story days |
| F-THREADS: MG-2 line | **Closed by citation** | CO-5/SP-1 records the MG-2 outcome in `check.json` (R10 §1). The packet quotes that entry |
| F-THREADS: "Action agreed" on ACT-002/003 | **(i) now** | Assert from `check.json` F-THREADS `thread_states` (a file read): both `state_label`s read "Action agreed". If not: back to me |

Nothing is dropped.

### 3. L1-L4

| Finding | Decision |
|---|---|
| **L1** EX-1 verdict | **Fix now, no rerun.** `tools/demo_combined_ex1.py`: exit non-zero when `comparison.passes` is false or when any read is not AVAILABLE; read `counts`, not `count`; any change in an `in_hand` item is an Action-words failure. L0s: exit code on a failing compare; `counts` read from the measured row shape; an `in_hand` text change fails. The valid run's whole-row diff was empty, so its verdict stands |
| **L2** lineage | (a) **Fix now:** the packet names the after tool that ran as the tree copy that differs from `411817ae8` (top-level import, equivalent), and then the B2 rerun uses the committed file, copied. (b) **Fix now:** O16's reads move into the after tool as assertions (each fuel row's day is a story day; none on a `steady` or `steady-before` day; S-14 and S-7 PRICED with quantity 0). This also gives E3.2 the MONEY-B gate the review found missing. O10's output goes into `.agent/DD-1b2b-rehearsal.json` as recorded, and the packet says where the script ran. (c) **(ii) E3.5:** `perf_budget --story --report --runs 3 --record <path>` on the E3 build, naming each NOT MEASURED route. NOT MEASURED is never a pass |
| **L3** DS-1 carry | **DS-1 draws from the rulings.** The packet gets a short index only (§6), not the full lines |
| **L4** `domain_action_index` window | **Fix now, in the after tool:** read Cold's and EV's `domain_action_index` on the Site-local story day and on its week. Assert ≥ 1 row, with ACT-000002 on Cold and ACT-000003 on EV. The F-THREADS row is not changed |

No new backlog item. **BL-50 stays free.**

### 4. E3 steps named here (the E3 card collects them)

- **E3.2** After the E3 prepare and self-check: `tools/demo_combined_after.py` in the tree form on the E3 build. It carries R13 §2's (i) asserts, the O16 asserts, the L4 reads, the `known_at` list and the Cold/EV Portfolio landing statement.
- **E3.3** R11 §1's serve step (heartbeat, live add, `tick --until-drained`, lock timeout), then one tree-form `check` rerun after the add (CO-2 and post-add F-COH).
- **E3.4** O13's browser path: Work → Maintenance → the mill row → "Target met", 42 → 110 (R11 §3).
- **E3.5** `perf_budget --record`, with the NOT MEASURED routes named (L2 (c)).

### 5. Fix round (Sonnet builder, about 0.2)

- **B1.** M1 (§1) with its eight L0s.
- **B2.** `tools/demo_combined_after.py`: an S+2 offset option; O12's S-8 and S-5 Grow nodes; the "Why?" price line; the Protect Cold-threads assert; the ACT-002/003 assert; L4's reads; O16's asserts; the `known_at` list and the Cold/EV landing statement (report rows). L0s on the pure parts. Exit non-zero on any failed assert.
- **B3.** L1 with its L0s.
- **B4.** Commit. Copy the after tool into `var/demo3_dd1b2/tree/tools/` and `var/demo3_dd1b2d/tree/tools/`. Run it once on `dd1b2` and once on `dd1b2d` (S+2 mode), tree form, `ASSETOPS_RESPONSE_STORE=compose`. No tick, prepare, add-day or suite. Scoped pytest of the touched test files only. Any failed assert: **stop**, back to me with the output.
- **B5.** Packet: this ruling's table with each item's evidence path; L2 (a)'s note; O19's text; the MG-2 and earnings citations; §6's DS-1 index. Write/Edit only, `git add -f` the explicit paths, one commit.

**Then a Sonnet re-review of the named findings** (M1, M2, L1, L2, L4). M1's rule and the new asserts are code, so a coordinator check is not enough for them. After ACCEPT, drop `dd1b2` and `dd1b2d` and their folders (R6 §6 step 9).

### 6. The DS-1 source index (for L3; the packet copies this list)

DS-1 takes its lines from these sections, with the measured numbers already filled in there:
- **R6 §4:** the mill route; R4 "about 96 / about 22" (allowed, R11 §3 O14); L6, as worded unless R13 §2's O12 row sends it back; the generator line with "about 15 minutes" and no litre figure (R11 §3 O15); "Do not add a Cold or EV day live".
- **The add-day line:** R6 §3's replacement line, plus R9 §2's clause ("Never run `tick --until-drained` after an add made without `--assess-now`") and R11 §2's numbers (add about 65 s, tick until drained about 200 s; the add changes nothing already shown).
- **Q7's "recurs" lines:** the DS-1 block at `:1561-1564`; "Seen again" stays (R10 §2).
- **R10 §4:** the month-start MG-1 line and the Depot fault-day income line.
- **R11 §1:** the `serve` line.
- **R12 (c):** the copy line. It is an E2/E3 line, not a presenter line.

### 7. Size

The first review spent 0.1 of the 0.15. New: the fix round, **+0.2**, and a Sonnet re-review, **+0.05**. **DD-1b2b has 0.3 left:** fix round 0.2, re-review 0.05, close 0.05. Its total is 2.95. **Lane 2 remaining: 0.3 + CH-5d1's 1.0 = 1.3.**

**Owner:** nothing new. No decision is needed.

## DD1b2-R14: R13's two failed asserts on `dd1b2` (Architect, Claude, 2026-11-07)

Input: the coordinator's relay of the stop (`28bb723d0`; after tool exit 1, 8 pass, 2 fail). **MEASURED** = my own read-only probes on `dd1b2`, tree form, `ASSETOPS_RESPONSE_STORE=compose`, `default_transaction_read_only=on` (scratchpad `r14_cold.py`, `r14_cold2.py`, `r14_cold3.py`). **READ** = code, cited. I wrote nothing to any DB.

### 1. `o12_grow_nodes_S-5`: a wrong expectation (ours), not a product fault

- R6 O12 took "No potential found yet" from the **does-not-recur** column. R6's own table gives S-5 under **Recurs** as "Seen again, no kW figure (the study is UNKNOWN)" (`:1549`). The build recurs (R10 §2): OPP-000002 is UNKNOWN with 1 eligible day (10-31). Its other four days are 11-01 and 11-03 (no run) and 11-02 and 11-04 (8 h runs). So "Not judged yet: 4 of the 5 study days have no reading" is the expected UNKNOWN sentence.
- **Assert becomes:** S-8 is unchanged (it passed). S-5: the potential starts "Not judged yet", with no kW figure and no money (the WK-2c bars). Record the mill thread's `state_label` on S-5's board, report only.
- **DS-1 (replaces R6 §4's L6 line):**
  - **On 28 Oct (S-8):** "The day after the change, the mill is checked and working. Spare solar was still seen on the well-observed days; the opportunity's size isn't repeated while the change is being checked."
  - **On 31 Oct (S-5):** "From 31 October the system saw spare solar again, so the opportunity is open again. Only one of its five check days has full readings so far, so it isn't sized yet." Use "Seen again" only if S-5's recorded label shows it. **Do not say** a kW or money figure on S-5.
- **Not demo-critical as a product item.** No BL.

### 2. `cold_protect_why_names_both_threads`: a product gap (Why? visibility cutoff), not demo data

- **MEASURED.** Thread `b13f2110` (COLD_EXCURSION, Protect MOVES CC-1, OPEN) has one occurrence, Finding `08d87808`. Its `created_at` is 2026-11-05 17:10Z. Cold's resolved cutoff is the evidence end, 17:05Z: the Why? `window.known_at` reads 17:05Z on the run window, on S's Site-local day (11-04 21:00Z → 11-05 21:00Z) and on the week. On all three, the Protect "Why?" names `aacec8fa` (known since 11-02) and not `b13f2110`. Its text reads "Unknown · ACT-002 · Open · linked finding outside this view". The Site chain lists both threads. So the tool's window choice is not the cause.
- **READ, probable cause:** the board looks up threads with `known_at=cutoff, visible_at=<request known_at>`, which is "as known now" when the request gives none (`site_outcomes/read.py:455-457`, "R-1: request bounds visibility"). The Why? reads `threads_through(..., cutoff=cutoff)` on the board's resolved cutoff (`chain/why.py:282-285`). For Cold and EV, that cutoff is the evidence end (`board_cutoff`, `read.py:805-809`). A Finding assessed after its evidence ends is therefore missing from the Why? but present on the board and chain. This affects every Cold and EV Finding created after its window's last reading, not only this demo day. The fix slice confirms the cause before it changes anything.
- **Class:** (c), a product gap. **Not fixed in DD-1b2b.** It is a backend read path, so it is an R6 §7 class item, but it needs no data rebuild and blocks nothing in this slice.
- **BL-50 (new, next free):** "The Site 'Why?' sees the same threads as the board. `site_trace` uses the board's visibility (`visible_at` = the request's cutoff, else now) and not Cold/EV's evidence-end cutoff, so a Finding assessed after its evidence ends is named in the 'Why?' (`chain/why.py:282-285`; `site_outcomes/read.py:455-457`). Proof: the Cold failure day's Protect 'Why?' names both Cold threads." Source: DD1b2-R14. Est. 0.25. Not demo-critical: the board and the Action are right, and DS-1 does not open this panel (below). **Added to the owner's walkthrough list.**
- **Assert becomes:** on S's Site-local day, the Cold Protect "Why?" names `aacec8fa` (ACT-002's thread). That part fails if missing. Record whether `b13f2110` is named, with the text. A missing `b13f2110` is reported as "BL-50 known gap", not a failure. If BL-50 merges before E3, E3.2 asserts both again.
- **DS-1 (new):** "On the Cold Room, explain the failure from the day's board and its Action. Do not open the Protect 'Why?' on the failure day." Also: "If a client opens it, it names the earlier cooling problem and says a linked finding is outside the view: that's a known display gap; the board above is complete."

### 3. Builder interpretations

- **(a) Confirmed.** Grow `open_findings` 1 on week and month is the mill thread counted open. It is Kobo's only Grow thread.
- **(b) Confirmed.** R13 meant the threads that hold ACT-002 and ACT-003. Cold's second thread (`b13f2110`) has no Action, and "Open" is correct for it. Tighten if cheap: key the Cold check on the thread whose Action is ACT-000002.

### 4. Resume, size, owner

- **The builder resumes (Sonnet):**
  1. Amend the two asserts (§1, §2) with their L0s.
  2. Rerun the after tool once on `dd1b2`, then on `dd1b2d` in S+2 mode.
  3. Do B5. The packet adds R14's DS-1 lines and BL-50.
  4. Add BL-50 to `.agent/backlog-post-demo.md`.
  - Any new failed assert stops the round, as R13 set.
- **Then the Sonnet re-review** of R13's named findings plus R14's two asserts.
- **Size:** the fix round has spent about 0.15, and these probes cost 0.05. Left: the builder about 0.1, re-review 0.05, close 0.05. **DD-1b2b has 0.2 left; its total is 3.0. Lane 2 has 1.2 left.** BL-50 is not counted.
- **Owner (information, no decision; walkthrough list):**
  - "On the Cold Room's failure day, the 'Why?' panel for protecting the asset names the earlier cooling problem but not the new temperature problem from that afternoon. It says a linked finding is outside the view. The board itself shows both. It's a display gap; we'll fix it after the demo, and in the demo we explain the Cold Room from the board."
  - "On 31 October the solar opportunity shows as not yet sized, because only one of its five check days has full readings. The script now says exactly that."
