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
`observation_reconciliation` payload and the panel that renders it. That was
Open Question 5 and undecided; it is now
`D-2026-09-22-reconciliation-panel-retirement`, which puts the panel, the
payload, the reference implementation, `declared_bounds` and
`IMPLICIT_LOWER_BOUND_DIMENSIONS` in **T022**, with (f). No slice before T022
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
`FrozenInitializationInput.value` and its canonical restatement are nullable
and absent together; the unit is not, because the scenario declares it
whether or not anything answers. This was a protected-seam change, so nothing
else about the identity's shape moved.

Three invariants guard it and **all three live on the record**, because the
service cannot produce a violation and a hand-edited document can:

- a run is `READY` exactly when it carries no blocking reason;
- every absent value has a blocking reason naming **the same state**. The
  first version of this asked only whether the run carried any reason at all,
  and the final gate satisfied it with an absent value beside a reason about
  an unrelated profile identity. **An invariant that is weaker than its own
  docstring is the docstring making a promise the code does not keep** - the
  same family as a screen asserting a guarantee the parser did not hold;
- the two number fields are absent together. That was enforced only where
  documents are read, while the record's own docstring stated it as a
  property of the record.

The reason the contradiction case refuses while the four location failures
block is **structural, not a judgement about fixability**: the four leave the
value with no answer, which the record can represent as absent, and the
contradiction leaves it with two, which the record cannot represent at all.
A blocked Draft would have to freeze one of the two numbers. The earlier
reason - that a profile finding another matching component would be shopping
for a value - falls to a site that declares a second matching component whose
rating equals the scenario's, and is kept only as the intuition.

**That argument is now in the vocabulary.** The contradiction is
`INITIAL_VALUE_ANSWERS_DISAGREE` rather than sharing
`INITIALIZATION_INPUT_MISSING` with a value nobody supplied: an absence and a
contradiction are not the same shape, and the old name described the wrong
one while sitting one word from the blocking `INITIAL_VALUE_NOT_RESOLVED`
with nothing in either name saying which side of the line it was on. The new
name is the mirror of the blocking side - a run can carry "no answer" and
cannot carry "answers disagree" - so a reader knows from the name alone that
it cannot appear on a persisted Draft and must be a refusal.

A test asserts the refusal and blocking vocabularies share no string. The
near-collision one step away is older and was left: `COMPONENT_OR_SIGNAL_
UNRESOLVED` refuses while `INITIAL_VALUE_NOT_RESOLVED` blocks, so "unresolved"
is already on both sides. **This vocabulary has no naming rule that would
have prevented either collision**, and inventing one at the end of a review
round is not an implementer's call.

 A refusal means the request could not be
frozen: something it names does not exist, does not resolve, is not well
formed, or would have to be invented. No `run_id` is allocated and nothing is
written, so there is nothing afterwards to inspect. `BLOCKED` means everything
was frozen and the run still must not execute: the Draft exists, is persisted,
and carries reasons. `runs/refusals.py` states it once, and the code has the
shape: everything in `_freeze` raises, everything in `_blocking_reasons`
returns. Every refusal test asserts the store is empty afterwards, because an
error raised after a write looks identical without that assertion.

Ten refusal kinds and six blocking-reason kinds, each a different fact with
its own code on the wire. The three `BLOCKED` reasons for the shipped Fuel
Loss Event against the shipped profile are three unmodelled forcing states,
so **the shipped scenario cannot reach `READY` in this build by
construction**. `READY` is proved against a fixture scenario instead.

Both counts moved during this slice and an earlier draft of this paragraph
kept the old ones. It said nine refusals, before the contradiction split out
of `INITIALIZATION_INPUT_MISSING` as `INITIAL_VALUE_ANSWERS_DISAGREE` and
`INITIAL_VALUE_NOT_RESOLVED` joined the blocking side; and it said five
blocking reasons on the shipped Draft, which was true before (e) removed the
two unreached readings and is contradicted three paragraphs above by this
same entry. A later slice that resolves the
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
with nothing under it. `ANSWERER_BY_INITIALIZATION_OWNER` maps T018's
`INITIALIZATION_OWNERS` one to one, asserted, so a fifth initialization owner
with no answerer fails. **The second half of that assertion is a subset, not
an equality**: `FROZEN_INPUT_ANSWERERS` may hold a member no initialization
owner maps to, which is what lets T020 add `PUBLICATION_PROFILE` without
touching the correspondence. The docstring and the test name saying "the four"
are prose and are T020's to correct.

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

**A reason's `subject` is what makes two rows two facts.** A state the
profile does not model was reported once per execution role, differing only
in which role the prose named, so a reader counting rows counted one problem
twice. Reasons are deduplicated on `(kind, subject)`, and a reason that
really is one per role carries the role in its subject.

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

## T020 - Runs inventory and Draft shell

What this slice settled in code.

**The Drafts T019 writes are now addressable.** `RunInventoryService` in
`backend/assetops_backend/runs/service.py` reads the SimulationRun port and
nothing else, and sorts newest-first on `(created_at, run_id)` so the order is
total rather than merely usually right. Two Lab routes serve it,
`GET /api/simulator-lab/runs` and `GET /api/simulator-lab/runs/{run_id}`, and
`frontend/src/shell/RunsFrame.tsx` and `RunFrame.tsx` render them. A
not-found run and an unreadable store are different screens, because they are
different facts about different things.

**`READY` states what it does not assert, on the record.**
`READY_DISCLOSURE` and `readiness_disclosure()` live in `runs/models.py` and
derive from the execution status, so the payload a caller reads and the panel a
person reads carry one sentence from one place - a screen composing its own
would be a second place for the claim to drift. It names the condition that
retires it, a conformance test deriving the supported states from a kernel,
never a slice number (`D-2026-09-22-expiry-follows-the-condition`). `BLOCKED`
gains nothing equivalent: there is no claim to qualify.

**`PUBLICATION_PROFILE` is the fifth answerer.** The cadence and both
publication-identity rows said `MODEL_PROFILE` answered them and the
publication profile did. The correspondence assertion could not have caught it
- its second half is a subset, so a new member passes silently - so the durable
guard is
`test_no_row_names_an_answerer_its_own_detail_contradicts`, which checks the
property rather than the three rows that carried the mislabel, plus a two
device-signal-source case where a count of three would have been wrong.

**`cadence_resolution` was deleted rather than renamed.** It was a total
function of `source_kind` and `cadence_minutes`, and storing it bought a
fourteen-line parser biconditional that checked a record against a restatement
of itself. `provenance.py` branches on the two fields instead. The run document
parser tolerates unknown keys, so every Draft written before this stayed
readable with the dead key ignored - which is also a strictness gap the
scenario and site parsers do not have, recorded in the packet's residual risk.
`EXECUTION_CONTRACT_VERSION` did not move: this is a run-record shape, not a
scenario-document one (`D-2026-09-22-contract-version-scope`).

**A form default is a thing the screen says it chose.** `RunSetupFrame` now
defaults the interval, the timestep, the seed and any profile selection with
exactly one option, and renders `.field-default` inside the field - "Default,
chosen by this form: X" - tied to the control by `aria-describedby`. The mark
stays after an edit, because "the form chose 15 and you typed 30" is more
useful than a mark that vanishes when it stops being true. The interval's
length is derived from the scenario's own last moment plus one timestep,
rounded to whole steps, because the interval is half-open. The clock is
injected (`App -> simulatorLabRoutes -> RunSetupFrame`) so a test can pin the
day. A value the scenario declares the run owns is never defaulted: that is an
initial world value, and a form supplying one is the fabricated default run
setup refuses over. M4's regression is restated as a property - no control may
hold a value the screen does not disclose - rather than as a list of fields.

**A ban on words became a ban on capability.** The gate suite forbade run
vocabulary on any control. After T020 a destination called "Runs", a row naming
a run identity and a disabled "Run this draft" all match that pattern
truthfully, so the rule is now: an anchor may match, a disabled button carrying
a reason may match, nothing else may, and on the two run surfaces no
non-anchor control may be enabled at all.

**A gate claim that measured an empty screen.** The gate suite rendered the app
with no run client, so both run surfaces showed "the run store could not be
read" - no controls at all - and every claim about what they may offer was a
claim about an empty set. Found by deliberate violation: an enabled Run button
passed the whole suite. The store is injected now. The lesson generalises: a
gate test that asserts an absence must first prove the screen rendered.

What T020 leaves open, for the slice that meets it.

- **No `READY` run is reachable through the product path.** The shipped model
  profile cannot execute the shipped Fuel Loss Event. Every `READY` claim is
  proved against a fixture run record written through the port
  (`run-b54689cf5dd14b5eb49e2e7a00f7275c` in `var/runs/` on this machine) or
  against an injected fixture in the UI suite. **T020B** makes the shipped
  scenario reach `READY` and should re-run the layout evidence then.
- **The inventory cannot disclose what `READY` does not assert.** The word
  stands alone in a table cell; the panel that qualifies it exists only on the
  detail. That is the thinnest point of the slice's presentation honesty and it
  is named in the packet's assessment.
- **The run store accepts unknown keys.** It is what kept older Drafts readable
  here, and it is a strictness gap. Closing it would turn a field deletion into
  a migration, so it was left.
- **`tools/layout-evidence.mjs` creates one Draft per run**, T019 behaviour,
  and nothing clears them. The inventory on a developer machine is dozens of
  near-identical blocked Drafts.

## T020A - Typed component properties and frozen Foundation answers

What this slice settled in code.

**A Foundation declares typed properties beside its ratings.** A `Rating` is
the one nameplate magnitude a component was sold with; a `ComponentProperty`
is a named, unit-carrying physical or control fact about the same component,
and a component may declare several. The vocabulary is closed in
`sites/models.py` - `COMPONENT_PROPERTY_DEFINITIONS` maps a key to its unit,
its kind and its display name, and `PROPERTY_UNITS` is derived from it so a
unit cannot outlive the property that used it. Four members today:
`tank-capacity`, `specific-fuel-consumption`, `reserve-state-of-charge` and
`minimum-runtime`. **The unit belongs to the key, not to the document**, so
`specific-fuel-consumption` in `L/h` is refused rather than stored as a number
that is true at one operating point.

`kind` is not authored. It is read from the vocabulary, so there is no
position a document could disagree from. `source` and `source_version` are,
following the `ControlAssumption.basis` precedent: a property copied from a
template keeps `TEMPLATE` and the template's version, so a later template edit
reads as drift rather than as something that reached back into a Site.

`foundation_parsing.parse_component_properties` is one validator for both
document families, called by the template parser and the Site parser, which is
the T014 rule applied to the new section rather than a new rule.

**The compatibility path is the absent key.** A Site document written before
this slice carries no `properties`, which parses to `None` - the document being
silent, never an empty list - and round-trips to an equal record. Nothing is
invented for it and nothing migrates it. `var/sites/mg-001.yaml` is untouched
and is the live proof: the shipped template moved to version 2 and MG-001 still
says version 1.

**A scenario parameter the Foundation owns has no value position.**
`D-2026-09-22-foundation-value-declaration`, closed at the structure: the rule
is keyed on the owner, because the owner is the only thing the document carries
that identifies these parameters - the binding that addresses a property lives
in the model profile and the scenario parser sees no profile. It reaches
`tank-capacity` as much as the coefficient. `ScenarioParameter.value` and
`InitializationInput.value` are now nullable and the unit is still required:
what kind of quantity the state is remains the scenario's to declare, and it is
what run setup checks the Foundation's property against.

