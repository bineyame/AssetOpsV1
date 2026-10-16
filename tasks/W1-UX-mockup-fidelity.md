# W1-UX — W1 product presentation and v69 fidelity

Status: implementation-ready. Branch per slice `task/W1-UX-01` through `task/W1-UX-05`; this planning branch is `plan/W1-ux-pass`. Frontend only unless an exact backend label is absent; then stop and ask Architect for a bounded read contract. Owner does **one combined W1 walkthrough after all slices**; each slice may merge after fresh independent review under `.agent/owner-walkthrough-policy-2026-10-16.md`. Coordinator commits this plan. No screen or panel promotion follows from copy/layout alone.

## Authority and boundary

Owner words: `.agent/owner-LR01-S501-acceptance-2026-10-15.md`, `owner-S404-S601b-acceptance-2026-10-16.md`, `owner-S405b-acceptance-2026-10-16.md`, `owner-S302b-acceptance-2026-10-16.md`, `owner-T028-presentation-direction-2026-10-04.md` (all in `.agent/`); backlog `.ai/MILESTONE_REVIEW_BACKLOG.md:2254`. Registry `delivery_plan.owner_inputs.W1.approved_manifest_ids` is the exhaustive scope: all delivered/partial product screens plus pending S6-03, S6-02b, S7-01b; `lab` is excluded. Use `frontend/mockups/v69/index.html` and `screen-manifest.json` for the named screen's hierarchy, story, and interaction; illustrative mock values never become live data. Source contracts and `MissingClaim` placements remain authoritative. The mock's question for each screen should become its visible lead, answered only to the strength of the read.

## Gap inventory, app versus v69

Each row names the current component seam; `pending` means inspect the merged UI packet before implementation. The mock reference for every row is `index.html#/<id>` and the matching `screen-manifest.json` entry. Layout work includes hierarchy/spacing at 1440 and 390 px; “detail” names material to move under the shared disclosure or existing Analysis tab, retaining exact links.

| Screen ID | App seam and short gap against mock |
| --- | --- |
| `sites` | `frontend/src/sites/SitesIndex.tsx:108-132`: inventory leads with table/state; use “Which site needs attention?” and concise site condition cards; exact IDs/registration detail. No estate health inference. |
| `mini` | `frontend/src/sites/SiteWindowOverview.tsx:209-316,510-597`: fragmented day/objective/money panels; lead with bounded operating answer, visual day timeline and one Finding consequence; status reasons/selection IDs to detail. |
| `foundation` | `frontend/src/sites/StoredFoundationViews.tsx:367-426`: configured topology and obligation labels read like a record; lead with “What is configured?” and a visual equipment summary; revision and mapping references to detail. |
| `readiness` | `frontend/src/sites/ReadinessOverview.tsx:264,512`: configuration and gateway facts compete; lead with “What needs connecting or confirming?” and a source/next-step graphic; raw status basis to detail. Preserve commissioning missing claim. |
| `sld` | `frontend/src/sites/StoredFoundationViews.tsx:494-675`: diagram plus part table; lead with connection/reporting story, visible missing links and clear legend; exact part references to detail. |
| `evidence` | `frontend/src/sites/LedgerSiteEvidence.tsx:377-502,649-737`: source and delivery tables dominate; lead with “What can we rely on?” and coverage/source timeline; receipt/digest details to disclosure. |
| `evidence-analysis` | `frontend/src/sites/EvidenceClaimLimit.tsx:300,509-549,667-728`: selected limit is present but dense; headline which conclusion is supported, show covered/missing span visual; rule/version/IDs remain detail. |
| `dispatch` | `frontend/src/sites/PerformanceDispatch.tsx:291-317,399-416`: block table and assessment vocabulary; lead with why generator operated and selected-block strip; model version/reasons to detail. |
| `analysis` | `frontend/src/sites/assessmentAnalysis.tsx:242-257`: method/revision prose leads; show measurement-to-conclusion sequence and selected limitation; method/version/record count to detail. |
| `finding` | `frontend/src/sites/FindingDetail.tsx:306-445`: many record sections; lead with defensible conclusion and what could change it, causal strip; alternative codes and revisions to detail. |
| `finding-evidence` | `frontend/src/sites/SiteFindingEvidence.tsx:270-331,389-524`: lineage/table first; lead with “Which records support this conclusion?” and visual record trail; IDs/digests to detail. |
| `finding-history` | `frontend/src/sites/SiteFindingHistory.tsx:145-171`: selected revision and history read; lead with “What changed, and when?” as timeline; revision IDs and cutoff to detail. |
| `sitefindings` | `frontend/src/sites/SiteFindingIndex.tsx:134-178,265-292`: status and basis dominate; lead with scoped Findings and consequence/next action, ranked visual rows; cursor/status reasons to detail. Current zero only with watermark. |
| `financials` | `frontend/src/sites/SiteFinancials.tsx:475-505` and `FindingConsequence.tsx:334`: price/money separated; lead with bounded consequence and basis/limit visual; source/model versions to detail. No amount without current priced read. |
| `assumptions` | `frontend/src/sites/SiteFinancials.tsx:259-405`: schedule/history reads as revision list; lead with price in use and effective-time strip; version/actor/reference to detail. |
| `recommendation` | `frontend/src/sites/SiteRecommendation.tsx:145-203,343-416`: trial and live-computation wording; lead with proposed action, why and success measure; input IDs/live state to detail. |
| `changes` | `frontend/src/sites/SiteFoundationChange.tsx:108-182`: application and Foundation versions foregrounded; lead with what changed and observed effect/unknown; event and version IDs to detail. Await S6-02b effect UI. |
| `action-overview` | `frontend/src/sites/SiteAction.tsx:290-367`: state/origin records; lead with intervention and outcome state; rule and source references to detail. |
| `action-execution` | `frontend/src/sites/SiteAction.tsx:451-537`: “Application”/technical control labels; lead with work done and pending next step; exact event/actor data to detail. |
| `action-history` | `frontend/src/sites/SiteAction.tsx:537-580`: activity log; make chronological change story; event IDs and cutoffs to detail. |
| `action-plan` | Pending `tasks/S6-02b-verification-ui.md` Plan route; compare after merge to mock goal/windows/guardrails layout; exact plan/revision IDs to detail. |
| `action-evidence` | Pending S6-02b Evidence route; show baseline-versus-later coverage/limits visually; slot/record IDs to detail. |
| `verification` | Pending S6-02b Verification route; headline measured outcome and trade-offs, with paired period visual; thresholds/typed reasons to detail. |
| `sitework` | Pending `tasks/S6-03-site-work-list.md` Site Work route; prioritize active work and next step over table plumbing; cursor/watermark to detail. Zero only after assessed window. |
| `health` | Pending `tasks/S7-01b-health-ui.md` Site Health route; lead with which source needs attention and contact/fact-age visual; diagnostic IDs to detail. Source contact is not equipment condition. |
| `asset` | Pending S7-01b battery route; lead with “Condition cannot yet be judged” and missing-input diagram; asset/binding IDs to detail. Never imply remaining life/warranty. |

