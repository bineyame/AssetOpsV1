# Planner + Architect request: W5-01 Cold depth and W5-03 EV depth build specs

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

Slices (Lane A), from post-W2-sequence rows W5-01 and W5-03:
- W5-01 Cold depth: `cooling`, `cold-health`, `cold-scenarios`. Migration `0032`. A scenario has an authored basis and no observed-outcome status.
- W5-03 EV depth: `availability`, `energy`, `ev-health`, `ev-scenarios`. Migration `0034`. Availability and charger health need their own observed denominators; session count and configured schedule alone do not prove them.

W2 structural gate: the W2 structural audit (`.agent/W2-structural-audit.md`) found 14 findings. W2-F fixed them all and merged as 2df2a3da, with a re-audit that closed all 14 (`.agent/W2-F-review-packet.md`, `.agent/W2-F-final-review.md`). Confirm in one line whether this satisfies the gate for closing the W5 specs. Also rule on the one open W2-F Low: the refused cold Finding page has no Unknown strip, although the M13 table calls for one. Give the literal fix and the unit that carries it, or say no change.

Write:
1. `tasks/W5-01-cold-depth.md` and `tasks/W5-03-ev-depth.md`, task packets (split into sub-slices if needed).
2. `.agent/W5-01-build-spec.md` and `.agent/W5-03-build-spec.md`, the exact build contracts.
3. README queue rows and decision `D-2026-10-22-w5-01-w5-03-buildspec` in `.ai/DECISIONS.md`.

Write nothing else. Do not commit.
