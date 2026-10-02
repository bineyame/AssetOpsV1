# Re-review: Demo-Led Replan fix round 1 (`591cff2..11acc6d`)

Reviewer: a fresh Claude Reviewer instance, under the Codex-reset exception in
`.ai/ROLE_CONFIG.md`, which binds the Reviewer to Claude until 2026-10-03
21:23. I did not author the plan or the fixes. Scope: the fix-round diff and
what it touches.

## Verdict

**ACCEPT.** All of B1-B3 and N1-N8 are resolved. I found no contradiction
against `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`, no product-decision change and
no edit to owner text. Four small new notes are below; none blocks the merge,
and each is a one-line edit the Planner can make in passing.

## Checks I ran

| Check | Result |
| --- | --- |
| `tools/check-agent-workflow.ps1` | Passed (B1 is cleared) |
| `tools/check-architecture.ps1` | Passed |
| `wc -l` | T027 220/220 (591cff2: 221); T028 220/220; T029 153; T029B 111/120; T034 208; T034A 172 |
| `git diff 591cff2..11acc6d --stat` | Only `tasks/`, `.ai/DECISIONS.md` and the packet. No code, tool or `Docs/` change, so pytest, `tsc` and the frontend suites have nothing to verify and were not run |

## Findings

| # | Status | Evidence |
| --- | --- | --- |
| B1 | Resolved | `T025h:3` is `Status: planned`; the workflow check passes |
| B2 | Resolved | `T027` AC23 (line 122-124) removes `Operator home` and its frame, redirects `/` to `/sites`, and renders the rail as Sites only; phase 1 lists AC23. The anchors exist: `OperatorShellLayout.tsx:34`, `OperatorShellFrame.tsx`, and the `/` visit in `tools/layout-evidence.mjs:1270-1272` (the "Operator home" report label, which the packet correctly says needs relabelling). The scope line now reads "only `/` now redirects to it". T028, T029, T029B and T034A all say the landing comes from T027. See nit R2 for one leftover |
| B3 | Resolved | T027 is 220 and T028 is 220 by `wc -l`. The longest line left in either is a Proof table row (T027:188, 106 characters), and no lines were joined. Compared with `591cff2`, the cuts are rationale and duplicate prose only. The AC18 rationale and the "No sites are configured" reason moved to the packet. AC19 was condensed (see R3). T028 now has no headroom, as before |
| N1 | Resolved | T029 AC12 (lines 94-101) sets the default to the start of the superseded version, allows an earlier time, stores it beside the recorded time (AC6) and has the UI check cover the seeded windows. The form states which windows it reprices, so the live edit is not misleading. This agrees with AC2, AC5 and AC13 and does not change the recommendation. See R1 for a tie-break gap |
| N2 | Resolved | T034 AC19 says the seed creates the Action through the same Accept API and that the Action is not evidence. AC18 says the Recommendation tab of an accepted Finding shows the accepted state, links to its Action and offers no second Accept. The UI check says "(accepted state)". Both are testable and agree with T034A, which reuses "T034's seed as delivered" |
| N3 | Resolved | T029B AC4 gives the within-site order (Candidate Avoidable, Indeterminate, Necessary, then latest window); AC5 orders sites by claim level, then coverage, then name, and calls it an interim that T034A's versioned rule replaces. This is consistent with T034A AC4 and testable. See R4 for one gap |
| N4 | Resolved | T031 AC12 ends with the new priority-rule version weighting opportunity (T034A AC4) |
| N5 | Resolved | T029B title, Outcome, ownership test, Read-for-detail, Deliver bullet and AC7 are updated; the layout-evidence remnant check is dropped; README row 22 is updated. See R2 |
| N6 | Resolved | README line 135 says "Every point from 2 onward" |
| N7 | Resolved | `.ai/DECISIONS.md` adds "(Architect reading, planner guide section 5; the 'never hand-staged' wording above is Planner wording)". It is purely an attribution label. No owner or Architect quote was altered, and the diff touches nothing else |
| N8 | Resolved | T028:192, T029B:83 and T036:34 are rewrapped and T034:160 is shortened. The two remaining long lines are Proof table rows, which cannot wrap |

## New notes (all minor, non-blocking)

- **R1.** `tasks/T029-bounded-dispatch-financials.md:97-99`. The default
  effective time (start of the superseded version) makes the new version's
  effective time equal the old one's. AC2 does not say which version wins a
  tie. Suggested fix: "ties resolve to the later recorded time".
- **R2.** `tasks/README.md:17` still says "T029B (thin follow-on, Sites ranking
  and landing)". `.agent/plan-demo-led-replan-review-packet.md:256` says
  Portfolio takes the landing "from T029B". Both should say "landing from
  T027".
- **R3.** `tasks/T027-commit-ingestion-and-site-overview.md:108-109`. AC19 no
  longer says "private execution artifacts unavailable". The meaning is
  nearly intact, but it was a cut to acceptance wording. Suggested fix: restore
  "with Lab routes and private execution artifacts unavailable".
- **R4.** `tasks/T029B-sites-ranking-and-landing.md:76-79`. AC5 does not say
  where a site whose only open Finding is Necessary ranks. Suggested fix:
  treat it as having no open Finding, or add it after Indeterminate.

## Residual risk

None beyond the packet. The packet's carried-forward T027 items (the `Changes`
ban and layout evidence on `/`) are now in T027 AC21 and the rendered
paragraph.
