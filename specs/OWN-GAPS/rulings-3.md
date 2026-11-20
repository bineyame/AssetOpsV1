## R5 — G1 rehearsal F-THREADS (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Owner away; decisions delegated ("let the architect make
decisions ... based on understanding of how real sites work and what assetops is trying to achieve, no cutting
corners on fundamentals"). Input: `AssetOpsV1-g1/.agent/OWN-G1-phase-2-handoff.md`, branch `task/OWN-G1-add-dates`
head `d9540c26c`. **READ** = code cited; **DB** = read-only query on `assetops_demo3_g1audit_test` (session
`default_transaction_read_only = on`; the drain `counts` child, which only SELECTs). Nothing was written to the clone.

### R5.1 Root cause (READ + DB): the added days' mini-depth work was still queued when "checked" was reported

- **DB, after run 1** (`demo_combined_drain.py counts`): every count is 0 except `mini_deferred`: **KOBO-001 24,
  KISIWA-001 70**. `recompute_job` rows created by run 1: Kobo 34 (10 `DONE`, 24 `PENDING`, all created 00:09:48Z,
  windows 2026-11-08 02:00–12:00Z = the added day); Kisiwa 92 (22 `DONE`, 70 `PENDING`, created 00:01:12Z, windows
  2026-11-07 14:00Z – 11-08 13:00Z = the added night). Nothing else is pending (dirty, snapshots, threads,
  opportunity all 0).
- **Why one tick is not enough (READ).** The tick's `mini` stage leases at most `TickLimits.mini_jobs_per_site = 10`
  jobs per Site (`scheduling/tick.py:70`, `scheduling/stages.py:140-155`). A day arriving at once creates ~34 Kobo jobs
  and ~92 Kisiwa jobs. §4.4 runs exactly one tick per date (`tick_and_verify`, `demo_combined.py:1145-1173`), so 10
  Kobo jobs ran and 24 stayed queued. `_add_core_day` drains mini only for `assess == "build"` (`:1018`); `add-dates`
  days are not "build".
- **Why the board says Unknown (READ).** The mini board's settledness needs every depth domain's head for the board
  day: `depth_ok = all(depth.get(d) is not None for d in DEPTH_DOMAINS)` (`site_outcomes/mini.py`, `compose`), and
  `settled["MG-1"] = settled["MG-5"] = base and depth_ok`; an unsettled outcome is `UNKNOWN / PRODUCER_NOT_SETTLED`
  (`outcomes/status.py:71-72`). F-THREADS (`demo_combined_finish.py:856-891`) reads every delivered `days.json` day's
  board through `board_faults` and found that code on KOBO-001 2026-11-08.
- **The builder's guess is right in substance, with one correction:** it is not the late assessment as such, nor a
  missing second tick. It is that the tool reported a day "checked" while the product's own queue for that day still
  held work. `serve` does not drain either (`:1209-1245`: one tick every 120 s); it simply keeps ticking, and would
  have settled Kobo after ~3 more ticks (~6 min) and Kisiwa after ~7 (~14 min).
- **Same defect on Kisiwa, uncaught.** The added Kisiwa night's board day had 70 depth jobs queued. No row caught it:
  F-THREADS reads only `days.json` days (Kobo, Cold, EV); Kisiwa nights live in `kisiwa-days.json`; KIS rows read story
  nights only. The fix below covers it at the producer level; R5.5 adds a rehearsal read of the Kisiwa boards.
- **Is the late arrival handled correctly by the product? Yes.** The readings went through the gateway path, were
  accepted at real time, and the product queued exactly the depth work a real gateway reconnecting after an outage
  would cause. The product is right; the tool's claim was premature. **No product change.**

### R5.2 Ruling: settle each date through the product's own producers before moving on (no product code; G1 tool only)

How a real site works: readings arrive, the product queues the work they cause, and the day is "checked" only when
that work has run. A whole day arriving at once (the R4.2 gateway-reconnect story) is a burst; the scheduler works it
off at its bounded rate. The tool simulates the gateway and also stands in for wall-clock time, so before it says a
day is checked, or sends the next day, it must let the queue run to empty **through the same producers**. It must not
skip, special-case or mark anything.

Both mechanisms below already exist and are the ones `prepare` uses (`finish`, `:785-808`):
- `drain_mini()` (`:810-826`): the worker's own CLI `mini_depth.worker run-pending`, i.e. the same
  `MiniDepthWorker.run_pending` the tick's `mini` stage calls, with the same DB-time lease and cutoff, without the
  per-tick bound of 10. Outputs are identical; only the throughput differs.
- `drain(name)` (`:878-934`): the product's scheduled tick (`TICK`, raw), repeated until every count (dirty,
  snapshots, threads, mini, opportunity) is 0 on every Site, with the N / 2N / two-flat-ticks failure guards; then
  Performance and pre-build once (as `tick()` does).

`drain()` alone is **not** enough: its N ignores `mini_deferred` (`demo_combined_drain.py:26-31`), so 70 Kisiwa jobs
at 10 per tick would fail "past 2N" (N = 2). `drain_mini()` comes first, exactly as in `prepare`.

**Exact change, `tools/demo_combined.py` only:**

1. New method:
   ```python
   def settle(self, name: str) -> dict:
       """R5.2: run the queued work of the added data through the product's own producers until nothing is due:
       the mini-depth worker (no per-tick bound), then the scheduled tick until every drain count is 0."""
       self.drain_mini()
       return self.drain(name)
   ```
   `defer_drain` stays False in `add-dates`, so a failed drain raises `SystemExit("DRAIN FAILED: …")` (`:925-926`).
2. In `add_dates`, the per-date block (`if today: added += self.tick_and_verify(today)`) becomes:
   - **A date with a Kisiwa night:** `self.drain_mini()`, then `tick_and_verify(today)` (unchanged: its `tick()`
     writes `last-tick.json`, which KIS-11 reads, and verify-day needs that report), then
     `record = self.drain(f"settle-{d.isoformat()}")`.
   - **A date with only Kobo/Cold/EV days:** `record = self.settle(f"settle-{d.isoformat()}")` and no separate
     `tick()`. `drain`'s first tick is the date's tick (§4.4's "one tick" becomes "ticks until settled"). This saves
     one ~80 s tick per date, which matters for R4.2's live step. It also leaves `last-tick.json` as the last
     Kisiwa-visiting report, as in `prepare`, where the drain ticks after `tick(times=2)` do not rewrite it.
   - Then, for every non-Kisiwa item of the date: `item["checked"] = f"settled ({record['ticks']} ticks)"` (replaces
     `"tick " + outcome`). Every item of the date also gets `"tick_failures"`: the `tick_failure` entries of
     `record["log"]` (an empty list when none). A non-empty list is printed in the item's plain line as "(a background
     step reported a failure; see logs)". It does not stop the command (prepare's own drains record and continue, and
     the closing `finish check` judges the build). The rehearsal requires it to be empty (R5.5).
   - Kisiwa's `tick_and_verify` loop is otherwise unchanged; for a Kisiwa-only date the non-Kisiwa `checked` loop
     simply has nothing to do.
3. **Closing settle (resume after a crash or a stopped run).** After the date loop and before `finish check`,
   whether or not any date was added, read `self.counts()`; if `demo_combined_drain.total(counts) > 0`, say "settling
   work left from an earlier run" and run `self.settle("settle-close")`. This makes the "already present" second run
   (§4.7 step 2) finish what a crashed or stopped first run left. It runs also under `--no-check`. With all counts 0 it
   costs one counts child and no tick.
4. `--no-check` skips only `finish check`, never the settle (R4.2's live command uses `--no-check`, and the presenter's
   reload must show the day checked, not Unknown).
