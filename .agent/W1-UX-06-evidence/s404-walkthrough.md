# Walkthrough: Site Findings list (`s404_finding_index_walkthrough.py`)

## 1. Prerequisites (one time)
- Docker Postgres running on 127.0.0.1:55432.
- `var/sites/kobo-001.yaml` copied from the main checkout into this folder (`var/` is ignored by git).

## 2. Commands (PowerShell, in order)
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3
$wt="C:\Users\assef\Bineyame\AssetOpsV1-review3"; $env:PYTHONPATH="$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator"
$T="--db","assetops_s404_owner_w1ux06","--work","var/s404_owner_w1ux06","--api-port","8993","--web-port","5493","--tls-port","8994","--http-port","8995"
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py prepare @T
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py serve @T
```
`prepare` takes about 2 minutes and must end with "0 failed check(s)". `serve` prints the addresses.
Second window:
```
cd C:\Users\assef\Bineyame\AssetOpsV1-review3\frontend; $env:ASSETOPS_API_PORT="8993"; npm.cmd run dev -- --port 5493 --strictPort
```
After looking at every day, in a third window (same first two lines as above, then `$T=...`):
```
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py late @T      # late readings for 15 Oct, not yet assessed
.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py settle @T    # assess them; 15 Oct is current again
```
This tool serves only the Site Findings list; the site's day Overview stays closed here (use the s502 walkthrough for it).

## 3. Ports and addresses
API 8993, web 5493. Mock: `http://localhost:5493/mockups/v69/index.html#/sitefindings`. All addresses start with `http://localhost:5493/sites/KOBO-001/findings?` and end with `&domain=mini-grid-dispatch`.

| Day / state | Address | Mock |
| --- | --- | --- |
| 15 Oct, Findings listed | http://localhost:5493/sites/KOBO-001/findings?from=2026-10-15T00%3A00%3A00Z&to=2026-10-16T00%3A00%3A00Z&domain=mini-grid-dispatch | `#/sitefindings` |
| 15 Oct, 2 per page | same as above plus `&limit=2` | `#/sitefindings` |
| 25 Oct, checked and none found | ...from=2026-10-25T00%3A00%3A00Z&to=2026-10-26T00%3A00%3A00Z... | `#/sitefindings` |
| 27 Oct, out of date | ...from=2026-10-27T00%3A00%3A00Z&to=2026-10-28T00%3A00%3A00Z... | `#/sitefindings` |
| 5 Nov, check failed | ...from=2026-11-05T00%3A00%3A00Z&to=2026-11-06T00%3A00%3A00Z... | `#/sitefindings` |
| 30 Oct, not assessed | ...from=2026-10-30T00%3A00%3A00Z&to=2026-10-31T00%3A00%3A00Z... | `#/sitefindings` |

## 4. What to look for
- 15 Oct: the bold answer is about the Findings for the day; the green line "Using the latest checked readings" shows the site, the day and "As of" while "How this was worked out" is closed; a small day strip; each row opens its Finding.
- 2 per page: two rows and a "Next page" link.
- 25 Oct: "Checked: nothing to report" - a proved zero, not a missing answer.
- 27 Oct: "This result may miss newer readings". 5 Nov: "The latest check could not be completed". 30 Oct: "We have not checked this period". None of these shows rows or a count.
- After `late`: 15 Oct says "This result may miss newer readings". After `settle`: back to "Using the latest checked readings".
- Keyboard: Tab reaches "How this was worked out". Exact link: paste in a new tab, same day. Reload: same day.

## 5. Data label
Authored test cases sent through the real intake (labelled fixture batches). Not field readings.

## 6. Stop and clean up
Ctrl+C in both windows, then `.venv\Scripts\python.exe tools\s404_finding_index_walkthrough.py drop @T`.

## 7. Captured in final run (code `bc3ef4c7`)
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
