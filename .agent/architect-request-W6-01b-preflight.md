# Architect request: rule on the W6-01b pre-flight batch (B1–B3)

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Builder pre-flight and quiet-machine suites" and "Token Efficiency";
- the B1–B3 cards and §3.1 in `.agent/W6-01-build-spec.md`;
- the pre-flight list in branch `task/W6-01b-maintenance`: run `MSYS_NO_PATHCONV=1 git show task/W6-01b-maintenance:.agent/W6-01b-phase-handoff.md`.

The list has 41 items, 7 of them High. W6-01a code is on `task/W6-01a-global-incidents`, built but not yet merged. The mock screens are `maintenance` and `maintenance-preventive` in `frontend/mockups/v69/index.html`.

1. Rule on every item with literal artifacts: file lists, wire fields with their sources, copy, producers with clocks that actually work at real read time, guard edits, and the tests that break. In particular:
   - P-B1-1: the selection key against the fixture write clock;
   - P-B1-2: a `linked` fixture that can actually be produced;
   - P-B1-4: the fixture content;
   - P-B2-1/2: how the pages share parts with `GlobalIncidents.tsx`, and the client interface, with those files added to the owning card;
   - P-B3-1: null `state_counts`;
   - P-B3-2: the EstateEvidence files on B3.
2. Restore every unlabelled departure from the mock to the mock: card labels, subtitles, footers, the status strip, the Assets link. Where a value has no source, show an honest gap inside the mock's own structure, or label a true exception `MOCK DEVIATION`.
3. Carried Low from the W5-02/04 recheck: add a "preserve the K4a rail override" note to the B3 and C2 cards for `operatorRouteFrames.test.tsx`.
4. Add a closure table mapping each P-ID to where it is closed. Amend `D-2026-10-22-w6-01-buildspec` in `.ai/DECISIONS.md`.

Write only `.agent/W6-01-build-spec.md` and `.ai/DECISIONS.md`. Do not commit. End your output with: the High rulings in one line each, every new `MOCK DEVIATION`, and any item left open.
