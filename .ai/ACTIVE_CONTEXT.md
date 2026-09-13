# Active Context

Keep this file compact and current. It is the agent handoff for what matters
now; durable reasoning stays in `.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md`,
`.ai/ARCHITECTURE.md`, and the task files.

## Current Milestone

M1 - A user can configure one mini-grid site, simulate it, and inspect the
resulting operational evidence in the UI.

## Active Task

Active task: `tasks/T007-site-details-by-site-id.md` (Status: `in_review`).

T007 is built on `task/T007-site-details-by-site-id` and awaits independent
review. `USER_REVIEW_REQUIRED: false`: the next reviewer is the independent
Reviewer, not the user. The review packet is `.agent/T007-review-packet.md`.
The task file stays in `tasks/` until review closes.

T006 is complete. Reviewer verdict was accept with no findings; user review on
2026-09-14 accepted the slice as built. The task file moved to
`tasks/completed/T006-create-a-site-from-a-template.md` with its Review Outcome
and User Review Outcome, and the branch merged to `main`.

T005 is complete. Its task file is in `tasks/completed/` with its Review
Outcome, and its branch merged to `main`.

Next task after T007 closes:

- `tasks/T008-read-only-site-configuration-presentation.md`
- Lane: Planned lane, then independent review, then user review.
- User review: T008 is the second and final user-review checkpoint of the
  feature.

## Current Site Foundation Sequence

Reworked Site Foundation tasks are T005-T013 in `tasks/`.

- T005: shipped Site Template catalog in Simulator Lab, gated. Complete.
- T006: create a Site from a template; first user-review checkpoint. Complete.
- T007: Site Details by `site_id`. Built, awaiting independent review.
- T008: read-only Site Configuration; second user-review checkpoint.
- T009-T013: staged visual fidelity after real content exists.

Capability planning stops at the second checkpoint. Causal Sequencing step 4,
topology, devices, and the configured single-line diagram, is not planned. No
step 3 slice may render the diagram, an empty frame for it, or its signal
selector.

## Read For T008

Carried forward from T007. T008 adds the read-only Site Configuration surface
and removes the parameterless `Site configuration` frame and navigation item,
so it consumes the substrate and the per-Site read path T007 built.

- `tasks/T008-read-only-site-configuration-presentation.md`
- `tasks/completed/T006-create-a-site-from-a-template.md` for the Site record
  shape, the port, and the substrate. Its "What T006 Settled In Code" summary
  is below, extended by "What T007 Settled In Code".
- `.ai/FEATURE_MAP.md` sections:
  - Feature Map Index
  - Product Spine
  - Enforceable Protected Seams
  - Early Feature: Site Foundation And Configuration-Only Site
- `.ai/DECISIONS.md` decision-index entries:
  - `D-2026-09-13-site-foundation-persistence`
  - `D-2026-09-13-site-foundation-resequence`
  - `D-2026-09-13-shared-site-substrate`
  - `D-2026-09-13-provenance-status-vocabulary`
  - `D-2026-09-13-canonical-fidelity`
- `.ai/ARCHITECTURE.md` only if dependency direction, contracts, simulator
  boundaries, or protected seams are in play.

## Settled Direction

- M1 ships zero canonical Sites. First run has a genuinely empty Sites index.
- A template is not a Site and never has `site_id`, lifecycle status, location,
  or a place-bound timezone.
- Template browsing and Site creation are Simulator Lab surfaces behind
  `simulator_lab.enabled`.
- Sites index, Site Details, and Site Configuration are operator surfaces and
  are never gated.
- A Site created from the Lab is a normal product Site with
  `source.mode = SIMULATED`; there is no Lab-owned Site store and no publish or
  promote step.
- Operator navigation does not grow for Site Foundation slices.
- Operator Site page and Lab Site page share one presentation substrate at
  `frontend/src/sites/`.
- Source mode, Site lifecycle, configuration origin, evidence readiness, and
  source health are separate concepts.

## What T006 Settled In Code

For later slices, so the shape is not rediscovered:

- The Site record is `site_id`, `display_name`, `site_type`, `location`
  (`country`, `locality`), `timezone`, `lifecycle_status`, `origin`,
  `source.mode`, `template` provenance or null, and `foundation` (`version`,
  `valid_from`, `summary`, `components`). `site_type` sits on the Site rather
  than inside `foundation`, because the M1 Site schema names it a Site field
  and two copies would be two sources of truth.
- Two Site stores: `config/sites/` ships empty and read-only, `var/` holds the
  writable user store and is gitignored. One composite adapter merges them and
  refuses a `site_id` present in both.
- `site_id` is charset- and shape-constrained in `sites/identity.py`, above the
  adapter layer, and compared case-insensitively.
- `timezone` is validated by IANA-name shape, not by membership of the tz
  database: `tzdata` is an optional platform package on Windows, and Site
  identity must not depend on which host validated a document. Tightening this
  means taking a dependency, which T006 did not.
- The create API is `POST /api/simulator-lab/sites`; the operator index is
  `GET /api/sites` and is never gated.
- Frontend substrate at `frontend/src/sites/`: `siteReadModel.ts`,
  `siteViewModel.ts`, `siteDirectoryClient.ts`, `SitesIndex.tsx`. Render
  equivalence still ships at causal step 6 with the Lab's Site view.

## What T007 Settled In Code

- `GET /api/sites/{site_id}` is the ungated operator read path. Lookup
  validates the requested identity in the handler before the port, so a
  malformed id and an unreadable store cannot arrive as the same exception; a
  malformed or unknown id is 404 with a `SITE_NOT_FOUND` refusal, an unreadable
  store is 503 with `SITE_STORE_UNAVAILABLE`. Case-insensitive lookup is
  confirmed as the wanted routing behaviour and the response carries the stored
  canonical `site_id`.
