# DD lane-wide pre-flight: every remaining part (22 Nov 2026)

Architect (Claude, kept DD lane Architect), under the owner's DD strategy (`owner/owner-dd-strategy-2026-11-22.md`;
`.ai/ROLE_CONFIG.md` "DD strategy"). Rulings: **D-DD.117 to D-DD.142** (`rulings.md`, round 16). Checked read-only
against main `965fc4d17`, `task/DD3c-unit-roles` `09bd3ba99`, `task/DD4-cold-ev-reality` `a5c7e9515`,
`task/DD4b-ev-measured` `8d519ef49`, and `M` by key. Builders follow this file and the rulings; any other question
keeps the builder's default, recorded in the packet and confirmed by the reviewer (strategy (b)). A mid-build round
is for a surprise only.

## 1. Questions by part, sorted

B = BLOCKER (ruled), M = model question (ruled), D = default the builder follows (no Architect round).

### DD3c parts 3-5 (`task/DD3c-unit-roles`, part 2 building)
- M: fuel balance on a multi-unit Site (one `generator_asset_id` column) → **D-DD.117** (lead unit; per-unit burn;
  digest and terms change only above one unit; no migration).
- D: dispatch_v3 pv sum, minimum-runtime from the lead, verification through `unit_roles`, replay refusal, Kobo
  roles-5 parity → **D-DD.118** (= D-DD.110, D-DD.114); `fuel_basis` is not on DD5's bulk path → backlog line.

### DD4a remaining (`task/DD4-cold-ev-reality`)
- B: cold books for the writer (`books_for` is mini-grid only) → **D-DD.119** (in-process ledger from
  `build_cold_exports`, byte check against the exported ledger, `f_m` from the view).
- M: Thika's events (incidents are outside the view) → **D-DD.120** (module table, `M` parity).
- D: C-DD6 live by vertical, pending clauses named → **D-DD.121**; writer run, output, timings → **D-DD.122**.
- Order unchanged: D-DD.89 `M` commit and sweep → cold books → writer run → `test_dd4_thika_incident.py`, C-DD6.

### DD4b (`task/DD4b-ev-measured`)
- B: branch predates the join and D-DD.98 (built spare is a ninth night bus) → **D-DD.123** (merge main after DD4a,
  `VERTICAL_RUNS`, seven-element rows, rotation and daytime spare rebuilt, measured hooks, bands from tariffs).
- D: cold bill profile, account, tariff code, statements (EV without revenue), `meter_billed`, C-DD5/7/20 judges →
  **D-DD.124**.
- M: `M`'s capacity stage pools energy one bus cannot draw (D-DD.98; owner: "Readings stand") → **D-DD.125**
  (per-charger bound in the structure, Kasarani November restated; new DD4.5).
- EV session ids for sealing → D-DD.139 (the writer adds a `session` object to in-session EV rows).

### DD3b (not started; branch `task/DD3b-mini-units`)
- B: Kisiwa failure instant 18:40 (operations) vs 19:10 (spec); August outage omitted → **D-DD.126**.
- M: no v9; FAILED cannot be entered in v8's lifecycle → **D-DD.127** (v9's own lifecycle, POINT forcings, one-unit
  fast path).
- D: Kisiwa/Mto kit missing in `/2` and `/1`, stale 400 L tank ratings, `pv-array-share` → **D-DD.128**.
- D: writer single-unit throughout, sun calendar applied to every Site, hidden `.get` defaults → **D-DD.129**.
- M: purchases vs consumption in the books (`EMU_FUEL`, C-DD4's fuel nodes) → **D-DD.130**.
- M: D-DD.92's deferred leaf-by-leaf list → **D-DD.131** (each leaf by its stated rule; no remainder line).
- D: pure-run checks without a database → **D-DD.132**.
- Not a question: D-DD.92's owner answer is in (`owner-demo-data-answers-2026-11-22.md`: "Revisit a plant figure",
  then "Approve 18:00 peak"); the honest result is the smaller Kobo story.

### DD5 (not started)
- B: world conversions publish no v4 metadata; EV depot channels are not in any closed table → **D-DD.138**.
- B: §4.6's batch shape cannot hold a 5-minute day (256 envelopes) → **D-DD.139** (split; one sequence per source;
  v3 for mini-grid; one builder; exit 2; ids incl. EV sessions).
