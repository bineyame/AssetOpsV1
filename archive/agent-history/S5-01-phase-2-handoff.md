# S5-01 phase 2 handoff - Site UI, walkthrough and slice closeout

Branch `task/S5-01-site-overview`; phase 2 commits from `440a2bad`; LR-01 fix rounds 1 (`78a47be5`) and 2 (`e8d555bc`)
merged in, no conflicts. Slice review is next (packet `.agent/S5-01-review-packet.md`).

## What landed

- UI: `frontend/src/sites/SiteWindowOverview.tsx` (new), `SiteOverview.tsx` (`useSearchParams`; `date`, `finding_id`,
  `finding_revision_id`; served values written back with `replace`; a ref skips the re-read the write-back would
  cause), `siteOverviewClient.ts` (`isSiteWindowSummary`, `OverviewSelection`), `shell/SiteDetailFrame.tsx`
  (`windowLinks`), `ui/primitives.css` (`.site-window-overview`, `.window-*`).
- Backend: phase-1 review M1/M2/L1-L4/L7 and L6 route tests; seam `current_amount_permitted` conjunct; interval spans;
  `main.py` startup fix (`app.router.on_shutdown`).
- Tools: `tools/s5_overview_walkthrough.py`, `tools/s5-overview-evidence.mjs`. Owner doc `.agent/S5-01-owner-walkthrough.md`.

## Anchors

- Money precedence `backend/assetops_backend/site_overview/money_state.py:money_state`; pin rules `read.py:_pin`,
  `_previous_pin`; UI state words `SiteWindowOverview.tsx` `FRESHNESS_WORDS`, `MONEY_STATE_WORDS`, `PIN_WORDS`.
- Walkthrough producers: `S5Walk(lr.Lr01Walk)`; price published once (`backend()` override); P01 via a swapped
  `power_spec`; failed day via `FAIL_STAGE`; ticks env `default`.

## Open / risks

- Merge and registry promotion wait for the owner record in the walkthrough doc.
- Review L5 (fence placement) and Postgres merge/midnight cases are recorded deviations.
- Production schedule thresholds: amounts lapse five minutes after a manual tick in the walkthrough.
