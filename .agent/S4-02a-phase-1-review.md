# S4-02a phase 1: fresh Claude review (assumption store and SYSTEM publication)

Reviewer: fresh Claude (did not build this). Branch `task/S4-02a-site-assumptions`. Diff reviewed: `ec74ac6..4e694bb`.
`412b564` is the coordinator's handoff note only. Judged against packet `tasks/S4-02a-site-assumptions.md`:
- the phase 1 row (:37);
- contract items 1-2 (:18-19);
- `D-2026-10-13-s4-bounded-financial-basis`;
- plan-review carries C1, C2 and C7, and re-review carries R1, R2 and R4.

## Verdict: ACCEPT with carries

The schema, the triggers, the change_kind planner, the locking and the write-route refusal order are correct. They match
the packet, and I could not break them; the probes are below. There are two Medium findings. Both are confined to the
demo fixture and the idempotency digest, and neither touches the migration. They are cheap now, but become costly once a
walkthrough database holds published digests. **Fix M1 and M2 as the first commit of phase 2, before anything is
published to a walkthrough or demo database.** Nothing in the migration needs to change before merge. L1 is an optional
hardening that is cheapest to make now, because the migration is not merged yet.

## Checks I ran (results as observed)

- **Focused suites.** `pytest tests/test_s4_assumption_publication.py tests/test_s4_assumptions_postgres.py` against my
  own scratch DB `assetops_s402a_review_test`, using `ASSETOPS_TEST_DATABASE_URL`; the DB name must end in `_test`, see
  `test_s1_bindings_postgres.py:67`. Result: **45 passed** (30 + 15).
- **Downgrade.** I ran alembic `downgrade 0009_finding_store` on the scratch DB.
  - Both tables and both functions were gone, and `ledger_append_only()` (owned by an earlier migration) was correctly
    kept.
  - Re-upgrading to head (`0010_financial_assumptions`) was clean.
- **`tools/check-all.ps1`.** All 9 guards passed: architecture, navigation, agent workflow, registry, delivery
  fixtures, mock-gap fixtures, orphan scan (30 tagged / 12 baselined), scan fixtures and screen ledger.
- **Not run.**
  - The full backend suite was not run, per the dispatch. The implementer's 1953 is unverified by me.
  - The frontend suite, `tsc` and the build were not run: no frontend file changed.
  - Layout evidence is not applicable, because phase 1 has no UI.
- **Reviewer probes.** I wrote a temporary scratch test file, placed it in `backend/tests` only for the run and then
  deleted it. Nothing was committed. It found:
  - **Lock removed, race test reruns.** I replaced `pg_advisory_xact_lock` with a no-op by monkeypatching `text` in
    the store, then reran `test_concurrent_publications_against_one_prior_admit_exactly_one`. It **failed 5/5**, so the
    race test really exercises contention and is not vacuous.
  - **Column updates on assignment rows.** UPDATEs of `id`, `revision_id` and `recorded_from` are refused by the
    immutability trigger. Reopening a closed `recorded_to` to NULL is refused ("already closed").
  - **Two Site series.** Two Sites each get `revision_no = 1`, with no interference between them.
  - **Re-pricing the scheduled v2 at its exact start (2027-01-01).**
    - As a SUCCESSION: refused, `SUCCESSION_OVERLAP_NOT_PERMITTED`.
    - As an open-ended CORRECTION: refused, `CORRECTION_NOT_BACKDATED_OR_BOUNDED`.
    - A **bounded backdated full-window CORRECTION over an Oct-Dec 2026 window succeeds** (revision 3). So the S4-02b
      need (a backdated full-window correction over a Finding window) is not blocked.
  - **Fixture replay after a byte-level change.** Two cases were tested against a DB that already holds v1-v3:
    - appending a v4 step to the fixture;
    - flipping only the line endings.

    Both re-runs exit 3 at **v1** with `IDEMPOTENCY_KEY_REUSED`; see M1.
  - **Retroactive close.** An UPDATE that closes a current assignment at `recorded_from + 1µs`, which is earlier than
    later publications, is **accepted** by the database; see L1.

## Focus areas

