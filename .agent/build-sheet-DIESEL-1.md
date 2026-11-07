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
