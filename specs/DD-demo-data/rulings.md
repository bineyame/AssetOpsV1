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
    into an invoice file (CHARGE) and a receipt file (RECEIPT), because a profile writes one kind. *Superseded by D-DD.59: one invoicing file with a Type column.*
  - The cold rate card and the EV tariff schedules are TARIFF_SCHEDULE records in `canonical-json-v1`, written by
    `records.py` as today. A CSV cannot carry `bands`, and DS1b already writes them. The `cold-rate-card` profile is
    dropped. *Corrected by D-DD.61: DS1b writes none; `world/tariffs.py` writes them.*
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

---

# DD rulings, round 6 (D-DD.48 to D-DD.57): DD2 pre-flight (B1, B2, Q3 to Q9)

Architect (Claude), 2026-11-22. Answers `handoff-DD2.md` (branch `task/DD2-books`, `ffe33beeb`). Architect-level calls,
logged for owner review. The owner is informed of D-DD.48 (it answers the owner's "code solution to a data issue"
concern for this case) and D-DD.49's dropped penalty rows; no weigh-in is needed to proceed.

- **D-DD.48 Mini-grid books: billed kWh, revenue, collections and fuel are nodes of the world's structure, evaluated
  every month from that month's leaves** (B1; amends spec §5.1 and D-DD.32's litres sentence).
  - *What the fault is (a class, W6).* Spec §5.1 called billed kWh, revenue and the collections split "`history.json`'s
    leaves". They are not leaves of the world. The manifest declares them as **nodes** of `structures.MINI_GRID`
    (`M:813-822`): `metered_kwh = delivered_kwh - technical_loss_kwh - unexplained_loss_kwh`, `billed_kwh = metered_kwh
    - adjustments_kwh - unmapped_kwh`, `revenue = billed_kwh * tariff + productive_kwh * productive_tariff`, `collected
    = revenue - in_transit - outstanding`, `diesel_l = necessary_l + candidate_l + unexplained_l + extra_l`, `fuel_cost
    = diesel_l * diesel_price`. The history generator generates leaves only, by its declared design ("Totals and nodes
    are not generated here: the evaluator computes them", `history.py:5`). October's `period` records leaves and nodes
    together, and the nodes satisfy the structure exactly at all three Sites (billed 8645, 7400, 5400; revenue 3458,
    4070, 2160; collected 3180, 3800, 1890; litres 1180, 2400, 320; fuel cost 1475, 3120, 400). So the gap is in the
    spec's wording, not in the world model or the generator. Adding node values to `history.json` would put a second
    copy of each figure beside the evaluator's, against "one model-computed figure per quantity", and would move the
    pinned history golden for nothing.
  - *Ruling.* In every month, October included, and on both sides, the exporter takes the mini-grid book figures from
    the structure's own node expressions, evaluated on the month's leaves through the manifest's `factor_map`. This is
    the world's balance computing its declared node. It is not a design value and not a fit. It is labelled in code
    and in the packet as "node of `structures.MINI_GRID`, evaluated on the month's leaves (D-DD.48)". The rows carry
    the source word *Emulated*, like every book row.
  - *One mechanism every month.* For October the evaluated node must equal the node that `period` records, or the
    emulator stops with `EMU_NODE <tenant>/<code> <month> <node>` (the period's `diesel_cost` is node `fuel_cost`).
    Then October's bytes are unchanged by this ruling, and October proves the derivation against the world's own record.
  - *Plan side, the same rule.* The plan's `revenue` and `fuel_cost` budget lines come from the same evaluation on the
    plan record. `delivered_kwh` falls back to plan `billed_kwh` and `necessary_l` to plan `diesel_l` (factor_map), and
    every leaf with a `| 0` alternative reads 0. October's plan nodes check exactly (3420, 875; 4125, 2990; 2240, 375).
    D-3A3.13's unit prices then follow from the evaluated plan nodes.
  - *Builder's change list (DD2.1):*
    1. `world/exports.py`: a module table `NODES["MINI_GRID"]` with the six expressions above as Python callables, in
       dependency order, plus each expression's manifest text as a string. Use exact `Decimal`: money in whole cents
       and kWh and litres whole. Leaves are read through `records.PASS_THROUGH["MINI_GRID"]` (the record fields, in
       order). Add a `ZERO_LEAVES` frozenset, the leaves whose `factor_map` text ends in `| 0`: technical_loss_kwh,
       unexplained_loss_kwh, adjustments_kwh, unmapped_kwh, in_transit, outstanding, candidate_l, unexplained_l.
       `productive_kwh` and `extra_l` are the constant 0 (factor_map `"0"`). `delivered_kwh` and `necessary_l` are
       required. Prices are `prices.tariff_usd_per_kwh[site]`, `prices.diesel_usd_per_l[site]` and
       `prices.productive_tariff_usd_per_kwh`. Watch the units: `history.json` money leaves are integer cents
       (`meta.money_unit`), and `period` money is in dollars.
    2. `_charges`, `_receipt_records`, `_fuel_records` and the plan `revenue`/`fuel_cost` lines read the evaluated
       nodes, never `s.a["billed_kwh"]`-style fields. The existing `EMU_REVENUE`, `EMU_COLLECTIONS` and `EMU_FUEL`
       checks stay. They compare the emitted rows with the evaluated nodes.
    3. If a required leaf is absent, that node and every node depending on it write no row, and the field is listed
       `NOT_IN_HISTORY`. A coverage line marked ESTIMATED writes nothing, as now (GAP-1). An absent price stops the
       emulator with `EMU_PRICE`, as now. A negative node (for example collected < 0) stops it with
       `EMU_COLLECTIONS`.
    4. Test `simulator/tests/world/test_dd2_nodes.py`:
       a. *Parity.* The table's text for each node equals `M` `structures.MINI_GRID[node]`. The `factor_map.MINI_GRID`
          text of each leaf it reads equals the table's alternatives, and `ZERO_LEAVES` is exactly the set ending
          `| 0`. The test reads the manifest. The module does not.
       b. *October.* Evaluated equals recorded for every node `period` carries, on both sides, at all three Sites.
       c. *Plant.* Change Kobo's October `adjustments_kwh` in a copied view and `EMU_NODE` fires.
       d. *History.* For July at Kobo: billed 8163, revenue 3265.20 and collected 3002.73, from the pinned
          `history.json`.
  - *Checker.* See D-DD.55: the checker evaluates the same nodes with its own code from the manifest text.

- **D-DD.49 Cold and EV budget workbooks are source profiles. The expense ledgers use the existing layout unchanged.
  No PENALTY rows. No contract change** (B2; amends spec §3 and §5.2-§5.3; the builder's default is not taken).
  - *Why not extend the illustrative maps.* `budget-illustrative-1` is a built-in contract layout. If each new vertical
    added lines to it, `contracts/` would be edited per vertical, which is an instance rule on a protected seam. The
    product's general mechanism for a new operator's file is the source profile (3A6). That is how §3 already brings in
    every other cold and EV file (D-DD.24), and it reads budget workbooks today
    (`backend/tests/fixtures/3a6/lakeside-budget.profile.json` maps `body.factor_id`). A real cold-chain operator's
    budget workbook is its own format, not Lakeside's.
  - *Why no PENALTY row.* §5.3's "PENALTY (0)" is a typed-in zero. In the world, penalties are a **node**:
    `penalties = departures_missed * penalty_rate` (`M` `structures.EV_DEPOT_CAPTIVE`). The product computes it from
    the measured departures (DD4.4) and the rights register. A zero expense row would be a second figure for the same
    quantity, and it could disagree with the node (Kasarani in November). The penalty statement is already a "not
    written" record (§3). Without PENALTY, the cold and EV ledgers need only OM and STAFF, and `expenses-illustrative-1`
    already maps both. Its use is unchanged.
  - *Which plan figures become budget lines (one rule).* (a) DS1b's own-leaf BUDGET_LINE records of the month, under
    DS1b R1's rule: a fallback field is never a leaf's line (`NOT_OWN_LINE`), so EV `offpeak_kwh` and `kwh` are not
    lines. (b) A plan field whose name is a **node** of the Site's structure becomes a node line carrying its recorded
    value: cold `kwh`; EV `energy_cost` and `departures_required` (Ruiru). This is the same as mini-grid's
    `billed_kwh` and `diesel_l` node lines. (c) Every other field stays in `unwritten.json` with DS1b's reason: Ruiru
    `total` is `NOT_READ_BY_A_LEAF`, and EV `kwh` and `offpeak_kwh` are `NOT_OWN_LINE`. The plan's off-peak energy is
    therefore not received at Embakasi and Kasarani, as `missing-records.json` already says for October. It reads as
    the labelled assumption, never zero.
  - *Builder's change list (DD2.3 builds both budget profiles; DD2.4 uses the EV one):*
    1. `backend/conversions/profiles/cold-budget-illustrative.profile.json` and `ev-budget-illustrative.profile.json`,
       each with `<id>.sample.csv` and `<id>.expected.json`: `source_type` budget_workbook; constants `kind`
       BUDGET_LINE and `source_version` "1"; the columns of spec §5.2's new budget table. The Line map is the plan
       field name to the factor ID, identity on these names. Cold: crate_days, kwh, staff, maint, liability. EV:
       peak_kwh, max_kw, maintenance, energy_cost, departures_required.
    2. `exports_cold.py` and `exports_ev.py`: a node-line table `NODE_LINES = {"COLD_CHAIN": {"kwh": "whole"},
       "EV_DEPOT_CAPTIVE": {"energy_cost": "money", "departures_required": "whole"}}`. Money lines carry
       `body.currency`. A parity test asserts each name is a key of `M` `structures[key]`. A field written as a node
       line leaves `unwritten.json`, as mini-grid's `billed_kwh` does. Files: `harvest-cold.profile.cold-budget.csv`,
       `metro-bus.profile.ev-budget.csv`, `harvest-cold.expenses.csv`, `metro-bus.expenses.csv`.
    3. The expense ledgers carry DS1b's EXPENSE rows only: cold `maint` as OM and `staff` as STAFF, EV `maintenance` as
       OM. A test asserts that no cold or EV expense row has category ENERGY or PENALTY.
    4. `contracts/` is not touched by DD2.3 or DD2.4. DD2.2 stays the only contract change in DD2.

- **D-DD.50 Cold revenue and received are nodes too** (Q3; the builder's default, restated as D-DD.48's mechanism).
  `NODES["COLD_CHAIN"]`: `revenue = crate_days * rate + contract_crate_days * contract_rate`, and `received = revenue
  - outstanding`. `rate` is `prices.storage_usd_per_crate_day`, and `contract_*` is the constant 0 (factor_map). The
  same parity test and October `EMU_NODE` check apply: Mwea 868/820, Thika 1736/1650, Kirinyaga 1984/1900. Invoices
  sum to revenue. Receipts sum to received, all COLLECTED, because the cold structure has no in-transit leaf. The rest
  is outstanding.

- **D-DD.51 Values held in incident blocks come from a module table with a manifest parity test** (Q4; default taken).
  `ManifestView` stays as it is: `history.json`'s `view_digest` does not move. The table holds the tickets (CH-K2
  opened 2026-11-01T23:40+03:00 and CH-R7 opened 2026-10-06T00:00+03:00, both OPEN on `as_of`) and the named batches
  B-1029, B-1031 and B-1034 (crates and times). A test reads `M` and asserts every table value. The CH-K2 ACKNOWLEDGED
  event is the warranty claim's, not the ticket's. Contractor `oem-contractor` (R5). This is the established pattern
  (`factors.py`, `records.py` tables with parity tests), and D-DD.53 uses it too.

- **D-DD.52 Roster: one generator, July to October in DD2; DD4.3 extends it to 6 Nov** (Q5; default taken, with one
  condition). DD4.3 adds the November nights, including Kasarani's three spare-bus nights, by giving the same
  `exports_ev` roster function a wider month span. It never writes a second roster writer. The roster file then holds 1
  Jul to 6 Nov.

- **D-DD.53 Note days: a disorder test that dates a note sets that note's day** (Q6; amends D-DD.32's last sentence;
  the builder's default is not taken). The writer puts deliveries into the tank at the note's `occurred_at` (D-DD.19),
  so the date must be right in DD2. If DD5.2 moved it later, the books and the tank would disagree.
  - Rule: a month's dated notes (from the manifest's `disorder_tests`, through a module table with a parity test as in
    D-DD.51) are cut first, each at its date and 10:00 local. The rest of the month's litres are cut into 400 L notes on
    the fixed cycle (1st, 8th, 15th, 22nd, 29th), and the last of them carries the remainder.
  - Today there is one dated note, OOO-1: Kobo, 400 L, 2026-10-26. Kobo's October is then 400 L on 26 Oct, 400 L on
    1 Oct and 380 L on 8 Oct, 1180 in all (`EMU_FUEL` holds).
  - DD2 writes all three notes in October's expenses file. DD5.2 plants OOO-1 as §5.5 says, unchanged.

- **D-DD.54 Staging in DD2.1 is the three DS1b JSON kinds; profile admission and the statements reader are DD5 and WK**
  (Q7; default taken, plus one invariant). DS1b's records for cold and EV must also each land in exactly one place: an
  exported file, a staged JSON or `unwritten.json`. A test over all three tenants asserts this, as the mini-grid
  exporter already does for its own tenant.

- **D-DD.55 C-DD2 to C-DD4 by SQL, live and failing until DD5; C-DD4 also checks the node figures on history months**
  (Q8; default taken, amends spec §8.1).
  - The checks join `commercial_record_revision` to `site` for the Site code. They are tested with pure judges on
    fixture rows, as C-DD1 is.
  - C-DD4 gains one clause. For each history month, the decided node figures (mini-grid billed kWh, revenue,
    collected, litres and fuel cost; cold revenue and received) must equal the checker's **own** evaluation of `M`
    `structures` and `factor_map` on `history.json`'s leaves, to the cent. The checker reads the manifest text itself,
    with a minimal evaluator of its own (names, numbers, `+ - *`, `a | b`), and shares no code with D-DD.48's table.
  - Without this clause the derived billed kWh would be checked by nothing independent (W2), because C-DD3's
    identities hold by construction once billed is given. The checker's inputs gain `structures` and `factor_map`.

- **D-DD.56 A bool cell missing from its map is refused `NATIVE_VALUE`** (Q9; default taken). This is the same code
  as every other map miss (`layouts_v1.py:482`). An empty cell reads as absent, and the kind's presence rule decides.

- **D-DD.57 Units: DD2 grows by 0.75 u to 6.25 u and splits** (W4).
  - Changes: D-DD.48 +0.25 (DD2.1: node table, parity, October check, plan side, D-DD.53's dated note); D-DD.49
    +0.25 on DD2.3 (both budget profiles with samples and expected files; partly offset by no contract change and no
    PENALTY);
    D-DD.55 +0.25 (DD2.5: the checker's evaluator).
  - **DD2a** (`task/DD2-books`, as built so far): DD2.2 (done, 0.5), DD2.1 (1.5), DD2.5 (1.0), **3.0 u**.
  - **DD2b** (`task/DD2b-cold-ev-books`, branched from DD2a's head once DD2.2's review is ACCEPT, or from `main` after
    DD2a merges): DD2.3 (1.75, with D-DD.50) and DD2.4 (1.5), **3.25 u**.
  - DD goes from 33.5 to **34.25 u** in eight parts.

# DD rulings, round 7 (D-DD.58 to D-DD.66): DD2a review question, DD2b questions and deviations

Architect (Claude), 2026-11-22. Inputs: `review-DD2a.md` round 1 (M1, L1-L3 and the question on C-DD3's EV clause, on
`task/DD2-books` at e55a79ff9) and `packet-DD2b.md` (deviations 1-8, Q1-Q4 and the Kirinyaga full-room risk, on
`task/DD2b-cold-ev-books` at 948515f0c), and `review-DD2b.md` round 1 (ACCEPT; M1 = Q2, M2 = Q1, L1-L4, at 3b353031c).
Checked against code on `main`: `commercial/uploads.py` `_refuse_switch`
(D-3A6.5), `commercial/profiles.py` (`PROFILE_SOURCE_SYSTEM_TAKEN`), `load_emulated_exports.py` `_mixed`,
`canonical/sources_v1.py`, `canonical/records_v1.py` (CHARGE, RECEIPT, ADJUSTMENT, TARIFF_SCHEDULE, `bands`),
`native/layouts_v1.py` (an empty cell writes nothing), `structure/sources.py` (cold `rate` and EV prices
`NOT_CONNECTED`; mini-grid `tariff` PROVIDED by the existing route) and `world/records.py` (DS1b writes EXPENSE,
ADJUSTMENT and BUDGET_LINE only). No product contract changes. Owner informed; no weigh-in needed to proceed (one
WORKAROUND in D-DD.61 is reported for the owner's review).

- **D-DD.58 C-DD3 never crashes, and its EV clause judges the tariff identity on stored invoice lines** (DD2a M1, L1-L3,
  the Architect question; amends spec §8.1 C-DD3).
  - *Missing figures.* A Site-month missing a figure a C-DD3 or C-DD4 clause needs (any vertical: mini, cold
    `crate_days`, EV) is a FAIL detail line `<tenant>/<site> <month>: <figure> not recorded`, never an exception.
  - *EV clause.* For every stored EV CHARGE line: `amount = round_half_even(quantity x rate, 0.01)`, where the rate is
    the line's band price in `M` `tenants.metro-bus.sites.<site>.tariff.prices`, read by the checker itself: `PEAK` →
    `peak`; `OFFPEAK` → `offpeak`; `NIGHT` → `night_from_1_nov`; `FLAT` → `usd_per_kwh`; `DEMAND` →
    `demand_per_kw_month`. A Site-month's lines then sum to `peak_cost + offpeak_cost + demand_cost`, the `checks`
    identity. Each failing line is one detail line. While no EV CHARGE row is stored, the clause reports
    `pending: EV utility invoices are DD4.4's` and is not judged. It is never compared with a `history.json` leaf
    (history holds no EV `energy_cost`).
  - *Tests.* One test runs `judge_identities` and `judge_leaves_and_nodes` on the real inputs with `tenants=None` and
    asserts no exception; one plant drops a cold `crate_days` and asserts a FAIL line. L2: delete `BOOK_MONTHS`. L1:
    carried; the packet states that DD5's first C-DD2 run is `BOOK_QUERY`'s first proof. L3: not adopted (§8.1 lists
    two mini identities; C-DD4 covers fuel cost).
  - *Reach.* The checker only. Parity: the mini-grid and cold clause detail lines on the existing fixture rows
    (`test_dd2_checker_on_emulated_rows.py`, `tenants=LAKESIDE`) stay identical.
  - *Why.* The old clause compared lines with a leaf that does not exist and so hid every other judgement. Amount =
    quantity x tariff is the same identity C-DD3 judges for mini (billed x tariff) and cold (crate-days x 0.20).

- **D-DD.59 Cold invoicing is one export of one system: invoices, receipts and credit notes** (DD2b Q1; replaces §5.2's
  two invoice and receipt profiles).
  - *Ruling.* One profile, `cold-storage-invoicing-illustrative` (`source_type` `customer_invoicing`, `source_system`
    `cold-storage-invoicing`, `version` `row_digest`), file `<slug>.profile.cold-storage-invoicing.csv`, no constants.
    A `Type` column writes `kind`. Its columns are in spec §5.2. Thika's October credit note
    (`gen:COLD-THIKA:2026-10:actual:liability`, DS1b's ADJUSTMENT) is a `Credit note` row of this file, with DS1b's
    values, subject `SITE` and reason; it is no longer staged JSON. D-DD.54's accounting places it in "files".
  - *Why.* In the operating world a cold-room operator's invoicing system issues the invoices, takes the payments and
    issues the credit notes, and exports them as one transaction list. The source-type table already says so
    (`customer_invoicing`: "cold-room invoices, receipts and credit notes"). Two profiles were the spec's error: one
    source system per source type per Site (D-3A6.5) and one profile per system (`PROFILE_SOURCE_SYSTEM_TAKEN`) are
    right, because a record's identity is `(tenant, source_system, source_record_id)`. A generator system beside the
    file would have been a second identity space for the same ledger.
  - *Rejected.* Receipts as `mobile_money_statement`, review-DD2b M2's default. Cold receipts are M-Pesa, bank and
    cash payments recorded against invoices, and a mobile-money statement holds no bank or cash payment. The
    mini-grid precedent fits because Lakeside's collections really are a mobile-money settlement statement. That
    default would also leave the Thika credit note without a home. Several profiles per system
    (a 3A6 seam change reaching every Site type, for no operating-world reason).
  - *If refused.* If `compile_profile` or admission refuses `kind` from a mapped column, or a coded column's empty
    cell, the builder stops and asks; no constant workaround.
  - *Reach.* Cold only. Parity: Lakeside's and Metro Bus's exported files are byte-identical to their pre-change bytes
    (mini-grid PINNED test; an EV golden of the DD2b head).

- **D-DD.60 The source-system rule holds at export, and staged JSON loads in its own step** (the class behind Q1;
  amends D-DD.54 and §5.1).
  - *Guard.* `build_books` stops `EMU_SOURCE_SWITCH <tenant> <source_type> <site>` when (a) two exported files of a
    tenant share a source type, or (b) a staged batch names a Site that an exported file of the same source type
    names under another `source_system`. This mirrors D-3A6.5 and the loader's `_mixed`, so a clash fails at
    generation, not at DD5's load.
  - *Staging.* Staged canonical JSON goes to `<slug>/staged/`, not `<slug>/commercial/`. DD5.3 loads it as step
    `L1.staged:<slug>`, after the commercial step. Staged today: the cold rate cards and EV tariff schedules
    (D-DD.61); DS1b's ADJUSTMENT only where no invoicing file of its source type exists. A mini-grid ADJUSTMENT under
    `billing_export` would clash with `billing-illustrative-1` and stop the export. No Site has one today (every
    mini-grid `liability` leaf is zero). A future one is an Architect question, not a bypass.
  - *Tests.* A plant with a non-zero Lakeside `liability` stops `EMU_SOURCE_SWITCH`; the real manifest passes.
  - *Reach.* All three verticals' export assembly. Parity: Lakeside's `commercial/` bytes are unchanged.
  - *Class and sweep.* Class: a store invariant (one system per source type per Site) that the emulator did not
    honour. Sweep: every source type with two writers. `customer_invoicing` is fixed by D-DD.59, `utility_invoice` by
    D-DD.61 (same system), and `billing_export` by the guard. `expense_ledger` and `budget_workbook` each have one
    writer per tenant.

- **D-DD.61 Tariff schedules are written from `M` by `world/tariffs.py`; the meter register is DD5.2's** (DD2b Q2;
  corrects spec §3 and §5.1, whose premise that DS1b writes TARIFF_SCHEDULE and METER_ASSIGNMENT is false).
  - *Writer.* `simulator/assetops_simulator/world/tariffs.py` (DD2b), `tariff_schedules(view) -> {slug: batch}`,
    canonical JSON, staged (D-DD.60), `source_version` "1", record IDs `gen:<code>:tariff:<effective_from>`:
    - Cold, `<slug>.storage_rate_card.json`, `source_type` `storage_rate_card`, `source_system`
      `cold-storage-invoicing`. One record per Site: `contract_ref` `T-STORAGE`, from 2026-07-01, band `STORAGE`
      00:00-24:00 at `prices.storage_usd_per_crate_day` (0.20) `per_crate_day`. The invoicing rows' `Tariff` is
      `T-STORAGE`.
    - EV, `<slug>.utility_invoice.json`, `source_type` `utility_invoice`, `source_system` `ev-utility-invoice` (the
      utility issues both the schedule and the invoice, so the same system as the invoice profile). Embakasi: `C-114`
      from 2026-07-01 to 2026-10-31 (`OFFPEAK-AM` 00:00-18:00 at 0.12, `PEAK` 18:00-22:00 at 0.24, `OFFPEAK-PM`
      22:00-24:00 at 0.12, `demand_rate` 12.00), and `C-114` from 2026-11-01 (`NIGHT` 00:00-05:00 at 0.09,
      `OFFPEAK-AM` 05:00-18:00, `PEAK`, `OFFPEAK-PM`, `demand_rate` 12.00). Ruiru: `C-117` from 2026-07-01, the
      October Embakasi bands with demand 12.00. Kasarani: `FLAT-EV-KASARANI` (the Site code's form), band `FLAT`
      00:00-24:00 at 0.15, no `demand_rate`. All prices are read from `M` `tariff.prices`.
  - *Parity test (review-DD2b M1).* Every `Tariff` code on a cold invoicing row or an EV invoice row, samples
    included, equals the `contract_ref` of a schedule of that Site in force on the row's `effective_from`. Every
    schedule rate equals `M`'s price. The spec's wording "DS1b already writes" (§3, §5.2, §5.3, and D-DD.24's note) is
    corrected.
    - Mini-grid: none. Its `tariff` leaf is PROVIDED by the existing route; Lakeside is unchanged (parity).
  - *WORKAROUND (owner review).* A canonical band is one interval with a unique name, so the all-other-hours
    off-peak price is written as two bands, `OFFPEAK-AM` and `OFFPEAK-PM`. The invoice line reads `OFFPEAK` (D-DD.64
    (2)). The link between them is the name before the hyphen. No product code reads tariff bands today: cold `rate`
    and the EV prices are `NOT_CONNECTED`. The model fix, a band with several intervals in canonical TARIFF_SCHEDULE,
    is a contracts change. It goes to the backlog for the first unit that reads time-of-use prices; it is not built
    in DD.
  - *Invoice lines (amends §5.6).* One USAGE line per price class of the Site's schedule (`PEAK`, `OFFPEAK`, `NIGHT`
    from 1 Nov, or `FLAT`), plus one DEMAND line where the schedule has a `demand_rate`. Kasarani has a single `FLAT`
    line and no DEMAND line.
  - *Meter register.* Only MAP-1 needs METER_ASSIGNMENT. DD5.2 writes Mto's six re-pointing rows as
    `lakeside-power.meter_register.json` (`meter_register`, `source_system` `illustrative-meter-register`), staged.
    There is no baseline register; §5.5's row is amended.
  - *Why.* Every record kind §3 lists for a Site must exist for C-DD2. A tariff comes from the party that sets it,
    so the operator issues its rate card and the utility issues its time-of-use schedule.

- **D-DD.62 One NODES table, and DD2a merges before DD2b, which owns every conflict** (DD2b Q3).
  - *Table.* `simulator/assetops_simulator/world/nodes.py` holds `NODES` (keys `MINI_GRID`, `COLD_CHAIN`), one
    `emu_node(tenant, code, month, values, recorded)` and one parity test parametrised over the keys against `M`
    `structures`. `exports.py` and `exports_cold.py` import from it, and their own tables and tests are deleted. The
    checker keeps its own evaluator (D-DD.55, independence).
  - *Order.* DD2a goes first, because DD2b carries DD2.2's commits (review-DD2b, Q3). (1) DD2a's fix round (D-DD.58), re-review, merge. (2) DD2b's fix round merges `main` and resolves every
    conflict: `tools/world_history.py`, `test_3a3_exports.py`, `exports.py`, `tools/world.py` staging. It then makes
    D-DD.59 to D-DD.62 and D-DD.64's text changes, and goes to review.
  - *Why.* Two copies of the structure text would drift. The later branch holds both sides, so it resolves the
    conflicts.

- **D-DD.63 The cold ledger rule** (DD2b deviation 3; replaces §5.2's "Ledger generation", whose division by 7 fails,
  for example Thika's 8,432 crate-days).
  - *Crate-day.* A crate counts on each date from its admission date up to the day before it leaves (a stored night;
    the check-out day is not counted). A month's crate-days are those dated in it, so a batch admitted late in a month
    carries crate-days into the next, as a real room does. The invoice bills the crate-days dated in its month.
  - *Fill, per Site-month, in month order.* `need` = the month's `crate_days` leaf minus the crate-days that earlier
    batches carry into it. Standard batches (40 crates, 7 days, Assumed) are placed one at a time on the day whose stay
    sees the fewest crates in the room (ties: the earlier day), while their in-month crate-days still fit in `need`.
    The rest (under 40) is one remainder batch inside the month, with `rest // 7` crates for 7 days and one crate
    leaving after `rest % 7` days (a partial early collection).
  - *Opening stock.* June batches, filled at July's daily rate, that are still in on 1 Jul are written, IN rows dated
    in June included, so every stored OUT has its IN. **June rows are opening stock** (review-DD2b L2). June has no
    invoice, statement or leaf. Every check that reads the ledger's months (C-DD2 to C-DD4, DD5's loads) judges July
    to October and treats June movements as opening stock, never as a missing month.
  - *Clock.* In at 08:00, out at 16:00 local. OUT rows after `as_of` are not written (those crates are still in).
  - *Bounds.* `EMU_CAPACITY` stops on a room above capacity. Reaching capacity is allowed (D-DD.65).
  - *November (DD4.2).* DD4.2 extends the ledger to `as_of` for the rooms' readings. November's admissions repeat 1-6
    Oct's generated admissions (named batches excluded), shifted by 31 days, with new batch refs. They are Assumed,
    with no November invoice (the month is not closed).
  - *Reach.* Cold only.

- **D-DD.64 DD2b deviations 1, 2 and 4 to 8 ratified, with the spec amended** (DD2b Q4).
  1. A profile with a `status` column uses `version: row_digest` (receipts, now the invoicing file, and tickets). A
     constant version would hide a status change.
  2. The EV invoice's `Line` (`body.band`, free text) and `Line type` (`body.line_type`, map `{"Usage": "USAGE",
     "Demand": "DEMAND"}`) are two columns, because a map is one-to-one.
  4. B-1029 is in on 28 Sep at 08:00. B-1031 and B-1034 are in on 1 Oct at 08:00 and out on 8 Oct at 16:00
     (Assumed), customer `COLD-THIKA-K-01` (R5).
  5. `NODE_LINES` applies wherever the plan holds the field, so October Embakasi and Kasarani get `energy_cost` and
     `departures_required` lines. §5.3's "at Ruiru" described history.
  6. A roster row's service day is the night's start date. Embakasi returns are rounded to the whole minute,
     half-even.
  7. Receipts are paid at month end, 10:00. Methods rotate M-Pesa, M-Pesa, Bank. The tariff code is `T-STORAGE`.
     Sample-only rows (a cash receipt, an in-transit receipt, ACKNOWLEDGED and CLOSED tickets, and a credit note
     where needed) exist only to cover every map value (admission step 4b).
  8. The cold electricity-bill profile is DD4.4's, with its rows (§7 DD4.4 amended).

- **D-DD.65 Kirinyaga's room at exactly 400 crates is accepted** (DD2b risk). The fill minimises crowding, so the
  peak is what Kirinyaga's crate-days require. A full room on peak days is the operating world. DD4.1's acceptance
  gains one test: cold-thermal 2 runs at occupancy = capacity with no clipping. C-DD20's Kirinyaga direction is still
  judged, never tuned.

- **D-DD.65a review-DD2b's Lows** (carried, none blocking).
  - L1 goes to DD4.4's acceptance: `HAND_SAMPLES` is empty once `exports_measured` exists, and the utility-invoice and
    departure samples are slices of emulated rows.
  - L2 is D-DD.63's opening-stock sentence.
  - L3 is D-DD.65. Capacity is met by the data and guarded by `EMU_CAPACITY`. A history change that trips it is an
    Architect question.
  - L4 goes to DD2b's fix round: `test_dd2b_ev.py` uses `zone_currency(view)[0]`, not the host's zone.
  - The residual determinism risk goes to DD2b's fix round: pin the sha256 of each cold and EV exported file, as 3A3
    does for mini-grid. This also serves as D-DD.59's EV parity golden.

- **D-DD.66 Units: DD2b +0.75 u, DD5 +0.25 u; DD 35.25 u in eight parts** (W4).
  - DD2b, 3.25 to **4.0 u**: D-DD.59 (one invoicing profile with Type column and credit-note row, replacing two)
    +0.25; D-DD.60 and D-DD.61 (guard, staged directory, `tariffs.py`) +0.5. D-DD.62's merge is inside the fix round.
  - DD2a: no change (D-DD.58 is M1's fix round).
  - DD5, 5.0 to **5.25 u**: D-DD.61's meter-register file in DD5.2, and the `L1.staged` step in DD5.3 (+0.25).
  - DD2 is 7.0 u (DD2a 3.0, DD2b 4.0). DD goes from 34.25 to **35.25 u**, each part at or under 6 u.

# DD rulings, round 8 (D-DD.67 to D-DD.73): DD3a mid-build questions and deviations

Architect (Claude), 2026-11-22. Input: `DD3a-handoff.md` on `task/DD3a-mini-reality` at e32b5d57f ("Risks and
Architect questions" and "Defaults taken"). Checked against code on that branch: `financials/fuel_cost_v2.py:35,158`
(`NO_LOAD_BASES`, the `NO_LOAD_RATE_BASIS_MISSING` refusal; the set is not in `PARAMETER_VERSION`),
`fuel_balance/service.py:25` (follows `STATE_PROPERTY_VALUES`), `structure/litres/inputs.py:22,107` (imports fuel
balance's set), `chain/vocabulary.py:117`, `site_outcomes/mini.py:74,446`, `actions/verification.py:1298`,
`financials/trial_fuel_comparison.py:69`, `packs/mini_grid.py:93-113` (`GENERATOR_LIFECYCLE`
`initial_values_supported` = {STOPPED, FAILED}), `sites/models.py:97,432-449` (`COMPONENT_PROPERTY_SOURCES` =
{TEMPLATE, SITE}; `source_version` = the declaring document's version) and `KOBO-001-bindings.json` (rows keyed by
`device_id`, `signal_id`). Owner rule applied: "one model-computed figure per quantity, loyal to the operating world;
fix model faults in the model". Owner informed; no weigh-in needed (no WORKAROUND).

- **D-DD.67 The no-load basis has one vocabulary; fuel-cost-2 and the client words read DATASHEET_FIT** (handoff risks
  (a) and (b); amends spec §6 "Labels"; the class behind both).
  - *Fault.* D-DD.17 added `DATASHEET_FIT` to `generator-no-load-fuel-rate-basis`, but two readers keep their own copy
    of the value set. fuel-cost-2 would refuse Kobo's 0.62 L/h `NO_LOAD_RATE_BASIS_MISSING`, so the fuel cost would
    read "not available" while the fuel balance and the litres structure (which follow `STATE_PROPERTY_VALUES`) show
    0.62, and the world's v8 burn uses 0.62. One quantity would have two answers. The fault is in the model, and it is
    fixed there.
  - *fuel-cost-2.* `NO_LOAD_BASES = ("GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST", "DATASHEET_FIT")`. It stays
    a literal: the financials models import nothing outside `financials/` and stay pure. `PARAMETER_VERSION` is not
    touched, so `PARAMETER_SHA256`, `FORMULA_VERSION` and `REVIEWED_PARAMETER_SHA256` are unchanged and no new
    parameter version is cut. The basis set is not in the reviewed parameter record. The formula and the inequality
    hold for "the declared no-load fuel rate with its declared basis", whatever the basis is. The `limitation` text
    (GENERIC_DEFAULT is a generic figure) stays true. A fitted rate is this generator's own figure, labelled Assumed
    by D-DD.17.
  - *Client words.* `NO_LOAD_BASIS_WORDS["DATASHEET_FIT"] = "the datasheet-fitted idle fuel rate"`. It renders "counted
    at the datasheet-fitted idle fuel rate of 0.62 L/h, not measured" (`COST_IDLE`) and "modelled from the
    datasheet-fitted idle fuel rate, not measured by a fuel meter" (`FUEL_VALUE_PAGE`). Guard V holds (no "no-load",
    no "load"). The words match D-DD.17's Foundation label ("Assumed: fitted to the data sheet's stated points").
  - *Sweep (every reader of the basis).* fuel-cost-2 and `NO_LOAD_BASIS_WORDS` change. These need no change:
    `fuel_balance/service.py` and `structure/litres/inputs.py` (they already follow the vocabulary); the Action and
    consequence stores and `chain/outcomes.py` (they pass the basis through); `site_outcomes/mini.py` and
    `actions/verification.py` (they read the words). In `trial_fuel_comparison.py:69`, the comment "one of the three
    states" becomes "one of the basis states". No frontend reads the basis.
  - *So it cannot recur.* One test asserts `set(fuel_cost_v2.NO_LOAD_BASES) ==
    STATE_PROPERTY_VALUES["generator-no-load-fuel-rate-basis"]` and `set(NO_LOAD_BASIS_WORDS) - {None}` equal to the
    same set. A basis value added later without both readers then fails a test.
  - *Acceptance (questions).* Does `fuel_cost_v2.quantify`, given a Foundation revision declaring 0.62 L/h
    `DATASHEET_FIT` with an idle reading, return AVAILABLE with rate 0.62 and basis `DATASHEET_FIT`? Does the idle
    cost row read the DATASHEET_FIT words? Does an unknown basis string still refuse `NO_LOAD_RATE_BASIS_MISSING`?
  - *Reach.* Mini-grid Sites only: Sites whose generator declares a no-load rate (Lakeside/Kobo, Kisiwa, Mto, and the
    test fixtures), on every mini-grid role set. Cold-chain and EV Sites declare no generator no-load rate, so
    fuel-cost-2 is never selected for them and the words never render. The change only admits one more value: no
    existing basis changes outcome. Parity: D-DD.68.

- **D-DD.68 Parity test for D-DD.67, golden from main** (standing rule, 22 Nov audit). File
  `backend/tests/test_dd3_no_load_basis_parity.py`. The goldens are generated on `main` 80661e824 before the change
  and committed beside the test. Each must match:
  - canonical JSON of `fuel_cost_v2.quantify` on the existing `test_fuel_cost_v2.py` fixtures, one each for
    GENERIC_DEFAULT, MANUFACTURER_DATASHEET and SITE_TEST, one for a missing basis (`NO_LOAD_RATE_BASIS_MISSING`) and
    one with no rate declared;
  - `PARAMETER_SHA256` and `FORMULA_VERSION`;
  - the three existing `NO_LOAD_BASIS_WORDS` entries and the `None` entry;
  - `COST_IDLE` as rendered for GENERIC_DEFAULT.
  The no-rate case (fuel-cost-1's result returned byte-equal) stands for cold-chain and EV, which declare no rate.
  Kisiwa and Mto (GENERIC_DEFAULT) are the GENERIC_DEFAULT case.

- **D-DD.69 The writer runs one continuous execution per Site, advanced one local day at a time** (deviation 1;
  amends spec §4.1 "Per Site-day").
  - Per Site there is one pack execution over the span. It starts at the span's first local midnight from the
    declared initial state: generator STOPPED, the tank at 50 % (D-DD.19), the rest as §4.2. It advances one local
    day at a time. Kobo, Kisiwa and Mto are on Africa/Nairobi, which has no DST, so a day is 288 five-minute steps.
    Each day's readings file is written from that day's steps. Day d+1 starts from day d's end state by
    construction. That includes a RUNNING or STARTING generator, which v8 cannot declare at a run start.
  - The rule holds for every pack the writer drives (DD4.2 and DD4.3 included), so there is one chaining mechanism.
    A refusal on any day is `TEL_PACK` naming the day.
  - *Test.* For Kobo, the readings from advancing 288 steps twice are byte-equal to the readings from advancing 576
    steps once.
  - *Why.* This is the same thing as chaining day to day, without a generator forced to STOPPED at every midnight.
    That forced stop would add starts and cut runs that the operating world does not have.

- **D-DD.70 Kisiwa's and Mto's pure run under D-DD.19 moves to DD3b** (deviation 2; amends D-DD.19 "Known before the
  build", spec §6 "Order inside DD3.2" and §7 DD3.2, DD3.3).
  - In DD3a, DD3.2 commit 1b runs the writer purely on Kobo, July to October, at 0.62 and at 3.3 L/h. It prints D-DD.19's
    table per month. Any bound hit, or a Kobo C-DD8 or C-DD17 failure, goes to the Architect before DD3a merges.
  - In DD3b, DD3.3 runs Kisiwa and Mto purely on v9, July to October, and prints the same table. A failure goes to the
    Architect before DD3b merges, which is still before DD4 and before DD5 loads their readings. D-DD.19's fallback
    applies per Site, unchanged.
  - *Why.* Kisiwa and Mto have two generators or two inverters, and v8 holds one of each (§0). A v8 run of them would
    print figures from a Site that does not exist.

- **D-DD.71 The data-sheet tool writes `source` "SITE", `source_version` 1** (deviation 3; amends spec §6 "The
  mapping"). Every property the tool writes carries these, and so does its `-basis` sibling.
  - *Why.* The closed set is {TEMPLATE, SITE}, and D-DD.17 allows no new value. The values are the Site's own equipment
    records, not a template copy (`sites/models.py:432`). Version 1 is the Site's first declaration of them. A later
    re-read of a sheet that changes a value writes the next integer.

- **D-DD.72 A reading's `source_id` is its binding row's `device_id`** (deviation 4; amends spec §4.1 "Output" and
  "Public records to readings").
  - In `assetops.world-readings/1`, `source_id` is the `device_id` and `signal_id` the `signal_id` of the Site's binding
    row for the record's role. The manifest's `mappings` lists (pack record, role, `source_id`, `signal_id`).
  - A public record with no binding row, or with two, refuses `TEL_BINDING <site> <role>`. This is a new refusal code
    in §4.1's list.
  - *Test.* Every pair written for Kobo resolves to exactly one row of `KOBO-001-bindings.json`.
  - *Why.* The binding conversion keys its rows by `device_id`, and §4.6 resolves each `source_id` through the
    foundation store's devices. A second identifier would be a second name for one device.

- **D-DD.73 Units: DD3a +0.25 u, DD3b +0.25 u; DD 35.75 u in eight parts** (W4).
  - DD3a, 3.75 to **4.0 u** (DD3.2 2.0 to 2.25): D-DD.67 and D-DD.68. D-DD.69, D-DD.71 and D-DD.72 are inside DD3.1
    and DD3.2 as built.
  - DD3b, 4.75 to **5.0 u** (DD3.3 2.25 to 2.5): D-DD.70's pure-run table and gate.
  - DD3 is 9.0 u. DD goes from 35.25 to **35.75 u**, and each part stays at or under 6 u.

- **D-DD.74 DD2b merges on its own once its consumers select their tenant: `exports --tenant`** (W6; amends spec §7
  DD2.3 and DD2.4, and DDR spec S3). Rules option (c) of review-DD2b V1, as a fix, not a workaround; (a) and (b) are
  refused.
  - *The class.* DD2b widened `tools/world_history.py exports` from Lakeside's mini-grid files to every manifest
    tenant's books in one flat directory. Every consumer reads one tenant's (or the definition's tenants') files and
    refuses a stranger: `load_emulated_exports --tenant` (`EXPORT_FILE_UNKNOWN`) and `tools/world.py` L1.exports
    (`WORLD_INPUT_UNPLACED`). The 12 red main tests (9 `test_ddr_rehearsal_postgres.py`, 3 `test_ds4_world_postgres.py`
    t12-t14) are two instances of it; the DDR spec's S3 and two runbooks carry the same command and would fail the same
    way in use. The producer's widened contract is DD2b's, so the consumer sweep is DD2b's too.
  - *Why not (a).* DD5 would not cure it: the definition `/2` places all three tenants (t12-t14 go green), but the DDR
    rehearsal and both runbooks load one tenant's directory and would stay red. Holding DD2b also holds DD3a, DD3b and
    DD4, which build on its files. *Why not (b).* Marking accepted tests expected-failing leaves main red in substance
    and is a workaround with no owning unit. *Why not loosen a consumer.* Skipping unknown files in either loader
    weakens a guard that catches real misplacement; both refusals keep their full meaning.
  - *Change list (DD2b fix round 8, 0.5 u):*
    1. `tools/world_history.py exports` gains `--tenant SLUG`, repeatable, optional. With it, the export directory and
       `--extras` hold only files whose name starts with `<slug>.` for a named slug; `unwritten.json` is written whole
       (it lists what the world did not write; every loader skips it by name). A slug that is not a manifest
       `tenant` prints `EMU_TENANT_UNKNOWN <slug>` and exits 3. Without `--tenant`, all tenants, as now. The filter runs
       on `build_books`' result; `build_books` is unchanged.
    2. `tools/world.py` `inputs()`: the L1.exports argv adds `--tenant <slug>` for each definition tenant. The
       `WORLD_INPUT_UNPLACED` refusal and the extras loop stay as they are (they now see only named tenants' files).
       Any `test_ds4_world.py` argv assertion follows.
    3. `backend/tests/test_ddr_rehearsal_postgres.py` S3 adds `--tenant lakeside-power`; the same in DDR spec S3
       (`specs/DDR-rehearsal/spec.md` row S3), `specs/ON1-operator-tenant/runbook.md` and
       `Docs/engineering/operator-deep-dive-runbook.md` at their `exports --manifest` lines.
    4. Tests (`simulator/tests/world/test_dd2b_round7.py` or a new `test_dd2b_tenant_filter.py`): `--tenant
       lakeside-power` writes no `harvest-cold.` or `metro-bus.` file and the same Lakeside bytes as the unfiltered run;
       two `--tenant` flags write both tenants' files; an unknown slug exits 3 with `EMU_TENANT_UNKNOWN`.
  - *Gate.* Before merge, the verifier's nine backend files run green on the branch (the 12 included), and
    `simulator/tests` stays green.
  - *DD5.* Nothing moves out of DD5 and its 5.25 u stand: DD5.3's L1 places cold and EV by naming their tenants in the
    `/2` definition, and item 2 carries them through unchanged.
  - *Units.* DD2b 4.0 to **4.5 u** (DD2.3 2.25 to 2.5, DD2.4 1.5 to 1.75); DD2 7.5 u; DD goes from 35.75 to
    **36.25 u**, each part at or under 6 u.

---

# DD rulings, round 9 (D-DD.75 to D-DD.79): DD3a blockers (kernel speed, Kobo's tank) and the Update 4 deviations

Architect (Claude), 2026-11-22. Input: `DD3a-handoff.md` Update 4 and its addendum on `task/DD3a-mini-reality` at
0bc54a00f. Checked against code on that branch: `kernel/execute.py:1263-1340` (`_compute_exposures`: every forcing,
every step), `:228` (`_entry_span`), `:282` (`_excluded` reads the frozen inputs only), `:1641`, `:1813-1826`
(`Execution`, `_advance_one`, `begins_a_step`, `step_length`), `:1994` (`ColdExecution` takes its own runner and never
reaches `_compute_exposures`), `host/execution_adapter.py:130` (`EXECUTABLE_MODELS`, ten `ModelSpec`s, all mini-grid
or fuel), `contracts/.../execution_contract.py:1596` (`overlap_minutes`), `contracts/.../trajectory.py:456`
(`content_digest`), `world/telemetry.py:60,175-181,287-297,310`, the Lakeside `/2` and `/1` files (all three tanks
`tank-capacity` 400 L, source TEMPLATE), the manifest's `history` block (`seasons`, `families.solar_surplus`) and
`history.json` fuel leaves. The kernel directory on the branch equals main's. The owner is informed of all five; the
owner is asked to weigh in on D-DD.76 (it declares three Site tanks).

- **D-DD.75 The kernel indexes forcings by step: option (a); (b) and (c) are refused** (addendum; protected seam,
  no contract change).
  - *The fault (a class, W6).* `_compute_exposures` walks `inputs.forcings` whole at every step, so one execution
    costs O(steps × forcings). Every long execution on the `Execution` path has it, not only the writer's; the writer
    is the first caller with a 123-day span. The fix is in the kernel, once.
  - *Change (`kernel/execute.py` only).*
    1. `_World` gains `forcings_by_step: dict[int, tuple[int, ...]] | None = None`.
    2. New pure function `_forcing_index(inputs) -> dict[int, tuple[int, ...]]`: for each position `p` of
       `inputs.forcings`, in order, `(start, end) = _entry_span(forcing, duration)`; skip when `end <= start`; for each
       step start `s` of `inputs.interval.step_starts` (found from `bisect_right(step_starts, start) - 1`, floor 0,
       while `s < end`) with `length = min(s + timestep, duration) - s`, append `p` to `s`'s list when
       `overlap_minutes(s, length, start, end - start) > 0`. Values are tuples, ascending by construction.
    3. In `_compute_exposures`, after the `begins_a_step` return: if `world.forcings_by_step is None`, build it. The loop
       at `:1280` becomes `for position in world.forcings_by_step.get(world.offset, ()):` with
       `forcing = world.inputs.forcings[position]` as its first line. Every line after it is unchanged, including the
       `_excluded`, handler and `overlap_minutes` checks.
    4. Nothing else changes: no other scan, no setup check, no contract, no pack.
  - *Why it is byte-identical.* The index holds exactly the forcings whose overlap with the step is positive, by the
    same predicate with the same arguments; the old loop skipped every other forcing with `continue` after pure reads
    (frozen inputs, the model's handler table), with no side effect. The kept forcings are visited in input order, so
    `exposed_by_address`, its stable sort, the ledger records and the exposures are the same. The lazy build covers
    every way a `_World` is made.
  - *Reach.* One Site type: mini-grid, through the ten `EXECUTABLE_MODELS` (minimal fuel tank, daytime mini-grid,
    mini-grid v1 to v8) and the DD3 writer. Cold chain (`ColdExecution`, its own runner) and EV charging (its own
    path, `execution_path_for` = EV) do not call `_compute_exposures` and are unchanged; the builder confirms by grep
    and adds them to the parity test if either does.
  - *Parity test (golden from main's kernel), `host/tests/test_kernel_forcing_index_parity.py` plus
    `host/tests/fixtures/kernel_forcing_index_parity.json` (case id → `PrivateTrajectory.content_digest`).* The golden
    is written and committed on the DD3a branch BEFORE the kernel edit (the kernel directory equals main's; the packet
    shows `git diff main -- simulator/assetops_simulator/kernel` empty at that commit), and the test passes there.
    Cases: K1 to K8, `host/tests/kobo_season.py base_run(2, version=N)` for N = 1 to 8 through
    `execution_adapter.frozen_world_inputs` and `model_for`; D1, the first run `host/tests/test_daytime_mini_grid.py`
    builds; F1, the first run `simulator/tests/test_fuel_trajectory.py` builds; X1, the `FORCING_VALUE_AMBIGUOUS` case of
    `simulator/tests/test_execution_failures.py` (failure and offset are in the digest); W1, the writer's Kobo 7 days
    from 2026-07-01 with the tank set to 2500 L inside the test; S1, K8 advanced one boundary at a time, equal to K8's
    digest.
  - *Timing (packet).* Wall time of the 7-day Kobo writer run before and after (11 s before), and of the 123-day pure
    run at 0.62 and 3.3. Stop rule: if the 123-day run takes over 10 minutes, the builder hands the top 15 lines of
    `cProfile` to the Architect and makes no further kernel change.
  - *Why not (b).* A window hand-off must start a RUNNING or STARTING generator, which v8 refuses
    (`mini_grid.py:93-113`); making it start would change a pack's admitted initial states, a larger seam than an
    index, and it would add a second chaining mechanism beside D-DD.69's. *Why not (c).* Season v2's load is already
    2-hour blocks; wider windows would flatten the world's inputs to suit the tool, and at 2-hour windows the cost is
    still O(steps × forcings) (about 35k × 5.9k).

- **D-DD.76 The three mini-grid tanks are declared by the Site, sized by a stated storage rule; the notes stay as
  dated** (tank blocker; amends spec §4.2 "Fuel" and §6's "tank" row, and D-DD.19's fallback). The owner is asked to
  weigh in.
  - *What the world is.* The 400 L is not Kobo's tank: all three Sites carry `tank-capacity` 400 L with source TEMPLATE,
    copied from the Kobo 60 kW Lab template, which was made for runs of hours. No operator takes 400 L notes into a
    400 L tank (it would accept one only when empty), and Kisiwa's 2,400 L a month would be six of them. The notes are
    the operator's records: their litres are the books' (D-DD.32, D-DD.48) and their days are set (D-DD.53, OOO-1);
    changing them would move story figures to fit a placeholder. Sizing deliveries to free space would make the books
    follow a placeholder, and D-DD.19's fallback cannot work at 400 L either (two notes, 800 L, into a tank below
    100 L). So the wrong figure is the tank.
  - *Rule (declared, computed from the books, never from a run).* Each mini-grid Site holds on-site storage for two
    months of its largest month of delivered litres July to October (D-DD.32 litres: `necessary_l + candidate_l +
    unexplained_l` of `history.json`, October `period.actual.diesel_l`), rounded up to the next standard size of 500,
    1000, 1500, 2000, 2500, 3000, 4000, 5000 or 10000 L. Two months: a remote Site keeps a month's reserve above a
    month's deliveries (road and rains). The rule is fixed here, before any run at the new size.
  - *Figures.* Kobo max 1180 (Oct) → 2360 → **2500 L**; Kisiwa max 2400 (Oct) → 4800 → **5000 L**; Mto max 320
    (Oct) → 640 → **1000 L**. The start stays 50 % (D-DD.19): 1250, 2500 and 500 L. If the builder finds other leaf
    values, the rule stands and the figures follow; the packet prints the inputs.
  - *Where.* `tank-capacity` of each Site's `fuel-tank` in `backend/tests/fixtures/on1/lakeside-power.onboarding.json`
    and `lakeside-power.v1.onboarding.json` (one figure in both files), `source` "SITE", `source_version` 1
    (D-DD.71's rule: the Site's own first declaration). Lab templates and scenarios keep 400 L (they are the template's
    figure). The writer reads the tank only from the foundation, as now.
  - *Gate unchanged.* The D-DD.19 / D-DD.70 pure run then runs. A bound hit is still reported, never tuned.
  - *D-DD.19's fallback, restated.* When a Site's dip falls below 25 % of capacity, the next notes are placed then:
    as many 400 L notes as fit in the free space, at most two. The books follow the tank and the owner is told the moved
    figures before DD4.
  - *Moved figures.* Any product figure computed from the tank (level as a share of capacity, days of cover) moves at
    Lakeside's three Sites; the packet lists them. No story figure moves.

- **D-DD.77 Kobo's July and August sun follow the world's declared season, not "all clear"** (Update 4 deviation:
  changed; amends spec §4.2 "Sun").
  - Season v2's calendar covers 1 September to 31 October only. For a Kobo day outside it, the irradiance is season
    v2's clear-day shape (`SUN_W_PER_M2["clear"]`) times the `solar_surplus` day weight (season × day class, no
    jitter): July and August are `cool_dry`, 0.80. This is the rule Kisiwa and Mto use (§4.2), so there is one rule
    for a day without a calendar. Hourly values are exact (`Fraction`) and the manifest's `conditions` record the rule.
  - *Why.* "All clear" in July and August is a fill the world does not declare: the manifest declares less sun in
    `cool_dry` (0.80) than in `warm_dry` (1.10).

- **D-DD.78 The other Update 4 deviations are ratified.**
  1. Load and sun are hour-block WINDOW forcings (96 a day at Kobo). Season v2's shape is 2-hour blocks, so hourly
     windows carry it whole; 5-minute windows would repeat values and add nothing. Kept after D-DD.75.
  2. Watt-hours by largest remainder per (day, feeder, hour) over the month, month totals exact (§4.1).
  3. The load shape is season v2's (`LOAD_SHAPE_KW`) and the day weight the `demand` family's.
  4. Critical-load order clinic, residential, mill (season v2's `critical-load-priority`).
  5. Notes outside the span are skipped; Kobo only in DD3a, Kisiwa and Mto `not_written` (D-DD.70).
  6. Readings to the thousandth, half-even, one JSON line per row.
  7. Fuel-limited burn when the tank is low (unserved appears); an empty tank from a declared draw is
     `INTEGRATION_BOUND_FAILURE`, an overfill `BOUNDED_AND_RECORDED`; both are `TEL_PACK` naming the day (D-DD.69) in
     the writer, and tabled in the pure run.
  8. C-DD21 (writer `NEEDS` table against the backend's frozen Kobo v8 initial values) is a new check in
     `tools/dd_check.py`; spec §8.1 lists it.

- **D-DD.79 Units: DD3a +0.75 u; DD 37.0 u** (W4). DD3.1 1.75 to **2.25** (D-DD.75 index, parity test and timing;
  D-DD.77); DD3.2 2.25 to **2.5** (D-DD.76: the tank rows in both files, the test sweep, the moved-figure list). DD3a
  4.0 to **4.75 u**, DD3 9.75 u; DD goes from 36.25 to **37.0 u**, each part at or under 6 u.
  - *Order inside DD3a.* (1) the parity golden on the unchanged kernel, committed; (2) the index, parity green, timing;
    (3) D-DD.77; (4) D-DD.76's tank rows, then commit 1b's pure run on the new tank; (5) commit 2 as §6 says.

# DD rulings, round 10 (D-DD.80): DD3a blocker (kernel speed, second round: the cause path)

Architect (Claude), 2026-11-22. Input: `DD3a-handoff.md` Update 5 on `task/DD3a-mini-reality` at c35c50e92 (timings
7 / 14 / 28 days 5.5 / 15.3 / 74.8 s, 123 days over 10 min; cProfile of 28 days, 99.7 s, `point_due_at` 53.2 s over
249,984 calls). Checked against code on that branch: `kernel/execute.py:250-271` (`_forcing_index`, D-DD.75), `:1079-1125`
(`_phase_apply_events`: every cause at every step, `point_due_at` per POINT cause), `:1383-1410` (`_phase_evolve`: every
cause at every step for the non-POINT shapes), `:1700-1706`, `:1845-1869` (`Execution`, `_advance_one`, `step_length`),
`:1618` (`_PHASES`, reached only through `Execution`), `contracts/.../execution_contract.py:1671` (`point_due_at`, a scan of
every step start), `contracts/.../world_inputs.py:77` (`FrozenInterval.step_starts`, a property that builds a tuple of every
step start at each read) and `:343` (`excludes`), every `for ... in world.inputs.<collection>` in `execute.py` (lines 260,
276, 361, 472, 544, 687, 715, 753, 757, 820, 887, 916 are setup, read once; 1100 and 1391 are per step), and
`host/forward_replay.py:193,320` (one read each). `git diff main -- simulator/assetops_simulator/kernel contracts` on the
branch is D-DD.75's index only. The owner is informed; no owner weigh-in is needed (no figure moves).

- **D-DD.80 The kernel indexes declared causes by step, as D-DD.75 indexes forcings; the per-boundary rebuild of the
  step starts goes with it; byte-identical** (blocker; protected seam, no contract change).
  - *The class (W6).* A boundary must cost the same whatever the span. Three per-step reads violate it, all in
    `kernel/execute.py`: (1) `_phase_apply_events` walks every cause and, for each POINT one, calls `point_due_at`, a scan
    of every step start: O(steps × POINT causes × steps), the square the timings show (the writer adds a draw a day and
    the notes, so POINT causes grow with the span too); (2) `_phase_evolve` walks every cause at every step for the WINDOW
    and INTERVAL_WIDE shapes: O(steps × causes); (3) `_phase_apply_events` reads `interval.step_starts`, which builds a
    tuple of every step start, at every boundary (8,064 reads at 28 days). D-DD.75 fixed the same class for forcings. This
    ruling closes it: after it, no per-step code in the kernel reads a frozen-input collection or a derived value whose
    size grows with the span. Every other loop over `world.inputs` in `execute.py` is setup (listed above), read once.
  - *Options.* An index of causes by step is taken. `point_due_at` by arithmetic is refused: it is a contract function
    (protected seam; `backend/.../scenarios/execution.py:82` re-exports it), it would leave (2) and (3), and it would put a
    second definition of `point-applied-once` beside the contract's. Caching `step_starts` alone is refused: it removes (3)
    only. With the index, nothing per step reads the step starts, so no cache is needed.
  - *Change (`kernel/execute.py` only).*
    1. `_World` gains `point_causes_by_step: dict[int, tuple[int, ...]] | None = None` and
       `spread_causes_by_step: dict[int, tuple[int, ...]] | None = None` beside `forcings_by_step`, with a comment
       citing D-DD.80.
    2. The step walk of `_forcing_index` moves, unchanged, into one pure helper
       `_steps_overlapping(step_starts, timestep, duration, start, end) -> Iterator[int]`: from
       `max(bisect_right(step_starts, start) - 1, 0)` while `step_starts[cursor] < end`, yield `s` when
       `overlap_minutes(s, min(s + timestep, duration) - s, start, end - start) > 0`. `_forcing_index` calls it; its
       output is unchanged.
    3. New pure function `_cause_index(inputs) -> tuple[dict[int, tuple[int, ...]], dict[int, tuple[int, ...]]]`, read
       once: `step_starts = inputs.interval.step_starts`; for each position `p` of `inputs.causes`, in order:
       - POINT: `due = point_due_at(step_starts, timestep, cause.offset_minutes)` (the contract's function, called once
         per cause); when `due is not None`, append `p` to the first map at `due`.
       - WINDOW or INTERVAL_WIDE: `(start, end) = _entry_span(cause, duration)`; when `end <= start`, append `p` to the
         second map at step 0 (the old loop reached such a cause at the first step and raised from
         `window_share_of_step`; keeping it there keeps that, which D-DD.75 could only skip); otherwise append `p` to the
         second map at every `s` of `_steps_overlapping(...)`.
       Values are tuples, ascending by construction.
    4. `_ensure_cause_index(world)`: when `world.point_causes_by_step is None`, set both maps from `_cause_index`.
    5. `_phase_apply_events`: after the terminal-instant return, call `_ensure_cause_index(world)`. The
       `step_starts = ...` line goes. The cause loop becomes `for position in world.point_causes_by_step.get(world.offset,
       ()):` with `cause = world.inputs.causes[position]` as its first line; the `shape != "POINT"` check, the
       `point_due_at` call and the `due != world.offset` check go (the index holds exactly those). From the `_excluded`
       check on, every line is unchanged.
    6. `_phase_evolve`: after the `begins_a_step` return, call `_ensure_cause_index(world)`. The loop becomes
       `for position in world.spread_causes_by_step.get(world.offset, ()):` with `cause = world.inputs.causes[position]`
       first; the `shape == "POINT"` check goes. From the `_excluded` check on (`_entry_span`, `window_share_of_step`,
       `if share == 0: continue`), every line is unchanged.
    7. Nothing else changes: no contract (`git diff main -- contracts` stays empty), no pack, no writer, no setup check,
       `point_due_at` and `FrozenInterval.step_starts` untouched.
  - *Why it is byte-identical.* (a) POINT: the old loop applied a cause at the one offset where
    `point_due_at(...) == world.offset`; the index stores the cause at exactly that value, computed by the same function
    with the same arguments. Every non-terminal boundary is a step start, and the terminal one returns before the loop in
    both. (b) Spread: `window_share_of_step` is `overlap_minutes(...) / (end - start)` with `world.step_length =
    min(s + dt, duration) - s` (`_advance_one`), so `share == 0` exactly when the helper's predicate fails; the loop keeps
    its own `share == 0` check besides. (c) Every skipped cause was skipped after pure reads (frozen inputs, the run's
    exclusions) with no side effect, and the kept ones are visited in input order, so `grouped`, its lists, the sorted
    address walk, the ledger and the digest are the same. (d) The lazy build covers every way a `_World` is made,
    stepped or batched.
  - *Reach.* One Site type, mini-grid: the ten `EXECUTABLE_MODELS` (minimal fuel tank, daytime mini-grid, mini-grid v1 to
    v8) and the DD3 writer, through `Execution` and `_PHASES`. Packs reached: the mini-grid and fuel packs those models
    bind (`packs/mini_grid.py`, `packs/minigrid.py`), unchanged. Cold chain (`ColdExecution`, its own runner) and EV
    charging (its own path) never reach `_PHASES`; the builder confirms by grep, as for D-DD.75, and adds a case if
    either does. Forward replay (`host/forward_replay.py`) reads the step starts once and is unchanged.
  - *Parity (golden from main's kernel; the loader `--reference main` exists).* Order: first commit the new cases with
    goldens from main's kernel and the test green on the branch's current kernel (D-DD.75 is byte-identical, so both
    agree; the packet shows both digests), then the kernel edit, then all cases green. Existing K1 to K8, D1, F1, X1, W1,
    S1 stay. W1 carries POINT causes (notes, the 02:00 draw); K1 to K8 may carry none, so three cases are added, built on
    F1's run (the minimal fuel tank model, whose tank takes `CAUSAL_INPUT`) with causes added in the test:
    - **C1 (POINT):** causes at offset 0, exactly on a later step boundary, mid-step, two on one address in one step
      (one INCREASE, one DECREASE), and in the last step; plus one on an address the run excludes as `CAUSAL_INPUT` when
      the frozen inputs admit such a record without a setup change (else the packet says it is not made).
    - **C2 (spread):** a WINDOW cause whose first and last steps are partial, one inside a single step, one ending at the
      interval's end, and one INTERVAL_WIDE; on a duration not a multiple of the timestep (short last step) when setup
      admits it (else the packet says so).
    - **S2:** C1 advanced one boundary at a time, equal to C1's digest.
    The zero-length spread cause has no case (setup or `overlap_minutes` refuses it before any case can carry it); the
    packet notes the edge, as D-DD.75's did.
  - *Timing, target and stop rule (packet).* Wall time of the Kobo pure run (`tools/dd3_pure_run.py`, 0.62 L/h) at 7, 14
    and 28 days before and after, and the 123-day run at 0.62 and at 3.3 on the 2500 L tank, with the 28-day cProfile top
    15 after. **Target:** each 123-day run at most **3 minutes** wall on the idle machine, and the cost linear in the
    span: wall(28 days) / wall(14 days) at most **2.4** (linear 2.0, square 4.0). The estimate from Update 5's profile is
    about 2 to 2.5 minutes. **Stop rule:** if either is missed, the builder keeps the edit if parity is green, makes no
    further kernel, writer or window change (never tunes inputs to meet a time), and hands the Architect the timings, the
    28-day cProfile top 15 and the size of `inputs.unmodelled_inputs` at 123 days (`excludes` scans it per cause and per
    forcing; it should not grow with the span).
  - *Order inside DD3a (amends D-DD.79's).* After (4): (4a) the C1, C2 and S2 goldens, committed; (4b) this index, parity
    green, timings; then commit 1b's pure run and (5) as D-DD.79 says.
  - *Units (W4).* DD3.1 2.25 to **2.75** (the index, three parity cases, timings). DD3a 4.75 to **5.25 u**, DD3 10.25 u,
    DD 37.0 to **37.5 u**; each part at or under 6 u. (A parallel DD4 ruling restates DD4 only; the DD total adds both.)

# DD rulings, round 11 (D-DD.81 to D-DD.88): DD4 mid-build questions Q1 to Q5 and the deviation

Architect (Claude), 2026-11-22. Input: `DD4-handoff.md` on `task/DD4-cold-ev-reality` at 66e0ae15d. Checked against
code on that branch: `packs/cold.py` (`ColdLoadParameters`, `step` stages 1 to 7, `_v2_forcing`, the v2 move set),
`world/exports_cold.py` (`_fill`, `_named`, `presence_peak`, `_november`), and on main `tools/dd_check.py:393-451`
(`_EV_PRICE`, `_site_prices`), `world/tariffs.py:62-65` (FLAT reads `tariff.usd_per_kwh`), `tools/world.py:1099` (C5
runs parity files as subprocesses), DD3a's `world/telemetry.py` at c35c50e92 (`SiteRun`, the frame helpers), and `M`
(Kasarani `tariff`, Thika `incident.backup`, the `cooling` family). Two measurements, run read-only on the DD4 branch:
- *Ledger stacking.* The built ledger admits up to 320 crates at one instant (Kirinyaga, every 8 days from 25 Jun;
  Thika and Mwea up to 280). `_fill`'s key (the fewest crates over the stay, ties the earlier day) puts the room's
  batches in lockstep, so admissions stack on the same mornings.
- *Exact arithmetic.* One cold-thermal 2 room stepped minute by minute: the temperature's denominator grows by about
  4,260 digits a day (the leak term multiplies it by 900 each minute), and day 6 alone takes 35 s, so cost grows with
  the square of the span. A 130-day room run would take many hours. Q4's "measured by the writer run" cannot be
  measured until D-DD.87 lands.

The owner is informed of all eight and is asked to weigh in on D-DD.83's prediction (the Thika chamber) and on
D-DD.85 (the receiving rule changes Assumed admission times; no story figure moves).

- **D-DD.81 Deviation accepted: `world/telemetry_cold.py` and `world/telemetry_ev.py` drive their packs, and DD3a's
  `world/telemetry.py` stays the only frame** (amends spec §4.1's module line).
  - *Why.* Each vertical's inputs and pack drive are their own (ledger and rooms; roster, practice and the depot load
    manager). The frame (span, day chaining by D-DD.69, binding map by D-DD.72, rounding, file bytes, manifest,
    refusals) is shared and is written once.
  - *Vertical protocol.* Each module has one class, `ColdSiteRun` and `EvSiteRun`. Each takes `(site, books, first,
    last)` and offers `advance_day()` (one local day, D-DD.69) and `day_records(day)`. `day_records` returns pack
    rows `(device_id, signal_id, start, end, value, unit)`, with UTC instants and exact `Fraction` or state values.
    Each also offers `conditions()` (each with its source key) and `private_parameters()`. The vertical modules do
    not map `source_id`, round, write bytes or build a manifest.
  - *Before DD3a merges,* DD4 tests these classes directly. A refusal is raised with its `TEL_*` code as the message's
    first word, and the tests assert that word.
  - *The join (one commit, after DD4 merges a main that holds DD3a).*
    - `build_telemetry` dispatches on the Site's pack family: mini-grid to DD3a's run, `cold-thermal` to
      `ColdSiteRun`, `ev-charger` to `EvSiteRun`.
    - The vertical modules import the frame's `TelemetryRefused`. No second refusal class, `QUANTUM`,
      `readings_bytes` or binding map remains: the reviewer greps for each.
    - If DD3a's mini-grid run is step-based, the join puts it behind the same day-level protocol.
  - *Reach and parity.* Mini-grid must stay unchanged. Parity test: `simulator/tests/world/test_telemetry_join_parity.py`
    with a golden written from main at DD3a's merge, before the join. Kobo's 7 days from 2026-07-01 (D-DD.75 W1's
    inputs), readings bytes and readings manifest are byte-identical. Cold and EV are new outputs.

- **D-DD.82 Q1: C-DD3 reads a FLAT Site's price at `tariff.usd_per_kwh`, as `M` states it** (default taken; amends
  spec §8.1 C-DD3).
  - `M` gives the FLAT type its one price at `tariff.usd_per_kwh`, and `world/tariffs.py` writes the FLAT band from
    that key. The checker reads the same place in `M` with its own code.
  - `_EV_PRICE` becomes a map from band to a path under the Site's `tariff`: `PEAK` → `prices.peak`, `OFFPEAK` →
    `prices.offpeak`, `NIGHT` → `prices.night_from_1_nov`, `FLAT` → `usd_per_kwh`, `DEMAND` →
    `prices.demand_per_kw_month`. `_site_prices` returns the whole `tariff` block. A missing path stays a FAIL line.
  - *Reach.* The checker's EV clause only. Mini and cold clauses are unchanged; the existing `test_dd1_check` cases
    stay green. Add one case: a FLAT line priced at 0.15 passes, and at 0.16 it FAILs naming `usd_per_kwh`.

- **D-DD.83 Q2: the Thika sequence comes from two v2 mechanisms that match `M`'s backup line; the builder's default
  (reset at the later minute) is refused** (amends spec §4.4 "New forcing" and "Thika").
  - *Why the default is refused.* `M` says: start requested 19:11:05, failed 19:11:10 (start controller), started by
    hand 19:14, cooling running 19:15, `cooling_minutes_unavailable` 4. With the 5-minute timeout the pack reports
    FAILED at 19:16. A reset after that, plus the automatic 2-minute start, gives cooling at about 19:19 and 8
    minutes without cooling. That moves a story figure to fit the model's gap. The gap is in the model, in two places:
    - v1 can report a failed start only at the timeout, but the start controller here reports the failure within the
      same minute;
    - `GENERATOR_RESET` (FAILED → STOPPED, then an automatic start) is not a start by hand.
  - *Mechanism 1: a failed start is reported when it happens.* `ColdLoadParameters` gains
    `start_failure_at_request: bool = False`; `DD_LOAD_PARAMETERS` sets True. In stage 3, a `START_REQUEST` made while
    `generator_fault` is set moves STARTING → FAILED in the same minute and emits `START_RESULT FAILED` (actor
    CONTROLLER, the same correlation) after the request, with both due times cleared. With False, v1's timeout rule
    holds. The timeout still governs a start that neither succeeds nor reports.
  - *Mechanism 2: `GENERATOR_HAND_START` replaces `GENERATOR_RESET`.* It is a v2 forcing on `generator-1` with value
    `RUNNING`.
    - Its move is FAILED → RUNNING at the forcing minute. The v2 move set holds `("FAILED", "RUNNING")` and drops
      `("FAILED", "STOPPED")`.
    - It clears `generator_fault` and emits `START_RESULT SUCCEEDED` with actor OPERATOR (in `V4_ACTORS`).
    - If the transfer is OPEN, it sets `transfer_due = t + transfer_delay`, as stage 2's success branch does.
    - A hand start on a generator that is not FAILED raises.
  - *Thika events (writer):* `GRID_LOSS` and `GENERATOR_FAILURE` at 19:11, `GENERATOR_HAND_START` at 19:14, and
    `GRID_RESTORE` at 22:00 (Assumed). By the pack's own delays this gives:
    - request and FAILED at 19:11;
    - running at 19:14;
    - transfer to backup and the bus powered at 19:15;
    - the compressor by demand from 19:15;
    - 4 minutes, 19:11 to 19:14, without cooling available.
  - *C-DD6* judges GEN-CR-01's failure as the 19:11 `START_RESULT FAILED`, which is now native.
  - *Reach.* cold-thermal 2 only. v1 (the product's `ColdExecution` and the Lab cold Sites) is unchanged; DD4.1's v1
    parity digest and the cold suites guard it. Tests: the failure lands in the request minute; a hand start runs at
    its minute and transfers one minute later; a hand start while STOPPED raises; with the flag False the timeout
    rule holds.
  - *Prediction, for the owner (nothing tuned).* The declared room has 1.2 kWh/°C and 6 kW of cooling. With 2 to 5
    kW of leak, respiration and any lot still pulling down, 4 minutes without cooling warms the chamber by about 0.1
    to 0.3 °C. `M`'s
    chamber figures (peak 8.2 °C at 19:19, 25 to 35 minutes above 4 °C) and C-DD6's "B-1031 above 5 °C for more than
    15 minutes" are not expected to follow from the declared room and the declared 4 minutes. The story's exposure and
    the credit note CN-0412 rest on that clause. The builder measures it in DD4a and stops for the owner if C-DD6's
    B-1031 clause fails, with the measured peak and minutes. The Architect's default for that stop: the readings
    stand, and the owner chooses whether the story's chamber figures follow the room or the room's declared figures
    are revisited.

- **D-DD.84 Q3: C-DD19 is judged by `world check` C5, which runs the two simulator parity tests in a subprocess;
  `dd_check` does not import or run the simulator** (default amended; amends spec §8.1 C-DD19).
  - *Why.* C-DD19 asks whether the simulator agrees with itself, so only a run of the simulator can answer it. The
    checker's independence (D-DD.14) concerns expected figures, and a parity has none. C5 already runs parity files as
    subprocesses (`tools/world.py:1099`), so this uses the existing mechanism.
  - *Change.*
    - C5 gains the cold node id (DD4.1's v1 digest test in `simulator/tests/test_cold_thermal2.py`) now, and DD3.3's
      v8/v9 test when it lands. It runs them with the simulator's interpreter, and the test files go into
      `CHECK_CODE`.
    - `dd_check`'s C-DD19 entry stops being a stub check. It prints `C-DD19 judged in world check C5 (D-DD.84)` and
      is excluded from its pass count; the table in §8.1 says so.
  - *Reach.* `tools/world.py` C5 and `tools/dd_check.py` only. C5's existing bulk-path parity files are unchanged,
    and a `tools/tests` case covers the new node ids with a fake runner.

- **D-DD.85 Q4: a room receives produce in lots at receiving times its declared cooling can pull down, and the pack
  refuses field heat beyond the produce's own temperature** (amends D-DD.63's "Fill", "Clock" and the named batches,
  D-DD.64 (4), and spec §4.4 and §5.2).
  - *What a real cold store does.* A store without a pre-cooler schedules deliveries so that each lot's field heat is
    pulled down before the next lot arrives, and it caps a lot at what the room's spare cooling can take. It never
    takes 320 crates at 24 °C into a 6 kW room in one morning. The 320-crate mornings are an artefact of `_fill`'s
    key, not an operator's practice. The pack's refusal is the honest result of an input no operator would create,
    so the input is fixed. The cooling (a Foundation figure the product sees) and the load table stay as they are.
  - *Receiving rule (declared, from the room's figures).* Each date has two receiving times, 08:00 and 16:00 local.
    Every IN movement takes one free receiving time and carries at most 40 crates (one lot). These figures follow
    from the room's figures:
    - At the world's warmest declared day (the `cooling` family's `warm_dry` 1.02, which gives 24.8 °C) and a full
      room of 400 crates at control low (2 °C), the sustained load is leak 1.824 kW + respiration 0.600 kW + one
      40-crate lot's field heat 2.850 kW (40 × 37/1800 × 20.8 / 6), which is 5.274 kW, inside 6 kW. The largest lot
      that fits is 50 crates. The 40-crate standard batch is one lot.
    - A pull-down lasts 6 h (§4.4), so receiving times 8 h apart never overlap two lots' field heat.
    - The door's 5 minutes per movement (1.2 kW) is a transient of 0.04 kWh and is not part of the sustained budget.
  - *Fill (replaces D-DD.63's placement key).* Standard batches go one at a time to the free receiving time chosen by
    `(crates already admitted that date, the crowd over the stay as now, date, 08:00 before 16:00)`, while their
    in-month crate-days fit in `need`. The remainder batch is placed the same way. A batch leaves at 16:00 seven dates
    later, so crate-days per batch are unchanged. Opening stock uses the same rule, and November keeps 1 to 6
    October's receiving times shifted 31 days. If a month's `need` cannot be placed, `EMU_RECEIVING <site> <month>`
    stops the build for the Architect.
  - *Named batches are received in lots.* They are placed before any fill, in `NAMED_BATCHES` order. Each lot takes
    the latest free receiving time at or before the named instant, full lots last. All lots of a batch share its ref
    and leave at its named OUT instant:
    - B-1029 (60): 40 on 28 Sep 08:00 and 20 on 27 Sep 16:00;
    - B-1031 (120): 40 each on 1 Oct 08:00, 30 Sep 16:00 and 30 Sep 08:00;
    - B-1034 (80): 40 each on 29 Sep 16:00 and 29 Sep 08:00.

    A batch now has one or more IN rows (each its own Movement id) and one or more OUT rows. `Batch` holds `ins` as it
    holds `outs`, and `crate_days_in` and `presence_*` count per lot.
  - *Pack guard.* §4.4's even spread is valid while the chamber is colder than the produce. Each pulse records its
    lot's admission ambient. A minute in which a pulse is active while the chamber is at or above that ambient raises
    `PhysicallyUnacceptable("field heat beyond the produce temperature")`, which the writer reports as `TEL_PACK`. The
    model then never heats a room past its produce. Under the receiving rule it should never fire, and if it does it
    goes to the Architect.
  - *Reach.* Cold only. Mini-grid and EV books are byte-identical (the DD2a and DD2b `books_support` goldens for
    lakeside-power and metro-bus, as the parity). Cold month totals of crate-days, revenue and received are unchanged
    (C-DD3, C-DD4). The ledger and the invoicing CSVs move: they are the pinned goldens, regenerated, and the customer
    split per month may shift. `test_dd4_cold_ledger` asserts unique refs over generated batches only. A new test
    checks three things: no receiving time holds two INs, no IN exceeds 40 crates, and every IN is at 08:00 or 16:00.
  - *Moved, Assumed:* admission times, and the named batches' receipts from 27 Sep. No story figure moves.

- **D-DD.86 Q5: AMBIENT and EFFICIENCY are ratified as private v2 forcings, placed by the writer at local midnights**
  (amends spec §4.4 "Efficiency condition" and "Ambient per day").
  - `AMBIENT` (`ambient-1`) is placed at 00:00 local of each day after the run's first day. Its value is the day's
    ambient as exact decimal text: 24 + (w_d − 1)/0.025, where w_d is the `cooling` family's season × day class with
    no jitter (D-DD.77's rule). That gives 22.8 °C in `cool_dry`, 24.8 °C in `warm_dry` and 24.0 °C in
    `short_rains`. The run's first day takes its ambient from the initial state.
  - `EFFICIENCY` (`compressor-1`) is placed at 00:00 local on a room-month's first day when `f_m` differs from the
    month before (and at the run's first minute when `f_m` ≠ 1). Its value is exact fraction text (`21/20`, `11/10`,
    `117/100`, `500/403`).
  - *Visibility.* The ambient is public: the ambient probe reports it, as in v1, so it needs its binding row
    (`TEL_BINDING` otherwise). `f_m` is written only under the readings manifest's `private_parameters`; the product
    never sees it (D-DD.22).
  - *Assumed.* A day-constant ambient is the resolution `M` declares; the readings manifest's `conditions` say so.

- **D-DD.87 cold-thermal 2 holds the chamber temperature on a declared 10⁻⁶ °C grid and books the rounding in its
  energy ledger** (found in this round; amends spec §4.4).
  - *The fault (a class, W6).* Exact rational stepping of a leak-coupled temperature has unbounded denominators (see
    the measurement above). Every long cold-thermal run has it. The fix is in the pack, once.
  - *Change (`packs/cold.py`, v2 only).*
    - `ColdLoadParameters` gains `temperature_quantum: Fraction | None = None`; `DD_LOAD_PARAMETERS` sets `1/1000000`.
    - After stage 4, `T_q = round_half_even(t_next / q) × q`. `rounding_kwh = thermal_capacity × (t_next − T_q)` is
      added to a new state field `rounding_total`.
    - `check_residual` checks `C × (T − T0) = heat_total − cool_total − rounding_total` exactly.
    - With `None`, `rounding_total` stays 0 and every byte is v1's.
  - *Why it is honest.* The grid is 10⁵ times finer than the probe's 0.1 °C error. The energy ledger stays exact, with
    the rounding stated, so nothing is hidden or clipped. The readings manifest writes the quantum and each
    room-month's `rounding_total`.
  - *Tests.*
    - Zero-terms parity unchanged (quantum None).
    - Every step's temperature denominator divides 10⁶.
    - A 6-hour run, exact against quantised, gives identical probe readings to the thousandth.
    - The residual holds.
    - Timing in the packet: one room for 7 days, and the projected full span.
    - Stop rule: if one room's full span takes over 15 minutes, hand the top 15 `cProfile` lines to the Architect and
      change nothing further.
  - *Reach.* cold-thermal 2 only; v1 is guarded as in D-DD.83. EV: the builder checks `ev-charger` denominators over
    7 days; if they grow, it stops and asks, and does not fix it silently. Mini-grid ran 123 days in DD3a and is not
    touched.

- **D-DD.88 Units: DD4 +1.5 u to 7.25 u, split into DD4a (4.0 u) and DD4b (3.25 u); DD 37.5 u to 39.0 u (after D-DD.80)** (W4: parts of at
  most 6 u; amends spec §7 DD4 and §8.2).
  - **DD4a, cold (`task/DD4-cold-ev-reality`, continuing): 4.0 u.**
    - DD4.1, 1.5 to 2.0 u: D-DD.83 +0.25, D-DD.87 +0.25.
    - DD4.2, 1.25 to 2.0 u: D-DD.85 +0.5, D-DD.81's join and mini parity +0.25.
    - D-DD.82 and D-DD.86 fall inside their units.
  - **DD4b, EV and measured books (`task/DD4b-ev-measured`, from main after DD4a merges): 3.25 u.**
    - DD4.3, 1.75 u.
    - DD4.4, 1.25 to 1.5 u: D-DD.84 +0.25.
  - *Sequencing.* DD4a's join waits for DD3a on main (not DD3b). DD4b follows DD4a. DD5 follows DD3b and DD4b.
  - *Builder order in DD4a.*
    1. D-DD.87, then D-DD.83, in `packs/cold.py` with their tests (v1 digest green at each commit).
    2. D-DD.85's ledger, goldens and parity.
    3. `ColdSiteRun` on the protocol, with D-DD.86's forcings.
    4. After DD3a merges: the join, its parity, and the writer run, measuring Thika against C-DD6.

---

# DD rulings, round 12 (D-DD.89 to D-DD.96): B-1031 resized, DD4a Q1-Q2, DD3a Q1-Q4, the catalogue guard

Architect (Claude), 2026-11-22. Inputs: `packet-DD3a.md` and `DD3a-handoff.md` Update 6 on `task/DD3a-mini-reality`
(816774bc8); `packet-DD4a.md` and `DD4-handoff.md` on `task/DD4-cold-ev-reality` (239980d64). Owner words:
`owner/owner-demo-data-answers-2026-11-22.md` §"B-1031 / CN-0412" ("Change the event": keep the room's declared
physics, resize the incident so it really breaches 5 °C, computed from the room model, not tuned) and
`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`. Checked against code on those branches:
`packs/cold.py` (stage 3 demand at 2/4 °C, stage 4 heat terms, probe on the 5-minute slot), `world/telemetry_cold.py`,
`world/telemetry.py` (`site_inputs`, `_sun`, `DEFAULT_SUN_WEIGHTS`, the readings row), `world/scope.py:15,50`
(`GLOBAL_KEYS` into every scope digest), `world/history.py:104-109`, `world/exports.py` (`NOTE_HOUR`, `_notes`),
`host/cold_publication.py:127-160` (event and correlation ids), `contracts/.../source_envelope_v4.py` (EVENT payload),
`tools/dd_check.py:569` (C-DD11 runs 1-2 Jul), and `M` (Thika `incident`, `kpis`, Kobo `physical` and `period`).

**Measurement (read-only, DD4 branch, scratch script deleted).** Thika as `packet-DD4a.md` ran it: the fixture-view
ledger, cold-lab-001 values with 6 kW cooling, M's seasons, `ColdSiteRun` 1 Jul to 5 Oct, then 6 Oct stepped minute by
minute with GRID_LOSS and GENERATOR_FAILURE at 19:11, GRID_RESTORE at 22:00 and the hand start at minute H. H = 19:14
reproduces the packet (peak 4.049 °C at 21:20, 0 minutes above 5 °C). At 19:11 the compressor is OFF at 3.341 °C;
without cooling the chamber warms by about 0.029 °C a minute (leak 0.08 kW/°C × about 20.5 °C, plus 320 crates'
respiration, over 1.2 kWh/°C) and reaches 5 °C at 20:08. With cooling back it falls about 0.055 °C a minute.

| H (hand start) | per-minute above 5 °C | 5-minute readings above 5 °C | bound from readings | peak (per minute) |
|---|---|---|---|---|
| 20:10 | 7 | 1 | 0-10 | 5.138 |
| 20:20 | 22 | 4 | 15-25 | 5.421 |
| 20:21 | 24 | 5 | 20-30 | 5.449 |
| **20:22** | **25** | **5 (20:10-20:30)** | **20-30** | **5.477 at 20:24** |
| 20:25 | 30 | 6 | 25-35 | 5.561 |
| none (grid at 22:00) | 168 | 34 | | 8.061 at 22:01 |

The owner is informed of all eight. The owner is asked to weigh in on **D-DD.92** before DD3b starts (Kobo's
fuel story moves), and is told the Thika figures D-DD.89 moves.

- **D-DD.89 B-1031: the hand start moves to 20:22, so the chamber really holds B-1031 above 5 °C for 25 minutes; the
  room is unchanged** (owner: "Change the event"; amends D-DD.83's Thika events and spec §4.4 "Thika").
  - *Failure mode.* As `M` states it: the start controller fails the automatic start at 19:11 (D-DD.83's mechanisms
    unchanged). What is resized is the time to a start by hand, not the room. The story already says why it was late:
    "no manual-start rota in October" (`observations.october.stock_and_rota_basis`), and the stopgap it recommends is a
    night manual-start rota plus an SMS alarm relay (`THIKA-EPC-STOPGAP`).
  - *Rule (declared, from `M`'s own figure).* The hand start is the minute at which the room's per-minute time above
    B-1031's 5 °C limit equals the midpoint of `M`'s `above_limit_minutes` "20-30" (25 minutes). That is **20:22**. At
    20:22 the 5-minute readings bound the excursion at 20-30 minutes, as `M` says. 20:21 also reads 20-30, but its
    20:30 reading is 5.064 °C (0.06 °C from the limit); 20:22's is 5.147 °C. The room and its parameters are not
    touched. Nothing in the room is fitted.
  - *New events (writer, from `M` `incident.backup`):* `GRID_LOSS` and `GENERATOR_FAILURE` at 19:11 (requested
    19:11:05, failed 19:11:10), `GENERATOR_HAND_START` at **20:22**, `GRID_RESTORE` at 22:00 (Assumed).
  - *Expected readings, which the DD4a writer run must reproduce:*
    - `START_RESULT SUCCEEDED` (OPERATOR) at 20:22; transfer and bus POWERED at 20:23.
    - Per minute: peak 5.477 °C at 20:24, above 5 °C 20:08-20:32 (25 minutes), above 4 °C 82 minutes, back at or below
      4 °C by 20:52.
    - 5-minute readings: above 5 °C at 20:10, 20:15, 20:20, 20:25 and 20:30 (largest 5.422 °C at 20:25); above 4 °C
      from 19:35 to 20:50 (bound 75-85 minutes); first reading in band 20:55 (3.793 °C).
    - B-1034 peaks at 5.48 °C, below its 12 °C limit. Cooling unavailable 19:11 to 20:23: 72 minutes.
  - *What moves in `M`* (DD4a, one commit, manifest rev bump):
    - `incident.backup`: "started by hand 20:22; cooling running 20:23".
    - `incident.chamber`: `above_4c_minutes` "75-85 (bounded by 5-minute readings)", `peak_c` 5.4, `peak_at` "20:25",
      `back_in_band` "by 20:55".
    - B-1034's `reason`: "peak 5.4 C is below its 12 C limit".
    - `observations.october.cooling_minutes_unavailable` and the incident consequence `cooling_minutes_unavailable`:
      4 → **72**.
    - `kpis` `cooling_availability`: Thika `minutes_unavailable` 4 → 72, `portfolio_pct` 99.997 → **99.946**, and the
      basis "Thika lost cooling 19:11-20:23 on 6 Oct".
    - The `thika-gen-2026-10-06` summary: "started by hand at 20:22".
  - *What stays:* B-1031 `above_limit_minutes` "20-30", `crate_minutes_above_limit` "2,400-3,600", exposure 2,160.00,
    QA (6 crates on 7 Oct), CN-0412 (108.00, `SPOILAGE_CREDIT`), liability 108.00, insurance (below the 500
    deductible), the EPC claim and its dates, and `days_backup_start_unproven` 26.
  - *Books and statements.* Neither the credit note nor any decided book changes. The readings' event rows move
    (above). The cold electricity bill (DD4b, metered, C-DD7 exact) moves a little, because the bus is unpowered for
    72 minutes instead of 4: that is a measured figure, not a story figure. World statements that quote
    `incident.backup` or `chamber` follow `M` through their regeneration.
  - *Sweep (W6, the class: a story figure typed by hand beside the world's).* Grep the Layer-4 docs, the vNEXT mock
    (`fixtures.js`, `screens.js`, `loop-decisions.js`, `CHANGE-REGISTER.md`) and `derived-values.json` for `19:14`,
    `19:15`, `19:19`, `19:45`, `8.2`, `99.997` and Thika's "4 minutes". Regenerate whatever the D-DD.30 chain
    regenerates. Edit the hand-typed text to the figures above and list each file and line in the packet. These are
    content changes only: the mock's form does not move, so there is no MOCK DEVIATION. `backend/`, `frontend/src`,
    `simulator/` and `tools/` hold none of these strings (grep, main 422518cce).
  - *Test (DD4a, after the join):* `simulator/tests/world/test_dd4_thika_incident.py` runs Thika 1 Jul to 7 Oct
    through `build_telemetry` and asserts the event rows, the five readings above 5 °C, and the bound 20-30.
    If any expected figure is not reproduced, stop and report to the Architect. The event is not moved again by hand.
  - *Reach.* Cold only, Thika only. Mwea and Kirinyaga have no events. D-DD.83's mechanism test
    (`test_thika_sequence_is_native`, synthetic 30 Sep) is unchanged.

- **D-DD.90 DD4a Q1: June needs no season; November is declared `short_rains` in the one season map, and the scope
  digest covers only the history's months** (amends spec §2 and §4.4 "Ambient per day"; ratifies DD4a deviation 4).
  - *June.* The span starts on 1 Jul at 00:00 local (D-DD.3), so no reading needs a June ambient. June movements are
    opening crates (spec §5.2). Carrying no field heat is exact, not an approximation: the latest June lot is
    received at 16:00 on 30 Jun, and its 360-minute pull-down ends at 22:00 the same day (D-DD.85). The initial chamber
    at control low stays Assumed and stated in `conditions` (deviation 4, ratified).
  - *November (the class: every vertical's readings reach 6 Nov; mini-grid sun and cold ambient both refuse
    `TEL_FOUNDATION` there).* `M` `history.seasons` gains `"2026-11": short_rains`. The short rains run from October
    to December, and the family weights already declare `short_rains`. So the cold ambient on 1-6 Nov is 24.0 °C, and
    Kobo's sun on 1-6 Nov is the clear shape × 1.00 (D-DD.77's rule). One map holds the season of every month the
    world runs. No second map is added.
  - *Digests unchanged.* `scope.py:50` puts all of `seasons` into every scope digest, so a new key would move every
    seed and history figure. Rule: a scope digest covers exactly what its rules read, so `history_global["seasons"]`
    is restricted to the keys in `months` plus `anchor_period`. Today that is the whole map, so every digest is
    byte-identical. Parity test `simulator/tests/world/test_scope_seasons_parity.py`, golden from main: every scope
    digest of the fixture view, and sha256(history.json) (K8), equal main's.
  - *The default sun table follows its source.* `telemetry.py` `DEFAULT_SUN_WEIGHTS["seasons"]` gains `2026-11`. A
    test asserts it equals `M`'s `history.seasons`.
  - *Who.* DD4a, at the join (DD3a on main), one commit before the writer run. If `check_manifest.py` or
    `history.py` refuses the extra key, the check is changed to "`seasons` covers `months` and `anchor_period` and may
    declare later months of the readings span". The packet lists any pin that moves. None is expected.

- **D-DD.91 DD4a Q2: an event row is a readings row with the v4 EVENT payload fields in an `event` object; the ids
  are formed at sealing** (deviation 3 replaced; amends spec §4.1 "Output" and D-DD.81's `day_records`).
  - *Why.* `source_envelope_v4` EVENT carries `record_kind`, `outcome`, `actor`, `component_id`, `event_id` and
    `correlation_id`, and `host/cold_publication.py` forms the two ids from the pack's `transition_ordinal` and
    `correlation_key`. A `"<KIND> <OUTCOME> <ACTOR>"` string drops the ordinal and the correlation, and it would need a
    second parser at load. One field per fact.
  - *Row.* `{"source_id", "signal_id", "start", "end", "value": null, "unit", "event": {"record_kind", "outcome",
    "actor", "component_id", "ordinal", "correlation": [kind, ordinal]}}`:
    - `start` = `end` = the source time;
    - `unit` is the binding row's `source_unit`, which must be `event` (`TEL_BINDING` otherwise);
    - `ordinal` is the pack's per-channel `transition_ordinal`, continuous over the span (one execution, D-DD.69);
    - `correlation` is the pack's `correlation_key` (`outage` or `door`, one-based).
  - *Order.* Sorted by (start, source_id, signal_id, `event.ordinal`, with 0 for a measurement row), so 19:11's
    request and failure on `start-event` keep the pack's order.
  - *Measurement rows have no `event` key*, so mini-grid bytes are unchanged: the D-DD.81 join parity covers it.
  - *Protocol.* `day_records` returns a seventh element, the event dict or None. `ColdSiteRun._row`'s string packing
    is removed; the reviewer greps for `record_kind} {r.outcome`.
  - *At load (DD5.1, recorded here so nothing is designed there).* `event_id` =
    `cold_event_id(scenario_sha256=<the Site's foundation_digest in F>, device_id, signal_id,
    transition_ordinal=ordinal)`, and `correlation_id` = `cold_correlation_id(<the same digest>, tuple(correlation))`.
    The readings files stay id-free (D-DD.8).
  - *EV (DD4b).* The same object, plus `session_id` and `connector_id` keys only when its pack gives them.

- **D-DD.92 DD3a Q1 (D-DD.19 gate): the books are the wrong side. A mini-grid Site's fuel purchases follow its tank
  by a declared reorder rule, and its consumption is the readings'. Kobo moves with Kisiwa and Mto in DD3b**
  (amends D-DD.32's delivered litres, D-DD.19's fallback and D-DD.76's restated fallback; the owner is asked to weigh
  in).
  - *Which side is wrong.* The declared plant is PV 60 kW (50 kW AC), battery 191.5 kWh, start at 35 % and stop at
    90 %, with load equal to the books' delivered kWh. It burns 37 / 0 / 744 / 508 L, July to October, at 0.62. That
    is physics on declared figures:
    - a July day yields about 6.6 × 0.80 × 60 ≈ 300 kWh of PV against about 283 kWh of load;
    - the battery's 105 kWh between 90 and 35 % carries the night load of about 81 kWh;
    - so the generator runs only after overcast spells (September and October's calendar).
    The notes' 983 / 967 / 1035 / 1180 L were never computed by any plant. D-DD.32 makes them from `history.json`'s
    `necessary_l + candidate_l + unexplained_l`, the history generator's fuel family, whose split D-DD.18 already
    refuses to serve. Overfill is the symptom. The cause is two figures for one quantity (fuel used), and the model's
    is the loyal one. Tuning the Assumed sun or load shape to reach the books' litres is refused.
  - *Fix at the source: purchases and consumption are two quantities.*
    - *Purchases* (delivery notes, the expense ledger, `fuel_balance.deliveries_l`) follow the operator's reorder
      practice on the world's tank. When the level at a step boundary first falls below 25 % of capacity, notes are
      placed at the next 10:00 local (`NOTE_HOUR`; the same day if the crossing is before 10:00). There are as many
      400 L notes as fit in the free space at that instant, at most two. A note dated by a disorder test keeps its date
      (D-DD.53: OOO-1's 400 L enters on 26 Oct).
    - *Consumption* (`diesel_l` = burned + declared draw; necessary, candidate; `diesel_cost` = consumption × price)
      is the readings' (D-DD.18). The declared unexplained draw (D-DD.19) stays a cause in the world.
    - The tool `tools/dd3_pure_run.py --restate-notes --site CODE` iterates: pure run, first crossing, place the notes,
      rerun, until no new crossing in the span. It writes `config/world/fuel-notes.json`
      (`assetops.world-fuel-notes/1`: per Site `site_code`, `rule` "D-DD.92", `tank_l`, and `notes`
      `[{"at", "litres": "400", "basis": "REORDER" | "STORY:OOO-1"}]`). `--check` exits 1 when the file differs from
      what the rule gives. `exports.py` reads that file's notes for a Site present in it.
  - *Tanks stay* (Kobo 2500, Kisiwa 5000, Mto 1000 L): they are declared Site figures now. D-DD.76's rule is not
    re-run on restated books, which would be circular.
  - *Projected for Kobo at 0.62 (the DD3b run gives the figures):* notes Jul 0, Aug 0, Sep two (800 L), Oct OOO-1 only
    (400 L). October consumption about 628 L (burned 508 + draw 120) against `M`'s 1,180. The candidate is about
    42 L against 330, so the CANDIDATE_RUNNING bridge goes from −412.50 to about −52.
  - *Where and when.* DD3b, DD3.3, for all three Sites at once (the class; Kisiwa and Mto after their D-DD.70 pure
    runs). DD3a merges without it. C-DD11 runs 1-2 Jul and the D-DD.81 parity runs 1-7 Jul, and neither reaches an
    overfill. The leaf-by-leaf list (history.json's Kobo fuel nodes, `M` October `period.actual` fuel leaves,
    `fuel_balance`, the bridge, `findings_expected`, derived values) is written as a ruling before DD3b starts, after
    the owner answers.
  - *Owner (asked to weigh in before DD3b).* Kobo is the hero, and its fuel figures move about 2× in consumption and
    about 8× in the candidate. Default: as above, loyal to the declared plant. The alternative is the owner's, as for
    Thika: keep the story's fuel and revisit a declared plant figure (PV size, battery, dispatch). Fitting the
    Assumed inputs is never an option.

- **D-DD.93 DD3a Q2: the five test figures are re-pinned to the new world in DD3a's fix round** (confirmed).
  - The five are:
    - `test_dd3_datasheet_template` CLI check;
    - `test_dd3_telemetry` frozen inputs (40 → 36, 0.3 → 0.2917);
    - `test_dd2_nodes` July;
    - `test_dd2_checker` C-DD4 plant;
    - backend `test_dd2_check` July.
  - Each is re-pinned to the regenerated source's value. Where the test already reads a file or golden, it asserts
    the read value. A literal is set to the regenerated figure, never a hand computation, and the packet lists old →
    new.
  - The CLI test stops depending on the repo's state. It copies the slot file to `tmp_path` with one property
    reverted, asserts `--check` exit 1 and the diff line, runs `--write`, then asserts exit 0.
  - The earlier edit was refused by the permission system. The coordinator grants the fix-round builder edits on
    these five files.

- **D-DD.94 DD3a Q3: `worked-portfolios.md:74` cites the declared rate instead of typing 0.30** (amends nothing;
  W6 sweep).
  - "× 0.30 L/kWh" becomes "× 0.2917 L/kWh" with the reference `rec:tenants[lakeside-power].sites[Kobo].physical.sfc_l_per_kwh` in the line's comment, as the other figures there carry. 1,060 L
    stays `M`'s October `model_implied_l` until D-DD.92 moves October's fuel in DD3b.
  - Sweep: Kobo figures typed by hand that commit 2 moved (0.30 L/kWh, a 40 kW genset, a 200 kWh battery) across the
    Layer-4 docs and the vNEXT mock become their `rec`/`fig` references. They are listed in the packet.
    `check_alignment.py` and `check_manifest.py` stay at their base counts.

- **D-DD.95 DD3a Q4: `site-inputs` reads `/2` onboarding documents only, and `rating` is optional, so `F` serves
  every Site type** (fixes a DD3.1 defect; amends spec §4.1 "`F` is written by").
  - The class: `F` is per Site for every Site type (D-DD.28), but `site_inputs` assumed a mini-grid component.
  - *Change.*
    - `_site_inputs` reads documents whose `format` is `assetops.operator-onboarding/2`. Every other document is
      skipped with a stderr line `SKIPPED <file> <format>`.
    - A component's `rating` is written only when it has one.
    - A Site code in two read documents refuses `TEL_FOUNDATION`.
    - The mini writer's own needs still refuse `TEL_FOUNDATION` when a needed value is absent.
  - *Parity.* `F`'s Lakeside entries built from `backend/tests/fixtures/on1` are byte-identical to `F` built from the
    `/2` Lakeside file alone. The golden comes from the branch's current `/2`-only run, since main has no
    `site-inputs`.
  - Tests: a `/1` file is skipped, a cold component without a rating passes, and a duplicate code refuses. C-DD11
    must then PASS.

- **D-DD.96 The statement catalogue is a required guard for every DD builder; units** (coordinator: main was broken
  by a merge that skipped it; amends spec §8.3 and §7).
  - Every DD packet runs `tools/checks/statement_catalogue.py`. It must exit 0, or give output identical to main's,
    run at the same time on the same base, with both outputs cited (ROLE_CONFIG brief footer). A builder whose diff
    adds a line fails.
  - *Units (W4).*
    - DD3a: 5.25 → **5.75 u** (D-DD.93/94 +0.25, D-DD.95 +0.25).
    - DD3b: 5.0 → **6.0 u** (D-DD.92 +1.0: the tool, the notes file, `exports.py`, regeneration and the moved list).
    - DD4a: 4.0 → **5.0 u** (D-DD.89 +0.5, D-DD.90 +0.25, D-DD.91 +0.25).
    - DD: 39.0 → **41.5 u**. Every part stays at 6 u or less.
  - *DD3a fix-round order:* D-DD.95, D-DD.93, D-DD.94, then the guards and the packet.
  - *DD4a, after DD3a merges:* D-DD.90, the join with D-DD.91, D-DD.89's `M` commit and sweep, then the writer run,
    `test_dd4_thika_incident.py` and C-DD6.

---

# DD rulings, round 13 (D-DD.97 to D-DD.101): Kobo's plant figure (DRAFT), DD4b pre-flight Q1-Q18

Architect (Claude), 2026-11-22, fresh hand-off after round 12. Read: `owner/owner-demo-data-answers-2026-11-22.md`
§"D-DD.92 Kobo fuel story" and its follow-up ("Revisit a plant figure"; "None: have the Architect propose");
`/opt/assetecon/evidence/kobo-datasheets/datasheets.md`; `specs/DD-demo-data/DD4b-preflight.md` on
`task/DD4b-ev-measured` at 8d519ef49; DD3a's writer on `task/DD3a-mini-reality` (worktree head 193a7cb5f with the
fix round's uncommitted D-DD.95 edits), run read-only from the session scratchpad.

The owner is informed of all five. **D-DD.97 was approved by the owner on 22 Nov ("Approve 18:00 peak"; owner-demo-data-answers-2026-11-22.md)**; nothing is built from it until the
owner approves. The owner is asked to weigh in on **D-DD.98**'s story consequence (Kasarani's November departures).

- **D-DD.97 (owner-approved 22 Nov) Kobo's weakest assumed plant figure is the load profile's timing: the
  residential evening block starts at dark. Honestly run, it does not enlarge the fuel story** (would amend spec §4.1
  `LOAD_SHAPE_KW`; owner rule: loyal to the operating world, nothing fitted).
  - *The three candidates, by provenance.*
    - *Solar 60 kWp.* The Site's declared size. With the writer's sun (clear day 6.6 kWh/m², performance 0.80), Kobo's
      October yield is about 4.4 kWh/kWp a day (23 clear, 8 overcast days), within the 4.3-4.5 kWh/kWp a day that
      Kenyan PV typically yields. Against about 283 kWh/day of sold load, 60 kWp is a plausible size. No source for a
      comparable site gives a better figure. Not the weakest.
    - *Start/stop SOC 35/90 %.* Operator settings inside common practice: inverter makers' generator-start examples
      run 30-40 % (SMA Sunny Island manual, parameters 235.03/235.04, example start 40 % by day, 30 % at night), and
      cycle charging commonly stops at 80-90 %. Defensible as declared. Not the weakest.
    - *Load profile.* `LOAD_SHAPE_KW` was copied from a test fixture's blocks (`host/tests/kobo_season.py`, season v2),
      not from a source. Its residential peak (14 kW) runs 16:00-19:59. Kobo is near the equator (Africa/Nairobi),
      where sunset is about 18:30-18:50 all year, and the writer's own sun is zero from 18:00. So half of the evening
      peak sits in daylight, when households are out working. Measured East-African mini-grid data put household use
      from 18:00 (Hartvigsson and Ahlgren 2018, *Energy for Sustainable Development* 43:186-195, Tanzania, measured
      household spike at 18:00). Tanzanian micro-grid segmentation work puts the peak at about 19:00-20:00, with
      lights, radio and TV mostly 18:00-22:00 (search excerpt, secondary read). **This is the weakest figure.**
  - *Proposed value (Assumed).* The residential evening block (14, 14, 14, 14, 9, 9, 5, 5) starts at dark, 18:00
    local instead of 16:00. The two afternoon hours it leaves (16:00-17:59) take the afternoon level, 8 kW. Hours
    00:00-01:59 take the block's tail, 5 kW. Result: `res` = (5, 5, 3, 3, 3, 5, 8, 8, 6, 6, 5, 5, 6, 6, 8, 8, 8, 8,
    14, 14, 14, 14, 9, 9). Clinic and mill are unchanged. The month's load energy stays the books' `delivered_kwh`
    (largest remainder), so only the timing and the feeders' shares move. Basis line in `conditions`: "residential
    evening use from dark (18:00 local); Assumed from measured East-African mini-grid profiles".
  - *Outcome (DD3a writer, `tools/dd3_pure_run.py`'s table, 1 Jul-31 Oct, no-load 0.62, the books' notes, run
    read-only).*

    | Kobo, October | Declared shape (D-DD.92) | Proposed shape | Story (`M`) |
    |---|---|---|---|
    | Burned (readings) | 507.86 L | 514.22 L | |
    | Consumption (burned + 120 L declared draw) | about 628 L | **about 634 L** | 1,180 L |
    | Candidate (the writer's stand-in: slots the battery could have carried) | 42.03 L | **24.56 L** | 330 L |
    | CANDIDATE_RUNNING bridge at 1.25 $/L | about −52.54 | **about −30.70** | −412.50 |
    | Generator hours | 51.2 | 51.3 | |

    September moves 772.86 → 782.91 L; July and August are unchanged to 0.1 L. The fuel is set by October's eight
    overcast days (PV about 110 kWh against about 283 kWh of load). The battery carries the later evening. So the
    timing barely moves the litres, and the candidate falls, because more of the generator's slots are ones the
    battery could not have carried.
  - *Sensitivities, run the same way (information only; none is proposed):* start/stop 40/80 % gives October
    burned 460.43 L (consumption about 580 L, stand-in 26.43 L); PV 50 kWp gives 548.59 L (about 669 L, stand-in
    9.45 L). **No sourced value of any of the three figures comes close to 1,180 L.** About 1,060 L burned would
    need the generator to carry about 40 % of October's load.
  - *Alternative.* None of the three is a close contender. The honest alternative is D-DD.92's default: keep the
    declared plant (about 628 L, candidate about 42 L, bridge about −52). The proposed shape costs one constant and
    a re-pin, and its effect on the story is small. Kobo's fuel story is then the smaller one. Its value rests on
    the 120 L unexplained draw and the overcast-spell runs, not on a 330 L candidate.
  - *Reach if approved.* `LOAD_SHAPE_KW` is one shape at every mini-grid Site, so Kisiwa and Mto move with Kobo. That
    is the class: one world, one shape. `host/tests/kobo_season.py` (0K4's fixture) is not touched. DD3b applies it,
    in DD3.3, before D-DD.92's restated notes (or DD3a's fix round if it has not merged, D-DD.101). The writer's frozen-input pins and DD3a's goldens that read the shape
    are re-pinned from the regenerated source (D-DD.93's rule), and the packet lists old → new. If approved, +0.25 u
    (D-DD.101).

- **D-DD.98 DD4b Q10: real depot practice rotates a full bus off its connector, and the spare bus charges by day. The
  readings stand; `M`'s capacity stage pools energy that one bus cannot draw, so Kasarani's November departures move
  in the story, not the room** (amends spec §4.5; replaces Q9's spare row; the owner is asked to weigh in).
  - *Practice (world, §4.5).*
    - Depots with fewer connectors than buses rotate plugs overnight. The attendant unplugs a bus that has its charge
      and plugs in a waiting one.
    - **Rule:** at the first minute a bus is waiting and a plugged bus has its `required_kwh`, the full bus `UNPLUG`s
      (session END). The longest-waiting bus (ties: roster order) plugs in on that connector `ROTATION_MINUTES` = 5
      later (Assumed attendant handling, in `conditions`). An unplugged full bus stays parked until its departure.
    - The load manager is unchanged: 1 kW round-robin quanta, as §4.5.
    - A fault-aborted bus is a waiting bus (Q7).
  - *The spare (replaces Q9's ninth night bus).* A spare is a free bus kept charged; it is not queued against the
    night's buses.
    - On each spare night it arrives at 10:00 local on the night's start date (Assumed), plugs in on arrival and
      charges on the idle daytime chargers.
    - It is unplugged by the rotation rule at 22:00, when the returning buses wait, and departs at 05:00 with
      150.000 kWh.
    - Roster row: bus `EV-KAS-S01`, block `EV-KAS-BLK-S01`, `return_at` 10:00 local, departure 05:00,
      `required_kwh` 150.000.
    - Spare nights: 2, 3 and 4 Nov (Q9's dates, ratified, `SPARE_NIGHTS` with its parity test).
    - Its daytime kWh is in the Site import and the FLAT invoice: a measured figure.
    - In the departure log the spare's row (`block_met` true) is the cover. The measured departures missed are the
      short rows less the spare rows met, as `M`'s `departures_missed` counts them.
  - *Reach.* Rotation acts only where a bus waits. Embakasi has 20 connectors for 20 buses. Ruiru has 23 working
    connectors for 14 buses. So only Kasarani after 1 Nov 23:40 changes. Parity test (golden from the branch at
    8d519ef49): the Embakasi and Ruiru plant days in the pre-flight are byte-identical.
  - *Physics (projection; the writer measures).*
    - A bus draws from one charger, and a 50 kW charger delivers 350 kWh in the 7-hour window. That is two full
      buses (300 kWh) and 50 kWh spare.
    - With three chargers, at most **six** buses are full. Two are short each night, at about 46 kWh each (04:05 to
      05:00 at 50 kW), with or without rotation. Night 1 is similar, with B03 and B04 at about 87 kWh.
    - Rotation lifts night energy from 900 to about 990 kWh. It cannot make a seventh bus full without moving a bus
      across chargers twice a night. That is refused as contrived practice.
  - *Where the figures differ.* `M` `EV_DEPOT_CAPTIVE` gives `buses_short_per_night` =
    ceil((1,200 − 3 × 50 × 7) / 150) = **1**: energy pooled across chargers. The room gives **2**. So `M` counts
    departures missed 5 × 1 − 3 = 2 (penalties 240.00), and the readings give about 5 × 2 − 3 = 7 (about 840.00).
    The class is two figures for one quantity, and the readings are the loyal one (D-DD.92's precedent). No world
    figure is tuned to `M`'s.
  - *Default, applied pending the owner:*
    - DD4b builds the practice above. The departure log and invoices are the readings'. `meter_billed` prints `M`'s
      figures beside them, as information (§5.6). C-DD7 is unchanged: readings against books.
    - The structure fault goes to the structure's owner as a finding, not a DD edit. The capacity stage should bound
      buses by charger as well as by energy: `buses_short_per_night` = max(the energy bound, `buses` −
      `chargers_in_service` × floor(min(`charger_kw`, `connector_kw`) × `window_h` / `kwh_per_bus_night`)). For every
      Site and option where the per-charger bound does not bind, which is all of them except Kasarani from 1 Nov, the
      figure is unchanged. The code is `backend/assetops_backend/structure/rows_ev_depot.py` and `M`'s
      `EV_DEPOT_CAPTIVE`, with a parity test from `backend/tests/golden/6h_parity.json` for every other figure.
    - Kasarani's November story (2 missed, 240.00, the stopgap's covered bus-nights) is restated only after that
      change and the owner's answer.
  - *Owner (asked to weigh in).* Kasarani's charger fault story grows: about 7 missed departures and about 840 in
    penalties, against 2 and 240, unless the spare is lent on more nights. The alternative is a depot that moves a
    bus across chargers to fill a seventh. That is a workaround: it is not common practice, and it is not proposed.

- **D-DD.99 DD4b Q16: the `measured.json` schema is DD3a's `assetops.world-measured/1`, extended per vertical; DD4.4
  starts after DD3a, DD4a and the join are on main** (amends spec §4.1 "Output" and §5.6; unblocks DD4.4).
  - *One file per tenant*, `<slug>/telemetry/measured.json`, written by the frame:
    `{"schema": "assetops.world-measured/1", "tenant": <slug>, "sites": {<code>: {<YYYY-MM>: <month>}},
    "departures": [...]}`.
    - Only the EV tenant's file has a `departures` key; no file writes an empty list.
    - Mini-grid months are byte-identical to DD3a's `measured_for`.
  - *`<month>` by vertical (key set fixed per vertical; any other key refuses `TEL_FOUNDATION` at read):*
    - mini-grid: DD3a's `{"demand_kwh": {feeder: kWh}, "served_kwh": {...}, "unserved_kwh": {...},
      "generator_kwh"}`, unchanged;
    - cold: `{"room_kwh"}`, the Site's room meter, Σ over the month's 5-minute slots of the exact slot energy;
    - EV: `{"bands": {<price class>: kWh}, "demand_kw", "import_kwh"}`. The price classes are those of the Site's
      schedule in that month (`PEAK`/`OFFPEAK`, plus `NIGHT` at Embakasi from 1 Nov, `FLAT` at Kasarani).
      `import_kwh` = Σ bands. `demand_kw` = the largest mean of six consecutive 5-minute slots aligned to :00 and
      :30 (Q17).
  - *Months.* Every month the readings touch. A month the span ends inside (November, to 6 Nov 06:00 local) carries
    `"partial_to": "<ISO local instant>"`. `exports_measured` writes bills and invoices for whole months only (July to
    October). The departure log covers every bus-night in the span.
  - *`departures`*: one object per roster bus-night, sorted by (`site_code`, `departure_at`, `vehicle_ref`). Fields:
    `site_code`, `vehicle_ref`, `block_ref`, `service_day`, `departure_at` (roster), `required_kwh`,
    `kwh_at_departure`. `block_met` and undelivered kWh are not stored: they are derived (one fact, one field;
    C-DD7 derives them).
  - *Numbers.* Every value is exact decimal text written by DD3a's `_decimal` (half-even to 0.001). Sums are taken
    over exact fractions and rounded once, at writing. `exports_measured` reads the written text, so a book equals
    the file exactly.
  - *Who.* DD4.4, after DD3a, DD4a and the join are on main (builder default, ratified). The schema is written in the
    frame (`measured_for` extended), with one test per vertical and a parity test: the mini-grid bytes equal DD3a's.

- **D-DD.100 DD4b Q1-Q9, Q11-Q15, Q17-Q18: the builder's defaults are ratified, with three amendments** (amends
  spec §4.5 where named).
  - *Ratified as written:*
    - Q1: `max_plugs`, v1 byte-identical;
    - Q2: always enabled;
    - Q3: declared component order, not string order; CLOCK-1's third charger is `ch-e3`;
    - Q4: `telemetry_ev.py` writes ev-publication/1's record set itself, with no ev-observation/1;
    - Q6: shares capped by need × 60 kW;
    - Q7: an aborted bus rejoins the queue;
    - Q8: November nights 1-5. Ruiru's `M` `nights: 6` beside 5 night records is information for the meter_billed
      line, not changed here;
    - Q11: an empty depot at 1 Jul 00:00;
    - Q12: CLOCK-1 shifts the session rows only;
    - Q13: deterministic tokens;
    - Q14: the `p_m` table with a parity test;
    - Q15: D-DD.87's denominator test;
    - Q17: band kWh and DEMAND, written per D-DD.99;
    - Q18: departure kWh, rounded per D-DD.99.
  - *Amended:*
    - Q5: "the bus stays plugged" holds only until D-DD.98's rotation rule unplugs a full bus;
    - Q9: the spare is a daytime-charged bus (D-DD.98), not a ninth night bus;
    - Q4's rows: a 5-minute `INTERVAL_MEAN` split at a session boundary is still one row per slot per connector,
      with the mean over the minutes the session held. The reviewer checks Σ row energy = meter delta per session.
  - All Assumed practice (5-minute rotation handling, the spare's 10:00 arrival, the empty start) is written in the
    readings manifest's `conditions`.

- **D-DD.101 Units** (W4).
  - DD4b: 3.25 → **3.75 u** (D-DD.98 +0.5: rotation, the daytime spare, the parity test).
  - D-DD.99 adds no units: DD4.4 already holds the measured books.
  - DD: 41.5 → **42.0 u**.
  - If the owner approves D-DD.97, it adds +0.25 u. If DD3a has not merged, it lands in DD3a's fix round (5.75 →
    6.0 u). Otherwise it lands in DD3b, whose 6.25 u would exceed W4's 6 u, so the Architect then splits DD3b
    before it starts. DD is then 42.25 u either way.
  - Every part stays at 6 u or less.

---

# DD rulings, round 14 (D-DD.102 to D-DD.107): DD3a review round 1 (M1, M2, L1-L6, Q1-Q4) and D-DD.97's placement

Architect (Claude), 2026-11-22, fresh hand-off after round 13. Read: `specs/DD-demo-data/review-DD3a.md` on
`task/DD3a-mini-reality` (35ac7f958); spec §2, §4.1, §4.2, §7, §8.2; rulings D-DD.48 to D-DD.101. Checked against code
on that branch: `world/scope.py` (`scope_input`, `GLOBAL_KEYS`), `world/history.py` (`_Scope`, `_parse`, `_value`'s
`fleet_kwh`/`fleet_nights`, the only `scope.physical` reads), `world/telemetry.py` (`frozen_inputs`, `_draws`,
`books_for`, `SEASON_V2_LAST_DAY`), `tools/world_history.py` (`--end`), `host/tests/kobo_season.py` (`SEASON_DAYS`),
and `M` (`as_of`, every `physical` block: Kobo, Kisiwa, Mto and the three depots; no cold Site has one).

**Measurement (read-only, DD3a head, scratch deleted).** Lakeside's books from `world_history.py exports`, Kobo through
`tools/dd3_pure_run.py`'s path (no-load 0.62), July only, the starting state of charge varied:

| Start SOC | July generator hours | July burned (readings) | SOC at 23:55, 1 Jul | 2 Jul min / 23:55 |
|---|---|---|---|---|
| 40 % (today's hidden default) | 3.75 h | 37.39 L | 60.402 % | 44.6 % / 60.402 % |
| 55 %, 70 % | 0 | 0 | | |
| 90 % | 0 | 0 | 60.402 % | 44.6 % / 60.402 % |

So Kobo's whole July fuel (D-DD.92's "37 L in July, 0 in August") is the undeclared 40 % start: from 40 % the battery
crosses the 35 % start in the first night. Any start of 55 % or more burns nothing, and the plant's own midnight state
is about 60.4 %, reached within one day from either end. L1 is therefore a story figure, not a label.

The owner is informed of all six. No ruling needs the owner's decision. Two story consequences are reported
(D-DD.102: July-September figures re-drawn once at six Sites; D-DD.104: Kobo burns no fuel in July).

- **D-DD.102 Q1 (M1): a scope digest covers only the `physical` keys its rules read; the read set is declared beside
  the rules that read it** (amends `scope.py`'s digest input; the D-DD.90 class, for `physical`; not the reviewer's
  default as written).
  - *Why the default cannot hold as stated.* Main's Kobo digest contains main's whole `physical` block (40 kW, 0.30,
    200 kWh). Any rule that drops or changes those bytes gives a digest different from main's. So "Kobo's digests
    equal main's" is impossible without keeping the old kit in the digest, which is the fault itself. And restricting
    `physical` necessarily changes every scope whose block holds an unread key: the three mini-grid Sites (no rule
    reads any) and the three depots (rules read `buses` and `kwh_per_bus_night`; the block also holds `chargers`,
    `charger_kw`, `import_limit_kw` and others). Only the cold scopes (no `physical`) are untouched.
  - *Decision.* Fix the class now: a one-time re-draw of the jittered July-September leaves at six Sites, after which
    no kit correction (Kobo's sheets, a future Kisiwa or Mto sheet, a depot import limit) ever re-seeds a history.
    Rejected: an instance fix for Kobo (a fitted seed or an excluded key list), which leaves the leak at five Sites.
    Rejected: carrying M1, because a data-sheet correction moving demand breaks "one figure, loyal to the operating
    world".
  - *Change (`world/scope.py`).*
    - `PHYSICAL_READS: dict[str, tuple[str, ...]] = {"fleet_kwh": ("buses", "kwh_per_bus_night"),
      "fleet_nights": ("buses",)}`: per rule word, the `physical` keys it reads. A rule word absent from the table
      reads none.
    - `physical_read(site_doc: dict, rules: dict) -> dict`: the words are the first whitespace token of every string
      rule on both sides of `rules` (the split `_parse` uses, without its checks); the result is
      `{k: site_doc["physical"][k] for k in sorted(union of PHYSICAL_READS[word]) if k in site_doc["physical"]}`, or
      `{}` when the Site has no block.
    - `scope_input` writes `site["physical"] = physical_read(site_doc, rules)` only when it is non-empty; otherwise the
      key is absent.
  - *Change (`world/history.py`).* `_Scope.__init__` stores `self.physical = physical_read(site, rules)`, and
    `_Scope.physical` reads that dict, not `self.site["physical"]`. A rule reading a key not declared for its word
    therefore refuses with the existing missing-key refusal: the table cannot drift from the reads.
  - *Sweep (W6).* The builder lists, in the packet, every key of the digest input (`history_global` keys, `rules`,
    `tenant`, `site`) and the rule word that reads it. `seasons` is D-DD.90's (DD4a). Any other unread input is
    reported to the Architect and not changed in this round.
  - *Tests (shared behaviour: every Site type named).* New `simulator/tests/world/test_scope_physical_reads.py`:
    - cold (unchanged): every cold scope digest of the fixture view, and the cold blocks of `history.json`, equal
      main's (golden from main at the fix round's base);
    - kit invariance: for every Site with a block, every key outside its read set changed (for Kobo: DD3a's kit
      replaced by main's 40 / 0.30 / 200) leaves every scope digest and every `history.json` block byte-identical;
    - read sensitivity: Embakasi's `buses` changed moves Embakasi's three scopes and no other;
    - every mini-grid scope input has no `physical` key.
  - *Regeneration.* `history.json` and the D-DD.30 chain (exports, the Layer-4 derived values, the mock's generated
    fixtures) are rerun as commit 2 ran them. Pins re-pin by D-DD.93's rule (K8, `PINNED_ALL_MONTHS`, the DD2 node and
    checker pins, backend `test_dd2_check`; a literal is the regenerated value, never a hand computation). The packet's
    moved list is grouped by Site: Kobo, Kisiwa, Mto, Embakasi, Kasarani, Ruiru; the three cold rooms must show none.
    Kobo's July-September figures do not return to main's: they are a third draw, and from here on independent of its
    kit.
  - *Who.* DD3a's fix round, first. DD4a and DD4b rebase on it (both follow DD3a) and re-pin by the same rule.

- **D-DD.103 Q2 (M2): the readings span is one declared constant; a month with no books runs at the last booked
  month's rate; the last day file ends at 06:00. DD4a builds it with D-DD.90** (amends spec §2, §4.1 "CLI", §4.2
  "Load" and "Fuel"; not the reviewer's default on the draw).
  - *Span.* `world/telemetry.py` declares `READINGS_SPAN = ("2026-07-01T00:00", "2026-11-06T06:00")`, local time, once.
    The mini-grid, cold and EV writers, the CLI defaults and DD5's world manifest `span` read it. A test asserts its
    end date equals `M` `as_of` and its start is `M` `history.months`' first day.
  - *The end instant.* The execution horizon ends at the end instant: no step is computed after 06:00 on 6 Nov. The
    last day file, `<SITE>.2026-11-06.readings.json`, keeps schema `assetops.world-readings/1` and holds the rows whose
    `end` is at or before 06:00. The Site manifest's `span` gains `"to": "<ISO local instant>"`. C-DD5 counts 6 Nov as a
    span day with readings to 06:00. `measured.json`'s November month carries `partial_to` (D-DD.99).
  - *CLI.* `--start` and `--end` default to `READINGS_SPAN`. `--end` takes a local date (the whole day: end instant at
    the next midnight, as today) or a local instant `YYYY-MM-DDTHH:MM`.
  - *Load in a month with no books (the class: every mini-grid Site, any day past the accounting period).* `books_for`
    writes the month as `{"rate_of": <accounting period>, "delivered_kwh": E}`. With `W(d)` the demand day weight and
    `S(h)` the summed load shape (kW) at hour `h`: the intensity is `k = delivered_kwh(October) /
    Σ_{d in October} W(d)·Σ_{h<24} S(h)`, and `E = round_half_even(k · Σ_{d in the month, in the span} W(d)·Σ_{h in
    the span on d} S(h))` kWh. The month's blocks inside the span are then scaled to `E` by largest remainder, as every
    month. October is the source because it is the last month booked and November shares its season (D-DD.90).
  - *Draw.* The declared unexplained draw is a cause in the world (D-DD.19), and nothing records its end. It does not
    stop at a month boundary. A `rate_of` month's day `n` draws the rate month's day-`n` part (the same centilitres,
    at 02:00), so 1-6 Nov draw October's first six parts. That includes 6 Nov at 02:00, which is inside the span. This
    is the cold ledger's rule (D-DD.63's extension repeats 1-6 Oct). The reviewer's "no draw" would make the cause
    vanish at all three Sites on 1 Nov, which no record says happened.
  - *Conditions.* `conditions.month_without_books = {"rule": "D-DD.103", "load": "the rate month's kWh per weighted
    shape unit", "draw": "the rate month's daily parts by day of month", "rate_of": "2026-10"}`.
  - *Tests (`simulator/tests/world/test_dd4_span_end.py`).* Kobo from 1 Nov to the span end writes six files. The last
    one's rows all end at or before 06:00, each 5-minute signal has 72 slots, and the last `end` is 06:00. November's
    load energy equals `E`. There are six draw rows at 02:00. A cold room (Mwea) ends at the same instant. Days 1 Jul to
    31 Oct are unchanged (C-DD11's golden digests stand).
  - *Who.* DD4a, at the join, after D-DD.90's map commit and before the writer run (+0.5 u). It belongs with D-DD.90:
    both make every vertical reach 6 Nov. A full Kobo run to 6 Nov 06:00 needs D-DD.92's notes (the overfill), so DD3b's
    notes run comes after DD4a is on main (D-DD.107).

- **D-DD.104 Q3 (L1): the starting state of charge is the plant's own midnight state, from one warm-up day; 40 % is
  removed** (amends spec §4.2; replaces the reviewer's default, which would have kept a figure that creates July's fuel).
  - *Rule.* Before the span's execution starts, the writer runs one warm-up day: the span's first day's inputs (load,
    sun, no fuel note and no draw), from the Site's declared stop SOC threshold (`generator-stop-soc-threshold`, Kobo
    90 %), with the tank as declared (D-DD.19). The SOC at the warm-up's end is the execution's `starting-state-of-charge`,
    exact, `answered_by` "SCENARIO". The warm-up writes no readings and no ledger row. Measured on DD3a's head, Kobo's is
    about 60.4 % (table above). A second warm-up day gives the same 23:55 value.
  - *Written.* `conditions.start_soc = {"value": <exact>, "unit": "%", "basis": "Derived: the 00:00 state after one
    warm-up day of the span's first day from the declared stop threshold (D-DD.104)"}`. `books.get("start_soc", 40)`
    is deleted. No book carries a SOC.
  - *Sweep (W6: every execution's starting state).* SOC is the only state with a daily cycle. The tank stays 50 %
    Assumed (D-DD.19; a level depends on delivery history, not the day), the generator starts OFF, the cold chamber at
    control low (D-DD.90), and EV with empty batteries (D-DD.100). Each is already written in `conditions`.
  - *Reach.* Mini-grid only (Kobo, Kisiwa, Mto, one rule). Kobo's July burned goes 37.39 → 0 L, so its July consumption
    is the 12 L draw. Cold and EV are untouched. W1's frozen inputs move, so its golden is regenerated with main's
    kernel (D-DD.68's path). The writer's frozen-input pins and C-DD11's golden digests re-pin by D-DD.93's rule.
  - *Who.* DD3b, in DD3.3, with D-DD.97 and before D-DD.92's notes: both move the litres the notes follow (+0.25 u).
    L1 is carried out of DD3a with this reason. Nothing reads DD3a's readings before DD5.

- **D-DD.105 Q4 (L4): the vNEXT mock's hand-typed Kobo kit goes to the design-doc alignment pass** (amends D-DD.94's
  sweep, mock part only).
  - "200 kWh" (`screens.js` 18 times, `screen-manifest-vnext.json` 5), "40 kW" (4) and "0.30 L/kWh" (`screens.js`
    lines 112, 279 and 478) become `rec`/`fig` references, or the declared figures, in the alignment pass that
    `.ai/NOW.md` queues after IA-P and DD. The mock has no reference mechanism in those strings, and that pass
    regenerates it from its audit. The mock is a destination reference, not the live product, so nothing served shows
    the old kit.
  - D-DD.94's Layer-4 document part stands as done in DD3a. The coordinator adds "Kobo kit strings (D-DD.105)" to the
    alignment-pass line in `.ai/NOW.md`. DD3a's packet records the deferral in one line.

- **D-DD.106 L2, L3, L5, L6: fixed in DD3a's fix round, as the reviewer proposes, with L2 made exact.**
  - *L2.* `telemetry.py` declares `SEASON_V2_DAYS = 61` (D-0K2.1's calendar length) and `SEASON_V2_LAST_DAY =
    SEASON_V2_DAY_ZERO + timedelta(days=SEASON_V2_DAYS - 1)`. A host test asserts `SEASON_V2_DAYS ==
    kobo_season.SEASON_DAYS` (host/tests, where `kobo_season` imports). The `world_history.py telemetry --end` default
    becomes `None`, resolved to `period_end(view["accounting_period"])` (the last day of the last booked month) until
    D-DD.103 replaces it with `READINGS_SPAN`. No literal is written to pass a guard, and no guard gets an allowance.
  - *L3.* `.ai/state/data.md` (DD3a's section) and `.ai/state/index-3.md` "Open" become the true open items: D-DD.92's
    overfill and notes (DD3b), D-DD.103 (DD4a), D-DD.104 and D-DD.97 (DD3b), and the mock kit strings (D-DD.105).
  - *L5.* One packet line names the tank's product readers: `runs/profiles.py:910-920` (frozen into lab runs) and
    `runs/operational_actions.py:76`. Nothing served moves before DD5 loads the `/2` file.
  - *L6.* Merge main into the branch, resolve `.ai/state/index-3.md` and `backend/tests/test_sc1_statements.py` by
    keeping both sides' entries, then rerun `statement_catalogue.py` and `test_sc1_statements.py` on the merged head
    (D-DD.96).
  - *DD3a fix-round order (two builder runs, one part each).* Run 1: L6 (merge main first, so the regeneration is on
    the current base), then D-DD.102 with its tests, the regeneration and the re-pins. Run 2: L2, L5, the D-DD.105
    packet line, L3, then the slice end: full scope against main, the catalogue and the packet.

- **D-DD.107 D-DD.97 lands in DD3b; DD3b splits; units and order** (W4; amends D-DD.101's placement and spec §7,
  §8.2).
  - *D-DD.97 (owner-approved 22 Nov) in DD3b, not DD3a's fix round.* DD3a at 5.75 u plus D-DD.102 is 6.0 u, and adding
    D-DD.97 would exceed W4's 6 u. D-DD.97 also belongs where its own text puts it: in DD3.3, before D-DD.92's restated
    notes, which follow the shape. DD3b applies it in its first run, with D-DD.104.
  - *Split (as D-DD.101 foresaw).* DD3b = DD3.3 (2.5) + D-DD.92 (1.0) + D-DD.97 (0.25) + D-DD.104 (0.25) = **4.0 u**,
    `task/DD3b-mini-units` kept. New **DD3c** = DD3.4 (unit roles in the readers, 2.5 u), `task/DD3c-unit-roles`, own
    discovery review. DD3c touches `sites/` readers and a migration, not the simulator, so it may run beside DD3b
    (no shared files). It merges before DD5.1 loads Kisiwa's or Mto's readings.
  - *Units.* DD3a 5.75 → **6.0 u** (D-DD.102 +0.25; the Lows are packet and merge work). DD4a 5.0 → **5.5 u** (D-DD.103
    +0.5). DD3b 6.0 → **4.0 u** and DD3c **2.5 u**. DD: 42.0 → **43.25 u** (D-DD.97 +0.25, D-DD.102 +0.25, D-DD.103
    +0.5, D-DD.104 +0.25), in **ten parts**, each at or under 6 u.
  - *Order.* DD3a (fix round) → DD4a (D-DD.90, D-DD.103, the join) ∥ DD3b runs 1-2 (D-DD.97, D-DD.104, v9, Kisiwa and Mto)
    ∥ DD3c. DD3b's D-DD.92 notes run starts once DD4a is on main, because the notes rule iterates over the whole span
    to 6 Nov 06:00. DD5 follows DD3b, DD3c and DD4b.
  - *Mid-build count.* The reviewer counted four Architect rounds inside DD3a. D-DD.104 shows one more fault, which
    the code-reality pre-flight would have found by varying one undeclared input. DD3b's pre-flight lists every
    writer default (`.get(..., <literal>)`) and its declared source before code.

---

# DD rulings, round 15 (D-DD.108 to D-DD.116): DD3c pre-flight Q1-Q12, the all-FAILED rating, DD3a's digest sweep

Architect (Claude), 2026-11-22, fresh hand-off after round 14. Read: `specs/DD-demo-data/DD3c-preflight.md` and
`DD3c-handoff.md` on `task/DD3c-unit-roles` (`f98233038`); rulings D-DD.41, .43, .44, .45, .70, .102, .107; spec §7
DD3. Checked against code on that branch: migrations `0029` (the final gate, `:196-205`), `0048` (`RENEWABLE_HOUR`,
`_functions_0048`), `0049` (calls `mini_enqueue_hour`, redefines nothing); `mini_depth/{inputs,read,store}.py`;
`analytics/assessment_worker.py:62-63` and `assessment_inputs.role_coverage`; `runs/replay_series.py:40,340`;
`structure/litres/{inputs,rules}.py`; `analytics/service.py:43-54,142` and `main.py:406-417`;
`sites/unit_roles.py`. DD3a's W6 digest sweep: `packet-DD3a.md` §"Sweep (W6)" on `task/DD3a-mini-reality`.

Two findings the pre-flight missed, both ruled below: `assessment_worker.ROLES_BY_SET` lists roles-1..4 only, so a
roles-5 set gets an empty role-coverage block in the dispatch input set (D-DD.109); and the litres split refuses every
multi-unit Site (D-DD.113). The owner is informed of all nine; none needs the owner's decision. The owner may want to
weigh in on D-DD.113's consequence (Kisiwa gets a litres split in the demo) and on D-DD.110's replay note.

- **D-DD.108 Q1, Q6, Q7, Q8 accepted as applied.**
  - *Q1.* "Exactly one set in force" counts `minigrid-roles-4` and `minigrid-roles-5` together, in Python and SQL;
    two overlapping sets of either name give no work (SQL) and the reader's existing `CONFIGURATION_MISSING` (Python).
    No new constraint: the world is built fresh (DD6), so no Site carries both. One Postgres test publishes a roles-4
    and a roles-5 set over one hour on one Site and asserts no job is enqueued and the mini-depth reader refuses.
  - *Q6.* `UnitRolesRefused(code="TEL_FOUNDATION", unit=...)`, mapped by each reader to its existing Foundation or
    configuration refusal; no new user-facing string.
  - *Q7.* Missing units' asset codes go into the existing detail or limit field; reason codes and text unchanged.
  - *Q8.* Events: union in time order; equal times in declared Foundation order (the order that also names the lead).

- **D-DD.109 Q2: migration `0074_unit_role_sets` accepted, with exact counts; one Python constant; every reach of the
  gate named with its parity test** (protected seam: the mini-depth enqueue gate).
  - *Constant.* `sites/binding_roles.py`: `MINI_DEPTH_ROLE_SETS: tuple[str, ...] = (ROLE_SET_MINIGRID_4,
    ROLE_SET_MINIGRID_5)`, comment citing this ID. Every Python gate below reads it; none names roles-4 alone.
  - *Migration.* Built in 0048's style from 0048's own texts (load 0048 as 0048 loads 0029). Upgrade:
    `_functions_0048()` with `b.role_set = 'minigrid-roles-4'` replaced by `b.role_set IN ('minigrid-roles-4',
    'minigrid-roles-5')` (count exactly 1, in `mini_enqueue_hour`) and the gate comment's "current `minigrid-roles-4`
    binding set" by "current `minigrid-roles-4` or `minigrid-roles-5` binding set" (count exactly 1);
    `RENEWABLE_HOUR` as `CREATE OR REPLACE` with `s.role_set = 'minigrid-roles-4'` replaced likewise (count exactly 1).
    Any other count raises. `mini_enqueue_accepted` and `mini_enqueue_configuration` hold no role-set text and are
    re-created unchanged inside the same body. Downgrade executes `_functions_0048()` and `RENEWABLE_HOUR` (as `CREATE
    OR REPLACE`) unchanged. No data change, no trigger change. The migration writes its own literals (migrations do not
    import live code); a test asserts they equal `MINI_DEPTH_ROLE_SETS`.
  - *Reaches (every place the gate's meaning is read).* SQL: (S1) `mini_enqueue_hour`'s final gate, reached by the
    `mini_enqueue_accepted` trigger (accepted evidence), by `mini_enqueue_configuration` (called at publish,
    `postgres_foundation_store.py:758`), and by 0049's one-time backfill (history, not re-run); (S2)
    `mini_renewable_hour`, reached by `mini_enqueue_hour`'s hour check and by both enqueue loops. Python: (P1)
    `mini_depth/store.read_hour_rows` (`role_set = :rs` becomes `role_set = ANY(:rs)` over the constant; the parameter
    becomes `role_sets`); (P2) `mini_depth/inputs.py:216,227` (the count spans both names); (P3) `mini_depth/read.py:220`
    and `:487-488` (feeder sets, hence `structure/energy/inputs.feeder_month`); (P4) `mini_depth/store.py:376-386`
    `_PV_BOUND` (hence `mini_decisions/projection` `daylight_hours`); (P5) `analytics/assessment_worker.ROLES_BY_SET`,
    hence `runs/replay_series.py:340`: today roles-1..4, so a roles-5 set gets no role-coverage rows. It becomes
    `{s: tuple(roles_for(s)) for s in sorted(SERVED_ROLE_SETS_BY_SITE_TYPE["MINIGRID"])}` (the served sets, not a
    hand list; W6). The refusal detail at `inputs.py:227` names both sets; if `statement_catalogue.py` covers it, the
    one changed line is re-hashed citing this ID and reported, nothing else may move.
  - *Parity tests (Postgres, `*_test` DB).* T1 roles-4 unchanged: on the existing 0029/0048 fixtures, the job rows
    (domain, window, cause) after upgrade equal those before, and after downgrade-upgrade; the existing 0029/0048
    tests pass untouched. T2 roles-5 one set: Kobo published under roles-5 enqueues the same job rows as under roles-4
    for one October day, from evidence and from publish. T3 both sets (D-DD.108 Q1): no job; Python refuses. T4 other
    sets: a roles-1..3 Site, a cold and an EV Site enqueue nothing, as on main. T5 renewable hour on two inverters: a
    positive `pv_available_power` on either unit makes the hour renewable; on neither, not; unbound, the 12:00 rule.
    T6 migration text: each replacement counted once, the downgrade body byte-equal to 0048's, literals equal the
    constant. T7 coverage: Kobo's dispatch input-set role coverage under roles-5 equals roles-4's after replacing the
    role-set name and UUIDs (D-DD.114's normaliser). Plant (reverted): drop roles-5 from the SQL list; T2 and T5 fail.

- **D-DD.110 Q3 and Q10 accepted; Kisiwa's replay refusal is honest output.**
  - *Q3.* The Site-figure readers call `sites/unit_roles.py` whatever the role set, as listed; one unit gives the
    unit's value byte for byte. The per-unit readers stay per unit, one two-unit test each. Plus D-DD.109 P5.
  - *Q10.* `replay_series` builds the Site series through `unit_roles`; `replay_study`/`headroom_replay` unchanged.
    Their v8 model needs refuse a two-unit Site. That refusal is honest, not a gap: v8 holds one generator and one
    inverter (§0), and a v8 replay of Kisiwa or Mto would print figures for a Site that does not exist (D-DD.70's
    reason). A v9 replay is a new capability, not a reader fix; the coordinator logs "v9 replay for multi-unit Sites"
    in `.agent/backlog-post-demo.md`. The owner may weigh in if a what-if at Kisiwa is demo-critical.

- **D-DD.111 Q4 amended: a Site state the known units decide is stated; otherwise absent, named by unit.**
  - D-DD.41's state rule is an "any" cascade, so some steps are decided whatever an absent unit holds. Per step:
    RUNNING if any unit with a state is RUNNING; else, if any unit has no state, absent (named by unit); else D-DD.41's
    cascade (STARTING if any starts, STOPPED if any is not FAILED, else FAILED).
  - *Why.* With one unit running and the other silent, the Site is running whatever the silent unit does; saying
    "absent" there drops a known fact. STARTING, STOPPED and FAILED depend on every unit, so a silent unit leaves them
    undecided. Nothing is imputed: the stated value holds for every value the absent unit could take.
  - *Builder.* `site_generator_state` in part 1's module; two tests (RUNNING + absent gives RUNNING; STOPPED + absent
    gives absent naming the unit); the one-unit identity test unchanged. Power keeps D-DD.41's rule (a sum is
    undecided while any term is absent).

- **D-DD.112 Q5 and the open point: installed and available rating are two quantities; every unit FAILED gives 0 kW
  available** (amends D-DD.41's rating sentence by naming the two).
  - *Two quantities, one figure each.* `site_installed_rating(components)`: the sum of every GENERATOR unit's
    `generator-rated-power` (a unit without exactly one gives absent, named by unit). `site_available_rating(components,
    states)`: at a step, the sum over units whose state is not FAILED; a unit with no state at the step gives absent,
    named by unit (its inclusion is undecided). `site_rating` with its optional `states` is replaced by these two, so
    no caller gets one quantity under two meanings. No reader reads a Site rating today (`generator-rated-power` is read
    only by `runs/profiles.py` and the module), so neither is wired into a reader in DD3c.
  - *All units FAILED: available rating 0 kW, not absent.* Every unit's state is known, and each says the unit gives
    no power: the evidence decides the sum, and it is zero (`Decimal("0")`, unit kW, no missing units). "Missing is
    never zero" forbids turning an unknown into 0; here nothing is unknown. D-DD.41's "absent if any unit is absent"
    is about absent values, and a FAILED state is a present value. Absent stays for: a unit with no state (undecided)
    and a Site with no GENERATOR (nothing declared). Builder: the empty-sum path returns the zero, not absent; one test
    each for all-FAILED (0, no missing), no GENERATOR (absent), one FAILED plus one silent (absent, naming the silent).

- **D-DD.113 Q9: Kisiwa's litres saying `NOT_ONE_EACH` is a gap, fixed in DD3c; `fuel_basis` checked, not changed**
  (W6: the class is "every reader of a GENERATOR unit quantity", wider than D-DD.41's list).
  - *Why a gap.* Kisiwa's generator readings and tank records exist, and D-DD.41 gives the rule (each unit burns on
    its own curve; Site litres are the sum; one tank). The refusal predates the rule; it is not a statement about the
    evidence. Left, Kisiwa would show no litres split where Kobo shows one from the same kind of data (owner: data in
    range gives output on every page, the same for every Site).
  - *Change (`structure/litres`).* `rules.py`: new `UnitFuel(unit: str, use: Callable[[datetime, datetime], SpanUse],
    curve: FuelCurve)`; `LitreInputs.use` and `.curve` are replaced by `units: tuple[UnitFuel, ...]` in declared
    Foundation order; `held` stays Site-level (any unit's power or state reading). `_piece` evaluates each unit as
    today and sums: any unit `USE_INCOMPLETE` gives that note first, then any `NO_LOAD_RATE_MISSING`; `idle` is any
    unit's. `FUEL_CURVE_MISSING` when any unit's `sfc` is None. The curve's validity window is the intersection of the
    units' windows (None if any is None). Sources list each unit's refs in unit order through `_unique`. `inputs.py`:
    the condition becomes one FUEL_TANK and at least one GENERATOR; each unit gets its own `sfc_for`/`no_load_for`
    reads and its own `_Readings(..., unit id)`; `relevant_readings` takes every unit's id. The values `"ONE_EACH"` and
    `"NOT_ONE_EACH"` are kept (pinned by 4d's tests); their comment now reads "one tank and every GENERATOR unit"
    citing this ID. No new note, no new copy.
  - *Tests.* Kobo's October litres month byte-equal to main (one unit); a two-unit fixture with different SFCs gives
    the per-unit sum; one unit without a curve gives `FUEL_CURVE_MISSING`; two tanks still give `NOT_ONE_EACH`. Plant:
    one curve applied to both units' kWh; the two-unit test fails.
  - *`analytics/service.fuel_basis` (first GENERATOR with an SFC, legacy dispatch on the ingestion listener,
    `main.py:417`).* Builder checks whether DD5's `load_world_inputs` path reaches `AssessmentService.assess_site`. If
    not, it is logged in `.agent/backlog-post-demo.md` ("fuel_basis first-match on multi-unit Sites") and untouched.
    If it does, the builder stops and reports to the Architect before part 4.
  - `mini_decisions/projection.py:85` is fixed by D-DD.109 P4, as the pre-flight says.

- **D-DD.114 Q11 accepted, with the parity defined.** Only `conversions/world/KOBO-001-bindings.json` moves to roles-5
  (and its three test pins); the demo-config and w402 conversions stay roles-4. The parity run publishes Kobo under
  roles-4 in one fresh scratch state and under roles-5 in another (never both sets on one Site; D-DD.108). Compared,
  for one October day (the month for litres): mini-depth revision values (figures, states, reasons, limits), the
  dispatch assessment (interval classes, limits, input-set coverage), the fuel balance, and the litres month. Each is
  serialised with `sort_keys`, UUIDs replaced by `uuid-<n>` in first-appearance order and the role-set name by
  `<role-set>` (D-DD.45's normaliser); then byte-equal. A stored digest is compared directly only if it embeds neither
  ids nor the role-set name; the packet lists which digests were compared which way. Any other difference stops for
  the Architect.

- **D-DD.115 DD3a's W6 digest sweep: `generator`, `site.code`, mini-grid `months`, EV `day_classes`/`families` stay
  in the scope digest; no re-draw before the demo** (coordinator item; D-DD.102's class, for the other keys).
  - *The class D-DD.102 fixed* is a digest input that is a world fact expected to be corrected (kit figures as data
    sheets arrive), so a truer world re-seeds history. These four are not that: `generator` is the generator's version
    constant, meant to re-seed when it changes; `site.code` is the Site's fixed identity (beside the key `site.site`);
    `months` is the fixed four-month calendar (D-DD.2); `day_classes`/`families` are fixed global shape tables. Each
    changes only by a deliberate design change that re-draws history anyway. None is wrong today, and removing any
    re-draws July-September at every affected Site for no change in any figure's meaning.
  - *Later.* The general form (each scope's digest covers exactly the keys its rules read, declared beside the rules,
    as D-DD.102 did for `physical`) goes to `.agent/backlog-post-demo.md` with the four keys named, for the first slice
    after the demo that re-draws history for its own reason. A digest change is a re-draw and needs that reason.

- **D-DD.116 Q12 and units: DD3c 2.5 → 3.25 u in five parts; DD 43.25 → 44.0 u** (W4; D-DD.44's 3 u stop, ruled here).
  - +0.25 u: the builder's survey (five readers, four per-unit checks, D-DD.109 P5 and T1-T7). +0.5 u: D-DD.113's
    litres per unit. D-DD.111 and D-DD.112 are small edits inside part 1. DD3c stays under W4's 6 u.
  - *Parts.* (1) `unit_roles.py` (done) plus D-DD.111, D-DD.112; (2) migration 0074, `MINI_DEPTH_ROLE_SETS`, the
    mini_depth and structure/energy readers, `ROLES_BY_SET`, T1-T7; (3) dispatch_v3, verification, replay_series,
    fuel_balance and the per-unit checks; (4) litres per unit (D-DD.113) and the `fuel_basis` check; (5) Kobo to
    roles-5 and D-DD.114's parity.
  - DD: 43.25 → **44.0 u** in ten parts, each at or under 6 u. Order unchanged (D-DD.107).

---

# DD rulings, round 16 (D-DD.117 onward): the lane-wide pre-flight for every remaining part

Architect (Claude, the kept DD lane Architect), 2026-11-22, under the owner's DD strategy
(`owner/owner-dd-strategy-2026-11-22.md`; `.ai/ROLE_CONFIG.md` "DD strategy"). One round for DD3c parts 3-5, DD4a's
remaining runs, DD4b, DD3b, DD5 and DD6. Checked read-only against main `965fc4d17`, `task/DD3c-unit-roles`
(`09bd3ba99`), `task/DD4-cold-ev-reality` (`a5c7e9515`), `task/DD4b-ev-measured` (`8d519ef49`) and `M` by key.
Owner words read: `owner/owner-demo-data-answers-2026-11-22.md` (D-DD.92: "Revisit a plant figure", then D-DD.97
"Approve 18:00 peak"; D-DD.98: "Readings stand"). The sorted question list, defaults, build plan, sizes and reach
sets are in `preflight-remaining.md`; this file holds the rulings. The owner is informed of all of them; the
owner-level questions are in `preflight-remaining.md` §2, each with its default applied.

## DD3c, parts 3 to 5

- **D-DD.117 Fuel balance on a multi-unit Site: the lead unit names the window; every unit burns; no schema change**
  (model; W6 class of D-DD.113: every reader of a GENERATOR unit quantity).
  - *Code.* `fuel_balance/service.py:75-79` refuses any Site without exactly one GENERATOR (`ASSETS_UNSUPPORTED`);
    `fuel_balance_window.generator_asset_id` (0055) and the unexplained-fuel finding's mini-grid key (0056:31) hold
    one generator id.
  - *Rule.* One FUEL_TANK and at least one GENERATOR. The window's `generator_asset_id` is the lead unit
    (`unit_roles.lead_unit`, D-DD.43: the first GENERATOR in declared Foundation order); at a one-unit Site that is the
    one unit, so every stored row is unchanged. `rules.assess` takes `units: tuple[(asset_id, sfc, no_load), ...]`:
    model-implied litres are the sum of each unit's burn on its own SFC and no-load rate (D-DD.113's shape); a unit
    without an SFC gives the existing missing-SFC limitation. `relevant_readings` takes every unit's id.
    `input_sha256` adds `"generator_asset_ids"` (all units, declared order) **only when there is more than one unit**,
    and `terms` gains a `units` list only then, so one-unit digests and terms are byte-identical.
  - *Tests.* Kobo one night: row and digest byte-equal to main. Two-unit fixture with different SFCs: implied litres
    = per-unit sum; lead id in the column. Plant (reverted): one SFC for both units; the two-unit test fails.
  - *Why no column.* The window is a tank's balance; the generator id only keys the finding to an asset an operator
    acts on. The lead unit carries the Site's policy, so a finding raised on it points at the right control. A list
    column would migrate two tables for no served difference.

- **D-DD.118 DD3c parts 3 to 5: the pre-flight defaults (Q3, Q10, Q11) stand as ruled by D-DD.110 and D-DD.114;
  `fuel_basis` resolved.** `dispatch_v3` pv sums the pv units through `unit_roles.site_power` (no
  `MULTIPLE_BINDINGS` at a Site whose units are each bound once); `minimum-runtime` reads `lead_policy`;
  `verification*` reads the three single-power roles and `generator_state` through `unit_roles`, the fuel comparison
  per unit summed. `analytics/service.fuel_basis` is reached only through `IngestionService`'s completed listener
  (`main.py:418`, central ingestion); DD5 loads through `BulkEvidenceLoad`, which does not call it, so D-DD.113's
  first branch holds: the coordinator logs "fuel_basis first-match on multi-unit Sites" in
  `.agent/backlog-post-demo.md`, untouched. The DD3c builder confirms with one grep and records it in the packet.

## DD4a, the remaining runs

- **D-DD.119 The cold writer's books are built in process from the same functions as the exported books, and checked
  against them byte for byte** (BLOCKER for the writer run: `books_for` is mini-grid only, `telemetry.py:825-860`;
  `build_telemetry` would `KeyError` on a cold Site).
  - `world/telemetry_cold.py` gains `cold_books_for(view, history, records) -> dict[code, books]`, called by
    `tools/world_history.py telemetry` beside `books_for`:
    - `ledger`: the rows of the `ExportFile` whose kind is `profile.cold-storage-ledger` returned by
      `exports_cold.build_cold_exports(view, history, records, tenant)` for each COLD_CHAIN tenant (`records` from the
      same DS1b function the `records` command runs);
    - `cooling`, `seasons`, `day_classes`: the view's `history.families.cooling`, `history.seasons`,
      `history.day_classes`;
    - `efficiency` (`f_m`): for each history month, the Site's `history.sites[<tenant>/<site>].actual.kwh` rule's
      `cooling` arguments, read by `world/history.py`'s own rule parser (no second parser); for the accounting period,
      `Fraction(period.actual.kwh) / Fraction(period.actual.kwh_model)` (Kirinyaga 5000/4030 = 500/403); for a month
      after it, the accounting period's value (D-DD.103's `rate_of` class). A Site with no `kwh` rule and no
      `kwh_model` has no entry (f = 1). Test: Kirinyaga's table is {07: 21/20, 08: 11/10, 09: 117/100, 10: 500/403,
      11: 500/403}; Mwea and Thika empty.
    - `events`: D-DD.120.
  - *Check.* The CLI renders the in-process ledger rows with the ledger profile and compares them with
    `<books>/<file_name>` byte for byte; a difference refuses `TEL_BOOKS <file>` (exit 3). So the readings and the
    books the product admits come from one ledger.

- **D-DD.120 Thika's events are a module table with a manifest parity test** (D-DD.51's class; `M`'s incidents are
  outside the view by design, `view.py:3-4`). `telemetry_cold.STORY_EVENTS = {"COLD-THIKA": ({"kind": "GRID_LOSS",
  "at": "2026-10-06T19:11:00+03:00", "source": "incident.grid_outage"}, {"kind": "GENERATOR_FAILURE", "at":
  "2026-10-06T19:11:00+03:00", "source": "incident.backup"}, {"kind": "GENERATOR_HAND_START", "at":
  "2026-10-06T20:22:00+03:00", "source": "incident.backup (D-DD.89)"}, {"kind": "GRID_RESTORE", "at":
  "2026-10-06T22:00:00+03:00", "source": "Assumed (spec §4.4): M states no restore"})}`. The parity test reads `M`
  after D-DD.89's commit and asserts the three `M` instants (`grid_outage` "from 19:11"; `backup`'s "failed to start
  19:11:10" minute and "started by hand 20:22"). Mwea and Kirinyaga have no entry.

- **D-DD.121 C-DD6 is written in DD4a and goes live by vertical; each clause not yet producible is pending with its
  unit** (amends §8.1 "Live from").
  - The judge (`check_failures_at_instant`) takes readings rows, as D-DD.55's judges do; its SQL fetch is the
    clone's. DD4a: Thika's clauses (GEN-CR-01 FAILED at 19:11 on its own device, B-1031 above 5 °C > 15 min,
    B-1034 below 12 °C) live, tested on the writer's Thika rows in `test_dd4_thika_incident.py`. DD4b: Kasarani CH-K2
    and Ruiru CH-R7 c2. DD3b: Kisiwa GEN-KS-01 (at 18:40, D-DD.126) and Mto INV-MT-02. On the clone it fails until
    DD5 loads. `STUBS["C-DD6"]` becomes the per-clause pending list.

- **D-DD.122 DD4a's writer run: the three rooms over `READINGS_SPAN`, out of tree, measured.** Output
  `/opt/assetecon/worlds/DD4a-<commit12>/` (never the tree). The packet records seconds and bytes per room and per
  Site-day, the five 5-minute readings above 5 °C at Thika, and each D-DD.89 expected figure reproduced (or the stop).
  C-DD11's two-process check gains Mwea for 1-2 Jul. Mwea, Kirinyaga and Thika must each end at 06:00 on 6 Nov.

## DD4b

- **D-DD.123 DD4b rejoins on DD4a's frame; DD4.3's spare and rotation are rebuilt to D-DD.98** (builder default made
  exact; the branch predates the join and D-DD.98).
  - *Order.* After DD4a merges: merge main into `task/DD4b-ev-measured` first. `telemetry.VERTICAL_PACKS` gains
    `"ev-charger": ("ev-charger", 1)`; `_vertical` picks the run class from one table `VERTICAL_RUNS = {"cold-thermal":
    ColdSiteRun, "ev-charger": EvSiteRun}` (no second branch). `EvSiteRun.day_records` returns D-DD.91's seven-element
    rows; its event object adds `session_id` and `connector_id` only where the pack gives them.
  - *Rebuild.* The ninth night spare of `22275cdaa` is replaced by D-DD.98's daytime spare (`EV-KAS-S01`, 10:00
    arrival on 2, 3, 4 Nov, unplugged by the rotation rule, departs 05:00 with 150.000 kWh) and the rotation rule with
    `ROTATION_MINUTES = 5`; D-DD.98's Embakasi/Ruiru parity golden from `8d519ef49`.
  - *Measured hooks.* Each run class exposes `measured_months() -> {month: dict}` with its vertical's fixed key set
    (D-DD.99); `EvSiteRun` also `departures()`. `measured_for` asks every run for its months, so mini-grid bytes stay
    DD3a's (parity test). The frame writes `departures` only for a tenant with EV Sites.
  - *One source for bands and prices.* Band hours, price classes and the demand rate come from the Site's
    `world/tariffs.py` TARIFF_SCHEDULE records (the records the product admits), never from literals; the cold bill's
    price is the view's `prices.electricity_usd_per_kwh`.

- **D-DD.124 DD4.4's open details.**
  - *Cold electricity bill profile* `cold-electricity-bill-illustrative`: profile, sample (a slice of emulated rows,
    D-DD.65a) and expected file, as §5.6's table. Account `<CODE>-UTIL` (the EV invoice's form), tariff code
    `T-GRID-COLD` (one illustrative grid tariff at 0.20, declared once in `exports_measured.py` with a parity test
    against `M` `prices.electricity_usd_per_kwh`), From the month's first day, To the next month's first day
    (exclusive, as the EV sample).
  - *Statements* (§5.4): cold `revenue` = Σ the invoicing file's CHARGE rows, `energy_cost` = Σ bill rows; EV has no
    revenue record (a captive depot, `M` holds none), so the EV statement omits `revenue` (schema
    `assetops.world-statements/1` admits it absent for EV_DEPOT only; missing is never zero) and `energy_cost` = Σ
    invoice rows. Neither is recorded by WK until Q11 sets `snapshot_months` (D-DD.28).
  - *`meter_billed`* is `<slug>.meter-billed.json` (`assetops.world-meter-billed/1`; rows `site_code`, `month`,
    `leaf`, `metered`, `manifest`), written by `exports --telemetry`, information only, never admitted.
  - *C-DD5, C-DD7, C-DD20* follow D-DD.55: judges on rows, tested on the emulated rows in `simulator/tests/world/`
    and on hand rows in `backend/tests/test_dd4_check.py` (no database); the SQL fetch fails on the clone until DD5.
    C-DD5's cadence table is the checker's own (5-minute means; states and events on change).

- **D-DD.125 The EV capacity stage bounds buses by charger as well as by energy; Kasarani's November story is
  restated from the readings** (model; the owner chose "Readings stand" for D-DD.98, and the owner's rule is "one
  figure, loyal to the operating world": D-DD.98's structure fault is fixed in the model now, not left as a finding).
  - `structure/rows_ev_depot.py` and `M` `structures`: new node `buses_full_by_charger = chargers_in_service ×
    floor(charger_kw × window_h / kwh_per_bus_night)`; `buses_short_per_night = max(ceil(max(required_kwh_night −
    supplied_kwh_night, 0) / kwh_per_bus_night), max(buses − buses_full_by_charger, 0))`. `charger_kw` is the charger's
    rating, which bounds every connector on it (each depot's connectors equal its chargers: 60/60, 50/50, 60/60), so no
    connector leaf is added. Registry pins and `home_categories` row (Protect P1) follow.
  - *Parity.* Every figure in `backend/tests/golden/6h_parity.json` and every `M` option figure is unchanged except
    Kasarani's from 1 Nov (the bound does not bind elsewhere); the test lists the moved ones.
  - *Restated in `M`* (one commit after DD4.4's measured departures, rev bump, D-DD.30 chain): Kasarani's November
    `departures_missed`, penalties, the stopgap's covered bus-nights, and every `{fig:...}` they feed, from the
    departure log (short rows less spare rows met). D-DD.98 projects about 7 missed and about 840.00 against 2 and
    240.00. A figure that does not follow the readings stops for the Architect.
  - New part **DD4.5** (1.0 u) in DD4b, after DD4.4.

## DD3b

- **D-DD.126 Kisiwa's failure is at 18:40, the instant `M`'s operations record; 19:10 is when it was reported. The
  August outage is in the world too** (BLOCKER; amends spec §A table, §4.2 "Unit failures", C-DD6, C-DD20).
  - `M` `operations` `kis-gen1-2026-10-30.at` is 18:40; 19:10 is the O&M `occurrence.reported` (the SLA clock).
    Physics follows the failure; the SLA reads the report. GEN-KS-01 `UNIT_FAIL` at 2026-10-30T18:40+03:00, no restore.
  - `kis-gen1-2026-08-14` (19:20, restored 17 Aug 11:00) is an outage inside the span. Leaving it out would show a
    running unit `M` records as out. `UNIT_FAIL` 2026-08-14T19:20+03:00 and `UNIT_RESTORE` 2026-08-17T11:00+03:00.
  - Mto `INV-MT-02` `UNIT_FAIL` 2026-10-28T11:02+03:00 (operations agree), no restore.
  - The writer reads these from a module table `UNIT_EVENTS` with a parity test against `M` `operations` (D-DD.51).
  - C-DD20 (Kisiwa): unserved evening energy after 30 Oct 18:40, and none from 17 Aug 11:00 to 30 Oct 18:40; the
    August days are printed as information (whether one 60 kW set carries the evening is the plant's answer).

- **D-DD.127 v9 adds a unit lifecycle in a new spec version; v1 to v8 are untouched** (model; protected seam: the
  pack's lifecycle). `MINI_GRID_V9_MODEL` carries its own lifecycle table: GENERATOR (STOPPED | STARTING | RUNNING) →
  FAILED on `UNIT_FAIL`, FAILED → STOPPED on `UNIT_RESTORE`; INVERTER {AVAILABLE, FAILED} with the same two forcings.
  `UNIT_FAIL`/`UNIT_RESTORE` are POINT forcings whose value is the component id, indexed by step like every forcing
  (D-DD.75). A unit failing while RUNNING stops at that step (§4.3). With one generator and one inverter, v9 runs v8's
  code path (a one-unit fast path), so C-DD19's parity is by construction and by test. v8's FAILED-initial rule is
  unchanged. `host/execution_adapter.py` `EXECUTABLE_MODELS` gains v9 only if a host test needs it (default: not
  registered; the writer drives the pack directly).

- **D-DD.128 Kisiwa's and Mto's kit is completed in the `/2` and `/1` files; the stale tank ratings are corrected**
  (default made exact; W6: every unit property §4.2 and §4.3 read).
  - Per generator unit: `generator-no-load-fuel-rate` 0.08 L/h per kW of `generator-rated-power` (Kisiwa 4.8, Mto
    2.4), `generator-minimum-load` 30 %, and per Site `battery-charge-taper-start` 95 %; each with its `-basis`
    GENERIC_DEFAULT, source SITE, version 1 (spec §4.2, owner 7 Nov).
  - `pv-array-share` per inverter = its `inverter-ac-limit` / Σ the Site's limits (Mto 1/2 each; Kisiwa's one
    inverter 1), basis "Assumed: array split in proportion to inverter rating" (`M` `physical.inverters` gives the
    ratings only).
  - Each FUEL_TANK component's `rating` equals its `tank-capacity` (5000, 1000, 2500 L): the 400 L is the template
    placeholder D-DD.76 removed from the property.

- **D-DD.129 The writer runs units: v8 where a Site has one of each, v9 otherwise; every hidden default is declared or
  refused** (D-DD.107's last bullet, done here).
  - `supported()`: one BATTERY, one FUEL_TANK, at least one GENERATOR and one INVERTER. GENERATOR and INVERTER roles
    are PER_ASSET, bound per unit as `feeder_demand` is. The pack per Site: v8 with exactly one of each (Kobo, also
    after DD3c moves it to roles-5: D-DD.21), else v9. The ledger burns each unit on its own curve and sums.
  - `NEEDS` rows gain `per_unit`; policy rows are read from the lead unit only (`TEL_FOUNDATION` otherwise, D-DD.43).
    C-DD21 keeps Kobo v8 and adds one v9 row check on Kisiwa.
  - *Sun.* The season v2 calendar applies only at the Sites in `SEASON_V2_SUN_SITES = ("KOBO-001",)` (spec §4.2 and
    D-DD.77 say so; `_sun` applies it to every Site today, a fault). Test: Kisiwa on 15 Sep uses clear × weight.
  - *Defaults removed* (each becomes a refusal, or a declared value): `books.get("sun_weights", ...)` and
    `books.get("fuel_notes", [])` become required keys; `expenses.get(slug, "")` refuses `TEL_BOOKS` for a mini-grid
    tenant with no expenses file; `interval_measurement(...) or Fraction(0)` and `or "STOPPED"` refuse `TEL_PACK`
    naming the unit and step; a state channel with an empty map refuses `TEL_BINDING`; a Site absent from the bindings
    is written as a `not_written` manifest line, not skipped. `DEFAULT_DAY_WEIGHTS` moves into the one test using it.
    Kept with their rulings: `TANK_START_FRACTION`, `DRAW_MINUTE`, `CRITICAL_ORDER`, generator initial OFF,
    `unexplained_l | 0` (`M` factor_map). `exports.py` `CUSTOMERS = 40`: the builder reports its source in the packet;
    unchanged in DD3b.
  - D-DD.97's shape and D-DD.104's warm-up land in the first run (the warm-up reads the lead unit's stop threshold).

- **D-DD.130 Purchases and consumption are separate in the books: the expense file follows the notes file**
  (completes D-DD.92; amends §4.2 "Fuel" wording and D-DD.32's `EMU_FUEL`).
  - `exports.py` reads `config/world/fuel-notes.json` (D-DD.92's schema) for every mini-grid Site in it; `_notes`'s
    cycle stays only for a Site not in the file (none after DD3b; the test asserts all three are listed). The expense
    rows are the notes: litres and amount = litres × the Site's diesel price. `EMU_FUEL` becomes Σ expense amounts =
    Σ note litres × price, per Site-month.
  - The books carry no consumption figure. Consumption is the readings' (D-DD.18), served by the product's fuel
    balance and litres split. C-DD4's node clause drops mini-grid `litres` and `fuel cost` (now purchases, judged by
    `EMU_FUEL` and C-DD8's balance); the other mini-grid nodes stay judged.
  - `history.json`'s mini-grid `necessary_l`/`candidate_l` remain history generator leaves (D-DD.18 already refuses
    to serve that split); `unexplained_l` stays the declared draw's input.
  - The expense category word is the layout's `Diesel`; §4.2's "category FUEL" is corrected.

- **D-DD.131 The fuel leaves of `M` are restated from the notes run, each by its own stated rule; nothing is a
  remainder** (the leaf-by-leaf list D-DD.92 deferred; one `M` commit after the notes run, rev bump).
  - A tool step `tools/dd3_pure_run.py --leaves --site CODE` prints the table below from the notes run; the builder
    writes the values into `M` and a test asserts `M` equals the tool's output (D-DD.93: a literal is the regenerated
    value).
  - Per Site (Kobo, Kisiwa, Mto), October `period.actual`: `diesel_l` = burned + declared draw (whole litres,
    half-even); `necessary_l`, `candidate_l` = the pure run's split (the writer's stand-in, labelled in `M` "projected
    from the pure run; the served figure is the product's"); `unexplained_l` unchanged; `diesel_cost` = `diesel_l` ×
    price; `contribution` and `variance` by `M`'s own identities.
  - Bridge: each fuel line keeps its stated basis formula on the restated leaves (CANDIDATE_RUNNING =
    −candidate × price; EVENING_LOAD_GROWTH and Kisiwa's SOLAR_SHORTFALL = −(necessary − plan necessary) × price;
    UNEXPLAINED_RESIDUAL = −unexplained × price). If the bridge does not close against the restated variance under
    the manifest check, stop for the Architect.
  - `fuel_balance`: `opening_dip_l`, `closing_dip_l` = the tank readings at 1 Oct 00:00 and 1 Nov 00:00 (whole
    litres); `deliveries_l` = Σ October notes; `consumed_l` = opening + deliveries − closing; `model_implied_l` =
    burned; `residual_l` = consumed − implied.
  - `findings_expected`: GENERATOR_SUPPORT_CANDIDATE `days` = October days with a positive stand-in, exposure
    `[0, candidate_l]` and `[0, × price]`; UNEXPLAINED_FUEL unchanged. Portfolio totals, `derived-values.json`,
    `missing-records.json` and the mock's generated fixtures by the D-DD.30 chain; `worked-portfolios.md:74` cites the
    record (D-DD.94). July-September `M` history stays (D-DD.130).
  - The packet lists every leaf old → new, grouped by Site. Owner informed (Kobo's story is the smaller one, as
    approved with D-DD.97).

- **D-DD.132 The pure-run checks run without a database.** `tools/dd_check.py --pure DIR` (the pure run's readings and
  `measured.json`) judges C-DD8 (tank within [0, capacity]; Kobo's October balance; Kisiwa zero candidate minutes),
  C-DD17's pure part and C-DD20's Kisiwa and Mto clauses; `--database-url` is then not required. Same judges as on
  the clone (D-DD.55).

## DD6

- **D-DD.133 C8 passes when every check passes or is pending with its closing unit; a stub fails** (BLOCKER:
  `dd_check` fails every non-live result, `dd_check.py:521,765`; §10 Q6 needs C8 to pass on DD6's first build).
  - A result is PENDING when every failing line names its closing unit (Q11, Q12, IA-P3, the unit of D-DD.137). C8 =
    no FAIL; PENDING lines are listed in the world check output. A stub (no live code) is a FAIL: by DD6 none is left.
  - C8 runs `python tools/dd_check.py --database-url <clone> --json --world-manifest <path>` as a `world.run_step`
    subprocess, before the clone is dropped (the ASGI client mutates `os.environ`, `dd_check.py:150-158`, so it stays
    in the child). Exit code = C8's state.
  - C-DD15: `_rung` writes `seconds` and `cap_seconds` into the world manifest; dd_check reads them by
    `--world-manifest`. C-DD17's served part goes live in DD6.1 (the fuel-balance read through the ASGI client).
    C-DD10 judges Lakeside; Harvest Cold and Metro Bus are pending Q11 (D-DD.11).

- **D-DD.134 WK: walk definition `/2`, statements placed by the build, one walk database for three tenants.**
  - `assetops.walk-definition/2` beside `/1`: `statements` may be `[]`, `expect` may be null, a statement carries
    `fuel_cost` or `energy_cost`; the file is `walk-layer4-v2-<slug>.json`; `world` must equal the world
    definition's.
  - `tools/world.py` copies each `<slug>.statements.json` into `inputs/<digest>/<slug>/statements/` (in the inputs
    digest), and the walk manifest records the path. `prepare` records a tenant's statements only when its
    `snapshot_months` is non-empty (D-DD.28), `--as` the tenant's finance lead (DD1's email rule). Cold and EV
    statements are therefore not recorded in DD; `energy_cost` recording is Q11's.
  - Snapshot, W4, W7 and S2 count only tenants and months in `snapshot_months`; a skipped step is recorded
    `{"step", "skipped": true}`.
  - One walk database and label hold the three tenants. `serve --tenant <slug>` sets `ASSETOPS_TENANT_SLUG` for the
    child; a serve whose recorded tenant differs is stopped by PID first. Ports 8991/5491; 8990, 5490 and the owner's
    walk stay protected.

- **D-DD.135 `demo_workflow`'s items: DD6 creates what the product's commands allow, as the people the product
  permits, at story time; the rest is listed pending** (model, with an owner-level question: `preflight-remaining.md`
  §2 O1, O2).
  - *Code.* `action.agree` and `decision.choose` are executive-only (`accounts/permissions.py:64,74`); `M` names Site
    managers and finance leads. `record_action` refuses a due date before the wall clock (`agreed.py:46,197`): seven
    of nine due dates (6-20 Nov) are before 22 Nov. `prepare_decision` needs a lever and period that items do not
    carry. The Decisions and Actions pages read the estate portfolio and the S6 action store, not 6a or 3C2 rows
    (`frontend/src/estate/homeLists.tsx:319-323`, `estate/composition.py:43`).
  - *Rule.* The product's permissions win over `M`'s naming: an act the product reserves to the executive is run as
    the tenant's executive, and `M`'s `created_by`/`chosen_by` are corrected to the person who may perform it (the
    manager is kept as `proposed_by` where `M` has the field). Due dates are judged against the world's story time,
    `M` `snapshot.as_of` (2026-11-06T06:00+03:00), not the wall clock: that needs a product clock under the world
    environment, which is not on main. Until it is, DD6 lists every item "pending: story clock (D-DD.137)" and the
    Decisions, Actions and Results cells of C-DD9 are PENDING with that unit and with "Decisions/Actions pages read 6a
    and 3C2 rows (IA-P lane)".
  - *Default if the owner does not answer:* the pending listing above; DD6 is complete without the items.

- **D-DD.136 DD6.3 tooling.** Keep-awake on this Linux host is `systemd-inhibit --what=sleep:idle` around the build
  (`tools/keep-awake-during-tests.ps1` is Windows-only). `--cap-seconds 28800` (the flag exists, default 3600).
  Evidence `/opt/assetecon/evidence/DD/<UTC date>-<commit12>/`, created by the build step. The ten clarity notes are
  `specs/DDR-rehearsal/packet.md` §"Where the runbook was unclear" 1-10, applied identically to both runbook copies
  (`Docs/engineering/operator-deep-dive-runbook.md`, `specs/ON1-operator-tenant/runbook.md`), then
  `test_ddr_rehearsal_check.py`.

- **D-DD.137 The story clock is a queued unit, outside DD's size, built only on the owner's yes** (owner-level O1).
  `WK-SC` (2.0 u): one product clock that reads `ASSETOPS_STORY_NOW` under `world.env` only (prepare and serve),
  every command and read that takes `system_clock` through it, a guard that it is unset outside world databases; then
  `prepare` creates `demo_workflow`'s items per D-DD.135. If the owner says no, the items stay pending and the served
  demo shows no decisions or actions from `demo_workflow`.

## DD5

- **D-DD.138 World cold and EV bindings carry v4 channel metadata; EV depots get one closed world table**
  (BLOCKER, model; protected seam `contracts/` and the binding service).
  - *Code.* `binding_service.py:712` publishes `v4_metadata=origin != "CONVERSION"`, so every world conversion
    (`onboard_operator apply --bindings`, D-DD.36) publishes without it and `_decide_v4` rejects each cold or EV
    envelope `MAPPING_INCOMPATIBLE` (`evidence/ledger.py:424-431`). `V4_EV_CHANNEL_MAPPINGS`
    (`source_envelope_v4.py:689-693`) is the lab's closed table (`c1`, `c2`, `site-meter`); the world's depots
    declare `ch-<charger>-c<n>-connector-*` and `site-meter-1` (D-DD.38).
  - *Rule.* A conversion publishes v4 metadata when its role set's channels are v4 (`cold-roles-1`, `ev-roles-1`),
    from the closed table for that role set; mini-grid role sets keep today's behaviour (v3; D-DD.139). New closed
    table `V4_WORLD_EV_CHANNEL_MAPPINGS`, built by `_ev_connector(prefix)` for exactly the prefixes
    `ch-<charger code lower>-c<n>` a depot's `/2` file declares, plus `("site-meter-1", "import")`: generated by one
    function from the Foundation, so it stays closed per Site and the lab table is byte-identical. The cold world
    devices are checked against the cold closed table first; a mismatch is the same fix, not a rename.
  - *Tests.* A conversion-published COLD-THIKA set accepts one v4 meter and one event envelope; EV-KAS likewise for a
    connector energy and the Site import; Kobo's roles-4 conversion digest is byte-equal to main; the lab EV table
    is unchanged (identity).

- **D-DD.139 Sealing: mini-grid rows as v3, cold and EV as v4; batches of at most 256; one sequence per source over
  the span** (BLOCKER for the ruling text of §4.6; amends §4.6).
  - Envelopes: mini-grid `SourceEnvelopeV3` (roles-4/5 are mixed sets, `binding_service.py:236-241`); cold and EV
    `SourceEnvelopeV4`. One pure backend builder `evidence/world_seal.py` `seal_readings(...)`, mirroring the gateway's
    `_envelope_v4`/`seal_batch_v2`, with a parity test against the gateway's output for one row of each kind.
  - Fields: `device_id` = the row's `source_id` (D-DD.72); envelope `source_id` = the source UUID from the binding
    set's snapshot download (`binding_service.py:1143`), which also gives foundation version and `valid_from`,
    binding set id and version and `snapshot_sha256`; `published_at` = source time; quality GOOD; STATE_AT_INSTANT
    when `start` = `end`, INTERVAL_MEAN otherwise, INTERVAL_DELTA for EV connector energy; times in UTC `Z`.
  - Batches: per (Site, source, local day), split into consecutive batches of at most `MAX_BATCH_ENVELOPES` (256) in
    reading order, `<SITE>.<source>.<day>.<n>.batch.json`; `sequence_epoch` "1" and one sequence per source running
    over the whole span (no message-id collision across days).
  - Ids: D-DD.91's cold ids; `cold_correlation_id` moves from `host/cold_publication.py` to `contracts/` beside
    `cold_event_id` (host re-exports it). EV: a connector session's `correlation_id` is its `session_id`
    (`source_envelope_v4.py` ~336), formed at sealing by a new `ev_session_id(foundation_digest, connector device,
    session ordinal)` in `contracts/`; DD4b's writer gives EV measurement rows inside a session a `"session":
    {"ordinal", "connector_id"}` object (mini-grid and cold rows have none, so their bytes are unchanged).
  - Resolution: `PostgresEvidenceLedger.site_scope(slug, code)` (not the FastAPI `registered_site_scope`); an unknown
    Site, gateway or source refuses `WORLD_TELEMETRY_UNRESOLVED`, **exit 2** (the module's refusal code; 3 is
    DATABASE_ERROR).

- **D-DD.140 The inputs folder: telemetry staged without manifests; `sealed/` beside, outside the digest**
  (model; amends §4.6 and DD5.3).
  - `L1.telemetry` copies only `*.readings.json` and `measured.json` into `inputs/<digest>/<slug>/telemetry/`; the
    readings manifests (they hold `private_parameters`) stay with the generator's output. F is
    `inputs/<digest>/site-inputs.json`. Both are in the inputs digest.
  - `load_world_inputs` accepts `staged/`, `sealed/` and `disorder/`; it writes `sealed/` once, and on a re-run
    re-seals and refuses if the bytes differ. `sealed/` is not in the digest (it is a function of the inputs and the
    database ids). C6 globs `*/sealed/*.batch.json`.
  - `read_definition` dispatches on format; for `/2`, `telemetry.span` must equal `READINGS_SPAN`. The `/1` key set
    and `batches == 0` guard (`world.py:739`) are unchanged for `/1`. C5 runs the two parity files as two
    `harness_run` calls.
  - Bulk lift: `BULK_SITE_TYPE_UNPROVEN` stays in `BULK_REFUSALS` and the guard at `postgres_evidence_ledger.py:688`
    stays (for any future type); `test_ds3_bulk_load_postgres.py`'s `case_coldchain_site` becomes an
    unknown-type case. The parity test also asserts that enqueue (`_enqueue_admitted`, v3 and COLDCHAIN only) is the
    same on both paths.

- **D-DD.141 Disorder is planted in loader-legal files, one directory per test** (model; amends §5.5).
  - `<slug>/disorder/<ID>/` holds loader-legal names (`load_emulated_exports._files`); each `L1.disorder:<ID>` step
    runs `load_emulated_exports --dir` on it with `fail=False` and records the exit, compared with §5.5's expected
    exit.
  - TENANT-1: a Harvest Cold canonical `customer_invoicing.json` whose batch `tenant_code` is `lakeside-power`
    (CSV rows carry no tenant), expected exit 3 and `INTAKE_TENANT_MISMATCH`; C-DD13 then drops its pending line
    (D-DD.40).
  - OOO-1: the late file repeats the 26 Oct note's `source_record_id` with `recorded` 2026-11-04 (a second revision
    by `row_digest`).
  - MAP-1: the meter register writer is `world/meter_register.py` (METER_ASSIGNMENT, `effective_from`; §5.5's
    `valid_from` corrected), six Mto meters in code order from 2026-10-03, its kWh taken from `M` by a module table
    with a parity test (D-DD.51); staged JSON.
  - FX-1 and LATE-SETTLE-1 are planted by `exports.py` outside the history months; goldens re-pin (D-DD.93).
  - CLOCK-1 stays "planted, not built" (D-DD.25); the manifest's "corrected; flagged" is listed in the packet for the
    design-doc alignment pass.

- **D-DD.142 Units and parts** (W4; the pre-flight's sizes, `preflight-remaining.md` §3).
  - DD3b 4.0 → **5.75 u** in three parts: DD3b1 v9 pack (D-DD.127) and its parity, 2.0; DD3b2 writer units,
    Kisiwa/Mto kit and pure runs, D-DD.97, D-DD.104, D-DD.126, D-DD.128, D-DD.129, D-DD.132, 2.0; DD3b3 notes and
    leaves (D-DD.92, D-DD.130, D-DD.131), 1.75 (after DD4a on main).
  - DD4a stays 5.5 u (D-DD.119 to D-DD.122 are the remaining runs already counted).
  - DD4b 3.75 → **4.75 u** (DD4.5, D-DD.125, +1.0; D-DD.123's rejoin is inside DD4.3's count).
  - DD5 5.25 → **7.25 u**, split: **DD5a** = DD5.1 with D-DD.138 to D-DD.140, 3.5 u (`task/DD5a-seal`); **DD5b** =
    DD5.2 and DD5.3 with D-DD.141, 3.75 u (`task/DD5b-ladder`). Each at or under 6 u.
  - DD6 3.75 → **4.75 u** (D-DD.133 +0.25, D-DD.134 +0.75).
  - DD: 44.0 → **49.75 u** in eleven slices. `WK-SC` (D-DD.137, 2.0 u) is outside DD and built only on the owner's
    yes.

# DD rulings, round 17 (D-DD.143 to D-DD.144): DD4a review Q1 (Mwea's `f_m`) and Q2 (metered room energy against `M`) (Q2 a DRAFT)

Architect (Claude, fresh DD lane hand-off after round 16), 2026-11-22. Read: `review-DD4a.md` Q1, Q2 and its residual-risk
note (on `task/DD4-cold-ev-reality` at 5d6217703; DD4a is since merged to main at 6e3c02ab5); D-DD.20, D-DD.119;
spec §4.4, §5.6; `M` (`demo-site-scenario-manifest.yaml`) `harvest-cold` (`energy_model`, the three rooms' `period`,
bridges and options) and `history.json`'s cold room-months. Writer run `/opt/assetecon/worlds/DD4a-0c5d5fab7b90/`
read only (Σ compressor-meter 5-minute means × 5/60 per room-month; ambient and chamber means from the readings);
the projection is a read-only script in the session scratchpad, deleted after. No database touched. Owner rules
applied: loyal to the operating world, one model-computed figure per quantity, nothing fitted to the story; the
Kobo precedent (D-DD.92: "Revisit a plant figure", then "Architect proposes, owner approves", D-DD.97; D-DD.98 and
D-DD.125: the readings stand and the story moves).

The owner is informed of both. **D-DD.144 was approved by the owner on 22 Nov ("Approve rebuild"; owner-demo-data-answers-2026-11-22.md); DD4.6 is in scope**: nothing beyond D-DD.20's meter bill is
built from it until the owner approves.

- **D-DD.143 Q1: Mwea has no efficiency condition, f = 1 in every month; the ruling's test holds and its text is
  amended** (model; amends D-DD.119 "efficiency" and spec §4.4; builder default 14 confirmed).
  - *Why.* `f_m` is a world input: a declared compressor condition that the meter then shows. Mwea's 2650 against
    2635 (+0.6 %) is a story residual "inside 5 % tolerance" whose own decision text says "no equipment problem to
    fix" (`MWEA-COMPRESSOR`). Reading it back as a condition would make an output an input, and under D-DD.144 both
    leaves follow the meter, which would make the input circular.
  - *Rule (replaces D-DD.119's sentence "for the accounting period, Fraction(period.actual.kwh) /
    Fraction(period.actual.kwh_model) ... A Site with no `kwh` rule and no `kwh_model` has no entry").* A room has
    an `f_m` table only where the story declares an equipment efficiency condition: Kirinyaga alone (`role_in_story`
    "normalised energy inefficiency", the `KIRI-REPAIR` condenser and leak repair). Its table stays {07: 21/20,
    08: 11/10, 09: 117/100, 10: 500/403, 11: 500/403}. Mwea and Thika have no entry (f = 1).
  - *Unit impact: none.* The built code and its test already do this; nothing moves (no readings, no pins).

- **D-DD.144 Q2 (DRAFT, awaiting the owner): `M`'s side is wrong. Its cold energy model is a figure no physics
  produced; the room stands and the cold energy story is restated from the meter** (model; would amend `M`
  `harvest-cold.energy_model` and the cold `period` leaves, D-DD.119's `f_m` source, spec §4.4 and §7 DD4).
  - *Which side.* The writer meters October at Mwea 1576.3, Thika 1771.3 and Kirinyaga 2113.6 kWh against `M`'s
    2650, 3720 and 5000. Decomposed from the readings (October, ambient 24 °C, chamber mean 3.02 °C):
    - crate-independent: auxiliary 1.0 kW × 744 h = 744 kWh, plus leak 0.08 × 21 K × 744 h / COP 2 ≈ 625 kWh:
      about 1,370 kWh a room, against `M`'s `base_kwh` 1550 (12 % apart);
    - crate-dependent (respiration, field heat, door): about 0.045-0.05 kWh per crate-day at the meter, against
      `M`'s `k_kwh_per_crate_day` **0.25**. That term is the whole gap: (M − meter) / crate-days is 0.247, 0.225
      and 0.220 (Kirinyaga at f = 1).
    - 0.25 kWh a crate-day at COP 2 is about 21 W of heat per 20 kg crate, about 1 W/kg: some ten times vegetable
      respiration at 2-5 °C (refrigeration handbook tables, about 20-150 mW/kg), or a full field-heat pull-down of
      the whole stock every day. No load the room lacks closes it: the gap is 1.4-2.9 kW continuous per room, while
      fans, controls, lighting and defrost (off-cycle at a 2-4 °C box) are already in the 1.0 kW auxiliary, and the
      door, the weakest figure by provenance (0.02 kWh/min, copied from the cold-lab fixture; a curtained 2 m² door
      at 21 K infiltrates nearer 3-4 kW), opens 33-62 times a month, so even a sourced value adds under 10 kWh.
    - `M` itself labels the model "[proposed] ... coefficients fitted on 60 days of meter + occupancy per room in a
      pilot". No pilot ran. Its October kWh are that model's output plus a story excess: the D-DD.92 class (a history
      no physics produced). Scale check (room volume Assumed, about 75 m³ for 400 crates): the meter's about
      19,000-21,000 kWh a year is about 250-285 kWh/m³, already above measured cold-store benchmarks (UK stores
      59-124 kWh/m³ a year, small stores higher, an 8× spread: Evans et al., Defra cold-store studies); `M`'s is
      420-800.
  - *Proposal (Assumed method, not a fitted world).* Keep every room figure. Restate `M`'s energy model by the
    product's own declared method run on the world's readings, so the model is computed, not typed:
    - `base_kwh` and `k_kwh_per_crate_day` = the ordinary least-squares line of the metered room-month kWh,
      normalised to 24 °C by `M`'s form (÷ (1 + 0.025 × (ambient − 24))), on `crate_days`, over the healthy rooms'
      pilot months: **Mwea and Thika, July-September** (6 room-months, 92 days a room; Kirinyaga is excluded because
      it carries a declared condition). `base_kwh` to whole kWh, `k` to 4 decimals, half-even. Projected: **1304 and
      0.0554** (`status` becomes "fitted on Jul-Sep meter + occupancy, Mwea and Thika (D-DD.144)").
    - Every cold `kwh` leaf (history and period) is the meter's (D-DD.20, unchanged); `kwh_model`, plan `kwh`, energy
      and every `{fig:}` they feed follow the restated model, in one `M` commit after DD4.4's bill, rev bump (D-DD.30
      chain). A figure that does not follow stops for the Architect.
    - `f_m` source frozen: Kirinyaga's table becomes the declared constant `telemetry_cold.EFFICIENCY_CONDITION`
      (D-DD.143's values) with a parity test against the view at main 6e3c02ab5, because `M`'s period `kwh` /
      `kwh_model` will follow the meter and can no longer be the input that drives it.
  - *Result, October (projection; the writer measures).*

    | Room | Meter kWh (`M`) | Energy cost at 0.20 (`M`) | Model kWh | Story |
    |---|---|---|---|---|
    | Mwea | 1576 (2650) | about 315.26 (530.00) | about 1544 | +2.1 % above model (`M` +0.6 %), still inside 5 %: "no equipment problem" holds; contribution about +203 (−12); still the highest cost per crate-day |
    | Thika | 1771 (3720) | about 354.26 (744.00) | about 1785 | −0.7 %; the incident story is untouched |
    | Kirinyaga | 2114 (5000) | about 422.72 (1000.00) | about 1854 | **about +14 % (`M` +24 %)**: about 260 kWh, about −52 a month (−194); repair about 41.65 a month, about +150 net on 12 months (+1,512.40); replace about −3,950 (−1,988.40). Repair still beats replace, by less |

    The 24 % is the compressor's own condition (f = 500/403); the meter shows about +14 % because the 1 kW auxiliary
    does not degrade. July-September at Kirinyaga read +3 %, +6 %, +8 % against the model, a visible drift.
  - *Alternative.* Revisit a room figure so the meter approaches `M`: it needs 1.4-2.9 kW more continuous load per
    room (auxiliary about 3-4 kW, or COP below 1), which no source supports. Refused as fitting the world to the
    story. The other alternative is to keep `M`'s model beside the meter: the product would then show every room
    40-55 % below its model, which is two figures for one quantity.
  - *Default applied pending the owner.* DD4.4 builds the cold bill from the meter as D-DD.20 already rules, and
    `meter_billed` prints `M`'s figures beside it. The restatement (new part **DD4.6**, 1.0 u, after DD4.5) waits
    for approval: the model fit as above, `M` restated with the sweep of every typed "24%", "+0.6%", "970 kWh",
    "194", "155.20", "1,512.40" and "775 kWh" in `M`, `domain-and-decision-models.md` and
    `interactive-mockup-vNEXT/`, the `EFFICIENCY_CONDITION` freeze and the parity re-pins
    (`backend/tests/golden/6h_parity.json` lists the moved figures). If approved, DD4b 4.75 → 5.75 u, DD 49.75 →
    50.75 u.

# DD rulings, round 18 (D-DD.145): DD3b1 deviations 1-4 (unit events as forcings)

Architect (Claude, DD lane), 2026-11-22. Read: `packet-DD3b.md` "Known Deviations" 1-4 on `task/DD3b-mini-plant`
(f1f71ae65); `simulator/assetops_simulator/kernel/execute.py` `_forcing_index` (skips `end <= start`) and
`_cause_index` (POINT causes at `point_due_at`); `world/telemetry.py` `STEP_MINUTES` 5; D-DD.75, D-DD.126,
D-DD.127. The owner is informed; no owner weigh-in is needed (no story figure moves).

- **D-DD.145 Unit events are one-minute WINDOW forcings read at the step that holds them; the kernel is unchanged.
  Deviations 2-4 are confirmed** (model; amends D-DD.127's "POINT forcings" and spec §4.3 "Forcings").
  - *Ruling on deviation 1: the builder's default.* A kernel that exposes POINT forcings is a version move at a
    protected seam. It would reach every pack that reads forcings (mini-grid v1-v9, cold-thermal 1-2, EV), and its
    proof would be a byte-parity golden over every pack's runs. It would buy nothing that the 5-minute step can
    resolve: a POINT and a one-minute WINDOW both land on the one step `point-applied-once` names. So:
    - the writer declares `UNIT_FAIL` / `UNIT_RESTORE <component>` as a WINDOW [t, t + 1 min), with t the instant
      in `UNIT_EVENTS`;
    - v9 applies it in `commit` at the start of the step that holds t;
    - the unit's state-change event row is stamped **t itself** (18:40, 19:20, 11:00, 11:02), never the step start
      or the next step, because C-DD6 and C-DD20 read the instant;
    - the 5-minute sample at the failing step's start still shows the unit as it was, and the controller acts from
      the next step;
    - `conditions` gains "unit failures and restores apply at the 5-minute step holding their instant; the
      controller responds at the next step (Assumed)". If the kernel ever exposes POINT forcings, `_unit_events`
      reads them unchanged (the builder's note), and no figure moves.
  - *Is the one-step lag honest for Kisiwa, 30 Oct 18:40 (D-DD.126)? Yes.* 18:40 is a step start, so GEN-KS-01 is
    out for the whole 18:40-18:45 step, and GEN-KS-02 can be asked to start from 18:45. A controller detecting a
    trip and bringing on the standby set takes a start delay, cranking and warm-up of about a minute to a few
    minutes, so a response within 5 minutes is ordinary practice. The battery carries the gap. C-DD20's question
    (unserved evening energy after 18:40) is unaffected. Mto's 11:02 is off the grid and applies from 11:00, two
    minutes early, inside one 5-minute mean: the same quantisation every forcing in the writer has (D-DD.75), not a
    claim. Its event row still reads 11:02.
  - *Deviation 2, confirmed with a floor:* the requested generator power P = max(0, demand + the battery's charge
    acceptance at T (taper and headroom, the pack's own limit) − available solar). This is v8's cycle-charging
    intent, made numeric for choosing a set.
  - *Deviation 3, confirmed:* on a fuel-limited multi-unit segment, each unit gets its rating share of the tank, and
    where the no-load burn exceeds the tank, the litres are scaled to the tank. A unit test asserts the segment's
    litres never exceed the tank. No Site reaches it.
  - *Deviation 4, confirmed:* `UNIT_RESTORE` returns a generator to STOPPED (D-DD.127), and it can be asked to start
    from the next step. Kisiwa's 17 Aug 11:00 restore therefore makes GEN-KS-01 startable from 11:05.
  - *Units:* none. This is the default already built, plus a `conditions` line and the event-stamp test (DD3b1's fix
    round or DD3b2, at the builder's choice).

# DD rulings, round 19 (D-DD.146): C-DD6's Kisiwa and Mto clauses on the channels roles-5 admits

Architect (Claude, DD lane), 2026-11-22. Read: `backend/conversions/world/KISIWA-001-bindings.json` and
`MTO-001-bindings.json` (`minigrid-roles-5`; `generator_state` ENUM admits FAILED; no inverter state role),
`COLD-THIKA-bindings.json`, `tools/dd_check.py` `judge_failures_at_instant`, spec §4.3, D-DD.45, D-DD.121,
D-DD.127, D-DD.145. The owner is informed, and may weigh in on the inverter-state gap (last bullet).

- **D-DD.146 No binding or role is added. C-DD6 asks each failure of the channel the product admits for that unit.
  Kisiwa and Mto go live in DD3b, not PENDING** (model; amends D-DD.145's "event row", D-DD.121, spec §4.3
  "Readings" and §8.1 C-DD6; the builder's defaults (a), (b) and (d) are confirmed, and (c) is changed).
  - *Why the judge moves, not the bindings.* The class is that the judge reads one channel shape. Thika's GEN-CR-01
    failure is a START_RESULT event, because its role set has `backup_start_event`. A mini-grid genset controller
    reports the same fact as a status change, and roles-5 already admits that change (`generator_state` per unit,
    FAILED in its map). An event channel added only so the judge finds an event would duplicate a fact already on
    the unit's own channel. That would be bridging, and it would move roles-5's readiness (D-DD.45
    `every_component` is true on the unit roles, so Kobo would show an unbound channel), DD3c's `unit_roles`
    readers and the onboarding parity goldens, for no reader.
  - *Rule (C-DD6, `judge_failures_at_instant`).* A clause names its evidence:
    - `"evidence": "event"`: a value-null `event` row with outcome FAILED (Thika, unchanged).
    - `"evidence": "state"`: a STATE row whose value is FAILED, starting at the clause minute, on the unit's own
      `source_id`. In both cases no other source shows FAILED at that minute.
    - Kisiwa: `{"site": "KISIWA-001", "unit": "GEN-KS-01", "source_id": "gen-ks-01-controller", "at":
      "2026-10-30T18:40", "evidence": "state"}`. The 14 Aug 19:20 FAILED and the 17 Aug 11:00 STOPPED rows are
      asserted in the same test as information.
    - The writer starts that state row at the instant (D-DD.145), so "the event row carries the instant" now reads
      "the unit's state row starts at the instant".
  - *Mto: the inverter's fault is in its power, and the instant is the O&M record's.* Roles-5 binds per-inverter
    `pv_power` and `pv_available_power`, with no state.
    - The clause is `"evidence": "power"`: INV-MT-02's (`inv-mt-02-controller` `ac-power`) 5-minute mean is 0 from
      the step holding 11:02 to the end of the span, while irradiance is above 0 and INV-MT-01's mean is above 0 at
      that step. It is above 0 at the step before.
    - The minute 11:02 itself is the book's (`M` operations, the O&M occurrence), not a reading. The judge's detail
      says so.
    - The pack's inverter state (D-DD.127) stays internal. The writer emits only bound channels.
    - Spec §4.3 "Readings" becomes: "per unit device, power (5-minute mean); generator units also state on change;
      inverter state is not emitted (roles-5 has no role for it, D-DD.146)".
  - *(b) confirmed:* `conditions.unit_events` lists every unit event with its instant and source. It is information,
    never admitted.
  - *The gap, stated rather than bridged.* A real inverter reports a fault state, and the product has no role to
    read one. The coordinator logs "inverter_state role (roles-6) and a reader" in `.agent/backlog-post-demo.md`
    (not demo-critical: the Mto beat is the claim and the lost daytime supply, which power shows). The owner may
    want it sooner.
  - *Units:* +0.25 u in DD3b2 (the judge's evidence field, two clauses, tests on the writer's rows). DD3b 5.75 →
    6.0 u, DD 50.75 → 51.0 u.

# DD rulings, round 20 (D-DD.147 to D-DD.149): DD3b2's pure runs (deviations 9-11, the bound hit)

Architect (Claude, DD lane), 2026-11-22. Read: `packet-DD3b.md` on `task/DD3b-mini-plant` (ab307b8c6) "Pure runs",
"`dd_check --pure`" and deviations 9-11; D-DD.92, D-DD.104, D-DD.126, D-DD.131, D-DD.132; `M` Kobo, Kisiwa and Mto
`period`, `factor_sources`, `observations`, `findings_expected` and OR-MG-2 (`M:1862`). No run was made. The owner
is informed of all three and asked to weigh in on **D-DD.148**'s story change and D-DD.147's Kisiwa figures.

- **D-DD.147 Q1: the bound hit is the ordering effect D-DD.92 named; DD3b3's reorder rule resolves it at all three
  Sites. What it exposes is that Kisiwa's and Mto's fuel story is also a figure no plant produced** (confirms
  D-DD.92 and D-DD.131 for Kisiwa and Mto; amends nothing in the plant).
  - *Why it is ordering.* The pure runs still take D-DD.32's notes (history litres). D-DD.92's rule places notes
    only below 25 % of the tank, and only as many as fit in the free space, so an overfill cannot occur by
    construction. Measured burns per month: Kisiwa 689-1,255 L on 5,000 L, Mto 0-32 L on 1,000 L, Kobo 0-762 L on
    2,500 L. From the 50 % start, Mto never reaches 250 L, so it has no purchase July-October. Kobo's new August
    overfill comes from D-DD.104 (July 0 L) and is the same effect. `--restate-notes` iterates to no crossing, and
    the strict writer then accepts the Jul-Oct DIR (deviation 10 closes there).
  - *What else is wrong (the class, W6).* `M`'s Kisiwa and Mto fuel leaves are typed like Kobo's (D-DD.92). D-DD.131
    already restates October `period.actual` for all three from the notes run. Projected (the run gives the figures):
    - Kisiwa: `diesel_l` about 904 L (burned 884 + draw 20) against 2,400; cost about 1,175 against 3,120;
      contribution about +1,695 against −250. It is still the highest diesel use of the three, and no longer
      loss-making.
    - Mto: about 32 L against 320; cost about 40 against 400.
  - *Plan leaves stay the operator's budget* (a booked record of intent, as D-DD.130 keeps the history months). The
    bridge lines that compare necessary litres with plan (`SOLAR_SHORTFALL_NECESSARY_GEN`, `EVENING_NECESSARY_GEN`)
    follow their stated formulas, so they turn favourable: fuel well under budget, which is what the tank says.
    D-DD.131's "stop if the bridge does not close" still applies.
  - Kisiwa's typed "95 %" (GEN-KS-02's evening load) and `BATTERY_NEAR_RESERVE` 22 days join D-DD.131's sweep. Each
    is printed from the readings by the product's own rule (the peak evening generator kW after 30 Oct 18:40 ÷ 60;
    the warning's own count). A leaf that has no rule stops for the Architect.

- **D-DD.148 Q2: at Kisiwa the plant stands. OR-MG-2 is restated to what the plant shows, and C-DD20's Kisiwa clause
  was the lane's own error, now corrected to `M`'s story** (amends D-DD.126's C-DD20 wording, spec §8.1 C-DD8 and
  C-DD20, `M` OR-MG-2 and Kisiwa `findings_expected`; nothing fitted).
  - *(a) Candidate minutes.* The 20 minutes are the declared dispatch working: cycle charging continues to the
    90 % stop past sunrise (GEN-KS-01 at 22.8 kW, 10:00-10:15, while PV gives 27 kW against a 19.8 kW load). A rule
    that stops the set when the sun is up would be a new plant figure chosen to meet the story, so it is refused.
    `M`'s `count: 0` was typed. Restated:
    - OR-MG-2 becomes "Kisiwa: candidate time immaterial (under 1 % of generator minutes in every month); no
      fuel-saving option qualifies". On the run, July is 20 min of about 5,555 (0.4 %), and 30 Oct is 20 min.
    - The product's rule gives about 2.4 L (about 3 at 1.30) on such a day.
    - `findings_expected` follows D-DD.131: days with a positive writer stand-in (labelled projected). That is about
      67 L in October and about 115 L in August that the battery could have carried, beside the product's own
      figure.
    - If the product's option logic qualifies a fuel option on these minutes, stop for the Architect.
  - *(b) Unserved energy.* `M` itself records none: `customer_hours_interrupted: 0`, "GEN-KS-02 carries the evening
    load", `standby_kw` "0 ... GEN-KS-02 carries", and `KIS-NOACT` rejected for lost *redundancy* (P1 on a single
    set), not for lost supply. D-DD.126's "unserved evening energy after 18:40" misread that. C-DD20 Kisiwa becomes:
    - GEN-KS-01 FAILED and at 0 kW from 30 Oct 18:40, with no restore;
    - every generator interval in 18:00-23:00 after then is on GEN-KS-02;
    - unserved energy 0 over the whole span (as in 14-17 Aug).
  - *Story, plainly.* Kisiwa's failure costs redundancy, not supply. The point becomes "one more failure and the
    evening goes dark", which is the existing `KIS-REPAIR` must-do reason, unchanged. "Nothing avoidable" becomes
    "nothing material avoidable".

- **D-DD.149 Q3 and Q4: the `--pure` defaults are confirmed, with two changes; `measured.json` gains no per-day
  series** (amends D-DD.132).
  - *Confirmed:*
    - burned per unit on its `/2` curve;
    - dips at the month's first and the next month's first tank reading (D-DD.131's dips);
    - candidate = a generator above 0 kW while PV ≥ 1.1 × feeder load (dispatch-3.2, OR-MG-2's measure);
    - MG-5 critical = the first of `critical_load_order` (clinic).
  - *Changed:*
    - the unexplained tolerance is read from `M` `fuel_balance.tolerance_pct` per Site (2.0 today), not typed;
    - C-DD8's Kisiwa candidate is judged per month against D-DD.148's bound and printed, not counted over the span.
  - *No per-day series.* The restated Kisiwa clause asks for 0 unserved. An energy quantity is never negative, so
    month totals of 0 prove every day is 0. The unit facts are read from the readings rows. Mto's litres per day
    before and after 28 Oct 11:02 are computed by the judge from the per-unit generator power rows on the same
    curve (D-DD.55: judges read rows). The writer is not changed.
  - *Units:* +0.25 u in DD3b3 (C-DD8 and C-DD20 Kisiwa judges, tolerance read, OR-MG-2 and `findings_expected` in
    D-DD.131's `M` commit). DD3b 6.25 u over its three parts (each part at most 6), DD 51.0 → 51.25 u.

# DD rulings, round 21 (D-DD.150 to D-DD.152): DD3b3 deviations 12-14 (the bridge stop, Kisiwa's candidate share, C-DD17 with no burn)

Architect (Claude, DD lane), 2026-11-23. Read: `packet-DD3b.md` on `task/DD3b-mini-plant` (6d567731e), "Moved figures
against D-DD.147", the full Jul-Oct `dd_check --pure` and deviations 12-15; D-DD.19, D-DD.104, D-DD.131, D-DD.147 to
D-DD.149; `M` Kobo, Kisiwa and Mto bridges. No run was made. The owner is informed of all three and asked to weigh
in on **D-DD.151** (Kisiwa's story) and **D-DD.152** (Kobo July and August).

**Owner-answered 23 Nov** (`owner/owner-demo-data-answers-2026-11-22.md` §"D-DD.150-152"): D-DD.150 and D-DD.151
"Accept (Recommended)"; D-DD.152 "Fix before demo", so the absolute tolerance floor is built before the demo
(D-DD.153), not logged to the backlog.

- **D-DD.150 Deviation 12: every mini-grid Site's fuel bridge carries the same three fuel lines. Kisiwa and Mto gain
  CANDIDATE_RUNNING, as Kobo has it** (model, W6 class; amends D-DD.131 "Bridge"; releases the held `M` commit).
  - *Why.* The lines decompose `diesel_l` = necessary + candidate + unexplained (the builder's identity, confirmed).
    Kisiwa and Mto had no candidate line only because their typed `candidate_l` was 0. Folding the candidate into the
    necessary line would label avoidable running as necessary: the opposite of the finding.
  - *Rule.* `{driver: CANDIDATE_RUNNING, overlap_group: <SITE>-2026-10-FUEL, amount: −candidate_l × price}`, with
    Kobo's basis text, its `fig`/`rec` references re-pointed to the Site. On the packet's leaves: Kisiwa −87.10, so
    the bridge closes at 1,759.80; Mto −40.00, so it closes at 255.00. The `M` commit then proceeds as D-DD.131
    (leaves, `fuel_balance`, `findings_expected`, chain).
  - *Figures the owner sees.* Mto's 32 L in October all came after the inverter trip. The writer's stand-in counts
    them as litres the battery could have carried (candidate 32 L, about 40.00, labelled projected). The product's
    own figure is served beside it.

- **D-DD.151 Deviation 13: the plant and the measure stand. My 1 % bound was wrong: it was drawn from July and one
  day. OR-MG-2 is no longer a negative control; Kisiwa's candidate is printed, not bounded** (amends D-DD.148 (a),
  spec §8.1 C-DD8, `M` OR-MG-2 and `phase-plan-and-acceptance.md` R3).
  - *Which is wrong.* The measure is the product's (dispatch-3.2: generator above 0 kW while PV ≥ 1.1 × load), and
    the plant is declared. Any bound chosen now to pass would be fitted. The full span gives 0.36 %, 11.27 %, 0 % and
    10.17 % of generator minutes (July-October). The writer's stand-in gives 67 L of 904 L in October (about 7 %,
    about 87.10).
  - *Rule.* C-DD8's Kisiwa clause prints the share per month and asserts only that the minutes were computed for
    every month. OR-MG-2 becomes "Kisiwa: candidate time printed per month; no fuel-saving option is in `M`". R3's
    negative controls drop OR-MG-2 and keep the rest. If the product raises a fuel-saving option at Kisiwa, it is
    reported, not suppressed.
  - *Story, plainly.* Kisiwa is no longer "nothing avoidable". About a tenth of its generator time in August and
    October is spent charging the battery while the sun could carry the load, which is about 87 a month in October.
    The repair beat is unchanged. The typed "95 %" for GEN-KS-02's evening load prints as about 70 % (41.87 kW of
    60): still no redundancy, but less strain than the story said.

- **D-DD.152 Deviation 14: the draw stands. C-DD17 judges the tolerance only in months the generator burned, and
  states what the product shows in the others** (amends spec §8.1 C-DD17; a structure finding to its owner; owner
  23 Nov "Fix before demo": the floor is ruled by D-DD.153, which replaces this bullet's C-DD17 rule).
  - *Why.* D-DD.19's 12/12/11 L draws are declared world causes: fuel did leave the tank. Removing or resizing them
    to pass a check would be fitting. A tolerance relative to consumption has no meaning when consumption is only
    the draw.
  - *Rule.* For each month: unexplained ≥ 0, and unexplained equals the declared draw. Where burned > 0, it must be
    within `fuel_balance.tolerance_pct` July-September and above it in October (September 1.42 %, October 18.92 %:
    passes). Where burned = 0 (Kobo July and August), the detail prints "no burn: 12 L unexplained, which the product
    shows against a 12 L consumption".
  - *Structure finding (not a DD edit; coordinator logs it in `.agent/backlog-post-demo.md`).* The unexplained-fuel
    tolerance is relative only. A real tank dip has an absolute uncertainty (litres), so at low consumption the
    product can flag a residual that is within measurement error. The fix is an absolute floor from the level
    sensor's declared accuracy, and it needs a sourced figure.
  - *Figures the owner sees.* Unless that floor lands, Kobo may show 12 L of unexplained fuel in July and August,
    months its generator never ran, beside October's 120 L. The October beat is unchanged.
  - *Units (D-DD.150 to D-DD.152):* +0.25 u in DD3b3 (two bridge lines, C-DD8 and C-DD17 judges, OR-MG-2 and R3
    wording). DD3b 6.5 u over three parts; if DD3b3 passes 6 u, the coordinator splits the `M` commit off. DD
    51.25 → 51.5 u. Deviation 15 (unwritten-list wording) is a builder tidy: `diesel_l` / `diesel_cost` are listed
    as written from purchases at a notes Site, with no new reason word.

# DD rulings, round 22 (D-DD.153 to D-DD.154): the absolute floor on the fuel-balance tolerance, and the fuel records it needs

Architect (Claude, DD lane, fresh hand-off), 2026-11-23. Read: rounds 17-21; owner §"D-DD.150-152" (D-DD.152 "Fix
before demo"); `fuel_balance/rules.py` (`balance`, `TANK_MARGIN_FACTOR`, `ACCURACY_BASES`), `fuel_balance/service.py`
(`accuracy_values`), `night_text.py`, `actions/fuel_verification.py`, `actions/verification_rules.py`;
`structure/observe/observe.py` (`_band`, `basis`, `claim`), `structure/observe/service.py`, `structure/litres/rules.py`
and `inputs.py`, `structure/rows_mini_grid.py` (`unexplained_l` tolerance 2.0 % of `diesel_l`; `diesel_l` =
necessary + candidate + unexplained + extra); `sites/models.py` (`fuel-level-sensor-accuracy` on `FUEL_TANK`);
`backend/tests/fixtures/on1/lakeside-power.onboarding.json` (no accuracy declared at any tank);
`test_dd3c_kobo_parity_postgres.py` (10 L injected into its copy only); `packet-DD3b.md` (6d567731e) pure-run table.
Source: Technoton DUT-E product page (https://jv-technoton.com/products/dut-e/), specification table: "Relative
measuring error (to the length of the measuring part), %, not more than ±1". No run was made; no database touched.
The owner is informed of both; **D-DD.154** is a structure finding the owner may want to weigh in on (default applied).

- **D-DD.153 The unexplained-fuel tolerance is max(relative × consumption, 2a), with a the tank's declared level
  accuracy, declared at the three mini-grid tanks as 1 % of capacity, Assumed** (model; amends D-DD.152's C-DD17 rule
  and its backlog finding, spec §8.1 C-DD17, §7; adds part DD3d).
  - *Why.* A month's balance is opening level + deliveries − closing level − modelled burn. Each level carries the
    sensor's absolute uncertainty, so the residual carries about 2a whatever the consumption. A tolerance that is only
    relative goes to zero with consumption and flags a residual inside measurement error: Kobo's 12 L draws in July and
    August (no burn) read as unexplained against a 0.24 L band. The product already has the term: `fuel-balance-1`
    (the night check) widens its band by `TANK_MARGIN_FACTOR × a` = 2a (F0, "applied to opening and closing, combined
    linearly"). The monthly observer reuses that term on merit; nothing new is invented.
  - *The figure (step 1).* The Foundation property exists: `fuel-level-sensor-accuracy` (L) with
    `fuel-level-sensor-accuracy-basis` on `FUEL_TANK`. It is missing at all three real Sites (Lakeside's `/2` file
    declares none; only the Kobo parity test's copy injects 10 L). The Sites declare a generic "Fuel level sensor"
    with no make or model, so no device sheet applies. The sourced figure is the class figure of a common capacitive
    tank probe: Technoton DUT-E, ±1 % of the measuring length, not more than. On a probe spanning the tank's height
    that is about 1 % of capacity (exact for an upright tank; up to about 1.27 % near mid-height in a horizontal
    cylinder, which is why the value is labelled Assumed and not Declared). It is K1's existing rule (10 L = "1 % of a
    1000 L tank") applied to each tank's declared capacity:

    | Tank (`/2` file) | `tank-capacity` | a = capacity / 100 | floor 2a |
    |---|---|---|---|
    | KOBO-001 `fuel-tank` | 2,500 L | **25 L** | 50 L |
    | KISIWA-001 `fuel-tank` | 5,000 L | **50 L** | 100 L |
    | MTO-001 `fuel-tank` | 1,000 L | **10 L** | 20 L |

    Each tank's `properties` list gains, after `tank-capacity`: `{"property_key": "fuel-level-sensor-accuracy",
    "value": <a>, "unit": "L", "source": "SITE", "source_version": 1}` and `{"property_key":
    "fuel-level-sensor-accuracy-basis", "value": "GENERIC_DEFAULT", "unit": "state", "source": "SITE",
    "source_version": 1}` (D-DD.71). GENERIC_DEFAULT renders Assumed (D-DD.17). The basis sentence, quoted in the
    packet and `conditions`: "Generic capacitive level-sensor class, ±1 % of measuring length (Technoton DUT-E data
    sheet), taken as 1 % of this tank's capacity; not this sensor's calibration (Assumed)". Lakeside's `/2` digest pin
    moves (D-DD.128's chain); the packet lists it.
  - *Rule (product, `structure/observe/`).*
    - `observe/rules.py` gains `FLOORED: Mapping[str, tuple[str, ...]] = {"MINI_GRID": ("unexplained_l",)}`: the only
      leaf with an absolute floor.
    - `observe.py` gains `@dataclass(frozen=True) class Floor: litres: Decimal; accuracy_l: Decimal; basis: str;
      revision_id: str` and `FactorObservation.floor: Floor | None = None` (last field, default None).
    - `observe(actual, target, declarations, floors: Mapping[str, Floor] = MappingProxyType({}))` and
      `observe_site(site, declarations, floors=...)` pass `floors.get(leaf)` to `_one` only for a leaf in
      `FLOORED[key]`; any other leaf gets None.
    - In `_one`, the adverse branch only: `rel = _band(tolerance, actual)` exactly as today. If `rel` is None the state
      stays TOLERANCE_NOT_AVAILABLE (unknown is never zero; the floor does not stand in for a missing `diesel_l`). If
      `tolerance.source == "NONE"` the band stays 0 (no floor). Otherwise, with a floor, `band = max(rel, floor.litres)`
      and `FactorObservation.floor = floor` **only when `floor.litres > rel`** (strict); else `band = rel` and `floor`
      None. The pct-0 case follows the same line: `rel` 0, so the floor binds (a declared 0 % sets no relative band;
      the measurement's own uncertainty remains).
    - `basis()` adds `"floor": {"litres": _dec(f.litres), "accuracy_l": _dec(f.accuracy_l), "basis": f.basis}` and
      `claim()` adds `"floor": {..., "revision_id": f.revision_id}` **only when `o.floor` is not None**. With no
      binding floor both strings are byte-identical to today's.
    - The floor in force (`observe/service.py`, new port `FloorReadPort.read(tenant_id, site_id, window, known_at) ->
      Floor | None`, wired in `structure/observe/composition` on the same Foundation read the litres inputs use,
      `FuelReadPort.read_at`): the Site's active `FUEL_TANK` assets; not exactly one gives None. Its accuracy is
      `fuel_balance.rules.declared_for(fuel_balance.service.accuracy_values(tx.properties(tank.asset_code,
      (ACCURACY_KEY, ACCURACY_BASIS_KEY), lo, hi)), lo, hi, fuel_balance.rules.ACCURACY_BASES)` over `window` =
      `month_bounds(month, tz)` (already computed in `_site`), imported by name, never re-derived. None gives no floor
      (today's behaviour). `litres = TANK_MARGIN_FACTOR × a` (imported), converted exactly to `Decimal` in the
      observer's 34-digit half-even context. `_site` passes `{"unexplained_l": floor}` when a floor exists.
    - No copy changes: no screen renders the observation's band today (swept: `frontend/src`, `i18n`, `chain/`).
  - *Every reach, named (W6).*

    | Reach | Change |
    |---|---|
    | Monthly observer, `unexplained_l` (`structure/observe/`) | the rule above |
    | `fuel_balance` night rules (`fuel-balance-1`) | **code unchanged**: already 2a; it now reads the declared a at the three tanks, so nights move from NOT_ASSESSED `NO_SENSOR_ACCURACY` to assessed (needs D-DD.154's delivery records first) |
    | Night text (`night_text.py`) | **code unchanged**: renders "Declared sensor accuracy ±25 L" (Kobo), ±50 L, ±10 L where it said "no tank sensor accuracy declared" |
    | Verification `fuel-residual-within-band-1` (`fuel_verification.py`) | **code unchanged**: reads the night's band, which carries 2a |
    | Verification cost check (`verification_rules.py`, modelled cost) | **not reached**: it compares modelled fuel cost and has no fuel-balance tolerance; held by `test_dd3c_kobo_one_unit_golden` |
    | C-DD17 (`tools/dd_check.py`) | restated below |
    | `structure/litres/rules.py` (`unexplained_l` value) | **unchanged**: the value stays burned − modelled; only its judgement moves |

  - *C-DD17 (replaces D-DD.152's rule).* The checker reads each tank's a from Lakeside's `/2` file by its own JSON
    read and types the factor 2 with a comment citing D-DD.153 (W2: no import from the product). Per month, July to
    October, with consumption = burned + draw and `tol = max(fuel_balance.tolerance_pct / 100 × consumption, 2a)`:
    - Kobo: unexplained ≥ 0 and equal to the declared draw; ≤ `tol` July-September, > `tol` in October. The no-burn
      carve-out is withdrawn: July and August are judged like any month.
    - Kisiwa: unexplained equal to the draw and ≤ `tol` every month (printed with its share). Mto: unexplained 0.
    - Served (DD6.1, through D-DD.133's read): each Site-month's `unexplained_l` observation state and band equal the
      table below. If that read does not carry the observation, DD6 stops for the Architect.
  - *Verdicts that change (step 3; projected from the DD3b pure run, target 0; the run measures, nothing tuned).*

    | Site-month | consumption (L) | unexplained | relative band | band now | state before → after |
    |---|---|---|---|---|---|
    | Kobo Jul | 12.00 | 12 | 0.24 | 50 | **RAISED → INSIDE_TOLERANCE** |
    | Kobo Aug | 12.00 | 12 | 0.24 | 50 | **RAISED → INSIDE_TOLERANCE** |
    | Kobo Sep | 773.20 | 11 | 15.46 | 50 | INSIDE_TOLERANCE (band and basis move) |
    | Kobo Oct | 634.22 | 120 | 12.68 | 50 | RAISED (band and basis move; the October beat holds, 120 > 50) |
    | Kisiwa Jul | 1,275.28 | 20 | 25.51 | 100 | INSIDE_TOLERANCE (band and basis move) |
    | Kisiwa Aug | 1,255.15 | 19 | 25.10 | 100 | INSIDE_TOLERANCE (band and basis move) |
    | Kisiwa Sep | 707.02 | 18 | 14.14 | 100 | **RAISED → INSIDE_TOLERANCE** |
    | Kisiwa Oct | 903.56 | 20 | 18.07 | 100 | **RAISED → INSIDE_TOLERANCE** |
    | Mto Jul-Oct | 0-32.38 | 0 | not computed | not computed | NO_GAP, byte-identical (no adverse gap) |
    | Cold and EV Sites | - | - | - | - | not observed for `unexplained_l`, byte-identical |

    Kisiwa's September and October flags were the same fault as Kobo's: 18-20 L monthly draws against a 2 % band of a
    700-900 L month (2.2-2.5 %), inside the probe's ±50 L. They were not in D-DD.152's figures because C-DD17 judged
    Kobo only. Story, plainly: unexplained fuel shows at Kobo in October only, which is the story; Kisiwa and Mto show
    none. The floor also bounds what the month can detect: under about 50 L a month at Kobo and 100 L at Kisiwa, a loss
    is within measurement error. The night check keeps its own 40 L materiality per night.
  - *Parity test (`backend/tests/test_dd3d_tolerance_floor.py`, pure).*
    - P1, relative dominates: one fixture per state path with `pct/100 × |diesel_l| ≥ 2a`. `diesel_l` 3,000 L, a 25
      (rel 60 > 50), unexplained 40 (INSIDE) and 70 (RAISED); and the tie, `diesel_l` 2,500 L (rel 50 = floor, no
      bind). For each, `observe(..., floors={"unexplained_l": F})` equals `observe(..., floors={})` field by field, and
      `basis()` and `claim()` are byte-identical strings.
    - P2, no adverse gap: NO_GAP, FAVOURABLE, ACTUAL_NOT_AVAILABLE, TARGET_NOT_AVAILABLE and TOLERANCE_NOT_AVAILABLE
      (`diesel_l` absent) with a floor are byte-identical to without.
    - P3, a leaf not in `FLOORED` given a floor in the mapping is byte-identical (the mapping is filtered).
    - P4, existing pins unchanged with no edit: `test_3b4_observer*.py`, `backend/tests/golden/6h_parity.json`,
      `test_dd3c_kobo_one_unit_golden.py`, and `git diff main --` on `fuel_balance/rules.py`, `night_text.py`,
      `actions/fuel_verification.py`, `actions/verification_rules.py` and `structure/litres/` is empty.
    - Binding cases: Kobo July (12/12, a 25: INSIDE, band 50, basis carries the floor), Kobo October (634.22/120:
      RAISED, band 50), Kisiwa September (707.02/18, a 50: INSIDE, band 100). Plant (negative control): the floor
      port returning None flips Kobo July back to RAISED with band 0.24. Service test: a Site with two tanks, or an
      accuracy revision starting mid-month, gets no floor.
    - `test_dd3c_kobo_parity_postgres.py` drops its 10 L injection (the file now declares 25 L, read in both
      states); its +5 L plant must still fail.
  - *Part and size (step 4): new part **DD3d** "fuel records and the tolerance floor", `task/DD3d-fuel-floor`, 2.25
    u with D-DD.154.* This ruling's share is 1.25 u: observer rule, port and wiring 0.5; parity and binding tests
    0.25; the three `/2` declarations, digest re-pin and the Kobo parity test 0.25; C-DD17 restated with Kisiwa and
    Mto clauses 0.25. It is its own part, not DD3b3: DD3b3 is at 6.5 u over three parts and is the writer's, while this
    changes a product reader (discovery review: a money-adjacent observation). Order: after DD3b3 merges (D-DD.154
    needs the restated notes); before DD5b loads.
  - *The backlog entry D-DD.152 asked the coordinator to log is withdrawn (built here).*

- **D-DD.154 The DD world writes no FUEL_DELIVERY or TANK_DIP records, so the product cannot value the month's
  unexplained fuel at any mini-grid Site, and a declared a alone would mark every delivery night EXCESS. Default: DD3d
  writes and loads them** (model, W6 class finding; amends spec §5.1, §7; D-DD.133's served C-DD17 depends on it).
  - *Finding.* `structure/litres/rules.py` values `unexplained_l` only between two `TANK_DIP` records within 24 h of
    the month's ends (D-4D.5), with `FUEL_DELIVERY` records between them; otherwise `TANK_DIPS_MISSING`, "not
    available yet". The night check subtracts recorded deliveries. No DD writer or loader emits either kind (swept:
    `simulator/`, `tools/world_history.py`, `tools/dd_check.py`, `tools/dd3_pure_run.py` on main and DD3b; the only
    producers are user entry, `runs/operational_actions.py` and the old `demo_combined*` tools). `M` itself declares
    the source: "fuel delivery notes + tank dips (existing operational records FUEL_DELIVERY, TANK_DIP)",
    source-emulated (`M:789`). So Kobo's October 120 L would not be served, and D-DD.152's "Kobo shows 12 L" is the
    figure the product would show once these records exist. The builder's pre-flight greps again; if a producer
    exists, D-DD.154 drops to 0 u and the records are taken from it.
  - *Rule (default applied pending the owner).*
    - `world/exports.py` (mini-grid books) writes `fuel-records.json` per mini-grid Site, schema
      `assetops.world-fuel-records/1`: one `FUEL_DELIVERY` per accepted note (DD3b3's restated notes) at the note's
      `occurred_at` with its litres, `recorded_at` as the note's (OOO-1's 26 Oct note recorded 4 Nov, so the night
      check shows its existing DELIVERY_RECORDED_LATE limitation); one `TANK_DIP` at 00:00 local on each month's first
      day, 1 Jul to 1 Nov, valued at the writer's published tank level at that step (exact to 0.01 L, D-DD.131's dips),
      `recorded_at` the same instant. Actor "Shift operator" (the Kisiwa operational-actions wording), source word
      Emulated. Month-end dips are ordinary operator practice (Assumed; stated in `conditions`).
    - `load_fuel_records(dir, tenant)` (DD3d, idempotent on `source_record_id`) records each through the existing
      operational fuel-record path that `work/operational_entry.compose_entry` builds (kinds `FUEL_DELIVERY`,
      `TANK_DIP`, unit L, the tank's asset id). DD5b's load step calls it once per tenant (one line in its step list,
      no unit added).
    - Checks: C-DD2 gains the two kinds for each mini-grid Site-month. C-DD8's balance is then also asserted on the
      stored records: opening dip + deliveries − closing dip − burned = the draw, per Site-month. Every assessed night
      is printed by state per Site; any UNEXPLAINED or EXCESS night stops for the Architect (projected: none; the
      largest nightly draw is Kobo's October 3.87 L against the 40 L materiality plus 2a).
  - *Units.* 1.0 u in DD3d (writer file, loader and its Postgres test, C-DD2/C-DD8 clauses). DD3d 2.25 u; DD 51.5 →
    **53.75 u in twelve parts**.
  - *Owner.* Informed. Weigh in if month-end dips at 00:00 should instead follow a stated operator dip time; nothing
    else in the story moves.

# DD rulings, round 23 (D-DD.155 to D-DD.160): DD3b3 deviations 17 (H5) and 18 (the tanks); DD4b review Q1-Q4; DD5a's blocker and deviations; the card sweep

Architect (Claude, DD lane, fresh hand-off), 2026-11-23. Read: `packet-DD3b.md` on `task/DD3b-mini-plant` (4154c09bb),
deviations 16-19; D-DD.76, D-DD.92 "Tanks stay", D-DD.131, D-DD.150 to D-DD.154; `check_manifest.py` H5 (branch line
1512); `simulator/tests/world/test_dd3_telemetry.py::test_each_lakeside_tank_is_the_sites_own_two_months_of_its_largest_month`
(branch); `M` lines 123, 198, 2178; owner §"D-DD.76 tank sizes". For D-DD.157 to D-DD.160: `review-DD4b.md` (branch `task/DD4b-ev-measured`) Q1-Q4
and its residual-risk note on `measured.json`; D-DD.20, D-DD.99, D-DD.124, D-DD.144; `cards/DD5b.md`, `cards/DD6.md`.
For D-DD.161 and D-DD.162: `packet-DD5a.md` (ba6282a8d) deviations 1-5; `evidence/world_seal.py` (`_value`, the EV
refusal); `source_envelope_v3.is_canonical_decimal`; DD4b's `world/telemetry_ev.py` (c86af1a2e: `_rows`, `_event`)
and `packs/ev_charger.scoped_session_id`; D-DD.91, D-DD.123, D-DD.138, D-DD.139; `cards/DD5a.md`.
No run was made; no database touched. The owner is informed of all eight; none moves a figure the owner approved.
D-DD.157 moves Kirinyaga's History series onto the meter (the drift story reads the same, more plainly).

- **D-DD.155 Deviation 18: the declared tanks stay 2,500 / 5,000 / 1,000 L, as the owner approved. The 1,500 / 2,000 /
  500 L are D-DD.76's sizing rule re-run on the restated fuel figures, which D-DD.92 already forbids; the test stops
  re-running it** (test; restates D-DD.76's rule as a declaration-time sizing, not a standing invariant).
  - *Where the smaller figures come from.* Not from `M`'s declarations, the `/2` file or the history's own fields: the
    `/2` and `/1` files still declare 2,500 / 5,000 / 1,000 L, SITE, version 1 (branch lines 830, 285, 1365). The test
    recomputes D-DD.76's rule (twice the largest month, rounded up to a standard size) on today's `history.json` and
    `M` rev 16.20. Those months fell when D-DD.92 and D-DD.131 made consumption the readings' (Kobo largest 634 L in
    October, so 1,268 to 1,500; Kisiwa 904, so 1,808 to 2,000; Mto below 250, so 500). D-DD.76 sized the tanks on the
    books of 22 Nov (1,180 / 2,400 / 320 L delivered). D-DD.92 then ruled: "D-DD.76's rule is not re-run on restated
    books, which would be circular". The tank now drives the purchases (the reorder rule), so sizing it from its own
    outputs is a loop. Its input was also *delivered* litres; the test feeds it consumption. The builder kept the
    declared sizes, correctly; only the test's second pin is wrong.
  - *Rule.* The test keeps one assertion on the declared figures, `declared == {KISIWA-001: (5000, SITE, 1), KOBO-001:
    (2500, SITE, 1), MTO-001: (1000, SITE, 1)}`, and replaces the recomputation with D-DD.76's own inputs typed as
    constants, `SIZED_ON = {"KOBO-001": 1180, "KISIWA-001": 2400, "MTO-001": 320}` (comment: "D-DD.76, books of 22 Nov;
    not re-run on restated books, D-DD.92"), asserting the rule on those gives the declared sizes. It no longer reads
    `history.json` or `M`. The test is renamed `test_each_lakeside_tank_is_declared_at_its_d_dd_76_size`.
  - *Figures that move.* None. The tanks, the 50 % start, the reorder notes, D-DD.153's a (25 / 50 / 10 L) and every
    story figure stay. The packet's deviation 18 closes.
  - *Where.* The DD3b3 fix round (Sonnet), 0 u.

- **D-DD.156 Deviation 17: the history is right; H5 is the old relative-only rule. H5 judges with D-DD.153's tolerance,
  max(2 % × `diesel_l`, 2a), restated in DD3d where a is declared** (check, W6 class: every restatement of the
  unexplained-fuel tolerance follows D-DD.153; amends `M` lines 123 and 198 wording; +0.25 u DD3d).
  - *Why the history stands.* The 12 / 12 / 11 L (Kobo) and 20 / 19 / 18 L (Kisiwa) draws are declared world causes
    (D-DD.19; D-DD.152 "the draw stands"). Lowering them in `history.rules` to pass a 2 % line would fit the world to a
    check. H5's question is "may history show the unexplained-fuel finding before October?". The finding's band is now
    D-DD.153's, so H5 asks it with that band. It is the same fault D-DD.153 fixed in the observer and C-DD17: a
    relative band that shrinks with consumption flags draws inside the tank's measurement error.
  - *Rule.* For a mini-grid Site's actual side: `unexplained_l <= max(D("0.02") × diesel_l, 2 × a)`. `a` is the Site's
    `fuel-level-sensor-accuracy` read by H5's own JSON read of Lakeside's `/2` file, matched by site code, as C-DD17
    reads it; the factor 2 is typed with a comment citing D-DD.153 (W2: no import from the product). The label prints
    both terms: `H5 {scope}: unexplained_l 20 <= max(2% of diesel_l 885 = 17.70, 2a = 100)`. No a declared at a
    mini-grid Site is a FAIL ("no declared level accuracy"); it never falls back to 2 % alone.
  - *Projected.* Kobo July-September 12 / 12 / 11 against max(10.16-10.20, 50): pass. Kisiwa 20 / 19 / 18 against
    max(16.70-17.70, 100): pass. The six failures close. October is not in H5 (it is the finding month).
  - *`M` wording (the same class).* Line 198, Kisiwa's UNEXPLAINED_RESIDUAL basis: "within 2% tolerance" becomes
    "within tolerance (the larger of 2 % and the tank's 100 L measurement floor), reported not investigated". Kisiwa's
    October 20 L of 904 is 2.2 %, inside the 100 L floor. Line 123, Kobo's note: "above 2% tolerance" becomes "above
    tolerance (the tank's 50 L measurement floor; 2 % is 12.68 L)". Kobo's 120 L stays the October beat.
  - *When.* DD3d.2, with the `/2` declarations it reads (a in DD3b3 would have nothing to read). DD3b3 merges with
    exactly these six H5 lines listed as known in its packet, closed by DD3d. DD3d follows DD3b3 directly, so the
    window is one part. Any other new check_manifest failure still blocks DD3b3.
  - *Units.* +0.25 u in DD3d (H5 read and label, two `M` strings, the check counts in the packet). DD3d 2.25 → **2.5 u**;
    DD 53.75 → **54.0 u in twelve parts**.
  - *Owner, plainly.* Kobo and Kisiwa lose a few litres a month in July to September that nobody has explained. Those
    amounts are smaller than the tank gauge can measure, so they are not shown as a problem. Only Kobo's October
    120 L is. Nothing to decide; weigh in only if you want those small amounts shown anyway.

- **D-DD.157 DD4b Q1: one figure per cold room-month. D-DD.144's parenthesis was wrong; DD6 sets `history.json`'s
  cold `actual.kwh` July-September from the meter** (model; amends D-DD.144 R2505 and D-DD.20's "beside, as
  information" for cold history `kwh`; +0.5 u DD6).
  - *What is wrong.* D-DD.144 says "every cold `kwh` leaf (history and period) is the meter's". On DD4b, history
    July-September is the restated model's output, 0.6-7.2 % off the bills (Kirinyaga +5.2 / +7.2 / +6.5 %). DD4b
    follows D-DD.20 and the spec (the pairs print in `meter_billed`, C-DD4 excludes them), so the branch is right
    and the ruling text is wrong. Left so, the product holds two figures for one room-month: the History series and
    the bill. The owner's rule is one figure, loyal to the operating world, and the meter is the operating world.
  - *Rule.* D-DD.144 R2505 reads "Every cold period `kwh` leaf is the meter's". In DD6, before the world build,
    each cold room's `history.json` `actual.kwh` July-September is set to that room-month's metered kWh from the
    cold tenant's `measured.json` (DD4b's frame output), rounded half-even to whole kWh, the leaf's precision (D-DD.162). Then the D-DD.30
    chain: `world_history.py check`, view, goldens, fixtures, re-pins each to the regenerated value (D-DD.93). Not
    circular: the cold writer no longer reads `kwh` (review Q1). `meter_billed` then prints equal pairs for those
    rows. `kwh_model` and plan `kwh` stay the model's: the drift is meter against model, which is the story.
  - *Stops.* Any H-check or C-DD check that then fails (H5's anchor "within 5 % of `kwh_model`" first) stops for
    the Architect, with the figures; nothing is tuned. The packet lists every moved figure.
  - *DD4b.* No change on that branch.
  - *Units.* DD6 4.75 → **5.25 u** (DD6.4 below).

- **D-DD.158 DD4b Q2: the EV month carries the two hour-window sums, and C-DD7's EV window clause goes live in a DD4b
  follow-up before DD6** (schema; amends D-DD.99's EV `<month>`; +0.25 u DD4b).
  - *Why.* D-DD.20 lists `kwh_2200_2400` and `kwh_0000_0500` as metered leaves and `rows_ev_depot.py` reads them
    (`scheduled_kwh_night`), but D-DD.99's EV month has no field, so they are written `metered: null`. The writer
    already holds the depot import by minute. Doing it now avoids a second 26-minute EV plant run in DD6.
  - *Rule.* D-DD.99's EV `<month>` gains `"windows": {"2200_2400": <kWh>, "0000_0500": <kWh>}`: sums of the depot
    import over local-clock minutes [22:00, 24:00) and [00:00, 05:00) of each day in the month, exact, rounded once
    to the month's kWh precision. The key set stays fixed per vertical (an absent or extra key refuses
    `TEL_FOUNDATION`). `meter_billed` writes them as `metered`. C-DD7's EV clause adds: each window equals
    the sum of `site-meter/import` over the same minutes, exactly.
  - *Where.* A DD4b follow-up on its branch after the review fixes (`task/DD4b-ev-measured`), merged with DD4b,
    before DD6 builds. DD4b 4.75 → **5.0 u**.

- **D-DD.159 DD4b Q3: C-DD5's cadence table is ratified; states and events are "ungridded"** (wording; amends
  D-DD.124 R2196 and spec §4.3's reading words where they say "on change"; 0 u).
  - *Why.* The writers repeat an unchanged state every minute or every 5 minutes; a strict "only on change" rule
    would fail correct writers. Counting a sample at a slot's start is faithful to the readings.
  - *Rule.* D-DD.124's parenthesis reads "(5-minute means; states and events ungridded: an unchanged state may
    repeat)". The checker's `CADENCE` value `ON_CHANGE` is renamed `UNGRIDDED` in DD4b's L-fix commit (decided, not
    a preference: the label must say what is judged).

- **D-DD.160 DD4b Q4 and the review's `measured.json` note: the hand-offs are written on the cards. DD5b alone owns
  C-DD7's mini-grid clause and the `stored_books` fetch; DD6 runs one writer process per tenant** (sequencing;
  +0.25 u DD5b).
  - *DD5b (card line, unit 2).* `stored_books` fetches TARIFF_SCHEDULE, FLEET_ROSTER and DEPARTURE as well. C-DD7's
    mini-grid clause (load served + unserved = `delivered_kwh`, exactly) reads unserved from the loaded world's
    `<slug>/telemetry/measured.json` `unserved_kwh` (no readings channel carries it). The pending text "DD3b/DD5"
    becomes "DD5b". DD5b 3.75 → **4.0 u**.
  - *DD6 (card line, unit 3).* D-DD.99 makes `measured.json` one file per tenant, written by the frame. The world
    build runs each tenant's Sites in one writer process; several processes write several files and `exports
    --telemetry` refuses `EMU_MEASURED` (exit 3). The build asserts one `measured.json` per tenant before exports.
  - *Units (D-DD.155 to D-DD.160).* DD 54.0 (after D-DD.156) → **55.0 u in twelve parts**: DD3d 2.5, DD4b 5.0,
    DD5b 4.0, DD6 5.25.

- **D-DD.161 DD5a BLOCKER and deviations 1, 3, 4: D-DD.138's v4 publish is for world conversions only (narrowing
  confirmed); the Foundation's `site-meter` stands; the sealer writes canonical decimals; an EV session has one id,
  the pack's, carried by the writer and copied by the sealer** (BLOCKER, protected seam `contracts/` and the binding
  service; amends D-DD.138 and D-DD.139's EV-id bullet; +0.25 u DD4b, +0.25 u DD5a).
  - *Deviation 5, the blocker: confirmed.* D-DD.138's finding was the world path (`onboard_operator apply
    --bindings`, D-DD.36); its rule was worded wider than its cause. The Lab's W2-02 design (a v3 conversion, then
    a v4 PUBLISH revision) is existing, tested behaviour and the rule must not change it. Rule: `convert(...,
    world_conversion: bool = False)`; v4 metadata is published at conversion only when `world_conversion` is True
    **and** the role set is v4 (`cold-roles-1`, `ev-roles-1`), from that role set's closed table. Only
    `onboard_operator apply --bindings` passes True. Mini-grid world role sets stay v3 either way. Test: the 24 Lab
    tests pass unedited, and a plant passing True from a Lab replay fails one of them.
  - *Deviation 1: confirmed.* D-DD.138 said the table is generated from the Foundation; the depots' `/2` files and
    conversions declare `site-meter`, so the entry is `("site-meter", "import")`. "`site-meter-1`" in D-DD.138
    (from D-DD.38) is wrong text; generation wins over a typed name (W6: no typed device name in a ruling stands
    against the Foundation).
  - *Deviation 2: accepted as built* (recomputed v3 formation from stored rows, plus no v4 rows), since
    `bindings_sha256` carries fresh UUIDs.
  - *Deviation 3: confirmed.* The readings writer prints exact millesimal text ("4.000"); envelopes admit only the
    canonical spelling. The sealer writes the same value canonically ("4"; "0" for zero; no exponent). It asserts
    `Decimal(out) == Decimal(in)` and `is_canonical_decimal(out)` (imported from `source_envelope_v3`) per value.
    Readings files are unchanged. Every check that compares a reading to a book compares `Decimal` values, never
    strings (C-DD7, C-DD8, D-DD.157's leaves).
  - *Deviation 4, and the class behind it: one id per EV session.* D-DD.139 had the sealer form a new
    `ev_session_id(foundation_digest, connector, ordinal)`. DD4b's writer already carries the pack's id
    (`scoped_session_id`, Q3: `ev-` + SHA-256 of `[scenario_sha256, "session", private_label]`) on each session event
    with `connector_id` (D-DD.123). Two formations would give one session two ids, so the event and the connector's
    energy would not correlate. Rule: the pack's id is the only one.
    - DD4b follow-up (with D-DD.158, +0.25 u, DD4b 5.0 → **5.25 u**): a connector measurement row inside a session
      carries `"session": {"session_id", "connector_id"}`, the same pair as that session's events. The depot import
      and rows outside a session carry none.
    - DD5a (fix round, +0.25 u, DD5a 3.5 → **3.75 u**): `ev_session_id` is withdrawn from `contracts/`. The sealer
      copies `session_id` and `connector_id` from the event object or the row's `session` object, and
      `correlation_id` = `session_id`. An EV event without a session forms its ids as a cold event does (D-DD.91,
      `cold_event_id` / `cold_correlation_id` over its `correlation`). `WORLD_SEAL_EV_EVENT_PENDING` is removed. An
      EV event that has neither a session nor a `correlation` refuses `WORLD_SEAL_EV_UNCORRELATED`, exit 2. Parity
      test on hand rows in DD4b's shape: one session event and one in-session connector energy give equal
      `session_id` and `correlation_id`.
  - *Test placement (standing).* The dependency-direction guard forbids `gateway`, `host` and `simulator` imports
    anywhere under `backend/`, tests included. A parity test against the gateway lives in `host/tests/`, as DD5a
    built it.

- **D-DD.162 The card sweep: the remaining cards name the same five kinds of fact** (cards; 0 u). Each card gains a
  "Facts the code fixes" list: (1) protected existing behaviour the part must not change; (2) device and channel
  names as the Foundation declares them, never as a ruling typed them; (3) decimal spelling: compare `Decimal`
  values, write canonical text; (4) the keys an id is formed on; (5) where a test may live under the import guard.
  DD5a gets the five DD5a facts above. DD5b and DD6 get their own, below. Swept: neither card types a device name or
  an id key. Both now state the import guard and the Decimal rule. Each also names the protected behaviour it
  touches: for DD5b the `/1` definition path and the Lab replays; for DD6 the owner's walk and ports
  5490/8990/8992, already stated.
  - *DD6 D-DD.157 precision.* `history.json` cold `kwh` leaves are whole kWh. The meter value is written rounded
    half-even to whole kWh (1659.750 → 1660), the History series' precision. The bill keeps the exact meter kWh.
    The two are one figure at two precisions, and `meter_billed` prints the pair.
  - *Units (D-DD.161, D-DD.162).* DD 55.0 → **55.5 u in twelve parts**: DD4b 5.25, DD5a 3.75.

# DD rulings, round 24 (D-DD.163): a month's fuel cost is the fuel burned, not the fuel bought

Architect (Claude, DD lane), 2026-11-23. Read: `DD3b-handoff.md` "Run 3 state" and `packet-DD3b.md` reach table on
`task/DD3b-mini-plant` (22cf40ec3); D-DD.18, D-DD.92, D-DD.130, D-DD.131; `structure/rows_mini_grid.py` (`fuel_cost`
= `diesel_l * diesel_price`, `stated_by` EXPENSE (FUEL)), `structure/evaluate.py` `_stated_node` (a stated record
governs the node), `structure/sources.py` `STATED_STATE` and `ASSUMPTION_WORDS`, `structure/money.py`
(`_ROWS["fuel_cost"]`, `_diesel_price`), `structure/reconciliation.py` (`used_lines`, `HEADING_WORDS`),
`deep_dive/tables.py`, `rehearsal_check.py` G4/G5, `backend/tests/test_ddr_rehearsal_postgres.py` and
`fixtures/ddr/lakeside-2026-10.expect.json`. No run was made; no database touched. The owner is informed; the
headline the owner was told (about +2,135) is what the screen will show.

- **D-DD.163 The product's month fuel cost is consumption × price, the node's own expression. The fuel invoices
  state purchases, a different quantity, and stop stating `fuel_cost`. A month with no invoice prices its fuel at
  the Site's declared diesel price, labelled Assumed. The statements and screen literals follow** (model, W6 class;
  completes D-DD.92 and D-DD.130 in the product; amends D-DD.130's C-DD4 clause; adds DD3d.4).
  - *What is wrong.* D-DD.92 made purchases and consumption two quantities, and D-DD.130 put the purchases in the
    books. The product's `fuel_cost` node, though, is `diesel_l × diesel_price` (consumption) with a `stated_by`
    record: the month's fuel invoices. In `_stated_node` the record governs, so the served fuel cost is whatever
    was bought that month: Kisiwa 1,040, Kobo 500, Mto nothing. `M` and the model say 1,175.20 / 792.50 / 40.00.
    `stated_by` assumed purchases equal consumption, which is only true for a Site without storage. With a tank,
    cost to serve and contribution would swing with delivery dates: Mto would show $0 of fuel while burning 32 L.
    The model's figure is the loyal one. The cause is two figures for one quantity, so the fix is in the model.
  - *Rule (product).*
    - `fuel_cost` is no longer a stated node. `rows_mini_grid.py` drops its `stated_by` (structure version 5;
      revenue, `metered_kwh` and `billed_kwh` keep theirs), and `STATED_STATE["MINI_GRID"]` drops `fuel_cost`.
      The node folds from `diesel_l × diesel_price`, with `diesel_l` the readings' litres split (D-DD.18). No
      `diesel_l`, no fuel cost ("not available yet"; never the invoices instead).
    - The invoices keep two jobs, under their own name:
      - `diesel_price`, unchanged (D-4B.6): invoice spend ÷ invoice litres in a month with invoices.
      - Fuel bought. `money._ROWS["fuel_cost"]` and `READ_AS["fuel_cost"]` are renamed `fuel_bought`, with the
        literal FilledBy("COMMERCIAL_RECORD", "EXPENSE (FUEL)", "Fuel invoices for the month"). It is not a
        structure row.
    - Reconciliation (`structure/reconciliation.py`) still compares the management accounts' fuel figure with
      the recorded invoices, a completeness check on the books. Its heading key becomes `FUEL_BOUGHT`, label
      "Fuel bought (invoices)"; the statement CLI's `--fuel-cost` flag and the stored field keep their names (a
      data contract; the label carries the meaning).
    - Deep dive (`deep_dive/tables.py`): the `fuel_cost` step's value is the node's. Its evidence stays
      `FUEL_INVOICES`, now as the price's evidence, beside the litres.
  - *Mto's price.* No invoice in the month gives the product's existing fallback: the Site's declared
    `diesel_price_per_litre`, ASSUMED, worded "Declared diesel price per litre, not a fuel invoice". The fuel in
    Mto's tank was bought before the span, so that is the honest price. The world declares it: DD3d.4 records
    Lakeside's per-Site declared price from `M`'s `prices.diesel_usd_per_l` (Kobo 1.25, Kisiwa 1.30, Mto 1.25)
    through the product's existing price-assumption path (the one PR1/PR2a write; the builder names the function
    in pre-flight; if no loader-callable path exists, stop for the Architect). G4 (`rehearsal_check.py`) changes:
    a Site-month with a fuel invoice needs `commercial:` sources as today; one without needs the declared price,
    evidence ASSUMED, and prints "declared, no fuel invoice this month". A missing price is still a FAIL.
  - *Statements (DDR S5/S8).* The management accounts state fuel bought, compared with the recorded invoices. The
    rehearsal's designed beats stay as offsets from the recorded total: S8 final = invoices + 5.00 (MATCHED within
    the 1 % tolerance); S5 draft = invoices + 105.00 (NOT_MATCHED). On today's books, invoices are 1,540.00, so
    S8 is **1,545.00** and S5 is **1,645.00** (were 5,000 / 5,100 against 4,995). The test computes them from the
    expect file's invoice total, never types them. Revenue 9,700.00 keeps its offset from the served revenue the
    same way.
  - *Screen literals (expect file).* Each literal is re-pinned to the served value (D-DD.93), and the packet maps
    each to its `M` figure. Projected from `M` rev 16.20:
    - Portfolio fuel: Actual **$2,007.70** · Target $4,240.00 · Difference **−$2,232.30**; effect on contribution
      **+$2,232.30**.
    - Headline: contribution **+$2,135.30** against target (actual 4,430.30, target 2,295.00); Grow −$97.00,
      Optimize +$2,232.30.
    - The sentences are the product's own copy for a favourable gap, not hand-written. A served figure that
      differs from `M` by more than money rounding stops for the Architect.
  - *Checks.* C-DD4 judges mini-grid `diesel_l` and `fuel_cost` again (served = `M`), reversing D-DD.130's drop.
    `EMU_FUEL` stays Σ invoices = fuel bought. `test_ds4_world_postgres` t12 then compares like with like.
  - *Owner, plainly.* A month's fuel cost is now what the generators burned, priced per litre. Fuel deliveries
    are shown separately as "fuel bought". The Portfolio headline stays at about **+2,135 above target**, as you
    were told. Without this ruling the screen would have shown about +2,603, because it was counting October's
    deliveries (1,540) instead of the fuel burned (2,007.70). Mto's fuel is priced at its declared 1.25 per litre,
    marked Assumed, since it bought no fuel in these months.
  - *Where and size.* DD3d.4 (product reader, discovery review with DD3d): +1.75 u (structure v5 and money rename
    0.5; reconciliation and deep-dive label 0.25; declared prices recorded and G4 0.5; re-pins, DDR expect file,
    C-DD4 restored 0.5). DD3d 2.5 → **4.25 u**; DD 55.5 → **57.25 u**. DD3b3 merges with exactly the seven DDR
    rehearsal failures and `test_ds4_world_postgres` t12 listed as known, closed by DD3d.4. DD3d follows DD3b3
    directly. Any other failure still blocks.

# DD rulings, round 25 (D-DD.164 to D-DD.165): the history seed loop, and Kisiwa's candidate share

Architect (Claude, DD lane), 2026-11-23. Read: `review-DD3b.md` (8ebad03df) H1, M1, Q1, Q2; D-DD.30, D-DD.102 (the
`physical` read set), D-DD.92, D-DD.130, D-DD.131, D-DD.144, D-DD.151; `simulator/assetops_simulator/world/scope.py`
(`scope_input`: the whole `site_doc["period"]` in the digest), `world/history.py` (`_Scope`, `october`, `_side`, the
family seeds `seed(digest, key, name)`), `telemetry.books_for` (what the mini writer reads from history:
`delivered_kwh`, `unexplained_l`), `telemetry_cold.cold_books_for` (the cold ledger reads history); the Lakeside rules
in `M`'s `history.rules`. No run was made; no database touched. The owner is told the final Kisiwa share (D-DD.165).

- **D-DD.164 Q1 (BLOCKER), H1: a history seed never covers a value written back from the run it seeds. The
  run-written October keys leave the scope digest; they stay readable as values. Acceptance is a fixed point
  proved by a second pass** (model, W6 class of D-DD.102; amends `scope.py`'s digest input and D-DD.131's test).
  - *The loop.* The October fuel leaves are written into `M` from the pure run (D-DD.131). `scope_input` hashes the
    whole `period`, and that digest seeds every July-September jitter draw. So writing the leaves re-seeds the
    history, which moves `delivered_kwh`, which is the writer's load. That moves the run, and so the leaves. With a
    seed that depends on its own output there is no fixed point; re-running cannot close it.
  - *Which break, and why.*
    - Taken: the run-written keys leave the digest. A seed decides the scope's jitter. A figure the run computes
      is a value, not part of the scope's identity. This is D-DD.102's rule (the digest covers only what is the
      scope's own input), applied to `period`.
    - Rejected: freezing July-September. It turns generated history into typed data, so a correction elsewhere
      would never reach it. And it breaks `scale`'s stated link to October.
    - Rejected: removing all of `period` from the digest. That re-seeds the cold and EV histories that the
      merged DD4 writers read (the cold ledger reads history), so it would move worlds with no loop.
    - Not a loop: history's `necessary_l` / `candidate_l` = October × family weight × jitter (`scale`). They move
      with October as values. No writer reads them (D-DD.18, D-DD.92: the writer reads `delivered_kwh` and the
      declared `unexplained_l`), so nothing feeds back.
  - *Change (`world/scope.py`).*
    - `RUN_WRITTEN: dict[str, dict[str, tuple[str, ...]]]`, by vertical and side, declared beside `PHYSICAL_READS`.
      Each entry is a period key whose value is written from a run:
      - `MINI_GRID`, `actual`: `diesel_l`, `necessary_l`, `candidate_l`, `diesel_cost`, `contribution`, `variance`
        (D-DD.131's restated leaves and the identities computed from them).
      - `MINI_GRID`, site-level: `fuel_balance`, `bridge`, `findings_expected` (the blocks D-DD.131 restates).
      - `COLD_CHAIN`, `actual`: `kwh` (the meter's, D-DD.144). `EV_DEPOT`, `actual`: the metered leaves of D-DD.20
        that `M` takes from `measured.json`; the builder lists them from D-DD.20 and D-DD.158 in pre-flight.
      - A key not in the table stays in the digest.
    - `period_input(site_doc, vertical) -> dict` is `period` with exactly those keys removed (a missing key is
      skipped, never an error). `scope_input` writes `"period": period_input(...)`. `_Scope.october` still reads
      the full `site_doc["period"]`, so values are unchanged as inputs.
  - *Moves (once).* The mini-grid digests change once (their run-written keys leave), so Lakeside's July-September
    jitter is re-drawn once more. After that, writing the leaves cannot re-seed. Cold and EV digests change only if
    their `RUN_WRITTEN` keys are in `M`'s period today; any moved cold or EV leaf that a cold or EV writer reads
    (crate days, ledger movements, roster) **stops for the Architect** before anything is written. The packet lists
    every moved leaf, grouped by Site.
  - *Acceptance (one pass, proved by a second).*
    1. `world_history.py generate` with the new digest.
    2. `dd3_pure_run.py --restate-notes --write` at all three Sites.
    3. The notes run and `--leaves --write`.
    4. `M` written from the tool (rev bump).
    5. `world_history.py generate` again: **`history.json` byte-identical to step 1** (the fixed point).
    6. `--restate-notes --check` and `--leaves --check` exit 0 at Kobo, Kisiwa and Mto.
    7. The D-DD.30 chain (view, goldens, fixtures, derived values) and re-pins (D-DD.93).
    If step 5 differs, stop: the table missed a key. The `--check` logs and the two `history.json` hashes go in
    the evidence.
  - *Guard (cheap, in the default suite).* `simulator/tests/world/test_scope_run_written.py`: on a copy of the view,
    changing each `RUN_WRITTEN` key of Kobo, Kisiwa and Mto leaves every scope digest and every July-September jitter
    factor equal. Changing a non-listed key (Kobo `delivered_kwh`) changes the digest (plant). D-DD.131's `M` test
    keeps comparing with `fuel-leaves.json`. The record is then valid because step 6 is in the packet, and a merge
    that touches `M`'s fuel leaves reruns step 6 (coordinator merge check for DD parts).
  - *Where and size.* The DD3b3 fix round (Opus: model change): +0.75 u (scope table and guard 0.25; the pass,
    regeneration and re-pins 0.5). DD3b 6.5 → 7.25 u over three parts; DD 57.25 → **58.0 u**. The coordinator may run
    it as its own commit series in DD3b3.

- **D-DD.165 M1, Q2: Kisiwa's candidate share is reported from the final pass, old → new with the cause. The owner
  is told in plain words, and the story sentence is restated from the printed figures** (story; amends D-DD.151's
  "about a tenth" sentence; no bound, nothing tuned; 0 u).
  - *Why it moved.* The measure (generator on while PV ≥ 1.1 × load) is a threshold. Many of Kisiwa's minutes are
    cycle-charge tails at 10:00-10:40, with PV about 21.6 kW against load 18.4-19.0 kW: just at 1.1 ×. A 1 % change in
    the load draw tips them over. H1's re-seeding moved the load about 1 %, and July went from 0.36 % to 18.80 %. That
    is the measure's real sensitivity, not a plant change. Bounding it, or choosing a seed, would be fitting.
  - *Rule.* After D-DD.164's pass, the packet prints July-October shares as D-DD.151's figures (0.36 / 11.27 / 0 /
    10.17 %), then run 2's (18.80 / 17.77 / 0 / 10.67 %), then the final ones. The cause is stated as above. The
    figures stay the final run's, rounded to whole percent in prose. The OR-MG-2 wording and `M`'s Kisiwa
    sentences quote the final figures, and D-DD.151's "about a tenth in August and October" is replaced by them.
  - *Owner, plainly (the coordinator relays this with the final numbers).* "Kisiwa's generator sometimes runs to
    finish charging the battery in mid-morning, when the sun is only just enough to carry the load. Whether those
    minutes count as avoidable depends on a margin of about 10 %. So a 1 % change in the month's demand can move
    the share a lot: it was about 0 % / 11 % / 0 % / 10 % (July to October) when you accepted the story, and is now
    [final]. Nothing was adjusted to get either figure. The product shows the share it measures." If the final
    August and October are no longer near 10 %, or July is well above 0 %, the owner is asked whether the story
    sentence should change. The default is that the sentence states the measured share, whatever it is.

# DD rulings, round 26 (D-DD.167 to D-DD.174): DD5a's re-seal question; DD3d's build card (fuel records' times, the declared prices, the run-rate plan's seed, the split); the story clock WK-SC; the card sweep

Architect (Claude, DD lane, fresh hand-off), 2026-11-23. Read: `.agent/codex-handoff.md`; owner `owner-dd-strategy-2026-11-22.md`
O1, O2 and `owner-demo-data-answers-2026-11-22.md` (D-DD.166 approved); `review-DD5a.md` (branch `task/DD5a-load`,
2805d367a) residual risk and question 1; `DD3b-handoff.md` on `task/DD3b-mini-plant` (b3478de5f, `M` rev 16.23);
`assessment-budget.md`; D-DD.135 to D-DD.137, D-DD.140, D-DD.153 to D-DD.166; code on main (87067a97f):
`load_world_inputs.py` (`_seal_tenant`), `tools/world.py` (`drop_db`, the inputs folder), `work/operational_entry.py`
(`compose_entry`), `work/service.py` (`post_operational_record`), `work/adapters/postgres_work_store.py`
(`command_now`, `test_db_clock_override`), `fuel_balance/rules.py` (`limitations`, DELIVERY_RECORDED_LATE),
`prepare_clock.py`, `tools/demo_story_clock.py`, `publish_assumption.py` (tenant check), `structure/money.py`
(`_diesel_price` fallback), `structure/sources.py` (`ASSUMPTION_WORDS["diesel_price"]`), `world/scope.py`
(`RUN_WRITTEN`, DD3b), `actions/agreed.py` (due check, OVERDUE), migration 0070 (`due_on >= created_at::date`),
`decisions/records.py`, `decisions/run.py` (one `now` for `known_at` and `run_at`), migration 0072 (act-time columns),
`accounts/permissions.py`, `structure/levers.py`, `specs/6h-named-option-levers/spec.md` §7, `M` `demo_workflow`,
`frontend/src/ui/sharedRange.ts` (`Date.now()` defaults). No run was made; no database touched.

- **D-DD.167 DD5a review Q1: `sealed/` is keyed by the database it was sealed against; a refusal holds within that
  database's lifetime; a dropped rung takes its sealed folder with it** (model; amends D-DD.140's `sealed/` bullet;
  +0.25 u DD5a, +0.25 u DD5b).
  - *Why.* D-DD.140 says sealed bytes are "a function of the inputs and the database ids". The ids are `uuid4` at
    onboarding (`binding_service.py:504,627,744`), and `tools/world.py` reuses `inputs/<digest>` when it exists. So a
    folder keyed only by the inputs holds the previous database's bytes, and every rebuild on unchanged inputs
    refuses `WORLD_SEALED_BYTES_DIFFER`. The folder's key must be what its content depends on: inputs (the folder's
    parent) and the database's seal context. Clearing `sealed/` by the caller (rejected) throws away the check
    D-DD.140 wants on a same-database re-run. Keying by the database name (rejected) fails too, since a rung is dropped and
    recreated under the same name (`name_for(prefix, rung, key12)`).
  - *Rule (DD5a, `load_world_inputs.py`).* `_seal_tenant` computes `context12` = the first 12 hex of SHA-256 over the
    canonical JSON (sorted keys, no spaces) of the sorted list of `[site_code, gateway_id, source_id,
    binding_set_id, foundation_digest]` for every Site it seals, all as text, from the resolved seal context. It
    writes to `<slug>/sealed/<context12>/`. That folder absent: write all. Present: re-seal and compare, refusing
    `WORLD_SEALED_BYTES_DIFFER <name> re-seal` or `... stray` exactly as today. The output line adds
    `"sealed_dir": "<slug>/sealed/<context12>"`. `sealed/` stays outside the inputs digest. A sibling
    `<context12>` folder is never read or deleted by the loader.
  - *Rule (DD5b, `tools/world.py`).* The rung manifest records every `sealed_dir` from the load step's output line.
    C6 globs only the manifest's `sealed_dirs` (`<dir>/*.batch.json`), not `*/sealed/*`. `drop_db(name)` then removes
    each `sealed_dir` recorded in that rung's manifest, unless another live rung's manifest records the same
    folder. The check clone is a copy of L2 with the same ids, so it shares L2's folder.
  - *Tests.* DD5a: (a) fresh database, unchanged inputs, existing folder of another context: exit 0, a new
    `<context12>` folder; (b) same-database re-run: same folder, no new bytes; (c) a changed byte in the folder: refuses
    `re-seal`; (d) a stray file: refuses `stray`. DD5b: C6 judges only recorded folders (a planted extra folder with a
    bad batch is not judged); dropping L1 removes L1's folder and keeps L2's.

- **D-DD.168 Fuel records carry their own times: each is recorded through the product's operational path at its
  record time, on the prepare clock** (model, W6 class of D-DD.154; amends D-DD.154's rule bullets 1-2; +0.25 u DD3d).
  - *What D-DD.154 missed.* The operational path stamps `recorded_at` with the work store's `command_now`, the
    database time of the load, weeks after the night. `fuel_balance.rules.limitations` flags DELIVERY_RECORDED_LATE
    whenever a delivery's `root_recorded_at` is after the night's end, so every world delivery night would read
    "recorded late" on screen. The world's operator recorded each note when it arrived. The precedent exists:
    `tools/demo_story_clock.story_commands` sets the work store's `test_db_clock_override` after
    `prepare_clock.require_prepare_database` (DD1b1-R Q1, Q2). The fix reuses it on merit.
  - *Guard, widened on merit (`prepare_clock.py`).* `PREPARE_DATABASE` also admits the world rung names
    (`^assetops_[a-z0-9]{1,24}_audit_(l0|l1|l2)_[0-9a-f]{12}$` and `^assetops_[a-z0-9]{1,24}_audit_c_[a-z0-9]{1,20}$`,
    the patterns `tools/world.py` makes), and `require_prepare_database` refuses any name for which
    `database_target.is_operator_name` is true, before the pattern. It is still the one check.
  - *The file (`world/exports_fuel_records.py`, new; written by `world_history.py exports` when `--telemetry` is
    given, for each mini-grid tenant, beside `measured.json`'s books).* `<out>/<slug>/fuel-records.json`, schema
    `assetops.world-fuel-records/1`: `{"schema", "tenant", "sites": [{"site_code", "records": [...]}]}`, each record
    `{"source_record_id", "kind", "taken_at_local", "litres", "ticket_reference", "recorded_at"}`:
    - `TANK_DIP`: one per Site at `YYYY-MM-01T00:00` local for 2026-07-01 to 2026-11-01. `litres` is the writer's
      published tank level at that step (the readings file's `fuel-tank` level row at that instant), exact as the
      readings print it (at most 3 decimals). `ticket_reference` null; `recorded_at` = the same instant (ISO with
      offset). `source_record_id` `<site>:dip:<YYYY-MM-DD>`.
    - `FUEL_DELIVERY`: one per fuel EXPENSE row of the books (D-DD.92, D-DD.130: the restated notes), at the row's
      `clocks.occurred_at` with its `quantity.value`. `ticket_reference` = `FN-<site code>-<YYYYMMDD>-<k>` (k the
      note's ordinal that day, from 1; matches `operational_entry.TICKET`). `recorded_at` = `occurred_at`, except the
      note D-DD.53's module table dates for OOO-1 (Kobo, 26 Oct), whose `recorded_at` is OOO-1's `recorded`
      (2026-11-04T10:00 local, from the same table, never typed). `source_record_id` = the EXPENSE row's.
    - A missing level row at a dip instant refuses `EMU_FUEL_RECORDS <site> <instant>` (exit 3).
  - *The loader (`backend/assetops_backend/load_fuel_records.py`, new; `load_fuel_records(dir, tenant) -> dict` and
    `python -m assetops_backend.load_fuel_records --dir DIR --tenant SLUG`).* Under `world.env` for the tenant:
    `require_prepare_database(DATABASE_URL)` first (refusal exit 2, nothing written). A holder clock
    `RecordClock` is set on the work store built by `work.composition.build_work_store` (the
    `story_commands` swap pattern, local to this module). Per record, in file order: the clock is set to the record's
    `recorded_at`; the body `{"entry": kind, "value": litres, "taken_at_local": ..., "ticket_reference": ...,
    "idempotency_key": "oprec-entry-" + sha256(source_record_id)[:32]}` goes through `validate_entry`,
    `entry_site_context` and `compose_entry(..., with_actor=True)`, then `post_operational_record(tenant_id, site_id,
    command, ENTRY_PRINCIPAL)`. 201 or 200 (re-run, same hash) both count; any refusal exits 2 with its code and the
    record's id. Output: one JSON line `{"tenant", "recorded", "already", "by_kind"}`. D-DD.154's "Shift operator"
    actor is withdrawn: the product's own entry actor (`ENTRY_ACTOR`) is the actor; the screen shows its words.
  - *Tests.* `backend/tests/test_dd3d_fuel_records_postgres.py`: one Site's file loads; the night check's read sees
    each record with `root_recorded_at` = its `recorded_at`; only OOO-1's night carries DELIVERY_RECORDED_LATE; a re-run
    records nothing new; a database name outside the guard refuses with nothing written (plant: an
    `assetops_op_*`-style operator name refuses even if it ends `_test`). Writer: `simulator/tests/world/
    test_dd3d_fuel_records_file.py` (dip count 5 per Site, dip litres equal the readings' level rows, deliveries equal
    the books' FUEL rows by id and litres).

- **D-DD.169 Lakeside's declared diesel prices are published by the existing assumption publisher, on the served
  tenant** (model; names D-DD.163's "builder names the function"; 0 u, inside DD3d.4's 0.5).
  - *Finding.* `publish_assumption fixture --site CODE --file F` is the loader-callable path (PR1/PR2a; the money
    fallback reads its `diesel_price_per_litre` series, `sources.PRICE_KEYS`). It refuses any `--tenant` other than
    the development tenant (`publish_assumption.py:127`), so it cannot publish to `lakeside-power`.
  - *Rule.* The check compares with `config.served_tenant_slug()` (the tenant `ASSETOPS_TENANT_SLUG` configures, the
    development tenant when unset), and `--tenant` defaults to it. The message keeps its words with "served" for
    "configured development". Three fixture files, `backend/conversions/world/lakeside-power.diesel-price.<SITE>.json`
    (`demo-diesel-price-publications` format version 2): one step `v1`, `INITIAL`, `USD`, value from `M`
    `prices.diesel_usd_per_l` of that Site (a parity test reads `M`), `basis` `AUTHORED_ESTIMATE`, `source_reference`
    "Declared diesel price per litre for this Site (world declaration); not a fuel invoice", `valid_from`
    `2026-06-30T21:00:00Z`, `valid_to` null, idempotency key `world-diesel-price-<site lower>-v1`. The fallback's
    screen words stay `ASSUMPTION_WORDS["diesel_price"]`. DD5b's L1 gains `L1.prices:lakeside-power`, three
    `publish_assumption fixture` calls under `world.env` (one line in its step list; no unit added). The DDR
    rehearsal Postgres test publishes the same three files in its setup.
  - *Tests.* `test_s4_assumptions_postgres.py` gains: with `ASSETOPS_TENANT_SLUG=lakeside-power` a publish to that
    tenant succeeds; a different `--tenant` refuses (exit 3, nothing written); unset, the development tenant behaves
    as today.

- **D-DD.170 The run-rate plan leaves are run-written: they leave the scope digest, and D-DD.164's fixed point is
  proved again after them** (model, W6 class of D-DD.164; amends D-DD.166's "where the figure comes from"; +0.25 u DD3d).
  - *Why.* D-DD.166 makes October `plan.diesel_l` a function of July-September deliveries, which come from the pure
    run, which reads `delivered_kwh`, which the history draws with a seed from the scope digest, which hashes
    `period`, plan included. Writing the plan litres would re-seed the history: D-DD.164's loop on the plan side.
  - *Rule.* `RUN_WRITTEN["MINI_GRID"]` gains side `plan`: `diesel_l`, `necessary_l`, `candidate_l`,
    `unexplained_l`, `diesel_cost`, `contribution`, `variance` (a key `M` does not carry is skipped, as today).
    `dd3_pure_run.py --leaves` records, per Site in `fuel-leaves.json`, `quarter`: `{"tank_open_jul",
    "deliveries_jul_sep", "tank_open_oct", "consumed_jul_sep", "contingency": "1.10", "plan_diesel_l"}` (fractions as
    the ledger prints them; `plan_diesel_l` whole litres, half-even), with `tank_open_jul` the run's ledger at
    2026-07-01 00:00 local and `deliveries_jul_sep` the sum of `fuel-notes.json` notes in July-September. The test of
    `M` asserts `M`'s plan litres equal `plan_diesel_l` (D-DD.93), never typed. D-DD.164's acceptance steps 1-7 are run
    again after `M` is written, including step 5 (second generate byte-identical) and step 6 (`--check` exit 0).
  - *Guard test.* `test_scope_run_written.py` gains the `plan` keys of Kobo, Kisiwa and Mto (digest and July-September
    jitter unchanged); the plant (Kobo `delivered_kwh`) still moves the digest.

- **D-DD.171 DD3d is renumbered to the build order and split into DD3d-a (2.75 u) and DD3d-b (3.75 u)** (sequencing;
  amends spec §7 DD3d; W4: a part over 6 u is split).
  - *Units, in build order.* DD3d.1 the floor (D-DD.153, 1.25); DD3d.2 fuel records (D-DD.154 with D-DD.168,
    1.25); DD3d.3 H5 on the floor (D-DD.156, 0.25); DD3d.4 fuel cost is burned × price (D-DD.163 with D-DD.169,
    1.75); DD3d.5 run-rate budget (D-DD.166 with D-DD.170, 2.0). Spec §7's old order (records first) is replaced;
    D-DD.156's "DD3d.2" reads "DD3d.1" (the `/2` declarations H5 reads).
  - *Parts.* **DD3d-a** = DD3d.1-3, 2.75 u, branch `task/DD3d-fuel-floor`: the reader's floor and the records it
    needs. **DD3d-b** = DD3d.4-5, 3.75 u, branch `task/DD3d-b-fuel-cost`: the fuel figure and the budget, re-pinned
    once at the end of DD3d.5 for the plan-side literals. Both after DD3b merges; DD3d-b merges after DD3d-a; both
    before DD5b. They may be built side by side (shared files `tools/dd_check.py`, `M`, `check_manifest.py`: merge
    main, rerun the reach set). Each has one discovery review (money-adjacent readers).
  - *Size.* DD 58.0 → 59.75 (D-DD.166) → **60.75 u in thirteen parts** (D-DD.167 +0.5, D-DD.168 +0.25, D-DD.170
    +0.25): DD3d 6.5 (a 2.75, b 3.75), DD5a 4.0, DD5b 4.25.

- **D-DD.172 The story clock WK-SC: operating-world time and system time are two clocks; the story clock moves only
  the first** (model, owner-approved scope O1; amends D-DD.137's "every command and read that takes `system_clock`";
  3.0 u, outside DD). Spec: `specs/DD-demo-data/spec-WK-SC.md`; card `cards/WK-SC.md`.
  - *Why D-DD.137 is narrowed.* Every world row is loaded at wall time: `received_at`, `recorded_at` and `known_at`
    reads are system time. Decisions read their inputs with `known_at = now` (`decisions/run.py`), so moving every
    clock to 6 Nov would hide every loaded row from every read. Two quantities had one clock. The rule classes each
    clock read by what it is compared with or stamped beside:
    - **World time (story clock):** a person's act time (`agreed_action.created_at`, `decision.prepared_at`,
      `option_one_off.declared_at`, the 6h option-record time, `option_evaluation_run.run_at`,
      `decision_choice.chosen_at`), a due or overdue judgement (`agreed.py` step 8, `state_code`), a verification
      `today` (`verification_families`), and the screen's calendar (range presets).
    - **System time (unchanged):** `received_at`, `recorded_at`, `command_now`, `known_at` of any read or run,
      leases, cursors, source health (it compares `received_at`).
  - *Rule.* `prepare_clock.story_now()` reads `ASSETOPS_STORY_NOW` (ISO instant with offset, whole seconds), only
    after `require_prepare_database(DATABASE_URL)` (D-DD.168's widened check). Unset gives None (production: wall
    clock everywhere). Set and refused, malformed, or later than the wall clock: `PrepareClockRefused` at
    composition; a serve does not start, a CLI exits 2. It runs: value + (monotonic now − monotonic at first read),
    truncated to whole seconds. Only the world-time sites above read it, through their compositions; system-time
    sites never import it. Details, guards, tests and gates: the spec.
  - *Owner.* Approved (O1). Size 2.0 → 3.0 u: the decisions' act times split from `known_at`, the screen calendar,
    and 6h §7's decisions (the "+0.25 u DD6.2" line, never counted in DD) are inside it. The owner is told.

- **D-DD.173 `demo_workflow` as built by WK-SC: the ten decisions of 6h §7, nine Actions and seven choices, the
  executive acting, the proposer kept in `M`** (model; O2; amends D-DD.135, 6h spec §7's DD6.2 line).
  - *Decisions.* The ten rows of `specs/6h-named-option-levers/spec.md` §7 (Kobo, Kisiwa, Mto, Mwea, Thika, Kirinyaga,
    Embakasi, Kasarani, Ruiru × 2), each through `prepare_decision` (the tenant's analyst), `state_one_off` and
    `state_option_record --emulated` (the Site's manager, `decision.one_off`/`decision.option_record`) where the row
    lists them, then `evaluate_options` (the analyst). Values come from `M` by option id, never retyped.
  - *Actions.* `M`'s nine `demo_workflow.actions`, each `record_action --as <tenant executive> --owner <M owner>
    --due <M due> --site <item's Site code>`, title the `M` text.
  - *Choices.* Seven items have a lever: KIS-REPAIR (Kisiwa `generator_redundancy` `repair`), MTO-HULLER (Mto
    `productive_demand` `new-connection`), THIKA-EPC-STOPGAP (Thika `backup_cover` `stopgap-and-claim`), KIRI-REPAIR
    (Kirinyaga `chamber_efficiency` `repair`), MWEA-AGG (Mwea `storage_contract` `storage-contract`),
    KAS-OEM-STOPGAP (Kasarani `charger_restore` `stopgap-and-claim`), EMB-DEADLINE (Embakasi `charging_schedule`
    `deadline-aware`). Each `choose_option --as <executive> --option <key>`, with `--action` = the item's one
    Action where it has one (MTO-HULLER has none: `actions_after_approval`). BAT-EVIDENCE and MTO-INV-CLAIM have no
    decision (rights-anchored, MD-6H-3); their Actions stand alone. KIS-SERVICE has no Action on 6 Nov (`M`).
    A refused choice (`OPTION_REJECTED`, `NOT_EVALUATED`, ...) is recorded with its code and listed pending; it is
    never tuned.
  - *People (O2).* The executive performs every act the product reserves to it. `M`'s `chosen_by` and `created_by`
    become the executive; the former names move to a new `proposed_by` key; `check_manifest.py` `workflow()` reads
    OD-16 as "owner = proposed_by". The product has no proposer field, so the proposer is not on screen (owner told).
  - *DD6.* DD6 keeps the pending listing, now naming "WK-SC" as the closing unit.

- **D-DD.174 Card sweep through D-DD.173** (cards; 0 u). DD5a: D-DD.167's loader rule and four tests, 4.0 u.
  DD5b: D-DD.167's manifest, C6 and drop rule; D-DD.169's price step; D-DD.168's loader is called under the widened
  guard; 4.25 u. DD6: closing unit "WK-SC" for the `demo_workflow` items and for C-DD9's Decisions, Actions and
  Results cells (with "IA-P lane" kept); 6h §7's decisions are WK-SC's; the C-DD17 served table is D-DD.153's states
  (bands unchanged by D-DD.164's re-seed); D-DD.166 moves no DD6 judge. Nothing else in the three cards disagrees
  with D-DD.17 to D-DD.173.

# DD rulings, round 27 (D-DD.175 to D-DD.176): a month with no fuel bought; D-DD.164's fixed point restated

Architect (Claude, DD lane), 2026-11-23. Read: `DD3b-handoff.md` "Fix round 1" on `task/DD3b-mini-plant` (e9ce0dd91);
D-DD.163, D-DD.164, D-DD.165, D-DD.170; `simulator/assetops_simulator/world/statements.py` (`figures_from_rows`),
`world/exports.py` (the statements call: FUEL expense rows), `simulator/tests/world/test_dd2_nodes.py` (statements
tests), `backend/assetops_backend/structure/reconciliation.py` (`_heading`: no used line and 0.00 stated is MATCHED,
`NONE_RECORDED_ZERO_STATED`, and never opens the gate; `standing`). No run was made; no database touched.

- **D-DD.175 BLOCKER: a trading month with no fuel bought has a statement whose fuel line is 0.00. The statement
  states fuel bought, never burned × price. Absence means zero only for a stocked good (fuel); an energy bill's
  absence is still refused** (model, W6 class of D-DD.92/D-DD.163; amends spec §5.4 and DD2.5's refusal; +0.25 u DD3b).
  - *What is wrong.* `figures_from_rows` refuses a month with revenue and no cost rows. That rule assumed a cost row
    every trading month, which held while invoices stated the month's fuel cost. Since D-DD.92 and D-DD.163, fuel is
    a stocked good: bought on delivery, burned from the tank. A month burning tank fuel with no delivery is a real
    month, and its accounts show no fuel purchase. Lakeside July after the restated notes is that month.
  - *Rejected: the fuel line from burned × price.* D-DD.163 made the management accounts state fuel bought, compared
    with the recorded invoices (reconciliation's heading, "Fuel bought (invoices)"). Burned × price on that line
    would be a second figure for the heading's quantity. July would read NOT_COMPARABLE (`NOT_RECEIVED`: the accounts
    state an amount, no invoice is recorded), and August and September NOT_MATCHED against their invoices: a false
    disagreement made by the world. A second key in `assetops.world-statements/1` is rejected too: the product's
    statement has one fuel field (a data contract, D-DD.163), and the burned cost is already the product's own node.
  - *Rule (`world/statements.py`).*
    - `ZERO_WHEN_NONE = {"fuel_cost": True, "energy_cost": False}` beside `COST_KEYS`.
    - `figures_from_rows(revenue_rows, cost_rows, months, cost_key)`: a month with neither is absent (unchanged). A
      month with revenue and no cost row is `(revenue, Decimal("0.00"))` when `ZERO_WHEN_NONE[cost_key]`, otherwise
      `STATEMENT_INCOMPLETE {month}`. A month with cost rows and no revenue is still `STATEMENT_INCOMPLETE {month}`
      (no trading month without billing). An unknown `cost_key` is `STATEMENT_COST_KEY` (as `statements_document`).
    - `exports.py` passes `"fuel_cost"`; the cold and EV callers (DD4.4) pass `"energy_cost"`. The docstring states
      the rule. The written figure is `"0.00"`; `source_ref` is unchanged ("..., final").
  - *What the product then shows (no product change).* Lakeside's July statement: revenue Σ billing, fuel 0.00.
    `_heading` reads the fuel heading MATCHED with `NONE_RECORDED_ZERO_STATED`; July's statement never opens the
    gate (3A7: "a missing figure is never 0 ... that never opens the gate"), and July's money reads reconciled only
    through another month that opens it (August and September carry invoices). The packet prints the served July
    standing for Lakeside and for each Site; nothing is typed (D-DD.93). If no Lakeside history month opens the
    gate after this, stop for the Architect.
  - *Tests (first, in `test_dd2_nodes.py`).* (a) `fuel_cost`: revenue rows, no cost rows in 2026-07 → `fuel_cost`
    `"0.00"` and revenue Σ rows. (b) `energy_cost`: the same → `STATEMENT_INCOMPLETE 2026-07` (the existing test,
    with the key passed). (c) Either key: cost rows, no revenue → `STATEMENT_INCOMPLETE`. (d) On the regenerated
    world, Lakeside's July statement has `fuel_cost` `"0.00"` and equals Σ July FUEL rows (zero), the existing July
    assertion made to hold for an empty sum. Then the 101 failures and 40 errors are rerun; the handoff's probe gives
    15 failed (7 main-identical, 8 re-pins of the re-seeded world), and any other failure still blocks.
  - *Checks.* `EMU_FUEL` (Σ invoices = fuel bought) holds as 0 = 0. C-DD4 is unchanged (it judges the burned
    `fuel_cost` node from `history.json`, not the statement).
  - *Owner, plainly.* In July Lakeside bought no diesel: the generators ran on fuel already in the tanks. So July's
    accounts show fuel bought $0.00, and the fuel the generators burned is still costed on screen (litres × price).
    Nothing is asked; you are told.
  - *Where and size.* DD3b fix round 1, before the pure DIR: +0.25 u (rule, caller, four tests). DD3b 7.25 → 7.5 u.

- **D-DD.176 D-DD.164's fixed point is restated: the fixed point is generates 2 and 3 byte-identical with every
  `--check` exit 0, and the move from generate 1 to 2 is proved values-only by a test. The move is honest** (model;
  amends D-DD.164 acceptance step 5 and D-DD.170's "including step 5"; +0.25 u DD3b).
  - *Why step 5 was mis-stated.* Step 1 is generated before step 3 writes the October leaves. `scale` makes history's
    `necessary_l` / `candidate_l` October × weight × jitter, and D-DD.164 itself calls them values that move with
    October. So when step 3 changes an October leaf (Kisiwa's), generate 2 must differ from generate 1 in exactly
    those values, and in `meta.view_digest` (a digest of the view, which includes `M`). Byte-identity to step 1 would
    hold only if the leaves had not moved. A fixed point is a state that a further pass leaves unchanged, so it is
    proved after the write, not against the state before it.
  - *Is the move honest? Yes.* No seed moved (0 scope digests, equal jitter), no writer input moved (the mini writer
    reads `delivered_kwh` and the declared `unexplained_l`, D-DD.18/D-DD.92; cold and EV exports byte-identical), and
    the leaves recomputed on generate 2 equal those written (every `--check` exit 0). History's scaled litres follow
    October's restated litres through the link the spec declares; nothing was tuned. Kisiwa Jul-Sep scaled necessary
    805/796/739 → 802/793/737 and candidate 54/51/71 → 56/53/73 are reported in the packet as such.
  - *Acceptance (replaces D-DD.164 step 5; steps 1-4, 6, 7 unchanged; applies to D-DD.170's re-proof too).*
    - 5a. `world_history.py generate` after `M` is written (generate 2), then step 6 (`--restate-notes --check` and
      `--leaves --check` exit 0 at Kobo, Kisiwa and Mto).
    - 5b. A third generate is byte-identical to generate 2. The two hashes go in the evidence.
    - 5c. `step1-vs-step2.txt` lists every differing JSON path. Each is `meta.view_digest` or a path in
      `history.RUN_DERIVED`; any other path stops for the Architect (the table missed a key).
  - *Declared table (`world/history.py`).* `RUN_DERIVED: dict[str, tuple[str, ...]]`, by vertical: the history keys
    computed from a `RUN_WRITTEN` value. `MINI_GRID`: `necessary_l`, `candidate_l`, plus any key `scale` (or another
    history function) computes from a `RUN_WRITTEN` key, which the builder lists from the code in pre-flight. Cold and
    EV: empty unless the code shows one. A static assertion: `RUN_DERIVED` is disjoint from `PHYSICAL_READS` and from
    every key a writer reads (`telemetry.books_for`, `telemetry_cold.cold_books_for`); a derived key a writer reads
    would be D-DD.164's loop again, and stops.
  - *Guard test (in `test_scope_run_written.py`, default suite).* On a copy of the view, change each `RUN_WRITTEN`
    October key of Kobo, Kisiwa and Mto and recompute the July-September history for that scope (in memory, no file;
    the per-scope function the existing guard uses). Every changed history path is in `RUN_DERIVED`, and no
    `PHYSICAL_READS` value moves. Plant: a function that also scales `delivered_kwh` fails it.
  - *Where and size.* DD3b fix round 1: +0.25 u (table, assertion, guard, the step-5 evidence already made). DD3b
    7.5 → **7.75 u**; DD 60.75 → **61.25 u**. Spec DD3.3's acceptance sentence is restated.
