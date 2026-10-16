# W1 remaining packets - plan review (S6-03, S7-01a/b, S3-02a/b)

Reviewer: fresh independent Claude Reviewer, 2026-10-16. Plan review only (nothing built). Worktree `AssetOpsV1-review5` at `ff798072` (`plan/W1-remaining-packets`); diff `7576ef9d..ff798072`. Authority: `.agent/architect-W1-remaining-answers.md`; `.ai/DECISIONS.md:4162,4164,4166`. Owner direction applied: demo speed; no wording/visual findings; only High/Medium block.

## Verdicts

| Packet | Verdict |
| --- | --- |
| S6-03 `tasks/S6-03-site-work-list.md` | **RETURN** (F1, F2 Medium) |
| S7-01a `tasks/S7-01a-health-read.md` | **ACCEPT** (Lows F6, F7, F8) |
| S7-01b `tasks/S7-01b-health-ui.md` | **RETURN** (F3 Medium) |
| S3-02a `tasks/S3-02a-capability-read.md` | **RETURN** (F4 Medium) |
| S3-02b `tasks/S3-02b-claim-limit-ui.md` | **RETURN** (F5 Medium) |
| Umbrellas S7-01, S3-02 | ACCEPT (no build of their own) |

All five Medium findings are small packet edits (one or two sentences each); none needs a new Architect ruling.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: "Registry valid: 234 nodes, 11 linked pilot panels", exit 0. Registry diff: new `I-S7-01a/b`, `I-S3-02a/b`; `task` fields on `D-edge-health-cases`, `I-source-health-read`, `I-asset-boundary-read`, `I-source-health-ui`, `I-asset-boundary-ui`, `I-capability-read`, `I-claim-limit-read`, `I-evidence-analysis-claim-limit-ui` moved to the a/b parts; `I-S7-01`/`I-S3-02` now require their b part. Consistent with the ruling's registry disposition (`architect-W1-remaining-answers.md:35`).
- `tools/check-agent-workflow.ps1`: "Agent workflow check passed.", exit 0.
- No suites run (per dispatch).

## Code reality (spot-verified)

All cited seams exist at or near the cited lines: `action`/`action_event` tables `0016_action_store.py:46,123` and `action_event_order` index `:169`; `ACTION_COLUMNS`/`EVENT_COLUMNS` `postgres_action_store.py:43-48`; `_finding_actions`/`actions_for_finding` `:186-200`; selection/links `actions/service.py:507-581`; `SITE_ACTION_ROUTE_PATH`/`siteActionHref` `operatorSiteRoutes.ts:230-244`; `SiteAction` `SiteAction.tsx:80`; `finding_index_api.py:3,40`; `gateway_health` `postgres_gateway_access.py:172-194`; `freshness`/`gateway_health_document` `gateway_access.py:289-343`; `GATEWAY_HEALTH_ROUTE` `gateway_api.py:38,93-109`; `gatewayHealthClient.ts:3,68`; `asset` `0001_foundation_identity.py:95`; binding tables `0002_signal_bindings.py:37,65`; `dispatch_read.py` window `:123-166`, revision `:178-202`; `performance_api.py:88-101`; `test_s3_dispatch_read_postgres.py`, `test_s3_dispatch_assessment_postgres.py`; `tools/writer_guard_probes.py`, `tools/check-all.ps1`; `backend/TESTING.md:104,112-125,159` (`-n 2` expected 8-10 min, cap 20). Migration head on main is `0018_finding_match_deferral`; `task/S6-02a-verification-core` adds `0019_verification_core`. New items are marked **New** in every packet. `GatewayDiagnosticsV1` (`contracts/assetops_contracts/gateway_diagnostics.py:83-96`, `DISK_PRESSURES = ("OK","WARN","STOP")` at `:42`, nullable `clock_offset_ms`) can carry all six `D-edge-health-cases` without a schema change. `I-sim-dispatch-cases` already includes two-capability Candidate, missing/poor-quality, contradictory and late cases (registry node, resolved), so the S3-02a fixture is reachable.

Sizing: every packet has exactly two phases. Migration chaining (re-chain after unmerged S6-02a `0019_verification_core`) and rule-8 writer audit with `tools/writer_guard_probes.py` are stated in all five packets. Each packet has exactly one Architect question with a recommendation.

## Findings

### F1 - Medium - S6-03 does not account for S6-02a's new Action event kinds (`tasks/S6-03-site-work-list.md:3,11,13`)

