# POLISH-PB-1 review packet: shell, time consolidation and P-03

- **Task:** `tasks/POLISH-PB-1-shell-time.md`.
- **Spec:** `.agent/build-sheet-POLISH.md` §3 (Times), §3.1 (Shell, Portfolio/Findings and the time rows below),
  §4 P-03, §5 Lane B PB-1, §6 D-1/D-4, §7 R650-R652, Addenda 1 Q1, 3, 5, 6 Q7 and **7** (the PB-1 pre-flight rulings).
- **Branch:** `task/POLISH-PB-1-shell-time`; base `ab248b4c3`.
- **Review status:** USER_REVIEW_REQUIRED: false. Merges on review ACCEPT.

## Outcome delivered

- One time formatter, `frontend/src/ui/time.ts`: `29 Oct 2026`, `29 Oct 2026, 16:00`, `16:00`,
  `29 Oct 2026, 16:00–17:05`, whole-day windows `23–29 Oct 2026` / `28 Sep – 4 Oct 2026` / both ends in full across
  years. No per-time "UTC" and no ISO stamps; invalid input reads "Time not available yet".
- `TimeZoneNote` (`[data-time-zone-note]`, "Times in UTC") once per page in the date or window bar.
- Shell: rail "Simulator Lab"; app-wide demonstration banner; Site badge "Example data".
- Estate date bar: "23–29 Oct 2026", "Latest information, as of 1 Nov 2026, 02:09", earlier-cutoff picker inside a
  closed "View an earlier point in time" disclosure.
- P-03: the Confidence chip wraps inside its cell; "Well supported".

## Files materially changed

- New: `ui/time.ts`, `ui/TimeZoneNote.tsx`, `ui/time-zone-note.css`, `ui/__tests__/time.test.ts`,
  `shell/demonstrationBanner.css`.
- Shell: `shell/OperatorShellLayout.tsx` (banner), `shell/simulatorLabRoutes.tsx` (label), `ui/V69Layout.tsx` (badge).
- Estate: `estateShared.tsx` (bar), `estatePortfolio.css` (P-03), `portfolioWords.ts` (Well supported; `dayMinute`),
  `EstatePortfolio.tsx` (scope window), `EstateEvidence.tsx`, `estateFinancialsWords.ts`.
- Formatter bodies delegating to `time.ts` (names kept): `ui/productWords.ts` (`plainTime`/`asOfText`),
  `sites/actionPresentation.tsx` (`when`), `work/globalWorkClient.ts`, `sites/coldFormat.ts`, `sites/EvEnergy.tsx`,
  `sites/EvScenarios.tsx`, `sites/SiteFindingIndex.tsx`, `sites/SiteWorkActions.tsx`, `sites/FoundationRevisionPanel.tsx`,
  `sites/SiteHealth.tsx`, `work/WorkRequestHistory.tsx`.
- Capture-screen UTC removal and notes (Addendum 7 Q1/Q1a): `sites/SiteWindowOverview.tsx`,
  `sites/SiteActionVerification.tsx`, `sites/coldSiteViews.tsx`, `sites/EvSiteViews.tsx`, `sites/EvAssessmentViews.tsx`,
  `work/globalWorkParts.tsx`, `work/workRequestShared.tsx`.
- Tests: expectations updated to the new forms (list in "Checks run"); `test/productPresentation.ts` `AS_OF_PATTERN`
  and its mirror in `tools/evidence-checks.mjs`.
- Tools: `tools/w1-ux-07-rail-evidence.mjs` ("Simulator Lab").
- Records: `.agent/mock-departure-register.md` R650-R652; `.ai/CODE_STATE.md` "POLISH PB-1".

## §3.1 rows done in PB-1 (Addendum 7 Q1a, Q4, Q5): PB-2/PB-3 skip these

| Row | Now |
|---|---|
| Kobo "UTC day" label; bounds sentence "… UTC, start included, end excluded." | "Day"; sentence deleted, `TimeZoneNote` in its place |
| Kobo "Using the latest checked readings · This answer uses … 2026-10-29, one UTC day at this site · As of … UTC" | "Latest checked readings · 29 Oct 2026 · updated 1 Nov 2026, 02:09" (CURRENT state; other states keep the shared line with "29 Oct 2026") |
| Cold "Selected window 29 Oct 2026 16:00–17:05 UTC · Selected evidence through 29 Oct 17:05 UTC" | "29 Oct 2026, 16:00–17:05 · information up to 17:05" (the day is added when the cutoff is on another day: "· information up to 29 Oct, 17:05") |
| EV "27 Oct 08:00–27 Oct 09:00 UTC · known at 27 Oct 09:00 UTC" | "27 Oct 2026, 08:00–09:00 · as of 27 Oct, 09:00" |
| Work/WR "As known at 1 Nov 2026 02:09:11 UTC · Reload" | "Updated 1 Nov 2026, 02:09 Times in UTC · Reload" |
| Portfolio/Findings window, cutoff, picker | "23–29 Oct 2026"; "Latest information, as of 1 Nov 2026, 02:09"; closed details "View an earlier point in time" |
| Portfolio "Supported, coherent source" | "Well supported" |

