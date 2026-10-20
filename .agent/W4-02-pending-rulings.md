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
