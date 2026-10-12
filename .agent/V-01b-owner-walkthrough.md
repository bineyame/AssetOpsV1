# V-01b owner walkthrough: Lab and Site Evidence next to the v6.9 mock

This task makes three screens look like the mock: the Lab run page ("Gateway & Ingestion"), Site Evidence (Overview) and Evidence Analysis. Put each app screen next to its mock screen and decide whether it now looks right.

As on V-01a, a mock panel that shows facts this product does not have yet now says so on the screen ("Not available yet: ..."). If you accept such a panel, the acceptance is for the layout and wording only, conditional on the named gap. A later task has to supply the data and be checked again.

The data is a private copy, so nothing here touches your own servers or `var/`.

## Start (four terminals, from the repository root)

1. If the S4 fixture output is missing, first run `.venv/Scripts/python.exe tools/s4_finding_cases.py run`.
2. `.venv/Scripts/python.exe tools/v01b_lab_evidence_walkthrough.py prepare` copies the Kobo database into `assetops_v01bwalk` (with the Lab run and a copy of its gateway ledger that never sends anything) and creates an empty `assetops_v01bempty`.
3. `.venv/Scripts/python.exe tools/v01b_lab_evidence_walkthrough.py serve` starts the two data services on 8862 and 8863.
4. From `frontend/`: `$env:ASSETOPS_API_PORT="8862"; npm.cmd run dev -- --port 5362 --strictPort`
5. From `frontend/`: `$env:ASSETOPS_API_PORT="8863"; npm.cmd run dev -- --port 5363 --strictPort`

`tools/v01b_lab_evidence_walkthrough.py links` prints every address. To repeat the measured checks: `node tools/v01b-lab-evidence-evidence.mjs http://localhost:5362 <folder> http://localhost:5363` (it should print 101/101). Ctrl+C stops each terminal.

The mock pages are `http://localhost:5362/mockups/v69/index.html#/lab`, `#/evidence` and `#/evidence-analysis`.

## Which screen goes with which

| Mock | App |
| --- | --- |
| `#/lab` (Kobo · Gateway & Ingestion) | Lab › Runs › the registered run (`/simulator-lab/runs/run-2348…`) |
| `#/evidence` (Overview) | `/sites/KOBO-001/evidence?from=2026-10-02T00:00:00Z&to=2026-10-03T00:00:00Z` |
| `#/evidence-analysis` | the same address with `view=analysis` (or the "Analysis →" link) |

## What to look at

1. **Lab run.** The page heading still says "Draft run"; the first section is **Gateway & Ingestion**. Under it: a status line (commit badge, execution status, "B of M batches have a central receipt", frozen versions, "Open Site Evidence →"); a four-box flow (private world → device reports → envelopes → accepted); then two rows of panels: **Selected canonical envelope** beside **Truth versus observed**, and **Release and ingestion** (with the Commit control under it) beside **What never crosses**. The old developer controls follow under "Execution and recorded history", and seven technical sections are closed under "Advanced details — …". Please look at the second flow box: it reads "321 reports published, 1 dropped / 329 admitted by the gateway". The two numbers come from two different records and the page does not explain the difference.
2. **Evidence Overview.** A status line ("N readings accepted · K of M sources with accepted readings · X not accepted", a grey "No capability conclusion yet" badge, "Analysis →"); **What we can conclude now**; then **Data sources** beside **Most useful next evidence** on a wide screen (stacked on a phone). The window chooser and its "Show this period" button sit at the top; the window is kept in the address, so reload and Back keep it.
3. **Evidence Analysis.** **Accepted records behind the conclusions** (Source · reading, Value, Taken, Sent, Received, "Open record"), then **How each limit is set**. "Open record" opens the record and ends with "Exact message as received", the stored message the value came from.
4. **Readings not accepted** shows a count line; the table is under "Advanced details — readings not accepted". When a reading was refused because it conflicts with an earlier one, a new column shows "Original reading taken <time>" with a link to it. This copy has no refused reading, so you will not see that column here; tests prove it.
5. **States to try.** Populated day 2026-10-02 (above). Nothing received: the same addresses with `from=2026-09-01T00:00:00Z&to=2026-09-02T00:00:00Z`. Empty store: `http://localhost:5363/sites/KOBO-001/evidence` says "No such site", and `http://localhost:5363/simulator-lab/runs` has no runs. Open any "Advanced details — …" section and close it again.
6. **Phone width (390 px).** Panels stack, tables scroll in their own boxes, and the Lab rail now folds into a top bar (before this task the Lab page left the content about 95 px wide on a phone).

## What you will see that is missing

| Screen | Exact words on screen | What would fill it |
| --- | --- | --- |
| Evidence Overview | "Not available yet: capability-by-capability conclusions (what can be said, what is missing and the next step for each). They need a reviewed capability assessment over accepted Evidence, which does not exist yet." | A reviewed capability assessment (later work). |
| Evidence Overview | "Not available yet: a status at the end of the period, a quality grade and which conclusions each source affects. No reviewed rule sets these." | A reviewed source-health rule. |
| Evidence Overview | "Not available yet: ranking the next evidence needs a reviewed rule linking missing readings to conclusions." | A next-evidence rule. The facts list of silent sources is shown instead. |
| Evidence Analysis | "Not available yet: the rule that turns accepted readings into a positive capability conclusion and sets its limit (a later capability assessment)." | The capability assessment (S3-02 owns the positive part). |
| Lab run | "Not available yet: the product consequence of each report (accepted, latency retained or indeterminate). These reads give central decisions per batch, not per device report." | A per-report decision read. |
| Lab run | "Not available yet: a link from this run's accepted records to the Dispatch analysis that used them. No run-to-analysis read exists here." | A run-to-analysis read. |

The mock's "Evidence limited" badge and "Portfolio evidence →" link are not shown: the first is a capability judgement the product cannot make yet, the second has no page yet.

## What to decide

- For each screen, at both widths: does it look acceptable next to the mock? A panel with a row above would be recorded as **"Owner visual acceptance conditional on these named data gaps; layout/copy accepted only."**
- Q2: keep the page headings "Draft run" and "Evidence" (as you kept "Foundation" on V-01a), or use the mock's "Gateway & Ingestion" / Site name?
- Q4: the mock says "How a claim limit is set"; the app says "How each limit is set" because the word "claim" is banned on product screens. Keep it?
- If something looks wrong, say which screen and what, in your own words.
