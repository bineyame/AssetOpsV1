# DD2 handoff (PARTIAL: stopped at pre-flight on blockers)

Branch `task/DD2-books`, worktree `/opt/assetecon/AssetOpsV1-dd2`, from `main` `13ba9c25b`.

## Done

- **DD2.2 profile `bool` type** (commit `0db0c72de`). `layouts_v1.TYPES` gains `bool` and `BOOL_VALUES`. `check_layout`
  and `compile_profile` require a map whose values are exactly {"true", "false"} on a bool path, and refuse a bool path
  that has no map. `read_rows` writes a JSON boolean. `run_probes` P5 skips mapped paths, because P4 already probes them.
  `contracts/tests/test_dd2_bool_type.py` has 12 tests. 11 failed before the change. The 12th (a map on a non-bool,
  non-coded path is refused) already held. After the change the 3A6 and 3A3 contract suites pass: 169 passed.
- Architecture check, agent-workflow check and decision index: all pass.

## Pre-flight questions (one batch, `.ai/RULES.md` §4)

**B1 (BLOCKER, DD2.1 money).** §5.1 says "July to September values are `history.json`'s leaves: billed kWh, revenue,
collections split". `history.json` (pinned) has none of these for mini-grid. Actual = adjustments_kwh, candidate_l,
delivered_kwh, in_transit, necessary_l, om, outstanding, staff, technical/expected loss, unexplained_kwh/l,
unbilled_mapping_kwh. Plan = billed_kwh, diesel_l, om, staff. There is no diesel_cost either. Read literally ("a
MISSING leaf writes no row"), 9 of the 12 mini Site-months get no CHARGE or RECEIPT rows. C-DD2 then fails, and the
statements have no revenue for July to September.
*Default offered:* billed = delivered − technical (or expected) loss − unexplained_kwh − unbilled_mapping −
adjustments. This is the factor_map balance, and October's `period` satisfies it at all three Sites (8645, 7400, 5400).
Then revenue = billed × tariff and collected = revenue − in_transit − outstanding (the manifest `checks`), and fuel
cost = litres × `prices.diesel_usd_per_l`. These are derived figures, so they need an Architect ruling.

**B2 (BLOCKER, DD2.3/2.4 contracts).** The expenses and budget files for cold and EV are to use "mini-grid layouts
(exist)". `budget-illustrative-1`'s Line map holds only mini factors, and `expenses-illustrative-1`'s Category map has
no PENALTY. Cold plan `kwh` (and EV plan `kwh`, `offpeak_kwh`) has no leaf factor, so it cannot become a BUDGET_LINE.
DS1b's `records.py` lists these as READ_IN_AN_EXPRESSION / NOT_OWN_LINE. Ruiru's plan carries `energy_cost`, `total`
and `departures_required`, not the EV rule keys.
*Default offered:* extend both illustrative maps (cold and EV factor ids, and "Penalty": "PENALTY"). This is a
protected contract change. Plan fields without a leaf factor stay in `unwritten.json` with DS1b's reasons.

**Q3.** Cold history months carry `outstanding` but no revenue or collected. *Default:* revenue = crate_days × 0.20
(the manifest check), and collected = revenue − outstanding, all COLLECTED.

**Q4.** The ticket rows (CH-K2, CH-R7) and the named batches (B-1029, B-1031, B-1034) sit in `incident` blocks.
`ManifestView` excludes those blocks, and widening the view moves `history.json`'s `view_digest`. *Default:* a module
table holding the spec's and the manifest's values, plus a test that compares the table with the manifest. Tickets are
OPEN: the CH-K2 ACKNOWLEDGED event is the warranty claim's, not the ticket's. Contractor ref `oem-contractor` (R5: no
named counterparty).

**Q5.** Roster span. *Default:* July to October in DD2. The November nights, including the 3 Kasarani spare-bus nights
and `november_to_date.kwh`, come in DD4.3 with the readings.

**Q6.** "OOO-1's note keeps its 26 Oct delivery" cannot be met under the fixed note days (1/8/15/22/29). *Default:*
cycling everywhere in DD2. DD5.2 plants the 26 Oct revision.

**Q7.** `world.py inputs()` runs only `exports` today. It never runs `records` and never admits profiles, and
`load_emulated_exports` refuses `statements.json` (`EXPORT_FILE_UNKNOWN`). *Default:* DD2.1 stages DS1b JSON for
METER_ASSIGNMENT, TARIFF_SCHEDULE and ADJUSTMENT only. Profile admission in the build, and the statements reader, wait
for DD5 / WK.

**Q8.** C-DD2 to C-DD4 by SQL run on `commercial_record_revision` (`canonical`, `provenance`, `recognition_period`;
there is no site_code column, so a join through `site`). *Default:* the checks go live but FAIL until DD5 loads the
books. They are tested with pure judges on fixture rows, as C-DD1 is.

**Q9.** A bool cell missing from the map is refused `NATIVE_VALUE` (a map miss), not `NATIVE_FORMAT`.

## Next

After the rulings: DD2.1 (exports months, fuel notes, `months=`, `SOURCE_VERSION` "2", pins moved, DS1b staging), then
DD2.3 (cold profiles, samples, expected files), DD2.4 (EV profiles, including the invoice and departure profiles of
§5.6), and DD2.5 (statements and C-DD2 to C-DD4). Then the packet and the state entry (index-3 number 199).

## Risks

DD2.2 is a protected seam (`contracts/`) and needs its own review. The worktree venv imports main's packages unless
`PYTHONPATH` points at the worktree (or the host runner is used).
