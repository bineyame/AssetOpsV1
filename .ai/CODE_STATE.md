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

Naming note for future slices: T008 built the current route and code symbols
under the user-visible name `Site Configuration`. The settled screen
architecture now names that operator surface `Foundation`; this file preserves
the slice record below, while future code state entries should use `Foundation`
for the user-visible surface and mention old code symbols only when they still
exist in code.

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
- `SiteDetails` holds the store's answer together with the identity it was
  asked about, and discards it in the render that first sees a new `siteId`,
  before any effect runs. Resetting inside the effect instead commits one frame
  with the previous site under the new address. A per-site surface added later,
  T008's configuration among them, needs the same shape or it will present the
  previous site as the one the address names.
- The three unavailable facts, integration readiness, evidence availability and
  source health, are constants in the view model with a value and a reason, so
  both shells state the same absence the same way.
- The architecture guard gained a Site-detail-component clause on the
  single-definition check (with `*Frame` exempt as the shell route-frame name)
  and a navigation-truthfulness check that `/site-details` appears nowhere in
  `frontend/src` while an identified site route does.

### T008 - read-only Site Configuration

- The Foundation reaches the wire on the existing `GET /api/sites/{site_id}`.
  Site Details and Site Configuration are two presentations of one configured
  Site rather than two resources, so there is no endpoint under a Site and no
  second read model. `foundation` is now exactly `version`, `valid_from`,
  `summary`, `components`, and the API test pins that set exactly so a later
  slice cannot put topology on the wire before a screen renders it.
- A component on the wire is `component_id`, `component_type`, `display_name`,
  `rating`. A component with no declared rating carries `null`, never `0`: no
  rating and a rating of zero are different facts.
- There is still no `valid_to`, and no topology, device, signal-mapping or
  control-assumption field, not even an empty list. An empty list would let a
  screen state that a Site has no devices; what is true is that the M1
  Foundation schema has nowhere to put one. Causal step 4 adds them, and both
  the API test and the substrate state the absence in those terms.
- Frontend: `frontend/src/sites/SiteConfiguration.tsx` and
  `deriveSiteConfigurationView` are the configuration surface, and
  `frontend/src/sites/useSiteRecord.ts` is the one-Site read both site
  surfaces share. The hook carries T007's identity pinning, so the second
  surface could not reproduce that defect.
- `SITE_CONFIGURATION_ROUTE_PATH` is built on `SITE_DETAIL_ROUTE_PATH`, so a
  configuration is addressed under its Site. The guard looks for that shape
  rather than for any configuration route: a path built on the Site's address
  has nowhere to put the identity it would have to drop to become a
  parameterless destination again.
- Operator navigation is `Operator home` and `Sites`. Both parameterless T002
  site frames are gone. The navigation-growth assertion is now stated against
  the T004 list as a baseline, so it catches an item added and removed within
  one slice as well as one added outright.
- The three undeclared facts - devices, signal mappings, control assumptions -
  are constants in the view model beside T007's three unavailable facts, with
  the same value-and-reason shape. The reason in each says the absence is a
  statement about the configuration document and not about the Site. This is
  the wording the second user-review checkpoint is being asked to settle.
- The architecture guard gained a configuration-component clause on the
  single-definition check and a parameterless-`/site-configuration` ban plus an
  identified-route vacuity clause on navigation truthfulness.
- Review fix: integration readiness and source health state what this build
  records, not what the Site has. "No integration is configured for this site"
  and "no source is expected to report" were claims no field backs, and a Site
  with a real integration arrives with exactly the same fields. Source health
  reads `Not recorded` rather than `Not applicable` for the same reason.
  Evidence availability is unchanged: that no evidence has been accepted is a
  fact about this build's own store. Both Site surfaces assert it.
- Review fix: `isSiteDetail` validates the Foundation's content and not only
  its metadata - `summary`, `components` as an array, each component's four
  fields, and a rating that is `null` or `{value, unit}`. A missing `rating`
  key is refused; only an explicit `null` is the document declaring no rating.
  A guard that stops at what one surface reads is a guard the next surface
  renders past, which is what happened here between T007 and T008.
- `frontend/src/sites/__tests__/siteDirectoryClient.test.ts` is the first test
  in the tree to exercise a client against responses rather than a fake: the
  three read outcomes, the request path, and eleven malformed bodies split by
  what each would do if it got through.

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
   validation is shape-only. Accepted by the user at the T006 checkpoint, and
   settled again on 2026-09-17: this is acceptable for storage/display, but real
   IANA membership validation must land before scenario timing, run windows,
   replay/evidence windows, scheduling, or analytics consume the value.
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
   only. Settled on 2026-09-17: add a focused integration test before the
   shared Site Foundation frontend/backend contract is materially expanded.
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

### From T008

1. The M1 Foundation carries components and nothing below them, so devices,
   signal mappings and control assumptions are rendered as stated absences. The
   task text asked for them as content. They do not exist to render, and the
   deviation and its reasoning are in `.agent/T008-review-packet.md`; the
   wording of the three absences is on the user-review list.
2. `Not declared` is new product language, written in this slice and not yet
   reviewed by the user. If the checkpoint changes it, it changes in one place:
   the three constants in `siteViewModel.ts`.
3. Integration readiness still has no field. Unchanged from T007, and now
   stated on two surfaces from one constant. Source health was settled again on
   2026-09-17: it must come from backed source/gateway observation,
   heartbeat/arrival evidence, and expected cadence, not from lifecycle or
   simulator provenance. Until then it stays not recorded/not backed.
4. Still no automated integration test binding the real frontend fetch clients
   to the backend. Fourth slice in a row. The configuration surface is the
   second consumer of the same client, so the untested seam now has two callers
   rather than one. Settled on 2026-09-17: add the focused integration test in
   or before the next slice that expands this seam, and do not defer it past
   T011.
5. `createSiteFlow.test.tsx`, the case-variant refusal case, failed once under
   heavy CPU contention on `main` during the T007 closeout and could not be
   reproduced in two further runs, one of them deliberately contended. No
   assertion text was captured. It predates this slice and is untouched by it.
   Worth knowing before trusting a single green run: it is the same shape as
   the defect `settledScreen` was written for, and that test does not use it.

## T009 - Shared visual vocabulary

What this slice settled in code.

`frontend/src/ui/` is the one visual vocabulary and a leaf. It holds
`tokens.css` (type scale, neutrals, rail, accent, four badge tones, spacing,
radius), `primitives.css` (the classes), and seven components: `AppHeader`,
`NavRail`, `Breadcrumbs`, `PageHeader`, `Badge`, `Panel`, and `DataTable` with
`FactList`/`Fact`. Before this slice the app had no stylesheet at all.

The values were read from `Docs/UI Design/Motivation/ScreenMockups.png`, not
invented: dark navy rail with a bright blue active item, white cards on a pale
blue-grey page, pill badges, one blue accent. Visual vocabulary only; no mockup
literal, control, column or rail item came with it.

Names in the primitives are deliberately generic - `DataTable`, `Panel`,
`Badge`, never `SiteTable`, `SitePanel`, `SiteBadge`. The T006 single-definition
guard flags a Site presentation component anywhere outside
`frontend/src/sites/`, so a Site-named primitive would fail it, correctly.

`tools/checks/ui-primitives.ps1` is a new seam with two clauses. Leaf
direction: the primitives import no shell code, no simulator code, no feature
flag and no Site substrate. Shared vocabulary: both the shell root and the
substrate must import the module, because a vocabulary nobody imports has been
forked. Five violations were proven to fail it.

`NavRail` owns no items. Both rails pass their own, so the operator rail and
the Lab rail cannot converge through the component they share. The Lab's items
are declared in `simulatorLabRoutes.tsx`, which is already the only module
allowed to spell a simulator path; `SimulatorLabShell` takes them as props and
names no path, so the gate chokepoint is unchanged.

The Simulator Lab has a rail for the first time, listing `Simulator Lab` and
`Site Templates` - the two destinations that already rendered truthful content.
The mockup's other eight rail items have no route behind them and are absent.

Badge tones are one per vocabulary and never shared: provenance, lifecycle,
origin, neutral. They differ in fill, border weight and corner radius as well
as hue, so the distinction survives greyscale, and every badge renders the word
it means so colour never carries meaning alone. A badge renders only where a
record supplies its value: template provenance stays plain text because a site
created from no template renders an absence there, and every stated absence on
Site Configuration stays plain text for the same reason.

`PageHeader` has no action or badge slot. `+ New Site` restyling is T011's, the
Site identity badge is T012's, and `Edit`/`Version History` are never rendered
at all, so the slots would have been machinery nothing fills.

The brand mark is drawn in CSS rather than as an inline `<svg>`, because
several screens assert no `svg`, `canvas`, `img` or `figure` exists in their
container and that guard is worth more than the glyph. Keep it that way.

What this slice leaves open.

1. Breadcrumbs are provided but adopted by no screen. Adopting them means
   changing settled back-link copy or adding a destination, both of which stage
   1 forbids. They belong to T011-T013 with the screens they describe.
2. Not rendered in a browser. Verified by the suites, the typecheck, the build,
   and by confirming the built stylesheet ships with the expected classes.
   Browser tooling was unavailable in the session.
3. Contrast is reasoned against WCAG AA and documented in `tokens.css`, but no
   contrast checker was run and no automated accessibility assertion exists.
4. Nothing proves a surface renders *with* the vocabulary rather than merely
   importing it. The guard proves the import; the rest is review-time.
5. `SiteConfiguration.tsx` carries a UTF-8 BOM, pre-existing from T008. It is
   invisible to the compiler and the tests and silently defeats line-anchored
   shell commands.

## T010A - Site Foundation fetch seam

What this slice settled in code.

The frontend/backend fetch seam is now a checked-in contract rather than an
assumption. `backend/tests/test_fetch_seam_contract.py` drives the real
application through `create_app` across six app configurations and captures
what every endpoint actually returns into
`contract-fixtures/site-foundation-fetch-seam.json`, 24 cases.
`frontend/src/__tests__/fetchSeamContract.test.ts` reads that same file back and
puts the three real clients in front of it, 26 tests.

Neither side imports the other. The fixture is the only crossing, which is what
keeps `tools/checks/dependency-direction.ps1` intact and why the fixture lives
at the repository root rather than inside either project.

The anti-rot rule is the load-bearing part, not the assertions. A normal backend
run fails when the captured responses stop matching what the backend sends, so
a contract change breaks the generator before it can quietly teach the frontend
tests a shape that no longer exists. Regeneration is explicit:
`ASSETOPS_UPDATE_CONTRACT_FIXTURE=1 python -m pytest backend/tests/test_fetch_seam_contract.py`.
A fixture nobody regenerates looks like coverage while proving nothing.

Seven backend guards sit beside the generator so that regenerating cannot
silently erase a distinction: an empty index is not an unreadable store, an
unknown Site is not an unreadable store, every create refusal still carries a
renderable `detail.message`, a closed gate serves no Lab route, a closed gate
does not reach Site reads, a template never acquires Site identity, and no
response carries evidence or simulator-truth fields.

