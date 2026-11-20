# 4d handshake

Reviewer questions and builder pre-flight, one combined round (`.ai/RULES.md` §4). Round 1 below; answered in
`rulings.md`, "Handshake answers (round 1)", and folded into spec rev 2.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, on `main` 93b9e23e1 (spec rev 1, `rulings.md`, `reviewer-guide.md`; owner RC1-RC9,
UI standing brief, k-of-n). Severity: **High** blocks coding; Medium needs a ruling; Low is the Architect's call.
**(done)** = the answer changes what counts as done.

### High

- **R1 (done) §2.3 rules 3 and 4: a month or a day with no generator readings gives 0.000 litres, not "Not available
  yet".** Rule 3 needs *both* `not readings_held` *and* every day `NO_READINGS`; a day is `NO_READINGS` only when it has
  no accepted reading of any dispatch role (§4.2: `selection` None and `accepted_reading_count` 0). A Site whose EMS
  export carries solar and battery but no generator columns (or loses them for a week) has ASSESSED days with no
  generator interval (`dispatch_v3.py:384-388` builds runs from generator state and power only), so rules 3 to 9 pass
  and `necessary_l` and `candidate_l` read **0.000 Modelled**. Unknown read as zero. V10 sets both conditions at once,
  so no test can tell. Expected: rule 3 fires on `not readings_held` alone; a day ASSESSED with no generator reading
  in it is a `RUNNING_RECORD_GAP` (needs a per-day "generator readings held" fact in `LitreInputs`); variants V18a
  (`readings_held` False, every day ASSESSED with no spans: `NO_RUNNING_RECORD`) and V18b (one ASSESSED day with no
  generator reading: `RUNNING_RECORD_GAP`), each with a plant.
- **R2 (done) §5 "The bridge": the fixture contradicts itself.** It reads "5b's Lakeside world (5b §5.2 *without its
  own step*; 4b's and 5a's files)", but without that step Mto has no billing, receipts or fuel invoice (5b §5.2
  "Without this file's step": Mto `GAP_NOT_AVAILABLE`, portfolio −747.00, 2 of 3). The expected values need the step:
  Mto's `fuel_cost` `NOT_SPLIT DETAIL_NOT_AVAILABLE`, portfolio `fuel_cost` −755.00 **3 of 3**, and `diesel_l`'s `out`
  giving Mto `("NOT_SPLIT",)` (without the step `portfolio.py:104-110` gives Mto `actual:<leaf>` reasons). Expected:
  "5b §5.2 *with* its step (`attribution_lakeside_mto.json`)", or the without-step literals. This is done question 2.
- **R3 (done) Reviewer guide P5 cannot fail.** "Deliveries counted by calendar month, not the dip window" gives the
  same delivery set as the window in every named case: in V7 the window gains 2026-09-30T15:00Z to `lo` but no
  delivery lies there; in V16 the extra delivery (2026-11-01T03:00Z) is after `hi` and after the closing dip, so a
  calendar-month count drops it too. Expected: a variant with a delivery inside the window but outside the month (for
  example V7 plus a delivery of 50 at 2026-09-30T20:00+03:00: burned 1250, `unexplained_l` 185.000), or a closing dip
  at 2026-11-01T12:00+03:00 with a delivery at 06:00+03:00.
- **R4 (done) Reviewer guide P12 cannot fail.** For Nairobi `lo` is 2026-09-30T21:00Z, so UTC day 2026-09-30 already
  meets `[lo, hi)`: a builder who reads rule 5 "from `lo`" still sees that day NOT_ASSESSED and passes V18 as written.
  The day only rule 5's `lo - 1 day` reaches is **2026-09-29**. Expected: V18 uses 2026-09-29.

### Medium

