# Architect request: W2-03 follow-up rulings (fidelity compaction + chip tones)

You are the AssetOps Architect. Read `.ai/ROLE_CONFIG.md` (the sections "Mockup drives the design; implementers never decide" and "Token Efficiency"), `.agent/W2-03-build-spec.md` (if present) and `tasks/W2-03-cold-assessment.md`, the height table in `.agent/W2-03-review-packet.md` §"App-vs-mock panel heights", and the "Run 9 rulings" M5 section in `.agent/W2-04-build-spec.md`. The v69 mock (`frontend/mockups/v69/`) is authoritative. Owner rule: stay faithful to the mock and leave nothing for the implementer to decide.

W2-03 is merged, but these panels exceed the roughly 1.3x mock-height limit:
- `temperature` "Claim boundary": 225 vs 120 px (1.88x);
- `cold-finding` "Operational context" and "Recommended next step": 348 vs 253 px (1.38x);
- `cold-finding-excursion` "Recommended next step": 487 vs 333 px (1.46x), pair height.

The code is in `frontend/src/` (the cold assessment views and `w2-cold-assessment.css`).

For each panel, rule an exact compaction that brings it to 1.3x or below while keeping every spec-required fact reachable. State:
- what stays in the closed panel;
- what moves to a disclosure or details view, with the exact disclosure label;
- the exact copy and the CSS (selector and value);
- or, alternatively, an explicit accepted-exception reason.

Also restate the W2-03 part of the M5 chip-tone ruling as an implementer checklist: which component and badge, which class, and which file.

Write `.agent/W2-03-followup-spec.md` as decision `D-2026-10-19-w2-03-followup`. Include an implementer dry-read, a copy dry-read, the required tests, and 1440/390 recapture of the four affected routes with re-measured heights. Write nothing else. Do not commit.
