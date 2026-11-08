# Build sheet DIESEL-1: the diesel-hybrid example Site "Kisiwa" (units D0–D5)

- Architect: Claude (fresh Architect, DIESEL-1), 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `8032040e8`. Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `T/` = `tools/`, `C/` = `config/`, `V/` = `backend/conversions/`.
- This sheet carries the D lane. It **supersedes `.agent/build-sheet-FUEL-1.md` §5.2–§5.6 where they differ.** Each difference is marked **(changed from FUEL-1)** and gives its reason. FUEL-1 §1–§4 (lanes 1 and 2) are unchanged.
- Owner decisions, verbatim (`.agent/owner-diesel-site-2026-11-07.md`, `.agent/owner-fuel-scope-2026-11-07.md`):
  - timing: "Before the demo" (the demo moves about 2–3 working days);
  - pass mark: "≥20% less diesel (Recommended)" = "at least 20% less diesel per night, over 3 fully checked nights before and 3 after, with no power cut to the cold store";
  - lever: "Stop generator at 60%";
  - idle rate: "Generic 3.3 L/h, labelled (Recommended)" (Kobo's 40 kW set; Kisiwa applies the same generic rule, §2.2);
  - the standing rules: never a combined savings total; no annualising.
- Rules for every D unit: FUEL-1 header rules (SCOPE-1, money only from evidence and declared prices, never tune, never add different bases, mock is the layout spec with MOCK DEVIATION ids, localised tests on own `*_test` DBs, never `assetops_demo3_full_test`, no `-ExecutionPolicy`, Opus first build and first review, Sonnet fix rounds, pre-flight questions batched).
- **The no-tuning rule for this lane, in one line:** every physical value, the lever, the night window, the weather, the calendar and the pass mark are fixed in this sheet *before* D0 runs. If the measured result misses the pass mark, the lane stops and the owner decides. Nobody changes an input to pass.

---

## 1. Order, lanes, conflicts and dates

### 1.1 Units

| Unit | What it delivers | Size | Ruling state | Depends on (merged) |
|---|---|---|---|---|
| **D0** simulator trial | The measured before/after nights, judged against the owner's pass mark. No product code and no DB | 0.5 | **Full ruling, ready now (§2)** | nothing |
| **D1** the Kisiwa Site | Template, demo import, configure, price, no-load fact, roles | 1.0 | Ruling with pinned decisions; pre-flight finishes literals (§3.1) | **D0 PASS**, A1 |
| **D2** `generator-night-fuel-1` family | Plan freeze, evaluate, verdict read and page, migration 0054 | 1.75 | Outline, decisions pinned; literals after D0 (§3.2) | D0 PASS, MV-1, A1, A2 |
| **D3** Kisiwa story data | Scenario, handover file, calendar v4, `demo_combined` child, story Action, Kisiwa-only scratch prepare | 1.5 | Outline, decisions pinned; dates after D0 (§3.3) | D1 (data part); D2 (the freeze step) |
| **D4** four Sites on the estate screens | Portfolio, estate and navigation with four Sites, Kisiwa value line, recaptures | 1.0 | Outline, decisions pinned (§3.4) | PV-1, A3, CH-5d1, D2; D3 for the captures |
| **D5** finish rows and rehearsal | KIS-1–KIS-7, COH extension, whole-list rehearsal prepare, DS-1 beat | 0.75 | Outline, rows named (§3.5, §4) | everything above |
| **Total** | | **6.5 planned; plan figure 7.0** (0.5 held for the post-D0 card round and D2's family-on-a-Finding-Action risk); range 6.5–8.5 | | |

FUEL-1 §5.6 sized this at 6.0 planned and 7.0 as the plan figure. D1 grows by +0.25 (the registered-publication check, §3.1) and D2 by +0.25 (migration 0054 and a generic verdict page). The plan figure stays **7.0**.

### 1.2 The gate after D0

- **D1–D5 do not start until D0 reports PASS** (§2.9), and the coordinator has told the owner the measured figure.
- **D0 NOT MET or FAIL:** the D lane stops at 0.5 units spent. The result goes to the owner, and the demo date returns to the lanes-1–2 plan.
- **D0 FRAGILE** (§2.9): the owner decides before D1 starts.

### 1.3 Order across all lanes (units are lane-time at §15's rate, about 3 units per lane-day including review)

```
now (t=0):        CH-5d1 (own worktree) | MV-1 (lane 1) | A1 (lane 2) | D0 (lane 3, no product code, no DB)
t≈0.5:            D0 result -> owner informed -> gate
t≈0.75:           CH-5d1 merged -> MB-1 (lane 1)
t≈0.85:           A1 merged -> A2 (lane 2) | D1 (lane 3, after D0 PASS)
t≈1.4:            A2 merged -> A3 (lane 2; copy edits after MB-1)
t≈1.85:           D1 merged -> D2 (lane 3; MV-1, A1, A2 are merged by then)
t≈2.0:            MB-1 merged -> WD-1 -> PV-1 (lane 1)
t≈2.3:            A3 merged -> D3 (lane 2 picks it up; its story-Action/freeze step waits for D2)
t≈2.9:            PV-1 merged -> D4 code (lane 1; captures after D3)
t≈3.6:            D2 merged -> D3 finishes its freeze step and its Kisiwa-only scratch prepare
t≈3.8:            D3 merged -> D4 captures -> D4 merged (≈3.9)
t≈3.9–4.65:       D5 (finish rows, COH, whole-list rehearsal prepare)
then:             DS-1 -> E1–E6
```

- **In parallel now:** CH-5d1, MV-1, A1 and D0. D0's files are disjoint from every other unit, and it uses no DB. Four builders run, but D0 is light (in memory).
- **Critical path:** lanes 1–2 alone reach DS-1 at about 2.9 lane-units, about 1 working day. With Kisiwa it is about 4.65 lane-units, about 1.6 working days, plus one extra rehearsal prepare (about 1.5 h machine) and one Kisiwa-only scratch prepare (about 40 min). **Plan figure: the demo moves +2 working days (range 1.5–3).** That is inside the owner's "about 2–3".
- **Dates, relative to the day D0 starts (working days):** day 1, D0, then the gate. Days 1–2, D1 and D2. Days 2–3, D3 and D4. Day 3, D5 and the rehearsal. Day 4, DS-1 and E1–E6. Without Kisiwa, DS-1 would start on day 2–3.

### 1.4 File and migration conflict map (D units against every other running or queued unit)

| D unit | Files it creates or edits | Shared with | Resolution |
|---|---|---|---|
| D0 | new `T/probe_kisiwa_nights.py`; new `host/tests/test_probe_kisiwa_metric.py`; new `.agent/DIESEL-D0/kisiwa-diesel-hybrid-60kw.draft.yaml`, `.agent/DIESEL-D0/probe-result.json`, `.agent/DIESEL-D0-probe-results.md` | none | runs now |
| D1 | new `C/site-templates/kisiwa-diesel-hybrid-60kw.yaml` (D0's draft, verbatim plus header); `backend/tests/test_site_template_fingerprints.py` (one pin); new `V/kisiwa-001-bindings.json`, `V/kisiwa-001-minigrid-roles-demo-config.json`; new `T/demo_combined_kisiwa.py` (import, configure, price, no-load); new `host/tests/kisiwa.py` (drafter); new `host/tests/test_d1_registered_kisiwa.py`; new `backend/tests/test_d1_kisiwa_site_postgres.py` | A1 (uses its vocabulary, does not edit `B/sites/models.py`) | after A1 merges. **No migration** |
| D2 | `B/actions/verification_families.py` (register the family); new `B/actions/night_fuel.py` (pure night choice and metric); `B/actions/verification.py` (summary dispatch per family); `B/actions/verification_rules.py` (night slot read, reusing A2's idle-seconds rule); **new migration `0054_night_fuel_family.py`**; new `F/sites/SiteNightFuelVerification.tsx`, `F/sites/nightFuelVerificationClient.ts`; the route registration (PRE-FLIGHT names the file); tests | MV-1 (`verification_families.py`, `verification.py`, the mill page it may share components with); A2 (`verification.py`, `verification_rules.py`); A1 (migration chain) | after MV-1, A1 and A2 merge |
| D3 | new `C/scenarios/kisiwa-day.yaml` (parent) and rendered per-day files (PRE-FLIGHT: rendered files or run inputs); new `V/kisiwa-day-handover-v1.json`; new `V/demo-story-days-v4.json` (v3 kept as history); `T/demo_story_days.py` (Kisiwa kinds); `T/demo_combined.py` (`SITES`, `SITE_CODE`, `EXPECTED_SECONDS`, instants); `V/demo-combined-story-v1.json` (a `kisiwa` block); `T/demo_combined_kisiwa.py` (story part); `T/probe_kisiwa_nights.py` (`--handover`) | no other lane edits `demo_combined.py`, the story JSON or the day calendar | data part after D1; the freeze step after D2 |
| D4 | `B/site_outcomes/read.py` (`portfolio_cards`), `B/site_outcomes/mini.py` (the Assure `verified_values` Kisiwa line), `B/estate/portfolio.py`, `B/chain/vocabulary.py` (only if a count word needs it), `F/estate/PortfolioOutcomes.tsx`, the estate and Site navigation files (PRE-FLIGHT), `portfolioFixtures.ts`, `estatePortfolio.test.tsx`, `backend/tests/test_ch6b2_portfolio_cards.py`, layout captures and the all-26 audit index | CH-5d1, MB-1, WD-1, PV-1, A3 | after PV-1 and A3 merge (lane 1's last unit) |
| D5 | `T/demo_combined_finish.py` (KIS rows), `T/checks/chain_coherence.py` (COH-17 and V4 for Kisiwa), the DS-1 draft | MV-1, MB-1, A3, PV-1 (finish rows); CH-5d1, MB-1, PV-1, A3 (COH) | last |

**Migrations.** A1 owns **0053** (`0053_fuel_cost_2.py`). A2, A3, MV-1, MB-1, WD-1 and PV-1 add none; MB-1's stop list forbids one. **D2 owns 0054**, with `down_revision` = A1's 0053 revision id. No other D unit adds a migration; if one would, the unit stops (S-MIG).
- If any unit merges a migration between A1 and D2 (none is planned), D2 renumbers to the next free number and re-points `down_revision`. The single-alembic-head test catches a missed renumber.
- D0, D1, D3, D4 and D5: no schema change.

**Data, not file, effects** (no edit needed, but tell the lane):
- **CH-5d1's Optimize card:** with Kisiwa there are two priced Sites (Kobo idle mornings after A3; Kisiwa nights). The card takes its "two or more priced Sites" path. That path never sums; KIS-6 checks it.
- **PV-1's Assure card** gains a third value line (Kisiwa, basis `NIGHT_MODELLED_FUEL`). It is never added to the mill or Kobo-trial lines; PV-A is re-expected in D5.
- **The all-26 layout audit:** D4 recaptures the four-Site pages.

---

## 2. D0: the Kisiwa simulator trial (full ruling, ready for a builder now)

### 2.1 Purpose and limits

- Run Kisiwa's stated physics through the real simulator, in memory: 5 nights before the change, then 4 nights after it.
- Measure modelled diesel per night, cold-store service and battery level.
- Judge the result against the owner's pass mark, as declared in §2.7.
- **No product code** (nothing under `backend/assetops_backend/`, `frontend/`, `config/`, `simulator/` or `contracts/` changes). **No DB, no prepare, no suites.**
- The builder never changes any value in §2.2–§2.7. That includes when the result misses the mark.

### 2.2 Kisiwa's physical assumptions (stated before any run; never tuned)

FUEL-1 §5.2 is kept, apart from the rows marked **(changed from FUEL-1)**.

| Item | Value | Basis |
|---|---|---|
| Site | "Kisiwa island mini-grid", code `KISIWA-001`, timezone **`Africa/Dar_es_Salaam` (UTC+3)** | Island in the Swahili coast; the same UTC offset as Kobo, so the story clock logic is unchanged |
| Component ids | **Kobo's ids, unchanged:** `pv-array`, `pv-inverter`, `battery`, `battery-pcs`, `generator`, `fuel-tank`, `ac-bus`, `load-res`, `load-clinic`, `load-mill`. **The device, signal and mapping ids are Kobo's too.** Only display names, ratings, property values and Site Controls differ **(changed from FUEL-1: made explicit)** | The product's dispatch analytic reads Kobo's device ids by name (`B/analytics/dispatch.py:70-74`, `FEEDERS`). New ids would need a product change and a `dispatch-2` model bump. Display names carry the meaning |
| Loads | `load-res` "Households", rating 15 kW; **`load-clinic` "Cold store (ice and fish)", rating 6 kW**; `load-mill` "Water pump", rating 8 kW | Display names only; ids as above |
| PV / inverter | 20 kWp (`pv-rated-power` 20 kW) / 20 kW AC (`inverter-ac-limit` 20) | Small array on an island site |
| Battery / PCS | 60 kWh; reserve 30 %; PCS 20 kW charge and 20 kW discharge, 95 % each way | |
| Generator | 60 kW (`generator-rated-power` 60); start 35 %, **stop 90 % (before)**, minimum runtime 30 min, start delay 5 min | Kobo's control values. v5's start rule gives min(35, 30 + 5) = 35 % |
| SFC | **0.355 L/kWh** = (0.08145 × 60 + 0.246 × 45) / 45, the generic fuel curve at 75 % of rating | One stated rule. Partial-load running is under-counted, which is conservative |
| No-load rate | **4.9 L/h**, basis `GENERIC_DEFAULT` (0.08145 × 60 = 4.887, shown as 4.9) | The same generic rule that gives Kobo's owner-chosen 3.3 L/h for 40 kW (0.08145 × 40 = 3.26). Not a new choice |
| Tank | 1000 L; **start full, 1000 L**. No tank signal is published (BL-16 stays post-demo) | |
| Diesel price | 1.25 USD/L, `V/demo-diesel-price-publications.json` v1, published at Kisiwa as its own publication | The same declared price as Kobo |
| **Source priority** | **`[pv-array, generator, battery]` ("cycle charging") (changed from FUEL-1: made explicit)** | FUEL-1 §5.2 states that the generator "carries the load and charges at the PCS limit until 90 %". In the mini-grid model that holds only when the generator is ahead of the battery (`mini_grid.py:567-583`: the battery serves before any source behind it; the generator charges only from what is left over). With Kobo's order `[pv, battery, generator]` the generator would idle beside a discharging battery, and the stop setting would mean something else. This is the standard diesel-hybrid strategy, and the only one the owner's lever describes |
| Critical-load priority | `[load-clinic (cold store), load-res, load-mill]` | The cold store is protected first, as Kobo's clinic is |
| Supply-use roles (D1) | cold store `ESSENTIAL_SERVICE`; households `HOUSEHOLD`; water pump `HOUSEHOLD` | Vocabulary `B/sites/models.py:290`. There is no productive load, so no mill-style sales line appears at Kisiwa |
| Loads, every day | Households: 2 kW 06:00–18:00, 8 kW 18:00–23:00, 3 kW 23:00–06:00. Cold store: 4 kW constant. Water pump: 6 kW 19:00–23:00, 0 kW otherwise (stated as 0, never left blank) | FUEL-1 §5.2. About 205 kWh a day |
| **Weather, every day** | **The `C/scenarios/kobo-daytime.yaml` sunny levels, local time, in 2-hour windows: 06–08 150, 08–10 550, 10–12 900, 12–14 950, 14–16 600, 16–18 150 W/m²; 0 from 18:00 to 06:00 (changed from FUEL-1)** | FUEL-1 said "Kobo's calendar day-kinds for the same dates". Kobo's calendar kinds are story scenarios (8-hour generator mornings), not full-day weather, so they do not transfer. Every day has the same weather, so before and after differ **only** by the change; that is a controlled comparison. Weather is not chosen per outcome. About 132 kWh of PV a day |
| Model | `mini-grid` v6, 5-minute step, Lab publication profile v3 (as `T/probe_kobo_nights.py`) | |

### 2.3 Runs, cuts and the lever

- **One run = one Kisiwa day, from 15:00 local to 15:00 local the next day** (12:00Z to 12:00Z), 288 steps. Simulation dates do not matter (nothing in §2.2 depends on the date). D0 uses run 1 starting `2026-10-01T12:00:00Z`.
- **Run 1 start:** battery 100 %, fuel 1000 L, generator STOPPED. The battery is full at 15:00 on a sunny afternoon. D0 reports the measured 15:00 level every day, so any drift is visible.
- **Every later run** starts at the previous run's measured end, at full precision (no rounding): the battery level and the fuel. The generator must be STOPPED at every 15:00 cut, because run setup refuses a RUNNING start. That makes a chain of day-runs equal to one continuous run (gate G4).
- **Runs 1–5: before** (stop 90 %). **Runs 6–9: after** (stop 60 %).
  - The change takes effect at the run 6 start, 15:00 local on the change day. That is the boundary between run 5 and run 6.
  - In D0 the after runs use `kisiwa_site(site_edit=…)` with `stop-soc-threshold` = 60 (the `host/tests/kobo.py:89-97` `set_property` pattern; source becomes SITE). In product (D3) the same change is a Foundation revision effective at that instant.
  - 35 % < 60 %, so the band holds (`mini_grid.py:409-415`).
- **Night k** = 18:00 local on run k's start day to **12:00 local the next day**, which is step indices `[36, 252)` of run k. It lies wholly inside run k, so it is wholly before or wholly after the change.

### 2.4 The night window: 18:00 to 12:00 (changed from FUEL-1's 18:00–06:00, fixed before any run)

- A generator run that starts in the night continues after sunrise until the battery reaches the stop setting. The lever acts exactly on that tail: stopping at 60 % ends the run earlier in the morning and lets the sun finish charging.
- A window ending at 06:00 would cut through that run. It would also let a change that merely *moved* fuel past 06:00 look like a saving. 18:00–12:00 holds the whole overnight run on these sunny days, so fuel can neither leave the window nor be hidden from it. This is the stricter definition.
- D0 also reports the 18:00–06:00 figure, for information only. **It is never the pass figure.**
- Client wording: "diesel per night (6 pm to noon)". The owner is told before D0 runs (§7, Q1). The definition is frozen once D0's measured run starts.

### 2.5 The metric (identical to what D2 will compute from readings)

For each 5-minute step i of night k, the tool reads the run trajectory, as `T/probe_kobo_nights.py:104-127` does:

- `state_i` = `discrete_for_step["generator-state@generator"]`;
- `E_i` = the accepted generator energy over the step (kWh). Read it from `boundaries[i].control_step.accepted.flows` (the generator output flow; the builder names its `flow_id` from `mini_grid.py:759-790`). Cross-check `E_i × 0.355 == fuel_i − fuel_{i+1}` exactly (Fraction), where fuel is the stock `fuel-tank-volume@fuel-tank`.
- Litres per step:
  - **loaded:** `state_i == RUNNING` and `E_i > 0`: `L_i = E_i × 0.355`;
  - **idle:** `state_i == RUNNING` and `E_i == 0`: `L_i = (5/60) × 4.9`;
  - otherwise `L_i = 0` (STOPPED and STARTING burn nothing in this rule, as fuel-cost-2).
- `night_litres_k = Σ L_i`, exact Fraction. Shown to 0.1 L. Nominal: no 1.10 multiplier. The multiplier is fuel-cost-2's upper bound for Findings; it would not change a ratio anyway.
- **Guardrail readings for each night:**
  - cold-store unserved energy = Σ `unserved_energy` of the `LoadService` for `load-clinic` in `control_step.accepted.loads` (kWh);
  - all-loads unserved, reported;
  - battery level at every boundary from `stocks["battery-state-of-charge@battery"]`, its minimum, and whether any boundary is below the reserve in effect (30 %).
- **Reported for each night:**
  - running, loaded and idle minutes; starts;
  - generator kWh; loaded litres; idle litres; night litres;
  - the simulator's own tank drop (it must equal loaded litres: the linear law has no idle fuel);
  - battery at 18:00, 06:00 and 12:00;
  - 18:00–06:00 litres (information only);
  - **indicative avoidable minutes** (information only): RUNNING steps where the battery is at least 10 points above reserve, and PV available + min(20 kW, battery energy above reserve × 0.95 / step hours) ≥ 1.10 × load demand. This mirrors the thresholds at `B/analytics/dispatch.py:51-65`. It is labelled indicative; the product's classification runs at D3.

### 2.6 Before and after nights

- **The 3 nights judged are the last 3 before the change and the first 3 after it: nights 3, 4, 5 before, and nights 6, 7, 8 after.** That mirrors the family's day rule (the mill's `choose_days`: the last 3 before, the first 3 after).
- Nights 1–2 and night 9 are margin for D3's "fully checked" grading. They are reported, never used in the pass figure.

### 2.7 Pass mark (owner, declared 2026-11-07; restated exactly, before any run)

PASS iff all three hold:
1. **Diesel:** `mean_b = (L3 + L4 + L5) / 3` and `mean_a = (L6 + L7 + L8) / 3`. `(mean_b − mean_a) / mean_b ≥ 1/5`, compared as exact Fractions and shown to 0.1 %.
2. **Cold store:** unserved energy at `load-clinic` = 0 at every step of nights 3–8. D0 also reports all steps of all 9 runs.
3. **Battery:** no boundary of nights 3–8 below the reserve in effect (30 %). This is the family guardrail from FUEL-1 §5.3; D2's verdict would fail on it, so D0 does too.

The result is one of: **PASS**, **NOT MET** (rule 1 fails, rules 2–3 hold), or **FAIL** (rule 2 or 3 fails).
- **FRAGILE** is added to a PASS when the same reduction over all before nights (1–5) against all after nights (6–9) is below 20 %. It means the pass depends on which 3 nights are used. It goes to the owner before D1.
- **Money, for information only, never a target:** `(mean_b − mean_a) × 1.25` USD per night, "modelled from a generic fuel curve, not measured by a fuel meter". No annualising.

### 2.8 Gates the tool asserts (lever-independent; a failing gate stops the run)

- **G1** Every run is READY at setup, and `run_to_end` completes (`assert run.execution_status == "READY"`, as `probe_kobo_nights.py:108`).
- **G2** For every step, `E_i × SFC` equals the tank drop exactly.
- **G3** The generator is STOPPED at every 15:00 cut (runs 1–9).
- **G4** Chained runs 1–5 equal one continuous 5-day run (`2026-10-01T12:00Z` to `2026-10-06T12:00Z`, stop 90) at every boundary: battery, fuel and generator state, exactly.
- **G5** No step is fuel-limited. The resolver's "fuel in tank" note never appears (`mini_grid.py:683-684`).
- **G6** The tool is deterministic: two runs give byte-equal `probe-result.json`.

### 2.9 Stops (report to the Architect and the coordinator; never design around them)

- **S1, NOT MET.** The reduction is below 20 %. **Stop.** Report the figures. Do not change any assumption, the lever, the window, the weather, the calendar, the start state or the nights judged. The coordinator takes it to the owner. *Architect's pre-registered expectation, written before any run: under cycle charging the saving comes only from diesel-charged energy still in the battery when the sun rises, so it depends on whether the overnight run reaches past dawn. A result below 20 % is plausible. That is why D0 runs before any product code.*
- **S2, FAIL.** A cold-store power cut or a battery level below reserve in nights 3–8. Stop and report.
- **S3, refusal.** Run setup, the template parser or the model refuses the template or a scenario (for example the source-priority order, a threshold band, a missing parameter). Stop. Report the refusal verbatim and the smallest fix that keeps every §2.2 value. The Architect rules. Never change a physical value to get past a refusal.
- **S4, G3 fails.** The generator is running at a 15:00 cut. Stop and report the run and its state. The Architect rules a cut time; that is never chosen by outcome.
- **S5, any other gate (G2, G4, G5, G6) fails.** Stop and report.
- **S6, FRAGILE PASS.** Report it; D1 waits for the owner.
- **S7, evidence risk (not a fail).** Zero indicative avoidable minutes on all of nights 3–5. Report it. The Architect rules before D1, because the story would then have no Finding to start from.
- **S8.** The work exceeds 0.75 unit.

### 2.10 Files, how to run, evidence

**Branch** `task/DIESEL-D0-kisiwa-probe` from main at or after `8032040e8`. **Worktree** `C:\Users\assef\Bineyame\AssetOpsV1-d0`; the builder creates both.

**Files (all new):**
1. **`.agent/DIESEL-D0/kisiwa-diesel-hybrid-60kw.draft.yaml`**: a full Site template.
   - Copy `C/site-templates/kobo-mini-grid-60kw.yaml` and change only what §2.2 lists:
     - `template_id: kisiwa-diesel-hybrid-60kw`, `template_version: 1`, `display_name: Kisiwa Diesel-Hybrid Mini-Grid (60 kW generator, island)`, and a summary;
     - ratings and properties;
     - load and meter display names ("Households", "Cold store (ice and fish)", "Water pump"; "Households meter", "Cold store meter", "Water pump meter");
     - `site_controls` per §2.2;
     - `control_assumptions`: `generator-charges-when-running` ("When the generator runs it serves load first and charges the battery with what is left, within the PCS limit, until the stop setting"), and `cold-store-protected`.
   - The header comment states: "DEMONSTRATION values, DIESEL-1 §2.2, fixed before the D0 probe; never tuned".
   - Not under `config/`, so no fingerprint test runs. D1 promotes it verbatim.
2. **`T/probe_kisiwa_nights.py`**, modelled on `T/probe_kobo_nights.py`:
   - `kisiwa_site(site_edit=None)` and `kisiwa_draft(document, start, end, site_edit=None)` mirror `host/tests/kobo.py:65-176`: `site_from_template` on the draft template, `site_id="KISIWA-001"`, timezone `Africa/Dar_es_Salaam`, Foundation `valid_from` `2026-09-01T00:00:00Z`, `mini-grid` v6, 5 min;
   - `day_document(start_soc, start_fuel)` builds one 15:00–15:00 scenario in memory. Copy the event and parameter shapes from `C/scenarios/kobo-s3-dispatch-necessary-run.yaml` (irradiance and the three start parameters) and `C/scenarios/kobo-daytime.yaml` (load events). Windows are cut at 15, 16, 18, 19, 23, 06, 08, 10, 12, 14 local, so each level is one window; `version_valid_from: '2026-09-01T00:00:00Z'`;
   - `measure_night(trajectory)` is the §2.5 metric as one pure function;
   - `build()` runs §2.3 and the gates and returns the result;
   - CLI: no argument prints the JSON; `--write` writes `.agent/DIESEL-D0/probe-result.json` and prints the verdict line; `--check` exits 1 if the committed JSON differs (G6).
   - Its docstring carries §2.2–§2.7 by reference ("DIESEL-1 §2").
3. **`host/tests/test_probe_kisiwa_metric.py`** (L0, no DB): `measure_night` on a hand-built 4-step series.
   - Steps: loaded 30 kW, idle RUNNING at 0, STARTING, STOPPED. Litres = `Fraction(30*5,60)*Fraction(355,1000) + Fraction(5,60)*Fraction(49,10)`.
   - Plus the cold-store unserved sum and the below-reserve flag.
4. **`.agent/DIESEL-D0/probe-result.json`**, written by the tool. Schema `{"id": "assetops.kisiwa-night-probe", "version": 1}`. Keys:
   - `assumptions` (the §2.2 table as data, plus the draft template's sha256);
   - `profile`, `runs` (start and end state per run), `nights` (all §2.5 fields per night, litres as exact-fraction strings and 3-dp decimals);
   - `gates`;
   - `verdict`: `nights_before [3,4,5]`, `nights_after [6,7,8]`, `mean_before`, `mean_after`, `reduction_pct`, `pass_mark "at least 20 % less diesel per night (owner 2026-11-07)"`, `guardrails`, `result`, `fragile`, `all_nights_reduction_pct`;
   - `money_info`.
5. **`.agent/DIESEL-D0-probe-results.md`**, the evidence file for the owner and the Architect:
   - (a) the plain-words result line, verbatim template: "Kisiwa trial (example data, simulator): {mean_b} L → {mean_a} L of modelled diesel per night (6 pm to noon), {pct} % less, on 3 nights before and 3 after stopping the generator at 60 % instead of 90 %. Cold store power cuts: {n}. Pass mark (at least 20 % less, declared by the owner on 7 Nov 2026): {passed | not met}.";
   - (b) the per-night table;
   - (c) the gates;
   - (d) the indicative avoidable minutes, and the 18:00–06:00 figures marked "information only";
   - (e) the in-memory seconds per 24-hour run, for the E3 estimate;
   - (f) which stop, if any, applied.

**How to run** (PowerShell, from the worktree; PYTHONPATH pinned because the shared `.venv` resolves editable installs to another checkout; see the FUEL design B2):
```
$wt = "C:\Users\assef\Bineyame\AssetOpsV1-d0"
$env:PYTHONPATH = "$wt\backend;$wt\contracts;$wt\simulator;$wt\field;$wt\gateway;$wt\host;$wt\host\tests;$wt\tools"
& C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe "$wt\tools\probe_kisiwa_nights.py" --write
& C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe -m pytest "$wt\host\tests\test_probe_kisiwa_metric.py" -q
& C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe "$wt\tools\probe_kisiwa_nights.py" --check
```
No `-ExecutionPolicy`, no DB, no suite.
- **Reading budget:** this §2; `T/probe_kobo_nights.py`; `host/tests/kobo.py`; `C/site-templates/kobo-mini-grid-60kw.yaml`; `C/scenarios/kobo-s3-dispatch-necessary-run.yaml:1-130`; `C/scenarios/kobo-daytime.yaml`; `simulator/assetops_simulator/packs/mini_grid.py:1-110`, `:405-790`, `:1140-1200`; `contracts/assetops_contracts/trajectory.py:240-300`; `contracts/assetops_contracts/control.py:145-230`, `:298-312`.
- **Review:** one fresh Opus reviewer.
  - It re-runs `--check` and confirms G6.
  - It reads the draft template against §2.2 value by value, and the metric against §2.5.
  - It confirms that nothing outside the D0 file list changed.
- **Merge:** on ACCEPT, whatever the result (PASS or not). The evidence is the deliverable.

---

## 3. D1–D5 (decisions pinned; literals and dates finalised in one card round after D0 PASS)

**Rule state.** D1's card is complete except for its pre-flight literals. D2–D5 are outlines with every decision pinned. After a D0 PASS, the Architect writes one consolidated card per unit (literals, dates, tests, reading index) in this file, as ROLE_CONFIG Token Efficiency item 5 requires. That card round is inside the 0.5 contingency.

### 3.1 D1: the Kisiwa Site, 1.0 (ready when D0 PASSES and A1 merges)

- **Template.** Promote `.agent/DIESEL-D0/kisiwa-diesel-hybrid-60kw.draft.yaml` to `C/site-templates/kisiwa-diesel-hybrid-60kw.yaml` **byte-equal in the `foundation` block**, with the shipped-template header. Pin its fingerprint in `backend/tests/test_site_template_fingerprints.py`.
- **Demo child, configure part (`T/demo_combined_kisiwa.py`, new):** import, convert, `configure_at`, modelled on `T/demo_combined_kobo.py`.
  - Bindings: `V/kisiwa-001-bindings.json`.
  - Roles config `V/kisiwa-001-minigrid-roles-demo-config.json`: the §2.2 supply-use roles, and the Kobo minigrid-roles-4 bindings carried over with the Site code changed.
  - Diesel price v1 recorded at install + 1 h, as Kobo.
  - **No-load fact** through A1's vocabulary, effective at install + `CONFIG_OFFSETS["uses"]`: `generator-no-load-fuel-rate` 4.9 L/h, basis `GENERIC_DEFAULT`, source SITE v1. Note: "Generic no-load fuel rate for a 60 kW diesel set (common design-software default, about 0.08 L/h per kW of rating); not this generator's datasheet. Owner decision 2026-11-07 (generic, labelled)."
- **Registered parity.** `host/tests/kisiwa.py` (a registered-Site drafter) and `host/tests/test_d1_registered_kisiwa.py`: the D0 probe re-run on the registered `KISIWA-001` must equal `probe-result.json`, as `test_dd1a1_registered_kobo.py` does for Kobo.
- **L2** `backend/tests/test_d1_kisiwa_site_postgres.py` on own `assetops_d1_test`: import, configure, price v1, no-load fact as known; the dispatch analytic accepts Kisiwa's readings (same device ids).
- **PRE-FLIGHT (no code first):**
  - (a) whether the registered publication profile (`registered-kobo-publication`) is bound to `KOBO-001` by name. If a Kisiwa publication profile is needed, **stop**; the Architect rules (+0.25, already in D1's size);
  - (b) grep every product string that would show "clinic", "mill" or "Kobo" on a Kisiwa screen by component id rather than display name. Each one is a finding for D1 (server copy reads the display name) or D4 (UI);
  - (c) the board rows with no PRODUCTIVE load: each must read an existing honest state. A row needing new text is a stop.
- **Stops:** any change to Kobo, Cold or EV bytes; a contract or run digest change; a migration; more than 1.25 units.

### 3.2 D2: the `generator-night-fuel-1` family, 1.75 (after D0 PASS, MV-1, A1, A2)

Pinned decisions:
- **Origin:** a **W1 Action raised from a Kisiwa dispatch Finding thread** (Candidate avoidable running is the evidence step). The family is its plan's `rule_id`.
  - Plan version `generator-night-fuel-verification-1`.
  - **Migration 0054** widens `verification_plan.rule_id` and `plan_version`, and the `verification_plan_family` CHECK lets a `generator-night-fuel-1` row on a Finding-origin action keep the reserve columns NULL. It follows the 0052 pattern (`backend/migrations/versions/0052_verification_plan_domain.py:59-104`), with a downgrade.
  - PRE-FLIGHT: if a W1 Action cannot carry a non-reserve family without changes beyond 0054 and the summary dispatch, **stop**; the Architect rules (contingency).
- **Night choice:** a night = 18:00 local to 12:00 local next day (§2.4). Effective instant = the Foundation revision's `effective_from` (the change); no night straddles it.
  - Baseline: the last 3 COMPLETE nights before, looking back at most 14. Later: the first 3 COMPLETE nights after, looking ahead at most 14.
  - A night counts only when every generator-state and generator-power reading in its window is COMPLETE (the weakest-row rule, as the mill's `DAY_RULE`). Chosen by grade, never by value.
  - SHORT handling as the mill's `SHORT_TEXT` pattern.
- **Metric:** §2.5 from accepted readings. Per 5-minute slot: loaded = slot generator kWh × the as-known SFC; idle = RUNNING with 0 kWh × r × 5/60, with r from A2's `store.no_load_history`.
  - It reuses A2's slot rule (`generator_idle_seconds`). It never re-derives it.
  - Exact Fraction stored; shown to 0.1 L.
- **Target (owner, verbatim, frozen in the plan):** `{"rule": "5*mean(later) <= 4*mean(baseline) modelled_diesel_l[night 18:00-12:00]", "over": "COMPLETE nights of each window", "ratio": [4, 5], "declared_by": "owner 2026-11-07"}`.
- **Guardrails (frozen in the plan):** cold-store (`load-clinic`) unserved energy = 0 in every night of both windows; sampled battery level never below the reserve in effect. Both are read from stored readings; NOT_KNOWN when a reading is missing (never assumed 0).
- **Verdicts:** the existing outcome vocabulary (VERIFIED / INEFFECTIVE / INCONCLUSIVE / NOT_JUDGED). INEFFECTIVE is recorded truthfully if the data says so.
- **Money line on VERIFIED:** `(mean_b − mean_a) L × declared diesel price` per night. Basis `NIGHT_MODELLED_FUEL`. Wording pattern as MV-1's `VALUE_TEXT`; literal fixed in the card round: "About {d} {cur} less diesel a night: ({b} − {a}) L a night × your declared {p} {cur} per litre, modelled from a generic fuel curve, not measured by a fuel meter, on 3 fully checked nights before and after the change". UNPRICED states as MV-1. No annualising, no total.
- **Page:** `F/sites/SiteNightFuelVerification.tsx`, reusing the mill page's panel components and CSS (no new layout).
  - **MOCK DEVIATION MD-FUEL-D-2:** v69 `:498-505` shows no money on Verification.
  - The browser formats no number.
- **Tests:**
  - L0 `backend/tests/test_d2_night_fuel.py`: night choice; metric (loaded, idle, mixed); target at exactly 20 % (passes) and at 19.9 % (fails); each guardrail; money reproduce-by-hand;
  - L2 `backend/tests/test_d2_night_fuel_postgres.py` on own `assetops_d2_test`: freeze, evaluate, read; migration up and down; single-alembic-head;
  - vitest for the page;
  - guards A, W, N, V, M, and frontend-hardwiring.
- **Stops:** any byte change to reserve-trial or mill plan, outcome or page bodies; A2's slot rule needing a change; more than 2.0 units.

### 3.3 D3: Kisiwa story data, 1.5 (data part after D1; freeze step after D2)

Pinned decisions:
- **Days = D0's run shape.** One run per Kisiwa day, 15:00 local to 15:00 local, same weather and loads.
  - Parent scenario `C/scenarios/kisiwa-day.yaml`.
  - Per-day start states from `V/kisiwa-day-handover-v1.json`, written by `T/probe_kisiwa_nights.py --handover` at full precision. Its `--check` mode guards it, as Kobo's handover file.
  - PRE-FLIGHT: rendered per-day files (Kobo's `derive_steady_scenarios` pattern) or start-state run inputs, whichever run setup supports without a contract change.
- **Calendar `V/demo-story-days-v4.json`:** v3's Kobo, Cold and EV entries byte-equal, plus `sites.kisiwa` and `kinds.kisiwa`.
  - Kisiwa = **9 day-runs**: K-5…K-1 before (stop 90), the change at 15:00 local on K0 = the start of the first after run, then 4 after runs.
  - Dates are placed so that the after nights end before the story's S+0 board cutoff. They are fixed in the card round against `demo_story_clock`; the weather does not depend on the date.
- **Story Action:** recorded at story time.
  - Finding thread (the before nights' Candidate Findings) → Action "Stop the generator at 60 % instead of 90 %" → Foundation revision `stop-soc-threshold` 60, effective at the change instant → plan freeze (D2) → evaluation after the last after night is graded.
- **`T/demo_combined.py`:**
  - `SITES += ("kisiwa",)`, after EV (install order);
  - `SITE_CODE["kisiwa"] = "KISIWA-001"`;
  - `EXPECTED_SECONDS["kisiwa"]` from the D0 in-memory seconds plus the per-run pipeline cost measured at the scratch prepare;
  - the price instant like Kobo's;
  - a `kisiwa` block in `V/demo-combined-story-v1.json`.
- **One Kisiwa-only scratch prepare** (`--sites kisiwa`) on own `assetops_kisiwa_d3_test`, keep-awake on, cap 1 h:
  - confirm the stored night litres equal `probe-result.json` (exact), and the verdict is the one D0 measured;
  - record seconds per day for E3;
  - drop the DB and the var folder.
- **Stops:**
  - a stored figure differs from D0. That is a data finding: report it, never retune;
  - any Kobo, Cold or EV digest change;
  - the scratch prepare exceeds 1 h;
  - more than 1.75 units.

### 3.4 D4: four Sites on the estate screens, 1.0 (after PV-1, A3, CH-5d1, D2; captures after D3)

- Portfolio, estate and Site navigation list four Sites. They are read from data, never a hard-coded count; the frontend-hardwiring count must not rise.
- **MOCK DEVIATION MD-FUEL-D-1:** v69 `:131` reads "3 priority sites".
- **Assure card:** PV-1's `verified_values` gains the Kisiwa line (basis `NIGHT_MODELLED_FUEL`): "{site} · {code}: about {l} L, {amount} {cur} less diesel a night (modelled, generic fuel curve, not metered)". It is listed after the mill and Kobo-trial lines in Site order. **No total, no Decimal arithmetic across lines.**
- **Optimize card (CH-5d1):** the "two or more priced Sites" path shows each Site's claim on its own. No sum.
- **Layout:** evidence at 1440 and 390 for every changed page; all-26 audit index regenerated.
- **Tests:** `test_ch6b2_portfolio_cards.py` (Grow and Protect byte-equal for the three existing Sites), `test_pv1_value_lines.py` (three lines, no field equal to any sum), `estatePortfolio.test.tsx`, `portfolioFixtures.ts`.
- **Stops:** any change to a Kobo, Cold or EV card value; a sum anywhere; more than 1.25 units.

### 3.5 D5: finish rows, coherence, rehearsal, DS-1 beat, 0.75 (last)

- Finish rows in `T/demo_combined_finish.py` (§4.3). Expected values are computed from stored rows and declared inputs, never typed from a run.
- COH-17 and V4 in `T/checks/chain_coherence.py` extended to Kisiwa, with a self-test pass and fail case.
- **Whole-list rehearsal prepare** on own `assetops_diesel_rehearsal_test`, keep-awake on, with the 3 h cap: all four Sites, then the finish rows; then drop the DB.
- DS-1 beat drafted: "Kisiwa: the generator was charging the battery the sun would fill → stop at 60 % → {pct} % less diesel a night, cold store never cut; modelled, not metered".

---

## 4. E3 impact

### 4.1 Prepare time

- Kisiwa adds 9 day-runs of 24 h each. Kobo runs measure about 110 s each, including the pipeline. A 24-hour run has more steps, so the estimate is about 150–200 s per Kisiwa run: **+25–35 min** sequential.
- **E3 ≈ 1.3–1.5 h of the one-time 3 h cap (OD-P12).** D0 records in-memory seconds and D3 records the pipeline seconds; D5 restates the figure from the rehearsal.
- **Stop:** if the rehearsal exceeds 2.5 h, the Architect rules before E3 (for example Sites in parallel). The 3 h cap is never raised silently.

### 4.2 Rehearsal prepare

- One whole-list rehearsal (D5) on `assetops_diesel_rehearsal_test`, about 1.5 h, as DD-1b2b did. It replaces nothing that already ran; it is the extra machine time in §1.3.
- Plus D3's Kisiwa-only scratch prepare, about 30–40 min.

### 4.3 Finish rows to add (written in D5; run at E3)

| Row | Checks |
|---|---|
| **KIS-1** | `KISIWA-001` exists. The diesel price v1 and the no-load fact (4.9 L/h, `GENERIC_DEFAULT`) are as known at the story cutoff, and the stop setting is 90 before and 60 after the change instant |
| **KIS-2** | The before nights' dispatch Findings are SUPPORTED, priced fuel-cost-2. `quantity_high` = 1.10 × (loaded SFC × kWh + idle h × r), computed from stored segments and readings |
| **KIS-3** | The verdict as computed from stored nights. It is VERIFIED only if 5 × mean(later) ≤ 4 × mean(baseline) and both guardrails pass. INEFFECTIVE is recorded truthfully and never forced |
| **KIS-4** | The night money line reproduces from the shown means and the declared price |
| **KIS-5** | The Portfolio and estate list four Sites, and the counts equal the per-Site boards |
| **KIS-6** | CH-5d1's Optimize card on the two-or-more-priced-Sites path, with each Site's line equal to its board claim and no sum |
| **KIS-7** | The Assure card's Kisiwa value line equals its source, and **no card field equals the sum of any two value lines** |
| *(re-expected)* | PV-A (now three lines), COH-17 and V4 (Kisiwa), F-THREADS (the Kisiwa thread) |

---

## 5. Plan HTML (`Docs/demo-sprint/client-demo-plan.html`): rows to change

1. **Build-units table** (around `:647-664`): add, before the DS-1 row, "DIESEL-1 Kisiwa diesel-hybrid example Site, D0–D5 (owner 2026-11-07: before the demo; ≥20 % less diesel per night; stop at 60 %)", **7.0** (D0 0.5, D1 1.0, D2 1.75, D3 1.5, D4 1.0, D5 0.75, +0.5 contingency). Note: D1–D5 run only after D0 PASSES. This replaces FUEL-1's suggested conditional "D-lane" row.
2. **Total row** (`:665`): ≈ 117.3 → **≈ 124.3**, and lanes +7.0.
3. **G5 freeze** (`:1172`) and **G6** (`:1173`): +7.0 (DIESEL-1), on top of FUEL-1's +5.35 and CH-5d's −0.25.
4. **Lanes schedule table** (around `:930-937`): add lane 3 rows D0 (now), D1, D2, and D3/D4/D5 on the freed lanes 2 and 1, per §1.3. Elapsed: about 1.6 working days of lanes after D0.
5. **Lanes figure** (around `:962-972`): a lane 3 strip with D0 → D1 → D2, then D3 on lane 2 after A3 and D4 → D5 on lane 1 after PV-1.
6. **E3 row** (`:1088`): add Kisiwa's 9 day-runs and the estimate "+25–35 min; E3 ≈ 1.3–1.5 h of the 3 h cap".
7. **Machine-time note** (`:1103`): +1.5 h rehearsal prepare (D5) and +30–40 min Kisiwa scratch prepare (D3), both before E3.
8. **Calendar estimate line** (`:1175`) and **OD-P9** (`:134`, `:1147`): G6 moves about +2 working days (range 1.5–3); the session date follows.
9. **Rulings table:** add a "DIESEL-1" row pointing to this sheet: the D0 ruling, the pinned window (18:00–12:00), cycle charging, weather, the gate after D0, migration 0054 owned by D2.
10. **After-the-demo list (§2.2):** add "Kisiwa measured tank or flow panel (simulator idle law for Kisiwa only, plus a tank publication; +1.0–1.5)". BL-16 stays post-demo.

---

## 6. Totals

- **Remaining before DS-1:** lanes 1–2 **5.85** (CH-5d1 0.75 + FUEL-1 5.1) + Kisiwa **7.0** = **12.85** (12.35 at the planned 6.5). Then DS-1 (1) and E1–E6.
- **If D0 does not pass:** Kisiwa costs 0.5, remaining is 6.35, and the demo date returns to the lanes-1–2 plan.
- **Plan total:** ≈ 117.3 + 7.0 = **≈ 124.3**.

---

## 7. Owner questions (plain language; for the coordinator to send before D0's measured run)

1. **What does "per night" cover?** We will count a night as **6 pm to noon the next day**. That way, if the generator keeps running after sunrise to finish charging the battery, that diesel is still counted. The change you chose acts on exactly that part, and it means no diesel can be moved out of the count to look like a saving. We also show the 6 pm to 6 am figure, for information only. If you want a different window, tell us before the trial runs; after it runs, the definition is fixed.

For your information (no decision needed):
- Kisiwa's 60 kW generator gets **4.9 L/h** at no load, by the same generic rule that gave Kobo's 40 kW generator your chosen 3.3 L/h. It is labelled generic.
- Every example day at Kisiwa has the same sunny weather, so "before" and "after" differ only by the change.
- When the generator runs, it powers the site and charges the battery. That is how a diesel-hybrid site is normally run, and it is what "stop at 60 % instead of 90 %" changes.
- **Our honest expectation:** the saving may come in under 20 %. It depends on how often the night-time run carries on past sunrise. The half-unit trial tells us before we build anything. If it misses, we stop and come back to you; we never adjust the example to pass.

---

## 8. Ruling DIESEL-1-R2: Kisiwa re-planned around unexplained fuel (supersedes §1, §3–§6 for D1–D5)

- Architect: Claude (fresh Architect), 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `2ca92124a` (MV-1, A1 and D0 merged; CH-5d1 in build).
- Owner decisions now in force, verbatim:
  - `.agent/owner-missing-fuel-2026-11-07.md`: "Before the demo, both"; if the 60 % trial misses, "Kisiwa with missing fuel"; "'Unexplained fuel', never 'theft'" (the "Label the 'after' nights" option was **not** selected); client diesel-heavy or raised missing fuel: "Not specifically".
  - `.agent/owner-scenario-data-2026-11-07.md`: "dont be limited by existing data, data that is reasonable and can reflect a situation can be legitmately added via a scneario for days that are not covered today", and the correction "this is not true, these are injected through operational actions" (§8.2a).
  - Still in force: the night window "6 pm to noon" (`owner-diesel-night-window-2026-11-07.md`), the generic no-load rate rule (`owner-fuel-scope-2026-11-07.md`), no combined savings total, no annualising.
- **§2 (D0) stays as history.** D1–D5 in §1, §3–§6 are **withdrawn**. They are replaced by F0 and K1–K9 below. The design basis is `.agent/fuel-loss-feasibility-2026-11-07.md` Part B; this ruling supersedes it where they differ.
- Paths as in the header: `B/`, `F/`, `T/`, `C/`, `V/`, `S/` = `simulator/assetops_simulator/`.

### 8.1 Disposition of D0

1. **The 4.4 % result is dropped from the demo.** It appears on no screen, in no finish row and in no DS-1 line, not even as "the setting change saved only about 4 %".
   - Reason: a demo claim must come from the product's own evidence path. The 4.4 % came from an agent's in-memory probe; no product code computes it (D2 is withdrawn). Showing it would mean quoting a number the product cannot show.
   - Reason: the owner ruled that the 60 % story "does not go in as a success". A failure beat would need the full night-fuel family (1.75) to be honest, and it would teach the client nothing they need.
   - It stays in `.agent/DIESEL-D0-probe-results.md` as the record. If the client asks, the presenter may say, unscripted and without a figure: "we tested a generator setting on this example site, it didn't meet the bar we set in advance, so we didn't show it."
2. **Kisiwa keeps D0's physics unchanged**, including the stop setting at **90 % throughout** (no setting change in the story) and cycle charging. The template D1 promotes is D0's draft, verbatim in the `foundation` block. D0 is **never re-run with changed assumptions.**
3. **G4 window merge: confirmed.** In the G4 comparison document only, `T/probe_kisiwa_nights.py:192-203` joins adjacent windows whose level is identical. The level at every minute is unchanged. The measured day-runs use the unjoined per-day document. The chained runs and the continuous run matched exactly across *different* window partitions, so the merge makes G4 a stricter check, not a weaker one: equality would have failed if event boundaries alone changed the physics. Conditions:
   - every measured or product run (F0, K7) uses the unjoined per-day document;
   - any later multi-day document joins only identical levels and records the node count;
   - no window is ever split or joined in a way that changes a level.
4. **Kisiwa's dispatch Findings stay.** The product's dispatch analytic will mark Candidate avoidable running on Kisiwa's nights (D0's indicative figure was 190 minutes a night). That is real product output from Kisiwa's readings, priced by fuel-cost-2. It is neither suppressed nor acted on. DS-1 does not narrate it. KIS-2 checks it.
5. **A rainy-season stretch is not proposed.** The new owner guidance allows one, but the unexplained-fuel story does not need it. Kisiwa already burns about 43 L a night. More diesel only widens the expected-use margin (±10 % of use), which makes a removal *harder* to see. No owner question.

### 8.2 Honest presentation of the "after" nights (no special label)

**Ruling: the general example-data labelling is enough, under the conditions below.** The owner did not choose a special label and has since said that reasonable authored days are legitimate. The removal (with the sensor unplugged), the delivery and the dips are authored operational actions (§8.2a), and the clean after-nights are authored days with no removal. Like every Kisiwa day, they are example data and labelled as such through the existing example-data labelling. Honesty then rests on what the product *claims*, which these rules pin:
- **H1. The verdict claims only what the check measures.** VERIFIED says the fuel stayed accounted for within the margin and the sensor reported all night. It never says the seal "stopped", "prevented" or "saved" anything. One fixed line on the verdict page: "This check shows the fuel stayed accounted for after the change; it does not measure how much the change itself prevented." (§8.4 K6).
- **H2. No money on the verification.** No "recovered" or "saved" value is computed for this Action. The Assure card counts it as a verified result with no value line.
- **H3. The Finding's money is a band from evidence.** Litres [low, high] × the declared price, with its own basis, never added to any other money.
- **H4. Wording.** Client copy and DS-1 say "unexplained fuel". They never say "theft", "stolen", "stole", "siphon" or "pilfer", and never imply any of them. A guard enforces this (K9). The two existing "theft" strings in `F/sites/MiniPerformance.tsx:1311` and `:1343` are reworded (K5).
- **H5. Inputs are declared before F0 runs** (§8.3) and never chosen to reach a result.

### 8.2a Owner correction: fuel events enter through operational actions

Owner, verbatim (`.agent/owner-scenario-data-2026-11-07.md`), correcting the coordinator's "where the simulator can't produce something (for example, a removal), an authored scenario input is acceptable": **"this is not true, these are injected through operational actions"**.
- **Binding rule (OA-1).** The fuel removal, the delivery, the hand dips, the tank seal and the sensor power fix are operational actions. None is written into a scenario as a direct state change (`CAUSAL_INPUT` on the tank) or as a reading (`REPORTED_OBSERVATION`). The scenario keeps only the world's own conditions: weather and loads, as in D0.

**What exists today (code reality at `2ca92124a`):**

| # | Mechanism | Where | What it can and cannot do |
|---|---|---|---|
| M1 | Scenario timeline entry kind `INTERVENTION` | `B/scenarios/models.py:93`, `:203-212` | An operator's act, as a `CAUSAL_INPUT` (moves world state) or a `REPORTED_OBSERVATION`. Run setup executes an INTERVENTION cause exactly like an EVENT cause. It is still scenario-authored, so **OA-1 rules it out** |
| M2 | `OPERATOR_RECORD` observation source | `B/scenarios/models.py:274-279`; used by `C/scenarios/fuel-loss-event.yaml:388-450` | A person's written value, Lab-only. **No run, publication or gateway path reads it** (no reader in `B/runs/service.py` or `host/execution_adapter.py`). It never reaches the product |
| M3 | Operator override commands | scenario CONTROL windows declared operator-issued: `B/runs/service.py:2151-2190`, `:3743-3746`; `B/scenarios/models.py:256` `OPERATOR_COMMANDABLE_STATES`; frozen as `OverrideCommand` (`contracts/assetops_contracts/operational_records.py:72-98`); published by `S/observation/records.py:39-120` as `OPERATIONAL_RECORD` envelopes, `record_kind` `OVERRIDE_COMMAND` (`contracts/assetops_contracts/source_envelope.py:126`, `:855-860`) | The only operational action that reaches the product through ingestion today. **CONTROL states only** (generator and battery policy); it cannot address the tank stock. Also scenario-authored |
| M4 | Run-scoped interventions | designed in `.ai/ARCHITECTURE.md:204-214`, `:228` | **Not built.** `intervention_history` is always empty (`B/runs/service.py:719`, `:1376`; `B/runs/models.py:900-918`). Nothing turns an operational action into a world change |
| M5 | Human operational records on the site-first path | `B/work/service.py:36-38` (`OPERATIONAL_KINDS = OPERATOR_LOG, MANUAL_READING, SHIFT_NOTE, SITE_VISIT`), `:470-520` `post_operational_record` (quantity and unit, source document hash, correction chain, idempotency) | **The real operations path for records.** It has no `FUEL_DELIVERY` or `TANK_DIP` kind and no tank link. The technical design names exactly this gap: `frontend/docs/architecture/production-shaped-mvp-technical-design.md:200` ("typed kind (such as fuel delivery) … Define approved record kinds … before FuelBalanceWindow") |
| M6 | W1 Actions and Foundation revisions | `B/actions/` | The lever path: an Action raised from a Finding thread, with an effective instant. Exists |
| M7 | The kernel's declared causes | `contracts/assetops_contracts/world_inputs.py:170-205` `DeclaredCause`; `S/kernel/execute.py:915-940` | Applies INCREASE/DECREASE to any `CAUSAL_INPUT` stock from the frozen world inputs, whatever their origin. This is the hook a run-scoped intervention would use |

**Conclusion: the mechanism is missing on the site-first path.** Records can enter the product the real way (M5, after two new kinds and a tank link). But **no operational action can change the simulated world** without being written into the scenario (M1, M3), and the designed path for that (M4) does not exist.

**Design under OA-1 (Option A, recommended): an operational-action bridge for the tank (new unit K0).**
- **One source per Site:** a versioned, Lab-private operational-action log, `C/operational-actions/kisiwa-001-v1.yaml`. Each action has `action_id`, `at`, `actor` and `kind`. Its effects are derived from the action, never authored separately:

| Action kind | Physical effect on the simulated world (frozen at run setup as a run-scoped intervention, M4, applied through M7) | Product record (through M5's API, the real operations path) |
|---|---|---|
| `FUEL_DELIVERY` | INCREASE on `fuel-tank-volume@fuel-tank` by the delivered volume, at `at` | `FUEL_DELIVERY` operational record: the ticket volume and reference, recorded by the operator 30 min later |
| `FUEL_REMOVAL_UNRECORDED` | DECREASE over its window; plus, when `sensor_disconnected` is given, the tank sensor's reporting path is unavailable over that span (the person unplugs it) | **none**: nobody records it, as in reality |
| `TANK_DIP` | none (a person reads the tank) | `TANK_DIP` operational record. The value is read from the run's tank stock at `at`, rounded half-even to 1 L, by the loader after the run. Never typed |
| `TANK_SEALED`, `SENSOR_POWER_PROTECTED` | none in v1 (no later removal is authored) | Work `SITE_VISIT` record "Tank cap sealed; tank sensor moved to its own protected supply", linked to the W1 Action (M6), which carries the effective instant |

- **Run setup** (`B/runs/service.py`) reads the log for the run's Site and interval and validates each action, with typed refusals: the component exists; the stock is a `CAUSAL_INPUT` stock in the model; the unit is L; a delivery fits free capacity at `at` (else refused, never clamped); the removal does not exceed the stock. It then freezes the physical effects as `DeclaredCause`s (and the reporting-path span as a reporting condition). Each one carries origin `OPERATIONAL_ACTION` and the action's content hash, listed in `deterministic_identity.intervention_history`.
- **Runs with no actions are byte-equal** (empty history, as today). That is a stop condition for K0.
- **The product never reads the log.** Analytics read only the M5 records and accepted readings, so the Lab-private removal stays private truth.

**Option B (cheaper, not OA-1-faithful): M1 from the same log.** The loader turns each physical effect into a scenario `INTERVENTION` entry, and the records go through M5 as in Option A. That is about +0.25 instead of K0's 2.0. It still writes the change into the scenario, which the owner's correction rejects, so it is offered only as an owner choice (§8.10 Q1).

**Sizes:**
- **K0 operational-action bridge: 2.0** (range 1.5–3.0): contract origin and history 0.5; run setup read, validation, freeze and parse 0.75; host and kernel application plus the reporting-path span 0.5; tests (byte-equal for runs with no actions, refusals, L2 setup) 0.25.
- **K2 becomes M5's extension** (same 0.75, §8.4).
- **K7 +0.25** for the action-log injector.
- **Net +2.25** over §8.4's figure.

### 8.3 F0: the Kisiwa fuel-events probe (full ruling, ready for a builder now), 0.5

**Purpose.** In memory, with no DB, no product code and no suite, answer six questions. **Question 0 is the operational-action path (§8.2a) and comes first:**
0. **The bridge hook.** On a Kisiwa run built by normal run setup from a weather-and-loads-only scenario, can the frozen world inputs carry extra `DeclaredCause`s **that no scenario entry produced**, and does the kernel apply them (M7) without a provenance refusal? Can a reporting-path span be added to the run's reporting inputs the same way? The probe adds them with `dataclasses.replace` on the frozen run, standing in for K0's run setup. **No scenario `CAUSAL_INPUT`, `INTERVENTION` or `REPORTED_OBSERVATION` entry is written (OA-1).** Also confirm, by code reading with file:line, that M2 and M3 cannot carry a tank action or a dip into the product, and that `intervention_history` has no reader that would refuse a non-empty value. The answer sizes K0.
1. Does `mini-grid` v6 apply the delivery (INCREASE, POINT) and the removal (DECREASE, WINDOW) on `fuel-tank-volume@fuel-tank` through that hook?
2. Does the removal's sensor-disconnected span silence `fuel-level-sensor/fuel-level`?
3. Is dispatch unaffected?
4. Does the declared `fuel-balance-1` band (below) flag the removal night and no other night, both from the true tank and from the published readings?
5. Does the registered publication path publish Kisiwa's tank level, and why does Kobo store 0 `fuel_level` rows (`.agent/build-sheet-DD-1.md:1934`)?

**Code reality the builder starts from:**
- The mini-grid tank stock is a `CAUSAL_INPUT` STOCK handler with `consume=daytime._apply_to_stock` and floor 0 (`S/packs/mini_grid.py:192-207`). Its statement says "moved only by accepted generator energy". Only the minimal fuel model has exercised authored INCREASE/DECREASE (`S/packs/fuel.py:93-101`; `C/scenarios/fuel-loss-event.yaml:329-357`, `:452-478`). For mini-grid this is unverified, hence F0.
- `registered-kobo-publication` v1–v5 inherit Lab v3's `fuel-level-sensor/fuel-level` (15 min, bias −0.5 L, dropout 40/1000) and the `fuel-level-reporting-availability` forcing state (`B/runs/profiles.py:1426-1470`, `:1843-1860`, `:1873-1890`, `:1911-1945`, `:1985-2000`, `:2052-2058`). Kobo still stores 0 tank rows. F0 finds the stage that drops them.
- In-memory publication: `host/execution_adapter.py:679` `reporting_inputs(run)`, then `S/observation/transform.py:224` `generate_observations(trajectory.boundaries, reporting)` (as `host/tests/test_generator_observation.py:466-469`). The gateway `publish(observations, mapping_set, …)` is `S/gateway/publish.py`. `SIMULATOR_LAB_DISPATCH_MAPPINGS` includes the fuel-level entry (`S/gateway/mappings.py:105-108`).

**Declared world (fixed now, before any run; never tuned).** Everything in §2.2 is unchanged except the start fuel and the operational actions:

| Item | Value | Basis |
|---|---|---|
| Runs | **10** day-runs, 15:00–15:00 local (§2.3 shape), run 1 at `2026-10-01T12:00:00Z`, chained at full precision, stop 90 % throughout | D0's run shape |
| Start fuel, run 1 | **700 L** of 1000 | A site between deliveries, so a delivery fits below capacity (the Lab's capped-delivery false positive is excluded). Not outcome-dependent: dispatch is never fuel-limited |
| Operational action `FUEL_DELIVERY` | **300 L**, **10:00 local on the morning that closes night 2** (run 2, offset 1140 min), actor "Fuel supplier". Ticket 300 L | The Lab scenario's figure, reused (`fuel-loss-event.yaml:466-474`) |
| Operational action `FUEL_REMOVAL_UNRECORDED` | **120 L** over **45 min, 01:00–01:45 local in night 4** (run 4, offset 600 min), actor "Unidentified", with `sensor_disconnected` **00:50–02:20 local** (run 4, offset 590 min, 90 min) | The Lab scenario's figure, duration, 10-min lead and 90-min span, reused (`:329-386`). Under OA-1 the gap is the same person's act (unplugging the sensor), not a scenario forcing |
| Operational action `TANK_DIP` | night 4 morning round **07:00 local**; after the change, **06:00 and 18:00 local** every day in runs 6–10; actor "Shift operator". Value = the tank stock at that instant, rounded half-even to **1 L** (dipstick reading) | Read from the trajectory, never typed |
| Operational actions `TANK_SEALED`, `SENSOR_POWER_PROTECTED` | at the change instant (below); no physical effect in v1 | Recorded only (§8.2a) |
| Where the actions live in F0 | `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml`, in K0's log format (K0 promotes it verbatim to `C/operational-actions/kisiwa-001-v1.yaml`) | One source for effects and records |
| Change instant (for partitioning only) | 15:00 local at the start of **run 6**. Before = nights 1–5 (night 4 = incident); after = nights 6–10 | Action is agreed the day after the Finding and done the next afternoon (K7) |

**`fuel-balance-1` parameters (declared now; K3 implements exactly these; any change is a new parameter version, never a retune):**
- Window = night k, 18:00 local to 12:00 local next day (owner window).
- **Opening** = the last accepted `fuel_level` reading in `[start − 30 min, start]`. **Closing** = the first in `[end, end + 30 min]`. If either is missing, the window is `NOT_ASSESSED` (limitation `MISSING_OPENING` / `MISSING_CLOSING`).
- **Tank margin** = 2 × a, where a = the Foundation `fuel-level-sensor-accuracy` = **10 L**, basis `GENERIC_DEFAULT` (1 % of a 1000 L tank, a common level-sensor class). Applied to opening and closing, combined linearly.
- **Deliveries** D = Σ ticket volumes of `FUEL_DELIVERY` records with instant in `[start, end)`. Tolerance = Σ 1/100 × ticket.
- **Use**, from the generator readings per 5-minute slot: loaded = Σ kWh × SFC (as known); idle hours = RUNNING slots at 0 kWh (A2's slot rule). `use_low = 9/10 × loaded`; `use_high = 11/10 × (loaded + idle_h × r)` (fuel-cost-2's multiplier and no-load rate r). The low edge counts no idle fuel, because the simulator burns none; that is the honest band from FUEL design B1.
- `residual_low = (O − C) + D − D_tol − use_high − 2a`; `residual_high = (O − C) + D + D_tol − use_low + 2a`. Exact Fractions.
- **States:** `UNEXPLAINED` iff `residual_low ≥ 40 L` (materiality, about one normal night's diesel); `WITHIN_MARGIN` iff `residual_low ≤ 0 ≤ residual_high`; `BELOW_MATERIALITY` iff `0 < residual_low < 40`; `EXCESS` iff `residual_high < 0` (more fuel than explained, e.g. an unrecorded delivery; reported, no Finding in v1).
- **Reporting gap minutes** = Σ over spans longer than **60 min** between consecutive accepted `fuel_level` readings inside the window, including the edges. A single or double dropout (30–45 min) is not a gap.

**Architect's pre-registered expectation (arithmetic, written before any run):** night use about 43.4 L (D0, since dispatch is unchanged). Incident night: residual ≈ [120 + 43.4 − 47.8 − 20, 120 + 43.4 − 39.1 + 20] ≈ **[95.7, 144.3] L, UNEXPLAINED**, gap 90 min. Clean nights ≈ [−24.3, +24.3] L, WITHIN_MARGIN. The delivery night ≈ [−27.3, +27.3] L, WITHIN_MARGIN.

**Gates (each one asserted; a failing gate stops the run):**
- **F0a (operational-action path)**:
  - each run is set up from a scenario holding **only** weather and load entries (grep of the documents: no tank `CAUSAL_INPUT`, no `INTERVENTION`, no `REPORTED_OBSERVATION`, no reporting-availability entry);
  - the actions enter only through the frozen-input hook, with origin `OPERATIONAL_ACTION` and their content hash on each added cause;
  - the kernel applies them, or refuses with a reason the builder reports verbatim.
  - Also report: (i) every place a frozen cause's provenance is checked against scenario entries (file:line), i.e. what K0 must extend; (ii) whether the host's `reporting_inputs` takes an added reporting-path span; (iii) the M2 and M3 findings and the `intervention_history` readers. These code facts go in the evidence file as K0's starting map.
- **F1** every run READY and `run_to_end` completes with the actions applied.
- **F2** tank law per step, exactly: `tank[i+1] = tank[i] − E_i × SFC − removal_i + delivery_i`. Σ removal = 120 and Σ delivery = 300 exactly. Report how the kernel spreads the removal over the 45 min (per-step litres).
- **F3** dispatch unaffected: a reference chain of the same 10 runs from the same start state, **without** the operational actions, has equal generator state, accepted generator energy and battery level at every boundary, exactly. Every night's litres equal D0's 43.428 L.
- **F4** no fuel-limited step (`mini_grid.py:683-684` note absent).
- **F5** publication on `registered-kobo-publication` v5, drafted for Kisiwa: fuel-level observations at 15-min cadence; **none** with an instant in `[00:50, 02:20)` of night 4; at least one in the 30 min before and the 30 min after the gap; bias −0.5 L.
- **F6** the registered path, in memory: publish the F5 observations through the mapping set the registered gateway uses for Kobo (the builder names it from code). Report whether fuel-level envelopes are produced. Report, with file:line, the stage at which Kobo's tank readings are dropped today (publication, mapping, binding role config or acceptance). **Not a stop**; it sizes K1 (§8.4).
- **F7** each per-day document's node count is below 4000; record the largest.
- **F8** determinism: `--check` gives byte-equal JSON.
- **F9** band results from **both** sources, (i) the true stock and (ii) the F5 readings (opening and closing chosen by the rule above): night 4 is `UNEXPLAINED` with gap > 0; every other night is `WITHIN_MARGIN` with gap 0; no night is `NOT_ASSESSED`.
- **F10** D0 untouched: `T/probe_kisiwa_nights.py --check` still prints "probe result current", and no D0 file changes.

**Stops (report to the Architect; never design around them):**
- **S0 (OA-1).** The only way to move the tank or open the gap is a scenario entry. **Never** fall back to writing one. Report it; K0's size is then re-ruled (a kernel or host provenance change).
- **S1 refusal** (F0a/F1). Report the refusal verbatim and the smallest fix. Candidates: a cause-origin field in the contract (K0); the stock statement or role in a new `mini-grid` version; a Kisiwa model version (+0.5–1.0). The Architect rules.
- **S2** F2 or F3 fails.
- **S3** F9 differs from the expectation: the incident night is not flagged, a clean night is flagged, or a night is NOT_ASSESSED because of dropout. Report the night and its terms. **Never** change the removal size, times, materiality, accuracy, tolerances, cadence, dropout or seed.
- **S4** F5 fails (the gap does not silence, or the profile refuses the forcing state).
- **S5** F7 over 4000 on a single day. Report it; the Architect rules on splitting the run.
- **S6** the work exceeds 0.75 unit.

**Files (all new; D0's files byte-equal):**
1. `T/probe_kisiwa_fuel.py`: **imports** `kisiwa_site`, `day_document`, `measure_night`, `stop_at` and the constants from `T/probe_kisiwa_nights.py`, never editing it.
   - `kisiwa_registered_draft(document, start, end)` copies `kisiwa_draft`'s pattern (`:130-157`) with the `registered-kobo-publication` v5 profile.
   - The scenario is `day_document(...)` **unchanged** (weather and loads only). `load_actions(path)` parses the draft operational-action log. `apply_actions(run, actions)` adds the run's physical effects to the frozen world inputs (and the reporting span to the reporting inputs) as `DeclaredCause`s with origin `OPERATIONAL_ACTION`, the F0a hook. `dip_values(trajectory, actions)` reads the dips.
   - `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml` (new) is the action log above.
   - `balance(window_terms)` = the parameters above as one pure function.
   - CLI: `--write` writes `.agent/DIESEL-F0/probe-result.json`; `--check`; `--handover` is K7's and is not built now.
2. `host/tests/test_probe_kisiwa_fuel_band.py` (L0, no DB): `balance` on hand-built terms. The incident terms give exactly `Fraction` [95.7…, 144.3…]; a clean night contains 0; residual_low at exactly 40 is UNEXPLAINED; 39.999 is BELOW_MATERIALITY; residual_high < 0 is EXCESS; gap spans of 60 and 61 min.
3. `.agent/DIESEL-F0/probe-result.json` (schema `{"id": "assetops.kisiwa-fuel-probe", "version": 1}`): assumptions, the per-step tank account for night 4, per-night terms and states (both sources), the derived dip values, gates, F6 findings.
4. `.agent/DIESEL-F0-probe-results.md`: a plain-words line ("Kisiwa fuel check (example data, simulator): on the night 120 L was taken out, the check found {lo}–{hi} L unexplained; on the other 9 nights it found nothing outside the margin."), the per-night table, gates, F6 findings, seconds per run, and the stop if any.

**Run** exactly as §2.10, with branch `task/DIESEL-F0-kisiwa-fuel-probe` and worktree `C:\Users\assef\Bineyame\AssetOpsV1-f0`, from main at or after `2ca92124a`. No DB, no prepare, no suite, no `-ExecutionPolicy`.
- **Reading budget:** this §8.1–§8.3 (with §8.2a); `contracts/assetops_contracts/world_inputs.py:140-300`; `S/kernel/execute.py:880-960`; `B/runs/service.py:700-730`, `:2140-2200`, `:3740-3760`; `B/work/service.py:30-40`, `:470-520`; `T/probe_kisiwa_nights.py`; `C/scenarios/fuel-loss-event.yaml:300-480`; `S/packs/mini_grid.py:180-210`, `:405-440`, `:635-740`, `:880-895`; `S/packs/fuel.py:80-110`; `host/execution_adapter.py:670-720`; `S/observation/transform.py:200-260`; `host/tests/test_generator_observation.py:60-110`, `:440-520`; `B/runs/profiles.py:1400-1470`, `:1840-1870`; `S/gateway/mappings.py`.
- **Review:** one fresh Opus reviewer. It re-runs both `--check`s and reads the events against the table and `balance` against the parameters.
- **Merge** on ACCEPT, whatever the result.

### 8.4 Units K0–K9 (outlines with decisions pinned; each gets one consolidated card after F0 and the owner's Q1 answer, inside the contingency)

| Unit | Delivers | Size | Depends on (merged) | Migration |
|---|---|---|---|---|
| **F0** | §8.3 | 0.5 | none (now) | none |
| **K0** operational-action bridge (§8.2a, Option A; owner Q1) | The Lab-private action log `C/operational-actions/kisiwa-001-v1.yaml` (F0's draft promoted). Run setup reads, validates and freezes the physical effects as run-scoped interventions (`DeclaredCause` origin `OPERATIONAL_ACTION`, content hash in `intervention_history`) plus the reporting-path span. Host and kernel apply them. Files: `contracts/assetops_contracts/world_inputs.py`, `B/runs/service.py`, `B/runs/parsing.py`, `B/runs/models.py`, `host/execution_adapter.py`, `S/kernel/execute.py` (only if F0a shows it is needed), tests. **Stop:** any digest or byte change for a run with no actions | 2.0 (1.5–3.0) | F0 | none (file-based log) |
| **K1** Kisiwa Site | D1 (§3.1) as written, **plus** the Foundation vocabulary `fuel-level-sensor-accuracy` (L, PHYSICAL) and `fuel-level-sensor-accuracy-basis` (state: `GENERIC_DEFAULT`, `MANUFACTURER_DATASHEET`, `SITE_CALIBRATION`), carried by `FUEL_TANK` in `B/sites/models.py` (A1's pattern), declared at Kisiwa as 10 L `GENERIC_DEFAULT` with the note "Generic level-sensor accuracy, about 1 % of a 1000 L tank; not this sensor's calibration". The tank publishes on the registered profile, fixed per F6 | 1.25 (+0.25–0.5 if F6 needs a new publication profile version) | F0, A1 | none |
| **K2** fuel records on the operations path (M5) | Extend Work operational records (`B/work/service.py:36-38`, `:470-520`, its model and store): add kinds `FUEL_DELIVERY` (quantity L and `source_document_sha256` for the ticket, required) and `TANK_DIP` (quantity L, required), and a nullable `asset_id` tank link, required for these two kinds and refused on others. Existing kinds and corrections are byte-equal. Add an as-known read `fuel_records(site, tank, window, known_at)` for K3. **Not a telemetry envelope:** the contract's `OPERATIONAL_RECORD_KINDS` (`source_envelope.py:126`) is untouched. **Changed by OA-1 from a separate table:** this is the record path real operations use, and the one the technical design names | 0.75 | F0 | **0054** (widen the kind CHECK, add `asset_id`) |
| **K3** `fuel-balance-1` | Pure rules (§8.3 parameters, verbatim), service and store; one stored row per night per Site with a bound `fuel_level` and a declared accuracy. States and limitations (`MISSING_OPENING`, `MISSING_CLOSING`, `REPORTING_GAP`, `DIP_SENSOR_CONFLICT` when \|dip − nearest sensor\| > a + 10 L, `DELIVERY_RECORDED_LATE`). Reuses A2's slot rule and the as-known SFC and no-load history; it never re-derives them. Parameter version `fuel-balance-1/v1`. It never feeds the dispatch consequence. Kobo (no accuracy declared) gets `NOT_ASSESSED`; `mini_depth.rules.assess_fuel_hour` and Kobo's Fuel page are byte-equal | 1.5 | K1, K2 | **0055** `0055_fuel_balance_window.py` |
| **K4** UNEXPLAINED_FUEL Finding | The Finding kind raised from an `UNEXPLAINED` window (one per window, existing thread and recurrence rules). Consequence model `fuel-residual-1` = [residual_low, residual_high] L × the declared diesel price as known at the window end (`select_window_price`), basis `UNEXPLAINED_FUEL_AT_DECLARED_PRICE`, never added to fuel-cost-1/2 rows. Kisiwa board **Protect** row: "Fuel" contributor from the window (replacing `NO_FUEL_BALANCE`, `B/site_outcomes/mini.py:77`, `:873-877`, only where a window is assessed) and the thread line; chain vocabulary and claims | 2.0 | K3; **board/chain part after CH-5d1, MB-1, A3, PV-1** | **0056** (Finding kind and consequence model CHECKs) |
| **K5** fuel screens | Site Performance › Fuel in **window mode** (night list; v69 `:623-630` cards, waterfall and bridge filled), a list of deliveries and hand dips, and the Finding's fuel panel. **MD-FUEL-K-1:** a night window, not the mock's Kobo hour. **MD-FUEL-K-2:** the notice and the RESIDUAL row reworded on every Site (owner wording rule, below). Layout evidence at 1440 and 390 | 1.0 | K3; the Finding panel after K4 | none |
| **K6** `fuel-residual-within-band-1` | The verification family and page (§8.5) | 1.5 | K4, MV-1, A2 | **0057** (0052 pattern: widen `rule_id`/`plan_version`, the family CHECK with reserve columns NULL) |
| **K7** Kisiwa story data | D3 (§3.3) as written, **with** 10 runs (§8.3 table). The per-day scenarios hold weather and loads only (OA-1); the fuel actions come from K0's log. `T/probe_kisiwa_fuel.py --handover` writes `V/kisiwa-day-handover-v1.json` (start states **and** dip values; `--check` guards it). The action-log injector posts each action's record through the Work API (delivery ticket recorded 30 min after delivery; dips signed by "Shift operator"; the SITE_VISIT for the seal and sensor fix), then the Action (§8.6), plan freeze and evaluation. One Kisiwa-only scratch prepare: stored windows equal F0 (exact), then drop | 2.25 | K0, K1, K2 (data part); K6 (freeze step) | none |
| **K8** four Sites on estate screens | D4 (§3.4) **minus** the Assure value line (H2), **plus** the Protect card Kisiwa unexplained-fuel line "{site} · {code}: about {lo}–{hi} L unexplained fuel, {lo$}–{hi$} {cur} at your declared price" (own basis, never summed). The Assure count includes the Kisiwa verified result. MD-FUEL-D-1 kept | 1.0 | PV-1, A3, CH-5d1, K4; captures after K7 | none |
| **K9** finish, guard, rehearsal | KIS-1–KIS-8 (§8.7), COH-17 and V4 for Kisiwa, **wording guard** (a new check in `tools/checks/`, wired into `check-all`): served copy and `F/` strings contain none of theft/stolen/stole/siphon/pilfer (case-insensitive; tests and code comments excluded), with a self-test. Whole-list rehearsal prepare (3 h cap). DS-1 beat (§8.6) | 1.0 | all | none |
| Contingency | Card round after F0, the F6 publication risk, the K4 Finding-kind risk | 0.5 | | |
| **Total** | | **14.75 remaining** (15.25 with D0's spent 0.5); range 13.0–17.5. With Option B instead of K0 (owner Q1): 12.75 remaining | | |

**Wording (K5, MD-FUEL-K-2), literals:**
- Notice (replaces `MiniPerformance.tsx:1311`): "Unexplained fuel is fuel that left the tank that the generator's running and recorded deliveries don't account for, within a stated margin. It does not say why the fuel left, and it is never added to the generator's possible extra fuel."
- RESIDUAL row (replaces `:1343`): "Needs every term with a supported range; never says why fuel left".
- These are the only Kobo Fuel page bytes that change.

**Finding literals (K4; the guard and guard V apply):**
- Title: "Unexplained fuel overnight".
- Line 1: "About {lo}–{hi} L left the tank on the night of {date} (6 pm to noon) that the generator's running and recorded deliveries don't explain."
- Line 2, only when the gap is above 0: "The tank sensor sent no readings from {a} to {b}."
- Money: "Worth about {lo$}–{hi$} {cur} at your declared {p} {cur} per litre. This does not say why the fuel left the tank."
- Litres to 0.1, money by `money2`; the browser formats no number.

**File and migration conflicts:**
- **Migrations: A1 owns 0053 (merged).** The earlier D2 claim on 0054 is **void** (D2 is withdrawn). The new chain is **K2 0054 → K3 0055 → K4 0056 → K6 0057**, each with `down_revision` = the previous one. FUEL-1 lanes (A2, A3, MB-1, WD-1, PV-1) and CH-5d1 add none. If any other merge lands a migration first, the next K unit renumbers; the single-alembic-head test catches a miss.
- **K4 ↔ MB-1, A3, PV-1, CH-5d1:** `B/site_outcomes/mini.py`, `board.py`, `B/chain/vocabulary.py`, `B/chain/claims.py`, `T/checks/chain_coherence.py`. K4 builds the Finding, consequence and store first; its board and chain edits wait for lane 1 to finish (PV-1 merged).
- **K5 ↔ none:** `F/sites/MiniPerformance.tsx` is not edited by lanes 1–2.
- **K0 ↔ none:** no lane 1–2 unit or CH-5d1 edits `B/runs/`, `host/execution_adapter.py`, the contracts or the kernel. K0's stop guards Kobo, Cold and EV run digests.
- **K2 ↔ none:** no lane 1–2 unit edits `B/work/`. The Work tests (`test_w401_*`) must stay green.
- **K6 ↔ A2:** `B/actions/verification.py`, `verification_rules.py`, `verification_families.py`. K6 starts after A2 merges.
- **K8 ↔ CH-5d1, PV-1:** `B/site_outcomes/read.py`, `F/estate/PortfolioOutcomes.tsx`. K8 goes after both; the CH-5d1 Optimize card and PV-1's Assure lines stay byte-equal for the three existing Sites.
- **K9 ↔ MV-1, MB-1, A3, PV-1:** `T/demo_combined_finish.py`, last.
- **Data effects (no edit; tell the lanes):**
  - CH-5d1's Optimize card takes the "two or more priced Sites" path (Kobo idle mornings after A3, and Kisiwa's dispatch Findings), never summed.
  - PV-1's Assure card gains **no** line (H2), so PV-A is unchanged.
  - The all-26 audit is recaptured in K8.

### 8.5 K6 decisions (verification)

- **Origin:** a W1 Action raised from the UNEXPLAINED_FUEL Finding thread. Plan version `fuel-residual-verification-1`.
- **Baseline:** the Finding's own window (stored id). **Later:** the first 3 COMPLETE nights whose window starts at or after the Action's effective instant, looking ahead at most 14.
  - COMPLETE = the window is not `NOT_ASSESSED`, and every generator-state and generator-power slot is COMPLETE (the mill's weakest-row rule).
  - Chosen by grade, never by value.
  - The night choice is built here, because D2 is withdrawn (+0.25 against the feasibility's 1.25).
- **Target (frozen in the plan):** `{"rule": "every later night: residual_low <= 0 <= residual_high and reporting_gap_minutes == 0", "over": "first 3 COMPLETE nights after the change", "basis": "owner-reviewed design, fuel-loss-feasibility Part A §3 Verify, chosen 2026-11-07"}`.
- **Verdicts:** VERIFIED (all 3 pass); INEFFECTIVE (any later night fails); INCONCLUSIVE (fewer than 3 COMPLETE nights in 14). All recorded truthfully.
- **Page** `F/sites/SiteFuelResidualVerification.tsx`, reusing the mill page's components and CSS.
  - VERIFIED line: "On {n} fully checked nights after the change, the tank's fuel matched the generator's running and recorded deliveries within the margin, and the tank sensor reported all night."
  - Fixed line (H1), always shown: "This check shows the fuel stayed accounted for after the change; it does not measure how much the change itself prevented."
  - No money, so no mock deviation is needed for money.

### 8.6 Story (K7) and DS-1 beat

- **Action**, raised from the Finding thread at 12:30 local on the day after night 4 (after the closing reading):
  - title "Seal the tank cap, sign the dip log at every shift change, and put the tank sensor on its own protected power supply";
  - effective at 15:00 local on run 6's start (done the next afternoon);
  - plan frozen at that instant.
- **Night 5** (Finding raised, change not yet done) is authored clean. That is reasonable and is not counted in either window.
- **After the change:** dips at 06:00 and 18:00 local each day, signed. The after-nights have no removal and no gap (authored, under the owner's scenario guidance; §8.2).
- The evaluation runs after night 8 is graded. Dates are fixed in K7's card so that night 8 closes before the S+0 board cutoff.
- **DS-1 beat (draft):** "Kisiwa: one night, about {lo}–{hi} L left the tank that the generator and deliveries don't explain, while the tank sensor was silent → seal the cap, sign the dip log, protect the sensor's power → the next 3 checked nights stayed within the margin with the sensor reporting. We say unexplained, not why; this is example data."

### 8.7 Finish rows (written in K9, run at E3)

| Row | Checks |
|---|---|
| KIS-1 | `KISIWA-001`; diesel price v1, no-load 4.9 L/h `GENERIC_DEFAULT` and sensor accuracy 10 L `GENERIC_DEFAULT`, as known; stop setting 90 throughout |
| KIS-2 | Kisiwa dispatch Findings are SUPPORTED and priced fuel-cost-2, with `quantity_high` computed from stored segments |
| KIS-3 | Every stored night window's band reproduces from its stored terms and the declared parameters (Fractions); night 4 is UNEXPLAINED and all others are WITHIN_MARGIN, as computed, never forced |
| KIS-4 | The Finding's money band = stored litres × the declared price; no field equals a sum with any dispatch money |
| KIS-5 | The verdict as computed from stored windows (INEFFECTIVE recorded truthfully if so); no money on the page |
| KIS-6 | Portfolio and estate list four Sites; counts equal the boards |
| KIS-7 | CH-5d1's Optimize card on the ≥2-priced-Sites path, with no sum |
| KIS-8 | The Protect card Kisiwa line equals its source; the wording guard is clean on served pages |
| re-expected | COH-17 and V4 (Kisiwa), F-THREADS (the Kisiwa thread) |

### 8.8 Order, totals, date, E3

```
now (t=0):   CH-5d1 (lane 1, finishing) | A2 (lane 2) | F0 (lane 3)
t≈0.5:       F0 result -> card round (contingency) | K2 (lane 3)
t≈0.55:      A2 merged -> K1 (lane 2)
t≈0.75:      CH-5d1 merged -> MB-1 -> WD-1 -> PV-1 (lane 1, to ≈2.9)
t≈1.25:      K2 merged (0054)
t≈1.8:       K1 merged -> A3 (lane 2, after MB-1) | K3 (lane 3, 0055)
t≈2.5:       A3 merged -> K0 (lane 2, after the owner's Q1 answer; to ≈4.5)
t≈4.5:       K0 merged -> K7 data part (lane 2, to ≈6.0)
t≈2.9:       PV-1 merged -> K5 fuel page (lane 1, after K3)
t≈3.3:       K3 merged -> K4 (lane 3, 0056; board part after PV-1)
t≈5.3:       K4 merged -> K6 (lane 3, 0057) | K8 code (lane 1) | K5 Finding panel
t≈6.8:       K6 merged -> K7 freeze step and Kisiwa scratch prepare (≈7.3)
t≈7.3–7.5:   K8 captures -> merged
t≈7.5–8.5:   K9 (finish rows, guard, rehearsal prepare)
then:        DS-1 -> E1–E6
```

- **Critical path:** F0 → K1 → K3 → K4 → K6 → K7 freeze → K8 captures → K9 ≈ **8.5 lane-units ≈ 2.8 working days**, plus the Kisiwa scratch prepare (about 40 min) and one rehearsal prepare (about 1.5 h).
- K0 runs on lane 2, off the critical path: K7's data part needs it only by about t≈6.8, when K6 merges.
- **Remaining before DS-1:** lanes 1–2 **4.5** (CH-5d1 0.75 + MB-1 1.25 + WD-1 0.15 + PV-1 0.75 + A2 0.55 + A3 0.7 + E3 allowance 0.35; the coordinator confirms CH-5d1's remainder) + Kisiwa **14.75** = **19.25** (Option B: 17.25).
- **Plan total:** ≈ 117.3 (FUEL-1) + 15.25 = **≈ 132.55** (Option B: ≈ 130.55). This replaces the earlier ≈ 124.3 with the withdrawn D lane.
- **Demo date:** about **+3 working days** (range 2.5–5) against the lanes-1–2 plan without Kisiwa. K0 adds effort but sits off the critical path; its slip risk widens the top of the range. That is about +1 more than the withdrawn D-lane plan, and inside the "about 4–5 working days later" the owner accepted with "Kisiwa with missing fuel". Without Kisiwa, DS-1 would start after about 1 working day of lanes.
- **E3:** 10 Kisiwa day-runs at an estimated 150–200 s each with the pipeline (D0: about 1 s in memory per run), plus one 15-min tank signal and a few records: **+25–35 min**, so **E3 ≈ 1.3–1.5 h of the 3 h cap**. K7 records seconds per day and K9 restates the figure. If the rehearsal exceeds 2.5 h, the Architect rules before E3; the cap is never raised silently.

### 8.9 Plan HTML (`Docs/demo-sprint/client-demo-plan.html`) rows to change

The coordinator carries FUEL-1's delta first (§6 of FUEL-1), then:
1. **Build-units table:** replace the "DIESEL-1 … D0–D5 … 7.0" row (or add, if not yet carried) with "DIESEL-1-R2 Kisiwa diesel-hybrid example Site with the unexplained-fuel story (owner 2026-11-07: Kisiwa with missing fuel; 'unexplained fuel', never 'theft'; fuel events through operational actions)", **15.25** (D0 0.5 done, F0 0.5, K0 2.0, K1 1.25, K2 0.75, K3 1.5, K4 2.0, K5 1.0, K6 1.5, K7 2.25, K8 1.0, K9 1.0, contingency 0.5). Note: "the 60 % generator-setting trial (D0) was not met at 4.4 % and is not shown in the demo". If the owner picks Option B: 13.25 without K0.
2. **Total row:** ≈ 132.55; lanes +15.25.
3. **G5 freeze and G6:** +15.25 (DIESEL-1-R2) on top of FUEL-1's +5.35 and CH-5d's −0.25.
4. **Lanes schedule table and figure:** a lane 3 strip F0 → K2 → K3 → K4 → K6 → K9; K1, then A3, K0 and K7 on lane 2; K5 then K8 on lane 1 after PV-1 (§8.8).
5. **E3 row:** "Kisiwa: 10 day-runs, +25–35 min; E3 ≈ 1.3–1.5 h of the 3 h cap".
6. **Machine-time note:** +1.5 h rehearsal prepare (K9) and +40 min Kisiwa scratch prepare (K7), both before E3.
7. **Calendar estimate line and OD-P9:** G6 moves about +3 working days (range 2.5–4.5) against the plan without Kisiwa.
8. **Rulings table:** a "DIESEL-1-R2" row pointing to this §8: D0 dropped from the demo, G4 merge confirmed, F0 ruling, OA-1 and the operational-action bridge (§8.2a), the fuel-balance-1 parameters, migrations 0054–0057, and no special label for the after-nights (H1–H5).
9. **After-the-demo list:** remove any "Kisiwa unexplained fuel ≈ 8.5" entry; keep "Kisiwa measured tank or flow panel (simulator idle law)". BL-16's tank half is now done by K1/K3 for Kisiwa only.

### 8.10 Owner questions

1. **How do fuel deliveries, the missing fuel and hand dips get into the example site?** You told us these come in through operational actions, the way real operations would. Today the product can *record* what people do, such as notes and readings, and with a small addition it can record fuel deliveries and dips. But nothing yet lets a recorded action change the simulated site itself: today the tank only changes if we write the change into the example day directly, which you ruled out. Options:
   - **(a) Recommended:** build that link. Each action (delivery, missing fuel, dip, the seal and sensor fix) is written once. The simulated tank changes because of it, and the records reach the product the normal way. The missing fuel has no record, as in real life. About **+2 units**. It runs beside other work, so the demo date moves little (range widens by about half a day).
   - **(b)** Keep the same single list of actions, but have the tool turn each one into an "operator action" entry in the example day, with the records going in the normal way. About +0.25 units. It is cheaper, but the change still sits inside the example day, which is what you said not to do.

   The half-unit trial (F0) runs now either way and tests the link in memory first, so nothing is built before you answer.

For the owner's information, in plain words:
- The 60 % generator-setting trial saved about 4 % of diesel a night against your 20 % bar, so we leave it out of the demo entirely rather than show a weak result.
- The nights after the fix are example data like every other Kisiwa day. The screen claims only that the fuel stayed accounted for afterwards, never that the fix stopped a loss. So no extra label is needed.
- Kisiwa will also show the usual "generator ran when the battery could have carried the load" findings; they are real results from its data, and we don't narrate them.
- We are not adding a rainy-season stretch: more diesel would make missing fuel harder to see, not easier.
- Kisiwa adds about 3 working days before the demo (range 2.5–5), within the 4–5 you accepted.

---

## 9. Ruling DIESEL-1-R3: after F0's stop (registered probe path, tank-level signal, K0 extended, F0 re-issued)

- Architect: Claude (fresh Architect), 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `826d91572` (CH-5d1 merged). F0 evidence read on `task/DIESEL-F0-kisiwa-fuel-probe` at `aa49a18fd` (`.agent/DIESEL-F0-probe-results.md`, `T/probe_kisiwa_fuel.py`, the draft action log).
- Owner decisions in force, verbatim: `.agent/owner-kisiwa-scope-2026-11-07.md` (build with the operational-action link, i.e. §8.2a Option A, K0); `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions"); `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'").
- **This section amends §8.3 (F0), §8.4 (K0, K1, totals) and §8.8–§8.9.** Everything else in §8 stands. Where §8 and §9 differ, §9 wins.
- **F0's stop was correct and is accepted as history.** The builder reported S1 verbatim, tried no fix and changed no declared item. F0 spent its 0.5 unit. Nothing in §8.3's declared world, parameters or pre-registered expectation changes.

### 9.1 Decision 1: the S1 fix for the probe — neither (a) nor (b) as proposed; (c) register Kisiwa in memory through the product's own import, conversion and selection code

**Ruling (c).** F0r registers Kisiwa in an `InMemoryFoundationStore` with the same calls K1 will make against Postgres, then sets up every run through the **real** `RegisteredLabBasis` over that store. Only the storage engine is substituted.
- `B/sites/foundation_service.py:247` `import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=ImportSource(path, sha256, record), legacy_documents=(), clock=…)` with the Kisiwa Site record (D0's `kisiwa_site()` rendered document; `B/sites/adapters/import_files.py:46` `read_import_source` if a file is needed, written to the scratch folder, never to `C/`).
- `B/sites/binding_conversion.py` `convert(store, BindingService(store, clock), tenant, site, fixture)` with a new draft fixture `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json` (§9.4).
- `RunSetupService(..., registered_bases=RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, "demo", clock))))` (`B/runs/registered_basis.py:49-107`). The `FakeSites` legacy store holds no Kisiwa.
- Precedent, default suite, no DB: `backend/tests/test_s2_registered_basis.py:83-93` and `backend/tests/test_s1_bindings.py:39-44` (Kobo imported and converted over `InMemoryFoundationStore`, `backend/tests/foundation_fakes.py`).

**Why not (a):** Lab v3 has no device resolutions and no registered basis, so a pass would prove a path the demo never uses (D0's limit, repeated). The demo prepare runs Kisiwa through `registered-kobo-publication` v5 and the gateway, exactly as Kobo (`T/demo_combined_kobo.py:401-410`).
**Why not (b):** a hand-built `RegisteredSiteSelection` skips `select_registered_basis`, `_signal_mappings` (`registered_basis.py:110-146`: every bound asset must be a Foundation component) and the resolution-unit check (`B/runs/service.py:919-937`). Those are the three places Kisiwa's template can fail on the registered path.
**What (c) proves beyond F0's questions:** that Kisiwa's template imports, that a Kobo-shaped binding set converts onto it, that the registered selection accepts it, and that `registered-kobo-publication` v5 is not tied to `KOBO-001` by name. That answers D1 pre-flight (a) (§3.1) before K1 starts.
**Cost:** about +0.15 inside F0r.

### 9.2 Decision 2: the tank-level signal — `mini-grid` v7, a new unit K1a (0.5), used by Kisiwa only

**Finding confirmed by Architect reading.** `S/kernel/model.py:396-400` reports a numeric STATE_SIGNAL only with a STATE_SAMPLE handler; `S/packs/mini_grid.py:192-207` has only the STOCK handler for `fuel-tank-volume`, and v2–v6 are `replace`s that keep that handler table (`:1019`, `:1244`). `host/execution_adapter.py:734-739` then drops `fuel-level-sensor/fuel-level` silently. The fuel pack's sampler (`S/packs/fuel.py:207-221`, `SAMPLE_HANDLER`) is model-agnostic. The `fuel-tank` component relation already names the state (`mini_grid.py:230-232`), so the kernel's one-relation rule (`model.py:360-380`) is satisfied.

**K1a: `mini-grid` v7 (simulator and product profile).** One new version; v1–v6 objects are not edited.
- Simulator (`S/packs/mini_grid.py`, after `:1256`): `MINI_GRID_V7_MODEL = replace(MINI_GRID_V6_MODEL, model_profile_version=7, statement=V6.statement + V7_SENTENCE, handlers=<V6 handlers with the stock handler restated> + (fuel.SAMPLE_HANDLER,))`.
  - `fuel.SAMPLE_HANDLER` is imported and reused, never copied.
  - The STOCK handler is restated for v7 only (same `handler_id`, role, kind, floor, `consume`, `initialize`), with statement: "The fuel in the tank, initialized by the scenario, moved by accepted generator energy and by any frozen declared cause, such as a recorded operational action." The v1–v6 handler keeps "moved only by accepted generator energy". Reason: K0 makes the old sentence false for a run with actions.
  - `V7_SENTENCE`: " Version seven also samples the fuel in the tank at an instant, after that instant's events, so a tank level sensor can report it."
- Product profile (`B/runs/profiles.py`, after `:1367`): `MINI_GRID_V7_MODEL = replace(MINI_GRID_V6_MODEL, model_profile_version=7, statement=…same sentence…, supported_states=<v6's, with fuel-tank-volume supported_roles {"CAUSAL_INPUT", "REPORTED_OBSERVATION"} and the restated statement>)`. Appended to `MODEL_PROFILES` (`:2164-2175`), after v6.
- Executable: appended to `host/execution_adapter.py:128-137` `EXECUTABLE_MODELS` and to the profile tuple in `host/tests/kobo.py:129-138` (the `next(...)` there picks the first match, so `None` still resolves to v1; no Kobo call changes).
- **Publication:** no new publication profile and no mapping or binding change. `registered-kobo-publication` v5 already declares `fuel-level-sensor/fuel-level` at 15 min, bias −0.5 L, dropout 40/1000, and the `fuel-level-reporting-availability` forcing state (`B/runs/profiles.py:1426-1470`, `:1985-2000`). Kisiwa's template already carries the device and the `fuel-tank-level` mapping (D0 draft `:292-297`, `:358-360`). §8.4's "K1 +0.25–0.5 if F6 needs a new publication profile version" is **withdrawn**: F6 found the drop at execution, not publication.

**Effects (the stops guard each):**
- **Digests.** v1–v6 trajectories, run identities and digests are byte-equal; v7 is a new identity, so no frozen run changes. A v7 run's trajectory carries the sampled tank value, so it differs from a v6 run of the same document by design. Stop: any v1–v6 digest change.
- **Kobo stays on v6 and publishes no tank level.** Kobo's replay pins the model through its manifest (`host/tests/test_s6_verification_replay.py:141-146`); `T/demo_combined_kobo.py` is not edited. So Kobo still stores **0** `fuel_level` rows, Kobo's Fuel page and `mini_depth.rules.assess_fuel_hour` are byte-equal, A2/A3/MB-1 checks and the all-26 audit are unaffected, and K3 gives Kobo `NOT_ASSESSED` as §8.4 says. Moving Kobo to v7 is **not** demo-critical (it would add tank rows to Kobo's Fuel page and change Kobo's evidence, checks and captures); it goes to the after-the-demo list as "Kobo tank level (mini-grid v7 on Kobo)".
- **Kisiwa starts publishing `fuel_level`** at 15 min from K1 onward, through the gateway and the activated binding snapshot, as any registered signal. Its consumers already exist (`mini_depth/inputs.py:141`, `:254`; `evidence/overview.py:80`); K3 is the first that judges it.
- **Profile listings.** The Lab's model-profile catalogue gains one row. Tests that enumerate `MODEL_PROFILES` or `EXECUTABLE_MODELS` (`backend/tests/test_component_properties.py`, `backend/tests/test_addressed_bindings.py`, `host/tests/test_kernel_conformance.py`, `host/tests/test_mini_grid.py`) take the new entry. That is a listing change, not a digest change.
- **Guards and checks:** no served copy changes; guards A, W, N, V, M and frontend-hardwiring are unaffected; chain coherence is unaffected.

**K1a card (0.5; range 0.4–0.75):** files above; tests:
- L0 `host/tests/test_mini_grid_v7.py`: `MINI_GRID_V7_MODEL.reports("fuel-tank-volume", "STATE_SIGNAL", "L")` is true and v6's is false; v7's advertised supported states equal the product profile's (the existing parity pattern); a short Kobo-template run on v7 with `registered-kobo-publication`'s fuel-level signal gives 15-min tank observations equal to the stock at each instant minus 0.5 L before noise; the same document on v6 gives an identical generator, battery and tank trajectory except the sample (physics unchanged).
- Byte-equal pins: one v6 Kobo run digest and one v5 run digest, re-asserted unchanged.
- **Stops:** any v1–v6 digest or trajectory byte change; any Kobo, Cold or EV byte change; a need to change a publication profile, mapping or binding; more than 0.75.
- **Order:** starts **now, in parallel with F0r** (its content does not depend on F0r's result; F0r uses a probe-local copy, §9.4). If F0r stops on S4 again (the sampled tank does not publish), K1a pauses at its next commit and the Architect rules.

### 9.3 Decision 3: K0's extended scope (2.0 → 2.5; range 2.0–3.25)

F0's code facts (§F0a in the evidence file) change K0 as follows: the host and kernel need **no** change to accept added causes and conditions (no provenance check refuses them: `S/kernel/execute.py:244-259`, `:721-730`, `:857-872`; `B/runs/models.py:976-1045`; `host/execution_adapter.py:769-820`), which frees about 0.4. But K0 must add the origin field on both frozen record kinds, provenance labels, persistence round-trip and composition wiring, which costs about 0.9.

**K0 consolidated scope:**
1. **Origin on causes and conditions.** Two fields on `DeclaredCause` (`contracts/assetops_contracts/world_inputs.py:170-204`), `FrozenCause` (`B/runs/models.py:572-619`), `FrozenReportingPathCondition` and its contract counterpart (PRE-FLIGHT names the class):
   - `origin: Literal["SCENARIO", "OPERATIONAL_ACTION"] = "SCENARIO"`;
   - `action_ref: str | None = None`, format `"{action_id}:{content_sha256}"` (content hash = sha256 of the action's canonical JSON, sorted keys, compact separators, ASCII, as F0's `load_actions`).
   - **Byte-equal rule:** every render, canonical form and hash (`B/runs/parsing.py`, the trajectory identity `contracts/assetops_contracts/trajectory.py:570-589`, `:639-662`, every run store) **omits both keys when `origin == "SCENARIO"` and `action_ref is None`.** So every existing run, scenario cause and digest is byte-equal. Stop: any digest change for a run with no actions.
   - Parse refusals, kind `CAUSE_ORIGIN_INVALID`: `OPERATIONAL_ACTION` without `action_ref`; `action_ref` with `SCENARIO`; an unknown origin.
2. **Run setup reads the log by a named version, never "latest".** New optional run-setup request key `operational_actions: {"log_id": "kisiwa-001", "log_version": 1}` (absent = no actions; the request and identity are then byte-equal). A new read-only port `OperationalActionLogPort` with a file adapter over `C/operational-actions/{log_id}-v{log_version}.yaml`. The identity freezes `operational_action_log = {log_id, log_version, sha256}` only when present (omitted otherwise).
   - Selection: actions with `at` in `[start_time, end_time)`.
   - Effects (unchanged from §8.2a): `FUEL_DELIVERY` → INCREASE POINT; `FUEL_REMOVAL_UNRECORDED` → DECREASE WINDOW plus, with `sensor_disconnected`, a `fuel-level-reporting-availability@fuel-tank` WINDOW condition; `TANK_DIP`, `TANK_SEALED`, `SENSOR_POWER_PROTECTED` → no physical effect.
   - `event_id` = `"{action_id}/{effect}"`, effect ∈ `tank-increase`, `tank-decrease`, `sensor-disconnected`. A clash with a scenario event id refuses (`OPERATIONAL_ACTION_EVENT_ID_CONFLICT`).
   - `intervention_history` += `"OPERATIONAL_ACTION:{action_id}:{content_sha256}"`, ordered by `at`, then `action_id` (F0's form).
   - Setup refusals (typed, nothing written): `OPERATIONAL_ACTION_COMPONENT_UNKNOWN`; `OPERATIONAL_ACTION_STATE_NOT_CAUSAL` (the model has no CAUSAL_INPUT STOCK for the state); `OPERATIONAL_ACTION_UNIT` (not L); `OPERATIONAL_ACTION_OVER_CAPACITY` when initial stock + Σ deliveries in the run up to and including this one > the frozen `fuel-tank-capacity` (an exact sufficient bound, since nothing else raises the stock; **refused, never clamped**); `OPERATIONAL_ACTION_OVER_STOCK` when a removal exceeds initial stock + earlier deliveries in the run. **Correction to §8.2a:** "a delivery fits free capacity at `at`" cannot be known at setup (the stock at `at` depends on dispatch); the bound above replaces it. The kernel floor (`insufficient-fuel`) remains the run-time backstop and is reported by the existing bound-case path, never silently.
   - `TANK_DIP` and the two `SITE_VISIT` actions are validated (component exists, `at` in interval) but freeze nothing.
3. **Provenance labels.** `B/runs/provenance.py:434-459` and `:513-536`: a cause or condition with `origin == "OPERATIONAL_ACTION"` renders `answered_by="OPERATIONAL_ACTION"`, `answered_by_detail="Operational action {action_id} ({kind}, by {actor}), log {log_id} v{log_version}"`. Scenario rows keep `"SCENARIO"` byte-equal. `answered_by` is a free string (`world_inputs.py:111`, `:266`; `F/shell/runSetupClient.ts:113`), so the Lab view shows it with no frontend edit; this is Lab-only, never client-facing.
4. **How operator records reach the product: only through the Work API (K2), never through the run.**
   - `OPERATOR_RECORD` (M2) gets **no** reader; registered v3+ keeps `record_channels=()` (`B/runs/profiles.py:1946`); `SourceEnvelope` stays MEASUREMENT-only for the registered path (`host/lab_execution.py:2829-2835`); `OPERATOR_COMMANDABLE_STATES` (`B/scenarios/models.py:255-258`) is unchanged.
   - The same log is the one source: K7's injector reads it and posts `FUEL_DELIVERY` (ticket 30 min after `at`), `TANK_DIP` (value from the handover file, §8.3) and the `SITE_VISIT` record through K2's `post_operational_record`. `FUEL_REMOVAL_UNRECORDED` posts nothing.
   - The product never reads `C/operational-actions/`: a K0 test asserts that no module under `B/` other than the run-setup adapter, and nothing under `F/`, names that path.
5. **Composition.** Wire the port in `B/main.py:690` (the Lab composition) and in the registered test harnesses that K7 uses (`host/tests/test_s6_verification_replay.py` `LabRunner` pattern; PRE-FLIGHT names the exact constructor). Default `None` → no actions.
6. **Host and kernel:** no change expected (F0r proves it in memory, §9.4 F0a). If F0r shows otherwise, K0's +0.5 reserve inside the range covers it, and the Architect rules.

**Files:** `contracts/assetops_contracts/world_inputs.py`, `contracts/assetops_contracts/trajectory.py` (only if the omit rule needs it), `B/runs/models.py`, `B/runs/parsing.py`, `B/runs/service.py`, `B/runs/ports.py`, new `B/runs/operational_actions.py` (loader, validation, freeze), new adapter under `B/runs/adapters/`, `B/runs/provenance.py`, every run store's render/parse (PRE-FLIGHT names them), `B/main.py`, new `C/operational-actions/kisiwa-001-v1.yaml` (F0r's draft, promoted verbatim after F0r merges), tests.
**Tests:** L0 round-trip of both origins on every store; byte-equal digests for one Kobo, one Cold and one EV fixture run and for every shipped scenario's frozen causes; each refusal; the Kisiwa run-2 delivery and run-4 removal frozen with origin, ref and history; the provenance rows; the no-reader test. L1/L2 setup through the registered path on own `assetops_k0_test`.
**Size, 2.5:** contract and models origin with the omit rule 0.5; request key, port, adapter, loader, validation and freeze 0.75; provenance 0.15; persistence round-trip 0.25; composition 0.2; tests 0.4; host/kernel reserve 0.25. **Stops:** any digest or byte change for a run with no actions; a need to change M2, M3, `record_channels` or the envelope schema; more than 3.25.

### 9.4 Re-issued F0 (F0r), full card, ready for a builder now, 0.5

**Branch and worktree:** continue `task/DIESEL-F0-kisiwa-fuel-probe` in `C:\Users\assef\Bineyame\AssetOpsV1-f0`. First merge main (for this §9). The pre-registration commit `54ef019e1` stands unchanged.

**Unchanged from §8.3, verbatim:** purpose questions 0–5; the declared world table (10 day-runs, 700 L start, the four action kinds and their times, dips, change instant); the `fuel-balance-1` parameters; the Architect's pre-registered expectation; the action log `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml` (not edited). D0's files stay byte-equal.

**What changes (and only this):**
1. **Registered setup through (c), §9.1.** New draft fixture `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json`: `backend/conversions/kobo-001-bindings.json` with the Site code `KISIWA-001` and every binding kept whose `legacy_mapping_id` is a mapping in Kisiwa's template. Report every Kobo binding dropped and why. A Kisiwa mapping with no binding in the fixture is a **stop** (conversion refuses unconverted mappings, `test_s1_bindings.py:148-154`); never invent a binding. K1 promotes this file verbatim to `V/kisiwa-001-bindings.json`.
   - Clocks: import at `2026-09-29T09:00:00Z`, conversion at `2026-09-29T09:30:00Z` (before run 1 at `2026-10-01T12:00:00Z`); `knowledge_at` absent; the request's `foundation_version` = the registered version the selection returns (as Kobo, likely 2). Record all three in the result JSON.
2. **Probe-local `mini-grid` v7, stated plainly.** The real v7 belongs to K1a (§9.2). F0r builds, **inside `T/probe_kisiwa_fuel.py` only**, `PROBE_V7_SIM` and `PROBE_V7_PROFILE` with exactly K1a's content (§9.2: version 7, `fuel.SAMPLE_HANDLER` reused, restated stock statement, product supported roles `{CAUSAL_INPUT, REPORTED_OBSERVATION}`). It passes `PROBE_V7_PROFILE` in `model_profiles=` and executes with `run_to_end(run, PROBE_V7_SIM)` and `reporting_inputs(run, profile, PROBE_V7_SIM)` instead of `model_for(run)` (which only knows `EXECUTABLE_MODELS`). The result JSON and the evidence file carry the line: **"Tank level from a probe-local mini-grid v7 identical in content to K1a's; product code has no v7 until K1a merges."** No product file is edited.
   - The reference chain (F3) uses the same probe-local v7 without actions, so dispatch equality compares like with like. F3 additionally asserts that a v6 chain without actions has equal generator state, accepted generator energy, battery level and tank stock at every boundary (v7 adds a sample, not physics).
3. **F0a carrier.** Origin and content hash ride in the `event_id` prefix `OPERATIONAL_ACTION/` and in `intervention_history`, as F0 built (no product origin field until K0). F0a passes on that carrier.
4. **F6 becomes a gate on the registered report path, in memory:** pass the F5 observations through `host/gateway_publication.py:79` `keyed_reports(run_id, basis.snapshot_sha256, observations, 5)` with the run's frozen basis. Gate: fuel-level report texts exist, one per F5 observation, and the activated binding snapshot (`basis.snapshot_canonical`) holds a `fuel_level` binding for `fuel-level-sensor/fuel-level`. **No gateway process and no SQLite ledger** (no DB of any kind). Kobo's 0-row cause is now settled (§9.2) and is not re-investigated.

**Gates (each asserted; a failing gate stops the run):**
- **F0a** scenario of every run is weather and loads only (F0's `scenario_is_weather_and_loads_only` empty); the actions enter only through `apply_actions` on the frozen run; the kernel applies them or refuses (report verbatim).
- **F1** every run READY on the registered path through (c), and `run_to_end` completes.
- **F2** tank law per step, exactly: `tank[i+1] = tank[i] − E_i × SFC − removal_i + delivery_i`; Σ removal = 120 and Σ delivery = 300 exactly; report the removal's per-step litres.
- **F3** dispatch unaffected, as above (with actions vs without, both probe v7; and probe v7 vs v6 without actions). Every night's litres equal D0's 43.428 L (26057/600).
- **F4** no fuel-limited step.
- **F5** fuel-level observations at 15-min cadence on `registered-kobo-publication` v5; none with an instant in `[00:50, 02:20)` local of night 4; at least one in the 30 min before and the 30 min after; bias −0.5 L.
- **F6** as item 4.
- **F7** each per-day document below 4000 nodes; record the largest.
- **F8** `--check` byte-equal.
- **F9** both sources (true stock; F5 readings): night 4 `UNEXPLAINED` with gap > 0; every other night `WITHIN_MARGIN` with gap 0; none `NOT_ASSESSED`.
- **F10** D0 untouched (`T/probe_kisiwa_nights.py --check` prints "probe result current").
- **F11 (new) K0's setup bounds hold for the declared world:** for runs 2 and 4, initial stock + deliveries ≤ 1000 L and removal ≤ initial stock + earlier deliveries (§9.3 item 2). Report the numbers.

**Stops (report to the Architect; never design around them):**
- **S0 (OA-1)** the only way to move the tank or open the gap is a scenario entry. Never write one.
- **S1** a refusal on the registered path through (c): import, conversion, selection (`REGISTERED_BASIS_*`), `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE`, `PUBLICATION_UNIT_MISMATCH`, a blocking reason, or a kernel refusal of an added cause. Report verbatim with file:line and the smallest fix. **Never fall back to Lab v3 or to a hand-built selection.**
- **S2** F2 or F3 fails.
- **S3** F9 differs from the expectation (report the night and its terms). Never change the removal size, times, materiality, accuracy, tolerances, cadence, dropout or seed.
- **S4** F5 fails with the probe-local v7 (the sample does not publish, or the gap does not silence). K1a pauses (§9.2).
- **S5** F7 over 4000 on a single day.
- **S6** a Kisiwa mapping has no Kobo binding to carry (item 1).
- **S7** F11 fails. Report; the Architect rules (the declared world is not changed).
- **S8** the re-issued work exceeds 0.75 unit.

**Files:** `T/probe_kisiwa_fuel.py` (edit: (c) setup, probe-local v7, F3/F6/F11 additions); new `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json`; `.agent/DIESEL-F0/probe-result.json` (new); `.agent/DIESEL-F0-probe-results.md`: keep the S1 stop section as "First attempt (stopped, aa49a18fd)" and add the re-run with the plain-words line of §8.3, the per-night table, gates, seconds per run and the probe-local-v7 line; `host/tests/test_probe_kisiwa_fuel_band.py` (L0, as §8.3, if not yet written).
- **Before running:** commit a short pre-registration addendum to the evidence file (the (c) path, the clocks, the bindings draft, the probe-local v7). No expectation changes.
- **Reading budget:** this §9; §8.3; `B/runs/registered_basis.py:49-170`; `B/runs/service.py:395-500`, `:740-790`, `:888-938`; `backend/tests/test_s2_registered_basis.py:1-100`; `backend/tests/test_s1_bindings.py:1-60`, `:140-160`; `backend/tests/test_s1_cutover.py:40-75`; `B/sites/foundation_service.py:100-130`, `:247-300`; `backend/conversions/kobo-001-bindings.json`; `S/packs/mini_grid.py:185-235`, `:1240-1257`; `S/packs/fuel.py:150-221`; `B/runs/profiles.py:1140-1165`, `:1354-1367`; `host/gateway_publication.py:60-105`.
- **Rules:** no DB (Postgres or SQLite), no prepare, no suite, no tick, no `-ExecutionPolicy`; never `assetops_demo3_full_test`. One fresh Opus reviewer re-runs both `--check`s, reads (c) against `test_s2_registered_basis.py`, and diffs the probe-local v7 against §9.2. **Merge on ACCEPT whatever the result.**

### 9.5 Revised sizes, order, lanes, totals and date

**Arithmetic correction to R2.** §8.4's unit rows sum to **15.25 remaining** (the rows are F0 0.5, K0 2.0, K1 1.25, K2 0.75, K3 1.5, K4 2.0, K5 1.0, K6 1.5, K7 2.25, K8 1.0, K9 1.0, contingency 0.5), not the 14.75 printed; the Kisiwa total with D0 was **15.75**, not 15.25. R2's "19.25 before DS-1" was therefore 19.75 on its own rows. The figures below use the rows.

| Unit | Size | Change | Depends on (merged) |
|---|---|---|---|
| D0 | 0.5 | spent | — |
| F0 (first attempt) | 0.5 | spent (stopped S1) | — |
| **F0r** | 0.5 | new (§9.4) | none (now) |
| K0 | **2.5** (2.0–3.25) | +0.5 (§9.3) | F0r; owner answered (Option A) |
| **K1a** mini-grid v7 | **0.5** (0.4–0.75) | new (§9.2) | none (now, parallel with F0r) |
| K1 | 1.25 | the "+0.25–0.5 publication profile" risk withdrawn; now uses v7 and promotes F0r's bindings draft | F0r, K1a, A1 |
| K2 | 0.75 | — | F0r |
| K3 | 1.5 | — | K1, K2 |
| K4 | 2.0 | — | K3; board/chain part after PV-1 |
| K5 | 1.0 | — | K3; panel after K4 |
| K6 | 1.5 | — | K4, MV-1, A2 |
| K7 | 2.25 | sets `operational_actions` on each Kisiwa run request (K0) and `model_profile` v7 (K1a) | K0, K1, K2; K6 for the freeze step |
| K8 | 1.0 | — | PV-1, A3, CH-5d1 (merged), K4; captures after K7 |
| K9 | 1.0 | — | all |
| Contingency | 0.5 | card round after F0r; K4 Finding-kind risk | |
| **Kisiwa remaining** | **16.25** (range 14.5–19.0) | +1.0 vs R2's corrected 15.25 after F0 spent (F0r +0.5, K0 +0.5, K1a +0.5, F0 −0.5 now spent) | |
| **Kisiwa total incl. spent** | **17.25** | | |

**Order (lane-units; about 3 units per lane-day including review):**
```
now (t=0):   MB-1 (lane 1) | A2 (lane 2) | F0r (lane 3) | K1a (lane 4, light, in parallel)
t≈0.5:       F0r result -> card round (contingency) | K1a merged
t≈0.55:      A2 merged -> K2 (lane 2, to ≈1.3)
t≈0.6:       K1 (lane 3, after F0r PASS and K1a; to ≈1.85)
t≈1.25:      MB-1 merged -> WD-1 -> PV-1 (lane 1, to ≈2.15)
t≈1.3:       K2 merged (0054) -> A3 (lane 2, after MB-1; to ≈2.0)
t≈1.85:      K1 merged -> K3 (lane 3, 0055; to ≈3.35)
t≈2.0:       A3 merged -> K0 (lane 2; to ≈4.5)
t≈2.15:      PV-1 merged -> lane 1 idle until K3 (the coordinator may pull backlog-free fix rounds here)
t≈3.35:      K3 merged -> K4 (lane 3, 0056; to ≈5.35) | K5 fuel page (lane 1; to ≈4.35)
t≈4.5:       K0 merged -> K7 data part (lane 2; to ≈6.25)
t≈5.35:      K4 merged -> K6 (lane 3, 0057; to ≈6.85) | K8 code (lane 1) | K5 Finding panel
t≈6.85:      K6 merged -> K7 freeze step and Kisiwa scratch prepare (≈7.35)
t≈7.35–7.6:  K8 captures -> merged
t≈7.6–8.6:   K9 (finish rows, guard, rehearsal prepare)
then:        DS-1 -> E1–E6
```
- If no fourth builder is available, K1a runs on lane 3 right after F0r (K1 then starts at ≈1.0 and the path grows by 0.4).
- **Critical path:** F0r 0.5 → K1 1.25 (K1a parallel) → K3 1.5 → K4 2.0 → K6 1.5 → K7 freeze 0.5 → K8 captures 0.25 → K9 1.0 ≈ **8.5–8.6 lane-units ≈ 2.9 working days** (≈ 9.0 if K1a is serial). K0 stays off the critical path with about 2.3 units of float (needed by t≈6.85).
- **Remaining before DS-1:** lanes 1–2 **3.75** (CH-5d1 merged; MB-1 1.25 + WD-1 0.15 + PV-1 0.75 + A2 0.55 + A3 0.7 + E3 allowance 0.35; the coordinator confirms A2's and MB-1's remainders) + Kisiwa **16.25** = **20.0** (R2 printed 19.25; on its own rows 19.75; less CH-5d1's 0.75 and F0's spent 0.5 that is 18.5; R3 adds +1.5).
- **Plan total:** ≈ 117.3 (FUEL-1) + 17.25 = **≈ 134.55** (R2 printed ≈ 132.55).
- **Demo date:** the critical path is about the same as R2's (8.5) when K1a runs in parallel, but it now starts half a unit later because F0's first attempt stopped. Net: **about +3.25 working days (range 2.75–5.25)** against the lanes-1–2 plan without Kisiwa, versus R2's +3 (2.5–5). The central figure is inside the owner's accepted "about +3 (range 2.5–5)" and inside the earlier "about 4–5". **The top of the range is now about a quarter-day over 5.** Tripwire: if, at any card round, the Kisiwa critical path re-plans above **9.75 lane-units** (the point where the central date passes +3.75 and the top passes about +5.5), the Architect stops the lane's next dispatch and the coordinator takes the cut options to the owner (first candidate: drop K6, the verification page, and end the DS-1 beat at the Action; about −1.75 units and −0.6 day).
- **E3:** unchanged (+25–35 min; E3 ≈ 1.3–1.5 h of the 3 h cap).

### 9.6 Plan HTML (`Docs/demo-sprint/client-demo-plan.html`) rows to change (the coordinator carries these on top of §8.9)

1. Build-units row "DIESEL-1-R2 …": becomes "DIESEL-1-R3 …", **17.25** (D0 0.5 and F0 0.5 spent, F0r 0.5, K0 2.5, K1a 0.5, K1 1.25, K2 0.75, K3 1.5, K4 2.0, K5 1.0, K6 1.5, K7 2.25, K8 1.0, K9 1.0, contingency 0.5). Note: "F0 stopped at run setup (no registered Site in memory) and found mini-grid never samples the tank; re-run on the real registered path with a new mini-grid v7 (Kisiwa only)".
2. Total row ≈ 134.55; G5/G6 +17.25 (DIESEL-1-R3) instead of R2's +15.25.
3. Lanes figure: K1a beside F0r; lane 3 F0r → K1 → K3 → K4 → K6 → K9; lane 2 A2 → K2 → A3 → K0 → K7; lane 1 MB-1 → WD-1 → PV-1 → K5 → K8.
4. Calendar line and OD-P9: G6 about +3.25 working days (range 2.75–5.25) against the plan without Kisiwa.
5. Rulings table: a "DIESEL-1-R3" row pointing to §9: (c) in-memory registered setup, mini-grid v7 for Kisiwa only (Kobo stays v6, 0 tank rows), K0 origin fields with the omit-when-scenario rule, records only through the Work API, R2 arithmetic corrected.
6. After-the-demo list: add "Kobo tank level (mini-grid v7 on Kobo)".

### 9.7 Owner questions

**None blocking.** The owner already chose the operational-action link (Option A); nothing here reopens it.

For the owner's information, in plain words:
- The first fuel trial stopped before measuring anything, for two technical reasons: the example site wasn't set up the way the real product sets up a site, and the simulated generator site never reported its tank level at all (that is also why Kobo shows no tank readings). We fix both: the trial re-runs on the real set-up path, and the simulated site gains the ability to report its tank level. Kobo keeps working exactly as it does today; only Kisiwa uses the new tank reading.
- Kisiwa now adds about **3¼ working days** before the demo, against about 3 before (range now 2¾ to 5¼, against 2½ to 5). The middle estimate is still inside what you accepted; the worst case is now about a quarter-day past your 5-day upper end. If the plan grows further, we will come back to you with a cut (most likely: skip the "after the fix" check page and end the Kisiwa story at the agreed action) before going over.

---

## 9a. Ruling DIESEL-1-R3a: F0r's S6 stop at conversion

- Architect: Claude, 2026-11-07. Binding unchanged (`.ai/ROLE_CONFIG.md:9`). F0r branch commits be4bbceb6, 3a147f96e, bf70fd180, 1ba54aa43 (`AssetOpsV1-f0`). This amends §9.4 item 1 only.
- Refusal, verbatim (`B/sites/binding_conversion.py:127-129`): "ConversionConflict: Legacy mappings ['battery-pcs-discharge-capability', 'generator-status', 'pv-inverter-available-power'] have no explicit conversion in the fixture." The stop was correct.
- **Cause:** Kisiwa's template has 12 legacy mappings (D0 draft `:326-372`). Kobo's conversion fixture (`V/kobo-001-bindings.json`, `minigrid-roles-1`) predates three of them. Kobo's import has no such mappings, so it bound `generator-controller/status` with `legacy_mapping_id: null` and gained the two capability channels later by republication (`V/kobo-001-s3-dispatch-demo-config.json` `bindings.add`, roles-2). Copying Kobo's history onto a Site whose template already has these mappings does not fit.

**Decision: fix (i), and it is the real K1 path too.** Kisiwa's conversion fixture converts **every** legacy mapping in its template, once, at import:
1. `role_set` = **`minigrid-roles-2`**: the set `B/sites/binding_roles.py:36` names as the default for a new MINIGRID publication, and the lowest one holding `pv_available_power` and `pcs_discharge_capability`.
2. `bindings` = 12 rows: the 9 F0r kept, plus:
   - `generator-status`: Kobo's status row (`V/kobo-001-bindings.json`, role `generator_state`, `state`→`state`, ENUM map STOPPED/STARTING/RUNNING/FAILED) **with `legacy_mapping_id: "generator-status"`**, not null (the template has the mapping; `plan_requests` checks the row matches it, `:95-101`);
   - `pv-inverter-available-power` and `battery-pcs-discharge-capability`: Kobo's two `add` rows from `V/kobo-001-s3-dispatch-demo-config.json` (roles `pv_available_power`, `pcs_discharge_capability`, kW→kW IDENTITY), each with its `legacy_mapping_id`.
3. `declare_signals` = **`[]`**. **The builder's judgement call is overruled.** Keeping Kobo's entry is harmless to the code (`B/sites/binding_service.py:507-522` returns no change for an already-declared signal with the same unit), but its `reason` ("Absent from the original Kobo import…") is false for Kisiwa, whose template declares the signal (`:289`). A fixture must state only true provenance. Set `note` to: "Converted from the imported Kisiwa Foundation's legacy signal_mappings; every template mapping converted once, under minigrid-roles-2 (DIESEL-1-R3a)."
- **Why not (ii):** republishing after conversion can't help, because conversion refuses first. Republication is only for channels the template does not have.
- **Why not (iii):** it changes D0's template, which §8.1 item 2 forbids.
- **Roles-3/4 stay a republication, as Kobo does.** The channels Kisiwa's template does not map (critical-load requested and delivered power, storage charge request, and the other roles-4 depth channels) stay for K1's `V/kisiwa-001-minigrid-roles-demo-config.json` through `B/sites/demo_configuration.py`, as §3.1 already says. F0r does **not** apply it, because none of its gates reads those channels. An unbound signal is not a reporting path (`B/runs/service.py:899-902`), so v5's resolutions for them are skipped. K1's registered-parity test proves the roles-4 step.
- **Kobo:** its fixtures and configs are not edited.

**F0r's other gates and stops stand unchanged** (§9.4: F0a–F11, S0–S8), with two additions:
- if the corrected fixture is refused again (a role, unit or conversion check), that is **S6**: report it verbatim, and never drop a mapping or edit the template;
- the evidence file records the 12-row fixture and the roles-2 choice in the pre-registration addendum before any run.
- The S8 cap (0.75 of re-issued work) stands; this fix is about 0.05.

**K1's size is unchanged at 1.25.** K1 promotes the corrected draft verbatim to `V/kisiwa-001-bindings.json`. It writes one roles-4 demo configuration for Kisiwa instead of replaying Kobo's three-step history (s3, s6, roles-4). That is no more work than §3.1 assumed. Totals and the date in §9.5 are unchanged.

---

## 9b. Ruling DIESEL-1-R3b: F0r result, F8, merge, next K units, setup clock

- Architect: Claude, 2026-11-07. Binding unchanged. F0r commits 0011ad361, 77ad11f17, 77958a20c, ab33768d7, 9e5fad4e1 on `task/DIESEL-F0-kisiwa-fuel-probe`. The result matches the pre-registration:
  - night 4 is UNEXPLAINED from both sources, [95.657, 144.343] L, with a 105-min gap (the builder's pre-run 105-min expectation, not the 90-min span);
  - every other night is WITHIN_MARGIN (±24.343 L; the delivery night ±27.343 L);
  - F0a, F1–F7, F9, F10 and F11 pass.
- Foundation selection v1 is correct: with R3a's `declare_signals: []` the conversion makes no joint Foundation revision.

**1. F8: seed the ids; F0 then closes PASS.**
- **The fix:** inside `T/probe_kisiwa_fuel.py` only, wrap the in-memory import and conversion in a context manager that replaces `uuid4` with a seeded generator: `random.Random(20260929)`, `uuid.UUID(int=rng.getrandbits(128), version=4)`.
  - Patch it at every name the store, the services and the conversion actually call (`uuid.uuid4` and any module-level `from uuid import uuid4` binding; the builder lists them in the evidence file).
  - Restore it on exit.
  - No product or `backend/tests/` file is edited.
- **Rejected: marking or omitting the ids as volatile.** The snapshot hash and the report key are part of what F6 proves, and a check that skips them cannot see a real regression in them.
- **Fallback:** if any id still varies after seeding, the builder stops and reports which one. Volatile marking is not a quiet alternative.
- **Who can apply it:** this is a Sonnet fix round.
- **Mechanical verification, by the coordinator, no reviewer judgement needed:**
  - (a) `--write`, then `--check` in a **fresh process**, prints "probe result current";
  - (b) a second fresh `--check` does the same;
  - (c) `git diff` of `probe-result.json` against 9e5fad4e1 changes only the id fields and the values derived from them (snapshot sha, report key and the ids listed). Every litre, band, state, gap, count and gate value is byte-equal;
  - (d) `T/probe_kisiwa_nights.py --check` still prints "probe result current".
- **Then F0 closes PASS**, with all gates F0a–F11 met.

**2. Merge: yes, as evidence-only, like D0.**
- The merge carries `T/probe_kisiwa_fuel.py`, `host/tests/test_probe_kisiwa_fuel_band.py`, `.agent/DIESEL-F0/` (the action-log draft, the bindings draft, the result JSON) and `.agent/DIESEL-F0-probe-results.md`. No product code.
- One fresh Opus reviewer runs §9.4's review: re-run both `--check`s, read (c) against `test_s2_registered_basis.py`, and diff the probe-local v7 against §9.2.
- The review starts once (1) verifies, and its finding goes in the same packet. Merge on ACCEPT.
- K0 promotes the action log later, and K1 promotes the bindings draft. Neither is moved now.

**3. K units: order and readiness**

| Order | Unit | Lane, start | Readiness |
|---|---|---|---|
| 1 | K1a | in build now | its card is §9.2 |
| 2 | **K1** Kisiwa Site (critical path) | lane 3, after F0 merges and K1a merges | **needs one consolidated card.** It is spread over §3.1, §8.4, §9.2 and §9a, and ROLE_CONFIG Token Efficiency item 5 requires one card. **The Architect writes it next (R3c)**, before K1a merges. |
| 3 | **K2** fuel records on the Work path (0054) | lane 2, after A2 merges | **needs a card**: the API body and refusal literals, the `fuel_records` read signature, migration 0054's exact CHECK and column, and the tests. §8.4 pins the decisions but not the literals. The Architect writes it in the same R3c round, after K1. |
| 4 | **K0** operational-action bridge | lane 2 after A3, or any lane that idles first (it has about 2.3 units of float) | **build-ready from §9.3 as its card**, with one pre-flight: the builder names the PRE-FLIGHT items (the contract reporting-condition class, every run store's render/parse, the harness constructor) and batches any questions before writing code. The Architect answers them within that pre-flight. No further card is needed. |

- Everything after these (K3 onward) keeps §9.5's order, and each gets its card at the round before it starts.

**4. The setup clock is confirmed: `2026-09-29T10:00:00Z`.**
- It falls after the 09:30 conversion, so the binding basis is recorded at setup, and before run 1 at `2026-10-01T12:00:00Z`.
- It is a probe-only constant and is recorded in the result JSON.
- R3 should have named it; this ruling fixes that omission.
- K1 and K7 use their own install and setup instants from the story calendar, never this one.

---

## 9c. Ruling DIESEL-1-R3c: the K1 and K2 consolidated cards

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `840d5dade`, then `992847b72`, where F0 merged and its review sits at `.agent/review-F0.md`. F0r evidence read on `task/DIESEL-F0-kisiwa-fuel-probe` at `c77eb135f`. K1a read on `task/DIESEL-K1a-minigrid-v7` at `1a4d3b5c5`. A2 read on `task/FUEL-A2-trial-fuel-comparison` at `7a390ea66`.
- Owner decisions in force, verbatim:
  - `.agent/owner-kisiwa-scope-2026-11-07.md`: "Build it, with the action link (Recommended)".
  - `.agent/owner-scenario-data-2026-11-07.md`: "this is not true, these are injected through operational actions".
  - `.agent/owner-missing-fuel-2026-11-07.md`: "'Unexplained fuel', never 'theft'".
  - `.agent/owner-fuel-scope-2026-11-07.md`: "Generic 3.3 L/h, labelled (Recommended)". Kisiwa applies the same generic rule, so its rate is 4.9 L/h.
- **What this section does.** Each card below is the one current card for its unit. It replaces §3.1, the K1 and K2 rows of §8.4, the K1 row of §9.5 and the K1 notes in §9.2 and §9a. **Builders read only their card.** Paths use the header's short forms.
- Two code facts change §3.1 and §8.4. Both are folded into the cards:
  - **Signal resolution (§3.1 pre-flight (a)) is closed.** F0r ran `registered-kobo-publication` v5 on an imported Kisiwa with no refusal. The profile is not bound to `KOBO-001` by name.
  - **The registered-parity reference is now F0r, not D0.** D0 is dropped from the demo (§8.1). F0r's `.agent/DIESEL-F0/probe-result.json` is the reference. Its F3 already holds D0's 43.428 L per night.

### 9c.1 K1 card: the Kisiwa Site, 1.25 (range 1.0–1.5)

**Lane, start, branch.**
- Lane 3. K1 starts once **F0 (the F8 fix, evidence-only) and K1a have both merged**. It is on the critical path.
- Branch `task/DIESEL-K1-kisiwa-site`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k1`, from main after both merges.
- Opus does the first build and the first review.

**What K1 delivers.** `KISIWA-001` registered the way the demo prepare will register it: import, convert, demo configuration, supply uses, no-load fact, sensor accuracy and diesel price. It also proves, on Postgres, that the registered Site reproduces F0r's measured result exactly.
- K1 does **not** add Kisiwa to `T/demo_combined.py` (`SITES`, `SITE_CODE`). It does not run a story day, a scenario calendar or a prepare. Those belong to K7.
- So no client screen of the demo DB changes when K1 merges.

**Files (all new unless marked edit):**

| # | File | Content |
|---|---|---|
| 1 | `C/site-templates/kisiwa-diesel-hybrid-60kw.yaml` | `.agent/DIESEL-D0/kisiwa-diesel-hybrid-60kw.draft.yaml`, **every byte from `template_id:` (line 23) to the end unchanged**. Only lines 1–21 (the DRAFT comment) are replaced by a shipped-template header (literal below). Parsed content therefore equals the draft. |
| 2 | `backend/tests/test_site_template_fingerprints.py` (edit) | One pin: `("kisiwa-diesel-hybrid-60kw", 1): ("013c3bbc9c9fcf6897eab6eb3d811637c606ee980feb06e53730f9903d4ca07c")`. The Architect computed it with `content_fingerprint` on the draft. |
| 3 | `backend/tests/test_site_template_catalog.py` (edit) | The shipped listing becomes `["hybrid-mini-grid-100kw", "kisiwa-diesel-hybrid-60kw", "kobo-mini-grid-60kw", "twin-tank-mini-grid-150kw"]`, with one comment line: "Four since DIESEL-1 K1: the Kisiwa diesel-hybrid island archetype." |
| 4 | `backend/tests/fixtures/s1/kisiwa-001.yaml` | The import record, as `B/tests/fixtures/s1/kobo-001.yaml` is for Kobo. It is exactly `yaml.safe_dump(render_site_document(record), sort_keys=True)`, where `record` = `site_from_template(<file 1>, site_id="KISIWA-001", display_name="Kisiwa island mini-grid", timezone="Africa/Dar_es_Salaam")` with `foundation.valid_from = "2026-09-01T00:00:00Z"`. That is F0r's `register_kisiwa` payload, with the shipped template in place of the draft. |
| 5 | `V/kisiwa-001-bindings.json` | `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json`, **byte-equal**: 12 rows, `minigrid-roles-2`, `declare_signals: []`, the R3a note. |
| 6 | `V/kisiwa-001-minigrid-roles-demo-config.json` | The roles-4 demo configuration (literal below). |
| 7 | `B/sites/models.py` (edit) | The sensor-accuracy vocabulary (below). |
| 8 | `T/demo_combined_kisiwa.py` | The registration flow (below). |
| 9 | `host/tests/kisiwa.py` | The registered Kisiwa drafter (below). |
| 10 | `backend/tests/test_k1_kisiwa_fixtures.py` | L0 tests, no DB. |
| 11 | `backend/tests/test_k1_kisiwa_site_postgres.py` | L2 on own `assetops_k1_test`. |
| 12 | `host/tests/test_k1_registered_kisiwa.py` | L2 registered parity on own `assetops_k1_test`. |

**Shipped-template header (file 1, lines 1–n, literal):**
```
# Shipped Site configuration template. Read-only at runtime.
#
# The Kisiwa diesel-hybrid island archetype (DIESEL-1 §2.2, promoted by K1,
# DIESEL-1-R3c): a small PV array behind one inverter, one battery behind one
# power conversion system, and a 60 kW diesel generator with its 1000 L tank
# that carries the night and charges the battery while it runs ("cycle
# charging": source priority PV, generator, battery). Three separately metered
# loads: households, a cold store for ice and fish, and a water pump.
#
# Component, device, signal and mapping ids are Kobo's, unchanged: the
# dispatch analytic reads Kobo's device ids by name. Display names, ratings,
# property values and Site Controls carry what differs.
#
# The numbers are DEMONSTRATION values, fixed before the D0 probe ran and
# never tuned: plausible for a small island mini-grid, not a recommendation
# for any real installation and not calibrated to one.
#
# Everything here is component truth about the template and never evidence.
# Templates copy; they never migrate an existing Site.
```

**Foundation vocabulary (file 7), following A1's pattern:**
- In `COMPONENT_PROPERTY_DEFINITIONS`, after the A1 entries, with the comment `# DIESEL-1 K1 (R3c): the tank level sensor's declared accuracy, read by fuel-balance-1 (K3) as the margin term a.`:
  - `"fuel-level-sensor-accuracy": PropertyDefinition(unit="L", kind="PHYSICAL", display_name="Fuel level sensor accuracy")`;
  - `"fuel-level-sensor-accuracy-basis": PropertyDefinition(unit="state", kind="PHYSICAL", display_name="Fuel level sensor accuracy basis")`.
- Add `STATE_PROPERTY_VALUES["fuel-level-sensor-accuracy-basis"] = frozenset({"GENERIC_DEFAULT", "MANUFACTURER_DATASHEET", "SITE_CALIBRATION"})`.
- Add both keys to `MINIGRID_PROPERTY_CARRIERS` with carrier `"FUEL_TANK"`, comment `# DIESEL-1 K1`.
- Add `"fuel-level-sensor-accuracy"` to `MINIGRID_STRICTLY_POSITIVE_PROPERTIES`. An accuracy of 0 L would claim a perfect sensor.
- `minigrid_foundation.py` needs no edit; it reads both tables.

**Roles-4 demo configuration (file 6, literal):**
```json
{
  "schema": {"id": "assetops.demo-configuration", "version": 1},
  "status": "SIMULATED DEMO CONFIGURATION - DIESEL-1-R3c (K1). Not operator-entered Site truth.",
  "label": "kisiwa-minigrid-roles-4-demo-config-v1",
  "site_code": "KISIWA-001",
  "component_properties": {
    "effective_from": "2026-09-29T09:57:00Z",
    "asset_code": "fuel-tank",
    "note": "Generic level-sensor accuracy, about 1 % of a 1000 L tank; not this sensor's calibration.",
    "properties": [
      {"property_key": "fuel-level-sensor-accuracy", "value": 10, "unit": "L", "source": "SITE", "source_version": 1},
      {"property_key": "fuel-level-sensor-accuracy-basis", "value": "GENERIC_DEFAULT", "unit": "state", "source": "SITE", "source_version": 1}
    ]
  },
  "bindings": {
    "effective_from": "2026-09-29T09:57:00Z",
    "role_set": "minigrid-roles-4",
    "note": "DIESEL-1-R3c K1 simulated demo configuration (kisiwa-minigrid-roles-4-demo-config-v1): every binding converted at import carried unchanged (12 rows, minigrid-roles-2), plus the cold store's (load-clinic, first in critical-load-priority) simulated requested and delivered power and the battery converter's charge request (registered-kobo-publication v5, mini-grid v7).",
    "declare_signals": [
      {"device_id": "clinic-meter", "signal_id": "requested-power", "display_name": "Cold store requested power (simulated critical load)", "unit": "kW"},
      {"device_id": "clinic-meter", "signal_id": "delivered-power", "display_name": "Cold store delivered power (simulated critical load)", "unit": "kW"},
      {"device_id": "battery-pcs-controller", "signal_id": "charge-requested-power", "display_name": "Battery charge requested power (simulated)", "unit": "kW"}
    ],
    "add": [
      {"device_id": "clinic-meter", "signal_id": "requested-power", "asset_code": "load-clinic", "role": "critical_load_requested_power", "source_unit": "kW", "canonical_unit": "kW", "conversion": {"kind": "IDENTITY", "parameters": {}}},
      {"device_id": "clinic-meter", "signal_id": "delivered-power", "asset_code": "load-clinic", "role": "critical_load_delivered_power", "source_unit": "kW", "canonical_unit": "kW", "conversion": {"kind": "IDENTITY", "parameters": {}}},
      {"device_id": "battery-pcs-controller", "signal_id": "charge-requested-power", "asset_code": "battery", "role": "storage_charge_requested_power", "source_unit": "kW", "canonical_unit": "kW", "conversion": {"kind": "IDENTITY", "parameters": {}}}
    ]
  }
}
```
- **Why the `component_properties` block is the sensor accuracy.** `apply_demo_configuration` requires the block (`B/sites/demo_configuration.py:49` `FIXTURE_KEYS`), and the tank is the one Kisiwa fact the roles-4 step needs. Both `effective_from` values are rewritten by the tool (Kobo's pattern, `T/demo_combined_kobo.py:112-116`).
- **Kobo's D-W1-3 margins are not declared at Kisiwa.** These are `pv-available-uncertainty` 3 kW and `renewable-retained-margin` 5 kW. They are Kobo's values for the mill's midday spare-solar check, Kisiwa has no productive load, and there is no basis for a Kisiwa figure. The midday check therefore reads its existing "not declared" state there. Pre-flight (c) confirms that this state exists.
- **Signals the template lacks.** The template declares none of the three added signals, so they are declared here with Kisiwa names. Kobo's configs name them "Clinic …", which is false for a cold store.

**Registration flow (`T/demo_combined_kisiwa.py`).** Modelled on `T/demo_combined_kobo.py:62-149`, `:385-408`. K7 later adds the story part to this file; K1 writes only the part below.
- Constants:
  - `SITE_CODE = "KISIWA-001"`;
  - `SITE_SOURCE = <file 4>`, `BINDINGS = <file 5>`, `ROLES4 = <file 6>`;
  - `CONFIG_OFFSETS = {"uses": timedelta(minutes=25), "roles4": timedelta(minutes=27), "known": timedelta(minutes=30), "price": timedelta(hours=1)}`;
  - `SUPPLY_USES = {"load-clinic": "ESSENTIAL_SERVICE", "load-res": "HOUSEHOLD", "load-mill": "HOUSEHOLD"}` (§2.2);
  - `NO_LOAD = [{"property_key": "generator-no-load-fuel-rate", "value": 4.9, "unit": "L/h", "source": "SITE", "source_version": 1}, {"property_key": "generator-no-load-fuel-rate-basis", "value": "GENERIC_DEFAULT", "unit": "state", "source": "SITE", "source_version": 1}]`;
  - `NO_LOAD_NOTE = "Generic no-load fuel rate for a 60 kW diesel set (common design-software default, about 0.08 L/h per kW of rating); not this generator's datasheet. Owner decision 2026-11-07 (generic, labelled)."`;
  - **the model pin:** `RUN_PROFILE = {"model_profile": {"profile_id": "mini-grid", "profile_version": 7}, "publication_profile": {"profile_id": "registered-kobo-publication", "profile_version": 5}, "timestep_minutes": 5, "seed": 20260929}`. Kisiwa runs only on v7 (K1a). Kobo stays on v6, through `V/d-verification-window-v3.json`, which is not edited.
- `register_in(store, import_at, install_at) -> dict`. It is store-agnostic: Postgres in the prepare and L2, `InMemoryFoundationStore` in L0. Steps, in order:
  1. `import_site(store, tenant_slug="demo", configured_tenant_slug="demo", source=ImportSource(path="var/sites/kisiwa-001.yaml", sha256=<sha256 of file 4's bytes>, record=read_import_source(file 4).record), legacy_documents=(), clock=Clock(import_at))` (`B/sites/foundation_service.py:247`).
  2. `convert(store, BindingService(store, Clock(install_at)), tenant, site, BINDINGS)`.
  3. Using `FoundationService(store, "demo", Clock(install_at + known))` and `BindingService(store, same clock)`:
     - (a) `declare_supply_uses`: one `publish_component_properties` per load at `install_at + uses`, note "Demonstration supply use declared at commissioning" (Kobo's literal);
     - (b) `declare_no_load_rate`: one publish on `generator` at `install_at + uses`, properties `NO_LOAD`, note `NO_LOAD_NOTE`;
     - (c) `configure_roles4`: deep-copy `ROLES4`, set both `effective_from` to `install_at + roles4`, assert the status prefix, then `apply_demo_configuration`, and assert `periods[-1]["role_set"] == "minigrid-roles-4"`.
  4. Return `{"site_code", "tenant_id", "site_id", "import_at", "install_at", "supply_uses_effective_from", "no_load_effective_from", "roles4_effective_from", "recorded_at", "periods"}`.
- `register(url, work, import_at, install_at) -> dict`. Postgres only:
  - `register_in(PostgresFoundationStore(url), …)`;
  - the same `UPDATE gateway/source SET disabled_at = NULL WHERE site_id = :s` as Kobo (`:405-407`);
  - **diesel price v1 only**: `publish(["fixture", "--site", "KISIWA-001", "--file", <V/demo-diesel-price-publications.json>, "--step", "v1"])` through `PostgresAssumptionStore(url, test_recorded_clock_override=lambda: install_at + price)`;
  - no productive-use price (Kisiwa has no productive load);
  - write `<work>/kisiwa-register.json`.
- CLI: `python tools/demo_combined_kisiwa.py register <database-url> <work> <import-at ISO> <install-at ISO>`.
- The no-load and the accuracy facts are Site-declared data. Their "generic" label travels in the basis property, never in product copy (A1's rule).

**The registered drafter (`host/tests/kisiwa.py`):**
- `class KisiwaRegistered`, constructed as `KisiwaRegistered(store, setup_at: str)`. It has the attribute and method surface that `T/probe_kisiwa_fuel.py` `build()`, `execute_day()` and `readings()` use from `Registered`:
  - `.store`;
  - `.basis = RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, "demo", Clock(setup_at))))`;
  - `.foundation_version`, from `basis.select("KISIWA-001", start_time=run 1 start, end_time=+1 day, knowledge_at=None)`;
  - `.v7_sim = assetops_simulator.packs.mini_grid.MINI_GRID_V7_MODEL` and `.v7_profile = B.runs.profiles.MINI_GRID_V7_MODEL` (**K1a's product v7, not the probe-local copy**);
  - `.draft(document, start, end, model="v7")`: the same `RunSetupService` call as the probe's `Registered.draft` (`T/probe_kisiwa_fuel.py:325-347`), with product v7 or v6;
  - `.sim(model)`.
- `def draft_day(store, document, start, end, setup_at)`: a convenience wrapper for the L2 site test.

**Registered parity (`host/tests/test_k1_registered_kisiwa.py`, L2, `assetops_k1_test`):**
- Module fixture:
  - `pg_harness.fresh_database()`;
  - `register_in(PostgresFoundationStore(URL), import_at=2026-09-29T09:00:00Z, install_at=2026-09-29T09:30:00Z)` (F0r's clock: import 09:00, conversion 09:30);
  - setup clock `"2026-09-29T11:00:00Z"`, after everything is recorded at 10:00.
- Test `test_f0r_reproduces_on_the_registered_site`:
  - `monkeypatch.setattr(probe, "Registered", lambda: KisiwaRegistered(store, "2026-09-29T11:00:00Z"))`, then `result = probe.build()`. **`T/probe_kisiwa_fuel.py` is not edited.**
  - Load the committed `.agent/DIESEL-F0/probe-result.json` as `ref`.
  - Assert `result == ref` after removing, from both, **only**:
    - `assumptions.model` and `assumptions.probe_local_v7` (product v7 replaces the probe copy);
    - `assumptions.registered_path` (foundation and binding-set version, snapshot, selection and clocks differ by design);
    - `gates.F6.example_fuel_level_report_text` (its key hashes the run id and snapshot).
  - From `gates.F6.snapshot_fuel_level_binding`, keep only `role`, `source_unit`, `canonical_unit` and `conversion`, and compare those.
  - Everything else must be equal, every litre, band, state, gap, dip, count and gate value included. That covers `runs` (scenario sha, intervention history, start and end states), `night4_tank_account`, `nights`, `dips`, and gates F0a–F5, F7, F9 and F11.
  - Print the removed keys' two values for the packet.
- Why this is the right check: F0r ran on Foundation v1 with roles-2. K1 adds the supply uses, the no-load fact, the accuracy and roles-4. None of these may change physics or the tank publication. Dropout is keyed per signal (`S/observation/transform.py:189-200`), so the added roles-4 signals cannot move a fuel-level dropout.

**L0 tests (`backend/tests/test_k1_kisiwa_fixtures.py`, no DB):**
1. The shipped template parses through the catalog. Its parsed document equals the draft's parsed document. Its bytes from `template_id:` onward equal the draft's.
2. File 5 is byte-equal to `.agent/DIESEL-F0/kisiwa-001-bindings.draft.json`.
3. File 4 is byte-equal to the render described in the files table.
4. File 6 checks:
   - its keys are exactly `FIXTURE_KEYS`, its status starts "SIMULATED DEMO CONFIGURATION", `site_code` is KISIWA-001 and `role_set` is roles-4;
   - each `add` role is in roles-4's vocabulary (`B/sites/binding_roles.py`);
   - no `display_name` or `note` contains "Clinic", "clinic ", "mill", "Mill" or "Kobo" (case-sensitive except as listed). The device id `clinic-meter` is an id, not copy, and is exempt.
5. The vocabulary:
   - 10 L accepted on FUEL_TANK and refused on GENERATOR (carrier);
   - 0 L refused (strictly positive);
   - basis `SITE_CALIBRATION` accepted and `SITE_TEST` refused;
   - `L/h` refused for the accuracy (unit).
6. `register_in` on `InMemoryFoundationStore` (F0r's precedent, `backend/tests/foundation_fakes.py`) at import 2026-09-29T09:00Z and install 09:30Z. At 2026-10-01T12:00Z, as known at 10:00Z:
   - `fuel-tank` declares 10 L and GENERIC_DEFAULT;
   - `generator` declares 4.9 L/h and GENERIC_DEFAULT, and keeps every template property;
   - the three loads carry their supply uses;
   - the binding set is roles-4 with 15 bindings (12 + 3).
   - If the in-memory store cannot run `apply_demo_configuration`, this item moves to L2 unchanged (no stop).
7. `RUN_PROFILE`'s model `("mini-grid", 7)` is in `host/execution_adapter.py` `EXECUTABLE_MODELS` and in `MODEL_PROFILES`, and `V/d-verification-window-v3.json` still pins mini-grid 6.

**L2 site test (`backend/tests/test_k1_kisiwa_site_postgres.py`, `assetops_k1_test`):**
- `register(url, tmp, import 2026-09-29T09:00Z, install 09:30Z)`. Then:
  - the three Foundation facts and the supply uses, as known at install + 30 min;
  - the diesel price v1 (1.25 USD/L) known at install + 1 h through the assumption read the cost path uses (PRE-FLIGHT names it; `select_window_price` or its store);
  - binding set roles-4.
- **One Kisiwa day end to end.** F0r run 1 is 2026-10-01T12:00Z to 2026-10-02T12:00Z, `probe_kisiwa_nights.day_document(probe_kisiwa_fuel.START_SOC, probe_kisiwa_fuel.START_FUEL)`, with no actions.
  - Draft it through `draft_day` (READY, registered basis frozen, v7/v5).
  - Publish and accept it with `test_s6_verification_replay._publish_and_accept` (real gateway, S2 at `received_at` = 2026-10-02T12:10Z).
  - Run S3 assess and S4 match with `LabRunner` at +5 min.
  - Assert:
    - accepted `fuel_level` records exist for KISIWA-001: the first tank readings the product has stored;
    - the dispatch assessment for the window exists with no refusal (same device ids);
    - the Site outcome board read for KISIWA-001 returns 200 (PRE-FLIGHT names the call), and every row's state is a member of its existing state set.
  - Print every served board string for pre-flight (c) and (b).
- Rough machine time: one 24 h run through the gateway, about 3–5 min.

**PRE-FLIGHT (no code first; batch every question in one message):**
- (a) Closed by F0r (see the top of §9c).
- (b) Strings that name "clinic", "mill" or "Kobo" on a Kisiwa screen by device or component id instead of the Site's display name. The Architect's grep finds:
  - server: `B/evidence/overview.py:71-75` `SERVICE_FEEDERS` ("Clinic feeder", "Mill feeder");
  - UI: `F/sites/MiniPerformance.tsx:971` `CLINIC_FEEDER_LABEL` and `F/sites/SiteWindowOverview.tsx:484` (the "residential, clinic and productive loads" objective).
  - Rule: **K1 fixes a server string only if the Site's display names are already an input of that read.** Otherwise, and for every UI string, K1 lists it with file:line in its packet as a finding for **K8**, which the Architect sizes at K8's card round.
  - `SERVICE_FEEDERS` has no Foundation input, so it goes to K8. **No Kobo byte changes in K1.**
- (c) Every board row without a PRODUCTIVE load (Grow sales, the mill's midday check, Kobo's D-W1-3 margins) must read an existing honest state at Kisiwa. A row that needs new text is a **stop**.
- (d) Name the in-memory store's support for `publish_component_properties` and `apply_demo_configuration` (decides L0 item 6), and the board and price read calls.

**Client wording.**
- K1 adds no served copy and no UI string. Its client-visible strings are Site data:
  - the Site name "Kisiwa island mini-grid";
  - the template's component display names ("Households", "Cold store (ice and fish)", "Water pump", "Generator fuel tank" …);
  - the property display names "Fuel level sensor accuracy" and "Fuel level sensor accuracy basis";
  - the three declared signal names above;
  - the two notes.
- None says theft, stolen, stole, siphon or pilfer (H4).
- **MOCK DEVIATION MD-KIS-K1-1.** On Kisiwa's pages, the load names and roles come from Kisiwa's Foundation, not from v69's Kobo-like text. Examples: `frontend/mockups/v69/index.html:420` "Clinic feeder", "Grain mill · productive", and `:619`. Layout and components are unchanged; only data differs. Kisiwa reaches a client screen only after K7, and the four-Site estate screens are K8's.

**Guards and checks.**
- `tools\check-all.ps1`, `tools\check-architecture.ps1`, `tools\check-agent-workflow.ps1` and `tools\check-navigation-truthfulness.ps1`, run directly with no `-ExecutionPolicy`.
- `T/probe_kisiwa_fuel.py --check` and `T/probe_kisiwa_nights.py --check` must still print "probe result current".
- **Localised tests only** (no full suite in the sprint):
  - the three new files;
  - `test_site_template_fingerprints.py`, `test_site_template_catalog.py`;
  - `test_s1_bindings.py`, `test_s2_registered_basis.py`;
  - the A1 vocabulary tests (`test_fuel_cost_v2.py` parser part);
  - `test_scenario_execution_contract.py`, `test_execution_contract_alignment.py` (vocabulary must not move a digest);
  - `host/tests/test_mini_grid_v7.py`.

**DB.** Only `assetops_k1_test`, created by `pg_harness`. Never `assetops_demo3_full_test` or any other DB. No prepare, no tick, no `serve`.

**Stops (report to the Architect; never design around them):**
- any Kobo, Cold or EV byte change (templates, fixtures, configs, digests, served bytes);
- the vocabulary addition moves a scenario, run-contract or handover digest;
- a refusal anywhere in the registration flow (import, convert, a publish, the demo configuration, the price): report it verbatim with file:line and never edit the template, the bindings or a value;
- **the parity test finds any difference** outside the removed keys: report the key and both values, and never edit `probe-result.json` or the probe;
- a board row at Kisiwa needs new text (pre-flight (c));
- a migration would be needed;
- more than 1.5 units.

**Size 1.25:**
- template, pin and catalog 0.1;
- import record and render check 0.1;
- vocabulary and parser tests 0.15;
- bindings promotion and roles-4 config 0.1;
- `register_in` / `register` 0.3;
- drafter and parity test 0.25;
- L2 site test 0.2;
- pre-flight inventory 0.05.

**Reading budget:** this §9c.1; §2.2 (the table only); `T/demo_combined_kobo.py:30-150`, `:385-410`; `host/tests/test_dd1a1_registered_kobo.py:1-100`; `T/probe_kisiwa_fuel.py:240-450`, `:482-520`; `B/sites/demo_configuration.py:80-215`; `B/sites/models.py:255-340`; `backend/tests/test_s1_bindings_postgres.py:35-110`; `backend/tests/test_s6_verification_replay.py` (`_draft`, `_publish_and_accept`, `LabRunner` only); the K1a diff for the v7 names.

### 9c.2 K2 card: fuel delivery and tank dip records on Work operational records, 0.75 (range 0.6–1.0)

**Lane, start, branch.**
- Lane 2, after **A2 merges**. Branch `task/DIESEL-K2-fuel-records`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k2`, from main after A2's merge.
- Opus does the first build and the first review.

**No conflict with A2, checked against A2's branch diff (`7a390ea66`).** A2 edits:
- `B/actions/` (`verification.py`, `verification_rules.py`, the Postgres action store);
- `B/financials/trial_fuel_comparison.py`, `B/outcomes/credit.py`, `B/estate/portfolio.py`, `B/site_outcomes/board.py`;
- `F/estate/estateClient.ts` and its tests.

A2 adds no migration. K2 touches none of those files. K0 (later on lane 2) and K1 (lane 3) do not touch `B/work/`. **K2 owns migration 0054.**

**What K2 delivers.**
- Two new Work operational record kinds, `FUEL_DELIVERY` and `TANK_DIP`, posted through the existing route `POST /api/sites/{site_code}/work/operational-records` (`B/work_api.py:185-189`). Each carries a tank link, `asset_id`.
- An as-known read, `fuel_records`, for K3.
- Plain labels for the two kinds on the existing records screens.
- **Unchanged:** the four existing kinds, their command hashes, responses and rows. The contract's `OPERATIONAL_RECORD_KINDS` (`contracts/…/source_envelope.py:126`) and the run path are untouched.

**API body (closed shape).**
- `OPERATIONAL_KEYS` (required) is unchanged.
- The optional keys become `OPERATIONAL_CORRECTION + ("asset_id",)`.
- `OPERATIONAL_KINDS = ("OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT", "FUEL_DELIVERY", "TANK_DIP")`, and `FUEL_KINDS = ("FUEL_DELIVERY", "TANK_DIP")` in `B/work/service.py`.

Examples. K7's injector uses these body sentences verbatim, filled from the action log and the handover file:
```json
{"kind": "FUEL_DELIVERY",
 "body": "Fuel delivery of 300 L received, ticket KIS-DT-0001.",
 "occurred_at": "2026-10-03T07:00:00Z", "period_end": null,
 "unit": "L", "quantity": "300",
 "source_document_sha256": "<64 lowercase hex: sha256 of the delivery ticket document>",
 "case_id": null, "asset_id": "<the Site's fuel-tank asset id>",
 "actor": {"kind": "SERVICE", "id": "<principal>", "attestation": "service=<principal>;job=<job>;rule=<rule>"},
 "idempotency_key": "kisiwa-kis-delivery-1"}
```
```json
{"kind": "TANK_DIP", "body": "Tank dip at the 07:00 round: 706 L.",
 "occurred_at": "2026-10-05T04:00:00Z", "period_end": null, "unit": "L", "quantity": "706",
 "source_document_sha256": null, "case_id": null, "asset_id": "<fuel-tank asset id>",
 "actor": {...}, "idempotency_key": "kisiwa-kis-dip-n4-0700"}
```
- `occurred_at` is when the delivery or dip happened. The record's `recorded_at` is the command's DB instant: K7 sets it through the existing test-only `test_db_clock_override` seam (`B/work/adapters/postgres_work_store.py:281-285`), recording the ticket 30 min after delivery (§8.2a).
- The existing 30-day backdate limit and the 5-minute future slack (`B/work/model.py:36-37`) apply unchanged.

**Validation, in this order. The existing steps are unchanged; the new ones are marked NEW:**
1. Gate; closed shape; actor; correction triple; `kind ∈ OPERATIONAL_KINDS` (else `WORK_INPUT_INVALID`); instants; quantity, unit and digest shapes; the existing check `(quantity is None) != (unit is None)` or MANUAL_READING without a quantity or `period_end < occurred_at` → `WORK_INPUT_INVALID`.
2. NEW, before the transaction:
   - a fuel kind without the `asset_id` key, or with null → `WORK_RECORD_ASSET_REQUIRED`;
   - a non-fuel kind with the `asset_id` key present (even null) → `WORK_RECORD_ASSET_NOT_ALLOWED`;
   - a fuel kind with `period_end` not null → `WORK_INPUT_INVALID` (both are instants);
   - a fuel kind with `quantity` null or `unit != "L"`, or a `FUEL_DELIVERY` with quantity 0 → `WORK_RECORD_QUANTITY_INVALID` (a dip may be 0 L);
   - a `FUEL_DELIVERY` with `source_document_sha256` null → `WORK_RECORD_TICKET_REQUIRED`;
   - `asset_id` not a UUID → `WORK_INPUT_INVALID` (`m.uuid_text`).
3. In the transaction, the existing order: an idempotent retry (200 or `WORK_EVENT_DUPLICATE_KEY`); `check_occurrence`; the case scope. Then NEW: `tx.asset_type(asset_id)` is None → `WORK_LINK_SCOPE_INVALID` (the existing code for a foreign or unknown asset); a value other than `"FUEL_TANK"` → `WORK_RECORD_ASSET_NOT_TANK`. Then the correction successor and the insert.
- **Canonical hash: byte-equal for the four existing kinds.** `canon["asset_id"] = m.uuid_text(body["asset_id"])` is added **only for a fuel kind**. The key is absent otherwise, so every existing `payload_sha256` and idempotency result is unchanged.
- The insert passes `asset_id` (None for the other kinds).
- The response `operational-record-1` is **unchanged** (no new field).

**Refusal codes (add to `B/work/model.py` `MESSAGES` and `STATUS`, all 422):**

| Code | Message (literal) |
|---|---|
| `WORK_RECORD_ASSET_REQUIRED` | "A fuel delivery or tank dip must name the fuel tank it concerns." |
| `WORK_RECORD_ASSET_NOT_ALLOWED` | "Only a fuel delivery or tank dip names a tank; other record kinds carry no asset." |
| `WORK_RECORD_ASSET_NOT_TANK` | "The named asset is not a fuel tank at this Site." |
| `WORK_RECORD_QUANTITY_INVALID` | "A fuel delivery needs a volume above 0 L, and a tank dip a volume of 0 L or more, in L." |
| `WORK_RECORD_TICKET_REQUIRED` | "A fuel delivery needs the SHA-256 of its delivery ticket." |

**Store (`B/work/adapters/postgres_work_store.py`):**
- `_Tx.asset_type(asset_id) -> str | None`, using `SELECT asset_type FROM asset WHERE tenant_id = :t AND site_id = :s AND id = :a AND retired_at IS NULL`.
- `insert_operational_record` gains the `asset_id` column and parameter.

**Migration `backend/migrations/versions/0054_operational_fuel_records.py`:**
- `revision = "0054_operational_fuel_records"`, `down_revision = "0053_fuel_cost_2"`.
- The constraint name `operational_record_kind_check` was confirmed by a read-only `pg_constraint` query on `assetops_test`.
```sql
ALTER TABLE operational_record DROP CONSTRAINT operational_record_kind_check;
ALTER TABLE operational_record ADD CONSTRAINT operational_record_kind_check
    CHECK (kind IN ('OPERATOR_LOG','MANUAL_READING','SHIFT_NOTE','SITE_VISIT','FUEL_DELIVERY','TANK_DIP'));
ALTER TABLE operational_record ADD COLUMN asset_id uuid NULL;
ALTER TABLE operational_record ADD CONSTRAINT operational_record_asset_fk
    FOREIGN KEY (tenant_id, site_id, asset_id) REFERENCES asset(tenant_id, site_id, id);
ALTER TABLE operational_record ADD CONSTRAINT operational_record_fuel_asset
    CHECK ((kind IN ('FUEL_DELIVERY','TANK_DIP')) = (asset_id IS NOT NULL));
ALTER TABLE operational_record ADD CONSTRAINT operational_record_fuel_quantity
    CHECK (kind NOT IN ('FUEL_DELIVERY','TANK_DIP') OR (quantity IS NOT NULL AND unit = 'L' AND period_end IS NULL));
ALTER TABLE operational_record ADD CONSTRAINT operational_record_delivery_ticket
    CHECK (kind <> 'FUEL_DELIVERY' OR (quantity > 0 AND source_document_sha256 IS NOT NULL));
CREATE INDEX operational_record_asset ON operational_record (tenant_id, site_id, asset_id, occurred_at)
    WHERE asset_id IS NOT NULL;
```
- The asset FK targets the existing `asset_scope_unique` (`0001`). Its default MATCH SIMPLE leaves rows with a null `asset_id` unchecked.
- Adding a nullable column fires none of the append-only triggers.
- **Downgrade:**
  - refuse with `RuntimeError("0054 downgrade requires no FUEL_DELIVERY or TANK_DIP operational records")` if any such row exists (rows are append-only, so they cannot be deleted);
  - then drop the index, the three CHECKs, the FK and the column;
  - restore the four-kind CHECK under the same name.
- **Renumber rule (§8.4):** if a migration has landed on main as 0054 before K2 starts, K2 takes the next free number and re-points `down_revision`. The single-alembic-head test catches a miss. **K3's 0055 then follows K2's number.**

**The `fuel_records` read, for K3 (new `B/work/fuel_records.py` and new `B/work/adapters/postgres_fuel_records.py`):**
```python
FUEL_KINDS = ("FUEL_DELIVERY", "TANK_DIP")

@dataclass(frozen=True)
class FuelRecord:
    root_id: str              # canonical record id (the REC lineage root)
    head_id: str              # the version selected at known_at
    code: str                 # the root's public code, REC-nnnnnn
    kind: str                 # the head's kind, one of FUEL_KINDS
    occurred_at: datetime     # the head's occurrence (a correction may move it)
    recorded_at: datetime     # the head's recorded_at
    root_recorded_at: datetime  # when the record was first recorded (K3's DELIVERY_RECORDED_LATE reads it)
    quantity_l: Decimal       # the head's quantity, exact
    ticket_sha256: str | None # the head's source_document_sha256
    actor_id: str
    body: str

class FuelRecordsPort(Protocol):
    def fuel_records(self, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID,
                     lo: datetime, hi: datetime, known_at: datetime) -> tuple[FuelRecord, ...]: ...
```
- **Selection.** Every operational-record root of the Site recorded at or before `known_at`, at its latest version recorded at or before `known_at` by `(recorded_at, id)`. This is the root/head shape of `_OPERATIONAL` (`B/work/adapters/postgres_global_read.py:74-85`). Keep a record whose **head** has kind in `FUEL_KINDS`, `asset_id = tank_asset_id`, and `occurred_at` in `[lo, hi)`. Order by `(occurred_at, root_id)`.
  - Membership uses the head's occurrence, unlike the list page's root occurrence: a corrected time must move a delivery to its true night.
- **Arguments.** All three instants must be UTC-aware and `lo < hi`, else `ValueError("fuel_records needs UTC instants with lo < hi")`. `known_at` is not capped (K3 passes a window end that is already in the past).
- **Adapter.**
  - `select_fuel_records(c: Connection, tenant_id, site_id, tank_asset_id, lo, hi, known_at)` runs on a caller's connection, so K3 can read inside its own snapshot.
  - `PostgresFuelRecords(database_url, *, statement_timeout_ms=30_000)` implements the port with one `REPEATABLE READ READ ONLY` transaction.
  - Neither one writes.
- **No new HTTP route in K2.** K5's list of deliveries and dips adds its route in its own card.

**Screens (frontend, small):**
- `F/work/WorkRequestRecord.tsx` `REC_KIND_LABEL` gains `FUEL_DELIVERY: "Fuel delivery"` and `TANK_DIP: "Tank dip"`. `recKindLabel` is also what the global Operational records page shows in its Type column (`F/work/OperationalRecords.tsx:126-128`), so no raw kind ever reaches the screen.
- In `F/work/globalWorkClient.ts`, add `export type FuelRecordKind = "FUEL_DELIVERY" | "TANK_DIP"` and set `GlobalOperationalRow.kind: GlobalOperationalKind | FuelRecordKind`.
- The kind filter (`GLOBAL_OPERATIONAL_KINDS`, `KIND_CHIPS`, `KIND_ZERO`, the backend `RECORD_KINDS` in `B/work/global_index.py:52` and `B/work/operational_index.py:26`) stays at the four v69 kinds.
- **MOCK DEVIATION MD-FUEL-K2-1.** v69's Operational records chips are "All, Operator log, Manual reading, Shift note, Site visit" (`frontend/mockups/v69/index.html:984`), and its subtitle names those four (`:1083`). Fuel delivery and tank dip rows appear under "All" with the plain labels above. No chip is added, and a `kind=FUEL_DELIVERY` URL stays the existing invalid-filter state.
- The reading line (`readingLine`, `OperationalRecords.tsx:97-101`) stays MANUAL_READING-only: the fuel bodies above already state the litres once.
- Wording: the guard words theft, stolen, stole, siphon and pilfer appear nowhere (H4).

**Tests:**
- **L0 `backend/tests/test_k2_fuel_records.py`** (no DB; a fake transaction implementing only the `_Tx` methods `post_operational_record` calls):
  - each new refusal, in the order above, with its literal message;
  - one existing-kind body (`oprec()` from `test_w401_work_service_postgres.py`, OPERATOR_LOG) gives a command hash **equal to a literal pinned from main before any edit**. The builder computes it on main first and commits the pin with the test;
  - `asset_id` present on a SITE_VISIT → `WORK_RECORD_ASSET_NOT_ALLOWED`;
  - `FuelRecord` window argument checks.
- **L2 `backend/tests/test_k2_fuel_records_postgres.py`** on own `assetops_k2_test` (Kobo imported via `test_s1_bindings_postgres.imported`; Kobo's `fuel-tank` asset is `FUEL_TANK`; `VirtualDbClock` as in W401):
  - migration up/down/up on an empty table;
  - down is refused with a fuel row present;
  - single alembic head;
  - post a delivery and a dip (201, `operational-record-1`, REC code, row `asset_id` set);
  - idempotent retry 200, and a different body under the same key gives 409;
  - the `generator` asset gives `WORK_RECORD_ASSET_NOT_TANK`; an unknown or foreign-Site asset gives `WORK_LINK_SCOPE_INVALID`;
  - a raw SQL insert of a TANK_DIP with a null `asset_id` violates `operational_record_fuel_asset` (the CHECKs hold below the service);
  - `fuel_records`:
    - the window is half-open at both edges;
    - a record recorded after `known_at` is absent;
    - a correction of the dip (new quantity, recorded later) is read as the head after its `recorded_at` and as the root before it;
    - a correction that moves `occurred_at` out of the window drops the record;
    - an OPERATOR_LOG of the same Site never appears;
  - the global Operational records list returns the fuel rows with `kind` set, and `?kind=FUEL_DELIVERY` keeps today's invalid-filter refusal.
- **Existing, must stay green unchanged:** `test_w401_work_service_postgres.py`, `test_w401_work_api.py`, `test_w401_migration_postgres.py`, `test_w401_work_read_postgres.py`, `test_w401_site_indexes_postgres.py`, the W6-01 operational-records tests (`test_w601*`), the single-alembic-head test. If any of them needs a behaviour edit, that is a stop. A test that only enumerates migration heads or the kind CHECK text may take the new head or kinds.
- **Frontend:** `operationalRecords.test.tsx` gains a TANK_DIP row rendering "Tank dip" in the Type cell. `workRequestRecord.test.tsx` gains a `recKindLabel("FUEL_DELIVERY") === "Fuel delivery"` case.
- **Guards:** the four tools, run directly, and `frontend-hardwiring` (the two labels are plain copy constants).

**DB.** Only `assetops_k2_test`. Never `assetops_demo3_full_test`. No prepare, tick or suite.

**Stops:**
- any change to an existing kind's `payload_sha256`, response bytes, row shape or refusal;
- a need to edit `contracts/` (`OPERATIONAL_RECORD_KINDS`), `B/runs/`, the scenario models or the envelope schema;
- a W401 or W601 test needs a behaviour change;
- a client screen would need a new chip, panel or route (that is K5's);
- more than 1.0 unit.

**Size 0.75:** migration and its tests 0.15; service, model codes and store 0.2; the read port and adapter 0.15; frontend labels 0.05; tests 0.2.

**Reading budget:** this §9c.2; `B/work/service.py:30-40`, `:398-530`; `B/work/model.py:1-90`, `:140-245`; `B/work/adapters/postgres_work_store.py:1-200`, `:266-333`; `B/work/adapters/postgres_global_read.py:55-145`; `backend/migrations/versions/0027_w4_work_cases.py:160-222`; `0053_fuel_cost_2.py` (pattern); `backend/tests/test_w401_work_service_postgres.py:1-150`, `:458-482`; `F/work/WorkRequestRecord.tsx:45-60`; `F/work/OperationalRecords.tsx:55-130`; `F/work/globalWorkClient.ts:140-200`.

### 9c.3 F0 review Lows and the residual risk, placed in the cards they belong to

F0 merged as evidence only (`992847b72`, review ACCEPT, `.agent/review-F0.md`). Its three Lows and its residual risk are assigned here. K0 is build-ready from §9.3 and its pre-flight, so items 1 and 4 bind K0 as amendments to §9.3. Item 2 binds K3's card, written at the round before K3 starts.

1. **L1, K0: the log id and file name.**
   - The F0r action log's own `log_id` is `kisiwa-001-operational-actions` (`.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml:18`). §9.3 item 2's example says `"log_id": "kisiwa-001"`.
   - **Ruling: the pre-registered file wins.** K0 promotes the log **verbatim** (§9.3) and never edits it, so the id stays `kisiwa-001-operational-actions`.
   - By §9.3's path rule `C/operational-actions/{log_id}-v{log_version}.yaml`, the file is **`C/operational-actions/kisiwa-001-operational-actions-v1.yaml`**. The run request key is `{"log_id": "kisiwa-001-operational-actions", "log_version": 1}`.
   - The adapter refuses a log whose inner `log_id` or `log_version` differs from its file name (`OPERATIONAL_ACTION_LOG_MISMATCH`, typed, nothing written). A K0 test covers that refusal.
   - This amends §9.3's example only. K7 uses the same key.
2. **L2, K3: the use-term source and the untested band edges.**
   - The probe's "readings" source took night use from the true trajectory (`T/probe_kisiwa_fuel.py:620-625`). §8.3 defines use from the **published generator readings per 5-minute slot**.
   - K3's card will require:
     - (a) K3 computes `loaded` and `idle_h` **only** from accepted generator readings, through A2's slot rule; it never reads a trajectory;
     - (b) K3's L0 tests pin the three edges F0's tests never exercised: an idle-only night with `idle_h × 4.9` in `use_high` (so dropping the idle term fails a test); a window with `residual_low` exactly 0 (WITHIN_MARGIN, not BELOW_MATERIALITY); and the delivery night's high edge, `+ D_tol` with the ticket tolerance, as an exact Fraction;
     - (c) K3's evidence states that Kisiwa has 0 idle minutes, so on Kisiwa's own nights the idle term is exercised only by the test in (b).
   - K3's L2 must also match F0r's per-night bands from the stored windows (the KIS-3 reproduction), now from readings.
3. **L3, information only:** `seeded_uuid4` wraps all of `build()` and so also seeds run ids. That is harmless.
   - K1's parity test calls `build()` without the seeding. Run ids and snapshot-derived values differ, and §9c.1 already removes exactly those keys. No action.
4. **Residual risk, K0: the operational origin is so far proven only through F0r's event-id carrier.** K0's tests add, beyond §9.3's list:
   - (a) a Kisiwa run-2 delivery and run-4 removal frozen with the **field** `origin == "OPERATIONAL_ACTION"` and `action_ref`, and an `event_id` that is `"{action_id}/{effect}"` with **no** `OPERATIONAL_ACTION/` prefix carrier;
   - (b) the omit rule, byte-level: for a scenario-only run, the rendered run, the frozen causes and conditions, the trajectory identity and every stored form contain neither the `origin` nor the `action_ref` key. The digests equal pins taken on main before K0's first edit (one Kobo, one Cold, one EV run);
   - (c) a round-trip through every run store keeps both fields for an action cause and keeps them absent for a scenario cause;
   - (d) the kernel result for the Kisiwa runs with actions equals F0r's per-step tank account for run 4 (40/3 L at steps 120–128) and run 2 (300 L at step 227). This shows that the real field path gives the same physics as the carrier.
   - Inside K0's 0.4 test allowance; no size change.

### 9c.4 Sizes, date and the tripwire

- **Unit sizes: unchanged.** K1 is 1.25 and K2 is 0.75. Every other §9.5 row stands.
- **Contingency (0.5).** It has now paid for the R3a, R3b and R3c card rounds and the F8 Sonnet round (about 0.25 together). About 0.25 remains, for K4's Finding-kind risk.
- **One new risk, off the critical path.** K1's pre-flight (b) routes Kisiwa's device-id copy, starting with `SERVICE_FEEDERS` and the two UI strings, to K8. The Architect sizes it at K8's card round; the estimate is +0.1 to +0.25 on lane 1. K8's code part runs beside K4 and K6, so the critical path does not move unless it exceeds about 1 unit.
- **Critical path.** F0r's two extra rounds (R3a and F8) add about 0.15 to its 0.5. The path is F0r about 0.65 → K1 1.25 → K3 1.5 → K4 2.0 → K6 1.5 → K7 freeze 0.5 → K8 captures 0.25 → K9 1.0, about **8.65 lane-units, about 2.9 working days**, with K1a run in parallel as it was. **That is below the 9.75 tripwire. It is not crossed, so no cut is needed.**
- **Demo date: unchanged at about +3.25 working days** (range 2.75–5.25) against the plan without Kisiwa.
- **Machine time:** K1's L2 adds about 5 min of one gateway-published day; K2 adds none of note. E3 is unchanged.

### 9c.5 Owner questions

None.

---

## 9d. Ruling DIESEL-1-R3d: the K3 consolidated card (`fuel-balance-1`, migration 0055)

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `5d8ac9ee3` (K2 merged, review `.agent/review-K2.md` ACCEPT with L1). K1 read on `task/DIESEL-K1-kisiwa-site` at `18b5bbcdc` (review packet; not merged). A2 (`099b57c96`) and K1a (`f9d27116b`) are merged.
- Owner decisions in force, verbatim: `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'"); `.agent/owner-diesel-night-window-2026-11-07.md` (a night runs "6 pm to noon"); `.agent/owner-fuel-scope-2026-11-07.md` ("Generic 3.3 L/h, labelled (Recommended)"; Kisiwa's generic rate is 4.9 L/h); `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions").
- **This card replaces** the K3 row of §8.4 and §9.5 and binds §9c.3 item 2. Builders read only this card. Paths use the header's short forms; `T/` = `tools/`.

### 9d.1 What K3 delivers

- The `fuel-balance-1` night check, as product code: for one Site, one fuel tank and one local night (18:00 to 12:00 next day, Site time), it compares the tank's change from **accepted `fuel_level` readings** with the generator's expected burn from **accepted generator readings** and the **recorded deliveries** (K2). The result is a residual band with a margin, a state, a reason when not assessed, limitations and reporting-gap minutes.
- One append-only stored row per night per tank. A new revision is written only when the inputs, as known, change.
- An explicit service and CLI that assess named nights. **No tick stage** in v1 (§9d.7).
- A read port K4 (Finding) and K6 (verification) use.
- **Unchanged:** dispatch Findings and their fuel-cost-1/2 money (K3 never feeds a dispatch consequence); `mini_depth.rules.assess_fuel_hour` and Kobo's Fuel page (byte-equal); every Kobo, Cold and EV file; `B/work/` (K2's read is called, not edited); `B/actions/` and `B/financials/` (imported, not edited); the probe files and `probe-result.json`.
- **No served copy and no UI string.** Reason and limitation codes are internal. K4/K5 own client wording. None of theft, stolen, stole, siphon or pilfer appears anywhere (H4).

### 9d.2 The calculation (pure, exact `Fraction`, in `B/fuel_balance/rules.py`)

**Parameters: F0's declaration, verbatim.** `PARAMETERS` is `T/probe_kisiwa_fuel.py:80-94` `PARAMETERS` copied byte-for-byte, plus one key `"parameter_version": "fuel-balance-1/v1"`. Constants, exactly as F0 (`:72-78`):
- `TANK_MARGIN_FACTOR = 2` (margin = 2 × a); `DELIVERY_TOLERANCE = Fraction(1, 100)`;
- `USE_LOW_FACTOR = Fraction(9, 10)`, `USE_HIGH_FACTOR = Fraction(11, 10)` (= fuel-cost-2's `MULTIPLIER`, asserted by a test);
- `MATERIALITY_L = Fraction(40)`; `EDGE_SEARCH_MIN = 30`; `GAP_LONGER_THAN_MIN = 60`; slot = 5 min.
- **a, SFC and r are not constants.** They are the Site's declared values as known (below). At Kisiwa they are 10 L `GENERIC_DEFAULT`, 0.355 L/kWh and 4.9 L/h `GENERIC_DEFAULT`, which are F0's values.
- Any change is a new parameter version, never a retune.

**Window.** Night `d` (a Site-local date) = `[local(d, 18:00), local(d + 1, 12:00))` converted to UTC with fold 0, using `mini_depth.inputs.zone(site timezone)`. A non-existent or ambiguous local instant refuses `FUEL_BALANCE_WINDOW_INVALID`. The window must start and end on a UTC 5-minute boundary (else the same refusal). At Kisiwa (`Africa/Dar_es_Salaam`, UTC+3) night `2026-10-04` = `[2026-10-04T15:00Z, 2026-10-05T09:00Z)`, 216 slots.

**Inputs (all as known at the cutoff `known_at`, §9d.4):**
- `fuel_level` readings of the tank asset with `source_time` in `[start − 30 min, end + 30 min]`; only quality `GOOD`, unit `L`, a finite decimal value (`verification_rules.parse_exact`, no `p/q`). Others are ignored.
- `generator_power` (INTERVAL_MEAN, kW) and `generator_state` (STATE_AT_INSTANT) readings of the generator asset over the same span, converted to `verification_rules.Reading` exactly as `B/actions/verification.py:653-658`.
- SFC: `PostgresActionStore.sfc_history(..., generator, start, end, known_at)` with `trial_fuel_comparison.sfc_for` semantics (one positive value in force over the whole window).
- r: `PostgresActionStore.no_load_history(...)` with `trial_fuel_comparison.no_load_for` semantics; its basis is read with the tank properties' query below (generator component, `generator-no-load-fuel-rate-basis`).
- a: the tank component's `fuel-level-sensor-accuracy` (unit `L`, one finite positive value) and `fuel-level-sensor-accuracy-basis` ∈ {`GENERIC_DEFAULT`, `MANUFACTURER_DATASHEET`, `SITE_CALIBRATION`}, on one Foundation revision in force over the whole window (K1's vocabulary literals, §9c.1). Read by K3's own adapter query, the `_generator_property_history` SQL shape (`B/actions/adapters/postgres_action_store.py:647-670`) with the tank's asset code and `value` kept as text for the state property.
- Fuel records: K2's `select_fuel_records(c, tenant, site, tank, lo=start, hi=end, known_at)` on K3's own connection (`B/work/adapters/postgres_fuel_records.py:40`). Deliveries = records whose `kind == "FUEL_DELIVERY"`; dips = `kind == "TANK_DIP"`.

**Use, only from accepted generator readings (§9c.3 L2 (a); A2's slot rule, never re-derived).** For each slot `t` in `[start, end)`:
- `kwh_t` = `verification_rules._power_slot(t, generator_power readings)[1]` (None when UNKNOWN);
- `state_t` = `verification_rules._instant(t, generator_state readings, numeric=False)[1]` (None when UNKNOWN);
- the slot is idle iff `state_t in verification_rules.RUNNING_STATES and kwh_t == 0` (A2's rule, `verification_rules.py:487-491`).
- `generator_kwh = Σ kwh_t`; `loaded_litres = SFC × generator_kwh` (A2's `fuel = SFC × generator kWh`, every slot's kWh, as fuel-cost does); `idle_seconds = 300 × idle slots`; `idle_h = idle_seconds / 3600`.
- Any `kwh_t` None → reason `GENERATOR_KWH_UNKNOWN`. Otherwise any `state_t` None → `IDLE_SECONDS_UNKNOWN` (A2's reason names).
- `verification_rules.py` is **imported, never edited** (the two private helpers are imported by name; K6 owns the next edit of that file). K3 never reads a run, a trajectory or the simulator.
- **Amended by DIESEL-1-R3h (§9h):** the idle test is the shared `verification_rules.idle_slot(...)`, which excludes the stop slot (RUNNING at `t`, a not-running sample at `t + 5 min`). K3 makes that one named edit to `verification_rules.py`.

**Opening, closing and conflicts (F0's rule).**
- Opening O = the value of the **last** accepted reading with `source_time` in `[start − 30 min, start]`; closing C = the **first** in `[end, end + 30 min]` (both ends inclusive).
- Two accepted readings at the instant chosen for O or C with different values → reason `FUEL_LEVEL_CONFLICT`.
- None found → `MISSING_OPENING` / `MISSING_CLOSING`.

**The band (F0's `balance`, `T/probe_kisiwa_fuel.py:106-134`, exactly):**
```
D      = Σ quantity_l of FUEL_DELIVERY records          D_tol = 1/100 × D
use_low  = 9/10 × loaded_litres
use_high = 11/10 × (loaded_litres + idle_h × r)
residual_low  = (O − C) + D − D_tol − use_high − 2a
residual_high = (O − C) + D + D_tol − use_low  + 2a
state: UNEXPLAINED        iff residual_low ≥ 40
       else EXCESS        iff residual_high < 0
       else WITHIN_MARGIN iff residual_low ≤ 0 ≤ residual_high
       else BELOW_MATERIALITY
```
- The evaluation order above is F0's. `residual_low == 0` is WITHIN_MARGIN.
- The five states are F0's: the brief's WITHIN_MARGIN / UNEXPLAINED / NOT_ASSESSED plus F0's BELOW_MATERIALITY and EXCESS (reported, no Finding in v1).

**NOT_ASSESSED reasons, in this precedence (the first that applies is stored):**
1. `NO_SENSOR_ACCURACY` (no single positive accuracy with a recognised basis in force over the window; Kobo's case);
2. `SFC_MISSING`; 3. `NO_LOAD_RATE_MISSING` (no rate in force over the window, or no recognised basis);
4. `MISSING_OPENING`; 5. `MISSING_CLOSING`; 6. `FUEL_LEVEL_CONFLICT`;
7. `GENERATOR_KWH_UNKNOWN`; 8. `IDLE_SECONDS_UNKNOWN`.
- F0 had only reasons 4 and 5, because a, SFC and r were probe constants and use came from the trajectory. Reasons 1–3 and 6–8 refuse a band when an input F0 held fixed is missing. They never change a band that is computed.
- Gap minutes and spans are computed and stored for NOT_ASSESSED windows too (F0 did the same).

**Reporting gap (F0's `reporting_gap_minutes`, `:100-103`).** Points = `[start] + sorted(source_time of accepted readings with start < t < end) + [end]`. `gap_minutes` = Σ of consecutive differences longer than 60 min. `gap_spans` = those `(from, to)` pairs, in order (K4's "from {a} to {b}"). Night 4: one span, `2026-10-04T21:45Z` to `2026-10-04T23:30Z`, 105 min.

**Limitations (information only; they never change the state; fixed order, each at most once):**
1. `REPORTING_GAP` iff `gap_minutes > 0`.
2. `DIP_SENSOR_CONFLICT` iff some dip in the window has a nearest accepted `fuel_level` reading within 30 min of its `occurred_at` (by |Δt|, ties to the earlier) and `|dip − reading| > a + 10 L` (strictly). A dip with no reading within 30 min is not checked.
3. `DELIVERY_RECORDED_LATE` iff some counted delivery has `root_recorded_at > end + 30 min` (strictly), §9d.3.

**Result shape** (`WindowResult`, frozen): `state`, `reason`, `residual_low`, `residual_high` (Fraction or None), `gap_minutes`, `gap_spans`, `limitations`, and `terms` = `{opening_l, opening_at, closing_l, closing_at, deliveries_l, delivery_tolerance_l, generator_kwh, loaded_litres, idle_seconds, use_low, use_high, accuracy_l, accuracy_basis, accuracy_revision_id, sfc_l_per_kwh, sfc_revision_id, no_load_l_per_h, no_load_basis, no_load_revision_id, unknown_slots}`. Exact values are serialised with `verification_rules.fmt` (decimal, or `p/q`); unknown terms are null.

### 9d.3 Rulings on K2's review (L1 and the residual risk)

- **L1 is closed in K3's tests (§9d.6 B2–B4).** A correction that changes a dip's kind or tank must drop it from the old tank's read after the correction's `recorded_at`, and keep it before. The tests are written so that each of the reviewer's three mutations of `postgres_fuel_records.py:33` (root kind only; root tank only; both) fails at least one test. K2's code is not edited.
- **Cross-kind correction (OPERATOR_LOG → FUEL_DELIVERY) keeps the root's code and first-recorded time: intended, and pinned.**
  - The question `DELIVERY_RECORDED_LATE` answers is whether the operator **first wrote the delivery down** after the night could be checked. An operator who logged "300 L delivered" as a free-text log on time and later retyped it as a fuel delivery reported it on time. The retyping is a correction of the record's type, not a late report. So lateness is measured from `root_recorded_at`.
  - What the late retyping does change is **what the check could count**. Before the correction's `recorded_at`, the head is an OPERATOR_LOG, so the delivery is absent from `fuel_records` and from the band. K3's as-known revisions keep both: the window assessed before the correction (the delivery missing, typically EXCESS or a low residual) and the window assessed after (the delivery counted). Nothing is rewritten.
  - The record keeps the root's public code (`REC-nnnnnn`), so the Finding and the records page point to one record.
  - B4 pins all three: absent before the correction, counted after with the root's code and `root_recorded_at`, and no `DELIVERY_RECORDED_LATE` when the root was recorded on time; plus the converse, a FUEL_DELIVERY root first recorded after `end + 30 min` is flagged.
- **The partial index is unused by K2's read** (review residual risk 2). Acceptable at demo scale (one tank, tens of records a night). After-the-demo list: "fuel_records read: use the asset index (filter tank and occurrence before the per-root head scan)".

### 9d.4 Storage, service and when it runs

**Migration `backend/migrations/versions/0055_fuel_balance_window.py`.** `revision = "0055_fuel_balance_window"`, `down_revision = "0054_operational_fuel_records"`. Renumber rule (§8.4): if another migration lands first, K3 takes the next free number; K4 then follows.
```sql
CREATE TABLE fuel_balance_window (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    tank_asset_id uuid NOT NULL,
    generator_asset_id uuid NOT NULL,
    night_date date NOT NULL,
    window_start timestamptz NOT NULL,
    window_end timestamptz NOT NULL,
    revision integer NOT NULL CHECK (revision >= 1),
    parameter_version text NOT NULL CHECK (parameter_version = 'fuel-balance-1/v1'),
    recorded_at timestamptz NOT NULL,
    state text NOT NULL CHECK (state IN ('UNEXPLAINED','BELOW_MATERIALITY','WITHIN_MARGIN','EXCESS','NOT_ASSESSED')),
    reason text NULL CHECK (reason IN ('NO_SENSOR_ACCURACY','SFC_MISSING','NO_LOAD_RATE_MISSING','MISSING_OPENING',
        'MISSING_CLOSING','FUEL_LEVEL_CONFLICT','GENERATOR_KWH_UNKNOWN','IDLE_SECONDS_UNKNOWN')),
    residual_low text NULL,
    residual_high text NULL,
    gap_minutes integer NOT NULL CHECK (gap_minutes >= 0),
    gap_spans jsonb NOT NULL,
    limitations jsonb NOT NULL,
    terms jsonb NOT NULL,
    evidence_ids jsonb NOT NULL,
    record_ids jsonb NOT NULL,
    input_sha256 text NOT NULL CHECK (input_sha256 ~ '^[0-9a-f]{64}$'),
    CONSTRAINT fuel_balance_window_revision_unique UNIQUE (tenant_id, site_id, tank_asset_id, night_date, revision),
    CONSTRAINT fuel_balance_window_tank_fk FOREIGN KEY (tenant_id, site_id, tank_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT fuel_balance_window_generator_fk FOREIGN KEY (tenant_id, site_id, generator_asset_id)
        REFERENCES asset(tenant_id, site_id, id),
    CONSTRAINT fuel_balance_window_closed CHECK (window_end > window_start
        AND recorded_at >= window_end + interval '30 minutes'),
    CONSTRAINT fuel_balance_window_reason CHECK ((state = 'NOT_ASSESSED') = (reason IS NOT NULL)),
    CONSTRAINT fuel_balance_window_band CHECK ((state = 'NOT_ASSESSED') = (residual_low IS NULL)
        AND (residual_low IS NULL) = (residual_high IS NULL))
);
CREATE INDEX fuel_balance_window_night
    ON fuel_balance_window (tenant_id, site_id, tank_asset_id, night_date, recorded_at);
CREATE TRIGGER fuel_balance_window_immutable BEFORE UPDATE OR DELETE ON fuel_balance_window
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
```
- `residual_low`/`residual_high` hold `fmt` exact text. `evidence_ids` = sorted accepted-evidence ids read; `record_ids` = sorted `[root_id, head_id]` pairs of the fuel records read.
- Downgrade: refuse with `RuntimeError("0055 downgrade requires no fuel_balance_window rows")` if any row exists; else drop the trigger, index and table.
- The table is **not** a chain-event producer (`0044` `PRODUCERS` unchanged). K4 links its Finding to a window by `id`.

**Store (`B/fuel_balance/adapters/postgres_fuel_balance_store.py`), class `PostgresFuelBalanceStore(database_url, *, statement_timeout_ms=30_000, lock_timeout_ms=5_000, test_db_clock_override=None)`.**
- `test_db_clock_override` is the Work store's test-only seam (`B/work/adapters/postgres_work_store.py:281-291`): constructor-only; no HTTP field, environment variable or composition sets it.
- `assess_inputs(...)` and `append(...)` run in **one** transaction:
  1. `known_at` = `SELECT clock_timestamp()` (or the override), taken first;
  2. `pg_advisory_xact_lock(hashtext('fuel-balance:' || site_id || ':' || tank_asset_id || ':' || night_date))`;
  3. fuel records (`select_fuel_records(c, …)`), the tank and no-load-basis property query, the asset rows, the Site timezone;
  4. readings, SFC and r are read through `PostgresActionStore(database_url)` (`window_readings`, `sfc_history`, `no_load_history`), all with the same `known_at`. These reads are as-known filtered on append-only rows, so they need no shared snapshot;
  5. the latest revision for the night; insert `revision + 1` with `recorded_at = known_at` only when `input_sha256` differs, else return the latest (`appended=False`).
- A `known_at` earlier than the latest revision's `recorded_at` refuses `FUEL_BALANCE_CLOCK_BACKWARDS` (tests only can cause it).

**`input_sha256`** = `financials.fuel_cost.sha256_canonical({"parameter_version", "night_date", "window": [start, end], "tank_asset_id", "generator_asset_id", "accuracy": [value, basis, revision_id], "sfc": [value, revision_id], "no_load": [value, basis, revision_id], "evidence_ids": sorted, "records": sorted [root_id, head_id, recorded_at]})`. The result is a function of these inputs, so equal digests mean an equal result.

**Service (`B/fuel_balance/service.py`), `FuelBalanceService(store).assess_night(tenant_id, site_id, night_date) -> AssessResult(window: FuelBalanceWindow, appended: bool)`.**
1. Assets: the Site's one active `FUEL_TANK` and one active `GENERATOR` asset (`retired_at IS NULL`). Zero or several of either refuses `FUEL_BALANCE_ASSETS_UNSUPPORTED` (v1 is one tank, one generator; nothing written).
2. Window from `night_date` and the Site timezone (§9d.2).
3. `known_at < window_end + 30 min` refuses `FUEL_BALANCE_WINDOW_OPEN` (the closing search is not over; nothing written).
4. Inputs, `rules.assess(...)`, digest, append.
- Refusals are `FuelBalanceRefused(code, detail)`; the four codes above are the only ones.

**When it runs: explicitly, never by itself in v1.**
- CLI `B/fuel_balance/worker.py`: `python -m assetops_backend.fuel_balance.worker assess --site <code> --from <local date> --to <local date>` (nights `[from, to)`), using `DATABASE_URL`. One JSON line per night: `{"site_code", "night_date", "status": "APPENDED"|"REUSED"|"OPEN", "revision", "state", "reason"}`. `OPEN` (window not closed) continues; any other refusal exits 2 after printing it.
- **K7's prepare calls it** for Kisiwa after each story day's acceptance; K4 raises its Finding from the stored UNEXPLAINED window afterwards. K7's card names the instants.
- **No tick stage, no job domain, no HTTP route in K3.** The demo database is prepared, so the demo shows stored windows. After-the-demo list: "fuel-balance tick stage (assess each closed night automatically)". K5 adds its own read route.

### 9d.5 The read K4 and K6 use (`B/fuel_balance/model.py`)

```python
PARAMETER_VERSION = "fuel-balance-1/v1"
STATES = ("UNEXPLAINED", "BELOW_MATERIALITY", "WITHIN_MARGIN", "EXCESS", "NOT_ASSESSED")

@dataclass(frozen=True)
class FuelBalanceWindow:
    id: UUID
    tenant_id: UUID
    site_id: UUID
    tank_asset_id: UUID
    generator_asset_id: UUID
    night_date: date                 # Site-local date of the 18:00 start
    window_start: datetime           # UTC
    window_end: datetime             # UTC
    revision: int
    parameter_version: str
    recorded_at: datetime            # also the inputs' known_at
    state: str                       # one of STATES
    reason: str | None               # set iff NOT_ASSESSED
    residual_low: Fraction | None
    residual_high: Fraction | None
    gap_minutes: int
    gap_spans: tuple[tuple[datetime, datetime], ...]
    limitations: tuple[str, ...]
    terms: Mapping[str, Any]         # §9d.2 result terms, exact text
    evidence_ids: tuple[str, ...]
    record_ids: tuple[tuple[str, str], ...]
    input_sha256: str

class FuelBalanceReadPort(Protocol):
    def windows(self, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID,
                lo: date, hi: date, known_at: datetime) -> tuple[FuelBalanceWindow, ...]: ...
    def window(self, tenant_id: UUID, site_id: UUID, window_id: UUID) -> FuelBalanceWindow | None: ...
```
- `windows`: per `night_date` in `[lo, hi)`, the latest revision with `recorded_at <= known_at`, ordered by `night_date`. `lo < hi` and a UTC-aware `known_at`, else `ValueError("fuel balance windows need lo < hi and a UTC known_at")`.
- `window`: one stored revision by id, any `known_at` (K4's Finding and K6's baseline cite a fixed revision).
- `PostgresFuelBalanceStore` implements both, read-only, in one `REPEATABLE READ READ ONLY` transaction.

### 9d.6 Tests (localised only; no full suite)

**A. L0 `backend/tests/test_k3_fuel_balance_rules.py` (no DB).** Every "must fail" names the mutation the test kills; the reviewer applies each to a scratch copy.
1. **Parameters verbatim.** `PARAMETERS` minus `parameter_version` equals `.agent/DIESEL-F0/probe-result.json` `assumptions.fuel_balance_1` exactly. The constants equal F0's. `Fraction(fuel_cost_v2.MULTIPLIER) == USE_HIGH_FACTOR`.
2. **Rule parity, all 10 nights.** For each night, feed `probe-result.json` `nights[k].readings` terms (opening, closing, deliveries, `loaded_litres`, idle 0, gap) with a = 10, r = 49/10 into `rules.balance`. State, `residual_low`, `residual_high`, `use_low`, `use_high`, `opening_minus_closing`, D and D_tol equal the committed exact values. Repeat for `true_tank` terms.
3. **Idle term (§9c.3 L2 (b)).** An idle-only night: loaded 0, 24 slots RUNNING at 0 kWh (idle 7200 s, built from synthetic readings through the slot path), r = 49/10, O = 100, C = 35, no delivery. Expect `use_high == Fraction(539, 50)` (10.78), `use_low == 0`, `residual_low == Fraction(1711, 50)` (34.22), **BELOW_MATERIALITY**. Must fail if the idle term is dropped (it would give UNEXPLAINED at 45) or if r is a constant (re-run with r = 33/10 and assert `use_high == Fraction(363, 50)`).
4. **`residual_low == 0` edge.** loaded 40, idle 0, O = 500, C = 436, no delivery: `residual_low == 0`, `residual_high == 48`, **WITHIN_MARGIN**. Must fail with `<` for `<=`. Also: `residual_low == 40` exactly → UNEXPLAINED; `40 − 1/1000` → BELOW_MATERIALITY; `residual_high == 0` → WITHIN_MARGIN; `residual_high < 0` → EXCESS.
5. **Delivery night high edge, exact.** F0's night-2 readings terms (O = 656071667/1000000, C = 912643333/1000000, D = [300], loaded 26057/600): `residual_high == Fraction(13671417, 500000)`, `residual_low == Fraction(-41014249, 1500000)`, `D_tol == 3`. Two tickets 300 and 150: `D_tol == Fraction(9, 2)`. Must fail without `+ D_tol` in the high edge, or with its sign flipped.
6. **Use only from accepted generator readings (§9c.3 L2 (a)).** Synthetic 5-min readings: `loaded_litres == SFC × Σ kWh` exactly; one missing power slot → NOT_ASSESSED `GENERATOR_KWH_UNKNOWN`; one missing state sample → `IDLE_SECONDS_UNKNOWN`; one non-GOOD power reading → `GENERATOR_KWH_UNKNOWN`. **A2 parity:** over one UTC hour of the same readings, K3's kWh and idle seconds equal `verification_rules.window_evidence(...)["generator_kwh"]` and `["generator_idle_seconds"]`. **Static test:** no module under `B/fuel_balance/` imports `assetops_simulator`, `host`, `tools`, `assetops_backend.runs`, or contains the word `trajectory`.
7. **Opening and closing.** A reading at exactly `start` is the opening; at `start − 30 min` counted, at `start − 31 min` not; at `end` and `end + 30 min` counted, `end + 31 min` not; the last-in-range opening and first-in-range closing are chosen; MISSING_OPENING, MISSING_CLOSING; two different values at the chosen instant → FUEL_LEVEL_CONFLICT; a non-GOOD reading is ignored.
8. **Gap.** Spans of 60 min → 0; 61 → 61; edges included; night-4-shaped readings (00:45 and 02:30 local) → 105 and the one span.
9. **Reason precedence** 1–8, each with all later reasons also present.
10. **Limitations.** DIP_SENSOR_CONFLICT at `|Δ| = a + 10` → absent, `a + 10 + 1/1000` → present; a dip with no reading within 30 min → absent. DELIVERY_RECORDED_LATE at `root_recorded_at = end + 30 min` → absent, `+ 1 s` → present. Fixed order.
11. **Window.** `Africa/Dar_es_Salaam` night `2026-10-04` → `[2026-10-04T15:00Z, 2026-10-05T09:00Z)`, 216 slots; a zone with a DST gap at 18:00 → `FUEL_BALANCE_WINDOW_INVALID`.
12. **Digest.** Equal inputs → equal `input_sha256`; one extra evidence id → different.

**B. L2 `backend/tests/test_k3_fuel_balance_postgres.py`, own `assetops_k3_test`** (Kobo imported as K2's L2 does, `test_s1_bindings_postgres.imported`; `VirtualDbClock` as W401).
1. Migration up/down/up on an empty table (exact constraint text, columns, index, trigger); downgrade refused with a row; single alembic head; UPDATE and DELETE refused by the trigger; a raw insert violating each CHECK (NOT_ASSESSED without reason; `recorded_at < window_end + 30 min`; a band on NOT_ASSESSED) fails.
2. **K2 L1, kind change.** On Kobo's tank: a TANK_DIP at T0, corrected at T1 to OPERATOR_LOG ("not a dip"). `fuel_records(known_at < T1)` contains it with kind TANK_DIP; `known_at >= T1` does not.
3. **K2 L1, tank change.** A second Site imported from `C/site-templates/twin-tank-mini-grid-150kw.yaml` (`site_from_template` + `import_site` on `PostgresFoundationStore`, K1's `register_in` step 1 pattern; PRE-FLIGHT (b)). A TANK_DIP on `north-tank` at T0, corrected at T1 to `south-tank`. North before T1: present; north after: absent; south before: absent; south after: present.
4. **Cross-kind correction (§9d.3).** On Kobo's tank: an OPERATOR_LOG "Fuel delivery of 300 L received, ticket KIS-DT-0001." at T0 (on time), corrected at T1 (after the window's `end + 30 min`) into a FUEL_DELIVERY of 300 L on the tank with a ticket digest. Absent before T1; after T1 present with `kind == "FUEL_DELIVERY"`, the root's `code`, `root_recorded_at == T0`; K3's rules on that record give **no** `DELIVERY_RECORDED_LATE`. Converse: a FUEL_DELIVERY root first recorded at `end + 31 min` gives the limitation.
   - Mutation check (reviewer, scratch copy of `postgres_fuel_records.py:33`): root kind only → B4 fails; root tank only → B3 fails; both → B2 fails.
5. **Kobo is NOT_ASSESSED.** `assess_night` for a Kobo night → stored NOT_ASSESSED `NO_SENSOR_ACCURACY`. No Kobo file changes (`git diff --stat main` lists none).
6. **Store.** `FUEL_BALANCE_WINDOW_OPEN` before `end + 30 min` writes nothing; equal inputs → `appended=False`, same id; `FUEL_BALANCE_CLOCK_BACKWARDS`; a Site with two FUEL_TANKs (the twin-tank Site) → `FUEL_BALANCE_ASSETS_UNSUPPORTED`; `windows()` argument checks.

**C. L2 parity `host/tests/test_k3_fuel_balance_parity.py`, own `assetops_k3_test`. Needs K1 merged.**
- Module fixture: `pg_harness.fresh_database()`; `demo_combined_kisiwa.register(URL, work, 2026-09-29T09:00Z, 2026-09-29T09:30Z)` (K1's flow: accuracy 10 L GENERIC_DEFAULT, no-load 4.9 L/h, SFC 0.355).
- **Nights 2, 4 and 6** (delivery, incident, after-phase dips). For each `k`:
  - start state = `float(Fraction(ref["runs"][k-1]["start"]["soc"]))`, likewise fuel (the probe's own chaining); document `probe_kisiwa_nights.day_document(soc, fuel)`;
  - draft through `KisiwaRegistered(store, "2026-09-29T11:00:00Z").draft(document, run k start, run k end)` (product v7, v5);
  - apply the F0 actions with **`probe_kisiwa_fuel.apply_actions(run, probe_kisiwa_fuel.load_actions(), run_start)`** (K0 is not merged; this is F0's hook, unchanged). Assert the returned history equals `ref["runs"][k-1]["intervention_history"]`;
  - publish and accept with `test_s6_verification_replay._publish_and_accept(tmp, run, f"epoch-{k}", run_end + 10 min)`;
  - assert the run's end tank and SOC equal `ref["runs"][k-1]["end"]` (physics guard).
- Records through `WorkService.post_operational_record` (K2), `PostgresWorkStore(test_db_clock_override=…)`, actor and fixtures as K2's L2:
  - night 2: K2's FUEL_DELIVERY example body verbatim (§9c.2), `occurred_at 2026-10-03T07:00:00Z`, recorded `07:30:00Z`, ticket digest = sha256 of the ASCII text `Fuel delivery ticket KIS-DT-0001, 300 L` (test literal);
  - dips, recorded 15 min after: night 4 `"Tank dip at the 07:00 round: 706 L."` at `2026-10-05T04:00:00Z`; night 6 663 L at `2026-10-06T15:00:00Z` (18:00 round) and 619 L at `2026-10-07T03:00:00Z` (06:00 round), values from `ref["dips"]`.
- Assess each night with the store clock at `run_end + 30 min`. Compare with `ref["nights"][k-1]["readings"]`:
  - **exact:** `state`, `reason` None, `gap_minutes`, opening and closing (`opening_reading_l.exact`, `closing_reading_l.exact`), D, D_tol;
  - **within 1/100000 L:** `loaded_litres`, `use_low`, `use_high`, `residual_low`, `residual_high`. Reason: generator power is published at 0.000001 kW resolution; over 216 slots that bounds the use error below 4 × 10⁻⁶ L. Print each term's |Δ|;
  - `idle_seconds == 0` on all three nights;
  - night 4: `gap_spans == ((2026-10-04T21:45Z, 2026-10-04T23:30Z),)`, `limitations == ("REPORTING_GAP",)`; nights 2 and 6: `()` (no dip conflict, delivery on time);
  - **independent use check (L2 (a)):** night 4's `generator_kwh` equals a test-side SQL sum over `accepted_evidence` of `generator_power` value × 5/60 h in the window, exactly.
- **As known.** Night 4 assessed first at `2026-10-05T09:45Z`, before acceptance (`12:10Z`): revision 1, NOT_ASSESSED `MISSING_OPENING`. Then at `12:30Z`: revision 2, UNEXPLAINED. `windows(known_at=10:00Z)` returns revision 1; at `12:30Z` revision 2; `window(id of revision 1)` returns revision 1.
- CLI once: `worker assess --site KISIWA-001 --from 2026-10-06 --to 2026-10-07` → one line, `REUSED`.
- Machine time about 12–18 min (three gateway days, as K1's one day at 3–5 min).
- **Packet evidence (§9c.3 L2 (c)):** "Kisiwa has 0 idle minutes on every night (F0 and these three nights), so on Kisiwa's own nights the idle × 4.9 L/h term is exercised only by test A3." All 10 nights are reproduced from stored windows in K7's KIS-3.

**Existing tests that must stay green unchanged:** `test_k2_fuel_records.py`, `test_k2_fuel_records_postgres.py`, `test_w401_work_service_postgres.py`, the single-alembic-head test, `test_fuel_cost_v2.py`, the A2 verification-rules tests, `host/tests/test_k1_registered_kisiwa.py`, and both probe `--check`s ("probe result current"). A test that only counts migrations, tables or indexes may take the new head and objects (K2's `INDEX_TOTAL` precedent); any behaviour edit is a stop.

**Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` if the worktree has no venv), `tools\check-agent-workflow.ps1`, `tools\check-navigation-truthfulness.ps1`, run directly, no `-ExecutionPolicy`. Allowlist joins (rule-8 `$pgReaders` for the new adapter, as K2) are listed in the packet with the reason; membership only, never a loosened rule.

### 9d.7 Files

| # | File | Content |
|---|---|---|
| 1 | `backend/migrations/versions/0055_fuel_balance_window.py` | §9d.4 |
| 2 | `B/fuel_balance/__init__.py` | empty |
| 3 | `B/fuel_balance/rules.py` | §9d.2: `PARAMETERS`, constants, `night_window`, `opening_closing`, `use_from_readings`, `reporting_gap`, `balance`, `limitations`, `assess`, `input_sha256` |
| 4 | `B/fuel_balance/model.py` | §9d.5, `FuelBalanceRefused`, the codes |
| 5 | `B/fuel_balance/service.py` | §9d.4 service |
| 6 | `B/fuel_balance/adapters/__init__.py`, `postgres_fuel_balance_store.py` | store and read port |
| 7 | `B/fuel_balance/worker.py` | CLI |
| 8 | the three test files of §9d.6 | |
| 9 | guard allowlists, only as PRE-FLIGHT (c) names | membership |

### 9d.8 PRE-FLIGHT (no code first; batch every question in one message)

- (a) Confirm, with file:line, that `test_s6_verification_replay._publish_and_accept` executes the **passed** in-memory run (with `apply_actions`' added frozen causes and reporting condition) and that `run_attestation` and `register_run` accept it. If either re-reads the run from a store or refuses, that is a stop (S2 below).
- (b) Confirm that importing the twin-tank template creates two active `FUEL_TANK` asset rows, and name the calls.
- (c) Name every guard list, allowlist and catalogue-count test the new package, adapter, table, index and trigger must join, and confirm the table needs no chain-producer classification.
- (d) From K1's L2 printout, the `measurement`, `source_time`, `interval_start` and `interval_end` of Kisiwa's accepted `fuel_level`, `generator_power` and `generator_state` rows (confirms the slot rule applies as written).
- (e) The call that gives the Site's timezone and its asset rows inside one transaction.

### 9d.9 Stops (report to the Architect; never design around them)

- **S1** any parity item of C differs (an exact item, or a toleranced term beyond 1/100000 L): report the night, the term and both values. Never edit `probe-result.json`, the probe, the parameters or the tolerance.
- **S2** the action-applied run cannot be published and accepted through `_publish_and_accept` (PRE-FLIGHT (a)). Report verbatim; never write a scenario entry (OA-1).
- **S3** a Kisiwa night in C has an UNKNOWN generator slot (power or state). Report it; never relax A2's slot rule.
- **S4** a need to edit `B/actions/verification_rules.py`, `B/actions/adapters/postgres_action_store.py`, `B/work/`, `B/financials/`, `B/mini_depth/`, `contracts/`, `B/runs/`, any Kobo, Cold or EV file, either probe or its result.
- **S5** an existing test in §9d.6 needs a behaviour change.
- **S6** PRE-FLIGHT (b) fails (no two FUEL_TANK assets). The Architect rules on B3.
- **S7** more than 1.9 units.

### 9d.10 Dependencies, start, branch, size and date

- **Depends on:** K2 merged (yes, `5d8ac9ee3`), A2 merged (yes), K1a merged (yes), and **K1 merged for part C only** (the `register` flow, `host/tests/kisiwa.py` and the accuracy vocabulary). K3 never merges before K1.
- **It can start before K1 merges, in two phases:**
  - **Phase A, now (about 1.1):** pre-flight, rules and A1–A12, migration, store, read, service, CLI, and B1–B6. None needs K1: the accuracy property key is a literal (§9c.1), and B runs on Kobo and the twin-tank Site.
  - **Phase B, after K1 merges (about 0.5):** merge main, then part C and the packet.
  - A builder free now takes phase A. If none is free, K3 starts on lane 3 when K1 merges, as §9.5 planned. K1 is at its review packet, so the overlap gained is at most about half a unit.
- **Branch** `task/DIESEL-K3-fuel-balance`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k3`, from main at or after `5d8ac9ee3`. Opus does the first build and the first review. Commit with `git add -f` of explicit paths.
- **DB:** only `assetops_k3_test` (and its harness clones). Never `assetops_demo3_full_test` or any other DB. No prepare, tick, `serve` or suite. Run part C when the machine is idle (free RAM checked first).
- **Size: 1.6** (range 1.4–1.9), +0.1 against §9.5's 1.5:
  - rules and L0 0.4; migration, store and read 0.3; service, inputs and CLI 0.3; B (K2 L1, cross-kind, twin-tank) 0.25; C parity 0.3; pre-flight 0.05.
  - The +0.1 is K2's L1 and residual-risk tests and the readings-based parity that F0 did not have. It is paid from the remaining contingency (0.25 → 0.15), so the Kisiwa total stays **17.25**.
- **Critical path:** F0r 0.65 → K1 1.25 → K3 1.6 → K4 2.0 → K6 1.5 → K7 freeze 0.5 → K8 captures 0.25 → K9 1.0 ≈ **8.75 lane-units** (8.65 before), or about 8.25–8.5 if phase A overlaps K1. **Below the 9.75 tripwire; no cut.**
- **Demo date: unchanged at about +3.25 working days** (range 2.75–5.25).
- **Plan HTML rows (coordinator):** the DIESEL-1-R3 build-units row keeps 17.25 with K3 1.6 and contingency 0.4; rulings table gains "DIESEL-1-R3d: K3 card (fuel-balance-1 from accepted readings, 0055, explicit assess, cross-kind lateness from the first recording)"; after-the-demo list gains "fuel-balance tick stage" and "fuel_records read uses the asset index".

**Reading budget:** this §9d; §8.3's `fuel-balance-1` block; `T/probe_kisiwa_fuel.py:56-135`, `:600-640`; `.agent/DIESEL-F0/probe-result.json` (`assumptions.fuel_balance_1`, `runs`, `nights`, `dips`); `B/actions/verification_rules.py:1-120`, `:170-340`, `:370-548`; `B/actions/verification.py:643-670`; `B/actions/adapters/postgres_action_store.py:590-670`; `B/financials/trial_fuel_comparison.py:40-105`; `B/financials/fuel_cost_v2.py:1-80`; `B/work/fuel_records.py`; `B/work/adapters/postgres_fuel_records.py`; `B/work/adapters/postgres_work_store.py:1-12`, `:281-320`; `B/mini_depth/inputs.py:55-80`; `backend/migrations/versions/0054_operational_fuel_records.py` (pattern); `backend/tests/test_k2_fuel_records_postgres.py`; `host/tests/test_s6_verification_replay.py:88-260`; K1's `host/tests/kisiwa.py`, `T/demo_combined_kisiwa.py` and `backend/tests/test_k1_kisiwa_site_postgres.py` (after K1 merges).

### 9d.11 Owner questions

None.

---

## 9e. Ruling DIESEL-1-R3e: F0 evidence line endings (K1 review L1)

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `da51c7a8a`. Source: L1 in `.agent/review-K1.md` on `task/DIESEL-K1-kisiwa-site` at `5218fba34`.
- **What the Architect verified on this checkout** (`core.autocrlf=true`; `git ls-files --eol` gives `i/lf w/crlf` for all five files under `.agent/DIESEL-F0/` and `.agent/DIESEL-D0/`):
  - `T/probe_kisiwa_nights.py --check` prints "probe result current (G6 pass)".
  - `T/probe_kisiwa_fuel.py --check` prints "probe result differs from the committed file".
  - A field-by-field diff of a fresh seeded `build()` against the committed F0 JSON shows **exactly two differences**: `assumptions.actions_sha256` and `assumptions.registered_path.bindings_sha256`. Both are working-copy CRLF hashes against committed LF hashes. Every litre, band, state, gap, dip, count and gate value is equal.
  - When each input is hashed after normalising it to LF (`read_text(encoding="utf-8").encode("utf-8")`), the hashes are actions `77777c82…`, bindings `68a54ef8…` and D0 template `261b7e64…414b`. None of the three files contains a lone CR.
- **D0 has no exposure.** `T/probe_kisiwa_nights.py:466-467` already hashes the template LF-normalised (`template_sha256_lf`). Its `--check` (`:506`) compares `read_text` output, which normalises line endings. D0's committed result already pins `template_sha256_lf = 261b7e642aa7e2f3a2d5175868cf7b2a406b2c89154b1229ca78424e65a6414b`, so the value F0 is re-pinned to is one D0 pre-registered independently. No D0 file is edited.

### 9e.1 Decision: the correction happens, as unit F0e

1. **Probe (`T/probe_kisiwa_fuel.py`, the only code edit).**
   - Add `def _sha256_lf(path): return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()`. This is D0's pattern (`probe_kisiwa_nights.py:466-467`).
   - Use it at `:698` (`d0_template_sha256`), `:699` (`actions_sha256`) and `:708` (`bindings_sha256`).
   - Key names stay as they are. Renaming them would move more of the pre-registered file than this fix needs.
   - `IMPORT_PATH`'s payload hash (`:261-262`) is canonical YAML and stays untouched.
2. **Re-pin by `--write`, never by hand.** The only line `git diff .agent/DIESEL-F0/probe-result.json` may show is `d0_template_sha256`, changing from `d9a4107a…aa11` to `261b7e642aa7e2f3a2d5175868cf7b2a406b2c89154b1229ca78424e65a6414b`. Any other changed line is a stop.
3. **`.gitattributes`**, appended after the PERF-01 lines:
   ```
   # DIESEL-1-R3e: Kisiwa probe evidence (pre-registered inputs and committed results) is LF on every host
   .agent/DIESEL-F0/* text eol=lf
   .agent/DIESEL-D0/* text eol=lf
   ```
   - **No renormalise commit is needed.** The index already holds LF for all five files. Proof: `git add --renormalize .agent/DIESEL-F0 .agent/DIESEL-D0`, after which `git diff --cached --name-only` lists none of them except the intentionally edited `probe-result.json`.
   - The rule is belt and braces. After item 1, both `--check`s are independent of checkout line endings. The rule makes the working-copy bytes equal the blob bytes, so a plain `sha256sum` by any reviewer matches the pins.
4. **Evidence note.** Append a section "Evidence correction (DIESEL-1-R3e)" to `.agent/DIESEL-F0-probe-results.md`. It records the cause (a mixed CRLF and LF reference), the one re-pinned value with its old and new hashes, the fact that it equals D0's `template_sha256_lf`, and the proof outputs of §9e.3. The section uses plain words and changes no earlier text.
5. **K1's monkeypatch** (`host/tests/test_k1_registered_kisiwa.py:94-101`, the `Path.read_bytes` patch and its comment) is removed. After item 1 the probe no longer calls `read_bytes` on those files, so the patch is inert, and leaving it would misstate why the parity test holds. See §9e.2 for who removes it.

**Why this re-pin is admissible under §9.4's evidence integrity:** the value re-pinned is an *input identity*, not a measurement. The proof shows the following:
- the probe's parse of each file (`yaml.safe_load` and `json.loads` over `read_text`) is line-ending-blind;
- the per-action `content_sha256` is over canonical JSON;
- the field diff in §9e.3 (c) shows every measured value byte-equal.

The new value was not computed to make a check pass. It is the LF blob hash and equals D0's independently committed pin. This is the F8 precedent (§9b item 1): the evidence changes where an identity was taken carelessly, and the measurement does not move.

### 9e.2 Who and when

- **A separate unit, F0e, now. Not folded into K3.** K3's S4 forbids it to edit either probe or its result, and K3 phase A is in build. Folding this in would mean re-carding a running builder. F0e touches no K3 file.
- **Builder:** Sonnet, a fix-round class job (mechanical, like F8). Branch `task/DIESEL-F0e-probe-eol`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-f0e`, from main at or after `da51c7a8a`. Files: `T/probe_kisiwa_fuel.py`, `.agent/DIESEL-F0/probe-result.json`, `.gitattributes`, `.agent/DIESEL-F0-probe-results.md`, plus `host/tests/test_k1_registered_kisiwa.py` only in case (b) below. Commit with `git add -f` of those explicit paths.
- **Verification:** the coordinator runs the §9e.3 mechanical checks. There is no reviewer judgement and no separate review, as with F8. Merge when every check passes.
- **Sequencing with K1 (K1 is on the critical path; F0e never blocks it):**
  - **(a) F0e merges before K1 is merge-ready (expected).** K1's fix round merges main and deletes the monkeypatch. Its own L2 run of `test_f0r_reproduces_on_the_registered_site` on `assetops_k1_test` is the proof. K1's reviewer or the coordinator confirms that the test passes with no patch.
  - **(b) K1 merges first.** K1 merges with the monkeypatch, which is correct on this checkout and accepted by its reviewer. F0e then merges main, deletes the monkeypatch and runs that one test once on `assetops_k1_test` (an authorised test DB; machine idle; no suite).
  - Rule: **the unit that merges second removes the monkeypatch.**
- **Hard deadline:** F0e merges **before K3 phase B**. K3 §9d.6 requires both `--check`s to print "probe result current", and on main today the F0 check cannot pass on any checkout. F0e also merges before K7 and before any Linux or container run of either probe. K3 §9d.10 gains this dependency. Phase A is unaffected.

### 9e.3 Proof steps (each output pasted into the evidence section)

Run with `PYTHONPATH` set to the worktree's `simulator;backend;contracts;host`. The plan2 `.venv` is installed editable against another checkout. Without this, the probes import the wrong tree and fail with `ImportError`. That failure is not a probe result.

- **(a) Before (CRLF, F0e worktree, before any edit).** D0 `--check` is current. F0 `--check` "differs", which records the defect.
- **(b) After, CRLF working copies.** Apply items 1–3, run `--write` once, then run each `--check` in a fresh process, twice. Both print current. This is done before any re-checkout, so the evidence files are still CRLF on disk.
- **(c) Field diff.** A scratch script compares the new committed JSON with `git show main:.agent/DIESEL-F0/probe-result.json` field by field. Exactly one path differs: `assumptions.d0_template_sha256`. `git diff --stat` shows one line changed in that file and no change to any `.agent/DIESEL-D0/` file.
- **(d) After, LF.** Run `git -c core.autocrlf=false archive HEAD | tar -x` into a scratch directory, and confirm with `git ls-files --eol` or a byte check that the five evidence files have no CR. Run both `--check`s there with `PYTHONPATH` pointing at the extracted tree. Both print current. This is the Linux or fresh-clone case.
- **(e) After re-checkout in the worktree.** Delete the five evidence files and run `git checkout -- .agent/DIESEL-F0 .agent/DIESEL-D0`. They come back LF (`w/lf`). Run both `--check`s; both print current. Run `git status`; the tree is clean.
- **(f) Renormalise.** Run `git add --renormalize .agent/DIESEL-F0 .agent/DIESEL-D0`. Nothing is staged beyond the intended commit.
- **(g) Band test.** `host/tests/test_probe_kisiwa_fuel_band.py` (no DB) passes unchanged.
- **(h) Case (b) only.** The single K1 parity test passes without the monkeypatch.

**Stops:**
- (c) shows any second changed path;
- any `--check` fails in (b), (d) or (e);
- a lone CR or a non-UTF-8 byte is found in an input;
- any D0 file would change.

On a stop, the builder reports it and never adjusts a value by hand.

### 9e.4 Size

- **F0e: 0.1** (range 0.1–0.15): code and re-pin 0.03; the proof matrix 0.05; the evidence note 0.02. Case (b)'s one L2 test run adds about 0.03 if it happens.
- Paid from contingency, 0.15 → 0.05. **The Kisiwa total stays 17.25.**
- F0e is off the critical path: it runs in parallel now and only gates K3 phase B, which is at least half a unit away. The critical path is still about **8.75 lane-units**, below the 9.75 tripwire. **The demo date is unchanged** at about +3.25 working days.
- After-the-demo list: none.

### 9e.5 Owner questions

None. For the owner, in plain words: one fingerprint in the fuel trial's record was taken from a Windows copy of a file instead of the stored copy, so the check failed on other machines. We fix how the fingerprint is taken. No measured fuel number changes.

---

## 9f. Ruling DIESEL-1-R3f: K0 pre-flight (Q1–Q10)

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `1fc354bee` (K1 merged). K0 worktree `C:\Users\assef\Bineyame\AssetOpsV1-k0`, branch `task/DIESEL-K0-action-bridge`, read clean at `1fc354bee`.
- **K0's card is §9.3 + §9c.3 items 1 and 4 + this section. Where they differ, §9f wins.** The main amendment: the origin fields live on the backend frozen records only. The kernel-facing contract, the host and the trajectory identity are **not** edited (Q1, Q2, Q4).
- Owner decision in force, verbatim: `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions").

**Code facts the Architect verified on the K0 worktree:**
- `B/runs/source_publication.py:27-33`: `run_identity_sha256` hashes `render_run_document(run)`'s `run_id`, `created_at`, `deterministic_identity` and `registered_basis`. Any render change to the identity moves the Postgres `evidence_publication` digest, so the omit rule is load-bearing there too.
- `B/runs/parsing.py:773-777` (`FrozenForcing.issued_by`) and `:874-888` (`signal_resolutions`, with its parse at `:1427-1442` refusing a stored empty list) are the two omit-when-default precedents. §9f uses both.
- `contracts/assetops_contracts/trajectory.py:570-589`: causes are hashed as 11-tuples, `intervention_history` is hashed, and reporting conditions are not (`IDENTITY_FIELDS_READ` at `:639-662` is per `FrozenWorldInputs` field).
- `contracts/assetops_contracts/observation.py:475-493`: `ReportingPathWindow` is a per-signal projection of a condition, not its counterpart.
- `B/runs/provenance.py:434-536`: provenance reads only the `DeterministicIdentity`, with every cause and condition row hard-coded `answered_by="SCENARIO"`.
- `B/runs/models.py:193-201` `FROZEN_INPUT_ANSWERERS` has no `OPERATIONAL_ACTION` member.
- `B/runs/service.py:464-491`: `_freeze`, then `signal_resolutions`, then `_decide`. `_decide` (`:1824-1870`) reads causes and conditions from the scenario, not the identity. `_cadence_reasons` and `_publication_reasons` ignore causes and conditions.
- `B/runs/refusals.py:111-154` holds the kinds. `backend/tests/test_run_setup.py:2091` asserts `produced == RUN_SETUP_REFUSAL_KINDS`, so every new kind needs a producer in that test. `F/shell/RunSetupFrame.tsx:1387` returns `null` for an unknown kind, which shows the backend message, so no frontend edit is needed.
- `backend/tests/test_run_setup.py:1600-1760` classifies every frozen-record field as rendered or `not_rendered` (with a reason). New fields must be classified there.
- `B/simulator_lab_api.py:2460-2467` composes `RunSetupService`, and the Lab identity wire at `:2250-2305` carries no causes. Neither the wire nor the frontend changes.
- `.agent/DIESEL-F0/probe-result.json:8` has `actions_sha256 = 77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634`. At `:2852-2858`, run 2's non-generator step is `step 227, offset 1135, -300`.

### 9f.1 Rulings

**Q1. Approved: no contract class change for conditions.**
- `ReportingPathWindow` stays as it is.
- `origin` and `action_ref` go on `B/runs/models.py` `FrozenReportingPathCondition` only.

**Q2. Corrected: `DeclaredCause` is not changed either, and the host is not edited.** This amends §9.3 item 1, which listed `DeclaredCause`, and confirms §9.3 item 6, "host: no change".
- Origin is provenance. The kernel boundary carries physics.
- The world identity already tells an action cause apart from a scenario cause by two hashed facts:
  - its `event_id` (`"{action_id}/{effect}"`);
  - its `intervention_history` entry, which carries the action's content hash.
- Adding the fields to `DeclaredCause` would either be dead weight (the host does not pass them) or change `frozen_inputs_identity` (the host does pass them). It buys no test and adds a hash risk.
- Files therefore **not** edited: `contracts/assetops_contracts/world_inputs.py`, `contracts/assetops_contracts/trajectory.py`, `contracts/assetops_contracts/observation.py`, `host/execution_adapter.py`, `S/**`. Any need to edit one of them is stop S2.

**Q3. Approved, with the shape below.**
- The identity freezes the log and the effect-bearing actions' display facts.
- Provenance reads only the frozen identity, never the live log.
- Shape: §9f.2 (2).

**Q4. Approved: not in the trajectory hash.**
- The log identity and the per-action tuple are in the run document. So they are in `run_identity_sha256` and in the stored bytes.
- They are not in `frozen_inputs_identity`.
- Same world means the same trajectory identity:
  - Two logs with identical effect-bearing actions give the same world.
  - Any change to an action's content changes its `content_sha256`, so it changes `intervention_history` and the trajectory identity.

**Q5. Approved.**
- `intervention_history` and `operational_action_log.actions` hold the **effect-bearing** actions only: `FUEL_DELIVERY`, and `FUEL_REMOVAL_UNRECORDED`.
- They hold only actions selected for this run (`at` in `[start_time, end_time)`).
- Order: by parsed `at` instant, then `action_id` (code-point order).
- The two lists correspond 1:1 in the same order.
- `TANK_DIP`, `TANK_SEALED` and `SENSOR_POWER_PROTECTED` are validated (§9f.3) but freeze nothing.

**Q6. Approved: refuse, never clip.**
- Code: `OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN`.
- It applies to any selected action whose physical span does not lie wholly inside `[start_time, end_time)`:
  - the removal window `[at, at + duration_minutes)`;
  - the sensor span `[sensor_disconnected.at, sensor_disconnected.at + duration_minutes)`.
- The sensor span may start before the action's `at`, as in F0 (`21:50Z` against `22:00Z`), but it must start at or after `start_time`.
- Offsets must also meet the alignment rule the existing setup applies to scenario entries (`_refuse_entries_outside_the_interval`). The builder mirrors that rule exactly, under this code.
- An `at` with non-zero seconds is refused under this code too.

**Q7. Approved, narrowed to the registered timeline path.**
- `operational_actions` is accepted only on the timeline `_freeze` path **with a registered selection** (`selection is not None`).
- It is refused with `OPERATIONAL_ACTIONS_UNSUPPORTED_PATH` in three places:
  - on the cold document draft (`_create_cold_draft`);
  - on the EV document draft (`_create_ev_draft`);
  - on a legacy YAML Site (no selection).
- Refusal happens before any freeze work. Nothing is allocated.
- The key is added to the shared `REQUEST_KEYS` (`B/runs/parsing.py:109`). The text of the `REQUEST_INVALID` message that lists the keys grows by one name. Tests that pin that whole message are updated, and this is the only permitted change to existing test expectations.

**Q8. Approved, all four items.**
- An `operational_actions` port on `RunSetupService`.
- `build_simulator_lab_router` and `main.py` pass the file adapter.
- The `host/tests/kisiwa.py` port.
- The default path constant lives in the adapter module only.
- Signatures: §9f.2 (6). The `LabRunner` harness named in §9.3 item 5 is replaced by `host/tests/kisiwa.py`, which K7 uses.

**Q9. Approved.**
- `.gitattributes` gets `config/operational-actions/* text eol=lf` (block in §9f.2 (7)).
- The frozen `sha256` is the LF hash, and it must equal F0's `actions_sha256` (`77777c82…b634`). Inequality is stop S4.
- The stale header comment stays verbatim. It says "DRAFT" and "promotes it verbatim to `config/operational-actions/kisiwa-001-v1.yaml`". The adapter module docstring and the packet each state, in one sentence, that the file is F0's pre-registered draft promoted byte-for-byte and that its header predates §9c.3 L1's file name.

**Q10. Approved, with one addition.**
- The pins are committed **as the branch's first commit**, before any production edit. Git history then proves they predate the change.
- Pins are a new test-data module `backend/tests/k0_byte_equal_pins.py` with literal hex strings, taken from the existing no-DB fixtures:
  - the Kobo draft (`host/tests/kobo.py:108`);
  - one Cold lab draft and one EV lab draft;
  - every shipped scenario's frozen-cause render.
- For each, pin three sha256 values:
  - (a) `json.dumps(render_run_document(run), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)`;
  - (b) `run_identity_sha256(run)`;
  - (c) the trajectory identity digest (`frozen_inputs_identity` over the host's `frozen_world_inputs(run)`), for each run the host can build world inputs for.
- `run_id` and `created_at` are fixed by the fixtures' seeded and clocked setup. If a fixture is not deterministic across two fresh processes, pin it after removing exactly `run_id` and `created_at`, and say so in the packet.
- Cold and EV have no timeline world inputs, so for them (c) is "not applicable", stated.

**Builder-resolved items, ruled:**
- `CAUSE_ORIGIN_INVALID` for both causes and conditions: **confirmed**. Mechanism in §9f.2 (1).
- `OPERATIONAL_ACTION_LOG_MISMATCH` for an inner id or version that differs from the file name: **confirmed**. It also covers an inner `site_code` that differs from the request's `site_id`.
- In-memory tank parity: **confirmed, read from evidence, not literals.**
  - Run 4 is steps 120–128, 40/3 L each (120 L over 45 min).
  - For run 2, the expected step, offset and litres are read from `probe-result.json` `non_generator_steps`. That is step 227 at offset 1135, −300 in the evidence's sign. It is not typed into the test.
- DB tests on `assetops_k0_test` only: **confirmed.**

### 9f.2 Exact specification

**(1) Frozen records (`B/runs/models.py`).**
- `FrozenCause` and `FrozenReportingPathCondition` each gain two fields, after their existing fields and with defaults:
  - `origin: str = "SCENARIO"`;
  - `action_ref: str | None = None`.
- `CAUSE_ORIGINS = frozenset({"SCENARIO", "OPERATIONAL_ACTION"})`.
- `ACTION_REF_PATTERN = r"^[a-z0-9][a-z0-9-]{0,63}:[0-9a-f]{64}$"`, which is `"{action_id}:{content_sha256}"`.
- `__post_init__` raises `ValueError` with a message starting `"CAUSE_ORIGIN_INVALID: "` in these cases:
  - origin not in `CAUSE_ORIGINS`;
  - `OPERATIONAL_ACTION` with `action_ref` None;
  - `SCENARIO` with `action_ref` not None;
  - an `action_ref` that does not match the pattern.
- New `FrozenOperationalAction(action_id: str, kind: str, actor: str, at: str, content_sha256: str)`.
  - `kind` is one of `FUEL_DELIVERY` or `FUEL_REMOVAL_UNRECORDED`.
  - `at` is the log's text, verbatim.
- New `FrozenOperationalActionLog(log_id: str, log_version: int, sha256: str, actions: tuple[FrozenOperationalAction, ...])`. `actions` may be empty: a requested log with no effect-bearing action in the interval.
- `DeterministicIdentity` gains `operational_action_log: FrozenOperationalActionLog | None = None`, last, with a default.
- `FROZEN_INPUT_ANSWERERS` gains `"OPERATIONAL_ACTION"`.
- Update the `DeterministicIdentity` docstring sentence that says `intervention_history` is always empty: it is empty unless the run names an operational-action log.

**(2) Render (`B/runs/parsing.py` `render_run_document`).**
- **Cause.** Append `"origin": "OPERATIONAL_ACTION", "action_ref": item.action_ref` to the existing cause dict **only when** `item.origin == "OPERATIONAL_ACTION"`. Use the `**({…} if … else {})` pattern from `:773-777`. A scenario cause renders exactly today's keys.
- **Condition.** The same, for each reporting-path condition.
- **Identity.** Append `"operational_action_log"` only when it is not None:
  `{"log_id", "log_version", "sha256", "actions": [{"action_id", "kind", "actor", "at", "content_sha256"}, …]}`.
  Use the `signal_resolutions` pattern (`:874-888`). Here, unlike there, an empty `actions` list **is** written, because the log was requested.

**(3) Parse (`B/runs/parsing.py`).**
- Strict, mirroring render. Every error is `RunConfigurationInvalid`, and an origin-family error message starts `"CAUSE_ORIGIN_INVALID: "`.
- Cause or condition:
  - `origin` absent means `SCENARIO` with `action_ref` None.
  - `origin` present must be exactly `"OPERATIONAL_ACTION"` and must have `action_ref`. An explicitly written `"SCENARIO"` is refused, because the writer never writes it. That keeps one stored form per record.
  - `action_ref` without `origin` is refused.
- `operational_action_log`: absent means None. Present means every key is required with the right type, and unknown keys are refused.
- **Cross-check, after the whole identity is parsed.** These must hold together:
  - the `intervention_history` entries starting `"OPERATIONAL_ACTION:"` equal, in order, `["OPERATIONAL_ACTION:" + a.action_id + ":" + a.content_sha256 for a in log.actions]`, and there are none when the log is absent;
  - every `action_ref` on a cause or condition names an action in `log.actions`;
  - every action in `log.actions` is named by at least one cause.
- Any break of the cross-check is `CAUSE_ORIGIN_INVALID`.
- The same cross-check runs in `operational_actions.py` before setup returns, as a self-check. Its failure is a defect (assert), not a refusal.

**(4) Provenance (`B/runs/provenance.py`).**
- **Cause or condition row with `origin == "OPERATIONAL_ACTION"`:**
  - `answered_by="OPERATIONAL_ACTION"`;
  - `answered_by_detail = f"Operational action {a.action_id} ({a.kind}, by {a.actor}), log {log.log_id} v{log.log_version}"`, where `a` is looked up in `identity.operational_action_log.actions` by `action_ref`'s action id.
  - `field` and `value` are built exactly as today.
- Scenario rows stay byte-equal.
- **Log row.** When the log is present, add one row after the reporting-path rows:
  - `identity_field="operational_action_log"`, `field="Operational action log"`;
  - `value=f"{log.log_id} v{log.log_version}, sha256 {log.sha256}"`;
  - `answered_by="OPERATIONAL_ACTION"`;
  - `answered_by_detail=f"{len(log.actions)} actions with a physical effect in this run"`.
  - When the log is absent there is no row, so provenance is byte-equal.
- **Field classification in `test_run_setup.py`:**
  - rendered: `FrozenCause.origin`, `FrozenReportingPathCondition.origin`, and the log's `log_id`, `log_version`, `sha256`, and `actions` (through the log row), plus `FrozenOperationalAction.action_id`, `.kind` and `.actor` (through the detail);
  - `not_rendered`, with these reasons:
    - both `action_ref` fields: "the action id reaches the row's detail; the content hash is on the intervention-history row";
    - `FrozenOperationalAction.content_sha256`: "on the intervention-history row";
    - `FrozenOperationalAction.at`: "the cause row's span states when, as an offset".

**(5) Request, port, adapter and loader.**
- **Request key** (`parsing.py` `parse_run_setup_request`): `operational_actions`, optional.
  - When present it must be an object with exactly `log_id` (str matching `^[a-z0-9][a-z0-9-]{0,63}$`) and `log_version` (int ≥ 1, not bool). Anything else is `REQUEST_INVALID`.
  - `RunSetupRequest` gains `operational_actions: OperationalActionsRequest | None = None` (a frozen dataclass with `log_id` and `log_version`).
- **Port** (`B/runs/ports.py`):
  - `class OperationalActionLogPort(Protocol): def read_log(self, log_id: str, log_version: int) -> OperationalActionLogSource`;
  - `OperationalActionLogSource(sha256: str, document: Mapping[str, Any])`;
  - `class OperationalActionLogUnavailable(Exception)`.
- **Adapter** (new `B/runs/adapters/yaml_operational_action_log.py`):
  - `DEFAULT_OPERATIONAL_ACTIONS_ROOT` is the repo's `config/operational-actions`, resolved the way `yaml_run_store.py` resolves its config root. This is the only place in `B/` that names the path.
  - `class YamlOperationalActionLog(root: Path = DEFAULT_OPERATIONAL_ACTIONS_ROOT)`.
  - It reads `{root}/{log_id}-v{log_version}.yaml`:
    - `text = read_text(encoding="utf-8")`;
    - `sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()` (LF-normalised, the F0e rule);
    - `document = yaml.safe_load(text)`.
  - A missing or unreadable file, a YAML error, or a non-mapping document raises `OperationalActionLogUnavailable`.
- **Loader and freeze** (new `B/runs/operational_actions.py`, pure, with no I/O): `freeze_operational_actions(request, identity, log_source, *, model, start, end) -> DeterministicIdentity`. In order:
  1. Validate the document. Top-level keys are exactly `log_id`, `log_version`, `site_code`, `timezone` and `actions`. Each action has `action_id` (the pattern above, unique in the log), `kind` (one of the five), `at` (`YYYY-MM-DDTHH:MM:SSZ`), `actor` (non-empty str) and `component_id`. Kind-specific keys:
     - `FUEL_DELIVERY`: `volume_l > 0`, `ticket`, `recorded_after_minutes`;
     - `FUEL_REMOVAL_UNRECORDED`: `volume_l > 0`, `duration_minutes > 0`, optional `sensor_disconnected {at, duration_minutes > 0}`;
     - `TANK_SEALED` and `SENSOR_POWER_PROTECTED`: optional `note`.

     Any other key, or a bad type, is `OPERATIONAL_ACTION_LOG_INVALID`.
  2. Inner `log_id` or `log_version` differs from the request, or `site_code` differs from `request.site_id`: `OPERATIONAL_ACTION_LOG_MISMATCH`.
  3. `content_sha256 = sha256(json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii"))` over the parsed action mapping (F0 `load_actions`).
  4. Select the actions with `at` in `[start, end)`.
  5. For each selected action, run §9.3 item 2's checks, in log order:
     - `OPERATIONAL_ACTION_COMPONENT_UNKNOWN`;
     - `OPERATIONAL_ACTION_STATE_NOT_CAUSAL`, which also covers a frozen identity with no initial `fuel-tank-volume` value or no `fuel-tank-capacity` value, since no bound can then be computed;
     - `OPERATIONAL_ACTION_UNIT`;
     - `OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN` (Q6).

     Then `OPERATIONAL_ACTION_OVER_CAPACITY` and `OPERATIONAL_ACTION_OVER_STOCK`, in exact `Fraction` arithmetic, over the effect-bearing actions in (`at`, `action_id`) order. Effect-free kinds get only the component and interval checks.
  6. Build the effects:
     - `FUEL_DELIVERY` is a `FrozenCause`: `event_id=f"{id}/tank-increase"`, `direction="INCREASE"`, `parameter_id=f"{id}-volume"`, `canonical_value=float(volume_l)`, the model stock's `canonical_unit` and `dimension`, `timing_shape="POINT"`, `offset_minutes` from `at`, `duration_minutes=None`.
     - `FUEL_REMOVAL_UNRECORDED` is the same with `"/tank-decrease"`, `"DECREASE"`, `"WINDOW"` and `duration_minutes`. With `sensor_disconnected`, add a `FrozenReportingPathCondition` with `event_id=f"{id}/sensor-disconnected"`, state `fuel-level-reporting-availability@fuel-tank`, `"WINDOW"`, and the span's offset and duration.
     - Every one of these has `origin="OPERATIONAL_ACTION"` and `action_ref=f"{id}:{content_sha256}"`.
  7. Any new `event_id` equal to a cause, forcing or condition `event_id` already in the identity: `OPERATIONAL_ACTION_EVENT_ID_CONFLICT`.
  8. Return `replace(identity, …)`:
     - `causes` = scenario causes then action causes, in (`at`, `action_id`) order;
     - the same for `reporting_path_conditions`;
     - `intervention_history` extended;
     - `operational_action_log` set.
- **Where it runs** (`B/runs/service.py` `create_draft_run`):
  - After the `signal_resolutions` replace (`:477-482`) and before `_decide`. The two placements are equivalent today (verified above). This one keeps the identity complete before any decision.
  - When `request.operational_actions` is None, nothing is called and nothing changes.
  - When it is set and the port is None, or the port raises `OperationalActionLogUnavailable`: `OPERATIONAL_ACTION_LOG_UNAVAILABLE`.

**(6) Composition.**
- `RunSetupService.__init__` gains keyword `operational_actions: OperationalActionLogPort | None = None`.
- `build_simulator_lab_router(…, operational_actions: OperationalActionLogPort | None = None)` passes it through.
- `B/main.py:677-697` passes `operational_actions=YamlOperationalActionLog()`.
- `host/tests/kisiwa.py`:
  - `KisiwaRegistered.__init__(store, setup_at, actions: OperationalActionLogPort | None = None)` hands `actions` to `RunSetupService`;
  - `draft(document, start, end, model="v7", operational_actions: dict | None = None)` adds the request key only when it is not None;
  - `draft_day` gains the same two optional arguments.
- Every other `RunSetupService(...)` caller is untouched, because the default is None.

**(7) `.gitattributes`**, appended after the R3e block:
```
# DIESEL-1-R3f: operational-action logs are hashed as LF on every host
config/operational-actions/* text eol=lf
```
- `C/operational-actions/kisiwa-001-operational-actions-v1.yaml` is a byte copy of `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml`'s blob (`git show main:<path> > <new>`).

**(8) New refusal kinds** (`B/runs/refusals.py`, each with a one-line meaning comment, each produced in `test_run_setup.py`'s `produced` set):
- `OPERATIONAL_ACTIONS_UNSUPPORTED_PATH`
- `OPERATIONAL_ACTION_LOG_UNAVAILABLE`
- `OPERATIONAL_ACTION_LOG_INVALID`
- `OPERATIONAL_ACTION_LOG_MISMATCH`
- `OPERATIONAL_ACTION_COMPONENT_UNKNOWN`
- `OPERATIONAL_ACTION_STATE_NOT_CAUSAL`
- `OPERATIONAL_ACTION_UNIT`
- `OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN`
- `OPERATIONAL_ACTION_OVER_CAPACITY`
- `OPERATIONAL_ACTION_OVER_STOCK`
- `OPERATIONAL_ACTION_EVENT_ID_CONFLICT`

`CAUSE_ORIGIN_INVALID` is **not** a setup refusal kind. Setup never builds an invalid origin. It is the message prefix of the model and parse errors in (1) and (3).

### 9f.3 Files (approved list; anything else is stop S5)

- **Edited:**
  - `B/runs/models.py`
  - `B/runs/parsing.py`
  - `B/runs/service.py`
  - `B/runs/ports.py`
  - `B/runs/refusals.py`
  - `B/runs/provenance.py`
  - `B/simulator_lab_api.py` (router signature and pass-through only)
  - `B/main.py`
  - `host/tests/kisiwa.py`
  - `.gitattributes`
  - `backend/tests/test_run_setup.py` (classification, `produced` set, and the REQUEST_KEYS message pin only)
  - any other existing test that pins the full REQUEST_KEYS message text (that line only)
- **New:**
  - `B/runs/operational_actions.py`
  - `B/runs/adapters/yaml_operational_action_log.py`
  - `config/operational-actions/kisiwa-001-operational-actions-v1.yaml`
  - `backend/tests/k0_byte_equal_pins.py` (first commit)
  - `backend/tests/test_k0_operational_actions.py` (L0 and L1)
  - `host/tests/test_k0_kisiwa_actions.py` (parity and L2)
- **Not edited:** `contracts/**`, `host/execution_adapter.py`, `S/**`, `F/**`, `.agent/DIESEL-F0/**`, `T/probe_kisiwa_fuel.py`, M2, M3, `record_channels`, and the envelope schema.

### 9f.4 Tests (localised only; no full suite; DB tests on `assetops_k0_test` only, machine idle)

**L0, no DB.**
1. **Byte-equal, against the first-commit pins** (Q10): all fixtures, all three digests. In addition, `"origin"` and `"action_ref"` appear in no rendered scenario-only run and no stored YAML file. This is §9c.3 (b).
2. **Model and parse refusals:** every `CAUSE_ORIGIN_INVALID` case in (1) and (3), including:
   - a stored `origin: SCENARIO`;
   - a history and log mismatch;
   - a dangling `action_ref`;
   - an orphan log action.
3. **Round-trip** on `YamlRunStore` (render, write, read, equality) and on each in-memory fake run store. An action cause and condition keep both fields and the log. A scenario cause keeps neither. This is §9c.3 (c).
4. **Setup** with an in-memory port over the promoted file's parsed content, for runs 2 and 4. The harness is the in-memory registered Kisiwa used by K1's tests if it runs without a DB; otherwise this test moves to L2. Checks:
   - origin is the field, `action_ref` is `"{id}:{sha}"`, and the `event_id` is `"{id}/{effect}"` with no `OPERATIONAL_ACTION/` prefix (§9c.3 (a));
   - the history equals `["OPERATIONAL_ACTION:" + ref]` and its content hashes equal those in `probe-result.json` `runs[k-1].intervention_history`;
   - the frozen log `sha256` equals `actions_sha256`.
5. **Each new setup refusal kind.** Nothing is written to the run store, and `create_run` is never called.
6. **Provenance rows** for an action cause, an action condition and the log row. Scenario rows are byte-equal.
7. **The no-reader test:**
   - `operational-actions` appears in no file under `B/` except `B/runs/adapters/yaml_operational_action_log.py`;
   - it appears in no file under `F/`;
   - `config/operational-actions` appears only in that adapter and `.gitattributes`.
8. **Adapter.** A CRLF copy of the file in a tmp dir gives the same `sha256` as the LF copy, and the hash equals `77777c82…b634`. A wrong file name gives `OPERATIONAL_ACTION_LOG_MISMATCH`, and a missing file gives `OPERATIONAL_ACTION_LOG_UNAVAILABLE`.

**L2 (`assetops_k0_test`):**
9. **Registered setup and kernel parity** for Kisiwa runs 2 and 4 through `host/tests/kisiwa.py` with `actions=YamlOperationalActionLog()`:
   - the per-step tank account equals F0r's (§9c.3 (d)): run 4 steps 120–128 at 40/3 L, and run 2 per `non_generator_steps`;
   - every other step's non-generator change is 0.
10. **Readback through the Lab API composition** (`main.py` app with the adapter): `POST` a Kisiwa run with the key, then `GET` it. The frozen inputs show `answered_by="OPERATIONAL_ACTION"` rows.

**Checks:** `ruff` and `mypy` on the touched backend files, and `git diff --check`.

### 9f.5 Stops (report to the Architect; never design around them)

- **S1.** Any pinned digest or byte changes for a run with no actions.
- **S2.** A need to edit `contracts/**`, `host/execution_adapter.py` or `S/**`, or M2, M3, `record_channels` or the envelope schema.
- **S3.** Kernel parity (test 9) differs from F0r's evidence by any amount.
- **S4.** The frozen log `sha256` ≠ `77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634`, or a K0 content hash ≠ F0's history hash.
- **S5.** A file outside §9f.3.
- **S6.** A fixture is not reproducible across two fresh processes even after removing `run_id` and `created_at`.
- **S7.** More than 3.0 units spent.

### 9f.6 Size, path and date

- **K0 stays 2.5** (range now 2.25–3.0, narrowed from 2.0–3.25).
- What Q2 and Q4 save:
  - no contract, host or trajectory edit, about −0.2 from the "contract and models origin" item;
  - the host and kernel reserve of 0.25, released to the range.
- What Q3, Q7, Q8 and Q10 add:
  - frozen log record, parse cross-check and log row, +0.15;
  - path refusals and the 11-kind producer set, +0.05;
  - harness port, +0.05;
  - first-commit pins, +0.05.
- Net about −0.05 at the centre, so the size stays 2.5.
- **Critical path unchanged.** K0 is off it, on lane 2, with about 2.3 units of float (§9.5). The path is still about **8.75 lane-units**, below the **9.75 tripwire**, and is not crossed.
- **Demo date unchanged** at about +3.25 working days. Contingency is unchanged at 0.05.
- After-the-demo list: none.

### 9f.7 Owner questions

None. For the owner, in plain words: the fuel delivery and the unrecorded removal now enter the simulated world as logged operator actions, stamped with who did what and from which log. Runs that have no actions stay exactly as they were, to the byte.

---

## 9g. Ruling DIESEL-1-R3g: K3 stop S4 (K2's fuel-records reader in the composition)

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27).
- Read on `task/DIESEL-K3-fuel-balance` at `7ded13f1c` (phase A `202535b81`, rule-8 reorder `f864e9e1a`, main merged `3843c82e2`). Read: `tools/checks/configuration-persistence.ps1` rule 1 (`:223-274`), `B/work/composition.py`, `B/evidence/composition.py:89-98`, `B/fuel_balance/composition.py`, `B/fuel_balance/worker.py:38-73`, `B/fuel_balance/adapters/postgres_fuel_balance_store.py:160-190`, `B/work/adapters/postgres_fuel_records.py:40-46`.

### 9g.1 Decision 1: allow the exposure in `B/work/composition.py` (a named, narrow exception to §9d.9 S4)

- **Allowed.** It is the established pattern: `evidence/composition.py:89 build_link_rows_reader()` hands a caller-connection reader across domains in the same way, and `work/composition.py` already uses it. Rule 1 is kept as written: the only `work.adapters` import stays inside `work/composition.py`.
- **Routes rejected:**
  - a second fuel-records query in `fuel_balance/adapters/` would duplicate K2's correction semantics, the very rows K2 L1 and §9d.3 test;
  - moving `select_fuel_records` out of `work/adapters/` changes K2's layout for no gain;
  - widening rule 1 is never done.
- **The exception is these lines only.** It covers no other `B/work/` edit and no behaviour change. S4 stays in force for everything else.

### 9g.2 Exact change

1. **`B/work/composition.py`**: add after `build_work_service`, with a lazy import like `build_link_rows_reader`:
   ```python
   def build_fuel_records_reader():
       """DIESEL-K3 (DIESEL-1-R3g): K2's fuel-records read on a caller's connection, for the fuel-balance store."""
       from assetops_backend.work.adapters.postgres_fuel_records import select_fuel_records
       return select_fuel_records
   ```
   - Add `"build_fuel_records_reader"` to `__all__`, in alphabetical position.
   - The name is `build_fuel_records_reader`, not `fuel_records_on_connection`, to match the `build_*_reader` precedent.
2. **`B/fuel_balance/composition.py`**:
   - The default branch becomes `from assetops_backend.work.composition import build_fuel_records_reader` and `fuel_records = build_fuel_records_reader()`.
   - Remove the `type: ignore` and the "K3 STOP S4" comment.
   - Keep the docstring, which names `work/composition.py`.
3. No other file changes for this item. The adapter, K2's tests and the rule-1 script stay untouched.

### 9g.3 Tests that the production path composes

- **A13 (L0, append to `backend/tests/test_k3_fuel_balance_rules.py`, no DB):**
  - (a) `work.composition.build_fuel_records_reader() is work.adapters.postgres_fuel_records.select_fuel_records`.
  - (b) `store = fuel_balance.composition.build_fuel_balance_store("postgresql://unused@127.0.0.1:1/none")`. Assert `store._fuel_records is select_fuel_records`, `isinstance(store._actions, PostgresActionStore)`, `store._engine is None` (nothing connects) and `store.test_db_clock_override is None`.
  - (c) **The worker's own branch.**
    - Spy on `fuel_balance.composition.build_fuel_balance_store` with a wrapper that delegates to the real function and keeps the store it returns.
    - With `DATABASE_URL` unset (monkeypatch `delenv`), run `worker.main(["assess", "--site", "KISIWA-001", "--from", "2026-10-06", "--to", "2026-10-07"])` with no `store=`. It must raise `RuntimeError` matching `"DATABASE_URL is not set"`.
    - The spy must record exactly one call with `None`, and the kept store's `_fuel_records is select_fuel_records`.
    - This test fails today with the `ImportError` the builder reported.
- **C (parity, `host/tests/test_k3_fuel_balance_parity.py`):**
  - Build the module's `kisiwa["fb"]` with `build_fuel_balance_store(URL, test_db_clock_override=<the existing virtual clock>)` instead of constructing `PostgresFuelBalanceStore` by hand with an adapter import.
  - Every C assertion, the CLI `REUSED` step included, then runs through the production composition against a real DB. The virtual clock is the composition's own test-only parameter (§9d.4).
  - Part B may keep its direct injection: its K2 L1 tests are about the reader, not the wiring.
- No other test changes. A13 is L0. C runs as already planned for phase B (machine idle, `assetops_k3_test` only).

### 9g.4 Who does it

- **The planned Sonnet round on `task/DIESEL-K3-fuel-balance` (worktree `C:\Users\assef\Bineyame\AssetOpsV1-k3`)**, in the same round that verifies and finishes phase B. Order:
  1. §9g.2 and A13;
  2. switch C's fixture to the composition;
  3. run phase B's part C;
  4. write the packet.
- One commit for §9g.2 + A13, then phase-B commits. Use `git add -f` of explicit paths.
- The packet lists the `work/composition.py` diff under "S4 exception, DIESEL-1-R3g".
- K3's first review (Opus, §9d.10) reviews the whole branch, this item included.
- Size: about 0.05, inside K3's 1.6. **Critical path, tripwire and date are unchanged.**

### 9g.5 Builder calls confirmed

- **K2 L2 single-head assertions made head-agnostic** (`backend/tests/test_k2_fuel_records_postgres.py:137-138, 168, 184, 186`, in `202535b81`): **confirmed**. This is a head-bookkeeping edit, not a behaviour change (not S5). It is the same allowance §9d.6 gives catalogue-count tests and K2 took for 0054.
  - The single-head property is still asserted (`get_heads() == [alembic_head()]`), and 0054's `down_revision == PREVIOUS` is kept.
  - The up/down/up and refused-downgrade tests still pass through 0054. Downgrading to `PREVIOUS` now also takes 0055 down first, on its empty table.
  - Condition: the packet states that these lines changed and why, and the reviewer re-reads them.
- **`$fuelBalanceWriter` moved before `$trialComparisonWriter` in rule 8's `$pgWriters`** (`f864e9e1a`, one line): **confirmed**.
  - The list membership is identical, so the rule is not loosened.
  - The order keeps `tools/checks/test_estate_guard.py:148`'s anchor `", $trialComparisonWriter)"`, which that self-test edits.
  - The packet lists it with that reason.

### 9g.6 Owner questions

None.

---

## 9h. Ruling DIESEL-1-R3h: K3 stop S1 (600 idle seconds on every Kisiwa night)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27).
- Read on `task/DIESEL-K3-fuel-balance` at `3c239ad2c`: `B/fuel_balance/rules.py:171-201` (`use_from_readings`), `B/actions/verification_rules.py:222-330` (`_power_slot`, `_instant`), `:372-373`, `:478-491` (A2's idle count), `B/analytics/dispatch.py:97-98`, `:242-300` (run reconstruction, `_off_after`), `simulator/assetops_simulator/packs/mini_grid.py:29-33` (lifecycle timing), `backend/tests/test_tfc2.py:146-177`, `backend/tests/test_k3_fuel_balance_rules.py:155-230`.
- Evidence: read-only SQL on `assetops_k3_test` (the stored windows of the failing run and their `accepted_evidence`).

### 9h.1 The stop

On nights 2, 4 and 6, `idle_seconds = 600` where the card and F0 expect 0. `use_high` and `residual_low` each differ from F0 by `539/600` L = `600/3600 h × 49/10 L/h × 11/10`. Every other term and all three states match F0.

### 9h.2 Cause, with evidence

**The idle slots are the two generator stop slots of each night.**
- The SQL pairs each accepted `generator_state` sample at `t` with the `generator_power` mean over `[t, t + 5 min)`, the pairing that `use_from_readings` and A2 both use. In each window it finds exactly two slots that are RUNNING at 0 kW. In UTC, the same instants each night:

  | Slot start (UTC) | Local | State at `t` | Mean kW over `[t, t+5)` | Mean kW over `[t−5, t)` | State at `t + 5` |
  |---|---|---|---|---|---|
  | 19:05 | 22:05 | RUNNING | 0 | 38 | STOPPED |
  | 00:15 (next day) | 03:15 | RUNNING | 0 | 27 | STOPPED |

- 2 × 300 s = 600 s on every night. No other slot is RUNNING at 0 kW.
- Starts give no idle slot. Example: STOPPED at 17:05 with 0 kW over `[17:05, 17:10)`, then RUNNING at 17:10 with positive kW from 17:10.

**Why the stop and the start differ.** The simulator's lifecycle timing (`mini_grid.py:29-33`) works like this:
- A request emitted at `T` changes the state in phase F, after the sample at `T`. So the sample at the stop instant still says RUNNING, and the slot that follows carries 0 kW: the generator is already STOPPED for the whole slot and burns nothing.
- At a start, the elapsed start delay moves STARTING to RUNNING in phase A, before the sample. So the STARTING step is published as STOPPED at 0 kW, and the first RUNNING sample opens a loaded slot.
- The result is that every stop publishes one "RUNNING at the slot start, 0 kW over the slot" pair. That is an artefact of the sampling order, not idle running.

**This is the shared slot rule, not a K3 bug.** K3 applies A2's rule exactly as §9d.2 ordered: `state_t ∈ RUNNING_STATES and kwh_t == 0` (`verification_rules.py:490`, mirrored at `rules.py:196`). A2's `generator_idle_seconds` would score the same two slots per night as 600 s, as K3 does; test A6 already pins that they are equal.

**The product disagrees with itself here.** The dispatch analytic, whose Candidate time drives fuel-cost-2, ends a run at its last RUNNING sample when a 0 kW interval starts there (`dispatch.py:292-300`, `_off_after`). So the product's own run reconstruction reads the stop slot as stopped, while A2's slot rule reads it as idle.

**F0's 0 is right.** L2 predicted that F0's true-trajectory terms could differ from the readings. Here the trajectory has 0 idle fuel, and the published evidence, read the way dispatch reads it, also has 0 idle.

### 9h.3 Decision: (c), a shared slot-rule defect. Fix the rule once, in `verification_rules.py`; parity expectations stay as the card wrote them.

- **Not (a).** Accepting 600 s would book about 0.9 L of "idle" fuel per Kisiwa night that the evidence does not show. The generator was published RUNNING only at the stop instant, and the product's own dispatch reading calls the following slot stopped. It would also make §9c.3 L2 (c) false ("Kisiwa has 0 idle minutes"), and it would put an artefact into A2's money wherever a trial window contains a stop.
- **Not (b).** K3 followed the card.
- **The rule (A2's, shared):** a slot is idle iff
  - the sample at `t` is RUNNING, and
  - the slot kWh is exactly 0, and
  - the accepted sample at `t + 5 min` is **not** one of the not-running states (`STOPPED`, `STARTING`, `FAILED`, i.e. `dispatch.NOT_RUNNING_STATES`).

  A missing, conflicting or non-GOOD sample at `t + 5 min` leaves the slot idle, exactly as today. The lookahead only removes a slot when there is a **positive** stop marker; it never makes a slot unknown. So no window's `None` or its problems change.
- **Why that rule.** It is dispatch's `_off_after` boundary, stated per slot. It removes only the stop slot. A generator that idles unloaded for the whole slot and stops at the next boundary is still counted, because the sample at that boundary is still RUNNING (phase F order). The cost: a real engine that idled part of the slot and then stopped is not counted for that part. That undercounts by at most one slot per stop, the same treatment the start slot already gets. In the fuel balance this is at most 0.45 L of `use_high` per stop, against a 2a = 20 L margin.
- **Tolerances are unchanged.** C keeps every exact item, 1/100000 L on the toleranced terms, and `idle_seconds == 0` on all three nights. No restatement is needed, because with the fix K3 equals F0.

### 9h.4 Exactly what changes

**1. `B/actions/verification_rules.py`** (named, narrow S4 exception, like R3g; nothing else in the file changes). Next to `RUNNING_STATES` (`:372-373`):
```python
#: DIESEL-1-R3h: the sampled values that end a run (`analytics.dispatch.NOT_RUNNING_STATES`)
NOT_RUNNING_STATES = frozenset({"STOPPED", "STARTING", "FAILED"})


def idle_slot(slot_start: datetime, state_value: Any, slot_kwh: Fraction | None,
              state_readings: Iterable[Reading]) -> bool:
    """A2's idle slot: sampled RUNNING at the slot start and exactly 0 kWh over the slot, unless the accepted sample at
    the slot end is a not-running state. That slot is the stop slot: the sample precedes the stop, and dispatch's
    `_off_after` ends the run there (DIESEL-1-R3h). A missing or unknown end sample keeps the slot idle."""
    if state_value not in RUNNING_STATES or slot_kwh is None or slot_kwh != 0:
        return False
    return _instant(slot_start + SLOT, state_readings, numeric=False)[1] not in NOT_RUNNING_STATES
```
- In `window_evidence`, `:490` becomes `elif idle_slot(t, gen_value, slot_gen_kwh, state_readings):`.
- The lookahead's payload is **discarded**: no `note(...)` and no `evidence.update(...)`. The window's problems, evidence ids, `plan_sha256` and stored details are therefore byte-equal. `generator_idle_seconds` is already outside `plan_sha256` and the details (`:435-436`, `test_out_e3_trial_comparison_postgres.py:52`).

**2. `B/fuel_balance/rules.py`**:
- `use_from_readings` imports `idle_slot` and replaces `value in RUNNING_STATES and kwh == 0` (`:196`) with `idle_slot(t, value, kwh, state)`. The unknown handling stays as it is.
- The docstring says "A2's slot rule (`verification_rules.idle_slot`)".

**3. Tests**
- **`backend/tests/test_tfc2.py`**: add `test_window_idle_seconds_exclude_the_stop_slot`:
  - gen 0 kW; RUNNING at slots 0–5, STOPPED at 6–11 → `generator_idle_seconds == 1500`, not 1800;
  - RUNNING at 0–11 with STOPPED at the window end (`T0 + 60 min`, an extra point) → 3300;
  - RUNNING at 0–11 with no end sample → 3600 (unchanged);
  - RUNNING at 0–5, then a non-GOOD sample at slot 6 → 1800 (no positive stop marker).
  - Each case must fail if the lookahead is removed or inverted.
  - **The existing tests stay byte-unchanged.** Line 169's `three` case keeps 900, because the sample after slot 2 is `"ON"`, which is not a not-running state.
- **`backend/tests/test_k3_fuel_balance_rules.py`**:
  - **A3 fixture:** `running = set(range(25))`. The idle night has 25 RUNNING samples (slot starts 0–24) and STOPPED from 25, so 24 idle slots. All of A3's expected numbers stay as the card wrote them (7200 s, `539/50`, `1711/50`, BELOW_MATERIALITY, the r = 33/10 rerun).
  - **New A14:** the Kisiwa stop shape. Slot `k` loaded at 38 kW, then RUNNING at `k+1` with 0 kW and STOPPED at `k+2` → `idle_seconds == 0`. Converse: RUNNING at `k+1` and `k+2`, 0 kW over both slots, STOPPED at `k+3` → 300 (slot `k+1` idle, slot `k+2` the stop slot).
  - **A6 extended** with one stop slot inside the hour: K3's idle seconds equal `window_evidence(...)["generator_idle_seconds"]`.
- **`host/tests/test_k3_fuel_balance_parity.py`**: no change. C is re-run as written, on `assetops_k3_test`, with the machine idle and free RAM checked. Expected: all three nights pass, with `idle_seconds == 0`.
- **Must stay green unchanged** (localised runs, no full suite):
  - `test_tfc2.py` (the existing cases);
  - `test_s6_verification_rules.py`;
  - `test_out_e3*` cost-check tests;
  - `test_ch9b2_reserve_byte_equal_postgres.py` and `test_s6_verification_evaluator_postgres.py` (their goldens hold `generator_idle_seconds: 0`, and a rule that only removes slots cannot change a 0);
  - K3's A1–A13 and B1–B6.

  If any of them needs a behaviour edit, stop under S5.

**4. What does not change:** `probe-result.json`, the probe, `PARAMETERS`, every C tolerance, `dispatch.py`, `fuel_cost_v2.py`, `trial_fuel_comparison.py`, and every Kobo, Cold and EV file.

### 9h.5 Who does it

- **A Sonnet fix round on `task/DIESEL-K3-fuel-balance`** (worktree `C:\Users\assef\Bineyame\AssetOpsV1-k3`). Order:
  1. §9h.4 items 1–3 in one commit;
  2. the localised runs;
  3. part C, re-run;
  4. the packet.
- The packet lists the `verification_rules.py` diff under "S4 exception, DIESEL-1-R3h" and quotes this section's SQL table as the cause.
- `git add -f` of explicit paths.
- **K3's first review (Opus)** covers it. The reviewer applies two mutations to a scratch copy:
  - delete the lookahead: the new tfc2 test, A14 and C must fail;
  - replace `NOT_RUNNING_STATES` with `{"STOPPED"}`: the tfc2 non-GOOD case must still pass, which shows that only positive markers act.
- **K6** merges main before its own `verification_rules.py` edit. The R3d note that K6 owns the next edit now reads "the next edit after R3h".

### 9h.6 Kobo impact (A2, stated plainly)

- **Kobo's idle-fuel money in the demo does not change.**
  - A2 changes only in a verification window that contains a stop slot: a RUNNING sample, then 0 kWh, then a not-running sample.
  - Kobo's trial baseline hour (09:00–10:00 local) sits inside a run that idles from 07:05 to 10:55 (`.agent/fuel-story-design-2026-11-07.md:66`, `:137`). Its later hour has no run. Neither hour contains a stop, so both keep 3600 s and 0 s.
- **fuel-cost-2** (Kobo's three idle mornings) counts idle inside dispatch's Candidate time, which already ends at the last RUNNING sample. It is unaffected.
- **The defect is real for Kobo in general.** Without the fix, any trial window that contains a generator stop would gain 300 s per stop: 0.275 L nominal, 0.3025 L upper at 3.3 L/h, about 0.34–0.38 USD at 1.25 USD/L. In a baseline window that inflates the claimed saving; in a later window it understates it. None of the demo's windows contains one.
- **A3's check stands as the backstop.** If the stored trial-hour idle differs from 12 slots, it is a data finding (`build-sheet-FUEL-1.md:425`). A3 needs no edit.

### 9h.7 Effect on the demo story

- With the fix, every Kisiwa night shows **0 idle minutes and no idle fuel**. That is honest: the generator runs loaded and stops, and both the simulator and the product's dispatch reading say it never idles.
- Night 4's band, and so K4's UNEXPLAINED figure, equals F0's exactly. Nights 2 and 6 stay WITHIN_MARGIN.
- **The alternative is not honest.** Without the fix every night would carry about 0.9 L of idle fuel (2 × 5 min at 4.9 L/h × 1.1) that never happened, and night 4's lower residual would sit about 0.9 L below F0.
- K4 and K5 add **no** idle line on Kisiwa (`idle_seconds` is 0). The idle term stays exercised only by A3, as §9c.3 L2 (c) says.

### 9h.8 Size

- About **0.15**: rule and helper 0.05, tests 0.05, part C re-run and packet 0.05. K3 goes from 1.6 to about 1.75, inside S7's 1.9.
- It is paid from the remaining contingency (0.15 → 0), so the Kisiwa total stays **17.25**.
- **Critical path:** about 8.9 lane-units (8.75 before). That is **below the 9.75 tripwire; no cut.**
- **Demo date:** unchanged at about +3.25 working days.
- **Contingency is now spent.** The next overrun on the Kisiwa lane is reported against the tripwire, not absorbed.

### 9h.9 Owner questions

None.

---

## 9i. Ruling DIESEL-1-R3i: K0's two S5 stops, five deviations, and a main-drift failure

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `bd15b0ca8`.
- K0 was read on `task/DIESEL-K0-action-bridge`:
  - `d782fc09f` holds the pins;
  - `dd4a3874f` holds the bridge;
  - `2b8ab3ab9` holds the packet `.agent/review-packet-K0.md`.

**Code facts the Architect verified on the K0 worktree:**
- `B/runs/composition.py` docstring: "the one place in the product allowed to import `assetops_backend.runs.adapters.*`".
- `tools/checks/configuration-persistence.ps1:580-640`, rule 7:
  - the run adapters hold exactly one `= yaml.load(..., Loader=CSafeLoader)`;
  - `safe_load` is banned anywhere in the run adapters;
  - the stated reason is one loader policy for the run domain (`D-2026-09-29-run-store-libyaml`).
- `yaml_run_documents.py:150` is that one load point today.
- `git diff d782fc09f 2b8ab3ab9 -- backend/tests/k0_byte_equal_pins.py` is empty. The pins have not moved since the first commit, and `seeded_uuid4()` was already in that commit.
- `backend/tests/test_run_binds_scenario_to_site.py` was last edited at `aeb53fb86` (2026-10-31). `config/scenarios/kobo-rest-mill.yaml` was added at `8b68aaa14` (2026-11-06, DD1a1-R16). The test's set equality (`:242-245`) cannot hold for scenarios added after it.

### 9i.1 Rulings

**S5-a. Approved: `B/runs/composition.py` joins §9f.3's file list.**
- Add `build_operational_action_log() -> OperationalActionLogPort`, which returns `YamlOperationalActionLog()`, beside `build_run_repository`. The docstring is one line.
- `B/main.py` imports it from `runs.composition` and passes `operational_actions=build_operational_action_log()`. It never imports the adapter.
- §9f.2 (6) is amended to read "through the composition".
- **Test.** §9f.4 test 10, on `assetops_k0_test`, must exercise this composed path: the `main.py` app, not an injected router.
  - It sets up Kisiwa run 4 with the named log.
  - It gets no `OPERATIONAL_ACTION_LOG_UNAVAILABLE`.
  - On readback it shows `answered_by="OPERATIONAL_ACTION"` rows.

**S5-b. Option (i): a shared text-load function in `B/runs/adapters/yaml_run_documents.py`. That file joins §9f.3. The guard is not changed.**
- In `yaml_run_documents.py`, add `def load_yaml_text(text: str) -> object: return yaml.load(text, Loader=CSafeLoader)`. It holds the one guarded line, and `yaml.YAMLError` propagates.
- `read_run_record` calls `load_yaml_text(text)` inside its existing `try`. Its behaviour and messages are unchanged.
- `yaml_operational_action_log.py` imports and calls `load_yaml_text`, and maps `yaml.YAMLError` to `OperationalActionLogUnavailable`. It no longer imports `CSafeLoader` or calls `yaml.load`.
- This is rule 7's own intent: one loader policy at one load point in the run adapters.
- §9f.2 (5)'s `yaml.safe_load` was the Architect's slip. The run domain's policy is libyaml `CSafeLoader`, and stop S4's hash and content-hash checks prove that the promoted log parses the same.
- Acceptance:
  - the architecture check and the estate-guard self-tests pass with **no** change to `configuration-persistence.ps1`;
  - `rg "yaml\.load\(" backend/assetops_backend/runs/adapters` gives exactly one hit.
- Option (ii) is refused. A guard is never loosened to fit a spec slip.

**Deviation 1, EV pin under `seeded_uuid4()`: accepted, not an S6 stop.**
- S6 exists so a pin cannot be meaningless. A render that varies only by random mapping ids would be meaningless.
- Under a fixed seed, the pin is deterministic and still covers every byte K0 could move. K0 produces no mapping id.
- The seeding has been in the first commit, unchanged since.
- Condition: the pin's docstring states that the seeding fixes only identifiers K0 does not produce. The packet's S6 note cites this ruling.

**Deviation 2, test 1 in `host/tests/test_k0_kisiwa_actions.py`: accepted.**
Digest (c) needs `host/`'s `frozen_world_inputs`, and `backend/tests` does not import `host/`.

**Deviation 3, the loader's `component_ids` keyword: accepted.**
The pure loader receives the Site's component ids instead of a Site record, so it stays I/O-free. §9f.2 (5)'s signature is amended to `freeze_operational_actions(request, identity, log_source, *, model, start, end, component_ids)`.

**Deviation 4, the coverage test excludes `operational_action_log`: accepted, with one tightening.**
- The exclusion is right for a run that names no log: the field is None, and it has no row so the run stays byte-equal.
- Add one K0 test assertion: for a run that **names** a log, the same coverage holds with **no** exclusion (`covered == declared`).
- This turns the exclusion into a tested conditional.

**Deviation 5, UNIT and EVENT_ID_CONFLICT reachable only by a direct loader call: accepted, kept as kinds.**
- Both have live producers that guard real input combinations:
  - UNIT: a selectable model profile whose `fuel-tank-volume` stock is not in L;
  - EVENT_ID_CONFLICT: a scenario event-id grammar that admits `{id}/{effect}`.
- Neither combination is shipped today. This is not the retired-kind case in `refusals.py:83-89`, where the producer had been deleted.
- Add a comment to each kind in `refusals.py`: "reachable only by a model profile (or scenario id grammar) not shipped today; tested by a direct loader call".
- The `produced` set keeps them, through those direct calls.

**Main drift, `test_run_binds_scenario_to_site.py` (12 failures, `KeyError 'kobo-rest-mill'`): confirmed main drift, not K0.**
- The test predates about 10 shipped Kobo scenarios added in the DD-1a1 and DD-1a2 rounds (up to 2026-11-06). K0 touches no scenario and not that test.
- **Who fixes it:** a separate Sonnet fix unit, **DRIFT-RB1**.
  - Branch `task/DRIFT-RB1-scenario-site-sample`, from main.
  - It edits that one test file only.
  - It does not block K0's review or merge, and K0 must not fix it.
- **Rule for the fix.** `FROZEN_V1_SAMPLE` is the frozen v1 sample and gets no new entries with invented dates. Each new stem goes into `NEVER_SHIPPED_AS_V1`, or a sibling set with a one-line reason if that set's meaning does not fit.
- **Verification:** that test file passes. `git diff --stat` shows one file. The coordinator verifies.
- **Cost:** about 0.05. It is charged to the DD (Kobo-day) lane's follow-ups, not to Kisiwa.

### 9i.2 Order

1. **K0 Sonnet fix round** on the K0 branch:
   - S5-a;
   - S5-b;
   - the deviation 1 docstring;
   - the deviation 4 assertion;
   - the deviation 5 comments;
   - a packet update citing R3i.

   It re-runs only the K0 tests (with test 10 on `assetops_k0_test`), the architecture check and the guard self-tests. There is no suite.
2. **Then K0's Opus first review, straight after**, on the final tree. No review happens before the fix round: both S5 items change wiring the reviewer must see.
3. **DRIFT-RB1** runs in parallel. It is independent.

### 9i.3 Size, path, date

- **K0: 2.5 → 2.6** (range 2.25–3.0, unchanged). The +0.1 covers the two S5 fixes and the EV-pin seeding.
- The contingency is spent (§9h.8). So this is **reported, not absorbed**: the Kisiwa total goes **17.25 → 17.35**.
- **Critical path unchanged at about 8.9 lane-units.** K0 is off it, and its float of about 2.3 absorbs the 0.1.
- **Below the 9.75 tripwire; no cut.** The demo date is unchanged at about +3.25 working days.
- DRIFT-RB1 (0.05) is outside the Kisiwa total.

### 9i.4 Owner questions

None.

---

## 9j. Ruling DIESEL-1-R3j: the K4 consolidated card (the unexplained-fuel Finding, migration 0056), split K4a / K4b

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `801efc0e2` (K3 merged `ce03ae246`, review `.agent/review-K3.md` ACCEPT; PV-1 `4d7f400c8`, MB-1a/b, CH-5d1, A1, A2, K1, K2 merged; K0 in its fix round; A3 not merged).
- Owner decisions in force, verbatim: `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'"); `.agent/owner-fuel-scope-2026-11-07.md` (no combined total; money only from evidence: "Portfolio line per proven result with no combined total"); `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions"); `.agent/owner-kisiwa-scope-2026-11-07.md` ("Build it, with the action link (Recommended)"); `.agent/owner-diesel-night-window-2026-11-07.md` (a night runs "6 pm to noon").
- **This card replaces** the K4 rows of §8.4 and §9.5 and §8.4's "Finding literals (K4)". It binds H1–H5 (§8.2). Builders read only their part below (K4a: §9j.1–§9j.9; K4b: §9j.1, §9j.10–§9j.14). Paths use the header's short forms; `T/` = `tools/`.
- READ = the Architect read the code at `801efc0e2`; nothing here was measured.

### 9j.1 Code reality and the decisions it forces (READ)

1. **A Finding is a row in the shared `finding`/`finding_revision` tables, and every Finding there cites an assessment.** `finding.anchor_assessment_revision_id`, `finding_revision.assessment_revision_id` and `analytic_run_id` are NOT NULL FKs (`backend/migrations/versions/0009_finding_store.py:33-106`). Cold and EV Findings meet this with their own `analytic_run` + `assessment_revision` written by the assessment store, then domain-specific inserts in the Finding store (`B/analytics/adapters/postgres_finding_store.py:588-711` `cold_apply`, `:713-828` `ev_apply`). The guard makes the assessment store the only writer of `analytic_run`/`assessment_revision` and the Finding store the only writer of the Finding tables (`T/checks/configuration-persistence.ps1:699-720`, `:1219-1224`).
   - **Decision: K4 follows the cold/EV pattern exactly.** A new Finding storage domain `fuel_balance`; one `analytic_run` + `assessment_revision` (analytic `fuel-balance-1`) per window revision a Finding cites; the Finding and its revisions inserted by a new `fuel_apply` in the Finding store. No NOT NULL is relaxed and no reader loses a join.
2. **The fuel-cost outbox does not fire for a new domain.** `financial_consequence_dirty_on_finding_revision` runs only `WHEN (NEW.domain = 'mini_grid')` (`0022_w2_cold_assessment.py:214-219`). The cold trigger runs only for `cold_chain` (`0023`). So a `fuel_balance` revision enqueues no fuel-cost work: **the Finding can never acquire fuel-cost-1/2 money.**
3. **`financial_consequence_revision` cannot hold this money.** Its CHECKs pin `quantity_low = 0` and `amount_low = 0` (`0011_financial_consequences.py:92-108`); the residual band's low edge is positive. Cold and EV each have their own consequence tables. **Decision:** a new append-only table `fuel_residual_consequence_revision`, written by the consequence store (the guard's sole consequence writer). Own model, own basis, own table: nothing that sums `financial_consequence_revision` can see it.
4. **Threads need one row.** `chain/threads.py:30-32` `SUBJECT_COLUMN`: "A further domain needs one row here, nothing else." Without it `finding_source` raises `KeyError` on the tick's threads step. K4a adds `"fuel_balance": "subject_asset_id"`. Thread key = `(tenant, site, UNEXPLAINED_FUEL, ASSET, tank id)`: every unexplained night of one tank is an occurrence on one thread, and the existing registry gives occurrence numbers and RECURRED (`RECURS_FROM`, `:34`).
5. **The board's Finding read is dispatch-only.** `_FINDING_HEADS` filters `f.domain = :domain AND f.analytic_id = :analytic` (`B/chain/adapters/postgres_chain_read.py:27-45`); the board's `lead_finding`/`money_head` path reads `financial_consequence_revision`. K4b adds a **second, separate** head read for `fuel_balance`, and keeps every dispatch-only path (COST lead, money head, Trial option) on dispatch heads only.
6. **Row placement is declared only in the outcome map.** `board._row` places issues, thread lines, in-hand and earlier items from `outcome_roles` (`B/outcomes/outcome_map.py:17-36`; `board.py:875-1029`). The mini Protect row has only `MG-5` "Reliable service" and `MG-4` "Battery and generator life" (`B/outcomes/catalogue.py:48-49`). Mapping unexplained fuel to either would state a false outcome. **Decision:** a new catalogue outcome **`MG-8` "Fuel accounted for"** (MINI, PROTECT_ASSET), moved by `FINDING:UNEXPLAINED_FUEL`; NOT_APPLICABLE on a Site with no stored fuel-balance window (Kobo), so Kobo's Protect row state cannot change.
7. **§8.4 misplaced one reference.** `NO_FUEL_BALANCE` (`B/site_outcomes/mini.py:81`, `:937`) is the **Optimize** row's "Fuel" contributor (from Kobo's hourly fuel depth), not Protect. It stays byte-equal on every Site. Kisiwa's Protect row gains a new "Fuel in the tank" contributor instead (K4b).
8. **The Portfolio line goes on the Protect card, not Assure.** H2 says the Assure card gains no line for this story, and PV-1's Assure `value_lines` are verified results only (`B/site_outcomes/read.py:820-836`). The unexplained-fuel money is a Finding's, so it is listed on the **Protect** card, PV-1's pattern (one line each, own basis, never summed). **K4b owns it** (moved from K8, §9j.14).
9. **Only two product strings say "theft"**: `F/sites/MiniPerformance.tsx:1311` (`FUEL_NOTICE`) and `:1343` (the RESIDUAL row); the only other hits are tests and `.agent/` logs (`git grep -i theft`). K4a rewords both (moved from K5; K5 must not touch those two lines).
10. **Why split.** K4 as one unit is about 2.4 with the placement work in items 5–6. K6 needs only the Finding, its thread and its money (K4a). The board, outcome and Portfolio placement (K4b) can run on lane 1 beside K6. The split shortens the critical path by about 1.0 (§9j.15).

### 9j.2 K4a: what it delivers (lane 3, critical path)

- Migration 0056 (§9j.3); `fuel_apply` and the window assessment persist (§9j.4); the consequence store's `fuel_residual_append` (§9j.5); the service and CLI that raise Findings from stored K3 windows (§9j.6); the pure client-text module (§9j.7); the threads mapping; the two "theft" strings reworded; K3's single-head test made head-agnostic; K3 review L1 and L2 closed; finish row KIS-4.
- **No board, outcome, Portfolio or route change** (K4b and K5). **No served page renders the Finding's lines yet** (K5's panel). **No tick stage:** like K3, the raise is explicit (K7's prepare calls it after `assess`, then runs the existing threads step).

### 9j.3 Migration `backend/migrations/versions/0056_unexplained_fuel_finding.py`

`revision = "0056_unexplained_fuel_finding"`, `down_revision = "0055_fuel_balance_window"`. Renumber rule (§8.4) stands: if another migration lands first, K4a takes the next number and K6 follows.

1. **Finding domain arm.** Recreate `finding_domain_subject` and `finding_revision_domain_minutes` exactly as `0025_w2_ev_session.py:52-63` (`DOMAIN_SUBJECT_0025`, `DOMAIN_MINUTES_0025`, copied as constants named `..._0025`, used by the downgrade) **plus one arm each**:
   - subject: `OR (domain = 'fuel_balance' AND subject_asset_id IS NOT NULL AND generator_asset_id IS NULL)`;
   - minutes: `OR (domain = 'fuel_balance' AND candidate_minutes IS NULL AND necessary_minutes IS NULL AND indeterminate_minutes IS NULL)`.
   - Use 0025's `_domain_checks` statement shape (DROP then ADD in one `ALTER TABLE` per table).
2. **The consequence table:**
```sql
CREATE TABLE fuel_residual_consequence_revision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    site_id uuid NOT NULL,
    finding_id uuid NOT NULL,
    finding_revision_id uuid NOT NULL,
    fuel_balance_window_id uuid NOT NULL,
    model_id text NOT NULL CHECK (model_id = 'fuel-residual-1'),
    basis text NOT NULL CHECK (basis = 'UNEXPLAINED_FUEL_AT_DECLARED_PRICE'),
    litres_low text NOT NULL CHECK (litres_low ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    litres_high text NOT NULL CHECK (litres_high ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    state text NOT NULL CHECK (state IN ('PRICED','UNPRICED')),
    price_reason text NULL,
    price_revision_id uuid NULL,
    price_assignment_id uuid NULL,
    price_value numeric NULL,
    currency text NULL CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    amount_low text NULL CHECK (amount_low IS NULL OR amount_low ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    amount_high text NULL CHECK (amount_high IS NULL OR amount_high ~ '^-?[0-9]+(\.[0-9]+)?$|^-?[0-9]+/[1-9][0-9]*$'),
    price_known_at timestamptz NOT NULL,
    basis_sha256 text NOT NULL CHECK (basis_sha256 ~ '^[0-9a-f]{64}$'),
    recorded_at timestamptz NOT NULL,
    CONSTRAINT fuel_residual_priced CHECK ((state = 'PRICED') = (price_revision_id IS NOT NULL)
        AND (state = 'PRICED') = (price_value IS NOT NULL AND price_value >= 0 AND price_value < 'Infinity'::numeric)
        AND (state = 'PRICED') = (currency IS NOT NULL AND amount_low IS NOT NULL AND amount_high IS NOT NULL)
        AND (state = 'PRICED') = (price_reason IS NULL)),
    CONSTRAINT fuel_residual_finding_fk FOREIGN KEY (tenant_id, site_id, finding_id)
        REFERENCES finding(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_revision_fk FOREIGN KEY (tenant_id, site_id, finding_revision_id)
        REFERENCES finding_revision(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_price_fk FOREIGN KEY (tenant_id, site_id, price_revision_id)
        REFERENCES financial_assumption_revision(tenant_id, site_id, id),
    CONSTRAINT fuel_residual_window_fk FOREIGN KEY (fuel_balance_window_id) REFERENCES fuel_balance_window(id),
    CONSTRAINT fuel_residual_once UNIQUE (finding_revision_id),
    CONSTRAINT fuel_residual_scope_unique UNIQUE (tenant_id, site_id, id)
);
CREATE INDEX fuel_residual_finding ON fuel_residual_consequence_revision (tenant_id, site_id, finding_id, recorded_at);
CREATE TRIGGER fuel_residual_consequence_revision_immutable BEFORE UPDATE OR DELETE
    ON fuel_residual_consequence_revision FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
```
   - One consequence row per SUPPORTED Finding revision (`UNIQUE (finding_revision_id)`); none for a NO_LONGER_SUPPORTED revision.
   - The table is **not** a chain-event producer (`0044` `PRODUCERS` unchanged) and has no outbox.
3. **Downgrade:** `LOCK TABLE finding, finding_revision, fuel_residual_consequence_revision IN ACCESS EXCLUSIVE MODE`; refuse with `RuntimeError("0056 downgrade requires no fuel_balance Findings or fuel residual consequences")` if any `finding`/`finding_revision` row has `domain = 'fuel_balance'` or the table has a row; else drop the trigger, index and table and restore the two 0025 CHECKs.
4. No other object changes. The fuel-cost and cold triggers, `fuel_balance_window` and 0044 are untouched.

### 9j.4 Storage: window assessment, Finding, lifecycle (READ-based; copy the cold shapes)

**`PostgresAssessmentStore.fuel_balance_persist(c, window: FuelBalanceWindow, now) -> dict`** (`B/analytics/adapters/postgres_assessment_store.py`, on the caller's connection):
- `analytic_run`: `analytic_id 'fuel-balance-1'`, `model_version 'fuel-balance-1/v1'`, `window_start/end` = the window's, `knowledge_cutoff` = `window.recorded_at`, `input_sha256` = `window.input_sha256`, `cohort_status 'COMPLETE'`, `cohort_sha256` = sha256 of `[]` canonical, `cohort '[]'`, `configuration_sha256` = `window.input_sha256`, `foundation_revision_ids` = sorted distinct `[accuracy_revision_id, sfc_revision_id, no_load_revision_id]` from `window.terms`, `binding_set_revision_ids '[]'`, `role_coverage '{}'`, `watermarks '{}'`, `selection 'EXPLICIT'`, `job_id NULL`, `status 'COMPLETED'`, `started_at = completed_at = now`.
- `analytic_run_evidence`: one row per `window.evidence_ids`.
- `assessment_revision`: `assessment_key` = `f"{tank_asset_id}:{night_date}"`, `revision_no` = `window.revision`, `claim_level 'COMPLETE'`, `result` = `{"fuel_balance_window_id", "revision", "state", "residual_low", "residual_high", "gap_minutes", "limitations"}` (exact text), `evidence_ids` = the window's, `basis_sha256` = `window.input_sha256`; plus the `analytic_run_assessment` row (`scope 'WINDOW'`).
- **Idempotent:** if an `assessment_revision` with that `(site_id, 'fuel-balance-1', assessment_key, revision_no)` exists, return it unchanged (`analytic_run_basis_unique` already makes the run unique).
- Returns `{"revision_id", "run_id", "basis": window.input_sha256}` (cold's `persisted` shape).

**`PostgresFindingStore.fuel_apply(c, tenant_id, site_id, window, persisted, consequence_writer, now) -> list[UUID]`** (Finding store, beside `cold_apply`; module docstring line added "fuel_balance (DIESEL-K4a)"). Constants beside `COLD_MATCHER_VERSION`:
```python
FUEL_DOMAIN, FUEL_MECHANISM, FUEL_ANALYTIC = "fuel_balance", "UNEXPLAINED_FUEL", "fuel-balance-1"
FUEL_MATCHER_VERSION = "fuel-finding/1"      # finding_type = "UNEXPLAINED_FUEL@fuel-finding/1"
FUEL_MODEL_VERSION = "fuel-balance-1/v1"
```
- `finding_key` = `f"fuel:{tank_asset_id}:{night_date.isoformat()}"` (one Finding per tank night, ever).
- **Lifecycle (the only transitions; first match wins):**

| Held Finding for the key | Latest window revision `W` (as passed) | Write |
|---|---|---|
| none | `W.state == "UNEXPLAINED"` | insert `finding`; revision `OPENED` / `SUPPORTED`; consequence |
| none | anything else | nothing |
| held, its latest revision's `claim.fuel_balance_window_id == W.id` | any | nothing (idempotent) |
| held | `UNEXPLAINED` (a newer window revision) | revision `SUPPORT_CHANGED` / `SUPPORTED`; consequence |
| held | not `UNEXPLAINED` | revision `NO_LONGER_SUPPORTED` / `NO_LONGER_SUPPORTED`; no consequence |

- `finding` row: `domain 'fuel_balance'`, `mechanism 'UNEXPLAINED_FUEL'`, `analytic_id 'fuel-balance-1'`, `generator_asset_id NULL`, `subject_asset_id` = tank, `anchor_start` = `window_start`, `anchor_assessment_revision_id` = persisted, `cohort_sha256 NULL`, `matcher_version` = `FUEL_MATCHER_VERSION`, `recurs_after_finding_id NULL`, `split_from_finding_id NULL`, `opened_at = created_at = now`.
- `finding_revision` row: `domain 'fuel_balance'`, `revision_no` = max + 1, `claim_level 'COMPLETE'`, `title` = `finding_text.TITLE` (§9j.7), mechanism, matcher, analytic, `model_version` = `FUEL_MODEL_VERSION`, `assessment_revision_id`/`analytic_run_id` = persisted, `window_assessment_revision_id NULL`, `episode_start/end` = the window, the three minute fields NULL, `basis_sha256` = `input_sha256` = `W.input_sha256`, `support_sha256` = `sha256_json(sorted evidence ids)`, `cited_evidence_sha256` = cold's envelope-digest rule (`:685-687`), `created_at = now`.
  - `claim` (jsonb): `{"fuel_balance_window_id", "window_revision", "night_date", "tank_asset_id", "state", "residual_low", "residual_high", "gap_minutes", "gap_spans": [[from, to], ...] (UTC ISO), "limitations": [...codes], "parameter_version", "accuracy_l"}` (exact text from the window).
  - `limitations` (jsonb, sentences, fixed order): `finding_text.NOT_WHY`, `finding_text.margin_line(accuracy_l)`, then `finding_text.gap_line(spans, tz)` when `gap_minutes > 0`.
  - Links: `finding_revision_assessment` (primary, `'WINDOW'`) and `finding_revision_evidence` for each window evidence id, exactly as `cold_apply`.
- A SUPPORTED revision calls `consequence_writer(c, finding_id, revision_id, W, now)` in the same transaction (§9j.5).
- Re-running with the same window writes nothing (`finding_revision_basis_unique` and the "cites `W.id`" rule).

**Threads and maps (one row each; existing values byte-equal):**
- `B/chain/threads.py:31` `SUBJECT_COLUMN` gains `"fuel_balance": "subject_asset_id"`.
- `B/chain/read.py:25` `SITE_TYPE_OF_DOMAIN` gains `"fuel_balance": "MINIGRID"`.
- PRE-FLIGHT (c) lists every other dict, tuple or SQL `IN` list keyed by a Finding storage domain (`git grep -n "cold_chain" backend/assetops_backend`); each gets the `fuel_balance` entry its reader needs, or the builder states why none. A reader that raises on an unknown domain is a stop (S3).

### 9j.5 The money: `fuel-residual-1` (own basis, never added)

**`PostgresConsequenceStore.fuel_residual_append(c, tenant_id, site_id, finding_id, finding_revision_id, window, price, now)`** (`B/financials/adapters/postgres_consequence_store.py`, the sole consequence writer; guard list gains the table).
- **Litres** = `window.residual_low`, `window.residual_high` (exact `Fraction`, stored with `verification_rules.fmt`). Never rounded in storage.
- **Price** = `price_selection(tenant_id, site_id, window_start, window_end, known_at=window_end)` from `B/financials/composition.py:142-155` `build_trial_comparison_ports(url).price_selection` (the one diesel price over the whole window, `fuel_cost.select_window_price`, as known at the window end; §8.4). K4a calls the existing builder; it adds no price reader.
- **PRICED:** `amount_low = residual_low × price_value`, `amount_high = residual_high × price_value`, exact (`Fraction(residual) × Fraction(str(price_value))`), stored with `fmt`; `price_revision_id`, `price_assignment_id`, `price_value`, `currency` from the selection; `price_reason NULL`.
- **UNPRICED:** `price_reason` = the selection's reason (`NO_PRICE`, `PRICE_CONFLICT`, `PRICE_SPANS_WINDOW`, `PRICE_REVISION_MISSING`, `PRICE_UNIT_MISMATCH`, `PRICE_INVALID`); every price and amount field NULL.
- `price_known_at` = `window_end`; `basis_sha256` = `sha256_canonical({"model": "fuel-residual-1", "window_id", "residual": [lo, hi], "price": [revision_id, value, currency] or [reason]})`; `recorded_at = now`.
- **Never:** a row in `financial_consequence_revision`; a call to `fuel_cost`/`fuel_cost_v2` quantity code; an addition with any other money anywhere (stored, served or displayed). A price republished later does not re-price a stored row in v1 (after-the-demo list: "re-price unexplained-fuel consequences on a price correction").

**Read (`B/fuel_balance/model.py` additions, implemented by `PostgresFuelBalanceStore`, read-only, `REPEATABLE READ READ ONLY`):**
```python
@dataclass(frozen=True)
class FuelFinding:
    finding_id: UUID
    revision_id: UUID
    revision_no: int
    lifecycle: str                      # SUPPORTED | NO_LONGER_SUPPORTED
    night_date: date
    window: FuelBalanceWindow           # the revision the Finding revision cites
    consequence: Mapping[str, Any] | None   # the row's columns (exact text), None when NO_LONGER_SUPPORTED
    created_at: datetime

class FuelFindingReadPort(Protocol):
    def fuel_findings(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                      known_at: datetime | None) -> tuple[FuelFinding, ...]: ...   # latest revision per Finding at known_at, window intersecting [lo, hi), by night_date
    def fuel_finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID,
                     known_at: datetime | None) -> FuelFinding | None: ...
```
- `known_at None` = now. `lo < hi`, UTC-aware, else `ValueError("fuel findings need lo < hi and UTC instants")`.

### 9j.6 Service and CLI (explicit, never by itself)

- **`B/fuel_balance/findings_service.py`**, `FuelFindingService(store_factory).raise_night(tenant_id, site_id, night_date) -> RaiseResult(status, finding_id|None, revision_id|None)`, status ∈ `OPENED`, `REVISED`, `WITHDRAWN`, `UNCHANGED`, `NO_FINDING`, `NO_WINDOW`:
  1. One transaction; `pg_advisory_xact_lock(hashtext('fuel-finding:' || site_id || ':' || night_date))`.
  2. The latest window revision for the night, as known now (`windows(...)` with `known_at` = the transaction's `clock_timestamp()` or the composition's test-only clock override). None → `NO_WINDOW`.
  3. If a Finding must be written (§9j.4 table): `fuel_balance_persist`, then `fuel_apply` (which calls `fuel_residual_append`), on the same connection.
  - The transaction owner mirrors the cold worker (`B/analytics/assessment_worker.py`, the guard's `$coldTransactionOwner`): PRE-FLIGHT (a) names its engine/connection pattern with file:line; K4a copies it in `findings_service.py` and joins the guard's owner list (membership only).
- **Composition** `B/fuel_balance/composition.py` gains `build_fuel_finding_service(database_url, *, test_db_clock_override=None)`, wiring the three stores and the price selection. Test-only clock: constructor-only, as K3.
- **CLI** in `B/fuel_balance/worker.py`: `python -m assetops_backend.fuel_balance.worker raise --site <code> --from <local date> --to <local date>`; one JSON line per night `{"site_code", "night_date", "status", "finding_id", "revision_id"}`; any refusal exits 2 after printing it. `assess` is unchanged.
- **K7's prepare order (for K7's card):** per story day: accept → `assess` the closed nights → `raise` the same nights → the existing threads step (`B/chain/backfill.py:33` `run_threads`, as the Kobo prepare does). The board reads PARTIAL until the threads consumer has consumed the `finding.revised` event (`postgres_chain_read.py:48-54`, R8); that is correct behaviour.

### 9j.7 Client wording (K4a literals; `B/fuel_balance/finding_text.py`, pure, no I/O)

Rules: H1–H5 (§8.2). **H4: none of theft, stolen, stole, siphon, pilfer, and nothing implying them.** The word "running" is avoided (guard V/N's "run" rule; `mini.py:71` precedent). Numbers are formatted here, never in the browser. Litres: one decimal, half-even on the exact `Fraction` (`Decimal(round(F * 10)) / 10`, `:.1f`). Money: `chain.vocabulary.money2` on the exact amount. Price `{p}`: `money2(price_value)`. `{date}`: `f"{d.day} {d:%b}"` of `night_date` (the board's `_short_day` form, e.g. "4 Oct"). Times `{a}`, `{b}`: Site-local `HH:MM` (24 h).

```python
TITLE = "Unexplained fuel overnight"
CLAIM_LINE = ("About {lo}–{hi} L left the tank on the night of {date} (6 pm to noon) that the generator's "
              "modelled use and the recorded deliveries don't explain.")
GAP_LINE = "The tank sensor sent no readings {spans}."          # SPAN joined with ", and "
SPAN = "from {a} to {b}"
MONEY_LINE = ("Worth about {lo_m}–{hi_m} {cur} at your declared {p} {cur} per litre "
              "(a modelled range that includes the stated margin)")
UNPRICED_NO_PRICE = "Not available yet · no diesel price declared for this night"
UNPRICED_PRICE_CHANGES = "Not available yet · the declared diesel price changes during this night"   # PRICE_CONFLICT, PRICE_SPANS_WINDOW
UNPRICED_OTHER = "Not available yet · the declared diesel price could not be used for this night"   # any other reason
NOT_WHY = "This does not say why the fuel left the tank."
MARGIN_LINE = ("The range allows for the tank sensor's declared accuracy of {a} L at each reading, 10 % either way "
               "on the generator's modelled use, and 1 % on each recorded delivery.")
NO_LONGER = "A later check of this night no longer finds unexplained fuel."
```
- `finding_lines(ff: FuelFinding, tz) -> {"title", "claim", "gap" | None, "money", "not_why", "margin", "no_longer" | None}`: SUPPORTED → `claim`, `gap` (only if `gap_minutes > 0`), `money` (MONEY_LINE or the UNPRICED literal), `not_why`, `margin`; NO_LONGER_SUPPORTED → `title`, `no_longer`, `not_why` only.
- **Expected values on Kisiwa night 4 (computed from F0's committed exact bands and price v1 1.25 USD; K4a asserts them, never forces them):** "About 95.7–144.3 L left the tank on the night of 4 Oct (6 pm to noon) …"; "The tank sensor sent no readings from 00:45 to 02:30."; "Worth about 119.57–180.43 USD at your declared 1.25 USD per litre (a modelled range that includes the stated margin)". If the stored band differs from F0's, that is K3's parity (already proven), not a K4a choice: K4a's test reads the stored window, so a mismatch with these strings is stop S1.
- **The two "theft" strings (`F/sites/MiniPerformance.tsx`), MD-FUEL-K-2, on every Site:**
  - `FUEL_NOTICE` (`:1310-1311`) becomes: "Unexplained fuel is fuel that left the tank and that the generator's modelled use and the recorded deliveries don't account for, within a stated margin. It does not say why the fuel left, and it is never added to the generator's possible extra fuel."
  - The RESIDUAL row (`:1343`) becomes: "Needs every term with a supported range; never says why fuel left".
  - Header comment at each: `// MOCK DEVIATION MD-FUEL-K-2 (DIESEL-1-R3j): v69 :627-628 say "never infer theft" / "cannot establish theft"; owner 2026-11-07: "'Unexplained fuel', never 'theft'".`
  - These are the only Kobo Fuel-page bytes that change. `F/sites/__tests__/miniFuelRoutes.test.tsx:188`, `:191` take the new literals (import the constant for `:191`; retype `:188`'s row literal).

### 9j.8 K4a tests (localised; no full suite). Every "must fail" names the mutation the reviewer applies to a scratch copy.

**A. L0 `backend/tests/test_k4a_fuel_finding_rules.py` (no DB)**
1. **Text, night 4.** `finding_lines` on a FuelFinding built from `probe-result.json` night 4 `readings` band (exact), `accuracy_l = 10`, price 1.25 USD, `Africa/Dar_es_Salaam`: the three expected strings of §9j.7 exactly. Must fail if litres round half-up at a `.x5` case (add a synthetic band `[1.25, 2.35]` → "1.2–2.4"), or if `money2` is replaced by `round(x, 2)` on a float.
2. **Gap.** No gap → `gap is None`; two spans → "from 00:45 to 02:30, and from 03:00 to 04:10"; times in Site time, not UTC (must fail if UTC).
3. **Unpriced.** Each reason maps to its literal; `money` never contains a digit when UNPRICED.
4. **Wording guard (local).** Every K4a literal and both new `MiniPerformance` strings, lower-cased, contain none of `theft`, `stolen`, `stole`, `siphon`, `pilfer`; and `F/sites/MiniPerformance.tsx` (read as text) contains none of them. Must fail if either old string is restored.
5. **Amounts exact.** For the night-4 band and 1.25: `amount_low == residual_low × 5/4` exactly, stored text round-trips through `fmt`/`parse`; must fail if amounts are computed from the 0.1-L display litres (95.7 × 1.25 = 119.625 → "119.62", not "119.57").
6. **Never summed (static).** No module under `B/fuel_balance/` and no `fuel_residual_*` function imports `fuel_cost_v2`, `financial_consequence`, or calls `sum(`/`+` over two consequence amounts (AST check over the new files: no `BinOp(Add)` whose operands both name an `amount_*`).
7. **Lifecycle table** (§9j.4) on a fake store: all five rows; the idempotent re-run writes nothing.
8. **K3 L1 (follow-up):** in `backend/tests/test_tfc2.py` `test_window_idle_seconds_exclude_the_stop_slot`, one more case: RUNNING at 0–11, **FAILED** at the window end → 3300. Must fail with `NOT_RUNNING_STATES = {"STOPPED"}`.

**B. L2 `backend/tests/test_k4a_fuel_finding_postgres.py`, own `assetops_k4_test`** (Kobo imported as K3's B does; synthetic windows through `PostgresFuelBalanceStore.append` with the test clock):
1. **0056** up/down/up on empty tables: the two recreated CHECKs' text (pg_get_constraintdef) equals 0025's plus the one arm; the consequence table's columns, constraints, index and trigger; downgrade refused with a `fuel_balance` Finding row and with a consequence row; single alembic head **head-agnostic** (below); UPDATE/DELETE refused; raw inserts violating `fuel_residual_priced` (priced without amount; unpriced with a price) fail; a `fuel_balance` Finding with a `generator_asset_id` fails the subject CHECK.
2. **Kobo's existing Findings byte-equal:** `domain = 'mini_grid'` rows and the fuel-cost trigger unchanged; inserting a `fuel_balance` revision adds **no** `financial_consequence_work` row (must fail if the trigger's `WHEN` is dropped).
3. **Raise lifecycle on a stored window** (tank = Kobo's tank, accuracy declared by the test): UNEXPLAINED → OPENED + one PRICED consequence; same again → UNCHANGED; a newer WITHIN_MARGIN revision → WITHDRAWN (`NO_LONGER_SUPPORTED`, no consequence); a later UNEXPLAINED revision of a second night → a second Finding on the **same** thread after `run_threads` (occurrence 2). No price declared → UNPRICED `NO_PRICE`.
4. **Threads:** after `raise` and `run_threads`, one `finding_thread` with mechanism `UNEXPLAINED_FUEL`, `subject_kind 'ASSET'`, `subject_ref` = tank id, `finding_type 'UNEXPLAINED_FUEL@fuel-finding/1'`; the R8 unsettled read is False after the consumer ran and True before.
5. **Reads:** `fuel_findings`/`fuel_finding` as known before and after the WITHDRAWN revision.
6. **Head-agnostic edit (K3 residual risk):** `backend/tests/test_k3_fuel_balance_postgres.py:183-187` `test_b1_single_alembic_head` asserts `script.get_heads() == [alembic_head()]`, `head(engine) == alembic_head()`, and `script.get_revision(MIGRATION).down_revision == PREVIOUS`; it no longer names 0055 as head. K4a's own head test is written the same way. The packet lists these lines as a head-bookkeeping edit (the §9g.5 precedent), not a behaviour change.

**C. L2 parity `host/tests/test_k4a_kisiwa_night4.py`, own `assetops_k4_test`** (machine idle, free RAM checked first; about 6–8 min): K3 part C's module fixture and steps for **night 4 only** (§9d.6 C, reusing its helpers by import), then `assess` and `raise` night 4 at `run_end + 30 min` through `build_fuel_finding_service`, then `run_threads`:
- one Finding, SUPPORTED; its claim's band equals the stored window's exactly and equals F0's night-4 `readings` band within K3's 1/100000 L;
- consequence PRICED, price revision = Kisiwa diesel v1, `amount_* = residual_* × 1.25` exactly;
- `finding_lines` gives the §9j.7 expected strings;
- **KIS-4 pure check** (below) passes on this DB;
- no `financial_consequence_revision` row cites this Finding.

**Must stay green unchanged:** K3's L0/L2 (except the head edit), `test_k2_*`, `test_tfc2.py` existing cases, `test_fuel_cost_v2.py`, the cold and EV Finding store tests, `test_w401_work_service_postgres.py`, CH-2 thread tests (`test_ch2_*`), and both probe `--check`s. Any behaviour edit is stop S5.

**Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` if no venv), `tools\check-agent-workflow.ps1`, run directly, no `-ExecutionPolicy`. Guard-list joins (the consequence writer's table list, the transaction owner, rule-8 readers) are membership only, listed in the packet with the reason.

### 9j.9 K4a finish row, files, pre-flight, stops, size, branch

**Finish row KIS-4** (written now; runs at E3). Pure logic `kis4(windows, findings, consequences, prices, dispatch_consequences)` in `T/demo_combined_rows.py`, wired in `T/demo_combined_finish.py` after the PV-A row; L0 self-test with pass and fail bodies:
- every SUPPORTED Kisiwa fuel Finding's consequence litres equal its cited window's `residual_low/high` exactly;
- PRICED amounts equal litres × the stored price value exactly, and the stored price revision equals a re-run of `select_window_price` at `known_at = window_end`;
- no `financial_consequence_revision` row has this Finding's id;
- no stored or served amount equals (as `Decimal`, two places) the sum of a fuel amount with any Kisiwa dispatch `amount_high`, or of two fuel amounts.
- §8.7's KIS-3 and KIS-5 stay K9's.

**Files (approved list; anything else is stop S6):**
1. `backend/migrations/versions/0056_unexplained_fuel_finding.py`
2. `B/analytics/adapters/postgres_assessment_store.py` (`fuel_balance_persist` only)
3. `B/analytics/adapters/postgres_finding_store.py` (constants, `fuel_apply` and its private helpers only)
4. `B/financials/adapters/postgres_consequence_store.py` (`fuel_residual_append` only)
5. `B/fuel_balance/model.py` (§9j.5 read types), `adapters/postgres_fuel_balance_store.py` (the two reads), `findings_service.py` (new), `finding_text.py` (new), `composition.py`, `worker.py` (`raise`), `rules.py` (docstring only: K3 L2, name `idle_slot` and R3h at `:9-10`, wrap `:174`)
6. `B/chain/threads.py:31`, `B/chain/read.py:25`, and the PRE-FLIGHT (c) maps (one entry each)
7. `F/sites/MiniPerformance.tsx` (the two strings), `F/sites/__tests__/miniFuelRoutes.test.tsx` (`:188`, `:191`)
8. `T/demo_combined_rows.py`, `T/demo_combined_finish.py` (KIS-4), `T/checks/configuration-persistence.ps1` (list membership only)
9. Tests: §9j.8 A, B, C; `backend/tests/test_tfc2.py` (one case); `backend/tests/test_k3_fuel_balance_postgres.py` (head lines); `backend/tests/test_out_b2_vocabulary.py` (K4a literals added to the scan list).

**PRE-FLIGHT (no code first; batch every question in one message):**
- (a) The cold worker's shared-transaction pattern (`assessment_worker.py`, file:line) and how `cold_apply` receives its connection; confirm `fuel_apply` can be called the same way from `findings_service.py`.
- (b) Every reader of `finding`/`finding_revision` that would see a `fuel_balance` row and dereference a dispatch-only field (candidate minutes, `generator_asset_id`, the dispatch claim keys) without a domain filter: list file:line and state whether it filters by domain/analytic. In particular the Finding detail API (`B/finding_api.py`), the Findings index (`index_snapshot`), `estate/placement.py`, `estate/coverage.py`, `work/site_index.py:186`, `work/adapters/postgres_work_read.py:303`, `chain/lookup.py`.
- (c) The `git grep -n "cold_chain" backend/assetops_backend` map list (§9j.4).
- (d) Whether the lifecycle runner (`chain/lifecycle_run.py`, `config/chain/thread-lifecycle-v1.json` `clean_day_measures`) raises for a mechanism with no `clean_day_measures` entry. If it does, that is stop S4 (the Architect rules; K4a does not add a measure).
- (e) The guard lists the new writers, owner and table must join.

**Stops (report to the Architect; never design around them):**
- **S1** a §9j.8 C item differs (band, amount, text). Never edit the probe, its result, K3's parameters or the price.
- **S2** a write needs a NOT NULL relaxed, a dispatch column filled with an invented value, or a row in `financial_consequence_revision`.
- **S3** a reader in PRE-FLIGHT (b)/(c) raises or mis-renders on a `fuel_balance` row and is not fixed by one map entry.
- **S4** PRE-FLIGHT (d) shows the lifecycle runner needs a measure.
- **S5** an existing test needs a behaviour change (head bookkeeping excepted, §9j.8 B6).
- **S6** a file outside the approved list, or any Cold/EV byte change, or a Kobo board/golden change.
- **S7** more than 1.6 units.

**Dependencies, start, branch, DB, size:**
- Depends on K3 merged (yes, `ce03ae246`). Needs nothing from K0, K5, A3 or K6. **K4a can start now**, on lane 3.
- Branch `task/DIESEL-K4a-unexplained-fuel-finding`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k4a`, from main at or after `801efc0e2`. Opus first build and first review. `git add -f` of explicit paths.
- **DB: only `assetops_k4_test`** (and its harness clones). Never `assetops_demo3_full_test` or any other DB. No prepare, tick, `serve` or suite. Part C when the machine is idle.
- **Size 1.4** (range 1.2–1.6): migration 0.25; three store methods 0.4; service, composition, CLI, price 0.2; text, maps, the two strings, K3 Lows 0.1; tests A+B 0.25; C and KIS-4 0.15; pre-flight 0.05.
- Reading budget: this §9j.1–§9j.9; §9d.4–§9d.5; `0009_finding_store.py:32-110`; `0022_w2_cold_assessment.py:40-80`, `:212-225`; `0025_w2_ev_session.py:40-80`, `:468-479`; `0011_financial_consequences.py:43-120`; `postgres_finding_store.py:39-50`, `:181-247`, `:586-711`; `postgres_assessment_store.py` (the cold persist it mirrors; pre-flight names lines); `B/financials/composition.py:134-155`; `B/financials/fuel_cost.py:440-464`; `B/chain/threads.py:1-180`; `B/chain/backfill.py:33-60`; `B/chain/adapters/postgres_chain_read.py:27-54`; `F/sites/MiniPerformance.tsx:1305-1345`; `host/tests/test_k3_fuel_balance_parity.py`.

### 9j.10 K4b: what it delivers (lane 1, after K4a merges; off the critical path)

- The Kisiwa board's **Protect** row shows the unexplained-fuel Finding (issue, thread line, in-hand/earlier Actions), a **"Fuel in the tank"** contributor and the new outcome **MG-8 "Fuel accounted for"**.
- The Portfolio **Protect** card lists each Site's unexplained-fuel line, never summed.
- COH-17 row **UF1** and its self-tests; the KIS-8 Protect-line half.
- **Unchanged:** every Cold and EV byte; Kobo's rows except the one MG-8 outcome entry (N/A); the Optimize row's "Fuel" contributor (`NO_FUEL_BALANCE`); the Grow, Optimize and Assure cards; PV-1's lines.

### 9j.11 K4b design (literals verbatim)

**Outcome MG-8 (`B/outcomes/catalogue.py`, `outcome_map.py`):**
- Catalogue, after MG-4 (PROTECT order MG-5, MG-4, MG-8): `_o("MG-8", MINI, "PROTECT_ASSET", "Fuel accounted for")`, measured.
- Map: `"FINDING:UNEXPLAINED_FUEL": (("MG-8",), ())`. No `@` alias changes.
- **Applicability:** `SiteFacts` gains `not_applicable: frozenset[str] = frozenset()` (last field, after `verified_values`). `board._row` and its `state_on` pass `applicable=o.key not in facts.not_applicable` to `outcome_state`. Cold/EV never set it.
- `mini.compose`: `not_applicable = {"MG-8"}` when the Site has **no** stored fuel-balance window at all as known at the board cutoff (Kobo); else empty. `settled["MG-8"]` = the window for **night D − 1** (the night that ends on board day D) exists as known and is not `NOT_ASSESSED`, and the fuel Finding read succeeded (`findings_ok` rule).
- Kobo's Protect row therefore gains exactly one `outcomes` entry `{"key": "MG-8", "label": "Fuel accounted for", "state": "NOT_APPLICABLE", "reason": "CONFIGURATION_NOT_APPLICABLE"}`; its state, tone, lead, headline and every other field are unchanged (NOT_APPLICABLE ranks last, `status.py:34`).

**Board reads (`B/site_outcomes/mini.py`, `read.py`):**
- `MiniPorts` gains, last and defaulted: `fuel_windows: Callable[[date, date], Any] = lambda lo, hi: ()` (K3's `windows`, tank resolved by the port) and `fuel_findings: Callable[[datetime, datetime], Any] = lambda lo, hi: ()` (K4a's `fuel_findings` at the board cutoff). Bound in `read.py` `mini_ports` from the fuel-balance composition; a failure is recorded by `Reads` (board PARTIAL), never a "0" claim.
- `FindingFact`s for fuel Findings are built from `fuel_findings(work_lo, end)` plus their thread rows (the chain reader's thread for `subject_ref` = tank) and **appended** to `findings`. `heads`, `lead_finding`, `money_head`, `lead` (the COST lead and the Trial option) stay on **dispatch heads only**: `lead` is chosen from Findings whose `mechanism == "GENERATOR_SUPPORT_CANDIDATE"`.
- Title on the board: `FINDING_TITLE_BY_MECHANISM = {"UNEXPLAINED_FUEL": {"SUPPORTED": "Unexplained fuel overnight", "NO_LONGER_SUPPORTED": "Unexplained fuel no longer supported by the latest check"}}`; the dispatch `FINDING_TITLE` map is unchanged and used for every other mechanism.
- Link: `refs.finding_ref(c, finding_id)` (K5 renders the page).

**Protect contributor "Fuel in the tank" (key `fuel_stock`), only on a Site with any stored window; placed after "Backup readiness".** For night D − 1's window `W` (latest as known):

| Case | Text | Chip |
|---|---|---|
| no window for the night | `FUEL_NO_WINDOW = "Not available yet · no fuel check for the night of {date}"` | none |
| `NOT_ASSESSED` | `FUEL_NOT_CHECKED = "Not available yet · the night of {date} could not be checked: {why}"` | `UNKNOWN_CHIP` |
| `WITHIN_MARGIN` | `FUEL_WITHIN = "Accounted for within the margin on the night of {date}"` | `HIGH_CHIP` |
| `BELOW_MATERIALITY` | `FUEL_BELOW = "About {lo}–{hi} L unexplained on the night of {date}, below the 40 L the check flags"` | `UNKNOWN_CHIP` |
| `UNEXPLAINED` | `FUEL_UNEXPLAINED = "About {lo}–{hi} L unexplained on the night of {date}"` | `{"label": "Limited", "tone": "amber"}` (the existing `PLACEMENT_CHIP["LIMITED"]`) |
| `EXCESS` | `FUEL_EXCESS = "More fuel in the tank than recorded on the night of {date}; a delivery may be unrecorded"` | `UNKNOWN_CHIP` |

`{why}` from `FUEL_REASON_WORDS = {"NO_SENSOR_ACCURACY": "no tank sensor accuracy declared", "SFC_MISSING": "no generator fuel rate declared", "NO_LOAD_RATE_MISSING": "no generator no-load rate declared", "MISSING_OPENING": "no tank reading at 6 pm", "MISSING_CLOSING": "no tank reading at noon", "FUEL_LEVEL_CONFLICT": "two different tank readings at the same time", "GENERATOR_KWH_UNKNOWN": "generator power readings incomplete", "IDLE_SECONDS_UNKNOWN": "generator state readings incomplete"}`. Litres and dates as §9j.7. Link: `refs.evidence_ref(c, "fuel")`.

**Board node and the Portfolio Protect line (PV-1's pattern):**
- `SiteFacts` gains `unexplained_fuel: tuple[Mapping[str, Any], ...] = ()`; `_row` adds `row["nodes"] = {**row["nodes"], "unexplained_fuel": [...]}` for `PROTECT_ASSET` only when non-empty (absent key = `[]`; every other board byte-equal).
- Entries: every fuel Finding whose latest revision (as known) is SUPPORTED and whose window ends inside the board's work window, by `night_date`: `{"key": finding_id, "night_date", "basis": "UNEXPLAINED_FUEL_AT_DECLARED_PRICE", "litres_low", "litres_high" (0.1 text), "amount_low", "amount_high" (money2 text or null), "currency" (or null), "text"}` with
  - `FUEL_LINE = "Unexplained fuel on the night of {date}: about {lo}–{hi} L, {lo_m}–{hi_m} {cur} at your declared price (a modelled range, shown on its own)"`;
  - unpriced: `FUEL_LINE_UNPRICED = "Unexplained fuel on the night of {date}: about {lo}–{hi} L (no money estimate)"`.
- `B/chain/vocabulary.py` `CARD_TEXT`, under Protect: `"protect.fuel_line": "{site} · {text}"`, `"protect.fuel_separate": "Unexplained fuel is shown on its own and never added to any other money"`.
- `portfolio_cards` (`read.py:794-837`): the `PROTECT` card gains `"fuel_lines"` (Site order, then `night_date`) and `"fuel_note"` (`protect.fuel_separate` iff lines, else `None`). **No total, no sum, no arithmetic across entries or with any other card.** Every other Protect key is byte-equal.
- Frontend (`F/estate/estateClient.ts`, `F/estate/PortfolioOutcomes.tsx`): `EstatePortfolioCard` gains `fuel_lines?: string[]; fuel_note?: string | null;`; rendered on the Protect card after `c.detail`, as PV-1 renders values: `<p className="oc-pfnote" data-portfolio-card-fuel-line>` per line, then `data-portfolio-card-fuel-note`. Server text only; no new CSS.

**Chain vocabulary and claims:** PRE-FLIGHT (b) confirms that `chain/claims.py`'s Protect claim (`SITES_DISRUPTED`) counts only service-disruption evidence and not an MG-8 Finding. If it would count it, K4b excludes `UNEXPLAINED_FUEL` from that claim's input, with a test. The open/in-hand/verified thread counts (`threads.classify`) include the fuel thread unchanged: that is correct.

**MOCK DEVIATIONs (header comment at each render or literal, and a packet row each):**
- **MD-FUEL-K4-1** (K4a text, K4b board issue): a Finding kind "Unexplained fuel overnight" that v69 does not have; v69 `:623-630` shows the fuel balance with no residual conclusion and defers "theft detection" (`:630`).
- **MD-FUEL-K4-2** (K4b): the Protect row gains outcome "Fuel accounted for" and contributor "Fuel in the tank"; v69's mini readiness lists "Fuel balance · None · No fuel balance" (`:345`) and no Protect fuel outcome.
- **MD-FUEL-K4-3** (K4b): the Portfolio Protect card lists unexplained-fuel lines; v69 `:131`, `:482` forbid a combined total, so each is its own line (as MD-FUEL-PV1-1).
- **MD-FUEL-K-2** (K4a): §9j.7.

### 9j.12 K4b coherence and finish rows

- **COH-17 row UF1** (`T/checks/chain_coherence.py`, new `coh17_fuel(w, summary, files, tally)` called right after `coh17_values`):
  - (i) `cards.PROTECT_ASSET.fuel_lines` equals the list rebuilt from `summary.sites[]` Protect `nodes.unexplained_fuel` with `protect.fuel_line` imported from `CARD_TEXT`;
  - (ii) for every same-currency pair drawn from {all fuel amounts} ∪ {Optimize claim amounts} ∪ {Assure `verified_values` amounts}, with at least one fuel amount in the pair, `f"{Decimal(a) + Decimal(b):.2f}"` appears in no string of any Portfolio card (walk all four cards' JSON);
  - (iii) `fuel_note` is `fuel_separate` iff lines;
  - an older bundle without the keys is skipped and counted.
  - Self-tests in `T/checks/test_chain_coherence.py`: pass (two lines); fail (i); fail (ii) with a fuel+Optimize sum in the Protect `detail`; fail (ii) with a fuel+fuel sum; fail (iii); skipped.
- **Finish row KIS-8a** (Protect half of §8.7 KIS-8; written now, runs at E3; `T/demo_combined_rows.py` `kis8_protect`, wired after KIS-4): on the week estate summary that contains Kisiwa's S+0 board, the Protect card's `fuel_lines` contains `card_text("protect.fuel_line", site=<Kisiwa name>, text=<the board node text>)` for night 4, and UF1 passes on that summary. L0 self-test pass/fail. The wording-guard half of KIS-8 stays K9's.

### 9j.13 K4b tests, files, pre-flight, stops, size, branch

**Tests (L0 unless named):**
- `backend/tests/test_k4b_protect_fuel.py` (fake ports): MG-8 NOT_APPLICABLE with no windows, UNKNOWN when night D−1 is NOT_ASSESSED, NEEDS_ATTENTION with an open SUPPORTED fuel Finding (rule 2), WATCH once its thread is ACTION_IN_HAND/applied; the six contributor cases and chips; the issue on Protect and on no other row; the COST lead and Trial option unchanged with and without a fuel Finding (must fail if `lead` is chosen from all Findings); thread line on Protect only; node present only when non-empty; Kobo Protect row with no windows equals main's except the MG-8 entry (must fail on any other diff).
- `test_pv1_value_lines.py`, `test_ch6b2_portfolio_cards.py`: Grow, Optimize, Assure byte-equal; Protect gains only `fuel_lines`/`fuel_note`; no card string contains a fuel sum.
- Goldens (`test_ch5a2_contract.py` and any mini board/estate goldens) regenerated by the DRIFT-R1 §2.2 procedure. **Acceptance:** the diff against main is only (a) each mini Protect row's `outcomes` gaining the MG-8 N/A entry and (b) `cards.PROTECT_ASSET` gaining `"fuel_lines": []` and `"fuel_note": null`. Anything else is stop S-b.
- `backend/tests/test_out_b2_vocabulary.py` gains every K4b literal; `test_out_b3_cold_ev.py` unchanged; `test_out_b4_imports.py` unchanged (no new import in `site_outcomes/` beyond the port call).
- Frontend: `F/estate/__tests__/estatePortfolio.test.tsx` and `portfolioFixtures.ts` (Protect renders lines and note; absent keys render nothing); the board's outcome list renders "Fuel accounted for" with its state label from the server (no new client words); `tsc`.
- Guards: A, W, N, V, M, chain coherence, `node tools/checks/frontend-hardwiring.mjs` (no rise); fast tier for the edited backend files. **Not run:** full suite, prepare.

**Files (approved list):** `B/outcomes/catalogue.py`, `B/outcomes/outcome_map.py`, `B/site_outcomes/board.py` (`SiteFacts` two fields, `_row` applicability and the node), `B/site_outcomes/mini.py`, `B/site_outcomes/read.py` (ports, `portfolio_cards` Protect keys), `B/chain/vocabulary.py` (two `CARD_TEXT` entries), `B/chain/claims.py` only if PRE-FLIGHT (b) requires, `F/estate/estateClient.ts`, `F/estate/PortfolioOutcomes.tsx`, `T/checks/chain_coherence.py`, `T/checks/test_chain_coherence.py`, `T/demo_combined_rows.py`, `T/demo_combined_finish.py`, the tests and goldens above.

**PRE-FLIGHT:** (a) every consumer of the mini catalogue list or `SITE_OUTCOMES` that enumerates outcomes (counts, frontend words, COH rows, estate categories), file:line, and what MG-8 does there; (b) the `SITES_DISRUPTED` claim input (above); (c) the chain reader call that gives a fuel Finding's thread view for `FindingFact.thread`/`lifecycle_view`; (d) whether A3 has merged (it edits `mini.py`/`board.py`; whichever of A3 and K4b merges second merges main first, PV-1-R's order rule).

**Stops:** **S-a** a guard rejects a literal (report the message; never reword silently); **S-b** a golden or Kobo diff beyond the acceptance above, or any Cold/EV change; **S-c** MG-8 changes Kobo's Protect row state, tone, lead or headline; **S-d** a placement needs a second placement path outside the outcome map; **S-e** more than 1.2 units.

**Dependencies, start, branch, DB, size:**
- Depends on **K4a merged**; PV-1, MB-1, CH-5d1 merged (yes). A3 is not a blocker (order rule above).
- Lane 1, after K5's first build (or whichever lane-1 builder frees first). Branch `task/DIESEL-K4b-protect-fuel`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k4b`. DB only `assetops_k4b_test` if a Postgres golden check needs one; never `assetops_demo3_full_test`. Opus first build and review.
- **Size 1.0** (range 0.85–1.2): MG-8 and applicability 0.2; board reads, Finding merge, lead restriction, titles 0.25; contributor, node, card, frontend 0.25; UF1, KIS-8a 0.1; goldens and tests 0.2.

### 9j.14 Effects on other cards

- **K5:** owns the Finding page panel (`finding_lines` server-composed, served by K5's own read route), the Findings-list entry for the fuel Finding and the Fuel page in window mode. K5 **must not** edit `FUEL_NOTICE` or the RESIDUAL row (K4a owns them). If K5 builds before K4a merges, it merges main before its packet.
- **K6:** raises its W1 Action from the fuel Finding's thread. Its card must confirm (pre-flight) that the Action path accepts an origin Finding of domain `fuel_balance` (`action.origin_finding_id` is a plain FK to `finding`; any service-level check for a dispatch Finding is K6's to rule on). K6 needs K4a only, not K4b.
- **K7:** prepare order of §9j.6; the night-4 Finding is raised after night 4 is assessed.
- **K8:** the Portfolio Protect line moved to K4b, so K8 = **0.85** (plus §9c.4's device-id copy risk, +0.1–0.25). K8 keeps the four-Site lists, COH re-expectations and the all-26 recapture, which now also captures the reworded Fuel notice and Kobo's MG-8 N/A entry.
- **K9:** the repo-wide wording guard (H4) stays K9's; K4a's local test is not a substitute.

### 9j.15 Sizes, critical path, tripwire, date

- **K4 = K4a 1.4 + K4b 1.0 = 2.4** (§9.5 had 2.0; +0.4: the assessment-backed Finding domain, the own consequence table, MG-8 and the Protect card line). **K8 −0.15** (line moved). Net **+0.25**, reported, not absorbed (contingency spent, §9h.8): **Kisiwa total 17.35 → 17.6**.
- **Critical path** (F0r 0.65 → K1 1.25 → K3 1.75 already spent = 3.65), then **K4a 1.4 → K6 1.5 → K7 freeze 0.5 → K8 captures 0.25 → K9 1.0 ≈ 8.3 lane-units**. The lane-1 branch (K4a → K4b 1.0 → K8 code 0.85–1.1 → captures → K9) is about 8.15–8.4 and joins at the captures. **The path is about 8.3–8.4, below the 9.75 tripwire (8.9 before this ruling). No cut is needed and no owner question arises.**
- K0 keeps its float (needed by K7's data part, which runs beside K4a and K6).
- **Demo date:** unchanged at about +3.25 working days (it may come in by up to about 0.2 day, because the split takes K4b off the critical path).
- **Plan HTML rows (coordinator):** the DIESEL-1-R3 build-units row becomes 17.6 with "K4a 1.4, K4b 1.0, K8 0.85"; the lanes figure shows K4a on lane 3 before K6 and K4b on lane 1 between K5 and K8; the rulings table gains "DIESEL-1-R3j: K4 split; unexplained-fuel Finding as a `fuel_balance` domain on the cold/EV pattern; own consequence table `fuel-residual-1` (0056), never summed; outcome MG-8 'Fuel accounted for' on Protect (Kobo N/A); Portfolio Protect line moved from K8; the two 'theft' strings reworded in K4a"; the after-the-demo list gains "re-price unexplained-fuel consequences on a price correction" and "fuel-finding tick stage".

### 9j.16 Owner questions

None. For the owner's information, in plain words: the "unexplained fuel" finding gets its own place under "Protect asset & capital", with a new line "Fuel accounted for". Sites that cannot check their fuel yet, such as Kobo, show that line as not applicable, and nothing else on their screens changes. The fuel's dollar value is always shown on its own and is never added to any other figure. The plan is about a quarter-unit bigger, but splitting the unit lets more of it run in parallel, so the demo date does not move.

## 9k. Ruling DIESEL-1-R3k: K4a pre-flight stop (two unfiltered Finding readers)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `662b2cf91` (R3j). K4a stopped at pre-flight with no code written (worktree `AssetOpsV1-k4a` clean).
- READ = the Architect read the code at `662b2cf91`; nothing was run or measured.
- **This ruling amends §9j.1(2), §9j.8 and §9j.9 for K4a.** Read it alongside §9j.1–§9j.9. Everything not named here stands.

### 9k.1 What the stop found (READ, confirmed)

1. `PostgresFindingStore.findings_over` (`B/analytics/adapters/postgres_finding_store.py:460-474`) reads every `finding_revision` of a Site, with no domain or analytic filter. Its three callers are all dispatch reads:
   - `scheduling/upstream.py:139`. It feeds the served mini Site overview (`site_overview/read.py:159-181`), where a fuel Finding could become the DISCOVERED Finding and add a CONSEQUENCE_PENDING blocker.
   - `analytics/finding_read.py:630` `window_state`, which serves `GET /api/sites/{code}/finding-windows/{day}` (`finding_api.py:102`). The fuel Finding cites no dispatch window, so `:650-653` would read FINDING_MATCH_PENDING.
   - `scheduling/health.py:254`, which supplies `stale_no_work`'s input.
   - There is also a defect that exists today: an open cold Finding (`episode_end` NULL, as `cold_apply` writes it) makes `:467` compare None with a datetime and raise. This is the same defect FIX-S4-DOMAIN fixed in `episodes` (`:133-146`, `backend/tests/test_s4_finding_domain_filter_postgres.py`).
2. `PostgresConsequenceStore.latest_revisions_overlapping` (`B/financials/adapters/postgres_consequence_store.py:386-397`) is unfiltered. It supplies the targets for `ASSUMPTION_PUBLISHED` work (`B/financials/recompute.py:230-232`). That work is written by `financial_consequence_dirty_on_assumption` (`0011:338-350`) on every `financial_assumption_revision` insert: diesel, EV tariff and productive price, on every Site, with no domain test. The mini consequence drain runs on **every** Site (`scheduling/tick.py:492-497`, no site-type gate). `derive()` (`recompute.py:169-177`) would run fc2 on the fuel Finding and append a `financial_consequence_revision` that cites it (an S2 breach), or fail the work. **§9j.1(2) was incomplete:** it closed only the Finding-revision trigger.
3. **The third path is safe, and this ruling adds a test to keep it that way.** `financial_consequence_dirty_on_evidence` (`0012:102-130`) enqueues `EVIDENCE_ACCEPTED` work for the latest revision of **every** Finding whose episode overlaps an accepted `generator_power` reading, and the fuel Finding is one of them. Kisiwa's night runs overlap its episode, so such work will exist. The worker no-ops it before `derive()`: `evidence_no_op` (`recompute.py:102-103`) returns `NO_OP_ASSET` because the fuel Finding's `generator_asset_id` is NULL (§9j.4), which never equals the reading's asset. So no row is written. The work row is still enqueued and drained as a SUCCEEDED no-op. That is acceptable, and 0012 is not edited.

### 9k.2 Decision: filter both readers in SQL, positively, to the dispatch domain

**Options weighed:**
- **(A) A positive domain filter in both readers. Chosen.**
  - It puts the fix where the wrong set is produced, and it follows the precedent: FIX-S4-DOMAIN's `episodes(..., domain=DOMAIN, analytic_id=DISPATCH_ANALYTIC_ID)`, and the 0022 trigger's `WHEN (NEW.domain = 'mini_grid')`.
  - No caller or test fake changes: the new parameters are keyword defaults, and the fakes in `test_s4_schedule_upstream_unit.py:28,136`, `test_s4_evidence_drain.py:83` and `test_s4_consequence_cause_dispatch.py:22` keep their signatures.
  - It also protects the next domain. A deny-list (`domain <> 'fuel_balance'`) is rejected for that reason.
- **(B) The recompute worker skips non-`mini_grid` targets.** Rejected. It changes the `(finding_id, revision_id)` target tuple and the `ConsequenceStore` protocol, so the test fakes would break (S5). It leaves `findings_over` unfixed. And it moves a storage predicate into the worker.
- **(C) A `WHEN` clause on the assumption trigger in 0056.** Not possible. A `financial_assumption_revision` row has no Finding domain. Narrowing by `assumption_key` would not help either, because Kisiwa's diesel price is exactly what must still re-price its dispatch Findings.
- **(D) Defence in depth in `load_input_on` (`postgres_consequence_store.py:96-110`).** Not now. It has other `known_at` callers (W3-01 Run 6, Trial comparison), and with (A) in place plus §9k.1(3) every target path is closed. This goes on the after-the-demo list: "fc2 `load_input_on` refuses a non-`mini_grid` revision".

**Literal changes (K4a):**
1. `B/analytics/adapters/postgres_finding_store.py` `findings_over`:
   - The signature becomes `findings_over(self, tenant_id, site_id, lo, hi, domain: str = DOMAIN, analytic_id: str = DISPATCH_ANALYTIC_ID)`.
   - The SQL gains `AND r.domain = :d AND r.analytic_id = :a`, bound to those two parameters. The docstring gains: "FIX-K4a (DIESEL-1-R3k): one domain's and analytic's Findings only (the `episodes` predicate); a Site's fuel-balance, cold or EV Findings never reach the dispatch readers."
   - Nothing else in the method changes. The Python-side overlap filter at `:467` stays as it is; it now sees only dispatch rows, whose `episode_end` is never NULL.
   - The `finding_read.py:239` `FindingReadStore` port signature gains the same two keyword defaults. That is a type-only line.
2. `B/financials/adapters/postgres_consequence_store.py` `latest_revisions_overlapping`:
   - The SQL gains `AND r.domain = 'mini_grid'` (a literal, mirroring the 0022 trigger's `WHEN`; no analytic filter and no new import).
   - The docstring gains: "FIX-K4a (DIESEL-1-R3k): `mini_grid` revisions only, the domain the fuel-cost work triggers cover (0022); the dispatch fuel-cost model is never derived for another domain's Finding."
   - The signature does not change.
3. **No caller, no worker and no migration changes** for this ruling. 0056 stays as §9j.3 specifies.

### 9k.3 Effect on Kobo, Cold and EV (READ)

- **Kobo:** it holds only `mini_grid` dispatch Findings, so both readers return byte-equal results. No Kobo board, overview, Finding-window, golden or capture changes.
- **Cold and EV Sites:**
  - `findings_over` on a cold or EV Site now returns `[]` instead of that Site's cold or EV Findings (and no longer raises on an open cold Finding). Its consumers are dispatch-only:
    - the mini overview (`site_overview/read.py:136-138`, which reads `dispatch_read.window`);
    - `finding-windows`, whose only frontend callers are `F/sites/PerformanceDispatch.tsx:564` and `F/sites/SiteFindingEvidence.tsx:1176`, both dispatch pages;
    - health's `stale_no_work`, where the narrower input can only remove alarms. The builder found that none fire today.
  - The Cold and EV overviews are separate routes (`coldSiteClient.ts:256`, `evSiteClient.ts:259`). The board reads domain-filtered heads (`postgres_chain_read.py:27-45`). **No served Cold or EV output or golden reads either function.**
  - `latest_revisions_overlapping` on an EV Site (EV tariff publications fire the 0011 trigger) no longer offers EV Findings to `derive()`. Today that work runs the dispatch fuel-cost model on a non-dispatch Finding. Removing it fixes a defect that exists today, outside the served EV reads (EV money reads `ev_consequence_*`).
  - **Deviation recorded, K4a-DEV-1:** "dispatch readers and the fuel-cost recompute target read are filtered to their domain; cold/EV Sites no longer offer their Findings to them". The packet lists it with this paragraph. This is **not** stop S6, because S6 covers served bytes.
- **If the narrower set shows up in any served output, it is a stop (S8, below).** That applies whether it shows up in an existing test, a Cold or EV golden, or K8's all-26 recapture.

### 9k.4 Extra files and memberships (approved)

- `B/chain/threads.py:31` `SUBJECT_COLUMN` gains `"fuel_balance": "subject_asset_id"`. This is already §9j.4 and §9j.9 item 6, and is confirmed here.
- `T/checks/configuration-persistence.ps1`, membership only:
  - `$consequenceTables` (`:746-748`) gains `'fuel_residual_consequence_revision'`.
  - A `$fuelTransactionOwner = 'backend/assetops_backend/fuel_balance/findings_service.py'` is declared beside `$coldTransactionOwner`. It is added to every list in which `$coldTransactionOwner` is an allowed transaction owner, and to the owner-existence loop at `:1841`.
  - No new probe is added in `tools/writer_guard_probes.py`. If the guard demands one, that is stop S-g (below).
- **Scope of §9j.9 widened:** item 3 now also covers `findings_over` and its docstring. Item 4 now also covers `latest_revisions_overlapping` and its docstring. `B/analytics/finding_read.py` (the `:239` port line only) is added. Nothing else changes.

### 9k.5 Tests (added to §9j.8 B; no new test file)

Each "must fail" names the mutation that the reviewer applies to a scratch copy.

- **B7. `findings_over` excludes the fuel Finding.**
  - Setup: on the K4 test Site, one dispatch Finding (from the Kobo import already used by B) and one fuel Finding raised through `raise_night`, with overlapping episodes.
  - `findings_over(t, s, lo, hi)` over the overlap returns only the dispatch Finding's id. Called with `domain="fuel_balance", analytic_id="fuel-balance-1"`, it returns only the fuel Finding (this makes the test non-vacuous).
  - `FindingReadService.window_state` for a day the fuel Finding overlaps lists no fuel Finding id in `findings`.
  - Must fail if the `r.domain`/`r.analytic_id` predicate is removed.
- **B8. Recompute never derives on the fuel Finding.**
  - Setup: after B7's fuel Finding exists, publish a diesel price revision on that Site through the assumption store. This fires `ASSUMPTION_PUBLISHED` over the night.
  - Run `build_recompute_worker(url).run(t, s, limit, now=...)`.
  - Expected: the work is SUCCEEDED; the dispatch Finding gets its consequence as before; **no** `financial_consequence_revision` row has the fuel Finding's id; `latest_revisions_overlapping` over the night returns no fuel id.
  - Must fail if `AND r.domain = 'mini_grid'` is removed: then a row cites the fuel Finding, or the work fails.
- **B9. The evidence path no-ops.**
  - Setup: accept one `generator_power` reading that overlaps the fuel Finding's episode.
  - The enqueued `EVIDENCE_ACCEPTED` work for the fuel revision finishes SUCCEEDED with `no_op_reason` = `NO_OP_ASSET`, and no `financial_consequence_revision` cites the fuel Finding.
  - Must fail if `fuel_apply` writes a non-NULL `generator_asset_id`. The subject CHECK refuses that write, so for a scratch mutation the reviewer may instead assert directly on `evidence_no_op` with a fuel-shaped target: `generator_asset_id None` gives `NO_OP_ASSET`.
- **A9 (L0, `test_k4a_fuel_finding_rules.py`).** `evidence_no_op` on a fuel-shaped target (`generator_asset_id None`, a `generator_power` reading on the generator) returns `NO_OP_ASSET`.
- **These must stay green unchanged**, in addition to §9j.8's list:
  - `test_s4_finding_domain_filter.py` and `test_s4_finding_domain_filter_postgres.py`;
  - `test_s4_schedule_upstream_unit.py`;
  - `test_s4_finding_api.py` and `test_s4_finding_read_postgres.py`;
  - `test_s4_consequence_recompute_postgres.py`, `test_s4_consequence_cause_dispatch.py` and `test_s4_evidence_drain.py`;
  - the scheduling health tests (`git grep -l "stale_no_work" backend/tests`).
  - A behaviour edit to any of them is S5.
- DB: only `assetops_k4_test`, as §9j.9 says. No suite.

### 9k.6 Stops (added to §9j.9)

- **S8:** a test listed in §9k.5 needs a behaviour change, or a Cold, EV or Kobo served byte or golden changes because of the filter. Report the diff. Never widen the filter to fix it.
- **S9:** a fourth path writes or derives money for a `fuel_balance` revision: any other reader of `finding_revision` that feeds `derive()`, the fuel-cost reads or the board's money head without a domain predicate. The builder runs `git grep -n "FROM finding_revision" backend/assetops_backend/financials backend/assetops_backend/scheduling` and lists each hit with the predicate it has, or why it is safe, in the packet's pre-flight answer. One `r.domain` predicate per hit is in scope for K4a **only** after this Architect approves it. Otherwise it is a stop.
- **S-g:** the guard requires a new writer probe or a list other than those in §9k.4.
- S1–S7 stand. **S7's ceiling is now 1.7.**

### 9k.7 Size, critical path, tripwire

- **K4a: 1.4 to 1.5** (range 1.3–1.7). That is +0.1: two predicates and docstrings 0.02; B7–B9 and A9 0.07; the S9 grep 0.01.
- **Kisiwa total: 17.6 to 17.7.** The increase is reported, not absorbed.
- **Critical path:** about 8.3–8.4 plus 0.1, so **about 8.4–8.5 lane-units**. That is below the 9.75 tripwire, with 1.25 of headroom. No cut is needed, no owner question arises, and the demo date is unchanged at about +3.25 working days.
- **Plan HTML (coordinator):** K4a becomes 1.5 and DIESEL-1-R3 becomes 17.7. The rulings table gains "DIESEL-1-R3k: dispatch Finding readers and the fuel-cost recompute target read filtered to their domain (FIX-S4-DOMAIN pattern); evidence path no-ops on the fuel Finding (`NO_OP_ASSET`); K4a 1.5". The after-the-demo list gains "fc2 `load_input_on` refuses a non-`mini_grid` revision".

### 9k.8 Owner questions

None. For the owner's information, in plain words: before building, the builder found two places where the system would have mixed the new "unexplained fuel" finding into the generator's fuel-cost checks. That could have given it a fuel-cost figure it must never have, or made the Kisiwa overview look out of date. Both places now look only at generator findings, as one similar place already does. This also closes a small existing gap on the cold-room and EV sites. Nothing on their screens changes. The work grows by a tenth of a unit, and the demo date does not move.

---

## 9l. Ruling DIESEL-1-R3l: the K5 and K7 consolidated cards

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `0c4aa7310` (K0 merged `a268b3ff6`; K1, K1a, K2, K3, F0/F0e merged; K4a in build in `AssetOpsV1-k4a`; A3 in pre-flight in `AssetOpsV1-a3`).
- Owner decisions in force, verbatim: `.agent/owner-scenario-data-2026-11-07.md` ("dont be limited by existing data, data that is reasonable and can reflect a situation can be legitmately added via a scneario for days that are not covered today"; "this is not true, these are injected through operational actions"); `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'"); `.agent/owner-kisiwa-scope-2026-11-07.md` ("Build it, with the action link (Recommended)"); `.agent/owner-diesel-night-window-2026-11-07.md` (a night runs "6 pm to noon").
- **These two cards replace** the K5 and K7 rows of §8.4 and §9.5, §8.6's Action time, §8.4's "Wording (K5)" block (K4a owns those two strings now, §9j.7) and §9j.14's K5 and K7 bullets. Builders read only their own card. Paths use the header's short forms; `T/` = `tools/`. READ = the Architect read the code at `0c4aa7310`; nothing was run.
- **Honesty rules H1–H5 (§8.2) bind both cards.** Client copy never says theft, stolen, stole, siphon or pilfer, and never implies them. Every client literal below was checked by hand against guard V's whole-word terms (`F/test/productVocabulary.json`): none uses run, runs, ran, running, load, claim, candidate, necessary, analytic, scenario, simulation, binding, mapping, stage or fixture. "Modelled use" replaces "running" (K4a's precedent). Guard V's own run is the builder's acceptance (stop S-a).

### 9l.1 Code reality and the decisions it forces (READ)

1. **The F0 world sits at absolute dates, but the demo story moves with the database clock.** The promoted log `C/operational-actions/kisiwa-001-operational-actions-v1.yaml` holds UTC instants from `2026-10-01` to `2026-10-11`. The combined prepare places every story day relative to `S = floor_utc_day(DB now) − 2 d` (`T/demo_combined.py:139-142`). The Portfolio and Findings week runs from `S−6d` to `S+1d` (`:202-205`). Today `S` is about 6 November, so:
   - the October nights would fall outside the week;
   - the Protect line (K4b, KIS-8a) would never show night 4;
   - the Work API's 30-day backdate rule (`B/work/model.py:36-37`) would soon refuse the records.

   **Decision: the Kisiwa story is the F0 world moved by a whole number of days.** This is the EV pattern (`base_e_start` plus `day_delta_days`, `T/demo_combined.py:161-163`).
2. **A whole-day move changes no physics and no published reading.**
   - The day document is date-free (`T/probe_kisiwa_nights.py` `day_document(soc, fuel)`).
   - The publication draw is keyed by seed, stream and **step index** (`S/observation/transform.py:189-201`), not by instant.
   - Kisiwa's zone (`Africa/Dar_es_Salaam`, UTC+3) has no daylight saving.

   So run k at `start + N days` gives F0's trajectory, readings, dropouts, gap and dips exactly. K7 proves this for each run (the physics guard) and each night (KIS-3). Any difference is a stop, never a retune.
3. **The log is named by version and never edited, so a moved log is a new log.** K0 reads `{root}/{log_id}-v{log_version}.yaml` and freezes its sha256 (§9f.2 (5)).
   - K7 therefore writes a derived log for each prepare, into the work folder. Its own id is `kisiwa-001-story-{yyyymmdd of night 1}`, version 1.
   - K7 hands `YamlOperationalActionLog(root=<work>/operational-actions)` to run setup.
   - The derived log's content is v1 with every `at` (and `sensor_disconnected.at`) moved by N days. Nothing else changes.
   - The shipped v1 file, its hash `77777c82…b634` and K0's pins are untouched.
4. **Every action already sits inside one run's day.** Run k runs from 15:00 local on day k to 15:00 local on day k+1. In those terms:
   - the delivery is in run 2;
   - the removal and the sensor span are in run 4, and so is the night-4 dip;
   - the seal and sensor-power actions are at run 6's start, which is inside `[start, end)`;
   - each after-change dip is in its own run, 6 to 10.

   No v2 action is needed: the story uses exactly F0's actions. K0's residual (an action that straddles a run start is silently dropped) is closed by a mechanical check (KIS-9 (c) and an L0 test), not by trust.
5. **The boards read as known at story cutoffs, so every stamp must be a story instant.**
   - K3's CLI stamps the database's wall clock (`B/fuel_balance/worker.py`). That clock is after every story cutoff, so boards for story days would not see the windows.
   - K3's and K4a's stores take a test-only clock override. It is constructor-only (§9d.4); K4a's form is `build_fuel_finding_service(…, test_db_clock_override=)`.
   - K3's `worker.main(argv, store=…)` takes an injected store (`host/tests/test_k3_fuel_balance_parity.py:263`).

   **Decision:** K7 calls the K3 CLI entry point in process, with an injected store whose clock is the story instant. It calls K4a's service the same way. Tools already set this seam for story stamps (`T/demo_combined_mill.py:138`, `:146`).
6. **The Finding cannot exist at 12:30 local on day 5.** Night 4's data arrive with run 4, which ends at 15:00 local on day 5 (§8.3: day-runs run 15:00–15:00). §8.6's "12:30 local … after the closing reading" came before that reading was delivered. **Corrected:** the Action is raised at **16:00 local on day 5**. By then run 4 has been received (+10 min), assessed (+30 min) and raised (+31 min). The effective instant (15:00 local, run 6's start) and the partition of nights are unchanged.
7. **Kobo's prepare must not move.**
   - `T/demo_combined.py` treats "all Sites" as exactly three in several places (`:100`, `:151`, `:176-182`, `:487`, `:533`, `:551`).
   - No tick may run before Kobo's mill step (`:498-501`).
   - The chain backfill takes `--site` (`B/chain/backfill.py:4`, `:33`), so a Kisiwa-scoped threads step touches no Kobo thread.
   - The S3 dispatch worker (`host/tests/test_s6_verification_replay.py:112-115`) drains every pending job, so K7 never calls it. Kisiwa's dispatch windows are assessed by the prepare's existing ticks and drains, as Kobo's `tick` days are.
8. **The Site Finding page is dispatch-shaped and has no domain filter.** `GET /api/sites/{code}/findings/{id}` reads `finding_detail` with no domain predicate (`B/analytics/finding_read.py:359-372`). It renders dispatch currentness and windows (`B/finding_api.py:111-143`), so a fuel Finding there would read wrongly. **Decision:** the fuel Finding gets its own address, as the mill verdict did (`DOMAIN_VERDICT`, `F/shell/operatorSiteRoutes.ts:593-594`). That means a new Ref kind `FUEL_FINDING` and the route `/sites/{site}/fuel-findings/{id}`. The dispatch route is not edited.
9. **The Kobo Fuel page is an hour read** (`F/sites/MiniPerformance.tsx:1574-1622`, `GET …/mini-depth/fuel`), but Kisiwa's night check is K3's stored window. **Decision:** the Fuel page has two modes:
   - **night mode** iff the Site has at least one stored fuel-balance window as known;
   - **hour mode** otherwise, exactly as today and byte-equal (Kobo).

### 9l.2 K5 card: the Fuel page night mode, the fuel Finding page and the Site Findings fuel panel, 1.3 (range 1.15–1.5)

**What K5 delivers.**
- **Site › Performance › Fuel in night mode,** on a Site with stored windows:
  - a night selector;
  - the v69 `fuel` cards, waterfall and bridge, filled from the stored window;
  - a "Deliveries and tank dips" table;
  - the reworded notice (K4a's constant, imported);
  - a "Finding for this night" panel.
- The **fuel Finding page** at its own address, with K4a's server lines.
- A **"Fuel checks" panel** on the Site Findings index, only when the Site has a fuel Finding.
- The read routes for all three. All text is formatted on the server; the browser formats no number.
- The `FUEL_FINDING` Ref kind.
- **Unchanged:**
  - Kobo's Fuel page in hour mode: every byte except K4a's two reworded strings. K5 does **not** edit those two lines (`FUEL_NOTICE` and the RESIDUAL row at `F/sites/MiniPerformance.tsx:1310-1311`, `:1343`).
  - every dispatch Finding page and route;
  - every Cold and EV byte;
  - K3's and K4a's write paths.
- **Moved out of K5:** the fuel Finding's entry in the **estate** Findings lists goes to K8 (+0.15 there), with the four-Site lists K8 already owns.

**Phases (K5 can start before K4a merges).**
- **Phase A, now (about 0.75):**
  - the pre-flight;
  - the nights routes and the night text below, except the two K4a lines;
  - night mode and the records table;
  - tests A1–A5, B1–B3 and F1–F4.
- **Phase B, after K4a merges (about 0.45):**
  - `git merge main`;
  - the margin and gap lines, imported from K4a's `B/fuel_balance/finding_text.py`;
  - the fuel Finding route and page, and the Ref kind;
  - the Site Findings panel, and the night page's Finding panel;
  - tests A6–A7, B4–B5 and F5–F8.
- **Captures (about 0.1):** taken after K7-D's Kisiwa scratch prepare has run (§9l.3), against its kept database. K5 merges after the captures.
- K4b may start after K5's phase B build, before K5's captures (lane-1 order).

**Backend: `B/fuel_balance/night_text.py` (new, pure, no I/O).**
- Litres: one decimal, half-even on the exact Fraction (K4a's rule). Phase A copies K4a's one-line helper; phase B replaces it with the import from `finding_text`.
- kWh: one decimal. SFC: as stored. Times: Site-local `HH:MM`. `{date}` = `f"{d.day} {d:%b}"`.
```python
NIGHT_LABEL = "Night of {date} · 6 pm to noon"
STATUS = {
    "UNEXPLAINED": "Fuel balance: unexplained fuel",
    "WITHIN_MARGIN": "Fuel balance: accounted for within the margin",
    "BELOW_MATERIALITY": "Fuel balance: a small difference, below the 40 L the check flags",
    "EXCESS": "Fuel balance: more fuel than recorded",
    "NOT_ASSESSED": "Fuel balance: not checked",
}
STATUS_TONE = {"UNEXPLAINED": "amber", "WITHIN_MARGIN": "neutral", "BELOW_MATERIALITY": "neutral",
               "EXCESS": "amber", "NOT_ASSESSED": "neutral"}
FUEL_REASON_WORDS = {  # K4b imports these (amended, §9l.4); §9j.11's literals, with "no-load" made guard-V safe
    "NO_SENSOR_ACCURACY": "no tank sensor accuracy declared",
    "SFC_MISSING": "no generator fuel rate declared",
    "NO_LOAD_RATE_MISSING": "no generator idle fuel rate declared",
    "MISSING_OPENING": "no tank reading at 6 pm",
    "MISSING_CLOSING": "no tank reading at noon",
    "FUEL_LEVEL_CONFLICT": "two different tank readings at the same time",
    "GENERATOR_KWH_UNKNOWN": "generator power readings incomplete",
    "IDLE_SECONDS_UNKNOWN": "generator state readings incomplete",
}
NOT_CHECKED = "Not checked: {why}"
# cards (label, value, note); labels are the existing ones (MiniPerformance.tsx:1417-1444)
OPENING_NOTE = "Tank reading at {hh_mm}"
DELIVERIES_NONE = "None recorded"
DELIVERIES_NOTE_ONE = "1 delivery record"
DELIVERIES_NOTE_MANY = "{n} delivery records"
DELIVERIES_NOTE_NONE = "Absence of record does not prove none occurred"          # v69 :625, verbatim
USE_NOTE = "Modelled: {kwh} kWh × {sfc} L/kWh, 10 % either way"
USE_NOTE_IDLE = "Modelled: {kwh} kWh × {sfc} L/kWh plus {m} min idle at {r} L/h, 10 % either way"
RESIDUAL_NOTE = {"UNEXPLAINED": "Above the 40 L the check flags", "WITHIN_MARGIN": "Zero lies inside this range",
                 "BELOW_MATERIALITY": "Below the 40 L the check flags", "EXCESS": "More fuel than recorded"}
CANNOT_COMPUTE = "Cannot compute"                                                  # v69 :626
UNKNOWN_VALUE = "Unknown"
# bridge rows: (term, label, evidence basis, treatment); the row shows "{label} · {value}"
BRIDGE = (
    ("OPENING", "Opening inventory", "Tank reading at {hh_mm}", "Declared sensor accuracy ±{a} L"),
    ("DELIVERIES", "Plus deliveries", "{deliveries_basis}", "1 % allowance on each ticket"),
    ("USE", "Less generator consumption", "Generator output × declared fuel coefficient",
     "Modelled range, not a fuel-meter reading"),
    ("CLOSING", "Less closing inventory", "Tank reading at {hh_mm}", "Declared sensor accuracy ±{a} L"),
    ("RESIDUAL", "Unexplained residual", "Opening + deliveries − use − closing",
     "Compared with the combined margin; never says why fuel left"),
)
DELIVERIES_BASIS_NONE = "No delivery record"     # else DELIVERIES_NOTE_ONE / _MANY
# records table
RECORD_KIND = {"FUEL_DELIVERY": "Fuel delivery", "TANK_DIP": "Tank dip"}           # K2's labels
RECORD_WHEN = "{hh_mm}, {date}"
RECORDS_EMPTY = "No delivery or tank dip recorded this night"
DIP_CONFLICT = "A tank dip differs from the nearest tank reading by more than the declared accuracy plus 10 L."
DELIVERY_LATE = "A delivery was first recorded after the night could be checked."
# Finding panel on the night page
FINDING_NONE_WITHIN = "No finding: the fuel was accounted for within the margin."
FINDING_NONE = "No finding for this night."
FINDING_NOT_RAISED = "Not available yet · the finding for this night has not been raised"
FUEL_NIGHT_LINK = "Open this night on the Fuel page"
# fuel Finding page and the Site Findings panel
LIFECYCLE = {"SUPPORTED": "Supported by the latest check", "NO_LONGER_SUPPORTED": "No longer supported"}
VERSION_ROW = "Version {n} · {lifecycle} · {hh_mm}, {date}"
FUEL_CHECKS_ROW = "{title} · {date} · about {lo}–{hi} L"
```
- Placeholder formats:
  - `{a}` is the stored `accuracy_l`, to 0.1, without a trailing ".0" for whole litres ("10");
  - `{m}` is whole minutes;
  - `{r}` is the rate as stored.
- In phase B, the night page's margin note is K4a's `finding_text.margin_line(accuracy_l)`. Its gap line is K4a's `finding_text.gap_line(spans, tz)`, shown when `gap_minutes > 0`. In phase A both are absent, and the chart note is only the existing sentence "A residual is shown only when every term has a supported range."

**Backend: `B/fuel_balance/night_read.py` (new) and `B/fuel_balance_api.py` (a new router), registered in `B/main.py`.**
- Scope, Site resolution and refusals copy `B/finding_api.py:46-100`: `open_scope`, development access, and 404 for a Site outside the configured tenant.
- Reads go through:
  - K3's `PostgresFuelBalanceStore` (`windows`, `window`);
  - K2's `select_fuel_records`;
  - K4a's `fuel_findings` and `fuel_finding` (phase B);
  - one new read-only store method, `has_windows(tenant_id, site_id, known_at) -> bool` (`SELECT EXISTS … recorded_at <= :k`).
- The provenance block is the one the mini-depth fuel read already returns. PRE-FLIGHT (a) names its builder. It is reused, never re-derived.

The four routes:
1. `GET /api/sites/{site_code}/fuel-balance/nights?from=YYYY-MM-DD&to=YYYY-MM-DD[&known_at=ISO]`
   - Body: `{"site_code", "mode": "NIGHTS"|"NONE", "time_zone", "known_at", "nights": [{"night_date", "label", "state", "status", "tone", "revision"}], "provenance"}`.
   - `mode` is `NONE` iff `has_windows` is false (Kobo); `nights` is then `[]`.
   - Without `from`/`to`, the range is the 14 nights ending with the latest stored night as known.
   - A span over 31 nights, `from >= to`, or a malformed date gives 422 `FUEL_BALANCE_RANGE_INVALID`, with the message "Choose up to 31 nights, with the first night before the last."
2. `GET /api/sites/{site_code}/fuel-balance/nights/{night_date}[?known_at=ISO]`
   - Body: `{"site_code", "night_date", "label", "time_zone", "known_at", "state", "status", "tone", "revision", "window_start", "window_end", "cards": [{"key", "label", "value", "note", "word"}] (4), "bars": [{"key", "label", "value_l", "text"}] (5), "bridge": [{"term", "label", "value", "basis", "treatment", "evidence_count"}] (5), "notes": [...], "records": [{"code", "kind", "when", "volume", "occurred_at"}], "finding": null | {"finding_id", "title", "text", "href"}, "finding_note": str | null, "provenance", "links": {"evidence", "fuel_page"}}`.
   - Card labels are the existing ones (`MiniPerformance.tsx:1417-1444`): "Opening evidence", "Recorded deliveries", "Modelled expected use", "Residual". Bar labels are the existing ones (`:1458-1462`).
   - `value_l` is a float used only to scale a bar. Every visible number is in `text` or `value`.
   - `notes`, in this fixed order:
     - the gap line (phase B);
     - `DIP_CONFLICT`, iff that limitation is set;
     - `DELIVERY_LATE`, iff that limitation is set;
     - `NOT_CHECKED`, iff the night is NOT_ASSESSED.
   - `records`: the K2 fuel records with occurrence in `[window_start, window_end)` as known, ordered by occurrence. `volume` = "{q} L" (whole litres when integral).
   - `finding` (phase B): the fuel Finding whose latest revision, as known, cites this night's window. `title` = K4a's `TITLE`, `text` = its `claim` line, `href` = `/sites/{code}/fuel-findings/{id}`.
   - If there is no such Finding, `finding_note` is `FINDING_NONE_WITHIN` for WITHIN_MARGIN, `FINDING_NOT_RAISED` for UNEXPLAINED, and `FINDING_NONE` otherwise.
   - In phase A, `finding` and `finding_note` are both null.
   - No window as known gives 404 `FUEL_BALANCE_NIGHT_NOT_FOUND`, "No fuel check is stored for this night."
3. `GET /api/sites/{site_code}/fuel-findings?from=ISO&to=ISO[&known_at=ISO]` (phase B)
   - Body: `{"site_code", "rows": [{"finding_id", "night_date", "lifecycle", "text", "href"}]}`. `text` is `FUEL_CHECKS_ROW` with K4a's title.
4. `GET /api/sites/{site_code}/fuel-findings/{finding_id}[?revision_id=]` (phase B)
   - Body: `{"site_code", "finding_id", "revision_id", "revision_no", "lifecycle", "lifecycle_text", "night_date", "label", "lines": finding_text.finding_lines(...), "night": <route 2's body for the cited window revision, without its finding block>, "revisions": [{"revision_id", "revision_no", "text"}], "provenance", "links": {"canonical", "fuel_night"}}`.
   - An unknown id, another Site's id, or a revision not of this Finding gives 404 `FUEL_FINDING_NOT_FOUND`, "No such fuel finding for this Site."

**Ref kind** (`B/chain/refs.py`): `fuel_finding_ref(site, finding_id, revision=None) -> _ref("FUEL_FINDING", site=…, id=…, revision=…)`. The kind joins the kinds list and every validator that list feeds (PRE-FLIGHT (c)).

**Frontend.**
- `F/sites/fuelBalanceClient.ts` (new): `getNights`, `getNight`, `getFuelFindings`, `getFuelFinding`. Bodies are typed as above, with the existing `MiniRead` result shape.
- `F/sites/MiniFuelNights.tsx` (new): `MiniFuelNightsPage`, composed of existing components only:
  - `StatusBar`;
  - `MetricCards` and `MetricCard`;
  - `Panel`, `ValueBars` and `ChartNote`;
  - `BoundedPanel` and `DataTable`;
  - `Notice`, with the imported `FUEL_NOTICE`.

  No new CSS, unless PRE-FLIGHT (d) shows a mock budget the existing classes miss.
  - **Night selector** (in place of `MiniHourBar`):
    - a `<nav aria-label="Nights">` holding a select of nights. Each option's text is the server `label` + " · " + the server `status`;
    - two buttons, "Previous night" and "Next night", disabled at the ends;
    - the address carries `?night=YYYY-MM-DD`. Without it, the page opens the latest listed night. A reload reopens the same night.
  - **Order** (v69 `:623-630`, MD-FUEL-K-1):
    1. the status bar: the badge (`status`, `tone`), provenance chips, and `notes` as strip items;
    2. the cards;
    3. "Fuel balance at a glance": the bars and the chart note;
    4. "Balance bridge": five rows, with `evidence_count` and the Evidence link as today's bridge has them;
    5. **"Deliveries and tank dips"**: columns "Time", "Record", "Volume", "Reference"; `RECORDS_EMPTY` when there are none;
    6. the notice;
    7. **"Finding for this night"**: the Finding's title as a link and its `text`, or `finding_note`. In phase A this panel is absent.
- `F/sites/MiniPerformance.tsx`: `MiniFuel` gains an optional prop, `fuelBalance?: FuelBalanceClient`.
  - With the prop, it first calls `getNights(siteCode)`. `mode === "NIGHTS"` renders `MiniFuelNightsPage`, with no hour bar.
  - `mode === "NONE"`, a failed read, or an absent prop renders today's hour-mode branch, unchanged.
  - **No other line of `MiniPerformance.tsx` changes.** The two K4a lines are not touched.
- `F/shell/SiteAnalyticsFrames.tsx` passes `fuelBalance` to `MiniFuel` (one prop).
- `F/sites/SiteFuelFinding.tsx` (new) at `SITE_FUEL_FINDING_ROUTE_PATH = ${SITE_DETAIL_ROUTE_PATH}/fuel-findings/:findingId`. The route and `siteFuelFindingHref(site, id, revision?)` live in `F/shell/operatorSiteRoutes.ts`; `?revision_id=` works as it does on the dispatch page. Layout, in order:
  1. `SitePageHeader`, and `OperatorSiteTabs current="Findings"`;
  2. a status bar: the badge `lifecycle_text`, the `label`, provenance chips;
  3. `BigClaim` with `lines.claim` (or `lines.no_longer`);
  4. a fact list of `lines.gap`, `lines.money`, `lines.margin` and `lines.not_why`, each only when present;
  5. the panel "How the night was checked": the bridge table component shared with the Fuel page, plus the `FUEL_NIGHT_LINK` link to `/sites/{code}/performance/fuel?night=…`;
  6. the panel "Deliveries and tank dips" (the shared component);
  7. the panel "Versions" (`revisions[].text`).
- `F/sites/chainRef.ts` gains `{ kind: "FUEL_FINDING"; site: string; id: string; revision?: string }`.
- `routeFor` gains `case "FUEL_FINDING": return siteFuelFindingHref(r.site, r.id, r.revision)`.
- `F/test/linkRefs.ts` parses the new path back to the Ref.
- `F/App.tsx` registers the route beside `SITE_FINDING_ROUTE_PATH`.
- The Site Findings index (`F/sites/SiteFindingIndex.tsx` or its frame; PRE-FLIGHT (e) names the component): on a MINIGRID Site, a panel "Fuel checks" after the dispatch table, with one link row per `rows[]`. It renders **only when `rows` is non-empty**, so Kobo stays byte-equal.

**MOCK DEVIATIONs (a header comment at each render, and one packet row each).**
- **MD-FUEL-K-1** (kept): a night window (6 pm to noon) with a night selector, instead of v69's hour bar (`:623-630` shows Kobo's selected hour).
- **MD-FUEL-K5-1:** the "Deliveries and tank dips" table. v69's `fuel` screen has no record list; its bridge names "Delivery / operator records" (`:627`).
- **MD-FUEL-K5-2:** in night mode, "Finding for this night" replaces v69's "Inspect existing generator fuel interpretation" (`:629`), which is about the dispatch consequence of a Kobo hour. Hour mode keeps v69's panel.
- **MD-FUEL-K5-3:** the "Fuel checks" panel on the Site Findings index. v69's Findings index lists dispatch Findings only.
- **MD-FUEL-K4-1** (K4a's, cited): the fuel Finding page itself. v69 has no unexplained-fuel Finding and defers "theft detection" (`:630`).

**Tests (localised; no full suite).** Every "must fail" names the mutation the reviewer applies to a scratch copy.
- **A. L0 `backend/tests/test_k5_fuel_night_text.py` (no DB).**
  1. Night 4, from `.agent/DIESEL-F0/probe-result.json` `nights[3].readings` (exact), with a = 10 and SFC 0.355, gives:
     - the residual value "95.7–144.3 L";
     - the status `STATUS["UNEXPLAINED"]` and its `RESIDUAL_NOTE`;
     - the use card's `USE_NOTE` with its kWh and SFC.

     Must fail if litres round half-up: the synthetic band [1.25, 2.35] must give "1.2–2.4".
  2. Night 2: the deliveries value "300 L", the note `DELIVERIES_NOTE_ONE`, the basis "1 delivery record". Night 1: `DELIVERIES_NONE`, with v69's note.
  3. Each state's status, tone and residual note. NOT_ASSESSED gives the value `CANNOT_COMPUTE` and `NOT_CHECKED` with each reason word.
  4. The idle note appears only when `idle_seconds > 0`.
  5. **Wording (local):**
     - every literal in `night_text.py`, lower-cased, holds none of theft, stolen, stole, siphon or pilfer;
     - guard V's `_patterns` (`backend/tests/test_out_b2_vocabulary.py`) pass on each one;
     - the K5 literals join that test's scan list.
  6. (phase B) The margin and gap lines equal K4a's `finding_text` output (imported, not retyped).
  7. (phase B) `FUEL_CHECKS_ROW` for night 4 = "Unexplained fuel overnight · 4 Oct · about 95.7–144.3 L".
- **B. L2 `backend/tests/test_k5_fuel_night_api_postgres.py`, on its own `assetops_k5_test`.** Kobo is imported as in K3's B tests; synthetic windows go through `PostgresFuelBalanceStore.append` with the test clock; records go through K2.
  1. Kobo with no window: nights gives `mode == "NONE"` and `nights == []`. The hour read is unchanged.
  2. With windows:
     - the list is as known (a revision recorded after `known_at` is absent);
     - the default range;
     - the 422 cases;
     - 404 for an unknown night and for another tenant's Site.
  3. The night body:
     - cards, bars and bridge;
     - records ordered, and half-open at both window edges;
     - the order of `notes`;
     - no number left for the browser: every `value` and `text` is a string.
  4. (phase B) With a Finding raised by `raise_night`:
     - the night body's `finding`;
     - the fuel-findings list;
     - the fuel Finding body (lines, `night`, revisions);
     - 404 for another Site's Finding id, and for a dispatch Finding's id. Must fail if the route reads `finding_detail` without the `fuel_balance` domain.
  5. (phase B) `fuel_finding_ref` resolves through the Ref validator.
- **F. Frontend** (`F/sites/__tests__/miniFuelNights.test.tsx`, `siteFuelFinding.test.tsx`, plus the existing route and ref tests):
  1. Night mode renders the server strings verbatim. A static test checks that `MiniFuelNights.tsx` and `SiteFuelFinding.tsx` call no `toFixed`, `Intl.NumberFormat` or `NUMBER.format`.
  2. The selector: with `?night=` absent it opens the latest night; Previous and Next change the address; both are disabled at the ends.
  3. The records table, and its empty text.
  4. Hour mode: with `mode: "NONE"`, with a failed nights read, and with no `fuelBalance` prop, the rendered DOM equals today's. The existing `miniFuelRoutes.test.tsx` passes unchanged except for K4a's two literals. Must fail if night mode renders on `NONE`.
  5. (phase B) The Finding panel: the link, `FINDING_NONE_WITHIN`, `FINDING_NOT_RAISED`.
  6. (phase B) The fuel Finding page: the SUPPORTED lines, the NO_LONGER_SUPPORTED lines, the night link, and `?revision_id=` pinning.
  7. (phase B) `routeFor({kind: "FUEL_FINDING", …})`, and the `linkRefs` round-trip.
  8. (phase B) The "Fuel checks" panel is present with rows and absent with none.
- **Must stay green unchanged:**
  - every existing mini page test;
  - `siteFinding*.test.tsx` and the Findings index tests;
  - K3's and K4a's tests;
  - `test_out_b2_vocabulary.py` (it gains literals only);
  - `tsc`.
- **Guards:** run directly, with no `-ExecutionPolicy`:
  - `tools\check-all.ps1`;
  - `tools\check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` if there is no venv);
  - `tools\check-agent-workflow.ps1`;
  - `tools\check-navigation-truthfulness.ps1`;
  - `node tools/checks/frontend-hardwiring.mjs` (no rise);
  - mock-deviation-labels;
  - guards A, W, N, V and M.

  Allowlist joins (rule-8 readers for the new router's reads, the Ref kind lists) are membership only, and the packet lists them.

**Layout evidence at 1440 and 390.** Taken with `node tools/layout-evidence.mjs` against `T/demo_combined.py … serve` on K7-D's kept `assetops_demo3_kisiwa_test`, or the coordinator-run equivalent.
- Pages to capture:
  - Kisiwa Fuel, night 4 (UNEXPLAINED, the gap note, one dip) and night 6 (WITHIN_MARGIN, two dips);
  - the night-2 delivery night, at 1440 only;
  - the fuel Finding page for night 4;
  - Kisiwa Site Findings with the "Fuel checks" panel;
  - Kobo's Fuel page in hour mode, at both widths, compared with main's capture of the same page: only K4a's two strings may differ.
- Before the build, `node tools/measure-mock-panels.mjs .agent/K5-mock-measurements fuel` is run and committed as `.agent/K5-mock-measurements.md`.
- The night page meets those panel budgets. The records table's height cap is sized for 10 rows; the worst case today is 2 dips plus at most 1 delivery a night. `ShowAll` applies after 6 rows.
- There is no horizontal scroll at 390, and every table scrolls inside its own panel.

**PRE-FLIGHT (no code first; batch every question in one message).**
- (a) The mini-depth fuel read's provenance builder (file:line) and its body key.
- (b) Where `B/main.py` registers `build_finding_router`, and confirmation that `host/lab_app.py` serves the same app (so `serve` exposes the new routes).
- (c) Every list or validator a new Ref kind must join, file:line: the backend refs, the chain-coherence link checks, the frontend `Ref` union and its exhaustive switches.
- (d) The `.agent/K5-mock-measurements.md` budgets, and whether the existing mini classes meet them.
- (e) The Site Findings index component and its MINIGRID branch.
- (f) Whether K4a's merged `finding_text.finding_lines` signature matches §9j.7 (phase B).

**Stops (report to the Architect; never design around them).**
- **S-a** guard V or N rejects a literal. Report the message; never reword silently.
- **S-b** any of these changes: a Kobo Fuel-page byte other than K4a's two strings; any Cold or EV byte; any dispatch Finding page or route.
- **S-c** a need to edit any of: K4a's two lines; K3's or K4a's write paths; `B/finding_api.py`; `B/analytics/`; `B/work/` (K2's read is called, not edited); any migration.
- **S-d** the provenance block cannot be reused (PRE-FLIGHT (a)).
- **S-e** the new Ref kind needs any change beyond list membership and one `routeFor` case.
- **S-f** more than 1.5 units.

**Files (approved list):**
- New: `B/fuel_balance/night_text.py`, `B/fuel_balance/night_read.py`, `B/fuel_balance_api.py`; `F/sites/fuelBalanceClient.ts`, `F/sites/MiniFuelNights.tsx`, `F/sites/SiteFuelFinding.tsx`; `.agent/K5-mock-measurements.md`.
- Edited:
  - `B/fuel_balance/adapters/postgres_fuel_balance_store.py` (`has_windows` only);
  - `B/main.py` (router registration);
  - `B/chain/refs.py` (`fuel_finding_ref` and the kind);
  - `F/sites/MiniPerformance.tsx` (the `MiniFuel` prop and branch only);
  - `F/shell/SiteAnalyticsFrames.tsx` (one prop);
  - `F/shell/operatorSiteRoutes.ts`, `F/sites/chainRef.ts`, `F/App.tsx`;
  - the Site Findings index component (PRE-FLIGHT (e));
  - `F/test/linkRefs.ts`.
- Also: the tests above, and guard allowlists (membership only).

**Dependencies, start, branch, DB, size.**
- **Depends on:** K3 merged (yes). Phase B needs K4a merged. The captures need K7-D's scratch prepare.
- **Lane:** lane 1. K5 starts now if lane 1 is free; otherwise the next free builder takes it.
- **Branch:** `task/DIESEL-K5-fuel-screens`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k5`, from main at or after `0c4aa7310`.
  - `git merge main` (never rebase) before phase B and again before the packet.
  - Opus does the first build and the first review.
  - Commit with `git add -f` of explicit paths.
- **DB:**
  - only `assetops_k5_test` (and its harness clones);
  - the captures read K7-D's `assetops_demo3_kisiwa_test` through `serve` and never write to it;
  - never `assetops_demo3_full_test`;
  - no prepare, tick or suite.
- **Size 1.3** (range 1.15–1.5):

  | Item | Units |
  |---|---|
  | Night routes and text | 0.25 |
  | Night mode and records table | 0.3 |
  | Fuel Finding route and page | 0.25 |
  | Ref kind and Site Findings panel | 0.15 |
  | Tests | 0.2 |
  | Captures and pre-flight | 0.15 |

  That is +0.3 against §9.5's 1.0. The increase covers the Finding's own address and route (§9l.1 item 8), the records table and the Site panel, less the estate-list entry moved to K8.
- **Reading budget:**
  - this §9l.1–§9l.2;
  - §9d.2 (result terms) and §9d.5;
  - §9j.5 (read types) and §9j.7;
  - `F/sites/MiniPerformance.tsx:1308-1622`;
  - `F/shell/SiteAnalyticsFrames.tsx:330-380`;
  - `F/shell/operatorSiteRoutes.ts:150-170`, `:575-600`;
  - `F/sites/chainRef.ts`;
  - `B/finding_api.py:1-145`;
  - `B/chain/refs.py:1-200`;
  - `B/fuel_balance/model.py`;
  - `B/fuel_balance/adapters/postgres_fuel_balance_store.py`;
  - `B/work/adapters/postgres_fuel_records.py`;
  - v69 `frontend/mockups/v69/index.html:623-630`.

### 9l.3 K7 card: the Kisiwa story days in the demo prepare, 2.4 (range 2.15–2.7), in two phases, K7-D and K7-F

**What K7 delivers.**
- Kisiwa (KISIWA-001) as the fourth Site of `T/demo_combined.py`, built after EV by `T/demo_combined_kisiwa.py build`. The build covers:
  - the registration;
  - ten day-runs on the story calendar, with F0's operational actions entering through K0;
  - the delivery, dip and site-visit records, through K2's Work API;
  - the ten nightly fuel checks (K3);
  - the unexplained-fuel Finding (K4a);
  - the threads;
  - the Action, with its maintenance request;
  - in K7-F, the plan freeze and the evaluation (K6).
- One Kisiwa-only scratch prepare per phase, with its gate rows.
- **Unchanged:**
  - every Kobo, Cold and EV child, day, instant and step;
  - a three-Site prepare's `story.json` (byte-equal, pinned);
  - the shipped v1 log, the probe files and `probe-result.json`;
  - every product module: K7 edits tools and conversions only.

**Phases.**
- **K7-D (data), 1.9, starts now** (K0, K1, K2, K3 are merged).
  - Everything up to the Action, except the Finding raise and the Action itself, can be built and tested before K4a merges.
  - After K4a merges: `git merge main`, then the raise and Action steps, then the K7-D scratch prepare.
  - **K7-D merges on review ACCEPT with Kisiwa opt-in** (`--sites kobo,cold,ev,kisiwa`). The default prepare stays three Sites.
- **K7-F (freeze), 0.5, after K6 merges** (see "The freeze step" below). It flips the default to four Sites.

**The story calendar: `V/demo-kisiwa-story-v1.json` (new).** Offsets use the existing form `S[+-]<days>d HH:MM` (UTC) and resolve against the prepare's one `S`.
```json
{
  "schema": {"id": "assetops.demo-kisiwa-story", "version": 1},
  "label": "Kisiwa diesel-hybrid example Site: the F0 world (DIESEL-1 §8.3) placed on the story calendar by a whole-day move",
  "base_log": {"log_id": "kisiwa-001-operational-actions", "log_version": 1,
               "sha256": "77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634"},
  "base_run1_start": "2026-10-01T12:00:00Z",
  "run1_start": "S-9d 12:00",
  "runs": 10,
  "import_at": "S-11d 09:00",
  "install_at": "S-11d 09:30",
  "setup_at": "S-11d 11:00",
  "received_after_run_end_minutes": 10,
  "assess_after_run_end_minutes": 30,
  "raise_after_run_end_minutes": 31,
  "dip_recorded_after_minutes": 15,
  "site_visit_recorded_after_minutes": 15,
  "story_log_id_prefix": "kisiwa-001-story-",
  "action": {
    "raised_at": "S-5d 13:00",
    "title": "Seal the tank cap, sign the dip log at every shift change, and put the tank sensor on its own protected power supply",
    "owner_label": "Site lead",
    "request": {"occurred_at": "S-5d 13:10",
                "title": "Seal the tank cap and put the tank sensor on its own protected power supply.",
                "narrative": "Seal the tank cap and put the tank sensor on its own protected power supply. Sign the dip log at every shift change."},
    "request_recorded_from": "S-5d 13:10",
    "assign_at": "S-5d 13:20",
    "record": {"occurred_at": "S-4d 12:00",
               "activity": "Tank cap sealed; tank sensor moved to its own protected supply. The dip log is now signed at every shift change."},
    "complete_at": "S-4d 12:05",
    "change_recorded_from": "S-4d 12:10",
    "site_visit": {"occurred_at": "S-4d 12:00",
                   "body": "Tank cap sealed; tank sensor moved to its own protected supply."},
    "case_link_at": "S-4d 12:20",
    "effective_at": "S-4d 12:00"
  },
  "plan": {"freeze_at": "S-4d 12:30"},
  "evaluate_at": "S-1d 13:00"
}
```
- **Derived values:**
  - `delta_days = (resolve(run1_start) − base_run1_start) / 1 day`. A non-integer is stop **S-1** (`STORY_SHIFT_NOT_WHOLE_DAYS`).
  - Run k = `[run1_start + (k−1) d, run1_start + k d)`.
  - Night k = the Site-local date of run k's start.
- **The resulting story (night 1 = `S−9d`):**

| Night (local date) | Run k (UTC) | What happens (the F0 world, moved) |
|---|---|---|
| 1 `S−9d` | `S−9d 12:00` → `S−8d 12:00` | clean |
| 2 `S−8d` | `S−8d` → `S−7d` | delivery of 300 L at `S−7d 07:00` (10:00 local), recorded `07:30` |
| 3 `S−7d` | | clean |
| 4 `S−6d` | `S−6d` → `S−5d` | removal of 120 L at `S−6d 22:00–22:45` (01:00–01:45 local), sensor unplugged `21:50–23:20`; dip at `S−5d 04:00` (07:00 local), recorded `04:15`; nothing records the removal |
| 5 `S−5d` | | run 4 received `S−5d 12:10`; night 4 assessed `12:30` and raised `12:31`; **Action at `13:00` (16:00 local)**; request `13:10`, assigned `13:20` |
| 6 `S−4d` | `S−4d` → `S−3d` | the change at `S−4d 12:00` (15:00 local, run 6's start): seal, sensor power, site visit, maintenance record; COMPLETE `12:05`, link `12:20`; **plan frozen `12:30`**, before night 6 opens at `15:00`; dips at 18:00 and 06:00 local from here on |
| 7 `S−3d`, 8 `S−2d` | | after-nights; night 8 assessed `S−1d 12:30` |
| — | | **evaluation at `S−1d 13:00`** |
| 9 `S−1d`, 10 `S+0d` | run 10 ends `S+1d 12:00` | after-nights; night 10 assessed `S+1d 12:30`, at least 11.5 h before any prepare's DB now (`S+2d 00:00` or later) |

- What the calendar guarantees:
  - Night 4's window `[S−6d 15:00, S−5d 09:00)` lies inside the story week `[S−6d, S+1d)`, so the Portfolio Protect line (K4b, KIS-8a) can show it.
  - Night 8 closes before the S+0 board. The S+0 board's night D−1 is night 9 (WITHIN_MARGIN).
  - Kisiwa's install, `S−11d 09:30`, is distinct from Kobo `S−29d 11:00`, Cold `S−26d 06:00` and EV `S−26d 06:30`. It is later than all three, so Kisiwa builds last, and it is more than `install_min_lead_hours` before run 1.
  - The records' 30-day backdate window (`B/work/model.py:36-37`) holds: the earliest Kisiwa record occurs at `S−7d 07:00`.
- **Order check** (stop S-2, `STORY_CLOCK_ORDER`, the mill's `instants_in_order` pattern). Each instant must come before the next:
  1. the night-4 raise;
  2. `raised_at`;
  3. `request.occurred_at` (≤ `request_recorded_from`);
  4. `assign_at`;
  5. `record.occurred_at`, which equals `effective_at` and run 6's start;
  6. `complete_at`;
  7. `change_recorded_from`;
  8. the site visit's recorded instant;
  9. `case_link_at`;
  10. `plan.freeze_at`;
  11. night 6's window start;
  12. night 8 assessed;
  13. `evaluate_at`;
  14. run 10 received.

**The derived log, written for each prepare: `<work>/operational-actions/kisiwa-001-story-{yyyymmdd}-v1.yaml`,** where `yyyymmdd` is night 1's local date.
- Read `C/operational-actions/kisiwa-001-operational-actions-v1.yaml` from the prepare tree. Assert that its LF sha256 equals `base_log.sha256` (else stop S-3).
- Parse it with `B/runs/adapters/yaml_run_documents.load_yaml_text`.
- Set `log_id` to the story id. Keep `log_version: 1`, `site_code` and `timezone`, and keep every action mapping, in order, with every key.
- Add `delta_days` to each `at` and each `sensor_disconnected.at`, in the same `YYYY-MM-DDTHH:MM:SSZ` form. Nothing else changes.
- Write the file as:
  - four `#` comment lines: "Kisiwa story operational-action log (DIESEL-1-R3l). Derived by tools/demo_combined_kisiwa.py from config/operational-actions/kisiwa-001-operational-actions-v1.yaml (sha256 77777c82…b634) by a move of {N} whole days; no other change. Lab-private: the product never reads this file. Never edit by hand.";
  - then `json.dumps(doc, indent=2, ensure_ascii=True)`, with LF line endings and a trailing newline.

  JSON is valid YAML, so K0's loader reads it unchanged.
- Run setup gets `KisiwaRegistered(store, setup_at, actions=YamlOperationalActionLog(root=<work>/operational-actions))`, and `draft(..., operational_actions={"log_id": <story id>, "log_version": 1})` on **every** Kisiwa run. A run with no effect-bearing action freezes the log with `actions: []` (§9f.2 (2)).
- **Straddle check (K0's residual):** before any run is drafted, every action's span must lie inside exactly one run's `[start, end)`. The span is `[at, at]` for a point action, and `[at, at + duration)` for a removal and for its sensor span. Otherwise it is stop S-4. An L0 test runs the same check on the base log against F0's run list.

**The handover: `V/kisiwa-day-handover-v1.json` (new), written by `T/probe_kisiwa_fuel.py --handover`.** It is needed because the prepare tree is a `git archive` of `backend, gateway, host, simulator, contracts, config, contract-fixtures, tools` (`T/demo_combined.py:397`), so `.agent/DIESEL-F0/probe-result.json` is not available there.
- **Content:** a pure projection of the committed `probe-result.json`:
  ```
  {"schema": {"id": "assetops.kisiwa-day-handover", "version": 1},
   "source": {"probe_result_sha256": <LF sha256 of probe-result.json>, "actions_sha256": "77777c82…b634"},
   "base_run1_start": "2026-10-01T12:00:00Z",
   "runs": [{"k", "start": {"soc", "fuel"}, "end": {"soc", "fuel"}, "intervention_history"}] (10),
   "dips": [{"action_id", "at", "dip_l"}] (11),
   "nights": [{"k", "night_date", "readings": {"state", "gap_minutes", "opening_exact", "closing_exact",
               "deliveries_exact", "delivery_tolerance_exact", "loaded_litres_exact", "use_low_exact",
               "use_high_exact", "residual_low_exact", "residual_high_exact"}}] (10)}
  ```
  Keys are sorted, indent 2, LF. Exact values are F0's text, verbatim.
- `--handover` writes it from the committed result.
- `--check` also asserts that the handover equals the projection of a fresh run, and exits 1 otherwise.
- `--write` is unchanged, `probe-result.json` stays byte-equal, and `--check` still prints "probe result current". `T/probe_kisiwa_nights.py` is not edited.

**The Kisiwa child: `T/demo_combined_kisiwa.py build <url> <work>`.** This is a new subcommand; `register` is unchanged. It refuses any database that `require_prepare_database` (`B/prepare_clock.py`, as the mill tool uses it) does not accept. Steps:
1. **Read and check the inputs.** Read `<work>/story.json` (its `story["kisiwa"]` block, written by the parent, below) and the handover. Write the derived log and run the straddle check.
2. **Register.** `register(url, work, import_at, install_at)` (K1, unchanged; diesel price v1 at install + 1 h).
3. **Build one event timeline,** sorted by instant. Ties go in this order: record posts, then publish, then assess, then raise.
   - **Record posts** go through `build_work_service(url)` (`B/work/composition.py`, the Work API's service, as in `T/demo_combined_mill.py:131-134`). For each post, the store clock is set to the record's recorded instant (`_store.test_db_clock_override`). Bodies are built with `test_w401_work_service_postgres.oprec` and `PRINCIPAL`, exactly as in K3's parity test (`host/tests/test_k3_fuel_balance_parity.py:76-94`).
     - **The `FUEL_DELIVERY`,** from the log:
       - body `f"Fuel delivery of {volume_l} L received, ticket {ticket.reference}."` ("Fuel delivery of 300 L received, ticket KIS-DT-0001.");
       - `occurred_at` = the moved `at`, recorded `recorded_after_minutes` (30) later;
       - quantity `str(volume_l)`, unit L;
       - `source_document_sha256` = the sha256 of the ASCII text `f"Fuel delivery ticket {reference}, {volume_l} L"`;
       - `asset_id` = the tank; key `kisiwa-kis-delivery-1`.
     - **Each `TANK_DIP`:**
       - body `f"Tank dip at the {HH:MM local} round: {dip_l} L."`;
       - `occurred_at` = the moved `at`, recorded 15 min later;
       - quantity = the handover's `dip_l` for that `action_id`;
       - key `f"kisiwa-{action_id}"`.
     - **One `SITE_VISIT`,** covering `TANK_SEALED` and `SENSOR_POWER_PROTECTED` together:
       - body `action.site_visit.body`;
       - `occurred_at` `S−4d 12:00`, recorded `S−4d 12:15`;
       - `case_id` = the Action's maintenance request (step 5); no quantity;
       - key `kisiwa-kis-sealed-1`.
     - `FUEL_REMOVAL_UNRECORDED` posts **nothing**.
   - **Publish run k** at run end + 10 min:
     - the start state comes from the handover's `runs[k−1].start` (the probe's own chaining);
     - the document is `probe_kisiwa_nights.day_document(soc, fuel)`;
     - draft through `host/tests/kisiwa.py` `KisiwaRegistered(store, setup_at, actions=…)`, with the request key;
     - assert READY and that `registered_basis` is present;
     - then call `test_s6_verification_replay._publish_and_accept(<work>/kisiwa-replay/r{k:02d}, run, f"epoch-{k}", run_end + 10 min)` (K3's call).

     Guards. Each failure is stop S-5, reported with both values:
     - the frozen `intervention_history` holds exactly the run's effect-bearing actions (run 2 the delivery, run 4 the removal, the others none), and the frozen log `sha256` equals the derived file's LF hash;
     - **physics:** the last boundary of `run_to_end(run, reg.sim("v7"))` has tank and SOC exactly equal to the handover's `runs[k−1].end`;
     - **dips:** for each dip in run k, the trajectory's tank at the dip instant, rounded half-even to 1 L, equals the handover's `dip_l`.
   - **Assess night k** at run end + 30 min. Call `fuel_balance.worker.main(["assess", "--site", "KISIWA-001", "--from", night_k, "--to", night_k + 1 d], store=<build_fuel_balance_store(url, test_db_clock_override=clock)>)`, with `clock` set to that instant. This is the K3 CLI entry point, in process (§9l.1 item 5). The printed line must be `APPENDED`, revision 1.
   - **Raise night k** at run end + 31 min: `build_fuel_finding_service(url, test_db_clock_override=clock).raise_night(tenant, site, night_k)` (K4a). Night 4 must give `OPENED`, and every other night `NO_FINDING`. Anything else is stop S-6.
4. **Threads, Kisiwa only.** Run `python -m assetops_backend.chain.backfill --site KISIWA-001 --steps a,b,c,d` as a child process in the tree, after the timeline and after the Action (step 5). It never runs for another Site, and the Kisiwa child runs no tick (§9l.1 item 7).
5. **The Action and its change.** These run after the timeline, and every stamp is its story instant. They follow the mill's `record_change` pattern (`T/demo_combined_mill.py:126-184`) with Kisiwa's literals:
   - **The Action:** `build_domain_intent_service(url).create_action(tenant, site, "KISIWA-001", {"domain": "MINI", "origin_finding_id": <night-4 Finding>, "origin_finding_revision_id": <its revision>, "title": action.title, "owner_label": "Site lead", "due_at": None, "raised_at": "S−5d 13:00", "actor": ACTOR, "idempotency_key": "kisiwa-fuel-action"}, PRINCIPAL)`, with the domain store's clock at `raised_at`. PRE-FLIGHT (b) names the two origin keys. A refusal of a `fuel_balance` origin is stop S-7 (K6 rules on the Action path, §9j.14).
   - **The maintenance request:** kind `MAINTENANCE_REQUEST`, `asset_id` None, the request's title and narrative, key `kisiwa-fuel-request`, recorded from `request_recorded_from`. Then `ASSIGN` to "Site lead" at `assign_at` (key `kisiwa-fuel-assign`).
   - **The change:** the maintenance record (`activity`, `occurred_at` `S−4d 12:00`, key `kisiwa-fuel-record`) and `COMPLETE` at `complete_at` (key `kisiwa-fuel-complete`). Both are recorded from `change_recorded_from`, using a second `StepClock`, so nothing is recorded before it occurred. Then the `SITE_VISIT` record of step 3.
   - **The link:** `post_case_link` at `case_link_at` (key `kisiwa-fuel-link`).
6. **Checks in the child: the CLI calls, as known now.**
   - `worker.main(["assess", "--site", "KISIWA-001", "--from", night 1, "--to", night 11], store=<store with the DB clock>)` must print 10 lines, all `REUSED`, revision 1.
   - K4a's `worker.main(["raise", …])` must give night 4 `UNCHANGED` and the others `NO_FINDING`. If that entry point takes no injected service, call `raise_night` per night instead (PRE-FLIGHT (c)).
   - Anything else is stop S-6.
7. **Write `<work>/kisiwa.json`.** It holds:
   - the register result;
   - `delta_days`, and the derived log's path, id and sha256;
   - per run: `run_id`, start, end, received, history, the physics and dip checks, seconds;
   - per record: code, kind, occurred, recorded, quantity;
   - per night: the window id, revision, state, band, gap and stamps;
   - the Finding: id, revision, consequence id, thread id;
   - the Action: id, code, case id, link;
   - the CLI lines;
   - K7-F's plan and verdict.

**`T/demo_combined.py` changes (exact; the three-Site path stays byte-equal):**
- **Constants:**
  - `CORE_SITES = ("kobo", "cold", "ev")`;
  - `SITES = CORE_SITES + ("kisiwa",)`;
  - `SITE_CODE["kisiwa"] = "KISIWA-001"`;
  - `EXPECTED_SECONDS["kisiwa"] = 2520`: 10 days at about 240 s each (K1's and K3's 3–5 min per gateway day), plus 120 s for the register;
  - `KISIWA_STORY_FILE = REPO / "backend" / "conversions" / "demo-kisiwa-story-v1.json"`.
- **`objectives_instants`** iterates `CORE_SITES`. Kisiwa declares no objectives in K7; K8 rules on Kisiwa objectives with the four-Site estate.
- **`resolve_story(db_now, doc=None, days_doc=None, kisiwa=False)`:**
  - every existing loop over `SITES` iterates `CORE_SITES`;
  - only when `kisiwa` is true:
    - `story["kisiwa"] = demo_combined_kisiwa.resolve(S, kisiwa_doc)`, imported inside the function (the module imports `at` and `iso` from `demo_combined`);
    - the four installs are asserted distinct, with Kisiwa's after all three (else `INSTALL_CLOCK_CONFLICT`);
    - Kisiwa's install plus the lead must precede run 1;
    - `"kisiwa"` is appended to `install_order`;
  - `story["installs"]` stays the three core Sites;
  - **with `kisiwa=False` the output equals today's** (pinned, test L0-1).
- **`prepare`** passes `kisiwa="kisiwa" in sites`.
- **`finish_build` and `finish`:** each `set(story["sites"]) == set(SITES)` becomes `set(CORE_SITES) <= set(story["sites"])`. The mini-depth drain in `finish` runs when `{"kobo", "kisiwa"} & set(story["sites"])` is non-empty.
- **`story_links`:** when `"kisiwa"` is in `story["sites"]` and `<work>/kisiwa.json` exists, add these rows:
  - "KISIWA-001 board, morning after the unexplained-fuel night (S-5d)": `/sites/KISIWA-001?date={S−5d}`;
  - "KISIWA-001 board, day S": `/sites/KISIWA-001?date={S}`;
  - "KISIWA-001 Fuel, night S-6d": `/sites/KISIWA-001/performance/fuel?night={S−6d}`;
  - "KISIWA-001 unexplained-fuel finding": `/sites/KISIWA-001/fuel-findings/{id}`.

  `LINK_FORMS` gains `"/sites/KISIWA-001?date="`, `"/sites/KISIWA-001/performance/fuel?night="` and `"/sites/KISIWA-001/fuel-findings/"`. K7-F adds the verification form that K6 names.
- **`--sites` default:** `",".join(CORE_SITES)` in K7-D; `",".join(SITES)` in K7-F.
- **`add-day`** for KISIWA-001 keeps today's refusal (there are no Kisiwa day kinds). Nothing else changes.
- **Not edited:** the Kobo, Cold and EV children, `demo_story_days.py`, `demo-combined-story-v1.json` and `demo-story-days-v3.json`.

**The freeze step (K7-F, after K6 merges).** K6's card is not written yet. K7-F's exact calls are folded into this card at K6's card round. What is fixed now:
- **When:**
  - The plan freezes at `plan.freeze_at` (`S−4d 12:30`): after the case link, and before night 6's window opens.
  - The evaluation runs at `evaluate_at` (`S−1d 13:00`), after night 8 is assessed.
  - Both are story instants, set through K6's service with the test-only clock seam, as the mill step does (`T/demo_combined_mill.py:282-293`).
- **The effective instant** is `S−4d 12:00` (15:00 local, run 6's start). K6's card names the field that carries it: the Action, the case COMPLETE or the plan. If K6 pins a different mechanism, K7-F follows K6's card.
- **The verdict:** K7-F records it **as computed** (VERIFIED, INEFFECTIVE or INCONCLUSIVE) in `kisiwa.json`. It never asserts a verdict. KIS-5 (K9) reads it.
- **What else K7-F does:**
  - it flips the default `--sites`;
  - it adds the verification link form;
  - it extends KIS-9 (e);
  - it runs the second scratch prepare.

**Finish rows** (pure logic in `T/demo_combined_rows.py`, wired in `T/demo_combined_finish.py` after KIS-4; each has L0 self-tests with pass and fail bodies).
- **KIS-3 (moved from K9 to K7, because it checks K7's data).** For nights 1–10, take the latest stored window, as known now:
  - **Exact:** `state`, `reason` (None), `gap_minutes`, opening, closing, D and D_tol equal the handover's night exactly.
  - **Within 1/100000 L:** `loaded_litres`, `use_low`, `use_high`, `residual_low`, `residual_high`. This is K3's parity rule (§9d.6 C): power is published at 0.000001 kW, so §8.4's "exact" is corrected for these five terms.
  - **Reproduced:** the band re-computed by `B/fuel_balance/rules.balance` from the stored terms equals the stored band exactly.
  - **Night 4:** `UNEXPLAINED`; `gap_spans` = F0's `[21:45, 23:30)` UTC (K3's literal) moved by `delta_days`; limitations `("REPORTING_GAP",)`.
  - **Every other night:** `WITHIN_MARGIN`, gap 0, no limitation.
  - **All ten nights:** `idle_seconds` 0.
- **KIS-9 (new): Kisiwa story coherence.**
  - (a) **Records:**
    - exactly one `FUEL_DELIVERY` (300 L, the ticket digest), recorded 30 min after it occurred;
    - eleven `TANK_DIP`s, one per log dip, each recorded 15 min after it occurred;
    - one `SITE_VISIT`, with `action.site_visit.body`;
    - **no** operational record of the Site occurs inside the removal's span or names the removal.
  - (b) Each dip's stored quantity equals the handover's `dip_l` and the build's trajectory check in `kisiwa.json`.
  - (c) Every action of the derived log lies inside exactly one run's `[start, end)` (the K0 residual).
  - (d) **The Finding:** exactly one fuel Finding, SUPPORTED, citing night 4's window revision 1, on one `UNEXPLAINED_FUEL` thread. Its consequence is PRICED at Kisiwa diesel v1. No other night has a fuel Finding.
  - (e) **The Action:** its origin is that Finding; its case is COMPLETE and linked; the site-visit record cites the case. K7-F adds: the plan is frozen at `plan.freeze_at`, and a verdict is stored at `evaluate_at`.
  - (f) Every Kisiwa run's frozen identity names the derived log (its id, version 1, its sha256), and its history holds exactly that run's effect-bearing actions.
  - (g) **Stamps are story instants:**
    - each window's `recorded_at` = run end + 30 min;
    - night 4's Finding revision `created_at` = run end + 31 min;
    - every record's `recorded_at` is as the calendar says.
- KIS-1, KIS-2, KIS-5, KIS-6, KIS-7 and KIS-8 stay K9's (with K4b's KIS-8a). K9's size is unchanged.

**The Kisiwa-only scratch prepare (one per phase).**
- **Command:** `python tools/demo_combined.py --db assetops_demo3_kisiwa_test --work var/demo3_kisiwa prepare --sites kisiwa --cap-seconds 5400`. The database name matches `^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$` (`T/demo_combined.py:53`) and the authorized `*_test` rule.
- **When:**
  - K7-D: after its L0 tests are green and committed, and after K4a has merged into the branch.
  - K7-F: after K6 has merged into the branch.
- **Gate before starting (all required):**
  - **Only one heavy job** on the machine: no other prepare, suite, L2 run or template rebuild. The coordinator confirms the other lanes are idle.
  - **RAM gate:** at least 2.5 GB free for 2 consecutive minutes, sampled every 30 s. The samples go in the packet.
  - `tools/keep-awake-during-tests.ps1` is running (no `-ExecutionPolicy`).
- **During:**
  - Sample free RAM and the prepare's peak working set every 60 s, and record the peak.
  - If free RAM drops below 1.0 GB: stop, drop the DB and the work folder, and report (S-8).
  - **Cap 5400 s:** the tool's 2× rule over about 42 min, enforced by the tool.
  - A stall with no output for 10 min is reported, not retried.
- **Reads:** `T/demo_combined_kisiwa.py check <url> <work>` runs KIS-3, KIS-4 and KIS-9 against the scratch DB and prints one JSON line per row. Every row must pass. The packet records:
  - seconds per Kisiwa day;
  - the register, assess and raise times;
  - the whole wall time (K9's E3 figure).
- **Afterwards:**
  - K7-D **keeps** the database and work folder, for K5's captures (read-only `serve`).
  - K7-F's prepare replaces them: the tool drops and recreates a database whose marker it owns.
  - K7-F runs `drop` after its packet evidence is recorded.

**Tests (localised; no full suite).**
- **L0 `backend/tests/test_k7_kisiwa_story.py` (no DB; it imports the tools as K3's tests do).** Every "must fail" names its mutation.
  1. **The three-Site story stays byte-equal.** `resolve_story(db_now)` with `kisiwa=False`, for two fixed `db_now` values, equals pins taken on main **as the branch's first commit**, before any production edit (the K0 precedent). Must fail if any core loop iterates `SITES`.
  2. **Kisiwa resolve:**
     - the table above, for a fixed `S`;
     - `delta_days` integral, and `STORY_SHIFT_NOT_WHOLE_DAYS` for a half-day `run1_start`;
     - install order, distinctness and lead;
     - `STORY_CLOCK_ORDER` for each adjacent pair swapped.
  3. **The derived log:**
     - its parsed actions, minus `at` and `sensor_disconnected.at`, equal v1's;
     - each moved instant differs by exactly `delta_days`;
     - the header lines, and LF;
     - K0's `freeze_operational_actions` accepts it for runs 2 and 4 with a matching id, and refuses `OPERATIONAL_ACTION_LOG_MISMATCH` if the id is left as v1's.
  4. **Straddle:** the base log against F0's run list passes. A synthetic dip at a run's end instant fails, and so does a removal that crosses a run start.
  5. **Injector bodies:** the delivery, the night-4 dip and the site visit match their literals; the removal yields no body.
  6. **Timeline order,** for a fixed `S`: records come before the publishes they precede, and assess comes before raise.
  7. **Handover:** `--handover`'s output equals the projection of the committed result; `--check` exits 0; a one-character change in the handover makes `--check` exit 1.
  8. **Prepare paths:**
     - `finish_build` takes the after-children path for `{kobo, cold, ev}` and for all four Sites, and not for `{kisiwa}` alone;
     - `objectives_instants` never sees KISIWA-001;
     - `LINK_FORMS` covers every printed Kisiwa link.
  9. **Row self-tests:** KIS-3 and KIS-9 (one pass body, and one fail body per item).
- **Must stay green unchanged:**
  - every existing `T/demo_combined*` test;
  - both probe `--check`s ("probe result current");
  - K0's, K1's, K2's, K3's and K4a's tests;
  - `test_out_b2_vocabulary.py`, which gains only the Action, request and record literals.
- **Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1` and `tools\check-agent-workflow.ps1`, run directly, with no `-ExecutionPolicy`.

**PRE-FLIGHT (no code first; batch every question in one message).**
- (a) Confirm, with file:line, that `YamlOperationalActionLog(root=…)` reads a work-folder root, and that `host/tests/kisiwa.py` `draft(..., operational_actions=…)` forwards the key.
- (b) The `create_action` body keys for a Finding origin (file:line in the domain intent service), and whether it checks the origin's domain.
- (c) K4a's merged `raise` entry point: does `worker.main` take an injected service or store?
- (d) Confirm that `_publish_and_accept` accepts a K0-frozen run (causes with `origin` and `action_ref`) unchanged. K3 proved it for F0's carrier.
- (e) Where the existing `T/demo_combined*` L0 tests live, so that `test_k7_kisiwa_story.py` follows them.
- (f) `require_prepare_database`'s rule, and confirmation that `assetops_demo3_kisiwa_test` passes it.

**Stops (report to the Architect and the coordinator; never design around them).**
- **S-1** a day move that is not a whole number of days.
- **S-2** a break in the story-clock order.
- **S-3** the shipped v1 log's hash differs from `77777c82…b634`.
- **S-4** an action straddles a run start, or lies in no run.
- **S-5** a run guard fails (history, log hash, physics or dip). Report the run and both values. **Never** change a start state, an action, the seed, the calendar move or the handover.
- **S-6** an assess or raise status differs from this card, or KIS-3 fails. Never edit K3's parameters, the tolerance, the probe or its result.
- **S-7** `create_action` refuses a `fuel_balance` origin (K6 rules).
- **S-8** the RAM floor or the cap is reached.
- **S-9** for a three-Site prepare, a Kobo, Cold or EV step, instant or `story.json` field changes (L0-1); or a need to edit their children, the day list or the shared story file.
- **S-10** a need to edit product code under `B/`, `F/`, `contracts/` or `S/`, or `host/execution_adapter.py`, or the shipped log.
- **S-11** more than 2.2 units in K7-D, or more than 0.7 in K7-F.

**Files (approved list):**
- New: `V/demo-kisiwa-story-v1.json`, `V/kisiwa-day-handover-v1.json`.
- `T/demo_combined_kisiwa.py`: `resolve`, `build`, `check`, the derived log and the injector.
- `T/demo_combined.py`: the changes above only.
- `T/probe_kisiwa_fuel.py`: `--handover` and its `--check`.
- `T/demo_combined_rows.py` and `T/demo_combined_finish.py`: KIS-3 and KIS-9.
- `backend/tests/test_k7_kisiwa_story.py`, and its pins module (the first commit).
- `backend/tests/test_out_b2_vocabulary.py`: literals added to the scan list.

**Dependencies, start, branch, DB, size.**
- **Dependencies:**
  - K7-D depends on K0, K1, K2 and K3 merged (all yes). Its raise and Action steps need K4a merged, and its scratch prepare needs both.
  - K7-F depends on K7-D merged and K6 merged.
- **Lanes:**
  - K7-D: lane 2 after A3, or any builder free now. Its first ~1.2 units need nothing from K4a.
  - K7-F: lane 3, straight after K6 (critical path).
- **Branches:**
  - K7-D: `task/DIESEL-K7-kisiwa-story`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k7`, from main at or after `0c4aa7310`.
  - K7-F: a fresh branch `task/DIESEL-K7F-kisiwa-freeze`, from main after K6 merges, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k7f`.
  - `git merge main`, never rebase. Opus does the first build and the first review in each phase. Commit with `git add -f` of explicit paths.
- **DB:**
  - only `assetops_demo3_kisiwa_test` with `var/demo3_kisiwa` (the scratch prepare); K7 has no other L2 test;
  - never `assetops_demo3_full_test` or any other DB;
  - no tick, no suite, and no `serve` except K5's read-only captures on the kept K7-D DB.
- **Size 2.4** (range 2.15–2.7), +0.15 against §9.5's 2.25.

  K7-D, 1.9:

  | Item | Units |
  |---|---|
  | Calendar, resolver, `demo_combined` changes and pins | 0.35 |
  | Handover | 0.15 |
  | Derived log and straddle check | 0.1 |
  | Build child, runs through K0, and guards | 0.35 |
  | Injector | 0.15 |
  | Assess, raise, threads and CLI checks | 0.15 |
  | Action and change | 0.15 |
  | KIS-3 and KIS-9 | 0.2 |
  | L0 tests | 0.15 |
  | Scratch prepare and evidence | 0.15 |

  K7-F, 0.5:

  | Item | Units |
  |---|---|
  | K6 wiring | 0.15 |
  | Default, links, KIS-9 (e) | 0.1 |
  | Second scratch prepare and evidence | 0.2 |
  | Packet | 0.05 |

  The +0.15 pays for the whole-day move (§9l.1 items 1–3) and for the story-instant stamping (item 5), neither of which §8.4 foresaw.
- **Reading budget:**
  - this §9l.1 and §9l.3;
  - §8.3's declared world; §9f.2 (5)–(6); §9d.4 (store, CLI); §9j.6;
  - `T/demo_combined.py:1-200`, `:360-560`;
  - `T/demo_combined_kisiwa.py`;
  - `host/tests/kisiwa.py`;
  - `host/tests/test_k3_fuel_balance_parity.py`;
  - `T/demo_combined_mill.py:120-300`;
  - `T/demo_combined_kobo.py:355-480`;
  - `T/probe_kisiwa_fuel.py:1-60`, `:200-260`, `:700-804`;
  - `C/operational-actions/kisiwa-001-operational-actions-v1.yaml`;
  - `V/demo-combined-story-v1.json`.

### 9l.4 Effects on other cards

- **K4b:**
  - the board issue links with `refs.fuel_finding_ref(c, finding_id)` (K5), not `refs.finding_ref`;
  - `FUEL_REASON_WORDS` is imported from `B/fuel_balance/night_text.py` (K5), not retyped;
  - K4b starts after K5's phase B build;
  - everything else in §9j.10–§9j.13 stands.
- **K6:**
  - its verification page links the origin Finding with `fuel_finding_ref`;
  - its card names the effective-instant field, and the freeze and evaluate calls K7-F makes, with K7's instants (`effective_at` `S−4d 12:00`, `freeze_at` `S−4d 12:30`, `evaluate_at` `S−1d 13:00`);
  - its pre-flight confirms that `create_action` accepts a `fuel_balance` origin. If K7-D has already stopped on S-7, K6 rules on it.
- **K8:**
  - gains the fuel Finding's entry in the estate Findings lists (+0.15; K8 is now 1.0, range 1.0–1.25 with §9c.4's device-copy risk);
  - rules on Kisiwa objectives;
  - its all-26 recapture adds the Kisiwa pages K5 built.
- **K9:**
  - KIS-3 has moved to K7;
  - the DS-1 beat's dates come from `links`;
  - the E3 Kisiwa figure is K7-F's measured wall time.
- **§8.6 is superseded** for the Action's time: 16:00 local on day 5 (§9l.1 item 6). Its title, effective instant, night 5 and the after-nights stand.

### 9l.5 Order, lanes, critical path, tripwire, size and date

**Remaining Kisiwa order** (lane-units; about 3 per lane-day including review):
```
now (t=0):    K4a (lane 3, in build, 1.5) | A3 (lane 2, pre-flight, 0.91) | K5 phase A (lane 1, 0.75)
              K7-D phase 1 (any free builder; else lane 2 after A3)
t≈0.9:        A3 merged -> K7-D (lane 2, if not started)
t≈1.5:        K4a merged -> K6 (lane 3, 1.5) | K5 phase B (lane 1) | K7-D raise + Action
t≈1.95:       K5 build done -> K4b (lane 1, 1.0)
t≈2.6–2.8:    K7-D scratch prepare (about 45 min machine time) -> K5 captures -> K5 merged; K7-D merged
t≈2.95:       K4b merged -> K8 code (lane 1, 1.0–1.25)
t≈3.0:        K6 merged -> K7-F (lane 3, 0.5, incl. its scratch prepare)
t≈3.5:        K7-F merged -> K8 captures (0.25)
t≈3.75–4.75:  K9 (finish rows, guard, rehearsal prepare)
then:         DS-1 -> E1–E6
```
- **Critical path:** spent 3.65 (F0r, K1, K3) → K4a 1.5 → K6 1.5 → K7-F 0.5 → K8 captures 0.25 → K9 1.0 ≈ **8.4 lane-units**. K6's size is §9.5's figure; its card is not yet written. **That is below the 9.75 tripwire, with about 1.35 of headroom. No cut.**
- **K7-D stays off the critical path** if it merges before K6 does (t≈3.0).
  - Started on lane 2 at t≈0.9, it ends at about 2.8: about 0.2 of float.
  - Started now, it has about 1.0 of float.
  - **Recommendation to the coordinator: start K7-D now, on a free builder.**
- **Lane 1** (K5 1.3 → K4b 1.0 → K8 ≤ 1.25) ends at about 3.55, beside K7-F, and joins at the captures.
- **Sizes:**

  | Unit | Before | Now |
  |---|---|---|
  | K5 | 1.0 | **1.3** |
  | K7 | 2.25 | **2.4** |
  | K8 | 0.85 | **1.0** (the estate Findings entry) |

  Net **+0.6**, reported, not absorbed (the contingency is spent, §9h.8). **Kisiwa total: 17.7 → 18.3.**
- **Demo date: unchanged** at about +3.25 working days (range 2.75–5.25). The extra 0.6 sits on lanes 1 and 2, beside the critical path.
- **Machine time:** two Kisiwa-only scratch prepares of about 45 min each (K7-D and K7-F).
- **E3:**
  - Kisiwa's share is now about 45–50 min, not R2's 25–35. That covers 10 gateway days at 3–5 min each, the register, assess, raise, threads and its mini-depth drain.
  - So **E3 ≈ 1.45–1.65 h of the 3 h cap.**
  - K9 restates the figure from K7-F's measured time. If the rehearsal exceeds 2.5 h, the Architect rules before E3.
- **Plan HTML rows (for the coordinator):**
  - **Build-units table:** the DIESEL-1-R3 row becomes 18.3, with "K5 1.3, K7 2.4 (K7-D 1.9, K7-F 0.5), K8 1.0".
  - **Lanes figure:** K7-D on lane 2 (or on a fourth builder now); K7-F on lane 3 after K6.
  - **Rulings table:** add "DIESEL-1-R3l: K5 and K7 cards; Kisiwa story = F0 world moved by whole days into the story week (derived log per prepare, never editing v1); stamps at story instants through the K3/K4a test-only clocks; Action at 16:00 local (after night 4's data arrive); fuel Finding at its own address (FUEL_FINDING ref); Fuel page night mode; KIS-3 to K7, KIS-9 new".
  - **E3 row:** "Kisiwa: 10 day-runs, about 45–50 min; E3 ≈ 1.45–1.65 h of the 3 h cap".
  - **Machine-time note:** two 45-min Kisiwa scratch prepares.

### 9l.6 Owner questions

None.

For the owner's information, in plain words:
- **The dates move, nothing else does.** The Kisiwa example days are the same ten days we already tested, moved onto the demo calendar so that the missing-fuel night falls in the week the demo shows. The fuel, the readings and the result are identical.
- **The fix is now agreed in the afternoon after the bad night.** Before, it was agreed at lunchtime, before that night's readings could have arrived. Now it comes once they have.
- **New screens for Kisiwa only.** The fuel page gets a night-by-night view for Kisiwa, and the finding gets its own page. Kobo's fuel page stays as it is.
- **The demo date does not move.** The work is about 0.6 unit bigger, all of it outside the longest chain of dependent steps.
- **Preparing the demo takes a little longer.** The full demo preparation takes about 15 minutes more than first estimated. That is still well inside its 3-hour limit.

---

## 9m. Ruling DIESEL-1-R3m: K7-D stop S-7 (the fuel Finding as an Action origin) and the K6 consolidated card, split K6a / K6b

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `4f6a5cae4`. K4a read on `task/DIESEL-K4a-unexplained-fuel-finding` at `ee86b5dea` (review packet; migration `0056_unexplained_fuel_finding`; `fuel_balance/finding_text.py`, `model.py` `FuelFinding`/`FuelFindingReadPort`, `composition.build_fuel_finding_service`).
- Owner decisions in force, verbatim: `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'"); `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions"); `.agent/owner-kisiwa-scope-2026-11-07.md` ("Build it, with the action link (Recommended)").
- **This ruling replaces** the K6 rows of §8.4 and §9.5, §8.5 (folded in below; its decisions stand except where named) and §9l.4's K6 bullets. It amends one line of §9l.3 (K7-D step 5) and fixes K7-F's freeze calls. Builders read only their part: K6a = §9m.1–§9m.3; K6b = §9m.1, §9m.4; K7 = §9m.5.
- **H1–H5 (§8.2) bind every literal below.** Each client literal was checked by hand against guard V (`F/test/productVocabulary.json`: run/runs/ran/running, load, claim, candidate, necessary, analytic, scenario, simulat*, draft, commit, fixture, stage, mapping, binding, payload, replay, digest, UUID and the closed upper-case codes) and against H4 (theft, stolen, stole, siphon, pilfer). None contains a money figure, a currency or a price. "Modelled use" replaces "running" (K4a's precedent). Guard V's own run is the builder's acceptance (stops S-a6 / S-a6b).
- READ = the Architect read the code at `4f6a5cae4` (and K4a at `ee86b5dea`); nothing was run.

### 9m.1 Code reality: why S-7 fires, and the decisions it forces (READ)

1. **Three independent refusals, not one.**
   - `work/domain_action.py:118` `MINI_SPEC` has `origin=ORIGIN_OPPORTUNITY`, so `_action_body` (`:283-294`) demands the opportunity pair and refuses `origin_finding_*` keys.
   - `work/domain_intent.py:102-109`: a Finding origin needs `revision["domain"] == spec.finding_domain` (no spec has `fuel_balance`), then `tx.selected_pin(revision)`. That is `work/adapters/postgres_work_read.py:299-309` `_pin`, which returns None for any domain other than `mini_grid`, `cold_chain`, `ev_charging`. So even a `fuel_balance` spec would be refused at the pin.
   - **The database refuses it too.** `0051_action_opportunity_origin.py:78-79` `domain_action_mini_origin CHECK ((domain = 'MINI') = (origin_opportunity_id IS NOT NULL))`: a `MINI` Action with a Finding origin cannot be stored.
2. **Options weighed.**
   - **(A) A new Action domain `FUEL_BALANCE`, Finding origin. Chosen.** It follows the Cold/EV pattern (`COLDCHAIN`/`cold_chain`, `EV_CHARGING`/`ev_charging`). `domain_action_mini_origin` stays exactly as it is and, unchanged, forces `FUEL_BALANCE` to carry a Finding origin. The mill's `MINI` contract and every MINI reader stay byte-equal. One DDL line widens `domain_action_domain_chk`.
   - **(B) Let `MINI` take either origin.** Rejected. It relaxes `domain_action_mini_origin`, and several readers treat `MINI` as "the mill" (`actions/verification.py:387`, `verification_families.py:137`, the MB-1 board path). Each would need a second test. It mixes two levers under one literal.
   - **(C) A W1 `action` (the reserve-trial table).** Rejected: its plan columns are reserve-shaped (Foundation change, battery asset, 60-minute windows; 0019, 0052's reserve arm).
   - **(D) Let K7-D write the Action with SQL.** Rejected: it bypasses the sole writer and K7's S-10.
3. **The fuel selection check.** A fuel Finding has no dispatch, cold or EV selection to pin. Its "selected" revision is simply the Finding's latest revision as known, if it is SUPPORTED (K4a's lifecycle, §9j.4). K6a adds that check to the domain-intent transaction and skips `selected_pin` for the fuel domain. `_pin` is not edited.
4. **Readers keyed by Action domain** (`git grep "FROM domain_action"`, READ):
   - `work/adapters/postgres_domain_action_index.py:66-79`: the Cold/EV Action surface. It excludes the mill by `origin_opportunity_id IS NULL`, so a fuel Action would appear there, where the page dispatches by `spec_of` and Cold/EV criteria. **Decision:** both predicates become the positive `domain IN ('COLDCHAIN', 'EV_CHARGING')`. Today this is the same set: 0051 ties `MINI` to the opportunity pair, so `origin_opportunity_id IS NULL` holds exactly for those two domains. The R3k precedent applies (a positive filter, never a deny-list).
   - `work/adapters/postgres_work_read.py:93` `_FINDING_DOMAIN_OF` (the maintenance request's domain-link lineage, `:275`). Without an entry the request page would show the fuel Action's link with broken lineage. **Decision:** one entry, `"FUEL_BALANCE": "fuel_balance"`. The row then reads like the mill's: lineage true, pin None. `backend/tests/test_w504_ev_intent_postgres.py:154` pins the map; it gains that one key (an approved assertion edit; the Cold and EV values are unchanged).
   - Safe as they are: `actions/adapters/postgres_action_store.py:298` (the code collision check) and `:748` (the mill context, which refuses non-MINI); `chain/adapters/postgres_chain_read.py:89`; `chain/adapters/postgres_thread_sources.py:73`, `:185`; `chain/lookup.py:44`; `work/adapters/postgres_work_read.py:52` (codes).
5. **The chain links the Action to the fuel thread with no new code.** `postgres_thread_sources.py:44-56` links a `DOMAIN_INTENT` by `origin_finding_id`, and K4a's thread (`UNEXPLAINED_FUEL`, ASSET, tank) holds the Finding. K7's Kisiwa-only backfill (`--steps a,b,c,d`, §9l.3 step 4) runs after the Action.
6. **But the chain's Action Ref would be wrong.** `chain/site_chain.py:147-152` `action_wire_ref` gives every Finding-origin `DOMAIN_INTENT` an `ACTION` Ref (`/sites/{site}/actions/{id}`, the W1 Action page). The fuel Action has no W1 row, so the link would show "not found". `_SITE_ACTIONS` (`postgres_chain_read.py:83-101`) does not carry the Action domain. **Decision (K6b):** `_SITE_ACTIONS` gains an `action_domain` column (a scalar subquery, like `accepted_at`; no view or DDL change), and `action_wire_ref` sends a `FUEL_BALANCE` Action to its verdict page, as DD1b2-R6 O1 did for the mill.
7. **The verification store is domain-ready but mill-hardwired.**
   - 0052 already made `verification_plan`, `verification_evaluation_request` and `verification_outcome` domain-Action-capable (`domain_action_id`, the three one-of CHECKs). Only the family CHECK (`verification_plan_family`) and the `rule_id`/`plan_version` CHECKs name the families. 0057 adds the fuel arm.
   - `VerificationService.freeze_domain_plan`/`evaluate_domain_plan`/`domain_summary` (`actions/verification.py:356-397`) call `FAMILIES[MIDDAY]` directly, and `domain_summary` refuses non-MINI. **Decision:** the mill methods stay byte-equal. K6b adds three fuel methods beside them, and a separate store context and freeze for the fuel plan, so the mill's `DOMAIN_PLAN_COLUMNS`, `domain_plan_context` and plan wire stay byte-equal. The outcome writer, the outcome read and `example_source_class` are shared unchanged.
8. **Why split.** The origin fix (K6a, about 0.6) unblocks K7-D's Action step and is small enough to merge fast. The verification family, verdict page and board entry (K6b, about 1.4) follow. **One migration (0057), owned by K6a, carries both DDL parts.** K6b then needs no migration, and the family columns are pinned now, in §9m.2.

### 9m.2 Migration `backend/migrations/versions/0057_fuel_verification.py` (owned by K6a)

`revision = "0057_fuel_verification"`, `down_revision = "0056_unexplained_fuel_finding"`. The renumber rule (§8.4) stands: if another migration lands first, K6a takes the next number. The head-agnostic single-head test (§9j.8 B6) catches a miss.

1. **Action domain.** `ALTER TABLE domain_action DROP CONSTRAINT domain_action_domain_chk, ADD CONSTRAINT domain_action_domain_chk CHECK (domain IN ('COLDCHAIN', 'EV_CHARGING', 'MINI', 'FUEL_BALANCE'));` `domain_action_mini_origin`, `domain_action_one_origin`, the FKs and the code-collision trigger are **not** touched. Unchanged, they force a `FUEL_BALANCE` row to carry the Finding pair.
2. **Verification families.** In one `ALTER TABLE verification_plan`, drop and re-add, by the same names:
   - `verification_plan_plan_version_check CHECK (plan_version IN ('reserve-trial-verification-1', 'midday-productive-shift-verification-1', 'fuel-residual-verification-1'))`;
   - `verification_plan_rule_id_check CHECK (rule_id IN ('reserve-trial-1', 'midday-productive-shift-1', 'fuel-residual-within-band-1'))`;
   - `verification_plan_family CHECK (` 0052's `_FAMILY` text verbatim (both arms) `OR (rule_id = 'fuel-residual-within-band-1' AND plan_version = 'fuel-residual-verification-1' AND action_id IS NULL AND applied_event_id IS NULL AND change_id IS NULL AND old_foundation_revision_id IS NULL AND new_foundation_revision_id IS NULL AND battery_asset_id IS NULL AND field IS NULL AND baseline_candidate_seconds IS NULL AND domain_action_id IS NOT NULL AND origin_finding_revision_id IS NOT NULL AND applied_work_event_id IS NOT NULL AND origin_opportunity_revision_id IS NULL AND supersedes_plan_id IS NULL AND triggering_fixture = 'fuel-seal-dip-sensor-power@1' AND baseline_start < baseline_end AND later_end - later_start = interval '14 days' AND baseline_end <= later_start))`.
   - Build the fuel arm with 0052's `_all` helper and copy 0052's `_FAMILY` as `FAMILY_0052` (used by the downgrade). The reserve arm keeps every reserve column NOT NULL, so a fuel row (reserve columns NULL except `origin_finding_revision_id`) can only match the fuel arm.
   - `origin_finding_revision_id` keeps its 0019 FK to `finding_revision`, which is how the plan cites the fuel Finding revision. 0019's `verification_plan_window_order` (`baseline_end <= effective_from AND later_start >= effective_from`) applies unchanged.
   - Nothing changes on `verification_evaluation_request`, `verification_outcome`, `verification_metric` or the 0044 producer (0052 made them domain-capable).
3. **Downgrade.** `LOCK TABLE verification_metric, verification_outcome, verification_evaluation_request, verification_plan, domain_action_case_link, domain_action_intent, domain_action IN ACCESS EXCLUSIVE MODE`. Refuse with `RuntimeError("0057 downgrade requires no fuel-balance Actions or fuel verification plans")` if any `domain_action.domain = 'FUEL_BALANCE'` or `verification_plan.rule_id = 'fuel-residual-within-band-1'` row exists. Otherwise restore 0052's three CHECKs and 0051's domain CHECK (constants `..._0052`, `DOMAIN_CHK_0051`).
4. No other object changes.

### 9m.3 K6a card: the fuel Finding as a domain-Action origin (0057), 0.6 (range 0.5–0.75)

**What K6a delivers.** Migration 0057 (§9m.2); the `FUEL_BALANCE` domain-Action contract; the fuel selection check; the Cold/EV index filter; the request-lineage map entry. **No verification code, no Ref kind, no page, no board edit** (K6b).

**Exact specification.**
1. `B/work/domain_action.py`, beside `MINI_SPEC`:
   ```python
   #: DIESEL-1-R3m: an Action raised from an unexplained-fuel Finding (lever `fuel-seal-dip-sensor-power@1`: seal the
   #: tank cap, sign the dip log at every shift change, put the tank sensor on its own protected supply). Finding
   #: origin (the 0051 CHECK forces it); no declared intent (`DOMAINS` stays the intent-capable Cold/EV set);
   #: APPLIED is its linked case's COMPLETE.
   FUEL_DOMAIN = "FUEL_BALANCE"
   FUEL_FINDING_DOMAIN = "fuel_balance"
   FUEL_MESSAGES = {
       "DOMAIN_INTENT_INVALID": "The fuel Action declaration is incomplete or invalid.",
       "DOMAIN_INTENT_LINK_INVALID": "The declared unexplained-fuel Finding is not its current supported version at this site and time.",
       "DOMAIN_INTENT_CONFLICT": "This Action declaration has a newer version; reload it.",
       "DOMAIN_INTENT_BASIS_CHANGED": "The selected fuel work basis changed; reload the Action.",
       "ACTION_NOT_FOUND": "Action was not found at this site.",
   }
   FUEL_SPEC = DomainSpec(FUEL_DOMAIN, FUEL_FINDING_DOMAIN, (), "Seal the tank cap, sign the dip log, protect the tank sensor's power",
                          (), FUEL_MESSAGES, (), origin=ORIGIN_FINDING, site_type="MINIGRID")
   ACTION_DOMAINS: Mapping[str, DomainSpec] = {**DOMAINS, MINI_DOMAIN: MINI_SPEC, FUEL_DOMAIN: FUEL_SPEC}
   ```
   - `DOMAINS`, `BY_FINDING_DOMAIN`, `_COMMON_BASIS` and `_ANY_BASIS` are unchanged (pinned by test A2). `_action_body` needs no edit: `origin=ORIGIN_FINDING` selects the Finding pair.
2. `B/work/domain_intent.py` `create_action`, the Finding branch (`:101-110`) becomes:
   ```python
   revision = tx.finding_revision(normalized["origin_finding_id"], normalized["origin_finding_revision_id"])
   if revision is None or revision["domain"] != spec.finding_domain:
       raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
   if spec.domain == d.FUEL_DOMAIN:
       # DIESEL-1-R3m: a fuel Finding has no analytic selection to pin; its selected revision is its latest as known,
       # when SUPPORTED (K4a lifecycle).
       if not tx.fuel_finding_selected(revision["finding_id"], revision["id"]):
           raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
   else:
       pin = tx.selected_pin(revision)
       if pin is None or (spec.domain == d.EV_DOMAIN and selected_ev_finding(tx, pin, revision["id"]) is None):
           raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
   origin = {k: normalized[k] for k in ("origin_finding_id", "origin_finding_revision_id")}
   ```
   - The site-type gate (`:94`) already refuses a non-MINIGRID Site, because `FUEL_SPEC.site_type == "MINIGRID"`.
   - `post_intent` already refuses (`:152-153`, no criteria). `post_case_link` already works (domain-independent; `_spec` finds `FUEL_SPEC`).
   - `_check_basis` is never reached for the fuel domain (there is no intent).
3. `B/work/adapters/postgres_domain_intent.py` `_DomainTx` gains:
   ```python
   def fuel_finding_selected(self, finding_id: str, revision_id: str) -> bool:
       """DIESEL-1-R3m: this revision is its Finding's latest by `command_now`, of the fuel domain and analytic, and
       SUPPORTED."""
       return self._c.execute(text(
           "SELECT EXISTS (SELECT 1 FROM finding_revision fr WHERE fr.tenant_id = :t AND fr.site_id = :s "
           "AND fr.finding_id = :f AND fr.id = :r AND fr.domain = 'fuel_balance' AND fr.analytic_id = 'fuel-balance-1' "
           "AND fr.lifecycle = 'SUPPORTED' AND fr.created_at <= :now AND fr.revision_no = (SELECT max(x.revision_no) "
           "FROM finding_revision x WHERE x.tenant_id = :t AND x.site_id = :s AND x.finding_id = :f "
           "AND x.created_at <= :now))"), self._p(f=finding_id, r=revision_id)).scalar_one()
   ```
   `insert_action`'s Finding-pair INSERT (`:139-144`) already writes it. No other store change.
4. `B/work/adapters/postgres_domain_action_index.py:69-79`: in both `action` and `actions_in_window`, `AND origin_opportunity_id IS NULL` becomes `AND domain IN ('COLDCHAIN', 'EV_CHARGING')`. The comment at `:66-67` gains: "DIESEL-1-R3m: positive Cold/EV filter (the same set under 0051's MINI tie); a fuel Action is read through the chain and its verdict page."
5. `B/work/adapters/postgres_work_read.py:93`: `_FINDING_DOMAIN_OF = {**{name: spec.finding_domain for name, spec in DOMAINS.items()}, FUEL_DOMAIN: FUEL_FINDING_DOMAIN}` (import the two names).

**Client wording (K6a):** only the five `FUEL_MESSAGES` (API refusal texts) and `FUEL_SPEC.summary`. They are added to `test_out_b2_vocabulary.py`'s scan list.

**Tests (localised; no full suite).** Each "must fail" names the mutation the reviewer applies to a scratch copy.
- **L0 `backend/tests/test_k6a_fuel_action_origin.py` (no DB, fake tx):**
  1. `action_body` for `FUEL_BALANCE` with the Finding pair normalizes; with the opportunity pair (or both pairs) → 422 with `FUEL_MESSAGES["DOMAIN_INTENT_INVALID"]`. Must fail if `FUEL_SPEC.origin` is `ORIGIN_OPPORTUNITY`.
  2. `set(ACTION_DOMAINS) == {COLDCHAIN, EV_CHARGING, MINI, FUEL_BALANCE}`; `DOMAINS` and `BY_FINDING_DOMAIN` equal their pinned values. Must fail if `FUEL_SPEC` is added to `DOMAINS` (that would make an intent possible).
  3. `create_action` with a fake tx: a `mini_grid` revision → LINK_INVALID; `fuel_finding_selected` False → LINK_INVALID; site type `COLDCHAIN` → LINK_INVALID; selected → 201 with `domain = FUEL_BALANCE` and the Finding pair. The fake's `selected_pin` raises if called. Must fail if the fuel branch falls through to `selected_pin`.
  4. `post_intent` on a stored `FUEL_BALANCE` Action → 422 with the fuel literal.
  5. The five messages and the summary pass guard V's terms and the H4 words.
- **L2 `backend/tests/test_k6a_fuel_action_origin_postgres.py`, own `assetops_k6_test`.** A fuel Finding is raised the K4a way (synthetic windows through `PostgresFuelBalanceStore.append` with the test clock, then `build_fuel_finding_service(…).raise_night`, as §9j.8 B3):
  1. **0057** up/down/up on empty tables. The domain CHECK and the three family CHECKs as pg prints them. Downgrade refused with a `FUEL_BALANCE` Action and with a fuel plan row. Raw inserts: `MINI` + Finding pair, and `FUEL_BALANCE` + opportunity pair, both refused (`domain_action_mini_origin`). A fuel plan row with a reserve column set, or a different `triggering_fixture`, or `later_end − later_start ≠ 14 days`, refused (`verification_plan_family`). Single alembic head, head-agnostic.
  2. **Create:** 201 with an `ACT-` code; an identical retry → 200; another body under the same key → 409.
     - The Finding's later NO_LONGER_SUPPORTED revision → LINK_INVALID. Must fail if `fr.lifecycle = 'SUPPORTED'` is dropped.
     - An older SUPPORTED revision while a newer one exists → LINK_INVALID. Must fail if the `max(revision_no)` predicate is dropped.
     - A revision created after `command_now` → LINK_INVALID.
  3. **Case:** create a `MAINTENANCE_REQUEST`, post a record, `ASSIGN`, `COMPLETE`, then `post_case_link` on the head → 201.
  4. **Index:** `PostgresDomainActionRead` `action(id)` is None and `actions_in_window` omits the fuel Action, while the K6a test's Cold Action (built as `test_w502_*` does) is still listed. Must fail if the predicate reverts to `origin_opportunity_id IS NULL`.
  5. **Request lineage:** the request detail's domain-link row for the fuel Action has `lineage` true and `pin` None.
  6. **Thread link:** after `run_threads` (`chain/backfill.py:33`), one `chain_action_thread` row joins the Action to the fuel Finding's thread.
- **Must stay green unchanged:** `test_w502_*`, `test_w504_*` (except the one pin line, item 5 above), `test_ch9b1_*`, `test_ch9b2_*`, `test_ch9b3_*`, the `test_s4_*` domain-action tests, K4a's tests. Any behaviour edit is stop S-a5.
- **Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1`, `tools\check-agent-workflow.ps1`, run directly, with no `-ExecutionPolicy`.

**Files (approved list; anything else is stop S-a4).** `backend/migrations/versions/0057_fuel_verification.py`; `B/work/domain_action.py`; `B/work/domain_intent.py`; `B/work/adapters/postgres_domain_intent.py`; `B/work/adapters/postgres_domain_action_index.py`; `B/work/adapters/postgres_work_read.py` (`:93` only); the two test files; `backend/tests/test_w504_ev_intent_postgres.py:154`; `backend/tests/test_out_b2_vocabulary.py`; the K3/K4a head tests only if they still name a fixed head (head bookkeeping, §9j.8 B6).

**PRE-FLIGHT (no code first; batch every question in one message).**
- (a) Every reader of `domain_action` or of `chain_action` rows that dispatches on the Action domain (`git grep -n "spec_of\|ACTION_DOMAINS\|\.domain\b" backend/assetops_backend/work backend/assetops_backend/chain`), with file:line, and what each does with `FUEL_BALANCE`. A reader that raises or mis-renders and is not fixed by this card is stop S-a3.
- (b) The frontend text the maintenance request page shows for a domain link with `lineage` true and `pin` None (the mill's case), with file:line.
- (c) Whether any golden or test asserts the exact `actions_in_window` SQL text.
- (d) That K4a's `raise_night` gives a `finding_revision.lifecycle = 'SUPPORTED'` row with `analytic_id = 'fuel-balance-1'` (READ on the K4a branch).

**Stops (report to the Architect; never design around them).**
- **S-a1** 0057 needs any object beyond §9m.2.
- **S-a2** `domain_action_mini_origin` or `domain_action_one_origin` would need relaxing.
- **S-a3** a PRE-FLIGHT (a) reader fails on `FUEL_BALANCE`.
- **S-a4** a file outside the list, or any Cold, EV or mill served byte changes.
- **S-a5** an existing test needs a behaviour change (head bookkeeping and the one pin line excepted).
- **S-a6** guard V or the H4 scan flags a K6a literal.
- **S-a7** more than 0.8 units.

**Dependencies, start, branch, DB, size.**
- **Before K4a merges:** pre-flight, the migration text (with `down_revision` 0056), the spec, the service branch, the store method and the L0 tests can all be written and run.
- **After K4a merges:** `git merge main`, then L2. **K6a merges before K6b starts its L2 and before K7-D's Action step.**
- Branch `task/DIESEL-K6a-fuel-action-origin`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k6a`, from main at or after this ruling's commit. Opus does the first build and the first review. `git add -f` of explicit paths; `git merge main`, never rebase.
- **DB: only `assetops_k6_test`** (and its harness clones). Never `assetops_demo3_full_test` or any other DB. No prepare, tick, `serve` or suite.
- **Size 0.6** (range 0.5–0.75): migration 0.2; spec, branch, store method, index, map 0.12; L0 0.08; L2 0.15; pre-flight and packet 0.05.
- **Reading budget:** §9m.1–§9m.3; `work/domain_action.py`; `work/domain_intent.py`; `work/adapters/postgres_domain_intent.py:30-145`; `work/adapters/postgres_domain_action_index.py:55-95`; `work/adapters/postgres_work_read.py:50-95`, `:240-298`; `0051_action_opportunity_origin.py:60-100`; `0052_verification_plan_domain.py`; `0019_verification_core.py:40-110`; K4a's `0056_unexplained_fuel_finding.py` and `backend/tests/test_k4a_fuel_finding_postgres.py` (the raise helpers).

### 9m.4 K6b card: `fuel-residual-within-band-1`, the verdict page and the board entry, 1.4 (range 1.25–1.6)

**What K6b delivers.**
- The pure family (`B/actions/fuel_verification.py`): night choice, verdict, outcome rows and client text.
- The plan freeze and the evaluation (service methods, a separate store context, ports, composition).
- The verdict read API and the page `F/sites/SiteFuelResidualVerification.tsx` at its own route, with the Ref kind `FUEL_VERDICT`.
- The chain Action Ref fix (§9m.1 item 6) and the Kisiwa board's Assure "Verified results" entry. **No value line, anywhere (H2).**
- Finish rows **KIS-5** (moved here from K9) and **KIS-10** (new).
- **Not in K6b:** a tick stage (the evaluation is explicit, as K3's assess and K4a's raise are; the after-the-demo list gains "fuel verdict tick stage"), the Portfolio Assure count (K8), the Protect thread line (K4b), and any edit to the mill's methods, columns, wire or page.

**The family (pure; no I/O; `B/actions/fuel_verification.py`).** It imports `reserve_trial`, `verification_rules as rules`, `actions.ports.ActionRefused`, `actions.lifecycle.SYSTEM_DEMO`, `fuel_balance.model` (types only) and `fuel_balance.finding_text` (`litres1`, `short_day`). It never imports `verification_families` (that avoids a cycle), `financials`, `fuel_cost*` or any price module.
```python
FUEL = "fuel-residual-within-band-1"
FUEL_PLAN_VERSION = "fuel-residual-verification-1"
FUEL_LEVER = "fuel-seal-dip-sensor-power@1"          # verification_plan.triggering_fixture (0057 pins it)
FREEZE_COMMAND = "FREEZE_FUEL_VERIFICATION_PLAN"
MIN_NIGHTS, LOOK_NIGHTS = 3, 14
METRIC_KEY = "fuel_residual_night"
EVALUATOR_JOB = "fuel-verification-evaluator"
#: §8.5, verbatim; frozen in the plan; never fitted.
TARGET = {"rule": "every later night: residual_low <= 0 <= residual_high and reporting_gap_minutes == 0",
          "over": "first 3 COMPLETE nights after the change",
          "basis": "owner-reviewed design, fuel-loss-feasibility Part A §3 Verify, chosen 2026-11-07"}
NIGHT_RULE = ("A night counts only when its stored fuel check is assessed (state is not NOT_ASSESSED) and every "
              "generator slot of the night is known (terms.unknown_slots == 0); nights are chosen by data quality "
              "only, never by value.")
BASIS_TEXT = ("SYSTEM_DEMONSTRATION: story-time freeze of a fuel Action's verification plan after its work case is "
              "COMPLETE and linked; no verified human principal exists, so no operator approval is recorded")
TARGET_MET, TARGET_MISS, LATER_SHORT = "TARGET_MET", rules.TARGET_MISS, "LATER_SHORT"
```
- **Later candidates** `later_nights(effective_from, tz) -> list[date]` (14 dates). `d0` = the Site-local date of `effective_from`. If the window start of `d0` (18:00 local on `d0`, as UTC) is earlier than `effective_from`, use `d0 + 1` instead. The candidates are `d0 … d0 + 13`. A window that starts exactly at `effective_from` counts (`>=`).
- **COMPLETE night** `complete(w) -> bool`: `w is not None and w.state != "NOT_ASSESSED" and int(w.terms["unknown_slots"]) == 0`. Gap minutes do **not** affect COMPLETE: a gap is part of the target and fails it.
- **Night passes** `passes(w) -> (bool, reason|None)`: `w.residual_low <= 0 <= w.residual_high` (exact `Fraction`; no tolerance) **and** `w.gap_minutes == 0`. The failure reason is `"BAND"` when the band test fails (checked first), else `"GAP"`.
- **Verdict** `assess(plan, windows_by_date, now) -> dict`. `windows_by_date` = the latest revision per candidate night as known at `now` (`FuelBalanceReadPort.windows(…, d0, d0 + 14, known_at=now)`):
  1. `chosen` = the first 3 candidates, in date order, that are COMPLETE (chosen by grade, never by value).
  2. `closed` = the window end of the 14th candidate (12:00 local on `d0 + 14`) is `<= now`.
  3. If 3 are chosen, or `closed`: if any chosen night fails → `INEFFECTIVE`, `[TARGET_MISS]`, with the sentence naming the **first** failing night; else if 3 are chosen → `VERIFIED`, `[TARGET_MET]`; else → `INCONCLUSIVE`, `[LATER_SHORT]`.
  4. Otherwise: not decided (`NOT_JUDGED`; nothing is stored).
- **Outcome rows** `outcome_rows(plan, result, now, source_class)`, the mill's shape (`verification_families.outcome_rows`):
  - Metrics, PK `(outcome_id, metric_key, window_name)`, all with `METRIC_KEY`:
    - BASELINE: `PASS`, `value` = the baseline range text, `reason` = "night {date}: UNEXPLAINED".
    - LATER: `PASS` if 3 were chosen, else `UNKNOWN`; `value` = `"{n} of 3"`; `reason` = the chosen night dates joined by ", ".
    - COMPARISON: `PASS`/`FAIL`/`UNKNOWN` by outcome; `reason` = `TARGET["rule"]`.
    - `unit` = "L".
  - `basis` = `{plan_id, plan_sha256, rule_id: FUEL, plan_version, target: TARGET, windows_known_at}`.
  - `details` = `{"baseline": {window pin}, "later": [{night_date, window_id, revision, input_sha256, state, residual_low, residual_high, gap_minutes, passes, fail_reason}], "first_fail": date|None, "sentence", "source": {"source_class"}, "look_ahead_closed"}`.
  - `idempotency_key` = `f"fuel-outcome-{plan_id}"`; `actor_id` "service:verification-evaluator"; `triggering_job` = `EVALUATOR_JOB`.
- **Client literals** (all server-composed; the browser formats no number; litres via K4a's `finding_text.litres1`, dates via `finding_text.short_day`):
```python
HEADLINE = {"VERIFIED": "Fuel stayed accounted for", "INEFFECTIVE": "Target not met",
            "INCONCLUSIVE": "Could not conclude", "NOT_JUDGED": "Not judged yet",
            "NO_PLAN": "No verification plan yet"}
VERIFIED_TEXT = ("On {n} fully checked nights after the change, the fuel in the tank matched the generator's "
                 "modelled use and the recorded deliveries within the stated margin, and the tank sensor sent "
                 "readings all night.")
FIXED_LINE = ("This check shows the fuel stayed accounted for after the change; it does not measure how much the "
              "change itself prevented.")                     # H1, §8.2 verbatim; shown in every state
MISS_BAND_TEXT = ("On the night of {date}, after the change, the fuel in the tank did not match the generator's "
                  "modelled use and the recorded deliveries within the stated margin.")
MISS_GAP_TEXT = "On the night of {date}, after the change, the tank sensor did not send readings all night."
LATER_TEXT = "Not judged yet: only {n} of 3 fully checked nights after the change"
LATER_SHORT_TEXT = ("Only {n} of 3 fully checked nights after the change in the 14 nights allowed, so no verdict "
                    "is given")
CRITERION_TEXT = ("3 fully checked nights after the change within the stated margin, with the tank sensor sending "
                  "readings all night")
RULE_TEXT = ("Rule fixed before the check: the first 3 fully checked nights after the change must each stay within "
             "the stated margin, with the tank sensor sending readings all night.")
ACTIVITY_NOTE = "Completed work is evidence of activity, not resolution."     # v69 :502, verbatim
NIGHT_TEXT = "{date} (6 pm to noon)"
RANGE_TEXT = "{lo} to {hi} L"
SENSOR_ALL = "Readings all night"
SENSOR_GAP = "No readings for {m} min"
RESULT_PASS, RESULT_BAND, RESULT_GAP = "Within the margin", "Outside the margin", "Sensor gap"
BASELINE_ROW = "The night of the finding"
BASELINE_RESULT = "Unexplained fuel found"
NOT_CHECKED = "Not checked yet"
CARDS = (("Nights checked after the change", "{n} of 3", "Chosen by data quality, never by result"),
         ("Fuel accounted for", "{k} of {n} nights", "Within the stated margin"),
         ("Tank sensor", "Readings all night on {g} of {n} nights", "A gap is more than 60 minutes without a reading"),
         ("Final outcome", "{headline}", "Decided by the rule fixed before the check"))
LITERALS = (...every string above...)        # scanned by the local guard test and test_out_b2_vocabulary.py
```
  - When `n == 0`, cards 2 and 3 show `NOT_CHECKED` as the value.
  - `{m}` is the stored `gap_minutes`.
  - `{date}` is `short_day(night_date)` ("4 Oct" form).

**Freeze** `VerificationService.freeze_fuel_plan(tenant_id, site_id, domain_action_id) -> (int, dict)`. A service method, with no HTTP route, as the mill's is. In order:
1. `ctx = store.fuel_plan_context(t, s, a)`, a new read in `postgres_action_store.py`. It returns the Action (`id, action_code, title, owner_label, domain, origin_finding_id, origin_finding_revision_id`, Site `timezone`), `applied` (the first COMPLETE `work_event` of a linked case: `id, case_id, occurred_at`, plus the case's `public_code`; the mill's statement) and the existing plan (`FUEL_PLAN_COLUMNS` = `DOMAIN_PLAN_COLUMNS + ", origin_finding_revision_id"`). None → 404 `ACTION_NOT_FOUND` "No such Action for this Site.".
2. If a plan exists → 200 `{"replayed": True, "plan": plan_wire(plan)}`.
3. `domain != "FUEL_BALANCE"` → 409 `VERIFICATION_FAMILY_UNSUPPORTED` "Only an Action raised from an unexplained-fuel Finding has a fuel verification plan."
4. `applied is None` → 409 `VERIFICATION_ACTION_NOT_APPLIED` "A verification plan needs the Action's linked work case to be COMPLETE."
5. Either fuel port is None → 503 `VERIFICATION_FUEL_READ_UNAVAILABLE` "The fuel checks cannot be read."
6. `ff = ports.fuel_findings.fuel_finding(t, s, origin_finding_id, known_at=now)`. If it is None, or the window its origin revision cites cannot be read (the plan cites **the Action's** `origin_finding_revision_id`: read that revision's claim `fuel_balance_window_id`, then `ports.fuel_windows.window(t, s, id)`) → 409 `VERIFICATION_ORIGIN_UNAVAILABLE` "The Action's unexplained-fuel Finding or its night check cannot be read."
7. `effective_from = applied["occurred_at"]` (UTC). **This is the effective-time field: `verification_plan.effective_from`, the linked case's first COMPLETE `occurred_at`** (the mill's anchor, `applied_work_event_id`).
   - `effective_from < baseline.window_end` → 409 `VERIFICATION_EFFECTIVE_BEFORE_BASELINE` "The change is recorded before the end of the night it answers."
8. Compute `later = later_nights(effective_from, tz)`. If `later_start` (the window start of `later[0]`) is `<= now` → 409 `VERIFICATION_LATER_WINDOW_STARTED` "The first night after the change has already begun; the plan must be frozen before it." (pre-registration).
9. Plan row:
   - `rule_id` FUEL; `plan_version`; `domain_action_id`; `origin_finding_revision_id`; `applied_work_event_id`; `effective_from`;
   - `baseline_start`/`baseline_end` = the baseline window's; `later_start` = `later[0]`'s window start; `later_end` = `later_start + 14 days`;
   - `baseline_selection` = `{"state": "COMPLETE", "night_date", "window_id", "window_revision", "input_sha256", "state_found": "UNEXPLAINED", "residual_low", "residual_high", "gap_minutes"}` (exact text); `baseline_evidence_ids []`;
   - `basis` = `{"timezone", "night_rule": NIGHT_RULE, "applied": {work_event_id, case_id, occurred_at}, "origin": {finding_id, revision_id}, "tank_asset_id", "windows_known_at": now}`;
   - `target` = `TARGET`; `guardrails {}`; `bands {}`;
   - `coverage {"min_nights": 3, "look_ahead_nights": 14}`;
   - `later_selection_rule {"rule": "the first 3 COMPLETE nights whose window starts at or after effective_from, at most 14 nights ahead, chosen by grade only at evaluation", "min_nights": 3, "candidates": {"from", "to"}}`;
   - `plan_sha256` = `reserve_trial.sha(content)`; the `SYSTEM_DEMO` actor columns; `authorization_basis` = `BASIS_TEXT`; `triggering_fixture` = `FUEL_LEVER`;
   - `idempotency_key` = `f"fuel-plan-{domain_action_id}"`; `payload` = `{"command": FREEZE_COMMAND, "domain_action_id"}`; `recorded_at` = now.
10. `store.freeze_fuel_plan(t, s, plan)` (the mill's `freeze_domain_plan` body with `FUEL_PLAN_COLUMNS`, the same advisory lock key form `verification-plan:{id}`) → 201, or 200 replayed.

**Evaluate** `VerificationService.evaluate_fuel_plan(tenant_id, site_id, domain_action_id) -> dict`. Mirrors `MiddayShift.evaluate`:
- 404 if there is no context.
- `{"state": "NO_PLAN", "stored": False}` if the plan is missing or not FUEL.
- If an outcome exists → `{"state", "stored": False, "replayed": True, "outcome_id"}`.
- 503 if a port is missing.
- `assess`. If not decided → `{"state": "NOT_JUDGED", "stored": False, "not_judged_text": LATER_TEXT…}`.
- Otherwise `source_class = store.example_source_class(t, s, used_dates, tz, now)`, where `used_dates` = for the baseline night and each chosen night, its `night_date` and `night_date + 1`, sorted and distinct (WD-1m-R2). Then `outcome_rows`, then `store.record_domain_outcome` (shared, unchanged) → `{"state", "stored", "replayed", "outcome_id"}`.

**Summary** `VerificationService.fuel_summary(tenant_id, site_id, domain_action_id) -> dict`. Read-only, the page's only read. A stored outcome is read back, never recomputed; with no outcome, the live `assess` gives the not-judged text. 404 if there is no context; 409 `VERIFICATION_FAMILY_UNSUPPORTED` for a non-fuel Action. Wire, `fuel_summary_wire(ctx, plan, outcomes, live, origin, baseline, site_code)`:
```
{"action_id", "action_code", "title", "owner_label", "rule_id": FUEL,
 "state": VERIFIED|INEFFECTIVE|INCONCLUSIVE|NOT_JUDGED|NO_PLAN, "headline": HEADLINE[state],
 "sentence": VERIFIED_TEXT|MISS_*_TEXT|LATER_SHORT_TEXT|None, "not_judged_text": LATER_TEXT|None,
 "fixed_line": FIXED_LINE, "criterion_text": CRITERION_TEXT, "rule_text": RULE_TEXT,
 "cards": [{"label", "value", "note"}] (4),
 "origin": {"finding_id", "revision_id", "title": finding_text.TITLE, "night_text", "ref": fuel_finding_ref(...), "href"},
 "nights": [{"role": "BASELINE"|"LATER", "label": BASELINE_ROW|NIGHT_TEXT, "range_text", "sensor_text",
             "result_text", "passes": bool|None, "window_id", "revision"}],   # baseline first, then chosen later nights
 "activity": {"case_code", "case_ref": case_ref(...), "case_href", "completed_text": "{d} {Mon} {HH:MM}" Site-local,
              "site_visit_text": the SITE_VISIT body citing the case, or None, "note": ACTIVITY_NOTE} | None,
 "effective_from": ISO, "plan": {"plan_id", "later_candidates": {"from","to"}} | None,
 "outcome": {"outcome_id", "outcome", "reasons", "recorded_at", "source_class"} | None,
 "value": None, "cost_check": None}
```
- `value` and `cost_check` are **always** null (H2).
- No key anywhere in the wire contains `amount`, `price`, `currency` or `money`.
- The SITE_VISIT text is read through the existing Work read port (PRE-FLIGHT (d) names it). It is the first `SITE_VISIT` operational record whose `case_id` is the linked case, as known. If it is absent, the field is None and the row is omitted.

**Ports and composition.**
- `VerificationPorts` (`actions/verification.py:54-72`) gains `fuel_windows: Any = None` (a `FuelBalanceReadPort`) and `fuel_findings: Any = None` (K4a's `FuelFindingReadPort`). Both are implemented by `PostgresFuelBalanceStore`.
- `B/actions/composition.py` gains `build_fuel_verification_service(database_url, *, test_clock=None) -> VerificationService`. It wires the existing verification store builder (PRE-FLIGHT (a) names it), `VerificationPorts(fuel_windows=s, fuel_findings=s)` with `s = build_fuel_balance_store(database_url)`, and `clock = test_clock or <the production clock the API uses>`. The test-only clock is constructor-only (§9d.4 precedent); production never passes it.
- `verification_families.py` gains only, at the bottom: `from assetops_backend.actions.fuel_verification import FUEL, FuelResidual` and `FAMILIES[FUEL] = FuelResidual()`, where `FuelResidual` is a frozen dataclass (`rule_id`, `plan_version`, `owner="domain_action"`). `family_of` then knows the family.

**API** (`B/action_api.py`, beside the mill's `:315`): `GET /api/sites/{site_code}/domain-work/actions/{action_id}/fuel-verification` → `{"access_basis", **verification.fuel_summary(...)}`, through the same `run(...)` error mapping. The router's verification service is built with `build_fuel_verification_service` (or the existing one gains the two ports; PRE-FLIGHT (b)).

**Ref kind and route.**
- `B/chain/refs.py`: `KINDS` gains `"FUEL_VERDICT"`. `href_for` gains `if kind == "FUEL_VERDICT": return f"{_site(ref)}/domain-actions/{_seg(ref['id'])}/fuel-verification"`. New constructor `fuel_verdict_ref(site, action_id) -> _ref("FUEL_VERDICT", site=site, id=str(action_id))`. It joins every validator the kinds list feeds (PRE-FLIGHT (c)).
- `F/sites/chainRef.ts` gains `| { kind: "FUEL_VERDICT"; site: string; id: string }`. `F/shell/operatorSiteRoutes.ts` gains ``SITE_FUEL_VERIFICATION_ROUTE_PATH = `${SITE_DETAIL_ROUTE_PATH}/domain-actions/:actionId/fuel-verification` ``, `siteFuelVerificationHref(siteId, actionId)`, and `case "FUEL_VERDICT": return siteFuelVerificationHref(r.site, r.id);`. `F/App.tsx` registers the route beside `SITE_MILL_VERIFICATION_ROUTE_PATH` (`:501`), with a `SiteFuelVerificationFrame` in `F/shell/SiteAnalyticsFrames.tsx` (the mill frame's pattern, `:2600-2620`).
- **`fuel_finding_ref` (the origin link, §9l.4).** If K5 phase B has merged, import it. If not, K6b adds `FUEL_FINDING`, `fuel_finding_ref`, `siteFuelFindingHref` and `SITE_FUEL_FINDING_ROUTE_PATH` **exactly as §9l.2 specifies** (`refs.py` per `:3139`; frontend per `:3168-3177`), and whichever of K5 and K6b merges second takes main's copy. Until K5's page merges, the origin link has no page (Kisiwa is opt-in until K7-F, so no default prepare shows it).

**Chain Ref fix.**
- `postgres_chain_read.py` `_SITE_ACTIONS` gains `CASE WHEN a.kind = 'DOMAIN_INTENT' THEN (SELECT d.domain FROM domain_action d WHERE d.tenant_id = a.tenant_id AND d.id = a.id) END AS action_domain`. Nothing else in the statement changes.
- `site_chain.action_wire_ref` gains, after the mill branch: `if a["kind"] == "DOMAIN_INTENT" and a.get("action_domain") == "FUEL_BALANCE": return refs.fuel_verdict_ref(site, a["action_id"])`. Docstring: "DIESEL-1-R3m: a fuel Action has no Action page; its Ref is the fuel verdict page."

**The board entry (Kisiwa Assure "Verified results").**
- `site_chain.fuel_verdict_actions(rows, *, site, cutoff, lo, hi)` is `opportunity_actions` with three differences:
  - the filter is `kind == "DOMAIN_INTENT" and action_domain == "FUEL_BALANCE"`;
  - the thread occurrence tested against `[lo, hi)` is one with a `finding_id`;
  - it returns `{action_id, code, thread_id, outcome (known by cutoff, else None), outcome_recorded_at, source_class, ref}`.
- `B/site_outcomes/board.py` gains `@dataclass(frozen=True) class FuelVerdictFact: action_id, code, thread_id, outcome, verdict_ref, source_class=None`, and the facts dataclass that holds `opportunity_actions` gains `fuel_verdicts: tuple[FuelVerdictFact, ...] = ()`.
- `B/site_outcomes/mini.py`:
  - builds `fuel = tuple(FuelVerdictFact(...) for a in site_chain.fuel_verdict_actions(ct.rows, site=c, cutoff=ct.k, lo=work_lo, hi=end))` beside `opp` (`:440-445`; an empty tuple when `ct is None`);
  - passes `fuel=fuel` to `_assure`, which merges it into the same code-ordered list and renders it as the `OpportunityActionFact` branch does: `VERIFICATION_TEXT[s].format(code=…, suffix=provenance_suffix(source_class))`, `PENDING_CHIP` when not judged, link `verdict_ref`;
  - **`_verified_values` is not given `fuel` and its signature does not change** (H2, structural).
  - The comment at the merge reads: `# MOCK DEVIATION MD-FUEL-K6-5 (DIESEL-1-R3m): as MD-FUEL-MB1-1, a fuel Action has no Action page; its Verified results entry opens its verdict page (FUEL_VERDICT). It carries no value line (H2).`
- On Kobo, Cold and EV no `FUEL_BALANCE` Action exists, so their boards and goldens are byte-equal (test B6).
- **Lane note:** K4b also edits `mini.py` and `board.py` (Protect). The edits are disjoint; whichever merges second merges main.

**The verdict page `F/sites/SiteFuelResidualVerification.tsx` (new) and `F/sites/fuelVerificationClient.ts` (new; the mill client's shape, `GET …/fuel-verification`, 404 → `not_found`).**
- Layout follows v69 `verification` (`frontend/mockups/v69/index.html:498-503`), top to bottom, with the existing `ui` components (`Panel`, `DataTable`, `Badge`) and the W1 verification card classes (`verificationCards.tsx` / `w1f4-verification.css`). No new CSS unless a class is missing; then add it in the page's own CSS file.
  1. **Status line:** `Badge` "{action_code} · {headline}", and the subtitle "{action_code} · source: {origin.title}, {origin.night_text} · owner: {owner_label}" (v69 `:503` `subtitle` form).
  2. **Header** (v69 `mheader`): Owner = `owner_label`; State = `headline`; Source = `origin.title` linked by `routeFor(origin.ref)`; Success criterion = `criterion_text`.
  3. **Four cards** from `cards` (v69's four `metric` cards).
  4. **Panel "Target evaluated night by night"** (v69 "Target and guardrails evaluated together"): a `DataTable` with columns "Night", "Role", "Unexplained fuel range", "Tank sensor", "Result". Rows come from `nights`. Role is "Before the change" for the baseline row and "Target" for the others. The panel note is `rule_text`.
  5. **Pair:** "Activity evidence" (v69 `:502`): Maintenance request = `case_code` linked by `routeFor(case_ref)`; Completed = `completed_text`; Site visit = `site_visit_text`; then the note `ACTIVITY_NOTE`. "Outcome evidence": `sentence` or `not_judged_text`, then **`fixed_line` in every state**.
  6. The `mock-deviation-line` paragraph listing MD-FUEL-K6-1 to -4.
- **States:**
  - loading: "Loading the fuel check." (`FUEL_LOADING`);
  - not found: "No such Action for this site." (the mill's `MILL_NOT_FOUND` literal, imported);
  - error: the server's message.
- **Header comment, MOCK DEVIATIONs** (each also in the packet's "Mock to new"):
  - `MD-FUEL-K6-1`: v69 `:501` evaluates one target **with guardrails**. The fuel check has one target and no guardrails (`guardrails = {}`, the BL-09/SCOPE-1 mill precedent), and its table lists nights, not metrics.
  - `MD-FUEL-K6-2`: v69's four cards (`:500`: target change, reserve breaches, critical service, final outcome) become nights checked, fuel accounted for, tank sensor and final outcome. **There is no money card and no "Realized savings"** (H2).
  - `MD-FUEL-K6-3`: v69's "Provisional target pass" badge is not shown. A night is either checked or "Not checked yet", and an undecided check reads `LATER_TEXT`.
  - `MD-FUEL-K6-4`: v69's "Outcome evidence" prose and its "Review a complete evidence example" button are replaced by the server's sentence and the fixed H1 line.
  - `MD-FUEL-K6-5` is on the board (above).
- **Layout evidence:** captures at 1440 and 390 of the VERIFIED state (the K6b L2 data, read-only `serve` on `assetops_k6_test`), plus NOT_JUDGED from a fixture. Height cap: the page fits 1440×1800 with three later nights. The K8 all-26 recapture adds this page.

**Finish rows** (pure logic in `T/demo_combined_rows.py`, wired in `T/demo_combined_finish.py` after KIS-4; each has an L0 self-test with pass and fail bodies; they run at E3):
- **KIS-5 (moved from K9 to K6b):** for the Kisiwa `FUEL_BALANCE` Action:
  - each pinned window in the outcome's `details` (baseline and later) is read back by `window(id)` and equals its pin (revision, `input_sha256`);
  - the later pins are exactly the first 3 COMPLETE candidates as known at the outcome's `recorded_at` (re-run `later_nights` + `complete`);
  - `fuel_verification.assess` over those windows gives the stored outcome and reasons. **The verdict is recorded as computed**; INEFFECTIVE or INCONCLUSIVE pass the row if they reproduce;
  - the served summary has `value is None`, `cost_check is None`, no money key, and `fixed_line == FIXED_LINE`.
- **KIS-10 (new): fuel verification coherence.**
  - `plan.recorded_at < later_start` (frozen before the first later night);
  - `effective_from` equals the linked case's first COMPLETE `occurred_at`;
  - `plan.origin_finding_revision_id` equals the Action's;
  - the baseline window id equals the origin revision's claim `fuel_balance_window_id`;
  - the Action's chain thread equals the Finding's `UNEXPLAINED_FUEL` thread;
  - the Kisiwa board on the outcome's Site-local day + 1 lists a Verified results entry whose text starts with the Action's display code and whose Ref is `FUEL_VERDICT`;
  - no Kisiwa board `verified_values` entry or Portfolio value line names this Action.

**Tests (localised; no full suite).** Each "must fail" names the mutation the reviewer applies to a scratch copy.
- **L0 `backend/tests/test_k6b_fuel_verification_rules.py` (no DB):**
  1. **`later_nights`:** effective 12:05 UTC (15:05 in Dar es Salaam) gives the same local date first; 18:30 local gives the next date; exactly 18:00 local gives the same date. Must fail if `>=` becomes `>`.
  2. **Choice:** NOT_ASSESSED and `unknown_slots > 0` nights are skipped; a COMPLETE failing night before two passing ones is chosen, which gives INEFFECTIVE. Must fail if the choice filters on `passes`.
  3. **Verdict table:**
     - 3 passes → VERIFIED with `VERIFIED_TEXT` ("On 3 fully checked nights …").
     - A band failure → INEFFECTIVE, `MISS_BAND_TEXT` naming the first failing night; a gap failure → `MISS_GAP_TEXT`; band and gap together → band.
     - `residual_low == 0` passes; `residual_high == 0` passes; `residual_low == Fraction(1, 10**6)` fails (must fail if any tolerance is added); EXCESS (`residual_high < 0`) fails.
     - 2 nights and open → NOT_JUDGED; 2 nights and closed → INCONCLUSIVE `LATER_SHORT_TEXT`; closed with a failing night → INEFFECTIVE.
  4. **Literals:**
     - `FIXED_LINE` equals §8.2 H1's text byte for byte;
     - every literal passes guard V's terms, the upper-case code pattern and the H4 words;
     - no literal contains a currency code, `$` or "price".
  5. **H2 static:** an AST check of `fuel_verification.py` shows no import of `financials`, `fuel_cost`, `fuel_cost_v2` or any `price` module. A fully populated `fuel_summary_wire` has `value is None`, `cost_check is None` and no key matching `amount|price|currency|money` at any depth. Must fail if a value line is added.
  6. **Outcome rows:** the three metric windows, reasons, pins, the idempotency key, and `source.source_class` in `details` (never in `basis`).
  7. **Board:**
     - `_assure` with a VERIFIED `FuelVerdictFact` gives "{code} verified on example data" (`source_class` example) with the `FUEL_VERDICT` Ref;
     - with no outcome it gives "{code} not yet verified" and `PENDING_CHIP`;
     - `inspect.signature(mini._verified_values)` is unchanged.
     - Must fail if `fuel` is passed into `_verified_values`.
  8. **Refs:** `href_for(fuel_verdict_ref("KISIWA-001", id))` = `/sites/KISIWA-001/domain-actions/{id}/fuel-verification`; `action_wire_ref` gives `FUEL_VERDICT` for a `FUEL_BALANCE` row, `DOMAIN_VERDICT` for the mill and `ACTION` for a Cold row.
  9. **KIS-5 and KIS-10 self-tests:** one pass body, and one fail body per item.
- **L2 `backend/tests/test_k6b_fuel_verification_postgres.py`, own `assetops_k6_test`.** The test builds:
  - synthetic K3 windows (test clock) for night N (UNEXPLAINED) and nights N+2, N+3, N+4 (WITHIN_MARGIN, gap 0);
  - the Finding through K4a's `raise_night`;
  - the Action through K6a's `create_action`;
  - the case with its record, COMPLETE and link.

  Then:
  1. **Freeze:** at an instant before N+2's window start → 201. The row's columns match the spec, `effective_from` equals the COMPLETE `occurred_at`, and a retry → 200 replayed. A second Action frozen after N+2's start → 409 `VERIFICATION_LATER_WINDOW_STARTED`. A mill Action → 409 `VERIFICATION_FAMILY_UNSUPPORTED`. Before COMPLETE → 409 `VERIFICATION_ACTION_NOT_APPLIED`.
  2. **Evaluate:** before night N+4 is known → NOT_JUDGED, with no outcome row. After → VERIFIED stored with three metrics; a retry → replayed. A WITHIN_MARGIN → UNEXPLAINED revision of N+3 appended after the outcome does not change the read-back. A separate DB state with N+3 set to a gap of 90 min → INEFFECTIVE, `MISS_GAP_TEXT`.
  3. **API** (TestClient): GET `…/fuel-verification` → 200 with the wire. An unknown id → 404. A mill Action → 409. The mill route on the fuel Action → 409 (its existing literal).
  4. **Chain:** after `run_threads`, `_SITE_ACTIONS` gives `action_domain = 'FUEL_BALANCE'`, and the thread detail's Action entry carries the `FUEL_VERDICT` Ref.
  5. **The mill path stays byte-equal:** `freeze_domain_plan`/`evaluate_domain_plan`/`domain_summary` outputs for the CH-9b fixture equal their pins taken **as the branch's first commit**.
  6. **Board goldens:** Kobo, Cold and EV board goldens are byte-equal. Must fail if `_SITE_ACTIONS` drops a row or reorders.
- **Frontend `F/sites/__tests__/fuelVerification.test.tsx`:**
  - each state renders from a fixture wire;
  - `fixed_line` is present in all five states;
  - no "$", currency code or "price" text appears;
  - the origin link resolves `routeFor({kind: "FUEL_FINDING", …})` and the case link `routeFor({kind: "CASE", …})`;
  - `routeFor({kind: "FUEL_VERDICT", …})` and the `linkRefs` round-trip work;
  - the MOCK DEVIATION line is present;
  - the page text passes the existing product-vocabulary scan helper.
- **Must stay green unchanged:** `test_ch9b2_*`, `test_ch9b3_*`, `test_mv1_*`, `test_mb1*`, `test_pv1*`, `test_wd1m*`, `millVerification.test.tsx`, K4a's and K6a's tests, and both probe `--check`s. Any behaviour edit is stop S-b5.
- **Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1`, `tools\check-agent-workflow.ps1` and `tools\check-navigation-truthfulness.ps1` (new route), run directly, with no `-ExecutionPolicy`.

**Files (approved list; anything else is stop S-b4).**
1. `B/actions/fuel_verification.py` (new); `B/actions/verification_families.py` (the bottom registration only); `B/actions/verification.py` (the ports and the three fuel methods only); `B/actions/adapters/postgres_action_store.py` (`FUEL_PLAN_COLUMNS`, `fuel_plan_context`, `freeze_fuel_plan`); `B/actions/composition.py`; `B/action_api.py` (one route).
2. `B/chain/refs.py`; `B/chain/adapters/postgres_chain_read.py` (`_SITE_ACTIONS`); `B/chain/site_chain.py`; `B/site_outcomes/board.py`; `B/site_outcomes/mini.py`.
3. `F/sites/SiteFuelResidualVerification.tsx`, `F/sites/fuelVerificationClient.ts` (new); `F/sites/chainRef.ts`; `F/shell/operatorSiteRoutes.ts`; `F/shell/SiteAnalyticsFrames.tsx` (the frame only); `F/App.tsx` (one route); the K5 `FUEL_FINDING` items only if K5 has not merged.
4. `T/demo_combined_rows.py`, `T/demo_combined_finish.py` (KIS-5, KIS-10).
5. Tests: the L0, L2 and frontend files above, their pins module, and `backend/tests/test_out_b2_vocabulary.py`.

**PRE-FLIGHT (no code first; batch every question in one message).**
- (a) The builder of the verification store and the production clock the action API uses (file:line).
- (b) How `action_api.py` obtains its `VerificationService`, and whether adding the two ports there changes any existing route's wire.
- (c) Every validator fed by `refs.KINDS` (backend and frontend), and any JSON schema of Refs.
- (d) The Work read that gives a case's `SITE_VISIT` operational records with `case_id` (K2's store), and whether `actions` may import it (architecture guard).
- (e) Whether the architecture guard allows `actions` → `fuel_balance` imports (`model`, `finding_text`, `composition`). If not, that is stop S-b3.
- (f) The chain lifecycle's handling of a `verification.outcome` event on an `UNEXPLAINED_FUEL` thread (`chain/lifecycle_run.py`, `config/chain/thread-lifecycle-v1.json`): does it raise for a mechanism with no `clean_day_measures`? If it raises, that is stop S-b6.
- (g) Whether any board or chain golden compares `_SITE_ACTIONS` row dicts exactly (the new key).

**Stops (report to the Architect; never design around them).**
- **S-b1** any mill method, column list, wire, page or golden would change.
- **S-b2** a money field, value line or price read is needed anywhere on the fuel path (H2).
- **S-b3** PRE-FLIGHT (e) forbids the import.
- **S-b4** a file outside the list, or a Kobo, Cold or EV served byte or golden changes.
- **S-b5** an existing test needs a behaviour change.
- **S-b6** PRE-FLIGHT (f) shows the lifecycle raises.
- **S-a6b** guard V, the H4 scan or the navigation-truthfulness guard flags a K6b literal or route.
- **S-b7** more than 1.6 units.

**Dependencies, start, branch, DB, size.**
- **Needs K4a and K6a merged** (0057 and the fuel Action). Not K4b, K5 or K7.
- **What can start earlier:** `fuel_verification.py` with its L0 tests, and the page with its fixture tests. They need only K3's types (on main) and K4a's `finding_text` (on main once K4a merges). A builder may begin them on the K6b branch from main as soon as K4a merges, while K6a is in review.
- Branch `task/DIESEL-K6b-fuel-verification`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k6b`, from main after K4a merges. `git merge main` after K6a merges, before L2. Opus does the first build and the first review. `git add -f` of explicit paths; never rebase.
- **DB: only `assetops_k6_test`** (and its harness clones). Never `assetops_demo3_full_test` or any other DB. No prepare, tick or suite. `serve` only read-only on `assetops_k6_test`, for the layout captures.
- **Size 1.4** (range 1.25–1.6):

  | Item | Units |
  |---|---|
  | Pure family and literals | 0.3 |
  | Service, store context and freeze, ports, composition, API | 0.25 |
  | Ref kind, chain Ref fix, board entry | 0.15 |
  | Page, client, route, frame | 0.3 |
  | KIS-5, KIS-10 | 0.1 |
  | Tests (L0, L2, frontend) and captures | 0.25 |
  | Pre-flight and packet | 0.05 |
- **Reading budget:**
  - this §9m.1 and §9m.4; §8.2 (H1–H5); §9d.5; §9j.4–§9j.7;
  - `actions/verification_families.py`; `actions/verification.py:40-80`, `:350-420`;
  - `actions/adapters/postgres_action_store.py:60-90`, `:740-850`;
  - `0052_verification_plan_domain.py`; `0019_verification_core.py:40-240`;
  - `chain/refs.py`; `chain/site_chain.py:120-185`; `chain/adapters/postgres_chain_read.py:80-101`;
  - `site_outcomes/board.py:180-210`; `site_outcomes/mini.py:430-460`, `:1030-1100`;
  - `F/sites/SiteMillVerification.tsx`, `F/sites/millVerificationClient.ts`; `F/shell/operatorSiteRoutes.ts:360-380`, `:580-600`;
  - `frontend/mockups/v69/index.html:498-503`;
  - K4a's `fuel_balance/finding_text.py` and `model.py`.

### 9m.5 Effects on K7 (K7-D step 5 and K7-F's freeze step)

- **K7-D, §9l.3 step 5, "The Action":** the body's `"domain": "MINI"` becomes **`"domain": "FUEL_BALANCE"`**. Nothing else changes: the keys `origin_finding_id`/`origin_finding_revision_id` (PRE-FLIGHT (b) is answered: `domain_action.py:283-294`; the domain is checked at `domain_intent.py:104`), the title, `owner_label` "Site lead", `raised_at` `S−5d 13:00`, `idempotency_key` "kisiwa-fuel-action", and the domain store's clock at `raised_at`. Full call:
  ```python
  domain._store.test_db_clock_override = lambda: at(action["raised_at"])          # S-5d 13:00
  status, act = domain.create_action(tenant_id, site_id, "KISIWA-001", {
      "domain": "FUEL_BALANCE", "origin_finding_id": <night-4 Finding id>,
      "origin_finding_revision_id": <its SUPPORTED revision id>, "title": action["title"], "owner_label": "Site lead",
      "due_at": None, "raised_at": wire(at(action["raised_at"])), "actor": dict(ACTOR),
      "idempotency_key": "kisiwa-fuel-action"}, PRINCIPAL)                        # expect 201
  ```
- **The remaining step-5 calls stand as K7-D chose them,** following `T/demo_combined_mill.py:126-184`:
  - `work.create_case` `MAINTENANCE_REQUEST` (`asset_id` None, `finding_links []`, `action_links []`, the request title and narrative, key `kisiwa-fuel-request`), with a `StepClock` from `S−5d 13:10`;
  - `post_event` `ASSIGN` to "Site lead", occurred `S−5d 13:20` (key `kisiwa-fuel-assign`);
  - with a second `StepClock` from `S−4d 12:10`: `post_record` (`activity`, occurred `S−4d 12:00`, key `kisiwa-fuel-record`), then `post_event` `COMPLETE` occurred `S−4d 12:05` (`maintenance_record_id`, key `kisiwa-fuel-complete`);
  - the `SITE_VISIT` operational record (occurred `S−4d 12:00`, recorded `S−4d 12:15`, `case_id` = the request, key `kisiwa-kis-sealed-1`);
  - then `post_case_link` with the case's head revision and its latest event by `recorded_at`, with the domain clock at `S−4d 12:20` (key `kisiwa-fuel-link`).
  - **Stop S-7 is cleared once K6a merges.** K7-D merges main after K6a, then builds the Action step. If `create_action` still refuses, that is a K6a defect: report it, never work around it.
- **K7-F, "The freeze step" (§9l.3), now exact:**
  ```python
  from assetops_backend.actions.composition import build_fuel_verification_service
  svc = build_fuel_verification_service(url, test_clock=lambda: at(story["kisiwa"]["plan"]["freeze_at"]))  # S-4d 12:30
  status, frozen = svc.freeze_fuel_plan(tenant_id, site_id, UUID(action_id))      # expect 201
  svc = build_fuel_verification_service(url, test_clock=lambda: at(story["kisiwa"]["evaluate_at"]))       # S-1d 13:00
  judged = svc.evaluate_fuel_plan(tenant_id, site_id, UUID(action_id))            # {"state", "stored", "replayed", "outcome_id"}
  summary = svc.fuel_summary(tenant_id, site_id, UUID(action_id))
  ```
  - **The effective-time field is `verification_plan.effective_from`** (`frozen["plan"]["effective_from"]`): the linked case's first COMPLETE `occurred_at`, which on K7's calendar is **`S−4d 12:05`** (15:05 local), the resolved `action.complete_at`. K7's `action.effective_at` (`S−4d 12:00`) stays the physical change instant: the record, the site visit and run 6's start. The two differ by 5 minutes, and both precede night 6's window start (`S−4d 15:00` UTC, 18:00 local). The night partition is unchanged.
  - K7-F asserts, as stop S-6 on failure: `status == 201`; `effective_from == iso(resolve(complete_at))`; `effective_from < night 6 window_start`; `later_selection_rule.candidates.from == night 6's local date`; `baseline_selection.window_id` = night 4's window id. It records `judged["state"]` **as computed** (VERIFIED, INEFFECTIVE or INCONCLUSIVE; a NOT_JUDGED there is stop S-6) and `summary` in `kisiwa.json`. It never asserts a verdict.
  - **Story link and form** (K7-F): "KISIWA-001 fuel verification": `/sites/KISIWA-001/domain-actions/{id}/fuel-verification`. `LINK_FORMS` gains `"/sites/KISIWA-001/domain-actions/"`.
  - KIS-9 (e)'s K7-F half reads `plan.recorded_at == freeze_at` and an outcome `recorded_at == evaluate_at`.
  - K7-F's size is unchanged (0.5): these calls were its "K6 wiring" item.
- **K9:** KIS-5 has moved to K6b, so K9's size is unchanged. KIS-10 runs at E3 with the other rows.
- **K8:** the Portfolio Assure **count** includes the Kisiwa fuel verdict (as §8.4 said), read from the board's Verified results entry. **There is no Portfolio value line for it (H2).** K8's all-26 recapture adds the fuel verdict page.
- **After-the-demo list (coordinator):** "fuel verdict tick stage (the evaluation is explicit in v1)"; "list fuel Actions on a Site Actions surface".

### 9m.6 Sizes, critical path, tripwire, date

- **K6 = K6a 0.6 + K6b 1.4 = 2.0** (§9.5 had 1.5). The +0.5 covers:
  - the S-7 origin work (a new Action domain and its selection check, §9m.1 items 1–4), about 0.4 of K6a, which §8.4 did not foresee;
  - the chain Ref fix (item 6);
  - the v69-shaped page in place of a single panel.

  It is reported, not absorbed (the contingency is spent, §9h.8). **Kisiwa total: 18.3 → 18.8.**
- **Critical path:** spent 3.65 (F0r, K1, K3) → K4a 1.5 → K6a 0.6 → K6b 1.4 → K7-F 0.5 → K8 captures 0.25 → K9 1.0 ≈ **8.9 lane-units**. That is up from R3l's 8.4 and **below the 9.75 tripwire, with about 0.85 of headroom. No cut, and no owner question.**
  - If K6b's pure module and page start while K6a is in review (§9m.4), about 0.3 overlaps and the path is about 8.6.
  - **Watch item:** the headroom is now the smallest it has been. If K6a ends above its 0.8 stop, or K6b above its 1.6 stop, together adding more than 0.85, the Architect re-rules before K7-F and puts the cut question to the owner. The first candidate stays as named before: drop the verdict **page and board entry** (K6b's 0.45 of UI), keeping the stored verdict and KIS-5; the second is dropping K6 entirely.
- **Lanes:**
  - lane 3 runs K4a (finishing) → K6a → K6b → K7-F;
  - K7-D (lane 2 / the fourth builder) builds its Action step after K6a merges, at about t≈K4a+0.6. It keeps its float, because it must merge before K7-F starts, about 2.0 later;
  - lane 1 (K5 → K4b → K8) is unchanged and shares `mini.py`/`board.py` with K6b (disjoint edits).
- **Demo date:** about **+3.4 working days** (range 2.9–5.4) against the plan without Kisiwa, up about 0.15 day from R3l's +3.25 (0.5 lane-unit on the critical path at about 3 lane-units a day).
- **Machine time:** unchanged (K6 adds no prepare; two L2 files on `assetops_k6_test` when the machine is idle).
- **Plan HTML rows (coordinator):**
  - **Build-units table:** the DIESEL-1-R3 row becomes **18.8**, with "K6 2.0 (K6a 0.6, K6b 1.4)".
  - **Lanes figure:** lane 3 strip K4a → K6a → K6b → K7-F.
  - **Rulings table:** add "DIESEL-1-R3m: K7-D stop S-7 ruled: fuel Finding raises a `FUEL_BALANCE` domain Action (0057 widens the domain CHECK; MINI unchanged); fuel selection = latest SUPPORTED revision; K6 split K6a/K6b; family `fuel-residual-within-band-1` in 0057; effective time = linked case COMPLETE `occurred_at`; fuel verdict page at its own route (FUEL_VERDICT); Assure entry without value line (H2); KIS-5 to K6b, KIS-10 new; Kisiwa 18.8; path about 8.9".
  - **After-the-demo list:** the two items in §9m.5.

### 9m.7 Owner questions

None.

For the owner's information, in plain words:
- **Why the fix needed a small change first.** The system only let a finding about the generator, the cold room or the chargers start an action. The new "unexplained fuel" finding could not, so the builder correctly stopped. We now add a fuel-specific kind of action ("seal the tank cap, sign the dip log, protect the sensor's power"). Kobo's mill action and the cold-room and charger actions stay exactly as they are.
- **What the check says.** After the fix, the system looks at the first 3 fully checked nights. If on each of them the fuel stayed inside the stated margin and the tank sensor sent readings all night, it says the fuel stayed accounted for. It always adds: "This check shows the fuel stayed accounted for after the change; it does not measure how much the change itself prevented." It shows no money, and it never says the fix stopped a loss.
- **The result is whatever the data says.** The nights are chosen by data quality before anyone looks at the result. If a night fails, the page says so.
- **Cost.** About half a unit more than planned, all on the longest chain of steps. The demo moves by about 0.15 of a working day. We are still inside the limit we set for that chain, with less room to spare than before.

## 9n. Ruling DIESEL-1-R3k2: K4a review FIX, M1 (a window that returns to an earlier digest) and L1/L2

- Architect: Claude, 2026-11-08. Binding: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Review: `.agent/review-K4a.md` on `task/DIESEL-K4a-unexplained-fuel-finding` at `979c9da3e` (FIX, M1 reproduced on `assetops_k4_test`).
- **M1 is accepted as a gap the spec caused.** §9j.4 relied on two unique constraints. One of them, `finding_revision_basis_unique`, was dropped in `0015_finding_returning_basis.py`. The other, `analytic_run_basis_unique` (`0007:64`), makes the run unique per digest, not per window revision. **This ruling replaces §9j.4's two "Idempotent" sentences** (the persist bullet and "Re-running with the same window writes nothing").

### 9n.1 Fix (K4a fix round; same files, no new file)

1. **`PostgresAssessmentStore.fuel_balance_persist`** (`B/analytics/adapters/postgres_assessment_store.py:1508-1530`):
   - Keep the first check unchanged: if an `assessment_revision` already exists for `(site, 'fuel-balance-1', "{tank}:{night}", window.revision)`, return it.
   - **Then reuse the run:** `SELECT id FROM analytic_run WHERE site_id = :s AND analytic_id = 'fuel-balance-1' AND model_version = 'fuel-balance-1/v1' AND window_start = :ws AND window_end = :we AND input_sha256 = :b` (the exact `analytic_run_basis_unique` key).
     - If a run is found, use its id. Do not insert into `analytic_run` or `analytic_run_evidence`.
     - Otherwise insert both, as now.
   - **Always** insert the new `assessment_revision` (`revision_no = window.revision`, `result` naming *this* window's id) and its `analytic_run_assessment` row, citing that run. `analytic_run_assessment`'s PK `(run_id, assessment_revision_id)` (`0007:112`) allows one run for several revisions.
   - Docstring: "Idempotent per window revision. A window revision whose digest an earlier revision of the same night already had cites that earlier run (`analytic_run_basis_unique`, 0007:64): same digest, same inputs (DIESEL-1-R3k2)."
   - **Run evidence must match.** When a run is reused, its `analytic_run_evidence` set must equal `window.evidence_ids`. If it differs, raise `RuntimeError("fuel-balance-1 run reused with a different evidence set")`. Never insert into the run to make them agree. If this ever fires in a test, that is stop **S10**.
2. **`PostgresFindingStore._insert_fuel_revision`** (`B/analytics/adapters/postgres_finding_store.py:789-791`):
   - The replay guard compares with the Finding's **latest** revision only, which has been the house rule since 0015 (`_insert_revision`):
     ```sql
     SELECT basis_sha256, transition FROM finding_revision WHERE finding_id = :f ORDER BY revision_no DESC LIMIT 1
     ```
   - It returns None only when both values equal `(window.input_sha256, transition)`.
   - Comment: `# DIESEL-1-R3k2: latest revision only (0015 LR-01 rule); a basis that returns after another revision is a new revision.`
3. Nothing else changes: the lifecycle table in §9j.4, `fuel_transition`, the service, the consequence writer, and the R3k filters all stay as they are.

### 9n.2 Tests (added to `backend/tests/test_k4a_fuel_finding_postgres.py`, `assetops_k4_test` only)

- **B10. A → B → A → B on one night.**
  - Append four window revisions through `PostgresFuelBalanceStore.append`, each with a **fixed** `input_sha256`: A, B, A, B. Their states are UNEXPLAINED, WITHIN_MARGIN, UNEXPLAINED, WITHIN_MARGIN. They need distinct `recorded_at`, but the digests are set explicitly and do not include the clock.
  - Call `raise_night` after each append.
  - **Expected statuses:** OPENED, WITHDRAWN, REVISED, WITHDRAWN.
  - **Expected Finding revisions (four):** `OPENED/SUPPORTED`, `NO_LONGER_SUPPORTED`, `SUPPORT_CHANGED/SUPPORTED`, `NO_LONGER_SUPPORTED`. Each claim's `fuel_balance_window_id` is the window revision it was raised from.
  - **Expected rows:**
    - exactly **2** `analytic_run` rows for the night (digests A and B);
    - **4** `assessment_revision` rows (`revision_no` 1–4), where revisions 1 and 3 cite run A and revisions 2 and 4 cite run B;
    - **2** `fuel_residual_consequence_revision` rows (for Finding revisions 1 and 3);
    - `fuel_finding(...)` reads NO_LONGER_SUPPORTED with `consequence None`.
  - Calling `raise_night` a fifth time with no new window gives UNCHANGED and writes nothing.
  - **Must fail** if the run reuse is removed (IntegrityError at the third raise), or if the guard goes back to "any revision" (the fourth raise returns UNCHANGED and the Finding stays SUPPORTED).
- **B11 (review L1, in this round). The price is the one known at the window end.**
  - Set up a stored UNEXPLAINED window for night N with no diesel price. Then publish a price whose validity covers night N, but **recorded after** `window_end` and before the raise (test clock).
  - `raise_night` gives OPENED with an **UNPRICED** consequence: `price_reason = 'NO_PRICE'`, and every price and amount field NULL.
  - **Must fail** if `findings_service.py:90` passes `known_at = now` instead of `w.window_end` (the reviewer's m3 mutation).
- Re-run: §9j.8 A and B, B7–B9, the K3 L2 file, and the must-stay-green list of §9j.8 and §9k.5 that touches these two store files: the cold and EV Finding store tests and `test_s4_finding_domain_filter_postgres.py`. **Part C is not re-run**, because night 4 has one window revision and the fix does not affect it. No suite.

### 9n.3 L2: carry for K7's card (the coordinator passes it to K7 verbatim)

> **K7 carry (DIESEL-1-R3k2, from K4a review L2):** once K7 merges, a combined dataset without Kisiwa is a failure, not a skip. In `tools/demo_combined_finish.py:957-959`, KIS-4 (and every other KIS row that has the same "not in this dataset (K7 adds it)" branch) returns a failing body `{"kisiwa": "missing: no KISIWA-001 Site in this dataset", "checked": 0}` with the row marked failed, in place of the skip. K7 adds an L0 self-test fail body for a summary with no `KISIWA-001`, and changes any existing self-test that expected the skip. K7's packet lists these lines as "carry R3k2 L2". If any KIS row would then fail on a dataset that legitimately lacks Kisiwa, K7 stops and reports it.

- No K4a code change for L2. K7's size grows by about 0.03, which is absorbed inside K7's range.

### 9n.4 Size, critical path, tripwire

- **K4a fix round: about 0.1** (two store edits 0.03, B10 0.04, B11 0.03). That takes K4a from **1.5 to 1.6**, inside S7's ceiling of 1.7. Reported, not absorbed.
- **Kisiwa total: +0.1** on whatever the coordinator's current figure is after R3m.
- **Critical path:** R3m's 8.9 plus 0.1, so **about 9.0 lane-units**. That is below the 9.75 tripwire, with about 0.75 of headroom. No cut and no owner question. The demo date moves by about 0.03 day, which is within the current range.
- Fix round on Sonnet, from this card, in worktree `AssetOpsV1-k4a`. The re-review goes to a fresh Claude reviewer and checks M1 and L1 by name, including the two B10 mutations and the B11 mutation.

### 9n.5 Owner note (plain words)

The reviewer found that if a fuel delivery is recorded on the wrong night and then corrected, the unexplained-fuel check would crash, or would leave an old warning showing. The fix makes each correction add a fresh, correct entry, as the generator findings already do. It also adds a test that the fuel price used is the one known at the end of the night. The work grows by a tenth of a unit, and the demo date does not move in any way you would notice.

---

## 9m2. Ruling DIESEL-1-R3m2: K6a stop S-a3 (the maintenance request's Action link)

- Architect: Claude, 2026-11-08. Binding: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. READ on main at `1e0020df8` and on K4a's branch. Nothing was run.
- **The stop is confirmed.** `work/site_index.py:229-241` `_action_link` gives every domain link that has lineage and a `finding_revision_id` the address `/sites/{site}/actions/{aid}/verification`. On a MINIGRID Site that address is the W1 Action frame, and a fuel Action has no W1 row.
- **Owner: K6a.** K6a is the unit that creates the fuel Action, so it must not ship a link that leads to a "not found" page. K6b fills in the real address.
- **Exact change (K6a):**
  1. `work/adapters/postgres_work_read.py:169-172` (the `domain` list in the case links read): add a conditional key, exactly as the opportunity key is added: `**({"action_domain": r["action_domain"]} if r["action_domain"] == FUEL_DOMAIN else {})`.
     - `_domain_links` already selects `a.domain AS action_domain` (`:60`).
     - Cold, EV and mill link dicts stay byte-equal.
  2. `work/site_index.py` `_action_link`, at the start of the `DOMAIN_ACTION` branch:
     ```python
     if link.get("action_domain") == FUEL_DOMAIN:  # DIESEL-1-R3m2: a fuel Action has no W1 page; K6b sets its verdict address
         href = None
     elif lineage and link["finding_revision_id"] is not None:
         ...
     ```
     The `elif`s that follow are unchanged. `FUEL_DOMAIN` is imported from `work.domain_action`.
  3. K6a's approved file list gains these two edits only.
- **What the link reads between the two merges:** the plain label "Action" (`ACTION_LABEL`) with `href` None. That is the existing no-link rendering (the label is shown, but it is not clickable). It is honest and needs no new literal.
- **K6b (added to §9m.4):** the fuel branch becomes `href = f"/sites/{site_code}/domain-actions/{aid}/fuel-verification" if lineage else None`. K6b adds `work/site_index.py` to its file list. Its L0 test flips the K6a assertion below to that address.
- **Tests (K6a):**
  - **L0**, in `test_k6a_fuel_action_origin.py`: `_action_link` on a fuel link with lineage true gives `href is None` and label "Action". The same link without `action_domain` (a Cold link) still gives `/actions/{aid}/verification`. A mill link still gives `/domain-actions/{aid}/verification`. Must fail if the fuel branch is removed (the fuel link then yields `/actions/…/verification`).
  - **L2**, item 5 of K6a's L2: the request detail and index for the fuel Action's case serve no `href` that contains `/actions/` for that Action id. Must fail on the same mutation.
- **Confirmed:**
  - 0057's `down_revision` = `"0056_unexplained_fuel_finding"`. That is K4a's `revision` (and K4a's own `down_revision` is `0055_fuel_balance_window`), read on `task/DIESEL-K4a-unexplained-fuel-finding`.
  - `test_w502_domain_intent_api.py` failing to collect without a DB URL (`NameError: COLD`) is **not K6a's to fix**. The file imports `COLD` from `test_w502_domain_intent_postgres` inside its DB-gated block (`:23`), and K6a does not touch that file. It is a pre-existing collection quirk, so the coordinator adds it to the follow-up list. K6a runs it with `ASSETOPS_TEST_DATABASE_URL` set to `assetops_k6_test`.
- **Size:** K6a +0.03 (within its 0.8 stop). The critical path is unchanged at about 8.9. Owner questions: none.

## 9j2. Ruling DIESEL-1-R3j2: K4b pre-flight stop S-a (the chain graph refuses `FINDING:UNEXPLAINED_FUEL`)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). READ on main at `c1324273b` (the K4b worktree base; K4a, K6a, K6b merged) and on `task/DIESEL-K5-fuel-screens` (not merged). Nothing was run.
- **This ruling amends §9j.11–§9j.13 and §9l.4's K4b bullets.** Everything not named here stands.

### 9j2.1 The stop (READ, confirmed)

- `chain/graph.py:159-160` rejects an `ENTRIES` key `FINDING:<m>` unless `<m>` is a key of the thread-lifecycle `clean_day_measures` (`chain_keys`, `:107-111`, through `thread_signal_key`). The check runs at app start (`main.py:644`), in `test_ch5b_graph.py::test_main_config_passes` and in `chain_graph_render`.
- `config/chain/thread-lifecycle-v1.json` has no `UNEXPLAINED_FUEL` key, and `parse_thread_lifecycle` (`chain/lifecycle.py:101-103`) rejects an empty list.
- §9j.11 adds the map entry and never names the lifecycle side. That was an Architect miss in R3j, not a builder error. It is recorded as D3 (structural oversight).

### 9j2.2 Decision: route (b), an explicit empty clean-day list

**Options weighed:**
- **(a) A real fuel clean-day measure** (a chain measure such as "night accounted for within the margin", register input, adapter, snapshot rows, lifecycle entry). **Rejected for the demo.** It is about 0.6–0.9 of new chain work. It would also change how the fuel thread closes (after N clean nights), and nothing in K6b's verdict or K7's story depends on that. It goes on the after-the-demo list: "fuel clean-night measure, so a verified fuel thread can close".
- **(b) An empty list is a valid declaration. Chosen.**
  - Runtime is unchanged. `measures_for` already returns `()` for a missing mechanism (`lifecycle.py:74-75`), `complete_days` returns `set()` for no measures (`:293-294`), `used_measures` uses `.get` (`why.py:91`), and `postgres_thread_sources.py:192`/`:269` take a union in which an empty list adds nothing. The fuel thread behaves exactly as it does today on main.
  - It is honest. It says in configuration what is true: this mechanism has no clean-day measure, so its thread never closes on clean days.
  - It is consistent with how a fuel thread is meant to end. K4a's lifecycle withdraws an Action-less thread when support is lost (`OPEN` + `SUPPORT_LOST` → `WITHDRAWN`, `lifecycle.py:57`). K6b's verdict drives `CHANGE_APPLIED` → `RESOLVED_MONITORING` on VERIFIED, or `REOPENED` on INEFFECTIVE / expired INCONCLUSIVE. A later UNEXPLAINED night is a new occurrence on the same thread, so `RESOLVED_MONITORING` → `RECURRED`. None of these needs a clean-day measure. The only transition the fuel thread cannot take is `RESOLVED_MONITORING` → `CLOSED` (`CLEAN_DAYS`), and with (b) that is a declared fact rather than an accident.
- **(c) Let the graph accept a `FINDING:` key with a `NOT_CHAIN_SOURCED` row.** **Rejected.** It widens a guard whose purpose is that every Finding mechanism has a lifecycle. A `FINDING:` key that the threads step does handle (it does, through `SUBJECT_COLUMN`) would be mislabelled "not chain-sourced".

**The policy version stays `thread-lifecycle/1`.** The effective policy is identical for every mechanism, including `UNEXPLAINED_FUEL` (empty before by default, empty now by declaration). No stored event changes meaning.

### 9j2.3 Exact changes for S-a (K4b)

1. `B/chain/lifecycle.py` `parse_thread_lifecycle`, the per-mechanism check (`:102`):
   - becomes `if not isinstance(names, list) or not all(isinstance(n, str) and n for n in names):` (the `or not names` term is removed). The error message is unchanged.
   - Comment above the loop, verbatim: `# DIESEL-1-R3j2: an empty list declares a mechanism with no clean-day measure; its thread never closes on clean days (it stays RESOLVED_MONITORING until a recurrence).`
   - The top-level "must be a non-empty object" check (`:98-99`) is unchanged.
2. `config/chain/thread-lifecycle-v1.json`: `"UNEXPLAINED_FUEL": []` added as the **last** key of `clean_day_measures`. No other byte changes.
3. `B/outcomes/outcome_map.py` `ENTRIES`: `"FINDING:UNEXPLAINED_FUEL": (("MG-8",), ()),  # DIESEL-1-R3j: no mock F-id (MD-FUEL-K4-1)` placed **directly after** `"FINDING:EV_INTERRUPTION"`. The group comment `# stored Finding mechanisms (the four that exist)` becomes `(the five that exist)`.
4. `Docs/demo-sprint/chain-graph.dot` and `.svg` regenerated with `chain_graph_render` (no hand edit). The mechanism node has no measure edge; that is correct.
5. Tests:
   - `test_ch5b_graph.py:31` becomes `"chain graph OK: 7 measures, 6 lifecycle mechanisms, 16 outcome-map entries"`. The mutation table is unchanged (its "Finding without lifecycle mechanism" case still fires).
   - `test_ch6_contributions.py` `ENTRIES_TODAY` gains the same line in the same position.
   - **New L0, in `test_k4b_protect_fuel.py`:**
     - `parse_thread_lifecycle` accepts `{"X": []}` and gives `measures_for("X") == ()`; it still raises `ChainConfigError` for `{"X": "a"}`, `{"X": [""]}` and `{}` (must fail if the list-type check is dropped too).
     - `load_thread_lifecycle().measures_for("UNEXPLAINED_FUEL") == ()` and `"UNEXPLAINED_FUEL" in load_thread_lifecycle().clean_day_measures` (must fail if the config line is removed: the graph check then raises `entry_source`).
     - `check(chain_graph_inputs())` passes (the app-start check).
   - `test_ch3_lifecycle.py`, `test_ch2_threads.py`, `test_md0b_ensure.py` and the CH-5a2 contract goldens stay green unchanged. The goldens hold no fuel thread, so the new key cannot reach them. Any change there is stop S-b.

### 9j2.4 The fuel thread line after a verdict (honesty guard)

- After K6b's VERIFIED, the fuel thread sits in `RESOLVED_MONITORING` and never closes. `THREAD_MONITORING` ("… · {k} more fully checked days to close") would then promise a countdown that never moves.
- Today that line cannot appear for the fuel thread: `_thread_action` (`board.py:725-732`) looks only at W1 `ActionFact`s, and the fuel Action is a domain Action. The verdict reaches the board as the Assure contributor (`FuelVerdictFact`, K6b). K4b keeps it that way with a guard, so a later change cannot produce the false countdown:
  - `B/site_outcomes/mini.py`: a fuel `FindingFact`'s `lifecycle_view` is `{**view, "close_measured": False}` when `ct.policy.measures_for(mechanism) == ()`. Dispatch views do not get the key.
  - `B/site_outcomes/board.py` `thread_line_item`, first line of the `if f.thread.get("verified"):` branch: `if view.get("close_measured") is False: return None  # DIESEL-1-R3j2: no clean-day measure, so no countdown; the verdict is the Assure contributor`.
  - L0 test: a fuel `FindingFact` with a verified thread **and** an `ActionFact` on that thread gives `thread_line_item(...) is None`; the same fact without `close_measured` gives a `MONITORING` item (non-vacuous). Must fail if the guard is removed.
  - Every dispatch, Cold and EV thread line stays byte-equal (no `close_measured` key).

### 9j2.5 Answers to the builder's other questions

1. **`site_outcomes/composition.py`: approved.**
   - `build_outcome_board_service` builds `fuel_balance = build_fuel_balance_store(database_url) if database_url else None`, with a function-local import from `assetops_backend.fuel_balance.composition` (this avoids an import cycle through `work.composition`). It passes `fuel_balance=fuel_balance` to `BoardServices`, and `dispose()` calls `fuel_balance.dispose()` when it is not None.
   - `BoardServices` (`read.py:87`) gains `fuel_balance: Any = None` as its **last** field, with the comment `# PostgresFuelBalanceStore (DIESEL-1-R3j2; K4b's fuel_windows/fuel_findings/has_windows)`.
   - `read.py` `mini_ports` binds `fuel_windows`, `fuel_findings` and the applicability read (`has_windows`) from it. If it is None, the port raises `PortUnavailable` as every other `BoardServices` port does, and `Reads` records PARTIAL. It is never a "0" or "not applicable" claim. **Exception, so Kobo stays byte-equal:** MG-8's `not_applicable` comes from `has_windows`. If that read fails, MG-8 is `UNKNOWN` (`findings_ok` rule), never N/A.
   - `test_out_b4_imports.py` stays unchanged and green (only `composition.py` imports another composition).
2. **The K5 code (store methods, `night_text.py`, `fuel_finding_ref`): no byte-for-byte copies.**
   - **Why:** K4b needs more of K5 than the builder listed. §9l.4 also requires `refs.fuel_finding_ref` and the `FUEL_FINDING` ref kind, which on K5's branch come with frontend counterparts (`linkRefs`, the client href builder). K5's `FUEL_REASON_WORDS` is already amended against §9j.11 (the guard-V-safe "no-load" wording), and K5 still has captures pending. Copies of a moving branch drift, and a partial copy of the store file (two of K5's three methods plus its import) is a real conflict, not a trivial one.
   - **Order:**
     - **Now:** K4b builds everything that does not need K5: §9j2.3, §9j2.4, MG-8 and applicability plumbing, the composition and ports (with `night_context`/`has_windows` calls written against K5's signatures as read above), the claims exclusion (§9j2.5 item 4), the Portfolio card keys and frontend, UF1 and KIS-8a, and their tests with fake ports.
     - **Preferred:** K5 merges to main, and K4b runs `git merge main` at its next commit boundary. It then imports `night_context`, `has_windows`, `FUEL_REASON_WORDS` (from `fuel_balance/night_text.py`) and `fuel_finding_ref` as they stand on main.
     - **Fallback**, only if K5 has not merged when K4b's K5-independent work is committed: the coordinator may tell K4b to `git merge task/DIESEL-K5-fuel-screens` (a real merge at K5's accepted head). K4b then **must not merge to main before K5 does**, and it merges main again before its packet.
     - In neither case does K4b edit a K5 file.
   - **New stop S-f:** K4b needs a change inside a K5 file (signature, literal or ref kind). Report it; K5's owner fixes it on main.
3. **The Protect category count: intended in K4b.** It does not wait for K8.
   - Once mapped, the fuel thread's primary category is Protect everywhere `outcome_roles` is read: `estate/portfolio.py:297` `category_counts` (`open_findings` and `sites_with_primary_finding`), the Findings lens chips (`lens_flags`) and thread `categories`. Kisiwa's Portfolio Protect count rises by one while an unexplained-fuel Finding is open.
   - That is true, and it is the purpose of the mapping. Holding it back would need a mechanism filter in `category_counts`, which is a special case that hides a real Protect finding.
   - **Goldens:** no Kobo, Cold or EV golden holds a fuel Finding, so §9j.13's golden acceptance stands unchanged. The Kisiwa effect first appears in K7's data. **K8** re-expects it in its COH rows and the all-26 recapture. The K8 card gains one line: "Kisiwa Protect `open_findings` +1 while the night-4 thread is open (R3j2)".
4. **`claims.disrupting`: exclude `UNEXPLAINED_FUEL`. Confirmed.** Unexplained fuel is a loss-of-stock finding, not a service disruption. `SITES_DISRUPTED` must not count it.
   - `B/chain/claims.py`: `NOT_DISRUPTION_MECHANISMS = frozenset({"UNEXPLAINED_FUEL"})  # DIESEL-1-R3j2: a stock finding, not a service disruption` beside `DISRUPTED_STATES` (`:41`). `disrupting` (`:112-114`) gains `and t.get("mechanism") not in NOT_DISRUPTION_MECHANISMS`. The thread wire carries `mechanism` (`site_chain.py:81`). Both callers (`claims.py:148`, `chain_api.py:379`) take the exclusion with no edit.
   - L0 test: an `OPEN` primary-Protect thread with `mechanism` `UNEXPLAINED_FUEL` is not in `disrupting(...)`; the same thread with `COLD_EXCURSION` is (must fail if the predicate is removed).
   - `threads.classify` (open/in-hand/verified counts) still includes the fuel thread, as §9j.11 says.

### 9j2.6 Approved files (added to §9j.13)

- `B/chain/lifecycle.py` (the `:102` predicate and its comment only)
- `config/chain/thread-lifecycle-v1.json` (one key)
- `Docs/demo-sprint/chain-graph.dot`, `Docs/demo-sprint/chain-graph.svg` (regenerated)
- `B/site_outcomes/composition.py` (the store, the field and the dispose)
- `B/chain/claims.py` (now required, no longer conditional)
- `backend/tests/test_ch5b_graph.py` (the count line), `backend/tests/test_ch6_contributions.py` (`ENTRIES_TODAY`)
- `B/site_outcomes/board.py` and `mini.py` were already on the list; the §9j2.4 guard is in scope.
- **Removed from §9l.4:** "K4b starts after K5's phase B build" is replaced by the order in §9j2.5 item 2.

### 9j2.7 Size, stops, critical path

- **K4b: 1.0 → 1.1** (range 0.95–1.3). That is +0.1: the S-a route and its tests 0.04, the thread-line guard 0.02, the claims exclusion 0.02, the composition field and dispose 0.02. **Stop S-e's ceiling becomes 1.3.** The increase is reported, not absorbed: **Kisiwa total +0.1.**
- **Critical path:** K4b stays off it. Lane 1 (K5 merge → K4b 1.1 → K8 → captures) was about 8.15–8.4; with +0.1 and a short wait for K5's merge it is about 8.3–8.6. That is still below the main path of **about 9.0**, which is unchanged. **Headroom to the 9.75 tripwire: about 0.75.** No cut is needed and the demo date does not move.
- **After-the-demo list (coordinator):** "fuel clean-night measure, so a verified fuel thread can close".
- **Plan HTML rows (coordinator):** K4b becomes 1.1. The rulings table gains "DIESEL-1-R3j2: `UNEXPLAINED_FUEL` declared with no clean-day measure (thread never closes on clean days); fuel thread excluded from `SITES_DISRUPTED`; Kisiwa Protect count +1 while open; K4b imports K5 after K5 merges (no copies); K4b 1.1".

### 9j2.8 Owner questions

None. For the owner's information, in plain words: the system has a rule that every kind of finding must say how it is closed. The unexplained-fuel finding had no such rule yet, so the system would have refused to start. It now states openly how this finding ends. It is withdrawn when a later check no longer supports it. Once a fix is verified, it stays under watch and comes back if fuel goes missing again. It does not yet close by itself after a run of clean nights. While the finding is open, Kisiwa's "Protect" count shows one more item, which is true. That count is not presented as a service outage. The work grows by a tenth of a unit, and the demo date does not move.

---

## 9o. Ruling DIESEL-1-R3n: after K7-D's scratch prepare (E3 timing, the KOBO-001 404s, KIS-3's evidence, K7-F start)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. READ on main at `c5b25066c` and on `task/DIESEL-K7-kisiwa-story` at `63f60f986` (packet `.agent/review-packet-K7.md`; `tools/demo_combined.py:404-633`; `tools/demo_combined_rows.py:526-590`). Nothing was run.
- **This ruling amends §9l.3 (K7-F, the scratch prepare, `EXPECTED_SECONDS`), §9l.5's E3 lines and §9m.6's path.** Everything not named here stands.

### 9o.1 E3 timing, restated from measured figures

- **Measured:**
  - three-Site whole-list prepare: 3585 s (DD-1b2b);
  - Kisiwa build step (Kisiwa-only scratch): 3568 s (10 days at 315–382 s, mean about 353 s; register 2 s);
  - Kisiwa-only total: 4199.5 s, so the shared tree, finish, ticks and prebuild cost about 630 s, and they are already inside the 3585 s.
- **Four-Site estimate:**

  | Part | Seconds |
  |---|---|
  | Three-Site prepare as measured | 3585 |
  | Slack for K4b/K5/K6 reads in the ticks and prebuild since DD-1b2b | 0–300 |
  | Kisiwa build, as measured | 3568 |
  | Slack for Kisiwa days built last, on a database that already holds Kobo, Cold and EV (up to +15%) | 0–535 |
  | Kisiwa's share of the shared steps: mini-depth drain, two ticks and prebuild with a fourth Site, KIS rows in the self-check | 150–400 |
  | **Total** | **about 7300–8390 s, 2.0–2.35 h** |

- **Margin against the 3 h cap (10800 s): about 2400–3500 s (0.65–0.95 h, 22–32%).** The top of the range is about 600 s under the 2.5 h (9000 s) re-ruling trigger. **It fits. It is not close to 3 h, so there is no owner question.**
- **Parallel: no.** Kisiwa installs after all three core Sites (§9l.3 install order), every step writes one database at story instants, and the K7-D run's lowest free RAM was 1.91 GB with a single job against the 1.0 GB floor. A second concurrent child would break the "one heavy job" gate and risk the floor.
- **Trim: none.** Every per-day step is a guard or a product write (publish and accept, the physics and dip checks, assess, raise). None is cut to save time. If K9's rehearsal exceeds 2.5 h, the first lever the Architect will weigh is profiling the per-day cost (where the 353 s go against K1/K3's 180–300 s). It is not parallelism and not a cap raise.
- **`EXPECTED_SECONDS["kisiwa"]` becomes 3600** in K7-F (10 × about 353 s, plus register, assess and raise; replaces 2520). Comment: `# DIESEL-1-R3n: measured in K7-D's scratch prepare (3568 s build step)`. This only feeds the default 2× cap; E3 and the rehearsal pass `--cap-seconds 10800` explicitly.
- **K9's rehearsal, restated:** a four-Site whole-list prepare on its own `*_test` database with `--cap-seconds 10800`, keep-awake on, about **2.0–2.35 h** of machine time (was about 1.5 h). It is machine time outside K9's 1.0 lane-units, as before. K9 restates E3 from the rehearsal's measured wall time. **Stops stand:** above 9000 s, the Architect rules before E3. If the run reaches the 10800 s cap, the cap is never raised silently: a higher cap or a cut goes to the owner.
- **The first four-Site run is K9's rehearsal.** It is also the first run in which Kisiwa sits beside the core Sites in the full self-check. A non-KIS row that fails only because Kisiwa is present (estate or Portfolio counts, COH rows, for example Protect `open_findings` +1, §9j2.5 item 3) is K8's re-expectation, reported as a stop to the Architect. K7-F does not edit those rows.

### 9o.2 The KOBO-001 404s in a Kisiwa-only prepare: expected, not a defect. Leave them alone.

- **Cause (READ):** `performance_and_prebuild` (`tools/demo_combined.py:626-633`) hard-codes `("KOBO-001",)` for the Performance comparison. That call and the prebuild both run with `check=False`. The prebuild warms pages that include Kobo's. Any partial prepare without Kobo (Cold-only, EV-only or Kisiwa-only) prints the same lines. This predates K7, and neither line can fail the prepare.
- **Decision: no `--sites` skip.** E3, K9's rehearsal and the default prepare after K7-F always include Kobo. A skip would edit a shared step for a scratch-only cosmetic gain, and the three-Site path must stay byte-equal in behaviour (S-9).
- **K7-F's scratch packet** lists these two lines as "expected in a Kisiwa-only prepare (R3n)". It also **records the prepare's exit code**: it must be 0, and a non-zero exit is stop S-6.

### 9o.3 KIS-3: it already asserts the tolerance; K7-F adds the printed evidence

- `kis3` (`tools/demo_combined_rows.py:555-571`) already asserts every one of the five terms against `Fraction("1/100000")` and fails the row beyond it. A pass therefore means "within 1/100000 L". No new assertion is needed.
- **What is missing is the evidence.** K7-F adds to KIS-3's pass body `"tolerance_l": "1/100000"` and `"max_diff_l": {term: str(<largest |stored − handover| over the ten nights>)}` for the five terms. The values are exact `Fraction` text. The L0 pass self-test asserts both keys, and every `max_diff_l` is ≤ the tolerance.
- **Owner: K7-F** (it already edits `T/demo_combined_rows.py` for KIS-9 (e)). Its second scratch packet quotes the printed line.
- **K7-D's ASSIGN deviation (packet "Deviation") is ratified.** The ASSIGN is recorded at `assign_at` (`S−5d 13:20`) on its own clock, because the Work API refuses an occurred-at more than 5 min after the recorded-at (`B/work/model.py:36`). It is at its story instant, and the calendar is unchanged.

### 9o.4 K7-F starts now, branched from K7-D; the two merge to main together

- **Start now.** K6a and K6b are merged, which was K7-F's dependency.
- **Branch:** `task/DIESEL-K7F-kisiwa-freeze` in `C:\Users\assef\Bineyame\AssetOpsV1-k7f`, **from `task/DIESEL-K7-kisiwa-story` at `63f60f986`** (this replaces §9l.3's "from main after K6 merges"). Then `git merge main` to bring in K6b. Never rebase.
- **Scope:** §9l.3 "The freeze step" as fixed by §9m.5, plus this ruling: `EXPECTED_SECONDS` (§9o.1), KIS-3 evidence (§9o.3), the default `--sites` flip, the verification link form and KIS-9 (e).
- **K7-D's review runs in parallel** on its own branch, against the K7-D diff. Any K7-D fix commits land on `task/DIESEL-K7-kisiwa-story`, and K7-F runs `git merge task/DIESEL-K7-kisiwa-story` before its packet. K7-F's review covers only the K7-F delta (`git diff <K7-D accepted head>...K7-F head`).
- **Merge:** after **both** reviews ACCEPT, the coordinator merges `task/DIESEL-K7F-kisiwa-freeze` into main **once**. It carries K7-D, and the merge message names both. K7-D is never merged alone, because the R3k2 L2 carry makes a three-Site default fail the KIS rows until the default flips.
- **Second scratch prepare (K7-F), same command and database as K7-D's:** `python tools/demo_combined.py --db assetops_demo3_kisiwa_test --work var/demo3_kisiwa prepare --sites kisiwa --cap-seconds 5400`.
  - **When:** after K7-F's L0 tests are green and committed, with main (K6b) merged in.
  - **Gate (all required):**
    - only one heavy job on the machine, which the coordinator confirms;
    - no K5 capture or `serve` reading `assetops_demo3_kisiwa_test` during the run, because the tool drops and recreates it;
    - free RAM ≥ 2.5 GB for 2 consecutive minutes, sampled every 30 s, with the samples in the packet;
    - `tools/keep-awake-during-tests.ps1` running (no `-ExecutionPolicy`).
  - **Cap 5400 s.** Measured 4199.5 s, plus seconds for the freeze and evaluation, is about 1.29×. The worst measured day ×10 gives about 4450 s. Stop at the free-RAM floor of 1.0 GB (S-8). A stall with no output for 10 min is reported, not retried.
  - **Run with `PYTHONUNBUFFERED=1`**, set in the environment, so the stall rule can actually see output: K7-D's log was blind for about 60 min. Also sample the prepare's peak working set every 60 s (K7-D missed it).
  - **Reads:**
    - `demo_combined_kisiwa.py check`: KIS-3 (with `max_diff_l`), KIS-4 and KIS-9 including (e). Every row must pass.
    - §9m.5's freeze and evaluate assertions, and the verdict as computed.
    - Seconds per day, the wall time and the exit code.
  - **Afterwards:** keep the database and work folder until the coordinator confirms K5's captures no longer need them, then `drop`. The K7-F data are a superset of K7-D's, so K5 can capture from them.
- **K7-F size: 0.5 → 0.65** (range 0.6–0.75):
  - the second scratch prepare runs about 70 min, not 45, so +0.1;
  - `EXPECTED_SECONDS`, KIS-3 evidence and the branch merges, +0.05.

  **S-11's K7-F ceiling becomes 0.8.** The increase is reported, not absorbed: **Kisiwa total +0.15.**

### 9o.5 Critical path against the 9.75 tripwire

- R3k2's **9.0**, with K7-F 0.5 → 0.65, gives **about 9.15 lane-units**: spent 3.65 → K4a 1.6 → K6a 0.6 → K6b 1.4 → K7-F 0.65 → K8 captures 0.25 → K9 1.0.
- **Headroom: about 0.6. No cut, and no owner question.** The cut candidates in §9m.6 stay named if a later stop eats the headroom.
- K7-D's review runs beside K7-F's build. It joins the path only if a K7-D fix round outlasts K7-F's build and scratch prepare, which take about 0.65 together.
- K9's rehearsal grows by about 0.5–0.85 h of machine time, outside lane-units. **Demo date:** about +0.1 working day on R3m's +3.4, so about **+3.5** (range 3.0–5.5).
- **Plan HTML rows (coordinator):**
  - K7 becomes 2.55, with "K7-D 1.9, K7-F 0.65".
  - The E3 row becomes "Kisiwa build measured 3568 s (about 353 s per day); four-Site E3 ≈ 2.0–2.35 h of the 3 h cap".
  - The machine-time note becomes "K7-F scratch about 70 min; rehearsal about 2.0–2.35 h".
  - The rulings table gains "DIESEL-1-R3n: E3 restated from measured Kisiwa days (2.0–2.35 h, fits the 3 h cap); KOBO-001 lines in a Kisiwa-only scratch expected, no skip; KIS-3 prints `max_diff_l`; K7-F from K7-D, one merge carrying both; K7-F 0.65; path about 9.15".

### 9o.6 Owner questions

None. For the owner's information, in plain words: each Kisiwa example day takes about twice as long to prepare as we estimated, about 6 minutes instead of 3. Preparing the full four-Site demo should now take about 2 to 2⅓ hours, still inside the 3-hour limit you set, with at least 40 minutes to spare. The full practice run will confirm the figure first. If that run takes more than 2½ hours, we will look at it again before the real one. If it ever needs more than 3 hours, we will ask you rather than raise the limit. The work grows by about 0.15 unit, and the demo date moves by about a tenth of a working day.

---

## 9j3. Ruling DIESEL-1-R3j3: K4b review FIX, H1 (two untracked fuel tables on stored routes) and L1–L3

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. READ on main at `58e401900` (K3, K4a, K6a, K6b, K5 merged) and on `task/DIESEL-K4b-protect-fuel` at `9331a094e` (review `.agent/review-K4b.md`). Read: migrations 0047, 0050–0057; `config/chain/watermark-inputs-v1.json`; `config/chain/stored-composer-modules-v1.json`; `tools/chain_watermark_guard.py`; `backend/tests/test_ch5c_watermark_postgres.py`; every `responses.serve` caller; every backend reader of `fuel_balance_window`, `fuel_residual_consequence_revision` and `operational_record`. Nothing was run.
- **This ruling amends §9j.13 and §9j2.6 (K4b's approved files) and §9j2.5 item 1, which approved the store injection without naming watermark coverage. That was an Architect miss in R3j2, recorded as D3 (structural oversight).** Everything not named here stands.
- **H1 is confirmed. Its fix is required before K4b merges.** No exemption: these tables change the stored board, summary and Portfolio bodies, and the guard contract has no exemption path except the store's own tables.

### 9j3.1 The fix: migration `0058_fuel_watermark_inputs`

**Is the gap already covered by Finding triggers? (READ)**
- `finding` and `finding_revision` are in 0047's `INPUT_TABLES` and carry the four `_cic_` triggers.
- **`fuel_residual_consequence_revision`: covered by accident, not by contract.** Its only writer is `fuel_residual_append` (`financials/adapters/postgres_consequence_store.py:405`). The raise calls it from `fuel_balance/findings_service.py:89-91` on the raise's connection, in the same transaction as `fuel_apply`'s `finding_revision` insert. So today every consequence row commits together with a `finding_revision` row, and that moves `W` for the Site. This holds only while there is one writer that shares the transaction. A later re-price or backfill would break it silently. The W6 guard reads `pg_trigger`, not co-commit habits, so it would still report the table `untracked`. **It gets its own triggers.**
- **`fuel_balance_window`: not covered.** K3's assess writes windows in their own transactions (0055: not a chain-event producer, no outbox, and no Finding or assessment write). The K4a raise reads the window later, in a separate transaction. A WITHIN_MARGIN, BELOW_MATERIALITY, EXCESS or NOT_ASSESSED night, or a Site's first window, never touches a tracked table. Even an UNEXPLAINED night leaves stale bodies between the K3 commit and the raise commit. **It needs triggers.**

**New file `backend/migrations/versions/0058_fuel_watermark_inputs.py`** (0058 is free on main, in K4b, and in K7-F):
- `revision = "0058_fuel_watermark_inputs"`, `down_revision = "0057_fuel_verification"`.
- The docstring says this migration extends the CH-5c W2 change log to the two fuel tables that the stored board, summary and Portfolio read since K4b (DIESEL-1-R3j3). The tables are append-only (`ledger_append_only`), so in practice only the INSERT trigger fires. All four are created because the W6 guard requires them.
- `INPUT_TABLES = ("fuel_balance_window", "fuel_residual_consequence_revision")`
- **Reuse 0047's generator. Do not copy it.** Load `0047_chain_response.py` through `importlib.util.spec_from_file_location("_m0047_chain_response", Path(__file__).with_name("0047_chain_response.py"))`, exactly as 0048 loads 0029 (`0048_daylight_enqueue.py:29-35`).
- `upgrade()`: for each table, `cols = _M._columns(bind, table)`. Raise `RuntimeError(f"watermark input table {table!r} does not exist")` when the table is empty. Then:
  - `tenant = _M._TENANT_COLUMN.get(table, "tenant_id" if "tenant_id" in cols else None)`
  - `site = _M._SITE_COLUMN.get(table, "site_id" if "site_id" in cols else None)`
  - `op.execute(_M._trigger_sql(table, tenant, site))`

  Both tables carry `tenant_id` and `site_id`, so the change rows are Site-scoped. A Kisiwa window write does not move Kobo's board watermark. It does move the estate summary and Portfolio, which is correct.
- **Created objects:** functions `chain_input_change_fuel_balance_window()` and `chain_input_change_fuel_residual_consequence_revision()`, plus the triggers `<table>_cic_ins`, `_cic_upd`, `_cic_del` and `_cic_trunc` on each table. Every name is under 63 characters.
- `downgrade()`, for each table in reverse order: `DROP TRIGGER IF EXISTS <table>_cic_trunc|_cic_del|_cic_upd|_cic_ins ON <table>`, then `DROP FUNCTION IF EXISTS chain_input_change_<table>()`. `chain_input_change` rows already written stay, because the log is append-only. That is the safe direction.
- **No backfill row.** The new alembic head changes `code_version` (the `file_code_version` head hash). Every stored body is therefore rebuilt once after the upgrade, and the demo's prebuild runs after prepare.
- **0047 is not edited.** It is an applied migration, and its frozen tuple stays as it is.

**Config:** `config/chain/watermark-inputs-v1.json` `tables` gains `"fuel_balance_window"` and `"fuel_residual_consequence_revision"`, in alphabetical position: after `"foundation_revision"` and before `"ingestion_batch"`. No other byte changes. `version` stays `watermark-inputs-v1`: the change adds coverage only, and over-invalidation is the safe direction.

**Tests (in `backend/tests/test_ch5c_watermark_postgres.py`, `assetops_k4b_test` only):**
1. Add `_migration_0058_tables()`, the same loader pattern as `_migration_tables()`. `test_declared_inputs_equal_the_frozen_migration_list` becomes `set(declared) - {"chain_action"} == set(_migration_tables()) | set(_migration_0058_tables())`. This must fail if either JSON line is removed, or if 0058 lists a table the JSON does not.
2. `test_every_declared_input_has_the_four_change_triggers` checks `_migration_tables() + _migration_0058_tables()`. This must fail if 0058's `upgrade` is skipped for either table.
3. **New `test_fuel_window_insert_flips_only_its_site(engine)`:** insert one `fuel_balance_window` row for Site A, using the existing real-table helpers' tenant, Site and asset setup or the K4a Postgres fixture pattern; the builder picks whichever is smaller. Then `read_watermark(A)` changes and `read_watermark(B)` does not. This must fail if the trigger is dropped. The consequence table is covered by test 2. Its insert needs the full Finding chain (FKs to `finding`, `finding_revision`, `fuel_balance_window`), which K4a's Postgres tests already exercise.

**Guard CLI evidence (W6), in the packet:**
- **Required in the fix round,** only if the coordinator names a kept, Kobo-bearing prepared `*_test` database and its work folder. Clone it to a producer scratch database `assetops_k4b_audit_guard` (`CREATE DATABASE … TEMPLATE …`, with no open connections to the template). Upgrade the clone to head at the K4b fix commit, then run:

  `python tools/chain_watermark_guard.py --database-url <clone> --work <work dir> --out var/k4b-guard.json`

  The packet quotes the printed summary line. Acceptance:
  - `untracked []` and `unresolved []`;
  - `fuel_balance_window` appears in `all.read` (it proves the Kobo `has_windows` path was listened to);
  - `unlisted_modules []`;
  - exit 0.

  Drop the clone afterwards.
- **If no such database is kept,** do not run a prepare (about 1 h) only for this evidence. Tests 1–3 are the contract, because the guard's `untracked` predicate is the same `pg_trigger` four-event check as test 2. **The CLI then moves to K9's rehearsal** (four-Site prepare, with a Kisiwa fuel Finding present, so `_fuel_findings` also reads the consequence table). K9's packet gets the same acceptance as above, plus `fuel_residual_consequence_revision` in `all.read`. The K9 card gains the line: "W6 guard CLI on the rehearsal database: `untracked []`, both fuel tables read (R3j3)".
- Either way, add **one row to the after-the-demo list**: "F4 checks modules, not tables: add a table-level W6 check to a Postgres test so a new stored read of an untriggered table fails in CI, not only in the CLI".

### 9j3.2 Scope across merged units: the gap is K4b's alone (READ)

The stored routes are exactly the `responses.serve` callers:
- `outcome_api.py:220` (board) and `:252` (outcome summary);
- `estate_portfolio_api.py:75` (Portfolio);
- `estate_api.py:64` (Findings index);
- `chain_api.py:165` and `:308` (the chain and "Why?" routes).

None of them reads a fuel table on main:

| Merged surface | Fuel table read | Stored composer? | Gap on main? |
|---|---|---|---|
| K3 `fuel_balance_window` (0055) | The table itself. Writers: K3 assess, K4a raise | Written only, never read by a stored route on main | No |
| K4a raise and `fuel_residual_consequence_revision` (0056) | Writes. `analytics/adapters/postgres_finding_store.py:740` and `actions/adapters/postgres_action_store.py:812` read only `finding_revision.claim->>'fuel_balance_window_id'` (JSON text, not the table) | Those modules are listed, but the reads are claim JSON on tracked tables | No |
| K5 Fuel page nights, night detail, fuel Finding list and page (`fuel_balance_api.py:98-142`) | `fuel_balance_window`, consequence, K2 records | **No.** Plain `served(...)`, with no `ResponseStore` | No |
| K6b verdict page (`action_api.py:322`, `actions/verification.py`, `fuel_verification.py`) | `fuel_balance_window` (night choice), `operational_record` (site visits through `case_operational_records`) | **No.** `action_api` never calls `responses.serve` | No |
| K6b board entry (`FuelVerdictFact`, `mini.py:458`, `site_chain.fuel_verdict_actions`) | Chain snapshot rows from `domain_action` and `verification_*`, all tracked | Yes, stored | No (tracked tables only) |
| K2 fuel records on `operational_record` (0054) | `work/adapters/postgres_fuel_records.py`, `postgres_global_read.py` | Read by work detail, the verdict page and K5 night detail. None of them is stored | No. **Residual:** `operational_record` is untracked. Any future stored read of it needs the same treatment |

- K4b's own board binding reads `site` and `asset` (`night_context`), and `finding` and `finding_revision` (`_fuel_findings`). All of these are tracked. The two fuel tables are the only untracked reads. K4b does **not** bind `night_records_and_provenance` (K2 records) into the board, so `operational_record` stays off stored routes.
- **Conclusion:** the gap opens with K4b's injection (§9j2.5 item 1). It is not a pre-existing hole, and no merged unit needs a fix.

### 9j3.3 Who does it, and the order with K7-F

- **K4b's fix round does it,** on `task/DIESEL-K4b-protect-fuel`, with a Sonnet builder (fix-round rule). There is no separate unit: the gap is K4b's alone, and the migration is what makes K4b's reads lawful.
- **Re-review:** a fresh Claude reviewer checks H1 and L1–L3 only, plus the 0058 file and the JSON diff. Merge on ACCEPT.
- **Order with K7-F: independent, either may merge first.** Whichever merges second runs `git merge main` first. Never rebase. K7-F adds no migration, so there is no number clash, and neither branch touches the other's files.
- **K7-F's scratch database without the triggers does not matter:**
  - On K7-F's tree no stored route reads a fuel table, because K4b's board binding is absent. Its stored bodies are therefore correct without them, and none of its KIS evidence depends on the change log.
  - `demo_combined.py prepare` drops, recreates and upgrades to head. The first database built on a main holding both K4b and K7-F carries 0058, and its K7 backdated writes then log change rows. The watermark is a count, not a time, so a backdated write still expires the historical (`known_at`) bodies. That closes the reviewer's K7 concern.
  - **No K7-F scratch re-run** and no edit to K7-F.
  - The extra cost per prepared window write is one statement-level insert into `chain_input_change`, which is negligible against the measured 353 s per day.
- **Test template:** the new head makes the `pg_harness` templates stale. They rebuild once at the first Postgres test run, at about the cost of minutes. This is expected and not a defect.

### 9j3.4 K4b's Lows: all three in the same round

- **L1, fix.** In `read.py` `mini_ports` → `fuel_findings`: `_tank, k = fuel_context()` and pass `k` (not `known_at`) to `.fuel_findings(t, sid, lo, hi, k)`. Now one board reads the window, applicability and Finding at one cutoff (§9j.11 "as known at the board cutoff"). Stored and historical composes are unchanged, because `k == known_at` when `known_at` is given.
  - L0 test in `test_k4b_protect_fuel.py`: with `known_at=None`, a fake store records the instant that `has_windows`, `windows` and `fuel_findings` receive. All three are equal to `night_context`'s instant. This must fail if `fuel_findings` reverts to `known_at`.
- **L2, fix (one token, safe direction).** In `mini.py` `_fuel_findings`: `no_close = policy is None or tuple(policy.measures_for(FUEL_MECHANISM)) == ()`.
  - With no policy (a failed `chain_threads` read, or `thread_policy` not injected), a fuel Finding never shows a countdown. The fuel mechanism's lifecycle is declared empty in configuration (§9j2.3 item 2), so "unknown policy" can only mean "no countdown we can stand behind".
  - L0 test: a fuel `FindingFact` composed with `policy=None` carries `close_measured: False`. This must fail on the old `policy is not None and …` form.
  - Dispatch, Cold and EV views are unchanged (still no key).
- **L3, fix.** Restore the space at `mini.py:504`: `plan_facts = tuple(...)`.

### 9j3.5 Approved files (added to §9j.13 and §9j2.6)

- `backend/migrations/versions/0058_fuel_watermark_inputs.py` (new)
- `config/chain/watermark-inputs-v1.json` (two lines)
- `backend/tests/test_ch5c_watermark_postgres.py` (tests 1–3 of §9j3.1)
- `B/site_outcomes/read.py` and `mini.py` (already approved: L1–L3), and `backend/tests/test_k4b_protect_fuel.py` (L1 and L2 tests)
- `.agent/review-packet-K4b.md` (a fix-round section, plus the guard CLI line or the note "CLI moved to K9 (R3j3)")

**New stops:**
- **S-g:** `_trigger_sql` from 0047 cannot be reused unchanged (signature or behaviour). Report it; do not copy or fork the generator.
- **S-h:** the guard CLI, when run, reports any `untracked` or `unresolved` table other than these two, or any `non_200`. Report it with the JSON; do not fix outside these files.

**Focused runs only:**
- `test_ch5c_watermark_postgres.py` and `test_k4b_protect_fuel.py`;
- the L0 files the review listed for `mini.py` and `read.py` (`test_ch5a1_board_contract.py`, `test_ch5a2_contract.py`, `test_ch2_threads.py`, `test_pv1_value_lines.py`);
- `test_out_b4_board_postgres.py -k kobo`.

No full suite.

### 9j3.6 Size and critical path

- **K4b: 1.1 → 1.25** (range 1.2–1.3). That is +0.15:
  - migration and JSON 0.04;
  - the three watermark tests 0.04;
  - L1 and L2 with their tests, plus L3, 0.03;
  - the guard CLI clone run or the K9 note 0.02;
  - re-review 0.02.

  This is inside stop S-e's ceiling of 1.3. The increase is reported, not absorbed: **Kisiwa total +0.15.** If K9 takes over the CLI, K9 absorbs it inside its 1.0, because the guard is about 10 min on the already-built rehearsal database.
- **Critical path: about 9.15, unchanged. Headroom to the 9.75 tripwire: about 0.6.** The path is spent 3.65 → K4a 1.6 → K6a 0.6 → K6b 1.4 → K7-F 0.65 → K8 captures 0.25 → K9 1.0.
  - K4b's fix round (about 0.15) runs beside K7-F's remaining review and merge, and K8 waits for both.
  - K4b joins the path only if its fix round and re-review outlast K7-F's merge. Then the path grows by at most the overlap, which is ≤ 0.15, giving ≤ 9.3, still about 0.45 under the tripwire.
- No cut, and the demo date does not move.
- **Plan HTML rows (coordinator):** K4b becomes 1.25. The rulings table gains "DIESEL-1-R3j3: 0058 adds W2 change triggers on `fuel_balance_window` and `fuel_residual_consequence_revision` (watermark-inputs +2); gap is K4b's alone (no merged stored route reads fuel tables); K4b fix round, independent of K7-F's merge; L1 one cutoff, L2 no countdown without a policy, L3 whitespace; K4b 1.25".

### 9j3.7 Owner questions

None. For the owner's information, in plain words: some pages are saved after they are first built, so they open quickly. A saved page is rebuilt when the data behind it changes. The new Protect fuel line reads two fuel records the system was not yet watching for changes, so a saved page could have kept showing an old fuel status. This fix makes the system watch both records. Any new fuel check now refreshes the saved pages straight away, including the ones for earlier days. It also tidies three small points. The work grows by about 0.15 unit and does not move the demo date.

---

## 9p. Ruling DIESEL-1-R3p — K8 consolidated card (four Sites on the estate screens, the fuel Finding in the estate lists, re-expectations, captures)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). READ on main at `3bfbff43e` (K4b with R3j3 0058 and K7-F merged). Read: `estate/index.py`, `estate/coverage.py`, `estate/portfolio.py`, `estate/placement.py`, `estate/financials.py:407-435`, `estate/money_invariants.py`, `estate/composition.py`, `estate/adapters/postgres_estate_read.py`, `fuel_balance/adapters/postgres_fuel_balance_store.py:200-335`, `chain/claims.py`, `chain/threads.py:31,111-126`, `site_outcomes/read.py:640-870`, `site_outcomes/mini.py:811-846`, `evidence/overview.py`, `evidence_api.py:393-409`, `config/chain/stored-composer-modules-v1.json`, `tools/checks/chain_coherence.py` (COH-0..13 and helpers), `tools/demo_combined_finish.py` (CO-6, CH5D1-O1, F-COH, `run`), `tools/demo_combined_rows.py` (`optimize_card`, `kis8_protect`), both Kobo and Kisiwa templates, `frontend/src/sites/SiteWindowOverview.tsx`, `MiniPerformance.tsx`, `shell/SiteDetailFrame.tsx`, `estate/findingIndex.tsx`, `EstatePortfolio.tsx`. Nothing was run.
- **This card supersedes every scattered K8 line** (§8.4 K8 row, §3.4 D4, §9j.14, §9l.4, §9m.5, §9j2.5 item 3, §9o.1's last bullet, §9c.4). Where they disagree, this card wins. D4's Assure value line stays removed (H2).

### 9p.1 Code reality that decides the card (READ)

1. **The fuel Finding is in no estate list on main.** `EstateSnapshot.finding_index` (`postgres_estate_read.py:163-164`) reads only the dispatch domain, and `coverage._mini_grid_basis` builds rows only from it. `select_finding_scope` therefore never emits a fuel row, so the estate Findings index, the Portfolio rows, `summary.category_counts`, `placement_counts`, `finding_count`, the Findings lens chips and the thread columns all omit it.
2. **R3j2 item 3 is unmet on main.** Its "Kisiwa Protect `open_findings` +1 via `portfolio.py:297 category_counts`" does not happen, because `category_counts` runs over `select_finding_scope` members. Two clarifications:
   - `summary.category_counts` is a wire field. No client screen renders it today (the only frontend reference is the type at `estateClient.ts:465`), and `demo_combined_after.py:286` reads only GROW.
   - The Portfolio **Protect card's value** is `count.sites_disrupted` (`read.py:859`), which correctly excludes fuel (R3j2 item 4). It is not meant to rise, and it does not.
   - **This round fixes item 3** by putting the fuel row into `select_finding_scope` (§9p.2).
3. **Money is separate by construction.** Estate money comes only from `select_financial_scope` (`financials.py:407`). That calls `site_coverage` → `_mini_grid` → `finding_index` itself, independently of `select_finding_scope`. `double_count_violations` reads only `selected_lines` and money `groups`. **So a join placed in `select_finding_scope`, after coverage, can never reach a money line, a group, `estate_total`, `combined_value` or Financials.** A join placed in `site_coverage`, `_mini_grid` or `finding_index` would reach them all. That is the whole design constraint.
4. **The W6 module list already has the fuel store** (`fuel_balance.adapters.postgres_fuel_balance_store`, listed). It does **not** have `actions.verification_rules` (`parse_exact`, called by `to_window`) or `fuel_balance.finding_text` (`litres1`, `money`, `short_day`). K4b's stored board already runs both whenever a fuel Finding is present, so K9's guard CLI would report them in `unlisted_modules`. That is a K4b gap the Kobo-only evidence could not show. K8 closes it (§9p.2 item 7).
5. **`SERVICE_FEEDERS` is not served for Kisiwa.** `GET /api/sites/{id}/overview` returns `site_overview.serve(...)` (the selected-day window summary) for an imported Site (`evidence_api.py:394-397`). The legacy `OverviewReadModel` and its `SERVICE_FEEDERS` cards are reached only for a non-imported Site. Kisiwa is imported (K1), so no Kisiwa screen shows "Clinic feeder" from that source.
6. **The two UI strings are on Kisiwa's screens.** `MINIGRID_OBJECTIVE` renders on every mini Site's Overview (`SiteWindowOverview.tsx:487-492`). `CLINIC_FEEDER_LABEL` renders for the CRITICAL row of the Service page (`MiniPerformance.tsx:974`). Kisiwa's cold store is declared `ESSENTIAL_SERVICE` (`demo_combined_kisiwa.py:62`), so it is Kisiwa's CRITICAL row. Kisiwa's Foundation loads are "Households", "Cold store (ice and fish)" and "Water pump" (`kisiwa-diesel-hybrid-60kw.yaml:156-172`). Its devices are still named `clinic-meter` and `mill-meter`.
7. **Estate rows match only W1 Actions.** `_action_for` matches `select_action_scope` rows: the W1 `action` table, mini only. The fuel Action is a `FUEL_BALANCE` domain Action, so a fuel row would read "No action agreed yet" next to a verified fix. Cold and EV rows have the same pre-existing gap, and it stays out of scope. For the fuel row it would contradict the Kisiwa board on the demo's main beat, so K8 corrects it for fuel rows only (§9p.2 item 5).
8. **COH rows and Kisiwa.** `chain_coherence.day_windows` collects boards only for `SITE_CODE` (three Sites), so COH-3/4(board)/5/10(board)/13 never see a Kisiwa board. The estate-level rules do see Kisiwa: COH-1 (links in Portfolio and Findings bodies), COH-4 (Portfolio ⊂ Findings) and COH-7a (summary Site windows). COH-7a's zone lookup (`chain_coherence.py:646`) has no Kisiwa zone, so Kisiwa's local-day window would be compared with a zone-less day.

### 9p.2 Q1: the estate fuel Finding entry (exact design)

1. **Store (`B/fuel_balance/adapters/postgres_fuel_balance_store.py`).** Add a connection-taking public method with the same contract as `fuel_findings`:
   ```python
   def fuel_findings_on(self, c: Connection, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                        known_at: datetime | None) -> tuple[FuelFinding, ...]:
       """DIESEL-1-R3p: `fuel_findings` on the caller's read-only connection (the estate snapshot); same refusal,
       same filter and order. Opens no transaction."""
   ```
   - It holds the existing validation and filter body.
   - `fuel_findings` becomes `return self._read(lambda c: self.fuel_findings_on(c, tenant_id, site_id, lo, hi, known_at))`.
   - Behaviour is byte-identical. The K4b and K5 tests stay green unchanged.
2. **Estate reader (`B/estate/adapters/postgres_estate_read.py`).**
   - `PostgresEstateRead.__init__` gains `fuel: Any = None` as the **last** keyword, stored as `self.fuel`, with the comment `# DIESEL-1-R3p: PostgresFuelBalanceStore (fuel_findings_on on this connection); None = no fuel rows`.
   - `dispose()` also calls `self.fuel.dispose()` when it is not None.
   - `EstateSnapshot` gains `fuel_findings(t, s, from_, to, k) -> list[dict]`:
     - `[]` when `self._o.fuel is None`;
     - else `self._o.fuel.fuel_findings_on(self._c, t, s, from_, to, k)`, plus **one** batched `SELECT finding_revision_id, evidence_id FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s AND finding_revision_id = ANY(CAST(:ids AS uuid[]))` on `self._c`;
     - each item is `{"finding": <FuelFinding>, "evidence_ids": sorted ids}`.
   - No new transaction and no write. `configuration-persistence.ps1` `$pgReaders` is unchanged, because no new driver import is added.
3. **Composition (`B/estate/composition.py`).**
   - `build_estate_read` builds `fuel = build_fuel_balance_store(database_url)` with a **function-local** import from `assetops_backend.fuel_balance.composition` (the site_outcomes pattern, which avoids the `work.composition` cycle), and passes `fuel=fuel`.
   - `build_estate_evidence_service`'s `keys` tuple gains `"fuel"` (last), so the Portfolio and Evidence reader carries it.
4. **The join (`B/estate/index.py`, `select_finding_scope`; no new module).** After the per-Site `for r in cov["rows"]` loop, for each Site with `domain == MINI_GRID` and `cov["state"] in (CURRENT, HISTORICAL, PARTIAL)` (the same gate as mini rows, "reading 6"):
   - `rows += _fuel_rows(snap, site, cov, req, scope["k"])`.
   - Read via `getattr(snap, "fuel_findings", None)`. A snapshot without it (test fakes) gives no fuel rows and no error.
   - Header comment at `_fuel_rows`: `# DIESEL-1-R3p, MOCK DEVIATION MD-FUEL-K4-1: the unexplained-fuel Finding joins the estate Finding rows here, after coverage and outside site_coverage/_mini_grid, so it never reaches select_financial_scope, selected_lines, money groups, estate_total or double_count_violations. Its money is its own fuel-residual-1 row, shown on its own and never added.`
   - Candidates: `snap.fuel_findings(tenant_id, site["site_id"], req.from_, req.to, scope["k"])`. These are the latest revision as known at `k` whose cited night window intersects `[from, to)`, every lifecycle. That is the same window rule as K4b's board `fuel_findings(work_lo, end)`, so COH-4's board half agrees once K9 collects Kisiwa boards.
   - **Row fields.** Every key a mini row has, in the same order, so the Findings and Portfolio wires are unchanged in shape. With `f = item["finding"]`, `fid = str(f.finding_id)`, `frid = str(f.revision_id)`:
     - `"finding_id": fid`, `"finding_revision_id": frid`, `"site_id"`, `"site_code"` and `"site_name"` as mini;
     - `"finding_label": finding_label(fuel_text.TITLE)`, `"title": fuel_text.TITLE` ("Unexplained fuel overnight"; import `assetops_backend.fuel_balance.finding_text as fuel_text`);
     - `"priority": None`, `"confidence": None`, `"confidence_reasons": []`;
     - `"lifecycle": str(f.lifecycle)`;
     - `"lens_flags": lens_flags(finding_signal_key("UNEXPLAINED_FUEL"), MINI_GRID)`, which gives `["RISK"]`;
     - `"categories": categories_for(finding_signal_key("UNEXPLAINED_FUEL"), MINI_GRID)`, which gives MAPPED, Protect, MOVES `MG-8`. These are the `outcome_roles` entries R3j2 added, so `category_counts` counts it under `PROTECT_ASSET`;
     - `"consequence"`: §9p.2 item 6;
     - `"source_provenance": snap.finding_provenance(tenant_id, site["site_id"], frid, item["evidence_ids"])`;
     - `"episode_start": wire_time(f.window.window_start)`, `"status": cov["state"]`;
     - `**_links({"finding": refs.fuel_finding_ref(code, fid), "site": site_home_ref(code, MINI_GRID)})`, the K5 page with no revision, as the board links it;
     - private keys: `"_at": f.window.window_start`, `"_site": site`, `"_domain": site["site_type"]`, `"_episode_end": f.window.window_end`, `"_mechanism": "UNEXPLAINED_FUEL"`, `"_recurs_after": None`, `"_recurs_after_title": None`, `"_transition": None`, `"_revision_no": f.revision_no`.
   - **Not touched:** `cov` (no array, token or selection id gains fuel ids), `cutoffs`, and the Site coverage state. The selection token does not cover fuel rows; that goes on the after-the-demo list (§9p.10).
5. **Portfolio Action column for fuel rows only (`B/estate/portfolio.py`, `B/estate/placement.py`).**
   - `placement.place` gains a last keyword `label: str | None = None`. When it is given, it replaces `workflow_label(action)`. The default keeps every existing caller byte-equal.
   - `portfolio.py` gains:
     ```python
     #: DIESEL-1-R3p: a fuel row's Action is a FUEL_BALANCE domain Action, which `_action_for` cannot see; its column
     #: reads its thread state with the existing workflow words. Cold and EV rows are unchanged.
     FUEL_THREAD_LABEL = {"RESOLVED_MONITORING": "Verified", "CLOSED": "Verified", "CHANGE_APPLIED": "Applied",
                          "ACTION_IN_HAND": "Pending"}
     ```
   - In `portfolio_row`, when `r["_mechanism"] == "UNEXPLAINED_FUEL"`, compute `label = FUEL_THREAD_LABEL.get(((r.get("_thread") or {}).get("state")), "No action agreed yet")`. Pass it to `place(..., label=label)` and use it as `"workflow_label"`. `action_*` stay None.
   - For every other row, `label` is None and nothing changes.
6. **Consequence block (fuel `fuel-residual-1`, own basis).** Let `q = f.consequence` (the stored row, or None), and let `live` mean `cov["state"] == CURRENT` (not HISTORICAL and not PARTIAL: the mini rule "a prior or partly checked amount is never current money").
   - `q is None`: `{"state": "UNPRICED", "amount": None, "amount_low": None, "amount_high": None, "currency": None, "source_revision_id": None, "basis": "UNEXPLAINED_FUEL_AT_DECLARED_PRICE"}`. The client words are "No consequence recorded".
   - `q["state"] == "UNPRICED"`: the same, with `source_revision_id = q["id"]`. The client words are "Unpriced".
   - `q["state"] == "PRICED"` and **not** `live`: `state "UNKNOWN"`, no amounts, `source_revision_id = q["id"]`. The client words are "Historical as of …" or "Partly checked · …".
   - `q["state"] == "PRICED"` and `live`: `state "PRICED"`, with `amount_low = amount = fuel_text.money(q["amount_low"])`, `amount_high = fuel_text.money(q["amount_high"])` (the same two-place text as K4b's Protect line), `currency = q["currency"]` and `source_revision_id = q["id"]`.
   - `basis` is the literal `"UNEXPLAINED_FUEL_AT_DECLARED_PRICE"` with the comment `# equals the stored fuel_residual_consequence_revision.basis and site_outcomes/mini.py FUEL_BASIS`. A test asserts the equality. It is additive, and only fuel rows carry it.
   - **Placement** follows from the existing rules, and `placement.py` gets no `_UNPRICED_REASON` entry:
     - priced and no thread work: rule 4, `COMPARE_VALUE` `PRICED_SINGLE` ("Priced cost exposure; no like line to compare with"). That is true, because the fuel row has no money line, so `line_group` is None;
     - unpriced: rule 5, `UNPRICED_OTHER` ("No price basis for this finding");
     - thread verified: rule 3, `MONITOR` `VERIFIED_WATCH_RETURN` with `provenance_suffix(None)`.
   - **Fuel money joins no estate money total.** It is never in `select_financial_scope`, `selected_lines`, `money.groups`, `money.estate_total`, `summary.combined_value`, `value_cards`, `footer`, Financials or any sum. It appears only as the row's own interval, beside K4b's own Protect line.
7. **W6 stored-route coverage.**
   - The estate Findings index (`estate_api.py:64`) and the Portfolio (`estate_portfolio_api.py:75`) are stored routes. They now read `finding`, `finding_revision`, `finding_revision_evidence`, `fuel_balance_window` and `fuel_residual_consequence_revision`. All of these are triggered: 0047, plus 0058 for the two fuel tables. **No migration.**
   - **No new reader module is created:** the join lives in `estate/index.py` and the snapshot method in the listed estate adapter.
   - `config/chain/stored-composer-modules-v1.json` gains **two** modules, in alphabetical position: `"assetops_backend.actions.verification_rules"` (after `"assetops_backend.actions.verification"`) and `"assetops_backend.fuel_balance.finding_text"` (after `"assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store"`; builder: keep the file's existing sort rule, whichever `test_module_list_is_recorded_and_resolves` enforces). Both are clock-free (READ). `test_ch5c2_clock_guard.py` must stay green unchanged.
   - K9's guard CLI acceptance (R3j3) then covers the estate routes too.

### 9p.3 Q2: the Assure count. Confirmed, with the window condition stated

- `count.verified_results` counts a thread in `VERIFIED_CLASS` (`RESOLVED_MONITORING`, `CLOSED`; `threads.py:113`) whose **Finding occurrence episode meets `[lo, hi)`** (`claims._finding_threads`), read at `LATEST_KNOWN` under the request cutoff. The fuel thread after K6b's VERIFIED is `RESOLVED_MONITORING`, so it counts **on windows that contain night 4's window** (the story week). **It does not count on the S-only window.** That is correct, not a defect. No product code changes.
- **K8 adds one L0 test** in `backend/tests/test_k8_estate_fuel.py`, through `estate_count_claims` with a fake `req`. Cases:
  - a `UNEXPLAINED_FUEL` thread at `RESOLVED_MONITORING` with a Finding occurrence inside `[lo, hi)` gives verified +1 and is absent from `disrupted`;
  - the same thread with the occurrence outside the window adds 0;
  - the test must fail if `VERIFIED_CLASS` loses `RESOLVED_MONITORING`.
- **The finish expectation is K9's** (it needs the four-Site run). K9's KIS-6 gains: on the week window, `/api/estate/chain` `sites` entry for `KISIWA-001` has `threads.verified == 1`, and the Portfolio Assure card `claim.value` equals the chain `count.verified_results`. Both are read from data. **No Assure value line (H2).**

### 9p.4 Q3: Kisiwa objectives. None for the demo (confirmed)

- Kisiwa shows the honest "no target" state. `objective_site_count` stays **3**, CO-6's `== 3` stays, and the Assure card detail reads the targets at 3 Sites, which is true.
- Declaring one would add stored objective data, a board and estate re-expectation, and captures for no demo beat. Not demo-critical (owner 2026-11-05). After-the-demo list: "Kisiwa operating objectives (for example, cold store supply kept)".

### 9p.5 Q4: device-id copy

**Shared rule R-LOAD:** a Site whose declared load names include a clinic or health load (`/clinic|health/i`) keeps v69's Kobo words. Any other Site's words are built from its own load names. **Kobo bytes do not change.** Kobo's Foundation names "Health clinic" (`kobo-mini-grid-60kw.yaml:195`), and the existing CRITICAL test fixture "Health post" matches as well, so its expectations stay byte-equal. **MOCK DEVIATION MD-KIS-K1-1** (already logged) covers the Kisiwa words, with a header comment at each helper.

1. **`evidence/overview.py` `SERVICE_FEEDERS`: no change.** It is not served for an imported Site (§9p.1 item 5).
   - **Pre-flight (a):** confirm `site_overview.serve` returns a body for `KISIWA-001`.
   - If it returns None, that is **stop S-5**. Do not add a feeder rule unasked.
   - After-the-demo list: "feeder labels from the Foundation on the legacy overview".
2. **`SiteWindowOverview.tsx` `MINIGRID_OBJECTIVE`: data rule.**
   - `OverviewMiniReads` gains `loadNames?: readonly string[]`: the Site's Foundation `components` with `component_type === "LOAD"`, `display_name` in document order. `SiteDetailFrame.tsx` sets it from the loaded `site` record when it builds `mini`.
   - New exported pure function in `SiteWindowOverview.tsx`:
     ```ts
     /** DIESEL-1-R3p R-LOAD, MOCK DEVIATION MD-KIS-K1-1: the objective names the Site's own loads; a Site with a clinic
      *  or health load keeps v69's words (Kobo byte-equal). */
     export const OBJECTIVE_NO_LOADS = "Objective: serve this site's loads while protecting the battery reserve.";
     export function minigridObjective(loadNames: readonly string[] | undefined): string
     ```
     - `undefined` gives `MINIGRID_OBJECTIVE`, so every existing caller and test is byte-equal.
     - Any name matching `/clinic|health/i` gives `MINIGRID_OBJECTIVE`.
     - `[]` gives `OBJECTIVE_NO_LOADS`.
     - Otherwise it gives `` `Objective: serve ${list} while protecting the battery reserve.` ``, where `list` is the names verbatim joined as "A", "A and B" or "A, B and C" (no serial comma).
   - **Kisiwa literal:** `Objective: serve Households, Cold store (ice and fish) and Water pump while protecting the battery reserve.`
   - `ObjectiveLine` renders `minigridObjective(mini?.loadNames)`.
3. **`MiniPerformance.tsx` `CLINIC_FEEDER_LABEL`: data rule.**
   ```ts
   const feederName = (row: ServiceRow): string =>
     row.role !== "CRITICAL" ? row.load_label
       : /clinic|health/i.test(row.load_label) ? CLINIC_FEEDER_LABEL : `${row.load_label} feeder delivered power`;
   ```
   - It carries an R-LOAD and MD-KIS-K1-1 comment.
   - **Kisiwa literal:** `Cold store (ice and fish) feeder delivered power`.
   - **Pre-flight (b):** confirm Kobo's served CRITICAL `load_label` matches `/clinic|health/i` (from the Kobo mini-depth golden or fixture). If it does not, that is **stop S-6**; never guess.

### 9p.6 Q5: template signal names. Deferred (confirmed)

- "Active power to the clinic" and "Active power to the mill" (`kisiwa-diesel-hybrid-60kw.yaml:312,320`) appear only in signal and evidence tables.
- A v2 template plus a re-import puts the K7 digests and the 3568 s build at risk for no demo beat.
- **Deferred after the demo as part of MD-KIS-K1-1.** After-the-demo list: "Kisiwa template v2: meter signal names to the cold store and water pump, then re-import".
- DS-1 note (for K9's beat): do not open Kisiwa's signal tables in the demo.

### 9p.7 Q6: re-expectations (exact values). K8 edits these rows directly; they are named here

The rule for every row: the core three Sites, plus Kisiwa **iff** the dataset holds Kisiwa. That is read from data, never typed from a run, so a three-Site partial prepare stays green.

1. **CO-6** (`T/demo_combined_finish.py:451`). A new helper is cached on `ctx`, with one `SELECT 1 FROM site WHERE site_code_key = lower(%s)` through the `_kisiwa_read` connection pattern:
   ```python
   def _kisiwa_present(ctx: Ctx) -> bool:
       """DIESEL-1-R3p: whether the dataset holds the Kisiwa Site (cached)."""
   def expected_site_codes(kisiwa: bool) -> list[str]:
       return sorted([KOBO, COLD, EV] + ([KISIWA] if kisiwa else []))
   ```
   - `assert codes == expected_site_codes(_kisiwa_present(ctx)), codes`.
   - `objective_site_count == 3` **stays** (§9p.4).
   - `double_count_violations(body) == []` stays and must still pass with fuel rows present (§9p.2 item 6).
   - The return gains `"kisiwa_present"`.
2. **CH5D1-O1** (`T/demo_combined_finish.py:1165`; A3 L3).
   - `demo_rows.optimize_card(summary, site="KOBO-001", allowed=("KOBO-001",))` gains the `allowed` parameter, and the call passes `allowed=(KOBO, KISIWA)`. The priced codes come from the summary in Site order.
   - Assert `site in codes` and `set(codes) <= set(allowed)`.
   - **Exactly one** (`[KOBO]`): the existing assertions, byte for byte.
   - **Two or more:**
     - `card.value.text == card_text("cost.sites", sites=sites_text(len(codes)))`;
     - `card.claim is None`;
     - `card.detail == " · ".join(card_text("cost.site", site=<site_name or code>, text=claim["text"], small=COST_SMALL[claim["key"].removeprefix("money.")]) for each priced Site in order)`, with imports from `assetops_backend.chain.vocabulary` and wherever `sites_text` lives.
   - It returns `{"text": card.value.text, "priced": codes}`.
   - Whether Kisiwa is priced is read from its board claim, never typed. The no-sum check stays in K9's KIS-6.
   - The docstring cites R3p.
3. **F-COH / COH-1** (`T/checks/fixtures/chain_coherence/screen_routes.json`). Add three App routes, keeping the file `sorted(set(...))`:
   - `"/sites/:siteId/domain-actions/:actionId/fuel-verification"`;
   - `"/sites/:siteId/domain-actions/:actionId/verification"` (the CH-9b3 mill verdict route, which is in `App.tsx` but missing from the file);
   - `"/sites/:siteId/fuel-findings/:findingId"`.

   The two `domain-actions` entries sort after `/sites/:siteId/configuration`, and `fuel-findings` sorts after `/sites/:siteId/foundation/changes/:changeId`.
4. **COH-7a** (`T/checks/chain_coherence.py:646`). Add, below `LOCAL_DAY_TZ`:
   `SUMMARY_SITE_TZ = {"KISIWA-001": "Africa/Dar_es_Salaam"}  # DIESEL-1-R3p: config/operational-actions/kisiwa-001-operational-actions-v1.yaml timezone; Kisiwa boards stay K9's (SITE_CODE)`
   - The lookup becomes `{**{SITE_CODE[k]: z for k, z in LOCAL_DAY_TZ.items()}, **SUMMARY_SITE_TZ}.get(...)`.
   - **Pre-flight (c):** confirm Kisiwa's stored Site timezone is `Africa/Dar_es_Salaam` (K1's Site document). If it is not, that is stop S-10.
5. **COH-10: no change.** It iterates the expected threads only, so an unlisted Kisiwa thread cannot fail it. **K9** adds the Kisiwa fuel thread `{"name": "kisiwa-fuel", "site_code": "KISIWA-001", "mechanism": "UNEXPLAINED_FUEL", "findings": [<night-4 finding id from kisiwa.json>]}` to `build_expected_threads`, together with the board collection.
6. **COH-13 / COH-4 board half (`SITE_CODE`): K9's job.**
   - Extending `SITE_CODE` (and `LOCAL_DAY_TZ` with `"kisiwa": "Africa/Dar_es_Salaam"`) collects Kisiwa boards. That switches on COH-3/4/5/10/13 for Kisiwa. It can only be proven on a four-Site bundle, and it is the same family as COH-17/V4, which K9 owns.
   - COH-4's estate half (Portfolio ⊂ Findings) already includes Kisiwa, and it holds by construction: both come from `select_finding_scope`.
   - K9's card gains: "`SITE_CODE`/`LOCAL_DAY_TZ` + Kisiwa; COH-10 Kisiwa thread; COH-13/COH-4 board half on Kisiwa (R3p)".
7. **Not changed:** `kis8_protect`'s `tally["compared"] == 3` (UF1's check count, not a Site count), CO-6b, CO-8, CO-11 and `_boards` (three-Site by design).

### 9p.8 Q7: the K7-F L3 docs. Yes, inside K8 (doc only, about 0.02)

- `backend/tests/test_demo_combined_postgres.py:3`: "(all three Sites, the shipped day list)" becomes "(all four Sites, the shipped day list)".
- `:9`: "one prepare is about 20-25 min" becomes "one prepare is about 2.0-2.35 h (DIESEL-1-R3n)".
- `backend/TESTING.md:327-328`: "one three-Site `tools/demo_combined.py prepare`, about 20-25 min" becomes "one four-Site `tools/demo_combined.py prepare`, about 2.0-2.35 h (DIESEL-1-R3n)".
- No code or runtime changes.

### 9p.9 Q8: capture data. Ruled (a) + (b); no dedicated four-Site prepare

- **(a) Kisiwa-only captures, inside K8 code.** Clone `assetops_demo3_kisiwa_test` to producer scratch `assetops_k8_audit_kisiwa` (`CREATE DATABASE … TEMPLATE …`, with no open connection to the template). Upgrade the clone to head (0058) at the K8 commit, `serve` it read-only, capture, then drop the clone. **The kept source DB is never written.** Captures at 1440 and 390:
  - the Kisiwa Overview objective line;
  - the Kisiwa Service page with the CRITICAL feeder name;
  - the estate Findings page (all and Risks) showing the Kisiwa fuel row;
  - the Portfolio row group showing the fuel row with "Verified".

  The same clone is the Postgres-backed evidence. In process, against the clone, read `/api/estate/findings` and `/api/estate/portfolio` for the story week and print:
  - the fuel row (consequence and link);
  - `category_counts.PROTECT_ASSET`;
  - `money.groups`/`selected_lines` lengths;
  - `double_count_violations == []`.
- **(b) The four-Site captures are a "K8 capture phase" (0.25) on K9's rehearsal DB.** This avoids a second 2.0–2.35 h heavy job (machine time and the one-heavy-job gate). **§3.5's "then drop the DB" is amended to: keep the rehearsal DB and work folder until the K8 capture phase and K9's guard CLI are done, then drop.** Scope:
  - the four-Site Portfolio, estate Findings (all, Risks), the Sites list and navigation, at 1440 and 390;
  - the all-26 recapture by W1-F5b's procedure (168 pairs as of W1-F5b), plus the Kisiwa pages built since (K5's Fuel night mode and fuel Finding page, K6b's verdict page, Kisiwa board): the regenerated audit index;
  - K4b's Protect line (§9p.11).

  The capture phase is its own small branch, `task/DIESEL-K8c-captures`, from main after the rehearsal. Coordinator capture check, then merge.
- **How K8 code merges before K9 without the four-Site self-check:** on review ACCEPT (W1 rule), with this evidence:
  - (i) the L0 tests of §9p.12, including pass and fail self-tests for every re-expected row, on synthetic bodies;
  - (ii) the Postgres test on `assetops_k8_test`;
  - (iii) the clone evidence of (a).

  The re-expected rows are data rules, so a three-Site dataset must still pass them. The builder proves that with the self-tests' three-Site cases.
- **If a re-expectation is wrong at K9's rehearsal:**
  1. K9 does **not** edit the row. It reports a stop (the §9o.1 pattern) with the row's printed `check.json` entry.
  2. K9 copies `check.json` to `check-rehearsal.json` first.
  3. The Architect rules, and a Sonnet fix round on `task/DIESEL-K8-fix-reexpect` edits only the named row or fixture.
  4. After it merges, `python tools/demo_combined_finish.py check <url> <work>` re-runs on the **kept** rehearsal DB. `run` skips `mutates` rows, so the re-check is read-only. No re-prepare is needed, because read-path code changes rebuild stored bodies through `code_version`.
  5. Only a fix that changes prepared **data** needs a re-prepare. That goes to the Architect, and the owner is told the machine time.
  6. K9's measured rehearsal wall time stands either way.

### 9p.10 After-the-demo list (coordinator)

- estate selection token covers fuel rows;
- estate rows match domain Actions (Cold, EV, fuel), replacing the fuel-only thread label;
- Kisiwa operating objectives;
- feeder labels from the Foundation on the legacy overview;
- Kisiwa template v2 signal names and re-import (MD-KIS-K1-1).

### 9p.11 Q9: the K4b Protect line. Confirmed: capture only

`portfolio_cards` emits `fuel_lines` and `fuel_note` (`read.py:850-865`), and `PortfolioOutcomes.tsx` renders them (K4b, merged). K8 changes neither and captures them in §9p.9 (b). KIS-8a (K4b) and UF1 already guard them.

### 9p.12 Tests (localised; no full suite)

Every "must fail" names the mutation the reviewer applies to a scratch copy.

**Backend L0, new `backend/tests/test_k8_estate_fuel.py`** (fake snapshot with `fuel_findings`, built on the existing estate fake patterns):
1. **Row.** A CURRENT mini Site with one SUPPORTED priced fuel Finding gives exactly one fuel row in `EstateIndexService._findings`, with every §9p.2 item 4 field:
   - `lens_flags == ["RISK"]`;
   - categories MAPPED with `PROTECT_ASSET`/MOVES/`MG-8`;
   - `links.finding == "/sites/KISIWA-001/fuel-findings/<id>"`;
   - `link_refs.finding.kind == "FUEL_FINDING"`;
   - consequence PRICED with the two-place amounts and `basis`.
2. **Money untouched.** `_portfolio` with and without the fuel Finding gives equal `selected_lines`, `money`, `value_cards`, `footer`, `summary.combined_value`, `summary.combined_value_state`, and `double_count_violations(body) == []`. Must fail if the join moves into `site_coverage`/`_mini_grid`.
3. **Counts.** `category_counts.PROTECT_ASSET.open_findings` is +1 and `sites_with_primary_finding` includes the Site. `finding_count` is +1. The Risks lens shows the row, and the Cost lens does not.
4. **Consequence cases.**
   - no row: UNPRICED with null source;
   - UNPRICED row: UNPRICED with its id;
   - PRICED with PARTIAL coverage: UNKNOWN with no amounts;
   - PRICED with HISTORICAL: UNKNOWN with no amounts;
   - `basis` equals `site_outcomes.mini.FUEL_BASIS`.
5. **Gates.**
   - Coverage UNKNOWN/PENDING/STALE gives no fuel row. Must fail if the gate is dropped.
   - A window outside `[from, to)` gives no row.
   - A snapshot without `fuel_findings` gives no row and no error.
   - A Site whose `fuel_findings` returns `[]` gives `_findings` and `_portfolio` bodies equal to the bodies from a snapshot lacking the method (Kobo byte-equality).
6. **Action column.**
   - A fuel row with thread `RESOLVED_MONITORING` gives `workflow_label == "Verified"`, placement `MONITOR`/`VERIFIED_WATCH_RETURN`.
   - Thread `OPEN` and priced gives "No action agreed yet", `COMPARE_VALUE`/`PRICED_SINGLE`.
   - Unpriced and OPEN gives `UNPRICED_RISK`/`UNPRICED_OTHER`.
   - A **cold** row with a `RESOLVED_MONITORING` thread keeps "No action agreed yet". Must fail if the override is not mechanism-gated.
   - `place(row, None, cov, None)` without `label` is unchanged.
7. **Assure.** §9p.3.
8. **Store parity.** With a fake connection, `fuel_findings_on` and `fuel_findings` return equal tuples, and both refuse bad bounds with `FINDINGS_REFUSED`.

**Backend Postgres, new `backend/tests/test_k8_estate_fuel_postgres.py`** (`assetops_k8_test` only; reuse `test_k4a_fuel_finding_postgres.py`'s fixture helpers by import, never copy):
- Raise one priced fuel Finding.
- `build_estate_index_service(url).findings(...)` shows the row, with consequence from the stored row and evidence-backed `source_provenance` state not `UNKNOWN`.
- `build_estate_portfolio_service(url).portfolio(...)` `money.groups`/`selected_lines` contain no fuel id.
- One estate read opens exactly one connection: assert through the existing engine-connect counting pattern if one exists, else skip this assertion and say so in the packet.

**Unchanged and green:** `test_ch5c2_clock_guard.py` (module list +2), `test_w303_portfolio_api.py`, `test_cc_placement.py`, `test_cov_partial_portfolio.py`, `test_ch6b2_portfolio_cards.py`, `test_pv1_value_lines.py`, `test_k4b_protect_fuel.py`, `test_out_b4_imports.py`, and estate goldens (fakes hold no fuel; **any golden diff is stop S-1**).

**Rows and coherence self-tests:**
- `backend/tests/test_demo_combined_finish_rows.py`:
  - `expected_site_codes(False/True)`;
  - `optimize_card`: one priced passes (unchanged); Kobo and Kisiwa priced passes with exact `detail`; Kisiwa priced with `allowed=(KOBO,)` fails; Kobo unpriced fails.
- `tools/checks/test_chain_coherence.py`:
  - COH-7a Kisiwa summary Site passes with the Dar local-day window and fails with the UTC-midnight window (must fail if `SUMMARY_SITE_TZ` is removed);
  - COH-1 accepts the fuel Finding and fuel verdict hrefs (must fail if either route is removed);
  - the route file stays sorted and unique.

**Frontend:**
- the `SiteWindowOverview` test file:
  - `minigridObjective(undefined)` and Kobo's names give `MINIGRID_OBJECTIVE`;
  - Kisiwa's names give the exact Kisiwa literal;
  - `[]` gives `OBJECTIVE_NO_LOADS`;
  - the rendered line uses `mini.loadNames`;
- the `MiniPerformance`/`miniServiceRoutes` test files:
  - "Health post" and "Health clinic" give `CLINIC_FEEDER_LABEL`;
  - "Cold store (ice and fish)" gives the Kisiwa literal;
- `estatePortfolio.test.tsx`/`findingIndex` tests: a fixture fuel row renders its interval, "Verified" and the `/fuel-findings/` link with no client words added;
- `tsc`.

**Guards:**
- `tools\check-all.ps1`, `check-architecture.ps1`, `check-agent-workflow.ps1`, `check-navigation-truthfulness.ps1`, run directly with no `-ExecutionPolicy`;
- chain coherence self-tests;
- `node tools/checks/frontend-hardwiring.mjs` (no rise);
- the fast tier for the edited backend files.

**Not run:** full suite, prepare.

### 9p.13 Files (approved list)

- **Backend:**
  - `B/fuel_balance/adapters/postgres_fuel_balance_store.py` (`fuel_findings_on`);
  - `B/estate/adapters/postgres_estate_read.py` (`fuel` kwarg, `dispose`, `EstateSnapshot.fuel_findings`);
  - `B/estate/composition.py`;
  - `B/estate/index.py` (`_fuel_rows`, the join);
  - `B/estate/portfolio.py` (`FUEL_THREAD_LABEL`, `portfolio_row`);
  - `B/estate/placement.py` (`label` kwarg only);
  - `config/chain/stored-composer-modules-v1.json` (+2).
- **Tools:**
  - `T/demo_combined_finish.py` (CO-6, `_kisiwa_present`, `expected_site_codes`, the CH5D1-O1 call);
  - `T/demo_combined_rows.py` (`optimize_card`);
  - `T/checks/chain_coherence.py` (`SUMMARY_SITE_TZ`);
  - `T/checks/fixtures/chain_coherence/screen_routes.json` (+3);
  - `T/checks/test_chain_coherence.py`.
- **Frontend:**
  - `F/sites/SiteWindowOverview.tsx`;
  - `F/shell/SiteDetailFrame.tsx` (`loadNames` only);
  - `F/sites/MiniPerformance.tsx` (`feederName` only);
  - their test files;
  - `F/estate/__tests__/` fixtures as needed.
- **Docs:** `backend/tests/test_demo_combined_postgres.py` (docstring lines 3 and 9 only), `backend/TESTING.md` (327-328).
- **Tests:** the two new backend files, `backend/tests/test_demo_combined_finish_rows.py`.
- **Packet:** `.agent/review-packet-K8.md`, plus the capture-phase section on `task/DIESEL-K8c-captures`.
- **Not touched:**
  - every K5 file (`refs.py`, `linkRefs`, the fuel pages) except by import;
  - `evidence/overview.py`;
  - the Kisiwa template;
  - `.agent/owner-walkthrough-notes-2026-11-01.md`;
  - `Docs/demo-sprint/implementation-logic-design-proposal.html`.

### 9p.14 Pre-flight (no code first; batch every question in one message)

- (a) `site_overview.serve` serves `KISIWA-001` (§9p.5 item 1).
- (b) Kobo's served CRITICAL `load_label` and Kobo's Foundation LOAD names match `/clinic|health/i`.
- (c) Kisiwa's stored timezone.
- (d) The frontend estate Findings and Portfolio link rendering accepts a `FUEL_FINDING` ref without a K5 file change (READ `linkRefs`/the row link code).
- (e) The sort rule of `stored-composer-modules-v1.json` as its test enforces it.
- (f) Whether the K4a Postgres fixture can be imported as is.
- (g) Name every other non-KIS finish or COH row that hard-codes three Sites or a three-Site count (the Architect's grep found only CO-6:451/453 and `SITE_CODE`). A new one is a stop for a ruling, not a silent edit.

### 9p.15 Stops

- **S-1:** any Kobo, Cold or EV served byte, golden or estate-fake body changes.
- **S-2:** fuel money reaches `select_financial_scope`, `selected_lines`, money groups, `estate_total`, `combined_value`, Financials, or any sum.
- **S-3:** the join needs a second transaction or connection, or a stored-route module beyond the two named.
- **S-4:** the frontend needs a K5 file change for the `FUEL_FINDING` link (pre-flight (d)).
- **S-5:** the legacy overview serves Kisiwa.
- **S-6:** a Kobo load name or label misses R-LOAD.
- **S-7:** a guard rejects a literal (report it; never reword silently).
- **S-8:** K8 code above **1.1**, or K8 total above **1.4**.
- **S-9 (capture phase):** a four-Site re-expectation or COH row fails on the rehearsal DB (§9p.9 procedure).
- **S-10:** Kisiwa's stored timezone is not `Africa/Dar_es_Salaam`.

### 9p.16 Branch, DB, model, size

- **K8 code:** branch `task/DIESEL-K8-estate-four-sites` in `C:\Users\assef\Bineyame\AssetOpsV1-k8` (exists, from main). DBs: `assetops_k8_test` and the producer scratch clone `assetops_k8_audit_kisiwa` only. Never `assetops_demo3_kisiwa_test` for writes, and never `assetops_demo3_full_test`. Opus first build and review. Merge on review ACCEPT.
- **K8 capture phase:** `task/DIESEL-K8c-captures`, after K9's rehearsal prepare, read-only `serve` on K9's rehearsal DB.
- **Size: K8 = 1.2** (range 1.1–1.35), against the card's 1.0. That is +0.2: the estate join is larger than §9l.4's +0.15 (consequence gates, Portfolio Action column, module list), plus the re-expectation self-tests and the device-copy rules. The increase is reported, not absorbed.
  - **K8 code 0.95:** estate join, store and composition 0.3; Portfolio label and placement 0.05; tests (L0 and Postgres) 0.25; re-expectations and self-tests 0.14; device copy 0.1; docs 0.02; clone captures (a) 0.09.
  - **K8 capture phase 0.25.**
  - **Template v2 is ruled out, so +0.**
  - **Kisiwa total +0.2.**

### 9p.17 Critical path, tripwire, date

- **Spent through K7-F:** 3.65 → K4a 1.6 → K6a 0.6 → K6b 1.4 → K7-F 0.65 = **7.9**.
- **K8 code is now on the path.** It waited for K4b's fix round (R3j3), and K9's rehearsal needs it on main. Remaining:
  - K8 code 0.95, **in parallel with K9's pre-rehearsal work** (wording guard, KIS-1/2/6/7 rows, COH-17/V4 and §9p.7 items 5–6, about 0.6 of K9's 1.0);
  - then K9's rehearsal (machine time, 2.0–2.35 h, outside lane-units);
  - then K9's remaining ~0.4 beside the K8 capture phase 0.25.
- **Path ≈ 7.9 + 0.95 + 0.4 = 9.25** if the captures overlap K9's reading, **≈ 9.5** if they run after it. **Headroom 0.25–0.5 to the 9.75 tripwire. Not crossed. No cut.**
- **Condition (coordinator):** K9's card and build must start **now** on another lane, beside K8 code. If K9 waits for K8 to merge, the path is 7.9 + 0.95 + 1.0 + 0.25 ≈ **10.1**, which crosses the tripwire. That then becomes an owner question with these cut options, in order:
  1. the all-26 recapture narrowed to the changed and new pages only (about −0.1);
  2. the device-copy rules of §9p.5 deferred, with Kisiwa's Overview showing Kobo's objective words under a logged MOCK DEVIATION (about −0.1);
  3. the K8 capture phase limited to the four-Site Portfolio and Findings (about −0.1).
- **Demo date:** about +0.05–0.1 working day on R3n's +3.5, so about **+3.6** (range 3.1–5.6).
- **Plan HTML rows (coordinator):**
  - K8 becomes 1.2 ("K8 code 0.95, K8 capture phase 0.25 on K9's rehearsal DB");
  - the lanes figure shows K8 code beside K9's pre-rehearsal work, then the rehearsal, then the K8 capture phase;
  - the rulings table gains "DIESEL-1-R3p: K8 card; fuel Finding joins the estate Finding rows after coverage (never money; R3j2 item 3 met); fuel rows' Action column from thread state; W6 list +2 (`verification_rules`, `finding_text`); Kisiwa no objectives; R-LOAD device copy (Kobo byte-equal); template v2 deferred; CO-6/CH5D1-O1/COH-1 routes/COH-7a re-expected by data; `SITE_CODE` to K9; captures (a) clone + (b) on K9's rehearsal DB (§3.5 keep until captures); K8 1.2; path about 9.25–9.5".

### 9p.18 Lines for K9's card (the coordinator passes these verbatim)

- Keep the rehearsal DB and work folder until the K8 capture phase and the W6 guard CLI are done (amends §3.5). Copy `check.json` to `check-rehearsal.json` before any re-check.
- `SITE_CODE` and `LOCAL_DAY_TZ` gain Kisiwa (`"kisiwa": "KISIWA-001"`, `"Africa/Dar_es_Salaam"`). COH-3/4/5/10/13 then run on Kisiwa boards. COH-10 gains the Kisiwa fuel thread (§9p.7 item 5).
- KIS-6 gains the Assure count line of §9p.3.
- The W6 guard CLI acceptance (R3j3) also expects `unlisted_modules []` with K8's two added modules. A further unlisted, clock-free fuel module is a one-line add, pre-authorised after `test_ch5c2_clock_guard.py` passes.
- A failing re-expected row is reported, never edited (§9p.9).

### 9p.19 Owner questions

None (conditional on §9p.17's parallel start). For the owner's information, in plain words:
- The unexplained-fuel finding now appears in the estate-wide finding lists and the portfolio table. Its money is shown only on its own row and is never added to any other figure.
- Kisiwa's overview now names its own loads: households, the cold store and the water pump, not a clinic and a mill. Kobo's pages are unchanged.
- Kisiwa declares no targets for the demo, and the screens say so.
- The work grows by about 0.2 unit. The demo date moves by about a tenth of a working day, provided the final check-and-rehearsal step starts now, alongside this work.

## 9q. Ruling DIESEL-1-R3q — K9 pre-rehearsal answers (Q1–Q5)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md` 2026-10-27). Read-only code reading in `AssetOpsV1-k9` (`task/DIESEL-K9-checks-rehearsal`, after 319236613) and main 6913b3454. No DB, no suites. This ruling amends §9p.7 items 2 and 6 and §9p.18 where they differ.

### 9q.1 Q1: Kisiwa board collection. The builder's proposal is confirmed, with the exact form below

**What the code does (READ).** `SITE_CODE` alone collects nothing for Kisiwa. `day_windows(days)` (`T/checks/chain_coherence.py:72`) iterates `days.json`, and `resolve_story` builds that file from `CORE_SITES` only (`T/demo_combined.py:166`). Kisiwa's calendar lives in `story["kisiwa"]`, and `date=` is sent only for Kobo (`:92`). §9p.7 item 6's sentence "extending `SITE_CODE` collects Kisiwa boards" was wrong. This section replaces it.

**Days.** Use exactly the two boards `story_links` opens (`T/demo_combined.py:306-309`), and no others:
- `S−5d`, the morning after the unexplained-fuel night: `(at(story["S"]) − 5 d).date()`;
- `S`: `at(story["S"]).date()`.

The S−6d board (the evening night 4 opens) is **not** collected. Neither story_links nor DS-1 opens it.

**Form.**
```python
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001", "kisiwa": "KISIWA-001"}
LOCAL_DAY_TZ = {"kobo": "Africa/Addis_Ababa", "cold": "Africa/Addis_Ababa", "kisiwa": "Africa/Dar_es_Salaam"}
#: DIESEL-1-R3q: the Kisiwa boards `demo_combined.story_links` opens (offset from S in days, id kind).
KISIWA_BOARD_DAYS = ((-5, "fuel-morning"), (0, "S"))

def kisiwa_day_windows(story: dict) -> list[dict[str, Any]]:
    """DIESEL-1-R3q: Kisiwa's board days, from `story["kisiwa"]` (not `days.json`), only when Kisiwa is in
    `story["sites"]`. Each is its Site-local day read by `?date=` (mini board), in `day_windows`' row shape."""
```
- **Gate.** Return `[]` unless `"kisiwa" in (story.get("sites") or [])` and `story.get("kisiwa")`. A three-Site or Kisiwa-less work folder therefore collects exactly what it collects today.
- **Row.** For each `(n, kind)`:
  - `day = (at(story["S"]) + timedelta(days=n)).date()`;
  - `local = datetime.combine(day, time(0), tzinfo=ZoneInfo(LOCAL_DAY_TZ["kisiwa"]))`;
  - `lo, hi` = `local` and `local + 1 d`, both in UTC (Dar es Salaam is UTC+3 with no DST, so `[D−1 21:00Z, D 21:00Z)`);
  - `estate` = `day_windows`' existing enclosing-midnight formula, which gives `[D−1 00:00Z, D+1 00:00Z)`;
  - `id = f"day:kisiwa:{kind}:{day.isoformat()}"`, `site_code = "KISIWA-001"`, `date = day.isoformat()`.
- **`day_windows`** skips `site == "kisiwa"` explicitly (its days come only from the function above). It is otherwise byte-equal for the three core Sites.
- **`collect`:** `days_out = day_windows(days) + kisiwa_day_windows(story)`. The board, `chain_site` and `day_` estate fetches then run unchanged (`date=` for both Kisiwa fetches).
- **`_coh7a_window`:** after the change, the K8 lookup `{**{SITE_CODE[k]: z for k, z in LOCAL_DAY_TZ.items()}, **SUMMARY_SITE_TZ}` maps `KISIWA-001` to the same zone twice. That is harmless.
- **Merge note.** Whichever of K8 and K9 merges second keeps the union:
  - K9's `"kisiwa"` entries in `SITE_CODE` and `LOCAL_DAY_TZ`;
  - K8's `SUMMARY_SITE_TZ` line and lookup, both unchanged (not removed: removal is churn with no effect).

**L0 tests (in `T/checks/test_chain_coherence.py`).**
1. With a story whose `sites` includes `kisiwa`, the two rows equal the `date=` values `story_links` prints for `KISIWA-001` boards on the same story. Call `demo_combined.story_links` with a stub `kisiwa` doc and parse its links. This proves "the boards the presenter opens".
2. The S−5d row's date equals `story["kisiwa"]["runs"][INCIDENT_K − 1]["night_date"] + 1 day`.
3. Without `kisiwa` in `sites`, `kisiwa_day_windows` returns `[]` and `day_windows` output is unchanged.
4. `LOCAL_DAY_TZ["kisiwa"] == demo_combined_kisiwa.ZONE`.

**Which rules then run on Kisiwa boards, and what must hold (READ against `board.py`, `mini.py:492-503`, `:811-827`).** The fuel Finding reaches the board as an ordinary `kind: "FINDING"` issue (`board.py:1105`) only where it is open and its night window meets the board day (`board.py:707`, `mini.py:825`):
- on **S−5d**, night 4's window `[S−6d 15:00Z, S−5d 09:00Z)` meets the local day, so it is a Protect MOVES issue;
- on **S** it does not, so it is not an issue there.

Kisiwa's dispatch Findings appear as issues on both days in the ordinary way.

| Rule | On Kisiwa boards | Expectation |
|---|---|---|
| COH-0 | 2 boards, 2 `chain_site`, 2 × `day_` estate reads | every one 200 |
| COH-3 | **0 Kisiwa pairs, by design** | see exception E1 |
| COH-4 (board half) | the fuel Finding (S−5d) and dispatch Findings are in `day_findings_all` for KISIWA-001 | pass. K8's estate fuel rows use the same intersect rule; the S−5d estate window `[S−6d, S−4d)` contains night 4's window |
| COH-5 | fuel: Protect → RISK, and K8 gives `lens_flags == ["RISK"]`; dispatch: Cost → COST | pass |
| COH-6 | Kisiwa shows no opportunity | vacuous, pass |
| COH-10 | Portfolio leg: the `kisiwa-fuel` thread (853fc207d), occurrence 1 of 1 in week and month (not in S, which does not contain night 4; "observed" needs one window). Board leg: the S−5d ref thread equals the Portfolio thread in week and month (both contain the S−5d window) | pass |
| COH-13 | S−5d board state (before the verdict) against the Portfolio state (`RESOLVED_MONITORING` if VERIFIED, effective on the evaluate day) | pass through the "hi took effect later" branch. Time-zone free |
| COH-14 | S: the Protect row may carry the fuel thread's MONITORING thread line with no MOVES Finding | pass: no Protect outcome is NEEDS_ATTENTION / PRIMARY_FINDING_OPEN on S |
| COH-17 (day leg) | `day_chain_estate` against `day_findings_all` on both Kisiwa day windows | pass (one computation) |

- **No countdown, multi-night window: no exception needed.**
  - No rule reads the countdown. R3j2 §9j2.4 `close_measured: False` changes only the line copy, and COH-14 keys on `thread_lines[].kind`, not on a countdown.
  - The multi-night window is judged per board, and only S−5d shows it.
- **Exception E1 (COH-3, named).** The fuel Action is a `FUEL_BALANCE` **domain** Action. It is absent from `/api/estate/actions` (mini `actions.site_window_on`, `postgres_estate_read.py:330`), and Kisiwa is not in `DOMAIN_SITES`, so `_actions` never yields it. Kisiwa's dispatch Findings have no Action. COH-3 therefore evaluates 0 Kisiwa pairs.
  - **Not extended.** Adding Kisiwa to `DOMAIN_SITES` also switches COH-2/8/11 onto a domain-Action row shape never proven on a mini Site. That is new scope with no demo beat (owner 2026-11-05).
  - The Finding → Action link is proven by KIS-10 (thread link) and KIS-9 (e).
  - The packet states "COH-3 Kisiwa pairs: 0 (R3q E1)". After-the-demo list: "COH-3 for mini-Site domain Actions (Kisiwa fuel)".
- **At the rehearsal:** a Kisiwa COH finding fails F-COH. It is a stop reported with its `check.json` entry (§9p.9), never edited.

### 9q.2 Q2: KIS-6 confirmed as CO-6's pattern. The Optimize no-sum is KIS-7

**Pick.** §8.7 is the row list: KIS-6 holds the counts, KIS-7 holds the Optimize card. §9p.7 item 2's "the no-sum check stays in K9's KIS-6" used the withdrawn §4.3 numbering, so it reads **KIS-7**. §9p.3's Assure line is a count and goes in **KIS-6** (as §9p.18 says).

**KIS-6** (`demo_rows.kis6`, pure; wired after KIS-8a; on a dataset without Kisiwa it raises `KisiwaMissing`, the KIS-4 pattern). It reads the week window `[S−6d, S+1d)`:
1. **Four Sites from data.**
   - Outcome-summary `sites[].site_code`, `/api/estate/chain` `sites[].code` and the Portfolio `objectives` site codes (the list CO-6 reads after K8) each equal `sorted([KOBO, COLD, EV, KISIWA])`.
   - `objective_site_count == 3` is CO-6's and is not repeated here.
2. **Kisiwa's summary cells equal its S board.**
   - `{category: state}` of the summary's KISIWA-001 `rows` equals `{category: state}` of `/api/sites/KISIWA-001/outcome-board?date=<S date>`.
   - The summary entry has `window_basis == "DAY"` and `window.from == iso(demo_rows.site_day_start(S.date(), "Africa/Dar_es_Salaam"))`.
3. **Assure line (§9p.3), with the verdict read from data.**
   - `want = 1 if kisiwa.json["verdict"] == "VERIFIED" else 0`. The verdict is recorded as computed (H, §9m.5) and never forced.
   - The chain `sites` entry for KISIWA-001 has `threads.verified == want`.
   - The Portfolio Assure card `claim.value` equals the chain `counts["count.verified_results"].value`.
   - No Assure value line exists for Kisiwa (H2).
4. **Return** the four code lists, Kisiwa's cells, `want` and the two Assure values.
5. **L0 self-test:** one pass body, plus one fail body for each of items 1–3.

**KIS-7** (`demo_rows.kis7`, pure; wired after KIS-6; `KisiwaMissing` if absent). It reads the S window (CH5D1-O1's).
1. The priced codes, read from each summary Site's cost claim (never typed), are exactly `[KOBO, KISIWA]` in Site order.
2. `card.claim is None`, and `card.value.text == card_text("cost.sites", sites=sites_text(2))`.
3. `demo_rows.never_summed([each priced Site's claim amount_high], bodies) > 0` and finds no sum. The bodies are the S and week outcome-summary bodies and the Portfolio week body.
4. If Kisiwa is not priced on S, the row fails and the failure is reported as a stop. It is never re-expected to the one-Site path.
5. **L0 self-test:** a pass body, plus fail bodies for one priced Site, a present claim and a summed string.

### 9q.3 Q3: KIS-1 sources and expected values

**"As known" means as known now.** Read the Site's Foundation revisions through `PostgresFoundationStore(ctx.url).revisions(tenant_id, site_id)` (`sites/foundation_records.py:269`). Keep only the current-knowledge rows (`superseded_at is None`). The components are in `RevisionRow.content`. Pure logic goes in `demo_rows.kis1(revisions, register, prices)`, and a dataset without Kisiwa raises `KisiwaMissing`.

| Item | Source | Expected |
|---|---|---|
| Site | `site` row `site_code_key = lower('KISIWA-001')` | exists |
| Stop setting, "90 throughout" | the `generator` component's `stop-soc-threshold` in **every** current revision (template `config/site-templates/kisiwa-diesel-hybrid-60kw.yaml:123`, fixture `backend/tests/fixtures/s1/kisiwa-001.yaml:86`) | one value across all revisions: `90`, unit `%`. "Throughout" means no revision changes it: Kisiwa's lever is the Action, not a stop setting (R2). K0's RUN_GUARD_HISTORY already proves every run froze this stored history |
| No-load rate | the `generator` component's `generator-no-load-fuel-rate` and `-basis` in every current revision with `valid_from ≥ kisiwa-register.json["no_load_effective_from"]` | equals `demo_combined_kisiwa.NO_LOAD` (read, never retyped) **and** the §8.7 literal `4.9` `L/h`, `GENERIC_DEFAULT`. No revision in that range lacks it |
| Sensor accuracy | the `fuel-tank` component's `fuel-level-sensor-accuracy` and `-basis` in every current revision with `valid_from ≥ register["roles4_effective_from"]` | equals `ROLES4["component_properties"]["properties"]` (`backend/conversions/kisiwa-001-minigrid-roles-demo-config.json`) **and** the literal `10` `L`, `GENERIC_DEFAULT` |
| Diesel price v1 | `build_trial_comparison_ports(ctx.url).price_selection(t, s, w.window_start, w.window_end, w.window_end)` for each of the 10 stored night windows (KIS-4's call) | every selection is priced with **one** `revision_id`, and its value and currency equal step `v1` of `backend/conversions/demo-diesel-price-publications.json` (`1.25` `USD`, read from the file). No later step was published for Kisiwa |

- **Component lookup.** Look up components by `component_id` (`generator`, `fuel-tank`) in `content`.
- **Content keys.** The builder confirms the content key path on the in-memory store from `register_in`, in the L0 test. If the path is not `components[].properties[]`, that is a one-line adaptation, not a stop.
- **L0 self-test:** a pass body, plus fail bodies for stop 60 in one revision, no-load 3.3, a missing accuracy basis and two price revisions.

### 9q.4 Q4: KIS-2 is the fuel-cost-2 formula over the stored power intervals, with exact equality

**Stored columns (READ).**
- `financial_consequence_revision` (0011 + 0053): `finding_id`, `finding_revision_id`, `revision_no`, `recorded_at`, `model_id`, `state`, `sfc_upper_multiplier`, `quantity_high_exact` (`n/d` text), `quantity_high` (ceiling Decimal), `no_load_fuel_rate_l_per_h`, `no_load_fuel_rate_basis`, `idle_seconds`.
- The "segments" are its `financial_consequence_power_interval` rows (`consequence_revision_id`, `mean_kw`, `duration_seconds`, `sfc_l_per_kwh`; written at `postgres_consequence_store.py:249-259`).

Kobo's `idle_morning` covers only the idle term, so KIS-2 needs its own function.

**Selection.**
- Kisiwa's dispatch Findings are `finding_revision` rows on KISIWA-001 in the dispatch domain. Bind the same backend constant the R3k filter binds, never a retyped literal.
- For each Finding, take the latest revision (`revision_no` DESC) and its head consequence: the Kobo `_consequence_heads` ordering, with the Site as a parameter.
- **At least one** Finding is required.

**Per Finding** (`demo_rows.kis2(heads, intervals_by_head, latest_revisions)`, pure, exact `Fraction`):
1. The latest Finding revision is `SUPPORTED`, and the head consequence cites it (`finding_revision_id`).
2. `model_id == "fuel-cost-2"`, `state == "PRICED"`, and `Decimal(sfc_upper_multiplier) == fuel_cost_v2.MULTIPLIER`.
3. `no_load_fuel_rate_l_per_h == 4.9` and its basis is `GENERIC_DEFAULT`. These equal KIS-1's Foundation value.
4. The computation:
   ```
   loaded = Σ_{mean_kw > 0}  F(mean_kw) × F(duration_seconds, 3600) × F(sfc_l_per_kwh)
   idle   = Σ_{mean_kw == 0} F(duration_seconds, 3600) × F(no_load_fuel_rate_l_per_h)
   exact  = F(sfc_upper_multiplier) × (loaded + idle)
   ```
   Here `F(x) = Fraction(str(x))`, which is exact for stored numerics.
5. **Tolerance zero:**
   - `exact == Fraction(quantity_high_exact)`;
   - `Decimal(quantity_high) == fuel_cost.to_decimal_ceiling(exact)` (import it, never re-implement it);
   - `idle_seconds == Σ duration_seconds over mean_kw == 0`.
6. Kisiwa has 0 idle minutes (§9d.6), so `idle` is 0 on the real data. That is **reported** (`idle_seconds` printed per Finding) and not asserted. The idle term is exercised by the self-test.
7. A non-SUPPORTED latest revision, or a non-PRICED head, fails the row and is reported as a stop. It is never forced.

**L0 self-test:**
- one pass body with one loaded and one idle interval;
- fail bodies for: a ×1.00 multiplier, a dropped idle interval, `quantity_high` rounded half-up instead of ceiling, `fuel-cost-1`, and `UNPRICED`.

### 9q.5 Q5: COH-17 and V4 confirmed

- The collector fetches `board_summary.{w}.{code}` for every summary Site (`chain_coherence.py:186-191`).
- `_coh17_full` iterates `chain["sites"]` (`:1395-1420`). V1–V3 run for every Site and window. V4 runs on the S window for every mini Site, so Kisiwa is included with no code change.
- K9's part is **self-tests only**, in `test_chain_coherence.py`, on a four-Site fixture bundle:
  - Kisiwa V4 passes when the nodes are equal and fails (`site_code == "KISIWA-001"`) when one node differs;
  - one C2/V2 pass and fail case on the Kisiwa entry.
- **Rehearsal evidence:** the packet quotes the `board_summary.S.KISIWA-001` request at status 200. That shows V4 actually compared Kisiwa: the Site-set guard at `:1368` did not skip the window.

### 9q.6 Files (added to K9's list)

- `T/checks/chain_coherence.py`: §9q.1.
- `T/checks/test_chain_coherence.py`: the §9q.1 tests and the §9q.5 self-tests, with fixture bundle(s) under `T/checks/fixtures/chain_coherence/bundles/`.
- `T/demo_combined_rows.py`: `kis1`, `kis2`, `kis6`, `kis7`.
- `T/demo_combined_finish.py`: the four rows, wired after KIS-8a in the order KIS-1, KIS-2, KIS-6, KIS-7.
- The existing row self-test file for the L0 bodies.

### 9q.7 Size, path, tripwire

- **K9 stays 1.0.** The answers match the builder's proposals, apart from these additions:
  - the E1 note;
  - the conditional `want` in KIS-6;
  - KIS-1's per-window price read;
  - KIS-2's interval read.

  Each is within its estimate. The pre-rehearsal work is about 0.25 spent plus 0.3–0.35, so **0.55–0.6, inside the 0.6 budget**.
- **Watch item.** If pre-rehearsal work passes 0.7, the builder reports before the rehearsal. The first lever is moving the KIS-7 Portfolio body out of `never_summed` (−0.02). No row is dropped.
- **Critical path unchanged: about 9.25 (captures overlapping K9's reading) to 9.5,** against the 9.75 tripwire. Not crossed, no cut.
- **Plan HTML (coordinator):** the rulings table gains "DIESEL-1-R3q: K9 pre-rehearsal answers; Kisiwa boards S−5d and S collected from `story.kisiwa` (`date=`, Site-local), COH-0/4/5/6/10/13/14/17 on them, COH-3 0 Kisiwa pairs by design (E1, domain Action); KIS-6 counts + Assure (verdict-conditional), KIS-7 Optimize no-sum; KIS-1 Foundation as known now (stop 90 every revision, 4.9 L/h, 10 L, price v1 1.25 USD); KIS-2 fuel-cost-2 over stored power intervals, exact; COH-17/V4 self-tests only; K9 1.0; path 9.25–9.5".

### 9q.8 Owner questions

None.

## 9r. Ruling DIESEL-1-R3r — Kisiwa Overview evidence state

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`, owner 2026-10-27). Read-only code reading in `AssetOpsV1-k9` (`task/DIESEL-K9-checks-rehearsal` at 8375e3864) and `AssetOpsV1-k8` (ee9c9805f). No DB, no suites. Trigger: K8 builder 3 served a clone of `assetops_demo3_kisiwa_test` and Kisiwa's Overview showed "Awaiting evidence migration" (409 `AWAITING_EVIDENCE_MIGRATION`), so R3p's Kisiwa objective line was never on screen.

### 9r.1 Q1: the default four-Site prepare does not open Kisiwa's Overview either (READ)

- **The gate.** `site_overview/route.py:139-147`: an imported Site's Overview is served only with a passing S2 Evidence comparison (`imported_scope`) **or** a persisted `NO_LEGACY_EVIDENCE` cutover basis for its current import (`no_legacy_basis`, wired at `main.py:430-432` to `PostgresFoundationStore.no_legacy_evidence_basis`, `postgres_foundation_store.py:254-268`).
- **The prepare.** `T/demo_combined.py` `finish` (`:585-588`) runs `evidence_migration run` for `KOBO-001` only. Nothing in the parent, in `T/demo_combined_kisiwa.py` `build`/`register` (`:159-181`, `:699-808`) or in `register_in` (`:121-141`) writes a comparison or a cutover basis for Kisiwa. The only basis writer in the code is `sites/w402_demo.py:62-66`, and no demo child calls it.
- **So the gap is not a Kisiwa-only-prepare artifact.** The four-Site rehearsal DB would show the same 409 on both Kisiwa board links `story_links` prints (`/sites/KISIWA-001?date=` for S−5d and S, `T/demo_combined.py:307-309`).
- **How the other Sites get past it.** Kobo: the S2 comparison in `finish`. Cold and EV: they never reach this gate. `SiteDetailFrame.tsx:130-156` sends a `COLDCHAIN` Site to the cold Overview and an `EV_CHARGING` Site to the EV page, and neither reads `/overview`. Kisiwa is `MINIGRID`, so it gets Kobo's mini Overview and therefore Kobo's gate (`SiteOverview.tsx:138`, `:182-196`).
- **Side effect today.** The outcome board's mini `source` port uses the same decision (`site_outcomes/composition.py:35-45`, `read.py:233-235`). It raises `OverviewClosed` for Kisiwa, so a Kisiwa board can read `read_state` PARTIAL with a failed port. That is a latent risk for the Kisiwa boards R3q §9q.1 now collects.

### 9r.2 Q2: ruling (a), record the honest no-legacy cutover basis at Kisiwa's import

**Why this is not faking.** Kisiwa is imported with `legacy_documents=()` (`demo_combined_kisiwa.py:127-128`), and the prepare tree's `var/sites` holds only `kobo-001.yaml` (`demo_combined.py:449-451`). No legacy evidence set exists to compare. q12-6 (W4-02) defines `NO_LEGACY_EVIDENCE` for exactly this case: "only an installer whose import carries no legacy documents calls this". `w402_demo.py:62-66` is the precedent.

The basis does **not** open the Performance gate. Kisiwa has no Performance comparison report, so S3, Finding and money claims on the Overview stay closed under the gate's own honest reason, `NO_LEGACY_EVIDENCE_REASON` ("No legacy evidence was imported for this Site. Dispatch has no assessed comparison for this selection.", `performance_comparison.py:186-196`). No comparison is written, nothing is tuned and nothing is forced.

(b) is rejected. It leaves two printed story links (the S−5d "morning after" board beat and the S board) on a refusal page. It also needs a links change of the same size as (a), and keeps the board-port risk in §9r.1.

**The change (K9, `T/demo_combined_kisiwa.py` `register`, Postgres path only):**
- Inside the `try`, directly after `result = register_in(store, import_at, install_at)` (`:169`), add:
  ```python
  # DIESEL-1-R3r (q12-6): the import carries no legacy documents (`legacy_documents=()` above), so record the
  # explicit NO_LEGACY_EVIDENCE cutover basis with it (w402_demo.py's pattern). Never a comparison; idempotent.
  store.record_no_legacy_evidence_basis(UUID(result["tenant_id"]), UUID(result["site_id"]), now=import_at)
  ```
  Import `UUID` locally.
- `register_in` is **not** changed, because the in-memory K1 callers keep their store contract. No new keys go into `kisiwa-register.json` or `kisiwa.json`, so KIS-1 (`kis1(..., register, ...)`) is byte-stable.
- **No frontend change.** R3p's objective line and its tests stand.

**Proof row (K9, `T/demo_combined_finish.py`): `KIS-OV`**, wired after KIS-7, using the existing `KisiwaMissing` pattern when Kisiwa is absent:
- `GET /api/sites/KISIWA-001/overview?date=<S−5d>` and `?date=<S>` (the two `story_links` days) each answer 200 with a selected-day window summary. Any 409 or 503 fails the row with the status and `detail.code`.
- One SQL read: exactly one `site_cutover_basis` row for Kisiwa, `basis = 'NO_LEGACY_EVIDENCE'`, with `site_import_id` and `source_sha256` equal to its `site_import` row.
- It reports, and does not assert, the Kisiwa S board's `read_state`.
- L0 self-test: one pass body; fail bodies for a 409 `AWAITING_EVIDENCE_MIGRATION` and for a missing basis row.

**Pre-rehearsal clone probe (K9 builder, before the 2-hour prepare, about 15 minutes):**
1. Clone `assetops_demo3_kisiwa_test` to a new `*_test` DB (authorized).
2. Upgrade it to head and call `record_no_legacy_evidence_basis` for Kisiwa (`now` = the stored `site_import` instant).
3. Serve it and confirm the Kisiwa Overview answers 200 for S−5d and S and shows the R3p objective line.
4. Record the Kisiwa S board `read_state` before and after.
5. Run whichever Kisiwa rows K9's check-all already ran on that DB, before and after.

**Stops:**
- **S-r1:** the Overview answers anything but 200 after the basis is recorded.
- **S-r2:** any Kisiwa row passes before and fails after.

Either stop means report to the Architect, with no patch and no prepare.

**Known honest gaps that stay** (presenter note, not fixed before the demo):
- Kisiwa's **Evidence tab** still answers 409. `imported_scope`/`ImportedEvidenceReads.scope` (`evidence/ledger_reads.py:212-232`) honours only the comparison, not the basis, so the Overview's evidence links lead to "Awaiting evidence migration".
- The demo script does not open Kisiwa's Evidence tab.
- After-the-demo list: "Evidence routes honour the no-legacy cutover basis".

### 9r.3 Q3: owner K9, before its rehearsal prepare

- The prepare archives `git archive HEAD` (`demo_combined.py:440`), so the change must be **committed on K9's branch before the prepare starts**. A rehearsal without it would need a second 2-hour prepare to put the Kisiwa board beat and the K8 (b) Overview capture on screen.
- **Review.** K9's pre-rehearsal review is in flight. This delta (register line, KIS-OV and its self-test) goes to the same review as an addendum, or to a fresh Claude delta review. Only the delta is gated, and only High or Medium findings block.
- **K8.** No change. K8 merges on its clone captures. Its Kisiwa Overview capture with the objective line moves to the (b) captures on K9's rehearsal DB (§9p, "captures (a) clone + (b) on K9's rehearsal DB"). R3p's pre-flight (a), "`site_overview.serve` serves `KISIWA-001`", is answered by KIS-OV on the rehearsal DB.

### 9r.4 Q4: the Service page's empty default day is acceptable

- The default day (the DB's current day) has no Kisiwa run. The story hours do, and the script links the story hour, so the empty day is not on the demo path.
- **Condition (checked in K8's or K9's captures, not built):** the default day must read as an explicit "no records for this day" state, not blank cards or zeros. If it shows zeros or blank cards, log it as a High finding for the post-rehearsal polish batch. It does not block the rehearsal.
- No new link is added.

### 9r.5 Q5: size, path, tripwire

- **K9 +0.1:** about 0.02 for the register line, 0.05 for KIS-OV and its self-test, and 0.03 for the clone probe.
- Pre-rehearsal work is about 0.65–0.7. That is at the R3q watch line (0.7), so the builder reports if it passes 0.7. The R3q lever stays first in line.
- **Critical path about 9.35–9.6** against the 9.75 tripwire. Not crossed, no cut. The clone probe overlaps K8's review.
- **Plan HTML (coordinator):** the rulings table gains "DIESEL-1-R3r: Kisiwa Overview 409 on every prepare (only Kobo gets the S2 comparison; Cold/EV never read /overview); K9 records the honest q12-6 NO_LEGACY_EVIDENCE cutover basis at Kisiwa's import (no comparison, Performance gate stays closed); KIS-OV proves 200 on S−5d and S; clone probe before the prepare (stops S-r1/S-r2); Kisiwa Evidence tab 409 stays (after-demo); Service empty default day acceptable if stated; K9 +0.1; path 9.35–9.6".

### 9r.6 Owner questions

None.

## 9s. Ruling DIESEL-1-R3s — Kisiwa's closed Performance gate (board PARTIAL) and KIS-7 on real data

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only code reading in `AssetOpsV1-k9` (`task/DIESEL-K9-checks-rehearsal` at 53421ce0d) and main 96d597573 (K8 merged). No DB, no suites. Trigger: the K9 fix round found the Kisiwa board PARTIAL from the closed Performance gate, and KIS-7 likely unpriced for Kisiwa on S. This ruling amends §9r.2 (R3r's statement that the Performance gate stays closed) and R3q §9q.2 KIS-7 item 4.

### 9s.1 What the closed gate costs on the demo (READ)

**The coordinator's cause is confirmed.**
- `dispatch` (`site_outcomes/read.py:257`) and `chain_findings` (`:240`) both go through `_open` (`:140-143`), which raises `PortUnavailable`.
- The gates are `performance_gate` and `finding_index_gate` = `basis_aware_gate(performance_gate, ...)` (`main.py:404-414`, `:566`). The second changes only the reason, never the permit.
- `performance_and_prebuild` runs the Performance comparison for `("KOBO-001",)` only (`T/demo_combined.py:631-635`).

**The Kisiwa board with the gate closed (`site_outcomes/mini.py:458-530`).**
- `read_state` is PARTIAL with `dispatch` and `chain_findings` failed.
- There is no Dispatch assessment. MG-2, MG-4 and MG-6 are unsettled because `base` needs `dispatch is not None`.
- No dispatch Finding and no lead is shown, because `lead_finding` needs heads and `source_open`. The Optimize `earnings` (MG-2 fuel cost) is never priced on **any** Kisiwa day.
- **The fuel story is hit as well.** `finding_moved_outcomes(MINI)` includes **MG-8**, because `outcome_map.py:23` maps `FINDING:UNEXPLAINED_FUEL` to MG-8. The loop at `mini.py:526-527` therefore sets MG-8 unsettled whenever `findings_ok` is false (`heads is None`).
- So the K4b Protect fuel row's **status is UNKNOWN** on every Kisiwa board, even though its `fuel_*` reads are ungated and succeed.
- The fuel thread line comes from `chain_threads`, which is ungated, and should still render. The R3m Assure fuel verdict is also ungated.
- **KIS-6** passes either way: the summary cells and the S board come from the same composition.
- **Conclusion.** The S−5d "morning after" board beat would show a partial-read notice and an UNKNOWN fuel outcome. That is demo-critical.

### 9s.2 (a) The honest fix: run the product's own Performance comparison for Kisiwa (empty-set)

**No legacy evidence is needed.**
- `performance_migration run` reads the file-backed dispatch history through `JsonAssessmentStore.load_history`, which returns an empty history when the Site has no file (`json_assessment_store.py:47-52`).
- `compare` then writes a designed **empty-set report** (`performance_comparison.py:139-158`). Its statement is "Empty-set comparison: the file-backed baseline holds no dispatch claim for KISIWA-001, so no claim is said to match; a zero-inventory statement, not claim parity."
- Its outcome is PASSED **only if** the live lineage has no breaks and no head selected under another model (`:141-146`, `:219-252`).
- This is the S3-01 tool run as designed, the same command Kobo gets. It is not tuned and not forced. If the lineage is broken, the report says FAILED and the gate stays closed with that reason.

**Rejected: opening the ports under the q12-6 cutover basis.**
- q12-6 is an *Evidence* cutover basis. Ruling 3 (M4) limited its effect on the Performance gate to the reason text (`basis_reason`), on purpose.
- Widening it is a product-semantics change. It is not a demo step.

**Rejected: accepting PARTIAL.** It loses MG-8 on the fuel beat (§9s.1).

**The change (K9, `T/demo_combined.py` `performance_and_prebuild`, `:631`):**
```python
for site in ("KOBO-001",) + (("KISIWA-001",) if "kisiwa" in self.story().get("sites", ()) else ()):
```
- `story.json` exists before the children run (`:481`). `performance_and_prebuild` is first called from `finish` → `tick` (`:592`).
- The serve loop's ticks then rerun Kisiwa's comparison as they do Kobo's: a new report after new assessments, so the gate never goes stale on a rehearsal day.
- R3r's cutover basis **stays**. It answers the separate S2 Evidence gate (Overview and board `source`).

**What changes on screen (honest).**
- Kisiwa's dispatch Findings and their money appear where the stored data has them. The Kisiwa board day of night 1 (local 2026-10-28/29) shows the MG-2 fuel-cost earnings.
- MG-8 settles. The boards read AVAILABLE.
- The Performance source reason on Kisiwa's screens becomes the report's own empty-set statement. Its system wording goes to the post-rehearsal plain-language polish batch and does not block.

**Proof (K9, extend KIS-OV; no new row).**
- KIS-OV also asserts that the newest Kisiwa Performance report is `outcome == "PASSED"` and `empty_set is True`, read through `build_performance_comparison_reports().latest("KISIWA-001")` in the served environment.
- It asserts that the S−5d and S boards read `read_state == "AVAILABLE"`, which replaces R3r's "reported, not asserted".
- L0 self-test: add fail bodies for a FAILED report and for a PARTIAL board.

### 9s.3 (b) Expectations: KIS-7 is rewritten from data; KIS-6 and CH5D1-O1 unchanged

**Real data has no priced Kisiwa Finding on S.**
- The two PRICED fuel-cost-2 heads are both on night 1 (2026-10-28 17:40–19:05Z and 22:55Z – 10-29 00:15Z).
- `lead_finding` (`chain/read.py:176-198`) picks a head only if its episode overlaps the board day `[local 00:00 S, +1 d)`.
- So Kisiwa is truthfully **unpriced on S** even with the gate open. R3q's KIS-7 premise ("Kisiwa priced on S") was wrong, and its item 4 ("never re-expected to the one-Site path") is withdrawn.
- **No story change.** Adding a priced consequence on S would tune data to a check.

**KIS-7 (replaces §9q.2 KIS-7).** It is pure in `demo_rows.kis7`, with its expectations derived from stored rows and never typed:
1. **S summary.** Run main's `optimize_card(s_body, KOBO, allowed=(KOBO, KISIWA))` (K8, data-tolerant, one-Site and ≥2 paths).
2. **Kisiwa on S matches the data.** `expected_s` = whether some Kisiwa dispatch Finding with a PRICED latest money head (KIS-2's head and interval reads) has an episode overlapping Kisiwa's S local day. Assert `(KISIWA in priced codes) == expected_s`. On the current story `expected_s` is False and Kobo alone is priced; that is reported.
3. **Kisiwa priced where the data is.** `d1` = the Kisiwa local date of the earliest PRICED head's episode start. Read `GET /api/sites/KISIWA-001/outcome-board?date=<d1>`. Its OPTIMIZE_COST `earnings` has a value, and `earnings_money(claim)["amount_high"]` equals the stored money head's `amount_high` for the lead head of that day.
4. **No sum.** `never_summed` runs over the S and week summaries and the Portfolio week body whenever two or more Sites are priced in any of them. Otherwise it is reported as "≥2 path not reached on real data" and stays covered by the L0 self-tests.
5. **L0:** pass bodies for the one-Site S and for priced `d1`; fail bodies for "Kisiwa priced on S while `expected_s` is False", "`d1` unpriced", "`d1` amount differs" and "a summed string".

**Unchanged.**
- **KIS-6:** its cells equal the board in either state.
- **CH5D1-O1** (main, K8): it already allows one or two priced Sites from `(KOBO, KISIWA)`.
- **Prerequisite:** K9 must merge main (96d597573, K8) before the prepare, since `optimize_card`'s `allowed` and the K8 re-expectations are not on K9 yet. That merge was needed for the rehearsal anyway.

### 9s.4 (c) Owner K9, before the rehearsal prepare, after one clone probe

Order:
1. Merge main into K9.
2. Make the §9s.2 change and the KIS-7 rewrite, then commit.
3. **Clone probe (about 20 minutes).**
   - Use a fresh `*_test` clone of `assetops_demo3_kisiwa_test` and a **copy** of `AssetOpsV1-k7f\var\demo3_kisiwa`. The K7-F folder itself is never written.
   - Record the R3r basis.
   - In the prepare's environment, run `python -m assetops_backend.performance_migration run --tenant demo --site KISIWA-001`.
   - Serve and record the following, before and after:
     - the report outcome and `empty_set`;
     - the S−5d and S boards' `read_state` and failed ports;
     - MG-8 state;
     - the `d1` board's Optimize earnings;
     - whether the estate Findings list holds Kisiwa's fuel Finding row (K8's after-coverage join);
     - the Kisiwa rows check-all runs on that DB.
4. The delta review (same addendum as R3r): only High or Medium findings block.
5. The 2-hour prepare.

**Stops (report to the Architect; no patch, no prepare):**
- **S-s1:** the Kisiwa report is not PASSED, or the gate is still closed after it.
- **S-s2:** any Kisiwa row passes before and fails after.
- **S-s3:** a board still reads PARTIAL after the report, with any failed port.
- **S-s4:** `d1` is unpriced after the report.

### 9s.5 (d) Size, path, tripwire

- **K9 +0.15:** 0.02 for the loop line, 0.06 for the KIS-7 rewrite, 0.02 for the KIS-OV extension, and 0.05 for the probe.
- Pre-rehearsal work is about 0.8–0.85, **over R3q's 0.7 watch line**. This ruling reports it.
- **Critical path about 9.5–9.75.** That is at the tripwire, not over it. The probe overlaps the delta review.
- **If a stop fires and the path would cross 9.75**, the cut options in order are:
  1. Keep the §9s.2 change, and make KIS-7 report-only for this rehearsal, asserting after it (−0.05).
  2. Drop the K8c four-Site Kisiwa Overview capture to the post-rehearsal batch (−0.05).
  3. Fall back to PARTIAL: revert the loop line, state the board's partial notice and MG-8 UNKNOWN honestly, and keep the S−5d board link out of the demo script (−0.1). This loses the fuel beat's outcome status, so it needs the owner's acceptance.

  Only option 3 is an owner question, and only if it is reached.
- **Plan HTML (coordinator):** the rulings table gains "DIESEL-1-R3s: Kisiwa Performance gate closed → board PARTIAL, MG-8 (fuel) unsettled via FINDING:UNEXPLAINED_FUEL; fix = product's own empty-set Performance comparison for KISIWA-001 in performance_and_prebuild (PASSED only on clean lineage; not the q12-6 basis); KIS-OV asserts PASSED/empty-set and AVAILABLE boards; KIS-7 rewritten from data (Kisiwa truthfully unpriced on S; priced on its night-1 board day; no story change); KIS-6/CH5D1-O1 unchanged; K9 merges main first; clone probe stops S-s1..S-s4; K9 +0.15; path 9.5–9.75".

### 9s.6 Owner questions

None now. Cut option 3 (§9s.5) becomes one only if a probe stop forces it.

## 9s2. Ruling DIESEL-1-R3s2 — R3s addendum: why Kisiwa's board days never settle (probe stop S-s4)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only code reading in `AssetOpsV1-k9` (f994e3cf9, d2c62c73c) and the probe's board JSON (`k9r3s/out/`, the "after" files). No DB, no suites.

### 9s2.1 Cause: Kisiwa has no subject for `productive_kwh`. A prepare will not fix this

The causal chain, READ:
1. **The measure set.** MINIGRID measures are `productive_kwh` (ASSET), `daylight_headroom_kw` (SITE), `critical_served` (SITE) and `avoidable_gen_min` (ASSET) (`chain/measures.py:44-59`).
2. **The subjects.** The subjects of `productive_kwh` are the Site's assets with `supply-use = PRODUCTIVE` (`chain/measure_impls.py:131`, `mini_depth/read.py:378-391`). Kisiwa declares `ESSENTIAL_SERVICE`, `HOUSEHOLD` and `HOUSEHOLD` only (`T/demo_combined_kisiwa.py:62`). So the builder writes **no `productive_kwh` row on any Kisiwa day** (`chain/builder.py:57`, one row per subject).
3. **The calendar.** Kisiwa has no calendar entry, so it takes the all-day default (`config/chain/operating-calendar-v1.json`). No NOT_EXPECTED row covers the day.
4. **Settlement.** `day_settled` needs a row for **every** measure (`chain/read.py:92-98`). So every Kisiwa board day is unsettled.
5. **Gaps.** `_day_grades` (`:53-60`) counts a missing measure as NO_DATA. So `day_gaps` names every day, which gives "31 of 31 days are not assessed yet" even on days whose dispatch was assessed. `chain/reader.py:59-82` counts the same way.
6. **The board.** `settled_day` is False, so `base` is False (`site_outcomes/mini.py:521`). MG-1 to MG-7 are PRODUCER_NOT_SETTLED. `money_head` needs `settled` (`chain/read.py:438`), so the d1 Optimize earnings read "Not known yet" even though the Finding and the price exist.

**A prepare-side contributor (fixed by a real prepare, but not sufficient).** The clone never had `after_children`'s `backfill-a` snapshot build, because that runs only when all three core Sites are present (`T/demo_combined.py:530`, `:561`). A four-Site prepare runs it for every tenant Site, Kisiwa included (`chain/backfill.py:111-155`). Step 4 still fails there, so S-s4 would recur in the rehearsal.

**Site-list audit (every list that could leave Kisiwa out):**

| List | Kisiwa included? | Effect |
|---|---|---|
| `evidence_migration` (`demo_combined.py:585-588`) | No (Kobo only) | covered by R3r's basis |
| Performance loop (`:631`) | yes after R3s | — |
| Objectives (`:576-584`) | No (core only) | by design (R3p Q3). MG-8 "NO_OBJECTIVE" on S is that honest state |
| `drain_mini` | yes (`:589`) | — |
| `after_children` / `backfill-a` | yes (all tenant Sites) | — |
| Tick | yes | `--max-sites 5` covers 4 Sites. The 240 s cap can defer a Site to the next tick through the fair cursor, which is not an exclusion |
| Prebuilt routes (`config/chain/prebuilt-routes-v1.json`) | No: `days.json` boards only | the first Kisiwa board open is a cold build, not a wrong one. **Presenter note:** open the S−5d Kisiwa board link once before the client joins |

No other list leaves Kisiwa out.

**MG-8 on d1 (UNKNOWN, PRODUCER_NOT_SETTLED) is correct.** MG-8 settles from night D−1's fuel window (`mini.py:521-525`). d1 is 2026-10-28, and night 10-27 has no window because night 1 is 10-28.

### 9s2.2 Probe: none needed to decide; the rehearsal goes ahead now

- No tick or prebuild run on the clone can create a `productive_kwh` subject. The cause is decided by code.
- **Optional, non-blocking (5 minutes, SELECT only, on the clone):** count Kisiwa snapshot rows by measure and confirm that `productive_kwh` is absent. If the builder runs it, the result goes in the packet.
- In the rehearsal itself, KIS-OV's AVAILABLE-board assertion stands; the probe showed AVAILABLE.

### 9s2.3 MG-8 "state null" on S−5d is not a defect

- The probe read the S−5d Protect row's `lead_outcome`, which carries only `{key, label}` (`{"key": "MG-8", "label": "Fuel accounted for"}`).
- The row itself reads `NEEDS_ATTENTION`, with the `unexplained_fuel` node for night 10-31 (95.7–144.3 L, 119.57–180.43 USD). So the K4b fuel beat renders.
- The K9 packet quotes the row state and the MG-8 entry from the board's outcome list.
- **Stop:** only if that outcome entry itself carries a null state.

### 9s2.4 Changes, owners, size, path

**Before the rehearsal (K9, about +0.01).**
- KIS-7 item 3 (d1 priced) and R3s stop S-s4 become **report-only for this rehearsal**, with the reason quoted: "d1 is unsettled: no `productive_kwh` subject (R3s2)". This is R3s cut option 1.
- KIS-7 items 1, 2 and 4 stay asserted. Item 2's `expected_s` is False and is observed False.
- No product code changes before the prepare. **The rehearsal prepare starts after the delta review.**

**The product fix is a separate unit, `DIESEL-K10` (measure applicability). It is built only if the owner says yes (§9s2.5).**
- **Rule.** An ASSET-kind measure with no snapshot row anywhere in the read's day range is not applicable to that Site. It is left out of `day_settled`, `readiness_of`, `day_gaps` and the `chain/reader.py` counts, **provided** at least one other measure has a row on that day.
  - A day with no rows at all stays unsettled.
  - A missing SITE-kind measure stays NO_DATA.
  - A subject declared part-way through the range keeps its earlier days unsettled, which is conservative.
- **Why it is sound.** The builder writes a row for every subject on every built day, including NO_DATA rows. So a measure missing from the whole range means the Site declares no subject for it. It does not mean "not built yet".
- **Where.** One shared pure helper, `applicable_measures(rows, measures)`, in `chain/read.py`, called by `ChainRequest.day` and by `chain/reader.py`'s counts. One helper keeps the COH coherence pairs equal.
- **Tests.**
  - A Kisiwa-shaped day (no `productive_kwh` rows) settles.
  - Kobo-shaped rows are byte-equal to before.
  - An empty day stays unsettled.
  - A missing SITE measure stays a gap.
  - A mid-range subject case.
- **Proof.** Serve the rehearsal DB with the K10 code. This is a read-side change, so no re-prepare. If `serve` cannot swap the tree, the proof and the Kisiwa board captures move to the demo-day prepare.
  - d1 earnings are priced, equal to the stored head's `amount_high` (KIS-7 item 3 asserted again).
  - The Kisiwa gap text names only the days before Kisiwa's first evidence.
  - Kobo, Cold and EV board bodies are unchanged on the story days.
- **Size and path.**
  - K10 is about 0.25: code 0.05, tests 0.08, review 0.05, served proof 0.07.
  - It overlaps the 2-hour rehearsal, so the path becomes **about 9.6–9.85, which can cross the 9.75 tripwire**.
  - Without K10, the path stays **about 9.5–9.75**.
- **If K10 is approved and crosses the tripwire, cut in this order:**
  1. Move the K8c four-Site Kisiwa Overview capture to the demo-day prepare (−0.05).
  2. Move the Service empty-default-day check (R3r §9r.4) to the polish batch (−0.02).
  3. Cut K10's served proof to Kisiwa d1 and S−5d only (−0.03).
- **Polish batch either way:** "N of 31 days are not assessed yet" also counts the days before the Site existed. That is a wording item.

### 9s2.5 Owner question

**Should the Kisiwa board days settle for the demo?**
- **Without K10.** The Kisiwa board's Protect row (the unexplained-fuel beat) renders correctly. But Grow, Optimize and Assure read "Unknown", and the board says "31 of 31 days are not assessed yet" beside an assessed fuel Finding. That is honest by the current rule, but it contradicts itself on screen.
- **With K10** (+0.25, path about 9.6–9.85, may cross the 9.75 tripwire), those rows settle and the d1 fuel-cost money shows.
- **Architect recommendation:** yes, K10. The contradiction sits on a demo beat. Use cut 1 first if the path crosses.
- **Default until the owner answers:** the rehearsal runs without K10, and K10 is not started (owner 2026-11-05, no new commitments).