1. **Migration 0010.**
   - The EXCLUDE (`0010:103-106`) is character-for-character the packet's shape.
   - The non-empty CHECKs hold on both axes (`:100-101`), and on the revision too (`:72`).
   - The set-once trigger (`:121-139`):
     - compares `to_jsonb(NEW) - 'recorded_to'` with OLD;
     - refuses changing a set `recorded_to`;
     - refuses DELETE.
   - The containment trigger (`:143-172`, BEFORE INSERT) does three things:
     - it checks `@>` against the revision's authored range;
     - it requires `recorded_from >= rev.recorded_at`;
     - it enforces series monotonicity. That rule is `>=`, which permits the same-publication siblings; the store
       separately enforces strict `>` for the new instant (`store:131-137`).
   - The revision table is append-only through `ledger_append_only()`.
   - The `numeric` CHECK `value >= 0 AND value < 'Infinity'` correctly excludes NaN as well (the negative, NaN and
     Infinity tests are parametrized).
   - **Boundary instant.** The closed row is `[r_prev, t)` and the new row is `[t, ∞)`. They are disjoint because the
     ranges are half-open, and `t > r_prev` is guaranteed, so no empty range is possible.
   - **NULL `valid_to`.** It becomes an unbounded upper end in `tstzrange`, which is correct.
   - The UPDATEs that close rows run before the INSERTs of new rows (`store:159-171`), so the non-deferrable exclusion
     is satisfied mid-transaction.
   - The downgrade is safe; see the checks above.
2. **change_kind.**
   - INITIAL, SUCCESSION and CORRECTION match packet item 2 and R1.
   - **Deviation: SUCCESSION/CORRECTION over uncovered time is refused.** This is consistent with the packet, which
     defines uncovered time as INITIAL, and it blocks nothing S4-02b needs. A CORRECTION that partly covers unpriced
     time is still allowed.
   - **Deviation: an open-ended future CORRECTION is refused.** This is the packet's literal "backdated or bounded".
   - **Unlisted deviation (L2).** A SUCCESSION exactly at the start of an open-ended assignment is refused. This
     matches the residual risk the plan re-review already recorded, and S4-02b does not need it.
3. **Idempotency and concurrency.** All five points hold:
   - The lock is taken first (`store:108-110`), keyed by tenant, Site and key, and it is transaction-scoped.
   - The replay is checked before the prior check, so a retry after success replays rather than raising 409.
   - A different digest returns 409.
   - A stale prior returns 409.
   - `clock_timestamp()` is read after the lock.

   Both race tests are real; see the probe.
4. **Actor authority.**
   - `SYSTEM_PUBLISHER` is a code constant, and the CLI has no actor or author flag.
   - The store refuses a non-SYSTEM principal.
   - The DB CHECK ties HUMAN to `author_id` and to `HUMAN_API`.
   - The route refuses in the order 401, then 422, then 403/404, then a 401 for an admitted request
     (`financial_api.py:61-87`).
   - It does not import `development_access`, and that is tested.
5. **Guard.**
   - The rule-8 writer list and per-table ownership are added symmetrically to the existing Finding rule.
   - The null-root skip (`configuration-persistence.ps1:435`) only drops a domain whose `UserRootVar` is `$null`. Only
     `financials` has one, and `ExtraUserRoots` is still iterated. `Writer = $null` was already handled at `:386`.
   - The change is narrow and does not weaken any other domain.
   - I did not re-run the implementer's non-vacuity probes, because they edit committed files. The regex review agrees
     with them: an UPDATE of any other column, or a comma-joined SET, fails `$assumptionUpdate`.
6. **Tests.** See the checks above. The implementer sharpened the history-rewrite test to move `recorded_to` earlier,
   so it targets the set-once trigger rather than the exclusion. That makes it non-vacuous.
7. **Fixture dates.** See M2 and C3.

## Findings

### Medium

**M1. The idempotency digest includes the whole fixture file's bytes, so a fixture replay breaks on any edit to the
file, including a line-ending change.**

Where:
- `publish_assumption.py:98` puts `fixture_sha256 = sha256(raw file bytes)` into `provenance`;
- `assumptions.py:136` puts `provenance` into `request_sha256`.

Failure scenarios, both observed:
- **Appending a step.** On a DB that already holds v1-v3, appending a v4 step (which S4-02b will need; see C3) makes
  `fixture --file ...` exit 3 at **v1** with `IDEMPOTENCY_KEY_REUSED`.
- **Line endings.** Flipping only LF and CRLF does the same.
  - The repo has `core.autocrlf=true` and no `.gitattributes` entry for this file.
  - The working copy is LF today, but a fresh Windows checkout writes CRLF.
  - So a walkthrough DB published from one checkout refuses a re-run from another.

The handoff's claim that "re-running the fixture replays every step" is true only for a byte-identical file.

The same class of problem exists for `SYSTEM_PUBLISHER.authorization_basis` (`assumptions.py:47-51`, digest `:138`).
Rewording that prose would make every stored publication non-replayable.

Why fix it now: once a walkthrough or demo DB holds digests, changing the digest formula makes every stored publication
conflict on replay. Today no persistent DB has been published (phase 2 does that), so the change is free.

Fix:
- Keep `fixture_sha256` and the authorization text in stored provenance, but exclude both from `request_sha256`.
- Alternatively, digest a canonical JSON of the **step** rather than the file.
- Add a test that replays v1-v3 from a copy of the fixture with a v4 appended and the line endings flipped, and expects
  `replayed=True`.

