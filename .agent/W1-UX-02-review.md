# W1-UX-02 review - Site, Finding and money presentation

Reviewer: fresh independent Claude reviewer (did not author the slice). Revision under review: `2aa3af3c` (detached, worktree `AssetOpsV1-review5`). Diff: `git diff b982905b..2aa3af3c -- ':!.agent'` (28 files, +4171/-1020). Task `tasks/W1-UX-02-site-money.md`; rulings `D-2026-10-16-w1-ux`, `D-2026-10-16-w1-ux-disclosure`, `D-2026-10-16-s408`.

## Verdict: RETURN

One Medium finding (M1) blocks merge. It is a small fix in one component. Everything in the "honest money" priority list held, apart from M1, which is about the price headline rather than an amount. After M1 is fixed, a narrow re-review of `SiteFinancials.tsx` `CurrentPrice`/`PriceTimeStrip` and its test is enough.

## Checks run (from `frontend/`, PowerShell)

- `npx.cmd tsc --noEmit -p .`: exit 0, no errors.
- `npx.cmd vitest run` on 13 files: the eight screens' tests (`sitesIndex`, `s5SiteWindowOverview`, `s502OverviewFindingList`, `s404SiteFindingIndex`, `siteFinding`, `siteFindingEvidence`, `siteFindingHistory`, `siteFinancials`), the vocabulary/parity tests (`findingLinkWordsParity`, `t028Vocabulary`, `productStatus`, `sharedVisualVocabulary`) and `sourceProvenance`. Result: **13 files, 381/381 passed**, 27.7 s. Only act() warnings on stderr. Vitest did load its config under this sandbox this time.
- Not run: the full `npm.cmd test`, `npm.cmd run build` and `tools/w1-ux-02-evidence.mjs`, which needs Chrome, the backend and a dev server. For the full suite I cite the implementer's run at `bc1cea1b`: 74/74 files, 1840/1840 tests, 145 s. `bc1cea1b..2aa3af3c` touches only `.agent`, `.ai` and the task status line, so that run applies to the revision under review. The 1440/390 captures are unverified by me (see L1 and the script assessment).

## Findings

### M1 (Medium, acceptance gap / honest state): a past-cutoff price list's headline and strip say the price is "in use" today
`frontend/src/sites/SiteFinancials.tsx:393`, `:410-412`, `:162` and `:171-178` (`PriceTimeStrip.stateOf`).

With `?recorded_at=<past>`, `CurrentPrice` gets `historical=true`, and the state line correctly says "Prices as recorded at an earlier moment ... it may not be the price in use now". But the headline is still `Diesel price in use: <price>` whenever the selection is PRICED, and the strip marks the selected entry **"In use today"**. The selection is the price that covered today as the records stood at the past cutoff. That read does not prove the price is in use now: a later correction could have replaced it, which is exactly what the state sentence warns about. So the headline and the visual claim more than the read proves, and they contradict the state line beside them (`D-2026-10-16-w1-ux`: "A headline, graphic or shorter label must not claim more than that read proves"). Before this slice the panel said "Diesel price, set by ... on ...", with no "in use" claim. The overclaim is new.

The existing test "an earlier recorded moment is its own state" (`siteFinancials.test.tsx` ~:1330) checks only the state line, so it does not catch this.

**Fix:** when `historical`, word the headline as a recorded-then statement, for example "Diesel price covering today, as recorded then: <price>". Give the strip's selected entry a historical label, for example "Covered today, as recorded then", in place of "In use today". Add assertions to the earlier-moment test that neither "in use" phrase appears.

### L1 (Low, evidence accuracy): the packet's reason for the untimed s402b priced case contradicts the API, and the capture cannot tell a hidden time from a missing one
`.agent/W1-UX-02-review-packet.md:96`, `tools/w1-ux-02-evidence.mjs:115-118`, `:200`, `frontend/src/sites/FindingConsequence.tsx:587,621`.

The packet says the s402b priced case shows "As of: time not recorded" because the head version carries no `recorded_at`. That cannot be the cause: `consequence_read.py:105` always serialises `recorded_at`, and `ConsequenceRevision.recorded_at` is a required string. The unit test for the priced case shows "As of 14 Oct 2026, 10:00 UTC" once the consequences read has loaded.

The likely cause is timing. The money card's `asOf` comes from the head of the second (consequences) read. That read starts only after the bridge read lands. The script's `go()` waits only for the state label and then 500 ms, and line 200 accepts "time not recorded" as a pass for every state. The capture probably caught the page before the second read landed, which would also leave out the "From finding to money" panel.

**Fix:** correct the packet. For the priced Financials capture, wait for `[data-consequence-method]` or an `As of <digit>` bound, then re-capture.

### L2 (Low): a current amount is briefly shown with "As of: time not recorded"
`frontend/src/sites/FindingConsequence.tsx:587,621`. While the consequences read is in flight, a PRICED CURRENT bridge already renders the positive label and the range, with an untimed bound. The bound fills in when the read lands. The window is honest but rough. Optional fix: leave the bound out, or show "Loading the time it was worked out", until the consequences read settles.

