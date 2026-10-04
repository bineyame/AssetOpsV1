# T028 fix round 1 - Claude re-review

Reviewer: a fresh Claude `assetops-reviewer`, 2026-10-04. It is independent of
the implementers and of the Codex first review. This is a **Claude re-review
under the owner's re-review rule**: re-reviews go to a fresh Claude reviewer,
not to Codex. It does not record owner acceptance.

Reviewed: `af668a7..7368637` on `task/T028-dispatch-finding-and-evidence`
(`e39150b` is code, tests and the decision table; `7368637` is records). I
judged it against `.agent/T028-codex-review.md` (R1-R5 and what each asked
for), the task's acceptance criteria, the decision table,
`D-2026-10-04-analytic-readiness-scope-and-gap-impact` and
`D-2026-09-22-milestone-speed-over-purity`.

## Verdict

**ACCEPT, with findings carried.** R1-R5 are closed. Each closure is checked
in code, by the new regressions and by my own probes. Nothing here meets the
bar for a block in `D-2026-09-22`: there is no expensive-to-reverse defect, no
record that would mislead an Implementer, and no decision only the owner can
take that has to be made before merge.

**Escalation signal, plainly.** This was not a pure verification round. The
packet records two choices the Implementer made between legitimate treatments:
for R2, splitting the segment rather than capping it; for R4, classifying under
each alternative rather than always returning Indeterminate. My probes also
found a defect no reviewer had named, F1, in the same area as R2. Under
`.ai/ROLE_CONFIG.md` "Which Reviewer For Which Round", both of these signal that
the round should go back to Codex. My view: both choices are sound (reasons
below), and F1 is wrong text with correct numbers, so I would not spend Codex
quota on it. Under the standing owner rule, that call goes to the owner, not
the coordinator.

## R1-R5 closure

- **R1 evidence basis: closed.**
  - `_off_before`/`_off_after` now return the records that place each bound.
  - `_alternatives` returns the records it read.
  - `_digest(used, fuel)` covers both, plus the fuel basis (`dispatch.py` `_digest`, `_interval`).
  - `service.py:186` adds a payload-equality check. Any change in the conclusion therefore appends a revision, even if the digest somehow misses an input.
  - The SOC lookup in the policy alternative is added to `used` only when it changes the statement. That is safe because of the payload check.
  - The test reloads from a fresh `JsonAssessmentStore` and reruns with no new revision, which shows the payload survives a round trip.
  - A `dispatch-1` revision is kept and `dispatch-2` is appended to it (test `test_r1_a_model_version_change...`).
- **R2 commands between reports: closed for classification.**
  - `_observed_segments` (`dispatch.py:929`) cuts a segment at every effective start or end of a constraint record strictly inside it.
  - Each part keeps the two reports' measurements, so nothing is invented, and is evaluated with the policies effective at that part's start.
  - I probed an override that spans a report (01:05-01:40). It gives `01:00 C, 01:05 N, 01:15 N, 01:30 N, 01:40 C`, which is correct.
  - Records that start or end exactly at a report time take the existing point path, which is conservative.
  - Splitting rather than capping is the more accurate choice, matches "do not invent measurements", and leaves undisturbed segments unchanged. I agree with it.
  - The statement repair is incomplete: see F1.
- **R3 SOC headroom in 5b: closed.**
  - `dispatch.py:545` returns Indeterminate before counting battery support when SOC is at most reserve + 10.
  - The `assert` before it cannot fire: that branch needs `soc` usable and `reserve` set, because `missing` is empty and `pv_alone` is false.
  - The decision table's row 6 wording matches the code.
- **R4 equal-rank conflicts: closed.**
  - `_Evidence.effective` (`dispatch.py:194`) returns every top-rank record, and `_distinct` collapses identical content.
  - `_evaluate` keeps a classification only when every alternative agrees. That never settles a policy by message or gateway order, and it is the narrower assessment Codex allowed.
  - The 30/70 reserve case is Indeterminate, both records are in the basis, and readiness is Limited.
  - Conflicting stop policies are not quoted.
- **R5 generator gaps in readiness: closed.**
  - `declaration._generator_gaps` (`declaration.py:241`) adds a limiting `COVERAGE_GAP` row, and `readiness-3` is versioned.
  - Codex's AC1 repro now scores Limited, with the row named.
  - The frontend test asserts the rendered row is limiting and that the "no claim-limiting gaps" text is absent. That test supplies the readiness row as fixture data, but the frontend has no readiness logic to test beyond rendering it.
  - Host `test_prolonged_and_healthy_readiness...` still passes at HEAD (host 616), so owner-walk step 12 (KOBO-P Full) still holds.

## Findings

### F1 - P3, carry: the override alternative still states things that are not true in three reachable cases

Anchors:
- `backend/assetops_backend/analytics/dispatch.py:771-795` (`_alternatives`: `assessed`, `edge`, `parts`)
- `dispatch.py:956-973` (`_edge_allowance`)
- `dispatch.py:1028` (the statement is also copied into `claim_limits`)

What is wrong. Codex R2 blocked partly because the override alternative made a
false claim. The fix makes it true for observed segments, but my executed
probes (on the `world` fixture with 15-minute reports, running from 00:15 to
02:00 and stopped evidence at 02:10) show three cases where it is still false:

