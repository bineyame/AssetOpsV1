# Architect request: W4-03 PR-13 (the last two cap breaches) and the four readings (u9c)

Read:
- `.agent/W4-03-build-spec.md`, through u9b;
- `.agent/W4-03-pending-rulings.md`, PR-13, with the builder's options;
- the four readings in `git show task/W4-03-mini-decisions-work:.agent/W4-03-phase-handoff.md`;
- the v69 Scenarios and Incidents mocks, and their measured mock heights.

356 of 359 capture checks pass. The remaining failures are:
1. **The populated Scenarios panel:** 381 px against a 348 cap at 1440, and 436 against 391 at 390.
2. **The refused-overlay Incidents panel:** 472 px against a 460 cap at 390.

For each, choose exactly one, with literals and a test:
- the exact layout or content fix that keeps faithfulness to the mock;
- a cap amendment, justified by the mock's own measured height for that state.

Confirm or replace each of the four readings, including the added "Alternatives unavailable" label on the 503 panel. Say whether that label departs from the mock.

Append the result as "Final capture rulings (u9c)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
