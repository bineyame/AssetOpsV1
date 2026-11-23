# Build card: DD3d, the fuel floor, the fuel records, the fuel cost and the budget

DD3d = five units, **6.5 u**, split by D-DD.171 into two parts (W4: over 6 u):

| Part | Units | Size | Branch | Review |
|---|---|---|---|---|
| **DD3d-a** | DD3d.1 floor, DD3d.2 records, DD3d.3 H5 | 2.75 u | `task/DD3d-fuel-floor` (exists, no commits) | one discovery review |
| **DD3d-b** | DD3d.4 fuel cost, DD3d.5 run-rate budget | 3.75 u | `task/DD3d-b-fuel-cost` | one discovery review |

Card by the DD lane Architect, 23 Nov, for a builder who has not seen the session (Codex or Claude). Line numbers:
`specs/DD-demo-data/spec.md` (S), `rulings.md` (R) and `assessment-budget.md` (A), all as at `task/DD-cards-2`. Read
only the lines named, then the code. A question the lines do not answer stops only the affected unit and goes to the
lane Architect (`rulings.md`); count it in the packet. Figures quoted below are projections from DD3b's run. The
tool prints the served ones, and a served figure that differs from `M` by more than money rounding stops for the
Architect. Nothing is tuned to a projection.

## Before you start (both parts)

- DD3b (`task/DD3b-mini-plant`) must be on main. Its packet lists exactly six known H5 failures (closed by DD3d.3)
  and seven DDR rehearsal failures plus `test_ds4_world_postgres` t12 (closed by DD3d.4). Any other failure blocks.
  DD3b's state on 23 Nov: `specs/DD-demo-data/DD3b-handoff.md` on its branch ("Run 4", then the D-DD.164 fix commits
  up to b3478de5f, `M` rev 16.23).
