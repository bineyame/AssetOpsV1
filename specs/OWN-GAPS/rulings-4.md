## E4 L2 ruling (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's delegation of 2026-11-08. Input: C2 review
L2 (`AssetOpsV1-c2/.agent/C2-review.md`), the E4 serve logs (`AssetOpsV1-e3/var/polish_client2/logs/39..111-*`), code on
main 0c8f7f668 and C2 7c71854c7, and read-only SQL on `assetops_polish_client2_test` (`chain_input_change`,
`chain_response`). **READ** = code cited; **DB** = queried; **LOG** = serve logs.

### D-E4.8 The per-tick rebuild is a defect: the serve loop moves `F` with no new data

**Root cause.**
- **No data arrived (LOG + DB).** Every serve tick from 92 onward reports `processed: 0` at every stage of every Site
  (s4 `SKIPPED_UNCHANGED_FENCE`; Kisiwa `fuel_night` re-reads 7 nights and writes nothing). The last
  `chain_input_change` row is 17:17:56Z; the ticks at 17:30-18:16Z wrote none. The serve loop ingests no simulator
  readings: data arrives only through `add-dates` and drains.
- **The DB watermark is stable; only `F` moves (DB).** In `chain_response`, successive rows for one request key carry
  the same `cic:` count (estate `cic:1130129`, Kobo `cic:675643`) and a different `|f:` term on each tick. The Sites
  whose `F` is stable (Cold, EV) are the 8-9 hits.
- **What moves `F` (READ).** `tools/demo_combined.Demo.tick` ends with `performance_and_prebuild` (`:842-867`), which
  reruns `performance_migration run` for KOBO-001 and KISIWA-001 on **every** tick. Each run writes a new timestamped
  report under `{evidence}/migration-performance/{site_key}/` (LOG: `97-performance.log`, `98-performance.log`). That
  directory is a declared `F` root (`config/chain/file-inputs-v1.json`, hashed by size and `mtime_ns` in
  `chain/adapters/file_inputs.file_state`). So every estate request (`F` over all Sites: 7 routes plus 3 scope-ids) and
  every Kobo and Kisiwa board misses. That is the 14-15 stored. The tool's own docstring says so: "a new report moves
  `F`".
- **The correction to D-E4.4(c).** The 134-149 s ticks were recorded there as data-arrival ticks. They were not: they
  were no-data ticks. Under PF3 as written they are a stop (`stored` above 0 on a no-data tick), which is what PF3 was
  for. The store and watermark rules are right; the tool feeds them a false change.
- **Real-site sense.** A comparison that re-reads unchanged evidence has nothing new to say. On a real Site the
  Performance gate is rerun when the evidence it compares has changed, not on a timer. Rerunning it on a timer turns a
  quiet store into a full rebuild every two minutes, and a presenter's click during that rebuild lands on a cold compose
  or a race.

**Fix card E4-C4: Performance comparison only on change.** Branch `task/E4-C4-performance-on-change`, cut from the C2
head (it edits the same file); merges after C2. Sonnet builder, about 0.25 unit. Tool only; no product code changes.
1. In `tools/demo_combined.py` `performance_and_prebuild`, run `performance_migration run` for a Site only when
   `performance_due(site, mark, marks, report_dir)` is true. This is a new pure function. It returns true when any of
   these holds:
   - the Site has no report file under its `migration-performance/{site_key}` directory;
   - `<work>/performance-marks.json` has no mark for the Site;
   - the recorded mark differs from `mark`.
2. `mark` is the Site's DB watermark, read **before** the run with the same predicate as
   `chain/adapters/postgres_response_store.read_watermark` for that one Site: the tenant's rows for the Site plus the
   tenant-wide NULL rows. Use one short read-only connection to the build's DB. Record `mark` after a run that exits
   0. Reading it before the run is the safe direction: a write during the run forces a rerun next time. Write the marks
   file atomically, as C2 does for the routes file.
3. Print one line per Site: `performance: skipped (no change since mark N)` or the run's last line, as now.
4. The prebuild still runs every tick, as now. With `F` quiet, it is a store hit for every request.
5. Tests (new `backend/tests/test_e4_performance_on_change.py`, no DB):
   - `performance_due` is true with no report, true with no mark, true on a changed mark, and false on an equal mark
     with a report present;
   - with a fake `py` and a fake mark reader, two `tick()` calls on an unchanged mark run `performance` once and
     `prebuild` twice;
   - a changed mark between the two calls runs `performance` twice;
   - a failed run (non-zero exit) records no mark.
   - Run `test_demo_combined_finish_rows.py` and the C2 tests. Any changed assertion is listed in the packet.
6. **BL-65 (post-demo).** Have `performance_migration` write a new report only when the comparison differs from the
   newest report. The product would then be quiet on its own, whoever schedules the comparison.

### D-E4.9 PF3, measured honestly

- **A no-data tick** is a serve tick for which (i) every Site's DB mark is equal before the tick and after its prebuild,
  and (ii) no `add-dates`, drain or other writer ran in that span. The E4 run records the four marks with read-only SQL
  around at least **three consecutive** serve ticks, and those ticks are PF3's sample.
- **On a no-data tick** the prebuild must show `stored: 0`, `race: 0`, and every request a `hit`. Its `prebuild_ms`
  must be 120,000 or less, the EX-3 rule. The expected figure is under 15 s (45 hits at about 50 ms, plus the child's
  start). `stored` above 0 is still a **stop**: with C4 in place it means something other than data moved a watermark.
- **A data-arrival tick** is the first prebuild after `add-dates` or a drain. It rebuilds the estate requests and the
  changed Sites' boards. That is legitimate: the store's watermark is Site-wide by design (W2/W4), so late data
  re-checks history.
  - The prebuild that follows `add-dates` (and each post-drain prebuild in `prepare`) is recorded, not budgeted. The
    gate is PF1 after it.
  - Any **other** data-arrival tick over 240 s (one full tick: it would overrun the next) is a Medium.

### D-E4.10 C2's longer list stands; no scoping down

- C2's 42 requests are `story_links`'s own rows, plus the S and month estate requests and each Site's boards from S+1
  to its last added date. The script links already **are** the DS-1a dates. The S+1 tail is one or two days per Site.
  These are the days a real manager opens first, and the step 7 day is among them. Cutting the list would move cold
  composes of 5-9.5 s onto presented beats, which is the failure D-E4.1 fixed.
- **Live-demo cost after C4.** A no-data tick is all hits (seconds). The full rebuild of about 5-6 min happens once,
  after the morning `add-dates`.
- **Prepare cost.** Each post-drain prebuild grows to about 5-6 min, about 10 min more in total on a run of about
  2 h 12 m. It is offline on an idle machine, and accepted.
- **Presenter rule (DS-1a runbook line, added at the DS-1a refresh).** Run `add-dates` at least 10 minutes before
  presenting. Do not open the first link until a `prebuild:` line after it shows `stored: 0` (the store is quiet). A
  click before that point is still correct, only slower.
- Pages outside the list compose on demand and are measured by PF4, as ruled.

### D-E4.11 Order (amends D-E4.7)

1. C4 is built and reviewed (fresh Claude review; only High or Medium findings block). It merges after C2 and before
   the fresh prepare.
2. The re-prepare (D-E4.5) waits for C1, C2 and C4.
3. The E4 rerun measures PF3 by D-E4.9.

### Decisions logged for owner review

- **D-E4.8** The rebuild on every tick is a tool defect. The serve loop reran the Performance comparison on a timer,
  and each new report moved the file term. The fix reruns it only when the Site's data changed.
- **D-E4.9** PF3 is measured on ticks proven quiet by the DB marks. The rebuild after `add-dates` is recorded, not
  budgeted.
