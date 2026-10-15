# LR-01 slice review: late-reading series and money limit

Reviewer: a fresh Claude reviewer who did not author the work. Worktree `AssetOpsV1-review`, branch `review/LR-01-slice` at `3b360af5`. The diff reviewed is `ad2a96d0..3b360af5`.

Authority:
- packet `tasks/LR-01-late-reading-series-and-money-limit.md` (the outcome table and the phase 2 row)
- `.agent/architect-LR-01-answers.md` and `D-2026-10-15-lr01-source-time-cohort`
- phase-1 review `.agent/LR-01-phase-1-review.md` (F1, L1, L2)
- plan re-review N1-N3
- review packet, both handoffs, owner walkthrough, and browser evidence

## Verdict

**Accept.** There are no High or Medium findings. The three Lows below can be carried or fixed on the branch at the Implementer's discretion. None of them is an acceptance gap.

Every outcome-table row is implemented and proven with exact persisted IDs. The money gate fails closed on every consumer I traced. F1, L1 and L2 are fixed for real. Migration 0015 is safe under the existing locking. The owner walkthrough reproduces from the tool.

## Outcome table (verified)

| Row | Verified by |
| --- | --- |
| Run 1, no attestation, settled | PG `test_run_one_withheld_then_attested_pending_then_eligible_then_revoked` (rev 2 [06:05, 07:00) `SERIES_LIMIT`, CUTS_TAIL limit citing the late ID and `NO_ATTESTATION`, 7.5625 CURRENT PRICED but WITHHELD, bridge has no amount and the recorded ID). Reproduced by me with the owner tool: `run --db assetops_lr01rev` gave 0 failed checks, S3 INDETERMINATE, inversion citing the late ID, and bridge `WITHHELD_GENERATOR_SERIES` with 7.5625 recorded. |
| Attested, before settle | Same PG test: PENDING with the same head ID and 7.5625. The requeued span covers 07:00-07:05 (L2). The tool `attest` prints PENDING. |
| Reassessed under attestation | PG rev 3 [06:05, 08:00), no series limit, 15.8125 shown, run IDs disjoint, rev 2 HISTORICAL with its old runs. I reproduced it: after `tick`, the live API returned rev 3, `PRICED 0.00-15.82 CURRENT`, gate `ELIGIBLE`, new consequence `a086237f…`. Rev 2 via `revision_id` returned `HISTORICAL`, no amount, consequence `301fd658…` (the 7.5625 record). |
| On-time attested | PG `test_on_time_sequenced_attested_upload_is_eligible_at_15_8125`, plus the packet's `--variant on-time` evidence JSON. I did not rerun the tool variant. |
| No attestation / revoked / expired / conflicting / step / overlap | Revoke goes PENDING, then rev 4 `SERIES_LIMIT` WITHHELD with 15.8125 kept (PG). The other S3 limits are phase-1 pure tests, already reviewed. Gate materiality and precedence are in `test_lr01_money_eligibility.py`. |

## Fail-closed money (traced)

- **`consequence_read`.** `presented_as_current` and `current_amount_shown` now also need `ELIGIBLE`. If no gate is wired, or the gate read raises, the state is `PENDING_REASSESSMENT` (`unavailable`).
- **Composition.** `composition.build_consequence_read_service` is the only builder, and it wires the real gate. `main.py` and `scheduling/composition.py` both use it. A grep found no other constructor outside tests.
- **Bridge (`finding_api.bridge_consequence`).** A CURRENT row with any gate state other than `ELIGIBLE`, including a missing gate (`None`), returns no amount and no quantity. A non-CURRENT row already had no amount, and a HISTORICAL revision has none either.
- **S5 seam (`scheduling/upstream`).** If the gate is missing, the seam reads it as PENDING. While S3, S4 or schedule blockers stand, the seam downgrades `ELIGIBLE` to PENDING (deviation 2). This makes the seam stricter than the API, never looser, which is acceptable.
- **Frontend.** The panel shows an amount only for `PRICED` + `CURRENT` + a non-null amount, and gated states never produce `PRICED`. History marks a row "current" only with `current_amount_shown`.

