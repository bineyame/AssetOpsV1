# W2-03 independent review - cold assessment, episodes, Findings, four cold screens

Reviewer: fresh Claude reviewer (not the author). Revision reviewed: `ac967654` (diff `a3ac189c..ac967654`, 23 non-merge commits).
Inputs: `tasks/W2-03-cold-assessment.md` (incl. plan-review fixes M1, L1-L3), `.agent/W2-03-build-spec.md` (incl. `D-2026-10-18-w2-03-answers` and the q2 amendment), `.agent/W2-03-review-packet.md` (deviations 1-21), captures in `.agent/W2-03-evidence/`.

## Verdict: RETURN

Two Medium findings, both small to fix on the branch. The rules, migration, worker, read contract and v69 structure are otherwise sound. Deviations 16 (withheld Cooling subtab and Recommendation tab) and 18 (W1-vocabulary strings bound by the mock and JSON) are **pending with the Architect** and are not re-argued here. Deviation 1 (work window) is now confirmed by the q2 amendment.

## Findings

1. **Medium - contradiction on the failed backup chain.** `frontend/src/sites/coldAssessmentWords.ts:72` (`PROBE: ["Chamber temperature after recovery", ...]`), used by `frontend/src/sites/ColdAssessmentViews.tsx:474-478` `establishes()`. The `coldbackup` stocked capture (backup-failed replay; start failed, transfer missing, bus unpowered, compressor off) shows "Chamber temperature after recovery" under *What it establishes* in the Probe row. There was no recovery, so the page contradicts itself. The packet's self-check fixed the GENERATOR, BUS and COMPRESSOR rows but missed this one. This is on the recurring-defect list ("no contradictions").
   **Fix:** in `establishes()`, return "Chamber temperature after recovery" for PROBE only when `coolingRunning(chain)` is true. Otherwise return a neutral phrase such as "Chamber temperature after the compressor record". Add a `coldRoutes.test.tsx` assertion that the backup-failed fixture does not contain "after recovery". Recapture `coldbackup-stocked` at 1440 and 390.

2. **Medium - plan-review fix L1 / spec "Negative accepted-evidence cases must enter by authenticated gateway Batch V2" is only partly met.** The SUSPECT and equal-event-ID cases go through intake (`backend/tests/test_w203_cold_replay_postgres.py:296-328`), and missing-transfer comes from the backup-failed replay. The **clock-skew/unattested** and **unbound-role** cases exist only as pure-rule tests over hand-edited `ColdEvidence` (`backend/tests/test_w203_cold_rules.py:244-265`). So the adapter mapping that decides them on real rows, `postgres_assessment_store.py:890-900` (`in_force` binding check and `attested` attestation match), has no negative end-to-end proof. If `attested` were always true, unattested readings would support claims and no test would fail. The packet does not record this as a deviation.
   **Fix:** add an intake-driven replay test. Record the SYSTEM attestation for every Lab source except the chamber-probe source, or give that source an attestation with `valid_to` before 19:25. Then assert that the affected readings link as `EXCLUDED`/`CLOCK_UNATTESTED`, never `SUPPORT`, and that coverage and gaps drop accordingly. For unbound role: either drive an accepted record outside its binding's effective period through intake and assert `EXCLUDED`/`UNBOUND`, or, if S2 cannot accept such a record, state that in the packet as a deviation with the reason.

3. **Low - wording run-on.** `ColdAssessmentViews.tsx:626` renders "Above policy At least 45 min" in the Backup event chains *Outcome for service* cell, because `range()` returns a capitalised phrase. **Fix:** lower-case the range here or join with " · ".

4. **Low - prominence of the result chip.** `ColdAssessmentViews.tsx:628` gives every chain result a neutral `Badge`. The mock's Result chip is red for a failed start. **Fix:** use the danger tone for `OBSERVED_FAILURE`, warning for `CONTRADICTORY`, neutral otherwise.

5. **Low - test gap.** M1 late-reading asks for "first high readings at 19:15 and 19:25" at the 20:05 cutoff. `test_w203_cold_replay_postgres.py:132-136` asserts only the 19:15 anchor. **Fix:** also assert the 19:25 point is present and HIGH, and that 19:20 is absent.

6. **Low - test gap.** No test covers a LOW-direction excursion (Q9 peak = minimum, Q4 durations). I checked it by script against `assess_excursion`: a 2-4 °C band with readings 1.5/1.2/0.9/1.1/1.4 gives LOW, peak 0.9, duration {20, 30}, BOUNDED. That is correct. **Fix:** add this as `test_w203_cold_rules.py::test_low_excursion_peak_is_minimum`.

7. **Low - stale docstring.** `backend/assetops_backend/analytics/cold_reads.py:4-5` names `analytics/adapters/postgres_cold_reads.py:ColdReadService`. That file does not exist (deviation 7 moved the class into `postgres_assessment_store.py`). **Fix:** correct the path.

No finding on assertions: no existing assertion was weakened. The edits elsewhere are 0021 to 0022 head bumps, plus the W2-00 "no dispatch job" filter that excludes `cold_chain`, which the q2 amendment confirmed (interpretation 5).

## What was verified

