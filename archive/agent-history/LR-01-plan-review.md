# LR-01 plan review (fresh Claude reviewer, 2026-10-15)

Subject: `tasks/LR-01-late-reading-series-and-money-limit.md` on `plan/late-reading-series` at `02e84619` (base main `af6f1306`), with the `tasks/README.md` row and the two registry node edits. No code yet. The Architect's answers to the four packet questions were pending; I judged the plan against the Planner's recommendations.

**Verdict: RETURN.** Five Medium findings. Each needs only a short packet edit, and none changes the slice's shape (M, two phases, owner walkthrough). The code-reality anchors are accurate, apart from one Low citation slip.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 224 nodes, 11 linked pilot panels".
- `... --next-work`: not refused. It reports `I-late-reading-series-and-money-limit` as eligible at 2.02. Decision: `stop_owner`, top `I-late-reading-series-and-money-limit`, gap 0.20% (unchanged from main).
- `delivery_next_work.cjs:39-51`. The packet's `Status: implementation-ready ...` maps to `not_started`, and `USER_REVIEW_REQUIRED: true` parses as true. `parseGateQueue` finds `LR-01` from the filename `LR-01-late-...md`.
- I read every cited `path:line` on the worktree (main content). Results are below.
- I did not run the test suite, by instruction. The worktree has no node_modules.

## Code-reality spot-check

All of these exist as described:

- Gateway admission sequencing: `gateway/assetops_gateway/service.py:8-11` and `:647-655`.
- `accepted_evidence` columns, with no attestation column: `0005_evidence_ledger.py:161-207`.
- `AcceptedReading`, `EvidenceQuery` and `placed_at`: `assessment_inputs.py:70-136`.
- The `_EVIDENCE` query and its mapping: `postgres_assessment_store.py:47-56,123-136`.
- The run-1 rule `series_limits`: `cohort.py:113-136`.
- `MODEL_VERSION="dispatch-3.1"` at `dispatch_v3.py:39`, and `GENERATOR_SERIES_AMBIGUOUS` at `:544-550`.
- `reconcile` model-version staleness: `assessment_worker.py:179-188`.
- The append-only `analytic_run_selection`: `0008:28-44`.
- The late-acceptance test: `test_s3_dispatch_assessment_postgres.py:110-143`.
- `MATCHER_VERSION="finding-episode-2"` at `finding_episode.py:66`, and the write basis at `:435-479`.
- `selected_intervals`: `postgres_assessment_store.py:557-579`.
- `finding_revision`: `0009:64-105`.
- The bridge and `bridge_consequence`: `finding_api.py:284-320,347-365`.
- `consequence_read.py:149-212`.
- `Headline` and `FindingBridge`, and the versions list: `FindingConsequence.tsx:369-436,526-562`.
- `scheduling/upstream.py`, `health.py:152-203`, and `schedule-install-gate.py:26-43`, where F1 gates demo and pilot hosts.
- Walkthrough DB guards: `s402c_late_power_walkthrough.py:111-126,365-391` and `s402d_tick_walkthrough.py:396`.
- `TESTING.md:103-105,110-153`, `keep-awake-during-tests.ps1`, `check-all.ps1`, and the registry checker.

New items are marked new: the attestation record, `money_eligibility`, the `SERIES_LIMIT` claim field, the new MODEL and MATCHER versions, and the walkthrough modes. The next migration would be `0014` (the head is `0013_schedule_state.py`).

## Coverage

| Item | Covered | Note |
| --- | --- | --- |
| Decision / Architect Q1 (source-time order when attested; limited otherwise) | Partly | The positive attested-admission case is not asserted (M2) |
| Q2 (Finding limit + end reason; S5 withholds) | Yes | `SERIES_LIMIT` end reason, `GENERATOR_SERIES_AMBIGUOUS` carried, 7.5625/15.8125 history kept |
| Q3 placement, R1 | Yes | Node requirements unchanged; install gate stays closed until resolved |
| L-a contract first | Yes | The contract has a soundness gap (M1) |
| L-b new version, history kept | Yes | — |
| L-c series limit/end reason | Yes | — |
| L-d / L1 signal named in both nodes | Yes | `money_eligibility` with three states appears in both acceptance targets |
| L-e regression run 1 + on-time variant | Partly | M2 |
| L-f real gateway without clock limited | Yes | L4 |
| S4-02b money-panel residual | Mostly | The API currentness fields are still unhandled (M5) |
| S4-02d S5 seam carries | Yes | Pending and stale work feed eligibility; S5-01 keeps its own integration |

## Findings