## Phase-1 carries

- **F1 is fixed.** `_clock` now returns `NO_ATTESTATION` unless an attestation touches the reading. A pair limit only forms inside a window that holds both readings, so the touched reading's requeue bracket covers it.
- **L1 is fixed.** The overlap checks now run over all attested readings in the channel, using each reading's own error. The early `break` at `2*MAX_UTC_ERROR` is sound because each error is at most `MAX_UTC_ERROR`.
- **L2 is fixed.** It is asserted in the PG outcome test.
- **N1-N3 are settled.** The walkthrough reruns the Performance comparison after every move; the gate was OPEN at every step in my run. The `assetops_lr01*` guard and the LOCALAPPDATA work directory are in place, and `drop` removed only its own folder. A missing episode-day selection is PENDING (pure test).

## Migration 0015 (Known Deviation 1): safe

The latest-revision-only replay guard holds for three reasons:

1. `apply` takes the Site advisory lock, `pg_advisory_xact_lock('finding:'||site)`, and re-reads the fence inside the same transaction before any insert. Two matcher passes for the same Site are therefore serialised, and a pass planned on an old view raises `FindingFenceMoved`.
2. `finding_revision_no_unique (finding_id, revision_no)` from 0009 is kept. Even a hypothetical unlocked concurrent append would collide on `revision_no` rather than duplicate.
3. Writes within one pass see their own earlier inserts, so a duplicate write in a single batch is still suppressed.

The only behaviour the dropped constraint used to block is A -> B -> A. That is the needed case, and the revoke step of the PG outcome test proves it: rev 4 would raise IntegrityError under the old constraint.

The downgrade refuses while a returning basis exists rather than deleting history. That is honest, but it is untested (L2 below). From a safety standpoint I see no reason to rule against it. The Architect's parallel ruling governs the shape.

## Known Deviations 2-5

- **2 (seam stricter than the API):** acceptable. It fails closed.
- **3 (any generator-role limit of the asset within ±6 h withholds):** fail closed and documented. Residual risk: a refusal that touches neither the episode nor its tail still withholds money until the evidence is resolved. That is an owner and Architect product choice, not a defect. See L1 for its copy consequence.
- **4 (the Finding money panel is the Financials bridge):** accurate. The Finding page has no money panel and gains the `SERIES_LIMIT` statement.
- **5 (gate-less service fails closed, tests use an explicit ELIGIBLE stub):** this is the right default. The stub is confined to `backend/tests/money_gate_stub.py`.

## Findings

### L1: Low, copy honesty. The withheld sentence asserts "the finding ends before them" for every limit

- **Where:** `frontend/src/sites/FindingConsequence.tsx:436-442` (`MoneyLimit`).
- **What is wrong:** every entry in `money_eligibility.series_limits` is rendered as "Generator records from X to Y … The finding ends before them and that time is not judged." The list mixes Finding-revision limits (relation `CUTS_TAIL`, `CUTS_HEAD`, `INSIDE_EPISODE`, `INSIDE_FORMER_EPISODE`) with the gate's `SELECTED_WINDOW` limits. Under Deviation 3, those can sit up to 6 h away from the episode. For any limit that is not `CUTS_TAIL`, the sentence is false. Two smaller issues:
  - If a withholding has no spans (for example, an `end_reason` only), the panel renders an empty `<ul>`.
  - In the authored case, the span shown is 07:05-08:00 "arrived out of order", while the reading that actually arrived late is the 07:00-07:05 mean. This is a precision point for the owner walkthrough.
- **Why it matters:** the authored fixture only exercises `CUTS_TAIL`, so the walkthrough looks right. Other refusals would show an untrue sentence on a money surface.
- **Fix:** word each sentence by `relation` and `source`: tail, head, inside, or "near this finding". Omit the list when it is empty. Add one test for a non-tail limit.

### L2: Low, test gap. The 0015 downgrade refusal is not exercised

