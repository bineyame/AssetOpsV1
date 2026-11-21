# 0M handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Checked against `main` at `5a3987dcd`: 0K2's `replay_study.py` and `host/tests/kobo_season.py` do not exist yet, so
every 0K2 name is judged from 0K2 `spec.md` §2.5 and §3, not from code.

- **R1 (done)** (spec §4 H6, reviewer-guide P2). P2 (customer steps on weekends too) is said to fail H6 "22
  weekdays". H6 only pins a calendar fact (September and October 2026 each have 22 weekdays; I confirmed both are
  22), which no implementation can break; P2 fails only M1 and H2 (the 8-day window holds Sat 5 and Sun 6). The
  monthly claim behind D-0M.5 (44 customer days, 3,300 kWh over the 61 days) is never asserted by anything. Expected:
  an M-test on a stub port over a 61-day window asserting `len(customer_days) == 44` and `customer_kwh == 44 × 75`,
  and P2 listed against it, not H6.
- **R2 (done)** (§2.1 `MIN_DEMAND_DAYS`, §2.2 step 2, P15). The header says "28 days over the customer's window",
  the code counts admissible days (every step of the day has generator and SOC data) whatever the customer's weekdays:
  a Monday-to-Friday customer on 28 admissible days has 20 customer days. Which is meant? Also P15 (`= 14`) is said to
  fail H7, but H7 uses 8 days, short under 14 too; only the H6 constant pin catches it. Expected: say "admissible
  days of the window" (D-0M.10 already reads "design §4.3: covering the window"), and add an M5 boundary: 27
  admissible days is `SAMPLE_TOO_SHORT` with zero calls, 28 proceeds.
- **R3 (done)** (§2.1, D-0M.11, §6 Q5; owner-away row 37). Only `HeadroomResult` carries `input_class` and
  `evidence_class`; `DemandOutcome` and `CapacityOutcome` carry neither, and `6g` will take outcomes one at a time,
  so a figure can leave the result unlabelled. Expected: both outcome types carry `input_class` and `evidence_class
  = "MODELLED"` (copied, validated like the result), the tool's JSON carries them and a plant line ("Kobo template
  edited to Mto's manifest facts; loads halved; simulated season"), and a test scans the tool's JSON and
  `headroom_replay.py` for any word that adopts a design value ("reproduces", "validates", "confirms", "replaces").
  The packet's design-value column is headed "design value, unchanged (held, row 37)". Today only the packet is
  specified, and §1's "until spike M reproduces them" (Why next) should read "until the owner rules (row 37)".
- **R4 (done)** (§2.3, §5 packet). The design values are October's (3 days, 225 kWh, 68 L); the outcome's
  `days_without_headroom` and `kwh_beyond_headroom` are whole-window figures, and only litres have a month split. The
  packet cannot set October beside the design without a hand-cut outside any test. Expected: `kwh_beyond_headroom_by_month`
  and a by-month count of days without headroom (via `by_month` on the per-step beyond-headroom values), checked in
  H2 against the reader's own loop.
- **R5 (done)** (§4 M1, H4, reviewer-guide plants). Three plants survive. (a) The kernel serves loads by their total
  (D-0K1.19), so H1 to H4 cannot see a wrong host load; only M1 and H5 can, and H5 must assert per-step equality
  by id on a real run's request. (b) Reduced headroom read with the full PV (not `pv_r`): H4's "REDUCED days include
  FULL days" holds for equal sets, and M4 checks the request, not the figures. Expected: a plant P18 and H4
  asserting every reduced `DemandOutcome` equals the reader's (with the precondition that the reduced
  `kwh_beyond_headroom` strictly exceeds the full one for the huller). (c) Boundary steps: M1 pins the first step
  (07:00Z) but not the last; expected: also 11:55Z has the customer, 12:00Z does not, and 06:55Z does not.
