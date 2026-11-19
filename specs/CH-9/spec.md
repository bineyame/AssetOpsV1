# Build sheet CH-9: the daylight-window solar read, single-source studies and "run the mill at midday" before/after

- Architect: Claude, 2026-11-04 (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). Rulings are logged in the plan as **CH9-R**. Rulings marked **(away)** are Architect calls while the owner is away; owner to review (`.agent/decisions-while-owner-away-2026-11-04.md` D-AW-7, D-AW-8).
- Plan: `Docs/demo-sprint/client-demo-plan.html` §2.1 CH-9 row (4 units, lane 2 after MD-0), OD-P2 (rebased onto CH-1b and CH-4, no CH-8), §2.5.1 (the CH-9 day becomes one DD-1 injected story day), §2.5.4, §4.2 CH-9 row, §4.4 (Kobo trimmed partial prepare).
- Design: AG-17, §5b.1 levers `productive-load-midday@1` and plan `midday-productive-shift-1`, §5b.6 composite row, §15 CH-9.
- Register: **I-17** (the opportunity value line never appears). Carried: CH4-R R3 (`headroom_kw` + `window_hours`), MD-CH4-5 ("mixed sources"), the CH-1a/CH-1b labelled keep "one-noon-hour basis".
- Branch: `task/CH-9-daylight-read`, cut from main after MD-0 merges. Paths: `B/` = `backend/assetops_backend/`, `M/` = `backend/migrations/versions/`. Lines are to main `a07452c63`.

## 0. Result and boundary

**Observable result.**
- Kobo's spare solar is assessed over every hour of its **declared daylight window**, not the 12:00–13:00 hour. A day snapshot `daylight_headroom_kw` grades the whole window.
- An opportunity study reads all daylight hours of its 5 days. When the study's readings are single-source it is SUPPORTED, and the value line appears: "{lo}–{hi} kW over {h} daylight hours on every eligible day" (I-17).
- A Kobo story day "run the mill at midday" carries a domain Action from the headroom thread. The Grow row and the opportunity page show a measured **before/after**: midday productive use on fully checked days before and after the change.

**Not in this slice.**
- The `GEN_WHILE_SPARE_SOLAR` composite (CH-8 catalogue; labelled keep).
- A verification plan family for a second lever. Lifecycle VERIFIED for this Action is not reached in CH-9 (R6).
- The DD-1 baseline itself. CH-9 delivers the story-day kind and proves it on a trimmed partial prepare; DD-1 injects it.

## 1. Rulings (CH9-R)

> **Revised 2026-11-04 (OWN-1104).** R1, R2, R3 and R6 below are **superseded by §9**. R4, R5, R7 and R8 stand, with "declared daylight hours" read as "measured daylight hours" (§9 R1). §9 adds R9 (full-day MG-5). Where §3, §5, §6 and §7 conflict with §9, §9 wins. The size is now 5 units.

