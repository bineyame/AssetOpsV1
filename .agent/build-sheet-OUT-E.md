# Build sheet OUT-E · cost check after the generator trial, read back on the board (self-contained)

Architect: Claude (`.ai/ROLE_CONFIG.md:9`), 2026-10-30, owner away (decisions delegated; every call is in
`.agent/decisions-while-owner-away-2026-10-30.md`). Code read at main **`833e7c95`** and `task/CC-M-combined-schema`
at **`e7191a88`** (worktree `AssetOpsV1-ccm`). Build after OUT-D merges. Branch **`task/OUT-E-cost-proof`**, worktree
`C:\Users\assef\Bineyame\AssetOpsV1-outE`. Backend paths are relative to `backend/assetops_backend/` unless they
start with `backend/`, `tools/` or `frontend/`.
Design evidence only (do not build from it): `.agent/build-spec-commercial-2026-10-27.md` "CC-D2". Where it and this
sheet differ, this sheet wins. Read nothing else unless a step names it.

**Outcome.** After the generator stop trial ACT-048 is verified at Kobo, the Optimize cost row's Earlier
interventions entry and the Assure row's Verified results line show (1) the modelled cost change per kWh of feeder
demand, labelled "Modelled change after the trial · not realised savings", computed on the trial's own frozen hours,
fuel rate and diesel price, and (2) the Supply cost per kWh objective before and after the trial on those same
hours. A change is credited to the trial only when its verification passed; otherwise the row says
"Status changed; not attributed".

## 0. Rules that bind every unit

- Do not touch `main.py`, `field/ gateway/ contracts/ simulator/ host/ contract-fixtures/`, `estate/**`,
  `outcomes/**` (except reading `outcomes.objectives`), any merged migration. E adds one empty merge revision and
  edits one guard (`configuration-persistence.ps1`, E3).
- No recompute on read, no worker, no annualising, no subtracting the intervention cost from a per-kWh change.
- On screen: no reason code, state code, formula id or policy version. The word "saving" appears only inside
  "not realised savings" (wording test, E4).
- Every string in §4 was scanned against `terms` + `w1.terms` + `w1.codes` + the w1 patterns of
  `frontend/src/test/productVocabulary.json`: 0 hits. "candidate" is forbidden: internal metric names stay internal.

## 1. Code reality (verified)

| Element | Source | Verdict |
|---|---|---|
| CC-M schema | `-ccm` `backend/migrations/versions/0036_cc_mini_contribution.py` (down 0035), `0037_cc_trial_cost_comparison.py` (down 0036): table `trial_cost_comparison_revision`, 3 states, 11 reasons, `DEMO_ACTOR` columns, trigger; test `backend/tests/test_cc_schema_postgres.py`; 20 head-literal files set to `0037_cc_trial_cost_comparison`; review ACCEPT (`-ccm/.agent/CC-M-review.md`) | MERGE |
| D's head | main after OUT-D: `0038_out_objectives` (down 0035); the same 20 files say `"0038_out_objectives"` | two heads → merge revision |
| w303 pair | the 2 failing w303 tests on CC-M are fixed on main | resolved by merging main |
| Frozen hours | `actions/verification_rules.py:378` `window_evidence(start, readings, *, load_asset_ids, ...)`; `_SINGLE_POWER_ROLES` incl. `generator_power` `:371`; `fmt` `:61`; `comparability` `:557`; `source_pair` `:680` | **EXTEND** (`generator_kwh`) |
| Before/after measure | stored outcome metrics `candidate_avoidable_seconds` BASELINE and LATER (`verification_rules.py:746-752`) | OK (read, never recomputed) |
| Verdict gate | `verification_rules.py:785-788`: VERIFIED only on `TARGET_AND_GUARDRAILS_PASS` | OK |
| Evaluation command | `actions/verification.py:742` `evaluate`; `record_evaluation` `:842`; new outcome flag `result["new_outcome"]` `:858` | **EXTEND** (hook) |
| Summary read | `actions/verification.py:966-971` `summary()` → board port `verification` (`site_outcomes/read.py:222-223`) | **EXTEND** |
| Fuel rate | generator `specific-fuel-consumption` L/kWh (`mini_depth/inputs.py:186`, `mini_depth/rules.py:591`); `postgres_action_store.py:587` `reserve_history` is the SQL shape to copy | **EXTEND** (`sfc_history`) |
| Price | `financials/fuel_cost.py:422` `PriceSelection`, `:440` `select_window_price`, `:81` `MULTIPLIER` | OK |
| Board Earlier item | `site_outcomes/board.py:423-440` `{text, href, result_label}`; frontend `ItemList` (`frontend/src/sites/OutcomeBoard.tsx:104-121`, used `:204`); type `OutcomeEarlierItem` (`outcomeBoardClient.ts:98-100`) | **EXTEND** (`detail`) |
| Assure line | `site_outcomes/mini.py:560-574` `VERIFICATION_TEXT["VERIFIED"] = "{code} verified on test data"` | **EXTEND** |
| MG-2 objective | OUT-D: `outcomes/objectives.py` `MEASURES["avoidable_generator_minutes"]`, `judge`; board `SiteFacts.objectives` | OK after D |
| Kobo VERIFIED data | `tools/s602b_test_scoped_cases.py:38` `CASES` has no plain verified case (`withdrawn` reaches VERIFIED then withdraws) | **EXTEND** (`verified` case) |
| Mock | v70 shows ACT-048 before verification only (`outcomes.js:67-68,75`) | register (§6) |

