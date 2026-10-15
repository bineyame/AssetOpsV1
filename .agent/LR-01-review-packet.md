# LR-01 review packet — late-reading series and money limit (slice)

Task `tasks/LR-01-late-reading-series-and-money-limit.md` (status `in_review`). Rulings `.agent/architect-LR-01-answers.md`,
`D-2026-10-15-lr01-source-time-cohort`. Branch `task/LR-01-late-reading-series-and-money-limit`; phase 1
`2539e5cf..445f3d18`, phase 2 `3f71deac..431a1c07` (+ closeout docs). Handoffs `.agent/LR-01-phase-1-handoff.md`,
`.agent/LR-01-phase-2-handoff.md`. USER_REVIEW_REQUIRED: yes — owner walkthrough `.agent/LR-01-owner-walkthrough.md`
is the merge checkpoint.

## Outcome delivered

Run 1 (admission-sequenced late mean, no clock proof) now ends its Finding at 07:00 with `SERIES_LIMIT`, carries the
refused span with exact lineage, and shows no current money anywhere (Finding bridge, Financials API, S5 seam);
the recorded 7.5625 USD consequence stays linked as a record. A labelled simulated attestation through the
SYSTEM-only CLI makes it `PENDING_REASSESSMENT`; one tick yields the full 06:05-08:00 episode and a new current
15.8125 USD with new IDs, the 7.5625 revision kept as history. The on-time-sequenced attested upload is eligible
at 15.8125.

## Files materially changed (phase 2)

- `backend/assetops_backend/analytics/finding_episode.py` (matcher `finding-episode-3`); `analytics/cohort.py` (F1, L1)
- `backend/assetops_backend/financials/money_eligibility.py` (new); `financials/consequence_read.py`; `financials/composition.py`
- `backend/assetops_backend/finding_api.py` (bridge states); `scheduling/upstream.py`; `scheduling/health.py` (release)
- `backend/assetops_backend/analytics/adapters/postgres_finding_store.py` (latest-only replay guard); `backend/migrations/versions/0015_finding_returning_basis.py`
- `frontend/src/sites/FindingConsequence.tsx`, `financialsClient.ts`, `findingClient.ts`, `SiteFinding.tsx`, `dispatchWords.ts`
- Tests: `test_lr01_money_eligibility_postgres.py`, `test_lr01_money_eligibility.py` (new), `test_s4_finding_episode.py`, `test_lr01_cohort_v4.py`, `test_s3_dispatch_assessment_postgres.py`, `money_gate_stub.py` (new), head/version churn in S1/S2/S4 files; `siteFinancials.test.tsx`, `siteFinding.test.tsx`
- Tools: `tools/s402c_late_power_walkthrough.py`, `tools/s402d_tick_walkthrough.py`, `tools/lr01-money-evidence.mjs` (new)

## Acceptance — outcome table

| Row | Status | Proof |
| --- | --- | --- |
| Run 1, no attestation, settled | Met | PG `test_run_one_withheld_then_attested_pending_then_eligible_then_revoked`: revision 2 SUPPORTED [06:05, 07:00) `SERIES_LIMIT`, `series_limits` CUTS_TAIL with late ID, `NO_ATTESTATION`, run ID; 7.5625 PRICED basis-CURRENT but `WITHHELD_GENERATOR_SERIES`, `presented_as_current`/`current_amount_shown` false, bridge no amount + recorded ID. Walkthrough row-1 checks (S3 INDETERMINATE, inversion, 07:00 end). Browser 22/22 |
| Attestation recorded, before settle | Met | Same PG test (+ requeued span covers 07:00-07:05, review L2): PENDING, same 7.5625 head ID; walkthrough row 2; browser 22/22 |
| Reassessed under attestation | Met | PG: revision 3 [06:05, 08:00), no series limit, 15.8125 ELIGIBLE shown, run IDs disjoint from old; revision 2 HISTORICAL with 7.5625 and its run IDs. Walkthrough row 3; browser 14/14 |
| On-time-sequenced attested upload | Met | PG `test_on_time_sequenced_attested_upload_is_eligible_at_15_8125`; walkthrough `--variant on-time`; browser 14/14 |
| No attestation / revoked etc. | Met | Run 1 is simulated without attestation; PG revoke -> PENDING -> revision 4 `SERIES_LIMIT` WITHHELD, 15.8125 kept. Expired/conflicting/clock-step/overlap S3 limits from phase 1; gate treats any generator-role limit in the bracket as material (pure tests) |
| Precedence pending > withheld > eligible | Met | `test_lr01_money_eligibility.py` (N3 missing episode-day selection, stale, live job, match pending, model, uncited window, old matcher; asset/role/bracket materiality) |

