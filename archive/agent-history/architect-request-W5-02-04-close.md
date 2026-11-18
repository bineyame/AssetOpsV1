# Architect request: close the W5-02/W5-04 readiness review

You are the AssetOps Architect and Planner (Codex). Read `.agent/W5-02-04-readiness-review.md`. It found 45 numbered gaps, challenged deviations and unlabelled departures from the mock. Also read `.ai/ROLE_CONFIG.md` (the readiness gate, W3/W4 lessons, both mock-fidelity rules, Token Efficiency), `.agent/W5-02-build-spec.md`, `.agent/W5-04-build-spec.md` and the v69 screens they own.

1. Close every numbered gap with literal artifacts in the unit cards: file lists, wire fields with their sources, copy, producers and clocks, guard registrations, broken-test edits, and the merge order with W6-01 A2/B2 for `WORK_CONTEXT_NOTICE` and its missing-claim exemption. Split K1, and any other unit too big for one builder run, so that no unit exceeds what one builder can finish.
2. Rule on each challenged deviation, M1, M3/E2, M4/E4 and E3. Prefer RESTORE TO MOCK. Where you KEEP one, label it `MOCK DEVIATION` with the replacement literal, the reason and the alternatives considered. Fix the ledger row for M4/E4.
3. Fix the unlabelled departures by restoring them to the mock: the Actions empty text, the request title in Related activity, the EV criterion wording, the Finding code, and the Open site button and subtitle. Where a value has no source, show an honest gap inside the mock's own structure.
4. Add a closure table mapping each gap number to where it is closed. Amend `D-2026-10-22-w5-02-w5-04-buildspec`.

Write only the two specs, the two task files if their scope changes, `tasks/README.md` if needed, and `.ai/DECISIONS.md`. Do not commit. End your output with:
- the new unit list, in order;
- every remaining `MOCK DEVIATION`;
- any gap you could not close, and why.
