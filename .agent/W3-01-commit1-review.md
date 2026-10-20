# W3-01 commit-1 unit review (shared public provenance DTO + cross-lane compatibility)

Reviewer: fresh Claude reviewer (did not author). Worktree `AssetOpsV1-review2`, branch
`task/W3-01-estate-claim-action-roots`, head `28906b40`. Range `1c409a3d^..HEAD`; net change `git diff main...HEAD`
(30 files). Authority: task packet, `.agent/W3-01-build-spec.md` (shared-provenance decision, D2/D3/D6, Run 1-4
rulings, selection-token v2), `.agent/W3-01-lane-a-adapter-contract.md`, `.agent/W3-01-phase-handoff.md`.

## Verdict: REVISE (no High; three Medium, all Architect rulings rather than code defects)

The DTO module, the cold/EV integration, the cursor fence and the ruling-7 test match the rulings as written.
I found no regression on W1 fields and no defect in the digest or reason rules. The three Medium items are
behaviour that the rulings either did not address or produce as an unintended side effect, and two of them are
user-visible. Each needs an Architect ruling (and possibly a small fix) before the W4 cherry-pick consumes this range.
Everything else is Low or confirmed.

## Findings

### M1 (Medium, needs Architect ruling): "Assessment basis" exact references now show the public selection digest, and show nothing on a pending read
- `frontend/src/sites/ColdAssessmentViews.tsx:438` ("Assessment basis"), `frontend/src/sites/EvAssessmentViews.tsx:324`
  ("Assessment basis (SHA-256)", sessions envelope) and `:673` (EV Finding detail) read `source_provenance.basis_sha256`.
  This field used to hold the stored assessment basis (cold `ColdSelected.basis`, EV `sel["basis"]`, the cold
  detail's stored Finding basis). It is now the `source-provenance-basis/1` selection digest. The label is unchanged,
  so it is now wrong.
- Failure scenario: on any cold temperature read or EV sessions read with a pending job, `source_provenance` is the
  pending alias (ruling 5), whose digest is `null`. The "Assessment basis" row then shows "not recorded" even though
  an assessment is selected and its stored basis exists. Before this commit it showed the stored basis.
- The handoff's reading 7 covers only the two EV labels. The cold label and the pending-null effect are not
  mentioned. None of these rows is in the v69 mock (they are app-only exact-reference disclosures), so no mock
  spec binds them: this is a product-copy and field-source decision.
- Fix options for the Architect: (a) relabel to the selection digest and read `selected_source_provenance` for
  selected facts; (b) keep "Assessment basis" by surfacing the stored basis (the private fence value is already
  computed) in a separately named field; or (c) drop the rows. The decision belongs to the Architect, not the
  builder, under "implementers never decide".

### M2 (Medium, needs Architect ruling): selected-assessment facts are labelled with the pending set's class
- Ruling 5 makes the envelope `source_provenance` the pending alias whenever pending work exists. Several consumers
  use that alias as the source label of the **selected** assessment's facts:
  - cold claim-boundary text and the "Source classification" reference (`ColdAssessmentViews.tsx:435,452-453`);
  - cold Site evidence rows (`coldSiteViews.tsx:1113,1151`);
  - EV `claim_rules[].source_class` (`backend/assetops_backend/ev_site_reads.py:699`) and the EV Site
    "source ..." lines (`EvSiteViews.tsx:796,1015,1211,1286`);
  - the EV simulation badge (`EvAssessmentViews.tsx:158-161`).
- Before this commit, cold used the selected head's stored `source_gate.classification` and EV used the persisted
  class. Pending EV changed only through `_unassessable`.
- Failure scenario: a selected head is REGISTERED_SIMULATION, and then a late upload brings MIXED accepted rows into
  the window with a pending job. The cold claim text "Accepted probe readings support a ... excursion" now carries
  "source: Mixed sources", and the EV claim rules report `source_class: MIXED`. Both describe the old selected result,
  not the pending set.
- The Run 3 frontend row says a current-set notice may use the alias "without labelling selected facts as pending".
  It does not say which of these surfaces count as current-set notices. Rule per surface whether it reads
  `selected_source_provenance` or the alias.
- Related wire change: with no selection, `classification` changes from `null` to `"UNKNOWN"`. The cold Site's
  "Source classification unknown" branch (`coldSiteViews.tsx:1113`) is now unreachable and renders "Unknown", and the
  EV lines render the raw `UNKNOWN`. This part is Low and covered by Run 3 q1 ("cold's classification:null is
  retired").

### M3 (Medium, needs Architect ruling): two ruled gates have consequences the rulings did not consider
1. **The EV Finding pin breaks one withdrawal shape.**
   - Where: `postgres_assessment_store.py:2682`, q4 ruling 4. `PostgresFindingStore.ev_apply`'s second loop
     (`postgres_finding_store.py:695-704`) withdraws a SUPPORTED Finding "whose session this basis no longer
     materializes". It appends `NO_LONGER_SUPPORTED` pinned to the new assessment, with the old `claim.session_id`.
   - The problem: that session is absent from the new assessment's `result.session_revision_ids` by construction.
     So `/ev/findings/{id}` (which reads a withdrawal at the selected assessment as history) now raises
     `EvReadUnavailable`, which is 503. Before this commit it returned 200.
   - What is tested: the w206 withdrawal vector only covers the first-loop shape, where the session is still
     materialized.
   - What I could not run: I did not reproduce the second-loop shape. The gap is shown from the code path.
   - Needs: a ruling on whether a withdrawn revision without a pinnable session (i) gets a row DTO without a session
     member, (ii) keeps the 503, or (iii) omits the row block. The literal q4 text says (ii), but that 503s a
     reviewed W2 route variant.
2. **Historical reads take the pending block from today's jobs.**
   - Where: `postgres_assessment_store.py:1714` (cold) and `:2287` (EV). Run 2/3 gate the pending block only on an
     overlapping open `recompute_job`. Neither job query has a cutoff filter.
   - The problem: a read at an earlier `known_at` (currentness `HISTORICAL`) therefore gets a pending block, and the
     pending alias, whenever a job is open *now*. The pending set itself is computed at the historical cutoff.
   - Failure scenario: reloading the same historical URL returns a different `source_provenance` before and after the
     worker drains. That breaks the reload-stability expectation for historical variants.
     `test_historical_cutoff_precedes_pending_job` asserts no provenance block.
   - Needs: a ruling on whether a historical read shows `pending_source_provenance` at all.

### L1 (Low): the persisted-class mismatch is not exercised on a public EV read
The Run 3 EV row asks for "persisted-class mismatch vectors" in the w206/w207 suites. Ruling 4 is proven only by
the direct adapter test `test_persisted_ev_class_disagreement_unknown`. The public path relies on
`(sel["result"].get("source_provenance") or {}).get("class")` (`postgres_assessment_store.py:2282-2285`), which the
positive w206 vector covers only by agreement. A wrong key would turn every selected EV read UNKNOWN, which that
vector would catch, but no public test shows that a disagreement surfaces `SOURCE_CLASS_MISMATCH`. Fix: one w206
vector that edits a stored result's class inside a rolled-back transaction, or document that the unit test is
sufficient.

### L2 (Low): cold "changed selected basis returns 409" uses a forged basis
`test_w203_cold_reads_postgres.py:166-171` proves that a random basis and the public digest both return 409. It does
not prove that a cursor from the real first selection is refused after a real reselection. EV has the real
before/after pair. Acceptable as a fence test; noted against the Run 3 cursor row.

### L3 (Low): the named test `test_pending_envelope_does_not_relabel_selected_row` does not exist
Its assertions are covered in substance by `test_w203_cold_reads_postgres.py::test_pending_historical_reload`
(cold list, detail and siblings) and the w206 pending vectors. Rename the test or record the mapping in the packet,
so the W4 cherry-pick reviewer can find it.

### L4 (Low): stale build artefact in the range
`.agent/W3-01-lane-a-partial.patch` (588 lines, already applied) travels with the commit-1 range into the W4
cherry-pick. Drop it or mark it historical.

### L5 (Low): the ruling-7 test reads W1 through the service layer, not HTTP
This is the declared reading L-B3. `_w1` builds `ConsequenceReadService` with the `ELIGIBLE` stub gate and the
production `build_public_provenance`. That proves the DTO mapping, but not the HTTP wrapper. The wrappers are
covered by `test_s4_finding_api.py` and `test_s5_overview_postgres.py`. Acceptable.

## Checked and confirmed (no finding)
- **Digest (ruling 2, D2).** The sorted-key compact canonical form uses
  `{version, tenant_id, site_id, selected_revision_ids, accepted_evidence_ids}`, with lowercase sorted distinct IDs.
  The digest is null only when nothing is selected. An empty citation set with a selection gives a digest, and the
  W20 literal `ed86298a...` is pinned in the test.
- **Selection helpers.** Each helper matches ruling 2 and the q3 sets exactly. W1 defaults to `{fr}` and
  `{cid, fr}`.
- **EV money (q4).** The money row selects `{row, stored assessment, all linked sessions}` and cites only
  `ev_consequence_evidence`. A NULL Finding pin is accepted, a non-null pin, missing assessment or inconsistent
  session fails closed, and a guard row has no block.
- **Reasons (D2).** Sorted by `(code, ids, canonical extras)`, with typed extras and resolver nulls kept.
  `detail.reasons` equals the top-level reasons.
- **EV mismatch adapter (ruling 4).** Reasons are appended with the full sorted cited set and `persisted_class`, and
  only `detail.state` and `detail.reasons` are overridden. No comparison is made without a selection, and no stored
  result is mutated.
- **`dual_blocks` (ruling 5, q2/q3).** It raises on a pending digest. Both-null gives the literal six-key alias.
  The pending block uses Run 2's exact SQL (cold) and all of `_ev_rows` (EV), and is present even when the pending
  set is positive or empty.
- **Cursor fence (ruling 3).** It moved to the private stored basis: cold `selected_basis` and
  `cold_site_reads.py:505`, EV `_basis` with the `route|basis` prefix. The payload and 409 behaviour are unchanged,
  and the public digest is never rewritten.
- **Detail top-level (q3 Q2).** It is the row DTO, the siblings stay the envelope's, and the stored `basis_sha256`
  keeps its own field. Cold no longer assigns `revisions[0][9]` into the DTO.
- **Pins (q4 rulings 2-4).** The cold episode/assessment, cold consequence and EV Finding pins are enforced on the
  snapshot connection.
- **W1 compatibility.** Every resolver top-level field is unchanged (only the `reasons` order is canonical, per D2).
  The `unresolved` fallback keeps its old shape. `build_source_provenance` is retained for the verification ports.
  Action, overview and Finding API wrappers are unchanged. No Action snapshot persists the block (the
  `actions/service.py:340,698` reads only).
- **`sourceProvenance.tsx`.** It reads `classification ?? state`, prefers `detail`, has safe empties and adds the
  `SOURCE_CLASS_MISMATCH` copy.
- **Ruling-7 test independence.**
  - The digest is recomputed by the file's own `digest()`. Selected IDs come from the public read, and pins and
    cited sets come from scoped DB queries.
  - Page size 1 (following every cursor) is compared against 200 for rows and all three siblings. This holds for
    W1 history (25 vs 1), cold (`normal` + `excursion`, with non-empty Finding and consequence rows asserted) and EV
    (all six replays, envelope, sessions, Findings and details, money UNPRICED and priced).
  - It is not a `PublicProvenance` unit call, and it uses no synthetic selected IDs.

## Builder readings classification
| Reading | Status |
|---|---|
| Lane A q4 readings 2-6 (cold Finding pin, cold consequence pin, EV Finding pin, EV pending job, failed link reads) | Covered by Run 4 rulings 2-6 (but see M3.1 and M3.2 for the unconsidered cases) |
| Lane A 1 (EV money set inlined, no Lane B helper) | Covered by q4 ruling 1 ("or an inline sorted set") |
| Lane A 2 (EV money integrity via direct `money_row_provenance_on` calls) | Covered (q4 asks for an unavailable response; a direct call on the real DB is an acceptable proof because FKs block the stored shape). Low risk |
| Lane A 3 (cold overview Finding projection unchanged; rows carry the DTO) | Covered by Run 3 q3 (item key on `_item` rows) |
| Lane A 4 (public reasons keep extras; w206 `_reasons` subset check) | Covered by D2 and Run 1 reading 4 |
| Lane A 5 (test-only DB edits: jobs DONE then restored, EXCLUDED meter row, retired cold job) | Covered (test technique; Run 3 asks for those vectors) |
| Lane A 6 (S6 harness keeps `build_source_provenance`; production block checked separately) | Covered by Run 3 reading 4 and the Action row |
| Lane A 7 (EV "Assessment basis (SHA-256)" label shows the public digest) | **Needs Architect ruling** (M1, widened to cold and pending-null) |
| Lane B L-B1 (cold adds `excursion` to `normal`) | Covered by ruling 7's intent (non-empty proof); fine |
| Lane B L-B2 (inline copy of the replay `chain` fixture body) | Covered (test mechanics) |
| Lane B L-B3 (W1 via the service layer, no HTTP) | Covered by ruling 7 ("public W1 ... read bodies" through the service); see L5 |
| Not raised by either lane: alias on selected facts | **Needs Architect ruling** (M2) |
| Not raised by either lane: withdrawn EV Finding without a pinnable session | **Needs Architect ruling** (M3.1) |
| Not raised by either lane: pending block on historical reads | **Needs Architect ruling** (M3.2) |

## Checks run (by this reviewer, at `28906b40`, private `w301r_test`, dropped afterwards)
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- pytest run 1 (`test_w301_provenance_dto_postgres`, `test_s4_power_demo_case_postgres`,
  `test_s4_finding_read_postgres`, `test_s4_finding_evidence_history_postgres`, `test_s4_finding_api`,
  `test_s4_consequence_history_postgres`, `test_s4_consequence_read`, `test_s5_overview_postgres`,
  `test_s6_action_records_postgres`): **53 passed**, 0 failed or skipped, 647 s.
- pytest run 2 (`test_w203_cold_reads_postgres`, `test_w204_cold_reads`, `test_w206_ev_reads_postgres`,
  `test_w207_ev_site_reads_postgres`, `test_w207_ev_money_postgres`): **76 passed**, 0 failed or skipped, 2130 s.
- `npx.cmd tsc --noEmit`: clean. `npx.cmd vitest run` on `sourceProvenance`, `coldRoutes` and `evAssessmentRoutes`:
  3 files, 85 passed. On this worktree, vitest did run under the sandbox.
- Not run: the full backend and frontend suites, the production build and layout evidence (the slice changes no
  layout).

## Residual risk not in the packet
- The W1 `detail` duplicates the nine resolver keys on every W1 Finding and consequence block. Payload growth on
  history pages is unmeasured.
- Per-row EV Finding and money citation queries run N+1 on the snapshot connection. That is fine at W2 sizes, and
  is worth watching in the estate commit, which reads these per Site before paging.

## Re-review r1 (head `4a9309ff`, range `1ceb1299..4a9309ff`): ACCEPT
Closed as ruled: M1 (labels `Selected source basis (SHA-256)` / `Finding source basis (SHA-256)`, read from selected sibling / row block, `Not recorded` only when null), M2 (selected-source helper, backend `claim_rules.source_class` from selected block), M3.1 (`transition` selected, two-ID selection only for NO_LONGER_SUPPORTED lifecycle+transition with a non-null session and zero matches; all else still refuses), M3.2 (`historical` computed before the job query on cold and EV), L1 (test), L3 (mapping in handoff), L4 (partial patch no longer tracked). L2/L5 backlog as ruled.
Ran on private `w301rr_test` (dropped): 6 new/changed backend tests (w203 x2, w206 x3, w207 x1) passed, 203 s. Full files, frontend vitest, tsc and guards not rerun; relying on the implementer's reported runs.
Fixer readings:
1. M3.2 `:k` = explicit `known_at` only: (a) mechanical. Ruling text said `:k = known`, but on a default read `known` is the watermark and any real pending job is created after it, so that literal form would hide every pending block. A default read is not historical by definition (historical needs an explicit `known_at < watermark`), and an explicit `known_at` is filtered by both the historical gate and `created_at <= :k`. No historical case is left unfiltered. Suggest the Architect note the literal text in the ruling for the record (no code change).
2. `SET LOCAL session_replication_role = replica` in tests: (a) acceptable. Ruling L1 required updating the stored class; the trigger makes that impossible otherwise. It is scoped to one transaction on a private DB, restored in `finally` and asserted restored. Same technique is used in `pg_harness`, w204 and s4 history fixtures; W2-07 L5 concerned downgrade probes, which prove migration behaviour and are not involved here.
3. Existing EV historical test extended rather than duplicated: (a). 4. Named frontend tests live in `evSiteMoneyRoutes.test.tsx` and Finding strip falls back to the row block: (a), consistent with the rulings (row block authority).
No High or Medium findings.