**The bound declaration survived the value's removal.** Which state caps which
is a relationship between two world states and stays in the document; how large
the cap is is the site's. `declared_bounds` reports `(0.0, None)` for
`fuel-tank-volume` and that is the correct answer
(`D-2026-09-22-capacity-bound-source`). The bound test was re-proved where the
distinction still exists - the relationship in the parsed document, the value in
the frozen run - because after the change its control and its case both returned
`(0.0, None)` and it would have passed while proving nothing.

**`FoundationBinding` names the property.** It was a component type and a
rating unit, which can address exactly one fact per component; a generator
needing both its specific fuel consumption and its minimum runtime had nothing
to say which was meant. It is now `(component_type, property_key, unit)`.
Resolution takes the components of the declared type as the candidate set and
looks for the property on the single candidate. **It does not narrow candidates
to components that happen to declare the property**: that would let a second
tank answer for the one the binding could not address, which is the fallback
criterion 7 forbids, and a deliberate violation proved three tests catch it.

**Every Foundation-value failure blocks; none refuses.** Five cases, all
`INITIAL_VALUE_NOT_RESOLVED`: no binding, no component of that type, more than
one, the component declares no such property
(`D-2026-09-22-foundation-property-absent-blocks`), and the property's unit is
not the scenario's. `INITIAL_VALUE_ANSWERS_DISAGREE` was retired with its only
producer, because no document can state the number it compared against.
`.ai/ARCHITECTURE.md`'s naming rule is re-illustrated from the pair that
remains.

**The dispatch window forces an output and causes nothing.** Under `L/kWh` the
coefficient is not a rate over time, so the entry stops naming one: it declares
that the generator runs and at what output, `dispatched-output` is promoted from
`NON_EXECUTABLE_CONDITION` to a `FORCING_INPUT` on `generator-output-power`, and
the model rule owns the transition
(`D-2026-09-22-consumption-coefficient-unit`). The shipped profile gains
`generator-specific-fuel-consumption` and `generator-output-power`.

**`EXECUTION_CONTRACT_VERSION` is 3.** The narrowing reaches a document that was
already valid, so it moved. Version two has been published - frozen Drafts carry
it - and a stored run keeps the version it froze.

**A resolved parameter with no value is left out of `resolved_parameters`.**
`answered_by` there has two cases, `SCENARIO` and `RUN_INPUT`, and neither is
true of a Foundation-owned value. Its real answer is a
`FrozenInitializationInput`, which is the record with a shape for an absent
value and a reason beside it.

**On the screen**, Foundation renders the physical properties with the
components and the control properties beside the control assumptions, each with
its unit and the document and version that declared it, plus a note where a
reader meets the numbers saying nothing writes one to a machine or reads one to
decide anything. A declared physical property joins Key parameters beside the
ratings. A scenario parameter with no number says who answers and in what unit.

Two proof lessons, both found by deliberate violation rather than by review.
The absent-property test asserted `"example-store" in statement` and the state
key `example-stored-volume` contains it as a substring, so it passed against the
wrong message. And the layout run caught what no unit test could: the scenario
detail page rendered with no tables at all, because the client's guard required
a number for every initialization input and two now carry none. A fixture is not
a payload.

**What an independent review returned, and what it changed.** Three reproduced
correctness defects, all closed in the same slice.

A `SITE_FOUNDATION` parameter with `initializes: false` parsed and then
qualified for neither frozen collection - no answer, no row, no blocking
reason, and the run reported `READY`. The parser refuses the combination now,
because a Foundation-owned parameter states no number and the only record for
its answer is a `FrozenInitializationInput`, which is built from parameters
whose ownership initializes. **The concept the refusal turns away is
legitimate and has no carrier: a Foundation-answered coefficient that is not an
initial value. The slice that needs one adds the carrier and lifts the refusal
together.** The service exclusion that assumed representation now keys on the
frozen collection itself rather than on `value is not None`, and the
completeness property is asserted directly, because a paired-absence invariant
cannot catch a row that vanished.

The property validator admitted `nan` and `inf` - both are floats and neither
is less than zero - and the review wrote positive infinity into a real Site
store, then watched serving it raise. Finiteness is checked at the shared
boundary and a percentage is bounded by what its unit implies. The bound is
keyed on the unit rather than on the property: a per-property range table is a
general mechanism a four-member vocabulary has not earned, and the cost is
recorded - a later property that is a percentage above one hundred cannot be
added under `%` without deciding this.

`FoundationBinding.unit` was read by nothing at all. Three units must agree
now, and the binding-versus-scenario half is decided before the Site is
consulted, because no Foundation can reconcile a profile and a scenario that
disagree about the quantity.

**The substring weakness is a pattern, not two incidents.** It was caught once
during the build and survived two files away, where the review proved it by
mutation: `fuel-tank-capacity` contains both `fuel-tank` and `tank-capacity`,
so replacing every explanation with the bare state key still passed. Assertions
across this slice's tests now pin phrases a state key cannot satisfy.

**And the layout abort had a different cause than the packet guessed.** It was
attributed to the run store's create cost; the actual cause was the submit
script clicking a button the form disables until the configured site has been
read. Clicking a disabled button does nothing, so nothing was posted - which is
why the local run store did not grow across an aborted run. Both layout runs
complete now, 204 claims each. The run store's O(n) create is still real, is
the product's own persistence path rather than a developer-machine cost, and
wants an owner before T027.

**And what a second independent pass corrected.** R1 and R3 were confirmed
closed and the AC6 coverage kept; three bounded items remained, and two of them
are patterns rather than incidents.

`math.isfinite` converts its argument before testing it, so it **throws** on an
integer no float can hold rather than returning False. A 401-digit integer is
valid YAML inside the document size limit, so it reached that line through both
document families and surfaced as a raw `OverflowError` with no property
position. The conversion is now asked first, and refused by position. The
round-one function had the same hole one line further down, at the `float()`
that builds the record - **this slice relocated it rather than introducing
it**, which is worth remembering the next time a check is moved rather than
added. The identical hole existed one domain along in `scenarios/parsing.py`, where
`_reject_unusable_quantity(float(value), ...)` put the conversion one character
outside every numeric rule it was about to apply. It was flagged rather than
quietly fixed - the round was bounded - and then closed in a round of its own
once the user approved. **That makes this a pattern with two confirmed
instances rather than two mistakes: a check moved in front of a conversion,
without the conversion itself being covered, carries the hole with it.** The
function there now takes the authored number and returns the converted one, so
the conversion happens inside the thing that owns the numeric rules.

**And the pattern is wider than the two that were fixed.** Looking for a third
instance while closing the second found four more, all reproduced: the run
setup request parser (`runs/parsing.py` `_quantity`, reachable from a request
body, so a 500 where a `REQUEST_INVALID` refusal already exists), the run
document reader (`_real`), and the rating parser in both Site document
families. None is T020A's surface and none persists a bad value; each is the
inspectable-error half, and each is one `try`/`except` plus a test. They are
flagged in the packet's residual risk rather than swept, because the round was
scoped to one call site - but the honest generalisation is that **this codebase
validates numbers with `float(value)` written inline, and every place it does
carries the same hole.**

A comment claimed the run record would refuse a valueless resolved parameter
loudly. It does not: `FrozenParameter` is annotated and not validated, and
`SimulationRun.__post_init__` checks initialization rows rather than resolved
parameters. The boundary that holds is `YamlRunStore.create_run` re-reading its
staged document. **The comment is corrected and `test_run_store.py` now pins
both halves**, including the dataclass limitation, so a later slice that makes
`FrozenParameter` validate has to delete a test that says it does not. A guard
promised in a comment and absent in code is worse than no guard, because the
next author builds on it.

**The assertion-satisfied-by-adjacent-text pattern reached three instances in
one slice.** After the backend sweep, a frontend test still claimed to prove a
bound survives rendering while matching text from the state column - and
`ScenarioFrame` renders `parameter.bounds` nowhere. It is renamed to what it
tests, and a second test asserts the bound is genuinely absent from the
declaring row, scoped to that row because the state name appears elsewhere in
the same table. Three instances is not three mistakes; it is a habit of
asserting on identifiers that appear near the thing being claimed, and the
fix that generalises is to assert phrases and to scope absence claims to the
element that would carry the thing.

The percent range is recorded as this vocabulary's policy rather than as a
property of the unit: a loading factor of 120 % is an ordinary number, and what
is true is only that the single `%` key here is a fraction of what a component
holds.

What T020A leaves open, for the slice that meets it.

- **Same-type component addressing is T020A1.** An unqualified binding resolves
  exactly one candidate or it blocks. Two tanks block today, with the ambiguity
  named.
- **The shipped Fuel Loss Event still cannot reach `READY`**, on any site. The
  three forcing states the profile does not model remain, and lowering them is
  **T020B** under `D-2026-09-22-forcing-state-requirements`.
- **Option C is still a follower.** No profile carries a model-supplied initial
  value; a `MODEL_RULE`-owned value blocks. Its trigger is the first model rule
  needing a Foundation value without a scenario asking for it.
- **`var/runs` holds 72 local Drafts and `create_run` is O(n) in that count.**
  It re-reads and re-parses every stored run twice to refuse a duplicate
  identity; one create measures 3 to 7 seconds here depending on load. That is
  T020's recorded behaviour biting - the layout script writes one Draft per
  visit and nothing clears them - and it is the PRODUCT's persistence path, so
  calling it a developer-machine cost understates it. It needs a bounded fix
  with an owner before T027's internal demo, preserving the duplicate and
  atomic-write guarantees.
- **A Foundation-answered value that is not an initial world value has no
  carrier**, and the scenario parser refuses the declaration rather than
  letting it vanish. The first law that needs one adds the carrier and lifts
  that refusal together; it is the same trigger as option C. The refusal
  message tells an author how to fit today's schema and does not name that
  third route - a reviewer's suggested wording improvement, carried.
- **`reconcile_reported_observations` reports a wider gap**, 310 L against the
  readings where it reported 254 L, because the document no longer carries the
  generator's consumption. That is the honest projection of a document that has
  stopped carrying a machine's physics, and closing it is T021's kernel.

## T020A1 - Addressed bindings from scenario to frozen initialization

A world state is now named by an ADDRESS rather than by a semantic key alone.
`StateRef` in `backend/assetops_backend/state_refs.py` carries three things: the
semantic key, the scope it is claimed at (`SITE` or `COMPONENT`), and, for a
component-scoped claim, which component. It sits at the package root beside
`document_bounds.py` and for the same reason - the rule is about addressing,
not about scenarios, profiles or runs, and `runs/profiles.py` may not import
the Site record family at all.

**The authored spelling is one string with three forms.** `fuel-tank-volume` is
component-scoped and unqualified, `fuel-tank-volume@north-tank` names the
component, and `site:site-load-demand` is a fact about the installation.
`component:` is accepted as the bare form said out loud and renders back as the
bare form. A bare key means COMPONENT and never SITE. **What makes that direction safe is
enforcement in `runs/service.py`, not the spelling**, and the property has
edges that have to be stated with it or the statement goes false again - it did
three times. A COMPONENT-scoped reference must identify one component of the
bound Site before that run is READY, whoever answers for its number, whether or
not it has one, and at either requirement level. A `site:` reference poses no
component question and is never asked one, though the profile must still model
the state at that scope. And whether this build can MODEL a state is a separate
obligation that stays requirement-sensitive: unsupported and REQUIRED blocks,
unsupported and OPTIONAL is recorded and proceeds. The other direction of the
default would have turned a statement about one machine into a statement about
the installation with nothing that could notice.

