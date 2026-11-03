# Review packet: MA-1, v70 mock addendum for the chain screens

- Task: brief `.agent/brief-MA-1-mock-addendum.md` (in AssetOpsV1-plan2). The plan is §2.1 MA-1 and OD-P5.
- The Architect's pre-flight rulings were applied: Q1, Q2, Q4, Q5, Q6, Q7 and Q9 use the proposed defaults, Q3 uses the alternative (ALT), and Q8 is modified.
- Branch: `task/MA-1-mock-addendum`.
- Commits: `990bd7809` (M1–M6) and `5bfd7fec4` (the "No action agreed yet" separator). This packet and the measurements are in a third commit, the branch head.
- Owner opens: `C:\Users\assef\Bineyame\AssetOpsV1-ma1\frontend\mockups\v70\index.html`. It is a standalone file, so a double-click opens it. Screens: `#/portfolio`, `#/mini`, `#/cold`, `#/ev`, `#/findings-opportunities`, `#/finding-history`, `#/verification`.
- USER_REVIEW_REQUIRED: yes. The owner approves in one quick look; this is a brief acceptance item.

## Outcome delivered

The edits are in place in v70: `outcomes.js`, `outcomes.css`, `screens.js` and `portfolio.js`. `index.html` was rebuilt with `node build.mjs`. Existing patterns are reused:
- The "Why?" dialog uses the `conf-pop` family.
- Problem history uses the `oc-recur` style.
- Everything else uses `panel()`, `badge()` and `link()`.

No v70 screen outside M1–M6 changed.

| # | Where (mock id) | What was added |
|---|---|---|
| M1 | `portfolio` (4 cards), `mini`/`cold`/`ev` (each outcome row with a value) | A days line under each value. `DAYS`, `PFDAYS` in `outcomes.js`. |
| M2 | `portfolio` (4 cards), `mini` (4 rows), `cold` (3 rows), `ev` (3 rows) | A "Why?" button beside the value. It opens a popover with the value in one sentence, "Comes from" (2–3 lines), "Days used" (the M1 line), "What would change it", and an evidence link. At ≤600 px it is a bottom sheet (`.why-pop.sheet`). `WHY`, `whyPop`, `openWhy`. |
| M3 | `mini` Grow row, `ev` Grow row, `portfolio` Grow card | Target, Potential and Estimated income are three separate parts, each with its own days line (`GROW`, `growParts`). The Portfolio card names each Site's share and does not add them (`pfGrowParts`). Grow rows that have parts now open by default, so the parts are visible on load. |
| M4 | `mini` Optimize row, `cold` rows (issues), `finding-history`, `verification` header | A problem-history line under each finding issue (`HIST`, `histNote`). A five-step fix timeline (`fixTimeline`) is the new "Problem history" panel on `finding-history` and sits at the top of `verification`. The current step is "Change made", per Q7. |
| M5 | `findings-opportunities`, `portfolio` strip and rows | A new "Opportunities to grow" list row. The strip reads "1 opportunity: Kobo daytime solar". The F-109 portfolio confidence reads "Limited evidence: demand not measured yet" instead of "Demand not established". |
| M6 | `cold` Cost row, `portfolio` action column | ACT-051 is added to the cold Cost row's in-hand list. The portfolio action column shows "ACT-xxx · title" plus the state. F-119 and F-109 keep "Review recommendation" with "· No action agreed yet" beside it, per the Q8 ruling. The EV and cold Protect rows already listed ACT-061 and ACT-051. |

## New panel headings and copy literals (for CH-5b and CH-6 specs)

- **Panel "Problem history"** (finding-history). Note: "Same generator problem each time it is seen · the highlighted step is where it is now".
  - Line: "F-104 Seen on 24 of the last 30 days · same generator".
  - Steps: "Seen · 6 Oct", "Action agreed · 6 Oct", "Change made · Date not set in this example" (current), "Checked and working, monitoring · Date not set in this example", "Closed after 7 clean days · Date not set in this example".
  - The same block, without the panel, heads `verification`.
- **Panel "Opportunities to grow"** (findings-opportunities). Note: "Each opportunity is one row · open it for the detail".
  - Row: "Daytime solar unused at Kobo" / "Seen on 3 of 5 well-observed days · 18–20 kW at midday · F-109" / "Limited evidence: the grain mill's demand is not measured yet" / "Inspect the solar room →".
