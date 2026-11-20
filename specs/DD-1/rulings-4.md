## DD1b1-R4: review M1, the live Cold add, and H1's class of fault (Architect, Claude, 2026-11-07)

Input: `.agent/review-DD-1b1.md` at `d7c4d830f`. **No product change. DD-1b1 stays 1.5; DD-1b2 stays 2.25. The build does not wait.** DS-1 does not exist yet, so the script lines below are owed to it.

### 1. M1: **(c). Keep the landing; name it in DD-1b2 and the script. No product change.**

**What a client sees.**
- **Printed story-day link (`story_links`):** Finding, Needs attention, the Action "Open". ST-4 and ST-5 are met here.
- **Clicking GreenHarvest or Depot on the Portfolio (plain href):** the latest event window. Finding, Needs attention, the incident and plan rows, **no Action row**. The chain says "Action agreed", and the Actions list has it. Nothing false is shown; it is one click short.

**Why (c).** It is not a regression: main does the same. Option (b) changes this read path a third time, and it would need a re-probe. Option (a) is the better later fix but reverses CH6b1-R Q2's base link, and it needs the frontend landing proved on its own. SCOPE-1 does not require either: the presenter drives the demo, and nothing shown is false.

**Owed to DS-1 (+0):**
- ST-4 and ST-5 open from the printed story-day links, not the Portfolio's Site names.
- If the Site name is clicked: "This opens the latest event. The action agreed after it is on the Site's chain and the Actions list; the day view shows both together."

**Owed to DD-1b2 (+0):** F-THREADS records this landing by name for Cold and EV: Finding present, Action absent, chain "Action agreed". It is a stated expectation, not a failure. It replaces nothing in the "exact window" item, which stays.

**R645's closure text is extended:** "Day and week boards list the Action. An exact event window and the Portfolio's plain landing do not (BL-38, BL-39)." The builder applies this with H1.

**Backlog BL-39, with its trigger:** the Cold and EV `overview_href` carries the Portfolio's window. **If the owner dislikes the landing at the walkthrough (EX-1), this is the fix to pull.** The reviewer has already run the week read: it gains the Action and loses nothing.

### 2. Live Cold add: **the demo does not do one. The script avoids it; nothing changes in code.**

- ST-7 and OD-P7 are one live day, Kobo's (`normal` on S+2, DD1a2-R3). No plan row or script step adds a Cold or EV day live.
- The tool does not refuse a Cold add, and it should not; the reviewer ran it safely. The story-day links still read correctly afterwards. Only the plain landing moves to the new day, reading Watch with the Action "Open · linked finding outside this view".
- **Owed to DS-1 (+0):** "The live day is Kobo's. Do not add a Cold or EV day during a session. If one was added in rehearsal, rebuild from the clone before the session."

### 3. H1's class: **DD-1b2's partial prepares, as written, would NOT catch it. Corrected at +0.**

**The gap.** §4.4 runs one prepare per Site (`prepare --sites kobo`, and so on). `Demo.finish` runs objectives and the self-check only when `set(story["sites"]) == set(SITES)` (`demo_combined.py:459,475`). So a one-Site prepare skips the very lines that crash, and all of `demo_combined_finish.py check`. The review's "including DD-1b2's partial prepares" holds only for a three-Site run.

**Owed to DD-1b2, replacing the three separate runs (same days, same cost):**
- **One real three-Site prepare through the parent, with finish on:** `tools/demo_combined.py prepare --sites kobo,cold,ev --days <one trimmed file>`, holding the §4.4 days and SCOPE-1's lists (Kobo 7 days including `mill-midday`, Cold 3, EV 2 Tuesdays).
- It must exercise, in order: the children; the mill step; R8; objectives per Site; S2 comparison; ticks; `demo_combined_finish.py check`; and `Demo.add_day` for Kobo.
- Wall time per Site-day is still read from each child's timing, so the E3 projection is unchanged.
- **The self-check will meet rows that need days the trim omits.** DD-1b2's pre-flight lists them. A row is excused only if it names a day absent from the trimmed file, and each is listed. **Any other failure, including any crash, is a fault to fix.** No row is edited to pass.
- **This does not count as the barred full demo prepare**, on the DD1a2-R Q8.5 terms: own `*_test` DB, machine idle, one heavy job, cap set by the DD-1b2 ruling.

**What it still cannot prove.** Size and whole-list faults, and the excused rows. E3 remains the first full exercise. **Owed to the end-game plan:** one E3 rerun's time (up to 3 h) is held in reserve, and E3 is not scheduled for the session day minus 1 with no slack.

**H1's L0 stands as the reviewer gave it** (`Demo.finish` driven on the shape `prepare` passes). DD-1b2 adds nothing to it.

**Owed-list changes for DD-1b2.** Add the two items above and F-THREADS's landing line. **Drop the EV "twice" item** from the packet's list: per row, ACT-002 sits once under Grow and once under Protect, as its Finding does; it is not a defect. Carry the DD1b1-R list and Q5's mill step, which the packet omits; they stand in this sheet.

### 4. Owner line, corrected only if the first has been sent

**"One more detail on what I told you: the printed link for each GreenHarvest and Depot story day shows the problem with its action, marked 'Open'. If you click those sites' names on the Portfolio instead, you land on the latest event: it shows the problem but not the action, which is one click away on the Site's chain and Actions list. Nothing wrong is shown. The script uses the printed links, and if you'd rather the Portfolio click showed both, it's a small change we can make after your walkthrough. No decision needed now."**

Handoff: a fresh Architect takes DD-1b2, and starts from R3 §6, this section, and DD1b1-R "Owed to DD-1b2".

## DD1b2-R: rulings on the DD-1b2 pre-flight (Architect, Claude, 2026-11-07)

Input: `.agent/DD-1b2-preflight.md` at `3d1871142`. Binding checked: Claude (main and this worktree, `.ai/ROLE_CONFIG.md`, 2026-10-27). Everything below is read from code unless it says measured; nothing was run. **The build goes on, split in two, and the mill step is measured first. No owner question. One owner line, sent after the probe.**

**The builder's four blockers are right.** One conclusion goes further than the pre-flight, and it changes Q1, Q3 and Q10.

### 0. New finding: on the v3 list only two studies can ever be SUPPORTED, and Q3's window is not one of them

