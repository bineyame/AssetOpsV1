# 6c review: option evaluator (discovery review, W5)

Reviewer: Claude (assetops-reviewer), not the implementer. 2026-11-22. Branch `task/6c-option-evaluator` at
6c1c4bfea, diff `main...HEAD` (57cecf954). Judged against `spec.md` rev 2, `reviewer-guide.md`, D-P6.1 to D-P6.31 and
the owner rule "one figure, loyal to the operating world".

## Summary (round 1)

- **Verdict: accept with findings fixed on the branch** (M1 and the Low test gaps), after the Architect rules on the
  questions below. No High. The rule, the difference operator by operator, R0 to R4, the run outcome, the study path
  and the world-month rule match the spec; every §5 literal I recomputed by hand agrees.
- **M1:** three spec'd rules have no test that fails when they are broken (mutations survived): the `/`/`min`/`max`/
  `ceil`/`floor` branch with a non-zero change, a changed leaf whose base is missing (read as 0 survives), and
  `ONE_OFF_CURRENCY`. Commit 2's tests pin the fixtures' paths, not these rules.
- **Low:** ranking edge rules untested (L1); any non-`SETTING_GRID` generator becomes a no-action row (L2);
  `ZERO_DENOMINATOR` is a catch-all name (L3); test 4's effects are built by helper arithmetic, not literals (L4,
  preference).
- Deviations 1 to 8: all acceptable as built; 1 and 3 need an Architect ruling (questions Q1, Q3), 4 and 5 a
  confirmation.
- Checks: 186 passed (6c's four files, 0K4d's two, 6a decisions) on Postgres; architecture and workflow guards pass.

## Checks run (this review)

- From the worktree root: `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_6c_difference.py
  backend/tests/test_6c_evaluate.py backend/tests/test_6c_run.py backend/tests/test_6c_run_postgres.py
  backend/tests/test_0k4d_admission.py host/tests/test_0k4d_v8_study.py backend/tests/test_6a_decisions.py -q`:
  `186 passed, 4 warnings in 107.09s`. (The dispatch's form, run from `backend/`, finds no files: the wrapper's
  targets are repo-relative. Worth fixing in dispatch templates.)
- `pwsh -NoProfile -File tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON` set: "Architecture check passed.",
  exit 0. Without it the chain-structure guard reports it cannot run (no `.venv` in the worktree); the packet's run
  passed, so this is the worktree's environment, not the slice.
- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- Mutation checks (commit 2 was not written test-first), on a `git archive` snapshot of 6c1c4bfea in scratch, running
  `test_6c_difference.py` and `test_6c_evaluate.py` against each mutant:

  | Mutant | Result |
  |---|---|
  | `difference.py:204` the non-zero `/`, `min`, `max`, `ceil`, `floor` change replaced by 0 | **survived** |
  | `difference.py:148` a changed leaf with a missing base read as base 0 | **survived** |
  | `evaluate.py:98-99` `ONE_OFF_CURRENCY` never added | **survived** |
  | `evaluate.py:196` R0 source class strongest instead of weakest | survived |
  | `evaluate.py:180` near set `>` instead of `>=` | survived |
  | `evaluate.py:181` distance tie broken by the lower value | survived |
  | `evaluate.py:131` `AT_GRID_EDGE` upper branch removed | survived |
  | `difference.py:89` the option-only neutral short cut removed | survived |
  | `evaluate.py:107-109` `assumed` takes any missing record, not only TARGET/ASSUMPTION | caught |
  | R1 disabled (rejected options rank) | caught |

  The packet's 14 plants are not repeated here; the two I tried in the same family were caught.
- Hand recomputation: F1b all seven rows (e.g. 200 × 1.25 − 50 × 0.05 = 247.50; × 12 = 2970.00; − 90 = 2880.00),
  the threshold 3012.00 × 0.9 = 2710.80, F1d (−898.00 best), C1 (−0.1 × 5000 kWh × 0.20 = −100.00; 1200 − 400 =
  800.00), E1 (−300 + 100 = −200.00; 2400.00). All agree with the tests' literals.
