# SR-12a packet (lane I) — Evidence rejections over the date range

Branch `task/SR-6-12a-pages` (from main e8f2bdea5). Spec: sequence doc rev 10b.4 "SR-12a", rev 10c (D-SR.39: IN),
D-SR.34. Commits 2e5119535 (server + pages), a1ec625d9 (guard order).

## Pre-flight: lists in the rejections body and their time column
| Path | List | Time column used |
|---|---|---|
| Postgres (`PostgresEvidenceLedger.rejections` → `ImportedEvidenceReads.rejections`) | `rejections` (and `total`, `rejected_without_source_time`) | batch `ingestion_batch.received_at` |
| same | `conflicts` (a subset of `rejections`) | batch `received_at` (same rows) |
| same | `duplicates` | batch `received_at` |
| File-backed (`EvidenceReadModel.rejections`) | `rejections`, `conflicts` | their own `received_at` (no batch table) |

**No recompute-job list exists in this body** (spec names one on `created_at`). Nothing to filter; question Q1.

## Done
- `evidence_api.py` `get_rejections`: cutover gate first (`imported_scope`), then optional `from`/`to` via the existing
  `_window_params` (UTC instants, `from < to`); exactly one bound → 422 `INVALID_WINDOW`. No range → unchanged.
- `postgres_evidence_ledger.py`: `rejections(..., window=None)` and `_rejection_rows(..., window=None)` add
  `b.received_at >= :w_from AND b.received_at < :w_to` (`_RECEIVED_IN_WINDOW`); `site_window`'s call is unchanged.
- `ledger_reads.py`: `ImportedEvidenceReads.rejections(scope, batch, window=None)`; the ledger is called with the window
  only when given (protocol updated).
- `read_model.py` (file-backed): filters rejections and conflicts on `received_at` in `[from, to)` (builder call: not
  named in the spec, but the generic page would otherwise list all dates without its line).
- Frontend: `siteEvidenceClient` / `ledgerEvidenceClient` `listRejections(site, batch, window)`.
  `SiteEvidence.tsx`: passes the address `from`/`to`; the rejections panel loses SR-4c's "All dates" line
  (`data-panel-range="range"`); over a range both count lines use the ranged read's `total` ("N records received in this
  date range were rejected…"). The analytics panel keeps its "All dates" line (SR-12b).
  `LedgerSiteEvidence.tsx` `Rejected`: passes the range; heading "Readings not accepted (received in this date range)"
  (was "(all periods)"), empty line "No reading received in this date range was refused or repeated." (builder wording).

## Tests
- No DB: `test_sr12a_rejections_range.py` 9 passed (window reaches the ledger as instants; no range unchanged; 422 ×5;
  imported reads pass window only when given; file-backed filter incl. `to` excluded); with `test_s2_rejection_placement`,
  `test_sites_api`, `test_health`: 77 passed.
- Postgres `assetops_sr12a_test` (created): `test_sr12a_rejections_postgres.py` + `test_s2_site_evidence_postgres.py`
  16 passed, 0 skipped, 20 s. Non-vacuous: `to` made inclusive (`<=`) → the edge assertion failed (`assert 1 == 0`);
  reverted with `git checkout`.
- Vitest: `siteEvidenceScreen` 16, `s2LedgerEvidence` (new SR-12a case) with `v01bEvidenceVisual`, `evidenceClaimLimit`
  115 passed; every evidence-related test file (65 files) 1955 passed. tsc clean.
- Guards run singly: configuration-persistence 0 (after a1ec625d9; first run caught the gate order),
  site-links-carry-range, ui-primitives, page-range-forms, dependency-direction 0. check-all: for coordinator.

## Questions for the Architect
1. The spec's "recompute-job list on `created_at`" has no list in `/evidence/rejections` (lists: rejections, conflicts,
   duplicates). Nothing was filtered for it. Confirm, or name the list meant.
2. Two time bases on one Evidence page: the ledger overview counts ("N readings in this period were not accepted",
   `counts.rejected/conflicts`) place rejections by their own **source time** (S2 Q19), while the ranged list uses the
   **batch receipt** (this ruling). On the ledger page the line and the list can differ near range edges, and an untimed
   rejection is counted in the line's untimed note but listed only if received in the range. Accept, or align one side?
3. File-backed path filtered too (builder call above). Confirm.
