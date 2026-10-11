# PRE-S3-03 review packet — delivery checker and next-work report

Task: `tasks/PRE-S3-03-delivery-checker-report.md` (USER_REVIEW_REQUIRED: false). Branch `plan/pre-S3-startup`, as the coordinator directed (the packet names `task/pre-S3-delivery-checker-report`). Commits: `04122ae`, `c62ff9e`, `147fc45`, `663bde2`.

## Outcome

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs --next-work [--json] [--out f]` publishes a deterministic report: raw ready-now, closure-unlock, technical and V-01 visual reach, d with path proof, D/B/P/R/E, score, eligible screens and blocked reasons for every candidate with a reviewed path. `--verify-report f` refuses (exit 3) when any input changed since generation. A refused report also exits 3.
- **Real report on the current registry: REFUSED, fail closed, no task selected.** 37 of the 51 approved core panels lack a reviewed claim-portion path: `evidence-analysis:2` and every S3–S7 core panel, because their paths still name proposed `R-*/UI-*/D-*` IDs. Fingerprints are `registry=cfeda7377485a4cd queue=7a51dc0f7ea2fd18 packet_status=89f0ac964fc2115b panel_contracts=37fd1252dfc006b5 manifest=468bd0cf06b26749 owner_input=f902d15082e24067`. The run was made from a clean `git worktree` at `663bde2`. It is identical from the LF working copy, so the fingerprints normalise CRLF.
- `tools/check-all.ps1` is the normal check command. It runs and reports six guards: architecture seams, navigation truthfulness, agent workflow, dependency registry, delivery fixtures and screen ledger. README "Guards" documents it.

## Files materially changed

- `frontend/docs/architecture/delivery_next_work.cjs` (new): the logic in `parseQueue`/`packetMeta`, `validateMapping`, `nextWork`, `decide` and `fingerprints`.
- `frontend/docs/architecture/test_delivery_next_work.cjs` (new): 17 node:test fixtures.
- `check_v69_dependency_registry.cjs`: task discovery goes through `parseQueue`. Mapping, visual-gate and outside-ranking validation now runs on every run. Adds the next-work/verify CLI and replaces the old "pending PRE-S3-03" stub.
- `v69-dependency-registry-pilot.json`:
  - every claim portion now has `id`, `core`, `variant` (bounded/positive/unknown) and `state` (delivered/open/unmapped/excluded); panels have `visual_gate`;
  - new `delivery_plan.visual_gates.V-01` and `outside_ranking`.
  - This commit also carries the Codex Planner's then-uncommitted S3 refinement (A-S3-dispatch resolved, `I-sim-dispatch-cases` requires, S3 panel claim text), kept per coordinator instruction.
- `tools/check-all.ps1` (new) and `README.md`.

## S1/S2 delivered portions {#s1s2-delivered-portions}

The bounded portions below were verified against the code merged on main (no product code has changed since `82ba6cd`). Each is recorded as `state: delivered` with `delivered_by` (resolved nodes), `evidence` (task/review/owner records) and `anchors` in the registry. **No panel is `real`.** All 15 are `partial`, V-01 is pending separately, and delivered nodes give no candidate reach or distance.

| Panel | Delivered bounded portion; anchor | Remaining |
| --- | --- | --- |
| `sites:1` | Persisted Site row in the index. Anchors: `SitesIndex.tsx:134`, `GET /api/sites` (`sites_api.py:247`). | V-01 (the title differs from the mock; "Last analysed" shows `--`). |
| `foundation:1–3` | Selected-period topology, identity/priority and effective reserve/bindings. Anchors: `StoredFoundationViews.tsx:258-316`, `FoundationRevisionPanel.tsx:93-311`, `foundation_api.py:454,490,586`. | `foundation:2#b` operating obligations: unmapped, non-core. V-01. |
| `readiness:1` | Configured roles/bindings and gaps. Anchors: `FoundationBindingsPanel.tsx:90-286`. | Caveat: the scope note still says "No accepted evidence is linked" (`foundation_api.py:295-298`). V-01. |
| `sld:1–2` | Configured SLD with unbound markers, and the parts table. Anchors: `SiteSingleLineDiagram.tsx:748,1067`, `StoredFoundationViews.tsx:320-419`. | V-01. |
| `lab:1–4` | Stored envelope/outbox, truth vs observed, release and central receipt, boundary text. Anchors: `GatewayLedgerView.tsx:219`, `RunFrame.tsx:876-909,1351`, `RunCommitPanel.tsx:65`, `simulator_lab_api.py:2955,2972,3256,3312`. | V-01. |
| `evidence:1–2` | Accepted counts and limits with no conclusion; sources and central contact. Anchors: `LedgerSiteEvidence.tsx:119-623`, `evidence_api.py:372`, `gateway_api.py:93`. | `evidence:1#b` capability: unmapped, non-core. `evidence:2#b` S7 outage/pressure: open, non-core. V-01. |
| `evidence-analysis:1` | Records inspector with configuration and receipt lineage. Anchors: `LedgerSiteEvidence.tsx:704-960`, `evidence_api.py:396,430`. | V-01. |
| `evidence-analysis:2` | The S2 explanation: partial/conflict/outdated notes, analysis status, no conclusion. Anchors: `LedgerSiteEvidence.tsx:212-219,293,555-574`. | `#b` positive claim-limit rule: **core, unmapped**. The panel is not reviewed (Q2). |

