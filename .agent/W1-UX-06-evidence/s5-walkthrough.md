# Walkthrough: Site Overview for one day (`s5_overview_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` copied from the main checkout into this folder (`var/` is ignored by git).

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s501_owner_w1ux06","--work","var/s501_owner_w1ux06","--api-port","8980","--web-port","5480"
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py @T serve
```
`prepare` takes about 4 minutes and must end with "0 failed checks". `serve` prints the day addresses.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="8980"; npm.cmd run dev -- --port 5480 --strictPort
```
Third window, within 5 minutes before looking (repeat if more than 5 minutes pass):
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s501_owner_w1ux06","--work","var/s501_owner_w1ux06","--api-port","8980","--web-port","5480"
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py @T tick
```

## 3. Ports and addresses
API 8980, web 5480. Mock: `http://localhost:5480/mockups/v69/index.html#/mini`.

| Day | Address | Mock |
| --- | --- | --- |
| P01, money shown | http://localhost:5480/sites/KOBO-001?date=2026-10-23 | `#/mini` |
| Not assessed | http://localhost:5480/sites/KOBO-001?date=2026-11-10 | `#/mini` |
| Ordinary day (also printed) | http://localhost:5480/sites/KOBO-001?date=2026-10-02 | `#/mini` |
| Failed day (also printed) | http://localhost:5480/sites/KOBO-001?date=2026-10-07 | `#/mini` |
| P02, money held back (also printed) | http://localhost:5480/sites/KOBO-001?date=2026-10-24 | `#/mini` |

## 4. What to look for
- P01: the bold answer says "No operating objective is stated for this day"; the green box "Using the latest checked readings" shows the day, site and "As of" time while "How this was worked out" is closed.
- The fuel-cost card shows "0.00 to 15.82 USD" with a two-bar range and says it is prepared example data.
- The link "Open this day in Performance > Dispatch" goes to the day's dispatch view.
- Not assessed: the answer says it cannot judge this yet, with no amount.
- If more than 5 minutes passed since `tick`, the page says the schedule stopped and hides the amount; run `tick` again.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same day. Reload: same day.

## 5. Data label
Authored demonstration cases (P01, P02) and generated simulated readings (ordinary day). Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows, then:
```
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py @T drop
```

## 7. Captured in final run (code `7f438f8f`, `tick` just before capture)
| Screen | Case | Address (localhost:5480) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| mini (`w1-ux-02`) | p01 | /sites/KOBO-001?date=2026-10-23 | 18/18 (both cases) | 20/20 (both cases) | mock objective strip, five-objective view and KPI tiles not built |
| mini (`w1-ux-02`) | unassessed | ?date=2026-11-10 | pass | pass | |
| mini (`w1-ux-01`) | p01, unassessed | as above | 18/18 (both cases) | 18/18 (both cases) | objective card has no small picture (allowed for `mini` by the script default) |

Totals: `w1-ux-02` 38/38 (`s5-w1-ux-02.txt`); `w1-ux-01` 36/36 (`s5-w1-ux-01.txt`). Ordinary, failed and P02 days were not captured (not in the brief's case list). Screenshots: `%TEMP%\w1ux06-final\s5\ux02` and `\ux01` (not in git).
