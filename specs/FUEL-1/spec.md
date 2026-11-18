# Build sheet FUEL-1: mill dollars, the mill on the board, Portfolio value lines, money wording, idle fuel (Option A), and the diesel-heavy story

- Architect: Claude (fresh Architect, FUEL-1), 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `da40bf5e7`. Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `T/` = `tools/`.
- Owner decisions, verbatim (`.agent/owner-fuel-scope-2026-11-07.md`):
  - scope: "Both (~5.4 units) (Recommended)" (shortlist items 1–4 and Option A idle fuel, before the demo script);
  - idle rate: "Generic 3.3 L/h, labelled (Recommended)";
  - example tank: "Leave it, explain in 'Why?' (Recommended)";
  - diesel-heavy story: "inject days, i don't see why it should be mutually exclusive". Read as: build it as well, not instead. Timing and form go back to the owner with sizes (section 5 and section 7).
  - The mill goes on the main board. `.agent/owner-mill-route-2026-11-07.md` ("Fix link, use route") is superseded; BL-45 comes out of the backlog.
- Design basis: `.agent/feature-shortlist-2026-11-07.md` (items 1–4, B5, B6, B8) and `.agent/fuel-story-design-2026-11-07.md` (Option A, B2 probe, B3 options (i) and (ii), B5 literals, B6 fit). This sheet supersedes both where they differ.
- Rules that apply to every unit:
  - SCOPE-1: only what we can present defensibly.
  - Money comes only from evidence and declared prices. Never tune a number. Expected values are computed from the inputs, never typed from a run.
  - Never add money with different bases (v69 `:131`, `:482`). Never annualise.
  - The mock is the layout spec. Label every deviation MOCK DEVIATION, with an id, in a code comment and a packet row.
  - Localised tests only. No full suite, no prepare (except A3's one Kobo-only scratch prepare, below), no baseline build. Every test runs on its own `*_test` DB. Never `assetops_demo3_full_test`. No `-ExecutionPolicy`.
  - Each unit: own Opus first build and first review, Sonnet fix rounds and re-reviews. Pre-flight questions are batched into one message before any code.

---

## 1. Units, lanes, order and conflicts

### 1.1 Units

| Unit | What the client gets | Size | Lane | Depends on | Files (main ones) |
|---|---|---|---|---|---|
| **MV-1** mill dollars on the verdict page (item 1) | "About 17.00 USD a day more in estimated sales…" under "Target met", and "No cost is recorded for this change" | 0.5 | 1 | none (starts now, beside CH-5d1) | `B/actions/verification_families.py`, `B/actions/verification.py`, `B/actions/composition.py`, `B/financials/composition.py`, `B/financials/fuel_cost.py` (two keyword arguments only), `F/sites/SiteMillVerification.tsx`, `F/sites/millVerificationClient.ts`, `T/demo_combined_finish.py` (one row) |
| **MB-1** mill on the main board (item 2, BL-45) | The Kobo board shows the mill change with its thread line and verdict link; the Assure row and the Portfolio count include it | 1.25 (1.0–1.5) | 1 | CH-5d1 merged | `B/site_outcomes/board.py`, `B/site_outcomes/mini.py`, `B/chain/claims.py`, `T/checks/chain_coherence.py`, the board, Portfolio and COH tests |
| **WD-1** money wording (item 4, BL-48) | Kobo month sales line and the Depot fault-day income line say plainly why there is no figure | 0.15 | 1 | CH-5d1 merged (`chain/vocabulary.py`) | `B/chain/vocabulary.py:268`, `B/site_outcomes/mini.py` (`MG1_ACTUAL`), `B/site_outcomes/ev.py:229` |
| **PV-1** Portfolio verified-value lines (item 3) | The Assure card lists one value line per verified result, each with its own basis, and never a total | 0.75 | 1 | MV-1, MB-1, A2, CH-5d1 merged | `B/site_outcomes/read.py` (`portfolio_cards` Assure), `B/site_outcomes/mini.py` (Assure node values), `B/estate/portfolio.py` (`card_notes`), `B/chain/vocabulary.py` `CARD_TEXT`, `F/estate/PortfolioOutcomes.tsx`, COH-17 |
| **A1** fuel-cost-2 and the declared no-load fact | Nothing visible yet; the reviewed model that counts idle running | 0.85 | 2 | none (starts now, beside CH-5d1) | `B/sites/models.py` (vocabulary and carriers), `B/financials/fuel_cost_v2.py` (new), the consequence store and recompute, migration `0053`, model-id readers |
| **A2** trial-fuel-comparison/2, priced total, no-sum credit | Nothing visible yet; the trial's fuel change stored in litres and USD; the Portfolio rule never adds results | 0.55 | 2 | A1 merged | `B/actions/verification_rules.py` (window idle seconds), `B/financials/trial_fuel_comparison.py`, `B/actions/verification.py` (`_cost_check`, `_cost_check_read`), `B/outcomes/credit.py`, `B/estate/portfolio.py` (`recovered`) |
| **A3** idle fuel on Kobo's screens and story | Three "0 USD" mornings become idle-fuel lines; the trial's verdict shows litres and USD saved, labelled modelled and generic | 0.7 | 2 | A2 and MB-1 merged | `T/demo_combined_kobo.py` (declare the fact), `B/site_outcomes/mini.py` and `board.py` copy, the trial verification page, finish rows, COH; one Kobo-only scratch prepare |
| **E3 allowance** | finish-row runs and recaptures of the changed screens inside E3 | 0.35 | end-game | all of the above | none |
| *(done)* idle-fuel probe | | 0.25 | | | `.agent/fuel-story-design-2026-11-07.md` B2 |

**Remaining build: 5.1 units** (2.65 lane 1, 2.1 lane 2, 0.35 E3). With the probe already spent: 5.35, which is the owner's "about 5.4".

### 1.2 Order and parallel work

```
now:            CH-5d1 (in build, lane 2 worktree)   |  MV-1 (lane 1)   |  A1 (lane 2b)
after CH-5d1:   MB-1 (lane 1)                         |  A2 (after A1)
after MB-1:     WD-1 (lane 1, 0.15)                   |  A3 (after A2 and MB-1)
after A2+MB-1+MV-1:  PV-1 (lane 1)
then:           E3 allowance rows written (inside A3 / PV-1), DS-1, E1–E6
```

- Lane 1 = MV-1 → MB-1 → WD-1 → PV-1 (2.65). Lane 2 = A1 → A2 → A3 (2.1).
- A3 must not start its copy edits before MB-1 merges (shared `board.py` and `mini.py`). Lane 2 reaches A3 at about 1.4 units, while MB-1 finishes at about 1.75 on lane 1. The A3 builder starts with the parts that touch neither file (the Kobo declaration, the finish rows, the scratch-prepare plan) and rebases before the copy edits.
- MB-1's pre-flight (reading and measurement, no code) may run while CH-5d1 builds. MB-1 code starts only after CH-5d1 merges.
- Three builders run at once only during the "now" row (CH-5d1, MV-1, A1). Their files are disjoint.

### 1.3 File-overlap conflicts

| Pair | Shared file | Resolution |
|---|---|---|
| CH-5d1 ↔ MB-1 | `T/checks/chain_coherence.py`, `backend/tests/test_ch6b2_portfolio_cards.py` | MB-1 code starts after CH-5d1 merges |
| CH-5d1 ↔ WD-1, PV-1 | `B/chain/vocabulary.py` (CH-5d1 adds `CARD_TEXT` cost keys and `COST_SMALL`) | both after CH-5d1 |
| CH-5d1 ↔ PV-1 | `B/site_outcomes/read.py` `portfolio_cards`, `F/estate/PortfolioOutcomes.tsx` | PV-1 after CH-5d1; PV-1 edits the Assure card only, and the CH-5d1 Optimize card stays byte-equal |
| **CH-5d1 ↔ A3 (data, not files)** | none | After A3, Kobo's Optimize row `nodes.earnings` (`money.possible_extra_fuel_cost`) is **priced above zero** on the three idle mornings. So the CH-5d1 Optimize card will show a money value at E3, not the "Not known yet" that CH5d1-R §4 forecast. That is the intended effect of Option A, and CH-5d1's code does not change. CH5d1-R §4 "Owed at E3" is superseded by A3's finish rows (section 4.3). Tell the CH-5d1 lane; it needs no edit |
| MV-1 ↔ A1 | `B/financials/fuel_cost.py` | MV-1 adds two keyword arguments to `select_window_price`. A1 puts fuel-cost-2 in a **new module**, `fuel_cost_v2.py`, and does not edit `fuel_cost.py`, so there is no conflict |
| MB-1 ↔ A3 | `B/site_outcomes/board.py` (`cost_line`), `B/site_outcomes/mini.py` (`COST_ZERO`, `VERIFIED_WITH_COST`) | A3 copy after MB-1 merges |
| MB-1 ↔ PV-1 | `B/site_outcomes/mini.py` Assure row | PV-1 after MB-1 |
| A2 ↔ PV-1 | `B/estate/portfolio.py` (`recovered`, `card_notes`) | PV-1 after A2. **Between A2's merge and PV-1's merge, main may show no recovered-value clause on the Assure note** (A2 makes the credit list per result, and the clause text is None while CREDITED). No demo build runs in that gap. PV-1 restores the clause |
| A1 ↔ A2 | migration | **One migration, `0053`, in A1**, carries both units' CHECK changes (section 4.1). A2 adds no migration, so there is no alembic-head race |

---

## 4. Lane 2 unit cards (Option A, idle fuel)

### 4.1 A1: fuel-cost-2 and the declared no-load fact, 0.85

**Foundation vocabulary (`B/sites/models.py`):**
- `"generator-no-load-fuel-rate": PropertyDefinition(unit="L/h", kind="PHYSICAL", display_name="Generator no-load fuel rate")`.
  - Comment: a no-load rate is defined at one operating point, zero load, which is exactly what it states. The `:75` argument against L/h applies to SFC and is unchanged. The parser still refuses SFC in L/h.
- `"generator-no-load-fuel-rate-basis"`: a state property, `STATE_PROPERTY_VALUES["generator-no-load-fuel-rate-basis"] = frozenset({"GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_TEST"})`, unit `"state"`.
- Both are carried by `GENERATOR`, added to `MINIGRID_PROPERTY_CARRIERS` (`:312`).
- The basis travels with every later Foundation revision, because additive publishes keep the other properties. So the "generic" label is data the Site declared, never product copy.

**fuel-cost-2 (`B/financials/fuel_cost_v2.py`, new; `fuel_cost.py` untouched):**
- `MODEL_ID = "fuel-cost-2"`. A new immutable `PARAMETER_VERSION`:
  - `parameter_version = "fuel-cost-2/sfc-upper-multiplier-and-no-load/v1"`, value 1.10, applied to both terms;
  - formula: `quantity_low = 0 L; quantity_high = 1.10 × [Σ_loaded P_j·h_j·SFC_j + Σ_idle h_j·r_j]`. An idle interval is a selected reading whose accepted GOOD mean is exactly 0 kW, wholly inside observed Candidate time; Candidate time is generator-running time by the dispatch classification. `r_j` is the single positive `generator-no-load-fuel-rate` of the generator in the reading's as-accepted Foundation revision, valid over the whole interval;
  - author "Claude Architect (FUEL-1)"; reviewer = the A1 review file;
  - source: this sheet and `.agent/owner-fuel-scope-2026-11-07.md`.
- **Selection:** fuel-cost-2 applies to a Finding revision **iff** at least one counted reading's as-accepted Foundation revision declares `generator-no-load-fuel-rate` on the generator. Otherwise `fuel_cost.quantify` runs exactly as today, so every existing fixture and test stays fuel-cost-1 and byte-equal.
- **Inside v2:** the v1 checks run in v1's order, then the new checks:
  - an idle reading whose revision has no rate → `QUANTITY_UNAVAILABLE` `NO_LOAD_RATE_MISSING`;
  - more than one distinct rate → `NO_LOAD_RATE_CONFLICT`;
  - a rate ≤ 0 or a unit other than L/h → `NO_LOAD_RATE_INVALID`;
  - no basis property → `NO_LOAD_RATE_BASIS_MISSING`.
- **Loaded intervals compute exactly as v1.** `CountedInterval` gains, in a v2 subclass, `idle: bool`, `no_load_l_per_h: Decimal | None` and `no_load_basis: str | None`. The v2 `litres` = `h × r` when idle, else v1's.
- `LIMITATIONS_V2` = v1's four lines, with line 3 reading "…specific fuel consumption, and the declared no-load fuel rate for running at 0 kW (fuel-cost-2 reviewed modelling allowance)", plus a fifth line: "Running at 0 kW inside Candidate time is counted at the declared no-load fuel rate; a generic rate is not this generator's own figure."
- The technical digest adds the model id, r, the basis and the idle flags.

**Migration `0053_fuel_cost_2.py`** (one migration for A1 and A2):
- `financial_consequence` (0011): `model_id IN ('fuel-cost-1','fuel-cost-2')`; nullable `no_load_fuel_rate_l_per_h numeric`, `no_load_fuel_rate_basis text CHECK IN (the three)`, `idle_seconds integer CHECK >= 0`; CHECK `model_id = 'fuel-cost-1'` ⇒ all three NULL.
- The trial cost table (0037 `TABLE`): `formula IN ('trial-fuel-comparison/1','trial-fuel-comparison/2')`; the REASONS CHECK widened by `NO_LOAD_RATE_DIFFERS` and `IDLE_SECONDS_UNKNOWN` (A2).
- Downgrade restores both. Run the single-alembic-head test.

**Store, recompute, readers:**
- The consequence store reads the two properties from each Foundation revision it already reads for SFC, and writes the new columns.
- Recompute calls the selection.
- PRE-FLIGHT lists every reader of the literal `fuel-cost-1` with a disposition: `B/finding_api.py:328`, `:352`; `B/site_overview/read.py:39`; `B/outcomes/outcome_map.py:164`; `B/mini_depth/rules.py:636`; `B/financials/recompute.py`. **Stop if any reader filters rows on `model_id = 'fuel-cost-1'`**, because it would silently drop v2 rows. Copy that names the model shows the stored row's model id.

**Tests:**
- new L0 `backend/tests/test_fuel_cost_v2.py`:
  - no rate → v1 selected and bytes equal;
  - idle-only, 200 min at 0 kW with r = 3.3: `high_exact == Fraction(11,10) * Fraction(200,60) * Fraction(33,10)` (= 12.1 L);
  - loaded-only with r declared: litres equal v1's;
  - mixed;
  - each of the four new refusals;
- parser tests (L/h accepted for the no-load rate and still refused for SFC; the basis states; carrier GENERATOR);
- L2 store round trip and migration up/down on own `assetops_a1_test`;
- `test_s4_fuel_cost.py` and `test_s4_consequence_*` unchanged and green.

**Stops:**
- adding the vocabulary changes any scenario, run-contract or handover digest in the contract tests (`test_scenario_execution_contract.py`, `test_execution_contract_alignment.py`);
- a reader filters on model id;
- more than 1.1 units.

### 4.2 A2: trial-fuel-comparison/2, priced total, no-sum credit, 0.55

- **Window idle seconds** (`B/actions/verification_rules.py` `window_evidence`, `:378-536`):
  - `generator_idle_seconds` = Σ `SLOT` seconds over slots whose sampled `generator_state` value is `"RUNNING"` (`analytics/dispatch.py:97`) and whose slot generator kWh is exactly 0. It is None if any such slot is unknown.
  - It gets the **same exclusion from `plan_sha256` and stored details as `gen_total`** (`:432` comment).
  - Stop if any existing plan digest or stored detail byte changes.
- **`trial_fuel_comparison.py`:**
  - `FORMULA_V2 = "trial-fuel-comparison/2"`;
  - `WindowFacts.idle_seconds: int | None = None` (the default keeps v1);
  - `compare(..., no_load_in_force=())`: v2 iff a no-load rate is in force over both windows;
  - window fuel = SFC × gen_kWh + r × idle_seconds/3600, the upper = × MULTIPLIER as v1;
  - new reasons, appended after `SFC_DIFFERS`: `IDLE_SECONDS_UNKNOWN`, `NO_LOAD_RATE_DIFFERS`;
  - on `MODELLED_IMPROVEMENT`, the result gains `priced_total = {"amount": fmt(cost_b_nominal - cost_l_nominal), "currency", "basis": "TRIAL_HOUR_MODELLED_FUEL", "window": [later_start, later_end], "fuel_change_l": fmt(fuel_b_nominal - fuel_l_nominal)}`;
  - `LABEL` unchanged ("Modelled change after the trial · not realised savings"). No annualising.
- **`verification._cost_check`:** pass the idle seconds and the no-load history (a `store.no_load_history` beside `sfc_history`).
- **`_cost_check_read`:** additive `priced_total`.
- PRE-FLIGHT checks where `COST_CHECK_SOURCE` ("Generator stop setting changed; no direct cost declared", `:49`) is shown. ACT-001 changed the battery reserve, not the stop setting. If a client screen shows the text, report it as a finding; do not rewrite stored data.
- **`B/outcomes/credit.py:74-96`, the owner-requested fix:**
  - `recovered_value` never sums. It returns `{"state": "CREDITED", "text": None, "items": [{"key": <outcome id>, "currency", "amount": _wire(amount), "basis": <priced_total basis>} per credited item]}`;
  - `"amounts"` is removed. PRE-FLIGHT greps its readers (`frontend/src/estate/estateClient.ts`, `portfolioFixtures.ts`, `test_w303_*`, `test_ch3_rows.py`) and updates them by the same rename;
  - fail loud on two items with the same key.
  - Tests: two credited items in the same currency → two items, and no field equals their sum.
- **Expected demo figures (computed in tests from the inputs, never typed from a run):** trial hour baseline 12 slots RUNNING at 0 kWh, later 0 slots, r = 3.3:
  - `fuel_change_l` 3.3;
  - `priced_total.amount` 3.3 × 1.25 = 4.125, shown by `money2` as 4.12 USD;
  - per kWh of demand 0.275 USD/kWh (15 kWh).
- **Tests:** `test_out_e*` cost-check tests green; a new `test_tfc2.py` (v1 byte-equal without a rate; idle only; loaded only; mixed; both new reasons; priced_total); the credit no-sum tests.

### 4.3 A3: idle fuel on Kobo's screens and story, 0.7

**Declaration** (`T/demo_combined_kobo.py`): `declare_no_load_rate(foundation, result, install_at)`, called in `configure_at` after `declare_supply_uses`.
- One `publish_component_properties` on the generator asset (PRE-FLIGHT: its asset code), `effective_from = install_at + CONFIG_OFFSETS["uses"]`.
- Properties `[{"property_key": "generator-no-load-fuel-rate", "value": 3.3, "unit": "L/h", "source": "SITE", "source_version": 1}, {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state", "source": "SITE", "source_version": 1}]`.
- Note: "Generic no-load fuel rate for a 40 kW diesel set (common design-software default, about 0.08 L/h per kW of rating); not this generator's datasheet. Owner decision 2026-11-07."
- The value 3.3 is the owner's; the source is the HOMER-style generic intercept, about 0.0815 L/h per kW × 40 kW. Never change it to reach a figure.

**Copy (all server-side; guard V; literals):**
- **Finding / board day line**, replacing `COST_ZERO` (`B/site_outcomes/mini.py:64-65`) only for a fuel-cost-2 PRICED row with idle seconds above 0. Fuel-cost-1 rows keep `COST_ZERO`.
  - `COST_IDLE = "Generator ran {h} with no load: up to about {l} L, {amount} of possible extra fuel · counted at {basis} of {r} L/h, not measured"`;
  - `{basis}` from `NO_LOAD_BASIS_WORDS = {"GENERIC_DEFAULT": "a generic no-load rate", "MANUFACTURER_DATASHEET": "the datasheet no-load rate", "SITE_TEST": "the site-tested no-load rate"}`;
  - `{h}` is the duration text helper the board already uses (PRE-FLIGHT names it), `{l}` is one decimal, and `{amount}` is `money_text`.
- **Board Optimize cost line** (`board.py:497-509` `cost_line`): when the cost check carries `priced_total`, `COST_PRICED = COST_PREFIX + "about {l} L less diesel in the trial hour, {amount} at {p} {cur} per litre."`. Without it, today's lines are unchanged.
- **Assure** `VERIFIED_WITH_COST` (`mini.py:96`, `:986-988`): with `priced_total`, the same litres-and-amount clause replaces the per-kWh clause.
- **Trial verification page** (the ACT-001 page): one line under the verdict, "About {l} L less diesel in the trial hour, about {amount} at {p} {cur} per litre · modelled from a generic no-load rate, not measured by a fuel meter" (basis words as above).
  - **MOCK DEVIATION MD-FUEL-A3-1:** v69 `:498-505` shows no money on Verification.
- **"Why?" line** (owner decision 3), on the Optimize row's "Why?" where the idle line shows: "The example data does not count fuel while the generator idles; this estimate does, at the declared no-load rate, so the two differ."
- **Readiness "Generator fuel curve"** (v69 `:426`), only if that row exists on main (PRE-FLIGHT greps). If it does not, nothing is added; that is not a mock gap this unit owns.

**Finish rows (written now; run at E3):**
- **MONEY-B / O16:** S-14, S-7 and S are PRICED fuel-cost-2. `quantity_high` = 1.10 × (stored Candidate idle seconds / 3600) × 3.3, computed from the stored segments and readings. The amount equals that × the stored price.
- **PROBE_CHOSEN** (`T/demo_combined_finish.py:39-40`): the cost state becomes `MODELLED_IMPROVEMENT`, and `fuel_change_l` = 3.3 × (stored baseline idle seconds − later idle seconds) / 3600.
- **CH-5d1:** the Optimize card on S equals the one priced Site's claim text (replacing CH5d1-R §4's "Not known yet" forecast).
- **COH-17:** unchanged rules, new data.

