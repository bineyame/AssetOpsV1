# S5-01 phase 1 handoff - scoped imported-Site Overview read

Branch `task/S5-01-site-overview` (stacked on LR-01 `3b360af5`, unmerged). Phase 1 only; no UI. Build commit `c21f279f`, guard commit follows it.

## What landed

- `backend/assetops_backend/site_overview/` (new package)
  - `read.py` `SiteOverviewRead.read(site_code, tenant_id, site_id, day, *, access_basis, source_open, source_reason, pinned)` builds `site-window-summary-1`.
    - Order of reads: accepted-source fence, `UpstreamCurrentness.window`, a second `dispatch_read.window` fenced on run/window revision, ledger context, then the fence again.
    - Finding choice: `intersects` (half-open) and `choose` (greatest start, then smallest UUID). Merged Findings are excluded via `finding_detail(...).relations.merged_into`.
    - Money: exact consequence read with the real `source_open`, plus a head fence against the seam's `head_consequence_revision_id`.
  - `money_state.py`: the pure precedence function `money_state(MoneyInputs)` and the 15 no-amount states plus `PRICED`.
  - `route.py`: `SiteOverviewRoute.serve`. Order: access 401/403, then `scope`, then S2 `imported_scope` (409, also 409 when there is no comparison reader), then UTC day 422s, then the pin, then the Performance gate, then the read. `selected_day` and `legacy_window` handle date parsing.
  - `composition.py`: `build_site_overview_read(database_url, ledger, thresholds, environment)`. It uses the production `build_consequence_read_service`, which wires the persisted LR-01 gate (Architect LR-01 deviations item 5).
- `evidence_api.py`: `build_evidence_router(..., site_overview=None)`. The existing Overview handler delegates to it first. For legacy Sites, `date=` becomes a midnight `from`/`to` pair. No new route.
- `main.py`: the Performance gate block moved above the evidence router include, so the delegate gets the same `performance_gate`. One `SiteOverviewRead` per app, disposed on shutdown. Store failures are typed 503 `SITE_OVERVIEW_UNAVAILABLE`.
- `evidence/adapters/postgres_evidence_ledger.py`: new read `accepted_fingerprint(t, s, lo, hi)`. It returns the count and the sha256 of the accepted IDs, ordered by ID, using the S3 interval-overlap test.
- `tools/checks/dependency-direction.ps1`: a new S5 guard. `site_overview/` may not import simulator, host, runs, Lab or adapters, and only its `composition.py` may import other domains' compositions. The guard has an anti-vacuity check.

## Choices to review (Known Deviations for the packet)