- **D-E4.10** The full story-derived warm list stays. The presenter waits for one quiet prebuild after `add-dates`.

## E3b stop ruling (2026-11-10)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's delegation of 2026-11-08. Input:
`AssetOpsV1-e3b/.agent/E3b-results.md` and `var/polish_client3/check.json` (8b13c7f95), code on main da68db6d4, and
read-only SQL on `assetops_polish_client3_test`. **READ** = code cited; **DB** = queried.

### D-E3b.1 Root cause: the board's thread lookup still reads the lifecycle at the evidence cutoff

**The board side (READ).**
- `site_outcomes/read.py` `board()` (`:470-495`) reads each listed Finding's thread with
  `known_at=cutoff`, where `cutoff = window["known_at"]`.
- For cold/EV, that value is `board_cutoff` (`:897`), which is `site_cutoff`. That is the window's last reading
  (`decided_at`), bounded by `k`.
- So the outcome-board reads the lifecycle at the **evidence** cutoff. This is the read CH6b2-R2 ruled out.

**The Portfolio side (READ).** After C1, `estate/portfolio.attach_threads` reads at `lifecycle_cutoff(k)`.

**The other readers (READ).** The `/chain` route (`chain_api.py:185-187`) and the claims (`chain/claims.py:84, 97`)
already read at `k`.

**My error.** D-E4.2 cited `chain_api.py:185-187` as "the board". That is the `/chain` route, not the outcome-board
composer. So C1 moved the Portfolio to `k` and left the board behind. The C1 review's L3 ("they agree at read time")
was wrong for the same reason.

**What F-COH requests (READ).** `_coh` calls `cc.collect(..., known_at=None)`, so both sides get the live request.
- The board resolves its cutoff to the window's last reading.
- The Portfolio resolves it to the envelope `k`.

**DB: all 8 mismatches are explained.**

| Site | Evidence cutoff | Thread events | Board sees | Portfolio sees |
|---|---|---|---|---|
| EV | 11-03 09:00Z | OPEN 09:35Z, ACTION_IN_HAND 09:40Z | neither: (None, None) | ACTION_IN_HAND |
| Cold, 11-07 window | 17:05Z | thread 3eef: OPEN on 11-04, ACTION_IN_HAND 17:15Z | OPEN | ACTION_IN_HAND |
| Cold, 11-07 window | 17:05Z | thread 8adc: OPEN 17:10Z | (None, None) | OPEN |

- EV gives 2 mismatches: the week and month windows.
- Cold gives 6: 2 threads in each of the week, S and month windows.

**Why client2 passed 51/51.** Before C1, both sides read at the evidence cutoff. They agreed because both were blind.
The board listed a Finding whose thread had no state at all.

**Verdict.**
- The **board** is wrong.
- The **check** is right. It caught the gap as soon as one side was fixed.
- The **Portfolio** (C1) is right.

**Real-site sense.**
- A Finding is always known after the evidence it assesses. A reading cutoff therefore hides the Finding's own
  opening, and any action agreed after it.
- A manager who opens EV on 11-03 must see that someone agreed an action that day, at 09:40Z. The time-travel
  honesty comes from the state **day** (`state_on(evs, board_day)`, each event's effective day), not from the
  reading cutoff.
- A board that lists a fault with no state, while the Portfolio says "Pending" for it, contradicts itself on the
  presented beat. R4.1's "Pending" intent holds on both screens only once the board reads at `k`.

### D-E3b.2 Fix card E4-C5: the board reads thread lifecycle at `k`

Branch `task/E4-C5-board-lifecycle-cutoff`, cut from main da68db6d4. Opus builder, about 0.5 unit. Fresh Claude
review; only High or Medium findings block. Do the pre-flight questions before writing code.

1. **Product.** In `site_outcomes/read.py` `board()`, pass `known_at=lifecycle_cutoff(known_at)` (the raw request,
   as `chain_api.py:185` does) to `self.s.threads.lookup`.
   - `visible_at=known_at` is unchanged (CH5a1-R2 R-1).
   - `day=board_day` is unchanged.
   - `facts.known_at` and every evidence read stay at `cutoff`.
   - Mini boards do not change, because `board_cutoff` is already the request's cutoff for mini. The opportunity
     read stays at `cutoff`.
   - Update the comment at `:472-475` to cite CH6b2-R2 and D-E3b.1.
   - The pre-flight confirms that no other board-side lifecycle read (Action refs, thread lines, `dated_lead`) uses the
     evidence cutoff. If one does, it moves to `k` in this change and is listed. Evidence reads never move.
2. **Check (fundamental: no agreement in blindness).** Extend `tools/checks/chain_coherence.py` COH-13. In a
   lifecycle-stamped bundle, a board or Portfolio thread on a **listed** Finding with `state` None is a finding:
   "listed Finding with no thread state".
   - Add one fixture to `tools/checks/test_chain_coherence.py` (the both-None pair fires).
   - Any existing fixture that relied on None is listed in the packet.
3. **Tests.**
   - New no-DB `backend/tests/test_e3b_board_lifecycle_cutoff.py`, with a fake `threads.lookup` that records its
     kwargs:
     - (a) a cold board with an evidence cutoff earlier than the request reads with `known_at` equal to the request
       value (None when live);
     - (b) an EV board behaves the same;
     - (c) a mini board's call is unchanged.
   - Run `test_ch2_threads.py`, `test_ch3_rows.py`, `test_ch5a1_r1_visibility.py`, `test_ch5a2_contract.py`,
     `test_e4_portfolio_lifecycle_cutoff.py`, `test_r4_domain_row_thread_state.py`, `test_chain_coherence.py` and
     `test_demo_combined_finish_rows.py`.
   - Rule for changed assertions:
     - An assertion that pinned a cold/EV **board** thread state at the evidence cutoff may change, and is listed.
     - Any other changed assertion is a stop.
     - Occurrence visibility must not move.
4. **In-process proof before the prepare (cheap; the machine is idle).** From the C5 worktree, run the finish rows
   F-COH and F-COH3 in-process against `assetops_polish_client3_test` / `var/polish_client3`. That DB is discarded
   and is a `*_test` DB.
   - Pass condition: F-COH passes, with the EV 11-03 and both Cold 11-07 pairs present and equal.
   - This is the gate for item 5, not a demo patch. client3's `tree` is never edited.

### D-E3b.3 Rebuild path

- Another full prepare is required: client4, from main after C5 merges, about 2 h 10 m on an idle machine.
- Reasons:
  - R6.3 forbids editing or replacing client3's `tree`.
  - The demo build must serve the fixed board code.
  - R4.1 must still be proven on a fresh build before any add-dates (D-E4.2's proof, plus: the EV 11-03 board and the
    Cold 11-07 board show those Findings as "Action agreed"/in hand).
- Nothing short of that proves the build. The in-process proof (D-E3b.2 item 4) only guards against wasting 2 h.
- client3 is retired. Do not serve it.
- D-E4.4(b), the forced unfinished Kisiwa night, runs on client2 as the coordinator proposed.
  - Snapshot before and after.
  - client2 already has add-dates through 11-09, so the only pending night is the unfinished one.
  - Run it before 15:00, never concurrently with the prepare.
- Order: C5 build and review, then the in-process proof, merge, check-all, prepare client4, the full E4 rerun
  (PF1-PF4, GE(b) per D-E4.3), then E5, DS-1a and the walkthrough.

### Decisions logged for owner review

- **D-E3b.1** The board, not the Portfolio, was wrong. My D-E4.2 ruling missed the board composer's thread read.
  Client2's earlier pass was agreement in blindness.
- **D-E3b.2** The board reads thread lifecycle at the request cutoff. COH-13 now refuses a listed Finding with no
  state.
- **D-E3b.3** A fresh prepare after C5. client3 is retired. The Kisiwa resume check runs on client2.

## Any-range speed ruling (2026-11-10)

- Architect: Claude (fresh `assetops-architect`). Full answer, measurements and design:
  `.agent/architect-answer-any-range-speed-2026-11-10.md`. Owner question verbatim:
  `.agent/owner-any-range-speed-2026-11-10.md`. Owner away, verbatim: "no cutting corners on fundamentals".
- Measured on client2, store off, cold: Kobo board day 11.2 s, Kisiwa board day 11.3 s, Cold board week 1.6 s,
  Portfolio week 12.1 s, Portfolio 10-12..10-19 4.2 s, Portfolio month 36.1 s. 80-85% of a mini board is the on-read
  hourly currentness re-fingerprint; the Portfolio is per-Site-day dispatch, claim and provenance recompute. Day
  snapshots themselves read in 2-160 ms.

### D-ANY.1 The full fix is BL-66, and it reverses CH5c-R2's substitution

The page cache (CH-5c option A) stands in for the stored daily read model the owner asked for on 2026-11-03. BL-66
moves every range-bound read onto revisioned per-period rows rebuilt per event through the existing register (cards
AR-0 to AR-6, 6.75 units, slices ANY-1 and ANY-2). ANY-2 is demo-critical if the owner sets the client session after
it can land; the date is the owner's.

### D-ANY.2 Pre-demo partial step: slice ANY-1 (boards), after FR-B

AR-0 (parity and arbitrary-range speed guard, 0.5), AR-1 (read-row foundation, 1.0), AR-2 (board mini depth on rows,
1.5): 3.0 units. It is the first slice of the real fix, not a workaround. It starts after FR-B (Wed 11 to Fri 13)
merges and does not displace it. Done when every mini-grid board day composes in 2 s or less cold with the store off,
and AR-0 parity holds byte for byte on the story requests and seeded random days, live and historical.

### D-ANY.3 No range-agnostic warm-up and no longer pre-load list

Pre-building more pages on data arrival cannot cover arbitrary ranges, multiplies the Site-wide rebuild after each
`add-dates`, and is thrown away by BL-66. Refused. D-E4.1 and D-E4.10 stand unchanged until AR-5 retires the list.

### D-ANY.4 Presenter rule until the fix lands

At the walkthrough, at FR-B and at any client session before ANY-2: stay on the script's ranges, and use the
Portfolio selector only for the pre-built week, S and month. Off-script, the presenter says the range is being
computed and moves on. The owner is shown the measured numbers before the walkthrough.

### Decisions logged for owner review

- **D-ANY.1** The full fix (BL-66, 6.75 units) replaces the page cache as the speed mechanism.
- **D-ANY.2** ANY-1 (boards, 3.0 units) is built before the client session, after FR-B.
- **D-ANY.3** No warm-up of more pages.
- **D-ANY.4** Presenter stays on script ranges until the fix lands.

## E5 rulings (2026-11-10)

This section was written by the Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). It works under the owner's delegation of 2026-11-08 ("no cutting
corners on fundamentals"). The owner can be reached today and will do the walkthrough this afternoon, so owner calls are listed separately and are not ruled here.

