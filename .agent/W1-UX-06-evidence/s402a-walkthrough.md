# Walkthrough: Financials > Assumptions, the site diesel price (`s402a_assumptions_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- The shared `assetops_s4cases` Finding template (`tools/s4_finding_cases.py run`, which needs `var/sites/kobo-001.yaml` copied from the main checkout). It was already present for this run.

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$A="--db","assetops_s402awalk_w1ux06","--empty-db","assetops_s402aempty_w1ux06","--work-name","s402a-w1ux06"
.venv\Scripts\python.exe tools\s402a_assumptions_walkthrough.py @A prepare
.venv\Scripts\python.exe tools\s402a_assumptions_walkthrough.py @A links --web-port 5560 --empty-web-port 5561
.venv\Scripts\python.exe tools\s402a_assumptions_walkthrough.py @A serve --port 9060 --empty-port 9061
```
`prepare` takes about 2 minutes and ends with "Prepared. Next: links, then serve." (it prints that twice). Always copy addresses from `links`. `serve` runs two APIs (priced 9060, empty-price 9061) until Ctrl+C.
Second and third windows:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9060"; npm.cmd run dev -- --port 5560 --strictPort
```
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9061"; npm.cmd run dev -- --port 5561 --strictPort
```

## 3. Ports and addresses
APIs 9060 / 9061, web 5560 / 5561.

| Screen / state | Address | Mock |
| --- | --- | --- |
| Assumptions, price in effect | http://localhost:5560/sites/KOBO-001/financials/assumptions | `http://localhost:5560/mockups/v69/index.html#/assumptions` |
| Assumptions, empty-price store (no price) | http://localhost:5561/sites/KOBO-001/financials/assumptions | `#/assumptions` |

`links` also prints each price version (`?revision_id=...`), "Prices as recorded then" (`?recorded_at=...`) and three Findings' money views; not captured here (recorded-time history is covered by s408).

## 4. What to look for
- Price in effect: the bold answer gives the diesel price now in effect, with "Price recorded for this site" and an "As of" time while "How this was worked out" is closed; a small price strip; a link "See every recorded price version". "Edit price" is shown but cannot be used.
- Empty-price store: "No price recorded", no number.
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same page. Reload: same page.

## 5. Data label
SYSTEM demonstration diesel price fixture (v1 initial, v2 succession, v3 correction) over the authored S4 Finding cases. Not field readings.

## 6. Stop and clean up
Ctrl+C in all three windows, then `.venv\Scripts\python.exe tools\s402a_assumptions_walkthrough.py @A drop`.

## 7. Captured in final run (code `26636869`)
| Screen | Case | URL | 1440 | 390 | App vs mock |
| --- | --- | --- | --- | --- | --- |
| assumptions (`w1-ux-02`) | price in effect | web 5560 | 10/10 | 11/11 | editable Assumptions with an impact preview not built ("Edit price" disabled) |
| assumptions (`w1-ux-02`) | `emptyprice` (extra case) | web 5561 | 7/8 | 8/9 | **FAIL** "the card has a small visual" at both widths: the no-price state draws no price strip |

Totals: `w1-ux-02` 36/38 (17/18 at 1440, 19/20 at 390) (`s402a-w1-ux-02.txt`); the required effective-price case is 21/21. Screenshots: `%TEMP%\w1ux06-final\s402a\` (not in git).
