## Why it is split (sizing ruling, CH6-R S1)

The plan's 6 units predate two additions: the OL-1 reshape with its ratchet guard (about 1 unit, plan §2.4) and the PC-1 money and verdict claims (about 1 unit, BASE-1). Counted per unit (§A10, §B9) the slice is **11 units**. It splits along the backend/estate seam:

| Slice | Lane | Units | Depends on | Delivers |
|---|---|---|---|---|
| **CH-6a** contributions, strategies, OutcomeEvaluator and the Site nodes | 1 | 6 | CH-5b (lane order), CH-5a2 (claim type, SiteChain) | `OutcomeContribution` records and the ratchet guard (OL-1). The strategy registry (AG-15). `OutcomeEvaluator`: A3 verdict over graded days, A4 earnings, the potential node, the evidence-class authority, the I-19 precedence fix. PC-1 money and verdict claims. Every board row and SiteChain outcome carries `nodes: {kpi, earnings, potential}`. MG-1 reads day snapshots, not a recount of readings. |
| **CH-6b** Portfolio from EstateChain and the Grow three parts on screen | 1 | 5 | CH-6a | EstateChain rows and earnings over the same graded window for every Site (A6, I-04). The Portfolio cards render server claims; the browser card rules are deleted (I-05, I-16, I-24). The Grow row in three parts on the board and the Portfolio card (M3, I-07). COH-17 over money and verdicts. |

- Lane 1 grows by 5 units (6 → 11). The plan's §2.1, §3 and §8 rows are updated with this sheet (**(away)**, D-AW-4).
- Order: CH-5b → CH-6a → CH-6b on lane 1. CH-6b's L3m step needs MD-0 (merged before CH-5a1). CH-9 (lane 2) may merge before or after CH-6b; §B6 says what each order means.

## CH6-R rulings (none needs the owner, except as marked)

