# Architect request: W3-01 q3 (Lane A compatibility commit blocked)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W3-01-build-spec.md`, including the q1 and q2 rulings;
- `.agent/W3-01-lane-a-adapter-contract.md`;
- `.agent/W3-01-pending-rulings.md` (q3: 3 questions plus 2 readings);
- `.agent/W3-01-phase-handoff.md`.

The code is on branch `task/W3-01-estate-claim-action-roots` at `1c49596e`.

This is the third round of questions on the same commit. Close it completely this time.

1. Answer Q1–Q3 with literal JSON, the key names, the exact evidence tables and predicates, and the named test changes. Q1 includes the fate of the existing `test_unassessable_source_has_unknown_status_and_limitation` assertion.
2. Confirm or replace both readings. One concerns the composition files injecting `PublicProvenance`, which are not listed in ruling 1; amend the ownership list if they are Lane A's.
3. Do a FULL implementer dry-read of Lane A's whole compatibility commit, call site by call site:
   - W1 Finding and consequence;
   - cold envelope, Finding detail and consequence;
   - EV envelope, session, Finding and money;
   - `site_overview`, `actions`, `finding_api`;
   - `sourceProvenance.tsx`.

   For each, state the exact before-to-after wire keys, the block source, the fallback shape, and the tests to change. Leave nothing for the builder to decide.

Append the result as "Run 3 rulings (q3)" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