Two facts the seam exposed, both previously unwritten.

1. The backend has two refusal envelope styles. `GET /api/sites/{id}` and all
   four create refusals return `detail: {code, message}`. The Sites list 503 and
   every template error return `detail: "<string>"`. The clients survive it
   because only the create path reads `detail.message` and the others branch on
   status codes, so this is an asymmetry rather than a defect - but it is now
   captured, and changing either style breaks the generator.
2. With the gate closed, an unserved Lab route and a genuinely unknown template
   are indistinguishable to the template detail client: both are 404, both
   become `not_found`. That is acceptable only because a closed gate serves no
   screen that could call it, and it is asserted rather than left implicit.

The fixture is read with `fs.readFileSync` from `process.cwd()`, not imported.
An import would make the bundler resolve a path outside the frontend project,
and `import.meta.url` is not a file URL under Vite's transform.

What this slice leaves open.

1. The seam covers the Site Foundation clients only. Any future client gets no
   coverage until its cases are added to the generator.
2. The fixture pins response shape, not backend behaviour under real stores. It
   is generated over fakes and a temporary store, as every other API test here
   is.
3. Nothing asserts that the app wires its clients with the same base paths the
   fixture records. The frontend test spells `/api/simulator-lab/...` itself,
   because the gate's chokepoint rule forbids importing those constants outside
   the gated module.

## T010 - Lab template and create surfaces to mockup quality

What this slice settled in code.

The Site Templates catalog is a canonical page: a search field, a site-type
filter, and a table whose five columns are the template document's own fields.
The filter's options are derived from the types the shipped catalog actually
contains, never from the site-type enum, and the whole toolbar is absent when
nothing ships. Offering a value nothing matches teaches a catalog the build
does not have, and a test fails if one appears.

The create flow is stepped: `Choose a template`, `Site identity`,
`Review and create`. Three steps because there are three stages of real input.
The review shows what the user supplied and which template it copies and stops
there, because source mode, configuration origin and lifecycle status are
assigned by the backend at creation; rendering them would predict a record that
does not exist, which a test forbids.

Refusals are placed against the field they concern by the backend's own refusal
code, in `REFUSAL_STEPS`. `TEMPLATE_NOT_FOUND` and `SITE_ID_IN_USE` each send
the flow back to the step that owns the field and mark the input with
`aria-invalid` and a described-by message; every other refusal renders where
the user is. Placement is never decided by reading the message text, which
would be a second copy of the identity rules in the UI. `CreateSiteResult`'s
refused branch carries `code` for this, and the code is never rendered.

`+ Add site` is the Lab's entry into the create flow, built by
`simulatorLabRoutes.tsx` beside the operator index's entry point. Two entry
points, one flow, one chokepoint, and no frame spells a simulator path.

The shared vocabulary gained toolbar, form control, step indicator and action
patterns. They live in `frontend/src/ui/` rather than in a Lab frame because
T011's Sites index needs the same search and filter row.

The step number is drawn by a CSS counter, not rendered as text, so the rule
that every digit inside `main` traces to a document or to user input stays
intact. Same trade as T009's brand mark. Keep it that way.

The template inspection view needed no change: T009 had already dressed it, and
its "a template is not a site" statement and absence of actions still pass
untouched.

What this slice leaves open.

1. Still not rendered in a browser. Third slice running, and this one is mostly
   visual: the toolbar, the table layout and the step indicator have not been
   looked at.
2. No client-side validation, deliberately. A user can reach the review step
   with empty fields and be refused by the backend at the end.
3. A refusal that names no field lands on the review step, where the offending
   input is not visible. Placing it better would mean guessing the field from
   the message.
4. Search covers name and template ID, not summary.
5. Filter state does not survive navigation away and back.
6. `SiteTemplatesFrame.tsx` and `CreateSiteFrame.tsx` were destroyed by a
   `git checkout --` used as an undo on uncommitted work during this slice, and
   rebuilt. Behaviour is asserted by the suite, but they are a reconstruction.

## T011 - Sites index to canonical screen one

What this slice settled in code.

The operator Sites index renders nine columns: name with identity, type,
location, mode, lifecycle, configuration origin, template provenance, last
analysed, actions. The set is a named constant in `SitesIndex.tsx` so a test
can assert it whole.

Nine rather than the seven the settled Sites index inventory in
`.ai/FEATURE_MAP.md` lists. That inventory omits configuration origin and
template provenance entirely, while T006's User Review Outcome records the user
accepting them as two of four separate provenance columns, and T011's own
criterion requires both to stay visible. The feature map's authority rule
settles it: where a user review has already redirected a surface, that decision
settles it. The inventory is the thing that should be corrected, not the screen.

Mode and lifecycle are adjacent and separate, each with its own tone. The
canonical mockup's single `Status` column is the error this screen exists to
correct, and a header matching `^status$` or naming both vocabularies now fails
a test.

`Last analysed` renders `NO_ANALYSIS_IN_WINDOW`, which is `--`. That is v6.9's
rendering for a site with no data in the window rather than a placeholder, and
it is a constant so that the day evidence exists there is one place that stops
being true. The column left the banned-evidence-header list; what that ban
protected is asserted directly instead, for every row and against digits and
time vocabulary.

Every filter's options are derived from the records present, never from the M1
schema's permitted values. `ANY` is the no-filter sentinel and cannot collide
with a value a record carries.

The Actions column holds `View` and no overflow menu. The mockup draws one; it
would open onto nothing, because every action it could hold is one M1 has
decided not to have.

`PageHeader` regained the `actions` slot T009 left for this slice, and renders
nothing when it is empty. The create action moved into it: same gated module,
same two flag states, same label the T006 checkpoint settled.

The subtitle is not the mockup's. "All sites (real or simulated)" contains a
word a gate-off build may not say, which three settled assertions check.

What this slice leaves open.

1. Not rendered in a browser since T010, and this is now the densest layout in
   the product. Column overflow, wrapping and the filter row at narrow widths
   are what tests cannot see.
2. Whether nine columns is readable is a product question this slice did not
   answer. The reasoning behind them is truthfulness, not density.
3. Filter state does not survive navigation away and back.
4. Search covers name and site ID, not location or template provenance.
5. No sorting. Canonical screen 1 implies sortable headers; sorting is a real
   capability and the scope limits forbid it, so rows appear in store order.

## T011A - Foundation naming and operator Site tab inventory

What this slice settled in code.

The read-only surface T008 built is called Foundation wherever a user meets it:
page heading, route, and the link into it. `configuration` stays as the domain
word, so `Configuration origin` and `Configuration is fixed at creation` are
unchanged, in wording as well as meaning. The rule is that the screen has a
product name and the document underneath it has a domain name, and they are
different words on purpose.

`SITE_FOUNDATION_ROUTE_PATH` and `siteFoundationHref` in
`frontend/src/shell/operatorSiteRoutes.ts` replace the configuration pair.
`LEGACY_SITE_CONFIGURATION_ROUTE_PATH` is declared beside them with no href
builder, deliberately: no caller should construct that address. It is
registered once, against `LegacySiteConfigurationRedirect`, which renders
`<Navigate replace>` and nothing else. The guard confines the string
`/configuration` to those two modules, so a link, tab or builder that reached
for the old address fails the architecture check rather than a review.

The operator Site tab row is `OPERATOR_SITE_TABS` in
`frontend/src/shell/operatorSiteTabs.tsx`: v6.9's eight, in order, each either
`kind: "destination"` with an href builder or `kind: "labelled_in_place"` with
nothing. Overview and Foundation are the two destinations. The six labels are
plain spans - no link, no button, no `aria-disabled`, no title, and no route
registered, which is asserted by requesting each lowercased path under a site
and getting `Page not available`.

Disabled is the state this row refuses. It says a capability exists and is
switched off; these are not built. That distinction is now enforced in the
guard, not just in review.

The inventory lives in the operator shell. The guard holds three things about
it: declared once, not under `frontend/src/sites/`, and carrying none of the
mockup's Lab run vocabulary (`Configuration`, `Devices`, `Gateway`,
`Ingestion`, `Events`, `Logs`).

The shared substrate gained its first extension slot. `SiteDetails` and
`SiteConfiguration` take `tabs?: ReactNode`, render it under the page header
and above the facts, and render it only in the loaded branch. The substrate
imports nothing from the shell and reads nothing from the slot. This is the
mechanism the feature map names under *Shared substrate consequence*; it exists
because the row's correct position is inside the shared region, and the only
alternative was rendering it above the page heading from the frame.

`.site-tabs` is in the shared vocabulary, with two treatments and no disabled
styling. A destination is a link and the current one carries the accent
underline that `aria-current` already states; a label is quieter so it does not
invite a click.

Internal names under `frontend/src/sites/` still say `SiteConfiguration`,
including the module, the component, `SITE_CONFIGURATION_HEADING_ID` and its
DOM id. Renaming them changes no rendered character and touches every test in
that directory plus both single-definition guard patterns. Every rendered
string and every route constant says Foundation.

T008's `Back to this site` link is gone; the Overview tab is the way back.

What this slice leaves open.

1. Not rendered in a browser. Eight tabs, two styled as links and six as
   quieter labels, is new chrome and whether the two treatments read correctly
   is a product judgement no test makes.
2. The six labels may read as disabled even though they are not. The fix if so
   is a treatment change, never a state change.
3. The row wraps at narrow widths rather than scrolling or collapsing.
4. There is still no breadcrumb anywhere in the product. A truthful Site crumb
   needs the loaded record, not the address, so it belongs where the record is,
   which is T012's dressing of Site Details.
5. The Foundation page has a panel also headed `Foundation`. v6.9 calls that
   content `Definition`, but the Foundation subtab row is T013's.
6. The `tabs` slot is one prop wide. T012 and T013 will want more positions.

What review corrected, and the lesson worth carrying.

Two of the five patterns in the tab row's disabled-affordance guard clause held
a literal `0x08` backspace where `` was meant, so they could never match.
Fixed in `ada4149`. The clause's own non-vacuity proof had passed, because the
single violation introduced tripped a third pattern in the same list and the
failure message names the clause rather than the pattern.

So: a guard clause built from a list of patterns is proved once per pattern,
not once per clause, and the violation used for each must be worded so no
sibling pattern can fire instead. A guard that silently stops matching is
invisible in exactly the way this project relies on guards not being, and this
one was caught by a human reading the file rather than by anything automatic.
Whether that class deserves its own seam - per-pattern fixtures, no control
characters in patterns, failure messages that name which pattern fired - is an
open Architect question the Planner declined to turn into a task.

## T011B - Shell and dense content overflow containment

What this slice settled in code.

