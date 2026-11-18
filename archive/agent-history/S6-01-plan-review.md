# S6-01a / S6-01b plan review

Reviewer: fresh Claude reviewer. I did not write the packets, the brief, the work order or the Architect ruling.
Reviewed: `tasks/S6-01a-action-store-read.md`, `tasks/S6-01b-action-ui.md`, `tasks/S6-01-action-change.md` (umbrella), the `tasks/README.md` row and registry `task` fields on `plan/S6-01-refine` at `7e0c5c43` (base `main` = `ad2a96d0`). The code-reality checks were against `main`.
Checked against: `D-2026-10-14-action-lifecycle-and-policy-application`, `.agent/A-action-lifecycle-review.md` (L1, L2, I1, P1-P10), `.agent/architect-autonomy-2026-10-15-answers.md` item 3, `.agent/planner-S6-01-brief.md`, `backend/TESTING.md`, `tools/checks/configuration-persistence.ps1` rule 8, and the shipped S1 publish path.
Architect ruling: when I finished, `.agent/architect-S6-01-answers.md` and `D-2026-10-15-s601-action-store-and-ui` were in the working tree but not committed. It amends Q1 to `reserve-trial-1`, accepts Q2-Q5 with detail, and requires packet changes in both packets. I read it and I do not repeat what it already orders.

## Verdict: RETURN

There are three Medium findings and no High. All three are packet-level fixes that fit in the Planner fold-in round the Architect ruling already requires. The rest of the plan is sound. It splits into a non-UI slice (a) and a held UI slice (b) on main, with no LR-01 or S5-01 dependency. It uses L1 model (a), with Action created on acceptance. It defines the acceptance and event idempotency keys, a tenant-scoped `action_code`, an expected-revision check under the Site lock with a typed 409 and a FAILED event, APPLIED in the publish transaction, no Action backdating (effective time at or after recorded time and after ACCEPTED), and the identical-retry-before-`FOUNDATION_NO_CHANGE` rule. It pins the origin revision and shows the latest beside it, uses the `site_code` routes, says no mock money is a saving, and labels SYSTEM demonstration commands. Each packet has two phases, its last phase review is the slice review, and each runs one full suite.

## Findings

### M1 (Medium, acceptance/architecture gap). The packet never says which module may write the Action tables in the publish transaction, or how rule 8 changes.

- **Where:** S6-01a "New storage and publish" (lines 29-31) and Q2 (line 55). Rule 8 is in `tools/checks/configuration-persistence.ps1:590-700`. It allows eight named PostgreSQL writers (`$pgWriters`), confines each to its own tables, and refuses any SQL write in any other module ("A second product database writer..."). `publish_configuration` (`backend/assetops_backend/sites/adapters/postgres_foundation_store.py:607-656`) opens its own transaction inside `work(connection)`, and its first statement is the Site `FOR UPDATE`.
- **What is wrong:** S6-01a needs `action`, `action_event` and `action_policy_change` rows, plus written-ID children. They are written on accept, without a publish, and atomically with the Foundation, SPLIT and binding writes on apply. The Architect's Q2 ruling also requires the Action lock to come before the Site lock inside the same transaction. The packet does not name the writer module. It also does not choose between two designs: (a) the Foundation adapter writes the Action tables, or (b) a new Action adapter shares the Foundation adapter's connection. Either way it must say how the transaction is opened so the Action lock comes before the existing in-`work` Site lock, and how rule 8 is extended. Today the guard does not know the new tables. Design (a) passes silently and widens the Foundation writer. Design (b) fails the guard until a ninth writer is added. The precedent for adding a writer is S4-02d's eighth writer, which `D-2026-10-14-s402d-schedule-storage-and-install-gate` ratified explicitly.
- **Why it matters:** this is the central seam of the slice (P3/P4). If an implementer has to invent the writer boundary, they either loosen an existing guard without review or have to restructure the S1 transaction mid-build. Both are architecture changes, and the slice-level review would catch them only after the build.
- **Fix:** name the Action adapter (for example `backend/assetops_backend/actions/adapters/postgres_action_store.py`, **new**) as the sole writer of the new tables. Choose and state the connection/transaction seam: either the S1 adapter accepts a caller-owned transaction, or a narrow hook receives the connection after the Action lock. List the rule-8 additions: the writer path, insert-only tables, no UPDATE/DELETE, and "no other module writes an Action table". Add a guard proof that the Foundation adapter writes no Action table. If this creates a ninth writer, record it as an Architect ratification item (it can go into the same S6-01 decision).

