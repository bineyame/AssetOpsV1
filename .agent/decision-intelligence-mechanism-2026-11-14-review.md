# Review: decision-intelligence-mechanism-2026-11-14.html

Reviewer: fresh Claude Reviewer, 2026-11-14. Repository at main 9b4d9bd15c53daff70b2322012932720e1f96edb, the same revision the document cites. No code, test, database or document was changed.

## Verdict: REVISE (one Medium finding, a wording fix of about five sentences)

The document is accurate, complete against sections 1 to 4 of the request, and honest about its gaps. About 120 `path:line` citations were opened, covering every citation in §2 and in §3.11 Case A and Case B, plus samples from §1, §3 and §4 and all the migration references. Almost every one says what the document claims. The rest drift by a line or two and are still correct in substance.

The central claim holds: no decision path reads the CHECKED role. One safeguard condition is misread, and it is repeated in the summary, the stage table, two figures and Q5. That is the only blocking item.

## What I verified

- **Who reads the map.** I searched the backend independently for `outcome_roles`, `categories_for(`, `lens_flags(`, `records_for(`, `kpi_record(`, `CONTRIBUTIONS`, `thread_signal_key(`, `finding_signal_key(`, `\bCHECKED\b`, `ENTRIES`, `@LINKED`, `["role"]`, `.role ==`, `must_not_harm` and `["items"]`, and the frontend for `CHECKED` and `must_not_harm`.
  - None of these modules imports `outcome_map` or `outcomes.status`, or reads a category role: `dispatch_v3`, `finding_episode`, `finding_service`, `fuel_cost`, `fuel_cost_v2`, `money_eligibility`, `recompute`, `reserve_trial`, `verification_rules`, `verification`, `verification_families` and `credit`.
  - `verification_families` imports `outcomes.price_action`, which does not touch the map.
  - `actions/service.py:706` uses `categories_for` only for the wire.
  - All 10 `CONTRIBUTIONS` records are MOVES.
  - The "no decision path reads CHECKED" conclusion is confirmed. Three small omissions from the reader list are in L1.
- **Probe results.** I wrote my own probe in the scratchpad, reusing the `test_s3_dispatch_v3_analytic` fixture. Every probe result in the document reproduces:
  - PV 40 / load 30 gives 60 min CANDIDATE, even at SOC 35.
  - SOC inside the headroom with PV 31 gives 60 min INDETERMINATE.
  - The mixed run gives 30 Candidate and 30 Necessary minutes, with `BATTERY_NEAR_RESERVE` on a CANDIDATE interval, so the battery warning fires.
  - The probe is correctly labelled "probe" wherever the document uses it.
- **Test names.** Every cited test exists under its file and name. I read the Case A and Case B tests, and each asserts the behaviour claimed. I also checked the "not covered by tests" claims and found no covering test:
  - PV-alone CANDIDATE in v3.
  - The unserved-critical-energy FAIL branch. `test_unserved_critical_energy` checks only the measurement.
  - The interval-level mix.
  - B4.
- **Pure tests.** `pytest` over the 18 listed files plus `test_fuel_cost_v2.py` gave 554 passed in 4.55 s. PostgreSQL tests were not run, as policy allows.
- **HTML.** The page is self-contained, with no `<script>`, `<link>` or external URL. All 5 SVGs parse as XML and the HTML tags balance. Colours are CSS tokens with dark mode under both `prefers-color-scheme` and `[data-theme]`, and the SVGs use only `var(--…)` colours. The two required diagrams are present: the architecture diagram (Fig 1) and the sequence diagram (Fig 3). Their labels and references match the text and the code.

## Findings

### M1 (Medium, blocks): the trial SOC safeguard is stated as stricter than the code

**Where.**
- Short answer ("The trial rule needs battery charge more than 10 points above the reserve").
- §1.1 stage 7 ("whose lowest usable Candidate-segment SOC is above r + 10").
- Fig 2 ("lowest SOC must exceed r + 10").
- Fig 3 step 12 and Fig 4 ("lowest Candidate SOC > r + 10").
- §2.4 Q5 ("refused … unless the lowest Candidate SOC exceeds r + 10").

**Code.** `actions/reserve_trial.py:249-252` judges each Candidate segment on its own: `eligible = [v for v in verdicts if v["eligible"]]`. The rule refuses only when no segment is eligible. The basis is the latest eligible segment (`:254-256`), and segments that are not eligible are skipped without a refusal.

A test pins this: `test_s6_action_rule.py::TestUnavailableReasons::test_any_eligible_segment_is_enough_and_is_cited`. "The lowest usable reading decides" (`:219`) holds only within one segment.

**Why it matters.**
- This is one of the three hard-coded reliability safeguards that the Case B analysis relies on.
- A Finding whose other Candidate segments ran with the battery inside the headroom can still be offered the trial. Those segments are Candidate through rule 3 (PV alone), which does not check SOC.
- Accuracy of the safeguard conditions is the review's first priority.

**Fix.** Reword all five places to say "at least one cited Candidate segment whose lowest usable SOC is strictly above r + 10; segments that fail this are ignored, not refused". Cite `reserve_trial.py:249-256` and the test above. The Case A "Proposal" row can keep its current tests and add this one.

### L1 (Low): the §2.2 reader list says "every hit" but misses three readers

None of the three changes a decision, so the conclusion stands.

- `site_outcomes/mini.py:718-719` counts the warnings that MOVE MG-4 into the Protect headline ("N early warnings on battery and generator"). This is MOVES, text.
- `chain/why.py:82-85` `related_threads` selects the "Why?" threads for a category in **either** role. This is CHECKED and MOVES, text.
- `site_outcomes/board.py:379-380` uses `kpi_record` to choose the KPI node, which is in `CONTRIBUTIONS` and so MOVES only.

**Fix.** Add the three rows, or soften "every hit" to "every hit that can affect a role-dependent result".

### L2 (Low): the reserve-trial adapter is labelled as unverified, but it can be verified

The document flags the adapter's `RuleInputs` source as taken from the docstring only. That label appears once, in "Not verified (b)". It is not repeated beside §3.4, stage 7, Q5 or the Case A Proposal row, all of which rely on it.

The adapter does exist and matches the docstring. `actions/adapters/postgres_action_store.py:159-215` reads the `battery_soc` rows of each CANDIDATE segment's cited `evidence_ids`.

