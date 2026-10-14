# S4-02b owner walkthrough: what a finding's generator time could cost in fuel, and how that changes with the price

## What changed

- **Financials › Overview** now shows, for one exact finding version, its **modelled potential fuel-cost exposure**: a range from zero up to an upper amount, for example "0.00 to 15.82 USD".
  - The default sentence (for you to accept or change): "Modelled potential fuel-cost exposure: 0.00 to 15.82 USD, under the reviewed fuel-cost-1 assumptions. This is not measured fuel saved or a physical maximum."
  - It is never a single "saving" figure. Zero is always the lower end.
- A short table, **From finding to money**, shows the steps: the finding's time, the diesel (0 to 12.65 litres), the diesel price used (1.25 USD per litre, linked to that exact price version) and the resulting range.
- **How this is worked out** (closed until you open it) holds the model name, the 1.10 allowance on fuel use, every counted generator reading, the record identifiers and digests.
- **Fuel cost versions** lists every version of the money figure for that finding version. A later price correction adds a version; the earlier one stays, labelled "kept for the record". The finding version and the fuel amount stay the same.
- When no amount can be shown, the page says why, in plain words, and shows no number:
  - **Not calculated**: the generator power readings cover too little of the finding's time (gaps are never filled in), or there are no power readings.
  - **No price for the whole window**: no diesel price is recorded, or the price changes part-way through.
  - **Not worked out yet**: the money figure has not been calculated yet.
  - **Out of date: no current cost**: the price changed and the figure has not been recalculated yet.
  - **Earlier finding version: kept for the record**.
  - **For the record only**: the finding's source is not open for current use.
- The one finding with an amount is the **authored demonstration case** you approved on 14 Oct (P01-power, 23 Oct 2026). It is labelled on the page: "Demonstration data. This finding comes from demonstration readings written by the AssetOps team to show a complete fuel-cost calculation. They are not measurements from a working generator." The ordinary gateway finding (F01-gateway, 2 Oct) is shown beside it as the honest "not calculated" example.
- Of the 11 ordinary findings, **none qualifies** for an amount: 8 have no generator power readings, 2 are not supported findings, and F01-gateway's readings cover only a third of its time.
- Assumptions: "Show later versions" now adds the next versions below the ones already shown instead of replacing them (S4-02a review note).
- Not shown, and deliberately left out: the mock's trade-offs panel, impact preview, maintenance line, extra cost cards, Scenarios, cash flow, currency conversion and monthly totals.

## Start (five PowerShell windows)

These use private databases `assetops_s402bwalk` (prices, gate open, money calculated) and `assetops_s402bempty` (same findings, no price, not yet calculated), data ports 8872/8873 and web ports 5372/5373. They are already prepared; step 1 is only needed to start again from scratch.

1. (Only to start again) Prepare. Needs the demonstration template from `tools\s402b_power_cases.py run` (about 2.5 minutes, already done):
   `cd C:\Users\assef\Bineyame\AssetOpsV1; .\.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py --db assetops_s402bwalk --empty-db assetops_s402bempty --work-name s402b-owner prepare`
2. Print your addresses:
   `.\.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py --db assetops_s402bwalk --empty-db assetops_s402bempty --work-name s402b-owner links`
3. Serve the data (leave running):
   `.\.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py --db assetops_s402bwalk --empty-db assetops_s402bempty --work-name s402b-owner serve`
4. Web app (leave running): `cd C:\Users\assef\Bineyame\AssetOpsV1\frontend; $env:ASSETOPS_API_PORT="8872"; npm.cmd run dev -- --port 5372 --strictPort`
5. Empty-price web app (leave running): `cd C:\Users\assef\Bineyame\AssetOpsV1\frontend; $env:ASSETOPS_API_PORT="8873"; npm.cmd run dev -- --port 5373 --strictPort`

The measured checks at 1440 and 390 pixels were run on separate copies: **90/90 claims passed**. Screenshots of the app and the mock are in `C:\Users\assef\AppData\Local\AssetOps\s402b-evidence\shots`.

## What to look at

1. **The demonstration finding's money view**: `http://localhost:5372/sites/KOBO-001/financials?finding_id=b524cc00-3bff-40a0-b9d1-1e97ce20f8c2&revision_id=ff0a2276-d1f8-478a-bf76-fb4bb170f689`
   - The blue "Demonstration data" note.
   - "0.00 to 15.82 USD" and the sentence under it.
   - The four-row "From finding to money" table. Click "The site price version used": it opens price version 1 on Assumptions.
   - Open "How this is worked out": 23 readings of 20 kW, 5 minutes each, 0.3 litres per kWh, allowance 1.10.
   - "See the evidence for this finding version" and back: the same version comes back. Reload: it stays.