**One Kobo-only scratch prepare** (approved with Option A: "one Kobo-only trial build is needed first"):
- `--sites kobo` on own `assetops_fuel_a3_test`, with the keep-awake script running;
- confirm the stored figures equal the computed ones (B2 table at r = 3.3: 11.0 L nominal per morning, 12.1 L upper; trial hour 3.3 L);
- confirm no scenario, handover or run digest changed;
- then drop the DB and its var folder. Cap 1 h; it takes about 20–30 min.

**Stops:**
- a digest changes;
- the stored idle seconds differ from the probe's 200 min per morning or 12 slots in the trial hour (that is a data finding, never a retune);
- more than 1.0 unit.

---

## 5. The diesel-heavy story (owner: "inject days")

### 5.1 Form: a fourth Site, "Kisiwa", a diesel-hybrid island mini-grid (recommended over a Kobo extension)

**Why not extend Kobo (option (i)):**
- The new days would sit inside the mill's 3+3 checked-day windows (mill change S-9) and the recurrence span.
- Four earlier attempts at a Kobo trial that both shows a lever and passes its check failed (`.agent/DEMO-SPARSE-trial-probe.md:63-126`).
- Every Kobo count that passes today (SP-3 gap 24, MILL-3, the recurrence, COH) would move.
- Kobo is mostly solar, so the numbers stay small.

