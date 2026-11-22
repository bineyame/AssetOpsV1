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

# DD rulings, round 10 (D-DD.80 to D-DD.87): DD4 mid-build questions Q1 to Q5 and the deviation

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
  measured until D-DD.86 lands.

The owner is informed of all eight and is asked to weigh in on D-DD.82's prediction (the Thika chamber) and on
D-DD.84 (the receiving rule changes Assumed admission times; no story figure moves).

- **D-DD.80 Deviation accepted: `world/telemetry_cold.py` and `world/telemetry_ev.py` drive their packs, and DD3a's
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

- **D-DD.81 Q1: C-DD3 reads a FLAT Site's price at `tariff.usd_per_kwh`, as `M` states it** (default taken; amends
  spec §8.1 C-DD3).
  - `M` gives the FLAT type its one price at `tariff.usd_per_kwh`, and `world/tariffs.py` writes the FLAT band from
    that key. The checker reads the same place in `M` with its own code.
  - `_EV_PRICE` becomes a map from band to a path under the Site's `tariff`: `PEAK` → `prices.peak`, `OFFPEAK` →
    `prices.offpeak`, `NIGHT` → `prices.night_from_1_nov`, `FLAT` → `usd_per_kwh`, `DEMAND` →
    `prices.demand_per_kw_month`. `_site_prices` returns the whole `tariff` block. A missing path stays a FAIL line.
  - *Reach.* The checker's EV clause only. Mini and cold clauses are unchanged; the existing `test_dd1_check` cases
    stay green. Add one case: a FLAT line priced at 0.15 passes, and at 0.16 it FAILs naming `usd_per_kwh`.

- **D-DD.82 Q2: the Thika sequence comes from two v2 mechanisms that match `M`'s backup line; the builder's default
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

- **D-DD.83 Q3: C-DD19 is judged by `world check` C5, which runs the two simulator parity tests in a subprocess;
  `dd_check` does not import or run the simulator** (default amended; amends spec §8.1 C-DD19).
  - *Why.* C-DD19 asks whether the simulator agrees with itself, so only a run of the simulator can answer it. The
    checker's independence (D-DD.14) concerns expected figures, and a parity has none. C5 already runs parity files as
    subprocesses (`tools/world.py:1099`), so this uses the existing mechanism.
  - *Change.*
    - C5 gains the cold node id (DD4.1's v1 digest test in `simulator/tests/test_cold_thermal2.py`) now, and DD3.3's
      v8/v9 test when it lands. It runs them with the simulator's interpreter, and the test files go into
      `CHECK_CODE`.
    - `dd_check`'s C-DD19 entry stops being a stub check. It prints `C-DD19 judged in world check C5 (D-DD.83)` and
      is excluded from its pass count; the table in §8.1 says so.
  - *Reach.* `tools/world.py` C5 and `tools/dd_check.py` only. C5's existing bulk-path parity files are unchanged,
    and a `tools/tests` case covers the new node ids with a fake runner.

- **D-DD.84 Q4: a room receives produce in lots at receiving times its declared cooling can pull down, and the pack
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

- **D-DD.85 Q5: AMBIENT and EFFICIENCY are ratified as private v2 forcings, placed by the writer at local midnights**
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

- **D-DD.86 cold-thermal 2 holds the chamber temperature on a declared 10⁻⁶ °C grid and books the rounding in its
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
  - *Reach.* cold-thermal 2 only; v1 is guarded as in D-DD.82. EV: the builder checks `ev-charger` denominators over
    7 days; if they grow, it stops and asks, and does not fix it silently. Mini-grid ran 123 days in DD3a and is not
    touched.

- **D-DD.87 Units: DD4 +1.5 u to 7.25 u, split into DD4a (4.0 u) and DD4b (3.25 u); DD 38.5 u** (W4: parts of at
  most 6 u; amends spec §7 DD4 and §8.2).
  - **DD4a, cold (`task/DD4-cold-ev-reality`, continuing): 4.0 u.**
    - DD4.1, 1.5 to 2.0 u: D-DD.82 +0.25, D-DD.86 +0.25.
    - DD4.2, 1.25 to 2.0 u: D-DD.84 +0.5, D-DD.80's join and mini parity +0.25.
    - D-DD.81 and D-DD.85 fall inside their units.
  - **DD4b, EV and measured books (`task/DD4b-ev-measured`, from main after DD4a merges): 3.25 u.**
    - DD4.3, 1.75 u.
    - DD4.4, 1.25 to 1.5 u: D-DD.83 +0.25.
  - *Sequencing.* DD4a's join waits for DD3a on main (not DD3b). DD4b follows DD4a. DD5 follows DD3b and DD4b.
  - *Builder order in DD4a.*
    1. D-DD.86, then D-DD.82, in `packs/cold.py` with their tests (v1 digest green at each commit).
    2. D-DD.84's ledger, goldens and parity.
    3. `ColdSiteRun` on the protocol, with D-DD.85's forcings.
    4. After DD3a merges: the join, its parity, and the writer run, measuring Thika against C-DD6.
