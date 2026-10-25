# Post-W6 W4-mini pre-flight (no code)

Read-only on main `ba971d96` (`AssetOpsV1-plan2`). Shell, W1-a, W1-b and W3 are merged. W2-EV, W2-cold and W6 are not. Card: `.agent/post-W6-audit/fix-slices.md:131-149`. Ledgers: batch-12 (42 pairs) and batch-13 (54 pairs), 96 pairs in total. Paths are under `frontend/src/` unless stated. MP = `sites/MiniPerformance.tsx`, SAF = `shell/SiteAnalyticsFrames.tsx`, SWC = `sites/siteWorkCases.tsx`.

Merged duplicates widen two IDs:
- R309 also covers B14-04 (cold tones on cooling, cold-health, cold-scenarios and cold-work).
- R322 also covers B15-03 and B15-04 (cold-work-* and cold-action) and B17-03 (ev-work-*). See classification.md:291, 307-309 and 340.

## (a) Build plan per D3

### R309 / B12-02: tones on renewable, service, fuel and backup
**Today**
- Every chip is `Badge tone="neutral"`.
- The only tone class is `.mini-tone--amber`, which colours text only (`sites/w4-mini-performance.css:2`). `muted` is applied (MP:392) but has no CSS rule.
- Decision chips emit `mini-decision--*` (MP:645, 1010, 1622) with no CSS behind them.
- `ValueBars` has no tone; its fill is always `--series-1` (`ui/ProductStatus.tsx:334`, `ui/primitives.css:4329`).

**Mock** (`mockups/v69/index.html` l.444-448 and 615-632)

Strip badges:
- Renewable: Watch is amber and "Lens: Opportunity" is green.
- Fuel: evidence-limited is amber.
- Service and backup: grey.

Decision chips: Eligible green, Excluded grey, Limited amber.

Bars:
- Renewable: Available PV amber #d9a346, Retained margin grey #99a5b7, Usable headroom green #409985.
- Service: Clinic (critical) red #c15d5d, Grain mill green.
- Unknown values are hatched (already built).

Metric cards stay untoned.

**Change**
- Add a `tone` prop to `ValueBars`, with series tokens added to `ui/tokens.css`.
- Map tones from stored enums only:
  - envelope `status` (`miniDepthClient.ts:76`)
  - `RenewableRow.decision` (:99)
  - `ServiceRow.role` CRITICAL (:118)
  - `BackupRow.result` (:184)
- Reuse the mock badge palette. `cold-tone--*` in `sites/w2-cold-site.css:141` already matches it but is scoped to `[data-cold-view]`. Promote it to a shared `badge--green|amber|red` set or add `mini-tone--*` rules. **Q2** decides which.
- Colour is never the only signal: the chip text stays.

**Tests:** add tone class assertions per enum to the four `mini*Routes.test.tsx` files, plus a CSS source assertion for each token.

**Recapture:** all 42 batch-12 pairs.

### R310 / B12-03: renewable confidence chip
- Insert "Confidence: Not assessed" in `RenewableStatus` between the status Badge (MP:391-395) and Lens (MP:396). This follows W4-02 build spec l.51: confidence stays not assessed until an approved rule exists.
- The mock shows "Confidence: Medium" (a dashed `conf-chip` with a popover, l.260 and 279). A Medium value would be a D1.
- Reuse the opportunity chip shape (`MiniOpportunity.tsx:141-143`) as a neutral Badge.

**Tests:** in miniRenewableRoutes, the chip renders in every state, refused included (see R313).

### R311 / B12-04 and R321 / B13-03: refusal copy keyed on the error code
`decisionRefusalCopy` (`sites/miniDecisionsClient.ts:168-176`) maps HTTP status only.
- Every 409 says "The evidence changed. Reload this page." That includes `PERFORMANCE_CUTOVER_CLOSED` (`backend/assetops_backend/mini_decisions_api.py:140`), where a reload cannot succeed.
- Every 422 and 503 says "Decisions are unavailable right now. Try again."

`DecisionRead` already carries `code` and `message` (:163), so the copy can key on them:

