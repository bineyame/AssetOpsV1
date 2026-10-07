# Site-first task queue

**Current direction (2026-10-07):** [accepted system architecture](../frontend/docs/architecture/production-shaped-mvp.md), [accepted technical design](../frontend/docs/architecture/production-shaped-mvp-technical-design.md), and [Site-first execution plan](../frontend/docs/architecture/site-first-execution-plan.md). This is the only executable queue. The [superseded T0xx queue](archive/pre-site-first-2026-10-07/README.md) and its open packets are historical reference with original status intact. Completed tasks and decisions remain historical built-state evidence.

One mini-grid Site and one assessed window form the first end-to-end path. Work one slice at a time. The first task of each milestone must persist enough to make its named screen state real. S1 packets are implementation-ready; S2–S7 are outlines to refine after the preceding review. Do not activate a later outline without that refinement. No product behavior is implemented by this planning change.

| Milestone | Task | Visible mock-screen result | Direct dependency | Status |
| --- | --- | --- | --- | --- |
| S1 Foundation | [S1-01](S1-01-persisted-foundation.md) | Foundation opens a persisted, time-selectable Kobo version | None; accepted architecture | Ready for implementation |
| S1 Foundation | [S1-02](S1-02-bindings-readiness.md) | Foundation mappings, Readiness gaps and configured SLD | S1-01 | Planned |
| S2 Evidence | [S2-01](S2-01-durable-gateway.md) | Lab gateway queue and sealed envelopes survive restart | S1-02 | Outline |
| S2 Evidence | [S2-02](S2-02-ingestion-site-evidence.md) | Site Evidence shows accepted, rejected and duplicate decisions | S2-01 | Outline; owner review checkpoint |
| S3 Performance | [S3-01](S3-01-dispatch-assessment.md) | Dispatch interval classification with evidence and gaps | S2-02 | Outline |
| S4 Finding + Financials | [S4-01](S4-01-finding-identity.md) | Finding detail opens from assessed interval with stable episode identity | S3-01 | Outline |
| S4 Finding + Financials | [S4-02](S4-02-bounded-financials.md) | Financials shows quantity, assumption and bounded amount | S4-01 | Outline; owner review checkpoint |
| S5 Overview | [S5-01](S5-01-site-overview.md) | Selected-window Site Overview composes real claims | S4-02 | Outline |
| S6 Work | [S6-01](S6-01-action-change.md) | Site Work records a real Action and policy change | S5-01 | Outline |
| S6 Work | [S6-02](S6-02-verification.md) | Verification compares a later accepted window and guardrails | S6-01 | Outline; owner review checkpoint |
| S7 Health | [S7-01](S7-01-site-health.md) | Health separates source freshness from battery stress | S6-02 | Outline; owner review checkpoint |

All packets inherit the accepted architecture and technical design. Every closeout needs the selected-window screen, read API, storage/reload, missing or contradictory evidence state, and lineage to the accepted SourceEnvelope. S2 additionally proves loss/retry/duplicate/conflict; S3–S4 preserve revisions after late evidence; S6 proves a failed guardrail. Follow `.ai/WORKFLOW.md` for independent review and appropriate checks. The four owner-review moments are S2 evidence, S4 bounded money, S6 verification and S7 Site Health. Global indexes, extra domains and empty tabs follow the Site journey.
