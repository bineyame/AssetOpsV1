# DD rulings, round 2 (D-DD.17 to D-DD.34): the handshake answered

Architect (Claude), 2026-11-22. Answers the combined handshake (`handshake.md`, R1-R10 and I1-I15, on `main` at
`9036fb9fb`). D-DD.1 to D-DD.16 stay in `spec.md` §9; this file amends three of them (D-DD.4, D-DD.5, D-DD.10, each
named below). Owner words read: `owner/owner-demo-data-spec-2026-11-22.md`, `owner/owner-demo-data-answers-2026-11-22.md`,
`owner/owner-fuel-scope-2026-11-07.md` (Q2: "Generic 3.3 L/h, labelled"), `owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md`,
`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`.

**The class behind most findings (W6).** Rev 1 let the books and the readings each carry their own figure for the same
quantity (fuel split, cold kWh, EV band kWh, departures), and then asked a tolerance to reconcile them, which invites
tuning an output. Rev 2 fixes the class with one rule: *a quantity a meter, a tank or a log measures in the operating
world has one figure, the simulator's; the books that report it (a utility bill, a departure log, a fuel balance) take
it from the readings; the books that report decisions and purchases (sales, deliveries, invoices raised, budgets) are
inputs, and the readings follow them.* Sweep: every leaf of `history.rules` and every §3 source was classed as input or
measured (spec §4.0 table); every check comparing books with readings is now exact or a direction, never a tolerance on
a measured figure (C-DD7, C-DD17, C-DD20).

---

- **D-DD.17 Data-sheet labels reuse the existing basis vocabulary; Kobo's no-load rate is Assumed** (R1, R10, I5;
  amends D-DD.10's labels).
  - No new `source` value, no `source_document` key: the closed key set `foundation_parsing.py:103` is unchanged.
  - The basis lives in the existing `-basis` state properties (`sites/models.py:342-345`). DD adds three siblings with the
    same value set `{GENERIC_DEFAULT, MANUFACTURER_DATASHEET, SITE_TEST}`: `generator-rated-power-basis`,
    `specific-fuel-consumption-basis`, `battery-energy-capacity-basis`. It adds one value, `DATASHEET_FIT`, to
    `generator-no-load-fuel-rate-basis` only.
  - Label rule (SC-1 statement `component_property.basis`): MANUFACTURER_DATASHEET reads "Declared, from the
    manufacturer data sheet ({maker} {model}, {revision})"; DATASHEET_FIT reads "Assumed: fitted to the data sheet's
    stated points ({maker} {model}); the sheet states no value"; GENERIC_DEFAULT reads "Assumed: {basis}". Maker,
    model, revision and basis text come from `config/datasheets/kobo-equipment.json`.
  - Kobo's `generator-no-load-fuel-rate` default is **0.62 L/h, basis DATASHEET_FIT** (Assumed). It replaces the owner's
    3.3 L/h of 7 Nov only on the owner's answer to Q7; until then the default applies (W3) and the coordinator puts Q7 to
    the owner before DD3.2 commit 2. The owner's 3.3 L/h stays in the K8 replay study, which ran on the 40 kW set and is
    not re-run (`replay-studies.json` unchanged).
  - Basis texts are exact to the research (R10): round-trip efficiency "not stated by Pylontech; comparable LFP banks
    state 95-97 % in search excerpts (BYD Battery-Box LVS, Freedom Won LiTE), secondary, not read from the sheets";
    minimum load "not on the sheet; makers' general guidance: Caterpillar at least 30 % load; Cummins 30 % of standby
    rating (12 kW, 33 % of this set's prime); the lower, 30 % of prime, is applied". The generator's `document` entry
    names the MSF cross-check, and the slot says the fuel row was read from a scrambled text layer.
  - *Why:* owner Q6 ("unpublished values labelled Assumed with their basis"); the fit is not published. The mechanism
    already exists (FUEL-1 A1, 0K4b), so a second one would be two vocabularies for one fact.

- **D-DD.18 The served fuel split is the readings-fed one** (R2). For every month with readings, necessary, candidate
  and unexplained litres are the product's, from stored readings. `history.json`'s split leaves are used only to make
  the month's delivered litres (D-DD.32) and are never served or exported as split rows. *Why:* one figure per quantity.

- **D-DD.19 Fuel in the operating world: deliveries in, burn out, the tank between** (R2, R9).
  - Deliveries are inputs: each 400 L note of the books (DD2.1) is a tank delivery in the writer at the note's
    `occurred_at`. OOO-1's note enters the tank on 26 Oct (when the fuel arrived), whatever date it is recorded.
  - Burn is v8's (v9's at Kisiwa) on the Site's curve. The tank level is v7's sampled state, published as the tank
    level signal.
  - The story's unexplained fuel is a declared condition of the world: litres leaving the tank unburned, cause not
    stated. Per month it is the month's `unexplained_l` (Jul-Sep from `history.json`, October 120 L from `period`),
    drawn in equal parts at 02:00 local on each day of the month, largest remainder to 0.01 L. Kisiwa and Mto draw only
    what their own `unexplained_l` leaves say.
  - The tank starts on 2026-07-01T00:00 local at 50 % of its capacity (Assumed, declared in the readings manifest).
  - A delivery that would overfill the tank, or a tank that empties, is not corrected: the pack refuses (`TEL_PACK`) or
    the generator is fuel-limited and unserved energy appears, and C-DD8 fails.
  - Known before the build: DD3.2 commit 1 runs the writer purely (no database) on the three mini-grid Sites for July
    to October. The packet prints per Site-month: delivered, burned, drawn, tank minimum and maximum, the
    product-definition balance (opening dip + deliveries − closing dip − burned), candidate litres, and the same at 3.3
    L/h for Kobo. Any bound hit, or a C-DD8 or C-DD17 failure, goes to the Architect before DD3 merges.
  - The stated fallback, if a bound is hit: that Site's note schedule is restated from a declared reorder rule (two
    notes when the dip falls below 25 % of capacity). The books then follow the tank, and the owner is told the moved
    fuel figures before DD4. Nothing is tuned.
  - *Why:* the manifest's own balance is dips plus deliveries minus model (`fuel_balance`, `M:58`). A residual the
    product finds must have a cause in the world, not a gap between two generators.

