# W1-F4 re-review (after fix rounds 1 and 2)

- Reviewer: fresh independent Claude reviewer. Revision `7a8df01c` (code as of `2045cfdd`). Diff `1132c336..7a8df01c -- frontend`.
- Inputs: the prior review `.agent/W1-F4-review.md`, the packet's fix table, and the captures `s601b`, `s602b` and `s603` at 1440 and 390 against the mock.

## Verdict: RETURN (one Medium)

All five prior findings are fixed and the layout now matches v69 on Verification and Site Work. One new Medium blocks. The Verification summary row can say "No success criteria recorded" when a frozen plan exists, which contradicts the panel beneath it. The fix is small.

## Prior findings

1. **High, summary row: fixed.**
   - `MetricHeader` (`ui/V69Layout.tsx`) renders `.v69-mheader` with Owner, Due / SLA, State, Source and Success criterion, in the mock's order.
   - It sits after the strip and before the cards, which the test asserts with `compareDocumentPosition`.
   - It is 5 across at 1440 and 2 across at 390 (`verification-pass-1440-app.png`, `verification-guardrail-390-app.png`).
   - In the refused variant every cell is a gap word. `LEADING_SELECTOR` gained the class and nothing else.
2. **Medium, Site Work columns: fixed.**
   - The table has the six mock columns, with "Not recorded", "Not set" and "Not recorded" in the gap cells.
   - State is a `w1f4-action-badge` tone badge. The latest-step link is the second line, and the created and recorded times are in its `title`.
   - The duplicate gap sentence is gone. Both tests assert the six headers and a badge on each row.
3. **Low, History codes: fixed, using the review's fallback option.** `DEMO_REVIEW_NOTE` and `ACTION_FOUNDATION_STALE` are shown in full. The expected and current IDs moved to `title`, and their plain meaning ("The Site configuration had changed…") is now in the cell.
4. **Low, duplicate no-plan sentence: fixed.** It is said once, and the test asserts that the second sentence is absent.
5. **Low, trial notice: fixed.** It is a `v69-chart-note` inside the owning panel on Plan, Evidence and Verification (in Outcome evidence). The comment is corrected, and the page-level callout is gone.

## New findings

1. **Medium: the Success criterion cell can falsely say none were recorded.**
   - **Where:** `frontend/src/sites/SiteActionVerification.tsx:388`.
   - **What is wrong:** the cell depends on the outcome's `target_reduction` metric, not on the plan.
     - On the plan-pinned path with no outcome yet (`noOutcomeForPlan`, lines 202-209), the plan is loaded but there is no outcome. The cell then reads "No success criteria recorded".
     - On the same screen, the Target panel says the outcome is pending and links "Open the success criteria" (line ~715).
     - The prior review specified "the plan target text, or No success criteria recorded".
   - **Why it matters:** this is a contradiction and a false negative claim. No test covers this variant. I found it by reading the code and did not render it.
   - **Fix:**
     - Fill the cell from what was actually read:
       - the criterion text when there is an outcome metric or a loaded plan (`plan !== null`);
       - "No success criteria recorded" only when the Action's verification state is `NO_PLAN`;
       - otherwise "Not available".
     - Name the subject, as the mock does ("≥25% less avoidable generator time; no reserve or service trade-off"). For example: "At least 25% less avoidable generator time; reserve and service limits no worse". The bare "At least 25% lower" does not say what is lower.
     - Add an assertion for the plan-pinned, no-outcome variant.
2. **Low: Outcome evidence states the trial limitation twice.**
   - The demonstration line ("This is a policy trial on demonstration data; it shows no savings or realized benefit.") is followed two lines later by `TrialNotice` ("…no savings or realized benefit; a resolution is never permanent"). Activity evidence also says that a resolution "is not permanent".
   - This is the exact cut for the Verification pair overage. On the Verification view, drop the demonstration sentence when `TrialNotice` follows it, or merge the two into one line. That saves 2 note lines (about 30 px), which brings the pair to about 1.3x.
3. **Low: the packet misstates a test change.** The round-2 table says `siteActionVerification` was re-pointed ("attempts counts read inside the disclosure, trial notice one sentence"). That file has no diff in `1132c336..7a8df01c`. Its existing regex at `:221` still matches the shorter notice. Correct the packet. The guarantee itself is not weakened.

## Heights

| Panel | Ratio | Judgment |
| --- | --- | --- |
| Verification pair | 1.40-1.47 | Mostly honest state: the withdrawable-resolution note and Finding version 2. The one cut is new finding 2. |
| Evidence guardrail | 1.52 | Honest state. The failed-limit line ("Failed limit: Time below the reserve… Battery charge at the end of the window") is a material limit and must stay visible. |
| Plan guardrail | 1.37 | Honest state. It has the same failed-limit line and 5 real criterion rows. |
| Site Work active | 1.36 | A working control. The window form is in the header, and the count and basis line is one compact row. Acceptable. |
| Recommendation guardrail | 1.39 | Honest state. It is the hold sentence, unchanged since the prior review, which accepted it. Not recaptured in round 2, and there is no code change on that route. |

## Regression scan

- **State line:** said once on each inspected screen.
- **Disclosures:** one per panel. Target has "Dig deeper" and Outcome evidence has "Earlier outcomes and plans". The strip's "How this was worked out" belongs to the strip, not a panel.
- **Labels and headings:** no leftover labels or h3s. The structure and plant tests pass.
- **Raw values:** no new raw IDs, enums or backend text. Remaining codes are pre-accepted (prior finding 3). Separately, the History "Earlier record" line still shows a short event ID (`a48e018a-…`); this was there before F4.
- **Mock content:** the mock's rows, columns and chips are present for the summary row and Site Work. As before, the Site Work Incidents and Maintenance subtabs are absent under the capability rule.
- **Material limits:** none hidden. Moving the attempts list into the closed "Earlier outcomes and plans" disclosure is acceptable, because History and Activity evidence keep the withdrawable and earlier/current state visible.
- **Assertions:** none weakened. `siteActionVerification.test.tsx` and its S6-02b fail-closed checks have no diff. The `siteWorkActions` vocabulary regex dropped `Owner` and `Due`, because those are now column headers by contract. Their cell values are asserted exactly instead.

## Checks run (this reviewer, at `7a8df01c`)

- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run` on the 4 `w1f4*Structure` files plus `siteAction`, `siteActionVerification`, `siteWorkActions` and `siteFoundationChange`: **8 files, 163 passed, 0 failed** (63 s).
- Not rerun:
  - The full suite. The implementer recorded 2019 passed and 0 failed at `2045cfdd`, which is the same code revision.
  - `check-all.ps1`.
  - The captures. I could not run them here, but I compared the stored pairs.
