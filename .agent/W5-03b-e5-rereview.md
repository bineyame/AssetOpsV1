# W5-03b E5 re-review: backend fix round

- Branch `task/W5-03b-e5-fix`, head `bf6fa1d4`. Fix diff `git diff 78c6c263..HEAD` (5 files, +323/-11): `postgres_assessment_store.py`, `ev_scenarios/service.py`, `ev_site_reads.py`, `test_w503_ev_scenarios_postgres.py`, the handoff.
- Reviewer: fresh Claude reviewer, not the author. I fixed nothing; this file is my only change.
- Judged against: `.agent/W5-03b-e5-review.md` (M1, L1-L4, A1-A6), `.agent/W5-03b-e5-rulings.md` (rulings 1-10), `.agent/W5-03-build-spec.md` E5, and `.agent/W5-04-build-spec.md` for downstream effects.

## Verdict: ACCEPT

Every finding and ruling is closed in the code. The only new behaviour is the three refusals the rulings require (A5, A6, ruling 7). No `main.py`, migration or guard file changed, and I found no new implementer decision. The three Low findings below are all test-file items. None of them blocks the merge, and they can be fixed on the branch or carried.

Counts: **0 High, 0 Medium, 3 Low.**

## Closure check

| Item | Status | Evidence |
| --- | --- | --- |
| A1 / ruling 1, current money head | Closed (no code change needed) | `service._basis` still calls `scenario_money_on(c, basis["snap"])` with no cutoff. The priced IDs are asserted in the baseline test. Null IDs on the unpriced `fault` chain are asserted in `test_currency_must_match_priced_tariff`. |
| A2 / ruling 2, limit | Closed | The exact `EV_LIMIT_INVALID` body for `limit=0` is asserted (`:645`). The other bad values were already covered. |
| A3 / ruling 3, correction codes | Closed | Exact bodies are asserted for 422 `DECISION_LINK_SCOPE_INVALID`, 422 `EV_SCENARIO_INVALID` (`not-a-uuid`) and 404 `DECISION_NOT_FOUND` (`:573-582`). The 409 stale case is retained. |
| A4 / ruling 4, order | Closed | `test_equal_recorded_at_pagination_order` uses 3 raw roots sharing one `recorded_at`. Paged at `limit=1`, the order equals `id DESC`, with nothing repeated or skipped. |
| A5 / ruling 5, currency | Closed | See the A5 section below. |
| A6 / ruling 6, foreign meter | Closed | See the A6 section below. |
| M1 / ruling 7, Foundation and meter refusals | Closed | `test_baseline_foundation_and_foreign_meter_refusals` covers cases (a)-(f) plus the correction path. Each case gives 422 and leaves `[0, 0]`, and the correction case leaves `[1, 1]`. See L2 below for a non-vacuity gap in (c) and (d). |
| L1 / ruling 8, malformed 503 | Closed | Missing `cutoff`, `to` and `from` each give 503 `DECISION_STORE_UNAVAILABLE` with the exact message and no `items`, on both default and `limit=1`. The list is restored after a replica-role delete. |
| L2 / ruling 9, default page | Closed | 51 roots with no `limit` give 50 rows and a cursor, then 1 row with no cursor. Page two keeps `scenario_at`, `window` and `selection`, and the 51 IDs are unique. |
| L3 / ruling 10, race | Closed | The tests cover one race then 201, a same-key race then 200, a correction race then 201, and two races then 503 on both create and correct. The counts are checked after each case. |
| L4 | Superseded by A6 | |

### A5 currency (`service.py:81-85`, `ev_site_reads.py:657-662`)