One parser serves both document families, which is what makes a frozen record
reconstruct to the address it was written from. `addressed_key` is the
canonical spelling and the identity everything keys on: duplicate detection,
blocking-reason subjects, dedup, the frozen row on the screen, and the run
document's `state_key` field. A run frozen before this slice carries a bare key
there and reads back as what it was - an unqualified component reference - so
the old Drafts stay inspectable.

**The address is stated in the document, the scope is stated twice on purpose.**
`SupportedState` gains a `scope` and still no component id: a profile says what
KIND of claim a state is, the scenario says which instance, and selecting the
same profile for a second Site addresses that Site's components. When the two
disagree the run blocks rather than guessing, and the disagreement is checked in
two places because they reach different declarations - the Foundation resolver
sees only the initial values a Foundation owns, and a scenario-owned forcing
input never goes near it. A `SITE`-scoped supported state may not carry a
`FoundationBinding` at all, refused in `__post_init__`, because such a binding
names a component type and could never resolve.

**Resolution has nine blocking cases and no refusal** - this said eight and
listed nine, and a backup review counted them; the nine are split across the
two functions as the later correction sections describe. Scope disagreement;
no binding; the binding's unit against the scenario's; a named component the
Foundation does not declare; a named component of the wrong type; no candidate
of the bound type; more than one candidate and no selector; the property
absent; the property's unit against the binding's. The candidate set is the components
OF THE DECLARED TYPE and never the components that happen to declare the
property - narrowing it would let a second tank answer for the one the address
could not reach, which is the fallback addressing exists to prevent. Every
reason's subject is the ADDRESS, so two tanks are two rows rather than one
deduplicated row with a hole behind it.

**A resolved input freezes the component that answered, even when the author
named none.** An unqualified `fuel-tank-capacity` against a one-tank site
freezes as `fuel-tank-capacity@fuel-tank`, so a later reader does not have to
re-run the resolution against a Foundation that may have been reordered since.
An unresolved input keeps the address exactly as authored, because nothing chose
a component and naming one would put an asset's identity beside a value it did
not supply - and that is also what lines it up with its blocking reason.

**The parser gained one rule that addressing made necessary.** A document may
not declare both `x` and `x@north-tank` as initial values: an unqualified
reference may resolve to the very component already named, so the two would be
one initial value with two owners, which the duplicate rule can no longer see
and run setup can no longer tell apart. Mixing the forms for one state key is
refused with the repair named.

**What moved to the addressed grain, all of it:** duplicate initialization
detection, the entry-versus-parameter state agreement, the state-effect
agreement, `declared_bounds`, `reconcile_reported_observations`,
`initialization_inputs` ordering, executable-input gathering, and
`SimulationRun.__post_init__`'s never-absent invariant. That last one is the
T020A defect at this slice's grain: keyed on the semantic key, the north tank's
blocking reason would explain the south tank's absent value - one reason, two
holes, and the second hole invisible.

`requirement_conflicts` reports an address and role a document states two
requirements for. Detection, not refusal: `_executable_inputs` keeps taking
`REQUIRED`, which can only block a run that would otherwise have run, and
T020B owns what the product finally does. Two components at different
requirements are NOT a conflict - they are two independent requirements, which
is the whole slice.

`EXECUTION_CONTRACT_VERSION` moved three to four. The same unedited Fuel Loss
Event against the same single-tank Foundation freezes
`fuel-tank-capacity@fuel-tank` where version three froze
`fuel-tank-capacity`, so the resolved identity of a run of an unchanged
document is different - the test `D-2026-09-22-contract-version-scope` sets.
`refuse_incompatible_execution` is the run half: a Draft frozen under another
contract stays readable and is refused execution rather than reinterpreted.
Nothing executes yet, so its one caller today is `runs/provenance.py`, which
puts the refusal on the run's own Execution contract row - a guard with no
caller would be the declaration-nothing-checks defect T020A's review found in
`FoundationBinding.unit`.

Run detail names the address on each frozen row and carries the reason an
unresolved value is missing IN the row it is missing from, matched on the
address. The blocked table still lists every reason; pairing two of them to two
rows that differ by a component id was the work this removes.

`config/site-templates/twin-tank-mini-grid-150kw.yaml` is a second shipped
archetype: two fuel tanks at 500 L and 800 L, two generators at 0.311 and
0.285 L/kWh, `load-res` and `load-mill`, and two fuel level sensors reporting a
signal spelled identically on both tanks - which only the declared mappings tell
apart. The differing values are load-bearing: two equal capacities would let a
resolver pick either component and still look right.

The shipped Fuel Loss Event is migrated. Every executable declaration names
what it is about - the tank, the generator, or the site - and it is STILL
BLOCKED on the three states the first profile does not model. Addressing is not
readiness and T020B owns the difference.

### T020A1 correction round: the address obligation belongs to the reference

An independent Codex review returned the slice with four defects and two
overclaiming tests. All six are closed; a fifth finding is carried by the
reviewer's own judgement. What follows is what changed and, where it matters,
what the first attempt got wrong - because three of the four are one mistake
wearing different clothes.

**The mistake.** Address resolution was written inside the Foundation value
lookup, so a reference was only ever resolved when the Site's Foundation was
the thing answering for its number. Everything else - a `SCENARIO_INPUT` or
`RUN_OVERRIDE` initial value, every forcing input, every reported observation
- carried its authored reference straight into the frozen run. So
`example-stored-level` with no selector, and `example-stored-level@ghost-tank`
naming a component the Foundation does not declare, both froze and reported
READY. The rows were present, so this was not T020A's disappearance defect: it
is the obligation beside it. **Who supplies the number and which asset the
number is about are two different questions, and only the first was asked.**

`resolve_state_addresses` is now one pass over every reference the document
declares - timeline entries, parameters on them, public parameters and the
state a bound names - run before anything is frozen, with the Foundation
lookup consuming its answer instead of doing the choosing. The obligation
cannot be attached to one owner again because it is not reached through one.

**`STATE_ADDRESS_NOT_RESOLVED` is a seventh blocking kind**, not the sixth
reused, because an initial value is not the only thing an address is needed
for. The two do not partition cleanly and a later reader must not act as
though they did: a missing binding and a scope disagreement both report
`INITIAL_VALUE_NOT_RESOLVED` before any asset has been looked for, so all that
kind means is a failure to obtain the initial value. Both carry an addressed
subject, which is what holds a reader's diagnosis together across them. A forcing input has no initial value to be
unresolved and still has to say which machine it forces, so naming this after
initial values would have been a kind unable to describe half the references it
reports on. The cases that moved to it: a named component the Foundation does
not declare, no candidate of the bound type, more than one candidate. What
stayed: no binding, the binding's unit against the scenario's, a named
component of the wrong type, the property absent, the property's unit.

An unqualified reference resolves only through the component type the selected
profile's `FoundationBinding` names for that state, and blocks when the profile
declares no binding to name one. Nothing reads a component type out of the
spelling of a state key.

**Unsupported-input diagnostics carry the address too.** Missing-state and
unsupported-role subjects and the optional record used the bare semantic key,
so two required declarations about two tanks deduplicated into ONE row and two
optional ones were identical in every field. The line now drawn, and both
halves are load-bearing: the profile is ASKED about the semantic key, because
it models a kind of state and knows nothing about how many a site has; what it
REPORTS is addressed, because the thing reported on is a declaration and there
were two. One address in two roles is still one missing-state row.

**`requirement_conflicts` resolves before it groups**, and so takes the Site
and the profile. On a one-tank site, `x` REQUIRED and `x@north-tank` OPTIONAL
are two authored spellings of one asset; grouped by spelling the function
returned nothing while advertising detection at the resolved grain. The
parser's qualified/unqualified refusal does not reach it either - that rule
inspects parameters that initialize, and one of the two does not.

**The state-reference grammar is matched with `fullmatch`.** It was anchored
with `^` and `$` and matched with `.match`, and Python's `$` also matches just
before a final newline - so a selector spelled `north-tank` followed by a line
feed satisfied it and kept that character inside the canonical identity. An
identity that looks like `north-tank`, is not equal to it, and which a YAML
block scalar supplies without an author noticing. Refused rather than
stripped, at both entry paths: trimming would turn one authored identity into
a different one silently.

**The shared scenario fixture is addressed.** It named bare `example-stored-volume`
and `example-demand` and passed only because the obligation was missing; it now
names `@example-store` and `site:example-demand`. A candidate-selection test
readdresses the whole document rather than one parameter, because two spellings
of one state produce two reasons and make a test about two things.

**Two proof overclaims, both found by the reviewer's mutations.**
`test_a_property_in_another_unit_than_the_binding_blocks` swapped the property
key, so the resolver reported a missing property and returned before comparing
the property's unit with the binding's - both unit tests passed with that guard
deleted. And `frozen_by_address` keyed rows into a dict before the whole-set
assertions ran, so a conflicting extra row disappeared into the mapping and
left two tests green. The helper now asserts multiplicity on the tuple before
keying, so every caller gets the check, and the two named tests count rows and
match parameter identities as well as addresses.

**Carried, not fixed: a hand-authored frozen document may hold two rows for one
address.** `runs/parsing.py` reconstructs the initialization tuple without a
uniqueness check and `SimulationRun.__post_init__` checks absence and status
but not uniqueness. The reviewer judged it inherited rather than introduced and
carried it under `D-2026-09-22-milestone-speed-over-purity`; the supported
setup path cannot produce one. **T021 must not reconstruct with
last-write-wins**, and the guard, when built, must keep reading valid older
documents.

`EXECUTION_CONTRACT_VERSION` did not move again. Version 4 has not been
published outside this branch, and the reviewer confirmed corrections inside
an unpublished version do not require another increment.

Also carried out of the review, named rather than swept: the second shipped
archetype's Foundation and SLD have not been measured at any viewport, and the
run-detail browser evidence is not evidence about the diagram it draws.

### T020A1 second correction round: visiting is not resolving

A second independent review closed five of six returned items and found three
more, all of them one sentence: **do not equate visiting a reference with
having resolved it.** The common pass was exhaustive as an ENUMERATION - every
reference was collected and looked at - and the round-two entry above read as
though that settled the matter. It did not.

**A reference now leaves `resolve_state_addresses` in one of three states**,
and naming the third is the fix. Two branches used to record a reference as
settled while checking nothing, on the assumption that `_support_for` would
report it; `_support_for` is asked about EXECUTABLE declarations, so a
reference written only as a bound target reached neither check and
`unmodelled-volume@ghost-tank` came back READY with no reasons and persisted.
The states are RESOLVED (it names one component, checked here), REFUSED (it
carries a reason), and DEFERRED - and `deferred_to_support` is set only when
the address really does appear among the executable inputs `_support_for` is
driven from, read from `_declared_requirements` rather than assumed.
`ResolvedAddress.is_resolved` was "no reason", which reported precisely the
unchecked cases as resolved; it now means what its name means.

**Existence is checked before the profile is consulted at all.** Whether this
Foundation declares a component with that identity needs no state vocabulary,
so asking it first means an explicitly addressed reference is checked even
when it names a state this profile does not model. That is what closes the
bound-only route without inventing a bounds mechanism.

