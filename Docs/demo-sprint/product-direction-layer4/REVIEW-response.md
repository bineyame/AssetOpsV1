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

## Author response (rev 9)

**Author:** AssetOps Architect (Claude), 17 Nov 2026. This answers "## Re-review (rev 8)" and the owner's ninth message ("the structural aspect of mechanics are still very important even in the document illustration").

### Owner, ninth message: the illustration is now evaluated through the structure, not hand-written

I accept the coordinator's point. Per-option Protect effects, option values and plan values were written by hand into the demo data, and the R8-M1 and R8-M2 errors are symptoms of that.

**What the manifest now declares (inputs only)**
- `structures:` holds the outcome structure of each vertical as node expressions over named factors (Define).
- `option_factor_changes:` holds how each valued option changes leaf factors, for how many months, and its one-off cost, with sensitivities as factor overrides.
- `plans:` holds the allocator inputs: budget, fixed must-do and protective items, candidate options, exclusivity, requirements and switches.

**What the new `evaluate_structure.py` derives from those inputs**
- **Observe:** every site's actual and plan outcome, bottom-up from its leaf factors.
- **Evaluate:**
  - every valued option, by re-running the same structure with its factor changes against no action, together with its sensitivities;
  - four Protect effects (Kisiwa, Mto inverter, Thika, Kasarani), from the option rows' restore dates, counted from `as_of`.
- **Choose:** every plan, switch case and downside, by enumerating subsets.

**Where the results go**
- The script writes `derived-values.json`, with each figure's formula.
- The mock-up's fixtures take every computed figure from that file.
- Drawers show the evaluator's formula and name the structure.

**How the check works**
- `check_manifest.py` asserts that every figure stated in the manifest and documents equals the evaluated one. It also asserts that every date-derived Protect effect is recomputed from its dates.
- A figure that does not follow from the structure now fails the check before it can reach a screen.
- No on-screen figure changed: 936 page and drawer views were compared before and after.

**Still inputs, by design:** Kobo dawn days and Embakasi's 93 missed departures are replay design values (spikes K and E). Kobo battery evidence is a record count.

**Where this is recorded:** main §10 and decision A23.

### Findings

| Finding | Outcome |
|---|---|
| **R8-M1** Kisiwa effect used a restore date before `as_of` | **Fixed.** `KIS-REPAIR` now carries `crew_visit` 8 Nov and `restore_date` 9 Nov. `KIS-REPLACE` carries `lead_time_days` 21 and `restore_date` 27 Nov. Evenings are counted from the decision date: 6–30 Nov is 25 evenings. Result: no action 125 h, repair 15 h, replace 105 h. The 25 h observed on 1–5 Nov appears separately, under every option, as observed. The evaluator derives these figures and the checker re-derives them from the dates. Act first reads "6–30 Nov: 125 → 15". |
| **R8-M2** Mto inverter had no Protect effect | **Fixed.** A new effect is declared on `obligation_hours_without_redundancy`, using the restore dates in the option rows and counted from 6 Nov: claim and wait 110 h (restored 28 Nov), buy now 30 h (12 Nov), no action 125 h. Local repair is shown as not evaluated, with the reason. The 1–5 Nov 25 h is shown as observed. **On the reviewer's figures (150 / 135 / 55):** I used the same counting rule as R8-M1, from the decision date rather than from 1 Nov. The difference between the two paths is the same either way: 80 h. The effect appears on `#/decision/mto-inverter` and beside the claim-versus-buy switch on Act first. CHANGE-REGISTER now says seven decisions have Protect effects. |
| **R8-L1** Two effects used measures outside the declared structure | **Fixed.** Thika's effect is now on a declared Protect measure, `nights_without_backup_cover` (Harvest, October: 26). The CSV has a row for it. Models §4.7 states why the Kobo stop setting is shown on its bound's own quantity: unserved critical kWh is 0 under every option, and the bound count is what tells the options apart. |
| **R8-L2** Spike lists and derived set disagreed; 406 kW unlabelled | **Fixed.** The manifest's `calibration_spikes` is now the enumeration. `check_manifest.py` runs `replay_values.py` and asserts that the derived set equals the spikes' scanned figures plus the plan values: 27 figures. 150 kWh, 2,900 kWh and 406 kW are added; $495 and Embakasi's no-action "0" are no longer labelled; the 406 kW sentence is tagged. The phase-plan spike table points to the enumeration. |
| **R8-L3** Label residues | **Fixed.** Frame letters are now the same in §6.2 and Q2: (a) six tabs, (b) one sequential page, (c) staged Overview, which is recommended. Q13 now follows Q12, and decisions A1–A23 are in numeric order. RR1 now points to calibration spike K (A21). Revision headers updated. The Act-first battery line now reads "assets with complete warranty evidence 1 of 3 → 2 of 3". The 30-minute path has a closing line pointing to the remaining owner decisions (CP-5 note). |

