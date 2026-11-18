# S6-01a slice review (phase 2) - independent

Reviewer: fresh Claude reviewer (did not author the slice). Worktree `AssetOpsV1-review`, branch `review/S6-01a-slice`
at `9ea575f5`; diff `fd7afd2c..9ea575f5` (code-final `375c8cf9`). Judged against `tasks/S6-01a-action-store-read.md`,
`.agent/architect-S6-01-answers.md` Q1-Q5 + M1-M3 / `D-2026-10-15-s601-action-store-and-ui`, and the phase-1 review.

## Verdict

**Accept.** No High, no Medium. Four Lows below, none blocking; fix on the branch or carry to S6-01b at the
coordinator's choice. The **full-suite proof is incomplete** (see Checks): my one full run was stopped at the 20-minute
cap at 59 % with no failure, because the machine was at 100 % CPU from other work. The implementer's full run on
`375c8cf9` (2207 passed, 1 environmental failure, no JUnit) is still the only full evidence. A JUnit full run on a quiet
machine is needed before merge.

## Checks run (by me, on `9ea575f5`)

- `assetops_backend.__file__` resolved to `AssetOpsV1-review\backend\assetops_backend\__init__.py`. Private base DB
  `assetops_s601arev_test`. The gitignored `var/sites/*.yaml` were copied in temporarily and removed afterwards.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- Rule-8 mutation: an `INSERT INTO action_event` in `sites/adapters/postgres_foundation_store.py` fails the guard with
  "Only ...postgres_action_store.py writes Action table 'action_event'". Reverted; tree clean. The phase-1 reviewer's
  rule-8 mutations and the implementer's six apply mutations are cited, not repeated.
