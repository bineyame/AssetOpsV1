# 4a rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-4A.1 to D-4A.14 are applied by `spec.md` rev 1. D-4A.1, D-4A.3, D-4A.5, D-4A.6 and D-4A.10 change what the screen
will show or settle a design-pack question, so each is logged for the owner in
`specs/OWNER-AWAY/decisions-2026-11-21.md` (rows 14 to 18). None widens an authorisation: no migration, no guard
change, no database, no purchase.

## D-4A.1 The billing export states billed kWh and the meter reads state metered kWh (registry v4)

- **Ruling.** `metered_kwh` and `billed_kwh` gain `stated_by` (the customer meter reads; the billing export's USAGE
  kWh), exactly as `revenue` and `fuel_cost` did in 4b1 (D-4B.1). Their expressions stay, as `computed` and
  `detail_missing`. `check._stated` accepts a summed node whose unit is money **or kWh**; litres and every compound
  unit stay refused. Registry version 3 → 4.
- **Why.** Both figures are written in the operator's own files; computing them only from the chain above (delivered
  less losses) would hide a billed kWh the billing export states whenever a feeder meter or a band is missing, which
  is most operators (build plan §0.4). With them stated, the bridge splits revenue into kWh billed and price wherever
  the budget states billed kWh (Kobo +38.00 and 0.00; gate 5 names "kWh billed +38.00"), and splits billed kWh into
  metered kWh and the named leaks only as far as each is observed. A record its factors do not explain is shown as a
  disagreement (5b's `RECORD_AND_FACTORS_DIFFER`, D-5B.4), never forced into a split. One mechanism for money and
  kWh: the design's "Record, then Calculated" (`worked-portfolios.md` Mto table). Litres are left out because no
  slice needs a stated litre figure (4d computes them) and S8's `diesel_l` plant guards that line.
- **Cost.** 0.5 unit over the plan's 2.5; the pins of spec §6.4 move by design (the W6 sweep lists them).
- **Reverse.** Drop the two `stated_by` (v5); the leaves of 4a still fill the chain.

## D-4A.2 Delivered kWh: every bound feeder, every day of the month, or no figure

- **Ruling.** `delivered_kwh` is the sum of the `feeder_demand` energy of the LOAD assets bound by the one
  `minigrid-roles-4` binding set in force over the whole month. A day counts only when every feeder has GOOD
  readings over the whole day with no conflicting spans (`productive_energy`'s rule). A month with any uncovered day
  has no figure (`FEEDER_READINGS_GAP`) and keeps its coverage. A reading from a SIMULATED gateway carries the origin
  `demo-simulated`; a LIVE one carries `unknown` until a field-provenance rule exists.
- **Why.** Delivered kWh is the top of the chain: a partial sum understates it and the whole shortfall would land on
  "losses beyond expected", the one figure the design forbids to inflate (domain models §3.2: never called theft).
  The binding rule follows 4d's "one generator and one tank" honesty (no weighting across a re-binding). The origin
  rule keeps the owner's rule "simulated data is never shown as observed": with `unknown` alone 5c would show a
  simulated reading as "Estimated", with nothing it would show "Measured".
- **Reverse.** Allow a partial month with its coverage (one step in `month_energy`); add a provenance rule for LIVE.

## D-4A.3 The expected technical loss is declared in the Site's setup, per feeder, with its basis

- **Ruling.** Two Foundation properties on the LOAD component a feeder is bound to: `technical-loss-band` (%, below
  100) and `technical-loss-band-basis` (`GENERIC_DEFAULT`, `DESIGN_STUDY`, `METERED_HISTORY`). Every bound feeder
  must declare it, with one value across the Foundation revisions that meet the month. The onboarding file (ON1) is
  not changed.
- **Why.** D-ON1.8 left the band to 4a. The Foundation is where a Site's declared physical facts already live,
  effective-dated and revisioned ("declared truth, never evidence", `sites/models.py`), with the same basis pattern
  as FUEL-1's no-load rate and DIESEL-1's sensor accuracy; the integration design asks for "a declared property with
  effective dates". Per feeder, because the design calibrates "loss band per feeder" and a Site figure is the case
  of every feeder declaring the same value. ON1's Sites have no LOAD components (`backend/tests/fixtures/on1/`), so
  they have no feeder to read either; a band field there would be collected with no reader (D-ON1.8's own reason).
  The assumption store is a price store (currency required), so it is not the home.
- **Reverse.** Move the declaration to a per-Site field; `feeder_month`'s band step changes, nothing else.
- **Amended by D-4A.18 (handshake):** no basis property in this slice.

## D-4A.4 Technical loss is Modelled; with no band, both loss figures are "Not available yet"

- **Ruling.** `technical_loss_kwh = Σ_f delivered_f × band_f / 100`, MODELLED (a declared rate applied to a
  measurement, as 4d's litres). A feeder with no band makes technical and unexplained losses NOT_CONNECTED
  (`LOSS_BAND_NOT_DECLARED`); neither is ever 0. Metered kWh keeps its record, so the bridge shows delivered against
  metered with the losses as one RESIDUAL naming both leaves.
- **Why.** `economic-metric-and-effect-contracts.md` §2.2: "Kobo and Kisiwa report loss as one figure ... their
  unexplained cell is '—', not zero." The pack's evaluator writes 0 there (`factor_map`: `record.unexplained_kwh |
  0`); the product does not, under the owner's rule.
- **Reverse.** None needed; a declared band fills both.

## D-4A.5 Losses beyond expected: delivered less technical less metered, signed, priced only as unexplained fuel is

- **Ruling.** `unexplained_loss_kwh = delivered − technical − metered`, MODELLED, never clamped (a negative value
  means less was lost than the band expects). It enters the bridge as any kWh term does (5b unchanged: an effect at
  the target tariff), exactly as unexplained litres enter at the diesel price. It is never a recoverable amount; the
  words for it are 5c's (SC-1), and they say "investigated", never "theft", never "recover".
- **Why.** The identity `metered = delivered − technical − unexplained` must hold, or the bridge would report a
  disagreement that is the observer's own clamp. Gate 5 prices unexplained fuel (−150.00); D-5B states one rule for
  kWh and litres. Domain models §3.2 says the unexplained kWh "are never priced"; that refusal is about claiming
  money (a Finding or option valuing recovery), which this slice does not do. **Pack divergence:** with targets at
  P5's rules (leaks at zero, delivered solved), Mto's metered gap (−8.00) now splits further into delivered +160.00,
  technical −120.00, unexplained −48.00, where the pack stops at the meter. The owner may prefer the pack's stop; the
  default follows P5 (owner-approved) and 5b.
- **Reverse.** A bridge rule that stops at `metered_kwh` when its target rests on assumptions (5b), or a registry
  flag that keeps `unexplained_loss_kwh` unpriced.

## D-4A.6 The tariff is billed money over billed kWh

- **Ruling.** `tariff` = Σ amount / Σ kWh over the month's standard-class USAGE charges, DERIVED ("Calculated"), one
  currency. A tariff sheet (`TARIFF_SCHEDULE`) is not read in this slice.
- **Why.** The same rule 4b uses for the diesel price (spend over litres, D-4B.6): one mechanism for a price read
  from the operator's records. Every operator with a billing export has it; few send a tariff sheet as a file, and
  reading one needs tariff codes matched to schedules and bands (time-of-use: AR3, out of scope). Computed revenue
  then equals the usage charges, so fixed charges show as revenue's disagreement, honestly. Residual risk
  `R-TARIFF`: a mix of tariff codes reads as one average price.
- **Reverse.** A tariff-sheet reader preferred when a schedule covers the month (a queued unit).

## D-4A.7 Unmapped kWh: kWh read on meters that billing does not charge

- **Ruling.** A read is charged when a charge of the month names its meter, or names (as `account_ref`, with no meter
  subject) the customer the register assigns that meter to over the whole read. Unmapped kWh = the read kWh not
  charged. A meter with no assignment over its read (`REGISTER_GAP`) is charged only through its meter. A shortfall on
  a charged meter is not unmapped: it is billed kWh's disagreement with its factors.
- **Why.** Trace A and MAP-1: the six new meters' 140 kWh are "read on six meters installed on 3 Oct but billed to the
  old meter numbers", a correctable charge, not loss, and the register is what ties a meter to a customer (5c's
  METER_REGISTER). Defining unmapped as metered less adjustments less billed would name every billing error
  "unmapped meters" and make the leak's name untestable; the join keeps each leak named for what it is.
- **Reverse.** None expected; a per-meter billed comparison would be a new factor.

## D-4A.8 Authorised adjustments: ADJUSTMENT kWh, signed as recorded

- **Ruling.** `adjustments_kwh` = Σ of the month's ADJUSTMENT kWh quantities, a positive quantity being kWh metered
  and not billed by authorisation (a negative one adds billed kWh back). Zero when the month's billing is held and
  carries none. ADJUSTMENTs with money only (credit notes) are not kWh.
- **Why.** 2a allows either sign and fixes no meaning; the structure subtracts adjustments from metered kWh, so the
  sign that makes Trace A's clinic allowance (40 kWh) hold is positive-not-billed.
- **Reverse.** Flip the sign in one line, with the fixtures.

## D-4A.9 5a: the main factor is solved under its nearest stated heading with a target

- **Ruling.** `MAIN_OF["MINI_GRID"]["delivered_kwh"] = ("billed_kwh", "revenue")`: solved under billed kWh when the
  budget states it, else under revenue.
- **Why.** With billed kWh stated (D-4A.1), a budget line on it is its target; solving delivered under revenue would
  ignore that line, and revenue's computed value no longer depends on delivered kWh once billed kWh is stated.
- **Reverse.** Back to `"revenue"` with D-4A.1.

## D-4A.10 Productive-class kWh inside metered kWh: the registry stays as it is this fortnight

- **Ruling.** Billed kWh counts standard-class usage only (productive kWh are 4b's `productive_kwh`), as `revenue =
  billed_kwh × tariff + productive_kwh × productive_tariff` requires. Metered kWh counts every meter. A Site with
  productive-class usage therefore shows billed kWh's disagreement with metered less leaks. No registry expression
  changes.
- **Why.** The registry's expressions mirror the manifest's (the parity test); fixing it (revenue over
  `billed_kwh − productive_kwh`) is a structure change for the owner (P3B). Every demo and rehearsal Site has
  productive kWh 0 (`derived-values.json`), so nothing on screen moves this fortnight. Residual risk `R-PRODUCTIVE`.
- **Reverse.** The owner approves the expression change; a 0.5-unit registry unit with its parity update.

## D-4A.11 Metered kWh needs the register, and complete, non-overlapping reads inside the month

- **Ruling.** Metered kWh has a figure only when the meter register is held, every assignment's span inside the
  month is covered by its meter's reads, no two reads of a meter overlap, and no read straddles the month.
- **Why.** Without the register, a missing meter's read is invisible and its kWh would appear as losses beyond
  expected. A straddling read cannot be split without an assumption. Claim only what was tested.
- **Reverse.** Prorate straddling reads by days (labelled), a later unit if a pilot's cycles need it.

## D-4A.12 No user-facing text; 5c names the records (amendment to 5c §2.3)

- **Ruling.** 4a serves codes only (causes and notes, spec §2.4 `NOTES`). The records they name are added to 5c's
  `RECORDS`, in this order after `METER_REGISTER`: `METER_READS` "the customer meter reads for the month";
  `LOSS_BAND` "the expected technical loss of each feeder, declared in the Site's setup". `TARIFF_SHEET` leaves
  `RECORDS` (no leaf names it now). `RECORD_KEYS` become: `technical_loss_kwh` (FEEDER_METER, LOSS_BAND);
  `unexplained_loss_kwh` (FEEDER_METER, LOSS_BAND, METER_READS, METER_REGISTER); `metered_kwh` (METER_READS,
  METER_REGISTER); `unmapped_kwh` (METER_READS, METER_REGISTER, BILLING); `tariff` (BILLING); the rest unchanged.
  `NOTE_KEYS` gain: `FEEDER_NOT_BOUND`, `FEEDER_BINDINGS_CHANGED`, `FEEDER_READINGS_GAP` (FEEDER_METER);
  `LOSS_BAND_NOT_DECLARED`, `LOSS_BAND_CHANGED` (LOSS_BAND); `METER_READ_STRADDLES`, `METER_READS_OVERLAP`,
  `METER_READS_INCOMPLETE`, `NEEDS:CUSTOMER_METER_READ` (METER_READS); `NEEDS:METER_ASSIGNMENT` (METER_REGISTER);
  `NEEDS:CHARGE` (BILLING). The words are SC-1 statements (D-SC1.28). Who builds it: if 5c has not merged when 4a
  starts, 5c's builder takes this amendment (a line in `specs/5c-deep-dive-screen/rulings.md` points here); if it has,
  4a's last commit adds it, after SC-1a's merge. **Amended by D-4A.20 and D-4A.24 (handshake):** `adjustments_kwh`
  (BILLING), `BILLING_ADJUSTMENTS` leaves `RECORDS`; `NOTE_KEYS` gains `METER_REF_CONFLICT` (METER_READS,
  METER_REGISTER).
- **Why.** D-SC1.28: no hand-built served text. 5c's current keys conflate the meter register with the meter reads
  and name a tariff sheet 4a does not read; leaving them would name the wrong record on screen.

## D-4A.13 No migration, no guard change; the feeder read is a SELECT on a named reader

- **Ruling.** `feeder_month` is a read-only method of `mini_depth/read.py` (`MiniDepthRead`), already a named reader
  of the persistence guard (`configuration-persistence.ps1:1075`). If `check-architecture.ps1` refuses
  `structure/energy` importing it, that is a handshake question; no guard is edited by this unit.
- **Why.** The delegation does not widen authorisations (OWNER-AWAY row 5); 4d set the pattern of adding a read to an
  existing store rather than a new adapter.

## D-4A.14 One read per Site-month, one cutoff

- **Ruling.** The commercial inputs come from one `latest_revisions` call at `known_at`, CHARGE and ADJUSTMENT
  placed by `recognition_period` (3A4's rule, D-3A4.2); the month is closed when its end is at or before the cutoff;
  `EnergyLeafSource` reads once per `ReadContext` object (D-4B.12).
- **Why.** 3A4's months carry no subjects, which the unmapped join needs; one call keeps every energy figure on one
  snapshot of the store, and 3B7a's pinned reads (`known_at` set) reproduce.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the owner's delegation. One answer per question of `handshake.md` (R1 to R6,
I1 to I5), each checked against `main` at `8eff70625`; all are folded into `spec.md` rev 2 and `reviewer-guide.md`
rev 2. D-4A.18 and D-4A.20 change what the owner was told or what the screen will name, so each is logged in
`specs/OWNER-AWAY/decisions-2026-11-21.md` (rows 19 and 20). No authorisation is widened: no migration, no guard
change, no database touched by this answer, no new external reader.

## D-4A.15 (R1) Mto's 300 and 120 run from real readings and a real Foundation band (PG1b)

- **Ruling.** A new Postgres test PG1b joins feeder rows → `feeder_month` → the Foundation band → technical →
  unexplained. World: the Kobo producer world of D-4A.22 (three feeders `load-clinic`, `load-res`, `load-mill`; a
  `minigrid-roles-4` set in force over all of October). Readings, hourly `INTERVAL_MEAN` in kW, GOOD, every
  Site-local day: clinic 2 kW every hour (48 kWh a day); res 4 kW every hour (96); mill 2 kW for 23 hours and 4 kW
  for the 18:00-19:00 local hour (50) on days 1 to 30, 1.5 kW every hour (36) on day 31. Totals: clinic 1488, res
  2976, mill 1536, delivered **6000** (Mto's figure, 194 a day on days 1 to 30 and 180 on day 31). Band: 5 on each
  LOAD (published as in D-4A.22), so technical **300** (74.4 + 148.8 + 76.8). `StoreEnergyInputs.read` at `known_at`
  2026-11-02T00:00Z gives delivered 6000 MEASURED, coverage (31, 31), origins (`demo-simulated`,), technical 300
  MODELLED; this Site holds no commercial record, so metered is NOT_CONNECTED. The test then feeds the same
  `EnergyInputs` with its commercial fields replaced by test 1's §5.1 literals (`dataclasses.replace`: `held`,
  `charges`, `adjustments`, `reads`, `assignments`) to `month_energy`: metered 5580, unexplained **120**. Done
  question 1 keeps its words; its evidence becomes tests 1, PG1b and PG2.
- **Why.** The reviewer is right that no test joined the chain; a band read from a hand-written `EnergyInputs` proves
  nothing about the Foundation read. Three feeders with literals that sum to Mto's numbers prove both the "every
  bound feeder" rule and the band per feeder, on the only world on `main` with a `minigrid-roles-4` feeder set.
  Hourly readings (2,232) keep the test small; the envelope contract sets no maximum interval
  (`source_envelope_v3.py:282-289`) and `productive_energy` integrates any interval.
- **Reverse.** Drop PG1b and reword done question 1 to "from `EnergyInputs`".

## D-4A.16 (R2) Every step of §2.4 has a named variant, and a table test proves the map is whole

- **Ruling.** Spec §5.4 gains V18 to V26 and V9b/V9c (D-4A.19, D-4A.24) and a step map (§5.4b): every (factor,
  step) of §2.4 names the variant that reaches it, plus the two ordering checks (delivered step 2 before 3: V26;
  technical step 2 before 3: V21). Test 2b is table-driven over the map: for each row it asserts cause, note and
  `value is None`; a second assertion compares the map's keys with a hand literal `STEPS` of §2.4 (every step
  once). Coverage on delivered is set only when the feeders are `ONE_SET` (an empty feeder list would otherwise
  cover every day vacuously). With `BINDINGS_CHANGED` the feeder list is empty, so delivered step 4 cannot apply
  after step 3; V26 covers the order that can fail.
- **Why.** Each step is an honesty path; a step no test reaches can turn into a 0 unseen. The map makes "each step
  is hit" checkable by the reviewer (guide item 2).
- **Reverse.** None needed.

## D-4A.17 (R3) "Never 0" is asserted on the evaluated structure; the registry's `absent` stays and is unread

- **Ruling.** PG3(a) asserts, on Kobo through `build_structure_read(URL).read.site` (no feeders bound in the
  commercial world): `delivered_kwh`, `technical_loss_kwh` and `unexplained_loss_kwh` value None, NOT_AVAILABLE,
  cause NOT_CONNECTED, note `FEEDER_NOT_BOUND`; `metered_kwh` stated 8690 RECORDED with `computed` None;
  `adjustments_kwh` 45, `unmapped_kwh` 0. PG1(e) asserts the band's own absence through the same read on the
  producer Site before the band is published: `technical_loss_kwh` and `unexplained_loss_kwh` value None,
  NOT_AVAILABLE, `LOSS_BAND_NOT_DECLARED`. The `absent` metadata of `unexplained_loss_kwh` (`ZERO_WHEN_HELD`) is
  **not** changed: it mirrors the manifest (`test_3b1_structure_registry.py:113`, parity), and the evaluator reads
  `absent` only for `OPTION_ONLY` (`evaluate.py:200`). Test 8 adds: no module under `structure/energy/` reads an
  `absent` attribute (`ast`). Residual risk `R-ABSENT-META` in the packet: the row says zero-when-held where the
  product says "Not available yet"; the fix is a manifest change queued with D-4A.10's (owner, P3B).
- **Why.** The reviewer's point holds: only the pure layer was tested. The correction to the question: in the
  commercial world Kobo has no feeders, so the read gives `FEEDER_NOT_BOUND` (technical step 1 precedes the band),
  and metered is stated (reads and register are held), so `metered_kwh` is present with `computed` None, not
  absent. `LOSS_BAND_NOT_DECLARED` through the real read needs bound feeders, hence PG1(e).
- **Reverse.** Change the row's `absent` to `MISSING` with the manifest when the owner approves the structure change.

## D-4A.18 (R4) The band's basis is dropped from this slice

- **Ruling.** Only `technical-loss-band` is added (§4.1). `technical-loss-band-basis`, its `STATE_PROPERTY_VALUES`
  entry and test 9's basis cases are removed; `test_w205a_ev_vocabulary.py:131` therefore does not move. D-4A.3
  stands otherwise (Foundation property on the LOAD component, per feeder, ON1 unchanged).
- **Why.** D-4A.3 refused an ON1 field because it would have no reader; the basis is the same case: no step of §2.4,
  no `LeafValue` field and no 4a screen reads it, and the evidence class MODELLED already says the figure rests on a
  declared rate. A basis becomes useful when the band's tolerance is judged (the Finding's, spec §9); that slice adds
  it with its reader. Logged as OWNER-AWAY row 20 (row 15 told the owner "with its basis").
- **Reverse.** Add the basis property with the slice that reads it (one property, one state set).

## D-4A.19 (R5) The customer join's negative case: V9b and V9c

- **Ruling.** Two variants on §5.1. **V9b:** add a USAGE STANDARD charge with no subject, account `C-0415`, 25 kWh,
  10.00 USD: unmapped **115** (the `M-2204` read, 25 kWh, is charged through its customer), billed 5425, tariff
  0.4 (2170.00 / 5425). **V9c:** V9b with the `M-2204` assignment removed: unmapped **140** (the read has no
  customer; nothing names its meter), billed 5425. Plant P20 (the account route matches a customer the meter was
  ever assigned to, ignoring the read's span) fails V9c; P6 names V9b as well as test 1.
- **Why.** In §5.1 the six new meters are uncharged whatever the register says, so V9 cannot fail on the join. The
  pair shows the account route both reaching a read and losing it with its assignment.
- **Reverse.** None needed.

## D-4A.20 (R6) `adjustments_kwh` names the billing export; `BILLING_ADJUSTMENTS` leaves 5c's records

- **Ruling.** In D-4A.12's amendment to 5c §2.3: `RECORD_KEYS` `adjustments_kwh` becomes (BILLING), and
  `BILLING_ADJUSTMENTS` ("billing adjustments (credit notes)") leaves `RECORDS` (no other leaf names it; checked in
  `specs/5c-deep-dive-screen/spec.md`). 5c's rulings line that points to D-4A.12 names this answer. Logged as
  OWNER-AWAY row 19 (a record name on the screen changes).
- **Why.** 4a reads ADJUSTMENT lines with a kWh quantity, which arrive in the billing export (`billing_export`
  batch); its absence note is `NEEDS:CHARGE`, which maps to BILLING. Asking an executive for credit notes to fill a
  kWh figure would name a record that cannot fill it (D-4A.8: credit notes are not kWh).
- **Reverse.** Restore the key with words naming authorised kWh allowances, if a separate allowance register appears.

## D-4A.21 (I1) The Kobo billed-kWh budget line is version `budget-2026-v1`

- **Ruling.** §5.5 step 4: `version_ref` `budget-2026-v1`, `line_ref` `billed_kwh`, `source_record_id`
  `BUD-2026-10:KOBO-001:billed_kwh`, no currency, batch `budget_workbook` as 5a's Kobo lines. PG3(a) also asserts
  that Kobo's revenue, fuel cost, O&M and staff targets are still used (no `BUDGET_VERSIONS` unused line).
- **Why.** Confirmed: every Kobo line in `targets_lakeside.json` is `budget-2026-v1`, and `lines.py` `_classify`
  rule 1 blocks every line of the month when two versions meet (D-5A.1). `B-2026` was a spec slip that would have
  removed every Kobo target. Rule 4 passes: `billed_kwh` is not money and the line carries no currency.
- **Reverse.** None needed.

## D-4A.22 (I2) PG1's harness: the Kobo producer world with a roles-4 set, hourly interval readings

- **Ruling.** PG1 and PG1b share one world built as `test_walk1_productive_producer_postgres.py` builds it
  (`pgb.imported`, `pgb.convert`, `producer.configure_at`) but with `IMPORT_AT` 2026-08-31T06:00Z and `INSTALL_AT`
  2026-09-01T06:00Z, so the `minigrid-roles-4` set (install + 27 min) covers all of October; Site zone
  `Africa/Addis_Ababa` (UTC+3, no daylight saving; the month window is Nairobi's). Readings go through central
  ingestion with a helper local to the test, `interval_envelope(kit, device, seq, end, kw)`, built on
  `test_s4_consequence_store_postgres.py:100`'s `INTERVAL_MEAN` shape (interval one hour, ending at `source_time`),
  sealed against the roles-4 set revision (the `Kit` class pointed at that revision's id), gateway mode SIMULATED.
  One batch per feeder per Site-local day, day `d`'s batches received at 2026-10-`(d+1)`T00:30Z (day 31's at 2026-11-01T00:30Z) (one
  `ingestion` service per receipt instant). Order: days 1 to 3; PG1's assertions; the band published with the
  Foundation service clock at 2026-10-04T01:00Z, effective `INSTALL_AT` + 28 min, on each LOAD
  (`{"property_key": "technical-loss-band", "value": 5, "unit": "%", "source": "SITE", "source_version": 1}`, as
  `declare_supply_uses` does); days 4 to 31; PG1b. The `Kit` world of `test_s2_evidence_ledger_postgres.py` is not
  used (its set is `minigrid-roles-1`, `kobo-001-bindings.json:5`, and `Kit.envelope` writes `STATE_AT_INSTANT`
  with no interval, line 100). Pre-flight (d), a hard stop: seal one feeder batch after a Foundation change and
  print its disposition; if it is not ACCEPTED, a mid-build question before PG1b is written.
- **Why.** The only `main` world with a `minigrid-roles-4` feeder set is the producer's (`demo_combined_kobo.py:123`);
  the Foundation service splits only the revision in force at the change (`foundation_service.py:557-600`), so a
  band published at + 28 min carries over the month and is invisible to a cutoff before its recorded time, which
  PG1b(c) uses as the band's own cutoff check (P24).
- **Reverse.** None needed.

## D-4A.23 (I3) A live read passes no cutoff to the reads; a refusal or an outage propagates

- **Ruling.** `EnergyInputsPort.read(site, month, known_at: datetime | None, now: datetime)`. `EnergyLeafSource`
  passes `ctx.known_at` (None for a live read) and `self._now()`. `StoreEnergyInputs.read`: `closed = hi <= (known_at
  or now)`; `feeder_month(..., known_at=known_at)` (None: the reader's own database read time) and
  `latest_revisions(..., known_at=known_at)` (None: no filter). `MiniReadRefused` and `MiniReadUnavailable` are not
  caught anywhere in `structure/energy/`: they propagate as 4d's litre reads do (no `except` in `structure/litres/`
  or `structure/read.py`). Test 6b (no database): a fake reader records the `known_at` it receives (None for a live
  context, the pinned instant otherwise) and, set to raise `MiniReadUnavailable`, the error leaves
  `EnergyLeafSource.leaf` unchanged (`pytest.raises`). Plants P22 and P23.
- **Why.** `_readonly` refuses a `known_at` later than `clock_timestamp()` (`read.py:415-416`); the application
  clock may run ahead of it, so a live read must not invent a cutoff. A refusal or outage is a bug or an outage,
  never a figure and never 0; turning it into an absence would show "Not available yet" naming a record the
  operator already sent.
- **Reverse.** None needed.

## D-4A.24 (I4) The meter is `subject.ref`; a record whose `body.meter_ref` differs blocks metered kWh

- **Ruling.** For reads, assignments and charges the meter is `subject.ref` (required on reads and assignments by
  2a, `records_v1.py:230-246`; the only meter field of a charge). `MeterRead` and `Assignment` gain `body_meter_ref:
  str`. New metered step 4: a read meeting the month, or an assignment whose span meets `[first, next_first)`, with
  `meter_ref != body_meter_ref`: NOT_CALCULATED_YET, note `METER_REF_CONFLICT` (unmapped and unexplained follow
  metered). `NOTES` gains it after `LOSS_BAND_CHANGED`; 5c `NOTE_KEYS` maps it to (METER_READS, METER_REGISTER).
  V18 and plant P21.
- **Why.** 2a does not require the two fields equal; picking one silently would be a silent choice on a record that
  contradicts itself. The case is rare (pseudonyms are per tenant and class, so equal refs stay equal), and the cost
  is one step and one note.
- **Reverse.** Treat a mismatch as out of scope and read `subject.ref` only (drop the step).

## D-4A.25 (I5) The sweep, by class; stored v3 snapshots read "rebuild needed" until 3B7a rebuilds them

- **Ruling.** §6.4 is rewritten as a class sweep (W6): every test asserting the MINI_GRID version, the stated rows,
  the state tables, the property tables, or a revenue `NOT_SPLIT`. Named pins found on `main` and missing from rev 1:
  `test_3b7a_site_inputs_seam.py:49` (`["revenue", "fuel_cost"]` → `["metered_kwh", "billed_kwh", "revenue",
  "fuel_cost"]`, registry row order), `test_4b_money_leaves.py:526` `STATED_TABLE`, and
  `test_w402_roles_properties.py:91-109` (the definitions table and `MINIGRID_PROPERTY_CARRIERS`, each gaining
  `technical-loss-band`). Stored snapshots: a 3B7a snapshot built at structure version 3 is served
  `REBUILD_NEEDED` with freshness reason `STRUCTURE_VERSION` (`test_3b7a_structure_snapshot.py:440`), never as
  version 4 and never with a figure. 4a writes no migration and touches no stored snapshot; 3B7a's own build
  rebuilds them, and the walkthrough database is rebuilt at the clean-database step (coordinator), not by 4a. The
  packet states this.
- **Why.** The rev 1 sweep listed instances; the class rule finds the seam pin and the property-table pins the
  implementer and this check found. The snapshot store already refuses a version it was not built for, which is the
  honest behaviour (a v3 snapshot lacks the stated kWh nodes).
- **Reverse.** None needed.

## D-4A.26 Size: 4.0 units in three units, no split

- **Ruling.** Unit 1 1.5 (rev 1's 1.25, plus the step map, V18 to V26, V9b/V9c, the conflict step, test 6b); unit 2
  1.5 (rev 1's 1.0, plus the producer harness, 2,232 readings, the band publication, PG1(e) and PG1b; less the
  basis); unit 3 1.0 (rev 1's 0.75, plus PG3(a)'s added assertions and plants P19 to P27). Under 6 units: no split.
- **Why.** The answers add tests and one rule step, no new mechanism.
