# Review: POLISH PB-1 (shell, time consolidation, P-03)

- Branch `task/POLISH-PB-1-shell-time`, head `700a4b7e4`, base main `ab248b4c3`. Diff `ab248b4c3...700a4b7e4` (82 files).
- `dfca8d5a8..700a4b7e4` changes only the packet, so the packet's checks at `dfca8d5a8` apply to the reviewed code.
- Reviewer: fresh Claude reviewer (not the author). No fixes made.

## Verdict: ACCEPT with findings fixed on the branch

There are no High findings. M1 is a packet-only fix (the PB-3 UTC hand-off list is incomplete). L1-L4 are optional.

## Findings

### M1. The PB-3 UTC hand-off list is incomplete (acceptance gap: Addendum 7 Q1, packet D1/D2)
`.agent/POLISH-PB-1-packet.md` "UTC left for PB-3" misses at least three visible strings that Addendum 7 Q1 requires removing:
- `frontend/src/sites/SiteHealth.tsx:295-297`: `clockTime` still returns `` `${match[1]} UTC` ``, rendered as the column header
  "Status at 09:10 UTC" (`:565`). The packet's D2 says Site Health "lost the per-time UTC", but that is only true of `formatInstant`.
- `frontend/src/sites/EvEnergy.tsx:211`: the row header "Peak sample time (UTC)".
- `frontend/src/sites/evWorkPresentation.ts:107`: `EV_WINDOW_NOT_UTC_TEXT` "The selected window start and end must be UTC
  times." This is a refusal sentence of the same class as the listed `domainActionClient` error.

**Why it matters:** PC's strict gate covers only the 14 capture screens. A miss in this list ships unless PB-3 finds it on its own.

**Fix:** add the three strings to the list, and correct the D2 Site Health wording. A packet edit only; no code change is
required in PB-1. The counts per file also differ from a raw grep in places (for example `SiteWorkActions` 4 visible
against 8 matches, `siteWorkCases` 3 against 1). The packet should say that the counts are visible-string counts.

