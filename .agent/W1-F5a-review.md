# W1-F5a review: Health, Asset, page titles, 390 rail

Reviewer: fresh independent Claude. Reviewed revision: `e84a3294` (code `e0815ac8`), base `4ea6c620`.

## Verdict: RETURN

There is 1 High and 1 Medium finding. Asset, the page headings, the 390 Menu rail, the registry gaps and the replaced assertions are acceptable.

## Findings

1. **High: the Health data-sources panel diverges from the mock's structure and is about 5x its height.** It is `frontend/src/sites/SiteHealth.tsx:466-600` (`SourcesBody`, `QualityCell`).
   - **What the mock shows.** `health:2` is a flat table with one row per source. Status is a single word ("Online", "Not connected"). Quality is a **chip** ("Gap", "None", "Good"). Above the table there is only a legend line.
   - **What the app does instead.**
     - (a) It doubles the rows. Every gateway gets a second "Device … as its gateway reports" row (`:545-575`), so 9 gateways become 17 rows.
     - (b) Status and Quality are prose. Status reads like "Disabled, not counted. Never received" or "Stale: nothing received for 16 min (limit 1 min); when it stopped is not known". Quality carries a second "Queue, as last reported … Storage …" line (`:587-`). As a result, rows are 2-3 lines at 1440 and tall wrapped rows at 390, where the source column wraps the mono IDs onto 2-3 lines (`health-kobo001-390-app.png`).
     - (c) The mock Quality chip is missing.
     - (d) There is a two-line contact summary and counts block (`:470-490`) above the table, which the mock does not have.
   - **Decision on deviation 2.** Nine real gateways is honest data and must not be truncated. Do not add a "latest N + Show all" cap, which could hide an attention row. The 5x height, though, does not come from the fixture's row count. It comes from (a)-(d). Nine single-line rows would be about 2x, which is acceptable for honest data.
   - **Fix:**
     - One row per gateway. Drop the device rows from the table. State the device count in the Source cell ("2 devices") and move per-device contact into the selected-gateway view (`?gateway=` / Details) or the Technical details disclosure.
     - Status: a short word with the age, on one line ("Current · 3 s ago", "Stale · 16 min", "Never received", "Disabled"). Move the limit and when-it-stopped text to the selected-gateway view.
     - Quality: a `Badge` chip per the mock ("Current", "Old", "Unknown age", "Nothing received"). Queue and storage go to the selected-gateway view or the disclosure. Keep the W1-UX-06 rule that an untrusted clock is "Unknown age", never "Old".
     - Order rows so the ones needing attention come first.
     - Shorten the contact summary to a single line (label plus counts). Remove the second sentence that repeats the label.
     - Re-capture at 1440 and 390 and record the new height ratio in the packet.

2. **Medium: the state is restated across the strip, panel and notice on both screens, which breaks "state line said once".**
   - **Health.** "The inputs needed to judge … battery condition are missing" appears in the strip (`healthHeadlines.tsx:212`), in the panel 1 lead (`SiteHealth.tsx:401`) and in the table's Main reason (`SiteHealth.tsx:431`). The strip `next` ("Open the battery to see what is missing", `:213`) duplicates the strip's own "Battery page →" action.
   - **Asset.** "Unknown does not mean normal, and it does not mean faulty" appears in the strip (`healthHeadlines.tsx:175`), the panel 2 lead (`SiteBattery.tsx:371-372`) and the notice (`SiteBattery.tsx:522`).
   - The mock strip is a chip plus a short scope. The contract places the prominent "Condition cannot yet be judged." in panel 1, so the strip should not also carry the full sentence.
   - **Fix:**
     - Health: change the `siteConditionWords` CONFIGURED sentence to "Unknown does not mean normal, and it does not mean faulty." and remove `next`. Change Main reason to a short "Inputs missing" variant, such as "Temperature, capacity and stress history missing" from `missing_causal_inputs`, or simply "See battery page".
     - Asset: remove the "does not mean normal… faulty" clause from the panel 2 lead (`SiteBattery.tsx:371-372`) and from the notice (`:522`), and keep it in the strip only. Remove the strip `next` "Add the missing inputs listed below." (`healthHeadlines.tsx:176`), because panel 2 is that list.

