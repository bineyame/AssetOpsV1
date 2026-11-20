# Review: 5a unit 1 (budget lines as target lines, declarer recorded), round 1

Reviewer (Claude, fresh; did not author the work), 2026-11-20. Discovery depth (W5).
Branch `task/5a-targets`, head `7bf9f7135`, base `880ba4dbf`; worktree `/opt/assetecon/AssetOpsV1-5a` (read only).

## Summary (round 1)

- **Verdict: accept with F1 fixed on the branch.** `lines.py` follows spec §2 rules 1 to 5 and the declarer join to the
  letter, and I found no honesty breach in the code.
- F1 (Medium, test gap): nothing tests that the declarer join honours `known_at`. A plant that drops it survives all
  11 tests and puts a later person's name on the earlier value. The test comment claims this cover.
- F2 (Low): the parity test checks fixture to DS1b in one direction only. Today the two sets match (6 of 6, checked by
  hand).
- Reruns: 5a + parity 15 passed; 5a + 3A4 + 3B3 (+ window price) 111 passed; `simulator/tests/world` + 5a 140
  passed; architecture guard passed; workflow guard passed; no `float(`; scope matches §7 question 8 (with Q1's file).
- My 4 plants: RA (versions counted over factors only) failed 2(a)-non-factor; RC (portfolio join keeps Site lines)
  failed 2(d); RB (join ignores `known_at`) **survived** (F1); RD (`search` for `fullmatch`) survived (residual, not a
  finding).

## What was checked against what

- **P5 rules 1 to 5 (unit 1 share).** Rule 1: `declared_by` / `declared_at` from the intake of the line's latest
  revision, `person_id` None for a bulk load (`loader:ds3`): matches (`lines.py:150-176`). Rule 2: a node line is
  marked `NODE` and not used as anything yet (the check comes in unit 2), so no second figure exists in unit 1. Rule
  5: two versions give `lines == ()` and every factor with a line blocked (`:89-95`). Two lines, or 3A4's duplicate
  (value None), block the factor and are never summed or picked (`:104-108`). Rules 3 and 4 (assumptions; unknown not
  zero) are unit 2. Unit 1 builds no value that is not a line, so no unlabelled assumption and no zero is possible here.
- **Head office.** The Site read takes only 3A4's `site_month` lines, which filter on `site_id`. The portfolio read
  uses `portfolio_month` (`site_id IS NULL`) and filters the join to `site_id is None` (`:141-142`; plant RC confirms
  the filter matters). Test 1(a)'s exact Kobo tuple would show a head-office `staff` as a duplicate.
- **D-5A.14.** The join reads `latest_revisions` (latest revision per record), and an unchanged re-upload writes no
  revision. Test 1(b) pins it, and the builder's V14 plant fails it.
- **The join key** `(factor_id, version_ref, line_ref, currency, provenance)` is the same key 3A4 groups on (`months.py`
  `_lines`: dims + currency + unit, which comes from the factor, + provenance + basis, always `RECOGNITION_PERIOD` for
  a budget line). A used line (one part) therefore matches exactly one revision. Placement (`recognition_period`) and the
  join's `recognition_period` filter agree.
- **Fixture vs DS1b.** I ran `build_records(load_fixture-view, generate_history(view))` myself. Lakeside's October
  `BUDGET_LINE`s are exactly the 6 in step 1 (om/staff for Kobo, Kisiwa, Mto, at spec §5's values, `budget-2026-v1`,
  USD). The envelope also matches on `source_system` (`assetops-world-generator`) and `produced_at`
  (`2026-11-06T06:00:00+03:00`). Step 2 matches spec §5 (Kisiwa contribution −60.00 kept with its `_note`).
- **Packet claims verified:** module paths (all three resolve to the worktree), the test counts, scope, no migration,
  and no existing module edited.

## Findings

### F1 (Medium, acceptance-relevant test gap): the declarer join's `known_at` is untested
- **Where:** `backend/tests/test_5a_targets.py:217-221` (`test_2_known_at_before_step_2`); code
  `backend/assetops_backend/structure/targets/lines.py:132-133`.
- **What:** the test's comment says "the cutoff reaches the declarer join too". It only proves that `amounts` honours
  the cutoff: step 1's lines are never revised, so a join without `known_at` finds the same revisions. Plant RB
  (`known_at=None` in the Site join) passes all 11 tests.
- **Why it matters:** §7 question 2, and the step-5 gate "is the declarer recorded?". With the plant, I revised Kobo
  `om` to 650.00 by `person:…0002` at step 3 and read at `2026-11-07T12:00Z`: the 600.00 value came back declared by
  person 2, not `loader:ds3`. The join key carries no value, so a regression would silently misattribute the declarer
  on any time-travel read (3B7a snapshots and history).
- **Fix:** add that case as a test. Step 3 revises `gen:KOBO-001:2026-10:plan:om` (`source_version` "2", 650.00,
  `source_system` GEN, by PERSON_2). With `known_at` 2026-11-07T12:00Z, assert `om` is 600.00, `loader:ds3`,
  `STEP_1_AT` and the revision id of revision 1. Without the cutoff, assert 650.00 and PERSON_2. I ran this probe in
  scratch: it passes on the branch and fails under RB. A portfolio twin is optional.

### F2 (Low, preference-level hardening): the parity test is one-directional
- **Where:** `simulator/tests/world/test_5a_fixture_parity.py:35-46, 57-63`.
- **What:** (a) hard-codes 6 records and (b) checks that each fixture ID is in DS1b. Neither checks that DS1b's Lakeside
  October `plan` records are all in the fixture. (d) leaves out `source_system` and `produced_at`, which test 1(a)
  relies on (`GEN`).
- **Why:** if DS1b gains a Lakeside October plan line (a new cost leaf, for example), the fixture is silently
  incomplete, which is exactly what this test exists to catch. The ruling's list (a to d) is met as written, so this
  is a preference, not an acceptance gap.
- **Fix:** assert that the set of DS1b's `lakeside-power` `BUDGET_LINE` IDs with `recognition_period` `2026-10` equals
  the fixture's set, and add `source_system` to (d).

### Not findings (noted)
- Packet deviation "a version with only non-factor lines is still reported": conservative and harmless, since nothing
  is used.
- The spec names the packet `packet.md`; the builder wrote `packet-5a-u1.md` (per unit). No action.

## Checks run (PYTHONPATH = worktree `backend`, `backend/tests`, `contracts`, `simulator`; interpreter
`/opt/assetecon/AssetOpsV1/.venv/bin/python`; no database URL, so not pooled per `backend/TESTING.md`)

