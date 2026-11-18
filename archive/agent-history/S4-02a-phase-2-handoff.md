# S4-02a phase 2 handoff: reads, Financials UI, Finding bridge, Foundation link

Branch `task/S4-02a-site-assumptions`, commits `408e9e6`..HEAD (`git log 5159b96..HEAD`). Phase 2 is complete; the slice is `in_review`. Packet: `.agent/S4-02a-review-packet.md`. Owner steps: `.agent/S4-02a-owner-walkthrough.md`.

## What landed (anchors)

- **C1/C2 (first commit `408e9e6`):**
  - `financials/assumptions.py` `PROVENANCE_NOT_DIGESTED` / `canonical_step_sha256` / `request_sha256`. The authorization prose is no longer digested.
  - `publish_assumption.py` adds `fixture_step_sha256`.
  - Fixture v2 is now `2030-01-01`. The test derives `V2_START` from the fixture.
  - Migration 0010's set-once trigger now refuses a close at or before the series' latest `recorded_from` (L1).
- **Reads:**
  - `financials/assumption_read.py` `AssumptionReadService.series/revision`.
  - Store `snapshot` / `revision_detail`, both REPEATABLE READ.
  - Routes in `financial_read_api.py`, wired in `main.py` after the write router.
- **Bridge:** `finding_api.py` `finding_financials` and `consequence_state`.
- **UI:**
  - `frontend/src/sites/SiteFinancials.tsx` (`SiteAssumptions`, `SiteFinancialsOverview`, `DisabledEdit`).
  - `sites/financialsClient.ts`.
  - `shell/SiteAnalyticsFrames.tsx` `SiteFinancialsFrame` and the Finding "What this finding means in money" link.
  - Routes `SITE_FINANCIALS_ROUTE_PATH` / `SITE_FINANCIAL_ASSUMPTIONS_ROUTE_PATH`.
- **Gap:** `G-assumptions-human-edit` in `ui/gapCatalogue.ts` and in the registry `mock_gaps`.
- **Tools:**
  - `tools/s402a_assumptions_walkthrough.py`: prepare, links, serve, drop; only `assetops_s402a*` DBs.
  - `tools/s402a-assumptions-evidence.mjs`.

## Checks

- Focused backend: 47 + 57 + 5 passed.
- Full backend: **1971 passed** in 458.83s (DB `assetops_s402a_test`).
- Frontend: `tsc` clean; vitest 1465/1465; build ok.
- `check-all.ps1`: 9/9.
- Browser evidence: 69/69 (non-vacuity run 67/69 as designed).
- `layout-evidence`: 206 PASS / 28 FAIL. All failures are fixture preconditions or claims older than this slice (packet, "Checks run").
- Servers on 8900/8901/5400/5401 are stopped. The scratch DBs `assetops_s402a_evwalk` and `assetops_s402a_evempty`, plus the work folder `%LOCALAPPDATA%/AssetOps/s402a-evidence-work`, are kept for the reviewer. Remove them with the tool's `drop`.

## Deviations for the Architect batch

- **L2 (unchanged, listed only).** A SUCCESSION whose `valid_from` equals an open-ended current assignment's start is refused (`assumptions.py` strict `<`). The packet's "containing" wording would admit it. There is no schema impact.
  - Options: (a) keep the refusal, so a CORRECTION re-prices a scheduled price; (b) admit it as a full replacement of that open assignment.
  - Recommendation: (b), defined in plan code with one test.
- **Registry edited for the gap mirror (D1).** See the packet.

## Registry / ledger closeout edits needed (not made here)

- `I-S4-02a`: phase status to built/in review, citing `.agent/S4-02a-review-packet.md` and the evidence folder.
- The assumption store, read and UI nodes (or the `assumptions:1#a` and `assumptions:3` core portions): reviewed paths from `financial_read_api.py` and `SiteFinancials.tsx`. `financials:1/2` stay partial (consequence lines need S4-02b). No W1 panel promotion.
- `G-foundation-financial-assumptions`:
  - Correct its `review_trigger` to say that the link to the Site assumptions read exists (`StoredFoundationViews.tsx` `data-financial-assumptions-link`) and that the gap resolves when that link is independently accepted.
  - Set `evidence.ui` to name the link.
- `G-assumptions-human-edit`: set `evidence.reviewed_by` after review.
- Screen ledger: `assumptions` / `financials` rows may gain `gap_ids: ["G-assumptions-human-edit"]` (assumptions) when G-05 enrols those screens.

## Next

Fresh Claude review of phase 2 and the closeout, then the owner walkthrough. S4-02b follows after merge, and needs a v4 Finding-window CORRECTION step (C3).