2. **The ordinary gateway finding**: `http://localhost:5372/sites/KOBO-001/financials?finding_id=edf43435-d5c9-4fec-87d4-168c3d8d4560&revision_id=28ff5283-4b1d-4dd0-b859-6f291d24cae4`
   - "Not calculated", with the reason: the readings cover too little of the finding's time. No number anywhere.
3. **An earlier finding version**: `http://localhost:5372/sites/KOBO-001/financials?finding_id=56400f93-edef-4ee1-b99e-36129bf7f87d&revision_id=24ddcfa6-4e6a-499f-86fb-7286dca8df9e` reads "Earlier finding version: kept for the record".
4. **No money calculated yet** (empty-price app): `http://localhost:5373/sites/KOBO-001/financials?finding_id=b524cc00-3bff-40a0-b9d1-1e97ce20f8c2&revision_id=ff0a2276-d1f8-478a-bf76-fb4bb170f689` reads "Not worked out yet". Then, in a sixth window, run
   `.\.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py --db assetops_s402bwalk --empty-db assetops_s402bempty --work-name s402b-owner recompute --empty`
   and reload: "No price for the whole window", because that copy has no price.
5. **A price correction** (October price 1.28 instead of 1.25):
   `.\.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py --db assetops_s402bwalk --empty-db assetops_s402bempty --work-name s402b-owner publish-v4`
   - Reload view 1: "Out of date: no current cost" and no amount in the money panel, only a line saying earlier versions are listed under "Fuel cost versions". (The older figure is still visible there, labelled "kept for the record", and the price in use shows 1.28 USD per litre.)
   - Then run `... recompute` (same command as above without `--empty`) and reload: **0.00 to 16.20 USD** at 1.28 USD per litre.
   - Under "Fuel cost versions": version 1 (15.82, kept for the record) and version 2 (16.20, the current fuel cost). Click "Open fuel cost version 1": it says the fuel amount is the same and only the price differs. Back and forward keep each version; reload keeps it.
   - Assumptions now lists four price versions.
6. **Source not open** (optional): run `... close-gate`, reload view 1: the note "Audit material only", then "For the record only: no current cost", and **no fuel-cost amount anywhere on the page**: the money panel says "No amount is shown while the source is closed", the Fuel cost versions list shows no amounts, and an opened earlier version says the source is closed with no figures. (The diesel price per litre in "Price in use" is a price, not a fuel cost, and stays.) Run `... open-gate` to undo.
7. At 390 px (phone width) the same pages stack; the tables wrap inside the panel without sideways page scrolling.

## Not walked, and limits of the demonstration label

- **"The price changes part-way through this finding's time" (PRICE_SPANS_WINDOW) is tested, not walked.** It is covered by a Postgres test and a screen test; this walkthrough does not stage it, so you will not see that wording on screen.
- **The "Demonstration data" label is decided by Site and day, not by who wrote the data.** It applies to any finding at KOBO-001 on 23 Oct 2026 (UTC), in any database, and it is not tenant-scoped. If live data lands on that day it would carry the label wrongly (an under-claim, never the reverse). If the label's source file cannot be read, findings show a cautious "Source not confirmed" note instead. Recording authorship at ingestion is an open Architect item.

## What to decide (S4-02 checkpoint)

1. Is the default money sentence acceptable as final product copy? ("Modelled potential fuel-cost exposure: 0 to [amount], under the reviewed fuel-cost-1 assumptions. This is not measured fuel saved or a physical maximum.")
2. Are the plain reasons for "Not calculated" and the other no-amount states clear enough?
3. Is the "Demonstration data" note clear, and is it acceptable that the only positive amount comes from that authored case while 0 of 11 ordinary findings qualify (reasons above)?
4. Should "Out of date" and "Not worked out yet" stay separate, or read as one "being updated" state? (They are separate now.)
5. Carried from S4-02a: version 1 shown as "with no end date" in Price history next to shorter Price schedule pieces. Still unchanged; keep as a later Financials usability item?
6. Carried: the six Site tabs wrap to a second line at 390 px; still accepted for now?
7. Fuel cost versions keep an older or out-of-date figure visible, labelled "kept for the record", while the money panel above says there is no current cost. Is that clear, or should older figures be hidden until you open that version? (Re-review I2: the pointer line says "Earlier fuel cost versions"; "Recorded fuel cost versions" may read more exactly.)
8. When the finding is shown for the record only (its source readings not yet confirmed by the comparison), no fuel cost appears, but the Site's diesel price for today ("Price in use ... USD per litre") still shows. Keep it, or hide it in that state too?

## Clean-up

Stop the windows with Ctrl+C, then:
`.\.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py --db assetops_s402bwalk --empty-db assetops_s402bempty --work-name s402b-owner drop`
