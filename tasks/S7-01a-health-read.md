# S7-01a — Central source health and asset boundary reads

Status: implementation-ready. USER_REVIEW_REQUIRED: false; non-UI, mergeable after independent review. Size M, two phases. Branch `task/S7-01a-health-read` from merged main. Depends on S2-02 central diagnostics and S1-02 effective bindings. Authority: `.agent/architect-W1-remaining-answers.md`; `.ai/DECISIONS.md` `D-2026-10-16-a-s7-health`, `D-2026-10-09-pre-s3-evidence-readiness-health`; registry `D-edge-health-cases`, `I-source-health-read`, `I-asset-boundary-read`. No UI/panel promotion in this part.

## Verified seams and new contract

Existing central diagnostic selection: `backend/assetops_backend/evidence/adapters/postgres_gateway_access.py:172-194`; cadence contact and diagnostic fields: `backend/assetops_backend/evidence/gateway_access.py:289-343`; `GET /api/sites/{site_id}/gateway-health`: `backend/assetops_backend/gateway_api.py:38,93-109`; existing client: `frontend/src/sites/gatewayHealthClient.ts:3,68`. Existing S1 asset/basis/binding tables: `backend/migrations/versions/0001_foundation_identity.py:95,149`, `backend/migrations/versions/0002_signal_bindings.py:37,65`. **New:** two-clock Site source-health interpretation/read and Site/asset-scoped configured-battery boundary read/API; neither is a physical health assessment.

Use the request-level `finding_api.Access`/`development_access` seam, as in `finding_index_api.py:28,44-50`, for 401/403/404 on the new reads; the existing S2 gateway-health route is a data precedent, not the access boundary.

Site read resolves registered gateway/source IDs, most recent centrally stored diagnostic per gateway, local sequence, diagnostic ID, server `received_at`, reported `observed_at`, cadence, read time, source watermark, source-specific contact time where supplied, queue depth/oldest age, clock offset/trust and disk pressure. Receipt freshness `CURRENT|STALE|UNKNOWN` is distinct from reported-fact age/trust and `STALE_PROJECTION`. If no derived projection is introduced, record `STALE_PROJECTION` as not applicable and test the inconsistent-selection refusal instead. Fresh receipt of old facts may have current gateway contact and old/Unknown facts. Gateway contact never proves source-device contact. No registered gateway = `NO_REGISTERED_SOURCE`; registered never received = `UNKNOWN`. Stale receipt does not date an outage; queue/disk are last reported, not current hardware state. Store failure or inconsistent registration/diagnostic selection cannot yield a current claim. No join from diagnostics to accepted measurements.

Battery read resolves effective Site basis and configured asset/binding IDs. Return `UNKNOWN` physical condition with named missing accepted causal temperature/capacity/stress inputs, or `NOT_CONFIGURED`/Unknown reason if absent/unbound. SOC and nameplate may appear only under separate evidence/declared labels and exact accepted IDs. Withhold degradation, remaining life, stress score, warranty/replacement exposure and diagnosis. Enforce tenant/Site/asset 401/403/404; a foreign asset is never an empty healthy row.

## Phases and proof

| Phase | Deliverable and focused proof |
| --- | --- |
| 1. Central fixture/read | **New** `D-edge-health-cases` through registered gateway authentication and central ingestion: current heartbeat, stale cadence, delayed old diagnostic freshly received, growing queue/old item, clock offset/untrusted time, disk pressure/acquisition stop then recovery; also never received and wrong Site. Assert ID, sequence, server/reported times and reload. Add `backend/tests/test_s7_source_health_postgres.py` (new), including refusal and, only if a derived projection exists, stale-projection cases; otherwise record not applicable and test inconsistent-selection refusal. |
| 2. Asset boundary/review | **New** configured battery with missing causal input, unbound/absent battery and wrong asset/Site checks in `backend/tests/test_s7_asset_boundary_postgres.py` (new). Pin basis/binding IDs after reload. If DDL is needed, allocate after main's `0018_finding_match_deferral`; S6-02a adds unmerged `0019_verification_core`, so re-chain migration at merge. Audit any new writer/fixture SQL against statement-level rule 8 and run `python tools/writer_guard_probes.py`. Run `tools/check-all.ps1`, registry checker and one final-revision full backend suite with private `*_test` DB per `backend/TESTING.md:104,112-125`: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml=.pytest-junit.xml`, keep-awake, 20-minute cap, JUnit zero skipped/failed. Fresh independent review permits merge; S7-01b consumes this contract. |

## Architect questions

1. **Recommendation:** expose a versioned read DTO for fact age/trust rather than mutate S2 gateway-health fields in place; select diagnostics and registration in one repeatable-read transaction so the per-gateway statements share one DB snapshot.

## Plan fix round 1

Named the request identity seam, bounded stale-projection proof to an actual producer, and required one repeatable-read snapshot for registration and diagnostics.
