# Build sheet DEMO-SPARSE · sparse story days with named gaps (extends DEMO-A)

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-31. Owner approval (verbatim, end of
`.agent/owner-client-demo-sequence-2026-10-30.md`): "approve all three, go ahead" on
`.agent/architect-sparse-days-proposal-2026-10-31.md` (recommendations 2 and 3). Code read at DEMO-A head `50cbc02be`
in `C:\Users\assef\Bineyame\AssetOpsV1-demo3`, branch `task/DEMO-A-combined-dataset` (this sheet **extends** that
branch; no new branch). Inputs that stay in force: `build-sheet-DEMO-COMBINED.md` §0 (CO-1..CO-12), §1, §4-§8 and
Addendum 1 (R1 price seam, R3 install order), plus `AssetOpsV1-demo3/.agent/DEMO-A-probe.md` and
`DEMO-A-phase-handoff.md`. **Where this sheet differs, it wins:** it replaces DEMO-COMBINED §2 (fixed timeline) and
re-points §3 U3-U6. Paths are repo-relative to `-demo3`.

## 0. Rules that bind every unit

- **Evidence is append-only.** A `missing` day is a day with no run and no delivery, never a deleted record. To
  remove a day, rebuild without it. `add-day` refuses any day that already holds delivered evidence.
- **Never tune.** Seeds, demand, irradiance, prices, reserve values and targets come from the registered scenarios,
  the v2 manifest and `demo-objectives.json` unchanged. Choosing *which* registered scenario or hour carries a story
  beat is allowed only by the rules fixed in this sheet before measuring (U1); a result is never a selection input.
- Every run is a registered Lab run (`REGISTERED_SIMULATION`, "Generated test data"). Nothing is relabelled as live.
- No product code changes in this sheet. Product behaviour the dataset needs comes from IDX-GAPS
  (`build-sheet-IDX-GAPS.md`), which builds in parallel (no shared files). No test module edits (DEMO-A U5 stop rule).
- No new on-screen copy. Work-row titles/notes already in `demo-combined-story-v1.json` were scanned (DEMO-A). The
  gap line text is IDX-GAPS's. Any new authored title is scanned against `terms` + `w1.terms` + `w1.codes` + the
  `w1.patterns` of `frontend/src/test/productVocabulary.json` before commit.
- Register IDs **R615-R619**.

## 1. Code reality

| Element | Where | Verdict |
|---|---|---|
| Story clock: `S = floor_utc_day(DB now) − 2 d`, offsets `S±Nd HH:MM` | `tools/demo_combined.py:62` `_OFFSET`, `:85-95` `_resolve`, `:97-138` `resolve_story` | EXTEND: day-relative `D±Nd HH:MM` per entry |
| Kobo install fixed 2026-10-07 | `demo-combined-story-v1.json` `kobo.install_fixed`; it comes from `pgb.converted` (`test_s1_bindings_postgres.py:101-104`): import at `NOW − 2 h`, convert at `NOW − 1 h`, `NOW = 2026-10-07 12:00` (`:53`) | **CHANGE** (U2): call `pgb.imported(store, when=…)` (`:88`, has a `when` keyword) and `pgb.convert(store, BindingService(store, Clock(…)), …, pgb.FIXTURE)` (`:103`) from the tool; no test-module edit |
| Kobo chain = the trial pair | `tools/demo_combined_kobo.py:106-200` (`resolved_manifest :29-42`, `_draft :127/:156`, `_publish_and_accept :128/:157`, `LabRunner :130`) | REUSE as kinds `trial-before`/`trial-after` |
| A run of another registered scenario | `host/tests/test_s6_verification_replay.py:128-137` `_scenario` reads `M["scenario"]["scenario_id"]` from `config/scenarios/`; `_draft :149-176` uses `M["model_profile"]` (mini-grid v5) and `M["publication_profile"]` | REUSE with a per-kind manifest copy; **compatibility unproven** for scenarios that declare other profile versions (U1 P1) |
| Late delivery | `_publish_and_accept(..., received_at)`; NOT_ASSESSED until a recompute covers it (probe R2 check 1 reason text) | `received_at` later; live: the `serve` tick (`demo_combined.py:54` `TICK_EVERY_SECONDS = 120`, `:304-312`) assesses it |
| Cold replays | DEMO-A U4 plan (handoff "Resume"): `ShiftedChain.open` threading `story_day`/`install_at`/`scenario_path` via `w502_cold_work_cases.py:69` `target_delta` | REUSE, one call per cold day |
| EV replays | DEMO-A U5 plan: `native_replay(..., window=)` (`w504_ev_work_walkthrough.py:105`, guard `:122-124`), `RunSetupService` swap, scenario via `Chain.open(scenarios=…, scenario_id=…)` | REUSE, one call per EV day |
| Board needs current Finding source | IDX-GAPS `finding-index/2`: PARTIAL settles when the board day is not a gap | **dependency** (§6) |
| Build test | DEMO-COMBINED §4 `backend/tests/test_demo_combined_postgres.py` (not written yet), slow tier (`conftest.py:121` `SLOW_MARKER`) | EXTEND (U6) |

