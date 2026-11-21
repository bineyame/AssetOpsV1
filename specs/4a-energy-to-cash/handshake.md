# 4a handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Read: `spec.md`, `rulings.md`, `reviewer-guide.md`; figures re-derived by hand from spec §5 (Mto 6000, 300, 5580,
120, 40, 140, 5400, 0.4; Kobo 9100, 8690, 45, 0, 8645, 0.4; V10 109 and 5431; V12 5750 and -50; P1 279; P5 310;
Kobo bridge 95 x 0.40 = +38.00, price 0.00). All reproduce from the fixtures named, and Kobo's budget revenue 3420
equals 8550 x 0.4, so the +38.00 is consistent with 5b's existing Kobo RESIDUAL. The questions are about what the
tests prove, not the arithmetic.

**R1 (done). Spec §6.1 test 1, §6.2 PG2, §8 question 1: nothing runs Mto's 6000, 300 and 120 from readings and a
declared band.** Done question 1 says "from feeder readings, a declared band and the operator's records (tests 1,
PG2)". Test 1 feeds `month_energy` a hand-written `EnergyInputs` (band already DECLARED, `day_kwh` literals); PG2's
Mto has no feeder (`FEEDER_NOT_BOUND`); PG1 uses Kobo and never reaches a band. So the chain feeder rows ->
`feeder_month` -> Foundation band -> technical 300 -> unexplained 120 is joined by no test, and neither is the
`technical-loss-band` read from a real Foundation revision. Expected: add one Postgres test (PG1b) on a Site with a
`minigrid-roles-4` set, one LOAD component with `technical-loss-band` 5, and readings giving 194 kWh a day for a
month (or a smaller closed month with its own literals), asserting delivered, technical and unexplained through
`StoreEnergyInputs`; or reword done question 1 to "from `EnergyInputs`" and say so in the packet.

**R2 (done). Spec §2.4 table, §5.4, §8 question 3: "each variant gives exactly its row" does not reach every step.**
Steps with no named variant: `delivered` step 3 (`FEEDER_BINDINGS_CHANGED`, only `feeder_month` is tested, not the
value it produces) and its ordering against step 4; `technical` step 3 on its own cause; `metered` step 1 (no
`CUSTOMER_METER_READ` held, V5 removes the register, not the reads) and step 7 (no read inside the month);
`adjustments` step 3 (charges held, none in the month); `billed` step 3 (same); `tariff` step 3 (`S` empty although
charges exist, e.g. only FIXED or only PRODUCTIVE lines); `unmapped` steps 2 and 6. Each is an honesty path ("Not
available yet", never 0). Expected: a table-driven test whose rows are exactly the steps of §2.4, each asserting
cause, note and `value is None`, plus a check that every step has a row; the reviewer guide gains "each step of
§2.4 is hit by a named test" as item 2's evidence.

**R3 (done). Spec §6.2 PG3(a), §8 question 2: Kobo's "never 0" is proved only at the pure layer.** Test 1 asserts
Kobo technical and unexplained absent on `month_energy` output. No test reads Kobo through
`StructureRead.site` and checks the evaluated factors: `technical_loss_kwh` and `unexplained_loss_kwh` leaves
NOT_AVAILABLE with `LOSS_BAND_NOT_DECLARED`, `metered_kwh` stated absent with `computed` None, and (the
interesting one) `unexplained_loss_kwh` not turned into 0 by anything downstream. The registry row still says
`absent="ZERO_WHEN_HELD"` for `unexplained_loss_kwh`, `unmapped_kwh` and `adjustments_kwh` (`rows_mini_grid.py`):
only the last two are meant to be zero when held (D-4A.4, D-4A.5). Expected: PG3(a) asserts those four Kobo values
on the evaluated structure, and the packet says the unexplained row's `absent` metadata is unread by the evaluator
(or the spec changes the row; it lists no such edit).

**R4 (done). Spec §4.1, D-4A.3, §6.1 test 9: `technical-loss-band-basis` has no reader and no rule.** D-4A.3 rejects
an ON1 field because it "would be collected with no reader"; the basis is the same: `FeederInput` carries no
basis, no §2.4 step uses it, and nothing says a band needs one. Expected: either the validator refuses a band
declared without a basis (test 9 adds it) and the spec names what reads the basis (5c's words, or the Finding
tolerance later), or the basis is dropped from this slice. The answer changes what counts as done.

**R5 (done). Spec §5.4 V9, reviewer guide P7: the customer join's negative case is not exercised.** In §5.1 the
six new meters are uncharged whether or not the register is held, because the `M-OLD-n` charges name their meter
(subject METER), so they never reach the account route. V9 (remove the `M-2203` assignment) therefore gives 140
before and after; P7 (a no-assignment read dropped) is caught only through 118, which is a different defect. What no
variant shows: a read charged **through** its customer that becomes unmapped when its assignment is removed.
Expected: V9b: add a charge with no subject, account `C-0415`, 25 kWh, to §5.1; unmapped 115; remove the `M-2204`
assignment: unmapped 140 (the account no longer reaches the read). P6 should name V9b as well as test 1.

**R6 (done). D-4A.12 and 5c §2.3: `adjustments_kwh` keeps `BILLING_ADJUSTMENTS`, "billing adjustments (credit
notes)".** 4a reads ADJUSTMENT lines with a kWh quantity (authorised allowances); D-4A.8 says credit notes are not
kWh. 5c's `RECORD_KEYS` would tell an executive to supply credit notes for a kWh figure that credit notes cannot
fill, while the note `NEEDS:CHARGE` maps to `BILLING`. D-4A.12 says "the rest unchanged". Expected: `adjustments_kwh`
(BILLING) only, or `BILLING_ADJUSTMENTS` reworded "billing adjustments (authorised kWh and credit notes)"; the
5c line in `specs/5c-deep-dive-screen/rulings.md:229` follows.

