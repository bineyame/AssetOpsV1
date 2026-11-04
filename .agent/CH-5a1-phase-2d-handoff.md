# CH-5a1 phase 2d handoff - COMPLETE (L2, collector, estate guard self-tests, guards). Next: phase 3.

Authority unchanged: build sheet Part A (incl. §A12). Previous: `CH-5a1-phase-2c-handoff.md`.
Branch `task/CH-5a1-chain-reader`. Commits this phase: 95f7bface, 4d0d6aa82 (L2), 073e96f2f (collector), this handoff.

## Landed
- **L2 `backend/tests/test_ch5a1_reader_postgres.py`** (7 tests). One module seed on `pg_harness.fresh_database()`
  (the s1 `engine` fixture): CaseRunner F01+F02, then `_settle_chain` from `test_out_b4_board_postgres.py`. Not on
  `setup_cache`: CaseRunner cannot be cached (CH-2 deviation D-3). Tests run in file order, read-only first:
  - `snapshots` equals the per-key max revision from raw `site_day_snapshot`;
  - `finding_heads` equals a Python head rule over the raw rows (2 heads, one thread, occurrences 1 and 2, other
    domain = ());
  - R8 settled after the seed;
  - the board route under TestClient: `read_scope.scope` is wrapped by monkeypatch (perf.route looks it up as a module
    attribute, `perf.py:133`), no production endpoint. Checks: non-empty `chain.*` names, none of the L1 `DELETED`,
    `max_per_key() == 1`;
  - known_at hides a later snapshot selection (an appended revision+1, cut on the DB clock);
  - F04 run stepwise:
    - R8 is False before the consume and True after it, twice;
    - k1 (runner story clock) hides F04's occurrence;
    - k2 hides F04's revision 2;
    - L5: F04 is occurrence 3 on the F01/F02 thread, and `lookup` gives occurrences 2 at k1 and 3 at None;
  - last, `has_change` equals `bool(detail.change)` on the HTTP detail, False after ACCEPT and True after APPLY;
    frozen.
  - L2m TODO block is in the module docstring.
- **Collector (`tools/checks/chain_coherence.py`)**:
  - `LOCAL_DAY_TZ` = {kobo, cold: Africa/Addis_Ababa};
  - `day_windows` gives Kobo and Cold days as the Site-local day of `start`. Kobo `date` = that local date. EV keeps
    `[start, end)`. The `estate` bounds are still the enclosing UTC midnights;
  - `_board_query(path, query, window)` maps `date=D` to the body's own `window.from/to`. With no body window there is
    no equivalence (never UTC midnights). `is_own_self_link` passes `b.body["window"]` and is otherwise unchanged.
- **`tools/checks/test_chain_coherence.py`**:
  - adapted for the intended R6 change: the date equivalence, does-not-widen and `day_windows` tests now use Addis
    local days;
  - added: the Addis UTC-day self-link is a contradiction; EV is unchanged; parametrised Kobo/Cold cases across UTC
    midnight. The new UTC-day case fails on the old `_board_query`.

## Tests run
| file | result |
|---|---|
| test_ch5a1_reader_postgres.py (`tools\run-host-tests.ps1`) | 7 passed, 0 failed, 0 skipped (25 s) |
| tools/checks/test_chain_coherence.py | 87 passed, 0 failed, 0 skipped |

There is no importer of `mechanism_dataset` in this tree (see deviation D-2d-1).

## Estate guard self-tests (`tools/checks/test_estate_guard.py`, 15 tests, by node id, PowerShell tool, foreground)
| chunk | tests | result | wall |
|---|---|---|---|
| 1 | pg_reader x2, domain_driver, domain_action_index | 4 passed | 139 s |
| 2 | trial_comparison x3, thread_writer, thread_sources_reader, chain_reader | 6 passed | 258 s |
| 3 | snapshot_writer, event_store, event_page, event_tables_foreign, event_migration | 5 passed | 362 s |
| **total** | 15 | **15 passed, 0 failed** | 759 s |

There is no `pytest-randomly` plugin (only xdist), so `-p no:randomly` was not passed. These tests must run from the
PowerShell tool: run from Git Bash, the child `powershell` refuses the scripts ("running scripts is disabled").

