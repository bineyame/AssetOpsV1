# S4-02b phase 1: fresh Claude review (`fuel-cost-1` model and consequence store)

Reviewer: fresh Claude (did not build this). Branch `task/S4-02b-fuel-consequence`. Diff reviewed: `16ba22d..bc88a0e`
(`7cbdef7`, `5b4be01`, `8eb4ee9`, `bc88a0e`). Judged against:
- packet `tasks/S4-02b-fuel-consequence.md`, phase row 1 (:37) and the contract items it owns (:18-20, :24-26);
- `D-2026-10-13-s4-bounded-financial-basis` and its `fuel-cost-1` addendum (`.ai/DECISIONS.md:4101-4109`);
- Architect Q1/C4 (`.agent/architect-S4-02-answers.md`);
- the handoff, questions Q1-Q10 and `.ai/CODE_STATE.md` "S4-02b phase 1".

## Verdict: ACCEPT with carries

The model follows the Architect rulings closely, and I could not break it with the probes below:
- C4 fail-closed containment per contiguous Candidate component;
- interval-once arithmetic;
- no `upper_minutes`;
- whole-window price selection;
- exact Fraction arithmetic with a ceiling to 50 digits.

Migration 0011 is sound:
- the tables are append-only;
- the number/amount CHECKs and the chain trigger hold;
- dirty work is written only by the triggers;
- a work item can have only one SUCCEEDED attempt;
- the downgrade and re-upgrade are clean.

C3 holds.

There are two Medium findings.
- **M1** is a defect in what goes into the consequence basis digest. With today's assumption store, it makes an
  *unchanged* price produce a new consequence revision. Phase 2a's STALE rule depends on this digest.
- **M2** is a factual error in the Q9 report. The packet makes Q9 owner-facing.

**Fix M1, and L1 (a one-character migration CHECK), as the first commit of phase 2a.** Do this before any consequence is
persisted to a walkthrough or demo database, and before the 2a worker or read compares bases. Correct M2 in the 2a
handoff and in `CODE_STATE`. The remaining items are carries.

## Checks I ran (results as observed)

- **Focused suites:** `pytest tests/test_s4_fuel_cost.py tests/test_s4_consequence_store_postgres.py
  tests/test_s4_assumptions_postgres.py` on my scratch DB `assetops_s402b_rev1_test`.
  - Result: **60 passed** (34 + 8 + 18).
  - The DB name has to end in `_test` (`test_s1_bindings_postgres.py:66`). My first attempt, on `assetops_s402b_rev1`,
    errored for exactly that reason. That was a harness refusal, not a product failure.
- **Downgrade:** alembic `downgrade 0010_financial_assumptions` on the scratch DB, then re-upgrade.
  - After the downgrade, 0 `financial_consequence%` tables and 0 dirty triggers remained.
  - The re-upgrade to `0011_financial_consequences` was clean.
- **`tools/check-all.ps1`:** **All 9 guards passed**.
  - The orphan scan reported 31 tagged and 12 baselined.
  - The working tree has unrelated uncommitted edits (task files and `frontend/docs/architecture/*` checkers) that
    predate this review. The guards ran over the working tree as it is.
- **Not run:**
  - The full backend suite, per the dispatch. The implementer's 2014 is unverified by me.
  - Frontend tests, `tsc` and the build: no frontend file changed.
  - Layout evidence: not applicable, because phase 1 has no UI.
- **Model mutations** (`fuel_cost.py`, run against `test_s4_fuel_cost.py`, each reverted with `git checkout --`):

| Mutation | Result |
| --- | --- |
| Coverage check (`merge(...) != components`) disabled | 2 failed |
| Candidate-span-is-a-stored-observed-segment check disabled | 1 failed |
| Upper rounded `ROUND_FLOOR` instead of ceiling | 1 failed (P4) |
| Run input-membership check disabled | 1 failed |
| Binding-valid-over-interval check disabled | 1 failed |
| Negative-power check disabled | 1 failed |
| Lifecycle `SUPPORTED` check disabled | 1 failed |
| "Exactly one primary INTERVAL" and generator-mismatch check disabled | **34 passed**: untested (L5) |
| "Candidate span inside Finding window" check disabled | **34 passed**: untested (L5) |
| `price.value` removed from the basis | 34 passed. Acceptable: the price revision ID is immutable and implies the value |

