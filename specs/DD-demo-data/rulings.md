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

---

# DD rulings, round 3 (D-DD.35 to D-DD.40): DD1 mid-build questions

Architect (Claude), 2026-11-22. Answers Q-DD1.1 to Q-DD1.6 of `handoff-DD1.md` (branch `task/DD1-operators`, commit
`26fbb3927`). None needs the owner; each is logged here for owner review.

- **D-DD.35 The gateway provisioning guard compares the served tenant** (Q-DD1.3; the blocker).
  - `evidence/provision_gateway.py:71` compares `args.tenant` with `config.served_tenant_slug()`, not the constant
    `DEVELOPMENT_TENANT_SLUG`. A `ConfigurationError` from it exits 2 with its own sentence before any store is built.
    The refusal reads `Tenant {x!r} is not the tenant this environment serves (ASSETOPS_TENANT_SLUG; unset means "demo").`
  - *Safety intent kept.* The S2-02 guard stops a gateway credential or enablement being written for a tenant the
    deployment does not serve, through a typo or a wrong flag. After the change: with the variable unset the behaviour is
    byte-identical ("demo" only); with it set, the flag and the environment must still agree, so it is still a two-key
    check; and an ON1 operator database holds one tenant (`ONBOARD_DATABASE_NOT_EMPTY`), so the flag cannot reach another
    tenant's rows. `served_tenant_slug()` is the server's own answer to "which tenant" (D-ON1.5), so the CLI and the app
    can no longer disagree. The old guard also made every ON1 operator's gateway unprovisionable, a latent fault.
  - Tests (no database, `store=` injected): unset + `demo` runs; unset + `lakeside-power` exits 2; set `lakeside-power` +
    `lakeside-power` runs; set `lakeside-power` + `demo` exits 2; set to an invalid slug exits 2 and builds no store.
  - *Class (W6):* thirteen other operator CLIs compare the constant (`publish_source`, `chain/backfill`,
    `chain/snapshots`, `chain/period_backfill`, `recompute_consequences`, `publish_assumption`, `declare_objective`,
    `record_clock_attestation`, `evidence_migration`, `performance_migration`, `sites/convert_kobo_bindings`,
    `sites/demo_configuration`; `sites/import_kobo` passes it as `configured_tenant_slug`). None is on DD's command
    list (spec §0: `bulk_load`, `source_profile admit`, `provision_gateway`, `build_structure_snapshot`,
    `observe_structure`), so DD changes only `provision_gateway`. Rule: a later unit that runs one of them for a
    non-"demo" tenant makes the same change with the same five tests. The coordinator records the thirteen as one
    backlog task. This is a guard change, which D-DS4.3 kept out of DS4; it is DD's, narrow and recorded here.

- **D-DD.36 The apply step lives in `onboard_operator apply --bindings DIR`** (Q-DD1.4; amends D-DD.29's "subprocess").
  - Adopted as proposed: optional `--bindings DIR`; `tools/world.py` L1 passes `backend/conversions/world`. Without the
    option `apply` is unchanged, so existing tests stay as they are.
  - The two provisioning steps run **in process** through `provision_gateway.main([...])`, not as a subprocess: the same
    entry, argument checks, guard (D-DD.35) and `gateway_access_event`, without a product command forking the
    interpreter. It runs in the same process whose `served_tenant_slug()` onboarding already checked
    (`ONBOARD_TENANT_NOT_SERVED`).
  - Order per Site: `convert` (idempotent) then publish; then read `registrations()` and call `enable-gateway` /
    `enable-source --source` only for rows with `disabled_at` set. A non-zero exit from a step stops the apply with that
    exit code and the step's own stderr; a re-run completes it.
  - A Site with no `<CODE>-bindings.json` in DIR refuses `ONBOARD_SITE_INVALID` with where `bindings/<CODE>`, before
    any write. No new sentence.
  - Real files: `ONBOARD_REAL_AWAITS_APPROVAL` already refuses before this step; a test shows a real file with
    `--bindings` exits with that code and writes no binding set and no event.

- **D-DD.37 Cold compressor rating 6 kW, the cooling rating** (Q-DD1.5). Adopted. `compressor-1.rating` is 6 kW,
  equal to `cold-cooling-capacity`, as in cold-lab-001: both state the cooling duty, one quantity. The electrical draw
  (cooling × f_m / cop, about 3 kW at full duty) stays the pack's private result (§4.4) and is never written as a rating.
  No product read uses a compressor's rating.

- **D-DD.38 EV ids follow the manifest's asset codes** (Q-DD1.6). Adopted, with display names.
  - Ids as proposed, lower-cased manifest codes, as Lakeside's `gen-ks-01`: chargers `ch-e1..ch-e10`, `ch-k1..ch-k4`,
    `ch-r1..ch-r12`; connectors `<charger>-c1`, `<charger>-c2`; devices `<connector>-charger-controller`,
    `-connector-controller`, `-connector-meter` (ev-lab-001's set); `feed-1`, `site-meter-1`.
  - Display names carry the manifest's codes, so C-DD6 and every screen name the story's unit: charger `Charger CH-K2`,
    connector `CH-R7 connector 2`, devices as ev-lab-001's wording with that prefix.
  - Topology: `feed-1` → `site-meter-1` → each charger → its two connectors (POWER), plus ev-lab-001's SIGNAL edges per
    charger.

- **D-DD.39 EV schedules: every connector enabled all day; `24:00` accepted as a day's end** (Q-DD1.2; amends the
  proposal).
  - Confirmed: `/2` accepts `connector_enable_schedules` (spec §7 DD1.1 amended).
  - Amended: the proposed 00:00-23:59 leaves a disabled minute every night, inside the overnight charging window, and
    the product's windows would show it. That is a model fault, so it is fixed in the model (owner, 2026-11-21: one
    figure loyal to the operating world): `sites/ev_foundation._validate_schedules` accepts `local_end` `24:00` (end of
    the local day), `local_start` stays `00:00`-`23:59`. The reads already take it (`ev_site_reads._occurrences` allows
    hour 24; the window builder adds 24 h), and the screen prints the text. Tests: `00:00`-`24:00` accepted; `24:00`
    as `local_start` refused; `24:01` refused.
  - Every connector: seven entries, `00:00`-`24:00`, `time_zone` `Africa/Nairobi`, `utc_offset_minutes` 180. The load
    manager (§4.5), not the schedule, limits charging.

