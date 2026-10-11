# S6-01 — Action and controlled policy change

Status: outline; refine after technical gates and owner wave input, before activation
USER_REVIEW_REQUIRED: true
Milestone: S6 Work / Action / Verification
Depends on: S4-01 Finding identity/read, S1 Foundation publish, and recorded actor/route contracts. S5-01 is ordering history only.
Branch: task/S6-01-action-change
Planner: Codex, 2026-10-07

## Visible outcome

Site changes/recommendation/sitework show one accepted Action and its applied Foundation reserve-SOC change.

## Persisted object and read contract

Action, ActionEvent and immutable policy-change artifact linked to a newly published Foundation revision; Site Work read API. Use the S1 Foundation publish path for the supported reserve-SOC change, not a Lab-only override. Apply the recorded actor identity and Finding/Action route contracts.

## Demo acceptance

Accept a recommendation, publish a controlled reserve-SOC revision, and record its application event. Show the Action and change artifact after reload with outcome pending. S6-02 owns the later Lab run, accepted window and verification outcome.

## Missing/conflicting evidence

If policy cannot apply or later evidence is absent, show pending/failed activity, not Verified.

## Evidence lineage

Action links Finding basis and configuration artifact; later accepted envelope IDs remain inspectable.

## Review and refinement

S6-01 owns `I-action-store/read/ui`, `D-action-records`, `I-recommendation-read/ui`, `I-configuration-change-read/ui`, `I-action-overview-ui`, `I-action-execution-ui` and `I-action-history-ui`. These close `sitework:1`, `action-overview:1`, `recommendation:1`, applied-change `changes:1`, `action-execution:1` and `action-history:1` only after review. The moved child views require ActionEvent IDs, actor/provenance, applied or failed policy activity, exact event/cutoff selection, pending state, stable Site Action navigation and app/mock desktop/narrow comparison. Activity and event history do not imply a verified outcome or human attestation.

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Global Actions index and generic intervention framework.
