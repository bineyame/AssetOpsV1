# V-01a owner walkthrough: Sites and Foundation next to the v6.9 mock (round 2)

This round applies your answers. It covers four screens: the Sites list, the Foundation Site model, the single line diagram and Readiness. For each one, put the app next to its mock screen and decide whether the differences are acceptable. The data is a private copy, so nothing here touches your own servers or `var/`.

## Start (four terminals, from the repository root)

1. `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py prepare` copies the Kobo database into `assetops_v01awalk` and creates an empty `assetops_v01aempty`. If the S4 fixture output is missing, run `tools/s4_finding_cases.py run` first.
2. `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py serve` starts the two data services, on 8860 and 8861.
3. From `frontend/`: `$env:ASSETOPS_API_PORT="8860"; npm.cmd run dev -- --port 5360 --strictPort`
4. From `frontend/`: `$env:ASSETOPS_API_PORT="8861"; npm.cmd run dev -- --port 5361 --strictPort`

`tools/v01a_foundation_walkthrough.py links` prints every address. To repeat the measured checks, run `node tools/v01a-foundation-evidence.mjs http://localhost:5360 <folder> http://localhost:5361`. It should print 105/105. Press Ctrl+C in each terminal to stop.

The mock pages are at `http://localhost:5360/mockups/v69/index.html#/sites`, `#/foundation`, `#/readiness` and `#/sld`.

## What to look at

1. **Sites: compare only Directory → "Site inventory"** (`http://localhost:5360/sites`).
   - Each row now shows the Site (its name, with its code and location underneath), Type, and Mode, as in the mock.
   - Lifecycle, configuration origin and template are under "Setup details" in the row.
   - The mock's Assessment, Top issue, Evidence and Last analysed columns are not shown. A note under the table says why: the directory has no source for them yet. The all-dash "Last analysed" column is gone.
   - For the empty state, open `http://localhost:5361/sites`. It shows "No sites configured".
2. **Look and feel, on every screen.**
   - The tab and subtab headers are grey, as in the mock. Only the tab you are on is blue and underlined.
   - Titles, panel headings, notes and table text use the mock's sizes and colours.
   - The left menu matches the mock's colours and spacing, and each item has its icon. Only the screens that exist are listed: Sites and Findings, and in the Lab, Simulator Lab, Site Templates, Scenarios and Runs.
3. **Site model** (`/sites/KOBO-001/foundation`). With no date in the address, this is the setup in effect now.
   - Each topology card shows an icon for each part, so you can tell solar, battery, converter, generator, fuel tank and load apart at a glance. The icon is named by the part's type.
   - Click a part name to choose it. A "Selected part" panel lists that part's channels.
4. **Single line diagram** (`.../foundation/sld`). The drawing now uses the mock's style:
   - supplies on the left, one vertical AC bus bar, and loads on the right;
   - an icon for each part;
   - the label "Configured, not live".

   It draws only the parts and connections stored for this Site. The mock's breakers, kWh meter, monitoring row, coloured status dots and "400/230 V" are not drawn, because this Site does not declare them. The AC bus shows its stored 400 V rating. Under each part, "Readings not assessed here" means this view does not look at readings. It does not mean nothing has arrived.
   - Click a part in the drawing, or Tab to it and press Enter, to choose it. The address gains `component=...`. The choice stays when you reload and when you switch between Site model, Single line diagram and Readiness. Clicking the part again, or "Clear selected part", removes it.
   - To see the missing state, use the "part this period does not declare" link. The choice is cleared and the screen says "Selected part is not in this Foundation period". Every stored Kobo period has the same ten parts, so this case comes from an address, not from a real period change.
5. **Readiness** (`.../foundation/readiness`). Green means the required setup is complete for the period shown. Amber means something required is not set up. Grey means it cannot be told. A legend says what the colours mean. The green badge has a tick, so it is not confused with the green "Demonstration data" Mode badge on the Site model. Neither colour says anything about the site's health, contact or evidence.
6. **Periods.** The scheduled period v13 (`?at=2026-10-22T00:00:00Z`, from 21 Oct 2026) says it is not in effect yet. The date 1 Sep 2026 says "No stored version for this period".
7. **Narrow screens (390 px).** The menu moves above the page and keeps its icons. The drawing scrolls sideways inside its own box. The chosen part's panel stays readable without scrolling.

## What to decide

- Do these four screens, at both widths and including the selection and missing states, now look acceptable next to the mock? If so, record V-01a visual acceptance for `sites:1`, `foundation:1-3`, `readiness:1` and `sld:1-2`. This is visual acceptance only. It does not close any technical item.
