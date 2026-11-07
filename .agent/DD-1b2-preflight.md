# DD-1b2 pre-flight: drain, finish rows, mill Action, rehearsal (questions for the lane-2 Architect)

Branch `task/DD-1b2-finish-rehearsal`, from main `aaea00962`. No code written and nothing run on a database. "Read" means read from code, not run. Day lists marked "resolved" went through the real `resolve_story` and `plan_add_runs` offline.

**Bottom line: DD1b1-R Q5's mill step cannot be built as ruled.** Its three named clocks do not date a study, and its freeze cannot see any snapshot at a story clock. Q2, Q4 and Q5 need rulings before code. Q7 asks for a decided fallback, because the later headroom studies probably reopen the mill thread after "Target met".

## In one view

| Q | Subject | Recommendation |
|---|---|---|
| Q1 | Trimmed day list, DB, cap | Kobo 12 days, Cold 3, EV 2; cap 90 min |
| Q2 | **Blocker:** the study is not dated by the clocks ruled | (a) `COALESCE` seam, as `store.py:70-74` |
| Q3 | Which study; what if it is not SUPPORTED | S-15 to S-11; report its status, stop only if no thread |
| Q4 | **Blocker:** the sequence needs `drain_mini` first | children, drain_mini, a, mill, b/c/d, R8, then finish |
| Q5 | **Blocker:** freeze and evaluate see no snapshots at a story clock | (a) process-local reader without `known_at` |
| Q6 | Instants and record wording | Table below, in the story file |
| Q7 | Later studies write RECURRED after VERIFIED | Measure it; decided fallback now |
| Q8 | R8: N, the 8 stuck events, re-dirty after finish | N after the first tick; drain again before check |
| Q9 | F-COH and F-PERF cannot run as they stand on a fresh build | Generated threads; dates from `story.json` |
| Q10 | F-THREADS: days and fail/report split | Table below |
| Q11 | F-CAL's meaning | Rows per `measures_for`, every built local day |
| Q12 | How E2 runs `test_demo_combined_postgres` | Against the E3 build, on a clone |
| Q13 | EX-1 on a clone; add-day time of day | One script, on the trim now and the whole build at E3 |
| Q14 | Timing, memory, wall cap | Elapsed line per day; sampler; projection formula below |
| Q15 | Size | 2.25 → 2.75 if Q2(a) and Q9 stand |

## Blockers, as checked in code

- **B1, the Action is refused.** `_INSERT_OPPORTUNITY_REVISION` and `_INSERT_OPPORTUNITY_SELECTION` bind no timestamp (`mini_decisions/store.py:84-89,95-97`). `created_at` and `selected_at` are `clock_timestamp()` defaults (`0030_w4_mini_decisions.py:161,182`). `opportunity_revision_selected` needs both `<= command_now` (`work/adapters/postgres_domain_intent.py:120-128`). So at a story `command_now` it returns False and `create_action` refuses `DOMAIN_INTENT_LINK_INVALID` (`work/domain_intent.py:99-100`). `test_lease_clock` only moves the lease; `test_clock_override` only moves job `available_at` and the scan instant (`mini_decisions/worker.py:103,113-115`). There is no third worker clock (read). DD1b1-R Q5 item 3 and `DD-1b1-preflight.md:64-67` assumed otherwise.
- **B2, a wall-clock OPEN skips every mill cause.** OPEN's `cause_known_at` is the study's `created_at` (`chain/threads.py:213`). A non-occurrence cause known before the head is `BEFORE_HEAD` (`chain/lifecycle.py:261-265`). So the thread must open from the story-dated study, before any tick places a wall-clock one. Q2 and Q4 together solve this.
- **B3, a permanent SHORT plan.** Freeze reads `snapshots.latest(..., known_at=now)` (`actions/verification_families.py:145`), which filters `computed_at <= :k` (`chain/adapters/postgres_snapshot_store.py:109-112`). `computed_at` is wall time (`0043_chain_snapshots.py:50`). At a story clock every day reads NO_DATA, the plan freezes SHORT, and a frozen plan is never rebuilt (read). Evaluate has the same filter (read).
- **B4, the order.** The Kobo child builds no renewable heads or snapshots. `drain_mini` and the first tick do (`tools/demo_combined.py:473-474`). DD1b1-R Q5 item 2 has step `a` first, but nothing places `drain_mini` before it. The same tick runs the opportunity and `chain_threads` stages (`scheduling/tick.py:459,485`), so no tick may run before the mill step.

