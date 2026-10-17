# Walkthrough: Site > Work > Actions (`s603_site_work_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432. Nothing else: `prepare` builds its own code copy and data.

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s603_owner_w1ux06","--work","var/s603_owner_w1ux06"
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py @T serve --port 9070 --web-port 5570
```
`prepare` takes about a minute and ends with "Prepared. Next: serve ...". `serve` prints the addresses below.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9070"; npm.cmd run dev -- --port 5570 --strictPort
```
Optional third window, to confirm the counts against the database (must end "ATTEST OK"):
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s603_owner_w1ux06","--work","var/s603_owner_w1ux06"
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py @T attest
```

## 3. Ports and addresses
API 9070, web 5570. Mock: `http://localhost:5570/mockups/v69/index.html#/sitework`.

| State | Address | Mock |
| --- | --- | --- |
| Active (two Actions on 1 Nov 2026) | http://localhost:5570/sites/KOBO-001/work?from=2026-11-01T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z | `#/sitework` |
| Same, one per page (Next page) | http://localhost:5570/sites/KOBO-001/work?from=2026-11-01T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z&limit=1 | `#/sitework` |
| Proved zero (October) | http://localhost:5570/sites/KOBO-001/work?from=2026-10-01T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z | `#/sitework` |
| No window chosen (also printed) | http://localhost:5570/sites/KOBO-001/work | `#/sitework` |

## 4. What to look for
- Active: the box reads "Every Action created here in this window" with "As of" and the time, while "How this was worked out" is closed. Rows ACT-000002 and ACT-000001 are listed; each opens its Action.
- One per page: one row and a Next page link.
- Proved zero: the box reads "Checked: nothing to report". There is no small picture in this state.
- No window chosen: the page asks you to choose a window; no answer box (by design).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same window. Reload: same window.

## 5. Data label
Generated demonstration records (test cases run through the real Action service). Not field readings. The "As of" time is the time you look, because the list is read live.

## 6. Stop and clean up
Ctrl+C in both windows, then:
```
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py @T drop
```

## 7. Captured in final run (code `9517eb8e`; `attest` printed ATTEST OK, `s603-attest.txt`)
| Screen | Case | Address (localhost:5570) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| sitework | active | /sites/KOBO-001/work?from=2026-11-01...&to=2026-11-02... | pass | pass | |
| sitework | paged | as above + &limit=1 | pass | pass | |
| sitework | proved zero | ?from=2026-10-01...&to=2026-11-01... | 1 FAIL: no small visual | 1 FAIL: no small visual | zero state draws no picture |
| sitework | no window | /sites/KOBO-001/work | not run | not run | no card by design |

Total `w1-ux-01`: 50/52 (`s603-w1-ux-01.txt`), default `W1_NO_VISUAL_OK` (mini only). Screenshots: `%TEMP%\w1ux06-final\s603` (not in git).
