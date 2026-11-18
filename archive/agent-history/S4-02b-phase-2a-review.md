# S4-02b phase 2a: fresh Claude review (read and recompute)

Reviewer: fresh Claude (did not build this). Branch `task/S4-02b-fuel-consequence`. Diff reviewed: `e45bbbc..7c21931`
(`5d400d6` .. `7c21931`, 12 commits). Judged against:
- packet `tasks/S4-02b-fuel-consequence.md`: phase row 2a, item 3, "Migration, recompute and reads";
- `D-2026-10-13-s4-bounded-financial-basis` and its `fuel-cost-1` addendum; `.agent/architect-A-S4-financial-answers.md`;
  `.agent/architect-S4-02-answers.md`;
- the phase-1 carries in `.agent/S4-02b-phase-1-review.md` (M1, M2, L1-L7);
- the owner ruling `.agent/owner-S4-02b-money-demo-2026-10-14.md`;
- the handoff `.agent/S4-02b-phase-2a-handoff.md`, questions `.agent/S4-02b-questions-2.md` (Q1-Q9), and `.ai/CODE_STATE.md`
  "S4-02b phase 2a".

## Verdict: ACCEPT with carries

All of the phase-1 carries landed, and none of them is vacuous. I confirmed each one by mutation or by reproducing it:
- **M1 basis.** The basis uses the window-clipped `(revision_id, from, to)` tuples, sorted by time. A future SUCCESSION replays.
- **L1 to L7** all landed.

The worker is durable:
- a failure becomes a typed FAILED attempt and the item stays pending;
- a retry succeeds;
- a crash after the append replays the same ID.

Currentness never presents a stale or old amount as current *within its own model*. Display rounding is outward. The
route's 404 never falls back. I independently reproduced the owner demonstration numbers (15.8125 / 15.82, then
16.192 / 16.20) and the ordinary split (8 / 2 / 1) through the producer, over TLS, into my own database.

I found one Medium contract defect and one Medium test gap. Neither needs the work returned, because no UI consumes the read
yet. Both must be closed at the start of 2b, before the UI is built on the read:
- **M1.** Under a closed S3 source gate, the consequence read and the bridge mark an amount `CURRENT` /
  `presented_as_current: true`, but the same response says `audit_only.non_current: true`.
- **M2.** Nothing tests the HISTORICAL currentness branch. A mutation that disables it survives every suite.

## Checks I ran (results as observed)

- **Focused suites:**
  - Command: `pytest test_s4_fuel_cost test_s4_consequence_read test_s4_consequence_store_postgres
    test_s4_consequence_recompute_postgres test_s4_power_demo_case_postgres test_s4_assumptions_postgres
    test_s4_assumption_read_postgres test_s4_assumption_publication test_s4_assumption_read_api`.
  - Scratch DB: `assetops_s402brev2_a_test`.
  - Result: **129 passed**, 9 warnings, in 120 s. This matches the handoff's 129.
- **Producer:** `tools/s402b_power_cases.py run --db assetops_s402brev2_cases_test` (own work folder).
  - **0 check failures, `VERIFY PASSED`**, produced in 144 s.
  - P01-power: 25 power means, 150 context readings, 1 new Finding (expected 1 OK). The reload matched: 175 readings.
- **On that DB:**
  - Before any price, `recompute_consequences pending` listed **31** items: the L4 backfill and trigger work for 31
    FindingRevisions.
  - I published v1-v3 and ran `run`: 34 items, all succeeded.
  - Latest FindingRevisions: **8 `POWER_MISSING`, 2 `FINDING_NOT_SUPPORTED`, 1 `POWER_COVERAGE_GAP` (F01-gateway
    `[05:15, 09:15)`), and P01-power `PRICED` 12.65 L / 15.8125 USD**.
  - Through `create_app()` + TestClient, P01-power read `CURRENT`, with display high `15.82` and the bridge amount
    `{0.00, 15.82}`.
  - I published v4. Before the run, P01-power read **`STALE` [`PRICE_SELECTION_CHANGED`]**, with
    `presented_as_current: false`, the bridge in state `STALE` with no amount, and `derived_now` showing v4 at 1.28.
  - `run`: 1 item, **1 appended, 11 replayed**. P01-power is now revision 2, **16.1920 / 16.20**, and `CURRENT`.
    F01-gateway is unchanged (`CURRENT`, `QUANTITY_UNAVAILABLE`).
- **Route probes (same DB):**

| Probe | Result |
| --- | --- |
| Superseded FindingRevision | `HISTORICAL` [`FINDING_REVISION_SUPERSEDED`], `presented_as_current: false` |
| A foreign `consequence_revision_id` on its own | 404 |
| Unknown Finding | 404 |
| A malformed UUID, or `after_revision_no=-1` | 422 |
| No `revision_id` under the closed gate | 409 `PERFORMANCE_CUTOVER_CLOSED` |
| An exact `revision_id` under the closed gate | 200, **`CURRENT` with an amount**: see M1 |