- **Migration mutations** (`0011`, run against `test_s4_consequence_store_postgres.py`, reverted):

| Mutation | Result |
| --- | --- |
| Assumption dirty trigger not created | 1 failed |
| `attempt_one_success` unique index removed | 1 failed |
| `unpriced_has_no_amount` CHECK removed | **8 passed**: not isolated (L5) |
| SUCCESSION `affected_to` CASE replaced by `NEW.valid_to` | 8 passed. Equivalent under every reachable input (a SUCCESSION is always open-ended, `assumptions.py:210-214`), so this is not a gap |

- **Reviewer probes:**
  - **Future SUCCESSION probe (M1).** This was a temporary scratch test in my scratchpad, not committed.
    - Publish v1, derive and append for the 2026-10-06 power Finding.
    - Then publish v2, the SUCCESSION from 2030.
    - Re-derive. The price revision is the same (1.25), and so is the amount (3.4375).
    - But the considered assignment ID changed (`e489a2a3…` became `63ec9e9e…`).
    - Result: `basis_same=False`, and `append` stored **revision 2** (`replayed=False`).
    - v2's dirty work covers only `[2030-01-01, ∞)`.
  - **Ordinary-data probe (Q9, M2).** I ran `load_input` + `quantify` read-only over every latest FindingRevision in the
    existing S4-02a walkthrough DB `assetops_s402awalk`, which holds the ordinary S4 data. Findings are under Q9 below.
  - **Zero-width episodes.** I searched `finding_revision` in `assetops_s4walk`, `assetops_s402awalk` and
    `assetops_test`. There were 30, 30 and 1 rows, and **0** with `episode_start = episode_end`, so L1 is latent today.

## Model correctness against the rulings

- **Containment (C4).**
  - `quantify` builds `C` only from the Finding's own candidate spans. Each span must exactly equal a stored observed
    `CANDIDATE_AVOIDABLE` segment of a linked INTERVAL assessment (`fuel_cost.py:296-307`).
  - It merges touching spans into components (`:311`).
  - It requires each selected reading to lie wholly inside one component (`:346-350`).
  - It requires the union of the readings to equal `C` exactly (`:351`).
  - `upper_minutes`, `off_before` and `off_after` are absent from the input types, and a test asserts it.
  - The P2 shared-edge reading is counted once and names both spans.
  - The failure reasons distinguish unobserved, Necessary, Indeterminate and outside-Finding time (`:261-280`).
- **Overlap.**
  - Readings are sorted by start, and adjacent pairs are compared (`:340-345`).
  - That suffices: if `r_i` overlaps any later `r_j`, then `r_{i+1}` also starts before `r_i` ends.
  - The whole quantity is refused, and neither reading is chosen.
- **SFC over the whole interval.**
  - The SFC comes from the reading's as-accepted Foundation revision.
  - That revision must be one of the cited runs' revisions (`:361`), and its validity must contain the interval (`:365`).
  - It must hold exactly one distinct L/kWh value (`:372-376`), and that value must be positive (`:380`).
  - The binding validity must also contain the interval (`:387`).
  - Foundation `valid_to` is immutable (`0001:188-189`), so the containment test is stable.
- **Whole-window price** (`:434-457`):
  - one assignment must contain `[window_start, window_end)`, with half-open ends;
  - an internal boundary gives `PRICE_SPANS_WINDOW`, and overlap gives `PRICE_CONFLICT`;
  - the window is never partitioned.
