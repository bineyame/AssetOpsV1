## A3-R: ruling on the A3 pre-flight; the consolidated A3 card (Architect, Claude, 2026-11-08)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. A3 worktree `C:\Users\assef\Bineyame\AssetOpsV1-a3`, branch `task/FUEL-A3-kobo-idle-fuel`, cut from main `b70be217b` (MB-1b, PV-1 and WD-1m are in it). `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `T/` = `tools/`.
- **This section replaces §4.3's build detail and is the one card the builder reads.** §4.3's declaration (value, basis, note, effective time) and A2-R1's "key on the presence of `priced_total`, no second sign check" stand.
- READ = I read the code at `b70be217b`. I also ran guard V's own pattern set (`test_out_b2_vocabulary._patterns`, rebuilt from `F/test/productVocabulary.json`) over every literal below: all pass. The builder's G1 finding is confirmed: "ran" and "running" are banned (`simulation and implementation: run`), and so is "load" (`unexplained abbreviations`), so "no load" and "no-load" fail.
- **Git: use `git merge main`, never rebase,** before the copy edits and again before the packet. Do not rewrite the branch's history.

### 0. Code reality the ruling rests on (READ)

- **The board prefixes money to the headline.** `F/sites/OutcomeBoard.tsx:199-200` renders `${boardMoneyText(headline_money)} ${headline}`, so today a priced day reads "0.00 to X USD possible extra fuel cost on this day". After A3's declaration, the three idle mornings become PRICED above 0. They then take the `COST_MONEY` path (`mini.py:508`) **with no copy change**, and `headline_money` already carries the amount. COH-7b (`T/checks/chain_coherence.py:683`), MONEY-B and the Portfolio summary row read `headline_money` as it is.
- **The idle facts are already on the board's money head.** `MoneyHead.body` is the whole consequence read (`B/chain/read.py:438`). For a fuel-cost-2 row its `consequence.model` carries `no_load_fuel_rate_l_per_h`, `no_load_fuel_rate_basis`, `idle_seconds` and `sfc_upper_multiplier`, and `consequence.quantity.high_exact` is exact text (`B/financials/consequence_read.py:107-120`).
- **The money head knows whether it is example data.** `MoneyHead.source_provenance.state` is the consequence's evidence source state. The board already prints it on the Readings line (`mini.py:1106`, `SOURCE_TEXT`). `EXAMPLE_SOURCES` is in `B/chain/vocabulary.py:107`.
- **Import directions.** `site_outcomes/ev.py` imports `mini`, so `mini` must not import `ev` (`duration_text` is out of reach). `actions/` already imports `chain.vocabulary` (`verification_families.py:41`). `board.py` and `mini.py` both import `chain.vocabulary`.
- **The trial cost row stores the shared price.** `result["price"]["value"]` is `fmt(...)` of the one shared price revision (`B/financials/trial_fuel_comparison.py:233-234`). `PRICE_BASIS_DIFFERS` guarantees that a `priced_total` implies one priced revision, so the price exists whenever `priced_total` does. `fmt` gives a decimal string for a terminating value, and a declared price always terminates.
- **The stored `/2` `no_load` block has the rate only** (`trial_fuel_comparison.py:240-241`). `no_load_history` reads one property through `_generator_property_history` (`B/actions/adapters/postgres_action_store.py:637-674`). `basis` (the digest input, `:213-228`) does not include the result's `no_load` block.
- **"Why?" lines.** `why.price_lines` (`B/chain/why.py:109-125`) builds the fuel line from the earnings claim value, and `trace` appends it (`:239-240`). Every `WHY_TEXT` entry is scanned by `test_out_b2_vocabulary.py:94` automatically.
- **No demo rows exist yet.** A `/2` row and a fuel-cost-2 row first appear at the scratch prepare and then at E3.

### 1. Decisions (one line each)