- **D-DD.20 Bills follow the meter** (I6, R7; owner Q9).
  - The cold electricity bill's kWh per room-month is the room meter's (compressor plus auxiliary, from readings), at
    0.20.
  - The EV utility invoice's band kWh per Site-month is the Site meter's energy in each tariff band. DEMAND is the
    month's largest 30-minute mean import in kW.
  - Each DEPARTURE's `block_met` is true when the energy delivered to that bus by `departure_at` is at least its
    `required_kwh`, and `kwh_at_departure` is that energy.
  - These rows are written after the readings, by `world_history.py exports --telemetry DIR`.
  - Their `history.json` and `period` leaves (cold `kwh`, energy cost; EV `peak_kwh`, `offpeak_kwh`, `kwh_2200_2400`,
    `kwh_0000_0500`, `max_kw` and their costs) are listed in the build manifest `meter_billed`, with the generated value
    beside the metered one for information. They are excluded from C-DD4 and checked exactly by C-DD7.
  - *Why:* the utility bills what the meter reads; a 3 % tolerance between them could only be met by tuning 13 thermal
    properties (I6).

- **D-DD.21 Mini-grid v9: several generator and PV-inverter units** (I4; amends D-DD.4).
  - `MINI_GRID_V9_MODEL` (`model_profile_version` 9) is v8 plus unit lists. The full rules are in spec §4.3.
  - With one generator unit and one inverter unit it produces v8's bytes; the parity test (C-DD19) proves it on Kobo's
    October inputs.
  - Kobo runs v8 (0K4f's study frame); Kisiwa and Mto run v9.
  - The writer runs every Site on its `/2` onboarding foundation, not a shipped template (I4 default), so the stored
    Site and the simulated Site are one.
  - *Why:* Kisiwa's second set and Mto's second inverter are the Protect beats. An aggregate would hide the failed unit
    the warranty and cover questions are about.

- **D-DD.22 cold-thermal/2: occupancy, compressor efficiency, auxiliary load** (I6; amends D-DD.4).
  - The pack gains crates in the room as state, respiration and field heat, produce thermal mass, a compressor COP, an
    auxiliary load and an efficiency condition. These are private load parameters, not Foundation properties: the
    product sees the 13 declared properties and the meter, as it would at a real Site.
  - Rules and per-room values are in spec §4.4. With zero load terms, COP 1 and auxiliary 0 it produces cold-thermal/1's
    bytes (C-DD19).
  - Kirinyaga's drift is the efficiency condition `f_m`: 1.05, 1.10, 1.17 from `history.sites` and 500/403 for October
    (5,000 / 4,030, `M:511`). It divides the COP and is applied as a private condition, never as a Foundation change:
    the product is meant to find it, not be told it.
  - *Why:* occupancy and efficiency are the cold stories, and rev 1 had no path from either to the meter.

- **D-DD.23 EV: depot load manager and the plug-in practice** (I6).
  - The writer runs every charger of a depot in lockstep, one `ev-charger` 1 instance per charger, each with
    `site_limit_kw` set to its own rating.
  - Each minute a depot load manager shares `ev-site-import-limit` among the charging connectors. It uses the pack's own
    1 kW round-robin with a persistent pointer, across chargers by (charger, connector) id, capped by connector and
    charger ratings and by the bus's remaining need. It passes each share to the pack as `REQUEST_KW`.
  - The practice is an input. At Embakasi, a share `p_m` of the buses plug in on arrival and the rest at 22:00 (the end
    of the peak band). `p_m` is the manifest's declared peak share read as the depot's practice: 0.36, 0.43, 0.49, 0.55.
    It is never inverted from a target. The metered peak share is the output.
  - At Kasarani and Ruiru every bus plugs in at its window start.
  - The roster, plug-in times and faults are in spec §4.5.
  - *Why:* the import limit binds across chargers, which one-charger packs cannot see. Reading `p_m` as practice keeps
    the story's cause (the depot charging on arrival more each month) without solving for the metered figure.

- **D-DD.24 Source profiles: column tables, a `bool` type, tariffs as canonical JSON** (I7; amends D-DD.5).
  - Every profile's column → path table, constants and coded maps are in spec §5.2 and §5.3. Storage invoicing splits
    into an invoice file (CHARGE) and a receipt file (RECEIPT), because a profile writes one kind.
  - The cold rate card and the EV tariff schedules are TARIFF_SCHEDULE records in `canonical-json-v1`, written by
    `records.py` as today. A CSV cannot carry `bands`, and DS1b already writes them. The `cold-rate-card` profile is
    dropped.
  - DEPARTURE keeps its profile through a contract change. `layouts_v1.TYPES` gains `bool`; a `bool` path must carry a
    `map` whose values are exactly `{"true", "false"}`, the one exception to "a map sits only on a coded path". It has
    its own contract tests (DD2.2).
  - Each profile ships `<id>.sample.csv` and `<id>.expected.json` and is admitted with `--expected` and `--as` the
    tenant's analyst.
  - *Why:* owner rule "ingest works for any Site". The bool type is the general fix: any log with a Y/N column.

- **D-DD.25 Disorder: a planting table per test** (R6). Spec §5.5 gives, per test, the file, the rows, the load step,
  the expected product result and what C-DD14 asserts.
  - TENANT-1 and DUP-1 run as their own L1 steps with an expected exit, recorded, not failed.
  - CLOCK-1 is planted in the readings as stamps 4 minutes ahead of the true minute (the charger's clock runs
    fast). It is admitted on the bulk path, and its correction is reported "not built".
  - *Why:* claim only what was tested.

- **D-DD.26 The range rule and the four categories gate the served demo** (R3, R4; owner Q8).
  - C-DD9 judges a page × Site type × range cell table (spec §8.1). C-DD18 asks that each served tenant shows each
    outcome category on October.
  - A "No monthly figures … yet" row, or a windowed span, does **not** count as output for the range.
  - DD's served-demo acceptance (§10 Q2, Q8) is taken on the one rebuild after 0K4f, the Q11 unit (cold and EV monthly
    figures) and the Q12 task (the 31-day caps). Both stay queued after IA-P with their own specs. DD4's first build
    lists every pending cell by the unit that closes it. Nothing is cut.
  - Ruiru leads **Grow revenue**: the city's six-bus route offer is new contract revenue taken on existing chargers.
    The route's revenue reads "Not available yet (route contract not in the books)". The avoided chargers are its
    capital side, under Protect asset and capital.
  - *Why:* owner range rule (2026-11-12) and the four categories (2026-10-29, reaffirmed 2026-11-19).

