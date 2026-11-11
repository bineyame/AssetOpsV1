# AR-4 packet: Portfolio evidence and money on stored rows - PHASE 1 (code + no-DB tests) - PARTIAL

Branch `task/ANY-2-AR4` (worktree `AssetOpsV1-ar4`) from `task/ANY-1-rows` `b1ca93b83`, with main `9fc353736` merged
(`aefb65d1e`: PF-C coverage_line, PARTIAL-MONEY, GAP-REASONS, INFRA-1 are needed for parity). Spec: architect answer
2026-11-10 §4 AR-4; sequence rev 4 (no PF-O2); D-ANY.1-6, D-MONEY.1-5. USER_REVIEW_REQUIRED: no (review ACCEPT
gates the merge). Rebase onto main after ANY-1 merges: AR-4's own commits are `d5382056c` and `d530aa5a0`.
Expected conflicts with AR-2 are in `chain/composition.py` `period_kind_builders`/`period_kind_versions`, the
register `kinds:`, and the two register-pin tests. Resolve them by merging both kind sets.

## Landed (phase 1)

| Item | Where |
|---|---|
| `claim_limit_on` = store read + new pure `project_claim_limit(selected, revision, ...)` (no behaviour change) | `analytics/claim_limit_read.py` |
| `PeriodFragment.local_day`: a row may carry its own register day (a UTC claim day keeps its date whichever local day dirtied it) | `chain/period_read.py` |
| Kind `evidence.claim`: one row per (mini-grid Site, UTC claim day). Body = the day's selected window revision ID plus that revision's exact `_revision_detail` (tagged JSON: datetime/date/UUID/Decimal/tuple round-trip). The interval Evidence link rows are stored once per revision in `revision_provenance` | `estate/period_rows.py` `EvidenceClaimKindBuilder` |
| Serve path: `EvidenceMoneySnapshot` records the page's own dispatch days. For each claim day it projects stored detail + page selection through `project_claim_limit` at the request's k and mode. `cited_provenance` runs today's `PublicProvenance.cited_set` over the stored link rows (the `_Prefetched` shape) | `estate/adapters/postgres_evidence_money_read.py`, `period_rows.RequestRows` |
| A day is served only if its row exists at k, is not PENDING on any local day it touches, has the current builder version, and names the page's revision. Otherwise the day is read as today, logged `period_row_absent` and counted (`row_misses()`) | `period_rows.RequestRows.claim` |
| Kill switch `ASSETOPS_PERIOD_READ_KINDS` (no `evidence.claim` = today's compose) | `EvidenceRows.request` |
| Register: `evidence.claim {grain: s3_day, MINIGRID, analytics [dispatch], job_domains [dispatch]}`; wiring `period_kind_builders(inputs)`, `period_kind_versions()`, `build_estate_evidence_rows()`; `day_revision` is now one shared rule in `mini_grid_rows` | `config/chain/event-register-v1.yaml`, `chain/composition.py`, `estate/composition.py`, `estate/evidence_money.py` |

## Not built yet (resume here)

1. `evidence.provenance` for cold/EV pinned windows (`windowed_rows`: `pinned_windows`, `cold_/ev_capabilities`, and their `cited_provenance`).
2. `money.lines` per D-MONEY.1-4: `mini_grid_lines` (consequence, `consequence_provenance`, eligibility) and `windowed_lines` (cold/EV money), with receipts. MN-1 (receipt on `productive_kwh.money`, builder bump), MN-2 (`money.potential`), MN-3 (an AST guard against no-total writes; `validate_body` already refuses `TOTAL_FIELDS`). The PARTIAL-MONEY `partial_money` and PF-C coverage_line labels must stay byte-equal.
3. `backend/tests/test_ar4_evidence_period_rows_postgres.py` (not written). It must cover:
   - rows vs compose, byte-equal, for live and historical k;
   - k before revision 1, which is read as today;
   - a late revision: PENDING is read as today until the rebuild.

## Checks run (phase 1, no DB)

- `test_ar4_evidence_period_rows.py`: 13 passed.
- Adjacent tests: 24 files matching `test_(w302|w303|partial_money|pfc|cov_partial|qw2|ch1b|any1|ar4|dd1b2b_drain|fix_cold_drain)`, excluding the Postgres ones, plus `tools/checks/test_event_register.py`, `tools/checks/test_period_read_parity.py` and `tools/checks/test_perf_budget.py`. Result: 513 passed, 5 skipped. The one failure was the register pin, which is now fixed: 58/58 pass.
- Non-vacuity: two mutations were made on `d530aa5a0` and then reverted with `git checkout`.
  - Pending checked on its own date only: fails `test_pending_local_day...`.
  - The revision-equality check dropped: fails `test_request_misses...`.
- Not run: Postgres, parity, perf, check-architecture, full suites (phase rule).

## Postgres and parity steps still to run (Thu from 12:30, after AR-3's slot; never client6 / demo3_full)

1. Write and run step 3 above on the own `assetops_ar4_test` DB (backend/TESTING.md focused run; keep-awake on; cap 2x).
2. Run `test_w302_*_postgres.py` and `test_w302_w1_claim_limit_on_postgres.py` focused: the `project_claim_limit` split must leave them green.
3. client4 (`assetops_polish_client4_test`, migration 0059 already applied): `python -m assetops_backend.chain.period_backfill build --site <S> --kind evidence.claim` for every MINIGRID Site. Record rows written and time per Site.
4. Parity:
   - Command: `tools/checks/period_read_parity.py --kinds evidence.claim --seed 20261111 --random 16 --work AssetOpsV1-e3c\var\polish_client4 --story <its story.json>`, with `ASSETOPS_PREBUILT_ROUTES` = its `prebuilt-routes.json`.
   - It must show 0 MISMATCH and 0 MISSING, byte-for-byte, on `/api/estate/portfolio`, `/evidence`, `/financials` and `/scope-ids`.
   - Coverage must include: unaligned UTC windows, 31-day ranges, historical `known_at`, `any.between_revisions.site_period_read`, and every PARTIAL-MONEY Site's "for n of m days analysed" money label and PF-C coverage_line.
   - A mismatch keeps `evidence.claim` off: it stays out of the kinds list and is reported, never approximated.
5. Run `perf_budget.py --any-range --kinds evidence.claim --report` and record the Portfolio before/after and the `period_row_absent` / `row_misses` counts.
6. After items 1-2 of "Not built yet": repeat steps 3-5 with `evidence.provenance,money.lines`.

## Known deviations (phase 1)

1. **Question for the Architect.** A claim day that has no current row is read as today, for that day only. This covers: absent at k, PENDING, an older builder, or a different revision than the page's. D-ANY.5 says "no fallback compose", but today's "nothing known at k" result for a claim day contains reason text that comes from the store, so only this per-day read can reproduce it byte-equal. Every miss is logged and counted.
2. The dispatch-day selection is not stored. It is the page's own `select_dispatch_days_on` row, which AR-3 owns. Only the immutable revision detail and the link rows are stored.
3. Link rows are stored as of build time (as AR-2 deviation 4). A link added later for an old ID is not seen until the day is rebuilt.
4. The rows are read once per Site (one reader read plus one provenance statement), not once for every Site together.
5. The stored detail is DB facts under its own keys. If a real detail holds a `WORD_FIELDS` key with plain text, `validate_body` refuses the build loudly. This shows in step 3.
