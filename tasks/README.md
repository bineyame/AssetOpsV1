# Site-first task queue

**Current direction (2026-10-07):** [current system architecture](../frontend/docs/architecture/production-shaped-mvp.md), [current technical design](../frontend/docs/architecture/production-shaped-mvp-technical-design.md), and [Site-first execution plan](../frontend/docs/architecture/site-first-execution-plan.md). These are current implementation authority under project routing; their proposal headers do not record owner sign-off. The Architect decision `D-2026-10-07-s1-foundation-import-and-cutover` and S1-01 addendum control the first slice. This is the only executable queue. The [superseded T0xx queue](archive/pre-site-first-2026-10-07/README.md) and its open packets are historical reference with original status intact. Completed tasks and decisions remain historical built-state evidence.

One mini-grid Site and one assessed window form the first end-to-end path. Work one slice at a time. The first task of each milestone must persist enough to make its named screen state real. S1 packets are implementation-ready; S2–S7 are outlines to refine after the preceding review. Do not activate a later outline without that refinement. No product behavior is implemented by this planning change.

**Pre-S4 Architect gates:** Record `A-claim-work-routes` before S4-01 refinement: stable tenant/Site-scoped Finding and Action routes, revision selection, and unavailable/forbidden behavior. Record `A-actor-identity` before S4-02 refinement: human author versus authenticated/system actor, authorization and attestation provenance for `financial_assumption_revision.author_id` and later Action/work events. S6-01 reuses both accepted contracts. These are decisions, not new implementation tasks. At each S2–S7 outline refinement, the Planner compares the packet with the dependency registry's `queue_baseline_nodes`; a contract or fixture no longer owned by the queue leaves that baseline before marginal estimates are used.

| Milestone | Task | Visible mock-screen result | Direct dependency | Status |
| --- | --- | --- | --- | --- |
| S1 Foundation | [S1-01](S1-01-persisted-foundation.md) | Foundation opens a persisted, time-selectable Kobo version | None; current architecture | Ready for implementation |
| S1 Foundation | [S1-02](S1-02-bindings-readiness.md) | Foundation mappings, Readiness gaps and configured SLD | S1-01 | Planned |
| S2 Evidence | [S2-01](S2-01-durable-gateway.md) | Lab gateway queue and sealed envelopes survive restart | S1-02 | Outline |
| S2 Evidence | [S2-02](S2-02-ingestion-site-evidence.md) | Site Evidence shows accepted, rejected and duplicate decisions | S2-01 | Outline; owner review checkpoint |
| S3 Performance | [S3-01](S3-01-dispatch-assessment.md) | Dispatch interval classification with evidence and gaps | S2-02 | Outline |
| S4 Finding + Financials | [S4-01](S4-01-finding-identity.md) | Finding detail opens from assessed interval with stable episode identity | S3-01; `A-claim-work-routes` | Outline |
| S4 Finding + Financials | [S4-02](S4-02-bounded-financials.md) | Financials shows quantity, assumption and bounded amount | S4-01; `A-actor-identity` | Outline; owner review checkpoint |
| S5 Overview | [S5-01](S5-01-site-overview.md) | Selected-window Site Overview composes real claims | S4-02 | Outline |
| S6 Work | [S6-01](S6-01-action-change.md) | Site Work records a real Action and policy change | S5-01; reuse both pre-S4 Architect gates | Outline |
| S6 Work | [S6-02](S6-02-verification.md) | Verification compares a later accepted window and guardrails | S6-01 | Outline; owner review checkpoint |
| S7 Health | [S7-01](S7-01-site-health.md) | Health separates source freshness from battery stress | S6-02 | Outline; owner review checkpoint |

## Screen-outward planning gate

The [v6.9 screen realization map](../frontend/docs/architecture/v69-screen-realization-map.md), [screen ledger](../frontend/docs/architecture/v69-screen-ledger.json), [model homes](../frontend/docs/architecture/v69-model-homes.json) and [panel contracts](../frontend/docs/architecture/v69-panel-contracts.json) are Architect planning overlays, not accepted screen completion. They account for 110 manifest IDs, 88 model names and 258 visible panels. Proposed fidelity tiers, including `Real with honest gaps`, remain **pending owner review**. The manifest ID and its `visual_reference` key each later comparison; `GAP` in a panel contract means no supported claim yet. Run `python frontend/docs/architecture/check_v69_ledger.py` after ledger changes.