| Code | Copy |
| --- | --- |
| `PERFORMANCE_CUTOVER_CLOSED` | not-at-this-cutoff sentence, no Reload |
| `DECISION_BASIS_CHANGED` | keep "evidence changed / Reload" |
| `INVALID_KNOWN_AT` | "Choose a valid evidence cutoff." (wording from `estate/estateClient.ts:372`) |
| `INVALID_WINDOW` / `INVALID_CURSOR` | specific sentence |
| 503 | "unavailable right now. Try again" |

The exact copy is **Q4**.

Callers:
- SAF:1194 (opportunity)
- `MiniOpportunity.tsx:399` (CTA) and its hard-coded duplicate at :366
- `MiniAlternatives.tsx:184`
- `MiniScenarios.tsx:300`, which currently passes the server 4xx message through at :297-300. **Q5**.

**Tests:** a code-by-copy table in `miniDecisions.test.tsx`. No raw code appears on screen.

**Recapture:** alternatives (all three 409 cases), opportunity refused-bad-known-at, renewable w403.

### R312 / B12-05: renewable recurrence wording
- The strip fact `Solar headroom on N of M assessed days` (MP:380-383) and the card "Recurring opportunity N / M days" (MP:442) skip the Q19 five-complete-day rule.
- `recurrenceText` (MP:598-604) applies the rule only in the chart note.
- Change: route the strip fact and the card through `recurrenceText`'s predicate. When it fails, the strip says "Recurrence is not established for this selection." and the card value is "Not established". Confirm Q19 still holds (**Q6**).
- The strip's "Not assessed · No selected assessment" beside populated cards is the currentness badge (MP:405, `CURRENTNESS_WORD.UNKNOWN` at MP:237). Hide that badge when rows are selected, or reword it to name the missing scope. **Q6**.

**Tests:** 3-of-3, 5-of-5 and gap-limited cases.

### R313 / B12-06: refused window on the four screens
- `MiniRefusal`/`refusalCopy` (MP:259-289) replaces the whole body after the period bar. It shows one sentence for every `INVALID_WINDOW`, and the backend sends a single message (`backend/assetops_backend/mini_depth/read.py:57`).
- Change: keep the page frame, as W2-cold Q4 does for cold depth:
  - a refused strip with the status, confidence chip and "Window cannot be read";
  - the tile row as muted "Not assessed" MetricCards;
  - one in-panel gap.
- Reuse the cold `RefusedStrip`/`RefusedTiles` (`sites/coldSiteViews.tsx:406-427`). They are private, so export them or lift them to a shared module. That file is a W2-cold edit target (**Q11**).
- Distinct copy can come from the client, because it knows the requested from/to. No backend change is needed:
  - renewable over 5 days: "Choose one to five complete Site-local days."
  - service/fuel/backup not one hour: "Choose one complete Site-local hour (or one day)."
  - reversed: "The end must be after the start."

**Tests:** 6-day, 2-hour and reversed fixtures per screen, with panel count > 0.

**Recapture:** refused-invalid ×4 ×2 widths.

### R316 / B12-09: service duplicate heading
- Drop the `ValueBars title` figcaption "Delivered power by addressed load" at MP:949. The mock has no figure title there (l.617).
- Keep an accessible name on the figure through `aria-label`, using the panel heading MP:939 "Where the power went".

**Tests:** in miniServiceRoutes, the heading text occurs once.

### R318 / B12-11: card headline size and unequal heights at 390
- `MetricCard` values are 27/24px, and `--word` values are 17px (`ui/primitives.css:4505-4519, 4730`).
- Service passes no `word` for "None seen in measured intervals" (MP:918), so it wraps at 24px. Fuel and backup mix 17px and 24px within one row.
- The mock uses the large size for all of these.

**Change**
- Pass `word` consistently for non-numeric values on all four screens. Word values in a row use one size.
- Add `align-items: stretch` with equal minimum heights per row through `.mini-cards-bound` (`sites/w4-mini-performance.css:167, 220-230`). Do not touch the global MetricCard, which has all-screen reach.

**Tests:** CSS source assertion and word-prop assertions.

