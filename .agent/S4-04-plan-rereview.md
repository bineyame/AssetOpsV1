# S4-04 plan re-review after fix round 1 (fresh Claude reviewer, no code)

Date: 2026-10-15
Reviewed: `tasks/S4-04-site-finding-index.md` on `plan/S4-04-refine` at HEAD `45df4788`. The fix diff is `c82b00c2..45df4788`; it touches only the packet, the fix brief and the Planner log.
Inputs: `.agent/S4-04-plan-review.md` (RETURN M1; L1-L5), `.agent/planner-S4-04-fix-brief.md`, `.agent/architect-S4-04-answers.md` / `D-2026-10-15-s404-contract`.
Scope: a targeted check of the dispatch items only.

## Verdict: ACCEPT

M1 is resolved. All three rulings are folded in with their tests. The no-snapshot choice is stated, and L1, L3 and L4 are done. I found no new High or Medium. Two Lows follow. They do not block, and the implementer can apply them while building.

## Checks

1. **M1: resolved.**
   - Read contract, packet line 139: `mini-grid-dispatch` is marked as a **new API domain token**. It maps to `finding.domain='mini_grid' AND finding.analytic_id='dispatch'`, to the S3 `dispatch` discovery basis and to the S4 `MATCHER_VERSION`.
   - Any other domain, or other invalid input, gets a typed 422 with "no status, rows or count, never `CURRENT` zero".
   - The response echoes both the requested and the resolved domain/analytic.
   - Tests: phase 1 includes "unsupported-domain 422 (never `CURRENT` zero)", and line 158 adds assertions for the echoed mapping and for no assessed zero.
   - Citations verified on `task/S5-01-site-overview`:
     - `finding_episode.py:76` is `MATCHER_VERSION = "finding-episode-3"` and `:78` is `DOMAIN = "mini_grid"`.
     - On main, `:68` is `DOMAIN`.
     - `dispatch.py:27` is `ANALYTIC_ID = "dispatch"`.
     - `assessment_worker.py:51` is `DOMAIN = "dispatch"`.
2. **Rulings: folded in exactly.**
   - Q1: 409 `INDEX_BASIS_CHANGED` with a machine-readable reason, a page-one instruction, and no rows, count or replacement cursor. A malformed cursor is a typed 422. Both are tested in phase 1.
   - Q2: the durable-snapshot rule and the no-snapshot branch, both with no rows and null count. A no-snapshot stale/failed test is present.
   - Q3: the fixed-point closure across actual 20-minute bridges on one fenced basis, and the 62-day total cap with 409 `INDEX_CONTINUITY_LIMIT`. Every inspected day is recorded with its S3/S4 seq, including empty days, and the cap is stated as not proof that continuity ended. Tests cover a chain beyond one neighbour, a dirty or failed neighbour, and cap failure.
   - Phase-2 UI states include continuity-limit Unknown.
   - The Architect question list is replaced, line 170.
3. **No-snapshot: stated.** Line 145 reads: "S4-04 builds **no durable snapshot**, migration or new writer". Stale and failed reads return no rows and null `total_count`. See L-a for one leftover phrase.
4. **L1: done.** Spot-checked with `git show task/S5-01-site-overview:<path>`. The stacked-base note is at line 135, and the LR-01 replay change is noted.
   - Store:
     - `_insert_revision`: `def` at 162, `return rid` at 214.
     - `rows`: 216-233.
     - `finding_detail`: 237-276.
     - `revision_lineage`: 278-308.
     - `match_state`: 404-420.
     - `findings_over`: 422-436, with an inclusive `lo <=` and an ascending sort.
   - `upstream.py`: 86 is `_match`, and the call to `findings_over` is at 139.
   - `finding_read.py:617`.
   - `finding_api.py`: `open_scope` at 63, the 409 at 88-91, and the route at 112/113-135.
   - `App.tsx:248-255`.
   - One trivial offset: the `findings_over(` call in `health.py` begins at 253, and 254 is its argument line. Not a finding.
5. **L3: done.**
   - The packet names `backend/tests/test_s4_finding_index_postgres.py` and adds it to the `backend/TESTING.md` "S4 Finding and money" command. That section exists on the base at line 100.
   - It names `tools/s404-finding-index-evidence.mjs` for 1440/390 px.
   - A skipped run is recorded as `not run` with its unmet precondition.
6. **L4: done.** The walkthrough has `settle` after both `late` and `gate --open`, modelled on `recover` (`tools/s4_finding_walkthrough.py:309,324`). It also states that `serve` installs no schedule.
7. **`total_count`: done.** It is null unless the status is `CURRENT`, line 141, and restated for stale/failed at line 145.
8. **No new fail-open.** The other new paths are each closed by 422 or 409 with no count. Those are the unsupported domain, the cap, a basis change and a malformed cursor.
9. **Registry checker.** `node frontend/docs/architecture/check_v69_dependency_registry.cjs` printed "Registry valid: 228 nodes, 11 linked pilot panels", exit 0.

## Low findings (non-blocking)

- **L-a (Low, consistency):** line 143 still allows "one transactionally consistent read **or atomically published projection**". A published projection would be a durable store with a writer and a migration, which contradicts the no-snapshot, no-migration, no-writer statement at line 145. Fix: delete "or atomically published projection", or add "(not in S4-04)".
- **L-b (Low, walkthrough wording):** line 164 says "see Unknown/stale/failed without zero claims". It should also say that the stale and failed variants show **no rows**, so that the owner does not expect historical rows. This is what the no-snapshot branch implies.

## Not run

No test suites and no build. This is a plan re-review. Only the registry checker and `git show` spot checks were run.
