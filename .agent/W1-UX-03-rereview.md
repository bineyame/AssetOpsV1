# W1-UX-03 re-review: fix round 1

Reviewer: fresh, independent Claude reviewer. I did not author the slice or the fix round.
Revision reviewed: `6db70ffd` (detached worktree `AssetOpsV1-review5`), diff `git diff e55d075a..6db70ffd`.
Inputs: `.agent/W1-UX-03-review.md`, "Fix round 1" in `.agent/W1-UX-03-review-packet.md`, `.agent/architect-W1-ux-disclosure-answers.md`.

## Verdict: ACCEPT

F1 (High) is closed, and the Lows are fixed or recorded honestly. No new High or Medium finding. Two Low notes follow and neither blocks.

## F1: closed

- **The change.** `PerformanceDispatch.tsx:286-307` derives `selectedIsCurrent = inWindow !== null`, so a version counts as current only when it is in `read.intervals`.
  - The Analysis state line gets `storedNotCurrent` when a selection exists and is not in the current set. It then uses `currentnessWords("HISTORICAL")` (tone `neutral`) with the sentence "This is a stored version for <day> ... not the current result", plus `data-dispatch-shown="stored-not-current"` (`:457-467`).
  - `AnalysisView` shows the shared `PinnedNotice` above the story (`:1254`).
  - The conclusion takes the stored-version branch before any day-state branch (`:1212-1216`). A non-current version can no longer reach the bare "<outcome>, for <scope>." sentence.
- **Direct URL.** The new test opens `?day=2026-10-02&revision=rev-old&view=analysis` on a CURRENT day. It asserts the stored conclusion, the notice, a non-"latest checked readings" label, a non-positive tone, and no "latest checked readings" text.
- **Versions panel.** Every panel link goes to `?revision=<id>&view=analysis` (`:1309-1316`). The same `inWindow` test therefore decides the framing for each link. The test clicks the non-current link from the current version and gets the stored framing. The current version keeps the bare conclusion and no notice.
- **Overview.** It was already pinned and now uses the same `PinnedNotice` component.
- **Revert plants (mine, all restored, tree clean afterwards).**
  - Product files reverted to `e55d075a` with the new tests kept: the F1 test fails, as do the F3 and F4 tests (3 failed, 89 passed).
  - Only the Analysis `PinnedNotice` removed: the F1 test fails (1 failed, 29 passed).
  - Only `storedNotCurrent` forced to `false`: the F1 test fails ("expected 'day' to be 'stored-not-current'").
  - Each of the three parts of the fix is therefore guarded independently.
- **Transient and failed-load cases.** While the detail of a non-current revision is loading, or if it fails to load, `selected` is null. Analysis then says "No period is selected, so nothing is concluded here" under the day's state line. That concludes nothing, so it is not fail-open. The wording is slightly inaccurate when the address does name a revision (Low note L1). This behaviour predates the fix round.

## F3: correct

`LedgerSiteEvidence.tsx:547-548`. The new branch runs only when no gateway is STALE, not all are CURRENT, and at least one is CURRENT. It reads "Some gateways are in contact; the others' contact is not known." with tone `not-known`, so it neither over-claims nor under-claims. The "No gateway report has been received yet" branch is now reached only when no gateway is CURRENT. Tested, and the test fails on revert.

## F4: correct; deviation 7 acceptable

- **Exemptions.** Only exact values remain exempt. "Rule wording" is removed, and each reason renders "Reason code <code>" with only the code under `REF`. The new test asserts that no exempt element, and no technical text at all, contains the statement, the not-inferred sentence or any reason text, and that the codes are listed exactly.
- **The plain restatement of "not inferred".** The recorded sentence is a backend constant, `NOT_INFERRED` in `backend/assetops_backend/analytics/claim_limit_read.py:57`. It is the same in every fixture sample, so exact-match recognition is sound.
  - The restatement keeps each element: no physical capacity is inferred; configured capacity is not treated as measured; only the selected version's accepted readings are used. It adds no claim.
  - It drops the word "public" from "accepted public readings" (Low note L2).
- **Unknown wording.** It renders "The record also states what is not inferred; that wording is not shown here." and never echoes the value. This is tested with `NEW_CODE`.
- **Deviation 7 (server sentences no longer verbatim): acceptable under `D-2026-10-16-w1-ux-disclosure`.**
  - The ruling allows individually labelled exact values. It says explicitly that "a labelled exact value does not authorize a technical explanation in the disclosure". Recorded prose therefore had no exemption to stand on.
  - Nothing the user needs is hidden:
    - Each reason's meaning is in the default reading's "What limits it". `reasonSentence` maps every code, including role and period.
    - The ceiling and support are in the headline, and their codes stay as exact values.
    - The API response is unchanged.
  - The packet correctly says that the verbatim strings would need an Architect exemption decision.

## F2: recorded honestly

The packet cites the logged `clientWidth` 390 and 1425 per screen. It says plainly that the `evidence` narrow pass has no log and is not established. It says the tool still lacks the width claim. It says layout evidence was not rerun, so the new Analysis notice, the state line and the disclosure changes are not depicted. That is a `not run` record, not a claimed pass. The only new visual element is a paragraph notice, so the layout risk is small, but it is unverified.

## No fail-open path, no weakened assertion

- The test diff is additions only: three new tests and a `waitFor` import. No existing assertion changed.
- Every new branch falls back to non-positive wording.

## Low notes (non-blocking)

- **L1.** `PerformanceDispatch.tsx:1160-1167`. When `revision=` names a version whose detail is loading or failed, Analysis says "No period is selected". "The selected version could not be loaded" would be more accurate. It is non-promoting and predates this round.
- **L2.** `EvidenceClaimLimit.tsx:766-767`. `NOT_INFERRED_WORDS` says "only the accepted readings of the selected version are used". The recorded sentence says "accepted public readings". The restatement is still true, but it loses the "public" restriction. Consider "only the selected version's accepted readings from the site's published record are used", or whatever plain gloss of "public" the Architect prefers.
- **Unchanged from the first review.** The "Versions of this period" links say "Version N: <outcome>" without marking which one is current. Once one is opened, the destination now frames it correctly.

## Checks I ran (from `frontend/`, PowerShell, at `6db70ffd`)

- **`npx.cmd tsc --noEmit`.** Exit 0.
- **`performanceDispatch`, `evidenceClaimLimit`, `v01bEvidenceVisual`.** 3 files, 92 passed.
- **`t028Vocabulary`, `sharedVisualVocabulary`, `w1Vocabulary`.** 3 files, 35 passed.
- **Revert plants.** As described under F1. All restored; `git status` is clean.

## Not verified

- **Full `npm.cmd test`, the build and `check-all.ps1`.** Not run. I cite the implementer: 74 files, 1762 passed, and 9 guards passed, both at `dd12f881`. The only later commit, `6db70ffd`, touches only the packet.
- **Served 1440 and 390 captures.** Not rerun (Chrome, dev server and DBs needed). They do not depict this round.
