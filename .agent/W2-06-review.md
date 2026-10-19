# W2-06 review (independent first review, Claude)

Branch `task/W2-06-ev-assessment`, head `5f90c3a6`, against `main...HEAD`. Reviewed against `tasks/W2-06-ev-assessment.md`,
`.agent/W2-06-build-spec.md` (rulings through r6) and `.agent/W2-06-review-packet.md`. P1-P8 in
`.agent/W2-06-pending-rulings.md` (run 8) are with the Architect and are not repeated here.

## Verdict: ACCEPT WITH FIXES

The six-case correlation, the 0025 schema/downgrade, the single-transaction writer and Finding, the selected-read
envelope and refusals, and both screens match the rulings closely. One High needs a fix or ruling before merge: the
worker re-assesses a widened window instead of the selected window a job dirtied, which leaves that window reading
CURRENT on a stale head. The other findings are Medium (implementer choices not fixed by spec) or Low.

## Findings

### H1 (High) - a dirtied selected window can be settled under a different window and then read CURRENT on its stale head

`backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:1127-1145` (`ev_windows`) with
`backend/migrations/versions/0025_w2_ev_session.py:276` (the `ev_enqueue_window` bridge merge) and the read's pending test
at `postgres_assessment_store.py:2055`.

- **What is wrong.** When a job intersects exactly one selected window, `ev_windows` returns
  `Window(min(start, a), max(end, b))`, which is the selected window widened by the job's brackets. `ev_persist` then
  writes the assessment and the DEFAULT selection under that new window's key (`assessment_key`, `select()` at :1286).
  The selected window the trigger dirtied gets no new head.
- **How it happens.** Take a selected window W = [08:00,09:00) and a session that starts at 08:50. Its END at 09:02
  arrives with ordinary state records for 09:00-09:05. The trigger enqueues W for the session extent and the 09:00-09:05
  bracket, which W does not contain. `ev_enqueue_window` merges the two, because the bridge holds and only one selection
  intersects. The job becomes [08:00,09:05), and the worker assesses and selects [08:00,09:05).
- **What the read then does.** An exact-window read of W, including every `links.self` and Finding href, which embed
  `from/to`, finds no overlapping PENDING/LEASED/FAILED job. It therefore returns `CURRENT` with the session still
  `INCOMPLETE`.
- **When it occurs.** Any update to a selected window coalesces with a bracket beyond its end, and in streaming that is
  the normal case.
- **Why it matters.** It breaks "a failed/leased/pending overlapping job keeps current reads PENDING_RECOMPUTE, never
  silently current", "Do not use the stale older head for a new current claim", and Q11, under which a late terminal
  re-assesses the selected window containing its START.
- **Why the tests miss it.** The six manifests never trigger it: the late END at 08:31 sits inside 08:00-09:00, and no
  record arrives past the window end.
- **Fix.** Assess each intersecting selected window at its exact bounds, and assess any job remainder outside the
  selections as its own bracket windows. Alternatively, get an Architect ruling on how a job maps to windows. Add a
  replay/store test in which a selected window is dirtied together with a bracket past its end, and assert that the
  window gets a new head, or reads PENDING until it does.

### M1 (Medium) - the per-record source-class gate turns a mixed or crossed window into a confident "No sessions observed"

`backend/assetops_backend/analytics/ev.py:440` with `postgres_assessment_store.py:1265` and `:1270`.

- **What is wrong.** Every record's own `classify([id])` state is compared to the window's `classify(all ids)` state.
  If one window holds records from two registered simulation runs, or from bound and unbound batches, the window state
  becomes MIXED/UNKNOWN. Every record then mismatches, so all are `EXCLUDED/SOURCE_UNVERIFIED` and no START qualifies.
- **What the user sees.** The result is `started=0`, the terminals counted as `orphan`, `status=NO_SESSIONS_OBSERVED`,
  and the UI line "No charging sessions were observed in this window." If every record is unbound, all records share
  the state UNKNOWN and pass the gate.
- **Why it matters.** Neither behaviour is fixed by R4/R8. The first contradicts "A permanently unassessable
  configuration is surfaced as UNKNOWN with a limitation, not a successful empty projection".
- **Fix.** Get an Architect ruling on the per-record gate. The likely answer is that a non-coherent window class refuses
  projection and reads UNKNOWN with a limitation, plus a test for each branch.

### M2 (Medium) - `completeness` derivation is an implementer choice, and it marks a contradictory session's terminal as present

`backend/assetops_backend/analytics/ev_reads.py:65-69`.

- **What is wrong.** The booleans are derived from reason codes alone. For CONTRADICTORY, `terminal` is true because
  `MISSING_TERMINAL` is absent, so the row shows a `Terminal` chip next to "Competing end records". The ledger says the
  chips come "from exact uses", and in contradiction the terminals are CONTEXT/CONFLICTING_TERMINAL, never SUPPORT.
- **Why it matters.** r5 fixes only the shape of `completeness`, not how each boolean is derived.
- **Fix.** Have the Architect confirm the derivation. The likely answer is that `terminal` is true only when a terminal
  has SUPPORT use, and likewise for `start`/`clock`. Then assert the contradictory row's chips.

### M3 (Medium) - which evidence ID the Finding's closed `Record {short id}` line names is not fixed by the spec

`frontend/src/sites/EvAssessmentViews.tsx:541-563`.

- **What is wrong.** The spec says "labelled `Record {short evidence_id}`", but the claim cites three records
  (START/FAULT/ABORT). The view picks `claim.fault_evidence_id` and repeats that one ID under "Analysis view not
  available for this EV record". The START and ABORT IDs are not in the disclosure.
