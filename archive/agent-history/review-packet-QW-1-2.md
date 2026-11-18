# Review packet: QW-1 + QW-2 (per-read timing, reuse within one request)

Task: design proposal §14b (AG-22), diagnosis §11b P-1..P-6. Branch `task/QW-1-2-load-timing` from `73a558a1b`.
USER_REVIEW_REQUIRED: no screen or wording change. The Architect needs to decide on the follow-ups in R1–R3.

## Outcome

- **QW-1 delivered.** Every producer read a board makes is timed through `Reads.call`/`pages` (`timings[name] = [calls, ms]`, `time.perf_counter`). Also timed: each Site board inside the summary, the summary's scope and window-choice reads, every estate snapshot, and the Portfolio sections (scope, findings, actions, evidence, money, coverage, rows, summary, disclosure, cards). There is one JSON line per request on logger `assetops.perf`, for the board, summary and Portfolio routes. The `Server-Timing` header is sent only when `ASSETOPS_SERVER_TIMING=1`.
- **QW-2 delivered as specified.**
  - The summary now makes one batched estate snapshot for all Sites (`site_selected_windows_many`, `site_readiness_many`, `site_work_rows_many` with `snap=`, through `read_snapshot`). Before, it made one to three per Site: 7 estate snapshots per summary before, 2 now (the route's Site list plus the batch). Every port takes its entry only on an exact match of its arguments (6/6 hits on the demo). Any batch failure falls back to the per-Site reads.
  - ~~The per-board memo~~ was removed in fix round 1 (see below).
- **Result: QW-2 gives no measurable speed-up on this data.** The estate time is spent computing each Site's selection, not opening snapshots or scopes (`estate.imported_sites` totals 15 ms per summary). The memo has 0 hits, because no identical `Reads` call happens inside one board. The acceptance line "the outcome summary must be measurably faster" is **not met** (see Deviations). QW-1's timings show where the time really goes (R1).

## Timing (in-process, `assetops_polish_full_test`)

How it was run: Postgres sessions were forced read-only (`PGOPTIONS=-c default_transaction_read_only=on`). There was no server, scheduler or tick. Runs were interleaved: A (main `73a558a1b`) alternated with B (this branch) in separate processes. Cold is the first request in a fresh process (5 per side). Warm is 5 repeats in process 1.

| URL | cold median A → B (ms) | warm median A → B (ms) | peak working set A / B (MB) |
|---|---|---|---|
| `/api/estate/outcome-summary?from=2026-10-25T00:00:00Z&to=2026-11-01T00:00:00Z` | 12,220 → 13,046 | 9,905 → 9,534 (−3.7%) | 128.0 / 126.5 |
| `/api/estate/portfolio` (same window) | 8,201 → 8,304 | 7,052 → 7,226 | 123.8 / 123.7 |
| `/api/sites/KOBO-001/outcome-board?date=2026-10-31` | 10,132 → 9,458 | 8,057 → 8,374 | 125.2 / 125.6 |

Run-to-run spread on this machine is ±15–25%; for example, the Kobo board's cold runs on B ranged from 9.3 to 13.1 s. Every A/B difference above is inside that noise. Peak memory did not rise, and no process, pool or connection was added.

Where the time goes (one warm request on B, `assetops.perf`):
- **Summary, about 11 s:**
  - Kobo board: 6.0–7.7 s. Inside it, `mini_overview` takes 2.8 s and `finding_index` 2.0–2.4 s.
  - `summary.prefetch`: 2.5 s, of which readiness is 1.5 s, work rows 0.7–0.9 s and windows 0.1–0.2 s.
  - `summary.scope` (the route's Site list): 0.9–1.2 s.
  - EV board 0.6–0.9 s, cold board 0.5–1.0 s.
- **Portfolio, about 7.3 s:** evidence 3.8 s, findings 1.7 s, money 1.2 s, disclosure 0.34 s, everything else under 0.11 s.
- **Kobo board, about 9.2 s:** `mini_overview` 2.8 s, `finding_index` 2.0 s, `evidence_readiness` 1.25 s, `estate` 0.75 s, `action_read` 0.74 s, `mini_depth` (4 calls) 0.64 s.
- **Repeated work, from a profile and a call counter on one summary:** `postgres_assessment_store._window` runs 55 times over 41 distinct arguments. The Kobo board day's dispatch window (2026-10-31) is read **13 times**: 7 live and 6 with the read-time cutoff. The repeats cost about **2.3 s of 5.2 s** spent in that method.

## Byte identity

14 capture URLs were byte-identical before and after on the final revision:
- the three acceptance URLs;
- the Kobo boards for 25–30 Oct;
- the cold and EV boards for the week;
- the summary for October;
- the `known_at=2026-11-03T00:00:00Z` variants of the summary, Portfolio and Kobo board.

The Portfolio without `known_at` differs from request to request even on main (`window.known_at` and `selection_token` carry the read time). Once those two fields are normalised it is equal, and its `known_at` variant is byte-identical. Each URL's body was also stable across its repeated runs.

## Checks

- **Unit** (`test_qw1_perf.py` 8, `test_qw2_reuse.py` 7, plus the adjacent outcome, Portfolio and evidence API tests): 448 passed, 1 skipped (a Postgres-only test with no URL set).
- **Postgres** (`tools\run-host-tests.ps1`, `*_test` DBs):

  | Test file / selection | Result | Time |
  |---|---|---|
  | `test_qw2_many_postgres.py` | 1 passed | 95 s |
  | `test_w303_portfolio_scope_snapshot_postgres.py -k "three_domains or foreign_tenant"` | 2 passed | 264 s |
  | `test_out_c4_ev_warnings_postgres` + `test_out_d5 -k kobo_estate_objectives` | 2 passed | 116 s |
  | `test_out_b4_board_postgres` + `test_out_d5 -k "kobo_estate_finding_rows or cold_w502 or ev_w504_positive"` | 4 passed | 203 s |

- **Non-vacuous proofs** (each change was committed first, then reverted with `git checkout`):
  - Dropping `known_at` from the readiness prefetch key fails `test_qw2_reuse` (1 failed).
  - Assigning readiness to the wrong Site in `site_readiness_many` fails `test_qw2_many_postgres` (`- NONE + LIMITED`).
- **Guards: 12/12 pass.** They were run one by one because `check-all.ps1` as a whole exceeds the 10-minute cap:
  - architecture, 189 s (needs `ASSETOPS_GUARD_PYTHON` set to the venv, as `check-all` sets it);
  - estate guard self-tests, 7 passed in 341 s;
  - the other 10 guards, 0 failures in 23 s. The missing-claim scan needs `frontend/node_modules`; I linked it as a junction to the plan2 checkout.
- Not run: the full backend suite (machine policy); `test_w303_portfolio_scope_snapshot_postgres` beyond the 2 tests above (8 deselected, each about 130 s); and the other board and summary Postgres tests.

## Deviations

1. **"Measurably faster" is not met.** Items 1 and 2 are built exactly as scoped. On this dataset they remove only snapshot-open overhead, about 0.5 s of estate time, which is lost in machine noise, and the memo finds no identical calls. No further optimisation was made without Architect sign-off.
2. **`*_many` signatures take per-Site windows.** `site_readiness_many(tenant, {code: (from, to)}, known_at, *, snap=None)` and `site_work_rows_many(tenant, {code: (day_from, day_to, work_from, work_to)}, ...)` take a window per Site, because a cold or EV Site's readiness window depends on its own event window. `site_selected_windows_many(tenant, site_codes, from, to, ...)` matches the spec. There is one scope per distinct window, not strictly one per request.
3. **Measurement harness overrides.** `json_evidence_store`, `legacy_comparison_file` and `json_commit_store` roots point at the demo tree (`AssetOpsV1-polC\var\polish_full\tree\var`) so the Kobo comparison gate opens. That folder's file list and mtimes were checked unchanged after every run.
4. **Postgres runs exceeded the 600 s tool cap twice.** A test run and the `check-all` run hit the cap and were moved to the background by the tool. Both were killed by PID and re-run in smaller chunks.

## Residual risk

- Memo hits return the same object: a caller that mutates a read result would see its own mutation on a second identical call. Today there are 0 hits.
- A prefetch entry is consumed once, so a second identical port call in the same summary reads live.
- The prefetch reads all Sites on one snapshot, where before each read had its own. This is consistent by construction, but a store write landing mid-summary would now be seen by all Sites or by none.

## Recommended next targets (Architect sign-off needed)

- **R1, highest.** Add a request-scoped memo of the assessment-store window snapshot (`postgres_assessment_store._window` / `window_snapshot`, keyed on site, analytic, window and cutoff). Expected saving: about 2.3 s per summary, and a similar share of the Kobo board, which reads its board day 13 times. It changes REPEATABLE READ transaction boundaries, so it needs an Architect ruling.
- **R2.** List the summary route's Sites with `_scope` only, instead of `estate.scope` (which computes Finding coverage for every Site just to read their codes). Expected saving: 0.9–1.2 s per summary, with an identical Site list. The trade-off: a coverage-inconsistency 409 would then surface per board instead of on the route.
- **R3.** Profile the evidence selection, which takes 3.8 s of the Portfolio and 1.5 s of the summary's readiness; per-row `cited_provenance` is the likely cost. Look also at `mini_overview` and `finding_index` (P-3, about 5 s of the Kobo board): candidates for the day-snapshot work in CH-0.

## Fix round 1: memo removed

Architect ruling: merge QW-1 (timing) and QW-2's batched estate reads (`*_many` and the summary prefetch), but remove the per-board memo (0 hits, and it returned the same object, which a caller could mutate). R1–R3 move into CH-5a.

Commit `3bf98c405`:
- `Reads` in `site_outcomes/mini.py` loses `memo`, `memo_hits`, `_memo` and `_key`; `call` is back to timing only. `cold.py`, `ev.py` and `mini.compose` use `Reads()`. The memo helper had no other user; no `perf.memo.*` record remains.
- `test_qw2_reuse.py`: the 3 memo tests are removed; the summary-batching tests are kept (QW-1 timing tests unchanged).

Re-run on `3bf98c405`:
- Unit: `test_qw1_perf.py` + `test_qw2_reuse.py` = 12 passed (6 s). Adjacent non-Postgres selection (`out_`/`outcome`/`qw`, excluding Postgres files and `test_w502_domain_intent_api.py`, which has a collection NameError on `COLD`, not touched by this change): 538 passed, 3 skipped, 1 failed (`test_run_store_loader ... without_libyaml`, environment-dependent, unrelated to the files changed).
- Postgres (`toolsun-host-tests.ps1`): `test_qw2_many_postgres.py` 1 passed (118 s); `test_out_c4_ev_warnings_postgres` + `test_out_d5_objectives_postgres` 4 passed (289 s); `test_out_b4_board_postgres` + d5 `-k "kobo_estate_finding_rows or cold_w502 or ev_w504_positive or test_out_b4"` 6 passed, 2 deselected (175 s); `test_w303_portfolio_scope_snapshot_postgres -k "three_domains or foreign_tenant"` 2 passed, 8 deselected (187 s).
- Byte identity (harness, in-process, read-only on `assetops_polish_full_test`, no serve or tick): 14 capture URLs plus `summary-oct` run against the plan2 tree (backend identical to base `73a558a1b`) and this tree. All byte-identical; the Portfolio without `known_at` differs only in `window.known_at` and `selection_token` (read time) and is equal once those are normalised, as before.
- Guards run individually: architecture (needs `ASSETOPS_GUARD_PYTHON`) passed; agent workflow passed; estate guard self-tests 7 passed (287 s). No other guard reads the changed files.
- Deferred: the 8 unrun Portfolio-snapshot Postgres tests (`test_w303_portfolio_scope_snapshot_postgres`, deselected above) are deferred to the end-game full suite E2 under plan decision OD-P4.
- Residual risk "memo returns the same object" no longer applies.
