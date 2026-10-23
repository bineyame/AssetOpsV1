# Architect request: W5-02b K3 review rulings (FINAL, no further loop)

You are the AssetOps Architect. Read:
- .ai/ROLE_CONFIG.md ("Mock fidelity", D1-D6)
- .agent/W5-02-build-spec.md (the K3 cards, K3 rulings 1-16, spec :78)
- .agent/W5-02b-K2-rulings.md (rulings 2 and 24)
- .agent/W5-02b-K3-review.md (REVISE: M1-M3, L1-L5, Architect items 1-7 with the reviewer's recommendations)
- .agent/W5-02b-K3-handoff.md
- the v69 mock (cold-work-incidents, cold-work-maintenance)

The code is on task/W5-02b-K3-cold-cases. Read it with `git show task/W5-02b-K3-cold-cases:<path>`.

Rule on Architect items 1-6 with exact values: the caps at each width, the all-open state definition and its caps, the CURRENT capture method, the ID-wrapping CSS behaviour, the 390 Incidents scroller scoping, and the WR completion in the producer, including its effect on K2/K4 evidence. Cite the mock for each. Accept the reviewer's recommendations or replace them.

Make the rulings final. State every cap so that one recapture closes it. If a remeasured state can still exceed a cap, state now what happens: an exemption, or a specific cap.

Also confirm that M1-M3 and L1-L5 are fixed as the review states, or amend them. Item 7 is information only; route it to the copy pass.

Append the rulings, numbered 17 onward, to the K3 rulings in .agent/W5-02-build-spec.md. Add register rows from R96 if needed (R95 may be taken by a parallel request; check the register's last row first). Do not touch product code. Do not commit.