3. **Low: the KOBO-002 no-gateway case repeats itself.** The contact sentence and the counts line both say "No gateway is enabled for this site, so nothing is known…" (`SiteHealth.tsx:484`). Panel 1 says "no battery is part of this site's configuration" and then "Battery condition: Unknown (not configured)" (`:405`). **Fix:** in the counts line, show only the counts and the disabled note. Reduce `:405` to the "Battery page" link.

4. **Low: the packet's residual risk is wrong.** Without `matchMedia`, the 640px CSS still hides `.app-frame__rail-body` (`primitives.css:2838`) and no Menu button renders, so the rail is **unreachable**, not "stays visible". Every target browser has `matchMedia`, so this does not block. **Fix:** scope the hide rule to a class that is set only when the toggle renders (for example `.app-frame--rail-collapsible`), or correct the packet text.

5. **Low: the breadcrumb shows the raw site code "KOBO-001"** where the mock shows the site name. This is pre-existing and not in the diff. Carry it to F5b.

## Checks I ran
- `npx.cmd vitest run src/sites/__tests__/siteHealthBoundary.test.tsx src/shell/__tests__/operatorRailInventory.test.tsx`: 2 files, **47/47 passed** (26 + 21).
- `npx.cmd vitest run src/shell`: 49 files, **1141/1141 passed**, 101 s.
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-all.ps1` in the implementer worktree at `e84a3294`: **10/10 PASS**. That includes Dependency registry, Mock-gap catalogue, Missing-claim scan (35 tagged uses) and Screen ledger.
- Not rerun: the full `npm.cmd test`. I cite the implementer's run: 1988 passed, 1 known `siteFinancials` flake, 164 s, at `e0815ac8`. Layout evidence: I reviewed the 60-PASS captures but could not rerun them (they need Chrome, the backend and a dev server).
- Note: the `AssetOpsV1-gap-planning` worktree was switched to `plan/W2-02-q2` by another agent at 19:53:54. My test and tsc runs finished before then, on `e84a3294`. Its check-all result was discarded because it ran on the switched tree. This review is committed from a separate worktree, `AssetOpsV1-review-f5a`, so the other agent's tree is not disturbed.

## What passed
- **Panel set, order and titles.** Health and asset match v69 at 1440 and 390, with `expectV69Panels` covering stocked, empty and refused cases. `asset:3` uses the ruled title.
- **Contact and condition are separated.** Condition appears only in the strip and panel 1. Contact appears only in panel 2. The test at `siteHealthBoundary.test.tsx:465` asserts that the strip never mentions contact or gateways.
- **Asset.** The 4 metric cards, the pair and the 4-row limits table match the mock. Heights are 1.12-1.38x. The gaps (exposure, capacity test, RUL) are stated in place, and no simulated value is shown.
- **Disclosures and remnants.** Each panel has one disclosure. No answer-card h3s remain. Gateway external IDs are user-assigned source references marked vocabulary-exempt, and internal IDs appear only in Technical details.
- **390 rail.**
  - The button is a native `<button>` named "Menu" with `aria-expanded` and `aria-controls`, and it gets the global `button:focus-visible` style.
  - The rail closes on a `pathname` change, and a test proves it.
  - The Lab shell's S1-03 wrapping rules are kept intact.
- **Registry.** The 4 new gaps are consistent between `v69-dependency-registry-pilot.json` and `gapCatalogue.ts`, each is placed once through `MissingClaim`, and the checker passes.
- **Assertions.** The removed W1-UX-05 card assertions have equivalents in the rewritten tests:
  - delayed-old: "Old … reached the server 6 h after"
  - selected old / untrusted clock: "In contact; its latest report is old" and "…cannot be confirmed", never "old"
  - SOMETHING_NEW: confined to the disclosure
  - zero enabled: non-positive with a next step
  - refused reads: "As of: time not recorded"
  - battery missing inputs: one item per `missing_causal_inputs`
  - no healthy/RUL/warranty words

  No weakening found.

## Residual risk
- When finding 1 moves the per-device rows out of the table, the device-contact assertions (`siteHealthBoundary.test.tsx:186-202`) need to follow those rows to their new home, not be deleted.
