# Architect request: W3-03 closure round 4 (post-merge seam re-check)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W3-03-build-spec.md`, closures 1–3;
- `.agent/W3-03-seam-recheck.md`: 33 items (4 Blocker, 19 Should, 10 Nit), the 17 delivered items, and the proposed 6-run split with per-run reading indexes;
- `.agent/W3-03-mock-measurements.md`;
- the v69 `portfolio` mock;
- `.agent/post-W2-sequence.md` (ownership).

Close all 33 with exact artifacts verified against main.
- B3, the three-domain proof. Adopt or replace the reviewer's concrete path: window `[2026-10-06,2026-10-07)`, `power_estate` as the W1 producer, `mixed_replay` plus `two_ev_sites`, and `known_at` omitted for the CURRENT variants. Give the exact fixture, clock, assertions and decline path.
- B1 and B2. There is no full-scope selector to reuse. Name the exact new shared function(s), their owner (Lane A for existing estate files), and the sequential handoff order. Cover the new `portfolio` parser and cursor kind, plus the row fields in `scope.py`, `index.py` and `coverage.py`.
- B4. The Finding↔Action join is unreachable in any aligned window: Actions are selected by `created_at` within the window, and S6 Actions are created on 2026-11-01. Give an honest fixture path for the "Verified" and "Resolution withdrawn" rows, or rule the honest limitation, keeping the mock slot with its gap copy.

Adopt the 6-run split, or give your own, with a reading index per run. Strike the delivered items in a supersession index.

Append the result as "Review closure 4 (2026-10-21)" to `.agent/W3-03-build-spec.md`. Write nothing else. Do not commit.
