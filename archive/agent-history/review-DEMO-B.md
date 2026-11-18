# Review: DEMO-B (combined-dataset captures, v70 comparison, walkthrough runbook)

Reviewer: fresh Claude reviewer (did not author). Date: 2026-11-01.
Worktree `C:\Users\assef\Bineyame\AssetOpsV1-demob`, branch `task/DEMO-B-captures`, head `f6ceb6eda`, base `d2e8407e4`.
Diff reviewed: `git diff d2e8407e4...f6ceb6eda` (61 files: 50 PNGs, 5 JSON/log files, packet, register +20/-0,
`.ai/ACTIVE_CONTEXT.md` +1/-0, `.ai/CODE_STATE.md` +12/-0, `tools/demo-combined-evidence.mjs` +258).
Spec: COMBINED §6 (B1-B3) plus DEMO-SPARSE Addenda 1-4.

## Verdict: REVISE

There is one Medium finding: R633 duplicates R154. It is a one-row register fix. Everything else is Low. The tool,
the captures, the CO-4 mapping, P-01 to P-10 and the runbook all hold up. Once R633 is fixed, a coordinator check is
enough. A full re-review is not needed.

## Findings

### Medium

**M1. R633 duplicates R154.** It is at `.agent/mock-departure-register.md:632`. R154 is at
`.agent/mock-departure-register.md:256`, on B2-05, for mini, evidence, dispatch, analysis and health. R154 already
registers the same departure on `mini`: "Status strip content differs: mock shows assessment chips (Needs attention,
Confidence: Low, Evidence limited, Asset assessment: Watch)…". R633 restates that mock element ("Status bar 'Needs
attention · Confidence Low…'") and adds a self-referential reason: "the reviewer confirms it is not a duplicate". The
reviewer does not confirm that. The packet flagged this itself at `.agent/DEMO-B-packet.md:177`. Leaving the row in
breaks the brief's "none duplicates an existing row" rule. It also leaves two live rows for one element, with
different categories (R154 is D1, R633 is D2).

Fix: remove R633, or turn it into a cross-reference ("see R154; the DEMO-B capture shows the freshness strip text"),
and fix its category to match R154. Add R154 to the "already registered" list at `.agent/DEMO-B-packet.md:48-51` and
to the register preamble.

### Low

**L1. P-04 does not name the standing rule it conflicts with.** P-04 is at `.agent/DEMO-B-packet.md:68`.
COMBINED §6 B2 says "No visible MOCK DEVIATION label", so the defect is real. I saw it in `wr-overview-1440.png`
(R396, R363, R365) and in the `captures.json` hits for R453 at 390. However, `.agent/mock-departure-register.md:212`
requires every open D1/D2/D4/D5/D6 row to show `MOCK DEVIATION Dn` beside the affected element. The polish round
cannot just delete the labels: it needs an Architect ruling first (for example, a demo-mode suppression, or closing
the rows). Fix: add that dependency to P-04.