## Questions

### Q1. The trimmed list, DB and cap

SCOPE-1's "Kobo 7 days" cannot hold in a real parent prepare:
- `_trial` requires `trial-before` and `trial-after` (`tools/demo_combined.py:129`, `next()` with no default).
- MILL-3 needs S-13, S-12, S-11, S-9, S-8, S-6, S-5. That is already 7, so the minimum is 9.
- MONEY-B's PRICED-with-quantity-0 check needs S-14 and S-7, or it is vacuous.
- WK-2a's 42.08 USD needs S-1.

**Recommend Kobo 12 built days: S-14, S-13, S-12, S-11, S-9, S-8, S-7, S-6, S-5, S-1, S+0, S+1 (7 full, 5 story-only), plus the `missing` S-10 entry, which builds nothing; Cold all 3; EV S-7 and S+0.** Entries are unchanged from v3, no kind edited. This exact list resolved offline (32 runs), and its add-day plan gives `normal` on S+2. File: `.agent/DD-1b2-trim-days.json`, passed by `--days`.

**Rows expected to be excused (read; each must name its absent day, and only actual failures are listed in the packet):** CO-5/SP-1 (S-28), SP-4 (S-3), SP-5 (S-21). COH-10 member counts are in Q9. Anything else failing is a fault.

**DB:** `assetops_demo3_dd1b2_test` (the only form `DB_RE` allows), work `var/demo3_dd1b2`, dropped afterwards. **Clone (Q13):** `assetops_demo3_dd1b2c_test`. **Estimate:** the 10-day dry run took 1113 s (`DD-1a2-mill3-dry-run.json`), so about 45 min in all. **Cap: 90 min**, then stop and report. Machine idle, keep-awake on, one heavy job.

**The prepare's own cap may stop this run.** `cap` here is 2 × (30 + 110×12+60 + 300 + 200 + 90) = 4000 s, below the 90 min asked for, and neither the mill step nor the drain is in it. See Q14.

### Q2. **Blocker.** How the one study gets its story date

| | Change | For | Against |
|---|---|---|---|
| **(a) Recommended** | Optional `created_at`/`selected_at` binds, `COALESCE(:x, clock_timestamp())`, on root, revision and selection, set only through a store override behind `require_prepare_database` | The file's own precedent (`store.py:70-74,180`), the style of `test_recorded_clock_override`, L0-testable | Edits a product store; needs the unset proof |
| (b) | Process-local swap of the SQL constants in the mill step, with the instant inlined | No product file changes | Silently breaks if a constant changes; a literal in SQL |
| (c) | Date the Action at wall time | No seam | Refused by DD1b1-R Q5 and every cutoff |

If (a): L0 for unset parameters None and DB time, set refused outside prepare DBs; L2 on the mill fixture. Reads are unaffected. The depth head pins stay wall-clock (`mini_depth_selection.selected_at`), so a read with an explicit `known_at` before build time hides the head (`mini_decisions/opportunities.py:103-106`, read). Is that accepted as a declared build-time fact? **Recommend yes:** no story link passes such a `known_at`.

### Q3. Which study