## 2. The day list (replaces DEMO-COMBINED §2's fixed timeline)

New file `backend/conversions/demo-story-days-v1.json` (the `prepare` default):
```json
{"schema": {"id": "assetops.demo-story-days", "version": 1},
 "label": "Sparse story calendar: assessed days and named gaps (registered Lab runs)",
 "kinds": { "<site>": { "<kind>": {"scenario_id": "...", "scenario_version": 1, "start": "D+0d 03:00",
            "end": "D+0d 11:00", "received_at": "D+0d 12:00", "assess": "build|tick|none", "note": "..."} } },
 "sites": {"kobo": [{"day": "S-28d", "kind": "normal"}, ...], "cold": [...], "ev": [...]},
 "trial": {"window_hour": "06:00", "probe_ref": ".agent/DEMO-SPARSE-trial-probe.md"}}
```

**Kinds** (first candidate per kind; U1 P1 confirms or takes the listed alternative, never anything else):

| Site | Kind | Mechanism (existing) | Interval / received | Alternative if P1 refuses |
|---|---|---|---|---|
| Kobo | `normal` | `kobo-s3-dispatch-necessary-run.yaml` (generator needed throughout → 0 avoidable minutes) | D 03:00-11:00 / D 12:00 | `kobo-mini-grid-stop-60.yaml`, then `kobo-mini-grid-evening.yaml` |
| Kobo | `overcast` | `kobo-daytime-overcast.yaml` (weather explains the generator) | as normal | `kobo-s3-dispatch-necessary-run.yaml` (its own text: overcast morning) |
| Kobo | `overuse` | `kobo-mini-grid-reserve-trial.yaml` baseline run under the 30 % reserve (the run that yields F-104) | as normal | `kobo-mini-grid-prolonged.yaml` |
| Kobo | `trial-before` / `trial-after` | the DEMO-A chain (`demo_combined_kobo.py:106-200`) on D and D+1; window hour from `trial.window_hour` | baseline D 03:00-11:00 recv D 12:00; later D+1 | — |
| Kobo | `missing` | no run, no delivery | — | — |
| Kobo | `late` | an `overuse` or `normal` run (field `as`) delivered late | recv D+2d 12:00 (prepare); live: now, assessed by the next tick | — |
| Kobo | `degraded` | `kobo-mini-grid-degraded-evidence.yaml` | as normal | deliver the first half of the run's sealed batches only (a gateway outage; label in `note`) |
| Cold | `normal` / `failure` / `degraded` | `cold-normal.yaml` / `cold-backup-failed.yaml` (+ w502 `positive` work) / `cold-missing-probe.yaml` | D 16:00-17:05 (w502 shape) | `cold-late-reading.yaml` for `late` (add-day only) |
| EV | `normal` / `fault` | `ev-complete.yaml` / `ev-fault.yaml` (+ w504 work) | D 08:00-09:00 | `ev-late-record.yaml` for `late` (add-day only) |

Every Kobo run: model profile and publication profile of the v2 manifest, seed `20260929`, a fresh
`sequence_epoch` `"day-<n>"` per run in build order, `foundation_known_at = D−1d 12:00` (trial-before keeps
`D−6d 12:00`, as v2), runner `now = received_at + 5 min`.

**Story calendar** (proposal §5; S = trial day):

| Day | Kobo | GreenHarvest | Depot |
|---|---|---|---|
| S−29 11:00 | install (import 10:00, convert 11:00), price v1 at 12:00 | — | — |
| S−28 | `normal` (Cost On track candidate) | — | — |
| S−26 | — | install 06:00 | install 06:30 |
| S−21 | `overcast` (control: no Finding) | — | — |
| S−14 | `overuse` (first seen) | — | — |
| S−10 | `missing` (gateway offline) | — | — |
| S−7 | `overuse` (repeat) | `normal` night (Protect On track candidate) | `normal` hour |
| S−3 | `late` (`as: normal`), recv S−1 12:00 | `degraded` night (probe dropped) | — |
| S | `trial-before` (F-104, ACT-048 accept/apply/freeze) | `failure` night + w502 work | `fault` hour + w504 work |
| S+1 | `trial-after` (verified, cost check) | — | — |

