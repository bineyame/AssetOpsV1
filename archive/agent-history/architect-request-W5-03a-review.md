# Architect request: rule on the W5-03a review items

You are the AssetOps Architect. Read .ai/ROLE_CONFIG.md, in particular "Mock fidelity" and "Departure categories" (D1-D6). Then read .agent/W5-03-build-spec.md (W5-03a), .agent/W5-03a-review.md (the independent review, verdict REVISE), .agent/W5-03a-phase-handoff.md, and the v69 mock frontend/mockups/v69/index.html. The branch code is task/W5-03a-ev-selected-depth; read files from it with `git show task/W5-03a-ev-selected-depth:<path>`.

Rule on each item in the review's "Items for the Architect" list. The fix-round builder must not decide anything.
1. H4: the import-note placement. Correct spec:711 so it matches the mock (the panel description under the heading, index.html:595), unless you record a MOCK DEVIATION with a D-label and a register row.
2. M1: choose the single source for the observed peak, and resolve the contradiction between spec:691 and spec:106. State the test to add.
3. M2: for every builder literal listed in the review, give the exact text, tone and placement. Cite the mock wherever it has the item. Where the mock is silent, state the value, or say to remove the item.
4. L1: `selected_provenance_on`. Either name its DTO field and test, or remove it.
5. L5: decide whether the manual rule-5 non-vacuity proofs are accepted.
6. Confirm ownership of the off-list edits (v69-panel-contracts.json six tiers, ledger to_candidate null), and state the fix for their stale gap text.
7. Confirm or correct the builder interpretations: a null connector_id binds to the component; an unusable row ends the previous observation; SITE_METER means a meter fed directly by a bus.

Also confirm that H1-H3, M3 and the other Lows are to be fixed exactly as the review states, or amend them.

Write .agent/W5-03a-review-rulings.md, numbered, and apply the corrections to .agent/W5-03-build-spec.md. Add register rows to .agent/mock-departure-register.md only for real departures, starting at R86. Do not touch product code. Do not commit.