Phase-1 review: F1 fixed (`cohort._clock`, PG `test_an_attestation_not_touching_a_limited_window_leaves_it_current` for first record and last revoke, pure byte-identical test); L1 fixed (pure cross-boundary overlap test); L2 asserted in the PG outcome test. N1 (walkthrough runs the Performance comparison after each selection move; gate OPEN at every step), N2 (`assetops_lr01*` only for attest/tick/serve; work dir `%LOCALAPPDATA%/AssetOps/<db>`; drop removes only that folder), N3 (above) settled.

## Checks run

- Full backend, revision `431a1c07`: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --durations=30 --junitxml=.pytest-junit.xml`, keep-awake started, cap 20 min: **wall 519 s, 2181 passed; JUnit cases=2181 skipped=0 failed=0**. (The previous run at `2f326600` had 1 failure, `test_s4_assumption_read_api.py::...bridge_summarises...`: its fake read lacked the gate and the bridge failed closed; the fake now carries it and two gated cases were added.)
- Focused S3/S4/LR-01 Postgres set (18 files) at `53196ca6`: 194 passed.
- Frontend: `npx.cmd tsc --noEmit` clean; `npm.cmd test` 62 files / 1482 passed; `npm.cmd run build` ok. One earlier `siteFinancials` run had a flaky failure ("pins the selected version") while the backend suite loaded the machine; two reruns passed.
- `tools/check-all.ps1`: All 9 guards passed (includes dependency registry checker).
- Mutations (each reverted by `git checkout`, tree clean): gate WITHHELD branch disabled -> 1 PG failed; PENDING branch disabled -> 2 failed; consequence read ungated -> 1 failed; bridge ungated -> 1 failed; F1 old reason -> 3 failed; L1 same-attestation-only -> 1 failed.
- Walkthroughs: `s402c ... run --db assetops_lr01_auto --through eligible` 0 failed checks; `--variant on-time` 0 failed; `s402d_tick_walkthrough.py run` 0 failed (new gate ELIGIBLE check). Evidence JSON in `.agent/LR-01-browser-evidence/`.
- Browser (`tools/lr01-money-evidence.mjs`, 1440x1000 and 390x900, served via `serve`): withheld 22/22, pending 22/22, eligible 14/14, on-time 14/14; no page-level horizontal overflow on Financials and Finding (measured -15/0 px). Screenshots in `.agent/LR-01-browser-evidence/`.
- All created DBs dropped (`assetops_lr01_auto|ev|evon`, `assetops_s402d3walk_lr01`); test DBs are run-owned.

## Known deviations

1. **Migration 0015** drops `finding_revision_basis_unique` (0009). Without it a revoked attestation (selection back to run B) could not append the FindingRevision, leaving the latest Finding on the attested basis and the gate PENDING forever. Replay safety now rests on the latest-revision guard, the Site advisory lock and the matcher fence. Architect may prefer a different shape.
2. (Fix round, Architect ruling 2) The S5 seam no longer rewrites the gate: `money_eligibility` stays the raw read-derived result; `upstream_status` (typed stage/code reasons, incl. `SCHEDULE_STOPPED`) and `current_amount_permitted` are separate fields. The Finding/Financials API does not read schedule health.
3. Materiality: any generator-role limit of the Finding's asset within episode ± 6 h withholds (fail closed), even one not touching the Candidate tail.
4. Money is shown on the Financials bridge for the selected FindingRevision; the Finding page shows the SERIES_LIMIT statement and its evidence link, not a money panel.
5. `ConsequenceReadService` without a gate fails closed; four existing tests pass an explicit ELIGIBLE stub (`backend/tests/money_gate_stub.py`).

## Residual risk

- A generator refusal in a neighbouring bracket day can withhold a Finding whose episode it never touches, until that refusal is resolved (fail closed; Deviation 3).
- Gate cost: each consequence read now performs up to ~3 day-window reads plus match states.
- `dispatch-3.1`/`finding-episode-2` literals remain in comments and frontend fixtures (fixture data, not behaviour).
- Real-source clock proof remains unavailable by design.

## User-review focus

Walk `.agent/LR-01-owner-walkthrough.md`: the withheld wording and the refused span sentence, the recorded 7.57 USD
record link, the "being reassessed" state, and the 15.82 USD current cost with the 7.57 record kept.
