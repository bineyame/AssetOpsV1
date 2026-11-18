# T027 phase 1 handoff

Phase 1 (Commit, ingestion, Site > Evidence, tab rule, `/` redirect) is built,
committed on `task/T027-commit-ingestion-and-site-overview` and in review.
Packet: `.agent/T027-phase-1-review-packet.md`. Layout:
`.agent/T027-phase-1-layout-evidence.txt`.

## What landed

1a tab rule/AC23 (53a5ac3); 1b contracts + ingestion/evidence backend
(06a2829..b6a1238); 1c commit store/routes + host proofs (a55ffe7..8a722b4);
1d Evidence UI + Commit panel (f0b30ee..a940f10); 1e layout evidence, the 640px
record-heading fix (5c19e90), dead tab CSS removal (d26d6e2), records.

## Anchors for phase 2 (Overview, AC11, AC22)

- Evidence read model: `backend/assetops_backend/evidence/read_model.py`
  (`EvidenceReadModel` :141; coverage uses `NEEDED_SIGNALS` :51, keyed by
  `site_type` "MINIGRID", read at :229). AC22's presentation profile (cards and
  order) is a separate substrate; the needed signals may become its per-card
  coverage, but card state must come from accepted evidence, not the profile.
- Evidence API: `backend/assetops_backend/evidence_api.py` (`SITE_EVIDENCE_*`
  routes :103-106); the Overview read belongs beside them (gate-independent).
- Frontend Evidence: `frontend/src/sites/SiteEvidence.tsx` (`SiteEvidence` :68,
  `SignalCoverage` :294, `RecordInspector` :456, `RecordDetail` :612),
  `sites/siteEvidenceClient.ts`. Overview evidence links should reuse the
  inspector URL: `/sites/{id}/evidence?signal=DEV/SIG&record=MSG`.
- Overview route: `frontend/src/App.tsx` :145 (`SITE_DETAIL_ROUTE_PATH`),
  tab inventory `frontend/src/shell/operatorSiteTabs.tsx` :73, current body
  `frontend/src/sites/SiteDetails.tsx`.
- Layout: `tools/layout-evidence.mjs` T027 section (after T026; `t027.run` is
  the committed profile-5 run, `KOBO_SITE` its Site). Add Overview populated and
  empty there. Run it as the packet's Layout evidence section says (isolated
  copy, `ASSETOPS_LAYOUT_SITE=MG-006 ASSETOPS_KOBO_SITE=SITET26`, preview build).

## Next

Owner phase-1 UI check (packet "User-review focus"), then phase 2: Overview
cards Service, Dispatch, Battery, Fuel, Renewable from Kobo v3 signals; neutral
"No assessment yet"; uncovered card names its gap; full suites and final packet.

## Open risks

- Fuel: the profile-5 run stages no fuel-level-sensor envelopes, so the Fuel
  card will show a coverage gap in the demo unless publication changes.
- AC15 rebuild is in-process; a subprocess proof without host/simulator on
  `sys.path` would close it.
- Evidence store is one JSON per Site, single-process lock.
- Layout script carries 3 environment "blocked table" failures and the T025e
  delta budget miss (from T026).

## Fix round 1 notes for phase 2

- N9: keep one list of Overview signals. `NEEDED_SIGNALS` in
  `backend/assetops_backend/evidence/read_model.py` and the AC22 presentation
  profile (substrate data keyed by `site_type`) must not drift: derive the
  needed signals from the profile's cards, or pin the two equal in a test.
- AC15 is now proven for Evidence by `backend/tests/t027_isolated_probe.py`
  (`build()`); extend `build()` to the Overview read model and the existing
  isolated test covers it.
- AC15 isolated test no longer needs the "AC15 rebuild is in-process" risk above.