| # | Gap (code reality) | Ruling |
|---|---|---|
| R1 **(away)** | "Declared daylight window": nothing declares one. Noon is fixed in three places: `B/mini_depth/worker.py:35` `RENEWABLE_LOCAL_HOUR = 12` (used `:117`), the SQL enqueue functions in `M/0029_w4_mini_depth.py:190,257,295` (`extract(hour …) = 12`, and `:190` raises otherwise), and the read `B/mini_depth/read.py:98-117` (`local_noon`). The calendar file is keyed by Site, but editing it changes `calendar_version` and re-revisions every demo snapshot (D-AW-1). | **A separate declaration, `config/chain/daylight-window-v1.json`**: `{"KOBO-001": {"from": "HH:MM", "to": "HH:MM", "source": "<reviewed file:line>", "label": "Declared daylight hours"}}`. Its own version, so `calendar_version` does not change. The hours come **from a reviewed source, never chosen to fit**: pre-flight P1 names the Kobo PV profile's own production span (the `kobo-daytime` reference scenario's daylight offsets, or the Site's PV model config). If no reviewed source exists, the builder stops and the Architect rules. D-AW-8. |
| R2 | The SQL enqueue cannot read a JSON file. | **Migration `0046_daylight_hours`**: table `mini_daylight_hour(tenant_id, site_id, local_hour smallint, declaration_version text, recorded_at)`, append-only (0030-style triggers, downgrade refuses once a row exists). The three 0029 functions are replaced (`CREATE OR REPLACE`) so renewable work is enqueued for a local hour **in that Site's declared rows**, and for the noon hour when a Site has none (unchanged behaviour for every other Site). One writer, `declare_daylight_hours(site_code)` in `B/mini_depth/daylight.py`, reads the JSON and appends rows; it is called by the Site setup the demo prepare uses (P2) and by MD-0's seed (fixture change by this ruling: Kobo gains its declaration). Guard registration for the new writer (P4). |
| R3 | The Python side. | `RENEWABLE_LOCAL_HOUR` is replaced by `store.daylight_hours(site_id)` (the declared hours, or `(12,)`). `reconcile` (`worker.py:117`) and `hour_windows` (`read.py:98-117`) use it. The read keeps its refusals. |
| R4 | The study reads noon heads only (`B/mini_decisions/projection.py:78-101` `day_heads`, store `renewable_noon_heads`, `B/mini_decisions/store.py:337`). | **`mini-opportunity/2`**: each study day reads every declared daylight hour's latest head. The day decision is CONFLICT if any hour conflicts, else LIMITED if any hour is LIMITED, else ELIGIBLE if any hour is ELIGIBLE, else EXCLUDED; a missing hour makes the day missing. The day's headroom is `headroom_on_every_eligible_day` (`B/mini_depth/rules.py:400`) over its eligible hours, and `window_hours` = the number of eligible hours on every eligible day (the minimum). `frozen_result` (`projection.py:163-195`) is otherwise unchanged: the same status rules, the same mixed-source rule. Old `/1` studies stay stored and readable; new studies are `/2`. No threshold is touched. |
| R5 | The day measure. `noon_headroom_kw` (`B/chain/measures.py:46-49`, period `midday`, `B/chain/policy.py:25-27`) is the labelled keep. | New measure **`daylight_headroom_kw`** (MINIGRID, SITE, MEASURED, period `daylight` = the declared hours, threshold 1.0, adapter `mini.daylight_headroom@1`). `measures_for(MINIGRID)` lists it instead of `noon_headroom_kw`. Stored noon rows stay as history. The event register (`config/chain/event-register-v1.yaml`) maps `mini_renewable` to the new measure. The CH-1a/CH-1b keep is closed. |
| R6 **(away)** | "Verified" before/after. The only verification family is the reserve trial (`reserve-trial-1`, s6), and the lifecycle's RESOLVED_MONITORING needs a `verification_outcome` row. A second family is CH-8 lever work. | **Measured before/after, not a verification verdict.** The Action is a domain intent on the headroom thread ("Run the grain mill at midday on sunny days"), so the lifecycle reaches ACTION_ACCEPTED and, with its case completed, ACTION_APPLIED (`B/chain/lifecycle_run.py:62-67`). The comparison `midday_shift` (pure, `B/chain/outcomes.py`) reads `productive_kwh` over the daylight hours on COMPLETE days: before = the last ≤ 3 COMPLETE days before the change's effective day, after = the first ≤ 3 on or after it; it is shown only when both sides have 3 days (design plan `min_days: 3`), else "Not judged yet: {n} of 3 fully checked days after the change". The words say "measured before and after", never "verified". D-AW-7. |
| R7 | The story day. | Kind `mill-midday` in `backend/conversions/demo-story-days-v1.json`, placed by DD-1. It uses an existing scenario if P3 finds one with a productive load in the daylight window; otherwise **one labelled scenario** derived from `kobo-daytime` with the mill's load window moved inside the declared daylight hours, reviewed as data under OD-P13's terms (same model profile and seed, no value chosen to reach a result). The Action is recorded at story time (DD-1 clock seams). |
| R8 | Single source. | No code forces a single source. A study is SUPPORTED only if its readings are single-class (the existing rule). The packet reports the class the trimmed prepare gives. If it is still MIXED, MD-CH4-5 stays and the value line does not appear; that is reported, never worked around. |

## 2. Copy (vocabulary; V guard; MOCK DEVIATION candidates against MA-1 M5)

| Key | Text |
|---|---|
| `VALUE_LINE` (`B/chain/vocabulary.py:17`) | `{lo}–{hi} kW over {h} daylight hours on every eligible day` (replaces "at midday"); one value: `{lo} kW over {h} daylight hours on every eligible day` |
| `potential.value` (CH-6) | `{lo}–{hi} kW of daytime solar unused` (unchanged) |
| `shift.before_after` | `Midday use measured before and after the change: {b} kWh a day on {nb} fully checked days, then {a} kWh a day on {na}` |
| `shift.not_judged` | `Not judged yet: {n} of 3 fully checked days after the change` |
| `daylight.label` | `Declared daylight hours {from}–{to}` |

## 3. Files

| File | Change |
|---|---|
| `config/chain/daylight-window-v1.json` (new) | R1 |
| `M/0046_daylight_hours.py` (new) | R2; `down_revision` = main's head at branch time (`pg_harness.alembic_head()` in tests) |
| `B/mini_depth/daylight.py` (new), `B/mini_depth/store.py`, `worker.py:35,117`, `read.py:98-117` | R2, R3 |
| `B/mini_decisions/projection.py`, `store.py:337`, `worker.py` | R4 (`mini-opportunity/2`) |
| `B/chain/measures.py`, `measure_impls.py`, `policy.py`, `config/chain/event-register-v1.yaml` | R5 |
| `B/chain/outcomes.py` (CH-6a), `B/chain/vocabulary.py` | R6, §2 |
| `backend/conversions/demo-story-days-v1.json`, `config/scenarios/` (only if R7 needs it) | R7 |
| `backend/tests/fixtures/mechanism/mechanism-v1.json`, `backend/tests/mechanism_dataset.py` | Kobo's daylight declaration (Architect ruling under MD-0 §7) |
| `F/sites/MiniOpportunity.tsx:115-130` | renders the server value line and the before/after text |
| `tools/checks/configuration-persistence.ps1`, `tools/checks/test_estate_guard.py` | only if P4 requires the writer registration (then the estate guard self-tests run) |