**Fix.** Cite the adapter and drop item (b). Otherwise, mark the dependent sentences "Doc says".

### L3 (Low): the test-run numbers cannot be reproduced

The document says "534 pure tests passed, in 19 files" but lists 18 files, with `test_fuel_cost_v2` cited elsewhere and missing from the list. I got 525 passed over the listed 18 files and 554 with `test_fuel_cost_v2.py` added. Neither matches 534.

**Fix.** List the exact files and the count.

### L4 (Low): small inaccuracies

- The Fig 1 caption says "Black arrows", but the arrows are drawn in `var(--muted)`, which is grey, and light grey in dark mode.
- §4.2 Work case lists its states as OPEN, IN_PROGRESS, COMPLETED, CLOSED and CANCELLED. `work/model.py:121` also has `VERIFICATION_WINDOW`.
- The 90-minute minimum-runtime probe is announced but its result is never reported. My run gave the whole 60-minute run as INDETERMINATE, with no Candidate. Report it in the B3 row or drop it from the probe list.
- The B1 row cites `test_candidate_over_a_closed_episode_reopens_it_under_the_same_id`. That test closes the episode with generic NECESSARY segments, not a reserve constraint. The chain is still sound when it is combined with `test_near_reserve_is_physical_necessary`. Say that the two tests together prove the B1 path.

## Not verified

- The PostgreSQL-backed tests cited by name were not run: `test_s6_verification_evaluator_postgres`, `test_s6_action_records_postgres` and `test_ch6b_estate_postgres`.
- The frontend role readers were checked only at the cited lines (`outcomeCategories.tsx:80-90, 150-158`, `OutcomeBoard.tsx:266-270`).
- No browser rendering. The HTML was inspected only as source.

## Re-review (revision 2)

Reviewer: fresh Claude Reviewer, 2026-11-14, main at 9b4d9bd15c53daff70b2322012932720e1f96edb. No code, test, database or document changed. Only pure tests were run.

### Verdict: ACCEPT WITH NOTES

M1 and L1-L4 are fixed in the body, not only in the change note. The new citations check out. Two Low notes remain, and neither blocks.

### Prior findings

- **M1, fixed.** I searched the whole file, including SVG text and titles, for "lowest", "every/all Candidate", "r + 10", "r+10" and "10 points". Every statement of the trial rule now says that one cited Candidate segment with lowest usable SOC strictly above r + 10 is enough, and that the other segments are ignored. These are the short answer (l.121), the §1.1 stage 7 row (l.308), Fig 2 (l.441), Fig 3 step 12 (l.562), §2.4 Q5 (l.497), §3.4 (l.619), Fig 4 (l.684, l.697) and the Case A Proposal row (l.720). This matches `reserve_trial.py:249-256`. The per-segment test (`low > threshold`) is at `:219-228`. No "lowest/every Candidate SOC" wording is left. The rows that still mention "SOC ≤ r + 10" (l.607, 610, 692, 694) describe the dispatch rules, not the trial rule, and they are correct.
- **L1, fixed.** The three readers are added at l.465-467, and the search note says revision 2 added them. I checked `mini.py:718-719`, `chain/why.py:82-85` and `board.py:379-380`, and each says what the row claims.
- **L2, fixed.** `postgres_action_store.py:159-215` is cited at l.308, l.497 and l.619, and it matches the code. It reads the `battery_soc` rows of each CANDIDATE segment's `evidence_ids`. The old "Not verified (b)" item is gone. The current (b), the headroom-study producer, is a different item.
- **L3, fixed.** l.133 lists 19 files, now with `test_tfc2` and `test_fuel_cost_v2`. My run of exactly those 19 files gave `554 passed, 1 warning in 4.53s`.
- **L4, fixed.**
  - Fig 1: the arrows are now called grey (l.152), and "Black" no longer appears.
  - VERIFICATION_WINDOW is added (l.812).
  - The 90-minute probe result is reported in the B3 row (l.732). It matches my first-round probe.
  - The B1 row says which two tests prove the path together (l.730).

### New citations checked

- `reserve_trial.py:29`, `:36` (the HEADROOM constant derived from `SOC_HEADROOM_POINTS`), `:219-229`, `:227-228`, `:234-289`, `:238-266`, `:240` (`lifecycle != "SUPPORTED"`) and `:249-256`.
- `test_s6_action_rule.py::TestUnavailableReasons::test_any_eligible_segment_is_enough_and_is_cited` (l.183).
- `work/model.py:107-121`.

All are accurate.

### Findings

- **N1 (Low).** The cited test's ineligible segment fails on SOC_MISSING (it has no readings, `segment(start=...)`), not on SOC_NOT_ABOVE_HEADROOM. The test proves that any ineligible segment is ignored. The claim at l.497 is narrower: a segment inside the headroom is ignored. That claim is true by the same code path (`:249-250`), but no test pins it.
  - Fix: optional. Add "same code path; the test uses a segment with no SOC" next to the citation.
- **N2 (Low).** l.497 says the proposal is refused "with `SOC_NOT_ABOVE_HEADROOM` only when no … segment" is eligible. When no segment is eligible, the code returns the *last* segment's reason (`verdicts[-1]["reason"]`, `:251-252`), which may be SOC_MISSING, ASSET_MISMATCH or another reason. The "only when" direction is correct. The implied reason code is not guaranteed.
  - Fix: optional. Say "refused (with the last segment's reason, for example SOC_NOT_ABOVE_HEADROOM)".

### HTML

- The page is self-contained. It has no `<script>`, `<link>`, `<img>`, `@import` or http(s) URL. The only hrefs are 8 in-page anchors, all of which resolve, plus the sibling `convertion_potential.html`.
- All 5 SVGs parse as XML, and the HTML tags balance.
- The light tokens (`:root`), the dark tokens (`prefers-color-scheme` + `:root:not([data-theme="light"])`) and `:root[data-theme="dark"]` define the same 16 tokens.
- Every `var(--…)` that is used is defined. There are no raw colour literals in fill or stroke, and `body` has an explicit background.

### Not verified

- PostgreSQL-backed tests, by constraint.
- Browser rendering. I inspected the source only.

## Review (revision 3)

