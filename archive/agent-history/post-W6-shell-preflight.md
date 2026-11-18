# post-W6 shell-typography-copy: builder pre-flight

Branch `task/post-W6-shell` from main `aa08d16d`. This is a dry read of the card (`post-W6-audit/fix-slices.md` §shell-typography-copy), register rows R115–R319, the batch ledgers and v69. No product code has been written. All paths are under `frontend/src/` unless noted. Mock references (`v69 Lnnn`) point to `frontend/mockups/v69/index.html`.

Each question below has a recommended default (**Default:**). I start code only after the rulings merge.

## A. Card-level gaps

**Q1. The "Panels and order" list does not match the IDs.** It looks generated from the batch-01 screens and misses two of the card's own IDs:
- `action-overview/plan/execution/evidence/history` (R203, B4-03).
- The cold/EV Work screens that inherit R319 through the shared `siteWorkCases.tsx:373`: `cold-work-incidents`, `cold-work-maintenance`, `ev-work-incidents`, `ev-work-maintenance`.

It also lists panels that no D3 here changes, such as "Effect on readiness and confidence" and "Connected sources".

**Default:** the affected-screen set is the 9 listed screens + 5 action-* + 4 cold/EV Work = 18 screens. Panels listed without a matching ID are regression-only.

**Q2. The Files list does not match the work.**
- Needed, but not listed:
  - `ui/primitives.css`, `ui/tokens.css`, `ui/Badge.tsx`, `ui/V69Layout.tsx` (Notice/KeyValues)
  - `shell/SitesFrame.tsx`, `shell/SiteFoundationFrame.tsx`, `shell/SiteAnalyticsFrames.tsx`, `shell/SiteHealthFrames.tsx`, `shell/SiteEvidenceFrame.tsx`
  - `sites/SitesIndex.tsx`, `sites/StoredFoundationViews.tsx`, `sites/FoundationRevisionPanel.tsx`, `sites/SiteSingleLineDiagram.tsx`, `sites/SiteFoundationChange.tsx`, `sites/SiteBattery.tsx`, `sites/LedgerSiteEvidence.tsx`
  - `sites/verificationClient.ts` (read only, if Q14 = plan read)
- Listed, but no ID needs them: `sites/domainActionClient.ts`, `sites/EvHealthDepth.tsx`, `work/globalWorkParts.tsx`, `work/WorkRequestOverview.tsx`, and `App.tsx`, which is routing only.

**Default:** the corrected list above. Do not touch the four unneeded files, which W5/W6 own. `OperatorShellLayout.tsx` and `WorkspaceShellLayout.tsx` are probably untouched too, since the R115 fix is CSS-only.

**Q3. Some IDs mix D3 and non-D3 sub-items.** The classification says multi-observation rows "use the disposition that gates the screen". The ledger proposals split these sub-items out:

| ID | Sub-item | Proposed disposition |
| --- | --- | --- |
| B1-06 | Missing sites/sld/changes callouts | D4 |
| B1-14 | Chip wording | D4 |
| B1-16 | Subtitle | D4 |
| B1-21 | Part links | D2 |
| B1-22 | Row count | data |
| B1-55 | Plan values | D1 if they are not on the DTO |
| B1-66 | Refusal structure | Accepted W1-F5b pattern |
| B1-66 | Generic h1 | D4 |
| B2-21 | Missing-gap row | D1 |

**Default:** fix only the D3 parts named in §B. For each excluded sub-item, add a `MOCK DEVIATION Dn` label plus a register row only when the Architect confirms it. Otherwise leave it unchanged and list it in the packet's Known Deviations. I will not invent register rows.

**Q4. The card's "States" line asks for "UTC/EAT" on every screen.** Only R170 (evidence-analysis) has a time-basis change in this slice.

**Default:** apply the time-basis ruling (Site timezone primary, UTC in a disclosure) to the evidence-analysis records table only. Do not sweep other screens; their time basis belongs to their seam cards.

## B. Target behaviour per ID