### R320 / B13-02: mini Site Work window in Site time
- Mini incident rows call `eatWindowText` (SWC:223-230), which hard-codes UTC+3.
- Several other places print UTC:
  - the WindowForm inputs (SWC:305-324)
  - the "based on" Window fact through `workUtcText` (SWC:458-461)
  - the HISTORICAL label (SWC:349)
- Cold and EV use `siteWindowText(row.occurred_at, cells.site.timezone)` (SWC:780, definition :236-253).
- The timezone reaches the mini branch from SAF:2270, but `cells` is null for MINIGRID (SWC:1093-1096, `DOMAIN_CASE_SITE_TYPES` :110).

**Change**
- Pass `site.timezone` into the mini branch and replace `eatWindowText` with `siteWindowText`.
- The facts become Site-local primary, with the exact UTC in a disclosure or title (Time-basis ruling, fix-slices:223).
- The date inputs become Site-local days. The URL stays UTC.
- Make `siteWindowText` delegate to `sites/siteTime.ts`, per W1 cross-card contract 1 (one formatter). **Q8**.

**Tests:** Addis vs UTC, local midnight boundary, missing zone falls back to labelled UTC.

**Recapture:** sitework-incidents and maintenance, all cases. Cold/EV regression because SWC changes.

### R322 / B13-04: refused Site Work (shared with cold and EV)
Today:
- `Refused` shows the raw server `message`, backticks included (SWC:430-431).
- The strip shows `WORK_COUNT_UNKNOWN` "Count unknown · work source unavailable" (SWC:199, 383) on an input error.
- The Work subrow shows "(—)" (SAF:2163, nulls from `useWorkCounts` :2085-2134).

Change:
- Map the 422 codes to plain copy keyed on `code`, with no server text. The reversed and over-31-day sentences are client-side.
- On a 422, the strip says the window is invalid rather than "source unavailable".
- Subrow counts drop the "(—)" suffix (label only) when the count is null because of input. Keep "(—)" for a genuine source failure? **Q9**.
- B15-04 cold-action is a different mount (`SiteWorkActions.tsx`). **Q10** decides whether it is in reach.

**Tests:** in siteWorkCases, coldWorkCases and evWorkCases: reversed, 36-day and 503 copy, plus the absence of backticks.

### R324 / B13-06: clamped Decision context and narrative
- `.work-cases-clamp` and `.work-cases-context` apply a 2-line clamp (`sites/w4-work-cases.css:69-84`). Full text exists only in `title`, which is unreachable by touch or keyboard.
- Cold and EV already have a "Read full text" disclosure (SWC:672ff).
- Change: give mini rows the same disclosure (progressive disclosure, WCAG 2.2 1.4.13/2.1.1), or remove the clamp on mini. **Q12**.
- The clamp class is shared, so do not alter cold/EV CSS.

**Tests:** a 160-character narrative is reachable via the disclosure.

### R325 / B13-07: Scenarios table cap and window control
- `.mini-scenarios-table .data-table__scroll {max-height:144px}`, and 188px at ≤600 (`sites/w4-mini-decisions.css:13, 112`). Row 2 is hidden. These caps came from the W4-03 u9c placeholder.
- Change: remove the inner cap and let the table grow to the panel cap (**Q13**).
- Add a compact page-local Window control mirroring R88/R112 (`DomainWorkWindow`, `sites/SiteWorkActions.tsx:767`) after the subtabs. Scope today comes only from the URL (SAF:1242-1251, `MiniScenarios.tsx:277-280`). This needs a register row (**Q14**).

**Tests:** two-row and five-row fixtures fully visible; window form submits a UTC URL.

### R328 / B13-11: Alternatives crumb and route header
Current state after W1-a:
- crumb "Findings › Finding code unavailable › …" (`FINDING_CODE_UNAVAILABLE` SAF:626, :897)
- subtitle "{site} · generator support finding" (SAF:917, already R389)
- Open site is present (SAF:921-931); no Site tabs (:936-943); money aside removed (:952-954)

Remaining D3: the crumb. Change it to show the Finding's public code when the Finding read resolves, matching the mock "Findings › F-104 › Alternatives". The code is "Finding" only on refusal.
- The subtitle and the mock question are covered by R389 (D1). The money tab and Open site are already resolved. Confirm R328's remainder (**Q15**).

