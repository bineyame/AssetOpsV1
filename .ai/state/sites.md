> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 11 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

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

## T027 phase 2 - mini-grid Site Overview

T027 complete; owner accepted 2026-10-03 after hands-on checks of both phases (Claude reviews ACCEPT after fix rounds; Codex retrospective pending).

Packet `archive/agent-history/T027-phase-2-review-packet.md`. In review (task-level, both phases).

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

Branch `task/S1-02-bindings-readiness` (cut from S1-01 `06ac8f5`); packet `.agent/S1-02-review-packet.md`. Decision `D-2026-10-08-s1-bindings-roles-and-snapshot` (answers in `archive/agent-history/architect-S1-02-answers-2026-10-08.md`).

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

Branch `task/S1-03-foundation-organization` (cut from S1-02 `d8dd3e9` + planning `f639990`); packet `archive/agent-history/S1-03-review-packet.md`. Decision `D-2026-10-08-s1-foundation-organization` (`archive/agent-history/architect-S1-ui-organization-2026-10-08.md`). Frontend and guards only; no backend or API change.

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
- Decisions taken under the ambiguity rule are in `archive/agent-history/S1-03-questions.md`: the narrow-shell stacking, the legacy view-route state, and the omitted legacy-only panels.
- Lab layout claims are still unmeasured. The run aborts at Lab run-setup when served by the product backend, as in S1-02.


### S1-03 fix round and S1-02 n6 (settled in code)

- `BindingService.publish` carries a binding edit through every contiguous later current period of the same binding set with unchanged bindings (Foundation-split copies), re-aligned atomically; it stops at a later independent binding change. The 201 body adds `applies_until` (null = open-ended) and `stopped_by_binding_version`; Readiness shows the end. Tests on the in-memory fake (`TestBindingEditThroughFoundationSplits`); no migration.
- `SiteFoundationFrame`: "needs an imported Site" only for `migration_required`; other failures say stored versions are unavailable.
- `navigation-truthfulness.ps1`: backtick labels, non-literal labels and a hard-coded `Changes` / `Change & effect` destination fail; page-level and panel-order tests in `siteFoundationRevision.test.tsx`.
- Phone-width shell rules are scoped to `.app-frame--operator` (set by `OperatorShellLayout`); `shell-overflow.ps1` fails an unscoped narrow `.app-frame`/`.nav-rail` rule. Lab shell unchanged; its phone layout is an open carry.
- Parts table column is "Channels" with a bound-versus-unbound legend; the SLD drawing precedes its paragraphs; the controls table names priority members.

## S5-01 - selected-window Site Overview (phases 1-2 built, slice review pending)

Branch `task/S5-01-site-overview` (LR-01 merged in, unmerged to main); handoffs `archive/agent-history/S5-01-phase-1-handoff.md`, `archive/agent-history/S5-01-phase-2-handoff.md`; packet `archive/agent-history/S5-01-review-packet.md`; owner steps `archive/agent-history/S5-01-owner-walkthrough.md`.

