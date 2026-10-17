# W1-F3 findings + money: independent review

Reviewer: fresh Claude reviewer (not the author). Revision reviewed: `a5e961fc`. The last code commit is `d79a9705`. Base: `4002b1ad` (merge-base with main).
Inputs: the packet, `architect-W1-fidelity.md`, `W1-F1-handoff.md`, the frontend diff, and the round-2 captures in `.agent/W1-F3-evidence-height2/`.

## Verdict: RETURN

The panel set, order and titles match v69 on all six screens. The money gates are unchanged. The tests are green.

The rework still fails in three ways:
- It hides material limits behind a closed expander.
- It omits mock summary columns and chips that the contract says must appear as honest unknowns.
- It leaves the recurring F2/F4 defects: the same state line repeated, duplicate disclosures, raw IDs, and a contradictory line.

Most of the remaining over-1.3x height comes from these defects, not from honest-state content that has to stay.

## Checks run (by me)

- `npx.cmd tsc --noEmit` passed: exit 0.
- `npx.cmd vitest run` passed: 7 files, 284 of 284 tests, 36.7 s. The files were `w1f3PanelGuard`, `panelStructure`, `siteFinancials`, `siteFinding`, `siteFindingEvidence`, `siteFindingHistory` and `s404SiteFindingIndex`. Vitest ran in this sandbox.
- I did not run the full suite or the production build. I cite the implementer's 2014/2014 at `08979345`. The final code revision `d79a9705` is CSS and copy only, and its full-suite result is not recorded.
- I did not rerun layout evidence. The packet records it at `cbf8819a` (288/288 claims). It was not re-captured at `d79a9705`, and the packet says so.

## Money and assertions

- The gates are unchanged:
  - `shown` and `gated` in `FindingConsequence.tsx:699-701` are identical to the base.
  - `BridgeTable current` is passed only for `stepHead`. A pinned version always gets `current={false}`.
  - The per-finding history list that carried `hideAmounts` was removed, not loosened. The site-wide Interpretation history uses the server's `recorded_amount.disposition`.
  - NO_PRICE and CONFLICT are kept in `SiteFinancials.tsx:580-612` and `:947-960`.
- I found no weakened assertion. Hidden rows stay mounted inside `<details>`.
- `expectV69Panels` runs on every route, with stocked, empty, pending and refused variants. Sitefindings is checked by a 6-state `it.each` (s404:428). The guard's non-vacuity is checked for all six screens.

## Findings

1. **High: material limits hidden in a closed expander.** `frontend/src/sites/SiteFinding.tsx:771-786` (`LimitList`, `LIMITS_SHOWN = 3`).
   - Only the first 3 limits show; the rest sit behind "Show all N limits". The hidden part can include read limitation groups (`groups.map`, :718), the stop-bridge caveat ("this joining rests on those two off reports", :729-735), and the recurrence caveat.
   - The contract says: "A closed disclosure cannot hold substantive method or hide a material limit … Keep material limits visible beside the claim."
   - Fix:
     - Always render, visibly: the bounded line, the record gap, the series limit, every `groups` item, the stops and the recurrence.
     - Put only the development-access note and the SUPPORTED lifecycle sentence behind the expander, or drop the expander and shorten each limit to one sentence.
     - Add a test with a fixture of 3 or more limitation groups, a series limit and stops, and assert that every one is visible.

2. **High: mock summary columns and chips missing; the contract requires honest unknowns.**
   - Sitefindings, `SiteFindingIndex.tsx:410-414`:
     - The mock columns are Finding, Domain, Priority, Confidence, State, Main consequence and Lens. The app has Finding, Period, State, Main consequence and Related.
     - The contract row for `sitefindings` says: "Unsupported priority/confidence chips are honest unknown."
     - Fix: add Priority and Confidence columns showing a muted "Not assessed" badge, and a Domain column with the supported domain ("Dispatch"). Lens can wait for F5. Keep Period, but drop Related into the Finding cell's second line (see 6).
   - Finding status strip:
     - The mock has Priority, Confidence, State, Claim and Lens chips. The app has no Priority or Confidence chip.
     - Fix: add a "Priority: not assessed" and a "Confidence: not assessed" muted chip to the strip.
   - Financials bridge table (`FindingConsequence.tsx`, BridgeTable header) and the strip:
     - The mock has a Confidence column and a "Data confidence" strip chip. The app has neither.
     - Fix: add a Confidence column with "Not assessed", and a matching strip chip.

