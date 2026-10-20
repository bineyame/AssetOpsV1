# W4-02 closure 4 check (main df7ed86e, read-only)

Result: all 20 items CLOSED (B1-B3, S1-S9, N1-N8). Each has a literal rule or table, an owning unit, and a named test.

## Spot checks against main
- 0029 role map: the 14 mapped roles are distinct and all in the 17-role gate. Counted from the table: 14 mapped plus 3 unmapped (`pv_irradiance`, `battery_power`, `pcs_discharge_capability`) = 17. The B1 table and the gate list use the renamed `mini_backup_*` roles consistently. The only gap is the cold-gate tie-break (see New questions).
- v4 mini-grid mapping rows: the three new keys are unique against `V4_CHANNEL_MAPPINGS` (`source_envelope_v4.py:694`). The 7-field tuples match the `ChannelMapping` dataclass order (`:605-620`). The event row matches `_events()`: kinds START_REQUEST and START_RESULT, correlation True, session False, units (). The state rows match `_point(DISCRETE_UNIT)`. A new `V4_CHANNEL_MAPPINGS_BY_PROFILE` entry gets found by `v4_mapping_profile` (`binding_service.py:228-233`, which matches `value is table`). The cold table and the cold `backup_bus_state` role are untouched (`binding_roles.py:145`, `BUS_STATES`).
- Role-name collision: `COLD_ROLE_NAMES` is `frozenset(r.role for r in COLD_ROLES_1)` (`postgres_evidence_ledger.py:67`). Line 472 (the spec says 466; the code is at 466-472) enqueues cold work only for v4 roles in that set. The renamed `mini_backup_start_event` and `mini_backup_bus_state` are outside it, so the collision is fixed. The extra COLDCHAIN gate is defensive.
- Overview five cards: `SiteWindowOverview.tsx:370-382` is `MetricCards columns={5}` with Service, Dispatch, Battery, Fuel, Renewable, matching B3. The three Overview test files named in N1 all exist on main.

## New questions (none block a build)
1. Cold-gate Site type: the ledger adapter has no Site-type lookup today (grep for `site_type` returns nothing there). The closure says to require "resolved Site type COLDCHAIN" but not how. Suggested answer: join `site` by `tenant_id` and `site_id` inside the same transaction.
2. `MG-W402-001` registration (S5): which registration path (`authored_fixture_specs` or demo-config) is left to the implementer. Low risk, since the closure says "explicitly registered" and gives the Site code.
