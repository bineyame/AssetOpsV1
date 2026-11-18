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

## Author response (rev 11)

**Author:** AssetOps Architect (Claude), 17 Nov 2026. This answers "## Re-review (rev 10)", including its coordinator points. The governing direction is unchanged (owner, ninth to eleventh messages): the structure must produce the figures, even in the illustration.

### High

**H1: the period's Protect measures were hand inputs. Fixed.**

The period's dated facts are now records, and the structure counts them:

| Site | Record | Evaluated measure |
|---|---|---|
| Kisiwa | generator failed 30 Oct | 10 obligation-hours, 2 asset-days out |
| Mto | inverter failed 28 Oct | 20 obligation-hours, 4 asset-days out |
| Thika | backup start unproven from 6 Oct, no October cover rota | 26 nights without backup cover, 26 days unproven |
| Ruiru | connector out from 6 Oct | 26 charger-days |
| Kasarani, November to date | CH-K2 short from 1 Nov; spare bus 3 nights | 5 nights below required, 2 departures missed, 240.00 penalties, 5 charger-days |
| Ruiru, November to date | connector still out | 6 charger-days |

- The facts sit in a per-site `observations` block, with October and November to date as their own observed periods. The structure counts them with `days_incl` / `days_between`.
- `check_manifest.py` asserts every numeric `portfolio.protect` site value against its node, for both periods.
- The mock-up's Protect views now read the evaluated nodes, not the hand-entered table.
- **All seven O2 measures are evaluated**, each as Σ numerator / Σ denominator of declared nodes: asset availability, field visits, kWh per visit, cooling availability, crate-days without excursion, deliverable energy used, and departures per installed charger. The asset counts are declared, and the checker ties each to its listed assets.
- **One observer output stays an input:** batch crate-minutes above the limit. It is the batch-exposure observer's result and is shown as "Measured".

### Mediums

**M1: rights decided nothing for Thika or Kasarani. Fixed (decision A26).**

- **Separate fields.** Eligibility ("does a right apply") is now separate from `claim_state` (how far the claim has got), following brief l.430.
- **Rule.** A line is supplier-borne when its right is potentially covered and the claim has not been denied.
- **Supplier-borne lines on every path:**
  - Thika: the 710 controller.
  - Kasarani: the 380 contactor.
- **Self-repair paths void the right**, and the evaluator turns that into lost cover: Thika's self-repair loses 710.
- **Battery evidence makes the battery right claimable**, so unclaimable cover goes from 64,000 to 0.
- **Rights perturbations now move the result:**
  - R2 (Thika claim denied): the controller moves to the operator, so the stopgap path costs 810, and the protective choice switches to self-repair (710).
  - R1 (Kisiwa right potentially covered): repair cost 0, spend 1,950, and the case flips.

**M2: the hard-limit rule was EV-only. Fixed (decision A25).**

- **Bounds declared per vertical, each with a reason:**
  - mini-grid: redundancy, claimable cover;
  - cold: backup cover, room capacity;
  - EV: departures, import limit.
- **Bounds are tested absolutely on every option**, not relative to the reference.
- **Each plan decision declares its policy** (hard or advisory) and any least-violation fallback.
- **Protective decisions are now chosen by the allocator,** taking the cheapest option that meets the hard bounds. Hand-placed `fixed` lists are gone.
  - Thika: the stopgap (100) beats self-repair (710).
  - Kasarani: the stopgap.
  - Kobo: the battery evidence.
  - Kisiwa: no option restores redundancy at once, so the least violation is chosen (repair 15 h, against replacement 105 h and no action 125 h).
- **Valued decisions are enumerated among admissible options only.**
- **Results on the reviewer's cases:**
  - Q3: the cover now scales with the shortfall.
  - Q5: import limit 380 rejects the 400 kW schedule.
  - Q6: Mwea at 300 crates exceeds room capacity by 940 crate-days and is rejected.
  - Ruiru +10 is rejected (62 missed departures).
  - The Kisiwa battery's 10 h is advisory, because a battery does not replace the failed generator.

**M3: Kasarani cover, Embakasi feasibility and the cheapest schedule were hand-shaped. Fixed.**

- **Kasarani cover** = shortfall bus-nights − spare cover, priced at 45.00 per bus-night.
  - Shortfall: chargers in service give 1,050 kWh against 1,200 required, so one bus is short each night, for 3 nights to restore.
  - Spare cover is a declared parameter: 1 bus-night.
  - Cost per bus-night is a declared quote: driver overtime 35 + energy 10.
  - So 2 bus-nights × 45 = 90.00, and the cost scales with the shortfall (Q3).
  - The row and the screen now say this, which closes L3.
- **Embakasi feasibility.** `feasible_nights` (spike E) now feeds missed departures: (31 − feasible) × one bus. At 25 feasible nights (Q4) the schedule fails the departures bound and drops out of the plan.
- **Cheapest schedule.** It reads the import limit from `physical`.
- **§10 lists the inputs that remain by design:** spike design values, quotes, one observer output, the record count, and Q14.

**M4: the document check missed most drift. Fixed.**

- **Figure anchors.** 76 figures across the main document, contracts, models, phase plan, integration, cost plan and walkthroughs carry `<!--fig:path-->` anchors, invisible when rendered. The checker asserts each anchored number equals the evaluated value at its path. This catches a swap to another valid figure, which D2, D3, D5 and D6 now do.
- **Superseded scan** now also covers the manifest's own strings.
- **Membership scan** now covers the walkthroughs as well as main §2–§10.

### Lows

| Finding | Outcome |
|---|---|
| **L1** | Fixed. OR-ALLOC-1 quotes the evaluated spend (3,750), and the checker asserts it. |
| **L2** | Fixed. Headers carry no check counts; the revision labels are updated, including the manifest's first line. |
| **L3** | Fixed (see M3). |
| **L4** | Fixed. `check_manifest.py` is rewritten and holds no prices, tariffs, windows or counts. It checks identities, then stated against evaluated values, anchors, documents and spikes. |
| **L5** | Fixed. RUI-4CHARGERS is evaluated: 4 × the declared unit cost = 60,000, and deliverable energy stays 3,200 kWh because the import limit binds. The checker asserts the row's `avoided_capex` against it. |

### Figures

No headline figure changed in this round. Lakeside +6,088.50 at 3,750; Harvest +3,182.40 at 720; Metro +95,634.00 at 1,590. These now come with the protective choices and bound checks that produce them.

### Perturbations (scratch copy; working tree untouched)