1. **A battery reserve override in the stop edge (02:02-02:08).** The statement
   says "the candidate's upper bound does not extend over that edge". The upper
   bound stays at 1.17 h, the same as with no override.
   - The cause: `_edge_allowance` only subtracts generator overrides whose
     control is `generator-stop-soc-threshold`, while `_edge_overrides` reports
     every override on both keys.
   - This case is reachable from shipped publication: `host/execution_adapter.py:857`
     maps `battery-reserve-state-of-charge` to the battery `override-command`.
2. **A generator override that covers only part of the edge (02:08-02:20).**
   The same sentence appears, but the bound is 1.13 h: the edge counts for
   8 of its 10 minutes. The number is right and the sentence overstates it.
3. **An override wholly inside an unobserved generator-state gap.** Records
   are dropped between 01:30 and 02:30, with an override from 01:40 to 02:20.
   The statement says it "is included in the constraint assessment at its
   effective time", but no segment there is assessed. The gap is Indeterminate,
   so the numbers are still right. This is exactly the sentence Codex called
   false.

Why carry rather than block:
- Every classification, duration bound and fuel figure in these cases is
  correct or conservative. Only the explanation text is wrong.
- It is user-visible (Alternatives tab, claim limits) but rare: it needs an
  override effective only inside a 5-15 minute edge or a gap.
- It is not expensive to reverse. The text is persisted per revision, and a
  model-version bump appends a corrected revision by design.

Fix:
- Choose the edge sentence from what `_edge_allowance` actually subtracted:
  the subtracted part of a generator stop-threshold override, versus "effective
  in the edge, which has no SOC to evaluate it against".
- Classify an override that overlaps only unobserved segments with the edge
  case, not the "included" case.
- Add one test per case.

The fix is small enough to make on this branch if the coordinator prefers.
Otherwise it goes to `.ai/MILESTONE_REVIEW_BACKLOG.md`.

### F2 - P3, carry (backlog, T028A): conflicting optional evidence leaves readiness Full with "no claim-limiting gaps"

Anchors:
- `backend/assetops_backend/analytics/declaration.py:198` (`_coverage_gaps` matches only coverage-row labels)
- `frontend/src/sites/CapabilityReadiness.tsx:124`

Executed probe: a second minimum-runtime policy record (60 versus 30 min) at
the same rank.
- The assessment names `Minimum runtime policy: conflicting records` and has
  0.5 h Indeterminate.
- `score_readiness` returns `FULL` with `missing_evidence: []`, so the screen
  would read "no claim-limiting gaps identified in assessed intervals".
- A conflicting pair of generator overrides behaves the same way.

The packet discloses this as "Left open". It has the same shape as R5, a Full
row while an assessed portion is Indeterminate. The difference is that a
conflict is not literally a coverage gap under the interim rule's wording, and
the decision keeps optional context distinct.

Why carry:
- Readiness is scored on read, so a later change costs nothing.
- The packet names the gap honestly.
- Whether a conflict in optional context lowers readiness is a gap-impact
  question that the decision gives to T028A.

Ask: the packet's open item is not yet in `.ai/MILESTONE_REVIEW_BACKLOG.md`.
The coordinator should add it under the T028A follow-up so it is not lost.

### F3 - P4, carry (records): the packet still asks the owner to answer closed decisions

Anchors: `.agent/T028-review-packet.md:59` and `:319`.

- The AC20 row was edited in this round but still ends "Open decisions 1 and 2".
- Owner-walk step 16 still says "Answer the two open decisions above".
- The section at line 143 says both decisions are closed by
  `D-2026-10-04-analytic-readiness-scope-and-gap-impact`.

This predates the round (it is present at `af668a7`) and is a one-line fix.
Fix it before the owner walk so the owner is not asked to re-decide something
already settled.

## Checks

Not re-run, per the brief. I accepted these as supplied at `7368637`: backend
1482, frontend 1099, host 616, `tsc --noEmit` clean, and both `tools/check-*.ps1`
pass. Neither the frontend suite nor the build was run by this reviewer.

Run by this reviewer:
- **The claimed regression proof.** I loaded the `af668a7`
  `assetops_backend/analytics` package in place of HEAD's and ran
  `backend/tests/test_t028_fix_round_1.py` against it: **13 failed, 1 passed**.
  The pass is `test_r4_identical_records_from_two_gateways_do_not_conflict`, as
  the packet says.
- **Stdin probes** with the existing test fixtures, for F1 (cases 1-3), F2, the
  override spanning a report, and the KOBO host readiness path (read only).

No repository files were changed apart from this review. The scratch copies
are in the session scratchpad.

## Not verified and residual risk

- **Layout evidence was not re-run.** The packet says no layout claim reads
  anything that changed. The worst case is one more list item in the readiness
  cell, so I accept the skip. The known profile-4 Lab residual is still carried.
- **The owner UI walk has not happened.** Step 14 (KOBO-R revisions) now also
  appends a `dispatch-2` revision to any `dispatch-1` lineage already stored in
  the owner's `var/assessments` on first read. That is intended, but the owner
  may see one more revision than the walk describes on a Site assessed before
  this round.
- **Split segments use both reports' measurements across the cut.** That is
  the same assumption the unsplit segment already made, so it adds no risk. A
  minimum-runtime expiry inside a segment still makes the whole segment
  Necessary, which is pre-existing and conservative.
- **Battery overrides with a control other than the reserve are compared
  against reserve overrides at the same rank** and could report a false
  conflict. No such control is published today (`execution_adapter.py:857`),
  so this is not a finding.
- Practitioner usefulness and the expert-feedback checkpoint are still
  outstanding, as Codex recorded.