5. A drain failure inside `add-dates` leaves earlier dates in place (append-only, as §4.5). The `SystemExit` message is
   prefixed with "{site list} {date}: the added data did not finish processing; " and ends with "prepare a fresh build
   before a demo." `.busy` is removed by the existing `finally`.
6. No change to `add-day` for Kobo/Cold/EV outside `add-dates` (its `late` kind deliberately leaves the day for the
   serve tick, DEMO-SPARSE U4), to `drain`, `drain_mini`, `n_for`, the tick limits or any product file.

**Time effect.** Per date add one `drain_mini` pass (Kobo 34 jobs) and usually 1–2 ticks. R4.2's live Kobo step goes
from ~9 min to an estimated ~10–11 min. R4.2 item 4 already says: if the Fri 13 walkthrough measures start-to-checked
above 11 min, start it at the end of step 0. Report the measured `settle-*` seconds in the packet.

### R5.3 Tests (no DB), `backend/tests/test_own_g1_add_dates.py`

Use a `Demo` test double: `object.__new__(Demo)` with `story`, `_add_core_day`, `add_kisiwa_night`, `kisiwa_child`,
`tick`, `drain_mini`, `drain`, `counts`, `finish_check`, `db_now`, `site_zones`, `delivered_days`, `hold_busy`
replaced by recorders that append `(name, args)` to one call list. `work` is a `tmp_path` holding `days.json` and an
empty `kisiwa-days.json`.
1. **Kobo-only date:** call order `_add_core_day(KOBO-001)`, `drain_mini`, `drain("settle-<date>")`; **no** `tick`;
   the summary item's `checked` is `"settled (2 ticks)"` from a drain record `{"ticks": 2, "log": []}`. **Must-fail
   guard:** with the settle removed this test fails (it asserts both `drain_mini` and `drain` are called, in that order,
   after the child).
2. **Date with a Kisiwa night and a Kobo day:** order `add_kisiwa_night`, `_add_core_day(KOBO-001)`, `drain_mini`,
   `tick`, `kisiwa_child("verify-day", …)`, `drain("settle-<date>")`. `drain` runs after verify-day, and `tick` is called
   exactly once when verify answers DONE the first time.
3. **Date-major preserved:** two dates; date 1's `drain` precedes date 2's first child.
4. **Drain failure stops the command:** `drain` raises `SystemExit("DRAIN FAILED: …")` on date 1; date 2's child is
   never called, `finish_check` is never called, `.busy` does not exist afterwards, and the message carries the
   R5.2 item 5 prefix and suffix.
5. **`--no-check` still settles:** order as test 1, `finish_check` not called.
6. **Nothing added, nothing pending:** every date "already present" (`_add_core_day` raises `DUPLICATE_DAY`), `counts`
   returns all zeros → no `drain_mini`, no `tick`, no `drain`; `finish_check` called once.
7. **Closing settle on resume:** as test 6 but `counts` returns Kobo `mini_deferred: 24` → `drain_mini`, then
   `drain("settle-close")`, then `finish_check`.
8. **Tick failures carried:** drain record `log` has one entry with `tick_failure` → the item's `tick_failures` has it,
   its plain line has the R5.2 text, and the command does not stop.
9. Existing `--dry-run` test extended: none of `drain_mini`, `drain`, `counts`, `tick` is called.

Run: `test_own_g1_add_dates.py` plus the phase-2 no-DB set; the same 5 known failures minus the one fixed in R5.6
(so 4, all identical on main).

### R5.4 F-THREADS: correct; it stays as is

F-THREADS states a fundamental: no board for a day with delivered data says Unknown because a producer has not
finished. A manager who opens yesterday and sees Grow and Cost "Unknown" learns that the product is not ready to be
looked at. It fired on exactly the board R4.2 step 7 will reload in front of the client. Including added days is
correct: they are delivered days in `days.json`. **No bound, no exclusion, no change.** R2-G1 Q3's pre-authorised
bound is for KIS rows only and does not extend to F-THREADS.

Kisiwa added nights are outside F-THREADS (R5.1). The producer-level guarantee (R5.2: `drain` ends only at all counts 0
on every Site) covers them for G1. A permanent Kisiwa added-night board row in `finish check` is **BL-52** (the coordinator adds it to `.agent/backlog-post-demo.md`;
not demo-critical given that guarantee; 0.25 unit).

### R5.5 Rehearsal re-run

The run-1 clone is in exactly the failing state. Use it first to prove the fix and the resume path. Then re-clone, to
prove the per-date path on fresh data, which the reused clone cannot show (its dates are already present).