3. **High: Interpretation history price versions are a list; the mock uses a table.** `SiteFinancials.tsx:716-744`.
   - The mock's Interpretation history is a 5-column table (Version, Fuel price, Maintenance, Provenance, Status). The fuel-cost rows are already a table (`ConsequenceHistory.tsx`). The price versions, which are what the captured cases show, render as an `<ol>` of prose lines with links.
   - This is a form mismatch, and it is the main cause of the 1.55-1.59x height.
   - Fix: render price versions as a `DataTable` with these columns, one line per row:
     - Version
     - Diesel price
     - Effective
     - Set by / why, with the correction reason in a `td small`
     - Status: a badge, plus "Open version N" as the one link
   - Move "Prices as recorded then" into the row's exact-reference disclosure.

4. **Medium: the state, period and version are repeated across the strip and panels.**
   - Finding (`SiteFinding.tsx:574-577`, `FindingStateLine`):
     - The strip says "Using the latest checked readings · Latest version (2 of 2) · period".
     - The What happened panel repeats all three, and the period appears 4 times (description, strip, state line, sentence).
     - Fix: inside the panel keep only the source-unverified clause and the as-of. Drop the label, version and period, which the strip and description own.
   - Financials bridge (`FindingConsequence.tsx:789-795`):
     - "Not measured fuel saved / not a measured saving" appears 5 times: the metric note, the state line, the "Modelled potential fuel-cost exposure" line, the basis cell and the Trade-offs "Limits of this figure".
     - The withheld case says "This is not zero" 4 times and gives the reason twice (state line and "Why no current amount").
     - Fix: delete the "Modelled potential fuel-cost exposure…" line (:789). Delete "Why no current amount" when the state line already gives the reason (:794). Keep the caveat once in the panel and once in Trade-offs.
   - Finding History (`SiteFindingHistory.tsx:217, 360`, and the state line):
     - "Latest version recorded when read" is said 3 times, and "3 recorded versions" twice.
     - Fix: make it one line, "Version 3 of 3 (latest when read) · As of … · Keep this exact version". Drop the completeness sentence when all versions are listed. Keep `[data-history-incomplete]` only for the incomplete case.
   - Finding Evidence state line:
     - "Latest recorded version, opened by its exact reference" and "Version 1" each appear twice.
     - Fix: keep one sentence.
   - Sitefindings (`SiteFindingIndex.tsx:399`):
     - "No amount is shown in this list" appears in each row's cell, in the in-panel note, and in the trailing notice.
     - Fix: delete the in-panel note at :399 (the cells and the notice remain). Delete "Showing 3 of 3." (:571) when all rows show. Hide the "Days in this window" strip (:321) when the window is one day, because the Period column already names it.

5. **Medium: duplicate disclosures.**
   - Financial assumptions has two "How this was worked out" disclosures in one panel (captures `assumptions*`, around `SiteFinancials.tsx:770-800` and the price-detail disclosure).
   - Finding Evidence has two: the bundle (`SiteFindingEvidence.tsx:244`) and the lineage.
   - Financials has three: "How this was worked out" in the bridge and in Assumptions in use, plus "How the range is worked out" in Trade-offs (`FindingConsequence.tsx:388`).
   - Fix:
     - Financial assumptions: merge into one per panel.
     - Finding Evidence: drop the lineage one, or fold it into the bundle's.
     - Financials: move the range method and "Generator power readings counted" (:402) into the bridge's single disclosure. This also brings Trade-offs (1.39x) under 1.3.

6. **Medium: raw backend IDs in the default view.** `SiteFindingEvidence.tsx:701-705`.
   - The bundle's Source column shows truncated UUIDs ("52c37a02", "1c2599a0, 37807b48, 3e175755"). The mock shows source names.
   - Fix: show the configured source or device label if the read has one. Otherwise show "Source not named" (or "3 sources"), with the IDs only in the exact-reference disclosure.

