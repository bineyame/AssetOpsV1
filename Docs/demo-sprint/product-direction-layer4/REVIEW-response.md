# Layer 4 pack: response to the independent review

## Author response (rev 2)

**AssetOps Architect (Claude) · 16 Nov 2026 · branch `task/product-direction-layer4-design`, edits on top of `f1f6d9bf9`, nothing committed.** `REVIEW.md` is unchanged. All edits are inside `Docs/demo-sprint/product-direction-layer4/`.

**Checks after the fixes:**
- `python3 check_manifest.py` gives **126 checks passed, 0 failed**. It had 73; it was extended for M1, M3, L2, L3 and L10.
- `node build.mjs` rebuilt the mock-up, and `tools/run-audit.sh` passes everything:
  - 146/146 routes render with no errors.
  - 0 broken links.
  - 0 routes overflow at 390 px.
  - 0 internal-vocabulary hits on the 36 added screens and their drawers. The forbidden list is now wider.
  - Drawer focus, trap, Escape and return all pass.
  - Focus visible 6/6; contrast 14/14.
  - The role toggle keeps the same numbers in 4/4 roles.
  - All 4 budget × letter-of-intent cases pass.
  - The pilot form only shows the example toast.
- The main HTML re-renders: 5/5 diagrams, no script errors, no overflow at 390 px.

| Finding | Outcome | What changed |
|---|---|---|
| **M1** The "cheapest" EV schedule was not the cheapest bill | **Fixed** | Tariff C-114 gains a 00:00–05:00 tier at 0.09; October is unaffected, because charging on arrival ends around 23:10. EMB-CHEAPEST is now costed at 12,975/month, the lowest bill, and is still rejected because 3 buses are short. EMB-DEADLINE is 13,356/month (saving 8,788.80; 12-month net 103,965.60). Ruiru is given its own older tariff C-117 (no tier), so its October figures stand. The checker asserts cheapest < deadline and checks every component. Updated: manifest; main document §6, §8.3; contracts §4.4 and new E7; models §4.1, EV-T1/T2 and C3 row 6; integration trace E; Q6; mock-up comparator and drawer. |
| **M2** `evidence_class` name collision | **Fixed** | The new axis is now `money_class`. Main document §5 now states that 0042:50 is a column named `evidence_class`, used as a source basis, and gives its readers. Also updated: §3.3(b), §4, §13, contracts §6.2, models, the matrix row, the manifest's R2 wording and new ruling A11. "Evidence class" appears nowhere on screen. |
| **M3** Budget switch mixed two assumptions; "or/and" wording | **Fixed** | The mock-up has a separate letter-of-intent control. All four cases show both inverter paths side by side, with the line "More budget never lowers the result". The checker enumerates the four cases by brute force: 6,096 / 2,556 / 6,096 / 3,546 at spend 6,430. The wording is "and" everywhere: main document §2.2 and §7.3, integration line 299, models §7.3. The manifest now states why the claim path loses the huller: restore on 28 Nov, connection needs 5 working days, lapse on 30 Nov. |
| **M4** Measured build cost absent | **Owner decision** | Q10 now records Deliverable 7 as "met except measurement". The options are to authorise one re-benchmark on an allowed `*_test` or `_audit` database, or to accept the gap. The cost plan's status line and the "could not be completed" table say the same. |
| **L1** Internal vocabulary on client screens | **Fixed** | The method and meter-check sentences are rewritten in plain language. "fixture" and "manifest" are removed from client text. The audit's forbidden list is extended and now also scans evidence drawers. |
| **L2** Coverage only for Lakeside | **Fixed** | Harvest coverage is 97.8% (Thika maintenance 80 estimated). Metro coverage is 99.28% (Kasarani maintenance 300 estimated). The checker verifies both. All three operators render coverage. |
| **L3** "[test-confirmed by checker]" overstated | **Fixed** | Relabelled "[derived, arithmetic checked]". The checker now covers the option economics (STOPSOC, huller, welding, billing, MWEA-AGG, KIRI repair and replace, EMB), the inverter residuals and allocation optimality. |
| **L4** Stale cross-references | **Fixed** | The C3 rows cite OR-ENT-2, OR-ENT-3, OR-ALLOC-1 and OR-VER-1. The link count is updated to 335 (after L6). |
| **L5** Kasarani stopgap basis ambiguous | **Fixed** | The manifest, main document, contracts and mock-up now say: 90 in total for the 3 nights to the 9 Nov restore, against about 240 of penalties and 2 broken departures if we wait. |
| **L6** X8 missing | **Fixed** | X8 rows link O2, P1 and A3 to S6 and S8. X8 is also tagged on crew-dependent levers (MG-L3, MG-L6, MG-L10, CC-L5, CC-L6, CC-L7, CC-L9, EV-L3, EV-L9). |
| **L7** Mock-up details | **Fixed** | Every do-nothing row has a reason. The Mto inverter "do nothing" path shows "$0 now; cover lost after 27 Nov 2026". Checklist B9 now says the budget switch is Lakeside only. |
| **L8** Replay figures read as results | **Fixed** | Main document §2.1 marks them at first use as design values that the slice 3 adapter must reproduce. The mock-up labels 210 L, 20 L and 68 L "Design value: to be reproduced from your data". |
| **L9** v72 characterisation thin | **Fixed** | Main document §9 names v72 as the v7.2 design foundation (tokens, Inter, light and dark) that UQ-FI builds on, says vNEXT has not adopted it yet, and refers to Q4. |
| **L10** Mixed EV cost bases | **Fixed** | Maintenance is now included at every depot (Embakasi 600, Ruiru 500). Plan is 38,520.80, actual 41,705.12, 32.03 per departure; the variance is unchanged at −3,184.32. |
| **L11** Oracle shipped in the bundle | **Fixed** | `tools/gen_fixtures.py` strips `oracle:`, and the bundle contains no oracle ids. Recorded as ruling A12. No owner decision is needed. |
| Residual risks 1–3 | **Recorded** | RR1 (replay calibration on clipped days) and RR2 (protected-seam port change) are now in slice 3 of the phase plan. RR3 (two demo estates side by side) is an owner decision before any client demo. All three are in `design-questions-and-decisions.md`. |

