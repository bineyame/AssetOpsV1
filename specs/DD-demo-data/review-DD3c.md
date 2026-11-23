# DD3c review (DD3.4 unit roles in the readers, parts 1-5)

## Round 1 (discovery), 2026-11-23, branch `task/DD3c-unit-roles` at 400bcd400

Summary (verdict: **accept once the findings are fixed on the branch**)
- Read: the packet, the pre-flight, the handoff, D-DD.41, .43, .45, .108-.118, spec §7 DD3.4, and `git diff main...HEAD` in full
  (the migration, `unit_roles`, every reader, the tests, the parity test, the world pins).
- Sound: `unit_roles` (D-DD.111/112 exact), migration 0074 (exact-count replacements, downgrade = 0048's bodies),
  `MINI_DEPTH_ROLE_SETS` at every Python gate, `ROLES_BY_SET` from the served sets, dispatch PV sums, replay, the fuel
  balance and litres per unit (D-DD.113/117), the one-unit identity paths, and the Kobo parity test's normaliser.
- H1: the mini-depth reader does not take a Site's units through `unit_roles`. Kisiwa's generator and Mto's PV still
  degrade there (CONFLICTING or dropped), and the packet's Outcome says the opposite.
- H2: verification gets its units from the readings, not from the bindings. A bound unit that sends nothing for a whole
  window drops out of the Site sum without a word, and the window still reads complete (reproduced).
- M1: a non-lead policy key raises out of `_configuration` as a job failure. D-DD.108 Q6 asks for a mapping to the
  existing refusal.
- Low: L1 the world seed is taken over `role_set`; L2 the fuel balance and litres sum units themselves; L3 the litres
  parity is weak and the packet says so.
- Checks: architecture, agent-workflow and the statement catalogue pass; the focused pure tests are reported below.
  Postgres was not rerun (no finding needs it).

### Findings

**H1 (High, acceptance gap): mini-depth is a Site-figure reader that does not call `unit_roles`.**
`backend/assetops_backend/mini_depth/inputs.py:255` (`_one_bound(bindings, rules.GENERATOR_POWER)` returns None when two
generators are bound, so `fuel_readings`/`backup_readings` (`:137-148`) are empty and no SFC is read, `:286-291`);
`backend/assetops_backend/mini_depth/rules.py:324-327` and `:714` merge PV and generator power across assets
(`any_asset=True`). Two units report the same interval, so `series()` (`:223-247`) classes the role CONFLICTING.
- What is wrong: D-DD.110 accepted pre-flight Q3 "as listed", and that list names `mini_depth/inputs.py (power, state,
  backup events, SFC burn, policy)`. Spec §7 DD3.4 says "called by every Site-figure reader whatever the role set";
  D-DD.41 puts `mini_depth/*` in DD3.4. The branch changes only the role-set filter in `mini_depth` (part 2). After
  DD5 loads their readings, Kisiwa's fuel, backup and generator hours and Mto's renewable hours read CONFLICTING or
  absent where Kobo's read figures. That is the "same data, output on every Site" gap D-DD.113 called a gap.
- Why it matters: DD3.4 must merge before DD5.1 loads Kisiwa and Mto (D-DD.44), and this is the reader behind the
  mini-grid depth pages. The packet's Outcome (`packet-DD3c.md:9-10`: "Kisiwa ... and Mto ... give summed Site figures
  where today they refuse") is not true for mini-depth. No test covers a two-unit mini-depth hour; T5 tests only the SQL
  renewable-hour gate.
- Fix: in `load_hour_inputs`, take the unit roles that are PER_ASSET in the pinned set (`unit_roles.per_asset`) as the
  Site's units. Build the Site series for `generator_power`/`pv_available_power`/`pv_power` through `site_power`, and
  `generator_state` through `site_generator_state`. Take the backup events through `site_events`, and the SFC burn per
  unit summed (D-DD.113's shape). Read the policy through `lead_policy`, with `UnitRolesRefused` mapped to
  `CONFIGURATION_MISSING`. Keep `generator_asset_id` as the lead unit, so one unit stays byte-identical (the role-sets
  golden and Kobo's parity hold). Add pure two-unit tests: one hour each for renewable, fuel and backup, with one plant.
  If the Architect meant mini-depth sums to come later (DD3b), the packet's Outcome must say so and the gap needs a
  ruling. That is the question below.

**H2 (High, correctness): verification takes its units from the readings, so a silent bound unit drops out of the sum.**
`backend/assetops_backend/actions/verification_rules.py:447` (`assets = sorted({r.asset_id for r in readings if
r.role == role})`).
- What is wrong: a unit role is summed only when two or more assets *reported* in the window. When one bound unit sends
  no reading for the whole 60 minutes, the role takes the single-asset path. The Site figure is then the other unit
  alone, stated COVERED, with no problem and no unit named. D-DD.41 says "a unit with no value at that step makes the
  Site value absent there, named by unit". Reproduced on the branch with the test's own helpers
  (`test_dd3c_cost_check_units.two_units` minus every `gen-2` row, `role_assets` naming both units): both units give
  `generator_kwh 26, complete True`; `gen-2` silent gives `generator_kwh 20, complete True, generator_units` absent,
  and no generator problem. The same holds for `pv_available_power` at Mto.
- Why it matters: verification judges the reserve trial on these window totals and the `complete` flag. A unit that has
  stopped reporting, which is likely in a unit-failure story, turns into a complete window with a smaller figure. The
  cost check itself is safe: the missing unit becomes `(None, None)`, so GENERATOR_KWH_UNKNOWN. Dispatch, replay, the
  fuel balance and litres take their units from the bindings or the Foundation and do not have this fault.
- Fix: for a role in `unit_role_set`, take the units from `allowed[role]` (the bound `role_assets`) whenever more than one
  asset is bound, whatever reported. A silent unit then goes through `power()`, reads UNKNOWN or MISSING, and is named.
  Add a test that a bound unit with no readings gives an unknown Site slot naming that unit, and `complete False`.

**M1 (Medium, ruling deviation, disclosed as deviation 4): `UnitRolesRefused` is not mapped to an existing refusal.**
`backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:345`.
- What is wrong: D-DD.108 Q6 says each reader maps the refusal to its existing Foundation or configuration refusal (the
  pre-flight's default for dispatch was "a limit line"). Here the exception escapes `_configuration`, the worker's
  `except Exception` (`assessment_worker.py:142`) records it as a job failure, and the job is retried. Nothing catches
  `UnitRolesRefused` anywhere in `backend/assetops_backend`.
- Why it matters: no demo file triggers it (DD1.2 tests that no non-lead unit carries policy). If one did, the Site
  would have a failing dispatch job instead of a stated configuration limit. That breaks the ruled contract and the
  "missing is stated" rule.
- Fix: catch it in `_configuration` and append the existing limit text the code already uses for a missing or
  unreadable `minimum-runtime` (no new string). Add one test with `gen-ks-02` carrying `minimum-runtime`.

**L1 (Low, residual risk the packet does not name): Kobo's world seed now depends on the role-set name.**
`simulator/assetops_simulator/world/telemetry.py:166` takes `foundation_digest` over `role_set`, and `:430` seeds the
frozen run with `int(digest[:8], 16)`. The move changes Kobo's seed (865796934 to 1552592118). I checked: on the W1
seven days, every reading entry is identical under both labels; only `role_set`, `foundation_digest` and
`golden_digests` move in the manifest. No draw consumes the seed today. Deviation 1's relabelled goldens hide this
coupling, not a value change. If a pack later draws on the seed (dropouts), a role-set rename re-draws Kobo's history,
which is D-DD.102/115's class. Fix: name it in the packet's residual risk and in the backlog line D-DD.115 opened.

**L2 (Low, D-DD.44 wording): two readers sum units themselves.** `fuel_balance/rules.py:306` (`_sum`) and
`structure/litres/rules.py` (`_piece`) add up the units' values instead of calling `unit_roles.site_litres`. The
behaviour is D-DD.41's (any unknown gives unknown), so this is a preference: route `_sum` through `site_litres` or say
in a comment why it does not.

**L3 (Low, disclosed): the litres month parity is weak.** With 1.5 days loaded, both states give the all-absent month
(RUNNING_RECORD_GAP). The valued one-unit litres month is covered only by the pure golden (4d's `kobo()`). This is
acceptable for D-DD.114 together with the golden. No action beyond the packet's own note.

### Points checked and found sound (no finding)
- `per_asset` decides summing (review focus 1): every reader sums only when every binding of the role is PER_ASSET in
  its set. Roles-4 with two assets keeps MULTIPLE_BINDINGS, AMBIGUOUS_BINDING and READER_BINDING_CHANGED, and the tests
  cover all three. A roles-5 Site with one unit takes the old path, which is what Kobo's parity shows.
- Deviation 2 (cost-check wire shape): the extra keys appear only above one unit and stay out of `details` and
  `plan_sha256`. `_fuel_value` reads none of them. Acceptable as the builder's shape in D-DD.117's pattern.
- Deviation 3 (blended night note): sum(loaded L)/sum(kWh) and sum(idle s × rate)/sum(idle s) are dimensionally right
  (L/kWh, L/h). It adds no new template. The form is the coordinator's default, still open for confirmation as the
  packet says.
- Migration 0074: each text is replaced exactly once, the bodies are `CREATE OR REPLACE`, and there is no trigger or
  data change.
- Parity test normaliser (D-DD.114): evidence ids are written as `device/signal#sequence`, and only lists made wholly of
  those are sorted. Membership is still exact, and the uniqueness assert guards the mapping. `committed_watermark` is
  masked as wall clock. No digest is compared directly, and each skipped digest is listed with its reason. Acceptable.
- Golden provenance: `kobo-one-unit-golden.json` (6b80566ed) was committed after part 3's reader commits (31abdf4da).
  Its capture is recorded as run on main a4dd5e801's code in a detached worktree, and the plants show the test catches
  a change. I did not re-capture it on main (not verified independently). The fuel-balance (55c32eb77) and role-sets
  (e201a8318) goldens come before their changes.

### Checks run (this review, worktree root)
- `ASSETOPS_GUARD_PYTHON=... pwsh tools/check-architecture.ps1`: "Architecture check passed."
- `pwsh tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- `python tools/checks/statement_catalogue.py`: "OK statement catalogue: ... (9 adopted)", 3 allowed entries, exit 0.
- Pure DD3c tests (`unit_roles`, `readers_units`, `cost_check_units`, `fuel_balance_units`, `litres_units`,
  `kobo_one_unit_golden`, `migration_0074`) via `tools/heavy-slot.sh -- python -m pytest` with the worktree first on
  PYTHONPATH: 90 passed in 4.78 s (the host runner refuses a non-`--db` slot because it sets a DB URL).
- Scratch reproductions (scratchpad, deleted): H2's silent unit; L1's seven-day reading comparison under both labels.
- Not rerun: Postgres parity, role sets, and the 84-file reach set. I cite the builder's runs (2f5a91e10 parity 1
  passed; reach set failures only in ch5c2, 3b1, k7, pr3 ×2, w403, each failing identically at merge-base 0c44ae75b).
  The reach set's first-run summary line was lost (packet). The rerun of the files after 88% and of every failing file
  is the only complete count.

### Residual risk not in the packet
- L1's seed coupling.
- Dispatch and replay take their units from the bindings in force at a step. A unit that is unbound mid-window leaves
  the Site sum without being named, just as a LOAD feeder does today. Readiness names unbound units (D-DD.45), so this
  is consistent, but it is not stated.

### Questions for the Architect
- Q1 (H1, scope): D-DD.110 accepted pre-flight Q3's list, which names `mini_depth/inputs.py` (power, state, backup
  events, SFC burn, policy), and spec §7 says "every Site-figure reader". The branch leaves mini-depth summing nothing,
  so Kisiwa and Mto read CONFLICTING or absent there. Default applied in this review: it is in DD3c, so fix it on the
  branch before merge (about +0.5 u). The alternative is a ruling that moves it to DD3b or DD5 before DD5.1 loads
  their readings.
