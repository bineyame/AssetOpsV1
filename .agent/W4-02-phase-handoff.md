# W4-02 unit 2 handoff (complete) -> unit 3

Branch `task/W4-02-mini-grid-depth`. Unit 1 product code: `00a5703a`; its q1-ruling-2 test repairs `1c1655ed`..`57aaf24e`
(see git history of this file for the unit-1 anchors: 0029 migration, roles-4, typed properties, `mini_depth/store.py`,
rule 8 in `tools/checks/configuration-persistence.ps1`, `backend/tests/mini_depth_probe.py`).
Unit 2 landed in `0f70936f` (after merging main at `4885e6ad`).

## Unit 2 anchors
- `backend/assetops_backend/mini_depth/rules.py` (pure, stdlib only): `Reading`, `Window`, `Bound`, `Coverage`,
  `series()` (clip/classify one role+asset: COMPLETE|PARTIAL|MISSING|CONFLICT), `RENEWABLE_CONSTRAINTS` (code->copy,
  stable order), `LIMITATION_ORDER`, `assess_renewable_hour`, `summarize_renewable`, `renewable_rows`,
  `LoadAsset`, `assess_service_hour` (rows sorted critical DESC, asset_code, asset_id).
  Values are `Decimal`; JSON shaping is unit 4's `projection.py`. Unit 3 adds fuel/backup rules to this module.
- `backend/tests/test_w402_rules.py`: `test_interval_coverage_and_nullable_denominators`,
  `test_service_request_supported_interruptions_and_critical_row`, `test_renewable_hour_headroom_constraints_and_precedence`,
  `test_renewable_daily_denominator` (4 collected, pure). Unit 3 adds `test_fuel_interval_and_completeness`,
  `test_backup_chain_order_and_no_event` here.

## Readings applied in unit 2 (for review; none changes a spec rule)
1. Renewable `used_kw` = sum of bound `feeder_demand` means over the hour (addressed load; closure 2 formula and the
   mock's "[41, 43] - 20 kW load - 3 kW margin"). `pv_power` must be complete but enters no arithmetic.
2. Capability bound = time-weighted hour mean of `pv_available_power` +/- `pv-available-uncertainty`, low floored at 0 (Q9).
3. A role with no usable row is `*_MISSING`; a role with usable rows that leave seconds uncovered adds `COVERAGE_GAP`.
   Missing `pv_power` or any bound feeder (or no bound feeder) is `PV_USE_MISSING`.
4. Any two usable rows of one role+asset overlapping in time (a duplicate included) is `CONFLICT`; no row is chosen.
5. Only GOOD, numeric, `kW`, interval rows cover time; instant, non-GOOD, non-kW or non-numeric rows cover 0 s but are
   cited. Rows are clipped to the window.
6. `CHARGE_OBLIGATION_ACTIVE`: complete `storage_charge_requested_power` with any interval mean > 0 (mock: "No charging
   obligation ... evidenced in eligible windows").
7. `CRITICAL_SERVICE_DEFICIT`: complete critical requested/delivered with identical interval boundaries and any
   requested > delivered (no tolerance). A complete but misaligned pair gives `CRITICAL_SERVICE_MISSING`.
8. **Flag for review:** `HEADROOM_NON_POSITIVE` when the floored headroom *low* is 0 (e.g. 0-1 kW is EXCLUDED); ELIGIBLE
   needs low > 0. The spec says "positive headroom" without naming the bound.
9. Contraindicating codes are added whenever their own inputs are complete, even if another term is missing; decision
   precedence CONFLICT > LIMITED > EXCLUDED > ELIGIBLE (closure 2). `opportunity_kwh` = headroom only when ELIGIBLE.
10. `eligible_days`/`assessed_days` are both null when no day is completely assessed; only-EXCLUDED days give 0/n.
    Cards are null without an eligible day. `recurrence_established` only for 5 requested, 5 rows, all assessed.
11. Row coverage: observed = seconds covered by every required role at once; gaps = the rest;
    `source_count` = distinct sources of usable rows of those roles. Row/hour `evidence_ids` = every reading passed for
    the hour (including context such as `battery_soc`); unit 4's input query decides that set.
12. Service request: per-asset `feeder_requested_power`; only if that is absent, `critical_load_requested_power`
    readings bound to the same asset qualify it. Partial request coverage is `MISSING`.
13. Service row assessment: conflict or partial delivery -> LIMITED; delivery missing or request not ACCEPTED -> UNKNOWN;
    complete and aligned -> SUPPORTED; complete but misaligned -> LIMITED.
14. Service cards: `delivered_load_kw` only when every bound feeder is complete; `interruptions_seen`/`unserved_kwh`
    only when every row is SUPPORTED (sum); `critical_delivered_kw` from a complete `critical_load_delivered_power`.
    No bound feeder -> UNKNOWN with `REQUEST_BASELINE_MISSING`. Status: conflict/gap -> LIMITED; all SUPPORTED -> SUPPORTED.
15. Deferred, not unit 2: local-noon/local-day window derivation and nonexistent-noon `INVALID_WINDOW` (units 4/5),
    mixed source class (provenance, unit 5), `AcceptedReading` -> `Reading` adaptation (unit 4 `inputs.py`).

## Checks (private DB `w402c_test`, dropped afterwards)
- `test_w402_rules.py` (4) + `test_w402_roles_properties.py` + job-counting files `test_s2_evidence_ledger_postgres`,
  `test_w200_source_events_postgres`, `test_s2_gateway_access_postgres`, `test_s3_dispatch_assessment_postgres`,
  `test_s4_evidence_decided_at_postgres`, `test_s4_schedule_tick_postgres`, `-n 2 --dist loadfile`: 129 passed, 6m44s.
- `tools/check-all.ps1`: all 10 guards passed.
- No full suite (not allowed this run).

## Next: unit 3
Spec closure 2 Q28 (3): pure fuel/backup rules (closure 1 Q16/Q22, closure 2 fuel paragraph, closure 4 B2 step roles)
plus authored fixture, conversion and accepted replay: closure 4 B2/S5, closure 5 (`MG-W402-001` registration,
cold-enqueue Site-type gate) and q1 ruling 1 (mixed v3/v4 predicate for `minigrid-roles-4`). Replay records accepted
IDs and binding/profile identity only (N4).