Optionally pin `*.json text eol=lf` for `backend/conversions`.

**M2. The fixture and one test carry a time bomb: the suite starts failing on 2026-12-12 and the fixture on
2027-01-01.**

Where:
- the fixture's v2 `valid_from` is `2027-01-01` (`demo-diesel-price-publications.json:26`);
- the test sets `soon = now + 20 days` (`test_s4_assumptions_postgres.py:190`).

Failure scenarios:
- **From 2026-12-12.** `soon` is at or after 2027-01-01, so it overlaps only v2's open tail, which strictly contains
  it. The SUCCESSION then **succeeds**, and `test_succession_overlapping_more_than_the_open_ended_assignment_is_409`
  fails with DID NOT RAISE.
- **From 2027-01-01.** Every fixture run on a fresh DB is refused at v2 with `SUCCESSION_NOT_FUTURE`. That breaks the
  restart test, the history-rewrite test and the walkthrough recipe.

This lands inside the expected S4-02b and owner-walkthrough period, which is 60-80 days away.

Fix (before the walkthrough DB is published, because of M1):
- move v2 well into the future, for example `2030-01-01`;
- derive the test's SUCCESSION instant from the v2 date (for example `v2 - 30 days`, asserted to be later than now)
  instead of `now + 20 days`.

### Low

**L1. The set-once trigger allows a retroactive close.** (`0010:121-139`)

`recorded_to` may be set to any instant later than `recorded_from`, including one earlier than later publications in
the series.

Failure scenario: a direct SQL writer closes a current row at `recorded_from + 1µs`, which the probe showed is
accepted. That silently changes what earlier recorded cutoffs select, and can leave an unpriced hole at a cutoff.
- Only the guarded store writes these tables, and it always closes at a fresh `clock_timestamp()` later than the
  series' latest `recorded_from`. So this is defence in depth, not a live bug.
- The `foundation_revision` precedent has the same gap.

Fix (optional; cheapest before merge, otherwise it needs a new migration): in the immutability trigger, when OLD
`recorded_to` is NULL and NEW is not, require NEW `recorded_to` > the series' `max(recorded_from)`.

**L2. Unlisted deviation: a SUCCESSION at exactly the start of the open-ended assignment is refused.**
(`assumptions.py:196`, `not only.valid_from < valid_from`)

The packet says SUCCESSION "may only truncate the single open-ended current assignment **containing** `valid_from`".
Half-open `[2027-01-01, ∞)` contains 2027-01-01. The strict `<` refuses that case, and an open-ended future CORRECTION
is also refused, so re-pricing an already-scheduled future price from its own start has no open-ended form. Only a
bounded CORRECTION with an arbitrary far end can do it.

This is pure plan code, with no schema impact and nothing S4-02b needs. The plan re-review already listed the related
residual risk.

Fix: record it as a listed deviation in the phase 2 handoff, and send it to the Architect with the next batched
questions. Do not change it now.

### Nit

- **Guard granularity.** The rule-8 regexes are per line. A single source line holding two statements, the second of
  them an arbitrary UPDATE, would pass. The DB triggers backstop this, and the same is true of the other writers.
- **Route body.** `financial_api.py:66` reads an unbounded request body before the 422 check. This is acceptable while
  the route is 401 by default, but worth a size cap when a human path exists.

## Carries for phase 2 / S4-02b

- **C1 (phase 2, first commit).** Fix M1 and M2 before running
  `publish_assumption fixture` against any walkthrough DB.
- **C2 (phase 2).** Optionally apply L1 while 0010 is unmerged, and list L2 in the handoff's deviations.
- **C3 (S4-02b).** v3 corrects June 2026, so the demo Findings (Oct/Nov 2026) stay on v1. That is fine for the phase 1
  contract, which asked for a middle-only correction and not a Finding-window one. S4-02b's "full-window backdated
  correction" fixture needs a new step, for example v4, a bounded CORRECTION over the selected Finding's whole window.
  - The probe shows the planner accepts it.
  - It replays safely only after M1 is fixed.
- **C4 (phase 2 reads).** Select at a cutoff `c` with `recorded_from <= c < recorded_to`, and select current rows with
  `recorded_to IS NULL`, both half-open. Keep the write route's default `no_verified_principal` when adding read
  routes with a Finding-like access default.

## Residual risk not named in the packet

- **Overlap rules live in plan code.** Which overlaps a change_kind permits is decided in plan code. The DB guarantees
  only that no overlap ever persists and that time is monotonic. So a planner bug would show as an exclusion error
  (fail-closed) or as a lawful-but-wrong split; the database would not catch the latter. The 30 pure plan tests cover
  the stated cases.
- **No `.gitattributes` for fixtures.** Any future byte-hashed fixture under `backend/conversions` has the same CRLF
  exposure as M1.
