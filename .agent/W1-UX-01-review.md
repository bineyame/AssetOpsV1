# W1-UX-01 review - shared product presentation

Reviewer: fresh independent Claude reviewer (did not author the slice). Revision reviewed: `184a6519` (head of `task/W1-UX-01`; final code revision `530da1c8`). Diff: `git diff 3e6dbc88..184a6519 -- ':!.agent'`.

## Verdict: RETURN

One Medium finding (an honest-state fallback in a new word map). It is a few lines to fix on the branch. The rest of the slice is sound: the shared map, the components, the scan extension and the three migrated cards meet the packet, and no fail-closed test was weakened.

## Findings

### 1. Medium - an unrecognised Evidence state reads as "Readings received and accepted"

`frontend/src/sites/LedgerSiteEvidence.tsx:365-388` (`receiptWords`). The new state-line words check `NO_DATA` and `REJECTED_ONLY`. Every other value, including a code the screen does not know, falls through to "Readings received and accepted" / "These counts say what arrived and was accepted". The client guard does not limit `state` to the three typed values (`frontend/src/sites/ledgerEvidenceClient.ts:280-292` only checks the key exists), so a new or drifted server state reaches this branch.

Why it matters: the packet and the Architect ruling require that an unknown code falls back to a non-positive sentence, with the code only in the detail disclosure. This is a new map written in this slice, beside the shared one that already has that fallback. It puts an unproved "accepted" claim on the state line that `expectStateLineVisible` exists to protect. The pre-existing `headlineOf` (`:281-290`) has the same fall-through, but it is now repeated on the shared state line.

Fix: add an explicit `ACCEPTED` branch. Send any other value to the shared unrecognised words, for example `{ ...currentnessWords(evidence.state) }` with the neutral "We cannot judge this yet" or an equivalent. The tone must not be positive. Add one route test with an unrecognised `state` that asserts the neutral label and checks that "accepted" is not on the state line. Optionally make `headlineOf` fall back the same way.

### 2. Low - the W1 closed code list misses single-word state codes these routes carry

`frontend/src/test/productVocabulary.json:114`. The case-sensitive single-word list has no `ACCEPTED`, `APPLIED`, `OBSERVED` or `REJECTED`. The migrated Evidence and Action routes use these raw states (Evidence `state`, Action `application`). The underscore shape pattern cannot catch them. I proved it: planting `${evidence.state}` (renders `ACCEPTED`) into the Evidence card's scope left `v01bEvidenceVisual` and `s2LedgerEvidence` passing 30/30. Nothing leaks today, and the Architect named the list only by example, so this does not block. Add them, plus other Action/Evidence single-word states, before UX-02..05 opt in more routes.

### 3. Low - the Action card repeats the old VERIFIED wording without the sampled qualifier

`frontend/src/sites/SiteAction.tsx:401-403`. "What this means" still renders S6-02b `stateLabel(v.state, v.reasons)`. For VERIFIED that is "Target met within every limit.", directly under the shared line "Target met within the sampled limits" and its "not continuous proof" sentence. The qualifier is visible beside the headline, so this is not a false claim. But the second line drops it and duplicates the state. Use `words.sentence` there, or drop the repeat.

### 4. Low - an exemption on an ancestor of the scan root still silences the scan

`frontend/src/test/productVocabulary.ts:174-177`. `exemptReason` uses `closest()`, which walks above the scan root. The new check only looks at the root and its descendants for invalid exemptions. If a container above a scanned root carries `data-vocabulary-exempt`, every text node under the root is skipped with no violation. The three route tests are not exposed, because their `main` scan would flag a card-level exemption (it wraps more than one value). A disclosure-only scan or a future narrower root would be exposed. Fix: stop the lookup at the scan root, or also validate exempt ancestors of the root.

## Honest-state checks (passed)