## Builder copy outside §3.1 (old → new, for review)

- "This is an earlier evidence cutoff." → "Showing an earlier point in time." (Addendum 7 Q5).
- Estate historical cutoff line → "Information as of {dayTime}" (Q5); no response yet → "Latest information".
- Estate picker label "Evidence cutoff (UTC)" → "Point in time" (inside the disclosure).
- Work controls "From (UTC)" / "To (UTC, exclusive)" → "From" / "To (not included)".
- `CHANGE_WINDOW` "Change the UTC window or open a Site record." → "Change the dates or open a Site record."
- Verification "Criteria and windows fixed before evaluation (UTC)", "Windows (UTC)", "Five-minute slots (UTC, end not
  included)" → the same without "UTC".
- EV assessment "Counted as of (UTC)" → "Counted as of".
- Kobo timeline caption/aria "on 2026-10-29, 00:00 to 24:00 UTC" → "on 29 Oct 2026, 00:00 to 24:00"; Kobo
  "one whole UTC day (2026-10-29)" → "one whole day (29 Oct 2026)" (PB-2 still deletes that line per §3.1).
- Site Finding index scope "… · {days} (UTC)" → "… · {days}".
- Missing-claim scan: one new reviewed exemption, `ui/time.ts` `TIME_NOT_AVAILABLE` "Time not available yet" (the
  invalid-input word ruled by §5 PB-1 and Addendum 7 Q3). **Guard change for review**; see Known deviations D3.

## Acceptance criteria

| Criterion | Status |
|---|---|
| P-04 (Addendum 1 Q1): one review-mode `kobo-board-S`, R453 visible at 390 and hidden at 1440; 0 MOCK DEVIATION in client-mode `portfolio-week`/`findings-all` | Met. In review mode, 390 records `mock deviation label: MOCK DEVIATION` and `R453`; 1440 records none. Client mode: 0 MOCK DEVIATION hits on all 28 captures. |
| P-03: no Confidence chip box crosses into the Action cell; chip `right` ≤ its `td` right on every row | Met. 1440: 5/5 chips, 0 failing (chip right 876.2 ≤ td right 892.6). 390: 5/5, 0 failing. Non-vacuous: with the old long text injected the rule keeps 5/5 inside; with the rule overridden 5/5 fail at 1440 (chip right 929 > 892.6, intersects the Action cell). |
| Banner (D-1, R651) and "Example data" badge | Met; visible in `portfolio-week-1440.png` |
| Rail "Simulator Lab"; navigation truthfulness stays green | Met; guard PASS; `w1-ux-07-rail-evidence.mjs` updated |
| `time.ts`, `TimeZoneNote` (two variants; plain note on every captured page per Addendum 7 Q6), formatter delegation, `EstateDateBar` | Met |
| Frontend UTC hits reach zero (PB-0 baseline: 13 per width) | Met: **0** "time zone suffix" hits on all 28 captures. The note's own "UTC" is recorded as one exempt hit per capture (`data-time-zone-note=utc`). |
| `reviewLabels.test.ts` | Landed in PB-0 (Addendum 1 Q1); passes |
| `time.test.ts`: same-day, cross-day, midnight, invalid | Met (8 tests) |
| Register R650-R652 | Met |

## Checks run (final code `dfca8d5a8`)

- `npx vitest run src/ui/__tests__/time.test.ts`: 8 passed.
- Scoped vitest over `src/estate src/shell src/ui src/work src/sites`. The first run on the source change had 196
  failing expectations; after the test updates every listed file passes except the 3 known `w1f4VerificationStructure`.
- `npx tsc --noEmit`: exit 0.
- `node --test tools/checks/test_evidence_checks.mjs`: 12/12. `test_missing_claim_scan.mjs`: 26/26 (+2 PB-1 tests).
  `test_mock_deviation_labels.mjs`: 12/12. `node --check tools/w1-ux-07-rail-evidence.mjs`: OK.
- `tools\check-all.ps1 -Python …plan2\.venv\Scripts\python.exe` at `dfca8d5a8`: **All 12 guards passed**. The first
  run failed 2/12 on the missing-claim scan (the "Time not available yet" literal); D3 fixed it.
