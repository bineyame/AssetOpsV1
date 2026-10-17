# Walkthrough: Evidence Analysis, what the readings can support (`s302_claim_limit_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432. Nothing else; `prepare` builds its own copy of the code and data.

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s302_w1ux06","--work","var/s302_w1ux06","--port","9040","--web-port","5540"
.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py @T serve
```
`prepare` takes about 2 minutes and ends with "Prepared. Next: serve." (every line "ok"). `serve` keeps running and prints the addresses (also `links`). The revision ids are new on every prepare: always copy them from the printed list.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9040"; npm.cmd run dev -- --port 5540 --strictPort
```
After looking at the current days, in a third window (same first three lines, then):
```
.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py @T late    # one late reading for 6 Oct; 6 Oct goes out of date
```

## 3. Ports and addresses
API 9040, web 5540. Mock: `http://localhost:5540/mockups/v69/index.html#/evidence-analysis`. All addresses start with `http://localhost:5540/sites/KOBO-001/evidence?view=analysis`.

| Day / state | Address (final run) | Mock |
| --- | --- | --- |
| 6 Oct, full coverage (supported) | ...&day=2026-10-06&revision=60851bad-ed23-4bce-9e77-20b280870b00 | `#/evidence-analysis` |
| 11 Oct, unreliable and conflicting readings (limited) | ...&day=2026-10-11&revision=0fc8c8a5-d77d-4185-8fa8-071c28e6118b | `#/evidence-analysis` |
| 6 Oct after `late` (out of date) | same 6 Oct address, reloaded | `#/evidence-analysis` |

`serve` also prints 8 Oct (missing solar reading), 13 Oct (earlier version, audit only), 15 Oct (out of date), "no assessment selected" and a refused address; not captured in this run.

## 4. What to look for
- 6 Oct: under "What the readings can support", the bold answer says the readings support calling this period of generator operation avoidable for 30 min and every needed reading is present; the line "Using the latest checked readings" with the period and "As of" shows while "Technical details" is closed; every needed reading's bar is fully covered.
- 11 Oct: the bold answer says the conclusion holds "for at most 5 min" and the rest is limited; the bars show striped "unreliable or conflicting" parts for solar power and battery output limit; "What limits it" lists the reasons with times.
- 6 Oct after `late`: the line reads "This result may miss newer readings"; no current conclusion, only what the version said at the time.
- "Open this assessment in Performance > Dispatch" goes to the same day.
- Keyboard: Tab reaches the "Technical details" disclosure. Exact link: paste in a new tab, same day. Reload: same day.

## 5. Data label
Authored test cases sent through the real intake and the real assessment worker (labelled fixture records). Not field readings; times are on a demonstration timeline.

## 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py @T drop`.

## 7. Captured in final run (code `08c81613`)
| Screen | Case | Day | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| evidence-analysis (`w1-ux-03`) | supported | 6 Oct | 10/10 | 10/10 | mock shows records first; app leads with "How each limit is set" and the selected assessment |
| evidence-analysis | limited | 11 Oct | 8/8 | 8/8 | state line reads "Using the latest checked readings" (current, limited tone) |
| evidence-analysis | stale (after `late`) | 6 Oct | 10/10 | 10/10 | records list follows the period filter, not the selected day |

Totals: `w1-ux-03` 36/36 for supported and limited (18 at 1440, 18 at 390) (`s302-w1-ux-03.txt`), stale 20/20 (10 at 1440, 10 at 390) (`s302-w1-ux-03-stale.txt`). Screenshots: `%TEMP%\w1ux06-final\s302\` (not in git). Mock lines are counted with the first case of each run.
