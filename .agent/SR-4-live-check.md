# SR-4 live check: Site pages x Site types on the real demo DB (D-SR.9)

Revision `35e8a8b59` (task/SR-4-site-range), 2026-11-12. No product code changed.

## Method
- Backend: `uvicorn lab_app:app` from the sr4 worktree on port 5611, env as `demo_combined.py serve_env` (keys.json, prebuilt-routes, DATABASE_URL `assetops_polish_vps1_test`), `ASSETOPS_PERIOD_READ_KINDS=dispatch.day,evidence.claim,mini_depth.renewable,mini_depth.fuel,mini_depth.service,mini_depth.backup`. No tick loop.
- Setup step (file only, no DB write): the Kobo S2 Evidence comparison file is bound to the evidence-store path of the build tree, so the sr4 serve refused Kobo Overview with `AWAITING_EVIDENCE_MIGRATION` ("made over another local evidence store"). I ran `python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001` in the worktree ("writes: none to Postgres") and copied the build tree's `var/evidence/migration-performance`. Both are in the worktree's ignored `var/`, deleted afterwards.
- Frontend: a temporary vitest file (not committed) rendered the whole `<App />` under `MemoryRouter` with the real clients, with `fetch` proxied to the live backend. It waited until no request was in flight for 1.5 s, then recorded every request with its status, the final address (after any redirect or safety-net fill), the range bar's dates and tag, and the `<main>` text. Read timestamps (`2026-11-12T..`) were normalised before comparing texts.
- Pages: crawled per Site from the 10 top tabs, then every in-Site link on them (tabs and subtabs), plus one page of each record type found (Finding, Action, verification, Opportunity, asset, fuel finding). That gave Kobo 30, Kisiwa 28, Cold 21 and EV 25 pages; 312 visits; 1,166 requests.
- Ranges, as the bar writes them (`rangeParams`): **A** = 4-10 Nov (7 days ending 2026-11-10); **B** = 1-5 Nov; **Y** = the "Yesterday" preset with now = 2026-11-11 (10 Nov, the last data day).
- Pass rule: each request carries A, B and Y exactly, or follows the page's declared rule (day tag = `range.to`, Site-local Renewable window, 12:00 local hour, or "Range not used"). Every response is 200 or a declared state that does not depend on the range. A data page's content differs between A and B.

## Result counts
- Kobo: 321 x 200 and 9 x 409. Kisiwa: 286 x 200 and 15 x 409. Cold: 220 x 200 and 1 x 404. EV: 304 x 200, 9 x 409 and 1 x 404.
- No `INVALID_WINDOW` (or any other `INVALID_*`) on any page, range or Site. The Yesterday preset never produced a refusal.
- All 409s are `AWAITING_EVIDENCE_MIGRATION`, the same on every range and on dates before the range. They are listed under "Not range" below.

## Matrix
Key:
- **R**: the request carries the range, and the content changes A to B.
- **D**: day rule. The request uses `range.to`, the tag reads "Showing <day> of the range", and the content changes.
- **N**: the tag reads "Range not used", no request carries the range, and the content is the same.
- **N\***: as N, with a note.

| Page | Kobo | Kisiwa | Cold | EV |
|---|---|---|---|---|
| Overview | D PASS (`overview?date=` 10/5/10 Nov, `outcome-board?date=`, `finding-index` the to-day, mini hour/day reads) | D PASS | R PASS (4 cold reads + outcome-board) | R PASS (`/sites/EV` -> `/ev`, 5 reads) |
| Performance / Dispatch | D PASS (`dispatch/windows/<to>`, `finding-windows/<to>`) | D PASS | R PASS (Temperature, Backup chain, Cooling) | R PASS (Sessions, Availability, Energy) |
| Service | D PASS (local 12:00 hour of `range.to`: `09:00Z-10:00Z`) | D PASS | n/a | n/a |
| Backup | D PASS (same hour rule) | D PASS | (cold Backup: R PASS) | n/a |
| Fuel | D PASS (hour view; the `fuel-balance/nights` list takes no query) | **FAIL** (see F1) | n/a | n/a |
| Renewable | PASS. A reads the last 5 local days, 6-10 Nov, with tag "Showing 6-10 Nov". B reads the whole range, `10-31T21:00Z..11-05T21:00Z` = local 1-5 Nov. Y reads local 10 Nov. Content differs | PASS (same) | n/a | n/a |
| Findings list | R PASS (`finding-index`, `fuel-findings`) | R PASS | R PASS | R PASS |
| Finding detail (and recommendation) | N\* PASS (no range sent; same content; tag "All pages") | N\* PASS | **FAIL** (F2) | **FAIL** (F2) |
| Fuel finding, Opportunity, Action, history, Mill/Fuel verification | N\* PASS (no range sent; same content) | N\* PASS | N\* PASS (Action verification) | N\* PASS |
| Work, Incidents, Maintenance | R PASS (`action-index`, `work/incidents`, `work/maintenance`) | R PASS | R PASS | R PASS |
| Evidence ledger | R PASS (`evidence?from&to`; rejections and analytics declared all-dates) | Not range (409 on every range; see below) | R PASS (`cold/evidence`) | Not range (409 on every range). `/ev/evidence` and `/ev/evidence/analysis`: R PASS |
| Financials | N PASS ("prices valid now"; SR-5 pending) | N PASS | R PASS | R PASS (`/financials` -> `/ev/financials`; the same 4 requests as a direct `/ev/financials` visit, so the fingerprint matches) |
| Financial assumptions | N PASS (redirects to Prices) | N PASS | N\* note F3 | N\* note F3 |
| Scenarios | R PASS | R PASS | R PASS | R PASS (requests carry the range; "No scenario defined yet", so the same text is honest) |
| Prices | N PASS | N PASS | N PASS | N PASS |
| Health | N PASS ("shows now"; SR-6 pending) | N PASS | R PASS | R PASS |
| Foundation, readiness, SLD, changes | N PASS | N PASS | N PASS | N PASS |
| Assets, asset page | N PASS | N PASS | N PASS | N PASS |