| # | Gap (code reality) | Ruling |
|---|---|---|
| R1 | OL-1 record shape vs today's table. `ENTRIES` (`B/outcomes/outcome_map.py:16-35`) holds **15** keys (4 Findings, 3 signals, **8** warnings; the plan's "7 warnings" is a miscount). It has 14 importers (P2 lists them), not nine. | `CONTRIBUTIONS: tuple[OutcomeContribution, ...]` with exactly the plan §2.4 fields. **`ENTRIES` is derived**: for each record with `source` kind in {FINDING, SIGNAL, WARNING} and `node == "status"`, grouped by source, `moves` = MOVES records by `rank`, `checked` = CHECKED records by `rank`. A test asserts the derived dict equals today's literal, kept verbatim in the test. `DOMAIN_ALIAS`, `@LINKED`, `outcome_roles`, `categories_for`, `lens_flags`, `thread_signal_key` are unchanged. No importer changes. |
| R2 | The node records have no today equivalent. | The new records (§A2.2) are `node` in {kpi, earnings, potential}. They never appear in `ENTRIES`. For a `kpi` record, `driver` is the **objective measure key** (`B/outcomes/objectives.py:57-73` `MEASURES`), so the evaluator finds the snapshot measure behind an objective without a second table. |
| R3 | The ratchet (plan §2.4, AG-31 pre-demo part). Today's literal sites: `objectives.py:58-71` (6), `site_outcomes/mini.py:417-419,480,502,559-562`, `cold.py:128-130,266`, `ev.py:100,156-157`, `objective_facts.py:20`, `read.py:65`; key constructions `board.py:211,305,930`, `mini.py:428-430`, `warnings.py:162,168`. | **`tools/checks/check_outcome_ids.py`** (AST, run from `tools/check-architecture.ps1`, guard A). Outside `outcomes/outcome_map.py` and `outcomes/catalogue.py`, and outside `backend/tests/`, it counts per file: (a) a `str` constant that fully matches `(MG\|CC\|EV)-\d+`; (b) a `str` constant, or the first constant part of a `JoinedStr`/`BinOp` concatenation, that starts with `FINDING:`, `SIGNAL:`, `WARNING:` or `MEASURE:`. The baseline `tools/checks/fixtures/outcome_id_baseline.json` is `{file: {"count", "owner"}}`, generated on the CH-6a head after the §A6 removals. A file's count rising, or a new file with a count, fails. `--shrink` rewrites downward only. Owners: CH-10a for `objectives.py` and the `settled` dicts; CH-7 for the cold/EV composers. Self-test `tools/checks/test_check_outcome_ids.py`. |
| R4 | Strategies (AG-15) and what each may compute. | Registry `B/chain/strategies/` with six keys. **No strategy computes new money.** `priced_energy@1` multiplies stored snapshot money only (the snapshot's `money` is already measured × declared price, `B/chain/measure_impls.py:152,358`), or headroom kW × 1 h × the declared price for a potential. `avoided_cost@1` reads the stored consequence through `ChainReader.money_head` (CH-5a1). `recorded_amount@1` returns `NOT_AVAILABLE` (no billing source, AG-11). Load-time check: every `CONTRIBUTIONS.strategy` resolves, or the app refuses to start (beside CH-5b's graph check). |
| R5 | A3 inputs. Today MG-1's month counts a "checked day" as any local day with GOOD coverage, and sums every day (`B/site_outcomes/mini.py:588-618`). | **MG-1 reads day snapshots.** `value` = Σ `productive_kwh.value.kwh` over the month's COMPLETE and PARTIAL days (every subject); `checked` = COMPLETE days only; LOW days are shown and not totalled; only MEASURED/RECORDED rows count (`AUTHORITY`, design §4.3b). `judge_month` (`objectives.py:127`) is reused unchanged on that `Reading`. `_productive_month` is deleted. The value change on the polish clone is listed old → new (expected: Kobo checked days fall, because 8-of-24 h days are PARTIAL). |
| R6 | Completeness of the other KPIs. MG-2 is per day; CC-1, CC-6 and EV-1 are window counts from the composer's Readings (`cold.py:252-266`, `ev.py:100`). Design A3 Cold 28 Oct: CC-1 must not read "Met" when the chamber was not read. | A KPI `Reading.complete` is **AND-ed** with "every expected day of its `kpi` record's measure in the window is COMPLETE". The value is unchanged. `judge` (`objectives.py:112`) is unchanged, so an AT_MOST miss is still proven on incomplete days and a MET needs complete days. CC-1 on 28 Oct then reads NOT_JUDGED (design A3 data check). |
| R7 | I-19 precedence. `PRECEDENCE` (`B/outcomes/status.py:34`) ranks NO_OBJECTIVE above ON_TRACK. | Swap them: `(NEEDS_ATTENTION, WATCH, UNKNOWN, OPPORTUNITY, ON_TRACK, NO_OBJECTIVE, NOT_MEASURED, NOT_APPLICABLE)`. `STATUS_POLICY = "outcome-status/4"`. The row gains `target_note` = "{k} of {m} outcomes have a target" when the winning state is ON_TRACK and any outcome of the row is NO_OBJECTIVE (vocabulary, §A4). The Portfolio dot word `DOT_NO_OBJECTIVE` (`F/estate/PortfolioOutcomes.tsx:247-250`) stays for an all-NO_OBJECTIVE row. |
| R8 | PC-1 money and verdict claims. CH-5a2 builds the `Claim` type and the count claims (plan §2.5.3), but its sheet gives no type. | The type is fixed **here** for both slices (§A3). CH-5a2 builds it as written; CH-6a adds `money_claim` and `verdict_claim`. If CH-5a2 has merged with a different shape, P3 reports it and CH-6a adapts to the merged type without changing a count claim. The browser renders `text` only. Money text is server-rendered by one function that must equal `boardMoneyText` (`F/sites/OutcomeBoard.tsx:73`) on a shared fixture. |
| R9 **(away)** | I-22: "EV-2 never judged; MG-5 read from one noon hour". EV-2 is NOT_MEASURED by the catalogue (no odometer, `catalogue.py:53-54`). MG-5 has no day-snapshot measure; a full-day unserved-critical measure is a new adapter (CH-8 catalogue work). | **CH-6 resolves I-22 in part.** The MG-5 verdict claim names its basis in words ("checked over 12:00–13:00"), so no wider claim is made. EV-2 keeps its ruled not-measured sentence. A full-day MG-5 measure is a **labelled keep → CH-8**. D-AW-6. |
| R10 **(away)** | MA-1 ruling: "CH-6 decides whether same-currency Grow figures may be added." | **Never added, even in one currency.** Design A6 and rev 6 §2.1 forbid sums across Sites; the Sites' checked days differ (Kobo 24 h days, EV Tuesdays). The Portfolio Grow card names each Site's figure; `money_total` stays null. The note reads the mock's "Different days at each site, so not added together" when the Sites' checked-day sets differ, else "Shown per site, never added together" (vocabulary). D-AW-5. |
| R11 | Mock M3 Kobo "Estimated income" ("$7.50 over the 3 checked study days (3 × $2.50)") prices headroom, not measured use. The plan §2.5.1 and the MA-1 brief M3 give "the week … at 0.25 USD per kWh" (measured × declared). | **Estimated income = measured productive kWh × declared price** (A4, `priced_energy@1` over `productive_kwh`). The headroom money is the **Potential** part's second line, only when the study is SUPPORTED ("{lo}–{hi} {cur} per hour of use", design §5b.4). The mock's own illustrative figures stay; the difference is **MD-CH6-1**. |
| R12 | EV Potential. The mock gives "Chargers used under a fifth of capacity", the title of the `CHARGERS_MOSTLY_IDLE` warning (moves EV-3, `outcome_map.py:34`). | A `potential` record `WARNING:CHARGERS_MOSTLY_IDLE → EV-3`, `direction_only@1`, no money. The part shows the warning's own title when the warning is present, else "No potential found yet". No new detector. |
| R13 | CH4-R R7 keep: the board's opportunity signal comes from the renewable cards (`mini.py:428`), not the thread. | **Fixed in CH-6a.** The Kobo `potential` node reads the headroom opportunity **thread** (CH-4 items: state, `headroom_kw`, `window_hours`, evidence status) through ChainReader. The `SIGNAL:PRODUCTIVE_USE_HEADROOM` status signal is open exactly when that thread is OPEN or RECURRED at `k`. The renewable cards stay a contributor line only. |
| R14 | Portfolio window (I-04). Cold and EV rows use the latest selected event window (`B/site_outcomes/read.py:168` `latest_window`, `:449` `_event_window`); mini uses the UTC day of `to`. | **One graded window for every Site** (A6). Each Site's nodes are evaluated over the Site-local days of `[from, to)`. Row **state** keeps CH3-R's rule: the board composition on the Site-local day of `to − 1 µs` for mini, and over the whole window for cold and EV (their composers take any `lo/hi`, `cold.compose`/`ev.compose`, `read.py:390-391`). `latest_window` and `_event_window` are deleted from the summary and EstateChain paths. |
| R15 | Recurrence while CHANGE_APPLIED (D-AW-3) is pending MD-0's measurement. | Not in CH-6 unless D-AW-3 assigns it. CH-6 reads thread states as stored. |

## Revision OWN-1104 (Architect 5, 2026-11-04; owner agreed "all as recommended")

**R10 replaced (D-AW-5 reversed): the Grow card adds estimated income across Sites, honestly worded.**
- `money_total` is a Claim (`money.estate_income`), built by one function in `B/chain/vocabulary.py`:
  - over the Sites whose `estimated_income` / `estimated_charging_income` claim has a value;
  - **only when every such claim has the same currency**; otherwise value null and text `money.currency_mixed`.
- **Text:**
  - every contributing Site COMPLETE: "Estimated income from checked days: {total}";
  - any contributing Site CHECKED_DAYS: "At least {total} estimated income, from checked days";
  - in both cases followed by `· not billed or collected` (MA-1 M3).
- **Under it, one line per Site:** "{Site}: {amount} over {k} of {m} days checked". A Site whose claim is NOT_KNOWN is named and excluded: "{Site}: not known yet".
- **Days rule.** An EV non-operating day is NOT_EXPECTED, so it is not counted in `m` and never makes the total partial.
- **No scaling.** Values are never scaled or extrapolated. Days are not aligned between Sites; each Site's own checked days are named.
- The D-AW-5 note "Different days at each site, so not added together" is deleted.
- COH-17 checks that the total equals the sum of the Site claims shown, in the one currency.
- Design A6 is amended for Grow income only (owner, OWN-1104). Optimize money is unchanged: per Site, CH-5c.
- **Size:** CH-6b +0.25 (5.25).

