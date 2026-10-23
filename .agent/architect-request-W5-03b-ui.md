# Architect request: rule on the W5-03b E4/E6 UI pre-flight refresh (16 points)

You are the AssetOps Architect. Read these first:
- .ai/ROLE_CONFIG.md ("Mock fidelity", D1-D6, pre-flight)
- tasks/W5-03-ev-depth.md
- .agent/W5-03-build-spec.md (the E4/E6 cards and every W5-03b pre-flight ruling)
- .agent/W5-03b-e5-rulings.md
- .agent/W5-02-build-spec.md (K3 rulings; K3 is unmerged and shares files)
- .agent/W5-02-04-mock-measurements.md
- .agent/mock-departure-register.md
- the v69 mock (EV health and EV scenarios)
- .agent/W5-03b-ui-preflight-questions.md

Main now includes W5-03a, K2 and the E5 backend.

Rule on all 16 points with exact literals, placement, file ownership, caps, ledger tiers and fixture identities. Cite the mock for every point that affects the screen. The builder decides nothing.

Points 2, 3 and 4 change earlier rulings (P-E4-4, P-E4-1, and the panel-structure check), so correct those rulings in the spec. For point 1, confirm the gate. For point 4, state who edits panelStructure.ts and in what order relative to K3. Add a register row for every real departure, starting at R95. Remove the R60 D3 extra panel if it is still in the cards.

Write .agent/W5-03b-ui-preflight-rulings.md, numbered to match the questions, and apply the corrections to .agent/W5-03-build-spec.md. Do not touch product code. Do not commit.