- **D-DD.27 Choices and Actions are made by WK `prepare` through the product's commands** (R8).
  - DD6.2's `prepare` creates `demo_workflow`'s decision records and Actions through the 3C2 and 6a commands, as the
    named people, at their manifest times. It never writes rows.
  - An item whose command is not on `main` at DD6 is listed "pending: <unit>" in the packet, and C-DD9 reads that page
    as its empty state.
  - *Why:* "a person acts and tracks" is a beat; who creates the items must be named.

- **D-DD.28 The world ladder judges the new world** (I8, I10, I11, I13, I14). Spec §7 DD5.3 and DD6.
  - C6 judges the sealed batches, written beside the inputs at sealing as `<slug>/sealed/*.batch.json`.
  - C4 judges October only; the history months are C-DD4's.
  - `CODE_PATHS` and `CHECK_CODE` gain the paths listed in spec §7. C5 runs both parity files. C8 runs `dd_check.py`.
  - `/2` keeps every `/1` key and adds §7's.
  - The Site-inputs file `F` is `assetops.world-site-inputs/1`, made by a pure function in DD3.1.
  - The inputs digest covers every input file. The drain joins `L2_STEPS`.
  - WK skips the rebuild, W4 and the statement steps for a tenant with no snapshot months, and records them as skipped.
  - Sealing runs under `world.env` for the tenant. `*.batch.json` stays accepted for `/1`.
  - `dd_check.py` reads the product through an in-process ASGI client on the app factory and opens no port.