**The binding's component type moved into the pass** with the rest of
selection. It had stayed in the Foundation's number lookup, so naming a
generator for a tank state blocked under `SITE_FOUNDATION` and froze 100 L
against that generator under `SCENARIO_INPUT` - the same ownership-dependent
obligation the previous round removed, one position further in. It is not
duplicated: by the time `_resolve_foundation_value` runs, the component is of
the bound type or there is none.

**A regression the previous round introduced, and the rule that prevents the
class.** Every owner's row moved onto the resolved address while the
MODEL_RULE branch still emitted its reason against the authored one. On a
one-tank Site a bare model-owned reference resolves to `@north-tank`, its
number is absent because no profile carries a model rule for it, and the
mismatch made `SimulationRun.__post_init__` raise - so a Draft that should
have been BLOCKED and inspectable was no Draft at all. **The missing value,
the reference frozen beside it and the explanation for it are kept at one
grain**, here and in `_resolve_foundation_value`.

**An unresolvable row is frozen ABSENT for every owner**, which reverses a
round-two decision. That round kept the scenario's number on such a row,
arguing the document really does state it. Two things were wrong: a frozen
initial value is the initial value OF a world state and an unresolvable
address names none, so the screen showed a quantity beside an asset that
cannot carry it; and it made the record behave one way for a scenario-owned
or run-owned value and another for a Foundation-owned one, which is the
ownership-dependent treatment these rounds exist to remove. My own new test
caught it.

**What the tests learned, which is the part worth carrying.** The round-two
test asserted that the pass VISITED every reference - the assertion that was
already passing while the defect was live.
`test_nothing_is_deferred_to_a_check_that_never_sees_it` asserts the property
that was missing instead: for every reference the pass declines to answer
itself, its address must appear among the executable inputs `_support_for` is
driven from. It counts the deferrals it saw and fails if there were none, so
it cannot pass because the branch was never taken. An enumeration assertion
survives the mutation that makes a deferral blind; this one does not.

Two prose claims were corrected at the places they were made rather than only
in a later section: the blanket safe-default guarantee about a bare key, in
`state_refs.py` and in the authored-spelling paragraph above, which is a
property of the enforcement in `runs/service.py` and not of the spelling; and
the claim that the two blocking kinds partition cleanly, in `models.py` and
above, which they do not - a missing binding and a scope disagreement both
report `INITIAL_VALUE_NOT_RESOLVED` before any asset has been looked for, so
that kind means only a failure to obtain the initial value.

`EXECUTION_CONTRACT_VERSION` did not move. Version 4 remains unpublished
outside this branch.

### T020A1 third correction round: two obligations, asked of every spelling

The Codex Reviewer was out of quota and `.ai/ROLE_CONFIG.md`'s backup rule put
a Claude reviewer on the slice. It found two things three Codex passes had not,
both the same mistake as the previous two rounds, one spelling and one
requirement level further in.

**The SITE branch returned before the profile was consulted.** So the check
round three added to close bound-only references never ran for a `site:`
spelling: `site:unmodelled-volume` as a bound target came back READY with zero
reasons and persisted, and so did `site:example-stored-volume`, a site-wide
claim on a state the profile carries per component.

**The deferral handed the whole reference to `_support_for`, which blocks only
on REQUIRED.** So an unqualified `unmodelled-level` marked OPTIONAL froze 200 L
against no asset and reported READY. Neither party enforced the address
obligation: the resolver had delegated it, and the delegate answers a different
question.

**The structure that came out of it is the durable part.** Two independent
obligations, asked of every reference:

- **does it name one component of this Site?** Component-scoped only, never
  deferred, never requirement-sensitive - because `_support_for` does not
  answer address questions at any requirement level. A `site:` reference poses
  no component question and is never asked one.
- **can this build model the state, at that scope?** Every scope. Deferred to
  `_support_for` when it is really asked, reported here when it is not, and
  requirement-sensitive as it always was: unsupported and REQUIRED blocks,
  unsupported and OPTIONAL is recorded and proceeds.

Conflating them produced both findings. Keeping them apart is what makes the
universal claim about component references finally true, because the things
that used to falsify it are now visibly the other obligation's business.

**The F2 decision was mine and I enforced rather than exempted.** An exemption
by requirement level would have reintroduced what the absent-row rule removed a
round earlier - a record that behaves one way here and another there - and the
requirement level was never the cause: it only decides whether a SUPPORT
failure blocks. The cost is one narrow case, an unqualified reference to an
unmodelled state marked OPTIONAL, which now blocks with the repair named.
`test_optional_still_means_the_run_may_proceed_without_support` pins the half
that stays requirement-sensitive, so OPTIONAL was not quietly promoted.

**The test had a hole the same shape as the code's, and that is the lesson.**
The enforcement assertion whitelisted `address.authored.scope == "SITE"` and
the parametrized bound test had five component-spelled targets and no `site:`
one. **A test written to prove enforcement must not exempt what the code
exempts**: it cannot fail where the code is wrong. Both holes are closed, and
the proof is an experiment rather than an assertion - the corrected assertion
fails against the old code, and with the escape restored it goes blind again
while only the new parametrized cases fire.

Two prose corrections. `_resolve_foundation_value` said "Five cases" over a
list of six, one of which its own later comment says moved out; the count and
the list are now stated together with the five `return blocked(...)` calls they
describe, and the four that moved are named as the address pass's.
`blocking_statement` was documented as appearing "only on a row whose value is
missing" while the execution-contract row, which has a value, carries one; the
docstring now says what the field means - why THIS row stops the run - and
names both kinds of row.

`EXECUTION_CONTRACT_VERSION` did not move. Version 4 remains unpublished
outside this branch.

What this leaves open.

- **T020B still owns readiness.** The three unmodelled forcing states are
  unchanged, and so is `D-2026-09-22-forcing-state-requirements`. It also owns
  what a requirement conflict finally does; `requirement_conflicts` reports them
  and nothing acts on one.
- **Nothing executes, so `refuse_incompatible_execution` has one caller.**
  T021's kernel is the second and calls it before it initializes anything.
- **The scope a state is claimed at is declared twice**, once per scenario
  reference and once per profile state. That is deliberate and the
  disagreement blocks, but it is two places a future slice must keep true.
- **The shipped Fuel Loss scenario's upper bound is INERT, and T021 is the
  first thing that will meet it.** `declared_bounds(fuel-loss-event)` returns
  `{'fuel-tank-volume@fuel-tank': (0.0, None)}`: the upper value is missing
  because `scenarios/execution.py` skips any parameter whose value is not a
  float, and a Foundation-owned parameter states no value by design under
  `D-2026-09-22-foundation-value-declaration`. So the tank capacity that
  bounds the stored volume never reaches the bounds map, and the only
  authored upper bound in the shipped document is absent from the projection
  of it.
  The identical guard is at `b004f58`, so this is inherited rather than
  T020A1's, and AC12's evidence remains true about the authored DOCUMENT -
  the declaration survives, addressed to the right tank. What does not
  survive is its VALUE, which now lives on the frozen run instead.
  **T021 is the first consumer of bounds** and must read the capacity from
  the frozen initialization input rather than from `declared_bounds`, or
  teach `declared_bounds` to take the frozen answers. A backup review found
  this; it is recorded rather than fixed because fixing it is the kernel's
  design decision about where a bound's number comes from.
- **A hand-authored frozen document may hold two rows for one address**, and
  T021 must not reconstruct with last-write-wins. Carried by the review, with
  the acceptance suite no longer claiming otherwise.
- **The twin-tank archetype's Foundation and SLD are unmeasured** at any
  viewport. The browser evidence is about MG-005's run detail and says nothing
  about the diagram that archetype draws.
- **`var/runs` now holds 102 local Drafts and `create_run` is still O(n)** in
  that count, unchanged from T020A and still wanting a bounded owner before
  T027. This slice added twenty-one Drafts to it, most of them written by four
  layout evidence runs.
- **The five inline `float(value)` overflow sites in
  `.ai/MILESTONE_REVIEW_BACKLOG.md` are untouched and no sixth was added.**
  `state_refs.py` converts no numbers.

## T020B - Reachable Fuel Loss readiness and boundary contract

What this slice settled in code.

**The shipped Fuel Loss Event reaches `READY` through the form and API path.**
Three states blocked every run of it, and they turned out to be three different
problems rather than one missing capability
(`D-2026-09-22-forcing-state-requirements`).

`site:site-load-demand` and `site:plane-of-array-irradiance` are now `OPTIONAL`
at all five positions in `config/scenarios/fuel-loss-event.yaml`. `REQUIRED`
means an executor must MODEL this to run this scenario, and producing the fuel
trajectory needs neither: the document declares the generator's dispatch
directly, so nothing computes it from load and PV, and a kernel that modelled
them would be computing dispatch. Both stay declared and reach the run as
`UnsupportedOptionalInput` rows, named on the run's own screen. What consumes
them electrically is T024.

`fuel-level-reporting-availability@fuel-tank` was never the model profile's to
answer, and that is the structural half of the slice. `runs/profiles.py` gains
`REPORTING_PATH_STATES`, a closed vocabulary of states that are facts about the
reporting PATH rather than about the world, and `SupportedReportingState`, which
a `PublicationProfile` declares them with. A `ModelProfile` that declares one is
refused at construction and a `SupportedReportingState` naming a world state is
refused the same way, so exactly one profile answers for each state.

**The authority is read from the state, never from whichever profile replied.**
`state_authority(state_key, model, publication)` returns a `StateAuthority` -
who answers, its detail text, and what it said - and the routing is by
vocabulary membership rather than by asking the model profile first and falling
back. That distinction is the whole value: "ask one and then the other" makes a
world state the model profile has not got round to look like a reporting-path
state, and sends the reader to the wrong profile. So a run whose publication
profile declares no reporting capability blocks with a reason naming THAT
profile and saying a model profile cannot answer for it.

**F5 is settled, and it was two functions ordering two facts oppositely.** An
unqualified reference to a state the profile models site-wide reached the
no-binding refusal, because a binding is only read when the scopes agree and a
site-wide state has no binding by construction. The statement told the author to
add an address or find a profile that declares the binding; the repair is to
write `site:` in front of the key. `_resolve_foundation_value` ordered scope
before binding and said so in its docstring, so one function contradicted the
other's stated rule.

Three things fix it and the third is the durable one. The scope check runs first
in `resolve_state_addresses` too. `scope_repair` computes the one string an
author types, from the two scopes, and `scope_disagreement_statement` is the
single wording all three sites use - the message was duplicated three times with
its own hedges in each. And all three ask `state_authority`, so an ordering
mistake is now one mistake rather than a disagreement between functions that
never read each other.

**One blocking row per address.** `_decide` takes the address resolutions and
skips the support question for an address the resolution pass already refused.
The obligations stay independent and a declaration can fail both, but a
reference that names no asset has nothing for a profile to be asked about, and
the second row added no repair the first did not state. Nothing is traded: the
address obligation is not requirement-sensitive, so such a run is `BLOCKED`
either way.

