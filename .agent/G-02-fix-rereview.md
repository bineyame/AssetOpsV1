# G-02 fix round 1 - fresh Claude re-review

Reviewer: fresh Claude Reviewer, independent of the Implementer. Branch `task/G-02-v01a-gap-pilot`, HEAD `e2010e6`, diff `e2ffd40..e2010e6`. Judged against `.agent/architect-G-02-answers.md` (Q1, Q2 overruled, binding) and `.agent/G-02-review.md` (F1, F2, C-a).

## Verdict

**ACCEPT, with R1 fixed on the branch.** R1 is a records-only fix to the owner walkthrough. The coordinator can check it; it does not need another code re-review. Q1, Q2, F1, F2 and C-a are done as ruled. The one evidence failure (390 SLD caption) is existing geometry that the new tag now measures. It is not a defect introduced here. Carry it as an owner item.

## Verification

1. **Q1, done as ruled.**
   - `G-sld-reporting-status` has seven placements, one per JSX source and slot kind. The registry, the mirror `gapCatalogue.ts` and the Vitest exact-text map all agree.
   - SVG bus and node slots render through `MissingClaimSvg` as SVG `<text>`. The test asserts the SVG namespace, `data-sld-slot="unfilled"`, no `aria-hidden`, exactly one bus slot and nodes-1 node slots. No HTML element is placed inside the SVG.
   - Parts-table cells hold an inline `MissingClaim` span inside the `<td>`. The cell keeps `data-sld-row-slot`, and its text is exactly "Readings not assessed here".
   - The Lab is untouched:
     - Only the `slots === null` branch is tagged.
     - The Lab's `drawingSlots` always passes non-null slots.
     - The Lab branch renders `content?.text ?? slots.unfilled`, which is the same value as before.
   - The split `SITE_SLD_INTRODUCTION_SCOPE + " " + _READINGS` assembles to the previous sentence character for character.
   - Pure scope captions stay untagged, and the test asserts this.
   - Accessibility is unchanged: the same elements are used, the words remain the element's own text, and no ARIA was added or removed.
   - **Caption tagging is correct.** "both are empty in this build, for every component, and neither holds a reading." asserts that the slot holds no reading. That is the absent-readings claim the Architect said to tag at its own placement. It is not a pure scope statement. The untagged lead-in ("The runtime and evidence column is the slot each drawn component carries:") is descriptive.
2. **Scan.**
   - `MissingClaimSvg` is recognised. A literal `as` of `text` or `tspan` is enforced, and a non-literal `as` is an error. `MissingClaim` with `as="text"` or `as="tspan"` is an error. Uniqueness and known-ID checks apply to both components.
   - The new cues are narrow, with no bare "not assessed", "not declared" or "No ... record here".
   - The Dispatch lookbehind behaves as intended: "Dispatch not available here" and "DISPATCH not available here" do not match. "Financial assumptions not available here" does match, and that copy is tagged.
   - **Fail-before, checked by me.** With `missing-claim-scan.mjs` reverted to `e2ffd40`, `node --test tools/checks/test_missing_claim_scan.mjs` gave 16 pass and 4 fail:
     - real-repo
     - C1
     - Q2 cue mutation
     - SVG variant
   - I restored the file with `git checkout --`. The tree is clean for `tools/checks`.
3. **F1, F2 and C-a.**
   - The walkthrough now limits the claim to statements of absent capability.
   - The packet's "HTML only" justification is marked as superseded, and the packet says correctly that it held only for the SVG.
   - `sld:2.what-it-reports` is in `G-sld-reporting-status.element_ids`.
   - Both older evidence tools carry an honest SUPERSEDED header.
4. **The 390 `sld.contents.caption` failure is existing geometry.**
   - No CSS changed in the diff. An inline span inside `<caption>` does not change layout.
   - The caption is as wide as its table, and the table is wider than the phone. The sentence was always reachable only through the table's inner scroll, and one line is wider than the visible scroll box.
   - The evidence tool only measures tagged elements, so tagging the sentence made the existing width visible to it.
   - This is the same kind of issue as V-01a round-3 C1 (Readiness table scrolls sideways inside its box at 390). The owner accepted that as a carry on 2026-10-12.
   - Page scroll is clean.
   - **Recommendation:** carry it as an owner item; do not fix it in G-02. The later fix is to move the caption prose out of `<caption>` into a note above or below the table, using the existing scope-note pattern at `frontend/src/ui/primitives.css:592`. That is a layout change outside G-02's gap-tagging scope.
   - The packet records the result honestly as 321/322 with the failure named. But see R1.

## Checks run (by me, on `e2010e6`)

- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run`: 61 files and 1446 tests passed. It ran in this session.
- `npm.cmd run build`: built. The only warning is the existing chunk-size warning.
- `tools/check-all.ps1`: all 9 guards passed. The scan reported 30 tagged uses, 12 baselined, merge-base `56254477fd`, ceiling 16.
- Registry checker: exit 0, valid. Ledger: valid (110 screens, 88 models, 258 panels).
- Fixtures:
  - `test_missing_claim_scan.mjs`: 20/20.
  - `test_mock_gaps.cjs`: 13/13.
  - `test_delivery_next_work.cjs`: 35/35.
- Not run:
  - `tools/g02-gap-evidence.mjs`. It needs Chrome, the backend and dev servers, and I was told to start no servers. The 321/322 figure is the Implementer's.
  - Backend pytest. Nothing in this diff touches the backend.
- The working-tree `M` on the registry, ledger and mock-gap checkers and on the task files is line-ending only. `git diff --ignore-cr-at-eol` is empty.

## Findings

**R1 (low; owner-facing record; fix on the branch).** `.agent/G-02-owner-walkthrough.md`:
- Line 29 still says "322/322 claims passed". The current evidence run is 321/322, with `390 /sld: (c)` failing.
- Step 5 tells the owner "The lines wrap inside their panels", which is not true for the SLD parts-table caption.
- Why it matters: the owner's visual decision is the remaining gate, and the walkthrough is what the owner reads. It currently states a clean pass and hides the one item that needs the owner's judgement.
- Fix:
  - Change line 29 to 321/322 and name the failure in one plain sentence.
  - Add to step 4 or step 5: "At 390 px the sentence under 'What the diagram draws' is part of the table and scrolls sideways with it; accept it as is, or ask for it to be moved out of the table."

## Carries and notes (not blocking)

- **N1 (scan breadth, preference).** The cue `\breadings?\b[^.]{0,40}\bnot\s+assessed\b` is scoped rather than exact. It would also match ordinary-state copy such as "The reading window is not assessed". No such copy exists today, and a false match fails closed: the copy must be tagged or reworded. A later G batch can tighten it to the two SLD phrasings if a legitimate window state trips it.
- **N2 (scan leak, small).** `(?<!dispatch )` exempts any copy ending in "dispatch not available here", for example a hypothetical "Live dispatch not available here". A tighter exemption would match only the exact string "Dispatch not available here" at the start of a text node, or exempt by `data-control-link="no-dispatch"`. This is low risk; it can go with the next G batch's cue review.
- **N3 (fixture gap).** No fixture covers a non-literal `as={expr}` on `MissingClaimSvg`, although the code path exists. It is a one-line addition when the scan is next touched.
- **Carry (owner):** the 390 SLD parts caption, as in item 4.
- The `.ai/DECISIONS.md` entry the Architect proposed is still pending for the coordinator after merge review.