## 2. Units (5). Effort 3.75 builder days including one full suite

### E1 · Merge the schema, merge revision, docstrings · 0.5 d · per-unit review
- In `-outE` on main: `git merge task/CC-M-combined-schema` (first `git -C AssetOpsV1-ccm merge main` is **not**
  needed; merge the branch into E directly). Conflicts are expected only in the 20 head-literal files: resolve each
  to `"0039_merge_objectives_cc"`. Keep CC-M's `test_cc_schema_postgres.py` `HEAD` = `"0039_merge_objectives_cc"`,
  `PREVIOUS` unchanged (`0035_w5_ev_work`, a downgrade target). `mini_depth_probe.py:22` `MINI_HEAD` likewise.
- New `backend/migrations/versions/0039_merge_objectives_cc.py`: `revision = "0039_merge_objectives_cc"`,
  `down_revision = ("0037_cc_trial_cost_comparison", "0038_out_objectives")`, empty `upgrade`/`downgrade`, docstring
  "Joins the productive-use and trial cost check schema with the declared objectives table."
- Reword only the docstrings of 0036 and 0037 (no code, constants or SQL): replace the planning labels "(D1, roadmap
  R4)", "(D2, roadmap R3)", "lands with CC-D2" with outcome words: 0036 "the productive-use contribution what-if
  kind"; 0037 "the modelled cost change after a verified generator trial; the writer is
  `financials/adapters/postgres_trial_comparison_store.py`".
- Test: `alembic heads` is exactly `{"0039_merge_objectives_cc"}`; `test_cc_schema_postgres.py`,
  `test_out_d1_schema_postgres.py` and the 20 files pass (`pg_harness.assert_at_head`).

### E2 · Pure cost comparison and generator energy · 0.75 d · per-unit review
Files: new `financials/trial_fuel_comparison.py`; `actions/verification_rules.py` (`window_evidence`); tests new
`backend/tests/test_out_e2_trial_comparison.py`, extend `backend/tests/test_s6_verification_rules.py`.
- `window_evidence` returns one more key `generator_kwh`: sum of the slots' `generator_power` kWh, `fmt`, null if
  any slot is unknown. It is **outside** `plan_sha256` and **not** added to stored outcome `details` (stop if either
  would change). `full_window` test helper gains `gen_kw="20"` with defaults that keep every caller byte-identical.
