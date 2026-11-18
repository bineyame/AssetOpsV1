# Architect request: W4-03 closure round 4 (post-merge seam re-check)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W4-03-build-spec.md`, closures 1–3;
- `.agent/W4-03-seam-recheck.md`: 35 items (5 Blocker, 21 Should, 9 Nit), the delivered-items list, and the proposed 12-unit split;
- `.agent/W4-03-mock-measurements.md`;
- the v69 mocks: `frontend/mockups/v69/screens.js`, especially around lines 940–980 for `opportunity-finding` and `alternatives`.

Close all 35 with exact artifacts verified against main.
- B1: the fixture Site. W4-02's positive data is on MG-W402-001, while the W1 dispatch Findings and the W4-01 cases are on KOBO-001. Rule one honest fixture path covering both, and name the Sites.
- B2: give the exact way a dev or test app injects the W4-01 work principal for the walkthrough and fixture.
- B3: add `mini_opportunity` to the exact domain exclusion lists in `postgres_finding_store.py:112-115` and `postgres_evidence_ledger.py:810-818`, with tests.
- B4: correct the Q24 navigation literal against the live tabs now on main. Incidents and Maintenance are live, and EV Scenarios does not exist.
- B5: closure 2 restored six context tabs on Opportunity, but this re-check reads the mock (`screens.js:948`) as Overview only. Re-read the mock yourself and state exactly which tabs v69 renders on `opportunity-finding` and on `alternatives`, citing the lines, then rule the tab set. The mock is the authority.

Adopt the 12-unit split, or give your own, each sized for one builder run with a "read only these sections" index. Strike the delivered items in a supersession index.

Append the result as "Review closure 4 (2026-10-21)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
