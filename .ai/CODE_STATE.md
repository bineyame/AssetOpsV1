# Code State

What completed slices already settled in code, and what they left open.

This file exists so `.ai/ACTIVE_CONTEXT.md` can stay a routing document. Both
sections below grow by one entry per slice; keeping them in the active context
made it the largest thing every implementer read, and it was the file that had
already been trimmed once for exactly that reason.

Read the entry for the slice you are building on, not the whole file. The
"Read For T00N" list in `.ai/ACTIVE_CONTEXT.md` names which entries matter.

Two rules keep this file useful:

- Record what a later slice would otherwise rediscover from the code, and the
  reason behind a shape that looks arbitrary. Not a change log.
- When an open item is closed, mark it settled in place and say which slice
  closed it. Do not delete it: a risk that disappears silently reads as a risk
  nobody ever had.

## What The Code Settles

### T006 - create a Site from a template

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

### T007 - Site Details by `site_id`

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
- The architecture guard gained a Site-detail-component clause on the
  single-definition check (with `*Frame` exempt as the shell route-frame name)
  and a navigation-truthfulness check that `/site-details` appears nowhere in
  `frontend/src` while an identified site route does.

### Tooling and test substrate

Not owned by a product slice, but load-bearing for every one of them.

- The architecture guard is a runner, `tools/check-architecture.ps1`, over one
  module per seam in `tools/checks/`. A slice that changes one seam reads that
  seam's module. The runner cross-checks its manifest against the directory, so
  a module cannot be added and left unwired or deleted and left unenforced.
- Screens that read the store render their own level-1 heading and their own
  `<main>` while the read is in flight, so neither is a settle point in a test.
  `frontend/src/test/settled.ts` exposes `settledScreen`, which waits for the
  loading state to go and therefore works for a loaded record, an empty index,
  a not-found refusal, and an unreadable store alike. Settling on a heading or
  a landmark instead is the defect described under T007 open item 5.

## Carried-Forward Risk

Settled before T006: the disabled-bundle concern is explicit in
`.ai/FEATURE_MAP.md` as a runtime reachability seam, not a bundle-content seam.
The gate must prove that no Lab route, action, API, create flow, simulator URL
backdoor, or operator import path into Lab internals is served when
`simulator_lab.enabled=false`; it does not try to prove Lab modules are absent
from the built frontend bundle.

Settled by T006, from T005: the template Foundation carries only `site_type`,
`summary`, and components with declared ratings. T006 copies that as the
Foundation seed, while the created Site record adds user-supplied identity
fields and service-defaulted origin, source mode, lifecycle, and template
provenance. Full carried-forward list is in the T005 Review Outcome.

### From T006

1. `timezone` accepts a syntactically valid but non-existent zone, because
   validation is shape-only. Accepted by the user at the T006 checkpoint.
   Tighten before scenario timing or window analytics consume the value, not
   after.
2. No automated integration test binds the real frontend fetch clients to the
   backend. Superseded by T007 open item 3, which is the same gap on its third
   slice.
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

### From T007

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
   only. This has stopped being a gap and should be decided.
4. The site page was verified by tests, the production build, and a real
   backend plus dev-proxy smoke of the API. It was not clicked through in a
   browser.
5. Settled after T007 was built, and worth knowing before trusting a green
   suite: twelve frontend tests settled on a level-1 heading or the `<main>`
   landmark, both of which render during loading, so they asserted against a
   screen that had not loaded. They passed in isolation and failed under CPU
   contention, which is what the T007 packet recorded as an unreproducible
   single failure; the diagnosis there, a `findBy*` timeout, was wrong. Most of
   the twelve assert absence, which a loading screen satisfies trivially. Fixed
   with `settledScreen`; the pattern is the thing to watch for, not the twelve.