1. **N3: pinned Finding.** Optional `finding_id` and `finding_revision_id` query parameters, checked against scope. An unknown or foreign ID returns 404 `FINDING_PIN_NOT_FOUND`; `finding_revision_id` without `finding_id` returns 422. The pin is kept (`selected_by: PINNED_RETAINED_WHILE_BASIS_INCOMPLETE`) while discovery is incomplete (fence moved, or any S3, S4 or schedule blocker) or while the source is closed. Once settled, the fresh choice wins and `previous_pin` is reported. A stateless read with a moving basis returns the provisionally discovered Finding with no amount. `ABSENT` requires complete discovery and upstream `CURRENT`.
2. **Architect LR-01 deviations item 2.** S5 takes the raw gate from its own exact `ConsequenceReadService.read` (`money.eligibility`), not from the seam's `findings[].money_eligibility`. The seam rewrite in `scheduling/upstream.py:186-193` is therefore unused by S5. **`scheduling/upstream.py` was not touched.** Upstream status and reasons are reported separately (`money.upstream`, `freshness`). Proved in both the unit and Postgres tests: after a stopped schedule the raw gate is still `ELIGIBLE`, the state is `UPSTREAM_STALE`, and the freshness reasons include `SCHEDULE_STOPPED`.
3. **Precedence vs. the owner walkthrough wording.** The packet precedence puts upstream before the LR gate. After `attest` and before `tick`, the visible state is therefore `UPSTREAM_STALE` (reasons `S3_STALE_PROJECTION`, `LIVE_JOB`), while the raw `money.eligibility.state` is `PENDING_REASSESSMENT`. The phase-2 UI and walkthrough must show both. A late acceptance likewise reads `UPSTREAM_STALE` (an older result exists), not `UPSTREAM_PENDING`.
4. **Upstream blockers that are only consequence work** (`WORK_OUTSTANDING`, `STALE_NO_WORK`, `CONSEQUENCE_*`) fall through to the per-Finding checks, so they give `CONSEQUENCE_*` and never an amount. Every other code, including unknown ones, gives `UPSTREAM_<status>`. A moved fence gives `UPSTREAM_PENDING` with freshness `STALE_PROJECTION`.
5. **Context `gaps`** is null with `gaps_reason`, because there is no reviewed gap rule. Context gives ledger coverage per device/signal and up to 500 accepted readings (`truncated` flag) with evidence links.
6. **N2.** The provenance input is the single `Provenance` callable (default `demonstration_case`). The unverified label always gives `MIXED_OR_UNKNOWN_SOURCE`. S4-05 replaces this input.
7. **Proof layering.** Exact-midnight end, merge-superseded, several Findings, unknown minor unit, failed upstream, moved selection and moved head are proved with fakes (`test_s5_overview_read.py`). The real-Postgres walk (`test_s5_overview_postgres.py`, LR-01 `Walk` plus a real schedule tick) proves the following on the existing route: the S2 409, unassessed, pending, `QUANTITY_UNAVAILABLE` (a real `POWER_COVERAGE_GAP` before the late mean), late pin retention, `WITHHELD_GENERATOR_SERIES`, attest, `PRICED` 15.82 at the exact head with exact links, same-day reload, stopped schedule, source closed with pinned audit, and a foreign-tenant pin 404. `UNPRICED` is unit-only, because in the fixture the quantity gap precedes the price.

## Checks run (phase 1)

- `pytest backend/tests/test_s5_overview_read.py backend/tests/test_s5_overview_postgres.py`: 28 passed (24 s), on the private DB `assetops_s501_test`.
- Focused and adjacent tests, `-n 2 --dist loadfile`: see the result below.
- Mutations. Each made `test_s5_overview_read.py` fail, and each was reverted with `git checkout`:
  - source-closed removed: 3 failed
  - withheld removed: 2
  - head fence removed: 2
  - basis-moved removed: 2
  - provenance removed: 2
  - upstream-first removed: 7
  - `presented_as_current` ignored: 1
  - LR gate moved before upstream: 1
  - route S2-None branch removed: 1
- The S5 guard was proven with an adapter import and with a foreign composition import in `read.py` (see below).

## Next (phase 2)

UI in `frontend/src/sites/SiteOverview.tsx` and `siteOverviewClient.ts`, with a new S5 branch that parses `site-window-summary-1` and derives nothing. The URL carries `date`, `finding_id` and `finding_revision_id`. Also due in phase 2: `tools/s5_overview_walkthrough.py` (reuse `tools/s402c_late_power_walkthrough.py run|attest|tick|serve|drop`, per N4), `tools/s5-overview-evidence.mjs`, the layout evidence, the full suite, the review packet, and the CODE_STATE entry. N5: P01 (10-23) can lose its amount between `attest` and `tick` because P02 sits in its bracket. That is fail-closed, so state it in the walkthrough.

## Risks

- LR-01 fix round: removing the seam rewrite does not change S5. If LR-01 changes the shape of the `ConsequenceReadService.read` keys, S5 must follow.
- `main.py` ordering moved (the Performance gate block is now before the evidence include). The coordinator should check this against any LR-01 `main.py` edits.
- No files from LR-01 itself were edited. Files edited outside the new package: `evidence_api.py`, `main.py`, `postgres_evidence_ledger.py`, `dependency-direction.ps1`.
