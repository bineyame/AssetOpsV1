# post-W6 W2-cold: builder pre-flight

2026-10-24. Branch `task/post-W6-W2-cold` from main `7554111e`. No product code is written yet. Sources: the W2-cold card and the shared sections of `post-W6-audit/fix-slices.md`, the R241-R261 register rows, the batch-06/07/14 ledgers and `differences.json`, the v69 mock (`index.html` lines 239, 322-330, 536-566), and current code. Every point below has a **recommended default**. The builder will use the default unless the Architect rules otherwise.

**Count:** 16 open questions (Q0-Q15), 14 per-ID defaults (section A), and 2 cap requests (section D, `cold-findings` 850/550). Top: Q1 frame/App files outside the card, Q2 orphaned EV Findings B9-10, Q3 cold index content, the Q8 Maintenance card data source, Q9 step outcome not on the overview wire.

**Scope rule assumed (Q0).** Each register row is a one-line pointer (`Bx-yy | screen | D3 | Fix in W2-cold`). I treat only the part of each ledger entry marked "(c) D3" as in scope. Parts marked D1/D2/D4 (chip wording, Incident links, F-codes, `Unknown` vs `Not determined`, legend, in-policy share) stay as they are. **Default: confirm.**

## A. Per-ID target behaviour

| ID | D3 part only | Mock evidence | Current code | Default fix |
| --- | --- | --- | --- | --- |
| R241 B6-10 `temperature` | Missing status-strip claim link | `status(..., claim('Inspect temperature claim','temperature'))` (mock 546) | `TemperatureStatus` `ColdAssessmentViews.tsx:239` has no `action` | Add `StatusBar action` → cold Evidence **Analysis** at the read's resolved window (`routes.evidence` + `?view=analysis` + `coldWindowSearch(read.window)`). `ColdPerformanceFrame` already receives `routes`, so no frame edit is needed. Copy: **"Inspect temperature claim"**, matching the cold Overview precedent `Inspect evidence` (`coldSiteViews.tsx:573`) with no ↗, because the target is a page, not a drawer. Omit the link when the read is not loaded. |
| R242 B6-11 `temperature`, `coldbackup` | KPI typography: number and unit set as one string; text values at 17 px vs the mock's 27 px | `metric('Peak','8.2 <small>°C</small>')`; `metric('Automatic start','Failed',...)` with no assessment class | `TemperatureCards` :267, `BackupPanels` cards :601-606 pass `word` | No CSS edit (primitives already style `.v69-metric__value small`, `primitives.css:4443`). Render numeric values as ReactNode `{n}<small>{unit}</small>` through a local helper (units `min`, `°C`, `°C·min`). Drop `word` on these eight cards so text values use the full value size. Keep the copy (`Not determined` etc. stays D2). |
| R244 B6-13 `temperature`, `coldbackup` | Refused window drops the strip and tiles; the "Durations are bounded" callout still shows; one generic window sentence | The mock always keeps the strip and four tiles | `ColdPerformanceFrame` :806-813 renders `PageRefusal` and no tiles; the notice at :422 is unconditional | Apply the W2-F M3 form: `RequestedWindowBar` → `RefusedStrip` → `RefusedTiles` (four `Not assessed` tiles; temperature labels `Time outside policy`, `Peak`, `Exposure size`, `Product outcome`; backup labels as loaded) → per-panel gaps (unchanged). Export `RefusedStrip`/`RefusedTiles` from `coldSiteViews.tsx` (currently file-private). The strip chip shows `refusalText(read).title`, so 403/404/503 do not say "Window cannot be read". Drop the title/body banner; keep the `cold-refusal-references` technical disclosure under the tiles. Hide the duration callout unless temperature loaded. Copy split: see Q5. |
| R245 B6-14 `temperature` | `Policy not recorded` / limit `Not recorded` when no assessment is selected, while Foundation declares 2-4 °C | — | strip :255, limit row via `deg(null)` | When the read has no selected assessment (`watermark.assessment_revision_ids` empty), the strip says **"Policy not read for this window"** and the limit row says **"Not read for this window"**. Keep `Policy not recorded` only for a selected read with `policy === null`. Do not read the Foundation policy into this selected-read screen. (Optional, ask: the no-selection chart panel keeps 379 px for one gap line. Default: leave it.) |
| R246 B6-15 `coldbackup` | No confidence chip on the strip | `badge('Confidence: High')` (mock 562) | `BackupStatus` :534 `Evidence: {claimWord}` | Rename the chip to **`Confidence: {claimWord(read.claim_level)}`**, the same form as the Finding/Overview strips (W2-F M9/M13). No second chip. |
| R247 B6-17 `coldbackup` | Successful start keeps the failure copy | mock success state n/a | prose :592; `STEP_ESTABLISHES.START_RESULT` in `coldAssessmentWords.ts:67` | Prose: show **"Which part failed, if any, is not determined here."** only for `OBSERVED_FAILURE`; `CONTRADICTORY`/`UNKNOWN` → **"Whether any part failed is not determined here."**; `OBSERVED_SUCCESS` → omit. START_RESULT limit by outcome: failure keeps **"A failed start needs inspection"**; success → **"One successful start is not a reliability test"**; otherwise → **"Start result not established"**. Implement as a state override in `establishes()` so `coldAssessmentWords.ts` stays unchanged. |
| R249 B6-20 `cold-finding` | Refused/unknown strip has no separator before the Site name | — | :1096 `Unknown Confidence: Unknown {site}` | `<Badge>Unknown</Badge> {[siteName, "Confidence: Unknown"].join(" · ")}`, the same order as the loaded `FindingStatus` (:849). Breaks `coldRoutes.test.tsx:793` on purpose. |
| R253 B7-01 `cold-findings` (High) | The cold Site Findings page renders the mini index and its false "not released" reason | `siteFindingsScreen` (mock 328-330): lens chips → strip `Scoped to … · n open` → 7-column table | `SiteFindingsFrame` `SiteAnalyticsFrames.tsx:451`; App mounts it with no cold client (`App.tsx:435`) | See Q1-Q3. |
| R254 B7-03 `cold` | Cards: the label is the link instead of `View detail →`; Cooling has no link; Maintenance hard-coded | `metric(...,'temperature'|'coldbackup'|'cooling'|'cold-work-maintenance'|'cold-evidence')` each with `View detail →` (mock 539) | `OverviewCards` `coldSiteViews.tsx:471-521` | Plain-text labels. Use the `MetricCard link` prop with **"View detail →"** on all five: Temperature/Backup/Evidence use their existing DTO links; Cooling → `routes.cooling` at the window; Maintenance → `siteWorkMaintenanceHref` at the window. Maintenance value: see Q8. |
| R255 B7-04 `cold` | Timeline titles read `role · Observed` in one tone; "steps below" sits under the steps | `eventChain()` (mock 239): event + outcome title, source line, danger/ok tone | `stripEvents` :525; the strip DTO has no `outcome` | See Q9. Copy: **"The steps above are based on the selected accepted records. Missing steps remain unobserved."** |
| R256 B7-05 `cold` | No SLD link on Chamber temperature; the same `Not observed: transfer to backup.` is repeated under both attention items | `panel('Chamber temperature',…, link('cold-sld','Single line diagram →'))` | :605 Panel has no actions; :629 `limitText(n.limitation)` per item | Panel `actions` = **"Single line diagram →"** to `siteFoundationViewHref(siteId,'sld')` (add `sld` to `ColdSiteRoutes`). Show each distinct limitation once, on the first item that carries it, and leave the body empty on later items. The Action/Next step parts stay D1. |
| R258 B7-07 `cold-evidence` | Strip link `Configuration at window end` instead of `Portfolio evidence`; Cooling row's generic next step; normal case `Next evidence not identified` beside a stated required basis | mock strip `Portfolio evidence`; row `Review cooling` | :816, :858, :997 | (a) Strip action → **"Portfolio evidence"** linking `EVIDENCE_PATH` (mounted, W3-02). Default: replace the Configuration link (the Foundation tab is one click away). (b) Cooling row and any cooling next-evidence item → **"Review cooling →"** to `routes.cooling` at the window. (c) See Q10. |
| R259 B7-08 `cold-evidence-analysis` | Received (and Sent) are time-only on a different date from Measured | — | :1136-1137 `utcClock` | Prefix the date (`24 Oct 16:08:42`) when the Sent/Received UTC day differs from the measured instant's UTC day; otherwise keep the time only. New local helper; **do not change `eatTime`** (`EvSiteViews.tsx:26` imports it, which would pull in EV reach). See Q11 for time basis. |
| R261 B7-11 `cold`, `cold-evidence`, `cold-financials`, `cold-assumptions`, `cold-evidence-analysis` | One generic invalid-window sentence for a reversed window | — | `refusalText` `ColdAssessmentViews.tsx:140`; `coldSiteViews.refusalOf` :263 reuses it | One change to `refusalText` fixes all five screens and temperature/backup/finding. See Q5. |