For each `Deferred` screen, the ledger's `promotion_dependencies.to_candidate` lists the design, projection, fixture and task gates before it can enter the executable queue. For every proposed `Real with honest gaps` screen, `promotion_dependencies.to_real` names unresolved panels and remaining work before full mock fidelity can be claimed. A named S task alone does not satisfy that gate. The Planner checks these fields when refining a packet and updates them when a dependency is met or the owner changes a tier.

S1-01, S1-02, S2-01 and S2-02 retain the statuses and acceptance boundaries above. **Before S3-01 is activated**, review the owner fidelity-tier choices, the [V-01 proposal](V-01-v69-visual-fidelity.md) after S2 evidence arrives, and the Architect decisions on shared projection/root navigation needed by S3/S4. Resolve only model gaps merited by the next supported claim; broader work, domains and indexes stay in the follow-on lane. S3-S7 packets remain outlines until the preceding slice is reviewed and their named manifest IDs, panel contracts, selected-window API, honest missing state and fidelity check are refined. A proposed tier does not authorize an empty route or an illustrative mock value as product data.

| Proposal | Manifest IDs | Dependency and review gate | Status |
| --- | --- | --- | --- |
| [V-01 visual fidelity](V-01-v69-visual-fidelity.md) | `sites`, `foundation`, `readiness`, `sld`, `evidence`, `evidence-analysis`, `lab`, initial `dispatch` | S2-02 evidence review; owner tier decision; relevant shared navigation/projection decision | Non-executable proposal |
| S3/S4 first claim fixture | `dispatch`, `analysis`, `finding`, `finding-evidence`, `financials`, `assumptions` | [Demo-data plan](../frontend/docs/architecture/v69-demo-data-plan-proposal.md): complete, missing/contradictory and late Kobo intervals, one price revision, exact accepted evidence | Planning dependency |
| S6 later-window fixture | `changes`, `recommendation`, `verification`, `sitework` | Baseline, applied change, later closed window, guardrail fail and inconclusive variant with lineage | Planning dependency |

Current S milestones also own bounded portions of `mini` (S5-01), `action-overview` (S6-01/S6-02), and `health` and `asset` (S7-01). Their remaining panels need the same tier, projection and evidence review; the post-S7 Action lane below refers only to fuller contextual detail.

## Non-executable follow-on dependency lane after S7

These are **planning lanes, not task IDs or executable packets**. Review the owner-approved tier and the ledger's exact panel contract before creating a slice. Keep multi-site and multi-window fixtures traceable through normal ingestion. A global comparison needs aligned windows, coverage, currency/price basis and non-overlap rules; Unknown stays visible when those conditions are absent.

