# Planner + Architect request: W6-01 Global work cases build spec

You are the AssetOps Planner and Architect.

Read first:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide", "Token Efficiency", "Build-Spec Readiness Gate For W5 And W6", and all 13 "W3/W4 lessons applied to W5 and W6". These are binding on this spec.
- `.agent/post-W2-sequence.md`: the slice rows, cross-cutting seams, and spec order (4).
- `frontend/mockups/v69/index.html` and its screen manifest, for the named screens.
- The merged code on `main` (W1-W4, W2-F all merged). The W4-01 work model is frozen. Copy state names, DTOs and refusal codes from merged code, never from prose.

The spec must be BUILD-READY with no open item, because implementer decisions are defects:
- Literal copy for every visible string, label, empty/refused/pending/historical state, link destination and ID source. Check each against the real guards and the registry checker (`tools/check-all`), and state the guard result.
- Mock measurements at 1440 and 390, including worst-case content length, with height caps.
- Every capture state and test variant names its producer: a fixture, scenario or command that you actually ran or verified exists in code, with a pinned clock and one clock per fixture.
- Consolidated unit cards: one per build unit. Each card holds its files (the shared files it may edit), steps, literals, tests and captures. Captures belong to the unit that builds the page. Each unit is sized for one builder run: 1-3 commits and 4 or fewer spec sections to read.
- No more than 6 units per slice, and no backend pipeline plus more than 2 new pages. If a slice exceeds this, split it into named sub-slices (for example W5-01a and W5-01b) with their own merge order.
- Units touching shared code or schema are marked "per-unit review".
- The Alembic revision number and its exact head dependency.

Slice (Lane B), from post-W2-sequence row W6-01 Global work cases: `incidents`, `maintenance`, `maintenance-preventive`, `wr-overview`, `wr-record`, `wr-history`, `oprecords`. Migration `0036`. It consumes the frozen W4-01 work model and `I-work-store`, `D-work-records`, `A-incident-index`, `A-maintenance-index`, `I-incident-read/ui` and `I-maintenance-read/ui`, with exact tenant/Site/Asset scope, authored events and correction history. It also reuses the W3-01/W3-03 global-root patterns (estate index scope, cursor and portfolio links) as merged. Seven screens is well over the size cap, so split into sub-slices with a merge order.

Write:
1. `tasks/W6-01-global-work-cases.md`, the task packet with its sub-slices.
2. `.agent/W6-01-build-spec.md`, the exact build contract.
3. A README queue row and decision `D-2026-10-22-w6-01-buildspec` in `.ai/DECISIONS.md`.

Write nothing else. Do not commit.
