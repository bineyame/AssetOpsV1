# W1-F5a review packet: Health, Asset, page titles, 390 rail

Branch `task/W1-F5a-health-shell` (worktree `AssetOpsV1-review5`), from main `4ea6c620` + brief `098c05d9`. Frontend only. Not merged.
Brief: `.agent/W1-F5a-build-brief.md`. Contract: `.agent/architect-W1-fidelity.md` (`health`, `asset` rows; F5 row). Carries 1 and 5 of `.agent/W1-F5-carries.md`.

## Outcome
- **health** rebuilt to v69: status strip (asset condition only, the one state line) → **Physical asset condition** → **Data sources · data quality, not equipment condition** → blue notice. The W1-UX-05 `HealthHeadline` answer card and the four old panels (gateway contact, queue/storage, device contact, battery condition) are gone; their content is merged into the two mock panels.
  - Panel 1: prominent "Condition cannot yet be judged.", the mock's 7-column asset table (Asset, Assessment, Evidence, Main reason, Open findings, Open work, Open) for the configured battery (Unknown; findings/work "Not recorded"), and other assets as a catalogued gap.
  - Panel 2: contact summary words (W1-UX-06 non-positive rules kept) + counts line, the selected gateway (`?gateway=`) inline, and the mock's 5-column table (Source, Status at HH:MM UTC, Quality, Affects, Open), with one row per gateway and one per device source. Contact (server receipt) is in Status. Reported fact age, queue and storage are in Quality. Affects is "Not recorded". Technical details: one closed disclosure.
- **asset** rebuilt to v69: status strip ("Cannot yet be judged" + "Capacity: unverified") → 4 mock metric cards (Reserve exposure / Thermal exposure / Power stress / Usable capacity) → pair(**Observed reserve and power exposure**, **Interpretation and next evidence**) → **Condition evidence and its limits** (4-row mock table) → notice. `BatteryHeadline` removed.
  - The heading follows the mock: the battery name, then "Battery · 200 kWh nominal · site: …".
  - Refusal (404/409/422/unrecognised condition): the strip gives the refusal state. A `page-refusal` follows, and the three panel skeletons each hold an in-panel gap.