- **Full `npx vitest run` once at `dfca8d5a8`:** 315 s; **3563 passed, 5 failed**, 147 files.
  - The 3 known `w1f4VerificationStructure` failures ("elements before panel 1 of v69 screen verification").
  - `evEnergy` "energy_states_table_loading" ("the store read has not settled") and `evScenarios` R347 (window not
    yet carried). Both pass in isolation (16/16), so they are load-timing flakes under the full run, not PB-1 output.
- Test updates were made by a helper agent on test files only; I reviewed the non-string changes:
  - `siteFoundationRevision` gets a `pageNote()` helper, because the banner is a second `role="note"`.
  - `s5SiteWindowOverview` gets `expectLatestCheckedLine`.
  - `simulatorLabWorkspaceEntryPoint`'s "no entry-point link" check ignores the Lab's own `aria-current="page"` link,
    now that both read "Simulator Lab".
  - The badge assertions expect "Example data".

## Live captures (Addendum 3 setup)

- Serve ran from `AssetOpsV1-demo3` on `assetops_demo3_full_test` / `var/demo3_full`, PID 18564. Vite ran from
  `polB1/frontend` with `ASSETOPS_API_PORT=8990`, PID 25400. The serve log showed
  `performance: Performance cutover: permitted`. There were no manual writes, `prepare` or `add-day`. Both were stopped
  by PID (`taskkill /T`), and ports 8990 and 5490 were free afterwards.
- **Strict run, all 14 keys × 2 widths** (before the chart-tick fix): exit 1; 672 counted hits (PB-0 baseline: 692; 6 of them were the remaining UTC chart ticks).
  The only PB-1 class left was 6 chart-tick "UTC" hits (cold-board-failure, cold-board-normal and ev-board-fault, at
  both widths). These were fixed in `assessmentGraphics.tsx`.
- **Strict re-run** of `portfolio-week`, `findings-all`, `cold-board-failure`, `cold-board-normal` and
  `ev-board-fault` after the fix: **0 UTC hits**; 88 counted hits, all in classes owned by other slices.
- Counts per owner, per width, over the 14 keys after the fix: the 5 re-captured keys plus the other 9 from the full
  run. That is **333 per width, 666 overall** (PB-0 baseline: 346 and 692). Both widths are identical. The
  classification follows PB-0's.

| Owner | Hits per width | What |
|---|---|---|
| PB-1 (this slice) | **0** | baseline 13 UTC; 0 MOCK DEVIATION |
| PB-2 | 258 | `-open` ids 256 (251 UUID, 2 enum, 3 raw timestamps); portfolio "scenario" 2 |
| PB-3 | 9 | EV `REC <uuid>` 3; EV "scenario" 2; preventive "draft" 2 and "running" 1; cold-normal "running" 1 |
| Awaiting PA-2 | 47 | padded codes 19 (+5 on `-open`); `Finding <8 hex>` 10; Portfolio row UUIDs 5; Finding-title words 6 ("candidate" 2, "candidate avoidable" 2, "running" 2 on portfolio/findings-all); "load" 2 (critical-load labels, kobo S and S+1) |
| Awaiting PA-3 | 19 | Lab names 12; "replay" 7 |

- `portfolio-week` did not settle in the re-run (both widths) or in the full run at 1440. The page holds "Loading
  outcomes across the estate…", the outcome-matrix read from the DEMO-A backend. At 390 in the full run it settled
  with identical hits, and the screenshot shows every PB-1 element. This is recorded, not a PB-1 output.
