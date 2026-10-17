# Walkthrough: one Finding, out of date, and its history (`s4_finding_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` copied from the main checkout into this folder (`var/` is ignored by git).
- The shared case database `assetops_s4cases` must exist. If it does not, build it once (about 10 minutes): `.venv\Scripts\python.exe tools\s4_finding_cases.py run` (same env lines as below). The final run used the existing copy.

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s4walk_w1ux06","--work","var/s4walk_w1ux06"
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T prepare
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T links --web-port 5496
.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T serve --port 8996 --web-port 5496
```
`prepare` takes about a minute and ends with "Prepared. Next: links, then serve." `links` prints every Finding address (they change only when `assetops_s4cases` is rebuilt).
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="8996"; npm.cmd run dev -- --port 5496 --strictPort
```
Optional, after looking: `.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T recover` makes the out-of-date Finding current again.

## 3. Ports and addresses
API 8996, web 5496. Mocks: `http://localhost:5496/mockups/v69/index.html#/finding` and `#/finding-history`.

| Screen | Address (from `links`) | Mock |
| --- | --- | --- |
| F01 open Finding (6 Oct) | http://localhost:5496/sites/KOBO-001/findings/937ffdef-a923-4f7b-b204-98fa61ce1058 | `#/finding` |
| F02 cross-midnight, out of date | http://localhost:5496/sites/KOBO-001/findings/ff2c2005-ec4f-413b-86f8-1fa8c8e6bce8 | `#/finding` |
| F01 history at version 1 | http://localhost:5496/sites/KOBO-001/findings/937ffdef-a923-4f7b-b204-98fa61ce1058/history?revision_id=b6af6f73-9be7-4a45-b729-86db1d3e2d92 | `#/finding-history` |

## 4. What to look for
- F01: the bold answer says what was found and when; the green line "Using the latest checked readings" shows the site and "As of" while "How this was worked out" is closed; a small picture of the episode; links "Open the recommendation" and "See how this conclusion was reached".
- F02: "This result may miss newer readings" (a newer record is waiting to be checked); the recorded version stays visible.
- History: "Earlier version, kept for the record", with the version timeline and links "Select the latest version", "Open version 1 of the Finding" and "Open version 1's evidence".
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same Finding and version. Reload: same page.

## 5. Data label
Authored test cases sent through the real intake (labelled fixture batches, `s4-finding-cases-v1`). The out-of-date state on 9 Oct is staged in the walkthrough copy only. Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s4_finding_walkthrough.py @T drop` (leaves `assetops_s4cases` alone).

## 7. Captured in final run (code `5f2fac28`)
| Screen | Case | Address (localhost:5496) | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| finding (`w1-ux-02`) | F01 open | /sites/KOBO-001/findings/937ffdef-... | pass | pass | priority/confidence chips not built |
| finding | stale (F02) | /findings/ff2c2005-... | pass | pass | |
| finding-history | F01 version 1 | /findings/937ffdef-.../history?revision_id=b6af6f73-... | pass | pass | |

Totals: `w1-ux-02` 59/59 (28 at 1440, 31 at 390; `s4_finding-w1-ux-02.txt`). Screenshots: `%TEMP%\w1ux06-final\s4_finding\ux02` (not in git).
