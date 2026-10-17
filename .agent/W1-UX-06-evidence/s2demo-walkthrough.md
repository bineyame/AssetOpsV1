# Walkthrough: Site Evidence, readings accepted and not accepted (`s2_demo_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `openssl` on the PATH (the tool makes a fresh test certificate).
- This tool has no `prepare` or `drop` mode: `run` builds everything (and drops/recreates the fixed database `assetops_s2demo`), `serve` reopens it.

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--work","$env:TEMP\s2demo_w1ux06","--tls-port","9031","--http-port","9030"
.venv\Scripts\python.exe tools\s2_demo_walkthrough.py run @T
.venv\Scripts\python.exe tools\s2_demo_walkthrough.py serve @T
```
`run` takes about 4 minutes (it waits two minutes on purpose to show the gateway going quiet) and ends with "Stopping every process this script started". `serve` keeps running. It prints web port 5310; this walkthrough uses 5530 instead.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9030"; npm.cmd run dev -- --port 5530 --strictPort
```

## 3. Ports and addresses
API 9030 (upload server 9031), web 5530.

| Screen / state | Address | Mock |
| --- | --- | --- |
| Evidence, every period | http://localhost:5530/sites/KOBO-001/evidence | `http://localhost:5530/mockups/v69/index.html#/evidence` |
| Evidence, one period (30 Sep 03:00 to 15:00) | http://localhost:5530/sites/KOBO-001/evidence?from=2026-09-30T03:00:00Z&to=2026-09-30T15:00:01Z | `#/evidence` |

The period address is the printed "selected-window link" without its `&view=analysis&record=...` tail (that tail opens Evidence > Analysis).

## 4. What to look for
- The bold answer: "318 readings were accepted for this period from 5 sources."
- The line "Readings received and accepted" with the scope ("Every period on record at this site") and "As of" shows while "How this was worked out" is closed.
- The small bar chart: Accepted 318, Not accepted 1, and the two "arrived again" rows at 0. "What this means" says the 1 reading that was not accepted is explained on Evidence > Analysis; the "Open Evidence > Analysis for this period" link goes there.
- "Which sources reported, and when": readings received, gateway contact and "Analysis up to date: Not yet" as three separate facts; three sources with no accepted reading are listed as facts.
- "Not available yet" for capability conclusions and ranked next evidence (no reviewed rule exists).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste the period address in a new tab, same period. Reload: same page.

## 5. Data label
Generated test data from a registered Lab run, sent by a registered gateway over the real upload path, plus one deliberately faulty fixture batch. Not field readings; times are on a demonstration timeline.

## 6. Stop and clean up
Ctrl+C in both windows, then:
```
docker exec assetopsv1-postgres-1 dropdb -U assetops assetops_s2demo
Remove-Item -Recurse -Force "$env:TEMP\s2demo_w1ux06"
```

## 7. Captured in final run (code `cf382bcd`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| evidence (`w1-ux-01`) | `all` (318 accepted, 1 not accepted) | every period | 10/10 | 10/10 | mock leads with a capability table; app says capability conclusions are "Not available yet" |
| evidence (`w1-ux-01`) | `window` | 30 Sep period | 8/8 | 8/8 | |
| evidence (`w1-ux-03`) | `all` | every period | 10/10 | 10/10 | mock source badges (Gap/Good/Limited, "Affects") and ranked next steps have no read |
| evidence (`w1-ux-03`) | `window` | 30 Sep period | 8/8 | 8/8 | |

Totals: `w1-ux-01` 36/36 (18 at 1440, 18 at 390), `w1-ux-03` 36/36 (18 at 1440, 18 at 390) (`s2demo-w1-ux-0*.txt`). Screenshots: `%TEMP%\w1ux06-final\s2demo\` (not in git). Mock lines are counted with the first case.
