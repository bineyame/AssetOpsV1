# S4-02a review packet: Site price publication and exact assumption history

Task `tasks/S4-02a-site-assumptions.md` (now `in_review`). Branch `task/S4-02a-site-assumptions`.
- Phase 1: `28668d9`..`5159b96`. Reviewed in `.agent/S4-02a-phase-1-review.md` (ACCEPT with carries).
- Phase 2: `408e9e6`..`17ae9e2`, plus the records commit.
- USER_REVIEW_REQUIRED: true. Do the owner walkthrough `.agent/S4-02a-owner-walkthrough.md` after a fresh review.

## Outcome delivered

At KOBO-001, an operator opens Financials > Assumptions. It shows the following:
- the persisted diesel price (currency/L) in plain words;
- its basis, source, SYSTEM setter and recorded date;
- the effective schedule (valid time) and every recorded version;
- an exact version (`?revision_id=`) and a recorded cutoff (`?recorded_at=`). Both survive reload and back/forward.

The human edit is visibly disabled. Its reason is a catalogued gap.

From a Finding, "What this finding means in money" opens the bridge. The bridge does the following:
- holds the Finding ID and the exact FindingRevision ID;
- states `QUANTITY_UNAVAILABLE` with no amount or currency;
- links to that version's S4-03 Evidence.

Foundation's open financial-assumptions gap line gains a sibling link to Assumptions.

## Files materially changed (phase 2)

- **C1/C2:**
  - `backend/assetops_backend/financials/assumptions.py` (`PROVENANCE_NOT_DIGESTED`, `canonical_step_sha256`, digest without the authorization prose)
  - `publish_assumption.py` (`fixture_step_sha256`)
  - fixture v2 moved to 2030-01-01
  - `migrations/versions/0010_financial_assumptions.py` (L1 in the set-once trigger)
- **Reads:**
  - `financials/assumption_read.py` (new)
  - `financials/adapters/postgres_assumption_store.py` (`snapshot`, `revision_detail`)
  - `financials/composition.py`
  - `financial_read_api.py` (new)
  - `finding_api.py` (bridge route, `consequence_state`)
  - `main.py`
- **UI:**
  - `frontend/src/sites/{financialsClient.ts,SiteFinancials.tsx}` (new)
  - `shell/SiteAnalyticsFrames.tsx` (`SiteFinancialsFrame`, Finding link)
  - `shell/{operatorSiteRoutes.ts,operatorSiteTabs.tsx}`
  - `App.tsx`
  - `sites/StoredFoundationViews.tsx` (link)
  - `ui/gapCatalogue.ts`
  - `ui/primitives.css`
  - `test/settled.ts`
- **Registry:** `frontend/docs/architecture/v69-dependency-registry-pilot.json`. One `mock_gaps` entry, `G-assumptions-human-edit`.
- **Tests:**
  - backend: `tests/test_s4_assumption_read_api.py`, `tests/test_s4_assumption_read_postgres.py`, `tests/test_s4_assumptions_postgres.py` (+2 tests)
  - frontend: `src/sites/__tests__/siteFinancials.test.tsx`, plus tab-list updates in 4 existing tests
- **Tools:**
  - `tools/s402a_assumptions_walkthrough.py`
  - `tools/s402a-assumptions-evidence.mjs`
  - `tools/layout-evidence.mjs` (both tab-list claims name Financials)

## Acceptance criteria

| # | Criterion (packet) | Status | Evidence |
|---|---|---|---|
| 1 | Store: migration, immutability, set-once `recorded_to`, exclusion, containment | Met (phase 1, plus L1) | phase 1 review; `test_closing_a_current_row_before_the_series_latest_start_is_refused` |
| 2 | SYSTEM publication, change kinds, retry, concurrency, write route refusal order | Met (phase 1, plus M1/M2) | `test_replay_from_a_modified_fixture_copy_returns_the_stored_ids` (CRLF, appended v4, bumped version) |
| 3 | Read: current or at cutoff, half-open on both axes, exact ID stable, pagination, 401/403/404/503, never latest | Met | `test_s4_assumption_read_postgres.py` (5) and `test_s4_assumption_read_api.py` matrix |
| 4 | Bridge holds the exact FindingRevision; `QUANTITY_UNAVAILABLE` / `UNPRICED` typed, no amount; Evidence link | Met (`UNPRICED` is unreachable: no quantity exists) | bridge tests (API + UI); browser claims "bridge state", "links that exact version's Evidence" |
| 5 | Current/history UI: valid vs recorded, SYSTEM label, source, reload; future v2 leaves the old window; middle correction shows three slices | Met | browser: schedule v1, v3, v1, v2; cutoffs r1 → [v1] and r2 → [v1, v2] after reload |
| 6 | Plain language by default; IDs/digests/enums in details | Met | browser: 0 UUIDs in visible text, v1 ID present once details open; vocabulary scan in unit tests |
| 7 | Tab flip and routes; Finding bridge query; reload/back | Met | browser: keyboard Enter, back, forward, reload; bridge reload and Evidence back |
| 8 | Disabled edit through `<MissingClaim>` as `G-assumptions-human-edit` (`build`) with mirror | Met (registry edited; see D1) | unit test and browser gap pair; mirror guard proven non-vacuous |
| 9 | Scenarios and other unsupported content omitted and itemized for G-05; no new untagged literal | Met | orphan scan: 31 tagged / 12 baselined (unchanged baseline); itemized below |
| 10 | Foundation `G-foundation-financial-assumptions` links to the Site read, or the gap stays open | Met: link added, gap stays open | browser claim; `siteFoundationRevision.test.tsx` |
| 11 | No priced amount, maintenance, scenario, FX or extrapolation | Met | `consequence_state(..., True, True)` raises; no amount in the bridge DOM |

