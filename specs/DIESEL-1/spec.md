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