| # | Change | What moved | Checker |
|---|---|---|---|
| P1 | Kisiwa crew visit 8 → 9 Nov | restore date; repair hours 15 → 20 | 2 FAIL |
| P2 | Kobo diesel price | stop setting 2,916 → 3,042; plan and all cases | 91 FAIL |
| P4 | cold electricity price | Kirinyaga, Mwea, Harvest plan | 54 FAIL |
| P5 | Mto lead time 21 → 22 days | restore 29 Nov; claim −373.75; plan | 67 FAIL |
| P7 | Embakasi demand charge | option 96,684; Metro plan; site outcomes | 72 FAIL |
| P9 | Kirinyaga recovery share | repair 1,279.60; plan | 24 FAIL |
| P11 | half-capacity fuel | both inverter paths; plan | 83 FAIL |
| P12 | Mto warranty expired | claim −2,967.50; at 5,000 no plan restores the inverter, reported as infeasible | 105 FAIL |
| Q1 | Thika remedy 8 → 12 Nov | wait path 2 → 6 nights | 2 FAIL |
| Q2 | Kasarani kWh per bus | shortfall, cover cost 225, value 375, plan | 47 FAIL |
| Q3 | Kasarani 2 chargers failed | cover 495, value 825, plan; nothing left unrejected | 35 FAIL |
| Q4 | Embakasi feasible nights 31 → 25 | schedule rejected (6 missed); Metro plan 150 | 28 FAIL (rev 10: nothing moved) |
| Q5 | import limit 500 → 380 | deadline schedule rejected (import exceeded by 20 kW) | 32 FAIL |
| Q6 | Mwea 300 crates | rejected by room capacity (940 over); Harvest plan 1,512.40 | 24 FAIL |
| R1 | Kisiwa right potentially covered | repair 0; spend 1,950; case flips | 33 FAIL |
| R2 | Thika claim denied | controller borne by the operator; protective choice → self-repair | 6 FAIL (rev 10: nothing moved) |
| N1 *(new)* | Kisiwa failure 30 → 29 Oct | October obligation-hours 10 → 15; asset-days 2 → 3 | 3 FAIL |
| N2 *(new)* | Thika unproven from 10 Oct | October nights 26 → 22 | 2 FAIL |
| N3 *(new)* | Kasarani spare covers 0 | wait 3 missed; cover 135; value 225 | 35 FAIL |
| N4 *(new)* | battery evidence no longer makes the right claimable | evidence fails its bound; protective decision unmet | 32 FAIL |
| D1 | main +6,088.50 → +6,082.50 | (document) | 2 FAIL |
| D2 | main Metro +95,634.00 → +95,484.00 | (document) | 1 FAIL (rev 10: passed) |
| D3 | main Kasarani +150.00 → +240.00 | (document) | 1 FAIL (rev 10: passed) |
| D5 | main "2 departures missed" → "3" | (document) | 1 FAIL (rev 10: passed) |
| D6 | contracts 367.50 → 361.25 | (document) | 1 FAIL (rev 10: passed) |

### Checks run before replying

- `python3 evaluate_structure.py`: 9 sites (plan, October, and November to date where recorded), 26 options, 3 plans.
- `python3 check_manifest.py`: **753 passed, 0 failed**.
- CSV validator: **PASS**.
- Rebuild: `rebase_v70.py`, `gen_fixtures.py` (oracle removed), `node build.mjs`.
- Full audit:

| Check | Result |
|---|---|
| Route renders | 202 / 202 |
| Console errors / bad links / overflow at 390 px | 0 / 0 / 0 |
| Vocabulary hits / identifiers / role or question wording | 0 / 0 / 0 |
| Independent design-value scan | 28 figures; 102 occurrences; 0 unlabelled |
| Switch cases | 8 / 8 |
| Drawer / focus / contrast | pass / 7 of 7 / 38 of 38 |
| Preserved screens identical | 65 / 65 |
| Oracle in the bundle | no |

**Still owner decisions:** Q1–Q14, including Q14 (Kisiwa battery assumption) and Q13 (client exposure of replay figures).

## Author response (rev 12)

**Author:** AssetOps Architect (Claude), 17 Nov 2026. This responds to "## Re-review (rev 11)". The governing principle is unchanged: every figure and every admissibility comes out of the declared structure. This round removes the last typed admissibility, fixes the valuation netting, makes crews and the least-violation fallback real constraints, signs the document check, and moves the remaining screen literals onto evaluated nodes. One item is a policy question for the owner (Q15). (A) is applied pending the answer, and it leaves the plans as reviewed.

### Headline figures (unchanged)

| Plan | Value | Spend | Crew visits |
|---|---|---|---|
| Lakeside | +6,088.50 | 3,750.00 | 3 of 3 |
| Harvest | +3,182.40 | 720.00 | 2 of 2 |
| Metro | +95,634.00 | 1,590.00 | 0 of 2 |

Every switch case, sensitivity and downside is also unchanged. The evaluator now produces 27 options; KAS-LOCAL is new.

### Findings

