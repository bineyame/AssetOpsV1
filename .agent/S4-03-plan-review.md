# S4-03 planning packet: fresh Claude review

Reviewer: fresh Claude reviewer (did not author the packet). Date 2026-10-13.
Worktree `AssetOpsV1-gap-planning`, branch `plan/S4-03-refine`, reviewed commit `2938d74` on main `d9eb9ca`.
Scope: `tasks/S4-03-finding-evidence-history.md` (47 lines) and the `tasks/README.md` S4-03 row, against `.ai/WORKFLOW.md` "Task Spec Size", the built S4-01 code, the registry and the ledger.

## Verdict: ACCEPT (with carries C1-C6 below)

An implementer holding this packet, its references and the built state can start phase 1 without asking a question. The anchors are real and described correctly. The read/route contract matches the built S4-01 API. The packet keeps cited evidence separate from analytic input and correctly forbids `knowledge_at` replay. Size is 47 lines against a 220-line ceiling (finding semantics). The three phases are each a bounded backend or UI context. No finding blocks activation. C1 and C2 are bookkeeping that the coordinator or Planner should do at activation, or name in the closeout. Neither needs an Architect decision.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0. "Registry valid: 212 nodes, 11 linked pilot panels".
- `python frontend/docs/architecture/check_v69_ledger.py`: exit 0. "v6.9 ledger valid: 110 screens, 88 distinct models, 258 panels".
- I did not run `check-all` because this worktree has no node_modules or .venv (per the dispatch). No product code changed, so I ran no product suites.

## Anchor verification (all exist; described correctly unless noted)

- `backend/assetops_backend/finding_api.py:104-106`: `GET /api/sites/{site_code}/findings/{finding_id}` already takes `revision_id`, `after_revision_no` (ge 0) and `limit` (default 200, le 500). The packet's "extend ... or add child routes" fits this.
- `analytics/finding_read.py:224-332`: `selection.selected_by` is LATEST_RECORDED or EXACT_REVISION_ID. `revision.cited_evidence` is distinct from `runs[].input_evidence_count` (count from `analytic_run_evidence`, `postgres_finding_store.py:288`). `input_evidence_sha256`, `SOURCE_CLOSED`, `revision_page.total/next_after_revision_no`, `revision_groups` (BASIS_REFRESHED grouping) and `REPLAY` (no `knowledge_at` replay) are all present as described. The current revision summary (`_summary`, :128-146) carries only `candidate_minutes`. The necessary and indeterminate quantities per History row are therefore a phase-1 extension, which the packet's "extend" covers.
- `postgres_assessment_store.py:580-594` `_evidence`: envelope_sha256, message_id, batch/external batch, gateway/source/epoch/sequence, source_mode, foundation/binding revision IDs. These match the Evidence fields the packet lists.
- `evidence_api.py:158,429-457` plus `postgres_evidence_ledger.py:609-627`: the record route accepts either evidence UUID or message ID, so `{evidence_id|message_id}` is accurate. Envelope text and sha256 are returned (`ledger_reads.py:336`).
- `performance_api.py:99`: `/api/sites/{site_code}/performance/dispatch/revisions/{revision_id}` exists (S3 drill-down).
- "60-row preview" = `PerformanceDispatch.tsx:770`. The Finding page's own preview is 8 (`SiteFinding.tsx:43`). The S3-01u day browser is an open task, which is correct as a caution.
- `backend/conversions/s4-finding-cases-v1.json`: F01-F06 and F08 cases plus `test_scoped` (F07) are present. `tools/s4_finding_cases.py` is present. See C3 for two label imprecisions.
- Registry: `I-finding-evidence-read`, `I-finding-evidence-ui`, `I-finding-history-read`, `I-finding-history-ui` and `I-S4-03` are open and assigned to S4-03. Portions `finding-evidence:1#a`, `finding-evidence:2#a` and `finding-history:1#a` exist, are core and are open (`v69-dependency-registry-pilot.json:287,288,316`). The owner W1 core panels match.
- G-01: `frontend/src/ui/MissingClaim.tsx`, `gapCatalogue.ts` and `tools/checks/missing-claim-scan.mjs` exist. The scan PATTERNS and the non-expanding file+literal baseline (SEED_CEILING 16) match the packet's AC4 description and `D-2026-10-13-g01-placement-and-orphan-scan-boundary` (DECISIONS.md:4095).

## Findings / carries

**C1 - Medium (closeout gap, not a preference). Registry acceptance text still says "knowledge cutoff".**
`v69-dependency-registry-pilot.json:184` (`I-S4-03` acceptance_target: "...accepted-source lineage and knowledge cutoff after reload"), `:216` (`I-finding-history-read`: "Read immutable revisions at knowledge cutoff") and `:316` (`finding-history:1#a` boundary: "Select exact finding_revision_id and knowledge cutoff").
The packet (line 23) correctly forbids arbitrary `knowledge_at` replay, per DECISIONS.md:4049 (`D-2026-10-11-s3-phase-2-selection-and-read`) and the built `REPLAY` statement. The closeout paragraph (line 45) does not tell anyone to reconcile these targets. As written, a closeout Reviewer either judges S4-03 against a claim it deliberately does not make, or resolves nodes whose text overclaims.
Fix: add one sentence to line 45 that rewords these three texts to "exact stored revision and its recorded basis/watermarks; no arbitrary knowledge_at replay (D-2026-10-11-s3-phase-2-selection-and-read)". The existing decision already rules on this, so no new Architect decision is needed. Because `finding-history:1#a` has `reviewed_mapping: true`, the closeout Reviewer should note the boundary-text change explicitly.