Inputs:
- `AssetOpsV1-ds1a/.agent/E5-captures.md` (c252b6cf3) and its `e5/text/*.txt`;
- the DS-1a draft on `task/DS-1a-client-script`;
- client4 (`assetops_polish_client4_test`, `var/polish_client4`, S = 11-08, tree code b234cea2a);
- `AssetOpsV1-e3c/.agent/E4b-results.md`.

**READ** means the code is cited, from main d5549feb6. `git diff b234cea2a main` over `frontend/src backend/assetops_backend host contracts config tools/demo_combined.py` is empty, so main's code is client4's code. **DB** means a read-only query on client4.

### D-E5.0 How a fix reaches client4 without a rebuild (READ)

- **The backend serves from the frozen tree.** `serve` starts uvicorn with `cwd=<work>/tree/host` (`tools/demo_combined.py:1477-1479`), and the tree is a `git archive` of the build commit (`:825-840`). A fix to the backend, `config/`, `host/` or `contracts/` therefore needs a new prepare. R6.3 still holds: the tree is never edited or replaced.
- **The frontend is not served from the tree.** `serve` prints "Frontend, from frontend/: npm run dev" (`:1495`), and E5 ran Vite from the e3c checkout.
- **`code_version` does not cover the frontend.** It hashes the alembic head, the backend sources, `config/`, `host/**/*.py` and `contracts/**` only (`chain/adapters/file_code_version.py:3`). A frontend change therefore touches neither the tree nor any stored page.
- **`tools/demo_combined.py` runs from the checkout.** Its `links` command is also outside `code_version`.
- **So:** a frontend or `links` fix applies by restarting Vite, and re-running `links`, from a checkout at the fix's merge. **No item below needs a rebuild of client4.**

### D-E5.1 STOP-1, "Yesterday arrives": R4.2 stands for demo day; today no Site has a day to release

**Root cause (READ and `days.json`).** S is the prepare day minus 2 (`demo_combined.py:12-13`). On 11-10, no Site has a finished day that has not been added yet:
- Kobo's story days run to S+1 (11-09, `trial-after`).
- Kisiwa's story nights also run to S+1 (`story_links`, "S-9d to S+1d"; the E4b dry-run gave `KISIWA-001: []`).
- E4b already added Cold 11-09.
- EV adds data on Tuesdays only, and 11-09 is a Monday.
- Today, 11-10, has not ended.

The product and the tool are working correctly. The build is one day too young for this beat.

**General rule, added to R4.2 item 2.** The live beat exists only when yesterday is later than S+1. That means the session date must be at least S+3, which is the **prepare date + 1**. A build prepared on the session day never has the beat.

**Demo day.** R4.2 is unchanged: Kobo's yesterday is held back and the script wording stays. Using Cold or Kisiwa instead is refused:
- a Cold day shows no change the client would notice;
- holding Kisiwa back would clash with the live-dip night (D-E5.2).

**Today's walkthrough.** Step 7 is shown in words, with the two honest stand-ins:
- 05, captioned "A day whose readings have not arrived yet (10 Nov)";
- 04, captioned "A checked day (9 Nov)".

They must never be captioned as the before and after of one day. The presenter says the real release is rehearsed tomorrow, in E5b.

**E5b** is an agent run on client4 on Wed 11 Nov, after Kobo-local midnight. It changes no product code and writes only add-dates data and one dip:
1. Run the morning runbook from R4.2 item 2: `add-dates --site COLD-LAB-001,EV-LAB-001,KISIWA-001 --no-check`, up to 11-10. EV adds its Tuesday. The Kobo command `--to 11-09` refuses with `STORY_DAY`. Confirm this with `--dry-run`, then run the first command again without `--no-check`.
2. Capture the "before" view: `/sites/KOBO-001?date=2026-11-10` at 1440 and 390, recording the board's words.
3. Run `add-dates --site KOBO-001 --to yesterday --no-check`. Time it from start until "KOBO-001: added" prints; R4.2 item 4's 11-minute rule is decided on this number. Reload the same URL and capture the "after" view.
4. Save the live dip (D-E5.2). Then run plain `add-dates`, which ends with the finish check; a FAIL retires client4. Then one tick, the prebuild, and PF1 on the `links` rows (every request must be a hit).
5. Take the D-E5.5 capture: the OPP-000003 page. Write the results to `.agent/E5b-results.md` on `task/E5-captures`.

### D-E5.2 STOP-2, the dip: no dip on client4 today; a real save is rehearsed in E5b; no fixture pictures in the client script