- **D-DD.40 C-DD13's TENANT-1 clause is pending until DD5.2** (Q-DD1.1). Confirmed. Until DD5.2 C-DD13 is judged on the
  cross-tenant reads and prints `TENANT-1: pending (DD5.2)` beside its result. DD5.2 makes the clause live, and from
  then C-DD13 passes only when both hold. A checker test asserts the pending line.

---

# DD rulings, round 4 (D-DD.41 to D-DD.44): DD1 questions Q-DD1.7 to Q-DD1.9

Architect (Claude), 2026-11-22. Answers Q-DD1.7 to Q-DD1.9 of `packet-DD1.md` (branch `task/DD1-operators`, commit
`68c799339`). Architect-level calls, logged for owner review; the owner may want to weigh in on D-DD.41 (it adds a
unit of work, D-DD.44).

- **D-DD.41 Multi-unit role binding: `minigrid-roles-5`, unit roles PER_ASSET, Site figures by one aggregation rule**
  (Q-DD1.7; the blocker; completes D-DD.21 on the evidence side).
  - *The fault (a class, W6).* `minigrid-roles-4` says "one generator, one PV inverter per Site": its GENERATOR and
    INVERTER roles are cardinality ONE, and `BindingService.publish` refuses a Foundation with two such components
    (`BINDING_ROLE_AMBIGUOUS`). v9 (D-DD.21) models several units, and the Protect beats need each unit's own
    evidence. Binding only unit 01, or a Site-total channel, would hide the failed unit or add a second figure for one
    quantity; both rejected. The fix is in the role model, not the data.
  - *Rule.* (Readiness coverage amended by D-DD.45.) A role is PER_ASSET in `minigrid-roles-5` exactly when its asset type is a unit type of v9 (GENERATOR,
    INVERTER): `generator_state`, `generator_power`, `mini_backup_start_event`, `pv_power`, `pv_available_power`.
    Every other role, label, unit, value kind, `required` flag, `states` and `event_kinds` is `minigrid-roles-4`'s,
    unchanged. Immutable, a new named version beside roles-4; roles-4 is untouched and still refuses (it stays
    interpretable for the sets published under it).
  - *Site figures from unit evidence (one rule, one module; built in DD3.4, D-DD.44).* Power roles: the Site value at a
    step is the sum of the bound units' values; a unit with no value at that step makes the Site value absent there,
    named by unit (no imputation). `generator_state`: RUNNING if any unit runs, else STARTING if any starts, else
    STOPPED if any unit is not FAILED, else FAILED. `mini_backup_start_event`: the union in time order, each event
    keeping its unit. Unit property reads: Site generator rating = the sum of non-FAILED units' `generator-rated-power`;
    burn per unit on its own curve, Site litres = the sum; Site policy from the lead unit (D-DD.43). One unit gives the
    unit's own value byte for byte, so a one-unit Site reads as today. Protect reads (C-DD6, the failure on its own unit)
    read the unit series, never the Site series.
  - *DD1 now (publish side only).* Kisiwa and Mto publish under roles-5; Kobo stays roles-4 until DD3.4 moves it with a
    parity proof, so the live Kobo figures are not touched before their readers accept roles-5. Until DD3.4 merges no
    reader selects a roles-5 set, so Kisiwa and Mto show no generator or PV figure rather than a wrong one; their
    readings are not loaded before DD5 in any case.
  - *Builder's change list (DD1.2):*
    1. `sites/binding_roles.py`: `ROLE_SET_MINIGRID_5 = "minigrid-roles-5"`; `MINIGRID_ROLES_5` = roles-4 with the five
       roles above as PER_ASSET (built by replacing those five entries, order kept); add it to `ROLES_BY_SET` and to
       `SERVED_ROLE_SETS_BY_SITE_TYPE["MINIGRID"]`. `ROLE_SET_BY_SITE_TYPE` unchanged.
    2. `sites/binding_service.py`: roles-5 beside roles-4 in `_V4_TABLE_BY_ROLE_SET` and `_MIXED_V4_ROLES_BY_ROLE_SET`
       (same entries), and at its third roles-4 reference. Class fix: the readiness branch (`role.cardinality ==
       "PER_ASSET" and role.asset_type == "LOAD"`, about `:814`) and the verification-missing branch (about `:908`)
       apply to every PER_ASSET role over the Site's components of `role.asset_type`, so an unbound unit of a required
       role is named as missing (LOAD output byte-identical).
       **Amended by D-DD.45:** the premise "every PER_ASSET role covers every component of its type" is wrong (cold's
       two probe roles share `TEMPERATURE_PROBE`). Both branches take a role exactly when its new explicit flag
       `every_component` is true (LOAD PER_ASSET roles and the five unit roles above); cold and EV keep main's output.
    3. `conversions/world/KISIWA-001-bindings.json`, `MTO-001-bindings.json`: `role_set` `minigrid-roles-5`, each
       unit's device signals bound with that unit's `asset_code`. KOBO-001 unchanged.
    4. Tests: roles-5 publishes Kisiwa (2 GENERATOR) and Mto (2 INVERTER); roles-4 on the same Foundation still refuses
       `BINDING_ROLE_AMBIGUOUS` (plant); two bindings of one unit role on one unit refuse `BINDING_ROLE_CONFLICT`;
       readiness lists `generator_power - <unit>` missing when one unit is unbound; LOAD readiness unchanged on an
       existing fixture; `test_dd1_onboarding_postgres` Lakeside apply with `--bindings` exits 0, one published set per
       Site, second apply unchanged (replaces the Q-DD1.7 refusal case).
  - Not in DD1: every reader (`analytics/assessment_worker`, `mini_depth/*`, migration 0029's lift, `dispatch_v3`,
    `fuel_balance`, `actions/verification*`, `finding_episode`, `financials/fuel_cost`, `chain/measure_impls`,
    `runs/replay_*`, `structure/energy/inputs`): DD3.4.

