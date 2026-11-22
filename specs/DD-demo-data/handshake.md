# DD handshake (rev 1 spec; reviewer and implementer pre-flight)

Fresh Claude reviewer, 2026-11-22, on `main` at `9036fb9fb`. Read: `spec.md`, `reviewer-guide.md`, D-DD.1 to D-DD.16
(`spec.md` §9; index `.ai/decisions/index-rulings-26.md:23-38`), `owner/owner-demo-data-answers-2026-11-22.md` (Q1-Q3,
Q6 settled, Q4-Q5 defaults stand; not re-raised), IA-P `spec.md` §3 matrix, the research file
`/opt/assetecon/evidence/kobo-datasheets/datasheets.md`, and the code below. `M` is
`Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml`. `B` is `backend/assetops_backend`, `C` is
`contracts/assetops_contracts`, `S` is `simulator/assetops_simulator`.

**Checked and found as the spec says.** `B/onboarding/operator_file.py:132` (`site_type` "MINIGRID"), `:255-256`
(`ONBOARD_VERTICAL`); `B/sites/foundation_service.py:204-229` (gateway `edge-<code>`, sources from `devices` only);
`S/world/exports.py:51, 292-295` (`NOT_ON_PATH_VERTICAL`); `tools/world.py:181-183` (`source` must be `none`), `:719-721`
(`batches != 0` fails L1), `:571-600` (`inputs()` stages exports only); `C/native/layouts_v1.py:664` (four layouts);
`C/canonical/sources_v1.py:20-41` (every cold and EV source type of §3 exists, kinds as §3 lists them);
`B/evidence/adapters/postgres_evidence_ledger.py:687-690` (`BULK_SITE_TYPE_UNPROVEN`); `B/structure_snapshot/build.py:82`,
`read.py:60`; `B/estate/scope.py:21` (`MAX_DAYS = 31`); `S/world/history.py:85-103` (exactly three history months);
`B/sites/models.py:97`; the packs `mini_grid.py` (`MINI_GRID_V8_MODEL`, :1864), `cold.py`, `ev_charger.py`
(`MODEL_PROFILE = ("ev-charger", 1)`); `generator_curve.fuel_curve` refusals (`:81-100`); `B/scheduling/run.py` `tick`
and `enrol`; `B/source_profile.py` `admit`; `B/sites/binding_conversion.py:137` `convert`, `binding_service.py:557`
`publish`; role sets `minigrid-roles-4`, `cold-roles-1`, `ev-roles-1` exist; `backend/tests/test_ds3_parity_postgres.py`,
`test_site_template_fingerprints.py`, `fixtures/w2/cold-lab-001.yaml`, `fixtures/w2/ev-lab-001.yaml`;
`M` `demo_workflow` holds 21 people (7 per operator, every role in `accounts/model.py:14`); `M` `history` keys
(`families`, `seasons`, `day_classes`, `rules`, the Mwea, Kirinyaga and Embakasi overrides) and Embakasi's October
figures (47,740 kWh × 0.24 = 11,457.60; 39,060 × 0.12 = 4,687.20; 500 kW × 12.00 = 6,000.00; `M:606`); DS4 `packet.md:225`
13.497 s per Site-day; 9 × 129 × 13.497 = 15,670 s.

**Data sheets checked against the research file.** FG Wilson P50-3: 45 kVA / 36 kW prime, 40 kW standby, doc code
P50-3/4PP/0414/GB, URL, MSF cross-check 68799, 10.5 / 7.8 / 5.6 L/h: all as §5b. Pylontech US5000: 4.8 / 4.56 kWh,
80 A / 100 A, PY230529-EN p. 03, ">8,000 at 25 C (attribution likely)": all as §2. Arithmetic re-done:
10.5 / 36 = 0.29167 → 0.2917; 42 × 4.56 = 191.52 → 191.5; least-squares intercept through (36, 10.5), (27, 7.8),
(18, 5.6) = 0.6167 → 0.62; v8 slope 0.2917 − 0.62/36 = 0.2745; residuals 10.50 / 8.03 / 5.56; 25 % point 3.09 L/h. All
match spec §6. Gaps are R1 and R10.

## Reviewer questions (R)

**R1. Kobo's no-load rate is labelled Declared, but it is not published, and it replaces an owner value five times
larger** (spec §6 mapping row 3; D-DD.10). High.
- The research file calls the intercept "derived, extrapolation, not published" (`datasheets.md` §5b). The owner's Q6
  answer reads "unpublished values labelled Assumed with their basis". The spec labels it "Declared (data sheet; fitted
  to the stated points)".
- Today's value is 3.3 L/h, "the owner's value of 2026-11-07 for a 40 kW set" (`M:1820`;
  `replay-studies.json:16`). The generic rule (0.08 L/h per kW) gives 2.9 L/h at 36 kW. The fit gives 0.62 L/h.