**A requirement conflict refuses, at the earliest layer that can decide it.**
The `REQUIRED`-wins collapse T019 invented is gone rather than kept as a
fallback, because the fallback is what made this lowering unobservable - demand
is declared at three positions, so raising one kept the state required. Two
levels on one AUTHORED address need only the document, so
`_validate_execution_requirements` in the scenario parser refuses it. Two
spellings that resolve to one address need a Foundation, so
`_refuse_requirement_conflicts` does, as `EXECUTION_REQUIREMENT_CONFLICT` with
no `run_id` allocated. `_declared_requirements` raises
`UnresolvedRequirementConflict` if one reaches it, so there is nothing silent
left to restore the old behaviour.

**The execution contract publishes what a kernel actually has to do.**
`scenarios/execution.py` gains `BOUNDARY_CYCLE`, the nine phases of v4 section
6.1 with declared ordinals - it replaces "observe after the step", which said
which side of a step a sample falls on and nothing about where a controller, a
resolver or an invariant check sits. `OBSERVATION_RULES` with `READING_CLASSES`
states what a reading timestamped `T` describes, per class: a stock is sampled
at `T` after that instant's events, a rate summarises `[T-dt, T)`, an interval
reading is UNAVAILABLE at the run's first boundary absent a declared historical
window, and a controller's view is not the published observation and no
reporting cadence becomes a control cadence. Two new `DISPATCH_RULES` declare
the linear window ramp between a window's own two endpoints and that a forcing
outside its window is UNAVAILABLE rather than zero or held.
`BOUND_POLICY_STATEMENTS` says what each policy commits a kernel to, which is
where `BOUNDED_AND_RECORDED` finally says the run CONTINUES and later causes
apply to the bounded value.

`quantity-across-a-window` was amended in the same pass, because it said the end
state is the same "whether a kernel applies it in one step or spreads it across
the window" and the ramp rule forbids that for every instant inside. Two rules
of one contract saying opposite things is what the amendment prevents.

**All of it is on a screen.** The contract payload carries `boundary_cycle`,
`observation_rules` and a `policy_statement` per bound case, and
`ScenarioFrame.tsx` renders two new tables and a note per policy. A contract
that reaches a kernel author only through a design document is not published.

**`EXECUTION_CONTRACT_VERSION` moved 4 to 5.** Version 4 is on `main` and local
Drafts carry it, so the unreleased-version doctrine that let three amendments
share version two does not apply. Three of this slice's changes reach a document
version 4 accepted: the conflict refusal refuses one that was valid, the
authority move changes the outcome of the shipped document against the same pair
of profiles, and the four declared semantics narrow what a conforming kernel may
do. The `OPTIONAL` lowering is authored content in one document and moves
nothing by itself.

**The fixture-only `READY` proof is retired as the demonstration.**
`backend/tests/test_execution_contract_alignment.py` reaches `READY` with the
shipped document against a Site instantiated from the shipped template through
`SiteCreationService`, and asserts the frozen answers, the two recorded optional
inputs, the disclosure and the contract version on that run. `MG-006` in
`var/sites/` is the same case through the real HTTP path, with
`var/scenarios/fuel-loss-event-mg006.yaml` naming it, and
`run-9f74603b06384126a627a5339fc78fbe` is the `READY` Draft the owner reviews.
T020's fixture run record was left in `var/runs` as user data.

What T020B leaves open, for the slice that meets it.

- **`supported_reporting_states` has no falsifier either.**
  `LAB_PUBLICATION_PROFILE` declares it can model the reporting path being
  unavailable, and nothing in this build can suppress a reading. It is the same
  shape as the `supported_states` entry already in
  `.ai/MILESTONE_REVIEW_BACKLOG.md`, and the observation transform is its
  falsifier: it is what makes the declaration true or false. The readiness
  disclosure covers both, which is why it stays - **but it did not when this
  entry was first written, and the entry said it did.** T020B's independent
  review caught it: `READY_DISCLOSURE` named only the model profile's supported
  states, `models.py` was not in the slice's diff at all, and three documents
  asserted a coverage that did not exist. The correction round widened the
  disclosure to name both profiles, both supported sets and both retirement
  conditions. It was dangerous rather than untidy because those two conditions
  fall on different slices - a kernel for one, the transform for the other - so a
  disclosure naming only the first would have been retired by the kernel slice
  while the second claim stood unfalsified.
- **Two blocking rows can still share a subject across two kinds.** An
  addressed reference whose scope disagrees with the profile produces
  `INITIAL_VALUE_NOT_RESOLVED` from the Foundation lookup and
  `STATE_NOT_SUPPORTED` from the support question, both about one address. The
  F5 item this slice owned was the address-versus-support pair and that one is
  closed; this pair predates T020A1 and has the same fix on both rows. Recorded
  in the backlog rather than fixed.
- **The reporting-path vocabulary has one member**, which is the honest size of
  it, and the routing is unreachable if it ever has none - asserted, so it
  fails rather than passing over an empty set. A second reporting-path state
  arrives with T022's observation transform.
- **`var/runs` now holds 127 local Drafts and `create_run` is still O(n)** in
  that count, unchanged from T020A1 and still wanting a bounded owner before
  T027. This slice added twenty-five: one is the `READY` MG-006 Draft the owner
  reviews, and twenty-four are `BLOCKED` Drafts of the shipped document that
  the layout evidence tool creates, one per run-setup visit across five runs of
  it. The tool has created a Draft per run since T019 and nothing clears them.
- **An `UnsupportedOptionalInput`'s statement is PERSISTED on the frozen run**,
  not computed when the run is read. That is correct - a frozen run records what
  it said at setup - and it has a consequence worth knowing: the review round
  that corrected this copy could not be seen by reloading an existing Draft, so
  the demo Draft was regenerated as
  `run-9f74603b06384126a627a5339fc78fbe`. It is the same shape as the
  instruction that T021 regenerates rather than executes a Draft frozen before
  its own build, one layer down: any slice that changes a persisted statement
  changes it for new runs only.
- **The five inline `float(value)` overflow sites are untouched and no sixth was
  added.** Nothing in this slice converts a number.

## T021 - The independent causal Fuel Loss kernel

What this slice settled in code. **A frozen READY Draft of the shipped Fuel Loss
Event now executes**, in a simulator that cannot see the product, and produces a
private trajectory whose tank movement follows dispatch, consumption and events.

### Where things live, and the rules that keep it that way

Three Python trees are importable and a fourth is not.
`contracts/assetops_contracts` holds what both sides of the truth barrier must
agree about: the versioned execution semantics (moved unchanged from
`scenarios/execution.py`), the frozen-input schema a kernel consumes, the private
trajectory, the execution-failure vocabulary and the BLAKE2b-256 identity domain.
`simulator/assetops_simulator` holds the kernel and the fuel pack.
`host/execution_adapter.py` is the composition leaf, and nothing imports it.

The backend re-exports every moved name, so a product caller still reads one
module and the scenario detail screen renders the contract's own objects rather
than copies: `is` holds, asserted. What stayed in `scenarios/execution.py` is
everything that reads a `ScenarioDefinition`.

`tools/checks/dependency-direction.ps1` gains two rules: nothing imports `host/`,
and the neutral contracts import neither side. Both patterns are anchored at the
start of a line, because these modules discuss both sides at length in prose and
a sentence naming a package is not an import of it - proven narrow by a probe that
inserts an INDENTED import and watches it caught.

**One thing was deliberately not moved.** `StateRef` stayed in the backend and the
neutral boundary carries canonical address TEXT - `fuel-tank-volume@fuel-tank`,
`site:site-load-demand` - which is what a frozen run document persists and what
every comparison in the product already keys on. Moving the record would have
relocated a validator with twenty callers and bought this slice no behaviour.

### The contract is conformed to, not resembled

Three mechanisms, each because the alternative is a claim nobody checks.

**The phase order is read from `BOUNDARY_CYCLE`.** `_PHASES` maps each declared
`phase_id` to the function that runs it and the loop visits them in the contract's
`sequence`. A phase added to the contract stops this kernel until it is
implemented rather than being skipped, which is what `BoundaryPhase.sequence`
being "the contract, not the tuple order" looks like when something consumes it.

**The two dispatch formulas are executable, in the module that publishes the
sentences describing them.** `step_concerns_window` is `window-overlap`'s
predicate and `window_share_of_step` is `window-ramp`'s share. The kernel calls
them rather than deriving overlap itself. Four T020B review rounds were spent on
sentences that each restated a subset of what the formula does; a kernel with its
own copy of the arithmetic would have been the next instance.

**The advertised supported set is derived from a table of executable handlers.**
`ModelSpec.advertised_supported_states` groups the handler table, and there is no
field in which to write a role no handler implements. That closes the backlog's
first entry: `supported_states` had no falsifier, so `READY` was computed from a
promise about a kernel that did not exist.

### The conformance test has three legs, and the third is the one that bites

Deriving a set and comparing it against another declaration would be two tables
somebody keeps in step by hand - the same defect one layer deeper. So: the set is
derived by grouping handlers; every advertised `(state, role)` pair must be
REACHED by executing a Draft created through `RunSetupService` from the shipped
document, recorded by an execution ledger; and the derived set and
`MINIMAL_FUEL_TANK_MODEL`'s declaration must be equal in both directions. A probe
removes a handler and watches the derived set narrow; another adds a handler
nothing calls and watches the ledger report it missing.

**`REPORTED_OBSERVATION` is verified at the model's grain and no further, and the
record has to say so.** The handler answers what a stock is at an instant, after
that instant's events, and refuses to answer in any other phase. Nothing here
publishes that answer: no device, no cadence, no sampling error, no dropout, no
envelope. That is why only half the readiness disclosure retired.

### The trajectory, and the numbers derived before the code ran

Against the shipped template's Foundation - a 500 L tank and a 0.311 L/kWh
generator - the stored volume is 430 L to offset 1080; loses 2799/800 L in each of
the sixteen dispatch steps, reaching 18701/50 = 374.02 L at 1320; holds that to
1500; loses 40 L in each of the three removal steps, reaching 12701/50 = 254.02 L
at 1545; and at 2400 the 300 L delivery fills the tank to 500 L with 2701/50 =
54.02 L recorded refused, after which the run continues and ends at 500 L.

Every number is a `Fraction`. `test_no_kernel_module_limits_a_denominator` scans
the package for `limit_denominator` and for `float(`, so `EXACT_RATIONAL` is
measured rather than intended; the one authored-float normalization is the
contract's own input boundary.

A bound is applied where the transition happens - phase 1 for a due event, phase 7
for the evolution - and phase 8 verifies. That pair reads two ways until one is
ruled out: a bound applied only at phase 8 would let phase 3 sample a volume above
the tank's capacity, which `fuel-tank-capacity` forbids at every step.

### Where a bound's number comes from, which was this slice's to decide

`D-2026-09-22-capacity-bound-source` settles the principle - the declaration is
the document's and the value is the site's - and left the mechanism to the kernel.
The mechanism is the host adapter: it reads the `bounds` block for WHICH state
caps which and the frozen initialization input for HOW LARGE, and
`BOUND_CASE_BY_DECLARED_BOUND` names which contract bound case a declared bound
falls under explicitly. An unmapped bound is refused rather than defaulted,
because deriving the case from a state key's spelling is a rule a later author
moves by renaming something. `declared_bounds` was NOT taught to read frozen
answers: it stays a projection of the document, and it is on its way to the test
suite with the reconciliation panel.

The floor comes from the model, never from `IMPLICIT_LOWER_BOUND_DIMENSIONS` -
`D-2026-09-22-reconciliation-panel-retirement`'s instruction to this slice. The
stock handler declares it with the bound case that says what happens when it is
reached, and the simulator cannot reach that constant anyway.