## B. Open questions (recommended default in bold)

**Q1 (High). R253 needs files outside the card list.** The cold Findings page needs a `COLDCHAIN` branch in `SiteFindingsFrame` (`SiteAnalyticsFrames.tsx:451`, the same pattern as `FindingDetailFrame` :675), and App must pass `coldAssessment` to that element (`App.tsx:435`; it already passes it to the Finding and Financials frames). `SiteFindingIndex.tsx` alone cannot tell the Site type. `SiteAnalyticsFrames.tsx` is shared with shell (Action/change crumbs) and W1-a/W1-b. **Default: a ~10-line branch in `SiteFindingsFrame` plus one prop on the App element. No route change. Land after shell, then rebase before or after W1 by agreement (non-overlapping hunks).** The alternative of a default client inside the frame avoids App but hides the dependency. Not recommended.

**Q2 (High). EV Findings (B9-10) was merged into R253.** B9-10 ("EV Site Findings shows the mini index with a false not-released reason", High) was folded into B7-01. W2-EV lists `ev-findings` only as a destination regression and does not own `SiteAnalyticsFrames.tsx`, so nobody owns the EV fix. **Default: W2-cold fixes cold only. The Architect assigns EV Findings explicitly, either to W2-cold, where the same frame branch plus `evAssessment.listFindings` would make it cheap but adds EV tests and 10 `ev-findings` pairs, or to W2-EV with the frame file.**