S6-03 says "S6-02 is queue order only", branches from merged main, selects the latest event by `(recorded_at,id)` and forbids an "invented verification result". S6-02a (queued ahead) alters `action_event_kind_check` to add `RESOLVED` and `RESOLUTION_WITHDRAWN` (`task/S6-02a-verification-core:backend/migrations/versions/0019_verification_core.py:212-230`) and extends `actions/lifecycle.py` reduction (`.../actions/service.py:24-25,53-77` on that branch). If S6-02a merges first, the index's "latest selected event" will often be a SYSTEM `RESOLVED`/`RESOLUTION_WITHDRAWN` event; the packet neither says the reduced lifecycle must come from the shared `actions.lifecycle.reduce` (so it absorbs the S6-02a extension) nor whether a persisted RESOLVED event is shown as recorded state (allowed - it is reviewed S6-02a output, not a v6.9 inference) versus hidden (which would misstate the Action). Either merge order can produce a list whose state disagrees with Action detail. Fix: state that lifecycle is reduced by the same `actions.lifecycle` reducer as `service.action`, that list state must equal Action detail at the same fence (already a parity test, `:19`), and that if S6-02a has merged the fixture includes a RESOLVED and a RESOLUTION_WITHDRAWN row shown as recorded events, never as a verdict derived by the list.

### F2 - Medium - S6-03 walkthrough omits the Performance comparison that releases Finding reads (`tasks/S6-03-site-work-list.md:24-26`)

The walkthrough must open "exact detail/event links after reload", and rows carry exact origin Finding/FindingRevision links. S6-01b's walkthrough had to run the Performance comparison in the private tree "so the Finding reads are released" (`tools/s601b_action_walkthrough.py:19,193-198`); without it the FindingRevision destinations read "not released". `prepare` here only "persists positive and assessed-zero windows via normal Action creation/event path" and does not name the builder. Fix: say `prepare` reuses `backend/tests/s6_action_records.py::build` (the `D-action-records` producer) the way `tools/s601b_action_walkthrough.py` does, then runs the Performance comparison, and `attest` fails if the comparison did not pass. (Reuse of the s601b private-tree/marker pattern keeps this cheap.)

### F3 - Medium - S7-01b walkthrough cannot show the case set it promises (`tasks/S7-01b-health-ui.md:20-22`)

`prepare` "publishes the six S7-01a cases ... plus never-received, no-source and configured-but-missing battery" and the owner opens one URL, `/sites/KOBO-001/health`. Three reachability gaps:
1. The read shows only the latest diagnostic per gateway (`postgres_gateway_access.py:184-187`), so six sequential cases on one gateway show one state. The packet must say the cases are spread over distinct registered gateways (or provide a `step <case>` command that advances one gateway through them).
2. `CURRENT` is `received_at` within `2 x cadence` of the real server clock (`gateway_access.py:50,293-297`; default cadence 60 s, `0006_gateway_access.py:39`), so any "current heartbeat" and "old facts freshly received" case published by `prepare` is `STALE` about two minutes later. The walkthrough needs a `heartbeat`/`deliver` command run immediately before the owner looks (or `serve` delivers it), using the authenticated central path.
3. `NO_REGISTERED_SOURCE` and unbound/absent battery cannot exist on KOBO-001 alongside its registered gateway and configured battery; they need a second prepared Site, and the walkthrough must print its URLs.
Fix: name per-case gateways or a step command, a fresh-receipt command, and the second Site with its printed health and asset URLs.

### F4 - Medium - S3-02a does not compose the existing Performance cutover gate (`tasks/S3-02a-capability-read.md:9,16`)

Every existing S3 read goes through `open_scope`, which refuses `409 PERFORMANCE_CUTOVER_CLOSED` until the Performance comparison passes (`backend/assetops_backend/performance_api.py:51-61`); the S4 index takes the same `Gate` (`finding_index_api.py:28`). The S3-02a refusal list is otherwise exhaustive (Site/revision/window/rule/lineage, 401/403/404) but omits the closed gate, so a new module-level route following the packet literally could serve a positive claim ceiling while the cutover is closed - a fail-open around the existing gate. Fix: require the new route to apply the same Performance gate (typed 409, never `UNASSESSED` or empty) and add a closed-gate case to `test_s3_claim_limit_postgres.py`.

### F5 - Medium - S3-02b walkthrough omits gate setup and names no reusable fixture (`tasks/S3-02b-claim-limit-ui.md:18-20`)

