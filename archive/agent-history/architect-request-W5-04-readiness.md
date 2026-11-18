# Architect request: W5-04 readiness refresh (26 points)

You are the AssetOps Architect. Read:
- .ai/ROLE_CONFIG.md, especially lesson 15 on caps
- tasks/W5-04-ev-work.md
- .agent/W5-04-build-spec.md
- .agent/W5-04-preflight-rulings.md (46 rulings)
- .agent/W5-03b-e5-rulings.md
- .agent/W5-03b-ui-preflight-rulings.md
- .agent/W5-02c-K4-preflight-rulings.md (K4 is unmerged; its branch is task/W5-02c-K4-cold-action, read with `git show task/W5-02c-K4-cold-action:<path>`)
- .agent/W5-02-build-spec.md (K2/K3 rulings)
- .agent/W5-02-04-mock-measurements.md
- .agent/mock-departure-register.md
- the v69 mock (ev-work, ev-work-incidents, ev-work-maintenance, ev-action)
- .agent/W5-04-readiness-questions.md

Main now includes W5-03a, K2, K3, E5 and E4/E6.

Rule on all 26 points. The builder decides nothing. Give exact names, literals, file ownership, migration steps, test files and fixture identities, and cite the mock for every point that affects a screen.

1. Point 1, the gate: either hold W5-04 until K5 merges, or allow V1a/V1b (backend: 0035, the intent store) to start now on a separate branch, as E5 did. State exactly which units may start and which must wait.
2. Amend rulings 13, 14, 15, 19, 22, 29, 32, 39 and 44, and confirm or reword 1-3, 5, 9-12, 17, 21, 33, 41 and 43.
3. Points 14-20: say whether EV generalises K4's DomainActionVerification and the cold-only seams, or adds EV branches. Give ownership and order relative to K4.
4. Points 23-24: register EV rows for the cold departures that carry over (R91-R94, R99, R101, the fold), starting after the register's last row.
5. Points 25-26, under lesson 15: replace the spec cap table with final caps sized from worst-case content, align it with cold's settled caps where the content is equivalent, and exempt every user-expanded state up front. State what happens if a remeasured state still exceeds its cap.

Write .agent/W5-04-readiness-rulings.md, numbered to match the points, and apply it to .agent/W5-04-build-spec.md and tasks/W5-04-ev-work.md. Do not touch product code. Do not commit.