**Q3. Cold Findings index content (new `ColdFindingIndex` in `ColdAssessmentViews.tsx`).** The DTO is `ColdFindingsRead` from `GET /api/sites/{code}/cold/findings` (`coldAssessmentClient.ts:156`). It carries title, kind, lifecycle, claim_level, claim, episode bounds and currentness. It has **no** priority, lens, code or money.
- Frame: the existing crumb, header and Site tabs. Panel title **"Findings at this site"**.
- Lens row: **reuse `LensChips` exported from `SiteFindingIndex.tsx`** (All selected; Cost/Risks/Opportunities through `UnavailableChip`). New chip literals would break the closed multiset in `navigation-truthfulness.ps1:778`. No mini opportunity helper.
- Strip: **"Scoped to {site} · {n} open"**, where n = items with lifecycle `SUPPORTED`, plus the read's window and currentness words. The mock's secondary "Same records … as the global Findings list" would be false, because the estate index reports cold as `NOT_APPLICABLE` (`estate/findingIndex.tsx:206`). Default secondary: **"Cold-chain Findings are not in the global Findings list"**, with `UnavailableInline label="Manage in Findings"` in the link slot (EV precedent `EvSiteViews.tsx:850`).
- Columns, 7 as in the mock: Finding (link = `title`, to `siteFindingHref` + the read's resolved window, so the cold Finding wiring shows the same revision; episode period in `<small>` under the title); Domain (`EXCURSION` → "Temperature" link, `START_RESPONSE` → "Backup" link, both at the window; other kinds → plain code words); Priority (**`Not assessed` badge**, mini precedent); Confidence (`claimWord(claim_level)`); State (`lifecycleWord`); Main consequence from on-wire `claim` only (excursion: `"{duration range} {above|below} the limit · peak {deg}"`; start: `startResultWord(claim.result)`; else "Not in this list"); Lens (**`Not assessed` badge**). No Period column (mock has 7; mini's 8th is its own W1 ruling).
- States: loading sentence; loaded rows; loaded empty and selected → **"No Findings at this site in the selected window."**; loaded with no selected assessment → the cold `NO_COLD_ASSESSMENT` gap; refused → `RequestedWindowBar` + `RefusedStrip` + in-panel `refusalText` body (Q5); `next_cursor !== null` → **"Showing the first {n} Findings; paging is not available on this page."** (no cursor UI; producer gap).
- Window: `coldWindowFromParams`. With no window the API uses the latest selected cold window, like every other cold screen. **Default: the global seven-day Default-window ruling does not apply (it targets event-time lists). No window control (B7-02/R88 D1).**