### The three backlog items addressed to this slice

**Regenerate rather than execute.** Every Draft in both new suites is created in
process by the real setup service. No local Draft is read, and the version-guard
test lowers the version on a rendered document so what is refused is a run whose
provenance is known.

**Cross-reference before initializing.** The adapter carries the run's
`unsupported_optional_inputs` addresses into the neutral inputs, and an initial
value for a state with no handler that is NOT recorded there stops the run as
`UNSUPPORTED_MODEL_STATE`. Recorded, it is skipped with a note saying nothing
about this run models it. The difference between the two is the cross-reference
and nothing else, and both halves are tested.

**The inert upper bound.** Answered above. The capacity reaching the kernel is the
frozen Foundation answer, proved on two Sites: 500 L on the shipped template and
800 L on the twin-tank archetype's south run, whose delivery refuses 65.8 L.
Neither number appears anywhere in the kernel.

### What the kernel refuses, and why each refusal is not the others

Ten execution failure kinds, disjoint from run setup's refusals and a Draft's
blocking reasons - asserted in `host/tests`, the only place that comparison can be
made. `contracts/assetops_contracts/failures.py` records every kind constructed in
a process and the simulator suite fails the session if any member was never
produced, so the vocabulary is reachable rather than decorative. Two are reached
by breaking a handler on purpose: `BALANCE_IDENTITY_VIOLATION` is a contradiction
inside a kernel and cannot be provoked from outside one.

`FORCING_VALUE_AMBIGUOUS` is how this slice **meets** the T020B carry about a
window declaring two values. `baseline-load-profile` declares two parameters for
one address and one role, and nothing says whether they are the ends of a ramp or
two named levels. The kernel refuses to compose them rather than inventing one of
two legitimate readings. It does not reach that refusal on the shipped document
only because nothing models site demand - so the semantic decision still belongs
to whoever models it, and the kernel will not have quietly chosen for them.

A reporting-path forcing never reaches the kernel as a forcing at all. It is the
publication profile's, it moves no stock, and it travels on
`reporting_path_addresses` so the kernel can say it was withheld deliberately
rather than report a declared entry it silently dropped. It is excluded from the
trajectory identity for the same reason: this is the identity of the WORLD, and
two runs differing only in whether a sensor reports produce the same world.

### The shipped document's numbers, corrected from the computed world

Two authored readings were 155 L and 150 L where the trajectory this document's
own declarations produce holds 254.02 L. They predate the consumption coefficient
moving from the document to the machine, and they are corrected to 254.02 with no
reporting error, because nothing in this build models one.

What the reconciliation panel shows afterwards is the honest residual: the
declared causes still reach 310 L, and the 55.98 L difference at BOTH readings is
exactly the fuel the model law burns and the document deliberately does not carry.
It was 155 L of unexplained difference and it is now one identified quantity.

`refuelling-is-not-a-loss` was the one private expectation the trajectory made
inconsistent. It assumed a clean 300 L rise; the tank fills at its capacity, so
54.02 L never arrive and an analysis reconciling the delivery record against the
level would find them. It now names both halves. The computed trajectory is
recorded as a private `TRAJECTORY` expectation - `EXPECTATION_KINDS`' fifth
member - so the corrections can be checked rather than taken. Five expectation
rows now render on the scenario detail, measured at 640px.

**`EXECUTION_CONTRACT_VERSION` did not move, and stays 5.** The `TRAJECTORY`
widening sits off every executable path, which
`D-2026-09-22-contract-version-scope` settles directly. The contract's relocation
moves identical objects. The two new formula functions are the arithmetic the
existing statements already published, tested against those statements' own worked
examples. The disclosure narrowing is about a run status, not about how a document
is read. And the kernel's refusal to compose two forcing values is this kernel's
behaviour rather than a contract statement, so it narrows no declared space.

The scenario document's own `scenario_version` did NOT move either, and that is a
carried deviation rather than a clean answer - see the backlog.

### What T021 leaves open, for the slice that meets it

- **A definition edited in place, at an unchanged scenario version, that MOVES an
  existing entry's offset or window length, is not detected.** A Draft freezes
  resolved values and profile answers rather than a copy of the timeline, so the
  adapter compares what it can - the scenario version, and the exact set of
  parameters the document declares against the set the run froze, which catches an
  entry added or removed. A moved offset changes structure without changing either.
  Recorded in the backlog rather than described as covered.
- **`reporting_path_addresses` carries addresses and not windows.** T022's
  observation transform needs the window to suppress a reading across it, and will
  widen that field rather than discover it missing.
- **The fuel model relates one generator to one fuel tank** and fails as
  `TOPOLOGY_INCONSISTENT` on a second of either. Addressing is not the missing
  piece - T020A1 built that - the missing piece is the declared relationship, and
  it arrives with the electrical world.
- **The law requires its dispatch forcing to be declared somewhere.** A fuel run
  with no generator dispatch at all fails as `FORCING_NOT_AVAILABLE` rather than
  running a tank that sits still. Honest for a world whose only law is driven by
  dispatch, and worth revisiting when a second law arrives.
- **`var/runs` holds 149 local Drafts.** The layout evidence tool added six across
  two runs, one per run-setup visit, which is what it has done since T019.
  `create_run` is still O(n) in that count and still wants a bounded owner before
  T027. The backend suite took 44 minutes in this slice, against 19 seconds in a
  quiet tree; the difference is contention with parallel work rather than a new
  cost, and the O(n) create is what makes it sensitive to it.
- **The three-suite setup needs three editable installs**, recorded in
  `README.md`. The backend imports the neutral contracts, so `assetops-contracts`
  is a real runtime dependency of the product and not only of the tests.

### T021 correction round: the run did not determine the experiment

The independent Codex review returned five defects, four High and one Medium, and
the user asked for all five. It confirmed the shipped arithmetic, all eight
mutation relationships, all fourteen guard probes and the four-tree dependency
direction, and closed the packet's own R0 by widening the product profile in
memory and watching the equality assertion fail. What it found is that the first
executor reinterpreted frozen runs, refused a case the contract had been
corrected to permit, and could report completion after omitting a physical law.

**R1 is the one worth carrying forward, and it was a design change rather than a
repair.** A Draft froze the resolved VALUES a scenario declared and left their
TIMING in a mutable document. So: execute the ordinary shipped Draft, move
`unaccounted-fuel-removal` from offset 1500 to 1515 on the live document at the
same scenario version, execute the SAME persisted run again, and the tank at 1515
goes from 334.02 L to 374.02 L. Both complete. Nothing in the run changed.

The fix is that run setup now freezes the whole causal projection -
`FrozenCause`, `FrozenForcing`, `FrozenDeclaredBound`,
`FrozenReportingPathCondition`, each with its resolved address, direction,
canonical magnitude, shape, offset and span - and `frozen_world_inputs` takes one
argument. **There is no parameter through which a different experiment can
arrive**, which is a stronger statement than any comparison the leaf could have
made. The packet had carried this as "a definition edited in place can still move
an entry's offset undetected", and the reviewer was right that the rationale was
insufficient: T021 owes this boundary and now produces the trajectory later slices
rely on, so "structure only" was not a reason to leave it.

A digest was the cheaper option and was rejected on the reviewer's own argument: a
digest detects drift and then refuses, and criterion 2 asks for RECONSTRUCTION.
Detection is not reconstruction.

**`EXECUTION_CONTRACT_VERSION` moved 5 to 6**, which is the first move this slice
made. A run of an unchanged document freezes differently than it did, which is
exactly `D-2026-09-22-contract-version-scope`'s test. Version 5 is published, so
this is a move rather than an amendment. Earlier runs keep their version, still
read - the four collections default to empty on parse - and are refused execution,
which is what makes an empty projection safe: it can never be mistaken for a run
that declared no causes. The frozen-inputs table grew from 44 rows to 52 and every
one of the four collections reaches a row, because what a reader needs from a
frozen run is what it is going to do.

**R2 was the sharpest irony in the slice.** The kernel rejected any two forcings
concerning one step without asking whether their exposures overlap - the case
`window-active-span` was corrected over four T020B rounds to settle, which R1b and
F-V1 exist to state. It read the phase order from `BOUNDARY_CYCLE.sequence` and
called the contract's own overlap predicate, and then contradicted the sentence
beside them. Each disjoint exposure is now accounted for over its own portion and
their energies add; a `ForcingExposure` per portion replaces one value per address,
so the trajectory can say what happened. Splitting the shipped dispatch at 1085,
inside a step, produces the identical trajectory to the undivided window. A
genuine overlap is still `FORCING_VALUE_AMBIGUOUS`.

**R3: a missing law operand was silence or a `KeyError`.** Remove only the
consumption coefficient and the run reported COMPLETED with zero law events and
430 L at 1320 - missing consumption treated as zero. Remove the starting level and
the stock-moving entries and it raised a raw `KeyError` with no trajectory at all.
`_bind_laws` now resolves every operand and output from `ModelLaw.reads`/`writes`
through the model's own declared component relations, before the first boundary,
and each absence is a classified failure.

**R4: a declared cause disappeared at the adapter.** A parameter that initializes
a state is frozen in `initialization_inputs` and the projection read only
`resolved_parameters`, so a `continue` dropped the cause and the removal stopped
happening. The projection reads both carriers and raises
`UnresolvedCausalProjection` rather than dropping: a declared effect is frozen or
refused, never converted into silence.

**R5: an excluded input manufactured a machine.** `_resolve_topology` collected
addresses before consulting `unmodelled_addresses`, and handler lookup ignored
scope, so an OPTIONAL `site:generator-specific-fuel-consumption` the run had
explicitly recorded as unsupported produced `TOPOLOGY_INCONSISTENT` about
"generator, site". `_excluded` is consulted before topology, initialization and
operand resolution, and `ModelSpec.handler` takes a scope.

**C1 is closed rather than carried.** A stored run carrying two initialization
rows for one address made the last row silently authoritative - the reviewer's
probe got a run starting at 400 L instead of 430. Refused now, in the leaf, where
both rows are still visible.

**C2 shrank.** `COMPONENT_RELATIONS` in the fuel pack declares which state keys
belong to one machine, and `kernel/execute.py` imports no fuel state key at all.
What remains of C2 is that `ModelSpec` is still not a general law executor, which
is the next physical-law slice's to know.

### What this round cost, and the lesson that is not about the kernel

**A fixture pinned a contract version it did not own.**
`simulator/tests/conftest.py` wrote `execution_contract_version=5` as a literal.
The contract moved to 6, the whole simulator suite went red, and nothing said so
until a guard probe reported CAUGHT against an already-failing suite - which is
that probe measuring nothing. Two probes were affected.

So the probe harness now **establishes a green baseline and refuses to probe if
any suite it reads a verdict from is red**. A probe asserts that a test FAILS
after a violation; unless that test passes before one, CAUGHT is a coincidence.
That is the durable half of this round: the fourteen probes were the right idea
and the harness was missing the precondition that makes them mean anything.

Two probes also needed retargeting for honest reasons rather than convenient ones.
The conformance probe added a component-scoped handler that `ModelSpec` now
refuses at construction, so it failed before the test it was about could run; it
uses a site-scoped one. And scope-awareness in `handler()` turned out to be the
layer UNDER the exclusion - the product path never reaches it while the exclusion
holds - so its guard is a kernel-boundary test reached by construction, with a
control, and the probe says why.

