# G-02 owner walkthrough: missing states on Sites, Site model, Readiness and the single line diagram

## What changed

- Every honest "not available" statement on these four pages that asserts an absent capability is now linked to its own entry in the gap catalogue. The entry names the claim, why it is missing, who owns it and what would close it.
  - The link sits in the page's HTML as `data-gap-id`. You never see it on screen.
  - No value is invented anywhere.
- One visible change, on Readiness > **Gateway status**. The old combined line ("Not available yet: uptime trend, expected-versus-delivered completeness and signal strength...") is now three lines, one per missing fact, matching the firmware line you accepted in G-01:
  - "Uptime trend not available yet: no reviewed source reports a gateway's uptime over time."
  - "Expected-versus-delivered completeness not available yet: no reviewed source compares the reports a gateway should send with those received."
  - "Signal strength not available yet: no reviewed source reports a gateway's signal strength."
  - "Firmware not available yet: no reviewed source reports what firmware a gateway runs." (unchanged)
- All other wording is unchanged.
- The automatic checks now also catch new untagged "not tracked yet" and "commissioning confirmation not recorded" copy.

## Start (four PowerShell windows)

These commands use private databases `assetops_g02walk` and `assetops_g02empty`, data ports 8868/8869 and web ports 5368/5369. Nothing else is touched. Docker Desktop's Postgres must be running.

1. Prepare:
   `cd C:\Users\assef\Bineyame\AssetOpsV1; C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe C:\Users\assef\Bineyame\AssetOpsV1\tools\v01a_foundation_walkthrough.py --db assetops_g02walk --empty-db assetops_g02empty --work-name g02-owner prepare`
2. Serve the data (leave this window running):
   `cd C:\Users\assef\Bineyame\AssetOpsV1; C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe C:\Users\assef\Bineyame\AssetOpsV1\tools\v01a_foundation_walkthrough.py --db assetops_g02walk --empty-db assetops_g02empty --work-name g02-owner serve --port 8868 --web-port 5368 --empty-port 8869 --empty-web-port 5369`
3. Start the web app (leave this window running):
   `cd C:\Users\assef\Bineyame\AssetOpsV1\frontend; $env:ASSETOPS_API_PORT="8868"; npm.cmd run dev -- --port 5368 --strictPort`
4. Optional, empty store:
   `cd C:\Users\assef\Bineyame\AssetOpsV1\frontend; $env:ASSETOPS_API_PORT="8869"; npm.cmd run dev -- --port 5369 --strictPort`

The measured checks at 1440 and 390 pixels have already been run: 322/322 claims passed. Screenshots of the app and the mock are in `C:\Users\assef\AppData\Local\AssetOps\evidence\g02`.

## What to look at

1. **Sites**, `http://localhost:5368/sites`:
   - The Operating view cell says "Not available yet".
   - Below the table are two notes: the analysis note, and "1 registered Site listed. Needs attention and Evidence limited counts ... Setup progress not tracked yet."
   - The empty store at `http://localhost:5369/sites` shows "No sites configured" and no missing-state lines.
2. **Site model**, `http://localhost:5368/sites/KOBO-001/foundation`:
   - Under Identity & operating obligations: "Productive-use designation: Not declared" and "Financial assumptions not available here...".
   - In the controls table: "No proposed-change record here" and "No linked constraint evidence".
3. **Readiness**, `http://localhost:5368/sites/KOBO-001/foundation/readiness`:
   - In the table, Confirmed shows "Not recorded" on every row, and Commissioning says no record exists.
   - In **Gateway status**, the four lines above appear one under another, plus "Device connection not established here."
   - Choose another period or a part. The same lines stay.
   - Reload the page. Nothing changes.
4. **Single line diagram**, `http://localhost:5368/sites/KOBO-001/foundation/sld`:
   - Beside the drawing: "Protection and meter positions are not declared ...; monitoring links and reporting status are not assessed on this diagram. See Site Evidence ..."
   - Above it: "Configured, not live · Readings are not assessed in this view."
   - The drawing has no fake breakers, meters or status dots.
5. Narrow the window to about 390 px. The lines wrap inside their panels. Wide tables scroll inside their own box, and the page does not scroll sideways.
6. Optional: right-click any of these lines and choose Inspect to see its `data-gap-id`.

## Stop and clean up

1. Press Ctrl+C in the web-app windows (steps 3 and 4), then in the data window (step 2).
2. Drop the private databases and work folder:
   `cd C:\Users\assef\Bineyame\AssetOpsV1; C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe C:\Users\assef\Bineyame\AssetOpsV1\tools\v01a_foundation_walkthrough.py --db assetops_g02walk --empty-db assetops_g02empty --work-name g02-owner drop`

## Your decision

Is each visible missing-state treatment acceptable, especially the three separate gateway lines? Acceptance stays conditional on these named gaps: layout and copy only. Nothing becomes Real, and no panel or screen status changes. Open product questions for the Architect, with defaults already shipped, are in `.agent/G-02-questions-1.md`. Q3 asks whether obligations/policy and the confidence effect should get a visible "not available yet" line.
