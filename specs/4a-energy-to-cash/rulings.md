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
  4a's last commit adds it, after SC-1a's merge.
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
