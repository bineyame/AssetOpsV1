# S5-02 plan review (fresh Claude Reviewer)

Reviewed: `tasks/S5-02-overview-finding-list.md` at `58e190c6` (`git diff 97851c68..58e190c6 -- tasks`), against code on the same tree.

## Verdict: ACCEPT (no High/Medium; four Lows, none blocking)

## Verified

- Seams are real: `frontend/src/sites/SiteOverview.tsx:73-94` (URL keys, served selection), `:106-159` (read, served-day write, `selectDay` drops the pin), `:186-195` (SiteWindowOverview mount); `SiteWindowOverview.tsx:575-626` (`KnownFinding` + `data-finding-list` placeholder); backend placeholder `site_overview/read.py:36` and `:214` (cited 213, off by one); `findingIndexClient.ts:20-108,192-202`; `SiteFindingIndex.tsx:263` `Loaded`, `:319` `Refused`, `:393` component; `SiteAnalyticsFrames.tsx:175-240`; route `finding_index_api.py:3,40`; `postgres_finding_store.py:407-427` (`match_state` checks `deferred_window_starts`) and `:471-480`; registry `v69-dependency-registry-pilot.json:243-244,316`; mock `index.html:410-416`, `screen-manifest.json:105-124`; both named test files exist under `frontend/src/shell/__tests__/`; `check_v69_dependency_registry.cjs` and `tools/check-all.ps1` exist.
- No backend change: holds. Overview `window.start/end` are `...T00:00:00Z` (`site_overview/read.py:69-71,184`) and the index's `_utc` accepts exactly that (`analytics/finding_index.py:92-101`); one UTC day is within 31 days; default `PAGE_DEFAULT=50` (`:44`). Both reads expose comparable basis fields (`siteOverviewClient.ts:416-424` vs index `watermarks.days[].s3.selection_seq`, `watermarks.matcher`). Backend parity on the same basis is already proven by `backend/tests/test_s4_finding_index_postgres.py:288,341-344`.
- Fail-closed: zero claim only on `CURRENT` + `is_current` + `total_count=0` + token/watermarks; non-current, 409/401/403/422/503 carry no count or empty claim; legacy Overview issues no index request; date change and late responses cannot resurrect old rows. No positive or empty claim is made without the index's own proof.
- Fixture sharing: the packet does not overclaim. The S4-04 fixture alone cannot serve the imported Overview: `site_overview/route.py:9-10` requires a PASSED S2 Evidence comparison (409 `AWAITING_EVIDENCE_MIGRATION`), and `tools/s404_finding_index_walkthrough.py` runs only the Performance comparison. The packet asks for a wrapper that passes S2/Performance and a typed stop otherwise. From `evidence/legacy_comparison.py:130-200,231+`, the S2 comparison reads only the legacy file store and its inventory; TLS ledger deliveries from the S4 producer do not change that, so running it in the S4-04 tree looks passable (as `tools/s5_overview_walkthrough.py:174-177` does). It is not proven until run, so see L1.
- Size: one frontend phase (client wiring, reuse of `Loaded`/`Refused`/rows, focused tests) plus a thin walkthrough wrapper. S with one build phase is credible.
- Architect question 1: the recommendation (assert equality only on the same settled S3/S4 basis with both rows intersecting the day, otherwise show both bases plus reload and make no equality claim) is safe and fails closed. No objection.
- Checks run: `tools/check-agent-workflow.ps1` passed; `check_v69_dependency_registry.cjs` ran clean. No suites run (plan review).

## Findings

1. **Low: the walkthrough's concrete missing step is not named.** Packet "Reproducible owner walkthrough". The only gap between the S4-04 fixture and the Overview route is the S2 Evidence comparison (`route.py:9-10`). Name it: `python -m assetops_backend.evidence_migration run --tenant demo --site KOBO-001` in the S4-04 work tree after `prepare` (pattern `s5_overview_walkthrough.py:174-177`), with the serve-time Performance re-run already in `s404...py`. Otherwise an implementer may hit the typed stop and leave the owner walkthrough unreachable. Without a schedule tick the Overview reads SCHEDULE_STOPPED freshness. That affects only money, not `known_finding` (`read.py:156-165`), so it does not block parity, but the walkthrough notes should say so.
2. **Low: the mount seam is not listed.** The index client and full-list href must be injected where `SiteOverview` is mounted (`frontend/src/shell/SiteDetailFrame.tsx:106-136`, `windowLinks`) and through the clients that frame receives, along with the test harness. Add it to "Verified seams" so the change stays in the shell composition and the Overview does not construct its own default client.
3. **Low: the preview limit is unspecified.** "A bounded limit" is left open. The positive day has at least 2 rows and the server default is 50, so the "first page only + full list" state is never owner-visible unless a small limit is fixed, such as 5. Fix the number so tests and the walkthrough are deterministic, or name the S4-04 `limit=2` URL as the way to exercise it.
4. **Low: citation drift.** `site_overview/read.py:213` should be `:214`. Cosmetic.

## Residual risk

- The S2 comparison passing on the S4-04 tree is inferred from code, not run.
- The packet already names the two-read non-atomicity (Overview stale vs index current on the same day). It relies on the UI showing both bases, which only the slice review can check.