## Failures
- **F1, Kisiwa Performance > Fuel (nights view).** Under B (1-5 Nov) the page requests `GET /api/sites/KISIWA-001/fuel-balance/nights/2026-11-10` (200) and shows the 10 Nov night. It does the same under A and Y, so the A and B texts are identical. The bar tag reads "All pages", so it claims the page follows the range, but the shown night is outside B. The nights list (`/fuel-balance/nights`, no query) shows all nights from 1 to 10 Nov. Rule 10d.3: "Kisiwa's Fuel tab via SR-10k ... until those merge: D with the 10d.2(a) tag". Expected: the night at `range.to` with "Showing 5 Nov of the range", or the range's nights. The hour read on the same page does follow the range (`mini/fuel?from=2026-11-05T09:00Z`).
- **F2, Cold and EV Finding detail** (rule 10.5: "N: one Finding's own episode").
  - Under B the requests `GET /api/sites/COLD-LAB-001/cold/findings/1d2d3f42-...?from=2026-11-01T00:00:00Z&to=2026-11-06T00:00:00Z` and `GET /api/sites/EV-LAB-001/ev/findings/7601a982-...?from=2026-11-01...&to=2026-11-06...` return **404** `COLD_FINDING_NOT_FOUND` / `EV_RECORD_NOT_FOUND`. The page shows the refusal frame.
  - Under A and Y the same Finding's header shows the address range as its window ("4 Nov 2026, 00:00 - 11 Nov 2026, 00:00", or "10 Nov ... 11 Nov"), so the range re-cuts the record.
  - The reader is unchanged by SR-4 (`git diff main...HEAD` touches only a Link import in `coldSiteViews.tsx`). SR-4 now carries the range onto this page, so changing the range while on it hits the refusal.
- **F3 (Low, contradiction, not a refusal): Cold and EV financial assumptions.** The tag reads "Range not used · prices valid now". But the request carries the range, and the page shows "Analysed periods in this range: 3 · showing 5 Nov" (Cold) and "Analysed period: 3 Nov ..." (EV), which change from A to B.

## Not range (pre-existing state, the same on every range)
- `GET /api/sites/{KOBO,KISIWA,EV}/analytics` returns 409 `AWAITING_EVIDENCE_MIGRATION` ("legacy file-backed surface"). It takes no query; the Evidence page declares it all-dates.
- `GET /api/sites/{KISIWA-001,EV-LAB-001}/evidence?from&to` and `/evidence/rejections` return 409 `AWAITING_EVIDENCE_MIGRATION` ("only after a passing legacy comparison record"). The ledger request carries A, B and Y correctly. The build tree holds a comparison file for Kobo only, so the build's own serve answers the same way.

## Limits of this method
- jsdom has no layout. Bar and tag positions, overflow, charts and SVG geometry were not seen; only text and requests were checked.
- Each page was opened directly at an address. Clicking the picker or a link was not exercised live, so the vitest pins (`siteRangeCarry`, `rangeLink`) remain the evidence for carry-over.
- A request was judged from its URL and status, and content only by whether the `<main>` text differs. The correctness of the numbers was not checked.
- Pages not reachable by links from the 10 tabs were not visited. These include Foundation change detail and the Sites index.