**Q4. B6-13 banner removal.** `coldRoutes.test.tsx:284-292` pins `[data-page-refusal]` on temperature and backup. **Default: remove the banner on these two screens only (the Finding keeps its W5-01b C5 strip + banner form) and update the test to the M3 form.** Confirm, or keep the banner above the strip.

**Q5. Refusal copy by code (R244, R261).** The backend distinguishes `COLD_TIME_INVALID`, `COLD_WINDOW_INVALID` (one-sided or reversed) and `COLD_WINDOW_TOO_LONG` (`cold_assessment_api.py:56-90`). Default bodies, with the title kept as "Window cannot be read":
- `COLD_TIME_INVALID`: **"The selected window start or end is not a UTC time."**
- `COLD_WINDOW_INVALID`: **"The selected window needs both a start and an end, with the start before the end."**
- `COLD_WINDOW_TOO_LONG`: **"The selected window is longer than 31 days."**
- Any other 422 keeps the current generic sentence.

All three keep `key: "invalid-window"`, because `RequestedWindowBar` (:398) and the cold depth screens test that key. Cold depth pages (`COLD_WINDOW_INVALID` raw text, B14-01) and `domainActionClient` (B14-02) are not changed here (Q13).

**Q6. B6-11 word size at 390.** Removing `word` puts `Not determined` and `Not assessed` at 27 px in the two-column 390 card grid, where they will wrap to two lines. **Default: accept the wrap (no hidden text). The capture shows it.**

**Q7. B6-10 link target.** **Default: Evidence → Analysis**, which shows the records and claim limits. Alternative: the Evidence overview.

**Q8. B7-03 Maintenance card data.** The overview DTO always sends `maintenance.state NOT_RECORDED` with the text "No maintenance work record is available for this window" (`cold_site_reads.py:89,335`). That is false since cold Work shipped. The card file list is frontend-only. **Default: no new read and no backend edit. Value "Not summarised here", note "Maintenance cases are listed under Work", link "View detail →" to cold Work › Maintenance at the window. The backend text is no longer rendered.** The copy avoids the `missing-claim-scan.mjs` patterns ("not available yet"), whose baseline may only shrink. Alternative: read the selected maintenance cases through the existing Site Work client, which needs a new client prop through `coldSiteScreen` and App.