- `trial_fuel_comparison.py` (pure; `Fraction` arithmetic): the CC-D2 interfaces kept as designed:
  `FORMULA = "trial-fuel-comparison/1"`, `REASSESSMENT_STATES`, `REASSESSMENT_REASONS` (the 11, **same order and
  spelling as 0037's `REASONS`**; a test imports both and asserts equality), `WindowFacts`, `OutcomeFacts`,
  `InterventionCost`, `compare(baseline, later, outcome, sfc_in_force, prices, intervention_cost) -> dict`.
  Reason precedence, compute (fuel = SFC × generator kWh, upper × `MULTIPLIER`; cost = fuel × price; per kWh of
  feeder demand; change = baseline − later; IMPROVEMENT iff nominal change > 0) and `basis_sha256` exactly as the
  CC-D2 section "Reason conditions", "Compute" and "Output split" of the design spec. Output adds nothing else.
- Tests: worked example (generator 40/28 kWh, feeder 120/126 kWh, SFC 0.3, price 1.25, cost 0) →
  `change_per_demand_kwh == {"nominal": "1/24", "upper": "11/240"}`, per-window cost per kWh `"0.125"` / `"1/12"`;
  one isolating test per reason and the precedence order; change 0 → MODELLED_NO_IMPROVEMENT.

### E3 · Writer: store, hook, fuel rate, guard, verified case · 1.25 d · per-unit review
Files: new `financials/adapters/postgres_trial_comparison_store.py`; `financials/composition.py`
(`build_trial_comparison_ports(url)` → store + `price_selection`); `actions/adapters/postgres_action_store.py`
(`sfc_history`); `actions/verification.py` (`_replay`, hook); `actions/composition.py` (calls
`financials.composition.build_trial_comparison_ports`; only `financials/composition.py` imports the adapter);
`tools/checks/configuration-persistence.ps1` (+ probe test like `tools/checks/test_estate_guard.py`);
`tools/s602b_test_scoped_cases.py`; `backend/tests/test_s6_verification_evaluator_postgres.py` helper
`complete_windows` (+ `baseline_gen_kw="20", later_gen_kw="20", baseline_load_kw="10", later_load_kw="10"`, defaults
byte-identical); new `backend/tests/test_out_e3_trial_comparison_postgres.py`.
- Store: `append(row) -> (row, inserted)` idempotent on `(verification_outcome_id, basis_sha256)` and on
  `(action_id, idempotency_key)` with the same `payload_sha256` (other payload → `IDEMPOTENCY_KEY_REUSED`);
  `revision_no` = previous + 1, `supersedes` = previous; `latest(tenant, site, outcome_id)`. INSERT-only.
- `sfc_history(tenant, site, generator_asset_id, lo, hi, known_at) -> list[SfcValue]`: the `reserve_history` SQL
  shape over the generator component's `specific-fuel-consumption`; generator = the plan basis' bound
  `generator_power` asset. Compared by value.
- `_replay(tenant, site, plan, outcome)`: the evaluator's own `_windows`, `rules.comparability`, provenance →
  `rules.source_pair` at `known_at = outcome.recorded_at` (`verification.py` ~598-610). No new loader.
- **Hook only** (no new route; decided). In `evaluate`, after `record_evaluation` commits a **newly inserted** final
  outcome (VERIFIED, INEFFECTIVE or INCONCLUSIVE), in its own transaction: compute and append with
  `idempotency_key = f"auto:{outcome_id}"`, the evaluation's SYSTEM demo actor and grant basis,
  `intervention_cost = {amount: "0", currency: null, source: "Generator stop setting changed; no direct cost
  declared"}`. A replayed evaluation does not run it. Any exception → nothing appended, logged, **never a rollback**
  of the outcome; the read then shows "Not calculated yet".
- Guard: `$trialComparisonWriter` in `$pgWriters`; `@('trial_cost_comparison_revision')` INSERT-only, only that
  writer, INSERT-seen counter; probe test proves the check fails with the writer removed.
- Producer: s602b gains case `verified` (added to `CASES` and its description map), built as the design spec's
  "Authored windows for `verified`": `complete_windows(..., baseline_gen_kw="40", later_gen_kw="28",
  baseline_load_kw="60", later_load_kw="63")`, then the `withdrawn` case's steps up to its first VERIFIED evaluation
  and no further; diesel price `publish_assumption.main(["fixture", "--site", "KOBO-001", "--file",
  "backend/conversions/demo-diesel-price-publications.json", "--step", "v1"], store=...)` after the Finding cases and
  before the evaluation. Case output records `outcome_id`, the two window bounds and `pinned_at`.
- Postgres test (fresh `assetops_out_e_trial_test`): `verified` → one revision, `MODELLED_IMPROVEMENT`, nominal
  `"1/24"`; re-POST of the same evaluation (replay) → still one revision; `inconclusive` → `UNAVAILABLE` /
  `OUTCOME_INCONCLUSIVE`; `target_miss` → `MODELLED_NO_IMPROVEMENT`, nominal `"0"`; an injected store failure leaves
  the outcome recorded and no revision. Record `plan_sha256` before and after: equal.

### E4 · Read-back on the board · 0.75 d · slice review (shared seam)
Files: `actions/verification.py` (`summary`), `site_outcomes/board.py`, `site_outcomes/mini.py`,
`frontend/src/sites/outcomeBoardClient.ts:98-100`, `frontend/src/sites/OutcomeBoard.tsx:104-121`; tests new
`backend/tests/test_out_e4_readback.py`, `frontend/src/sites/__tests__/outcomeBoard.test.tsx` (extend), new
`backend/tests/test_out_e4_readback_postgres.py`.
- `summary()` adds (additive; existing keys unchanged), for the outcome the current state names (null when none):
  `"cost_check": {state, reason, nominal, upper, currency, recorded_at} | null` from `latest(...)` (`nominal`/`upper`
  = `change_per_demand_kwh` strings, currency = stored `price.currency`) and
  `"trial_hours": {"before_seconds": int | null, "after_seconds": int | null}` from that outcome's stored metrics
  `candidate_avoidable_seconds` BASELINE/LATER.
- `mini._actions`: `ActionFact` gains `cost_check: Mapping | None = None` and `trial_hours: Mapping | None = None`
  (last fields, defaults keep B fakes).
- Board (`_row` Earlier, `board.py:431-434`): the ACT entry in a MOVES category gains `"detail": str | None`, the
  parts below joined by " · ", null when no part applies. Every other Earlier item gets `"detail": None`.
  1. **Cost line** (Optimize cost row only): `cost_check` MODELLED_IMPROVEMENT → "Modelled change after the trial ·
     not realised savings: {lo}–{hi} {currency} less per kWh of feeder demand" (`lo`/`hi` = nominal/upper rounded to
     3 decimals, half-even, via `Fraction` → `Decimal`; one figure when equal); MODELLED_NO_IMPROVEMENT →
     "Modelled change after the trial · not realised savings: no lower cost per kWh of feeder demand"; UNAVAILABLE →
     "Modelled change not calculated: {reason words}"; `cost_check` null on a final outcome → "Not calculated yet".
  2. **Before/after line**, only when the row holds the MG-2 objective (OUT-D), its target is 0 and both
     `trial_hours` values are known: before = `judge(MG-2 objective, Reading(before_seconds/60, True, None))`, after
     likewise. VERIFIED → "Supply cost per kWh before the trial: {missed|met} · after: {missed|met}"; not VERIFIED
     and the verdicts differ → "Status changed; not attributed"; not VERIFIED and equal → "Supply cost per kWh:
     {missed|met} before and after the trial". A non-zero target gives no line (R593).