- **G1 (literals): approved, with the board line reshaped** so it extends `COST_MONEY` and the money stays in its usual slot (§2). Basis words say "idle fuel rate", not "no-load".
- **G2: approved.** `_cost_check_read` adds `price_per_litre` (the stored `result.price.value`) only when `priced_total` is present. It is never derived as amount ÷ litres.
- **G3: approved.** `outcome()` adds `fuel_value` (one server line) only when the chosen outcome is VERIFIED and its stored trial row has `priced_total`. The key is absent otherwise. Frontend renders it. **MD-FUEL-A3-1.**
- **G4: option (b), not the builder's (a).** The stored `/2` result's `no_load` block gains `basis`, read with the rate from the same Foundation revision. Reason: the label belongs to the stored fact (the WD-1m-R2 principle: store the class when the result is computed). It needs no second read path, no new port and no fakes, and there are no demo rows to migrate. `basis` stays out of the digest input, so `basis_sha256` is unchanged.
- **G5: approved, with an example-data gate.** `fuel_basis` adds `idle_seconds`, `no_load_basis` and `source_class` to the claim value for a fuel-cost-2 row with idle time above 0. `price_lines` adds the "Why?" line only when `source_class` is in `EXAMPLE_SOURCES`. The line names the example data's tank, so it must never appear on field data, where it would be false.
- **Q2: approved.** `COST_IDLE` applies only when all counted fuel is idle: `Fraction(high_exact) == Fraction(sfc_upper_multiplier) × Fraction(idle_seconds, 3600) × Fraction(rate)`. The multiplier is read from the stored model, never retyped. Mixed rows keep `COST_MONEY`, byte-equal.
- **Q3: neither proposed option.** `headline_money` is unchanged, and `{amount}` is not in the text. The board shows the amount once, in front, as it does on every priced day. COH-7b, MONEY-B, the Portfolio rows and CH-5d1 are untouched.
- **Q4: minutes, in the mini board's own form,** `{n} {minute|minutes}` with `num` and `plural`. The same row's subline already says "Generator stayed on N minutes…". No import from `ev`.
- **Q5: the builder's literal is approved** (`VERIFIED_WITH_FUEL`, §2). Litres and money use PV-1's exact half-even rules through one shared helper (§2.4).
- **Q6: approved.** Use DB `assetops_demo3_fuela3_test` and work dir `var/demo3_fuela3`. It matches `DB_RE` (`T/demo_combined.py:53`) and the authorized `*_test` rule.
- **Q7: approved.** Digests are proven by the no-DB pins and contract tests: the K0 byte-equal pins, `test_scenario_execution_contract.py` and `test_execution_contract_alignment.py`, run before and after the declaration change, all green and unchanged. No second baseline prepare.
- **Q8: approved.** Leave `outcome_map.py:164` (`model.fuel-cost-1`). It is a descriptor, not a filter, and changing it moves CH digests. Backlog: "outcome-map fuel descriptor names the model generically (A1 L4)".
- **A1 L2, third gap (follow-up list): closed in A3** by one L0 test (§5.1 item 8).
- **Readiness "Generator fuel curve" (v69 `:426`):** as §4.3. Add nothing unless the row exists on main. The pre-flight did not report one, so nothing is added.

### 2. Client literals (verbatim; all pass guard V)

**2.1 `B/chain/vocabulary.py`, new, beside `EXAMPLE_SOURCES`:**
```python
#: FUEL-1 A3-R: the declared idle (no-load) fuel rate's basis in client words; guard V refuses "no-load" and "load".
#: None = a rate whose basis is not stored (the trial row's basis differs between hours, or is missing).
NO_LOAD_BASIS_WORDS = {"GENERIC_DEFAULT": "a generic idle fuel rate", "MANUFACTURER_DATASHEET": "the datasheet idle fuel rate",
                       "SITE_TEST": "the site-tested idle fuel rate", None: "a declared idle fuel rate"}
#: FUEL-1 A3-R G3: the trial verification page's money line (MOCK DEVIATION MD-FUEL-A3-1).
FUEL_VALUE_PAGE = ("About {l} L less diesel in the trial hour, about {amount} at {p} {cur} per litre · modelled from "
                   "{basis}, not measured by a fuel meter")
```
- `WHY_TEXT`, new key, after `"why.from.fuel_price_one"` (MOCK DEVIATION MD-FUEL-A3-3, in a comment beside it):
  `"why.from.fuel_idle_example": "The example data's fuel tank does not count fuel while the generator idles; this estimate does, at the declared idle fuel rate, so the two differ",`
  - No closing full stop, as for the other `why.from.*` lines. The owner's decision 3 is met: the line explains the example tank in "Why?".
  - Comment beside it: "true for the simulator's linear tank law (no idle fuel); if the after-demo 'simulator idle law' item lands, remove or re-gate this line".

