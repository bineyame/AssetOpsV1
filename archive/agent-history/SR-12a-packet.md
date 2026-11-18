# SR-12a packet (lane I) — Evidence rejections over the date range

Branch `task/SR-6-12a-pages` (from main e8f2bdea5). Spec: sequence doc rev 10b.4 "SR-12a", rev 10c (D-SR.39: IN),
D-SR.34. Commits 2e5119535 (server + pages), a1ec625d9 (guard order).

## Pre-flight: lists in the rejections body and their time column
| Path | List | Time column used |
|---|---|---|


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

## Fix round (D-SR.76 Q7-Q9, ruled)
- Q7: the recompute-list spec line is withdrawn; nothing to filter (note removed from this packet).
- Q8: every ranged list, `conflicts`, `duplicates` and `total` are placed by the reading's SOURCE time in `[from, to)`; a rejection with
  no source time is placed by batch receipt, on the list and the count line's untimed note (`ledger_reads.py`). The ledger read is
  unwindowed; duplicates carry the first accepted reading's source time (`LEFT JOIN accepted_evidence`). Heading "Readings not accepted
  (from this date range)"; empty line "No reading from this date range was refused or repeated."; untimed row "No reading time; received in this date range".
- Q9: file-backed rows carry no source time, so they are placed by receipt (the Q8 fallback) in `EvidenceReadModel.rejections`.
- L1: a failed ranged rejections read shows no count (`SiteEvidence.tsx`). L2: stale comment at `PANEL_ALL_DATES` fixed.
- Tests: no-DB `test_sr12a_rejections_range.py` (9 pass; source edges from=in / to=out, untimed by receipt, duplicates);
  Postgres on `assetops_sr12a_test`: `test_sr12a_rejections_postgres.py` + `test_s2_site_evidence_postgres.py` 16 pass (edges per row, line = list,
  receipt does not place a timed reading); vitest siteEvidenceScreen, s2LedgerEvidence, siteHealthRange pass; tsc clean.
