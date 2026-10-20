# Architect request: W3-01 commit-1 review findings (r1)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W3-01-build-spec.md`, rulings q1–q4;
- `.agent/W3-01-commit1-review.md`, which has M1, M2, M3.1, M3.2 and Lows;
- `.agent/W3-01-phase-handoff.md`, especially Lane A reading 7.

The code is on branch `task/W3-01-estate-claim-action-roots` at `1ceb1299`.

Rule each finding with exact replacements, so a Sonnet fixer decides nothing:
- M1: the label and field source for "Assessment basis" on cold (`ColdAssessmentViews.tsx:438`) and EV (`EvAssessmentViews.tsx:324`, `:673`), covering both the selected and the pending case. Give the literal copy, keeping the v69 mock wording.
- M2: an exhaustive table of every surface, mapping each to `source_provenance` (the pending alias) or `selected_source_provenance`. Cover the cold claim text and Site rows, EV `claim_rules[].source_class`, the EV badge and lines, and any others. Name the test assertions.
- M3.1: the withdrawn EV Finding whose session was dropped. Give the exact check change, so the detail read returns 200 with honest provenance, plus a test.
- M3.2: the cutoff filter for pending-job selection on historical reads, with the predicate and a test.
- The Lows: decide each one (fix, or accept as backlog), and give the exact test name where one is required.

Append the result as "Commit-1 review r1 rulings" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
