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

# Phase b (built; commits 7d5be15, a8a6222 Evidence; 3f0452c, 76832af Lab)

## b1 Site Evidence (`LedgerSiteEvidence.tsx`, `ui/primitives.css` "V-01b Evidence" block, test `shell/__tests__/v01bEvidenceVisual.test.tsx` 10 tests: 8 failed before, all pass after; `s2LedgerEvidence.test.tsx` selector/name updates only)
- Overview status bar (read: GET evidence `counts`, `sources`): "N readings accepted · K of M sources with accepted readings · X not accepted", neutral Badge "No capability conclusion yet", link "Analysis →".
- `evidence:1` "What we can conclude now" (desc "Evidence readiness is not equipment condition"): headline, partial/conflict/outdated notes, outcome facts row `[data-evidence-outcome-facts]`, refused line, no-conclusion limit. Missing: "Not available yet: capability-by-capability conclusions (what can be said, what is missing and the next step for each). They need a reviewed capability assessment over accepted Evidence, which does not exist yet."
- `evidence:2` "Data sources · data quality, not equipment condition" (two-col ≥1100px): Source | Accepted in period | Latest taken | Latest received | Readings; zero source "No accepted reading in this period"; gateway-health contact block. Missing: "Not available yet: a status at the end of the period, a quality grade and which conclusions each source affects. No reviewed rule sets these."
- `evidence:3` "Most useful next evidence": "Not available yet: ranking the next evidence needs a reviewed rule linking missing readings to conclusions." plus "Sources with no accepted reading in this period (a fact, not a recommendation):" list, or "Every source has at least one accepted reading in this period."
- Closing notice "Record-level detail, timing and how each limit is set are on Evidence › Analysis."; earlier-store note under "Advanced details — earlier store".
- Analysis: status bar Badge "Evidence · Analysis" + "Accepted records, timing and how each limit is set". `evidence-analysis:1` "Accepted records behind the conclusions" (desc "Measured time is kept even when a report arrives late"; `listRecords`, 10/page whole site, 50 per chosen source): Source · reading | Value | Taken | Sent | Received | Record ("Open record" → record view ending "Exact message as received"); empty "No accepted reading in this period." `evidence-analysis:2` titled "How each limit is set" (Q4: "claim" banned by vocabulary guard); missing: "Not available yet: the rule that turns accepted readings into a positive capability conclusion and sets its limit (a later capability assessment)."
- Readings not accepted: visible count line; table, bars and repeats under "Advanced details — readings not accepted"; new "Original reading" column "Original reading taken <time>" from `conflicts_with_source_time`, link to `conflicts_with_evidence_id` (backlog carry closed).
- Advanced details (closed by default): which clock each time uses; sources in this period; deliveries (N); readings by input; analysis status; earlier store comparison; gateway contact (full facts).
- Open: 390 px not verified by b1; "Show this period" primary styling may look secondary; Source · reading shows source id and device id that are identical on KOBO-001.

