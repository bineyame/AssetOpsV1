# Architect request: rule on the W5-03b pre-flight batch (39 items)

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Departure categories and register", the pre-flight and quiet-suite rules, lessons 13–14 and Token Efficiency;
- `.agent/W5-03-build-spec.md` (W5-03b units and all rulings), `.agent/W5-04-build-spec.md` (V1a) and `.agent/mock-departure-register.md`;
- the pre-flight list in branch `task/W5-03b-ev-health-scenarios`: run `MSYS_NO_PATHCONV=1 git show task/W5-03b-ev-health-scenarios:.agent/W5-03b-phase-handoff.md`.

The mock screens are `ev-health` and `ev-scenarios`.

1. Rule on every item with literal artifacts:
   - the gate (P-G-1..3): W5-02a core (`0033`) and W5-03a merge first;
   - the 18 head-pin tests moving to `0034`;
   - `evSiteMoneyRoutes.test.tsx`;
   - the EV rail fixture at `navigation-rail-fixtures.ps1:204`;
   - `expectV69Panels`;
   - the E5 consequence and tariff selection predicate;
   - item 34 (P-34-1..3): confirm that the generated EV producer is owned by W5-04 V1a, the clock-generic cutoff, and whether W5-03b tests the 422 `EV_TIME_INVALID`.
2. **EV Health Data sources panel (P-E4-1).** The same extra panel was ruled D3 on cold Health and removed in W5-F1 (register R22). Apply the same treatment to EV Health unless there is a real difference: remove it, and point the Foundation link at the existing EV Evidence sources panel. Give the literal change.
3. **Departures.** For the uncoded departures (ev-health card values, notes, links, tones, table rows; ev-scenarios "(placeholder)" subtitle, panel meta, empty body, heading, and the misdescribed R27), restore each to the mock or code it Dn with a register row. Correct R27.
4. Add a closure table mapping each P-ID to where it is closed. Amend `D-2026-10-22-w5-01-w5-03-buildspec`.

Write only `.agent/W5-03-build-spec.md`, `.agent/W5-04-build-spec.md` if item 34 changes it, `.agent/mock-departure-register.md` and `.ai/DECISIONS.md`. Do not commit. End your output with: the gate, item 34, every new departure with its code, and anything left open.