Every table renders through `DataTable`, which wraps it in
`.data-table__scroll`, a region that owns the table's horizontal overflow. The
wrapping happens in the primitive rather than at each call site so a screen
cannot render a bare table by forgetting to, and a guard clause holds the other
half: a `<table>` element anywhere outside `frontend/src/ui/DataTable.tsx`
fails the architecture check.

The region is a named focus stop - `tabIndex={0}` plus `role="region"` labelled
by the heading the table already answers to - because a region only a mouse can
scroll hides its far side from a keyboard. Both are conditional on the caller
supplying `labelledBy`: an unnamed `role="region"` is not exposed as a landmark
and an unnamed focus stop announces nothing.

Only `overflow-x` is declared. CSS resolves the other axis to `auto` once one
axis scrolls, but the box has no height constraint, so it grows to its rows and
never produces a vertical scrollbar. Giving that region a height is what would
put rows behind an inner scrollbar.

`.app-shell > .app-frame` sets `min-height: 0`. `.app-frame` keeps its own
`min-height: 100vh` because `SimulatorLabShell` renders that frame standalone,
outside the shell. Two uses of one frame, and the nested one is the exception:
deleting the base rule would take the Lab's full height with it, which is why
the guard asserts both halves separately.

New seam, `tools/checks/shell-overflow.ps1`, registered as the eighth. Five
clauses: the region contains the inline axis; the standalone frame is full
height; the nested frame is not; no shell selector hides page overflow; every
table goes through the primitive. The fourth is the one that matters most -
`overflow-x: hidden` on the document is the tempting wrong fix, because the
scrollbar disappears and the content beyond it becomes unreachable rather than
contained. Hiding is not containing.

Each clause was proved to fail on its own, worded so no sibling clause could
fire instead. That is the T011A lesson applied.

Nothing was dropped to make anything fit, and that is now asserted here rather
than only in the slices that introduced each inventory: nine Sites index
columns, eight Site tabs with no menu, toggle or hidden element, both rail
labels.

What this slice leaves open.

1. Nobody has seen the fix work. jsdom has no layout, so no test here can
   observe a scrollbar; everything asserted is structure and CSS text. This
   needs a browser before it is believed.
2. At exactly 1280px the Sites index table will probably still scroll inside
   its region. The table's floor is roughly 950-1100px and the rail and padding
   take about 250px more. That is the intended behaviour; closing it would mean
   changing density or dropping a column, which the policy forbids.
3. No affordance says more columns exist to the right of the region. That is a
   design addition, not a correction.
4. The tab row wraps rather than scrolling, so it has no overflow owner. A
   wrapping row cannot overflow, and a wrapped tab is visible where a scrolled
   one is not.
5. The unsupported-viewport state the policy permits is not built. It is new
   chrome that makes a claim and should have its own slice.
6. No breakpoint tokens were introduced, so the conditional breakpoint-token
   seam in the guard table remains unshipped.

## T011C - Site tab row treatment

What this slice settled in code.

A destination looks like a link because it is one. `.site-tabs__link` no longer
overrides the colour, so it inherits the accent every other link in the product
uses, and the current tab is told apart by weight and underline rather than by
being the only thing that is not grey.

That override was the defect. T011A styled a destination `--text-secondary` and
a label `--text-muted`, five percent apart, and the user read the whole row as
disabled. Nothing was disabled; the treatment said otherwise, which is a
reminder that the three-state rule is only as true as its rendering.

Two signals now, not one. A divider marks where the destinations end, and a
sentence under the row says how many aspects have no content in this build yet,
so the distinction holds in greyscale and for a reader who does not know that
grey means unbuilt here.

The sentence counts rather than names. The first version listed all six under a
row that had just shown all six, and the user's browser pass called it heavier
than the row it was explaining. It reads "Six aspects of a Site have no content
in this build yet." - `of a Site`, not `of this Site`, because no aspect is
missing content because of anything about the site on screen, and the shorter
phrasing must not become a claim about that particular site.

`labelledAspectsSentence` derives that sentence from the tab inventory and is
exported with the inventory as a parameter, so tests can hand it arrangements
this product does not have yet. An aspect promoted to a destination leaves the
sentence in the same change that moves it. A written-out list would have gone
stale the first time an aspect got content, and the screen would then have said
something has no content while the tab beside it opened that content. It
returns null when nothing is labelled, so the day every aspect has content the
sentence disappears rather than becoming an empty claim.

The sentence states what this build contains and never what a later one will.
`coming soon` and its family stay banned, and the guard enforces it inside this
module - it caught a code comment that explained the ban by quoting the banned
phrase, which is incidental evidence that the `ada4149` repair holds.

The baseline rule moved from `.site-tabs` to `.site-tabs__list`. The sentence
lives inside the same landmark, and a border on the nav would have drawn itself
under the sentence, leaving the active tab's negative-margin underline against
nothing.

What the user confirmed, and what is still unseen.

This row was seen. The user rendered it, reported the six read as disabled,
chose the treatment, rendered the result, and confirmed the row reads correctly
with only the sentence to shorten. That is the whole reason this slice exists,
and it is settled. What remains unseen belongs to T011B, not here: whether
chrome stays anchored while a table scrolls, and whether an empty operator page
with the gate open still runs past the viewport.

What this slice leaves open.

1. The correction may overshoot: two accent destinations could make the row
   read as all links. Not raised by the user, and not something a test sees.
2. The divider is a border rather than an element, so the grouping is visual
   only and the sentence is the whole non-visual channel.
3. The sentence sits inside the nav, so a reader skipping navigation skips the
   explanation with it.
4. Colour and divider have no guard clause. Consistent with the viewport
   policy, which leaves exact visual fit to review, but it means a future slice
   could regrey the row without anything failing except a human looking.

## T012 - Site Details to canonical screen two

What this slice settled in code.

The Site page is titled by `site_id`, with the display name beneath it and the
mode badge beside it. What addresses a site titles its page; a name is a label
on the thing rather than the thing. The id rendered is the record's, so a
case-variant address still resolves to one spelling on screen.

Breadcrumbs exist for the first time. The shell names the parent, because where
a surface sits in a route hierarchy is a shell's fact about its own routes, and
the substrate appends the Site from the loaded record. That split is what T011A
could not do: a crumb built from the address would have rendered `mg-002` on a
page showing `MG-002`. `Back to Sites` is gone, superseded by the crumb.

`PageHeader` gained the `badge` slot T009 deferred to this slice.

Quick actions is where the three-state rule becomes markup, and it carries two
different rules at once.

- The gate rule is about existence. `Open in Simulator Lab` and `Start
  Simulation` come from `simulatorLabSiteActions` in the one gated module,
  which returns an empty list when the flag is off, so a gate-off build renders
  no control, no label and no hint that a developer workspace exists.
- The sequencing rule is about eligibility. With the flag on those two render
  disabled, naming the causal step that would make them work.
- `View Live Data` obeys only the second rule. It is not a simulator
  capability, so it is the substrate's, renders in both gate states, and is
  unavailable for an evidence reason rather than a Lab reason.

Getting either rule backwards looks like a detail and is not: a gated control
rendered disabled leaks the existence of a developer workspace into a build
that has none, and a sequenced control that disappears hides a capability the
product intends to have.

Every disabled control carries its prerequisite as visible text tied by
`aria-describedby`, never a tooltip: a disabled button takes no focus, so a
tooltip on one is a reason a keyboard cannot reach. Everything M1 decided
against stays absent from the DOM, because disabled would read as soon.

The substrate gained its second and third slots, `parentCrumb` and
`quickActions`. It still imports no shell code, no simulator code and no
feature flag, and carries no discriminant. With the slots empty - the shape a
substrate test renders and the shape a gate-off build produces - the panel is
still correct rather than an empty frame.

Four inherited assertions moved and none was loosened. "No control renders"
became "no enabled control renders", which also requires every control to be a
button. "Identical markup in both gate states" became identical Site facts,
comparing everything but the Quick actions panel, with a stripper that throws
when it finds no panel so it cannot pass by deleting both sides. "Names and
reaches no simulator surface" split into an absolute reachability claim in both
states and a naming claim scoped to gate-off, plus a new positive assertion for
gate-on. The heading assertions followed the title to `site_id` and gained the
display name beneath it.

What this slice leaves open.

1. Not rendered in a browser. Three disabled buttons each with a paragraph of
   reason may be the heaviest region on the screen.
2. A disabled button takes no focus, so a keyboard user tabs past all three
   actions. The reasons are visible text and are read in document order, but
   they are not reachable by tabbing to the control they describe.
3. The mode badge appears twice, in the identity header and in the provenance
   panel. Both are true; a reader may wonder whether they are one fact.
4. The prerequisite strings are authored prose about the product's own
   sequencing, not derived facts. They will need revisiting as those steps land.
5. The Site information panel keeps the heading id
   `site-detail-identity-heading` while its heading text changed.
6. `site_id` as the page title is a visible change to a screen the user has
   already seen titled by the display name.

What review corrected in T012.

The `Site information` panel did not carry the facts the task assigns to it:
Lifecycle sat with provenance, and the foundation's version and validity had a
panel of their own. They moved. Mode, configuration origin and template
provenance stayed, because those describe where evidence and documents come
from rather than the site itself.

The reason it went unnoticed is the part worth keeping. Every fact was asserted
with a helper that searched the whole container, so a fact could be anywhere on
the page and still satisfy a criterion that names a panel. Panel membership was
never tested, only presence. The assertions now scope by heading id and throw
when there is no panel to scope to.

Proving that took two attempts and the first was wrong. Deleting a fact fails
plenty of assertions and proves nothing about membership; the scenario the
finding describes is a fact still on the page in the wrong place. Moving
lifecycle back to provenance leaves every global assertion green and fails only
the two scoped ones, which is the proof that was needed.

Rearranging panels put a settled seam at risk: the mockup collapses lifecycle
and mode into one `Status`, and T007 placed them adjacent so a reader could see
they were not. Adjacency was never what carried it - separate terms, values and
tones are - so the separation survived the move, and the doc comment claiming
they are adjacent rows was corrected rather than left to go stale.

## T013 - Foundation to canonical screen three

What this slice settled in code.

The Foundation subtab row is `FOUNDATION_SUBTABS` in
`frontend/src/sites/FoundationSubtabs.tsx`: v6.9 line 2117's five, with
`Changes` filtered out. It lives in the substrate rather than a shell, and the
distinction from the operator Site tab row is real. Which aspects a workspace
divides a Site into is a shell's opinion; what a Foundation is made of is the
same whoever renders it, so both shells will present these four.

`Changes` is absent in every state, not labelled in place. v6.9 lines 2149 and
2225-2228 make it an intervention and change-effect capability rather than the
mockup's `Version History`, no configuration-change model exists, and the T008
checkpoint removed that territory. Labelling it would name a capability whose
eventual meaning is not the one a reader would assume, which is worse than
naming nothing. The guard holds it.