- **`tools/check-all.ps1`:** **All 9 guards passed**.
  - The orphan scan reported 31 tagged and 12 baselined.
  - The working tree carries the same unrelated uncommitted edits as at phase 1 (task files and
    `frontend/docs/architecture/*` checkers). The guards ran over that tree.
- **Not run:**
  - The full backend suite, per the dispatch. The implementer's 2037 passed is unverified by me.
  - Frontend `npm.cmd test`, `npm.cmd run build` and `tsc`: no frontend file changed. The frontend suite and build are
    sandbox-blocked on this machine in any case.
  - Layout evidence: not applicable, because there is no UI in 2a. The handoff correctly records it as `not run`.
  - 401/403 on the new route: no test exercises it (L1), and I did not probe it. It reuses `open_scope`, which runs
    before any lookup (`finding_api.py:249`).
- **Mutations I ran myself.** Each was applied to committed code, run against the relevant suites, and reverted with
  `git checkout --`. The tree was clean afterwards.

| Mutation | Result |
| --- | --- |
| `presented_as_current = is_head` (no CURRENT check) | killed (1 failed) |
| Clipped tuple keyed on assignment ID (M1 regressed) | killed (1 failed, pure) |
| Clipped tuples sorted by revision ID rather than time | killed (1 failed) |
| Worker records failures as success | killed (1 failed) |
| Display high `ROUND_HALF_UP` | killed (1 failed) |
| Pinned consequence: no refusal when not this FindingRevision's (fallback) | killed (1 failed) |
| Migration backfill `WHERE false` (L4) | killed (1 failed) |
| Bridge shows an amount for any non-null row (STALE etc.) | killed (1 failed) |
| **HISTORICAL branch disabled** (`if not finding_revision_is_latest` becomes `if False`) | **30 passed: survived (M2)** |
| **L6 assessment-completeness RAISE becomes `NULL`** | **11 passed: survived (L2)** |
| **`latest_revisions_overlapping` without the latest-revision filter** | **21 passed: survived (L3)** |
| **`skip_if_succeeded=False`** in the worker | **19 passed: survived (L3)** |
| **Pending-work list not scoped to the Finding** | **8 passed: survived (L4)** |

## Carry verification (phase-1 review)

| Carry | Landed | Evidence |
| --- | --- | --- |
| M1 basis on clipped tuples | yes | `fuel_cost.py:466-472` `clipped`, stored as `price_considered`. `TestReviewCarries::test_a_later_succession…` replays. My two mutations were killed. I also reproduced it: v2/v3 publications over the P01 window replayed, and only v4 appended |
| M2 Q9 text | yes | Corrected in questions-1, the phase-1 handoff and `CODE_STATE`, and the original is kept as superseded. My producer run reproduces the 8 / 2 / 1 split |
| L1 work CHECK `<=` | yes | `0011:205`. Zero-width test |
| L2 reviewer field, re-pinned digest | yes | `fuel_cost.py:77-79`, `fuel-cost-1-cases-v1.json:5` |
| L3 whole seconds | yes | `fuel_cost.py:392-396`. The DB CHECK compares the exact epoch (`0011:175`) |
| L4 backfill and PENDING read | yes | `0011` final INSERT. The read gives `NOT_YET_COMPUTED_NO_WORK_RECORDED`. My mutation was killed |
| L5 test gaps | yes | Per the handoff (I did not re-mutate those three) |
| L6 price value/currency, PRICE link, assessment completeness | **partly tested** | The value and PRICE-link checks are tested. The assessment-completeness half is untested (L2) |
| L7 docs | yes | S4-02a handoff note and `CODE_STATE` |

Migration 0011 was edited in place. This is acceptable: `main` (`14ad5ef`) has no 0011.

## Focus areas

- **Recompute durability** (`recompute.py:102-125`):
  - Every exception becomes a typed FAILED attempt, and the item stays pending (no SUCCEEDED attempt).
  - If `record_attempt` itself fails, the run aborts, and the next run replays through the idempotent append. This is
    tested.
  - There is no retry cap and no backoff (Q6), which is acceptable for a one-shot CLI.
- **Currentness** (`consequence_read.py:157-183`):
  - CURRENT requires the head's full basis digest to equal a fresh derivation. Because the basis includes the amount,
    a CURRENT head's amount is by construction the amount the inputs give now.
  - The read takes the chain snapshot and the derivation in separate transactions. Every interleaving I could construct
    produces a false STALE, never a false CURRENT, except one microsecond window. In that window a technical input
    changes between `load_input` and the price snapshot, and no work row exists for that change anyway (Q2).
  - HISTORICAL never derives and never presents as current: verified by probe, but untested (M2).
