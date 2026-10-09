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

- Batch count 246 / 293 versus the spec's 245 / 292: explained in Fix round 1 (the profile-v2 delayed closing report).
- Rotation requires a gateway restart to switch `upload_credential_file` (Q33).
- The demo isolates by a `git archive` copy with its own `var/` (Q34).
- Two runs over the same window both appear in Site Evidence (Q35).
- Not live: crash/resume 202 and closing-boundary rejection (Postgres test evidence, Q32/Q36). The rejected sibling is live via the labelled fault fixture (Fix round 1).
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

## Fix round 1 (review F1; Architect batch 4 items 1-4)

Commits: `15f5c62` F1, `888a836` Q28 (both by the previous implementer, verified here), `c128129` + `1eb52ea` Q26, `8aa35a6` + the following commit Q32/count (walkthrough).

| Item | Status | Evidence |
| --- | --- | --- |
| F1 forwarded scheme | Done | `serve_tls` passes `proxy_headers=False`. `gateway_api.install_gateway_tls_boundary` returns 426 for any gateway request that carries `X-Forwarded-Proto` or `Forwarded`. Test `test_a_forwarded_scheme_header_never_satisfies_the_tls_boundary[both headers]`. |
| Q28 uncertain COMMIT | Done (complete at `888a836`; no change needed) | See "Q28 behaviour" below. |
| Q26 store root | Done | See "Q26 behaviour" below. |
| Q32 rejected sibling | Live | See "Q32 behaviour" below. |
| 246/293 vs 245/292 | Explained, expected | See "Count difference" below. |

**Q28 behaviour.** An ambiguous issue failure keeps the new protected file. `PostgresGatewayAccess.issue_outcome` then discards the old pool and does a fresh read of the scoped gateway, the selector's verifier, `credential_ref` and the named sources.
- Full match: issued. The command prints the new file to switch the gateway to.
- No row with the new selector: proven non-commit. Only the new file is removed, and nothing is claimed about the old credential.
- Otherwise, or if the database is still unreadable: `ISSUE_OUTCOME_UNKNOWN`, exit 3. The file is kept and rotation is halted.
- Nothing is ever reissued blindly.

Tests cover committed-but-response-lost, rolled back, and still unavailable (two variants). `ProvisioningRefused` stays a proven in-transaction rollback.

**Q26 behaviour.**
- Report schema v3 adds `store_root`: the sha256 of the canonical resolved evidence and commit roots, from `canonical_root()` on both ports and adapters. No path is stored.
- `permits_cutover` closes the gate when that root is missing or different. `ImportedEvidenceReads` passes the current root on every read.
- The Q14 configuration-persistence guard now requires `store_root=self._current_store_root()`.
- Tests:
  - same database, same tenant and Site, and zero inventory from another root stays closed (pure test, and all routes in the Postgres test);
  - the adapter canonicalises spelling;
  - v2 reports stay closed;
  - Evidence responses carry no `store_root` and no path.
- The developer KOBO-001 report was regenerated (v3, PASSED, `.agent/S2-02-legacy-comparison-KOBO-001.json`). The isolated demo makes its own in step 2.

**Q32 behaviour.** Walkthrough step 8b posts a FAULT FIXTURE Batch V2 over the normal authenticated HTTPS route. It holds two envelopes copied from a sealed reading under the sequence epoch `fault-fixture-epoch`.
- Result: 200 {accepted 1, rejected 1}.
- Ordinal 1 is `BINDING_NOT_REGISTERED` on `source.signal_id`.
- After reload, `/evidence/rejections` lists it and Site Evidence lists the batch.
- The step says the gateway never emits such input. Crash/202 and the outside-period rejection stay Postgres test evidence.

**Count difference.** Step 5 now diffs the gateway's sealed batches. After run-to-end it holds 245 batches / 292 envelopes. The advance to 15:10 adds exactly one batch, holding one envelope.
- What it is: `battery-pcs-controller/state-of-charge`, source time `2026-09-30T15:00:00Z`, published `15:10:00Z`, publication profile `registered-kobo-publication` v2.
- In this run: batch `ad6fab4b…0b5ea`, source `01e01d6a…2548`.
- Why it is expected: it is the profile-v2 delayed closing report, as in the S2-01c phase-3a proof. The earlier 245/292 count stopped before the post-run advance.

**Checks (after the fix commits):**
- Isolated walkthrough `run`: exit 0, every process stopped. Recorded in `.agent/S2-02-demo-run-output.txt`; no full credential token in it.
- Test suites:
  - backend with `ASSETOPS_TEST_DATABASE_URL`: **1760 passed**;
  - gateway: **164 passed**;
  - host: **662 passed**.
- Frontend: not touched.
- Architecture and workflow checks: passed.
- Non-vacuous proofs, each reverted with `git checkout`:
  - dropping the header test fails both F1 tests;
  - forcing reconcile to `NOT_ISSUED` fails the lost-response test and both unreadable tests;
  - forcing `UNKNOWN` fails the lost-response and rollback tests;
  - removing the gate's store-root check fails the Q26 test;
  - passing `store_root=None` in `scope` fails the architecture guard.

**New questions:** `.agent/S2-02-questions-7.md`.
- Q37: halt rotation is an instruction, not a lock.
- Q38: residual window on a proven non-commit.
- Q39: servers on pre-fix code close KOBO-001 on the v3 report; restart the owner's servers on this branch.
- Q40: root identity semantics.

**Review:** focused independent re-review is required (Architect batch 4). Then the S2 Evidence owner checkpoint (USER_REVIEW_REQUIRED).