`readiness:2#a`/`3#a` are **not** recorded as delivered. They render, but the hardcoded "awaiting credentials, not sending data" text has been stale since S2-02 (Q8).

14 panels are `reviewed_mapping:true`, each with `mapping_review` noting that independent review is pending.

## Acceptance criteria

| Criterion | Status |
| --- | --- |
| Task discovery from `tasks/README.md`: unique ordered rows, packets, layer status | Met. `parseQueue` is shared by the checker and report. Packet `Status` is checked against node status (done ⇔ resolved); a mismatch gives a `queue_mismatch` refusal. |
| 110 allocations, 64 W1 keys/titles, 27/9/22, owner core/value/K=10 | Met (existing checks kept). The report re-validates owner input and fails closed. |
| S1/S2 reconciliation; delivered vs open vs unmapped; V-01 separate; no panel real | Met; see the table above. The `real` status is guarded and requires every portion delivered plus accepted visual gate evidence. |
| Technical readiness from `requires` and AND portion gates; variants separate; typed node errors | Met. All core portions of a panel are combined with AND. Unknown never completes a positive claim. An unknown node gives `unknown_node`. |
| Fingerprints for registry, queue, packet status, contracts, manifest, owner input; stale inputs refuse | Met (`--verify-report`). Proven with a real packet edit: `stale_input: packet_status`. |
| Scoring: B, P with K, inherited max D, R by area, E; XL unscored; delivered gives no reach; V-01 visual-only; each panel counted once | Met; fixtures cover each. |
| Stops before ranking; tie-break; ≤5% stop, 5–10% notice, >10% top, single candidate without notice; `USER_REVIEW_REQUIRED` never cleared | Met in `decide`. Exact 5% and exact 10% boundaries are tested. `user_review_required` is carried on the selection. |
| Fixtures: missing owner value, unmapped panel, proposed-only, stale, ordering-only S6, technical S5 money edge, tie/5/10, XL, one-candidate, mixed S1/S2 panel | Met: 17/17 pass. |
| Normal check path wired; each guard reported; missing tool or failure exits nonzero | Met: `tools/check-all.ps1`. |
| Report from a clean tree | Met: a clean worktree produces the refusal above. |

## Checks run

- `tools/check-all.ps1`: all 6 guards pass. It includes `check-architecture.ps1`, `check-agent-workflow.ps1`, the registry checker, 17/17 fixtures and the ledger (110/88/258).
- Non-vacuity proofs: each mutation was made on committed work and reverted with `git checkout`.
  1. `delivered_by` set to an open node: the Dependency registry guard fails `[delivered_proof]` (exit 1).
  2. A partial panel set to `real`: `[panel_status]`.
  3. `/site-details` added to `frontend/src/sites/siteViewModel.ts`: the Navigation guard fails.
  4. `-Python C:/nope/python.exe`: `missing tool` (exit 1).
  5. The 5% boundary loosened: the fixtures guard fails.
  6. V-01 manifest drift: a visual-gate assignment error.
- Frontend and backend suites were not run. No product code changed: the diff touches only `frontend/docs/architecture/*.cjs`/`.json`, `tools/` and `README.md`. Layout evidence: not applicable.

