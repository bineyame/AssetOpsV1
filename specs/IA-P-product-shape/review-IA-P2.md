# IA-P2 review (P3a, P3b, P4a and D-IAP.34): discovery round 1

Reviewer: fresh Claude reviewer (not the author). Branch `task/IA-P2-portfolio-figures`, head `b332feb9a`, worktree
`/opt/assetecon/AssetOpsV1-iap2b`. Diff `main...HEAD` (72 files). Judged against `spec.md` rev 3 §3, §4.2, §6 P3a/P3b/P4a,
`spec-period.md` P.1 to P.9, D-IAP.34, register rows R784 to R789.

## Summary (round 1)

- **Verdict: accept with findings fixed on the branch** (two Medium, four Low; no High).
- The backend (E2, E0, E1) matches P.2 to P.8; the plants and failing-first runs are credible and the focused tests pass.
- The Overview by mode, the three tabs, Results, the scope section, the aliases and `entryRange` match the P3b card.
- M1: the "Month by month" table runs text together ("September 20263 of 4 Sites"; "Fuel cost −$755.00Optimize cost
  and efficiency"), seen in my shots at 1440 and 390.
- M2: the shot set misses the card's required Overview modes (period, none) and the 1280 width, and the gate's default
  E2 stub serves a body for another range, so the recorded Overview shot shows a false bar state and a wrong note.
- Lows: D-IAP.34 `out` line picks the wrong month on 3+ months; a new unhandled rejection in `sharedRange.test`;
  an empty, unlabelled `<nav>` in the period header; the dead 5c fixture.
- The 140-test migration table was spot-checked (DeepDiveMonth, estatePortfolio, sharedRange, rail lists): every
  case read is a (b) migration citing the right section; no loosened assertion found.

## Findings

### M1 (Medium, acceptance gap: honest numbers, readable figures) Month-by-month cells run their two parts together

- `frontend/src/estate/PortfolioPeriod.tsx:72` and `:88`. `<small className="dd-meta">` sits inline right after the
  month link and after the driver, with no space or block break. Rendered text: **"September 20263 of 4 Sites"**,
  **"October 20263 of 4 Sites"** and **"Fuel cost −$755.00Optimize cost and efficiency"** (my shots, World G and World P
  period bodies, 1440 and 390). The year then reads as a five-digit number beside a count, on the front page's table.
- Why it matters: the period hub is the new front page for any range over two months; the run-together year is a
  misreadable figure (UI standing brief: honest numbers).
- Fix: make these `small`s a block line (for example `.dd-month [data-period-months] small { display: block }`, as 5c's
  other two-line cells do) or render them in their own element; add a vitest assertion that the row header's text
  content is "September 2026" and "3 of 4 Sites" separately (or that the link's text is exactly `month_words`) and a
  one-line gate check that no `[data-period-month] th` text matches `/\d{5}/`.

### M2 (Medium, layout evidence) The Overview's modes are not in the shot set, and the recorded Overview shot shows a false state

- Spec §6 P3b "Shots": "the three tabs and the Overview **in each mode** ... at the three widths, light and dark".
  `/opt/assetecon/evidence/IA-P/IA-P2/iap/` holds one `_portfolio` shot set (mode month) at 1440 and 390 only; there is
  no period or none Overview shot and no 1280 width in `iap/` (`dd/` has World X only). The packet §4 says "the three
  widths, light and dark".
- `tools/iap_gates.cjs:47`, `:122`: any range not in `PERIOD_BY_RANGE` is answered with `period-month-2026-10.json`,
  which is E2's body for **2026-09-01..2026-10-31 with September missing** (`shown` = October, note "No figures are
  served for September…"). So the recorded `_portfolio-1440x900-light.png` (range Last month, 1–31 Oct) shows the bar's
  "Showing 1–31 Oct of the range" and a September note, both false for that range (P.1 table: Last month is "All
  pages"). With the range-true fixture `period-month-g-2026-10.json` the same page reads "All pages" (my run, below).
  H6 still catches the `span` plant, but its positive case is satisfied by a body that was not made for H6's range.
- Fix: key the stub truthfully (`2026-10-01|2026-10-31` → `period-month-g-2026-10.json`; keep the September-missing
  body only for its own range, or generate one for `2026-10-01..2026-11-21` for H6 with the November partial note);
  capture the Overview in modes month, period (World G, with `[data-dd-out]`) and none at 1440, 1280 and 390, light and
  dark; correct the packet's shot line.

### L1 (Low, spec literal, latent) D-IAP.34 `out` line comes from the earliest, not the latest, month on 3+ months

- `backend/assetops_backend/deep_dive/period.py:297`: `for v in (latest, *vs[:-1])` tries the latest month, then the
  **earliest** upward. P.5: "each line is `V_m.out_line(code, reasons)` of the latest served month in which it is out".
  For a Site out in months 1 and 2 of three (not 3), the line is month 1's. `out_line` depends on the month's reasons
  (actual/target missing, currency), so the sentence can differ. World P has two months, so no test sees it.
- Fix: `for v in reversed(vs)`; add a three-month case to test 13 where the reasons differ between months.

### L2 (Low) New unhandled rejection in `sharedRange.test.tsx`

- `frontend/src/shell/__tests__/sharedRange.test.tsx:265` (R7/R8): clicking the rail Portfolio link now mounts the
  Overview, whose `DecisionsRows` reads `portfolio` through the shared cache; the fixture client rejects
  ("the W3-01 roots do not read the Portfolio", `estateFixtures.ts:178`). Vitest reports "2 unhandled errors" and
  exits non-zero even with all tests green (my focused run). Not in the packet's counts.
- Fix: give that test a portfolio answer (or a client whose `portfolio` returns a refusal), so the run has no
  unhandled errors.

### L3 (Low, accessibility) Empty, unlabelled navigation landmark in the period header

- `frontend/src/estate/PortfolioPeriod.tsx:115`: `<nav className="dd-nav">` holds only `<b>{periodWords}</b>`, no link
  and no `aria-label`. Screen readers announce an unnamed navigation region with nothing to navigate.
- Fix: a `<div className="dd-nav">` (the class keeps the look), or `aria-label` plus the links if any are intended.

### L4 (Low, tidy; packet question 1) Dead fixture

- `frontend/src/estate/__tests__/fixtures/portfolioTabsOverview.before.html` is referenced only by a comment
  (`DeepDiveMonth.test.tsx:517`). Delete it on this branch and reword the comment (`.ai/RULES.md` keep-it-tidy).

### Not findings (checked)

- `entryRange('/portfolio')` last month and `/findings` 7 days; the `/portfolio/month?month=` alias drops `month` and its
  days win; Results and the Evidence scope section render `ProgressPanel`/scope verbatim; refusal handling (401 sign-in,
  422 no retry, others "Try again"); the client's schema and `out` check; `useDeclareRangeSpan` only on non-null `shown`.
- `view.py` is unchanged (`git diff main...HEAD -- backend/assetops_backend/deep_dive/view.py` empty).
- Register R784 to R789 match spec §7's MD-IAP-3, -7, -10, -11, -12, -16.

## Checks run (at `b332feb9a`)

- `ASSETOPS_GUARD_PYTHON=… pwsh tools/check-architecture.ps1`: "Architecture check passed."
- `pwsh tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- test_iap_portfolio_period.py test_iap_portfolio_sites.py
  test_iap_waiting_counts.py test_w303_portfolio_api.py`: 91 passed.
- vitest (heavy slot) `portfolioHub`, `Results`, `DeepDiveMonth`, `estateEvidence`, `sharedRange`,
  `estatePortfolioRoutes`: 6 files, 94 passed, **2 unhandled errors** (L2). `tsc --noEmit`: clean.
- Lean shots (my script, `vite preview` on the head's build, gate fixtures): `/portfolio` in mode period (World P and
  World G), none, and month on the range-true World G body, at 1440 and 390. Page width equals the viewport at 390 in
  every mode; no page error; `[data-dd-out]` reads "Thika: not a mini-grid Site, not included." on World G only; the bar
  says "All pages" on 1–31 Oct with the World G body. Shots deleted with the scratch folder.

Cited, not rerun: the builder's broad vitest (main 1981/4 failed, head 1998/8 failed, extras timing flakes), backend 43
files (1223, the one main failure), `iap_gates` 50/50, `deep_dive_gates` A 9/9 and X 7/7, the plants.

## Not verified

- The full backend set over Postgres and the broad vitest run (cited). The plants (not replanted). Dark mode of the new
  period and none layouts (my shots were light only). The v70 mock element by element for the period hub (its
  departures are registered as MD-IAP-10, -11, -16).

## Residual risk the packet does not name

- The demo's first story link, "Portfolio, week to story day S" (`tools/demo_combined.py:354`), is a 7-day range, so the
  Overview opens in mode `none` (no figures) on the walkthrough's first click, besides the unwarmed reads of Risk 1.
- In mode `month`, E2's `notes` and 5c's own month body are read separately; a store change between the two reads can
  show a month whose note set differs from its body (low; both are served snapshots).

## Questions for the Architect (each with a default)

1. **Demo prebuilt responses (packet Risk 1).** `prebuilt_routes` maps `/portfolio?` to the estate reads only; the
   Overview now reads `/api/portfolio/period` and `/api/portfolio/month` (and its L2 still reads the estate portfolio).
   **Default:** a small follow-up task before the next demo build (not blocking this merge): `prebuilt_routes` adds
   the E2 request for each `/portfolio?` link and the month request for E2's served month, and `story_links` gains (or
   switches to) a whole-month Portfolio link (the last closed month before S) so the walkthrough opens on figures; the
   week link stays for the lists.
2. **The dead tab-row fixture (packet question 1).** **Default:** delete it on this branch with L4 (no ruling needed).
3. **World ladder L2 `code` rebuild after merge (packet Risk 3) and the load flakes (Risk 4).** **Default:** the
   coordinator rebuilds the current rung once after merge, as spec §8 says; the `s502OverviewFindingList` and
   `simulatorLabGate` flakes go to the test-suite speedup backlog with their file names, not fixed here.