## b2 Lab run (`shell/RunIngestionOverview.tsx`, `shell/runIngestion.css`, `RunFrame.tsx`, `RunCommitPanel.tsx` optional `onRead`, `GatewayLedgerView.tsx` Q1 label; test `shell/__tests__/v01bLabIngestion.test.tsx` 9 tests: all 9 failed before, pass after; updated `cockpitLayout`, `runExecution`, `simulatorLabGate`; 11 files 252/252)
- h1 stays "Draft run" (Q2); first h2 "Gateway & Ingestion"; below it h2 "Execution and recorded history". Seven technical disclosures prefixed "Advanced details — ".
- Status bar (`.status-strip`): commit badge (Released to gateway / Committed / Not committed), "Execution <status>", "B of M batches have a central receipt" (legacy: "Ingestion processed P of T envelopes"), frozen profile/scenario versions; "Open Site Evidence →" only with registered_release and ≥1 receipt, else "Nothing from this run has been received centrally." (legacy: "Not a registered Site: no Site Evidence link. The release is under Release and ingestion.")
- Flow strip `[data-flow-box]` world/reports/envelopes/accepted from execution, Stage and Commit reads; absent states "Execution not available.", "Stage not available.", "Not committed: nothing released, nothing accepted centrally."
- `lab:1` "Selected canonical envelope" (desc "Exactly the source boundary; no private-truth field"): earliest envelope as `<pre>` projection; "No envelope is stored for this run yet."
- `lab:2` "Truth versus observed": At / signal | Private truth | Observed (latest step); "No step yet"; missing "Not available yet: the product consequence of each report (accepted, latency retained or indeterminate). These reads give central decisions per batch, not per device report."
- `lab:3` "Release and ingestion": Commit, Batches, Central receipts, Accepted, Duplicates, Conflicts, Rejected; "Inspect accepted records" (Site Evidence analysis for run interval) only when received; actionable RunCommitPanel directly under.
- `lab:4` "What never crosses": prose + "The gateway observes, maps and publishes."; missing "Not available yet: a link from this run's accepted records to the Dispatch analysis that used them. No run-to-analysis read exists here."
- Q1 label under Stage Upload fact: "This is the gateway's local Stage statement. Central receipt is shown under Release and ingestion."
- Layout tool (`76832af`): Lab Site from `/api/sites`; registered dates 2026-10-04..05 (Foundation v10) and profiles by id@version; timeout prints `#run-setup-blocked-reason`; new registered Kobo section (`ASSETOPS_LAYOUT_V01B_ONLY=1`, `ASSETOPS_LAYOUT_V01B_RELEASED_RUN=<run>`), CDP port `ASSETOPS_CDP_PORT` (default 9333). Full run: 266 PASS / 32 FAIL. Lab FAILs are named preconditions: fuel-loss 430 L > KOBO tank 400 L; drawing unbound (current Foundation v10 ≠ frozen v7; v10 blocks mini-grid drafts, Q8) ×3; **Lab shell at phone width: main 95px of 375px (open carry S1-03 Q1)** ×2; legacy file Kobo Site absent. 26 non-Lab FAILs: operator Site sections measure `SITE` default MG-001 (absent here; pass KOBO-001 as 3rd arg).

# Phase c1 (commits 437a1cb Lab phone shell, 28743ad Evidence primary button, 49e3b49 evidence tool)

- Lab 390 root cause: the <640px shell rules applied only to `.app-frame--operator` (S1-03 Architect Q1 scoping, enforced by
  `shell-overflow.ps1`); `SimulatorLabShell` used a bare `.app-frame`, so main got ~95 of 375 px. Fix: `app-frame app-frame--lab`,
  every 640px rule lists both shells. Guard `shell-overflow.ps1` 2b now requires each narrow selector part to start with
  `.app-frame--operator` or `.app-frame--lab` and fails when either shell has no narrow rule (needs a non-vacuity proof and a
  reviewer note: it amends the S1-03 Q1 scoping because the Lab phone layout is now browser-verified).
  `overflowContainment.test.tsx` asserts `app-frame--lab`.
- Layout tool Lab section (V01B_ONLY): 71 PASS / 3 FAIL — the 3 are the Q8 drawing precondition only.
- `.evidence-toolbar .action--primary`: a later generic `.action` block (~primitives.css:1439) overrides `.action--primary`
  at equal specificity; same cascade probably affects other primary buttons (CreateSiteFrame ×3, RunSetupFrame "Create draft
  run", SimulatorLabFrame, SitesFrame) — out of scope, backlog carry.
- `tools/v01b-lab-evidence-evidence.mjs`: 101/101 claims at 1440 and 390 (screens: mock-lab, mock-evidence,
  mock-evidence-analysis, app-evidence-{populated,empty,no-site,gateway-unavailable,record-detail},
  app-evidence-analysis-{populated,empty,advanced-open}, app-lab-run(-top,-advanced-open,-not-committed), app-lab-runs-empty).
  Value→SourceEnvelope trace: row "STOPPED state" equals the read API's value; API `envelope.text` equals displayed message;
  `payload.value` equals `original.value`. Gateway unavailable is an intercepted 503 (response shape, not stored state).
  Not-committed state uses a real draft created by the layout tool (executed, never committed). Missing-Site copy is
  "No such site". The layout tool creates a draft per run (populated private store now has ~40 runs).
- Review focus: Lab flow box 2 reads "321 reports published, 1 dropped / 329 admitted by the gateway" (two different reads'
  counts side by side; the difference is not explained on screen).