### L3 (Low): a priced Overview money read without both bounds draws a positive "Current amount" state line
`frontend/src/sites/SiteWindowOverview.tsx:82-86`, `:618-620`. The words come from `m.state` alone. A `PRICED` read with a null bound would show "No current amount." beside a positive "Current amount" status. The label is unchanged from before, but it is now drawn as a positive `ProductStatus`. **Fix:** when `priced` is false, use non-positive words.

### L4 (Low, preference): the Overview card and Financials word the same money codes differently
`SiteWindowOverview.tsx:59-122` and `FindingConsequence.tsx:94-146`. For example, the Overview says "Fuel quantity not known" and "Fuel cost out of date", while Financials says "Not calculated: no fuel amount, so no cost" and "No current amount can be shown". The Overview's "Upstream out of date" label and its "Upstream" fact term are jargon. This is consistent with four parallel sub-implementers. It is not dishonest, so it belongs in the batched W1 plain-language task.

### L5 (Low, cleanup): `STATUS_WORDS` is now dead
`frontend/src/sites/SiteFindingIndex.tsx:82-93`. Its comment says the export is kept for `OverviewFindingList`, but that view no longer imports it. Remove it, or fix the comment. The packet already notes the stale `[data-finding-index-token]` selector in `tools/s502-overview-finding-list-evidence.mjs:148`.

### L6 (Low, owner awareness): untimed Financials non-positive states
`FindingConsequence.tsx:621`. When a recorded head is loaded (STALE, LR-01-withheld), the read carries the recorded cost's `recorded_at`, but the state line shows "As of: time not recorded". This is defensible: that instant dates the recorded cost, not the "no current amount" judgement, and the bridge carries no read instant. But it is a time the read has, so it belongs on the owner's list beside the packet's own "read time on the bridge needs an Architect decision" item.

## Priority checks that held

- **Amount gate.** `FindingBridge` `shown` requires PRICED, CURRENT, an amount and a currency (tighter than before). Every other state draws one `not-known` value bar, no zero bar and the "Why no current amount" line. `consequenceWords` routes PRICED-not-current by its currentness. Unknown codes fall to the shared non-positive fallback (`moneyWords` treats PRICED as unrecognised, tone limited). This is tested with 9 non-positive cases and 3 withheld cases.
- **LR-01.** `MoneyLimit` and the exact recorded-cost link are kept for the gated states.
- **S4-08.** The history state line is "Recorded versions, kept for the record" (neutral), with the cutoff as its bound. There is no positive status and no known bar, and rows keep "Not a current cost."
- **S5-02 no-parity.** `compareParity` logic is unchanged (labels only). The Overview basis references appear only when parity is not "same".
- **S4-04 proved zero.** Proved zero appears only when the status is CURRENT and `total_count === 0`, with `knowledge_at` as its bound. Not-current and no-count states say "not known / not a zero".
- **S4-05 provenance.** `SourceProvenanceNotice` stays inside the visible `ProductStatus` on Finding, Evidence and Financials, and beside the Overview money state line.
- **MissingClaims.** None removed. All three `MissingClaim` imports are retained, and `G-assumptions-human-edit` is asserted.
- **Changed test assertions.** I read every removed line. None weakens a fail-closed check. The moved token, reason and version assertions keep equality inside a labelled exact row. The withheld and reassessing assertions now pin the exact sentence plus the label. The `sitesIndex` interactive list is still exact. The fuel-cost test adds absence checks outside the disclosure for `fuel-cost-1` and `ev-1`. The `data-finding-currentness` query already resolved to the page root before this diff, and a stricter card-sentence check was added.
- **`LINK_DISPLAY_OVERRIDES`: acceptable.** `LINK_WORDS` stays word for word with the backend `BROKEN_WORDS`, and the parity test is unchanged and passing. The overlay only rewords the two "fingerprint" keys, and the frontend never renders the backend's `detail` strings. The guard test checks that keys are a subset, that the key sets are equal and that no text contains "fingerprint". A backend rewording should retire the overlay.
- **Deviations: accepted.**
  - `FindingDetail.tsx` is the legacy route; `SiteFinding.tsx` is the migrated one.
  - No Financials Analysis tab. Method and limits are now visible prose, the readings table sits in its own closed disclosure (before this slice the whole method sat inside one closed disclosure, so this is an improvement), and Evidence owns the trail. Owner review is still flagged.
  - Mock items with no read are not built, which follows the honest-missing rule.
- **The 390 px check is real.** `Emulation.setDeviceMetricsOverride` sets width 390 with `mobile: true`, and the script then requires `documentElement.clientWidth` to be in 370..390. A page without a working viewport would lay out at about 980 and fail. It also requires page `scrollWidth <= clientWidth` and that no card element overflows outside a closed disclosure or a contained scroller. Its weakness is the as-of acceptance described in L1.

## Residual risk not named in the packet

- Captures at 1440 and 390 were not re-run by the reviewer.
- The Site Findings rows table now sits in the card's `visual` slot. Its density at 1440 is visible only in the captures.
