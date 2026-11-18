# W1-UX-04 re-review - fix round 1

Reviewer: fresh independent Claude reviewer. I did not author this slice or the fix round.
Revision reviewed: `e1fb7575`, detached in `AssetOpsV1-review5`.
Diff reviewed: `git diff fb2c387b..e1fb7575`. It changes 4 files: the packet, `verificationCards.tsx`, `ProductStatus.tsx` and `siteActionVerification.test.tsx`.

## Verdict: ACCEPT

All three Medium findings are fixed. I found no regression. Two new Lows are below; neither blocks.

## Checks I ran (from `frontend/`, PowerShell)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` | exit 0 |
| `npx.cmd vitest run src/ui src/sites/__tests__/siteActionVerification.test.tsx src/sites/__tests__/siteAction.test.tsx` | 7 files, 140/140 passed (28 s) |

I did not run these, so they are unverified by me:
- the full `npm.cmd test`. The packet reports 1756/1756 on a second run, after one `siteFoundationChange` flake on the first.
- `npm.cmd run build`
- the served captures. The served INCONCLUSIVE capture is recorded as not run.

## Findings checked

### M1 (historical outcome drops source, note and failures): fixed

`verificationCards.tsx:105-130`. The historical branch now renders:
- `Source: {words.source.label}`
- the demonstration note, when there is one
- the failed limits, as before
- the known failures, gated on `words.showsKnownFailures` exactly as `ProductOutcome` gates them

`words` is still built from the record's outcome and source class. The historical test now asserts `^Source: .+` and the policy/no-savings note.

One gap: no test asserts the known failures on a historical card. The code path mirrors the current branch, so I am not raising it.

### M2 (INCONCLUSIVE with a measured failure): fixed

- **Shared component.** `ProductOutcome` gains `showLimits = false`. The limits branch is now `words.showsFailedLimit || (showLimits && failedLimits.length > 0)`, which is additive. With the prop omitted, rendering is byte-identical to before. `verificationCards.tsx` is the only non-test caller of `ProductOutcome` (grep), so no other consumer changes.
- **The card.** It passes `showLimits={limits.length > 0}`. `limits` comes only from metrics whose state is FAIL (`failedLimits`), so a VERIFIED or REASSESSMENT_PENDING outcome cannot gain a limits list this way.
- **Single prefix.** The card strips the leading "Known failure: " from `reasonWords`, and the component adds it once.
- **Test.** The INCONCLUSIVE case now has a FAIL `below_reserve_seconds` metric (3600 s). It asserts:
  - the known-failure list exists
  - it starts with a single "Known failure: " and does not double it
  - the list names the reserve
  - the card shows "measured 60 min, limit 0 min"

  The test passes.

### M3 (390 px claims): fixed

The acceptance row (`W1-UX-04-review-packet.md:77`) now reads: "1440: met ... 390: not established by measurement (visual check of PNGs only)". Fix round 1 (`:148`) extends that to every 390 claim, including the "364/364" total. The packet also records:
- that the `W1_NO_VISUAL_OK` setting is unknown per run (only the tool default is assumed)
- that the served INCONCLUSIVE capture is not run

### Lows from the first review

- **L4 (Evidence headline when both windows are incomplete).** Fixed: it now says "both windows".
- **L5 (Historical status on a cutoff).**
  - **Evidence card.** It adds a HISTORICAL `ProductStatus` when `verification_state.historical`, with as-of `knowledge_cutoff`. That is the right time.
  - **Plan card.** It adds the HISTORICAL status for a current, non-replaced plan when `verification_state.historical`, with as-of `plan.recorded_at`. Is this honest? It is not false: the plan was fixed at that time and is the same plan at the selected time. It is imprecise, though; see N1.

## New findings

### N1. Low - the Plan card's Historical as-of is the plan's recording time, not the selected time

`frontend/src/sites/verificationCards.tsx:241-247`

- **What is wrong.** The scope line says "The plan as it stood at the selected earlier time", but the as-of shows `plan.recorded_at`, the time the plan was fixed. The selected time is a different, later instant.
- **Why it does not block.** The time shown is true, the plan did not change in between, and `CurrentStrip` above shows the selected time and the actual current state.
- **Fix.** Prefer `body.selector.recorded_at` when it is set, and fall back to `plan.recorded_at` with a scope that says "recorded".

### N2. Low - the packet's capture table still shows combined 1440+390 totals without an inline qualifier

`.agent/W1-UX-04-review-packet.md:110-116`

The table still shows totals such as 136/136. The Fix round 1 section qualifies them, but the table itself does not. Fix: add a note under the table that the 390 claims are not measured.

## No-regression check

- **No fail-open path.**
  - The new Historical statuses only add a label; they never drop one.
  - `showLimits` only adds rendering, and only for FAIL metrics.
  - Stripping the prefix only changes text.
- **No weakened assertion.** The test diff adds assertions. The INCONCLUSIVE fixture changed from `KNOWN_FAILURE:target_reduction` to `KNOWN_FAILURE:below_reserve_seconds` with a measured FAIL. That is the backend's real shape (a guardrail measured FAIL while another fact is unknown), and the case is now asserted more strictly than before.
- **S6-02b tests.** The fail-closed tests, including F1 and F3, pass unchanged.

## Residual risk

- The served INCONCLUSIVE capture is still not run. Its card is covered only by jsdom.
- The 390 measurements wait on the shared tool fix, which is owned outside this slice.