## 4. DS-R1, OL-1 and mock deviations

| Item | Touched how | Resolution |
|---|---|---|
| One-noon-hour solar basis (`worker.py:35`, `0029:190,257,295`, `read.py:114`, `measures.py:46-49`) | Replaced | **Fixed** (R2–R5) |
| "at midday" value line | Edited | **Fixed** (§2) |
| The composite `GEN_WHILE_SPARE_SOLAR` | Not built | **Labelled keep → CH-8** |
| `reserve-trial-1` as the only verification family | Not edited | **Labelled keep → CH-8 / SWEEP-DS** (R6) |

**OL-1.** No outcome link is added. The new measure names no outcome; the potential record (CH-6a) keys on `SIGNAL:PRODUCTIVE_USE_HEADROOM`, which is unchanged. The ratchet baseline does not grow.

**MOCK DEVIATIONS.** MD-CH9-1: the value line's daylight wording. MD-CH9-2: the before/after line has no mock place (opportunity page and Grow Potential part).

## 5. Test ladder

1. **L0** `tools\run-host-tests.ps1 -- backend/tests/test_ch9_daylight.py`:
   - the declaration parser (refuses a missing `source`, `from ≥ to`, an unknown Site);
   - the R4 day-decision truth table (each order of CONFLICT / LIMITED / ELIGIBLE / EXCLUDED / missing hour);
   - `window_hours` and the headroom over eligible hours;
   - `midday_shift` with 0–3 days on each side;
   - the §2 texts.
2. **L2** `backend/tests/test_ch9_daylight_postgres.py` (`pg_harness.fresh_database()`): 0046 upgrade; the enqueue functions accept every declared hour and still refuse an undeclared non-noon hour; a Site with no declaration keeps noon; downgrade refuses once a row exists; append-only.
3. **L2m** on `mechanism_db()` (MD-0 §7): Kobo D12/D13 are eligible over the daylight window and the busy days are not; W2 is `mini-opportunity/2`, SUPPORTED, with `window_hours` reported; `daylight_headroom_kw` COMPLETE on delivered days, NO_DATA on GAP-K7. Every changed MD-0 value is listed old → new.
4. **§4.4 partial prepare:** `tools/demo_combined.py --db assetops_polish_ch9_test --work var/polish_ch9 prepare --sites kobo --days <the mill-midday day and the days its study and before/after need> --no-finish`, then settle-style tick, collect, check. Report: the study class (R8), the value line, the before/after text. Drop the scratch DB and folder.
5. **Existing, scoped:** `test_w402_*`, the mini_decisions projection tests, `test_ch4_*`, `test_ch1a_*` measure tests, `test_event_register.py`, `test_ch6_*`.
6. **Frontend:** `npx vitest related --run src/sites/MiniOpportunity.tsx`.
7. **Guards:** A, W, V; the estate guard self-tests only if the guard is edited.

## 6. Pre-flight (answer from code, batch them, then stop)

- **P1.** The reviewed source of Kobo's daylight hours (file:line), and the span it gives. If none exists, stop (R1).
- **P2.** Where the demo prepare sets up Kobo (the call that should run `declare_daylight_hours`), and MD-0's seed step 1.
- **P3.** Whether any existing scenario in `config/scenarios/` puts a productive load inside the daylight window (R7); its name and offsets.
- **P4.** Whether the new writer and reader need estate-guard registration (`configuration-persistence.ps1`), with line numbers.
- **P5.** Every reader of `renewable_noon_heads`, `RENEWABLE_LOCAL_HOUR`, `noon_headroom_kw` and `VALUE_LINE`.
- **P6.** The cost: hours enqueued per Kobo day before and after (1 → n), and the expected tick-time growth on a 24 h day (report against the CH-1b stage bound).

## 7. Size: 4 units

- u1 (1.25): R1–R3, 0046, the writer, the worker and read changes, L2.
- u2 (1): R4 study `/2`, R5 measure and register, L0/L2m.
- u3 (0.75): R6 `midday_shift` and copy, the frontend line.
- u4 (1): R7 story-day kind, the partial-prepare proof, the packet.

## 8. Review focus

- The daylight hours come from a named reviewed source, never chosen to fit.
- Sites without a declaration behave exactly as today.
- No threshold or status rule changed; old studies stay readable.
- The before/after never says "verified".