- **"Why?" dialog.** Its sections are, in order: the heading "<Site> · <outcome>" (or "Portfolio · <outcome>"), the value sentence, and the eyebrows "Comes from", "Days used" and "What would change it". The literal text for every entry is in `WHY` (`outcomes.js`).
  - Example, Kobo Optimize: "$3.31–3.97 cost exposure in this hour on 6 Oct." Comes from:
    - "The generator ran 30 minutes longer than needed, 14:20–15:20"
    - "Fuel at a public 0.30 litres per kWh × declared price $1.20 per litre"
    - "Includes $0.40 of generator wear, an assumed figure"
  - Days: "6 Oct partly checked · 30 of 60 minutes have every reading". Change: "Restoring the missing 14:50 battery report would settle the 30 unclear minutes." Link: "Dispatch evidence →".
- **Grow parts.**
  - Part labels: "Target", "Potential", "Estimated income".
  - Kobo: "No target set yet"; "18–20 kW of daytime solar unused"; "$2.50 per eligible window at the assumed $0.25 per kWh · not billed or collected".
  - Depot: "No target set yet"; "Chargers used under a fifth of capacity"; "$36.00 at the assumed $0.30 per kWh · not billed or collected".
  - Portfolio note: "Different days at each site, so not added together · not billed or collected".
  - **Filled Target format for CH-6 (Q3 ruling):** `"<target> · <verdict>, <n> of <N> checked days"`. Example: "300 kWh a month · too early to judge, 2 of 3 checked days".
  - Empty-Target days line: "No target, so no days are judged yet".
- **Problem-history lines (`HIST`):**
  - F-104: "Seen on 24 of the last 30 days · same generator"
  - F-118: "3 grid losses in 30 days · same backup generator · started by itself on 2 of 3"
- **Strip and action copy:** "1 opportunity: Kobo daytime solar". Action labels: "ACT-051 · Witness automatic-start test", "ACT-048 · Generator stop trial", "ACT-061 · Investigate connector 2", "ACT-049 · Restore battery-limit reporting". The no-action note is "· No action agreed yet".

## New illustrative values (Q2 ruling), each with the v70 record it is consistent with

| Value | Where | Consistent with (v70) |
|---|---|---|
| "3 of 5 study days checked · 1 partly checked · 1 with too little data, not counted" | Kobo Grow, Potential | CONF f109 "Only 3 of 5 days were adequately observed; day 4 is missing critical-service evidence" |
| "3 eligible one-hour windows on the 3 checked days" | Kobo Estimated income | Portfolio scope "Separate five-day study · 3 eligible one-hour windows" |
| "6 Oct partly checked · 30 of 60 minutes have every reading" | Kobo Optimize | CONF minifin "only 30 of 60 minutes support a money figure" |
| "30 of 30 days checked · 88–99% of readings each day" | Kobo Protect | `DAILY.mini[].cov` = 88–99, all ≥80% (AG-4 band) |
| "6 Oct partly checked · 92% of expected readings" | Kobo Assure | BOARD mini.assure "92% of expected readings" |
| "Counted from 3 work records, 14 Aug – 6 Oct" | GreenHarvest Optimize | BOARD cold.cost: visits 14 Aug, 18 Sep, 6 Oct |
| "7 of 7 days checked across 24 h · 6 Oct fully recorded" | GreenHarvest Protect | `DAILY.cold[].cov` 99–100; "Every step recorded" |
| "7 of 7 days checked · door and loading not recorded on any day" | GreenHarvest Assure | BOARD cold.assure "Loading and door records · Not available yet" |
| "6 Oct · 7 of 8 hours checked · 1 hour partly checked" (also "(connector 2)") | Depot Grow and Protect | 08:00–16:00 window; "Connector status missing 15:00–16:00" |
| "6 Oct partly checked · connector 2 status missing 15:00–16:00" | Depot Assure | Same record |
| "started by itself on 2 of 3" | F-118 history | RECUR F-118 "3 grid losses in 30 days · backup started by itself on 2" |
| Timeline "6 Oct" on Seen and Action agreed | F-104 | Revision history "6 Oct · 16:01 F-104 revision 1 constructed" |

