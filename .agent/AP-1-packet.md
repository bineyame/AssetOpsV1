# AP-1 review packet: stored-Site analytics readiness (`/api/sites/{id}/analytics`)

Branch `task/AP-1-analytics-port` (worktree `/opt/assetecon/AssetOpsV1-ap1`), based on `task/SR-12-warm-routes` + main.
Design: `.agent/architect-analytics-port-and-db-choice-2026-11-13.html` Part A; rulings D-SR.75, D-SR.77.
Commits: `f75c70cec` backend, `9f5b8e6f1` frontend branch fix, then the probe + packet commit.
USER_REVIEW_REQUIRED: none stated; merge on fresh-review ACCEPT plus the pending Kobo parity (below).

## Delivered
- `backend/assetops_backend/analytics/stored_declaration.py` (new): `ROLE_OF_REQUIREMENT` (fail-closed: an
  unmapped label or a NOT_STORED kind is not available), `stored_requirements` (one row per bound asset; Load = each
  bound `feeder_demand`; policies only from a configured Foundation control, never a reading), `v3_assessment_view`
  (dispatch-3.2 only, else `UnsupportedModel`; per-input usable/evaluated from `claim_limit_read.segment_roles`,
  unobserved generator spans, `missing` labels, `assessed_window`), `stored_site_declaration` (one REPEATABLE READ
  snapshot; cold/EV -> `analytics: []` without the gate or any reading query).
- `postgres_assessment_store.py`: `role_presence` (latest GOOD accepted reading per unsuperseded binding,
  `ORDER BY source_time DESC LIMIT 1`, no count), `foundation_controls_on`, `site_type_on`, `read_snapshot`;
  `selected_intervals` now delegates to `selected_intervals_on(c, ..., window)` with `window_start < hi AND
  window_end > lo` (existing callers unchanged; `in_window` still applied per assessment).
- `declaration.py`: `declaration_payload` extracted (shared by file and stored reads; `site_declaration` output
  unchanged). `plain.py`: v3 input labels added to `INPUT_NAMES` so gaps read "Available battery output" etc.
- `analytics_api.py`: `scope`/`stored`/`gate`; stored code -> stored branch; closed gate -> existing 409
  `AWAITING_EVIDENCE_MIGRATION` (message = gate reason; SR-12b shows "not available yet"); unsupported model 422;
  store down / no DB 503. Legacy codes and sibling routes unchanged (`LegacySiteGate`). `main.py`: 3-line wiring
  (`registry.ledger_scope`, `performance_gate`, `partial(stored_site_declaration, lineage)`).
- Frontend (D-SR.77): `SitePerformance` takes `configurationStore`; `POSTGRES` goes to the durable Dispatch reads
  without asking `/analytics` (409 remains the signal only when the store is unstated). `SiteAnalyticsFrames` passes
  `site.configuration_store`. `SiteEvidence`/`CapabilityReadiness` render the stored 200 as the existing table;
  `usable_records` is `number | null`, null reads "Usable records received, latest ...".
  `FindingsIndexes`/`FindingDetail` read the sibling routes (`/findings`, `/api/findings`, `/assessments/...`),
  which stay gated, so they need no change; `SiteEvidenceFrame` needs none (it renders `SiteEvidence`).
- `tools/ap1_parity_probe.py`: the Kobo parity probe (unrun; needs a DB slot).

## Acceptance (Part A3/A5) status
| Item | Status |
|---|---|
| Role map fail-closed, test per requirement | done: `test_every_dispatch_requirement_maps_or_fails_closed`, `..._configured_capability_is_never_an_observed_reading`, Load per feeder |
| v3 adapter: covered / PCS gap / unobserved gen / unknown text | done (4 tests) + other model refused |
| SR-12b four edges through stored path | done |
| Route: stored 200 T028 shape, legacy unchanged, closed gate 409, cold/EV [], store down 503 | done (+422 model, 422 window) |
| Consistency vs claim-limit section | done: no-DB over 5 fixture revisions; Postgres over 3 fixture days via the real claim-limit route |
| Postgres integration (`*_test`) | done: `test_ap1_stored_declaration_postgres.py` on `assetops_ap1_test` |
| vitest stored 200 renders table | done: `ap1StoredAnalytics.test.tsx` (3 tests, incl. Performance store branch) |
| Kobo parity on scratch clone + Kisiwa live read + unwarmed timing | **PENDING: needs a coordinator DB slot** |

## Checks run (revision 9f5b8e6f1 + probe commit)
- `pytest tests/test_ap1_stored_declaration.py test_sr12b_... test_t028_... test_s3_claim_limit_vocabulary.py
  test_health.py test_uq6a_message_seam.py`: 107 passed.
