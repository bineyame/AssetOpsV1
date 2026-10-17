# Walkthrough: Finding Evidence and Financials source labels (`s405_provenance_walkthrough.py`, owner case)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` copied from the main checkout into this folder (`var/` is ignored by git).

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--suffix","_w1ux06","--api-port","9020","--web-port","5520","--tls-port","9021","--http-port","9022"
.venv\Scripts\python.exe tools\s405_provenance_walkthrough.py prepare --only owner @T
.venv\Scripts\python.exe tools\s405_provenance_walkthrough.py links @T
.venv\Scripts\python.exe tools\s405_provenance_walkthrough.py serve --case owner @T
```
`prepare` takes about 2 minutes and must end with "failed checks: {'owner': 0}". `links` prints the addresses (the ids are new on every prepare, so always copy them from `links`). `serve` keeps running and re-checks the schedule every two minutes.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9020"; npm.cmd run dev -- --port 5520 --strictPort
```

## 3. Ports and addresses
API 9020, web 5520. Addresses from the final run (`<F1>` = `cff9cbd1-3ae4-449e-b2ee-893a04c61bca`, `<R1>` = `45e11224-cf58-450a-9156-58bfafdd0ee1`; `<F2>` = `3f93014d-7b29-4d6a-adca-578786f74f6a`, `<R2>` = `a570010c-154e-4af2-8e42-b1874f9b88b7`):

| Screen / state | Address | Mock |
| --- | --- | --- |
| Finding Evidence, 23 Oct (prepared example data) | http://localhost:5520/sites/KOBO-001/findings/<F1>/evidence?revision_id=<R1> | `http://localhost:5520/mockups/v69/index.html#/finding-evidence` |
| Financials, 23 Oct, amount shown with its source | http://localhost:5520/sites/KOBO-001/financials?finding_id=<F1>&revision_id=<R1> | `#/financials` |
| Financials, 24 Oct, amount withheld | http://localhost:5520/sites/KOBO-001/financials?finding_id=<F2>&revision_id=<R2> | `#/financials` |

`links` also prints the 2 Oct "Generated test data" Finding/Evidence/Financials and the older versions; they were not captured in this run.

## 4. What to look for
- Finding Evidence: the bold answer says where this Finding's readings came from; the line "Latest recorded version, opened by its exact reference" with "As of" shows while "How this was worked out" is closed; a "Source record for this finding version" panel says "Prepared example data"; links back to the Finding.
- Financials 23 Oct: a money range (0.00 to 15.82 USD) with "Modelled range, using the latest checked readings", the same source label as the Finding, and a link to the Evidence.
- Financials 24 Oct: "No current amount can be shown" - no number, because the generator readings needed for it are missing. Its "As of" reads "time not recorded" (no read time for this state).
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same page. Reload: same page.

## 5. Data label
Authored test batches sent through the real intake ("Prepared example data"), plus one registered Lab run ("Generated test data"). Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s405_provenance_walkthrough.py drop @T`.

## 7. Captured in final run (code `c104f3cc`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| finding-evidence (`w1-ux-02`) | labelled source | Finding Evidence 23 Oct | 10/10 | 11/11 | |
| financials (`w1-ux-02`) | `provenance` (priced, source shown) | Financials 23 Oct | 11/11 | 12/12 | revenue/asset/realised-savings tiles, trade-offs and Scenarios not built |
| financials (`w1-ux-02`) | `withheld` | Financials 24 Oct | 9/9 | 10/10 | as-of reads "time not recorded" |
| evidence (`w1-ux-03`) | labelled source/unknown | - | **not run** | **not run** | `links` prints only Finding-level Evidence addresses, no Site Evidence (`/sites/KOBO-001/evidence`) address |

Totals: `w1-ux-02` 63/63 (30 at 1440, 33 at 390) (`s405-w1-ux-02.txt`). Screenshots: `%TEMP%\w1ux06-final\s405\` (not in git).
