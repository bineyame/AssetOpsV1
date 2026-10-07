# S7-01 — Site Health and first asset risk

Status: outline; refine after preceding task review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S7 Health
Depends on: S6-02
Branch: task/S7-01-site-health
Planner: Codex, 2026-10-07

## Visible outcome

Site health and battery asset detail separate source freshness, observed stress and unknown state.

## Persisted object and read contract

Site source-health read model from cadence/heartbeat, ingestion lag and edge diagnostics; a bounded battery stress/asset-life assessment linked to Asset only when a causal observation supports it, otherwise an explicit Unknown state.

## Demo acceptance

Use centrally received gateway diagnostics from S2-02 for stale contact, queue age/depth, clock offset and disk pressure; a local Lab status alone cannot support Site Health. Planner names `D-edge-health-cases` for outage/pressure and verifies central reload. Battery stress is shown only if a causally supportable simulator observation exists; otherwise the battery claim is Unknown with its missing input named. `I-sim-battery-cases` is an optional follow-on producer, not an S7 queue prerequisite, and captured-device replay is unavailable for this simulated-only demo choice. Keep source freshness distinct from battery stress.

Stale gateway versus live source, and a battery stress window only if the simulator can produce defensible public observations; otherwise show Unknown and withhold replacement exposure. Reload both central diagnostics and the supported asset state.

## Missing/conflicting evidence

Absent evidence is Unknown, not healthy; no remaining-life date or failure diagnosis without inputs.

## Evidence lineage

Health and asset claims resolve accepted readings, configuration, assumptions and SourceEnvelope IDs.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Global Assets root, broad health rules and unsupported maintenance next steps.
