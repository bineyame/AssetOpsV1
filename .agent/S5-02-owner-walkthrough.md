# S5-02 owner walkthrough - Finding list in the Site Overview

What you are checking: on a Site's Overview page, the "Findings" panel now lists the Findings for the selected day
(from the Site Findings list), or says honestly that it cannot. It never says "no Findings" unless that day was
assessed and matched, and never shows a count from a read that is not current.

All commands run in PowerShell from `C:\Users\assef\Bineyame\AssetOpsV1-review3` on branch
`task/S5-02-overview-finding-list`. Docker Postgres must be running. Ports: API 8952, web 5452. The private
database is `assetops_s404_owner_s502` and its work folder `var\s404_owner_s502`; nothing else is touched.

## 1. Prepare (a few minutes, once; about 3 minutes on 2026-10-16)

```powershell
$w=(Get-Location).Path; $env:PYTHONPATH="$w\backend;$w\contracts;$w\gateway;$w\simulator"
.\.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py prepare
```

It ends with `0 Overview check(s) failed`. (If `var\sites\kobo-001.yaml` is missing, copy it from the main checkout's
`var\sites` first.)

## 2. Serve (two windows; leave both open)

Window A (API; same `$env:PYTHONPATH` line first):

```powershell
.\.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py serve
```

Window B (website):

```powershell
cd frontend; $env:ASSETOPS_API_PORT="8952"; npm.cmd run dev -- --port 5452 --strictPort
```

## 3. Look at each day (scroll to the "Findings" panel)

| Open | What you should see |
| --- | --- |
| http://localhost:5452/sites/KOBO-001?date=2026-10-25 | "No Findings for this day." with the days that were checked, and a link to the full list. |
| http://localhost:5452/sites/KOBO-001?date=2026-10-30 | "Not known. This window has not been assessed..." No rows, no count, and a line saying this is not a statement that the day has no Findings. |
| http://localhost:5452/sites/KOBO-001?date=2026-10-27 | "Not current. Newer evidence or work for this window is waiting to be assessed." No rows, no count. |
| http://localhost:5452/sites/KOBO-001?date=2026-11-05 | "Not known. Assessment work for this window failed." No rows, no count. |
| http://localhost:5452/sites/KOBO-001?date=2026-10-15 | "N Findings overlap this day.", two rows (newest first), "Showing the first 2 of N. This is not the whole list.", a link to the full list, and one line comparing the first row with the Finding shown above it (see note). |

On 2026-10-15 also:

1. Press Tab until the first row's link is highlighted, press Enter: the Finding page opens at that exact version.
2. Press the browser Back button: you are back on the Overview for 2026-10-15.
3. Reload (F5): same day, same rows.
4. Click "Open the full Findings list for this day": the Site Findings page opens for the same day with all rows.
5. Back on the Overview, click "Next day": the panel now shows 2026-10-16, never the 2026-10-15 rows.

Note on the comparison line: the Finding card above the list and the list are two separate reads. The page only
says "the same Finding version" when both reads are current on the same basis. Otherwise it says they cannot be
compared and offers "Reload both". Money on these pages reads limited because no schedule runs in this walkthrough;
that is expected and not part of this check.

## 4. Change the data (Window C, same `$env:PYTHONPATH` line first)

| Run | Then open 2026-10-15 and look for |
| --- | --- |
| `.\.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py late` | "Not current", no rows, no count. |
| `.\.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py settle` | Rows again, now led by the late Finding, and the comparison line again says "the same Finding version". |
| `.\.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py gate --close` | "Not known. The Findings list is closed for this Site..." no rows, no count; the rest of the Overview still shows. |
| `.\.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py gate --open` | Back to normal. |

## 5. Clean up

Stop windows A and B with Ctrl+C, then:

```powershell
.\.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py drop
```

## What is not in this slice

Wording polish (W1-conclusion task). The v6.9 mock's priority, action and money items in "Needs attention" are not
shown: no supported evidence exists for them yet.