- `enqueue_from_selections` would queue every later study at a past clock, since the scan has only a lower bound (`worker.py:156`). **Recommend** `reconcile` over one explicit window, then `run_pending(scan=False)` (`worker.py:164-183,265-272`, read).
- **Window: S-15 to S-11.** Five days ending on the last built day before S-9, because S-10 is `missing`.
- **Its status is unknown until run.** SUPPORTED needs no missing day (`mini_decisions/projection.py:202-219`), and S-14 is a story-only day. The trim also lacks S-15: `FULL_DAY_JOIN_UNMEASURED` refuses S-15 unless the chain from S-20 is built, which is 17 Kobo days (resolved). So on the rehearsal the study is at best UNKNOWN, and its full-build status is first seen at E3.
- `create_action` checks only the selected head, not the status (read). Placement needs `eligible_days >= 1` (`chain/threads.py:28,161-163`); without it the link stays PENDING_PLACEMENT and no lifecycle event exists.

**Recommend:** F-THREADS reports the pinned study's status and eligible days. It fails only on no thread. The rule is unchanged and no study is moved. **Ask:** is a mill Action from a non-SUPPORTED study acceptable if E3 shows that? ST-3's value line comes from "a supported study", which may be a different, later one. **Recommend:** yes, reported, and the owner told before E3 only if the board line reads differently from ST-3.

### Q4. **Blocker.** The sequence

Replaces the order in DD1b1-R4 §3 at the marked points:

1. Children: Kobo, Cold, EV.
2. **`drain_mini` (new here).**
3. `backfill --steps a`.
4. Mill step: study, Action, record, freeze, evaluate.
5. `backfill --steps b,c,d`.
6. R8 drain.
7. Objectives, S2 comparison, `drain_mini` again, `tick(2)`, **R8 drain again (Q8)**, self-check.
8. `Demo.add_day` on the clone (Q13).

**Risk:** S2 comparison now follows the first `drain_mini`. Today it precedes it (`demo_combined.py:468-473`). I have not traced whether the mini jobs read its result. **Recommend** accepting this and comparing Kobo rows through the finish rows; a changed row is a fault. A one-Site prepare keeps today's path: the mill step needs all three Sites.

### Q5. **Blocker.** Freeze and evaluate at a story clock

| | Change | For | Against |
|---|---|---|---|
| **(a) Recommended** | The tool passes a process-local reader that drops `known_at` through `VerificationPorts(snapshots=)` (`actions/composition.py:137-139`). No product edit | Candidates are bounded to days already ended at the clock, so the rows read are what the day holds; Q5 item 4's story times stand | Not an as-known read; disclosed in the tool and the packet |
| (b) | Story-date snapshot `computed_at` | A true as-known read | Touches the builder and every reader; a large change on a defended seam |
| (c) | Freeze and evaluate at wall time | No seam | `recorded_at` is build time; contradicts "in story time" |

**The tick's evaluator** would otherwise judge an undecided plan at wall time (`scheduling/stages.py:315-327`). The tool's stored outcome removes the plan from that list (read), so the stored outcome stays story-dated.

### Q6. Instants and wording

Required order: study known ≤ Action < COMPLETE `recorded_at` < outcome `recorded_at` (`chain/lifecycle_run.py:50-68`). `effective_day` is the local day of COMPLETE's `occurred_at` (`verification_families.py:142-143`). Evaluate needs `today` after S-5 local (`:289,334`).

| Step | Instant (UTC) | Local (+03) |
|---|---|---|
| Study: job, lease, created, selected | S-10 06:00 | S-10 09:00, after S-11 ended |
| Action `raised_at`, `recorded_at` | S-10 09:00 | S-10 12:00 |
| Request, record, assign, COMPLETE `occurred_at` | S-9 04:00, 04:30, 04:40, 05:00 | S-9 08:00 at the latest, before midday |
| Their `recorded_at` | S-9 05:10 onward, +1 s | |
| Case link, then freeze | S-9 05:20, 05:25 | |
| Evaluate, `today` = S-4 local | S-5 22:00 | S-4 01:00 |

