# Planner + Architect request: W2-F structural fix slice

You are the AssetOps Planner and Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W2-structural-audit.md`, which has 14 findings: 1 High, 13 Medium;
- `.agent/owner-walkthrough-after-w6-2026-10-20.md`;
- `.agent/post-W2-sequence.md`;
- the W2-03, W2-04, W2-06 and W2-07 build specs, with all their rulings;
- `.agent/W3-01-build-spec.md` q1–q6 and the commit-1 r1 rulings. These already change `ColdAssessmentViews.tsx`, `EvAssessmentViews.tsx` and `sourceProvenance.tsx` on the unmerged W3-01 branch.

Write:
1. `tasks/W2-F-structural-fixes.md`, a task packet.
2. `.agent/W2-F-build-spec.md`, an exact build contract. For EACH finding, give the root cause verified against merged code, then the literal fix: the data source, copy, component, state table and named test. The H1 inconsistency between cooling recovery "Full", "Not recorded" and "not assessed" needs ONE rule applied across all three screens. Keep every mock slot.
3. The slice's position. It must merge before the first W5 build and must not collide with W3-01's edits to the same view files. State the exact merge order relative to W3-01 and W4-01, and which lane runs it. Size the commits for one builder run each.

Add a README queue row and decision `D-2026-10-20-w2-f-structural`. Write nothing else. Do not commit.