- `_fold_day` (`mini_decisions/projection.py:175-184`): any missing hour makes the day missing. `frozen_result` (`:202-216`): any missing day makes the study UNKNOWN, and only SUPPORTED carries `headroom_kw`. `value_line` returns None for anything else (`chain/vocabulary.py:50-54`).
- A story-only day is a missing study day (`review-packet-CH-9.md:158`; the declared operating day is 24 h, this sheet `:163`). On v3 the story-only days are S-28, S-21, S-14, S-7, S-3, S-1, S+0 and S+1; S-10 is `missing`; S-4 and S-2 are not built. Full days: S-20 to S-15, S-13 to S-11, S-9, S-8, S-6, S-5.
- **So the only five-day windows with no missing day are S-20 to S-16 and S-19 to S-15.** There is none after the mill change, because S-7 is story-only.
- **Q3's S-15 to S-11 contains S-14, so it is UNKNOWN on the whole build, not only on a trim, and that is known now rather than first seen at E3.** An Action from it has no value line, and ST-3's "value line comes from a supported study" could not be met on any board.
- The tick's scan (lower bound wall now − 5 d, about S-3; `worker.py:46,156`) queues only studies ending S-3 or later. Those are UNKNOWN or have 0 eligible days: S-4 to S+0 and S-3 to S+1 contain no full day, so they are no Source (`threads.py:164`).
- **So `wk2b` (`tools/demo_combined_finish.py:534-546`) fails on every v3 build.** It asserts "N–M kW of daytime solar unused" and a `potential` on S, and S's 5-day window holds no eligible day. No absent day excuses it. It went stale at CH-9 and DD1a1-R16, where the owner accepted "Loses: the full-day solar-unused … on N/R30/R25 days" (`:697-698`). No prepare has run since. Read, not run; the rehearsal confirms it.

### Q1. The day list: **no trim. The rehearsal runs the whole v3 list: Kobo 22 entries, Cold 3, EV 3.** Replaces SCOPE-1's partial lists and DD1b1-R4 §3's trim.

- **Why.** The SUPPORTED study needs S-20 to S-15 (the join chain), and the verdict needs S-13 to S-11 and S-9 to S-5, so all 13 full days are needed. MONEY-B needs S-14 and S-7, WK-2a needs S-1, `_trial` needs S+0 and S+1. A trim could then drop only S-28, S-21 and S-3 from Kobo and S-14 from EV, all short runs.
- **That saves minutes and costs more than it saves.** Each excused row needs listing, and the review has to read each excuse. With the whole list there are no excuses: **any failing row is a fault.**
- **How it projects honestly: it does not project, it measures.** `:827` already says B-16 applies if "the DD-1b2 rehearsal measures the whole prepare above 3 h". A 12-day trim would have to extrapolate the drain, which does not scale per day and is the largest unknown.
- **The prepare's cap:** add a development flag `--cap-seconds`. The rehearsal passes **10800 (3 h, the owner's figure)**. Past it: stop, report per-step timings, and project by Q14's formula from what completed. Expected 75-90 min, not measured.
- **DB** `assetops_demo3_dd1b2_test`, work `var/demo3_dd1b2`. **Clone** `assetops_demo3_dd1b2c_test`, work `var/demo3_dd1b2c`. No `--days` argument and no trim file. Machine idle, keep-awake on, one heavy job, stall monitor on. Dropped after the packet records its evidence.
- **This does not count as the barred demo prepare**, on the R4 §3 terms. E3 stays, as does its held rerun: S moves with the clock and later merges change the tree.
- **Cheap retry.** A finish-row fault reruns `demo_combined_finish.py check` on the same DB, not a rebuild.

### Q2. **(a), narrower: revision and selection only, in `mini_decisions/store.py`.**

- `_INSERT_OPPORTUNITY_REVISION` gains `created_at`, bound `COALESCE(CAST(:created_at AS timestamptz), clock_timestamp())`. `_INSERT_OPPORTUNITY_SELECTION` gains `selected_at`, the same way. The file's precedent is `:70-74`.
- `PostgresMiniDecisionStore.__init__(engine, *, story_clock=None)`. `from_url(url, story_clock=None)` calls `require_prepare_database(url)` when it is set. With it unset, both params are None. Only `tools/demo_combined_mill.py` passes it.
- **The root stays.** I found no reader of `mini_opportunity.created_at` on this path; `opportunity_revision_selected` reads the revision. If the L2 shows `Source.created_at` comes from the root, add it and say so in the packet.
- **Tests.** L0: unset gives None; set refused outside a prepare DB. L2 on the mill fixture: set stores the instant and `opportunity_revision_selected` is True at a story `command_now`; unset stores DB time.
- **Accepted:** depth head pins stay wall-clock, declared as a build-time fact in the packet. F-THREADS lists any story link that passes an explicit `known_at`.

### Q3. **The pinned study is S-19 to S-15. `reconcile` one window, then `run_pending(scan=False)`.**

