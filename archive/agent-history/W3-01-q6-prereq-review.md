# W3-01 q6 prerequisite review (independent, per commit)

Reviewer: fresh Claude reviewer (not the author). Branch `task/W3-01-estate-claim-action-roots`, handoff `f8ca78d1`.
Authority: W3-01 build spec "Prerequisite review r1 rulings", "Run 6 rulings (q6)", "W4-01 Run 3 shared cold/EV
snapshot handoff"; W4-01 "Run 3 rulings (q3)" ruling 6; W3-02 "Run 6 dependency amendment"; handoff readings 1a-4c.

## Checks run (by this reviewer)

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Private DB `w301n_test`, one serial run of the four touched files
  (`test_w301_w1_snapshot_helpers_postgres.py`, `test_w301_w1_money_snapshot_helpers_postgres.py`,
  `test_w301_cold_selection_on_postgres.py`, `test_w301_ev_selection_on_postgres.py`) at `f8ca78d1`:
  **14 passed, 0 failed, 0 skipped, 234 s**. DB dropped afterwards.
- Not rerun here: the W1 consequence/money regressions (handoff: 80 and 74 passed) and the W2 cold/EV Site read
  suites `test_w203_cold_reads`, `test_w206_ev_reads`, `test_w207_ev_site_reads` (handoff: 63 passed, 38 min). The
  implementer's mutation results were not reproduced. Default-mode equivalence was instead verified by diff (below).
- Merge commits `2310ccda`/`f8ca78d1` carry only `.agent/` changes; no code between the reviewed commits.

## Commit 1: `2a1b59cf` (reason text): ACCEPT

The reason now ends `no stored completion selection establishes its state at the cutoff`; code and outcome are
unchanged; the test asserts the exact suffix and that the old phrase is absent. That matches the Run 6 Low ruling.
Reading 1a (the whole tail was replaced, so the cutoff phrase is not doubled) is covered by that ruling.
No findings.

## Commit 2: `c55dadd4` (`0a`, `select_consequence_on`): ACCEPT (one Low worth fixing on the branch)

The signature `select_consequence_on(c, tenant_id, site_id, finding_revision_id, known_at)` matches Run 6 and the
W3-02 amendment. No transaction is opened or committed: `selected_on`, `load_input_on` and `snapshot_on` are static
methods that run only on `c`. The public `snapshot` and `load_input` keep the same statements inside their own
`_run(..., "REPEATABLE READ")`. With `known_at=None`, the SQL of `load_input_on` is byte-identical to before.

Column fact verified: in `migrations/versions/0011_financial_consequences.py`, `financial_consequence_revision` has
no `created_at`. Its insert time is `recorded_at timestamptz NOT NULL`, written from the store's single
`clock_timestamp()` instant (`postgres_consequence_store.py:198`). No later migration adds a `created_at` column.
Using `recorded_at <= :k` with `(revision_no DESC, id DESC)` is correct. Price as-of uses
`snapshot_on(recorded_at=k)` (`recorded_from <= k < recorded_to`), not today's timeline. Readings are filtered by
`decided_at <= k`. Tests are non-vacuous: at k1 the UNPRICED revision 1 is CURRENT; at k2 the price is known and the
same revision is STALE with `PRICE_SELECTION_CHANGED` and is not repriced; the pin is exact; foreign and early
revisions are UNKNOWN; created-without-consequence is PENDING; a superseded revision is HISTORICAL.

- **L1 (Low, `financials/consequence_read.py:304` vs `:331-333`): the precedence differs from W1 `read`.** W1
  checks `not finding_revision_is_latest -> HISTORICAL` before `head is None -> PENDING`. Here a FindingRevision that
  was superseded by `:k` and has no consequence recorded returns `PENDING NO_CONSEQUENCE_AT_CUTOFF`. That suggests
  recompute work on a revision that will never get any. Run 6 says to apply W1 `read` currentness semantics, so this
  is an acceptance gap in reading 2c, not a preference. It is reachable only when a caller pins a non-head revision;
  the estate head path through `index_snapshot_on` never does. Fix: when `rev["latest_id"] != finding_revision_id`,
  return HISTORICAL with `FINDING_REVISION_SUPERSEDED` before the `head is None` branch, and add one assertion.
  No Architect decision is needed.
