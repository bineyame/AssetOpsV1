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

Site source-health read model from cadence/heartbeat, ingestion lag and edge diagnostics; bounded battery stress/asset-life assessment linked to Asset.

## Demo acceptance

Stale gateway versus live stressed battery, battery stress window and modelled replacement exposure when supportable; reload.

## Missing/conflicting evidence

Absent evidence is Unknown, not healthy; no remaining-life date or failure diagnosis without inputs.

## Evidence lineage

Health and asset claims resolve accepted readings, configuration, assumptions and SourceEnvelope IDs.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Global Assets root, broad health rules and unsupported maintenance next steps.
