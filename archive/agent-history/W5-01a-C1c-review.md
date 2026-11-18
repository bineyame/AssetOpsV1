# W5-01a C1c (Q13) review, commit 29d24321

Verdict: ACCEPT. No findings. Read-only review; tests not rerun (builder: 62 passed, check-all 11/11).

- Predicate: foundation_on maps node_id to component_id; keeps SIGNAL edges whose from_node is a COLD_ROOM and whose to_node component is a returned TEMPERATURE_PROBE; asset_id returned only when exactly one distinct component, else null. Missing topology gives `{}` and null. Matches the Q13 ruling.
- Candidate order in health_rows via _asset_id: excursion policy, START policy, chamber_probe_asset_id, only asset; each counts only if in assets. Matches.
- Tests: test_health_not_configured asserts ['ambient-1','probe-1'] codes and asset_id == probe-1; test_health_rows adds the three named cases (chamber set, null, policy wins).
- Scope: 4 ruled files plus the handoff only. foundation_on remains SELECT-only (no writes added).