### M2 (Medium, correctness). The recommendation identity and accepted snapshot are not persisted, so Recommendation reload after acceptance or apply is undefined.

- **Where:** S6-01a line 15 (recommendation key `(tenant_id,site_id,finding_revision_id,rule_id,rule_version,asset_id)`) and line 29 (`action` columns). The fixture list also says "Persist proposed/unavailable". S6-01b line 17 (Recommendation shows the proposed reserve value, basis and limitation) and its reload states.
- **What is wrong:** the recommendation is computed live. Under the Architect's `reserve-trial-1`, it is eligible only while the current Site Foundation reserve equals the pinned reserve. After a successful apply, GET recommendation for the same FindingRevision therefore turns into "unavailable: stale basis". The packet has no recommendation table, and its `action` column list has no proposed or old value, unit, pinned Foundation revision ID or rule input IDs/digest. The key also leaves out the pinned Foundation basis, so two proposals over different Foundation revisions share one key. The Architect asks to "pin input IDs, rule version, old/proposed values and the limitation", but the packet names no column or row for them, and nothing defines what `GET .../recommendation` returns once an Action exists.
- **Why it matters:** `recommendation:1#a` and the "accepted pending / applied pending / reload" states in S6-01b would either show a different (unavailable) recommendation from the one accepted, or force the implementer to reconstruct it. That breaks P6-style origin pinning for the recommendation itself, and it leaves "Persist proposed" in the fixture without a store.
- **Fix:** add the pinned Foundation revision ID (or basis digest) to the recommendation key. On acceptance, persist an immutable accepted-recommendation snapshot: rule id/version, input assessment/evidence IDs and digest, pinned FoundationRevision ID, asset, field, unit, old and proposed value, and limitation text or code. Store it on `action` or in a new child row. Define the read: once an Action exists for the key, GET recommendation returns that snapshot with the Action link, plus the live recomputation status beside it. Replace "Persist proposed/unavailable" with "served from persisted inputs" unless a recommendation table is added.

### M3 (Medium, acceptance gap). P9's backdated `occurred_at` case cannot be produced with the packet's commands.

- **Where:** S6-01a line 25 ("`occurred_at` may be backdated for non-application activity ... Accept/apply use server time") and line 37 (the fixture needs a "backdated non-application `occurred_at`"). S6-01b line 17 (History "distinguishes backdated occurred time"). Carry P9 requires it.
- **What is wrong:** the only event kinds are ACCEPTED, APPLIED and FAILED, and all of them use server time. No command or event kind can carry a backdated `occurred_at`, so the fixture, History state and P9 cannot be satisfied without an event kind nobody has approved.
- **Fix:** name one bounded event kind and its command. An example is a SYSTEM demonstration `NOTE`/`OBSERVED` event with an explicit `occurred_at` earlier than `recorded_at`, which changes no reduced state. Give its precondition, refusal (for example a future `occurred_at` returns 422) and idempotency. Alternatively, record that the Architect defers the case and remove it from both packets and the P9 claim.

### L1 (Low). The transition table leaves out apply on an already-APPLIED Action, and FAILED-then-retry keying.

S6-01a lines 19-25. State the response to an apply with a new idempotency key on an APPLIED Action (suggested: typed 409, with no FAILED event because no publish was attempted, or say otherwise). State the reduced application state after FAILED (still ACCEPTED/pending). State that a fresh attempt needs a new idempotency key while the old key returns the FAILED event. The concurrent-apply proof covers only identical commands.

### L2 (Low). Migration ordering with LR-01.

`main` ends at `0013_schedule_state`, and the unmerged LR-01 adds `0014_source_clock_attestation` and `0015_finding_returning_basis`. A new S6-01a migration cut from main with `down_revision = "0013_schedule_state"` gives two heads once LR-01 merges first, which is the work-order order. State that the S6-01a migration re-chains onto main's head at rebase, and that the full suite and slice review run on the re-chained revision.

### L3 (Low). The queue mapping differs from the S4-02a/b precedent.

`parseQueue` maps only `S6-01` to the umbrella. S6-01a/b are found only through `parseGateQueue`. An active or in-review S6-01a still stops selection globally (`delivery_next_work.cjs:335-340`), but per-candidate `taskInfo` is missing. A decision that selects an S6-01a/b node therefore reports `user_review_required: null`, and for S6-01b the correct value is `true` (`:345`). S4-02a and S4-02b each have their own README row. Give S6-01a and S6-01b their own rows (umbrella row kept for closeout), or accept the null as recorded.

### L4 (Low). Some citations need to be precise.