Spot-check method: a grep for `\sUTC\b|\(UTC` and `["`>]\s*UTC|UTC[;,)]|UTC \w` over `frontend/src` (no tests, no
comments). Every other hit is in the packet's list, or is in its "left on purpose" class: `title` attributes, the
"UTC; Site time zone unavailable" / `SITE_ZONE_UNAVAILABLE_LABEL` labels, Lab tooling, or `siteTime`/`findingTime`/`miniDepthClient`
identifiers.

### L1. The Work "Updated … · Reload" line runs the note into the time (preference, §3.1 Work row)
`frontend/src/work/globalWorkParts.tsx:232` and `workRequestShared.tsx:270-274` render `{text} <TimeZoneNote />`, which gives
"Updated 1 Nov 2026, 02:09 Times in UTC". There is no separator, and `.time-zone-note` (`ui/time-zone-note.css`) has no margin.
The verification strip (`SiteActionVerification.tsx:649-650`) uses an `aria-hidden` " · ".
**Fix:** use the same " · " separator, or give the note a left margin.

### L2. `coldFormat.windowText` drops seconds that the old formatter showed (Addendum 7 Q2)
`frontend/src/sites/coldFormat.ts:31-36` now calls `formatRange(a, b)` with no `seconds`. The old body used `hm(from)`,
which showed `:ss` when the instant had seconds. Q2 keeps seconds for "the cold hm", and `hm`/`dayHm` still honour that.
A window bound with seconds would now read to the minute, so two different windows could read the same.
The demo windows are whole minutes, so this is not visible in the captures.
**Fix (optional):** pass `seconds` when either bound has non-zero seconds, or record that the window line is minutes-only by ruling.

### L3. The packet does not say how `tools/layout-evidence.mjs` was handled
The slice is layout-sensitive: an app-wide banner row, a date bar with a new `<details>`, and the P-03 chip in a dense table.
The packet's layout proof is the 28 demo-combined captures at 390/1440 plus the P-03 rectangle script. That is what the build
sheet asks for, and it is credible. But `layout-evidence.mjs` is not mentioned, either as run or as "not run" with a reason.
**Fix:** add one line saying it was not run and that the sheet's capture gate stands in for it.

### L4. Record D3 as a guard change for the PC whole-diff review (process)
`tools/checks/missing-claim-scan.mjs:77-83` adds a fourth `REVIEWED_EXEMPTIONS` entry. This review accepts it (see D3 below).
The scan header says that adding an entry is a guard change for review, so PC's reviewer and the Architect's decision log
should see it once. It is not a code change.

## Judgement calls requested

**D3: guard exemption. Accepted as narrow and justified.** I checked three alternatives that would not loosen the guard:
- **Route through `<MissingClaim>`.** This needs a `mock_gaps` registry gap and a literal `gapId`/`placement` at each JSX site.
  An unparseable wire instant is not a catalogued product gap. The formatters also return strings into many contexts
  (attributes, joined sentences, SVG text), so they cannot wrap JSX. Registering a fake gap would corrupt the registry.
- **Add a baseline entry.** That grows a baseline whose rule is that it may only shrink. It would be worse than a reviewed exemption.
- **Reword so the cue does not match.** The text "Time not available yet" is ruled verbatim (§5 PB-1 tests; Addendum 7 Q3).
  It also follows the owner's "not available yet" rule for missing data.

The entry follows the existing pattern exactly: one file, one const, the exact text, and every reference to the const in
the same file. Only `time.test.ts` imports the const, and tests are outside the scan. It also has a pass test and a
mutation test (moving it to another file, or using the phrase inline, fails). The live scan passes. This is the least
loosening that is available.

**`portfolio-week` not settling at 1440: not caused by PB-1.**
- The line is `OUTCOME_MATRIX_LOADING` (`estate/PortfolioOutcomes.tsx:278,341`). It shows while `reads.getOutcomeSummary(window)`
  (`estate/EstatePortfolio.tsx:721-735`, `estateClient.ts` `/outcome-summary`) has not resolved, and `LOADING_LINE` holds settle on it.
- PB-1 does not touch this path. In `EstatePortfolio.tsx` the only change is the scope-disclosure day range (`:499`). `estateClient.ts`
  and `PortfolioOutcomes.tsx` are unchanged. The window object and `windowKey` that feed the request are unchanged, so
  the frontend sends the same request PB-0 sent.
- It settled at 390 in the same full run, and PB-0 got 28/28 settled on the same DEMO-A backend. So this is backend
  latency or tick contention on the outcome-summary read, not a frontend hang.
- Residual: the matrix's own rendering under PB-1 has no capture. PC's 28/28 settled requirement covers it.

**Flakes: pre-existing, not PB-1.**
- `evEnergy.test.tsx` and `evScenarios.test.tsx` run alone pass 16/16, and PB-1 changed only expected strings in them.
- The same two failures under full-run load are already recorded before PB-1: `.agent/OUT-A-packet.md:83`
  (`energy_states_table_loading`) and `OUT-D-packet.md:72` / `OUT-D-phase-handoff.md:38` (evEnergy R347).
- The 3 `w1f4VerificationStructure` failures are identical on main `ab248b4c3`. Both runs have the same extra
  `<p class="claim-label">` "Technical result verified on test data…". They are unrelated to the banner.

## Spec checks

- **`time.ts`** (`frontend/src/ui/time.ts`).
  - Forms match §3: `29 Oct 2026`, `29 Oct 2026, 16:00`, `16:00`, a same-day range, and a cross-day range with both ends in full.
  - It computes in UTC. Microseconds are truncated. `hour % 24` guards the h23 quirk.
  - An unparseable value gives `TIME_NOT_AVAILABLE` and never the raw string. Several formatters used to echo `value`
    (Foundation, SiteFindingIndex, SiteWorkActions, EvScenarios, SiteHealth, globalWork); that is now fixed, as Q3 requires.
  - `formatDayRange` handles one day, the same month, across months and across years (`28 Dec 2026 – 3 Jan 2027`), and a reversed range.
  - Null words are kept: `plainTime` null, Site Health "none", SiteWorkActions "none", Foundation "no end", EvEnergy "Unknown",
    SiteFindingIndex "not recorded", and `when` "not reported" (the same as the old `stamp`).
  - Seconds appear only where ruled: R372 work historical lines, R369 WR history, Site Health, EvEnergy, and the cold `hm`/`dayHm`.
    Live and latest lines are minutes only. Estate "Information as of" and "Historical as of" drop seconds, which is consistent with Q5.
- **`TimeZoneNote`** renders `<span data-time-zone-note="utc">Times in UTC</span>`, and its only text is the exempt "UTC".
  The `dueDates` variant exists but nothing uses it, which matches Q6. It appears once in each bar: estate, Kobo day control,
  cold selected/requested bars (mutually exclusive), EV window/refused head, global work status line, WR bar, and verification strip.
- **§3.1 rows applied** (Shell ×3, Kobo day label and bounds sentence, Kobo state line, Cold, EV, Work, Portfolio/Findings ×3,
  "Well supported"): each matches the sheet's text. Q5 detail: the Show button stays in the bar, and the `<details>` is open when `known_at` is set.
- **Builder copy outside §3.1** ("Showing an earlier point in time.", "Point in time", "From"/"To (not included)",
  "Change the dates or open a Site record.", the UTC-free captions) is plain, and I found no banned vocabulary in it.
  The product-vocabulary vitest passes.
- **Shell.**
  - `SIMULATOR_LAB_ENTRY_POINT_LABEL = "Simulator Lab"`.
  - The banner text matches D-1. It has `role="note"`, 12 px, is not dismissible, and uses tokens that exist in `tokens.css`.
  - The badge maps "Demonstration data" to "Example data". Other modes keep `{mode} · {id}`.
- **P-03.** The CSS rule is the sheet's text verbatim (`estatePortfolio.css:56`). The rectangle script (`scratchpad/pb1/p03-check.mjs`)
  measures each chip against its `td` right edge and against the next cell. Its LONG and NOCSS mutation modes support the
  packet's non-vacuous claim. The evidence is credible.
- **Test expectation updates.** I spot-checked about 40 files.
  - The changes are string-for-string copy updates. The test diff has more added lines (225) than removed (160), and no `.skip`, `.only` or `todo`.
  - The structural changes are justified:
    - `pageNote()` scoping exists because the banner is a second `role="note"`.
    - The Lab entry-point check filters out the Lab rail's own `aria-current="page"` link. The non-current link is still asserted absent.
    - `expectLatestCheckedLine` asserts the exact scope and "updated …" forms with regexes.
    - The provenance badge tests lose the Site id assertion. That follows from the §3.1 row ("Example data" replaces the code).
  - One test is weaker: `.window-day` `not.toContain("end excluded")` replaces a positive check. It is acceptable because the sentence is now deleted.

## Checks I ran

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run src/ui/__tests__/time.test.ts src/sites/__tests__/evEnergy.test.tsx src/sites/__tests__/evScenarios.test.tsx` | 3 files, 24/24 passed |
| `npx.cmd vitest run src/estate src/shell src/ui src/work` | 84 files, 1666/1666 passed (158 s) |
| vitest on the 16 changed `src/sites/__tests__` files | 16 files, 685/685 passed |
| `vitest w1f4VerificationStructure.test.tsx` on branch and on main `ab248b4c3` | 3 failed in both, same assertion (pre-existing) |
| `node tools/checks/missing-claim-scan.mjs` | passed (43 tagged, 10 baselined, ceiling 16) |
| `node --test test_missing_claim_scan.mjs test_evidence_checks.mjs test_mock_deviation_labels.mjs` | 50/50 passed |
| `node --check tools/w1-ux-07-rail-evidence.mjs` | OK |
| `powershell -NoProfile -File tools/check-all.ps1 -Python …plan2\.venv\Scripts\python.exe` (no Bypass) | All 12 guards passed, including navigation truthfulness, the missing-claim scan, and mock deviation labels/client vocabulary (estate guard self-tests took 478 s) |

**Not rerun:**
- The full vitest suite. I cite the implementer's run at `dfca8d5a8`, which matches the reviewed code: 3563 passed, 5 failed, 147 files, 315 s.
- The production build, serve, captures, and `layout-evidence.mjs`. Per the dispatch, no serve or browser was used.
- The capture numbers (0 UTC hits, 666 counted hits, the P-03 rectangles) are the packet's. I checked them against the script, not by rerunning them.

## Residual risk not named in the packet

- `instantMs` uses `Date.parse`. That parses a non-ISO string without a zone (for example "2026-10-29 16:00") in the browser's
  local zone, not UTC. Wire instants carry a zone, so this is latent only.
- The banner sits above `.app-frame__content` on every operator page and adds about 26 px of height. The 390 captures cover the 14 keys only.