**Q5. R115 / B1-02: tall dark band on short 390 pages.**
- Cause: at ≤640px, `primitives.css:2911` makes `.app-frame--operator` a single column without `grid-template-rows`. `.app-shell` is `min-height:100vh` (`:73`) and `.app-frame` is `flex:1` (`:92`), so the leftover height stretches the side row.
- Mock: white topbar, no dark band (`v69 L4-L6`).
- **Default:** add `grid-template-rows: auto minmax(0,1fr)` (or `align-content:start`) to the 640px rule, so the band holds at 92px on every page.
- Out of scope: replacing the dark rail with a white topbar at 390. That is R114 (D1, no topbar).

**Q6. R119 / B1-06: closing callout.**
- Mock: `notice blue`, 11px, bordered (`v69 L4`, `L180`).
- App primitive: `V69Notice` blue (`ui/V69Layout.tsx:171`, `.v69-notice` `primitives.css:4686`).
- **Default:** convert the readiness closing note (`StoredFoundationViews.tsx:1005`, unboxed `<p class="note">`) and the changes page-end note (`SiteFoundationChange.tsx:374`, left-bar `notice--info`) to `V69Notice` blue, keeping the app's copy.
- Do not add the mock's sites/sld/changes callout texts. They assert illustrative facts (D4). The asset callout stays as R147 (D1).
- To confirm: the readiness copy stays the app's existing sentence rather than the mock's L427 sentence. The mock's sentence is true of the app, so adopting it is an option.

**Q7. R120 / B1-07: 14px body text where the mock uses 11–12px.**
- Mock: `.prose` 12px/1.8, `.notice` 11px, `table` 11px; root is 14px (`v69 L3-4`).
- **Default:** apply `.v69-prose` (12px, `primitives.css:4703`) to these named paragraphs:
  - sites empty (`SitesIndex.tsx:148-157`)
  - reserve-form intro (`FoundationRevisionPanel.tsx` ~528)
  - asset refusal sentences (`SiteBattery.tsx:229-270`)
- The SLD unknown-part notice (`StoredFoundationViews.tsx:145`) and the readiness note become `V69Notice` at 11px.
- No global `body`/`p` font-size change. That would hit every screen and every seam.

**Q8. R125 / B1-14: green "Demonstration data" chip.**
- Mock: `badge('Simulated','purple')`, #f0eafa / #725094 (`v69 L4`, `L407`, `L420`).
- **Default:** retone `--badge-provenance-*` in `tokens.css:106-108` to the mock purple. This is one token change, so every use follows: `StoredFoundationViews:566`, `SitesIndex:556`, `SiteDetails:334`, `SiteConfiguration:430`.
- Keep the class name `badge--provenance`, so `sharedVisualVocabulary.test.tsx:175` still passes. Keep the wording "Demonstration data" (wording is D4).
- Risk: cold R235 already renders purple through `.prov-tag`. Check that no cold/EV screen relies on the green provenance badge.

**Q9. R127 / B1-16: missing root breadcrumb on Sites.**
- Mock: "Sites ›" crumb above the h1 (`v69 L1117-1125`).
- **Default:** render `<Breadcrumbs trail={[{label:"Sites"}]}/>` in `shell/SitesFrame.tsx`.
- The subtitle stays "Every site configured in this build." (D4, true of the build). To confirm: whether the Architect wants the mock subtitle, which is neutral copy and not a false fact.

**Q10. R129 / B1-21: topology bus colour and icons.**
- Mock: `.plant-bus` border-top 3px #6ca99a; single centred node icon #348a75 (`v69 L418-421`).
- App: `primitives.css:2773` uses `var(--accent)` (blue).
- **Default:**
  - Add a token `--plant-bus: #6ca99a` and use it.
  - Centre the icon row (`.plant-card__icons`, `:2762`).
  - Keep the paired icons and underlined part links (D2, `?component` carry).
- To confirm: whether "single centred icon" is part of the D3 or rides with the D2 links.