- `pytest backend/tests/test_5a_targets.py simulator/tests/world/test_5a_fixture_parity.py` -> `15 passed in 0.64s`.
- `pytest test_5a_targets.py test_3a4_commercial_months.py test_3b3_structure_evaluate.py
  test_3b3_window_price_selection.py` -> `111 passed in 1.80s` (matches the builder).
- `pytest simulator/tests/world backend/tests/test_5a_targets.py` -> `140 passed in 5.48s` (matches the builder).
- `tools/check-architecture.ps1`: without `ASSETOPS_GUARD_PYTHON` the chain-structure guard cannot find an interpreter
  (the worktree has no `.venv`). With it set to the main venv -> `Architecture check passed.`
- `tools/check-agent-workflow.ps1` -> `Agent workflow check passed.`
- `grep -rn "float(" structure/targets/` -> nothing. `git diff --name-only main...HEAD` -> the files listed in the
  packet, and no others.
- Plants in the scratch copy `.../scratchpad/rev5a-u1-r1-plants-1910086` (from `git archive HEAD`; each reverted, the
  last file diffed equal to HEAD): RA fails `test_2a_a_non_factor_in_a_second_version_still_blocks`; RB survives
  (F1); RC fails `test_2d_the_portfolio_read` (RuntimeError); RD survives.

**Cited, not rerun:** the builder's fast check-all (40 guards passed, on the final tree) and plants V1, V2, V9a/b, V14
and P10a-c (`/opt/assetecon/evidence/5a-targets/u1/plants.txt`). The full suite was not run: `select-tests` selects
full because of the fixture, and per the brief that is the coordinator's call. Only `test_5a_targets.py` reads the
fixture.

## Could not verify
- No Postgres path in unit 1 (spec §9: unit 3), so the real `PostgresCommercialStore.latest_revisions` / `intake` are
  untried against this reader.

## Residual risk not named in the packet
- RD: `person_id` relies on `fullmatch`. No test has an `entered_by` that contains `person:<uuid>` without being one.
  The code is correct today.
- Units 2 and 3 carry every money-honesty rule (assumption labels, unknown never zero, the 2,295.00 figure). Unit 1
  only guarantees that a used line is single, in its currency and declared.