- Assure (`mini.py:571`): VERIFIED with MODELLED_IMPROVEMENT → "{code} verified on test data · modelled change
  {lo}–{hi} {currency} less per kWh of feeder demand"; otherwise the existing text.
- Frontend: `OutcomeEarlierItem.detail?: string | null`; `ItemList` renders `{item.detail ? <small>{item.detail}
  </small> : null}` after the note, inside the `<li>` (no new class; the list's `small` style). Vitest: detail shown,
  absent when null, vocabulary scan, and `/sav(e|ed|ing)/i` matches only inside "not realised savings".
- Unit tests (fake ports): every Cost-line state and the 11 reason words; rounding (1/24 → 0.042, 11/240 → 0.046);
  equal bounds → one figure; before/after attributed vs not attributed vs unchanged; no line without a MG-2
  objective or with a non-zero target; Assure text.
- Postgres (DB `assetops_out_e_board_test`): s602b `verified` built in a child as `test_out_b4_board_postgres.py:292`
  does, `_pin_kobo` with the case's `pinned_at`, OUT-D's `declare_objective` fixture for KOBO-001, board on the UTC
  day of the later hour's end (`day=` param). Assert the Cost row Earlier ACT-048 entry: result label as today's
  VERIFIED label; detail = "Modelled change after the trial · not realised savings: 0.042–0.046 USD less per kWh of
  feeder demand · Supply cost per kWh before the trial: missed · after: met" (before/after from the authored windows:
  baseline > 0 s, later 0 s; record if the data differs and assert the recorded text); Assure line; no reason code in
  the body text.

