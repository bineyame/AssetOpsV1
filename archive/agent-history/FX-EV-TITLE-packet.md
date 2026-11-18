# FX-EV-TITLE packet (D-E5.9 / D-E5.10)

Change: EV action title literal "Investigate connector 2" -> "Investigate connector c1" in tools/w504_ev_work_cases.py:52 (the producer ACTION).

Also updated (every non-mockup occurrence found by repo grep):
- tools/w504_ev_work_walkthrough.py (docstring)
- backend/tests/test_w504_ev_intent_api.py (3 assertions)
- backend/tests/test_w504_ev_work_cases.py
- backend/tests/test_w504_ev_work_producer_postgres.py
- frontend/src/shell/__tests__/operatorRouteFrames.test.tsx (fixture + h1 assert)
- frontend/src/sites/__tests__/domainActionVerification.test.tsx (fixture + h1 assert)
- frontend/src/sites/__tests__/evWorkActions.test.tsx (link text + fixture)
- frontend/src/sites/__tests__/evWorkCases.test.tsx
- frontend/src/sites/__tests__/evWorkFixtures.ts

Mockups left unchanged: frontend/mockups/v69 and v70 (index.html, screens.js, portfolio.js, outcomes.js, screen-manifest.json, browser-review.json). No guard comparing against them was observed failing in the tests run; no guard was inspected exhaustively. No captures metadata matched.

Tests (worktree PYTHONPATH, *_test DB only, one file at a time):
- test_w504_ev_work_cases.py: 18 passed
- test_w504_ev_intent_api.py: 6 passed (assetops_test)
- test_w504_ev_work_producer_postgres.py: 4 passed (assetops_test)
- vitest: evWorkActions, evWorkCases, domainActionVerification, operatorRouteFrames: 153 passed
- Temporary node_modules junction removed before commit.
