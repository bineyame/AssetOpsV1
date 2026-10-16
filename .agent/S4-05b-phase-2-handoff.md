# S4-05b phase 2 handoff - PARTIAL (context budget reached)

Branch `task/S4-05b-producers-reads-walkthrough` (worktree `AssetOpsV1-review2`). Environment as in
`.agent/S4-05b-phase-1-brief.md`; focused Postgres DB `assetops_s405b_test`. Phase-1 review cherry-picked
(`bd3ef292`, `.agent/S4-05b-phase-1-review.md`); its L1 and L2 are fixed here, L3 (layout evidence + end-to-end
producer run) is still open and blocking for the phase-2 review.

## Landed (commits after `f5ea7202`)

- `fbdc7066` money gate + labels + Actions + L1/L2:
  - `evidence/provenance_read.py`: `MIXED_OR_UNKNOWN_SOURCE`, `POSITIVE_STATES`, `permits_current_money`,
    `source_gate(block)`.
  - `financials/consequence_read.py` read(): head's union block -> `gate`; `presented_as_current` also needs
    `gate["permits_current_money"]`; `currentness.source_gate` and `currentness.withheld_reasons`
    (`withheld_reasons()` at file end: currentness state+reasons, `MONEY_<state>`, source reason, head non-PRICED
    state, all at once).
  - `finding_api.py` `bridge_consequence`: new state `MIXED_OR_UNKNOWN_SOURCE` (CURRENT + ELIGIBLE + source
    refused; recorded head linked, no amount/quantity), source reason appended to `currentness_reasons` in every
    branch with a row; `source_gate`/`withheld_reasons` on the bridge; REASONS sentence.
  - `site_overview/read.py`: `demonstration_case` gone; `stored_source(body,...)` (consequence block else Finding
    block else UNKNOWN); `provenance_resolved` from the source gate; output `source_provenance`, `source_gate`,
    `withheld_reasons`; `limitation` adds `MIXED_OR_UNKNOWN_SOURCE` beside another state.
  - `actions/service.py`: `source=` callable (composed in `actions/composition.py` from
    `finding_reads.source_provenance`); recommendation reads the selected revision, Action detail the pinned
    `origin_finding_revision_id`; unwired/failing -> UNKNOWN (`PROVENANCE_NOT_WIRED|UNREADABLE`). Field
    `demonstration` replaced by `source_provenance`.
  - `backend/assetops_backend/demonstration_label.py` deleted with its unit tests (no importer left).
  - `runs/registered_release.py`: Stage status outside `{STAGED, NOT_STAGED, HELD}` (e.g. `GATEWAY_UNAVAILABLE`,
    `SEALING_*`) -> `SOURCE_PUBLICATION_REFUSED` `STAGE_NOT_ATTESTABLE` before any registration (L1).
  - Frontend: `sourceProvenance.tsx` labels/statements exactly per D-2026-10-16-s405b-label, unknown state ->
    UNKNOWN (L2), plain disclosure titles + method paragraph, IDs `data-vocabulary-exempt="source-reference"`;
    `FindingConsequence.tsx` (`MIXED_OR_UNKNOWN_SOURCE` gated like LR states, pinned-version notice, per-history
    row `data-consequence-source`); `SiteWindowOverview.tsx` (notice replaces `data-financials-demonstration`);
    `SiteAction.tsx` (Origin panel) and `SiteRecommendation.tsx` notices; client types.
  - Tests: `money_gate_stub.AUTHORED` provenance stub wired where tests exercise basis currentness only;
    `test_s4_assumption_read_api` (bridge source gate, simultaneous reasons, `test_every_failed_money_gate_is_named_at_once`),
    `test_lr01_money_eligibility_postgres` (production composition: published P02 -> authored; resolver unwired ->
    ELIGIBLE+CURRENT PRICED withheld), `test_s5_overview_read` (UNKNOWN/MIXED/absent, positives, UNPRICED+MIXED),
    `test_s6_action_store_postgres` (pinned origin, UNKNOWN, unwired/failing), `test_s405b_registered_release`
    (+2 L1), `host/tests/test_registered_gateway_delivery.py` (`test_an_unreadable_stage_refuses_commit_and_releases_nothing`),
    frontend `sourceProvenance.test.tsx` (labels, L2, a11y visibility, vocabulary scan x4 populated states),
    `siteFinancials` (MIXED/UNKNOWN withheld + vocab), `s5SiteWindowOverview` (MIXED/UNKNOWN + vocab).
