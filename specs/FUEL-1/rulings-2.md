## MB-1a-R2: ruling on the MB-1a build's stops and deviations (Architect, Claude, 2026-11-07)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `099b57c96`. Build `845ece111`, packet `fa186fa3c` (`.agent/review-packet-MB-1a.md` in the mb1 worktree).
- This section **amends MB-1-R §1 Q1(c) and §2.1** for MB-1a. Every other part of MB-1-R stands. `B/` = `backend/assetops_backend/`, `T/` = `tools/`. READ = I read the code; nothing here was measured.

### 0. Order of the fix round (builder, mb1 worktree, Sonnet)

1. Merge main (`099b57c96` or later) into `task/FUEL-MB1-mill-on-board`. Reconcile the golden as in §3.
2. Apply §1 (S-d) and §2 (cap).
3. Run the checks in §6 and amend the packet as in §7. Commit. Do not push.

### 1. S-d: the policy is injected by `site_outcomes/composition.py` (builder's option, approved)

- **Decision.** `read.py` must not import `chain.composition`. OUT-B4 §B.3 (`backend/tests/test_out_b4_imports.py`) is the rule, and MB-1-R's "import locally" was wrong for `site_outcomes/`; the `postgres_estate_read.py` precedent is an adapter, not a `site_outcomes` module. Deferring to MB-1b is rejected: `ChainThreads` already carries the field, and leaving it unbound would hand MB-1b a half-wired port.
- **READ facts.** `site_outcomes/composition.py:18` already imports from `assetops_backend.chain.composition`. `thread_lifecycle_policy` is `chain/composition.py:113`. `BoardServices` is `B/site_outcomes/read.py:85-113`.
- **Code.**
  - `B/site_outcomes/read.py` `BoardServices`, directly after `chain_reader` (`:108`), verbatim:
    ```python
    thread_policy: Callable[[], Any] | None = None  # MB-1a-R2: chain.composition.thread_lifecycle_policy (composition.py injects it; OUT-B4)
    ```
  - `B/site_outcomes/read.py` `chain_threads` binding (`:295-300`): delete the local import. The body becomes:
    ```python
    if s.chain_reader is None:
        return None
    req = chain()
    return mini.ChainThreads(req.threads(sid), req.k, None if s.thread_policy is None else s.thread_policy())
    ```
    Update the comment above it: "... and the lifecycle policy (`BoardServices.thread_policy`, None when not injected)".
  - `B/site_outcomes/composition.py:18`: `from assetops_backend.chain.composition import build_chain_reader, build_thread_sources, thread_lifecycle_policy`. In the `BoardServices(...)` call, add `thread_policy=thread_lifecycle_policy` after `chain_reader=chain_reader`. Pass the function, not its value (the policy is read per board read, as MB-1-R ruled).
  - `B/site_outcomes/mini.py:210-212` comment: replace "(`chain.composition.thread_lifecycle_policy()`)" with "(`BoardServices.thread_policy`; None when not injected)". `ChainThreads.policy` stays typed `Any`; None is allowed.
- **Test**, in `backend/tests/test_mb1_opportunity_board.py` (L0, no DB):
  - `test_composition_injects_the_thread_policy(monkeypatch)`: monkeypatch `composition.build_chain_reader` to `lambda url, **kw: (None, lambda: None)` and `composition.build_thread_sources` to `lambda url: None`, as `test_out_b4_imports.py:76-77` does. Call `composition.build_outcome_board_service(None)` and assert `service.s.thread_policy is chain_composition.thread_lifecycle_policy`.
  - In the existing board-service test (the `test_ch5a1_board_contract.Port` subclass, D6), assert the `ChainThreads` built there has `policy is None` when `thread_policy` is not set. That pins the None branch.
- **MB-1b consequence (amends MB-1-R §3.3 step 4).** If `ct.policy is None`, the view is None, so there is no thread line, never a guessed `close_after`. Add one L0 case for it to `test_mb1_thread_line.py`. Production always injects the policy.
- **Files approved:** `B/site_outcomes/composition.py` (the import line and one keyword argument only).

### 2. Origin-reader cap: approved, `chain/site_chain.py` cap 8, class "both"

