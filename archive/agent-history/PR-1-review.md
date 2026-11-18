# PR-1 review (Claude reviewer, 2026-11-12)

Reviewed: `task/PR-1-price-action` head `81c8bd95d`, diff vs merge-base `9fc353736`, against card PR-1 (sequence doc rev 4 l.49-54) and `architect-answer-price-it-2026-11-10.md` §3, §4.1, §5, §7. Packet `.agent/PR-1-packet.md`.

**Verdict: ACCEPT WITH NOTES** (no High or Medium findings; the merge still waits on the packet's listed Postgres files).

## k8 batch failure: not caused by this branch
The 14 `test_k8_estate_fuel.py` failures (`AttributeError: 'types.SimpleNamespace' object has no attribute 'known_at'`, `estate/coverage.py:68`) reproduce on the merge-base `9fc353736` with no PR-1 code. The command was `pytest tests/test_out_b4_main_binding.py tests/test_k8_estate_fuel.py`, and the result was 14 failed, 9 passed, on both the base and the branch. With `test_runs_api.py` first, the base gives 14 failed, 35 passed. The k8 file alone gives 21 passed. Cause: `main.py:685` sets the module global `estate_coverage.day_grades_provider` in `create_app`, and nothing resets it. Any earlier test that builds the app leaks the provider into k8's `SimpleNamespace` requests. This is pre-existing test-isolation debt for FR-B, not a PR-1 defect.

## Findings
- **Low.** `outcomes/price_action.py:94-107`, SET_PRICE label for keys not in `STORED_KEYS` (`repair_visit_cost`, `planned_service_cost`, `charger_repair_cost`). Every REPEATED / PLAN_* / CHARGER_FAULT warning reads "Set a … for X →" for a price that cannot be stored yet. Rev 5 §5.3 (l.123, l.148) assigns this change to PR-3 ("What pricing this needs →"), so it is not a PR-1 gap. If PR-3 slips, this wording promises a save that cannot happen.
- **Low.** `shell/SitePricesFrame.tsx:11-12`, sign-in sentence. It matches rev 4. Rev 5 l.122 replaces it with the "entered by site admin" sentence. It is one constant, so it does not block PR-2a or PR-3.
- **Low (test gap).** `frontend/src/sites/__tests__/priceAction.test.tsx` covers warnings, mill value, routing, return and the target page. No frontend test renders the link on the Finding cost tile (`SiteFinding.tsx:802,862`) or on the estate money row (`EstateFinancials.tsx:213`). The backend side is tested in `test_pr1_price_action.py`.
- **Low.** NEEDS_MODEL `text` (the §5 sentence) is on the wire but never rendered. Only `label` shows. The §5 block is PR-5, which is out of scope, so this is acceptable.
- **Note.** The card says `/sites/:id/prices` and the build uses the spec's `/sites/:code/financials/prices`. Rev 5 l.175 confirms the built address.

## PR-3 compatibility
PR-1 does not block PR-3. Rev 5 builds on PR-1's address, `PRICE_NOUN` and `STORED_KEYS` (l.75, l.103-104, l.175). There is no write path, and `financial_api.py` and `HUMAN_PRINCIPAL_REQUIRED` are untouched. The target frame is a placeholder that PR-2a replaces.

## Checks I ran
- No DB. `test_pr1_price_action`, `test_out_c_rules`, `test_out_c2_board`, `test_out_c1_never_money`, `test_k8_estate_fuel` (alone), `test_partial_money`: 73 passed.
- `tsc --noEmit` on `81c8bd95d`: exit 0.
- `check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv: passed. `check-agent-workflow.ps1`: passed.
- **Not run, and unverified:** Postgres files (lane rule), including the hand-edited `k6b_mill_pins.json` pin (Site code `MG-W402-001` is inferred). Also not run: vitest and build (sandbox), and layout evidence (the packet records it as not run).

## Residual risk
- AR-4 and AR-0 parity: whichever of AR-4 and PR-1 lands second must carry `price_action` on `_line` and `_card`. The packet names this.
- `mill_value` gets `price_action` only when the action context carries `site_code`. Only the Postgres `domain_plan_context` adds it, so any other store yields `None` silently.
