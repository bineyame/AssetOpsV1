# S2-02 phase 3a2 handoff — items 3 (backend) and 5 landed; phase 3b (frontend) next

Branch `task/S2-02-ingestion-site-evidence`. Builds on `.agent/S2-02-phase-3a-handoff.md` (items 1, 2, 4-backend). Commits: `23da99d` (Evidence reads + comparison gate + CLI + guard), `59d76fe` (comparison tests, recorded KOBO-001 record, Q18–Q20). New questions Q18–Q20 in `.agent/S2-02-questions-3.md`.

## Landed

**Item 3 backend — Postgres Site Evidence reads.**
- SQL (read-only) in `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py` section "Site Evidence reads": `site_scope`, `site_window` (per-source counts, coverage, batches + `accepted_in_window`, overlapping PENDING/LEASED/FAILED recompute jobs, extent, rejections), `records_page` (half-open window, filters, `(source_time, id)` cursor), `record_detail` (by evidence UUID or message ID; duplicates and conflicts with the conflicting envelope text from `batch_text`), `rejections`, `dispatch_jobs`, `message_digests`, `bound_channels`; helper `_envelope_at`.
- Pure builder `backend/assetops_backend/evidence/ledger_reads.py` (payload shapes in its docstring): `ImportedEvidenceReads.scope` → `permits_cutover` (raises `AwaitingComparison`); `site_evidence` (state `NO_DATA|REJECTED_ONLY|ACCEPTED` + `PARTIAL_BATCH|CONFLICTING|STALE_PROJECTION|OUTDATED_CONFIGURATION`), `records`, `record` (`accepted_as` UUIDs, `receipt{batch_id, batch_uuid, ordinal, decision, received_at, decided_at, payload_sha256,...}`, `envelope{sha256,text}`, `duplicates[]`, `conflicts[]`), `rejections` (`duplicates[].first_accepted_evidence_id`). Clock labels via `clocks(source_mode)`: `RUN_VIRTUAL`/`SOURCE_REPORTED` + `SERVER_RECEIVED_AT`; `received_at` = `ingestion_batch.received_at` (6-digit), `decided_at` separate.
- Routes `backend/assetops_backend/evidence_api.py`: new `imported_reads` param; helpers `imported_scope`, `from_ledger`, `_window_params` (422 `INVALID_WINDOW` when from ≥ to); each of the four Site Evidence routes calls `imported_scope(site_id)` first; new codes `INVALID_CURSOR` 422, `RECORD_AMBIGUOUS` 409, `EVIDENCE_LEDGER_UNAVAILABLE` 503. Imported without a passing record keeps 409 `AWAITING_EVIDENCE_MIGRATION`. Overview/analytics unchanged (legacy gate).
- Wiring `main.py` (`comparison_reports` param; a composition injecting its own evidence store reads no workspace report unless it injects reports) and `sites/cutover.py` `ImportedSiteRegistry.ledger_scope`.
- Tests `backend/tests/test_s2_site_evidence_postgres.py` (12): gate closed for missing/FAILED/EXCEPTIONS/other-Site/unstated-empty-set on all four routes; window states; cursor paging + half-open end; record lineage, duplicate, conflict; `received_at` stays first receipt after a resumed partial batch decided 7 minutes later.

**Item 5 — legacy comparison.** `evidence/legacy_comparison.py` (`compare`, `permits_cutover`), immutable writer `evidence/adapters/legacy_comparison_file.py` (`var/evidence/migration/<site_key>/<stamp>-<id>.json`, O_EXCL, newest decides), CLI `backend/assetops_backend/evidence_migration.py` (`run --tenant demo --site KOBO-001`, `show --site`; top-level because evidence may not import analytics). Ran on the dev DB (upgraded 0004 → head to do so): `PASSED`, `empty_set: true`, zero counts, cutover permitted (Q18 asks whether that suffices). Copy at `.agent/S2-02-legacy-comparison-KOBO-001.json`. S3 fixtures ride in the report (`s3_fixtures.legacy_dispatch_claims`, `.recompute_jobs`; both empty on the dev DB today — re-run after the demo ingests to hand S3 real jobs). Tests `backend/tests/test_s2_legacy_comparison.py` (4, real V1 envelopes: matched non-empty PASSED, digest/ledger/parse FAILED, unmapped channel EXCEPTIONS, never-overwritten newest-decides).

**Guard** `tools/checks/configuration-persistence.ps1`: writer list adds the report adapter; new block "S2-02 phase 3a: the Evidence cutover gate" (four routes ask `imported_scope` first; `scope` asks `permits_cutover`; CLI calls no store write). Non-vacuity shown: each of the three violations failed the check; `permits_cutover` bypass failed 5 gate tests; `received_at` from `decided_at` failed the receipt-time test; skipping the digest check failed the comparison test. All reverted with `git checkout`.

## Phase 3b anchors (frontend)

- Client `frontend/src/sites/siteEvidenceClient.ts` :340-378 (getEvidence/listRecords/getRecord/listRejections); 409 handling :313 and `AwaitingEvidenceMigration.tsx`. Branch on `store === "POSTGRES"` for the new shapes (`ledger_reads.py` docstring + `record_payload`); records take `cursor`, a record opens by `evidence_id`.
- Show: window (half-open, source-time) + `extent`; `state`/`states`; per-source `clocks` and `clock_statement` (never subtract virtual vs real); batches `partial`; `projection.status` STALE with `statement`; `migration` summary (empty-set statement visible); record `original`/`normalized`, `envelope`, `accepted_as`, `receipt` with `received_at` vs `decided_at`, `duplicates`, `conflicts` (conflicting envelope text).
- Route `frontend/src/shell/operatorSiteRoutes.ts` :78-82; Analysis view over `analytics_api.py` :25-29 (still legacy-gated for imported Sites — Analysis on Postgres is not built; decide in 3b whether Analysis shows Evidence-only limits).
- Lab Commit (item 4 frontend): GET commit `registered_release.delivery.batches[]`, `.publication_schedule`, `.release_blockers`, `shared_batch_ids`; `frontend/src/shell/GatewayPublicationPanels.tsx` (TERMINAL_GAP :69); refusal vocabulary `runSetupClient.ts` :933-995. Gateway health `GET /api/sites/{id}/gateway-health`.

## Checks

Architecture and agent-workflow checks passed after `59d76fe`. Full suites after `59d76fe`: backend with `ASSETOPS_TEST_DATABASE_URL` **1739 passed** (246 s); gateway **162 passed**; host **662 passed** (323 s). Frontend untouched, not run; layout evidence not applicable (no layout change).

## Risks / open

- Because the dev workspace now holds a PASSED KOBO-001 record, the running app serves KOBO-001 Evidence in the POSTGRES shape; the current frontend expects the legacy shape or 409, so Site Evidence for KOBO-001 may render wrongly until 3b. Deleting the report closes the gate again (not done; reports are immutable records).
- Item 6 walkthrough not started. Dev DB was upgraded to 0006 (additive).
- Q18 (empty-set basis), Q19 (rejection placement, batch refusals audit-only), Q20 (projection never CURRENT in S2) await the Architect.
