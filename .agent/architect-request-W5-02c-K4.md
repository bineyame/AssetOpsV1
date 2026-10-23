# Architect request: rule on the W5-02c K4a/K4b/K5 pre-flight refresh (13 questions + cap audit)

You are the AssetOps Architect. Read:
- .ai/ROLE_CONFIG.md, including the new lesson 15 on ruling caps once with the worst case in view
- tasks/W5-02-cold-work.md
- .agent/W5-02-build-spec.md (K4/K5 cards, "K4a, K4b and K5: Action detail", K3 rulings 1-25)
- .agent/W5-02b-K2-rulings.md
- .agent/W5-03b-ui-preflight-rulings.md (E4/E6 merges before K4 and shares files)
- .agent/W5-02-04-mock-measurements.md
- .agent/mock-departure-register.md
- the v69 mock (cold-action)
- .agent/W5-02c-K4-preflight-questions.md

Main includes K2 and K3.

Rule on all 13 questions with exact literals, elements, placement, file ownership, the worst-case fixture definition, and registry handling. Cite the mock for each.

Apply lesson 15. Give every K4 cap a final value sized from the worst-case content, including:
- Q6 (the Action strip with the long owner) and the overflow-wrap treatment of the H1 and owner;
- the new criteria and Related activity caps in ACTION_CAPS;
- an up-front exemption for any user-expanded state;
- what happens if a remeasure still exceeds a cap.

Also confirm the backlog-Low assignments in Q12, and the order and ownership against E4/E6 for the shared files: panelStructure.ts, the rail guard and fixtures, App.tsx and missing-claim-scan.mjs.

Write .agent/W5-02c-K4-preflight-rulings.md, numbered, and apply it to .agent/W5-02-build-spec.md. Add register rows from R99. Do not touch product code. Do not commit.