- Read: `site_overview/read.py` `SiteOverviewRead.read` builds `site-window-summary-1` for one UTC day over committed records (no projection table): accepted-source fingerprint fence, S4-02d `UpstreamCurrentness.window`, fenced S3 day detail, ledger context, one Finding by `D-2026-10-15-s501-finding-choice`, exact-head money with the real Performance gate. `money_state.py` is the pure no-amount precedence.
- Money: `PRICED` also requires the LR-01 seam row's `current_amount_permitted` (fail closed as `CONSEQUENCE_STALE`); the raw gate is S5's own exact read, never the seam's rewrite.
- Pin: optional `finding_id`/`finding_revision_id`; must intersect the day (`NOT_IN_SELECTED_DAY`), exact revision only while the source is closed, retained while discovery is incomplete; `previous_pin` (top-level and in `known_finding`) names why a pin is not shown. `PinNotFound` -> 404.
- Route: `site_overview/route.py` at the existing `GET /api/sites/{site}/overview` (evidence router delegates first): access 401/403, scope (typed 503 `SITE_STORE_UNAVAILABLE`), S2 409, UTC day 422s, Performance gate. Legacy `date=` becomes the midnight pair.
- Composition: one seam per process; S5 reuses the seam's consequence read and Finding store; `main.py` disposes through `app.router.on_shutdown` (FastAPI 0.141 has no `add_event_handler`).
- UI: `sites/SiteWindowOverview.tsx` (no SVG; CSS-bar timeline), `SiteOverview.tsx` S5 branch with URL `date`/pin written back from the served values, `siteOverviewClient.ts` validator; destinations from `shell/SiteDetailFrame.tsx`. Day navigation is links.
- Walkthrough: `tools/s5_overview_walkthrough.py` (`assetops_s501_owner*`, `var/s501_owner*`, ports 8925/5425, ticks env `default`); browser claims `tools/s5-overview-evidence.mjs <base> <initial|pending|eligible|stopped|closed>`.
- Open: Site Finding index (list stays unavailable); `mini:3#a/b` (S4-04/S5-02); L5 fence placement and Postgres merge/midnight cases (fakes only); production schedule thresholds make demo amounts lapse 5 minutes after a manual tick; merge and `mini:1#a/2#a/4#a` promotion held for the owner record.

## S5-02 - Finding list in Site Overview (built, slice review pending)

Branch `task/S5-02-overview-finding-list` (base main `5c1d9d42`, unmerged); packet `archive/agent-history/S5-02-review-packet.md`; owner steps `archive/agent-history/S5-02-owner-walkthrough.md`. No backend change.

- UI: `sites/OverviewFindingList.tsx` reads the S4-04 index for the Overview's served `window.start/end` (domain `mini-grid-dispatch`, `OVERVIEW_FINDING_PREVIEW_LIMIT = 2`, first page), drops older answers, renders `current-empty` / non-current status / refusal / `current-rows` (`data-overview-finding-list`), full-list link with the identical window.
- Parity: `compareParity` implements `D-2026-10-16-s502-parity` (index CURRENT+is_current with a row; card `DISCOVERED`, source open, not audit; both episodes intersect the day; Site, window, day selection seq, run, assessment record, model, input/config hashes, match pass and matched-through all present and equal; day matched) -> `same` / `different` / `not-compared` with both bases and "Reload both". Rows are never hidden.
- Composition: `shell/SiteDetailFrame.tsx` injects `findingIndex` (default client; `App` `siteFindingIndex`) and `windowLinks.findingList`; `SiteWindowOverview` shows the list only when both are supplied, else the old placeholder. `SiteOverview` has a reload counter. `SiteFindingIndex.tsx` exports `STATUS_WORDS` and `Basis`.
- Tests: `shell/__tests__/s502OverviewFindingList.test.tsx`; S5 summary builders in `shell/__tests__/s5WindowFixtures.ts`.
- Walkthrough: `tools/s502_overview_finding_list_walkthrough.py` wraps the S4-04 tool (default DB `assetops_s404_owner_s502`, `var/s404_owner_s502`, API 8952, web 5452, TLS 8953, HTTP 8954), runs the S2 Evidence comparison after `prepare` and checks every day reads `site-window-summary-1`; browser claims `tools/s502-overview-finding-list-evidence.mjs <base> <initial|late|settled|closed> <out> <s502-manifest> <s404-manifest>`.
- Open: backend still emits `finding_list: UNAVAILABLE` (validator requires it); owner record before merge and `mini:3#a/b` promotion; copy ("window" wording, status sentences) for the W1-conclusion task.

## S7-01a - Site source-health and battery boundary reads (built, slice review pending)

Branch `task/S7-01a-health-read` (base main `8b5d8137`, unmerged); packet `archive/agent-history/S7-01a-review-packet.md`; S7-01b contract `archive/agent-history/S7-01a-handoff.md`. No migration.