## Known deviations

- Work is on `plan/pre-S3-startup`, not the packet's branch name, by coordinator instruction.
- Defaults for Q1–Q9 are in `.agent/PRE-S3-03-questions.md`:
  - V-01 effort is unrecorded, so V-01 is blocked `effort`;
  - `evidence-analysis:2` positive is treated as core;
  - any in_review/active packet stops selection globally.
- `delivery_plan.report_input_fingerprints` stays `null`. Reports carry their fingerprints externally, so the registry hash cannot be self-referential.
- The navigation guard runs twice: inside architecture and on its own, so that it is reported by name.

## Residual risk

- The mapping review is self-verification. The 14 `reviewed_mapping:true` rows need independent review before any ranking is authoritative.
- A live ranking requires reviewed S3–S7 paths: real nodes in place of the proposed `R-*/UI-*/D-*` IDs. Until then the report refuses by design.
- The stale Readiness text (Q8) is a truthfulness defect in shipped UI, outside this task's scope.
- `.ai/CODE_STATE.md` S1/S2 headings still read "(in review)" although merged; left unchanged.

## User-review focus

None required (USER_REVIEW_REQUIRED: false). For the reviewer:
- the delivered-portion table above;
- the Q2/Q3/Q8 defaults;
- whether `d = |open AND closure of the panel's core portions| − 1` matches the strategy's distance.

## Fix round 1 (review F1)

- Fix: `delivery_next_work.cjs` visual branch now takes the union of V-01's open prerequisites and the panel's open technical gates (`p.needed`) for `d` and `proof`; `closure_unlock` is true only when `p.needed` is a subset of V-01's prerequisites.
- Fixture: new test `V-01 distance includes the panel open technical gates (review F1)` in `test_delivery_next_work.cjs` (V-01 sized M, `site:1#b/#c` open on `I-S7-01`: d=1, proof `[I-S7-01]`, ready_now=0, closure_unlock=0; plus a subset case where V-01 requires `I-S7-01`: d=1, closure_unlock=1). Before the fix it failed (`actual: 0, expected: 1`); after, 18/18 delivery fixtures pass.
- `tools/check-all.ps1`: all six guards PASS. Live `--next-work` still refuses with `unmapped_approved_panel` (37 approved core panels unmapped), unchanged.
- Carries C1-C5 not worked.

## Carry round (C1, C2, C3, C5; Architect Q9 and "C5 checker fix")

- **C1/Q9:** the 14 `reviewed_mapping:true` S1/S2 rows' `mapping_review.by/evidence` now cite the fresh Claude review (`.agent/PRE-S3-03-review.md`) and F1 re-review (`.agent/PRE-S3-03-fix-rereview.md`); "independent review pending" removed (0 remain). The 37 newly mapped rows stay `reviewed_mapping:false`.
- **C2:** independent verdicts added to delivered-portion `evidence`: S1-02/S1-03 portions (`S1-codex-review`, `S1-02-fix-rereview`, `S1-03-review`, `S1-fix-rereview`, `S1-fix-rereview-2`), `lab:1#a` (`S2-01b-codex-review`, `-fix-rereview`, `-fix-rereview-2`), `lab:2#a`/`lab:4#a` (`S2-01a-codex-review`).
- **C3:** `lab:3#a` boundary now "delivered by I-S2-02"; `R-/UI-capability`, `D-coverage-window` removed from `evidence:1#a` superseded list (live on `#b`); those plus `R-claim-lineage`/`UI-evidence-analysis` removed from `evidence-analysis:2#a` (its `#b` now has real nodes).
- **C5:** `validateMapping` (used by both the report and the registry checker) emits typed `unsupported_enables` for any non-empty `delivery_plan.enables`; empty stays valid. Fixture added; with the guard disabled the suite fails 1 of 19 (non-vacuous), restored to 19/19.
- **Checks:** `tools/check-all.ps1` all 6 guards pass; delivery fixtures 19 pass. Live `--next-work` still REFUSED, sole reason `[unmapped_approved_panel]` 37 approved core panels lack a reviewed claim-portion path (awaiting review of the new mappings).
- Note: the registry/checker edits were swept into commit `75dd4d8` (PRE-S3-04 implementer's commit); this commit adds only this section.