## 9. Revision OWN-1104 (Architect 5, 2026-11-04; owner agreed "all as recommended")

| # | Ruling |
|---|---|
| R1 (replaces R1) | **Daylight is measured, per Site and per day, from `pv_available_power`** (`B/mini_depth/rules.py:67` `PV_AVAILABLE`; input `B/mini_depth/inputs.py:35`). There is no declaration file. **Why `pv_available` and not `pv_power`:** output is curtailed when batteries are full and load is low, which is exactly the spare-solar case this read exists to find. Daylight defined by output would hide the hours it is meant to measure, a definition that depends on load, which would be circular. Availability is what the array could produce, independent of curtailment. **Rule:** a local hour is a daylight hour on day D when the hour holds the expected `pv_available_power` readings and every one is > 0, so the sun is up for the whole hour. Dawn and dusk partial hours are not daylight hours. Zero is the physical bound, not a chosen threshold. An hour with missing `pv_available_power` readings is a **missing hour** (R4), never a non-daylight hour. A Site with no `pv_available_power` binding keeps noon, unchanged. |
| R2 (replaces R2) | **Migration `0046_daylight_enqueue`** replaces the three 0029 enqueue functions (`M/0029_w4_mini_depth.py:190,257,295`) with `CREATE OR REPLACE`. Renewable work is enqueued for a Site-local hour when an accepted `pv_available_power` reading in that hour is > 0, and for the noon hour as today when the Site has no `pv_available_power` binding. The `:190` "raise otherwise" becomes "refuse an hour with no positive `pv_available_power` reading". **No table and no writer.** The worker decides the hour's daylight status by the R1 rule, so a reading trigger cannot mark a partial hour as daylight. `down_revision` = main's head at branch time. There is no `daylight-window-v1.json` and no MD-0 fixture declaration; the MD-0 §7 CH-9 row loses that item. |
| R3 (replaces R3) | `RENEWABLE_LOCAL_HOUR` (`B/mini_depth/worker.py:35`) is replaced by `store.daylight_hours(site_id, day)`: the R1 hours for that day, from the stored readings, or `(12,)`. `reconcile` (`:117`) and `hour_windows` (`B/mini_depth/read.py:98-117`) use it. The read keeps its refusals. `window_hours` in R4 is the number of eligible daylight hours on every eligible day, so it varies with season and cloud. That is honest and is stated on the line. |
| R6 (replaces R6) | **"Run the mill at midday" is verified, in CH-9b** (`.agent/build-sheet-CH-9b.md`, the design's `midday-productive-shift-1`). CH-9 records the domain Action and its apply (ACTION_ACCEPTED → ACTION_APPLIED) and builds nothing of the comparison. `midday_shift` and the `shift.before_after` copy move to CH-9b as that plan's evaluator and its text. The §2 row `shift.before_after` and the R6 review-focus line ("never says verified") are deleted from CH-9. |
| R9 (new; D-AW-6 reversed) | **Full-day MG-5.** New day measure **`critical_served`** (MINIGRID, SITE, MEASURED, period = the Site's declared operating hours from the operating calendar, Kobo 24 h; adapter `mini.critical_served@1`). Its value is `{served_kwh, demand_kwh, unserved_kwh}` over the critical-load channels of the roles-3/roles-4 configuration. Its grade is the coverage of those channels over the period, with the same coverage threshold the other MINIGRID measures use in `B/chain/policy.py` (P8 names it; no new value). `measures_for(MINIGRID)` lists it. MG-5's KPI reads it through a CH-6a `kpi` record and `judge`, unchanged, over COMPLETE days only (CH6-R R5-R6). The one-noon-hour MG-5 read (`B/site_outcomes/mini.py:526-527,543-545`) is deleted, and the board says the basis in words ("over the whole day"). EV-2 stays "not measured · needs vehicle odometer data" (no source). |

**Pre-flight additions** (replacing P1, P2 and P4):
- **P1.** Confirm `pv_available_power` is bound on Kobo in roles-2/3/4, and in which simulator scenarios it is emitted. If it is never emitted, stop.
- **P7.** The cost: daylight hours per Kobo day on the DD-1 scenarios, mini-depth jobs per day (1 → n), and the tick growth against the CH-1b stage bound.
- **P8.** The critical-load channel roles (demand, served) in roles-3/4, the existing coverage threshold to reuse, and every reader of the noon MG-5 path. If there is no served/unserved signal, stop.

**Tests (replacing the declaration cases):**
- L0: the R1 hour rule (all > 0, one zero, a missing reading, dawn); the `critical_served` adapter truth table.
- L2: 0046 enqueues positive-PV hours only; a Site with no PV binding keeps noon.
- L2m: Kobo daylight hours per day; `critical_served` COMPLETE on delivered days and NO_DATA on GAP-K7; MG-5 judged over COMPLETE days.

**Files:**
- removed: `config/chain/daylight-window-v1.json`, `B/mini_depth/daylight.py`, and the MD-0 declaration;
- added: `M/0046_daylight_enqueue.py`; the `critical_served` entry in `B/chain/measures.py`/`measure_impls.py`; the MG-5 `kpi` record (CH-6a `CONTRIBUTIONS`, owned here if CH-6a has merged, else noted for CH-6a).

**Size: 5 units.**

| Unit | Content |
|---|---|
| u1 (1) | R1–R3, 0046, L2 |
| u2 (1) | R4 study `/2`, R5 measure |
| u3 (1) | R9 `critical_served` and MG-5 |
| u4 (1) | R7 story-day kind and the partial-prepare proof |
| u5 (1) | Action recording, frontend value line, packet |

**Review focus (added):**
- Daylight is measured from availability, never chosen.
- Sites without PV behave exactly as today.
- MG-5 is judged on whole days.

## 10. Pre-flight rulings CH9-R2 (Architect 8, Claude, 2026-11-05; pre-flight `AssetOpsV1-ch9\.agent\CH-9-preflight.md` at `5af83b877`)

P1, P3, P5, P7 and P8 are accepted as facts. These rulings amend §9 and §1 R4/R7. Where they conflict, §10 wins. **Size stays 5 units.** Q2's period helper is the same one `critical_served` needs, so it adds no code.

- **Q1, MD-0 busy days: default accepted.** `busy_noon`'s charge request spans the 06:00–18:00 solar block, so a busy day means demand takes the solar for the whole day, as MD0-S5 M2(A) intended. Spare-solar D12/D13 are unchanged. MD-0 keeps a real day-level EXCLUDED case next to its ELIGIBLE days. This is a labelled fixture change (`CH9-R2:Q1`) that keeps the fixture's declared role; it is not a value chosen to hit a result. The template rebuild is needed anyway, because 0046 and the worker are fingerprinted. **Add the per-hour proof** at L0: one busy hour among eligible hours gives an ELIGIBLE day with `window_hours` reduced by one, and that hour's row EXCLUDED with CHARGE_OBLIGATION_ACTIVE.
- **Q2, missing vs not assessed: overridden.** The default's "first to last reading" span lets a run that stops early read as a shorter, clean window. It hides undelivered hours, which is what the pre-flight rightly rejects for MG-5 in Q6. There is one rule for both measures:
  - The **expected hours** of a day are the Site's declared operating hours from the operating calendar: Kobo 24 h, the same period as `critical_served`. One helper serves both.
  - Inside that period, an hour that is not fully covered by `pv_available_power` readings at the cutoff is a **missing hour** (§9 R1). §1 R4 then applies unchanged: any missing hour makes the study day missing.
  - **Daylight hours** are the fully covered hours with every value > 0. Night hours with zero readings are covered and not daylight. A day with no pv reading at all is missing (GAP-K7).
  - **Consequence, reported and never adapted:** current 8 h Kobo story days (06:00–14:00 local) become missing study days, and MG-5 is PARTIAL on them (Q6). The packet lists every study and thread whose state changes on the polish clone. Their `expected-today.json` entries are owned changes, owner DD-1.
  - **For DD-1 (a pre-flight item for its Architect, not a CH-9 task):** apply the already-agreed direction "extend the story days to their declared hours using existing scenarios only". A story day is the full declared day, with the story run in its hours and the steady scenario in the rest. The DD-1 Architect sizes it.
- **Q3, hour membership: default accepted, one clarification.** An interval that crosses an hour boundary counts, clipped, toward each hour it overlaps, through the existing `rules._coverage` union. "Every value > 0" is over every reading that overlaps the hour. The cutoff is `received_at <= k`.
- **Q4, who applies the rule: default accepted.** 0046 enqueues coarsely: any positive reading, plus the late-feeder case and noon for Sites with no binding. The worker's job semantics are unchanged. Exactly **one** function, `daylight_hours(site, day, cutoff)`, built on the Q2 period helper, is read by `reconcile`, `hour_windows`, `read_selected_renewable_basis` (`read.py:510`), `day_heads` and the measure. An AST or grep test asserts that no other noon or daylight literal remains in those five places.
- **Q5, `mini-opportunity/2` shape: default accepted.** `day_rows` keeps its keys and adds `window_hours` and `hours[]`. There is one `selected_hours` pin per daylight hour. The result's `window_hours` is the minimum over eligible days. `/1` stays readable, branched on `model_version`.
- **Q6, MG-5 on story days: default accepted.** PARTIAL on 8 h days is the honest grade ("not measured over the whole day"); the packet reports it. The period is never shortened to the hours that ran. The DD-1 item under Q2 removes the cause in data, not in the rule.
- **Q7, `critical_served` source: default accepted.** It sums the stored per-hour `mini_service` heads at the cutoff, with no new reading query. An operating hour with no service head counts as uncovered.
- **Q8, `mill-midday`: default accepted.** `kobo-daytime` v1, 03:00–15:00 UTC, received 16:00, with no new scenario. The Action is recorded at story time and its case completed (ACTION_ACCEPTED → ACTION_APPLIED). Under Q2 this 12 h day is itself a missing study day and PARTIAL for MG-5 until DD-1 fills it, so the partial prepare proves the kind, the measured daylight hours (expected 12 on this scenario; report whatever the data gives) and the Action. The study class is proven at L2m on MD-0's full days. R8 is reported as found.
- **Cost (P7):** about +15–28% mini-depth jobs, accepted. The tick growth on the polish clone is reported against the CH-1b stage bound, which is not changed.
- **Lane-1 overlap:** the expected conflicts in `chain/vocabulary.py` and `site_outcomes/mini.py` against CH-5a2b are resolved by whichever slice merges second, keeping both sides' edits local to their named functions. Neither slice waits for the other.

## 11. Build rulings CH9-R3 (Architect 9, Claude, 2026-11-05; handoff `AssetOpsV1-ch9\.agent\CH-9-handoff.md` at `a21d58440`)

**Size: CH-9 goes from 5 to 4.5 units.** The Action part of u5 moves to CH-9b, which grows from 2.5 to 4.5 units. Net +1.5 on lane 2.

- **Q1, u5 blocked: (b), deferred to CH-9b.** The contract change is named and sized below.
  - **Facts.** Every Action store requires an origin Finding:
    - `action`, the Kobo/mini store, needs `origin_finding_id` plus a revision, NOT NULL with an FK (`0016_action_store.py:55,74-76`).
    - `domain_action` is COLDCHAIN-only (`0033_w5_cold_work.py:44`), so it is the wrong table for Kobo in any case. The handoff's "domain Action" should read "Kobo `action` (MINI_TRIAL)".
    - `chain_action_thread.origin_finding_id` is NOT NULL, and its trigger matches on it (`0042_chain_threads.py:81-109`).
    - `link` finds the thread only through `finding_thread_occurrence.finding_id` (`postgres_thread_store.py:50-51`).
    - `verification_plan` references `action` (`0019_verification_core.py:91`). So CH-9b's mill verification needs the mill Action to be an `action` row.
  - **(c) is rejected.** No Kobo Finding is about the mill or the daylight headroom. The headroom is an opportunity by CH-4's design: `SIGNAL:PRODUCTIVE_USE_HEADROOM` and the `_THREAD_SIGNAL_MECHANISMS` map key. Hanging the Action on an unrelated Finding would put it on the wrong thread and outcome.
  - **(a) in CH-9 is rejected.** At about 2 units it would take CH-9 past the 6-unit cap. The consumer of the change is CH-9b's verification, so the change and its proof belong in one slice.
- **The contract change: CH-9b, new first part "R0. Actions from an opportunity", 2 units.**
  - **Migration.** Allocate it in the CH-9b pre-flight, after CH-9's 0046.
    - On `action`: add `origin_opportunity_id` and `origin_opportunity_revision_id`, both NULL, with FKs to the mini opportunity and its study revision. The CH-9b pre-flight names the revision table.
    - On `action`: `origin_finding_id` and `origin_finding_revision_id` become NULL-able, with a CHECK that exactly one origin pair is set. This is `DROP NOT NULL`, with no row rewrite, so the append-only rules are unchanged.
    - On `chain_action_thread`: the same exactly-one-of pair. The trigger matches on whichever origin is set.
  - **Port.** `link_action(kind, action_id, origin)` takes a `Source`-style origin (Finding or opportunity). It resolves the thread through `finding_thread_occurrence` on the matching column. There is one function, and the Finding path is byte-unchanged. `link_all` passes whichever origin the row has.
  - **Readers (the bulletproof part).**
    - Every reader of `action.origin_finding_id` / `origin_finding_revision_id` is listed in the CH-9b pre-flight.
    - Each one either filters to Finding-origin Actions explicitly or handles both origins.
    - A guard test (AST or grep over `B/`) fails on any new unlisted reader of those columns.
    - An L2 test proves that a Finding-origin Action's board, Actions-list, thread and verification bodies are byte-equal before and after the migration.
  - **The lifecycle.** The headroom thread then reaches ACTION_IN_HAND and CHANGE_APPLIED through the existing `lifecycle_run` mapping, with no new state. CH-4 R6 SUPPORT_LOST ("with no linked Action") then sees the link. The CH-9b pre-flight adds one L2 test of R6 with a linked Action, so the opportunity is not withdrawn.
  - **OL-1.** Unchanged. The thread's mechanism still maps to its signal key, so the Grow (MG-1) row is where the Action and its verification show.
  - **API and recording.** The mill Action is recorded at story time against the opportunity, as R7/Q8 intended. Its ACTION_ACCEPTED → ACTION_APPLIED proof (L0 and L2) moves here from CH-9 u5.
- **CH-9 now ships:**
  - u5's copy part (VALUE_LINE and `MiniOpportunity.tsx`), Q2 below, and the packet.
  - There is no product stub. The headroom thread has no Action until CH-9b, and the board and opportunity page already render "no action" for that case.
  - The packet records the deferral as a Known Deviation, citing this section.
- **Demo story.** The Grow mill story (opportunity → Action → change made → verified) completes in CH-9b. That was already the plan for the verified step. DD-1 places the story day after CH-9b, unchanged.
- **Q2, `EstatePortfolio.tsx:423` "kW at midday": in CH-9 (DS-R1, fixed when touched; about 0.1 unit).**
  - CH-9 makes the label false: the headroom is now over measured daylight hours.
  - If the Portfolio opportunity item already carries the server's value line or `window_hours`, render that server copy (AG-29).
  - Otherwise replace the literal with one constant, "kW over daylight hours", labelled as a MOCK DEVIATION candidate and passed through guard V. CH-6b moves it to server copy when it rebuilds the card.
  - The test at `estatePortfolio.test.tsx:435-436` is an owned change.
- **Q3, `kobo-daytime` v2: confirmed.** Q8's "v1" was a wrong version number, not a rule. The rule is "an existing registered scenario, no new scenario". v2 is the only registered version and resolves under the L2 test. Record it in the packet as a fact, not a deviation.
- **Q4, SCENARIO_BASIS_MISMATCH: pre-ruled.** A scenario that pins one hour a day does not match a `/2` study with several hours in a day. That is an honest mismatch. It is never hidden, and no pin is re-cut to fit.
  - **If builder 6 finds it on a demo-visible surface on today's data:**
    - The surface must say it in plain language. If the existing copy for that code is plain and passes guard V, nothing changes.
    - If it shows a raw code or system words, CH-9 adds one server sentence, for example "This what-if was set for one hour a day, so it can't be compared with a study over {h} daylight hours." Treat it as a MOCK DEVIATION candidate through guard V, about 0.1 unit inside the 4.5.
    - The packet lists the surface, the screen and the data row.
  - **The scenario-pin contract** (multi-hour pins) is not in CH-9 or CH-9b. It goes to the post-demo list. If the demo script needs a Kobo what-if, it goes back to the Architect at DS-1.

## 12. Packet rulings CH9-R4 (Architect 11, Claude, 2026-11-05; packet `AssetOpsV1-ch9\.agent\review-packet-CH-9.md` at `ec34b487d`)

**Size: CH-9 goes from 4.5 to 5.75 units** (F1 +1, F2 +0.25, F3 0). This is under the 6-unit cap, so there is no split. The merge stays blocked until F1 and F2 are closed and the L3 A/B is re-run.

### F1, `critical_served` NO_DATA: option (a), refined, fixed in CH-9 (+1 unit)

- **Facts (verified at `ec34b487d`).**
  - `rules._service_row` already computes the per-row `unserved_kwh` (request minus delivery, per segment, on a SUPPORTED row).
  - `projection._service` drops it from the stored rows (`mini_depth/projection.py:145-148`).
  - The site card `unserved_kwh` is stated only when every row is SUPPORTED (`rules.py:~607`).
  - The adapter (`chain/measure_impls.py:248-259`) has a second defect besides the NO_DATA. Even when every row is SUPPORTED, it adds the **critical** `critical_delivered_kw` to the **all-load** `unserved_kwh`. That mixes two load populations, so its `demand_kwh` has no single meaning.
- **The measure's meaning (R9):** the service of the critical load over the whole operating day. So every figure comes from the one CRITICAL row, and from the one series pair its unserved figure is computed from.
- **Mechanism:**
  1. **Store the fact the rule already computes.** `projection._service` writes each row's `unserved_kwh`. It is null unless the row is SUPPORTED, exactly as the rule returns it. No rule changes.
  2. **`MODEL_VERSIONS["service"] = "mini-service/2"`** (explicit; the other domains stay `/1`).
     - The bump is required, not cosmetic. Revision reuse is keyed on `(model_version, input_sha256)` (`mini_depth/store.py:215`), so without it a re-run would return the stored `/1` revision, which lacks the field.
     - `/1` heads stay readable.
     - The pre-flight lists every reader of the service model version or literal.
  3. **The adapter reads the CRITICAL row only.** For each hour:
     - The head's `rows` must have exactly one `role == "CRITICAL"` row, and that row must be `assessment == "SUPPORTED"` with a stated `unserved_kwh`. Otherwise the hour is uncovered.
     - served = that row's `delivered_kw` × 1 h, which is the same feeder series the unserved figure was computed against.
     - unserved = that row's `unserved_kwh`.
     - demand = served + unserved.
     - The covered span is that row's own `coverage` minus its gaps.
     - The adapter no longer reads `cards.unserved_kwh` or `critical_delivered_kw`.
     - A `/1` head does not state the row figure, so it is uncovered. It is never inferred.
     - UNCLASSIFIED rows never affect the measure.
  4. **Re-derive stored hours: migration 0047, enqueue only.**
     - For every Site-local hour whose selected service head is `mini-service/1`, it calls the existing `mini_enqueue_hour(..., 'service', ...)`.
     - There is no row rewrite, no new worker and no change to job semantics. Append-only is unchanged.
     - Downgrade is a no-op. Jobs are work, not state, and the docstring says so.
     - The pre-flight confirms the `p_cause` argument to pass (the head's newest cited evidence id, or the existing convention), and that no other migration path exists. If 0047 cannot be enqueue-only, stop.
     - The CH-1b MINI stage bound is not changed. The packet reports how many ticks or drains polish needs (165 heads) and MD-0 needs (332).
     - MD-0 templates rebuild anyway, because of the fingerprint.
- **Tests (the L0/L2 gap was fixtures that are all SUPPORTED, so the real shape is now mandatory):**
  - **L0 adapter truth table**, built on the stored row shape copied from one real polish head, as follows. **CRITICAL SUPPORTED + UNCLASSIFIED UNKNOWN (no request) → counted.**
    - CRITICAL LIMITED or UNKNOWN → uncovered;
    - two CRITICAL rows or none → uncovered;
    - a `/1` head → uncovered;
    - a gap in the row's coverage → partial coverage;
    - demand = served + unserved.
  - **L0 projection:** a `/2` result carries the per-row `unserved_kwh`, null on a row that is not SUPPORTED.
  - **L2:** 0047 enqueues `/1` service hours only. A drained hour selects a `/2` head. `critical_served` is COMPLETE over a delivered day whose UNCLASSIFIED load has no request.
  - **L2m:** as §9: COMPLETE on delivered MD-0 days, NO_DATA on GAP-K7.
  - **L3:** re-collect polish, MD-0 states and MD-0 close, and redo the CH5a2b-R2 table and the `count_basis` table.
    - Expected: built non-gap MD-0 days grade COMPLETE.
    - Polish Kobo story days grade PARTIAL, as in A: 8 of 24 hours are covered (§10 Q6).
    - Any other result is reported row by row, never adapted.
- **Rejected:**
  - **(b)** derives the same quantity a second time from readings. Two derivations can disagree, and it reverses Q7.
  - **(c)** ships the slice without R9, its own deliverable, and hides MG-5's whole-day basis.
- **In this slice:** yes. R9 is CH-9's. Merging as is would regress every Kobo grade and claim on `main` to "Not known yet".

### F2, two headroom ranges: the study is authoritative (+0.25 unit)

- The opportunity is the study. Its `headroom_on_every_eligible_day` is the headroom that holds in every daylight hour of every eligible day.
  - The value line and the Portfolio already read it (2–8 kW).
  - The 2–20 kW figure is the spread of single-hour headroom across hours. It is a different fact and never names the opportunity.
- **Fix: one source.**
  - `site_outcomes/mini.py:468-475`: the GROW headline figure and the `SIGNAL:PRODUCTIVE_USE_HEADROOM` eligibility read the selected study through the same server read the Portfolio card uses. There is no second computation, and the `renewable.cards.headroom_kw` / `eligible_days` reads are removed from that function.
  - With no study, or no eligible day, there is no GROW headline (the existing fallback).
  - The renewable page's per-hour card stays where it is. The pre-flight quotes its on-screen label. If that label names the opportunity rather than single hours, report it; do not fix it here.
- **Test:** L2 on the MD-0 fixture: the summary figure, the value line and the Portfolio show the same lo–hi. The L3 MD-0 states table shows "2–8" on all three.

### F3, +0.5 s on the Kobo board: accepted, folded into CH-5c/CH-5b

- One condition: the packet lists the arguments of the 4 `read.mini_depth` calls. A same-argument repeat breaks CH-5a R1 and is fixed here, within the 5.75.
- The rest is real work: every operating hour is now read.
  - CH-5c's stored responses carry the warm and pre-built path.
  - CH-5b carries the uncached read.
  - Budgets are unchanged. The F1 fix's re-measure goes in the packet.

### Polish summary row: honest, and DD-1 full-day story days become a hard requirement

- Losing "25–31 kW of daytime solar unused" on polish is the owned consequence of §10 Q2. The 8 h story days are missing study days, so there is no eligible study. The fallback sales line is true data. After F2 the headline reads the study, so the result is the same.
- **DD-1's full-day story days (§10 Q2 item) are now a hard requirement for G5, not a best effort.** Without them, the demo data shows:
  - no Grow opportunity;
  - nothing for CH-9b's mill Action to act on;
  - MG-5 PARTIAL.
- If the DD-1 pre-flight measures the full-day extension above the +50% prepare budget, it goes to the owner then as a measured choice. It is not decided now.
- **Owner:** inform now, nothing to decide (text in the handoff, Architect 11).