- Source health: `evidence/source_health.py` (schema `assetops.site-source-health` v1, rule `assetops.source-health.two-clock.v1`): contact `CURRENT|STALE|UNKNOWN` from server receipt (`freshness`), reported facts `CURRENT|OLD|UNKNOWN` from `observed_at` and clock trust (`|offset| > 5000 ms` UNTRUSTED, null UNKNOWN), queue/disk as `LAST_REPORTED`, per-source contact only when the diagnostic carries it. `check_consistent` refuses a non-snapshot isolation, duplicate/foreign/unregistered rows, row/text mismatch and a receipt after `read_at`. No derived projection: `stale_projection.applicable = false`.
- Store: `PostgresGatewayAccess.source_health_snapshot` (read only; `_health_registration`, `_health_latest` `DISTINCT ON` with the S2 order) in one REPEATABLE READ transaction. S2 `gateway_health` and its route unchanged.
- Battery: `sites/battery_boundary.py` (schema `assetops.asset-boundary` v1) over `FoundationService.read` (effective Foundation + binding set); physical condition always `UNKNOWN` (missing temperature history, measured capacity, stress history) or `NOT_CONFIGURED`; declared rating and bound channel IDs under their own labels; no SOC value.
- Routes: `source_health_api.py` `GET /api/sites/{code}/source-health`; `asset_boundary_api.py` `GET /api/sites/{code}/battery`, `GET /api/sites/{code}/assets/{asset_id}/battery`; both use `finding_api.Access`, wired in `main.py`.
- Fixture: `backend/tests/s7_health_cases.py` `HealthCases.register/publish/deliver` (`D-edge-health-cases`, one gateway per case, provisioning CLI + authenticated central ingestion; fixture SQL only for case gateway/source registration).
- Tests: `test_s7_source_health_postgres.py`, `test_s7_asset_boundary_postgres.py`.
- Open: registry `D-edge-health-cases`, `I-source-health-read`, `I-asset-boundary-read`, `I-S7-01a` stay open until review; no superseded-revision battery case (no Foundation revision writer used); accepted SOC not selected; S7-01b UI and walkthrough.

## S7-01b - Site Health and battery boundary UI (built, slice review then owner walkthrough)

Branch `task/S7-01b-health-ui` (base main `f3de235a`, unmerged); packet `archive/agent-history/S7-01b-review-packet.md`; owner steps `archive/agent-history/S7-01b-owner-walkthrough.md`. No migration.

- Backend follow-up (`D-2026-10-16-s701-clock`): `evidence/source_health.py` `CLOCK_OFFSET_LIMIT_MS` and `OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS` (both 5000, inclusive; the latter disclosed as `clock.observed_after_receipt_allowance_ms`); `summary.reason` `NO_ENABLED_GATEWAY|NO_REGISTERED_GATEWAY|null`; `reported_age` nulls `fact_age_seconds` / `reported_contact_age_seconds` under an UNTRUSTED clock or a time after `read_at`. `sites/battery_boundary.py` raises `BindingBasisInconsistent` (409 `FOUNDATION_BASIS_UNAVAILABLE`) when the binding set names another Foundation revision (review L6).
- Fixture: `s7_health_cases.HealthCases.deliver(keys)` re-posts each case's last facts; `CURRENT_CONTACT_KEYS` for the walkthrough.
- Contract: `backend/tests/fixtures/s7_health_api_contract.json` (UUIDs/digests normalised), regenerated/compared by `test_s7_health_contract_postgres.py` (`ASSETOPS_WRITE_S7_CONTRACT=1`); the frontend tests read it.
- UI: `frontend/src/sites/healthClient.ts` (typed refusals keep HTTP status/code), `SiteHealth.tsx` (status strip "Gateway contact", battery, contact, queue/storage, device contact, Technical details; `?gateway=` selection), `SiteBattery.tsx` (entry `/assets`, detail `/assets/{asset}`); links via `HealthLinksContext` from `shell/SiteHealthFrames.tsx` (substrate stays a leaf). Routes `SITE_HEALTH_ROUTE_PATH`, `SITE_ASSETS_ROUTE_PATH`, `SITE_ASSET_ROUTE_PATH`; Health tab enabled in `operatorSiteTabs.tsx` (tab inventories in three tests and `tools/layout-evidence.mjs` updated).
- Walkthrough: `tools/s701_health_walkthrough.py prepare|serve|links|deliver|attest|drop` (KOBO-001 bindings before case gateways; KOBO-002 without battery); evidence `tools/s701-health-evidence.mjs` (40 claims at 1440/390).
- Open: no `STALE_PROJECTION` state (read has none); accepted SOC not shown; positive `asset:3#b`, warranty/replacement stay unmapped; plain-language and visual polish carry to the W1-conclusion fidelity pass; registry `I-source-health-ui`, `I-asset-boundary-ui`, `health:2#a`, `asset:3#a` close only after review and owner walkthrough.

