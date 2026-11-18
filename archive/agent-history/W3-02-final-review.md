# W3-02 final review (whole slice, before merge)

Branch `task/W3-02-estate-evidence-money-basis`, head `5fe9d4b2`. Read through git objects. The tests ran in a private
worktree, `AssetOpsV1-w302final` at `5fe9d4b2`, which has since been removed. The review2 worktree was not modified.
Main has no commits that are not on the branch (`git log 5fe9d4b2..main` is empty), and `git merge-tree` against main
is clean.

## Verdict: REVISE

One High and one Medium finding block the merge. Units 0a, 0b and 0c and commits 1 to 3 were accepted earlier, and I
found nothing in them that needs reopening.

## Findings

### High

**H1 - At 390 the Consequence register hides part of a two-row register behind a nested vertical scroll. This is a
user-visible mismatch with the mock and with the ruled layout.**
- Where: `frontend/src/estate/estateFinancials.css:67` (`max-height: 300px` at 390) together with `:8`
  (`min-width: 500px`), and the column percentages in `EstateFinancials.tsx` `RegisterTable`.
- What the captures show: both 390 states (`app-financials-positive.json` and `app-financials-partial.json`) record
  `registerTable clientH 300 / scrollH 345`, with only 2 rows.
  - In `financials-positive-390-app.png` and `financials-partial-390-open-app.png`, the cold row has a band of about
    100 px of empty space. The cause is that the hidden Basis / limit column is about 120 px wide and wraps the limit
    sentence and the Basis disclosure.
  - The EV row is cut off at the bottom of the scroll region.
- What the mock does: at 390 the mock shows three rows (97/97/79) with nothing scrolled.
- What the ruling says: closure 1, "Mock copy, navigation and measured layout", allows "a bounded internal list
  **after the measured three-row baseline**". Here the internal scroll starts before row two is fully visible.
- Related risk: the partial register at 390 measures 446 against its 448 cap with only two notes. Any third note
  (the `conflict` or `historical` RegisterNotes) would push it over the cap.
- Fix: shorten the rows at 390 so that the three-row baseline fits within the 448 cap.
  - For example, widen the narrow-table `min-width` toward the mock's 514 to 700 px scroll width, and give
    Basis / limit a wider share.
  - Keep the 448 cap.
  - Then recapture 390 in both states and assert, in `meetsMeasuredNarrowLayoutWithoutDocumentOverflow`, that the
    register table's `scrollH <= clientH` when there are 3 or fewer rows.

### Medium

**M1 - There is no review packet.**
- `.agent/W3-02-review-packet.md` does not exist at `5fe9d4b2`. The phase handoff is a running log, not a packet. It
  has no acceptance-criteria-to-evidence map for the task file.
- The task's required same-revision full real-Postgres suite is not recorded as run. Handoff line 11 says "Not run:
  the full real-Postgres suite". The coordinator says a run is in progress now, so its JUnit results
  (cases/skipped/failed) and wall time still have to be cited against `5fe9d4b2`.
- The Financials captures use the custom CDP script `capture-financials.mjs`. There is no line recording
  `tools/layout-evidence.mjs` as either run or `not run` with its blocking precondition.
- The c4-q3 two-line limitation appears only inside the capture JSON. It does not appear in any packet text.
- Fix: write the packet, covering:
  - the acceptance mapping
  - the full-suite citation for `5fe9d4b2`
  - the layout-evidence status
  - the c4-q3 limitation copy, verbatim
  - the 1440/390 mock and app rectangles (already in the JSON)
  - the residual risks listed below

### Low

- **L1 - The pending-rulings record is stale.**
  - Where: `.agent/W3-02-pending-rulings.md`.
  - What is wrong: c1-q1..q3, c2-q1..q8, c3-q1..q3 and c4-q1..q3 are not marked resolved, but the build spec contains
    rulings for them (sections c1 to c4). Only c3b-q1/q2 and c4-q4 are marked.
  - Fix: mark each entry resolved and cite the ruling section.
- **L2 - The Aggregation summary's accessible name does not contain its visible label (WCAG 2.5.3).**
  - Where: `EstateFinancials.tsx:318-321`.
  - What is wrong: the visible `Results (3) · No comparable total` is `aria-hidden`, so the name is only
    `3 grouping results. Comparable total unavailable for this selection.` A voice-control user saying "Results"
    may not match it.
  - Fix: keep the visible text exposed and append the full sentence as visually hidden text. This still meets c4's
    rule that the name states the full no-total meaning.
- **L3 - `Basis: 0 revisions` is visible by default.**
  - Where: `BasisDetails` (`EstateFinancials.tsx`), as seen on the cold row in every capture.
  - What is wrong: it reads as "no basis", and "revision" is system vocabulary on a default-visible line. The mock's
    column carries plain basis prose.
  - Fix: use a plain summary such as `Basis details`, or defer it to the W1 copy pass. This is a preference-level
    copy issue, not an acceptance gap.
- **L4 - A stale doc comment.**
  - Where: `frontend/src/ui/PageHeader.tsx:26,35`.
  - What is wrong: the comment calls the eyebrow "uppercase", but `primitives.css` sets `text-transform: none` (the
    c2 r1 L4 ruling).
  - Fix: correct the comment.

## Focus checks