- **Rounding.**
  - The upper is an exact Fraction, stored as `num/den` plus a 50-significant-digit `ROUND_CEILING` Decimal
    (`:253-258`).
  - `amount_high` is the exact product of that rounded-up quantity and the price, computed at a precision of 300
    (`:494-496`), and the DB CHECK enforces it (`0011:103`).
  - Rounding at every step is outward for an upper bound. Display rounding is correctly left to 2a.
- **Basis digest.**
  - The technical digest covers: model, parameter digest, FindingRevision, window, every linked assessment (both
    scopes), spans, the examined evidence IDs, each counted interval (envelope sha, endpoints, kW, SFC, Foundation and
    binding revision), and the quantity state and reason.
  - The consequence basis adds the price and the amount.
  - The content is right, except that it includes **assignment IDs** (M1).

## Findings

### M1 (Medium, fix first in 2a): the basis digest keys on assignment IDs, so an unchanged price re-revises the consequence

- **Where.** `fuel_cost.py:428`, `:439`, `:457` and `:504-505` (`considered_assignment_ids` in the basis). The handoff
  `.agent/S4-02b-phase-1-handoff.md:112` tells 2a to mark STALE when the "considered assignments differ".
- **Why it is wrong.** `plan_assignments` closes the old assignment rows and re-inserts the remainders under **new**
  assignment UUIDs, even though the revision is the same:
  - a SUCCESSION re-IDs the whole history of the open-ended assignment (`assumptions.py:214`);
  - a CORRECTION re-IDs both its left and right remainders (`:223-228`).

  So any later publication changes the basis of every consequence whose window lies in a re-IDed remainder, even when
  that window's selected price and amount are identical. The probe above shows this: future v2 led to revision 2 of an
  October consequence at the same 1.25 USD.