- **Why.** The guard exists so that a new reader is classified before it lands. `opportunity_actions` is a chain reader that handles the opportunity origin on purpose. Class "both" is already correct, and its "names the opportunity origin" check still holds. The four new tokens are the verbatim docstring, the filter, and the item key and value. Nothing new is unclassified.
- **Code.** `backend/tests/test_ch9b1_origin_readers.py:42` becomes:
  ```python
      "chain/site_chain.py": ("both", 8),  # MB-1a-R2: + opportunity_actions (MB-1-R Q1(b))
  ```
  Change nothing else in that file. The non-vacuity cases (`higher_count` uses `chain/lookup.py`; `both_ignores` uses `site_chain.py`'s text) are unaffected.
- **Files approved:** `backend/tests/test_ch9b1_origin_readers.py` (that one line).

### 3. D2, the `estate_week_2026-10-25` golden: take main's file, then regenerate; the only diff must be `verified_actions`

- **Main already carries the card.** DRIFT-R1 (merge `7bba9e64f`, `.agent/build-sheet-TEST-drift.md` §2.2) added `cards.OPTIMIZE_COST` to this golden. The builder's "pre-existing drift" diagnosis is right, and main has settled it.
- **Procedure during the merge in §0.**
  1. On a conflict in `backend/tests/fixtures/ch5a2_chain_contract/estate_week_2026-10-25.json`, take main's version whole: `git checkout --theirs -- <that path>` (during `git merge main`, "theirs" is main). Never hand-merge the JSON.
  2. If there is no conflict, still restore main's file before regenerating: `git checkout main -- <that path>`.
  3. Regenerate with DRIFT-R1 §2.2's procedure, using the mb1 worktree paths in place of `AssetOpsV1-drift`. Then run `tests/test_ch5a2_contract.py` without the variable.
- **Acceptance (STOP if any fails):**
  - `git diff main -- backend/tests/fixtures/ch5a2_chain_contract/` touches only `estate_week_2026-10-25.json`.
  - That diff adds only `"verified_actions": 0` inside each `sites[].threads` object. It adds no other key, it does not move the `OPTIMIZE_COST` card, and it changes no value.
  - If another golden or key changes, stop and report the diff. Do not commit it.
- D2 is confirmed on those terms. In the packet, replace D2's "pre-existing drift ... please confirm" with "main's DRIFT-R1 golden plus `verified_actions: 0` per Site (MB-1a-R2 §3)".

### 4. Deviations D3-D6 and the wording check

- **D3, MILL-5 in `T/demo_combined_rows.py`: confirmed. The file is approved retroactively for `mill_assure` only.** The precedent is MILL-3b, whose pure logic lives in the same file with its L0 self-test beside it. The function is pure over the board and chain bodies. It imports only backend constants (`VERIFICATION_TEXT`, `NO_VERIFIED`, `display_code`, `provenance_suffix`) and never retypes them. No other edit to that file.
- **D4, A1 skips a mini board with no Assure row: confirmed. It does not weaken A1.**
  - A1's rule is "headline count == listed verified entries". With no Assure row there is no headline to judge, so judging would mean inventing a value.
  - The skip is counted (`tally["skipped"]`), never silent.
  - The live story board is held separately. MILL-5 asserts that the S+0 Kobo Assure row exists (`"no Assure row on the S+0 Kobo board"`). E3 also checks every live mini board's rows through the V-rows (summary nodes vs board nodes).
- **D5, A1 excludes the `NO_VERIFIED` entry: confirmed. It does not weaken A1.**
  - The exclusion is exact string equality with the backend constant, not a pattern.
  - "No verified result yet" is the empty-state entry, not a verified result. Counting it would make A1 fire on every board with nothing verified, which is a false finding, not a stricter rule.
  - Add one self-test to `T/checks/test_chain_coherence.py`: headline "1 verified result" with one verified entry plus a `NO_VERIFIED` entry must FAIL. That shape is impossible on a real board, and the test proves that the exclusion cannot hide a real mismatch the other way.
- **D1 and D6: confirmed.** D1 is the cutoff rule MB-1-R Q1(b) already states (outcome None when not known by the cutoff). D6 is a stronger form of §2.5 item 4.
- **"ACT-048 verified on example data": confirmed as the existing trial (ACT-001-class) entry, byte-equal to today.**
  - It is `VERIFICATION_TEXT["VERIFIED"]` with `provenance_suffix(a.source_class)` (`mini.py:1021`), and the fake carries an example-data source class (`EXAMPLE_SOURCES`, `chain/vocabulary.py:106-112`).
  - The mill entry is `provenance_suffix(None)`, which reads "ACT-… verified" with no suffix, as MB-1-R §2.3 ruled. A domain verdict row carries no source class on `_SITE_ACTIONS`.
  - **Note, not an MB-1a change.** If the live S+0 Kobo board shows the trial "on example data" while the mill, on the same Site's data, shows no suffix, that asymmetry is a wording question. It goes to **WD-1** (money and verdict wording) as an item. WD-1 decides whether the mill line gains the suffix from the Site's source mode. MB-1a adds no literal.

### 5. Main-branch drift (not MB-1a's)

- **`test_ch9b2_midday_plan_postgres.py::test_0052_round_trip_and_refusal`: test drift. Fix it in a small Sonnet round on main**, on its own branch `task/TEST-drift-0053` from main, in worktree `C:\Users\assef\Bineyame\AssetOpsV1-drift2`. It runs in parallel with MB-1a.
  - Cause (READ): the test pins the Alembic head literally (`:236`, `:240`, `:252`). `0053_fuel_cost_2` (A1, `4be7bbc44`) is now head. `test_ch9b1_opportunity_actions_postgres.py:218,222,239` already uses the head-agnostic form; follow it.
  - Code, in `test_0052_round_trip_and_refusal` only:
    - `:236` → `assert head(mill.engine) == pg_harness.alembic_head()`. Then add `command.downgrade(_alembic(), "0052_verification_plan_domain")` and `assert head(mill.engine) == "0052_verification_plan_domain"`. The fixture has no fuel-cost-2 or `/2` rows, so 0053's downgrade does not refuse (`0053_fuel_cost_2.py:62-73`). Lines 237-250 are then unchanged and test 0052 itself.
    - `:252` → `assert head(mill.engine) == pg_harness.alembic_head()`.
    - Docstring line 1: add "(head-agnostic since 0053, MB-1a-R2 §5)".
  - Check: that one test plus `test_0052_checks_exactly_one_action_and_family_coupling`, on pg_harness base `assetops_drift2_test`. Drop it after the merge. No other test, no suite.
  - Review: a fresh Sonnet reviewer checks the diff against this item. The coordinator merges on ACCEPT.
- **`test_out_d2_objectives.py::test_policy_is_v2`** (packet, fast tier): DRIFT-R1 §2.1 is on main, so this should pass once MB-1a merges main. If it still fails after the merge, record it in the packet as main drift. It is not an MB-1a stop.
- **`test_ch5a1_mechanism_postgres` and `test_ch6b_estate_postgres`, `TEMPLATE_STALE`: rebuild once, at the start of E2, not now.**
  - Why: the template fingerprint covers the input writers. Lane 2 (A3), MB-1b and the Kisiwa story will change writers again before E2. Each rebuild costs about 1300-1700 s of machine time, and every rebuild before the last writer change is wasted.
  - Who and when: the coordinator, once, on an idle machine (the quiet-suites rule), as E2's first step and before E2's full suites. Use the exact command that the `TEMPLATE_STALE` message prints (`backend/tests/mechanism_dataset.py:1205-1243`).
  - Until then: these two tests failing with `TEMPLATE_STALE` is expected. It does not block any unit's review or merge, MB-1a's included, because MB-1a's L2 proof builds its own DB (`test_mb1_site_actions_postgres.py`).
  - Exception: if a later unit's acceptance needs a mechanism-template test, that unit's ruling orders the rebuild then, and E2 does not repeat it unless the fingerprint has moved again.

### 6. Checks for the fix round

- **L0:** `test_mb1_opportunity_board.py`, `test_out_b4_imports.py`, `test_ch9b1_origin_readers.py`, `test_ch5a2_contract.py`, `test_ch5a1_board_contract.py`, `test_out_b2_mini.py`, `test_out_b3_cold_ev.py`, `test_out_d2_objectives.py`. Also `T/checks/test_chain_coherence.py`, which includes the new D5 case.
- **Fast tier:** the same scoped set as the packet (48 files, `-m "not slow"`). Expected: 0 failures.
- **Guards:** A, W, N, V, M, chain coherence, and `node tools/checks/frontend-hardwiring.mjs` (no rise). The orphan-scan `MODULE_NOT_FOUND` stays a known worktree condition (no `npm ci`). Say so in the packet.
- **L2:** do not rerun `test_mb1_site_actions_postgres.py` unless `read.py` / `composition.py` changes touch its path. They do not, because it calls the chain reader and claims directly.
- **Not run:** the full suite, prepare, the template rebuild.

### 7. Packet amendments

- Change the status to "built; S-d and the cap closed by MB-1a-R2".
- Stops: mark both closed and cite §1 and §2.
- D2 as in §3. D3, D4 and D5 marked "confirmed (MB-1a-R2 §4)".
- Add the two approved extra files (`composition.py`, `test_ch9b1_origin_readers.py`) and `T/demo_combined_rows.py` to the files table, with their MB-1a-R2 reason.
- Add the WD-1 note on the provenance suffix (§4) under residual risk.
- Main-drift lines: point to §5. MB-1a fixes none of them.

### 8. Size and review

- **Size:** +0.05 (S-d wiring and test 0.02, cap 0.01, merge and golden reconcile 0.02). **MB-1a = 0.85**, inside S-f (0.9). Lane 1 = 2.8. FUEL-1 total = 5.5.
- The drift-0053 round is ≈0.05 of main-maintenance work outside FUEL-1.
- **Review:** MB-1a has had no review yet. After this fix round it goes **straight to its first review**: a fresh Opus reviewer, per Model by role. There is no separate re-review of this round. The reviewer reads MB-1-R §2, this section, and the packet. Review focus: §1's injection and the OUT-B4 guard passing, §3's golden diff limited to `verified_actions`, D4 and D5 against §4, and R4 (Cold and EV byte-equal).
- MB-1b stays blocked on MB-1a's merge. Its card gains only §1's "policy None → no line" case.

**Owner question: none.** For information only: two main tests were stale against migration 0053 and the mechanism template, and are scheduled as above.

---

## PV-1-R: ruling on the PV-1 pre-flight (Architect, Claude, 2026-11-07)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `70a5e8699` (MB-1a merged).
- This section **replaces §3.3's build detail**. §3.3's two line literals, MOCK DEVIATION MD-FUEL-PV1-1 and the no-total rule stand. Every other part of §3.3 is superseded where this section differs.
- `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `T/` = `tools/`. READ = I read the code; nothing here was measured.
- **Order.** PV-1 and MB-1b both edit `board.py` `SiteFacts` (last field) and `_row`. Whichever merges second merges main first and puts its field after the other's. Neither waits for the other.

### 0. Code reality (READ)

- **Mill value.** `VerificationService.domain_summary` (`B/actions/verification.py:381-401`) returns the verdict page's `value`. That is `mill_value(details, outcome, _mill_price(...))`, with the price as known at the outcome's `recorded_at` (`:403-419`). For a VERIFIED outcome it reads the context, the outcomes and one price. It runs no live assessment.
- **The board already holds that service.** `BoardServices.verification` (`B/site_outcomes/read.py:98`) is built in `site_outcomes/composition.py:59` as `VerificationService(actions)`. Its ports come from `actions.verification_ports` (`verification.py:547`), and they include `productive_price` (`B/actions/composition.py:125`). It is the same port the verdict page uses.
- **Trial fuel.** The board's `ActionFact.cost_check` is the verification summary's `cost_check`, passed whole (`B/chain/read.py:416`). Since A2 it carries `priced_total` (`verification.py:1210`), which holds `amount`, `currency`, `basis`, `window` and `fuel_change_l` (`B/financials/trial_fuel_comparison.py:199-201`).
- **Summary path.** The Portfolio summary rows' `nodes` come from `_window_parts`, which is `assemble(replace(comp.facts, nodes=...))` (`read.py:496-522`). A new `SiteFacts` field set in `mini.compose` therefore reaches both the board and the summary rows unchanged.
- **Card note.** `card_notes` (`B/estate/portfolio.py:658-668`) joins the recovered-value text and the evidence-gap clause into one server line. The browser renders it whole (`F/estate/PortfolioOutcomes.tsx:89`). The estate read cannot see the board's value lines.

### 1. S1: the mill line reads the verdict page's own `value` through the board's existing verification service (option c)

- **Decision.** Add one `MiniPorts` port, bound in `read.py` to the already-injected `s.verification.domain_summary(...)["value"]`.
- **Rejected.**
  - **(b)**, widening `_SITE_ACTIONS` and adding a price read, re-derives MV-1. Two code paths would then decide the same figure, and PV-A could drift after a price revision.
  - **(a) as proposed**, a new composition injection, is unnecessary: the service is already injected, and calling a method on an injected instance imports nothing. OUT-B4 holds with no new import in `site_outcomes/`.
  - The board's day price (`read.py:286`) is never used for this line.
- **No leak past the cutoff.** The port is called only for an opportunity Action whose `outcome == "VERIFIED"` is known by the board cutoff (`opportunity_actions` already nulls a later outcome). Domain verdicts are single and decisive (MB-1-R §0), and the price is read as known at that verdict's `recorded_at`, which is at or before the cutoff.
- **Code, `B/site_outcomes/mini.py`.** `MiniPorts` gains, last and defaulted, verbatim:
  ```python
  #: PV-1-R §1: the verdict page's own `value` (`VerificationService.domain_summary`, MV-1 `mill_value` at the price as
  #: known when the verdict was recorded) of one VERIFIED opportunity-origin domain Action; None = no value.
  verdict_value: Callable[[str], Any] = lambda action_id: None
  ```
- **Code, `B/site_outcomes/read.py` `mini_ports`,** beside `chain_threads`:
  ```python
  def verdict_value(action_id: str) -> Any:
      return jsonable_encoder(_need(s.verification, "verification").domain_summary(t, sid, UUID(action_id))["value"])
  ```
  Pass `verdict_value=verdict_value` to `mini.MiniPorts(...)`.
- **Code, in `mini.compose` after `opp` and `actions` exist,** for `o` in `opp` with `o.outcome == "VERIFIED"`:
  - `v = reads.call("verdict_value", ports.verdict_value, o.action_id, memo=True)`.
  - A failure is recorded by `Reads` (board PARTIAL, `verdict_value` in `failed`) and gives no line.
  - `None`, or `v["state"] != "PRICED"`, gives no line. The verdict page already states why a value is unpriced.
  - The port is never called when there is no VERIFIED opportunity Action. The CH-5a1 contract fixture has none, so its goldens do not move on this account.

### 2. S2: the money clause moves from `card_notes` to the Assure card (option c)

- **Decision.**
  - The Assure card, built by `portfolio_cards` (the one source that sees the board rows), carries the value lines **and** the money clause.
  - `card_notes` keeps only the evidence-gap clause.
  - `recovered()` and the estate `cost_checks` port do **not** change in PV-1. The estate body's `summary.recovered_value` field stays as it is: it is still computed, and it is no longer rendered on the card.
- **Rejected.**
  - (a) as stated: `portfolio_cards` cannot rebuild the evidence-gap clause, because that comes from the estate body. The browser must not split or join server lines.
  - (b): the estate read would have to compose boards.
- **Code, `B/estate/portfolio.py` `card_notes`.**
  - The signature becomes `card_notes(summary, authorized)`.
  - Assure = `evidence_gap_text(...)` alone.
  - Docstring: "PV-1-R §2: the money clause is the Assure card's `value_note` (`portfolio_cards`)."
  - Update the one call at `:894` (drop the third argument).
- **Code, `B/chain/vocabulary.py` `CARD_TEXT`,** under the Assure block, verbatim:
  ```python
  # PV-1-R §2: the Assure card's verified-value lines (one per result, never added) and their clause.
  "assure.value_line": "{site} · {text}",
  "assure.values_separate": "Each result's money is shown on its own and never added together",
  ```
- **Code, `B/site_outcomes/read.py` `portfolio_cards`.** The `ASSURE` card dict gains two keys after `"claim"`:
  - `"value_lines"`: for each `s` in `sites` (summary order), for each `e` in that Site's `ASSURE_PERFORMANCE` row's `(nodes or {}).get("verified_values") or []` (already in code order), the string `card_text("assure.value_line", site=s.get("site_name") or s["site_code"], text=e["text"])`.
  - `"value_note"`: `card_text("assure.values_separate")` if `value_lines`, else `MONEY_NOT_CREDITED` (imported from `B/outcomes/credit.py`).
  - Grow, Optimize and Protect are untouched.
  - There is no total, no sum and no arithmetic across entries.

### 3. The builder's defaults

**Default 1, entry shape: amended.** Each `verified_values` entry is a dict with these keys, in this order:
`{"key": action_id, "action_code": code, "basis": <stored basis>, "amount": <shown money text>, "currency": cur, "text": <line without the Site>}`.
- **No `site` key.** The board does not know the Site's display name. The card adds the Site via `assure.value_line`, as every other card Site line does.
- `amount` and `currency` exist so that COH PV1 can prove nothing is summed.
- `basis` is the stored value: the mill's `v["basis"]` (`ESTIMATED_SALES_AT_DECLARED_PRICE`) or the cost check's `priced_total["basis"]` (`TRIAL_HOUR_MODELLED_FUEL`). It is never retyped.

**Default 2, carriage: confirmed, with one change. The key is emitted only when the list is non-empty.**
- `B/site_outcomes/board.py` `SiteFacts` gains `verified_values: tuple[Mapping[str, Any], ...] = ()`, last field.
- `mini.compose` passes it in the existing `SiteFacts(...)` call, after `opportunity_actions=opp`.
- In `_row` (`board.py:816`), directly after the `GROW_REVENUE` `grow_headline` block and **before** the `NOT_MEASURED` early return:
  ```python
  if cat == "ASSURE_PERFORMANCE" and facts.verified_values:   # PV-1-R §3: nodes only; the board shows no new line
      row["nodes"] = {**row["nodes"], "verified_values": [dict(v) for v in facts.verified_values]}
  ```
- Cold and EV never set the field, so they carry no key, and every board and golden without a value line is byte-equal. A reader takes an absent key as `[]`.

**Default 3, trial fuel: confirmed, with exact rounding.**
- For each trial `a` in `actions` (`not a.is_domain`) with `a.verification_state == "VERIFIED"`:
  - `got = credited(a.cost_check, "VERIFIED")` (from `B/outcomes/credit.py`);
  - `pt = (a.cost_check or {}).get("priced_total") or {}`.
  - A line is produced only when `got` is not None and `pt.get("fuel_change_l")` is set.
- `(n, d), cur = got`.
- `amount = f"{Decimal(round(Fraction(n, d) * 100)) / 100:.2f}"`. Python's `round` on a `Fraction` is exact half-even, the same rule as `money2`.
- `litres = f"{Decimal(round(Fraction(str(pt['fuel_change_l'])) * 10)) / 10:.1f}"`.
- No new read.

**Literals, `B/site_outcomes/mini.py`, beside `VERIFICATION_TEXT`, verbatim.** These are §3.3's lines without the Site prefix, which the card adds:
```python
#: PV-1-R §3: a verified result's money, one line each, never added together (the card prefixes the Site).
VALUE_LINE_MILL = "{code}: about {d} {cur} a day more in estimated sales to productive users (your declared price)"
VALUE_LINE_TRIAL_FUEL = "{code}: about {l} L, {amount} {cur} less diesel in the one-hour trial (modelled, not metered)"
```

**Building the entries.**
- Mill: `{"key": o.action_id, "action_code": o.code, "basis": v["basis"], "amount": v["per_day"], "currency": v["currency"], "text": VALUE_LINE_MILL.format(code=display_code(o.code), d=v["per_day"], cur=v["currency"])}`.
- Trial: `{"key": a.action_id, "action_code": a.code, "basis": pt["basis"], "amount": amount, "currency": cur, "text": VALUE_LINE_TRIAL_FUEL.format(code=display_code(a.code), l=litres, amount=amount, cur=cur)}`.
- Order: all entries sorted by `(action_code or "", key)`, the Assure contributors' order.
- Add both literals and both `CARD_TEXT` strings to `backend/tests/test_out_b2_vocabulary.py`'s list. If guard V or N rejects any of them, stop (S-a) with the message.

### 4. Frontend (`F/estate/estateClient.ts`, `F/estate/PortfolioOutcomes.tsx`)

- `EstatePortfolioCard` gains `value_lines?: string[]; value_note?: string | null;`.
- `CardContent` gains `values: { lines: string[]; note: string | null } | null`.
  - In `content()`, set `values` to `key === "ASSURE_PERFORMANCE" && card ? { lines: card.value_lines ?? [], note: card.value_note ?? null } : null`.
  - It is `null` on the not-loaded path. `grow` is unchanged.
- **Render**, after `c.detail` and before `c.note`, using existing classes only:
  - each line as `<p className="oc-pfnote" data-portfolio-card-value-line>{line}</p>`;
  - then, when set, `<p className="oc-pfnote" data-portfolio-card-value-note>{c.values.note}</p>`.
  - Server text only. No join, no new CSS.
- Header comment at the render: **MOCK DEVIATION MD-FUEL-PV1-1** (text as in §3.3). Add a packet row.

### 5. COH and finish row

- **COH-17 row PV1.** Name it PV1, not V1, because V1 already exists in COH-17 (CH6b3-R Q1). Put it in a new function `coh17_values(w, summary, files, tally)`, called in `_coh17_full` right after `coh17_optimize` (`T/checks/chain_coherence.py`, ~`:1290`).
  - (i) `cards.ASSURE_PERFORMANCE.value_lines` must equal the list rebuilt from `summary.sites[]`'s Assure `nodes.verified_values`, using the `assure.value_line` form imported from `CARD_TEXT`.
  - (ii) For every pair of entries with the same currency, the exact sum `f"{Decimal(a) + Decimal(b):.2f}"` must not appear as a substring of any string in the Assure card (walk the card JSON).
  - (iii) `value_note` is `values_separate` if and only if there are lines.
  - A summary without the keys (an older bundle) is skipped and counted.
- **Self-tests (`T/checks/test_chain_coherence.py`):**
  - pass: two Sites with one entry each;
  - fail (i): a card line differs;
  - fail (ii): a card `detail` holding the sum of two same-currency amounts;
  - fail (iii);
  - skipped: an older bundle.
- **Finish row PV-A (written now, runs at E3), `T/demo_combined_finish.py` after MILL-5,** with pure logic in `T/demo_combined_rows.py` `pv_values` (the D3 precedent):
  - On the week estate summary that contains the S+0 Kobo board, the Assure card's `value_lines` contains `card_text("assure.value_line", site=<Kobo name>, text=VALUE_LINE_MILL.format(code=display_code(code), d=page["value"]["per_day"], cur=page["value"]["currency"]))`. Here `page` is the mill's verdict page body (`GET` the domain verdict, as MILL-3b reads it).
  - The trial-fuel line is present **if and only if** `credited(ACT-001's summary cost_check, "VERIFIED")` is not None. Report which case holds.
  - No card string contains the sum of two same-currency amounts.
  - Add an L0 self-test with pass and fail bodies.

### 6. Tests

- **New `backend/tests/test_pv1_value_lines.py` (L0, fake ports, no DB):**
  - 0, 1 and 2 entries: no mill and no credited trial; mill only; mill plus trial, in code order.
  - The mill `UNPRICED` or None gives no entry.
  - `verdict_value` raising gives board PARTIAL with `verdict_value` in `failed`, and no entry.
  - The port is not called when there is no VERIFIED opportunity Action (a counting fake).
  - A trial whose `credited` is None (a `/1` result, `priced_total` absent, a negative or zero amount, or INEFFECTIVE) gives no entry.
  - Rounding: `amount` for `"1/3"` is `0.33`, `"0.125"` gives `0.12`, `"0.135"` gives `0.14`; litres for `"0.25"` is `0.2`.
  - The Assure row `nodes.verified_values` is present only when non-empty. Kobo Grow, Optimize and Protect rows are byte-equal with and without entries.
  - `portfolio_cards`: `value_lines` order (Site order, then code order); `value_note` in both forms; the Grow, Optimize and Protect cards byte-equal; no card string equal to or containing the Decimal sum of the two amounts.
  - `card_notes` gives the gap clause alone.
  - Parity: the mill entry's `amount` equals `mill_value(details, "VERIFIED", price)["per_day"]` for the same fake details and price.
- **Existing tests, updated by import, never retyped:**
  - `test_ch6b2_portfolio_cards.py:195-205` (`card_notes` without the money clause);
  - `test_w303_portfolio_api.py:422-423`;
  - `test_ch5a2_contract.py` goldens, regenerated by the DRIFT-R1 §2.2 procedure. **Acceptance:** the diff against main is only `cards.ASSURE_PERFORMANCE` gaining `"value_lines": []` and `"value_note": "No money credited · modelled, not saved"`. Anything else is a stop (S-b).
  - `test_out_b3_cold_ev.py` must pass unchanged;
  - `test_out_b2_mini.py`;
  - `test_out_b4_imports.py`;
  - `F/estate/__tests__/estatePortfolio.test.tsx` and `portfolioFixtures.ts`: the Assure card renders its lines and note; a card without the keys renders neither; the body note is the gap clause.
- **Guards:** A, W, N, V, M, chain coherence, and `node tools/checks/frontend-hardwiring.mjs` (no rise). Fast tier for `board.py`, `mini.py`, `read.py` and `portfolio.py`. Frontend: the two test files plus `tsc`. **Not run:** the full suite, prepare.

### 7. Files (complete list)

- Backend:
  - `B/site_outcomes/mini.py`;
  - `B/site_outcomes/board.py` (the field and the `_row` lines only);
  - `B/site_outcomes/read.py` (`verdict_value`, `portfolio_cards`);
  - `B/estate/portfolio.py` (`card_notes` and its call);
  - `B/chain/vocabulary.py` (two `CARD_TEXT` entries).
- Tools: `T/checks/chain_coherence.py`, `T/checks/test_chain_coherence.py`, `T/demo_combined_finish.py`, `T/demo_combined_rows.py`.
- Frontend: `F/estate/estateClient.ts`, `F/estate/PortfolioOutcomes.tsx`.
- Tests: as in §6.
- No other file. In particular, `recovered()` and `postgres_estate_read.py` `cost_checks` are not changed.

### 8. Stops

- **S-a.** A guard rejects a literal.
- **S-b.** A golden diff beyond §6, or any Grow, Optimize or Protect card or row byte change, or any Cold or EV change.
- **S-c.** `domain_summary`'s `value` for the mill differs from `mill_value` over the same details and price (the parity test).
- **S-d.** The work exceeds 1.0 unit.

### 9. Size and review

- **Size:** +0.1. The `verdict_value` port is 0.03; moving the clause out of `card_notes` and its two test updates is 0.04; COH PV1 is 0.03. **PV-1 = 0.85.** Lane 1 = 2.9 and FUEL-1 = 5.6.
- **Review:** PV-1 has had no review. After the build it goes to its first review with a fresh Opus reviewer. Focus:
  - S1 parity with the verdict page;
  - the no-sum proof;
  - the `card_notes` move and the card-render order;
  - the golden diff limited to the Assure card.
- PV-1 is a screen change (the Assure card). It joins the post-W6 owner walkthrough, with no separate walkthrough.

**Owner question: none.**

---

## WD-1-R: ruling on the WD-1 pre-flight (Architect, Claude, 2026-11-07)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `4235318d6`. This section amends §3.2 for WD-1. `B/` = `backend/assetops_backend/`. READ = I read the code; nothing here was measured.
- Sources: §3.2, A2-R1 L4 (the `GENERATOR_KWH_UNKNOWN` note), MB-1a-R2 §4 (the mill suffix note), BL-48.

### 1. EV fault-day Grow headline: the §3.2 literal, confirmed

- **READ.** `B/site_outcomes/ev.py:229` picks the headline from `priced` (the overview's money state). `_charging_from_claim` (`:293-309`) later sets `headline_money[GROW]` to None when the chain earnings claim is NOT_KNOWN, but leaves the headline. So a priced fault day shows "estimated charging income" with no amount.
- **Decision.** The builder's proposal is the §3.2 card's literal. New constant in `ev.py`, beside `NO_TARIFF` (`:51`), verbatim:
  ```python
  NO_INCOME_FIGURE = "No income figure for this day: it is not fully checked"  # WD-1 (BL-48); MOCK DEVIATION MD-WD1-1
  ```
- **Rule (three cases, exhaustive):**
  - shown Grow money has a value: `TARIFF_ESTIMATE` (unchanged);
  - `priced` is true and the shown Grow money is None (the claim is NOT_KNOWN): `NO_INCOME_FIGURE`;
  - `priced` is false: `NO_TARIFF` (unchanged; the reason there is a missing price, not a missing check).
- **Code.** `_charging_from_claim` returns `"headline": {**facts.headline, GROW: NO_INCOME_FIGURE}` when `priced and money is None`, else it leaves the headline unchanged. Add `NO_INCOME_FIGURE` to the export tuple at `:79-82`. No other module changes.
- **Test.** One new L0 case beside the existing EV Grow row tests: a priced day with a NOT_KNOWN claim gives `headline[GROW] == ev.NO_INCOME_FIGURE` and `headline_money[GROW] is None`. Non-vacuity: drop the override, and the case fails. Existing tests import the constants, never retype them.
- **MOCK DEVIATION MD-WD1-1.** v69 shows the Depot Grow headline only with a figure ("gross tariff estimate"). It has no no-figure state, so this literal has no mock example.

### 2. Kobo monthly sales line: the §3.2 literal, confirmed

- **Decision.** `MG1_NO_DAY` (`B/chain/vocabulary.py:268`) and `MG1_ACTUAL` (`B/site_outcomes/mini.py:135`; §3.2 cited `:127`) both become, verbatim:
  ```python
  "no fully checked day counted yet this month"
  ```
  They must stay equal. Make it one literal: `mini.py:135` becomes `MG1_ACTUAL = MG1_NO_DAY`, added to the existing `chain.vocabulary` import at `mini.py:27` (READ: that import already brings in the `MG1_*` forms, so there is no new edge). Update the CH6a2-R Q5 twin comment at `vocabulary.py:267` to say so.
- **Retyped strings: approved, by import.** These files change only to import the constant in place of the old text:
  - `backend/tests/test_ch6_claims.py:84`
  - `backend/tests/test_ch6_evaluator.py:90`
  - `backend/tests/test_out_d4_board.py:124`
  - `backend/tests/test_demo_combined_finish_rows.py:441`
  - `tools/demo_combined_rows.py:93,98` (finish rows WK-1 and WK-4)
- **Test.** One new L0 case: a month with no fully checked day renders the line equal to `MG1_NO_DAY`, and the text does not contain "sales not recorded".
- **MOCK DEVIATION MD-WD1-2.** v69 shows the sales line only with a value. The empty state has no mock example; this replaces the earlier unlabelled empty-state words.

### 3. `GENERATOR_KWH_UNKNOWN`: change it

- **READ.** The reason fires when **either** window's generator energy is None (`B/financials/trial_fuel_comparison.py:129-130`). "Not known for both hours" is false when only one hour is missing. Rows store the reason code; the words are applied at read time (`B/site_outcomes/board.py:90`), so no stored row or golden carries the text (grep: the literal appears only at `board.py:90`).
- **Decision** (`B/site_outcomes/board.py:90`), verbatim:
  ```python
  "GENERATOR_KWH_UNKNOWN": "generator energy is not known for one or both hours",
  ```
  It matches A2-R1's `IDLE_SECONDS_UNKNOWN` form. No mock deviation: the reason words have no v69 example, as for A2-R1 D1.
- **Guard.** Run `backend/tests/test_out_e4_readback.py` (the no-code-on-screen and reason-set tests). If any other test or golden fails on this text, STOP and report it.

### 4. Mill "verified" line suffix: the mill must be labelled; not in WD-1

- **Decision.** Leaving the mill plain is **rejected**. The owner rule is that example data is clearly labelled as example data on client screens. On the S+0 Kobo board the mill verdict is judged on the same Site's example readings as the trial. A plain "ACT-… verified" beside "ACT-048 verified on example data" reads as a field result, and that is a false impression.
- **The literal** is the existing one: the mill entry uses `VERIFICATION_TEXT[s]` with `provenance_suffix(<the verdict's source class>)`, giving "… verified on example data" (`B/chain/vocabulary.py:106-112`). No new words.
- **Not in WD-1.** `OpportunityActionFact` (`B/site_outcomes/board.py:190`) and `site_chain.opportunity_actions` (`B/chain/site_chain.py:155-180`) carry no source class, and the verdict row has none on `_SITE_ACTIONS` (MB-1a-R2 §4). Labelling needs new plumbing: a source class read for the mill verdict, a field on the fact, the `provenance_suffix` call at `mini.py:1084`, MILL-5 in `tools/demo_combined_rows.py` taking the suffix by import, and the `estate_week_2026-10-25` golden check.
- **New unit WD-1m, "mill example-data label", 0.35, lane 1, after WD-1 and before PV-1** (PV-1 reads the mill verdict line too). It is demo-critical, because the mill line is on the demo board. The WD-1m pre-flight names the source: the verdict's stored evidence source class if it exists; otherwise the Site's bound telemetry source class over the verdict window (`analytics/adapters/postgres_assessment_store.py:2760` pattern). It must never be a hard-coded "example" flag. If neither source is readable within 0.35, STOP and report to the Architect.
- **Until WD-1m merges,** WD-1 leaves the mill line unchanged. WD-1's packet lists the asymmetry under residual risk, as "closed by WD-1m". It is not "accepted".

### 5. Size and order

- **WD-1: 0.15 → 0.17** (+0.02 for item 3: one literal and one guard run). Items 1 and 2 are inside the card's 0.15.
- **WD-1m: +0.35, new.** Lane 1 becomes MV-1 → MB-1a → MB-1b → WD-1 (0.17) → **WD-1m (0.35)** → PV-1. That is 2.75 + 0.02 + 0.35 = **3.12**.
- WD-1 and WD-1m are screen-wording changes. They join the post-W6 owner walkthrough, with no separate walkthrough. Guards V and N run on both.
- Logged for the owner (Architect decision during delegated absence): the mill result will carry "on example data" like the trial, which costs +0.35.

**Owner question: none.**

---

## WD-1m-R: ruling on the WD-1m pre-flight (Architect, Claude, 2026-11-08)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `cbb89ed60`; worktree `C:\Users\assef\Bineyame\AssetOpsV1-wd1m`. This section replaces WD-1-R §4's "source" paragraph. Everything else in WD-1-R §4 stands. `B/` = `backend/assetops_backend/`, `T/` = `tools/`. READ = I read the code; nothing here was measured.
- The builder's first-choice finding is accepted. The mill outcome `details` has no `source` block (`B/actions/verification_families.py:382-390`), and `site_day_snapshot.evidence_class` is not a source class. The fallback applies.

### 0. Code reality the ruling rests on (READ)

- `B/evidence/source_provenance.py:40-41`: there are exactly two positive source classes, `AUTHORED_DEMONSTRATION` and `REGISTERED_SIMULATION`, and both are in `EXAMPLE_SOURCES` (`B/chain/vocabulary.py`). Field telemetry has no publication link; it is UNBOUND. So "any of the window's evidence is published under a positive class" means the same as "some of it is example data".
- `batch_publication_link` is keyed by `batch_id` (`0017_evidence_publication.py:83`), so a class lives per batch, not per reading.
- `accepted_evidence` has `source_time` and `received_at`, and the index `accepted_evidence_site_time (site_id, source_time DESC)` (`0005_evidence_ledger.py:214`). `site.timezone` is `text NOT NULL` (`0001`).

### 1. Decisions (one line each)

- **Q1 window: (ii).** The verdict's used days (`details.baseline.days` ∪ `details.later.days`), as Site-local dates, limited to evidence received by the outcome's `recorded_at`. Rejected: (i) labels on days the verdict never used; (iii) is exact but repeats the measure per day for a label.
- **Q2 classification: "any example data labels it", not `classify`.** Return the smallest positive publication class found among the window's batches, else NULL. A mixed window still gets the label. `classify` would give MIXED/UNKNOWN and drop the label for a window that does contain example data, which breaks the owner's labelling rule. The trial's `source_pair` is a comparability gate, not a label rule, and is not reused.
- **Q3 location: (a), as a guarded lateral on `_SITE_ACTIONS`.** (b) is rejected because it crosses OUT-B4 and the evidence boundary. (c) is rejected for now: the verdict code has no evidence ids, so (c) would need this same window query at verdict time *plus* a write path, golden churn and a rebuild. E3's rebuild does not remove the golden churn. (c) goes to the backlog as BL-"mill verdict stores its source", post-demo.
- **Q4 speed: measure first; stop at more than 50 ms added per board read, or any seq scan** (§4).

### 2. The SQL (`B/chain/adapters/postgres_chain_read.py`, `_SITE_ACTIONS`)

- The existing lateral `v` also selects `o.details`. Add one guarded lateral and one output column, `source_class`. The intended form is below. The builder may adjust the syntax, but it must not change the semantics:
  ```sql
  -- in the select list:
         v.outcome, v.recorded_at AS outcome_recorded_at, src.source_class
  -- the existing lateral v also selects o.details:
  LEFT JOIN LATERAL (SELECT o.outcome, o.recorded_at, o.details FROM verification_outcome o ...) v ON true
  -- WD-1m (WD-1m-R §2): the mill verdict's example-data class over its used days; NULL = none found.
  -- No S4-05 commitment checks on purpose: a broken link can only add "on example data", never remove it.
  LEFT JOIN LATERAL (
    SELECT min(p.source_class) AS source_class
      FROM site st,
           LATERAL (SELECT array_agg(CAST(d AS date)) AS days
                      FROM jsonb_array_elements_text(coalesce(v.details->'baseline'->'days', '[]'::jsonb)
                                                     || coalesce(v.details->'later'->'days', '[]'::jsonb)) d) u
      JOIN accepted_evidence e
        ON e.tenant_id = a.tenant_id AND e.site_id = a.site_id
       AND e.source_time >= (CAST((SELECT min(x) FROM unnest(u.days) x) AS timestamp) AT TIME ZONE st.timezone)
       AND e.source_time <  (CAST((SELECT max(x) FROM unnest(u.days) x) + 1 AS timestamp) AT TIME ZONE st.timezone)
       AND CAST(e.source_time AT TIME ZONE st.timezone AS date) = ANY(u.days)
       AND e.received_at <= v.recorded_at
      JOIN batch_publication_link l ON l.batch_id = e.batch_id
      JOIN evidence_publication p ON p.id = l.publication_id
     WHERE st.tenant_id = a.tenant_id AND st.id = a.site_id
       AND a.kind = 'DOMAIN_INTENT' AND a.origin_opportunity_id IS NOT NULL AND v.outcome IS NOT NULL
  ) src ON true
  ```
- **Guard.** The lateral runs only for an opportunity-origin domain Action that has an outcome. Trials and other Actions get NULL and no scan.
- **Commitment checks are deliberately not repeated.** The S4-05 select (`postgres_evidence_ledger.py:1171-1194`) checks commitments, and a broken link resolves to BROKEN_LINK. Here a broken link to an example publication still labels. That is the conservative direction: a broken link can add the words "on example data", and it can never remove them. Write this in the packet.
- **Approved cap.** If `test_ch9b1_origin_readers.py` counts the new `origin_opportunity_id` token, raise the `chain/adapters/postgres_chain_read.py` cap by exactly the counted tokens (expected +1, class "both") with a `# WD-1m-R` comment. Anything beyond +2: STOP.

### 3. Pass-through and render

- `B/chain/site_chain.py` `opportunity_actions` (`:175-178`): add `"source_class": a.get("source_class") if known else None`. The class follows the outcome's own cutoff visibility. If no outcome is known by the cutoff, there is no class.
- `B/chain/claims.py:95` also calls `opportunity_actions`. It must ignore the new key. If any claims wire or golden gains the key, STOP.
- `B/site_outcomes/board.py` `OpportunityActionFact`: add `source_class: str | None = None` with the comment `# WD-1m-R: example-data class over the verdict's used days (None = none found)`. Fill it where the fact is built from the `opportunity_actions` dict (`mini.py:444`).
- `B/site_outcomes/mini.py:1084`: `provenance_suffix(None)` becomes `provenance_suffix(a.source_class)`. Literal: the existing `VERIFICATION_TEXT[s]` with " on example data", so the entry reads "ACT-… verified on example data". No new words and no mock deviation, because this is the trial's existing form.
- `T/demo_combined_rows.py` MILL-5 (`:279-286`): the expected mill entry takes `provenance_suffix` by import, with the class read from the board body. The live S+0 Kobo mill entry must end with `provenance_suffix(<Kobo's publication class>)`; name the class in the packet. It must never be retyped.

### 4. Speed check (before writing the render; STOP gate)

- On the authorized test DB (`*_test` in `assetopsv1-postgres-1`) with the prepared Kobo story data, run `EXPLAIN (ANALYZE, BUFFERS)` on `_SITE_ACTIONS` for Kobo with and without the new lateral.
- **STOP** and report the plan if either holds:
  - the added time is more than **50 ms**;
  - the plan reads `accepted_evidence` by seq scan rather than `accepted_evidence_site_time`.
- Record both timings and the index line in the packet. Do not add an index or a migration to fix a slow plan; report it.

### 5. Parity test (Postgres, test DB; new file `backend/tests/test_wd1m_mill_source_postgres.py`)

- **Reference.** For the same window, select the ids of `accepted_evidence` on the used days that were received by `recorded_at`. Pass them to `link_rows_on`, apply `source_provenance.link_of` to each row, keep the links that are `BOUND` with a class in `EXAMPLE_SOURCES`, and take `min` of their classes, else None. The adapter column must equal the reference in every case below.
- **Seed:** one Site whose `timezone` is not UTC, two batches on different days, one published as `REGISTERED_SIMULATION` and one unpublished (UNBOUND), and an opportunity-origin domain Action with a recorded outcome whose `details` name the days.
- **Cases:**
  1. used days only on the published batch: `REGISTERED_SIMULATION`;
  2. used days only on the unpublished batch: None;
  3. used days on both: `REGISTERED_SIMULATION` (the mixed window keeps the label; `classify` would say UNKNOWN, and the test asserts the difference on purpose);
  4. the published batch's evidence lies on a day that is not used: None (proves the window);
  5. the published evidence has `received_at` after `recorded_at`: None (proves the knowledge limit);
  6. a reading at 23:30 Site-local on a used day, which is the next day in UTC: it counts (proves the Site-local mapping);
  7. a `MINI_TRIAL` Action on the same Site: `source_class` is NULL (proves the guard).
- **Non-vacuity:** remove `= ANY(u.days)` and case 4 fails; remove the `received_at` line and case 5 fails. Record both in the packet.
- **L0:**
  - In `test_mb1_opportunity_board.py`, a mill fact with `source_class="REGISTERED_SIMULATION"` renders the entry with `provenance_suffix(...)`, and one with None renders it plain.
  - MILL-5's self-test gains a mill entry that is missing its suffix on an example Site, and that entry must FAIL.

### 6. Goldens, files, size

- **Golden diffs allowed:** only the Kobo mill "Verified results" entry gains " on example data", in any board or Portfolio golden that carries it. Any other change: STOP and report.
- **Files:**
  - `B/chain/adapters/postgres_chain_read.py`
  - `B/chain/site_chain.py`
  - `B/site_outcomes/board.py`
  - `B/site_outcomes/mini.py`
  - `T/demo_combined_rows.py` (MILL-5 only)
  - `backend/tests/test_wd1m_mill_source_postgres.py` (new)
  - `backend/tests/test_mb1_opportunity_board.py`
  - MILL-5's self-test file
  - `backend/tests/test_ch9b1_origin_readers.py` (the cap line only, if needed)
  - the affected goldens
- **Out of scope, a stop-check only.** The builder records whether the mill **verdict page** already says the result is on example data. If it does not, report it; it is not fixed in WD-1m.
- **Size: WD-1m 0.35 → 0.45** (+0.1 for the Postgres parity test and the speed gate). Lane 1 total: 3.12 → **3.22**.
- WD-1m is a screen-wording change. It joins the post-W6 owner walkthrough, with no separate walkthrough. Guards V and N run.

**Owner question: none.**

---

## WD-1m-R2: the speed gate failed; the class is stored at verdict time (Architect, Claude, 2026-11-08)

- Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `cbb89ed60`; WIP `0bc9c2e14` on `task/FUEL-WD1m-mill-example-label`. This section **replaces WD-1m-R §1 Q3, §2, §4 and §5**. Its Q1 window (used days, Site-local, received by the knowledge time) and Q2 rule ("any example class in the window labels it; `min` of the classes, else None") stand unchanged. `B/` = `backend/assetops_backend/`, `T/` = `tools/`.
- **The measurement is accepted.** The lateral adds a median of 663.5 ms per board read against the 50 ms limit. It is index-led (bitmap on `accepted_evidence_site_time`, 57,600 rows), and the cost is the per-row link and publication lookups. Real Kobo volume is very likely above the ~700 rows/day break-even. A per-read scan cannot be made honest and fast inside this unit.

### 1. Decision: route (c), the verdict stores its own source class

- **Why (c).** The mill verdict is computed and stored once (`MiddayShift.evaluate`, `B/actions/verification_families.py:197-216`; a stored outcome replays and never re-evaluates). One window query per verdict costs about the measured 0.66 s, once. Each board read then costs one jsonb field. This is also the trial's existing shape: a trial outcome carries `details.source.source_class`, and the chain read already selects that path (`B/chain/adapters/postgres_chain_read.py:134`).
- **Rejected: a Site-level declared source** (publication profile or binding basis). It describes the Site, not the readings this verdict used. If a Site mixes field and example data, it would mislabel in one direction or the other. "On example data" must be true of the result shown.
- **Rejected: descope** (plain line, DS-1 presenter line, a note elsewhere). A presenter line is not on screen. A note elsewhere leaves this line reading as a field result beside a labelled trial, which is exactly what the owner's labelling rule forbids.

### 2. Write path

- **Store port.** Add one method to the actions store port (`B/actions/ports.py`, beside `record_domain_outcome`) and implement it in `B/actions/adapters/postgres_action_store.py`:
  ```python
  def example_source_class(self, tenant_id: UUID, site_id: UUID, days: list[str], timezone: str,
                           known_at: datetime) -> str | None:
      """WD-1m-R2: `min` of the positive publication classes over the Site's accepted evidence on `days` (Site-local
      dates in `timezone`) received by `known_at`; None = none found. No S4-05 commitment checks: a broken link can
      only add "on example data", never remove it (WD-1m-R §2)."""
  ```
  The SQL is the WIP lateral's body (`0bc9c2e14`) with parameters in place of the lateral references: `:t`, `:s`, `:days` (`date[]`), `:tz`, `:k`. Keep the `source_time` range bound from min day to max day + 1 (Site-local), the `= ANY(:days)` day test, and `e.received_at <= :k`. Remove the `kind` / `origin` / `v.outcome` guard; the caller is the guard. Empty `days` returns None without querying.
- **Evaluate** (`verification_families.py:212-216`). After `result["decided"]` is true and before `outcome_rows`:
  ```python
  used = [d.isoformat() for d in result["baseline_days"] + result["later_days"]]
  source_class = store.example_source_class(tenant_id, site_id, used, plan["basis"]["timezone"], now)
  outcome, metrics = outcome_rows(plan, result, now, source_class)
  ```
- **`outcome_rows`** (`:364`) takes `source_class: str | None = None` and adds `"source": {"source_class": source_class}` to `details`, always, with None allowed. It goes in `details`, never in `basis`, so `basis_sha256` and replay identity are unchanged.
- **Fakes.** Every in-repo fake store that `evaluate` runs against gains `def example_source_class(self, *a, **k): return None`. If more than 3 fakes need it, STOP and report; do not add a `getattr` fallback.
- **Stored verdicts written before this unit** have no `details.source`. They read NULL and show plain. Demo data gets the class at E3's rebuild. Do not write a backfill or a migration (`verification_outcome` is append-only). Note it in the packet under residual risk: "a verdict stored before WD-1m shows no suffix until the data is rebuilt".

### 3. Read path

- `B/chain/adapters/postgres_chain_read.py` `_SITE_ACTIONS`: **delete the WIP's evidence lateral.** The existing lateral `v` selects `o.details->'source'->>'source_class' AS source_class` (the `:134` form). The output column stays `source_class`.
- The WIP pass-through stays as built: `site_chain.opportunity_actions` (`"source_class": ... if known else None`), `OpportunityActionFact.source_class`, and `claims.py:95` ignoring the key.
- `B/site_outcomes/mini.py:1084`: `provenance_suffix(None)` becomes `provenance_suffix(a.source_class)`. Same literal as WD-1-R §4 ("ACT-… verified on example data"); no mock deviation.
- **The origin-reader cap.** Undo any WIP cap change that the deleted lateral needed. If the new select still counts a token, apply WD-1m-R §2's rule (exact count, `# WD-1m-R2`, STOP beyond +2).

### 4. MILL-5 field: the verdict page's `outcome.source_class`

- The board wire carries no class, and it gains none. The field is on the mill verdict page wire. In `summary_wire`'s judged branch (`verification_families.py:464-466`), the `outcome` object gains:
  ```python
  "source_class": (d.get("source") or {}).get("source_class"),
  ```
  It is a wire field only, not shown on screen. This also gives the verdict page what it needs to label itself later; that is out of scope here, as in WD-1m-R §6.
- `T/demo_combined_rows.py` `mill_assure` gains a `page: dict` parameter, the same verdict-page body that the mill value check reads. The call site passes it.
  - The expected text uses `provenance_suffix((page.get("outcome") or {}).get("source_class"))`.
  - On the S+0 Kobo story it also asserts that `source_class in EXAMPLE_SOURCES`, imported from `chain/vocabulary.py`. Kobo's readings are example data, so a None there means the write path did not run, and MILL-5 FAILS rather than passing on a plain line.
  - MILL-5's self-test keeps WD-1m-R §5's FAIL case (no suffix on an example Site). Add a FAIL case for `outcome.source_class` None on the S+0 Kobo page.

### 5. Tests

- **Parity** (Postgres, test DB; refactor the WIP `test_wd1m_mill_source_postgres.py` to call the store method):
  - Cases 1-6 of WD-1m-R §5 run against `store.example_source_class(...)`, with the same reference (`link_rows_on`, `link_of`, BOUND ∩ `EXAMPLE_SOURCES`, `min`) and the same non-vacuity (remove the day test and case 4 fails; remove `received_at` and case 5 fails).
  - Case 7 is replaced. A mill outcome stored **without** `details.source` reads `source_class` NULL through `_SITE_ACTIONS`, and a `MINI_TRIAL` Action keeps its own class path unchanged.
  - New end-to-end case: `MiddayShift.evaluate` on the seeded published-batch days stores `details.source.source_class == "REGISTERED_SIMULATION"`, `_SITE_ACTIONS` returns it, and `summary_wire` shows it as `outcome.source_class`.
- **Speed:**
  - **Board read (structural, L0):** assert that the `_SITE_ACTIONS` text does not contain `accepted_evidence`. This pins that the board read never scans evidence. Then rerun the WIP harness, with `EXPLAIN (ANALYZE)` on `_SITE_ACTIONS` over the same 268,800-row data, and record the timing. Expected near the old 0.655 ms. STOP if it is above 50 ms.
  - **Verdict time:** time `example_source_class` once on the same data and record it. STOP if it is above **3 s**, because it runs once per verdict inside the evaluate step.
- **L0:** the WD-1m-R §5 board cases stand (suffix with `"REGISTERED_SIMULATION"`, plain with None). Add an `outcome_rows` case: `details["source"] == {"source_class": X}` for X in (None, `"REGISTERED_SIMULATION"`), and `basis` is byte-equal to the case without it.

### 6. WIP commit, goldens, files, size

- **WIP `0bc9c2e14`:** keep it, and build on top of it on the same branch. Do not rewrite history. The next commit deletes the lateral and adds the write path. The branch's merged diff must contain no `accepted_evidence` in `postgres_chain_read.py`.
- **Golden diffs allowed (E3 rebuilds the demo data; refresh only these):**
  1. a stored mill outcome's `details` gains `"source": {"source_class": ...}`;
  2. a mill verdict-page wire's `outcome` gains `source_class`;
  3. the Kobo mill "Verified results" entry gains " on example data".
  Any other diff: STOP and report it.
- **Files** (WD-1m-R §6's list, minus nothing, plus):
  - `B/actions/ports.py`
  - `B/actions/adapters/postgres_action_store.py`
  - `B/actions/verification_families.py` (`evaluate`, `outcome_rows`, `summary_wire` only)
  - the fake stores (one line each, at most 3)
  - the `mill_assure` call site in `T/`
- **Size: WD-1m 0.45 → 0.7** (+0.25: port and adapter method, evaluate and `outcome_rows`, the wire field, fakes, the MILL-5 parameter, the end-to-end case, goldens). About 0.2 of the WIP is reused (pass-through, fact field, parity cases). Lane 1 total: 3.22 → **3.47**.
- Logged for the owner (Architect decision during delegated absence): the mill result is labelled "on example data" from a class recorded when the result is judged, and the extra cost is +0.25.

**Owner question: none.**

---

