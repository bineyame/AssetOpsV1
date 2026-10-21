# W3-02 phase handoff

## Commit 2 (Lane B) - Evidence page landed; READY FOR LANE A SHELL

Commit `d9f898e7` (after merging main into `33b9711e`). Branch released to Lane A.

What landed (build spec: mock ledger 72-104, states 105-119, closure 1 "Mock copy..." 183-194, closure 2 Q27, closure 4 wire/links 398-407, closure 5 S13):
- `frontend/src/estate/estateEvidenceMoneyClient.ts`: typed `estate-evidence-1` envelope/rows/gaps, `EMPTY_SCOPE`/`EMPTY` unions, `EVIDENCE_REFUSAL_COPY` (W3-02 state-table copy), `createEstateEvidenceMoneyClient` (`GET /api/estate/evidence`); the W3-01 `EstateClient` is unchanged. Commit 4 adds Financials here.
- `frontend/src/estate/EstateEvidence.tsx`: `EstateEvidencePage`, `ESTATE_EVIDENCE_PATH="/evidence"`. Header `Portfolio evidence` + subtitle; shared `EstateDateBar`; three neutral (`muted`) cards with the ruled values/notes; panel `Capability coverage across sites` (mock subtitle, 5 columns, server `links.site_readiness` + `Opens current Site view`, readiness chips with page-local `estate-tone--*`, context chip, `No current ceiling`/`Not recorded`, closed `Record details` disclosure); panel `Recurring evidence gaps` (4 columns, Unlocks dictionary, `{next_step} · Not available yet` via `UnavailableInline`, `Next step not recorded`, inert `Example destinations` via `UnavailableLinkEntry`); blue mock notice. Empty-scope, no-selection, partial and historical notes sit outside the tables with headers kept. Refusals clear rows.
- `frontend/src/estate/estateEvidence.css`: tones, bounded internal table scroll (coverage 200/300 px, gaps 180/420 px at 1440/<=640), table min-widths 520/330 px.
- `frontend/src/estate/__tests__/estateEvidence.test.tsx`: `rendersMockEvidencePanelsAndHonestCards` (with `expectV69Panels` + planted-panel rejection), `rendersGroupedCapabilitiesAndTypedGaps`, `keepsInertMockActions`, `rendersEvidenceEmptyPendingAndRefusals`, `preservesSupportedSiteLinksAndCurrentViewLabel`, `readsTheEvidenceWireAndMapsRefusals`.

Checks at `d9f898e7`: focused 6/6; `tsc --noEmit` clean; full frontend 95 files / 2379 tests passed; `tools/check-all.ps1` 11/11.
Not run: 1440/390 captures (blocked: no shell route until Lane A mounts `/evidence`); layout claims unverified.

Next (Lane A, `.agent/W3-02-lane-a-requests.md` "Commit 2"): frame, App prop/route, live rail entry, registry `I-estate-evidence-root` paths, worksheet correction, captures; then independent commit-2 review. Open: `.agent/W3-02-pending-rulings.md` c2-q1..q4 (gap Site names, refusal copy for unnamed codes, B5 route-read follow tests, row context words).

## Commit 1 - READY FOR COMBINED REVIEW (Lane B c1 follow-ups landed)

`9efa3914` applies the c1 rulings (build spec "Commit-1 rulings (c1)") on top of Lane A's `cb39fdc9`. Lane B files only.
- c1-q2: `EvidenceMoneySnapshot.ev_capabilities` uses the public `capabilities_on` `unknown_meter`; the private `_sessions(_pinned_ctx(...))` call is gone.
- c1-q7: the adapter's `claim_limit_on` passes the estate `page_one_mode` (`snap.basis_historical`) as `basis_mode`.
- c1-q1: the W1 day is labelled `Historical as of {estate known_at}` from the estate basis (cold/EV already were).
- c1-q3(5): EV token `selected_assessment_revision_ids` adds the pinned selected session revision IDs.
- Tests: pure `test_w302_evidence_meter_gap_and_frozen_basis_mode`, W1 historical-label and session-only 409 asserts; Postgres `test_w302_evidence_ev_meter_gap_from_unknown_meter_seconds` (`missing-meter` replay).
- Checks: `test_w301_estate_*` + `test_w302_*` on private `w302h_test` (dropped): 119 passed, 0 skipped, 16m38s. `check-all` 11/11. No full suite.
- No new pending rulings. Branch released.