- The detail wire shape is the index shape plus `foundation.version` and
  `foundation.valid_from`. Foundation content, the summary and the components,
  is deliberately not on the wire yet: it is T008's shape and no field for it is
  declared before a screen renders it.
- The Site record still carries no `created_at` or `updated_at`.
  `foundation.valid_from` is the only record-backed timestamp and is rendered
  verbatim as `Valid from`.
- Frontend: `frontend/src/shell/operatorSiteRoutes.ts` owns `SITES_PATH`,
  `SITE_DETAIL_ROUTE_PATH` (`/sites/:siteId`) and `siteDetailHref`. The
  substrate gained `SiteDetailReadModel`, `SiteDetailResult`,
  `SiteDetailClient`, `deriveSiteDetailView` and `SiteDetails.tsx`;
  `SitesIndex` takes a `siteHref` builder so the row link is an address, not a
  mode.
- The three unavailable facts, integration readiness, evidence availability and
  source health, are constants in the view model with a value and a reason, so
  both shells state the same absence the same way.
- `tools/check-architecture.ps1` gained a Site-detail-component clause on the
  single-definition check (with `*Frame` exempt as the shell route-frame name)
  and a navigation-truthfulness check that `/site-details` appears nowhere in
  `frontend/src` while an identified site route does.

## Carried-Forward Risk

Settled before T006: the disabled-bundle concern is now explicit in
`.ai/FEATURE_MAP.md` as a runtime reachability seam, not a bundle-content seam.
The gate must prove that no Lab route, action, API, create flow, simulator URL
backdoor, or operator import path into Lab internals is served when
`simulator_lab.enabled=false`; it does not try to prove Lab modules are absent
from the built frontend bundle.

From T005, settled by T006: the template Foundation carries only `site_type`,
`summary`, and components with declared ratings. T006 copies that as the
Foundation seed, while the created Site record adds user-supplied identity
fields and service-defaulted origin, source mode, lifecycle, and template
provenance. Full carried-forward list is in the T005 Review Outcome.

From T006, open and not actionable inside it:

1. `timezone` accepts a syntactically valid but non-existent zone, because
   validation is shape-only. Accepted by the user at the T006 checkpoint. Tighten
   before scenario timing or window analytics consume the value, not after.
2. No automated integration test binds the real frontend fetch clients to the
   backend. Same gap T005 recorded, now spanning two slices; covered by manual
   dev-proxy smoke only. If a third slice inherits it, it stops being a gap and
   becomes a decision.
3. Write exclusivity on the user store is process-scoped, not an OS-level
   exclusive rename. Atomicity and durability hold; a cross-process race does
   not. Single-host file store, so not yet reachable.
4. Settled by T007: `get_site` resolves `site_id` case-insensitively, matching
   the conflict rule. T007 confirmed this is the routing behaviour it wants and
   pinned it with API and UI tests; the canonical stored spelling is what is
   returned and rendered.
5. The substrate single-definition guard keys on naming patterns. Render
   equivalence at causal step 6 is the real guard.
6. Product copy uses "capitalisation" in the duplicate-`site_id` refusal. Noted
   at the T006 user review as a consistency question for a later copy pass.

From T007, open and not actionable inside it:

1. The M1 Site record has no `created_at` or `updated_at`. The T007 narrative
   listed created and updated timestamps; only `foundation.valid_from` exists,
   so that is what the site page renders, labelled as what it is. Adding the two
   fields is a schema plus write-path change and belongs to a slice that decides
   it deliberately.
2. Integration readiness has no field on the record. The site page states it as
   `Not recorded` with a reason. It stays a stated absence until a slice gives
   it a truthful source.
3. Still no automated integration test binding the real frontend fetch clients
   to the backend. Third slice in a row; covered by a manual dev-proxy smoke
   only. This has now stopped being a gap and should be decided.
4. The site page was verified by tests, the production build, and a real
   backend plus dev-proxy smoke of the API. It was not clicked through in a
   browser.


## Standard Checks

- `tools/check-architecture.ps1`
- `tools/check-agent-workflow.ps1`
- Existing backend and frontend tests relevant to the active slice.

## Task Spec Hygiene

For new or revised task specs, follow `.ai/WORKFLOW.md` Task Spec Size guidance.
Large early M1 specs are acceptable only when they protect dangerous firsts; do
not let that become the default task shape.

Before handing off a new task, scan for repeated negative lists, exact wording
requirements, and implementation mechanics. Keep only what protects a named
seam or slice-specific risk.

## Inherited M1 Step 3 Exclusions

Tasks T005-T013 inherit these exclusions unless a later reviewed task explicitly
changes them:

- No in-place Site/Foundation editing, Save/Publish over an existing Site,
  rename, duplicate, delete, configuration history, rollback, approval flow, or
  disabled placeholder for those capabilities.
- No user-facing removal flow.
- No Single Line Diagram, empty diagram frame, signal selector, SLD view model,
  topology auto-layout, Devices & Sensors screen, or device-management surface.
- No scenarios, run setup, simulator execution, gateway staging, ingestion,
  source envelopes, evidence records, source health, charts, analytics, Replay,
  or Findings.
- No speculative database, ORM, migration tool, cache, query DSL, pagination,
  or port methods beyond the active slice.
- No operator navigation item, second simulator chokepoint, or weakening of
  previous route, API, navigation, architecture, or fabricated-value guards.
- No mockup value, timestamp, status, label, control, or destination unless the
  active slice supplies truthful backing content.