**Why a fourth Site:**
- Kobo's checks are isolated by construction.
- Diesel is the main source there, so the numbers are CFO-sized and honest.
- It reuses Option A's fuel-cost-2 unchanged.

**The cost of a fourth Site:**
- a four-Site Portfolio. **MOCK DEVIATION MD-FUEL-D-1:** v69 `:131` shows "3 priority sites";
- Site navigation;
- layout recaptures;
- new finish rows.

### 5.2 Stated physical assumptions (declared before any probe; never tuned)

| Item | Value | Basis |
|---|---|---|
| Template | new `config/site-templates/kisiwa-diesel-hybrid-60kw.yaml`, built from Kobo's component and topology pattern | |
| PV / inverter | 20 kWp / 20 kW AC | small array on an island site |
| Battery / PCS | 60 kWh, reserve 30 %, PCS ±20 kW at 95 % | |
| Generator | 60 kW (75 kVA prime). Start 35 %, stop 90 %, minimum runtime 30 min, start delay 5 min (Kobo's control values) | |
| SFC | **0.355 L/kWh**: the generic fuel curve F = 0.08145 L/h per kW rated + 0.246 L/kWh × P, evaluated at 75 % of rating (45 kW): (4.887 + 11.07) / 45 | One stated rule, at the common prime rating point. Partial-load running is then under-counted, which is conservative |
| No-load rate | **4.9 L/h**, basis `GENERIC_DEFAULT` (0.08145 × 60 = 4.887) | The same generic rule as Kobo's 3.3 L/h |
| Tank | 1000 L, not published (no tank signal; see 5.4) | |
| Diesel price | **1.25 USD/L**, Kobo's declared demo price, one publication | The same declared price; island transport premium not assumed |
| Load: households | 2 kW 06–18, 8 kW 18–23, 3 kW 23–06 (85 kWh/day) | |
| Load: cold store (ice / fish) | 4 kW constant (96 kWh/day). It is the critical load, so its unserved energy is a guardrail | |
| Load: water pump | 6 kW 19:00–23:00 (24 kWh/day), today's habit | |
| Solar | the same irradiance day-kinds as Kobo's calendar for the same dates (normal / overcast), scaled to 20 kWp | Weather is not chosen per outcome |

- Load ≈ 205 kWh/day; sunny PV ≈ 100 kWh/day. So about 100 kWh/day is diesel, roughly 35–40 L/day and about 1,100 L a month. This is an estimate to be measured by the probe, not a target.
- **Where the avoidable diesel comes from (stated physics):**
  - The evening load drains the battery to the 35 % start at about 21:00.
  - The generator then carries the load and charges at the PCS limit until 90 %.
  - Once SOC is above reserve + 10 points and the battery could carry the load, the dispatch classifier (`B/analytics/dispatch.py:44-63` thresholds) marks the running as Candidate avoidable. That is loaded diesel spent filling a battery the next morning's sun would partly refill.

### 5.3 Lever and before/after verification

- **Lever: owner question Q3**, both options declared before the probe:
  - (a) **stop the generator at 60 % instead of 90 %** and let the sun finish charging (v69 ACT-048 / CHG-019, `:335`, `:431-433`);
  - (b) **pump water at 10:00–14:00 instead of 19:00–23:00**.
  - If the probe shows that the chosen lever does not lower modelled diesel, we report it and do not swap levers silently.
- **Verification:** a new family, `generator-night-fuel-1`, built on the mill family's day choice (`choose_days`, 3 + 3 COMPLETE days, 14-day look limits; `B/actions/verification_families.py`). It is not the one-hour reserve trial, which is the path that failed four times.
  - Metric: modelled diesel litres per night (18:00–06:00 local), by fuel-cost-2's rule, from accepted readings: loaded SFC × kWh plus idle h × r.
  - Target: **owner-declared before the probe** (Q2), for example "at least 20 % less modelled diesel per night".
  - Guardrails: no unserved cold-store energy in either window, and sampled SOC never below the reserve.
  - Verdict page: a generic version of the mill verdict page, reusing its components.
- **Money on the verdict:** (mean baseline litres − mean later litres) × 1.25 USD, per night, "modelled from a generic fuel curve, not measured by a fuel meter". No annualising. The Portfolio line follows PV-1's per-basis rule (basis `NIGHT_MODELLED_FUEL`), never added to the mill or Kobo trial lines.
- **Measured tank or flow signal: not included.** The simulator's mini-grid law burns 0 L idle (BL-16), and no tank publication exists. A published tank would contradict the product's idle-inclusive estimate unless the simulator gets a Kisiwa-only law version and a tank publication (+1.0–1.5). That is post-demo, and it is the only path to the mock's "measured tank drop agrees with modelled" panel (v69 `:623-630`).

### 5.4 Screens (v69 as the layout spec)

- The Kisiwa Site board (the shared mini board; no new layout).
- The Finding fuel panel (v69 `:459`, `:468-472`).
- Financials assumptions (`:479-481`).
- The Change and Verification pages (`:431-433`, `:498-505`). MOCK DEVIATION MD-FUEL-D-2: money on Verification.
- Portfolio and estate pages with four Sites (MD-FUEL-D-1), and Site navigation.
- Layout evidence at 1440 and 390 for every changed page.

### 5.5 Finish rows, coherence, E3

- **New rows:**
  - KIS-1: Site, prices and declared facts;
  - KIS-2: Findings on the before nights, PRICED fuel-cost-2, `quantity_high` computed from the stored segments;
  - KIS-3: the verdict as computed. INEFFECTIVE is recorded truthfully and DS-1 tells it; it is never forced;
  - KIS-4: the money line reproduces from the shown means and price;
  - KIS-5: four-Site Portfolio counts;
  - KIS-6: CH-5d1's Optimize card on the "≥2 priced Sites" path (Kobo and Kisiwa), with no sum.
- **COH-17 and V4** extend to Kisiwa.
- **E3 prepare:** about 16 Kisiwa days (10 before nights including the baseline, the change day, 5 after). Estimate +15–25 min, giving about 1.3 h of the 3 h cap. One whole-list rehearsal prepare on its own `*_test` DB before E3 (about 1.3 h), as DD-1b2b did.

### 5.6 Units, size and risk

| Unit | Content | Size |
|---|---|---|
| D0 | In-memory probe (no DB), as `T/probe_kobo_nights.py` does: the 5.2 Site through the simulator for before and after nights under the owner's lever. Measure Candidate loaded hours, litres per night and the guardrails, and confirm the family's freeze rules accept the windows | 0.5 |
| D1 | Template, import, configure, prices, the no-load fact (reuses A1) | 0.75 |
| D2 | `generator-night-fuel-1` family: freeze, evaluate, read, verdict page | 1.5 |
| D3 | Authored calendar, scenarios, `demo_combined` child, story days, prepare list | 1.5 |
| D4 | Four-Site Portfolio, estate and navigation; mock deviations; recaptures | 1.0 |
| D5 | Finish rows, COH, rehearsal prepare, DS-1 beat | 0.75 |
| **Total** | | **6.0 planned, range 6.0–8.5 (plan figure 7.0)** |

**Risk:**
- **High on schedule and on the verification path.** The new family is new code, and the Kobo record shows trial windows can be refused at freeze. D0 de-risks this before any product code.
- **Medium-high on what passes today.** Every Portfolio and estate check, COH-17 and the all-26 layout audit gain a fourth Site.
- **Low for Kobo,** which is isolated.

**Honest assessment:** this cannot sensibly land before the demo **on the current date**.
- At about 7 units it is larger than everything else left combined (5.85 units).
- It changes the Portfolio checks and captures that pass now.
- Its verification path is unproven until D0.
- It can land before the demo only if the owner moves the demo by about 2–3 working days (two lanes at §15's rate, plus one extra rehearsal prepare) **and** D0 shows the lever lowers modelled diesel.
- Only the owner can trade those off. **Recommended:** run D0 (0.5, no product code, no risk to anything that passes) beside lanes 1 and 2 now, then decide with a measured size.

---

## 6. Plan delta (for the coordinator to carry into `Docs/demo-sprint/client-demo-plan.html`)

**New order:** CH-5d1 → {MV-1 ‖ A1} → {MB-1 ‖ A2} → {WD-1 ‖ A3} → PV-1 → DS-1 → E1–E6. With the diesel story before the demo: the D lane runs as lane 3 from now (D0 first) and merges before E1. Otherwise it runs after E6.

**Totals:**
- Before: ≈ 112.2 per the handoff, or ≈ 111.95 after CH5d1-R's −0.25 (CH-5d1 1.0 → 0.75).
- FUEL-1 adds +5.35: MV-1 0.5, MB-1 1.25, WD-1 0.15, PV-1 0.75, A1 0.85, A2 0.55, A3 0.7, E3 allowance 0.35, probe 0.25 (done).
- **New total ≈ 117.3.** Remaining before DS-1: CH-5d1 0.75 + 5.1 = **5.85**.
- With the diesel story before the demo: **+7.0 → ≈ 124.3**, remaining ≈ 12.85.

**Rows to change in the plan HTML:**
- Build-units table (around `:647-664`): add one FUEL-1 row before the DS-1 row (`:664`), "FUEL-1 mill dollars, mill on board, Portfolio value lines, wording, idle fuel (owner 2026-11-07)", 5.35. Add a "D-lane diesel-hybrid Site (owner timing question)" row, 7.0 est., marked conditional.
- Total row (`:665`): ≈ 117.3 (and lanes +5.0).
- G5 freeze (`:1172`) and G6 (`:1173`): +5.35, and the CH-5d −0.25 already owed.
- The lanes schedule table and figure (`:935`, `:968`): FUEL-1 lanes 1 and 2 between CH-5d1 and DS-1.
- Add a rulings-table row "FUEL-1" pointing to this sheet. Note BL-45 and BL-48 leave the backlog (`.agent/backlog-post-demo.md` rows 66 and 69 marked "scheduled FUEL-1"), and BL-16 is partly done (product side, Kobo).

---

## 7. Owner questions (plain language; for the coordinator to send)

1. **When do we build the diesel-heavy example?** It is a fourth example site, a diesel-hybrid island where the generator carries most nights. That gives large, honest fuel numbers without touching Kobo. It is about 7 units, more than all the other remaining work together, and it changes every Portfolio check that passes today. Options:
   - (a) after the demo;
   - (b) before the demo, moving the demo by about 2–3 working days;
   - (c) recommended: first a half-unit trial run of the new site in the simulator, beside the other work, which risks nothing that works now; then decide with a measured size.
2. *(Only if you choose (b) or (c).)* **What counts as success for the diesel change?** We need your pass mark before we run anything, so it cannot be chosen to fit the result. For example: "at least 20 % less diesel per night, averaged over 3 fully checked nights before and 3 after, with no power cut to the cold store".
3. *(Only if you choose (b) or (c).)* **Which change do we test at the diesel site?**
   - (a) stop the generator when the battery reaches 60 % instead of 90 %, and let the sun finish charging;
   - (b) pump water at midday instead of in the evening.
4. **Did the mill change have a real cost you can state, with where the figure comes from?** If not, the mill result page says "No cost is recorded for this change", which is true. If yes, we add a "pays back in N days" line (about a quarter unit).

Nothing else needs your decision. The idle-fuel work, the mill dollars, the mill on the board, the Portfolio lines and the wording fixes follow your answers from today.

---

