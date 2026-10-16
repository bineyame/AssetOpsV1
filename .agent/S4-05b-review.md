# S4-05b phase-2 and slice review - registered producers, stored source on reads, money gate, walkthrough

Reviewer: fresh independent Claude reviewer (did not author). Revision reviewed: `5324e24d`
(`task/S4-05b-producers-reads-walkthrough` head), phase-2 diff `e147b06d..5324e24d` excluding `.agent`.
Worktree `AssetOpsV1-review5`; `assetops_backend.__file__` resolves to this worktree.

## Verdict: ACCEPT

No High or Medium findings. Four Lows below; none blocks. Per owner direction no wording findings are raised;
the four labels match `D-2026-10-16-s405b-label` and final wording is the owner's W1 checkpoint. Merge still waits
for the owner walkthrough record.

## Focus answers

- **Money gate, fail closed.** `evidence/provenance_read.py` `source_gate` permits current money only for
  `AUTHORED_DEMONSTRATION` / `REGISTERED_SIMULATION`; a missing block is UNKNOWN. Consequence read
  (`financials/consequence_read.py:227-241`) gates `presented_as_current` on the head's union block in addition to
  CURRENT and LR `ELIGIBLE`, and `withheld_reasons()` names every failed gate at once. Finding Financials bridge
  (`finding_api.py:373-400`) adds a `MIXED_OR_UNKNOWN_SOURCE` state for CURRENT + ELIGIBLE + refused source, appends
  the source reason beside LR states and other currentness states, and treats a missing `source_gate` as refused.
  S5 Overview (`site_overview/read.py:302-336`) requires both the consequence gate and the stored block, and adds
  `MIXED_OR_UNKNOWN_SOURCE` to `limitation` beside a higher-precedence state. Covered by bridge, `withheld_reasons`,
  S5 unit and Postgres tests (unwired resolver on a published P02 gives `MIXED_OR_UNKNOWN_SOURCE`).
- **Historical amounts.** Every history row and a pinned non-head row keeps its own `source_provenance`; a pinned
  row is never `presented_as_current`; the UI shows a per-version label (`FindingConsequence.tsx:598,671-674`).
- **Heuristic retired.** `demonstration_label.py` is deleted; no reference to `demonstration_label` /
  `demonstration_case` remains in backend, frontend or tools (one docstring mention). Overview reads the stored
  block from the consequence read; recommendation reads the selected revision; Action detail reads
  `origin_finding_revision_id` (`actions/service.py:214,581`). Unwired or raising resolver gives UNKNOWN with
  `PROVENANCE_NOT_WIRED` / `PROVENANCE_UNREADABLE`, shown as `Source unverified`.
- **Phase-1 L1 fixed.** `runs/registered_release.py:49-54` refuses with `SOURCE_PUBLICATION_REFUSED` /
  `STAGE_NOT_ATTESTABLE` for any Stage status outside `STAGED|NOT_STAGED|HELD`. Per
  `contracts/assetops_contracts/gateway_stage.py:122-132`, any unsealed envelope makes the status
  `SEALING_PENDING|SEALING_REFUSED`, so a partly sealed Stage is refused whole; `NOT_STAGED`/`HELD` have no
  envelopes, so nothing can be released unpublished. Host test proves nothing is released.
- **Phase-1 L2 fixed.** `sourceState` maps any state outside `SOURCE_WORDS` to UNKNOWN; tested with
  `ATTESTED_REAL_SOURCE`.
- **Labels and visibility.** `SOURCE_WORDS` equals the ruling table verbatim; label and statement sit outside the
  closed disclosure, are asserted visible and not inside `<details>`; layout evidence claims 178/178 at 1440/390
  (not rerun by me; script exists at `tools/s405-provenance-evidence.mjs`).
- **Vocabulary exemption.** `frontend/src/test/productVocabulary.ts` is unchanged. The only exemption used is the
  existing `data-vocabulary-exempt="source-reference"`, applied only to `<code>` wrapping server identifiers
  (revision, publication, fixture ID/version, run, evidence IDs) in `IdList`; titles, reasons, method text and
  labels are scanned. Not a backdoor: no authored prose sits inside the exempt element. Fixture IDs do contain
  `demo` (e.g. `s4-power-demo-cases-v1`), which is exactly the source-identifier purpose.
- **Install gate.** `tools/schedule-install-gate.py:35` prepends `I-attested-real-source-provenance` for `pilot`
  regardless of `real_pilot_requires`; demo/walkthrough/private unchanged; tests cover open, missing and resolved,
  and S4-05 resolved alone leaves pilot CLOSED.
- **S5-01 amendment** (`tasks/S5-01-site-overview.md:34,39,52`) is coherent with shared contract item 5: stored
  exact-revision trigger, all classes, regardless of spec readability, consequence-only power, simultaneous reasons,
  source does not influence Finding choice, walkthrough expectations updated. See L3 for one inaccurate pointer.
- **S6 contract fixture.** `test_s6_action_records_postgres::test_d_action_records_walkthrough_and_contract`
  passes against it; it has no `demonstration` key and 11 `source_provenance` blocks, all UNKNOWN /
  `NO_POSITIVE_BINDING` (the real resolver ran, not `PROVENANCE_NOT_WIRED`).