- **Gaps stated, not filled**: four new `mock_gaps` + mirror entries, each placed once through `<MissingClaim>`:
  - `G-health-asset-inventory` (other assets' condition)
  - `G-asset-battery-exposure` (SOC/power exposure history)
  - `G-asset-capacity-test` (capacity test action)
  - `G-asset-remaining-life` (RUL/replacement date)
- **Carry 1, page headings**: Health uses `SitePageHeader` (site name, provenance badge, "Health · site-level asset-condition summary"). The changes are:
  - Site Findings, Financials and Assumptions now use `SitePageHeader` (new `SITE_SCREEN_DESCRIPTIONS` keys). Before, each showed a generic "Findings"/"Financials" h1.
  - Finding subtitle: the raw site code is dropped.
  - Action subtitle: the raw "SYSTEM demonstration" enum is dropped.
  - New helper `siteSourceModeLabel` (badge mode without needing a full site summary).
- **Carry 5, 390 rail**: at ≤640px the operator rail collapses behind a **Menu** button. Before, it stacked about 600px above the content.
  - The button has `aria-expanded`/`aria-controls`, and the rail closes on navigation.
  - The button is rendered only at that width (`matchMedia`), so desktop adds no control and the existing "no form controls" guards are unchanged.
  - The Lab shell keeps its S1-03 wrapping row.

## Files materially changed
- `frontend/src/sites/SiteHealth.tsx`, `SiteBattery.tsx`, `healthHeadlines.tsx` (cards removed; `siteConditionWords` added)
- `frontend/src/shell/SiteHealthFrames.tsx`, `SiteAnalyticsFrames.tsx` (headings), `OperatorShellLayout.tsx` (Menu)
- `frontend/src/sites/siteViewModel.ts` (`siteSourceModeLabel`)
- `frontend/src/ui/V69Layout.tsx` (descriptions), `gapCatalogue.ts`, `primitives.css` (health patterns; 640px operator rail block)
- `frontend/docs/architecture/v69-dependency-registry-pilot.json` (4 gaps), `frontend/src/test/v69PanelTitles.ts` (see deviation 1)
- Tests: `src/sites/__tests__/siteHealthBoundary.test.tsx` (rewritten to the panels), `src/shell/__tests__/operatorRailInventory.test.tsx` (+2)

## Acceptance (brief scope)
| Item | Status |
| --- | --- |
| health panels/order/titles per v69 | Met. `expectV69Panels("health")` passes in the stocked (KOBO-001), no-gateway (KOBO-002), none-registered, selected-gateway, unknown-gateway, refused source-health (404/503/409/401/403) and refused-battery variants |
| asset panels/order/titles per v69 | Met, with one proposed plain-language title (deviation 1). `expectV69Panels("asset")` passes stocked, channels-not-set-up, foreign (404), invalid (422), 409 and unrecognised-condition variants |
| Source contact separate from condition | Met. Condition comes only from the battery read (strip + panel 1). Contact sits only in panel 2. A test asserts that the strip never mentions contact or gateways and that panel 1 holds no gateway, queue or source row |
| Battery condition/capacity test/RUL stated honestly | Met: catalogued gaps plus the read's named missing inputs. Metric cards show "Not available"/"Unknown"/"Unverified" |
| Carry 1 headings | Met for Health, Asset, Site Findings, Financials, Assumptions, Finding/Action subtitles. Finding child views: see deviation 3 |
| Carry 5 rail at 390 | Met. Capture `health-kobo001-390-app.png` shows the collapsed rail with Menu. Tests prove open, keep destinations and close-on-navigate |
| Planted-panel failure | Done on commit `914adc6f`. A planted `<Panel heading="Planted panel">` in both screens failed 11 tests ("panel structure of v69 screen health/asset"), then the plant was reverted with `git checkout`. Menu guard: removing close-on-navigate failed the new test, then reverted |
| Pre-review self-check | State line once (asserted: one `[data-product-status]`, in the strip). One disclosure per panel (asserted). No answer-card h3s. Raw codes only in disclosures. Mock rows/columns present ("Not recorded" where no read). No horizontal overflow at 390. Height table below |

## App-vs-mock panel height (evidence.json, rev `e0815ac8`)
| Screen / case | Panel | 1440 app / mock (ratio) | 390 app / mock |
| --- | --- | --- | --- |
| health KOBO-001 | Physical asset condition | 253 / 285 (0.89) | 377 / 442 (0.85) |
| health KOBO-001 | Data sources | 1411 / 285 (**4.95**) | 1767 / 391 (**4.52**) |
| health KOBO-002 | Physical asset condition | 197 / 285 (0.69) | 297 / 442 (0.67) |
| health KOBO-002 | Data sources | 304 / 285 (1.07) | 458 / 391 (1.17) |
| asset KOBO-001 | Observed reserve and power exposure | 399 / 316 (1.26) | 330 / 274 (1.20) |
| asset KOBO-001 | Interpretation and next evidence | 399 / 316 (1.26) | 435 / 316 (1.38) |
| asset KOBO-001 | Condition evidence and its limits | 358 / 287 (1.25) | 478 / 428 (1.12) |
| asset refusal | each panel (gap only) | 103-126 / 287-316 | 126 / 274-428 |
| sitefindings (heading check) | Findings list closed | 325 / 288 (1.13) | 439 / 460 (0.95) |

## Checks run (final code revision `e0815ac8`)
- Targeted: `siteHealthBoundary.test.tsx` 26/26; `operatorRailInventory` 21/21; all of `src/shell` 1139/1139 (after carry 5).
- `npx.cmd tsc --noEmit`: clean.
- Full `npm.cmd test` on the final revision `e0815ac8`: 76 files, **1988 passed, 1 failed**, 164 s wall. The failure was `siteFinancials` "pins the selected version into the address when the link named none", a known-flake file. Rerun alone twice, it gave **75/75 passed** both times. An earlier full run on `91247a6f` gave 76 files, 1989 passed, 163 s.
  - Known flake `siteFinancials` S4-08 "reloads page one… (typed 409)": failed in a targeted batch and passed when rerun alone.
- `tools/check-all.ps1`: 10/10 guards PASS on `e0815ac8` (Missing-claim scan: 35 tagged uses).
- Evidence: `node tools/w1-fidelity-evidence.mjs .agent/W1-F5a-evidence …` on API 9605, web 6005, CDP 9607 (S7-01 walkthrough fixture `assetops_s701_owner_f5a`, delivered right before capture). Result: **60 PASS / 0 FAIL**, rev `e0815ac8`.
  - Pairs: health KOBO-001, health KOBO-002 (no gateway), asset KOBO-001, asset refusal (KOBO-002 foreign ID), sitefindings heading, each at 1440 and 390.
  - Side-by-side page: `.agent/W1-F5a-evidence/index.html`.
  - Afterwards the fixture DB and work dir were dropped and the servers stopped.
- The captures found a real defect: a visually hidden `th` overflowed at 390 (`innerWidth 543`). It was fixed in `83d4cfa4`. Tall wrapped rows at 390 were fixed by giving the tables a scroll min-width (`d54e6757`, `e0815ac8`).

## Known deviations
1. **`asset:3` title.** "Condition evidence and claim boundary" contains "claim", which is on the W1 vocabulary list. Both the product vocabulary scan and the W1 scan failed on it.
   - Following the F2 `evidence-analysis:2` precedent, I added a **proposed** `APPROVED_TITLE_CHANGES["asset:3"] = "Condition evidence and its limits"`, marked pending the coordinator's ruling.
   - If it is rejected, revert that entry and the `ASSET_PANELS[2]` string and accept a vocabulary exemption instead.
2. **Health data-sources height is 4.5-5x the mock.** The mock has 3 rows. The walkthrough fixture has 9 gateways (8 deliberate S7 cases plus one disabled) and their device rows, so the panel shows 17 rows.
   - Per-row density is mock-like: one line at 1440, scrolling at 390. KOBO-002 is 1.07x.
   - I did not hide rows to meet the ratio, because the rows are the read's real sources. The reviewer should judge from the capture.
3. **Finding child views** (`finding-evidence`, `finding-history`, recommendation) keep their h1 "Finding evidence"/"Finding history". The mock uses the finding name.
   - Those views receive no finding title, and F3 (in review) is rebuilding them. The change is left to F5b to avoid conflicts. Changes/Work headings are F4's.
4. **Registry**: 4 `mock_gaps` entries added (the contract says the registry and its checker stay unchanged). F3 set the precedent of adding gaps for its screens. `check-all` registry/catalogue guards pass.
5. **Removed W1-UX-05 card assertions.** These covered the "N of M gateways need attention" headline, the two value-bar lanes and the battery step strip. They tested the answer cards the contract removes, so they were replaced with equivalent assertions on the strip, contact line, selected line and attention list. The W1-UX-06 non-positive and unknown-age semantics are all still asserted.
6. The 390 tabs wrap to two rows, where the mock scrolls them. Tab treatment is F5b scope.

## Residual risk
- `SiteAnalyticsFrames.tsx` and the registry `mock_gaps` list will conflict textually with F3/F4 at merge (different hunks; append-position conflict in the registry).
- The Menu control depends on `matchMedia`. If it is absent, the button is not rendered, but the 640px CSS (`primitives.css:2838`) still hides `.app-frame__rail-body`, so the rail is unreachable (corrected in the fix round; the review's L4). Every target browser has `matchMedia`, so this does not block.

## User review
No owner review per slice (W1 walkthroughs deferred to the combined owner walkthrough after F5). Coordinator ruling needed on deviation 1. Independent fresh-Claude review next.

## Fix round (review RETURN: 1 High, 1 Medium, 3 Low)
Code `6cf0692c`; base review revision `e84a3294`.

| Finding | Fix |
| --- | --- |
| H1 Health data-sources panel | One row per gateway (9 rows, no cap). Source cell gives the device count ("2 devices"). Status is a short word with age ("Current · 5 s ago", "Stale · 10 min", "Never received", "Disabled"). Quality is a `Badge` ("Current", "Old", "Unknown age", "Nothing received"; an untrusted clock stays "Unknown age"). Rows needing attention come first, then current, then disabled. The device rows, queue and storage moved to a "what each gateway last reported" table in Technical details (`HealthReportedDetail`; keeps `data-health-queue-row` and `data-health-source`). The selected-gateway view gains a Queue row. The summary is one line: label plus counts (the sentence is kept only when no gateway is enabled, so that its next step stays) |
| M2 state said once | Health strip is now "Unknown does not mean normal, and it does not mean faulty." with no `next`. The Main reason cell says "See battery page". Asset: the clause is removed from the panel 2 lead and the notice, and stays in the strip; the strip `next` is removed. New test counts "does not mean normal" once per screen |
| L3 KOBO-002 repeats | Counts line no longer repeats the no-gateway sentence. The panel 1 not-configured line is just the "Battery page" link |
| L4 matchMedia note | Packet residual-risk text corrected (above). The CSS was not changed |
| L5 breadcrumb | Out of scope, carried to F5b |

### Re-pointed assertions (none weakened or deleted)
- Row wording ("Current: received 5 s ago", "Stale: ... (limit 1 min)", "Old: observed 6 h ago; it reached the server 6 h after", "Unknown age: the gateway's clock is off by 95 s ...", "Nothing received yet"): the short forms are asserted on the row (status and quality cells). The long wording is asserted on `[data-health-reported]` rows. The stale limit, "when it stopped is not known" and "Disabled (not counted)" are asserted in a new selected-gateway test.
- "Disabled, not counted." on the row: the summary's "1 disabled, not counted" is asserted, and "Disabled (not counted)" in the selected view.
- "Gateway contact: not all current / no enabled gateway / not recognised": the label ("Some gateways are not in contact.", "No gateway is reporting.", "not recognised") is asserted. Those prefixes were the second statement of the label.
- "No gateway is enabled ... about contact": now "... about source contact." (the headline sentence; the duplicate counts-line copy is gone).
- "Unknown (not configured)" under panel 1: replaced with the lead text "No battery is part of this site's configuration" plus the link. The review asked to remove the duplicate line.
- Technical-details `aria-current` lookup now targets `[data-health-technical]`, because the reported table also marks the selected row.
- New tests: 9 rows, no device rows in the table, attention first, disabled last, device count, Quality chip per row.

### Checks (final fix revision)
- `npx.cmd tsc --noEmit`: clean. `siteHealthBoundary` 29/29. `src/sites/__tests__` 20 files, 740/740.
- Full `npm.cmd test`: 76 files, **1992 passed, 0 failed**, 133 s. No known flake appeared.
- `tools/check-all.ps1`: 10/10 PASS.
- Evidence: `tools/w1-fidelity-evidence.mjs` on API 9606, web 6006, CDP 9607 with a fresh S7-01 fixture (`assetops_s701_owner_f5afix`): **60/60 claims pass**, no horizontal overflow. The fixture DB, work dir and servers were dropped and stopped afterwards.

### New heights (app / mock)
| Screen / case | Panel | 1440 | 390 |
| --- | --- | --- | --- |
| health KOBO-001 | Data sources | 766 / 285 (**2.69**, was 4.95) | 867 / 391 (**2.22**, was 4.52) |
| health KOBO-001 | Physical asset condition | 253 / 285 (0.89) | 342 / 442 (0.77) |
| health KOBO-002 | Data sources | 308 / 285 (1.08) | 426 / 391 (1.09) |
| asset KOBO-001 | the three panels | 379 / 316, 379 / 316, 358 / 287 | 330 / 274, 415 / 316, 478 / 428 |

The remaining height above ~2x at 1440 is nine honest rows; none is hidden.