## post-W6 W1-mini-Action-a - W1 mini Overview, Dispatch, Finding and Site Findings D3 fixes (built, in_review)

- Rulings `archive/agent-history/post-W6-W1-rulings.md`; packet `archive/agent-history/post-W6-W1-a-packet.md`; handoff `archive/agent-history/post-W6-W1-a-handoff.md`.
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

- Rulings `archive/agent-history/post-W6-W1-rulings.md` (W1-b 30-63) amended by `archive/agent-history/post-W6-W1-b-preflight-rulings.md`; packet `archive/agent-history/post-W6-W1-b-packet.md`; handoff `archive/agent-history/post-W6-W1-b-handoff.md`.
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

## post-W6 W4-mini - mini depth, mini decisions and Site Work text (built, in_review)

Branch `task/post-W6-W4-mini` (main `4d51df61` merged). Packet `archive/agent-history/post-W6-W4-packet.md`; rulings `archive/agent-history/post-W6-W4-rulings.md`, `archive/agent-history/post-W6-W4-build-rulings.md`; evidence `.agent/post-W6-W4-recapture/`. No backend change.

- Mini Performance/Scenarios/Alternatives/Opportunity: tones, chips and bars per v69 (contrast min 3.47:1 bars, 5.3:1 chips); neutral `Lens: Opportunity` (D1 R454); recurrence wording through the Q19 predicate; refused-window frame keeps every v69 panel (service, fuel, backup) and is scoped to 422 only (`miniRefusalScope.test.tsx`: 4 screens x 5 statuses).
- Refusal copy by exact code before status (Q4); Scenarios `To (EAT, included)` and Work `to (EAT, included)` via `siteLocalLastDay`/`nextIsoDate`/`siteLocalEndUtc` in `lib/siteTime.ts` (month-end and Europe/London clock-change tests).
- Site Work: Site time, plain refusals, count cause, long text; Site tab row wraps up to 760 px (R453, D2 labelled); mini Incident table bounded above 760 px (`max-height: 330px`, `[data-work-mini]`) with a hint outside the labelled `mini-scroll` region; Productive-use evaluation overflows inside a focusable labelled region.
- Capture tooling: `.agent/post-W6-W4-recapture/tools/` (`run_b_full.sh`, `run_c_cold.sh`, `run_c_ev.sh`, `mk_probe_b.py`); run each ONE at a time (overlapping launches deadlock the walkthrough DB).
- Verified at final head: vitest 3344/3344, tsc, build, check-all 11/11; captures 240/240, 168/168, 12/12, 24/24, late 130/132 (refused bad-known-at has no panels by design), cold 192/192 and 48/48, EV 144/144.
- Open: R328 (backend public-code dependency); provisional Q18 caps await the Architect; producer late gate still has retired u9c caps (Scenarios 348/391, Incidents 460); EV worstcase refused by producer; populated Alternatives (F02 future-dated), five-long-row and mini 503 are probe/component proof only.


