# Build card: DD6, the world built and served

Part DD6 = DD6.1 to DD6.3 with D-DD.133 to D-DD.136 (D-DD.137 outside DD). **4.75 u**, branch `task/DD6-world`, one
discovery review. Card by the DD lane Architect, 23 Nov, under `.ai/ROLE_CONFIG.md` "Fourth audit" (a). Line numbers
are `specs/DD-demo-data/spec.md` (S) and `rulings.md` (R) as at `task/DD-rulings-22`. Read only the lines named here,
then the code. A question the lines do not answer stops only the affected unit and goes to the lane Architect; count
it in the packet.

## What you build

1. **World check C8 (1.25; DD6.1 S928-929; D-DD.133 R2309-2319; D-DD.84 R1237-1250; D-DD.153 R2765 onward).**
   - C8 runs `python tools/dd_check.py --database-url <clone> --json --world-manifest <path>` as a `world.run_step`
     subprocess before the clone is dropped (the ASGI client mutates `os.environ`, `dd_check.py:150-158`). Exit code
     = C8's state.
   - A result is PENDING when every failing line names its closing unit (Q11, Q12, IA-P3, D-DD.137's `WK-SC`, "IA-P
     lane" for the Decisions/Actions pages). C8 = no FAIL; PENDING lines are listed in the world check output. A stub
     is a FAIL; none may remain.
   - Live here: C-DD9 (S963, cells S977-988), C-DD10 (S964; judges Lakeside, Harvest Cold and Metro Bus pending Q11,
     D-DD.11), C-DD15 (S969; `_rung` writes `seconds` and `cap_seconds` into the world manifest, read by
     `--world-manifest`), C-DD18 (S972), and C-DD17's served part (S971): each Site-month's `unexplained_l`
     observation state and band equal D-DD.153's table (Kobo Jul-Sep INSIDE_TOLERANCE band 50, Oct RAISED band 50;
     Kisiwa INSIDE_TOLERANCE band 100 every month; Mto NO_GAP). Read the observation through the read D-DD.133
     names; if it does not carry the observation, stop for the Architect.
   - C-DD19 prints "judged in world check C5 (D-DD.84)" and is not counted.
   - A "No monthly figures … yet" row or a windowed span does not count as output (D-DD.26, R138-149).
2. **WK for three operators (2.75; DD6.2 S930-938; D-DD.134 R2320-2333; D-DD.27 R150-156; D-DD.135 R2334-2350).**
   - `assetops.walk-definition/2` beside `/1`: `statements` may be `[]`, `expect` may be null, a statement carries
     `fuel_cost` or `energy_cost`; file `walk-layer4-v2-<slug>.json`; `world` must equal the world definition's.
   - `tools/world.py` copies each `<slug>.statements.json` (S613-622) into `inputs/<digest>/<slug>/statements/` (in the
     inputs digest); the walk manifest records the path. `prepare` records a tenant's statements only when its
     `snapshot_months` is non-empty, `--as` the tenant's finance lead (DD1's email rule). Cold and EV statements are
     not recorded in DD (`energy_cost` recording is Q11's).
   - Snapshot, W4, W7 and S2 count only tenants and months in `snapshot_months`; a skipped step is recorded
     `{"step", "skipped": true}`.
   - `demo_workflow` items: the product's permissions win (executive-only `action.agree`, `decision.choose`); `M`'s
     `created_by`/`chosen_by` corrected to who may act, the manager kept as `proposed_by` where `M` has it. Due dates
     need the story clock (not on main), so every item is listed "pending: story clock (D-DD.137)" and C-DD9's
     Decisions, Actions and Results cells are PENDING with that unit and "Decisions/Actions pages read 6a and 3C2
     rows (IA-P lane)". `prepare` never writes rows (D-DD.27).
   - One walk database and label for the three tenants. `serve --tenant <slug>` sets `ASSETOPS_TENANT_SLUG` for the
     child on ports 8991/5491; a serve whose recorded tenant differs is stopped by PID first. Ports 8990, 5490, 8992
     and the owner's walk stay untouched.
3. **The build, measured, and the runbook pass (0.75; DD6.3 S939-943; D-DD.136 R2351-2357; D-DD.15).**
   - One build on a quiet machine: `systemd-inhibit --what=sleep:idle` around it, `--cap-seconds 28800`.
   - Record each rung's seconds and size and the cold and EV seconds per Site-day (C-DD15). DS7 is pulled only if
     L2 exceeds 4 h (D-DD.15).
   - Evidence `/opt/assetecon/evidence/DD/<UTC date>-<commit12>/`, created by the build step.
   - Apply `specs/DDR-rehearsal/packet.md` §"Where the runbook was unclear" 1-10 identically to
     `Docs/engineering/operator-deep-dive-runbook.md` and `specs/ON1-operator-tenant/runbook.md`; then
     `test_ddr_rehearsal_check.py`.

## Rules that apply (by id)

D-DD.11, D-DD.15, D-DD.26, D-DD.27, D-DD.28 (R157-167: `dd_check` reads the product through an in-process ASGI client,
no port), D-DD.84, D-DD.133 to D-DD.136, D-DD.137 (pending listing only; `WK-SC` is built only on the owner's yes),
D-DD.142, D-DD.153 (C-DD17 served), D-DD.154 (the records C-DD17 and C-DD8 read are loaded by DD5b).

## Tests (each can fail) and plants

- `dd_check` unit tests: PENDING with a closing unit passes C8; a failing line without one FAILs; a stub FAILs;
  C-DD17 served judge on hand observation rows (one RAISED Kobo July must FAIL).
- `test_wk_walk_world.py`: `/2` walk definition read; statements staged in the digest; skipped steps; `serve --tenant`
  stops a differing serve by PID; a cold tenant records no statement.
- `test_ds4_world.py`: C8 subprocess step, exit code mapping, world manifest `seconds`/`cap_seconds`.
- Plants: (a) remove one month of Kobo readings from the clone: C-DD9 FAILs naming the cell; (b) declare no tank
  accuracy at Kobo: C-DD17 served FAILs on July (RAISED); (c) drop the closing unit text from a Q12 cell: C8 FAILs.

## Reach set (`preflight-remaining.md:146-148`)

`test_ds4_world{,_postgres}.py`, `test_wk_walk_world.py`, `test_dd1_check.py`, `test_dd2_check.py`,
`test_dd3_datasheet_check.py`, `test_ddr_rehearsal_check.py`, `test_on1_served_tenant.py`; simulator
`world/{test_dd2_checker_on_emulated_rows, test_history, test_dd2_nodes}.py`. Plus statement catalogue (D-DD.96),
check-decision-index, check-agent-workflow. Postgres through `tools/heavy-slot.sh --db-lane`.

## Merge order and shared files

- Starts after DD5b is on main (IA-P2 merged). Shared: `tools/dd_check.py`, `tools/world.py`, `tools/walk_world.py`
  (DD5b → DD6). The demo is accepted on one rebuild after 0K4f, Q11 and Q12 (S990-1011, owner Q8); DD6's first build
  lists every pending cell with its closing unit.
- Guards S1013-1024 (one full build at a time, cap twice the expected time, never ports 5490/8990/8992).

## Done when (S1058-1071)

- C1 to C8 pass on the check clone with L2's seconds recorded; every pending cell listed with its unit.
- Packet: mid-build question count, the build's seconds per rung, C8's PENDING list, the runbook notes applied.
