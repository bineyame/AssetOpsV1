# FIX clock-dependent power fixture - review

Reviewer: fresh Claude reviewer (did not author). Branch `task/FIX-clock-dependent-power-fixture`,
`git diff 32adae2f..70b00b73` (commits 44c09c5c, 70b00b73). Test code only; no product code changed.

## Verdict: ACCEPT

The four Low findings are optional. Fixing them on the branch is welcome but does not block the merge.

## Per-question findings

1. **`publishing_submit` seam - correct.** `CaseRunner.submit` (test_s3_dispatch_assessment_postgres.py:74-75) builds
   `BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=Clock(decided_at)), Clock(decided_at))`;
   the change (test_s405_resolver_postgres.py:218-219) is now identical. The override is the ledger's documented test-only
   decision-instant seam (postgres_evidence_ledger.py:141-146, 526-527; README-db.md:155), so evidence `recorded_at` follows
   the fixture clock as in every other ledger-building fixture. No production behaviour is touched.

2. **`frozen` rounded up - safe.** Rounding up (test_w303_portfolio_fixture_postgres.py:264-265) only moves `frozen`
   later, so `frozen >= latest_recorded + 1us`, `>= db_now` and `>= runner.now + 1min` all still hold. The estate parses
   `known_at` at full precision and emits it at second precision, so a microsecond `frozen` could never equal the
   `known_at` the server returns (fixture:297, scope_snapshot:125). Rounding up is the right direction. The only thing it adds is a
   window under one second in which a database-clock write made *after* the fixture returns would become visible at
   `frozen`. No consumer writes and then expects invisibility at `frozen`, and `db_now` was already a candidate, so this
   is a theoretical residual, not a finding.

3. **`created != recorded_at` - still proves the claim.** The test's point is that history cutoffs use the
   consequence's own database clock, not the FindingRevision's application `created_at`. Two assertions follow: at
   `recorded_at` the row is CURRENT_AT_CUTOFF (:143), and at `recorded_at - 1us` it is absent (:146).
   - If the service wrongly filtered on `created_at` and `created > recorded_at`, the first assertion fails.
   - If it did so and `created < recorded_at`, the second fails.
   Only `created == recorded_at` would let a wrong-clock implementation pass both. `!=` therefore states exactly the
   precondition the test needs, in either order. The test keeps its meaning.

4. **w403 replay.**
   - (a) The implementer's claim that the not-yet-visible exit "is now tested nowhere" is **not accurate**.
     test_w403_alternative_postgres.py:395-398 drives the service with a command clock before R2's `created_at` and asserts
     `(409, DECISION_BASIS_CHANGED)` for R2 "not yet visible" (w403-clk-002/003). That branch is guarded by
     `received < r2.created_at`. Both values are on the fixture clock, so the guard is deterministic, not wall-clock
     dependent. The route's 409 envelope for this refusal is pinned at :524-532.
     What is lost is only the end-to-end served-app version: the walkthrough's 409 branch, plus "no `id` in the body"
     and "the Alternatives read is empty after the refusal". Even that branch could only run while the wall clock was
     before F02 SETUP_AT (2026-10-29), so it was already unreachable on every future run date. The loss is cosmetic.
     If the end-to-end shape is wanted, the minimal restoration is a separate test that runs `http_replay` with a
     fixture whose F02 SETUP_AT is moved past `clock_timestamp()`. It would assert `409 DECISION_BASIS_CHANGED`,
     `"id" not in body`, and an Alternatives read with no rows. See L1.
   - (b) **Verified in the product code.** alternatives.py:289-295 digests `known_at` together with tenant, site, route,
     `access_basis`, `finding_id`, the selected `finding_revision_id`, and per row `root_id`, `selected_revision_id` and
     `linked_ids` (cited evidence). Every non-time input except `access_basis` is also echoed elsewhere in the compared
     body: row `id`, `revision_id`, `finding_revision_id` and `cited_accepted_evidence_ids` (`_row`, :319-324), plus
     `total_count`, currentness and the provenance blocks. `access_basis` comes from the same principal in both reads.
     Rows past the first page are not echoed, but the replay holds exactly one Alternative row (asserted at :185-186), so
     that cannot happen here. With today's fixture, ignoring the token hides nothing the rest of the comparison does not
     catch. A stronger form is L2.

5. **`power_estate` pin `max(fixture + 1min, db_now)` - correct.** The lambda is evaluated per read, so every read is
   at or after every database-clocked row and after the fixture clock. The same idiom is already used at
   test_w301_estate_index_postgres.py:778 and test_w303_portfolio_scope_snapshot_postgres.py:554. Stale comment: see L3.

6. **Cost lens earlier cutoff - still meaningful.** `then` is now the consequence's own `recorded_at` at full
   microsecond precision (`iso` keeps microseconds; the estate parses `known_at` at full precision). At that instant the
   consequence is selectable (`<=`), so `source_revision_id` is the same revision. `then` is strictly earlier than the
   live read pin, so the read is HISTORICAL. The UNKNOWN expectation therefore still proves the W7 rule: a historical
   cutoff that sees the exact priced consequence never makes a current-money claim and leaves the Cost lens. If
   anything, this is tighter than the old `runner.now`, which only happened to fall after the consequence while the
   database clock trailed the fixture clock.