1. **Commit 4 Financials page and shell (c4/c4b).**
   - Panel set, order and titles match v69 `globalfinancials` (`screens.js:528-532`), checked against
     `mock-globalfinancials-1440.png`:
     - eyebrow `Financials`, h1 and subtitle exact
     - status bar with the blue `Site-owned consequences` chip and its subcopy
     - `Consequence register`: the 6 mock columns in mock order, with the subtitle under the title
     - amber notice with the exact copy
     - `Aggregation rule` with the exact prose at 12px/21.6px
   - The closed `Results (N) · ...` disclosure is a single line. It opens unclipped, with list scroll equal to
     client height.
   - Every measured piece is within its maximum:
     - 1440: status 46, register 256 (positive) / 280 (partial), notice 43, aggregation 121
     - 390: status 69, register 403 (positive) / 446 (partial), notice 61, aggregation 186
     - document width equals client width at both widths, closed and open
   - No raw codes are shown. `PARTITION_INELIGIBLE`, the L3 differing-value copy and the L5 prior-mini-grid note are
     all in plain words.
   - Rail and route: `/financials` is live, the navigation-truthfulness rows are updated, and the registry and
     ledger entries (`I-estate-money-root`, `globalfinancials:1-2`) stay `gap` per c4-q2.
   - The honest two-line limitation (c4-q3) is recorded in both capture JSONs. No row is fabricated for KOBO.
   - Two small differences from the mock are not counted as slice findings: the notice has no info icon, and the
     status chip size differs slightly. Both come from the shared `Notice`/`StatusBar` primitives and look the same
     on the already-accepted Evidence and W3-01 screens, so they belong to the W1 UI pass.
2. **Net diff against main.**
   - 97 files. No `node_modules`, `dist`, `tsbuildinfo` or log files.
   - No `console.log`, `debugger`, `.only`, `breakpoint` or TODO additions.
   - The `.agent/W3-02-evidence/` serve and capture scripts are evidence tooling, kept in line with the earlier
     slices.
   - Shared edits are limited to `PageHeader` (eyebrow), `primitives.css`, `OperatorShellLayout` (two rail items
     made live), the `settled.ts` loading regex, the shell tests' rail pins and the two navigation guard fixtures.
   - Changes to W3-01 `estate/` (index, scope, composition, adapter) are the reviewed 0a/0c work.
   - Regressions: none observed in the W3-01 or W4-01/W4-02 frontend tests. The full frontend suite is green.
3. **Test-only fixture and the `ev_parsing` admission.**
   - The admission is exactly one (scenario ID, Site, seed) triple, `ev-complete-lab-002` / `EV-LAB-002` / `20518`.
     Every other ID keeps the `EV-LAB-001`/`20517` pin, and the definition carries the validated pair.
   - The fixture YAML is under `backend/tests/fixtures/w3/`. The second Foundation is test-only.
   - `backend/conversions/ev-lab-002-bindings.json` is labelled test-only and only tests reference it. No production
     code loads it.
   - These are acceptable as ruled (c3b, commit-3 r1 M2).
   - Residual risk: production `ev_parsing.py` now carries a test-only constant. The only effect is that a user
     scenario named `ev-complete-lab-002` must target `EV-LAB-002`.
4. **Review packet.** Missing, see M1.
5. **Unclassified builder readings.** None found.
   - The 0a readings 1-4 were classified in `W3-02-0a-review.md`.
   - The 0b and 0c readings were superseded by the 0b r1 and 0c r1 rulings, including the 0c "never pick a newer
     head" reading, which became `cold_heads_on(known_at=)`.
   - The commit-2 mapping gaps were ruled in c2d.
   - The c4 copy readings were ruled in c4-q1.
   - The commit-1 note that "two live reads at different cutoffs have different tokens" is informational and
     consistent with the token contract.

## Checks I ran (private worktree at `5fe9d4b2`)

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | Passed. The first attempt failed only because the worktree had no `.venv`; it passed once the repo venv was linked. |
| `tools/check-agent-workflow.ps1` | Passed. |
| `tools/check-all.ps1` | 11/11 passed. |
| `npx.cmd tsc --noEmit` | Exit 0. |
| `npm.cmd test` (in a worktree with no sandbox) | 102 files, 2435 passed, 326 s. This matches the handoff. |
| `npm.cmd run build` | Built OK. Only the usual chunk-size warning. |
| `pytest tests/test_w302_financials_links_postgres.py tests/test_w302_money_api.py tests/test_w302_money_comparability_postgres.py` on private DB `assetops_w302fin_test` (now dropped) | 21 passed, 314 s. |

About the earlier backend failures: my first attempts failed at import, and then 6 tests failed with the EV lab run
`FAILED`. The cause was my environment. The installed `gateway`, `simulator` and `contracts` packages point at the
stale main checkout. With all package roots of the worktree on `PYTHONPATH`, the W2-05b EV replay baseline passed 6/6
and the W3-02 files passed.

## Not verified

- The full real-Postgres backend suite at `5fe9d4b2`. It is running elsewhere, and I did not rerun it.
- The browser captures. I did not rerun them; the values above are the committed JSON and PNGs, which I read and
  viewed.
- `tools/layout-evidence.mjs`. I did not run it.

## Residual risk not in the handoff

- The register at 390 has 2 px of headroom. See H1.
- The three-row register density is still unproven, because no real W1 head exists in the capture seed. This is
  acknowledged in c4-q3.
