# S2-02 phase 3b handoff — frontend Site Evidence (ledger) and Lab Commit/status landed; phase 3c next

Branch `task/S2-02-ingestion-site-evidence`. Commits: `c17bef2` (build), `9d84f20` (tests), `32b1bcd` (bars moved to graphics module for the shell-overflow guard), `f22c320` (questions 4: Q21–Q24, fail-closed defaults). Architect rulings in `.agent/architect-S2-batch-answers-3.md` applied on the UI side (empty-set cutover renders Postgres Evidence and never says "matched"; Q17 schedule-based completeness; Q19 unwindowed refused list + untimed count, unavailable when absent, batch refusals "operational audit only"; Q20 analysis status separate from freshness, no dispatch/healthy conclusion). Backend Q14/Q15/Q16/Q19 corrections are not in this phase.

## Landed (anchors)

- `frontend/src/sites/evidenceRead.ts` — shared `read`/`query`/guards moved out of `siteEvidenceClient.ts` (re-exported there) to avoid an import cycle.
- `frontend/src/sites/ledgerEvidenceClient.ts` — ledger types mirroring `ledger_reads.py`; `isLedgerEvidence` (requires `store: "POSTGRES"`); records by `cursor`, record by evidence id, rejections.
- `frontend/src/sites/gatewayHealthClient.ts` — `GET /api/sites/{id}/gateway-health` (404 → `not_found`).
- `frontend/src/sites/siteEvidenceClient.ts` — `getEvidence` accepts legacy or ledger shape; `SiteEvidenceClient.ledger?` and `.gatewayHealth?` (created by `createSiteEvidenceClient`).
- `frontend/src/sites/SiteEvidence.tsx` — after the 409/unavailable checks, a ledger payload renders `LedgerSiteEvidence`; legacy path unchanged.
- `frontend/src/sites/LedgerSiteEvidence.tsx` — Overview: period chooser (UTC `from`/`to` into the URL, half-open wording), "What arrived" headline per state + notes (PARTIAL_BATCH, CONFLICTING, OUTDATED_CONFIGURATION), outcome count bars, gateway contact (CURRENT/STALE/UNKNOWN/none/unavailable), sources, empty-set migration note, limits. Analysis: clocks, sources table (three clocks labelled), deliveries (partial), readings by input, analysis status (STALE_PROJECTION), earlier-store comparison, refused readings (unwindowed; untimed count; duplicates link to first accepted reading), inspector (cursor paging, `record=<evidence_id>`) and reading detail (as reported vs site units, accepted-as revision ids, receipt first-received vs decided, exact message text, repeats, conflicting message text).
- `frontend/src/sites/assessmentGraphics.tsx` — `CountBars` (svg must live in a graphics module).
- `frontend/src/shell/runSetupClient.ts` — `RunCommit.commit` adds `RELEASED_TO_GATEWAY`; `registered_release` types + `isRegisteredRelease`; local diagnostics `upload` accepts `ACKED` (was `PENDING` only, which would have made the Lab diagnostics panel "unavailable" once every diagnostic was receipted).
- `frontend/src/shell/RegisteredDeliveryView.tsx` — `registeredReleaseClaim` (FULLY_RELEASED only if server flag, no blockers, schedule COMPLETE or NOT_APPLICABLE, no shared batch, gateway_complete), blocker text, publication completeness, Stage caveat, batch table in a Disclosure (shared = "Blocked"), refusals, last upload error, release button rule (Q24). Mounted from `RunCommitPanel.tsx` `CommitBody` when `registered_release` is present.
- `frontend/src/shell/GatewayPublicationPanels.tsx` — `diagnosticUploadText` (Q21), `ORDINARY_PUBLICATION_TEXT` exported.
- `frontend/src/test/settled.ts` — loading phrases "the site's gateway contact", "the refused readings".
- Tests: `frontend/src/shell/__tests__/s2LedgerEvidence.test.tsx` (19), `s2RegisteredCommit.test.tsx` (11), fixtures `frontend/src/sites/__tests__/ledgerEvidenceFixtures.ts`.

## Checks

Frontend vitest **53 files / 1269 passed**; `tsc --noEmit` clean; `npm run build` ok; `tools/check-architecture.ps1` passed (after moving the svg); `tools/check-agent-workflow.ps1` passed. Non-vacuity (each reverted with `git checkout`): dropping the schedule condition in `registeredReleaseClaim` → 3 fail; "Normalized value" label → 2 vocabulary fails; untimed `?? 0` → 1 fail; empty-set copy saying "matched" → 1 fail; shared batch shown "Released" → 1 fail. Backend/gateway/host untouched, not run. Layout evidence not run (phase 3c).

## Owner-walkthrough steps the UI now supports (phase 3c)

1. Lab run screen, Commit panel: a registered completed run shows Not fully released + blockers + publication completeness; "Commit and release" releases sealed batches; the batch table (245 rows for the Kobo run) shows states, receipts (server real UTC), shared-blocked rows; reload re-reads GET commit.
2. Terminal-gap/INCOMPLETE run: Commit panel shows "Incomplete for good"/INCOMPLETE and never "Fully released".
3. Gateway unreachable: Commit panel says "Release status unavailable ... not a refusal".
4. Lab diagnostics panel: last stored diagnostic upload state (receipt / waiting / attempt without receipt).
5. Site > Evidence for KOBO-001 (`/sites/KOBO-001/evidence`, optionally `?from=...Z&to=...Z`): headline, outcome bars, gateway contact; stop the gateway > 120 s and reload → "not heard from recently".
6. `?view=analysis`: clocks, deliveries (partial while a batch is IN_PROGRESS), refused readings incl. untimed, comparison (empty set, "none were carried over").
7. "See readings" → cursor paging → "Show reading": as reported / site units, accepted-as revisions, receipt first-received vs decided, exact message text, repeat and conflict. Reload keeps `record=`.
8. Delete/close the comparison record → 409 → "Awaiting evidence migration" (legacy Sites unchanged).

## Risks / open

- Not exercised against the live backend yet (fixtures mirror `ledger_reads.py`/`gateway_access.py`/`run_delivery_in` shapes); 3c should load KOBO-001 Evidence and a registered run's Commit panel on the real stack.
- 245-row batch table and long message text are layout-sensitive (Disclosure + `.evidence-message-text` wrap in `frontend/src/ui/primitives.css`); 3c layout evidence at narrow/desktop.
- Q21–Q24 await the Architect.