**Tests:** in miniDecisions: resolved code, refusal and no-revision.

**Recapture:** 3 alternatives cases. Populated geometry uses a pure selected-row test (producer gap table, fix-slices:237).

### R331 / B13-15: opportunity subtitle
- `V69Layout.tsx:317` claims "an explicitly authored scenario" unconditionally (SAF:1170).
- Change: branch on `opportunity.scenario_id` (`miniDecisionsClient.ts:118`; `MiniOpportunity.tsx:159` already branches). Use the mock question "Can recurring renewable headroom support useful additional demand?" (mock l.731) with no scenario claim, or a conditional clause. **Q16**.

**Tests:** linked vs unlinked.

### R333 / B13-18: Site tab row at 390 hides Overview
- `useCurrentTabInView` (`ui/useCurrentTabInView.ts:8-21`) shifts `scrollLeft` in `OperatorSiteTabs` (`shell/operatorSiteTabs.tsx:103-126`).
- The CSS is `.site-tabs__list{flex-wrap:nowrap;overflow-x:auto}` (`ui/primitives.css:321-329`).
- W6 Q9 asks for the same wrap rule as R364: up to 760px, wrap with complete labels, no inner scroller, `UnavailableTab` untouched.
- This is one shared component for every mini, cold and EV Site page, so reach is app-wide (**Q17**).
- Change: a `@media (max-width:760px)` wrap on `.site-tabs__list`, and the hook is skipped when the list wraps.
- `operatorSiteTabs.tsx` also receives W2-EV's href override, so rebase after W2-cold.

**Tests:** extend `shell/__tests__/operatorSiteTabs.test.tsx` with a CSS source assertion and a no-scroll-mutation case.

### Recapture inventory
- All 96 indexed pairs, both widths, at the current SHA:
  - renewable/service/fuel/backup: 42
  - sitework-incidents and maintenance, scenarios, alternatives, opportunity-finding: 54
- Cold/EV Work case regression pairs, because SWC changes.
- R333 reach representatives (**Q17**).
- Five-row 160-character DOM probes for every capped panel.
- Capture gaps to log:
  - populated Alternatives
  - five long Work rows (no producer mode offers them)
  - scenarios 503
- Producers: the W4-02 seed (`.agent/W4-02-evidence/seed.py`) and the W4-03 walkthrough (`tools/w403_mini_decisions_walkthrough.py`). Both are `*_test` DBs.

## (b) Architect questions (one batch)

1. **Scope of the merged duplicates.** R309 absorbs B14-04 (cold tones) and R322 absorbs B15-03/04 and B17-03 (cold/EV Work refusal). *Default:* W4 fixes R322 in shared SWC, so cold-work-* and ev-work-* inherit it, and W4 recaptures them. R309 stays mini-only. Cold already has `cold-tone--*` matching the mock, and B14-04 screens are W2-cold/W5-cold surfaces: W4 lands the shared tokens and W5-cold applies them.

2. **R309 tone mechanism.** *Default:* promote the mock badge palette (green/amber/red/grey) to shared `badge--{tone}` tokens in `ui/tokens.css`. Map tones only from stored enums (status, decision, role, result). Add a `tone` prop to `ValueBars`. Text always accompanies colour. Pattern: semantic status colours (Carbon/Atlassian status tokens; WCAG 1.4.1 use of colour, 1.4.11 contrast ≥3:1 for bar fills). `muted` gets a real grey rule.

3. **R309 bar colours with no stored driver.** The mock colours fixed series: PV amber, margin grey, headroom green, mill green, clinic red. *Default:* map series colour to role only. Critical load is red, because `role=CRITICAL` is stored. Headroom is green, PV amber and margin grey, as fixed series semantics rather than claims. Grain mill uses the default series colour unless a stored classification exists, so we don't imply a judgement. Register this as D1 if the Architect prefers the mock's exact palette.