- **Why it matters.** It is user-visible, and the mock's matching slot is "Inspect claim evidence" for the whole claim.
- **Fix.** Get an Architect ruling: either the fault ID, or all three support IDs in the disclosure.

### L1 (Low) - `limit` with a non-ASCII digit returns 500

`backend/assetops_backend/ev_assessment_api.py:131`. `str.isdigit()` accepts characters such as `²` that `int()`
rejects. `int("²")` raises `ValueError`, which `served` does not catch, so the request returns 500 instead of 422
`EV_LIMIT_INVALID`. Use `raw.isascii() and raw.isdigit()`, or try/except.

### L2 (Low) - the trigger tests seed accepted evidence and selections directly, but the packet does not say so

`backend/tests/test_w206_ev_enqueue_postgres.py:68-100,117-125`.

- **What is wrong.** These tests clone `accepted_evidence` rows and insert `analytic_run_selection` rows by SQL. The
  task says "No test seeds analytic results or accepted evidence directly".
- **Why it is only Low.** The replay, store and read proofs do go through the registered chain, and q3 P8 acknowledges
  raw-SQL accepted rows in trigger tests. Only the unit tests of the trigger are affected.
- **Fix.** The packet should state this exception.

## Checked and found consistent (no finding)

- **Migration 0025.**
  - Revision chain 0024 -> 0025.
  - Four tables in spec order, with scoped FKs and `UNIQUE(tenant,site,id)`.
  - The R1 nullable `unknown_meter_seconds` and `quantity_state` CHECK.
  - The end/state CHECKs.
  - SUPPORT/EXCLUDED reason rules and the GiST no-overlap exclusion on SUPPORT.
  - The four indexes and append-only triggers.
  - Finding CHECKs widened, keeping the mini_grid/cold arms; the 0022 text is restored on downgrade. 0023/0024 do not
    touch those CHECKs.
  - The downgrade refuses first and covers the EV tables, EV Finding/revision and `ev_charging` jobs, and drops objects
    in reverse order.
- **Correlation (`ev.py`).**
  - R4 precedence, including the SUSPECT event CONTEXT versus SUSPECT meter EXCLUDED split.
  - The 30 s straddle applies only to events. Two FAULTs give no support.
  - Both overlapping deltas are excluded.
  - The R6 power/error bound, the R3 INCOMPLETE span and the R1 contradictory nulls/end bounds.
  - R9 reason order, Q14 claim level/status and whole-window counts.
  - The q3 P3 run rows and P4 policy document.
  - The Finding key, support SHA and EMPTY SHA on withdrawal.
- **Writer and Finding (Q14/Q15).**
  - One transaction per job, with `fail_job` outside it.
  - The idempotent run key and per-session basis reuse.
  - Revision numbering under the advisory lock.
  - Finding columns, transitions, limitations and the withdrawal sweep.
  - Configuration enqueue on the publishing connection for every Foundation/binding insert (R5-2).
- **Reads.**
  - Exact-window selection (r6-1) and no `STALE_SOURCE` (r6-2).
  - Precedence UNKNOWN > HISTORICAL > PENDING > CURRENT (r6-3).
  - Repeated keys give 422 (r6-4). There is no `EV_SELECTION_UNSETTLED` (r6-5).
  - A canonical cursor bound to window/cutoff/basis.
  - One REPEATABLE READ, READ ONLY snapshot.
  - Tenant/Site scope on every query, and wrong type gives 404 `SITE_NOT_FOUND`.
  - Null links except `self` and a proven `finding`.
- **UI.**
  - Panel set/order/titles and the 1.8:1 pair.
  - Cards, strip words, the six headers and column widths.
  - Tone CSS values per the ruling.
  - r5/r6 state copy: no-session, orphan, pending, historical, contradictory, simulation, conclusion and next step.
  - The refusal copy.
  - Disabled Recommendation/destination slots.
  - Packet heights are all under 1.3x and the spec ceilings. I viewed the 1440 sessions and ev-finding captures against
    the mock.

## Checks I ran (worktree at `5f90c3a6`)

- `tools/check-architecture.ps1`: **failed only on Navigation truthfulness and the rail fixture baseline**, which is the
  known P8 tab inventory. Every other section passed.
- `tools/check-agent-workflow.ps1`: passed.
- `npx.cmd tsc --noEmit` (frontend): exit 0.
- `npx.cmd vitest run src/sites/__tests__/evAssessmentRoutes.test.tsx`: 20 passed. The sandbox did not block it in this
  worktree. I did not run the full frontend suite or the production build.
- Focused backend tests on the private `w206rv_test` database: the seven `test_w206_ev_*` files (migration, session rules, vector cases, store, reads, enqueue, publication enqueue): **124 passed**, 0 failed, 0 skipped, in 716 s. The run-owned clone databases were dropped by the harness, and `w206rv_test` was dropped afterwards.
- I did not rerun the full backend or host suites, as the brief instructed. I cite the packet: backend 3221 passed, 0
  skipped, 0 failed; host 787 passed, both at `0dcedf16`. The head adds only packet/ruling text (`5f90c3a6`), so that
  evidence is same-revision for code.
- `tools/layout-evidence.mjs` was not run. The packet records 1440/390 captures and heights from the interrupted state
  only; the other states are covered by jsdom only, as the packet's residual risk notes.

## Residual risk not named in the packet

- H1, the widened-window settlement, also makes selected windows overlap each other ([08:00,09:00) and
  [08:00,09:05)). The default read picks the latest selected window, so denominators across overlapping windows can
  double-count a session for any consumer that sums windows.
- The EV watermark is the Site-wide `max(decided_at)` read at READ COMMITTED, as cold does. A concurrent intake commit
  with an earlier `decided_at` can make the same `known_at` select more rows later. This is shared with cold and not
  specific to W2-06.