- No-load burn is what makes "generator running after the battery is full" cost litres, so this one value drives the
  hero beat's candidate litres. The spec does not say that the owner's value is replaced, or what that does to Kobo's
  October split.

*Default:* `generator-no-load-fuel-rate` 0.62 is labelled **Assumed**, with the basis "fitted to the three published
part-load points; the sheet states no no-load rate". The packet for DD3.2 commit 1 prints Kobo's October necessary,
candidate and unexplained litres from the v8 writer at 3.3 L/h and at 0.62 L/h, side by side. The coordinator puts the
replacement of the owner's 3.3 L/h to the owner as one line before commit 2.

**R2. Two figures for Kobo's fuel split in July to September, and the trend beat is checked on neither** (spec §A row
2, §4 reason 2, §5.1; C-DD4, C-DD8). High.
- `history.json` already carries `necessary_l`, `candidate_l` and `unexplained_l` as generated leaves (`M` `history.rules
  .MINI_GRID.actual`; the Kobo override `unexplained_l: trend generator 0.10 0.10 0.10`).
- DD's readings make the observer compute the same split from v8's generator state for the same months. That is two
  figures for one quantity (`owner-one-figure-loyal-to-operating-world`).
- C-DD4 checks the books against `history.json`. C-DD8 checks only October, and only that unexplained ≥ 0. Nothing
  checks that the served July-October series still shows "Kobo's unexplained fuel rising", the beat §A promises.

*Default:* for every month with readings, the served split is the readings-fed one. The history split leaves feed only
the books' delivered litres and are never served beside it. New check C-DD17: the served unexplained litres for Kobo,
July to October, are each ≥ 0 and rise month on month, as the manifest's story says. A failure stops for the Architect,
as C-DD8 does; nothing is tuned.

**R3. Page × Site-type: cold-chain and EV have data in the range but no output on three pages, and C-DD9 cannot tell
the difference** (spec §A rows 2 and 6, §10.2; C-DD9; IA-P `spec.md:220-226`). High.
- No product code reads the cold or EV books DD adds. `grep` finds no reader of `electricity_bill`, `utility_invoice`,
  `DEPARTURE` or `SERVICE_TICKET`. `STORAGE_MOVEMENT` appears only in `commercial/pseudonym.py`, and `FLEET_ROSTER` only
  in `structure/rows_ev_depot.py`.
- IA-P's matrix gives cold and EV a "No monthly figures … yet" row on the Overview, Outcomes L1/L2 and the Sites list
  until Q11.
- §A row 2 still promises "Month by month … all nine", with Mwea's occupancy, Kirinyaga's energy and Embakasi's peak
  share as trends. On the served app those trends appear nowhere until Q11. That breaks the owner's range rule ("data in
  range → output for the range on every page, same for every Site type").
- C-DD9 "returns 200 with output and no 'Not analysed yet'" is passed by the "No monthly figures" row. On Jul-Oct it is
  also passed by the non-whole pages, which show only the last 31 days. Site tabs (the reading-fed Operations tab of each
  Site, spec §4 reason 4) are outside C-DD9.

*Default:*
- §A row 2 is amended to say that the cold and EV month trends show after Q11, and the owner sees that line.
- C-DD9 gets a cell table (page × Site type × range) stating what counts as output:
  - mini-grid: figures for each month of the range;
  - cold and EV on the three month pages: the named row, which is not counted as figures;
  - windowed pages: the window label, and readings on the window's first day.
- C-DD9 also covers each of the nine Sites' tabs on the three ranges.
- The packet lists every cell that shows a "not available" or "no figures" line with data in range. That list is the
  Q11 and Q12 backlog.

