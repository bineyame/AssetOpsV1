# Architect request: reconcile the W2-07 build spec with the W2-06 merge

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: the sections "Mockup drives the design; implementers never decide", the Architect readiness gate, and "Token Efficiency";
- `tasks/W2-07-ev-site-evidence-money.md`;
- `.agent/W2-07-build-spec.md`, including the pre-build closure and the concrete-artifact closure;
- `.agent/W2-06-build-spec.md` rulings r5–r10;
- the merged W2-06 code on main (`d4d13735`): `analytics/ev_reads.py`, `EvReadService` in `analytics/adapters/postgres_assessment_store.py`, `backend/assetops_backend/ev_assessment_api.py`, migration `0025_w2_ev_session.py`, and `frontend/src/sites/EvAssessmentViews.tsx`.

W2-06 changed during review in these ways:
- the exact-window selection;
- the currentness precedence;
- `EV_SELECTION_UNSETTLED` was removed;
- the `source_provenance.reasons` field and the M1-a/b/c unassessable-source handling;
- completeness now comes from SUPPORT uses;
- the read-time `start_evidence_id`/`abort_evidence_id`;
- the P8 tab-inventory guard;
- r10 N3, which hands the per-record `SOURCE_UNVERIFIED` sentence to W2-07's `ev-evidence-analysis` route.

Do one full implementer dry-read of every W2-07 spec commit against the code as merged. Fix every place where the W2-07 spec now conflicts with it or omits something:
- the 0026 `down_revision` and its constraints;
- the wire keys reused from W2-06;
- the currentness and refusal codes;
- the provenance shape;
- the tab-inventory entries any W2-07 route adds, with the exact guard multiset change;
- the N3 sentence placement, with exact copy and test;
- the test names.

Give concrete artifacts: literal JSON, tables and copy. Answer in advance any question a mid-level implementer would ask.

Append everything to `.agent/W2-07-build-spec.md` as "Post-W2-06 reconciliation (2026-10-20)", amending `D-2026-10-18-w2-06-07-buildspec`. Write nothing else. Do not commit.