**One pre-existing flake was found and fixed rather than swept.**
`test_the_order_is_newest_first_and_total` said its fixture clock was fixed and
asserted the list was sorted by `run_id` descending. `client()` injects no clock,
so that held only while three runs landed in the same second; freezing the
projection made `create_run` do enough more work to straddle a boundary. It now
asserts what `list_runs` guarantees - a total order, stable between reads, sorted
by `(created_at, run_id)` descending.

### What the correction round leaves open

- **`ModelSpec` is not a general law executor**, and the next slice adding a
  physical law must not mistake it for one. A law's operands resolve through
  declared component relations and one write target; two writes, or a law needing
  a relationship between machines rather than within one, need more.
- **`reporting_path_conditions` carries windows now and nothing reads them.** That
  closes the carry that said T022 would have to widen the field, and it leaves a
  frozen collection with one consumer for its address and none for its span.
- **C3 from the review is carried**: several proof descriptions are stronger than
  their assertions. The TRAJECTORY oracle test checks that number strings occur in
  a free-text statement rather than parsing and attributing each to its boundary,
  and the identity field-list guard compares a maintained list against dataclass
  fields rather than mutating each field to prove the digest reads it. Both were
  read and are correct today.
- **`var/runs` holds 159 local Drafts.** Ten more than before this round: the
  layout tool creates one per run-setup visit and was run three times, plus one
  manual POST against the live backend to confirm it served the new projection.

### T021 second correction round: the boundary a run is frozen at

Codex's second pass confirmed the first round's five closed - ten CAUGHT lines,
plus it verified the new red-baseline control by feeding the harness a deliberately
red suite and watching it refuse to probe, and confirmed the adjacent-window fix
works with two DIFFERENT levels (first step energy 75/4, not just the identical
case the tests used). It then found four more and hit its usage limit before
writing a report, so `.agent/T021-codex-second-pass-probes.py` is the review.

Where the first four defects were a kernel reinterpreting or omitting things, these
four are about the **boundary a run is frozen at**.

**1. A rate was normalized twice, and a valid removal became zero.** The worst of
the four, because it was a silent wrong number in the one property this kernel
exists to provide. The projection called a conversion that normalizes and returns a
float, then normalized THAT float again before multiplying by the window's length.
A millionth of a litre an hour is 1/60000000 of a litre a minute; the float is
1.67e-08; normalizing it again gives ZERO, and the run reported COMPLETED having
moved nothing. 1.000001 L/h froze as 999960/999959.

`frozen_canonical_value` in the contract does the whole conversion in exact
arithmetic **with the integration inside it**, converts to float once, and asserts
the round trip. Where the exact value cannot survive the float a frozen record
carries it refuses: `limit_denominator` recovers any denominator within its limit
and none outside it, and a run carrying a number the document did not declare is
what `EXACT_RATIONAL` exists to rule out. Every number a run freezes crosses it,
including initial values - the reported site was the projection and the same
unchecked conversion was one function away, which is how a class comes back.

**2. A version-6 record could omit the fields version 6 exists to carry.** Deleting
`causes` parsed, was READY, executed, and reported COMPLETED with the removal never
happening. Deleting `declared_bounds` overfilled the tank past its capacity. The
version guard cannot help when the version is the current one - and **this was my
own argument for the version move applied to a layer I had not applied it to.** A
run AT this build's version now carries the projection; an empty list is still a
real answer and a missing or null key is not; a run below it may carry none of it,
which is what preserves earlier readback. Both directions are probed, because a
guard that required the fields at every version would pass the first probe and lose
every earlier run.

**3. An unanswered magnitude raised where the product blocks.** A `MODEL_RULE`
magnitude no profile supplies a rule for has no number, and the product has always
BLOCKED such a run because a different profile may answer - the reviewer's own
control proved it by disabling the projection and getting
`INITIAL_VALUE_NOT_RESOLVED`. Raising turned that into HTTP 500 with nothing
written. `FrozenCause.canonical_value` and `FrozenForcing`'s have an absent case
now, and `SimulationRun` enforces for them the invariant it already enforced for an
absent initial value: the thing that made it absent is on the run beside it, naming
the same address. `UnresolvedCausalProjection` survives only for what the scenario
parser already guarantees cannot happen, and its docstring says so.

**4. The exclusion was one notch too wide.** A model may model a state without
modelling every role of it: this one moves a tank's stored volume and cannot have
one FORCED, so a scenario forcing `fuel-tank-volume@fuel-tank` is correctly
recorded unsupported at that role. Excluding the ADDRESS then suppressed the
`CAUSAL_INPUT` role it does support, and execution failed `INITIAL_STATE_UNANSWERED`
for a stock the run genuinely carried. The neutral boundary carries `(address,
role)` pairs - `UnsupportedOptionalInput` has carried both since T020A1 - and
topology asks the different question it should have been asking: an address
excluded in EVERY role it appears in contributes no machine, which is what keeps
R5 fixed.

Also, the same class as 3: a zero-length window reached the kernel and escaped as
an unclassified `ValueError`. It is refused where a document is read.

### The contract version did not move again, and why

**It stays 6, and the four fixes ride on it.** Version 6 has never left this
branch - `main` is at 5 - so the unreleased-version doctrine that let version 2
carry three amendments and version 5 carry four applies, and this paragraph is what
stops the amendment being invisible afterwards.

Judged per change even so, because two of them would otherwise look like moves.
Fix 1 changes what a run freezes for an unchanged document, which is the policy's
test - but the contract already said one-time normalization at the input boundary,
so a conforming implementation always produced 1/1000000 and this is conformance
rather than a rule change. Fix 2 narrows what a version-6 RECORD may be, which is a
rule, and it lands on 6 before 6 is published. Fixes 3 and 4 change what a
non-conforming implementation did.

**One thing to know about `var/runs`.** It holds 165 Drafts and contains version-6
ones frozen by the pre-fix code, created by the layout tool against the live
backend. They are
indistinguishable from post-fix ones by version - the same trap the backlog named
for version 5 - so any Draft there could carry a wrongly normalized rate. Nothing
executes a local Draft and every test regenerates, so it is a note rather than a
defect, and it is the third time this integer-equality guard has been the thing
that cannot tell two builds apart.

### What this round cost, and what the probes caught that I did not

Three probe results were mine rather than the code's, and each is worth keeping.

**A test was satisfied by an adjacent mechanism.**
`test_an_address_excluded_in_every_role_contributes_no_machine` used a `site:`
address, which the scope filter removes before the exclusion is consulted - so it
passed with the exclusion deleted from topology and proved nothing. The probe
written for it found that. It now names a second COMPONENT-scoped tank on the
twin-tank Site, mentioned only in a role the run records as unsupported.

**Two probe anchors went stale** when the exclusion gained a role, and the harness
reported SKIPPED rather than passing. That is the harness working: a probe whose
anchor has moved says so. Both anchors follow the new signature.

**A patch script wrote newline escapes into Python source through a script where
they were already newlines**, and broke every multi-line anchor in the block it
inserted. `.agent/` is gitignored, so there was no committed copy to restore from;
the block was rebuilt with a `lines()` helper so no probe body contains an escape
sequence at all. The instance was cheap and the class is not: a repair that removes
the possibility is worth more than one that removes the symptom.

## T021A - Narrow reported-observation declarations

What this slice settled in code. **A reading declares no execution requirement**,
and an authored document that says one is refused at the strict boundary with the
position named. Nothing else moved: the kernel, the packs, the trace, the
reconciliation payload and every authored value are untouched.

### The rule is a list, and both sides read it

`REQUIREMENT_BEARING_ROLES = {"CAUSAL_INPUT", "FORCING_INPUT"}` in
`scenarios/models.py`, beside `EXECUTABLE_ROLES` and deliberately different from
it. `_parse_execution_placement` refuses `execution_requirement` outside that set;
`_declared_requirements` and `requirement_conflicts` in `runs/service.py` gather
within it. One list rather than a rule written twice, which is the shape this
project keeps paying for when a rule reaches three of four positions.

The two sets differ on purpose and a future reader has to know which one their
rule belongs in. A reading IS executable - the reporting path consumes it and the
kernel's `SAMPLE_HANDLER` samples `fuel-tank-volume` in the
`REPORTED_OBSERVATION` role - but it is not an input a run can proceed-or-block
over, because a requirement level answers "may setup proceed without support for
this" and nothing was ever asking that about a reading.

### What a reading keeps, and it is the half worth remembering

Its ADDRESS. `declared_state_refs` reads all four positions a reference can be
written at and has never been requirement-sensitive, so a reading naming a
component this Site does not declare still blocks with
`STATE_ADDRESS_NOT_RESOLVED`. The narrowing removed a support question, not a
reference obligation. `TestTheAddressObligationIgnoresTheRequirementLevel` is the
class that holds this, and its `declared()` helper now skips the reading entry
when it re-levels a document, because writing a level there is refused.

### The version move, and why it is a move at all

6 to 7. Nothing executes differently - that is the whole argument for removing
the field - and under `D-2026-09-22-contract-version-scope` that is not the test.
The test is DIRECTION against documents that already exist: this narrows, so the
shipped document valid at 6 is refused at 7 and a run frozen against it can no
longer be re-derived from a document that parses. Six was published (T021 merged
at `ed0635c`, `var/runs` carries Drafts at 6), so the unreleased-version doctrine
did not apply and the ledger's own "the next narrowing is a seven" stood.

Worth keeping for the next vocabulary change: this is the first entry in the
ledger where the number moves although no conforming kernel could behave
differently. The paragraph in `execution_contract.py` says so explicitly, so
nobody re-derives it as "document shape changed" - which would bump on
everything.

### What an earlier frozen run does now, measured rather than assumed

