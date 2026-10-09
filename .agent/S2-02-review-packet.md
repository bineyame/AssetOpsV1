# S2-02 review packet - Authenticated ingestion and Site Evidence

Task `tasks/S2-02-ingestion-site-evidence.md` (USER_REVIEW_REQUIRED: S2 Evidence owner checkpoint). Branch `task/S2-02-ingestion-site-evidence`. Phases: 1 (ledger), 2 (credential/transport/diagnostics/Commit), 3a/3a2 (corrections, Postgres Evidence reads, legacy comparison), 3b (frontend Evidence + Lab Commit), corrections (Q14/Q15/Q16/Q19/Q21), 3c (this: demo, real-stack verification, carries, packet). Handoffs `.agent/S2-02-phase-{1,2,3a,3a2,3b}-handoff.md`, `.agent/S2-02-corrections-handoff.md`; Architect rulings `.agent/architect-S2-batch-answers-2.md`, `-3.md`.

## Outcome delivered

A completed registered simulated Kobo run Commits its existing sealed Batch V2 bytes. The separate gateway uploads them over direct TLS with an owner-only bearer credential. Postgres records per-ordinal decisions and Receipt V2. Imported KOBO-001 Site Evidence and Evidence Analysis read Postgres behind a fingerprinted empty-set comparison gate. Lab Commit shows full, partial and terminal release from GET commit and the publication schedule. Central gateway health shows UNKNOWN, then CURRENT, then STALE from server receipt time. A repeatable owner walkthrough script runs the whole path end to end on an isolated database and work directory.

## Files materially changed (all phases)

- Backend: migrations `0005_evidence_ledger`, `0006_gateway_access`; `evidence/{ledger,ledger_service,gateway_access,ledger_reads,legacy_comparison,provision_gateway,composition}.py`, `evidence/adapters/{postgres_evidence_ledger,postgres_gateway_access,gateway_credential_file,legacy_comparison_file}.py`, `evidence_api.py`, `gateway_api.py`, `evidence_migration.py`, `serve_tls.py`, `main.py`, `sites/cutover.py`, `simulator_lab_api.py`.
- Contracts: `ingestion_receipt_v2.py`.
- Gateway: `uploader.py`, `credential_protection.py`, `service.py`, `ledger.py` (SQLite migration 5), `ipc.py`, `__main__.py`.
- Host: `lab_execution.py` (terminal-gap preflight, release/delivery views), `gateway_publication.py`.
- Frontend: `sites/{LedgerSiteEvidence.tsx, ledgerEvidenceClient.ts, gatewayHealthClient.ts, evidenceRead.ts, siteEvidenceClient.ts, SiteEvidence.tsx, assessmentGraphics.tsx}`, `shell/{RegisteredDeliveryView.tsx, GatewayPublicationPanels.tsx, runSetupClient.ts, RunCommitPanel.tsx}`.
- Tools/guards: `tools/checks/configuration-persistence.ps1` (ledger/access writer confinement, cutover gate, freshness, issuance order); `tools/layout-evidence.mjs` (S2-02 block, 3c); `tools/s2_demo_walkthrough.py` (3c).

## Acceptance criteria

1. **Credential and identity boundary - met.**
   - The credential is an `aog1.<selector>.<secret>` token. The server stores only the selector and a SHA-256 verifier.
   - The secret goes only to a new versioned file with an owner-only DACL. The file is written and verified before the commit (Q8/Q16). The gateway re-checks the DACL before every read (Q15).
   - The principal comes from the credential and gateway rows only. Results: 401 wrong or revoked credential, 403 scope, mode or source failure (no ledger row), 426 plaintext.
   - Live (3c):
     - wrong credential gives 401;
     - plain HTTP gives 426;
     - after rotation the old credential gives 401 at once, and the new one reads the byte-identical receipt;
     - the old file is left untouched.
   - Tests: `test_s2_gateway_access_postgres.py` (failure at five boundaries, rotation), gateway permissive-ACL refusal.
2. **Immutable batch and per-record decisions - met.**
   - Batch/Receipt V2 is built on exact bytes, with short per-chunk transactions.
   - Live: an identical retry returns 200 with ledger counts unchanged (246/293/293/0 before and after).
   - Live: same ID with changed bytes (validly resealed) returns 409 `BATCH_ID_CONFLICT`, adds one audit refusal row and leaves the stored batch unchanged.
   - Live: the outage, then an exact-byte retry, leaves the server `payload_sha256` equal to the gateway's sealed digest.
   - Rejected sibling, crash/resume and 202 `IN_PROGRESS` are test evidence only (`test_s2_evidence_ledger_postgres.py`; Q32).
3. **Accepted-as validation and normalization - met (tests + live acceptance).**
   - Tests prove strict V3, the exact `foundation_valid_from` spelling, half-open periods, superseded-but-original acceptance with `configuration_outdated`, closing-boundary `OUTSIDE_FOUNDATION_PERIOD`, ENUM and `SCHEMA_UNSUPPORTED`.
   - Live: 293 accepted readings with normalized values and revision IDs. The 15:00:00Z closing readings were accepted, because their binding period does not end there (Q36).
4. **Identity hardening - met** (phase 1). An `asset_code` UPDATE is refused, and the binding asset UUID still resolves to its Foundation component.
5. **Gateway delivery and Commit - met.**
   - Live: Commit released 246 sealed batches (the spec text said "245"). They uploaded in 10 bounded passes of 25.
   - GET commit `fully_released=True` with every batch ACKED.
   - The gap run shows `fully_released=False`, `TERMINAL_GAP`, blockers `PUBLICATION_REFUSED` and `PUBLICATION_GAP`. Its later advance returned 409 and the publication read is unchanged.
   - A shared batch stays blocked (tests).
   - The Lab writes no Evidence: the guard holds, and the commit route branches to `release_registered`.
