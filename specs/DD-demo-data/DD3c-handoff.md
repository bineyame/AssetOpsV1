# DD3c handoff (partial: pre-flight and part 1 of 4)

- Done: `DD3c-preflight.md` (12 questions, defaults, no blocker); part 1 `backend/assetops_backend/sites/unit_roles.py`
  (pure: `site_power`/`site_litres`/`site_power_series`, `site_generator_state`, `site_events`, `units`, `lead_unit`,
  `lead_policy` refusing `TEL_FOUNDATION` via `UnitRolesRefused`, `site_rating`), tests
  `backend/tests/test_dd3c_unit_roles.py` (33, incl. one-unit Kobo parity: same object, type and repr).
- Plants (each reverted): sum with a start term (7 fail), no one-unit state shortcut (1), no lead refusal (1),
  FAILED unit rated (1).
- Next: part 2 migration `0074` (roles-4 or roles-5 in 0048's bodies) and the mini_depth/structure readers; part 3
  dispatch_v3, verification, replay_series, fuel_balance; part 4 Kobo world conversion to roles-5 and Postgres
  product parity. Per the pre-flight defaults unless the Architect rules otherwise.
- Risks: all units FAILED gives an absent rating (empty sum), not 0 (not ruled); no reader calls the module yet.