- `productWords.ts`: every lookup keys on the caller's code. An unknown code returns "We cannot judge this yet" / "We cannot explain the limit from this record." with tone `limited`, and the code stays only on `code`. `positive` is returned only for CURRENT and VERIFIED, and VERIFIED on an unestablished source is downgraded to `limited` (`:326`).
- Trial outcomes key on (outcome, reasons, source). INEFFECTIVE + `GUARDRAIL_FAIL` gives "Trial missed a safety or service limit", never "Target not met". I checked the backend: `verification_rules.py:781` always emits `GUARDRAIL_FAIL` alongside `GUARDRAIL:<metric>`, so the reason match is complete. VERIFIED keeps "five-minute sample ... not continuous proof". Demonstration sources carry the policy-trial / no-savings note.
- Money: withheld and no-price are separate sentences, each "not zero"; no `$0` path.
- `ValueBars`: a null value draws a hatched `not-known` mark and "not known" text; a known 0 draws an empty track with "0".
- `asOfText`: a missing instant reads "As of: time not recorded", never now.
- Overview `objectiveWords`: CLOSED stays domain, UNKNOWN is explicit, and everything else goes through the shared fallback. Action `trialStep` falls back to `not-known`, and the application words fall back to "not recognised".
- Accepted deviations: the Evidence as-of uses `extent.last_received_at`, which may understate; the Action summary passes source `null`, so VERIFIED reads `limited` with a note pointing to Verification.

## Scan checks

- The disclosure list matches `D-2026-10-16-w1-ux-disclosure` exactly: 7 phrases, 20 words and 16 codes, plus the underscore shape.
- Raw-code matching is case-sensitive. SOC/UTC/kW/kWh/PV are not flagged; the T028 acronym gloss rule still applies separately, as ruled.
- The scan root itself is checked for an exemption, which closes the self-exemption hole (test "an exemption cannot cover the disclosure container"); see finding 4 for the ancestor case.
- `expectStateLineVisible` asserts state, sentence, scope and as-of: each is present and non-empty, sits outside any closed `details` body, the exact-reference disclosures are closed, and as-of starts with "As of ".
- My own mutation proofs, each reverted with `git checkout`:
  - "(UNASSESSED)" in the Action card description failed `siteAction` (W1 scan).
  - "Assessment run" as an Overview disclosure label failed `s5SiteWindowOverview` (W1 scan).
  - "(ACCEPTED)" in the Evidence label failed only on label equality, not on the scan. That led to finding 2, which I confirmed with a scope-only plant that passed.

## Test assertions changed

I diffed every changed assertion. `s2LedgerEvidence` and `v01bEvidenceVisual` swap the outcome-facts selector for the equivalent value-bar keys, in the same order; `v01b` adds a value check. `s5SiteWindowOverview` replaces the old state words ("Unknown", "Reassessment failed") with the new ones and adds state-line checks. Nothing was removed or weakened. The T028 tests are untouched.

## Migrated cards

The hierarchy is question, headline, state line, visual, then What this means / What to do, a destination link and the closed disclosure last. The recorded differences from v69 are reasonable and honest. Exact links are kept: the Overview dispatch-day link with revision (omitted when CLOSED, as before), the Evidence Analysis link keeping `from`/`to` (tested), and the Action Verification link.

## Checks run (from `frontend/`, revision `184a6519`)

- `npx.cmd tsc --noEmit`: clean (exit 0).
- `npx.cmd vitest run src/ui src/shell/__tests__/s5SiteWindowOverview.test.tsx src/shell/__tests__/s2LedgerEvidence.test.tsx src/shell/__tests__/v01bEvidenceVisual.test.tsx src/sites/__tests__/siteAction.test.tsx`: 9 files, 170 passed.
- The full suite was not rerun, per the dispatch. The implementer reports 1737 passed at `530da1c8`; I did not verify it.

## Not verified

- The 1440/390 captures and keyboard reach (`tools/w1-ux-01-evidence.mjs`) need served walkthroughs and Chrome. I did not rerun them; the packet records 16/16, 44/44 and 30/30.
- `tools/check-all.ps1` was not rerun.