## Implementer pre-flight questions

Pre-flight results (spec §0): (a) with `structure/energy/composition.py` importing `mini_depth.read` and
`inputs.py` importing `site_outcomes.productive_use` and `mini_depth.store`, `tools/check-architecture.ps1` on a
scratch copy printed "Architecture check passed." (needs `ASSETOPS_GUARD_PYTHON` set in a fresh worktree); no
D-4A.13 question. (b) The Kobo `Kit` binding set is **not** `minigrid-roles-4` (I2). (c) `Kit` readings are
received at 2026-10-09T08:30:00Z (`RECEIVED`), so any `known_at` after 2026-11-01T00:00+03:00 passes. Checked and
matching: `check._stated` (`check.py:185`), `STATED_STATE`/`SOURCE_STATE` literals (`sources.py:36,73`),
`CommercialLeafSource.stated` (`money.py`), `MiniDepthRead._readonly`, `productive_energy`, `latest_revisions`,
`RevisionRow`, the four canonical kinds, 5a `MAIN_OF` (`rules.py:46`, `read.py:164`), 3B2 (it added `check_pins`;
`_stated` untouched), `ORIGIN_ORDER` (holds `demo-simulated`), pseudonyms (one per tenant and class). 5c is not on
`main` (no `RECORD_KEYS`), so D-4A.12's "5c's builder takes it" path applies and 4a's own tests do not touch 5c.
`month_window` returns `(lo, hi, first, last)`; `next_first` is `last + 1 day` (no question).

**I1 (done). Spec §5.5 step 4: the Kobo budget line's `version_ref` `B-2026` blocks every Kobo target.**
`targets_lakeside.json` declares Kobo's revenue, fuel cost, om and staff under `version_ref` `budget-2026-v1`. With a
second version in one month, `lines.py` `_classify` rule 1 returns `BUDGET_VERSIONS`, uses no line and blocks them
all (D-5A.1: never pick a version). PG3(a) would then show no target at all, not +38.00. Expected: `version_ref`
`budget-2026-v1`, `line_ref` `billed_kwh`, source system as the 5a Kobo lines; the packet checks that Kobo's other
budget lines are still used. (Currency stays absent: `billed_kwh` is not money, rule 4 passes.)

**I2 (done). Spec §6.2 PG1 and §0 pre-flight (b): the Kobo `Kit` cannot produce the data PG1 needs.** (1)
`conversions/kobo-001-bindings.json` declares `role_set: minigrid-roles-1`; `feeder_month` takes only
`minigrid-roles-4` sets, so it returns NOT_BOUND and PG1's "one set, three feeder bindings" fails. (2)
`Kit.envelope` writes `STATE_AT_INSTANT` with `interval_start`/`interval_end` None, and `feeder_month` returns only
rows with both set, so the 864 readings would be 0 (`INTERVAL_MEAN` envelopes exist in `test_s4_consequence_store_
postgres.py:100`). (3) PG1 never gives the Foundation a LOAD component with a band (R1). Expected: PG1 builds on the
`test_walk1_productive_producer_postgres.py` world (Kobo producer, Foundation revision with feeder supply uses) or
`test_w402_authored_v4_postgres.py` for a roles-4 set, with an `INTERVAL_MEAN` helper local to the test; name the
chosen harness in the spec.

**I3 (done). Spec §4.2, §3: what the energy source does when the feeder read refuses.** `_readonly` raises
`MiniReadRefused("INVALID_KNOWN_AT")` when `known_at` is later than the database clock, and `MiniReadUnavailable` on
a database error. For a live read `known_at` is `now()` from the application clock, which can run ahead of the
database's `clock_timestamp()`. The spec lists no absence for either. Expected: a live read passes `known_at=None`
to `feeder_month` (the reader's own read time) and uses `now()` only for `closed`; a refusal or unavailable read
propagates (a bug or an outage, never a figure and never 0), with one test; or name a cause and note instead.

**I4 (done). Spec §2.4 `MeterRead`, `Assignment`, `Charge`: which field is the meter.** A read and an assignment
carry the meter twice, `subject.ref` and `body.meter_ref` (both pseudonymised as `M`); 2a does not require them
equal; a charge has only `subject`. The join compares `subject == ("METER", m)` to the read's meter. Expected: the
spec says `subject.ref` for all three (the one 2a requires on every kind) and a refused record (subject differs from
`body.meter_ref`) is out of scope, or the adapter treats a difference as `METER_READS_OVERLAP`-style ambiguity with
its own note.

**I5 (done). Spec §6.4: the sweep misses pins that fail by design.** `test_3b7a_site_inputs_seam.py:49` asserts
`list(inputs.stated) == ["revenue", "fuel_cost"]` (it becomes four keys). Registry v4 also makes every stored 3B7a
snapshot built at version 3 a version mismatch (`test_3b7a_structure_snapshot.py:440` shows the refusal), so any
snapshot already stored in a demo database is refused until rebuilt. Expected: the sweep names the seam test; the
packet states that stored v3 snapshots are rebuilt by 3B7a's own build and that 4a does not touch them (no
migration), or the spec says what serves a v3 row.