- `ASSETOPS_TEST_DATABASE_URL=.../assetops_ap1_test pytest test_ap1_stored_declaration_postgres.py
  test_s3_claim_limit_postgres.py`: 24 passed (23.5 s); `test_s3_dispatch_read_postgres.py`: 9 passed (23 s).
- vitest: `ap1StoredAnalytics`, `t028EvidenceCapability`, `t028Screens`, `siteEvidenceScreen`: 59 passed; the 21
  files that mount Performance with `configuration_store`/AWAITING: 656 passed, 3 failed, all in
  `siteFoundationRevision.test.tsx` (G-01 firmware) and failing identically on the base without AP-1 changes.
- `tsc --noEmit` clean. Guards run alone: analytic-declaration, dependency-direction, configuration-persistence,
  missing-claim-scan, frontend-hardwiring, mock-deviation labels, `check_v69_dependency_registry.cjs`,
  `test_mock_gaps.cjs`: all pass. check-all: for coordinator. No full suite (test-suite policy).

## Pending (DB slot from the coordinator)
```
# 1. scratch clone of the demo DB (name <prefix>_audit*), e.g. assetops_ap1_audit, from the prepared demo DB
# 2. Kobo parity + unwarmed timing (file stores are the main checkout's legacy roots, as the app reads them):
cd /opt/assetecon/AssetOpsV1-ap1 && W=$PWD && \
PYTHONPATH=$W/backend:$W/backend/tests:$W/contracts:$W/simulator:$W/gateway:$W/field:$W/host:$W/tools \
DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_ap1_audit \
/opt/assetecon/AssetOpsV1/.venv/bin/python tools/ap1_parity_probe.py KOBO-001 > .agent/AP-1-parity-kobo.json
# 3. Kisiwa live read (no legacy evidence): GET /api/sites/<kisiwa code>/analytics on the clone-backed app; expect 200,
#    one Dispatch row, or the 409 if its Performance gate is closed.
```
Pass rule: `available_mismatch` empty; every level/ceiling/gap difference classified; read <= 2 s else +1 warm entry.

## Known deviations / questions
1. `usable_records` is null on stored rows (design A3 says EXISTS/max, not a count); TS type widened, copy
   "Usable records received". Q: acceptable, or should the stored read count?
2. A role with no binding keeps the declaration's file-era device/signal ids (not available). Q: keep, or show
   "not bound"? Policy and not-stored rows also carry the declaration's ids.
3. A selected revision of another model makes the whole read 422 `UNSUPPORTED_RULE_VERSION` (fail closed rather
   than skip). Q: confirm vs. skipping such revisions.
4. Closed gate returns the existing code `AWAITING_EVIDENCE_MIGRATION` (message = gate reason) so the SR-12b
   "not available yet" line applies unchanged, not `PERFORMANCE_CUTOVER_CLOSED`.
5. Stored Kobo-fixture day with full coverage still reads LIMITED because no generator output reading exists
   (`Generator state and output` NOT_ACCEPTED), same rule as the file side.
6. `plain.INPUT_NAMES` gained the v3 labels (data only; `plain.readiness` unchanged).

## Residual risk
- Unwarmed latency on the real Kobo ledger unmeasured (selected_intervals_on also reads per-window jobs).
- Kobo levels will likely differ from the file-era level (dispatch-2 vs 3.2); classification pending.

## D-SR.78 rulings applied (2026-11-13)
- Q2 built: stored path ids come only from a stored binding (`stored_declaration._row`); unbound reading role gives null ids and `unbound: true`; policy/not-stored rows null ids, no reference. `CapabilityReadiness` shows "(reference Not bound)" for unbound, nothing for null-id policy rows. Tests: `test_unbound_role_gives_null_ids_and_policy_rows_no_reference` (backend), "an unbound role shows Not bound..." (`ap1StoredAnalytics.test.tsx`). The old fallback assertion in the mystery-role test now expects (None, None).
- Q1 (no count, presence only), Q3 (whole-read 422 fail closed, matches claim_limit_read.SUPPORTED_MODELS), Q4 (closed gate returns existing 409 AWAITING_EVIDENCE_MIGRATION): confirmed as built, no change.
- `git merge main` conflicted in SiteEvidence.tsx and siteEvidenceScreen.test.tsx (SR-12a rejections range vs SR-12b analytics range); both ranges kept, all-dates line on neither panel.
- Runs: no-DB ap1 28 + sr12b 8 passed; Postgres ap1 file on assetops_ap1_test 6 passed; vitest ap1StoredAnalytics + siteEvidenceScreen + t028EvidenceCapability 36 passed; tsc clean. check-all: for coordinator.