**Conflict to rule:** the mill runs from 08:00 on S-9 (`kobo-mill-midday`), so COMPLETE at 08:00 reads "the change was made as the day began". Accepted? **Recommend yes.** `story_commands` is not reused, since it exits on this order by design (`tools/demo_story_clock.py:70-72`).

**Wording:** I found no story text for this record. The test fixture says title "Run the mill at midday", owner "Plant lead". **Recommend** those two, plus plain request and record text, under `kobo.mill` in `demo-combined-story-v1.json`, so `_resolve` resolves the instants. The code follows ACT-001/002/003, so ACT-000004 (read). Please confirm the words.

### Q7. RECURRED after "Target met": a fallback is needed now

`RECURS_FROM` includes RESOLVED_MONITORING (`chain/threads.py:34`). Placement writes RECURRED with no day check (`:220-221`). The tick's scan lower bound is wall now − 5 d (`worker.py:156`), so studies ending S-3 to S+1 are queued and share this one thread (`threads.py:175-176`). WK-2b says spare solar rides as a potential on S, so an eligible later study is likely. **Read, not run: after VERIFIED, the mill thread probably reads RECURRED on the first tick.** A client would see "Target met" on the Action and "happened again" on the thread. BL-07 only covers occurrences during the check.

- **(a) Recommended.** Keep what is measured, F-THREADS reports the thread's events, and the verdict and the Action line stay. The later sunny day with the mill idle really does have headroom. The script names it, and the owner is told before E3 if it fires.
- (b) A recurrence rule that compares study days with the effective day: a product change, new as-known semantics, fails SCOPE-1 at this stage.
- (c) Leave later studies unbuilt: removes ST-3's potential. Refused by me.

**Early close** is not expected: 7 clean COMPLETE days are needed (`config/chain/thread-lifecycle-v1.json:2`) and only S-8, S-6 and S-5 are after S-9 (read). F-THREADS reports it if it fires.

### Q8. R8 details

- **N.** Dirty rows are marked only when `consume('snapshots')` runs inside a tick (`chain/events.py:319-324`), so before the first tick the count is near 0 and R8's N undercounts. **Recommend:** tick once, then N = ceil((dirty + pending `snapshots` events)/200) + 2 ticks from there, fixed; past N is a prepare failure with counts. The L0 and L2 pin this.
- **Tick output.** The drain loop reads stdout and the return code itself, as `Demo.tick` uses `check=False` and truncates (`demo_combined.py:504-505`). Exit 1 on a FAILED Site stops the prepare. Counts come from `PostgresEventStore.pending` and `queued` (`chain/adapters/postgres_event_store.py:103,146`), with subscribed types from `load_event_register()`.
- **The 8 stuck events.** `DD-0c-probe-results.md:45` measured `snapshots` holding at 8 unconsumed events after every tick. Cause not found. R8 requires 0, so as written this may fail every prepare. **Recommend:** I diagnose it in the rehearsal and report. If they are by design (for example, past a consume bound), the Architect rules what "0 pending" counts. It is not filtered out by me.
- **Re-dirty.** Objectives, S2 comparison, Performance and the second `drain_mini` run after R8, so F-DRAIN could fail on what they add. **Recommend** the second R8 run in Q4 step 7; F-DRAIN reads after it.

### Q9. F-COH and F-PERF