- **D-DD.29 Onboarding details** (I1, I2, I3, I15).
  - The new apply step enables the gateway and each source through `provision_gateway enable-gateway` and
    `enable-source` (subprocess), for `data: emulated` files only. A second apply changes nothing.
  - A batch is one (Site, source, local day), with `sequence_epoch` 1 and sequences in reading order. A unit test shows
    the largest source-day fits under 1 MiB.
  - Every `/2` file and binding set has `valid_from` 2026-06-30T21:00:00Z (local midnight on 1 July).
  - The DD1.1 refusal sentence goes beside `ONBOARD_VERTICAL`'s current one in `onboard_operator._SENTENCES`. The
    basis labels go in SC-1.

- **D-DD.30 Kobo's template v4 moves back to 0K4f; DD restates the world's Kobo** (I9; amends D-DD.10's split).
  - DD writes the data-sheet values into Lakeside's `/2` onboarding file and into the manifest's Kobo `physical`. It
    regenerates `history.json`, the history, records and export goldens, the pinned export digests and
    `derived-values.json`, and re-runs `check_manifest.py` and `check_alignment.py`. Every moved figure is listed, none
    hand-edited, and §0's "golden digests unchanged" is withdrawn.
  - `config/site-templates/kobo-mini-grid-60kw.yaml` stays v3 (40 kW), and the lab tests and the K8 study stay on it,
    labelled "40 kW lab Site, before the data-sheet kit".
  - 0K4f takes template v4 with its fingerprint pin and the lab moves (about 2.75 u, from 2.25). C-DD16 compares the
    world's Kobo with the slot file.
  - *Why:* the world is served from the onboarded Site; moving 37 lab and test references inside DD buys the demo
    nothing.

- **D-DD.31 Checker inputs and exact checks** (R5, R7).
  - D-DD.14 names `history.json` as a declared, committed input. The checker reads it with its own JSON read after
    asserting its sha256 equals the history golden.
  - C-DD7 is exact on scaled and meter-billed quantities.
  - C-DD8 reports Kobo's October balance beside the manifest's 120 L.
  - C-DD1 checks (person, role, Site) triples.
  - C-DD5 reads cadence from each readings manifest and asserts the checker's own cadence table equals it.

- **D-DD.32 Exports details** (I12).
  - The signature is `build_exports(view, history, *, months=None)`. `SOURCE_VERSION` "2" moves the pinned export
    digests, listed in the packet.
  - The month's delivered litres are `necessary_l + candidate_l + unexplained_l` of `history.json` (October:
    `period.actual.diesel_l`), cut into 400 L notes. The last note carries the remainder, stated in its document
    reference.
  - Notes fall on fixed days: the 1st, 8th, 15th, 22nd and 29th at 10:00 local, cycling. OOO-1's note keeps its 26 Oct
    delivery.

- **D-DD.33 Units restated** (all). Six parts, none over 6 units: DD1 4.0, DD2 5.5, DD3 6.0, DD4 5.75, DD5 5.0, DD6
  3.75, **30.0 u** (rev 1: 19.5 u in four parts). Plus 0K4f +0.5 u (D-DD.30). Spec §7.

- **D-DD.34 Owner queue, round 2.** Q7, Q8 and Q9 of spec §A, with defaults applied now (W3). The owner is asked to
  weigh in on all three: Q7 replaces an owner value, Q8 sets when the demo counts as done, and Q9 moves story figures.