- **R6** (§0 Start, D-0M.1, §8 Q1). Is the dependency real? What 0M needs of 0K2 is not only the calibration rule:
  it is every §2.5 helper plus `kobo_season.py` (`base_run`, `season_inputs` with `load_scale`, `observed_series`),
  all absent on main. A stub of `calibrate` would unblock neither `mto.py` nor H1 to H7, and two copies of the rule
  is what D-0M.1 forbids. Expected: the dependency stands; the start gate is "0K2 merged", and the packet records
  the merge commit. Unit 1 (M1 to M7, stub port) could start earlier only if 0K2's helper signatures were frozen
  and its Unit 1 reviewed; it gains nothing against lane C's schedule (0K2 days 8 to 10, 0M days 10 to 12), so
  decline stacking and say so.

## Implementer questions

Pre-flight on `main`: I ran the Mto edit through `kobo_draft("kobo-mini-grid-prolonged", 5-minute, mini-grid v7)`
for 8 days, scratch only, with the spec's `MTO_FACTS`, the four ratings and the tank (`set_property`, then `rating`
edits), at inverter limit 50 and 25: both `READY`. Without `valid_from = 2026-08-01` (what `season_site` does) both
are `BLOCKED`, since `kobo_site` stamps 2026-09-01, after the window start. The edits are accepted; every
`MTO_FACTS` key exists on its component. The 74.47 L and 51.40 L probe figures I could not check (no
`kobo_season.py`, no `season_inputs`).

- **I1 (done)** (§2.1 `CustomerLoad.customer_id`, §2.2 steps 1 and 5; `contracts/.../forward_replay.py:41`).
  `CASE_ID` allows up to 40 characters; the reduced case id is `reduced-<customer_id>`, up to 48. A long id passes
  step 1, runs `1 + k` replays, then `ForwardReplayRequest` raises `ValueError` in step 5, breaking "every refusal
  before the port is called" (§6 Q4) and the `HEADROOM_REFUSALS` contract. Expected: step 1 also refuses an id
  longer than 32 characters (`CUSTOMER_ID_INVALID`), with an M5 case at 33 characters and zero calls.
- **I2 (done)** (§2.1 `ReducedCapacity`, §2.2 step 5). `inverter_limit_kw` is the caller's and nothing ties it to
  `reduced.run`'s frozen `inverter-ac-limit`, which the port does not expose. Given 25 on a run frozen at 50, the
  study replays a full-limit plant with PV clipped to 25 and labels it reduced; given 30 on a run frozen at 25, the
  port refuses `REPLAY_SERIES_INVALID` (51 > 25 never; 30 > 25) only after the baseline and `k` customers have run.
  Nor is it checked that `reduced.run` differs from `run` only in the limit. Expected: after the `reduced` call,
  `clipped_offsets` must equal the offsets where `pv_r == inverter_limit_kw`, else `REDUCED_CAPACITY_INVALID`
  (an M4 stub case and an H1 case with a mismatched limit), and the packet's pre-flight print of both runs'
  `inverter-ac-limit` becomes a test pin; or the Architect states that the caller's trust is the boundary and the
  half-run port refusal is accepted.
- **I3** (§3 `mto_site`). `mto_site` must start from `season_site` (its `valid_from`), or the run is `BLOCKED` (above).
  §3 says so by writing `season_site(doc)` first; say it in a comment and have H1 assert `execution_status ==
  "READY"` for both runs, so a later edit of the order fails loudly.
- **I4 (done)** (§3 "facts Mto does not state keep the Kobo template's values"). The list is incomplete, and D-0M.2's
  "every edit traced to a stated fact" needs the complete one. Also kept from the template and the season: tank 20,000
  L (rating too) and start fuel 15,000 L (`season_site`, `SEASON_START_FUEL_L`), start SOC 48%, the load ratings (25,
  10, 40 kW, now above half their series), the Kobo irradiance windows and the overcast calendar, and the site id
  `KOBO-001`. Two traced edits also remove a margin: PV 50 against inverter 50 (Kobo's 60 against 50 clipped), and the
  reserve edit (30) equals the template's, a no-op. Expected: the packet lists each kept value and each edit against
  its manifest line, H6 pins the kept values that the replay reads (tank, start SOC and fuel), and the 0.52 behind
  the `1/2` scale (6,000 / 11,580) is stated as the only derivation.