**Q9. B7-04 outcome is not on the overview wire.** `causal_strip` drops each step's `outcome` (`cold_site_reads.py:447`); `ColdStepRead.outcome` exists on the backup-chain read. **Default: the Overview also reads `assessment.getBackupChain(site, window)` and joins strip steps to chain steps by `evidence_id`. Title = `{stepLabel} · {outcomeText}` as on the Backup page (`chainTimeline` :544). Tone: danger on `ADVERSE`, ok on `RUNNING`, gap for missing. The detail line keeps the current text. Unmatched steps keep today's label.** Alternative: a backend `outcome` field on `causal_strip` (out of card scope).

**Q10. B7-07(c) conflicts with W2-F S5.** S5 says the stock prompt follows a selected excursion, never the product chip. **Default: keep S5. In the normal case, change only the gap copy to "No missing record blocks this window's claims. Pricing a future exposure still needs the required basis stated above."** Alternative: always list the stock item when the Product exposure row is not Full (overrides S5).

**Q11. B7-08 time basis.** The Time-basis ruling makes the Site timezone primary on Site-scoped reads, but `Measured (EAT)` is a hard-coded +3 h (`coldSiteViews.tsx:168`), and shell Q4 says each seam card owns its own time displays. **Default: R259 fixes only the missing date (A-table). Converting Sent/Received/Measured to the Site's timezone with a UTC disclosure is a separate ruling.** If the Architect wants it now, pass `site.timezone` through `coldSiteScreen` (`coldSiteRoutes.tsx`, in the card) and follow shell Q18.

**Q12. Other UTC displays on these screens** (strip window text, chart axes, timeline `hh:mm UTC`) cite B2-21/B3-04, whose rows cover mini screens. **Default: out of W2-cold scope; no change.** Confirm or name an owner.

**Q13. Merged duplicates outside the card's screens.** B14-01 (cold depth refused form) → R244; B14-02 (cold-work `domainActionClient` generic message) → R261; B9-02/B9-06/B9-07 (EV Overview cards, EV evidence link, EV Received) → R254/R258/R259; B16-01/B16-02 (EV depth/work). **Default: W2-cold changes only the nine listed cold screens. B14-01/B14-02 stay with W5-cold-Work (it reads `domainActionClient` and owns the depth files); the EV analogues stay with W2-EV/W5-EV. The Architect records that the merged rows close only when those cards land.**

**Q14. Files beyond the card list.**
- `SiteAnalyticsFrames.tsx` and `App.tsx` (Q1).
- The `ColdSiteRoutes` interface in `coldSiteViews.tsx` gains `sld` and `workMaintenance`. Add them as optional, or update every literal in the test fixtures; `ColdCooling`/`ColdHealthDepth` also use the type.
- `SiteFindingIndex.tsx` exports `LensChips`.
- `coldAssessmentWords.ts` and `coldFormat.ts` stay unchanged by default.

No backend edit. **Default: accept.**

**Q15. Guards.** `navigation-truthfulness.ps1` closed chip multiset: reuse the existing component, which adds no literal. `missing-claim-scan.mjs`: no new "not available yet" text outside `UnavailableEntry`. `shell-overflow.ps1`: the new table goes in the existing `DataTable` scroller. A new `UnavailableInline` use is not in the multiset; the builder will confirm with check-architecture. **No guard loosening.**

## C. Tests that will break (intended) and tests to add

- Will break or need updating:
  - `coldRoutes.test.tsx`: :284-292 page-refusal on temperature/backup; :793 strip text; the KPI `textContent` at :345-346 should survive, since the `<small>` text joins the string; status-bar `Evidence:` chip tests near :670.
  - `coldSiteViews.test.tsx`: :574 Configuration link; :906 "Review evidence" row list (cooling row); :965-969 next-evidence copy; :694/:1158 Received cells if dated; card-label links; overview fixtures need a `getBackupChain` stub.
  - `s404SiteFindingIndex.test.tsx`: frame props only; mini assertions must still pass.
