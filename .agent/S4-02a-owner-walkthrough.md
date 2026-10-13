# S4-02a owner walkthrough: the Site diesel price, its history, the disabled edit and a finding's money view

## What changed

- Sites now have a **Financials** tab with two sections:
  - **Overview**: what a finding means in money.
  - **Assumptions**: the site's diesel price.
- **Assumptions** shows the following:
  - The diesel price in use today, in plain words: "Diesel price, set by the system on 13 Oct 2026: 1.25 USD per litre, from 1 Jul 2026 until 1 Jan 2030."
  - Its basis, source and who set it.
  - A **Price schedule** that shows which price applies to which dates.
  - A **Price history** of every recorded version.
  - The exact record identifiers stay inside a closed "Record details" section.
- The prices are illustrative demonstration values published by the system, not market quotes:
  - Version 1 (first price): 1.25 from 1 Jan 2026.
  - Version 2 (scheduled change): 1.32 from 1 Jan 2030.
  - Version 3 (correction): 1.19 for June 2026 only.
- **Edit price** is visibly greyed out. Beside it: "Editing the price here is not available yet: a price change must be made by a signed-in operator, and operator sign-in is not built yet. Prices are published by the system." This wording is for you to accept or change.
- Every finding page has a new link, "What this finding means in money". It opens Financials for that exact finding version, which shows the following:
  - Cost: **Not calculated**.
  - The reason: no fuel quantity has been calculated for the finding yet.
  - No amount and no currency.
  - A link to that version's evidence.
- The Site model page keeps its line "Financial assumptions not available here...". It now adds "The site's diesel price is on Financials › Assumptions" as a link.
- Not shown, and deliberately left out:
  - the mock's Scenarios section and its Impact preview;
  - the maintenance line;
  - the cost cards;
  - cash flow, currency conversion and monthly totals.

## Start (four PowerShell windows)

These commands use private databases `assetops_s402awalk` (with prices) and `assetops_s402aempty` (same findings, no price), data ports 8870/8871 and web ports 5370/5371. Nothing else is touched. Docker Desktop's Postgres must be running, and the reviewed finding cases must exist (`tools\s4_finding_cases.py run` was run for S4-01).

1. Prepare. This copies the finding cases, upgrades the copy, publishes the three demonstration prices with the system publisher, and makes the empty-price copy:
   `cd C:\Users\assef\Bineyame\AssetOpsV1; C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe C:\Users\assef\Bineyame\AssetOpsV1\tools\s402a_assumptions_walkthrough.py --db assetops_s402awalk --empty-db assetops_s402aempty --work-name s402a-owner prepare`
2. Print your addresses (version links and finding links):
   `C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe C:\Users\assef\Bineyame\AssetOpsV1\tools\s402a_assumptions_walkthrough.py --db assetops_s402awalk --empty-db assetops_s402aempty --work-name s402a-owner links --web-port 5370 --empty-web-port 5371`
3. Serve the data (leave this window running):
   `cd C:\Users\assef\Bineyame\AssetOpsV1; C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe C:\Users\assef\Bineyame\AssetOpsV1\tools\s402a_assumptions_walkthrough.py --db assetops_s402awalk --empty-db assetops_s402aempty --work-name s402a-owner serve --port 8870 --empty-port 8871`
4. Start the web app (leave this window running):
   `cd C:\Users\assef\Bineyame\AssetOpsV1\frontend; $env:ASSETOPS_API_PORT="8870"; npm.cmd run dev -- --port 5370 --strictPort`
5. Start the empty-price web app (leave this window running):
   `cd C:\Users\assef\Bineyame\AssetOpsV1\frontend; $env:ASSETOPS_API_PORT="8871"; npm.cmd run dev -- --port 5371 --strictPort`

The measured checks at 1440 and 390 pixels have already been run: **69/69 claims passed**. The screenshots of the app and the mock are in `C:\Users\assef\AppData\Local\AssetOps\evidence\s402a`.

## What to look at

1. **Assumptions**, `http://localhost:5370/sites/KOBO-001/financials/assumptions`:
   - The first sentence names the price, who set it and when it applies.
   - Edit price is greyed out, with the reason beside it.
   - The Price schedule has four rows:
     - 1.25 (January to June);
     - 1.19 (June only, Correction);
     - 1.25 (July 2026 to 2030, marked "applies today");
     - 1.32 (from 2030).
   - Open "Record details" to see the identifiers. They are hidden until you open it.
2. **One exact version**: in Price history, click "Open version 3".
   - You see 1.19 and where it applied.
   - Reload the page: it is the same version.
   - Browser Back: you return to the current list.
3. **Prices as recorded earlier**: click "Prices as recorded then" under Version 1.
   - The schedule shows only version 1, as it was before the later changes.
   - "Show the current prices" returns to today's view.
4. **A finding's money view**: open a finding address from step 2 of Start, then click "What this finding means in money".
   - Cost reads "Not calculated", with the reason. There is no amount.
   - The address now holds the exact finding version, so a reload shows the same version.
   - "See the evidence for this finding version" opens that version's evidence. Back returns here.
5. **No price recorded**: open `http://localhost:5371/sites/KOBO-001/financials/assumptions`. It says "No diesel price is recorded for today at this site. No default or company-wide price is used in its place." The greyed-out edit and its reason are still there.
6. **Site model**: open `http://localhost:5370/sites/KOBO-001/foundation`. Under Identity, the financial-assumptions line now links to Financials › Assumptions.

## What to decide

- Is the disabled-edit wording acceptable?
- Is "Not calculated" with that reason the right reading for a finding's cost today?

## Stop and clean up

1. Press Ctrl+C in the serve window and in both web windows.
2. Remove the private databases and the work folder:
   `C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe C:\Users\assef\Bineyame\AssetOpsV1\tools\s402a_assumptions_walkthrough.py --db assetops_s402awalk --empty-db assetops_s402aempty --work-name s402a-owner drop`
