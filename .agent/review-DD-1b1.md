# Review: DD-1b1 story-time Actions

Reviewed `task/DD-1b1-story-time-actions` at `deaed0bb0` against `f7c045bee`, by an independent reviewer. Spec: `build-sheet-DD-1.md` DD-1b1, SCOPE-1, DD1b1-R, R2, R3.

## Verdict: REVISE

One High and one Medium. Everything else holds, including the product read change, the instants and add-day. The fixes are small. After them, a focused re-check is enough; no re-probe is needed unless the Medium is fixed in the read path.

## Findings

### H1. A full prepare crashes at finish with `KeyError: 'days'` (blocks the demo build)
- **Where:** `tools/demo_combined.py:424` pops `days` from `story`; `:445` calls `self.finish(story)`; `:461` calls `objectives_instants(story)`; `:100` reads `story["days"]`.
- **Scenario:** any prepare with all three Sites, including DD-1b2's partial prepares, finishes building them and then dies at the objectives step, before the ticks and self-check.
- **Executed:** `resolve_story` on real v3 with baseline `b22`, then `pop("days")`, then `objectives_instants` raises `KeyError 'days'`. With `days` present it returns the three instants.
- **Why nothing caught it:** the probe passes `{**story, "days": rows}` (`tools/dd1b1_coh3_probe.py:242`) and the L0s build their own dict. The real call shape never runs in the scoped set.
- **Client effect:** no demo dataset. R2 section 6 sized this item because "a full prepare stops at finish without S3"; as committed, it still stops there.
- **Fix:** `self.finish({**story, "days": days})` at `:445`, or give `finish` a `days` argument. Add an L0 that drives `Demo.finish` with a stubbed `py` on the shape `prepare` really passes. Keep `story.json` unchanged.

### M1. The Portfolio's links open a board that does not list the Action (acceptance gap, client-visible)
- **Where:** `backend/assetops_backend/site_outcomes/read.py:784-787` (`_overview_href`: plain `/sites/COLD-LAB-001`, `/sites/EV-LAB-001/ev`, rendered at `frontend/src/estate/PortfolioOutcomes.tsx:320,338`) and `read.py:387` (`event` is None with no window, so `actions_to` is None).
- **Scenario, read on a story-clock DB with all six Cold and EV days:** with no window the overview resolves the latest event window (Cold `16:00-17:05`, EV `08:00-09:00`). Already in hand lists INC-001, PM-005 and PM-006 on Cold and PM-009 on EV, with no ACT row. The week board behind the Portfolio does list it. So a client who clicks GreenHarvest or Depot on the Portfolio sees the Finding and Needs attention with no Action, while the chain says "Action agreed".
- **Not a regression:** main behaves the same here. It is still the natural way into the board, and ST-4 and ST-5 are only met on the printed day links.
- **Why it is not covered by what is owed:** R2 and R3 owe "any in-app link carrying an exact event window". This href carries no window, so that item would miss it. The packet does not mention it, and R645's closure text names only the exact event-window board.
- **Nothing shown is false.** The Action is omitted, and the rule accepted that for exact windows (BL-38), so this needs a ruling and not necessarily code.
- **Fix, the Architect's choice:** (a) the summary's Cold and EV `overview_href` carries the requested window; (b) a no-window board reads Actions to the read's "now"; or (c) keep it, add it by name to DD-1b2's owed list and the script, and extend R645's closure text. Any one of these closes the finding. (c) costs no code.

### Low (do not block)
- **L1. 13 `.pyc` files committed** under `tools/__pycache__`, `tools/checks/__pycache__` (commits `dc94fef35`, `313cb847e`) despite `.gitignore:10`. Remove them.
- **L2. `read.py:387` wiring has no L0.** Mutation `actions_to = None` passes `test_out_b3_cold_ev` and `test_ch6b1_r5_dated_lead` (29 pass); only the probe catches it. The dated-lead fake takes `actions_to` and ignores it, which is honest but a one-line assert there closes the gap.
- **L3. Two probe checks cannot judge the Finding.** `r2.*.utc_day.finding_in_issues` and `event_window.finding_shown` (`dd1b1_coh3_probe.py:193,196`) pass on any issue; the Cold local-day read has plan issues and no Finding. The stored data does show the Finding on those boards, and `coh3_pairs` needs it on the board, so the result stands. Judge the Finding's own text if the probe is reused.
- **L4. Words and format.** `cold.py:112` docstring still says Actions read to `hi`. `prepare_clock.py:5` says production composition never imports the module, but `postgres_objective_store.py:28` does at import; the check still only runs with an override. `demo_combined_cold.py:39` `REPO =Path`. `test_demo_combined_links.py` has wide gaps left by removed line continuations.