- **R5 §2.1, §4.2: the classification strings.** dispatch-3.2 writes `"CANDIDATE_AVOIDABLE"` (`analytics/dispatch.py:32`),
  not `"CANDIDATE"`; §2.1's comment and §5's fixture say CANDIDATE. And a segment whose classification is none of the
  three is not covered: as written its litres are in neither N nor C and fall into `unexplained_l`. Expected: `RunSpan.
  claim` holds the dispatch constants (tests import them), and an unknown claim stops the month (a note, say
  `SPANS_OVERLAP`'s cause NOT_CALCULATED_YET, or a new one), with a variant.
- **R6 §4.2: a STALE or FAILED selection counts as ASSESSED.** `_dispatch_day_on` returns a selection with `status`
  STALE when accepted readings changed after the selected run (`dispatch_read.py:85-115`); §4.2 looks only at
  `selection`, so Modelled litres are served from a run that did not see the latest readings. Expected: `status` other
  than CURRENT with a selection is `NOT_ASSESSED` (cause NOT_CALCULATED_YET), or a ruling that stale runs are acceptable.
- **R7 (done) §2.2: do the spans cover the running time?** A dispatch interval runs from its first ON instant to its
  last ON instant (`dispatch_v3.py:397-432`, `first_on` = the first ON reading's `placed_at` or a power reading's
  `interval_end`); the slot that ends at `first_on` and the time from `last_on` to the OFF reading lie in no segment.
  At 5-minute reporting each run loses about one slot to `unexplained_l`; on KOBO-OCT's 36 runs that is roughly
  36 × 5/12 L = 15 L "unexplained" that the generator's own readings explain (D-4D.3 says explained running must not
  read as unexplained). The fixture writes spans by hand, so this never shows. Expected: a ruling (accept and say so
  on the figure, or widen each interval to its first slot), and Postgres test 1 extended to compare one real day's
  span coverage with its generator ON slots.
- **R8 (done) §2.1 `indeterminate_l`: the part that could not be judged never leaves `month_litres`.** `LeafValue` has
  no field for it and `LitreLeafSource.leaf` returns only `values[factor_id]`, so 5c cannot say how much of "Diesel
  needed to serve the load" is undecided (see 5c R7). Expected: say where it travels (a `sources` entry such as
  `"indeterminate_l:<value>"`, a note, or out of scope with 5c's label changed).
- **R9 §2.4: `GENERATOR_OR_TANK_NOT_DECLARED` names the wrong record for a Site with two generators.** Kisiwa
  (ON1 fixture) declares two GENERATOR components; v1 reads one each (as K3). "the Site's generator and fuel tank,
  declared in its setup" tells the operator to declare what is already declared. Expected: split the note
  (`TANK_NOT_DECLARED`, `GENERATORS_NOT_ONE`) or words that say "one generator and one fuel tank (v1 reads one
  each)".

### Low

- **R10 Reviewer guide P7: per-span rounding is undetectable.** Every fixture span is a whole number of hours (30 L)
  except V17's single span (55/12 L); rounding each *span* to 0.001 before summing gives 734.583 and 115.417, the same
  as the spec. Add a variant with two spans of 5/12 L each (0.834 rounded per span, 0.833 exact).
- **R11 §2.1 vs rule 11:** `tank` holds records in `[lo - EDGE, hi + EDGE)` (K2's `select_fuel_records` is half-open,
  `work/adapters/postgres_fuel_records.py:33`) but rule 11 admits a closing dip at exactly `hi + EDGE`. Pick one.
- **R12 §4.3 step 2:** the SFC and no-load rate are chosen in force over `[lo, hi]` only, but the dip window may run
  up to 24 h either side (V7). A curve revision at the month boundary is applied to the outside part. State it, or
  choose over the window.
- **R13 3B7a interplay:** valued litre leaves have non-`commercial:` sources, so 3B7a lists them `untracked` (3B7a
  §2.4): a corrected dip or a dispatch re-run after the snapshot never marks it out of date. Confirm this is intended
  (5c shows "Not checked for later changes").
- **R14 rule 1 vs rule 11:** between `hi` and `hi + EDGE` the closing dip may still arrive, but the read gives
  `TANK_DIPS_MISSING` (NOT_RECEIVED) rather than "month not closed". Acceptable for snapshots built days later; say so.

## Implementer pre-flight

