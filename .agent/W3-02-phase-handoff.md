# W3-02 phase handoff

## 0b (Lane A) - READY FOR REVIEW

Commit `d208faef` on `task/W3-02-estate-evidence-money-basis` (after merging main into `2d36689a`). 0a files
untouched. Branch released. Spec: Review closure 4, "W1 day source, cold/EV windows and pinned facades", first
paragraph only.

What landed:
- `analytics/claim_limit_read.py`: `ClaimLimitReadService.claim_limit_on(c,tenant_id,site_id,day,revision_id,
  known_at)` (never `read()`/`claim_limit_snapshot()`); module `interval_state`, `reduce_day`, `GAP_CODES`,
  `HISTORICAL_SELECTION_UNAVAILABLE`, state constants. Protocol `ClaimLimitStore` gains `claim_limit_snapshot_on`.
- `analytics/adapters/postgres_assessment_store.py`: one new method `claim_limit_snapshot_on`, placed directly after
  `_revision_detail`; it composes `select_dispatch_days_on` (one day) and `_revision_detail`. No existing function
  changed (W4-02 merge surface untouched).
- Tests: `tests/test_w302_w1_day_reduction.py` (5, pure: precedence, zero intervals, single-ceiling agreement,
  role-tagged gaps vs role-less window reasons, unavailable). `tests/test_w302_w1_claim_limit_on_postgres.py` (3:
  F02 two days; F06 cutoff with disagreeing FULL/LIMITED intervals, gaps, later CONTRADICTORY selection, later
  revision/acceptance excluded, earlier selection as HISTORICAL; DONE-without-selection unavailable history). The
  store `_snapshot` is monkeypatched to raise, so any second transaction fails the test.

Checks: those 2 files + `test_w301_w1_snapshot_helpers_postgres`, `test_s3_claim_limit_postgres`,
`test_s3_claim_limit_vocabulary`, `test_s3_dispatch_read_postgres`, `test_s3_dispatch_assessment_postgres`,
`test_s3_dispatch_v3_analytic` on private DB `w302b_test`: 77 passed, 0 skipped, 1m43s; DB dropped. `check-all`:
11/11 guards passed. No full suite run. The `_snapshot` trap was not separately mutation-proven.

Readings (recorded, not rulings):
1. `revision_id` is the day's window revision (all INTERVAL revisions of its run are projected) or one INTERVAL
   revision (that one only). Lane B calls it with `window_assessment_revision_id`.
2. Interval state: a role-tagged `CONFLICTING` reason gives CONTRADICTORY (even when not CURRENT); otherwise any
   non-CURRENT currentness (PENDING/FAILED/STALE_PROJECTION/UNASSESSED/HISTORICAL) gives UNKNOWN; else support
   COMPLETE/NONE/LIMITED -> FULL/NONE/LIMITED.
3. A revision not in the day's selection at `known_at` is HISTORICAL (IDs, `historical_ceiling` kept, no current
   claim), not refused. Day unavailable, revision/interval/run recorded after the cutoff, or cited Evidence accepted
   after it -> `available=False` + `HISTORICAL_SELECTION_UNAVAILABLE`. Unknown revision 404, other window 422,
   unsupported model 422 and absent lineage 409 are raised as `read()` does; the estate caller maps them to UNKNOWN.
4. Interval reasons exclude window limitations; role-less window reasons are returned separately as
   `window_reasons` and never become gaps. Gaps carry `domain="dispatch"` (the W1 DOMAIN constant).
5. The W1 `_reasons` maps NOT_EVALUATED spans to `GENERATOR_UNOBSERVED` with the span's role, so F06 yields
   `GENERATOR_UNOBSERVED` gaps for non-generator roles; kept as the reused W1 vocabulary.
6. The row key `GENERATOR_SUPPORT@YYYY-MM-DD` and placeholders are left to commit 1.

Next: `0c` (Lane A, pinned facades), after 0b review.

## 0a (Lane A) - READY FOR REVIEW

Commit `7a4d06ef` on `task/W3-02-estate-evidence-money-basis` (base main `c50ea24b`). Branch released.

What landed (the spec is Review closure 4, "Shared parser, 3- and 5-part cursor, refusals (B1, S7-S8)"):
- `backend/assetops_backend/estate/scope.py`: `KEYS` gains `evidence` and `financials`, both
  `from,to,known_at,limit,cursor`. `parse_request` and `decode_cursor` refuse an unsupported kind with
  `EstateRefusal("INVALID_CURSOR")` (422). New cursors use the Action key set, with `kind` equal to the root.
  `_marker_ok` validates the 3-part Evidence marker and the 5-part Financials marker (null-first). `cursor_after` is
  kind-aware. New helpers: `cursor_marker(kind, after)`, the wire inverse, and `resume_after(markers, after)`, which
  raises 422 for an absent marker and is called only after the fence.
- `backend/assetops_backend/estate/index.py`: `_fence` returns `cursor_after(cursor)`, so it handles any kind.
  `_cursor(tenant_id, req, scope, token, *after)` keeps the old `(at, row_id)` call sites. `kind` comes from
  `req.kind`. The Finding/Action bytes are unchanged, and a test pins them.
- `backend/tests/test_w302_estate_cursor.py`: 31 tests. They cover parser kinds and the typed unknown-kind refusal,
  both marker arities, null-first money, 20 malformed cases (missing `page_one_mode`, wrong kind, unknown or extra
  keys, arity, non-UUID, empty string, non-canonical instant), kinds not crossing, old bytes unchanged, changed
  grant/selection/window/cutoff and the old `/1` digest giving 409, and historical page two.

Checks: the 6 estate test files on the private DB `w302a_test` gave 66 passed, 0 skipped, in 9m31s. The DB was
dropped afterwards. `tools/check-all.ps1` passed all 11 guards. I ran no full suite, as instructed.

Readings (I am recording these, not making rulings):
1. Evidence/Financials cursors also need the canonical six-digit `from/to/known_at`, matching the "canonical time"
   wording. Finding/Action cursors keep the looser W3-01 check.
2. `site_id` is the marker element at index 1 (Evidence) and index 2 (Financials). It is validated as a UUID string,
   and its case is not normalized.
3. I added `resume_after` to `scope.py` as the shared absent-marker check. Phases 1 and 3 should call it on the full
   ordered marker list, after `_fence`.
4. A changed cutoff is refused 409 inside `_scope` (W3-01 behaviour), before `_fence`.

Next: `0b` (Lane A, W1 day projection), after 0a has its independent review.