**L2. A packet claim contradicts the captures.** At `.agent/DEMO-B-packet.md:170` and in P-04 ("in the text at 1440
too"), the packet says the R453 label is counted at 1440. It is not. `captures.json` has the R453 and MOCK DEVIATION
hits only at 390 for `kobo-board-S`, `kobo-board-S1`, `cold-board-*` and `ev-board-fault`. `innerText` already
leaves out `display:none` text. Fix: correct both sentences.

**L3. The card comparison misses outcome cards on two screens.** `.agent/DEMO-B-packet.md:46` says "Cards match 4/4
where the mock has them". `compare-run.log` reports cards 0/0 for portfolio and mini. Yet `portfolio-week-1440.png`
and the v70 portfolio mock both show four outcome cards. The `.cards,.v69-cards` selector at
`tools/demo-combined-evidence.mjs:107` does not match them. Those two screens were not card-compared. Fix: state this
as a limit of the measurement, or widen the selector in a later tool pass.

**L4. A half-loaded capture would not fail the run.** At `tools/demo-combined-evidence.mjs:194-206`, when the page
has not settled within 60 s the tool logs `WAIT`, still writes the PNG and the measurements, and exits 0 (line 258).
The settle check (lines 151-163) needs three stable reads 600 ms apart and no word "Loading" in `<main>`. A read
that lands more than about 1.8 s after a stable render, without any "Loading" text, could still be captured early. In
this run every capture recorded `settled: true`, so the evidence stands. But the tool does not block a half-loaded
page: it records it and carries on. Fix: exit non-zero when any capture is unsettled. Also, if Chrome fails to
start, the tool throws without stopping it (no try/finally around lines 123-212), which leaves an orphan headless
Chrome.

**L5. The runbook has two copy-paste gaps.**
- Step 2 (`.agent/DEMO-B-packet.md:121`) describes the `PYTHONPATH` value in words. It should give the literal
  PowerShell line with the absolute paths for `AssetOpsV1-demo3`.
- Step 5 (`.agent/DEMO-B-packet.md:142`) uses `$(node tools/demo-combined-evidence.mjs mock-ids)`. In PowerShell,
  which steps 2-3 use, that passes all 11 ids as one argument. It only works in bash. Name the shell, or give the
  PowerShell form, for example `(node … mock-ids) -split ' '`.

Step 1 uses bare `python` while step 2 uses the venv interpreter. Apart from these, a person could follow the
runbook: the routes, the windows and the stop steps are correct.

**L6. Two contradictions on screen are missing from the polish and copy lists.**
- `ev-board-fault-1440.png`: the Optimize row says "a tariff estimate exists in Financials", while Grow, the money
  panel and Next step all say no EV tariff is published (R628). A client sees two answers, the same kind of defect
  as P-09.
- Kobo Assure reads "No objective declared" on day S (`kobo-board-S-1440.png`) but "Unknown" on S+1
  (`kobo-board-S1-1440.png`). R627 (`.agent/mock-departure-register.md:626`) says Kobo declares no Assure objective,
  which does not explain the S+1 chip.

Fix: add both to the polish list (P-11 and P-12) or to the client-copy list.

## What I checked and what I saw

**The tool.** I read all 258 lines of `tools/demo-combined-evidence.mjs`. `node --check` exits 0, and its import
`tools/evidence-checks.mjs` exists. It captures 14 keys at 1440 and 390 px; the 28 PNG headers confirm the widths. At
1440 the page measures 1425 px of content because of the scrollbar, the same as the mock captures. With
`captureBeyondViewport`, the full-page heights are real: for example `kobo-board-S-1440` is 2476 px and
`cold-board-failure-390` is 4616 px. `requireWidth` is called before and after every navigation, including the find
step. The diff touches only `tools/*.mjs`, `.agent/` and `.ai/`: no product code, Python or data changed.

**Settle evidence.** All 28 records in `captures.json` have `settled: true`, `overflow: false` and empty
`stale_words`. The log ends "exit 0 wall 270 s".

**The windows match the spec.** The week window is S-6d to S+1d (10-23 to 10-30). The month window is S-28d to S+3d
(10-01 to 11-01). The cold and EV boards use the `start`/`end` event windows from `days.json`, which matches
Addendum 1 (a). The CO-4 to R632 mapping is honest. `kobo-verification-1440.png` shows "60 min → 0 min", "0 kWh",
"Verified", and no cost line. `kobo-board-S-1440.png` shows the Cost row's Earlier entry with the modelled-change
line.

**Register rows R625-R634.** I compared each against the captures:

| Row | Result |
|---|---|
| R625 | Matches `portfolio-week-1440.png` (card headlines and strip). |
| R626 | "0.00 USD exposure in this hour", 200 min, "0.00 to 0.00 USD" all visible. |
| R627 | Accurate for day S (see L6 for S+1). |
| R628 | Matches the EV capture. |
| R629 | The window logic in the tool and the `Listed by the time each plan was first recorded` copy agree. The "0 requests on S+1" claim was not captured. |
| R630 | WR-000006 shows no repeat notice, and the cold board shows "Repeated maintenance without a result". |
| R631 | Two identical titles, told apart only by `a8cea97b` and `047d9a51`. |
| R632 | Accurate. |
| R633 | Duplicate (M1). |
| R634 | Confirmed in code at `backend/assetops_backend/site_outcomes/mini.py:697-699`: the modelled line appears only when the stored check is `MODELLED_IMPROVEMENT`. The S+1 capture shows the Assure row collapsed, so the text itself is not in the PNG. |

There are no ID collisions (no duplicate `| Rnnn` keys). R628 overlaps R263 and R53 (EV tariff) in subject, but it is
on a different screen, so it is not a duplicate. Citing R263 would help. The statuses are honest: R626 and R630 are
open because their causes are undiagnosed, and the rest are standing D4 data readings.

**Polish defects P-01 to P-10.** All are confirmed.

| Defect | Evidence |
|---|---|
| P-01 | `tools/demo_combined.py:447` prints `/sites/{code}/outcomes?…` and line 451 prints `/sites/KOBO-001/overview?date=`. `frontend/src/App.tsx` has no such routes, and its catch-all at line 563 is `RouteNotAvailableFrame`. The real routes are `SITE_DETAIL_ROUTE_PATH` `/sites/:siteId` and `SITE_EV_ROUTE_PATH` `/sites/:siteId/ev` (`operatorSiteRoutes.ts:35,257`). |
| P-02 | `demo_combined.py:447` uses whole-day windows. |
| P-03 | The chip overlaps the Action cell on all four rows of `portfolio-week-1440.png`. |
| P-04 | See L1 and L2. |
| P-05 | UUIDs in the Portfolio Finding cells and `REC <uuid>` on the EV timeline. |
| P-06 | Visible in `kobo-board-S-1440.png`. |
| P-07 | Visible in `wr-overview-1440.png`. |
| P-08 | Already in hand shows only PM-000013. |
| P-09 | Preventive shows "Not assessed · No due evaluator", while the cold board shows "Overdue" chips. |
| P-10 | "No incident recorded", while INC-000005 is listed Open. |

**`.ai/*` edits are append-only.** `--numstat` shows `ACTIVE_CONTEXT` 1/0, `CODE_STATE` 12/0 and the register
20/0. There is no merge commit in the range.

**Checks I ran:**
- `node --check tools/demo-combined-evidence.mjs` exits 0.
- `powershell -NoProfile -File tools/check-agent-workflow.ps1` passed.
- `powershell -NoProfile -File tools/check-architecture.ps1` failed the first time with "no Python interpreter at ''
  or .venv", because the worktree has no `.venv`. With `ASSETOPS_GUARD_PYTHON` set to the plan2 venv it passed. I
  did not use `-ExecutionPolicy Bypass`; the machine's effective policy already allows scripts.

## Not verified

- I did not rerun the captures, `serve`, Vite or Chrome. The PNG and JSON evidence is the implementer's, and I
  checked it for internal consistency.
- I did not rerun `check-all` 11/11. The packet cites it at `3dc50c75b`, which is one docs-only commit before head.
- I did not measure the runbook timings (3.1 s, 39 s, 41 s, 1.6 s, 2.5 s).
- R629's "0 requests on a window ending S+1d" has no capture.
- No frontend or backend suites ran. None apply, since no product code changed.

## Residual risk

- R626 (zero money over 200 avoidable minutes), P-07, P-08 and P-10 are client-visible contradictions with no
  diagnosed cause. They must be closed or scripted around before the client demo.
- Because P-04 conflicts with the register's label rule (L1), the polish round needs an Architect decision before it
  edits the labels.
- The verification link in the runbook uses an action UUID that changes on every rebuild. The runbook says to
  re-quote dates after a rebuild, but it should also say to re-quote that link from `links`.