- Focused and adjacent tests, `-n 2 --dist loadfile`, JUnit: **173 tests, 0 skipped, 0 failed**, 19 min 34 s under
  full machine load. Files run:
  - `test_s6_action_rule`, `test_s6_action_store_postgres`, `test_s6_action_apply_postgres` and
    `test_s6_action_records_postgres` (this one includes the committed-contract equality);
  - `test_s1_bindings_postgres`, `test_s1_foundation_postgres` and `test_s4_finding_read_postgres`;
  - `test_s2_evidence_ledger_postgres` and `test_s4_evidence_consequence_work_postgres` (head pins and downgrade);
  - `test_runs_api` (the implementer's one failure, which passes with `var/sites` present).
- **Full suite: not completed.** No other `pytest` was running when I started. The command was
  `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder --junitxml=<abs>`. I stopped it at the
  26-minute mark, which was over the cap; it had reached 59 % with every test passing. Postgres activity showed it
  progressing, not hung, and the host was at 100 % CPU. No JUnit file exists for the run.
- Not run: `tools/check-all.ps1` (the implementer reported 9/9; architecture and workflow were run directly), frontend
  checks (no frontend change), layout evidence (not applicable: non-UI).
- Main is still `fd7afd2c` and is an ancestor of the branch. LR-01 has not merged, so no re-chain is due yet.

## What I verified holds

- **Apply transaction** (`postgres_action_store.py` `apply`, about lines 291-347):
  - **Order inside one transaction:**
    1. `SELECT ... FROM action ... FOR UPDATE` comes first.
    2. A stored event under the key is a REPLAY; an existing APPLIED returns `ALREADY_APPLIED`; an unknown expected
       Foundation returns 404.
    3. `attempt` runs the S1 publish on the same connection. `_run(connection=)` neither begins nor commits.
    4. The Site `FOR UPDATE` follows.
    5. `then` inserts the artifact, the binding rows and APPLIED.
    6. The adapter's `engine.begin()` makes the only commit.
  - **APPLIED only after commit:** APPLIED is returned only after that commit.
  - **FAILED:** an `ApplyFailed` rolls everything back, and `_append_failed` writes FAILED in a new transaction. It
    re-locks the Action and returns any event already stored under the key. A key collision on
    `action_event_idempotency_unique` re-reads and returns the existing event.
  - **APPLIED is never reverted:** the reducer has no transition out of APPLIED, and no table is ever updated.
  - **Tests:** lock order (`NOWAIT` on the Action fails while the apply waits on the Site), rollback after every
    insert, and identical and distinct races publishing once.
- **Under the Site lock** (`foundation_service.py` `_publish_content_change`): expected covering revision, then
  no-change, then expected reserve value. All three raise `FoundationRefused` with `current_revision_id`. They map to
  `ACTION_FOUNDATION_STALE` 409, `ACTION_NO_CHANGE` 422 and `ACTION_VALUE_INVALID` /
  `ACTION_EFFECTIVE_TIME_INVALID` 422. The S1 entrypoint without `caller` is unchanged (its own transaction and
  clock).
- **No backdating:** `effective < recorded or effective <= accepted_at` is a 422 plus FAILED. The DB backs it with
  `action_policy_change_effective CHECK (effective_from >= recorded_at)` and `occurred_at = recorded_at` for
  non-OBSERVED events.
- **Refusals that write nothing:** 401, 403, capability 403, wrong-Site and unknown Action 404, unknown expected
  Foundation 404, and malformed 422 all come before the transaction or return before any insert (`table_counts`
  asserted). `ACTION_ALREADY_APPLIED` writes no FAILED. An identical applied retry returns the artifact before
  no-change.
- **M1 grant scoping** (`capability.py`): a grant needs a valid tenant ID, Site ID and `records`. An accept targets the
  path Finding; apply and OBSERVE target the Action's origin Finding. A non-fixture Finding and its Action get 403
  with nothing written (tested). A client body naming actor, capability and so on is a 422.
- **Contract and records fixture:**
  - `s6_action_records.build` runs F01, F02 and an authored SOC-at-headroom block through ingestion, assess and
    match, then every command through the real API.
  - It is keyed to the five manifest IDs, with fixed clocks.
  - The committed JSON matches a fresh run after normalisation: it passed in my run.
  - Referential links are asserted separately against the written rows.
  - The basis evidence values are uniform, so normalised ordering is stable.
  - It is usable by S6-01b as the committed file.
- **Money consequence:** a labelled "Consequence" link to the exact FindingRevision's
  `/financial-consequences?revision_id=` (the route exists, `finding_api.py:246`). No amount; it says the trial
  predicts no saving. This is an acceptable reading of "shown only for its exact basis, labelled consequence" for a
  non-UI slice, and it is disclosed.
- **Rule 8:** the ninth writer is registered in all three tables. It is INSERT-only into the six Action tables, with
  every-line bans on UPDATE, DELETE, TRUNCATE, upsert, MERGE and DDL. Reverse ownership applies to every other module
  (mutation above). The existing eight restrictions are unchanged.
- **Migration re-chain obligation:** stated in the packet's residual risk with the four head-pin locations.

## Findings (all Low, non-blocking)

### L1 - apply's server instant is taken before the Action and Site locks

`backend/assetops_backend/actions/service.py:274` (`recorded = self.clock()`) is passed into `store.apply` and used
as both the event `recorded_at` and the S1 publish's `now` (`CallerTransaction.recorded_at`). The lock wait can take
up to the 5 s `lock_timeout` on each lock. If another Action of the same Site, or an ordinary S1 publish, commits a
Foundation change in that window, `planner` raises `FOUNDATION_CLOCK_BEHIND`, which runs before `expect`. The
result is a FAILED with the generic `ACTION_PUBLISH_REFUSED` (409, `current_foundation_revision_id` null), not the
typed `ACTION_FOUNDATION_STALE`. Tests use a fixed clock, so this path is unexercised. The same pre-lock instant also
means a `recorded_at` cutoff read can later gain an event recorded at or before an instant it already showed.

- **Why it matters:** the typed stale code is the contract for a stale basis.
- **Fix:** take the instant inside the transaction after the Action lock (or after the Site lock, for the publish),
  or map `FOUNDATION_CLOCK_BEHIND` to `ACTION_FOUNDATION_STALE` with the covering ID.

### L2 - `application_basis` label over-promises for future-period applies

`service.py:379`: "Current Site Foundation at read time; an apply command names it as expected_foundation_revision_id".
The server checks the revision covering `effective_from`, not the one covering now (packet deviation 3). The
fixture's no-change case shows the two differ once a future-dated revision exists. In that case a client following
the label gets a stale 409 and a permanent FAILED.

- **Fix:** do one of the following, and record it in the contract `notes` for S6-01b:
  - expose the covering revision for a stated `effective_from`;
  - soften the label.

### L3 - `D-action-records` ineligible record is SOC-at-headroom, not "missing/conflicting"

`backend/tests/s6_action_records.py:88` authors SOC exactly 30 against a 20 reserve (`SOC_NOT_ABOVE_HEADROOM`). The
packet asks for "an ineligible missing/conflicting case". Missing and conflicting SOC are covered at rule level
(`test_s6_action_rule.py`), but no persisted record or contract response carries those codes. That is acceptable for
S6-01b (one unavailable state). Add a persisted missing or conflicting record if S6-01b needs to show that copy.

### L4 - unmapped S1 refusals are forced to 409

`service.py:37` `FAILURE_STATUS` gives every `ACTION_PUBLISH_REFUSED` a 409, whatever the S1 status (for example
`SITE_NOT_FOUND` 404 inside the publish). Non-`FoundationRefused` S1 errors (`FoundationOverlap`, `BindingOverlap`)
roll back and surface as 500 with no FAILED. That is disclosed as deviation 6 and is safe, but it is untyped.

- **Fix:** carry `ApplyFailed.status` into the stored response path, or narrow the mapping. Low.

## Residual risk not named in the packet

- **Full-suite evidence on `9ea575f5` is still missing as JUnit.** The implementer's summary line and my 59 % partial
  run are not the zero-skip proof `backend/TESTING.md` requires. Run it once on a quiet machine before merge.
- **The grants document is read once at app composition** (`composition.py` `capability_from_environment`).
  Changing `ASSETOPS_ACTION_DEMO_GRANTS` needs a restart. This is operational, not a defect.
- **`action_no_unique` is global and the sequence is global,** while the packet says "tenant-scoped sequence".
  `UNIQUE(tenant_id, action_code)` holds, so this only matters for multi-tenant numbering density. The phase-1
  review accepted it.