### E5 · Captures, register, full suite · 0.5 d · slice review
- Captures 1440 and 390: Kobo Overview on the `verified` DB, Cost row and Assure row open; the same page on the
  `inconclusive` DB (Cost line "Modelled change not calculated: the trial result is not determined"). Record pairs vs
  v70 in `.agent/OUT-E-packet.md`.
- Register §6. One full backend run (migrations) and one full `npx vitest run`.

## 3. Wire (additions only)

Verification summary: `cost_check {state, reason, nominal, upper, currency, recorded_at} | null`, `trial_hours
{before_seconds, after_seconds} | null`. Board `earlier[].detail: string | null`. Schema versions unchanged.

## 4. Copy (exact; scanned, 0 hits)

"Modelled change after the trial · not realised savings: {lo}–{hi} {currency} less per kWh of feeder demand" · "…: no
lower cost per kWh of feeder demand" · "Modelled change not calculated: {words}" · "Not calculated yet" · "Supply
cost per kWh before the trial: {missed|met} · after: {missed|met}" · "Status changed; not attributed" · "Supply cost
per kWh: {missed|met} before and after the trial" · Assure "{code} verified on test data · modelled change {lo}–{hi}
{currency} less per kWh of feeder demand".
Reason words: OUTCOME_INCONCLUSIVE "the trial result is not determined" · WINDOW_INCOMPLETE "a comparison hour is
incomplete" · NOT_COMPARABLE "the two hours are not comparable" · SOURCE_NOT_COHERENT "the two hours come from
different sources" · EVIDENCE_REPLAY_MISMATCH "the readings changed after the result was recorded" ·
GENERATOR_KWH_UNKNOWN "generator energy is not known for both hours" · ZERO_DEMAND "an hour had no demand" ·
SFC_MISSING "the generator fuel rate is not recorded" · SFC_DIFFERS "the generator fuel rate differs between the
hours" · PRICE_MISSING "no diesel price covers both hours" · PRICE_BASIS_DIFFERS "the two hours were priced from
different diesel price records". Intervention cost source (stored, not shown): "Generator stop setting changed; no
direct cost declared".

## 5. Validation tier

| Unit | Focused backend | Frontend |
|---|---|---|
| E1 | `test_cc_schema_postgres.py test_out_d1_schema_postgres.py` + the 20 head-literal files | — |
| E2 | `test_out_e2_trial_comparison.py test_s6_verification_rules.py` | — |
| E3 | `test_out_e3_trial_comparison_postgres.py test_s6_verification_evaluator_postgres.py` + s602b users (`python tools/select-tests.py --base main` lists them) + `tools/checks/test_estate_guard.py`-style probe | — |
| E4 | `test_out_e4_readback.py test_out_e4_readback_postgres.py` + the OUT-D U4 set | `npx vitest related --run <changed>`, `npx tsc --noEmit` |

