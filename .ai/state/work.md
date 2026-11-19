> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 7 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## S6-01a - Action store, controlled application and exact read (in_review)

Branch `task/S6-01a-action-store-read` from main `fd7afd2c`. Packet `archive/agent-history/S6-01a-review-packet.md`; handoffs `archive/agent-history/S6-01a-phase-1-handoff.md`, `archive/agent-history/S6-01a-phase-2-handoff.md`. Authority `D-2026-10-15-s601-action-store-and-ui` (`archive/agent-history/architect-S6-01-answers.md` Q1-Q5, M1-M3).

- Migration `0016_action_store` (down `0013_schedule_state`): `action` (accepted-recommendation snapshot), `action_basis_assessment`/`_evidence`, `action_event`, `action_policy_change`, `action_policy_change_binding`; all append-only (`ledger_append_only`), same-Site composite FKs, `action_code_seq`. Event expected/current Foundation IDs carry same-Site FKs; the change's APPLIED event must be its own Action's (`action_event_action_unique`).
- `backend/assetops_backend/actions/`: `reserve_trial.py` (pure `reserve-trial-1`), `lifecycle.py` (transition table, reducer, selectors, `SYSTEM_DEMO`), `capability.py` (grants v2: tenant ID + Site ID + command + fixture record Finding IDs), `service.py` (`ActionService`), `composition.py` (`foundation_publish(registry)` maps S1 refusals to Action failure codes), adapter `adapters/postgres_action_store.py` (ninth writer, INSERT only).
- Apply: the Action adapter opens the transaction, locks the Action row `FOR UPDATE`, returns a stored event for the same key (`REPLAY`) or `ALREADY_APPLIED`, then calls the S1 publish on its own connection: `FoundationService.publish_battery_reserve(..., expected_revision_id, expected_value, caller=CallerTransaction(connection, then, recorded_at))` -> `PostgresFoundationStore.publish_configuration(..., connection=, then=)` (Site lock, expected covering revision, no-change, expected reserve; `written_ids(plan)` to `then`). `then` inserts the change, binding rows and APPLIED; one commit. `ApplyFailed` rolls back, then FAILED is appended in its own transaction (existing event returned on key collision). Without `caller`, S1 publish is unchanged.
- Routes (`action_api.py`, wired `main.py` with `registry=`): recommendation, accept, apply, observations, Action and events reads (`event_id` | `recorded_at`, both = 422), `GET /api/sites/{code}/foundation/changes/{change_id}`. Refusal order: access, Site 404, Finding/Action 404, fixture-record capability 403, body 422, revision/expected-Foundation 404, domain.
- Action read adds `change` (only when APPLIED is inside the selected prefix), `application_basis` (read-time covering Foundation), `demonstration` (`demonstration_case` on the origin episode); recommendation adds `demonstration` and a `money_consequence` link to the exact FindingRevision's S4 consequence (no number).
- `D-action-records` v1: `backend/tests/s6_action_records.py` (loader, `fixture_grants`, `normalise`), committed contract `backend/tests/fixtures/s6_action_api_contract.json` (manifest IDs `recommendation:1#a`, `action-overview:1#a`, `action-execution:1#a`, `action-history:1#a`, `changes:1#a`), test `test_s6_action_records_postgres.py` (rebuild + normalised equality; `ASSETOPS_WRITE_S6_CONTRACT=1` regenerates, `ASSETOPS_S6_WALKTHROUGH_OUT=<file>` dumps rows).
- Rule 8 (`tools/checks/configuration-persistence.ps1`): ninth writer registered; INSERT-only into the six Action tables; Action-table writes refused from every other module.
- Reopen (`D-2026-10-15-s601-reopen`): the recommendation read carries `prior_actions.items` (every Action on the canonical Finding with its own origin revision, application/outcome state, link) and `prior_action_block`; an unresolved earlier `reserve-trial-1` Action (PENDING or APPLIED; nothing releases it until S6-02) sets `state=PRIOR_ACTION_UNRESOLVED`, `proposal=null`, Accept capability false, live result in `live_status`. Accept refuses 409 `PRIOR_ACTION_UNRESOLVED`, rechecked in `PostgresActionStore.accept(..., guard=)` under an advisory lock per (Site, Finding, asset, field, rule).
- Open: migration must be re-chained if LR-01 (`0014`/`0015`) merges first (head pins at `test_s1_bindings_postgres.py:118`, `test_s2_evidence_ledger_postgres.py:445`, `test_s4_evidence_consequence_work_postgres.py:516,539`). No runtime grants file is generated for a dev server: the loader builds it per run (`fixture_grants`). `application_basis` is read-time; an apply effective in a recorded future period must name that period's revision. The rule picks the lowest usable SOC per segment (stricter than the ruling). S6-01b UI, S6-02 verification and S6-03 Site ActionIndex not built.