| Lane | Manifest IDs from screen ledger | Must exist before an executable packet |
| --- | --- | --- |
| Mini-grid breadth and Site work views | `renewable`, `service`, `fuel`, `backup`, `sitefindings`, `sitework-incidents`, `sitework-maintenance` | Domain role/analytic and work-case decisions; distinct renewable/service/fuel/backup windows and human attestation where needed; Site-scoped projections and lineage. |
| Work-domain identity | `incidents`, `maintenance`, `maintenance-preventive`, `oprecords` | Architect separates Incident, MaintenanceWorkRequest/Record and OperationalRecord identities/events from Action; author/provenance and Site/Asset links. |
| Global/contextual roots | `assets`, `findings`, `actions`, `action-overview`, `alternatives`, `finding-history`, `action-plan`, `action-execution`, `action-evidence`, `action-history`, `opportunity-finding`, `asset-register`, `asset-overview`, `asset-performance`, `asset-config`, `asset-edit`, `asset-work`, `asset-evidence`, `findings-cost`, `findings-risks`, `findings-opportunities` | Durable Site Finding/Action/Asset objects, shared `FindingIndex`/`AssetHealthSummary` projection contracts, stable root identity/navigation, supported drill-downs and multi-window claim fixtures. |
| Cold-chain and EV Sites | `cold`, `temperature`, `cooling`, `coldbackup`, `incident`, `workverification`, `cold-foundation`, `cold-health`, `cold-evidence`, `cold-evidence-analysis`, `cold-financials`, `cold-assumptions`, `cold-findings`, `cold-work`, `cold-work-incidents`, `cold-work-maintenance`, `cold-finding`, `cold-recommendation`, `cold-finding-excursion`, `cold-action`, `cold-scenarios`, `cold-readiness`, `cold-sld`, `wr-overview`, `wr-record`, `wr-history`; `ev`, `sessions`, `availability`, `energy`, `ev-foundation`, `ev-health`, `ev-evidence`, `ev-evidence-analysis`, `ev-financials`, `ev-assumptions`, `ev-findings`, `ev-work`, `ev-work-incidents`, `ev-work-maintenance`, `ev-finding`, `ev-recommendation`, `ev-action`, `ev-scenarios`, `ev-readiness`, `ev-sld` | Separate Site/role and captured-device fixtures, domain assessments, bounded Finding/consequence and work semantics through the shared ingestion path; missing sensors/sessions remain Unknown. |
| Estate and finance roots | `portfolio`, `globalevidence`, `globalfinancials`, `scenarios` | Multi-site/domain fixture gate; tenant/window/coverage/currency and overlap rules, `CapabilityReadiness`/source-health projection contracts; scenario basis separate from observed money. |
| Asset cover, policy and onboarding | `assets-warranty`, `asset-warranty`, `settings-policies`, `settings-tenant`, `site-create-form`, `site-create-template`, `site-batch-upload`, `site-setup-history` | Audited asset/warranty and tenant policy authority; SiteDraft/Template/ImportBatch/SetupEvent decisions, per-row refusals and tenant authorization. |

For each activated lane, compare app and mock at desktop and narrow widths, including visual tokens/components, navigation and reload. Unsupported routes stay hidden or honestly unavailable; populated, missing and conflicting/late states come from persisted source-to-claim data, never copied mock values. See [V-01](V-01-v69-visual-fidelity.md) for the repeatable comparison method.

## Current-code transition by slice

| Slice | Keep/adapt | Replace or retire at the visible cutover |
| --- | --- | --- |
| S1 | Existing Site shell/Foundation presentation and explicit Kobo fixture | YAML/JSON Site writes for the supported Foundation path become Postgres revisions; old files remain read-only comparison inputs. |
| S2-01 | Simulated observation transform, mapping and envelope publisher | In-process gateway publication becomes a separate SQLite-backed gateway process with a physical adapter contract and durable V3 identity. |
| S2-02 | Existing ingestion validation/deduplication and Evidence UI | Batch V1 remains readable for migration; authenticated V2 HTTPS receipts and Postgres decisions replace in-process Commit-to-ingest and JSON evidence as product authority. |
| S3-S5 | Existing dispatch, Finding and Site presentation where claim semantics still fit | Hard-coded device keys, JSON assessment authority and independent view recalculation give way to typed accepted-evidence inputs, revisioned claims and derived read models. |
| S6-S7 | Existing Lab control and Site shell where they fit | Persist Action/verification/health claims from public evidence and work records; no Lab truth or static mock value becomes product history. |

This is a cutover map, not permission to delete historical fixtures or completed task evidence. The technical design's demo-to-Postgres comparison must pass per supported read: Evidence changes in S2-02 after evidence comparison; Performance changes in S3-01 after dispatch comparison. S2-01 makes the gateway durable; S2-02 makes its upload and central acceptance real; S3 consumes durable recompute jobs. Do not call the current in-process publisher or JSON ingestion the production gateway/ledger.

All packets inherit the current architecture and technical design. Every closeout needs the selected-window screen, read API, storage/reload, missing or contradictory evidence state, and lineage to the accepted SourceEnvelope. S2 additionally proves loss/retry/duplicate/conflict; S3–S4 preserve revisions after late evidence; S6 proves a failed guardrail. Follow `.ai/WORKFLOW.md` for independent review and appropriate checks. The four owner-review moments are S2 evidence, S4 bounded money, S6 verification and S7 Site Health. Global indexes, extra domains and empty tabs follow the Site journey.
