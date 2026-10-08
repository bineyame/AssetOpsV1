# S1-02 — Versioned bindings, Readiness and configured SLD

Status: done
USER_REVIEW_REQUIRED: true
Milestone: S1 Foundation
Depends on: S1-01
Branch: task/S1-02-bindings-readiness
Planner: Codex, 2026-10-07

## Outcome and reason

Kobo's `foundation`, `readiness` and configured `sld` surfaces show registered devices mapped to physical assets and analytic roles. The screen identifies missing required roles before S2 can accept evidence.

## Architect carry-forward

Start from S1-01's Foundation-only Postgres cutover: its eight device sources and pending simulated gateway are registration metadata, not an edge process or evidence authority. One source owns one device report stream beneath one gateway; its signals share a sequence scope. Convert legacy `signal_mappings` only after explicit role, unit and conversion decisions. Publish the first atomic Foundation-plus-binding snapshot; a mapping-affecting publish thereafter follows joint publication. Keep the shared YAML Site source read-only for imported KOBO-001. New Lab Draft setup plus start, step, run-to-end and Commit of existing Drafts stay blocked until Lab can use the registered Foundation/gateway snapshot; Commit of a pre-import Stage remains blocked. Historical run detail and read-only `GET /runs/{run_id}/stage` remain inspectable with their frozen YAML basis.

## Contract and migration seam

- Add immutable SignalBindingRevision storage and publication for one mini-grid role set. Each registered gateway/source/device channel maps to a Site asset, typed role, source/canonical unit and conversion with valid and recorded periods. Publish a binding set atomically with the Foundation basis and reject unknown assets, role/unit conflicts and overlapping current validity.
- `GET /api/sites/{id}/foundation?at=` includes selected binding-set ID/version, device-to-asset/role mappings, required role coverage and explicit gaps. Provide an authenticated download of the registered gateway's immutable versioned snapshot with a verifiable canonical hash. Preserve old snapshots after edits; `knowledge_at` can select the earlier recorded basis. A detached signature is outside this queue.
- Readiness derives from configuration only: unbound generator state/power, feeder demand or battery reserve roles are named; configured roles say ready to report, not healthy or currently reporting. SLD renders actual registered topology and distinguishes unbound devices.
- Migrate an explicit Kobo mapping fixture from existing JSON/YAML for comparison; retain legacy files. A changed binding creates a new effective version. Accepted evidence later retains its original mapping and Foundation basis; a backdated correction may drive a new analytic revision at a later `knowledge_at`, never rewrite the accepted envelope. S2 uses the snapshot as its acquisition contract.

## Demo and acceptance fixture

1. Open Kobo Foundation, Readiness and SLD for a selected time. Trace generator controller status and battery SOC channels to registered source, asset, role, unit, Foundation revision and binding revision. Reload all three surfaces and the snapshot.
2. Remove a required binding in a new effective version. Readiness names the missing role; SLD shows only supported configured links. Reopen an earlier time and recover the old mapping and snapshot hash.
3. Refuse a mismatched unit, another Site's asset and overlapping current channel binding atomically. An absent source or binding is shown as Unknown/unbound, never as a healthy operating state.
4. Reviewer follows a mapping ID from the screen through the read API to Postgres and the snapshot. State explicitly that accepted SourceEnvelope lineage starts with S2; this configuration basis is what a later envelope must cite.

## Protected seams and checks

Use current technical design configuration and snapshot rules. Test atomic publish, validity cutover, historical read, missing role and cross-site refusal, plus changed frontend checks and workflow/architecture guards. Inspect screen and API at both times.

## Defer

No evidence acceptance, analytics, live state, broad device authoring, multi-protocol drivers or full bitemporal editing UI.
