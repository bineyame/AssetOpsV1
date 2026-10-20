# W4-02 pending rulings (builder questions; Architect decides)

Raised by the unit-1 builder run on `task/W4-02-mini-grid-depth`. Unit 1 did not need either ruling, so this run
did not stop for them. Unit 3 cannot build B2 or the closure-5 `MG-W402-001` install path without the first.

## R1 (blocks unit 3): mixed v3/v4 channel validation for `minigrid-roles-4`

Closure 4 B2 says `sites/binding_service.py` "must point `minigrid-roles-4` to this exact table" (the three-row
authored profile `authored-mini-depth-cases/1`). Closure 5 installs `MG-W402-001` with
`BindingService.publish(..., role_set="minigrid-roles-4")`, which is a non-conversion publish, so
`validate_bindings(..., v4_metadata=True)` runs (`binding_service.py:684`).

In the shipped validator (`binding_service.py:391-417`), when a role set is in `_V4_TABLE_BY_ROLE_SET`, every
channel binding of that set must appear in the role set's v4 table. If it does not, the binding is refused as
`BINDING_CHANNEL_V4_UNKNOWN`. Cold and EV bind only v4 channels, so this has not mattered for them. Roles-4 is
different: it keeps the 14 roles-3 channels on v3 sources, such as `generator_power` and `feeder_demand`, and adds
only three v4 tuples. Mapping roles-4 to the three-row table therefore refuses every v3 channel binding.

Options the spec does not choose between:
- (a) For `minigrid-roles-4` only, apply the v4 checks and pin v4 metadata only for the roles that a row of the
  authored table names (`site_supply_state`, `mini_backup_start_event`, `mini_backup_bus_state`). The other
  channels stay v3 bindings with no v4 metadata.
- (b) Decide v4 versus v3 per bound source (its envelope schema), not per role set.
- (c) Another rule.

The answer also decides whether `_decide_v4`'s pinned-metadata check stays exactly as it is for a mixed binding set.

## q6 (unit 4 step 3, `e0f7c9de` `mini_depth/projection.py`): projection readings to confirm or replace

Step 3 is built with these readings; none blocks step 4's worker, but each fixes a persisted `result` shape, so a
change after revisions exist needs a new model version. Please rule before step 5's selection proof.

1. **Renewable per-hour result has no `status` or `cards`.** Each revision is one noon hour (closure 1 Q4); the
   result holds `hour:{capability_kw,used_kw(number),headroom_kw,decision}`, the one day `rows[]` entry, empty
   `limitations`, `coverage` and `basis`. The read composes cards (`summarize_renewable`, `used_kw` as a bound) and
   the envelope status over the selected days. Is that right, and what is the renewable envelope status rule
   (e.g. any LIMITED/CONFLICT day -> LIMITED; all days ELIGIBLE/EXCLUDED -> SUPPORTED; else UNKNOWN)?
2. **Fuel and backup rows carry no `coverage`.** Q8 says every row has `coverage`; `FuelRow` and `BackupChain` have
   none. Should fuel term rows / backup chain rows get one (which seconds?), or does Q8's sentence apply to
   renewable and service rows only?
3. **Backup `role_coverage` for instant roles.** `site_supply_state`, `mini_backup_start_event`,
   `mini_backup_bus_state` are listed with `observed_seconds:0`, a whole-hour gap and `source_count:0`
   (`Observation` carries no source ID). Accept, or should `Observation` carry `source_id` for a real count?
4. **`specific_fuel_consumption_property_revision_id`** is the one SFC revision used, or null when the hour used
   none or several (rules allow different in-force SFCs on different intervals). Accept null for several?
5. **`source_freshness` at assessment** = CURRENT iff every `role_coverage` entry is complete with no gap, every
   required series is COMPLETE with no unusable row, and no CONFLICT/REQUIRED_INPUT_UNUSABLE/COVERAGE_GAP
   limitation; else UNKNOWN. "Cited source gate resolves" is taken as satisfied by the Q13 gated selection. Thus
   fuel (tank instants) and backup (instant roles) are always UNKNOWN in W4-02. Accept?
6. **`cards.start_success_count`** stays the rule's count (only `outage_count` is nulled per q3 8). Accept?
