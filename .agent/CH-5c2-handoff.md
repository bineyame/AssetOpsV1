# CH-5c2 handoff (PARTIAL, builder 4 at the context cap; builder 3 before) - branch `task/CH-5c2-store-safety`

Spec: `AssetOpsV1-plan2\.agent\build-sheet-CH-5c.md` §8.6 + §8.7; pre-flight `.agent/CH-5c2-preflight.md`.
Env: `scratchpad/ch5c2/env.sh` (absolute PYTHONPATH of this worktree; plan2 venv; `$WK` work dir with keys.json).
Test DB: `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test`.
Clone `assetops_chainclone_ch5c2_test` is at `0048_chain_response_expiry`, settled, with store rows. KEEP it for the
sweep, then `python tools/chain_clone.py drop ch5c2`. CH-9 is NOT on main (checked `git log main`), so no re-point.

## Landed by builders 2 and 3
- `9e2315ae0` (b2): W6 CLI compose mode, F4 audit hook, Q5 capture, C3 listener; L4 trigger-only guard rule.
- `ee87d7385` (b3): `tests/test_ch5c2_store_safety_postgres.py` covers M1 x3 ports, L1 conflict, C2 valid_until +
  moved clock, historical NULL, and L4 TRUNCATE refused / replica allowed. `tests/test_ch5c2_clock_guard.py` (L0).
  Docstrings: `watermark.py` F, `response_store.py`, `stages.prebuild` C5.
  **Bug found and fixed:** an expired live row blocked its own re-warm. `ON CONFLICT DO NOTHING` under the same W
  made every request after expiry a `race` that was never stored again, which broke C5. `_INSERT` is now `DO UPDATE ...
  WHERE chain_response.valid_until <= greatest(clock_timestamp(), :now)` (`postgres_response_store.py`).
  `etag(..., until)` now includes `valid_until`, so the re-warmed body never shares the expired body's tag (CH-5b 304).
  Both are Known Deviations: the sheet defines ETag over route/key/W/version only.
- `4e7240ce7` (b3): Q4 parity test, old SQL against `current()`. It covers the live real clock, the live app clock at
  each instant, and historical reads, each at `recorded_at` +-1 us, with >= 3 distinct head sets.
- `2e6399e3a` (b3):
  - `config/chain/stored-composer-modules-v1.json`: 122 modules, reviewed. All are `assetops_backend.*` composer or
    read modules; there is no writer CLI.
  - C3 SQL allowlist: 31 entries, each with a reason.
  - Five composer-module Python clocks now read `read_scope.clock()`, semantics-preserving:
    `analytics/assessment_worker.py utc_now`, `evidence/service.py system_clock`, `evidence_migration.py _now`,
    `performance_migration.py compared_at`, `sites/foundation_service.py utc_now`.

## Non-vacuity proven (planted, then `git checkout --`)
- Proven:
  - M1: removing the lookup and store `try` fails the tests.
  - L1: removing the `inserted` check fails.
  - C2: dropping the boundaries fails.
  - Q4: replacing `within` with `True` fails.
  - L0: the planted `datetime.now()`, `utcnow` default and unlisted `now()` are tests in the file.
- Not yet:
  - L4 is structural only: a missing trigger would let the TRUNCATE succeed.
  - The W6 F4 and C3 hooks still need planted proofs with the CLI: a planted read and listdir in a composer, and a
    planted `WHERE ... now()`.

## L3 results on the clone (head `2e6399e3a`)
- W6, 61 s: `requests 23 non-200 0 tables 79 unresolved [] untracked [] event_consumption_read True clock_predicates 0
  file_violations 0 modules 122 unlisted_modules []`.
- prebuild: 23 requests (stored 20, hit 3), 42.5 s.
- `fresh`: 23/23. All 23 rows have `valid_until` (20:59:59Z to 23:59:59Z).
- Q1 `site_index.py:164 read_at`, proved absent:
  - `actions.site_index` IS in the module set.
  - `"read_at"` occurs in 0 of 23 stored bodies (SQL over `chain_response.body`).
  - `fresh` masks only known_at/selection_token.
- Idle: two ticks (the settle tick step only, 74 s each). `watermarks --compare` gives `moved {}`, and F is unmoved for
  all 4 Site sets.
- F (scratch `fstate.py`, clone env): median 3.1-3.3 ms per Site and 8.1 ms for all three, so <= 20 ms. The first cold
  call reached a 180 ms max (OS cache); note this in the packet.