7. **Mechanism assertions match CC-R2 (0bcb7f16).** CC-R2 adds `f.mechanism` to the finding read
   (postgres_finding_store.py:540) and `_with_mechanism` (postgres_estate_read.py:216-224). These feed `_mechanism`
   (estate/index.py:139) and the Portfolio row `mechanism` (portfolio.py:176). The stored values are
   `finding_episode.MECHANISM = "GENERATOR_SUPPORT_CANDIDATE"` for the mini-grid dispatch Finding, and
   `COLD_MECHANISMS = {EXCURSION: COLD_EXCURSION, START_RESPONSE: COLD_START_FAILURE}` for cold Findings
   (postgres_finding_store.py:40, 634). Neither assertion is clock-related: these were the "2 known w303 failures"
   left by CC-R2's stale `is None` assertions. They are small and in scope as part of making the main suite green.
   - selectors:79 hard-codes `GENERATOR_SUPPORT_CANDIDATE`, which is right for the KOBO dispatch runner.
   - scope_snapshot:170 checks each row against the database.
   - scope_snapshot:156-157 additionally pins "EV Sites contribute no member row". That is stronger than the fixture
     contract, which treats EV rows as optional (`rows.get(...)` at test_w303_portfolio_fixture_postgres.py:323-324).
     It is an observed fixture fact, not a CC-R2 fact. Acceptable, but it will fail loudly if the EV fixture later
     produces member Findings (L4).

## Findings

- **L1 (Low, accuracy of record)** - test_w403_replay_postgres.py:180-183 and `.agent/clockbug-packet.md` (Round 2).
  The packet says the 409 not-yet-visible exit is "not covered elsewhere". The code comment cites only a generic
  "stale-basis 409". In fact the not-yet-visible service exit is covered at test_w403_alternative_postgres.py:395-398,
  and the dropped branch was unreachable after 2026-10-29. Fix: correct the comment and the packet to cite :395-398.
  Optionally, a future-SETUP_AT replay test can restore the end-to-end shape (see 4a). This is not a coverage gap
  that blocks the change.
- **L2 (Low, preference)** - test_w403_replay_postgres.py:228-234. The token could be compared rather than ignored:
  reload with explicit `known_at=pos["alternatives"]["body"]["window"]["known_at"]` and compare the full body, token
  included. As written the comparison is sound for the one-row fixture, but it would not notice a token-only change to
  an off-page row if the fixture ever grew past one page.
- **L3 (Low, stale comment)** - test_w303_portfolio_fixture_postgres.py:248 still says the pin is
  `runner.now + 1min` "as `power_estate` pins". `power_estate` now pins `max(..., db_now)`. Only the build-phase pin is
  affected and it is overridden by `frozen`, so this is a comment fix only.
- **L4 (Low, observation)** - test_w303_portfolio_scope_snapshot_postgres.py:155-157. The EV "no member row" pin goes
  beyond the fixture's stated contract (see 7). Keep it or relax it to `<=`. This is the author's choice.

No High or Medium findings.

## Checks run (reviewer, this revision 70b00b73)

One combined host pass over the 10 packet files plus the two other changed files (resolver, consequence history).
- Setup: interpreter `AssetOpsV1-plan2\.venv`, PYTHONPATH set to the worktree's backend, contracts, tools, simulator,
  gateway, host and field. `ASSETOPS_SETUP_CACHE=0` and no cache dir (cache off). `-p no:cacheprovider`. Private base
  database `assetops_clockrev_test` on 127.0.0.1:55432 (dropped afterwards, along with its run-owned clones), with the
  keep-awake helper running. No other pytest or browser job was running at the start. Run on 2026-10-30 from about
  19:19 local, which is after 09:00 UTC, so in the failing regime.
- Result: **80 passed, 0 failed, 0 skipped, 0 errors in 1650.5 s (27 min 30 s)**. JUnit had 80 cases.
- Cases per file: s405_resolver 9, s4_consequence_history 7, cc_placement 2, s4_power_demo_case 8, w301_estate_index 20,
  w301_provenance_dto 7, w301_w1_money_snapshot_helpers 6, w303_portfolio_comparison 4, w303_portfolio_fixture 2,
  w303_portfolio_scope_snapshot 10, w303_selectors 3, w403_replay 2.
- These match the packet's per-file counts.

Not run: `tools/check-architecture.ps1` and `check-agent-workflow.ps1` are not relevant to a test-only diff of
backend tests and were not run. There is no frontend change.

## Residual risk

- `rr-main.txt` (the main failure list the packet cites) could not be located, so I could not check one-to-one that
  all ~24 failures on main map to files in this pass. Other `runner.now + 1min`-only pins still exist, for example
  test_w301_estate_index_postgres.py:427, test_w301_estate_golden_postgres.py:229 and
  test_w302_evidence_scope_snapshot_postgres.py:197. Whether these are clock-safe depends on whether their paths write
  on the database clock. The next main safety-net full run settles it.
- The fixture clock is a fixed date, so these fixes rely on the wall clock now being after it. They are correct for
  every future run date, but they would not be correct on a machine whose clock is set before 2026-10-30.
