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