**C2 - Medium (activation bookkeeping). The ledger still shows finding-history as Deferred with no task.**
`v69-screen-ledger.json:2329` `finding-history` has `coverage: "deferred"`, `task: null` and `to_candidate.task_gate` "Planner must refine S4-01 or a bounded companion slice with reviewed read, fixture and visual path before activation". `:2271` `finding-evidence` has `task: "S4-01"`.
`tasks/README.md:58` says the Planner updates `to_candidate` when refining. The refinement left the ledger untouched and defers all ledger review to closeout (packet line 45). This packet, with its reviewed read, fixture (`D-finding-revisions`, resolved) and visual path, now meets that task gate.
Fix (Planner or coordinator, at activation): set `finding-history.task` and `finding-evidence.task` to S4-03 and record the met `to_candidate` gates, citing this packet and this review. Keep `to_real` and the tier unchanged. The ledger checker passes as-is, so this is a consistency carry rather than a blocker.

**C3 - Low (anchor precision), packet line 43.**
"Inspect F01 ordinary gateway case": the ordinary gateway-sealed case is `F01-gateway` (`tools/s4_finding_cases.py:16-20`). Plain F01 is a labelled authenticated fixture like the others.
"F04 late append/retry": F04 is `late-earlier-acceptance`. The retry case is F08 (`retry-and-absent-basis`).
Fix: correct both names so the Reviewer compares the right cases.

**C4 - Low (honest-missing-state ambiguity), AC4 at line 31 together with line 29.**
Line 29 asks to "Name mock ActionEvent/recommendation content unavailable". Visible absent-capability copy needs `<MissingClaim>` with a new `mock_gaps` node and placement. Today the catalogue has only `G-readiness-gateway-firmware` (`gapCatalogue.ts:14`). A new node needs the fields required by `D-2026-10-12-mock-gap-closure-mechanism` (owner_or_role, allocation, boundary and so on).
The alternative, "recorded for G-04", names no record location. Neither route forbids rewording the copy to slip past the three scan PATTERNS.
Fix: state the fail-closed default. Either do not render the mock-only ActionEvent/recommendation content and list its mock element IDs in the closeout for G-04, or render it through `<MissingClaim>` with a new catalogued node. Paraphrasing an absent-capability statement to avoid the scan is not allowed.

**C5 - Low (route clarity), lines 16 and 20.**
A legacy T028 assessment-keyed Finding surface with its own `evidence` tab exists at `/findings/:siteId/:assessmentId/:findingTab` (`operatorSiteRoutes.ts:158-170`, `SiteAnalyticsFrames.tsx:211`). The packet does not say that this is not the S4-03 target. It also leaves the "named Evidence or History view" URL shape open, and that shape is the reload/back contract.
Fix: one clause naming the frontend child shape under the canonical Site route (for example `/sites/{site}/findings/{id}/evidence|history?revision_id=`, built from `siteFindingHref`) and stating that the legacy tabs are not repurposed.
Optional: name the existing walkthrough and browser-evidence scripts to extend, `tools/s4_finding_walkthrough.py` and `tools/s4-finding-evidence.mjs`.

**C6 - Low (wording), line 10.**
"Coordinator should reconcile that ordering edge" implies the registry needs an action before activation. It does not (see Q5 below).
Fix: "No registry change is needed; `sequenced_after` records history (WORKFLOW.md:202). Record the owner's choice in the handoff."

Optional note, not a carry: a record link built from a message ID can return 409 `RECORD_AMBIGUOUS` (`ledger_reads.py:326-330`). Prefer the exact evidence ID for drill-down links.

## Q5: the `I-S4-03.sequenced_after: ["I-S4-02"]` edge

- `.ai/WORKFLOW.md:202`: "`sequenced_after` records history; an `enables` path supplies planning benefit only". Selection requires closed technical `requires`, not ordering edges. `v69-dependency-registry-pilot.md:9` adds that it "is excluded from distance, reach and readiness". It does **not** gate selection. The next-work report already ranked `I-finding-evidence-read` as eligible.
- Precedent: `I-S4-01` is resolved and merged while its `sequenced_after: ["I-S3-02"]` points at a still-open node.
- `I-S4-03.requires` does not contain S4-02 (registry:184), so the technical gate is S4-01 and its fixtures, and both are resolved.
- The checker (`check_v69_dependency_registry.cjs:127-128`) enforces `sequenced_after` equal to the previous README queue row. Deleting or rewriting the edge alone would fail the guard. Making it match the actual order would mean reordering the README rows (S4-03 before S4-02), which also shifts S4-02's, S4-04's and S5-01's chain.
- DECISIONS.md:3971 (older W1 order guidance, "binding until reconciled") was superseded by the pre-S3 reconciliation that wrote WORKFLOW.md:202 (`376486e`), and the S4-01 precedent shows that reading in practice.

**Recommendation: change nothing in the registry.** Record the owner's verbatim choice (`.agent/owner-next-work-2026-10-13.md`) in the coordinator handoff at activation. No Architect decision is needed. If the queue is later made to reflect delivered order, that is a Planner queue reorder (README rows, registry chain and checker agreeing), done outside an active slice.

## Q6: decisions needed before activation

None blocking. Every semantic the packet relies on is already decided: the revision/episode model, no `knowledge_at` replay, the routes and refusals, cited versus input evidence, and the MissingClaim boundary. C1 and C2 are Planner or coordinator edits under existing decisions. The owner checkpoint (`USER_REVIEW_REQUIRED: true`) remains at closeout, and the packet correctly leaves recording the owner's words to the coordinator.

## Closeout guidance check (item 4)

Line 45 promotes only the proven `finding-evidence:1#a`, `finding-evidence:2#a` and `finding-history:1#a` portions. It keeps partial status and W1 core gates, keeps G-04 for non-core backfill, and says passing the scan does not make the screen Real (line 31). It does not over-promote. C1 is the one missing item.