Reviewer: fresh Claude Reviewer, 2026-11-15, main at bf6014e02956d9e7392329cbce46300037c9d9d8 (the document's working-tree revision 3). Scope: the new §5-8 against `.agent/owner-portfolio-composition-request-2026-11-15.md` and the demo-data question. I changed no code, test, database or document. I ran only pure tests and read-only queries (inside `BEGIN READ ONLY`) on `assetops_polish_walk1113_test`.

### Verdict: REVISE (one Medium; seven Lows that do not block)

§5, §6 and §7 are accurate. I found no false "summed", "never summed" or "lead Finding only" claim. The one blocking item is in §8.9. The build-time extrapolation is the headline answer to the owner's question about cost as Sites and horizon grow, and it counts only the Kobo child phase, so it is about a third of the measured build. The fix is a few sentences.

### What I verified

**§5 composition (code read line by line):**

- **Moves, checks and records.**
  - `ENTRIES` is at `outcome_map.py:17-37`.
  - The 10 CONTRIBUTIONS records are at `:150-180`, all MOVES. `status` is declared at `:147` and has no record.
  - `OutcomeEvaluator._record` takes the first match (`chain/outcomes.py:94-95`).
  - Six strategies are registered (`strategies/__init__.py:12-13`). Records use only graded_verdict, priced_energy, avoided_cost and direction_only. `finding_presence@` and `recorded_amount@` appear in no record.
  - `recorded_amount@1` returns `NO_RECORDS` unconditionally (`recorded_amount.py:1-11`).
- **Status rules and roll-up.**
  - First match wins: an open, unapplied primary Finding or a NEEDS_ATTENTION warning gives NEEDS_ATTENTION, then MISSED, then WATCH (`status.py:73-102`).
  - The roll-up uses `PRECEDENCE`, and the lead is the first outcome in catalogue order (`:34`, `:105-113`).
  - `row_nodes` takes earnings and potential from the first outcome in catalogue order, and kpi from the lead / declared outcome / record cascade (`board.py:367-382`).
- **Money.**
  - `estate_income` rounds each Site to the minor unit and then sums. It accepts one currency only, and "At least" applies when any basis is not COMPLETE or any Site is not known (`vocabulary.py:459-508`).
  - The Optimize card lists the claims and never sums them (`read.py:901-924`).
  - Value and fuel lines are one line each and never summed (`read.py:952-962`).
  - Counts are summed, and any failed Site read makes them NOT_KNOWN (`claims.py:206-216`).
  - Sites disrupted means primary Protect, in OPEN / RECURRED / ACTION_IN_HAND, excluding UNEXPLAINED_FUEL (`:42-43`, `:157-161`).
  - A mill Action on a thread that is already counted is excluded (`:137-143`).
  - A data-gap day is not taken twice (`:100-108`).
  - One builder serves both routes (`read.py:759-777`, `:926`).
- **Lead-Finding money and the 7-day claim.**
  - `lead_finding` is at `chain/read.py:190-212`. The MG-2 earnings read only `inp.money_heads[inp.lead_findings[...]]` (`chain/outcomes.py:190-196`).
  - `_window_parts` replaces only `window` and `rows` (`read.py:586`). The money head therefore stays the board day's lead, and the Portfolio Optimize figure for a 7-day window is one Finding's exposure from the last day. The document is correct, and this is the most useful new fact in §5.
- **Tests.** All 23 test names cited in §5-8 exist in the named files. I ran `tests/test_ch6_contributions.py test_out_b1_status.py test_out_b2_mini.py test_ch6b_estate_chain.py test_ch5d1_optimize_card.py test_ch3_rows.py test_pv1_value_lines.py test_ch6b2_portfolio_cards.py test_mb1_opportunity_board.py test_s4_fuel_cost.py test_hon1_complete_readings.py test_tfc2.py -q`. Result: **345 passed, 1 warning in 3.87 s**.

**§5.6 frontend (`frontend/src`):**

- The Portfolio matrix renders only the pill and the lead label (`PortfolioOutcomes.tsx:350-366`).
- `headline`, `short_value`, `headline_money` on the summary rows, `sites_needing_attention`, `warning_count`, `category_counts`, `recovered_value` and `value_cards` are typed only (`estateClient.ts:490-513`, `:647-671`). None of these is rendered by an estate component.
- Only the Grow row renders nodes (`OutcomeBoard.tsx:118-147`, `:264`).
- Value and fuel lines sit inside `CardQualifiers`, behind "Why?".
- `verified_values`, `unexplained_fuel` and `thread_lines` do not occur in `frontend/src`.
- No frontend code builds the bare `/api/estate/chain` URL (see L3).

**§6.** Each verdict follows from §5 and §7. I checked `warnings.py:42` and `:45`, `credit.py:57-72`, `dispatch_v3.py:466-468` and `placement.py:5`, and found no "recoverable" in the backend. None of the verdicts over- or under-claims.

**§7:**

- Cold and EV have no verification family. `FAMILIES` is reserve + MIDDAY + FUEL (`verification_families.py:502`, `:516`), and MIDDAY refuses a non-MINI Action (`:139`).
- `WorkService.post_event` refuses outcome requests (`work/service.py:265-266`).
- VERIFIED is a cause only from `verification_outcome` (`lifecycle_run.py:45-53`). `ACTION_IN_HAND → CHANGE_APPLIED` is at `lifecycle.py:49`, and `DISRUPTED_STATES` excludes CHANGE_APPLIED. The §7.5 inference holds, and the walk1113 log shows `CHANGE_APPLIED: 2`.
- `convertion_potential.html:413` says what §7.5 quotes. Its cold cell already says "no cold verification plan exists", so the correction mostly adds the EV case and the Protect-count consequence.
- I also checked price keys (`assumptions.py:32`, `price_page.py:82-88`), the cold consequence nulls, the domain_action criteria, `BILLING_GAP` / `NO_RECORD`, the idle-charger record with no producer (`chain/graph.py:47-50`), and the scenario-kind rules. All are accurate.

**§8:**

- **Template.** Every §8.1 template value matches `kobo-mini-grid-60kw.yaml`.
- **Scenarios.** The scenario values in §8.2 match (37 files = 36 YAML + README).
- **Simulator.**
  - The mini_grid docstring says: linear fuel, "no idle fuel and no start fuel", rating a ceiling, FAILED inert.
  - Charging only when the battery is not discharging is at `:721-730`.
  - v5 uses `effective_start_threshold = min(start, reserve + 5)` (`:1141-1156`). With 30 / 35 that gives 35, and a 25 % reserve gives 30. The "trial effect built in" claim is correct.
  - Case A: PV 48 kW is more than the 15 kW load, so dispatch rule 1 (`load > pv`) cannot fire and rule 3 does (`dispatch_v3.py:290-296`). The PV-alone claim is correct.
- **Idle fuel.** An unloaded generator gives 0 L by the linear law. `NO_LOAD` is 3.3 L/h `GENERIC_DEFAULT` (`demo_combined_kobo.py:140-153`). `test_tfc2.py:73-88` pins a 3.3 L / 4.125 USD idle-only credit.
- **Profiles.** Profiles, versions, parsing limits, cadence / bias / dropout and the transform order are correct.
- **Calendar.** The calendar matches v4. `S = DB day − 2` holds, and `mill_change_day` is S-9.
- **Ingestion.** The ingestion route exists. `ADD_DAY_KINDS` matches. The planner estimate is 110 × 28 + 60 = 3,140 s. `prepare` drops and recreates the database (`:1045-1046`).
- **Measured figures.** Phase times match `polish_walk1113-prepare.log`: 1724.7, 1473.9, 1195.1, 817.2, 132.6, 52.4, 47.6, 45.6, 35.4 + 1.0, 22.4 and 5.8 s, which sum to ≈ 5,554 s. The work marker is at 08:50:40 and the log mtime at 10:50. The other two logs match too (1991.0 / 2671.7 and 1234.4 / 2282.2).
- **Read-only database queries.**
  - `pg_database_size` = 1,769 MB.
  - The largest tables match to the MB (635 / 259 / 208 / 104 / 97 / 91 / 70 / 66).
  - `chain_response` has 8,828 rows.
  - `accepted_evidence` holds 131,249 rows: KOBO 85,326 / KISIWA 40,104 / EV 4,951 / COLD 868, all `source_mode = SIMULATED`.
  - The per-day figures use distinct UTC source days (30 / 12 / 3 / 9).
- **Storage arithmetic.** 5.9 MB and 107 GB, then 40 MB and 732 GB, are correct, labelled and bounded.

**HTML:**

- The page is self-contained: no script, link, img, @import or URL. 18 hrefs, all resolve.
- 8 SVGs parse as XML, the tags balance, and there are no duplicate ids or dangling `url(#)`.
- The light, `prefers-color-scheme` and `[data-theme="dark"]` blocks define the same 16 tokens. Every `var()` is defined, there are no raw fill or stroke literals, and `body` has a background.

### Findings

- **M1 (Medium). §8.9 build-time extrapolation understates the build by about 3×, and its wording hides it** (the "Extrapolated" list, first item; Figure 8 caption).
  - *What the document says.* "Build time for Kobo-like Sites ≈ N × D × 62 s … The 62 s is 1,724.7 s ÷ 28 built Kobo days …, plus drains and self-check, which grow with the data. Example: 50 Sites × 365 days ≈ 1.1 × 10⁶ s ≈ 13 days."
  - *What 62 s covers.* It is the `kobo:` child phase only. Drains, self-check, mini-depth (2,996 jobs, untimed), period rows and day rows are not in the 62 s or in the 13-day example, even though the sentence reads as if they are. The measured walk1113 build was ≈ 7,200 s wall, of which Kobo was 1,725 s. Kisiwa costs about 119 s per night, about twice Kobo's per-day rate. Figure 8's own caption says most of the time goes to drains and self-check.
  - *Why it matters.* This is the number the owner will use to judge whether portfolio-scale simulation is feasible, and it is presented as the estimate rather than as a floor.
  - *Fix.* Label 62 s per Site-day as a lower bound for ingest + assess + match only, and add a whole-build figure. The measured ≈ 7,200 s wall over ≈ 49 built Site-days (28 Kobo + 10 Kisiwa + 8 Cold + 3 EV) is ≈ 147 s per Site-day, or ≈ 2.7 × 10⁶ s ≈ 31 days for 50 × 365, if drains and checks scale with data. State the 50 × 365 result as a range of about 13 to 31 days, sequential, and name the assumption that the self-check and drains scale linearly. While there, use one day denominator: r = 2,844 uses 30 UTC days, while the time rate uses 28 built days.
- **L1. §5.2 states the lead-Finding precedence backwards.** "The lead is the pinned one, else the latest episode start …" is not what the code does. In `chain/read.py:205-211`, the pin wins only while the day is not settled or the source is closed. In the normal case (settled and source open), the discovered head wins: the greatest episode start, then the smallest id. Fix: "the latest episode start meeting the day (smallest id on a tie); a pinned Finding only while the basis is incomplete or the source closed."
- **L2. §5.3 "Open threads … summed" cites a test that does not prove a thread sum.**
  - `test_ch6b_estate_chain.py::test_counts_are_summed_over_the_sites` has no thread rows, so the thread read raises `AttributeError` and the thread claims are NOT_KNOWN. It asserts only that days are summed (`:239-243`).
  - The thread-count tests in `test_ch5a2b_claims.py:140-162` each use one Site. The sum at `claims.py:209-212` is correct by reading, but no multi-Site thread-sum test exists.
  - Fix: cite the test for days, and say "thread sum: by code, no multi-Site test".
- **L3. §5.6 "/api/estate/chain is never called (searched estate/chain)" needs a qualifier.**
  - The claim is true for the bare route.
  - The search method would not find URLs that the frontend builds from parts. The frontend does call `/api/estate/chain/why`, built as `ESTATE_API_PATH` + `/chain/why` (`frontend/src/sites/chainClient.ts:16`, `:81`).
  - Fix: name the why route as called and the bare route as not called.
- **L4. §8.5 and §8.7 day kinds.**
  - The v4 calendar has no Kobo `degraded` day. Only S-28 (normal) and S-21 (overcast) run `kobo-s3-dispatch-necessary-run`, so Case B appears on two calendar days.
  - §8.7 "On every overuse and trial day … the 90 % stop policy then keeps the generator on" should exclude trial-after (S+1, 25 % reserve), where the generator never starts. The next paragraph says this, but the first sentence contradicts it.
  - Fix: name the two days, and say "overuse days and trial-before".
- **L5. §8.6 idle-fuel row merges two figures.** The row says the fuel figure "comes only from the declared generic 3.3 L/h no-load rate × 1.10". The × 1.10 is the exposure's upper multiplier (`chain/outcomes.py:308`). The credited trial value uses the nominal 3.3 L/h with no multiplier (`test_tfc2.py:76-78`: 3.3 L, 4.125 USD). Fix: split the sentence into the exposure upper bound (× 1.10) and the credit (nominal).
- **L6. Citation drift (no claim affected).**
  - `objectives.py:112-145`: the file has 143 lines.
  - "Only PRODUCTIVE_LOAD calculates" is cited at `scenario_rules.py:24-25`, but the rule is at `:194-200`.
  - `evidence_api.py:158` is `SITE_EVIDENCE_ROUTE`; the batches route is at `:157`.
  - `packs/cold.py:44-58`: the 13-property map starts at `:50`.
  - The rev-3 note (l.107) and §7 lead (l.997) announce "two corrections", but §7.5 is one correction plus its consequence.
- **L7. Context for §8.9's source build.** The walk1113 prepare ended `SELF-CHECK FAILED` (CO-10). This does not change the timings, but the page names the build as the measurement source. Fix: optional; add one clause noting that the self-check failed on CO-10 and that the timings are unaffected.

### Not verified

- PostgreSQL-backed tests, by constraint. Browser rendering: I inspected the source only.
- §8.7 Case A and Case B are inferred from scenario values and are not simulated. The document says so, and I did not run them either.
- The `kisiwa-diesel-hybrid-60kw.yaml` and other template line citations, and `host/ev_publication.py:282` / `:331` beyond the TUESDAY 08:00-16:00 rule: spot-checked, not line-audited.
- The database size and `chain_response` rows were read on 2026-11-15 and can drift as the walkthrough database is used.

### Residual risk not named in the document

- The Optimize card's 7-day window equals one Finding on the last day (§5.2). A viewer would read it as the window's exposure, and the card text does not say so. This is worth an owner decision, not a document fix.

## Re-review (revision 3.1)

Reviewer: fresh Claude Reviewer, 2026-11-15. Document: working-tree revision 3.1 of `.agent/decision-intelligence-mechanism-2026-11-14.html` (main at bf6014e02 plus uncommitted edits). There was no saved revision-3 copy, so I read every section that the 3.1 change note names, and opened every citation in those sections. I changed no code, test, database or document; I only appended this section. I ran pure tests only and read-only queries (`BEGIN READ ONLY … ROLLBACK`) on `assetops_polish_walk1113_test`.

### Verdict: ACCEPT WITH NOTES (no High or Medium; three Lows)

M1 and L1-L7 are fixed in the body, not just in the change note. The new §5.2 bullet is accurate and makes no design proposal. The HTML is still clean. The three Lows are arithmetic and labelling details in §8.9 and Figure 8. None of them changes a conclusion.

### Prior findings

- **M1: fixed.**
  - *Lower bound.* §8.9 now labels 62 s as a lower bound covering ingest, assess and match only, and names what it leaves out: drains, mini-depth, period rows, day rows and the self-check. 1,724.7 ÷ 28 = 61.6 s, and 72 runs at about 24 s each is correct.
  - *Whole build.* I re-derived the rate from `/opt/assetecon/AssetOpsV1-walk/var/polish_walk1113-prepare.log` and the files in the work directory. The log mtime is 10:50:48.07. The 7,204 s figure runs from `keys.json` (08:50:44); the marker file itself is at 08:50:40 (see N3). The build covered 28 Kobo built days (30 calendar days in v4 minus the 2 `missing` days), 10 Kisiwa nights, 8 Cold sessions and 3 EV runs, which is 49 Site-days. 7,204 ÷ 49 = 147.0 s.
  - *50 × 365 range.* 18,250 × 61.6 s gives 13.1 days and 18,250 × 147 s gives 31.05 days. The page labels both as extrapolations ("formulas, not measurements") and names the linear-scaling assumption.
  - *Storage.*
    - `pg_total_relation_size('accepted_evidence')` is 272,015,360 B. Divided by 131,249 readings, that is 2,072 B per reading.
    - Kobo r = 85,326 ÷ 28 = 3,047. That gives 6.31 MB per Site-day and 115.2 GB for 50 × 365.
    - The whole database is 1,770 MiB ÷ 131,249 = 14.14 KB per reading. That gives 43.1 MB per Site-day and 786 GB.
    - All of these match the page.
  - *Day count.* The 30 vs 28 problem is gone. The old "30 UTC days / 2,844 / 5.9 MB / 107 GB / 732 GB" figures appear nowhere, and both the time rate and r use built Site-days.
  - *Planner estimate.* `tools/demo_combined.py:132-133` matches the 110 × days + 60 estimate.
- **L1: fixed.** §5.2 now matches `chain/read.py:205-211`. The latest episode start wins, then the smallest id. The pin wins only when `not (settled and source_open)`. The added cites `mini.py:587-590` (the `lead_finding` call) and `:1366-1374` (`_lead_findings`, the generator-only gate) are accurate.
- **L2: fixed.**
  - §5.3 now cites the test for days only. It gives the thread sum as "by code (`:209-212`)", and `claims.py:209-212` is the `open_n` / `verified_n` / `disrupted_n` sums.
  - It also states that no multi-Site test exists, which matches the single-Site tests in `test_ch5a2b_claims.py:140-172`.
- **L3: fixed.** §5.6 says that the bare route is not called and that `/chain/why` is called. `chainClient.ts:16` is `const ESTATE_API_PATH = "/api/estate"`, and `:81` returns `${basePath}/chain/why?…`.
- **L4: fixed.**
  - §8.5 names S-28 (`normal`) and S-21 (`overcast`) as the Case B days and states that v4 has no Kobo `degraded` day. I confirmed this from the `sites.kobo` list in `demo-story-days-v4.json`, which has 30 entries.
  - §8.7 Case A now reads "overuse days (S-14, S-7) and trial-before (S)", which excludes trial-after.
- **L5: fixed.** §8.6 separates the exposure upper bound (× 1.10, `chain/outcomes.py:308`, `idle_part = mult × …`) from the credit. The credit is 3.3 L and 4.125 USD nominal (`test_tfc2.py:76-78`, inside `test_idle_only_demo_figures_from_the_inputs`).
- **L6: fixed.**
  - `objectives.py:112-143`: the file has 143 lines, and `judge` is at `:112`.
  - `scenario_rules.py:194-200`: "Only PRODUCTIVE_LOAD calculates" plus the `kind != "PRODUCTIVE_LOAD"` guard.
  - `evidence_api.py:157` is `INGESTION_BATCHES_ROUTE`.
  - `packs/cold.py:50-64` is the comment plus the 13-entry `PROPERTY_FIELDS`, which closes at `:65`. That is acceptable.
  - The §7 lead (l.1005) and the rev-3 note (l.114) both say "one correction … plus its consequence".
  - The §4 table (l.826) still cites `scenario_rules.py:24-25`, but only for "a stored calculation" (`CALCULATION_STATES`), which those lines support.
- **L7: fixed.** §8.9 cites `53 pass, 1 fail ['CO-10']` at log line 55, which I confirmed. The self-check is the last phase, it ran all 54 checks with 0 skipped, and the timings are unaffected.
- **New §5.2 presentation-risk bullet: accurate.**
  - `_optimize_card` (`read.py:901-924`) builds value, detail ("At {site} · not added across sites"), basis and days_line, and none of them mentions the last day or a single Finding.
  - `vocabulary.py:580` is quoted exactly.
  - The bullet says "records the risk and does not propose a design", and it doesn't propose one.

### Citations opened for 3.1

All of the following resolve and support the claims made of them:

- `chain/read.py:205-211`
- `mini.py:587-590`, `:1366-1374`
- `claims.py:42`, `:209-212`
- `lifecycle_run.py:50-53`
- `lifecycle.py:49`
- `chainClient.ts:16`, `:81`
- `read.py:586`, `:602-607`, `:901-924`
- `vocabulary.py:580`
- `chain/outcomes.py:308`
- `test_tfc2.py:76-78`
- `objectives.py:112-143`
- `scenario_rules.py:194-200`
- `evidence_api.py:157`
- `packs/cold.py:50-64`
- `demo_combined.py:132-133`
- prepare log line 55

The four cited test names exist.

### Findings

- **N1 (Low). Figure 8, "per built Site-day: KISIWA 4,010 · COLD 109", divides by the prepare's day counts, but the readings include the add-dates day.**
  - *What the database shows.* `polish_walk1113-adddates.log` (13 Nov 13:02) added one Kisiwa night and one Cold session after the prepare. A read-only count shows 3,645 Kisiwa and 98 Cold readings received after the prepare ended at 10:51: Kisiwa 36,459 of 40,104 and Cold 770 of 868 were in place by then.
  - *Correct figures.* 40,104 ÷ 11 ≈ 3,646 and 868 ÷ 9 ≈ 96. Alternatively, keep the 10 and 8 denominators with 36,459 and 770 readings.
  - *What is not affected.* Kobo (85,326, all present by the end of the prepare) and EV are correct. The headline extrapolations use Kobo r only, so 115 GB and 785 GB stand.
  - *Fix.* Use 11 and 9 as the denominators, or say that the database also holds the 12 Nov add-dates day.
- **N2 (Low). The 147 s rate averages full days with short sessions, so 31 days is not an upper end for Kobo-like Sites.**
  - *The problem.* The 49 Site-days include 8 Cold sessions of about 65 minutes and 3 EV runs of 8 h. Over the 38 full-day Sites (Kobo + Kisiwa), the same wall time gives 7,204 ÷ 38 ≈ 190 s. For 50 × 365 Kobo-like Sites, that is ≈ 40 days.
  - *How the page reads.* "between … 13 days and … 31 days" reads as a bracket. This was the shape the revision-3 review suggested, and the conclusion holds either way: weeks of sequential compute, so per-Site regeneration or parallelism is needed.
  - *Fix.* Add one clause: 147 s is a mixed-vertical average, and for full-day mini-grid Sites it is about 190 s, or about 40 days.
- **N3 (Low, trivial).** §8.9 says the build ran "from the work marker at 08:50:44". The marker file `.demo3-combined-work` is at 08:50:40 (7,208 s), and 08:50:44 is `keys.json`. The rate is unchanged at 147 s. Fix: say "08:50:40" or name `keys.json`.

### Checks run

- Pure tests: `.venv/bin/python -m pytest tests/test_ch6b_estate_chain.py tests/test_ch5a2b_claims.py tests/test_tfc2.py tests/test_out_b2_mini.py tests/test_ch5d1_optimize_card.py -q`. Result: **113 passed in 2.12 s**.
- Read-only queries, inside a READ ONLY transaction:
  - `pg_database_size` = 1,770 MB.
  - `pg_total_relation_size('accepted_evidence')` = 272,015,360 B.
  - Readings per Site, with distinct UTC days and how many arrived before 10:51:
    - KOBO: 85,326, 30 UTC days, all before the end of the prepare.
    - KISIWA: 40,104, 12 UTC days, 36,459 before.
    - EV: 4,951, 3 UTC days, all before.
    - COLD: 868, 9 UTC days, 770 before.
- HTML:
  - No script, link, img, `@import`, external `url(` or http(s) reference.
  - All 8 SVGs parse as XML.
  - 39 ids, none duplicated, and no dangling `url(#)`, `href="#"` or `aria-labelledby`.
  - The light, `prefers-color-scheme` and `[data-theme="dark"]` blocks define the same 16 tokens, and every `var()` is defined.
  - There are no raw hex fill or stroke values, and `body` has a background.
  - The only file link, `convertion_potential.html`, exists.

### Not verified

- Browser rendering: I inspected the source only.
- Revision 3 → 3.1 as a literal diff: no revision-3 copy exists, so I checked by section and citation instead.
- PostgreSQL-backed tests and the full suite, by constraint.

### Residual note (not a finding)

- The Optimize card can carry a days line from the shared coverage line (`_own_days`, `read.py:807-820`). That line names the window's checked days, which may reinforce the §5.2 misreading. This belongs with the owner decision that §5.2 already raises.

## Review (revision 3.2)

Reviewer: fresh Claude Reviewer, 2026-11-15. Document: working-tree revision 3.2 of `.agent/decision-intelligence-mechanism-2026-11-14.html`. I changed no code, test, database or document; I only appended this section. I ran in-memory probes and one pure test file, and read-only queries (`BEGIN READ ONLY … ROLLBACK`) on `assetops_polish_walk1113_test`.

### Verdict: ACCEPT WITH NOTES (no High or Medium; five Lows)

Every measured figure in §8.10 and Figure 9 reproduces from the probes and the walk1113 artefacts. The growth claim is sound, its cause is cited correctly and labelled as inferred, and the extrapolation arithmetic is right. N1-N3 and the two Q5 Lows are fixed in the body. The Lows are one inaccurate clause in the parallelism table, three places where a hedge in the text is dropped in a figure or conclusion, a point estimate given without its measured range, a Figure 8 / Figure 9 inconsistency, and two trivial details.

### Measured figures (reproduced)

- **Simulator step.** My own probe (`kobo_draft` + `run_to_end`, reserve trial, model v6, 3 repeats each) gave 97 boundaries in 0.123-0.138 s (1.28-1.44 ms per step) and 481 boundaries in 0.648-0.723 s (1.35-1.51 ms). The page says ≈ 1.4 ms, 0.134 s and 0.694 s: matches.
- **Live window.** `generate_live_window` for 8 h gave 0.63-0.65 s for 842 readings (0.75-0.77 ms per reading). The page says 0.66 s and ≈ 0.8 ms: matches.
- **Per run.** From the mtimes of the 72 `kobo-replay-a0alpf69/*/h/run-*.yaml` drafts, the successive intervals range from 10.6 to 78.3 s. 1,724.7 ÷ 72 = 24.0 s.
- **Per Site-day.**
  - Kobo: 1,724.7 ÷ 28 = 61.6 s.
  - Kisiwa: `kisiwa.json` `wall_seconds` 1,192.7 ÷ 10 = 119 s.
  - Cold: 22.4 ÷ 8 = 2.8 s.
  - EV: 52.4 ÷ 3 = 17.5 s.
  - `manifest.json`: `wall_seconds` 7,207.7, `finish-rows` (the self-check, `demo_combined.py:1201-1205`) 1,473.9, `finish-ticks` 656.0, `drain-1` + `drain-2` = 864.8, `mini-depth` 414.5, rows 45.6 + 132.6 = 178.2.
  - The remainder of `after_children` (1,837.5 − 1,273.9 = 563.6 s) is the performance step and the pre-build after the drain (`demo_combined.py:1395-1400` docstring), so the "≈ 564 s (derived)" bar is right.
  - The eight bars sum to 7,209 s.
  - The bar widths are at 14.4 s/px.
- **Drains.** I parsed the 8 drain tick reports: 384 stage runs, of which 348 did no work, for 313.6 s (about 0.90 s each, about 10.8 s per idle Site visit). Kobo `chain_snapshots` processed 825 items in 289.4 s, which is 351 ms each and 10.3 s per built day. The "≈ 56 %" share equals the children, mini-depth and rows plus the 447 s of snapshot-stage time: (3,588 + 447) ÷ 7,208 = 56 %.
- **Kisiwa batches.** Read-only count: 20,033 `ingestion_batch` rows carrying 40,104 accepted readings.

### Growth with Site history (sound)

- **Evidence.** Grouping the run intervals by kind and regressing against the global run index gives:
  - steady-before: 18.2 → 34.8 s, slope 0.410
  - before-rest: 14.0 → 21.2 s, slope 0.213
  - night-early: 11.0 → 29.6 s, slope 0.276
  - steady: 36.8 → 45.5 s, slope 0.494
  - night-early-after-before: slope 0.234
  - mill-rest: slope 0.325
  - steady-before-first: slope 0.380

  Every kind rises, so the stated range of 0.21-0.49 is right. The 12 steady-before runs are 16-31 Oct and 12 h long (`interval_start_time` 03:00, end 15:00). The Figure 9 dots plot correctly at 6 px per second.
- **Second Site.** Kisiwa's per-night `seconds` in `kisiwa.json` also rise, from 103.6 to 127.1 s. That supports the claim, and the page could mention it.
- **Cause.** The cause is correctly cited.
  - `finding_service.py:44-60` (`bases`) reads every window from `assessed_days`. That is `SELECT DISTINCT window_start … ORDER BY window_start` in `postgres_finding_store.py:139-143`.
  - `:62-68` (`match`) calls it on every pass.
  - The build calls `match` once per run (`demo_combined_kobo.py:398-400`).

  The section labels the cause "Probable cause, by code reading and not profiled".
- **Hedge on the quadratic total.** The 50 × 365 paragraph hedges it ("could flatten … not known"). The exception is the owner conclusions (L2).

### Parallelism and optimisation claims (code-checked)

- **No parallel Site builds:** confirmed (`demo_combined.py:1080-1088`).
- **No parallel runs:** confirmed (`demo_combined_kobo.py:398-400`).
- **Thread pool only in `warm_ranges.py:51` and `:484`:** confirmed. A grep of `tools/` and `backend/assetops_backend/` (excluding tests) finds no other `ThreadPool`, `ProcessPool`, `multiprocessing` or `concurrent.futures` use.
- **One environment claim:** confirmed (`tick.py:10-11`).
- **Ordered Site visits:** confirmed (`:382`).
- **Stage children by `subprocess.run`:** confirmed (`:152-156`).
- **`MERGE_COPY` guard string:** confirmed (`writer_guard_probes.py:95`).
- **Mini-depth `limit=500` loop:** confirmed (`demo_combined.py:1303-1318`), against the tick's `mini_jobs_per_site: int = 10` (`tick.py:70`).
- **`CREATE DATABASE … TEMPLATE`:** confirmed (`chain_clone.py:64`).
- **Seal-once:** confirmed (`demo_combined_kobo.py:355-361`).
- **`seed_snapshots`:** confirmed (`site_outcomes/read.py:649`).
- **`read_scope.memo`:** confirmed (`claims.py:172`).
- **`"written": 0` at prepare log lines 52-53.** Note that the day rows still took 102.7 s to establish that nothing changed.
- **Per-Site claims:** see L1.

### Extrapolations (arithmetic checked)

With c(d) = 33 + 2.0 d summed over d = 1..D:

| D | Σ c(d) | Downstream (26 × D) | Total |
| --- | --- | --- | --- |
| 28 | 1,736 | 728 | 0.68 h |
| 90 | 11,160 | 2,340 | 3.75 h |
| 365 | 145,635 | 9,490 | 43.1 h |

- 50 × 43.1 h = 89.8 days.
- The linear figures are 18,250 × 61.6 / 147 / 190 s = 13.0 / 31.1 / 40.1 days.
- The downstream parts are right:
  - mini-depth: 414.5 ÷ 38 = 10.9 s, and 414.5 ÷ 2,996 = 0.138 s per job;
  - snapshots: 10.3 s;
  - Kobo rows: (35.0 + 103.8) ÷ 28 = 5.0 s.
- Everything is labelled derived or extrapolated.

### N1-N3 and Q5: fixed in the body

- **N1.** Figure 8 reads "KISIWA 3,646 · … · COLD 96" with the "÷ 11 and ÷ 9" note.
- **N2.** §8.9 has the mixed-vertical clause and ≈ 190 s / ≈ 40 days.
- **N3.** §8.9 gives "work marker 08:50:40" (the marker mtime is 08:50:40.42) and `manifest.json` 7207.7.
- **Q5.** The returned reason is now stated as `verdicts[-1]["reason"]` (`reserve_trial.py:251-252`, confirmed). The headroom-ignored case is stated as having no pinning test. That is confirmed: `TestSocHeadroomBoundary` (`test_s6_action_rule.py:89-101`) uses single segments only, and `test_any_eligible_segment_is_enough_and_is_cited` (`:183-189`) uses a segment with no readings.

### Findings

- **L1 (Low). The parallelism table, row "Ticks or stages in parallel", says of per-Site claims "no build or serve path uses it". The tick takes the per-Site claim on every visit.**
  - *What the code does.* `tick.py:19` (docstring step 5) and `:415-417` show `_site` → `self.store.claim_site(...)`, which writes `schedule_site_head` (`postgres_schedule_store.py:194-201`).
  - *What would be true.* What no path does is run Sites concurrently: the environment claim serialises ticks, and the build children call `runner.step` directly without any Site claim.
  - *"Safe by design" is also unverified.* Discovery (`reconcile_all()`) is global, and the build path takes no claims, so the page shows no concurrency safety.
  - *Why it matters.* The owner asked specifically about parallelism.
  - *Fix.* "Each tick takes a per-Site claim (`tick.py:417`), but the environment claim lets only one tick run at a time, and the build children take no claim. Whether Site work could run concurrently was not examined."
- **L2 (Low). Three places state as fact what the text hedges.**
  - *The owner conclusions.* Conclusion 2 lists "the O(D²) re-read in matching" as a lever. The body calls the cause probable and not profiled.
  - *Figure 9's left panel.* It labels the self-check "fixed per build" and says "about 44 % is fixed per build or per tick". The bullet below says that how these grow "was not measured", and the self-check does check data over all Sites.
  - *"With Sites: linear".* It carries no measured or derived tag, and it is an assumption: the per-tick idle cost grows with N, and the discovery step is global.
  - *Fix.* Add "probable" to the conclusion, "(not measured)" to the figure, and a "derived" tag to "With Sites".
- **L3 (Low). The model gives a point estimate without the measured range.**
  - *The problem.* The per-day slope 2.0 implies a per-run slope of about 0.30 (2.0 ÷ 2.6²), but the page does not say which per-run slope it used. Across the measured 0.21-0.49, refitting to the 62 s mean gives:
    - 365 days: ≈ 33-65 h for one Site;
    - 50 × 365: ≈ 70-135 days, not a single 90.
  - *A small indexing point.* d is defined as "days already built" (0..27). The fit (intercept 33) uses d = 1..28, and with 0..27 the mean is 60 s.
  - *Fix.* State the slope that was used and give the range next to 43 h and 90 days.
- **L4 (Low). Figure 8's left panel is now inconsistent with Figure 9 and the manifest.**
  - *Figure 8.* It says "Timed phases ≈ 5,554 s … (untimed steps incl. 2,996 mini-depth jobs)".
  - *The manifest.* `step_timings_seconds` times mini-depth at 414.5 s and finish-ticks at 656.0 s.
  - *Figure 9.* It shows both as measured.
  - *Fix.* Drop "untimed … mini-depth" from Figure 8, or point it to Figure 9's full composition.
- **L5 (Low, trivial).**
  - *A stray parenthesis.* §2.4 Q5 l.522 reads "no test pins that case ( inputs from `…postgres_action_store.py:159-215`)": the parenthesis is stray and the sentence is broken.
  - *Kisiwa batches.* §8.10 says "about 2,000 small batches a night (20,033 batches …)", but the 20,033 include the add-dates night, which is the N1 issue again: 20,033 ÷ 11 ≈ 1,820.

### Checks run

- **Probes**, written to `…/scratchpad/rv/p.py`:
  - My own `run_to_end` probe, as above.
  - The existing `simprobe/probe2.py`, run twice.
  - Load average 1.3-2.5 on 8 cores during the probes. The page states 0.7.
- **Artefact parsers:**
  - `…/scratchpad/rv/runs.py`: per-run intervals and slopes by kind.
  - `…/scratchpad/rv/drain.py`: drain stage idle and snapshot totals.
- **Pure test:** `.venv/bin/python -m pytest backend/tests/test_s6_action_rule.py -q` gave **60 passed in 0.37 s**.
- **Read-only query:** `ingestion_batch` count and `sum(accepted_count)` per Site: KOBO 532 / 85,326, KISIWA 20,033 / 40,104, EV 30 / 4,951, COLD 71 / 868.
- **HTML:**
  - The 9 SVGs parse as XML.
  - 42 ids, none duplicated, and no dangling `url(#)`, `href="#"` or `aria-labelledby`.
  - No script, link, img, `@import` or http(s) reference.
  - The `:root`, `:root:not([data-theme="light"])` (inside `prefers-color-scheme`) and `:root[data-theme="dark"]` blocks define the same 16 tokens, and every `var()` is defined.
  - There are no raw hex fill or stroke values.
  - Figure 9's longest right-panel lines estimate to about x = 953 of 1000 with Helvetica metrics, so they fit.

### Not verified

- The "cold import of the stage module measured 1.9 s". `import assetops_backend.scheduling.stages` took 0.07 s warm here, because the stage imports are lazy. I did not reproduce a cold first-import. The 0.7-1.2 s idle floor itself is confirmed from the tick reports.
- That the run-level split is impossible because of story-clock timestamps. I accepted this as stated.
- Browser rendering. I inspected the source only.
- The PostgreSQL-backed tests and the full suite, by constraint.
