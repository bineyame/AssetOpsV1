# W3-01 pending rulings (q5, Lane B commit-2 run, 2026-10-20)

Branch `task/W3-01-estate-claim-action-roots` at `e0d7ab04` (main merged: already up to date). Commit 2 (estate
read/API) was **not started in code**: its one-transaction read needs edits to existing shared files and a guard
that the spec does not assign to Lane B. Earlier q1-q4 are answered in `.agent/W3-01-build-spec.md`.

## Blocking questions

1. **Connection-taking W1 selection helpers: who adds them, and in which commit?** B5/W5 require the estate
   REPEATABLE READ to reuse the W1 selection logic on the estate connection. Every existing W1 read opens its own
   transaction and takes no connection:
   - mini-grid Finding heads/matcher/fence: `analytics/adapters/postgres_finding_store.py:464 index_snapshot`,
     `:114 fence`, `:499 index_lineage` (each via `_read`, `:90-92`);
   - S3 per-day selection: `analytics/dispatch_read.py:123 DispatchReadService.window` (assessment store + evidence
     ledger reads, `OPEN_CUTOFF`);
   - Actions: `actions/adapters/postgres_action_store.py:891 site_window` (used by `actions/site_index.py:155`).
   Run 1 ruling 1 and W3-02 N1 ("Lane A owns every existing shared file") put these files with Lane A; the W3-01
   spec names only new `estate/` files for Lane B. Options: (a) Lane A adds `*_on(c, ...)` variants (like W3-02
   commit `0a` `select_dispatch_days_on`) as a reviewed prerequisite before W3-01 commit 2; (b) Lane B adds them in
   commit 2 under an explicit ownership extension; (c) another split. Please name the exact functions/signatures.
2. **Mini-grid historical cutoff.** `DispatchReadService.window` reads at `OPEN_CUTOFF` and the W1 index has no
   `known_at`. The spec's explicit `known_at` (selected S3 day, matcher pass, Finding revision as of the cutoff)
   needs an as-of S3 selection and matcher-pass query that does not exist. Is W3-02 `0a`'s
   `select_dispatch_days_on(c,tenant_id,site_id,from_,to,known_at)` the intended W3-01 dependency (so `0a` moves
   before W3-01 commit 2), or should W3-01 mark an explicit mini-grid cutoff `HISTORICAL`/`UNKNOWN` without rows?
3. **`$pgReaders` guard owner and timing.** `estate/adapters/postgres_estate_read.py` must import SQLAlchemy;
   `tools/checks/configuration-persistence.ps1:804-830` fails any driver import outside `$pgWriters`. W3-02 Q8 assigns
   the `$pgReaders` change to Lane A (in W3-02 `0c`), which now comes after W3-01. Request written to
   `.agent/W3-01-lane-a-requests.md` item 1; confirm Lane A lands it before W3-01 commit 2 (check-all cannot pass
   otherwise), and whether the estate package also needs a `$domains` entry (`estate/composition.py` as the only
   adapter importer).

## Readings (to confirm with the answers; none built yet)

4. Token v2 is built directly: W3-01 commit 2 implements only `estate-selection/2` (no `/1` builder ever ships).
   `test_selection_token_v2_endpoint_cursor_compatibility` constructs a structurally valid `/1`-digest cursor and
   expects 409 `ESTATE_BASIS_CHANGED`. W3-02 `0c` then keeps only the `$pgReaders` guard work.
5. The shared estate parameter parser (built by Lane B in commit 2) rejects unknown/repeated query keys per W3-02
   Q11-Q13 (`INVALID_WINDOW` for a missing/duplicated window key, else `INVALID_CURSOR`), for all three W3-01
   endpoints, rather than waiting for a Lane A integration.
6. Cold/EV coverage calls the existing connection-taking `ColdReadService._snapshot(c, ...)`
   (`postgres_assessment_store.py:1607`) and `EvReadService._snapshot(c, ...)` (`:2189`) on composed service
   instances; W5's "extract" needs no edit because both already take `c`. If a public name is required, that is
   item 1's ownership question.
7. `main.py` router mount stays Lane A (request item 2). Commit-2 API tests mount `build_estate_router` on a local
   FastAPI app, as the existing `finding_index_api` tests do.
8. W3-01 keeps its own `status`/`coverage.state` enums (`CURRENT|PENDING_RECOMPUTE|STALE_SOURCE|HISTORICAL|UNKNOWN`,
   `COMPLETE|PARTIAL|UNKNOWN`); W3-02's `EMPTY`/`EMPTY_SCOPE` are W3-02-only. Complete empty authorized scope is
   `coverage.state=COMPLETE` with zero counts, per the W3-01 example text.
9. The shared financial `group_key` (W3-02 commit 3) is not a W3-01 concern; W3-01 emits no group key.