- Add:
  - Cold index: rows, columns, links with the window, domain links, empty/no-selection/refused/403/503/next_cursor; mini and EV unchanged.
  - Event-chain order and outcome tone; the evidence_id join with its fallback.
  - The three window-refusal copies plus the unknown-422 fallback.
  - Temperature/backup refused strip and tiles, with the callout hidden.
  - No-selection policy copy.
  - Success/failure/unknown backup copy.
  - `View detail` links on all five cards.
  - SLD link; limitation dedupe; Portfolio and Cooling links; dated Received.

## D. Caps (lesson 15): likely misses flagged now

| Screen · panel · width | Docket cap | Risk | Default request |
| --- | --- | --- | --- |
| `cold-findings` · Findings at this site · 390 | 500 | **Likely miss.** The observed 441 was the mini gap with 0 rows. Chips (~80) + the 7-column scroller with 5 worst-case 160-char titles (wrapping in a ~200 px first column) ≈ 650-800 | **Revised cap 850 at 390**, set from a five-row 160-char pure-render fixture before build |
| `cold-findings` · Findings at this site · 1440 | none | No docket row | **Cap 550 at 1440** (5 rows × ~64 + chips + header) |
| `temperature`/`coldbackup` refused pages | none | Tiles add ~120 px | No cap (short refusal pages) |
| `cold` · Needs attention / cards | none | `View detail` adds ~20 px per card | No cap |
| `cold-evidence` · What we can conclude now · 390 | 800 | Peak 615. The cooling link changes words only | Keep |
| `cold-evidence-analysis` · records · 1440/390 | 450/800 | A dated Received cell may widen the table (it scrolls inside) without adding height | Keep |
| `cold-finding` · Bounded conclusion · 390 | 400 | Unchanged | Keep |
| `coldbackup` · Evidence by causal step | 700/1050 | Unchanged | Keep |

All-disclosures-open stays exempt and must not clip. Over-cap after remeasure: change wrapping or the inner scroll first, then return to the Architect with the measured fixture.

## E. Recapture set

- **92 indexed pairs** (from `audit-index.json`): `temperature` 10 (b6: excursion, no-selection, refused, normal, backup-failed); `coldbackup` 12 (+ default-window); `cold-finding` 10 (start-excursion, unknown-id, excursion-finding, start-backup-failed, start-refused-window); `cold-findings`, `cold`, `cold-evidence`, `cold-evidence-analysis`, `cold-financials`, `cold-assumptions` 10 each (b7: stocked, no-selection, refused, no-window, normal).
- **+2 `cold-finding-excursion` representative pairs** at 1440/390, using batch-06's `targets-excursion.json` row (`/sites/COLD-LAB-001/findings/00000002-…0170`, mock `#/cold-finding-excursion`) under its own id.
- **The "false Findings reason" proof** is covered by the 10 `cold-findings` pairs (the not-released copy must be gone in every case).
- **Shared-component reach** if Q1 lands: `sitefindings` (mini) and `ev-findings` regression at both widths, one representative case each (+4). If Q2 brings EV in: all indexed `ev-findings` pairs instead.
- Producer: `.agent/W2-F-evidence/seed.py` phases excursion/normal/backup-failed on an `assetops_*_test` DB. Capture tools: `batch-06/tools/capture-b6.mjs` and `batch-07/tools/capture-b7.mjs` with their target JSONs (new ports/CDP). Record SHA, panels, overflow and closed heights in `.agent/post-W6-W2-cold-recapture/`.
- **Total default: 98 pairs** (92 + 2 + 4).

## F. Capture gaps (selected-DTO tests instead)

- Pending, stale and historical currentness on all nine screens: the producer cannot make them (batch-07 Blockers).
- Cold index 403/503 and `next_cursor` (>50 Findings).
- `COLD_TIME_INVALID` and `COLD_WINDOW_TOO_LONG` can be made by URL. Default: pure tests only; optional extra capture.
- Overview step-outcome join fallback (unmatched evidence_id).
- A populated Maintenance summary (no read under the Q8 default).
- Successful-start copy is capturable (normal phase).