- **Where:** `backend/migrations/versions/0015_finding_returning_basis.py:33-45`.
- **What is wrong:** the head and downgrade tests assert the head name and roll back whole downgrades. No test creates a returning basis and asserts that the 0015 downgrade raises, or that it succeeds and restores the constraint without one.
- **Fix:** add one PG test for each path.

### L3: Low, residual from Deviation 3 not named in the packet

- **Where:** `backend/assetops_backend/financials/money_eligibility.py:126-133`.
- **What is wrong:** a generator-role refusal in a neighbouring bracket day withholds a Finding whose own revision carries no series limit and whose episode it never touches. There is no path to `ELIGIBLE` except resolving that unrelated refusal.
- **Why it matters:** it fails closed, so it is not a defect. It should be named as residual risk for S5-01 and the owner: money can stay withheld because of a refusal hours away from the episode.
- **Fix:** none required for this slice. Record it in the residual risk.

## Checks run (all in the worktree; `assetops_backend.__file__` confirmed under `AssetOpsV1-review`)

- **Focused Postgres and pure set, 13 files.** Command: `pytest test_lr01_money_eligibility_postgres.py test_lr01_money_eligibility.py test_lr01_cohort_v4.py test_s4_finding_episode.py test_s4_finding_api.py test_s4_consequence_read.py test_s4_consequence_recompute_postgres.py test_s4_consequence_store_postgres.py test_s4_schedule_tick_postgres.py test_s4_schedule_health_postgres.py test_s4_finding_store_postgres.py test_s4_assumption_read_api.py test_s3_dispatch_assessment_postgres.py -n 2 --dist loadfile`, private base `assetops_lr01rev_test`. Result: **183 passed**, 305 s.
- **Full suite: not rerun.** `git diff 431a1c07..3b360af5 --stat` touches only `.agent/`, `.ai/` and the task file, with no backend code. I cite the implementer's run at `431a1c07`: 2181 passed, JUnit cases=2181, skipped=0, failed=0, 519 s.
- **`tools/check-architecture.ps1`:** passed.
- **`tools/check-agent-workflow.ps1`:** passed.
- **`npx.cmd tsc --noEmit`:** clean (exit 0).
- **`npm.cmd test` on `siteFinancials.test.tsx` and `siteFinding.test.tsx`:** vitest ran (the sandbox esbuild error did not occur), but **32 failed, 35 passed**. Every failure is `Invalid Chai property: toHaveTextContent` or `toBeInTheDocument`. An untouched file (`sitesIndexRoute.test.tsx`) fails the same way. The `@testing-library/jest-dom/vitest` matchers are not registered through the worktree's `node_modules` junction, so this is environmental. **The frontend suite and the production build are unverified by me.** The implementer reports 1482 passed and a successful build.
- **Owner walkthrough (reproduced):**
  - Steps 1-3 ran on `assetops_lr01rev` with the tool: `run` gave 0 failed checks, then `attest` gave PENDING, then `tick`.
  - `serve` (API 8931) printed the Financials, Finding and withheld-revision links. The live API matched rows 1 and 3, as recorded above.
  - The on-time variant (step 4) and the browser and frontend dev server were not run.
  - Two local preconditions are needed in a fresh worktree, a gitignored `var/sites/kobo-001.yaml` and a repo `.venv`. The owner's main checkout has both.
- **Browser evidence:** the claim JSONs are all ok, with page overflow -15 at 1440 and 0 at 390 on both Financials and Finding. I viewed the 390 withheld Financials screenshot and saw no overflow. I could not rerun the evidence script (it needs Chrome and the dev server).
- **Cleanup:** I dropped `assetops_lr01rev` and its LOCALAPPDATA folder and `assetops_lr01rev_test`. No `assetops_lr01*` databases remain. The temporary `.venv` junction and the `var/` copy were removed.
- **Mutations:** I ran none. The packet's six recorded mutations, together with the A->B->A revoke step that only passes with 0015, give the gate, bridge, read and migration enough teeth for this review.

## Residual risk

- L3 (Deviation 3 materiality).
- Gate cost: about 3 day-window reads plus match state per consequence read, as named in the packet.
- The frontend test count is not independently verified (environmental, see above).
- Real-source clock proof is still unavailable, by design.