**Q11. R130 / B1-22: Identity panel layout.**
- Mock: `.key-values`, 11px, right-aligned `dd`, row rules (`v69 L185`, `L4`).
- App: `FactList` (left-aligned, no rules, `overflow-wrap:anywhere`) breaks `KOBO-001` into `KOBO-/001`.
- **Default:**
  - Switch `IdentityPanel` (`StoredFoundationViews.tsx:516-585`) to `KeyValues` (`V69Layout.tsx:102`, `.v69-key-values`).
  - Keep all 10 stored rows (data; no row hidden).
  - Make `code` values `white-space:nowrap`, with wrapping only at token boundaries.
- Also stop the Topology panel stretching to the Identity row height: `align-items:start` on that grid.

**Q12. R133 / B1-25: no-version h1 shows "KOBO-001".**
- Cause: `shell/SiteFoundationFrame.tsx:267` passes `siteName={siteId}`; `knownSiteName` (line 199) is already in scope. The skeletons around line 300 have the same problem.
- **Default:** use `knownSiteName ?? siteId` for foundation and readiness (one branch).
- The ledger also asks whether the name must come from the Foundation version instead, which would make it D1. Default: use the Site read's `display_name`, which is stored and current.

**Q13. R140 / B1-43: SLD at 390 (952px drawing in a 316px scroller; mock scales to fit).**
- The SVG already has a viewBox (`SiteSingleLineDiagram.tsx:678-692`). `tools/checks/shell-overflow.ps1:44` requires `.sld__scroll` to keep its declared inline overflow.
- **Default:** keep the `.sld__scroll` region and its `overflow-x:auto`, so the guard is untouched. Give the SVG `width:100%; height:auto; max-width:<W>px` and drop the fixed width/height attributes, so it scales to the column like the mock (`v69 L15`, `L833`).
- Readability risk: labels shrink to about 0.33×, roughly 4px text. Alternatives:
  - (a) Scale only down to a floor (e.g. `min-width:560px`) and scroll beyond that.
  - (b) Full scale-to-fit, as in the mock.
- Recommend (b) for mock fidelity. The selected-part box below the drawing still carries the readable names. Needs ruling.

**Q14. R141 / B1-55: "Set in the plan" where a frozen plan exists.**
- The change DTO (`actionClient.ts:274-296` `PolicyChange`) has no target or guardrails. `VerificationPlan` (`verificationClient.ts:106`, target `:131`, guardrails `:132`) does.
- **Default:** when `planId` is present, read the frozen plan via the existing verification-plan client.
  - Render the target as stored, and guardrails as "{n} required" from the guardrail count.
  - On read failure or pending, fall back to the existing "Set in the plan" text plus a short "not available yet" note.
  - No backend change.
- If the Architect prefers no new client read in a shell slice, re-dispose as D1 with a label instead.

**Q15. R151 / B1-53: raw UUID and failure codes.**
- `SiteFoundationChange.tsx:256` and `:353` show `Battery <uuid>`. Lines `610-628` render `failure_code` raw.
- **Default:**
  - Show the battery by its stored asset name/label when the DTO or Foundation read has it. Otherwise show "Battery", with the UUID moved into the existing technical-details disclosure.
  - Map failure codes to plain text:
    - `ACTION_FOUNDATION_STALE` → "The site configuration changed before this was applied"
    - `ACTION_VALUE_INVALID` → "The proposed value was outside the allowed range"
    - `ACTION_EFFECTIVE_TIME_INVALID` → "The effective time was not valid"
    - Unknown codes → "The attempt was refused"
  - Keep the raw code inside the disclosure.
- This affects `siteAction.test.tsx:553,575`. Default: keep those tests by asserting the code inside the disclosure. Literals need confirmation.

**Q16. R152 / B1-54: breadcrumb leaf.**
- "Change" at `SiteAnalyticsFrames.tsx:1757`; "Change & effect" at `:1787`. Mock: "Sites › Kobo Mini-grid › Foundation".
- **Default:** use "Sites › {site} › Foundation › Change & effect" on both routes, linking Foundation. The leaf is consistent and the mock's Foundation section is kept.
- The note style is handled in Q6.

