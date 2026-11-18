# LR-01 plan re-review after fix round 1 (fresh Claude reviewer, 2026-10-15)

Subject: `tasks/LR-01-late-reading-series-and-money-limit.md` and the registry node edit on `plan/late-reading-series` at `bf05bf0c`. Judged against `.agent/LR-01-plan-review.md` (M1-M5, L1-L5), `.agent/architect-LR-01-answers.md` (Q1-Q4, packet changes 1-3, Follow-up M1), `D-2026-10-15-lr01-source-time-cohort` (`.ai/DECISIONS.md:4137`) and `.agent/planner-LR-01-fix-brief.md`.

**Verdict: ACCEPT.** All five Medium and five Low findings are resolved, and the Architect's packet changes are in. Every new citation exists as described. I found no new fail-open path. There are three new Low findings and two Info notes, none of which blocks.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`, run in the worktree: exit 0, "Registry valid: 224 nodes, 11 linked pilot panels".
- `--next-work`: `stop_owner`, top `I-late-reading-series-and-money-limit`, gap 0.20%. This is unchanged from the first review.
- Registry diff: only the node's `task` field changed, to `"LR-01"`.
- No code changes on the branch for `backend/`, `tools/` or `frontend/src` relative to main `af6f1306`. So the citations in the worktree are main's content.
- I did not run the test suite, by instruction.

## Prior findings

| Finding | Resolved | Where in the packet |
| --- | --- | --- |
| M1 | Yes | Contract item 2 (line 17) matches Follow-up M1 almost word for word. See the M1 note below. |
| M2 | Yes | Outcome table (lines 38-44) |
| M3 | Yes | Table row 1 (line 24) and phase 1 (line 48) |
| M4 | Yes | Line 53 |
| M5 | Yes | Line 29 and phase 2 |
| L1 | Yes | Digest citation |
| L2 | Yes | Registry node |
| L3 | Yes | Phase 2 test set |
| L4 | Yes | Simulated wording |
| L5 | Yes | Window scope |
| Info (churn) | Yes | Both phases |

**M1.** The order key is `placed_at` (interval end, otherwise source time) ± the attested error, not the widened measurement interval. Intervals that only touch do not overlap. Genuine measurement overlap, or overlapping placement-uncertainty intervals, stays `REPORTS_OVERLAP` "even if gateway sequence agrees". That clause is consistent with the Architect's ruling, which has no sequence condition, and the ruling governs over my original wording. Where the intervals are disjoint, a late arrival is not `SEQUENCE_ORDER_INVERTED`. "Dense in-order five-minute means must remain usable" is required in the contract, and phase 1 proves it.

**M2.** Every row has an S3 status, a Finding revision and end reason, a consequence amount with exact IDs, and a `money_eligibility` value. This includes the run-1 transition: withheld, then attested, then pending, then eligible at 15.8125, with the old 7.5625 revision and old run/selection IDs kept. Both phase proofs use the table as their oracle, and the owner walkthrough (line 51) walks the full transition.

**M3.** The packet specifies:

- a SYSTEM-only, server-authorized CLI or route for labelled simulated attestations only;
- no real-source write path;
- refusal of gateway-credential and client authorship;
- append-only records, with supersede and revoke as new events;
- an as-of `knowledge_at` read that cites `test_s3_dispatch_assessment_postgres.py:139-143`;
- requeue on revocation and expiry.

On replay safety: `canonical()` excludes `knowledge_at` (`assessment_inputs.py:287-303`), so an as-of attestation read keeps a past cutoff's digest stable.

**M4.** The packet adds a `serve` mode, a new `assetops_lr01*` DB guard, and exact backend and frontend commands. The commands mirror `s402b_fuel_cost_walkthrough.py:257-268`, which I confirmed: `uvicorn lab_app:app` in the tree's `host/` with `tree_env`, and `$env:ASSETOPS_API_PORT=...; npm.cmd run dev -- --port N --strictPort`. The packet also states the source-gate precondition, citing `:7`, and a browser-evidence run at 1440 and 390 px with the "not run" rule. See new Low N1.

**M5.** The packet gates `presented_as_current` and `current_amount_shown` at `consequence_read.py:202-214` on the same eligibility. I confirmed the lines 202-214 match. Eligibility is exposed there. Run 1 is asserted false on both the Finding API and the Financials API.

**Lows.**

- **L1.** `assessment_inputs.py:287-307` is `canonical` plus `sha256_json`. Correct.
- **L2.** The node `task` is now `"LR-01"`.
- **L3.** The phase 2 test set now:
  - names `test_s4_finding_api.py` and `siteFinancials.test.tsx`;
  - adds the consequence store, recompute, tick and health files, all of which exist;
  - adds `tsc --noEmit` and `npm.cmd test`.
