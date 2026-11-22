# 6h review: named-option levers (discovery review, W5)

## Round 1 (discovery), 2026-11-22, branch `task/6h-named-option-levers` at `c2442a68b`

**Summary (verdict: ACCEPT with findings fixed on the branch; no High, no Medium).**
- Read against spec rev 1, rulings D-P6.51 to D-P6.67, the handshake, the packet, the owner file, and every file in
  `git diff main...HEAD` (base `19c8b2b3b`; `main` has not touched any 6h path since the base, and no `0073` exists there).
- The change rule (record minus the decision month's level, keyed by (option, factor), missing base named, never 0),
  the forced `OUTCOME_FACTOR` and `also` scope, `LeafChange.currency`, D-P6.60/61 in `_value_option`, the
  `BOUNDS_NOT_CHECKED` rewrite after R1 to R4, branches 15 to 22 (6 to 13 for the grid only), `check_lever_paths`,
  migration 0073 (live constraint names, reversible, guarded downgrade, append-only triggers), R1 to R9, both stores
  and the CLI all match the spec. The nine levers match §5.1. Every `changes` tuple is in registry order (checked).
- The parity golden was committed first (`b3137c352`). Capture script and golden are unchanged since then.
- Plants: I reran one myself. The "records by factor alone, newest of any option" plant (as a scratch pytest plugin,
  worktree untouched) fails T1, T1o and **T1b** (the stopgap reads −16), so the N10 fixture does its job.
- Seven Lows (merge hygiene, one loosened head assertion, robustness on catalogue drift, a spec wording claim, the
  admitted W2 order, a stale handoff file). Q4: I agree with the builder's default (see the questions below).

### Checks run (worktree root, this head)
- `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- test_6h_{parity,levers,prepare,words,evaluate,run,
  option_record,migration_postgres,run_postgres}.py test_6c_evaluate.py test_6c_difference.py -q`: **170 passed**, 8
  warnings, 30.4 s.
- `ASSETOPS_GUARD_PYTHON=... pwsh -NoProfile -File tools/check-architecture.ps1`: "Architecture check passed."
- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- Plant probe (above): 3 failed, 8 passed in `test_6h_evaluate.py`, as expected.
- Probe: K2 with `short_nights` missing gives `BOUNDS_NOT_CHECKED`, every row `DEFERRED`, evidence `DECLARED` (inside
  0072's `evidence_class` check), so Kasarani on the DD world before Q11 stores a run instead of `RECORD_INVALID`.
- Not rerun (cited): the builder's 69-file comparison set (pure 2 failed / 2714 passed / 1 skipped on branch and on base
  `19c8b2b3b`, Postgres 145 passed on both). The two failures are the pre-existing 3b1/3b3 `dispatch-3.3` vs `3.2`.
  Layout evidence: not applicable (no screen; G3 holds, the diff touches no `frontend/` file).

### Findings

**L1 (Low, merge hygiene) `.ai/state/index-3.md:24`.** The new line is numbered `199`. `main` already has `199` (DD2a)
through `202` (IA-P1) appended at the same place, so the merge will conflict and the numbers will clash. Fix: renumber
to the next free number (203 at today's `main`) in merge prep.

**L2 (Low, test strength) `backend/tests/test_6a_migration_postgres.py:254`, `:511`.** Both head assertions became
`len(...) == 1`. That still proves there is one head, but no test now pins *which* head: `test_6h_migration_postgres.py`
calls `assert_at_head` only. A stray migration that became the single head would pass both files. This is not an
acceptance gap; the packet names it (deviation 1). Fix: in `test_6h_migration_postgres.py` assert
`scripts.get_heads() == ["0073_named_option_levers"]`, and keep 6a's one-head form.

**L3 (Low, robustness) `backend/assetops_backend/decisions/models.py:84`, `:87`.** `stated_changes` does
`next(o for o in lever.options if o.key == option.option_key)` and `lever.change_sources[leaf]`. If a stored option's
key ever leaves the catalogue (an option renamed or removed after `prepare`), `evaluate` crashes with a bare
`StopIteration` instead of a refusal. Today nothing triggers it. The grid path has the same kind of exposure, but there
the study match reports the mismatch first. Fix (small): in E3 refuse `LEVER_UNKNOWN` (D-P6.38's code) when a
`STATED_OPTIONS` option key is not in `lever.options`, and add one test. Alternatively, record it as accepted residual
risk.

**L4 (Low, preference; deviation 6) `backend/assetops_backend/decisions/evaluate.py:121`.** `also` is passed only when
the lever's purpose factor is a row of the registry, and only as a keyword when it is non-empty. The reason is that 6c's
planted registries lack the factor and three 6c tests monkeypatch `difference` with a 3-argument double. In production,
branch 3 of `check_levers` guarantees the row exists, so the guard never fires and no figure moves. Parity holds. The
cost is a production line shaped by test doubles. No fix needed if the Architect accepts it (question A2).

**L5 (Low, spec wording) spec §5.4 last sentence vs. code.** The spec says a lever with no words "fails the start-up
statement check (SC-1's exhaustive selector)". In the code, each `decision_lever.*` statement is exhaustive only over
its own literal `values` list. The tie to `LEVERS` is `test_6h_words.py::test_7_every_selector_the_catalogue_names_has_its_variant`
(test 7), not start-up. A lever added to `LEVERS` without words starts up and fails test 7. That meets §10.2 test 7 but
not the sentence in §5.4. Fix: amend §5.4 to "fails test 7", or add a start-up check. Default: the spec wording.

**L6 (Low, process; W2) packet "Test-first".** For 6h2 and 6h4, the code was written before their tests first ran.
The packet says so. The tests carry the spec's hand-derived literals, all 16 plants are reported failing, and I
reproduced the one plant that matters most for 6h2 (the plant probe above). No fix. Recorded for the W2 count.

**L7 (Low, tidiness) `specs/6h-named-option-levers/6h-handoff.md`.** A partial mid-build handoff ("6h2 and 6h4 next")
is committed in the spec folder and is now stale. Fix: delete it in merge prep, or move it to history. The packet and
state entry already carry the outcome.

No acceptance gap found against spec §11 questions 1 to 7:
- (1) `check_lever_paths` runs in `check_all` and every type has a lever.
- (2) `evaluate.py` and `run.py` name no structure.
- (3) N1 is 1670.00, also through Postgres.
- (4) T1 and K2 are `CONDITIONAL` and unranked, and the purpose factor's change is shown.
- (5) N1m, T1 and the missing-base test name the missing input and never read 0.
- (6) The golden is equal byte for byte (Q4 aside).
- (7) T1o passes.

### Questions for the Architect (each with a default)

- **A1 (packet Q4, D-P6.61's premise).** `test_6c_evaluate::test_4_a_node_with_no_value_is_named_by_its_own_missing_leaves`
  monkeypatches `difference` with a double whose Deltas carry no origins, while the changed leaf carries
  `demo-simulated`. Under D-P6.61 that row's `source_class` reads SIMULATED; the golden says RECORDED. I checked this:
  the double breaks the premise ("every known changed leaf is already in `contribution.used`"), and no real `difference`
  result differs. **Default: accept the exemption as built** (that one key's `source_class` only; every other field of
  that key and every other key compared byte for byte). Record it as a ruling, so that "the golden is never refreshed"
  stays an explicit rule with one named, explained exception.
- **A2 (deviation 6, L4).** Is the guarded `also` in `_value_option` acceptable? **Default: yes.** It is forced by 6c
  tests that §10.2 says stay untouched, and it is unreachable in production.
- **A3 (R6 sign).** `_value_ok` accepts negative record values, which matches spec R6. A negative crate-days,
  uncovered-nights or buses level means nothing, but a negative `excess_kwh` could be real. **Default: no sign rule in
  6h.** If one is wanted, add it later as per-leaf data, not as a code branch.
- **A4 (packet Q1 to Q3).** Q1 "evening supply with no standby generator" (SC-1 bans `one`/`single`); Q2 the unused
  `levers` argument of `check_lever_paths`; Q3 prepare parity covered by the prepare tests. **Default: accept all three
  as built.**

### Residual risk the packet does not name
- The demo values depend on DD6.2 stating records with the right units. R5 compares `unit` with
  `str(registry unit)`, so `buses` and `model_factor` take the literal `1`, and `contract_rate` takes `MONEY/DAY`. A
  wrong unit string refuses `BAD_RECORD_UNIT`, which is loud, not silent.
- `DecisionBundle` does not carry option records. 6f can name a missing record from `missing`, but to show the stated
  document and its basis it needs its own read (a 6f seam, outside 6h's scope).
- No 6h test drives `evaluate_options.py` (the CLI) on a stated lever. `--study` is already optional, and the service
  path is covered on Postgres. DD6.2 is the first CLI use.
