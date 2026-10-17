# W1 combined owner walkthrough

Final version, written at W1-UX-06 phase 2 (2026-10-17). It covers all 26 W1 Site screens plus the S4-08 fuel-price history. Follow it top to bottom. Each part prepares one test case, serves it, shows you what to look at, and then cleans it up again.

## What changed in W1, in plain words

W1 did not add new features or new data. It changed how the existing Site screens explain themselves, so that each one reads like the v69 mock-up while saying no more than the stored records support.

- **Most screens now open with an answer card.** (Exceptions: some held or empty states draw no picture, listed in owner note 10, and a few refusal or not-yet-stored states show no card at all, marked "not run" in their part's capture table.) At the top is the question the screen answers, for example "Which site should I open?" or "What can we rely on?". Below it come a short plain answer, a state line, a small picture (bars, a step strip or a time strip), "What this means" and "What to do", and a link to the place that holds the detail.
- **The state line is always visible.** It gives the state, what the answer covers, and "As of <time>". When the record has no time, it says "As of: time not recorded", and never pretends the time is now.
- **Codes and IDs are tucked away.** References, versions and codes sit in one closed "How this was worked out" section at the bottom of each card. The main reading uses plain words.
- **Unknown is shown as unknown.** A missing value is drawn as a hatched "not known" mark, never as a zero bar. Refused, unavailable, stale or withdrawn reads say so in words.
- **A current amount is shown only when the current read proves it is current and priced.** Otherwise the screen says "No current amount can be shown" or "No price recorded", and never shows zero. Earlier recorded amounts appear only on history pages, each labelled as history.
- **Set-up and health stay separate.** The Readiness badge now says "Set up to report", which means configuration only. Gateway contact is shown on Health, and contact never stands in for equipment condition.
- **Test data is labelled.** All data in this walkthrough is authored, generated or simulated test data, not field readings. Do not compare numbers between different cases; each case is its own story.

## Before you start (once)

1. Open PowerShell and go to the folder you will run everything from, then confirm it is on the merged revision:
   ```powershell
   cd C:\Users\assef\Bineyame\AssetOpsV1
   git log --oneline -1
   ```
   The line shown must be the commit the coordinator gives you (the W1 closeout merge). If it is not, stop and ask. Use only this folder for the whole walkthrough.
2. Docker Desktop is running, with the AssetOps Postgres container on port 55432.
3. In **every** PowerShell window you open for this walkthrough, paste these lines first (they move to the walkthrough folder and set the paths every command below uses):
   ```powershell
   cd C:\Users\assef\Bineyame\AssetOpsV1
   $wt = (Get-Location).Path
   $env:PYTHONPATH = "$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
   ```
   The Python used is `$wt\.venv\Scripts\python.exe` (the `.venv\Scripts\python.exe` lines below, run from `$wt`).
4. Site files and dependencies (once). Dependencies changed during W1, so install them; the site files are copied only if missing:
   ```powershell
   New-Item -ItemType Directory -Force "$wt\var\sites" | Out-Null
   if (-not (Test-Path "$wt\var\sites\kobo-001.yaml")) { Write-Host "kobo-001.yaml is missing in var\sites; ask the coordinator for the site files" }
   cd $wt\frontend
   npm.cmd ci
   cd $wt
   ```
   Stop any AssetOps dev server already running from this folder before `npm.cmd ci`.
5. Each part uses **two windows**. Window 1 runs the test-case tool (its API server). Window 2 runs the screens:
   ```powershell
   cd $wt\frontend
   $env:ASSETOPS_API_PORT = "<API port named in the part>"
   npm.cmd run dev -- --port <web port named in the part> --strictPort
   ```
   Open the addresses on `http://localhost:<web port>`. Use `localhost`, not `127.0.0.1`.
6. Open the mock-up beside the app at `http://localhost:<web port>/mockups/v69/index.html#/<screen id>`.
7. **On every screen, check:**
   - the answer card reads in plain words;
   - the state line (state, scope, "As of ...") is visible while "How this was worked out" is closed;
   - pressing Tab from the top eventually reaches "How this was worked out";
   - copying the address into a new tab opens the same view;
   - reloading keeps the same view.
   Narrow the browser to phone width (about 390 px) and check that nothing scrolls sideways.
8. **Run one part at a time.** When a part is finished, stop both windows with Ctrl+C and run its clean-up lines before you start the next part.

## Where each of the 26 screens is walked

| # | Screen | Part | | # | Screen | Part |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `sites` | Part 1 | | 14 | `financials` | Part 10 |
| 2 | `mini` | Part 2 | | 15 | `assumptions` | Part 11 |
| 3 | `foundation` | Part 1 | | 16 | `recommendation` | Part 13 |
| 4 | `readiness` | Part 1 | | 17 | `changes` | Part 13 |
| 5 | `sld` | Part 1 | | 18 | `action-overview` | Part 13 |
| 6 | `evidence` | Part 4 | | 19 | `action-execution` | Part 13 |
| 7 | `evidence-analysis` | Part 6 | | 20 | `action-history` | Part 13 |
| 8 | `dispatch` | Part 7 | | 21 | `action-plan` | Part 14 |
| 9 | `analysis` | Part 7 | | 22 | `action-evidence` | Part 14 |
| 10 | `finding` | Part 8 | | 23 | `verification` | Part 14 |
| 11 | `finding-evidence` | Part 5 | | 24 | `sitework` | Part 15 |
| 12 | `finding-history` | Part 8 | | 25 | `health` | Part 16 |
| 13 | `sitefindings` | Part 9 | | 26 | `asset` | Part 16 |

The S4-08 fuel-price history (default address and `recorded_at` moments) is Part 12. Parts 2 and 3 both cover `mini`, and Parts 3 and 9 both cover `sitefindings`.

**About the addresses below.** The long IDs in each address come from the final capture run. Most tools make new IDs each time `prepare` or `links` runs, so use the addresses **your** run prints, and treat the ones here as examples of their shape. Where a part says an address was not printed by the tool, reach that view by clicking from a printed page.

## Part 1. Sites, Foundation, Readiness, single line diagram (`v01a_foundation_walkthrough.py`)

Screens: sites, foundation, readiness, sld. Run log: `.agent/W1-UX-06-evidence/v01a-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` present in this folder (see "Before you start", step 4) (`var/` is ignored by git).
- The shared test database `assetops_s4cases` must exist. If `docker exec assetopsv1-postgres-1 psql -U assetops -lqt` does not list it, run once:
```
.venv\Scripts\python.exe tools\s4_finding_cases.py run
```

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_v01awalk_w1ux06","--empty-db","assetops_v01aempty_w1ux06","--work-name","v01a-w1ux06"
.venv\Scripts\python.exe tools\v01a_foundation_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\v01a_foundation_walkthrough.py @T links --web-port 5460 --empty-web-port 5461
.venv\Scripts\python.exe tools\v01a_foundation_walkthrough.py @T serve --port 8960 --web-port 5460 --empty-port 8961 --empty-web-port 5461
```
Second window (stocked site):
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="8960"; npm.cmd run dev -- --port 5460 --strictPort
```
Third window (no site stored):
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="8961"; npm.cmd run dev -- --port 5461 --strictPort
```

### 3. Ports and addresses
APIs 8960 (stocked) and 8961 (empty); web 5460 and 5461. Mock: `http://localhost:5460/mockups/v69/index.html#/<id>`.

| Screen | Address | Mock |
| --- | --- | --- |
| Sites | http://localhost:5460/sites | `#/sites` |
| Sites, none stored | http://localhost:5461/sites | `#/sites` |
| Site model, in effect now | http://localhost:5460/sites/KOBO-001/foundation | `#/foundation` |
| Site model, scheduled | http://localhost:5460/sites/KOBO-001/foundation?at=2026-10-22T00:00:00Z | `#/foundation` |
| Site model, before any stored version | http://localhost:5460/sites/KOBO-001/foundation?at=2026-09-01T00:00:00Z | `#/foundation` |
| Readiness, now | http://localhost:5460/sites/KOBO-001/foundation/readiness | `#/readiness` |
| Readiness, imported period | http://localhost:5460/sites/KOBO-001/foundation/readiness?at=2026-09-30T00:00:00Z | `#/readiness` |
| Diagram, now | http://localhost:5460/sites/KOBO-001/foundation/sld | `#/sld` |
| Diagram, battery chosen | http://localhost:5460/sites/KOBO-001/foundation/sld?at=2026-10-22T00:00:00Z&component=battery | `#/sld` |

### 4. What to look for
- The bold first sentence of the top card answers the question in plain words (for example "9 pieces of equipment and 4 of 5 operating settings are recorded").
- Under it, with "How this was worked out" still closed, the state box shows the state, the site and version, and an "As of" time. On Sites it says "As of: time not recorded" (the list has no read time).
- The small picture (bars or setting tiles) is beside the answer; Sites has none by design.
- The link under the card goes to the next place (Readiness, Single line diagram, Health).
- Scheduled view: a yellow line says this is not the configuration in effect now.
- Before any stored version: only the state line shows, no card (by design). Look by eye only.
- Battery chosen: the battery is highlighted and stays chosen after a reload.
- Keyboard: press Tab from the top of the page; it reaches "How this was worked out".
- Exact link: paste the address in a new tab; the same view opens. Reload: nothing changes.

### 5. Data label
Authored test configuration of KOBO-001 (imported and published Foundation versions). Not field readings.

### 6. Stop and clean up
Ctrl+C in all three windows, then:
```
.venv\Scripts\python.exe tools\v01a_foundation_walkthrough.py @T drop
```
`drop` removes both databases and the work folder `%LOCALAPPDATA%\AssetOps\v01a-w1ux06`.

### 7. Captured in final run (code `b7d75daf`)
| Screen | Case | Address (localhost) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| sites | stocked | 5460/sites | 17/17 (both cases) | 19/19 (both cases) | mock counts (needs attention, evidence limited), assessment/top-issue columns and "In setup" table not built; shown as "Not available yet" |
| sites | empty | 5461/sites | pass | pass | no "How this was worked out" in this state (nothing to reference) |
| foundation | now, scheduled | 5460/.../foundation[?at=2026-10-22...] | pass | pass | |
| foundation | before any version | ?at=2026-09-01... | **not run** | **not run** | no card by design; manual look only |
| readiness | now, imported | .../readiness[?at=2026-09-30...] | pass | pass | stale gateway contact shows only in the panel below the card |
| sld | now, battery | .../sld[?at=2026-10-22...&component=battery] | pass | pass | at 390 the diagram is cut at the right edge and scrolls inside its own box |

Totals: `w1-ux-02` 36/36 (`v01a-w1-ux-02.txt`); `w1-ux-05` 108/108, 54 at 1440 and 54 at 390 (`v01a-w1-ux-05.txt`). Screenshots: `%TEMP%\w1ux06-final\v01a` (not in git).

## Part 2. Site Overview for one day (`s5_overview_walkthrough.py`)

Screens: mini. Run log: `.agent/W1-UX-06-evidence/s5-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` present in this folder (see "Before you start", step 4) (`var/` is ignored by git).

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s501_owner_w1ux06","--work","var/s501_owner_w1ux06","--api-port","8980","--web-port","5480"
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py @T serve
```
`prepare` takes about 4 minutes and must end with "0 failed checks". `serve` prints the day addresses.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="8980"; npm.cmd run dev -- --port 5480 --strictPort
```
Third window, within 5 minutes before looking (repeat if more than 5 minutes pass):
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s501_owner_w1ux06","--work","var/s501_owner_w1ux06","--api-port","8980","--web-port","5480"
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py @T tick
```

### 3. Ports and addresses
API 8980, web 5480. Mock: `http://localhost:5480/mockups/v69/index.html#/mini`.

| Day | Address | Mock |
| --- | --- | --- |
| P01, money shown | http://localhost:5480/sites/KOBO-001?date=2026-10-23 | `#/mini` |
| Not assessed | http://localhost:5480/sites/KOBO-001?date=2026-11-10 | `#/mini` |
| Ordinary day (also printed) | http://localhost:5480/sites/KOBO-001?date=2026-10-02 | `#/mini` |
| Failed day (also printed) | http://localhost:5480/sites/KOBO-001?date=2026-10-07 | `#/mini` |
| P02, money held back (also printed) | http://localhost:5480/sites/KOBO-001?date=2026-10-24 | `#/mini` |

### 4. What to look for
- P01: the bold answer says "No operating objective is stated for this day"; the green box "Using the latest checked readings" shows the day, site and "As of" time while "How this was worked out" is closed.
- The fuel-cost card shows "0.00 to 15.82 USD" with a two-bar range and says it is prepared example data.
- The link "Open this day in Performance > Dispatch" goes to the day's dispatch view.
- Not assessed: the answer says it cannot judge this yet, with no amount.
- If more than 5 minutes passed since `tick`, the page says the schedule stopped and hides the amount; run `tick` again.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same day. Reload: same day.

### 5. Data label
Authored demonstration cases (P01, P02) and generated simulated readings (ordinary day). Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows, then:
```
.venv\Scripts\python.exe tools\s5_overview_walkthrough.py @T drop
```

### 7. Captured in final run (code `7f438f8f`, `tick` just before capture)
| Screen | Case | Address (localhost:5480) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| mini (`w1-ux-02`) | p01 | /sites/KOBO-001?date=2026-10-23 | 18/18 (both cases) | 20/20 (both cases) | mock objective strip, five-objective view and KPI tiles not built |
| mini (`w1-ux-02`) | unassessed | ?date=2026-11-10 | pass | pass | |
| mini (`w1-ux-01`) | p01, unassessed | as above | 18/18 (both cases) | 18/18 (both cases) | objective card has no small picture (allowed for `mini` by the script default) |

Totals: `w1-ux-02` 38/38 (`s5-w1-ux-02.txt`); `w1-ux-01` 36/36 (`s5-w1-ux-01.txt`). Ordinary, failed and P02 days were not captured (not in the brief's case list). Screenshots: `%TEMP%\w1ux06-final\s5\ux02` and `\ux01` (not in git).

## Part 3. Overview Finding list and Site Findings bridge (`s502_overview_finding_list_walkthrough.py`)

Screens: mini (Finding row), sitefindings (bridge). Run log: `.agent/W1-UX-06-evidence/s502-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` present in this folder (see "Before you start", step 4) (`var/` is ignored by git).

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s404_owner_s502_w1ux06","--work","var/s404_owner_s502_w1ux06","--api-port","8990","--web-port","5490","--tls-port","8991","--http-port","8992"
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py prepare @T
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py serve @T
```
`prepare` takes about 4 minutes and must end with "0 failed check(s)" and "0 Overview check(s) failed". `serve` prints the addresses.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="8990"; npm.cmd run dev -- --port 5490 --strictPort
```
Look at the first set of days BEFORE running `tick`: `tick` assesses the waiting evidence, so the "out of date" day becomes current. Then, in a third window (same first two lines as above, then `$T=...`), one at a time:
```
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py late @T      # late readings for 15 Oct, not yet assessed
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py settle @T    # assess them; 15 Oct is current again
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py gate --close @T   # the list is closed
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py gate --open @T    # undo
```

### 3. Ports and addresses
API 8990, web 5490. Mocks: `http://localhost:5490/mockups/v69/index.html#/mini` and `#/sitefindings`.

| Day / state | Address | Mock |
| --- | --- | --- |
| 15 Oct, Findings listed | http://localhost:5490/sites/KOBO-001?date=2026-10-15 | `#/mini` |
| 25 Oct, checked and none found | http://localhost:5490/sites/KOBO-001?date=2026-10-25 | `#/mini` |
| 27 Oct, out of date | http://localhost:5490/sites/KOBO-001?date=2026-10-27 | `#/mini` |
| 5 Nov, check failed | http://localhost:5490/sites/KOBO-001?date=2026-11-05 | `#/mini` |
| 30 Oct, not assessed | http://localhost:5490/sites/KOBO-001?date=2026-10-30 | `#/mini` |
| Full list, 15 Oct | http://localhost:5490/sites/KOBO-001/findings?from=2026-10-15T00%3A00%3A00Z&to=2026-10-16T00%3A00%3A00Z&domain=mini-grid-dispatch | `#/sitefindings` |
| Full list, 25 Oct (none) | http://localhost:5490/sites/KOBO-001/findings?from=2026-10-25T00%3A00%3A00Z&to=2026-10-26T00%3A00%3A00Z&domain=mini-grid-dispatch | `#/sitefindings` |
| Full list, 27 Oct | http://localhost:5490/sites/KOBO-001/findings?from=2026-10-27T00%3A00%3A00Z&to=2026-10-28T00%3A00%3A00Z&domain=mini-grid-dispatch | `#/sitefindings` |

The Finding page is opened from a row on 15 Oct; its address changes with every `prepare` (in the final run: `/sites/KOBO-001/findings/56c36dcf-...?revision_id=dfd7ace9-...`).

### 4. What to look for
- 15 Oct: the list shows Findings in order and says "Showing the first 2 of 3. This is not the whole list."; each row opens that exact Finding; "Open the full Findings list for this day" opens the same day on Site Findings.
- 25 Oct: "No Findings for this day." with the green state line. 27 Oct, 5 Nov, 30 Oct: no rows and no count, with the reason (out of date, failed, not assessed).
- After `late`: 15 Oct shows no rows and says it is out of date. After `settle`: rows are back. After `gate --close`: the list says it is closed with no rows; the rest of the Overview stays.
- The state line (state, site, "As of") is visible with "How this was worked out" closed.
- Keyboard: Tab reaches "How this was worked out"; Enter on a row opens the Finding and Back returns to the same day. Exact link: paste in a new tab, same day. Reload: same day and rows.

### 5. Data label
Authored test cases sent through the real intake (labelled fixture batches). Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py drop @T`.

### 7. Captured in final run (code `41160b19`; no `tick` before the first set)
| Screen | Case | Address (localhost:5490) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| mini Finding list (`s502` initial) | empty, unassessed, dirty, failed, positive, row, back, reload, full list, date change | as table above | 42/42 | 42/42 | mock KPI tiles and objective strip not built |
| mini Finding list (`s502` late) | positive after `late` | ?date=2026-10-15 | 5/5 | 5/5 | |
| mini Finding list (`s502` settled) | positive after `settle` | ?date=2026-10-15 | 6/6 | 6/6 | |
| mini Finding list (`s502` closed) | positive, empty with gate closed | ?date=2026-10-15, 10-25 | 10/10 | 10/10 | |
| mini (`w1-ux-02`) | positive, empty | ?date=2026-10-15, 10-25 | pass | pass | objective card has no small picture ("none by design") |
| sitefindings (`w1-ux-02`) | positive, empty (proved zero), dirty | /findings 15, 25, 27 Oct | pass | pass | lens chips, priority/confidence columns not built |
| mini, sitefindings (`w1-ux-02`) | late | 15 Oct | pass | pass | |

Totals: `s502` initial 84/84, late 10/10, settled 12/12, closed 20/20; `w1-ux-02` 93/93 and late 42/42. An earlier initial run made after `tick` scored 82/84 (27 Oct read "none found" instead of "out of date" because `tick` assessed it); kept as `s502-s502-initial-after-tick.txt`, then re-prepared and rerun. The s502 script's list-token selector was updated (`41160b19`). Screenshots: `%TEMP%\w1ux06-final\s502\` (not in git).

## Part 4. Site Evidence, readings accepted and not accepted (`s2_demo_walkthrough.py`)

Screens: evidence. Run log: `.agent/W1-UX-06-evidence/s2demo-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `openssl` on the PATH (the tool makes a fresh test certificate).
- This tool has no `prepare` or `drop` mode: `run` builds everything (and drops/recreates the fixed database `assetops_s2demo`), `serve` reopens it.

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--work","$env:TEMP\s2demo_w1ux06","--tls-port","9031","--http-port","9030"
.venv\Scripts\python.exe tools\s2_demo_walkthrough.py run @T
.venv\Scripts\python.exe tools\s2_demo_walkthrough.py serve @T
```
`run` takes about 4 minutes (it waits two minutes on purpose to show the gateway going quiet) and ends with "Stopping every process this script started". `serve` keeps running. It prints web port 5310; this walkthrough uses 5530 instead.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9030"; npm.cmd run dev -- --port 5530 --strictPort
```

### 3. Ports and addresses
API 9030 (upload server 9031), web 5530.

| Screen / state | Address | Mock |
| --- | --- | --- |
| Evidence, every period | http://localhost:5530/sites/KOBO-001/evidence | `http://localhost:5530/mockups/v69/index.html#/evidence` |
| Evidence, one period (30 Sep 03:00 to 15:00) | http://localhost:5530/sites/KOBO-001/evidence?from=2026-09-30T03:00:00Z&to=2026-09-30T15:00:01Z | `#/evidence` |

The period address is the printed "selected-window link" without its `&view=analysis&record=...` tail (that tail opens Evidence > Analysis).

### 4. What to look for
- The bold answer: "318 readings were accepted for this period from 5 sources."
- The line "Readings received and accepted" with the scope ("Every period on record at this site") and "As of" shows while "How this was worked out" is closed.
- The small bar chart: Accepted 318, Not accepted 1, and the two "arrived again" rows at 0. "What this means" says the 1 reading that was not accepted is explained on Evidence > Analysis; the "Open Evidence > Analysis for this period" link goes there.
- "Which sources reported, and when": readings received, gateway contact and "Analysis up to date: Not yet" as three separate facts; three sources with no accepted reading are listed as facts.
- "Not available yet" for capability conclusions and ranked next evidence (no reviewed rule exists).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste the period address in a new tab, same period. Reload: same page.

### 5. Data label
Generated test data from a registered Lab run, sent by a registered gateway over the real upload path, plus one deliberately faulty fixture batch. Not field readings; times are on a demonstration timeline.

### 6. Stop and clean up
Ctrl+C in both windows, then:
```
docker exec assetopsv1-postgres-1 dropdb -U assetops assetops_s2demo
Remove-Item -Recurse -Force "$env:TEMP\s2demo_w1ux06"
```

### 7. Captured in final run (code `cf382bcd`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| evidence (`w1-ux-01`) | `all` (318 accepted, 1 not accepted) | every period | 10/10 | 10/10 | mock leads with a capability table; app says capability conclusions are "Not available yet" |
| evidence (`w1-ux-01`) | `window` | 30 Sep period | 8/8 | 8/8 | |
| evidence (`w1-ux-03`) | `all` | every period | 10/10 | 10/10 | mock source badges (Gap/Good/Limited, "Affects") and ranked next steps have no read |
| evidence (`w1-ux-03`) | `window` | 30 Sep period | 8/8 | 8/8 | |

Totals: `w1-ux-01` 36/36 (18 at 1440, 18 at 390), `w1-ux-03` 36/36 (18 at 1440, 18 at 390) (`s2demo-w1-ux-0*.txt`). Screenshots: `%TEMP%\w1ux06-final\s2demo\` (not in git). Mock lines are counted with the first case.

## Part 5. Finding Evidence and Financials source labels (`s405_provenance_walkthrough.py`, owner case)

Screens: finding-evidence, financials (source label), evidence (Finding-level). Run log: `.agent/W1-UX-06-evidence/s405-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` present in this folder (see "Before you start", step 4) (`var/` is ignored by git).

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--suffix","_w1ux06","--api-port","9020","--web-port","5520","--tls-port","9021","--http-port","9022"
.venv\Scripts\python.exe tools\s405_provenance_walkthrough.py prepare --only owner @T
.venv\Scripts\python.exe tools\s405_provenance_walkthrough.py links @T
.venv\Scripts\python.exe tools\s405_provenance_walkthrough.py serve --case owner @T
```
`prepare` takes about 2 minutes and must end with "failed checks: {'owner': 0}". `links` prints the addresses (the ids are new on every prepare, so always copy them from `links`). `serve` keeps running and re-checks the schedule every two minutes.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9020"; npm.cmd run dev -- --port 5520 --strictPort
```

### 3. Ports and addresses
API 9020, web 5520. Addresses from the final run (`<F1>` = `cff9cbd1-3ae4-449e-b2ee-893a04c61bca`, `<R1>` = `45e11224-cf58-450a-9156-58bfafdd0ee1`; `<F2>` = `3f93014d-7b29-4d6a-adca-578786f74f6a`, `<R2>` = `a570010c-154e-4af2-8e42-b1874f9b88b7`):

| Screen / state | Address | Mock |
| --- | --- | --- |
| Finding Evidence, 23 Oct (prepared example data) | http://localhost:5520/sites/KOBO-001/findings/<F1>/evidence?revision_id=<R1> | `http://localhost:5520/mockups/v69/index.html#/finding-evidence` |
| Financials, 23 Oct, amount shown with its source | http://localhost:5520/sites/KOBO-001/financials?finding_id=<F1>&revision_id=<R1> | `#/financials` |
| Financials, 24 Oct, amount withheld | http://localhost:5520/sites/KOBO-001/financials?finding_id=<F2>&revision_id=<R2> | `#/financials` |

`links` also prints the 2 Oct "Generated test data" Finding/Evidence/Financials and the older versions; they were not captured in this run.

### 4. What to look for
- Finding Evidence: the bold answer says where this Finding's readings came from; the line "Latest recorded version, opened by its exact reference" with "As of" shows while "How this was worked out" is closed; a "Source record for this finding version" panel says "Prepared example data"; links back to the Finding.
- Financials 23 Oct: a money range (0.00 to 15.82 USD) with "Modelled range, using the latest checked readings", the same source label as the Finding, and a link to the Evidence.
- Financials 24 Oct: "No current amount can be shown" - no number, because the generator readings needed for it are missing. Its "As of" reads "time not recorded" (no read time for this state).
- Site Evidence with a source label: open `http://localhost:<web port>/sites/KOBO-001/evidence` (the web port this part prints). It should show the source label for the site's latest evidence, or say plainly that the source is unknown.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same page. Reload: same page.

### 5. Data label
Authored test batches sent through the real intake ("Prepared example data"), plus one registered Lab run ("Generated test data"). Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s405_provenance_walkthrough.py drop @T`.

### 7. Captured in final run (code `c104f3cc`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| finding-evidence (`w1-ux-02`) | labelled source | Finding Evidence 23 Oct | 10/10 | 11/11 | |
| financials (`w1-ux-02`) | `provenance` (priced, source shown) | Financials 23 Oct | 11/11 | 12/12 | revenue/asset/realised-savings tiles, trade-offs and Scenarios not built |
| financials (`w1-ux-02`) | `withheld` | Financials 24 Oct | 9/9 | 10/10 | as-of reads "time not recorded" |
| evidence (`w1-ux-03`) | labelled source/unknown | `/sites/KOBO-001/evidence` | **not captured by script; now an owner look (section 4)** | **same** | the address is the printed site's route; no invented ID needed |

Totals: `w1-ux-02` 63/63 (30 at 1440, 33 at 390) (`s405-w1-ux-02.txt`). Screenshots: `%TEMP%\w1ux06-final\s405\` (not in git).

## Part 6. Evidence Analysis, what the readings can support (`s302_claim_limit_walkthrough.py`)

Screens: evidence-analysis. Run log: `.agent/W1-UX-06-evidence/s302-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432. Nothing else; `prepare` builds its own copy of the code and data.

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s302_w1ux06","--work","var/s302_w1ux06","--port","9040","--web-port","5540"
.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py @T serve
```
`prepare` takes about 2 minutes and ends with "Prepared. Next: serve." (every line "ok"). `serve` keeps running and prints the addresses (also `links`). The revision ids are new on every prepare: always copy them from the printed list.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9040"; npm.cmd run dev -- --port 5540 --strictPort
```
After looking at the current days, in a third window (same first three lines, then):
```
.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py @T late    # one late reading for 6 Oct; 6 Oct goes out of date
```

### 3. Ports and addresses
API 9040, web 5540. Mock: `http://localhost:5540/mockups/v69/index.html#/evidence-analysis`. All addresses start with `http://localhost:5540/sites/KOBO-001/evidence?view=analysis`.

| Day / state | Address (final run) | Mock |
| --- | --- | --- |
| 6 Oct, full coverage (supported) | ...&day=2026-10-06&revision=60851bad-ed23-4bce-9e77-20b280870b00 | `#/evidence-analysis` |
| 11 Oct, unreliable and conflicting readings (limited) | ...&day=2026-10-11&revision=0fc8c8a5-d77d-4185-8fa8-071c28e6118b | `#/evidence-analysis` |
| 6 Oct after `late` (out of date) | same 6 Oct address, reloaded | `#/evidence-analysis` |

`serve` also prints 8 Oct (missing solar reading), 13 Oct (earlier version, audit only), 15 Oct (out of date), "no assessment selected" and a refused address; not captured in this run.

### 4. What to look for
- 6 Oct: under "What the readings can support", the bold answer says the readings support calling this period of generator operation avoidable for 30 min and every needed reading is present; the line "Using the latest checked readings" with the period and "As of" shows while "Technical details" is closed; every needed reading's bar is fully covered.
- 11 Oct: the bold answer says the conclusion holds "for at most 5 min" and the rest is limited; the bars show striped "unreliable or conflicting" parts for solar power and battery output limit; "What limits it" lists the reasons with times.
- 6 Oct after `late`: the line reads "This result may miss newer readings"; no current conclusion, only what the version said at the time.
- "Open this assessment in Performance > Dispatch" goes to the same day.
- Keyboard: Tab reaches the "Technical details" disclosure. Exact link: paste in a new tab, same day. Reload: same day.

### 5. Data label
Authored test cases sent through the real intake and the real assessment worker (labelled fixture records). Not field readings; times are on a demonstration timeline.

### 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s302_claim_limit_walkthrough.py @T drop`.

### 7. Captured in final run (code `08c81613`)
| Screen | Case | Day | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| evidence-analysis (`w1-ux-03`) | supported | 6 Oct | 10/10 | 10/10 | mock shows records first; app leads with "How each limit is set" and the selected assessment |
| evidence-analysis | limited | 11 Oct | 8/8 | 8/8 | state line reads "Using the latest checked readings" (current, limited tone) |
| evidence-analysis | stale (after `late`) | 6 Oct | 10/10 | 10/10 | records list follows the period filter, not the selected day |

Totals: `w1-ux-03` 36/36 for supported and limited (18 at 1440, 18 at 390) (`s302-w1-ux-03.txt`), stale 20/20 (10 at 1440, 10 at 390) (`s302-w1-ux-03-stale.txt`). Screenshots: `%TEMP%\w1ux06-final\s302\` (not in git). Mock lines are counted with the first case of each run.

## Part 7. Performance > Dispatch and its Analysis (`s3_dispatch_walkthrough.py`)

Screens: dispatch, analysis. Run log: `.agent/W1-UX-06-evidence/s3dispatch-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- The shared producer database `assetops_s3cases` must exist (it is copied, never changed). If `prepare` says it is missing or out of date, run `.venv\Scripts\python.exe tools\s3_dispatch_cases.py run` once (same first two lines as below).
- This tool has no `drop` mode and uses fixed names: database `assetops_s3walk`, work folder `%LOCALAPPDATA%\AssetOps\s3-dispatch-walkthrough`.

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
.venv\Scripts\python.exe tools\s3_dispatch_walkthrough.py prepare
.venv\Scripts\python.exe tools\s3_dispatch_walkthrough.py serve --port 9050
```
`prepare` takes under a minute and ends with "Prepared. Next: serve." `serve` keeps running. It prints web port 5320; this walkthrough uses 5550 instead.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9050"; npm.cmd run dev -- --port 5550 --strictPort
```

### 3. Ports and addresses
API 9050, web 5550. All addresses start with `http://localhost:5550/sites/KOBO-001/performance/dispatch`.

| Day / state | Address | Mock |
| --- | --- | --- |
| 9 Oct, generator needed, partly bounded (limited) | ...?day=2026-10-09 (printed by `serve`) | `http://localhost:5550/mockups/v69/index.html#/dispatch` |
| 2 Oct, possibly avoidable, no limits (supported) | ...?day=2026-10-02 | `#/dispatch` |
| 9 Oct Analysis | ...?day=2026-10-09&revision=e1cb9f3c-0424-4d37-9ba6-0fc3337984e1&view=analysis | `#/analysis` |
| 2 Oct Analysis | ...?day=2026-10-02&revision=5671edfb-6901-4ddf-8026-ab2ec388c045&view=analysis | `#/analysis` |

`serve` prints only the 9 Oct day address. The 2 Oct day address is the printed one with the day changed (the page's day picker gives the same address); the two revision ids are the day's current result as the served API reports it (`http://127.0.0.1:9050/api/sites/KOBO-001/performance/dispatch/windows/<day>`, first interval `id`). They stay the same on every `prepare` while `assetops_s3cases` is unchanged; on the page, "Open Dispatch > Analysis" reaches the same view. Day picker: 5 Oct shows "out of date" and 7 Oct shows "failed" (staged by this tool).

### 4. What to look for
- 9 Oct: the bold answer "The generator operated for at least 7 h 30 min: 0 min possibly avoidable, 7 h 30 min needed and 0 min that cannot be determined."; the line "Using the latest checked readings" with the day and "As of" while "How this was worked out" is closed; the 15-minute block strip and four totals; "What limits this day's result: A generator period is only partly bounded by the records."
- 2 Oct: "The generator operated for 5 h 30 min to 6 h: 4 h possibly avoidable, 1 h 30 min needed and 0 min that cannot be determined."; "What limits this day's result" says no limitation is recorded.
- Analysis: how the readings lead to each outcome for the selected result, with the same state line; the constraint table scrolls inside its card on a phone.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same day. Reload: same day.

### 5. Data label
Generated test data (registered simulator runs through the real intake, `s3-dispatch-cases-v1`) plus two clearly labelled fault fixtures. Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows, then:
```
docker exec assetopsv1-postgres-1 dropdb -U assetops assetops_s3walk
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\AssetOps\s3-dispatch-walkthrough"
```
Leave `assetops_s3cases` (shared producer).

### 7. Captured in final run (code `bf76f7ff`)
| Screen | Case | Day | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| dispatch (`w1-ux-03`) | limited | 9 Oct | 10/10 | 10/10 | mock has a PV/load/generator kW chart; app has the block strip and totals (no kW series in the read) |
| dispatch | supported | 2 Oct | 8/8 | 8/8 | full records and 12-row coverage tables make the page long |
| analysis (`w1-ux-03`) | limited | 9 Oct | 10/10 | 10/10 | mock `#/analysis` is a Finding Analysis; only section names align |
| analysis | supported | 2 Oct | 8/8 | 8/8 | |

Totals: `w1-ux-03` 72/72 (36 at 1440, 36 at 390) (`s3dispatch-w1-ux-03.txt`). Screenshots: `%TEMP%\w1ux06-final\s3dispatch\` (not in git). Mock lines are counted with the first case of each screen.

## Part 8. One Finding, out of date, and its history (`s4_finding_walkthrough.py`)

Screens: finding, finding-history. Run log: `.agent/W1-UX-06-evidence/s4_finding-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` present in this folder (see "Before you start", step 4) (`var/` is ignored by git).
- The shared case database `assetops_s4cases` must exist. If it does not, build it once (about 10 minutes): `.venv\Scripts\python.exe tools\s4_finding_cases.py run` (same env lines as below). The final run used the existing copy.

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s4walk_w1ux06","--work","var/s4walk_w1ux06"
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T links --web-port 5496
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T serve --port 8996 --web-port 5496
```
`prepare` takes about a minute and ends with "Prepared. Next: links, then serve." `links` prints every Finding address (they change only when `assetops_s4cases` is rebuilt).
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="8996"; npm.cmd run dev -- --port 5496 --strictPort
```
Optional, after looking: `.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T recover` makes the out-of-date Finding current again.

### 3. Ports and addresses
API 8996, web 5496. Mocks: `http://localhost:5496/mockups/v69/index.html#/finding` and `#/finding-history`.

| Screen | Address (from `links`) | Mock |
| --- | --- | --- |
| F01 open Finding (6 Oct) | http://localhost:5496/sites/KOBO-001/findings/937ffdef-a923-4f7b-b204-98fa61ce1058 | `#/finding` |
| F02 cross-midnight, out of date | http://localhost:5496/sites/KOBO-001/findings/ff2c2005-ec4f-413b-86f8-1fa8c8e6bce8 | `#/finding` |
| F01 history at version 1 | http://localhost:5496/sites/KOBO-001/findings/937ffdef-a923-4f7b-b204-98fa61ce1058/history?revision_id=b6af6f73-9be7-4a45-b729-86db1d3e2d92 | `#/finding-history` |

### 4. What to look for
- F01: the bold answer says what was found and when; the green line "Using the latest checked readings" shows the site and "As of" while "How this was worked out" is closed; a small picture of the episode; links "Open the recommendation" and "See how this conclusion was reached".
- F02: "This result may miss newer readings" (a newer record is waiting to be checked); the recorded version stays visible.
- History: "Earlier version, kept for the record", with the version timeline and links "Select the latest version", "Open version 1 of the Finding" and "Open version 1's evidence".
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same Finding and version. Reload: same page.

### 5. Data label
Authored test cases sent through the real intake (labelled fixture batches, `s4-finding-cases-v1`). The out-of-date state on 9 Oct is staged in the walkthrough copy only. Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T drop` (leaves `assetops_s4cases` alone).

### 7. Captured in final run (code `5f2fac28`)
| Screen | Case | Address (localhost:5496) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| finding (`w1-ux-02`) | F01 open | /sites/KOBO-001/findings/937ffdef-... | pass | pass | priority/confidence chips not built |
| finding | stale (F02) | /findings/ff2c2005-... | pass | pass | |
| finding-history | F01 version 1 | /findings/937ffdef-.../history?revision_id=b6af6f73-... | pass | pass | |

Totals: `w1-ux-02` 59/59 (28 at 1440, 31 at 390; `s4_finding-w1-ux-02.txt`). Screenshots: `%TEMP%\w1ux06-final\s4_finding\ux02` (not in git).

## Part 9. Site Findings list (`s404_finding_index_walkthrough.py`)

Screens: sitefindings. Run log: `.agent/W1-UX-06-evidence/s404-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` present in this folder (see "Before you start", step 4) (`var/` is ignored by git).

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s404_owner_w1ux06","--work","var/s404_owner_w1ux06","--api-port","8993","--web-port","5493","--tls-port","8994","--http-port","8995"
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py prepare @T
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py serve @T
```
`prepare` takes about 2 minutes and must end with "0 failed check(s)". `serve` prints the addresses.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="8993"; npm.cmd run dev -- --port 5493 --strictPort
```
After looking at every day, in a third window (same first two lines as above, then `$T=...`):
```
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py late @T      # late readings for 15 Oct, not yet assessed
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py settle @T    # assess them; 15 Oct is current again
```
This tool serves only the Site Findings list; the site's day Overview stays closed here (use the s502 walkthrough for it).

### 3. Ports and addresses
API 8993, web 5493. Mock: `http://localhost:5493/mockups/v69/index.html#/sitefindings`. All addresses start with `http://localhost:5493/sites/KOBO-001/findings?` and end with `&domain=mini-grid-dispatch`.

| Day / state | Address | Mock |
| --- | --- | --- |
| 15 Oct, Findings listed | http://localhost:5493/sites/KOBO-001/findings?from=2026-10-15T00%3A00%3A00Z&to=2026-10-16T00%3A00%3A00Z&domain=mini-grid-dispatch | `#/sitefindings` |
| 15 Oct, 2 per page | same as above plus `&limit=2` | `#/sitefindings` |
| 25 Oct, checked and none found | ...from=2026-10-25T00%3A00%3A00Z&to=2026-10-26T00%3A00%3A00Z... | `#/sitefindings` |
| 27 Oct, out of date | ...from=2026-10-27T00%3A00%3A00Z&to=2026-10-28T00%3A00%3A00Z... | `#/sitefindings` |
| 5 Nov, check failed | ...from=2026-11-05T00%3A00%3A00Z&to=2026-11-06T00%3A00%3A00Z... | `#/sitefindings` |
| 30 Oct, not assessed | ...from=2026-10-30T00%3A00%3A00Z&to=2026-10-31T00%3A00%3A00Z... | `#/sitefindings` |

### 4. What to look for
- 15 Oct: the bold answer is about the Findings for the day; the green line "Using the latest checked readings" shows the site, the day and "As of" while "How this was worked out" is closed; a small day strip; each row opens its Finding.
- 2 per page: two rows and a "Next page" link.
- 25 Oct: "Checked: nothing to report" - a proved zero, not a missing answer.
- 27 Oct: "This result may miss newer readings". 5 Nov: "The latest check could not be completed". 30 Oct: "We have not checked this period". None of these shows rows or a count.
- After `late`: 15 Oct says "This result may miss newer readings". After `settle`: back to "Using the latest checked readings".
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same day. Reload: same day.

### 5. Data label
Authored test cases sent through the real intake (labelled fixture batches). Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py drop @T`.

### 7. Captured in final run (code `bc3ef4c7`)
| Screen | Case | Day | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| sitefindings (`w1-ux-02`) | positive | 15 Oct | pass | pass | lens chips, priority/confidence/domain columns not built |
| sitefindings | empty (proved zero) | 25 Oct | pass | pass | |
| sitefindings | dirty (stale) | 27 Oct | pass | pass | |
| sitefindings | failed | 5 Nov | pass | pass | as-of reads "time not recorded" |
| sitefindings | unassessed | 30 Oct | pass | pass | as-of reads "time not recorded" |
| sitefindings | 2 per page (tag `page2`) | 15 Oct | pass | pass | |
| sitefindings | late (after `late`) | 15 Oct | 10/10 | 11/11 | |
| sitefindings | settled (after `settle`) | 15 Oct | 10/10 | 11/11 | |

Totals: `w1-ux-02` 106/106 for the six days (50 at 1440, 56 at 390), late 21/21, settled 21/21 (`s404-w1-ux-02*.txt`). Screenshots: `%TEMP%\w1ux06-final\s404\` (not in git).

## Part 10. Financials fuel cost states (`s402b_fuel_cost_walkthrough.py`)

Screens: financials. Run log: `.agent/W1-UX-06-evidence/s402b-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- A fresh `assetops_s402bcases` template (about 2.5 minutes; it must end with "VERIFY PASSED"). The old template was stale, so rebuild it before the first walkthrough:
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
.venv\Scripts\python.exe tools\s402b_power_cases.py --tls-port 9062 --http-port 9063 run
```

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$A="--db","assetops_s402bwalk_w1ux06","--empty-db","assetops_s402bempty_w1ux06","--work-name","s402b-w1ux06"
.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A prepare
.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A links --web-port 5560 --empty-web-port 5561
.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A serve --port 9060 --empty-port 9061 --web-port 5560 --empty-web-port 5561
```
`prepare` takes about 1 minute and ends with "Prepared. Next: links, then serve." The ids are new on every prepare, so always copy addresses from `links`. `serve` runs two APIs (priced store 9060, empty-price store 9061) until Ctrl+C.
Second and third windows:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9060"; npm.cmd run dev -- --port 5560 --strictPort
```
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9061"; npm.cmd run dev -- --port 5561 --strictPort
```
For the "no price recorded" state, after looking at the empty-price store once, run (first window, `serve` may keep running):
```
.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A recompute --empty
```

### 3. Ports and addresses
APIs 9060 / 9061, web 5560 / 5561. From the final run (`<P>` = `finding_id=0e95ad69-759b-4c45-92e9-222146268f54&revision_id=565111ca-4bfa-44d0-bf48-05bb9525fe3b`):

| Screen / state | Address | Mock |
| --- | --- | --- |
| Financials, P01 (23 Oct), priced | http://localhost:5560/sites/KOBO-001/financials?<P> | `http://localhost:5560/mockups/v69/index.html#/financials` |
| Financials, F01 gateway (2 Oct), not calculated | http://localhost:5560/sites/KOBO-001/financials?finding_id=81b63e65-b87a-4d2b-a4dd-7819ef2dcf9f&revision_id=fcd0a325-d68a-4bc9-8898-ac880a4df7d1 | `#/financials` |
| Financials, P01 in the empty-price store, before `recompute --empty` | http://localhost:5561/sites/KOBO-001/financials?<P> | `#/financials` |
| Same address after `recompute --empty` (no price) | http://localhost:5561/sites/KOBO-001/financials?<P> | `#/financials` |

`links` also prints the Assumptions page, the price versions, exact fuel cost versions and an earlier Finding version; those were not captured here (Assumptions is covered by s402a and s408).

### 4. What to look for
- Priced: a money range with "Modelled range, using the latest checked readings" and an "As of" time, while "How this was worked out" is closed; a small chart; links to the Evidence and back to the Finding.
- Not calculated: "Not calculated: no fuel amount, so no cost" - no number, because the power readings cover too little of the time. "As of: time not recorded".
- Empty-price store before recompute: "No current amount can be shown" (not worked out yet). After `recompute --empty`: "No price recorded". Both say "As of: time not recorded" and show no number.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same page. Reload: same page.

### 5. Data label
Authored power demonstration batch (P01) and an ordinary Lab gateway run (F01), sent through the real intake; diesel prices are the SYSTEM demonstration fixture. Not field readings.

### 6. Stop and clean up
Ctrl+C in all three windows, then `.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A drop`. Keep `assetops_s402bcases` (shared template).

### 7. Captured in final run (code `0a4da463`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| financials (`w1-ux-02`) | priced | P01, web 5560 | 11/11 | 12/12 | revenue/asset/realised-savings tiles, trade-offs and Scenarios not built |
| financials (`w1-ux-02`) | `notcalculated` | F01 gateway, web 5560 | 9/9 | 10/10 | as-of reads "time not recorded" |
| financials (`w1-ux-02`) | `notworkedout` (empty store, before recompute) | P01, web 5561 | 9/9 | 10/10 | as-of reads "time not recorded" |
| financials (`w1-ux-02`) | `emptyprice` (after `recompute --empty`) | P01, web 5561 | 11/11 | 12/12 | as-of reads "time not recorded" |

Totals: `w1-ux-02` 84/84 (40 at 1440, 44 at 390) (`s402b-w1-ux-02.txt` 61/61, `s402b-w1-ux-02-emptyprice.txt` 23/23). Screenshots: `%TEMP%\w1ux06-final\s402b\` (not in git).

## Part 11. Financials > Assumptions, the site diesel price (`s402a_assumptions_walkthrough.py`)

Screens: assumptions. Run log: `.agent/W1-UX-06-evidence/s402a-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- The shared `assetops_s4cases` Finding template (`tools/s4_finding_cases.py run`, which needs `var/sites/kobo-001.yaml` present). It was already present for this run.

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$A="--db","assetops_s402awalk_w1ux06","--empty-db","assetops_s402aempty_w1ux06","--work-name","s402a-w1ux06"
.venv\Scripts\python.exe tools\s402a_assumptions_walkthrough.py @A prepare
.venv\Scripts\python.exe tools\s402a_assumptions_walkthrough.py @A links --web-port 5560 --empty-web-port 5561
.venv\Scripts\python.exe tools\s402a_assumptions_walkthrough.py @A serve --port 9060 --empty-port 9061
```
`prepare` takes about 2 minutes and ends with "Prepared. Next: links, then serve." (it prints that twice). Always copy addresses from `links`. `serve` runs two APIs (priced 9060, empty-price 9061) until Ctrl+C.
Second and third windows:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9060"; npm.cmd run dev -- --port 5560 --strictPort
```
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9061"; npm.cmd run dev -- --port 5561 --strictPort
```

### 3. Ports and addresses
APIs 9060 / 9061, web 5560 / 5561.

| Screen / state | Address | Mock |
| --- | --- | --- |
| Assumptions, price in effect | http://localhost:5560/sites/KOBO-001/financials/assumptions | `http://localhost:5560/mockups/v69/index.html#/assumptions` |
| Assumptions, empty-price store (no price) | http://localhost:5561/sites/KOBO-001/financials/assumptions | `#/assumptions` |

`links` also prints each price version (`?revision_id=...`), "Prices as recorded then" (`?recorded_at=...`) and three Findings' money views; not captured here (recorded-time history is covered by s408).

### 4. What to look for
- Price in effect: the bold answer gives the diesel price now in effect, with "Price recorded for this site" and an "As of" time while "How this was worked out" is closed; a small price strip; a link "See every recorded price version". "Edit price" is shown but cannot be used.
- Empty-price store: "No price recorded", no number.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same page. Reload: same page.

### 5. Data label
SYSTEM demonstration diesel price fixture (v1 initial, v2 succession, v3 correction) over the authored S4 Finding cases. Not field readings.

### 6. Stop and clean up
Ctrl+C in all three windows, then `.venv\Scripts\python.exe tools\s402a_assumptions_walkthrough.py @A drop`.

### 7. Captured in final run (code `26636869`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| assumptions (`w1-ux-02`) | price in effect | web 5560 | 10/10 | 11/11 | editable Assumptions with an impact preview not built ("Edit price" disabled) |
| assumptions (`w1-ux-02`) | `emptyprice` (extra case) | web 5561 | 7/8 | 8/9 | **FAIL** "the card has a small visual" at both widths: the no-price state draws no price strip |

Totals: `w1-ux-02` 36/38 (17/18 at 1440, 19/20 at 390) (`s402a-w1-ux-02.txt`); the required effective-price case is 21/21. Screenshots: `%TEMP%\w1ux06-final\s402a\` (not in git).

## Part 12. Assumptions price and fuel cost history (`s408_assumption_history_walkthrough.py`, owner and mixed cases)

Screens: assumptions: S4-08 fuel-price history. Run log: `.agent/W1-UX-06-evidence/s408-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` present in this folder (see "Before you start", step 4) (`var/` is ignored by git).

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--suffix","_w1ux06","--api-port","9060","--web-port","5560","--tls-port","9061","--http-port","9062"
.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py prepare @T
.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py links @T
.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py serve --case owner @T
```
`prepare` takes about 3.5 minutes and must end with "0 failed checks". The recorded moments T1/T2/T3 are new on every prepare, so always copy addresses from `links`. `serve` keeps running until Ctrl+C.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9060"; npm.cmd run dev -- --port 5560 --strictPort
```
Closed source: Ctrl+C `serve`, then `... close-gate @T`, `... serve --case owner @T`, reload; afterwards Ctrl+C and `... open-gate @T`.
Mixed source: Ctrl+C `serve`, then `... serve --case mixed @T` and reload the default address.

### 3. Ports and addresses
API 9060, web 5560. From the final run (`<A>` = `http://localhost:5560/sites/KOBO-001/financials/assumptions`):

| Screen / state | Address | Mock |
| --- | --- | --- |
| Assumptions + history, default (owner) | `<A>` | `http://localhost:5560/mockups/v69/index.html#/assumptions` |
| Recorded at T1, before the October price change | `<A>?recorded_at=2026-10-17T01%3A29%3A19.770015%2B00%3A00` | `#/assumptions` |
| Recorded at T3, after the part-way correction | `<A>?recorded_at=2026-10-17T01%3A29%3A43.163510%2B00%3A00` | `#/assumptions` |
| Second history page at T3 | the "Second page at T3" address printed by `links` (long) | - |
| Closed source (after `close-gate`) | `<A>` | `#/assumptions` |
| Mixed source (`serve --case mixed`) | `<A>` | `#/assumptions` |

The fuel cost version's own Financials page was reached by clicking its link in the history (the evidence script does this).

### 4. What to look for
- Default: the price now in effect ("Price recorded for this site", "As of" time) while "How this was worked out" is closed; a price strip; under "Interpretation history" the latest and earlier fuel cost versions, each recorded amount labelled as history beside its source; a plain sentence where only the price changed; one version with no amount (unpriced).
- T1 / T3: "Prices as recorded at an earlier moment"; the prices and the history are for the same moment; the address keeps `recorded_at` after reload.
- Closed source: every version is listed without an amount, and the page says the source is closed. Mixed source: every recorded amount is withheld ("Sources do not agree").
- Keyboard: Tab reaches "How this was worked out". Exact link: a history version opens that Finding's Financials at that exact version. Reload: same page, same moment.

### 5. Data label
Authored batches sent through the real intake ("Prepared example data") and the SYSTEM demonstration price fixture with extra authored price corrections. Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows (run `open-gate` first if the gate is closed), then `.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py drop @T`.

### 7. Captured in final run (code `f4da5ec4`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| assumptions (`w1-ux-02`) | owner default | `<A>` | 10/10 | 11/11 | editable Assumptions with impact preview not built |
| assumptions (`w1-ux-02`) | `historyT1` | T1 | 8/8 | 9/9 | |
| assumptions (`w1-ux-02`) | `historyT3` | T3 | 8/8 | 9/9 | |
| assumptions (`w1-ux-02`) | `closed` | `<A>` after close-gate | 10/10 | 11/11 | the price card itself still shows the price |
| assumptions (`w1-ux-02`) | `mixed` | `<A>`, mixed case | 10/10 | 11/11 | the price card itself still shows the price |
| S4-08 history (`s408-assumption-history-evidence`) | owner: default, T1/T3 reload, next page, exact version link | as above | 30/30 | 30/30 | |
| S4-08 history | closed | `<A>` after close-gate | 9/9 | 9/9 | |
| S4-08 history | mixed | `<A>`, mixed case | 9/9 | 9/9 | |
| S4-08 history | missing source | - | **not run** | **not run** | the tool has no missing-source case (only owner, mixed, closed) |

Totals: `w1-ux-02` 97/97 (`s408-w1-ux-02.txt` 55/55, `-closed` 21/21, `-mixed` 21/21); S4-08 96/96 (`s408-s408-owner.txt` 60/60, `-closed` 18/18, `-mixed` 18/18). The source label is checked beside each recorded amount on load; the reload checks cover the moment (`recorded_at`) and price list, not the label text. Screenshots: `%TEMP%\w1ux06-final\s408\` (not in git).

## Part 13. Recommendation, Action and Foundation change (`s601b_action_walkthrough.py`)

Screens: recommendation, changes, action-overview, action-execution, action-history. Run log: `.agent/W1-UX-06-evidence/s601b-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- Nothing else: `prepare` builds its own copy of the code and data.

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s601b_w1ux06","--work","var/s601b_w1ux06"
.venv\Scripts\python.exe tools\s601b_action_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s601b_action_walkthrough.py @T links
.venv\Scripts\python.exe tools\s601b_action_walkthrough.py @T serve
```
`prepare` takes about a minute and ends with "Prepared. Next: links, then serve." `links` prints every address below. The ports are fixed by the tool.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="8961"; npm.cmd run dev -- --port 5461 --strictPort
```

### 3. Ports and addresses
API 8961, web 5461. Mock: `http://localhost:5461/mockups/v69/index.html#/<id>`. The IDs below were printed by `links` in the final run; a fresh `prepare` prints new ones, so use the ones your `links` prints.

| Screen and state | Address | Mock |
| --- | --- | --- |
| Recommendation, accepted (version it was made on) | http://localhost:5461/sites/KOBO-001/findings/0c8dff18-e4e3-4856-99ce-d8ef125fa27f/recommendation?revision_id=507d5dd0-1bb1-4e19-acd2-afd05dd58b1b | `#/recommendation` |
| Recommendation, latest version (held: earlier trial still open) | http://localhost:5461/sites/KOBO-001/findings/0c8dff18-e4e3-4856-99ce-d8ef125fa27f/recommendation | `#/recommendation` |
| Recommendation, unavailable (second Finding) | http://localhost:5461/sites/KOBO-001/findings/4546dd78-4a7b-4599-8c19-a2378fae1616/recommendation | `#/recommendation` |
| The change (applied setting) | http://localhost:5461/sites/KOBO-001/foundation/changes/09f35a1c-4ff2-4b2b-b1f0-de2255f918cf | `#/changes` |
| Action overview, recorded | http://localhost:5461/sites/KOBO-001/actions/8b26e88e-a066-485c-b6a6-3c9542596c3a | `#/action-overview` |
| Action overview, still pending (not printed; open the printed "second Action" address and click the "Action" breadcrumb) | http://localhost:5461/sites/KOBO-001/actions/5f8bf165-7da6-412b-a0bc-42d6c0a1934e | `#/action-overview` |
| Application, applied | http://localhost:5461/sites/KOBO-001/actions/8b26e88e-a066-485c-b6a6-3c9542596c3a/execution | `#/action-execution` |
| Application, an attempt failed, still pending | http://localhost:5461/sites/KOBO-001/actions/5f8bf165-7da6-412b-a0bc-42d6c0a1934e/execution | `#/action-execution` |
| History, every event | http://localhost:5461/sites/KOBO-001/actions/8b26e88e-a066-485c-b6a6-3c9542596c3a/history | `#/action-history` |
| History at APPLIED | http://localhost:5461/sites/KOBO-001/actions/8b26e88e-a066-485c-b6a6-3c9542596c3a/history?event_id=d95e4f80-6d14-4a32-9992-1662eb4dc9d9 | `#/action-history` |
| History at OBSERVED | http://localhost:5461/sites/KOBO-001/actions/8b26e88e-a066-485c-b6a6-3c9542596c3a/history?event_id=484f9ef8-c65b-44a5-a893-5c9ac7d12778 | `#/action-history` |

### 4. What to look for
- Recommendation, accepted: the box reads "Accepted; result not yet known" with "As of 1 Nov 2026, 00:00 UTC" while "How this was worked out" is closed. Links "Open the Action" and "Open Verification" are there.
- Recommendation, latest and unavailable: the box reads "Held: an earlier trial is still open". These two have no small picture.
- The change: "Setting changed; effect judged separately", with the date and time.
- Action overview (both): "No trial plan yet".
- Application: applied shows "Applied; effect not yet measured"; the second Action shows "Not applied yet; an attempt failed".
- History: the full list shows "Every recorded event"; an event address shows "Earlier version, kept for the record" and the time of that event.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same screen and state. Reload: same screen and state.

### 5. Data label
Generated demonstration records (test cases F01/F02 run through the real Action screens' service). Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows, then:
```
.venv\Scripts\python.exe tools\s601b_action_walkthrough.py @T drop
```

### 7. Captured in final run (code `1d1fcc8e`)
| Screen | Case | Address (localhost:5461) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| recommendation | accepted | /findings/0c8d.../recommendation?revision_id=507d... | pass | pass | |
| recommendation | latest (held) | /findings/0c8d.../recommendation | 1 FAIL: no small visual | 1 FAIL: no small visual | held state draws no picture |
| recommendation | unavailable | /findings/4546.../recommendation | 1 FAIL: no small visual | 1 FAIL: no small visual | label reads "Held: an earlier trial is still open", not an "unavailable" wording |
| changes | applied | /foundation/changes/09f3... | pass | pass | title "The change" (guard forbids mock name) |
| action-overview | recorded / pending (pending reached by click) | /actions/8b26... , /actions/5f8b... | pass | pass | |
| action-execution | applied / failed | .../execution | pass | pass | |
| action-history | all / APPLIED / OBSERVED events | .../history[?event_id=] | pass | pass | |

Total `w1-ux-01`: 192/196 (`s601b-w1-ux-01.txt`), default `W1_NO_VISUAL_OK` (mini only). Screenshots: `%TEMP%\w1ux06-final\s601b` (not in git).

## Part 14. Action Plan, Evidence and Verification (`s602b_verification_walkthrough.py`)

Screens: action-plan, action-evidence, verification. Run log: `.agent/W1-UX-06-evidence/s602b-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432. Nothing else: `prepare` builds its own code copy and data.

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s602b_w1ux06","--work","var/s602b_w1ux06"
.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py @T links --web-port 5570
.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py @T serve --port 9070 --web-port 5570 --case guardrail
```
`prepare` takes about 5 minutes and ends with "Prepared. Next: serve, then capture." It makes five databases (the replay plus one per test case). To see another test case, Ctrl+C `serve` and start it again with `--case target_miss`, `--case inconclusive` or `--case withdrawn`; the two web windows keep running.
Second window (the replay, a real Lab run):
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9070"; npm.cmd run dev -- --port 5570 --strictPort
```
Third window (the test cases):
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9071"; npm.cmd run dev -- --port 5571 --strictPort
```

### 3. Ports and addresses
API 9070 and 9071, web 5570 (replay) and 5571 (test case). Mock: `http://localhost:5570/mockups/v69/index.html#/<id>`. IDs are from the final run's `links`; a fresh `prepare` prints new ones. Plan and Evidence addresses for the test cases are not printed: open the printed Verification address and click the "Plan" or the second "Evidence" tab (the Action's tab row, not the Site menu).

| Screen and state | Address | Mock |
| --- | --- | --- |
| Plan, sampled pass (current / exact) | http://localhost:5570/sites/KOBO-001/actions/f89ba10f-aecf-4213-a6eb-b6fb3f554783/plan , ...plan?plan_revision_id=10b2966b-80c3-4af3-ba45-84cc0faf3114 | `#/action-plan` |
| Evidence, sampled pass | http://localhost:5570/sites/KOBO-001/actions/f89ba10f-aecf-4213-a6eb-b6fb3f554783/evidence | `#/action-evidence` |
| Verification, sampled pass (current / exact outcome) | http://localhost:5570/sites/KOBO-001/actions/f89ba10f-aecf-4213-a6eb-b6fb3f554783/verification , ...verification?outcome_id=34ca961a-069f-405b-8e91-56608edbf9b7 | `#/verification` |
| Guardrail fail (`--case guardrail`) | http://localhost:5571/sites/KOBO-001/actions/93ebef0d-48b9-43ff-8d06-b9ba718b4d2b/verification (+ /plan, /evidence by click) | `#/verification` |
| Withdrawn (`--case withdrawn`) | http://localhost:5571/sites/KOBO-001/actions/38da3f33-8441-454a-bcd0-c2af0981d28c/verification (+ /plan, /evidence by click); hold: http://localhost:5571/sites/KOBO-001/findings/9897b026-68da-432c-880b-81ad1968d83c/recommendation?revision_id=9c825cb0-002a-4fdb-bba8-55e9351f0b28 | `#/verification`, `#/recommendation` |
| Target not met (`--case target_miss`) | http://localhost:5571/sites/KOBO-001/actions/3095d875-6c62-4283-80f6-f3c16a655cfd/verification (+ /plan, /evidence by click) | `#/verification` |
| Could not conclude (`--case inconclusive`) | http://localhost:5571/sites/KOBO-001/actions/da220af2-0504-49bd-920f-c2b989c48e8e/verification (+ /plan, /evidence by click) | `#/verification` |

### 4. What to look for
- Plan (all cases): "Plan fixed before the later readings" with its date, while "How this was worked out" is closed.
- Evidence: sampled pass, guardrail and target miss say "Both windows have their readings"; withdrawn says "Some readings are missing".
- Verification: sampled pass "Target met within the sampled limits"; exact outcome "Earlier version, kept for the record"; guardrail "Trial missed a safety or service limit"; target miss "Target not met"; withdrawn and inconclusive "Could not conclude".
- Withdrawn hold: the recommendation says "Held: late evidence withdrew an earlier trial's result" (no small picture).
- Inconclusive Evidence says "Some readings are missing" (the earlier blank page was fixed in `2d03f626`).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same state. Reload: same state.

### 5. Data label
Sampled pass: simulated readings from two real Lab runs, replayed. The four other cases are authored test examples, not Lab runs. None are field readings.

### 6. Stop and clean up
Ctrl+C in all three windows, then:
```
.venv\Scripts\python.exe tools\s602b_verification_walkthrough.py @T drop
```

### 7. Captured in final run (code `01bdfd9c`)
| Screen | Case | 1440 | 390 | App vs mock / notes |
| --- | --- | --- | --- | --- |
| action-plan | pass, pass exact, guardrail, withdrawn, target_miss, inconclusive | pass | pass | test-case Plan reached by click |
| action-evidence | pass, guardrail, withdrawn, target_miss | pass | pass | |
| action-evidence | inconclusive | rerun at `2d03f626`: pass ("Some readings are missing") | pass (same) | superseded: the `01bdfd9c` run failed 2 + 2 (page crashed: "Objects are not valid as a React child (found: object with keys {code, accepted_evidence_ids})" in `Ref` under `WindowPanel` > `DigDeeper`, `SiteActionVerification.tsx`); fixed by `2d03f626` |
| verification | pass, pass historical, guardrail, withdrawn, target_miss, inconclusive | pass | pass | inconclusive Plan and Verification also re-passed in the `2d03f626` rerun |
| recommendation | withdrawn hold | 1 FAIL: no small visual | 1 FAIL (same) | held state draws no picture |

`w1-ux-01` totals: replay + guardrail 140/140, withdrawn 78/80, target_miss 60/60, inconclusive 42/46 (files `s602b-w1-ux-01-*.txt`), 320/326 overall at `01bdfd9c`. Inconclusive rerun at `2d03f626` (fresh `prepare`, `serve --case inconclusive`, Action `50c7912f-20b2-4786-9c18-aa6b245497c7`): 60/60 (30/30 at 1440, 30/30 at 390; `s602b-w1-ux-01-inconclusive-rerun.txt`), superseding the 42/46; overall with the rerun 338/340. Tool's own `capture` (`s602b-verification-evidence.mjs`, replay and every case): 120/120 (`s602b-capture.txt`). Screenshots: `%TEMP%\w1ux06-final\s602b` (not in git).

## Part 15. Site > Work > Actions (`s603_site_work_walkthrough.py`)

Screens: sitework. Run log: `.agent/W1-UX-06-evidence/s603-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432. Nothing else: `prepare` builds its own code copy and data.

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s603_owner_w1ux06","--work","var/s603_owner_w1ux06"
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py @T serve --port 9070 --web-port 5570
```
`prepare` takes about a minute and ends with "Prepared. Next: serve ...". `serve` prints the addresses below.
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="9070"; npm.cmd run dev -- --port 5570 --strictPort
```
Optional third window, to confirm the counts against the database (must end "ATTEST OK"):
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s603_owner_w1ux06","--work","var/s603_owner_w1ux06"
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py @T attest
```

### 3. Ports and addresses
API 9070, web 5570. Mock: `http://localhost:5570/mockups/v69/index.html#/sitework`.

| State | Address | Mock |
| --- | --- | --- |
| Active (two Actions on 1 Nov 2026) | http://localhost:5570/sites/KOBO-001/work?from=2026-11-01T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z | `#/sitework` |
| Same, one per page (Next page) | http://localhost:5570/sites/KOBO-001/work?from=2026-11-01T00%3A00%3A00Z&to=2026-11-02T00%3A00%3A00Z&limit=1 | `#/sitework` |
| Proved zero (October) | http://localhost:5570/sites/KOBO-001/work?from=2026-10-01T00%3A00%3A00Z&to=2026-11-01T00%3A00%3A00Z | `#/sitework` |
| No window chosen (also printed) | http://localhost:5570/sites/KOBO-001/work | `#/sitework` |

### 4. What to look for
- Active: the box reads "Every Action created here in this window" with "As of" and the time, while "How this was worked out" is closed. Rows ACT-000002 and ACT-000001 are listed; each opens its Action.
- One per page: one row and a Next page link.
- Proved zero: the box reads "Checked: nothing to report". There is no small picture in this state.
- No window chosen: the page asks you to choose a window; no answer box (by design).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same window. Reload: same window.

### 5. Data label
Generated demonstration records (test cases run through the real Action service). Not field readings. The "As of" time is the time you look, because the list is read live.

### 6. Stop and clean up
Ctrl+C in both windows, then:
```
.venv\Scripts\python.exe tools\s603_site_work_walkthrough.py @T drop
```

### 7. Captured in final run (code `9517eb8e`; `attest` printed ATTEST OK, `s603-attest.txt`)
| Screen | Case | Address (localhost:5570) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| sitework | active | /sites/KOBO-001/work?from=2026-11-01...&to=2026-11-02... | pass | pass | |
| sitework | paged | as above + &limit=1 | pass | pass | |
| sitework | proved zero | ?from=2026-10-01...&to=2026-11-01... | 1 FAIL: no small visual | 1 FAIL: no small visual | zero state draws no picture |
| sitework | no window | /sites/KOBO-001/work | not run | not run | no card by design |

Total `w1-ux-01`: 50/52 (`s603-w1-ux-01.txt`), default `W1_NO_VISUAL_OK` (mini only). Screenshots: `%TEMP%\w1ux06-final\s603` (not in git).

## Part 16. Health and battery (`s701_health_walkthrough.py`)

Screens: health, asset. Run log: `.agent/W1-UX-06-evidence/s701-*.txt`.

### 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` present in this folder (see "Before you start", step 4) (`var/` is ignored by git).

### 2. Commands (PowerShell, in order)
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s701_owner_w1ux06","--work","var/s701_owner_w1ux06"
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T serve --port 8970 --web-port 5470
```
Second window:
```
cd $wt\frontend; $env:ASSETOPS_API_PORT="8970"; npm.cmd run dev -- --port 5470 --strictPort
```
Third window, once the API is up (prints the battery address), then right before looking (fresh contacts last about 2 minutes), then the self-check:
```
cd $wt
$env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s701_owner_w1ux06","--work","var/s701_owner_w1ux06"
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T links --port 8970 --web-port 5470
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T deliver
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T attest --port 8970
```
`attest` should end with `attest: ok`.

### 3. Ports and addresses
API 8970, web 5470. The tool prints `127.0.0.1`; open the same port and path on `localhost`. Mock: `http://localhost:5470/mockups/v69/index.html#/<id>`.

| Screen | Address | Mock |
| --- | --- | --- |
| Health, KOBO-001 | http://localhost:5470/sites/KOBO-001/health | `#/health` |
| Health, KOBO-002 (no gateway) | http://localhost:5470/sites/KOBO-002/health | `#/health` |
| Battery, KOBO-001 | http://localhost:5470/sites/KOBO-001/assets/<id printed by links> (this run `61e5e895-c41a-4ef4-b3e8-6df022af4053`; it changes every prepare) | `#/asset` |
| Battery refusal | http://localhost:5470/sites/KOBO-002/assets/00000000-0000-4000-8000-000000000000 | `#/asset` |

### 4. What to look for
- Health KOBO-001: the bold answer reads "4 of 8 enabled gateways need attention"; the yellow box says some gateways are not in contact, with site and "As of" time, while "How this was worked out" is closed.
- Two bar groups: contact (in contact / out of contact / never heard) and how old the reports are. "What to do" links open each gateway. Click one of those links: on the selected-gateway view, look for "In contact; its latest report is old" where the data shows it (and "...age cannot be confirmed" where a report time is missing).
- The battery link goes to the battery page.
- KOBO-002: says there is no gateway to read from, with no empty bars pretending to be zero.
- Battery: says its condition cannot be judged yet and lists the missing inputs.
- Refusal address: a plain refusal panel (no card).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same view. Reload: same view (after about 2 minutes, contacts turn old; run `deliver` again).

### 5. Data label
Generated test data: eight test gateways on KOBO-001 with made-up reports; KOBO-002 has no enabled gateway. Not field readings.

### 6. Stop and clean up
Ctrl+C in both windows, then:
```
.venv\Scripts\python.exe tools\s701_health_walkthrough.py @T drop
```

### 7. Captured in final run (code `7350857f`, after `deliver`, `attest: ok`)
| Screen | Case | Address (localhost:5470) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| health | KOBO-001 | /sites/KOBO-001/health | pass | pass | both bar groups use the same colour; meaning is in words |
| health | KOBO-002 no source | /sites/KOBO-002/health | pass | pass | |
| health | selected gateway | `?gateway=<id>` | **not captured by script; now an owner look (section 4, via "What to do")** | **same** | reached by the card's own link |
| asset | KOBO-001 battery | /sites/KOBO-001/assets/61e5e895-... | pass | pass | |
| asset | refusal | /sites/KOBO-002/assets/0000... | **not run** | **not run** | refusal panel has no card |

Totals: `w1-ux-05` 56/56, 28 at 1440 and 28 at 390 (`s701-w1-ux-05.txt`). Screenshots: `%TEMP%\w1ux06-final\s701` (not in git).


## Part 17. The left menu (W1-UX-07)

No extra setup: look at the menu on any page you already have open in an earlier part (for example Sites in Part 1), and open the mock-up beside it at `#/sites`.

What to look for:
- The menu now shows the whole mock-up menu: six groups, OPERATIONS, INTELLIGENCE, WORK, ASSURANCE, BUSINESS and ADMIN, with eleven entries in the mock-up's order.
- Only **Sites** and **Findings** open a page. The other nine (Portfolio, Assets, Actions, Incidents, Maintenance, Operational records, Evidence, Financials, Settings) are greyed out and each says "Not available yet" under its name. Clicking them does nothing, and pressing Tab skips them.
- "Not available yet" here means the product has no all-sites page for that entry yet. It does not mean a site has no data: a site's own Assets, Work, Financials and Evidence tabs still work from the site.
- Under the menu, a WORKSPACE section holds "Open Simulator Lab" (shown because the Simulator Lab is switched on in this build). There is no longer a separate bar above the page for it.
- The mock-up's "Demo workspace / 3 sites" line is left out: that count is example data.
- At phone width (about 390 px) the menu sits above the page and wraps; every entry keeps its "Not available yet" with it, and nothing scrolls sideways.

Captured (code at W1-UX-07): `node tools/w1-ux-07-rail-evidence.mjs` 118/118 with the Lab on and 62/62 with the Lab off, at 1440 and 390 px, beside the mock rail.

## Owner's notes: open questions to decide during or after the walk

These are not defects in W1. They are choices the reviews left for you. Mark each one accept, change, or later.

1. **Money words differ between Overview and Financials (W1-UX-02 L4).** The same money state reads differently on the two screens. For example, the Overview says "Fuel quantity not known" and "Fuel cost out of date", while Financials says "Not calculated: no fuel amount, so no cost" and "No current amount can be shown". The Overview's "Upstream out of date" label is jargon. Should the two screens use one set of words?
2. **Financials "no current amount" states show "As of: time not recorded" (W1-UX-02 L6).** The record does carry the time the earlier cost was recorded, but that time dates the old cost, not today's "no current amount" judgement. Should that time be shown, labelled as "earlier cost recorded at ..."? This would need an Architect decision on a read time for the money view.
3. **The Readiness strip and gateway contact.** The strip is now titled "Set-up steps" and covers configuration only. Gateway contact, including stale contact, is shown separately on Health and in the Gateway status panel. Is that split right, or should the strip also show a contact line from the health read? That would be a new read for that screen.
4. **New cards sit above the older panels, so some facts appear twice.** On the Action, Plan, Evidence and Verification screens, the outcome, failed limits and source appear first in the card and again in the older panel below it (W1-UX-04 review item 8). The Dispatch block strip and the per-period block chooser also both select a block (W1-UX-03). Folding these together is a later slice with its own test changes. Is the current density acceptable for now?
5. **Long pages.** Overview and Financials keep their older sections below the new answer card, so they are much longer than the mock-up.
6. **Mock-up content with no record behind it is not built.** On these screens it is either left out or shown as "not available yet":
   - directory counts and type chips;
   - the five-objective strip;
   - Finding priority and confidence chips;
   - the revenue, asset and realised-savings tiles on Financials;
   - Scenarios;
   - editable Assumptions with an impact preview.
7. **Evidence "As of" uses the latest delivery received.** The Evidence read has no read time of its own, so its "As of" can only understate how current it is.
8. **Action Overview names no data source.** Its summary record carries no source label, so the card says so and points to Verification for it.
9. **Dispatch Analysis money sentence.** It still waits for G-04 to tag the fuel/money sentence as missing. Until then a test allowance remains.
10. **Some held or empty states draw no small picture.** The final capture recorded a failed "the card has a small visual" check for these states, which have nothing to draw:
    - the latest and the unavailable Recommendation (both held);
    - the withdrawn trial's held Recommendation;
    - Site Work with nothing to do (proved zero);
    - Assumptions with no price recorded.
    Is a card without a picture right for these, or should they show a "not known" or "nothing scheduled" mark?
11. **The single-line diagram at phone width.** At 390 px the diagram is wider than the screen, so it scrolls sideways inside its own box. The page itself does not scroll sideways.
12. **A Recommendation whose read is unavailable is labelled as held.** In the Action case it reads "Held: an earlier trial is still open". Check that this is the wording you want for that case.
13. **Dispatch Analysis addresses.** The Dispatch tool prints only the day address, so open Analysis from the page's own link rather than typing an address.

## Gate

14. **Menu height and status text size at phone width.** At 390 px the full menu sits above the page and is about 575 px tall, and the "Not available yet" status text is small (9 px, readable contrast). Judge whether the menu should collapse on phones or the status text be larger.

W1 closes only after you have walked this script and recorded your acceptance. Screenshots and passing checks do not count as acceptance, and nothing in this script promotes a screen or panel.