Definition, Topology and Controls are fragment links to sections on this page.
Not routes, because the content is all on one screen and a route would be a
second address for something already here; not a client-side switcher, because
that would hide content with no reason to be hidden. Readiness is labelled in
place with no section to point at, and a test asserts no heading anywhere is
named `Readiness` - an empty panel for it would be the placeholder the task
forbids.

The panel headed `Foundation` under a page titled `Foundation` is gone. T011A
left it deliberately and named this slice its owner. It is `Definition` now and
carries what that subtab is supposed to carry - identity, summary, validity and
provenance - rather than being scattered across three panels the row does not
name.

`keyParameters` is filtered on the record, not on the rendered string. A
component with no declared rating produces no parameter at all, and the panel
does not render when nothing is rated. The components table states which
components declare no rating, in words, which is a fact about the document; a
blank line in a parameters list would read as a property of the site.

Breadcrumbs generalised T012's prop: both Site surfaces take
`parentTrail(siteId)` rather than a single crumb, because Foundation's parent is
the Site and only the substrate knows how the record spells it.

T008's ban on every interactive element narrowed to a ban on acting, and gained
a stricter half: every anchor on the surface must be a fragment resolving to a
section that is actually on the page.

A proof lesson, from the same family as T011A's. The first attempt to prove
that subtab links resolve changed the shared id constant - which moves the link
and its target together, so by construction they cannot disagree and nothing
failed. An assertion guaranteed by the design is not proved by breaking the
design symmetrically. The real failure mode is a section that stops rendering
while its subtab stays, and that is what the second proof did.

What this slice leaves open.

1. Two tab rows now stack on this page, the Site tabs and then the Foundation
   subtabs. Whether that reads as a hierarchy or as clutter is unjudged.
2. Definition is eleven facts and two paragraphs. It may want splitting, which
   would mean revisiting what the criterion assigns to it.
3. Fragment links scroll; they do not filter. A reader expecting tabs may find
   that flat.
4. The sentence under the subtab row is hardcoded, unlike the operator row's
   derived one, because exactly one subtab is labelled in place. If a second
   ever is, it goes stale - the failure T011C's derived sentence exists to
   prevent.
5. The evidence-absence panel is deliberately not Readiness content, but a
   reader may still connect them.

What review and the Architect corrected in T013.

The Foundation row is section navigation, not a tab switcher. The Architect
settled that in its UI/UX hat after the user asked what clicking a subtab is
supposed to do, and `.ai/FEATURE_MAP.md` carries it: clicking locates a named
section on the same page and does not swap panels, route, or hide content. v6.9
and the mockup name and draw the row but say nothing about behaviour, so the
project owns it.

It therefore does not borrow the tab treatment. `.section-nav` is its own
pattern - a contents line labelled `On this page`, smaller and lighter, with no
underline rail and no active state, because nothing is current when every
section is on the page at once. Two stacked rows may share vocabulary but must
not ask a reader to infer two behaviours from one appearance.

`scroll-margin-top` on `.panel__heading` gives a section link somewhere
deliberate to land. The anchors target headings, so the margin belongs on the
heading and not on the panel.

The components table moved below Controls. It is not named by the row, and an
unlinked panel between two named sections makes the row misleading about where
a section ends. It also had a measured cost: with the table above it, Controls
could be reached only by the document clamping at the page bottom, landing
336px from the top while every other link landed at 24px. It now lands at its
target minus the margin, like the others. A test holds the principle rather
than the arrangement: no unlinked panel may sit between the sections the row
names.

The lesson worth carrying is about assertions, not layout.

`Node.textContent` concatenates descendants with nothing between them. A
word-boundary ban cannot match a word glued to its neighbour, so
`/\btopology\b/` never matched `...creationTopology...` and `/\bdiagram\b/` in
the same regex was dead with it - the ban holding the configured diagram out of
step 3 was checking nothing, and had been for several slices. `spacedText` in
`frontend/src/test/text.ts` joins text nodes with a space so a boundary ban
means what it says.

Ninety-three assertions across fourteen test files had the same hole and now
use it. None was hiding a live violation, which is the point: a ban can stop
working without anything failing, and nothing in the suite would have said so.
When a defect is a class rather than an instance, the sweep is the fix.

## T014 - Foundation topology, devices and signal mappings

What this slice settled in code.

The canonical `SiteFoundation` carries `topology`, `devices`, `signal_mappings`
and `control_assumptions` beside the T008 four. This is the first slice since
T008 that adds content rather than arranging it, and the shape of what it added
is the substance of the entry.

`backend/assetops_backend/sites/foundation_parsing.py` is one strict validator
for all four sections, called by the template parser and the Site parser alike.
That is stronger than the T008 "one strict parser" rule rather than a repeat of
it: the two parsers own different identity and provenance rules, but what a
Foundation declares below its component list is the same thing whoever wrote the
document, so it is checked by the same function. Two copies would have let a
template declare a topology the Site store refuses, and the Site it seeded would
be unreadable in the store it was written to. A test asserts the two modules
expose the same object, not merely that both validate.

`null` and `[]` are different facts and stay different all the way to the
screen. `null` is the document declaring none; an empty list is refused by the
parser, refused by the frontend response guard, and never sent by the API. The
reason is one sentence: `[]` renders as a table with a header row and no rows,
which says this site HAS no devices, and a configuration document is not
entitled to make a claim about the world. It is the only malformed body in this
tree that would not look broken, which is why it is refused twice.

References resolve or the document is refused. The component list is the only
component authority: a topology node, a device, a mapping and an assumption each
name a declared component, a connection names two declared nodes, and a mapping
names a declared device plus one of that device's own declared signals. A
mapping's component is deliberately separate from its device's - a site meter on
the bus describing the distribution load is the case that exists for, and a view
model taking the device's component instead would look right on every other row.

Signal identity is per device. Two controllers both reporting `ac-power` is
ordinary, and a globally unique spelling would turn every mapping into a naming
convention rather than a declaration.

Vocabularies are closed and small: `TOPOLOGY_NODE_ROLES`, `CONNECTION_MEDIA`,
`DEVICE_TYPES`, `SIGNAL_UNITS`, `CONTROL_ASSUMPTION_BASES`. `SIGNAL_UNITS` is
separate from `RATING_UNITS` on purpose - a nameplate rating and a reportable
signal are different kinds of fact, and one vocabulary would let `kVA` onto a
signal and `%` onto a rating. The topology role is `GENERATION`, not `SOURCE`,
because `source` already means where a Site's evidence comes from and the two
would have sat on one screen beside each other.

A control assumption is an identity, a name, the component it is about or `null`
for the site, its provenance, and a statement in words. No state, no setpoint,
no mode, no breaker position. A test scans every `frozenset` in `models.py` for
control-state values so that vocabulary cannot be settled in a schema name
before the T016 checkpoint sees the question.

The T008 stated absences survive, and their reasons changed. They explained the
absence by what the M1 schema could carry; this slice gives the schema somewhere
to put a device, so that explanation became untrue the moment it landed. They
now say what this site's document declares. A test bans the old wording: a
reason that is no longer true is worse than no reason, because it explains an
absence by a constraint the product no longer has.

On the screen, the tables are subsections of the Topology panel rather than
panels of their own, because T013 settled that no unlinked panel may sit between
the sections the subtab row names. `SiteDeclaredSection<T>` is the two-state
type behind them: declared content, or the absence with its reason. There is no
third state and no empty `entries`.

`tools/layout-evidence.mjs` measures every table on a page now, not the first
one, and visits Foundation at 640px. At 1280 and 1000 every table fits, so the
containment claim was a claim about an empty set - it would have passed on a
page whose regions did not scroll at all. At 640 all six overflow, each scrolls
inside its own region, the document does not, and an explicit claim asserts the
set is not empty so the check cannot go quiet as content narrows.

A proof lesson, in the same family as T011A's and T013's. Putting diagram
vocabulary into the connections caption failed only the declared-state ban; the
inherited undeclared-state ban did not notice, because that caption does not
render when topology is `null`. A ban written against the screen as it was is
not a ban against the screen as it becomes, and the slice that fills a screen
with new content is exactly when the old bans stop being exercised by the case
they were written for.

What this slice leaves open.

1. Six tables on one screen, and nobody has judged whether it reads well. T013
   already left the two stacked rows unjudged; Topology is now four tables and a
   paragraph.
2. `node_id` and `component_id` carry the same string in the shipped template,
   so the nodes table shows two columns of identical values. The schema keeps
   them separate and the parser assumes nothing, but it may read as a redundant
   column rather than as two identities that coincide.
3. Identity columns are rendered in every table because a later diagram,
   evidence record and mapping version are keyed on them. Whether they earn
   their width is unjudged.
4. `TOPOLOGY_NODE_ROLES` has seven values chosen for one archetype. A cold-chain
   site will need more, and the closed set makes that a deliberate edit.
5. No component-level `role` axis was added. `component_type` is already the
   canonical component vocabulary and the current template needs no second one;
   if the Architect intended a distinct component role, it is additive.
6. The template API response still carries only `site_type`, `summary` and
   `components`. The template store and parser carry all four sections - that is
   what the create flow copies - but nothing on the Lab's template surfaces
   renders them, and a field does not reach the wire before a screen renders it.
7. No migration path for a stored Site. Fine while M1 ships zero Sites and
   configuration is fixed at creation; a real question the first time the schema
   changes after anyone has data. Pre-T014 local dev Sites still parse and
   render stated absences.
8. Document bounds rose to 8,000 nodes and 96,000 characters on both families,
   because the expanded template no longer fits the old budget. Nesting depth is
   unchanged at 8 and the deepest path reaches 6.

What review corrected in T014.

The document bounds were relaxed on a false premise - `MAX_DOCUMENT_NODES`
2,000 to 8,000 and `MAX_DOCUMENT_TEXT_LENGTH` 64,000 to 96,000, justified by an
expanded template that in fact fits the old limits five to six times over. Both
restored.

Restoring them exposed three cardinality caps that could never fire.
`MAX_DEVICES` was 128 while the node ceiling refuses at 77 devices;
`MAX_SIGNAL_MAPPINGS` was 256 while the ceiling refuses at 208. A document past
either was refused, but for node count, with a message naming nodes rather than
the collection an author had too many of - which tells them nothing about what
to remove. Both moved under the ceiling, to 64 and 160. The other four were
measured and were already reachable.

The direction matters and is the reusable part: **move the cap under the
ceiling, never the ceiling over the cap.** Raising a whole-document guard to
make a per-section guard reachable is how the bounds came to be relaxed in the
first place.

`TestEveryCapCanFire` in `backend/tests/test_foundation_content_parsing.py`
holds the property rather than the instances: for every cap, build a document
at `cap + 1` and require the refusal to name the limit rather than the node
count. Add a cap, and it is measured there automatically.

This is the third appearance of one family in this project - two guard patterns
that could never match in T011A, a diagram ban that could never match in T013,
and now caps above their own ceiling. The common shape is protection that looks
present and is not, and it is invisible precisely because the suite stays
green. Assume a new guard is dead until a violation makes it speak, and read
which guard answered rather than only that something failed.