- **S6-02a overlap.** `git merge-tree HEAD task/S6-02a-verification-core` reports content conflicts in
  `actions/service.py`, `actions/composition.py`, `backend/tests/fixtures/s6_action_api_contract.json`,
  `frontend/src/shell/__tests__/s5SiteWindowOverview.test.tsx` and `.ai/CODE_STATE.md`. Semantically, S6-02a's
  branch still imports `demonstration_label` in `actions/service.py:33,314,679` (and its base copies in
  `finding_api.py`/`site_overview/read.py`). Whichever merges second must: keep `source=` and S6-02a's
  `publish=`/new kwargs in `build_action_service`; drop every `demonstration` field S6-02a adds or keeps, including
  any new verification read that labels source; regenerate the contract fixture rather than hand-merge it; and
  rerun `test_s6_*` plus `rg demonstration_` to prove the heuristic did not return. If S6-02a merges second, the
  deleted module makes its import fail loudly, which is the safe direction.
- **Walkthrough reachability.** `.agent/S4-05b-owner-walkthrough.md` is plain, two windows, copy-paste commands,
  expected labels per case, and a clean-up step. D1 (`serve --case owner|old|mixed`, separate private DBs for
  old/mixed) is declared, guarded (`assetops_s405*`, `var/s405*`, rejects `_test`), and the web server stays up while
  the API switches. Acceptable: the old case proves "same Site/day confers nothing" for an unbound P01 upload, which
  is what the same-day case was for. See L4 for the pinned worktree path.

## Findings

1. **Low - a missing consequence head raises a spurious `MIXED_OR_UNKNOWN_SOURCE`.**
   `backend/assetops_backend/financials/consequence_read.py:229-236,283` and
   `backend/assetops_backend/site_overview/read.py:304,334-336`. When `head is None` (consequence PENDING), the
   gate is `source_gate(None)`, so `withheld_reasons` and the Overview `limitation` name `MIXED_OR_UNKNOWN_SOURCE`
   beside `CONSEQUENCE_PENDING` even when the selected FindingRevision is authored, while the Overview notice shows
   the Finding block's `Prepared example data`. No amount is ever shown wrongly (fail-closed direction), but a typed
   reason is false and the disclosure contradicts the label. Fix: when there is no head, either omit the source
   gate reason or derive it from the FindingRevision block; add a test for an authored Finding with no consequence.
2. **Low - the "absent list" case of the install-gate test is not absent.**
   `backend/tests/test_s4_schedule_install_gate.py:44` passes `None`, which becomes `()` and is written as
   `"real_pilot_requires": []` by `run()` (`:22-23`). The key-missing path is therefore untested, though
   `registry.get(...) or []` handles it. Fix: let `run()` omit the key when `pilot is None`.
3. **Low - S5-01 amendment names the wrong seam.** `tasks/S5-01-site-overview.md:39` says the Overview reads
   provenance "through the Finding bridge (`finding_api.py` `bridge_consequence`)". The code reads the consequence
   read's `source_provenance` and `currentness.source_gate` directly (`site_overview/read.py:46-49,302-304`), not the
   bridge. Fix: point at `financials/consequence_read.py` `ConsequenceReadService.read`.
4. **Low - owner steps are pinned to the implementer's worktree.** `.agent/S4-05b-owner-walkthrough.md:25,45`
   `cd C:\Users\assef\Bineyame\AssetOpsV1-review2`. That worktree is at `5324e24d` today; if it is moved, reused or
   removed before the owner walks through, the steps break or run another revision. Coordinator note: keep it at
   the reviewed head (or update the path) until the owner record exists.

## Checks run (this reviewer, revision `5324e24d`)

- Focused backend, private `assetops_s405brev2_test` (created, dropped afterwards), `-n 2 --dist loadfile`:
  `test_s4_assumption_read_api`, `test_lr01_money_eligibility_postgres`, `test_s5_overview_read`,
  `test_s5_overview_postgres`, `test_s6_action_store_postgres`, `test_s6_action_records_postgres`,
  `test_s405b_registered_release`, `test_s4_schedule_install_gate`, `test_s4_power_demo_case_postgres`,
  `test_s4_consequence_recompute_postgres`, `test_s4_evidence_consequence_work_postgres`,
  `test_s4_evidence_drain_postgres`, `test_s405_resolver_postgres`, `host/tests/test_registered_gateway_delivery.py`.
  JUnit tests=146, failures=0, errors=0, skipped=0, 364 s. (A first attempt errored at setup only because the base
  DB did not exist yet; rerun after creating it.)
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
  `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0.
- Frontend (`npm.cmd ci` then): `npx.cmd tsc --noEmit` exit 0. `npx.cmd vitest run` on sourceProvenance, siteAction,
  s5SiteWindowOverview, runCommitPanel, siteFinancials, t028Vocabulary: 6 files, 142 passed. (Vitest ran in this
  sandbox; the full `npm.cmd test` and the build were not run.)
- Trial merge with `git merge-tree` against `task/S6-02a-verification-core` (no worktree change).
- Not run: full backend suite (implementer's same-revision-code run at `64c6f6bd`, later commits docs only:
  2408 passed, 0 failed/errored/skipped, 18:50), full `npm.cmd test` (implementer 1588 passed), `check-all.ps1`,
  walkthrough `prepare` and layout evidence (implementer 0 failed checks; 98/98, 40/40, 40/40). These are cited,
  not independently confirmed.

## Residual risk not already named

1. The S6-02a merge (above) is the main integration risk: conflicts are mechanical, but a careless resolution can
   reintroduce the date/spec label on Action reads. The second merger should rerun the S6 Postgres tests and grep.
2. Consequence history still resolves provenance per row (named in the packet); with S6-02a adding Action
   verification reads, any new per-Action provenance call multiplies this. Not measured.