6. **Central diagnostics - met.**
   - Live: UNKNOWN before the first report, then CURRENT (`SERVER_RECEIVED_AT`, cadence 60 s), then STALE after 125 s of silence, then CURRENT after restart.
   - Identical/changed diagnostic bytes give 200/409 (tests).
   - Q21: diagnostic refusal and failing-code text in the Lab panel.
7. **Site reads and visible limits - met for KOBO-001 with an empty-set basis.**
   - The 3c regenerated dev-DB report is schema v2, `empty_set: true` and PASSED, bound to the tenant, the Site UUID, the environment `postgresql://127.0.0.1:55432/assetops` and the inventory digest `sha256:3e6ad354...`. Copy: `.agent/S2-02-legacy-comparison-KOBO-001.json`.
   - With it, a backend on the current code with `DATABASE_URL` (port 8620) served KOBO-001 Evidence: `store: POSTGRES`, state `NO_DATA`, records 200. SITET26 stayed on its file path (200).
   - Demo DB: state `ACCEPTED` plus `STALE_PROJECTION`, 317 accepted, no rejections, record detail with `accepted_as`, `envelope` and receipt (`received_at` 12:13:06.819669Z, `decided_at` 12:13:06.876669Z).
   - Layout: both pages hold at 1280 and 640 px.

**Demo setup / cutover / owner review.**
- The comparison is honest about the empty set and claims no replay parity. The non-empty V1 parser fixture regression is retained.
- Live V2 acceptance and the selected-window link are in the walkthrough.
- Not built (withheld claims): the generator-status run and the capability channels are unconfigured.
- S3 handover: dispatch recompute jobs are queued, and the comparison report carries `s3_fixtures` (empty on the dev DB).

## Checks run (3c)

- Demo, `tools/s2_demo_walkthrough.py run` at `0a22895`:
  - every step passed and every started process stopped;
  - output `.agent/S2-02-demo-run-output.txt`;
  - no raw secret in the output (redacted selectors only).
- Layout, `ASSETOPS_LAYOUT_S2_02_RUN=<main run> ASSETOPS_LAYOUT_S2_02_RECORD=<id> node tools/layout-evidence.mjs http://localhost:5310` against `serve` plus an isolated vite on 5310:
  - ALL CLAIMS HOLD, `.agent/S2-02-layout-evidence.txt`;
  - Evidence overview, analysis (280 table rows) and reading detail (796-character message, wraps, overflow 0) at 1280x800 and 640x700;
  - Lab Commit (246 batch rows, scroller right 559 at 640).
- Layout non-vacuity: with `.evidence-message-text` set to `white-space: pre`, two claims FAILED at each width (scrollWidth 6160 vs 625); the CSS was then reverted.
- Carries:
  - N1 asserts `BAD_REQUEST`; non-vacuity: expecting `PUBLICATION_INSTANT_INVALID` failed it.
  - N3 rewording.
  - C2 link-loss test asserts stored diagnostics byte-identical across a real reconnect; non-vacuity: rewriting `diagnostic_outbox` bytes with its triggers dropped failed it ("earlier diagnostics byte-identical").
- Frontend: vitest **53 files / 1270 passed**; `tsc --noEmit` exit 0; `npm run build` exit 0.
- Full suites after the last code commit `30b8cd5`:
  - backend with `ASSETOPS_TEST_DATABASE_URL`: **1750 passed** (277 s);
  - gateway: **164 passed**;
  - simulator: **265 passed**;
  - host: **662 passed** (444 s);
  - `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed (run with `-ExecutionPolicy Bypass`; the first attempt without it was refused by execution policy).

## Known deviations

- Batch count is 246 batches / 293 envelopes for the post-run publication profile v2 run, against the spec's 245 / 292. The difference is one envelope and one batch. It is probably the post-run closing report, but this was not investigated.
- Rotation requires a gateway restart to switch `upload_credential_file` (Q33).
- The demo isolates by a `git archive` copy with its own `var/` (Q34).
- Two runs over the same window both appear in Site Evidence (Q35).
- Not live: rejected sibling, crash/resume 202, closing-boundary rejection (Q32/Q36).
- Not done: C3/N2 full seeded layout run. The isolated demo store lacks the legacy Sites and scenario fixtures it needs, the owner's servers were off limits, and the context budget was reached. The carry stays open.
- The owner's long-running backend on 8000 still answers 409 for KOBO-001 (its process predates this code or lacks `DATABASE_URL`). It was not restarted.

## Residual risk

- The Windows DACL check is verified on this machine's profile paths only.
- Freshness depends on the server clock.
- The comparison gate is newest-report-wins, so a newer report from another environment in the same `var/` closes it (fail-closed).
- The checked-in test TLS key remains test-only. The demo generates its own key each run.

## Open questions

`.agent/S2-02-questions-1.md` .. `-5.md` (answered in `architect-S2-batch-answers-2.md`/`-3.md`, except questions-5 Q25-Q31, open with fail-closed defaults) and `.agent/S2-02-questions-6.md` (Q32-Q36, new).

## User-review focus

Follow `.agent/S2-02-owner-walkthrough.md`:
- Site Evidence period link, reading lineage, gateway contact turning stale, the 246-row Commit table, the terminal-gap run;
- the explicit limits: no historical KOBO replay, no S3 projection, no physical-device proof.

Owner acceptance is recorded separately from technical review. A fresh Claude reviewer and the S2-wide Codex review follow the owner routing.
