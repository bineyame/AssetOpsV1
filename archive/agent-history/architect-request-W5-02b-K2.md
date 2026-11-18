# Architect request: W5-02b K2a/K2b review rulings, plus a lane question

You are the AssetOps Architect. Read .ai/ROLE_CONFIG.md, in particular "Mock fidelity" and the D1-D6 departure categories. Also read .agent/W5-02-build-spec.md (the K2a/K2b authority sections and the 2026-10-23 Site-screens pre-flight ruling), tasks/W5-02-cold-work.md, .agent/W5-02-04-mock-measurements.md, .agent/mock-departure-register.md and the v69 mock in frontend/mockups/v69/.

Inputs:
- .agent/W5-02b-K2-review.md: the independent review, verdict REVISE. Its "Items for the Architect" list has 19 items.
- .agent/W5-02b-questions.md: the builder's Q1-Q17.
- .agent/W5-02b-phase-handoff.md.
- The code is on branch task/W5-02b-cold-site-screens. Read it with `git show task/W5-02b-cold-site-screens:<path>`.

A. Rule on all 19 review items and on every builder question they cover. The fix builder must not decide anything. Give exact literals, placement, tone and fixture identities, and cite the mock wherever an item affects a screen. In particular:
- Item 1 / Q6: where the cold range control lives, given that no topbar range, Site-switch or picker slot exists in the app. Either rule the minimal faithful placement, or rule it a D1/D2 departure with a register row. Restate P-K2a-39 and the U2 assertions to match.
- Item 2 / F1: the Actions panel cap. Rule it on the basis that the H1 fix, wrapping at 1440, will make the rows taller.
- Item 6: the domain-work access hook. No product authentication exists yet, so rule whether this is future work (with a tracked item) or part of this slice.
- Items 7 and 19: correct the stale spec statements.

The reviewer's direct fixes, which are H1 (wrapping at 1440 and a cell-containment capture claim), H2 (the three unlabelled departures: fix them to match the mock), L1 (use DataTable stickyFirstColumn) and L2, are already being applied. Confirm them, or amend them.

B. Lane question. Lane 2 is idle until K2 merges. Can W5-03b's backend-only units (the 0034 migration and the E5 store and read methods, per .agent/W5-03-build-spec.md) start now on their own branch, given that K2/K3 touch no backend? Rule yes or no, and name exactly which units may start and which must still wait for K3a/K3b.

Write .agent/W5-02b-K2-rulings.md with numbered rulings. Apply the corrections to .agent/W5-02-build-spec.md, and to .agent/W5-03-build-spec.md if B changes the order. Add any register rows starting at R88. Do not touch product code. Do not commit.
