# W2-04 phase handoff - run 1 (spec commit 1, partial; STOPPED for Architect questions)

Branch `task/W2-04-cold-site-evidence-money`, commit `11abf439` (on top of `d9d13255`). Not merged.

## Landed

- `backend/migrations/versions/0023_w2_cold_consequence.py`: four scoped append-only tables, unpriced CHECK
  (amount/currency NULL), `batch_publication_link_scope_unique`, `cold_consequence_dirty_key()` +
  `cold_consequence_enqueue()` (the only `INSERT INTO cold_consequence_work`, `ON CONFLICT (tenant_id, site_id,
  dirty_key_sha256) DO NOTHING`), three triggers (cold FindingRevision `WHEN domain='cold_chain'`, cold episode
  revision, `batch_publication_link`) each taking `ENQUEUE_LOCK` first, idempotent backfill of latest heads,
  refusing downgrade. No `ASSUMPTION_PUBLISHED` cause.
- `backend/tests/test_w204_cold_migration.py` (8 tests passing on private `assetops_w204_test`): money bytes,
  constraints, triggers, functions and `load_input` read unchanged across 0022<->0023; scoped FKs, CHECKs, uniques;
  work/attempt shape; append-only on all four; canonical dirty key equals Python `canonical_json` SHA; source-gate
  link enqueues only heads citing that batch; backfill latest-only + idempotent; downgrade refusal.
- Head literal `0022`->`0023` in 7 older tests. `test_w203_cold_migration_postgres.py`: `HEAD`=0023, and its 0022
  downgrade tests clear the W2-04 work rows first (`CLEAR_W204`). Run: w203 migration + s4 evidence-work, 18 passed.

## Open questions for the Architect (owner rule: implementer makes no interpretive choice)

The committed migration already contains a provisional answer for Q1-Q8, so the build could continue. Each one
must be ruled on, and changed if the ruling differs, before step 1 is complete.

1. **Work window/room per cause.** The spec says "its selected Site/window/room". Provisional: a FindingRevision
   uses `assessment_revision(NEW.assessment_revision_id).window_start/window_end` and `finding.subject_asset_id`. An
   episode revision uses its `assessment_revision_id` window and `cold_episode.asset_id`. Is that the window
   intended, or should it be `window_assessment_revision_id` or the episode bounds?
2. **Source-gate "cold heads".** Provisional: the latest revision per cold episode citing the batch through
   `cold_episode_evidence`, together with the latest cold FindingRevision per Finding citing it through
   `finding_revision_evidence`. Should episodes alone count, or both?
3. **Dirty-key canonical spelling.** Provisional: JSON array of strings, with UUIDs as lowercase hyphenated text
   and instants as `YYYY-MM-DDTHH:MM:SSZ` (second precision, matching `source_envelope.instant_text`). Confirm the
   precision.
4. **`degC_min` null-bound rule.** "Null bounds only when the technical claim is limited/withheld". Provisional
   CHECK: both bounds non-null, OR `state='WITHHELD'`, OR `limitation IS NOT NULL`. Is "limited" meant as
   `limitation IS NOT NULL`?
5. **Integrity extras the spec does not list.** Provisional, all added: a scoped self-FK on `prior_revision_id`, a
   CHECK `(revision_no=1) = (prior_revision_id IS NULL)`, a kind<->model pairing CHECK, `room_asset_id NOT NULL`
   with a scoped `asset` FK (on both revision and work), and nullable `cold_consequence_evidence.reason`
   (mirroring `cold_episode_evidence`). Keep or drop each?
6. **"Server created_at/finished_at".** Provisional: `DEFAULT clock_timestamp()` on revision `created_at`, evidence
   `created_at` (a column the spec did not list), work `enqueued_at` and attempt `finished_at`. Store code is to
   omit these columns. Should the links have `created_at`, and is a DEFAULT enough, or is a trigger that forces
   the server value required?
7. **`source_classification` domain.** Provisional: free nonempty text. Should it be constrained to the S4-05
   values (`AUTHORED_DEMONSTRATION|REGISTERED_SIMULATION|...`)? If so, give the exact set.