- **D-DD.42 Site document limits: 10,000 nodes, 96 devices, accepted with their basis** (Q-DD1.8).
  - Accepted. The limits guard parsing cost and refuse runaway documents; they are not product rules. The byte bound
    (256 KiB) stays and is the binding memory limit (10,000 nodes fit it at about 25 bytes a node). Basis: the largest
    real demo Site is Ruiru, 6,623 nodes and 73 devices; 10,000 and 96 leave about 1.5x and 1.3x. The template
    `MAX_DOCUMENT_NODES` moves with them so the device cap stays under the ceiling.
  - Builder: the three constants' comments name this ID and the basis; one test each that a document at the new
    limit parses and one over it refuses with the existing code. The user-facing refusal sentences, if they quote a
    number, quote the new one (statement baseline re-hashed, ratchet count unchanged).

- **D-DD.43 Lakeside template fill accepted; the Site's generator policy is held once, on the lead unit** (Q-DD1.9).
  - Accepted as applied: where the manifest is silent, template v3's values (PCS 30 kW, tank 400 L, load ratings
    25/10/40 kW, Kisiwa inverter 30 kW). Values taken from the manifest (Kisiwa SFC 0.31, Mto inverters 25 kW) are
    labelled `TEMPLATE` today; DD3.2's basis vocabulary relabels Lakeside's `/2` values (Declared, Assumed), as planned.
    C-DD8 (tank within [0, capacity]) is the check on the 400 L tanks; a breach stops for the Architect.
  - Amended: start and stop SOC, start delay and minimum runtime are the Site's one control policy (spec §4.3). Copied
    onto both Kisiwa units they are two stored figures for one quantity. They are held once, on the lead unit (first
    GENERATOR in declared order, `gen-ks-01`), as a lead set's controller holds a plant's set points. `gen-ks-02`
    carries only its unit properties (`generator-rated-power`, `specific-fuel-consumption`; DD3.3 adds no-load rate and
    minimum load). DD3.3's v9 reads the policy from the lead unit and refuses `TEL_FOUNDATION` when a non-lead unit
    carries one; DD3.4's readers do the same.
  - Builder (DD1.2): remove the four policy properties from `gen-ks-02` in `lakeside-power.onboarding.json`; a test
    that no non-lead GENERATOR in the three files carries a policy property. If an existing DD1 test or readiness check
    requires them on every GENERATOR, stop and report (do not restore them).