**Itemized for G-05, not rendered:**
- `financials`: Scenarios subtab; metric cards (operating-cost exposure, revenue/service, asset exposure, realized savings); panel 1's consequence table (beyond the one bridge state); the second (maintenance) line; panel 3 "Trade-offs and exclusions"; portfolio roll-up.
- `assumptions`: panel 2 "Impact preview"; maintenance accrual; the interactive price input and "Apply example price"; "Proposed next version" history row.

## Checks run (counts)

- **Backend:**
  - Focused: `test_s4_assumptions_postgres.py` + `test_s4_assumption_publication.py` 47 passed; `test_s4_assumption_read_api.py` + `test_s4_assumption_publication.py` + `test_s4_finding_api.py` 57 passed; `test_s4_assumption_read_postgres.py` 5 passed.
  - Full: **1971 passed** in 458.83s (`assetops_s402a_test`; phase 1 was 1953).
- **Frontend:**
  - `npx.cmd tsc --noEmit` clean.
  - Full `npx.cmd vitest run`: 62 files, **1465 passed**.
  - `npm.cmd run build` ok (chunk-size warning only).
- **Guards:** `tools/check-all.ps1`: **all 9 guards passed**.
- **Non-vacuity (each on committed work, reverted with `git checkout --`):**
  - Re-digesting `fixture_sha256` gives `IDEMPOTENCY_KEY_REUSED` in the replay test.
  - Disabling L1 gives DID NOT RAISE.
  - Deleting the registry gap gives `mirror_unknown`.
  - `S402A_ALTER=1` fails exactly the 2 schedule claims (67/69).
- **Browser evidence:** `node tools/s402a-assumptions-evidence.mjs` at 1440/390 gave **69/69 PASS**, with screenshots (app and mock) in `%LOCALAPPDATA%/AssetOps/evidence/s402a`.
- **Layout evidence:** `node tools/layout-evidence.mjs` on the Finding-case store gave 206 PASS / 28 FAIL.
  - All 28 failures are fixture preconditions or claims older than this slice:
    - no MG-001 Lab Site, so the Site-page tab claims read 0 tabs;
    - no Foundation diagram;
    - the T011A "Overview, Foundation, Evidence" claim.
  - This store cannot exercise them, so the Site-page tab claim is **unverified by layout-evidence**. Six-tab rendering and no page overflow at 1440/390 are measured by the slice tool instead.

## Known deviations

- **D1: the registry was edited.** The packet says "this plan does not edit the registry". The missing-claim mirror guard requires `gapCatalogue.ts` to equal the registry `mock_gaps`, so one `mock_gaps` entry was added. No node, status or ledger change was made.
- **D2: L2 is unchanged and listed for the Architect batch.** A SUCCESSION exactly at an open-ended assignment's start is refused (`assumptions.py`, strict `<`).
- **D3: the bridge route is Finding-scoped.** It is `/api/sites/{site}/findings/{id}/financials`, an equivalent Site-scoped route as the packet allows. `UNPRICED` is typed and tested, but no path produces it, because no technical quantity exists.
- **D4: read access.** Reads use the Finding read's `development_access` (in a separate module, `financial_read_api.py`). The write module still never imports it.
- **D5: a 422 is mapped to "not found".** The UI client maps 422 (for example a malformed revision ID) to `not_found`.
- **D6: the Foundation gap stays open.** Its `review_trigger` correction is a registry closeout edit, listed in the handoff.

## Residual risk

- **Shared recorded day.** All three fixture versions are recorded within one second, so "Prices as recorded then" differs only by sub-second cutoffs. This is honest but subtle to demo.
- **Overlap rules live in plan code.** The database enforces only non-overlap and monotonic time (phase 1 residual).
- **Fixture source text.** The demo source reference says "demonstration fixture"; it is honest data, not product copy.

## User-review focus

- the wording of the disabled edit;
- "Not calculated" as a finding's cost today;
- the plain first sentence of Assumptions;
- whether the Schedule plus History reads clearly at 390 px.