- **F-COH.** `expected-threads.json` holds polish-build UUIDs, so a fresh build fails COH-10 on "no Portfolio row shows a Finding" (read, `chain_coherence.py:864-865,893-895`). **Recommend:** the row generates a threads file from the build's own `kobo.json`, `cold.json` and `ev.json`, and calls `check` with no `--expect`, as EX-2 says. On the trim, the member count falls with the absent days, derived from the day list rather than a literal. `expected-today.json`'s I-09 entries (`:6-21`, polish UUIDs) are not used; R6 is meant to clear them. A remaining COH-2/COH-3 finding is a fault unless it names a day absent from the trim. **This is the I-09 reconciliation; please confirm.** ACT-002 and ACT-003 "Action agreed" go in that generated file and in F-THREADS.
- **F-PERF.** `perf_budget.py` hardcodes 2026-10-27/31 URLs (`:37-44`, and `chain_perf_probe.py:35-42`), so on a fresh build it measures empty windows. **Recommend:** an optional date mapping from `<work>/story.json`, keeping the fixture path unchanged. Run from the private tree with `--report` and the default 3 runs. Its time goes in the projection. Expect some minutes (10 routes × 3 cold processes; not measured).

### Q10. F-THREADS

§A8 item 3 names mechanism days (D7-D13, EV D9), not B-22 days. **Recommended mapping:**

| Check | Board | Rule |
|---|---|---|
| Earnings, ONE-SOURCE, "Why?" price line | Kobo S-1, S-5; week S-6 to S+0; EV S+0 | Recompute Σ stored money, kWh × price; fail if unequal or null |
| SUPPORTED potential + money | Kobo S+0, S+1 | Report the state; recompute if present. Fail if none is SUPPORTED on **any** story day; on the trim, excused only if the failure names an absent day |
| MG-1 verdict + days read | Kobo S+0 | Recompute `judge_month`; report the days read and whether that is what the screen implies (DD1a2-R Q6) |
| MG-2 | Kobo S+0 MISSED/MET, S+1 | The "{lo}–{hi} L × {price}" line reproduces, or the Known-Deviation omission |
| MILL-3 | stored rows | 3 COMPLETE each side, `kobo-steady-day` in later run sets, VERIFIED, not SHORT, `origin_opportunity_id` set, CHANGE_APPLIED reached. Prepare fails otherwise |
| G1 | stored rows | The packet's accepted line (DD1a2-R2): reported, not re-gated |
| MONEY-B | stored rows | Each fuel row traces to a story-day Finding, none on a steady day; S-14, S-7 PRICED with quantity 0, reported; Cost headline on one `steady-before` and one `steady` day; WK-2a 42.08 |
| Every link | all `story_links` boards + bare Site boards, 3 Sites | Report each row's state; fail on PRODUCER_NOT_SETTLED or PARTIAL |
| Failed reads | Cold, EV day and week boards | `read_state` and the `Reads.call` hook name `domain_action_index`: fail |
| Plain landing | Portfolio's Cold, EV href | Stated: Finding present, Action absent, chain "Action agreed" |
| Walkthrough items | Portfolio Cold, EV week | Report "No action agreed yet" against ST-4/5; Protect "Why?" names both Cold threads; not a failure |

- **The hook misses** direct appends (`site_outcomes/mini.py:279,400`, `ev.py:157-158`) and stored-response hits (read). **Recommend** reading with stored responses off for this row if that switch exists; otherwise the limit is stated.
- **Cold residual (`review-CH-6b3.md`):** story links now open the whole UTC day (DD1b1-R2), so the local-midnight pair is unreached by any link. **Recommend:** report the bare-board and day states; judged here as closed unless a linked board fails. BL-37 stays.
- **Exact-window links:** I will list those the script follows from `story_links`. None today carry an exact Cold or EV event window (read); the plain landing is the one exception, recorded above.
- **Finish rows moved to the day window:** rows reading the Action use the day window; `Ctx.window` stays for rows that need the event, per R2. Each moved row is listed in the packet.

### Q11. F-CAL

**Recommend:** for every local day of a built entry, `site_day_snapshot` has one row per `measures_for(site type)` × subject (`chain/measures.py:72`), and grades are reported. A `missing` day (S-10) has NO_DATA rows, since rows exist from first evidence to today (read). Keyed on the Site-local day, not `days.json`'s UTC form. It does not assert a grade.

### Q12. E2 and `test_demo_combined_postgres`