## Questions asked in the dispatch

**Product read change: confirmed by trace and by comparing bodies with main.** I built all six Cold and EV days on `f7c045bee` and on HEAD and diffed the board bodies for the same reads, ids normalised.
- Callers: only `SiteOutcomeBoardService.compose` (`read.py:388-391`), for `board` and for the summary through `board`. The mini branch returns at `:370-377`, before this code.
- Exact event window: the Action read arguments are unchanged. No-event and no-window reads: `actions_to` None, unchanged. The body differences on these reads come from the story clock (below), not this line.
- **Less shown than before: nothing in the story.** The 30-day, 31-day, week and story-day reads gain the ACT row, `counts.in_hand` +1, and the option link moves from Finding recommendation to the Action. No row, issue or Earlier entry is lost. A 45-day request is refused 422 on both, so the read can never exceed 31 days. A window starting more than 31 d before its end does not exist.
- Dropping older Actions is real in principle: an Action up to 31 d before an early event in a wide window. No Cold or EV Action in the story is that old, and the mill Action is on Kobo. Low residual for real Sites.
- **Known-time rule holds, executed.** Request `known_at` 17:14 hides ACT-001; 17:25 lists it. EV 09:39 hides ACT-002; 09:50 lists it. Those reads are `PARTIAL` because the evidence reads refuse a `known_at` later than the latest committed cutoff, which is the existing rule. COH-3: 2 pairs, linked, 0 findings on all six days.
- Story-clock effect on boards: Cold issues now carry `thread.state` OPEN where main had none on the same reads, the intended result of causes being known at story time. Normal-day boards are identical to main.

**EV "listed twice": not a defect, and it is not a duplicate row.** The probe's `_board_view` (`dd1b1_coh3_probe.py:134`) flattens `in_hand` across rows. Per row, ACT-002 is once under Grow revenue and once under Protect. `outcome_map.py:22` maps `FINDING:EV_INTERRUPTION` to two moved outcomes, and `board.py:850,865` places the Action on each, as its Finding is (the issue also appears on both rows). `OutcomeBoard.tsx:278` renders per row, so a client sees one row in each column. Remove this item from DD-1b2's owed list.

**Story clock: no production path found.** `test_recorded_clock_override` is only passed from `tools/demo_declare_objectives.py`. `story_commands` and `worker_instant` are only in `tools/`, called from the children's `build` path; the composition swaps are process-local and restored. Refusal tested on URL forms: `assetops`, query-string `_test` and a `/` or `?` in the password all refuse. The `urlsplit` replacement for `make_url` agrees on the database name or fails closed, except a percent-encoded name (`assetops%5Ftest` passes), which no deployment uses. The unset statement text is byte-equal to main by reading. `--db` names `assetops_demo3_<name>_test` and `assetops_polish_<name>_test` both pass.

**Instants: confirmed on my own build.** Cold Action 17:15:00, recorded 17:15:01; EV 09:40:00, recorded 09:40:01. Selections at 17:10 and 09:35 on all six days. Threads: Cold start failure and EV interruption ACTION_IN_HAND, Cold excursion OPEN, no CHANGE_APPLIED. Objective instants resolve on v3. No `occurred_at` edit in the diff.

**What a client sees.**
- Story day-links: Finding, Needs attention, ACT "Open", no suffix; chain "Action agreed". Confirmed.
- Local-day Cold: no client link reaches it. `localDaysWindow` is used only by Mini views and `story_links` opens UTC days. Only a hand-typed URL does.
- Portfolio: see M1.
- `story_links` and `day_windows` carry the new form. `demo_combined_finish.Ctx.window` still reads event windows, as ruled for DD-1b2.

**Probe.** Its checks can fail (two earlier runs failed on real causes). They judge the Action's own row by id. See L3 for the two weak ones. **Real-parser L0's mutation proof holds, rerun:** `work_lo` restored fails 3 tests. `test_ch6b1_r5_dated_lead.py`'s fake is changed honestly: it only accepts the new keyword.