**R4. The four outcome categories per served operator** (spec §A table, §1 cast "Category it leads"; owner Q3 "one
operator at a time … to match the prospect"). High.
- Each prospect sees one operator.
- Harvest Cold has no Assure beat: no snapshot months, `statements: []` (§5.4).
- Metro Bus's Assure rests on Kasarani, with no month to compare it against.
- Ruiru's "Grow revenue (avoided CAPEX)" is avoided spend. That reads as Optimize cost or Protect capital, not revenue.
- No C-DD check asks whether each category is served.

*Default:*
- New check C-DD18: for each tenant served on October, each of Grow revenue, Optimize cost and efficiency, Protect asset
  and capital, and Assure performance and returns has at least one surfaced item (Finding, decision or outcome row), or
  a stated "not available yet" naming the missing record.
- §A gains a per-operator line naming the categories each operator cannot show yet (Harvest Cold: Assure until Q11).
- The Architect reclassifies or justifies Ruiru's category.

**R5. C-DD4's expected figures come from the generator's own output** (§8.1 C-DD4; D-DD.14 "expected figures come
only from the manifest's `oracle`, `checks` and `period`"). Medium. "each history month equal `history.json` to the
cent" uses a file the generator wrote (`S/world/history.py`).
*Default:* D-DD.14 names `history.json` as a declared, committed input pinned by the history golden digest
(`simulator/tests/world/golden/history_v1.json`). The checker reads it with its own JSON read and asserts its sha256
equals the golden before using it. The manifest `checks` identities (C-DD3) stay the independent half.

**R6. The disorder tests are not "as today": none is planted, and three cannot be planted as written** (§5.5; C-DD14;
DD2.4 at 1.25 u). High.
- `grep` over `simulator/`, `tools/` and `B/` finds DUP-1, OOO-1, LATE-SETTLE-1, MAP-1, FX-1, TENANT-1 and CLOCK-1
  nowhere. GAP-1 exists only as an absent row (`S/world/exports.py:10`).
- TENANT-1, a refused row in Harvest Cold's file, makes `load_emulated_exports` exit 3. `world.py:719-721` then fails
  L1.
- DUP-1, a second identical Mto billing file, meets `EXPORT_PATHS_MIXED` (`load_emulated_exports.py` docstring: "Two
  files of one source type").
- CLOCK-1's expectation ("corrected from StatusNotification pairing") has no product path. The bulk loader refuses any
  batch with a rejected ordinal (`B/evidence/bulk_load.py:180-183`).
- So C-DD14 "handled as `expect` says" cannot be judged for these.

*Default:*
- DD2.4 gets a table per test: file, rows, load step, expected product result, and what C-DD14 asserts.
- TENANT-1 and DUP-1 run as their own L1 steps with an expected exit (refused, or 0 new revisions). They are recorded,
  not failed.
- CLOCK-1 is planted in the readings within what the bulk path admits. C-DD14 asserts it is planted and listed; its
  correction is "not built" in the packet.
- DD2.4 is re-sized.

**R7. Checks that pass on wrong data** (§8.1). Medium.
- C-DD7 allows 1 % on mini delivered kWh and EV session kWh. These are scaled inputs that `TEL_INPUT_TOTAL` already
  makes exact, so a 0.9 % mis-scale passes.
- C-DD8's "≥ 0" passes any positive balance.
- C-DD1 counts people, but not each site manager's Site binding.
- C-DD5's "declared cadence" names no source for the cadence.

*Default:*
- C-DD7 is exact on scaled inputs: delivered kWh, EV kWh and peak kWh. Tolerances stay only on model outputs, each with
  its reason (cold metered kWh; see I6).
- C-DD8 also reports the value beside the manifest's October 120 L, as information.
- C-DD1 checks the (person, role, Site) triples of `demo_workflow`.
- C-DD5 reads cadence from each Site's readings manifest (§4.1), and the checker's own table must equal it.

**R8. "A person acts and tracks": who creates the choices and Actions?** (§A row 5, §1 "Actions and choices are made
later through the product's commands"). Medium. `demo_workflow` lists 10 items and 9 Actions, some `RELEASED` or
`AT_CREATION` on `as_of`. DD onboards the people only. After the build, Decisions and Actions show the same for every
operator, and C-DD9 cannot judge those pages.
*Default:* §11 states that choices and Actions are not in DD and names who makes them (the walkthrough script, or a
later WK `prepare` step through 3C2 and 6a commands). C-DD9 treats the Actions and Results pages as "empty state shown"
until then.

**R9. Kobo's October balance can be known before DD4** (§6 "Story consequence"; §10.7 mid-build count 0). Medium. A
negative unexplained balance on the 36 kW, 0.62 L/h kit stops the 4-hour build "for the Architect". That is a
predictable mid-build question.
*Default:* DD3.2 commit 2 runs the writer on Kobo's October inputs alone, a pure run with no database. It prints
delivered, model litres and the balance in the packet. A negative balance goes to the Architect before DD3 merges.

**R10. Basis words for the Assumed values overstate the research** (§6 slot `assumed`). Low.
- Round-trip efficiency "comparable LFP banks state 95-97 % (BYD Battery-Box LVS, Freedom Won LiTE)": the research says
  BYD's value "was not recovered" and both figures are "search excerpt; secondary-read" (`datasheets.md` §6).
- Minimum load: the Cummins guidance is 30 % of **standby** rating (`datasheets.md` §5c). That is 12 kW, or 33 % of the
  36 kW prime the property applies to.
- The P50-3 fuel row was read from a "scrambled text layer" and matched by MSF.

*Default:* the basis texts say "search excerpts, secondary" and "30 % of standby rating (12 kW); applied as 30 % of
prime". The generator `source_document` carries the MSF cross-check beside the sheet.

## Implementer pre-flight (I)

**I1. Imported gateways and sources are disabled, and the bulk path refuses a disabled gateway** (§4.2; D-DD.7). High.
- `B/sites/foundation_service.py:210, 227` create the gateway and every source with `disabled_at=now`.
- `bulk_load` admits through the claims check, which refuses `GATEWAY_DISABLED` (`postgres_evidence_ledger.py:625-626`;
  `B/evidence/ledger_service.py:231`).
- No DD step enables them.

*Default:* DD1.2's new apply step enables the gateway and each source through the product command
`python -m assetops_backend.evidence.provision_gateway enable-gateway` / `enable-source` (subprocess, D-DS4.3), for
`data: emulated` files only. The apply test asserts both are enabled and that a second apply changes nothing.

**I2. A batch is one source, not one Site-day** (§4.2 "one `ingestion_batch_v2` per Site-day"). Medium.
`C/ingestion_batch_v2.py:18, 111` carries one `source_id` per batch. `bulk_admit` takes one `source_id`
(`postgres_evidence_ledger.py:648`). `MAX_BATCH_BYTES = 1_048_576` (`:64`).
*Default:* one batch per (Site, source, local day), with `sequence_epoch` and the sequence rule stated in §4.2. A unit
test on the largest source-day (an Embakasi charger's 5-minute power) shows it fits under 1 MiB.

**I3. Readings start three hours before the Sites exist** (§2 span; DD1.2). High.
- Readings start 2026-07-01T00:00 Africa/Nairobi, which is 2026-06-30T21:00Z.
- Lakeside's file has `valid_from: 2026-07-01T00:00:00Z`, and binding sets use `FOUNDATION_ORIGINAL_VALID_FROM`
  (`backend/conversions/ev-lab-001-bindings.json`).
- Every 1 July batch therefore holds ordinals with no basis. `BULK_REJECTED_ORDINAL` refuses the whole batch
  (`bulk_load.py:180-183`).

*Default:* every `/2` file has `valid_from: "2026-06-30T21:00:00Z"`, local midnight. The `/1` digest rule still holds,
because Lakeside's file moves to `/2` anyway.

**I4. v8 cannot run Kisiwa or Mto as the manifest declares them, and four of nine Sites have no template** (§2 "v8 on
the Site's template"; §4.1 `SiteInputs`; §4 reason 3). High.
- v8 is "one generator with its fuel tank" (`S/packs/mini_grid.py:933`) behind one PV inverter.
- Kisiwa has two 60 kW sets, and GEN-KS-01 fails on 30 Oct while GEN-KS-02 runs (`M:182`). Its template
  `kisiwa-diesel-hybrid-60kw` v1 has one generator and a 20 kW PV array, against the onboarding file's 30 kW and the
  battery's 80 kWh.
- Mto has two 25 kW inverters, and INV-MT-02 fails on 28 Oct. There is no Mto template in `config/site-templates/`.
- Cold and EV have no shipped template, only the test fixtures `w2/cold-lab-001.yaml` and `ev-lab-001.yaml`.

*Default:*
- The writer runs on each Site's `/2` onboarding foundation (components, devices and properties), not a shipped
  template, so the stored Site and the writer agree for all nine Sites. C-DD16 generalises to that.
- The Architect writes, per Site, how a story failure maps onto v8:
  - Mto: inverter limit 50 → 25 kW from 28 Oct 00:00;
  - Kisiwa: one 60 kW aggregate set, with GEN-KS-01's failure a state event on its own device.
- Each mapping is labelled in the readings manifest.

**I5. Template v3 has none of the three v8 properties, and the repo already has a data-sheet basis** (§6 mapping;
D-DD.10). High.
- `kobo-mini-grid-60kw.yaml` v3 holds 14 property keys. It has no `generator-no-load-fuel-rate`,
  `generator-minimum-load` or `battery-charge-taper-start`, which v8 reads (`S/packs/generator_curve.py:40-42, 159-181`).
  So "unchanged" and "as today" in the mapping table are wrong: v4 adds them.
- `B/sites/models.py:342-345` already declares `generator-no-load-fuel-rate-basis`, `generator-minimum-load-basis` and
  `battery-charge-taper-start-basis`, with values `GENERIC_DEFAULT`, `MANUFACTURER_DATASHEET` and `SITE_TEST`.
- The spec's new `DATASHEET` source plus `source_document` duplicates that mechanism. It also opens the closed property
  key set `{"property_key", "value", "unit", "source", "source_version"}` (`B/sites/foundation_parsing.py:103`), which
  changes stored foundation content.

*Default:*
- Reuse the existing basis vocabulary. v4 adds the three properties with their `-basis` properties: `MANUFACTURER_
  DATASHEET` for the sheet-derived values, `GENERIC_DEFAULT` for the minimum load and taper.
- Add `-basis` siblings for `generator-rated-power`, `specific-fuel-consumption` and `battery-energy-capacity` in the
  same closed set.
- The maker, model and revision live in `config/datasheets/kobo-equipment.json` and are rendered by the SC-1 statement.
- No new `source` value, and the property key set is unchanged. The Architect confirms or rules otherwise.

**I6. The cold and EV packs lack the inputs the writer is told to scale** (§4.1 "cooling → room heat load … cold
`crate_days` through occupancy"; C-DD7 cold 3 %). High.
- `cold.run_window` (`S/packs/cold.py:441`) takes one constant `ambient` per window. Its forcings are only grid loss or
  restore, `GENERATOR_FAILURE`, `DOOR_OPEN` and `DOOR_CLOSE`. It has no occupancy or produce heat-load input. So "through
  occupancy" and Kirinyaga's +24 % have no mechanism.
- Hitting the bill within 3 % then means choosing 13 thermal properties per room (`cold.py:51-65`), which is
  calibration of an output.
- Public readings come through `S/observation/transform.py` (`cold-observation/1`), which the spec does not name.
- For EV, when a bus plugs in decides the 55 % peak share, and §4.1 gives no rule for it.

*Default:* the Architect writes, per room:
- the 13 property values;
- door openings derived from the storage ledger's IN and OUT movements (the scaled input);
- ambient per day from the `cooling` family;
- Kirinyaga's drift as a dated, declared property change, with value and dates;
- the observation transform per vertical;
- the EV plug-in rule from the roster's `return_at` and the schedule.

C-DD7's cold tolerance keeps its 3 % only with that basis written down.

**I7. The §5.2 and §5.3 columns cannot produce the records' required fields through a profile** (`C/canonical/
records_v1.py:160-290`; `C/native/layouts_v1.py:43-49`). High.
- DEPARTURE needs `service_day` (date) and `block_met` (bool). Profile types have no bool, and `body.block_met` is not a
  coded path, so `soc_ok (Y|N)` cannot be mapped.
- SERVICE_TICKET needs `status` (OPEN, ACKNOWLEDGED, RESTORED, CLOSED), `counterparty_ref` and an ASSET subject.
  `kind (FAULT|RESTORE|SERVICE)` is not a field.
- RECEIPT needs `payer_ref` and `method`.
- CHARGE needs `account_ref`, `tariff_code`, `effective_from` and `effective_to`.
- The EV invoice's TARIFF_SCHEDULE needs `contract_ref`, `currency` and `bands`, and an invoice line carries no band
  table.
- `source_profile admit` requires `--expected E` and `--as EMAIL` (`B/source_profile.py:5-6`). The spec names only the
  sample.

*Default:*
- The Architect writes each profile's column → path table, including constants and coded maps (for example `kind` →
  `status`).
- DEPARTURE takes one of two routes:
  - a contract change adding a `bool` type with a Y/N map to `layouts_v1`, with its own test (a protected seam, in the
    unit's size); or
  - DEPARTURE leaves DD, and C-DD2's EV list says so.
- Each profile ships `<profile id>.expected.json` beside its sample, admitted by the analyst.

**I8. The world check would pass on the new world without checking it** (`tools/world.py`). High.
- C6 globs `*.batch.json` (`:1097`). With `*.readings.json` inputs it returns "0 batches (telemetry none)", a PASS.
- C4 judges every snapshot against `derived-values.json`'s one month (`:963`). Lakeside's July to September snapshots
  would fail against October's nodes, or go unchecked if filtered.
- `CODE_PATHS` and `CHECK_CODE` (`:43-47`) omit `tools/dd_check.py`, `tools/datasheet_template.py`, the new parity test,
  `config/site-templates/`, `config/datasheets/`, `backend/conversions/world/` and `backend/conversions/profiles/`. A
  change there would not stale the ladder.

*Default:*
- C6 judges the sealed batches, read from the L1 store or written beside the inputs at sealing.
- C4 judges October only, stated; history months are C-DD4's.
- The named paths join the keys.
- C5 runs both parity files (§4.3), and C8 runs `dd_check.py`.

**I9. Restating Kobo moves far more than DD3.2 lists** (§6 "the manifest's Kobo `physical` … change in DD3.2"; §0
"the seeds by scope and the golden digests" stay). High.
- `physical` is a view key (`S/world/view.py:19`). Editing `genset_kw`, `sfc_l_per_kwh` and `battery_kwh` (`M:89-93`)
  changes Lakeside's scope digest. That changes:
  - the seeds (`S/world/scope.py:61`);
  - `history.json` and the history and records goldens (`simulator/tests/world/golden/`);
  - the pinned export digests (`simulator/tests/world/test_3a3_exports.py:142, 243`);
  - `derived-values.json` (diesel figures at 0.2917; `standby_kw: "physical.genset_kw"`, `M:230`);
  - C4's oracle;
  - 0K4m's frozen-view proof (D-0K4.35).
- The K8 replay study ran on 40 kW and 200 kWh.
- `kobo-mini-grid-60kw` is read by lab and host tests (`test_run_binds_scenario_to_site.py`,
  `test_site_template_lineage.py`, `test_0k4b_properties.py`, `host/tests/test_t025g_*.py`, `test_lab_cockpit_window.py`).

*Default:*
- DD3.2 commit 2 regenerates `history.json`, the goldens, `derived-values.json` and the pack checks (`check_manifest.py`,
  `check_alignment.py`), and lists every moved figure.
- §0 is amended.
- The K8 study and the lab Sites stay on v3 / 40 kW, labelled, until 0K4f. Whether lab tests pin v3 or move is the
  Architect's call.
- DD3.2 is re-sized (it is not 1.25 u).

**I10. Definition `/2`, the Site-inputs file and the input digest are left to the builder** (§4.1 CLI, §7 DD4.1).
Medium.
- `/1` requires `derived_values`, `projection`, `built_by` and per-tenant `submit_as`, `accept_as` and `sites`
  (`world.py:140-189`). §7 does not say which of these stay in `/2`.
- `--sites F` is "produced by DD4.1's step", but DD3.1 tests the writer before DD4 exists, and F has no schema.
- The inputs digest (`world.py:595`) hashes staged files and onboarding files. It must also cover the readings files,
  the profiles and the binding conversions.
- `L2_STEPS` (`:48`) keys L2, so the drain must join it.

*Default:*
- `/2` = `/1`'s keys plus §7's additions.
- F is `assetops.world-site-inputs/1`, written by a pure function from the `/2` onboarding files and binding conversions,
  built in DD3.1.
- The digest covers every input file.
- The drain is in `L2_STEPS`.

**I11. WK for a tenant without snapshot months** (§7 DD4.3). Medium.
- `walk_world.py:162` requires a non-empty `statements`. `prepare` does "one snapshot rebuild" (`:4`), which
  `build.py:82` refuses for COLDCHAIN and EV_CHARGING.
- `judge_month` (W4) needs an `expect`.

*Default:* when `snapshot_months` is empty, `statements` may be `[]`, and the rebuild, W4 and the statement steps are
skipped and recorded as skipped. The packet lists the W-steps that run per tenant.

**I12. Exports: signature, version bump and fuel notes** (§5.1). Medium.
- §5.1 writes `build_exports(view, *, months=None)`; today it is `build_exports(view, history)` (`S/world/exports.py:280`).
- `SOURCE_VERSION` "1" → "2" (`:35`) changes every October row, the pinned digests above and the served world's L1
  inputs.
- History months have no `diesel_l` leaf (0K4m I2), so "fuel deliveries in 400 L notes" has no named source.

*Default:*
- Keep `history` as an argument and add `months`.
- List the pin moves.
- Monthly delivered litres = `necessary_l + candidate_l + unexplained_l` from `history.json`, cut into 400 L notes by
  largest remainder, with the remainder note stated.

**I13. `load_world_inputs` details** (§4.2, §4.3). Low.
- `registered_site_scope` resolves through the served tenant (`B/gateway_api.py:144-158`), so sealing must run with
  that tenant's env. `world.env(name, slug, kd)` already does this; state it.
- `_LAYOUT` and the glob (`load_world_inputs.py:30, 93`) change from `*.batch.json` to `*.readings.json`.
- §4.3's "allow set" is today `site_type != "MINIGRID"` (`postgres_evidence_ledger.py:688`), not a set.

*Default:* as stated. `*.batch.json` stays accepted for `/1`.

**I14. How `dd_check.py` reaches "the product's HTTP reads"** (§7 DD1.3, §8.3 port guard). Low. No port is named, and
5490, 8990 and 8992 are barred.
*Default:* an in-process ASGI client on the app factory, pointed at the clone's URL, with no port opened.

**I15. Copy path for the DD1.1 refusal** (§7 DD1.1 "SC-1 catalogue"). Low. Today's onboarding refusals are in
`B/onboard_operator.py`'s `_SENTENCES` (`:50`), not the SC-1 catalogue (`B/i18n/`).
*Default:* the new sentence goes where `ONBOARD_VERTICAL`'s current one lives, and the DATASHEET label goes in SC-1.

## Pre-flight as run here

There is no code yet, so I ran no tests. Checks were reads and `grep` on `main` at `9036fb9fb`, plus the §6
arithmetic redone by hand, which matches the spec. Not verified: v8's Kobo October balance on the new kit (R9), cold
pack energy against the bills (I6), and the cost per Site-day for cold and EV, since DS4's 13.497 s was measured on
mini-grid Site-days only.

**Counts:** R1-R10 (High: R1, R2, R3, R4, R6; Medium: R5, R7, R8, R9; Low: R10). I1-I15 (High: I1, I3, I4, I5, I6,
I7, I8, I9; Medium: I2, I10, I11, I12; Low: I13, I14, I15).

## Answers (Architect)

Architect (Claude), 2026-11-22. Every question is answered once, here. The rulings are D-DD.17 to D-DD.34 in
`rulings.md`, and the spec is rev 2 (`spec.md`). One class sits behind R2, R7, R9 and I6. Rev 1 let the books and the
readings each carry a figure for one measured quantity, and then reconciled them with a tolerance. Rev 2 classes every
quantity as input or measured (`spec.md` §4.0): measured books follow the meter, and the readings follow the decided
books. That rule, and its sweep, is at the head of `rulings.md`. Where a default below is accepted, it is cited, not
restated.

**R1 (no-load rate labelled Declared).** Accepted, with one change: the owner decides. 0.62 L/h is labelled
**Assumed**, through a new basis value `DATASHEET_FIT` on the existing `generator-no-load-fuel-rate-basis`, which reads
"Assumed: fitted to the data sheet's stated points". It replaces the owner's 3.3 L/h of 7 Nov
(`owner/owner-fuel-scope-2026-11-07.md` Q2) only on the owner's answer to the new **owner Q7**, whose default is 0.62.
DD3.2 commit 1 prints Kobo's October necessary, candidate and unexplained litres at both values. Commit 2 waits until
the coordinator has put Q7 to the owner, then applies the answer, or the default under W3. The K8 study keeps 3.3.
D-DD.17; `spec.md` §A Q7, §6.

**R2 (two fuel splits; trend unchecked).** Accepted. The served split is the readings-fed one (D-DD.18). The trend check
is restated to the manifest's own story rather than "rises month on month": the history override says Kobo stays
within tolerance before October (`M` `history.sites`, "before it, within tolerance"). So **C-DD17** asks: each month
≥ 0, July to September within the product's tolerance, October above it. The world now has a cause for the residual:
a declared tank draw (D-DD.19).

**R3 (page × Site type).** Accepted in part. The C-DD9 cell table and the per-Site tabs are adopted (`spec.md` §8.1).
The rest of the default is not taken: §A is **not** amended to accept "trends after Q11" as the end state. A "No
monthly figures" row and a 31-day window both count as **not output**. DD's acceptance build is the one rebuild after
0K4f, Q11 and Q12 (**owner Q8**, default: those gate acceptance; nothing cut). DD6's first build lists each pending
cell with the unit that closes it. D-DD.26.

**R4 (four categories per operator).** Accepted. **C-DD18** is added, and §A gains the operator × category table.
Ruiru keeps **Grow revenue**: the city's +6 bus route is new contract revenue on existing chargers, and its revenue
reads "Not available yet (route contract not in the books)". The avoided chargers are its capital side, under Protect.
Harvest Cold's and Metro Bus's Assure beats come with Q11 (Q8). D-DD.26.

**R5 (C-DD4 from generator output).** Accepted as stated. D-DD.31; `spec.md` DD1.3.

**R6 (disorder not plantable as written).** Accepted. `spec.md` §5.5 now has a table per test. TENANT-1 and DUP-1 run
as their own L1 steps with expected exits. CLOCK-1 is stamped 4 minutes ahead in the readings, admitted, and its
correction reported "not built". DD5.2 is a unit of 1.25 u. D-DD.25.

**R7 (checks that pass on wrong data).** Accepted, and widened by the class rule. C-DD7 is exact on every scaled and
measured quantity, including the cold bill against its meter and the EV invoice against its meter. That replaces the
3 % and 1 % tolerances, because the bills now come from the meters (D-DD.20). C-DD8 prints the balance beside 120 L.
C-DD1 checks (person, role, Site) triples. C-DD5 reads cadence from the readings manifest. D-DD.31.

**R8 (who makes choices and Actions).** The default is not taken; DD does it. DD6.2's WK `prepare` creates
`demo_workflow`'s decision records and Actions through the 3C2 and 6a commands, as the named people. An item whose
command is not on `main` is listed as pending, and C-DD9 reads that page as its empty state. DD6.2 is 2.0 u. D-DD.27.

**R9 (Kobo's balance knowable before DD4).** Accepted and widened. DD3.2 commit 1 makes a pure run of all three
mini-grid Sites, July to October. It prints delivered, burned, drawn, tank minimum and maximum, the balance, and
candidate litres, with Kobo at both no-load values. Any bound hit, or a C-DD8 or C-DD17 failure, goes to the Architect
before DD3 merges. The fallback is stated in advance: a declared reorder rule, with the books following the tank and
the owner told. D-DD.19.

**R10 (basis words overstate).** Accepted. The basis texts are rewritten to the research's own words, including the
"30 % of standby (12 kW, 33 % of prime); 30 % of prime applied" line. The slot's `document` names the scrambled text
layer and the MSF match. D-DD.17; `spec.md` §6.

**I1 (disabled gateway and sources).** Accepted. D-DD.29; `spec.md` DD1.2.

**I2 (a batch is one source).** Accepted: one batch per (Site, source, local day), `sequence_epoch` 1, sequences in
reading order, with the 1 MiB unit test. D-DD.29; `spec.md` §4.6.

**I3 (readings before the Sites exist).** Accepted: `valid_from` 2026-06-30T21:00:00Z on every `/2` file and binding
set. D-DD.29.

**I4 (v8 cannot run Kisiwa or Mto).** The writer runs on each Site's `/2` foundation: accepted. The aggregate-set
mapping is **not** taken: it would hide the failed unit that the cover and warranty beats are about. The mechanism is
specified instead. **Mini-grid v9** adds ordered generator units sharing one tank, dispatched by shortest prefix and
sharing load in proportion to rating, each with v8's lifecycle and curve. It adds PV inverter units by array share,
and `UNIT_FAIL` and `UNIT_RESTORE` forcings. With one unit each it gives v8's bytes, proven on Kobo's October (C-DD19).
Kobo stays on v8; Kisiwa and Mto run v9. The new unit is DD3.3, 2.25 u. D-DD.21; `spec.md` §4.3.

**I5 (template v3 lacks the v8 properties; basis vocabulary exists).** Accepted. The existing `-basis` mechanism is
reused, with three new siblings and one new value, `DATASHEET_FIT`. There is no new `source` and no `source_document`;
the closed key set is unchanged. D-DD.17.

**I6 (cold and EV packs lack the scaled inputs).** The mechanism is specified, and no output is calibrated.
- **cold-thermal 2** adds crates as state from the storage ledger's movements, respiration and field heat, door
  openings per movement, a compressor COP, an auxiliary load, and Kirinyaga's efficiency condition `f_m` as a private
  condition. It uses private load parameters with their basis, and the thirteen Foundation values come from
  cold-lab-001 with cooling capacity 6 kW. With zero terms it gives v1's bytes.
- Ambient per day comes from the `cooling` weight through the manifest's own 24 °C and 2.5 %/°C.
- **EV:** a depot load manager shares the import limit across chargers with the pack's own round-robin. The roster and
  plug-in practice are inputs; `p_m` is the declared share read as the depot's practice, never inverted from a target.
- The cold bill, EV invoice and departures follow the meters, which removes the 3 % target (D-DD.20; **owner Q9**).
- The observation path: readings leave the writer as canonical readings, not through `S/observation/transform.py`.
  The writer emits the pack's public records mapped to the role set's `source_id` and `signal_id`; the mapping is
  recorded in each readings manifest's `mappings`.
- D-DD.22, D-DD.23; `spec.md` §4.4, §4.5.

**I7 (profiles cannot produce required fields).** Accepted. `spec.md` §5.2, §5.3 and §5.6 give every profile's column
→ path table. Invoicing splits into invoices and receipts, and tariff schedules go as canonical JSON (DS1b). DEPARTURE
takes the contract route: a `bool` type in `layouts_v1` with a required Y/N map and its own tests (DD2.2, 0.5 u). Each
profile ships `<id>.expected.json`, admitted with `--expected` and `--as` the analyst. D-DD.24.

**I8 (the world check would pass without checking).** Accepted. C6 judges the sealed batches written at sealing; C4
judges October only. The named paths join `CODE_PATHS` and `CHECK_CODE`, C5 runs both parity files, and C8 runs
`dd_check.py`. D-DD.28; `spec.md` DD5.3.

**I9 (restating Kobo moves more than listed).** Accepted, with the template moved out. DD3.2 regenerates
`history.json`, the goldens, the export pins and `derived-values.json`, and lists every moved figure; §0 is amended.
Template v4, its fingerprint pin and the lab moves go back to **0K4f**, which grows from 2.25 to about 2.75 u. Lab
tests and the K8 study stay on v3 at 40 kW, labelled. C-DD16 compares the world's Kobo with the slot. DD3.2 is 2.0 u.
D-DD.30.

**I10 (definition `/2`, site inputs, digest).** Accepted as stated, plus the readings files, measured books and slot
in the digest. D-DD.28; `spec.md` §4.1, DD5.3.

**I11 (WK without snapshot months).** Accepted. D-DD.28; `spec.md` DD6.2.

**I12 (exports details).** Accepted, with fixed note days: the 1st, 8th, 15th, 22nd and 29th at 10:00 local. OOO-1
keeps 26 Oct. D-DD.32.

**I13, I14, I15.** Accepted as stated. D-DD.28, D-DD.29.

**Sizes.** Rev 1 had 19.5 u in four parts; rev 2 has **30.0 u in six parts**: DD1 4.0, DD2 5.5, DD3 6.0, DD4 5.75,
DD5 5.0, DD6 3.75. No part is over 6 u. 0K4f grows by 0.5 u. D-DD.33.

**Owner questions (D-DD.34), defaults applied:**
- **Q7**, the Kobo no-load rate: default 0.62 L/h, Assumed (fit); the alternative is to keep the owner's 3.3 L/h.
- **Q8**, Q11 and Q12 gate demo acceptance: default yes.
- **Q9**, bills follow the meter: default yes, so story figures move and the stories are checked by direction.

**Open after this round:** none for the reviewer or implementer. The handshake can close once the reviewer confirms.
