# POLISH-PB-1 Shell, labels check, time consolidation and P-03

Status: in_review
USER_REVIEW_REQUIRED: false
Lane: B (frontend and tools). Units: 5.25 (Addendum 1 Q1). Branch `task/POLISH-PB-1-shell-time`.

The spec is `.agent/build-sheet-POLISH.md`: §3 (Times rule, Shell and Portfolio/Findings rows of §3.1), §4 P-03,
§5 Lane B "PB-1", §6 D-1/D-4, §7 (R650-R652), Addendum 1 Q1 (P-04 is verification only), Addendum 3 (captures),
Addendum 5 (exemption rules) and Addendum 6 Q7 (revised D-4). This file states scope only; the sheet is the contract.
Pre-flight answers from the coordinator are recorded in the packet `.agent/POLISH-PB-1-packet.md`.

## Scope

- Shell: rail label "Simulator Lab"; app-wide demonstration banner (D-1, R651); Site badge "Example data".
- Time: `ui/time.ts` (`formatDay`, `formatDayTime`, `formatTime`, `formatRange`), `ui/TimeZoneNote.tsx`
  (`[data-time-zone-note]`, "Times in UTC" and "Times in UTC · due dates in each site's local date"), the §3 formatter
  bodies delegate to `time.ts`, no visible per-time "UTC" on the capture screens (R650).
- `EstateDateBar`: window "23–29 Oct 2026", cutoff "Latest information, as of …", cutoff picker in a closed
  `<details>` "View an earlier point in time" (R652).
- P-03: Confidence chip wraps inside its cell (`estatePortfolio.css`) and the shorter "Well supported" copy.
- P-04: verification captures only (Addendum 1 Q1).
- `tools/w1-ux-07-rail-evidence.mjs` updated for "Simulator Lab".

## Not in scope

Kobo board, verification and display-code copy (PB-2); estate, cold/EV and work copy and P-07/P-09/P-10 (PB-3);
server text (lane A).

## Checks

- New `ui/__tests__/time.test.ts`; scoped vitest (`estate`, `shell`, `ui`, `work/globalWork*`, cold/EV formatter users).
- `tsc --noEmit`; `tools\check-all.ps1`: 12 guards pass.
- Captures (strict): `portfolio-week` (P-03 rectangle check) and `findings-all`; review-mode `kobo-board-S` (R453 at 390,
  hidden at 1440).
- Full `npx vitest run` once at the end.