1. The Evidence Analysis page and every exact Evidence drill-down go through the S2 Evidence cutover (`409 AWAITING_EVIDENCE_MIGRATION` until `assetops_backend.evidence_migration run` passes, `backend/assetops_backend/evidence_api.py:205-206,237-245`), and the S3 reads need the Performance comparison (F4). This is the same setup step the S5 Overview walkthrough needed (`tools/s5_overview_walkthrough.py:174-177,189`). `prepare` names neither.
2. `prepare` "reuses the reviewed S3-02a public-ingestion fixture", but S3-02a defines only test files, no builder or manifest a tool can call. Either S3-02a names a reusable builder (like `backend/tests/s6_action_records.py::build`) or S3-02b copies the reviewed `assetops_s3cases` producer DB as `tools/s3_dispatch_walkthrough.py:6-10` does.
3. The URL shape `/sites/KOBO-001/evidence/analysis?date=&assessment_revision_id=` does not exist; the current route is `/sites/{id}/evidence?view=analysis&assessment=` (`frontend/src/shell/operatorSiteRoutes.ts:108-122`). The packet hedges ("wrapper must print authoritative route"), so this part alone would be Low.
Fix: add the S2 Evidence comparison and Performance comparison steps to `prepare` (and `attest` fails if either did not pass), name the fixture source, and cite the real route.

### F6 - Low - Identity seam not cited for the two reused route families (`tasks/S7-01a-health-read.md:7,11`; `tasks/S3-02a-capability-read.md:7,9`)

Both packets require 401/403/404, but the routes they tell the implementer to reuse have no request-level access check: `GET /api/sites/{site_id}/gateway-health` takes no `Request` (`gateway_api.py:93-95`) and performance `open_scope(site_code)` has no access callback (`performance_api.py:51`). The existing seam is `finding_api.Access`/`development_access` as used by `finding_index_api.py:28,44-50`. Citing it avoids an implementer extending the unauthenticated S2 route in place (the S7-01a Architect question already points to a new versioned DTO).

### F7 - Low - `STALE_PROJECTION` may have no producer in S7-01a (`tasks/S7-01a-health-read.md:9,17`; `tasks/S7-01b-health-ui.md:15`)

The ruling makes `STALE_PROJECTION` apply "if any derived read lags" (`architect-W1-remaining-answers.md:17`). Site Health reads the central store directly; if no projection is introduced, the required "stale-projection cases" are untestable and invite an invented projection. Say: if the read has no derived projection, record `STALE_PROJECTION` as not applicable and test only the inconsistent-selection refusal.

### F8 - Low - Layout evidence not mentioned for dense lists (`tasks/S6-03-site-work-list.md:20`, `tasks/S7-01b-health-ui.md:15`, `tasks/S3-02b-claim-limit-ui.md:13`)

All three UI packets are dense table/list surfaces at 1440/390, but none asks for `tools/layout-evidence.mjs` or a `not run` record with its precondition, as S6-02b does (`tasks/S6-02b-verification-ui.md:24`). Process only; not a visual finding.

### F9 - Low - S6-03 has no default window for an unparameterised Work entry (`tasks/S6-03-site-work-list.md:13`)

The URL carries `from`/`to`, but entering Site Work from navigation without them is undefined (default window, or a typed "choose a window" state). Not a fail-open (an unbounded window is a refusal), but the implementer will need to choose; one line avoids a review round.

## Architect questions - are the recommendations safe?

1. **S6-03** (cursor fence over all scoped Actions/events, including off-page rows): **safe**, and fails closed. Clarify "scoped" means Site plus selected window (the ruling's "max included" fence), not the whole Site, to avoid spurious invalidation. Residual risk to carry: a max-`recorded_at` fence alone can miss a later-committing event stamped before the fence if `recorded_at` is a transaction-start time; including the included-row and event counts in the fence closes that cheaply.
2. **S7-01a** (versioned fact-age/trust DTO, no in-place mutation of S2 `gateway-health`; registration and diagnostics in one snapshot): **safe**. Note the existing `gateway_health` issues per-gateway statements (`postgres_gateway_access.py:174-187`); the new read must run them in one repeatable-read transaction for the snapshot claim to hold.
3. **S7-01b** (asset route keyed by configured effective asset ID; typed `NOT_CONFIGURED` Site entry when no battery): **safe**. Add that an asset ID outside the effective basis (foreign, or only in a superseded Foundation revision) is a 404/typed refusal, never a healthy or Unknown row for the old asset.
4. **S3-02a** (role coverage as exact interval spans plus duration, one versioned rule ID; never aggregate away a missing/conflicted subspan): **safe**; it is the fail-closed reading of the ruling.
5. **S3-02b** (keep S2 explanation as its own section; render S3 ceiling only when a selected assessment revision is explicit): **safe** (absence is not a claim). The UI should say why no ceiling is shown (`UNASSESSED` or "no assessment selected") rather than omit the section silently, per the ruling's `UNASSESSED` state.

## Residual risk not named in the packets

- S6-03 and S6-02a both touch Action reads; whichever merges second must rerun the Action parity tests against the other's event kinds (F1).
- S7-01b and S3-02b walkthroughs run on the real clock while fixtures use recorded clocks; owner-visible freshness states depend on when commands are run (F3).