- **Why it matters.** It contradicts the packet:
  - item 3 (:20): "A future-effective price leaves yesterday's selected price and consequence current";
  - item 3 again: "change only consequences whose full-window selected price changes".

  The consequences:
  - Any recompute appends spurious revisions.
  - The handoff's suggested STALE rule would flag these consequences STALE/PENDING, but no dirty work covers them
    (v2's range is `[2030, ∞)`). They would stay pending forever, or until an unrelated recompute.
  - The v1 to v3 to v4 sequence already re-IDs the July-September and November-December remainders.
- **Fix.**
  - Replace `considered_assignment_ids` in the basis with the sorted, **window-clipped**
    `(revision_id, max(valid_from, window_start), min(valid_to, window_end))` tuples of the overlapping assignments.
    These are stable under remainder re-IDing outside the window. They still distinguish two `PRICE_SPANS_WINDOW`
    states over different boundaries, which is the concern behind Q6.
  - Keep `assignment_id` in `financial_consequence_assumption_revision` as lineage only.
  - Base 2a's STALE comparison on the selected revision (PRICED) or on the clipped tuples (UNPRICED), never on raw
    assignment IDs.
  - Add a test: publish v1 and append; publish v2; re-derive; assert the basis is equal and `append` replays.
  - Rework `test_unpriced_bases_over_different_price_boundaries_differ` (`test_s4_fuel_cost.py:200-210`) so that it
    still passes on boundary instants, not on assignment IDs.

### M2 (Medium, documentation and owner-facing): the Q9 "every ordinary Finding is `POWER_MISSING`" claim is wrong

- **Where.** `.agent/S4-02b-questions-1.md:51`, handoff `:94`, `.ai/CODE_STATE.md:5393`.
- **What is wrong.** The ordinary S4 data does contain accepted generator power. The registered KOBO gateway case
  (`F01-gateway`, publication `registered-kobo-publication` v3, which "also publishes … its output power every fifteen
  minutes", `runs/profiles.py:1864-1874`) has **33 accepted `generator_power` interval means**, 32 of them GOOD, on
  2026-10-02. They are present in `assetops_s4walk`, `assetops_s4cases` and both S4-02a walkthrough DBs.
- **What the latest FindingRevisions in `assetops_s402awalk` actually give** (11 rows):
  - **8 `POWER_MISSING`.** These are the authored state-only fixture cases.
  - **2 `FINDING_NOT_SUPPORTED`.**
  - **1 `POWER_COVERAGE_GAP`.** This is the F01-gateway Finding, `[05:15, 09:15)`. Its 16 means are all GOOD, all in the
    run's input set, all wholly inside Candidate time, and all on Foundation `c5cac745` with SFC 0.3 L/kWh valid all
    day. But each one is a **5-minute** mean (`05:25-05:30`, `05:40-05:45`, …) published every 15 minutes, so they cover
    only a third of the Candidate time.
- **Why it matters.** The packet (:41) requires reporting "how many ordinary Findings qualify … or state plainly that
  none qualified and why". The owner would be told the wrong reason, and the most instructive fail-closed example
  would be missed.
- **Fix.** Correct the three texts to the counts and reasons above.

### L1 (Low, latent; fix in the migration before merge): the dirty-work CHECK refuses a zero-width FindingRevision, which 0009 allows

- **Where.**
  - `0011:199`: `affected_to IS NULL OR affected_from < affected_to`.
  - `0011:321-322`: the trigger copies `episode_start` and `episode_end` into it.
  - `0009:102`: `finding_revision_bounds CHECK (episode_start <= episode_end)`.
- **Why it matters.** A zero-width FindingRevision is legal under S4-01's own schema, and Q1 itself reasons that one
  can exist. Its INSERT would now fail inside the Finding writer's transaction: the S4-02b trigger would block the
  S4-01 writer. I found 0 such rows today, so this is latent.
- **Fix.**
  - Relax the work CHECK to `affected_from <= affected_to` (consistent with the Q1 window CHECK), or skip the work row
    when the episode is empty.
  - Add a one-row DB test for this case.

### L2 (Low, carry): the parameter record's `reviewer` field is inside its digest and says "review pending"

- **Where.** `fuel_cost.py:77` is inside `PARAMETER_VERSION`, whose digest is pinned at
  `fuel-cost-1-cases-v1.json:4` and stored on every consequence row.
- **Why it matters.** Recording this review changes the digest. That is cheap now and costly once any consequence is
  persisted outside tests.
- **Fix.** In the 2a first commit, set it to the actual review record (this file, 2026-10-14) and re-pin the digest.
  Do this together with M1, before any walkthrough persistence.

### L3 (Low): interval duration truncates sub-second time

- **Where.** `fuel_cost.py:392` has `int((b - a).total_seconds())`. `0011:170` compares it with `extract(epoch)::integer`,
  which rounds.
- **What happens.** With sub-second interval endpoints:
  - the upper is computed on truncated seconds, which is the wrong direction for an upper bound;
  - when the fraction is at least .5, the DB CHECK fails the insert.

  Today's means are whole minutes.
- **Fix.** Use the exact `Fraction` of the timedelta, or refuse `INTERVAL_NOT_WHOLE_SECONDS`.

### L4 (Low, carry for 2a): pre-existing data gets no dirty work

Migration 0011 seeds no work rows for FindingRevisions or price revisions that exist when it runs. The triggers fire only
on new inserts. A walkthrough DB upgraded from 0010 therefore has neither a consequence nor pending work for its
Findings. 2a needs one of these:
- a bootstrap or backfill enqueue;
- a read that treats "no consequence and no work" as PENDING rather than as absent.

### L5 (Low): test gaps the mutations exposed

- The "exactly one primary INTERVAL" and generator-mismatch refusal (`fuel_cost.py:289-293`) is untested.
- The span-inside-window refusal (`:306`) is untested.
- The `financial_consequence_unpriced_has_no_amount` CHECK is not isolated. The clone case matches
  `"financial_consequence_unpriced"` (`test_s4_consequence_store_postgres.py:298`), and `unpriced_reason` satisfies
  that match on its own. A dedicated case is needed: UNPRICED with a valid `price_state`/reason but a non-null amount.

### L6 (Low, optional hardening)

The DB ties `price_revision_id` to a revision by FK, but it does not enforce three things:
- that `price_value` and `price_currency` equal that revision's value and currency;
- that a PRICED row has its PRICE link row;
- that the assessment links are complete.

The store does all three correctly. A deferred constraint trigger would make them DB invariants, as the rest of 0011
does. This is cheap while 0011 is unmerged.

### L7 (Low, docs)

- `.ai/CODE_STATE.md:5376` still describes the demo fixture as v1-v3.
- `.agent/S4-02a-phase-1-handoff.md:123` documents running `fixture` without `--step`, which now also publishes v4. The
  walkthrough script is correctly pinned. Note the change in `CODE_STATE`.

## Carry C3 (price fixture v4): holds

- v4 is a bounded backdated CORRECTION to 1.28 over `[2026-10-01, 2026-11-01)` with `expected_prior_step` v3.
- `test_v4_october_correction_appends_and_replays_safely` (passed) proves:
  - v1-v3 replay with their stored IDs;
  - a second full run writes nothing;
  - the current timeline becomes v1 / v4 / v1 around October.
- `run_fixture` defaults to `S4_02A_STEPS`, and `tools/s402a_assumptions_walkthrough.py:89` publishes only v1-v3.
- The M1 test copy truncates to three steps before appending its own v4.
- The S4-02a walkthrough DBs hold v1-v3 at 0010 and are untouched.

## Migration 0011 (focus)

- **Append-only.** `ledger_append_only` covers all six tables (`:231-246`). The probe UPDATE and DELETE on the revision,
  interval and work tables are refused.
- **Idempotency.**
  - UNIQUE `(finding_revision_id, type, consequence_basis_sha256)` backs the advisory-locked select-then-insert.
  - The concurrent-append test stores one row.
  - The chain trigger enforces `revision_no = max+1` and checks the prior.
- **Dirty work only via triggers.**
  - The AFTER INSERT triggers on `financial_assumption_revision` and `finding_revision` write the work rows in the
    writer's own transaction.
  - Guard rule 8 forbids any module from writing `financial_consequence_work`. It also confines the store to five
    tables, INSERT only.
  - Mutation: with the assumption trigger removed, the dirty-work test fails.
- **One SUCCEEDED attempt per work item.** A partial unique index enforces it (`:228-229`). The mutation is caught.
- **Window equals the FindingRevision episode.** The trigger enforces it (`:261-263`), and so does the assessment-link
  trigger (INTERVAL only).

## Q1-Q10 rulings

| Q | Ruling | Note |
| --- | --- | --- |
| Q1 window `<=` | **Acceptable** | It matches 0009's `episode_start <= episode_end`, but the work CHECK must agree (L1). Storing a `NO_CANDIDATE_TIME` row for a zero-width episode is fine and honest |
| Q2 run input-set membership | **Acceptable** | Stricter than citation and fail-closed. On ordinary data, all 16 F01-gateway means were in the run set, so it does not over-refuse |
| Q3 as-accepted SFC | **Acceptable** | This is the packet's own wording (:18, "as-accepted Foundation/binding revisions"). Residual: a later Foundation SFC correction neither requotes nor enqueues work. Name this in the 2a limitations |
| Q4 50-digit ceiling plus exact fraction | **Acceptable** | Outward at every step, and the amount product is exact. Display rounding stays in 2a |
| Q5 unavailable ignores price | **Acceptable** | No amount exists to reprice, and a price change carries no information for an unavailable quantity. No owner ruling is needed. Mention it at the checkpoint if the owner asks |
| Q6 replay of an older identical basis | **Needs fix (via M1)** | The real hazard is the opposite one: identical prices get *different* bases. After M1, 2a must still compare the head revision, as the Implementer says |
| Q7 parameter as a code constant | **Acceptable** | The packet links assumptions only "when represented as an assumption" (:24). The version, digest and value are on every row. Finalize the reviewer field (L2) |
| Q8 currentness deferred to 2a | **Acceptable** | Phase 1 derives from the exact revision. 2a owns latest-revision and window currentness |
| Q9 ordinary Findings | **Needs fix (M2) then owner/coordinator** | See below |
| Q10 non-GOOD skipped, GOOD negative refuses | **Acceptable** | Coverage decides, so a SUSPECT gap fails closed (tested). A negative GOOD mean is refused outright |

No question needs the Architect. Q9's remaining choice is a planning and owner choice, not an architecture question.

## Q9 assessment: the S4-02b owner checkpoint

**From today's ordinary data, no positive amount can be shown.**
- 0 of the 11 latest FindingRevisions qualify.
- The only Finding with ordinary accepted power, the registered-gateway F01 Finding, fails `POWER_COVERAGE_GAP`. Its
  generator power is a 5-minute mean published every 15 minutes.
- That failure is the correct fail-closed outcome under C4. Interpolating or stretching the 5-minute means would be the
  unsupported interpolation that D-2026-10-13 forbids, so the rule must not be relaxed.

The least-cost honest options for 2a/2b, cheapest first:

1. **Authored power-mean case on the ordinary S4 path (recommended).**
   - The S4 fixture cases are themselves "authored public Batch V2 content posted by the registered gateway credential"
     (`s4-finding-cases-v1.json:4`). So one new, labelled case with contiguous 5-minute generator-power means on its own
     day is the same evidentiary class as every other ordinary S4 Finding.
   - The phase-1 Postgres `PowerSite` already proves this path. It gives 2.75 L, which is 3.4375 USD at v1 and 3.52 USD
     at v4.
   - Put it in a new versioned spec or walkthrough step, not in `s4-finding-cases-v1`, so that S4-01 and S4-03 evidence
     stays valid.
   - At the checkpoint, show the owner the F01-gateway Finding as the honest `QUANTITY_UNAVAILABLE`
     (coverage-gap) example beside it.
2. **Gateway-sealed positive.**
   - A new `registered-kobo-publication` version in which generator ac-power cadence equals the 5-minute timestep, so
     the means tile Candidate time.
   - This is more "ordinary", but it is a Lab/publication-profile change with S2/S3 evidence lineage. It is larger and
     belongs to the Planner, not to 2a.
3. **No positive ordinary case.** State plainly at the checkpoint: "none qualified: the ordinary Findings carry
   generator state only, or 5-of-15-minute power coverage". Show the positive amount only from the labelled test case.
   The packet permits this, but it is the weakest demonstration.

Option 1 meets the packet's "at least one positive amount from ordinary accepted data". It fits within 2a/2b, provided
the case is labelled as an authored fixture in the walkthrough and on the owner screen. Whether the owner accepts an
authored S4 case as "ordinary" should be put to them explicitly at the checkpoint, not assumed.

## Carries for phase 2a

1. **First commit:** M1 (basis content plus test), L1 (work CHECK `<=` plus test) and L2 (reviewer field, re-pinned
   digest). Do these before persisting any consequence to a walkthrough or demo DB.
2. Correct the Q9 text (M2) in the 2a handoff and in `CODE_STATE`. Report the 8 / 2 / 1 split and the F01-gateway
   coverage reason.
3. Base the STALE/PENDING comparison on the selected price revision, or on the window-clipped boundary tuples, and the
   latest FindingRevision. Never base it on raw assignment IDs. Treat a replay of a non-head revision as recompute input
   (Q6).
4. Add a backfill or bootstrap for pre-0011 data, or read "no consequence, no work" as PENDING (L4).
5. Name the as-accepted SFC limitation in the read and limitations: no requote on a later Foundation correction (Q3).
6. Close the test gaps in L5. Consider L3 and L6 while 0011 is still unmerged.
7. For the walkthrough positive case, use option 1 above, keep it labelled, and leave `s4-finding-cases-v1` unchanged.
