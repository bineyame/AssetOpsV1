# S7-01 — Site Health and first asset risk

Status: outline; refine after technical gates and owner wave input, before activation
USER_REVIEW_REQUIRED: true
Milestone: S7 Health
Depends on: S2-02 central diagnostics, S1-02 bindings, bounded readiness/health contract and D-edge-health-cases. S6-02 is ordering history only.
Branch: task/S7-01-site-health
Planner: Codex, 2026-10-07

## Visible outcome

Site health and battery asset detail separate source freshness, observed stress and unknown state.

## Persisted object and read contract

Site source-health read model from cadence/heartbeat, ingestion lag and edge diagnostics; a bounded battery stress/asset-life assessment linked to Asset only when a causal observation supports it, otherwise an explicit Unknown state.

## Demo acceptance

Use centrally received gateway diagnostics from S2-02 for stale contact, queue age/depth, clock offset and disk pressure; a local Lab status alone cannot support Site Health. Planner names `D-edge-health-cases` for outage/pressure and verifies central reload. Show battery stress only if a causal simulator observation exists; otherwise name the missing input, show Unknown and withhold replacement exposure. `I-sim-battery-cases` is outside the S7 queue and captured-device replay is unavailable for this simulated-only demo. Reload the central diagnostic and asset states.

## Missing/conflicting evidence

Absent evidence is Unknown, not healthy; no remaining-life date or failure diagnosis without inputs.

## Evidence lineage

Source-health state resolves central diagnostic IDs and server receive times. Any supported battery claim additionally resolves accepted readings, configuration, assumptions and SourceEnvelope IDs; an Unknown state names the missing input.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Global Assets root, broad health rules and unsupported maintenance next steps.