- next commit: `tools/schedule-install-gate.py` always requires `I-attested-real-source-provenance` for pilot
  (+ `test_pilot_always_requires_attested_real_source_provenance`); `test_s5_overview_postgres` publishes P02 and
  proves unwired resolver -> `MIXED_OR_UNKNOWN_SOURCE`.
- next commit: `tools/s5_overview_walkthrough.py` and `tools/s402b-fuel-cost-evidence.mjs` read the stored state.

## Resume here (in order)

1. DONE: S6 contract regenerated (`28e81bd7`; fixture grew to ~840 KB because each Action/recommendation response
   carries the full provenance block) and `siteAction.test.tsx` asserts `Source unverified.` on the recommendation.
2. Lab: refusal is rendered generically by `frontend/src/shell/RunCommitPanel.tsx:268-292`; add a
   `runCommitPanel.test.tsx` case for `SOURCE_PUBLICATION_REFUSED` (statement in
   `contracts/assetops_contracts/lab_projection.py:165-169`, "no partial release" visible).
3. S5-01 packet amendment (shared contract item 5; S4-05b merges second): `tasks/completed/S5-01-*.md:39` (or
   wherever S5-01 lives) - replace the `demonstration_case` trigger with the stored exact-revision provenance.
4. `tools/s405_provenance_walkthrough.py prepare|serve|links|drop` per packet phase 2 (DB guard `assetops_s405*`,
   work `var/s405*`, ports 8935/5435, P01+P02 authored, ordinary registered run, same-day unbound, mixed case,
   old-host DB `assetops_s405_old*`). Reuse `tools/s4_finding_cases.py` (`Cases.publish_authored`, `post(fixture=)`)
   and `tools/s402b_power_cases.py`; pattern from `tools/s5_overview_walkthrough.py`. Run it end to end (L3).
5. `.agent/S4-05b-owner-walkthrough.md` (non-developer steps), layout evidence 1440/390
   (`node tools/layout-evidence.mjs`), `tools/check-all.ps1`, registry checker, tsc, `npm.cmd test`, ONE full
   backend suite (brief command, cap 25 min, copy `var/sites/*.yaml` first, remove after), review packet.

## Open risks

- `MoneyInputs.provenance_resolved` default stays `True` (S5 unit tests rely on it); production always passes it.
- Ordinary Findings without publication now show `Source unverified` and no current amount everywhere (intended by
  the contract); any other walkthrough expecting an amount on unpublished data will now show none.
- Action contract fixture grows by a provenance block per Action/recommendation response.

## Checks (this partial)

- Focused Postgres/host (`assetops_s405b_test`, `-n 2 --dist loadfile`, 12 files at `fbdc7066`+): 132 passed,
  1 failed (`test_s6_action_records_postgres`, stale contract, then regenerated); rerun of
  `test_s6_action_records_postgres` + `test_s5_overview_postgres`: 3 passed; contract check alone: 1 passed.
- Non-DB: `test_s4_assumption_read_api`, `test_s5_overview_read`, `test_s405b_registered_release`,
  `test_s4_schedule_install_gate`, host `test_registered_gateway_delivery` all passed.
- Frontend: `npx.cmd tsc --noEmit` clean; affected suites (sourceProvenance 9, siteFinancials 40, siteFinding,
  siteFindingEvidence, s5SiteWindowOverview, siteAction 35, siteFoundationChange, siteRecommendation) passed. An
  earlier `src/sites src/shell` run had one `siteFoundationChange` failure under load that passed on rerun and on
  the base revision (flaky timing, not this change).
- Mutation: `permits_current_money` -> always True: 5 failed in `test_s4_assumption_read_api`/`test_s5_overview_read`;
  reverted with `git checkout --`.
- Not yet run: check-all, registry checker, full `npm.cmd test`, full backend suite, layout evidence, walkthrough.