- **D-DD.44 DD restated: 33.0 u in seven parts** (amends D-DD.33).
  - DD1.2 grows 0.5 u (2.25; DD1 4.5 u): D-DD.41's publish side and D-DD.43's edit.
  - New **DD3.4 Unit roles in the readers (2.5 u)**: one module (`sites/unit_roles.py`: the D-DD.41 aggregation and
    the lead-unit policy read) that every listed reader calls for a roles-5 set; no reader sums units itself. A new
    migration lets the mini-depth lift accept one roles-4 or roles-5 set in force. Kobo's world conversion moves to
    roles-5, and a parity test shows Kobo's product outputs equal under roles-4 and roles-5 (as C-DD19 for v9). The
    Planner's code-reality check confirms the size; over 3 u stops for the Architect.
  - DD3 (8.5 u) splits at its seam: **DD3a** DD3.1 and DD3.2 (3.75 u; `task/DD3a-mini-reality`), then **DD3b** DD3.3
    and DD3.4 (4.75 u; `task/DD3b-mini-units`). DD3.4 must merge before DD5.1 loads Kisiwa's or Mto's readings.

---

# DD rulings, round 5 (D-DD.45 to D-DD.47): DD1 review round 1, H1 and L1 to L3

Architect (Claude), 2026-11-22. Answers `review-DD1.md` round 1 (branch `task/DD1-operators`, `6161bc186`): H1, L1,
L2, L3 and the Architect question. Architect-level calls, logged for owner review; no owner weigh-in needed (D-DD.45
restores main's behaviour for cold and EV and changes nothing a user sees for mini-grid beyond D-DD.41).

- **D-DD.45 Readiness coverage is an explicit role property, `every_component`; cardinality only keys the binding**
  (H1; amends D-DD.41 builder item 2).
  - *The fault (a class, W6).* D-DD.41 read one field for two facts. `cardinality` PER_ASSET says how a binding is
    keyed (one per asset, conflict key `(role, asset_id)`, `binding_service.py:472`). It does not say that the role
    must be bound on *every* component of its asset type. That second fact is true of LOAD feeders and of the v9 units,
    and false where one asset type carries several roles on different components (cold: `chamber_temperature` on
    `probe-1`, `ambient_temperature` on `ambient-1`, both `TEMPERATURE_PROBE`). Inferring coverage from cardinality made
    every correctly bound cold Site state a channel as missing; that is a false statement to the user, the reverse
    of "missing is stated honestly".
  - *Ruling.* Coverage is declared where the role is defined, not inferred. `Role` gains
    `every_component: bool = False`: "readiness and verification readiness read this role once per Site component of
    `asset_type`, and name each unbound one". It is true on exactly: `feeder_demand` and `feeder_requested_power` (every
    role set that holds them) and the five `minigrid-roles-5` unit roles of D-DD.41. False on every cold and EV role, so
    their readiness and verification output is main's, byte for byte.
  - *Why the flag, not the reviewer's default* (`asset_type == "LOAD"` or role set `minigrid-roles-5`). Same cost (one
    field, seven true values), but the default is an instance rule in the service: it names one type and one set, and
    the next multi-unit role set (a second cold room, a second charger bank) would edit `binding_service.py` again. The
    flag is the general mechanism: the role table states the fact, every reader asks the role, and a new set declares
    it. An invariant keeps it honest: `every_component` implies PER_ASSET.
  - *Not ruled now (backlog, owner may weigh in later).* Whether some cold and EV roles *should* cover every component
    (each compressor, each connector) is a product question; today `cold_foundation.py:333` answers it for cold by
    reading PER_ASSET as coverage and skipping `chamber_temperature` by name (an instance rule). The sweep that moves
    `cold_foundation.py` and the cold/EV role tables onto `every_component` changes user-visible readiness, so it waits
    for a demo-critical reason. Logged in `.agent/backlog-post-demo.md` by the coordinator.
  - *Builder's change list (DD1 fix round):*
    1. `sites/binding_roles.py`: add the field after `event_kinds` with a one-line comment citing D-DD.45; set
       `every_component=True` on `feeder_demand` (`MINIGRID_ROLES`) and `feeder_requested_power`; in `MINIGRID_ROLES_5`
       use `replace(r, cardinality=PER_ASSET, every_component=True)`. Add a module-level check (or test, item 4c) that no
       role in `ROLES_BY_SET` has `every_component` without PER_ASSET.
    2. `sites/binding_service.py:818` and `:914`: the branch condition becomes `role.every_component` (nothing else);
       rename the loop variable `loads` to `components`; the comment cites D-DD.45. The generic branch is untouched.
    3. Sweep: `grep -n 'cardinality\|asset_type == "LOAD"' backend/assetops_backend/sites/*.py`; no other site changes
       (publish keys stay on cardinality; `cold_foundation.py` is the backlog item above). Report the grep in the packet.
    4. Tests (`test_dd1_onboarding_postgres` or a new `test_dd1_readiness_parity_postgres`):
       a. *Cold and EV parity, byte for byte.* `readiness()` for cold-lab-001 (the W2-02 lab fixture), COLD-KIRI over
          its DD1 world conversion, and the W2-05a EV fixture Site, serialised as `json.dumps(x, sort_keys=True,
          indent=1)` after replacing every UUID string by `uuid-<n>` in first-appearance order, equals a golden file
          `backend/tests/fixtures/dd1_readiness_parity/<site>.json` captured by running the same helper on main
          `05be2b968` (capture command and main SHA written in the file's sibling `README`). The cold goldens show
          `READY_TO_REPORT` and no missing role.
       b. *Plant.* The same cold comparison with `chamber_temperature` monkeypatched `every_component=True` fails
          (proves the test catches H1).
       c. Every role with `every_component` is PER_ASSET; the true set per role set is exactly the seven names above.
       d. Kept: LOAD readiness unchanged on its existing fixture; Kisiwa with `gen-ks-02` unbound names
          `Generator power - Generator 02` and `Generator state - Generator 02`, and verification readiness lists
          `['gen-ks-02']`.
  - Packet: the false claim "cold tests pass unchanged" is replaced by 4a's result.

- **D-DD.46 L1 fixed now: the document-limit comments state D-DD.42's basis** (L1).
  - `sites/foundation_parsing.py:119-143`: replace the paragraph arguing 64 against 77 under 2,000 nodes, and the
    `MAX_SIGNAL_MAPPINGS` note, with D-DD.42's basis in at most three lines (10,000 nodes, 96 devices; Ruiru 6,623/73).
    No behaviour change; `TestEveryCapCanFire` still passes.

- **D-DD.47 L3 fixed now in the pre-write check; L2 to the backlog with D-DD.42's premise corrected** (L3, L2).
  - *L3 (a class: every input is read before the first write).* The `--bindings` pre-write check in
    `onboard_operator.main` reads and parses each `<CODE>-bindings.json` (`json.loads`; catch `OSError`, `ValueError`)
    and refuses `ONBOARD_SITE_INVALID bindings/<CODE>` with exit 2 and nothing written, the same refusal as a missing
    file. `_publish_and_enable` takes the parsed fixtures by Site code and no longer opens files. Test: a malformed
    `KISIWA-001-bindings.json` beside valid ones exits 2, the stderr line names `bindings/KISIWA-001`, and the tenant
    and Sites are not created.
  - *L2.* D-DD.42's premise is corrected: the byte bound binds operator files (256 KiB, `operator_file.py:32`) and Site
    import files (128 KiB, `import_files.py:24`); the Foundation revision POST (`foundation_api.py:492`) has no body
    bound, and the 10,000-node walker runs after FastAPI has parsed the body. Authenticated route, small risk, not
    demo-critical: backlog item "content-length bound on the Foundation revision POST, like `evidence_api.py:303`,
    256 KiB" (coordinator logs it in `.agent/backlog-post-demo.md`).
  - *Unit impact (D-DD.45 to D-DD.47).* One DD1 fix round, 0.5 u (flag and parity goldens 0.25, L1 and L3 0.25):
    DD1 4.5 to 5.0 u; DD 33.0 to 33.5 u. Sonnet fix-round builder; re-review by a fresh Claude reviewer on H1 and L3.
