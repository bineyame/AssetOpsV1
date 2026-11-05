# CH-5c2 handoff (PARTIAL, builder 3 at the context cap) - branch `task/CH-5c2-store-safety`

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

## Remaining, in order
1. L2 tests on the real composers (see `test_out_b4_board_postgres.py:120 _evidence_root`). Prove each non-vacuous.
   - F6: a Performance report, a planted FAILED, and an S2 report on the summary.
   - C4 sweep:
     - Seed plan windows and a verified outcome within 40 days.
     - Candidates are the seeded timestamps, +VERIFIED_LOOKBACK, +-1 us, and local midnights.
     - Assert: body differs at t => valid_until(t0) <= t.
     - Patch `read_scope.clock` and `read_scope.read_instant`.
   - F4 over every stored route: a planted file read and a planted listdir under `COMPOSING`.
2. W6 F4/C3 planted proofs with the CLI on the clone, one run each (~60 s).
3. Packet Q1 table:
   - `verification.py` 149/379/547/784/903 (writers / non-stored detail);
   - `site_index.py:164` (above);
   - `analytics/service.py:151`, `sites/cutover.py:209`, `gateway_api.py:109`;
   - the 31 allowlist entries, by reference.
4. Guards, one at a time under the 10-min cap, with the estate self-tests in parts via `-k`. Then
   `check-architecture.ps1` and `check-agent-workflow.ps1`. Rerun `test_ch5c_response_store_postgres.py` (it passes
   at `ee87d7385`).
5. Packet `.agent/review-packet-CH-5c2.md`. At the top, list the sites needing an Architect ruling:
   - `analytics/cold_reads.py:65`;
   - `actions/verification.py current_state` (~966);
   - the `greatest(clock_timestamp(), :now)` lookup;
   - the upsert of an expired row;
   - `valid_until` in the ETag;
   - `site_history.work`, allowlisted as not in a stored compose.

   Then drop the clone, set the task status to `in_review`, and update ACTIVE_CONTEXT and CODE_STATE.