The fixture calls `d.prepare()` and drops the DB and work folder (`:39-67`). That is a second B-22 build at about E3 cost, and there is no reuse switch.

- **(a) Recommended.** E2 runs against the E3 build's clone. A new env var names the DB and work folder, read rows run on it, and mutating rows run only on that clone. Costs a small fixture branch. **I cannot run it here** (barred), so it is stated, not proved.
- (b) Pin by `--days`: also needs `:185,:198` changed, with the excused rows from Q1. It proves less.

**Ask:** state it only, or also build the branch unrun? **Recommend** build it, marked not run; first run at E2.

### Q13. EX-1 and add-day

- DD1a2-R3 asks for a clone of the **whole** build, which this unit does not make. **Recommend** one script, `tools/demo_combined_ex1.py`: clone the DB and work folder, read the board, `Demo.add_day` KOBO-001 `normal`, tick, read again, compare Assure count, trial line, the Action's words and new Findings. Run on the trim's clone now, and at E3 on the whole build. The rehearsal's own `Demo.add_day` runs through this.
- **Time of day.** S = today − 2, so S+2 is today, and `add-day` refuses until that day's `normal` run has ended at 11:00Z (`DAY_NOT_IN_PAST`; ST-7; the end resolved offline, the refusal read). **Recommend:** a refusal for that reason is not a fault; the step reruns later on the same DB, and the packet says so.

### Q14. Timing, memory, wall cap

- **Per-Site-day.** Children print untimed lines (`demo_combined_kobo.py:424`, `_cold.py:222`, `_ev.py:312`). **Recommend** an elapsed field on those lines, carried into `manifest.json`. No behaviour change.
- **Projection (E3, B-22 sequential).** Measured seconds per **full** Kobo day × 13, per **story-only** Kobo day × 8, Cold and EV per-day figures × their v3 counts, plus mill, backfill, measured drain scaled by dirty rows, finish rows, F-PERF. Stated with its assumptions. Over 3 h: the B-16 projection goes to the owner before E3.
- **R11 check.** One 24 h Kobo day's consume against 50 % of `chain_snapshot_seconds`: BL-11 dropped the split, so tick JSON no longer shows `consume`. **Recommend:** read the `assetops.perf` line if it has it, else report "not measured".
- **Memory.** The floor is minimum **free RAM** ≥ 2 GB (`DD-1a1-preflight.md:35`). `psutil` is absent. **Recommend** a scratchpad sampler (not committed): every 30 s, free RAM, sum of python working sets, and `docker stats` for Postgres, with the container noted as shared.
- **Wall cap.** **Recommend** adding `mill` and `drain` to `EXPECTED_SECONDS`, using `MD-0`'s and this run's measured seconds after the rehearsal; the rehearsal itself passes a cap override of 5400 s. No numbers tuned to pass: the 3 h cap is the owner's.

### Q15. Size

2.25 assumed the Q5 seams existed. The extras are Q2's store seam and its proofs (+0.25) and Q9's generated threads and perf dates (+0.25). **Recommend 2.75.** SCOPE-1 reason: without them there is no mill Action and no honest F-COH or F-PERF on a fresh build. Backing it down is possible only by Q2(b).

## Consolidated checklist: everything owed to this unit

