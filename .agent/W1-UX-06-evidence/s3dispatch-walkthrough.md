# Walkthrough: Performance > Dispatch and its Analysis (`s3_dispatch_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- The shared producer database `assetops_s3cases` must exist (it is copied, never changed). If `prepare` says it is missing or out of date, run `.venv\Scripts\python.exe tools\s3_dispatch_cases.py run` once (same first two lines as below).
- This tool has no `drop` mode and uses fixed names: database `assetops_s3walk`, work folder `%LOCALAPPDATA%\AssetOps\s3-dispatch-walkthrough`.

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
.venv\Scripts\python.exe tools\s3_dispatch_walkthrough.py prepare
.venv\Scripts\python.exe tools\s3_dispatch_walkthrough.py serve --port 9050
```
`prepare` takes under a minute and ends with "Prepared. Next: serve." `serve` keeps running. It prints web port 5320; this walkthrough uses 5550 instead.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9050"; npm.cmd run dev -- --port 5550 --strictPort
```

## 3. Ports and addresses
API 9050, web 5550. All addresses start with `http://localhost:5550/sites/KOBO-001/performance/dispatch`.

| Day / state | Address | Mock |
| --- | --- | --- |
| 9 Oct, generator needed, partly bounded (limited) | ...?day=2026-10-09 (printed by `serve`) | `http://localhost:5550/mockups/v69/index.html#/dispatch` |
| 2 Oct, possibly avoidable, no limits (supported) | ...?day=2026-10-02 | `#/dispatch` |
| 9 Oct Analysis | ...?day=2026-10-09&revision=e1cb9f3c-0424-4d37-9ba6-0fc3337984e1&view=analysis | `#/analysis` |
| 2 Oct Analysis | ...?day=2026-10-02&revision=5671edfb-6901-4ddf-8026-ab2ec388c045&view=analysis | `#/analysis` |

`serve` prints only the 9 Oct day address. The 2 Oct day address is the printed one with the day changed (the page's day picker gives the same address); the two revision ids are the day's current result as the served API reports it (`http://127.0.0.1:9050/api/sites/KOBO-001/performance/dispatch/windows/<day>`, first interval `id`). They stay the same on every `prepare` while `assetops_s3cases` is unchanged; on the page, "Open Dispatch > Analysis" reaches the same view. Day picker: 5 Oct shows "out of date" and 7 Oct shows "failed" (staged by this tool).

## 4. What to look for
- 9 Oct: the bold answer "The generator operated for at least 7 h 30 min: 0 min possibly avoidable, 7 h 30 min needed and 0 min that cannot be determined."; the line "Using the latest checked readings" with the day and "As of" while "How this was worked out" is closed; the 15-minute block strip and four totals; "What limits this day's result: A generator period is only partly bounded by the records."
- 2 Oct: "The generator operated for 5 h 30 min to 6 h: 4 h possibly avoidable, 1 h 30 min needed and 0 min that cannot be determined."; "What limits this day's result" says no limitation is recorded.
- Analysis: how the readings lead to each outcome for the selected result, with the same state line; the constraint table scrolls inside its card on a phone.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same day. Reload: same day.

## 5. Data label
Generated test data (registered simulator runs through the real intake, `s3-dispatch-cases-v1`) plus two clearly labelled fault fixtures. Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows, then:
```
docker exec assetopsv1-postgres-1 dropdb -U assetops assetops_s3walk
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\AssetOps\s3-dispatch-walkthrough"
```
Leave `assetops_s3cases` (shared producer).

## 7. Captured in final run (code `bf76f7ff`)
| Screen | Case | Day | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| dispatch (`w1-ux-03`) | limited | 9 Oct | 10/10 | 10/10 | mock has a PV/load/generator kW chart; app has the block strip and totals (no kW series in the read) |
| dispatch | supported | 2 Oct | 8/8 | 8/8 | full records and 12-row coverage tables make the page long |
| analysis (`w1-ux-03`) | limited | 9 Oct | 10/10 | 10/10 | mock `#/analysis` is a Finding Analysis; only section names align |
| analysis | supported | 2 Oct | 8/8 | 8/8 | |

Totals: `w1-ux-03` 72/72 (36 at 1440, 36 at 390) (`s3dispatch-w1-ux-03.txt`). Screenshots: `%TEMP%\w1ux06-final\s3dispatch\` (not in git). Mock lines are counted with the first case of each screen.
