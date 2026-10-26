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
- **Every execution artifact states the schema version it was written in**,
  first in the file, and `EXECUTION_ARTIFACT_SCHEMA_VERSION` is 2. One is the
  first build that persisted an execution; two added the reporting condition's
  shape and the run's timestep to every gap row. The number exists because
  adding those fields broke every record already on disk: the reader demanded
  them and four completed runs became an HTTP 500 on the screen that inspects
  them.

  **Three layouts exist on disk and each was written by a build on this branch.**
  The current one says its schema. The two older ones do not, and
  `_identify_layout` tells them apart by whether their reporting-gap rows carry
  `timing_shape` - the exact field the later of those two builds added, and the
  only evidence such a record holds about its own provenance. All rows or none;
  a record whose rows disagree was written by neither and is not interpreted.

  **Where the shape was recorded it is honoured**, and the span follows from it
  by `end_offset_minutes` - the same rule that build resolved with, so what is
  shown is what was computed. **Where it was not**, each row carries
  `recorded_end_offset_minutes`, the span that build resolved, recoverable
  exactly because it resolved every window by one rule over fields the record
  still carries; the shape is `SHAPE_NOT_RECORDED`, which is not a shape and
  never a guess. **A record this build cannot interpret** - a later schema, a
  marker that is not a whole number, disagreeing rows, or a record that states a
  layout and then lacks what it requires - is reported: status
  `ARTIFACT_UNREADABLE` with the reason on the projection, and a typed refusal on
  every control, because an unreadable record treated as no record would let
  Start overwrite the very result nobody could read. Nothing is re-executed,
  rewritten or discarded.

  **A version marker cannot name what predates it, and the first attempt proved
  it.** The marker was added by the build that fixed the shape collapse, so the
  build before it had already written records with the shape on them and no
  marker. Assigning every unmarked record to the oldest known layout discarded
  that shape and printed a note saying it had never been recorded - while it sat
  in the same file - and turned an honest `KeyError` into a confident wrong
  reading. That is in the published rule now, not only here:
  `a-record-older-than-a-rule-is-read-as-what-it-recorded`, with version 8's
  ledger carrying the third amendment. **A later slice adding a persisted field
  inherits the rule, not the mechanism**: the run store and the scenario
  documents have their own versioning conventions and were not touched here, and
  the rule's second half - identify what predates the marker from what it carries
  - is the half that is easy to skip.
- **A window's declared instant and its resolved span are separate everywhere.**
  For a POINT they differ: an entry declared at offset 1490 in a fifteen-minute
  run silences the sample at 1485. The suppression sentence names both, the wire
  carries `declared_offset_minutes` beside `start_offset_minutes` and
  `end_offset_minutes`, and the gaps table has a column for each. One field
  named `offset_minutes` was carrying the resolved start - the right number
  under a name that promised the other one.
- **`draw_fraction` refuses a field of the wrong type**, narrowly and on
  purpose. A signature constrains arity and not types, so the claim that an
  address "cannot be supplied" was false - `draw_fraction(7, "a-stream",
  "<an address>", 1500)` returned a Fraction. The refusal is here rather than
  everywhere because this substitution IS the defect R1 was: a draw keyed on an
  address is deterministic, returns a plausible number, and differs from the
  contract's stream with nothing on any surface to show it.
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
### The fifth variant of one defect, and why it is a rule now

R4 was a change correct going forward and silent going backward. So were three
before it: T021's frozen runs reinterpreted by a live document, a version guard
unable to separate two builds sharing a number, T021A's narrowing invalidating
four authored documents, and then a schema with no reader for its own past.
**And so was R4's own fix**, which is the fifth: a version marker that correctly
identified future writes and could not identify the two historical shapes that
lacked it. The fourth was the fix for the third and the fifth was the fix for the
fourth. That is why the backward path is a published rule rather than something
each slice is expected to remember, and why the rule now names its own second
half - identifying what predates the marker from what it carries - which is the
half that was skipped.

The shape is worth recognising rather than the instance: every one of the five
was found by somebody looking at existing data, and none by a suite, because a
suite writes its fixtures with the build that reads them. A round trip through
one schema cannot fail this way. **The test that catches it supplies a record in
the shape the PREVIOUS build wrote**, and the one for R4 builds that record by
executing a real run and removing exactly what the old build never wrote - with a
precondition test asserting the fixture really is that shape.

A sixth instance of the same habit, smaller and caught by a reviewer rather than
by data: the fix's own tests all build their fixtures by STRIPPING a record the
current build wrote, so none of them states a schema marker the current build
would not write - and a record stating `artifact_schema_version: 1` was read
under the current layout and then told it had said 2. The lesson applies to a
fix as readily as to a defect, and the missing case is always the one the author
did not think to write down.

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

## T022A - A run read that does not cost the whole store

The owner found this stepping the first real run T022 delivered: everything was
correct and every interaction took about nine seconds, which reads as a hang.
`YamlRunStore.get_run` called `list_runs`, parsed all 216 stored documents and
then scanned the records for one identity, so a single read paid for the whole
store. It is the cost T020A measured at 70 Drafts and 6.8 seconds.

### What a single read does now

`get_run` looks for the document filed under the requested identity first. The
file name has always been the case-folded `run_id`, and using it as a hint about
WHERE TO LOOK is a different thing from reading identity out of it. Three
properties keep that true, and a reader changing this code needs all three:

- a key may name a file only when `is_allocated_run_id_key` says it is the shape
  allocation produces. **This is a barrier, not defence in depth**: it is the
  only thing that stops an out-of-root file being opened and parsed, because the
  identity comparison below never runs on a file that will not parse. T022A's
  packet called it defence in depth and was wrong; a reviewer found the mutation
  that proves otherwise, and the guard now carries an out-of-root sentinel;
- the document is read by the same strict reader the inventory uses, so the fast
  path refuses exactly what the slow path refused;
- the identity comes from the PARSED DOCUMENT and is compared to the key before
  the record is returned. **This is the load-bearing barrier.** Remove it as
  redundant and one run's frozen record can be answered under another's name.

A name that leads nowhere, or to a document declaring a different run, falls
back to the old scan. That is why a store somebody rearranged by hand still
answers, and why a MISSING run still costs the whole store - unchanged behaviour
on a path that is not the defect.

Measured through `host/lab_app.py` against the real `var/runs` at 216 records:
216 documents parsed becomes 1, and every wall-clock ratio sits around two
orders of magnitude - run detail and execution read both from about nine seconds
to under a tenth, a step from about ten seconds to about a twentieth. In a
browser, clicking Step went from about nine and a half seconds to about an
eighth. **Quote the ratios, not the seconds**: see the measurement warning
below.

Cost is guarded by counting documents parsed, not by timing. A clock measures
the machine; the count measures the property.

### One behaviour deliberately changed, and one bound deliberately dropped

An unrelated invalid document no longer refuses a sound single read - criterion
4 asked for that. And `MAX_DOCUMENTS` is enforced by `document_paths`, so a
store above the bound still refuses to be enumerated and still refuses a new
run, but a run somebody can name is now readable in one. Counting the directory
on every read is the shape of cost the slice exists to remove.

### An absolute measured once here is not a project fact

Recorded because this slice got it wrong first. `read_run_records` over the same
216 documents was measured three times by three readers and returned about
**15 ms, 41 ms and 49 ms per record** - more than a three-fold spread on machine
state alone, on the same corpus and the same operation. The first packet wrote
41.3 ms and a derived threshold into this file as fact, and a reviewer's
measurement disagreed by 2.7x. The same session had already seen `/api/sites`
move from 0.41 s to 0.13 s with nothing touching the site store, which was the
warning.

**So quote a ratio, a share or a shape here; quote an absolute only with the
conditions it was taken under.** What reproduced across all three readings: the
average stored document is about 6.7 KB, the YAML scanner is about 99% of the
inventory with the record parser under 1%, and libyaml reads the same corpus
about eight times faster.

### The inventory was measured and left alone, and it is NOT acceptable

`list_runs` still reads and strictly validates every record - a partial
inventory is a wrong answer rather than a slow one - and it costs a whole-store
parse every time. **99% of that is the pure-Python YAML scanner**; the record
parser is under 1%. Across the measured range the inventory passes one second
somewhere between about 20 and 65 stored runs. **It stopped being acceptable
long before the 216 the store now holds**, which is consistent with T020A
finding it uncomfortable at 70 Drafts.

The one lever measured to be worth anything is the constant: libyaml's scanner
is present here and reads the same corpus about eight times faster, with the
same `SafeConstructor` and `Resolver`, so only the scanner differs. A reviewer
went further and confirmed the two produce EQUAL documents for all 216 stored
runs - which settles the constructor argument and settles nothing about what the
two scanners REFUSE, and refusal is the question. It was reported rather than
taken, because this slice was told strictness is not what is being traded.
**It wants an owner's decision.**

`create_run` is also still O(n): `_refuse_existing_identity` calls `list_runs`,
so setting a Draft up still pays the inventory's cost. Both costs are carried in
`.ai/MILESTONE_REVIEW_BACKLOG.md` under "Reading the run store still costs the
whole store, twice" - an entry T022A had to WRITE, because three documents
including this one cited it before it existed.

### What the records on disk proved before anything changed

All 216 stored documents are filed under their own case-folded identity, with no
duplicates and no non-YAML entries. That was checked FIRST, because a change to
how a record is located is exactly the shape that is right going forward and
silently wrong going backward. Nothing enforces the invariant and nothing needs
to; the fallback covers a store where it does not hold, at the old cost.

### Two things the review round added

**The one filesystem touch outside the strict reader now translates.**
`Path.is_file` answers False for "not there" and lets a permission denial, a
sharing violation and an unacceptable path through. That stat sits outside
`read_run_record`, so an `OSError` on the requested document crossed the port
raw and a 503 became a 500 - breaking the rule `yaml_run_documents` states in
its own docstring. Because every record in the real store is canonically filed,
it was reachable on every read. Fixed with the same translation one line below
it, and guarded.

**Duplicate identities resolve differently now**, to the canonically filed
document rather than to whichever path sorted first. Unreachable through
`create_run` and absent from the store; carried, and recorded because criterion
10 asked for the list of behaviour changes to be complete.

- Packet: `.agent/T022A-review-packet.md`; reviews `.agent/T022A-review.md`
  (Claude backup) and `.agent/T022A-codex-review.md` (incomplete); the
  criterion-9 harness and its pre-change baseline server at
  `.agent/T022A-step-evidence.mjs` and `.agent/T022A-before-app.py`.

## T023 - Staged canonical source envelopes

The first canonical evidence boundary, staging only. Executing a Draft in the Lab
now also publishes, through a simulated gateway, the canonical source envelopes a
later Commit would release, persists them as an immutable stage, and shows them
exactly as persisted on the Draft's own screen. Nothing is committed, received,
ingested or accepted; no Site history changes.

### What it settled in code

- **`contracts/assetops_contracts/source_envelope.py` is the one crossing.**
  Schema `assetops.source-envelope` **v1**, independent of
  `EXECUTION_CONTRACT_VERSION` (still 8) - `D-2026-09-29-source-envelope-schema-v1`
  records the choices. Exact key sets at every level, no free-text field, exact
  decimal text for values, `YYYY-MM-DDTHH:MM:SSZ` instants, `published_at >=
  source_time`, `received_at` refused as an unknown field. `SourceEnvelope`
  validates in `__post_init__`, so an invalid one cannot be constructed, and
  `parse_canonical_envelope_json` refuses text that is not already canonical.
- **The message id is derived and content is not in it**: BLAKE2b-256 over Site,
  gateway, source, device, signal and source time, recomputed by the parser. A
  retry is the same id by construction; same id with different content is a
  `StageConflict`, never an overwrite.
- **Stock versus interval survives**: `STATE_AT_INSTANT` names no interval;
  `INTERVAL_MEAN` carries `interval_start`/`interval_end` with the end equal to
  `source_time`, the span read off the interval's real boundaries.