0. Commit the R5.2 change, the R5.3 tests and R5.6 as separate commits; rebuild `tree` from the new HEAD (handoff
   recipe: `git archive`, prepare's parts + `var/sites/kobo-001.yaml`); expect the one-time `chain_snapshots` rebuild.
1. **Reused clone (resume proof):** the same command,
   `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to 2026-11-08`, on `assetops_demo3_g1audit_test` /
   `var/demo3_g1audit`. Expect: plan with nothing new (or Kisiwa 11-08 if run after 12:05Z, which is then added and
   settled per date), "already present" for the run-1 days, "settling work left from an earlier run", `settle-close`
   `verdict: done`, **finish check PASS (51/51)**. Keep `check.json` and `settle-close.json` as evidence. Then rename
   the folder to `var/demo3_g1audit_run1` (evidence; untracked) and drop the database.
2. **Fresh clone:** no serve on the template; `CREATE DATABASE assetops_demo3_g1audit_test TEMPLATE
   assetops_k9_audit_r3u`; robocopy `AssetOpsV1-k10\var\demo3_r3u` → `var/demo3_g1audit` without `tree`; `tree` from
   the new HEAD; `evidence_migration run` (KOBO-001) and `performance_migration run` (KOBO-001, KISIWA-001), all
   "cutover: permitted" (as phase 2).
3. **Run A:** `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to 2026-11-08` (`yesterday` also works once every
   Site's yesterday is 11-08). Expect per-date `settle-<date>.json` with `verdict: done`, every item's `tick_failures`
   empty, the Kisiwa night(s) `WITHIN_MARGIN (revision 1)`, Kobo `settled (n ticks)`, **finish check PASS (51/51)**.
4. **Run B:** the same command: everything "already present", counts all 0 so no settle (no `settle-close.json`
   written), finish check PASS.
5. `--to` today: the run-1 evidence (`DATE_NOT_PAST`, nothing written) stands; that path is unchanged. Do not repeat it.
6. Read-only proofs after run B: the drain `counts` child shows 0 for every field on every Site. A scratch
   (uncommitted) read through `finish.app_client` of the KISIWA-001 board for each added `night_date` gives
   `board_faults == []`. For the last added night's next board day, record the faults; they are not blocking.
   `chain_coherence collect` + `check` gives EX-2 = 0.
7. Then the review packet `.agent/review-packet-G1.md` with the settle timings, run A wall time and both `check.json`
   summaries. Keep the fresh clone until review ACCEPT, then drop it.
   **Stops:** any non-PASS row, any `tick_failures`, a `settle-*` `verdict: fail`, or a Kisiwa board fault on an added
   `night_date` → back to the Architect with the file. A KIS row failing only on added-night content still takes the
   R2-G1 Q3 bound. Cap: the original 2 × 1.5 h for steps 1–6.

### R5.6 `test_carry_r3k2_l2_no_kis_row_keeps_the_skip_branch` (12 vs 13): fix it on the G1 branch

READ: main's `demo_combined_finish.py` has 13 `raise KisiwaMissing()`. The 13th is KIS-11's no-Kisiwa branch
(`:1489-1490`, added by OWN-G2 u2 `06c09b95b`). It is the same skip-branch pattern the test protects, and the test
pin was simply not updated when G2 merged. A known-red test hides real failures behind "fails on main too", so it is
not left to E2. **Fix on the G1 branch as its own commit:** `== 12` → `== 13` and add "KIS-11 (OWN-G2)" to the comment
list on `:594-595`. If the builder's count of the 13 raises does not match the 13 `@row("KIS-…")` rows one-to-one
(KIS-4, 8a, 1, 2, 6, 7, OV, 5, 10, 3, 9, 11, 8), stop and report; do not change the count.

### R5.7 Decisions logged for owner review

- **D-R5.1** Cause of the G1 rehearsal failure: the tool said Kobo's added day was checked after one background
  refresh, while the product still had 24 of that day's 34 analysis jobs queued (10 run per refresh). Kisiwa's added
  night had 70 queued, and no check caught it. The product handled the late day correctly; the tool's claim was early.
  No product change.
- **D-R5.2** Fix: before `add-dates` reports a day checked or sends the next day, it runs the queued work through the
  product's own workers and scheduled refresh until nothing is due (the method `prepare` already uses), under
  `--no-check` too. It also does this once at the end if an earlier run left work pending. The live Kobo step may take
  ~1–2 min longer (R4.2's start-earlier rule covers it).
- **D-R5.3** The failing check (F-THREADS: no board may say "Unknown" because processing has not finished) is right and
  stays unchanged. A Kisiwa equivalent for added nights is backlog BL-52; the settle covers Kisiwa now.
- **D-R5.4** Rehearsal: first on the failing clone (proves the fix and the resume path), then on a fresh clone (two
  identical runs), all checks green before review.
- **D-R5.5** The stale Kisiwa test count (12 → 13 after the diesel-night check added KIS-11) is fixed on the G1 branch
  now, not left red until E2.

## R6 — G1 resume run: CO-2, WK-6 and the tree rebuild (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Owner away; same delegation and fundamentals instruction
as R5. Input: `AssetOpsV1-g1/.agent/OWN-G1-phase-3-handoff.md` (branch head `7bf811898`). **READ** = code cited;
**DB** = read-only query on `assetops_demo3_g1audit_test`. R5's settle fix is confirmed: `settle-close` drained 94
mini jobs, every count reached 0, and F-THREADS passed.

### R6.1 CO-2 (STALE_PROJECTION: SCHEDULE_STOPPED, SITE_VISIT_STALE): the product is right; add-dates ticks once before the check

**What the product does (READ).** `UpstreamCurrentness` (`scheduling/upstream.py:176-183`) blocks currentness with
`SCHEDULE_STOPPED` when the environment heartbeat is older than its threshold (300 s), and with `SITE_VISIT_STALE` when
the Site head is not observed. CO-2 (`demo_combined_finish.py:252-264`) requires the Kobo overview freshness `CURRENT`.
After 23 min with no tick, the overview says the figures are not current.

**What a real stopped schedule must show.** Exactly that. If the background schedule stops on a real Site, the
figures stop being refreshed, and the screen must say "not current" rather than present old figures as current. That
honesty is a fundamental, so **the check does not tolerate a stale heartbeat, with or without a serve.** Exempting it
would let a build pass while its screens say "not current".

**What `finish check` asserts.** The build as served, with the schedule running, as on a demo day (`serve` ticks every
120 s). `prepare` meets that by ticking right before its check (`finish`: `tick(times=2)` + `retry_until_visited`,
then the check). `add-dates` must meet it the same way. A run that adds nothing and has nothing pending still ends in a
check of the served state, so it ticks once. This is the scheduler running, not a cosmetic heartbeat touch: the tick is
the product's full scheduled tick and does real work if any is due.

**Change (`tools/demo_combined.py`, `add_dates`).** Immediately before `check = self.finish_check()`, and only when
the check runs (not under `--no-check`):
```python
report = self.tick()   # R6.1: the check reads the served state; the schedule must have just run (as prepare's finish)
if "kisiwa" in story["sites"]:
    report, extra = retry_until_visited(report, lambda: self.tick(times=1))
    if extra:
        say(f"  tick: {extra} extra tick(s) for KISIWA-001's fuel_night stage")
```
This always runs after the closing settle (R5.2 item 3). It rewrites `last-tick.json` with a Kisiwa-visiting report,
which KIS-11 reads, exactly as in `prepare`. Under `--no-check` nothing changes: the serve keeps the schedule running
during the demo. Runbook line (DS-1a refresh, R1.5): "A check of a build with no serve running is valid only right
after `add-dates`, which runs the schedule first; on the demo machine `serve` must be running whenever a screen is
shown. If a screen says the figures are not current, `serve` has stopped."

**Test changes (`test_own_g1_add_dates.py`, no DB):**
- R5.3 test 6 (nothing added, nothing pending): the order becomes `counts`, `tick`, `finish_check`; no `drain_mini`
  and no `drain`.
- R5.3 test 7 (closing settle): `drain_mini`, `drain("settle-close")`, `tick`, `finish_check`.
- R5.3 test 1: no `tick` between the child and `drain`; exactly one `tick`, after the last `drain` and directly before
  `finish_check`.
- R5.3 test 5 (`--no-check`): no `tick` at all on a Kobo-only date.
- New: Kisiwa in the story and the closing tick's report has no KISIWA-001 `fuel_night` entry → one extra
  `tick(times=1)` (patch `time.sleep`), then `finish_check`.
- **Must-fail guard:** test 6 fails if the closing tick is removed.

### R6.2 WK-6: select the study the row is about (the one ending S+1), not the newest

**What happened (DB).** Kobo's rolling five-day productive-use studies: #9 is `2026-11-03..11-07` (S+1 = 11-07; S =
11-06), created by prepare. #11 is `2026-11-04..11-08`, created at 03:55Z by the added day. #9 is still there and
unchanged. WK-6 lists opportunities over the S+1 board link's five days (`:647-655`), which overlap #11 too. It then
takes `max(found, key=last_day)` (`:657`) and asserts `last_day == S+1`.

**Ruling.** WK-6's own docstring names its subject: "the Kobo productive-use opportunity page for the 5-day study
ending S+1". `max()` was a stand-in that held only while S+1 was the newest day. A real Site makes a new rolling study
every day, so a check that wants a specific day's study must select it by that day. This is the row's intent made
exact. It is not a loosening and not a bound that hides content: #11 is correct product output, and other rows (and the
board for 11-08) cover it.
- New pure helper in `tools/demo_combined_rows.py`:
  ```python
  def study_ending(found: list[dict], last_day: str) -> dict:
      """WK-6 (OWN-GAPS R6.2): the one opportunity whose study ends on `last_day`; later rolling studies are ignored."""
      hits = [o for o in found if o.get("last_day") == last_day]
      assert len(hits) == 1, ("expected exactly one study ending", last_day, sorted(o.get("last_day") for o in found))
      return hits[0]
  ```
- `wk6`: replace `:657-658` with `opp = demo_rows.study_ending(found, ctx.day(1).date().isoformat())`. Everything else
  in the row is unchanged (the `scenario_id`, mill and tariff asserts). Add to the docstring: "R6.2: the study is
  selected by its last day; later studies from added days are other days' studies."
- No-DB tests (in `test_own_g1_add_dates.py`): (a) `found` = studies ending 11-06, 11-07, 11-08 → returns the 11-07 one
  (**must-fail guard**: `max()` would return 11-08); (b) no study ends 11-07 → `AssertionError`; (c) two ending 11-07
  → `AssertionError`.

**Narrow pre-authorisation for the rest of the rehearsal.** A non-KIS row that fails **only** because an added day
produced a newer object may get the same fix, but only when all of these hold:
1. The row's docstring names a story day or story object as its subject.
2. The fix selects that object by its story key (day, code or id from `story.json` / `days.json` / the row's own docs).
3. No assertion on the object's content changes.
4. It comes with a no-DB test that includes the newer object, and it is listed in the packet.

Anything else, including any assertion change, any CO-2-style state failure or any COH row, stops and comes to the
Architect.

### R6.3 Rebuilding `tree` deleted the legacy comparison report: recipe fix only; no add-dates or E3 guard

**What happened (handoff).** The legacy S2 comparison report is file-backed inside `tree`. Replacing `tree` removed
it, and the Kobo overview answered 409 `AWAITING_EVIDENCE_MIGRATION` until `evidence_migration run` was repeated.
`performance_migration` already runs on every `tick()` (`performance_and_prebuild`, `:857-865`).

**Ruling.**
- Only the rehearsal recipe (R2-G1 Q4) replaces `tree` on an existing build. On the demo path `tree` is written once,
  by `prepare`, whose `finish` runs `evidence_migration` (`:796-799`). `add-dates`, `serve` and E3 (a fresh `prepare`)
  never replace it. So this is a **recipe step**. The R2-G1 Q4 recipe gains: "after replacing `tree`, run
  `evidence_migration run --tenant demo --site KOBO-001` and `performance_migration run` for KOBO-001 and KISIWA-001,
  and require 'cutover: permitted' before any `add-dates` or check."
- **No add-dates guard.** The failure is not silent: the product answers 409 with its reason, and `finish check`
  fails on many rows. Making `add-dates` run a migration would turn a data-arrival tool into a deployment tool, which no
  real gateway does. Refusing would duplicate a signal that is already loud.
- Runbook line (DS-1a refresh, R1.5): "Never replace or edit a build's `tree`. New code means a fresh `prepare`."
- E3 unchanged.

### R6.4 Rehearsal from here (replaces R5.5 steps 1–4)

0. Commit R6.1 (closing tick + tests) and R6.2 (helper, WK-6, tests) as two commits. Run the no-DB set (expected: the
   4 known failures only). Rebuild `tree` from the new HEAD **for the fresh clone only** (step 2).
1. **Reused clone: no further run.** Its two runs are kept as evidence: `settle-close-attempt1.json` (R5 resume proof)
   and `check.json` (49/51, CO-2 and WK-6, the input to this ruling). A third run there would repeat run B below. Rename
   the folder to `var/demo3_g1audit_run1`, then drop `assetops_demo3_g1audit_test`.
2. **Fresh clone:** as R5.5 step 2. After the new `tree` is in place, run `evidence_migration` (KOBO-001) and
   `performance_migration` (KOBO-001, KISIWA-001); all "cutover: permitted" (R6.3).
3. **Run A, kept:** `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to 2026-11-08`. Must show: per-date
   `settle-<date>.json` `verdict: done`; every `tick_failures` empty; Kisiwa night(s) `WITHIN_MARGIN (revision 1)`;
   Kobo `settled (n ticks)`; the closing tick; **finish check 51/51 PASS**; F-THREADS, CO-2, WK-6 and KIS-11 named in
   the packet as passing.
4. **Run B, kept:** the same command, started **at least 10 minutes after run A ends** (so the heartbeat is stale
   before it starts, which proves R6.1 on real wall time). Must show: everything "already present", counts all 0, no
   settle, one closing tick, **finish check 51/51 PASS**.
5. R5.5 step 6 read-only proofs after run B (counts 0 everywhere; Kisiwa added-`night_date` boards with
   `board_faults == []`; `chain_coherence` EX-2 = 0). The `--to` today refusal is not repeated.
6. Packet `.agent/review-packet-G1.md`: both runs' wall times, `settle-*` seconds, the closing-tick seconds, both
   `check.json` summaries, and any R6.2 pre-authorised fix used. Keep the fresh clone until review ACCEPT.
   **Stops:** as R5.5, plus anything outside R6.2's pre-authorisation. Cap: the remaining part of 2 × 1.5 h, counted
   from the fresh clone's creation.

### R6.5 Decisions logged for owner review

- **D-R6.1** When the background schedule has stopped, the product says the figures are not current, and that stays:
  it is what a real Site must show. The build check reads the build as served, so `add-dates` runs the product's
  scheduled refresh once right before its check, as `prepare` does. On demo days `serve` must be running.
- **D-R6.2** The productive-use check now picks the study that ends on the story day it is about, not the newest
  study. Real Sites produce a new rolling study every day. Further fixes of this exact kind are pre-authorised under
  four conditions; anything else comes back to the Architect.
- **D-R6.3** A build's code folder is never replaced on the demo path. The rehearsal recipe re-runs the comparison
  setup after replacing it. `add-dates` does not run deployment steps, and E3 is unchanged.
- **D-R6.4** Rehearsal keeps both fresh-clone runs (A: add and settle; B: nothing to add, started on a stopped
  schedule), each 51/51. The reused clone runs no more; its earlier runs are kept as evidence.

## FR-A stop rulings (2026-11-09)

- Architect: Claude (assetops-architect), delegated by the owner. Binding checked: `.ai/ROLE_CONFIG.md` makes the
  Architect Claude since 2026-10-27. Input: `AssetOpsV1-e2fa/.agent/review-packet-E2-fix-A.md` (`task/E2-fix-A`,
  d0e678eb9) and the console log of its run `20261109-160557-644a04`. I read the code at d0e678eb9. I ran read-only
  queries on the latest demo builds: `assetops_demo3_g1audit_test`, `assetops_demo3_k9rehearsal_test` and
  `assetops_demo3_kisiwa_test`. Nothing else was touched.

### R-1 G-e: a real inconsistency that no presented screen shows. Bounded deferral with an E4 check. (D-E2.9)

**What the board does.** The MG-2 NEEDS_ATTENTION and MG-4 WATCH states come from a Finding, not from readiness.
- Status rule 5 (`outcomes/status.py:69-77`) gives NEEDS_ATTENTION for an open primary Finding and WATCH for an open
  secondary one.
- `board.py:688-694` raises those signals only for Findings whose episode is inside the board day (`in_window`).
- MG-2 and MG-4 count as `settled` (`mini.py:539-540`) when the source gate is open, the board day is settled and the
  dispatch read returned.
- `day_settled` (`chain/read.py:100-108`) treats a stored NO_DATA row as settled.

So a day can be "settled" with nothing checked.

**What the gap line counts.** "N of the last 31 days have no checked readings yet" (`mini.py:133`, `:361-385`) counts
the days whose day grade is NO_DATA or PENDING. A day's grade is the weakest grade among its measures. NO_DATA means
`covered_seconds <= 0` (`chain/grading.py:76-97`). MG-2's measure is `avoidable_gen_min`. Its coverage is the union of
the evidence intervals of the selected dispatch run (`chain/measure_impls.py:286-318`, `analytic_run_evidence`).

**What s602b stores.** On 10-06, 10-21 and 11-02, all three stored measures are NO_DATA (packet, G-f). The same boards
hold SUPPORTED or UNCONFIRMED generator Findings with episodes inside those days. From the run log: 10-06
08:00-09:00Z, 11-02 09:30-09:45Z and 10-21 08:00-09:00Z. `mini_depth` returned 0 rows.

**How a site lead reads it.** A Finding is a claim about one episode, judged on its own evidence. On a real Site a
Finding often falls on a day that is only partly checked. "Needs attention" next to "only part of today is checked"
is honest, and it is how a site lead triages. s602b is different. On the Finding's own day, the generator measure that
the Finding moves has zero counted evidence, and the board says the day has no checked readings. A site lead reads
that as "you judged a day you say you did not check", or as "the checking is broken". This is not a legitimate design:
two producers disagree about the same generator hour. The likely cause is in the fixture. s602b's dispatch runs come
from the S3-01 Performance comparison path, which stores no `analytic_run_evidence` rows. But nothing in the product
prevents the combination, so it counts as a product inconsistency.

**The demo build does not show it.** On both demo builds, every generator Finding falls on a PARTIAL day with counted
evidence:

| Site | Finding days | `avoidable_gen_min` grade | Covered |
|---|---|---|---|
| KOBO-001 | 10-23, 10-30, 11-06 | PARTIAL | 29,100 s |
| KISIWA-001 | 10-28, 10-29 | PARTIAL | 32,700 s and 32,400 s |

The Kobo NO_DATA days (10-27, 11-02, 11-04 and early October) have no in-window Finding.
`assetops_demo3_kisiwa_test` shows PENDING on the Kisiwa days, but it is an intermediate database that was never
settled, not a presented build. So no presented beat shows the case today.

One risk remains. The demo Kobo declares an MG-2 objective ("avoidable generator minutes at most 0", BOARD_DAY), and
`mini_readings` judges it from the dispatch read, not from the snapshot. In principle a NO_DATA day could therefore
read "On track". E4 checks this (below).

**Why there is no product fix now.** The right fix is at the producer: the measure a Finding moves must count that
Finding's evidence. A mask on the board would hide one producer's output behind the other's. Either fix changes the
board or the chain under every mini screen, two days before E3, for a case the demo build does not contain. That is
the corner the owner warned against cutting. The E4 check proves the demo build is clean, and BL-63 carries the fix.

**Builder changes (tests only, `backend/tests/test_out_b4_board_postgres.py`):**
1. `test_kobo_guardrail_two_board_days`: replace the loop asserts at `:430-438`. Keep the CATEGORIES assert and the
   MG-8 pop. For each of `a` and `b`:
   - Assert that `measured` equals the exact dict the board returns. Copy that dict in full from a focused run into
     `S602B_STATES`, with MG-8 removed.
   - Assert the reasons on the wire (`board.py:888`): MG-2's `reason` is `"PRIMARY_FINDING_OPEN"` and MG-4's is
     `"SECONDARY_FINDING_OPEN"`.
   - Assert `LAST_PORTS[key]["chain_day"] == {"settled": True, "readiness": "NONE", "gaps": 31}`. Either capture the
     port right after each `_board` call, or move this assert after the overview loop that records `chain_day`.
   - Replace the comment with: "D-E2.9: since CH-5a1 the states come from the in-window Findings over the chain day,
     not from the STALE_PROJECTION overview. s602b stores no counted dispatch evidence, so the same day grades
     NO_DATA. That contradiction is BL-63, held by `test_kobo_s602b_no_judgement_on_unchecked_day` (strict xfail)."

   The asserts after the loop (F01 MOVES, SAFEGUARD, Action keys, the ACT index) stay unchanged. The first failing
   assert stops the test today, so they never run. Now they must run and pass. If any of them fails, stop.
2. `test_kobo_estate_finding_rows_and_states`: make the same change for the 10-21 board. Pin the exact recorded dict
   with MG-8 popped, the two reasons and the `chain_day` port. If the dict differs from `S602B_STATES`, put it in a
   second constant.
3. Add `test_kobo_s602b_no_judgement_on_unchecked_day(kobo_guardrail, monkeypatch)`, marked
   `@pytest.mark.xfail(strict=True, reason="BL-63: a Finding-driven state on a day whose moved measure has no counted
   evidence")`.
   - Read both boards (10-06 and 11-02).
   - For each board, read the latest stored `avoidable_gen_min` grade for that Site-local day from
     `site_day_snapshot` (`DISTINCT ON (local_day, measure, subject_ref) ... ORDER BY revision DESC`).
   - If the grade is NO_DATA or PENDING, or there is no row: assert that no outcome on the board has a `reason`
     starting with `PRIMARY_FINDING_` or `SECONDARY_FINDING_`, or equal to `OBJECTIVE_MET`, `OBJECTIVE_MISSED` or
     `OBJECTIVE_ON_PACE`.

   Today the test must report XFAIL. When BL-63 lands it will XPASS, which fails the run, and the mark comes off.
4. Run focused on the host (`tools\run-host-tests.ps1`, on `assetops_test` only). `test_out_b4_board_postgres.py`
   must show these two tests passed, the new test as 1 xfailed, and every other test as before. Record the pinned
   dicts in the packet.

**E4-GE (new E4 item, no code).** Run on the E3 build, before E6:
- (a) Read-only SQL. For every Finding head with mechanism `GENERATOR_SUPPORT_CANDIDATE` on a mini Site (KOBO-001,
  KISIWA-001), the Site-local day of `episode_start` must have a latest `avoidable_gen_min` row with
  `covered_seconds > 0` and a grade that is neither NO_DATA nor PENDING. Use the query the Architect ran on g1audit,
  and record it in the E4 notes.
- (b) Read-only board check. Read `GET /api/sites/{code}/outcome-board?date=D` for every Kobo and Kisiwa day the demo
  script opens, and for every Kobo day from D7 to the last story day. On any day whose `avoidable_gen_min` grade is
  NO_DATA or PENDING, no MG-2 or MG-4 outcome may have a reason in `PRIMARY_FINDING_*`, `SECONDARY_FINDING_*`,
  `OBJECTIVE_MET`, `OBJECTIVE_MISSED` or `OBJECTIVE_ON_PACE`.
- A hit on a day the script opens is a High, and E6 waits. A hit only on a day the script does not open is a Medium
  for the owner walkthrough list. Either way, BL-63 is promoted.

### R-2 G-h: the cause is the test's normalizer, not the clock. Fix the normalizer and transform the pins. Do not freeze `_BASE` and do not re-capture. (D-E2.10)

**Diagnosis.** `_Norm` (`test_k6b_fuel_verification_postgres.py:124-153`) has two faults:
- It makes every value relative to the effective day but leaves dict keys absolute (`{k: self(x) ...}`). The
  `grades` map is keyed by date over `LOOK_DAYS = 14` (`verification_families.py:51`), so its keys move with the wall
  clock.
- It treats the rule's declaration date as a story date. `TARGET["declared_by"] = "owner 2026-11-05"`
  (`verification_families.py:55-56`, CH9b1-R P1) is a constant the owner declared, yet it reads `<d-3>` on 11-08 and
  `<d-4>` on 11-09.

The verdict, the counts and the values do not move (packet capture). The effective day follows the real clock:
`at()` sets the COMPLETE `occurred_at`. The fixture also reads the DB clock (`_now(engine)` for `raised_at`,
`test_ch9b1...:52-60`), and the store stamps rows with DB time.

**Why not freeze `_BASE`.** Freezing `_BASE` puts the Action's completion on a fixed past date while `raised_at` and
the store stay on the DB clock. One story would then run on two clocks, the failure family FIX-W401b fixed, and the
completion could fall before the Action was raised. On a real Site one clock orders these events. The test has to
keep them on one clock and compare relatively.

**Why not re-capture.** The pins prove that the mill path is byte-equal to its state before K6b (d25f95ccb). A new
capture would lose that proof. A mechanical transform of the original file keeps it.

**Builder changes (tests only):**
1. `_Norm.__call__`, dict branch: `{(self(k) if isinstance(k, str) else k): self(x) for k, x in v.items()}`.
2. `_Norm.__call__`, string branch, as its first line: `if v == fv_families.TARGET["declared_by"]: return v`. Import
   `assetops_backend.actions.verification_families` as `fv_families`, or reuse the import if it already exists. A
   change to the declared rule is a product change that the pin must catch, so the date stays literal.
3. `fixtures/k6b_mill_pins.json`: edit it by hand or by script. Do **not** use `K6B_CAPTURE_PINS`. The capture's
   effective day is 2026-11-08: the commit time is 2026-11-08 06:25 +0300, and the baseline COMPLETE days 11-05 to
   11-07 read `<d-3>` to `<d-1>`. Make these changes:
   - Rewrite the `grades` keys `"2026-10-25"` to `"2026-11-07"` as `"<d-14>"` to `"<d-1>"`.
   - Rewrite the three `"owner <d-3>"` values as `"owner 2026-11-05"`.
   - Apply the same rule to any other date-shaped key.

   The file diff must contain exactly these lines. The commit message names d25f95ccb as the source.
4. In `test_5`, after `got`: assert that no key or value in `got` matches `\d{4}-\d{2}-\d{2}`, except the literal
   `TARGET["declared_by"]`. This makes independence from the wall clock checkable.
5. Run `test_k6b_fuel_verification_postgres.py` focused on the host: every test passes. Mutation proof: temporarily set
   `TARGET["declared_by"]` to `"owner 2026-11-06"`, confirm that `test_5` fails, then revert.

**Stop rule.** If today's output still differs from the transformed pins anywhere besides those lines, stop:
something other than the clock has moved.

### R-3 G-g deviation: accepted. (D-E2.11)

My spec premise was wrong. `test_ch6_nodes_postgres::test_kobo_estate_grow_nodes` builds the S4/s602b test-scoped
Kobo, not the mechanism Kobo. The builder's fix states a fact about that Site and proves it from stored data: every
`foundation_revision` has zero PRODUCTIVE loads, and the test first checks that the set is not empty. "No
productive-use equipment declared" is therefore true for that Site, and the text is K10 v2's (56256bbc9). The demo
Kobo declares its mill, which `test_walk1_productive_producer_postgres` covers.

**E4-GG (no code).** On the E3 build, the Kobo board on the ST-3 story day must not contain "no productive-use
equipment declared", and its Grow row must show the mill's sales line. A miss is a High.

### R-4 G-i follow-up: confirmed for FR-B. (D-E2.12)

`pin_read_at` (`test_w301_estate_index_postgres.py:398-410`) patches only `postgres_estate_read.EstateSnapshot`.
`EvidenceMoneySnapshot(EstateSnapshot)` (`estate/adapters/postgres_evidence_money_read.py:55`) binds its base class at
first import, so a Portfolio read under the helper depends on import order. The helper has five users: w301_golden,
w301_estate_index, w302_evidence_scope_snapshot, w303_portfolio_fixture and w303_selectors. It produces no wrong
product output, and k8 already has a local fix, so it does not block E3.

**FR-B adds** (beyond its earlier file list):
- `pin_read_at` also patches `postgres_evidence_money_read.EvidenceMoneySnapshot` with the same `present()` pin.
- k8 drops its local `_PinnedMoney` and uses the helper.
- FR-B's run targets add the five helper users and `test_k8_estate_fuel_postgres.py`, each run after one estate
  test, which is the order that exposed the hole.

The reviewer checks this with the rest of FR-B.

### R-5 E3 start

E3 starts once all of the following hold:
1. FR-A carries R-1 (test edits 1-4) and R-2 (edits 1-5).
2. Focused host runs of `test_out_b4_board_postgres.py` and `test_k6b_fuel_verification_postgres.py` are green,
   with exactly one xfail.
3. `check-all` passes 18/18.
4. A fresh Claude reviewer (Opus) accepts the whole FR-A diff. The reviewer checks each stale claim against its named
   commit, and checks that every state R-1 pins has the strict xfail beside it.
5. FR-A is merged.

No new container run is needed. The two files changed only in themselves, and every other scoped file was already
green at 52190948d. BL-63 does not hold E3. E4 adds E4-GE and E4-GG beside E4-K8 and E4-env.

### Decisions
- **D-E2.9** G-e is a real inconsistency that no presented screen shows. On s602b, a Finding-driven NEEDS_ATTENTION
  or WATCH appears on days whose generator measure has no counted evidence ("no checked readings"). The demo builds
  put every generator Finding on a PARTIAL day with counted evidence. Ruling: a bounded deferral.
  - The tests pin the recorded states, the reasons and the `chain_day` port.
  - A strict-xfail test holds the invariant.
  - E4-GE proves the E3 build is clean, including objective verdicts on NO_DATA days.
  - The producer-side fix is BL-63. A board-side mask is rejected.
- **D-E2.10** G-h: the k6b normalizer left date keys absolute and treated the owner's rule date as a story date. Fix
  the normalizer, and transform the d25f95ccb pins: the keys become relative and the rule date stays literal. Assert
  that no absolute date remains. Do not freeze `_BASE`, because that splits one story across two clocks. Do not
  re-capture.
- **D-E2.11** The G-g deviation is accepted. The test's Site is the s602b Kobo, which has no productive loads, proved
  from its stored Foundation revisions. E4-GG checks that the demo Kobo never reads "none declared".
- **D-E2.12** The `pin_read_at` import-order hole goes to FR-B. Patch `EvidenceMoneySnapshot` in the helper, drop
  k8's local pin, and run the five helper users plus k8.
- **D-E2.13** E3 starts after FR-A merges. That needs R-1 and R-2 built, the two files green with one strict xfail,
  check-all at 18/18 and the reviewer's ACCEPT. No new container run is needed. BL-63 is post-demo.

## E3 stop rulings (2026-11-09)

Claude Architect, under the owner's delegation of 2026-11-08 (`.agent/owner-away-architect-decides-2026-11-08.md`):
"let the architect make decisions if there are any input required from my side and make sure it makes decisions based
on understanding of how real sites work and what assetops is trying to achieve, no cutting corners on fundamentals".
E3 = `task/E3-demo-build` 80f4a21d4, `assetops_polish_client2_test`, S = 2026-11-07, finish check 51/51.

### STOP 1 (G-m): the builder's reading is right; the G-m premise was wrong
- Code path: `Demo.tick()` ends in `performance_and_prebuild()` (`tools/demo_combined.py:861`), which calls
  `self.story()` and reads `<self.work>/story.json`. The parity test sets `demo.work = tmp_path` and calls `demo.tick()`;
  the mill tests build `Recording(tmp_path)`, and `finish_build` -> `finish` -> `tick(times=2)` reaches the same read.
  The prepared `var/` is never read, so no prepare can make them pass. The read came in with f994e3cf9 (K9 R3s); the
  tests predate it. This is a test-fixture defect, not a product or build defect.
- What E3 already proves: the 3-Site mill order is proven by outcome. A tick before the mill step skips every mill
  cause, and the finish-check rows on `mill.json` would then fail (VERIFIED mill Action, 5 eligible days, MILL-4 thread
  line, COH-17 on the mill thread only). The one-Site plain finish is not exercised. Tick/serve `code_version` parity
  is not checked by any finish row; the prebuild's "8 hit" compares prebuild with prebuild, not tick with serve.
- Ruling: fix the tests now (option a) and add a live parity check to E4. Skipping the unit proof is a corner cut:
  only the L0 test has the keyless control that shows the comparison can fail.

### FLAG 2: Kobo `fuel_night` `eligible: true, processed: 0` is correct
- `due_nights` returns eligible when the Site has a tank asset, and a night is due only when it has tank `fuel_level`
  readings (`fuel_balance/scheduled.py` docstring: "Kobo (a tank with no `fuel_level`) gets no row"; spec §2.4 P2, P3).
- Real-site sense: Kobo runs a genset with a tank but no level sensor; diesel is known only from deliveries. A night
  balance needs a level read at both edges, so producing nothing is the honest result. Eligible means "the stage
  applies to this Site", not "a night was found". Not a defect.

### Decisions
- **D-E3.1** G-m test fix on `task/E3-gm-story-fixture` (Sonnet builder, fresh Claude Sonnet reviewer, test files only):
  1. `test_ch5c_env_parity.py::_captured_envs`: write `tmp_path/"story.json"` = `{"sites": list(tool.SITES)}` (the
     three Sites, so the Kisiwa performance branch runs too).
  2. `test_demo_combined_mill.py`: each test that reaches `finish_build(..., True, ...)` writes
     `tmp_path/"story.json"` = `{"sites": story["sites"]}` after it sets `story["sites"]`.
  3. Fix both module docstrings: the work folder is `tmp_path` holding the `story.json` that prepare would write.
  No product code changes and no assertion is weakened. The rest of BL-62 stays in the backlog. Run the two files
  (L0, seconds): all pass. Merge before E4.
- **D-E3.2** E4-env runs the fixed files in the E3 checkout (with the merged fix applied) and stays an E4 stop.
- **D-E3.3** New check E4-PARITY: with the demo server up, after one loop tick (tick plus its serve-env prebuild),
  GET the first page the demo opens (the S+0 Kobo board request). It must answer `X-AssetOps-Stored: hit`. A
  `stored` or `composed` answer means tick and serve disagree on `code_version`, and that is an E4 stop.
- **D-E3.4** FLAG 2 is not a defect. New check E4-FN: in `last-tick.json`, KOBO-001 `fuel_night` is `OK`,
  `eligible: true`, `processed: 0`, `deferred: 0`; KISIWA-001 is `OK`/eligible; COLD/EV are `eligible: false`. Then
  `SELECT count(*) FROM fuel_balance_window` for KOBO-001 = 0 (P3). Any Kobo row is a High.

## E4 stop rulings (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's delegation of 2026-11-08
(`.agent/owner-away-architect-decides-2026-11-08.md`): "let the architect make decisions if there are any input
required from my side and make sure it makes decisions based on understanding of how real sites work and what assetops
is trying to achieve, no cutting corners on fundamentals". Input: `AssetOpsV1-e3/.agent/E4-results.md` (690c54532),
code at that commit, and read-only SQL on `assetops_polish_client2_test`. **READ** = code cited; **DB** = queried.

### D-E4.1 STOP 1 (E4-PARITY): a defect. The warm list is a frozen copy of an old story calendar.

**Root cause (READ).**
- The prebuild sends every request in `config/chain/prebuilt-routes-v1.json` (`chain/prebuild.py:28-35`, via
  `file_chain_config.load_prebuilt_routes`, `:99-103`). That file is static. It was committed once in CH-5c u2
  (36d0e08de) with the note "Generated from the demo story calendar (S=2026-10-31)". No generator exists in the repo,
  and neither `prepare` nor `add-dates` writes the file. So every build since S moved has warmed October boards that no
  script opens. Parity itself holds: 20 of 20 listed routes hit.
- This is also a miss in the Q7 audit (§7.1): a product config file carries demo-story dates.
- **Real-site sense:** the warm list exists so that the pages people open next answer at once. On a real Site those
  pages are the latest days and this week. In the demo they are the pages the script opens. A list that warms neither
  does no useful work. The presenter's first open of each story board then pays a compose of 5 to 9.5 s.

**Fix: product root plus tool.** Branch `task/E4-C2-prebuild-follows-calendar`, Opus builder, about 0.75 unit.
1. **Product.** `chain/adapters/file_chain_config.load_prebuilt_routes` reads the file named by
   `ASSETOPS_PREBUILT_ROUTES` when that variable is set. The schema is the same (`chain/prebuilt.parse`). When it is not
   set, it reads the config default.
   - Do **not** add the variable to `chain/watermark.COMPOSER_ENV` or `SERVE_KEYS`. The list chooses what to warm and
     never changes a body.
   - Test, new `backend/tests/test_e4_prebuilt_routes_source.py`, no DB:
     - with the variable set, `prebuilt_requests()` returns the file's requests;
     - without it, the default;
     - `code_version()` is equal with and without it (clear the `lru_cache`);
     - the name is not in `COMPOSER_ENV`.
2. **Tool.** In `tools/demo_combined.py`, add a pure function
   `prebuilt_routes(story, days, kisiwa, sites_last_day)`.
   - It derives the requests **from `story_links`'s own rows**, so what is warmed equals what the script opens, by
     construction.
   - It maps each web link to the stored-route API request(s) its page issues, with the exact query the frontend
     sends:
     - Portfolio (`lens=all`);
     - outcome-summary;
     - Findings (`lens=all&state=all`);
     - each `/sites/{code}` board to `/api/sites/{code}/outcome-board`, with the same `date=` or `from/to`.
   - It also adds each Site's board for every date from S+1 to that Site's last added date (Kobo by `date`). The story
     step 7 day is then warm as soon as the tick after its release ends.
   - The tool writes `<work>/prebuilt-routes.json` before every prebuild (`performance_and_prebuild`) and at `serve`
     start. It sets `ASSETOPS_PREBUILT_ROUTES` in `serve_env`, so both the tool's prebuild and the serve loop's prebuild
     read the file.
   - Tests, no DB (in `backend/tests/test_own_g1_add_dates.py` or a new file):
     - S=2026-11-07 gives a `board.day` request for every story-day link, plus the week, S and month estate requests;
     - no date falls outside the story calendar or the added dates;
     - the file is rewritten when the last added date moves.
3. **Config default.** It stays as it is, for the existing tests and `chain_watermark_guard.py`. **BL-64 (post-demo):**
   replace it with a relative production list (the latest local day per Site and the current week, anchored on DB now).

### D-E4.2 STOP 2 (Cold/EV "Pending"): a defect. The Portfolio reads thread state at the evidence cutoff.

**Root cause (READ + DB).**
- `estate/portfolio.attach_threads` (`:144-162`) reads each Cold/EV row's thread state with `known_at` set to the
  Site's **evidence cutoff**: `cutoffs[site_code]`, from `select_finding_scope` (`estate/index.py:151-156`,
  `site_cutoff`). That cutoff is `max(ingestion_disposition.decided_at)`, the Site's last reading.
- CH-6b2 R2 (cb73f7409) ruled the opposite for lifecycle reads. `chain/read.lifecycle_cutoff` says the evidence cutoff
  bounds evidence only, and the request cutoff `k` bounds a thread's lifecycle. That commit changed the board
  (`chain_api.py:185-187`) and the claims (`chain/claims.py:84, 97`). It missed the Portfolio.
- DB, EV: the last reading is 2026-11-03 09:00Z. The ACTION_IN_HAND event has `cause_known_at` 11-03 09:40Z, after
  that reading. So the event is never visible, and the row reads OPEN.
- DB, Cold: the ACTION_IN_HAND event is at 11-07 17:15Z. The Cold rows read "Pending" only once add-dates wrote readings
  after that instant. Cold's last `decided_at` is now 11-09 17:09Z.
- So R4.1's label code is right; the state it is given is wrong. Neither stale storage nor the prepare order is the
  cause.
- **Real-site sense:** an action agreed after the last reading is still agreed. A cold room whose logger is quiet is
  the case where the manager most needs to see that someone is acting, and bounding the state by the last reading hides
  exactly that case.

**Fix.** Branch `task/E4-C1-portfolio-lifecycle-cutoff`, Opus builder, about 0.25 unit.
- In `estate/portfolio.attach_threads`, read every row's thread state and Action segments at
  `lifecycle_cutoff(default)`, as one group rather than one group per Site.
  - `day_at` (`req.to - 1µs`) and `visible_at` (`default`) are unchanged.
  - Set `_thread_cutoff` to the same value, so `action_segment_for` stays consistent.
  - Update the comment to cite CH6b2-R2.
  - Keep the `cutoffs` parameter for its callers; it no longer bounds the lifecycle.
  - Mini-grid rows are unchanged: their cutoff was already `default`.
- Tests: a new no-DB file, `backend/tests/test_e4_portfolio_lifecycle_cutoff.py`, with a fake `threads` port that
  records its kwargs:
  - (a) a Cold row whose evidence cutoff is earlier than `k` is read with `known_at == k`;
  - (b) the same row, with the fake state `ACTION_IN_HAND`, gives `workflow_label` "Pending";
  - (c) an EV row behaves like (a) and (b);
  - (d) a mini row's call is unchanged.
- Run `test_ch2_threads.py`, `test_ch3_rows.py`, `test_ch5a1_r1_visibility.py`,
  `test_w303_portfolio_workflow_labels.py` and `test_r4_domain_row_thread_state.py`.
  - An assertion that pinned a Cold/EV state at the evidence cutoff may be updated, and is listed in the packet.
  - Any other changed assertion is a stop.
  - Occurrence visibility (CH5a1-R2 R-1) must not move.
- **Proof on the fresh build, before any add-dates.** On the Portfolio week link, both Cold start-failure rows and the
  EV row read "Pending". The Cold temperature row reads "No action yet".

### D-E4.3 STOP 3 (E4-GE any-outcome sweep): all 4 hits are correct behaviour; the sweep's test was too strict

**Kobo 10-28 and 11-05, MG-1 OBJECTIVE_MET (READ).**
- MG-1 is the only monthly measure (`outcomes/objectives.py:46, 61`).
- `judge_month` judges it over the Site-local month **up to the board day** (`chain/outcomes.py:108-123`). No later day
  is read.
- MET means the month-to-date kWh has already reached an at-least target. Missing days can only add to the total.
- The row text says so: "{mtd} kWh so far this month, on {c} of {e} days checked" (`chain/vocabulary.py:275`).
- **Real-site sense:** a site lead reads "the month's target is already reached; today's readings are not in yet".
  Both are true, and both are on the screen.
- This is not the BL-63 case. BL-63 is a day-scoped verdict (MG-2/MG-4) on a day whose own measure has no counted
  evidence.

**Kisiwa 11-01 and 11-02, MG-8 PRIMARY_FINDING_OPEN (DB).**
- On both days `critical_served` is COMPLETE (82,800 s) and `daylight_headroom_kw` is PARTIAL. Only
  `avoidable_gen_min` is NO_DATA.
- The Finding is the unexplained-fuel night. Its own measure, the night's fuel balance, is graded.
- By D-E2.9's principle (a Finding is judged on the evidence of the measure it moves), this is honest.

**Ruling: no High and no fix.**
- E4-GE(b) is restated for every later run: "no outcome may carry a Finding or objective reason on a day where **that
  outcome's own measure** has no counted evidence over **its judged span**".
- The judged span is the board day for MG-2/MG-4, the month up to the board day for MG-1, and the Finding's night or
  episode for a Finding reason.
- DS-1a presenter note for the Kobo 10-28 beat: "The monthly target was already reached; this day's readings had not
  arrived yet. Both are on the screen."

### D-E4.4 Items E4 did not run

**(a) COH.** There is no number to invent. The finish check's F-COH and F-COH3 rows are the COH gate, and both pass
(51/51). Closed as PASS.

**(b) Forced unfinished Kisiwa night.** This check is still required: on a demo morning the catch-up must never write
a night that has not ended.
- Run it at the next E4-lite, before 15:00 local:
  1. `add-dates --site KISIWA-001 --to <today-1> --dry-run`;
  2. then the same command without `--dry-run`.
- Expected: "night not over yet" and NIGHT_NOT_OVER. The Kisiwa evidence and `fuel_balance_window` counts do not change
  (take a snapshot before and after).
- Any write is a High.
- Meanwhile the unit pins (`test_own_g1_add_dates.py:179, 611`) stand. This check does not block E5.

**(c) Perf: the budgets, now named.**
- **PF1.** After one serve tick and its prebuild, every API request behind every `links` row answers
  `X-AssetOps-Stored: hit` on first open. This replaces the single-page check in D-E3.3.
- **PF2.** Each of those hits answers in 1.0 s or less (`curl` time_total).
- **PF3.** A serve tick with no new data has prebuild states `stored: 0` and `prebuild_ms` of 120,000 or less.
  - The limit is the product's own EX-3 rule: 50% of `TickLimits.tick_seconds` (240 s; `scheduling/tick.py:87, 303-306`).
  - The observed 134-149 s were data-arrival ticks. A data-arrival tick over 120 s is recorded, not a stop.
  - A no-data tick with `stored` above 0 is a stop: it means the watermark moved without data.
- **PF4.** Report the composed (cold) Portfolio week read and the slowest board. Either one over 15 s is a Medium for
  the walkthrough. PF1 keeps cold reads off the presented beats.

### D-E4.5 Re-prepare: yes, once C1 and C2 have merged

- Neither fix changes stored data. But the `tree` under `var/polish_client2/tree` is a code snapshot, and R6.3's runbook
  rule stands: "Never replace or edit a build's `tree`. New code means a fresh `prepare`."
- R4.1 must be proven on a **fresh** build before any add-dates. Only a fresh prepare can prove that.
- So: one fresh E3 prepare from main after both merges (about 2 h 12 m, machine idle). No demo patch, and no tree swap.

### D-E4.6 Observation, not an E4 stop: the board gap line over-states on Kisiwa

- `site_outcomes/mini.py:133, 361-385` counts a day as "no checked readings" when its **weakest** measure is NO_DATA.
- On Kisiwa from 11-01 to 11-07, `critical_served` is COMPLETE. Even so, those days are counted as having no checked
  readings ("28 of the last 31 days").
- A real manager reads that line as "the gateway was down", which is false.
- **Ruling: an honesty defect on a presented board. Fix it with two tiers.**
  - Days with no counted measure keep `GAPS_NO_READINGS`.
  - Days where some measures are counted read "{p} of the last {n} days {verb} only partly checked".
  - Branch `task/E4-C3-gap-line-tiers`, Sonnet builder, about 0.5 unit.
  - Tests: the `finding_gap_line` cases and the IDX-GAPS pins. List any capture change.
- C3 joins the re-prepare only if it is reviewed and merged when C1 and C2 are. Otherwise it is a Medium on the owner
  walkthrough list and lands in the Sun-15 build. It never holds E5.

### D-E4.7 Order of work

1. C1 and C2 build in parallel, and each gets a fresh Opus review; only High or Medium findings block. C3 builds
   alongside them on Sonnet. Merge, then run check-all on main.
2. A fresh E3 prepare from main (one heavy job).
3. E4 again, in full. It includes D-E4.2's proof before any add-dates, D-E4.3's restated GE(b), and PF1-PF4.
4. E5 screenshots (1440/390), then the DS-1a refresh (the R4.1 lines and D-E4.3's note), then the owner walkthrough.
   Item (b) runs at the first morning E4-lite.

### Decisions logged for owner review

- **D-E4.1** The warm list follows the story calendar. It is derived from the script links, and the product reads it
  from a deployment input. The production default goes to BL-64.
- **D-E4.2** The Portfolio reads a thread's lifecycle state at the request cutoff, as the board does. Cold/EV "Pending"
  then shows on a fresh build.
- **D-E4.3** Two cases are honest: a monthly "met" on a no-data day, and a fuel Finding on a day whose generator measure
  is unchecked. The sweep is restated per measure.
- **D-E4.4** COH is closed by F-COH and F-COH3. The resume check runs at the next E4-lite. The perf budgets are
  PF1-PF4.
- **D-E4.5** A fresh prepare after the fixes; no tree swap.
- **D-E4.6** The gap line separates "no checked readings" from "only partly checked".

