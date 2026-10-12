# S4-01 — Candidate generator-support Finding

Status: active (selected 2026-10-12 via owner contest choice `.agent/owner-contest-rule-2026-10-12.md`; phase 1)
USER_REVIEW_REQUIRED: true
Milestone: S4 Finding + Financials
Depends on: merged S3-01 (`I-S3-01`), resolved `A-finding-episode` and `A-claim-work-routes`, accepted S2 Evidence
Branch: task/S4-01-finding-identity
Planner: Codex, 2026-10-12

## Outcome and authority

Open a persisted mini-grid candidate generator-support Finding from a CURRENT, coherent `dispatch-3.1` selected assessment containing at least one bounded `CANDIDATE_AVOIDABLE` segment. The Site-scoped Finding detail (`finding:1,2,4`) shows its exact selected revision, bounded duration/limitations, lifecycle state and accepted-source drill-down after reload. Necessary and Indeterminate portions remain distinct facts; a candidate segment does not make a whole generator interval avoidable. Owner W1 core approval is a target, not panel delivery or whole-screen Real status.

Use `D-2026-10-12-finding-episode-and-revisions` and `.agent/architect-A-finding-episode-answers.md`, the S3-01 reviewed `dispatch-3.1` selected-revision/read contract, technical design §§1/3–4, and `D-2026-10-09-pre-s3-claim-routes-and-actor`. Existing file-backed/T028 Findings are comparison history only; their assessment IDs are not durable Finding identity. `A-finding-index` and the S3-01u assessed-day/paged-evidence carry are separate and are not S4-01 technical gates.

## Write, matching and lineage contract

- Allocate `finding.id` and immutable `finding_key` once for tenant, Site, mini-grid, generator asset and candidate-support episode. Persist the first accepted candidate anchor, selected public cohort, supported bounds/window IDs and matcher version. Never key ongoing identity from a mutable first-ON time, UTC day, assessment hash or private Lab run.
- Match a CURRENT selected candidate span to persisted episodes across UTC-day boundaries. Supported overlap or a gap ≤20 minutes may extend one episode only with a coherent, noncontradictory public series. A proven gap >20 minutes starts a new Finding with `recurs_after_finding_id`. Contradictory, ambiguous or insufficient evidence never bridges a gap. Late earlier accepted evidence may move the bound/first-ON key without renaming the Finding.
- On a split, retain the original ID for the part containing its immutable anchor, append a revision explaining changed support, and link a new Finding for each other supported part. On a later bridge between two persisted IDs, preserve both old URLs/revisions, choose the earlier stable anchor (then UUID) as canonical, record a durable merge/supersession relation, and show only the canonical active episode. Do not silently delete or reuse either ID.
- Persist Finding and append-only FindingRevision. Idempotency is `(finding, canonical selected assessment basis, transition)`: retry of one basis adds no revision. Each revision cites exact selected interval AssessmentRevision, its AnalyticRun/model/cohort/window and selected window AssessmentRevision; cross-window episodes also cite every supporting interval revision, using a relation when one FK is insufficient. Keep the technical design's primary assessment FK. Preserve the complete analytic input set separately from accepted evidence IDs/digests actually cited by candidate segments, plus as-accepted Foundation/binding and selected control revisions, source/batch/envelope lineage.
- A changed accepted basis, candidate duration/limit, backdated control or reviewed model version appends a revision. Historical `dispatch-3` may be pinned for audit but cannot create/refresh a CURRENT `dispatch-3.1` Finding; later reviewed `dispatch-3.x` is a new basis, never a relabel. An Indeterminate CURRENT reassessment may append `UNCONFIRMED` to an existing episode but creates no new avoidability Finding. A complete CURRENT no-Candidate/Necessary-only reassessment can append `NO_LONGER_SUPPORTED`; it does not say repaired or savings realised. STALE/FAILED/UNASSESSED changes read status without manufacturing a revision.

## Detail read and visible states

Implement canonical `/sites/{site_code}/findings/{finding_id}` and `GET /api/sites/{site_code}/findings/{finding_id}` with optional exact `revision_id`, tenant/Site scope and `A-claim-work-routes` status semantics (401 unauthenticated, 403 unauthorized known scope, 404 foreign/nonexistent root or revision). Omitted revision selects latest permitted recorded revision; exact ID pins history after late evidence. Return stable Finding UUID/key, selected FindingRevision, episode relationship IDs, selected dispatch/run/model/cohort/window and supporting revision IDs, claim and limitations, cited accepted evidence IDs/digests, projection state and source/analytic watermarks. Preserve Site/window/revision in back-links. The S3 worker-clock `knowledge_at` is not a commit-ordered audit fence: advertise exact stored revision/IDs, not arbitrary historical replay.

Distinguish `NOT_ASSESSED`, `PENDING`, `STALE`, `FAILED`, assessed `NO_FINDING`, current supported, existing `UNCONFIRMED`, and `NO_LONGER_SUPPORTED`/recurrence. No Finding row alone is not a healthy verdict; no current assessed basis cannot become `NO_FINDING`. Show supported claim, confidence/limitations and workflow state separately. Keep unsupported money, recommendations and full Evidence/History tabs hidden or typed unavailable. S4-03 owns those child views, S4-04 the Site list, S4-02 money and S6 Action/verification.

