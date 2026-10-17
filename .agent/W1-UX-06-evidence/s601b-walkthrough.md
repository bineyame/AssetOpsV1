# Walkthrough: Recommendation, Action and Foundation change (`s601b_action_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- Nothing else: `prepare` builds its own copy of the code and data.

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s601b_w1ux06","--work","var/s601b_w1ux06"
.venv\Scripts\python.exe tools\s601b_action_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s601b_action_walkthrough.py @T links
.venv\Scripts\python.exe tools\s601b_action_walkthrough.py @T serve
```
`prepare` takes about a minute and ends with "Prepared. Next: links, then serve." `links` prints every address below. The ports are fixed by the tool.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="8961"; npm.cmd run dev -- --port 5461 --strictPort
```

## 3. Ports and addresses
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

## 4. What to look for
- Recommendation, accepted: the box reads "Accepted; result not yet known" with "As of 1 Nov 2026, 00:00 UTC" while "How this was worked out" is closed. Links "Open the Action" and "Open Verification" are there.
- Recommendation, latest and unavailable: the box reads "Held: an earlier trial is still open". These two have no small picture.
- The change: "Setting changed; effect judged separately", with the date and time.
- Action overview (both): "No trial plan yet".
- Application: applied shows "Applied; effect not yet measured"; the second Action shows "Not applied yet; an attempt failed".
- History: the full list shows "Every recorded event"; an event address shows "Earlier version, kept for the record" and the time of that event.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same screen and state. Reload: same screen and state.

## 5. Data label
Generated demonstration records (test cases F01/F02 run through the real Action screens' service). Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows, then:
```
.venv\Scripts\python.exe tools\s601b_action_walkthrough.py @T drop
```

## 7. Captured in final run (code `1d1fcc8e`)
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