**2.2 `B/site_outcomes/mini.py`, beside `COST_MONEY`:**
```python
#: FUEL-1 A3-R Q2/Q3: a fuel-cost-2 PRICED day whose counted fuel is all idle; extends COST_MONEY so the board's money
#: prefix (`headline_money`, unchanged) reads once. MOCK DEVIATION MD-FUEL-A3-2: v69's cost row has no idle-fuel basis.
COST_IDLE = COST_MONEY + (": generator on for {h} delivering no power, up to about {l} L · counted at {basis} of {r} "
                          "L/h, not measured")
#: FUEL-1 A3-R Q5: the Verified results line of a VERIFIED trial whose stored cost check has a priced total.
#: MOCK DEVIATION MD-FUEL-A3-4 (shared with board.COST_PRICED): v69 states the trial's effect per kWh only.
VERIFIED_WITH_FUEL = ("{code} verified{suffix}: estimated effect of the trial (not money saved): about {l} L less "
                      "diesel in the trial hour, {amount} at {p} {cur} per litre")
```
- Add both to `COPY` and to `test_out_b2_vocabulary.py`'s list.
- **S-14 client view (forecast; computed at run time, never typed):** "0.00 to 15.13 USD possible extra fuel cost on this day: generator on for 200 minutes delivering no power, up to about 12.1 L · counted at a generic idle fuel rate of 3.3 L/h, not measured".
  - The money prefix is the frontend's `money2` of the stored `amount_high`. If the stored high is the exact 15.125, it reads 15.12 (half-even). If the store rounded it outward, it reads 15.13. Report which one; neither is a stop.

**2.3 `B/site_outcomes/board.py`, beside `COST_CHANGE`:**
```python
COST_PRICED = COST_PREFIX + "about {l} L less diesel in the trial hour, {amount} at {p} {cur} per litre."  # A3-R; MD-FUEL-A3-4
```
- Add it to `test_out_b2_vocabulary.py`'s list.

**2.4 Formatting (single sources):**
- `{l}` on the idle line is `chain.outcomes._litres(quantity.high)`: half up, trailing zeros dropped. This is the same rule as the "Why?" fuel line, so "12.1" on the board matches "0–12.1 L × 1.25 USD/L".
- `{l}` on the trial lines (board, Assure, page, PV-1 value line) is a new pure `trial_litres(value) -> str` in `B/chain/vocabulary.py`, beside `money2`. Its body is PV-1's expression moved verbatim: `f"{Decimal(round(Fraction(str(value)) * 10)) / 10:.1f}"`. `mini.py`'s PV-1 code calls it, and `VALUE_LINE_TRIAL_FUEL` output stays byte-equal.
- `{amount}` = `money_text(priced_total["amount"], None, currency)`, giving "4.12 USD". `money_text` is half-even, the same as `money2` and PV-1.
- `{p}` = `price_text(price_per_litre)`. **Move** `price_text` from `mini.py:369` to `B/chain/vocabulary.py`, verbatim. `mini.py` keeps the name by import (add it to the existing `chain.vocabulary` import). If `price_text` returns None, the trial lines fall back to today's per-kWh lines.
- `{r}` = `mini.num(rate)`. `{h}` = `f"{num(m)} {plural(num(m), 'minute', 'minutes')}"`, with `m = Fraction(idle_seconds, 60)` as a Decimal.

### 3. Build

**3.1 Declaration (`T/demo_combined_kobo.py`):** as §4.3. `declare_no_load_rate(foundation, result, install_at)` is called in `configure_at` right after `declare_supply_uses`. It makes one `publish_component_properties` on the generator asset, `effective_from = install_at + CONFIG_OFFSETS["uses"]`, with the two properties and the note verbatim from §4.3. The value 3.3 is never changed to reach a figure.

