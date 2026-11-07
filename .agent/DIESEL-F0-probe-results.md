# DIESEL-F0: Kisiwa fuel-events probe, evidence

Ruling: DIESEL-1-R2 §8.3 with §8.2a (`.agent/build-sheet-DIESEL-1.md`, dc72cb72a). Branch
`task/DIESEL-F0-kisiwa-fuel-probe`. In memory; no DB, no product code, no suite.

## Pre-registered expectation (committed before any run)

Committed together with the operational-action log `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml`,
before the probe tool was written or run. Restated from §8.3 verbatim in substance; nothing below is changed after a
result is seen.

- Declared world: §2.2 unchanged except start fuel **700 L** (run 1) and the operational actions; 10 day-runs
  15:00-15:00 local from `2026-10-01T12:00:00Z`, chained at full precision, stop 90 % throughout.
- Actions: delivery 300 L at 10:00 local closing night 2 (ticket 300 L); unrecorded removal 120 L over 45 min,
  01:00-01:45 local in night 4, sensor disconnected 00:50-02:20 local; dips at 07:00 local closing night 4 and at
  18:00 and 06:00 local in runs 6-10; seal and sensor-power fix at the run 6 start (no physical effect in v1).
- `fuel-balance-1` parameters exactly as §8.3 (a = 10 L, margin 2a, delivery tolerance 1 %, use band 9/10 loaded to
  11/10 (loaded + idle_h x 4.9), materiality 40 L, gap spans > 60 min).
- Architect's expectation (arithmetic): night use about 43.4 L, unchanged by the actions. Night 4 residual about
  **[95.7, 144.3] L, UNEXPLAINED**, gap > 0 (about 90 min of silence). Clean nights about [-24.3, +24.3] L,
  WITHIN_MARGIN. Night 2 (delivery) about [-27.3, +27.3] L, WITHIN_MARGIN. No night NOT_ASSESSED.
- Builder's expectation for F0a, written before running: the frozen run's causes and reporting-path conditions are
  read by `host/execution_adapter.py` `frozen_world_inputs` / `reporting_inputs` from the run alone, so causes and a
  reporting condition added with `dataclasses.replace` should be applied with no scenario entry. `FrozenCause` has no
  origin field, so the origin and content hash can only be carried in the cause's `event_id` and in
  `intervention_history` until K0 adds a field. The gap measured between readings is expected to be about 105 min
  (00:45 to 02:30 local readings around a 00:50-02:20 silence), not 90.

## Result

(Written after the measured run.)
