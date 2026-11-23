# Build card: DD5b, disorder and the world ladder

Part DD5b = DD5.2 and DD5.3 with D-DD.141 (and the one-line call D-DD.154 adds). **4.25 u** (3.75, +0.25 by D-DD.160, +0.25 by D-DD.167), branch
`task/DD5b-ladder`, one discovery review. Card by the DD lane Architect, 23 Nov, under `.ai/ROLE_CONFIG.md` "Fourth
audit" (a). Line numbers are `specs/DD-demo-data/spec.md` (S) and `rulings.md` (R) as at `task/DD-rulings-22` (D-DD.167 onward: as at `task/DD-cards-2`). Read
only the lines named here, then the code. A question the lines do not answer stops only the affected unit and goes to
the lane Architect; count it in the packet.

## What you build

1. **Disorder files and steps (1.5; DD5.2 S905-906, table S624-637, amended by D-DD.141 R2420-2435; D-DD.25
   R131-136; D-DD.53 R567; D-DD.61 meter register R709-711).**
   - `<slug>/disorder/<ID>/` holds loader-legal names (`load_emulated_exports._files`). Each `L1.disorder:<ID>` step
     runs `load_emulated_exports --dir` on its folder with `fail=False`, records the exit, compares it with S624-637's
     expected exit (recorded, not failed: R133).
   - DUP-1: byte copy of Mto's October billing rows; exit 0, 0 new revisions.
   - OOO-1: the late file repeats the 26 Oct note's `source_record_id` with `recorded` 2026-11-04 (second revision by
     `row_digest`). The note's day is set by the test (D-DD.53); DD2 already writes it in October's file (R575).
   - TENANT-1: a Harvest Cold canonical `customer_invoicing.json` whose batch `tenant_code` is `lakeside-power`;
     expected exit 3, `INTAKE_TENANT_MISMATCH`. C-DD13 drops its `TENANT-1: pending (DD5.2)` line and passes only when
     both clauses hold (D-DD.40, R281-284).
   - MAP-1: `world/meter_register.py` writes `lakeside-power.meter_register.json` (`meter_register`, `source_system`
     `illustrative-meter-register`, METER_ASSIGNMENT, `effective_from`), six Mto meters in code order from
     2026-10-03, kWh from `M` through a module table with a manifest parity test (D-DD.51, R555); staged JSON.
   - FX-1 and LATE-SETTLE-1: planted by `exports.py` outside the history months; goldens re-pin (D-DD.93, R1520).
   - GAP-1: no row; `unwritten.json` lists it. CLOCK-1: "planted, not built" (D-DD.25); list the manifest's
     "corrected; flagged" in the packet for the design-doc alignment pass.
   - C-DD14 goes live (S968).
2. **Definition `/2` and the ladder (2.25; DD5.3 S907-924; D-DD.28 R157-167; D-DD.60 R668-670; D-DD.66 R778-782;
   D-DD.140 R2404-2415).**
   - `backend/conversions/world-layer4-v2.json`, `assetops.world-definition/2`: every `/1` key kept; adds `months`
     ["2026-07" … "2026-10"], per tenant `profiles` and `snapshot_months` (Lakeside the four months; Harvest Cold and
     Metro Bus `[]`), `not_built` `[]`, `disorder` (unit 1's steps) and `telemetry` (`source`, `span` equal to
     `READINGS_SPAN` (D-DD.103, R1829), `writer_version` 1).
   - `read_definition` dispatches on format; `/1` key set and the `batches == 0` guard (`world.py:739`) unchanged for
     `/1`.
   - L1 adds `L1.admit:<slug>:<profile>`, `L1.staged:<slug>` (after the commercial step), `L1.site-inputs`,
     `L1.telemetry` (copies only `*.readings.json` and `measured.json` into `inputs/<digest>/<slug>/telemetry/`; the
     readings manifests stay out, they hold `private_parameters`), `L1.measured-books`, the disorder steps, and, per
     mini-grid tenant, a call to DD3d-a's `load_fuel_records(dir, tenant)` (D-DD.154 with D-DD.168, R3286-3328; it
     records each record at its own time and runs only under `prepare_clock`'s check, which admits the world rung
     names; no unit added), and `L1.prices:lakeside-power`: three `publish_assumption fixture --site <SITE> --file
     backend/conversions/world/lakeside-power.diesel-price.<SITE>.json` calls under `world.env` (D-DD.169,
     R3330-3347; no unit added).
     F is `inputs/<digest>/site-inputs.json`.
   - L2 adds the drain (enrol, then `scheduling.run tick` to done); the drain joins `L2_STEPS`. Snapshot and observer
     run per tenant's `snapshot_months`.
   - Inputs digest covers every input file listed in S917-919 plus `fuel-records.json`; `sealed/` is not in it.
   - World check: C5 runs the two parity files as two `harness_run` calls (D-DD.140); C4 judges October only.
   - C4 after the drain (D-DD.177): actual `fuel_cost`, `cost_to_serve` and `contribution` return to "E" (Kisiwa's `om`
     override stays, so its two totals stay "B"), and Mto's actual `diesel_price` with `L1.prices`. Served litres are to
     the millilitre: `diesel_l` passes when its half-even whole litre equals `M`'s, and `fuel_cost`, `cost_to_serve`,
     `contribution` pass within 0.5 L × the Site's price. Every other cell stays exact. A "B" cell the readings fill
     stops for the Architect with its value.
   - C-DD4's fuel clause (D-DD.180) must pass on the loaded world; it fails by name before the fuel records load.
   - (0.25 u, D-DD.167, R3260-3284.) The rung manifest records every `sealed_dir` from the load step's output line;
     C6 globs only those (`<dir>/*.batch.json`); `drop_db(name)` removes the `sealed_dir`s recorded in that rung's
     manifest unless another live rung's manifest records the same folder (the check clone shares L2's).
   - `CODE_PATHS` and `CHECK_CODE` gain the paths of S920-924.
   - (0.25 u added by D-DD.160, R round 23.) `stored_books` also fetches TARIFF_SCHEDULE, FLEET_ROSTER and DEPARTURE.
     C-DD7's mini-grid clause goes live here, its only owner: load served + unserved = `delivered_kwh`, exactly, with
     unserved read from the loaded world's `<slug>/telemetry/measured.json` `unserved_kwh` (no readings channel
     carries it). The pending text "DD3b/DD5" becomes "DD5b". Test: the clause fails on a hand row with 1 kWh
     moved from served to nowhere.
   - (D-DD.158, DD4b follow-up review L1.) The same fetch passes the loaded world's EV `measured.json` to
     `judge_meter_books(..., measured=)`, so C-DD7's EV window clause (`windows.2200_2400`/`0000_0500`) is judged
     live, not pending. Test: the clause fails on a planted 1 kWh window shift.

