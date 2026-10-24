# Post-W6 audit, batch 05: W1 verification

IDs: `verification`, `sitework`. Branch `audit/batch-05` at main `73d538ab` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review6`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows.

Machine-readable record: `batch-05.json` (26 pairs, every field the spec lists). Side-by-side view: `index.html`. Difference source: `differences.json` (written by `tools/differences.py`).

## Route reconciliation

Both IDs are mounted in `frontend/src/App.tsx` as the spec states: `sitework` = `SITE_WORK_ROUTE_PATH` (`/sites/:siteId/work`, `SiteWorkFrame`; mini-grid takes the W1 branch, not `DomainWorkActionsPage`); `verification` = `SITE_ACTION_VIEW_ROUTE_PATH` (`/sites/:siteId/actions/:actionId/:actionView`, `SiteActionFrame`). No spec route-table error.

## Run record

- **Ports.** API 18501 (s603), 18502 replay + 18503 test-scoped case (s602b `serve --port 18502`); Vite 5185 restarted per API (`ASSETOPS_API_PORT` 18501, then 18502, then 18503), since only one Vite port is allotted; Chrome CDP 9525. Every process stopped by PID.
- **Databases.** Created and dropped only by the producers' own `prepare`/`drop`, unmodified, under the 2026-10-24 scratch-DB authorization: `assetops_s603_owner_audit` (work `var/s603_owner_audit`); `assetops_s602b_audit` plus its case DBs `_target_miss`, `_guardrail`, `_inconclusive`, `_withdrawn` (work `var/s602b_audit`). `assetops_s602b_audit` was held by batch 4 at start, so s603 ran first and s602b was prepared only after `pg_database` showed it free. No `assetops_audit_b05*_test` DB was needed. No other DB touched.
- **Producers.**
  - `tools/s603_site_work_walkthrough.py` prepare (2 Actions ACT-000001/ACT-000002 created 2026-11-01, Performance cutover permitted), `attest` (ATTEST OK), `serve --port 18501 --web-port 5185`, `drop`. URLs are the ones the producer prints (positive, limit=1, zero, no window), plus an invalid window (`from` after `to`), which is a URL only (capture-only; the server refuses it).
  - `tools/s602b_verification_walkthrough.py` prepare (replay: VERIFIED Action ACT-000001 `235e5f8e…`, outcome `8e84494a…`; cases target_miss INEFFECTIVE, guardrail INEFFECTIVE, inconclusive INCONCLUSIVE, withdrawn re-settled INCONCLUSIVE), `links`, `serve --case <name>` per case, `drop`. Replay URLs from `links` (current, exact historical outcome, selector conflict), plus an unknown Action id `00000000-0000-4000-8000-000000000000` (capture-only URL).
- **Capture.** `tools/capture-b5.mjs` = `capture-b3.mjs` with only the CDP port and profile prefix changed (navigate, wait, screenshot, measure DOM). `tools/run-cases.sh` only restarts the unmodified `serve --case` and runs the capture. Claims: s603 60/60, replay 48/48, each case 12/12. No console errors.

## Pairs (26)

| Screen | Cases (each at 1440 and 390) | Max panel ratio |
| --- | --- | --- |
| verification | verified-current, historical-outcome, selector-conflict, unknown-action, target_miss, guardrail, inconclusive, withdrawn | 1.53 (inconclusive 390 Outcome evidence) |
| sitework | positive, page1-limit1, zero, no-window, invalid-window | 1.65 (positive 390) |

Panel count and title order match the mock on all 26 pairs (verification: Target and guardrails evaluated together / Activity evidence / Outcome evidence; sitework: Actions at this site). No page horizontal overflow at either width. All >1.3x panels fall under the W1-F5b overage rulings in `.agent/W1-F5b-evidence/overages.json` (verification x3, sitework x1); those rulings still need register rows.

## Differences (proposals)

- **B5-X1** cross-cutting, cited only: B1-01/B2-01, B1-04/B2-36 (all pairs); B2-21/B3-04 UTC (all verification pairs; sitework strip/zero/invalid copy); B2-02 (sitework window control in panel); B1-02/B2-04 (390 dark header 109 px sitework no-window/invalid, 115 px verification unknown-action); B1-07/B2-03 (sitework closing note at 14 px); B1-53 (`VERIFICATION_SELECTOR_CONFLICT` code; backticked `from`/`to` in sitework invalid copy).
- **B5-01** verification: Site tab row with `Findings` current above the Action tabs, breadcrumb via Findings / `Action`; mock has only the Action row and an Actions breadcrumb. Proposed (c) D3, shared with batch 4 action-* screens.
- **B5-02** tab `Application` vs mock `Execution`. (b) D2, or (c) D3 rename.
- **B5-03** header: `Open site` button missing (c) D3 Low; title/F-code arrangement (b) D1 extend R65.
- **B5-04** status strip additions (b) D2 (as R80/R91); Owner/F-code (b) D1.
- **B5-05** criteria table `Limit` vs `Evidence` column, additions, 1.44x at 390: (a) W1-F5b ruling; Limit `None` for a 0 min limit: (c) D3 Low copy.
- **B5-06** Activity/Outcome evidence content and 1.34-1.53x: (a) W1-F5b rulings; no change reference (b) D1.
- **B5-07** selector conflict: duplicate sentence in Outcome evidence and "read failed" KPI wording: (c) D3 Low.
- **B5-08** unknown Action: subtitle asserts "an action raised from a finding" (c) D3 Low; three headed refusal panels vs cold/EV single state panel (R101/R110): (b) D2 align or rule.
- **B5-09** sitework strip lacks `Manage in Actions` (c) D3 Low; wording (a) W1-F5b ruling.
- **B5-10** sitework table: F-code (b) D1 extend R65; Owner/criterion `Not recorded` (b) D1; state vocabulary, footer, 1.36x/1.65x (a) W1-F5b ruling.
- **B5-11** zero / no-window / invalid states and footer copy: (b) D1 honest states.
- **B5-12** carried checks: plural not observable; `c1 · EV_CONNECTOR` n/a; mini invalid-window copy is one combined message for distinct inputs (carry with the domainActionClient item, (c) D3 Low); R88/R112 n/a (cold/EV); R22/R23/R24/R37/R38/R60 do not touch these screens; R69 verified closed (rail shows Actions on W1 Action detail).

## Blockers

None. Not observable with these producers: a `1 incidents`/`1 maintenance` count on the mini Work subrow; a verification state with a mock-style "Pending" outcome (s602b yields only settled outcomes).