**3.2 `B/chain/outcomes.py`:**
- A new pure helper beside `fuel_basis`, verbatim contract:
  ```python
  def idle_fuel(head: Any) -> dict[str, Any] | None:
      """FUEL-1 A3-R Q2: the idle part of a fuel-cost-2 consequence on the money head: {"idle_seconds", "rate",
      "basis", "litres_high", "idle_only"}; None for fuel-cost-1, no idle time (idle_seconds None or 0), or a
      missing rate, multiplier or exact quantity. `idle_only` is exact: high_exact == multiplier x idle_h x rate."""
  ```
  - `litres_high = _litres(quantity.high)`.
  - Use `Fraction(str(...))` on the stored texts. No floats.
- `fuel_basis(head)`: when `idle_fuel(head)` is not None, add `"idle_seconds": int`, `"no_load_basis": <stored basis or None>` and `"source_class": <head.source_provenance.state if it is in EXAMPLE_SOURCES, else None>`. The dict is byte-equal otherwise: fuel-cost-1, idle 0, or no price.

**3.3 `B/chain/why.py` `price_lines`:** the return shape `(energy, fuel)` is unchanged. When `fuel` is set **and** `value.get("idle_seconds")` and `value.get("source_class") in EXAMPLE_SOURCES`, `fuel` becomes `fuel + " · " + why("why.from.fuel_idle_example")`. That keeps one fuel line and one append site (`:239-240`). Import `EXAMPLE_SOURCES` from `chain.vocabulary`.

**3.4 `B/site_outcomes/mini.py`:**
- Headline (`:506-509`): `idle = idle_fuel(money_head) if priced and not zero else None`. `COST` = `COST_IDLE.format(...)` when `idle` and `idle["idle_only"]`; otherwise the existing expression, unchanged. `headline_money` is unchanged.
- `_assure`: a VERIFIED trial with `cc.state == "MODELLED_IMPROVEMENT"`, `cc.get("priced_total")` and `price_text(cc.get("price_per_litre"))` not None gets `VERIFIED_WITH_FUEL`. Otherwise `VERIFIED_WITH_COST` as today. `{suffix}` is unchanged (`provenance_suffix(a.source_class)`).
- The PV-1 value-line code calls `trial_litres` (§2.4), byte-equal.

**3.5 `B/site_outcomes/board.py` `cost_line`:** inside the `MODELLED_IMPROVEMENT` + VERIFIED branch, use `COST_PRICED` when `priced_total` and a non-None `price_text(price_per_litre)` are present, else `COST_CHANGE` as today. Non-VERIFIED stays `COST_NOT_CREDITED`. No sign check (A2-R1).

**3.6 `B/actions/verification.py`:**
- `_cost_check_read` (`:1194-1210`): after building `cost`, `if cost["priced_total"] is not None: cost["price_per_litre"] = ((row["result"] or {}).get("price") or {}).get("value")`.
- `outcome()` (`:1135-1163`): after `body["outcome"]` is set, call a new private helper `_fuel_value(tenant_id, site_id, chosen)`. When it returns text, set `body["fuel_value"]` to it; otherwise the key is absent.
  - The helper reads `ports.trial_comparison.store.latest(tenant, site, chosen["id"])`.
  - It returns None unless `chosen["outcome"] == "VERIFIED"`, the row's `result.priced_total` is set, and `price_text(result.price.value)` is not None.
  - Otherwise it returns `FUEL_VALUE_PAGE.format(l=trial_litres(pt["fuel_change_l"]), amount=money_text(pt["amount"], None, pt["currency"]), p=price_text(...), cur=pt["currency"], basis=NO_LOAD_BASIS_WORDS.get((result.get("no_load") or {}).get("basis"), NO_LOAD_BASIS_WORDS[None]))`.
- Imports come from `chain.vocabulary` only (precedent `verification_families.py:41`).

**3.7 G4(b) store and model:**
- `trial_fuel_comparison.NoLoadValue` gains a last field `basis: str | None = None`.
- `_generator_property_history` gains `companion: str | None = None`. When it is set, find exactly one property with that key in the same component whose value is one of the three basis states, and pass `basis=` to `make`. Otherwise pass `basis=None`. `sfc_history`'s call is unchanged. `no_load_history` passes `companion="generator-no-load-fuel-rate-basis"`.
- `compare` (`:240-241`): `result["no_load"] = {"value_l_per_h": ..., "basis": rates[0].basis if rates[0].basis == rates[1].basis else None} if same else None`. `basis` (the digest input) is unchanged.
- **STOP S-e** if any reader outside A3's files reads `result["no_load"]` by equality (grep `"no_load"` across `B/` and `T/`), or if any fake builds `NoLoadValue` with keyword names that clash.