| # | Item | Source |
|---|---|---|
| 1 | R8 drain: backfill, tick to 0 dirty and 0 pending, stop past N with counts; L0 N formula; L2 stops at 0 and fails past N | `build-sheet-DD-1.md:43,121`, §3 |
| 2 | Finish rows F-DRAIN, F-COH, F-PERF, F-THREADS, F-COH3 (non-vacuous), F-CAL | R10, SCOPE-1 `:130` |
| 3 | M2 and F-FILL are backlogged: not built | SCOPE-1 `:130`, BL-10, BL-12 |
| 4 | F-THREADS addition: non-null earnings, SUPPORTED potential + money, MG-1 verdict, "Why?" price line; recomputed; ONE-SOURCE | SCOPE-1 `:131`, `build-sheet-CH-6.md:590` |
| 5 | MG-2 verdict and its line | Coordinator note `:462` |
| 6 | Each Grow value reproduces from its rows; MILL-3 in F-THREADS; G1 on the whole build | R12 `:565,569`, DD1a2-R `:880` |
| 7 | How many days MG-1 reads, and whether the screen implies it | DD1a2-R `:836` |
| 8 | MONEY-B, including S-14/S-7 PRICED quantity 0; Cost headline on one `steady-before` and one `steady` day; WK-2a; owner told before E3 if different | DD1a2-R2 `:961-965`, R3 `:1017` |
| 9 | How E2 runs `test_demo_combined_postgres` (state, do not run); finish rows it breaks | DD1a2-R2 `:972` |
| 10 | EX-1 board read after the live `normal` add, on a clone | DD1a2-R3 `:1003` |
| 11 | The mill Action step `tools/demo_combined_mill.py`, after all three children, after `a`, before `b,c,d`, one story-dated study, Action-first order | DD1b1-R Q5, `build-sheet-CH-9b.md:187` |
| 12 | Mill Action linked (`origin_opportunity_id`), ACTION_IN_HAND/CHANGE_APPLIED; prepare fails otherwise; plan not SHORT | CH9b1-R2 `:147`, CH9b2-R `:175` |
| 13 | `expected-threads.json` and F-THREADS: ACT-002, ACT-003 "Action agreed"; `expected-today.json` I-09; effects of story-dated Cold and EV rows; Protect "Why?" names both Cold threads | DD1b1-R `:1180` |
| 14 | Rows needing the Action read the day window | DD1b1-R2 §6 `:1278`, R3 §6 `:1394` |
| 15 | `domain_action_index` not a failed read on Cold and EV story-day and week boards | R3 §6 `:1395` |
| 16 | Exact-window links the script follows: listed, avoided or stated | R2 §6, R3 §6 `:1396` |
| 17 | COH rules on the new day windows reconciled with `expected-today.json` | R3 §6 `:1397` |
| 18 | F-THREADS records the Portfolio's plain landing for Cold and EV | DD1b1-R4 §1 `:1419` |
| 19 | One three-Site prepare with finish on, then Kobo `add_day`; excuses only for absent days, each listed | DD1b1-R4 §3 `:1435-1439` |
| 20 | Every `story_links` board + bare Site board, 3 Sites; fail on PRODUCER_NOT_SETTLED or PARTIAL; every shown Kobo row state | CH6b3-R2 `:1041`, R3 `:1138` |
| 21 | Report Cold and EV Portfolio "No action agreed yet" against ST-4/5 | CH6b3-R3 `:1128` |
| 22 | Judge the Cold failure-day "unsettled" residual | `review-CH-6b3.md:103`, BL-37 |
| 23 | Wall time per Site-day; projected B-22 E3 against 3 h; B-16 projection to the owner if over | R1, DD0c-R `:150`, DD1a2-R Q6 `:827` |
| 24 | Peak memory against the 2 GB floor | §2 P6 |
| 25 | One 24 h Kobo day's consume against 50 % of `chain_snapshot_seconds` | R11 |
| 26 | Scoped `tools/checks/test_chain_coherence.py`; guards A, W, N, V, M | `:121` |
| 27 | DD-1a2 packet item 5: the Finding revision count (3 vs 1), "if the Architect wants it pinned" | `review-packet-DD-1a2.md:44,53` |
| 28 | Add-day run (by construction until now) | DD1b1-R2 §5 `:1269`, packet `:31` |

**Dropped by ruling, not owed:** the EV "twice" item (DD1b1-R4 §3). **Owed elsewhere, not here:** DS-1's script lines; the end-game plan's E3 rerun reserve (R4 §3).

## Stop

Committed and stopped here for the Architect's rulings. No code before them.
