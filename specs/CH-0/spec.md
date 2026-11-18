# Build sheet CH-0: the chain coherence check, the L3 clone helper, and tick stage timings

- Architect: Claude, 2026-11-03.
- Plan: `Docs/demo-sprint/client-demo-plan.html`, agreed by the owner ("Let the build begin now").
- Design: `Docs/demo-sprint/implementation-logic-design-proposal.html` §13 (coherence check), §11b (timings), §15 (CH-0 row, 3 units).
- Branch: `task/CH-0-coherence-timings`, cut from main **after QW-1/QW-2 merge**. It imports `assetops_backend.perf`, which QW-1 adds.
- Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`. Line references are to main at `73a558a1b` unless a QW file is named.

## 0. What the slice delivers, and what it does not

**Observable result.** One command prints a report of the contradictions between today's screens. Each one has a rule id, a Site and window, the bodies involved, and the register issue it corresponds to. Every tick logs one structured line with per-stage elapsed time, each stage's share of its bound, and the stage child's peak memory.

**Not in scope.**
- No product read path changes, and no response body changes.
- No migrations.
- No finish-check rows. DD-1 wires the check into `demo_combined_finish.py` later.
- No L2 synthetic fixture. Each of CH-1a and CH-2 defines its own; that is a plan amendment already made in the plan's §4.1.

**Overlap with QW-1/QW-2** (`task/QW-1-2-load-timing`, worktree `AssetOpsV1-qw`, commits up to `b5483939f`):
- QW touches `B/perf.py` (new), `B/estate/{evidence_money,index,portfolio}.py`, `B/estate_portfolio_api.py`, `B/outcome_api.py`, `B/site_outcomes/{cold,ev,mini,read}.py` and `backend/tests/test_qw1_perf.py`.
- CH-0 **reads** `B/perf.py` (it uses `perf.LOG`, the `assetops.perf` logger) and edits none of the QW files.
- CH-0 edits `B/scheduling/tick.py` and `B/scheduling/stages.py`, which QW does not touch.
- So there is no textual overlap, but CH-0 depends on QW-1. If QW-1 has not merged when CH-0 starts, stop and ask; do not copy `perf.py`.

## 1. Units (≤ 6; this slice is 3)

| Unit | Content | Files |
|---|---|---|
| U1 | Collector and rules, `tools/checks/chain_coherence.py` | new file; reads only |
| U2 | Fixtures, self-tests, screen-route list and vitest sync test, check-all line, and the L3 clone helper; today's report recorded | `tools/checks/test_chain_coherence.py`, `tools/checks/fixtures/chain_coherence/**`, `F/__tests__/chainScreenRoutes.test.ts`, `tools/chain_clone.py`, `tools/check-all.ps1` (one line), `.agent/CH-0-today-report.json` |
| U3 | Tick stage timings and peak memory | `B/scheduling/tick.py`, `B/scheduling/stages.py`, `backend/tests/test_ch0_tick_timing.py` |

Pre-flight first, then stop (ROLE_CONFIG). Dry-read this sheet against main, batch every open point into one note, and wait for rulings before writing code. The known pre-flight items are listed in §6.

## 2. U1: `tools/checks/chain_coherence.py`

### 2.1 Command line

```
python tools/checks/chain_coherence.py collect --work <work-dir> --database-url <url> --out <bundle-dir> [--known-at <iso>]
python tools/checks/chain_coherence.py collect --work <work-dir> --base-url http://127.0.0.1:8990 --out <bundle-dir>
python tools/checks/chain_coherence.py check   --bundle <bundle-dir> [--expect <expected.json>] [--report <out.json>]
```

- **`collect` in process (`--database-url`).** It uses `tools/demo_combined_finish.py` `app_client(url, work)` (`:583`) and `load(work, client)` (`:573`). Import these two; do not copy them. The work dir supplies `story.json`, `days.json`, `keys.json`, `kobo.json`, `cold.json` and `ev.json`.
- **`collect` over HTTP (`--base-url`).** It issues the same GETs with `urllib.request` and a 30 s timeout per request. It is GET-only, so it is allowed against a running serve **only when the coordinator says so**. Never start or restart a serve for it.
- **Pages.** Every estate body that carries `next_cursor` is followed until the cursor is null (`EstateEnvelope.next_cursor`, `F/estate/estateClient.ts:69-70`). Pages are stored as `<name>.p<N>.json`.
- **The bundle** is a directory holding `manifest.json` (`{schema: "chain-coherence-bundle/1", S, code, collected_at, source: "in-process"|"http", requests: [{name, path, params, status, file}]}`) plus one JSON file per response. A non-200 response is recorded with its status and body; it is never retried.
- **`check`** is pure. It reads only the bundle and `tools/checks/fixtures/chain_coherence/screen_routes.json`. It needs no DB, no app and no network.

### 2.2 Windows and requests (all derived from `story.json` and `days.json`, never hand-typed)

Let S = `story["S"]` and `day(n) = S + n days`. Windows are half-open `[from, to)`, in UTC ISO with a `Z`, matching `demo_combined_finish.iso` (`:47`).

| Window id | Range |
|---|---|
| `week` | `[day(-6), day(1))`. Same as the runbook's Portfolio week, `tools/demo_combined.py:174` `story_week_query`. Reuse that function. |
| `S` | `[day(0), day(1))` |
| `month` | `[day(-28), day(3))`. Same as `tools/demo_combined.py:224`. |
| `day:<site>:<kind>:<day>` | Kobo: for each `days.json` row with `site == "kobo"` and `has_run`/`assess == "build"`, the UTC day of `start`. Cold and EV: each row's `[start, end)`, as `Ctx.window` does (`demo_combined_finish.py:88-90`). |

For each estate window (`week`, `S`, `month`), collect:
- `GET /api/estate/outcome-summary?from&to`
- `GET /api/estate/portfolio?from&to&lens=all`
- `GET /api/estate/findings?from&to&lens=all&state=all`
- `GET /api/estate/findings?from&to&lens=opportunities&state=all`
- `GET /api/estate/actions?from&to`
- for each of `COLD-LAB-001` and `EV-LAB-001`, `GET /api/sites/<code>/domain-work/action-index?from&to`

For each `day:*` window, collect the board:
- Kobo: `GET /api/sites/KOBO-001/outcome-board?date=<day>`, as `Ctx.board` does (`:79-82`).
- Cold and EV: `?from&to`.

Also collect `GET /api/estate/findings?from&to&lens=all&state=all` for the same window, restricted to that Site in the rules.

For every summary Site row, also collect the board for the window that summary row declares (`site.window.from/to`), so COH-7 can compare like with like.

Query parameter names are exactly those of the finish check and the frontend clients (`F/estate/estateClient.ts:452-465`). Confirm in pre-flight that `/api/estate/actions` and `/api/estate/findings` accept `from`/`to`/`lens`/`state` as named; `B/estate_api.py:67,71` are the routes.

### 2.3 Rules (rule id, inputs, pass condition)

A rule yields zero or more **findings**:

```
{rule, site_code, window, subject (finding_id | action_id | href), detail, bodies: [file names]}
```

`check` exits 0 when every finding is listed in `--expect` (same rule, site_code, window and subject). It exits 1 when a finding is not expected, and it also prints **resolved** expectations (expected but no longer found) so that later slices shrink the file. With no `--expect`, any finding fails.

| Rule | Inputs | Pass condition | Today's register issue |
|---|---|---|---|
| **COH-1 links** | Every body | Every non-null string under a key `href`, any key ending `_href`, every value of a `links` object, `destination` and `overview_href` does **not** start with `/api` and contains no `://`. Its pathname (before `?` and `#`) matches a pattern in `screen_routes.json`: `:name` matches exactly one non-empty segment, and a trailing `/*` matches the rest. | I-08 (Cold and EV board Finding links are API URLs) |
| **COH-2 Action on Portfolio** | Portfolio (all pages), estate actions, domain action index | For every Action `A` (mini: `source_finding_id`; domain: its origin Finding field, see pre-flight P2) whose origin Finding id `F` is a Portfolio row's `finding_id` in the same window, that Portfolio row's `action_id` is non-null. | I-03 (Kobo ACT-001); I-09 (Cold ACT-002, EV ACT-003) |
| **COH-3 Action on board** | `day:*` boards; estate actions and domain index for the window containing the day | When a board row has an `issues[]` item with `kind == "FINDING"` and `ref.finding_id == F`, and an Action whose origin is `F` was created at or before the board window's `to`, then that Action's id occurs as a substring of some `href` in that board's `in_hand`, `earlier`, `issues` or `must_not_harm`. | I-09 |
| **COH-4 Findings contain the Portfolio and the board** | Portfolio, estate findings (lens all), boards | Each Portfolio row's `finding_id` is among the Findings `rows[].finding_id` for the same window. Each board FINDING `ref.finding_id` is among the Findings rows for the board's own window and Site. | none expected today (a guard for later slices) |
| **COH-5 lens** | Boards; estate findings for the board window | For each board FINDING issue under row `category` c, with c mapped as OPTIMIZE_COST → COST, PROTECT_ASSET → RISK and GROW_REVENUE → OPPORTUNITY (ASSURE_PERFORMANCE has no lens and is skipped), the Findings row for that id has that lens in `lens_flags`. The map is a module constant `CATEGORY_LENS`, documented as the outcome-map/1 reading. Confirm it in pre-flight P3. | I-21 |
| **COH-6 opportunity** | Boards; Findings with lens opportunities; Portfolio | When any board row in a window has an `issues[]` item of `kind == "OPPORTUNITY"`, or any `warnings[]` item has `badge == "OPPORTUNITY"`, then for each estate window containing that day: (a) the opportunities-lens Findings body has at least one row for that Site, and (b) Portfolio `opportunity.state != "UNSUPPORTED"`. | I-06 |
| **COH-7 one basis for the summary** | Summary; boards collected at each summary Site window | (a) All summary `sites[].window_basis` values in one summary are equal, and every `sites[].window` equals the requested window. (b) For each Site and category, the summary row's `state` and `headline_money` equal the board's row (same category) at the summary Site's own window. | (a) I-04; (b) none expected |
| **COH-8 verified Action reaches the Portfolio** | Estate actions; Portfolio | For each Action with `verification_outcome == "VERIFIED"` whose origin Finding is a Portfolio row: that row's `verification_outcome == "VERIFIED"`, and the Portfolio `progress.rows[]` entry for the Action has `origin_revision_selected == true`. | I-03, I-01 (part) |
| **COH-9 day counts** (info) | Portfolio `summary.checked_days`, envelope `coverage.sites[].days`, board texts | (a) **Fails** when Portfolio `checked_days[site].checked/requested` differs from that Site's `coverage.sites[].days.checked/requested` in the same body. (b) **Info only, never failing:** every phrase matching `(\d+) of (\d+) (?:well-observed )?days` or `(\d+) of the last (\d+) days` in board `subline`, `contributors[].text` and `not_measured_text` is listed per Site and day, so the I-15 "three meanings" are visible in the report. | (a) none expected; (b) I-15 listed |

The rules live in a list `RULES: list[tuple[str, Callable[[Bundle], list[Finding]]]]`, and later slices append rules (CH-2 thread rules, CH-3 lifecycle rules). Each rule is pure over the bundle, never reads the DB, and never parses copy except COH-9(b).

### 2.4 Report

`--report` writes `{schema: "chain-coherence-report/1", bundle: manifest, findings: [...], expected_unmatched: [...], resolved: [...], info: {COH-9b: [...]}, summary: {rule: count}}`. The stdout summary is one line per rule, then a total, in the style of `self-check: N pass, M fail`.

## 3. U2: fixtures, self-tests, routes, clone helper

### 3.1 Screen route list

`tools/checks/fixtures/chain_coherence/screen_routes.json` holds `{"schema": "screen-routes/1", "routes": [<pattern>, ...]}`. It is exactly the set of path patterns that `F/App.tsx` registers with `<Route path=...>`, excluding `"*"` and the `"/"` redirect.

The 22 expressions found at `73a558a1b` are:
- `ACTIONS_PATH`, `EVIDENCE_PATH`, `FINANCIALS_PATH`, `FINDINGS_PATH`, `FINDINGS_COST_PATH`, `FINDINGS_RISKS_PATH`;
- `INCIDENTS_PATH`, `MAINTENANCE_PATH`, `MAINTENANCE_PREVENTIVE_PATH`, `OPERATIONAL_RECORDS_PATH`, `PORTFOLIO_ROOT_PATH`;
- `SITE_ASSETS_ROUTE_PATH`, `SITE_ASSET_ROUTE_PATH`, `SITE_HEALTH_ROUTE_PATH`, `SITE_WORK_ROUTE_PATH`;
- `WORK_REQUEST_HISTORY_ROUTE_PATH`, `WORK_REQUEST_RECORD_ROUTE_PATH`, `WORK_REQUEST_ROUTE_PATH`;
- `"/maintenance/requests/:caseId/*"`;
- plus the dynamic `path={path}` and `path={route.path}` lists. Enumerate their sources in pre-flight P1.

`FINDINGS_OPPORTUNITIES_PATH` (`F/shell/operatorSiteRoutes.ts:432`) must appear if App registers it. If it does not, record that as a pre-flight point; do not add the route.

`F/__tests__/chainScreenRoutes.test.ts` (vitest) imports the same constants, plus the arrays behind the dynamic routes, and asserts that the JSON's `routes` equal that set exactly (sorted). A route added to App without the JSON fails this test. That keeps the Python check honest without parsing TSX.

### 3.2 Self-tests: `tools/checks/test_chain_coherence.py` (pytest, pure, fixture bundles)

Fixture bundles live under `tools/checks/fixtures/chain_coherence/bundles/`. Each is a hand-made, minimal manifest plus bodies, holding only the fields the rules read and at most 2 Sites.

- `clean/`: every rule passes (0 findings).
- One failing bundle per rule:
  - `coh1_api_link/`: a Cold board issue `href` of `/api/sites/COLD-LAB-001/cold/findings/x`.
  - `coh2_no_action/`: Portfolio row `action_id: null` for an Action's Finding.
  - `coh3_board_missing_action/`
  - `coh4_missing_finding/`
  - `coh5_lens/`: an OPTIMIZE_COST Finding without COST.
  - `coh6_opportunity_denied/`: a board OPPORTUNITY issue, while the Portfolio `opportunity.state` is `UNSUPPORTED`.
  - `coh7_basis/`: summary Sites with `DAY` and `LATEST_EVENT`.
  - `coh8_verified/`
  - `coh9_counts/`
- The tests assert, for each failing bundle, exactly one finding with the right rule, site_code and subject.
- `--expect` semantics: an expected finding passes; a new one fails; an expected but absent one is reported as resolved and does not fail.
- COH-1's pattern matcher: `:name` with one segment; `/*` tail; query and fragment stripped; `https://x` rejected.
- Pagination merge in the bundle loader: `p1` plus `p2` rows are concatenated.

Runtime target: under 5 s. No DB, no app import except `tools/checks/chain_coherence.py` itself.

### 3.3 check-all

Add one line to `tools/check-all.ps1`, after line 67 ("Screen ledger"):

```
Invoke-Guard "Chain coherence rules (fixtures)" $Python @("-m", "pytest", "tools/checks/test_chain_coherence.py", "-q", "-p", "no:cacheprovider")
```

This makes 13 guards. Search the repo for any doc or test that asserts "12 guards" (for example in `.ai/` or `backend/TESTING.md`). Report each hit in the packet and do not edit `.ai/*`; the coordinator updates routing docs.

### 3.4 L3 clone helper: `tools/chain_clone.py`

```
python tools/chain_clone.py create <name> [--migrate]    # assetops_chainclone_<name>_test from TEMPLATE assetops_polish_full_test
python tools/chain_clone.py drop   <name>
```

- **Refusal: target name.** It refuses unless the target matches `^assetops_chainclone_[a-z0-9]{1,20}_test$`.
- **Fixed source.** The source is the constant `assetops_polish_full_test`. There is no option to change it, and `assetops_demo3_full_test` is never named in the file.
- **Refusal: source sessions.** It refuses when the source has any other session: `SELECT count(*) FROM pg_stat_activity WHERE datname = 'assetops_polish_full_test' AND pid <> pg_backend_pid()` must be 0. It then prints "stop serve and any client of the polish DB first". It never terminates sessions.
- **Create.** `CREATE DATABASE <target> TEMPLATE assetops_polish_full_test`. Connect as `tools/demo_combined.py` `PG_ADMIN` does; import its constants and do not hard-code a password.
- **`--migrate`.** Upgrades the clone to this worktree's head the way `tools/demo_combined.py` `prepare` migrates. Find the `pg_harness._alembic` call in `prepare` (`:378`).
- **Drop.** `drop` removes only names matching the pattern (`DROP DATABASE … WITH (FORCE)`).
- **Not done.** It never ticks, serves or writes anything else.
- **The work dir.** For an in-process `collect` on a clone, use the polish work dir `C:\Users\assef\Bineyame\AssetOpsV1-polC\var\polish_full` **read-only**, as the `--work` argument. `collect` only reads its JSON files.
- **Tests.** `tools/checks/test_chain_coherence.py` covers the name refusals and the fixed source with pure tests: the SQL builder is a function, and it is tested with no DB.

### 3.5 Today's report (deliverable)

Run once, on a quiet machine:

```
python tools/chain_clone.py create ch0 --migrate
python tools/checks/chain_coherence.py collect --work ..\AssetOpsV1-polC\var\polish_full --database-url <clone-url> --out var/ch0-bundle
python tools/checks/chain_coherence.py check --bundle var/ch0-bundle --report .agent/CH-0-today-report.json
python tools/chain_clone.py drop ch0
```

Then write `tools/checks/fixtures/chain_coherence/expected-today.json` from the report:
- Each finding becomes an expectation with a `register` field (I-nn), assigned by the mapping in §2.3.
- A finding that maps to no register issue is listed in the packet as a **new contradiction**. Report it; do not fix it.

> Note. The clone is not ticked, so Kobo's freshness may read Unknown (I-25). The report checks structure and agreement only, and its header says `freshness: not ticked`.

## 4. U3: tick stage timings and peak memory

- **`B/scheduling/stages.py:342`.** Before printing `STAGE_RESULT`, add `result["peak_rss_kb"] = _peak_rss_kb()`.
  - POSIX: `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` (kB on Linux).
  - Windows: `ctypes` `GetProcessMemoryInfo` with `PeakWorkingSetSize // 1024`.
  - Any exception gives `None`.
  - It never changes `code` or any other key.
- **`B/scheduling/tick.py:178`.** Add `"peak_rss_kb"` to the tuple of copied stage keys in `TickReport.as_json`.
- **`B/scheduling/tick.py` `ScheduleTick.tick`.** Wrap the body after the claim so that, on every return path that has a `report.selected`, one line is logged to `perf.LOG` (`assetops.perf`). Keep it never-raising, as `perf.finish` is.

```
{"route": "tick", "outcome": ..., "total_ms": ..., "sites": [{"site_code": ..., "result": ...,
  "stages": {"s3": {"elapsed_ms": n, "limit_ms": n, "share": 0.00-1.00, "peak_rss_kb": n|null}, ...}}]}
```

- `limit_ms` comes from `TickLimits` (`tick.py:57-76`). The stage-name map is:

| Stage | Limit |
|---|---|
| s3 | `s3_seconds` |
| cold_assess, ev_assess | `domain_assess_seconds` |
| mini | `mini_seconds` |
| opportunity | `opportunity_seconds` |
| s4 | `s4_seconds` |
| consequence stages | `consequence_seconds` / `domain_consequence_seconds`, by the names used further down `_site` |

  A stage name with no mapped limit gets `limit_ms: null` and `share: null`, never an error.
- **No other change.** No change to the stage order, timeouts, claims or the printed JSON of `run.py:81`, beyond the extra `peak_rss_kb` key.
- **Tests: `backend/tests/test_ch0_tick_timing.py`** (pure, no DB). Use the existing fake-store and `overrides` pattern in `test_s4_schedule_tick_postgres.py`: find the fake runner. If only a Postgres harness exists, build a fake `ScheduleStore` and a `StageRunner` subclass returning canned results.
  - The perf line is emitted once per tick, with share = elapsed / limit.
  - An unmapped stage gives null.
  - A logging failure does not change `TickReport`.
  - `_peak_rss_kb` returns int or None and never raises.

## 4b. Demo-shaped logic this slice touches (standing rule DS-R1, plan §2.3)

CH-0 edits no product read path, so it fixes no product item. It **records** the demo-shaped items its rules can see, so that the owning slice and SWEEP-DS start from evidence.

| Item | Touched how | Resolution |
|---|---|---|
| 4. Hard-coded wording about where data came from: "Verified on example data" (`B/site_outcomes/board.py:50`, `mini.py:85,89`, `B/estate/placement.py:42`) | Read in the bundle | **COH-12 (info, never failing).** Lists every body string containing "example data", with the Site, the key path and the Site's source mode where the body states one (`source_provenance` / `source_mode`). Owning fix: CH-5a, where copy is derived from source provenance (design §8b item 10). This is a labelled keep until then. |
| 4. Cold and EV Actions recorded at build time | Seen by COH-3 | Recorded in `expected-today.json` with `register: "I-09"` and `owner: "DD-1"`. |
| 2. Fixed claims (Portfolio `opportunity.state` `UNSUPPORTED`, productive use "Not established") | Seen by COH-6 | Recorded with `register: "I-06"` and `owner: "CH-4"`. |
| U3 timing code | New code | It must not hold demo-shaped values. Stage limits are read from `TickLimits`, never typed in. |

`expected-today.json` entries carry an `owner` field naming the slice that resolves them. Reviewers check that no rule in CH-0 is weakened to fit the demo data (DS-R1).

## 5. Acceptance

1. `pytest tools/checks/test_chain_coherence.py` passes in under 5 s, with the cases in §3.2.
2. `vitest run src/__tests__/chainScreenRoutes.test.ts` passes. Adding a fake `<Route path="/x">` locally makes it fail; this is a mutation test that is reverted and noted in the packet.
3. `.agent/CH-0-today-report.json` and `expected-today.json` exist. Each expectation names an I-nn or is listed as new. `check --expect expected-today.json` on the same bundle exits 0. The packet's table lists the findings per rule, which should include at least one finding each for COH-1 (I-08), COH-2 (I-03/I-09), COH-5 (I-21), COH-6 (I-06) and COH-7a (I-04). If one of these is absent, say so; do not force it.
4. `backend/tests/test_ch0_tick_timing.py` passes.
5. Existing tick tests named below still pass.
6. No response body changes: CH-0 touches no read path. The reviewer checks the diff file list.
7. The guards listed below pass, including the new check-all line.

## 6. Pre-flight items (answer from the code, batch them, then stop)

- **P1.** Enumerate the dynamic `path={path}` and `path={route.path}` sources in `F/App.tsx`, and the values of the 22 constants. Produce the exact `screen_routes.json`.
- **P2.** Domain action index row keys for the Action id, the origin Finding id and `created_at` (`B/work/domain_action_index.py` around `:184`, `:260`, `:339`; response shape from `reads.index`).
- **P3.** Confirm the category-to-lens reading for COH-5 against `B/outcomes` outcome-map/1 and `B/estate/index.py:26,127-128`. If the map differs, propose the right constant.
- **P4.** Confirm the estate route query names and that `state=all` is valid (`B/estate/scope.py` `parse_request`).
- **P5.** Confirm whether an in-process app from this worktree needs `var/sites/kobo-001.yaml` or another file store for the board read (`tools/demo_combined.py:363-364` copies it into the tree). If it does, `collect` sets the app's file-store root to the polish work dir's `tree` **read-only**, or the run copies the YAML into this worktree's untracked `var/sites/`. Propose one.
- **P6.** The names of the consequence stages in `tick.py` `_site` after `:380`, for the limit map.

## 7. Localised test ladder (run exactly these; no full suite, no full vitest, no demo prepare)

1. **L1:** `.venv\Scripts\python.exe -m pytest tools/checks/test_chain_coherence.py -q -p no:cacheprovider`
2. **L0:** `tools\run-host-tests.ps1 -- backend/tests/test_ch0_tick_timing.py`
3. **Existing tick tests, scoped:** `tools\run-host-tests.ps1 -- backend/tests/test_s4_schedule_tick_postgres.py -m "not slow"`. These are Postgres tests on the shared test server (`assetops_test`), skipped without `ASSETOPS_TEST_DATABASE_URL`. Also run any non-Postgres test file importing `assetops_backend.scheduling.tick` or `.stages`; list them in the packet.
4. **Frontend:** from `frontend/`, `npx vitest run src/__tests__/chainScreenRoutes.test.ts`
5. **L3:** once, for §3.5 only, after checking that no serve runs on the polish DB.
6. **Guards, run directly** with their check-all command lines and no execution-policy override:
   - A: Architecture seams (`check-all.ps1:56`)
   - W: Agent workflow (`:59`)
   - N: Navigation truthfulness (`:58`), because of the route list
   - the new chain-coherence line
   - **Deferred:** the estate guard self-tests, the delivery, mock-gap and missing-claim fixture tests, and evidence width.

Test DBs: only `*_test` names, and the clone is dropped after use (`.agent/owner-test-db-authorization-2026-10-18.md`). `assetops_demo3_full_test` is never touched, and `assetops_polish_full_test` is only cloned, never connected to by the app or a tick.

## 8. Review focus (fresh Reviewer)

- The rules are pure over the bundle. There is no DB in `check`, and no copy parsing except COH-9(b).
- `chain_clone.py` cannot target or touch any DB other than the clone pattern and its fixed template.
- The timing code never changes a stage result, a timeout or the tick outcome.
- `expected-today.json` maps to register issues honestly: no rule is weakened to make today pass.
- Any change to a product read path is High.
