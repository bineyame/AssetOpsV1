# G-02 — V-01a mock-gap pilot

Status: done (owner accepted conditionally 2026-10-13; reviews ACCEPT; merged to main by coordinator)
USER_REVIEW_REQUIRED: true
Depends on: merged V-01a and reviewed G-01 catalogue/guard
Branch when activated: task/G-02-v01a-gap-pilot
Planner: Codex, 2026-10-12

## Visible outcome

Missing-capability states on `sites`, `foundation`, `readiness` and `sld` point to a traceable gap and remain honest across selection, reload and viewport changes. The pilot compares the merged V-01a app with the v6.9 manifest/mock at 1440 and 390 pixels.

## Acceptance

- Inventory each non-core/open panel portion and each distinct visible or omitted missing claim/interaction in the four merged surfaces, using the merged UI and V-01a round-3 ruling. The current registry seeds include `sites:2#a`, `foundation:2#b`, `readiness:2#a/#b`, `readiness:3#a/#b`, and `readiness:4#a/#b`; inspect SLD elements as well. The round-3 addendum is present in `.agent/architect-V-01a-round3-answers.md`; reconcile it against the reviewed merged V-01a UI before freezing the pilot map. V-01a's accepted visual gate is a reviewed merge prerequisite here, not a substitute for the `I-S1-03` technical dependency.
- Assign exactly one traceable gap ID per distinct claim, with shared IDs only for the same fact. Record exact panel/element, claim boundary, missing kind, source status, owner, target wave or `unplanned`, technical prerequisites and evidence/review trigger in `mock_gaps`; add `gap_ids` to non-core/open `w1_panel_mapping` portions and keyed ledger references. Preserve existing reviewed core paths, `core`, `state`, `technical_requires` and `panel_status: partial` where positive portions remain open.
- Map gateway signal strength and firmware separately as absent-source claims if still present; contact, registered/enabled configuration, commissioning records, policy documents, productive-use designation, uptime/completeness and accepted-evidence capability each retain their own typed boundary. Reuse exact S1/S2 nodes only where they prove the claim. An absent producer stays `data_source/absent`, unrankable and visibly owned; neither Lab truth nor a mock value becomes Site evidence.
- Annotate every visible missing-capability placement with the typed component/API; catalogue omitted content with `unplaced_reason`. Verify populated, missing and conditional branches, selection/date/revision changes and reload. A test proves at least one real rendered placement and exact `data-gap-id` membership; mutation checks reject unknown/unused IDs and untagged new copy.
- Compare app/mock desktop and narrow states per manifest ID. Record deliberate differences and source/API lineage. A sample conditional V-01a visual record leaves positive gaps and partial panel/screen status unchanged.
- Seed the inventory from the merged V-01a record: the Addendum table of visible missing states in `.agent/architect-V-01a-round3-answers.md`, the Round 3 conditional-acceptance rows in `.agent/V-01a-review-packet.md`, and the V-01a carries in `.ai/MILESTONE_REVIEW_BACKLOG.md` (C1 390 px Readiness table scroll, C2 readiness sentence versus gateway panel, C3 evidence screenshot name clash, C4 SLD `aria-controls`; gateway Site Evidence pointer; non-STALE gateway states proven only by response substitution). Carries are inputs to classify, not scope to fix here; the conditional V-01a acceptance leaves positive gaps and panel status unchanged.

## Review and checks

Independent Reviewer checks the graph, visible placements, 1440/390 pairs and source-to-claim boundaries. Run focused frontend tests/build, registry and ledger checkers, delivery fixtures and `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1`. Owner reviews the four visible missing-state treatments. G-02 closes the pilot mapping, not W1 non-core ranking or full mock completion.

## Review Outcome (recorded by coordinator, 2026-10-13)

- Reviews read (both): `.agent/G-02-review.md` (no blocking finding; F1 walkthrough/packet overstated SLD coverage, F2 `sld:2` reporting column uncatalogued); `.agent/G-02-fix-rereview.md` ACCEPT with R1 (walkthrough evidence count) fixed on the branch `5ba5d38`. Browser evidence 321/322 at 1440/390; the one failure is the pre-existing 390 px SLD parts-table caption. Screenshots kept at %LOCALAPPDATA%/AssetOps/evidence/g02.
- Architect: `.agent/architect-G-02-answers.md` (Q1, Q2 overruled and corrected in fix round 1; Q3-Q6 ratified; Lab entry labels accepted as developer affordances), decision `D-2026-10-13-g02-visible-placement-and-state-boundary`.
- Owner checkpoint: `.agent/owner-G-02-acceptance-2026-10-13.md` — accepted conditionally; nothing becomes Real. The 390 px SLD caption item was not separately ruled on and stays an open owner carry.
- Carries: `.ai/MILESTONE_REVIEW_BACKLOG.md` "G-02 carries (2026-10-13)".