## S6-01b - Action, recommendation and change surfaces (in_review)

Branch `task/S6-01b-action-ui`, stacked on unmerged S6-01a `c341599b`; no backend change. Packet `archive/agent-history/S6-01b-review-packet.md`; handoffs `archive/agent-history/S6-01b-phase-1-handoff.md`, `archive/agent-history/S6-01b-phase-2-handoff.md`; owner steps `archive/agent-history/S6-01b-owner-walkthrough.md`.

- Client `frontend/src/sites/actionClient.ts`: recommendation, Action, events and change reads, accept and apply POSTs. Every refusal is a typed `Refusal`. `system_demo_capability` is optional; when it is absent or `allowed:false` the screens are read-only.
- Shared words `sites/actionPresentation.tsx`:
  - `granted()` requires `allowed === true` and the exact command;
  - `TrialLimitation` carries plain copy, because the server's text uses a banned word;
  - `Ref` is the exact-ID element, exempt from the vocabulary scan;
  - `RefusalPanel` and `CommandRefusal`.
- Recommendation `sites/SiteRecommendation.tsx`. It is a Finding child view `recommendation` (`operatorSiteRoutes.ts` `FINDING_CHILD_VIEWS`). Finding "What to do next" links to it at the exact version.
- Reopen round (`D-2026-10-15-s601-reopen`): `SiteRecommendation.tsx` lists `prior_actions.items` ("Actions on this Finding", own origin version, never relabelled). `state=PRIOR_ACTION_UNRESOLVED` (from `state`, not block presence) shows the notice naming/linking the blocking Action, the live recomputation as a separate reason, and a disabled Accept with the stated reason; a 409 `PRIOR_ACTION_UNRESOLVED` on accept is reported likewise. Apply is disabled while the effective-time field is cleared; failure codes in the change page list do not wrap. Open: S6-02 must add the resolved/closed transition that releases the hold.
- Action root `sites/SiteAction.tsx` + `SiteActionFrame` (`shell/SiteAnalyticsFrames.tsx`).
  - Overview, Application (`/execution`) and History. The selector `event_id` | `recorded_at` is carried in every section link.
  - 404 `ACTION_EVENT_NOT_FOUND` reads "Selected event not found" and links the latest record (phase-1 review M1).
  - An untouched `effective_from` default is re-derived at click: next UTC midnight after max(read time, now) (L1).
  - With no `application_basis.current_foundation_revision_id`, Apply is not offered and the reason is stated (L3).
- Foundation change `sites/SiteFoundationChange.tsx` + `SiteFoundationChangeFrame`. It is the deep route `/sites/{site}/foundation/changes/{change_id}` (`SITE_FOUNDATION_CHANGE_ROUTE_PATH`).
  - Content: old/new reserve, unit, asset, effective and recorded times, versions by role and origin, signal assignment set IDs, Action and application-event links, pending outcome, and the Action's FAILED attempts (a second read).
  - Bare `/foundation/changes` is `SiteFoundationChangesFrame`, an unavailable state with a link back.
  - Both are static segments, so they outrank `:foundationView`. `FOUNDATION_SUBTABS` is unchanged.
