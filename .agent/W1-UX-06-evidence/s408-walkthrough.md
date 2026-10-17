# Walkthrough: Assumptions price and fuel cost history (`s408_assumption_history_walkthrough.py`, owner and mixed cases)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` copied from the main checkout into this folder (`var/` is ignored by git).

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--suffix","_w1ux06","--api-port","9060","--web-port","5560","--tls-port","9061","--http-port","9062"
.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py prepare @T
.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py links @T
.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py serve --case owner @T
```
`prepare` takes about 3.5 minutes and must end with "0 failed checks". The recorded moments T1/T2/T3 are new on every prepare, so always copy addresses from `links`. `serve` keeps running until Ctrl+C.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="9060"; npm.cmd run dev -- --port 5560 --strictPort
```
Closed source: Ctrl+C `serve`, then `... close-gate @T`, `... serve --case owner @T`, reload; afterwards Ctrl+C and `... open-gate @T`.
Mixed source: Ctrl+C `serve`, then `... serve --case mixed @T` and reload the default address.

## 3. Ports and addresses
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

## 4. What to look for
- Default: the price now in effect ("Price recorded for this site", "As of" time) while "How this was worked out" is closed; a price strip; under "Interpretation history" the latest and earlier fuel cost versions, each recorded amount labelled as history beside its source; a plain sentence where only the price changed; one version with no amount (unpriced).
- T1 / T3: "Prices as recorded at an earlier moment"; the prices and the history are for the same moment; the address keeps `recorded_at` after reload.
- Closed source: every version is listed without an amount, and the page says the source is closed. Mixed source: every recorded amount is withheld ("Sources do not agree").
- Keyboard: Tab reaches "How this was worked out". Exact link: a history version opens that Finding's Financials at that exact version. Reload: same page, same moment.

## 5. Data label
Authored batches sent through the real intake ("Prepared example data") and the SYSTEM demonstration price fixture with extra authored price corrections. Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows (run `open-gate` first if the gate is closed), then `.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py drop @T`.

## 7. Captured in final run (code `f4da5ec4`)
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
