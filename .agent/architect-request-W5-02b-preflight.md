# Architect request: rule on the W5-02 Site-screens pre-flight batch (47 items)

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Departure categories and register", the pre-flight and quiet-suite rules, lessons 13–14 and Token Efficiency;
- `.agent/W5-02-build-spec.md` (K2a–K5 and all rulings) and `.agent/mock-departure-register.md`;
- the pre-flight list in branch `task/W5-02b-cold-site-screens`: run `MSYS_NO_PATHCONV=1 git show task/W5-02b-cold-site-screens:.agent/W5-02b-phase-handoff.md`.

The mock screens are `cold-work`, `cold-work-incidents`, `cold-work-maintenance` and `cold-action`.

1. **Gates (P-G-1..3).** Restate the order:
   - the core (on `task/W5-02a-cold-action-root`, now in its full suite) merges;
   - W5-03a E2/E3;
   - W6-01e (built, merging soon) merges before K4a, so reverse the K4a/E2 rail-preservation direction accordingly.
2. **Missing producers.** Rule on the maintenance request link, which is always null on the wire; the capture tooling (`w502-cold-work-evidence.mjs`); asset type, which only exists as the composite `GEN-CR-01 · GENERATOR`; and the honoured Finding revision link, since the cold Finding frame ignores `revision_id`. Give literal wire fields, files and tests.
3. **Conflicts.**
   - The rail guard requires the exact `<NavRail …/>` tag, which breaks the K4a override. Give the guard edit.
   - Update the stale "before W6" Manage wording.
   - Say whether EV moves off W1 now or at V2.
   - Give the route for a W1 Action on a cold Site.
4. **Departures.** For the 7 uncoded departures ("in this example" dropped, `Finding {id8}` in place of Finding codes, the interim Sites rail state, and the rest), restore each to the mock or code it Dn with a register row. Fix the owning units in R01/R02.
5. **Sub-slices.** Confirm the proposed sub-slices (K2a+K2b, K3a+K3b, K4a+K4b+K5), or change them.
6. Add a closure table mapping each P-ID to where it is closed. Amend `D-2026-10-22-w5-02-w5-04-buildspec`.

Write only `.agent/W5-02-build-spec.md`, `tasks/W5-02-cold-work.md` if needed, `.agent/mock-departure-register.md` and `.ai/DECISIONS.md`. Do not commit. End your output with: the sub-slices, every new departure with its code, and anything left open.