### M1 (Medium, contract soundness): the uncertainty and overlap rule, as written, refuses ordinary in-order series, including the slice's own positive case

Packet "Reviewed contract" item 2 (packet line 40) and Architect question 2.

Item 2 treats each reading as `[source_time−error, source_time+error]` "(or the reported measurement interval widened by error)", and says equal or overlapping intervals "remain REPORTS_OVERLAP/ambiguous". The S4 power series is back-to-back 5-minute `INTERVAL_MEAN`s (`s4-power-late-demo-cases-v1.json:10`). Widen each by 60 s and every neighbouring pair overlaps: [06:59,07:06] against [07:04,07:11]. The same happens to point readings taken 2 minutes apart or less. So the rule can make attested on-time data, and the 15.8125 positive variant, ambiguous. Today's rule (`cohort.py:113-136`) flags overlap only for identical `placed_at`, and flags order only where sequence and placement disagree.

- **Why it matters.** This is the reviewed contract that phase 1 implements. Read literally, it regresses ordinary data. Read loosely, the implementer chooses the ordering key. Either way, the Architect is being asked to bless an unsound sentence.
- **Fix.** State the ordering key: `placed_at` (interval end, else source time) ± error, not the widened measurement interval. Say that abutting interval means are not overlap. Say that uncertainty-interval overlap creates ambiguity only where gateway sequence and source order disagree; where they agree, today's result stands. Add a pure test with dense, in-order attested data that stays usable.

### M2 (Medium, acceptance gap): the attested admission-sequenced case, which is the core of Architect Q1, is neither asserted nor walked

Packet phase 1 tests (packet line 61), phase 2 walkthrough (line 62), and the owner walkthrough (line 64).

Q1's positive rule is that an attested same-epoch stream is placed by source time, so "a later gateway sequence with an earlier source time is a late arrival, not `SEQUENCE_ORDER_INVERTED`". The owner walkthrough shows only two cases:

- run 1 limited and withheld (unattested);
- the on-time-sequenced upload with an attestation, at 15.8125.

The on-time variant does not exercise the new rule at all, because it passes today's sequence check. Phase 1 lists "admission-sequenced run 1" with no expected outcome. Nothing asserts the append-only transition the decision describes: run 1 withheld, then an attestation recorded, then requeue and reassess, then a new selection and FindingRevision, then `ELIGIBLE` at 15.8125, with the 7.5625 revision and the dispatch-3.1 selection kept.

- **Why it matters.** A build could ship the fail-closed half and never prove the reordering the node exists to add. The registry acceptance target requires "verify exact assessment, Finding and consequence lineage" for both variants.
- **Fix.** Add an explicit outcome matrix to phase 1 and phase 2:

  | Case | Expected result |
  | --- | --- |
  | Run 1, unattested | INDETERMINATE, `SERIES_LIMIT`, `WITHHELD_GENERATOR_SERIES` |
  | Run 1, attested | Source-ordered, full episode, 15.8125, `ELIGIBLE` |
  | Run 1, attestation added later | Withheld, then pending reassessment, then eligible; old IDs unchanged |
  | On-time variant | 15.8125 |
  | Clock-negative cases | As listed in the packet |

  Add the attested run-1 transition to the owner walkthrough.

### M3 (Medium, fail-closed boundary underspecified): the attestation write route, authority and as-of read are left open

Packet table row 1 (line 47) and contract item 1 (line 39).

The attestation is the one record that turns a withheld amount into current money. Yet the packet leaves its route as "new migration/adapter/API or importer", without:

- who may author it;
- how it is scoped to a tenant and Site;
- whether it is append-only, or can be superseded or revoked;
- whether it is read as of `knowledge_at`.

The existing replay test (`test_s3_dispatch_assessment_postgres.py:139-143`) re-derives a past cutoff's `input_sha256`. An attestation read without a `recorded_at <= knowledge_at` filter would change past bases or break that replay. A revoked or superseded attestation must withhold money again; the packet requeues on "attestation changes", but does not say revocation is a change.

- **Fix.**
  - Name one route: for example, a SYSTEM-only, server-authorized fixture or CLI importer for labelled simulated attestations, with no real-source write path in this slice.
  - Refuse gateway-credential and client authorship, consistent with the A-S5-overview P7 Q3 rule.
  - Make the record append-only, with supersession and revocation.
  - Read it as of `knowledge_at`.
  - Requeue on revocation as well, with tests for each.

### M4 (Medium, walkthrough not reachable with the named tools): no UI serving path for the owner checkpoint

Packet phase 2 (line 62) and the owner walkthrough (line 64).

