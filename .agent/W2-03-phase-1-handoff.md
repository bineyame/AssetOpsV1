# W2-03 handoff (partial; stopped on an Architect question)

Branch `task/W2-03-cold-assessment`. Landed:
- 7667ad97, 4d704f76 — commit (1): `0022_w2_cold_assessment.py`, Finding revision `domain` write, rule-8 cold policy + 25 probes (20 caught / 5 allowed, non-vacuity proven), `test_w203_cold_migration_postgres.py` (4 pass), head literals 0021->0022 in 7 tests. check-all 10/10.
- 0089cdb8 — commit (2): `analytics/cold.py` pure rules, `test_w203_cold_rules.py` (7 pass), pinned vectors `backend/tests/fixtures/w2/cold-w203-vectors.json` + drift check `host/tests/test_w203_cold_vectors.py`. Six W2-02 cases give the spec outcomes.

## Blocking question (commit 3)
Q1. Trigger `financial_consequence_dirty_on_finding_revision` (0011/0012) fires on every `finding_revision` INSERT and copies `episode_start/end` into `financial_consequence_work.affected_from/to`. A cold revision with null bounds fails NOT NULL; with bounds it queues mini-grid fuel work. 0022 spec is silent. Should 0022 narrow it to `WHEN (NEW.domain = 'mini_grid')` (W2-04 adds cold money triggers in 0023), or otherwise?

## Readings to confirm (commit 1/2 built on the narrowest reading)
Q2. `cold_episode_revision.coverage` NOT NULL; "peak null if no usable point" as `CHECK (peak_observed IS NULL OR coverage > 0)`. Added scope-unique `(tenant_id,site_id,id)` on episode/revision (needed by scoped FKs), no-self-split CHECK, 64-hex SHA CHECKs.
Q3. `cold-excursion/1` stored as analytic_id `cold-excursion` + model_version `1`.
Q4. Open-episode low duration ends at last continuously observed out-of-band reading (20:00 -> 45 min); literal "window end" (20:05) would give 50, contradicting the required 45.
Q5. Earliest start null when prior reading is >10 min earlier or not in band.
Q6. Claim mapping: coverage<0.8 UNKNOWN; confirmed >=15 min + gate permits BOUNDED+exposure; confirmed short or gate refuses POSSIBLE; single out-of-band reading state UNKNOWN/claim POSSIBLE; in band NO_EXCURSION_OBSERVED/BOUNDED; conflicting GOOD probe values at one instant CONTRADICTORY.
Q7. Start Finding only for OBSERVED_FAILURE with permitting gate (timeout-inferred failure also OBSERVED); success -> no Finding.
Q8. Backup transfer step counts only TRANSFER_RESULT before first POWER_RESTORED in the correlation.
Q9. Low-excursion peak = minimum observed value.
Q10. Calibration settled at configuration selection (commit 3) via probe_asset_id; ColdEvidence has no calibration field.
Q11. Contradictory records linked EXCLUDED reason CONTRADICTORY.

## Remaining
Commit (3) worker/episode/Finding writes + `test_w203_cold_replay_postgres.py` (anchors: assessment store `query_evidence` :176, `_configuration` :201, `enqueue` :318, `_persist` :421, own txn :544; finding store `apply` :118 txn :145, `_insert_finding` :151, `_insert_revision` :165; intake kit `test_s2_evidence_ledger_postgres.py`, v4 fixture `test_w200_source_events_postgres.py:55`); (4) read API + reads tests; (5) four routes, panel guard, 1440/390 captures, packet; then full backend + host suites, full npm test, check-all. Private DB `assetops_w203_test` exists.