**The "not run" items, decided:**
- **Mutation proofs: now run, both hold.** Inverting the COH-3 window fails `test_coh3_pairs_share_the_rule_loop` and the `coh3_board_missing_action` case. Dropping the objective-store refusal fails `test_a_refused_construction_opens_no_connection`.
- **Scoped set after the last test fix: now run.** Not owed again except what H1's fix touches.
- **Add-day: safe, run, not only read.** On the story-clock DB: Cold `normal` S+1 and EV `normal` on a free past Tuesday through each child's `add-day`, both exit 0, the next tick wrote 0 thread events, threads unchanged, and the story-day boards still list the Action "Open" at Needs attention. By reading, `add_day` passes no story clock and `story` is None on EV, so `declare_and_work` is not reached; Kobo's child is not in the diff. DD-1b2 still runs it through the `Demo.add_day` parent. Not owed before merge.

**R645's closure:** holds for the day and week boards. Extend its text per M1.

**Owed to DD-1b2:** R2 section 6 and R3 section 6 items are complete in the packet. The packet omits DD1b1-R's list (`expected-threads.json` and F-THREADS, `expected-today.json` I-09, E2 effects, Protect "Why?" naming both Cold threads) and Q5's mill step. They stand in the build sheet. Drop the EV duplicate item; add M1 if ruled (c).

**Scope:** BL-30, BL-31, BL-32, BL-38 not built. R9 not built (BL-11). No migration, no frontend change.

## Checks run

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` in the worktree | passed (needs `ASSETOPS_GUARD_PYTHON`; it stops without an interpreter) |
| `tools/check-agent-workflow.ps1`, `tools/check-navigation-truthfulness.ps1` | passed |
| `test_dd1b1_prepare_clock`, `test_out_b3_cold_ev`, `test_ch6b1_r5_dated_lead`, `test_demo_combined_links` | 57 passed |
| `tools/checks/test_chain_coherence.py` | 139 passed |
| `test_dd1b1_story_clock_postgres` plus `test_ch1b_*`, `test_ch6b1*`, `test_ch6b2*`, routed from a private base | 122 passed. The Q4 pin file was not in the packet's scoped list; it passes |
| Five mutations on a scratch export | COH-3 window, refusal, `work_lo`, `actions_hi = hi` caught; `read.py` wiring not caught (L2) |
| Extended probe on HEAD: six days, backfill, tick, reads, add-day, tick | no stop; 2 pairs, linked; 0 COH-3 findings; 0 thread events on both ticks |
| Same build and reads on `f7c045bee`, body diff | as above |

All databases were run-owned clones routed from a private base, `assetops_dd1b1rev_test`. All were dropped, confirmed by a listing that returned none. The `assetops_test` base and `assetops_demo3_full_test` were not used. The worktree stayed clean; runs used `PYTHONDONTWRITEBYTECODE`.

## Not verified
- A full prepare, the finish rows and `test_demo_combined_postgres`: barred. H1 was found by reading and a direct call, and other faults may sit behind it. DD-1b2's rehearsal is the first real run.
- The Kobo interaction: the probe builds no Kobo, so Action codes read ACT-001 and ACT-002 here, not ACT-002 and ACT-003.
- `test_s6_verification_replay` not rerun: no Kobo or host code in the diff. Implementer reports it passing.
- Frontend suite, build and layout evidence: no frontend change in the diff. Portfolio and board rendering was judged by reading.
- Guards V and M, and the full suite: not run. No same-revision full-suite evidence exists, and policy defers it.
- Forward-day EV add-day: the next free Tuesday is in the future and is refused `DAY_NOT_IN_PAST`, so I used a past one.

## Residual risk, not in the packet
- **After a live Cold add-day, the Portfolio landing changes.** It moves to the new day and reads Protect at Watch, with ACT-001 "Open · linked finding outside this view". This is honest, but it is new text in the ST-7 moment (on main the Action was build-dated and did not list). The script should state it or open the story-day link.
- **EV add-day on an earlier free day moves the plain landing back to that day** (`no_window` read Oct 13, Protect No objective). Behaviour unrelated to this diff, but the demo should avoid it.
- **The Portfolio row wording** "No action agreed yet" (`build-sheet-CH-6.md:1128`) was not read here; DD-1b2 F-THREADS reports it.