- Styles: `ui/primitives.css` end, all under `.app-frame--operator`. Pairs go side by side from 1100px. Refs wrap, except inside dense tables, which scroll in their own scroller.
- Tests:
  - `sites/__tests__/siteAction.test.tsx` (30) and `siteFoundationChange.test.tsx` (8, mounted through `App`) load `backend/tests/fixtures/s6_action_api_contract.json`. Derived bodies are listed in the test headers.
  - `siteFinding.test.tsx` adds the no-recommendation-link case.
- Tools:
  - `tools/s601b_action_walkthrough.py` (`prepare|links|serve|drop`). It uses DB `assetops_s601b*` (never `_test`), work folder `var/s601b*`, API 8961 and web 5461. It runs `s6_action_records.build` into the private DB and writes the scoped `ASSETOPS_ACTION_DEMO_GRANTS` document.
  - `tools/s601b-action-evidence.mjs` (CDP 9461): 56 claims plus `comparison.md`.
- Open:
  - The Recommendation for a newer FindingRevision does not mention an Action accepted on an earlier one. This is S6-01a server behaviour, recorded for the owner.
  - The served walkthrough uses the real clock against fixture-clock records.
  - There is no OBSERVED command control.
  - S6-02 owns Plan, Evidence and Verification, the change index and effect verdicts.
## S6-02a - frozen verification, evaluator and exact read (phases 1-2 built, slice review pending)

Branch `task/S6-02a-verification-core` (main `e39a3c20` merged in; unmerged). Packet `archive/agent-history/S6-02a-review-packet.md`; handoffs `archive/agent-history/S6-02a-phase-1-handoff.md`, `archive/agent-history/S6-02a-phase-2-handoff.md`. Authority `D-2026-10-16-s6-verification`, `-s602-questions`, `-s602a-cutoff`.