The work rows (visits, plans) keep `demo-combined-story-v1.json`'s offsets. Kobo board day S then inspects
`[S−30, S+1)`: 6 assessed days, so its gap line reads "Not available yet · 25 of 31 days have no assessed readings"
(U6 asserts the template with `g = 31 − assessed days in the window`, not this literal).

## 3. Units (6). Effort 5.75 builder days (3.0 new + DEMO-A U4-U6 re-pointed 2.75)

### U1 · Probe: kind compatibility and the trial hour (no product code) · 0.5 d · gate for U3
DBs `assetops_demo3_probe<k>_test`; results in `.agent/DEMO-SPARSE-trial-probe.md` (all rows, kept even when unused).
- **P1 kinds.** For each Kobo kind's first candidate and alternatives: `rp._draft` with a manifest copy whose
  `scenario` is that id → record `execution_status`, `blocking_reasons`. Then for the READY ones, one run delivered
  and assessed on a scratch day: record the dispatch window status, avoidable generator minutes, any Finding (id,
  episode start/end). Rule (fixed now): a kind takes the **first READY candidate whose outcome matches the kind's
  stated meaning** (`normal`: 0 avoidable minutes, no Finding; `overcast`: generator ran, no Finding; `overuse`: a
  Finding). If none matches, the kind is dropped from the calendar and the beat is registered (R617), never forced.
- **P2 episode edges.** Every Finding episode recorded in P1 must start ≥ 00:20 and end ≤ 23:40 UTC of its day;
  otherwise IDX-GAPS withholds it next to a gap. Record; stop and report if F-104's episode fails this.
- **P3 trial hour.** Candidates, each a full trial-pair chain on scratch S/S+1:
  (a) window 06:00 (current; known result `MODELLED_NO_IMPROVEMENT`, 0 USD);
  (b) the earliest whole hour in `[03:00, 10:00]` where the baseline run's dispatch intervals show a generator start
      with binding constraint `BATTERY_AT_RESERVE` or `BATTERY_NEAR_RESERVE` (from the S3 dispatch window body,
      `analytics/dispatch_v3.py:291`);
  (c) `kobo-mini-grid-evening.yaml` as both runs' scenario, window at its first such hour (the scenario's run
      interval as P1 records it).
  Record per candidate: lever evidence (constraint and start time), F-104 on S (yes/no), verification outcome, cost
  check state, nominal and upper USD.
  **Choice rule (fixed now, savings are not an input):** the first of (b), (c) that shows the lever, keeps F-104 on S
  and VERIFIES; otherwise (a). The chosen result is shown as calculated, **including 0** ("no modelled improvement").
  Write `trial.window_hour` (and `trial.scenario_id` if (c)) into the day list with `probe_ref`.
- **P4 back-dating.** Import/convert at S−29 and a run delivered for S−28 under the fixture decision clock: record any
  refusal. A refusal stops the unit (report; the Architect re-places the calendar, never shortens silently).
- Stop rules: P2 fails for F-104; P4 refuses; a tick creates a new F-104 revision or a withdrawal (DEMO-A U1 rule).

### U2 · Day list, resolver, relative Kobo install · 0.5 d
- New `tools/demo_story_days.py`: `load(path) -> dict`, `resolve(days_doc, S) -> list[DayRun]` sorted by
  `received_at` (the build order), `DayRun = (site, day, kind, start, end, received_at, assess, scenario, epoch)`.
  Day offsets `S±Nd`; kind times `D±Nd HH:MM` resolved against the entry's day. Validation (each a `StoryDaysError`
  code): `UNKNOWN_KIND`, `DUPLICATE_DAY`, `TRIAL_PAIR_INVALID` (exactly one trial-before at D and trial-after at D+1),
  `DAY_BEFORE_INSTALL` (run start < install + 1 h), `DAY_NOT_IN_PAST` (received_at > DB now − 5 min),
  `OUTSIDE_BOARD_WINDOW` (a day earlier than S−30).
- `demo_combined.py`:
  - `prepare --days <file>` (default `backend/conversions/demo-story-days-v1.json`); writes `<work>/days.json`
    (resolved list) beside `story.json`. `EXPECTED_SECONDS["kobo"]` (`:58`) becomes `80 × kobo runs + 60`; the wall
    cap stays 2× (`:214-216`).
  - `resolve_story` (`:97-138`): `kobo.install_at` from `"S-29d 11:00"`; `import_at = install_at − 1 h`;
    `price_recorded_at = install_at + 1 h`. Delete `install_fixed`. `earliest["kobo"]` (`:116-118`) includes every
    day run's `start`. Install order (R3) is then Kobo, cold, EV.