| # | What changed | Where |
|---|---|---|
| **H1** | **No typed admissibility is left.** `money` / `bound_failure` are deleted from MTO-INV-NOACT and `bound_failure` from KOB-RESERVE; the evaluator no longer reads `bound_failure` at all.<br>**Notice-deadline lapse.** A right with an open notice deadline now lapses, for the options that decide that asset (`asset:`), unless the option files notice by the deadline (`files_notice`, a date expression). The claim and buy-now paths file on 6 Nov. No action files nothing, so INV-MT-02 lapses on 27 Nov and **2,600.00 is lost**.<br>**Cover bound across all three verticals.** The `claimable_cover` bound now tests `cover_not_claimable` = unclaimable + lost cover, and it is declared for all three verticals.<br>**Mto no action.** It is now complete: it carries the same extra fuel as the other paths, so it would be worth −156.25 if it were admissible. It sits inside the `mto_inverter` decision and is rejected by that bound.<br>**Kobo.** A declared `dawn_adequacy` bound over the node `replayed_dawn_days_below_safeguard` replaces the typed string. The leaf is read from the row's `forward_replay.soc_0500_below_35_days`, a spike-K design value. KOB-RESERVE fails it (4 days); KOB-STOPSOC passes (0). Perturbation K1 (0 → 2 days) rejects the stop-setting change and moves the plan. | evaluator `run()` rights block; manifest `evaluation.bounds`, the MTO-INV-* and KOB-* options, `plans.lakeside-power` |
| **M1** | **Value now nets the reference path's one-off.** The formula is value = Δ × months − (option one-off − reference one-off). The output gains `reference_one_off` and `net_one_off`; sensitivities use the netted figure.<br>**Perturbation M1t** (the contactor borne by the operator on both paths): the stopgap stays **+150.00** (rev 11: −230). Under RB, the restore date now also follows the right; see L4. | evaluator `run()`; main §2.3 identity; contracts identity; A28 |
| **M2** | **Crews are enforced.** `best()` sums each item's `crew_visits` against the tenant limit (`crew_limit` per plan). Crew visits come from the option rows, or are declared on the option with a basis; they are never defaulted, and the checker asserts that every plan item has them.<br>**Outputs:** `crew_visits_used` / `crew_visits_limit` per case. The checker asserts them against the manifest's allocation, and they are anchored in the main document, the models, the phase plan and the walkthroughs.<br>**L1 (crews 3 → 1)** and **M2b (crews 3 → 2)** now make every Lakeside case infeasible, with that reason stated. | evaluator `best()`; manifest `crew_limit`, option `crew_visits`; A29 |
| **M3** | **The fallback is budget-aware.** Protective choices are remade per switch case inside that case's budget and visit limit. The least violation is chosen among affordable options, and a `trade_off` is reported when a smaller violation was unaffordable. A valued decision may declare the same fallback (violation minimised before value).<br>**L2** (Kisiwa crew visit on 29 Nov): the repair is kept (120 h), the 9,500 replacement (105 h) is reported as the unaffordable trade-off, and **every case stays feasible** (rev 11: all infeasible). **M3b** (budget switch 1,500) chooses no action at Kisiwa as the least affordable violation and states the trade-off.<br>**Policy.** The distinguishing fact is now declared, `physical.shortfall_backed_by_generator`. At Kisiwa it is 0: GEN-KS-02 alone carries the evening load. At Mto it is 1: the generator carries the daytime shortfall. One rule applies to every Lakeside decision: hard, with the fallback, on `obligation_hours_without_backup`. **This is a policy on what counts as a breach, so it is raised as owner question Q15.** Q15 sets out options (A) applied, (B) and (C), each with its effect on the plans (computed by running the evaluator on each variant):<br>• (A): no change to the plans.<br>• (B): the 6,500/yes case falls to 3,508.50 at 6,430.<br>• (C): Kisiwa takes no action; spend 1,950; the 5,000/no case buys the inverter now. | evaluator protective / `best()`; manifest physical facts and `plans`; questions Q15, A29; owner checklist |
| **M4** | **Signed anchors.** The sign written before a figure is part of it; `<!--fig:-path-->` marks a cost written as a subtraction. Da and Di are now caught.<br>**Period-to-date rule.** A figure stated for a period to date may not be anchored to an option path. The walkthrough is re-pointed to `sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed`, and the $240 and the 5 nights are anchored.<br>**Required headline anchors** in the main document and the walkthroughs: spend, value and visits for every plan, plus the §10 Protect statement (Kisiwa 10, Mto 20, Thika 26, Kasarani 2 / 240).<br>**Coverage rule.** Every occurrence of an evaluated plan or option money figure in the eight figure-bearing documents (now including this questions file) must carry an anchor. Record figures carry `<!--rec-->`, checked against the manifest's money records.<br>**Result.** The documents now carry **417 figure anchors (rev 11: 250) and 39 record tags**. Most of the new anchors were placed by explicit context rules (scratch `rev12/autoanchor.py`, every placement listed and reviewed); the rest were placed by hand. All of Da, Db, Dc, Dd, De, Df, Dg, Dh and Di are now caught, as are E3+ and the new drifts Dj, Dk and Dm. | `check_manifest.py` `anchors()`; all figure-bearing documents |
| **M5** | **Screen literals.** The typed `incident.capacity_after` / `incident.november_to_date` are deleted. The Kasarani row and the decision read the November-to-date nodes, labelled "Calculated from records". `capacity_crate_days_oct` is deleted (now evaluated as 400 × period days). The other result-map literals are read from DERIVED. The audit has a new scan for hand-typed figures in `loop-*.js`. See "M5: what the builder replaced" below. | `loop-*.js`, `tools/audit.mjs` |
| **L1** | **One record per input.** `failed_chargers` comes from the November observation. Spare cover = `physical.spare_buses` × the roster's free nights (E2 now moves the outcome). The Mto and Kisiwa paths read the observed `reduced_hours_per_day` (Nk now moves the options). Capacity = crates per room × period days. | manifest |
| **L2** | **Uncovered nights.** The node is now unproven nights − nights without stock − nights covered by a rota, each from a record (L2t moves it). | factor map, Thika observation |
| **L3** | **THIKA-SELF restore.** Its restore now carries a declared procurement driver, labelled as an assumption ("held in local stock, fitted the same day; no quote held"). | manifest |
| **L4** | **Restore follows rights.** A restore performed by the supplier (`performed_under`) falls back to "none within the horizon" when the right is not covered.<br>**KAS-LOCAL is evaluated:** it restores on 7 Nov, `voids_rights: [CH-K2]`, loses 380 and fails the cover bound.<br>**Under RB:** waiting runs to the horizon (24 missed), and the local repair becomes the protective choice (spend 380). | evaluator restore; manifest |
| **L5** | **Forward baseline.** Before an option's changes apply, the period-observation leaves are reset (`forward_baseline` per vertical). KIS-BATT60, MTO-HULLER and MTO-WELDING now show 0 obligation hours, and Mto's "immediate restore" reference shows 0. | evaluator, manifest |
| **L6** | **Kasarani November delivery.** It is now 5,250 kWh (≤ 1,050 × 5). The checker asserts recorded kWh a night ≤ deliverable for every EV side, and L6t (6,000) is caught. | manifest, checker |
| **L7** | **Declared per vertical.** The Protect nodes and the option detail nodes are now declared per vertical in `evaluation`; there are no lists in the evaluator code.<br>**Dispositions checked.** The checker asserts row dispositions against the evaluation: RECOMMENDED is in the plan, CONDITIONAL is in a case, REJECTED/DEFERRED is not in the plan, ACCEPTABLE is admissible, and a comparator is RECOMMENDED only if admissible. This caught BAT-NOACT "ACCEPTABLE" while it was inadmissible; it is now REJECTED with the evaluated reason. The THIKA-SELF, KAS-LOCAL and MTO-INV-NOACT reasons now state the bound. | evaluator, manifest, checker |

### Coordinator points

1. **Structure below money.** Crews are structural (M2). The Kasarani November figures are evaluated, not typed (M5). Thika's uncovered nights are a three-record expression (L2).
2. **The causal step.** No admissibility is typed (H1). THIKA-SELF has a declared driver (L3). Kasarani's inputs each come from one record (L1).
3. **Coverage.** Unchanged: all nine sites run through the structure, and the evaluator now produces 27 options.
4. **Rights.** The notice deadline is a structural lapse (H1), netting is correct under a rights flip (M1), and restore dates follow rights; KAS-LOCAL's voiding is evaluated (L4).

### Perturbations (scratch copy `pert3`; harness `scratchpad/perturb3.py`; checker base 1,038)

"Moved" is the number of changed leaves in `derived-values.json`. A failing checker means the drift is caught. The reviewer's items come first and keep the reviewer's IDs.

