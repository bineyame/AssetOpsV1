# W1-UX-02 — Site, Finding and money presentation

Status: implementation-ready. Branch `task/W1-UX-02`, after reviewed/merged W1-UX-01 and relevant W1 UI. Frontend only; owner walkthrough deferred to combined W1. Scope: registry IDs `sites`, `mini`, `sitefindings`, `finding`, `finding-evidence`, `finding-history`, `financials`, `assumptions`. Read the [umbrella inventory](W1-UX-mockup-fidelity.md), shared presentation packet, `frontend/mockups/v69/index.html#/<id>` and manifest entries, plus S5-01/S5-02/S4-01–05 packets for exact read boundaries.

## Visible result

Site directory: concise site card/list with answer “Which site needs attention?”, registered scope and evidence limit; no aggregate health score. Overview: one day headline, day timeline, scoped Finding row and bounded money card. Finding index/detail/history/evidence: conclusion → cause → consequence → next useful evidence/action; simple timeline/record trail; preserve exact revision, source, selected day and historical links. Financials/Assumptions: amount only when the current priced Finding read qualifies, show price/effective-time visual and explicit “why no current amount” otherwise. Default text must explain stale/pending/limited without enum. Technical IDs, model versions, provenance, raw reasons, cursor/watermarks move into `DigDeeper`, retaining direct exact links and labels. Use only figures returned by the selected read; no v69 mock numbers or inferred totals.

`SiteWindowOverview.tsx:510-566`, `OverviewFindingList.tsx:181-184`, `SiteFindingIndex.tsx:265-292`, `FindingDetail.tsx:306-445`, `SiteFindingEvidence.tsx:389-524`, `SiteFindingHistory.tsx:145-171`, `SiteFinancials.tsx:475-505`, `FindingConsequence.tsx:334`, `SitesIndex.tsx:108-132` are first change seams. Retain `MissingClaim` and registry gap tags. Keep S5-02 no parity claim for noncomparable rows, S4-04 proved-zero watermark, S4-05 source provenance and LR-01 withheld money states. Design the 390 px state with stacked cards and scrollable exact-detail tables; do not hide limits to fit.

## Phases and proof

| Phase | Deliverable | Focused proof |
| --- | --- | --- |
| 1 | Directory/Overview/Finding hierarchy, headlines and causal/timeline graphics | Existing S5/S4 UI tests plus populated, stale, pending, unassessed, proved-zero and historical selection; screenshot app/mock `sites`, `mini`, Finding family at 1440/390. |
| 2 | Financials/Assumptions card and all detail disclosures; close screen audit | Price/revision selection and money-withheld tests, current-only amount assertion, exact links/reload, vocabulary scan, 1440/390 `financials`/`assumptions` evidence. |

One full `npm.cmd test` and type check on final revision; focused tests per phase; registry checker and relevant guards; fresh independent review of all eight named screens and app/mock differences. No new backend read unless an exact *label* is missing; send that case to Architect before extending an API. No owner walkthrough for this slice.

## Architect questions

Recommend the headline “A possible fuel-cost exposure in this assessed period” for a bounded modelled amount, never “loss” or “savings”. Confirm the exact qualifier with the financial read owner before implementation.