- **L2 (Low, test gap):** `PRICE_NOT_AT_CUTOFF`, `CONSEQUENCE_LINEAGE_MISSING` and `FINDING_INPUT_MISSING` are not
  exercised. The named Run 6 tests are present and pass. These are defensive branches that no fixture writer
  produces, so optional.

Readings: 2a covered by the column fact. The ruling's "created_at" names a column that does not exist; the
Architect should acknowledge the `recorded_at` substitution, which is non-blocking. 2b covered ("a later
consequence or price cannot change an earlier read"). 2c covered except L1. 2d covered (Run 6 gives the signature
with no `source_open`; the source and day gates belong to the caller). 2e covered ("PRICED/COST is a current claim
only ... at the live cutoff").

## Commit 3: `da15d71f` (`0b`, `for_finding_on`, source gate, `ProvenanceReadsOn`): ACCEPT

The signature `for_finding_on(c, tenant_id, site_id, finding_id, known_at)` matches. It reads only through
`index_snapshot_on`, `index_lineage_on`, the new static `money_revision_on` and `select_dispatch_days_on`, all on
`c`; nothing opens or commits a transaction. `ProvenanceReadsOn(c)` provides exactly the three methods that
`PublicProvenance` calls (`link_rows`, `finding_revision_evidence`, `consequence_inputs`). The ledger's own methods
delegate to it with the same SQL inside their own `_run`. The matched rule
(`matched_through_selection_seq >= day seq` and the window not in `deferred_window_starts`, from a pass completed by
`:k` of `MATCHER_VERSION`) matches W1 `match_state` evaluated as of `:k`. An unavailable day forces
`PENDING_REASSESSMENT`; the function never returns ELIGIBLE without proof. Composition passes
`build_finding_store`, so `index_snapshot_on` is wired and the `AS_OF_GATE_NOT_WIRED` branch is only a guard.
Tests are non-vacuous: live equals W1 ELIGIBLE with identical days; k2 gives PENDING with `LIVE_JOB` while the job
is finished now; k1 equals W1 as it read at k1; unknown, early and foreign inputs fail closed; the block equals the
W1 resolver's; evidence equals Finding-cited plus power IDs; a MIXED control withholds.

No findings above cosmetic. One nit: there is a single blank line before `def link_rows_on` in
`postgres_evidence_ledger.py`.

Readings: 3a covered ("exact selected Finding revision's episode", W1 latest rule). 3b covered (q6 reading 4, "selected seq matched by the
as-of pass and outside deferred windows"). 3c covered (fail closed). Database errors propagating rather than
mapping to `ELIGIBILITY_READ_FAILED` is acceptable because the shared transaction is aborted and the estate caller
maps the failure; it can never yield ELIGIBLE. 3d covered (additive `known_at`). The additive
`selection.model_version`/`cohort` on the q5 day dict and the `days=` keyword are additive, are needed by
`evaluate`, and change no public W1 behaviour (W3-02 amendment: "not silently alter their public W1 wrappers").
Covered.

## Commit 4: `4442d33c` + `8d73c035` + `9956b6b8` (cold/EV pinned mode): ACCEPT (one Low worth fixing before the W4 cherry-pick)

The shape matches W4-01 ruling 6 exactly:
`_snapshot(c, t, s, code, lo, hi, known_at, *, selection_cutoff=None, selection_seqs=None)` on both services, with
`selection_seqs` mapping analytic to int seq. In pinned mode it uses the exact stored window (equality), `sel.seq`,
`selected_at`/`completed_at`/`ar.created_at <= selection_cutoff` and same-tenant/Site run joins, and it returns
`selection_seqs` and `selection_cutoff`. An inconsistent pin raises `SelectionPinRefused` (a LookupError) and never
falls back. `selected_windows_on` implements the Run 6 intersection predicate, the greatest qualifying seq per exact
key, and the `(ws, we, analytic, seq)` sort. Cold groups both analytics per window. Everything runs on `c`; no
transaction is opened or committed.

**Default mode is byte-identical:** every removed line reappears verbatim in the added lines. The exceptions are the
two signatures, `return {` becoming `snap = {`, and `if` becoming `elif`. Both default SELECTs (cold covering, EV
equality) are unchanged text, and the returned dict gains keys only when `pinned`. That removes the regression risk
to the merged W2 screens at code level; the Site suites themselves were not rerun here.

Tests are non-vacuous: a whole-day W2 read selects nothing while the estate enumeration selects the exact window
with identical revision IDs and state. Outside the day returns `[]`. A later reselection is invisible at k1, and
pinning its seq at k1 raises `SelectionPinRefused`. An earlier cutoff gives HISTORICAL. EV covers two windows in one
day, a selection written after k0 over committed evidence, an unclamped `known_at` still raising 422, and clamped
`known_at` with a later selection cutoff not raising. `9956b6b8` isolates `selected_at` as the only excluding filter.

- **L1 (Low, `postgres_assessment_store.py:1750`, `:1769`, `:1833`, `:2375`, `:2393`, `:2448`): the pinned-mode
  contract has three silent paths.**
  - (a) `selection_seqs` passed without `selection_cutoff` silently runs the default, unpinned selection, which
    returns the newest head. W4 ruling 6 says "never a fallback to a newer head".
  - (b) EV in pinned mode with `known` None (no `known_at` and no watermark) skips the pinned SELECT, returns
    `selected=None`, and still echoes the caller's `selection_seqs` as if verified.
  - (c) Cold pinned mode silently drops `selection_seqs` keys that are not cold analytics, and also returns an empty
    selection when `known` is None.

  None of these is reachable through `estate_snapshots_on`. They are reachable through W4's direct `_snapshot`
  calls, and W4 cherry-picks this reviewed commit as-is. Fix: raise `ValueError` when `selection_seqs` is given
  without `selection_cutoff` or contains an unknown analytic; raise `SelectionPinRefused` when pinned and `known` is
  None. Add one test per guard, then name the fix commit in the W4 cherry-pick record. No Architect decision is
  needed.
- **L2 (Low, residual / input to Q7-1, `:1697` vs `:1779`/`:2402`): enumeration and pin bound `knowledge_cutoff`
  differently.** `selected_windows_on` filters `r.knowledge_cutoff <= selection_cutoff`, while the pinned SQL
  filters `r.knowledge_cutoff <= known` (the clamped value). Under Q7-1 option (a), a run whose `knowledge_cutoff`
  falls in (clamped, requested] would be enumerated and then refused with a 409 rather than skipped. This fails
  closed and does not happen on the fixtures: the W2 default reads already require `knowledge_cutoff <= watermark`.
  Record it with the Q7-1 answer, so that whichever rule is chosen applies to both statements.
- **L3 (Low, test gap):** the `ValueError` guards and the `completed_at`/`ar.created_at` pinned filters are not
  individually exercised. Only `selected_at` is isolated, by `9956b6b8`.

Readings: 4a covered (Run 6, "the exact stored window ... pins the enumerated seq"). 4b is Q7-1, with the
Architect and not ruled here. 4c covered: W4 ruling 6 and the W3 handoff note require only focused as-of and
ordinary cold/EV Site regressions before transfer, and the four q6-named `test_w301_estate_index_postgres.py` tests
need Lane B's estate core. The `selected_windows_on`/`estate_snapshots_on`/`SelectionPinRefused` helpers fall
within Run 6's allowance of a named wrapper over the same query. They add no second cold/EV SQL owner, because they
call the single `_snapshot`.

**Q7-1 support:** the API cleanly supports either answer. `known_at` (the W2 grammar and its clamp) and
`selection_cutoff` (the selection filters) are independent arguments on both `_snapshot` and
`estate_snapshots_on`. Option (a) passes clamped and requested; option (b) passes clamped for both. Neither needs a
code change, apart from the L2 consistency note.

## Readings needing the Architect

- 2a: acknowledge `recorded_at` as the consequence cutoff column, because the ruling's `created_at` does not exist.
  Non-blocking.
- 4b: Q7-1, already pending.
- All other readings are covered by a ruling. Commit 2 L1 and commit 4 L1 are implementer fixes against existing
  rulings.

## Verdicts

| Commit | Verdict |
| --- | --- |
| `2a1b59cf` | ACCEPT |
| `c55dadd4` | ACCEPT (L1 fix on branch recommended) |
| `da15d71f` | ACCEPT |
| `4442d33c` + `8d73c035` + `9956b6b8` | ACCEPT (L1 fix on branch recommended before the W4 cherry-pick) |

No High or Medium findings.