Every other figure is an existing v70 value: $3.31–3.97 via `money()`, 18–20 kW, $2.50, $0.25, $36.00, 120 kWh, $0.30, $1.20 per litre, 0.30 L/kWh, $0.40, 8.2°C and 25–35 min.

## Checks run (all foreground, at 5bfd7fec4)

- `node --test tools/checks/test_mock_deviation_labels.mjs` (check-all line 66): 14/14 pass. Note: this guard tests only its own fixtures; it does not scan the mock.
- `node --test frontend/docs/architecture/test_mock_gaps.cjs` (mock-gap catalogue): 13/13 pass.
- Vocabulary scan of every added line (`git diff main` on the three JS files) for these words: thread, snapshot, revision, COMPLETE/PARTIAL, state codes, load. Every hit was pre-existing v70 text on a touched line:
  - "Revision history" and "revision 1 constructed" on finding-history;
  - "productive load" in the F-109 portfolio row;
  - the existing "door and loading" log wording.

  No new banned word was added. "complete sessions" and "A complete check" are plain lower-case words, not grade codes.
- Screen ledger: not touched, not run.
- Measurements: `node tools/measure-mock-panels.mjs --mock frontend/mockups/v70 …` on the seven screens, 14 measurements. Committed as `.agent/MA-1-mock-measurements.md`, with the PNGs and JSON in `.agent/MA-1-captures/`.
  - `docScrollW = clientW` on every screen at 1440 and 390, so there is no horizontal page scroll.
  - At 390, three wide tables scroll inside their own wrapper. They are v70's existing table-wrap behaviour, not M1–M6 content:
    - Portfolio "Where management should act first", 338/720;
    - the Opportunities lens table, 320/629;
    - Verification "Target and guardrails", 320/481.
- "Why?" interaction check: a scratch CDP script clicked one "Why?" per screen at 1440 and 390. Captures are `.agent/MA-1-captures/why-*.png`.
  - Button counts: portfolio 4, mini 4, cold 3, ev 3.
  - No button is inside a link.
  - The `<details>` open state is unchanged after the click, so the toggle is stopped.
  - At 1440 the popover sits within the viewport.
  - At 390 it is a bottom sheet (left 0, right 390, bottom 900 = viewport) with no horizontal scroll.
- No full suites, DB access or server were used.

## Known deviations and MOCK DEVIATION candidates

1. **"Lab session hours" is not drawn.** v70 has no lab Site (Q5). This is a MOCK DEVIATION candidate for CH-5b, where the product's cold lab uses session hours.
2. **Product today vs. mock:** the product's Kobo Grow has a declared 300 kWh-a-month target and the demo-data numbers. The mock shows "No target set yet" and v70 numbers (Q1, Q3). CH-6 cites the filled-Target format above.
3. **Portfolio Grow card:** per-Site shares only, with no estate total (Q4). The brief's "totals estimated income per Site over the same days" applies per Site; Kobo's and Depot's days differ in v70.
4. **Portfolio cards changed from `<a>` to `<div>`** with one full-card link (`.oc-cardlink::after`) and a sibling "Why?" button (Q6). The look is unchanged and the button has its own tab stop.
5. **Grow rows open by default** when they carry the three parts, so M3 is visible at 1440 and 390. Earlier, only "Needs attention" rows opened.
6. **Problem-history line is board-only.** It shows wherever a finding issue has a `HIST` entry, which includes the Kobo Protect row's F-104 safeguard line and both GreenHarvest rows. The global Findings list keeps v70's `RECUR` text unchanged.
7. **Undated future steps.** Later timeline steps read "Date not set in this example", per the Q7 ruling's literal wording, even though they are not reached yet.

## Residual risk

- The "Why?" popover's keyboard behaviour (focus moves into the dialog; Escape closes it) reuses the confidence-popover handlers. It was not exercised by keyboard in a browser.
- Only one "Why?" per screen was clicked; the other entries render from the same `WHY` map.

## User-review focus

- Are the three Grow parts readable, especially at 390?
- Does the "Why?" wording and bottom sheet work?
- Is the five-step fix timeline wording right?
- Are the M1 days lines clear in plain words ("checked", "partly checked", "too little data, not counted")?
