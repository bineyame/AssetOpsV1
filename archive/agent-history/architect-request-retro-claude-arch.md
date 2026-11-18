# Architect request: retrospective review of Claude Architect rulings, with mock fidelity

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`, especially the new rule "Both Architects (Codex and Claude) check every screen-affecting spec, ruling and design against the v69 mock" and "Mockup drives the design";
- `.agent/owner-architect-mock-fidelity-2026-10-22.md`;
- the list "Codex retrospective queue" at the end of `.agent/coordinator-handoff.md`.

A Claude Architect made rulings between 08:52 and 12:39 on 2026-10-22, recorded in `.agent/W5-01-build-spec.md`, `.agent/W5-03-build-spec.md` and `.agent/W6-01-build-spec.md` and marked "Claude Architect ... Codex-reset exception".

1. **Mock fidelity first.** For every ruling that affects a screen, compare it with `frontend/mockups/v69/index.html` and `screen-manifest.json`. Rule each of these explicitly as KEEP (labelled `MOCK DEVIATION`, with reason and alternatives) or RESTORE TO MOCK (with literal replacement text: file list, guard registration, component, test, capture):
   - a. W5-01 C2 Context normalization heading `Match` -> `Status`.
   - b. W5-01 C2 Recovery curves: mock chart -> DataTable, because of `tools/checks/shell-overflow.ps1` rule 5. Consider rendering the chart in an allowed graphics module, or registering a new one. C2 is already built (`task/W5-01a-cold-selected-depth` at `2812d7aa`, under review), so give the exact rebuild delta if you restore it.
   - c. W5-01 C3 and W5-03 E4 new notice sentences not in the mock.
   - d. W5-03 E2 bars as plain divs, and E3 with no svg: compare them with the mock graphics.
   - e. Any other screen-affecting Claude ruling that departs from the mock (a W6-01 sweep: A2Q, CL3, A2Q11).
2. **Correctness.** Review the remaining Claude rulings for errors against the code and the technical design. Confirm each one, or give a literal correction.

Append the result as "Codex retrospective of Claude Architect rulings (2026-10-22)" to each affected spec, amending the decisions `D-2026-10-22-w5-01-w5-03-buildspec` and `D-2026-10-22-w6-01-buildspec` in `.ai/DECISIONS.md`. Write nothing else. Do not commit. End your output with a short list: each RESTORE, and which built or in-flight unit it changes.
