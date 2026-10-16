# W1-UX-01 re-review - fix round 1

Reviewer: fresh independent Claude reviewer (did not author the slice or the fix). Revision: `8298fed7`. Diff: `git diff e7b99a11..8298fed7`.

## Verdict: ACCEPT

M1 is closed and L2-L4 are addressed. I found no new fail-open path and no weakened assertion. No blocking findings.

## Prior findings

- **M1 (closed).** `receiptWords` (`frontend/src/sites/LedgerSiteEvidence.tsx:365-394`) now has explicit `NO_DATA`, `REJECTED_ONLY` and `ACCEPTED` branches. Any other state returns `currentnessWords(null)`. That goes through `lookup` -> `unrecognised(null)`, giving "We cannot judge this yet" with tone `limited`, and the raw state stays on `code` only. The new route test (`s2LedgerEvidence.test.tsx:120-133`) asserts the neutral label, the `limited` tone and no "accepted" on the state line. Mutation proof (mine, reverted): sending every state to the accepted branch made that test fail (1 failed, 19 passed).
- **L2 (closed).** The W1 single-word codes now include ACCEPTED, APPLIED, OBSERVED, REJECTED, EFFECTIVE and COMPLETED. Matching is case-sensitive, and the code boundary excludes letters, digits and `_`. So "Effective", "completed" and "accepted" in ordinary copy are not flagged, and `INEFFECTIVE` does not also report `EFFECTIVE`. Mutation proof (mine, reverted): planting `evidence.state` into the Evidence state-line sentence failed `v01bEvidenceVisual` (1 failed, 30 passed). Before this fix the same plant passed 30/30.
- **L3 (closed).** For VERIFIED, `SiteAction.tsx:401-408` now renders only an empty `data-action-verification-state` marker. The qualified shared line ("within the sampled limits ... not continuous proof") is the only VERIFIED sentence. Other states keep their sentence.
- **L4 (closed).** `exemptReason(element, root)` (`frontend/src/test/productVocabulary.ts:174-182`) walks up and stops after checking the root itself. An exemption on the root is still honoured by the lookup, but the existing "exemption cannot cover the disclosure container" check still flags it. The new test proves that an exempt ancestor outside the root does not silence a leak.

## Observations (non-blocking, no action required)

- `headlineOf` (`LedgerSiteEvidence.tsx:282-291`) still falls through to the accepted-count sentence for an unknown state. The first review marked this optional. The sentence states the `accepted` count as a number, which is a factual count and not a judgement, and the state line beside it now reads "We cannot judge this yet". This is residual and is not a false claim.
- `w1Vocabulary.test.tsx` loops over ACCEPTED, APPLIED, OBSERVED and REJECTED but not over EFFECTIVE and COMPLETED. They share the same JSON-driven path, so the coverage gap is cosmetic.

## Checks run (from `frontend/`, at `8298fed7`)

- `npx.cmd tsc --noEmit`: clean (exit 0).
- `npx.cmd vitest run src/ui src/shell/__tests__/s2LedgerEvidence.test.tsx src/shell/__tests__/v01bEvidenceVisual.test.tsx src/sites/__tests__/siteAction.test.tsx`: 8 files, 141 passed.
- Two mutation proofs, described above. Both were reverted, and the worktree was clean afterwards.

## Not verified

- The full frontend suite: the packet reports 1738/1739, with `siteFoundationChange` passing 8/8 on rerun. I did not rerun the full suite or `tools/check-all.ps1`.
- Layout evidence was not rerun. That is acceptable because the fix makes no layout change: the VERIFIED marker is an empty span and only text changed.
