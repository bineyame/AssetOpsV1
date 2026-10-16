# W1-UX-03 — Evidence, Dispatch and Analysis presentation

Status: done (merged to main 2026-10-17; review ACCEPT after fix round 1; owner visual acceptance in the combined W1 walkthrough); was in_review (built 2026-10-17 on `task/W1-UX-03`, phases 1-2; packet `.agent/W1-UX-03-review-packet.md`); activated 2026-10-16 from main `b4a89314`. Branch `task/W1-UX-03`, after reviewed/merged W1-UX-01. Frontend only. Owner walkthrough deferred to combined W1. Scope: registry IDs `evidence`, `evidence-analysis`, `dispatch`, `analysis`. Use [umbrella inventory](W1-UX-mockup-fidelity.md), v69 named screens/manifest and S2-02/S3-01/S3-02b exact-read packets.

## Visible result

Evidence leads with “Which readings can we rely on?” and a coverage/source timeline. Separate accepted/rejected/duplicate records, central contact and derived-analysis freshness; fresh gateway receipt cannot imply fresh source facts or current analysis. Claim-limit card leads with what selected assessment supports and a covered/missing span visual; keep missing role and selected-window bound beside it. Dispatch leads with the generator story and block classification timeline, selected block and limitation. Analysis turns accepted measurements into a short evidence → rule → bounded conclusion sequence. Existing detailed tables and direct record links remain in their owning Analysis/Evidence view; only a few labelled exact references use the small disclosure; no selected revision/cutoff loss. Revisit S4-05b interim source labels for plain contact/fact-age explanations without implying physical origin or equipment condition.

First seams: `LedgerSiteEvidence.tsx:377-502,649-737,774-801`, `EvidenceClaimLimit.tsx:300-381,509-549,667-728`, `PerformanceDispatch.tsx:291-317,399-416,600-624`, `assessmentAnalysis.tsx:242-257`. Preserve S3-02b `Technical details` exact records, rule and versions while replacing default “claim limit” style language. Keep unsupported evidence-health grades and source status explicit `MissingClaim` states. No conclusion from a missing battery-limit report, stale analysis or refused read.

Shared acceptance applies to this slice: opt every owned route into the W1 vocabulary set as it migrates; scan default, graphics, accessibility and Analysis/Evidence prose. With the exact-reference disclosure closed, test each applicable non-positive state for a visible plain state sentence, scope and “as of <time>” outside it. Keep material limitations beside the headline, and substantive depth in the owning contextual tab/view link at 1440 and 390. Preserve labelled exact references, authored/test-data qualification and fail-closed assertions. Capture 1440/390 served app versus `frontend/mockups/v69/index.html#/<id>` using a per-slice Playwright evidence script following `tools/v01a-foundation-evidence.mjs`; record each skipped capture as **not run** with its blocking precondition.

## Phases and proof

| Phase | Deliverable | Focused proof |
| --- | --- | --- |
| 1 | Evidence and selected claim-limit hierarchy, source/coverage visual, disclosure | S2/S3 UI tests for accepted/rejected/duplicate/missing/stale/refused and selected ID/reload; v69 `evidence`, `evidence-analysis` screenshots at 1440/390. |
| 2 | Dispatch/Analysis block timeline and causal story; finish vocabulary audit | Exact selected revision and source links, indeterminate/missing block, late input/pending reassessment, no raw model version by default; 1440/390 `dispatch`, `analysis` screenshots. |

Focused tests per phase; final-revision full `npm.cmd test`, type check, registry checker, relevant `tools/check-all.ps1` guards; fresh independent review of four screens and app/mock difference table. No per-slice owner walkthrough. Do not change classification, evidence provenance or stale/current policy.

## Architect ruling

Questions answered by `D-2026-10-16-w1-ux` in `.agent/architect-W1-ux-answers.md`. Its destination, vocabulary and honest-state boundaries govern this packet.