**Q17. R149 / B1-66: asset refusal (D3 part only).**
- **Default:**
  - Typography: 12px prose (Q7).
  - The 369px band is fixed by Q5.
  - The unknown-Site single panel ("Site not found", `SiteAnalyticsFrames.tsx:161-172`) stays as the shared SiteScoped refusal. The 3-slot structure is the accepted W1-F5b pattern, and changing SiteScoped hits every site route.
  - The generic h1 "Battery" stays (D4).
- To confirm: R149's D3 is typography only.

**Q18. R170 / B2-21: evidence-analysis records time column.**
- Mock: "Measured (EAT)", `HH:MM:SS` site-local (`v69 L363`, `L360`). App: `LedgerSiteEvidence.tsx:1388` "Taken", `:1412` `when()` → `readableTime` (always UTC, with date).
- **Default:**
  - Thread `site.timezone` from `SiteEvidenceFrame.tsx:119-140` into `LedgerSiteEvidence`.
  - Header: "Measured ({tz abbreviation, e.g. EAT})".
  - Cell: site-local time with seconds.
  - Add the date only when the record's local day differs from the selected day.
  - Exact UTC instant goes in a `title`/disclosure, per the time-basis ruling.
- Reuse the `siteWindowText` / `localTimeOf` pattern (`siteWorkCases.tsx:231`, `miniDepthClient.ts:307`); no new formatter module.
- Breaks `v01bEvidenceVisual.test.tsx:231` ("Taken"). Update it.
- The "Missing / Inspect the gap" row and the external-link marker are out of scope (D1).

**Q19. R203 / B4-03: Action breadcrumb.**
- `SiteAnalyticsFrames.tsx:1659-1668` builds a Finding-rooted trail. The mock is Action-rooted: "Actions › ACT-048 › Overview · site: Kobo Mini-grid" (`v69 L1121`).
- The cold/EV `DomainActionShell` (`:1424-1445`) already renders this shape (R342).
- **Default:**
  - Reuse that crumb markup: Actions (`/actions`) › `action_code` (from the W1 action read) › section, plus a "· site:" link.
  - Overview is the leaf on the overview view.
  - If the W1 action read lacks `action_code` before load, render the crumb after the read settles.
- To confirm: `/actions` is the W3-01 estate index route, so it is a valid link target.
- Cross-seam: W1-mini-Action-a/b own `SiteAction.tsx` but not `SiteAnalyticsFrames.tsx`. Overlap is low.

**Q20. R319 / B13-01: "1 incidents" / "1 maintenance".**
- `siteWorkCases.tsx:373`, nouns at `:148` and `:163`. The mock does not pluralise either, but "1 incidents" is wrong English.
- **Default:**
  - Lift a `plural(count, one, many)` helper (one exists locally at `LedgerSiteEvidence.tsx:86`) into a small shared copy util.
  - Wording: "1 incident" / "{n} incidents". "Maintenance" is a mass noun, so it reads "1 maintenance case" / "{n} maintenance cases".
- Updates `siteWorkCases.test.tsx:332,366`, `coldWorkCases.test.tsx:193`, `evWorkCases.test.tsx:134,241`.
- To confirm: the maintenance noun. The alternative is to keep "maintenance" for all counts ("3 maintenance").

## C. Cross-seam files

**Q21. `siteWorkCases.tsx` is also in W4-mini, W5-cold-Work and W5-EV-Work. `SiteAnalyticsFrames.tsx` hosts the W1 Action routes (W1-mini cards).**

**Default:**
- In `siteWorkCases.tsx`, touch only the count-strip line and the noun table. That is a few lines, merged first; the later cards rebase.
- In `SiteAnalyticsFrames.tsx`, touch only the W1 Action crumb and the change crumb.
- The token/CSS changes are global by intent: Q5 rail rows, Q8 provenance token, Q10 bus token.

## D. Tests likely to break

**Q22.** Expected breakage:
- R319: `sites/__tests__/siteWorkCases.test.tsx`, `coldWorkCases.test.tsx`, `evWorkCases.test.tsx`.
- R170: `shell/__tests__/v01bEvidenceVisual.test.tsx`.
- R151: `sites/__tests__/siteAction.test.tsx`, if it reads failure codes off the change screen.
- Q11: Foundation identity tests that query the `FactList` structure (`foundationScreen.test.tsx`, `siteFoundationRevision.test.tsx`).
- Q16 crumb: tests matching the leaf "Change".
- "Demonstration data" tests should survive Q8 because the class name is unchanged.