None of the findings is disputed.

## Author response (rev 3)

**AssetOps Architect (Claude) · 16 Nov 2026 · on top of `d30ef6af4`, nothing committed, `REVIEW.md` unchanged.**

**Checks after the fixes:**
- `check_manifest.py`: **127 passed, 0 failed**. One check was added for N3 (cost per kWh).
- The mock-up was rebuilt: `fixtures.js` regenerated with no oracle ids, then `node build.mjs`.
- The audit now runs through the portable `tools/run-audit.sh --shots`:
  - 146/146 routes render with no errors.
  - 0 broken links; 0 routes overflow at 390 px.
  - 0 vocabulary hits.
  - Focus 6/6; contrast 14/14.
  - Drawer, role and budget × letter-of-intent checks all pass.
- I spot-checked the edited screens in the browser.

| Finding | Outcome | What changed |
|---|---|---|
| **N1** M2 rename incomplete, and the wrong column cited | **Fixed** | Changed `money_class` in: matrix row 61 (and row 79's "money class"), phase plan slice 2b, A4, integration §App 6, and the contracts §3.1 header. The main document §5, A11, the matrix and the manifest now cite **both** existing source-basis columns: `finding_thread_occurrence.evidence_class` (0042:50, written by `chain/threads.py:205`) and the snapshot column (`0043_chain_snapshots.py:37`, `chain/measures.py:37`, read in `chain/ports.py`, `chain/builder.py` and `chain/outcomes.py`). |
| **N2** October rationale impossible | **Fixed** | The 00:00–05:00 tier is now a contract term effective 1 Nov 2026, so October is billed at 0.12 in all non-peak hours. Updated the manifest tariff and note, the models §4.1, the main document §6, and the mock-up's "what happened" text. |
| **N3** Cheapest bill only because it buys less | **Fixed** | The models §4.1, contracts E7, main document §6, manifest note and walkthrough now say that the cheapest schedule is lowest only because it buys 9,300 kWh less, and that per kWh delivered it costs 0.167 against 0.154. The checker asserts the per-kWh ordering. |
| **N4** Stale 6,928.80 | **Fixed** | `fixture-mapping.md` now reads $8,788.80, with the new verification target. |
| **N5** Metro proof target weaker than the model | **Fixed** | The target is now near-zero peak-price charging, about 62,000 kWh a month at the 00:00–05:00 rate, peak ≤ 400 kW, and every departure met. |
| **N6** Kasarani "wait" path shown as $0 | **Fixed** | The path now reads "$0 now; about $240 in likely penalties and 2 broken departures". |
| **N7** Crew meter ignores the letter-of-intent case | **Disputed, with an explanation added on screen** | 3 of 3 is correct even when the huller is lost. The Mto visit is still needed to fit the restored inverter and check the meters; the huller connection only shared that visit (manifest: Mto inverter + huller + audit combined into one visit). The plan page now shows this explanation under the meter in that case. |
| **N8** Pre-existing UI issues | **Fixed (cheap)** | Thika now reads "Within the occupancy model" when occupancy is at plan. Bridge driver amounts on cost operators use one sign convention (negative = worse), so −$2,604 matches the cost lines. The energy-model formula on client screens is replaced by plain words. |
| **N9** Audit wrapper not reproducible | **Fixed** | `tools/run-audit.sh` now reads `CHROME` and `PW` (required) and the optional `AUDIT_LD_LIBRARY_PATH` / `FONTCONFIG_FILE` from the environment, with clear errors when they are missing. The README documents the setup for any machine. |

Residual risks from the re-review are unchanged and already recorded: screenshots were spot-checked rather than compared in full, and RR1 still governs the replay design values.

## Author response (rev 5)

**Author:** AssetOps Architect (Claude) · 17 Nov 2026 · answering "## Review (rev 4 redesign)" in `REVIEW.md` (verdict REVISE, targeted). Also applied in this round: owner messages 7 and 8 (executive questions never shown on screen).

| Finding | Outcome | What changed |
|---|---|---|
| **H1** Protect not built from factors | **Fixed** | Protect is now a declared structure of measured factors with unit, period, target, class, coverage and Σ composition over sites. Measures: <br>- mini-grid: unserved critical kWh (0); obligation-hours without redundancy (30: Kisiwa 10, Mto 20); asset-days out of service (6); <br>- cold: batches exposed (1); crate-minutes above limit (2,400–3,600); days with backup start unproven (26); <br>- EV: departures missed (0 in October; 2 in November to 6 Nov); nights below required (0; 5); charger-days out of service (26); <br>- money measures (liability 108.00, penalties 240.00) are the same factor as their cost line and are never added twice; values at stake are listed and never summed. <br>Obligation bounds are now derived from these measures: an option fails a bound when its counterfactual pushes a measure above target. <br>Files: manifest `portfolio.protect` blocks; checker (composition and field checks); main doc §2.1, §3.1, §3.1a and §6.2; contracts §2.6, §3.4, §6.6, E11–E12, N18–N19; models §3.11, §4.7; matrix §A1; CSV `protect-measure` rows; phase plan slice 3 tests. Mock-up: Overview Protect card, the Outcomes-by-site Protect section and grid column, and the site Protect panels all show measures against target; EV shows October and November to date separately. |
| **M1** Fuel structure node depends on one option | **Fixed** | The observed split is now necessary running, candidate running (330 L, −412.50, calculated from records) and not explained by the model (120 L, −150.00). Kobo still sums to −562.00. The 210 L and 20 L appear only as option effects on the decision page. Models add a start-up check that no observed node is an option counterfactual. The manifest note now separates the fuel-cost-1 upper bound from the observed 330 L. Applied in the main doc, contracts, models, integration doc, cost plan, CSV, matrix, phase plan and mock-up. |
| **M2** Plan value does not net all spend | **Fixed (relabel and split)** | The figure now reads "modelled 12-month change from the valued options, net of their own one-off costs". Must-do and protective spend is shown beside it as not valued in money, with its effect on Protect measures. <br>- Lakeside: +6,096.00 net of 1,650.00, with 2,230.00 not valued; every switch case satisfies valued costs = spend − 2,230.00. <br>- Harvest: +3,182.40 net of 620.00; 100.00 not valued. <br>- Metro: +95,484.00 net of 1,500.00; 90.00 not valued; the 60,000.00 avoided purchase is listed beside, not added. <br>The fields are in the manifest and checked by the checker. I did not value the must-do in money, because that would need a value-of-lost-load assumption the brief does not give (decision A16). |
| **M3** Slices 4/5 lack cold and EV cases | **Fixed** | Slice 4 now tests the general evaluator on cold and EV inputs: Kirinyaga repair +1,512.40 vs replace −1,988.40; Embakasi's cheapest schedule rejected by the departures bound, and the deadline schedule at 8,082.00 a month against November no-action. Its gate forbids vertical-specific code in the evaluator. Slice 5 adds a Harvest Cold allocation case (720.00, or 450.00 without the aggregator). |
| **L1** Wrong register reason for `#/renewable` | **Fixed** | The register now gives the Kobo headroom banner text. |
| **L2** Record ids in prose | **Fixed** | One rule: product record ids (F-, ACT-, WR-, INC-, PM-) never appear on added or changed screens; they become plain words linked to their page. Client asset and batch tags appear only as "plain name (TAG)". The audit's vocabulary check is widened to these patterns: 0 hits on added and changed screens. Preserved v7.0 screens are exempt and reported separately (140 occurrences of 16 ids). |
| **L3** Small inconsistencies | **Fixed, one partly disputed** | **Node kinds:** one list in contracts and models. **Evidence words:** nine, listed in UI strategy §6.1.4. **Residual label:** "not explained by the model yet" on screen; the attention tag reads "Not explained". **CONTRIBUTIONS citation (disputed in part):** every pack file now cites `outcomes/outcome_map.py:149-180`. The review's proposed `:150-174` would cut off the last two records (EV-3 charging income, lines 173–176; idle-charger potential, lines 178–179). The assignment is at line 149 and the closing parenthesis at 180. |
| Owner messages 7 and 8 | **Applied** | No executive question, role or question stem on any added or changed screen, tab name, section name, drawer or review note. Headings name business content. UI strategy §3.4 and §6.1 state the rule. The §6.2 table column now reads "acceptance test it must pass (never shown on screen)". Walkthroughs mark presenter speech and do not quote the questions as screen text. The audit adds a role and question-stem check: 0 hits. |

**Checks run for this round**

- `python3 check_manifest.py` → **202 checks passed, 0 failed** (up from 167; adds Protect composition, valued and unvalued spend split, plan value totals).
- Mock-up rebuild: `tools/rebase_v70.py`, `tools/gen_fixtures.py` (oracle removed, sha a196bcd30435) and `node build.mjs` all succeeded.
- Full audit (`tools/run-audit.sh --shots`, headless Chromium, file://):
  - 202 of 202 route renders with an h1, 184 screens;
  - 0 console-error routes, 0 bad links, 0 overflow at 390 px;
  - vocabulary 0; identifier rule 0 on added and changed screens; role and question stems 0;
  - filter controls on Portfolio 0; operator selector in the product top bar 0;
  - switch cases 8 of 8; drawer pass; focus 7 of 7; contrast spot checks 36 of 36; preserved screens identical 65 of 65; oracle not shipped.
- CSV validator: PASS, 429 rows. Coverage: objectives 15/15, levers 28/28, classes 9/9, capabilities 30/30, options 38/38, Protect measures 14/14.

**Not changed:**
- The preserved v7.0 Ruiru pages still show a smaller public depot than the manifest's Ruiru (owner checklist item 11).
- Decision pages show the per-option bound checks, not a per-option Protect value table, because the manifest holds no per-option Protect values; the bounds now name the measure they protect.

## Author response (rev 6)

**Author:** AssetOps Architect (Claude), 17 Nov 2026. This answers "## Re-review (rev 5)" (L1–L6) and its addendum (OE-1 to OE-6, LY-1 to LY-5) in `REVIEW.md`. The owner's feedback file remains the governing direction.

### Blocking findings (Medium)

**OE-1: Portfolio tab frame not judged on merit. Fixed.**

Main §6.1 item 2 and §6.2 now judge each tab against the loop, and the tabs are reordered to follow it: Observe, then Evaluate/Choose, then Prove.

| New position | Tab | Decision |
|---|---|---|
| 1 | Overview | Keep. Results and choices lead (C1 D6). |
| 2 | Outcomes by site | Keep the name; move to 2nd (Observe). |
| 3 | Demand and capacity | **Renamed** from *Opportunity*: in the loop every option is an opportunity, and this tab holds latent demand factors and capacity without a customer. |
| 4 | Act first | Keep the name, because it says where action is decided; move to 4th (Choose). |
| 5 | What changed | Keep (Prove). |
| 6 | Scope & coverage | Keep, last (evidence state, then pilot). |

- The old `#/portfolio/opportunity` route redirects to the new tab.
- CHANGE-REGISTER §7a records the reason for each tab.
- Owner decision Q2 now asks for approval of the new order and the rename.

**OE-6: Mock-up no longer disclosed replay design values. Fixed (decision A20).**

Every replay-based figure now carries the label "Design value: the replay has not yet been run on site data":
- Kobo 210 L, 20 L, 61/61 and 4/61 days, $2,916;
- Mto 68 L, $395 a month, $3,540;
- Embakasi 31/31 nights;
- the Mto inverter sensitivity;
- each operator's plan-value drawer and the plan rows on Act first.

Kirinyaga's 80% recovery is labelled as an assumption. The Overview plan figure says "includes design values not yet run on site data". The audit checks that the labels are present, and phase-plan release test R13 fails if they are missing.

**LY-1: O2 and A4 had no declared measure. Fixed (decision A18).**

O2 is now declared for each vertical as measured factors that compose as Σ numerator / Σ denominator (manifest `operations`; contracts §2.7; models §3.13; checker):

| Vertical | O2 measures |
|---|---|
| Mini-grid | asset availability 98.51% (397 of 403 asset-days); field visits 3; 7,683.33 kWh delivered per visit |
| Cold | cooling availability 99.997%; 22,820 crate-days without excursion |
| EV | charger energy utilisation 41.50%; 50.08 departures per charger in service |

- A4 is declared as the evidence pack: a reading of A1–A3 with lineage, built in slice 9. It adds no new measure.
- Attribution rules A1–A5 are renamed AR1–AR5 everywhere, so they no longer clash with the Assure objectives.
- The CSV gains a `declared_measure` column and no longer claims coverage by enumeration. The validator now reports 14 of 15 objectives with a declared measure; the 15th is A4, which is a reading.

### Lows from the addendum

| Finding | Outcome |
|---|---|
| **OE-2** | **Fixed.** The §6.2 column is now a trace showing how the executive concerns are met. Each concern spans several sections; no tab is assigned to a role. These are acceptance tests and never appear on screen. |
| **OE-4** | **Fixed.** The Overview's first fold is the headline, four figures with one-line notes, and "The plan's first three moves" with "Open the plan". The value chain is behind a disclosure, closed at phone width. |
| **LY-2** | **Fixed.** The cold realisation stages are declared: occupied → chargeable → invoiced → received, with a storage-ledger-to-invoice observer (models §3.12) and negative test N20. October has no discrepancy, so CC-L8 has no demo option; this is stated in the docs, the CSV and on screen. |
| **LY-3** | **Fixed.** MG-L2 has a load-shift model line, deferred under the brief's tariff boundary. EV-L7 battery health is deferred under the brief's "without validated battery data" boundary; charger reliability is carried by fault consequence. MG-C4 gains a fuel price-discrepancy check (P1-P). See models §4.9. |
| **LY-4** | **Fixed.** Act first shows the plan's downside beside its value: Lakeside +2,556.00 (other sensitivities +5,466.00 and +5,346.00), Harvest +1,512.40, Metro 0.00. The values are in the manifest, and the checker asserts downside ≤ value. |
| **LY-5** | **Fixed.** P4/A5 measures are declared by contract and period (manifest `rights`, contracts §5.5) and shown on What changed: complete contract evidence 1 of 3, 1 of 1 and 2 of 2; open deadlines; remedy days; residual expense; credits. The EV-C5 position is in main §2.4: different defensible allocations are switch settings a person chooses over one evidence base, never role views. |

### Lows from the re-review

| Finding | Outcome |
|---|---|
| **L1** | **Fixed.** There is one plan-value drawer per operator, generated from `modelled_12m_change` and titled "Modelled 12-month change from the valued options". It shows the valued options, the must-do and protective spend not valued in money, the downside and the design-value note. |
| **L2** | **Fixed (decision A19).** Must-do means that taking no action fails a hard bound. That applies to the Kisiwa repair, the Thika stopgap and the Kasarani stopgap (`must_do: true` in the manifest, with the reason). Protective covers only the Kobo battery evidence. The measures are named "days with backup start unproven" and "departures missed". |
| **L3** | **Fixed.** Ruiru's +19.68 now reads "not attributed: the plan is declared only as a bill total" everywhere, never "not explained by the model". The audit checks this. |
| **L4** | **Fixed.** Both halves of the dispatch split (necessary and candidate running) are now "Calculated from records" (DERIVED): one rule on metered generator energy with a declared consumption rate. This is updated in the manifest, the main doc and the models doc (§3.4 is now BOUNDED, not MODELLED). |
| **L5** | **Fixed (decision A17).** Customer-hours interrupted is added as a Protect measure (0). Asset value at risk is declared but shown as "not available yet", deferred under the brief's own "expected loss only with defensible likelihood" rule. Exposure measures are listed, never summed (manifest `LISTED`, CSV, contracts). |
| **L6** | **Fixed.** `loop-protect.js` was committed in 146667cfc. The dead `GEN_POLICY_RUNNING_*` keys are removed from `loop-core.js`. |

**Also corrected:** Ruiru's charger utilisation in the manifest was 0.31 and did not reconcile with the stated chargers, power and window. It is now 0.34 (1,960 ÷ 5,760). The Harvest cooling-minutes field is split into per-room and portfolio minutes.

**OE-3 and OE-5:** rejected by the reviewer; no action.

### Checks run before replying

- `python3 check_manifest.py`: **217 checks passed, 0 failed**. New checks cover O2 composition, availability agreeing with the Protect asset-days, and downside ≤ value.
- CSV validator: **PASS**.
  - 453 rows and 18 columns.
  - Objectives 15/15, levers 28/28, lever classes 9/9, capabilities 30/30, options 38/38, Protect measures 16/16.
  - 14 of 15 objectives have a declared measure; A4 is a reading.
- Mock-up rebuild: `tools/rebase_v70.py`, `tools/gen_fixtures.py` (oracle removed, sha d31a2c9e18bb) and `node build.mjs` all succeeded.
- Full audit (`tools/run-audit.sh --shots`):

| Check | Result |
|---|---|
| Routes rendering an h1 | 202 of 202 (184 screens) |
| Console-error routes | 0 |
| Bad links | 0 |
| Overflow at 390 px | 0 |
| Vocabulary hits | 0 |
| Identifier rule on added and changed screens | 0 |
| Role and question hits | 0 |
| Filter controls on the Portfolio | 0 |
| Operator selector in the product top bar | 0 |
| Tab order | pass |
| Old route redirect | pass |
| Design-value labels | pass |
| Ruiru wording | pass |
| Switch cases, including downside and must-do wording | 8 of 8 |
| Evidence drawer | pass |
| Focus | 7 of 7 |
| Contrast | 38 of 38 |
| Preserved screens identical to v7.0 | 65 of 65 |
| Oracle shipped in the bundle | no |

### Not changed

- The preserved v7.0 Ruiru pages show a smaller depot than the manifest's Ruiru. This needs the owner's decision (checklist item 11).
- Decision pages show each option's bound checks, naming the Protect measure each one protects, but not a per-option table of Protect values; the manifest holds no such values.
- Two O2 measures (kWh per field visit, departures per charger) are given only at portfolio level.

## Author response (rev 7)

**Author:** AssetOps Architect (Claude), 17 Nov 2026. This answers "## Re-review (rev 6)" in `REVIEW.md` (verdict REVISE, targeted).

### N-M1: EV utilisation denominator ignored the import limit. Fixed.

I took the reviewer's first option: make the measure use the structure's own `deliverable_kwh_per_night` stage, so the O2 measure and the capacity bounds share one definition.
- The measure is renamed `deliverable_energy_used`. Its denominator is min(chargers in service × kW, import limit) × window.
- The manifest records the binding limit per depot. The checker recomputes each denominator and asserts that Ruiru's 3,200 kWh equals RUI-ABSORB6's deliverable figure.

| Depot | Binding limit | kWh used / deliverable a night | Share |
|---|---|---|---|
| Embakasi | import limit, 500 kW | 2,800 / 6,000 | 46.67% |
| Kasarani | chargers, 200 kW | 1,200 / 1,400 | 85.71% |
| Ruiru | import limit, 400 kW | 1,960 / 3,200 | 61.25% |
| Portfolio | Σ/Σ | 5,960 / 10,600 | 56.23% |

- Contracts l.181 now says that Ruiru's headroom is 1,240 kWh, room for 8.9 buses. That is why +6 buses passes and +10 fails.
- Nameplate charger-hour use (Ruiru 34%) stays on screen only as a labelled secondary figure, shown beside "61% of deliverable energy a night (the 400 kW import limit binds)".
- Updated in: manifest, checker, contracts §2.7, models §3.13 (OP-T2), the CSV measure ids, the matrix, the phase plan, the main doc, and the mock-up's Outcomes by site, Grow card, Demand and capacity tab and Ruiru decision page.

### N-M2: replay figures still unlabelled in several places. Fixed, and the check is widened.

- **The tag.** One tagging rule in the mock-up (`tagReplay`) runs after every render and every drawer opening. Any element that holds a replay figure, or a value computed from one, gets "Design value: the replay has not yet been run on site data". This now covers:
  - the Overview Optimize card and the "Sites that look alike" panel;
  - the Act first path cards and the four-case switch table;
  - every drawer.
- **The Mto inverter page.** Its banner now names both the Kobo stop-setting replay and the huller replay.
- **The audit.** It now scans every route and every drawer for:
  - replay figures: 210 L, 20 L avoided, 61 of 61 and 4 of 61 days, 68 L, and 31 of 31 nights;
  - money values: $2,916, $395, $3,540, $6,096, $2,556, $3,546, $5,670 and $5,346.

  It fails on any figure whose container is unlabelled. Result: 53 occurrences across 202 routes and 734 drawers, **0 unlabelled**.
- **The rules.** Decision A20 and release test R13 are widened to "every occurrence, including values computed from replay figures (plan values, switch cases, sensitivities, downsides), on any card, table or drawer".
- **Harvest.** Its plan value rests on no replay, so its notes use the assumption wording instead: "includes an assumed recovery share (80%) at Kirinyaga".

### Lows

| Finding | Outcome |
|---|---|
| **N-L1** | **Fixed.** Contracts §5 reads "R3a, P4, A5, S12". |
| **N-L2** | **Fixed.** The diesel −20% sensitivity now applies to every valued option that buys diesel: stop setting 2,286 + huller 3,744 ((495 − 68 × 1.00 − 15) × 12 − 1,200) − inverter claim 360 = **+5,670.00**. The manifest note carries the working, the checker recomputes it, and the main doc, models §6.4, phase plan and screen are updated. The downside (+2,556) is unchanged. |
| **N-L3** | **Fixed.** The path cards are retitled "Modelled 12-month change from the valued options". The duplicated "Net of …" sentence is removed from the Lakeside drawer. The Harvest drawer uses the assumption wording, and its source line no longer says "forward replay". |
| **N-L4** | **Fixed.** The measure is renamed "departures met per installed charger" (50.08). Its basis note gives the per-charger-day-in-service figure (51.75). Asset availability now counts a declared asset list per site, with the counting rule stated ("every power-conversion or generation unit listed in the site's physical block": Kobo 5, Kisiwa 4, Mto 5). Lakeside becomes 428 / 434 = **98.62%**, and the checker verifies it. |
| **N-L5** | Already handled by the coordinator in the rev 6 commit. |

### Checks run before replying

| Check | Result |
|---|---|
| `python3 check_manifest.py` | **222 checks passed, 0 failed** (new: import-limited deliverable energy per depot, the Ruiru deliverable figure against RUI-ABSORB6, and the diesel −20% whole-plan sensitivity) |
| CSV validator | **PASS** (453 rows; measure ids match the manifest) |
| Mock-up rebuild: `rebase_v70.py`, `gen_fixtures.py` (oracle removed, sha 00d50e72bfc1), `node build.mjs` | succeeded |
| Full audit: routes rendering an h1 | 202 / 202 (184 screens) |
| Full audit: console errors, bad links, overflow at 390 px | 0 / 0 / 0 |
| Full audit: vocabulary hits; identifiers on added and changed screens; role and question hits | 0 / 0 / 0 |
| Full audit: filter controls; operator selector in the top bar | 0 / 0 |
| Full audit: design-value scan | 53 occurrences, 734 drawers, 0 unlabelled |
| Full audit: tab order, old route, rev 7 EV measure, Ruiru nameplate wording, Ruiru not-attributed wording | pass |
| Full audit: switch cases | 8 / 8 |
| Full audit: evidence drawer | pass |
| Full audit: focus | 7 / 7 |
| Full audit: contrast | 38 / 38 |
| Full audit: preserved screens identical to v7.0 | 65 / 65 |
| Full audit: oracle in the bundle | none |

**Limits of the design-value scan.** It covers each page in its default switch state; other switch states use the same tagging rule and are captured in the screenshots. It counts "20 L" only when phrased as litres avoided, because the observed 20 L figures (Kisiwa residual, Mto evening running) are not replay figures.

## Author response (rev 8)

**Author:** AssetOps Architect (Claude), 17 Nov 2026. This answers "## Re-review (rev 7)", including its coordinator points. I accept the reviewer's CP-4 judgement: this is the last author round, and anything still open is an owner decision in `design-questions-and-decisions.md`. That file now states this at the top.

### Medium findings

**CP-1: alternatives to six parallel tabs were never weighed. Fixed in the documents; the choice goes to the owner.**
- Main §6.2 now weighs three frames against the loop, the four executive concerns and the demo flow, with arguments for and against each:
  - (a) six parallel tabs;
  - (b) one sequential Portfolio page;
  - (c) a staged Overview that reads the loop in sequence, with the other tabs as drill-downs in loop order.
- **Chosen: (c).** The first fold already reads Observe → Choose. Each tab deepens one stage and keeps a stable address, and it works at phone width.
- **Why not (b):** the loop becomes literal, but the page would be several times the Overview's length (about 2,000 px on desktop and 4,300 px on a phone for the Overview alone), and deep views would lose stable addresses.
- Q2 now offers the owner real alternatives: (a) old tabs, (b) staged Overview with tabs in loop order (recommended), (c) one sequential page. As the reviewer suggested, no mock-up of (c) is built unless the owner picks it.

**CP-2: per-option Protect effects were neither declared nor shown. Fixed (decision A22).**
- The manifest now declares `protect_effects` per decision, each with horizon, measure, values per option and evidence class:

| Decision | Measure | No action | Recommended | Other |
|---|---|---|---|---|
| Kisiwa | hours without a backup generator in November | 150 | repair 15 | replace 105 |
| Kobo stop setting | days below 35% at 5 am (design value) | 0 | 0 | reserve 4 |
| Kobo battery evidence | assets with complete contract evidence | 1 of 3 | 2 of 3 | — |
| Thika | nights with stock and no backup cover | 2 | 0 | self-repair 0, but the $710 cover is lost |
| Kasarani | departures missed | 2 (penalties $240) | 0 ($0) | — |
| Embakasi | departures missed (design value) | 0 | 0 | cheapest schedule 93 |

- The checker reconciles these with the option rows:
  - penalties = missed departures × $120, and matches the option's expected penalties;
  - Kisiwa hours = evenings × 5 h;
  - Embakasi 93 = 3 short × 31 nights;
  - Kobo reserve 4 = its replay days.
- They appear in models §4.7, main §2.3 and §7.1.
- On screen:
  - each of the six decision pages has a "Protect measures under each option" section;
  - the must-do and protective spend line on Act first names the measure each item moves, for example "Kisiwa repair: … 150 → 15".
- The $2,230 Lakeside spend is now justified by computed Protect effects, not prose.
- **Limit:** the other eight decisions have no Protect effect in the file. Their options leave Protect measures unchanged, and they keep their bound checks.

**CP-3: calibration covered Kobo only, came late, and had no client-exposure rule. Fixed (decision A21; owner decision Q13).**
- The single Kobo spike is now a **calibration lane** that runs first, read-only and in parallel with slice 1. It depends on no slice.
- It has three spikes, each with its own exit and replacing only its own figures:

| Spike | Replay | Figures it replaces |
|---|---|---|
| K | Kobo forward replay | 210 L, 20 L, 61/61 and 4/61 days, $2,916, $2,286, $2,166, $250.50 |
| M | Mto headroom replay | 68 L, 3 days, $395, $3,540 |
| E | Embakasi schedule replay | 31/31 nights, 2,900 kWh, 93 departures, $8,082, $95,484 |

- Plan values built from these figures lose the label only when every spike they depend on has passed.
- **Client-exposure rule:** no client sees a replay-derived figure unless its spike has passed, or it carries the label and the presenter says so aloud. Whether "labelled and said" is enough for early prospect demos is owner decision Q13.
- Updated in: the phase-plan graph, the slice-order table, the readiness and sizing rows, R13 (now tied to K, M or E), main §9 (new row "0 Calibration lane") and RR1.

### Low findings

| Finding | Outcome |
|---|---|
| **CP-5** | **Fixed.** An "Owner review in 30 minutes" section now opens `owner-inspection-checklist.md`, and the main document points to it at the top. It covers the five mechanics in five lines, one Lakeside walk, one cross-vertical contrast (Metro Ruiru and Kasarani, Harvest Thika), and the owner decisions with the one screen to open for each. The checklist's stale row 13 is corrected. The rev labels in the main document and the decisions file now say rev 8, and the pack index says the review history runs rev 1–7. |
| **R7-L1** | **Fixed.** `tools/gen_fixtures.py` now derives the replay-dependent set from the manifest: options carrying `forward_replay`, `replay` or `design_value`, their economics and sensitivities, and the plan values, switch cases, downsides and Protect effects built from them. The tagger uses only that set. The audit derives its own set separately (`tools/replay_values.py` reads the YAML directly), so it can find anything the tagger misses. Result: 25 figures, the same in both sets; 94 occurrences across all routes and 734 drawers; **0 unlabelled**. The set now includes $250.50, $2,286, $2,166, $8,082 and $13,356. **Stated limits:** amounts under $50 and bare integers under 10 are not scanned, because they collide with unrelated prices. "20 L" and "93" are matched only in their replay phrasing, because the same numbers appear as observed figures elsewhere. |
| **R7-L2** | **Fixed.** Contracts: 428 / 434. `gen_docs.cjs`: +$5,670. CSV T0438: "share of deliverable energy a night (import-limited)". Headers: see CP-5. |

### Checks run before replying

| Check | Result |
|---|---|
| `python3 check_manifest.py` | **236 checks passed, 0 failed** (new: Protect effects reconciled with the option rows) |
| CSV validator | **PASS** |
| Mock-up rebuild (`rebase_v70.py`, `gen_fixtures.py`, `node build.mjs`) | succeeded; oracle removed, 25 replay patterns derived, sha 41b935209449 |
| Full audit: routes rendering an h1 | 202 / 202 |
| Full audit: console errors, bad links, overflow at 390 px | 0 / 0 / 0 |
| Full audit: vocabulary hits, identifiers on added and changed screens | 0 / 0 |
| Full audit: role and question hits, filter controls, operator selector in the top bar | 0 / 0 / 0 |
| Full audit: independent design-value scan | 0 unlabelled of 94 |
| Full audit: tab order, EV measure | pass |
| Full audit: switch cases | 8 / 8 |
| Full audit: drawer, focus, contrast | pass, 7 / 7, 38 / 38 |
| Full audit: preserved screens identical to v7.0 | 65 / 65 |
| Full audit: oracle shipped | no |

**Now owner decisions (no further author round):** Q1–Q13, including the new Q2 frame choice and Q13 client exposure, and checklist item 11 (Ruiru's preserved deep views).
