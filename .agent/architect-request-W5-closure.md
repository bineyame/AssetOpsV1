# Architect request: close the W5-01 and W5-03 readiness gate

You are the AssetOps Architect. The independent readiness review `.agent/W5-readiness-review.md` found both specs NOT READY: W5-01 has 13 BLOCKERs and W5-03 has 11, among 46 items. Read it, `.agent/W5-01-build-spec.md`, `.agent/W5-03-build-spec.md`, and `.ai/ROLE_CONFIG.md` ("Build-Spec Readiness Gate For W5 And W6" and the 13 lessons).

Close EVERY BLOCKER and NOTE with a literal artifact verified against merged code. Literal artifacts are:
- the exact copy per state, including `NOT_CONFIGURED`;
- a DTO, column or constraint table;
- a refusal table;
- a route;
- a producer command with its real clock;
- the registry rows, written out in full (area, requires, status, reason);
- the file list per unit;
- a test name.

Specifically:
- **Clocks:** re-derive every pinned clock and historical cutoff from the merged producers. Cold evidence is stamped with wall-clock time; the EV chain watermark is 09:00/09:05. Where a producer cannot reach a state, specify the producer change, or a new producer, in a named unit.
- **Unit file lists:** add the missing files to each unit's list: `ColdAssessmentViews.tsx`, `EvAssessmentViews.tsx`, `EvSiteViews.tsx`, and the nested `cold_site_api.opened`.
- **Cold Scenarios tab:** rule how its unavailable label is replaced, given that it is shared with other non-mini-grid Sites.
- **Scenario store (C4 and E5):** give the full spec, including the migration columns and constraints, the POST body, the write refusals, the pending list field, and the historical predicate.
- **Cooling and cold Health copy:** give the copy for every state, including source roles for context rows and the backup-failed fixture's door events.
- **Health pages:** rule whether the gateway "Data sources" panel stays on the cold and EV Health pages, matching v69.
- **EV:**
  - the availability hold rule, without the non-existent "declared state validity end";
  - the "no battery" Foundation, or drop `Not applicable`;
  - the Energy and EV Scenarios routes, and the Session-detail link destination;
  - the status-gap and no-schedule producers;
  - the metered-energy baseline table.
- **Size:** split E1 if it is more than one builder run. Re-split any sub-slice that grows past the size cap.
- **Stale text:** remove the outdated check-all and `.venv` sentences. The reviewer ran all 11 guards and they pass, including the estate self-test.

Update both specs in place, so that each unit card is the single current source; do not append a rulings log. Update the task packets, the README rows if they change, and the registry if the spec says so. Append an amendment line to `D-2026-10-22-w5-01-w5-03-buildspec`. At the end of each spec, add a "Readiness closure" table: each review item number, then the closing artifact location. Write nothing else. Do not commit.
