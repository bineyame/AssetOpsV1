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