- Read against the spec: `structure/difference.py` (§2, operator by operator), `decisions/evaluate.py` (§3.4),
  `decisions/models.py` (§3.3), `decisions/study_input.py` (§3.1), `decisions/run.py` (§3.5, §4), the `runs/admission.py`
  delta (`judge` is `admit`'s former body; `admit` delegates; `DAWN_LIMIT_PCT` is its default) and the 6a delta
  (`admit_person` lifted verbatim).

## Findings

### M1 (Medium, acceptance gap: spec §6 tests 1 and 4) Three rules of the difference and the value are untested

- `backend/assetops_backend/structure/difference.py:200-204`: when an operand of `/`, `min`, `max`, `ceil` or
  `floor` changes, the change is `val1(e) − val0(e)`. No fixture reaches it with a non-zero change (C1 and E1 only
  pass zeros through these operators), and replacing the branch's result with 0 passes every test. This is the path
  any capacity rule (`ceil`, `min`) or ratio takes, so a wrong value there would ship silently.
- `difference.py:148`: a changed leaf whose base is missing has no option-side value. Reading it as `0 + delta` passes
  every test. That is the owner's "missing is never zero" rule in the one place this slice can break it; F1b's
  `candidate_l` never needs `val1`, so nothing pins it.
- `backend/assetops_backend/decisions/evaluate.py:98-99`: `ONE_OFF_CURRENCY` (§3.4 step 1) is never exercised; deleting
  the check passes. A one-off in another currency would then be subtracted from a USD change.
- **Why it matters:** these are the rules whose failure gives a confident wrong money figure; the spec's own plant
  list does not cover them, and the packet's "done" answers rest on the fixtures' paths.
- **Fix:** three hand-literal tests in `test_6c_difference.py` / `test_6c_evaluate.py`: (a) a planted registry or an
  existing node where a changed leaf passes through `ceil`/`min`/`/` with a non-zero change (literal expected
  change); (b) a product of two changed operands where one changed leaf's base is NOT_AVAILABLE: the change is
  MISSING naming that leaf; (c) F1b with one option's one-off in EUR: `missing` `[["ONE_OFF_CURRENCY", "DECISION",
  null]]`, value None, DEFERRED. Show each failing on its mutant in the packet.

### L1 (Low, test gap) Ranking edge rules untested

`evaluate.py:180` (`>=` at the threshold), `:181` (equal distance → higher value), `:131` (`AT_GRID_EDGE` when the
setting is higher than current), `:196` (R0's source class is the weakest across options; every fixture has one
class), `difference.py:89` (the option-only neutral short cut; the parity test values every leaf). Each mutant
survived. Fix: one small `evaluate_options` case per rule with injected changes (no study needed), literal outcomes.

### L2 (Low, latent) Any generator other than `SETTING_GRID` is treated as no action

`backend/assetops_backend/decisions/run.py:58-60` gives every non-`SETTING_GRID` option `changes=None`, and
`evaluate.py` reads `changes is None` as no action: COMPARISON, value 0. `run.py:97-98` refuses `STUDY_REQUIRED`
whatever the generator. Today 6a writes only `NO_ACTION` and `SETTING_GRID`, so nothing is wrong now; when 6g or 6b
adds a generator, its options would silently read "worth the same as doing nothing" (a missing value shown as 0).
Fix: branch on `"NO_ACTION"` explicitly in `option_inputs`, refuse an unknown generator (e.g. `LEVER_UNKNOWN`), and
test E2 on the lever's generator as §4 E2 states.

### L3 (Low) `ZERO_DENOMINATOR` names any unresolved name

`evaluate.py:61-66`: every missing name that is neither a changed leaf without a delta nor a base leaf with a missing
record becomes `ZERO_DENOMINATOR`/`STRUCTURE`. That includes a node whose no-action value is missing with no leaves
(`difference.py` `read0`), which is not always a zero denominator. No fixture reaches it (deviation 4). Fix: see Q4.

### L4 (Low, preference) Test 4's effect rows are computed by a helper

`backend/tests/test_6c_evaluate.py` `_mg_effects` builds the expected MINI_GRID effects by arithmetic (−a × 1.25,
t × 0.05). It does not call the evaluator, so it is not the High of reviewer guide item 1, and the monthly, horizon and
value columns are literals; but §6 test 4 asks for every field as a literal. Optional: write F1b's
`stop-70-reserve-30` effect list as literals (it already is in test 1).

Nothing else found. Specifically confirmed: no `stated` map reaches `evaluate` (D-P6.4); the product rule uses
`val1(b)` with `d(a)` and `val0(a)` with `d(b)`; the zero short cut is only on an exactly-zero `d`; F1a's
`stop-90-reserve-25` is valued by that rule, not a special case; dawn enters no rule; a REJECTED option never ranks;
`RANKING_INCOMPLETE` withholds every rank; declared seasons read no `*_by_month` value; no design figure or structure
key under `decisions/` (test 8); `judge` equals `admit`'s parts and 0K4d's two files pass unchanged.

## Deviations 1 to 8

| # | Deviation | Acceptable? | Note |
|---|---|---|---|
| 1 | A money effect with an exactly-zero change that read no money value has currency null (F1b/F1j `battery_wear`); §5 says money effects carry USD | Acceptable as built; needs a ruling (Q1) | Follows §2 literally; §2 and §5 conflict. Not a figure question: the figure is exactly 0 either way |
| 2 | F1j's zero row has `assumed` [] | Yes | Nothing changed, so no price was read; §3.4 step 3 literal. Spec text "every other row as F1b" refers to the other rows |
| 3 | `assumed` lists used leaves only, not a used node's assumed leaves | Acceptable now (no fixture reaches it); needs a ruling (Q3) | Inconsistent with evidence, origins and currency, which already come from a used node's `FactorValue` |
| 4 | `ZERO_DENOMINATOR`/`STRUCTURE`/node; no `ONE_OFF_CURRENCY` when the option has no currency | Yes, with Q4 | The second is right: with no currency the change is already missing. The first is a catch-all (L3) |
| 5 | `STUDY_REQUIRED` whenever no study; `LEVER_UNKNOWN` for an unknown lever | Yes today | Correct while `SETTING_GRID` is the only generator; see L2 for when it is not |
| 6 | "Every case has the baseline's full months" (`STUDY_UNREADABLE`) runs after the frame check, before `STUDY_MONTH_NOT_COVERED` | Yes | §3.3 places the check at E3; this order refuses a malformed file before judging its month |
| 7 | 6a's `records.py` (`admit_person` lifted, codes added), `cli.run(build=)`; own `StudyRefused` | Yes | `admit_person` is a verbatim lift; 6a's tests pass; §0 allows 6a files touched when named |
| 8 | `read_study(path, read_bytes)`, `EvaluationService(read_bytes=)` | Yes | Required by the configuration-persistence guard; the adapter is the only file read |

## Questions for the Architect

Batched; each has a recommended default. None blocks the branch fixes in M1 and L1 to L3.

- **Q1 (deviation 1): currency of an exactly-zero money effect that read no money value.** Options: (a) null, as §2
  says, and amend §5's "money effects carry USD"; (b) extend D-P6.29 to effect rows: a money effect whose change is
  exactly 0 and read no money value takes the option's currency. **Default: (b)**, set in `evaluate.py` when building
  `EffectRow`s. Reason: the stored row is what 6f and 7c read; a money row with no currency is indistinguishable from
  a row whose currency is unknown, and 6f would need a special case. It adds a label, not a figure, so it respects
  "one figure". A missing money effect (F1a's `battery_wear`) stays null.
- **Q2 (deviation 2): F1j's `assumed` [].** **Default: accept**, and amend §5 F1j to say `assumed` [] (no price read).
- **Q3 (deviation 3): should a used node's assumed leaves be listed?** **Default: yes**: `assumed` is the union of
  each used leaf that is TARGET/ASSUMPTION and each used node's `FactorValue.assumed_leaves` (already computed by
  `evaluate`), in registry order. Reason: evidence, origins and currency already propagate from a used node's
  `FactorValue`; leaving `assumed` out would hide an assumption under a figure the executive chooses by. Add one test
  with a node resting on an ASSUMPTION leaf.
- **Q4 (deviation 4, L3): the name of a missing value that is no record.** **Default:** keep
  `MissingInput("ZERO_DENOMINATOR", "STRUCTURE", node)` only when the fold met a zero denominator (tag it in
  `_fold_v`), and name any other node with no value of its own by the node's own `missing_leaves` (never a catch-all);
  register `ZERO_DENOMINATOR` as a record kind for 6f's "Not available yet" text.
- **Q5 (deviation 5, L2): E2 and unknown generators.** **Default:** E2 tests the lever's generator as §4 states;
  `option_inputs` branches on `NO_ACTION` explicitly and refuses any other generator until its model exists.
- **Q6 (deviations 6 to 8):** **Default: accept as built**; record them in the spec at the next revision.
- **Q7 (M1, spec §6):** add the three rules of M1 to the spec's plant list so a later slice cannot drop their tests.
  **Default: yes.**

## Could not verify

- `build_evaluation` end to end (the real structure read over Postgres feeding `site_inputs`): no test runs it; the
  packet names this. I checked that `site_by_id` returns the same `chain.ports.SiteRef` that `site_inputs` takes.
- Full suites: not run (dispatch). The packet's same-revision adjacent run (852 passed, one pre-existing 3B3 t6
  failure) was at c380b1faf; later commits are the adapter move and the packet, covered by my run above.

## Residual risk not named in the packet

- `run.py:101-104`: `except Exception` around `site_inputs` turns any defect in the read (a type error included)
  into `STRUCTURE_UNAVAILABLE`, exit 3. With `build_evaluation` untested end to end, a wiring fault would show as
  "the month's figures cannot be read right now", not as a bug. A Postgres test of `build_evaluation` on one seeded
  Site would close both.
- `horizon_change = monthly × horizon_months` (`evaluate.py:89`) runs outside `evaluate`'s 34-digit context (default
  28 digits). Harmless at these magnitudes; noted for consistency with "nothing quantised".