**Root cause (READ and E5).** R1.4 ties the dip to the newest *added* Kisiwa night and to the value `links` prints (`added_night_links`, `demo_combined.py:1456-1459`). client4 has no added Kisiwa night (D-E5.1), so no night is safe. Three options are refused:
- **A story night.** Every Kisiwa night in client4 is a story night. A dip there would honestly re-check that night and could change the ACT-004 verdict (R1.4 presenter note).
- **Tonight (11-10).** A dip there would sit in a night that later receives simulated tank data, and could create unexplained fuel that does not belong to the story.
- **Any other night.** None exists.

**Ruling.** §5.3 says the after-submit state is captured only in G3b fixtures, never on the demo DB. That is **amended for E5b only**:
- E5b saves one dip through the Operational records form, which uses the product's entry route (`service:operator-entry`).
- The dip goes on the newest added Kisiwa night from E5b step 1, at 06:00, with the value `links` prints.
- Capture, at 1440 and 390:
  - the form after the save;
  - the records list showing the dip as "Submitted", "Entered by site admin";
  - after the next tick, that night's Fuel page, checked again.

This is exactly the session's beat. At the session the newest added night will be a later one, so the rehearsal dip simply stays as one more true record.

**Order.** E5-FX (D-E5.3) merges and Vite restarts on it before the E5b dip, so the list shows the fixed labels.

**Client script.** The `*-FIXTURE.png` pictures are never used: they show another Site and other values (REC-041, 198 L). If E5b is not done before DS-1f, step K has no saved-dip picture.

### D-E5.3 STOP-3, `service:w401-fixture` in the By column: a product display defect; frontend fix, no rebuild

**Root cause (READ).**
- The prepare seeds every story record through `WorkService` in process, with `PRINCIPAL = "service:w401-fixture"`: Kisiwa `demo_combined_kisiwa.py:719, 772`, Kobo `:172`, EV `:109`, mill `:35-36`. This is the documented actor for example records (`demo_combined.py:14-15`, `work_api.py:48`).
- The list renders `actorLabel(row.actor_id)` (`OperationalRecords.tsx:213`). That function maps only `service:operator-entry` (`:89-91`) and prints any other ID as it is stored.
- R30 (W6-01 E2) accepted stored actor IDs at a time when no client screen existed.

**Why the seeding path is not changed.** Re-seeding the story records through the entry route would:
- claim the site admin typed records that the prepare created;
- be unable to place them at their story `recorded_at`;
- need a rebuild.

It is refused.

**Card E5-FX, part A.** Branch `task/E5-FX-actor-label-links` from main. **Sonnet**. Parts A and B together are **0.25 unit**, including a fresh Claude light review; only High or Medium findings block.
- Change `actorLabel` in `frontend/src/work/OperationalRecords.tsx`:
  - `service:operator-entry` → "Entered by site admin" (unchanged);
  - `service:w401-fixture` → **"Prepared example record"**;
  - any other `service:` ID → "Entered by a system service";
  - any other value is unchanged.
- `data-global-work-actor` keeps the raw ID as a test hook; it is not visible.
- Add the comment `MOCK DEVIATION MD-E5-1` and register row **R714**. R714 amends R30 for the By cell only; WorkRequestHistory's "Stored actor" disclosure (R39) is unchanged.
- **Tests.**
  - `frontend/src/work/__tests__/operationalRecords.test.tsx` gains the three mappings.
  - An assertion that pinned the raw `service:w401-fixture` By text may change; list it in the packet. Any other changed assertion is a stop.
  - Run that file and `operationalEntryForm.test.tsx` only; no full suite.
- **No rebuild needed** (D-E5.0): restart Vite from a checkout at the merge.

### D-E5.4 The Kobo finding link pins revision 1 of 3: a `story_links` defect; drop the pin

**Root cause (READ and DB).**
- `story_links` builds `?revision_id={kobo['finding_revision']}` (`demo_combined.py:320`).
- `kobo.json` stores the revision current when the Action was raised: `fc457881`, revision 1, 11-08 12:07.
- The Finding then gained two `BASIS_REFRESHED` revisions at story times, 11-08 14:02 and 11-09 12:07, with the same claim (200 candidate minutes). This is correct product behaviour, not tick churn.
- Version 1 says "Earlier version ... not the current answer" and "No current amount can be shown". The script describes the current conclusion and its cost.
- R2-DS1a 2 kept the pin because it was the revision the script describes; that no longer holds. **R2-DS1a 2 is superseded.**

**Card E5-FX, part B.**
- `tools/demo_combined.py:320` links to `/sites/KOBO-001/findings/{kobo['finding']}` with no query string.
- Update `backend/tests/test_demo_combined_links.py:56`, and run that file.
- The pre-built route list is unaffected, because it is built with `kobo=None` (`:424`).
- No rebuild: `links` runs from the checkout.

### D-E5.5 The Kobo opportunity hop lands on OPP-000005: the product is right; E5 used the wrong route

**READ.**
- The board's Grow option is "Productive-use what-if". It goes to the Site's financial scenarios (`site_outcomes/mini.py:589`), then to Renewable evaluation and OPP-000005. That page is the headroom study, and it honestly says "Five-day study incomplete".
- On 11-09 the board's Grow potential reads "No potential found yet". The midday-solar opportunity, OPP-000003 "Daytime solar unused at Kobo mini-grid", was seen on 3-7 Nov, outside that day.

This is not a defect.

**Ruling.**
- The script's opportunity page is **OPP-000003**. It is reached from Findings › Opportunities on the story week (capture 07) or from the Portfolio Grow card.
- The presenter never takes the hop from the board's what-if.
- E5b captures the OPP-000003 page at 1440 and 390, from 07's row.
- OPP-000005's header, "Global Findings unavailable ...", is system wording, but it is off the script path: backlog Low, not demo-critical.

### D-E5.6 "4.50 USD" is not stale; the Portfolio writes it as "$4.50"

**READ.** The line is the Portfolio context footer (`EstatePortfolio.tsx:731`). Capture 01 has it at line 350: "Depot Charging Hub delivered 15 kWh in selected records; $4.50 at the recorded tariff, before costs (a what-if)". E5 searched the EV board for "4.50 USD"; the EV board only points to Financials.

**Ruling.**
- Keep the value. Quote "$4.50" exactly as the screen writes it, and attribute it to the Portfolio, not the EV board.
- The Portfolio page mixes "$" and "USD": backlog Low, not demo-critical.

### D-E5.7 DS-1f brief (Sonnet, after E5b; fresh Opus light review)

- **All steps.**
  - Quote dates as story days. Take real dates and every href from `links` on the session build.
  - Replace the draft's hard-coded checklist hrefs with `links` placeholders; for example the step 2 Finding `b824c41c...?revision_id=...`, dated "6 Nov".
  - Keep the "rehearsal build" caption.
- **Step 1.** Crop from 01 (the act-first view and the outcomes grid). The "$4.50" footer line goes here.
- **Step 2.** Use the finding picture from **03b** (the current version), never 03.
- **Step 3.**
  - Crop 02's Grow row, E5b's OPP-000003 page and 07. Never use 06.
  - The placeholder "the midday mill opportunity page" becomes "the daytime solar opportunity page".
  - Quote "Daytime solar unused at Kobo mini-grid" and "Size not worked out yet".
  - The "about 17 USD a day" figure is ACT-005, taken from 01.
- **Step 3b.** Kept. Crop 02's cost row with the screen's qualifier: "counted at a generic idle fuel rate of 3.3 L/h, not measured".
- **EV step.**
  - Keep the board crop from 10.
  - Move the "What you see" bullet with "$4.50" to step 1, or mark it "on the Portfolio".
  - "If asked" quotes "$4.50 ... (a what-if)".