## Facts the code fixes (D-DD.162)

- Protected: the `/1` definition path (key set, digest, `batches == 0` guard) and the Lab replays' v3 conversions
  (D-DD.161: only `onboard_operator apply --bindings` passes `world_conversion=True`).
- Names: device and channel ids come from the Foundation (`/2` files), e.g. the depot import is `site-meter`, never
  a ruling's typed name.
- Decimals: C-DD2 to C-DD7 compare `Decimal` values, never strings (readings print "4.000", envelopes "4").
- Ids: EV `session_id` is the pack's, carried by the writer and copied by the sealer (D-DD.161); disorder steps never
  re-form an id.
- Tests: nothing under `backend/` imports `gateway`, `host` or `simulator` (tests included); such a test lives in
  `host/tests/` or `simulator/tests/`.

## Rules that apply (by id)

D-DD.25, D-DD.28, D-DD.40, D-DD.51, D-DD.53, D-DD.60, D-DD.61, D-DD.66, D-DD.74 (R890-940: L1.exports passes `--tenant
<slug>` per definition tenant; DD5.3 places cold and EV by naming their tenants, R921), D-DD.93, D-DD.103, D-DD.140,
D-DD.141, D-DD.142 (R2436-2445), D-DD.154 (the load call only), D-DD.160 (C-DD7 mini clause, the fetch), D-DD.161, D-DD.162,
D-DD.167 (sealed folders), D-DD.168 (the loader's check), D-DD.169 (the price step).

## Checks that go live or change

- C-DD13 TENANT-1 clause live (S967). C-DD14 live (S968).
- C-DD2 to C-DD7 (S956-961) are judged on the loaded store from here; C-DD2 includes the two fuel-record kinds per
  mini-grid Site-month (D-DD.154). A failure is reported with its detail, never tuned.

## Tests (each can fail) and plants

- `test_ds4_world.py`: `/2` read (keys, span equality refusal), `/1` unchanged (digest and guard), L1 step list and
  order, the drain in `L2_STEPS`, skipped steps recorded `{"step", "skipped": true}` for an empty `snapshot_months`.
- Disorder: each step's recorded exit equals S624-637; TENANT-1 stores no row in either tenant.
- MAP-1 module table equals `M` (parity); FX-1/LATE-SETTLE-1 goldens re-pinned and listed.
- Inputs digest: changing one byte of any input file (incl. `fuel-records.json`) changes it; `sealed/` does not.
- D-DD.167: C6 judges only recorded folders (a planted extra folder with a bad batch is not judged); dropping L1
  removes L1's folder and keeps L2's. `L1.prices` publishes three revisions; a re-run answers with the stored ones.
- Plants: (a) TENANT-1 with the right tenant code: step exits 0, C-DD14 FAILs; (b) drop `L1.staged`: C-DD2 FAILs on
  the rate cards; (c) put a readings manifest in `telemetry/`: a test refuses (private parameters staged).

## Reach set (`preflight-remaining.md:143-145`)

`test_ds4_world{,_postgres}.py`, `test_ds4_batch_days{,_postgres}.py`, `test_ds4_bench_pipeline_postgres.py`,
`test_wk_walk_world.py`, `test_3a3_load_emulated{,_postgres}.py`, `test_dd1_check.py`; simulator `world/*` (exports
goldens). Plus statement catalogue (D-DD.96), check-decision-index, check-agent-workflow. Postgres through
`tools/heavy-slot.sh --db-lane`.

## Merge order and shared files

- Starts after DD5a, DD3b3, DD4.4 (DD4b), DD3d-a and DD3d-b are on main.
- Shared: `tools/world_history.py` and `world/exports.py` (DD4a → DD3b3 → DD4b → DD5b), `tools/dd_check.py` (… →
  DD3d-a → DD3d-b → DD5b → DD6), `tools/world.py` and `tools/walk_world.py` (DD5b → DD6). Merge main, rerun the reach set.
- Guards S1013-1024; evidence under `/opt/assetecon/evidence/DD5b/`.

## Done when

- All tests pass; plants fail as stated and are reverted; reach set green or identical to main.
- Packet: mid-build question count, each disorder step's exit, every re-pinned golden, the inputs digest's file list.