**R16 new (D-AW-3, OWN-1104): a recurrence while a change is under check is recorded.**
- `B/chain/lifecycle.py` `TRANSITIONS` (`:45-56`) gains `(CHANGE_APPLIED, OCCURRENCE) → CHANGE_APPLIED`, recorded as a thread event with `cause_kind = RECURRED_DURING_CHECK`. The cause is no longer skipped (`:280`, `lifecycle_run.py:117-143`).
- **Thread line:** `thread_lines` (CH-5a2 B4) gains kind `RECURRED_DURING_CHECK`, with text "Happened again on {day}, after the change on {day} · still being checked". This is a vocabulary template and a MOCK DEVIATION candidate.
- **Counting.** The occurrence counts against the change: the verification evaluators receive the thread's during-check occurrences as an input. `reserve-trial-1` already sees the event in its later window. For CH-9b see its R6. No rule threshold changes.
- **L2m (MD-0 Kobo):** the recurrence day after ACT-K1's apply (MD0-S2) produces exactly one RECURRED_DURING_CHECK event and the line.
- **Placement and size.** Placed in **CH-6b** (+0.5), not CH-6a: CH-6a is already at 6 units, and the owner's rule splits slices over 6. **CH-6b = 5.75.**

**R16 addendum (MD-0 phase 3, 2026-11-04).** On MD-0 `states`, the D14 recurrence joined the thread (steps b/c) but produced **no lifecycle cause at all**: `run_lifecycle` returned `written 2, skipped 0, skipped_causes []`. That is a silent drop, not a skip.
- **R16 must therefore cover the cause-generation path.** `lifecycle_run` derives an OCCURRENCE cause for every occurrence joined to a thread in CHANGE_APPLIED (or later) state whose episode starts on or after the change's effective day, and the new transition records it.
- **L2m assertion:** exactly one `RECURRED_DURING_CHECK` event and one line for the D14 recurrence. An L0 test asserts that `written` counts it, not merely that `skipped` is 0.

**R16 revision MD0b-R (2026-11-04).** MD-0b verifies ACT-K1 on D12, so the D14 recurrence is now a real RECURRED from RESOLVED_MONITORING. MD-0 no longer exercises an occurrence during CHANGE_APPLIED. The D14 assertions above are replaced:
- **L0:** a thread in CHANGE_APPLIED plus an OCCURRENCE cause whose episode starts on or after the change's effective day, before any outcome. This gives exactly one RECURRED_DURING_CHECK event, `written` counts it, and the state stays CHANGE_APPLIED.
- **L2 synthetic** (`pg_harness.fresh_database()`): the same case through `run_lifecycle` and the thread store, plus the thread line.
- **L2m (MD-0):** D14 still reads RECURRED from RESOLVED_MONITORING, with no RECURRED_DURING_CHECK event (the negative case).
- No MD-0 fixture change.

## CH6a1-R: rulings on the CH-6a1 pre-flight (Architect 17, Claude, 2026-11-05)

Pre-flight: `AssetOpsV1-ch6a1\.agent\CH-6a1-preflight.md` at `4cb9dbd94`. **CH-6a1 stays 1.25 and CH-6a3 stays 1.5. No unit change.**