- **What is not published has no envelope.** `SUPPRESSED_BY_GAP` and `DROPPED`
  publish nothing; `NO_PRECEDING_INTERVAL`/`NO_VALUE_AT_BOUNDARY` become a typed
  `UNAVAILABLE` envelope only where the mapping says the signal publishes
  unavailability. The suppression sentence (which names the scenario's event)
  never crosses.
- **The gateway is `simulator/assetops_simulator/gateway/`**, a component beside
  the transform. It reads `DeviceObservation`s only. The shipped allowlist is
  `simulator-lab-gateway-fuel` v1: the fuel level sensor alone, 3 s declared
  publication latency. The generator's power signal is generated and NOT
  published - T026 extends the allowlist.
- **`contracts/assetops_contracts/source_stage.py` is the stage**: admission
  appends only, the whole mapping is frozen into the stage and read back from
  it, a refused conflict is recorded by id and kind and blocks release, and the
  persisted document is canonical JSON carrying each envelope as its own
  canonical text plus a BLAKE2b-256 integrity digest. Anything that fails to
  verify is `STAGE_UNREADABLE`, and an unreadable stage is never overwritten.
- **`host/source_stages.py` persists under `var/stages/<run_id>.json`**, atomic
  via a `.partial` sibling and `os.replace`. Gitignored user data, safe to
  delete; a missing stage reads `NOT_STAGED`.
- **`host/lab_execution.py` stages on start and on every step, before writing
  the execution artifact**. That order only means a stage write that RAISES
  aborts the step before the artifact is written; a publication refusal caught
  in `_stage` (by design) is followed by the artifact write, so a persisted
  execution CAN be ahead of the stage's watermark (review R5: 106 vs 105).
  **Write order does NOT make eligibility honest** - the first
  packet said it did, and the independent review (R1) disproved it: a failed
  final stage write with the process still alive, and a publication refusal
  caught in `_stage`, both read as ELIGIBLE. What does is the stage's own
  watermark: a stage (schema **2**) records `boundaries_total` and
  `published_through`, the latter moving only when a stage write succeeds, and
  `published_through < boundaries_total` is the `STAGING_INCOMPLETE` blocker -
  after a reload too. Measured by `TestEligibilityRequiresStagingThroughCompletion`
  without `forget`, and by guard probes P13/P14. It is a progress record, not
  T027's seal. Every step
  republishes the whole series, which is the idempotent-retry case by
  construction. The session freezes the gateway mapping at start.
- **The port gained one READ, `staged_envelopes(run) -> SourceStageView`** (v4
  3.3's name), which re-reads and verifies the persisted stage and never reads a
  live session. Route `GET /api/simulator-lab/runs/{run_id}/stage`, gated, no
  write verb. `PORT_NOT_COMPOSED` answers 503 like the execution routes.
- **Only `simulator_lab_api.py` and `runs/execution_ports.py` may import the
  stage contract** in the product; `tools/checks/dependency-direction.ps1`
  enforces it with an anti-vacuity count. The envelope schema is deliberately
  NOT restricted: T027's ingestion must parse it.
- **The inspector** (`RunFrame.tsx`, panels "Staged source envelopes" onward)
  shows status, eligibility and blockers, schema versions, frozen mapping and
  allowlist, integrity digest, one row per envelope with source and publication
  time in separate cells, and the selected envelope's canonical text byte for
  byte in `pre.canonical-text`. It is re-read after every control. It has no
  input and no control but "Show envelope N". `settledScreen` knows its loading
  sentence.

### The demonstration, in numbers

Shipped Fuel Loss Event against MG-001 (host suite): stepped to offset 1545 the
stage holds 91 envelopes, the newest at source time `2026-09-22T00:45:00Z`,
published `00:45:03Z`, value 373.52 L, and none inside the gap; completed, 147,
eligible. In the browser against `fuel-loss-event-mg006` the draws differ: 97
staged at 1545, newest `00:30:00Z`/`00:30:03Z`, 154 when complete, and a fresh
page load at 640px shows the same 154 and the same 643 characters of canonical
text. Quote the relationship, not the count: which samples drop is the draw.

### What this leaves open

- **Two Drafts of one Site produce the same message ids** for the same device
  and source time, because the id is the publication's and not the run's. Within
  a stage that is correct; across runs it is a real collision T027's commit or
  ingestion must decide about.
- **The shipped allowlist has no interval signal**, so `INTERVAL_MEAN` and the
  typed-unavailable path are proved by the gateway suite's fixtures, not by the
  shipped run. T026 is where they meet real data.
- **A stage is rewritten whole on every step** (about 110 KB at completion), so
  staging a run is quadratic in its envelope count. Fine at 150; not at T026's
  scale without an append format.
- **Eligibility rests on the publication watermark, not a seal.** It says
  every boundary was published into the stage; sealing is Commit's (T027).
- **The integrity digest is redundant with the canonical-form check**; a probe
  found the digest comparison removable with every damage case still refused.
  Both stay; the reason is now asserted.
- `var/stages` grows by one stage per layout-evidence run, beside the four Drafts
  `var/runs` gains.
- Guard probes: `.agent/T023-guard-probes.py` (12 of 12 CAUGHT); browser log
  `.agent/T023-layout-evidence.log`.

## T022B - The run store reads with libyaml

Under `D-2026-09-29-run-store-libyaml`. Packet: `.agent/T022B-review-packet.md`;
evidence `.agent/T022B-evidence/`.

### What the code settles

- **One load point, libyaml, required.** `runs/adapters/yaml_run_documents.py`
  loads every run document with `yaml.load(text, Loader=CSafeLoader)`. The
  inventory, canonical and fallback reads, both create identity scans and the
  staged readback all pass through `read_run_record`. `from yaml import
  CSafeLoader` failing raises `LibyamlUnavailable` (an `ImportError`) at import,
  so an installation without the C extension cannot import the run store - or
  `assetops_backend.main` - and is told how to reinstall. No fallback exists.
  Site, scenario, execution-artifact and stage readers are untouched.
- **Guard:** `tools/checks/configuration-persistence.ps1` check 7 - exactly one
  `= yaml.load(..., Loader=CSafeLoader)` in the run adapters, a direct
  `from yaml import CSafeLoader`, and no `safe_load`, other `Loader=`, other
  loader import or `__with_libyaml__` there. Proven non-vacuous four ways.
- **Declared compatibility changes, pinned both ways** in
  `backend/tests/test_run_store_loader.py`: tab after a colon and tab in a flow
  sequence now accepted; literal `\uD800` and `\U00110000` now
  `RunConfigurationInvalid` (the latter was an untranslated `ValueError`); ~600-
  deep flow nesting was an untranslated `RecursionError` and is now the run
  parser's own depth refusal. 34 further probes give equal outcomes. Inherited
  policy unchanged: unknown top-level fields ignored, duplicate keys keep the
  last value.
- **Counts:** canonical hit 1 parse, inventory N, fallback N, create 2N+1 - now
  asserted at the loader, not just at `read_run_record`.
- **Tools:** `tools/run-store-evidence.py` (`runtime` is the installation check
  named in README and in the diagnostic; `compare-corpus` is read-only and
  hashes; `seed`/`measure`/`serve` write only to a directory outside `var/`,
  and refuse one inside it). `tools/run-store-browser-evidence.mjs` times Runs,
  setup and run detail in headless Chrome.

### The numbers, and what they do not say

Owner corpus 223 docs / 1,504,668 B: equal under both readers. Composed
in-process at 223, warm medians: inventory 4.14 s -> **0.73 s**, setup 9.43 s ->
**1.57 s** - both inside the budgets at the server. At 300 generated records
(2,305,440 B) the warm medians are 1.09 s / 2.26 s, **both over budget**: 300 is
an observed breach point, and where between the two corpora the server stops
meeting the budgets is not established. At 500: 1.93 s / 4.06 s; at 2,000:
6.8 s / 34 s (wide ranges). The browser is a separate and worse result.
Browser, dev server, 223-231 records, CPU ~50 %: Runs **1.46-1.48 s** by
navigation, 1.32-1.37 s in-app (API ~0.67 s, the rest React dev-build
rendering); setup through populated run detail, one clock, **median 1.86 s
[1.73-2.37], 2 of 7 samples over 2 s** (the created summary on the setup page
alone: 1.62 s). **T022A criterion 2 stays open: the 1 s inventory budget is
missed on the dev server.** Quote conditions with the numbers: loaded samples
on this workstation ran 2.5-4x slower (setup through detail 4.8 s at 86 % CPU).

### What this leaves open

- **Deep flow nesting kills the process (open Architect/owner decision).**
  libyaml's C composer overflows the native stack at ~2.5-3k levels on Windows,
  ~20-30k on Linux - inside the 256 KiB bound - where the baseline raised
  `RecursionError`. Pinned by
  `test_flow_nesting_a_few_thousand_deep_ends_the_process`. A pre-load nesting
  bound would be a new refusal rule; not added.
- **The inventory budget.** Remaining cost at 223: ~0.65 s client rendering in
  the dev build, ~0.37 s PyYAML building Python nodes and resolving scalars on
  top of libyaml, ~0.07 s domain parsing. O(N) retained. Demonstrated server
  envelope: 223 records / 1,504,668 B passes; 300 / 2,305,440 B breaches; the
  threshold between them is not established. The browser misses inventory
  already at 223.
- **No CI exists**; the backend test `test_the_installed_pyyaml_carries_libyaml`
  and `tools/run-store-evidence.py runtime` are the gates. Verified at runtime
  on Windows x86-64, Linux x86-64 and Linux aarch64 (emulated); macOS only at
  the wheel-contents level.

## T024 - Daytime PV, storage and addressed load service

The first electrical world. A Kobo-like Site runs a daytime interval in the Lab:
PV, a battery and three separately addressed loads, a controller that reads a
local view and requests battery power, a declared-cascade resolver that
accepts what the installation allows, and exact energy balances. The generator
is not modelled (T025).

### What it settled in code

- **`EXECUTION_CONTRACT_VERSION` is 9** (`D-2026-09-29-t024-option-c-and-reserve-override`).
  The ledger paragraph names three moves: model-owned needs and Site Controls
  frozen in the identity, `a-control-override-replaces-its-baseline` in
  `DISPATCH_RULES`, and `COUPLING_RULES` (local view, intent versus acceptance,
  declared cascade, segment split, exact balance). New bound case
  `battery-state-of-charge-limits` (FAIL_RUN). Every Draft below 9 reads and is
  refused execution.
- **Option C.** `ModelProfile` gained `foundation_needs`, `site_control_needs`
  and `initialization_needs`; `SupportedState` gained an optional carrier
  `component_type` for unbound component states. Run setup resolves each need
  at every component of the bound type and freezes a `FrozenModelNeed`
  (declared_by, answered_by, Foundation version and valid_from, property
  source and version) in `DeterministicIdentity.model_needs`; Site Controls
  freeze as `FrozenSiteControl` in `site_controls`. Absent answers BLOCK:
  `INITIAL_VALUE_NOT_RESOLVED` at the address, and new
  `SITE_CONTROL_NOT_RESOLVED` at `site-control:<key>`. A run-start state of
  charge the scenario does not state blocks at `battery-state-of-charge@<battery>`.
  A version-9 run document omitting either collection is refused; below 9 they
  read as empty. Provenance rows render on the Draft's frozen table.
- **Foundation.** Six electrical properties (`pv-rated-power`,
  `inverter-ac-limit`, `battery-energy-capacity`, `pcs-charge-limit`,
  `pcs-discharge-limit`, `pcs-conversion-efficiency`) and an optional typed
  `site_controls` section: `source-priority` and `critical-load-priority`, each
  an ordered list naming every component of its member types exactly once.
  Existing Sites parse unchanged. Rendered on the Foundation Controls section.
  The control-properties note no longer says nothing reads them.
- **Profiles.** New `daytime-mini-grid` v1 beside the unchanged
  `minimal-fuel-tank` v1. Publication profile **3** adds six electrical paths;
  a declared path whose state the selected model does not produce is skipped,
  so a fuel run grows no electrical column.
- **Kernel.** `ModelSpec` gained an optional `Coupling` (prepare, view, decide,
  resolve) and `measured_interval_states`; phases D-F call it, G applies only
  the accepted stock accounts (origin `ACCEPTED_FLOW`), H checks every declared
  balance and the stock account exactly from the named flows. `StateHandler`
  gained a `ceiling`; `ComponentRelation` gained `many`. The kernel imports no
  electrical pack, guarded in `tools/checks/dependency-direction.ps1`.
  Contract records live in `contracts/assetops_contracts/control.py`;
  `BoundaryState.control_step` carries view, intent and acceptance, and is left
  out of the digest when absent, so fuel digests are unchanged in shape.
- **Pack** `simulator/assetops_simulator/packs/minigrid.py`: PV potential =
  rated x irradiance / 1000, capped by the inverter (clipping); battery SOC in
  %, 95 %-style one-way efficiency each direction; the controller requests the
  deficit (or the whole demand when the battery precedes PV) above the reserve
  in effect, or the surplus to charge; the resolver clips by PCS limit, energy
  above the reserve and headroom, serves loads in critical priority, curtails
  the rest; segments split where a forcing window starts or ends in a step.
- **Host.** `model_for(run)` selects the model by the frozen profile identity;
  model needs reach the kernel as initial values answered by the Foundation.
  The Lab projection gains `electrical` and the execution artifact is schema
  **3**; schema-2 records read with no electrical view.
- **Shipped content.** Template `kobo-mini-grid-60kw` and scenarios
  `kobo-daytime`, `kobo-daytime-overcast` (with the 16:00-18:00 reserve
  override to 15 %) and `kobo-daytime-larger-mill`, targeting `KOBO-001`.

### The demonstration, in numbers

Sunny: no load unserved, battery full at 100 % by early afternoon and PV
curtailed after, 7 kW clipped at 12:00, SOC 55 % -> 89.47 %. Overcast: the
battery holds the 30 % reserve, 56.9 kWh of mill and 6.3 kWh of residential
demand unserved, clinic fully served, and the override carries the evening to
15 %. Larger mill: residential demand unserved in the evening (19.865 kWh),
SOC ends at the reserve. 30 kW requested through a 22 kW PCS: accepted 22 kW,
SOC falls 55/19 %, 2 kWh unserved in the step, next PCS reading 22 kW.

### What this leaves open

Carried in `.ai/MILESTONE_REVIEW_BACKLOG.md` under "Carried from T024": the
controller decides once per step; "battery first" semantics; one of each
electrical machine; the kernel's fuel default import; electrical readings not
yet published (T026); ratios approximated on screen; priority lists
baseline-only; one CDP hang in layout evidence. `var/sites` gained `kobo-001`
(created through the product for the browser evidence).

### T024 fix round 1

Codex review R1-R3 closed on the branch (`.agent/T024-review-packet.md`, "Fix round 1"). Setup now: blocks a scenario/run value at a model-owned Foundation address while still resolving the Foundation's need; blocks needs and controls when the Foundation's `valid_from` is after run start (`_instant`); and validates the single-bus topology, freezing `FrozenBusAttachment` rows (`bus_attachments`, optional in the run document, required by the model at execution) under the new blocking kind `ELECTRICAL_TOPOLOGY_NOT_CONNECTED`. Open: connections are undirected; offset instants unreachable through setup.


## T025a - Generator lifecycle and healthy full-site runtime

In review (`.agent/T025a-review-packet.md`). Contract 9 kept, additively
(`D-2026-09-29-t025-generator-policy-package`).

### What it settled in code

- **Kernel discrete state.** `DiscreteStateSpec`, `DiscreteValue`,
  `TransitionRequest` (`kernel/model.py`); `ModelSpec.discrete_states`,
  `StepContext.discrete`, `Coupling.due` (phase A, before the sample) and
  `Coupling.commit` (phase F, before the resolver). The kernel validates every
  edge and records `DiscreteTransition` (address, previous/next, phase, cause,
  controller ref, instant). `BoundaryState.discrete` / `discrete_for_step`,
  `PrivateTrajectory.discrete_transitions` and
  `FrozenWorldInputs.discrete_initial_values` enter digests and identities only
  when non-empty. `KERNEL_VERSION` stays 1.
- **Typed enums.** `DISCRETE_UNIT = "state"` (`contracts/control.py`); view,
  request and acceptance values are text exactly in that unit, checked on
  construction. Scenarios author a discrete initial value as `value: STOPPED,
  unit: state` (CAUSAL_INPUT, scenario-owned, initializes only).
- **Profile `mini-grid` v1** (`runs/profiles.py`, `packs/mini_grid.py`):
  daytime states plus `generator-state`, `fuel-tank-volume` and seven Option C
  needs (rating, SFC, start/stop thresholds, minimum runtime, start delay, tank
  capacity). New Foundation properties `start-soc-threshold`,
  `stop-soc-threshold`, `start-delay`, `generator-rated-power`; `min` is a
  model-need-only unit (`MODEL_NEED_ONLY_UNITS`), still no scenario unit.
  Bus paths may attach directly (`GENERATION`, via `None`); `FUEL_SUPPLY` is
  tank via generator. `DISCRETE_STATE_RULES` state the contract text.
- **Setup blocks**: initial RUNNING/STARTING or a number for a discrete state
  (`INITIAL_VALUE_NOT_RESOLVED`), a timeline entry on a discrete state
  (`STATE_NOT_SUPPORTED`, T035's), and new kind `LIFECYCLE_TIMING_NOT_ALIGNED`.
- **Lab.** `ElectricalView.generator` (`GeneratorView`); service counts
  `generator_to_load`. Artifact schema **4** only when a generator is recorded;
  every other record is still written as 3, byte-identical. API serves
  `electrical.generator`; `GeneratorPanels.tsx` renders it.
- **Shipped content.** Scenario `kobo-mini-grid-evening` (5-min, 12:00-20:00);
  template gains the generator policy (35/90 %, 5 min, 40 kW).
- **Merge gate** `host/tests/contract9_gate`: all 15 v9 Drafts from `var/runs`
  plus a within-step reserve Draft, captured before any shared change.

### What this leaves open

The owner's `var/sites/kobo-001` lacks the four new properties, so a
`mini-grid` Draft against it BLOCKS until its Foundation gains them. Under
Kobo's `[pv-array, battery, generator]` the battery serves ahead of a running
generator, so the state of charge hovers at the reserve while the generator
charges only when the battery is not discharging. Generator status is not
yet reported (T025b) or staged (T026).

## T025b - Generator policy recipes, reported status and A acceptance

Complete; owner accepted A on 2026-09-29 (`.agent/T025b-review-packet.md` is
also A's integrated acceptance packet; Codex ACCEPT WITH CARRY). Contract 9 kept; `D-2026-09-29-t025-generator-policy-package`.

### What it settled in code

- **`mini-grid` v2** (`runs/profiles.py`, `packs/mini_grid.py` `resolve_v2`):
  v1 unchanged. The stop threshold is a second overridable CONTROL
  (`STOP_THRESHOLD_OVERRIDE`, value in (start, 100]); `ModelProfile.step_aligned_forcings`
  makes setup block an off-step stop window as `LIFECYCLE_TIMING_NOT_ALIGNED`;
  overlap is the kernel's runtime `FORCING_VALUE_AMBIGUOUS`. `effective_controls`
  is (reserve, stop threshold) per step - nothing may assume index 0 is the
  only one. v2 measures generator power over the completed interval.
- **Shipped recipes** `kobo-mini-grid-prolonged` / `kobo-mini-grid-stop-60`
  (03:00Z-11:00Z, 5 min), identical but for one 60 % stop override.
- **Publication profile 4** (`LAB_PUBLICATION_PROFILE_V4`), v3 kept: typed
  `generator-controller/status` (unit `state`, 15 min, bias 0, dropout 40/1000)
  and 15-min generator power. An enum is marked by unit `state`; numeric error
  on it is refused (`refuse_numeric_error_on_a_discrete_signal`). A status at T
  reads phase-B `BoundaryState.discrete`.
- **Artifact schema 5** only when a `state` reading is recorded (4 and 3 keep
  their bytes). `GeneratorStepRow.reported_state/reported_quality`;
  `GENERATOR_STATUS_REPORTED_NOT_STAGED` for profile-4 runs.
- **Envelope** schema 1 and the fuel-only mapping unchanged;
  `refuse_an_enum_under_schema_1` refuses an enum mapping or allowlist entry.
- **Frontend.** Client guards type the step's reported status (closed members,
  qualities) and refuse a `state` reading carrying a decimal or bias.
  `GeneratorPanels` shows reported status beside physical state (fact and
  series column, profile-4 only); `ElectricalPanels` names each effective
  control by address; the stage panel names each `state` signal as observed,
  not staged. Real-backend fixture `kobo-mini-grid-stop-60-execution.json`.
- **Layout evidence** pins the T025a run to `mini-grid@1`/profile 3 and adds
  three v2/profile-4 runs; it creates three more Drafts per run in its store.

### What this leaves open

Setup preselects no publication profile when two are offered (owner question).
The owner's `var/sites/kobo-001` lacks the status signal and generator
properties; demo on a Site created from the current template. Content digests
differ across separately created Drafts (run metadata); reproduction is
trajectory/step equality. Generator status staging is T026's; start-failure
causes are T035's. Demo values await the owner's hands-on check.

## T025c - Persisted Lab history, addressed charts and run identity (L1a)

Complete; owner accepted 2026-09-30 (packet `.agent/T025c-review-packet.md`). Contract 9
kept: an artifact-only addition, no execution-contract bump.

### What it settled in code

- **History contract** `contracts/assetops_contracts/lab_history.py`
  (`LAB_HISTORY_SCHEMA_VERSION = 2`; 1 existed only before the R1 fix and now
  reads as an unknown schema): manifest, five families (`state_samples`,
  `intervals`, `observation_attempts`, `timeline`, `drawing`), each
  `RECORDED`/`NOT_APPLICABLE`/`UNAVAILABLE`; sources `LIVE_SESSION`,
  `PERSISTED`, `LEGACY_ARTIFACT`, `NOT_RECORDED`, `WRITE_FAILED`,
  `HISTORY_UNREADABLE`. Sample phases `POST_EVENT`, `FOR_STEP`,
  `PRECEDING_INTERVAL` (interval samples are kWh over the step in "model unit").
  Only the backend's `simulator_lab_api.py` and `execution_ports.py` may import
  it (`dependency-direction.ps1`, with an anti-vacuity count).
- **Artifact layout** (`host/lab_execution.py`, `host/lab_history.py`): the
  projection document is byte-identical; a TERMINAL artifact appends
  `--- # assetops-lab-history` and one line of canonical JSON with a blake2b
  `history_digest` (distinct from the trajectory digest), written by one atomic
  rename. The digest covers a manifest `projection_binding` over the
  projection's `signals`, `reporting_gaps` and `electrical` view, so an edit to
  the projection alone reads back as `HISTORY_UNREADABLE` (R1 fix). `read()` never parses it; `read_history()` is strict and writes
  nothing. RUNNING artifacts carry none. **Any tool that `yaml.safe_load`s a
  terminal artifact whole now fails on the second document** - split at
  `HISTORY_MARKER` first.
- **Port/route**: `HostLabExecution.history(run)` / `LabExecutionPort.history`;
  gated `GET /runs/{run_id}/execution/history` (`history_payload`). A live
  session answers `LIVE_SESSION` (no digest) even after it completed; the
  artifact answers `PERSISTED` only when no session is held, i.e. after a
  restart. The simulator gained read-only `Execution.applied_events` and
  `bounded_transitions`.
- **Frontend**: `runHistory.ts` (types/guard/fetch), `HistoryInspector.tsx`
  (coverage + records at one boundary), `historyChartModel.ts` (pure chart
  model, stale rule mirroring `reading_at`), `HistoryCharts.tsx` (the only other
  module allowed an `<svg>`, inside `.history-chart__scroll`), `RunHeader.tsx`.
  PV potential/accepted/curtailed/clipped and battery signed power are read
  from the execution projection's `electrical.steps` (host sums); loads,
  SOC, reserve/stop threshold, generator output, fuel and generator state from
  the history. `--series-1..4` tokens added. One selection drives the range
  input, every chart cursor, the exact-value table and the boundary select.
- **Guards/evidence**: `shell-overflow.ps1` admits `HistoryCharts.tsx` under its
  own region rule (three new failure modes, proven). `layout-evidence.mjs` adds
  the T025c section and a `--readback <file>` pass for after a host restart
  (`ASSETOPS_EVIDENCE_ENV` hashes the artifact). Fixture generator
  `host/tests/make_history_fixtures.py`.

### What this leaves open

- The single-run history payload is ~1 MB for the 8 h mini-grid window; full
  wire kept (a selection re-render ~55-65 ms). First paint of the whole run
  screen after a host restart was 1.6-3.2 s after the history response,
  dominated by the page's other panels, not measured in isolation.
- Live history is recomputed on every read; T025d's auto-play must not fetch it
  per step. The history read re-parses the projection YAML.
- Charts are keyed by this model family's state keys (`pv-ac-power`,
  `load-served-power@<load>`, `battery-*`, `generator-*`, unit `L`/`%`); an
  unmatched reported signal is listed as not charted rather than dropped.
- SLD overlays, the causal timeline, requested/accepted panel and playback are
  T025d's; `bus_attachments` is recorded for it.

## T025d - Lab SLD, causal inspection and playback (L1b)

Complete; owner accepted 2026-09-30 (packet `.agent/T025d-review-packet.md`).
Contract 9 and history schema 2 kept: wire additions only, no persisted change.

### What it settled in code

- **Wire** `simulator_lab_api.py` `history_payload(history, run)`: per-interval
  `balance_identities` (exact source/sink sums, residual), `reporting_gaps`,
  and `drawing_context` (`VERIFIED | NOT_RECORDED | DISAGREES` against the
  run's frozen bus attachments; attachments with connection ids only when
  VERIFIED). Live `history()` reports `WRITE_FAILED` (backlog C3, closed).
- **Shared SLD slots** `sites/SiteSingleLineDiagram.tsx` `SldSlotContent`:
  node and connection slots (`ALONG|AGAINST|NONE`, text, detail, optional short
  `label`), arrow marker, contents table, headless `ConfiguredSingleLineDrawing`.
  No slots = Foundation screen unchanged. Labels are short and centred; full
  statement in `<title>` and the table (sentences overlapped boxes, measured).
- **Lab composition** (shell): `intervalDrawingModel.ts` (`bindDrawing`,
  `drawingSlots`, `FLOW_ROLES` keyed by mini-grid flow ids, `drawnValue`),
  `IntervalDrawing`, `IntervalInspection` (C4), `historyTimelineModel` +
  `HistoryTimeline` (C3). One selection = the interval that ENDED at T.
  `HistoryCharts` labels a held reading with its own support (backlog C1, closed).
- **Playback** `shell/runPlayback.ts` `PlaybackScheduler`: one one-boundary
  guarded Step in flight, next only after its answer plus a wall delay
  (0.25/1/2/5 s); stops on pause, terminal, refusal, 404, network error,
  timeout (20 s, re-read), hidden tab, unmount; `laterExecution` never moves the
  display backwards. `RunFrame` disables Step/Run to end while it schedules and
  re-reads history/stage only when it stops. Reload starts paused.
- **Proof** `host/tests/test_lab_cockpit_window.py` (window [55,135) derived
  from template and scenario: event phase, gap, PCS- and reserve-limited
  requests, reversal, balance; duplicate step, restart, pacing digests, reload
  with the kernel unreachable). `layout-evidence.mjs` T025d section + readback.

### What this leaves open

- Drawing binding needs the current Site read to be the frozen Foundation
  version; a future Foundation edit path would make old runs "unavailable"
  (no presentation snapshot is persisted). `DISAGREES` is unit-tested only.
- Flow roles are frontend-keyed; a new model family needs its own roles.
- History read ~1.15 MB for the 8 h window; first chart 3.7 s after the
  response on a cold reload (informational); selection re-render 118-143 ms.
- Trajectory digest is run-bound, so pacing equality across Drafts is shown on
  the reading digest and inputs identity; same-run pacing is host-tested.
- Backlog C2, C4, K1, K3 untouched.

## T025e - Lab cockpit organisation and live playback (L1c)

Complete; owner accepted 2026-10-01 (packet `.agent/T025e-review-packet.md`, evidence
`.agent/T025e-layout-evidence.txt`). Contract 9 and history schema 2 kept;
`contract9_gate` unedited. Three phases; handoffs in `.agent/`.

### What it settled in code

- **Wire** `?since_boundary=n` on the gated history read: append families
  (`HISTORY_APPEND_FAMILY_KEYS`, `simulator_lab_api.py`) keyed by the boundary
  that records the row (intervals, exposures and `electrical_steps` on
  `from_offset`); static families empty; `delta` envelope; typed refusals.
  Prefix stability proved per family in `host/tests/test_lab_history_prefix.py`.
- **Option R** `LabHistory.electrical_steps`: the projection's own
  `ElectricalStepRow`s, joined only where intervals are recorded (live
  projection or the binding-verified stored one); never persisted in the
  history document. Charts read `pv_output` and signed `battery_power` from it.
- **Client** `liveHistory.ts` pure merge + slice index; `runFrameState.ts` one
  owner (execution, history, fullReadDue, cursor); `RunFrame.commit` one read
  and one dispatch per answer; `PlaybackScheduler` awaits `show`.
- **Layout** control strip (`data-control-strip`), then `HistoryCockpit`
  (drawing beside inspection in a fixed row, cursor, charts, timeline, all
  reserved before the first boundary); nine closed `Disclosure`s (new `ui/`
  primitive, `data-disclosure`). Drawing, inspection and raw records are
  memoised on slice/row references; chart points cached per row (WeakMap);
  playing status is one sentence, in-flight on `data-playback-in-flight`.
- **Evidence** `tools/layout-evidence.mjs` opens disclosures before measuring
  and has a T025e section (per-frame sampling, pinned MutationObserver, delta
  bytes, server p95 at boundary 96, `run-frame-commit` measures).

### What this leaves open

- Server delta p95 45.9 ms against 50 ms (within 8 %); capture memoisation
  (the named stop) not taken.
- Charts start below an 800 px first viewport; the charts region grows once at
  the first recorded interval (panels derive from recorded rows).
- A second tab stepping the run can make recorded > clock until the next
  answer (not clipped). The screen-test fake history has no intervals.
- Backlog C2, C4, K1, K3 untouched; T026 adds dispatch panels here.

## T025f - Template versioning and site lineage staleness (S0)

Complete (fast lane; packet `.agent/T025f-review-packet.md`; Claude review ACCEPT WITH CARRIES). No
contract move; no Site record rewritten; no run reads a template.

### What it settled in code

- **Template v2.** `kobo-mini-grid-60kw` is `template_version: 2`; the four
  generator properties T025a added (`2f076d3`) carry `source_version: 2`.
  T025b's status signal and mapping (`0dc42c0`) have no per-entity provenance
  field, so only the bump records them.
- **Fingerprint guard** `backend/tests/test_site_template_fingerprints.py`:
  `PINNED_TEMPLATE_FINGERPRINTS[(id, version)]` = SHA-256 of the parsed
  document as sorted canonical JSON (comments and order are not content).
  Changed content at a pinned version fails naming the template and the bump;
  an unpinned version fails asking for its pin. Kobo v1 is deliberately
  unpinned (it named two contents).
- **Lineage read** `sites/lineage.py` `assess_template_lineage`: `CURRENT`,
  `BEHIND`, `NOT_SHIPPED`, `NO_TEMPLATE`, `UNRECOGNISED_VERSION`, computed on
  read. Served only at gated `GET /api/simulator-lab/site-template-lineage`
  (the catalog is gated; `create_app` must not touch it when closed). The
  operator `/api/sites` shapes are unchanged.
- **UI** `sites/siteTemplateLineage.ts` (client, `templateLineageNote`,
  `useSiteTemplateLineage`) and `sites/TemplateProvenanceText.tsx`: a
  `cell-secondary` line under "Created from template" on the Sites index,
  Overview and Foundation ("Created from v1; current template is v2"). The
  client is handed out only by `simulatorLabSiteTemplateLineage(flags)`,
  resolved once in `App`; closed gate, no read and no note.

### What this leaves open

- The note appears only with the Lab gate open (AC4's gated-surface rule).
- A lineage read that fails shows the recorded provenance alone (no note),
  not an "unknown" note.
- Scenario fingerprints are T025g's; the same digest shape is reusable.

## T025g - The run is the only join of scenario and site (S1)

Complete; owner accepted 2026-10-02 (packet `.agent/T025g-review-packet.md`; `USER_REVIEW_REQUIRED: true`).
Rule `D-2026-10-01-run-binds-scenario-to-site`; contract stays 9 (gate unedited).

### What it settled in code

- **Parser.** `target_site` optional legacy (parsed only when present; null or
  malformed refused); `site_contract: {description}` only (`scenarios/parsing.py`).
- **Run setup** binds the site in the request; only the no-topology refusal
  remains (`runs/service.py` `_refuse_site_without_topology`); legacy
  `target_site` ignored.
- **Lineage** `FrozenSiteBinding.template_lineage` (`runs/models.py`), frozen
  from `SiteRecord.template`; `None` = not recorded (pre-T025g runs). Outside
  `FrozenWorldInputs`. Served as `template_lineage {state RECORDED |
  NO_TEMPLATE | NOT_RECORDED, template_id, template_version}` on `run_summary`
  (top level and `deterministic_identity.site`); `RunHeader` and the setup
  summary render it (`templateLineageText`).
- **Scenario domain reads no site.** `ScenarioDetailService(repository)`;
  resolution code, state sets and payloads gone. Detail payload carries
  `scenario.site_needs {addresses[], device_sources[]}` from
  `scenario_site_needs()`. AST guard in `test_run_binds_scenario_to_site.py`
  allows only `validate_site_id` and `SiteConfigurationInvalid` from `sites`.
- **Picker** (`RunSetupFrame` `SitePicker`): list + per-site `getSite` + gated
  lineage client; nothing preselected; Create disabled until picked.
- **Shipped scenarios v2** (no `target_site`, `site_contract.description`).
  `test_scenario_fingerprints.py` pins `(scenario_id, version)` via the shared
  `backend/tests/content_fingerprint.py` (T025f's guard uses it too) and fails
  on site-naming keys.
- **Join proof** `host/tests/test_t025g_join.py` (READY current Kobo, BLOCKED
  pre-T025a content, v1 refused).

### What this leaves open

- A missing status source does not block (publication declaration only); the
  Draft records its absence. Known deviation in the packet.
- Scenario detail and run setup scroll the page at 375 px (shared FactList and
  PageHeader); below the measured widths.
- `tools/layout-evidence.mjs` cannot complete on an isolated `var/` (needs the
  owner's MG-006 scenario).
- Superseded scenario versions are not retained in the store (git only).
- Picker reads one site detail per site; a summary field would be needed at scale.

## T026 - Dispatch-capable evidence (B extension)

Complete; owner accepted 2026-10-02 after hands-on check (Claude review ACCEPT after fix rounds 1-2; Codex retrospective pending).

Branch `task/T026-dispatch-capable-evidence`; packet `.agent/T026-review-packet.md`,
handoffs `.agent/T026-phase-{1,2,3a}-handoff.md`. Contract stays 9
(`host/tests/contract9_gate` green, execution_contract.py untouched); every change
reaches new Drafts only.

### What is settled in code

- **Schemas.** Envelope schema 2 (families MEASUREMENT / STATE enum member /
  POLICY / OPERATIONAL records; schema 1 still readable, stage schema stays 2,
  `envelope_schema` is the frozen mapping's version). Publication profile 5,
  `mini-grid` v3, site template v3, scenario `kobo-mini-grid-degraded-evidence`.
  Profiles 3/4 keep the fuel-only schema-1 mapping.
- **Evidence.** Capability signals (`pv-inverter-controller/available-power`,
  `battery-pcs-controller/discharge-capability`) exist only under v3; policy
  records (Foundation version, valid-from, source), override records from the
  scenario CONTROL overrides, generator status staged as a typed member. Two
  imperfections: one reporting gap and one hold (`PublicationDelayWindow`: a
  publication due inside the window is released at its end; refused if it would
  reorder, `PUBLICATION_DELAY_REFUSED`). A held envelope enters the stage only
  at its release (`publish(reached_offset_minutes)`, `_still_held`).
- **History schema 3** (`lab_history.py`): append families `records`
  (key occurrence) and `publications` (key release, `HeldPublication`); 7
  coverage rows; schema 2 reads and discloses both UNAVAILABLE; prefix proof
  `test_lab_history_prefix.py` covers both.
- **Screen.** Frontend mirrors both append keys (`liveHistory.ts`); records,
  declared gaps clipped to recorded time and `Publication delay` entries in
  the Applied timeline REPORTING lane; inspector "Publication" column
  (sensor gap / delay / none recorded); stage "Arrival" fact; capability tracks
  join PV and battery curves (second reported track = square marks, dashed
  join); "observed, not staged" shown only when the frozen mapping lacks the
  signal, host statement `GENERATOR_STATUS_REPORTED_STAGED` otherwise.
- **Layout evidence** follows the run's mapping (`EXPECT_UNSTAGED` by profile),
  T025e AC12 section now measures a profile-5 degraded Draft, new T026 section.

### Measurements (this machine, 2026-10-02)

- Delta bytes max 20,249 B (limit 32,768); tick commit p95 30.5 ms max 34.6.
- Server delta p95 at boundary 96 **misses 50 ms**: 108-134 ms through the
  preview proxy on profile 5, 131.7 ms on the T025e profile-4 stop-60 run on
  the same day; in-process (`delta_ms` method, packet) pre-T026 tree 68-93 ms,
  head profile 4 84-95, head profile 5 95-97. T025e's 45.9 ms is not
  reproducible on this machine today; T026 adds roughly 0-15 %.
  Memoisation (backlog T025e C2) NOT taken, owner/Architect to rule.
- Stage: 329-333 envelopes, 267 KB final, per-control write ~36-47 ms CPU.

- **Override issuer (fix round 2, C1,
  `D-2026-10-02-scenario-states-override-issuer`).** Optional `issued_by: OPERATOR`
  on scenario EVENT entries (`TimelineEntry`/`FrozenForcing.issued_by`, in the
  frozen identity only when set); refused except on the stop-threshold and
  battery-reserve forcings. Host `record_inputs` and backend delay refusal read
  it; degraded-evidence v1 declares it (re-pinned, no bump); stop-60 unchanged
  and publishes no override record under profile 5.

### What this leaves open

- Carried to the backlog: AC15 delta p95 misses 50 ms before T026 too
  (performance task, T025e C2); T028 to decide whether stop-60's policy change
  is a policy record.
- Stage order in a stepped run is arrival order (pre-existing); a run stopped
  inside a hold shows "No publication delay recorded" for that reading.
- `kobo-degraded-evidence-deltas.json` fixture is 1.38 MB.
- `tools/layout-evidence.mjs` needs `ASSETOPS_LAYOUT_SITE=MG-006`, a store of
  `.demo/T025c` runs with no executions, and backdated Site `valid_from`; with
  that, 3 pre-existing "blocked table" claims fail (run-setup against MG-006 is
  READY, no blocked table) - environment, not T026.
- No shipped world curtails PV (available == output); T026A owns bias/noise.

## T027 phase 1 - Commit, ingestion and Site > Evidence

Packet `.agent/T027-phase-1-review-packet.md`; handoff `.agent/T027-phase-1-handoff.md`.
In review (phase 1); phase 2 (Overview, AC11, AC22) not started.

- Commit: a release-eligible stage seals once into `var/commits` (contracts
  `committed_artifact.py`; `runs/adapters/json_commit_store.py`); a filed artifact
  is never rewritten, a changed stage is refused, a tampered one reads unreadable.
  `RUN_COMMIT_ROUTE` exists only when the Lab gate is open.
- Release goes through the one product ingest (`evidence/service.py`,
  `ingestion_batch.py`); `received_at` is ingestion's; duplicates idempotent,
  same id/other content a conflict keeping the original, reused batch id with
  other content `BATCH_ID_CONFLICT`; an unknown-Site batch is refused, not stored.
  Store: `var/evidence`, one JSON per Site rewritten per 64-record chunk,
  single-process lock.
- Read model `evidence/read_model.py`: accepted content only; coverage over
  `NEEDED_SIGNALS` keyed by `site_type` (MINIGRID); routes `evidence_api.py`,
  served gate open or closed. Rebuild from artifact text matches (in-process).
- UI: Site > Evidence (`sites/SiteEvidence.tsx`; inspector state in
  `?signal=`/`?source=` + `&record=`; `?batch=` only highlights). Lab
  `RunCommitPanel.tsx` keeps Commit and release apart; Open in AssetOps ->
  `/sites/{id}/evidence`.
- Tabs per `D-2026-10-02-rendered-tabs-per-capability`: Overview|Foundation|Evidence,
  Definition|Topology|Controls; `/` -> `/sites`; rail Sites only.
- Checks: evidence dependency rule (`dependency-direction.ps1`), evidence and
  commit domains (`configuration-persistence.ps1`), navigation-truthfulness
  messages "not rendered, never disabled, never labelled in place"; all proven
  by mutation (no Pester tests for navigation-truthfulness).
- Layout evidence needs T026's isolated method (packet); 3 "blocked table" and
  the T025e delta-budget claims fail for environment reasons.
- Open: AC15 rebuild not proven without host/simulator on `sys.path`; the
  profile-5 run stages no fuel-level envelopes (Fuel NOT_REPORTED).

## T027 phase 2 - mini-grid Site Overview

T027 complete; owner accepted 2026-10-03 after hands-on checks of both phases (Claude reviews ACCEPT after fix rounds; Codex retrospective pending).

Packet `.agent/T027-phase-2-review-packet.md`. In review (task-level, both phases).

- Read model `evidence/overview.py` (`OverviewReadModel`), route
  `GET /api/sites/{id}/overview` in `evidence_api.py` beside Site evidence, so
  served gate open or closed under the evidence dependency rule. Same default
  window as Evidence (`read_model.default_window`).
- One domain list: `OVERVIEW_DOMAIN_SIGNALS` (read_model.py) names each
  MINIGRID domain's signals; `NEEDED_SIGNALS` is derived from it; `DOMAIN_METRICS`
  computes each card. `backend/tests/test_t027_overview.py` pins the domains equal
  to the profile's cards (review N9; proven by mutation).
- Presentation profile: `frontend/src/sites/presentationProfiles.json` (substrate
  data keyed by `site_type`, `{id, label}` per card only), read through
  `sites/presentationProfile.ts`. A profile card the backend does not serve
  renders nothing; a backend card the profile lacks is not rendered (AC22: the
  profile owns existence); the pin test keeps them equal.
- Metric rules: energy and running time are summed over measured intervals only
  (interval mean x interval length), with measured hours stated; instants are
  shown at their own source time; a needed signal with no GOOD record is a named
  gap and its metrics have no value; overlapping records (same span or instant,
  distinct ids) are used by no metric; Fuel is tank level only. Every card and
  the objective strip are `NO_ASSESSMENT` ("No assessment yet").
- Fix round 1: coverage is decided from the records a metric can read
  (`_Window.usable`): gap statuses `NO_INTERVAL_SPAN` and `OVERLAPPING_ONLY` carry
  a named `reason`; interval metrics carry `window_note` ("X h of the Y h window
  measured"), shown in the strip with the metric's label; the client's shape
  check covers every rendered field; the strip counts source and gateway pairs.
  The Foundation tab's "Evidence availability"/"Source health" facts are retired.
- UI: `sites/SiteOverview.tsx` placed by `SiteDetails` through a new `overview`
  slot that `shell/SiteDetailFrame.tsx` fills; evidence links via
  `operatorSiteRoutes.siteEvidenceRecordHref` (`?signal=DEV/SIG&record=MSG`).
  The Overview page's old "Not available for this site" panel (its "no accepted
  evidence" sentence is false after a Commit) is gone.
- Guard: `shell-overflow.ps1` admits `SiteOverview.tsx` as a fourth svg module
  under the same region rules (`.overview-timeline__scroll`; proven by mutation).
- AC14/AC15: the rebuild snapshot and `t027_isolated_probe.build()` include the
  Overview (isolation proven by mutation: `import assetops_simulator` fails it).
- Open: generator running time is whole-interval (backlog, T028); the Kobo v3 interval means
  cover the 5-minute timestep of each 15-minute report, so measured-interval
  energy covers about a third of the window and is labelled so; the profile-5
  run stages no fuel envelopes, so the demo Fuel card shows its gap.

## T028 - Dispatch Finding and Evidence capability table

In review (independent review and owner UI walk pending). Packet
`.agent/T028-review-packet.md`; handoffs `.agent/T028-phase-{1,2,3a}-handoff.md`,
`.agent/T028-presentation-cp{1,2a}-handoff.md`; final layout evidence
`.agent/T028-layout-evidence-final.txt` (presentation cp2b).

- Analytic `analytics/dispatch.py` (model `dispatch-2`, `assess()`); rules and
  thresholds in `backend/tests/dispatch_decision_table.md`. Classification uses
  accepted evidence only; never observed PV as capability, never simulator truth.
  Fix round 1 (Codex R1-R5, `.agent/T028-review-packet.md` "Fix round 1"):
  segments split at constraint-record effective times between reports; 5b
  enforces SOC headroom; equal-rank differing policy/override records are
  classified under each (agree or Indeterminate); evidence digest covers
  bounds, alternatives and fuel basis; reconcile also compares the payload.
- `AssessmentService` (`analytics/service.py`) reconciles assessments: same
  evidence gives no new revision; changed evidence appends a revision and keeps
  the prior; stored under `var/assessments` (`json_assessment_store.py`). Runs on
  ingestion completion (listener in `evidence/service.py`) and on read. Evidence
  never imports analytics (card assessments are injected into `overview.py`).
- Routes (`analytics_api.py`, ungated): `/api/sites/{id}/analytics` (declaration
  with per-analytic `readiness`), `/dispatch`, `/findings`,
  `/assessments/{aid}`, `/assessments/{aid}/revisions`, and global `GET /api/findings`.
- Declaration (`analytics/declaration.py`): id, site types, Finding type, required
  and optional evidence, claim levels, `readiness` basis (`readiness-3`; `-2` made None need neither generator status nor output, `-3` counts unobserved generator-state spans as a limiting gap).
  `score_readiness`: Full/Limited/None, ceiling, missing evidence. A coverage gap
  lowers Full only when it left a segment Indeterminate; absent optional evidence
  is listed and never lowers it. Site-wide, not the selected window.
- Guard `tools/checks/analytic-declaration.ps1` (declaration fields incl.
  `readiness`; no `EXECUTION_REQUIREMENTS` or simulator reads); dependency rule
  (evidence may not import analytics); persistence domain for analytics;
  `navigation-truthfulness.ps1` rail rule is two grouped items. Probes proven.
- Frontend: Performance > Dispatch (only subtab), Finding detail
  `Overview | Evidence | Alternatives` with `ClaimDrawer` reusing T027
  `RecordDetail` (`?record=&claim=`, root unchanged), Findings rail root,
  Site > Findings, `CapabilityReadiness.tsx` above source health. Rail groups via
  `ui/NavRail.tsx` `group`. Presentation profile (`presentationProfile.ts`,
  `presentationProfiles.json` `capabilities`, `performanceSubtabs`,
  `finding_types`) obeys the three rules; orphan lists `EXPECTED_ORPHANS`,
  `EXPECTED_ORPHAN_FINDING_TYPES` in `test_t028_presentation_profile.py`.
- Owner rulings 2026-10-03: Necessary intervals stay assessments without a
  Finding; stop-60 gets no policy record (T034).
- Presentation correction (`D-2026-10-04-practitioner-first-finding-presentation`,
  packet "Presentation correction"): `dispatch.reading()` (meaning, next steps
  with targets, framing) is served at read time on every lineage summary, never
  persisted (adds no revision); readiness carries `question`/`meaning`/`scope`.
  Frontend leads with plain six-part headings, readable UTC periods
  (`readablePeriod`), and puts IDs/revisions/digest, full coverage, fuel inputs,
  Performance method and readiness scoring behind closed `Disclosure`s.
- Totals at closeout: backend 1465, host 616, simulator 244, frontend 1097.
- Presentation revision cp1 (`D-2026-10-04-plain-language-analysis-views`,
  supersedes the disclosure layout above; packet "Presentation checkpoint 1"):
  `analytics/plain.py` generates every product sentence at read time from the
  stored structured assessment (`reading`, `card`, `readiness`, `role`); old
  `dispatch.reading`/`CLAIM_MEANINGS` removed. Finding tabs
  `Overview | Analysis | Evidence | Alternatives` (`/analysis`); Dispatch and
  Site Evidence local `Overview | Analysis` (`?view=analysis`, other params
  kept); shared `sites/assessmentAnalysis.tsx`; card and index "View analysis".
- Presentation cp2a (packet "Presentation checkpoint 2a"): four graphics in
  `sites/assessmentGraphics.tsx` (assessed-period timeline full/compact, fuel
  range, reported values for a selected part `?part=N`, coverage by input),
  region `.assessment-graphic` named in `shell-overflow.ps1`; card
  `lead_timeline`/`lead_revision` from `plain.card_timeline`; Site Evidence
  `?view=analysis&assessment=<id>` one-period coverage, apart from readiness.
- Presentation cp2b (packet "Presentation checkpoint 2b"): vocabulary guard -
  list `frontend/src/test/productVocabulary.json` (v1), scanner
  `productVocabulary.ts`, suite `shell/__tests__/t028Vocabulary.test.tsx`
  (29 Lab-off + 2 Lab-on states), exemptions only `data-vocabulary-exempt=
  source-reference|user-owned|lab` on single values; live scan `t028Journey`
  in `tools/layout-evidence.mjs` (`ASSETOPS_LAYOUT_T028_JOURNEY_ONLY=1` runs
  it alone, Lab-off); backend test scans served evidence statements and
  rejection reasons against the same list. Read-time rejection `reason`
  (`evidence/read_model.py` `REJECTION_READINGS`; stored detail unchanged);
  plain `NORMALIZATION_STATEMENT`, `INTERVAL_STATEMENT`; source mode label
  "Demonstration data". Layout evidence `.agent/T028-layout-evidence-final.txt`
  (615 PASS, 4 known FAIL) and `-lab-off.txt` (4 PASS).
  Exclusions also by value: `data-vocabulary-reference` (`sites/vocabularyReference.ts`).

### What this leaves open

- Owner decisions: any-gap vs limiting-gap readiness rule; site-wide vs selected
  window readiness.
- Overview shows whole-interval generator runtime beside a different-basis
  assessment (backlog item stays open for the metric).
- `GET /api/findings` and `/analytics` run `assess_site` per Site on read.
- Ingestion keeps the first record at a key, so same-key recipe re-runs do not
  revise intervals.
- Recommendation and History tabs, verification rules: T034.
- Legacy product copy outside the T028 journey (Foundation, Sites index
  filters, other pages) is not scanned by the vocabulary guard: post-T029
  inventory follow-up. `INPUT_WORDS` coverage labels are still a frontend map.
- Persisted `summary`/claim-limit wording unchanged by the presentation
  correction (Necessary "4.5-open", `(dispatch-2)` in the Candidate limit);
  rewording them appends a revision per lineage.

## S1-01 - Persisted Site Foundation (in review)

Branch `task/S1-01-persisted-foundation`; packet `.agent/S1-01-review-packet.md`.

### What it settled in code

- PostgreSQL 16 (`docker-compose.yml`, `postgres:16.4-alpine`, 127.0.0.1:55432,
  dbs `assetops` + disposable `assetops_test`); `DATABASE_URL` required, no
  backend default; commands in `backend/README-db.md`.
- Alembic `backend/migrations/versions/0001_foundation_identity.py`: tenant,
  site, site_import, asset, gateway, source, foundation_revision; composite
  `(tenant_id, site_id)` FKs; btree_gist + GiST exclusion over currently
  recorded validity; triggers make revision content immutable (only
  `superseded_at` settable once) and registration rows undeletable.
- `sites/foundation_records.py` (rows, `FoundationStore` port),
  `sites/foundation_content.py` (content = rendered YAML `foundation` minus
  version/valid_from; record rebuilt through the strict parser; gaps),
  `sites/foundation_service.py` (import, `revision_at`, reserve publish:
  split earlier segment + changed later segment, supersede the old row),
  `sites/adapters/postgres_foundation_store.py` (sole SQL writer, Site row
  lock), `sites/import_kobo.py` CLI.
- Cutover (`sites/cutover.py`): `ProductSiteDirectory` serves `/api/sites`
  and detail (imported codes from Postgres, listed once; collision or changed
  legacy bytes = 503 conflict); `LegacySiteGate` wraps the YAML repository
  for ingestion, Evidence, Overview, analytics and Lab (409
  `AWAITING_EVIDENCE_MIGRATION`; Lab start/step/run-to-end/Commit 409
  `SITE_AWAITING_MIGRATION`; setup refusal kind `SITE_AWAITING_MIGRATION`;
  stage GET adds `frozen_basis`).
- `foundation_api.py`: GET foundation (`at`, `knowledge_at`), GET versions,
  POST revisions (battery reserve only). Tenant = `config.DEVELOPMENT_TENANT_SLUG`.
- Frontend: `sites/siteFoundationClient.ts`, `FoundationRevisionPanel.tsx`
  (slot `revision` on `SiteConfiguration`), `?at=` in the Foundation URL,
  `AwaitingEvidenceMigration` on Overview/Evidence/Performance.
- Guard: `configuration-persistence.ps1` rule 8 (sole Postgres writer, driver
  ban, report-writer confinement, main.py routing scan, Lab/gate refusals).

### What this leaves open

- `create_app` with an injected Site repository and no Foundation store is a
  legacy-only composition (no imports); product composition fails closed.
- Fix round: no tenant row means no imported Sites, while an unreachable store
  still fails closed. Cutover tests run by default over
  `tests/foundation_fakes.py`. Carried from review: m1 (lexical guard), m4
  (identity UPDATE/TRUNCATE), m6 (layout skip), m7 (YAML scan cost).
- Layout tool (correction round, Architect 2026-10-08): only the imported
  Site's "Publish reserve change" is allowed; the Kobo Lab sections (T024-T028)
  are reported SKIP until S2; `ASSETOPS_LAB_SITE` binds run setup elsewhere.
  Draft-screen claims still need the isolated `var/` store.
- The reserve form states the resulting period: start to end of the containing
  period, or "no end".
- Lab Site creation for a new code that later gets imported is not migrated.
- S1-02: bindings, Readiness, snapshot; S2-02/S3/S5 evidence/dispatch/Overview cutovers.

## S1-02 - Versioned bindings, Readiness and configured SLD (in review)

Branch `task/S1-02-bindings-readiness` (cut from S1-01 `06ac8f5`); packet `.agent/S1-02-review-packet.md`. Decision `D-2026-10-08-s1-bindings-roles-and-snapshot` (answers in `.agent/architect-S1-02-answers-2026-10-08.md`).

### What it settled in code

- Migrations 0002 and 0003 add two tables:
  - `signal_binding_set_revision` holds one time-valid version per Foundation-aligned period. It names its Foundation revision and gateway, and pins `snapshot_schema` and `snapshot_sha256`.
  - `signal_binding_revision` holds one bound channel per row.
  - Database constraints:
    - GiST exclusions: one current set per Site and role set, and one current binding per channel `(source, signal)`;
    - same-Site composite foreign keys, plus a source-of-gateway foreign key that also checks `device_id`;
    - append-only triggers, with closing a set closing its rows;
    - a trigger that keeps each set inside a current Foundation revision.
- Role vocabulary: `sites/binding_roles.py` holds `minigrid-roles-1`. Battery reserve is covered by a Foundation control. Only IDENTITY and ENUM conversions are accepted; LINEAR is refused.
- Publication: `sites/binding_service.py` validates the whole set atomically. A refusal returns the code and every problem, and writes nothing.
- Joint plans: `FoundationStore.publish_configuration` writes the Foundation and binding parts of one plan under the Site lock.
- Alignment: `sites/binding_alignment.py` `finalize` aligns binding sets to Foundation periods and pins each snapshot (canonical serializer `assetops.acquisition-snapshot/1`). The reserve publish now runs through it as well, so a Foundation split also re-aligns the binding sets.
- API:
  - The Foundation read gains `bindings`, a configuration-only `readiness` (READY_TO_REPORT, INCOMPLETE or UNKNOWN) and `acquisition_snapshot`.
  - New `POST .../foundation/bindings`.
  - New `GET .../foundation/snapshot`. It serves the stored canonical bytes and refuses a hash mismatch. It is a development download only: gateway authentication is pending.
  - `versions` now lists `binding_sets`.
- Conversion: `sites/convert_kobo_bindings.py` takes the explicit fixture `backend/conversions/kobo-001-bindings.json`, holding nine legacy IDENTITY mappings plus the status ENUM the decision declared.
- UI:
  - `FoundationBindingsPanel` shows Readiness, the bindings, unbound channels, the snapshot and binding removal.
  - The period picker lists binding periods.
  - For a stored Site, the SLD lists only bound signals and marks each device with no bound channel.

- Fix round (Codex review M1-M3, Architect rulings D2-D5):
  - Migration 0004 stores `snapshot_canonical` (NOT NULL, CHECKed against `snapshot_sha256`, immutable under the 0003 trigger). Downloads serve those bytes; they never rebuild from registration rows. 0004 backfills existing rows only when the v1 serializer reproduces the pinned hash, else refuses.
  - `validate_bindings` refuses `BINDING_ROLE_AMBIGUOUS` when a Foundation period declares more than one eligible component for a ONE role the publication needs, and `BINDING_BATTERY_MISMATCH` when the SOC binding names a battery other than the reserve's.
  - `readiness()` is INCOMPLETE while the selected Foundation revision has configuration gaps, reported as `readiness.foundation_gaps`, apart from `missing_roles`.
  - On a stored Site the shared "Signal mappings" table is captioned as the selected binding set's links (binding version and record, Foundation version) with a "Binding ID" column; legacy Sites keep "Mapping ID".

### What this leaves open

- Readiness is a section of Foundation, not its own subtab (ruling D2). Guard rule 5 forbids a "Readiness" subtab label.
- Gateway-credential download and ingestion are S2.
- A Foundation split re-issues unchanged binding rows with new IDs (ruling D4). Each split copy is a new snapshot.
- Registration identity fields stay updatable; a later publication snapshots their then-current values. Download availability still depends on current configuration gaps.
- Codex carries m1 (mixed Foundation/binding read under concurrency), m2 (conversion rerun provenance), m3 (insert-only alignment trigger; Foundation-only `store.publish()`).

## S1-03 - Foundation organized as Site model, SLD and Readiness views (in review)

Branch `task/S1-03-foundation-organization` (cut from S1-02 `d8dd3e9` + planning `f639990`); packet `.agent/S1-03-review-packet.md`. Decision `D-2026-10-08-s1-foundation-organization` (`.agent/architect-S1-ui-organization-2026-10-08.md`). Frontend and guards only; no backend or API change.

### What it settled in code

- Routes: `SITE_FOUNDATION_VIEW_ROUTE_PATH` (`/sites/:siteId/foundation/:foundationView`) beside the Foundation route. `siteFoundationViewHref(siteId, segment, at)` carries `at`. A segment that is not a view renders `RouteNotAvailableFrame`.
- `sites/FoundationSubtabs.tsx`: `FOUNDATION_SUBTABS` is the view row, exactly Site model (segment ""), Single line diagram (`sld`) and Readiness (`readiness`). It renders as a link row (`site-tabs site-subtabs`) with `aria-current`. The old `Definition | Topology | Controls` contents row and `.section-nav` use are gone.
- `sites/StoredFoundationViews.tsx` composes the three views for an imported Site from one stored read:
  - Site model: status strip, gaps panel when present, configured-topology cards beside identity, controls with the reserve form, then audit and inventory disclosures.
  - SLD: drawing first (`SiteSldPrimary`), then the configured-parts table, then detail disclosures (`SiteSldDetails`, nodes and connections, devices with the D5 table).
  - Readiness: verdict with counts and what is missing, role coverage, signal bindings with the removal form, registered sources, acquisition details with the snapshot.
- `FoundationRevisionPanel.tsx` and `FoundationBindingsPanel.tsx` are split into composable pieces.
- The status strip names a scheduled or past binding period when the Foundation version is current, so a future binding set is never called "in effect now".
- The verdict separates "Not configured: Battery reserve" from unbound channel roles.
- Legacy Site: one page, no view row. Its `/sld` and `/readiness` addresses state "This view needs an imported Site".
- CSS:
  - Status strip, panel pair, plant cards, verdict, metric row and action form.
  - Attention tokens (`--attention-*`) for historical and incomplete states.
  - At 640 px and below the rail stacks above the content, a shell-wide change.
  - At 1100 px and above the SLD drawing scales to its panel.
- Guards:
  - `navigation-truthfulness.ps1` requires the exact three views in order.
  - It still refuses Change & effect / Changes, the superseded vocabulary (now including Definition, Topology and Controls) and disabled or labelled-in-place affordances.
  - `layout-evidence.mjs` measures each view of an imported Site, at a new 390 px width as well.

### What this leaves open

- Owner side-by-side UI acceptance; S1 merge is held on it.
- Decisions taken under the ambiguity rule are in `.agent/S1-03-questions.md`: the narrow-shell stacking, the legacy view-route state, and the omitted legacy-only panels.
- Lab layout claims are still unmeasured. The run aborts at Lab run-setup when served by the product backend, as in S1-02.


### S1-03 fix round and S1-02 n6 (settled in code)

- `BindingService.publish` carries a binding edit through every contiguous later current period of the same binding set with unchanged bindings (Foundation-split copies), re-aligned atomically; it stops at a later independent binding change. The 201 body adds `applies_until` (null = open-ended) and `stopped_by_binding_version`; Readiness shows the end. Tests on the in-memory fake (`TestBindingEditThroughFoundationSplits`); no migration.
- `SiteFoundationFrame`: "needs an imported Site" only for `migration_required`; other failures say stored versions are unavailable.
- `navigation-truthfulness.ps1`: backtick labels, non-literal labels and a hard-coded `Changes` / `Change & effect` destination fail; page-level and panel-order tests in `siteFoundationRevision.test.tsx`.
- Phone-width shell rules are scoped to `.app-frame--operator` (set by `OperatorShellLayout`); `shell-overflow.ps1` fails an unscoped narrow `.app-frame`/`.nav-rail` rule. Lab shell unchanged; its phone layout is an open carry.
- Parts table column is "Channels" with a bound-versus-unbound legend; the SLD drawing precedes its paragraphs; the controls table names priority members.

## S2-01a - Registered Kobo Lab basis (in review)

Branch `task/S2-01a-registered-lab-basis`. Phase 1: commits `ce65b8d`, `fabbfc2`, `f1b78bd`, `ad0b210`. Phase 2: commits `8d0e1d3`, `7c2b271`, `d0042fb`. Packet `.agent/S2-01a-review-packet.md`; phase-1 anchors `.agent/S2-01a-phase-1-handoff.md`. Decision `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary` with its amendment; Architect answers are in `.agent/architect-S2-01a-answers-2.md`.

### What it settled in code

- Selection: `sites/registered_basis.py::select_registered_basis` picks the Foundation and binding set at the run's source start, as recorded at `knowledge_at`. It refuses with typed `BasisRefused` codes:
  - not registered, inconsistent, or crossing a boundary (`end_time` included);
  - a role-set mismatch, or an invalid Site row;
  - any snapshot error.
- Snapshot verification: `binding_service.acquisition_snapshot(now=)` classifies a snapshot as CURRENT or HISTORICAL. A historical one is verified from its pinned identity, and current-row gaps are reported separately.
- Run adapter: `runs/registered_basis.py::RegisteredLabBasis` supplies the Site record, the binding-derived links and a `RegisteredBasis`.
  - Links are frozen from binding rows only: `mapping_id` is the binding revision ID, and the asset code must be in the selected Foundation.
  - The frozen display name is `site_display_name`.
  - `RegisteredBasis.__post_init__` re-hashes the stored snapshot text, so a tampered stored run is refused on reload.
- Run read: `simulator_lab_api.configuration_basis_payload` reports `LEGACY_FILE`, or `REGISTERED` with:
  - the revisions, the hash and the two selecting instants;
  - `site_metadata.source = CURRENT_SITE_ROW_AT_SETUP`;
  - `accepted_evidence: false`.
- Lab writes: `_refuse_if_imported(record, *, commit=False)` is the one shared boundary.
  - A registered Draft may start, step and run to end.
  - Commit refuses any registered run with `REGISTERED_COMMIT_UNAVAILABLE` (409).
  - A pre-import YAML Draft of an imported code keeps `SITE_AWAITING_MIGRATION`.
- Stage read: `_frozen_basis` reports `configuration_store: REGISTERED` with the basis and `can_release: false`. Legacy Drafts are unchanged.
- Guard: `configuration-persistence.ps1` rule 8 requires the plain boundary call on start, step and run-to-end, and `commit=True` on Commit. It also requires the registered Commit refusal to come first in the boundary. Both parts were proven non-vacuous.
- Host: no code change. `host/tests/test_registered_kobo_execution.py` shows:
  - the ten binding links, including `generator-controller/status`, resolve as frozen;
  - the two legacy-only capability links are absent;
  - registered and legacy daytime runs produce identical observations;
  - public reports carry no cause, oracle, intent or private keys.
- Frontend:
  - Setup labels each picker row with its configuration store.
  - For a registered Site, setup reads the configuration the start selects and sends that version. It blocks Create with the snapshot reason and shows `reasonCode`.
  - The run page has a `ConfigurationBasisPanel`, with name and time zone labelled as setup metadata.
  - The Stage shows the frozen basis.
  - `commitBasisBlock` disables Commit when `can_release` is false or the basis is unreadable.
- Layout evidence: `ASSETOPS_LAYOUT_S2_01A_RUN=<run_id> node tools/layout-evidence.mjs <base>` measures a registered run at 1280 and 640 px.

### Open

- Q4: two KOBO-001 capability signals are unbound, so a profile-5 run reports them as unconfigured.
- Q5: the imported Foundation lacks generator parameters, so mini-grid models are BLOCKED. Generator status is proven at link resolution only.
- Backlog: Site name, type and time zone are current-row metadata (snapshot v1 does not version them). Asset-code identity is mutable before S2-02.
- The full `layout-evidence.mjs` run stopped after the run-setup sections because the browser stopped answering (no FAIL before that point).


## S2-01b - Durable simulated gateway (in review)

Packet `.agent/S2-01b-review-packet.md`; phase handoffs `.agent/S2-01b-phase-{1,2,3a}-handoff.md`.

- Wire: `contracts/assetops_contracts/source_envelope_v3.py` (length-delimited message id, canonical V3 text), `ingestion_batch_v2.py` (sealed, bounded, source-homogeneous Batch V2; digest excludes `payload_sha256`), `gateway_report.py` (`assetops.simulated-device-report` v1, the only text that crosses the process boundary), `gateway_stage.py` (`RegisteredStageView`, `GATEWAY_LEDGER`, upload always `PENDING`). Vectors: `contract-fixtures/source-envelope-v3-vectors.json`.
- Gateway: `gateway/assetops_gateway/` is a separate process (`python -m assetops_gateway serve --config`), importing contracts only. WAL SQLite ledger with single-writer file lock, immutability triggers, per-(gateway,source,epoch) sequence, `report_admission` dedupe, `mapping_hold` holds; authenticated local IPC with a protected credential file.
- Host: `host/gateway_publication.py` publishes a registered run's public reports through `assetops_gateway.ipc` only (guarded); `lab_execution.py::_stage` for registered runs uses the gateway; a delay-window run is refused before activation. `execution_adapter.py::frozen_resolutions` makes the frozen identity the resolution authority.
- Profiles: `registered-kobo-publication` v1 = v3 plus `resolution="0.000001"` on each numeric signal; quantized half-even after bias in `simulator/.../observation/transform.py`; frozen as `DeterministicIdentity.signal_resolutions` (written only when non-empty). Refusals `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE`, `PUBLICATION_UNIT_MISMATCH`. Every run's `frozen_inputs` gains a "Device resolution" row.
- API: `GET /runs/{id}/stage` returns `registered_stage_payload` for a registered run (never the file Stage); `signals[].resolution`; profile summary `device_resolutions`, `requires_registered_site`.
- Frontend: `runSetupClient.ts::isGatewayLedgerStage` accepts only pending, receipt-free, non-eligible ledgers and yields `status: "gateway"`; `GatewayLedgerView.tsx` renders it; `commitBasisBlock`/`releaseBasisBlock` block Commit and release for it. F1 closed: `releaseBasisBlock` blocks Resume/Retry for a committed legacy artifact whose Site was imported since. Run view shows a resolution column and half-step note; setup shows the profile's resolution and labels the two refusals.
- Q4: `ObservationView` docstring no longer says reported minus bias recovers a quantized or gap-hidden value exactly.
- Layout: `ASSETOPS_LAYOUT_S2_01B_RUN=<run_id> node tools/layout-evidence.mjs <base>`.

### Open

- ENUM is proved by a direct public generator-status observation, not by the daytime run (S2-02 owns a selectable generator-status run). Delay windows are refused only (S2-01c owns delayed admission).
- No product path writes gateway provisioning; it is an operator config file. No IPC idle timeout; Windows credential protection relies on the profile ACL.
- Whole-series republish per step is O(n); a long run needs a watermark. Hold rows are not byte-fixed (`seen_count`).

## S2-01c - Gateway diagnostics and fault scenarios (in review)

Packet `.agent/S2-01c-review-packet.md`; handoffs `.agent/S2-01c-phase-{1,2,3a}-handoff.md`; open questions `.agent/S2-01c-questions-6.md` (3, 4, 5 answered).

- Gateway ledger: schema 3 keys `seal_refusal` by `(source, epoch, snapshot, outbox_state)` (R1); `diagnostic_config` (frozen), `diagnostic_outbox` (one immutable report per cadence slot, READY only, never received), `health_observation` (contacts, injected faults). Schema 4 `publication_clock(lab_run_ref)` forward-only.
- Wire: `contracts/assetops_contracts/gateway_diagnostics.py` `GatewayDiagnosticsV1` + `DiagnosticConfig` (60 s cadence, 1 GiB/256 MiB WARN/STOP demo triggers); vectors `contract-fixtures/gateway-diagnostics-v1-vectors.json`. `publication_schedule.py` holds the Lab-private `PublicationSchedule`/`DelayedReport`.
- Service: STOP refuses acquisition before any write; `mapping_error_count` counts mapping kinds only; queue age on real-UTC `created_at`; `admit_at_run_clock` stamps V3 `published_at` from the scoped virtual clock. IPC ops `diagnostics`, `emit_diagnostic`, `advance_publication_clock`, `admit_at_run_clock`, `inject_fault` (fixture only; no Lab port method).
- Profiles/scenarios: `registered-kobo-publication` v2 (`publication_clock: RUN_VIRTUAL`, opt-in); `kobo-daytime-delayed-publication` v1 and `kobo-daytime-post-run-publication` v1 (closing window [710,725)); setup allows only a RUN_VIRTUAL reporting-path WINDOW ending at most one timestep after the interval (`runs/service.py` `_post_run_release_window`). Manifests `host/fixtures/gateway-fault-scenarios.v{1,2}.json`.
- Host: `lab_execution.py` `advance_publication` (`release_basis` LIVE_SESSION|STORED_SCHEDULE_ONLY; refusals CLOCK_NOT_SUPPORTED, CLOCK_BACKWARD, AHEAD_OF_WORLD, SCHEDULE_UNREADABLE, SCHEDULE_MISSING, INSTANT_INVALID), `publication_schedule`, `gateway_diagnostics` (AVAILABLE|GATEWAY_UNAVAILABLE).
- API: `GET /runs/{id}/publication`, `POST /runs/{id}/publication/advance` `{instant}`, `GET /gateway/diagnostics`; profile `publication_clock`; seal refusals carry `outbox_state`.
- Frontend: `runSetupClient.ts` `isRunPublicationSchedule` (no private fields, absent schedule never a list), `isGatewayDiagnostics` (unavailable carries no counters, no ACKED), optional client methods `getPublication`/`advancePublication`/`getGatewayDiagnostics`; `GatewayPublicationPanels.tsx` renders schedule, advance and diagnostics with clock labels on a registered run's Stage; setup names the profile's publication clock. F2: `releaseBasisBlock` blocks Resume/Retry while the basis is pending, unreadable or unreported.
- Layout: `ASSETOPS_LAYOUT_S2_01C_RUN=<run_id> node tools/layout-evidence.mjs <base>` (includes a fetch-intercepted Sealing-refused row).
- Fix round 1 (`D-2026-10-09-s2-ordered-publication-and-closing-boundary`): IPC `admit_at_run_clock` requires `at_instant`; the gateway advances the run clock to it in the admission transaction and, once the clock has passed it, answers replays only and refuses a new admission `PUBLICATION_INSTANT_PASSED` (`service.py` `_clock_at`, `_admit_in(replay_only=)`). Host `RegisteredGatewayPublisher.publish_in_boundary_order` + `lab_execution.py` `_release`: each reached boundary after the schedule's `admitted_through` watermark is admitted at its own instant (due delayed reports first), sealed per boundary; post-run leftovers go at the explicit advance instant. Undelayed `published_at == source_time`; run_to_end and single steps give identical envelope and batch bytes. Read `SCHEDULE_MISSING` for an executed run with no schedule and no session; Lab view renders gateway HELD releases as held.
- Fix round 2 (`D-2026-10-09-s2-publication-gap-and-batch-boundary`): `PublicationSchedule` persists `world_boundaries_completed` and `ordinary_stopped_at` and derives `ordinary_publication()` (NOT_STARTED|CONTIGUOUS|COMPLETE|INCOMPLETE|TERMINAL_GAP). `advance_publication` with no live session refuses `PUBLICATION_GAP` (both instants in the detail) before the Lab clock, the gateway or a seal moves. `_release` records `ordinary_stopped_at` when the gateway refuses an ordinary boundary `PUBLICATION_INSTANT_PASSED`. Read and advance refuse `SCHEDULE_MISSING` for an executed run even with a live session, and `_stage_registered_virtual` creates a schedule only before the execution artifact exists. The API schedule read carries `admitted_through`, `ordinary_publication` and `ordinary_stopped_at`. The panel shows an "Ordinary publication" fact (`data-ordinary-publication`), a `data-publication-gap` paragraph and the `PUBLICATION_GAP` refusal.

### Open

- Architect: questions-6 (legacy schedules without a boundary count, live terminal-gap clock movement, first-start schedule failure, refusal shape, which refusal is terminal). questions-5 answered in `.agent/architect-S2-batch-answers-2026-10-09.md`; questions-3/-4 in `.agent/architect-S2-01c-answers-4.md`.
- N1 (exact IPC key-set refusal kind) and N2 (HELD/SCHEDULE_MISSING strings at 640 px) carried to the S2 checkpoint.
- Carries C2 (AC5 diagnostic bytes across a real reconnect not asserted) and C3 (full seeded layout run unverified) for the S2 milestone checkpoint.
- A seal refusal after admission leaves a delayed report PENDING until the next advance. S2-02 owns upload, central receipt and diagnostic freshness.

## S2-02 - Authenticated ingestion and Site Evidence (in review)

Packet `.agent/S2-02-review-packet.md`; walkthrough `.agent/S2-02-owner-walkthrough.md`; handoffs `.agent/S2-02-phase-{1,2,3a,3a2,3b}-handoff.md`, `.agent/S2-02-corrections-handoff.md`.

- Postgres ledger (migrations 0005/0006): `ingestion_batch`, `accepted_evidence`, `evidence_rejection`, `ingestion_disposition`, `batch_refusal`, `recompute_job` (`dispatch` domain); `gateway_credential` (selector + SHA-256 verifier), `gateway_access_event`, `gateway_diagnostic`(+refusal). Three confined writers (guard `tools/checks/configuration-persistence.ps1`).
- Ingestion: `evidence/ledger_service.py` `BatchIngestionService.submit` (413/422/403/409/202/200, per-chunk transactions, first-receipt `received_at`); Receipt V2 contract `contracts/assetops_contracts/ingestion_receipt_v2.py`.
- Credential: `provision_gateway issue` writes `<credential-out>.<selector>` owner-only (DACL/0600) and verifies it BEFORE one DB transaction (verifier, revocation, enablement); gateway `read_upload_credential` re-checks the DACL. Rotation = new file + gateway config switch + restart.
- Transport: `python -m assetops_backend.serve_tls` (426 on plaintext credentialed routes); gateway `uploader.py` bounded passes, exact bytes, receipt verification before ACK; IPC `deliver`, `release_run`, `run_delivery`.
- Reads: `evidence/ledger_reads.py` + four Site Evidence routes for imported Sites behind `permits_cutover` (schema v2 report bound to tenant/Site/environment/inventory digest, newest report decides, `var/evidence/migration/<site>/`); CLI `python -m assetops_backend.evidence_migration run|show`. `GET /api/sites/{id}/gateway-health` UNKNOWN/CURRENT(2x cadence)/STALE.
- Frontend: `sites/LedgerSiteEvidence.tsx` (overview/analysis/inspector/reading detail), `shell/RegisteredDeliveryView.tsx` (Commit release claim, batch table, blockers).
- Demo: `tools/s2_demo_walkthrough.py run|serve` (isolated `git archive` tree under `%LOCALAPPDATA%\AssetOps\s2-demo`, DB `assetops_s2demo`, API 8610, TLS 8643, new openssl cert). Layout: `ASSETOPS_LAYOUT_S2_02_RUN=<run> ASSETOPS_LAYOUT_S2_02_RECORD=<evidence id> node tools/layout-evidence.mjs <base>`.
- Dev DB KOBO-001 comparison regenerated 2026-10-09 (schema v3, empty set, PASSED).
- S2-01c carries closed here: N1, N3, C2.
- Fix round 1 (review F1, Architect batch 4 Q28/Q26/Q32/count): forwarded scheme headers -> 426 and `serve_tls` `proxy_headers=False`; `provision_gateway` reconciles an ambiguous issue COMMIT via `PostgresGatewayAccess.issue_outcome` (ISSUED / proven NOT_ISSUED / `ISSUE_OUTCOME_UNKNOWN` exit 3, file kept); comparison report schema v3 binds `store_root` (digest of adapters' `canonical_root()`), checked in `permits_cutover` and by the configuration-persistence guard; walkthrough step 8b posts a labelled fault-fixture sibling batch, step 5 prints the post-run batch (245/292 -> 246/293 = profile-v2 delayed 15:00 battery SOC report).

### Open

- Questions-7 (Q37-Q40) await the Architect (fail-closed defaults shipped); questions-5/6 answered in `.agent/architect-batch-answers-4.md`.
- C3/N2 full seeded layout run still unverified.
- Crash/resume 202 and closing-boundary rejection are Postgres test evidence only; the rejected sibling is live via the labelled fault fixture.
- Generator-status run and capability channels unconfigured; no S3 projection; physical devices remain a pilot gate.

## PRE-S3-03 - Delivery checker and next-work report (in review)

Built on `plan/pre-S3-startup`; packet `.agent/PRE-S3-03-review-packet.md`, questions `.agent/PRE-S3-03-questions.md`.

- `frontend/docs/architecture/delivery_next_work.cjs` owns delivery-plan validation and the `next-work` report; `check_v69_dependency_registry.cjs --next-work [--out f]` / `--verify-report f` drive it (exit 3 on refusal or stale inputs). Fixtures: `test_delivery_next_work.cjs` (node:test).
- Registry claim portions now carry `id`, `core`, `variant` (bounded/positive/unknown) and `state` (delivered/open/unmapped/excluded). Only `open` portions with real-node `technical_requires` and no proposed IDs are reviewed paths; `delivered` needs resolved `delivered_by` plus evidence. `real` panels need every portion delivered and an accepted visual gate.
- 15 S1/S2 bounded portions recorded delivered (14 panels `reviewed_mapping:true`, all `partial`); V-01 is `delivery_plan.visual_gates.V-01` (effort unrecorded, so blocked); `outside_ranking` holds A-finding-index and A-money-comparability.
- `tools/check-all.ps1` is the normal check command (architecture, navigation, workflow, registry, delivery fixtures, ledger).
- Open: the live report refuses (37 approved core panels unmapped: evidence-analysis:2 and all S3-S7 cores still name proposed R-/UI-/D- IDs). Independent mapping review pending. Stale Readiness text after S2-02 (foundation_api.py:270,286,295-298; FoundationRevisionPanel.tsx:318-353) is unowned (Q8).

## S3-01 phase 1 - Role vocabulary and `s3-dispatch-cases-v1` fixture (reviewed, accepted with carries)

Built on `task/S3-01-dispatch-assessment` (1a `e68da1c`, 1b `7e9da8c`..`f508bae`); packet `.agent/S3-01-phase-1-review-packet.md`, questions `.agent/S3-01-questions-1.md`.

### What it settled in code

- `sites/binding_roles.py`: `minigrid-roles-2` = roles-1 + optional `pv_available_power` (INVERTER) and `pcs_discharge_capability` (POWER_CONVERSION_SYSTEM), kW, ONE. MINIGRID publishes roles-2 and still serves roles-1; `BindingService.publish(role_set=)` refuses an unserved set; the replayed Kobo conversion records roles-1.
- `FoundationService.publish_component_properties` (no API route) and `sites/demo_configuration.py` (CLI `python -m assetops_backend.sites.demo_configuration --fixture backend/conversions/kobo-001-s3-dispatch-demo-config.json --tenant demo [--steps properties]`): labelled SIMULATED demo configuration - generator rated power/start 35/stop 90/start-delay 5 (TEMPLATE v2) from 2026-10-01, roles-2 bindings with both declared capability channels from 2026-10-02. Idempotent; earlier periods split, never rewritten.
- `runs/profiles.py` `registered-kobo-publication` v3: v2 + generator status (STATE_SIGNAL), generator power at 15 min, both capability signals at resolution 0.000001, discharge-capability reporting gap; `record_channels=()`. v1/v2 unchanged.
- The Lab publishes a declared signal only where the frozen basis maps it (`host/execution_adapter.py:690-705`), so on a roles-1 basis capability readings never exist on the public path (not a gateway hold).
- Scenario `config/scenarios/kobo-s3-dispatch-degraded-reporting.yaml` v1 (prolonged world, 1 h discharge-capability gap, 10-min SOC hold, no override/record); fingerprint pinned.
- `tools/s3_dispatch_cases.py run|verify` (reuses S2 `Demo`; DB `assetops_s3cases`, ports 8710/8743, own pipe): 8 cases, 2868 accepted readings; manifest with public IDs only, Lab run IDs under `private_oracle`; `verify` reloads accepted IDs from Postgres and fails on any mismatch or unmet precondition. Run output `.agent/S3-01-dispatch-cases-run.txt`, manifest copy `.agent/S3-01-dispatch-cases-v1.manifest.json`.
- Registry `I-sim-dispatch-cases` has an `acceptance_target`; status stays `open` (tied to `I-S3-01`).

### Open

- No analytic, `EvidenceQuery`, cohort selection or persistence yet (phase 2); no UI (phase 3).
- Q1-Q6 unanswered: contradiction is a labelled fault-fixture batch; poor quality = UNAVAILABLE readings + gap (no SUSPECT); same-epoch overlap is ambiguous by construction; the ordinary path produces late but not out-of-order-within-source readings; `fuel_level` is not published by `mini-grid` v3 registered runs.
- Any Foundation-UI binding edit on a MINIGRID Site now records roles-2 (risk noted in packet).
- The manifest's IDs are environment-specific (fresh import UUIDs per run); replay regenerates, `verify` compares within one environment.

## S3-01 phase 2 - Typed seam and durable dispatch assessment (active, phase review pending)

Built on `task/S3-01-dispatch-assessment` (`75886d1`..HEAD); packet `.agent/S3-01-phase-2-review-packet.md`, questions `.agent/S3-01-questions-2.md`, table `backend/tests/dispatch_3_decision_table.md`.

### What it settled in code

- `analytics/assessment_inputs.py`: `EvidenceQuery` (tenant/Site/domain, UTC half-open `Window`, `knowledge_at`, optional explicit cohort, roles, 6 h `BRACKET`), `AcceptedReading`, `RoleBinding`, `ControlValue`, `EvidenceQueryResult`, `CohortSelection`/`CohortLimit`, `AnalyticInputSet` with canonical `input_sha256` (evidence IDs + digests, cohort, as-accepted and selected revisions, controls, bindings, coverage, window, model; not `knowledge_at`).
- `analytics/cohort.py`: default cohort = streams `(gateway, source, epoch)` with a reading in the window; overlapping epochs of one source -> `AMBIGUOUS`; explicit selection; per-channel `SEQUENCE_ORDER_INVERTED` / `REPORTS_OVERLAP` limits. No epoch-name, manifest or receipt-order logic.
- `analytics/dispatch_v3.py` (`MODEL_VERSION = "dispatch-3"`, reuses `dispatch.ANALYTIC_ID`, no own declaration): pure; window + interval assessments; rows 3/4/5a/5b carried; row 1 unavailable; row 2 = Candidate-blocking minimum runtime only; window `COMPLETE|LIMITED|INDETERMINATE`. `dispatch.py` (`dispatch-2`) untouched.
- Migration `0007_dispatch_assessment`: `analytic_run` (idempotent basis key), `analytic_run_evidence`, `assessment_revision`, `analytic_run_assessment` (all append-only), `recompute_job.last_error`.
- `analytics/adapters/postgres_assessment_store.py`: the fourth product DB writer (guard rule 8 extended: own tables plus `recompute_job` lease/retry/scheduling only). Evidence read joins the ACCEPTED disposition; cutoff on `decided_at`; Foundation/binding selected bitemporally at the cutoff, tenant/Site scoped.
- `analytics/assessment_worker.py` + CLI `python -m assetops_backend.analytics.assess_dispatch process-jobs|reconcile|assess`: lease (SKIP LOCKED, expired leases reclaimed), UTC-day windows over job window +/- bracket, one commit for runs + revisions + DONE under a lease token; retry with back-off, FAILED after 3 with `last_error`; `reconcile` enqueues windows whose latest default run has another model version or configuration digest.
- `tools/s3_dispatch_cases.py`: case `late-out-of-order` renamed `late-publication`; new `out-of-order-fault-fixture` (10-07, labelled epoch) and `late-central-acceptance` (10-08, two batches held at the gateway; cutoff A/B); each case carries its persisted `dispatch-3` result and a check; `verify` reloads runs and the cutoff-A revision.

### Open

- No read API, projection table, UI or Performance cutover (phase 3); phase 3 derives `CURRENT/STALE_PROJECTION/...` from runs + overlapping jobs unless Q7 rules otherwise.
- Questions Q1-Q8 in `.agent/S3-01-questions-2.md` (controls at cutoff vs as-accepted, minimum runtime mapping, day windows, fixture-epoch default read, in-flight cutoff, interval key anchoring).
- Same-epoch overlap (10-04) yields a window `INDETERMINATE` with no intervals (generator series ambiguous).

## S3-01 phase 3a - Durable dispatch read, comparison and cutover gate (active, phase review pending)

Built on `task/S3-01-dispatch-assessment` (`aaa47ae`..HEAD); packet `.agent/S3-01-phase-3a-review-packet.md`, questions `.agent/S3-01-questions-3.md` (Q9-Q13), handoff `.agent/S3-01-phase-3a-handoff.md`.

### What it settled in code

- `analytics/cohort.py` `_multi_epoch`: two or more epochs of one source in a window make the default cohort `AMBIGUOUS`, overlapping or not (F3).
- `postgres_assessment_store.lease_job(max_attempts)`: an expired lease on its last attempt is `FAILED` with "lease expired on attempt N of M" (F6). Worker `run_pending(reconcile=True)` reconciles every assessed Site (F4).
- Migration `0008_assessment_selection`: append-only `analytic_run_selection` (commit order `seq`), written per DEFAULT run; `run_heads` reads it. Guard rule 8 lists it.
- `analytics/dispatch_v3.py`: a `LIMITED` window always names its limitation; interval limitations are lifted as `INTERVAL_LIMITED: interval from <first_on>: ...` (the necessary-interval open-bound anomaly; Q13).
- `analytics/dispatch_read.py`: `derive_status` (UNASSESSED/PENDING/CURRENT/STALE_PROJECTION/FAILED + reasons) over one REPEATABLE READ `window_snapshot`; `window`/`run`/`revision` with as-accepted revisions, `selection_note`, `CUTOFF_LABEL`, typed `UNAVAILABLE`, `superseded_keys`, demo annotations kept apart from provenance (`adapters/demo_manifest_file.py`, env `ASSETOPS_DEMO_FIXTURE_MANIFEST`).
- `performance_api.py` (mounted in `main.py`): `/api/sites/{code}/performance/dispatch/cutover` always; `windows/{day}`, `runs/{id}`, `revisions/{id}` 409 `PERFORMANCE_CUTOVER_CLOSED` until the gate opens, 404 unknown/foreign, 503 store unavailable.
- `analytics/performance_comparison.py` + CLI `python -m assetops_backend.performance_migration run|show`: MATCH / INTENTIONAL_DELTA / MISSING_SOURCE / UNPROVEN; gate opens only on PASSED, current legacy digest, same tenant/Site/environment, zero live lineage breaks. Reports under `<EVIDENCE_STORE_ROOT>/migration-performance/<site>/`.
- Fixture: case `necessary-interval` (scenario `kobo-s3-dispatch-necessary-run` v1, 10-09); fault-fixture SOC template chosen by minimum `(source_time, sequence)`.

### Open

- No UI yet (phase 3b): `SitePerformance.tsx` `DispatchView` still reads the file-backed `/dispatch`; anchors in the 3a handoff.
- Q9-Q13 resolved by `D-2026-10-11-s3-phase-3a-version-and-cutover`; built as `dispatch-3.1` (next entry).
- A window read evaluates the full input basis per request; `run_pending` reconciles every assessed Site per pass.

## S3-01 dispatch-3.1 - Model version bump, stored-window reassessment, stricter comparison (active, review pending)

Built on `task/S3-01-dispatch-assessment` (`05f9b4d`..HEAD) under `D-2026-10-11-s3-phase-3a-version-and-cutover`. Packet: the "dispatch-3.1" section of `.agent/S3-01-phase-3a-review-packet.md`. Handoff to 3b: `.agent/S3-01-dispatch-3-1-handoff.md`. Questions: `.agent/S3-01-questions-4.md` (Q14-Q16).

### What it settled in code

- `dispatch_v3.MODEL_VERSION = "dispatch-3.1"` covers Q9 and Q13. Stored `dispatch-3` runs and revisions are immutable history. The worker reconcile, already keyed on `model_version`, reassesses their windows; `assess_dispatch process-jobs` runs it. Explicit selections are not remapped.
- `dispatch_read`: `run` and `revision` carry `model_note` (`OLDER_RULE_RESULT ...` for a non-current model); a `dispatch-3` head reads `STALE_PROJECTION` with `MODEL_VERSION_CHANGED`.
- `postgres_assessment_store`:
  - `lineage_breaks(..., model_version)` counts `selected_heads_other_model`;
  - `accepted_evidence` maps a message ID to its evidence ID;
  - `selected_intervals(..., domain, bracket)` adds the overlapping `window_jobs`.
- `performance_comparison` (report schema v2, which records `model_version`):
  - `STALE_MODEL` and `STALE_PROJECTION` are `UNPROVEN`.
  - `MATCH` and `INTENTIONAL_DELTA` need the cited records in the interval's evidence.
  - `INTENTIONAL_DELTA` applies only through `DOCUMENTED_DELTAS` (`CAPABILITY_CHANNELS_REQUIRED`, rows 5a/5b), and only on the interval's own limitation.
  - `MISSING_SOURCE` gives `EXCEPTIONS`, which keeps the gate closed.
  - The gate refuses a report made under another model, and refuses while any head uses another model.
- The cutover route's read label is now `POSTGRES_DISPATCH_3_1`. The decision table has "Model versions" and "Comparison" sections.

### Open

- Phase 3b UI. Its required displays are listed in the handoff, and the cutover route does not yet expose the report summary.
- Q14-Q16 are open, with fail-closed defaults built.

## S3-01 phase 3b - Performance > Dispatch UI, cutover summary, walkthrough (in review)

Built on `task/S3-01-dispatch-assessment` (`b04b904`..closeout). Packet: `.agent/S3-01-review-packet.md`; questions Q17-Q22 in `.agent/S3-01-questions-5.md`.

### What it settled in code

- `performance_comparison.comparison_summary` and `classified_revision_ids`. `permits_performance_cutover(..., selected_revision_ids=)` refuses when a classified MATCH or INTENTIONAL_DELTA revision is no longer selected or the selection is unreadable (R2). An empty-set report needs no recheck.
- The cutover route returns `comparison`. File-store errors give a 503 with a closed body (`read: CLOSED`, `permitted: false`, `unavailable.code` COMPARISON_STORE_UNAVAILABLE or ASSESSMENT_STORE_UNAVAILABLE) (R3). `main.py` wires the live `selected_intervals`.
- Frontend: `sites/PerformanceDispatch.tsx` (Overview and Analysis views), `performanceDispatchClient.ts`, `dispatchWords.ts`; `SitePerformance.tsx` renders it when the legacy declaration is AWAITING_EVIDENCE_MIGRATION. Address state `?day=&revision=&block=&view=`. Without `?day=` the screen opens on today UTC.
- Fuel, money and Finding panels are gated and typed unavailable. Demo annotations are shown apart from provenance.
- `tools/s3_dispatch_walkthrough.py` (prepare/serve/recover; private DB `assetops_s3walk`, port 8820) and `tools/s3-dispatch-evidence.mjs` (32 claims at 1440 and 390).
- Comparison recovery test closes R1-C1.

### Open

- No list of assessed days; older-rule label and late-evidence history proven by tests only; demo notes absent from walkthrough data; staged FAILED/STALE days have no interval.
- Carries: R1-C2, 3a R4/R5. Committed fixture manifest is per run (evidence IDs change on a new producer run).
- Owner checkpoint pending.

## S4-01 phase 1 - Finding store, episode matcher, `s4-finding-cases-v1` (active, review pending)

Built on `task/S4-01-finding-identity` (`bcbc3f4`, `6b891ef`, closeout; fix round 1 `7781821`..`71dd0b6`). Packet `.agent/S4-01-phase-1-review-packet.md` (Fix round 1 section); questions Q1-Q9 in `.agent/S4-01-questions-1.md`, Q10-Q15 in `.agent/S4-01-questions-2.md`.

### What it settled in code

- Migration 0009: `finding` (immutable key/anchor/cohort/matcher version, `recurs_after_finding_id`, `split_from_finding_id`), `finding_revision` (UNIQUE `(finding_id, revision_no)` and `(finding_id, basis_sha256, transition)`, primary `assessment_revision_id`), `finding_revision_assessment`, `finding_revision_evidence` (cited only), `finding_merge`; all append-only. Alembic head is 0009.
- `analytics/finding_episode.py` (pure, `finding-episode-1`): CURRENT windows of the current model only; <=20-min bridges only through observed Necessary or modelling-reason Indeterminate; recurrence link only across an observed OFF; window revision cited but not in the basis hash.
- `analytics/finding_service.FindingMatcher` reads via `DispatchReadService.window` under a fence; `adapters/postgres_finding_store.py` is the fifth guarded writer (INSERT-only, advisory lock, `FindingFenceMoved`, `rows()` reload).
- Composition `build_finding_matcher` / `build_finding_store`; CLI `assess_dispatch match-findings|finding-rows`.
- `tools/checks/configuration-persistence.ps1`: only the Finding store writes Finding tables, insert-only.
- `backend/conversions/s4-finding-cases-v1.json` + `tools/s4_finding_cases.py run|verify` (DB `assetops_s4cases`, TLS 8763; labelled authenticated Batch V2; per-run IDs in `%LOCALAPPDATA%/AssetOps/s4-finding-cases/s4-finding-cases-run.json`). Run on `6b891ef`: all checks OK, VERIFY PASSED (`.agent/S4-01-finding-cases-run.txt`).
- `backend/tests/test_s4_finding_store_postgres.py`: all cases in one Site, stale window, F07 test-scoped upgrade, append-only, moved fence.
- Fix round 1: anchor-first split ownership (B1); fence counts the Site's `finding_revision` rows (B2); recurrence only with proven gap coverage and both OFFs observed (B3); bridges need full observed coverage incl. stop spans (Q2); basis includes window revision IDs and input digests (Q4); `support_sha256` + `BASIS_REFRESHED` for provenance-only changes (Q5); `REOPENED` after NO_LONGER_SUPPORTED (C3). Pure `tests/test_s4_finding_episode.py` (16).
- Producer `F01-gateway` (Q6): a Lab run sealed by the durable registered gateway (epoch `s4-gateway-epoch-1`) over TLS on 2026-10-02 opens a SUPPORTED Finding. Run on `71dd0b6`: 11 Findings / 30 revisions, VERIFY PASSED.

### Open

- No Finding read API/UI yet (phases 2-3). F07 is test-scoped: no reviewed later `dispatch-3.x`.
- Backdated controls append collateral BASIS_REFRESHED to Findings on earlier days; every same-day reassessment appends BASIS_REFRESHED to that day's Findings - phase 2/3 History must group them (Q14).
- Lab refuses a 0-minute minimum runtime, so the gateway case runs on 10-02, outside the fixture controls (Q15).
- 3+-way merge untested by fixture (pure test only); matcher is linear in assessed days.

## S4-01 phase 2 - Exact Finding root/revision read (active, review pending)

Packet `.agent/S4-01-phase-2-review-packet.md`; questions `.agent/S4-01-questions-3.md` (Q16-Q20).

- Read service `backend/assetops_backend/analytics/finding_read.py` (`FindingReadService.finding`,
  `.window_state`, `revision_groups`); routes `backend/assetops_backend/finding_api.py`:
  `GET /api/sites/{site_code}/findings/{finding_id}?revision_id=&after_revision_no=&limit=` and
  `GET /api/sites/{site_code}/finding-windows/{day}`; wired in `main.py` via
  `composition.build_finding_read_service` (manifest env `ASSETOPS_FINDING_CASES_MANIFEST`, else
  `ASSETOPS_DEMO_FIXTURE_MANIFEST`).
- Status matrix: `access` seam gives 401/403 before lookup (default admits the development tenant's operator
  context and says so in `access_basis`, Q16); unknown/foreign Site, root or revision 404; malformed ID 422;
  no DB or store failure typed 503 `FINDING_STORE_UNAVAILABLE`.
- Selection: omitted revision = latest recorded; exact ID pins; `selection.replay` states no `knowledge_at`
  replay. Every revision returned in `revision_no` order (paged) with prior/new window and interval IDs,
  Foundation/binding revisions of the cited runs, basis/support digests, `support_changed`; groups are a hint.
- Currentness compares the revision's own cited WINDOW assessments with the S3 read's current selection
  (`CURRENT`, `FINDING_MATCH_PENDING`, `STALE`, `PENDING`, `FAILED`, `NOT_ASSESSED`; merged =
  `MERGED_INTO_CANONICAL`). `window_state` returns `NO_FINDING` only for a CURRENT window without Candidate or
  Finding.
- Matcher (`finding_episode.py`) now records `claim.continuity` (bridged gaps: segments+reasons, observed stops
  with both OFF times, `candidate_minutes_added "0"`) and `claim.recurrence` (LINKED with both OFF bounds and
  covered windows, or NOT_ESTABLISHED + reason; split parts NOT_APPLICABLE). Not in the basis digest. The read
  resolves OFF evidence IDs from the cited interval revision's evidence at the recorded time
  (`PostgresFindingStore.revision_lineage`).
- Store reads added: `finding_detail`, `revision_lineage`, `findings_over` (SELECT only; the existing
  persistence guard still limits Finding writes to the store - proven by a write in `finding_read.py`).
- `DemoManifestAnnotations` also labels an opt-in `gateway_sealed` case (`DEMO_MANIFEST_GATEWAY_CASE`).
- Producer: R2 asserts F01-gateway cites only gateway-sealed batch evidence (102 IDs, 0 outside); writes
  `s4-finding-cases-manifest.json`; `verify` reads every Finding through `assess_dispatch finding-reads`.
- Open: Q17 (contradictory report between stop OFFs is invisible to the matcher); Q18 window-state route vs
  S4-04; no UI (phase 3); R1 gateway-day labelling for the owner walkthrough.

### S4-01 phase 2 fix round 1 (review B1/B2/C3; Q17-Q20)

Commit `254b843`; packet "Fix round 1" section; questions `.agent/S4-01-questions-4.md` (Q21-Q24).
- Matcher `finding-episode-2`: `FindingMatcher.bases` reads each CURRENT window's selected run input evidence
  once per run (`DispatchReadService.run`) into typed `StateReport`s; `_stop_proof` confirms a stop only when both
  OFF endpoints are in the run evidence and every report between last ON and next first ON is accepted, GOOD,
  in-cohort and OFF, in CURRENT non-Indeterminate windows with no generator cohort limit; otherwise the stop does
  not bridge (two Findings) and recurrence is `NOT_ESTABLISHED: SEPARATION_STOP_NOT_CONFIRMED: <reason>` (Q21).
  Continuity stops carry `proof` (evidence IDs, run/window IDs, `reports_sha256`).
- Q20: relation facts in `support_sha256`, full continuity/recurrence records in `basis_sha256`; the opening
  recurrence record is carried on `Episode.recurrence` into every later revision. Old v1 rows would get an
  appended revision (basis includes the matcher version); 0009 reached only disposable DBs.
- Q18: `finding_match_pass` (append-only, added to unmerged 0009; persistence guard table list extended) records
  each committed pass's fenced `selection_seq`; `window_state` says `NO_FINDING` only when a v2 pass covers the
  window's current selection, else `FINDING_MATCH_PENDING`. B1: Indeterminate window = `NOT_DETERMINABLE`; body
  has `window_claim_level`, `window_limitations`, `selected_run_id`, watermarks, `finding_match`.
- B2: a pinned non-latest revision's currentness is `SUPERSEDED_BY_LATER_REVISION` + `latest_revision_id`;
  `state.claim_is_current_refers_to = LATEST_REVISION`.
- Q19: `build_finding_router(gate=...)` reuses `main.performance_gate`; an unconfigured gate is closed. Closed:
  default detail and window reads 409 `PERFORMANCE_CUTOVER_CLOSED`; pinned `revision_id` 200 with
  `audit_only`, `SOURCE_CLOSED` projection, no S3 read and S3 links withheld (`links.performance`). The
  `finding-reads` operator CLI is ungated (Q23).
- Open: Q21-Q24; phase 3 UI.


## S4-01 phase 3 - Site Finding detail UI and closeout (in_review)

Task `tasks/S4-01-finding-identity.md`; packet `.agent/S4-01-review-packet.md` (all phases); questions
`.agent/S4-01-questions-5.md` (Q25-Q30); owner steps `.agent/S4-01-owner-walkthrough.md`.

### What it settled in code

- Route `SITE_FINDING_ROUTE_PATH` = `/sites/:siteId/findings/:findingId`, exact version `?revision_id=` (the API
  parameter), view `?view=analysis`, block `?portion=` (`frontend/src/shell/operatorSiteRoutes.ts`,
  `siteFindingHref`). Frame `SiteFindingFrame` (`frontend/src/shell/SiteAnalyticsFrames.tsx`): trail Sites > site >
  Findings > Finding, Findings tab current, h1 from the lifecycle. The T028 file-backed `/findings/:siteId/:assessmentId`
  stays as it was.
- `frontend/src/sites/findingClient.ts`: the 401/403/404/409 `PERFORMANCE_CUTOVER_CLOSED`/503 responses map to
  named states, plus `getFindingWindow` for `finding-windows/{day}`. `findingWords.ts` holds the plain words for
  lifecycle, transition, currentness and window states.
- `frontend/src/sites/SiteFinding.tsx` leads with the most limiting state, in this order: closed source (audit
  record only, C7), merged, earlier version, lifecycle, then currentness. It then shows the panels:
  - What happened: separate minutes cards, money "Not yet available", and a keyboard-selectable block bar.
  - What limits this conclusion: limitations, joined gaps and stop bridges with the sparse-reporting caveat, and
    recurrence that never implies the earlier Finding is open.
  - What to do next: not yet available.
  - Where to look next: Dispatch days carrying the interval revision, records, related Findings.
  - Versions: BASIS_REFRESHED runs grouped with count and exact links.
  - Records summary: demo-manifest kind in plain words.
  The Analysis view holds the full IDs and codes behind `data-vocabulary-exempt`.
- Dispatch day (`PerformanceDispatch` `DayFindings`) reads `finding-windows/{day}`. It links non-merged Findings
  and names NO_FINDING / NOT_DETERMINABLE / FINDING_MATCH_PENDING / NOT_ASSESSED without a link.
- Tools: `tools/s4_finding_walkthrough.py` (DB `assetops_s4walk` copied from `assetops_s4cases`, API 8840, web
  5340, staged PENDING 2026-10-09; `links` prints this run's addresses) and `tools/s4-finding-evidence.mjs`
  (CDP 9343; 36 claims at 1440/390; run record `.agent/S4-01-phase-3-evidence-run.txt`).

### Open

- Q25 the S3 `unavailable.finding` text remains; Q27 no priority/confidence chip; Q28 the generic
  `layout-evidence.mjs` needs a Lab backend and was not run to completion; Q29 ledger row unchanged.
- Carries still open: C5 one-hop canonical, C6/C9 read and pass cost (S4-04), C8 recurrence record only on the
  opening revision.
- `?portion=` is an index into the selected version's blocks (Q30).

## V-01a - Site and Foundation visual fidelity (in_review)

Branch `task/V-01a-foundation-visual`; packet `.agent/V-01a-review-packet.md`. Visual gate only; no new data claim.

- `FoundationPeriodStrip` (`FoundationRevisionPanel.tsx`): an `?at=` instant that is not a period start now
  gets its own selected option ("At ... (from the address)"). Before this, the controlled select fell back to
  "In effect now" on reload or shared links while showing another period.
- `Panel` takes an optional `description` (the v6.9 `.panel-head p` sub-line, CSS `.panel__description`).
  It is used on Site inventory, Configured topology, the SLD panel and Configuration readiness. The Readiness
  sub-line carries the PRE-S3-04 separation at the top of the view.
- Sites list panel retitled "Site inventory" (v6.9 label). The topology bus label carries the bus's declared
  rating (`data-topology-bus`, e.g. "AC bus · 400 V").
- Devices caption (`SiteConfiguration.tsx` `SiteFoundationDevices`) no longer says "none has reported". It
  states only that reporting is not assessed here (backlog carry).
- Tools: `tools/v01a_foundation_walkthrough.py` (copy of `assetops_s4cases`, plus an empty migrated DB;
  API 8860/8861, web 5360/5361) and `tools/v01a-foundation-evidence.mjs` (25 claims at each of 1440 and
  390 = 50; CDP port 9361).
- Q1-Q5 were answered by the owner and ruled in `D-2026-10-12-v01a-owner-visual-rulings` (round 2 below).
- Open: `SiteOverview.tsx:241` stale "No window" text stays with S5-01 (backlog C2).
- Open: the shell-wide `layout-evidence.mjs` stops at the Lab run-setup precondition in the walkthrough tree.

### V-01a round 2 (owner rulings; packet section "Round 2")

- `SitesIndex.tsx`: columns Site / Type / Mode / Setup details / Actions; `Last analysed` and
  `NO_ANALYSIS_IN_WINDOW` removed; `DIRECTORY_ANALYSIS_ABSENT` note under the table.
- Readiness: Badge tones `configured` (green, tick) and `config-gap` (amber, "!"), configuration-only;
  `ReadinessLegend` in `FoundationBindingsPanel.tsx`.
- Part selection: `component=` beside `at` (`FOUNDATION_COMPONENT_PARAM`, `siteFoundationViewHref`);
  `SiteFoundationFrame` clears an undeclared part and shows `[data-selected-part-missing]`;
  `SelectedPartPanel` on all three views.
- SLD (`SiteSingleLineDiagram.tsx`): bus-bar layout (`latticeFor`, `runPoints`, `SldBus`, `SldNode`),
  `data-sld-layout="bus-bar"`, `SLD_CONFIGURED_NOT_LIVE`, optional `SldSelection` (svg becomes a named
  `group`, parts are `role="button"` toggles). The slot text is now "Readings not assessed here"; the constant
  name `AWAITING_RUNTIME_OR_EVIDENCE` is unchanged. The view model is unchanged except `sldSymbolFor`.
- Icons: `sites/componentIcons.tsx` (one icon family per type, used by the SLD and `ComponentTypeIcon` on the
  topology cards); `ui/RailIcon.tsx` (mock line icons; `NavRailItem.icon`).
- Shared type, colour, tab and rail tokens follow the mock (`ui/tokens.css`). This affects every screen.
- Guard: `shell-overflow.ps1` allows fixed-size icon svgs in exactly those two modules.
- Open: bus-bar routing has no detour for a supply that bypasses an occupied conversion row. No stored topology
  has one.
- Open: the V-01a evidence tool does not exercise Finding detail. The store holds 11 Findings, but its prepare skips the comparison step, so the index is empty and detail answers PERFORMANCE_CUTOVER_CLOSED. The reviewer verified detail at 1440/390 by hand on a private copy.
- Open: the Lab run interval drawing now uses the bus-bar geometry; its browser label-collision check (layout-evidence T025d) is unverified behind the Lab precondition.
- Open: `layout-evidence.mjs` still stops at the Lab run-setup precondition.


### V-01a round 3 (readiness and organization; packet section "Round 3")

- `sites/ReadinessOverview.tsx` (new): `readinessCards()`/`ReadinessCards` (four cards from typed `configuration_gaps`;
  Unknown only on `NO_EFFECTIVE_REVISION`), `ReadinessEvidenceTable` (six rows; Confirmed always "Not recorded"),
  `GatewayStatusPanel` over the S2 `/gateway-health` read (`App.tsx` → `SiteFoundationFrame` `gatewayHealth`).
  Gateway badges are neutral; contact is labelled as server-time, apart from the selected `at`.
- Plain-first layers: `Disclosure` "Advanced details — Foundation records | diagram records | roles, channels and
  records | selected part channels" (`foundation-advanced`, `sld-advanced`, `readiness-advanced`,
  `selected-part-channels-{model,sld}`). "Review or change bindings" (`[data-review-bindings]`) opens the Readiness one.
- Site model: `IdentityPanel` critical-load/loads/productive-use/financial facts; `FoundationControlsPanel`
  "Evidence / change" column (`[data-control-link]`). SLD: `[data-sld-missing]` note; parts table shows counts only.
- `SelectedPartStrip` replaces the global Selected part panel (topology panel and `SiteSldPrimary` `strip`);
  Readiness shows `[data-selected-part-chip]`. Sites: "Operating view" column and `sites-aggregate-absent` note.
- Tools: `v01a_foundation_walkthrough.py` gains `--db/--empty-db/--work-name` and `drop` (refuses owner defaults);
  `v01a-foundation-evidence.mjs` 185 claims, gateway variants via DevTools `Fetch` interception (documented in its
  header); `layout-evidence.mjs` expects six Sites columns and excludes `[data-review-bindings]` from actions.
- Open: only STALE gateway contact is reachable on the stored copy; other states are intercepted-response evidence.
- Open: registry `readiness:2#a/2#b/3#a` and the ledger/registry conditional caveats wait for independent review
  and the owner's decision; nothing was edited.
- Open: `.readiness-cards` 2-column band (480-900 px) unmeasured; `layout-evidence.mjs` still stops at the Lab precondition.

## V-01b - Lab and Evidence visual fidelity (in_review)

Task `tasks/V-01b-evidence-lab-visual-fidelity.md`, branch `task/V-01b-evidence-lab-visual`, diff base `b1ac0a8`.
Packet `.agent/V-01b-review-packet.md`, handoff `.agent/V-01b-handoff.md`, questions `.agent/V-01b-questions-1.md`
(Q1-Q8, fail-closed defaults shipped), owner guide `.agent/V-01b-owner-walkthrough.md`. No backend change.

- Site Evidence (`frontend/src/sites/LedgerSiteEvidence.tsx`, `ui/primitives.css` "V-01b Evidence" block): status bar
  of window facts with neutral "No capability conclusion yet" badge and "Analysis →"; `evidence:1` "What we can
  conclude now"; `evidence:2` "Data sources" table beside `evidence:3` "Most useful next evidence" (two-column
  ≥1100px); each unsupported portion is a "Not available yet: ..." statement. Analysis: `evidence-analysis:1`
  accepted records table (`listRecords`, "Open record" → "Exact message as received"), `evidence-analysis:2`
  "How each limit is set" (Q4). Technical panels under closed "Advanced details — ..." disclosures.
- Conflict original time: refused-readings table "Original reading" column renders `conflicts_with_source_time`
  with a link to `conflicts_with_evidence_id` (S2-02 batch-4 carry closed).
- Lab run (`shell/RunIngestionOverview.tsx`, `shell/runIngestion.css`, `RunFrame.tsx`, `RunCommitPanel.tsx` `onRead`):
  h1 "Draft run" (Q2) then h2 "Gateway & Ingestion": status strip, four `[data-flow-box]`es, `lab:1` envelope `<pre>`,
  `lab:2` truth vs observed, `lab:3` release and ingestion with the Commit panel, `lab:4` boundary; "Execution and
  recorded history" below; seven "Advanced details — ..." disclosures. `GatewayLedgerView.tsx` Q1 Stage label.
- Lab phone shell: `SimulatorLabShell.tsx` uses `app-frame app-frame--lab`; every <640px shell rule lists both
  `.app-frame--operator` and `.app-frame--lab` (S1-03 Q1 carry closed). Guard `tools/checks/shell-overflow.ps1` 2b
  requires each narrow selector part to start with one of the two and fails when either has no narrow rule
  (non-vacuity proven in the packet). `overflowContainment.test.tsx` asserts the class.
- Tests: `shell/__tests__/v01bEvidenceVisual.test.tsx` (10), `v01bLabIngestion.test.tsx` (9); order/name updates in
  `cockpitLayout`, `runExecution`, `simulatorLabGate`, `s2LedgerEvidence`, `runsInventory` (Commit first).
- Tools: `tools/v01b_lab_evidence_walkthrough.py` (prepare/links/serve/drop, `--db/--empty-db/--work-name`, owner
  ports 8862/8863/5362/5363); `tools/v01b-lab-evidence-evidence.mjs` (101 claims at 1440/390, SourceEnvelope trace,
  intercepted 503 gateway variant); `tools/layout-evidence.mjs` registered Lab Site/dates/profiles, Kobo registered run
  section (`ASSETOPS_LAYOUT_V01B_ONLY`, `ASSETOPS_LAYOUT_V01B_RELEASED_RUN`), `ASSETOPS_CDP_PORT`, run-setup overflow
  proof at 390px. Full run with KOBO-001: 398 PASS / 5 FAIL, all named preconditions.
- Open: Q8 drawing precondition (T025d label claims unmeasured); Q1 stale Stage upload constant; `.action` cascade
  over `.action--primary` elsewhere; layout tool creates a draft per run; ledger/registry caveats wait for owner
  acceptance (nothing edited).

## G-01 - Mock-gap catalogue and orphan guard (in_review)

Task `tasks/G-01-mock-gap-catalogue-and-guard.md`, branch `task/G-01-mock-gap-catalogue-and-guard`, diff base `db98e54`.
Packet `.agent/G-01-review-packet.md`, handoff `.agent/G-01-handoff.md` (design + phase log), questions
`.agent/G-01-questions-1.md` (Q1-Q4, fail-closed defaults shipped), owner guide `.agent/G-01-owner-walkthrough.md`.
No backend change.

- Registry schema `assetops.v69.dependency-registry.pilot.v3` with top-level `mock_gaps` (version 1,
  `gap_enrolled_screens: []`); one gap `G-readiness-gateway-firmware` (data_source/absent/open/unplanned, element
  `readiness:2.firmware`, placement `readiness.gateway.firmware`). Ledger row `readiness.gap_ids`. Portions may carry
  `gap_ids` (none yet). Readiness is not enrolled; G-02 enrolls `sites`, `foundation`, `readiness`, `sld`.
- `frontend/docs/architecture/mock_gaps.cjs` `validateMockGaps(registry, {contracts, screenIds, screenLedger,
  requirePresent})` returns typed errors (gap_shape/id/duplicate/reference/enum/combination/requires/cycle/placement/
  join/ledger/enrollment). Registry checker runs it with `requirePresent: true`; `nextWork` with `false`, refusing on
  errors (type `mock_gaps`) and adding an informational `gap_catalogue` summary; gaps never touch candidates/scores.
- UI: `frontend/src/ui/gapCatalogue.ts` (`UI_GAP_CATALOGUE` typed mirror) and `frontend/src/ui/MissingClaim.tsx`
  (`data-gap-id`/`data-gap-placement`/`data-gap-status`; unknown pair is a TS error and a runtime throw).
  `ReadinessOverview.tsx` splits `GATEWAY_FIRMWARE_NOT_AVAILABLE_YET` out of `GATEWAY_NOT_AVAILABLE_YET` and renders it
  through `MissingClaim` unconditionally in `GatewayStatusPanel`.
- Guard: `tools/checks/missing-claim-scan.mjs` (TS AST) checks mirror == registry, literal catalogued MissingClaim
  pairs, every placement used, and untagged copy (`not available yet`/`not yet available`/`no reviewed source`) equals
  `tools/checks/missing-claim-baseline.json` exactly (dated 2026-10-13, 16 entries, shrink-only vs merge-base main
  baseline, `SEED_CEILING = 16`). check-all guards: "Mock-gap catalogue fixtures", "Missing-claim orphan scan",
  "Missing-claim scan fixtures".
- Open: baseline holds 16 legacy untagged strings for G-02..G-05; non-core ranking and per-screen completion remain
  W1-exit owner decisions; Q1 phrase set excludes `not recorded` (commissioning copy is for G-02).

## S4-03 - Finding Evidence and History (in_review)

- Reads (phase 1): `GET /api/sites/{code}/findings/{id}/evidence?revision_id=&offset=&limit=` and
  `/history?revision_id=&after_revision_no=&limit=` (`finding_api.py:142-209`, `finding_read.py` `evidence()`/`history()`,
  `postgres_finding_store.py` `revision_evidence`/`revision_times`). Same scope/gate/refusals as the S4-01 root;
  unpinned read is 409 while the Performance cutover is closed; broken lineage is 200 `lineage.status=BROKEN` with
  named link codes and product-safe words (`BROKEN_WORDS`, parity-tested against frontend `LINK_WORDS`).
- Evidence membership is `finding_revision_evidence` (cited set), counted separately from the run input set;
  `provenance.cited_evidence_by_source` and `cited_evidence_by_role` are whole-set aggregates (phase 3, N1).
- History rows carry `cited_evidence.accepted_rows` (row existence only, never a lineage verdict) and five time kinds;
  no `knowledge_at` replay anywhere.
- UI: child views of the canonical Finding root, `FINDING_CHILD_VIEWS = ["evidence","history"]`
  (`operatorSiteRoutes.ts`), rendered by `SiteFindingFrame` (`SiteAnalyticsFrames.tsx`); `SiteFindingEvidence.tsx`
  (50-record pages, `offset`/`record` local to Evidence) and `SiteFindingHistory.tsx` (loads every page, 100 per
  request, checks loaded == total, selected/latest marked separately, late-acceptance note from stored times).
  `revision_id` is the only context carried between Finding, Evidence and History (Architect Q3).
- Legacy `/findings/{site}/{assessment}/evidence` lists overlapping same-day Findings as a day-level aid, never a
  redirect (Architect Q1).
- Retired: `UNAVAILABLE.evidence_tab/history_tab`, S4-01 history placeholder (baseline 16 -> 15).
- Tools: `tools/s4_finding_walkthrough.py --db/--work` (protected names refused; `prepare` refuses a foreign
  non-empty folder; `drop` removes only a marked folder), `tools/s4-finding-evidence.mjs` suites
  all/finding/evidence/history/closed/broken (110/110 + closed 8/8 at 1440/390 on phase 3).
- Open: Architect Q4-Q6 (`.agent/S4-03-questions-2.md`, incl. M4 shape); registry "knowledge cutoff" rewording and
  node/portion/ledger promotion proposed in the packet, not applied; legacy tab not browser-captured (no readable
  assessment on KOBO-001); Coverage/Use stay catalogued gaps; ActionEvent/recommendation/Alternatives for G-04;
  `ASSESSMENT_CITATION` assumption (phase-1 C1) carried.

## G-02 - V-01a mock-gap pilot (in_review)

Task `tasks/G-02-v01a-gap-pilot.md`, branch `task/G-02-v01a-gap-pilot`, diff base `42bd74d` (main `5625447`).
Packet `.agent/G-02-review-packet.md`, handoff `.agent/G-02-handoff.md`, questions `.agent/G-02-questions-1.md`
(Q1-Q6, fail-closed defaults shipped), owner guide `.agent/G-02-owner-walkthrough.md`. No backend change.

- Registry `mock_gaps.gap_enrolled_screens = [sites, foundation, readiness, sld]`; 20 new gaps (23 total). Every
  non-core open portion of the four carries `gap_ids` (`sites:2#a`, `foundation:2#b`, `readiness:2#a/#b`, `3#a/#b`,
  `4#a/#b`); ledger rows list their gaps. Core paths, `core`, `state`, `technical_requires`, `panel_status` unchanged.
- Placed (17 gaps, 25 MissingClaim uses incl. firmware and S4-03's two): Sites operating view (cell + note), attention
  counts, setup progress; Foundation productive use, financial assumptions, control change record, constraint evidence;
  Readiness commissioning (5 placements), gateway uptime / completeness / signal strength (Architect C5 split, one
  element each) + firmware, per-source contact (3 placements); SLD protection/metering and reporting status (2).
  Unplaced with reasons: obligation policy, confidence effect, evidence capability, and three portion-review gaps.
- Visible copy unchanged except the gateway split; bundled Sites/SLD notes are now one element per claim.
- Scan: phrase set + `not tracked yet`, `commissioning confirmation not recorded` (C7); the result line names the
  merge-base comparison or `SKIPPED (<reason>)` (C1). Baseline 15 -> 12 entries (G-03/G-04 remain).
- Tests: `siteFoundationRevision.test.tsx` "G-02: V-01a pilot missing-state placements" (branch/date/selection/reload,
  exact per-element text) and the G-01 block (C6 loading); `sitesIndex.test.tsx`; `test_mock_gaps.cjs`;
  `test_missing_claim_scan.mjs` (17). Evidence tool `tools/g02-gap-evidence.mjs`.
- Open: SLD per-node SVG slots/captions restate the reporting-status fact untagged (Q1); other euphemisms are tagged
  but not scan cues (Q2); `tools/v01a-foundation-evidence.mjs` and `tools/g01-firmware-evidence.mjs` assert the
  pre-split gateway copy (historical).

## S4-02a - Site price publication and exact assumption history (in_review)

Branch `task/S4-02a-site-assumptions`; phase 1 `28668d9`..`5159b96`, phase 2 `408e9e6`..HEAD. Packet `.agent/S4-02a-review-packet.md`.

- Store: migration `0010_financial_assumptions` (head). `financial_assumption_revision` (immutable, append-only) and `financial_assumption_assignment` (valid x recorded, GiST exclusion, set-once `recorded_to` that must be later than the series' latest `recorded_from`, containment trigger). Sixth product DB writer `financials/adapters/postgres_assumption_store.py` (guard rule 8).
- Publication: SYSTEM only, `python -m assetops_backend.publish_assumption publish|fixture` (no actor flag). Retry digest = canonical publication step; fixture file bytes/version and authorization prose are stored in provenance but not digested (`PROVENANCE_NOT_DIGESTED`). Fixture `backend/conversions/demo-diesel-price-publications.json`: v1 INITIAL 1.25 from 2026-01-01, v2 SUCCESSION 1.32 from 2030-01-01, v3 CORRECTION 1.19 over June 2026. (S4-02b phase 1 added v4 CORRECTION 1.28 over October 2026; `publish_assumption fixture` without `--step` now also publishes v4, the S4-02a walkthrough pins v1-v3 - review L7.)
- Reads: `financial_read_api.py` `GET /api/sites/{site}/financial-assumptions?key=&valid_at=&recorded_at=&after_revision_no=&limit=` (PRICED/NO_PRICE/CONFLICT selection, timeline at cutoff, paged revisions) and `/{revision_id}` (exact, Site-scoped, 404 never latest); Finding read scope semantics, 503 `ASSUMPTION_STORE_UNAVAILABLE`. Write route `financial_api.py` keeps `no_verified_principal` (no success path).
- Finding bridge: `GET /api/sites/{site}/findings/{id}/financials?revision_id=` in `finding_api.py`; `consequence_state` returns `QUANTITY_UNAVAILABLE` (always, until `fuel-cost-1`) or `UNPRICED`; a priced amount raises.
- UI: Financials tab live; `/sites/{site}/financials` (bridge with `finding_id`+`revision_id`, pinned into the URL on first load; price in use) and `/financials/assumptions?revision_id=&recorded_at=` (`sites/SiteFinancials.tsx`, `sites/financialsClient.ts`, frame `SiteFinancialsFrame` in `shell/SiteAnalyticsFrames.tsx`). Finding frame links "What this finding means in money"; Foundation's open `G-foundation-financial-assumptions` line has a sibling link to Assumptions.
- Gap: `G-assumptions-human-edit` (`build`, placement `assumptions.price.human-edit`) in `ui/gapCatalogue.ts` and registry `mock_gaps`.
- Omitted for G-05: Scenarios subtab, Impact preview, maintenance line/accrual, metric cards, Trade-offs, cash flow, FX, extrapolation.
- Walkthrough/evidence: `tools/s402a_assumptions_walkthrough.py` (private `assetops_s402a*` DBs), `tools/s402a-assumptions-evidence.mjs` (69/69 at 1440/390).
- Open: L2 (SUCCESSION exactly at an open assignment's start is refused) for an Architect batch; C3 (S4-02b needs a Finding-window correction step); registry closeout for `I-S4-02a` and the Foundation gap is the coordinator's; `tools/layout-evidence.mjs` has pre-existing fixture-precondition failures on the Finding-case store.

## S4-02b phase 1 - `fuel-cost-1` and the consequence store (active, review pending)

Branch `task/S4-02b-fuel-consequence`, `7cbdef7`..HEAD. Handoff `.agent/S4-02b-phase-1-handoff.md`; questions `.agent/S4-02b-questions-1.md` (Q1-Q10).

- Pure `financials/fuel_cost.py`: immutable conditional `PARAMETER_VERSION` (1.10, digest pinned in fixture), `quantify` (Architect C4 fail-closed containment over stored observed `CANDIDATE_AVOIDABLE` segments, cited-run input membership, as-accepted SFC/binding valid over each interval; exact Fraction, upper stored at 50 digits ceiling plus exact fraction), `select_window_price` (whole-window only, typed UNPRICED reasons), `consequence` (exact amount, basis digest incl. considered price assignments). Fixture `conversions/fuel-cost-1-cases-v1.json` (P1-P4, U1-U17).
- Migration `0011_financial_consequences` (head): append-only `financial_consequence_revision` (number/amount CHECKs, window = FindingRevision episode, chain +1 trigger, unique revision_no and basis), assessment/assumption/power-interval links, trigger-only `financial_consequence_work` (on assumption publication and FindingRevision insert) and append-only `financial_consequence_work_attempt`.
- Seventh product DB writer `financials/adapters/postgres_consequence_store.py` (`load_input`, idempotent `append`, `pending_work`, `record_attempt`, `rows`); guard rule 8 confines it and forbids any module writing work rows.
- Carry C3: price fixture v4 CORRECTION 1.28 USD over October 2026; S4-02a tests and walkthrough pinned to v1-v3.
- Open: no read/recompute worker (2a) or UI (2b); ordinary Findings (review M2 correction): 8 `POWER_MISSING`, 2 `FINDING_NOT_SUPPORTED`, 1 F01-gateway `POWER_COVERAGE_GAP` (5-minute means every 15 minutes, one third coverage), so none qualify - only the power-mean Postgres case is positive (2.75 L; 3.4375 / 3.52 USD at v1 / v4); `finding_api.consequence_state` still the S4-02a placeholder; display rounding and STALE/PENDING are 2a.

## S4-02b phase 2a - read and recompute (built, review pending)

Branch `task/S4-02b-fuel-consequence`, `5d400d6`..HEAD. Handoff `.agent/S4-02b-phase-2a-handoff.md`; questions `.agent/S4-02b-questions-2.md` (Q1-Q9).

- Phase-1 carries: consequence basis uses window-clipped `(revision_id, from, to)` price boundaries (`PriceSelection.considered`, column `price_considered`), never assignment IDs (M1); work CHECK `<=` (L1); reviewer field final, digest `18595762…` (L2); `INTERVAL_NOT_WHOLE_SECONDS` (L3); 0011 enqueues pre-existing FindingRevisions (L4); L5 tests; L6 price value/currency trigger and deferred `financial_consequence_links_complete`. 0011 edited in place (unmerged).
- Worker `financials/recompute.py` (`derive`, `ConsequenceRecomputeWorker`), CLI `python -m assetops_backend.recompute_consequences run|pending --site`; typed FAILED attempts stay pending and retry; replay keeps IDs across restart and append-then-crash.
- Read `financials/consequence_read.py`: `CURRENT/STALE/PENDING/HISTORICAL` by comparing the head basis with a fresh derivation; outward display rounding to ISO minor units (`MINOR_UNIT_UNKNOWN` otherwise). Route `GET /api/sites/{site}/findings/{id}/financial-consequences` in `finding_api.py` (exact/pinned/paged, lineage links, 404 never falls back, 503 `CONSEQUENCE_STORE_UNAVAILABLE`). `/financials` bridge now `bridge_consequence` (amount only for a CURRENT PRICED head); `consequence_state` removed.
- Owner demo (`.agent/owner-S4-02b-money-demo-2026-10-14.md`): spec `conversions/s4-power-demo-cases-v1.json` (P01-power 2026-10-23, labelled AUTHORED DEMONSTRATION; 12.65 L, 15.8125 USD at v1, 16.192 at v4); producer `tools/s402b_power_cases.py` (S4 cases + P01-power into its own `assetops_s402b*` DB). `s4-finding-cases-v1` unchanged.
- Open: no UI (2b); S4-02a frontend mis-words the new bridge states until 2b (`SiteFinancials.tsx:481`); evidence acceptance enqueues no work (Q2); worker is a one-shot CLI (Q6).

## S4-02b phase 2b - Financials UI, walkthrough and evidence (in_review)

Branch `task/S4-02b-fuel-consequence`, `dbaba10`..HEAD. Packet `.agent/S4-02b-review-packet.md` (whole slice); handoff `.agent/S4-02b-phase-2b-handoff.md`; questions `.agent/S4-02b-questions-3.md` (Q10-Q15); owner steps `.agent/S4-02b-owner-walkthrough.md`.

- Review carries: read takes `source_open` (S3 gate); closed gate gives currentness `AUDIT_ONLY` (`SOURCE_CLOSED`), never presented as current, bridge state `AUDIT_ONLY` with no amount (M1). Tests: HISTORICAL over a superseded FindingRevision (M2, test-scoped model upgrade), 401/403 and failing-store 503 on `/financial-consequences` (L1), assessment-completeness trigger (L2), latest-revision filter and `skip_if_succeeded` (L3), pending-work scope (L4). Bridge STALE says "queued" only when pending work exists, and carries `recalculation_queued`, `currentness_reasons`.
- `backend/assetops_backend/demonstration_label.py`: labels the P01-power Finding from the spec's declared Site/day; bridge and consequence read carry `demonstration` (Q11).
- Frontend: `sites/FindingConsequence.tsx` (`FindingBridge`: headline range only for CURRENT PRICED with display, "From finding to money" table, "How this is worked out" lineage disclosure, pinned earlier version panel, "Fuel cost versions" history); `financialsClient.ts` types + `getFindingConsequences`; `SiteFinancials.tsx` Overview reads bridge + consequences (`consequence_revision_id` in the address), S4-02a `:481` wording replaced; Assumptions "Show later versions" appends (S4-02a L5). `settled.ts` knows "Loading the fuel cost versions".
- Tools: `tools/s402b_fuel_cost_walkthrough.py` (one code tree per DB so each keeps its own source gate; prepare/links/serve/publish-v4/recompute/close-gate/open-gate/drop; `assetops_s402b*` non-test names only); `tools/s402b-fuel-cost-evidence.mjs` (90 claims at 1440/390, mutates its own evidence DBs).
- Open: Site-level consequence list on Assumptions (Q12); authorship label at ingestion (Q11); Architect Q2 (evidence acceptance enqueues no work); G-05 itemization in the packet; owner checkpoint after fresh review.

## S4-02c phase 1 - transactional acceptance work (reviewed: ACCEPT with carries)

Branch `task/S4-02c-evidence-consequence-work`, `5af9f214`..HEAD. Handoff `.agent/S4-02c-phase-1-handoff.md`; no open questions file.

- Migration `0012_evidence_consequence_work` (head): `financial_consequence_work.accepted_evidence_id` with scoped FK `(tenant_id, site_id, accepted_evidence_id)` -> `accepted_evidence`; cause CHECK adds `EVIDENCE_ACCEPTED`; three-arm `financial_consequence_work_cause_shape` (evidence arm requires accepted, Finding and revision locators and a non-empty `[affected_from, affected_to)`); `UNIQUE (finding_revision_id)` replaced by partial unique index `..._finding_revision_once WHERE cause = 'FINDING_REVISION_APPENDED'`; new partial `..._evidence_once (accepted_evidence_id, finding_revision_id)`; index `..._work_finding (tenant_id, site_id, finding_id)`; attempt index `(work_id, attempt_no DESC)`; `financial_consequence_work_attempt.no_op_reason` (enum CHECK, only on SUCCEEDED with `[]` IDs).
- Triggers: `financial_consequence_dirty_on_evidence` (AFTER INSERT on `ingestion_disposition` WHEN ACCEPTED; stored role `generator_power`, non-empty interval; one row per same tenant/Site Finding's highest-`revision_no` revision with a non-empty episode strictly overlapping). 0011 `financial_consequence_dirty_on_finding_revision` replaced with `ON CONFLICT ... WHERE`. Both take `pg_advisory_xact_lock(hashtextextended('financial_consequence_enqueue:' || NEW.site_id::text, 0))` (evidence: after the role check).
- Downgrade refuses while any `EVIDENCE_ACCEPTED` row or `no_op_reason` exists; otherwise restores the 0011 body, two-arm CHECK and UNIQUE. No backfill of pre-0012 acceptances.
- `PostgresConsequenceStore.chain()` pending matches unsucceeded `EVIDENCE_ACCEPTED` by `finding_id` (selects `accepted_evidence_id`); read `pending_work` items carry `finding_revision_id`, `accepted_evidence_id`; STALE with no pending work adds typed `NO_WORK_RECORDED` (`consequence_read.NO_WORK_RECORDED`); bridge keeps `REASONS["STALE"]`, no new copy.
- `recompute.py`: explicit cause dispatch; `EVIDENCE_ACCEPTED`/unknown -> FAILED attempt `CAUSE_NOT_SUPPORTED` (stays pending), never the assumption-range path.
- Guard rule 8 comment and message name 0011/0012 triggers; logic unchanged.
- Tests: `backend/tests/test_s4_evidence_consequence_work_postgres.py` (12), `backend/tests/test_s4_consequence_cause_dispatch.py` (2).
- Open (phase 2): scoped drain of `EVIDENCE_ACCEPTED` (recheck, typed no-op, N1 predicate), runner/Site claim/retry schedule; phase 3 walkthrough. Until phase 2, the CLI `run` records `CAUSE_NOT_SUPPORTED` attempts for evidence work and exits 1.

## S4-02c phase 2 - scoped drain and run plan (reviewed: ACCEPT with carries)

Branch `task/S4-02c-evidence-consequence-work`, `0a79be14`..HEAD. Handoff `.agent/S4-02c-phase-2-handoff.md`; no questions file.

- `recompute.py`: `EVIDENCE_ACCEPTED` dispatched via `PostgresConsequenceStore.evidence_target` (tenant/Site-scoped snapshot of accepted reading, queued revision, same tenant/Site/Finding max `revision_no`). Unreadable locator -> FAILED `EVIDENCE_LOCATOR_NOT_IN_SITE`; no ACCEPTED disposition -> FAILED `EVIDENCE_NOT_ACCEPTED`; other-Site work dict -> `WORK_SCOPE_MISMATCH` (unrecorded). `evidence_no_op` gives `FINDING_REVISION_SUPERSEDED` / `EVIDENCE_ROLE_NOT_RELEVANT` / `EVIDENCE_ASSET_NOT_RELEVANT` / `EVIDENCE_OUTSIDE_CANDIDATE_TIME` (strict overlap with merged positive-width claim spans), never quality; otherwise the same revision is derived from its own inputs.
- No-ops: `record_attempt(..., no_op_reason=)` -> SUCCEEDED, `[]` IDs, typed reason.
- Runner: `ConsequenceRecomputeWorker.run(tenant, site, limit, now=None)` with injectable `clock`; `claim_site` session lock `financial_consequence_runner:<site>` on a dedicated connection, unlocked in `finally`; due = never attempted or `now >= retry_due_at(last finished_at, last attempt_no)` (1/2/4/8/16 then 16 min, no cap); ordered by eligible-since instant (no starvation); `RunReport.counts()`. `run_pending` unchanged (unscheduled helper). `pending_work` returns last-attempt fields.
- CLI `recompute_consequences run --tenant --site [--limit 100]`: tenant required, non-dev tenant exit 2, summary JSON line, skipped Site exit 0. Runbook in `backend/README-db.md`.
- Tests: `test_s4_evidence_drain_postgres.py` (10), `test_s4_evidence_drain.py` (12); phase 1 file gains L3 no-op downgrade refusal and the L1-scoped race probe.
- Open (phase 3): two-leg late-power walkthrough (N2 price, N5 precondition, C5 IDs). R1 (S3/S4 commands unscheduled) and I1 (concurrent overlapping chunks) remain named risks.

## S4-02c phase 3 - late-power walkthrough and slice wrap-up (built, review pending)

Branch `task/S4-02c-evidence-consequence-work`, `6d4a1995`..HEAD. Packet `.agent/S4-02c-review-packet.md`, handoff `.agent/S4-02c-phase-3-handoff.md`, evidence `.agent/S4-02c-walkthrough-evidence.md`; no questions file.

- Phase-2 carries: `tools/s402b_fuel_cost_walkthrough.py` `recompute` now runs `recompute_consequences run --tenant demo --site KOBO-001` in bounded runs until backlog 0 and counts only `work_id` lines (M1, proved on private DBs); `tools/s402b-fuel-cost-evidence.mjs` claims the recompute exit status; runbook (`backend/README-db.md`) names repeated `skipped` as the hung-runner alarm (no timeout) and the uncapped permanent-failure retry volume; tests assert backlog after a failed run and the per-Site runner key.
- Fixture `backend/conversions/s4-power-late-demo-cases-v1.json` (`P02-power-late`, 2026-10-24): P01-power's shape with the 20 kW mean `[07:00, 07:05)` withheld and delivered later; `power_rules.sequence_rule = SOURCE_ORDER` (the late mean keeps its source sequence, the first delivery leaves a gap). Existing S4/S4-02b specs unchanged.
- Tool `tools/s402c_late_power_walkthrough.py run|drop` (DB `assetops_s402c3walk*`, ports 8918/8919): price v1 first (N2); N5 asserted (stops otherwise); Leg A STALE/TECHNICAL_INPUT_CHANGED + STALE_QUEUED with the EVIDENCE_ACCEPTED work ID, runner drain -> same revision consequence 2 CURRENT POWER_NOT_IN_ASSESSMENT_INPUTS, not S5-eligible; Leg B process-jobs + match-findings -> r2 SUPPORT_CHANGED citing the late ID, its FRA work -> CURRENT PRICED 12.65 L / 15.8125 USD, S5-eligible; replay selects 0; no duplicate basis. Reads use `ConsequenceReadService.read` with `source_open=True`.
- Finding: appending a late mean after the epoch's last sequence makes S3 dispatch-3.1 report `SEQUENCE_ORDER_INVERTED` and shortens the revised Finding (run 1, recorded).
- Open: R1 (S3/S4 commands unscheduled), I1 (permanent-failure attempt growth), I2 (hung runner visible only as `skipped`), I3 clock skew, I4 concurrent overlapping chunks unmeasured; pre-0012 stale heads `NO_WORK_RECORDED` without backfill; late-delivery sequence numbering on real gateways unproved.

## S4-02d phase 1 - bounded orchestration and schedule storage (built, review pending)

Branch `task/S4-02d-analytic-finding-worker-schedule`, `7851b4da`..HEAD. Handoff `.agent/S4-02d-phase-1-handoff.md`; questions `.agent/S4-02d-questions-1.md` (conservative choices built).

- Migration `0013_schedule_state` (head): `schedule_tick_head`, `schedule_site_head`, `schedule_cursor`, `schedule_enrolment`; one row per environment/Site, FK to `site(tenant_id, id)`, no trigger.
- Eighth writer `scheduling/adapters/postgres_schedule_store.py` (D-2026-10-14-s402d-schedule-storage-and-install-gate): expiring DB-time claims for tick and Site, heartbeat only on a completed tick, back-off on failure, fair cursor, enrolment, `site_inventory` read. Port `scheduling/ports.py`; composition `scheduling/composition.py` (adapter-isolation domain `scheduling`).
- Guard rule 8: schedule writer allowlist with named UPDATE columns per table, one-line UPDATE rule, no DELETE/TRUNCATE/DDL/upsert, reverse ownership; probes `.agent/S4-02d-phase-1-probes.py guard` all caught.
- `scheduling/tick.py` `ScheduleTick.tick()`: discover child (`reconcile_all()` timed + inventory + live jobs + pending work) -> active predicate (imported, not DECOMMISSIONED/ARCHIVED, any `accepted_evidence` row or enrolment; PLANNED qualifies; Sites with live work kept as `EXCLUDED_WITH_WORK`) -> `max_sites` after the cursor -> per Site claim, `s3` -> `s4` (skipped unless matcher version/fence changed) -> `consequence` (DB `now`), each a killable child with `PGOPTIONS` statement/lock timeouts. CLI `python -m assetops_backend.scheduling.run tick|enrol|heads`. No timer installed.
- S3: `lease_job` Site-scoped option, `run_site`, reads `live_jobs`/`job`. S4: `MatchOutcome.fence`. Consequence: `pending_work_sites()`. `assess_dispatch requeue --job-id` re-enqueues a live FAILED job's window.
- Tests `backend/tests/test_s4_schedule_tick_postgres.py` (7).
- Open (phase 2): health report and alarms, S5 seam, timer/runbook behind F1, I3 skew proof; I4 race proof at review. S3 cutoff and matcher `now` still app clock; one-off CLIs bypass the schedule Site claim.

## S4-02d phase 2 - health, install gate and S5 currentness seam (built, review pending)

Branch `task/S4-02d-analytic-finding-worker-schedule`, `8cf2d147`..HEAD. Handoff `.agent/S4-02d-phase-2-handoff.md`; probes `.agent/S4-02d-phase-2-probes.py`.

- Phase-1 review fixes: F1 rule-8 schedule-writer rules case-insensitive with strict one-line SET-list parse (phase-1 guard probes 20/20 incl. seven bypass lines); F2 Site back-off test; F3 `CLAIM_LOST` stops a Site on a lost claim; `requeue` usage error.
- `scheduling/health.py` read-only report (`run health`): environment and per-Site `STOPPED|FAILED|RETRY_DUE|BACKLOG|RUNNING|IDLE`, typed alarms (heartbeat/claim/skip/failure/fence-moved streaks, `S3_JOB_FAILED` with requeue, consequence attempt growth, `STALE_NO_WORK` IDs, S4 backlog outside the active set), all in DB time.
- `scheduling/upstream.py` S5 seam (`UpstreamCurrentnessRead` port, `run upstream`): per-day S3 read status/limits/basis/watermark (selection seq), bracketed live jobs, `match_state`, latest Finding revisions with consequence reads, pending work, schedule state; eligibility CURRENT only with a healthy heartbeat AND Site head (Q1); before/after `match_state` comparison reports `SELECTION_MOVED_DURING_READ`.
- I3: DB clock for discover reconcile, S3 worker, matcher `now` and drain; one-off `recompute_consequences run` defaults to DB time, `--now` override, `now_source` reported. `SKIPPED_UNCHANGED_FENCE` clears `fence_moved_streak`.
- Gated install: `backend/deploy/schedule/assetops-schedule-tick@.service|.timer`, `tools/schedule-install-gate.py` (demo CLOSED until `I-late-reading-series-and-money-limit` resolved); `backend/README-db.md` runbook retires the per-Site consequence timer, covers `CONSEQUENCE_CLAIMED`, stop-the-tick before manual Leg B. Nothing installed.
- Tests: `test_s4_schedule_health_postgres.py` (10, incl. I3 skew and I4 two-chunk race), `test_s4_schedule_upstream_unit.py` (5), `test_s4_schedule_install_gate.py` (3). Tick cost: ~4-5 s per Site-visit tick on Windows (child start ~1 s x3), 4 Sites 12.6 s.
- Checks: full backend pytest 2115 passed; `tools/check-all.ps1` 9/9; phase-2 probes 21/21, phase-1 guard probes 20/20.
- Open: phase 3 walkthrough; I4 still needs the independent review's own race; one-off S3/S4 CLIs remain app clock and bypass the Site claim (runbook); health `STALE_NO_WORK` scan cost grows with Findings.

## S4-02d phase 3 - tick-only late-power walkthrough and slice wrap-up (built, review pending)

Branch `task/S4-02d-analytic-finding-worker-schedule`, `62581ecd`..HEAD. Handoff `.agent/S4-02d-phase-3-handoff.md`; slice packet `.agent/S4-02d-review-packet.md`.

- Phase-2 review fixes: F-A health alarm `S3_STALE_NO_JOB` (selected UTC day `STALE_PROJECTION` with no live S3 job; Site `FAILED`) and `assess_dispatch requeue --day` (refused unless STALE with no live job); F-C service `TimeoutStartSec=900`; F-D install-gate dedupe; phase-1 probes usage.
- I3 residual (open, evidence owner): scheduled S3 cutoff is DB time, `ingestion_disposition.decided_at` is the ingestion app clock; documented in `backend/README-db.md`; ingestion unchanged.
- `tools/s402d_tick_walkthrough.py` (reuses `s402c_late_power_walkthrough.LateWalk`; DB `assetops_s402d3walk*`, environment `walkthrough`): five schedule ticks only, command-log grep for hand-run Leg B (mutation caught). Evidence `.agent/S4-02d-walkthrough-evidence.md`: 23/23; tick 3 rebuilt S3, appended r2 citing the late ID, r1's EVIDENCE_ACCEPTED attempt typed `FINDING_REVISION_SUPERSEDED` no-op, r2 CURRENT PRICED; seam CURRENT only after the tick; stopped worker blocks the seam.
- I4: proved by the independent phase-2 review race (0 false CURRENT).
- Open: F-B statement-level guard; evidence-owner `decided_at` packet; health scan cost; S5-01 seam carries; demo-host tick cost; no owner-visible install before F1.

## OPS-01 - backend test turnaround (phases 1-2 built, review pending)

Branch `task/OPS-01-backend-test-speed` from main `52189ec7`. Handoffs `.agent/OPS-01-phase-1-handoff.md`, `.agent/OPS-01-phase-2-handoff.md`; packet `.agent/OPS-01-review-packet.md`. Guide: `backend/TESTING.md`.

- `backend/tests/pg_harness.py`: run-owned databases `<stem>_pt<run>_<tag>_test`, one migrated template per run (`ALLOW_CONNECTIONS false`), per-module `DROP ... WITH (FORCE)` + `CREATE ... TEMPLATE`, `assert_at_head`, lease-guarded orphan sweep, `empty_tables` (DELETE over the TRUNCATE CASCADE closure under `session_replication_role = replica`), `dispose`.
- xdist (`pytest-xdist==3.8.0`, dev extra): controller makes the run id (`conftest.pytest_configure_node` -> `workerinput`), routes nothing; workers `route(tag=gwN, run=...)` before collection and return early from basetemp handling; first worker builds the shared template under `pg_advisory_lock`; workers drop only their own DB; controller `cleanup_run` drops the rest (covers crashed workers). Workers move `conftest.START_FIRST` modules to the front.
- Normal full command: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder` (7.7 / 8.4 min, peak 35 / 32 sessions; serial 30.8 min; pre-OPS-01 41-80 min). `-n 3`: one run, 6.5 min, peak 41.
- Parametrize IDs must be deterministic (xdist refuses differing collections); `test_s3_performance_cutover.py` now uses fixed UUIDs.
- Role guidance: reviewers reuse implementer same-revision full evidence; full suite once per slice; keep-awake + 2x cap (`.claude/agents/assetops-{reviewer,implementer}.md`, `.ai/ROLE_CONFIG.md`).
- Escape hatches: `ASSETOPS_TEST_TEMPLATE=0`, `ASSETOPS_TEST_CLEANUP=truncate`; measurement knobs off by default.
- Open: inline stores still GC-disposed (no public `dispose()` on production stores); `gc.collect()` fixtures kept; concurrent full runs unproven (one-at-a-time policy); timing-sensitive S4 cases did not flake in 3 parallel runs but remain disk-stall sensitive; `-n 3` not adopted on one run.

## S4-05a - immutable source binding and exact-revision resolver (built, in_review)

Branch `task/S4-05a-provenance-binding-resolver` from main `fd7afd2c`. Handoffs `.agent/S4-05a-phase-1-handoff.md`, `.agent/S4-05a-phase-2-handoff.md` (resolver field contract for S4-05b); packet `.agent/S4-05a-review-packet.md`. Authority `D-2026-10-15-s405-stored-demo-provenance`, `.agent/architect-S4-05-answers.md`.

- Migration `0017_evidence_publication`: insert-only `evidence_publication` (SYSTEM actor, class CHECK: authored fixture ID+version or run ID+64-hex run digest) and `batch_publication_link` (composite FKs to the exact batch and publication commitment); UPDATE/DELETE triggers; downgrade refuses while publications exist (tested).
- Ledger writer (`postgres_evidence_ledger.py`) is the only provenance writer: `register_publication` and `open_batch` share `pg_advisory_xact_lock` on (tenant, Site, external batch ID); registration refuses after any admission, needs a registered gateway/source and (phase-1 review M1) a `SIMULATED` gateway for every class; `open_batch` binds the exact commitment or refuses 409 `PUBLICATION_MISMATCH`. Unpublished uploads stay accepted and unbound.
- Domain `evidence/publication.py` (authored records, run attestation), `runs/source_publication.py`, server CLI `publish_source.py`; no HTTP route.
- Resolver `evidence/source_provenance.py` (pure, route-safe) + read-only ledger methods `link_rows`, `finding_revision_evidence`, `consequence_inputs`; `composition.build_source_provenance`. FindingRevision cited set; consequence = union of its FindingRevision set and its own power-interval IDs, with `finding_revision_state` and `CONSEQUENCE_POWER_INPUT_CONFLICT`. Several run IDs -> MIXED (N-L2). Missing/foreign-Site/broken precede MIXED. Cross-tenant IDs read as not found (no disclosure).
- Rule 8 (`configuration-persistence.ps1`): ledger INSERT-only provenance; split `UPDATE|DELETE FROM|TRUNCATE <provenance table>` refused in any module (review L1); HTTP modules may not reference designation.
- Not changed: every read DTO and the date/spec source heuristic (S4-05b cuts over).
- Open: N-L1 producer registration in a non-route module (S4-05b); migration re-chain vs LR-01/S6-01a; run identity digest is not re-verified after registration (file-backed run store); lock key is the admission slot, stricter than the packet wording; no TRUNCATE trigger (rule 8 only); S5-01 amendment (N-L3).
## S6-01a - Action store, controlled application and exact read (in_review)

Branch `task/S6-01a-action-store-read` from main `fd7afd2c`. Packet `.agent/S6-01a-review-packet.md`; handoffs `.agent/S6-01a-phase-1-handoff.md`, `.agent/S6-01a-phase-2-handoff.md`. Authority `D-2026-10-15-s601-action-store-and-ui` (`.agent/architect-S6-01-answers.md` Q1-Q5, M1-M3).

- Migration `0016_action_store` (down `0013_schedule_state`): `action` (accepted-recommendation snapshot), `action_basis_assessment`/`_evidence`, `action_event`, `action_policy_change`, `action_policy_change_binding`; all append-only (`ledger_append_only`), same-Site composite FKs, `action_code_seq`. Event expected/current Foundation IDs carry same-Site FKs; the change's APPLIED event must be its own Action's (`action_event_action_unique`).
- `backend/assetops_backend/actions/`: `reserve_trial.py` (pure `reserve-trial-1`), `lifecycle.py` (transition table, reducer, selectors, `SYSTEM_DEMO`), `capability.py` (grants v2: tenant ID + Site ID + command + fixture record Finding IDs), `service.py` (`ActionService`), `composition.py` (`foundation_publish(registry)` maps S1 refusals to Action failure codes), adapter `adapters/postgres_action_store.py` (ninth writer, INSERT only).
- Apply: the Action adapter opens the transaction, locks the Action row `FOR UPDATE`, returns a stored event for the same key (`REPLAY`) or `ALREADY_APPLIED`, then calls the S1 publish on its own connection: `FoundationService.publish_battery_reserve(..., expected_revision_id, expected_value, caller=CallerTransaction(connection, then, recorded_at))` -> `PostgresFoundationStore.publish_configuration(..., connection=, then=)` (Site lock, expected covering revision, no-change, expected reserve; `written_ids(plan)` to `then`). `then` inserts the change, binding rows and APPLIED; one commit. `ApplyFailed` rolls back, then FAILED is appended in its own transaction (existing event returned on key collision). Without `caller`, S1 publish is unchanged.
- Routes (`action_api.py`, wired `main.py` with `registry=`): recommendation, accept, apply, observations, Action and events reads (`event_id` | `recorded_at`, both = 422), `GET /api/sites/{code}/foundation/changes/{change_id}`. Refusal order: access, Site 404, Finding/Action 404, fixture-record capability 403, body 422, revision/expected-Foundation 404, domain.
- Action read adds `change` (only when APPLIED is inside the selected prefix), `application_basis` (read-time covering Foundation), `demonstration` (`demonstration_case` on the origin episode); recommendation adds `demonstration` and a `money_consequence` link to the exact FindingRevision's S4 consequence (no number).
- `D-action-records` v1: `backend/tests/s6_action_records.py` (loader, `fixture_grants`, `normalise`), committed contract `backend/tests/fixtures/s6_action_api_contract.json` (manifest IDs `recommendation:1#a`, `action-overview:1#a`, `action-execution:1#a`, `action-history:1#a`, `changes:1#a`), test `test_s6_action_records_postgres.py` (rebuild + normalised equality; `ASSETOPS_WRITE_S6_CONTRACT=1` regenerates, `ASSETOPS_S6_WALKTHROUGH_OUT=<file>` dumps rows).
- Rule 8 (`tools/checks/configuration-persistence.ps1`): ninth writer registered; INSERT-only into the six Action tables; Action-table writes refused from every other module.
- Reopen (`D-2026-10-15-s601-reopen`): the recommendation read carries `prior_actions.items` (every Action on the canonical Finding with its own origin revision, application/outcome state, link) and `prior_action_block`; an unresolved earlier `reserve-trial-1` Action (PENDING or APPLIED; nothing releases it until S6-02) sets `state=PRIOR_ACTION_UNRESOLVED`, `proposal=null`, Accept capability false, live result in `live_status`. Accept refuses 409 `PRIOR_ACTION_UNRESOLVED`, rechecked in `PostgresActionStore.accept(..., guard=)` under an advisory lock per (Site, Finding, asset, field, rule).
- Open: migration must be re-chained if LR-01 (`0014`/`0015`) merges first (head pins at `test_s1_bindings_postgres.py:118`, `test_s2_evidence_ledger_postgres.py:445`, `test_s4_evidence_consequence_work_postgres.py:516,539`). No runtime grants file is generated for a dev server: the loader builds it per run (`fixture_grants`). `application_basis` is read-time; an apply effective in a recorded future period must name that period's revision. The rule picks the lowest usable SOC per segment (stricter than the ruling). S6-01b UI, S6-02 verification and S6-03 Site ActionIndex not built.

## S6-01b - Action, recommendation and change surfaces (in_review)

Branch `task/S6-01b-action-ui`, stacked on unmerged S6-01a `c341599b`; no backend change. Packet `.agent/S6-01b-review-packet.md`; handoffs `.agent/S6-01b-phase-1-handoff.md`, `.agent/S6-01b-phase-2-handoff.md`; owner steps `.agent/S6-01b-owner-walkthrough.md`.

- Client `frontend/src/sites/actionClient.ts`: recommendation, Action, events and change reads, accept and apply POSTs. Every refusal is a typed `Refusal`. `system_demo_capability` is optional; when it is absent or `allowed:false` the screens are read-only.
- Shared words `sites/actionPresentation.tsx`:
  - `granted()` requires `allowed === true` and the exact command;
  - `TrialLimitation` carries plain copy, because the server's text uses a banned word;
  - `Ref` is the exact-ID element, exempt from the vocabulary scan;
  - `RefusalPanel` and `CommandRefusal`.
- Recommendation `sites/SiteRecommendation.tsx`. It is a Finding child view `recommendation` (`operatorSiteRoutes.ts` `FINDING_CHILD_VIEWS`). Finding "What to do next" links to it at the exact version.
- Reopen round (`D-2026-10-15-s601-reopen`): `SiteRecommendation.tsx` lists `prior_actions.items` ("Actions on this Finding", own origin version, never relabelled). `state=PRIOR_ACTION_UNRESOLVED` (from `state`, not block presence) shows the notice naming/linking the blocking Action, the live recomputation as a separate reason, and a disabled Accept with the stated reason; a 409 `PRIOR_ACTION_UNRESOLVED` on accept is reported likewise. Apply is disabled while the effective-time field is cleared; failure codes in the change page list do not wrap. Open: S6-02 must add the resolved/closed transition that releases the hold.
- Action root `sites/SiteAction.tsx` + `SiteActionFrame` (`shell/SiteAnalyticsFrames.tsx`).
  - Overview, Application (`/execution`) and History. The selector `event_id` | `recorded_at` is carried in every section link.
  - 404 `ACTION_EVENT_NOT_FOUND` reads "Selected event not found" and links the latest record (phase-1 review M1).
  - An untouched `effective_from` default is re-derived at click: next UTC midnight after max(read time, now) (L1).
  - With no `application_basis.current_foundation_revision_id`, Apply is not offered and the reason is stated (L3).
- Foundation change `sites/SiteFoundationChange.tsx` + `SiteFoundationChangeFrame`. It is the deep route `/sites/{site}/foundation/changes/{change_id}` (`SITE_FOUNDATION_CHANGE_ROUTE_PATH`).
  - Content: old/new reserve, unit, asset, effective and recorded times, versions by role and origin, signal assignment set IDs, Action and application-event links, pending outcome, and the Action's FAILED attempts (a second read).
  - Bare `/foundation/changes` is `SiteFoundationChangesFrame`, an unavailable state with a link back.
  - Both are static segments, so they outrank `:foundationView`. `FOUNDATION_SUBTABS` is unchanged.
- Styles: `ui/primitives.css` end, all under `.app-frame--operator`. Pairs go side by side from 1100px. Refs wrap, except inside dense tables, which scroll in their own scroller.
- Tests:
  - `sites/__tests__/siteAction.test.tsx` (30) and `siteFoundationChange.test.tsx` (8, mounted through `App`) load `backend/tests/fixtures/s6_action_api_contract.json`. Derived bodies are listed in the test headers.
  - `siteFinding.test.tsx` adds the no-recommendation-link case.
- Tools:
  - `tools/s601b_action_walkthrough.py` (`prepare|links|serve|drop`). It uses DB `assetops_s601b*` (never `_test`), work folder `var/s601b*`, API 8961 and web 5461. It runs `s6_action_records.build` into the private DB and writes the scoped `ASSETOPS_ACTION_DEMO_GRANTS` document.
  - `tools/s601b-action-evidence.mjs` (CDP 9461): 56 claims plus `comparison.md`.
- Open:
  - The Recommendation for a newer FindingRevision does not mention an Action accepted on an earlier one. This is S6-01a server behaviour, recorded for the owner.
  - The served walkthrough uses the real clock against fixture-clock records.
  - There is no OBSERVED command control.
  - S6-02 owns Plan, Evidence and Verification, the change index and effect verdicts.
## S4-06 - equal-start future price succession (built, review pending)

Branch `task/S4-06-price-succession` from main `7c72c6b3`; packet `.agent/S4-06-review-packet.md`.

- `financials/assumptions.py` `plan_assignments`: a SUCCESSION whose `valid_from` equals the sole open-ended current assignment's start closes it and inserts only the new `[valid_from, inf)` row (Architect S4-02 Q1); no zero-length remainder. Later-start SUCCESSION, INITIAL, CORRECTION, `SUCCESSION_NOT_FUTURE` and `SUCCESSION_OVERLAP_NOT_PERMITTED` (bounded / >1 overlap) unchanged.
- No writer, migration or rule-8 change: `postgres_assumption_store.publish` already applies any plan under the Site/key advisory lock; earlier recorded cutoffs keep the scheduled assignment through the existing `snapshot` history read.
- Proofs: `test_s4_assumptions_postgres.py` `TestEqualStartSuccession` (cutoff history, retry, key reuse, stale prior, 2-publisher race, bounded/multiple refusal, CORRECTION tail on an older revision, unchanged earlier-price window selection); planner unit tests in `test_s4_assumption_publication.py`.
- Open: registry `I-price-equal-start-succession` stays `open` until merge.

## OPS-02 - statement-level rule 8 writer guard (done, pending merge)

Branch `task/OPS-02-writer-guard-ast` from main `5bfff665`; packet `.agent/OPS-02-review-packet.md`; closes S4-02d phase-2 review F-B and OPS-01 L1.

- `tools/checks/sql_statements.py`: table-agnostic AST extractor. Renders whole string expressions (implicit concatenation, triple quotes, escapes; `+`, f-string, `%`, `.format`, `"".join` with dynamic parts as `{?}`), strips SQL comments, collapses whitespace, splits on `;` and at each write head (INSERT INTO/UPDATE/DELETE/TRUNCATE/MERGE/COPY/CREATE/ALTER/DROP/GRANT; `DO|THEN|FOR|KEY UPDATE` stay in their clause), and synthesises SQLAlchemy Core `insert/update/delete` (aliased imports, `sa.` attributes, `table("x").delete()`) into SQL. Bare string statements (docstrings) are skipped.
- `configuration-persistence.ps1` rule 8 applies the unchanged per-writer policy tables to clauses (`$line` = clause, `$lineNumber` = expression start line); the driver-import check stays per line. New global refusals: MERGE/COPY, a DML clause whose target is not a literal identifier, a dangling write head (`sql +=` assembly). Schedule UPDATE allows a table alias; its "one line" rule became "one statement". Writer non-vacuity is reported only when the extractor ran (its own failure is reported instead).
- Interpreter: `ASSETOPS_GUARD_PYTHON` (set by `check-all.ps1` from `-Python`), else `.venv/Scripts/python.exe` or `.venv/bin/python`; a missing or failing extractor is a rule-8 failure, never a skip.
- Proof corpus `tools/writer_guard_probes.py` (`--seam` = rule-8 module only): 11 F-B forms, a two-line UPDATE per writer, reverse ownership per table family, dynamic/Core/fragment/CTE/upsert/COPY forms, plus one controls run.
- `backend/tests/conftest.py` `refuse_template_opt_out_under_xdist`: `ASSETOPS_TEST_TEMPLATE=0` under xdist (controller or worker) is a `pytest.UsageError` before routing; serial and `-n 0` unchanged.
- Adding a writer table (LR-01 `source_clock_attestation`, S6-01a Action tables, S4-05a provenance tables): extend the rule-8 policy arrays only; the extractor needs no change.
- Merge with main `0d3114a3` (2026-10-16): rule 8 statements carry the ninth writer (Action store, insert-only), LR-01 `source_clock_attestation` (assessment store, insert-only) and S4-05a provenance (ledger, insert-only; three DO NOTHING arbiters). S4-05a's provenance verb refusal and S6-01a's Action every-line refusal run on source lines (driver loop) and on clauses; new: an insert-only table (attestation, Action, provenance) is never upserted (`DO UPDATE`).
- Open: SQL read from files, or assembled across statements other than a dangling head, is not resolved; `.agent/S4-02d-phase-1-probes.py` "split update" is now an allowed form (see packet).
## S4-07 - evidence decided_at on DB time (built, review pending)

Branch `task/S4-07-evidence-decided-at` from main `5bfff665`; packet `.agent/S4-07-review-packet.md`.

- `PostgresEvidenceLedger.decide_chunk` takes one DB `clock_timestamp()` per chunk after the batch row lock (`_decision_instant`), inside the write transaction; it stamps every newly decided ordinal's `decided_at` and a newly inserted `recompute_job`'s `available_at`/`created_at`. A widened PENDING job keeps `created_at` and has `available_at` lifted to `GREATEST(available_at, decision)` (Known Deviation 1; closes the cutoff-sampled-before-commit race, proved failing without it).
- `EvidenceLedger.decide_chunk(..., completed_at=)` replaces `decided_at=`: `BatchIngestionService` passes its app clock only for the receipt `completed_at`; `received_at` unchanged.
- `test_decision_clock_override` (constructor kwarg/attribute) is test-only; `main.py`/`evidence/composition.py` never set it. Deterministic fixtures (S2 ledger/site evidence, S3 dispatch, S4 CaseRunner, S4 consequence work) use it.
- Proofs: `tests/test_s4_evidence_decided_at_postgres.py` (production path, fast/slow app clocks: ingestion-first, worker-first with L-b lock wait, cutoff-sampled race, uncommitted-job tick; crash/replay across two windows, duplicate-only chunk, another Site). F-A test re-driven as override-path, skew 120 s (R-2).
- Open: manual app-clock `process-jobs` beside the tick (README-db); configuration `recorded_at` vs `reconcile`; `clock_timestamp()` vs `now()` (an instant predating a batch-lock wait) is reasoned, not mutation-proved (no batch-lock contention test).
## LR-01 - late-reading series and money limit (phases 1-2 built, slice review pending)

Branch `task/LR-01-late-reading-series-and-money-limit`; handoffs `.agent/LR-01-phase-1-handoff.md`, `.agent/LR-01-phase-2-handoff.md`; packet `.agent/LR-01-review-packet.md`; decision `D-2026-10-15-lr01-source-time-cohort`.

- Clock attestation: append-only `source_clock_attestation` (migration 0014), SYSTEM-only CLI `assetops_backend.record_clock_attestation`, `SIMULATED` proof class only; attestation change requeues old+new validity (`postgres_assessment_store.record_clock_attestation`).
- cohort-4 / `dispatch-3.2`: source-time order only under one covering attestation (`analytics/cohort.py`); a reading's clock reason depends only on attestations touching it (phase-1 review F1); overlap checks span attestation boundaries (L1).
- Matcher `finding-episode-3` (`analytics/finding_episode.py`): `claim.end_reason` (`OFF_OBSERVED|CANDIDATE_ENDED|OPEN_BOUND|SERIES_LIMIT`) and `claim.series_limits` with exact lineage; a cut tail drops its dependent `OPEN_BOUND`.
- Shared money gate `financials/money_eligibility.py` (`money-eligibility-1`): PENDING_REASSESSMENT > WITHHELD_GENERATOR_SERIES > ELIGIBLE, read-derived on every read, fails closed. Consumed by `ConsequenceReadService(eligibility=...)` (gates `presented_as_current`/`current_amount_shown`), `finding_api.bridge_consequence` (states + `recorded_consequence_revision_id`), and `scheduling/upstream.py` `findings[].money_eligibility` for S5-01. ELIGIBLE is not an amount authorization.
- Migration 0015 `0015_finding_returning_basis`: FindingRevision basis may return (A -> B -> A); replay guard compares with the latest revision only.
- UI: Financials bridge shows withheld/pending with the refused span and an exact link to the recorded consequence; Finding page states a SERIES_LIMIT end.
- Walkthrough: `tools/s402c_late_power_walkthrough.py run|attest|tick|serve|drop --db assetops_lr01*`; browser claims `tools/lr01-money-evidence.mjs`.
- Open: real-source clock proof has no write path (by design); S5-01 owns its own UI over the seam; the schedule install gate stays closed until this slice is reviewed and merged; broader per-analytic input/clock coverage remains the owner analysis-input backlog.

## S5-01 - selected-window Site Overview (phases 1-2 built, slice review pending)

Branch `task/S5-01-site-overview` (LR-01 merged in, unmerged to main); handoffs `.agent/S5-01-phase-1-handoff.md`, `.agent/S5-01-phase-2-handoff.md`; packet `.agent/S5-01-review-packet.md`; owner steps `.agent/S5-01-owner-walkthrough.md`.

- Read: `site_overview/read.py` `SiteOverviewRead.read` builds `site-window-summary-1` for one UTC day over committed records (no projection table): accepted-source fingerprint fence, S4-02d `UpstreamCurrentness.window`, fenced S3 day detail, ledger context, one Finding by `D-2026-10-15-s501-finding-choice`, exact-head money with the real Performance gate. `money_state.py` is the pure no-amount precedence.
- Money: `PRICED` also requires the LR-01 seam row's `current_amount_permitted` (fail closed as `CONSEQUENCE_STALE`); the raw gate is S5's own exact read, never the seam's rewrite.
- Pin: optional `finding_id`/`finding_revision_id`; must intersect the day (`NOT_IN_SELECTED_DAY`), exact revision only while the source is closed, retained while discovery is incomplete; `previous_pin` (top-level and in `known_finding`) names why a pin is not shown. `PinNotFound` -> 404.
- Route: `site_overview/route.py` at the existing `GET /api/sites/{site}/overview` (evidence router delegates first): access 401/403, scope (typed 503 `SITE_STORE_UNAVAILABLE`), S2 409, UTC day 422s, Performance gate. Legacy `date=` becomes the midnight pair.
- Composition: one seam per process; S5 reuses the seam's consequence read and Finding store; `main.py` disposes through `app.router.on_shutdown` (FastAPI 0.141 has no `add_event_handler`).
- UI: `sites/SiteWindowOverview.tsx` (no SVG; CSS-bar timeline), `SiteOverview.tsx` S5 branch with URL `date`/pin written back from the served values, `siteOverviewClient.ts` validator; destinations from `shell/SiteDetailFrame.tsx`. Day navigation is links.
- Walkthrough: `tools/s5_overview_walkthrough.py` (`assetops_s501_owner*`, `var/s501_owner*`, ports 8925/5425, ticks env `default`); browser claims `tools/s5-overview-evidence.mjs <base> <initial|pending|eligible|stopped|closed>`.
- Open: Site Finding index (list stays unavailable); `mini:3#a/b` (S4-04/S5-02); L5 fence placement and Postgres merge/midnight cases (fakes only); production schedule thresholds make demo amounts lapse 5 minutes after a manual tick; merge and `mini:1#a/2#a/4#a` promotion held for the owner record.

## S4-04 - Site Finding index and list (phases 1-2 built, slice review pending)

Branch `task/S4-04-site-finding-index` (base main `f8a131e3`, unmerged); handoffs `.agent/S4-04-phase-1-handoff.md`, `.agent/S4-04-phase-2-handoff.md`; packet `.agent/S4-04-review-packet.md`; owner steps `.agent/S4-04-owner-walkthrough.md`.

- Read: `GET /api/sites/{site_code}/finding-index` (`finding_index_api.py`, service `analytics/finding_index.py`, SELECT-only store reads `index_snapshot`/`index_lineage` in `postgres_finding_store.py`). No snapshot table, so only `CURRENT` carries rows and `total_count`; refusals 422/409 carry neither.
- Discovery: fixed point over UTC days via stored canonical episodes within 20 min of an edge AND (phase-1 review H1) selected S3 Candidate segments within 20 min of the edge day's edge (`candidate_reach`); cap 62 -> 409 `INDEX_CONTINUITY_LIMIT`. The H1 root cause (matcher pass marking a deferred window matched) is fixed separately on `fix/S4-deferred-match`.
- UI: `sites/findingIndexClient.ts` (typed result union incl. `not_imported`, `closed`, `continuity_limit`, `basis_changed`, `invalid`), `sites/SiteFindingIndex.tsx`; `shell/SiteAnalyticsFrames.tsx` `SiteFindingsFrame` keeps scope in the URL (`domain/from/to/limit/cursor`, default today's UTC day) and falls back to the T028 `SiteFindings` on a 404. `App` prop `siteFindingIndex`. Row link text is the lifecycle title (stored titles fail the product-vocabulary scan).
- Walkthrough: `tools/s404_finding_index_walkthrough.py` (`assetops_s404_owner*`, `var/s404_owner*`, API 8934/web 5434, TLS 8935/HTTP 8936): prepare/serve/late/settle/gate/drop; browser claims `tools/s404-finding-index-evidence.mjs <base> <initial|late|settled|closed> <out> <manifest>`.
- Open: owner record; `mini:3#a/b` (S5-02 consumes this order); money stays unavailable until S4-05 provenance + LR-01 both reviewed in baseline; S5-01 Overview `finding_list` still says unavailable; plain-language copy for the W1 task; merge main after the deferred-match fix and rerun the focused index tests.
## S6-02a - frozen verification, evaluator and exact read (phases 1-2 built, slice review pending)

Branch `task/S6-02a-verification-core` (main `e39a3c20` merged in; unmerged). Packet `.agent/S6-02a-review-packet.md`; handoffs `.agent/S6-02a-phase-1-handoff.md`, `.agent/S6-02a-phase-2-handoff.md`. Authority `D-2026-10-16-s6-verification`, `-s602-questions`, `-s602a-cutoff`.

- Migration `0019_verification_core`: insert-only plan, later selection binding (now with `idempotency_key`/`payload_sha256`), evaluation request, outcome, metric; `action_event` RESOLVED/RESOLUTION_WITHDRAWN only via the evaluator job (SYSTEM_JOB). Ninth writer only; rule 8 entries literal.
- Rules `actions/verification_rules.py`: slots/coverage/bands/target plus `decide` (VERIFIED/INEFFECTIVE/INCONCLUSIVE, unknown overrides known failure) and `source_pair` (per window, never the union). Timestamps `+00:00`.
- Service `actions/verification.py`: freeze (F1 baseline revision = change's split/superseded; F2 every baseline day S3 CURRENT; F3 S2 acceptance fence in `freeze_plan`), binding (after `later_end`, head plan, CURRENT, idempotent key), `evaluate` (one trial-locked transaction: request, outcome+metrics, RESOLVED/WITHDRAWN), `current_state` (late evidence, moved/non-current S3 or S4 day, changed covering Foundation -> REASSESSMENT_PENDING), `outcome`, `history`, `summary`.
- Ports: `VerificationPorts(day_status, provenance)` wired by `actions/composition.verification_ports` (S3 `DispatchReadService.window` + S4 `match_state`; S4-05a resolver). Missing port fails closed.
- Holds `actions/service.py`: `is_unresolved` from latest resolution; `PRIOR_TRIAL_GUARDRAIL_FAILED`; `reassessment_overlaps` (R1: only the withdrawal's named late evidence; window `[max(closure, evidence accepted), withdrawal)`) -> `PRIOR_TRIAL_REASSESSMENT_OVERLAP`. Same codes in accept guard and Recommendation.
- Routes: POST `.../verification/evaluations`; GET `.../verification/outcome`, `.../verification/history`; Action, Change and Recommendation reads carry `verification`.
- Fixtures: `backend/tests/fixtures/s6_verification_api_contract.json` (TEST-SCOPED complete windows over a real roles-2 Site; shape check), `s6_action_api_contract.json` regenerated (additive). Replay `backend/conversions/d-verification-window-v1.json` + `host/tests/test_s6_verification_replay.py`.
- Open: the replay is complete (12/12 slots, REGISTERED_SIMULATION pair PASS) but settles INCONCLUSIVE: the shipped mini-grid generator ignores the reserve, so no VERIFIED Lab path exists (Architect). Registered scenario/profile lineage is not centrally observable (source pair checks class, fixtures or distinct run digests only). Change read keeps its apply-time `outcome: PENDING` beside `verification`. Late-evidence race between the evaluator's read and its commit is narrow, not closed. Registry nodes stay `open` until review.

## S4-05b - registered producers, stored-source reads and owner walkthrough (phases 1-2 built, in_review)

Branch `task/S4-05b-producers-reads-walkthrough` (unmerged; owner W1 copy checkpoint first). Packet
`.agent/S4-05b-review-packet.md`; owner steps `.agent/S4-05b-owner-walkthrough.md`; ruling D-2026-10-16-s405b-label
(`.agent/architect-S4-05b-answers.md`).

- Producers: `tools/s4_finding_cases.py` `publish_authored`/`post(fixture=)` publish each exact batch before upload
  (P01/P02); Lab Commit registers the whole sealed Stage first (`runs/registered_release.py` `publisher_for`, wired in
  `host/lab_app.py`); any Stage status outside STAGED/NOT_STAGED/HELD -> `SOURCE_PUBLICATION_REFUSED`
  (`STAGE_NOT_ATTESTABLE`), nothing released; Lab shows the refusal (`RunCommitPanel`).
- Reads: `evidence/provenance_read.py` (`source_gate`, `permits_current_money`, `MIXED_OR_UNKNOWN_SOURCE`) feeds
  `financials/consequence_read.py`, `finding_api.py` `bridge_consequence`, `site_overview/read.py`
  (`source_provenance`, `source_gate`, `withheld_reasons`) and `actions/service.py` (pinned origin revision; unwired
  or failing -> UNKNOWN). `demonstration_label.py` deleted.
- UI: `frontend/src/sites/sourceProvenance.tsx` (`SOURCE_WORDS` per ruling; unknown states -> UNKNOWN), used by
  Finding, Evidence, consequence/Financials, Overview, Action, Recommendation; marker `[data-source-provenance]`.
- Pilot install gate (`tools/schedule-install-gate.py`) always requires `I-attested-real-source-provenance`.
- Walkthrough `tools/s405_provenance_walkthrough.py` (DBs `assetops_s405_{owner,old,mixed}<suffix>`, work
  `var/s405_*`, API 8935/web 5435, `serve --case`); browser claims `tools/s405-provenance-evidence.mjs`.
- S5-01 packet amended (shared contract item 5).
- Open: owner copy approval; `ATTESTED_REAL_SOURCE` class (separate task); `MoneyInputs.provenance_resolved`
  default True for unit tests; per-row provenance queries in consequence history; Action fixture size.
## S5-02 - Finding list in Site Overview (built, slice review pending)

Branch `task/S5-02-overview-finding-list` (base main `5c1d9d42`, unmerged); packet `.agent/S5-02-review-packet.md`; owner steps `.agent/S5-02-owner-walkthrough.md`. No backend change.

- UI: `sites/OverviewFindingList.tsx` reads the S4-04 index for the Overview's served `window.start/end` (domain `mini-grid-dispatch`, `OVERVIEW_FINDING_PREVIEW_LIMIT = 2`, first page), drops older answers, renders `current-empty` / non-current status / refusal / `current-rows` (`data-overview-finding-list`), full-list link with the identical window.
- Parity: `compareParity` implements `D-2026-10-16-s502-parity` (index CURRENT+is_current with a row; card `DISCOVERED`, source open, not audit; both episodes intersect the day; Site, window, day selection seq, run, assessment record, model, input/config hashes, match pass and matched-through all present and equal; day matched) -> `same` / `different` / `not-compared` with both bases and "Reload both". Rows are never hidden.
- Composition: `shell/SiteDetailFrame.tsx` injects `findingIndex` (default client; `App` `siteFindingIndex`) and `windowLinks.findingList`; `SiteWindowOverview` shows the list only when both are supplied, else the old placeholder. `SiteOverview` has a reload counter. `SiteFindingIndex.tsx` exports `STATUS_WORDS` and `Basis`.
- Tests: `shell/__tests__/s502OverviewFindingList.test.tsx`; S5 summary builders in `shell/__tests__/s5WindowFixtures.ts`.
- Walkthrough: `tools/s502_overview_finding_list_walkthrough.py` wraps the S4-04 tool (default DB `assetops_s404_owner_s502`, `var/s404_owner_s502`, API 8952, web 5452, TLS 8953, HTTP 8954), runs the S2 Evidence comparison after `prepare` and checks every day reads `site-window-summary-1`; browser claims `tools/s502-overview-finding-list-evidence.mjs <base> <initial|late|settled|closed> <out> <s502-manifest> <s404-manifest>`.
- Open: backend still emits `finding_list: UNAVAILABLE` (validator requires it); owner record before merge and `mini:3#a/b` promotion; copy ("window" wording, status sentences) for the W1-conclusion task.

## S3-02a - selected-assessment capability and claim-limit read (built, slice review pending)

Branch `task/S3-02a-capability-read` (base main `71009bf6`, unmerged); packet `.agent/S3-02a-review-packet.md`; S3-02b handoff `.agent/S3-02a-handoff.md`. No migration.

- Read: `analytics/claim_limit_read.py` `ClaimLimitReadService.read(tenant, site, day, revision_id, rule)`, rule `s3-claim-limit-1` over `dispatch-3.2` only (`SUPPORTED_MODELS`). Capability = per required role (`generator_state`, `feeder_demand`, `pv_available_power`, `pcs_discharge_capability`, `battery_soc`) exact COVERED/MISSING/POOR_QUALITY/CONFLICTED/NOT_EVALUATED spans with minutes and pinned accepted Evidence IDs, derived from the revision's stored segments (unknown problem text fails closed to MISSING). Claim limit: interval ceiling CANDIDATE_AVOIDABLE/NECESSARY (COMPLETE or LIMITED, `supported_minutes` = that class's segment sum) or INDETERMINATE; withheld (INDETERMINATE) on unusable cohort or a non-covered required role inside a claim-carrying segment. Current ceiling only when the window projection is CURRENT and the revision is in the selected run; otherwise `currentness` PENDING/FAILED/STALE_PROJECTION/HISTORICAL and only `historical_ceiling`. No revision -> `UNASSESSED` + `NO_REVISION_SELECTED`. Window revisions list `interval_ceilings (top level only when CURRENT; otherwise under historical_ceiling)`, no single ceiling.
- Store: `PostgresAssessmentStore.claim_limit_snapshot` reads the window snapshot and the revision detail in one REPEATABLE READ snapshot (`_window`, `_revision_detail` extracted; existing methods unchanged in behaviour). Reads only; no new SQL writer.
- Route: `claim_limit_api.py` `GET /api/sites/{code}/performance/dispatch/windows/{day}/claim-limit?revision=&rule=`; order access 401/403 -> scope 404 -> 503 -> 422 (`INVALID_REVISION_ID`, `UNSUPPORTED_RULE_VERSION`) -> Performance gate 409 `PERFORMANCE_CUTOVER_CLOSED` -> read (404 `ASSESSMENT_REVISION_NOT_FOUND`, 422 `REVISION_OUTSIDE_WINDOW`/`UNSUPPORTED_RULE_VERSION`, 409 `ACCEPTED_LINEAGE_ABSENT`). Wired in `main.py` with `performance_gate`; composition `build_claim_limit_read_service`.
- Fixture: `backend/tests/s3_claim_limit_records.py::build(runner, url)` (S4 `CaseRunner`, Batch V2 + S3 worker) -> manifest `s3-claim-limit-records-v1` (days 10-06 full-candidate, 10-08 missing-pv, 10-11 poor-quality-conflict, 10-13 late-revision with `withdrawn`, 10-15 stale-selection). Normalised sample responses `backend/tests/fixtures/s3_claim_limit_api_samples.json`.
- Tests: `test_s3_capability_read_postgres.py`, `test_s3_claim_limit_postgres.py` (gate, fail-closed and currentness mutations proven).
- Open: registry `I-capability-read`/`I-claim-limit-read`/`I-S3-02a` stay open until review; Necessary/open-bound/cohort/configuration/absent-lineage are proven by mutating the real snapshot, not by separate ingested cases; S3-02b UI and walkthrough; S6-02a's `0019` does not interact (no migration here).

## S6-02b - Action verification surfaces (phases 1-2 built, in_review)

Branch `task/S6-02b-verification-ui` (from main `cdb09767`; unmerged; owner walkthrough required). Packet `.agent/S6-02b-review-packet.md`; handoffs `.agent/S6-02b-phase-1-handoff.md`, `.agent/S6-02b-phase-2-handoff.md`. Authority `D-2026-10-16-s6-verification`, `-s602-questions`, `-s602a-replay`, `-s602a-holds`.

- Simulator: `mini-grid` v5 (`packs/mini_grid.py` `decide_v5`, `START_HEADROOM_OVER_RESERVE = 5`) starts the generator at min(Site start threshold, reserve in effect + 5); v1-v4 unchanged. Registered in `runs/profiles.py`, `host/execution_adapter.py`. Scenario `kobo-mini-grid-reserve-trial` v1 (fingerprint pinned).
- Replay: `backend/conversions/d-verification-window-v2.json` (windows predeclared) reaches VERIFIED through gateway/S2/S3/S4 and the Action API; `host/tests/test_s6_verification_replay.py` parametrized v1 (INCONCLUSIVE) and v2.
- Frontend: Action child views `plan`, `evidence`, `verification` (`sites/SiteActionVerification.tsx`, `verificationClient.ts`, `verificationWords.ts`); selectors `plan_revision_id`, `outcome_id`, `event_id`, `recorded_at` carried by `SiteActionFrame` section links; explicit selection = Historical with separate current state; typed `VERIFICATION_SELECTOR_CONFLICT`; Recommendation/Change panels in `recommendationVerification.tsx`; Change and Overview read the `verification` block (F5).
- Tools: `tools/s602b_verification_walkthrough.py` (replay DB + one DB per test-scoped case; `serve --case`; `capture` starts APIs itself), `tools/s602b_test_scoped_cases.py` (build + pinned-clock wrapper reusing the evaluator builders' fakes), `tools/s602b-verification-evidence.mjs` (`ASSETOPS_S602B_PART`), `tools/layout-evidence.mjs` mode `ASSETOPS_LAYOUT_S602B_ACTION`.
- Open: `I-sim-verification-cases`, `D-verification-window` stay open (non-pass variants are test-scoped, not Lab runs); served REASSESSMENT_PENDING proven only in fixture tests; inconclusive case has no data-carried test-scoped label; mock-fidelity copy pass at W1 conclusion; `siteFoundationChange.test.tsx` h1 wait is load-sensitive in the full parallel run.
## S6-03 - Site Work Action list (phases 1-2 built, in_review)

Branch `task/S6-03-site-work-list` (base main `cdb09767`, unmerged); packet `.agent/S6-03-review-packet.md`; owner steps `.agent/S6-03-owner-walkthrough.md`. No migration (head stays `0019_verification_core`); no new SQL writer.

- Store: `PostgresActionStore.site_window(tenant, site, start, end)` (`actions/adapters/postgres_action_store.py`) reads every Action created in `[start,end)` and all their events in one REPEATABLE READ, READ ONLY snapshot (SELECT only).
- Read: `actions/site_index.py` `ActionIndexService.read` + `parse_request` (UTC, `from<to`, <=31 days, limit 1-100 default 25, opaque base64 cursor). Latest event by `(recorded_at,id)`; state = `actions.lifecycle.reduce` (same as detail); links via `actions/service.py` `selected_action_links` (module function extracted from `ActionService._links`; detail unchanged). Fence = max created, max event recorded, Action count, event count (+ token `sai1-...`); cursor binds tenant/Site/window/fence/last key. Refusals: 422 `WINDOW_REQUIRED|INVALID_WINDOW|INVALID_LIMIT|INVALID_CURSOR`, 409 `ACTION_INDEX_BASIS_CHANGED` (`SCOPE_CHANGED|FENCE_CHANGED`), 409 `ACTION_INDEX_INCONSISTENT` (event without Action, Action without any ACCEPTED event), 503 `ACTION_STORE_UNAVAILABLE`; all carry `rows: null, total_count: null`.
- Route: `action_index_api.py` `GET /api/sites/{code}/action-index?from=&to=&limit=&cursor=` (401/403 -> 404 -> 503 -> 422 -> read); composed in `main.py` over the Action service's store and clock. No Performance gate (Action detail has none).
- Fixture: `s6_action_records.build(..., second_created_after=)` (default keeps the committed S6-01a contract); `backend/tests/fixtures/s6_site_action_index_contract.json` (regenerate `ASSETOPS_WRITE_S603_CONTRACT=1`; each run checks field structure).
- Tests: `test_s6_site_action_index.py` (no DB), `test_s6_site_action_index_postgres.py` (D-action-records rows, paging, fence incl. older-stamped event, isolation, zero, refusals, same-fence detail parity; S6-02a RESOLVED/RESOLUTION_WITHDRAWN rows).
- UI: route `/sites/:siteId/work` (`SITE_WORK_ROUTE_PATH`, `siteWorkHref`), Work tab capability true, `SiteWorkFrame` (SiteAnalyticsFrames.tsx) with one "Actions" sub-tab; `sites/SiteWorkActions.tsx` + `sites/actionIndexClient.ts`; choose-window state reads nothing; IDs/fence in the "What this list is based on" disclosure. Tests `sites/__tests__/siteWorkActions.test.tsx`; tab expectations updated in `operatorSiteTabs.test.tsx`, `overflowContainment.test.tsx`, `tools/layout-evidence.mjs`.
- Walkthrough: `tools/s603_site_work_walkthrough.py prepare|serve|attest|drop` (`assetops_s603_owner*`, `var/s603_owner*`, API 8963/web 5463); browser claims `tools/s603-site-work-evidence.mjs`.
- Open: registry `I-site-action-index-read`/`I-sitework-ui`/`I-S6-03`/`sitework:1#a` stay open until review; Incidents/Maintenance tabs not rendered; owner/due/priority absent; plain-language copy for the W1-conclusion task; whole-window load (no SQL paging) is fine at W1 sizes.
## S3-02b - Evidence Analysis selected claim limit UI (built, in_review; owner walkthrough before merge)

Branch `task/S3-02b-claim-limit-ui` (base main `8b5d8137`, S3-02a merged); packet `.agent/S3-02b-review-packet.md`; owner steps `.agent/S3-02b-owner-walkthrough.md`. Frontend and a walkthrough tool only; no backend change, no migration.

- Client `frontend/src/sites/claimLimitClient.ts`: `getClaimLimit(site, day, revision|null, signal)` over the S3-02a route; `getAssessedDay(site, day, signal)` maps the S3 dispatch window read to periods (whole-day revision + interval revisions, interval bounds from segments). Results are named: loaded / unauthenticated / forbidden / not_found(code) / closed / refused(code: 422 and 409 lineage) / unavailable / aborted.
- Section `frontend/src/sites/EvidenceClaimLimit.tsx` ("What the selected assessment can support"), rendered on every Evidence Analysis view beneath S2's `ClaimLimit` (`LedgerSiteEvidence.tsx`) and on the legacy analysis view (`SiteEvidence.tsx`). Selection is `day=<YYYY-MM-DD>&revision=<id>`; the legacy `assessment` parameter is not read. No day -> no read, "No assessment selected"; day without revision -> UNASSESSED read + period links. Positive sentence only when `currentness === CURRENT` with the rule's current claim (INDETERMINATE stated as such); others say no current conclusion and show the earlier ceiling as "At the time ...". Accepted IDs link in-page (`record=`, day/revision kept); pinned revision links to Performance > Dispatch through a shell-built `assessmentHref` (`SiteEvidenceFrame.tsx`). Rule, codes, IDs, run/cohort and watermarks sit in a closed "Technical details" disclosure. Stale answers are dropped (AbortController per selection).
- `SiteEvidenceClient.claimLimit` (optional) is wired in `createSiteEvidenceClient`; `settled.ts` LOADING knows the two new sentences; CSS `.claim-limit*` in `ui/primitives.css`.
- Tests `frontend/src/sites/__tests__/evidenceClaimLimit.test.tsx` (28) over S3-02a's samples.
- Walkthrough `tools/s302_claim_limit_walkthrough.py prepare|links|serve|late|attest|drop` (db `assetops_s302*`, work `var/s302*`, API 8932, web 5442): builds S3-02a's fixture, runs the Evidence then Performance comparisons (recorded in `gates.json`), verifies every case through the served route; `late` ingests a late SOC reading on 10-06 without a worker pass (STALE_PROJECTION); `attest` fails unless both gates passed and every served read matches.
- Open: registry `I-evidence-analysis-claim-limit-ui`, `I-S3-02b`, `I-S3-02` and `evidence-analysis:2#b` stay open until review and owner walkthrough; no ingested NECESSARY case (vocabulary only); a CURRENT whole-day revision's interval list is not covered by a sample or the walkthrough; copy polish goes to the W1-conclusion task.
## S7-01a - Site source-health and battery boundary reads (built, slice review pending)

Branch `task/S7-01a-health-read` (base main `8b5d8137`, unmerged); packet `.agent/S7-01a-review-packet.md`; S7-01b contract `.agent/S7-01a-handoff.md`. No migration.

- Source health: `evidence/source_health.py` (schema `assetops.site-source-health` v1, rule `assetops.source-health.two-clock.v1`): contact `CURRENT|STALE|UNKNOWN` from server receipt (`freshness`), reported facts `CURRENT|OLD|UNKNOWN` from `observed_at` and clock trust (`|offset| > 5000 ms` UNTRUSTED, null UNKNOWN), queue/disk as `LAST_REPORTED`, per-source contact only when the diagnostic carries it. `check_consistent` refuses a non-snapshot isolation, duplicate/foreign/unregistered rows, row/text mismatch and a receipt after `read_at`. No derived projection: `stale_projection.applicable = false`.
- Store: `PostgresGatewayAccess.source_health_snapshot` (read only; `_health_registration`, `_health_latest` `DISTINCT ON` with the S2 order) in one REPEATABLE READ transaction. S2 `gateway_health` and its route unchanged.
- Battery: `sites/battery_boundary.py` (schema `assetops.asset-boundary` v1) over `FoundationService.read` (effective Foundation + binding set); physical condition always `UNKNOWN` (missing temperature history, measured capacity, stress history) or `NOT_CONFIGURED`; declared rating and bound channel IDs under their own labels; no SOC value.
- Routes: `source_health_api.py` `GET /api/sites/{code}/source-health`; `asset_boundary_api.py` `GET /api/sites/{code}/battery`, `GET /api/sites/{code}/assets/{asset_id}/battery`; both use `finding_api.Access`, wired in `main.py`.
- Fixture: `backend/tests/s7_health_cases.py` `HealthCases.register/publish/deliver` (`D-edge-health-cases`, one gateway per case, provisioning CLI + authenticated central ingestion; fixture SQL only for case gateway/source registration).
- Tests: `test_s7_source_health_postgres.py`, `test_s7_asset_boundary_postgres.py`.
- Open: registry `D-edge-health-cases`, `I-source-health-read`, `I-asset-boundary-read`, `I-S7-01a` stay open until review; no superseded-revision battery case (no Foundation revision writer used); accepted SOC not selected; S7-01b UI and walkthrough.

## S7-01b - Site Health and battery boundary UI (built, slice review then owner walkthrough)

Branch `task/S7-01b-health-ui` (base main `f3de235a`, unmerged); packet `.agent/S7-01b-review-packet.md`; owner steps `.agent/S7-01b-owner-walkthrough.md`. No migration.

- Backend follow-up (`D-2026-10-16-s701-clock`): `evidence/source_health.py` `CLOCK_OFFSET_LIMIT_MS` and `OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS` (both 5000, inclusive; the latter disclosed as `clock.observed_after_receipt_allowance_ms`); `summary.reason` `NO_ENABLED_GATEWAY|NO_REGISTERED_GATEWAY|null`; `reported_age` nulls `fact_age_seconds` / `reported_contact_age_seconds` under an UNTRUSTED clock or a time after `read_at`. `sites/battery_boundary.py` raises `BindingBasisInconsistent` (409 `FOUNDATION_BASIS_UNAVAILABLE`) when the binding set names another Foundation revision (review L6).
- Fixture: `s7_health_cases.HealthCases.deliver(keys)` re-posts each case's last facts; `CURRENT_CONTACT_KEYS` for the walkthrough.
- Contract: `backend/tests/fixtures/s7_health_api_contract.json` (UUIDs/digests normalised), regenerated/compared by `test_s7_health_contract_postgres.py` (`ASSETOPS_WRITE_S7_CONTRACT=1`); the frontend tests read it.
- UI: `frontend/src/sites/healthClient.ts` (typed refusals keep HTTP status/code), `SiteHealth.tsx` (status strip "Gateway contact", battery, contact, queue/storage, device contact, Technical details; `?gateway=` selection), `SiteBattery.tsx` (entry `/assets`, detail `/assets/{asset}`); links via `HealthLinksContext` from `shell/SiteHealthFrames.tsx` (substrate stays a leaf). Routes `SITE_HEALTH_ROUTE_PATH`, `SITE_ASSETS_ROUTE_PATH`, `SITE_ASSET_ROUTE_PATH`; Health tab enabled in `operatorSiteTabs.tsx` (tab inventories in three tests and `tools/layout-evidence.mjs` updated).
- Walkthrough: `tools/s701_health_walkthrough.py prepare|serve|links|deliver|attest|drop` (KOBO-001 bindings before case gateways; KOBO-002 without battery); evidence `tools/s701-health-evidence.mjs` (40 claims at 1440/390).
- Open: no `STALE_PROJECTION` state (read has none); accepted SOC not shown; positive `asset:3#b`, warranty/replacement stay unmapped; plain-language and visual polish carry to the W1-conclusion fidelity pass; registry `I-source-health-ui`, `I-asset-boundary-ui`, `health:2#a`, `asset:3#a` close only after review and owner walkthrough.

## S4-08 - Site assumption and consequence history (built, in_review; slice review gates merge)

Branch `task/S4-08-assumption-history` (base main `e46bbd7c`, unmerged); packet `.agent/S4-08-review-packet.md`. No migration; read-only (no new writer).

- Read: `financials/consequence_history.py` (`ConsequenceHistoryService`, cursor/fence, `classify`), store method `PostgresConsequenceStore.site_history` (one REPEATABLE READ snapshot: DB-clock default cutoff, fence count + max `(recorded_at, id)`, keyset page, FindingRevisions with latest consequence at cutoff, price links joined to assignments, prior digests). Route `consequence_history_api.py` `GET /api/sites/{site}/financial-assumptions/consequences?recorded_at=&after=&limit=`, included in `main.py` before the price-revision route; composed by `financials/composition.build_consequence_history_service`.
- Row contract: exact Finding/FindingRevision/consequence/price IDs, `at_cutoff` CURRENT/HISTORICAL, price state `LINKED|NO_PRICE_LINK|NOT_EVALUATED|LINEAGE_INCONSISTENT`, `change_from_prior` (`PRICE_ONLY` drives the plain sentence), `recorded_amount.disposition` `SHOWN|SOURCE_CLOSED|MIXED_OR_UNKNOWN_SOURCE|UNPRICED|QUANTITY_UNAVAILABLE|MINOR_UNIT_UNKNOWN|LINEAGE_INCONSISTENT`, per-row S4-05b block; `current_amount_shown` is always false. Cutoff string is `isoformat()` UTC (`+00:00`, microseconds), equal to the price read's echo.
- Refusals: 400 `INVALID_CURSOR`, 409 `CONSEQUENCE_HISTORY_BASIS_CHANGED` (`SCOPE_CHANGED|FENCE_CHANGED`), 422 `INSTANT_NOT_ZONED|INVALID_CUTOFF|INVALID_LIMIT|CUTOFF_REQUIRED_WITH_CURSOR`, 503 `CONSEQUENCE_HISTORY_UNAVAILABLE`; closed S3 gate lists rows with `SOURCE_CLOSED`.
- UI: `frontend/src/sites/ConsequenceHistory.tsx` ("Interpretation history" panel), `SiteAssumptions` reads history first and passes its cutoff string to the price read (default URL unchanged; `data-price-cutoff` now RECORDED_CUTOFF on default; history failure = plain price refusal `data-financials-read="no-cutoff"`); URL params `history_after`, `history_limit`; client `getConsequenceHistory` (`basis_changed` result reloads page one).
- Tests: `backend/tests/test_s4_consequence_history.py` (25), `test_s4_consequence_history_postgres.py` (7, incl. interleaved late commit), `frontend/src/sites/__tests__/siteFinancials.test.tsx` (+8).
- Walkthrough: `tools/s408_assumption_history_walkthrough.py` (wraps s405 owner+mixed under `assetops_s408*`; adds v2-v6 incl. S4-06 equal-start v5 and part-way v6); evidence `tools/s408-assumption-history-evidence.mjs` (owner/closed/mixed modes); S4-02a evidence asserts the unchanged default URL and one cutoff.
- Open: recorded amount display does not apply LR-01 eligibility (history is audit, as pinned versions on Finding Financials); Finding links pin exact IDs, not the cutoff; `assumptions:3#a` promotion waits for review; wording to W1-UX-02.
## W1-UX-01 - shared product presentation (built, in_review)

Branch `task/W1-UX-01` (base main `3e6dbc88`, unmerged); packet `.agent/W1-UX-01-review-packet.md`; shared API `.agent/W1-UX-01-handoff.md`. Frontend only.

- Words: `frontend/src/ui/productWords.ts` - `currentnessWords`, `readResultWords`, `moneyWords`, `outcomeWords(outcome, reasons, sourceClass)`, `limitationWords`, `sourceQualification`, `asOfText`/`plainTime`; unknown codes -> `UNRECOGNISED_SENTENCE`, never positive.
- Components: `frontend/src/ui/ProductStatus.tsx` - `ProductStatus`, `ProductOutcome`, `ProductLimitation`, `HeadlineVisualCard`, `ExactReferences` (closed "How this was worked out"), `ValueBars` (null = hatched "not known"), `StepStrip`; CSS at the end of `primitives.css`.
- Scan: `productVocabulary.json` v3 with `w1` set v1; `scanProductVocabulary(root, page, { set: "w1" })`, `scanDisclosureVocabulary`, `rawCodes` (case-sensitive; SOC/UTC/kW/kWh/PV allow-listed); a scan root cannot exempt itself. Shared check `frontend/src/test/productPresentation.ts` `expectStateLineVisible`.
- Migrated and opted into W1: Overview objective (`SiteWindowOverview.tsx` `Objective`), Evidence conclusion (`LedgerSiteEvidence.tsx` `OverviewBody`), Action state (`SiteAction.tsx` `ActionStateCard`).
- Capture: `tools/w1-ux-01-evidence.mjs <out> <mock-id>[:<case>]=<url>`.
- Open: the other 23 W1 routes remain on the T028 scan until UX-02..05; domain word maps still duplicate cross-screen states; the Evidence read has no read instant (as of = latest delivery received); the Action summary has no source class; registry Low D (`I-W1-UX-01` requires) untouched.

## W1-UX-02 - Site, Finding and money presentation (built, in_review)

Branch `task/W1-UX-02` (base main `a8cbb3d1`, code `bc1cea1b`, unmerged); packet `.agent/W1-UX-02-review-packet.md`; handoff `.agent/W1-UX-02-handoff.md`. Frontend only.

- Migrated to the W1-UX-01 layer and opted into the W1 set: `sites` (`SitesIndex.tsx` `SitesAnswer`), `mini` freshness/money/timeline/Finding list (`SiteWindowOverview.tsx`, `OverviewFindingList.tsx`), `sitefindings` (`SiteFindingIndex.tsx`), `finding`/`finding-evidence`/`finding-history` (`SiteFinding.tsx`, `SiteFindingEvidence.tsx`, `SiteFindingHistory.tsx`), `financials` (`FindingConsequence.tsx`), `assumptions` (`SiteFinancials.tsx`, `ConsequenceHistory.tsx`).
- Word maps: `findingCurrentnessWords` (`findingWords.ts`), `consequenceWords` (`FindingConsequence.tsx`), `MONEY_STATE_WORDS` on `moneyWords`; `FRESHNESS_WORDS`, `CURRENTNESS_WORDS`, `STATE_HEADLINE` removed. `FindingRefusalCard` (`findingPresentation.tsx`).
- `LINK_WORDS` stays equal to backend `BROKEN_WORDS`; `LINK_DISPLAY_OVERRIDES` rewords two "fingerprint" codes on screen.
- Money: a `ValueBars` amount only for a PRICED+CURRENT bridge with both bounds; every other state draws a not-known mark and gives a "why no current amount" line. The S4-08 history is recorded-only.
- Evidence: `tools/w1-ux-02-evidence.mjs`; all eight screens captured at 1440/390 (packet).
- Open: untimed reads say "As of: time not recorded"; `LINK_DISPLAY_OVERRIDES` awaits a backend rewording; there is no Financials Analysis tab; `FindingDetail.tsx` (legacy route) is not migrated; `s502-overview-finding-list-evidence.mjs:148` is stale.
## W1-UX-03 - Evidence, Dispatch and Analysis presentation (built, in_review)

Branch `task/W1-UX-03` (base main `b4a89314`, unmerged); packet `.agent/W1-UX-03-review-packet.md`; handoff `.agent/W1-UX-03-handoff.md`. Frontend only.

- `frontend/src/sites/periodStrip.tsx` (+ `.css`): local `PeriodStrip` - rows of read-returned time segments on the period's own bounds, optional exact links per segment, required summary text, hatched "not known" row; used by Evidence and Dispatch.
- Evidence Overview: `ReportingFacts` (readings / gateway contact / analysis up to date as separate facts, as-of, per-source latest-taken strip). Evidence Analysis: lead question; S2 limit panel and the S3-02b section ("What the readings can support") precede the inspector.
- `EvidenceClaimLimit.tsx`: shared `ProductStatus` (currentnessWords; CURRENT without a positive conclusion -> limited tone; refusals via `readResultWords`, as of = answer time), `RoleStrip` covered/missing per needed reading; local `CURRENTNESS_WORDS` removed; Technical disclosure values are single labelled references.
- `PerformanceDispatch.tsx`: `statusWords` wraps `currentnessWords` with dispatch `STATUS_SENTENCES` (`dispatchWords.ts`, replaces `STATUS_WORDS`); Overview `HeadlineVisualCard` "dispatch-story" with `DayBlockStrip` (exact revision+block links), totals (unstated portion = not known), limitations, Analysis link, `DispatchReferences`; Analysis `ReadingsToOutcome` (readings -> rule -> bounded conclusion), versions list, stored record and comparison as closed technical disclosures; `constraintWords` unknown -> plain fallback.
- `assessmentAnalysis.tsx`: method version / assessment reference / record-set reference -> `ExactReferences`.
- W1 set opted in: `evidence-analysis`, `dispatch`, `analysis` (`evidence` since UX-01). Capture tool `tools/w1-ux-03-evidence.mjs`.
- Open: G-04 baselined fuel/money sentence keeps "claim" (W1 scan allows only it); no-day claim-limit state has no read instant; source strip shows latest-taken only (no per-source span in the read).
## W1-UX-04 - Action, work, change and verification presentation (built, in_review)

Branch `task/W1-UX-04` (base main `b4a89314`, unmerged); packet `.agent/W1-UX-04-review-packet.md`. Frontend only. All nine routes opted into the W1 vocabulary set (action-overview was opted in by W1-UX-01).

- Answer cards (shared `HeadlineVisualCard`, `data-headline-card`): `recommendation` (`SiteRecommendation.tsx` `RecommendationCard`), `change` (`SiteFoundationChange.tsx` `ChangeCard`), `action-work` / `action-history` (`SiteAction.tsx` `WorkCard`, `HistoryCard`), `site-work` (`SiteWorkActions.tsx` `SiteWorkCard`), `verification` / `action-plan` / `action-evidence` (`verificationCards.tsx`, mounted in `SiteActionVerification.tsx`).
- Domain-local words in `actionPresentation.tsx`: `applicationWords`, `recommendationWords` (holds are problem/waiting, never positive), `plainEventWords`, `trialStep` (moved from `SiteAction.tsx`).
- As-of sources (no read carries a read instant except Site Work `read_at` and Evidence `knowledge_cutoff`): recommendation = acceptance time, else latest stored input window end, else (held) the blocking Action's latest recorded step; change = `recorded_at`; verification = outcome `recorded_at`, else the Action read cutoff/last event; plan = plan `recorded_at`.
- Site Work: proved zero only after a loaded read (`read_at` beside it); a refused/unread list shows "As of: time not recorded" and no count.
- Verification card: failed limits in plain units (minutes, %, kWh); a selected earlier outcome reads Historical with "Current state:" beside it.
- Jargon labels made plain: Input/Plan content/Day group/Configuration reference; stored measure values and day-group status are exact references.
- Capture: `tools/w1-ux-01-evidence.mjs` knows all W1-UX-04 cards; `W1_NO_VISUAL_OK`, `W1_TAB_TRACE` env.
- Open: refusal states cannot meet `expectStateLineVisible` (no instant to show); Evidence completeness counts slots with no problems (caller-side `slotProblems`); duplicate word maps in `verificationWords.ts` remain (wrapped, not replaced).

## W1-UX-05 - Foundation, Readiness, SLD, Health and battery presentation (built, in_review)

Branch `task/W1-UX-05` (base main `815888f0`). Packet `.agent/W1-UX-05-review-packet.md`.

- Settled: the five routes `foundation`, `readiness`, `sld`, `health`, `asset` lead with the shared `HeadlineVisualCard` and are opted into the W1 vocabulary set. Cards live in `frontend/src/sites/foundationHeadlines.tsx` and `healthHeadlines.tsx`, with domain-local `ProductWords` (period, set-up readiness, contact summary, gateway contact, battery condition); none is `positive`.
- Foundation wording: signal binding -> "channel link", digest -> "content reference", type labels "Solar array"/"Supplied users"; single values marked via `frontend/src/sites/exactValues.tsx` (`UserName`, `ExactRef`).
- SLD reporting is drawn as a not-known mark; Health contact and reported-fact age are separate lanes; battery "cannot yet be judged" with missing inputs as a step strip.
- S7-01b Lows: L1 (observed-after-receipt -> Unknown age), L3 (selected-gateway IDs to the disclosure), L4 (`isBatteryDetail` requires UNKNOWN; 409 test) done.
- Refusals, the empty Foundation period and the unreadable store carry the state line.
- Open: S7-01b L2 (backend negative `receipt_lag_seconds`); shared `expectStateLineVisible` rejects `asOfText(null)`; three backend "binding" statements replaced in the UI only when no link set is in effect; green S1 "Ready to report" verdict remains under the neutral card; `tools/w1-ux-05-evidence.mjs` 390 px overflow measurement inherits a UX-01 timing issue.
- Proof at `af9b6406`: tsc 0; full frontend 1755 passed; check-all 9/9; served captures for all five screens (empty-period page not run by design).

## W1-UX-06 - W1 presentation closeout and combined owner walkthrough (built, in_review)

Branch `task/W1-UX-06` (base main `a9b3b297`, main merged at `22df6d7d`). Packet `.agent/W1-UX-06-review-packet.md`; phase-1 handoff `.agent/W1-UX-06-phase-1-handoff.md`; ruling `D-2026-10-17-w1-ux-06`.

- Settled: one shared evidence width check `tools/evidence-checks.mjs` (`widthGuard`, `AS_OF_PATTERN`) in all 24 browser evidence scripts, enforced by `tools/checks/test_evidence_checks.mjs` (inventory + proximity rule ignoring commented guards) in `check-all.ps1`; shared `expectStateLineVisible` accepts only a formatted UTC instant or "As of: time not recorded".
- Backend: negative `receipt_lag_seconds` -> null; no-set sentences say "channel-link set"; `READINESS_STATEMENT` says "Set up to report means ..." (configuration only); `BINDINGS_NOT_REGISTERED` refusal reworded (code unchanged).
- Labels per the ruling: "Set up to report" badge, "Set-up steps" strip, old/unknown-age selected-gateway lines, non-positive unrecognised/zero-enabled headlines and state line (Health `contactSummaryWords`), own-key Readiness codes (`Object.hasOwn`).
- Financials `useRead` is keyed on its request (no stale-answer commit); `w1-ux-02-evidence` amount check scoped to the card.
- Fixed: Action Evidence crashed on object `SourceSide.reasons` (`SiteActionVerification.tsx`, type in `verificationClient.ts`).
- Walkthrough: `.agent/W1-UX-combined-owner-walkthrough.md` (16 parts, 26 screens + S4-08); final captures and per-tool guides in `.agent/W1-UX-06-evidence/` (1898/1908; the 10 failures are "small visual" on held/empty cards).
- Open: owner notes 1-13 in the walkthrough (money words L4, untimed money L6, Readiness strip vs contact, card/panel duplication, no-picture held/empty cards, SLD 390 inner scroll); `widthGuard` window fallback unexercised in real Chrome; `LINK_DISPLAY_OVERRIDES` and G-04 allowance carried from UX-02/03.
- Proof: backend full 2590 passed/0 skipped at `b7d75daf`; frontend and guards in the packet.

## W1-UX-07 - full v6.9 left menu with unavailable entries (built, in_review)

Branch `task/W1-UX-07` (base main `3bb1b8b2`). Packet `.agent/W1-UX-07-review-packet.md`; ruling `D-2026-10-17-w1-rail`.

- Settled: `NavRailItem` is a discriminated union (`NavRailUnavailableItem`: `kind: "unavailable"; to?: never`); unavailable roots render as `li.nav-rail__unavailable` text with visible `NAV_RAIL_UNAVAILABLE_STATUS` ("Not available yet") and `aria-label="<label>, Not available yet"`, no link/handler/tabindex.
- `OperatorShellLayout.operatorRailItems`: six groups / eleven roots in v6.9 order; live only Sites `/sites` and Findings `/findings`. One item per line (the guard parses it).
- Workspace footer: `WorkspaceShellLayout` renders the gated `Workspace utilities` nav ("WORKSPACE" + "Open Simulator Lab") and passes it via outlet context (`WorkspaceChrome`); `OperatorShellLayout` places it under the rail and stays flag-free. The old `.workspace-bar` above the shell is gone.
- Guard: `Get-OperatorRailFailures` in `navigation-truthfulness.ps1` (fail-closed inventory, live targets registered inside the OperatorShellLayout block before the `*` catch-all, no destination on unavailable items, NavRail type check); 14 fixtures in `tools/checks/navigation-rail-fixtures.ps1` (architecture seam).
- Orphan scan: `REVIEWED_EXEMPTIONS` in `missing-claim-scan.mjs` exempts only the NavRail status const (file + const + exact text, refs confined to that file).
- Evidence: `tools/w1-ux-07-rail-evidence.mjs` (1440/390, gate on/off, mock rail equality).
- Open: promoting any other root needs its cross-site route, inventory, guard expectation and tests changed together; the 390 px rail is about 575 px tall above content (owner look).

## W2-00 - ordinary source events and interval evidence (built, in_review)

Branch `task/W2-00-source-events` (base merged main `dc643215`, rulings `D-2026-10-17-w2-00-answers`). Packet `.agent/W2-00-review-packet.md`.

- Settled: `contracts/assetops_contracts/source_envelope_v4.py` is the V4 parser/canonical text (schema 4, V3 message identity), `V4_MEASUREMENTS`, the kind-to-outcome allowlist, `event_identity_sha256` (canonical `{source, timing minus published_at, payload}`), the dispatcher `parse_canonical_source_envelope_text`, the Batch V2 header reader `read_envelope_header`, and the closed `V4_CHANNEL_MAPPINGS` (`simulator-lab-gateway-cold/1`: 12 cold tuples + 2 reserved EV). V4-only refusal kinds are a subclass of `EnvelopeRejected`; the shared `ENVELOPE_REJECTION_KINDS` is unchanged. Vectors `contract-fixtures/source-envelope-v4-vectors.json`.
- `ingestion_batch_v2.seal_batch_v2`: schema-4 texts (or schema 3 with EVENT/INTERVAL_DELTA) are admitted by header only; V3 texts stay strict.
- Migration `0020_w2_source_event`: seven nullable event columns, four relaxed columns, family/shape/delta/ID/kind-outcome/actor/length CHECKs, partial unique `accepted_event_identity_unique` and `accepted_ev_start_unique`, conflict-kind CHECK for three kinds; downgrade refuses while events, deltas, event/session conflicts or `cold_chain` jobs exist.
- `ledger.decide` dispatches by stated schema; `_decide_v4` requires the closed tuple and the pinned row's five v4 keys to agree (`MAPPING_INCOMPATIBLE`), then unit, periods and EV connector (`asset.asset_code` of the bound asset, read with the binding set). `postgres_evidence_ledger._persist` wraps each INSERT in a savepoint, keeps the message DO NOTHING arbiter and rereads `_REREAD_ORDER` (message, event, session); unlisted integrity errors propagate. Only accepted V3 rows enqueue the `dispatch` job.
- Reads: Postgres `records_page` family/kind filters and the seven event fields (`record_payload`, null on old rows); the legacy file read refuses the filters with 422 `FILTER_UNSUPPORTED`; `ledger_reads.CONFLICT_KINDS` counts all three conflict kinds.
- Snapshot: `gateway/snapshot.py` admits the five optional v4 binding keys all-or-none; `BindingRow.v4_mapping` serializes them only when supplied; `BindingBasis` reads absent keys as None.
- Rule 8: `$ledgerOwnedTables`, the accepted-evidence message-arbiter check (with vacuity count) and the exact `_REREAD_ORDER` line; 11 `w200` negative probes and one control in `tools/writer_guard_probes.py` (two replace the order line).
- Open: no runtime cold/EV publication profile or producer (W2-02/W2-05b); no closed tuple carries `INTERVAL_DELTA` yet, so a delta cannot be accepted until W2-05b; v4 metadata is not persisted on `signal_binding_revision` (W2-01 publishes it); read-model plain readings for the new rejection kinds are absent.

## W2-01 - cold Foundation, readiness and configured topology (built, in_review)

Branch `task/W2-01-cold-foundation` (base main `8e0af014`; design `.agent/W2-technical-design-cold.md` section 3 A-I, panel map section 6). Packet `.agent/W2-01-review-packet.md`; phase-1 handoff `.agent/W2-01-phase-1-handoff.md`.

- Backend (phase 1): `0021_w2_cold_config` no-op anchor; cold component types, node roles, media, `event`/`degC` units and the 13 `cold-*` properties in `sites/models.py`/`foundation_parsing.py`; immutable `cold-roles-1` (14 roles, EVENT value kind, role-specific state ENUMs, 300 s periodic cadence) in `sites/binding_roles.py`; `sites/cold_foundation.py` validator (runs on import and every revision) and `cold_foundation_document`; `GET /api/sites/{code}/cold/foundation?at=` (`cold_foundation_api.py`); `FoundationService.publish_topology`; W2-00 Low 2 folded (`ChannelMapping.role`, ledger `MAPPING_INCOMPATIBLE` on role drift, `BINDING_CHANNEL_ROLE_MISMATCH`). Fixtures `backend/tests/fixtures/w2/cold-00{1,2}.yaml` + `backend/conversions/cold-00{1,2}-bindings.json`.
- Frontend (phase 2): `SiteFoundationFrame` reads the Site record (`useSiteRecord`) and, for `site_type=COLDCHAIN`, renders `sites/ColdFoundationViews.tsx` (`ColdFoundationFrame`) from `sites/coldFoundationClient.ts` on the existing `/foundation`, `/foundation/readiness`, `/foundation/sld` routes; MINIGRID is unchanged. A refused Foundation read waits for the record before choosing views.
- Panels: cold-foundation 2 (equal pair), cold-readiness 4 (gateway panel nests 3 and 4), cold-sld 2; refusals are `div.page-refusal` + `ColdSkeletons` with in-panel gaps. Labels `Configured`/`Needs a source`; optional roles shown as `(optional)`.
- Title map: `cold-readiness:2` (gateway from `/gateway-health` `gateway_external_id`, else "No gateway selected") and `cold-sld:1` (Site name; no topology type is declared) in `test/v69PanelTitles.ts`.
- The cold drawing `ColdTopologyDiagram` lives in `sites/SiteSingleLineDiagram.tsx` (shell-overflow guard: SVG only in diagram modules); layered by longest path, scrolls in its own region below 760 px.
- Tests: `sites/__tests__/coldFoundation.test.tsx` (structure in stocked/missing-probe/no-version/unavailable, gaps, vocabulary, exact IDs closed, selection); loading sentence "Loading the site's cold configuration." added to `test/settled.ts`.
- Captures: `.agent/W2-01-evidence/` (9 pairs x 2 widths, 108/108 claims).
- Open: no per-source contact read (panel 3 gap), no capability read (panel 4 "Confidence is not assessed"), no part-function description (SLD panel 2), no topology type; contact is current, not as of `at`; cold binding rows carry no v4 metadata and the acquisition snapshot/`configuration_gaps` path still treats COLDCHAIN as unsupported (W2-02); the generic Foundation read still lists `SITE_TYPE_UNSUPPORTED` for cold Sites (not shown on cold views).

## W2-03 - cold assessment, episodes, Findings and the four cold screens (built, in_review)

Branch `task/W2-03-cold-assessment` (base main `e74309db`; spec `.agent/W2-03-build-spec.md` incl. `D-2026-10-18-w2-03-answers` and the commit-4 freshness amendment). Packet `.agent/W2-03-review-packet.md`; handoff `.agent/W2-03-phase-1-handoff.md`.

- Migration `0022_w2_cold_assessment`: `cold_episode`, `cold_episode_revision`, `cold_episode_evidence`, Finding `domain` (`mini_grid|cold_chain`); the fuel consequence trigger fires only for `domain='mini_grid'`.
- Pure rules `analytics/cold.py` (`cold-excursion/1`, `cold-start-response/1`, pinned vectors) and `analytics/cold_reads.py` (one `probe_fresh`, `currentness_state`, cursor codec).
- `ColdAssessmentWorker` (`analytics/assessment_worker.py`) projects assessment, episodes and cold Findings in one transaction; cold store paths in `postgres_assessment_store.py` (sole writer of assessment/episode tables, also hosts the read-only `ColdReadService`) and `postgres_finding_store.py` (`cold_apply`). Intake enqueues `cold_chain` for new accepted v4 cold-role rows (10-min bridge).
- Reads `cold_assessment_api.py`: `/api/sites/{code}/cold/{temperature,backup-chain,findings,findings/{id}}`; default window = latest selected cold window; `disclosure` seam (default allow).
- Frontend: `sites/coldAssessmentClient.ts`, `sites/ColdAssessmentViews.tsx` (`ColdPerformanceFrame`, `ColdFindingFrame`), `sites/coldAssessmentWords.ts`, `sites/coldFormat.ts`; chart `ColdTemperatureChart` in `sites/assessmentGraphics.tsx` (overflow guard). COLDCHAIN switches in `shell/SiteAnalyticsFrames.tsx` (`SitePerformanceFrame` temperature/backup, `SiteFindingFrame` by kind), `coldAssessment` prop on `App`.
- Tests: `backend/tests/test_w203_cold_{rules,migration_postgres,replay_postgres,reads_postgres}.py`, `frontend/src/sites/__tests__/coldRoutes.test.tsx`; captures `.agent/W2-03-evidence/`.
- Open: Cooling subtab and cold Finding Recommendation tab withheld (unbuilt-entry ruling); `Claim boundary` title and mock columns `Power to load`/`Load response` and "Registered simulation" sit on the W1 vocabulary list (filtered in the test, ruling requested); no production source-disclosure policy; no manual-recovery/operational-log source; Analysis link targets the existing evidence Analysis view.

## W2-04 - cold Site, evidence and unpriced consequence (built, in_review)

Branch `task/W2-04-cold-site-evidence-money` (merge-base main `54b0bece`; spec `.agent/W2-04-build-spec.md` incl. Run-5/7/8 rulings). Packet `.agent/W2-04-review-packet.md`; handoff `.agent/W2-04-phase-handoff.md`.

- Migration `0023_w2_cold_consequence`: append-only `cold_consequence_revision`, `_evidence`, `_work`, `_work_attempt`; trigger-only work on cold FindingRevision/episode revision and source-gate link; adds `batch_publication_link_scope_unique`; guarded downgrade.
- Money: `financials/cold_consequence.py` (pure rules: `PRODUCT_EXPOSURE` degC_min bounds, open episode null high + `OPEN_EPISODE_UPPER_UNKNOWN`, no price/currency), `financials/cold_recompute.py` worker (advisory lock, SUCCEEDED/FAILED attempts); sole writer `adapters/postgres_consequence_store.py`.
- Reads `cold_site_api.py` + `analytics/cold_site_reads.py`: `/api/sites/{code}/cold/{overview,evidence,evidence/analysis,financials,financial-assumptions}`; `accepted_records.total_count` via `PostgresAssessmentStore.accepted_count_on`.
- Frontend: `sites/coldSiteViews.tsx` (five routes, `SelectedWindowBar`, `SOURCE_ROWS`, `RECORD_LABEL`), `sites/coldSiteClient.ts`, `sites/w2-cold-site.css` (route-scoped 1440 widths), `shell/coldSiteRoutes.tsx`.
- Tests: `backend/tests/test_w204_cold_{migration,consequence,worker,reads}.py`, `frontend/src/sites/__tests__/coldSiteViews.test.tsx`; captures `.agent/W2-04-evidence/`.
- Open: Data sources chips overflow at the ruled widths (D1); Accepted records 423/345 px, Record cell wraps 3 lines (D2); unbound-row closed What copy (R1); Q-R9 record links unproven; `SOURCE_GATE_CHANGED` path untested; host suite and a final full backend run outstanding; W2-03 `How each limit is set` 225/120 follow-up.

## post-W6 W1-mini-Action-a - W1 mini Overview, Dispatch, Finding and Site Findings D3 fixes (built, in_review)

- Rulings `.agent/post-W6-W1-rulings.md`; packet `.agent/post-W6-W1-a-packet.md`; handoff `.agent/post-W6-W1-a-handoff.md`.
- Time: `sites/siteTime.ts` is canonical (blob identical to W2-EV 3c533f0f); `sites/findingTime.ts` reshapes it (`findingLocalTime`, `findingLocalPeriod`); shell's `usableZone`/`zoneAbbreviation`/`selectedLocalDay`/`measuredTime` in `LedgerSiteEvidence.tsx` delegate to it (extra EAT set for Asmara/Djibouti/Mogadishu kept in the wrapper).
- Overview: `SiteDetails` `siteHref` prop gives `Sites › {site} › Overview`; `WindowOverviewLinks.assets`/`sld` (optional); objective card links in `MetricCard link`; Dispatch `assessment` border only when CURRENT (`data-objective-card-tone`).
- Dispatch: `isIntervalRevision` (performanceDispatchClient) guards `WindowView`; refusal `name="not-interval"`.
- Finding frame (`CanonicalMiniFinding`): Analysis tab = root `?view=analysis`; `Open site` on all sections (`data-finding-open-site`); refused selection -> `UnavailableTab` Alternatives + `[data-alternatives-finding-unavailable]` line; Alternatives/Recommendation heading = selection title or `Finding`; no money aside; helper only on Alternatives/Recommendation.
- `SiteFinding`: props `timeZone`, `financials` (`FindingCostClient`, one exact-revision `getFindingFinancials`, priced only for same-revision CURRENT PRICED); links `alternatives`, `assumptions`, `financials`; `LocalViews` removed (implementation stays for Dispatch). `SiteFindingFrame` optional `financials` (default module client).
- `SiteFindingHistory` `timeZone`: `Time ({zone})`, local `D Mon · HH:MM`.
- `SiteFindingIndex`: `LensRow`/`ManageHref` contexts, `LensChips({hrefs})` (literal unbuilt chips), `FindingIndexLinks.manage`.
- Guards: navigation inventory has Alternatives (not Analysis); panelStructure admits the Q16 line.
- Register: R21 narrowed; R386 (error-boundary backlog), R387-R394 G1 split-offs, R395 (Q52 Finding Site tabs).
- Open: Q11/Q15 cap fallbacks depend on the capture caps table; W2-EV/W2-cold rebase over the mini Finding hunks.

## post-W6 W1-mini-Action-b - W1 mini Recommendation, Action, Financials and Site Findings table D3 fixes (built, in_review)

- Rulings `.agent/post-W6-W1-rulings.md` (W1-b 30-63) amended by `.agent/post-W6-W1-b-preflight-rulings.md`; packet `.agent/post-W6-W1-b-packet.md`; handoff `.agent/post-W6-W1-b-handoff.md`.
- Rail: `OperatorShellLayout.tsx` `railActiveLabel` (exact ruled line, pinned at `navigation-truthfulness.ps1` `$railHelper`): Finding detail paths select Findings, Action detail paths select Actions; index keeps NavLink matching.
- Site Findings table: Domain cell `Dispatch` link (UTC day of episode start; `revision` only when in `assessment.interval_assessment_revision_ids`, a type-only field in `findingIndexClient.ts`); renewable helper link.
- Financials: `FinancialsStatusBar` `Portfolio roll-up` to `/financials`; Trade-offs `Inspect technical basis` to Dispatch `?day=&view=analysis` (day-only; never a whole-window revision); assumptions footer `Return to financial overview`.
- Interpretation history (`ConsequenceHistory.tsx`): default `history_limit=3`; repeated `history_back` cursor stack (`parseHistoryBack`, `0` = first page); Previous/Next versions and Back to newest; compact rows with `Show this version`; `PriceHistory` inside closed `Price versions recorded (n)`; `siteFinancialAssumptionsHref` carries the stack; Q23 cap fallback `VersionsScroll` (`[data-consequence-history-scroll]`, max 480/900 px in `w1ux02-money.css`, cue only on overflow).
- Frames (`SiteAnalyticsFrames.tsx`): no Site tabs on Recommendation and all Action views; Finding overview/Analysis/Evidence/History (and the unknown-section state) keep tabs plus one `MOCK DEVIATION D2 (R383)` line; Action `Open site`; `/overview` alias for every Site type; unknown Action section body + `Open Action overview`; subtitle suffix only after a valid `w1ActionCode`; `ANALYSIS_HELPER_SECTION` removed.
- Action history (`SiteAction.tsx`): RESOLVED / RESOLUTION_WITHDRAWN words, unknown kind `Recorded event`; union deduplicated by resolution ID; `Latest at read time`; truncation sentence and `Show all {total} entries` only past three.
- Verification: `requirementTone(true)` = info (blue); source words once; scoped row-heading CSS in `w1f4-verification.css`; conflict KPI note `Not read: the address names conflicting selections.`; history gap shown only when distinct per panel.
- Sitework: mini scope strip `Manage in Actions` to Site `/actions` (cold/EV unchanged).
- Register: R383 (Finding Site tabs, supersedes W1-a's R395), R384 (B4-21), R385 (B4-22); `test/panelStructure.ts` admits the R383 line.
- Captures `.agent/post-W6-W1-b-recapture/` (142/142; RESOLUTION_WITHDRAWN produced by s602b `withdrawn`).
- Open: Evidence requirements (458/956 vs 450/800) and Action history Q37 (963 vs 800 at 390) exceed caps in synthetic probes with no ruled fallback (Architect); R395 marked superseded by R383; R197-R230 D3 dispositions after review.

## post-W6 W2-EV - EV Site screens D3 fixes (built, in_review)

- Rulings `.agent/post-W6-W2-EV-rulings.md` (cross-card ownership 1-8, Q1-Q31) and `.agent/post-W6-W1-rulings.md` cross-card contract; packet `.agent/post-W6-W2-EV-packet.md`; build history `.agent/post-W6-W2-EV-phase-1-handoff.md`.
- Tabs: `shell/operatorSiteTabs.tsx` optional `hrefs`/`search` override and `operatorSiteTabHref()` (R347 common mechanism; W2-cold and W5-EV-Work consume it); `evSiteRoutes.tsx` `EV_SITE_TAB_HREFS`; `sites/evSelectedWindow.ts` `selectedWindowSearch(read)`, `EvTabs` = ReactNode | (search) => ReactNode. Tabs carry the loaded read's `from`/`to`/`known_at`, never the raw URL; refused/no-window reads carry none; depth pages pass "" (W5-EV-Work).
- Bare `/sites/:id` redirects an `EV_CHARGING` Site to `/ev` (`SiteDetailFrame.tsx`), keeping the query.
- Readiness Financials/Assumptions links (`/ev/financials`, `/ev/financial-assumptions`); unique ExactReferences labels.
- Sessions: lineage link to EV Analysis at the read window; outside-outcomes line (D4 R420); Outcome column CSS; `plural()` exported from `EvAssessmentViews.tsx`.
- Finding: strip joins claim, Site, window; Bounded conclusion "Inspect claim evidence" link at the Finding's window; `FINDING_SECTION_UNAVAILABLE` common copy (cold and EV).
- Refusals (cross-card ruling 5): `RefusedHead`/`RefusedGap`/`NOT_ASSESSED` live in `EvAssessmentViews.tsx`, shared by EV Overview, Evidence, Analysis, Financials, Assumptions, Sessions, Finding and the EV Findings index: strip title "Window cannot be read" for 422, tile labels with `Not assessed`, exactly one in-panel sentence plus technical disclosure, no banner.
- EV Site views: chronology renders all accepted events (no padding); Overview cards plain labels + "View detail →"; Evidence strip "Portfolio evidence", "Review energy →", no padded rows; Analysis times in the Site zone via `sites/siteTime.ts` (exact UTC in `title`); Financials "Energy ↗" only when estimated; billing chips (D4 R421).
- `sites/siteTime.ts` canonical EAT zones incl. Asmara/Djibouti/Mogadishu; `LedgerSiteEvidence.EXTRA_EAT_ZONES` removed (W1-a closeout ruling 5).
- EV Findings index (`sites/EvFindingIndex.tsx`, `SiteFindingsFrame` EV branch, `App.tsx` `evAssessment`): 7 columns, `finding-index-row` column treatment, strip `Scoped to {site} · {n} open · window · global-list note`.
- Captures `.agent/post-W6-W2-EV-recapture/r2/` (122 app captures at dab4d15e; probes in `r2/probe/`).
- Open: cap reading for EV Findings / Accepted records (variable-cell reading passes; Accepted records Source+Value 1344 at 1440 vs 700 if Value is counted) for the Architect; EV depth refused pages raw codes (B16-01) belong to W5-EV-Work; register R420/R421 statuses update after review.

## post-W6 W2-cold - cold Site screens D3 fixes (built, in_review)

- Rulings `.agent/post-W6-W2-cold-rulings.md` (cross-card ownership 1-8, Q0-Q15); packet `.agent/post-W6-W2-cold-packet.md`; recapture `.agent/post-W6-W2-cold-recapture/`.
- Refusals (cross-card ruling 5): `refusalText` classifies `COLD_TIME_INVALID`/`COLD_WINDOW_INVALID`/`COLD_WINDOW_TOO_LONG` before the generic 422; refused Temperature/Backup use `PerformanceRefusal` (strip, `Not assessed` tiles, no banner); every cold page carries the sentence once in panel 1 and later panels say `Not assessed` (`RefusedGap repeat` in `coldSiteViews.tsx`, `REPEATED_GAP` in `ColdAssessmentViews.tsx`). Window refusals show no requested-window line.
- Cold Findings index: `ColdFindingIndex` (`ColdAssessmentViews.tsx`), COLDCHAIN branch first in `SiteFindingsFrame` (then EV, then mini), `App.tsx` `coldAssessment`; shared `LensChips`; `finding-index-row` treatment; D1 R435/R436 visible labels.
- Overview: five "View detail →" cards (Maintenance D1 R437 label in the card), strip outcomes joined from `getBackupChain` by `evidence_id`, SLD link, deduplicated limitations. `ColdSiteRoutes` gains `sld`, `workMaintenance`, `portfolioEvidence`.
- Evidence "Portfolio evidence" / "Review cooling →"; Analysis Measured/Sent/Received in the Site zone via canonical `sites/siteTime.ts` (missing zone: `UTC; Site time zone unavailable`).
- Tabs: `coldTabSearch(site, params)` feeds the W2-EV `OperatorSiteTabs` search override on cold Overview, Evidence, Performance, Findings, Finding, Financials, Health.
- Open: Work/Scenarios tab window and depth copies (W5-cold-Work); register statuses R241-R261, R435-R437 after review; Not-determined 390 wrap not producible.

## post-W6 W6-global-Work - global work list/WR D3 fixes and caps fix round (built, in_review)

Branch `task/post-W6-W6-global` (from main `821ad6bf`). Rulings `.agent/post-W6-W6-rulings.md` (Q1-Q21) and `.agent/post-W6-W6-caps-rulings.md` (1-5). Packet `.agent/post-W6-W6-packet.md`; handoff `.agent/post-W6-W6-handoff.md`.

- Backend (`fe52c862`): `site_domain` on global list rows and detail `selected`; `links.site` via `estate/evidence_money.site_home_href`; incident `linked_requests` [{label, href}] with IDs in the basis; Site incidents/maintenance fallbacks carry `known_at` only for an explicit cutoff; global Action labels use stored `ACT-` codes. Files `work/{global_index,global_detail,operational_index}.py`, `work/adapters/postgres_global_read.py`; tests `test_w601{a,b,c,e}`.
- Frontend (`5685abad`): R352-R372 D3s across `frontend/src/work/*`, R371 route `/maintenance/requests/:caseId/*`, guard rule in `tools/checks/navigation-truthfulness.ps1`.
- Caps fix round: `work/CellDisclosure.tsx` (two-line preview; visible "Show full"/"Show less" native button with `aria-expanded`/`aria-controls` and a "Show full {column} for {row}" name, overlaid at the end of line 2; shown only when the value overflows, re-measured by ResizeObserver and MutationObserver). Used for Incident Site/Severity/Owner/Findings, Corrective Work request links/Asset-site/Owner, Preventive Asset-site/Trigger/Last done/Next due/What it proves/correction, Operational Record/correction/Type/Site/By/Feeds. CSS `.cell-disclosure*`, `.global-work-clamp--two` in `work/globalWork.css`.
- R356: Operational records Feeds 125 px (fixed sum 1085, fits the 1090 px client width beside the inner vertical scrollbar); 390 px inner table minimum 1085.
- Tests: `work/__tests__/cellDisclosure.test.tsx`, `cellDisclosureStub.ts` (jsdom box-size and ResizeObserver stubs), page tests' "caps ruling 4" blocks.
- Evidence: `.agent/post-W6-W6-evidence/q15b/` (cap probe at the final SHA), `b18r/`, `b19r/` (recaptures), earlier `b18/`, `b19/`, `q15/`.
- Open: VERIFICATION_WINDOW has no writer (capture gap); cold/EV preventive and operational rows, one list with all three domains, and pending/stale global states have no producer; registry chain Q19 nodes remain open (see packet); the other 3-line title/body clamps keep their existing "Full ... text" disclosures (not changed by ruling 4).

## post-W6 W5-EV-Work - EV depth and Work D3 fixes (built, in_review)

- Branch `task/post-W6-W5-EV-work` (main `104e9c33`); rulings `.agent/post-W6-W5-rulings.md` 3-5; packet `.agent/post-W6-W5-EV-packet.md`; evidence `.agent/post-W6-W5-EV/`.
- `EvAvailability.tsx` `EvDepthRefusal` is the one refusal block for all four depth pages (RefusedHead + RefusedGap + `Read without a selected window` link for window refusals + Reload for 503/409/unreached); old `data-ev-depth-error` marker is gone. `connectorHoursText` uses `plural`, tiles show decimal `connector-h` with exact `X h Y min` in the title.
- `EvEnergy.tsx` `bridgeRows`: WITHHELD + null quantity shows metered kWh in row 1; visible `MOCK DEVIATION D1 (R06)` line. `ev_site_reads.py` `MONEY_COPY["STALE_BASIS"]` = `No stored gross tariff estimate matches the current evidence.` (wire unchanged).
- `sites/evSelectedWindow.ts` `ReportSelected` / `useReportSelectedWindow`: depth pages report the window they read; `SiteHealthFrames.tsx` EV uses `EvHealthWithTabs`; `shell/evSiteRoutes.tsx` `evWorkTabHrefs/evWorkTabSearch` feed the Work mounts (explicit valid URL window only).
- SAF `DomainActionShell`: EV `actionWindowRefusal` (evWorkPresentation.ts) refuses before any read; presentation fields `reloadLabel`, `technicalDetail`, `headings`. `DomainActionUnknownSection`: for COLDCHAIN and EV_CHARGING, `/plan /execution /history /evidence` render `This address is not served` with `Open this Action's verification`, no read, no redirect (also for a W1 ID: residual risk in the packet). Bare route still redirects (R222 `/overview` alias unchanged).
- `tools/w504_ev_work_walkthrough.py` Site Work router passes `details=` (R373 EV case-detail 503 fix). `evHealthDepth.css`: Asset column 40/30/30 at <=640 px (R470).
- Cap tooling: `.agent/post-W6-W5-EV/tools/measure-caps.mjs` (closed height, labelled 160-char DOM stress probe, refusal block, text probe), `run_ev_all.sh`, `startvite.ps1` (start Vite with Start-Process; a bare `nohup` Vite died twice). Provisional caps for unruled EV panels are in the packet; ruled ev-health 400/800 and ev-work 550/800 hold.
- Open: unknown/pending/stale EV modes, missing-meter, historical depth, authored scenario, non-Open Action states have no unmodified producer (selected-DTO tests only); backend full suite held by the coordinator. Register: R345-R350 closed, R06 noted, R470 added.

## post-W6 W5-cold-Work - cold depth and Work D3 fixes (built, in_review)

- Branch `task/post-W6-W5-cold-work`; rulings `.agent/post-W6-W5-rulings.md` 1-2; packet `.agent/post-W6-W5-cold-packet.md`; handoff `.agent/post-W6-W5-cold-handoff.md`.
- `defaultWorkWindow` (`sites/workClient.ts`) is `[today−6d, tomorrow)` UTC for every Site Work consumer (cold/EV Actions, all cases incl. mini).
- `DomainWorkWindow` requires `basis` (`actions|incidents|maintenance`) and states `DOMAIN_WORK_WINDOW_BASIS` under the control; mini cases form has none.
- `DomainActionPresentation.refusal?` maps a refusal to `{message, retry}`; cold uses `coldActionRefusal` (exact code, Retry only 503/unreached, `role="alert"`); EV absent = unchanged.
- `relatedSentence` states linked VERIFICATION_WINDOW (with record) and linked CANCELLED; cold `coldDepthStateNotice` / `scenariosStateNotice` make UNKNOWN and pending notices row/count-aware; R25 subtitle replaced.
- Cooling badges carry W4 `status-tone--*` classes (CSS `ui/primitives.css:1202`, verified). R339: the Work Actions and cases tab rows take `coldTabSearch(site, params)` (cold only; mini/EV bare); Scenarios/Health/Cooling came with W2-cold.
- Evidence `.agent/post-W6-W5-cold-recapture/` (cold b14/b15 sets, EV, mini, tab row; all pass except the baseline 6+6 state-panel pairs and forbidden/unavailable cold-action 2 each). Open: R344 VERIFICATION_WINDOW/linked CANCELLED no producer; ruled-cap stress clones not re-measured; W5-EV edits the same shared files next. Rows R334/R336-R339/R344 closed, R460/R461 added.
## post-W6 W4-mini - mini depth, mini decisions and Site Work text (built, in_review)

Branch `task/post-W6-W4-mini` (main `4d51df61` merged). Packet `.agent/post-W6-W4-packet.md`; rulings `.agent/post-W6-W4-rulings.md`, `.agent/post-W6-W4-build-rulings.md`; evidence `.agent/post-W6-W4-recapture/`. No backend change.

- Mini Performance/Scenarios/Alternatives/Opportunity: tones, chips and bars per v69 (contrast min 3.47:1 bars, 5.3:1 chips); neutral `Lens: Opportunity` (D1 R454); recurrence wording through the Q19 predicate; refused-window frame keeps every v69 panel (service, fuel, backup) and is scoped to 422 only (`miniRefusalScope.test.tsx`: 4 screens x 5 statuses).
- Refusal copy by exact code before status (Q4); Scenarios `To (EAT, included)` and Work `to (EAT, included)` via `siteLocalLastDay`/`nextIsoDate`/`siteLocalEndUtc` in `lib/siteTime.ts` (month-end and Europe/London clock-change tests).
- Site Work: Site time, plain refusals, count cause, long text; Site tab row wraps up to 760 px (R453, D2 labelled); mini Incident table bounded above 760 px (`max-height: 330px`, `[data-work-mini]`) with a hint outside the labelled `mini-scroll` region; Productive-use evaluation overflows inside a focusable labelled region.
- Capture tooling: `.agent/post-W6-W4-recapture/tools/` (`run_b_full.sh`, `run_c_cold.sh`, `run_c_ev.sh`, `mk_probe_b.py`); run each ONE at a time (overlapping launches deadlock the walkthrough DB).
- Verified at final head: vitest 3344/3344, tsc, build, check-all 11/11; captures 240/240, 168/168, 12/12, 24/24, late 130/132 (refused bad-known-at has no panels by design), cold 192/192 and 48/48, EV 144/144.
- Open: R328 (backend public-code dependency); provisional Q18 caps await the Architect; producer late gate still has retired u9c caps (Scenarios 348/391, Incidents 460); EV worstcase refused by producer; populated Alternatives (F02 future-dated), five-long-row and mini 503 are probe/component proof only.