## Landed by builder 4 (heads `a78579ef1`, `5d8342845`, `2186fda25`)
- `tests/test_ch5c2_real_composers_postgres.py`: the Kobo `guardrail` case (b4 `_build_kobo`, own DB
  `assetops_out_ch5c2_guardrail_test`, ~1 min build), 6 tests, **6 passed in 334 s** at `2186fda25`. PATHS = every
  stored route (board dated + dateless, summary, findings, portfolio, scope-ids; summary window <= 31 days).
  - F6 board: hit; new PASSED report -> not hit, equals fresh; planted FAILED -> body changes (AVAILABLE -> PARTIAL).
    F6 summary (no S2 stand-in): hit; `evidence_migration run` -> not hit, body changed; planted FAILED -> back to
    the pre-report body. **Non-vacuous:** F dropped from W (`response_store.py:130`) -> both fail `'hit'` (rc6).
  - C4 sweep (`tools/chain_response_probe.py` `sweep`/`candidates`/`seeded_instants`, also a CLI `sweep` command):
    `_place` shifts one verification plan's later window by whole days past t0 and one outcome's recorded_at to
    t0-30d+3h (replica role). 569 seeded instants, ~1720 candidates; only candidates before valid_until(t0) are
    composed (later ones satisfy the claim). Portfolio/dateless board valid_until = the placed later_end - 1 s, so
    the placement registers. 0 violations.
    **Non-vacuity NOT proven:** planting `within` without the end registration (`read_scope.py:218`) still passed
    (rc7): no body on this seed changes at the placed later_end, so the registration is conservative here. Needs a
    planted visible defect (e.g. an unregistered clock-dependent field in one composer) or a seed whose label flips
    at later_end. Also check `verification.current_state:965` `now = at or self.clock()`: what `at` is on the board.
  - F4: clean run over every route records 0 violations; planted `open` and `os.listdir` inside each compose are
    recorded on all 5 routes (the proof). Q5 on this seed found two unlisted modules, now fixed (below).
- **Found + fixed:** a dateless board/overview reads its day from `PostgresScheduleStore.db_now` (DB clock, UTC
  date), unregistered; the midnight cap is Site-local, so a Site west of UTC would be served yesterday's body
  after 00:00Z. `site_overview/read.py db_today` now wraps it in `read_scope.read_instant` and registers the next UTC
  midnight via `within`. `site_overview.read` and `scheduling.adapters.postgres_schedule_store` joined
  `stored-composer-modules-v1.json` (124 modules); the schedule store's db_now is allowlisted as a capture and its 9
  writers as writers (`test_ch5c2_clock_guard.py`, 5 passed). **Add to the Architect-ruling list.** The W6 CLI on
  the clone did not reach these (all prebuilt boards carry `date=`); re-run W6 on the clone (module count 124 now).

## Remaining, in order
1. C4 non-vacuity (above). Then rerun `test_ch5c2_real_composers_postgres.py` once (~6 min, under the cap).
2. W6 F4/C3 planted proofs with the CLI on the clone, one run each (~60 s), plus one clean W6 at the new head.
3. Packet Q1 table:
   - `verification.py` clock reads at the current lines (builder 4 mapped them): 150 `freeze`, 380
     `bind_later_selection`, 548 `evidence`, 785 `evaluate`, 904 `_cost_check` (writers / non-stored detail);
     965/983 `current_state` (Architect ruling);
   - `work/site_index.py` read_at refusals 342-356 (constant for a live request) and the `read_at` absence (above);
   - `analytics/service.py:151 _reconcile`, `sites/cutover.py:209 _current`, `gateway_api.py:109
     read_gateway_health` (not stored routes; confirm each with a grep before citing);
   - `site_overview/read.py db_today` (fixed by builder 4; see above);
   - the allowlist entries (now 41), by reference to `test_ch5c2_clock_guard.py`.
4. Guards, one at a time under the 10-min cap, with the estate self-tests in parts via `-k`. Then
   `check-architecture.ps1` and `check-agent-workflow.ps1`. Rerun `test_ch5c_response_store_postgres.py` (it passes
   at `ee87d7385`).
5. Packet `.agent/review-packet-CH-5c2.md`. At the top, list the sites needing an Architect ruling:
   - `analytics/cold_reads.py:65`;
   - `actions/verification.py current_state` (~966);
   - the `greatest(clock_timestamp(), :now)` lookup;
   - the upsert of an expired row;
   - `valid_until` in the ETag;
   - `site_history.work`, allowlisted as not in a stored compose;
   - the dateless board day `db_today` (UTC date, now registered at the next UTC midnight).

6. C4 sweep on the clone: `python tools/chain_response_probe.py --database-url <clone> --work $WK sweep
   [--t0 ISO] [--limit N] [--only substr]` (writes store rows; split by `--only` to stay under 10 min), then
   `python tools/chain_clone.py drop ch5c2`. Coordinator owns ACTIVE_CONTEXT/CODE_STATE (do NOT edit them); set the
   task status to `in_review`. Lane-2 rule: wait while `mechanism_dataset.py`/`chain_clone.py`/collect runs.
   CH-9 was still not on `main` at builder 4 (checked).