- **Rules vs spec:** I read `analytics/cold.py` against the spec and Q4-Q11. Covered: two-sample crossing 5-10 min; return with hysteresis; earliest start only from an in-band point at most 10 min before; open lower duration ends at the last continuously observed out-of-band point (45 min); `duration_high` null when open; observed-rectangle degree minutes with no gap area; peak max/min; coverage < 0.8 gives UNKNOWN and no Finding; contradictory GOOD gives CONTRADICTORY, never failure; transfer only before the first POWER_RESTORED; timeout failure only with complete generator-state coverage.
- **Six replays through intake and the worker** (`test_all_six_w202_manifests_through_intake`): every M1 claim is asserted.
  - normal: NO_EXCURSION_OBSERVED, start 19:07, transfer 19:08.
  - excursion: 19:15, open, 45, null upper bound, peak 4.8, BOUNDED Finding.
  - backup-failed: OBSERVED_FAILURE, TRANSFER missing, door CONTEXT, exposure Finding held.
  - missing-probe: 7/13 UNKNOWN, gap 19:15-19:45, start failure observed.
  - late-reading: 12/13, then 13/13 on revision 2, old revision retained, same episode, OPENED then SUPPORT_CHANGED.
  - contradictory: CONTRADICTORY, no failure Finding.
- **Split, retry and read contract:** split (L3) is tested both with the MIXED gate and with the classify double. Atomic retry leaves zero projection rows after an injected failure and DONE on retry. Read contract (L2) covers the 31-day 422, paging and cursor, typed errors, 200 UNKNOWN, currentness precedence, and pending/historical reload.
- **Migration 0022:** upgrade preserves mini-grid rows and constraints. Scoped FKs, append-only triggers and the duplicate episode/basis refusal hold. Downgrade refuses while cold rows exist and restores the unconditional trigger first. The fuel trigger is narrowed to `WHEN (NEW.domain = 'mini_grid')`, and `test_fuel_trigger_is_mini_grid_only` passes. The replay test asserts 0 `financial_consequence_work` rows for cold revisions.
- **Mini-grid Findings and fuel money are unchanged:** the adjacent S4 Finding store/read/index/history, consequence store/recompute/evidence-work, S4-05 publication, power demo case, W2-00, W2-01 and S3 dispatch assessment suites all pass (below). The dispatch `_insert_revision` only gained the `domain` column.
- **Rule 8 (broken by me, then reverted):** I appended `INSERT INTO cold_episode` to `postgres_finding_store.py`. `check-architecture.ps1` then failed with two errors: "The Finding store only inserts into finding, ..." and "Only .../postgres_assessment_store.py writes assessment table 'cold_episode'". After `git checkout` of the file it passed again; tree clean.
- **UI against the mock:** I compared the 1440 and 390 captures for the stocked temperature, coldbackup, cold-finding and cold-finding-excursion screens. Panel set, order, titles, grid and prominence match v69: 3 panels (with the mock's metric-card row and footnote), 4, 3 and 3. The state is said once, in the strip. Each panel has at most one disclosure. Raw IDs appear only as numbered record links or inside the disclosure. Mock rows, columns and cards are present ("Not recorded" where there is no source). Limits are shown. At 390 nothing overflows horizontally; the dense tables scroll inside their own region and rows stay short. `expectV69Panels` runs for all four routes in stocked, empty and refused states, plus planted-panel rejection. Heights spot-checked from the recaptured images: temperature Claim boundary is about 225 px and coldbackup Evidence by causal step about 554 px, matching the packet's table. The table, measured before the last three commits, still holds.

## Checks run (this review, on `ac967654`, private DB `assetops_w203rev_test` on 127.0.0.1:55432, created and dropped)

| Check | Result |
|---|---|
| `pytest test_w203_cold_rules.py test_w203_cold_migration_postgres.py test_w203_cold_replay_postgres.py test_w203_cold_reads_postgres.py host/tests/test_w203_cold_vectors.py` | 30 passed, 0 failed (8m48s) |
| Adjacent: S4 Finding store/read/index/history, consequence store/recompute/evidence work, S4-05 publication, power demo case, W2-00, W2-01, S3 dispatch assessment | 136 passed, 0 failed (7m51s) |
| `npx.cmd vitest run src/sites/__tests__/coldRoutes.test.tsx` | 19 passed (vitest ran in this worktree) |
| `npx.cmd tsc --noEmit` | exit 0 |
| `tools/check-architecture.ps1` / `tools/check-agent-workflow.ps1` | both passed; architecture check fails on the planted rule-8 break, as expected |

Not rerun: the full backend (2752), host (708) and frontend (2175) suites. The implementer's runs at `264dfe9a` are cited; `ac967654` only adds the evidence and packet commit on top. Not rerun: `layout-evidence.mjs` and the fidelity capture tool; the captures were reviewed as recorded.

## Residual risk (not in the packet)

- `postgres_evidence_ledger.py:650`: cold job IDs come from `gen_random_uuid()` only so the replay fixtures' pinned `uuid4` sequence does not shift. The production code path is bent around test ID pinning. It is harmless, but the next producer that pins IDs the same way will be fragile.
- `_cold_revision` and `cold_persist` treat a basis that returns to an earlier value (A, then B, then A) as already held. No FindingRevision is appended, contrary to the commit-3 sentence "a returned old basis ... must append a new FindingRevision". A forced episode insert would also hit `cold_episode_revision_basis_unique`. Under DEFAULT selection this cannot happen, because `known_at` (inside the basis) only grows. It becomes reachable only if an explicit or older-cutoff path ever selects.
- Deviation 14 (cold IDs drilling into the existing Evidence Analysis view) is still unverified, as the packet states.