## `D-finding-revisions` acceptance fixture

Use versioned `s4-finding-cases-v1` labels below. The stable fixture specification records producer version, seed, public source/binding/control IDs, selected S3 model/version and expected transition; per-run generated batch/evidence/run/Finding IDs live in an environment-bound verified artifact, not a committed “current” snapshot. Produce selected assessments through the S2 registered simulated gateway, sealed Batch V2, central acceptance and S3 recompute/read. A separate labelled authenticated fault fixture follows S2's precedent and is never described as gateway-sealed. Never insert Finding rows directly as fixture truth.

| Case | Expected Finding transition and proof |
| --- | --- |
| F01 candidate/open | CURRENT coherent candidate segment opens one ID; persist bounded candidate duration, distinct Necessary/Indeterminate facts and exact cited accepted IDs. |
| F02 overlap/adjacent/cross-day | Same ID extends across overlap and a ≤20-minute coherent gap, including UTC midnight; a changed basis appends a revision. |
| F03 recurrence | Supported >20-minute separation opens a new ID with `recurs_after_finding_id`; both old URLs reload. |
| F04 late earlier acceptance | Later accepted source record shifts first-ON/coverage; original immutable anchor/ID survives and revision 2 selects new S3 revision while revision 1 remains readable. |
| F05 limitation and closure | A CURRENT Indeterminate reassessment limits an existing episode as UNCONFIRMED, creating no new Finding; a later complete CURRENT no-Candidate basis closes support as NO_LONGER_SUPPORTED, not repair. |
| F06 split and bridge | Accepted reassessment splits one episode around its anchor; other supported part gets a linked ID. A later coherent bridge merges two persisted IDs via canonical/supersession relation while both histories remain addressable and only one active claim appears. |
| F07 model upgrade | A genuinely versioned, reviewed later `dispatch-3.x` re-evaluation appends a new FindingRevision; old `dispatch-3`/`3.1` lineage stays pinned. If no reviewed later model exists during implementation, prove the version-change path with a clearly labelled test-scoped rule fixture and withhold a live upgraded claim; record this limit at review. |
| F08 retry and absent basis | Replaying the same selected basis adds no row; stale/failed/unassessed or ambiguous cohort does not create or close a Finding. |

## Phases and reviewer handoffs

Each phase is a bounded Implementer context below ~120k and has its own reviewable evidence; `I-S4-01` closes only after all phases, independent review and owner checkpoint.

| Phase | Reviewable result |
| --- | --- |
| 1. `I-finding-store` and `D-finding-revisions` | Migration for Finding/revision and supporting assessment/evidence/episode relations; idempotent matcher/transitions; F01–F08 public fixture specification and accepted IDs. Verify same-ID extension, recurrence, split/merge, upgrade and retry with Postgres reload before proceeding. |
| 2. `I-finding-read` | Tenant/Site-scoped exact root/revision API, selected S3/currentness read, 401/403/404/typed unavailable matrix and old/new pinned lineage. No arbitrary `knowledge_at` replay claim. |
| 3. `I-finding-ui` and closeout | `finding:1,2,4` detail and concise evidence summary, honest empty/lag/closed states, stable route/back-links, app/mock comparison, end-to-end walkthrough and cutover proof. |

Reviewer follows F01, F04, F05, F06 and F07 after reload: verify selected IDs, immutable old/new revisions, model/cohort/window, cited versus full input evidence, accepted envelope and as-accepted binding/selected Foundation control. Exercise recurrence, cross-day continuity and no-new-row states; compare returned API IDs with stored relations. A positive claim from private Lab oracle, a stale selected model or an unresolved merge blocks closeout. Inspect migrations and focused Postgres matcher/revision/route tests; run normal backend/frontend checks and registry, ledger, navigation, workflow and architecture guards. Record fixture/run IDs and exact commands in the review packet.

Compare app `/sites/{site_code}/findings/{finding_id}` with v6.9 `index.html#/finding` at 1440px desktop and 390px narrow (or documented equivalents) for `finding:1,2,4`: hierarchy, labels, bounded claim, limitations, status, evidence drill-down, keyboard selection and reload. Capture populated, unconfirmed, no-finding and pending/stale states; document supported portions and deliberately unavailable mock content. App screenshots plus interaction/API lineage evidence are required; visual similarity alone does not make a panel Real. Use `tools/layout-evidence.mjs` for layout-sensitive work.

Owner checkpoint: prepare a repeatable walkthrough from a clean fixture run showing open candidate, same-ID late revision, recurrence, unconfirmed/no-longer-supported states, exact old revision URL and one accepted-source lineage trace; show mock/app desktop and narrow comparisons and name withheld money/Action/child-list content. State whether F07 was a live reviewed upgrade or test-scoped proof. The coordinator records the owner's words; the Implementer and Reviewer do not pre-record approval.