- `demo-combined-story-v1.json`: `schema.version` 2; remove `kobo.install_fixed` and `kobo.runs` (moved to the
  `trial-*` kinds); keep visits/plans/action/plan/windows/evaluate offsets.
- Tests (fast, pure): new `backend/tests/test_demo_story_days.py` (imports the tool module through `tools` on
  PYTHONPATH): resolution of S/D offsets; each error code; build order by `received_at` (the late S−3 run sorts after
  S−1 12:00 and before S 12:00); default file validates for S = 2026-10-29 and for S = 2027-03-01 (relative dates).

### U3 · Kobo day builder (folds DEMO-A U3) · 1.0 d
- `demo_combined_kobo.py`:
  - `build` (`:106`) replaces `pgb.converted` (`:120`) with `pgb.imported(store, when=import_at)` and
    `pgb.convert(store, BindingService(store, pgb.Clock(install_at)), result.tenant, result.site, pgb.FIXTURE)`
    (import `BindingService` from where `test_s1_bindings_postgres` imports it; never edit that module).
  - New `run_day(store, runner, tmp, day: DayRun, M)`: manifest copy with `scenario`, `runs.<day>` = the DayRun
    instants, then `rp._draft` → `rp._publish_and_accept(..., received_at)` → when `assess == "build"`,
    `runner.now = max(runner.now, received_at + 5 min)`, `assess` + `match`. `assess == "tick"` leaves it to
    `finish()`'s ticks. `missing` writes nothing. `degraded` fallback delivers `batches[: len // 2]` (U1 P1 decides).
  - The trial pair keeps the existing chain body (`:130-171`) with `windows.*_start` from `trial.window_hour` (and the
    scenario if U1 chose (c)); it runs at its place in the build order.
  - `kobo.json` gains `days: [{day, kind, run_id, received_at, findings: [ids], status_after_build}]`.
- Unit check in the child: after the last run, `GET /api/sites/KOBO-001/finding-index` over `[S, S+1)` holds the
  accepted Finding (CURRENT; it does not need IDX-GAPS for a one-day window).

### U4 · `add-day` (live and before a demo) · 0.5 d
- `demo_combined.py add-day --site KOBO-001|COLD-LAB-001|EV-LAB-001 --kind <kind> [--day S±Nd] [--as normal|overuse]`.
  - Default day: the day after the site's last day in `<work>/days.json`. An explicit `--day` must hold no run and no
    delivered evidence (checked by `SELECT count(*) FROM ingestion_disposition` joined to the run's interval, plus
    `days.json`), lie in `[S−30, today]`, and pass `DAY_NOT_IN_PAST`; else refuse with the code.
  - Kinds allowed: Kobo `normal|overuse|overcast|late|missing|degraded`; cold `normal|degraded|late`; EV
    `normal|late`. `trial-*` and `failure`/`fault` are prepare-only (they carry work and Actions).
  - Live delivery uses **real time**: no decision-clock override; `received_at` = DB now. `late` and every live day
    stay unassessed until the running `serve` loop's next tick (≤ 120 s), so the client sees "not checked yet" turn
    into an assessed day; `--assess-now` (non-late only) runs assess + match in process.
  - `missing` appends the entry to `days.json` only (honest: nothing arrives). It changes no screen except the board
    gap count when that day falls in a board window.
  - Runs in its own child with the tree's interpreter and env (`Demo.env`, `:153`); refuses while another
    `prepare`/`add-day` holds the marker lock (`<work>/.busy`).
- Tests: `test_demo_story_days.py` adds the refusal cases (delivered day, future day, before install, unknown kind,
  trial kind). The live path is exercised once in U6's slow test (`add-day --kind late` then one `tick`).

### U5 · GreenHarvest and Depot on the day list (DEMO-A U4 + U5 re-pointed) · 2.0 d
- DEMO-A U4/U5 as planned (handoff "Resume" notes, DEMO-COMBINED §3 and Addendum 1 R3), with the days taken from
  `days.json` instead of `cold.failure_night_day` / `normal_night_day` / `ev.e_start`:
  - cold: `normal` S−7, `degraded` S−3 (`cold-missing-probe.yaml`, no work rows), `failure` S (w502 `positive` work);
  - EV: `normal` S−7 (`ev-complete.yaml`, no work rows), `fault` S (w504 work, plan, visits).
- Each day is one shifted replay in build order (cold and EV runs are interleaved with Kobo's by `received_at`; the
  child for a site may run all its days in one process). `story.json` `cold`/`ev` blocks keep install instants.
- `cold.json`/`ev.json` gain `days: [...]` like Kobo's.

### U6 · Acceptance, build test, serve, register (DEMO-A U6 re-pointed) · 1.25 d
- `finish()` (`:283-302`) unchanged in order; the self-check child `tools/demo_combined_finish.py check` (still to
  write, handoff) asserts §5 through the in-process app.