### Checks run before replying

- `python3 evaluate_structure.py`: 9 site outcomes, 12 options, 4 Protect effects, 3 plans.
- `python3 check_manifest.py`: **325 checks passed, 0 failed**. New checks:
  - evaluated figures equal stated figures;
  - date-derived Protect effects are recomputed from their dates;
  - the spike enumeration equals the derived replay set.
- CSV validator: **PASS** (454 rows; includes the new Protect measure).
- Mock-up rebuild: evaluator, `rebase_v70.py`, `gen_fixtures.py` (27 replay patterns; private oracle removed) and `node build.mjs`.
- Full audit:

| Check | Result |
|---|---|
| Routes that render | 202 / 202 |
| Console errors / bad links / overflow at 390 px | 0 / 0 / 0 |
| Vocabulary hits / identifiers / role or question wording | 0 / 0 / 0 |
| Independent design-value scan | 27-figure set, same as the tagger's; 102 occurrences; 0 unlabelled |
| Switch cases | 8 / 8 |
| Drawer / focus / contrast | pass / 7 of 7 / 38 of 38 |
| Preserved screens identical to v7.0 | 65 / 65 |
| Private oracle in the bundle | no |

The design-value scan and tagger now skip the preserved v7.0 pages. The scan reports 2 unrelated "150 kWh" matches there as exempt; tagging them would have broken those screens' identity with v7.0.

## Author response (rev 10)