- **Step K.**
  - The saved-dip picture comes from E5b only; without E5b, there is none.
  - Presenter line: "Records marked 'Prepared example record' came with the example site; the one I save now is listed as entered by the site admin."
- **Step 7.**
  - The backup pictures are E5b's before and after of the same Kobo day.
  - Caption: "Kobo board, one day, before and after its readings arrived (rehearsal)".
  - Add the D-E5.1 rule to the runbook: the beat exists only when the session is at least one day after the prepare.

### Decisions logged for owner review

- **D-E5.1** Yesterday-arrives stays as Kobo's held-back day on demo day. It needs a session at least one day after the prepare. Today it is walked with honest stand-ins, and E5b rehearses it for real on 11-11.
- **D-E5.2** No dip on client4 today. One real rehearsal dip goes on the newest added night in E5b. Fixture pictures are not used in the client script.
- **D-E5.3** Example records read "Prepared example record" in the By column. This is a frontend fix; no rebuild.
- **D-E5.4** The Kobo Finding link opens the current version.
- **D-E5.5 and D-E5.6** Neither is a defect. The opportunity route and the "$4.50" attribution are script corrections.

### Questions for the owner (not ruled)

1. **On-screen dip today.** It cannot be done honestly on client4 today. Would you rather watch the E5b rehearsal tomorrow, or see its pictures?
2. **Label wording.** Records that came with the example sites will read "Prepared example record". Keep this, or use other wording on a client screen?
3. **Session date and build.** Please confirm the client session date and which build serves it. The live beat needs a build prepared at least the day before.

## DS-1f anomaly rulings (2026-11-10)