Pre-flight of spec §0, §2 to §6 against `main` 93b9e23e1 (read-only). Verified: `ReadContext`, `LeafValue` field order
and `Missing(…, note)` (`structure/evaluate.py:51-87`); `_absent`'s shape (`structure/sources.py:124-126`);
`month_window` returns `(lo, hi, first, last)`; `ProductLeafSource.leaf` line 151 is where `LITRE_LEAVES` joins
`COMMERCIAL_LEAVES`; `CommercialLeafSource.leaf` passes the litre leaves to its fallback (`structure/money.py:164-171`:
not in `_ROWS`), so §4.3's chain works without editing `money.py`; `use_from_readings` returns a dict with
`generator_kwh` (Fraction or None) and `idle_seconds`; `relevant_readings`, `ROLES`, `GENERATOR_POWER`,
`GENERATOR_STATE`; `NO_LOAD_BASIS_KEY`, `NO_LOAD_BASES`, `no_load_basis` (`fuel_balance/service.py:24-62`); K3's
choice at `service.py:96-107` (SFC ref attribute `property_revision_id`, no-load `foundation_revision_id`);
`WindowFacts((), False, None, None, lo, hi)` positional; `_Tx(c, actions, fuel_records, tenant_id, site_id, known_at)`;
`FuelRecord.kind/occurred_at/quantity_l/root_id`; `select_dispatch_days_on(c, …, from_, to, known_at)` and the day
dict keys `available`, `selection`, `run_id`, `accepted_reading_count`, `assessment_revision_ids`; `_run_detail`'s
revisions carry `scope` (`'INTERVAL'` / `'WINDOW'`) and `result["segments"]` with `start`, `end`, `classification`;
`build_fuel_balance_store`, `build_postgres_assessment_store`; registry `diesel_l = necessary_l + candidate_l +
unexplained_l + extra_l`; 5b's unit-1 vectors (730/330/120 against 700/0/0 → −37.50, −412.50, −150.00).

- **P1 (Medium) §4.3 "`dispose` disposes all four": `PostgresAssessmentStore` has no `dispose`** (class at
  `analytics/adapters/postgres_assessment_store.py:250-2143`; it owns `_engine`). Expected: §0 allows adding one
  `dispose()` to that adapter (it is already on the collision list), or the composition disposes `_engine` through
  `analytics.composition`. Test 3's "a failing fourth builder disposes the first three" needs it either way.
- **P2 (Medium) §6 test 7 "the only 3B3 test edit" is not the only one.** `backend/tests/test_4b_money_leaves.py:55-62`
  (`STATE_TABLE`: the three in HELD_NOT_CALCULATED, and the PROVIDED set) and `backend/tests/test_3b3_structure_evaluate.py:76`
  both pin the old state; 3B7a's branch tests may pin the litre leaves' cause (NOT_CALCULATED_YET becomes
  NOT_CONNECTED through `ProductLeafSource`). Expected: §0 lists the 4b test lines too, and the packet's W6 sweep
  covers 3B7a's tests once it merges.
- **P3 (Medium) §4.1 "one REPEATABLE READ READ ONLY transaction" covers less than it says.** `_Tx.readings`,
  `sfc_history` and `no_load_history` go through the Action store (`postgres_fuel_balance_store.py:149-163`), its own
  connection, not `c`; only assets, properties and fuel records are on the read-only transaction. They are pinned by
  `known_at`, so the values are consistent, but Postgres test 2's "an INSERT through `tx.c` raises" proves only `c`.
  Expected: the spec says so (or asks for the Action store's reads on `c`, which is a larger change).
- **P4 (Low) Two `LITRE_LEAVES`:** a tuple in `structure/litres/rules.py` (§2.1) and a frozenset in
  `structure/sources.py` (§3.1). Rename one (`LITRE_ORDER`?) or have `rules.py` import the frozenset and keep order
  in its own name.
- **P5 (Low) `_run_detail` takes a `UUID`** and orders revisions `scope DESC, assessment_key`; §4.2's "in the
  revision's order" is key order, not time order. Rules sort spans themselves, so harmless; say so.
- **P6 (Low) Cost.** One snapshot build per Site reads ~34 UTC days of `select_dispatch_days_on` plus one
  `_run_detail` per ASSESSED day, and readings for the month plus 2 days. Fine for Lakeside; note for 300 Sites.