- "S1 binding tests" (S6-01a line 42): the file is `backend/tests/test_s1_bindings_postgres.py`.
- S6-01b's Changes route sits under Site Foundation. `frontend/src/sites/__tests__/foundationScreen.test.tsx:306,344` asserts that "Changes" is not a Foundation subtab and that `foundationViewFor("changes")` is null. `FoundationView` is `"model" | "sld" | "readiness"` (`frontend/src/sites/FoundationSubtabs.tsx:32`). Cite these, state whether `/foundation/changes/{change_id}` stays a non-subtab deep route, and say what bare `/foundation/changes` returns.

### L5 (Low). Proof of the exact consumer.

S6-01a says payloads are "consumed by S6-01b", but S6-01b does not exist when S6-01a merges. Make the consumer mechanical. Commit the walkthrough's API responses (Action, events with each selector, recommendation, change) as a contract fixture keyed by the `D-action-records` manifest IDs. Check its fields in the S6-01a tests, and have S6-01b's frontend tests load the same fixture. This turns "exact S6-01 consumer demonstrated" from a statement into a check.

## Required fold-in, not repeated as findings

The Architect ruling orders packet changes before implementation: the `reserve-trial-1` eligibility and numeric source with boundary tests, an eligible plus an ineligible fixture, the callback returning every written or superseded ID, the Action-then-Site lock and rollback tests, removing wrong-Site from the persisted FAILED cases (the packet currently lists it at line 37), the scoped SYSTEM capability field with absent and denied tests at 1440 and 390, and the selector 422 wire contract. The packets are not implementation-ready until these and M1-M3 are folded in.

## Coverage of the carries

- L1 / P1: covered (model (a), acceptance key, `action_code` sequence, event uniqueness).
- P2: covered in principle; the rule itself is now settled by the Architect's Q1.
- P3: covered.
- P4: covered, but the writer seam is open (M1).
- P5: covered.
- P6: covered for the Finding origin; the recommendation origin is open (M2).
- P7: covered.
- P8: covered; the Changes route needs the L4 citations.
- P9: the backdated case is missing (M3); the other cases are covered.
- P10: covered (new real columns).
- L2: covered (S6-02 defers to `A-S6-verification` with `VERIFIED`/`INEFFECTIVE`/`INCONCLUSIVE`).
- I1: covered through P3-P5.

## Code reality (checked on `main`)

Verified:

- `foundation_service.py`: `publish_battery_reserve` at :362, `_publish_content_change` at :415, with the planner covering check, SPLIT, `FOUNDATION_NO_CHANGE` 422 and `FOUNDATION_CLOCK_BEHIND` 409 through about :528.
- `postgres_foundation_store.py`: Site `FOR UPDATE` at :612-616 (cited as 607-620).
- `finding_api.py`: Finding route at :112-150.
- `finding_read.py`: `FindingReadService` at :306.
- `postgres_finding_store.py`: `revision_lineage` at :274.
- Migration 0009: `finding_revision` at :64-105.
- Technical design :55-56: `action` and `action_event` rows (proposed, not shipped).
- `backend/TESTING.md` :7-31 rules.
- Test files `test_s4_finding_read_postgres.py` and `test_s1_foundation_postgres.py`.
- `App.tsx`: Finding routes at :274-290.
- `SiteFinding.tsx`: the recommendation unavailable statement at :120.
- `screen-manifest.json`: `recommendation` and `action-*` in the cited ranges, and `changes` at :161.

Correctly marked **new**:

- The Action tables, routes, store, fixture and loader.
- The S6-01b components and the walkthrough tool.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 224 nodes". The S6-01a and S6-01b `task` fields are set on 5 and 6 nodes.
- `--next-work --json`: exit 0, `ranked`, `stop_owner` (LR-01 2.02 vs `I-action-store` 2.016). Not refused. The packet Status lines `implementation-ready ...` parse as `not_started`, and `USER_REVIEW_REQUIRED` parses false for a and true for b.
- `tools/check-agent-workflow.ps1`: passed.
- I did not run any test suite, `tools/check-all.ps1` or tsc. This is a plan with no code, there are no `node_modules`, and the dispatch said so.

## Residual risk

- `reserve-trial-1` needs a pinned Candidate with numeric SOC above reserve plus 10. The existing S4 demonstration cases may not contain one. If they do not, `D-action-records` needs authored accepted evidence, which must carry the demonstration label (`demonstration_label.py`) through the Action surfaces.
- An applied reserve change has no Lab or simulator effect until S6-02. The S6-01b copy must not suggest the Site now behaves differently.
