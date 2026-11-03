# Review: MA-1, v70 mock addendum (M1–M6)

- Reviewer: independent Claude reviewer, 2026-11-03.
- Branch `task/MA-1-mock-addendum`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ma1`, head `29d552bf3`.
- Diff `git diff main...HEAD -- ':!.agent'`: `frontend/mockups/v70/{index.html,outcomes.css,outcomes.js,portfolio.js,screens.js}` only.
- Judged against `brief-MA-1-mock-addendum.md` and the MA-1 rulings (Q1–Q8, plan line 142).

## Verdict: REVISE

One Medium finding (Grow rows open by default). Fix it on the branch, or get an explicit owner or Architect ruling that accepts it. Everything else meets the brief. The Low findings are optional polish, but L1 and L2 are worth doing in the same pass.

## Checks run (by me, at 29d552bf3)

| Check | Result |
|---|---|
| Rebuilt `index.html` from the branch sources in scratch (`node build.mjs` on copied files) and ran `cmp` against the committed file | **Identical** |
| Files outside the mock | None changed, apart from `.agent` |
| `node --test tools/checks/test_mock_deviation_labels.mjs` | 14/14 pass. The guard tests only its own fixtures, as the packet says. |
| `node --test frontend/docs/architecture/test_mock_gaps.cjs` | 13/13 pass |
| Headless Chrome CDP script (scratch, modelled on `measure-mock-panels.mjs`) on the 7 named screens at 1440×1000 and 390×900 | See below |
| Regression: built main's v70 in scratch and compared the `<main>` innerText of all 110 SCREENS, branch vs main | **Only the 7 named screens differ.** No other v70 screen changed. |

### CDP results

- **Page scroll.** At rest, `scrollWidth = clientWidth` on every screen at both widths.
- **Additions inside the viewport.** All new elements (`.ob-days`, `.why-btn`, `.ob-grow`, `.oc-pfgrow`, `.fix-head`, `.opp-list`, `.oc-recur`) sit inside the viewport. The one exception is `.oc-noact` at 390, which sits inside the Portfolio table's own scroll wrapper (338/720, the same as main).
- **Counts:**
  - "Why?" buttons: portfolio 4, mini 4, cold 3, ev 3.
  - Grow parts: 3 on mini and 3 on ev; Portfolio has a 3-term `dl`.
  - Fix timeline: 5 steps on finding-history and on verification, with "Change made" current.
  - Opportunity row: 1.
  - Problem-history lines: on the mini and cold boards.
  - Portfolio `.oc-noact`: 2 (F-119 and F-109).
- **Every one of the 14 "Why?" buttons at both widths:**
  - Keyboard Enter, keyboard Space and mouse click each open the dialog.
  - A second click closes it, and Escape closes it.
  - Focus moves into the dialog.
  - No `<details>` open state changes, so no summary toggles.
  - At 390 it is a bottom sheet (left 0, right 390, bottom 900).
- **HTML.** Nothing interactive is nested inside an `<a>`. Every button has an accessible name; "Why?" carries `aria-label="Why? <Site> · <outcome>"`.
- **Vocabulary.** No thread, snapshot, revision, COMPLETE/PARTIAL, state code, "load" or "lab" in any new element's visible text, the "Why?" dialogs included.
  - The words that match in added lines are all pre-existing v70 text on touched lines: "Revision history", "productive load", and `state:` keys.
  - The cold-chain "door and loading" wording is v70's and is about stock, not power. New copy reuses it in three places, and I judge that acceptable.

### Data consistency

I traced every figure in `DAYS`, `PFDAYS`, `GROW`, `WHY`, `HIST` and the opportunity row to main's v70 sources, or to the packet's illustrative table:

- **Existing v70 values:** 24 of 30 days, 462/500 h, PM-0447, TMP-003, SES-011 at 3.6 kWh, SES-012, 1 interrupted and 1 unknown of 12, 10 kW × 1 h, 120 kWh in 10 complete sessions, 5 of 30 days with lowest 22%, 92%, 30 of 60 minutes, 3 of 5 days, "under a fifth", 15:00–16:00, 0.30 L/kWh, $1.20/L, $0.40, $2.50 = 10 kWh × $0.25, $36.00.
- **New illustrative day counts:** all are listed in the packet, and they agree with `DAILY`:
  - `DAILY.mini.cov` is 88–99, with 92 on 6 Oct;
  - `DAILY.cold.cov` is 99–100;
  - the Depot 08:00–16:00 window has its 15:00–16:00 gap.
- I found no tuned or demo-build numbers.

### Rulings

All applied:

- **Q1:** v70 data only.
- **Q2:** the new values are listed in the packet.
- **Q3:** Kobo Target reads "No target set yet", and the filled format is given for CH-6.
- **Q4:** per-Site figures with "not added together".
- **Q5:** no lab wording; recorded as a MOCK DEVIATION candidate.
- **Q6:** a sibling button with its own tab stop; the Portfolio card is now a `div` with a stretched `.oc-cardlink`; no summary toggle.
- **Q8:** "Review recommendation" plus "· No action agreed yet", outside the link.

### Not verified

- Behaviour with a screen reader: I checked only the DOM roles and names.
- Touch gestures on a real device.
- The `measure-mock-panels.mjs` numbers. I did not rerun them; my own CDP run covers the same width checks.

## Findings

### M1 (Medium): Grow rows now open by default, which pushes "Needs attention" rows far down the Site boards

- **Where:** `frontend/mockups/v70/outcomes.js:112`, the `${x.st==='needs'||parts?'open':''}` condition (packet deviation 5).
- **What I measured** (row top y, main → branch):

| Screen | Width | Row | Main | Branch |
|---|---|---|---|---|
| mini | 390 | Optimize, Needs attention | 899 | 1766 (about two screens down) |
| mini | 1440 | Optimize, Needs attention | 528 | 890 (body now below the fold) |
| ev | 390 | Protect, Needs attention | 1072 | 1893 |

  Page height grows from 3741 to 4742 (mini 390) and from 3921 to 4836 (ev 390).
- **Why it matters:**
  - v70's board opens only the rows that need attention, so what needs a decision comes first. This change makes an "Opportunity" row the first thing open on Kobo and Depot.
  - It changes a v70 screen beyond what M3 requires. The brief says M3 must be visible on the screen; it does not require the row to load open.
  - CH-6 and CH-5b will copy this rule, because the mock is the layout spec.
- **Fix:**
  - Restore v70's open rule (`x.st==='needs'` only) and keep the three parts in the row body.
  - Capture the M3 evidence with the Grow row opened, by clicking it in the capture script.
  - If the owner wants the parts visible on load, put a one-line compact form in the summary instead: "Target: none set · Potential: 18–20 kW · Income: $2.50 per window".
  - Either way, record the choice as an owner or Architect ruling, not an unflagged mock rule.

### L1 (Low): Kobo's Estimated income is a per-window rate, not an amount over the days

- **Where:** `outcomes.js:70` (`GROW.mini`) and `:73` (`pfGrowParts`).
- **What is wrong:** the brief's M3 shape is an amount at a price over the counted days ("42.08 at the declared price"), with the Portfolio card giving each Site's figure over its days.
  - Kobo shows "$2.50 per eligible window", with "3 eligible one-hour windows on the 3 checked days" as its days line.
  - Depot shows a 6 Oct amount ($36.00).
  - So the two Sites' parts have different shapes, and CH-6 has no Kobo example of the amount it will build.
- **Fix:** either show "$7.50 over 3 checked study days (3 × $2.50) at the assumed $0.25 per kWh" and list $7.50 as a derived illustrative value under Q2, or add a MOCK DEVIATION candidate note that CH-6 shows an amount over the days.

### L2 (Low): Escape and close do not return focus to the "Why?" button

- **Where:** `screens.js:1122` (shared Escape handler) and `openWhy` (`outcomes.js:94`).
- **What is wrong:** after Escape, `document.activeElement` is `<body>`. A keyboard user loses their place on a long board. The confidence popover has the same behaviour, so this is inherited, but CH-5b will implement it from the mock.
- **Fix:** store the trigger button on the popover, and focus it again on Escape and on toggle-close.

### L3 (Low): the last Portfolio "Why?" causes 3 px of horizontal page scroll at 1440

- **Where:** `outcomes.js:95`, where `left` is clamped with `innerWidth`, which includes the scrollbar.
- **What is wrong:** opening the Assure card's "Why?" puts the dialog's right edge at 1428 against `clientWidth` 1425, so `scrollWidth` becomes 1428.
- **Fix:** clamp with `document.documentElement.clientWidth`.

### L4 (Low): the bottom sheet has no visible close control

- **What is wrong:** at 390 the sheet covers about 40% of the screen. It closes by tapping outside it, by Escape, or by tapping "Why?" again, but there is no visible "Close" or "×".
- **Why it matters:** it is dismissible, but a touch user is not shown how.
- **Fix:** add a labelled close button in `.conf-head` for the sheet.

### L5 (Low): "Why?" sits inside `<summary>` on the Site boards

- **What is wrong:** `summary` has an implicit button role, so assistive technology sees a button nested in a button (axe `nested-interactive`), and the summary's accessible name includes "Why? …".
- **Why it is only Low:** this is consistent with the Q6 ruling ("does not toggle summary rows"), and the behaviour is correct.
- **Fix:** either note it for CH-5b, or move the button and the days line just after `</summary>` in the row head.

### L6 (Low, consistency): "Opportunities to grow" lists only Kobo, though the same screen and the Depot Grow row present a second opportunity

- **Where:** `screens.js` `oppListPanel()`.
- **What is wrong:** the findings-opportunities lens panel directly below still shows "Chargers mostly idle" (Depot, `kind:'opp'`), and Depot's Grow row shows it as "Potential". The new list's note ("Each opportunity is one row") reads as if Kobo is the only one.
- **Why it is only Low:** the brief asks for the Kobo row only.
- **Fix:** add the Depot row, saying in words that it is an early signal and not priced, or change the note to "Findings with an opportunity · early signals are listed below".

### L7 (Low, cosmetic): the Portfolio Grow card sets the height of all four cards

- **What is wrong:** card height goes from 270 to 413 at 1440, and the other three cards carry about 140 px of empty space. Their `value-basis` line also sits at the bottom with a gap. At 390 the Grow card is 535 tall (main: 333).
- **Fix:** acceptable for a mock. Optionally compress `.oc-pfgrow` to three single lines.

## Residual risk not named in the packet

- The `HIST` problem-history lines appear wherever an issue id matches, including the cold Protect row's F-118. The two cold rows therefore repeat the identical line, which is visible on the cold board.
- The GreenHarvest days lines use a 7-day period ("7 of 7 days checked across 24 h") while Kobo's Protect line uses 30 days. Both are consistent with `DAILY`. But the mock shows no period selector state that explains why the two Sites differ, so CH-5b should take the period from the window, not from these literals.
