# Architect request: W6-01 closure round 2

You are the AssetOps Architect. The closure check `.agent/W6-01-closure-check.md` confirms all 36 first-review items are closed. It found 10 new open items: OI-1 to OI-10, 4 BLOCKERs and 6 NOTEs. Measurements are in `.agent/W6-01-mock-measure-2.md`.

Close each one in place in `.agent/W6-01-build-spec.md`, with a literal artifact verified against merged code:
- **OI-1:** the global sort order for incidents and maintenance. Give the exact keys, direction and tiebreak, consistent with the cursor.
- **OI-2:** the replacement literals for the Site Work strip "Manage in Incidents/Maintenance · Not available yet" and for `WORK_CONTEXT_NOTICE` once the global pages are live. Name the unit and the pinning test files.
- **OI-3:** the time precision of the detail example versus the nested `work_detail` (six-digit times). State one rule.
- **OI-5:** the request header cap at 390. The mock is already 430, and a 200-character title gives 844. Set a cap derived from the measurements, plus the clamp/disclosure rule.
- The 6 NOTEs.

Add rows to the "Readiness closure" table, and append an amendment line to `D-2026-10-22-w6-01-buildspec`. Write nothing else. Do not commit.