`tools/check-all.ps1` at every unit commit. Slice end: **one full backend run** (`-Tier all`, idle machine) and one
full `npx vitest run`. If `fixtures/s6_verification_api_contract.json` pins the summary's exact keys, add only the two
new keys and list them in the packet.

## 6. Register rows (R590-R596)

- **R590** · E E4 · mini · D2 · standing. Mock: ACT-048 before verification only. Shown: after verification, the
  Earlier entry carries the modelled cost line and the before/after line.
- **R591** · E E4 · mini · D3 copy honesty · standing. The cost change is modelled per kWh of feeder demand on the two
  trial hours, never a saving; the intervention cost is stated as zero and not subtracted.
- **R592** · E E3 · verification · D1 · standing. No command to re-run the cost check with another intervention cost
  or a republished price; the stored check stands "as calculated", and a failed check reads "Not calculated yet".
- **R593** · E E4 · mini · D4 reading · standing. Before/after uses the Supply cost per kWh objective only when its
  target is 0, because the trial hours are one hour each and the objective is per day.
- **R594** · E E4 · mini · D2 · standing. The Assure Verified results line adds the modelled change.
- Resolve nothing else. R542's note (OUT-D) stands.

## 7. Pre-flight checklist (answer in one batch before code, then stop)

- [ ] Worktree on main after OUT-D (`alembic heads` = `0038_out_objectives`); `git log task/CC-M-combined-schema -1`
  is `e7191a88` or a later docs-only commit; list the conflict files after the merge before resolving.
- [ ] `git ls-files --eol | grep "eol=lf" | awk '$2=="w/crlf"'` empty; `.venv` junction; PYTHONPATH as OUT-W §7.
- [ ] `0037` `REASONS` and the design spec's `REASSESSMENT_REASONS` are identical (they are at `e7191a88`).
- [ ] Kobo generator SFC: in an s602b build, `sfc_history` for the plan's generator over both hours returns exactly
  one positive value (expected 0.3 L/kWh). If not, stop and ask (do not author a fuel rate here).
- [ ] The v1 diesel price covers both authored hours with one revision (expected 1.25 USD/L).
- [ ] `plan_sha256` and stored outcome `details` unchanged by `generator_kwh` (record both before E2 code).
- [ ] s602b `verified` reaches VERIFIED with `later_generator_off` (0 later seconds) and baseline > 0 s; record both.
- [ ] Vocabulary as OUT-D §7; plus "candidate" never on screen; "saving" only in "not realised savings".
- [ ] DB names `assetops_out_e_<x>_test`, dropped by the fixture.
- [ ] `grep -c "| R59[0-6] " .agent/mock-departure-register.md` is 0.

**Known failures:** as OUT-W §7. Any other failure blocks.

## 8. Acceptance

1. CC-M merged with only docstring rewording; one head `0039_merge_objectives_cc`; both schema tests green.
2. Pure worked example and every reason pass; the reason list equals the DB CHECK.
3. A new final outcome appends exactly one cost-check revision (INCONCLUSIVE → not calculated, with its reason); a
   replay appends none; a writer failure never removes the outcome.
4. Kobo `verified`: Cost row Earlier ACT-048 shows "Modelled change after the trial · not realised savings:
   0.042–0.046 USD less per kWh of feeder demand · Supply cost per kWh before the trial: missed · after: met"; Assure
   shows the verified line with the modelled change. On a not-verified outcome no change is credited to the trial.
5. Guard registers the writer and fails without it; full backend, full vitest and `check-all` pass, except the known
   failures.

## 9. Review points

- **E1:** no SQL or constant change to 0036/0037; merge revision empty; head literals only where they mean head.
- **E2:** `generator_kwh` outside `plan_sha256` and `details`; exact `Fraction` arithmetic; reasons equal the CHECK.
- **E3:** hook only on a newly inserted final outcome, own transaction, never a rollback; INSERT-only writer; producer
  case additive (no existing case's output changes).
- **E4:** no recompute on read; before/after only on target 0 and known seconds; attribution only on VERIFIED; no
  code on screen; wording test.
