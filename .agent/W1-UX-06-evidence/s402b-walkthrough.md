# Walkthrough: Financials fuel cost states (`s402b_fuel_cost_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- A fresh `assetops_s402bcases` template (about 2.5 minutes; it must end with "VERIFY PASSED"). The old template was stale, so rebuild it before the first walkthrough:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
.venv\Scripts\python.exe tools\s402b_power_cases.py --tls-port 9062 --http-port 9063 run
```

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$A="--db","assetops_s402bwalk_w1ux06","--empty-db","assetops_s402bempty_w1ux06","--work-name","s402b-w1ux06"
.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A prepare
.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A links --web-port 5560 --empty-web-port 5561
.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A serve --port 9060 --empty-port 9061 --web-port 5560 --empty-web-port 5561
```
`prepare` takes about 1 minute and ends with "Prepared. Next: links, then serve." The ids are new on every prepare, so always copy addresses from `links`. `serve` runs two APIs (priced store 9060, empty-price store 9061) until Ctrl+C.
Second and third windows:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9060"; npm.cmd run dev -- --port 5560 --strictPort
```
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9061"; npm.cmd run dev -- --port 5561 --strictPort
```
For the "no price recorded" state, after looking at the empty-price store once, run (first window, `serve` may keep running):
```
.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A recompute --empty
```

## 3. Ports and addresses
APIs 9060 / 9061, web 5560 / 5561. From the final run (`<P>` = `finding_id=0e95ad69-759b-4c45-92e9-222146268f54&revision_id=565111ca-4bfa-44d0-bf48-05bb9525fe3b`):

| Screen / state | Address | Mock |
| --- | --- | --- |
| Financials, P01 (23 Oct), priced | http://localhost:5560/sites/KOBO-001/financials?<P> | `http://localhost:5560/mockups/v69/index.html#/financials` |
| Financials, F01 gateway (2 Oct), not calculated | http://localhost:5560/sites/KOBO-001/financials?finding_id=81b63e65-b87a-4d2b-a4dd-7819ef2dcf9f&revision_id=fcd0a325-d68a-4bc9-8898-ac880a4df7d1 | `#/financials` |
| Financials, P01 in the empty-price store, before `recompute --empty` | http://localhost:5561/sites/KOBO-001/financials?<P> | `#/financials` |
| Same address after `recompute --empty` (no price) | http://localhost:5561/sites/KOBO-001/financials?<P> | `#/financials` |

`links` also prints the Assumptions page, the price versions, exact fuel cost versions and an earlier Finding version; those were not captured here (Assumptions is covered by s402a and s408).

## 4. What to look for
- Priced: a money range with "Modelled range, using the latest checked readings" and an "As of" time, while "How this was worked out" is closed; a small chart; links to the Evidence and back to the Finding.
- Not calculated: "Not calculated: no fuel amount, so no cost" - no number, because the power readings cover too little of the time. "As of: time not recorded".
- Empty-price store before recompute: "No current amount can be shown" (not worked out yet). After `recompute --empty`: "No price recorded". Both say "As of: time not recorded" and show no number.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same page. Reload: same page.

## 5. Data label
Authored power demonstration batch (P01) and an ordinary Lab gateway run (F01), sent through the real intake; diesel prices are the SYSTEM demonstration fixture. Not field readings.

## 6. Stop and clean up
Ctrl+C in all three windows, then `.venv\Scripts\python.exe tools\s402b_fuel_cost_walkthrough.py @A drop`. Keep `assetops_s402bcases` (shared template).

## 7. Captured in final run (code `0a4da463`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| financials (`w1-ux-02`) | priced | P01, web 5560 | 11/11 | 12/12 | revenue/asset/realised-savings tiles, trade-offs and Scenarios not built |
| financials (`w1-ux-02`) | `notcalculated` | F01 gateway, web 5560 | 9/9 | 10/10 | as-of reads "time not recorded" |
| financials (`w1-ux-02`) | `notworkedout` (empty store, before recompute) | P01, web 5561 | 9/9 | 10/10 | as-of reads "time not recorded" |
| financials (`w1-ux-02`) | `emptyprice` (after `recompute --empty`) | P01, web 5561 | 11/11 | 12/12 | as-of reads "time not recorded" |

Totals: `w1-ux-02` 84/84 (40 at 1440, 44 at 390) (`s402b-w1-ux-02.txt` 61/61, `s402b-w1-ux-02-emptyprice.txt` 23/23). Screenshots: `%TEMP%\w1ux06-final\s402b\` (not in git).