4. **R311/R321 copy table.** *Default* (plain-language error messages, GOV.UK "error messages" pattern: say what happened and what to do, never a code):

   | Code | Copy |
   | --- | --- |
   | `PERFORMANCE_CUTOVER_CLOSED` | "Decisions for this cutoff are closed. Choose a later evidence cutoff." (no Reload) |
   | `DECISION_BASIS_CHANGED` | "The evidence changed. Reload this page." |
   | `INVALID_KNOWN_AT` | "Choose a valid evidence cutoff." |
   | `INVALID_WINDOW` | "Choose a valid Site-local window." |
   | `INVALID_CURSOR` | "This page of results expired. Go back to the first page." |
   | `DUPLICATE_KEY` / `CORRECTION_CONFLICT` | "This change was already recorded. Reload this page." |
   | 503 | "Decisions are unavailable right now. Try again." |

   Confirm the wording and the `PERFORMANCE_CUTOVER_CLOSED` semantics.

5. **Scenarios server-message pass-through** (`MiniScenarios.tsx:297-300`). *Default:* replace it with the same code table. No server text on screen.

6. **R312 recurrence.** Does Q19 (five completely assessed days, or "Recurrence is not established for this selection.") still hold for the strip fact and the "Recurring opportunity" card? *Default:* yes. The card value reads "Not established" with note "Needs five completely assessed days". The currentness badge "No selected assessment" is hidden when any day row is selected, or names the scope, e.g. "2 of 5 days not selected".

7. **R313 refused layout.** *Default:* follow W2-cold Q4 for consistency (persistent page structure with an inline error, NN/g heuristic 9 and GOV.UK error-summary pattern):
   - keep the period bar, a refused strip and muted "Not assessed" tiles;
   - one in-panel message;
   - distinct client-computed sentences for over-5-days, not-one-hour and reversed windows (copy in the plan above);
   - no backend change.

   Confirm W4 may export cold's `RefusedStrip`/`RefusedTiles` (see Q11) or should build mini-local equivalents.

8. **R320 formatter.** *Default:* `siteWindowText` delegates to `sites/siteTime.ts` (W1 contract 1). Mini Work shows Site-local window text with the zone label, and the exact UTC in the existing "UTC and IDs" disclosure (R323). Date inputs are Site-local days, with UTC kept in the URL. Missing zone falls back to explicit "UTC" text. Does W4 own the delegation edit to `siteWindowText`? It is used by cold/EV, so cold/EV need regression recapture.

9. **R322 counts on input error.** *Default:*
   - strip: "Counts not shown: the selected window is not valid." in place of "Count unknown · work source unavailable";
   - subrow tabs show the bare label without "(—)" on a 422;
   - keep "Count unknown" and "(—)" for genuine 503 or unavailable.

   Pattern: don't present a system failure for a user input error (NN/g heuristic 9).

10. **B15-04 cold-action reach.** That refusal is in `SiteWorkActions.tsx`, not SWC. *Default:* out of W4. W5-cold-Work fixes it with the same copy table, and the register row cites R322.

11. **Shared-file overlap with W2-cold.** W2-cold edits `coldSiteViews.tsx` (Q4 refused strip) and the cold timezone formatter. *Default:* W4 rebases after W2-cold (already ordered) and then lifts `RefusedStrip`/`RefusedTiles` into a shared `ui/RefusedWindow.tsx` that cold imports. W2-cold's behaviour is unchanged. Alternative: mini-local copies, with no cold edit.

12. **R324 clamp.** *Default:* reuse the cold/EV "Read full text" disclosure on mini rows. A clamp plus an explicit disclosure is a modern truncation pattern, while `title` alone fails WCAG 2.1.1 and 1.4.13 on touch and keyboard. Keep the shared clamp CSS unchanged. The all-open state is exempt from caps.

13. **R325 Scenarios cap.** *Default:* delete the 144/188px inner cap (placeholder-derived, hides rows). Panel caps follow Lesson 15: measure five 160-character rows at the final SHA, provisional cap `ceil(peak×1.15/50)×50` (the W6 Q15 formula), Architect ratifies before merge. Fallback is an inner scroll only with an obvious bounded region (visible scrollbar or edge fade, keyboard focusable `tabindex=0` with label, never hiding row 2 at the default page size). Confirm W4-03 u9c's 348/391 panel caps are retired.