**Author:** AssetOps Architect (Claude), 17 Nov 2026. This answers "## Re-review (rev 9)" (R9-M1 to M4, R9-L1 to L3), the owner's tenth message (option A, points 1, 3 and 4) and the owner's eleventh message (the coordinator's full comment, points 1 to 4). The owner's ninth message governs: the structure must produce the figures, even in the illustration.

### What changed in the mechanism

`evaluate_structure.py` is rebuilt so that the illustration is produced by the structure all the way down. The manifest now holds only inputs:

| Manifest block | What it holds |
|---|---|
| `structures:` | Every layer of each vertical's structure, as node expressions. **Mini-grid:** delivered → metered → billed → revenue → collected; diesel = necessary + candidate + unexplained + extra running; cost to serve; contribution; obligation-hours. **Cold:** revenue and receipts; normalised energy model × model factor + excess; cost to serve; contribution; nights without backup cover. **EV:** deliverable energy a night = min(chargers × kW, import limit) × window; supplied energy; required energy; buses short; departures missed and met; energy cost; penalties; cost per departure met. |
| `factor_map:` | Turns each site's source records into leaf factors, using record fields, tenant prices, site tariff and physical data, the energy model and incident data. The evaluator contains no numbers of its own. |
| `evaluation:` | Each of 24 options, with: its parameters, taken from its record or declared with provenance (spike design value, assumption, quote); its factor changes as expressions over those parameters; its reference; its cost lines, each naming the right that could bear it; and restore dates derived from what drives them. |
| `plans:` | Allocator inputs. |

The evaluator observes all nine sites (actual and plan) bottom-up, composes the portfolio (Σ, and Σ/Σ for ratios), evaluates every option through the same structure against its reference, applies hard bounds, decides who pays from rights, and chooses every plan, switch case and downside.

`check_manifest.py` asserts every stated figure in the manifest against the evaluation, at every layer:
- value-chain stages, physical splits, cost lines and outcomes for every site and plan;
- portfolio composition;
- option values, operator costs and restore dates;
- Protect effects;
- plans, switch cases, sensitivities and downsides;
- O2 measures.

It also checks the documents (R9-M4).

### Outcomes, R9 findings

| Finding | Outcome |
|---|---|
| **R9-M1** Cold and EV observation hard-coded prices and constants | **Fixed.** All three verticals observe through the declared `factor_map`; the evaluator holds no numeric literals. Cold reads `prices` and the `energy_model` (base 1,550, k 0.25, now declared). EV reads each site's `tariff.prices` (peak, off-peak, night from 1 Nov, night in October, demand) and `physical` (chargers, kW, import limit, window hours, buses, kWh per bus). Embakasi's October split by interval (15,500 / 23,560 kWh) is now a recorded leaf. Kasarani's plan is now decomposed (37,200 kWh at 0.15). Ruiru's plan is stated only as a bill total, so the evaluator labels it "not decomposed: stated total" and does not count it as evaluated. Perturbations P4 and P7 now move every dependent figure and the checker catches them (below). |
| **R9-M2** Options used a second hand-entered copy of base factors and hand-worked deltas | **Fixed.** `base_site_factors` is deleted; each option starts from the site's observed factors. Deltas are now expressions over the option's own parameters: huller `load_kw × hours × days`; welding kWh × the site's consumption rate; Kirinyaga repair `excess × (1 − recovery_share)` (recovery share read from the row); Mwea `crates × days`; Embakasi schedules `max_kw × hours × nights`. Kirinyaga replacement now acts on its own leaf: excess → 0 and model factor 0.95 (a declared assumption). The excess therefore never goes negative, and the value is unchanged (−1,988.40). P6 (base drifting from October) can no longer happen. |
| **R9-M3** Mto inverter money entered as one-off results, contradicting the restore horizon | **Fixed (decision A24).** Reduced capacity now runs through the structure as extra running (5 L a day at half inverter capacity, a spike-M design value) over each path's own derived restore horizon. Cost lines carry who bears them through the right. The figures now differ, and they are the honest ones: claim and wait **367.50** = 230.00 one-off (the 2,600 unit is borne by the supplier) + 137.50 fuel (22 days); buy now **2,947.50** = 2,910.00 + 37.50 fuel (6 days). Every plan figure follows. No chosen plan changes. |
| **R9-M4** Documents unchecked | **Fixed.** `check_manifest.py` now has a document pass. **(1)** It checks that a list of superseded figures appears in no pack document; review history and the mock-up's revision log are excepted. **(2)** It checks that every money or quantity figure in main §2–§10 is either an evaluated value or a declared input. Both currently pass. **Drift corrected:** §7.2 now names Thika's measure correctly, and §10 says exactly what is checked. The manifest's Protect `basis` strings no longer carry hand-written numbers. Figures typed into the mock-up's strings (`loop-portfolio.js`) now come from evaluated nodes. |
| **R9-L1** Rough edges in the Protect rule | **Fixed.** Protect measures are now structure nodes, not a date rule. The horizon end comes from `evaluation.horizon_end`. The spare bus is a factor (`physical.spare_buses`). Cover options use cover-from-decision, not a restore sentinel. Units are correct per measure. The `minus` adjustment is removed. |
| **R9-L2** Restore dates not tied to their drivers | **Fixed.** Every restore date is derived from its drivers: Kisiwa repair = crew visit + 1 repair day; replacement = decision + the row's 21 days; Mto claim = decision + warranty lead time + 1 installation day; buy now = decision + 5-day local supply + 1 day; Kasarani = notice (2 Nov) + 5 business days (the SLA term); Thika = the supplier's scheduled remedy. The checker asserts that each stated date equals the derived one. P1 and P8 (below) now move the date and the Protect hours, and both are caught. |
| **R9-L3** Stale header claims | **Fixed.** Headers no longer quote a check count; they name the evaluator and checker. Manifest revision labels are updated. |

### Outcomes, owner's tenth message (points 1, 3, 4) and eleventh message (points 1 to 4)

| Point | Outcome |
|---|---|
| **1. The evaluated structure stops at the money layer** | **Fixed.** Value chain, physical split, cost, outcome and Protect nodes are all evaluated and checked against the stated figures (e.g. Mto 6,000 → 5,580 → 5,400 → 2,160 → collected 1,890; Kobo diesel 730 + 330 + 120 = 1,180). O2 measures and portfolio composition are evaluated too. Protect effects are now node values of the counterfactual structure; the date rule is gone. |
| **2. The causal step is hand-entered, and some deltas are unflagged** (eleventh message) | **Fixed where a structure can produce it; flagged where only a replay can.** Every delta is now an expression over named parameters, and every non-record parameter declares its provenance. The remaining causal inputs are replay outputs: 210 L and 20 L avoided, 150 kWh throughput, 68 L, and 5 L a day at half capacity (spikes K and M; Embakasi's feasibility, spike E). These are flagged design values with a calibration spike as their exit. Welding's 217.8 L and Kirinyaga's −1,171.5 kWh are now computed. One figure has no model: Kisiwa's 60 kWh battery saving (150 L a month), on a deferred option in no plan. It is flagged as an assumption and recorded as **owner decision Q14** rather than entered silently. |
| **3. Thika, Kasarani and Ruiru were not evaluated** | **Fixed.** All 24 options across all nine sites run through the structure. **Thika:** nights without backup cover 2 / 0 / 0; self-repair bears the 710 controller. **Kasarani:** chargers in service 3 → supplied energy 1,050 against 1,200 required → 1 bus short a night × 3 nights − 1 spare = 2 departures missed, 240.00 penalties; the cover avoids them for 90.00, so the stopgap is now **valued +150.00** by the structural rule below. **Ruiru:** +6 buses supplied 2,800 within 3,200, 0 missed, cost per departure met 26.14; +10 buses 2 short a night, 62 missed, rejected by the bound. |
| **4. Rights sit outside the structure** | **Fixed (A24).** Each cost line names the right that could bear it. The operator's share is 0 when that right is potentially covering or accepted, and 1 otherwise. The difference between the Mto paths is now fully structural: the supplier bears the unit under the claim; the operator buys it under buy-now; and each path pays its own extra fuel up to its own restore date. Kisiwa's expired cover leaves the 1,800 repair with the operator. |

**Two structural rules replace hand classifications.**
- An option is valued in money only when it changes a money node (A16 revised). Kasarani's stopgap is now valued; the Kisiwa repair, the Thika stopgap and the Kobo battery evidence are not.
- An option whose counterfactual raises a hard Protect measure above its reference (departures missed), or that carries a declared spike bound failure, is rejected before valuation. The cheapest Embakasi schedule, the Kobo reserve change and Ruiru +10 therefore show no money value.

### Figures that changed (all evaluator outputs)

| | Before | Now |
|---|---|---|
| Mto claim / buy now (operator cost) | 360 / 2,910 | 367.50 / 2,947.50 |
| Lakeside plan | value 6,096 at spend 3,880 | value **6,088.50** at spend **3,750** (valued 1,520; not valued 2,230) |
| Lakeside, budget 5,000, no LOI extension | 2,556 at spend 2,680 | 2,548.50 at spend 2,550 |
| Lakeside, budget 6,500, no LOI extension | 3,546 | 3,508.50 at spend 6,430 (buy-now wins by 960) |
| Lakeside downside | 2,556 | 2,548.50 |
| Lakeside, diesel −20% | 5,670 | 5,690 |
| Lakeside, 160 L feasible | 5,346 | 5,338.50 |
| Metro plan | 95,484 | **95,634** (stopgap +150) |
| Metro, flat tariff, and downside | 0 | 150 |

Unchanged: Harvest, all site outcomes, all Protect effects and the O2 measures. The documents, mock-up, walkthroughs, fixture mapping, phase plan, matrix and CSV are updated, and the document pass confirms that no superseded figure remains.

### Perturbations re-run (scratch copy; working tree untouched)

| # | Change | What moves now | Checker |
|---|---|---|---|
| P1 | Kisiwa crew visit 8 → 9 Nov | Restore 9 → 10 Nov; repair Protect 15 → 20 h | 2 FAIL (stated date and hours), caught |
| P5 | Mto warranty lead time 21 → 22 days | Claim restore 28 → 29 Nov; claim −367.50 → −373.75 (fuel follows the horizon); plan 6,088.50 → 6,082.25 and every case and downside | 12 FAIL, caught |
| P2 | Kobo diesel price 1.25 → 1.30 | Site outcome and stop-setting value 2,916 → 3,042; plan, cases and downsides | 22 FAIL, caught (in rev 9 the option did not move) |
| P3 / P6 | Kobo October diesel 1,180 → 1,200 (+20 L candidate) | Site outcome and portfolio; no second copy exists to drift | 5 FAIL, caught |
| P4 | Cold electricity 0.20 → 0.22 | 36 figures: site outcomes, Mwea, Kirinyaga options, Harvest plan | 25 FAIL, caught (rev 9: nothing moved) |
| P7 | Embakasi demand rate 12 → 13 | Site outcomes, the Embakasi option 95,484 → 96,684, the Metro plan | 13 FAIL, caught (rev 9: nothing moved) |
| P8 | Kisiwa repair days 1 → 0 | Restore 9 → 8 Nov; Protect hours | 2 FAIL, caught (rev 9: nothing moved) |
| P9 | Kirinyaga recovery share 0.80 → 0.70 | Repair 1,512.40 → 1,279.60; Harvest plan and downside | 5 FAIL, caught by derivation, not by an old reconciliation |
| P10 | Huller days 22 → 20 | Huller 3,540 → 3,000; Lakeside plan and cases | 10 FAIL, caught by derivation |
| P11 *(new)* | Mto half-capacity fuel 5 → 6 L a day | Both inverter paths; plan and every case | 12 FAIL, caught |
| P12 *(new)* | Mto warranty expired | Rights move the 2,600 unit to the operator; claim −2,967.50. At budget 5,000 no plan can restore the inverter, so the evaluator reports "infeasible" as a result. At 6,500, buy-now is chosen. | 17 FAIL, caught |

### Checks run before replying

- `python3 evaluate_structure.py`: 9 sites, 24 options, 3 plans.
- `python3 check_manifest.py`: **587 checks passed, 0 failed**, including the document pass.
- CSV validator: **PASS** (454 rows).
- Rebuild: `rebase_v70.py`, then `gen_fixtures.py` (evaluator vs stated: 0 differences; 28 replay patterns; private oracle removed), then `node build.mjs`.
- Full audit:

| Check | Result |
|---|---|
| Routes rendering | 202 / 202 |
| Console errors / bad links / overflow at 390 px | 0 / 0 / 0 |
| Vocabulary hits | 0 |
| Record identifiers on added and changed screens | 0 |
| Role or question wording | 0 |
| Independent design-value scan | 28-figure set, same as the tagger's; 101 occurrences across all routes and 734 drawers; 0 unlabelled |
| Switch cases | 8 / 8 |
| Drawer / visible focus / contrast | pass / 7 / 7 / 38 / 38 |
| Preserved screens identical to v7.0 | 65 / 65 |
| Private oracle in the bundle | no |

### Owner decision added

**Q14:** keep Kisiwa's battery fuel saving as a flagged assumption, add a fourth calibration spike, or drop the option. Recommended: keep it flagged. The option is deferred and appears in no plan.
