# Architect request: W5-01a C3 builder questions (Q-C3-1..4)

You are the AssetOps Architect (Codex). Read `.ai/ROLE_CONFIG.md`: "Mockup drives the design", the new "Both Architects ... check every screen-affecting spec ... against the v69 mock" rule, and "Token Efficiency". Read the C3 card in `.agent/W5-01-build-spec.md`, including your retrospective, and the v69 `cold-health` screen in `frontend/mockups/v69/index.html` and `screen-manifest.json`.

The C3 builder (branch `task/W5-01a-cold-selected-depth`, commits `a374e2d8` and `ef933516`) built the client and the page body. It stopped on Q-C3-1..4 in "Run" of that branch's `.agent/W5-01a-phase-handoff.md`; read it with `MSYS_NO_PATHCONV=1 git show task/W5-01a-cold-selected-depth:.agent/W5-01a-phase-handoff.md`.

1. **Q-C3-1:** the S7 Data sources panel can't be rendered on its own. `SiteHealth.tsx` (not on C3's list) draws it together with the battery strip, the battery panel and a blue notice. Rule it from the mock's `cold-health` panel set, as an exact file list, export and render plan, and say whether the battery parts appear on the cold Health page.
2. **Q-C3-2:** the ledger heading says `Health`, but the frame's h1 is the Site name. Confirm or correct this against the mock, as was done for C2's Q-C2-6.
3. **Q-C3-3:** `coldDepth.test.tsx:454-459` asserts that the health link stays unmapped. Give the literal replacement assertion, and add the file to C3's list.
4. **Q-C3-4:** the Data sources link test needs `coldFoundation.test.tsx`. Rule whether to add it to the list, with the literal test.

Append the result as "C3 rulings (Q-C3-1..4)" to the C3 card, amending `D-2026-10-22-w5-01-w5-03-buildspec`. Label any departure from the mock `MOCK DEVIATION`. Write nothing else. Do not commit.
