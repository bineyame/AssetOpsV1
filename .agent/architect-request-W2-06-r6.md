# Architect request: W2-06 commit 4 implementer choices (r6)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide" and "Token Efficiency";
- `.agent/W2-06-build-spec.md`, with all rulings through "Run 5 rulings (r5)";
- `.agent/W2-technical-design-ev.md`;
- the cold selected-read equivalent, `backend/assetops_backend/cold_assessment_api.py`, and its W2-03/W2-04 rulings.

Branch `task/W2-06-ev-assessment` commit `41f32db2` holds commit 4 (`analytics/ev_reads.py`, `EvReadService` in `analytics/adapters/postgres_assessment_store.py`, the `/ev/...` routes). See "Run 7" in that branch's `.agent/W2-06-phase-handoff.md` (`git show task/W2-06-ev-assessment:.agent/W2-06-phase-handoff.md`).

The builder made five choices where the spec was silent. Implementer decisions are defects. For each one, either confirm it or give the exact replacement, as a literal predicate, a status/code table, or a test name:

1. The requested window must match the selected assessment window exactly; a covering selection does not count.
2. `STALE_SOURCE` currentness is never emitted.
3. When more than one state applies, HISTORICAL ranks above PENDING. Give the full precedence order over all currentness states.
4. A repeated query key answers `EV_PARAMETER_UNKNOWN`.
5. `EV_SELECTION_UNSETTLED` cannot occur, because there is no exact-revision parameter. Say whether to keep the code, remove it, or add a trigger.

Then dry-read spec commit 5 (the two UI routes) once more against the commit 4 wire as built, including how the UI states map to these currentness rulings. Answer any question still open with concrete artifacts; if nothing is open, say so in one line.

Append the result to `.agent/W2-06-build-spec.md` as "Run 7 rulings (r6)", amending `D-2026-10-18-w2-06-07-buildspec`. Write nothing else. Do not commit.