7. **Medium: contradictory line in Interpretation history.** `ConsequenceHistory.tsx:60-62` (`RECORDED_WORDS`).
   - When there are no fuel-cost rows, the state line says "Every amount here is shown as it was recorded…". The next line says no fuel cost version was recorded.
   - Fix: when `body.rows.length === 0`, use a state sentence such as "No fuel cost version recorded by this moment; prices below are prices only." Fold the empty line and the prices-only clarifier into it, so it is one line.

8. **Medium: Finding Evidence lineage at 1.75x is cuttable.** `SiteFindingEvidence.tsx:266, 530`.
   - "Every one of the N cited records traces to …" restates the bundle headline ("N cited records, each traced back to its accepted record").
   - "Choose a record's reference in the evidence bundle" points at references that sit in a closed disclosure.
   - The panel head carries two links.
   - Fix:
     - Keep the step line and any broken-step line.
     - Delete the :530 sentence when the trail is complete.
     - Reword :266 to "Open 'How this was worked out' above and choose a record to follow its trail".
     - Keep one head link.

9. **Medium: sitefindings rows at 390.** Capture `part9/sitefindings-390-app.png`.
   - Each row is about 170 px tall, with blank space in the visible columns, because the off-screen State and Related cells wrap.
   - The 1440 capture also shows "Version" and "4" split across two lines (fixed by `d79a9705`, not re-captured).
   - Fix: give the State caption and Related cell `white-space: nowrap` or a min-width, or move Related under the Finding title (as in 2). Re-capture at 390.

10. **Low: missing space before a disclosure.** `ProductStatus inline` plus `SourceProvenanceNotice` render "…shown.Source record for this finding version" and "…equipment.Source record…". A following line also starts with a stray "· Finding version …".
    - Fix: add a leading space, or a separator before the disclosure summary. Do not start the bound line with a separator when it wraps.

11. **Low: inaccurate packet claim about the Assumptions notice.** The packet says the notice follows its pair "as in mock siteAssumptionsScreen". The mini `assumptions` mock (screens.js:338) puts the notice first. That notice is mock-only meta, so putting the app's notice after the pair is defensible. Correct the packet wording.

## Height cases (about 1.3x rule): keep versus cut

| Case | Ratio | Must stay | Exact cut |
| --- | --- | --- | --- |
| finding-history, -latest | 1.63 / 1.95 | the version table, the incomplete line (when incomplete), the no-replay line, shortened | Finding 4 History: one state line, and drop the completeness sentence when complete. Per row, drop "Open this version", which duplicates "Select version N". Merge "Check their record trail · Times and references" into one inline link. Drop the panel-head links, which duplicate the row links. |
| finding-evidence lineage | 1.75 | the step line, broken steps | Finding 8. |
| finding-evidence bundle | 1.44 | the table, the gap line, the demonstration note | Finding 4 (one state sentence) and Finding 6 (Source column becomes one line). |
| assumptions Interpretation history | 1.55-1.59 | the empty and prices-only fact, the price versions | Findings 3 and 7. Drop "Showing 3 of 3 versions." |
| assumptions Financial assumptions | 1.38-1.59 | the fields, the in-use line, the disabled edit with its reason | Finding 5 (one disclosure). Drop the uppercase "SELECTED: …" eyebrow sentence: the selected version is already in the field note "Version 1 · First price". Keep "Back to current prices" as a link in the state line. |
| sitefindings | 1.51 | the rows and the gap note in the cells | Finding 4, sitefindings part. |
| financials-withheld bridge | 1.54 | the withheld state, the series-limit bullet, the record link | Finding 4, Financials part. |
| financials-priced Trade-offs | 1.39 | When shown / Not included | Finding 5 (move the two disclosures into the bridge). |
| finding-stale limits | 1.40 | every material limit (Finding 1) | Shorten each limit to one sentence rather than hiding any. Height must not be bought by hiding limits. |

## Residual risk not named in the packet

- After Finding 1 is fixed, limits-heavy versions will exceed 1.3x. That is honest content. Record those as accepted overages, and do not hide them.
- The full suite was not run at the final revision `d79a9705`. It is CSS and copy only, but the s404 and siteFoundationChange flakes recur under load.