14. **R325 window control.** *Default:* add a compact page-local Window control on mini Scenarios, mirroring R88/R112 (`DomainWorkWindow`), after the subtabs. Register a new D1 row extending R88/R112 to `scenarios`, rather than editing those rows. Should cold/EV scenarios match later (W5)?

15. **R328 remainder.** After W1-a, only the crumb remains: "Finding code unavailable" where the mock shows F-104. *Default:* show the resolved Finding public code, with "Finding" on refusal, matching W1 Q16. The subtitle stays under R389 and the money tab and Open site are closed. Confirm R328 closes on the crumb alone.

16. **R331 subtitle.** *Default:* use the mock question "Can recurring renewable headroom support useful additional demand?" for every state. It makes no claim, so no branch is needed. Alternative: branch on `scenario_id` and add "with an authored scenario" only when linked.

17. **R333 tab wrap reach.** `OperatorSiteTabs` is one component on every Site page, so the W6 Q9 wrap rule changes all Site tab rows at 390.
    - *Default:* apply it globally in `ui/primitives.css` (≤760px wrap, complete labels, no inner scroller) and disable `useCurrentTabInView` scroll when the list wraps. Pattern: Material 3 / GOV.UK tabs, where on small screens tabs stack or wrap rather than hide; WCAG 1.4.10 reflow.
    - Recapture representatives: one 390 pair per distinct Site tab row (mini Performance, Findings, Financials, Work, Foundation; cold and EV overview) plus every W4 screen.
    - Is the visual departure from the mock's single-line row a D2 needing a register row and visible label? *Default:* no label. R364 set no label for the equivalent WR wrap. Confirm.

18. **Missing caps (Lesson 15).** The docket has only `sitework-incidents` Incidents at 1440 (500). *Default:* for every other W4 named panel at each width, set the provisional cap from the final SHA's largest closed case, using a five-row 160-character probe in each variable field, with `ceil(peak×1.15/50)×50`. Record peak, cap and producer, and the Architect ratifies before merge. This covers the renewable windows table, service loads, fuel bridge, backup chains, Incidents at 390, Maintenance, Scenarios, Alternatives and the Opportunity cards. User-expanded all-open is exempt but must not clip. If over cap: wrap first, then paging, then an obvious inner scroll. Never hide rows. If none preserves content, return the fixture for revision. The existing W4-02 bounded budgets (`sites/w4-mini-performance.css:178-203`) stay unless a probe fails. Should R332's 443px measurement be the 1440 floor?

19. **Producer gaps.** *Default:* no new producer modes.
    - Populated Alternatives: pure selected-row test (fix-slices:237).
    - Five long Work rows and Scenarios rows: capture-only DOM probe (W6 Q15).
    - Mini 503 states: component tests only.

    All three are logged as capture gaps.

20. **Backend.** *Default:* none. All distinct copy keys on existing `code`, or on client-known from/to. Confirm W4 must not add a detail sub-code to mini `INVALID_WINDOW` (`backend/assetops_backend/mini_depth/read.py:57`).

21. **Cross-card overlaps.** *Default:*
    - Rebase after W2-cold and own only the mini hunks of SAF: subtitle, alternatives crumb, Scenarios window mount, Work subrow counts.
    - W2-EV's `operatorSiteTabs.tsx` override is kept intact.
    - W5-cold-Work and W5-EV-Work rebase onto W4 for SWC (serialize SWC edits per fix-slices:7).
    - W6 is independent except for the shared tab-wrap CSS. Whichever lands second reuses the first's rule.

    Confirm W4 may land before W6 and that W6 then reuses the global `.site-tabs__list` wrap rather than its own `globalWork.css` rule.

22. **Register numbering.**
    - Main's highest row is R395. R396 is reserved for W6, and W6 takes R397 onward for any further rows.
    - *Default:* reserve **R400–R404** for W4 so it cannot collide with unmerged W6 rows. Candidates:
      - R400: D1 Scenarios Window control (Q14)
      - R401: D1 renewable confidence "Not assessed" vs mock "Medium" (R310)
      - R402: D1 bar series colours, if Q3 departs
      - R403: tab wrap D2, if Q17 needs a label
      - R404: spare
    - D3 rows R309–R333 close in place.
