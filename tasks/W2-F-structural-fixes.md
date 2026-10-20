# W2-F — W2 structural corrections

Status: planned. Decision: `D-2026-10-20-w2-f-structural`. Build contract: [W2-F build spec](../.agent/W2-F-build-spec.md). Source audit: `.agent/W2-structural-audit.md` (H1, M2–M14). `USER_REVIEW_REQUIRED: false`; independent slice review and the structural re-audit gate merge and W5 readiness. The owner's complete walkthrough remains after W6.

## Outcome and scope

Correct the 14 audited structural defects across the existing W2 cold and EV Site screens. A selected cold recovery that was not recorded cannot be called Full; EV/cold rows, labels, strips, links, counts and unavailable slots must describe the exact selected data. Preserve the v6.9 panel set and order on all 22 screens, the existing selected-window and provenance boundaries, and the mock's intentionally unavailable destinations. This is a correction of existing W2 reads and presentation, not W5 depth or a new observed claim.

## Placement and ownership

Lane A builds this slice on `task/W2-F-structural` from main **after reviewed W4-01 merges and then reviewed W3-01 merges**. W3-01's reviewed commit-1 provenance range reaches main through W4-01 first and W3-01 incorporates it; W2-F consumes the merged W3 public-read and frontend compatibility changes. Do not edit `ColdAssessmentViews.tsx`, `EvAssessmentViews.tsx` or `sourceProvenance.tsx` while W3-01's commit-1 handoff or final branch is open. W2-F merges before the first W5-01 or W5-03 build, and gates W5-02/04. W3-02, W4-02/03, W3-03 and independent W6 work may proceed on their own disjoint paths; Lane A serializes its shared-file edits. This slice has no migration or new route.

## Build units

1. Cold truth: H1, M4, M6, M7 and M13; selected capability rule, copy and cross-screen proof. One builder run.
2. Cold frame and counts: M3 and cold M5/M10; refused strips/tiles/footer, table count and identifiable records. One builder run.
3. EV configuration and overview: M2, M8, M9, M14 and EV M10; readiness, diagram, status and links. One builder run.
4. EV evidence, financials and Finding: M5, M10–M13; missing reasons, row count, Scenarios slot and Finding strip. One builder run.
5. Final integration: focused and same-revision checks, 1440/390 app/mock captures for all affected states, independent review packet and re-audit. One builder run; no new feature behavior.

The build spec assigns a source, literal UI rule, state table and named tests to each finding. A builder may refine mechanics but may not choose a different claim, mock slot or merge order.

## Acceptance

- H1 reproduces the recorded-normal fixture as Limited cooling recovery and None product exposure, with explicit missing basis; the overview, Backup and Evidence use one recovery rule. No Full row contains a missing basis or a conflicting unrecorded conclusion.
- All 13 Medium findings close under the spec's named tests. Every affected state retains its mock slot, including refused cold strip/tiles and unavailable EV Scenarios.
- Existing selected IDs, cutoff, source classification/digest, cursor fence and exact links are unchanged except for explicitly corrected presentation. No invented commissioning, recovery, stock, diagnostics, value or lifecycle data enters a read.
- Focused backend/frontend tests, typecheck/build, architecture/workflow/navigation guards, registry checker and one same-revision full backend suite on a private `*_test` Postgres DB pass. Capture 1440/390 app/mock pairs for stocked, no-selection and refused/pending paths as applicable; reviewer independently rechecks the 14 findings.