- M: inputs folder (telemetry staging, `sealed/` outside the digest, F's place, C5/C6) → **D-DD.140**.
- M: disorder files are not loader-legal; TENANT-1, OOO-1, MAP-1, FX-1, LATE-SETTLE-1, CLOCK-1 → **D-DD.141**.

### DD6 (after DD5b; IA-P2 is merged)
- B: C8 cannot pass while any cell is pending → **D-DD.133** (PENDING with closing unit passes; subprocess call;
  C-DD15 from the world manifest; C-DD17 served; C-DD10 Lakeside only).
- B: `<slug>.statements.json` never reaches WK; walk definition fixed at `/1`; `serve --tenant` missing →
  **D-DD.134**.
- B + owner: `demo_workflow` items cannot be made by the product's commands as named, nor with past due dates →
  **D-DD.135**, **D-DD.137** (owner questions O1-O3 below).
- D: keep-awake, cap, evidence path, the ten runbook notes → **D-DD.136**.

## 2. Owner-level questions (plain language; default applied now)

- **O1. Should the demo run on the story's date?** The demo's "today" is 6 Nov, 06:00. The product checks action
  due dates against the real clock, so seven of the nine demo actions (due 6-20 Nov) are refused, and no decision or
  action from the demo script can be created. A story clock for the demo worlds only is a 2.0 u unit (`WK-SC`).
  *Recommendation:* yes, build it after DD6. *Default if no answer:* not built; the Decisions, Actions and Results
  pages show their empty state, listed as pending. *Moves:* 0 → 10 demo decisions and 9 actions on the served demo.
- **O2. Who is shown as deciding?** The product lets only an operator's executive agree an action or choose an
  option; the scenario names Site managers and finance leads. *Default:* the executive is the one who agrees and
  chooses; the manager stays named as the one who proposed it. *Moves:* the name on each decision and action.
- **O3. The Decisions and Actions pages do not yet list decision records (6a) or agreed actions (3C2).** They read
  older stores. *Default:* logged to the IA-P lane as a page gap; DD reports those cells as pending. *Moves:* nothing
  in DD; it decides whether O1's items are visible once made.
- **Told, not asked** (each follows an earlier owner answer):
  - Kasarani with a charger out: about 7 missed departures and about $840 in penalties in November, not 2 and $240,
    and the decision model now agrees with the readings (D-DD.125; "Readings stand").
  - Kobo's October fuel restated from the plant: about 634 L, candidate about 25 L, bridge about −$31 (was 1,180 L,
    330 L, −$412.50); Kisiwa and Mto restated the same way (D-DD.131; "Approve 18:00 peak").
  - Kisiwa's generator 1 fails at 18:40 on 30 Oct (19:10 is when it was reported), and its August outage (14-17 Aug)
    is now in the readings (D-DD.126).

## 3. Build plan, sizes and shared files

| Slice | Parts (u) | Size | Starts when |
|---|---|---|---|
| DD3c | parts 3, 4, 5 of 5 | 3.25 (unchanged) | now (part 2 building) |
| DD4a | D-DD.89 `M` commit; cold books + writer run; Thika test + C-DD6 | 5.5 (unchanged) | now |
| DD3b | DD3b1 v9 pack 2.0; DD3b2 writer units 2.0; DD3b3 notes and leaves 1.75 | 5.75 | DD3b1 now; DD3b2 after DD4a merges; DD3b3 after DD3b2 |
| DD4b | rejoin + DD4.3 rebuild; DD4.4; DD4.5 | 4.75 | after DD4a merges |
| DD5a | DD5.1 + D-DD.138-140 | 3.5 | contracts/bindings now-able after DD4a; EV half after DD4b's session rows |
| DD5b | DD5.2 + DD5.3 + D-DD.141 | 3.75 | after DD5a, DD3b3 and DD4.4 |
| DD6 | DD6.1-6.3 + D-DD.133-136 | 4.75 | after DD5b (IA-P2 merged) |

**DD total 49.75 u** (was 44.0; D-DD.142). Each part at or under 6 u. `WK-SC` 2.0 u only on O1's yes.

**Critical path:** DD4a → DD4b (rejoin, DD4.4, DD4.5) → DD5a (EV half) → DD5b → DD6. Off the path, in parallel:
DD3c parts 3-5; DD3b1 now (only `packs/mini_grid.py` and host tests); DD3b2 and DD3b3 after DD4a, which must merge
before DD5b.

**Shared files: build in parallel, merge in this order, the second merges main and reruns its reach set:**
- `M` (scenario manifest) and the D-DD.30 chain: DD4a (D-DD.89) → DD3b3 (D-DD.131) → DD4b's DD4.5 (D-DD.125). One
  `M` commit at a time, each with its rev bump.
- `simulator/.../world/telemetry.py`: DD4a → DD3b2 and DD4b (different functions; whichever merges second rebases).
- `tools/dd_check.py`: DD4a → DD3b2 / DD4b → DD5b → DD6.
- `tools/world_history.py`, `world/exports.py`: DD4a (cold books) → DD3b3 (notes) → DD4b (`--telemetry`) → DD5b
  (FX-1, LATE-SETTLE-1).
