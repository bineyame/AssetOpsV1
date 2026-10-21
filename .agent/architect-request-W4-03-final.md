# Architect request: W4-03 final review items needing a ruling (uF)

Read:
- `.agent/W4-03-build-spec.md`, all of it;
- `.agent/W4-03-final-review.md`, all of it;
- the v69 Alternatives, Opportunity and Site Work mocks.

Code: `f06e9bab` on `task/W4-03-mini-decisions-work`. A fixer is applying the clear fixes in parallel: H1–H3, M2, M3 (to closure 1's 2000), M4, M7 and the hygiene Lows.

Rule these with literals and tests:
- **M1.** The Alternatives DB-time capture is a 404 "decision not found", which PR-12.4 does not allow. Give the exact capture path or fixture change that yields the allowed state.
- **M5.** The scenario-link Work context is neither captured nor recorded as unproved. Give the capture state and its producer, or the honest-limitation wording for the packet.
- **M6.** Alternatives shows a Site tab row, inherited from the W1 shell, that the mock lacks. Remove it for this page, or keep it with a recorded departure? Give the exact rule.
- **The unruled builder reading behind M3,** and any other Low the review says needs a ruling, including the PR-1 RESOLVED marker.

Also confirm that the clear fixes listed above match the spec. If any should differ, say so.

Append the result as "Final review rulings (uF)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