## Slice order and common acceptance

1. [W1-UX-01 shared presentation](W1-UX-01-shared-presentation.md): vocabulary, disclosure, headline/visual pattern and scan. Required before screen work.
2. [W1-UX-02 Site and money](W1-UX-02-site-money.md): `sites`, `mini`, Finding family, `financials`, `assumptions`.
3. [W1-UX-03 evidence and performance](W1-UX-03-evidence-performance.md): `evidence`, `evidence-analysis`, `dispatch`, `analysis`.
4. [W1-UX-04 actions and work](W1-UX-04-actions-work.md): `recommendation`, `changes`, Action family, `verification`, `sitework`; starts after S6-02b/S6-03 merge.
5. [W1-UX-05 configuration and health](W1-UX-05-foundation-health.md): `foundation`, `readiness`, `sld`, `health`, `asset`; starts after S7-01b merge.

Each packet has at most two phases, focused tests, one full `npm.cmd test` on final revision, 1440/390 served app versus named mock screenshots and recorded differences, and a fresh reviewer independent of implementation. Keep read/selector/URL/lineage tests and fail-closed assertions. No new empty/current/positive state without proof from the read. Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs` and relevant `tools/check-all.ps1` guards. Treat unavailable/dirty/withdrawn and the mock's unsupported values as explicit limited states. No per-slice owner walkthrough.

## One combined W1 owner walkthrough

Use an ordered list of existing private walkthrough tools because their guarded DBs, state transitions and ports differ; do not blend authored fixtures into a synthetic live Site. Coordinator prepares and serves one case at a time with the tool's private DB/work prefix, records exact URL and dataset provenance, and drops it after evidence capture: `tools/s5_overview_walkthrough.py` (Overview, Finding, money), `tools/s404_finding_index_walkthrough.py`, `tools/s402b_fuel_cost_walkthrough.py` plus `tools/s402a_assumptions_walkthrough.py`, `tools/s302_claim_limit_walkthrough.py` plus `tools/s3_dispatch_walkthrough.py`, `tools/s601b_action_walkthrough.py`, then the merged S6-02b, S6-03 and S7-01b walkthrough tools named in their task packets. Add `tools/s2_demo_walkthrough.py` for accepted/rejected Evidence and the S1 owner fixture for Foundation/Readiness/SLD. An index page/script may print this ordered URL list, but it must not mutate datasets or claim a single common lineage. Capture one supported, one limited/pending, one stale/withdrawn and one proved-zero path where their read supports them; 1440 and 390 screenshots, keyboard disclosure, exact links/reload, no cross-case numeric comparisons. Owner walks the complete W1 journey once and records acceptance; W1 completes only then.

## Architect questions

1. Recommend a closed inline “How this was worked out” disclosure on every default screen, with existing Analysis tab for long evidence trails. This satisfies the owner's deeper-analysis option without inventing a route or fragmenting selected state. Architect should settle whether a separate tab is mandatory for the small screens.
2. Recommend retaining approved domain words “Finding”, “Action”, “Evidence”, “Site”, “Verification” when explained by nearby plain text. Ban implementation states and IDs from default prose, while exact user/source references remain inside detail or labelled links. Architect should approve the vocabulary exceptions before W1-UX-01 implementation.