- **Shape.** `scenario_money_on` returns `currency` (uppercased) only on the eligible priced branch. Otherwise it returns `None`, beside the two null IDs.
- **Not persisted.** `_authorable` builds the persisted `authored_basis` from an explicit key list that excludes `currency`. `basis_sha256` is therefore unchanged. The test asserts `"currency" not in basis`.
- **Rule.** The refusal fires only when `tariff_revision_id` is non-null and the authored currency differs. That matches the ruling's "non-null tariff revision" condition. The authored side is already uppercase-only through the imported C4 `CURRENCY`/`ISO_4217` grammar, so a plain comparison is case-correct.
- **Message.** It is the ruled message verbatim: `The authored currency must match the selected priced tariff currency.` The create test asserts it exactly.
- **Both paths.** `create` (`:112`) and `correct` (`:156`) both pass `cmd` into `_authorable`. Both run on the same REPEATABLE READ write connection (`store.reading` inside `store.transaction`).
- **Tests.** The ruled triple is tested: KES with USD is refused and leaves `[0,0]`; KES with KES succeeds; unpriced with USD succeeds and stores null IDs. The correction refusal is tested too, with an append count of 0.
- **Edge case.** A priced row whose `currency` is null is accepted. I treat that as unreachable, because a priced consequence carries its currency.

### A6 foreign meter (`postgres_assessment_store.py:3109,3117`)

- `head_cited` is the lowercased set of the selected head's `evidence_ids`. `meter_ids` are already lowercased, so membership is case-normalized as the ruling requires.
- `foreign_meter_evidence` is true when a meter ID is outside `accepted` **or** outside `head_cited`. The full meter list is still persisted, and nothing is silently intersected.
- Tests (e) and (f) cover the two cases: an accepted meter dropped from the head's `evidence_ids`, and `accepted_on` returning `[]`.
- The positive baseline asserts that the stored IDs equal the complete-session meters and are a subset of the accepted set, the head's cited set and `source_provenance.evidence_ids`.

### Ruling 7 Foundation and W5-04

- The `sel["foundation_ids"]` truthiness guard is removed. An empty cited set now nulls any resolved Foundation, which then refuses (`:3106-3108`). `foundation_revision_on` itself is unchanged.
- **Consumers.** `scenario_basis_on`, `scenario_money_on` and the E5 `foundation_revision_id` have no consumer outside `ev_scenarios/service.py`. I grepped `backend` and `frontend/src`.
- **W5-04.** `.agent/W5-04-build-spec.md` and `W5-04-preflight-rulings.md` reference E5 only through the `0034_w5_ev_scenarios` head and parent. The W5-04 "selected Foundation connector label" uses the Foundation read, not the E5 basis. So ruling 7 has no downstream effect on W5-04.
- The positive E1 fixture still authors (the baseline passes), so its head does cite a Foundation.

## Test strength

- **Race count changed from 1 to 2, which is correct and not a weakening** (`:946-965`).
  - The patched `insert_scenario` counts every call. The outer request's first attempt calls it once (`seen=1`). That call synchronously runs the second client's POST, which goes through the same patch (`seen=2`) and commits the key.
  - The outer insert then collides. `store.transaction` maps the `IntegrityError` or 40001 to `EvScenarioWriteRefused`, and `_write` retries once.
  - The retry finds the key through `scenario_by_create_key` and returns 200 without inserting.
  - A retry that inserted would give 3, so `== 2` still proves that the retry inserts nothing. The old `== 1` could never hold, because the racing writer passes through the same patch.
  - The `[2, 2]` count independently confirms one root per key.
- **Exactly 15 tests, all unique.** The test functions are at lines 124, 203, 420, 498, 519, 607, 673, 707, 729, 756, 802, 858, 882, 906 and 928, and my run collected 15. Commit `bf6fa1d4` removed the duplicated copies of the new test functions, but in-body duplicates from the same paste remain (L1).
- **Monkeypatches hit real code paths.**
  - `EvReadService._snapshot`, `foundation_revision_on` and `accepted_on` are each called through `self.` inside `scenario_basis_on`.
  - `scenarios_client` builds a real `EvReadService` (`build_ev_read_service` returns `EvReadService(...)`), so the class-level patches apply.
  - `insert_scenario` and `insert_scenario_revision` are `@staticmethod` on the store (`store.py:163-168`), so patching them with `staticmethod(...)` matches how the service calls them.
  - The synthetic `IntegrityError` goes through the real `store.transaction` mapping and the real `_write` retry loop.