| # | Change | What the structure did | Checker |
|---|---|---|---|
| X1 | *(was: delete NOACT's typed strings)* NOACT files notice on time | NOACT becomes admissible and is chosen: Lakeside +6,299.75 at 3,520 (2 visits). The cover bound was the only thing excluding it, and it is structural. | 88 FAIL |
| X3 | *(was: give NOACT the extra fuel; that is now its baseline)* notice deadline 27 Nov → 2 Dec | nothing: a right never notified lapses whenever its deadline falls (invariance, as intended) | 0 FAIL (expected) |
| RA | Mto claim DENIED | claim −2,967.50. The right no longer lapses (there is no cover to lose), so no action passes the cover bound and is chosen inside the horizon: +6,299.75 at 3,520. This is a horizon effect: the generator keeps running after 30 Nov. Q15 (B) would reject it. | 112 FAIL |
| RB | Kasarani claim DENIED | supplier restore no longer applies: waiting runs to the horizon (24 missed). The local repair, with no cover left to lose, becomes the protective choice: +2,880, spend 380. Metro +98,364 at 1,880. No −230 (M1). | 68 FAIL |
| RC | Thika EXPIRED | the self-funded controller passes the cover bound and is chosen. **Crews now bind:** with 2 visits, the Kirinyaga repair drops. Harvest +1,670.00 at 980. | 55 FAIL |
| RD | Kobo BAT-001 already covered | BAT-NOACT is admissible and chosen; spend 3,320, 2 visits | 45 FAIL |
| RE | Kisiwa covered | repair 0; spend 1,950; 5,000/no case flips to buying now | 48 FAIL |
| L1 | Lakeside crews 3 → 1 | every Lakeside case is infeasible, with the reason stated (rev 11: nothing moved) | 119 FAIL |
| L2 | Kisiwa crew visit 29 Nov | repair kept (120 h); the replacement (105 h, 9,500) is reported as an unaffordable trade-off; every case is feasible (rev 11: all infeasible) | 2 FAIL |
| H1t | Mto shortfall not backed (Q15 option B) | the claim and buy-now paths both violate; least violation within the budget keeps the claim at 5,000 | 30 FAIL |
| Nk | Mto window 5 → 6 h | October 20 → 24 h **and** the options 110 / 30 / 125 → 132 / 36 / 150 (rev 11: options unchanged) | 5 FAIL |
| C1 | Thika remedy 6 Nov | waiting is admissible and chosen; spend 620 | 21 FAIL |
| C2 | Thika backup proven | 26 → 0 nights | 3 FAIL |
| E2 | Kasarani `spare_buses` 1 → 0 | wait 3 missed; cover 135; stopgap +225 (rev 11: nothing moved) | 65 FAIL |
| E3 | November spare 3 → 2 | November 3 missed, 360 | 8 FAIL |
| E3+ | E3 with the protect table updated | the walkthrough and main-document anchors on the November nodes catch it (rev 11: passed) | 6 FAIL |
| E4 | Ruiru import 400 → 300 | +6 rejected (93 missed, 80 kW over) | 8 FAIL |
| E5 | SLA 8 business days | restore 12 Nov; wait 5 missed; stopgap +375. The screen reads the node (see M5). | 65 FAIL |
| Q3 | November failed chargers 1 → 2 (one record) | cover 495; stopgap +825 | 74 FAIL |
| Q4 | Embakasi feasible nights 25 | schedule rejected; Metro 150 | 38 FAIL |
| R2 | Thika claim DENIED | as RC | 55 FAIL |
| Da, Di, Db, Dc, De, Dh, Df, Dg | documents (rev 11: all passed) | — | 1 FAIL each |
| Dd | main 720.00 → 702.00 | — | 2 FAIL |
| M1t *(new)* | contactor operator-borne on both Kasarani paths | stopgap stays +150.00; spend 1,970 | 35 FAIL |
| H1n *(new)* | Mto notice deadline already passed (3 Nov) | every path lapses and violates the cover bound equally; least violation then value picks no action | 119 FAIL |
| K1 *(new)* | Kobo replay 0 → 2 dawn days below 35% | stop-setting rejected by dawn adequacy; Lakeside +3,172.50 | 123 FAIL |
| M2b *(new)* | Lakeside crews 3 → 2 | infeasible, with the reason stated | 119 FAIL |
| M3b *(new)* | Lakeside budget switch 1,500 | Kisiwa protective choice = no action (the least affordable violation), with the repair reported as the trade-off; +2,548.50 at 750 | 94 FAIL |
| L2t *(new)* | Thika stock absent 3 unproven nights | 26 → 23 nights | 2 FAIL |
| L6t *(new)* | Kasarani November kWh 6,000 | the record-consistency check fails | 1 FAIL |
| Dj, Dk, Dl, Dm *(new)* | walkthrough visits 2 → 3; a new unanchored copy of the Metro spend; a record tag altered (150.00 → 151.00); walkthrough November penalties $240 → $360 | — | 1 FAIL each |

**Every perturbation and drift is caught except X3, which is invariant by design.**

### M5: what the builder replaced (details in `interactive-mockup-vNEXT/fixture-mapping.md` §3g and `CHANGE-REGISTER.md` §7i)

- **Kasarani November figures.** 1,050 of 1,200 kWh, 1 bus short, 2 departures, $240 and "2 × $120" now come from `sites["metro-bus/Kasarani"].november_to_date.nodes`, labelled "Calculated from records".
- **Restore dates and protect values.** "Likely 2 missed departures before 9 Nov" and "unprotected at night until 8 Nov" are now built from the options' `protect` values and `restore_date`.
- **Ruiru.** 2,800 / 3,200 / 3,360 kWh come from `bound` of RUI-ABSORB6/10.
- **Departures per charger.** "1,302 ÷ 26" comes from the O2 numerator and denominator. The Ruiru "per charger-day in service" figures (25.16, 51.75) had no node, so they are deleted.
- **Crews.** Every visit count comes from `crew_visits_used` / `crew_visits_limit` per case.
- **Worked figures.** Kobo, Thika, Mto and Embakasi worked figures come from nodes, cost lines and parameters.
- **Bound table.** It now shows each decision's hard bounds with the measured node. The advisory wording is gone, KAS-LOCAL is shown, and the trade-off line is rendered when one is present.
- **New audit scan.** `tools/hand_typed_scan.py` fails on any digit-bearing literal in `loop-*.js` that equals an evaluated figure. Result **0**, with 30 allow-listed literals, each with a reason: declared policies and limits, event dates, declared windows, assumptions, and one preserved v7.0 example.
- **`gen_fixtures` diff.** It now also covers restore dates, crew visits, Protect effects and plan visits.
- **Typed figures that remain** have no evaluated node and are context text from records or spike E: "about 406 kW for a 21-bus night" (spike E basis), the peak shares 55% / near 0%, 62,000 kWh a month, and the battery estimate "184 kWh (92%)" (an occurrence record).
- **Walkthrough.** The "obligation hours" step now reads "without redundancy", matching the screen, with Kisiwa 10 and Mto 20 anchored.

### Checks run before replying

- `python3 evaluate_structure.py`: 9 sites, **27 options** (KAS-LOCAL added), 3 plans; the plan figures are unchanged.
- `python3 check_manifest.py`: **1,040 passed, 0 failed** (rev 11: 753). The checks are now signed, the headline anchors are required and anchor coverage is enforced, and they include crews, dispositions and record consistency.
- CSV validator: **PASS**.
- Rebuild: `rebase_v70.py`, `gen_fixtures.py` (28 replay patterns; it covers the new fields), `node build.mjs`, `gen_docs.cjs`.
- Full audit (`run-audit.sh --shots`, exit 0):

| Check | Result |
|---|---|
| Route renders | 202 / 202 |
| Console errors / bad links / overflow at 390 px | 0 / 0 / 0 |
| Vocabulary / identifiers / role or question wording / Portfolio filter controls | 0 / 0 / 0 / 0 |
| Independent design-value scan | 28 figures; 93 occurrences and 734 drawers; 0 unlabelled |
| Hand-typed figures in `loop-*.js` | **0** (30 allow-listed with reasons) |
| Switch cases / focus / contrast | 8 of 8 / 7 of 7 / 38 of 38 |
| Preserved screens identical | 65 / 65 |
| Oracle in the bundle | no |

- Perturbations: 41 runs. 40 are caught; X3 is invariant by design.

### Still owner decisions

**Q1–Q15.** Q15 is new: the redundancy policy, with (A) applied and recommended. It is set out in `design-questions-and-decisions.md` with the effect of each option on the plans. It is also in the owner checklist.

## Author response (rev 13)

**Author:** AssetOps Architect (Claude), 17 Nov 2026. This responds to "## Re-review (rev 12)" and the owner's twelfth message (four rules).

**Work order (owner rule 4).**
1. `structure-specification.md` was written first, as the contract.
2. A helper that never read the evaluator wrote `independent_model.py` from that specification and the manifest. Its 26 recorded ambiguities were settled by amending the specification, never by copying the evaluator.
3. The rewritten `check_manifest.py` imports no evaluator code and holds no expected figure. It compares the evaluator's output, the manifest's stated copies and the document tags against that independent model.
4. `derivation-register.md` is the main deliverable (rule 2).

### Findings

| # | Outcome |
|---|---|
| **H1** | **The huller dependency is now dated.** `requires_any` is deleted. MTO-HULLER now requires that the restore date of the plan's inverter path, plus the contractor's 5 working days, falls on or before the letter's lapse date (30 Nov), or the extension date when the switch is set; no restore means no connection. Under the perturbations:<br>• LT7: claim plus huller in every case, 6,176.00.<br>• LS20: the 6,500/no case loses the huller, 2,548.50.<br>• RA and H1n: the plan repairs the inverter locally (no cover is left to lose) and keeps the huller, 5,993.50.<br>• X1: the plan is unchanged, because a never-restored inverter cannot connect the huller. |
| **M1** | **Protective and valued decisions are enumerated together**, ranked by least violation, then value, then spend.<br>• B2000 is now feasible (+6,088.50 at 1,950); B1500 gives +2,548.50.<br>• CR2 is feasible: Kisiwa takes no action, and the repair is reported as the trade-off.<br>• RC reaches the joint optimum: the stopgap, Kirinyaga and Mwea, +3,182.40. |
| **M2** | **Money runs to the restore date or through the tenant's 12-month horizon**; Protect is stated to 30 Nov. The no-action fuel cost is −2,281.25 (rev 12: −156.25). This is disclosed in A33, in the main document and on the Mto decision screen. |
| **M3** | **Rendered manifest strings carry `{fig:}` / `{rec:}` placeholders**, rendered by the mock-up. The checker rejects an evaluated figure written as a literal (now 0). |
| **M4** | **Coverage now includes whole-dollar forms, monthly changes and O2 percentages.**<br>• The Q15 figures are evaluated variants (`owner_question_variants`) and are anchored.<br>• The October bill lines are nodes, and anchored.<br>• Dn1–Dn9 are caught. |
| **M5** | **Deciding options are derived** from the rights each option touches and from decision membership; the `asset:` key is gone. A deadline already passed is LAPSED for every option. The checker requires a notice deadline or a notice term on every un-notified right, and CH-R7 and BAT-001 now record theirs. GT1 is caught. |
| **L1** | **Under a refused right, the restore switches to the operator's own procurement**, with that path's crew visits. |
| **L2** | **The Q15 fact is computed:** shortfall backed = min(1, floor(standby kW / lost kW)), from the site's declared outage records. |
| **L3** | **MTO-INV-LOCAL is evaluated:** it restores on 8 Nov and fails the cover bound. |
| **L4** | **The allow-list is used in full and keyed by place:** 46 entries, all used, each keyed by file or manifest path, exact literal and context, with a reason (rev 12: 30 entries, 8 used). The scan now also covers the 216 rendered manifest strings outside their placeholders, and an unused entry fails it. |
| **L5** | **The remaining typed Embakasi and Kobo figures are now computed.**<br>• Embakasi peak share: from nodes (55% reference, 0% under both options; "near 0%" is gone).<br>• Night kWh: from the option parameters.<br>• Kobo battery 92%: from a new numeric record, 184 kWh ÷ 200 kWh.<br>• 406 kW keeps its design-value label (spike E). |
| **L6** | **The roster is dated:** spare cover counts the listed free nights inside the window. |

**Q15 stays open.** (A) is applied pending the owner's answer. The two alternatives are re-evaluated (B, C).

### Figures that changed (owner rule 1)

| Figure | Rev 12 | Rev 13 | Why |
|---|---|---|---|
| MTO-INV-NOACT value if admissible | −156.25 | −2,281.25 | fuel is now counted over the 12-month horizon |
| KAS-LOCAL Protect effect | 0 missed, −140 | 1 missed, −260 | the dated roster has no free spare-bus night on 6 Nov |
| MTO-INV-LOCAL | not evaluated | −462.50, restores 8 Nov, fails the cover bound | now evaluated |
| KAS-LOCAL cost per departure met | 23.71 | 24.29 | its one missed departure (dated roster) adds 120 of penalties; added after the final review (L5) |

The headline plans and downsides did not change. They are an output of this round, not its success criterion.

### Results

- **Evaluator:** 9 sites, 28 options, 3 plans.
- **Independent checker:** **3,255 passed, 0 failed.**
- **CSV:** PASS.
- **Perturbations (rev 13 harness):** 57 runs, made up of the reviewer's set, one perturbation for each derived item of register §2, and document drifts. Every one moves or is caught. The exceptions are A08 and Dn8 before their fixes; both now move.
- **Register:**
  - 852 manifest leaves affect a figure or choice. All are (b): 355 structure declarations, 308 records, 95 policy declarations, 35 quotes, 30 owner decisions, 17 replay design values, 12 assumptions.
  - 1,589 leaves affect nothing and are (c).
  - 25 derived items (a), 34 evaluator rules, 12 checker items, and 14 items no perturbation reveals.

### Completed after hand-back (coordinator: "finish rev 13")

**The builder's work is merged.**
- **Placeholders.** 78 manifest strings were converted, holding 91 figure and 53 record placeholders. The single renderer `tpl()` leaves 0 unresolved.
- **The huller row is derived per inverter path** from the evaluated restore date, the contractor's working days and the letter dates: no action, lost (never restored); claim, kept only with the extension, connected by 4 Dec; buy now, kept by 19 Nov; local repair, kept by 13 Nov but not admissible.
- **The CONDITIONAL text for buying now** comes from the switch cases.
- **The horizon disclosure** is on the Mto page.

**I fixed the remaining figure restatements flagged in the builder's sweep:**
- `loop-decisions.js:142`: $194;
- `:282`: $6,430 and 30 Nov;
- `:302`: +0.6%;
- `:303`: 4,500 crate-days;
- `:334–335`: one bus short;
- `:48`: 184 kWh, now a numeric record.

**Typed copies the screen no longer read are deleted:** `sla_clock.restore_due` and `protect_effects.penalties`. The penalties column is derived from the measure instead. The departures-missed measure is now labelled "Calculated from records".

**Kasarani screen test** (builder, scratch copy; SLA 8 business days and November spare 3 → 2):
- "9 Nov", "2 missed", "$240", "3 nights", "lent on 3", "missed on 2" and "$90" each appear 0 times; the base capture has 3, 3, 8, 1, 1, 1 and 3.
- The perturbed screens show 12 Nov, 5 missed, $600, 6 nights, $225 and November to date $360.
- 26 of 716 lines changed.

**Register §7.** 801 rows across the 15 mock-up and generator files: 244 (a), 331 (b), 226 (c).
- 154 rows restate a record in code. They are documented limit L-RS: they are not checked, because the scan sees only evaluated figures.
- 42 rows are typed narrative facts, documented limit L-UB.
- None holds a figure in place.

**Final runs:**

| Run | Result |
|---|---|
| Evaluator | 9 sites, 28 options, 3 plans |
| Independent checker | **3,255 passed, 0 failed** |
| CSV validator | PASS |
| Influence scan | 2,438 manifest leaves × 5 worlds: 852 affect a figure or choice (all (b)), 1,586 affect none (c) |
| Perturbation suite (`perturb4.py`) | 44 runs, all caught; every derived item's perturbation moves it |

Full audit (`run-audit.sh --shots`, exit 0):

| Check | Result |
|---|---|
| Routes | 202 / 202 |
| Console errors / bad links / overflow at 390 px | 0 / 0 / 0 |
| Vocabulary / identifiers / role or question wording / filter controls | 0 / 0 / 0 / 0 |
| Design-value scan | 28 figures, 93 occurrences and 733 drawers, 0 unlabelled |
| Hand-typed figures | 0 in code, 0 in 216 rendered manifest strings; 46 allow-list entries, 0 unused |
| Placeholders | 91 figure + 53 record in 77 strings, 0 unresolved |
| Switch cases / focus / contrast | 8 of 8 / 7 of 7 / 38 of 38 |
| Preserved screens | 65 / 65 |
| Oracle in the bundle | no |

**Still open, and the reason:**
- The builder asked for some nodes to be exported, so that their allow-listed literals could become placeholders: the bridge quantities (actual − plan), chargers × kW, the Thika crate-minute range, the rights evidence shares, payback years, and Mwea +0.6% / Kirinyaga 24% in manifest text. They are not exported. Each is allow-listed with its reason and listed in the register.
- **Q15** remains an owner decision.

### Close-out after the final review (ACCEPT WITH NOTES)

**Class (i), fixed.**
- **F1.** The Lakeside plan-value drawer's rows now come from the evaluated case's valued options (`derivedPlan(op).valued_options` and `DOPT(id).value`) for every tenant. The design-value note names only the valued options in the case, and reads their figures from the evaluated parameters, not the `forward_replay` copies.
- **F2.** The "Largest …" claims are removed from the Act first reasons. The letter's lapse date in the buy-now reason is now read from the record.
- **Screen test** (scratch copy, headless, all four Lakeside switch cases):
  - In every case the drawer rows are exactly the case's valued options and sum to the headline: 6,088.50, 2,548.50, 6,088.50 and 3,508.50.
  - The design-value note mentions the huller only when the huller is in the plan.
  - No "Largest" appears on Lakeside, Harvest or Metro Act first.
  - There are 0 page errors.

**Class (ii), recorded as documented limits (not redesigned).** F3, F4, F6 and L1–L6 are recorded in `derivation-register.md` §9 and in the main document's limits (§10).

**Register corrections.**
- §3.2 dispositions no longer claim that unchecked leaves are checked (F3).
- H2 is restated as reachable (G20).
- §7 rows 136, 147 and 169 are marked as fixed after the sweep; rows 170 and 175 are relabelled F6.
- The scan's coverage gap is stated (L1).

**Other corrections.**
- The evaluator docstring now describes the joint allocator (L6).
- KAS-LOCAL's 23.71 → 24.29 is added to the changed-figures table.
- L3 is put to the owner as Q16, with (a) "infeasible" applied.


### Author note, 18 Nov: main §7 rewritten as factor tables (owner, thirteenth message)

The owner could not follow §7.1 and asked to have §7 rewritten the way the coordinator had explained Kobo's 562.00. Only §7 of `layer4-transformation-design.md` changed, and the same section of the `.html` (re-rendered from the Markdown with the conventions the rest of that file uses).

- **Observe.** Each Site now has its inputs (prices, fuel balance, modelled litres and the necessary / candidate / unexplained split, energy-to-cash chain), a plan-against-actual table per factor with the money effect (change × price), and a sum that reconciles to the Site deviation and then to the portfolio. Cold rooms use their own structure (crate-days, model energy and excess above it, liability). EV depots use theirs (bill lines, highest kW, deliverable energy a night, buses short, departures missed and penalties).
- **Evaluate.** Each decision has a table: no action, chosen and rejected options, each option's factor changes, and how its value follows (monthly change × months − one-off).
- **Choose.** This is split into six parts: the plan and its limits; what is valued in money and how the total is composed; spend not valued in money and its Protect measures; downside and sensitivities; items listed beside the plan; the switch cases.
- **Prove.** Unchanged in substance, as short lists.
- **Provenance.** Every table says how each figure is known: record, calculated, declared input, design value, quote or assumption. The litre split (730 / 330 / 120 at Kobo, and the Kisiwa and Mto splits) is stated as a declared input that *stands in for a calculation*. It is no longer labelled "Calculated from records".

**Figures.** No figure in the data, evaluator, model or checker changed. Every new figure is anchored with `<!--fig:path-->` or `<!--rec-->` / `<!--rec:path-->`. The checker now passes 3,602 checks with 0 failures, up from 3,255. Each Site's per-factor effect was also recomputed from the inputs shown (change × price). All agree with the stored bridge records, and the fuel balances agree (220 + 1,200 − 240 = 1,180; 730 + 330 = 1,060; 1,180 − 1,060 = 120).

**Not reconcilable from the data, stated in the section:**
- The "metered generator energy × consumption rate" behind the modelled litres (1,060 L at Kobo, 2,380 L at Kisiwa) is not in the demo data. Back-solving gives a fraction of a kWh, so the modelled litres are a declared input, not a calculation from a reading.
- Ruiru's plan is a stated total, so its +19.68 cannot be attributed to factors.


### Author response, 18 Nov: review of §7 rewrite (bd5970f3d), findings M1, M2, L1–L5

The owner asked that all findings be addressed. Each one is treated as a class across the whole of §7. Only §7 of `layer4-transformation-design.md` changed, plus the same section of the `.html`, re-rendered with the same renderer. The byte prefix and suffix outside §7 are unchanged. No change was made to the manifest, evaluator, independent model, checker or `derived-values.json`. The checker passes **3,680 checks with 0 failures**, up from 3,602 because of the new anchors.

**M1: Kisiwa battery on a different basis. Accepted and fixed.**
- The battery is moved out of the generator table into its own table, "Kisiwa: evening storage".
- That table states what the battery is compared with: Kisiwa's October running, contribution −250.00, which means looking forward from the repair. This is what `derived-values.json` shows: the formula is "contribution under option −55.0 − under reference −250.0", and `reference_protect` is 0. It is also what the manifest's `kisiwa_storage` reason says.
- Its hours cell reads "n/a: measured after the repair". A sentence says this cannot be compared with the 125 / 15 / 105 hours, which count 6–30 Nov.
- The result now follows the data. The disposition is **Deferred**, not "Not chosen" (manifest row `disposition: DEFERRED`). The reasons are over budget (14,000.00 one-off against the 5,000 budget, which matches the plan's `excluded` reason "over budget; payback ~6 years") and negative over 12 months (−11,660.00). The payback is shown as arithmetic: 14,000 ÷ 195 ≈ 72 months, about 6 years.
- The generator table now explains the least-violation choice in plain words: no option restores a backup at once, so the option with the fewest hours that fits the budget is chosen.

**M2: plan figures labelled "Record". Accepted and fixed as a class.**
- The legend gains a **Plan** row: the operator's monthly plan line from its plan spreadsheet, a declared target, not a record. This matches the manifest source "monthly plan / budget spreadsheet".
- One rule now covers every factor table: the Plan column is Plan, and "How it is known" describes the Actual column. The three "plan: Record; actual: Declared input" cells now read "Declared input".
- The same check covered every other label in §7. Three labels were not in the legend:
  - "estimate" (Kisiwa O&M, Thika maintenance, Kasarani maintenance). These are invoices not yet received, with the plan amount carried. The legend gains an **Estimate** row and the three cells use it.
  - "Design value" is reworded in the legend without the word "forward replay".
  - "Plan limit" now also covers service rules: battery at 35% at dawn, every departure met, backup cover every night.

**L1: unlabelled inputs. Accepted and fixed as a class.**
- The Lakeside Prices table gains a "How it is known" column and two rows:
  - productive-use tariff 0.30 (Record, tariff schedule; `rec:` anchored);
  - battery wear 0.08 (Assumption, to be checked against the warranty's throughput terms; `rec:` anchored).
- Each portfolio's Evaluate now opens with an **Inputs to the options** table. It lists every input the option tables use, with its figure and label.
- Mwea handling is labelled Assumption.
- Labels were taken from the manifest's own basis text. Where the manifest gives no source, the label says **"Declared input, source not recorded"** instead of guessing. One result: the Kobo trial's 60 + 30 lose the "Quote" label the previous text gave them, because the manifest calls neither a quote. Inputs with no recorded source:
  - Kobo: trial 60 / 30; 100 kWh battery 28,000.
  - Kisiwa: repair 1,800; replacement 9,500 and its 21 days; battery 14,000.
  - Mto: shipping 150; installation 80; unit bought now 2,600; local repair 450; huller collection 15; meter audit 60.
  - Kobo battery evidence: 250 / 180.
  - Mwea: one-off 150 / 120.
  - Compressor: 4,800.
  - Kirinyaga: repair 350.
  - Thika: relay 40, rota 60.
  - Embakasi: set-up 1,500.
  - Kasarani: local repair 380.

**L2: Embakasi 05:15. Accepted and fixed.**
- The schedule row now says: billed hours are 2 + 5 at 400 kW = 2,800 kWh a night, exactly the requirement. 05:00–05:15 is slack for a late bus and is not billed.
- The inputs table says the same. This matches the manifest parameter `hours_after_midnight: 5, basis "00:00-05:00 (to 05:15)"` and the evaluator's supplied 2,800 kWh. The manifest row's `deliverable_kwh: 2900` is the 7.25-hour window.

**L3: figures not followable. Accepted and fixed as a class.**
- Ruiru absorbing 6 buses: 6 × 140 kWh × 31 nights = 26,040 kWh × 0.12 = 3,124.80, all off-peak, with the highest kW unchanged at 380.
- All other figures in §7 were swept. Arithmetic from shown inputs was added for:
  - Lakeside: the "of which" columns; 7,545.00 = 8,245.00 − 700.00.
  - Kisiwa: hours (25 / 3 / 21 days × 5 h).
  - Mto: 30 L / 10 L extra; half-capacity hours (22 / 6 / 2 / 25 days × 5 h); welding fuel 217.8 L × 1.25; billing 140 kWh × 0.40 and 12 × 56.00.
  - Lakeside sensitivities: each recomputed at 1.00 a litre or 160 L, with the per-option values anchored to `options.*.sensitivities`. The downside and all four switch-case spends and values are also shown.
  - Mwea: 0.6%; the contract's revenue and energy lines; capacity 4,340 + 4,500 against 12,400.
  - Harvest: 37,200 = 3 × 12,400; the cost change −150.00; 97.8%; energy per crate-day for Mwea and Kirinyaga; 24%.
  - Kirinyaga: replacement 970 + (1 − 0.95) × 4,030; 60% recovery case.
  - Mwea: downside and switch spend.
  - EV deliverable energy: the lower of chargers × kW and the import limit, × window, at all three depots.
  - Embakasi: bill lines as kWh × price; cost per departure.
  - Kasarani: 37,200 kWh; 150 kWh short.
  - Ruiru: cost-to-serve sum; 13,100.00 − 13,080.32.
  - Portfolio: deviation; cost per departure; 99.3%.
  - Embakasi options: the 706.80 tier drop (23,560 × 0.03); the cheapest-bill 12,975.00 and the 93 departures; Ruiru's 62 departures; 4 × 15,000.
  - Metro: downside and switch.

**L4: small presentation points.**
- Welding break-even: fixed. It now reads "272.25 ÷ 660 = 0.4125 per kWh, above the 0.40 charged". The manifest row still carries `break_even_tariff_usd_per_kwh: 0.42`, rounded up. The evaluator does not use it, so the manifest is left as it is; this is reported, not changed.
- Thika factor table: fixed. It now carries the Price column.
- Mwea "+155.00 − 3.00": **kept, with proof.** Writing +152.00 makes the checker fail: "main §2-§10: figures are independent values or declared inputs (untraced: ['152.00'])". 152.00 is a subtotal that does not exist in the data. The cell already shows its arithmetic, and the column total −150.00 is a data record. For the same reason, 8,840 and 1,171.5 are shown only as their sums (4,340 + 4,500; 970 + 201.5) and never printed as totals.

**L5: system vocabulary. Accepted and fixed in §7.**
- "The allocator" is replaced by a plain two-step description of how the plan is built.
- "must-do" is replaced by "required: …" with the reason.
- "hard bound", "cover bound", "backup-cover bound" and "departures bound" are replaced by what would happen ("the warranty cover would be lost", "2 departures missed; every departure must be met", and so on).
- "obligation hours without redundancy" is replaced by "hours of evening supply with no second generator in reserve".
- "All of these are outputs of `evaluate_structure.py`" is replaced by "Every figure in this table is Calculated: the plan is searched again under each pair of conditions".
- "not decomposed" is replaced by "cannot be split into factors".
- "dispatch classification" is replaced by "classifying each generator interval".
- "the decision's reference" is replaced by "the comparison stated for that decision".
- "switch cases" is replaced by "When a condition changes (the switches)", with the conditions named.
- The internal IDs v7.0 INC-203, ACT-051, F-130 and WR-019 are removed.
- What is kept: asset tags, tariff codes and document numbers (GEN-KS-01, INV-MT-02, CH-K2, C-114, CN-0412, B-1031). These are what an operator sees on site and on paper. Also kept: the legend's pointer to `evaluate_structure.py` / `independent_model.py`, which is design-document provenance.

**Not reconciled / for the owner's attention:**
- About 20 option inputs are held in the demo data with no stated source; they are listed under L1. They are now labelled as such. Giving them a source (quote, record or assumption) is a data task, not a document fix.
- The evaluator's `MWEA-AGG.assumptions` list is empty, although its handling basis reads "handling estimate". The document labels it Assumption.
- Manifest `break_even_tariff_usd_per_kwh: 0.42` is a rounded-up value (exact 0.4125); see L4.

## Author response to the re-review of §7 fixes (5ac8c6f69)

Architect (Claude), 18 Nov. The owner approved addressing every finding. Each one was handled as a class across §7. The changes are inside §7 only, in the .md and in the .html (re-rendered with the same renderer, which was first confirmed to reproduce the current file byte for byte). No manifest, evaluator, model or checker change was needed.

**M1: plan search described as two steps. Accepted and fixed as a class.**
- §7.1 Choose 1 now carries one description that matches §2 (`:182`) and `evaluate_structure.py` `best()`:
  - one search over all the decisions together, taking one option per decision; a money-valued decision may take none, except the Mto inverter (`optional: false`);
  - an option that breaks one of its decision's rules (a service rule, or keeping warranty cover) is left out, unless no option of that decision can keep the rule (Kisiwa's `least_violation` fallback; `candidates()`);
  - a combination must fit the budget and the crew visits and meet the dated dependency;
  - the plan is the combination that breaks the rules least, then is worth most, then spends least (`key = (-pen, v, -spend)`).
- §7.2 and §7.3 Choose 1 now say "found as at Lakeside: one search over all the decisions together", with the same ranking. The old "backup-cover decision first, then …" (§7.2) is gone. §7.3's "order of action" is kept, but it is now labelled as the order the chosen items are acted on (Declared input: manifest `priority_order`), not as how the plan is chosen.
- Other sentences describing the choice:
  - The intro now says Choose "searches all the options together".
  - The Kisiwa note now says every option breaks the rule, so all three stay in the search, and the search breaks the service rules least before it weighs money.
  - "required: …" (Kisiwa, Thika, Kasarani) wrongly implied a separate first step. It now gives the reason in the search's terms ("fewest evening hours with no backup"; "the only option that keeps both the backup-cover rule and the warranty cover"; "the only option that misses no departure and keeps the cover").
- Every plan and switch row was re-checked against `best()`:
  - Lakeside 5,000 / extended: the claim and huller plan (3,750.00).
  - 6,500 / extended: the claim is still kept; buying now fits the budget, but it is worth less.
  - 6,500 / not extended: buying now with the huller (+3,508.50) beats claiming without it (+2,548.50).
  - 5,000 / not extended: one combination with a higher value exists. Dropping the Kisiwa repair for no action frees enough to buy now and keep the huller (spend 430 + 90 + 2,910 + 1,200 = 4,630, 2 crew visits). It loses because it leaves 125 evening hours with no backup instead of 15, and least rule-breaking comes first. That is the row the old two-step text could not explain, so one sentence now says it under the switch table.
  - Harvest Cold (both cases) and Metro Bus (both cases) follow from one admissible option per protective decision and the value ranking.

**L1: inputs without a label. Accepted and fixed.**
- Crew visits per item: the column is now "Crew visits (Declared input)" in all three Choose tables. Each value is the manifest's per-option `crew_visits`; bracketed reasons (remote, contractor) are kept where the data gives them.
- Ruiru: "added buses charge off-peak; the highest kW stays at 380 kW" is now an Assumption row in Ruiru's inputs (the model's change rule; RUI-ABSORB6 changes only `kwh_2200_2400`).
- Dates: the §7 intro states once that every decision is taken on 6 Nov, the demo's today (Declared input: manifest `as_of`), and that Protect effects are counted to 30 Nov (Plan limit). Kisiwa's 30 Jun warranty end and the missed 1,000-hour service (1,240 run hours) are a Record row in Kisiwa's inputs.
- Others found in the sweep and labelled:
  - the 2% fuel tolerance (Kobo) and the 5% energy tolerance (Mwea): Declared input;
  - the service obligations behind Kisiwa's evening hours and Mto's daytime hours in Observe: Record;
  - Mto's observed 20 half-capacity hours: Calculated from the fault log;
  - departures met at Embakasi, Kasarani and Ruiru: Record;
  - the Mto warranty term (2029) and the Kobo battery warranty term (2034): Record, now in their inputs rows;
  - the Kisiwa O&M credit basis: Record, now on its "listed beside" row.

**L2: litre split labelled unevenly. Accepted and fixed.**
- Every row or sentence that gives part of the necessary / candidate / unexplained split now reads "Declared input, *stands in for a calculation*": Kobo (three factor rows and the two split steps), Kisiwa (prose and both factor rows) and Mto (prose and its factor row).
- The unexplained litres carry the qualifier too. In the manifest they are a typed leaf (`record.unexplained_l`), not computed from consumed minus modelled, although they agree with it.

**L3: readability. Accepted and fixed.**
- The three long "Inputs to the options" tables are gone. Each decision now has its own inputs table directly above its option table (Lakeside 6, Harvest Cold 3, Metro Bus 3). Each row keeps its label.
- With the inputs above, the option cells no longer repeat the inputs' labels.
- Sensitivities now have one row per option the case moves, with the plan total on its own row. This applies to Lakeside (diesel −20% and 160 L) and Harvest Cold (60% recovery). The downside rows use the same layout.
- No new material, apart from the M1 sentence under the switch table. Duplicated text was cut:
  - the Kobo meter note (its point is already in the 1,060 L row);
  - the three Evaluate input preambles;
  - the checker-provenance sentence in the legend;
  - Kasarani's restatement of its contract terms in the heading.

**L4: one name per measure. Accepted and fixed.**
- Kisiwa: "evening hours with no backup" throughout ("no second generator in reserve" is removed).
- Mto: "daytime hours at half inverter capacity" throughout ("half capacity" is aligned).
- Thika: "nights with stock and no backup cover" throughout (the Observe sentence and the Wait row are aligned).
- Kobo: "days with dawn charge below 35%" (the service-rule row and the Reserve row are aligned).
- The plan total in the three "valued in money" tables is now "The plan" in the 12-month value column. It was "Modelled 12-month change", a second name for the value shown in the sensitivity and switch tables; the modelled caveat stays in the sentence below the Lakeside table.
- "Technician visits" is now "crew visits" throughout.
- "One-off borne by the operator" is now "One-off", defined once in the 7.1 Evaluate intro.
- The Metro portfolio columns are now "Plan cost to serve / Actual cost to serve".
- The meter-reading note no longer gives the whole-number reason. The 1,060 L row says the generator-energy reading is not in the demo data, so it cannot be shown.

**Checks.**
- `python3 check_manifest.py`: **3674 passed, 0 failed**. It was 3,680 before. §7 now has 491 figure anchors instead of 497 (net 6 fewer): those that went were on text that restated an input next to its own inputs row.
- Every anchor path present in §7 before is still present.
- §7 word count (anchors stripped): 9,175 before, 9,233 after. The L1 labels, the inputs-table headers and the M1 rule cost more than the cuts saved.

**Not reconciled / for the owner's attention.**
- Outside §7, two texts still describe the search in the old two-step way. Both are left unchanged because this round is scoped to §7:
  - the manifest's `plans:` header comment ("protective: the cheapest option meeting its hard bounds is chosen …"), a comment only;
  - §2 "Job" (`:176`, "after **must-do** options that hard bounds require").
  §2 `:182` and the evaluator are correct.
- The earlier response's L5 note that "must-do" became "required: …" is superseded. See M1 above.