### Earlier: commit 1 (Lane B) - Evidence read/API, before the c1 rulings

Commits `8d1e6325` (code + pure tests) and `c9e19695` (Postgres proofs) on `task/W3-02-estate-evidence-money-basis`, after `git merge main`. Lane A files were not touched. The branch is released to Lane A for the mount (exact diff in `.agent/W3-02-lane-a-requests.md`).

What landed:
- `estate/evidence_money.py`: `EstateEvidenceService(EstateIndexService)` reuses the shared `_scope/_fence/_cursor/_envelope/_read`, `site_coverage`, `selection_token` and `resume_after`.
  - W1: one `GENERATOR_SUPPORT@day` row per intersecting day from `claim_limit_on` + `reduce_day`.
  - Cold/EV: four grouped rows per pinned window from `capabilities_on`. A Site with no selected window gets four unsuffixed placeholders.
  - Also: typed gap groups, B5 row-local links, `EMPTY_SCOPE`/`EMPTY`, and the 3-part cursor.
- `estate/adapters/postgres_evidence_money_read.py`: `PostgresEvidenceMoneyRead` and `EvidenceMoneySnapshot`, subclasses that keep the one REPEATABLE READ transaction and add `claim_limit_on`, `pinned_windows`, `cold_capabilities` and `ev_capabilities`.
- `estate_evidence_money_api.py`: `build_estate_evidence_money_router`. Every refusal includes `gaps:null` inside `detail` (401 and 503 too).
- Tests:
  - `test_w302_evidence_api.py` (5, pure), including the literal empty-scope vector and `/2` token `5944cb...`.
  - `test_w302_evidence_scope_snapshot_postgres.py` (2: cold scope/windows/citations/cursor/409/foreign, and W1 two days plus historical, with the store's own transaction trapped).
  - `test_w302_evidence_ev_postgres.py` (1: EV rows, links, gaps).

Checks, on the private DB `w302f_test` (dropped afterwards):
- The 3 new files plus `test_w301_estate_api`, `test_w302_estate_cursor`, `test_w302_w1_day_reduction`, `test_w302_pinned_facades` and `test_w301_estate_coverage`: 73 passed, 0 skipped, 54s.
- Mutations, both reverted:
  - Rows cite all window evidence: the pure test failed.
  - The link `from` is shifted off the row window: the cold and EV Postgres tests failed (2 failed).
- `check-all`: 11/11. No full suite.

Pending rulings: `.agent/W3-02-pending-rulings.md`.
- c1-q1: the EV `historical_label` is set only when the snapshot state is HISTORICAL, which differs from "explicit earlier cutoff". This matters for commit 3.
- c1-q2: `unknown_meter` is not exposed by the EV facade; there is an interim private `_sessions` call.
- c1-q3: readings applied where the spec is silent.

Next: Lane A mounts the router in `main.py` (with the composition builder), then the combined phase-1 review. Then commit 2 (Lane B).

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
- 0b fix r1: W3-02 0b fix r1 — trap now patches _snapshot/_run/_connect_engine (mutation via _run: 4 failed, reverted); window-only revision mode (non-window 422 REVISION_NOT_WINDOW); HISTORICAL day shape/copy, conflict precedence, gap key (mini_grid, code, role) per rulings; 63 passed on w302d_test.
- 0c fix r1 (`2c46c9fd`): H1 cold heads `created_at <= K` before DISTINCT ON (`cold_heads_on(known_at=)`), EV basis from tariff assignments recorded at K + head `recorded_at <= K` (also under HISTORICAL; as-of head labelled history, `historical_label`), pinned STALE_BASIS copy `STALE_AS_OF_COPY`; M1 W2-04 drain before the comparison, ≥1 PRODUCT_EXPOSURE, ids/kind/basis/counted/withheld/hold vs W2; L1 `cold_pending_as_of_on`; L2 K+ε absent at K in pure + Postgres; L3 `ev-session/1` key + positive seq. Mutation (drop as-of bounds): both historical Postgres tests failed, reverted. 0c + w204 cold reads/consequence/worker + w207 EV money/Site reads: 118 passed, 0 skipped, 20m26s on w302e_test (dropped). check-all 11/11.
- commit-1 Lane A integration (`71c00d59`, after merging main): c1-q2 `EvSiteReads.capabilities_on` now returns
  `unknown_meter: bool` (one `_pinned_ctx`, `any(unknown_meter_seconds > 0)` over `_sessions(ctx)`;
  `ev_site_reads.py:334`). c1-q7 `ClaimLimitReadService.claim_limit_on(..., *, basis_mode=None|"live"|"historical")`
  (`analytics/claim_limit_read.py:357`, applied at `historical_day`; other values raise `ValueError`; `None` keeps
  `known_at < transaction_time`). Evidence router mounted: `build_estate_evidence_service` in
  `estate/composition.py` (exactly the requested builder) and `main.py` mount after the W3-01 estate router. No guard
  change. c1-q1 assigns no Lane A file. Tests: `test_w302_pinned_facades_postgres.py::test_ev_capabilities_on_exposes_unknown_meter_of_the_selected_sessions`
  (complete / missing-meter) and `test_w302_w1_claim_limit_on_postgres.py::test_w1_frozen_basis_mode_overrides_the_transaction_time_comparison`.
  W3-01 estate (5 files) + all `test_w302_*` + `test_w207_ev_site_reads_postgres.py`: 136 passed, 0 skipped, 19m49s on
  `w302g_test` (dropped). check-all 11/11.
  Next for Lane B: in `PostgresEvidenceMoneyRead.ev_capabilities` consume `read["unknown_meter"]` and drop the private
  `_sessions(_pinned_ctx(...))` call; pass the cursor's `page_one_mode` as `basis_mode=` to `claim_limit_on`
  (c1-q7); add the estate METER_GAP test for a selected session with positive unknown meter seconds (c1-q2), the
  c1-q1 label change in `evidence_money.py`, and the c1-q3 token replacement (5). `evidence_read` in
  `test_w302_evidence_scope_snapshot_postgres.py` may now call `build_estate_evidence_service`.

## Commit-1 fix r1

Implements "Commit-1 review r1 rulings" (build spec) against `.agent/W3-02-commit1-review.md`; no new pending rulings.
- M1: `_window_state` (`estate/evidence_money.py`): a live basis maps pin `HISTORICAL` to CURRENT; PENDING/STALE precedence kept; a missing pin stays UNKNOWN. Pure test in `test_w302_evidence_meter_gap_and_frozen_basis_mode`; Postgres `test_w302_evidence_live_cursor_later_disposition_preserves_rows_and_token` (ordinary late disposition after the cursor cutoff) plus control `..._changed_selected_id_is_409`.
- M2: `adapters/postgres_evidence_money_read.py` maps the five finite `ClaimLimitRefusal` codes to an unavailable day projection (HISTORICAL_SELECTION_UNAVAILABLE + original code); the row is UNKNOWN with no IDs. Other refusals still 409. Tests `..._w1_refusals_are_unknown_days` (5 codes), `..._w1_refusal_preserves_other_sites`.
- R1 role-specific `GENERATOR_UNOBSERVED` copy (generator_state unchanged); R2 confirmed (energy row only); L1 token cites full `read["evidence_ids"]`, claimless row cites nothing (`_token_cited`); L2 interval reasons in constituents and labelled `prior_selection` for non-current days; L3 canonical six-digit `Z` historical statements; L4 `complete` keyed on `snap.basis_historical`; L5 token session IDs asserted in the EV Postgres test, plus `test_w302_evidence_composition_mount_no_db_503`.
- Note: two live reads at different cutoffs have different tokens (k is in the token); the M1 test compares page two to page one only.