- **Rounding** (`consequence_read.py:49-66`):
  - The low bound uses `ROUND_FLOOR` and the high bound `ROUND_CEILING`, to the ISO minor unit.
  - The 33-entry table is correct for the 0- and 3-digit currencies listed.
  - An unknown currency gives no display amount, and the bridge shows none.
  - `quantity.high_display` is ceilinged to 0.01 L.
- **Route** (`finding_api.py:245-277`):
  - Scope and access come first.
  - A store that is absent gives 503 (tested). A store that fails also gives 503, through `consequence_down`; this is
    untested at route level, but the bridge degrades to `UNAVAILABLE` (tested).
  - A bad or foreign ID gives 404 and never falls back (tested, and my mutation was killed).
- **Owner demonstration case:**
  - It is labelled `AUTHORED S4-02b DEMONSTRATION CASE`.
  - `s4-finding-cases-v1` is untouched: it is not in the diff.
  - Its day is clear of every S4 case day (tested).
  - The producer posts over TLS with the registered gateway credential into its own `assetops_s402b*` DB, and refuses
    any other name.
  - The arithmetic checks: 23 × 5 min × 20 kW × 0.3 × 1.10 = 12.65 L; × 1.25 = 15.8125, and × 1.28 = 16.192.
  - The Postgres test uses the in-process submit path. Only the producer exercises TLS.
- **Deviations:**
  - The bridge shape change breaks the S4-02a wording. `SiteFinancials.tsx:481` would label a PRICED head "No price for
    the whole window" next to a "Modelled potential…" reason. It never shows an amount, so it is wrong but not
    over-claiming. Acceptable *only* because the branch is unmerged and 2b replaces it. The branch must not merge
    without 2b.
  - Evidence acceptance enqueues no work: see Q2.

## Findings

### M1 (Medium, fix first in 2b, backend): under a closed S3 source gate the amount is presented as current

- **Where.**
  - `finding_api.py:262-264` and `:311` pass only `finding_revision_is_latest` to the read.
  - `consequence_read.py:182` sets `presented_as_current = is_head and state == "CURRENT"`.
  - `bridge_consequence` (`finding_api.py:336-358`) returns `currentness: "CURRENT"` and an amount.
- **Observed.** `assetops_s402brev2_cases_test` has no Performance comparison report, so the gate is closed. An exact
  `revision_id` read of P01-power returns all of the following:
  - top-level `audit_only.non_current: true` ("this recorded revision is not a current claim");
  - `currentness.state: "CURRENT"`, `current_amount_shown: true` and `consequence.presented_as_current: true`;
  - a bridge with `currentness: "CURRENT"` and amount `{0.00, 15.82}`.
- **Why it matters.**
  - The handoff tells 2b: "Show the amount only when `consequence.presented_as_current`". A UI following that rule
    would present a money amount as current on a Finding the same response declares audit-only.
  - The packet requires a typed closed-source state in this read.
  - The Architect requires that a pinned row "never masquerades as current".
- **Fix.**
  - Pass `source["permitted"]` into `ConsequenceReadService.read`.
  - When the source is closed, give currentness `AUDIT_ONLY` (or `HISTORICAL` with reason `SOURCE_CLOSED`), set
    `presented_as_current` false, and make the bridge return that typed state with no amount.
  - Add a route test with a closed gate and an exact `revision_id`.

### M2 (Medium, test gap): the HISTORICAL branch is unprotected

- **Where.** `consequence_read.py:157-159`.
- **What is wrong.** Replacing the condition with `if False` passes all 30 tests in the recompute, store and API suites.
  The only HISTORICAL coverage is a stubbed bridge test.
- **Why it matters.** Without it, the head of a superseded FindingRevision would be presented as current. The packet
  names this contract: "Old pinned row is labelled historical".
- **Fix.** Add a Postgres test that appends a second FindingRevision, or reuses a multi-revision case. It must assert
  that the old revision's read is `HISTORICAL`, with `presented_as_current` false and no bridge amount.

### L1 (Low, test gap): the new route has no 401/403 or failing-store 503 test

The route reuses `open_scope`, and `consequence_call` maps `consequence_down`. Mirror the S4-02a bridge tests
(`test_s4_assumption_read_api.py:143-147`) for `/financial-consequences`.

### L2 (Low, test gap): the L6 assessment-completeness half of `financial_consequence_links_complete` is untested

- **Where.** `0011:306-311`.
- **What is wrong.** The test (`test_s4_consequence_store_postgres.py` "Review L6, at commit") clones a PRICED row, so it
  trips the PRICE-link RAISE first. Disabling the completeness RAISE survives. The test comment claims both halves.
