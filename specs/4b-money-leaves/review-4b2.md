# 4b2 review r1 (discovery, W5): money leaves from the commercial records

Reviewer (Claude, fresh; did not author 4b1 or 4b2), 2026-11-20. Branch `task/4b2-money-providers`, head
`6fab536f7`, worktree `/opt/assetecon/AssetOpsV1-4b2`. Read only.

## Summary (r1)

- **Verdict: ACCEPT.** No High or Medium finding. Three Low findings and two Info notes; F1 and F3 are cheap and
  worth folding in before merge (F3 needs the Architect's one-line confirmation), F2 optional.
- Every honesty point on the hunt list holds in code and is pinned by a test that fails under a plant (mine or the
  builder's), except two untested corners: the R9 currency check on a recorded zero (F1) and `known_at` on the
  "connected" read (F2). Neither changes a figure in any current world.
- Kobo 3458.00 / 3180.00 / 278.00 / 883.00 reproduced from records (hand-checked against the fixture, and against
  the pack's `derived-values.json` in test 1); Kisiwa O&M missing gives om 2 of 3 and contribution 1 of 3 with
  KISIWA-001 `("om",)` out.
- Deviation 1 (test 5 under `simulator/tests/world/`): accept; same class and reason as 5a mid-build Q1.
- Q2 (`test:4b` vs `service:test-4b`): the 5a ruling applies by class (F3): change the literal everywhere.
- Reruns: 268 no-DB passed; parity 1 passed; Postgres 2 passed; 3 own plants (2 caught nothing: F1, F2).

## Checks I ran (module paths verified: `assetops_backend`, `assetops_contracts`, `assetops_simulator` and
`structure/money.py` all import from `/opt/assetecon/AssetOpsV1-4b2/...`)

| Check | Result |
|---|---|
| No-DB focused + regression (`test_4b_money_leaves`, `test_3b3_structure_evaluate`, `test_4b1_stated_nodes`, `test_3a4_commercial_months`, `test_3b1_structure_registry`, `test_3b3_window_price_selection`), via heavy-slot, DB vars unset | **268 passed** in 4.09 s |
| `simulator/tests/world/test_4b_fixture_parity.py` | **1 passed** |
| `heavy-slot.sh --db -- pwsh run-host-tests.ps1 -- backend/tests/test_4b_money_leaves_postgres.py` | **2 passed** in 6.14 s (not skipped) |
| `check-architecture.ps1` | passed (with `ASSETOPS_GUARD_PYTHON` set; without it the chain-structure guard cannot find an interpreter: environment, not the branch) |
| `check-agent-workflow.ps1` | passed |

Cited, not rerun: builder's 17 Postgres (3 files), fast check-all "All 40 guards passed", and plants V7-V15, V17,
V19, V20 and test 5, all at `8bb488bae`. `git diff 8bb488bae 6fab536f7` touches only the packet, spec status,
`specs/INDEX.md` and `.ai/state/`, so the code-level runs are same-revision.

### My plants (scratch copy `scratchpad/rev4b2-r1-plants-2006644`, a `git archive` of `6fab536f7`; restored after each)

| Plant | Result |
|---|---|
| R1: skip the currency check when the value is a recorded zero (R9) | **16 passed**: nothing fails (F1) |
| R2: fuel litres taken from every FUEL QUANTITY line, QUOTE included | 3 failed (tests 1, 10, 11b) |
| R3: "connected" read with `known_at=None` (ignores the read's `known_at`) | **16 passed**: nothing fails (F2) |
| R5 (extra): drop the `NEEDS:<kind>` note on `outstanding` case 3 | 1 failed (test 7) |

## Honesty hunt (each verified in `structure/money.py` and its test)

- QUOTE as cost: `_cost` filters `COST_STATUSES` for amounts and litres (`money.py:71-75`, `:233`, `:242`); test 1
  (1475.00, 1.25), test 8 (revised to INVOICED gives 1835.00); my R2 caught.
- Open month gives no value: step 2 before step 3 (`:201`), diesel `:237`; test 2.
- Unknown is never zero: a value only from used lines, or a ZERO_WHEN_HELD row whose kind has a line in the month
  (`:205-216`); Kisiwa om is `NOT_RECEIVED`, never 0 (test 1, V8).
- Gap names `READ_AS` (D-4B.13): `_record` (`:117-121`); `in_transit` names RECEIPT, `outstanding` the failing
  kind with `NEEDS:`, cases 2 and 4 its `filled_by`; tests 7 and 10 (literal mapping, >= 20 gaps checked).
- Open-month price (D-4B.14): fallback only with no fuel cost line (`:234`); test 2(ii).
- Zero litres (D-4B.15): `ZERO_DENOMINATOR:fuel_litres`, never the fallback (`:245`); test 12.
- Origins (D-4B.18): both valued `LeafValue` calls carry `_origins(...)` over a non-empty basis (`:227`, `:250`);
  absent values carry `()`. Provenances (3A4 `PROVENANCE_ORDER`) are a prefix of `ORIGIN_ORDER`, so none is dropped.
  "unknown" appears only on the fallback's declared price (Mto, as D-4B.18 rules), never where a record is read.
- Declared price with invoices: only the no-fuel-line path reaches the fallback; mixed currency and open month refuse
  (tests 6, 2(ii)).
- Exact sums under the 200-digit trapping context, price under 34-digit HALF_EVEN; test 11b under `prec=3`.
- k of n: test 3 asserts every row of §4.1's portfolio table with `out`; Postgres test 1 reruns it.

## Findings

### F1 (Low; test gap, not an acceptance gap) R9's currency check on a recorded zero is unpinned

- **Where.** `backend/assetops_backend/structure/money.py:218-221` (the check runs over `basis` = every line of the
  kind for a recorded zero); `backend/tests/test_4b_money_leaves.py` test 6 covers only `om` and the fuel lines.
- **What.** Plant R1 (check only when lines were used) passes all 16 tests. A month whose receipts are USD and KES,
  none in transit, would then read `in_transit` 0 USD instead of `NOT_CALCULATED_YET`.
- **Why it matters.** Handshake R9 was accepted precisely for this case; without a test a later edit can drop it
  silently, and a recorded zero labelled in one currency hides a second one.
- **Fix.** Add to test 6: a KES COLLECTED RECEIPT for Kobo in October; assert `in_transit` (and `outstanding`) have
  no value, `NOT_CALCULATED_YET`, `CURRENCY_MISMATCH:KES,USD`.

### F2 (Low; test gap) `known_at` on the "connected" read is unpinned

- **Where.** `money.py:187-188`; spec §3.1 names `known_at=known_at`.
- **What.** Plant R3 (`known_at=None`) passes all tests. An as-of read before a kind's first intake would then say
  `NOT_RECEIVED` where the truth at that time was `NOT_CONNECTED`. Values cannot change (the month read keeps
  `known_at`), only the cause.
- **Fix (optional).** In test 7(b), read Kisiwa October with `known_at` before the `KISIWA-RC-0901` ingest and
  assert `NOT_CONNECTED`.

### F3 (Low; spec/fixture literal) Q2: the 5a ruling applies; change `test:4b` to `service:test-4b` everywhere

- **Where.** Fixture `backend/tests/fixtures/money_leaves_lakeside.json` (all five steps), `test_4b_money_leaves.py:81`
  default, `test_4b_money_leaves_postgres.py` (`PG_ENTERED_BY` and its docstring), spec §4.1 and §5 test 2(ii),
  `mid-build-questions.md` Q2.
- **Why.** 5a's mid-build answer (round 2, Q2) rules the same class: "one literal must serve both stores; a
  Postgres-only name means the in-memory tests prove a value the product could never store (W6: a fixture must
  satisfy the production constraint, migration 0063)". That reason does not depend on whether `entered_by` enters a
  figure, so it applies here unchanged. Its sweep predates this fixture, which is now the one other off-pattern
  literal. Architect to confirm in `rulings.md`; the code change is mechanical, no figure moves.

### Info

- **I1 (deviation 1).** Test 5 under `simulator/tests/world/` is correct: `tools/checks/dependency-direction.ps1:60`
  bans `assetops_simulator` under `backend/`, and 5a mid-build Q1 placed its parity test the same way. The test
  compares parsed records and the envelope fields. Architect to add the file to spec §6 Q8 and §5 test 5, as for 5a.
- **I2.** Spec §0 names the branch `task/4b2-money-leaves`; the branch is `task/4b2-money-providers`. Cosmetic.

## Scope

Diff (14 files) is inside done Q8 plus the deviation-1 file and the state/index entries. No migration; nothing under
`commercial/` changed; `commercial/` imports nothing from `structure/` (test 11a). T6 edits limited to the table and
body (P2).

## Residual risk not named in the packet

- `READ_AS` reads the registry rows at import; a later registry edit to `om`/`staff`/`outstanding` words moves the
  gap text without touching `money.py`. Test 10's literal catches it, so it is a deliberate coupling, not a hole.
- `diesel_price` counts every INVOICED/PAID FUEL line, so a credit-type fuel line (if 2a ever allows a negative
  EXPENSE amount) would lower the price without a refusal; today 2a's EXPENSE amount rules make this moot.
- Not verified: check-all (cited), the full suite (not required), UI (non-screen).