- **L4.** The case is renamed to "simulated data without attestation". The delayed path gets no automatic attestation, and the walkthrough records one explicitly.
- **L5.** The window scope is now every latest selected UTC-day window overlapping the episode plus its six-hour bracket.

## Architect packet changes

1. **Requeue.** Requeue now covers both old and new validity intervals, the accepted source and measurement intervals, and the same six-hour bracket, without expanding the bracket twice. Creation, replacement, expiry and withdrawal are named in the phase 1 proof (lines 27 and 48). Present.
2. **Eligibility precedence.** Pending, or a stale selection, wins. Once work is settled, a material refusal is withheld. `ELIGIBLE` is the gate only; the money invariant at line 32 still requires exact-head `CURRENT PRICED` plus source and currentness checks. The pending, settled-withheld and eligible cases are asserted in phase 2. Present.
3. **Epochs.** Explicit selection of an epoch stays available, and automatic cross-epoch continuity is out of scope (contract item 3). Present.

The "Architect rulings" section cites the answers file and the decision. A "Plan fix round 1" note is present.

## New citation spot-check

All of these exist on main as described:

- `assessment_inputs.py:287-307`
- `consequence_read.py:149-214` and `:202-214`: `presented_as_current` and `current_amount_shown`
- `test_s3_dispatch_assessment_postgres.py:139-143`: the replay digest assertion
- `s402b_fuel_cost_walkthrough.py:7` (gate via comparison) and `:257-268` (`serve`)
- `vite.config.ts` honours `ASSETOPS_API_PORT`
- the test files `test_s4_finding_api.py`, `test_s4_consequence_store_postgres.py`, `test_s4_consequence_recompute_postgres.py`, `test_s4_schedule_tick_postgres.py`, `test_s4_schedule_health_postgres.py`, `test_s4_consequence_read.py` and `siteFinancials.test.tsx`
- `test_s4_finding_store_postgres.py:249-273`

The adjusted ranges also check out:

- `service.py:649-655`
- `postgres_assessment_store.py:48-56` and `:559-579`
- `assessment_worker.py:173-185` (`reconcile`)
- `dispatch_v3.py:528-550`
- `finding_api.py:279-320`
- `s402d_tick_walkthrough.py:94/180/386`
- `check-all.ps1:7-12`
- checker `:354`
- `TESTING.md:103-105`
- backlog `:2176-2178` and `:2223-2231`
- `upstream.py:13,110`

## Fail-open check (d)

No path lets an ambiguous or unattested reading yield a CURRENT amount:

- Eligibility is computed on every read from persisted lineage.
- Pending work, or a stale selection, takes precedence.
- Unattested and invalid proof produce a typed limit, and once settled, `WITHHELD_GENERATOR_SERIES`.
- Simulated proof cannot validate a real source.
- The API currentness fields share the gate, with no UI-only predicate.
- Historical and pinned rows stay audit-only.

## New findings (Low, non-blocking)

- **N1 (Low, walkthrough reachability).** Line 53 makes `serve` conditional on "the source gate opened by a passing file-backed Performance comparison in the prepared host", but no step is assigned to run that comparison. Today `s402c_late_power_walkthrough.py` reads with `source_open=True` in-process (its `READ`, lines 47-60) and never runs a comparison. Without one, the served Financials would show the money read as blocked rather than the four states. **Fix:** say that the LR-01 `run` runs the normal comparison in the private tree, as s402b's `prepare` does.
- **N2 (Low, tool guard).** The packet moves `run`/`drop` to an `assetops_lr01*` prefix, but the tool's S4-02c legs are guarded by `assetops_s402c3walk` (`:375`) and its `drop` removes only work folders named `s402c3*` (`:387`). The owner command also uses a repo-relative `--work var/lr01_owner`, while the tool defaults to `%LOCALAPPDATA%/AssetOps/...`. **Fix:** state whether the S4-02c evidence mode keeps its own prefix. Make the LR-01 work directory follow the existing LOCALAPPDATA convention, or add an `lr01*` name check to `drop`.
- **N3 (Low, fail-closed default).** The eligibility read does not name the case of an overlapping bracket day that has no selected window. Pending ingestion-triggered work covers it in practice, so I found no concrete fail-open. **Fix:** state that a missing selection for any required window is treated as `PENDING_REASSESSMENT`, never `ELIGIBLE`.

## Info

- Under the Architect's ±60 s placement rule, point readings in one channel that are less than 2 minutes apart are always ambiguous, even when in order. This does not affect the five-minute-mean fixture. It is a ruled consequence, worth a line in the phase 1 review, but not a packet change.
- Time-based attestation expiry has no named trigger event. This is not fail-open: validity is evaluated at reading times, and new readings after expiry enqueue through the evidence trigger. The implementer should state how "expiry" requeue is realised.