- **Fix.** Add a NOT_EVALUATED or UNPRICED clone without assessment links, matched on "does not link every INTERVAL
  assessment".

### L3 (Low, test gaps): worker target selection and concurrent skip

- **Where.** `postgres_consequence_store.py:281` (latest-revision filter) and `:255` (`skip_if_succeeded`).
- **What is wrong.** Both mutations survive.
- **Why it matters.**
  - Without the filter, ASSUMPTION_PUBLISHED would reprice superseded FindingRevisions, which contradicts Q5.
  - Without the skip, two workers would each record a SUCCEEDED attempt. The unique index would then raise on the
    second, and that worker would convert the error into a FAILED record. This is harmless, but it is unproven.
- **Fix.** Add one test per item.

### L4 (Low): bridge STALE wording claims a recompute is under way

- **Where.** `finding_api.py:324`: "it is being recalculated".
- **What is wrong.** In the Q2 case (`TECHNICAL_INPUT_CHANGED` with no pending work), and with a one-shot CLI (Q6),
  nothing is necessarily queued.
- **Fix.** Word the state from `pending_work`, for example "will be recalculated" versus "needs recalculation". Settle
  this with the 2b copy.
- The pending-work list scoping (`postgres_consequence_store.py:336`) is also untested; the mutation survived. It affects
  only the listed `pending_work`, not the state.

## Q1-Q9 rulings

| Q | Ruling | Note |
| --- | --- | --- |
| Q1 four currentness states | **Acceptable** | It refines the packet's STALE/PENDING without weakening it. 2b may merge STALE and PENDING in the copy. Add the closed-source state (M1) |
| Q2 fresh derivation; evidence acceptance enqueues no work | **Acceptable for 2a; batched Architect question, non-blocking** | Fail-closed: the head shows STALE, never current. Ask whether an `accepted_evidence` trigger, or a periodic sweep, should enqueue. Fix the wording (L4) |
| Q3 replay of a non-head basis | **Acceptable** | I agree it is unreachable. Price and FindingRevision IDs are fresh, and the evidence and examined sets only grow. If it ever happened, the result would be a fail-closed STALE |
| Q4 backfill plus PENDING read | **Acceptable** | Verified: 31 rows enqueued on a fresh producer DB |
| Q5 work targets | **Acceptable** | Matches the packet. The latest-only filter needs a test (L3) |
| Q6 one-shot CLI worker | **Acceptable** | The packet allows "retry a durable worker". Whether a deployment needs a scheduler is an operations or Planner choice, not an Architect one. The walkthrough runs it explicitly |
| Q7 bridge shape change | **Acceptable as a deviation** | Only because the branch is unmerged. 2b must update `financialsClient.ts:79` and `SiteFinancials.tsx:481`. Do not merge without 2b |
| Q8 display rounding | **Acceptable** | The table is correct. A variable-scale unrounded text is fine as long as clients use Decimal |
| Q9 producer DB | **Acceptable** | The name guard works, and `assetops_s4cases` is untouched |

The only Architect question is Q2. It is batchable and does not block 2b.

## Residual risk not named in the packet or handoff

- **Closed-gate walkthroughs.** A producer-template DB has no comparison report, so every Finding read is closed-gate
  and audit-only. That makes M1 the *default* walkthrough state, not an edge case. Either the 2b walkthrough opens the
  gate, or M1's fix shows audit-only money.
- **Cost per read.** Every bridge and read call runs a full `load_input` plus a price snapshot. This is fine at the
  scale of one Finding, but a list view over many Findings would multiply it.
- **Unmapped store errors.** `_run` maps only `OperationalError` and `ProgrammingError` to unavailable. Any other DB error
  inside a derive would surface as a 500 on the bridge, rather than as typed `UNAVAILABLE`.

## Carries for phase 2b

1. **First commit (backend):** M1 (closed-source currentness and bridge, plus a route test) and M2 (HISTORICAL Postgres
   test). Do these before any UI binds to `presented_as_current`.
2. L1-L3 tests. L4 wording together with the 2b copy.
3. Update the frontend types and wording for `PRICED`, `STALE`, `PENDING`, `HISTORICAL`, `UNAVAILABLE` and the new
   closed-source state. Show the amount only from `display.amount_low/high`, and only when `presented_as_current`.
4. Walkthrough: decide whether the gate is open (run the comparison) or whether money is shown as audit-only.
5. Send Q2 to the Architect in the milestone batch.
6. Do not merge `task/S4-02b-fuel-consequence` until 2b replaces the S4-02a Financials wording.

The scratch DB `assetops_s402brev2_cases_test` is left in place. It holds the reproduced state: v1-v4 published and
recomputed, P01-power at revision 2. Drop it freely.