## Guards
`tools/check-architecture.ps1`: Architecture check passed. `tools/check-agent-workflow.ps1`: Agent workflow check passed.

## Production fixes
None this phase. The L2 ordering quirk is test-only: run before F04, the APPLY (a new reserve FoundationRevision)
left F04's first match with no unconsumed `finding.revised`. The APPLY test therefore runs last. The behaviour is
recorded in its docstring and not investigated further.

## Rulings and deviations to carry to the packet
- **Coordinator rulings on the 2c open questions (all four defaults accepted):**
  1. c3 window spy: accepted as an R5 consequence. Phase 3 greps the A-side log for "batched estate reads fell back".
  2. idx_gaps p5: the NO_DATA chain day is accepted (deleted read). L2m covers real readings.
  3. EV site-type fix: L3 A/B reads EV readiness, listed per day in the packet (E1 "EV 20/27 Oct Limited -> Low").
  4. The 2b Known Deviations stand: estate read on UTC-day bounds; Q2 dispatch refusal; Q8 pooled local days;
     Findings settledness from R8 alone.
- **D-2d-1:** `backend/tests/mechanism_dataset.py` is not in this branch, because MD-0 (`task/MD-0-mechanism`,
  36427c1b2) is not merged. The `build_work` local-day change (`mechanism_dataset.py:1062` on that branch,
  `start = datetime.combine(d, time.min, tzinfo=timezone.utc)`) is still to do. After MD-0 merges, merge main in and
  set `start` to the Addis local midnight converted to UTC, so `end = start + 1 day`. `day_windows` already takes the
  local date of `start`, so it reads both the old and the new `days.json` correctly.
- **D-2d-2:** "known_at hides a later selection" is read as the snapshot store's latest-row selection (DISTINCT ON
  revision DESC). Opportunity `selected_at` is not seeded in L2 (no opportunity on the S4 case).
- **D-2d-3:** L2 is not on `setup_cache` (CaseRunner is uncacheable, CH-2 D-3). It seeds once per module.
- **Importer list addition:** `test_ch5a1_reader_postgres.py`, `tools/checks/test_chain_coherence.py`.

## Commands phase 3 needs (real paths, as found in `tools/`)
- Clone (source is fixed: `assetops_polish_full_test`; target `assetops_chainclone_<name>_test`):
  - `python tools/chain_clone.py create ch5a1 --migrate`
  - `python tools/chain_clone.py settle ch5a1`
  - `python tools/chain_clone.py drop ch5a1`
- Backfill, on the clone with `DATABASE_URL` set to the clone URL: `python -m assetops_backend.chain.backfill --steps a,b,c,d`.
  The flags are `--tenant` (default demo), `--site`, `--steps` (default a,b,c,d,e) and `--dry-run`.
- Coherence:
  - `python tools/checks/chain_coherence.py collect --work <work-dir with story.json, days.json> --database-url <clone url> --out <bundle> [--known-at <iso>]`
  - or `collect --base-url http://127.0.0.1:8990`
  - then `python tools/checks/chain_coherence.py check --bundle <bundle> --expect tools/checks/fixtures/chain_coherence/expected-today.json --report <out.json>`
- **A/B collector:** no dedicated script exists in `tools/`. CH-3 did its A/B ad hoc: `chain_coherence.py collect` run
  from a read-only main worktree (A) and from this branch (B) on their clones, both given B's `days.json`, then a JSON
  diff after normalising `window.known_at`, `selection_token` and `links.self` (§A6; QW packet `:45`). Phase 3 must
  script it in scratch.
- **`tools/chain_perf_probe.py` does not exist**, and `git log --all` shows no history for it. §A9 item 5 names it.
  Phase 3 writes it or records the gap. Ask the coordinator.
- **P1 profile:** no script exists either. `tools/profile-summary.py` is the py-spy test profiler, not P1. P1 means
  cProfile of one warm `GET /api/estate/portfolio` (story week) on the settled clone, top 20 cumulative under
  `select_evidence_scope` / `select_financial_scope`, through an in-process TestClient (`demo_combined_finish.app_client`).
- Guards: `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1`. Run the estate guard self-tests in the 3
  chunks above, from the PowerShell tool.