- Pre-flight against main: grep for an existing producer of FUEL_DELIVERY/TANK_DIP rows in `simulator/` and `tools/`
  (D-DD.154 R2897-2898: if one exists, DD3d.2's writer is taken from it). Batch every question into one request.
- Tests through `tools/heavy-slot.sh --db-lane -- pwsh tools/run-host-tests.ps1 -- <files>` from the worktree root.
  Simulator tests with `PYTHONPATH=$PWD/simulator:$PWD/contracts:$PWD/backend:$PWD/host`. Compare with
  `.agent/main-baseline/`. Evidence under `/opt/assetecon/evidence/DD3d-a/` and `/opt/assetecon/evidence/DD3d-b/`.

---

## Part DD3d-a (2.75 u)

### DD3d.1 The tolerance floor (1.25; D-DD.153 R2765-2885; S882-885; C-DD17 S986)

- Lakeside's `/2` file (`backend/tests/fixtures/on1/lakeside-power.onboarding.json`): each tank's `properties`
  gains, after `tank-capacity`, `fuel-level-sensor-accuracy` (KOBO-001 25, KISIWA-001 50, MTO-001 10 L, `SITE`,
  version 1) and `fuel-level-sensor-accuracy-basis` `GENERIC_DEFAULT` (R2789-2795). The packet quotes the basis
  sentence (R2792-2795). Lakeside's `/2` digest pin moves (D-DD.128 chain); list it.
- `structure/observe/`: `FLOORED`, `Floor`, `FactorObservation.floor`, the `floors` argument, the adverse-branch
  rule, `basis()`/`claim()` only when the floor binds (strict `>`), and the `FloorReadPort` wired in
  `structure/observe/composition` on the Foundation read the litres inputs use (R2796-2820). Import
  `TANK_MARGIN_FACTOR`, `declared_for`, `accuracy_values`, `ACCURACY_BASES` by name; never re-derive them.
- No copy changes (no screen renders the band; R2821).
- `tools/dd_check.py` C-DD17: the rule of R2834-2841 (own JSON read of a; factor 2 typed with a comment citing
  D-DD.153; Kobo, Kisiwa, Mto clauses; no carve-out for no-burn months). The served clause stays DD6's.
- Tests: `backend/tests/test_dd3d_tolerance_floor.py` P1-P4, the three binding cases, the plant and the service test
  (R2862-2879). `test_dd3c_kobo_parity_postgres.py` drops its 10 L injection; its +5 L plant must still fail.

### DD3d.2 The fuel records (1.25; D-DD.154 R2887-2918 as amended by D-DD.168 R3286-3328; S886-889)

- Writer: `simulator/assetops_simulator/world/exports_fuel_records.py` (new), called by `tools/world_history.py
  exports` when `--telemetry` is given, for each mini-grid tenant. It writes `<out>/<slug>/fuel-records.json`, schema
  `assetops.world-fuel-records/1`, with the exact fields, dip instants, ticket format, `recorded_at` rule (OOO-1's
  from D-DD.53's module table) and refusal `EMU_FUEL_RECORDS` of R3298-3311.
- Guard: `backend/assetops_backend/prepare_clock.py` `PREPARE_DATABASE` gains the two world rung patterns, and
  `require_prepare_database` refuses `database_target.is_operator_name` names first (R3294-3297). It stays the one
  check.
- Loader: `backend/assetops_backend/load_fuel_records.py` (new), `load_fuel_records(dir, tenant) -> dict` and its
  `python -m` entry, exactly R3312-3322: guard first; the `RecordClock` holder set as the work store's
  `test_db_clock_override` (the `tools/demo_story_clock.story_commands` swap pattern, local to this module); per
  record `validate_entry` → `entry_site_context` → `compose_entry(..., with_actor=True)` →
  `post_operational_record(..., ENTRY_PRINCIPAL)`; idempotency key `oprec-entry-` + sha256(source_record_id)[:32];
  exit 2 on a refusal; one JSON output line. DD5b calls it; DD3d does not wire the ladder.
- `tools/dd_check.py`: C-DD2 gains FUEL_DELIVERY and TANK_DIP for each mini-grid Site-month (S971). C-DD8 also
  asserts on stored records: opening dip + deliveries − closing dip − burned = the draw, per Site-month; it prints
  every assessed night by state per Site, and any UNEXPLAINED or EXCESS night is a FAIL that names the night
  (R2911-2914). On the pure DIR (`--pure`) C-DD8 judges the file instead of the store.
- Tests: `backend/tests/test_dd3d_fuel_records_postgres.py` and `simulator/tests/world/test_dd3d_fuel_records_file.py`
  (R3323-3328).

### DD3d.3 H5 on the floor (0.25; D-DD.156 R2954-2980; S890-891)

- `Docs/demo-sprint/product-direction-layer4/check_manifest.py` H5 (the mini-grid clause, about line 1520 on main):
  `unexplained_l <= max(D("0.02") × diesel_l, 2 × a)`, a from Lakeside's `/2` file by H5's own JSON read, matched by
  site code; factor 2 typed with a comment citing D-DD.153; the label prints both terms (R2962-2968). No declared a
  is a FAIL, never a 2 % fallback.
- `M` lines 123 and 198: the two wording changes of R2969-2972 (one `M` commit; rev bump).
- The six known H5 lines close. The packet prints check_manifest's count before and after.

### DD3d-a: facts the code fixes (D-DD.162)

- Protected: `fuel_balance/rules.py`, `night_text.py`, `actions/fuel_verification.py`, `actions/verification_rules.py`
  and `structure/litres/` are not edited (`git diff main --` on them is empty; R2875-2877). The observer's strings
  are byte-identical when no floor binds. The work store's override stays constructor-only. Production composition
  never sets it, and only the guarded loader and the existing demo prepare do.
- Names: tank asset codes and property keys as the `/2` file declares them (`fuel-tank`, `tank-capacity`,
  `fuel-level-sensor-accuracy`).
- Decimals: litres compared as `Decimal`; the floor converted exactly in the observer's 34-digit half-even context;
  `value` strings in the loader's body are `operational_entry.VALUE`-legal (at most 3 decimals).
- Ids: a fuel record's identity is its `source_record_id`. Its idempotency key is derived from that id alone, so a
  re-run is a 200.
- Tests: nothing under `backend/` imports `gateway`, `host` or `simulator`; the file test lives in
  `simulator/tests/world/`.

### DD3d-a: plants (introduce, see it fail, revert)

(a) The floor port returns None: Kobo July flips back to RAISED, band 0.24. (b) Declare no a at Kisiwa: H5 FAILs
"no declared level accuracy". (c) Load one record with the guard bypassed onto a name `assetops_op_x_test`: the
loader refuses with nothing written. (d) Set OOO-1's `recorded_at` to its `occurred_at`: the DELIVERY_RECORDED_LATE
assertion fails.

### DD3d-a: reach set

`test_3b4_observer{,_postgres}.py`, `test_3b2_findings_pinned.py`, `test_4d_litre_split{,_postgres}.py`,
`test_dd3c_*` (all), `test_k2_fuel_records{,_postgres}.py`, `test_k3_fuel_balance_{rules,postgres}.py`,
`test_k5_fuel_night_text.py`, `test_k5_fuel_night_api_postgres.py`, `test_own_g3_operational_entry{,_postgres}.py`,
`test_own_g2_fuel_night_tick_postgres.py`, `test_6c_difference.py`, `test_6h_levers.py`, `test_dd1_*`,
`test_dd2_check.py`, `test_ds4_world.py`; the tests importing `prepare_clock` (`grep -l prepare_clock backend/tests
host/tests tools`); simulator `world/*`; `check_manifest.py` (count = main's + 0 new). Guards: statement catalogue
(D-DD.96), `check-decision-index.py`, `check-agent-workflow.ps1`, the architecture guard with
`ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python`.

### DD3d-a: done when

All tests pass; plants fail as stated and are reverted; reach set green or identical to main except the six H5
lines now passing. Packet: mid-build question count, the `/2` digest move, C-DD17 per Site-month (consumption,
unexplained, relative band, band, state; compare with R2842-2856), the night states per Site, check_manifest counts.

---

## Part DD3d-b (3.75 u)

### DD3d.4 Fuel cost is burned × price (1.75; D-DD.163 R3100-3160 with D-DD.169 R3330-3347; S892-895)

- Structure v5 (R3111-3115): `rows_mini_grid.py` drops `fuel_cost`'s `stated_by`; `STATED_STATE["MINI_GRID"]` drops
  `fuel_cost`. No `diesel_l` gives no fuel cost ("not available yet"), never the invoices.
- Fuel bought (R3116-3126): `money._ROWS["fuel_cost"]` and `READ_AS["fuel_cost"]` renamed `fuel_bought` with
  FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", "Fuel invoices for the month"); reconciliation heading key
  `FUEL_BOUGHT`, label "Fuel bought (invoices)"; the statement CLI's `--fuel-cost` flag and the stored field keep
  their names; deep dive's `fuel_cost` step takes the node's value, evidence `FUEL_INVOICES` as the price's.
- Declared prices (D-DD.169): `publish_assumption.py`'s tenant check against `config.served_tenant_slug()`;
  three fixture files `backend/conversions/world/lakeside-power.diesel-price.<SITE>.json` (fields R3337-3344;
  value from `M` `prices.diesel_usd_per_l`, a parity test reads `M`); the DDR rehearsal Postgres test publishes them
  in its setup. DD5b adds the ladder step.
- G4 (`backend/assetops_backend/rehearsal_check.py`): a Site-month without a fuel invoice needs the declared price,
  evidence ASSUMED, printed "declared, no fuel invoice this month"; a missing price is still a FAIL (R3127-3134).
- DDR statements S5/S8 as offsets from the expect file's invoice total (+105.00 / +5.00), computed by the test,
  never typed; revenue keeps its offset from the served revenue (R3135-3140).
- Screen literals (`backend/tests/fixtures/ddr/lakeside-2026-10.expect.json`): re-pinned to served values, mapped to
  `M` in the packet (R3141-3148). After DD3d.4 the fuel actual is burned × price; the plan side still reads the typed
  plan until DD3d.5. Re-pin the actual-side literals here and the plan-side ones (target, difference, headline) once,
  in DD3d.5.
- `tools/dd_check.py` C-DD4 judges mini `diesel_l` and `fuel_cost` again (served = `M`); `EMU_FUEL` stays Σ invoices =
  fuel bought (R3149-3150).

### DD3d.5 Run-rate fuel budget (2.0; D-DD.166 A99-121 and A50-89, with D-DD.170 R3349-3363; S896-898)

- `tools/dd3_pure_run.py --leaves` records `quarter` per Site in `config/world/fuel-leaves.json` (keys R3356-3359;
  `tank_open_jul` from the run's ledger at 2026-07-01 00:00 local; `deliveries_jul_sep` from `fuel-notes.json`).
  `plan_diesel_l` = round_half_even(1.10 × consumed_jul_sep / 3), whole litres.
- `simulator/assetops_simulator/world/scope.py` `RUN_WRITTEN["MINI_GRID"]["plan"]` = the seven keys of R3354-3355.
- `M` (one commit series, rev bump, written from the tool): October `plan.diesel_l` = `plan_diesel_l`;
  `plan.diesel_cost` = litres × declared price; plan necessary = plan litres, candidate and unexplained 0; contribution
  and variance by `M`'s identities; the basis string and class ASSUMED on the fuel plan line (A52-56, A104-107). July-September
  plans by `per_day`. Bridges by their stated formulas (D-DD.131), Portfolio totals.
- Then D-DD.164's acceptance steps 1-7 (R3206-3215) again: generate, `--restate-notes`, `--leaves --write`, `M`
  from the tool, **generate again byte-identical**, `--check` exit 0 at all three Sites, the D-DD.30 chain
  (`history.json`, `derived-values.json`, `missing-records.json`, mock fixtures) and re-pins (D-DD.93). If step 5
  differs, stop: a run-written key is missing from the table.
- The budget export rows (`exports.py` `_budget_records`) follow the new plan; goldens re-pin and are listed.
- DDR expect file: the plan-side literals re-pinned to served values (projected: Portfolio about −196.60 against
  plan, Grow −97.00, Optimize about −99.60; A72-80). Anchored-figure doc sweep: every `check_manifest.py` anchor that
  moves is updated to the check's value, nothing else.
- Pre-flight confirm (A114-116): no reader serves `history.json`'s July-September *actual* litre leaves; if one does,
  stop for the Architect.

### DD3d-b: facts the code fixes (D-DD.162)

- Protected: revenue, `metered_kwh` and `billed_kwh` keep their `stated_by` (structure v5 changes only `fuel_cost`).
  The reconciliation's stored field and CLI flag are a data contract and keep their names. The cold and EV plans are
  untouched (A40-48). The development tenant's publisher behaviour is unchanged when `ASSETOPS_TENANT_SLUG` is unset.
- Names: price key `diesel_price_per_litre`; assumption words from `sources.ASSUMPTION_WORDS["diesel_price"]`.
- Decimals: money compared as `Decimal` to the cent; plan litres whole, half-even; ledger fractions as printed.
- Ids: fixture idempotency keys `world-diesel-price-<site lower>-v1`; no other id formed.
- Tests: the `M`/tool parity test and the scope guard live in `simulator/tests/world/`; nothing under `backend/`
  imports `simulator`.

### DD3d-b: plants

(a) Restore `fuel_cost`'s `stated_by`: Mto's October fuel cost reads 0 and C-DD4 FAILs. (b) Remove Mto's price
fixture: G4 FAILs "missing price". (c) Drop `plan` from `RUN_WRITTEN`: step 5's second generate differs (or the
scope guard test fails). (d) Type 700 into `M`'s Kobo plan litres: the `M` parity test FAILs.

### DD3d-b: reach set

The structure and money suites: `test_3b1*`, `test_3b2*`, `test_3b3*`, `test_3b4*`, `test_3b6*`, `test_3b7a*`,
`test_4a*`, `test_4b*`, `test_4d*`, `test_5a*`, `test_5b*`, `test_5c*`, `test_6a*`, `test_6c*`, `test_6h*`,
`test_3a7*`, `test_ch6*`, `test_ch5d1_optimize_card.py`, `test_fuel_cost_v2{,_postgres}.py`, `test_pr1_price_action.py`,
`test_s4_assumptions_postgres.py`, `test_data8_kisiwa_productive.py`, `test_ch9b3_mill_verdict_postgres.py`,
`test_ddr_rehearsal_{check,postgres}.py`, `test_ds4_world{,_postgres}.py`, `test_dd2_check.py`, `test_dd3c_*`;
`golden/6h_parity.json` readers; simulator `world/*` (`test_scope_run_written.py`, history and exports goldens);
`check_manifest.py`. Guards as DD3d-a. The structure-version bump may reach structure-snapshot goldens: re-pin each
to its regenerated value and list it.

### DD3d-b: done when

All tests pass; plants fail and are reverted; the seven DDR lines and t12 pass; reach set green or identical to
main. Packet: mid-build question count; every literal old → served → `M` figure; the two `history.json` hashes
(step 1 and step 5) and the `--check` logs; the quarter table per Site (A72-80 to compare); every re-pinned golden.

---

## Rules that apply (by id)

D-DD.17, D-DD.18, D-DD.30, D-DD.53, D-DD.92, D-DD.93, D-DD.96, D-DD.128, D-DD.130, D-DD.131, D-DD.147 (amended),
D-DD.152 (replaced by D-DD.153), D-DD.153, D-DD.154, D-DD.155 (tanks stay), D-DD.156, D-DD.162, D-DD.163, D-DD.164,
D-DD.166, D-DD.168 to D-DD.171.

## Merge order and shared files

- DD3b → **DD3d-a** → **DD3d-b** → DD5b (DD5a is independent). DD3d-a and DD3d-b may be built side by side; DD3d-b
  merges main after DD3d-a and reruns its reach set.
- Shared: `tools/dd_check.py` (DD3b → DD3d-a → DD3d-b → DD5b → DD6), `M` and `check_manifest.py` (DD3b → DD3d-a →
  DD3d-b), `world/exports.py` and `tools/world_history.py` (DD3b → DD3d-a → DD5b), `prepare_clock.py` (DD3d-a →
  WK-SC).
- Coordinator merge check: for each part also `simulator/tests/world` and, for DD3d-b, D-DD.164 step 6 (`--check`)
  on the merged tree.
- Guards S1028-1040: databases `*_test` or `assetops_world_audit*` only; never ports 5490/8990/8992; scratch deleted.
