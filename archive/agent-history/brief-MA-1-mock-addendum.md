# Brief MA-1: v70 mock addendum for the chain screens (OD-P5, agreed)

- Architect: Claude, 2026-11-03.
- Plan: `Docs/demo-sprint/client-demo-plan.html` §2.1 MA-1. About 1 unit, off-lane.
- **Needed before the CH-5b and CH-6 UI units start.** The owner approves it in one quick look.
- The mock stays the layout spec. This addendum adds only what the chain design introduces. Everything else in v70 is unchanged.

## Where and how

- Edit `frontend/mockups/v70/` in place: `screens.js` (screen bodies, data constants), `outcomes.js`/`outcomes.css` (outcome rows) and `portfolio.js`/`portfolio.css`. Use a branch `task/MA-1-mock-addendum`.
- **Reuse the existing patterns; do not invent a new visual family.**
  - The confidence chip and popover: `screens.js:132-134` `conf()` / `confPop()`, the "Why · what raises it" dialog. This is the base for the **"Why?" trace**.
  - The recurrence note: `recurNote()`, used at `screens.js:181`. This is the base for the **thread occurrence line**.
  - Badges, `panel()`, `pair()` and `table()` stay as they are.
- **Data.** Keep v70's own illustrative data: Kobo F-104/F-109, ACT-048; GreenHarvest F-118, WR-019; Depot F-130, ACT-061 (`screens.js:107-129`, `:188-190`). Do not paste demo-build numbers into the mock.
- **Copy.** Plain-language client copy, with no system vocabulary. Do not use these words in visible text: thread, snapshot, revision, grade code names (`COMPLETE`/`PARTIAL`), lifecycle state codes, or "load" (banned product term; WALK1-G2 D2). Run the vocabulary guard (`tools/checks/test_mock_deviation_labels.mjs`, `check-all.ps1:66`).
- **Widths.** Every addition must fit at 1440 and 390 px with no horizontal scroll.
- **Measurements.** After editing, run `node tools/measure-mock-panels.mjs --mock frontend/mockups/v70 <out> portfolio mini cold ev findings-opportunities finding-history verification`. Commit the measurements as `.agent/MA-1-mock-measurements.md` (ROLE_CONFIG: mock measurements before the spec).

## What to add (six items)

| # | Item | Screens (mock ids) | Content | Slice that builds it |
|---|---|---|---|---|
| M1 | **Day coverage line**, a measure tile footer | `portfolio`, `mini`, `cold`, `ev` | A short line under each outcome value giving the days behind it. Examples: "5 of 7 days checked · 2 partly checked" and "No readings on 21 Oct". Partly checked days are counted and labelled; days with very little data are shown but not totalled (AG-4, AG-5). For a lab Site: "Lab session hours". | CH-1a data; CH-5b block |
| M2 | **"Why?" trace** popover | `portfolio` (each of the four outcome cards), `mini`/`cold`/`ev` (each outcome row) | A button "Why?" next to the value. It opens the same dialog family as `confPop`. Content, top to bottom: the value in one sentence; "Comes from": 2–4 lines (for example "Grain-mill electricity on 3 checked days × declared price 0.25 per kWh"); "Days used" (the M1 line); "What would change it" (one line); and a link to the evidence screen. At 390 px it is a bottom sheet. | CH-5b |
| M3 | **Grow row in three parts** | `mini` (Grow row), `ev` (Grow row), `portfolio` (Grow card) | Three labelled parts, never merged: **Target** (the KPI verdict, for example "300 kWh a month · too early to judge, 2 of 3 checked days"), **Potential** (for example "25–31 kW of daytime solar unused"), and **Estimated income** (for example "42.08 at the declared price · not billed or collected"). Each part has its own M1 line. The Portfolio Grow card totals estimated income per Site over the same days and names each Site's share. | CH-6 |
| M4 | **Problem history** on a Finding and on the board | `finding-history`, `mini` (Optimize row issue), `cold` | One line from the `recurNote` family, for example "3rd time since 17 Oct · same generator". On `finding-history`, add a compact timeline: Seen → Action agreed → Change made → Checked and working, monitoring → (Closed after 7 clean days). The current step is highlighted, with each step's date. The same timeline goes on the `verification` screen header. | CH-2 data; CH-3 states; CH-5b block |
| M5 | **Opportunities list and strip** | `findings-opportunities`, `portfolio` (opportunity strip) | The productive-use headroom item as a list row ("Daytime solar unused at Kobo · seen on 2 of 3 well-observed days"). The Portfolio strip names it ("1 opportunity: Kobo daytime solar"). An opportunity with limited evidence says so in words, not as "Not established". | CH-4 |
| M6 | **Action visible everywhere** | `cold`, `ev`, `portfolio` rows | The "Already in hand" item on the cold and EV boards (for example "ACT-051 · Witness automatic-start test · open"). The Portfolio row shows the Action instead of "No action agreed yet" (I-03, I-09). | CH-2; CH-5a |

## Acceptance

- Each of M1–M6 is visible on the named mock screens at 1440 and 390 px.
- The vocabulary guard passes, and the mock measurements are committed.
- The packet lists every new panel heading, with the copy literal for each, because the build specs cite them. It also lists any intended difference from today's product as a future MOCK DEVIATION candidate.
- The owner approves.

**Not in scope:** the detail pages (CH-10a/b, after the demo), integrations, and any change to v70 screens outside M1–M6.
