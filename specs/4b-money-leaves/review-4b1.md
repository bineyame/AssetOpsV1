# Review 4b1 r1: the stated-node seam (discovery, W5)

Reviewer: fresh Claude (Opus 5.5), not the author. 2026-11-20. Branch `task/4b1-money-leaves`, head `aa5e78036`,
worktree `/opt/assetecon/AssetOpsV1-4b1`, base `main` `880ba4dbf`. Read only; nothing in the worktree changed.

## Summary (round 1)

- **Verdict: accept, with findings fixed on the branch.** No honesty breach in the code. One spec-required gate
  (D-4B.17's plant, S8/V18) has no failing test (Q1), and three rows of the §2.3 table are untested.
- F1 Medium: V18 passes the 4b1 tests. The gap is in the tests, not in the rule (`check.py:185` is right).
- F2 Low: row 1's `missing`/`assumed_leaves` and rows 3/4's `sources`/`origins`/`coverage` are untested (3 plants of mine pass).
- F3 Medium, for the Architect, not blocking 4b1: a valued leaf with `origins == ()` adds no constraint, so
  `weakest_origin` can read stronger than a part whose origin is unknown. Every `ProductLeafSource` leaf has `()`.
- F4 Low (spec text): §2.7 says "only the `:366` edit"; §2.1 and P1 name four. The build follows §2.1.
- Q1 view: use a `MONEY^2` (or `MONEY*KWH`) SUM plant. Keep the check order.
- P2 deferral and S1-S10 are right: §3.2 is 4b2's and §8 gives 4b1 S1 to S10.
- 282-value parity: confirmed, and widened to 564 values with sha256 (main vs branch identical).
- Reruns: 181 passed (no DB); 3B3 Postgres 5 passed (`--db`, routed `*_test`); architecture and workflow checks
  passed. Plants: V18, row-1 `assumed_leaves`, row-1 `missing`, rows-3/4 provenance all pass (gaps); row-1
  origins from the expression fails S1 and S7.

## Honesty hunt (what I checked, `evaluate.py`)

- **Unknown read as zero.** No new zero path. The stated rows never give a value without a stated value
  (row 1) or the expression's value (row 2). Rows 3/4 set `value=None`, `NOT_AVAILABLE` (`:387-390`). The
  neutral identity is unchanged and returns the neutral operand's own origins and `detail_missing` (`_expr`, `*`).
- **A stated value labelled stronger than its origin.** Row 1 (`:378-385`) takes `evidence`, `sources`,
  `origins` and `coverage` only from the stated value. That value is checked by `_check_leaf`: TARGET and
  ASSUMPTION must be `ESTIMATED`, origins must be in `ORIGIN_ORDER` with no repeats. Correct. See F3 for empty origins.
- **Weakest-origin ordering.** `_origin_union` and `weakest_origin` (`:137-148`) both iterate `ORIGIN_ORDER`.
  `_check_leaf` refuses out-of-order, unknown and repeated origins. S5 and S6 hold the alphabetical traps (R1).
- **A refused record silently computed (D-4B.16).** Only `NOT_CONNECTED` and `NOT_RECEIVED` with an expression value
  return the expression (`_NOTHING_TO_READ`). Every other cause, including a misspelt one, falls through to the
  blocking rows, which is the safe direction. S10 and the builder's V16 cover it.
- **The gap naming the wrong record (D-4B.13).** Rows 3/4 keep the *stated* `Missing` (the CHARGE record) and add the
  node to `missing_leaves`, so ancestors name `revenue` and `revenue` names CHARGE. Row 2 drops the stated `Missing`,
  as the table says. `READ_AS` itself is 4b2's.
- **Portfolio k of n.** `compose` is unchanged apart from `origins` and `detail_missing`, which are taken over
  `included` only. Left-out Sites stay in `excluded`, as 3B3 has them. S7 is right.
- **MINI_GRID v3 against 3B1 and 3B3.** `stated_by` is product-only, and the 3B1 manifest parity passes in the 181.
  The four version edits are the only test edits. The sweep leaves only `test_s3_dispatch_assessment_postgres.py:455`
  (unrelated). Outside `structure/`, nothing reads `FactorValue` or `REGISTRIES` (grep: only tests). `compose`'s
  version check reads `registry.version`.

## Findings

### F1 Medium (acceptance gap): D-4B.17 has no failing test; V18 passes
- `backend/tests/test_4b1_stated_nodes.py:199`. The spec's S8 rate assertion is not written (Q1).
- **What is wrong.** The spec (§2.7 S8) and the reviewer guide (V18) require a plant that fails when `stated_by` is
  allowed on any MONEY exponent. Nothing fails today: I planted V18 (`check.py:185` →
  `any(d == "MONEY" and e != 0 ...)`) and got **30 passed**. The only unit assertion, `diesel_l` (L), has no MONEY
  exponent, so it cannot tell `is_money` from "any MONEY exponent".
- **Gap in the tests or the plant?** In the tests. The rule as built is right. The spec's `MONEY / KWH` plant cannot
  reach it, which I confirmed: on `contribution`, `MONEY/KWH` with SUM is refused by `STRUCTURE_COMPOSES`, and with
  NONE it is refused by `STRUCTURE_STATED`, but for `composes`.
- **Why it matters.** It is a named gate with no proof. A later loosening of the rule would pass unnoticed.
- **Fix (after the Architect rules Q1).** Add an S8 case: `_plant(MG, "contribution", expression="revenue * om",
  unit=MONEY*MONEY, composes="SUM", stated_by=FilledBy("COMMERCIAL_RECORD", "CHARGE", None))`. Run on the branch it
  raises `STRUCTURE_STATED`; under V18 it passes `check`. `revenue * delivered_kwh` (`MONEY*KWH`) behaves the same.
  Both were verified in a scratch copy. Then re-run V18 and record that it fails.

### F2 Low (test gap, spec-defined behaviour): parts of §2.3's table are unpinned
- `evaluate.py:378-390`, with no corresponding assertions in the test file.
- Plants that pass all 30 4b1 tests:
  - (a) row 1 with `assumed_leaves` always `()`;
  - (b) row 1 dropping the stated `missing` (`missing = None`);
  - (c) rows 3/4 taking `sources`, `origins` and `coverage` from the stated value instead of from the expression.
- The code is right today. These fields matter for 5a's target side: a stated budget line carried as TARGET must
  stay in `assumed_leaves` and keep its `Missing` with `blocks`.
- **Fix.** Add one S-case with a stated value carried as `TARGET` (`ESTIMATED`). It should assert
  `assumed_leaves == ("revenue",)` and `missing.blocks == ("collected", "contribution")`. Also assert S4's revenue
  `sources` and `origins` equal the expression's.

### F3 Medium (spec question for the Architect; not a 4b1 acceptance gap): an empty `origins` on a valued part
- **What happens.** `_origin_union` treats `()` as "adds nothing". In 4b2, the money leaves will carry origins while
  `ProductLeafSource` leaves (snapshots, declared price, calendar) keep `()`. The `LeafValue(...)` calls in
  `sources.py` pass no origins. So, for example, `contribution` over source-emulated records and a part with unknown
  provenance reads `weakest_origin == "source-emulated"`. That part could be simulated telemetry.
- **Why it matters.** D-4B.2 says "no total is shown as a stronger ... provenance than its weakest part". With an
  unknown part, the label can be stronger than the truth, and 3A5's rule on 5c reads it.
- **The question.** Should a valued, non-NEUTRAL leaf be required to carry an origin (a runtime check, or an explicit
  "unknown" ranked weakest)? Or is origin deliberately defined over records only, with the evidence class covering
  the rest? Rule it before 4b2 builds providers and before 5a and 5c read `origins`. A change after merge needs a
  ruling anyway (guide, Risks).

### F4 Low (spec text): §2.7's regression line contradicts §2.1
- `specs/4b-money-leaves/spec.md:185`: "only the `:366` edit". §2.1 and handshake P1 name `:366` and `:652`. The
  build makes both edits, which is correct.
- **Fix.** The Architect corrects the line. Not the implementer's.

Info: spec §0 names the branch `task/4b1-stated-nodes`; the dispatch's `task/4b1-money-leaves` was used. The packet
says so.

## Judgements asked for

- **V18 does not fail.** A test gap, not a plant or code defect (F1).
- **Mid-build Q1.** I agree with the builder: a `MONEY^2` SUM node plant isolates D-4B.17. `MONEY*KWH` does too.
  Plant it on `contribution`, which has no parents, so `STRUCTURE_UNIT` passes. A new row is not needed. Do not
  reorder `_CHECKS`. Moving `STRUCTURE_STATED` before `STRUCTURE_COMPOSES` only to serve one test would change the
  documented code-major order and `CODES`, for no product gain. The Architect rules.
- **P2 deferred to 4b2; S1-S10 built in 4b1.** Both correct:
  - §3.2 (a 4b2 section) holds the T6 table and body edits, alongside the `SOURCE_STATE` change they test. Rulings
    P2 says "4b2 edits T6".
  - Making the edit in 4b1 would turn T6 red against unchanged states.
  - §2.7 and §8 assign S1 to S10 to 4b1. The dispatch's "S5-S10" was the narrower reading.
- **282-value parity with `stated` empty.** Confirmed. I re-ran the probe with sha256 instead of `hash()`. Python's
  `hash()` of a string is salted per process, so the packet's "identical repr hash" is only meaningful with a fixed
  `PYTHONHASHSEED`. I widened it to 4 variants × 3 Sites × 47 factors = **564 values**, adding no price, no staff and
  no tariff. Main (archived tree, v2) and the branch (v3) gave the same digest, `9001fdd5c1cfc142`. On the branch, the
  new fields are `stated=False`, `computed=None` and `origins=()` everywhere: 0 violations.

## Checks run (my own output)

All with `PYTHONPATH` = worktree `backend`, `backend/tests`, `contracts`, `simulator`. Module paths were verified:
- `/opt/assetecon/AssetOpsV1-4b1/backend/assetops_backend/structure/evaluate.py`
- `/opt/assetecon/AssetOpsV1-4b1/contracts/assetops_contracts/__init__.py`
- `/opt/assetecon/AssetOpsV1-4b1/backend/tests/test_3b3_structure_evaluate.py`

- No DB, pooled (`heavy-slot.sh`, `DATABASE_URL` and `ASSETOPS_TEST_DATABASE_URL` unset): `test_4b1_stated_nodes.py`,
  `test_3b3_structure_evaluate.py`, `test_3b1_structure_registry.py`: **181 passed** in 2.89 s.
- Postgres: `heavy-slot.sh --db`, base `assetops_test` on 127.0.0.1:55432, routed by the harness to a run-owned
  `*_test` clone. `test_3b3_structure_read_postgres.py`: **5 passed** in 5.6 s.
- `tools/check-architecture.ps1`: **passed**. It needed `ASSETOPS_GUARD_PYTHON` set to the main checkout's
  `.venv` python, because the worktree has no `.venv`. Without it, the chain-structure guard says it cannot run, which
  is an environment issue and not a finding. `tools/check-agent-workflow.ps1`: **passed**.
- Plants, each applied alone to a scratch copy
  (`/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/rev4b1r1-plant`,
  `git archive aa5e78036`). Each was run against the 4b1 file and restored from `git show`:

  | Plant | Result |
  |---|---|
  | V18 (`is_money` → any MONEY exponent) | 30 passed (F1). With it, the MONEY^2 and MONEY*KWH plants pass `check`; without it, they raise `STRUCTURE_STATED`. |
  | Row 1 `assumed_leaves` always `()` | 30 passed (F2a) |
  | Row 1 `missing = None` | 30 passed (F2b) |
  | Rows 3/4 provenance from the stated value | 30 passed (F2c) |
  | Row 1 origins from the expression | **failed** S1, S7 (good) |

- The worktree's `git status` is clean after all runs.

## Cited, not rerun (builder, same revision `70d40757e`/`aa5e78036`)

- 336 passed for the structure and commercial selection with a DB.
- check-all: 40 guards passed at `70d40757e`.
- Plants V1 to V6 and V16 each fail their named tests (packet table).
- The commit after `70d40757e` changes only docs, so the code revision is the same.

## Not verified

- The 273-file select-tests tier and any full suite (coordinator's to schedule).
- Whether `5a`'s use of the new fields fits.
- `build_commercial_reads` against a real Postgres store: only the monkeypatched test exists, and 4b2 exercises it.

## Residual risk not in the packet

- F3, origins with unknown provenance.
- Every production leaf today has `origins == ()`, so `weakest_origin` returns `None` on every real read until 4b2.
  A screen must not read `None` as "no weak part".
- `_check_leaf` does not validate `Missing.cause` against `CAUSES`. Any unknown cause on a stated value blocks, which
  is safe, but 4b2's providers should be held to `CAUSES`.

---

# Review r2 (verification, fix round 1, head dc731bf29)

Verdict: ACCEPT WITH ONE FINDING (R2-1, Low/Medium test gap). Reviewer text: `.agent/review-4b1-r2.md`.

- F1 to F4 fixed as classes: S8 plants for MONEY^2 and MONEY*KWH with no-stated_by controls (V18b); provenance rows 3/4 and TARGET row 1 pinned; D-4B.18 in one door (`_check_leaf`, also used by `_check_stated`): exemption is NEUTRAL or family CALENDAR only, `()` refused and never inferred, `unknown` ranks last; spec text fixed.
- Ran (no DB): 4b1 + 3B3 tests, 112 passed. Not run: builder's 191, check-all, Postgres 3B3, frontend.
- Plants in a scratch copy, both survived all 112 tests: P1 (refuse `()` only when the leaf has a currency) and P2 (exemption widened to CALENDAR plus OPERATIONAL_RECORD).
- R2-1 (test gap, code right): S11(a) covered only `om` and `outstanding`; no test refused `()` on each non-CALENDAR family or on a non-money leaf.

## R2-1 closed (builder, commit bfe57c2f0)

`test_s11a_every_valued_part_with_empty_origins_is_refused` is parametrized from `REGISTRIES`: every valued leaf row not in CALENDAR (money and non-money) plus every stated node, each with empty origins, asserting `STRUCTURE_ORIGIN` on that factor (38 S11 cases; `test_s11a_the_registry_yields_money_and_non_money_leaves` proves both sets non-empty).
- P1 replayed: 20 failed. P2 replayed: 3 failed. Each reverted with `git checkout`; tree clean.
