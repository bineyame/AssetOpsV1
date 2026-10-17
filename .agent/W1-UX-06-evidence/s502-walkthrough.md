# Walkthrough: Overview Finding list and Site Findings bridge (`s502_overview_finding_list_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` copied from the main checkout into this folder (`var/` is ignored by git).

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s404_owner_s502_w1ux06","--work","var/s404_owner_s502_w1ux06","--api-port","8990","--web-port","5490","--tls-port","8991","--http-port","8992"
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py prepare @T
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py serve @T
```
`prepare` takes about 4 minutes and must end with "0 failed check(s)" and "0 Overview check(s) failed". `serve` prints the addresses.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="8990"; npm.cmd run dev -- --port 5490 --strictPort
```
Look at the first set of days BEFORE running `tick`: `tick` assesses the waiting evidence, so the "out of date" day becomes current. Then, in a third window (same first two lines as above, then `$T=...`), one at a time:
```
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py late @T      # late readings for 15 Oct, not yet assessed
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py settle @T    # assess them; 15 Oct is current again
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py gate --close @T   # the list is closed
.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py gate --open @T    # undo
```

## 3. Ports and addresses
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

## 4. What to look for
- 15 Oct: the list shows Findings in order and says "Showing the first 2 of 3. This is not the whole list."; each row opens that exact Finding; "Open the full Findings list for this day" opens the same day on Site Findings.
- 25 Oct: "No Findings for this day." with the green state line. 27 Oct, 5 Nov, 30 Oct: no rows and no count, with the reason (out of date, failed, not assessed).
- After `late`: 15 Oct shows no rows and says it is out of date. After `settle`: rows are back. After `gate --close`: the list says it is closed with no rows; the rest of the Overview stays.
- The state line (state, site, "As of") is visible with "How this was worked out" closed.
- Keyboard: Tab reaches "How this was worked out"; Enter on a row opens the Finding and Back returns to the same day. Exact link: paste in a new tab, same day. Reload: same day and rows.

## 5. Data label
Authored test cases sent through the real intake (labelled fixture batches). Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s502_overview_finding_list_walkthrough.py drop @T`.

## 7. Captured in final run (code `41160b19`; no `tick` before the first set)
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
