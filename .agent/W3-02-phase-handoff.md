# W3-02 phase handoff

## 0c (Lane A) - READY FOR REVIEW

Commit `750ce929` on `task/W3-02-estate-evidence-money-basis` (`git merge main` was already up to date at `724c0832`).
0a/0b files untouched. Branch released. Spec: closure 4, "W1 day source, cold/EV windows and pinned facades",
third and fourth paragraphs, plus the `0c` row of the per-commit index.

What landed:
- `analytics/cold_site_reads.py`: `ColdSiteReadService.capabilities_on(c,pinned_snap)` and
  `money_on(c,pinned_snap,selected_findings)`, with the helpers `_pinned` (the proof check) and `_pinned_ids`.
  `_money` gains an optional `cutoff`, and the default `None` keeps W2 unchanged.
- `ev_site_reads.py`: `EvSiteReads.capabilities_on(c,pinned_snap)` and `money_on(c,pinned_snap)`, with the helpers
  `_pinned_ctx` (built without `_ctx`/`open_on`) and `_pinned_ids`. `_select` gains an optional `cutoff`, and the
  default `None` keeps W2 unchanged.
- `financials/consequence_read.py:select_consequence_on` adds `window_start/window_end` (ISO),
  `quantity_low/quantity_high` (Decimal text), `quantity_unit` and `overlap_group` from the selected head. They are
  null without a head. The old keys and the cutoff semantics are unchanged.
- `estate/adapters/postgres_estate_read.py`: `imported_sites` items add `site_code_key`.
  `PostgresEstateRead.__init__` takes optional `cold_site`, `ev_site` and `ev_money`.
- `estate/composition.py`: wires `ColdSiteReadService(cold, cold consequence store)`, `EvSiteReads(ev, ev_money)` and
  `ev_money` onto the same owner, sharing its cold/EV read services. `financials/composition.py` has a new
  `build_ev_money_reads(link_rows)`, because the architecture guard bans adapter imports outside the financials
  composition.
- Tests: `tests/test_w302_pinned_facades.py` (16, pure) covers unprovable pins (cold 7 cases, EV 7 cases) refused
  as typed errors, a head newer than the cutoff refused, later history/work dropped, `STALE_BASIS` kept as a guard
  with `revision_id:null`, and the default paths unchanged. `tests/test_w302_pinned_facades_postgres.py` (3) shows
  that cold and EV facades equal the W2 Site `_capabilities`/money for the same exact window. `_ctx`, `open_on`,
  `_selected`, `within` and the routes are monkeypatched to fail. The EV case uses a stored, priced head from the
  W2-07 golden tariff. It also checks that the W1 head fields equal the stored immutable row for revisions 1 and 2,
  and are null when PENDING.

Checks: on the private DB `w302c_test` I ran the touched tests plus `test_s4_consequence_read`,
`test_w204_cold_consequence`, `test_w204_cold_reads`, `test_w207_ev_money`, `test_w207_ev_money_postgres`,
`test_w207_ev_site_reads_postgres`, the `test_w301_{cold,ev}_selection_on_postgres` pair,
`test_w301_w1_money_snapshot_helpers_postgres` and every `test_w301_estate_*`/`test_w302_estate_cursor` file:
191 passed, 0 skipped, 30m51s (JUnit 191/0/0/0). That run's code was revision `5c241fa5`. The amend to `750ce929`
only moved the `EvMoneyReads` construction into `build_ev_money_reads`, and I re-ran
`test_w301_estate_index_postgres` + the pure facades on it: 36 passed, 0 skipped, 7m03s. The DB was dropped afterwards.
`check-all`: 11/11 guards passed. No full suite run.

Readings (I am recording these, not making rulings):
1. A pin counts as "provable" when the snapshot carries `selection_cutoff` and `selection_seqs`, the seqs name
   exactly the selected analytics (cold) or the one session analytic (EV), it has an exact `lo/hi`, and its
   row-local `known <= selection_cutoff` and `known <= watermark`. A failure raises `ColdPinnedLineageUnavailable`/
   `EvPinnedLineageUnavailable`, which composition already maps to `EstateSelectionInconsistent` (409). I did not
   return an in-band unavailable value.
2. "Never pick a newer head": a selected cold head (`cold_heads_on` latest per Finding revision/kind) or an EV
   current head (`select_on`) recorded after `selection_cutoff` (the estate `k`) is refused (409). It is not
   replaced by an older revision. This fails closed, and a historical estate read after a later recompute
   therefore refuses. If an older-head fallback is wanted, that needs a ruling.
3. Under the pin, cold work enqueued after the cutoff does not withhold, and EV history recorded after the cutoff
   is dropped.
4. Cold `money_on` returns every selected head of both kinds (`PRODUCT_EXPOSURE` and `RECORDED_REPAIR`), each with
   `counted` (the W2 latest-per-overlap-group exposure), `finding_revision_id` and its window. `selected_findings`
   items may carry `revision_id` or `finding_revision_id`.
5. EV `money_on` returns `consequence` (the W2 `_consequence` DTO), `history` (labelled), `guard` and `state`. The
   per-row `source_provenance` is not included. Lane B calls `money_row_provenance_on` if it needs it.
6. I did not rename `cited.power_evidence_ids` to `technical_interval_ids`. That is the commit 3 wire; the docstring
   records the mapping.

Next: commit 1 (Lane B), after 0a-0c review.

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