- `exempt_hits`: every capture has 1 (`time zone suffix | data-time-zone-note=utc`, the note itself), except
  `kobo-board-S-open`, which has 24 (PB-0's 23 `data-vocabulary-exempt` plus the note).
- Review mode: run `DEMOB_REVIEW_LABELS=1 DEMOB_ONLY=kobo-board-S`. The log says "review labels on". R453 shows at
  390 and is absent at 1440.
- Output: scratchpad `pb1/cap-strict`, `pb1/cap-strict2`, `pb1/cap-review`; the P-03 measurement script is `pb1/p03-check.mjs`.

## UTC left for PB-3 (Addendum 7 Q1: PB-1 stopped at the 14 capture screens)

Visible "UTC" remains on non-captured screens. The counts below are of source strings that render visibly, not of
capture hits:
- `PerformanceDispatch.tsx` (18), `SiteFinding.tsx` (10), `LedgerSiteEvidence.tsx` (10), `SiteFindingIndex.tsx`
  (5: day-window inputs and copy), `SiteFindingEvidence.tsx` (5), `EvAvailability.tsx` (5), `SiteWorkActions.tsx` (4),
  `siteWorkCases.tsx` (3), `findingPresentation.tsx` (3: `readablePeriod`/`readableTime`), `EvidenceClaimLimit.tsx`
  (3), `SiteFindingHistory.tsx` (2), `MiniPerformance.tsx` (2), `ColdAssessmentViews.tsx` (2).
- One each in `SitePerformance`, `MiniScenarios`, `ColdScenarios` (`utcDayHm`), `ColdCooling`, `coldDepthGraphics`,
  `evDepthGraphics`, `coldWorkPresentation`, `SiteAction`, `FoundationRevisionPanel`/`FoundationBindingsPanel`
  ("Effective from (UTC)"), and `domainActionClient` (an error message).
- Added from review M1:
  - `SiteHealth.tsx:295-297` `clockTime` renders "Status at 09:10 UTC";
  - `EvEnergy.tsx:211` has the table header "Peak sample time (UTC)";
  - `evWorkPresentation.ts:107` has `EV_WINDOW_NOT_UTC_TEXT`.
- Each of those pages also needs its `TimeZoneNote`.
- Left on purpose: `title` attributes ("exact UTC"); the Analysis column labels that state a missing Site zone
  ("UTC; Site time zone unavailable"); the verification Dig-deeper fact "UTC, attested per day"; and the
  Simulator Lab tooling (`GatewayPublicationPanels`, `RunSetupFrame`, `RegisteredDeliveryView`).

## Known deviations

- **D1.** Addendum 7 Q1 asks for every visible UTC in all files, capped at 6 units. The full set is about 30 files, so
  PB-1 covered the 14 capture screens plus the shared formatters and lists the rest above for PB-3.
- **D2.** "One page note" is met on every captured page. Pages outside the capture set have no note yet. Some lost
  their per-time "UTC" through the delegated formatters, such as Foundation's `formatInstant` and Site Health's
  `formatInstant`. Others still show UTC from local helpers, such as Site Health's `clockTime` "Status at 09:10 UTC"
  (review M1). They are all in the PB-3 list.
- **D3. Guard change (review):** I added a fourth `REVIEWED_EXEMPTIONS` entry in `tools/checks/missing-claim-scan.mjs`
  for `ui/time.ts` `TIME_NOT_AVAILABLE`, with a pass test and a narrowness mutation test. Moving the const to another
  file, or inlining the text, still fails. Without the entry the live scan fails, as the first check-all showed. The
  sheet rules the text, and it names a malformed value rather than a missing capability. The reviewer accepted it
  for this slice. It also goes to PC's whole-diff review and to the Architect's decision log (review L4).
- **D4.** Serve stdout is block-buffered when redirected, so the `performance:` line arrived late. The API answered
  throughout.
- **D5.** `.ai/ACTIVE_CONTEXT.md` is not updated: two lanes run in parallel and the coordinator owns routing (as in PB-0).
- **D6. Layout evidence: not run** (review L3). I did not run `node tools/layout-evidence.mjs`. The layout claims
  rest on the PB-0 capture gate:
  - captures at 1440 and 390, with their `overflow` measurements;
  - the P-03 chip-rectangle measurement (5/5 chips at both widths, shown to be non-vacuous).
  Shell layout outside the 14 keys, such as the banner at other widths, is not separately measured.

## Review fold-in (`.agent/review-POLISH-PB-1.md`, ACCEPT)

- **L1:** "Updated …" and "Historical as of …" are now separated from the note by " · " (`aria-hidden`), as on the
  verification strip. This is in `globalWorkParts.tsx` `StatusLine` and the work request as-of line in
  `workRequestShared.tsx`. Seven work test files were updated.
- **L2:** `coldFormat.windowText` passes `{seconds: true}` when either bound has non-zero seconds, matching the old
  `hm` behaviour. A test was added to `ui/__tests__/time.test.ts`.
- **M1, L3, L4:** packet changes above (the PB-3 list, D2, D6 and D3).

## Residual risk

- The banner adds a second `role="note"` on every operator page. Tests that query `getByRole("note")` must scope
  their query (one test needed a helper).
- The CURRENT Kobo state line is a local rendering (`DayStateLine`); other states still use the shared `ProductStatus`.
- PB-2 and PB-3 rewrite the surrounding copy on the Kobo and verification pages. They should keep using `ui/time.ts`
  for any time they touch.

## User-review focus

None required (USER_REVIEW_REQUIRED: false). The reviewer should check:
- D3, the guard exemption;
- the Q1a rows table;
- the builder copy list;
- `portfolio-week-1440.png` (banner, date bar, note, chips).