- `tools/world.py`, `tools/walk_world.py`: DD5b → DD6.
- No overlap: DD3c (backend `sites/`, `mini_depth/`, `fuel_balance/`, migration 0074) with DD5a (binding service,
  `contracts/`, `evidence/`) or DD4.5 (`structure/rows_ev_depot.py`); DD3b1 with DD4a. DD5a adds no migration (0074
  is DD3c's).

## 4. Reach sets for the shared main baseline (strategy (a))

- **DD3c 3-5:** `backend/tests/test_dd3c_*.py`; every test importing `dispatch_v3`, `actions/verification*`,
  `runs/replay_series`, `fuel_balance/`, `structure/litres/`: incl. `test_0k3_replay_series_postgres.py`,
  `test_w2*_fuel*`/`test_diesel_k*` files, `test_4d_*litres*`; `test_dd1_operator_files.py`,
  `test_dd1_onboarding_postgres.py`, `test_dd1_readiness_parity_postgres.py` (Kobo pins).
- **DD4a:** `simulator/tests/world/{test_dd4_*, test_dd3_telemetry, test_telemetry_join_parity,
  test_scope_seasons_parity, test_dd2b_*, test_history, test_records}.py`; `backend/tests/{test_dd1_check,
  test_dd2_check, test_dd3_datasheet_check}.py`; `test_ddr_rehearsal_postgres.py`; the Layer-4 derived-values and
  mock fixture tests the D-DD.30 chain runs.
- **DD3b:** host `{test_mini_grid, test_mini_grid_v2, _v5, _v6, test_0k4a_dispatch_v8, test_lab_history,
  test_kernel_forcing_index_parity, test_0k4c_season_v2}.py`; simulator `{test_decide_v8, test_cycle_charge_split}.py`
  and `world/{test_dd3_telemetry, test_dd3_site_inputs_cli, test_dd4_span_end, test_telemetry_join_parity,
  test_3a3_exports, test_dd2_nodes, test_dd2_checker_on_emulated_rows, test_dd2b_*}.py`; backend
  `{test_0k4a_profile_words, test_k1_kisiwa_fixtures, test_dd1_operator_files, test_dd2_check, test_dd1_check}.py`.
- **DD4b:** simulator `world/{test_dd4_telemetry_ev, test_dd4_ev_roster, test_dd2b_ev, test_dd2b_books,
  test_dd2b_round7, test_telemetry_join_parity, test_dd4_span_end}.py`; backend `{test_dd4_check (new),
  test_dd2_check}.py`; for DD4.5 every `test_3b*_structure*`, `test_6h*`, `test_6c*` file and those reading
  `golden/6h_parity.json`.
- **DD5a:** `test_ds3_bulk_load{,_postgres}.py`, `test_ds3_parity_postgres.py`, `test_ds3_bench_postgres.py`,
  `test_dd_parity_cold_ev_postgres.py` (new), `test_w200_source_events_postgres.py`,
  `test_w202_cold_replay_postgres.py`, `test_w205a_ev_roles.py`, `test_w205a_ev_foundation_postgres.py`,
  `test_w205b_ev_replay_postgres.py`, `test_w206_ev_store_postgres.py`, `test_w402_authored_v4_postgres.py`,
  `test_w402_cold_enqueue_gate_postgres.py`, `test_s2_evidence_ledger_postgres.py`, `test_dd1_onboarding_postgres.py`,
  `test_dd1_readiness_parity_postgres.py`; host tests importing `cold_publication`.
- **DD5b:** `test_ds4_world{,_postgres}.py`, `test_ds4_batch_days{,_postgres}.py`,
  `test_ds4_bench_pipeline_postgres.py`, `test_wk_walk_world.py`, `test_3a3_load_emulated{,_postgres}.py`,
  `test_dd1_check.py`; simulator `world/*` (exports goldens).
- **DD6:** `test_ds4_world{,_postgres}.py`, `test_wk_walk_world.py`, `test_dd1_check.py`, `test_dd2_check.py`,
  `test_dd3_datasheet_check.py`, `test_ddr_rehearsal_check.py`, `test_on1_served_tenant.py`; simulator
  `world/{test_dd2_checker_on_emulated_rows, test_history, test_dd2_nodes}.py`.

Every slice also runs `tools/checks/statement_catalogue.py` (D-DD.96), check-decision-index and
check-agent-workflow.

## 5. Handoff

All parts are ruled in one series; no open Architect item. Next Architect round only for a surprise, a review High
or Medium that needs a ruling, or the owner's answers to O1-O3.