- `serve` (`:332`) unchanged plus: it prints the `add-day` commands for the next free day per site.
- `links` prints, per site, every story day with its kind and the board URL for S, S−28 and S−7.
- Build test `backend/tests/test_demo_combined_postgres.py` (DEMO-COMBINED §4), `@pytest.mark.slow`, DB
  `assetops_demo3_t<run>_test`: one `prepare` in a module fixture, then every §5 row as its own test function.
  The rows marked **[IDX]** carry `needs_v2 = pytest.mark.skipif(getattr(finding_index, "POLICY_VERSION", None) !=
  "finding-index/2", reason="needs IDX-GAPS")`. **At merge none may skip** (the packet shows `0 skipped`).
- Register (§7) and DEMO-COMBINED's R535, R552, R569, R595 resolutions as DEMO-A U6 planned.

## 4. Re-pointing DEMO-A (summary)

| DEMO-A unit | Before | Now |
|---|---|---|
| U3 Kobo | fixed two-day chain at S/S+1, install 2026-10-07 | folded into DEMO-SPARSE U2+U3: the chain is the trial pair inside an 8-entry day list; install S−29 |
| U4 cold | normal S−7 + failure S | DEMO-SPARSE U5: + `degraded` S−3, days from `days.json` |
| U5 EV | fault S | DEMO-SPARSE U5: + `normal` S−7 |
| U6 acceptance | CO-1..CO-12 | DEMO-SPARSE U6: CO-1..CO-12 + SP-1..SP-7 |

## 5. Acceptance (each row is one test in the slow build test)

