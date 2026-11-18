# Architect request: close the W6-01 readiness gate

You are the AssetOps Architect. The independent readiness review `.agent/W6-01-readiness-review.md` found W6-01 NOT READY, with 16 BLOCKERs and 20 NOTEs. Read it, `.agent/W6-01-build-spec.md`, `.agent/W6-01-mock-measure.md`, and `.ai/ROLE_CONFIG.md` ("Build-Spec Readiness Gate For W5 And W6" and the 13 lessons).

Close EVERY BLOCKER and every NOTE with a literal artifact, verified against merged code. Literal artifacts are:
- a DTO field table;
- a refusal and status table;
- the exact copy;
- a route;
- a producer command;
- the registry path;
- the file list per unit;
- a cap in px;
- a test name.

Specifically:
- Use Site route identity as code actually does it (`sites_api.py:212`).
- Decide the global-root parser, refusal and default-window rules consistent with the merged W3-01/W3-03 estate roots.
- Give a full row DTO per root.
- Give producers for the historical, correction, cursor, linked, PARTIAL and EMPTY_SCOPE states (more than one fixture clock is allowed if needed; one clock per fixture).
- Give the UI page size and per-panel height caps at 1440/390.
- Give the long-title rule. Unbroken 200-character titles overflow the page at 1440 and 390; choose wrap or ellipsis with full text in a named disclosure, as v69 and earlier waves do.
- Give an atomic rail/test/fixture change carried by a named unit, with every test file it must edit.
- Fix the tab guard and merge-order conflict, and the E2 write identity and permissions, or cut E2 if no honest write path exists.
- Fix the `operational_record.case_id` notice.
- Give the history event labels.

The measurement worst-case pass was incomplete: long titles were never injected into table cells, the 4000-character text missed the incidents, maintenance and preventive tables, and the header, tabs and chips were not measured. Re-measure those with `tools/measure-mock-panels.mjs` plus an injection, if your sandbox can run a browser; the W5 spec pass did measure successfully. If you cannot, set caps from the design rule and list the exact extra measurements still needed.

`P-work-cases` in the registry is "pending owner". By owner precedent (2026-10-17 and `.agent/owner-W3-W4-wave-start-2026-10-20.md`), scope decisions proceed on the Architect's recommendation, recorded as not yet owner-accepted. Give your recommendation and record it that way.

If closing a blocker grows any sub-slice past the size cap, re-split it.

Update `.agent/W6-01-build-spec.md` in place so each unit card is the single current source; do not append a rulings log. Update the task packet, the README row if it changes, and the registry nodes if the spec says so. Append an amendment line to `D-2026-10-22-w6-01-buildspec`. At the end of the spec, add a "Readiness closure" table: each review item number, then the closing artifact location. Write nothing else. Do not commit.