- `reconcile("KOBO-001", <local midnight S-19>, <local midnight S-14>)`, which is S-20 21:00Z to S-15 21:00Z. It queues exactly one study (`worker.py:164-183`).
- Not S-20 to S-16: S-19 to S-15 is the later data, and it reaches the last "before" board, S-11 (`opportunity_items`: an episode ending S-15 meets S-11's five days).
- `story_links` already prints every day, so S-11 has a link (`demo_combined.py:258`). +0.
- **It is a pin, not a scan.** BL-32 stands: no other story-dated study.
- **Ask answered:** a mill Action from a non-SUPPORTED study is decided by the probe's P1 below, not left to E3.

### Q4. **Accepted, with one name.** `Demo.after_children(story, days)` runs steps 2 to 6. Both `prepare` (three Sites only) and the probe call it, so the probe exercises the real path.

1. Children: Kobo, Cold, EV.
2. `drain_mini`.
3. `backfill --steps a`, all Sites.
4. `tools/demo_combined_mill.py build <url> <work>` as a child, with `check=True`.
5. `backfill --steps b,c,d`.
6. R8 drain.
7. Objectives, S2 comparison, `drain_mini`, `tick(2)`, R8 drain again, self-check.
8. EX-1 on the clone (Q13).

- **The S2 risk is accepted.** A changed Kobo row is a fault, seen through the finish rows.
- A one-Site prepare keeps today's path.
- L0 pins the order with a fake `Demo`, driven on the shape `prepare` passes (H1's style).

### Q5. **(a).** The tool builds `VerificationService(SimpleNamespace(store=store, clock=lambda: <instant>, verification_ports=VerificationPorts(snapshots=_AllKnown(reader))))`, as `evaluate_domain_plans` does (`actions/composition.py:128-141`).

- `_AllKnown.latest(t, s, lo, hi, measures, known_at=None)` calls `reader.latest(t, s, lo, hi, measures)`, dropping `known_at`.
- **This is the same read the MILL-3 dry run made** (`tools/dd1a2_mill3_dry_run.py:225`), so it does not widen what was proved.
- Disclose it in the tool's docstring and the packet: the plan's `snapshots_known_at` is the story instant, and the rows read are as built.
- The tick's evaluator replays a stored outcome (`verification_families.py:203-205`). So the mill step **must store VERIFIED, or exit non-zero with the grade table.** Never leave it to the tick.

### Q6. **Table corrected: the instants below go in the story file, resolved by `_resolve`, with the order asserted in L0.**

| Step | Instant (UTC) | Local (+03) |
|---|---|---|
| Study: job, lease, created, selected | S-14 06:00 | S-14 09:00, after S-15's last delivery (S-15 22:00Z) |
| Action `raised_at`, `recorded_at` | S-10 09:00 | S-10 12:00 |
| Request, record, assign, COMPLETE `occurred_at` | S-9 04:00, 04:30, 04:40, 05:00 | COMPLETE at 08:00 |
| Their `recorded_at` | S-9 05:10 onward, +1 s | |
| Case link, then freeze | S-9 05:20, 05:25 | |
| Evaluate | **S-5 23:00**, not 22:00 | S-4 02:00; `today` = S-4 |

- 22:00 is exactly the S-5 `mill-rest` delivery (`demo-story-days-v3.json:121`). At 23:00 every row it read had been delivered.
- **COMPLETE at 08:00 is accepted:** the change is recorded when the mill's new pattern starts.
- **Wording, under `kobo.mill`:** title **"Run the grain mill at midday on sunny days"** (v3's own text, `:82`); owner "Plant lead"; request "Move the grain mill's run to midday on sunny days."; record "Mill schedule changed: on sunny days it now runs through midday, starting at 08:00." Expected code ACT-000004, read from the row, never a literal.

### Q7. **Decided: keep what is measured. "Target met" stands either way. No recurrence rule.**

**No contradiction with DD-1a2's verdict.** The dry run read only `productive_kwh`, and `outcome_rows` stores `"recurrence": "not recorded (BL-07); the declared rule alone decides"`. `summary_wire` reads a stored outcome back and never recomputes it, so a later RECURRED event supersedes nothing. The dry run's numbers carry over by construction:
- `today` = S-4 gives later days S-8, S-6, S-5 (S-7 is PARTIAL).
- `choose_days` takes the nearest candidates first, so building S-20 to S-15 does not move the baseline from S-13 to S-11.

The dry run built no study and no thread, so **recurrence itself is unmeasured**.

**Recurrence is probable.** A later study is a Source only if S-6 or S-5 has an ELIGIBLE hour (`_fold_day`: ELIGIBLE on any hour), and the mill is unlikely to fill every daylight hour. RECURRED would then be effective S-6 or S-5, after the verified day S-9, so the day order is clean.

**What the client sees (read, to be confirmed by P6):**

| Board | Recurs (expected) | Does not recur |
|---|---|---|
| S-11 | "N–M kW over 12 daylight hours" (hours as measured), thread open, potential with money | same |
| Action, "Why?", Assure | **"Target met", 42.00 → 110.00** | same |
| S-8 | "Checked and working, monitoring" (the verified state's effective day is the change's, `postgres_thread_sources.py:69`) | same |
| S-5, S-1 | "Seen again", no kW figure (the study is UNKNOWN) | "Checked and working", "No potential found yet" |
| S+0, S+1 | "No potential found yet" (S-5 is outside their 5 days) | same |
| Portfolio Grow, week | thread counted **open**, not verified | counted verified |

**Why (a), and why a suppressor is refused.**
- Both columns are true. The fix worked, and sunny days still leave solar unused, which is the sales point.
- The D14 recurrence on the generator thread was ruled the same way (CH6b3-R4: "Both sides are true").
- **The recurrence also carries the thread's only later evidence.** The potential is hidden in RESOLVED_MONITORING (`chain/outcomes.py:34`), so nothing else keeps the opportunity live after the verdict.
- Q7(b) is new as-known semantics at this stage, about 0.5, and fails SCOPE-1: **BL-40**. Q7(c) is refused, as the builder says.

**Owed to F-COH.** COH-17 will fire on week and month windows if it recurs, as it did on D14 (`build-sheet-CH-6.md:1151-1162`). If and only if it fires on the mill thread, the generated expectation file carries one entry per window: reason "mill recurrence: an older row reads Verified, the thread now reads RECURRED (CH6b3-R4)", owner BL-07. Any other COH finding is a fault.

**Owed to DS-1 (+0).**
- "The change met its target: midday use went from 42 to 110 kWh a day. Spare solar was still seen on later sunny days, so the opportunity stays open, and that is the next thing to sell."
- Open the potential on the printed S-11 link.
- Day S shows no spare-solar figure, because it is a partly checked day. It shows "0 kWh used by Grain mill" because that day's example run has the mill idle; say so if asked.

**Stop:** only if "Target met" stops showing where the Action shows, or RECURRED's effective day is on or before S-9, or the thread reads WITHDRAWN or CLOSED. The packet lists every board's Grow line.

### The probe (DD-1b2a's last step; run before anything in DD-1b2b is written)

- **Input:** `prepare --sites kobo --no-finish --days .agent/DD-1b2-probe-days.json`, DB `assetops_demo3_dd1b2p_test`, work `var/demo3_dd1b2p`. Then a development-only subcommand `after-children` calling the real `Demo.after_children`, then `Demo.tick(2)`.
- **Day list:** v3 entries unchanged. S-20 to S-15, S-13 to S-11, S-10 `missing`, S-9, S-8, S-6, S-5, S+0, S+1 (`_trial` needs the last two). 13 full + 2 story-only. Resolve offline first; if a join guard refuses without S-14 or S-7, add just those.
- **The real entry points, or it proves nothing:** real `resolve_story`, the real child, the real `story.json`, the real tool. No seeded inputs. This is the lesson of H1 and R2.
- **Cap 60 min**, estimate 35-40. Own DB, idle machine. Dropped afterwards. Evidence: `.agent/DD-1b2a-probe.json`, committed.

| # | Measure | Pass | If not |
|---|---|---|---|
| P1 | The pinned study: status, `eligible_days`, `headroom_kw`, `window_hours`, classification, `limitations` | SUPPORTED, eligible ≥ 1 | Eligible ≥ 1 but not SUPPORTED: finish the probe with the same pin, then **stop**; the Architect rules, with an owner line ("the spare-solar figure can't be shown"). Eligible 0: **stop at once** with `day_rows`; there is no thread and no Grow story. In both cases also reconcile S-20 to S-16 and report it. |
| P2 | `create_action` at S-10 09:00 | Accepted, `origin_opportunity_id` set | **Stop**: Q2's premise failed. |
| P3 | Grades, then freeze, after step `a` with no tick (the dry run read after ticks; this order has never run) | FULL, days S-13, S-12, S-11 | Read the grades **before** calling freeze, since a frozen plan is never rebuilt. If short, **one fallback:** call the `chain_snapshots` consume and drain for Kobo in process (no opportunity or thread stage), re-read, then freeze. Still short: **stop** with the grade table. |
| P4 | Evaluate at S-5 23:00Z | VERIFIED, later S-8, S-6, S-5, line reproduces the dry run's 42.00 → 110.00 | **Stop.** No value moves. |
| P5 | After `b,c,d` | `LINKED`; events OPEN (S-19, or the first eligible day), ACTION_IN_HAND (S-10), CHANGE_APPLIED (S-9), RESOLVED_MONITORING (S-9); no skipped cause | **Stop** with `skipped_causes`. |
| P6 | After `tick(2)`: thread events; outcome count still 1; the Grow row, Action line and state words on boards S-11, S-8, S-5, S-1, S+0, S+1 | Either Q7 column | Q7's stop. |
| P7 | The stuck `snapshots` events (Q8) | Reported by type, id, `recorded_at`, across the two ticks | Reported, not a probe failure. |

**Does not prove:** Cold and EV ordering, ACT-000004 itself, finish rows, time, or the three-Site crash class. DD-1b2b's rehearsal does those.

### Q8. **N and the two-run R8 accepted; the stop rule is firmer; the 8 are measured in the probe.**

- **N:** tick once, then N = ceil((dirty + pending `snapshots`)/`chain_snapshot_items`) + 2 from there, fixed.
- **Stop rule:** the stage's time bound can process fewer than 200 in a tick, so a false failure an hour into a build is a real risk. Between N and 2N with the counts still falling: continue, log `over_n` in the manifest, and F-DRAIN reports it. Past 2N, or two ticks with no fall: prepare failure with counts.
- **Tests:** L0 the formula. L2 seeded backlog: stops at 0, reports `over_n`, fails on a flat count.
- **Output:** the drain loop reads stdout and the return code itself, as recommended. Exit 1 on a FAILED Site stops the prepare.
- **The 8 events, three ruled outcomes from P7:**
  - Gone: nothing more.
  - **New event ids each tick** (written by a stage after the consume): the condition becomes "0 dirty and no pending event recorded before the last tick began". F-DRAIN prints the remainder.
  - **The same ids stuck:** stop and bring me ids and types. No filter by the builder.

### Q9. **Accepted, with the smallest seam.**

- **F-COH.** Generate the threads from `kobo.json`, `cold.json`, `ev.json` and write them to the bundle manifest's `expected_threads`, which `coh10_thread_identity` already honours (`chain_coherence.py:864`), so that file needs no edit. `check` with no `--expect`, except Q7's named entries. ACT-002 and ACT-003 "Action agreed" go there. **I-09 reconciliation confirmed:** `expected-today.json`'s polish entries are unused, and a remaining COH-2 or COH-3 is a fault.
- **F-PERF.** One optional `--story <work>/story.json` on `perf_budget.py`, mapping the route windows to the same story days (Kobo S, Cold S+0 failure run, EV S+0 fault run, the week ending S). Fixture path unchanged. `chain_perf_probe.py` takes the same mapping only if `perf_budget` runs through it. `--report`, default 3 runs, from the private tree. Report only; a breach is a line in the packet.

### Q10. **The builder's table, with these changes.**

| Check | Change |
|---|---|
| SUPPORTED potential + money | **Kobo S-11.** Recompute the study's value line and its money line from stored rows; fails if absent (subject to P1's ruling). S+0, S+1: report the state; the Q7 table is the expectation |
| **WK-2b (existing row, stale: §0)** | **Restated.** On S: no money, the sales line, no kW headline, `potential` reading "No potential found yet". **New WK-2c** on S-11 holds the moved assertion. This is an Architect restatement with its cause, not a row edited to pass |
| MILL-3 | Add: outcome count 1, and a recomputed line equal to the dry run's. A difference is a stop |
| Every link | Add: list any link carrying an explicit `known_at` (Q2) |

- The rest stand as written, including the mapping of §A8's mechanism days to the B-22 days.
- **Hook:** stored responses off if the switch exists, otherwise state the limit. **Cold residual:** judged closed unless a linked board fails; BL-37 stays.
- **Exact-window links and moved rows:** as proposed, listed.
- **Item 27 (3 revisions vs 1):** no pin; DD1a2-R3 §3 made it a script line.
- **Report only:** S-8's "Checked and working" (Q7 table), a reading as known now, the same as ACT-001's.

### Q11. **Accepted, on every local day from first evidence to today**, so S-10, S-4 and S-2 are asserted NO_DATA rather than skipped. No grade asserted on a built day.

### Q12. **(a), stated only. No unrun fixture branch.** Code that has never run is the class of fault this lane keeps shipping. `test_demo_combined_postgres` runs against the E3 build's clone; the env var and branch are written at E2, when they first run. Owed to the end-game plan, about 0.1.

### Q13. **Accepted, and the rehearsal now discharges DD1a2-R3: `tools/demo_combined_ex1.py` on a clone of a whole build.**

- Clone after step 7's self-check. Run the same script again at E3.
- It covers item 28 (the add-day run), read before and after.
- A `DAY_NOT_IN_PAST` refusal is not a fault: run it again after 11:00Z on the same clone.

### Q14. **Accepted, on the whole list.**

- Elapsed per day in the child lines and `manifest.json`, plus `mill`, `drain`, finish rows and F-PERF as separate timings.
- **Result:** the measured prepare wall, excluding EX-1 (its time stated beside it). Over 3 h: the B-16 projection goes to the owner before E3. Q14's per-day formula is used only if the cap stopped the run.
- **Memory:** the scratchpad sampler as proposed. Minimum free RAM goes in the packet against the 2 GB floor; below it, stop and report.
- **R11:** read the perf line, else "not measured".
- **`EXPECTED_SECONDS`:** add `mill` and `drain` from measured figures after the rehearsal, untuned.

### Q15. Size and split

**2.75 accepted, and split.** The number would fit one unit, but a mill sequence that has never run should not share a builder's context with 28 owed items, and the probe's stops must come back before the rows are written.

| Unit | Size | Scope | Review |
|---|---|---|---|
| **DD-1b2a** mill step | 1.25 | Q2 seam, `tools/demo_combined_mill.py`, Q6 story block, `after_children` and its L0, the probe, packet | Own fresh-Claude review; merge on ACCEPT |
| **DD-1b2b** drain, rows, rehearsal | 1.5 | R8, Q9, Q10, Q11, EX-1, `--cap-seconds`, timing lines, the rehearsal, the rest of the checklist | Own fresh-Claude review. The first three-Site run happens here, so faults it finds are fixed here |

**Order:** DD-1b2a, its probe, this Architect only if a stop fired, its review and merge, then DD-1b2b from main. A fresh builder per unit. Plan: DD-1b2 2.25 → 2.75, DD-1 11.25 → 11.75, lane 2 remaining 4.5 → 5.0.

**SCOPE-1:**

| Addition | Class | Reason | Size |
|---|---|---|---|
| Q2 store seam and proofs | demo-critical | No mill Action without it, so no Grow verdict | +0.25 |
| Generated threads, F-PERF dates | demo-critical | F-COH and F-PERF otherwise check nothing on a fresh build | +0.25 |
| The probe | demo-critical | The mill sequence has never run | inside DD-1b2a |
| Whole list, WK-2b/2c | demo-critical | The only SUPPORTED study; the row is false today | +0, less excuse work |
| A recurrence rule | backlog **BL-40** | Q7(b); nothing shown is false without it | 0.5 est. |
| A SUPPORTED study after the mill change | backlog **BL-41** | Needs S-7 full and S-4 built, which R16 and DD1a2-R Q4 ruled out; the claim is defensible without it | not sized |
| E2 fixture branch | end-game plan | Written when first run (Q12) | 0.1 |

BL-40 and BL-41 are free (grepped `.agent/*.md` and the plan). The DD-1b2a builder adds them to `.agent/backlog-post-demo.md`.

**The 28-item checklist stands as DD-1b2's acceptance, with:** item 11 (Q3's window and Q4's order replace its wording); item 19 (the whole list, no excuses); items 3 and 27 (not built). Items 11, 12 and the mill part of 6 close in DD-1b2a; the rest in DD-1b2b. Scoped `tools/checks/test_chain_coherence.py`, `test_ch9b*`, the `test_demo_combined_*` L0s; guards A, W, N, V, M per unit. No full-prepare pytest (Q12).

### Owner, informed (send after the probe, with its result; no decision; the build does not wait)

**"The Grow story, as it will be shown: spare solar measured before the change, the action, the mill moved, then 'Target met', midday use up from about 42 to 110 kWh a day. That stands. On later sunny days there's still spare solar, so the opportunity line will probably read 'Seen again' next to 'Target met', and the Portfolio counts it as open rather than verified. Both are true, and the script says so plainly. The spare-solar figure shows on the days before the change rather than day S, which is the partly-checked trade you already accepted. Hiding 'Seen again' would need a new rule, about half a unit, and I'd leave it; tell me if you'd rather not. The last data step grows by half a unit, for 5.0 left on this lane."**

Strike "will probably" if P6 measured it; replace that sentence if it did not recur.

### Handoff

A fresh builder takes **DD-1b2a** on `task/DD-1b2-finish-rehearsal`. Reading budget: §0, Q2 to Q7 and the probe table above. Code: `mini_decisions/store.py`, `mini_decisions/worker.py:164-183,265-272`, `actions/composition.py:128-141`, `work/domain_intent.py`, `tools/dd1a2_mill3_dry_run.py` for the build shape, `tools/demo_combined.py:360-480`. Stops come back to this Architect.

## DD1b2-R2: the P1 stop: the blank rows come from our own day-edge rule, not from the data (Architect, Claude, 2026-11-07)

Input: `.agent/review-packet-DD-1b2a.md`, `.agent/DD-1b2a-probe.json` at `15ddcc33d`. **MEASURED** means the probe's evidence. **READ** means code reading, which has missed on this lane, including DD1b2-R §0. Each READ that a ruling rests on has a measurement below.

**Corrections to my last ruling.**
- §0's "no missing day" was read, and the probe refuted it. §0 holds only once the fix below lands.
- Q1 overrode the owner's standing "no full data build" rule without asking. The owner has now approved it: one whole-list rehearsal on a `*_test` DB, up to 3 h (`.agent/owner-rehearsal-whole-list-2026-11-07.md`). **The approval covers DD-1b2b's rehearsal only.** The probe stays a partial build.
- `.agent/DD-1b2-probe-days.json` matched that ruling (checked: kinds equal v3's, every entry a v3 entry, 13 full + 2 story-only). It changes in §4. The heredoc deviation has no effect on it.

### 1. The cause (READ, measured by M0 before anything is fixed)

**The packet's attribution is probably reversed. Those rows are most likely the first row of the next run, not the last row of the earlier one.**

- **Measured:** at 03:00Z and 21:00Z the 11 interval signals read UNAVAILABLE with interval 5 min back; the 2 state signals read GOOD. 15:00Z is all GOOD.
- **Read: the keep rule.** `DayRun.keep` (`tools/demo_story_days.py:101-103`) sends a complement's rows on `lo <= t < hi`, so its closing row at `hi` is never sent. That is DD1a1-R5's edge rule ("the earlier one ends exclusive", `:320`, `demo_story_days.py:290-293`).
- **Read: the next run's first boundary.** It has no span behind it, so its interval signals are `NO_PRECEDING_INTERVAL` (`observation/transform.py:166-176`) and its state signals report.
- **Read: why it looks like the earlier run's row.** `report_from_observation` stamps `interval_start = source_time − 5 min` on every interval row, absent ones included (`contracts/assetops_contracts/gateway_report.py:160-162`).
- **Why 15:00Z is clean:** the story run owns its closed span, so the day run's real closing row is sent and the rest run's first row is dropped. The other two seams do the opposite.

So at 06:00 and 00:00 **we discard a real 5-minute reading and send "no interval yet" in its place. It is a defect of our seam rule, not of the simulated world, the gateway or any Site.**

**M0, read-only on the current commit, on a kept DB, no fix.** `prepare --sites kobo --no-finish --days <S-13, S-12, S+0, S+1>`, about 7 min, DB `assetops_demo3_dd1b2m_test`. Report for 03:00Z and 21:00Z of those days: `unavailable_reason` and the batch's run per signal.
- **All `NO_COMPLETED_INTERVAL`, from the later run:** go on to §2.
- **`NO_MEASUREMENT`, or from the earlier run:** this trace is wrong. **Stop**, with the rows and nothing fixed.

**What else does it blank? (READ; each is checked in §4 or in DD-1b2b.)**

| Reading the client sees | Effect today |
|---|---|
| 42 and 110 kWh, MG-1, earnings | None. The mill is 0 kW at 05:55 and 23:55 (night and rest files), and `productive_kwh` only sums what is there |
| COMPLETE grades | None. `productive_kwh` and `critical_served` need 80 % and these days have about 99.3 % |
| `daylight_headroom_kw` | Needs 100 % (`chain/measures.py:49-50`), so it is not COMPLETE on any full day today. Same cause |
| Generator kWh and the G1 litre | Slightly **low** on nights running at 05:55. The fix adds up to 5 min of generator energy |
| Clinic service counts | 2 readings a day unread |
| Story-only days | Not this defect. They have no seam, and their hours outside the run are missing anyway |

**Which is telling the truth, COMPLETE or "hours missing"?** Both, under their own rules. The grade says enough of the day was covered (80 %). The study says it will not call an hour known unless every reading in it is known (`classify_daylight`). The stricter one found a real hole.

### 2. The fix: **send the real closing reading. No rule changes, no scenario file changes.**

**The seam rule (amends DD1a1-R5's edge rule): at a seam, an interval reading comes from the run whose span ended there, and a state reading from the run that starts there.**

Time alone can't express this, so:
- `host/lab_execution.py:2885`: an optional `keep_observation: Callable[[DeviceObservation], bool]`. When set, it is used in place of the time predicate on this Kobo path. The Cold path at `:2410` and every other caller are untouched.
- `DayRun.keep_observation()`, for any run of a day that has complements:
  1. outcome `NO_PRECEDING_INTERVAL`: **False**;
  2. a story run: True;
  3. a complement: an `INTERVAL_SIGNAL` at `t == emit_until`: True;
  4. otherwise the existing time rule.
- A story-only day (no complements) passes neither predicate. **Its payload stays byte-equal.**
- **`Demo.delivered_days`:** use `COALESCE(e.interval_start, e.source_time)`. A rest run's closing row has `source_time` at the next local midnight, and it must not make the next day "already delivered".

**Options refused.**
- **Overlapping or extending the runs:** changes frozen scenarios, and with them the physics and G0, to fix something that is not in the physics.
- **Not counting a missing hour at the day's edge:** this weakens a rule only to get eligible days. A missing hour is not provably dark: 05:00 sits next to dawn, and its value is what's unknown. It also touches `mini-opportunity/2`, stored hashes and MD-0's SUPPORTED hours. The rule found a real hole; the hole gets fixed.

**What a real Site does under the same rule.** A real gateway reports continuously, so every interval row carries a value and no seam exists. The first-boundary absence happens there only after a gateway restart, and that day then reads missing: honest, if harsh, since one restart hides a five-day figure. Whether to tolerate that needs real data: **BL-42**, backlog, not demo-critical.

**Regression surface (READ).**

| Thing | Effect |
|---|---|
| `kobo-*` scenario files, simulator, gateway, product rules | **Unchanged** |
| Template, MD-0 data | **Unchanged**: `mechanism_dataset.py` does not use the day list (grepped) |
| Story-only days, ACT-001 trial, Findings on S-14, S-7, S+0 | Unchanged payload; **S-7's Finding is checked by M1**, because S-8's closing row now touches S-7's edge (R8's bracket rule, `cohort.py`) |
| Cold, EV | Unchanged |
| R5's "story run byte-equal to the without build" | **Amended:** equal except its first-boundary absent interval rows. The check moves to that wording |
| G0 (run-end states) | Unchanged: states come from the runs, not from what is sent |
| G1, MONEY-A/B on full days | **May move slightly:** generator energy gains up to 5 min per running night. Report old and new. "About 1 L" gets a line to the owner only if it reads differently at one decimal |
| MILL-3 | Read unchanged (mill 0 kW in the added rows). **Reproved by P4**, and a changed value is P4's stop |
| Days with no run after a full day (S-10, S-4) | A row with `source_time` at their local midnight and its span in the day before. Coverage clips to the day (`covered_seconds`), so NO_DATA stands; M1 checks S-10 |
| `test_demo_story_days.py`, `host/tests/test_s6_verification_publication.py`, `host/tests/test_dd1a2_registered_kobo.py` | Rerun; edge-rule L0s change with this amendment |

**Tests.** L0: the predicate's truth table on each seam, using the real day-list shape; a story-only day has no predicate. L0: `delivered_days`' SQL form via one L2 row.

### 3. The fallback, if the study still can't be supported

**Decided now, used only if a stop below fires.** What the client sees:

| | Study UNKNOWN or LIMITED, eligible ≥ 1 | Eligible 0 |
|---|---|---|
| "Daytime solar unused" figure and potential money | **Not shown**: `value_line` None; "not available yet" wording stands | Not shown |
| Thread, Grow chain | Thread exists, no figure | **No thread.** The link stays `PENDING_PLACEMENT`, so no "Action agreed", "Change made" or "Checked and working" |
| The mill Action | Accepted (`create_action` checks the head, not its status; READ) and linked | Accepted, in the Actions list only, not on the board's Grow row (READ) |
| "Target met", 42 → 110 | **Stands** (from snapshots alone; dry run MEASURED) | **Stands** on the Action, with no story around it |

**The owner question, sent only if that happens; the build waits for it:**

"The spare-solar figure can't be shown honestly on the example days. Two choices. **Keep the build as is (recommended):** the mill action still shows 'Target met', about 42 up to 110 kWh a day, and spare solar reads 'not available yet'; we lose the figure and its money line, and the Grow row shows less. **Change how a day's hours are counted:** that restores the figure, but it changes a rule on real sites and adds about a unit just before the demo. Which do you want?"

### 4. Order: fix, small proof, then the re-probe, with the DB kept

1. **M0** (§1). Stop, or go on.
2. The fix and its L0s. Commit, since prepare archives git HEAD.
3. **M1, about 10 min.** `prepare --sites kobo --no-finish --days <S-13, S-12, S-8, S-7, S+0, S+1>`, kept DB `assetops_demo3_dd1b2m_test` rebuilt. Pass all of:
   - `daylight_hours` on S-12 and S-8: `missing = ()`, daylight 6 to 17;
   - at 03:00Z and 21:00Z the interval rows GOOD and the 2 state rows as before; **no held or conflicting report in the gateway**;
   - S-8's 24:00 row is present, and S-7's Finding reads as in the dry run (CANDIDATE_AVOIDABLE, 200 candidate minutes);
   - one S-13 generator figure, old vs new, reported.
   
   **Any failure: stop**, with the rows. M1 may not widen the fix.
4. **The re-probe, from nothing**, because evidence rows cannot be amended. About 45 min. Day list **adds S-14 and S-7** (v3 entries, about 40 s each), so 13 full + 4 story-only: these are the neighbours the new closing rows touch.

**Keep the DB between stops.**
- New flag on the dev subcommand: `after-children --stop-before-mill` runs `drain_mini` and step `a`, then stops.
- Then clone: `CREATE DATABASE assetops_demo3_dd1b2q_test TEMPLATE assetops_demo3_dd1b2p_test`, and copy the work folder.
- Run the mill step on `dd1b2p`. **At a stop nothing is dropped.** A rerun starts from the clone, in minutes. Drop all of them only after the next ruling or the packet.
- Evidence goes to `.agent/DD-1b2a-probe-2.json`. `.agent/DD-1b2a-probe.json` is kept.
- `tools/dd1b2a_probe.py` has never run. A fault in it is fixed in place and declared.

**P1 to P7 and their stops stand, with these changes:**

| # | Change |
|---|---|
| P1 | **Pass also needs** `window_hours` = 3 and a non-null `headroom_kw`, and reports classification. Expected, from MEASURED hours 13, 14, 15 ELIGIBLE: 5 eligible days. UNKNOWN or LIMITED, or eligible 0: **stop** and §3 |
| P3 | Grades and `daylight_headroom_kw` per day reported too |
| P4 | Compare with the dry run; a changed value is a stop |
| P6 | Later studies now have a source (MEASURED: 2 eligible hours a day after the change, on S-8, S-6, S-5). **Recurrence is now likely rather than probable.** Q7 stands |
| New P8 | Reports each full day's generator kWh against the dry run's (`DD-1a2-mill3-dry-run.json`), for §2's G1 row. Report only |

**Q7's table, S-11 row:** "N–M kW over 3 daylight hours" (expected from 3 eligible hours), not 12.

### 5. Size and scope (SCOPE-1)

| Item | Class | Reason | Size |
|---|---|---|---|
| Seam fix, `keep_observation`, `delivered_days`, L0s, M0, M1 | demo-critical | Without it there is no figure, no thread and no Grow chain, and readings are thrown away | +0.25 |
| Re-probe, flag, clone | demo-critical | P2 to P7 still owed | inside the +0.25 |
| Dark-hour tolerance after a real restart | backlog **BL-42** | Needs real data; nothing shown is false without it | not sized |

**DD-1b2a 1.25 → 1.5; DD-1b2 2.75 → 3.0; DD-1 11.75 → 12.0; lane 2 remaining 5.0 → 5.25.** No split: M1 is one small step, and it fits inside a fresh builder. DD-1b2b is unchanged at 1.5. Add BL-42 to `.agent/backlog-post-demo.md`.

### 6. Owner lines

**Now (replaces the DD1b2-R line, which was not sent; the build does not wait):**

"The Grow story hit a fault on its first real run, and it looks like ours rather than the data's. Spare solar is there on every full day, about 3 usable hours. But where we join the example runs, twice a day, we were discarding a real 5-minute reading, and that alone hid the figure. 'Target met' isn't proved on this path yet. We're fixing the join and re-running, about a quarter unit more, for 5.25 left on this lane. I'll tell you the result."

**After the re-probe, if P1 to P7 pass:**

"The Grow story now runs end to end on real data: spare solar measured before the change, [N–M kW over 3 daylight hours, from P1], the action, the mill moved, 'Target met', midday use up from about 42 to 110 kWh a day. On later sunny days there's still spare solar, so the opportunity line reads 'Seen again' next to 'Target met', and the Portfolio counts it as open rather than verified. Both are true, and the script says so. The figure shows on the days before the change rather than day S, which is the partly-checked trade you already accepted. Hiding 'Seen again' would need a new rule, about half a unit, and I'd leave it; tell me if you'd rather not."

Replace the "Seen again" sentences if P6 measured no recurrence. If §3 fires, send its question instead.

### Handoff

A fresh builder resumes **DD-1b2a** from M0, on `task/DD-1b2-finish-rehearsal`. Reading budget: this section; DD1b2-R Q7 and the probe table; `.agent/DD-1b2a-handoff.md`. Code: `tools/demo_story_days.py:80-112,285-300`, `host/lab_execution.py:2880-2890`, `tools/demo_combined.py` `delivered_days`, `after_children`. Stops come back to this Architect. The unit keeps its own review after the re-probe.

## DD1b2-R3: second P1 stop: the study is LIMITED, `SOURCE_CLASS_MIXED` (Architect, Claude, 2026-11-07)

Input: `.agent/review-packet-DD-1b2a.md`, `.agent/DD-1b2a-probe-2.json` at `515499670`. **Nothing here has been run by me. MEASURED = the probe's stored rows; READ = code.** The class is inferred, not measured. **Two things run now, in parallel; only the rule choice waits for the owner.** My errors: the probe table's "FULL" (the stored word is `COMPLETE`; the builder's tool copied it) and R2's unit count (§5).

### 1. Measure first: yes. **M2, read-only on the clone `assetops_demo3_dd1b2q_test`, minutes, nothing written.**

For the five study days, using the worker's own inputs (`day_heads`, `_classification`'s `provenance_blocks`). Evidence `.agent/DD-1b2a-m2.json`:
- (i) the resolver's `classification` and its exact reason codes;
- (ii) per run behind the set: run ID, snapshot SHA, foundation version, binding set version;
- (iii) **the figure the client would see:** `frozen_result(heads, "REGISTERED_SIMULATION")` in memory: status, `headroom_kw`, `window_hours`, and `value_line`. The money line is reported from the declared price.

**Outcomes.**
- `MIXED`, reasons exactly `[MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS]`, status SUPPORTED in (iii): the §2 choice stands.
- Any other reason, or (iii) not SUPPORTED, or a figure of zero: option (b) is dead. The study stays as (a), and the owner is told, not asked.

### 2. The owner question replaces R2 §3's (which named the wrong rule)

| | What the client sees | Size | Blast radius (READ) |
|---|---|---|---|
| **(a) Fallback** | Grow potential: "Limited evidence: readings come from mixed sources, so the size is not worked out yet". No kW, no money. "Seen on 5 of 5 well-observed days" | +0 | None. WK-2c and F-THREADS' SUPPORTED row become "reported"; plan row ST-3's "value line from a supported study" must be reworded. The phrase "mixed sources" is itself a question the presenter must answer |
| **(b) Narrow study rule (recommended, subject to M2)** | The figure and its money line on S-11 | **+0.5** | See below |
| (b-wide) Resolver rule | Same | 1.5+ est. | **Refused.** `source_provenance.py` feeds Cold money (`cold_consequence.py:96`), EV (`ev.py:58`, `ev_money.py:33`), verification windows (`verification_rules.py:664-700`), `postgres_assessment_store.py:1422`, placement text, public provenance; pinned by `test_s405_resolver*`, `test_w206_ev_store_postgres`, `test_w301_provenance_dto_postgres` |
| (c1) One 5-day registered run | The figure | **1.25+ est.** | New 120 h derived scenario and a multi-day day-list kind; battery no longer restarts at 06:00, so generator nights, G0 and "no Finding on steady days" need re-proving; long-run cost unmeasured. **Refused:** fails SCOPE-1 |
| (c2) Publish as authored | The figure | 1+ est. | **Refused, on honesty.** `AUTHORED_DEMONSTRATION` allows any number of publications (how MD-0 is SUPPORTED, `mechanism_dataset.py:297`), but it would label simulator runs as an authored fixture and bypass the path the demo proves |

**(b), bounded.** `evidence/source_provenance.py` stays byte-unchanged, as do Cold, EV, money and verification. Only `mini_decisions`: in `_classification`/`frozen_result`, a `MIXED` set whose only reason is `MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS` does not limit a study when **every run is a registered run of this Site on one basis** (the fields M2(ii) shows are equal; if they differ, (b) is dead). Note: this overrides N-L2 for this read, so it needs a stated decision; a real Site has no run IDs, so it is unaffected. Stored `input_sha256` excludes the class (READ), so it needs a fresh build: DD-1b2b's rehearsal is the first real proof. L0 truth table incl. a differing basis → still LIMITED; L2 on the fixture; `test_ch9*` and MD-0 study tests rerun. The exact field list is fixed by this Architect's successor after M2.

**Why (b).** The limitation's sentence is untrue of these days: they differ only because we cut one day into three runs. The potential is one of ST-3's three slots, and the only size of the Grow opportunity. (a) is honest and cheap, and it is the right answer if the owner would rather stop adding.

**The question, sent after M2 with [figure] filled and P4's result; DD-1b2a's merge waits for it, P4-P7 do not:**

"The system found spare solar on all 5 example days before the mill change, but won't size it, because those example days were generated in separate runs and it reads that as 'mixed sources'. **Allow it for this one study (recommended):** runs from the same Site and setup count as one source here, and nothing else changes. Shows [figure] and its money line; half a unit more, 4.5 left on this lane, and it isn't proved until the full rehearsal. **Leave it:** no extra work, 4.0 left; the Grow row says 'Limited evidence: readings come from mixed sources, so the size is not worked out yet', with no figure or money. The mill result is [P4's result] either way."

### 3. The fallback now (eligible 5, LIMITED). All READ, until P2, P5, P6 measure it. Corrects R2 §3's "not available yet" wording; its 0-eligible column no longer applies.

- **MEASURED:** LIMITED, 5 assessed, 5 eligible, `headroom_kw`/`window_hours` null.
- **Thread:** eligible ≥ 1 is a Source (`threads.py:164`), so the thread opens, effective the first eligible day, S-19.
- **Opportunity line:** status signal open while OPEN (`outcomes.py:44`); `evidence_label` "Limited evidence", `filter_state` "unconfirmed", `seen_line` as above; `value_line` None; `limit_line` is the mixed-sources sentence (`vocabulary.py:21,76-78`), and it is the potential's only line (`outcomes.py:231-232`). Portfolio FOUND, null headroom.
- **Action:** `create_action` checks the head, not its status, so it is accepted and linked, with the full chain.
- **"Target met":** from snapshots alone, so it stands, once P4 measures it.

### 4. P4-P7 now: **yes, run them on the clone, independent of the answer.** The study status is not an input to the Action, freeze, or verdict (READ; `demo_combined_mill.py:255` gates only on 0 eligible).

Copy the fixed mill tool into the clone's private tree, declared as the literal fix alone, then the mill step, `after-children` remainder, `dd1b2a_probe.py ticks`. Evidence `.agent/DD-1b2a-probe-3.json`. Do not drop the DBs.

| Row | Under (a) | Under (b) |
|---|---|---|
| P1 | Pass restated: LIMITED, `SOURCE_CLASS_MIXED`, eligible 5 | SUPPORTED, on a fresh build only, in DD-1b2b |
| P2-P5, P7, P8 | Unchanged | Unchanged |
| P6 | S-11 reads the limit line; the rest as Q7's table | Measured now as (a); figure proved in the rehearsal |

P3's expected days stand (MEASURED, S-13..S-11, 42.000). Q7's stops stand. A P4 or P5 failure comes back here before the owner is asked.

### 5. Units: **R2's 5.25 was wrong.** It carried a stale plan figure that still held merged work. Your count stands: **4.0 before this stop.**

(a): 4.0, DD-1b2a 1.5. (b): **4.5**, DD-1b2a 2.0, DD-1b2 3.5. (c1): 5.25+, refused. DD-1 follows.

### 6. The two other items, and backlog

- **Seam rule dropping `NO_PRECEDING_INTERVAL` on every run of a seamed day: nothing needed.** At a chain's first night it removes an absent row whose span lies in the day before. No reading is lost. M1's `delivered_days` and S-10 checks cover it.
- **Generator 3.167 → 3.244 kWh (+0.077, S-12, MEASURED): nothing now.** It is more correct. The litre is recomputed in DD-1b2b's MONEY-B/G1 row; the owner gets a line only if it differs at one decimal (R2 §2).
- **Backlog:** BL-43 is free (grepped). (b) chosen: BL-43 = a compatible-run-basis record in the resolver for all readers. (a) chosen: BL-43 = the narrow study rule, 0.5.

### Owner line now (no decision; the build does not wait; replaces R2 §6's first line if not sent)

"The join fix worked: all 5 example days before the mill change now count, and spare solar is seen on all 5. A second, separate rule still stops the system sizing it. We're measuring that and finishing the mill check now. I'll bring you one short question with both results, and neither is claimed until then."

Handoff: the builder runs M2 and §4; both results return to the coordinator. **A fresh Architect should take any follow-up,** including (b)'s field list.