- **Q1 overridden: data only here; the wiring goes in CH-6a3 at +0.**
  - It is defensibility-critical. Without it, EV Grow's "Why?" for "$36.00" cannot show the 120 kWh behind it.
  - CH-6a3 already changes the stored "Why?" bodies: SCOPE-1 added the "{kWh} kWh × {price}" line there. Wiring `used_measures` (the thread measures UNION the category's `MEASURE:` measures, in Site-type order) in the same composer pass therefore costs one body change and one clone run, not two.
  - It closes CH5b2-R's Q5 Known Deviation in CH-6a3, and the CH-6a3 packet says so.
- **Q2 accepted.** L0 allows either a `MEASURES` key or `CHAMBER_RANGE_MEASURE`, and the record keeps `excursions`.
- **Q3 accepted.** `headroom_kw` keeps the sheet text that R13 reads from the thread items, and the L0 rule is as proposed.
- **Q4 accepted.** The key and the R12 record stay, and the graph owner becomes BL-06 (SCOPE-1).
- **Q5 accepted.** A frozen dataclass of facts already read. CH-6a2 may add fields, additively only. `Effect.money=None` carries a `reason`.

## CH6a2-R: rulings on the CH-6a2 pre-flight (Architect 18, Claude, 2026-11-05)

Pre-flight: `AssetOpsV1-ch6a2\.agent\CH-6a2-preflight.md` at `42a2cbaaf`. **CH-6a2 stays 2. No unit change, no new work, nothing backlogged.**

- **Q1 accepted.** The value line and the money line are joined by `"\n"` in `text`, and the money fields sit in `value` as strings. The money line is present only when the study is SUPPORTED (R11), so a LIMITED or UNKNOWN potential is one line. CH-6a3's `OutcomeRow` splits on `"\n"`, and no literal `"\n"` may reach the screen.
- **Q2 overridden for the potential; MG-5 and MG-2 accepted with one condition.**
  - MG-5 and the MG-2 `avoided_cost` earnings take `days` from `_counts` of `critical_served` and `avoidable_gen_min` only if that measure's rows are the rows the reading or the stored consequence was computed from. The packet must cite the line that shows this. If they are not, `days=None` and the basis is NOT_KNOWN. A basis must describe the days behind the figure, not a nearby measure.
  - "COMPLETE when shown" is rejected because it is untrue. The mock's own Kobo potential reads "3 of 5 study days checked · 1 partly checked · 1 with too little data" (`v70/index.html:418`), and a study like that is not COMPLETE.
  - A potential takes `days` = `_counts` over the study's own days when the CH-4 item carries them. The basis is then `count_basis(days)`, the one basis rule (§S.2). If the item carries no study days, `days=None` and the basis is NOT_KNOWN, while the text is still shown. The missing days line then becomes MD-CH6-4 (present less, not built).
  - The EV potential has `days=None`, which is moot while R12's warning has no producer (BL-06).
- **Q3 accepted.** The change to `mini.py` is import-only, with no logic line, and its `COPY` and tests stay unchanged.
- **Q4 overridden.** The study shows for OPEN, RECURRED, REOPENED and CHANGE_APPLIED (a change that is applied but not verified leaves the study as the latest evidence). For RESOLVED_MONITORING, CLOSED, WITHDRAWN or no thread, the part reads `potential.none`.
  - Reason: "18–20 kW of daytime solar unused" is untrue for a thread whose change has been verified (`lifecycle.py:30` `VERIFIED_STATES`).
  - The R13 status signal stays OPEN or RECURRED, as written.
- **Q5 accepted.** `MG1_ACTUAL` ("sales not recorded") and NOT_JUDGED are the board's existing rule for no checked day (`mini.py:623`), so no new claim is made.
- **Q6 overridden on the basis; the copy is accepted.**
  - With no objective, nothing is judged, so the `kpi` claim has `value=None`, `days=None` and basis NOT_KNOWN. A basis taken from the days would label a non-judgement COMPLETE.
  - The text `target.none` "No target set yet" and the days line `target.days_none` "No target, so no days are judged yet" equal the mock (`v70/index.html:418-419`). There is no MOCK DEVIATION.
  - Both strings are vocabulary templates (guard V).

## CH6a3-R: rulings on the CH-6a3 pre-flight (Architect 18, Claude, 2026-11-05)

Pre-flight: `AssetOpsV1-ch6a3\.agent\CH-6a3-preflight.md` at `c41dc104b`. **CH-6a3 goes from 1.75 to 2.0** (+0.25 for the MG-2 price line, Q3, which is defensibility-critical). BL-13 stays in the backlog.

**The CH-6a2 Known Deviations: all eight are confirmed.**
- **D1.** The MG-5 suffix is not built. Since CH-9 R9 the reading covers the whole day, so "12:00–13:00" would be untrue.
- **D2, ACTION_IN_HAND.** Confirmed, which corrects CH6a2-R Q4: the list there left this state out by mistake. Before a change is applied, the study is the latest evidence, so "No potential found yet" would be untrue.
  - To prevent another omission, `POTENTIAL_STATES` is defined by exclusion: every thread state except RESOLVED_MONITORING, CLOSED and WITHDRAWN.
  - A test covers ACTION_IN_HAND and each excluded state.
  - The R13 signal stays OPEN or RECURRED.
- **D3 to D8** are confirmed as recommended.

**Questions**
- **Q1 accepted.**
- **Q2 accepted.** Each Grow part carries its own days line, as in mock M3, so every shown figure has its days. BL-13 (the row-level M1 line, which stays in "Why?") is not defensibility-critical and stays in the backlog.
- **Q3 overridden on two points; the kWh default is accepted.**
  - **Earnings:** "{kwh} kWh × {price} {cur}/kWh", as proposed (MOCK DEVIATION against "× assumed price $0.30 per kWh", as listed).
  - **Several prices:** the line is not omitted. A figure whose price "Why?" leaves out silently cannot be traced. "Why?" shows the vocabulary line `why.from.price_several` = "{kwh} kWh at {n} declared prices over these days" (copy only, +0). The packet still counts the case.
  - **MG-2 Cost is included,** since the owner said every money figure and an untraceable cost cannot be defended.
    - The line is `why.from.fuel_price` = "{lo}–{hi} L × {price} {cur}/L", built from the stored consequence's `low_litres` / `high_litres` (`analytics/dispatch.py:735-736`) and its declared fuel price.
    - It uses one value when low and high are equal, and the several-prices rule above applies.
    - If the body carries no price, the line is omitted, and the packet records that as a Known Deviation. No new price read is built. **+0.25.**
- **Q4 accepted, with one condition.** Showing money on a LOW or NO_DATA day would price unchecked data, which breaks A4. So the change is the defensible one, and it is listed in L3.
  - The Estimated income part must read `money.not_known` with its days line, never an empty part or a missing figure.
- **Q5 accepted, with the same predicate.** Wherever the Grow headroom words ("18–20 kW…") are still shown outside the Potential part, they follow `POTENTIAL_STATES`. They must not stay on from a study whose change has been verified. This costs +0 because the predicate already exists.
- **Q6 accepted.** The golden diff is limited to the named keys plus the R5/R6/R7/R13 value changes.

## CH6a3-R2: fix shape for the CH-6a2/6a3 review (Architect 21, Claude, 2026-11-06)

Review: `.agent/review-CH-6a2-6a3.md` (REVISE) at `f1beed6d9`. Binding checked: Claude. **CH-6a3 goes from 2.0 to 4.25** (below the cap of 6), and the fix runs as two sequential rounds, R2a and R2b, with one re-review after R2b. Every item below gives its SCOPE-1 reason. No owner question.

**The governing rule (H3, ONE-SOURCE).** Each Grow figure on a board has one source: the stored day snapshot, as read by the evaluator's claim.
- The Grow row's money, the productive-use or charging **subline**, and the sales or charging **contributor** that state kWh or price come from the earnings claim, and only from it. Their kWh is `energy_basis.kwh`, and their price is the price on the basis line.
- When the earnings claim is NOT_KNOWN, all of them say "Not known yet", each with the claim's days line. The subline is None. The composer's own live read (`_measured_sales`, the EV session text) can no longer put a kWh, a "complete meter record" or a price beside that "Not known yet".
- The live read stays only where it was before CH-6 for non-money facts that the snapshot does not cover, such as conflicting readings and users with no readings.
- SCOPE-1 reason: as it stands, one row states two contradictory things, so one of them is untrue.

**H1: the test is stale in its fixture, and its money expectations are still the ruled behaviour.** It is not a regression in which money a client should see.
- The fakes give no snapshot rows, so the earnings claim is NOT_KNOWN. MG-1 has moved from `facts.readings` to `facts.nodes["MG-1"]["kpi"]` (R5).
- Fix: give the fakes snapshot rows. A COMPLETE or PARTIAL day must still yield 25.25 and 42.08 USD with the subline from the claim.
- Add one LOW-day case: the money is None, the subline is None, and the contributor reads "Not known yet" with its days line (ONE-SOURCE).
- Repoint the 4 MG-1 asserts to the kpi claim, recomputed through `judge_month`. Do not delete any test.

**H2: what proves the figures now, and what moves.**
- *Why everything is NOT_KNOWN on real data: not proven, so neither "missing data" nor "defect" is accepted yet.* R5 makes 8-of-24 h story days PARTIAL, and a PARTIAL day is counted. So the full days of DD-1 do not explain an all-NOT_KNOWN board. The packet's "no productive-sales snapshots on the clone" has no evidence behind it.
- *R2a must settle it (this closes M1):* give the clone's `chain_day_snapshot` row counts and grades per measure (`productive_kwh`, the EV charging measure) for the Kobo month and the 6 EV boards, and the settle/collect log.
  - If the rows exist but are not read, that is a defect, fixed in R2a.
  - If they were never produced, record the producer cause in L3. It is fixed in R2a if it takes 0.25 or less; otherwise STOP and report to the Architect.
- *CH-6a3 must prove now:* every §A8 item 3 bullet on `mechanism_db()`, asserted by recomputation. The MD-0 data has COMPLETE `productive_kwh` days, so a NOT_KNOWN there is a defect, not missing data. Then:
  - each money figure equals the Σ of the stored rows;
  - each "Why?" price line reproduces the figure as kWh × price;
  - the SUPPORTED potential carries its money line;
  - add the ONE-SOURCE assert on one Kobo day and one EV day.
- *Moves to DD-1b2 F-THREADS:* on the combined demo dataset, the Kobo and EV boards show a non-null earnings figure, a SUPPORTED potential, an MG-1 verdict and the price "Why?" line on the story days the sheet names. That is real-data end-to-end proof, which needs the full days. The DD-1 sheet takes this as one added F-THREADS assertion (+0).

**H4: the required layout (mock v70 `:213-215`, `:416-420`; MOCK DEVIATION labels cite v70, not v69).**
- The wire carries a days line per part: each Grow claim JSON carries `days_line`, from the one `days_line` function over that claim's own `days`.
  - The row-level `days_line` field added in this slice is removed. A line attributed to another figure is untrue.
  - The day argument is passed only when the window is one Site-local day (this closes M4).
- The three parts always render, in the order Target, Potential, Estimated income. The server fills the missing ones:
  - no kpi record: `target.none` plus `target.days_none`, which equal the mock;
  - no potential: `potential.none` with no days line;
  - no earnings record: `money.not_known` with no days line.
  - So EV shows "Target: No target set yet".
- Markup and CSS match the mock: `div.ob-grow` is a grid of `repeat(3,minmax(0,1fr))` with an 8px gap, and drops to one column at 760px. Each part is `div.ob-part` (bordered, 6px radius), containing `span.ob-plabel` + `b` (one per `"\n"` line) + `small.ob-days`.
- A part whose claim has `days=None` shows no days line. It never shows a neighbour's line.
- Register in `mock-departure-register.md`, with an inline MOCK DEVIATION label in `OutcomeBoard.tsx`:
  - MD-CH6-1 (R11 basis);
  - MD-CH6-2 (the §A4 lines vs the mock examples, listed old → new);
  - MD-CH6-3 (`target_note` in the subline);
  - **MD-CH6-7**: the Potential days line is missing when the study carries no day grades. CH6a2-R called it MD-CH6-4, but that id is already §B4's (CH-6b Protect), so it is renumbered here.
- Layout evidence at 1440 and 390 for Kobo and EV Grow is owed in R2b.
- The vitest uses server vocabulary (this closes L2).
- SCOPE-1 reason: R2 Q2 and Q4 ("each shown figure has its days") are unmet, and a wrongly attributed days line is untrue.

**Medium findings**
- **M1:** fix now (in H2 above). It is the evidence behind a shown "sales not recorded".
- **M2:** fix now. Add the R7 "Cold lab 24 Oct" L0 case (sheet-required, and it sets the shown row state), a `row_nodes` selection test, an `_lead_findings` other-mechanism negative test, and an EV priced/unpriced `not_measured_text` test.
- **M3:** fix now. Add one composer-level MG-1 test on snapshot rows: MET → ON_TRACK with a "Met" chip, BEHIND_PACE → WATCH, no objective → OPPORTUNITY with the potential chip. The packet lists the seventh removed test.
- **M4:** fix now, folded into H4's per-part `days_line` (+0). A wrong date is untrue.
- **M5:** fix now.
  - Print `price` only when its revision id equals the counted rows' single revision. Otherwise use `price_several`, or print no line when the rows carry no revision.
  - Assert kWh × price ≈ amount on the mechanism data.
  - Round the litres as `dispatch.py:735-736` does.
  - Reason: a price line that does not reproduce its figure cannot be traced.

**Low findings**
- **L1:** merge main before the re-review.
- **L2:** closed under H4.
- **L4:** fix now (+0).
- **L3 → backlog BL-15:** the `target_note` denominator excludes outcomes that can never have a target. "2 of 3 outcomes have a target" is true as ruled in R7, so this is not defensibility-critical (0.25).

**Rounds and size (+2.25)**
- **R2a, backend truth: 1.5.**
  - H1: 0.25.
  - H2: the §A8 item 3 L2m bullets, 0.5 (already owed acceptance), and the M1 clone evidence, 0.25.
  - H3 ONE-SOURCE in `mini.py` and `ev.py`: 0.25.
  - M2 + M3: 0.25.
  - M5: in the H2 bullets.
- **R2b, wire and layout: 0.75.**
  - Per-part `days_line`, server-filled parts, and the grid/markup with M4 and L2/L4: 0.5.
  - Register and labels, and the layout evidence at 1440 and 390: 0.25.
- R2b follows R2a. Each round fits one Sonnet builder. **One fresh Claude re-review covers both rounds**, after L1, and R2a's gate is the scoped list plus `test_walk1_productive_sales.py`.
- The plan row records CH-6a3 at 2.0 → 4.25 and the CH-6a total at +2.25, with the SCOPE-1 reasons above.

## CH6b1-R: rulings on the CH-6b1 pre-flight (Architect 24, Claude, 2026-11-06)

Pre-flight: `AssetOpsV1-ch6b1\.agent\CH-6b1-preflight.md` at `0de1dfeec`. Binding checked: Claude (branch ROLE_CONFIG, owner 2026-10-27). **CH-6b1 stays at 1.75.** The bar is that every Portfolio number is true, traceable through "Why?", and equal to the sum of the Sites it claims to sum. No owner question.
- **Q1 accepted.** Portfolio nodes use `window_days(lo, hi, tz)`, the frame `days` and `claim_days` already use. This is R14's "Site-local days of `[from, to)`" read with the UTC-midnight-names-dates rule. Otherwise Addis would show 8 days beside a "7 days" claim, which is untrue. L0 asserts that, for each Site in both time zones, every node's `days` and the Site's `days` cover the same day set.
- **Q2 accepted, with one condition.** PERIOD over the requested window is the honest basis: a Portfolio card that names a window must judge that window. LATEST_EVENT showed an event from outside it.
  - Condition: a cold/EV Site with no event in the window shows its composer's none or not-known state with its days line. It never reaches back to an older event.
  - COH-7a becomes the per-domain rule (mini DAY on `window_day`, every other Site PERIOD on the requested window). Its "more than one basis" finding is deleted, since two bases are now correct by design. `test_out_w2_summary_window.py` is rewritten to this rule and is not deleted.
- **Q3 accepted.** One `read_latest` for all Sites, with seeded memo keys exactly as listed. L0 asserts that the seeded reads equal the per-Site reads. A fallback is counted in the packet and never silent. The plan and timing go in the packet; over 50 ms is reported.
- **Q4 accepted.** One function builds `sites[]` (`rows`, `nodes`, `earnings`) and `money_total`, and both EstateChain and the summary call it. Summary = EstateChain holds by construction and L2m asserts it. Server-filled parts are not earnings. A NOT_KNOWN earnings claim from a real record is an earnings entry, so Q5 can name it.
- **Q5 accepted, with two overrides (+0).**
  - (a) **"At least" form.** The "At least {total}…" form is also used when any Site with an income record is NOT_KNOWN, not only when a contributor is CHECKED_DAYS. A total that leaves out a named Site is a lower bound for the estate.
  - (b) **Rounding.** Each Site's value is rounded to the currency's minor unit with the same formatter the line uses, and the total is the sum of those rounded values. The shown lines then add up to the shown total exactly (COH-17 in CH-6b3).
  - **Accepted as proposed:** one currency only, else null value and `money.currency_mixed`, still with the per-Site lines; " · {p} partly checked", since the money includes PARTIAL days; a Site with no income record is not named; `days` = `sum_days` of the contributors; EV non-operating days are not in `m`. The copy follows mock v70 `pfGrowParts` ("· not billed or collected"). The D-AW-5 note is deleted, as OWN-1104 already says, and recorded as MD-CH6-5 in CH-6b3.
- **Q6 accepted.** Cold 7/7 and EV D9 (days and earnings) are asserted at L0 on the fixture ChainRequest and recorded as a Known Deviation for L2m, because `mechanism_db()` holds Kobo only. Real-data cross-Site agreement is covered by the L3 clone (0 new) and by COH-17 in CH-6b3.
- **Q7 accepted:** L1 → CH-6b3, L4 → CH-6b2, L5 → CH-6b3.
- **Q8 accepted:** one template rebuild, at the final L2m run.
- **Lane-2 overlap: CH-6b1 owns the edit** to `tools/demo_combined_finish.py` CO-6/CO-6b (`:416`, `:458-460`, LATEST_EVENT → PERIOD, those lines only).
  - The wire change and its assertion must land in one merge. Otherwise main carries a failing demo check.
  - DD-1a1 does not edit those lines. Whichever slice merges second merges main and resolves the conflict, keeping PERIOD.
  - No `host/*` or scenario file is touched.

## CH6b1-R2: Known Deviations in the CH-6b1 handoff (Architect 24, Claude, 2026-11-06)

Handoff: `AssetOpsV1-ch6b1\.agent\CH-6b1-handoff.md` at `771170f2a`. **CH-6b1 goes from 1.75 to 2.0.** No owner question.

**KD-2 (MG-5) is not defensible as shown, and a label fix is required.** On a weekly row, "1 of 1" with no date reads as a judgement on the week, which is untrue. The judgement itself is true for the day it covers. It also matches the mini row state, which CH3-R and R14 already set on the last local day.
- **Rule:** keep the MG-5 judgement on the last window day. Its node claim's `days_line` is built by the one `days_line` function with the day argument, because the node's own window is that single Site-local day (CH6a3-R2 H4 / M4). The line therefore names the day, for example "13 Oct · 1 of 1 day checked".
- This applies to every reading-based verdict that has no kpi record (`chain/outcomes.py:136-140`), not to MG-5 alone.
- L0 checks that the line names the last local day in both time zones and never shows a bare "1 of 1" on a window longer than one day.
- **Size:** +0.25.
- Judging MG-5 over every day of the window (a per-day evaluator over stored rows) is not defensibility-critical once the line is labelled. It goes to the backlog as **BL-17** (SCOPE-1; BL-16 is already the idle-fuel item).

**KD-3 is confirmed as a Known Deviation.**
- The `states` template holds no D8–D9 rows, so Kobo reads 4 of 7 on D7–D13 (D7, D8 and D9 are NO_DATA).
- L2m asserts the counts recomputed from the stored rows, not §B5's literal 6 of 7. The money is the sum of the stored money of the counted days.
- The packet records the template gap and states that the template is not rebuilt to reach 6 of 7.

**KD-1 is confirmed** (CH6b1-R Q6): Cold and EV are checked at L0 only. Real-data cross-Site agreement is covered by the L3 clone and by COH-17 in CH-6b3.

## CH6b1-R3: KD-4, cold and EV event evidence inside a PERIOD window (Architect 24, Claude, 2026-11-06)

Packet: `AssetOpsV1-ch6b1\.agent\review-packet-CH-6b1.md` at `e98db433d`. **KD-4 is not accepted as an honest result. CH-6b1 goes from 2.0 to 2.75.** No owner question.
- **Why it is not honest.** A day or week that contains an assessed failure now reads UNKNOWN on the Portfolio and on the Site board, with no repeat warning. The `overview_href` is now the plain Site link, so the Portfolio no longer leads to the failure either. Only a deep Finding or evidence link still reaches the failure.
  - "Not known" said about a window whose evidence is known and assessed is untrue by omission, and the Cold failure-cost story drops out of the demo's main path.
  - CH6b1-R Q2's condition covered a window with **no** event in it (no reach-back). It never allowed a contained event to vanish.
- **Rule.** PERIOD stays: the basis is PERIOD and the window is the requested window. But cold/EV evidence-bound reads cover every selected evidence window that lies inside `[lo, hi)`, using the existing `site_selected_windows(_many)` (`estate/evidence_money.py:506,554`).
  - Overview, findings and their cost or consequence are read per contained window.
  - The row shows the latest contained event's facts. Its days line names that event's window, for example "26 Oct 16:00–17:05".
  - The repeat warning counts the contained events.
  - No window outside `[lo, hi)` is ever read (the Q2 no-reach-back rule).
  - No contained window: the composers' none or not-known state, unchanged.
  - The summary, EstateChain and the Site board all go through this one path, so summary = EstateChain = board still holds.
- **Tests.** `test_out_c3_repeat_visits_postgres.py` returns to NEEDS_ATTENTION with the REPEATED warning on day and week, with PERIOD basis and the requested window. Add an L0 case where an event lies outside the window and is not read. The EV equivalent goes in L0 if EV reads are window-bound.
- **Packet.**
  - The L3 clone records the Cold and EV Portfolio and board values old → new on the story days, with 0 new.
  - The packet also states which client surface reached the failure before this fix: the Findings or evidence page.
- **Size:** +0.75 (cold and EV composer read over contained windows 0.5; tests and clone evidence 0.25).

## CH6b1-R4: the CH-6b1 review fix (Architect 24, Claude, 2026-11-06)

Review: `.agent/review-CH-6b1.md` (REVISE). **One fix round applies R3 and R4 together.** No owner question.

**The governing rule for H1, H2 and M1 (SPAN):** every node claim carries the span it actually judged, as `span: {first, last}`, Site-local and additive on the wire, set by the evaluator branch that produced it.
- The one `days_line` function counts `days` over that span.
- It names the span only when the span differs from the Portfolio window's `window_days`. A one-day span reads "27 Oct · …"; a longer span reads "1–31 Oct · …".
- A span equal to the window is not named.
- A figure's days line therefore always covers the reading it sits beside (the one-source rule of CH6a3-R2, applied to the window). This replaces R2's "name the last day" trigger.

**H1: carry the judged day; do not gate on the record.**
- A record-based kpi's span is the window, so EV-1 over a week reads "0 of 1 day checked · …" with no date. Its one expected day is the Tuesday, and that is in `days`.
- The no-record branch (`chain/outcomes.py:136-140`) sets span = its judged day, so it is named as R2 requires.
- L0 adds a record-based EV kpi over a week with one TUE expected day. The last window day must not be named.

**H2: (a), label with its day.** The mini MG-2 reading is the composer's board day (R14 / CH3-R), so its span is that day, and its `days` are counted over that day, not the week. Recomputing over the window is not defensibility-critical once the line is labelled, and goes to the backlog as BL-17 together with KD-2's window-wide judging. L0 gives Kobo an MG-2 objective.

**M1: a defect; name the span.** MG-1 month-to-date sets span = [1st of the month, the window's last local day]. Week and month cards then read, for example, "1–31 Oct · 0 of 31 days checked · 7 partly checked". L0 gives Kobo an MG-1 objective. The Q1 check becomes: an unnamed node's day set equals the Site's window days, and a named node's `days` equal its span's day set. The check is non-vacuous for CC-1, earnings, MG-1, MG-2 and EV-1.

**KD-4: R3 stands and closes it.** The reviewer's backlog recommendation is overridden.
- The round's first step is the clone check R3 requires: the Cold and EV week and day rows on the story days.
- If those rows already show the contained event and its repeat warning, with no UNKNOWN, the demo story is intact. In that case:
  - R3's composer change for sub-day windows goes to the backlog as BL-18;
  - KD-4 is recorded as a Known Deviation, with that evidence;
  - the size drops by 0.5.
- Otherwise R3 applies as ruled.
- L4 is folded into R3's tests: assert that the Cold board over the same day and week has the same OPTIMIZE_COST state as the summary.

**Lows confirmed.**
- L1: fix the docstrings at `:403` and `:451`.
- L2: `site_selected_windows_many` is R3's reader, so it is kept with a production caller. If R3 goes to the backlog, delete it and its spy and repoint `test_qw2_many_postgres.py`.
- L3: log every fallback path, or correct the docstring to "counted", and put the L3 W6 fallback count (expected 0) in the packet.
- The "1 day" / "1 of 1 days" wording preference goes to CH-6b2 copy.

**Size:** R4 +0.5 (SPAN on the claim and `days_line` 0.25; L0 objectives and the EV, MG-1 and MG-2 cases 0.25); the Lows +0. **CH-6b1: 2.75 → 3.25** (2.75 if R3 shrinks as above). The round is one Sonnet builder, followed by one fresh Claude re-review.

## CH6b1-R5: the event window and the clone COH-2 (Architect 24, Claude, 2026-11-06)

Packet at `9d84b9913`. No owner question.

**1. The builder was right to leave the event window out of the days line.** The days line is counted over the window, so naming the event there would break R4 SPAN. That part of R3 is withdrawn.
- **But the row is not yet defensible on "when".** The Cold lead reads "Chamber above {high}°C for {span} min" (`cold.py:263-275`), which carries no date. On a week card, a client cannot tell which night it was without opening a Finding.
- **Minimal honest fix (copy only, no wire change):**
  - When the requested window is longer than the contained event, the cold/EV lead text gains the event's Site-local date and time range: " · 26 Oct 16:00–17:05". It comes from the contained selected window that R3 already reads, through a vocabulary template (guard V).
  - The days line stays the window's. Facts named with their time, days named with their window: each stays true for what it covers.
  - L0 adds two cases: a week window, where the date is named, and a window equal to the event, where it is not.
- **Size:** +0.25.
- **Backlog:** counting claims over the event's own span (a wire change) becomes **BL-19**, not defensibility-critical once the lead names the event.

**2. The two COH-2 findings are pre-existing and expected.**
- They are `expected-today.json` entries COH-2 / month / COLD-LAB-001 and EV-LAB-001, register I-09, owner DD-1, and the old-code bundle shows the same two. They are not CH-6b1's to resolve.
- The "self-check 0 pass 2 fail" is because the subjects are Action UUIDs from the `polish_full` baseline, and this clone's work dir (`ch6b1work`) comes from an earlier polish copy, so the ids differ.
- Required in the packet:
  - one line matching the two findings to I-09 by rule, Site and window;
  - the old-bundle result.
- "0 new" is then met in substance. No baseline change in this slice, and the subjects are not re-keyed here.

**CH-6b1: 3.25 → 3.5.** The +0.25 goes into the current round, before the re-review.

## CH6b2-R: rulings on the CH-6b2 pre-flight (Architect 24, Claude, 2026-11-06)

Pre-flight: `AssetOpsV1-ch6b2\.agent\CH-6b2-preflight.md` at `bd24773f0`. **CH-6b2 stays at 2.25.** No owner question. Mock v70 is the layout spec.

- **Q1 accepted.** One function, `portfolio_cards`, is carried by both the summary and `/estate/chain`, so summary = EstateChain by construction, as in CH6b1-R Q4.
  - `card_notes` is one server line, rendered as its own line and never joined in the browser.
  - Optimize stays on its CH-5c money line.
- **Q2 accepted as the honest definition.** `site_thread_states` already restricts to threads with a Finding occurrence whose episode meets `[lo, hi)`. The count therefore means "a Protect event happened in this window and is not yet resolved", which is the mock's "sites disrupted" (v70 `:436`, `:491`).
  - Conditions:
    - (a) Early warnings never count. The mock says "counted separately"; the packet confirms that no warning-only thread enters.
    - (b) The card's "Why?" names each counted Site and its thread title, as in the mock's `from` list, so the number is traceable.
  - L3 lists old → new per window.
  - Dropping "None shown yet" is accepted, because the basis rule covers it.
- **Q3 accepted.** Optimize has no days line (ONE-SOURCE), MD-CH5b-4 is kept for Optimize, and CH-5c owns it.
- **Q4 accepted, with one override.**
  - The value's prefix and form follow `money_total`'s own form. "At least" therefore applies whenever the claim does, which includes an excluded NOT_KNOWN Site (CH6b1-R Q5a), not only on CHECKED_DAYS.
  - With mixed currencies there is no amount; the value is the claim's text.
  - With no total, the fallback potential value carries the small "possible", never "estimated".
- **Q5 accepted.** MD-CH6-6 is registered, with an inline label.
- **Q6 accepted, with one condition.** The chip's link moves onto the Potential part.
  - The row state "Opportunity" and the Potential part already say what the chip said, so nothing a client needs is lost, provided the chip's link moves with it.
  - Captures at 1440 and 390 px against v70.
- **Q7 accepted.** (a) "1 of 1 day checked" when `m == 1`. (b) The dated lead is kept. (c) `study.headroom_unit` comes from the server, and the browser constant is deleted.
- **Q8 accepted:** `NOT_KNOWN` is added to `EstateCountBasis`, with one vitest.

## CH6b2-R2: the CH-6b2 review fix (Architect 27, Claude, 2026-11-06)

Review: `.agent/review-CH-6b2.md` (REVISE) at `5ab2bbf1e`. Binding checked: Claude (plan2 ROLE_CONFIG, owner 2026-10-27). **CH-6b2: 2.25 → 3.0.** One Sonnet fix round, then one fresh Claude re-review. No owner question.

**H1: (a). A thread's lifecycle is read at the request cutoff `k`, for every domain.** (b) is rejected: it invents OPEN, so a thread that is really ACTION_IN_HAND, CHANGE_APPLIED or VERIFIED would be shown in the wrong state. It also leaves `verified_results` blind, and it treats the symptom, not the cause.
- **Why (a) is honest.** R7's evidence cutoff bounds *evidence*: readings, dispositions and the overview body. A Finding is always known after the evidence it assesses, so lifecycle events read at that cutoff can never become visible unless a later disposition exists. The lifecycle is a fact known at `cause_known_at`, and `k` is the as-known bound for it. Evidence reads keep R7 unchanged.
- **Rule.** Add `lifecycle_cutoff(k)` beside `site_cutoff` in `chain/read.py` (it returns `k` for every domain). Thread and Action reads use it, at both callers:
  - `chain/claims.py` `counted_threads`: `count.sites_disrupted`, `open_threads` and `verified_results`.
  - `chain_api.py` `site_parts`: the `threads_of` and `actions_of` calls, which today use the board's `window.known_at`.
  - Portfolio card = Site chain = Site row then holds by construction. Fixing only `claims.py` would leave the Site chain showing `state: None` beside a NEEDS_ATTENTION row.
  - `board_cutoff` and every evidence read are unchanged.
- **The test the fix must pass.** A card never contradicts a row on the same page, and an open Protect problem is never hidden.
- **L0 tests:**
  - (1) A cold thread whose OPEN `cause_known_at` is later than the evidence cutoff and no later than `k` is disrupting. It counts in `sites_disrupted` and `open_threads`, and the card's "Why?" names it.
  - (2) The same thread with `cause_known_at` later than `k` is not visible. This is the as-known bound.
  - (3) An EV thread at ACTION_IN_HAND under the same condition.
  - (4) A CHANGE_APPLIED or VERIFIED event later than the evidence cutoff reaches `verified_results` only when VERIFIED.
  - (5) The Site chain's thread `state` equals the claims' state for the same Site and window.
- **L3 clone re-check:**
  - Week and month Protect read "2 found on the days checked", and "Why?" names GreenHarvest (both threads) and Depot.
  - Cold and EV `open_threads` and `in_hand` are recorded old → new.
  - `verified_results` and the Assure card are recorded old → new. The reviewer expects week "None confirmed" and month "1 confirmed" to be unchanged, so confirm it.
  - `chain_site` day files show non-None states.
  - COH: 0 new.
  - The packet's "no graded day is complete" explanation is replaced by this cause.
- **DD-1a1 trap.** Once full days land, the COMPLETE form must read "2 sites disrupted", not "No sites disrupted". The packet states this as the expected post-merge value.
- **Size:** +0.5 (the cutoff rule at two callers 0.25; L0 and the clone 0.25).

**M1: confirmed. The server tests must restore the full case coverage.** The old vitest expectations are the goldens. Add parametrised L0 cases in `test_ch6b2_portfolio_cards.py` for each of these:
- the evidence gap: unknown, all, some, many, one, zero;
- `zero_checked`;
- `checked_one`, `checked_many` and `withheld_many` for two Sites;
- `targets_none`, only when every Site was read as None;
- the `n == 0 and unread > 0` branch.
Each case asserts the exact server text. **Size:** +0.25.

**M2: deferred to end-game E5, as CH5b3-R Q7 ruled.** Captures belong with the one full recapture. The reviewer confirmed the DOM order against v70 `outcomes.js:158-162` and `pfGrowParts`.
- The packet records the 1440 and 390 captures as `not run`. Its blocking precondition is the E5 recapture, and its deferral is this ruling.
- Required now (+0): one vitest asserts the structure. The Grow parts are first in `ob-body`, there is no Grow chip, `dl.oc-pfgrow` holds Target, Potential, Estimated income and `dd.oc-pfnote` in that order, and `oc-pfdays` is present.
- A layout mismatch found at E5 is High (mock-is-layout-spec).

**Lows (+0):**
- **L1.** Add the MD-CH6-4 and MD-CH6-6 rows to `.agent/mock-departure-register.md` in this round, citing v70 and the inline labels. CH-6b3 adds only MD-CH6-5.
- **L2.** Correct the packet: early warnings are week 7, month 7 and S 5, taken from the bundle.
- **L3.** Remove the never-firing "possible" fallback from `_grow_card`. It is dead code: `short_values` is never filled.
  - This is honest without it. A SUPPORTED potential with no income still shows on the card's Potential part, and the value keeps "Not available yet".
  - Record it as a Known Deviation. The Q4 "possible" clause is withdrawn.
  - Removing the unfilled `CompositionResult.short_values` and `_short_values` plumbing goes to the backlog as **BL-22**. It is pre-existing and is also read by `_summary_row`.

