# V-01b handoff — phase a (survey, gap inventory, Lab precondition)

Branch `task/V-01b-evidence-lab-visual`. Task `tasks/V-01b-evidence-lab-visual-fidelity.md`. Binding precedents:
`.agent/architect-V-01a-answers.md`, `.agent/architect-V-01a-round3-answers.md` (incl. Addendum),
`D-2026-10-12-v01a-owner-visual-rulings`, `D-2026-10-12-v01a-round3-readiness-and-organization`,
`D-2026-10-04-plain-language-analysis-views`. Questions: `.agent/V-01b-questions-1.md`.

## Private servers (phase a)

`tools/v01b_lab_evidence_walkthrough.py` (new; copy of `assetops_s4cases` + the producer's Lab files and a
non-delivering copy of its gateway ledger; step 4 runs the Evidence store comparison so the ledger read opens).
Implementer copy: `--db assetops_v01bimpl --empty-db assetops_v01bimplempty --work-name v01b-impl`, API 8884/8885,
Vite 5384/5385 (`$env:ASSETOPS_API_PORT=8884; npm.cmd run dev -- --port 5384 --strictPort`). Never use
8860-8863/5360-5363. Data: KOBO-001 (POSTGRES), 329 accepted readings on 2026-10-02 from 6 sources (8 registered),
0 refused; one registered run `run-234889a36d0a4333a1e8877bf5015762` (COMPLETED, 97 steps, `RELEASED_TO_GATEWAY`,
198 batches with central receipts in the Commit read; Stage = GATEWAY_LEDGER, 329 envelopes). Empty window:
`from=2026-09-01T00:00:00Z&to=2026-09-02T00:00:00Z`. Empty store (no Site): API 8885.

## Gap inventory (mock survey: `frontend/mockups/v69/index.html` L519-534 lab, L345-366 evidence/analysis)

### Site Evidence Overview (`frontend/src/sites/LedgerSiteEvidence.tsx`; KOBO-001 uses the ledger path)
Mock: subtabs Overview|Analysis; `.statusbar` (badge + "5 capabilities · ..." + "Portfolio evidence →");
`evidence:1` "What we can conclude now" full-width table Capability|Evidence|What we can say|What is missing|Next step;
row 2 two-col (1.8fr/1fr): `evidence:2` "Data sources · data quality, not equipment condition" table
Source|Status at window end|Quality|What it provides|Affects, and `evidence:3` "Most useful next evidence" (ranked
attention items); closing blue notice linking to Analysis.
App: native unstyled window chooser; "What arrived" one-line panel; full-width "Gateway contact"; orphan outcome
bars table; "Sources" as eight prose lines with buttons; three loose paragraphs (refused, migration, no-conclusion).
Supported (registry `evidence:1#a`, `evidence:2#a`): accepted counts per window, outcome counts, partial/conflict/
outdated notes, explicit no-conclusion limit, per-source accepted count/latest taken/latest received, gateway
central contact (CURRENT/STALE/UNKNOWN, server time). Unsupported (named missing states, never mock values):
`evidence:1#b` capability/claim-ceiling rows (no capability assessment); `evidence:2` per-source "status at window
end"/"quality" judgement and "Affects" capability; `evidence:3#a` ranked next evidence (no rule; panel status gap);
"Portfolio evidence" (W3, no route).

### Site Evidence Analysis
Mock: statusbar "Evidence · Analysis"; `evidence-analysis:1` "Accepted records behind the conclusions" table
Source · reading|Value|Measured|Sent|Received|Record ("Open record"); `evidence-analysis:2` "How a claim limit is
set" two prose paragraphs. Nothing else.
App: very long page (clock panel, sources table, ~200-row Deliveries table, readings by input, analysis status,
earlier store comparison, refused readings, inspector/record detail with SourceEnvelope lineage).
Supported: `evidence-analysis:1#a` record inspection with configuration/receipt lineage (Taken/Sent/Received exist);
`evidence-analysis:2#a` S2 explanation (partial, conflict, outdated configuration, analysis status, no conclusion).
Unsupported: `evidence-analysis:2#b` positive capability claim-limit rule (core, open) → named missing state.
Carry folded here: Evidence conflict original time (`conflicts_with_source_time` sent by backend
`ledger_reads.py:141`, typed `ledgerEvidenceClient.ts:240`, never rendered) — the task's "late/contradictory states".

### Lab run (`frontend/src/shell/RunFrame.tsx`, `RunCommitPanel.tsx`, `RegisteredDeliveryView.tsx`, `GatewayLedgerView.tsx`)
Mock "Gateway & Ingestion": statusbar (run · Committed, Ingestion completed, frozen inputs, "Open in AssetOps →");
4-box flow strip Private world → Device report → SourceEnvelope → Accepted evidence; two-col rows:
`lab:1` Selected canonical envelope (code block of one envelope) | `lab:2` Truth versus observed (At/signal|Private
truth|Observed|Product consequence); `lab:3` Release and ingestion (key-values + "Inspect accepted record") |
`lab:4` What never crosses (prose + link).
App: h1 "Draft run", execution controls, a ~5000 px developer cockpit, then nine disclosures; the four mock panels
exist only inside disclosures (`RunFrame.tsx:876-909` world, `:1144` Stage, `:1347` Commit, `:1350` boundary).
Supported (`lab:1-4#a`): stored envelope, private world beside device reports (Lab only), persisted release and
central receipt, static boundary text.

### Lab layout-evidence precondition (diagnosed)
`tools/layout-evidence.mjs` `SUBMIT_RUN_SETUP` (:601-672) picks radio `MG-001`, else the first radio, and fixes
2026-09-21/22. `/api/sites` now lists only Postgres Sites, so on the walkthrough copy the only radio is KOBO-001
(POSTGRES). `GET /api/sites/KOBO-001/foundation?at=2026-09-21T00:00:00Z` answers `FOUNDATION_REVISION_NOT_FOUND`
(first registered period 2026-09-29), so `RunSetupFrame.tsx:994-1001` keeps "Create draft run" disabled
(`foundationVersion === null`). Verdict: tool, not product — the product correctly refuses an unconfigured instant.
Fix belongs in the tool (registered-Site dates/profiles; print `#run-setup-blocked-reason` on timeout).

## Product truthfulness finding (questions file Q1)
Stage read for a registered run says "Upload pending: no batch has been sent and no receipt exists" (constant
`contracts/assetops_contracts/gateway_stage.py:59-61`, "Until S2-02 adds authenticated upload, every registered batch
is pending"; used `backend/assetops_backend/simulator_lab_api.py:1827`) while the Commit read on the same run shows
198 batches with central receipts and the gateway ledger copy has 198 `batch_receipt` rows. Stale S2-01b constant.