## Findings

### L1 (Low, test hygiene). Duplicated paste residue remains in the existing tests.
- `backend/tests/test_w503_ev_scenarios_postgres.py:411-412` has a duplicate `"accepted"` dict key. The second silently overrides the first, and ruff/pyflakes would flag it as F601.
- The same file has duplicated blocks at `:448-451` and `:452-455` (the A6 assertions), at `:573-582` and `:583-592` (the A3 loop and the 404 check), and at `:645-646` and `:647-648` (the A2 assertion).
- **Why it matters.** It is not a weakening: each block is identical and the repeated refusals write nothing. But the fix commit says the duplicates were dropped, and these copies make the file read as if the cases were distinct.
- **Fix.** Delete the second copy of each.

### L2 (Low, test strength). Foundation cases (c) and (d) do not prove they reach the membership branch.
- `backend/tests/test_w503_ev_scenarios_postgres.py:777-782`.
- With `foundation_ids` patched to two strangers, or to `[]`, `foundation_revision_on` takes its effective-at-cutoff fallback (`postgres_assessment_store.py:3045-3050`).
- If that fallback resolved nothing in this fixture, (c) and (d) would refuse through the absent-Foundation path (a) and never exercise the "outside the cited set" or "uncited head" nulling that ruling 7 specifies.
- The fixture almost certainly has an effective revision at 09:00, but no assertion pins it.
- **Fix.** In the same patched context, assert that `foundation_revision_on(c, snap)` returns a non-null revision whose ID is outside the patched set, for example through a small `reads.within` call.

### L3 (Low, test strength). The correction-path currency refusal asserts the code but not the ruled message.
- `backend/tests/test_w503_ev_scenarios_postgres.py:821`.
- Ruling 5 names the message for "POST or correction". The create case asserts it exactly; the correction case checks only `EV_SCENARIO_INVALID`.
- The same `_authorable` call raises both, so the risk is small.
- **Fix.** Assert the full error body, as the create case does.

## Checks I ran (actual output)

- `tools/check-architecture.ps1`: "Architecture check passed."
  - The first run, without `ASSETOPS_GUARD_PYTHON`, failed with Rule 8 "no Python interpreter at '' or .venv", followed by a cascade of vacuity messages. The cause is that this worktree has no `.venv`.
  - With `ASSETOPS_GUARD_PYTHON` set to the main checkout's venv python, it passed. The handoff records the same setup.
- `tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- `backend/tests/test_w503_ev_scenarios_postgres.py -q -n 2`, on a private `assetops_w503e5rr_test` with the PYTHONPATH from the brief:
  - Result: **15 passed, 11 warnings in 239.78 s**. The warnings are starlette and alembic deprecations.
  - The DB was dropped afterwards, and no `assetops_w503e5rr%` database remains.
- **Not run.**
  - The adjacent files and the full suite: I ran only the E5 file, as the brief instructs, because the machine is shared. The full suite's 3979 passed (plus 1 known timing flake) is on the pre-fix head `50b43246`, not this revision. The fix touches only `ev_scenarios/service.py`, `scenario_basis_on` and `scenario_money_on`, and the only caller of all three is E5. The implementer's batch run on this fix (E5 plus the 0034 head-pin files plus `test_w503_ev_depth` and `test_w207_ev_site_reads`: 258 passed, and the 1 failure was the since-corrected race count) is the adjacent evidence. I did not reproduce it.
  - Writer probes: no guard or schema change, so not needed.
  - Frontend: no frontend change, so `tsc` and the layout evidence do not apply.

## Residual risk

- **Pre-fix full suite.** The full-suite proof is from the pre-fix head. The changed surfaces have no caller outside E5, so the risk of an untested regression elsewhere is low. A safety-net full run on `main` after the merge, per the tiered test policy, covers it.
- **Worktree setup.** This worktree needs both `ASSETOPS_GUARD_PYTHON` and the explicit PYTHONPATH. Without either, the guard check and the suite fail for environmental reasons. That is not a product defect.