**Default:** update the assertions to the new literals. Add focused tests for:
- singular/plural count
- the site-local time column and its UTC disclosure
- the Action-rooted crumb
- the no-version h1 display name
- plan target/guardrail rendering, with pending and failure fallbacks
- plain-language failure codes
- the 640px grid rows (class/CSS presence only, since jsdom has no layout)

## E. Caps

**Q23. The docket has no rows for this slice's mini screens:** `sites`, `foundation`, `readiness`, `sld`, `asset` (1440), `changes` (1440), `evidence-analysis` (mini), `sitework-*` (mini), `action-*`. It does have rows for asset Interpretation 390 (500), changes Change-and-effect 390 (800), and the action-* panels.

Likely misses:
- **(a) mini `evidence-analysis` "Accepted records…"**: observed 436/629, and record-opened 910/1235, against the cold rows' 450/800. The site-local column will not shrink it.
- **(b) foundation Identity panel with 10 rows in `KeyValues`**: likely taller at 390 than today's FactList.
- **(c) SLD at 1440**: unchanged (1.63×). At 390 it shrinks under Q13(b).
- **(d) action-* panels**: unaffected (crumb only).

**Default:**
- Undocketed panels: the closed height must not grow above the frozen `fddf5cad` measurement plus 10%. For (a), use the cold `evidence-analysis` caps, with record-opened treated as a user-expanded state (exempt).
- Request explicit Architect caps for mini evidence-analysis and foundation Identity before merge, sized from five 160-character rows.

## F. Recapture plan

**Q24. "All 87 baseline screens" against 1414 indexed pairs from 60 producer invocations.** A greedy cover of the frozen `audit-index.json` shows that **21 producers reach all 88 captured screen IDs**:

Greedy cover, in order (batch: producer → new screens):
b1 v01a (6), b2 renamed-s5 (6), b4 s601b (6), b6 cold excursion (6), b7 b07 seed (6), b8 ev interrupted (6), b3 s408 owner (5), b9 b09 seed (5), b10 w301cap (5), b13 w403 (5), b16 w504 (5), b12 w402r (4), b14 w502 (4), b18 w502 (4), b11 w302 serve (3), b15 w502 (3), b17 w504 (3), b19 w601 detail (3), b3 s404 (1), b5 s602b (1), b5 s603 (1) = 88.

Each batch folder already has a `capture-bNN.mjs` and target JSONs.

**Default, tiered:**
- **(1) Shell-wide, because Q5/Q7/Q8 touch every screen:** one representative case per screen at 1440 and 390, i.e. 174 pairs. That is the index's own `minimum_pairs`, produced by those 21 producers through each batch's existing capture script, with targets filtered to the first case per screen.
- **(2) Directly changed screens:** every indexed case. That is 230 pairs across the 18 screens in Q1, including all refusals, singleton counts, no-version and unknown-id cases, and the UTC/EAT evidence days.
- Put both under `.agent/post-W6-shell-recapture/`, with an index that records the new SHA and per-panel closed heights against caps.
- `cold-finding-excursion` stays with the W2-cold recapture, per the ruling.
- Alternative, if the Architect insists on the full 1414-pair rerun: about 60 producer runs. Recommend against it. Cases 2..n on unchanged screens differ only in data, which this slice does not touch.

**Q25. Capture-only clicks.** **Default:** no clicks are needed for this slice's cases. Any disclosure-open state (e.g. the UTC disclosure, R170) is captured as a recorded viewer-state pair under the ruling.

## G. Guards

**Q26.**
- `shell-overflow.ps1` (`.sld__scroll` region) is preserved per Q13.
- No guard pins the provenance colour or the rail grid. I will check `tools/checks/*` for `badge--provenance`, `.plant-bus` and `app-frame--operator` rule pins before editing.
- **Default:** no guard is loosened. If a guard pins the old values, I extend it to pin the new ones and prove that it fails on the old value.