The owner is to view Financials at desktop and narrow width on a private DB. The two named tools are backend-only:

- `s402c_late_power_walkthrough.py` reads consequences in-process (`:56,72-91`) and has only `run`/`drop` (`:367`).
- `s402d_tick_walkthrough.py` likewise.

The only `serve` (API plus printed `npm.cmd run dev` commands) is in `s402b_fuel_cost_walkthrough.py:257-268`, and `checked_db` limits it to `assetops_s402b*` databases (docstring `:21-23`). Money also reads current through the API only once the source gate is open; s402b opens it with a Performance comparison (`:7`).

The packet also names no browser-evidence run (as `tools/s402b-fuel-cost-evidence.mjs` was for S4-02b, 90/90 at 1440/390) for a changed owner-visible panel.

- **Fix.**
  - Add a `serve` subcommand (new) to the extended walkthrough, or name another serving route, together with the frontend command and the source-gate precondition.
  - Name a browser-evidence run at 1440 and 390 for the four states (new script, or an extension of the s402b one). Record a skipped run as `not run` with its precondition.

### M5 (Medium, fail-closed gap on the S4 Financials API): consequence read fields still assert a current amount for run 1

`backend/assetops_backend/financials/consequence_read.py:202-214`, served by `GET .../financial-consequences` at `finding_api.py:246-277`.

The packet routes eligibility through the bridge and the panel. But the consequence read still sets these from basis currentness alone:

- `selected.presented_as_current = is_head and state == "CURRENT"`
- `currentness.current_amount_shown`

So for run 1 the S4 Financials API says a current amount is shown while the bridge withholds it. The walkthrough's money predicate (`s402c_late_power_walkthrough.py:91`) uses the same basis test. The packet's own invariant says "Do not rely on a UI-only predicate", and these fields are API-level claims that S5-01 or tools may read.

- **Fix.** Either gate `presented_as_current` and `current_amount_shown` on `money_eligibility` and include eligibility in that response, or rename or document them as basis-currentness only. Then assert run 1 shows false or withheld on both endpoints.

### Low (carries)

- **L1.** The digest citation `assessment_inputs.py:205,334` is off. Line 205 is `watermarks` and line 334 is inside `build_input_set`. The input payload and digest are at about `:280-301` and `sha256_json` at `:305-307`.
- **L2.** The registry node `task` is `"LR-01-late-reading-series-and-money-limit"`. Other non-S nodes use the short id (`G-05`, `PRE-S3-04`), and the gate lookup at `delivery_next_work.cjs:247` matches `q.task === node.task`, where the gate id is `LR-01`. This is harmless today, because the global active and in-review stop uses the gate queue. Use `"LR-01"` for consistency.
- **L3.** Name the existing test files to extend: `backend/tests/test_s4_finding_api.py` and `frontend/src/sites/__tests__/siteFinancials.test.tsx`. Add `npx.cmd tsc --noEmit` and the frontend test run to phase 2. `test_s4_consequence_read.py:18-31` covers only display rounding. Phase 2's focused set should also include the S4 consequence, recompute, tick and health files (`TESTING.md:101`), because eligibility reads their state.
- **L4.** The "real-source-without-clock" walkthrough case will be SIMULATED evidence without an attestation. Call it that, unless a LIVE-mode fixture is built. Also state whether the Lab-delayed simulated gateway path (`service.py`, the default late path for S2-S7) gets a simulated attestation in this slice or stays limited. That decides whether ordinary simulated late data ever shows money in S5 demos.
- **L5.** "Latest selected window" should mean every selected UTC-day window intersecting the episode plus its bracket, for episodes that cross midnight.

### Info

- The new MODEL_VERSION and MATCHER_VERSION make `reconcile` reassess every assessed window, and re-evaluate every Finding, on every Site. Expect revision churn in existing walkthrough and test assertions, and extra tick cost on the first post-deploy run. The packet should say so, so that reviewers do not read the churn as regressions.
- The coordinator committed `.agent/planner-late-reading-log.txt` (3792 lines) on the branch. Confirm that this is intended.

## Phasing, tests, owner review

- **Phasing.** M in two phases. Phase 1 has its own independent review, and phase 2's review is the slice review. This is correct.
- **Full suite.** One `-n 2` run at slice end with keep-awake, the 20-minute cap and the JUnit zero-skip proof. This is correct against `backend/TESTING.md`.
- **USER_REVIEW_REQUIRED.** `true` is correct: the Financials panel copy and states change. The walkthrough needs M4 to be reachable.
- **Install gate.** It stays closed until the node resolves. This matches the S4-02d carry.