**3.8 Frontend:**
- `F/sites/verificationClient.ts`: `OutcomeBody` gains `fuel_value?: string | null`.
- `F/sites/SiteActionVerification.tsx`: directly under the verdict, render `<p className="<existing verdict-detail class>" data-verification-fuel-value>{outcome.fuel_value}</p>` when it is set. Server text only, no new CSS. Comment: **MOCK DEVIATION MD-FUEL-A3-1** (v69 `:498-505` shows no money on Verification; the trial's modelled fuel value is shown with its basis).

**3.9 Finish rows (written now, run at E3; pure logic in `T/demo_combined_rows.py`, the D3 precedent):**
- **MONEY-B extended (O16):** for each idle morning (S-14, S-7, S) on the Kobo board:
  - the Optimize cost headline equals `COST_IDLE.format(...)` built from that day's stored consequence fields, through the imported helpers;
  - `headline_money.amount_high` equals the stored `display.amount_high`;
  - the stored row is fuel-cost-2 PRICED, and `high_exact == multiplier × idle_seconds/3600 × 3.3` from stored values;
  - `idle_seconds == 12000` on each morning (the probe's 200 min), else **STOP S-c**;
  - no string in the week estate body contains the exact Decimal sum of two mornings' amounts (the mornings are never summed).
  - Steady and steady-before days: stored `idle_seconds == 0` and the headline is `COST_MONEY` (byte-equal path); report the headline and money as now.
- **PROBE_CHOSEN** (`T/demo_combined_finish.py:42`, `:333-337`):
  - `cost_state` becomes `"MODELLED_IMPROVEMENT"`;
  - replace the `nominal == 0` assertion with `fuel_change_l == 3.3 × (stored baseline idle seconds − later idle seconds)/3600`;
  - baseline idle seconds must be `3600`, the 12 slots that R3h kept, else **STOP S-c**;
  - add `priced_total.amount == fuel_change_l × stored price` and `no_load.basis == "GENERIC_DEFAULT"`.
- **CH-5d1 / O1:** the S Optimize card equals the priced Site's claim text (replacing CH5d1-R §4's "Not known yet" forecast).
- **WK-2a** is unchanged and must still hold at 42.08.
- **A3-PAGE (new):** ACT-001's verification outcome body has `fuel_value` equal to `FUEL_VALUE_PAGE.format(...)` from the stored row, through the imported helpers.
- Add an L0 self-test, pass and fail, for each new or changed row in `backend/tests/test_demo_combined_finish_rows.py`.

### 4. Files (complete list)

- Backend:
  - `B/chain/vocabulary.py`
  - `B/chain/outcomes.py`
  - `B/chain/why.py`
  - `B/site_outcomes/mini.py`
  - `B/site_outcomes/board.py` (`COST_PRICED` and `cost_line` only)
  - `B/actions/verification.py` (`_cost_check_read`, `outcome`, `_fuel_value`)
  - `B/financials/trial_fuel_comparison.py` (`NoLoadValue`, `compare`'s `no_load` block)
  - `B/actions/adapters/postgres_action_store.py` (`no_load_history`, `_generator_property_history`)
- Tools: `T/demo_combined_kobo.py`, `T/demo_combined_finish.py`, `T/demo_combined_rows.py`.
- Frontend: `F/sites/verificationClient.ts`, `F/sites/SiteActionVerification.tsx`, `F/sites/__tests__/siteActionVerification.test.tsx`.
- Tests per §5.
- **No migration and no golden change.** Any `test_ch5a2_contract` or board golden diff is **STOP S-b**: no golden carries a `/2` row, a fuel-cost-2 row or `priced_total`.

### 5. Tests

**5.1 New `backend/tests/test_a3_idle_fuel.py` (L0, fakes, no DB):**
1. `idle_fuel`:
   - fuel-cost-1 → None;
   - fuel-cost-2 with `idle_seconds` 0 or None → None;
   - idle-only (12000 s, 3.3, multiplier "1.10", high_exact "121/10") → `idle_only` True, `litres_high == "12.1"`;
   - mixed (high_exact above the idle part) → `idle_only` False;
   - a missing multiplier → None.
   - **Must-fail:** replace the exact equality with `>=`, and the mixed case fails.
2. Mini headline (the `test_out_b2_mini` fake-port pattern):
   - idle-only priced → `COST_IDLE.format(h="200 minutes", l="12.1", basis=NO_LOAD_BASIS_WORDS["GENERIC_DEFAULT"], r="3.3")`, built from constants, and `headline_money` equal to the head's display;
   - mixed → `COST_MONEY`;
   - fuel-cost-1 priced → `COST_MONEY`;
   - fuel-cost-1 zero → `COST_ZERO`;
   - each of the three basis words;
   - 60 s idle → "1 minute".
   - **Must-fail:** drop the `idle_only` test, and the mixed case fails.
3. `fuel_basis`:
   - fuel-cost-1 dict byte-equal to before;
   - fuel-cost-2 idle 0 byte-equal;
   - idle > 0 with `REGISTERED_SIMULATION` → three keys added;
   - idle > 0 with an UNKNOWN source → `source_class` None.
4. `price_lines`:
   - example and idle → fuel line + " · " + the "Why?" text;
   - idle but not example → the fuel line alone;
   - no idle → byte-equal;
   - energy line unchanged.
   - **Must-fail:** drop the `EXAMPLE_SOURCES` gate, and the not-example case fails.
5. `cost_line` and `_assure`:
   - `priced_total` + `price_per_litre` + VERIFIED → `COST_PRICED` / `VERIFIED_WITH_FUEL`, with "3.3", "4.12 USD", "1.25";
   - not VERIFIED → `COST_NOT_CREDITED`;
   - no `priced_total` → `COST_CHANGE` / `VERIFIED_WITH_COST`, byte-equal;
   - `priced_total` without `price_per_litre` → per-kWh lines.
6. Helpers:
   - `trial_litres`: "3.3"→"3.3", "0.25"→"0.2", "33/10"→"3.3";
   - `money_text("4.125", None, "USD") == "4.12 USD"`, and "0.135" gives "0.14 USD";
   - `price_text` moved: `mini.price_text is vocabulary.price_text`;
   - `test_pv1_value_lines.py` green, unchanged.
7. Vocabulary: `COST_IDLE`, `VERIFIED_WITH_FUEL`, `COST_PRICED`, `FUEL_VALUE_PAGE` (formatted with each basis word) are added to `test_out_b2_vocabulary.py`'s list. `WHY_TEXT` is covered automatically.
8. **A1 L2 gap:** `finding_api.bridge_consequence` on a synthetic CURRENT PRICED fuel-cost-2 result names `quantity_source` from the stored model (`"fuel-cost-2"`).

**5.2 Verification (L0, fake store, in `test_a3_idle_fuel.py`):**
- `_cost_check_read`: `price_per_litre` is present iff `priced_total` is; a `/1` row's dict is byte-equal.
- `outcome()`:
  - VERIFIED + `priced_total` → `fuel_value` equals `FUEL_VALUE_PAGE` formatted with the generic words;
  - stored `no_load.basis` None → "a declared idle fuel rate";
  - no `priced_total` → key absent.
  - **Must-fail:** an INEFFECTIVE outcome with `priced_total` → key absent (remove the VERIFIED check, and it fails).

**5.3 `backend/tests/test_tfc2.py` (amend):**
- `no_load` gains `basis`, and a basis mismatch between the hours gives `basis` None.
- **Must-fail:** `basis_sha256` with `basis="GENERIC_DEFAULT"` on both rates equals the same result with `basis=None`. Proves `basis` is outside the digest; adding it to the digest input fails this.

**5.4 L2, own DB `assetops_a3_test`:** in the existing A2 Postgres file that covers `no_load_history`, add:
- the rate with the basis → `NoLoadValue.basis == "GENERIC_DEFAULT"`;
- the rate without the basis property → `basis` None;
- `sfc_history` unchanged.
- Drop the DB after the merge.

**5.5 Contracts and existing tests:**
- Contracts, run before and after the declaration edit, all green and unchanged (Q7): the K0 pins, `test_scenario_execution_contract.py`, `test_execution_contract_alignment.py`.
- Existing:
  - `test_out_b2_mini.py`;
  - `test_out_b3_cold_ev.py` (must pass unchanged);
  - `test_ch3_rows.py`;
  - `test_pv1_value_lines.py`;
  - `test_out_e4_readback.py`;
  - `test_ch5a2_contract.py` (no golden change);
  - `test_demo_combined_finish_rows.py`;
  - `T/checks/test_chain_coherence.py`.
- Frontend: `siteActionVerification.test.tsx` renders `fuel_value` when set and nothing when absent; `tsc`.
- **Guards:** A, W, N, V, M, chain coherence, `node tools/checks/frontend-hardwiring.mjs` (no rise) and `mock-deviation-labels`. Fast tier for `mini.py`, `board.py`, `outcomes.py`, `why.py` and `verification.py`. **Not run:** the full suite, a baseline build, or any prepare but §6.

### 6. The one Kobo-only scratch prepare (gate)

- **When:** after §5 is green and committed, and before the packet.
- **Command:** `python tools/demo_combined.py --db assetops_demo3_fuela3_test --work var/demo3_fuela3 prepare --sites kobo --cap-seconds 3600`.
- **Before starting (all required):**
  - **Only one heavy job.** No other prepare, suite, L2 run or template rebuild runs on the machine; the coordinator confirms the other lanes are idle.
  - **RAM gate.** At least 2.5 GB free for 2 consecutive minutes, sampled every 30 s. Record the samples in the packet.
  - **Keep-awake.** `tools/keep-awake-during-tests.ps1` is running, started the way the long-runs rule says, without `-ExecutionPolicy`.
- **During:**
  - Sample free RAM and the prepare's peak working set every 60 s, and record the peak (the estimate of 1.5–2.5 GB is unmeasured).
  - If free RAM drops below 1.0 GB, stop the run, drop the DB and the work dir, and report (**S-f**).
  - The cap is 3600 s, enforced by the tool. The tool's own model forecasts about 41 min, so §4.3's "20–30 min" is superseded. A stall with no output for 10 min is reported, not retried.
- **Reads (SQL and API; record each value in the packet; expected values computed from stored inputs, never typed from the run):**
  1. The generator's Foundation revision has the rate 3.3 L/h `GENERIC_DEFAULT` as known.
  2. S-14, S-7, S: fuel-cost-2 PRICED, `idle_seconds` 12000, `high_exact` = 1.10 × 12000/3600 × 3.3 (= 12.1), nominal 11.0 L. Amount = upper litres × stored price. The board headline equals `COST_IDLE` formatted from those fields.
  3. Steady and steady-before days: `idle_seconds` 0, headline `COST_MONEY`. Report the money.
  4. ACT-001's row:
     - `/2` MODELLED_IMPROVEMENT;
     - baseline idle 3600 s, later 0;
     - `fuel_change_l` 3.3;
     - `priced_total.amount` = 3.3 × price (4.125, shown 4.12);
     - per demand kWh 0.275;
     - `no_load.basis` `GENERIC_DEFAULT`.
     The summary's `price_per_litre` and the outcome body's `fuel_value` are as §3.6.
  5. WK-2a's 42.08 and the CH-5d1 Optimize card, as §3.9.
  - Call the §3.9 row functions directly against the scratch API (there is no row filter). Rows needing cold or EV are out of scope.
- **Afterwards:** run `drop` for the DB and delete `var/demo3_fuela3`. Record both in the packet.

### 7. Stops (report to the Architect; never design around)

- **S-a.** Guard V or N rejects a literal.
- **S-b.** Any golden diff; any Cold or EV byte change; any Grow, Protect or Assure byte change other than the `VERIFIED_WITH_FUEL` line on a row with `priced_total`.
- **S-c.** Stored idle seconds differ from 12000 per morning or 3600 in the trial baseline, or a morning is mixed rather than idle-only. That is a data finding, never a retune.
- **S-d.** A K0 pin or a contract digest moves.
- **S-e.** As §3.7.
- **S-f.** The RAM floor is reached, or the cap is hit.
- **S-g.** The work exceeds 1.0 unit.

### 8. Size, review, plan

- **Size: A3 0.7 → 0.91.**

  | Change | Units |
  |---|---|
  | G2 | +0.02 |
  | G3 server read and frontend | +0.06 |
  | G4(b) | +0.05 |
  | G5 gate | +0.03 |
  | `idle_fuel` helper | +0.02 |
  | helper moves | +0.02 |
  | A1 L2 test | +0.01 |

  The scratch prepare's time is machine time inside the card. Lane 2 rises by +0.21, and so does FUEL-1.
- **Review:** first review by a fresh Opus reviewer, reading this section and the packet. Focus:
  - the Q2 exactness;
  - the example-data gate on "Why?";
  - G4's digest invariance;
  - `headline_money` unchanged;
  - the scratch-prepare figures against §6.
- A3 changes screens (the Kobo cost row, Assure, Optimize, verification page and "Why?"). It joins the post-W6 owner walkthrough, with no separate walkthrough.
- **Backlog, added:**
  - outcome-map fuel descriptor (Q8);
  - Foundation display name "Generator no-load fuel rate" versus the board's "idle fuel rate". The builder greps whether a client screen shows the display name and records the answer in the packet; A3 does not change it.
- Logged for the owner (Architect decision during delegated absence): the "Why?" line about the example tank shows only on example data; on field data it would be false.

**Owner question: none.**

---

## A3-R2: ruling on A3 deviations D3 and D4 (Architect, Claude, 2026-11-08)

- Build `58b09582c`, packet `9074ac4e6` (A3 worktree). This addendum amends A3-R §3.9, §4 and §6. Everything else in A3-R stands. D1, D2, D5 and D6 are noted as reported and accepted; no change.

### D3: update O16; do not retire it

- **Why keep it.** O16 (`T/demo_combined_after.py:146-159`, `fuel_rows_ok`) is the only check on the stored rows themselves, rather than on the served board:
  - every fuel row lies on a story day;
  - no fuel row lies on a steady or steady-before day.
  
  MONEY-B does not cover either rule. Only the "quantity 0" half is false after A3.
- **New assertions** (`fuel_rows_ok`; the signature and return shape are unchanged):
  - **Unchanged:** each row's Site-local day is a story day and not in `STEADY_KINDS`.
  - **Replaced:** for offsets −14 and −7, there is at least one row, and every row has `state == "PRICED"`, `Decimal(lo) == 0` and `Decimal(hi) > 0`.
  - **Exact values stay with MONEY-B** (`idle_seconds == 12000`, `high_exact`, the amount). O16 must not repeat them, so the two rows cannot drift apart.
  - Update the docstring: "S-14 and S-7 are PRICED above 0 (idle fuel since FUEL-1 A3); the exact figures are MONEY-B's (A3-R2)".
- **Self-tests** (`backend/tests/test_demo_combined_finish_rows.py:408-415`):
  - the "good" fixture's S-14 and S-7 rows become `hi > 0` and pass;
  - add a FAIL case with `hi == 0` on S-14, the old PRICED-0 shape, which must now fail;
  - keep the existing steady-day FAIL case.
- **Who and when:** A3's fix round (Sonnet), **before** the scratch prepare. The prepare's reads (A3-R §6) then also run `fuel_rows_ok` over the scratch DB's stored rows through the `:384-391` query, and the packet records its result.
- **File approved:** `T/demo_combined_after.py` (`fuel_rows_ok` only).

### D4: the builder's `steady_day` is confirmed; A3-R is corrected

- **The correction.** A3-R §3.9 and §6 read 3 said steady days show `COST_MONEY` with 0 idle seconds. That was wrong. O16 holds that steady and steady-before days have **no fuel row**, so they have no PRICED head, and the headline is whatever the no-row path shows.
- **The rule, as built:**
  - every stored head row on the day (normally none) has no idle seconds;
  - the headline is not the `COST_IDLE` form;
  - the headline and money are reported as shown.
- **Combined with O16:** if a fuel row ever appears on a steady day, O16 fails. A3 must not make that happen.
- §6 read 3 now reads: "Steady and steady-before days: no fuel row (O16), no idle line; report the headline and money".

### Size

- +0.02 (O16 rewrite and one self-test). **A3 = 0.93**, inside S-g (1.0). Lane 2 and FUEL-1 rise by another +0.02.

**Owner question: none.**