8. **Failed enqueue.** If the assessment window is empty or the room is missing, the trigger raises and rolls back
   the W2-03 assessment/Finding transaction, which matches 0012's pattern. Confirm that, or say to skip.
9. **Rule-8 "migration trigger ON CONFLICT ... DO NOTHING" pass probe.** `configuration-persistence.ps1` scans only
   `backend/assetops_backend/` (migrations are skipped at line ~786), so a probe appended to a migration would pass
   vacuously. The proposed fix adds a rule-8 text check on `0023_w2_cold_consequence.py`: every
   `INSERT INTO cold_consequence_work` must carry exactly that DO NOTHING arbiter, there must be at least one, and
   any `DO UPDATE` fails. The pass and fail probes would then mutate that migration file. Approve that, or name
   the intended mechanism.
10. **Fail-closed "inserts seen" for the three cold consequence tables.** Requiring at least one consequence-store
    INSERT per table would fail commit 1, because the store methods arrive in commit 2. Proposal: add the probe-name
    and owner fail-closed checks in commit 1 and the inserts-seen check in commit 2. Approve?

## Remaining steps (in spec order)

1. After the ruling, adjust 0023 and its tests as needed. Then do rule 8: add the three cold tables to
   `$consequenceTables` (line ~670) and a separate `cold_consequence_work` trigger-only refusal next to the
   `financial_consequence_work` one (line ~918). Add the per-table cold insert-only and no-DO-UPDATE checks, the Q9
   migration check, and probe-name fail-closed checks next to the W2-03 block (line ~1077). In
   `tools/writer_guard_probes.py`, add the `controls cold_consequence_* insert` controls (CONSEQUENCE) and the
   foreign/runtime-work/UPDATE/DELETE/DO UPDATE fail probes. Prove non-vacuous with
   `python tools/writer_guard_probes.py --seam <names>` on a clean tree. Commit.
2. Spec commit 2: `financials/cold_consequence.py:derive,basis_sha256`, cold methods on
   `PostgresConsequenceStore`, `financials/cold_recompute.py:ColdConsequenceWorker.run,process_one`, and
   `test_w204_cold_consequence.py` + `test_w204_cold_worker.py` (six W2-02 replays via S2 -> W2-03).
3. Spec commit 3: `analytics/cold_site_reads.py`, `cold_site_api.py` (five GETs), `main.py` wiring,
   `test_w204_cold_reads.py`.
4. Spec commit 4: frontend client, five views, `w2-cold-site.css`, `coldSiteViews.test.tsx` with
   `expectV69Panels`, and 1440/390 captures with `tools/w1-fidelity-evidence.mjs`.
5. Spec commit 5: registry nodes, guards, one full backend suite and host suite, frontend, check-all, review
   packet, task `in_review`, ACTIVE_CONTEXT/CODE_STATE.

Environment: private DB `assetops_w204_test` (created). The env script pattern is in the build brief.

## Retro-ruling corrections to fold in (coordinator, `D-2026-10-18-w2-retro-rulings`, merged from main at `d6a01683`)

Do these as their own separate commit, with the frontend work (step 4), and list both in the review packet. The
exact text is in `.agent/W2-retro-rulings.md` rows "Deviation 14" and "Deviation 17" (lines 39 and 42).
- **Dev 14 (CORRECT).** Cold Evidence Analysis links render only after an integration test proves that the exact
  `record`/`assessment` target shows the selected cold ID in the existing Evidence Analysis route, preserving
  Site, window and cutoff. Until then, show the reference as labelled text with the gap "Analysis view not
  available for this cold record". Never render a dead link. Finding and evidence destinations stay independent.
- **Dev 17 (CORRECT).** Restore the mock's exact "Loading / batch" row label (W2-03 currently says "Stock loading
  / batch"). Keep "Not established" when there is no loading record. Fix the capture/settling detector so it
  matches the real loading-state element or the exact loading sentences, not any text containing "Loading". Then
  recapture the affected cold screens.
