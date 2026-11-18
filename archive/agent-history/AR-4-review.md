# AR-4 review (task/ANY-2-AR4, head 786d2293a, diff vs merge-base f4e2ec9fa)

Reviewer: fresh Claude, read-only, no Postgres, no parity (lane rules 2026-11-12). Spec: sequence rev 4/5a/7 AR-4;
D-ANY.5, 6a, 7, 8, 9, 10, 11 (build sheet on main). Packet claims (client4 parity 61/0/0 incl. before_build /
after_build, timings) are cited, not rerun.

## Verdict

**Not mergeable as-is. ACCEPT WITH NOTES for claim rows + both dispatch.day switches once commit `e265813b0`
(money.lines MN-2/MN-3 and MN-1) moves to `task/ANY-2-AR4b` (D-ANY.8 item 5).** Claim rows and the switches meet
D-ANY.5/6a/7/8/9/10 on reading; nothing new is served with `ASSETOPS_PERIOD_READ_KINDS` unset.

## Findings

- **M1 Medium - the money.lines builder writes rows on the live tick, kill switch or not.**
  `chain/composition.py:95` registers `money.lines` whenever chain inputs exist; `config/chain/event-register-v1.yaml:45`
  declares it with `roles: [pv_available_power]`, the renewable inputs and `productive_use_price_per_kwh`, and
  `foundation.revised` / `price.revised` / renewable `assessment.revised` dirty it (pinned in `test_ch1b_register.py`).
  The tick drain (`chain/drain.py:67-73`, `scheduling/stages.py:305-307`) builds every kind in `period_builder.kinds`,
  so every Kobo reading dirties today's `money.lines` day and the drain runs `money_rows.fragments` (estate read +
  `opportunity_threads` over 5 days + an assumption series read) and appends a row. Verified no-DB:
  `period_kind_builders(<inputs>)` returns `['evidence.claim', 'money.lines']` with the env unset.
  No served read is affected (there is no read side; nothing reads `money.lines`). The risk is the write path: no
  Postgres test, no client4 build and no parity has exercised it, and an exception in it propagates out of `drain`
  and fails the Site's snapshots stage, which also carries productive_kwh, dispatch.day, mini_depth and
  evidence.claim. With MB-1/UP-1 feeding Kobo live, that is the demo tick.
  MN-1 (`chain/measure_impls.py:125,160-163`, `chain/measures.py:46`): **no served amount or wire change** - the
  amount formula is identical (`priced_line`), and the only readers of snapshot `money` (`strategies/priced_energy.py:22,49`,
  `chain/outcomes.py:272-278`) read `amount`/`currency`/`assumption_revision_id`; `SnapshotRow.to_json` is CLI-only.
  But the adapter key moves every productive_kwh `input_fp`, so each rebuilt day appends a revision (watermark moves,
  warmed pages void on rebuild), and `test_ch1a_snapshot_postgres.py` was edited for MN-1 and not run (packet Not
  built 2). D-ANY.9 Q2 accepted receipt-less rows on the premise of the 4b rebuild, which is not done.
  Fix: move `e265813b0` whole to `task/ANY-2-AR4b` (revert on AR-4: `estate/money_rows.py`, `financials/money_lines.py`,
  the `money.lines` registration and `_assumption_read` in `chain/composition.py`, the register kind line and comment,
  the MN-1 adapter/measure lines, and the pin-test edits in `test_ch1b_register.py`, `test_ch1b_drain.py`,
  `test_any1_period_read.py`, `test_ar2_mini_period_rows.py`, `test_ch1a_snapshot_postgres.py`), then rerun the no-DB
  set. Claim parity stays valid: money.lines was never served and MN-1 does not change an amount.
- **L1 Low - claim rows read outside the request snapshot** (`estate/period_rows.py` `RequestRows._load`, `known = None`
  unless `basis_historical`; it ignores `continuation`, unlike `estate/coverage.py:71`). Safe as built: a row is served
  only when it names the page day's own revision, currentness comes from the page's dispatch day, and PENDING /
  older builder / other revision read as today. So a race reads as today (or PENDING via the page), never a false
  CURRENT - the AR-3 L1 note holds for AR-4. Link rows are as of build (deviation 2).
- **L2 Low - builders bind `config.database_url()` through `lru_cache`** (`chain/composition.py:110-131`), not the
  stage's `url`; a process that builds for a different URL would read the env DB. Same shape for evidence.claim.
  Name it in the runbook; no fix for 17 Nov.
- **L3 Low (pre-existing, not AR-4)** - `backend/tests/test_ch1a_snapshot_postgres.py:78` raises NameError (`w402`) at
  collection when `ASSETOPS_TEST_DATABASE_URL` is unset; same on main.

## Checked and clean

- Claim-row pruning (`claim_inputs`, builder `estate-evidence-rows-2`): `project_claim_limit`
  (`analytics/claim_limit_read.py:429-449`) reads only `evidence_id`, `disposition`, `role`, `interval_end`,
  `source_time`, `accepted_at` of Evidence, and only ACCEPTED entries; `run.revisions`/`result` are kept whole. No
  field the projection reads is dropped. Byte-equality evidence is the Postgres test and client4 parity (packet).
- D-ANY.5 (no revision: pure projection, no row, no compose), D-ANY.6a (PENDING on any touched local day, older
  builder, other revision -> today, counted), D-ANY.7 (selected revision, no row -> today, counted): `RequestRows.claim`.
- `note_page_days` (D-ANY.9 accepted deviation): optional via `getattr`, no-op without rows; double note when
  dispatch.day is not served is harmless (same range).
- D-ANY.10 item 4: `evidence_money.py:577` reads `coverage.dispatch_days`.
- Seam: the Site lookup is in the adapter (`postgres_evidence_money_read.py` `site_ref`), none in `estate/period_rows.py`.
- Kill switch: `served_kinds()` empty by default; with it empty `coverage.dispatch_days` falls to `snap.dispatch_days`,
  `_rows_of` is None, and `claim_limit_on` / `cited_provenance` take today's path.
- Register/pins: `evidence.claim` (s3_day) pinned; `period_kind_builders(None)` early `{}` equals the old result.
- Migrations: none in the diff, so no clash with PR-3's 0060. No `.pyc` committed.

## Checks run (this review, worktree head 786d2293a)

- No-DB pytest (plan2 venv, PYTHONPATH = worktree backend;backend\tests;contracts;simulator;gateway;field;host;tools):
  ar4_evidence_period_rows, ar4_money_lines, ch1b_register, ch1b_drain, any1_period_read, ar2_mini_period_rows,
  ar3_dispatch_day_rows, ar4_evidence_period_rows_postgres (skipped), tools/checks test_period_read_parity +
  test_perf_budget: **182 passed, 1 skipped**, 14.9 s.
- `tools/check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` = plan2 venv): "Architecture check passed.", exit 0.
- Not run (lane rules): Postgres files, client4 parity, timings, frontend (diff is backend-only).
