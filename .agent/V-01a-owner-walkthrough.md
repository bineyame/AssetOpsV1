# V-01a owner walkthrough: Sites and Foundation next to the v6.9 mock

This check covers four screens: the Sites list, the Foundation Site model, the single line diagram and Readiness. For each one, put the app next to its mock screen and decide whether the differences are acceptable. The data is a private copy, so nothing you do here touches your own servers or `var/`.

## Start (four terminals, from the repository root)

1. `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py prepare` copies the Kobo database into `assetops_v01awalk` and creates an empty `assetops_v01aempty`. This needs the S4 fixture producer output; if it is missing, run `tools/s4_finding_cases.py run` first.
2. `.venv/Scripts/python.exe tools/v01a_foundation_walkthrough.py serve` starts the two data services, on 8860 and 8861.
3. From `frontend/`: `$env:ASSETOPS_API_PORT="8860"; npm.cmd run dev -- --port 5360 --strictPort`
4. From `frontend/`: `$env:ASSETOPS_API_PORT="8861"; npm.cmd run dev -- --port 5361 --strictPort`

`tools/v01a_foundation_walkthrough.py links` prints every address. To repeat the measured checks, run `node tools/v01a-foundation-evidence.mjs http://localhost:5360 <folder> http://localhost:5361`. It should print 62/62. Press Ctrl+C in each terminal to stop.

The mock pages are at `http://localhost:5360/mockups/v69/index.html#/sites`, `#/foundation`, `#/readiness` and `#/sld`.

## What to look at

1. **Sites** (`http://localhost:5360/sites`): one real Site appears under "Site inventory", with a one-line note that Mode means provenance. The mock's three summary tiles, filter chips, "In setup" panel and setup tabs are not built. Setup is later work (W6), and the counts have no source.
   Then open `http://localhost:5361/sites`. It shows "No sites configured" with no example rows.
2. **Site model, in effect now** (`/sites/KOBO-001/foundation`, no `?at=`; this is where a user lands): the selector reads "In effect now" and the strip says this is the configuration in effect now (today v10). Then "Configured topology" (cards on a bus labelled "AC bus · 400 V"), "Identity & operating obligations" and "Time-valid control configuration". For comparison, the scheduled period (`?at=2026-10-22T00:00:00Z`, v13, starts 21 Oct 2026) says it is a scheduled period and not in effect yet.
   The period selector now names the instant from the address ("At ... (from the address)"). Before this change it wrongly showed "In effect now".
   The mock's "Evidence / change" column and its policy links have no source in the app, so they are left out.
3. **Missing period** (`...foundation?at=2026-09-01T00:00:00Z`): the screen says "No stored version for this period". It does not fall back to the configuration in effect now.
4. **Single line diagram** (`/sites/KOBO-001/foundation/sld` for in effect now; `?at=2026-10-22T00:00:00Z` for the scheduled v13 period): the configured drawing, then "What each configured part is", which lists each part's bound channels. The AC bus has no channel, and the screen says so.
   - Reload the page: the period and every part's channels stay the same.
   - Switch the period to the imported one (29 Sep). (The links tool prints these addresses; the instants lie inside each period, and v13 is scheduled until 21 Oct 2026.) Some parts show fewer channels, because the two capability channels were added on 2 Oct.
   - Open "Diagram detail", then "Devices…". The caption now says only that whether any device is reporting is not assessed here. Before, it said both "none has reported" and "nothing states whether any is reporting".
   - The mock's green and amber reporting dots are not shown. Reporting is Evidence, not configuration.
5. **Readiness** (`.../foundation/readiness`, in effect now; add `?at=2026-10-22T00:00:00Z` for the scheduled period): "Configuration readiness" now opens with "Configuration readiness is distinct from claim readiness and from operational status, which are not assessed here."
   Below it come role coverage, signal bindings and the registered gateway (registration only).
   The mock's gateway status (Online, 100%, 95%), connected-source health and commissioning columns are not built. They need real contact and commissioning evidence.
6. **Keyboard**: press Tab to reach the "Site model" subtab, then press Enter. The view changes and the selected period stays the same. Tab moves on to "Single line diagram".

## Decisions for you (defaults already applied; see `.agent/V-01a-questions-1.md`)

- Keep the app's grid drawing of the single line diagram, rather than redraw it as the mock's bus-bar style (Q1).
- Keep the view name as the page heading ("Foundation"), rather than the Site name (Q2).
- Keep configuration readiness in neutral colours, rather than the mock's green and amber (Q3).
- Read "bound component stays stable" as each part's bound channels staying stable; no clickable-part selection is added (Q4).
- Keep the topology cards text-only, without icons (Q5).

If these look right, record V-01a visual acceptance for `sites:1`, `foundation:1-3`, `readiness:1` and `sld:1-2`. This is visual acceptance only. It does not close any technical node.