- Migration `0019_verification_core`: insert-only plan, later selection binding (now with `idempotency_key`/`payload_sha256`), evaluation request, outcome, metric; `action_event` RESOLVED/RESOLUTION_WITHDRAWN only via the evaluator job (SYSTEM_JOB). Ninth writer only; rule 8 entries literal.
- Rules `actions/verification_rules.py`: slots/coverage/bands/target plus `decide` (VERIFIED/INEFFECTIVE/INCONCLUSIVE, unknown overrides known failure) and `source_pair` (per window, never the union). Timestamps `+00:00`.
- Service `actions/verification.py`: freeze (F1 baseline revision = change's split/superseded; F2 every baseline day S3 CURRENT; F3 S2 acceptance fence in `freeze_plan`), binding (after `later_end`, head plan, CURRENT, idempotent key), `evaluate` (one trial-locked transaction: request, outcome+metrics, RESOLVED/WITHDRAWN), `current_state` (late evidence, moved/non-current S3 or S4 day, changed covering Foundation -> REASSESSMENT_PENDING), `outcome`, `history`, `summary`.
- Ports: `VerificationPorts(day_status, provenance)` wired by `actions/composition.verification_ports` (S3 `DispatchReadService.window` + S4 `match_state`; S4-05a resolver). Missing port fails closed.
- Holds `actions/service.py`: `is_unresolved` from latest resolution; `PRIOR_TRIAL_GUARDRAIL_FAILED`; `reassessment_overlaps` (R1: only the withdrawal's named late evidence; window `[max(closure, evidence accepted), withdrawal)`) -> `PRIOR_TRIAL_REASSESSMENT_OVERLAP`. Same codes in accept guard and Recommendation.
- Routes: POST `.../verification/evaluations`; GET `.../verification/outcome`, `.../verification/history`; Action, Change and Recommendation reads carry `verification`.
- Fixtures: `backend/tests/fixtures/s6_verification_api_contract.json` (TEST-SCOPED complete windows over a real roles-2 Site; shape check), `s6_action_api_contract.json` regenerated (additive). Replay `backend/conversions/d-verification-window-v1.json` + `host/tests/test_s6_verification_replay.py`.
- Open: the replay is complete (12/12 slots, REGISTERED_SIMULATION pair PASS) but settles INCONCLUSIVE: the shipped mini-grid generator ignores the reserve, so no VERIFIED Lab path exists (Architect). Registered scenario/profile lineage is not centrally observable (source pair checks class, fixtures or distinct run digests only). Change read keeps its apply-time `outcome: PENDING` beside `verification`. Late-evidence race between the evaluator's read and its commit is narrow, not closed. Registry nodes stay `open` until review.

## S6-02b - Action verification surfaces (phases 1-2 built, in_review)

Branch `task/S6-02b-verification-ui` (from main `cdb09767`; unmerged; owner walkthrough required). Packet `archive/agent-history/S6-02b-review-packet.md`; handoffs `archive/agent-history/S6-02b-phase-1-handoff.md`, `archive/agent-history/S6-02b-phase-2-handoff.md`. Authority `D-2026-10-16-s6-verification`, `-s602-questions`, `-s602a-replay`, `-s602a-holds`.

- Simulator: `mini-grid` v5 (`packs/mini_grid.py` `decide_v5`, `START_HEADROOM_OVER_RESERVE = 5`) starts the generator at min(Site start threshold, reserve in effect + 5); v1-v4 unchanged. Registered in `runs/profiles.py`, `host/execution_adapter.py`. Scenario `kobo-mini-grid-reserve-trial` v1 (fingerprint pinned).
- Replay: `backend/conversions/d-verification-window-v2.json` (windows predeclared) reaches VERIFIED through gateway/S2/S3/S4 and the Action API; `host/tests/test_s6_verification_replay.py` parametrized v1 (INCONCLUSIVE) and v2.
- Frontend: Action child views `plan`, `evidence`, `verification` (`sites/SiteActionVerification.tsx`, `verificationClient.ts`, `verificationWords.ts`); selectors `plan_revision_id`, `outcome_id`, `event_id`, `recorded_at` carried by `SiteActionFrame` section links; explicit selection = Historical with separate current state; typed `VERIFICATION_SELECTOR_CONFLICT`; Recommendation/Change panels in `recommendationVerification.tsx`; Change and Overview read the `verification` block (F5).
- Tools: `tools/s602b_verification_walkthrough.py` (replay DB + one DB per test-scoped case; `serve --case`; `capture` starts APIs itself), `tools/s602b_test_scoped_cases.py` (build + pinned-clock wrapper reusing the evaluator builders' fakes), `tools/s602b-verification-evidence.mjs` (`ASSETOPS_S602B_PART`), `tools/layout-evidence.mjs` mode `ASSETOPS_LAYOUT_S602B_ACTION`.
- Open: `I-sim-verification-cases`, `D-verification-window` stay open (non-pass variants are test-scoped, not Lab runs); served REASSESSMENT_PENDING proven only in fixture tests; inconclusive case has no data-carried test-scoped label; mock-fidelity copy pass at W1 conclusion; `siteFoundationChange.test.tsx` h1 wait is load-sensitive in the full parallel run.
## S6-03 - Site Work Action list (phases 1-2 built, in_review)

Branch `task/S6-03-site-work-list` (base main `cdb09767`, unmerged); packet `archive/agent-history/S6-03-review-packet.md`; owner steps `archive/agent-history/S6-03-owner-walkthrough.md`. No migration (head stays `0019_verification_core`); no new SQL writer.

- Store: `PostgresActionStore.site_window(tenant, site, start, end)` (`actions/adapters/postgres_action_store.py`) reads every Action created in `[start,end)` and all their events in one REPEATABLE READ, READ ONLY snapshot (SELECT only).
- Read: `actions/site_index.py` `ActionIndexService.read` + `parse_request` (UTC, `from<to`, <=31 days, limit 1-100 default 25, opaque base64 cursor). Latest event by `(recorded_at,id)`; state = `actions.lifecycle.reduce` (same as detail); links via `actions/service.py` `selected_action_links` (module function extracted from `ActionService._links`; detail unchanged). Fence = max created, max event recorded, Action count, event count (+ token `sai1-...`); cursor binds tenant/Site/window/fence/last key. Refusals: 422 `WINDOW_REQUIRED|INVALID_WINDOW|INVALID_LIMIT|INVALID_CURSOR`, 409 `ACTION_INDEX_BASIS_CHANGED` (`SCOPE_CHANGED|FENCE_CHANGED`), 409 `ACTION_INDEX_INCONSISTENT` (event without Action, Action without any ACCEPTED event), 503 `ACTION_STORE_UNAVAILABLE`; all carry `rows: null, total_count: null`.
- Route: `action_index_api.py` `GET /api/sites/{code}/action-index?from=&to=&limit=&cursor=` (401/403 -> 404 -> 503 -> 422 -> read); composed in `main.py` over the Action service's store and clock. No Performance gate (Action detail has none).
- Fixture: `s6_action_records.build(..., second_created_after=)` (default keeps the committed S6-01a contract); `backend/tests/fixtures/s6_site_action_index_contract.json` (regenerate `ASSETOPS_WRITE_S603_CONTRACT=1`; each run checks field structure).
- Tests: `test_s6_site_action_index.py` (no DB), `test_s6_site_action_index_postgres.py` (D-action-records rows, paging, fence incl. older-stamped event, isolation, zero, refusals, same-fence detail parity; S6-02a RESOLVED/RESOLUTION_WITHDRAWN rows).
- UI: route `/sites/:siteId/work` (`SITE_WORK_ROUTE_PATH`, `siteWorkHref`), Work tab capability true, `SiteWorkFrame` (SiteAnalyticsFrames.tsx) with one "Actions" sub-tab; `sites/SiteWorkActions.tsx` + `sites/actionIndexClient.ts`; choose-window state reads nothing; IDs/fence in the "What this list is based on" disclosure. Tests `sites/__tests__/siteWorkActions.test.tsx`; tab expectations updated in `operatorSiteTabs.test.tsx`, `overflowContainment.test.tsx`, `tools/layout-evidence.mjs`.
- Walkthrough: `tools/s603_site_work_walkthrough.py prepare|serve|attest|drop` (`assetops_s603_owner*`, `var/s603_owner*`, API 8963/web 5463); browser claims `tools/s603-site-work-evidence.mjs`.
- Open: registry `I-site-action-index-read`/`I-sitework-ui`/`I-S6-03`/`sitework:1#a` stay open until review; Incidents/Maintenance tabs not rendered; owner/due/priority absent; plain-language copy for the W1-conclusion task; whole-window load (no SQL paging) is fine at W1 sizes.
## post-W6 W6-global-Work - global work list/WR D3 fixes and caps fix round (built, in_review)

Branch `task/post-W6-W6-global` (from main `821ad6bf`). Rulings `archive/agent-history/post-W6-W6-rulings.md` (Q1-Q21) and `archive/agent-history/post-W6-W6-caps-rulings.md` (1-5). Packet `archive/agent-history/post-W6-W6-packet.md`; handoff `archive/agent-history/post-W6-W6-handoff.md`.

- Backend (`fe52c862`): `site_domain` on global list rows and detail `selected`; `links.site` via `estate/evidence_money.site_home_href`; incident `linked_requests` [{label, href}] with IDs in the basis; Site incidents/maintenance fallbacks carry `known_at` only for an explicit cutoff; global Action labels use stored `ACT-` codes. Files `work/{global_index,global_detail,operational_index}.py`, `work/adapters/postgres_global_read.py`; tests `test_w601{a,b,c,e}`.
- Frontend (`5685abad`): R352-R372 D3s across `frontend/src/work/*`, R371 route `/maintenance/requests/:caseId/*`, guard rule in `tools/checks/navigation-truthfulness.ps1`.
- Caps fix round: `work/CellDisclosure.tsx` (two-line preview; visible "Show full"/"Show less" native button with `aria-expanded`/`aria-controls` and a "Show full {column} for {row}" name, overlaid at the end of line 2; shown only when the value overflows, re-measured by ResizeObserver and MutationObserver). Used for Incident Site/Severity/Owner/Findings, Corrective Work request links/Asset-site/Owner, Preventive Asset-site/Trigger/Last done/Next due/What it proves/correction, Operational Record/correction/Type/Site/By/Feeds. CSS `.cell-disclosure*`, `.global-work-clamp--two` in `work/globalWork.css`.
- R356: Operational records Feeds 125 px (fixed sum 1085, fits the 1090 px client width beside the inner vertical scrollbar); 390 px inner table minimum 1085.
- Tests: `work/__tests__/cellDisclosure.test.tsx`, `cellDisclosureStub.ts` (jsdom box-size and ResizeObserver stubs), page tests' "caps ruling 4" blocks.
- Evidence: `.agent/post-W6-W6-evidence/q15b/` (cap probe at the final SHA), `b18r/`, `b19r/` (recaptures), earlier `b18/`, `b19/`, `q15/`.
- Open: VERIFICATION_WINDOW has no writer (capture gap); cold/EV preventive and operational rows, one list with all three domains, and pending/stale global states have no producer; registry chain Q19 nodes remain open (see packet); the other 3-line title/body clamps keep their existing "Full ... text" disclosures (not changed by ruling 4).

## LINK-LINEAGE - the board links an Action across basis-only Finding revisions (built, in_review)
Branch `task/LINK-LINEAGE-board-action` (from main 15eed62c8). Sheet `AssetOpsV1-plan2/specs/LINK-LINEAGE/spec.md`;
decision `D-2026-10-31-board-action-refresh-lineage`; packet `archive/agent-history/LINK-LINEAGE-packet.md`.
- `site_outcomes/board.py`: pure `refresh_chain(revisions, origin_id, shown_id)` (sheet §2; reads only revisions up to
  the shown one) and `BASIS_REFRESHED`; `FindingFact.refreshed_from: tuple[str, ...] = ()` (last field);
  `assemble`'s join is `linked_actions` (exact revision or `origin_revision_id in f.refreshed_from`), used only by the
  applied signal and Must-not-harm. Earlier lists keep their `origin_finding_id` join.
- `site_outcomes/mini.py`: `MiniPorts.finding_history` (default `lambda f, r: None`) and `_lineage` after `_actions`:
  one `finding_history` read per Finding, only when a non-domain Action points at another revision of it; a raise is a
  `failed` port (PARTIAL), None links nothing. Cold/EV unchanged (domain Actions only, never joined).
- `site_outcomes/read.py`: `BoardServices.finding_reads` and the `finding_history` port (finding-index gate, then
  `FindingReadService.history` paged at 500 through `jsonable_encoder`); `composition.py`/`main.py` pass the app's
  `finding_reads`.
- Tests: `test_link_lineage.py` (P1-P3, N1-N11, B1-B3, N6), `test_out_b2_mini.py` M1-M6b (M6 crosses the real
  `FindingReadService.history` and the B4 port), `test_out_b4_main_binding.py` (wiring), b4/e4 Postgres pins compute
  the rule inline from the history route (`_expected_link`).
- Open: estate Finding->Action join stays exact (C5); R552 stays open until DEMO-SPARSE CO-1 passes on the combined
  dataset (DEMO-A edits `tools/demo_combined_finish.py` co1 after this merges).
