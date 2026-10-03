# T027 phase 2 review packet - the mini-grid Site Overview

## Task

`tasks/T027-commit-ingestion-and-site-overview.md`, phase 2: ACs 11 and 22 in
full; 10 (each card names its coverage), 12 (Overview evidence links), 13, 14, 15
and 19 extended to the Overview read model. Branch
`task/T027-commit-ingestion-and-site-overview`, from 593d2ff. Phase 1 evidence:
`.agent/T027-phase-1-review-packet.md` (owner UI check successful, 2026-10-03).
USER_REVIEW_REQUIRED: true. Status stays `in_review`.

## Outcome delivered

`/sites/{id}` (the Overview tab) now opens with the Overview body. It has the
objective strip (site assessment "No assessment yet", service delivered, window,
evidence count with a link to Site > Evidence), then one card per profile domain
in the order Service, Dispatch, Battery, Fuel, Renewable. Each card shows "No
assessment yet", measured metrics with units and the time of each instant, the
signals it reads with their coverage counts, and, when uncovered, a named
coverage gap with no value. Below the cards are the selected-window timeline
(demand, PV and generator in kW; SOC in %, on separate axes) and Findings ("no
analytic has assessed this site yet"). Every metric's evidence link opens the
Site > Evidence record inspector at `/sites/{id}/evidence?signal=DEV/SIG&record=MSG`.
All of this comes from `GET /api/sites/{id}/overview`, which is computed from
accepted evidence only and served beside the Site evidence routes, with the Lab
gate open or closed.

## Files materially changed

- Backend:
  - `evidence/overview.py` (new: `OverviewReadModel`, `DOMAIN_METRICS`).
  - `evidence/read_model.py` (`OVERVIEW_DOMAIN_SIGNALS`; `NEEDED_SIGNALS` derived from it; `default_window`, `in_window`).
  - `evidence_api.py` (`SITE_OVERVIEW_ROUTE`, documented payload).
- Backend tests:
  - `tests/test_t027_overview.py` (new, 14 tests).
  - `tests/t027_isolated_probe.py` (`build()` now includes `overview`).
  - `tests/test_t027_ingestion.py` (the rebuild snapshot includes the Overview; the isolated test asserts on the Fuel card).
  - `tests/test_health.py` and `tests/test_sites_api.py` (exact per-Site route lists gain `/overview`).
- Frontend, substrate:
  - `sites/SiteOverview.tsx` (new).
  - `sites/siteOverviewClient.ts` (new).
  - `sites/presentationProfile.ts` and `sites/presentationProfiles.json` (new: the profile).
  - `sites/SiteDetails.tsx` (`overview` slot; the "Not available for this site" panel removed).
  - `sites/siteEvidenceClient.ts` (read helpers exported).
- Frontend, shell:
  - `shell/SiteDetailFrame.tsx` (fills the slot).
  - `shell/operatorSiteRoutes.ts` (`siteEvidenceRecordHref`).
  - `App.tsx` (`siteOverview` client).
- Frontend, shared:
  - `ui/primitives.css` (Overview styles, `.overview-timeline__scroll`).
  - `test/settled.ts` (the loading sentence).
- Frontend tests:
  - `shell/__tests__/siteOverviewScreen.test.tsx` (new, 13 tests).
  - `sites/__tests__/overviewFixtures.ts` (new).
  - `sites/__tests__/siteDetail.test.tsx` (the removed panel's assertions replaced).
- Checks and tools:
  - `tools/checks/shell-overflow.ps1` (a fourth svg module under the same region rules).
  - `tools/layout-evidence.mjs` (T027 phase 2 Overview cases).
- Records: `.ai/CODE_STATE.md` ("T027 phase 2"), `.ai/ACTIVE_CONTEXT.md`, and the task file's Review line.

## Acceptance criteria (phase 2 scope)

| AC | Status | Evidence |
| --- | --- | --- |
| 10 coverage names Overview signals and window; no carry-forward | met | `NEEDED_SIGNALS` is derived from `OVERVIEW_DOMAIN_SIGNALS` (overview::test_needed_signals_are_derived_from_the_domains). Each card carries per-signal coverage and named gaps (::test_an_uncovered_card_names_its_gap_and_has_no_value, ::test_unavailable_records_are_counted_never_filled). Energy and runtime count measured intervals only (::test_metrics_sum_measured_intervals_only, where the 10 unmeasured minutes are not counted). Overlaps are used by no metric (::test_overlapping_records_are_neither_summed_nor_replaced). |
| 11 window/context, metrics with units, evidence links; "No assessment yet"; no invented result; never "Unknown" | met | overview::test_every_card_is_no_assessment_yet_and_nothing_is_unknown. The screen tests "shows No assessment yet on every card and never Unknown", "shows the objective strip...", "links a metric's evidence..." and empty "names every gap..." cover the UI. Findings is empty, with a neutral statement. |
| 12 Overview evidence links open the inspector, root unchanged | met | Screen test "links a metric's evidence to the record inspector without changing the Site root" (clicks, lands on the record detail with Evidence current). overview::test_evidence_links_name_accepted_records; route test resolves a link through `/evidence/records/{id}`. The layout run clicks one link in a browser (below). |
| 13 gate off: Overview remains | met | overview::TestOverviewRoute::test_served_with_the_gate_closed_from_accepted_evidence_only and ::test_a_closed_build_still_reads_overview_beside_evidence. The screen test "renders the same Overview with the Lab gate closed and open" covers the UI. |
| 14 rebuild matches | met | ingestion::TestRebuild snapshot now includes `OverviewReadModel.site_overview`; it matches after `clear_derived()` and re-ingest. |
| 15 rebuild without simulator/host | met | `t027_isolated_probe.build()` includes `overview`. TestRebuildIsolated (`python -I`, blocker) equals the in-process payload, `leaked == []`, and the Fuel card reads 100. Non-vacuity: appending `import assetops_simulator` to `evidence/overview.py` failed it with `ImportError: blocked`; reverted. |
| 19 gate off: accepted evidence alone feeds views | met | As AC13. The Overview module is under the evidence dependency rule (`dependency-direction.ps1` scans `evidence/**` and `evidence_api.py`); architecture check passes. |
| 22 profile is substrate data keyed by `site_type`, owns only which cards and their order; state never from it | met | `presentationProfiles.json` holds `{id, label}` per card only (overview::test_the_profile_owns_no_card_state). Profile and backend domains are pinned equal in order (::test_the_profile_cards_are_the_backend_domains_in_order; non-vacuity: adding a "Grid" card failed it; reverted). Screen tests order backend cards served out of order by the profile, render nothing for an unserved profile card, and keep the backend card objects as state. |

Phase-1 ACs are unchanged (phase-1 packet).

## Checks run (final, at 1968dde plus records)

- Backend `pytest -q`: 1431 passed (phase-1 baseline 1417; +14). The first full run had 3 failures, all exact route-inventory pins missing `/overview` (`test_health`, `test_sites_api` x2). They were fixed in 06baefa and the rerun is clean.
- Host: 602 passed (baseline 602). Simulator, run from `simulator/`: 244 passed (baseline 244).
- Frontend `vitest run`: 1068 passed, 43 files (baseline 1056; +13 Overview, net -1 in siteDetail). `tsc --noEmit` clean. `npm run build` clean.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Guard non-vacuity:
  - Renaming `.overview-timeline__scroll` in CSS failed `shell-overflow.ps1`; reverted.
  - The N9 pin and AC15 proofs are listed above.
  - All were run on committed work and restored with `git checkout`.

## Layout evidence

Command, as in phase 1:
`ASSETOPS_LAYOUT_SITE=MG-006 ASSETOPS_KOBO_SITE=SITET26 node tools/layout-evidence.mjs http://localhost:4173`.

Setup:

- The production build was served by `vite preview`.
- `host/lab_app:app` ran on port 8000 from a fresh `git archive HEAD` copy.
- That copy's `var/` holds the sites (with `valid_from` backdated in the copy only), the scenarios, and the `.demo/T025c` runs. It had no evidence, commits or executions.
- `PYTHONPATH` pointed at the copy, so the editable installs could not reach the working tree's `var/`. I verified this: `EVIDENCE_STORE_ROOT` resolved inside the copy.

Output: `.agent/T027-phase-2-layout-evidence.txt`. The result was **514 PASS, 4 FAIL**. The four failures are exactly phase 1's pre-existing ones: three "blocked table" claims (the MG-006 setup is READY) and the T025e 50 ms p95 delta budget (75.6 ms this run).

Every T027 Overview claim passes:

- **Populated, SITET26, at 1280/1000/640:**
  - Cards come in profile order.
  - "No assessment yet" appears on 5 of 5 cards, and "Unknown" appears nowhere.
  - The non-empty measured set is Service 4 values, Dispatch 3, Battery 3, Renewable 2. Fuel has 0 values and 1 named gap.
  - There are 17 evidence links, all addressed to the inspector.
  - The timeline has 96 kW marks and 32 % marks. The charts are 951/671/320 px wide.
  - At 640 the chart overflows its own region, which scrolls (`overflow-x: auto`), so the containment claim is measured on a non-empty set. The page never scrolls horizontally.
  - The tab row reads Overview|Foundation|Evidence with Overview current.
- **An evidence link clicked** opens `/sites/SITET26/evidence` with that record in the inspector and Evidence current.
- **Empty, MG-006, at 1280/640:** five cards, each "No assessment yet" with named gaps and no value, no chart, and no horizontal scroll.

Two earlier runs are recorded for honesty; neither is the evidence:

- **Run 1** (same method, 507 PASS / 11 FAIL) found two measurement bugs in my new claims. Its current-tab read hit the rail. Its timeline claim forbade a chart wider than its region even when that region scrolls. Both were fixed in 1968dde. Run 1 also failed two Lab claims outside this slice: T025b profile 4 "unstaged none" and T026 "delayed reading named". Neither repeated in run 3.
- **Run 2** stopped early in the Lab run-setup step ("did not find the controls it drives"). That step does not repeat in run 3, and this slice does not touch it.

The gate-closed browser pass was not run, as in phase 1. Gate-closed behaviour is covered by the backend and frontend tests listed under AC13.

## Known deviations

1. **The profile, not the backend, decides which Overview cards exist.** A backend card that the profile does not list is not rendered. This follows AC22, and decision `D-2026-10-02-presentation-profile-and-capability-declaration`, which applies the "unknown backend id still renders" rule to backend capability ids rather than to Overview domain cards. Drift is caught by the backend pin test, not on screen.
2. **The profile lives in `frontend/src/sites/presentationProfiles.json`**, and a backend test reads it. That test is the only cross-tree read. It is a pin, not a runtime dependency.
3. **The objective strip shows no "confidence".** No analytic exists, so any confidence would be invented. The strip shows assessment, service delivered, window and evidence count.
4. **The Overview page's "Not available for this site" panel is removed.** Its "no accepted evidence" sentence is false once a Commit is ingested. The Overview now states evidence from the evidence. Integration readiness and source health are no longer listed on the Overview page.
5. **The overflow guard was extended, not loosened.** `SiteOverview.tsx` is a fourth svg module under the same three rules.

## Residual risk

- **Measured-interval energy covers about a third of the window.** Kobo v3 interval means cover the 5-minute timestep before each 15-minute report. On the demo run, the 8 h window has 2.67 measured hours, so served energy reads 67.3 kWh. Each value states its measured hours and says it is "measured intervals"; it is not an estimate of the whole window.
- **The demo Fuel card shows a coverage gap.** The profile-5 run stages no fuel-level envelopes. This is honest, and expected.
- **The Foundation tab still states "No evidence"** for a Site with accepted evidence. That is the pre-existing `SiteConfiguration` panel, outside phase 2. A fast-lane fix is suggested.
- **The timeline below 20rem scrolls inside its region.** At 640 it is 9px wider than its column. The page does not scroll.
- **Generator running time counts measured intervals with output above zero.** Status samples are shown separately as "N of M reading RUNNING". Nothing between samples is inferred.

## User-review focus (owner demo point 1)

Demo point 1 journey (recommendation 5.2 row 1): Lab run -> stage -> Commit ->
Sites -> Kobo Overview -> Evidence -> Lab off, history stays.

1. Run a Kobo mini-grid scenario to completion in the Lab, stage it, then Commit and release.
2. From Sites, open the Kobo Site. On the Overview, check the following:
   - The objective strip reads "No assessment yet" and shows the window and the accepted-record count.
   - Five cards appear, in the order Service, Dispatch, Battery, Fuel, Renewable.
   - Each card reads "No assessment yet". "Unknown" appears nowhere.
   - Each value carries its unit, and "measured intervals" with its hours where relevant.
   - The Fuel card names its gap (`fuel-level-sensor/fuel-level`) and shows no number.
3. Click any metric's evidence link. The Evidence tab opens with that record in the inspector, showing three timestamps, and the Site root is unchanged.
4. Look at the timeline. kW and % are on separate panels, with a legend, and the timeline is context only.
5. Restart with `simulator_lab.enabled` false. The Overview and Evidence still show the same accepted history, and the Lab is gone.
6. Judge the energy wording. In the strip, Service delivered reads
   "Served energy, measured intervals", then "67.3 kWh", then "2.67 h of the
   8.00 h window measured", then the feeder basis "(residential feeder 2.67 h,
   clinic feeder 2.67 h, mill feeder 2.67 h)". These are the demo run's figures
   (fix round 1, F3). Is that clear enough for a demo, or should a later slice
   change cadence or how it is presented?
7. Open Foundation. It no longer states "No evidence" or "Source health: Not
   recorded"; it says nothing on the tab is evidence and points to the Evidence
   tab (fix round 1, F2).

## Fix round 1

Review: `.agent/T027-phase-2-claude-review.md` (accept with fixes, 6035bcb).

| Finding | Disposition |
| --- | --- |
| F1 coverage from the records a metric uses (must) | Fixed in 01b1326 and a71dc8c. `_Window.usable(key)` is the record set a metric reads: non-overlapping records, with a positive interval span for interval-mean signals (`INTERVAL_SIGNALS`). New coverage statuses `NO_INTERVAL_SPAN` and `OVERLAPPING_ONLY` sit beside `NOT_REPORTED` and `NO_GOOD_RECORD`, each with a named `reason` in `gaps`. `unavailable_because` names the signal and the reason. A span-less interval signal has no value, so "0.0 kWh over 0.00 h" is no longer shown. An overlap-only feeder makes Served energy unavailable and names the feeder. Coverage rows also gain `usable`. Tests: overview::test_all_overlapping_instants_are_a_named_gap_not_a_bare_absence, ::test_an_interval_signal_with_no_span_has_no_value_never_zero, ::test_an_overlap_only_feeder_is_not_counted_as_zero, and screen "names an overlap-only signal's gap with the backend's reason". Non-vacuity: with `usable()` reverted to the old any-GOOD rule, all three backend tests failed; reverted. |
| F2 Foundation false facts (must) | Fixed in 2fafa71. `SiteDetailView` no longer carries `evidenceAvailability` or `sourceHealth`, and their constants are gone. The Foundation panel keeps Integration readiness and says: "This tab states the site's configuration, and nothing on it is evidence. What has been accepted for this site, the health of each source that delivered it and its coverage are on the Evidence tab." Tests: siteConfiguration "states no evidence availability or source health on the Foundation (T027)"; the siteDetail view test asserts both keys are absent. |
| F3 strip truthful about coverage | Fixed in a71dc8c. Interval metrics carry `window_note`, e.g. "2.67 h of the 8.00 h window measured", rendered under the value. The strip shows the metric's label ("Served energy, measured intervals") before the value. User-review focus point 6 now quotes the screen. Tests: overview::test_metrics_sum_measured_intervals_only checks `window_note`; the screen strip test checks both strings. |
| F4 response shape check | Fixed in a71dc8c. `isSiteOverview` checks every rendered field: metric `at`, `window_note` and `unavailable_because`; evidence items; gap `reason`; coverage counts; card and objective assessment; the three statements; timeline `basis` and each point. Test: the real client over a stubbed `fetch` reads a response missing `unavailable_because` as `unavailable`. Non-vacuity: removing that key from the check failed it; reverted. |
| F5 strip count name | Fixed. `source_gateway_pairs_in_window`; the strip says "source and gateway pair(s)". |
| Generator running time | Carried to `.ai/MILESTONE_REVIEW_BACKLOG.md` "Carried from T027 phase 2" (T028), as the dispatch asked. |

Also carried, as an observation that is not a finding: `shell/RunSetupFrame.tsx` and `shell/RunsFrame.tsx` still explain a draft as never executed, with "no accepted evidence". That was already false since T022. Both are Lab-only screens, and a fast-lane wording pass is suggested.

**Checks after the fix round (at 1159420):**

| Check | Result | Change |
| --- | --- | --- |
| Backend | 1434 passed | +3 |
| Host | 602 passed | - |
| Simulator (from `simulator/`) | 244 passed | - |
| Frontend (43 files) | 1071 passed | +3 |
| `tsc --noEmit` | clean | |
| `npm run build` | clean | |
| `check-architecture` | passed | |
| `check-agent-workflow` | passed | |

**Layout evidence rerun** (Overview rendering changed): same method, on a fresh copy and a rebuilt preview. Output: `.agent/T027-phase-2-layout-evidence-fix-round-1.txt`. Result: **513 PASS, 5 FAIL**.

- **The four known pre-existing failures:** the three "blocked table" claims and the T025e delta budget (p95 73.3 ms).
- **The T026 "held publication: a delayed reading is named" claim:** this is the same intermittent Lab claim that failed in run 1 and passed in run 3. It sits outside this slice.
- **Every T027 claim passes,** with the same populated, link-click and empty results as before at 1280/1000/640. At 640 the region again overflows and scrolls.
