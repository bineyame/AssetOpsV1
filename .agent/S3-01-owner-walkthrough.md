# S3-01 owner walkthrough: Performance > Dispatch

What this shows: for one chosen day, whether Kobo's generator was needed, possibly avoidable, or cannot be determined, and which accepted records each answer rests on. It runs on a private copy of the reviewed dispatch-case data. Your own servers and databases are not touched.

## Before you start

- Local Postgres is running on port 55432 (the same one used by the earlier S2 demo).
- The database `assetops_s3cases` exists and its manifest is at `%LOCALAPPDATA%\AssetOps\s3-dispatch-cases\s3-dispatch-cases-v1.json` (made by `tools\s3_dispatch_cases.py`).
- `var\sites\kobo-001.yaml` exists in the repository.

`prepare` stops with a "Missing prerequisite" or "FAILED" message if one is missing or the check against the earlier results does not pass; in that case do not start `serve`. It prints "Prepared" only when everything worked.

## Start (about two minutes)

From the repository root, in PowerShell:

1. `.venv\Scripts\python.exe tools\s3_dispatch_walkthrough.py prepare`
   This copies the data into a private database (`assetops_s3walk`) and a private code folder, runs the check against the earlier file-based results, and sets up two problem days (described below).
2. `.venv\Scripts\python.exe tools\s3_dispatch_walkthrough.py serve`
   Starts the API on port 8820. Leave it running.
3. In a second window: `cd frontend`, then `$env:ASSETOPS_API_PORT="8820"; npm.cmd run dev -- --port 5320 --strictPort`

Open the links below. Ctrl+C in each window stops everything.

## What to look at

Each link opens Performance > Dispatch for one UTC day.

1. **A day with both outcomes (2 Oct):** http://localhost:5320/sites/KOBO-001/performance/dispatch?day=2026-10-02
   - The four totals: 1 h 30 min Needed and 4 h Possibly avoidable. "Possibly avoidable" counts only the qualifying 15-minute blocks, never the whole period.
   - Select the period, then any coloured block. The Selected period panel explains that block. The table below lists the accepted records behind it.
   - Open a record's ID to see where it came from: the gateway, the source, its series and number, the batch and the message.
   - Reload the page. The same period, block and records come back, because their IDs are in the address.
2. **Needed (9 Oct):** `...?day=2026-10-09`
   - The battery was at its reserve level.
   - The day names one limit: the generator had not been seen switching off by the end of the records, so the period is open-ended. That is why the total reads "at least".
3. **Cannot determine (1 Oct):** `...?day=2026-10-01`
   - Available solar power and the battery output limit were not yet reported, so the result cannot say "possibly avoidable".
   - "What limits this day's result" says this in plain words.
4. **Out of date (5 Oct):** `...?day=2026-10-05`
   - The page says a reassessment has not finished.
   - This day also shows two overlapping series of records for the same times. Neither series is chosen, so no period is assessed.
5. **Reassessment failed (7 Oct):** `...?day=2026-10-07`
   - The page says the latest reassessment failed. The earlier result is kept for inspection and marked as not current.
6. **Not assessed (any day without data, e.g. 1 Jan 2027):** `...?day=2027-01-01`
   - The page says plainly that nothing exists for that day. It shows no zero, no "healthy" and no default result.
7. **Analysis tab** (from any selected period, "See how the readings lead to this outcome"):
   - Each block's demand, spare capacity and recorded reason or missing input.
   - Confidence, and which record series was used.
   - The stored-record identifiers: run, digests, revisions, jobs and the full list of limitations.
   - The comparison with the earlier file-based results.
   - Fuel, money, alternatives and Finding comparison are labelled "Not yet available".
8. **A stored result opened on another day** (reference only): open a 2 Oct period, copy its `revision=` value, then change `day=` to 2026-10-05. The result reopens marked "not the current one" instead of being passed off as current.

Optional: `.venv\Scripts\python.exe tools\s3_dispatch_walkthrough.py recover` runs the normal assessment worker over 5 and 7 Oct. Reload those days and they read "Up to date".

## Limits to keep in mind

- **The file-based check compared nothing.** The earlier file-based results held no dispatch result for Kobo. The page says "there were none ... This is not a match". It is not proof that the two agree.
- **No fuel, money or saving figure.** "Possibly avoidable" is a bounded estimate, not proof of wasted fuel.
- **No operator command record exists.** An override is neither assumed nor ruled out.
- **Minimum runtime is not a policy result.** The configured minimum runtime only blocks "possibly avoidable". It never makes a block "needed" by policy.
- **The problem days are staged in the private copy only.** They were made by this script:
  - 5 Oct: a reassessment queued and left waiting.
  - 7 Oct: an assessment run that always fails.

  Their 6-hour look-around also marks the neighbouring days (4, 6 and 8 Oct). 1, 2, 3 and 9 Oct are untouched.
- **No older-rule result in this data.** The dispatch-case data was rebuilt under the current rules (dispatch-3.1), so no older-rule result exists here. The "Older rule result" label and the late-record revision history are covered by automated tests, not by this data.
- **Demonstration-data notes do show.** Days 6 and 7 Oct rest on records that the demonstration data labels as fault cases (for example records that arrived in a different order). The Overview shows a "Note supplied with the demonstration data" box on those days, apart from the records and without changing the result. Day 7 Oct has no generator period to select, and the box still appears.
- **There is no list of assessed days yet.** You choose a day with the date box or Previous/Next. Opening Dispatch without a day shows today (UTC), which normally reads "Not assessed".
- **The mock is a reference, not the target.** Compare it with the app in `.agent/S3-01-phase-3b-shots/`: `mock-dispatch-*` against `app-dispatch-*`, at desktop and narrow widths. The mock's single selected hour, fuel note and EAT times are deliberately not reproduced.