| ID | Assertion | Waits on IDX-GAPS |
|---|---|---|
| CO-1 | Kobo board `from=S&to=S+1`: Cost lists the accepted Finding (the mock's F-104); Protect lists it as checked; Cost `must_not_harm` with ACT-048's verification href; ACT-048 on the Cost row; no "linked finding outside this view" | **[IDX]** |
| CO-2 | Overview `date=S` `freshness.state == CURRENT`; board Finding index status ∈ {CURRENT, PARTIAL} with the Finding in its rows; no measured mini outcome UNKNOWN from an unsettled producer | **[IDX]** (index part) |
| CO-3 | `cost_check.state` set; the Cost-row Earlier ACT-048 entry carries the modelled line with "not realised savings" | **[IDX]** |
| CO-4 | (DEMO-B captures) | after IDX |
| CO-5 / SP-1 | Kobo board `from=S−28d&to=S−27d`: Cost **On track** when U1 P1 gave `normal` 0 avoidable minutes (else R585 stays standing with the measured value recorded; the test asserts the recorded branch) | **[IDX]** |
| CO-5 / SP-2 | Cold board on the S−7 normal window: Protect On track (CC-1 and CC-6 met), or the recorded measured values | no |
| CO-6..CO-12 | as DEMO-COMBINED §4 (Portfolio 3 Sites, `objective_site_count == 3`, cold Earlier inspection, estate keys, EV readiness, plan and fault warnings, visits/plans/objectives on all Sites, slice outputs) | CO-6 Kobo cells **[IDX]**; others no |
| SP-3 | Kobo board S `finding_gaps.text` == `"Not available yet · {g} of 31 days have no assessed readings"` with `g` from `days.json`; `finding_gaps.days` contains S−10 and never contains an assessed day | **[IDX]** |
| SP-4 | Finding index `[S−30, S+1)` (the board's read): status PARTIAL; `gaps` has S−10 `UNASSESSED`; S−3 is not a gap (the late day assessed after its delivery); rows include every Finding `kobo.json` `days[]` records for S−14, S−7 and S | **[IDX]** |
| SP-5 | S−21 overcast: dispatch shows generator time and no Finding has an episode on S−21 | no |
| SP-6 | Trial: `kobo.json` window hour and cost check equal the U1-chosen candidate's row in the probe file; a 0 result reads "no modelled improvement" on the verification page body | no |
| SP-7 | Append-only: `add-day --day S−14d` refuses (delivered); `add-day --kind late` for the next free day, then one `tick`: that day turns from a gap (`UNASSESSED`/NOT_ASSESSED) to assessed; `prepare` again from the same file gives the same kinds per day with every date moved by the rebuild's S | no (index read is one day) |

## 6. Dependency on IDX-GAPS and order

- U1, U2, U3, U4, U5 build now, in parallel with IDX-GAPS (no shared files: IDX-GAPS touches `analytics/`,
  `site_outcomes/`, `frontend/`; this sheet touches `tools/demo_*`, `backend/conversions/demo-*`, new tests).
- U6's **[IDX]** rows run only after IDX-GAPS merges to main and main is merged into `task/DEMO-A-combined-dataset`.
  DEMO-A merges after that, with the full `-Tier all` on the combined tree. DEMO-B captures follow DEMO-A.

## 7. Register rows (R615-R619)

- **R615** · DEMO-SPARSE · mini overview board · D4 data reading · standing. Shown: on early story days the gap line
  counts days before the Site's install as days without assessed readings. Reason: true; the board reads 31 days.
- **R616** · DEMO-SPARSE · mini, cold, ev · D4 · standing. Mock: continuous month. Shown: a sparse month (8 Kobo,
  3 cold, 2 EV assessed days) with the gaps named. Reason: owner-approved story calendar (2026-10-31).
- **R617** · U1 P1/P3 · mini · D3 honesty · standing. Records each dropped beat or the trial hour chosen, with the
  measured values, including a 0 cost result. (Only if a beat is dropped or the hour changes; else not added.)
- **R618** · U5 · cold · D4 · standing. Shown: the S−3 night reads as limited evidence (probe readings missing).
- R619 reserved.

## 8. Validation tier

| Unit | Tests |
|---|---|
| U1 | none (probe; scratch DBs dropped by the probe script) |
| U2, U4 | `backend/tests/test_demo_story_days.py` (fast) |
| U3, U5 | the child self-checks on a dev `prepare` (`--sites kobo`, then all), plus DEMO-COMBINED §5 scoped list: `test_out_b4_board_postgres.py test_out_e4_readback_postgres.py test_out_d5_objectives_postgres.py test_out_c4_ev_warnings_postgres.py test_out_c3_repeat_visits_postgres.py` and both producers' existing `prepare` once (byte-unchanged manifests) |
| U6 | `tools\run-backend-suite-in-container.ps1 -Tier slow` for the build test (about 20-25 min for one `prepare`); **merge gate: one `-Tier all`** on an idle machine on the tree containing IDX-GAPS (any `tools/*.py` change selects the whole suite, `tools/select-tests.py:45-47`) |

`tools\check-all.ps1` at every commit. Build-time budget: about 8 Kobo runs × 80 s + 3 cold + 2 EV replays +
finish ≈ 18-22 min, inside the 30-min producer budget; the tool's cap is 2× its expected seconds.

## 9. Pre-flight (one batch in `.agent/DEMO-SPARSE-preflight.md` before code, then stop)

- [ ] Worktree `-demo3` at `50cbc02be`, clean except DEMO-A's known WIP; `git ls-files --eol` shows no `w/crlf` on
  `eol=lf` files.
- [ ] Builder PYTHONPATH (tests, probes): `<wt>\backend;<wt>\contracts;<wt>\tools;<wt>\simulator;<wt>\gateway;
  <wt>\host;<wt>\field` with `<wt>` = `C:\Users\assef\Bineyame\AssetOpsV1-demo3`; the tool's child env keeps
  DEMO-COMBINED §5's list (adds `backend\tests`, `host\tests`, `gateway\tests`). Python
  `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`; `assetops_backend.__file__` resolves into the tree.
- [ ] DB names only `assetops_demo3_<x>_test` (probes `assetops_demo3_probe<k>_test`) in `assetopsv1-postgres-1`, or a
  producer's `<prefix>_audit*`; drop only through the tool's marker.
- [ ] **Never pass `-ExecutionPolicy`**; run guards directly.
- [ ] No BOM: `.py`/`.json` written with `write_text(..., encoding="utf-8")` or the Edit tool; never PowerShell
  `Out-File`/`Set-Content` for repo files.
- [ ] `serve` and any capture need `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` and `ASSETOPS_WORK_CURSOR_KEY_HEX` from
  `<work>/keys.json` (`Demo.env(keys=True)`); never committed, logged or put in a URL.
- [ ] Keep-awake on; one heavy job at a time; no `prepare` beside a suite; long runs capped at 2×.
- [ ] Never `datetime.now()` for a story instant (prepare); live `add-day` is the only real-time path.
- [ ] Confirm `pgb.imported(..., when=)`, `pgb.convert`, `pgb.Clock`, `pgb.FIXTURE` and `BindingService`'s import
  path exist as named; if any needs a test-module edit, stop (DEMO-A U5 rule).
- [ ] `git archive HEAD` builds the tree: commit `demo-story-days-v1.json` before `prepare` reads it.
- [ ] Register: `grep -c "| R61[5-9] " .agent/mock-departure-register.md` is 0.

## 10. Owner decisions

None new. Decision 1 of DEMO-COMBINED (show a 0 cost result) is answered by recommendation 3 ("shows whatever saving
(or none) the simulator gives"). If U1 drops a beat (no compatible `normal` or `overcast` scenario), the Architect
re-places it and informs the owner; no number is tuned.

## Addendum 1 · builder deviations and SCN outcome (Architect: Claude, 2026-10-31)

- **(a) EV days on the Tuesday on or before the listed day: accepted** (the EV charger model accepts only a Tuesday
  window, `host/ev_publication.py` `ev_parameters`). The fault day is `Tue ≤ S`, the normal day `Tue ≤ S−7`.
  **Condition:** the Portfolio acceptance (CO-6) and `links` use the week period `from=S−6d&to=S+1d`. That period
  always contains the EV fault Tuesday, so EV's `LATEST_EVENT` window resolves; mini still reads
  `mini_summary_day(to)` (B-Q7, unchanged; the builder confirms it resolves to S), and cold's latest event is the S failure night. The EV board is checked on its event window.
  Work rows keep their offsets relative to the EV day. Add R619 (D4, standing): "Depot's story hour falls on the
  Tuesday before the trial day; the charger model publishes only Tuesday windows".
- **(b) EV `fault` kind = `ev-interrupted` v1: accepted** (`ev-fault` faults before any session, so it gives no
  Finding and no Action). CO-9/CO-10 (readiness, PLAN_OVERDUE, CHARGER_FAULT_OVERDUE_INSPECTION) run on it as
  written. Any that does not hold on this data is recorded with its cause and is not forced.
- **Cold `degraded` (S−3) gives a COLD_START_FAILURE Finding: real data, kept.** The S−3 board reads Needs attention.
  CO-5's cold On track candidate stays the S−7 normal window.
- **Overcast stays on `kobo-s3-dispatch-necessary-run`** (SCN Addendum 1). The `kinds.kobo.overcast` 720-min change
  is withdrawn.
- **Trial:** after SCN D2, `trial.*` changes only if U3 (d) VERIFIES. Otherwise (a), 0 shown honestly, plus R617.

## Addendum 2 · CO-6 on a sparse week (Architect: Claude, 2026-10-31, pre-ruled before the full build)

- **Ruling (i), with a day-S companion check.** No period can contain both the EV Tuesday and only assessed Kobo
  days, so (ii) cannot work. Aligning S to a Tuesday would push the w502 visit at S−24 d past the 30-day work rule
  whenever the shift is more than about 3 days, so that is refused too.
- **CO-6, week `from=S−6d&to=S+1d`.** Assert what the rules give, not a forced CURRENT:
  - estate coverage for Kobo is UNKNOWN with its stated reason (`estate/coverage.py:98-100`, R613); the builder
    records the exact reason and the overall `status` the estate rule derives, and asserts those values;
  - cold and EV `window_basis == "LATEST_EVENT"`;
  - three Sites; `objective_site_count == 3`; `double_count_violations == []`;
  - Kobo's outcome cells come from its day-S board (`mini_summary_day(to)` = S, `read.py:138`), so they are settled.
- **CO-6b, day `from=S&to=S+1d`.** Kobo coverage CURRENT. Cold `LATEST_EVENT` (the S failure night). EV reads its
  honest no-event state (`window_basis` PERIOD, Unknown cells), unless S is itself a Tuesday. Record it and assert
  it; never force it.
- **Demo script (sequence step 4).** Open the Portfolio on the week. The four outcome cells per Site are the story:
  Kobo's come from day S, GreenHarvest's and Depot's from their latest events. Kobo's weekly evidence reads Unknown
  because most days that week have no assessed readings. Say so plainly and frame it as a pilot ask: "a gateway that
  reports every day turns this into a weekly verdict". Then click Kobo, which opens on day S with the gap line
  ("Not available yet · {g} of 31 days have no assessed readings"). Do not present the Portfolio on day S as the main
  view: EV would read Unknown there.
- **Owner (the open R613 question).** Extending the `finding-index/2` rule to estate coverage (PARTIAL with named
  gaps instead of UNKNOWN) would let the weekly Portfolio show Kobo's assessed days. It is a separate product slice
  (about 2 builder days, its own review). It is not required for this build. The owner decides whether it comes
  before the client demo.

## Addendum 3 · full-build rulings (Architect: Claude, 2026-10-31; build `78e6b9748`, 15/17 self-check rows pass)

**1. The s4 crash: a separate fix slice that merges first.** Slice `FIX-S4-DOMAIN` · `task/FIX-S4-domain-filter`, from
main, 1 unit, 0.5 d, its own review.
- Cause: `PostgresFindingStore.episodes` (`analytics/adapters/postgres_finding_store.py:131-141`) reads every Finding
  of the Site. The mini matcher (`analytics/finding_service.py:67` → `plan_pass`) then meets cold Findings, whose
  `episode_end` is NULL, and fails in `margin_windows` (`finding_episode.py:296-299`). Any Site holding a non-mini
  Finding breaks the tick: a main bug, not a demo issue.
- Fix: `episodes(tenant_id, site_id, domain: str = FINDING_DOMAIN, analytic_id: str = dispatch.ANALYTIC_ID)`, with the
  WHERE gaining `AND f.domain = :d AND f.analytic_id = :a` (the predicate `_index_snapshot` already uses, `:544`).
  Update every fake that implements `episodes` (grep `def episodes`). Do **not** special-case a NULL `episode_end`
  in the matcher: a mini episode always has an end, and a NULL there must keep failing loudly.
- Tests: a Postgres test with one open cold Finding and one mini Finding on the same Site; a matcher pass completes;
  only the mini episode is planned. A unit test that `episodes` passes the domain and analytic. Tier: the scoped
  `test_s4_*` and `test_w2*_cold*` sets, then one `-Tier all` (an `analytics/` shared seam).
- Then merge main into DEMO-A and rebuild once. CO-6 is re-read after the rebuild.

**2. CO-1 / R552: neither a board change nor a re-ordered build; this goes to the owner.** The exact-revision link
(`site_outcomes/board.py:468-470`) is a board rule, and the owner allowed one exception (IDX-GAPS). Accepting after
the reassessment is impossible, because apply follows accept. The revision split is real product behaviour (the
apply records a new Foundation revision, so day S's basis refreshes).
- Recommendation for the owner (one line, with this justification): a narrow board rule. An Action also links to a
  later revision of the same Finding when every revision after its origin is `BASIS_REFRESHED` with unchanged
  lifecycle and episode. Same Finding, same facts, only the basis reference is newer. About 0.75 d, its own slice
  and review; any other transition still breaks the link.
- Until the owner answers, CO-1's Action link and Must-not-harm assertions are re-premised to the current behaviour:
  the Action is absent from day S's Cost row, and that is recorded. R552 stays open with this cause. The rest of
  CO-1 is asserted as is.

**3. SCN (d) re-probe with a normal S−1: accepted, once, with the same choice rule.** The refusal
(`actions/verification.py:86-93`, `VERIFICATION_BASELINE_NOT_SELECTED`) is a precondition of the chosen hour: a
window before 06:00 needs the previous UTC day selected. It is not a result. Adding a `normal` day
(`kobo-s3-dispatch-necessary-run`) at S−1 is a calendar fact, decided before any saving is known.
- Day list: `{"day": "S-1d", "kind": "normal"}`. The gap count moves by one (SP-3 computes `g`, no literal).
- Re-run (d) once at H = 04:00 UTC. Take (d) only if it shows the lever, keeps the Finding on S and VERIFIES;
  otherwise (a), 0 USD shown, and R617 stays. Record every column. S−1 stays in the calendar either way: the board
  story is unchanged by it.
- Interaction with ruling 2: if (d) is taken, the same refresh split applies. Record whether the trial Action's
  origin revision equals day S's shown revision.

**FYI ruling: "NOT_ASSESSED: accepted evidence exists" on each D−1 does not matter for honesty.** It is a true state
(readings arrived for that day and no run covers it). The day is still a gap, and the board line's "no assessed
readings" form stays correct. The builder names in the handoff, in one line, which evidence lands on D−1 (expected:
records stamped at gateway provisioning, `foundation_known_at` D−1 12:00). If it turns out to be part of the next
day's run readings, stop and report: that would mean a run is split across days.
- **FYI follow-up (2026-10-31): acceptable as is; no calendar or build change.** Every accepted row sits on its own run
  day, so no run is split. D−1 reads "accepted evidence exists" only because its read range is the day widened by the
  designed 6-hour bracket (`analytics/assessment_inputs.py:99-101`, counted at `analytics/dispatch_read.py:88-89`),
  which reaches the next day's 02:55–06:00 readings. That is true for that read, and the day is still an honest gap.
  My stop condition targeted a split run, which this is not. Record the cause in one line in the handoff.
- **Recorded:** the SCN (d) re-probe used its single try. S−1 was selected, the lever showed and the Finding stayed
  on S, but the freeze was refused with 409 `VERIFICATION_BASELINE_UNSUPPORTED` (the 04:00 window is INCONCLUSIVE
  `OPEN_BOUND`, from the interval starting at 03:05). The trial stays on (a), 0 USD shown, R617 stands, and there are
  no further tries. CO-1: ACT-000001 does appear in the Cost row's `earlier` list; only the Must-not-harm/link part
  waits on the owner's lineage decision (ruling 2).
