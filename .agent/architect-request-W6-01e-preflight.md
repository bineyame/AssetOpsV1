# Architect request: rule on the W6-01e pre-flight batch (E1–E2)

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Builder pre-flight and quiet-machine suites", lesson 14 and "Token Efficiency";
- the E1/E2 cards and all W6-01 rulings in `.agent/W6-01-build-spec.md`;
- the pre-flight list in branch `task/W6-01e-operational-records`: run `MSYS_NO_PATHCONV=1 git show task/W6-01e-operational-records:.agent/W6-01e-phase-handoff.md`.

There are 23 items, 10 of them blocking. W6-01c (built and accepted, on `task/W6-01c-request-overview`) and W6-01d (planned) merge first. The mock screen is `oprecords` in `frontend/mockups/v69/index.html`.

1. Rule on every item with literal artifacts:
   - the merge base;
   - the selector signature;
   - the `operational` fixture recipe and capture plan, with clocks that work at real read time;
   - `kind` in the cursor, and which record version the filter reads;
   - the record-to-case link rule (incident window, cutoff);
   - shared page parts carrying `kind`, with the files added to E2;
   - the C3 record-page link text;
   - K4a preservation, given that K4a is not on main yet: state the rule for whichever of them merges second.
2. Restore the mock: kind chips stay buttons, plus the card notes and tone, the table sub-line, the "How records are used" copy and the table cells. Where the mock's manual-reading form cannot be supported, keep its structure as an honest unavailable form or label a `MOCK DEVIATION` with reason and alternatives.
3. Add a closure table mapping each P-ID to where it is closed. Amend `D-2026-10-22-w6-01-buildspec`.

Write only `.agent/W6-01-build-spec.md` and `.ai/DECISIONS.md`. Do not commit. End your output with: the key rulings in one line each, every new `MOCK DEVIATION`, and any item left open.