Writing the reachability test reproduced the same defect once more. Its first
version asserted the refusal did not contain the word `nodes`, which fails on a
passing case: one collection is called `topology.nodes`, so its correct message
contains the word. It matches the ceiling's own wording now, `has more than N
nodes`. A check that matches the wrong thing fails as badly as one that matches
nothing.

Also recorded as a deviation rather than residual risk: a locally created Site
in gitignored `var/sites/` was deleted to make browser evidence deterministic.
Nothing in the slice required deleting rather than adding one, and data outside
version control is exactly where "do not discard unrelated user changes"
matters most.

## T015 - Hybrid mini-grid SLD view model

What this slice settled in code.

`frontend/src/sites/sldViewModel.ts` turns a validated Site Foundation into
either a compatible hybrid mini-grid diagram view or an explicit unavailable
result with a stable reason. It renders nothing, and nothing outside tests
imports it until T016 - which is why the production bundle is unchanged.

The archetype owns presentation and nothing else. Every node and connection in
the output traces to a Foundation id; nothing declared goes missing and nothing
undeclared appears. Binding is by canonical type and role, never by site id,
display name or array position, and separate tests assert the model decides
nothing from array order and nothing from a display name.

Unsupported topology is a closed set of unavailable codes, each with a stable
statement, each exercised by a document that produces it. An incompatible Site
returns no diagram at all rather than a partial one - a partial diagram is the
failure this state exists to prevent.

`SldValueSlot = Record<string, never>`: a type that cannot hold a field, frozen
at runtime. Runtime and evidence slots are named and empty on every node and
connection, and nothing binds either boundary.

The undecided vocabularies stay undecided. No control-state word appears in any
key or value, and the cold-room symbol is `COLD_ROOM_TREATMENT_CANDIDATE` with
an explicit unsettled marker rather than a silent decision - both belong to the
T016 checkpoint.

No new guard clause was added for the import criterion, and that was the right
call. The module lives under `frontend/src/sites/`, where the substrate guard
already bans shell, simulator and feature-flag imports, and there is no evidence
store in this codebase to ban. A clause banning a module that does not exist
cannot fail. The existing guard was proved to cover the new file rather than
assumed to.

The lesson this slice added to the family.

Proving the slot assertions found the fourth instance of one shape. Widening
`SldValueSlot` to `{ lastReading?: number }` failed **zero tests**: the objects
this build produces are still empty, still frozen, still carry no key, so every
runtime assertion passed. What changed was the contract - the type would then
say a reading may be attached, which is the claim the slice exists not to make.

Two `@ts-expect-error` assignments close it: while a slot may hold no field the
directives are used, and widening the type makes them unused so `tsc` fails.

So the family now reads: a guard pattern that cannot match (T011A), a ban
compared against text that cannot contain a boundary (T013), a cap above its own
ceiling (T014), and **a runtime assertion that survives the contract being
widened underneath it** (T015). When a claim is enforced by a type, test the
type, not only the values.

How it was built, which matters for how much to trust it.

The Implementer agent stalled before committing, before running any check, and
before writing a packet. Its work was committed verbatim and unreviewed by the
coordinating session so it could not be lost, then verified and extended from
the outside. 783 lines of new logic were reviewed by their own tests and by
proving, and the author verified none of it.

What this slice leaves open.

1. The archetype's lane and row assignment is tested for determinism and
   non-collision, not for whether the geometry makes a sensible diagram. T016
   inherits it either way.
2. `SLD_UNAVAILABLE_STATEMENTS` is authored prose about the product's own
   limits, and will need revisiting as archetypes are added.
3. Nothing here has been seen, because there is nothing to see.

What review corrected in T015.

Two findings, both from the family this project keeps meeting.

The test proving the Foundation screen renders none of the archetype's
vocabulary built its matcher with a `\b` inside a JavaScript template string.
That is a backspace character, U+0008, not a word-boundary escape: the regex
source began with character code 8, so it matched nothing and passed on a
screen rendering the token as readily as on one that did not. It is the same
escape as the two dead PowerShell patterns in T011A, in a second language.

`deriveSiteSldView` did not validate `device.component_id` or
`mapping.component_id` against the declared components, so a dangling reference
arrived as an `unplaced` entry and the model still reported `compatible`.
Unplaced and unresolved look alike and are not: unplaced means the component
exists and the diagram has nowhere for it; unresolved means it was never
declared. Both are `REFERENCE_UNRESOLVED` now.

The family, after five instances:

1. T011A - a guard pattern that could never match, `\b` becoming a control
   character in PowerShell.
2. T013 - a ban compared against `textContent`, which glues elements together
   so no word boundary exists to match.
3. T014 - three cardinality caps above their own document ceiling.
4. T015 - a runtime assertion that survived the contract widening underneath
   it.
5. T015 - `\b` becoming a control character again, this time in a JavaScript
   template literal.

The shape is always the same: protection that looks present, is not, and is
invisible because the suite stays green. Three habits fall out of it, and they
are cheaper than the reviews that found these.

- **Assume a new guard is dead until a violation makes it speak**, and read
  *which* guard answered rather than only that something failed.
- **When a claim is enforced by a type, test the type**, not only the values.
- **An escape that can become a control character is worth printing once.** The
  character code says in a second what review cannot see at all.

A sweep across TypeScript, PowerShell, Node and Python found no other live
instance. The only embedded control character in the tree is deliberate:
`test_site_parsing.py` uses a BEL to prove free text containing one is refused.

## T016 - Foundation SLD and device/signal presentation

What this slice settled in code.

`frontend/src/sites/SiteSingleLineDiagram.tsx` renders the configured Single
Line Diagram inside Foundation. It reads `deriveSiteSldView` and nothing else:
no component lookup, no device resolution, no signal derivation. Every identity
it draws came out of the T015 view model, and a UI test compares the rendered
node, connection and component id sets to the Foundation's for exact equality
in both directions. That chain - record, tested view model, renderer that adds
nothing - is why a diagram on this screen can be trusted to be a picture of the
record.

Two states, and neither degrades into the other. Compatible gets the drawing,
the diagram's contents in text, and a statement of anything the archetype has
no place for. Incompatible gets the refusal with its stable statement and its
detail, and no nodes at all. A test asserts the section holds exactly one of
the two, never neither and never both.

The archetype's own vocabulary stays off the screen. `BUSBAR`, `TERMINAL`,
`SOLID`, `COLUMN_FIRST` reach the DOM as `data-` attributes and never as text,
so T015's ban on that vocabulary is unchanged and is now exercised by a screen
that renders the diagram. The same trick is what lets a test bind to the
archetype's decisions without the product having words for them.

Every drawn node carries one line reading `Awaiting runtime/evidence`, from one
exported constant the drawing, the contents table and the tests all read.
Rendered rather than left blank: a gap beside a component reads as a value that
failed to arrive.

Where it sits is settled. The diagram is a subsection of Topology, not a panel
of its own, because T013's rule is that no unlinked panel may sit between the
sections the Foundation row names.

Narrowing a ban without loosening it. `withoutRegion` in
`frontend/src/test/text.ts` removes one named region and **throws** when the
region is not there. That throw is the whole point: a narrowing helper that
silently found no region would assert over the whole screen while the test's
name claimed a narrower scope, and on a screen that had lost the region the ban
would pass for the wrong reason. Three bans are narrowed this way - diagram
vocabulary, control vocabulary, cold-chain vocabulary - and each gained a
second half stricter than the original. The control one is the sharpest: the
vocabulary may be spoken in prose inside the block that asks the question, and
in no form that makes it a fact - no column, no cell, no badge, no label on the
drawing.

One assertion's purpose expired and was replaced rather than dropped. "No panel
body is empty" was written when an empty body could only be a region kept warm
for a diagram that did not exist. It now covers subsections too, and adds the
claim the old one could not make: the diagram section holds either a drawing
with nodes in it or a refusal with a reason.

`tools/checks/shell-overflow.ps1` gained the diagram's half of the table rule:
`.sld__scroll` must declare `overflow-x`, and every `<svg>` must render through
the diagram module. Both refuse to run vacuously. The svg scan skips comment
lines, because the first version reported AppHeader's own doc comment, which
mentions `<svg>` in a sentence about not having one.

`tools/layout-evidence.mjs` measures the drawing at 1280, 1000 and 640: drawn
with nodes and connections, region named and focusable, scrolls inside itself,
one empty slot per node, and never a drawing and a refusal together. At 640 it
asserts the drawing actually overflows, so the scroll claim is not about an
empty set.

Three smaller settlements. The mapping rows carry the `signal_id` the document
binds by, because a signal id is unique within its device only. Protocol
metadata and sample cadence - both named in the feature map, neither in T014's
schema - are stated once in words, with a `th` ban holding them out of a column
of dashes. The bus-cardinality refusal names the offending nodes instead of
counting them, because T016 renders that detail on a screen where no digit may
appear that the record did not supply.

The lesson this slice adds, and the one it re-learns.

Re-learned, as the sixth instance of the family: widening
`SldCandidateTreatment.settled` from `false` to `boolean` broke **zero** of 279
runtime assertions and was caught only by `tsc`, through an unused
`@ts-expect-error`. T015 wrote that habit down; T016 is the first slice to use
it on a new claim rather than to fix an old one.

New: **jsdom cannot see a diagram, so a diagram has to be looked at.** Three
defects survived a green suite and were found in a browser. A run that skipped
a lane turned at the midpoint of its whole length, drawing a line through
whatever that lane held. SVG text neither wraps nor clips, so a component name
longer than its box ran out of the side of it and across the drawing - fixed by
wrapping onto two lines, never by truncating, because a shortened component
name is a fact hidden to tidy a layout. And `Proposed treatment` sat on top of
the name it was a marking about. The agreement test then caught the wrap
immediately, which is the useful half: `textContent` across two `tspan` lines
gives `Generator fueltank`, the same gluing `spacedText` exists for, inside one
element instead of between two.

What this slice leaves open.

1. The lane and row assignment is still tested only for determinism, inherited
   from T015. The routing defect above is evidence that another arrangement
   could carry another such flaw that no test can see.
2. A component name longer than two wrapped lines overflows its box. Nothing is
   hidden; it would be visibly untidy. No name in the shipped catalogue does.
3. The drawing has no keyboard navigation of its own. Its region is a named
   focus stop and its contents are a table; reaching one node by keyboard is
   not possible and is not claimed.
4. `role="img"` hides the drawing's inner text from assistive technology. The
   `title` and `desc` name it and point at the tables, which carry every fact
   it draws, so a screen-reader user reads the tables and not the picture.
5. The two vocabularies are still open. They are now open *on the screen*,
   which is the difference this slice makes, but nothing is settled until the
   checkpoint is answered.

Local review data, not in the build. `var/sites/mg-002.yaml` (a cold room) and
`var/sites/mg-003.yaml` (two AC buses) were added beside the Site the user
created, because the shipped template declares no cold room and is drawable, so
neither reviewable state could otherwise be opened in a browser. `var/sites/`
is gitignored and `mg-001.yaml` is untouched.

## T016 - Foundation SLD and device/signal presentation

What this slice settled in code.

Foundation draws the configured Single Line Diagram, as an `h3` subsection of
the Topology panel rather than a panel of its own - T013's rule forbids an
unlinked panel between the sections the Foundation row names, and a diagram
belongs with the topology it draws.

`SiteSingleLineDiagram.tsx` reads `deriveSiteSldView` and nothing else. No
component lookup, no device resolution, no signal derivation: every identity it
draws came out of the T015 view model, which is already tested to introduce
nothing. Its own decisions are geometry, wrapping and glyph rendering. The
independent Reviewer confirmed that from the code rather than from the tests.

Two states, never neither and never both: a drawing, or the refusal with its
stable statement. When the diagram is incompatible the device, mapping and
topology rows still render, because a diagram incompatibility is not evidence
that the Site has no devices.

The archetype's own vocabulary reaches the DOM only as `data-` attributes, never
as text, which is why T015's ban on that vocabulary is unchanged and is now
finally exercised by a screen that draws.

Eight absence assertions were narrowed, none deleted, through `withoutRegion` in
`frontend/src/test/text.ts`. It removes one named region and **throws when the
region is absent**, so an exception that stopped existing cannot silently widen
the ban it was carved out of. Proved: removing `data-sld-region` fails nine
tests with that message rather than passing.

The bus-cardinality refusal names the offending nodes instead of counting them.
This screen allows no digit the record did not supply, and a count is a number
the build authored.

New guard clauses in `tools/checks/shell-overflow.ps1`: the diagram's scroll
region must declare `overflow-x`, and every `<svg>` must render through the
diagram module. Six new measured claims in `tools/layout-evidence.mjs`.

Three defects only the browser found: a connection routed through the battery
power conversion system, SVG text running out of its box because SVG neither
wraps nor clips, and a label colliding with the name it marks. None of them is
visible to jsdom, and none would have been found by reading.

The family, at six.

Widening `SldCandidateTreatment.settled` from the literal `false` to `boolean` -
the flag marking the cold-room treatment provisional - passes **every runtime
assertion**. Only `tsc` catches it, through an unused `@ts-expect-error`. The
Implementer found and closed that unprompted, which is T015's lesson arriving
before the defect rather than after it.

So the habits hold: assume a new guard is dead until a violation makes it speak;
read which guard answered; and when a claim is enforced by a type, test the
type.

What the checkpoint settled, and what it did not.

The cold-room treatment was proposed on screen and accepted. The breaker and
control vocabulary was presented with candidates considered and **not chosen**,
so accepting the screen chose nothing: it remains open, and it remains banned
everywhere outside the review block. Nothing in M1A draws a breaker, so nothing
was blocked. **The first slice that renders or stores a breaker state needs the
answer first, from the user.** T014's `frozenset` scan keeps that honest.

`SldCandidateTreatment` and its `settled: false` literal stay until a slice
removes the provisional marker deliberately. Removing it is a visible product
change and should be a commit that says so.

## T017 - Scenario catalog and Fuel Loss Event detail

What this slice settled in code.

`backend/assetops_backend/scenarios/` is the first new domain package since
Sites. It is built to the same shape and holds the same line:
`ScenarioDefinitionRepository` in `ports.py` speaks domain records and its own
error family - not found, identity conflict, configuration invalid, store
unavailable - and `adapters/` owns every path, file handle and YAML call. The
error family is parallel to the Site one and deliberately not a reuse of it: a
missing scenario and a missing Site are different facts about different
identity spaces.

There is no write path anywhere in the package. T017 ships no scenario creation
flow, so neither store has a create method and the port has none to implement.
That is structural, not a convention, and `tools/checks/configuration-persistence.ps1`
holds it: writes are allowed only in the one Site user-store adapter, so a
write appearing in any scenario module fails the build.

Two stores, one `scenario_id` space, no overlay and no precedence. Duplicates
within a store are caught by the document reader, which is the only layer that
can see two files; duplicates across stores are caught by the composite. Both
fail on list and on read - a read that quietly picked a store would be
precedence arrived at by accident.

`config/scenarios/fuel-loss-event.yaml` is tracked and read-only at runtime,
and unlike `config/sites/` the shipped scenario store deliberately does NOT
ship empty: with no create flow, an empty store would leave a fresh checkout
with nothing to inspect. The guard asserts both asymmetric expectations rather
than tolerating either.

The parser/service split is the load-bearing seam and it was an Architect
finding before it was code. `scenarios/parsing.py` validates the SHAPE of the
target-site declaration - including the policy-shape rule, where each field is
individually well formed and only the combination is wrong - and never reaches
into Site storage. `ScenarioDetailService` resolves the declared `site_id`
through `SiteRepository` and returns one of four target-resolution states.
Removing a Site therefore makes a scenario's target unresolved; it does not
make the scenario unreadable, and a test asserts the timeline still renders in
that state.

Public authoring data and private test-oracle expectations are separate parsed
fields on `ScenarioDefinition` and separate payload builders in
`simulator_lab_api.py`. The public builders never name the private field, so
they cannot leak one by omission. Proved with a sentinel that is present in the
private payload and absent from the public one, so the assertion cannot pass
because the sentinel was never there.

The breaker/control vocabulary protection grew and the banned list moved to
`backend/tests/control_vocabulary.py`, read by both scans. It now covers the
scenario domain model, the parser's key vocabularies, the shipped definition
and `backend/tests/scenario_fixtures.py`. It compares TOKENS, not substrings,
and scans schema positions only: every mapping key, plus every string value
spelled in upper snake case, which is exactly how this project spells an
enumerated value. Prose is not schema, so a description may use the word
"closed" in English while a category may not. The ban is unconditional: the
taxonomy is typed, because the parser refuses an unsupported value.

Four deliberate violations proved it: a banned category in the model, a
`breaker_position: CLOSED` parameter key in the shipped document, the same key
in the fixture, and `BREAKER` as a Foundation `DEVICE_TYPE`. Each failed
naming the offending term.

`tools/checks/configuration-persistence.ps1` is now stated once and applied per
configuration domain rather than written out twice. Four deliberate violations
proved the scenario half: a scenario adapter imported outside its composition
module, `import yaml` above the scenario adapter layer, a `.mkdir(` in the
shipped scenario store, and the shipped definition removed.

`frontend/src/ui/ReviewProposal.tsx` is a new primitive whose TYPE requires a
question, a proposal, what is already settled, and what accepting and
redirecting mean. T016's checkpoint put candidates on screen with no proposal
and settled nothing; a region that cannot be rendered without a proposal is the
structural answer to that.

The family, at eight, and the eighth is the one worth carrying forward.

**A proof can pass for the wrong reason, and then it has proved nothing.** The
vocabulary scan read mapping keys and upper-snake enum values. A scenario
parameter key is neither: it is the lowercase identifier in the `parameter_id`
FIELD. So `parameter_id: breaker-position` passed the guard and the parser, and
so did `event_id: auto-mode-change` and a `scenario_id` built the same way.

Four deliberate violations did not find it. The reason is the lesson: the
parameter proof added `breaker_position` as a mapping KEY, and the strict
parser already refuses unknown mapping keys, so the document was refused before
the vocabulary rule was ever consulted. It failed, it failed loudly, and it
measured a different guard. **A deliberate violation has to be one the rest of
the system would otherwise accept.** An independent reviewer found this, not the
proofs.

The fix moved the banned list into product code at
`assetops_backend/control_vocabulary.py`, so `scenarios/parsing.py` and
`scenarios/identity.py` refuse a banned identifier at parse time rather than
the rule living only in a scan that might not reach the position it protects.
The scan gained an `identifier` position kind, and
`TestTheIdentifierAuditIsComplete` makes the audit permanent: every `*_id`
field in the scenario schema must be classified as scenario vocabulary or as a
reference into another identity space, and a new one fails until somebody
decides which. Fixing only the position the review named would have left the
next one.

The ninth, found by a proof in the same pass.

The invented-digit assertion took three attempts.
`digitsInRecord()` compared digit RUNS against the record's runs, so an
invented `7` matched a real sequence number - a deliberate "all 7 categories"
passed. Carving out the containers that hold record values failed for the
complementary reason a reviewer named: those containers hold authored text too,
so a static digit in a table heading was removed wholesale. What holds is at
leaf level: every text node is either exactly a string the record supplies, or
carries no digit at all, asserted in both directions so the expectation cannot
be padded.

Then the proof of THAT found a third thing: a digit inserted into the
`No earlier version` fallback still passed, because the loaded fixture takes
the other branch and the fallback never rendered. **Authored text that no test
renders is authored text no assertion covers, whatever the assertion says.** A
second record that takes every fallback branch, and carries no digit of its
own, closed it.

So three habits, in the order they were learned the hard way: break the thing a
guard protects in the cheapest way a careless author would; check that the
break reaches the guard you meant rather than some earlier one; and check that
the branch you broke is a branch the test renders at all.

What the checkpoint proposes, and what it does not settle.

Three `ReviewProposal` regions on `/simulator-lab/scenarios/fuel-loss-event`:
`scenario-versioning` in the identity panel, `scenario-event-taxonomy` under
the timeline and its legend, and `scenario-public-private-boundary` in the
private expectations panel. Each states a proposal, not a menu.

Until the user answers, the values in `EVENT_CATEGORIES`,
`TIMELINE_ENTRY_KINDS` and `SCENARIO_VERSION_FIELDS` are provisional in
meaning but strict in enforcement: the parser refuses anything outside them.
T018 and T019 stay non-implementable until the Review Outcome is recorded.

## T018 - The executable scenario contract

What this slice settled in code.

Scenario content now has two orthogonal axes. `entry_kind` and `category` say
what sort of authored item something is; `execution_role` says what an
executor may do with it. Collapsing them would make a row's meaning depend on
who is reading it, which is exactly the ambiguity T017 left open.

Four roles: `CAUSAL_INPUT` initializes or changes private world state and is
the only one that may; `FORCING_INPUT` is an exogenous condition on the world
or on the reporting path; `REPORTED_OBSERVATION` arrives through a named
source; `NON_EXECUTABLE_CONDITION` is description nothing consumes.

The guarantee "an observation never prescribes private world state" is
structural, not a rule to remember. `ROLES_BY_ENTRY_KIND` refuses an evidence
condition that tries to be a cause. A reported value may carry no `ownership`
block and no `state_effect`, so there is no field it could arrive in as an
initial value or a transition. `initialization_inputs` and
`state_transition_inputs` are built only from causal inputs. Three layers, and
a deliberate violation had to be applied at the third to measure the contract
test at all - relaxing the parser rule tripped a different guard first, twice.

`scenarios/execution.py` is a new module and it holds what the roles commit
the product to, because those semantics are the same for every scenario and
are versioned simulator rules rather than authoring: canonical units, dispatch
rules, bound cases. It converts through exact ratios rather than floats, so
14 L/h over 240 min is 56.0 and not 56.00000000000001 - a screen showing the
second would state a precision the scenario does not have.

`reconcile_reported_observations` lives there and is contract arithmetic, not
a kernel. No clock, no timestep, no state record, no output for any instant
the scenario did not author a reading at, and it declines to answer when a
causal window is still open rather than apportioning half an effect. The
module docstring says so, and a reviewer should keep checking it: the scope
limit that forbids a kernel is the reason the line matters.

Bound behaviour has three policies and the absent fourth is the point: there
is no `SILENT_CLAMP` and no `DISCARD`. `invalid-rate` is the one of four cases
decidable without executing anything, so the parser enforces it end to end - a
negative or non-finite quantity in a non-negative dimension is refused when
the definition is read.

Cadence is declared and never derived. A device source says `NOT_DECLARED`, an
operator record says `NOT_APPLICABLE`, and the vocabulary has no value meaning
"the scenario declares it". The prohibition is enforced where a cadence would
actually be written: a duration parameter on a reading, refused by name. That
Foundation declares no cadence is checked rather than asserted - a test pins
`DeviceSignal` to exactly `signal_id`, `display_name`, `unit`.

`ScenarioDetailService.resolve_observation_sources` follows the target-site
split exactly: the parser validates that a device-signal source names a
well-formed device and signal, and the service resolves them against the Site
store into a screen state. A missing device is an unresolved source, not an
unreadable scenario.

The identifier audit widened from `*_id` to `*_key`. A world state key is an
identifier this domain coins and renders as the name of a thing, and
`state_key: breaker-position` would have read as perfectly natural to an
author - the same hole the T017 review found in `parameter_id`, one field
along. Proved by putting `breaker-position-availability` in the shipped
document and watching both the parser and the scan name `BREAKER`.

The shipped Fuel Loss Event's numbers are unchanged and they do not agree.
430 L initial, less 56 L over the dispatch window, less 120 L removed, is
254 L at both reading offsets, against 155 L reported and 150 L
hand-recorded. Both readings are now classified as reported observations from
a named source, so neither prescribes tank state and the contract is coherent.
What it also does is say the difference out loud, with quantity and sign, and
leave the resolution to review. Editing a number into agreement would have
settled a product question by arithmetic. Two authored values did change
shape: `overcast-day` gained a 360-minute window, which is the distance
between two offsets the document already declared, and the free-text
`observed-signal` parameter was removed because `observation_sources` now
carries that identity machine-readably.

The tenth member of the family, and it is a layout one.

`minmax(8rem, auto)` on the `.fact-list` term column gives that track a
max-content growth limit, and grid hands a non-flexible track all the free
space it can absorb before a `1fr` track sees any. A long term therefore took
the whole row, the value column resolved to zero, and its text pushed the
DOCUMENT sideways: seventeen pixels of horizontal scroll at 640px, with the
rail going with it. The first cap made it worse by moving the overflow one
level down into the value column. **A cap has to leave the other column room
for its longest word.** Twelve rem measured clean. jsdom has no layout, so
neither suite could have seen any of it - only `tools/layout-evidence.mjs`
could, and only because the slice ran it.

What T018 deliberately does not do: no model profile, so nothing computes a
Draft status; no run, no trace, no kernel. Every executable input names the
state it needs and whether it is required, which is what makes that decision
possible for T019.

### What review round one changed, and the three lessons in it

Independent review accepted the slice with five findings, all fixed on the
branch. Three are worth carrying forward because each is a failure shape, not
a typo.

**A screen may not assert a guarantee the code does not hold.** The role
legend said only a causal input could reach private world state, and the
proposal asked the user to accept that, while a forcing input could declare
`initializes: true` and came back as the initializer of a world state. On a
`USER_REVIEW_REQUIRED` screen that is worse than a plain bug: accepting it
would have locked in a guarantee nothing enforced. The fix made the sentence
true rather than weakening it, because the stricter rule is also truer - an
exogenous state's value at every instant comes from its forcing profile,
including the first. `STATE_CHANGING_ROLES` had no consumer anywhere and its
only test asserted its own literal value; it now has two consumers that do
not depend on each other, and a test that measures both.

**A rule written for one position is a rule with positions left over.** The
cadence prohibition was enforced on a duration parameter hung on a reported
observation. Three neighbours were wide open: a top-level duration, a duration
on the entry forcing the reporting path, and a reading timed as a window. The
fix was not to add two more position rules. `min` and `h` stopped being
authoring units, so a duration has no unit to be written in anywhere, and the
closed unit vocabulary the parser already enforced does the work; separately a
reading must be a POINT. The packet had claimed "there is no field a rate
could occupy" while three fields could - so the claim is now true rather than
softened, and what the rule does not reach is stated: prose, which is English.

**A contract may not report a number the same contract refuses.** The
reconciliation summed every completed transition without consulting a bound
and, with the delivery moved before the readings, reported a declared 554 L
against a declared 500 L capacity under a column headed "declared causes
reach". Capacity and volume were two state keys with nothing connecting them,
so a `bounds` declaration now says which state a world value limits - declared
rather than guessed from a shared prefix. Reaching a bound makes the reading
`NOT_RECONCILABLE`, because applying the clamp is the kernel's. The
transitions are walked in completion order rather than summed, since a bound
is reached at a moment and a total that came back inside would hide it. Every
answer now carries a reason: a `NOT_RECONCILABLE` with none was three
different facts wearing one name.

The habit underneath all three: a guard, a sentence and a number each have to
be checked against the thing they describe, not against themselves.

### What round two left open

Re-review accepted the slice. It reproduced every before/after rather than
reading the packet, judged both departures from its own suggested fixes to be
better than what it offered, and confirmed the T017 vocabularies byte-identical
after a round that narrowed the unit vocabulary. Four findings, all Low, all
preferences or test-strength points, none an acceptance gap. They were not
fixed before merge and are the first cleanup available to a later slice:

- **Intra-instant ordering is load-bearing and undeclared.** SETTLED by T019.
  Transitions completing at the same offset are walked in authored `sequence`
  order, which is deterministic, but `DISPATCH_RULES` did not say so - and
  with the bound walk that order decides whether the contract answers or
  abstains. Two causes at one instant, authored either way round, give
  `NOT_RECONCILABLE` or `declared 454.0`. Never a wrong number, and the
  shipped document has no simultaneous transitions on one state. T019 made it
  observable from outside the contract, because the answer became a blocking
  reason persisted on a Draft, so it is now the `intra-instant-order` dispatch
  rule. The rule does NOT say authored order decides: the T019 checkpoint
  reversed that, and simultaneous causes are a group with a net effect whose
  order-dependence is decided exactly. The T019 entry has the reasoning.
- **The second initialization layer is real but unmeasured.** The role guard
  in `initialization_inputs` holds if the parser refusal is ever loosened -
  verified by constructing the record directly - but the branch is unreachable
  through `parse_scenario_document`, so no test exercises it. The same shape as
  the round-one lesson, one size smaller.
- **The contract-version test is honest but weak.** SETTLED by T019, as a
  side effect of the entry above. The fixture value and
  `EXECUTION_CONTRACT_VERSION` were both `1`, so a hard-coded `1` in the
  component would still have passed, and the backend asserted `>= 1`. The
  constant moved to `2` because the rule set gained a rule; the backend now
  asserts equality with it and the frontend fixture stays at `1`, so the two
  cannot be one literal by accident.
- **Two forward constraints live only in code comments.** A `POINT`-only
  reading has no shape for a metered `kWh` aggregate, which a later evidence
  slice will meet; and no duration has an authoring home outside
  `timing.duration_minutes` until a slice reopens that vocabulary on the
  record.

## T019 - Draft run setup

What this slice settled in code.

`backend/assetops_backend/runs/` is the third domain package, built to the
same shape as `sites/` and `scenarios/` and holding the same line: a port
speaking domain records with its own error family, one composition module, one
adapter layer. It is deliberately not a reuse of either - a missing run, a
missing Site and a missing scenario are three facts about three identity
spaces - and it is the second package in the product with a write path.

**Run setup decides one kind of thing, and Amendment 1 is what made that
true.** Every blocking reason is a statement about the SELECTED PROFILE:
a state it does not model, a role it does not support, a cadence or a
publication identity it does not resolve. A sixth kind was removed to make it
so. `OBSERVATION_NOT_ACCOUNTED_FOR` blocked a run when the causes a scenario
declared did not reach a reading the same scenario declared, and proposal (e)
took it out: run setup has no kernel, so whether declared causes reach a
reading is a statement about what a run would produce and not one it can
make. The shipped Fuel Loss Draft blocks on three reasons rather than five;
`BLOCKED` is unchanged as an outcome and is reached for a sounder reason. A
kind added later that is not about the profile's ability to execute an input
is that mistake returning, and the vocabulary is pinned as an exact set for
exactly that reason.

`reconcile_reported_observations` still exists, still answers that question
for the scenario detail surface, and is labelled in the test suite as a
specification reference implementation
(`D-2026-09-21-specification-reference-implementation`). **Its expiry is a
condition, not a slice number**: it stops being an authority when a kernel
exists and the two are compared, which is T021's comparison, and it leaves
the repository when its last product-path caller goes - the
`observation_reconciliation` payload and the panel that renders it, whose
removal is Open Question 5 and undecided. No slice before that decision
treats the removal as in scope.

**The refusal line is the slice, and the T019 user review sharpened it into
a question about who failed to answer.** The scenario's declared owner has no
answer, so nothing can be frozen and no profile helps: refuse. The selected
profile cannot answer, so a different profile would: persist a `BLOCKED`
Draft. T019 was aligned to T020A rather than the reverse.

The observation that decides the hard cases: **a Foundation's answer is only
locatable THROUGH the selected profile's binding**, so failing to locate it is
a joint fact about the pair, and the profile is the half a person can change
on the setup form. Four failures therefore block - the profile declares no
binding, the binding matches nothing, it matches more than one thing, or its
unit is not the scenario's - and one refuses: the Foundation's value
disagreeing with the value the scenario states it declares, where both
declared owners answered and contradict each other. A profile pointing at
some other component that happened to match would be resolving a
contradiction by shopping for a value.

`INITIAL_VALUE_NOT_RESOLVED` carries all four, and the name is chosen for
that: it names the state the value is left in rather than the cause, so one
name covers four causes here and T020A's uncarried `MODEL_RULE` case without
rewording.

**The frozen identity has one absent case, and it is load-bearing.**
`FrozenInitializationInput.value` and its canonical restatement are nullable,
absent together, enforced when a document is read; the unit is not, because
the scenario declares it whether or not anything answers. **A `READY` run may
not carry an absent value**, asserted on the record beside the status
invariant - an absent value exists only because something blocked the run.
This was a protected-seam change, so nothing else about the identity's shape
moved.

 A refusal means the request could not be
frozen: something it names does not exist, does not resolve, is not well
formed, or would have to be invented. No `run_id` is allocated and nothing is
written, so there is nothing afterwards to inspect. `BLOCKED` means everything
was frozen and the run still must not execute: the Draft exists, is persisted,
and carries reasons. `runs/refusals.py` states it once, and the code has the
shape: everything in `_freeze` raises, everything in `_blocking_reasons`
returns. Every refusal test asserts the store is empty afterwards, because an
error raised after a write looks identical without that assertion.

Nine refusal kinds and six blocking-reason kinds, each a different fact with
its own code on the wire. The `BLOCKED` five for the shipped Fuel Loss Event
against the shipped profile are three unmodelled forcing states and two
unreached readings - the second pair being
`D-2026-09-21-scenario-execution-contract` applied as written, so **the
shipped scenario cannot reach `READY` in this build by construction**. `READY`
is proved against a fixture scenario instead. A later slice that resolves the
residual or widens the model profile changes that, and the test naming the
three unsupported states will fail when it does, which is the point.

**Nothing is defaulted, in either direction.** A parameter the scenario
declares `RUN_OVERRIDE` must be supplied by the run and a parameter the
scenario owns may not be overridden; a Foundation-owned initial value is
resolved through a binding the model profile declares, never by matching a
state key against a component by spelling, and a Foundation that disagrees
with the scenario's stated requirement refuses rather than silently winning.
Two components that both fit the binding also refuse: two answers to one
initial value is not something a run may choose between.

**Cadence, simulator source identity and gateway identity are structural.**
They are resolved in `runs/profiles.py`, which imports nothing from the Site
domain, and the two records that carry them may be constructed only there and
in the store's own document parser. `tools/checks/run-setup.ps1` holds both,
plus the identity chokepoint: the `run-` prefix is spelled in
`runs/identity.py` alone and one caller allocates.

**That guard scanned one directory for its first two rounds, and the
independent review disproved it.** A function in `simulator_lab_api.py`
deriving a cadence from a device display name passed 789 tests and passed the
architecture check, because the scan never looked outside
`backend/assetops_backend/runs`. It scans the whole backend package now, with
a vacuity assertion that fails if it ever reaches no module outside the run
domain. The lesson generalises past this guard: **a guard's scope is part of
its claim, and a module that describes itself as protecting the product while
scanning one folder is a false statement about a real check.** The ban is on the IMPORT
rather than on words like `display_name` or `lifecycle_status`, which collide
with the run's own fields - a ban with exceptions is a ban somebody widens.

A run identity is allocated from nothing: no Site, no scenario, no text, no
clock, no counter. The request has no field for one and a request that sends
one is refused by name, which is how "a scenario label never becomes a
`site_id`" holds one space further along.

Real IANA membership is checked against `zoneinfo.available_timezones()`, in
both directions: `Africa/Atlantis` is refused though it is shaped like a zone
and `UTC` is accepted though it is not. `tzdata` is a declared dependency
because Windows ships no database and a membership test against an empty set
refuses every real zone. "Not a zone" and "no database" are two different
failures and stay two.

`frozen_inputs` turns the identity into one row per value with its answerer,
and a test walks `dataclasses.fields(DeterministicIdentity)`: a field added
with no answerer fails the build rather than reaching a screen in a column
with nothing under it. The four answerers correspond one to one with T018's
`INITIALIZATION_OWNERS`, asserted, so a fifth owner on either side fails.

The persistence guard now registers a third domain. A run is not
configuration, but the seam is the same one, and the guard proved it by
failing with seven findings the moment the store appeared.

The eleventh member of the family, and it is the tenth one again.

T018 capped the fact list's TERM column because an unbreakable term pushed the
document sideways at 640px. T019 put an unbreakable VALUE in the same
component - a run identity is thirty-six characters with no break opportunity
- and the value column resolved to 103px against 230px of content: seventy-
nine pixels of horizontal document scroll, rail included. **A fix applied to
one column of a two-column component is a fix with one column left over.**
`.fact-list__value` now breaks anywhere, which is the right treatment for a
machine identity. Only `tools/layout-evidence.mjs` could see it, and only
because the tool was taught to fill the form and submit it first - the summary
does not exist until somebody does.

Three deliberate violations proved the new guard, each accepted by all 785
backend tests and caught only by the scan: the observation binding built
inline in the service with identical behaviour, an unused Site-record import
in the resolver, and the run identity assembled in the service. The third
found a hole in the guard: its vacuity check counted `def allocate_run_id(` as
a call, so "nothing allocates" would have passed on a tree where nothing did.

What T019 settled from T018's open list, and what the checkpoint reversed.

`intra-instant-order` is now a `DISPATCH_RULES` entry. Freezing run inputs is
what made the question decidable from outside the contract: whether the
reconciliation answers or abstains becomes a blocking reason **persisted** on
a Draft and read back, so the rule decides what a stored run says about
itself and belongs in the contract rather than in the stability of a sort.

**The first rule this slice declared was wrong and the T019 checkpoint
reversed it.** It said two transitions completing at one offset apply in
authored `sequence` order. Three things were wrong with that, and they are
the reason the replacement looks as it does:

- serialising two causes the author declared to happen together produces a
  level the state is never in, and the contract then abstained *on a number
  that does not exist* - the same family as the round-one finding where a
  contract reported a number the same contract refuses;
- `sequence` is an authoring and display field, and reading it as physics is
  the shape of the bound that used to be guessed from a shared prefix;
- it would have obliged T021's kernel to serialise sub-steps within one
  instant in document order and evaluate bounds between them, forbidding a
  net-change-per-step implementation, making bound behaviour depend on
  document position, and removing the metamorphic invariant
  `D-2026-09-21-causal-runtime-before-golden-traces` asks for - under that
  rule, reordering two simultaneous entries changes the trajectory. It also
  sat badly beside `quantity-across-a-window`, which already declares
  intra-step path independence for a single entry.

What replaced it: everything completing on one state at one offset is one
step with a net effect, and a bound is evaluated on that net. Order-dependence
is decided exactly rather than assumed, by testing the two extremes that
bracket every ordering - every increase first against the upper bound, every
decrease first against the lower. If the net itself ends outside a bound every
ordering does, so that is the bound case it already was. If neither extreme
reaches one, no ordering does and the net stands. Only when one extreme
reaches a bound and the other does not is the group genuinely ambiguous, and
then the contract abstains with `ORDER_DEPENDENT_GROUP`, a fourth
`NOT_RECONCILABLE` reason saying to separate the offsets. **Order is expressed
as time, not as position in a document**, and `accounted_by` is sorted within
each instant so the whole record is order-independent - asserted by comparing
two documents that differ only in the listing order of one pair.

The statement covers the case where BOTH extremes reach a bound, which the
code always abstained on and the first draft left unspecified - T019's review
found it, and under this contract's own bump policy an unspecified case is
one where two conforming kernels may legitimately disagree.

One thing about that rule is worth knowing before reading its history: **the
argument that first motivated declaring it no longer holds**. It was declared
because freezing run inputs made the answer a blocking reason on a persisted
Draft. Proposal (e) then removed that blocking reason, so the rule reaches no
run at all. It still belongs in the contract - it decides what the scenario
detail surface reports and what a kernel must do at a shared instant - but a
later reader should not take "a persisted run says it" as current.

`EXECUTION_CONTRACT_VERSION` is 2 and **the bump policy is now written beside
it**: a version moves when the space of behaviours a conforming
implementation may exhibit changes, including when it narrows, and never for
wording. That is stricter than "the rule set is what is versioned", which the
first draft said, and the difference has a cost:
`D-2026-09-21-causal-runtime-before-golden-traces` makes a provenance
mismatch REFUSE playback rather than fall back, so a version that moved on a
prose edit would force regeneration of golden traces that were never invalid.
Under that test the reversal moves nothing further - version 1 left the
instant unspecified, both drafts narrow the same space, and nothing ever
conformed to the first draft.

The version move also closed the weak contract-version test for free: it now
compares against the constant, and the frontend fixture stays at 1 so the two
cannot be one literal by accident. The other two round-two findings are
untouched and unaffected: the unmeasured second initialization layer, and the
two forward constraints that live only in code comments.

What T019 leaves open, for the slice that meets it.

- **A `MODEL_RULE`-owned initial value has no carrier.** Review finding L9,
  narrowed by the user review: it no longer refuses, it blocks with
  `INITIAL_VALUE_NOT_RESOLVED`, so the person gets a Draft to inspect. What
  remains is that no profile in this build can carry such a rule. **T020A
  adds the carrier.** No shipped scenario declares the owner.
- **Narrowing a stored vocabulary makes older Drafts unreadable, and the
  store fails closed.** Removing a blocking kind stopped every Draft written
  before it from parsing, and because `create_run` lists the store to refuse
  a duplicate identity, that stopped run creation entirely until the stale
  documents were deleted. Free on unmerged data; not free after merge. There
  is no migration path and no per-document quarantine, and one unreadable run
  blocks the creation of every other. Checking identity by file name would
  avoid it and is refused on purpose: identity is never read back out of a
  file name. T020 reads this store and meets the same posture.
- **The amendment to `D-2026-09-21-scenario-execution-contract`** for the
  reversed ordering rule is Architect's and is pending.
- **Four small things the re-review logged and left**, in the packet's
  residual risk with the reasoning: the frozen-table layout claim asserting a
  floor its wording outruns; the reason-set audit deriving membership from a
  name-suffix scan with a hand-written count, where the durable fix is
  exporting a vocabulary `frozenset` the way `BLOCKING_REASON_KINDS` is; a
  dead duplicate docstring in the execution contract tests; and the
  stale-vocabulary lockout's 503 saying the store could not be READ when it
  is readable apart from one document - the same collapse this project
  polices elsewhere, in copy this slice introduced.

Two lessons from the last two rounds, because both are about tests rather
than about runs.

**A guard's scope is part of its claim.** `tools/checks/run-setup.ps1`
described itself as protecting the product while scanning one folder, and a
reviewer disproved it with a function that passed 789 tests.

**An assertion that holds against a value the product cannot make proves
nothing about the product.** This slice met that three times: a fixture whose
loading sentence the screen never says, a fixture whose 503 message the
endpoint never sends, and a whole client tested only through a stub of its
own interface - so a duplicated sentence in the copy survived a full review
round. Stubbing an interface tests the caller; it never tests the thing that
implements it.

What T019 deliberately does not do: no execution, no step, no trace, no
staging, no Commit, no ingestion, no Replay, no analytics, no Findings. No run
inventory and no run detail surface either - the setup summary is returned
once and is not addressable, which is T020's to fix. A template-derived
scenario cannot have a run set up for it at all: a run is bound to a concrete
Site, and matching the Site's template provenance would be Site provenance
driving a run input.
