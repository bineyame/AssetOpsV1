# Architect request: rule on the W6-01d pre-flight batch (C4 History)

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Builder pre-flight and quiet-machine suites", "W3/W4 lessons" (check literals against the real guards) and "Token Efficiency";
- the C4 card and all W6-01 rulings in `.agent/W6-01-build-spec.md`;
- the pre-flight list in branch `task/W6-01d-request-history`: run `MSYS_NO_PATHCONV=1 git show task/W6-01d-request-history:.agent/W6-01d-phase-handoff.md`.

There are 22 items, 6 of them blocking. W6-01b is on `task/W6-01b-maintenance` (built) and W6-01c on `task/W6-01c-request-overview` (planned); both merge first. The mock screen is `wr-history` in `frontend/mockups/v69/index.html`.

1. Rule on every item with literal artifacts:
   - the W6-01c parts C4 relies on;
   - the Overview and Record tests that break, added to C4's list;
   - a client-side pager that the guards allow;
   - whether the first revision row is shown;
   - one historical cutoff for X3 that shows older rows, reconciling the three in the spec;
   - unknown event kinds, including `OPEN_VERIFICATION`;
   - a browser check for a missing Created event;
   - the breadcrumb and column widths, the final ledger sentence, and the capture list.
2. Restore the mock: the Event cell details (assignee, reasons, comment text); the "Raised from INC-203", "Verification pending" and "Site visit started" rows; the time format (seconds, if writes need them, or the mock format with a tie rule); and the By column (a name, not an ID). Where a value has no source, show an honest gap inside the mock's own structure, or label a true exception `MOCK DEVIATION`.
3. Add a closure table mapping each P-ID to where it is closed. Amend `D-2026-10-22-w6-01-buildspec`.

Write only `.agent/W6-01-build-spec.md` and `.ai/DECISIONS.md`. Do not commit. End your output with: the key rulings in one line each, every new `MOCK DEVIATION`, and any item left open.