Claude Architect (binding Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's 2026-11-08 delegation. Code READ at e3c `5e46dae89` (= client4 code); DB = read-only queries on `assetops_polish_client4_test`.

### D-E5.8 Cold third visit: product defect (Cold composer lacks the linked-Finding resolve); fix with the rebuild

- **Facts (DB).** Backup generator: WR-000007 10-15, WR-000008 10-28, WR-000006 11-08, all COMPLETE. Only WR-000006 links a Finding (`3733fcfd…`, COLD_START_FAILURE, rev 1 OPENED/SUPPORTED, never closed). Cold also has a clean assessment pair for **11-09** (created 11-10 05:26 by the E5 add-dates/tick), with no Findings.
- **Rule (READ).** `outcomes/warnings.py:_repeated` fires on ≥2 completed visits to one asset in `[to-60 d, to)` with at least one linked Finding open in `open_findings`. The board 08 (day 11-08) shows it correctly: "3 visits (15 Oct, 28 Oct, 8 Nov)".
- **Root cause.** 09b uses the window `S-28 d .. S+3 d` (`demo_combined.py:293`). The estate summary reads Cold over that period, `cold_findings` returns only the *selected* (latest) assessment's Findings (`postgres_assessment_store.py:2548`), i.e. the clean 11-09 pair, so the still-open start failure is absent from `open_findings` and the warning is dropped. The card then claims "None found at GreenHarvest", a false all-clear. EV already resolves linked Findings that the selection lacks (`site_outcomes/ev.py:149-162`, addendum 3 (d)); Cold does not (`site_outcomes/cold.py:121-135`). The S shift exposed it only because a post-S Cold day now sits inside the window. Not the warning's window or rule.
- **Ruling: defect.** **Fix card FX-COLD-LINKED (Opus, S, ~60 lines):** `site_outcomes/cold.py` mirrors the EV block: for each visit/action-linked Finding id missing from `findings`, read it through a new `ColdPorts.finding` (bound in `site_outcomes/read.py:cold_ports` to `cold_reads.finding`); a refused read unsettles CC-3 and lists `cold_findings` in `reads.failed`. The read must return the Finding's current revision as of `known_at` independent of the selected assessment; if `cold_reads.finding` filters by the snapshot, add an id read that does not. Check mini for the same gap (report, do not widen). Tests: a backend unit test with a later clean assessment in the window (warning still fires, cites WR-006); a Postgres summary test over a window that contains a clean post-failure day. **Backend: needs a rebuild.**
- **Script.** Before the rebuild, never use the S+3 d window for this beat: take Maintenance with `from=S-28 d&to=S+1 d`. Wording: "The maintenance page flags the backup generator: three visits in 60 days, and the automatic start failure is still open."

### D-E5.9 EV "connector 2": data/story defect (fixture literal); fix with the rebuild

- **Root cause (READ).** `tools/w504_ev_work_cases.py:52` hard-codes `ACTION.title = "Investigate connector 2"` (a v6.9 mock literal). The registered replay `ev-interrupted` faults connector c1, and the board derives "Connector c1" from data (`ev.py:connector_name`). The product renders both correctly.
- **Ruling: defect in the story data.** **Fix card FX-EV-TITLE (Sonnet, XS):** set the title to "Investigate connector c1"; update `backend/tests/test_w504_ev_work_cases.py`, `test_w504_ev_intent_api.py`, `test_w504_ev_work_producer_postgres.py` and the frontend EV fixtures (`evWorkFixtures.ts` and its tests) that assert the literal. Tools-only code, but the title is stored in the DB, so **client4 keeps the old title; it needs the rebuild.**
- **Script.** After the rebuild: "ACT-003 · Investigate connector c1". On client4 (presenter note): "The example action's title says connector 2; it was raised from this connector c1 fault."

### D-E5.10 One rebuild

Merge FX-COLD-LINKED and FX-EV-TITLE (fresh Claude review each), then prepare one new build on 11-11 (~2 h 20 m). It also satisfies D-E5.1 for a Thursday session. E5b and the DS-1f picture retakes (09b, 10) run on that build.

### Decisions logged for owner review

- **D-E5.8** The missing Cold notice is a product defect (false "None found"); backend fix and rebuild.
- **D-E5.9** "Connector 2" is a fixture typo; fixed in the same rebuild.
- **D-E5.10** One rebuild on 11-11 and E5b moves to it. Owner may veto and keep client4 with the stand-in wording above.

## Kobo gap-pattern ruling (2026-11-10)

Claude Architect (binding Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's 2026-11-08 delegation. Owner text: `.agent/owner-kobo-gap-pattern-2026-11-10.md` ("1 missed day with 1 partly missing would make sense"). Code READ at main `04bbb1b80`. DB = read-only queries on `assetops_polish_client4_test` (S = 11-08) and `assetops_polish_client2_test` (S = 11-07). Nothing was run or built.

### D-E5.11 Root cause: the v3 calendar, not the product (READ + DB)

The week S-6..S comes straight from `backend/conversions/demo-story-days-v3.json` (`sd.DEFAULT_FILE`):

| Day (S = 11-08) | v3 entry | What it reads | Deliberate? |
|---|---|---|---|
| S-6, S-5 (2, 3 Nov) | `steady` (3 runs tile 00-24) | COMPLETE 24 h | yes (MILL-3 later days S-8, S-6, S-5) |
| S-4 (4 Nov) | **no entry** | NO_DATA | **no**: side effect |
| S-3 (5 Nov) | `late` as `normal` | PARTIAL 8 h | the late kind is a calendar choice; no script beat uses it |
| S-2 (6 Nov) | **no entry** | NO_DATA | **no**: side effect |
| S-1 (7 Nov) | `normal` | PARTIAL 8 h | carries finish row WK-2a (42.08 USD) only |
| S (8 Nov) | `trial-before` | PARTIAL 8 h | **yes**: ACT-001 baseline |

- **Why S-4 and S-2 are empty.** `resolve` refuses a `late` day inside a multi-day stream (`LATE_IN_STREAM`, `tools/demo_story_days.py:390-395`), so DD1a2-R Q4 left both neighbours of the late S-3 unbuilt and logged the fix as BL-25 ("no shown claim needs those two days", `build-sheet-DD-1.md:817-821`). That reason no longer holds: the Portfolio week now shows them.
- **Why exactly 8 of 24 h.** The story-only kinds replay registered Lab scenarios that run 03:00-11:00Z, i.e. 06:00-14:00 local (`kinds.kobo.normal/overuse/trial-*`: `start D+0d 03:00`, `end D+0d 11:00`). No gateway behaviour causes it. DD1a1-R16 made the necessary-run (N) and trial (R30/R25) days story-only: N is RUNNING at 14:00 and 24:00, and R30/R25 are RUNNING at 24:00, so no honest rest-of-day or night could be joined (`build-sheet-DD-1.md:680-713`). Only the mill and steady chains passed, which is why only `steady*` and `mill-midday` days read 24 h.
- **Deliberate beats in or near the week:** the trial pair S/S+1 (ACT-001, the "Verified" headline), the weekly generator days S-28/S-21/S-14/S-7 (story-only by R16), the `missing` day S-10 (the FILL-1 beat), and the mill change S-9 with its later days S-8/S-6/S-5. **Side effects:** S-4 and S-2 (BL-25), and the 8 h reads on S-3 and S-1.
- **S-dependence: none for the pattern.** Every Kobo offset is S-relative; only EV has a weekday rule (`SITE_WEEKDAY`). client2 (S = 11-07) shows the same shape one day earlier: 1-2 Nov COMPLETE, 3 and 5 Nov NO_DATA, 4, 6 and 7 Nov PARTIAL. Only month boundaries move with S. (K7-D/K7-F are Kisiwa plan steps, `demo_combined_kisiwa.py:804`; they do not touch Kobo days.)

### D-E5.12 The fix: calendar v4, S-4 missed, S partly checked, five full days

**`backend/conversions/demo-story-days-v4.json`** (becomes `DEFAULT_FILE`; v3 kept as history, as v1 and v2 were). It is a copy of v3 with three entries changed in the week:

| Day | v3 | v4 | Reads |
|---|---|---|---|
| S-4 | none | `{"day": "S-4d", "kind": "missing"}` ("gateway offline: no run, no delivery") | NO_DATA, the week's one missed day |
| S-3 | `late` as `normal` | `steady` | COMPLETE |
| S-2 | none | `steady` | COMPLETE |
| S-1 | `normal` | `steady` | COMPLETE |
| S | `trial-before` | unchanged | PARTIAL, the week's one partly checked day |

All other entries, kinds and the trial block stay byte-equal. Label and status are updated to say "v4 (D-E5.12)".

- **Why S is the partial day and not a few-hour dropout.** S is ACT-001's baseline. Filling it needs either a rest-of-day run inside S's UTC day after the baseline pin, which moves the selected run and takes the trial off Verified (the DD1a2-R3 H1 mechanism), or a night run whose 06:00 end does not match the trial's declared start. Neither can be made safe tonight, so S stays 06:00-14:00. Presenter line: "8 November is the trial day. Its example readings cover 06:00 to 14:00, the hours the trial needed, so the day reads partly checked." A real few-hour dropout day needs the BL-18 source-time cut (Kobo `degraded` is held, `DEGRADED_PROBE`). That is backlog.
- **Why S-4 is the missed day.** It is already "4 Nov, not assessed" in the scripts, so the script change is smallest. It keeps the gap away from the trial pair: the trial reads only S and S+1, and the Finding on S does not touch S-4, so the PARTIAL Portfolio still lists it (CO-6). `missing` is the existing, honest kind.
- **Why this is safe (READ).**
  - `steady` uses `night-early` (the fresh declared start) and `mill-rest`. The same chain is already built back to back on S-6 and S-5, so `check_full_day`, `check_full_day_chains`, `check_mill_side` (offset > S-9) and `_tiled` pass by construction. S-1's runs end at S-1 21:00Z, outside S's UTC day, so the trial baseline is untouched. `FULL_DAY_AFTER_TRIAL` concerns S+2 only.
  - No `late` entry remains, so `LATE_IN_STREAM` cannot fire. The late-delivery path is still shown live by script Step 7 (add-dates) and is still covered by the existing L0 tests, which now load `V3_FILE`.
  - MILL-3 is unchanged: `choose_days` takes the first 3 COMPLETE days nearest the change (`verification_families.py:85-89`), still S-8, S-6, S-5. The baseline S-13..S-11 and the pinned study S-19..S-15 are unchanged. ACT-005 stays 17.00 USD.
  - No post-change five-day study becomes SUPPORTED: every window from S-8 to S+1 contains S-7 (partly checked), S-4 (missed) or S (partly checked), so each stays UNKNOWN (`projection.frozen_result`).
  - The extra build time is about +5 min: 3 full days (about 131 s each) replace 2 story-only days (about 38 s each).
- **Fallback with no code revert:** `prepare --days backend/conversions/demo-story-days-v3.json` rebuilds the old pattern. The restated rows below are written to pass on both calendars.

### D-E5.13 Fix card FX-KOBO-GAPS (Opus, S, about 0.5 unit / about 150 lines; fresh Claude review; parallel with FX-COLD-LINKED, no shared files)

Branch `task/FX-KOBO-GAPS`.

1. **Data.** Add `demo-story-days-v4.json` as in D-E5.12. In `tools/demo_story_days.py`, set `DEFAULT_FILE` to v4 and add `V3_FILE`. Update the manifest label `"days"` in `tools/demo_combined_kobo.py:563` to the v4 path.
2. **L0, `backend/tests/test_demo_story_days.py`.**
   - Tests that need a `late` entry or v3's table (`:52`, `:96`, `:109`, `:174`, `:322`, `:510-525`, `:583-612`, `:769`) load `sd.V3_FILE` explicitly. They are not deleted.
   - New `test_v4_story_week_one_missed_one_partial`. For S in {11-07, 11-08, 11-09}, `resolve(load(), S, installs=...)` gives, on S-6..S: exactly one day with no run (S-4, kind `missing`); exactly one story-only day (S, `trial-before`); five days whose runs tile [00:00, 24:00) local; and no `late` entry. Assert also that `DEFAULT_FILE.name == "demo-story-days-v4.json"` and that v4 minus the 4 week entries equals v3 minus its 2 week entries.
   - Must-fail: the same test run against v3 fails.
3. **New finish row `WK-GAP`** (`tools/demo_combined_finish.py`, `idx=True`), with a pure helper `demo_rows.week_gap_pattern(grades_by_measure)` and its own L0 test. Use a must-fail fixture that is client4's real pattern (2 NO_DATA + 3 PARTIAL) and must fail.
   - The row reads Kobo `site_day_snapshot` (latest revision per day, measure and subject) for `critical_served`, `daylight_headroom_kw`, `productive_kwh` and `avoidable_gen_min` on [S-6, S].
   - It asserts, for every measure: NO_DATA on exactly {S-4}; PARTIAL on exactly {S}; COMPLETE on the other five days.
   - It also asserts the served Portfolio week: the Kobo days line reads "5 of 7 days checked · 1 partly checked", and the CO-6 coverage `gaps == [S-4]`.
   - It derives the expected days from `ctx.site_days("kobo")` (the `missing` kinds and the story-only kinds) and never hard-codes dates, so on a v3 fallback it reports the v3 pattern and fails, which is the intended alarm.
4. **Restated rows (cause: D-E5.12; not edited to pass).**
   - **WK-2a.** The S-1 Grow headline is still "estimated productive-use sales". Its money follows S-1's kind: `steady` gives 110.000 kWh × 0.25 = **27.50 USD**, and `normal` (v3) gives 42.08. Docstring: "a mill-working steady day".
   - **WK-2b.** The potential on S follows the study ending S. If that study has ≥ 1 eligible day, the potential reads `LIMIT_UNKNOWN` ("Not judged yet: 2 of the 5 study days …", for S-4 and S), with no kW and no money. With 0 eligible days it reads "No potential found yet" (v3). The other WK-2b clauses are unchanged.
   - **WK-6.** Fix the docstring/comment only ("its v3 November days are 8 h runs").
5. **Copy (client-visible, caused by this change).** `chain/vocabulary.py:24` `LIMIT_UNKNOWN` gets a singular form: "1 of the 5 study days has no reading". The study 3-7 Nov will now have one empty day. Update the test(s) that pin the literal.
6. **Gates.** Guards A, W, V and N; `test_demo_story_days.py`; the new helper's L0; the vocabulary test. No full suite (demo-sprint policy). `python tools/demo_combined.py`'s offline resolve/`--check` on v4 must pass.
7. **Stop rules on tonight's build.** If WK-GAP, WK-2a, WK-2b, F-COH, F-CAL, SP-3, SP-4 or the `demo_combined_after.py` reads fail, stop, do not tune, and report to the Architect. One difference is allowed and must be reported, not treated as a failure: the mill thread's RECURRED effective day may move earlier, because the study ending S-4 now holds eligible days from S-8. `recurrence_holds`' hard-coded `"2026-10-31"` is S-dependent (it runs only in `--s2` mode), and the report gives the value read. The fallback is the v3 `--days` rebuild.

### D-E5.14 Downstream figures (for the DS-1 scripts after the fresh build; expected values, confirm from the build)

These are for S = 11-08. If the fresh prepare lands S = 11-09, every date moves +1 day and the month figures are given in brackets. Each is "expected", by the same arithmetic the technical script uses. The build's numbers decide.

| Where | client4 now | After FX-KOBO-GAPS |
|---|---|---|
| Coverage line (client `:350`, technical `:535-538`, opening `:984`) | 5 of 7 days assessed · 2 days not available yet · not assessed: 4 Nov, 6 Nov | **6 of 7 days assessed · 1 day not available yet · not assessed: 4 Nov** |
| Days line under the cards (technical `:541-544`) | 2 of 7 days checked · 3 partly checked | **5 of 7 days checked · 1 partly checked**. Estate: 22 expected, 5 complete, 1 partial, 3 low, 13 no data |
| Grow card (client `:351`, technical `:547-550`, `:628`) | 139.16 USD over 2 of 7 · 3 partly | **137.50 USD** = 5 × 27.50 + 0.00 (S), "over 5 of 7 days checked · 1 partly checked" |
| MG-1 line (client `:474`, technical `:556`) | 556.7 kWh so far this month, on 2 of 8 days checked | **550.0 kWh on 5 of 8 days checked** (110 × 5 + 0 on 1 Nov + 0 on 8 Nov) [S = 11-09: 660.0 kWh on 6 of 9]. Target 300, so still **MET / On track** |
| Daytime-solar study 3-7 Nov (client `:472`) | Seen on 1 of 1 · 4 of the 5 study days have no reading | **Seen on 4 of 4 well-observed days · 1 of the 5 study days has no reading** |
| Kobo board potential on S (WK-2b) | No potential found yet | **Not judged yet: 2 of the 5 study days have no reading** |
| Board gap line (31 days) | 11 no checked readings · 7 partly checked | **10 · 5** (S-30, S-29, S-27..S-22, S-10, S-4; partly S-28, S-21, S-14, S-7, S) |
| Unchanged | | Generator Finding 8 Nov 04:35-07:55 and 0.00-15.13 USD; ACT-001 3.3 L / 4.12 USD, Verified; ACT-005 17.00 USD; MILL-3 "Target met"; Protect 2; Assure 3; Kobo stays PARTIAL, so its Portfolio row is still "Partly checked"; Kisiwa, Cold and EV all unchanged |

**Month view.** It improves but is not clean. On the 30 days [S-29, S]: 16 checked (now 13), 5 partly checked (the four weekly generator days S-28, S-21, S-14, S-7, plus the trial day), 9 with no data. The no-data days are the install day, a 6-day block S-27..S-22 that B-22 never built, S-10 (the FILL-1 beat) and S-4. Presenter answer: "The example starts at commissioning on 10 October. The first week has two example days, and from 19 October the readings run daily apart from two gateway-outage days. The weekly generator days carry only the example hours." Filling S-27..S-22 (`steady-before`, about +13 min of build) would also create new pre-change studies, so it is not tonight's work. It is offered to the owner below.

### D-E5.15 Order

FX-COLD-LINKED and FX-KOBO-GAPS build in parallel (no shared files), each gets a fresh Claude review, then both merge, then one fresh prepare (D-E5.10). The DS-1 script figures are refreshed from that build's finish/after output, not from the table above.

### Decisions logged for owner review

- **D-E5.11** The 2-missed/3-partial week is a calendar side effect (BL-25 and the R16 8-hour story-only days), not a product fault.
- **D-E5.12** v4: S-4 is the missed day ("gateway offline"), and the trial day S is the one partly checked day (06:00-14:00, the trial hours), not a few-hour dropout. S-3 loses its `late` kind, and S-3, S-2 and S-1 become full steady days.
- **D-E5.13** Fix card FX-KOBO-GAPS (Opus, S), with a new WK-GAP finish row, WK-2a/WK-2b restated with cause, and a singular "has no reading".

### Questions for the owner (not ruled)

1. "On the trial day the example readings cover 06:00 to 14:00 only, so that is the week's partly checked day. Is that acceptable? Making it look like a short gateway dropout instead needs simulator work after the demo."
2. "The month view still has a 6-day stretch with no readings just after commissioning (12-17 Oct), and the weekly generator days read partly checked. Leave it as is (recommended), or fill those 6 days for about 13 more minutes of build time?"

## Kobo days amendment (2026-11-10)

Claude Architect (binding Claude, `.ai/ROLE_CONFIG.md:9` on main), under the owner's 2026-11-08 delegation. Owner text: `.agent/owner-kobo-gap-pattern-2026-11-10.md` ("is it possible to inject days and extend the scope (or can i just select dates that has longer spans)?"; 12-17 Oct: "Fix it now"). Read at main `2121e3712`: `config/scenarios/kobo-*.yaml`, `backend/conversions/demo-story-days-v3.json`, `kobo-night-handover-v1.json` (`full_days`), `tools/demo_story_days.py`, `tools/demo_combined_finish.py`, DD1a1-R16, DD1a2-R, DD1a2-R3, DD1b2-R Q0/Q3 in `build-sheet-DD-1.md`. Nothing was run. This amends D-E5.12/D-E5.13; everything not named here stands.

### D-E5.16 Longer spans: not available; DD1a1-R16 still holds (READ)

- **No longer recording exists.** The Lab keeps no recorded Kobo runs: every Kobo day is re-simulated at prepare from a registered scenario. Of the 23 Kobo scenarios, none runs longer than 12 h. The trial (`kobo-mini-grid-reserve-trial`), necessary-run, prolonged, stop-60, reserve-matters and degraded scenarios run 8 h (06:00-14:00). The evening run is 12:00-20:00, and the daytime, mill, steady and steady-before runs are 06:00-18:00. A 24 h day exists only as a stitched chain (night 00-06, day 06-18, rest 18-24). Only 3 chains have a measured join that is STOPPED at every seam (`full_days`): `kobo-mill-midday`, `kobo-steady-day` and `kobo-steady-before-mill`.
- **Choosing other dates does not help.** Every Kobo offset is relative to S, so moving S moves the whole pattern (D-E5.11).
- **Why R16 still holds.** Its facts are about the scenarios and the model profile, and neither has changed:
  - The necessary-run (normal and overcast days) is RUNNING at 14:00 and at 24:00.
  - The R30 and R25 trial runs are RUNNING at 24:00 (from 22:05 and 23:25).
  - So wrapping a normal day's background around 06:00-14:00 needs a run that starts with the generator RUNNING, or a cut through a running generator. The first needs simulator work (option B, about 1-1.5 units). The second would be a dishonest join.
  - The trial adds a second bar (DD1a2-R3, BL-26): any other readings inside the trial days' UTC windows take ACT-001 off Verified.
  - A rest-of-day run on any generator day would add generator minutes. That changes the Findings and the 0.00-15.13 USD idle-fuel range.
  - A different scenario for the trial is a different trial, so the Verified headline would no longer be the measured one.
  - Verdict: the trial and generator days stay story-only (06:00-14:00).
- **A realistic few-hour dropout is not available.** The only truncation mechanism is Kobo `degraded`, which is held (`DEGRADED_DAY_HELD`): it cuts by batch order, which no real outage looks like, and the source-time cut is BL-18. There is a second reason too. The trial day S is in the week and can only be partly checked, so a truncated full day would make a second partly checked day. **S stays the week's one partly checked day.** The presenter line of D-E5.12 stands.

### D-E5.17 Injecting days: yes, through the product's ingest path; fill S-27..S-22 now

- Injecting is what the build already does. Each calendar entry replays its runs through the gateway publication, acceptance and assessment path, exactly as for the existing full days. No reading is written directly.
- **Fill S-27..S-22 (12-17 Oct for S = 11-08) with the existing before-mill chain:**
  - S-27 is `steady-before-first`. Its neighbour S-28 is story-only with no measured 24:00, so it takes the fresh declared night (Q8.1).
  - S-26..S-22 are `steady-before`. Each night starts from the previous day's measured 24:00, the same chain already built on S-19..S-15.
  - This passes `check_full_day`, `check_full_day_chains`, `check_mill_side` (all before S-9) and `_tiled` by construction.
  - Every day is after install (S-29) and inside the board window (30 days).
  - The 06:00 disclosure line applies as on every full day.
- **No new study is created.** Two new five-day windows have no missing day (S-27..S-23 and S-26..S-22), but no code queues them. Studies are pinned by `reconcile` on S-19..S-15 only (DD1b2-R Q3, BL-32), and the tick's scan reaches only studies ending about S-3 or later. So no new potential, Opportunity or Grow thread appears. The D-E5.14 month note that "it would also create new pre-change studies" is withdrawn.
- **MILL-3 is unchanged.** `choose_days` takes the complete days nearest the change: S-13..S-11 before and S-8, S-6, S-5 after. ACT-005 stays 17.00 USD.
- **Two side effects are expected, not measured:**
  - S-28..S-11 becomes one gateway stream, so the epoch strings of S-21 and S-14 change. Their readings do not change.
  - The before pattern adds about 42 kWh of daylight mill use per day: about +252 kWh and +63.00 USD in October productive use, wherever an October total is read.
- **Not filled:**
  - S-29, the install day.
  - S-10, kept as the FILL-1 live beat.
  - S-4, the week's one missed day ("gateway offline").
  - The generator days S-28, S-21, S-14 and S-7, and the trial days S and S+1 (D-E5.16).

### D-E5.18 The day list (v4 as amended)

| Days | Kind | Reads |
|---|---|---|
| S-29 | install | no data |
| S-28, S-21 | `normal`, `overcast` (unchanged) | partly checked |
| **S-27** | **`steady-before-first` (new)** | **checked** |
| **S-26..S-22** | **`steady-before` (new)** | **checked** |
| S-20..S-15, S-13..S-11 | unchanged | checked |
| S-14, S-7 | `overuse` (unchanged) | partly checked |
| S-10 | `missing` (unchanged) | no data (FILL-1) |
| S-9, S-8, S-6, S-5 | unchanged | checked |
| S-4 | `missing` (D-E5.12) | no data |
| S-3, S-2, S-1 | `steady` (D-E5.12) | checked |
| S, S+1 | trial pair (unchanged) | partly checked |

- **Week S-6..S:** 5 checked, 1 missed (S-4), 1 partly checked (S).
- **Month [S-29, S]:** 22 checked, 5 partly checked, 3 with no data (S-29, S-10, S-4). Presenter answer: "Readings run daily from 11 October. Two days are gateway outages. The weekly generator days and the trial day carry only the example hours."

### D-E5.19 Card FX-KOBO-GAPS, amended (same branch, same review; about +0.1 unit, about +40 lines)

1. **Data.** `demo-story-days-v4.json` adds six entries: `{"day": "S-27d", "kind": "steady-before-first"}`, then `steady-before` on S-26d..S-22d, in day order. The label reads "v4 (D-E5.12, D-E5.17)".
2. **L0.**
   - The v3-equality clause becomes: "v4 minus its 4 week entries and its 6 S-27..S-22 entries equals v3 minus its 2 week entries".
   - New `test_v4_month_fill`. For S in {11-07, 11-08, 11-09}:
     - `resolve` passes with installs;
     - S-27 is `steady-before-first` and S-26..S-22 are `steady-before`, each tiling [00:00, 24:00) local;
     - the days in [S-28, S] with no run are exactly {S-10, S-4}.
   - Must-fail: the same test fails on the unamended v4 (S-27..S-22 absent).
3. **WK-GAP.** Add a month clause. On [S-28, S], NO_DATA is exactly the days of `missing` kind, and PARTIAL is exactly the story-only days. Both come from `ctx.site_days("kobo")` and are never hard-coded.
4. **Stop rules.** The rows of D-E5.13 §7, plus SP-1 (its window now meets the full day S-27), F-CAL and CO-6: on any failure, stop and report. Also report, not as a fault: any October total read and the epochs of S-21 and S-14.
5. **Fallback.** `prepare --days backend/conversions/demo-story-days-v3.json` is unchanged.

### D-E5.20 Figures (S = 11-08; expected, the build decides)

- **Unchanged from D-E5.14 (all are week or November figures):**
  - Coverage line: 6 of 7 assessed, not assessed 4 Nov.
  - Days line: 5 of 7 checked, 1 partly checked.
  - Grow: 137.50 USD.
  - MG-1: 550.0 kWh on 5 of 8 days [S = 11-09: 660.0 kWh on 6 of 9], MET.
  - Study 3-7 Nov: 4 of 4 well-observed days, 1 of the 5 study days has no reading.
  - WK-2b on S: not judged yet.
  - Pinned study S-19..S-15, MILL-3 "Target met", ACT-001 Verified (3.3 L / 4.12 USD), ACT-005 17.00 USD.
  - Generator Finding: 8 Nov 04:35-07:55, 0.00-15.13 USD.
- **Board gap line (31 days):** 4 no checked readings · 5 partly checked (no data: S-30, S-29, S-10, S-4; partly: S-28, S-21, S-14, S-7, S). This replaces D-E5.14's 10 · 5.
- **Month:** 22 checked (up from 16), 5 partly checked, 3 no data.
- **Prepare time:** 6 more full days at about 131 s each is about +13 min over the v4 card, and about +18 min over v3. Kobo goes from about 29 to about 47 min, and the whole prepare from about 2 h 20 m to about 2 h 38 m. That is still under the 3 h B-16 line. This is estimated, not measured.

### Decisions logged for owner review

- **D-E5.16** Neither longer runs nor other dates exist. The trial and generator days stay 06:00-14:00, and the trial day is the week's one partly checked day.
- **D-E5.17** Fill 12-17 Oct with six before-mill full days through the normal ingest path. No new study is created.
- **D-E5.18** The day list above.
- **D-E5.19** The card is amended: 6 entries, 1 L0 test, a WK-GAP month clause and the added stop rows.
- **D-E5.20** The figures above.