A version-6 record carries a causal projection. The readback rule REQUIRES the
projection key at the current version and TOLERATES its absence below - so a
record carrying one below the current version is read, not refused. Confirmed
against real runs already in `var/runs`:
`run-0cc40a866aa0472b97ac33f736f0309f` (version 6, READY, 2 causes, 4 forcings)
and `run-9f74603b06384126a627a5339fc78fbe` (version 5, T020B's Draft) both parse
under build 7 and both are refused execution. The test for it is parametrized
over 4 and 6 and asserts the record came back WHOLE - run id and frozen causes
equal to the original - rather than that parsing returned something.

### A narrowing of the document structure invalidates documents that exist

The cost this slice actually paid, and the thing a future narrowing should expect
to pay again. The version number protects RUNS: an old frozen run keeps its
identity, stays readable and is refused execution. There is no equivalent signal
for authored DOCUMENTS. The four user-authored scenarios in `var/scenarios/` all
declared `execution_requirement` on their readings, and after the narrowing none
of them parsed.

Two consequences, and the second is open.

- Those four documents had the field removed from their reading positions and
  nothing else, by the same mechanical rule applied to the shipped document. No
  value, address, source or identity changed. Pre-edit copies were kept outside
  the repository for the length of the slice.
- **One invalid user document makes the whole catalog unreadable.**
  `composite_scenario_repository.list_scenarios` raises out of the list rather
  than reporting the one document it could not read, so a single unparseable file
  in `var/scenarios/` takes the scenario catalog down. That is how this was
  found: `test_scenario_repository.py` and four `test_scenarios_api.py` tests
  failed on this checkout for a reason that had nothing to do with the shipped
  document. Pre-existing, unowned, and deliberately not fixed here - the slice
  was time-boxed to the parser closure.

### What stayed inside the box

The Execution rule said implement the narrow closure and stop. What was NOT done,
so a reviewer does not have to infer it: no readiness rework, no vocabulary
decision about what an author should write instead, no reconciliation-panel
retirement, no trace, no authored value change, and no fix for the catalog
fragility above. The Implementer wrote no backlog entry, correctly, because
writing one is a planning act the time-box excluded; **the coordinator then
wrote it at the owner's direction after the packet was closed** -
`.ai/MILESTONE_REVIEW_BACKLOG.md`, "One invalid scenario document takes the
whole catalog down". Do not read the sentence above as saying the item is
unrecorded. Two tests changed the role they prove the
role-support rule with - `FORCING_INPUT` in place of the observation role - and
that was forced by the closure rather than chosen: the case they used no longer
exists.

### What this leaves open

- **The intent the field used to carry has no home yet.** An author who meant
  "the world state behind this reading must be modelled" is pointed at the cause
  that moves it, and one who meant "the reporting path must carry readings" at
  the reporting-path forcing. If a real authoring case fits neither, the
  vocabulary needs a decision.
- **`requirement_conflicts` keeps a `requirement is None` guard that the parser
  now makes unreachable.** Left as defence in a reporting function.
- **The catalog fragility above has no owner.**
- Guard probes: `.agent/T021A-guard-probes.py`, 8 probes, all CAUGHT, baseline
  measured green before any mutation.

## T022 - Execute a Draft in the Lab, and inspect generated device observations

The first visible slice since T020. Before it, the kernel existed, executed and
was confirmed by three independent reviewers, and nobody outside a test had seen
it run. After it, the owner starts a Draft in the gated Lab, steps it across the
fuel event, and reads three things that used to be one: what the world holds,
what a device reported, and the fact that nothing reported at all.

### The demonstration, in numbers, because it is what the slice is for

The shipped reporting gap is `[1490, 1580)` and the removal `[1500, 1545)` sits
entirely inside it. At offset 1545 the Lab shows:

- true value **254.02 L** - the tank after the removal;
- reported value **373.52 L** - the fuel sensor's last reading before the gap
  opened, half a litre below the 374.02 L the world held when it was taken;
- a source sample time that is that earlier instant and not this one. WHICH
  earlier instant depends on the draws, so it is not a constant of the slice:
  the host suite's fixture retains offset 1485 (`2026-09-22T00:45:00Z`) and the
  browser, executing `fuel-loss-event-mg006`, retains offset 1470
  (`2026-09-22T00:30:00Z`). The reported value is 373.52 L either way, because
  nothing moves the tank between those instants and the removal;
- quality **STALE**, outcome **SUPPRESSED_BY_GAP**, and the authored entry that
  did it named on the row.

The two columns differ by 119.50 L. The removal is 120 L, and the difference is
that number with the sensor's declared -0.5 L bias taken back out: 373.52 + 0.5 =
374.02 L when it was taken, less 254.02 L now. Saying "the columns differ by 120"
would be reading the reported value as the world's, which is the one confusion
this screen exists to prevent. That is asserted in
`host/tests/test_lab_execution.py` and measured in a real browser by
`tools/layout-evidence.mjs`.

### What it settled in code

- **`EXECUTION_CONTRACT_VERSION` is 8.** `REPORTING_RULES` in the contract
  answers four questions a version-seven implementation was free to answer any
  way it liked: when a sample is due, what a forced gap does to one, what a
  consumer sees when nothing fresh arrived, and whether a publication failure is
  drawn or chosen. Two of them are executable beside their sentences -
  `sample_due_at` and `cadence_is_expressible` - for the reason `window-overlap`
  and `window-ramp` are.
- **The publication profile is version 2**, and the two moves are one move. It
  now declares `device_signals`: which configured signal reports which world
  state, at what cadence, with what bias and with what dropout. A run freezes
  which publication profile answered, so a run of an unchanged document freezes
  a different identity under eight than under seven - which is
  `D-2026-09-22-contract-version-scope`'s own test.
- **A kernel execution is a handle.** `Execution` advances a boundary at a time
  with the boundaries so far readable mid-flight; `execute` is that handle
  advanced to the end and returns the trajectory it always did. Every scrap of
  state was already on one mutable object, so this changes when a caller may
  look rather than what any boundary holds - and five batching patterns are
  asserted to produce one content digest.
- **The observation transform is a separate component**, in
  `simulator/assetops_simulator/observation/`. It is handed the boundaries and a
  `FrozenReportingInputs` with no field a stock could arrive in; the kernel is
  handed a `FrozenWorldInputs` with no field a cadence could. Criterion 8 -
  changing a cadence, a bias or a dropout changes the reports and not the world -
  is therefore a fact about two signatures rather than a rule a caller remembers.
- **A `DeviceObservation` carries no true value**, deliberately. Pairing truth
  with a reading happens once, in `LabProjection`, built by the composition leaf
  and consumed by a gated surface. That is the exception to the truth barrier
  stated as one record rather than left as a habit.
- **The first stochastic mechanism draws under `assetops-sim-rng-v1`**, the
  domain v4 reserved and `identity.py` declined to spell until something consumed
  it. A draw is BLAKE2b-256 over the seed, a stream name derived from the device
  and signal, and the fields that locate it - never over how many draws came
  before. That is what makes "adding an unrelated stream changes no existing
  stream" structural rather than a hope about call order.
- **The execution port is the backend's, and only the leaf can implement one.**
  `runs/execution_ports.py` speaks `SimulationRun` in and `LabProjection` out.
  `host/lab_app.py` is the entry point for a build that executes; run it from
  `host/` with `python -m uvicorn lab_app:app`. `assetops_backend.main:app` still
  serves everything else and answers `PORT_NOT_COMPOSED` on the four execution
  routes, which keeps the served route set a function of the gate alone.
- **Private execution artifacts are the leaf's**, under `var/executions`, one
  file per run. A terminal run reloads from its artifact; a run recorded as
  RUNNING with no live handle reads back as `INTERRUPTED`, because its world
  lived in a process that has ended and re-executing it would be a second
  trajectory under the first one's identity.
- **Every exact quantity leaves the backend as text.** `EXACT_RATIONAL` never
  rounds, and a payload carrying a binary float would be the one place the policy
  stopped holding. A test walks the whole payload and fails on a float anywhere.
- **Criterion 14 is done.** `reconcile_reported_observations`,
  `ObservationReconciliation`, `RECONCILIATION_STATES`, its seven reason strings,
  `unaccounted_observations`, `declared_bounds` and
  `IMPLICIT_LOWER_BOUND_DIMENSIONS` are gone with the scenario detail panel that
  was their last product-path caller. Nothing survived the retirement. The
  frozen run's own `declared_bounds` - a tuple of `FrozenDeclaredBound` on the
  deterministic identity - is a different thing with the same name, is
  load-bearing, and is untouched.

### One defect the browser found, which no suite could

`reporting_inputs` asked whether the run had selected this publication profile
BEFORE asking whether it was frozen under this contract version. A run from an
earlier build fails both, and it was reporting the narrower one: "this run does
not determine one experiment" for a run whose real answer is "these rules are not
the rules it was frozen under". Every suite builds its runs in process at the
current version, so none of them had a run that failed both. The coarse, prior
fact is asked first now.

### What this leaves open

- **The shipped scenario cannot reach READY against the MG-001 in `var/sites`**,
  which predates the two Foundation properties the model profile binds to. Both
  suites and the browser evidence reach a READY execution through the product
  path from the user's own `fuel-loss-event-mg006` document instead. Backlog.
- **`var/runs` grows by four per layout-evidence run**, not three: three BLOCKED
  MG-001 Drafts from the run-setup measurement at three widths, plus the READY
  MG-006 Draft the execution measurements need.
- **The run setup screen does not show a publication profile's declared reporting
  paths.** They are on the Draft's own execution panel, which is the screen where
  they decide something, and there is one profile to choose from.
- **`private_state` carries stocks and not interval measurements**, because a
  stock's unit is the run's and an interval measurement's is the model's. The
  interval truth is in the observation row, in the unit the profile declared.
- **The dependency-direction guard's three oldest patterns match prose.** A
  docstring saying the backend cannot import the simulator failed the check. It
  was reworded rather than fixed, because loosening a dependency check inside the
  slice it blocks is the one edit that file forbids. Backlog.
### What the independent review returned, and what it cost to be wrong about

Three defects, and each was missed by a test that was written from the code
rather than from the contract or from the surface a user meets. That is one
lesson with three instances, and it is the one worth carrying.

- **R1: the draw identity was not v4 section 9.2's.** It hashed the domain, the
  stream, the seed and whatever the caller found convenient - an address and an
  offset in minutes - where the specification names the domain, the seed, the
  stream name, the step index and the ordinal. Deterministic, domain-separated,
  and a different contract. **The test could not catch it because it recomputed
  the payload the implementation had chosen.** It now writes the expected payload
  from the specification's field list, and `draw_fraction` has no variadic
  parameter, so a caller cannot supply an address because there is nowhere to put
  one. The shipped run drops 12 samples where it dropped 13.
- **R2: a READY Draft at a 30-minute timestep answered HTTP 500 on Start.** The
  cadence check ran outside the port's exception translation and the route
  catches only `LabControlRefused`, so the explanation naming the signal and both
  numbers never arrived. **The test proved the lower-level object raises and
  never drove the HTTP composition.** The check moved inside `_reporting_for`,
  `CADENCE_NOT_EXPRESSIBLE` is a ninth control refusal, and `LabControlRefused`
  gained a `detail` because a per-kind statement cannot name two particular
  numbers.
- **R3: a POINT reporting condition became an outage lasting the rest of the
  run.** `reporting_inputs` dropped the frozen `timing_shape` and every absent
  duration read as the interval's end, so POINT and INTERVAL_WIDE collapsed.
  **Every test used the shipped document, which declares a WINDOW**, so the one
  shape that worked was the only shape covered. The shape travels now,
  `ReportingPathWindow` resolves its own span from it, and
  `reporting-path-conditions-occupy-time-by-their-shape` publishes the rule.

`EXECUTION_CONTRACT_VERSION` stays 8. R1 and R3 each narrow what a conforming
implementation may do and would each move a number; they ride on eight because
eight has never been published - `main` is at seven - and the ledger records the
amendment rather than leaving it invisible after the merge. R2 moved nothing: a
translation is not a rule.

Three smaller corrections. The Lab landing page still said no simulator run
exists and that execution was not implemented. The retained-timestamp probe's
mutant was an undefined name, so its CAUGHT measured a `NameError` rather than a
rejected restamping - and the test it named survived the reviewer's semantic
mutant, because it asserted the offset and the value and never the timestamp.
And `NOT_STARTED` said "Its frozen inputs are eligible", which a BLOCKED Draft
renders beside its own blocking reasons.

**The displayed columns differ by 119.50 L and not 120.** The removal is 120 L;
the difference is that with the sensor's -0.5 L bias taken back out. Saying 120
reads the reported value as the world's, which is the confusion the screen exists
to prevent.

- Guard probes: `.agent/T022-guard-probes.py` (11 of 11 CAUGHT) and
  `.agent/T022-return-probes.py` (4 of 4, each putting a returned defect back
  exactly as it was).
