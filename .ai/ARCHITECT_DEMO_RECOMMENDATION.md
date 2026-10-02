# Architect Recommendation: Demo-Led Navigation, Content And Sequencing

**Status: Final version for owner review, 2026-10-02.** This is a
recommendation input, not the roadmap. It does not change `tasks/README.md`,
any task file, `.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md`, `.ai/ARCHITECTURE.md`
or `Docs/mini-grid-demo-architecture-and-roadmap.md`. Once the owner approves
it, the Architect briefs the Planner, and the Planner applies it to the queue
and the planning records. Everything below that touches the queue is a
**proposal for the Planner**, and items marked **[Planner verifies]** must be
checked against the task files, not assumed.

It answers the owner's request of 2026-10-02 (saved verbatim at
`.agent/architect-demo-roadmap-request.md` on
`task/T025h-picker-compatibility`). It carries the owner's review of the same
day: the owner's rules are quoted verbatim where the owner set them, and the
D1-D8 dispositions are in section 8 as the owner worded them.

Produced by Claude as Architect under the ROLE_CONFIG exception in force until
the Codex reset on 2026-10-03 21:23. A later reader may send any judgement here
back to Codex. A Planner pass that runs after that time is Codex-bound and will
inherit this document as Claude-authored input.

Sources: v6.9 canonical screens (sections 2, 4-8), roadmap sections 3-5, 8 and
13, `.ai/PRODUCT.md`, `.ai/ARCHITECTURE.md` (Shells And Navigation, Shared
Presentation Substrate, Presentation Honesty, Domain Reuse Boundary),
`.ai/DECISIONS.md` (2026-09-13 and 2026-09-17 navigation entries),
`.ai/FEATURE_MAP.md`, `tasks/README.md`, the T027-T036 task files, T025h (on
its branch), CODE_STATE T011A/T012/T026, and the backlog items carried from
T026.

**Built state these proposals start from.** A is accepted. Lab cockpit L1a-L1c
are built. Template v3 and T026's dispatch evidence are merged. That evidence
(capability signals, policy and override records, one gap, one held
publication) is **staged, never committed**. The operator shell has two
navigation items (`Operator home`, `Sites`). A Site has two tab destinations
(Overview showing identity only, and Foundation) and six tabs labelled in
place; Foundation's `Readiness` subtab is also labelled in place. There are no
Findings, Financials, Actions or accepted history yet, so **every
client-visible surface the demo needs is still ahead of us**. That is why
sequencing now has more effect on demo value than anything else.

---

## 1. Executive Recommendation

**Navigation philosophy.** The owner's principle: **"Preserve v6.9's grammar
unless the demo/product reasoning reveals a genuine ownership problem."** v6.9
is the reference, not a frozen end-state. Its ten root classes, its grouped
menu, its eight Site tabs, the "at most one subtab row" invariant and the
scoped-index rule (v6.9 sections 2.1-2.4) already separate the canonical
object, the menu item, the contextual tab and the drill-down. What they lack is
an order of prominence, and this recommendation supplies it.

"Genuine ownership problem" is given a test so it cannot become a loophole for
demo preferences (section 2.2): a place keeps its slot only if it owns
something no other place shows, and an exception must name what is lost by
removing it and what already duplicates it. Every exception gets a
`DECISIONS.md` entry. Global Financials is the one candidate so far, and it is
still open (section 2.5).

**One truthfulness rule governs the rail and the tabs.** A navigation item or a
tab appears only once a truthful surface exists behind it. For tabs this is the
owner's rule: **"The canonical tab set defines ownership and future placement;
the rendered tab set contains only meaningful destinations unless absence
itself communicates something useful."** It is applied **per capability, not
per site**: once this build has a truthful surface for an aspect, its tab
renders on every site it applies to, and a site that lacks the evidence shows
the gap inside the tab. Adopting this retires "labelled in place" in operator
views, which needs a decision record and an `ARCHITECTURE.md` edit and lands in
T027 phase 1 (section 2.4).

**Root menu.** Target: v6.9's grouped menu, OPERATE (Portfolio, Sites,
Assets), INTELLIGENCE (Findings), WORK (Actions, Incidents, Maintenance),
ASSURANCE (Evidence), BUSINESS (Financials, Reports P1). The client sees it
filtered to live items, in canonical order, with a group header only over a
live item: Sites now; Findings from T028; Actions from T034; Portfolio as the
landing page at Portfolio-lite; Assets at T033; global Evidence at T036 if it
passes the ownership test. Global Financials, Incidents, Maintenance and
Reports stay out of the demo rail. Simulator Lab stays a separate gated
workspace, reached from the utility menu and opened last as proof.

**Site structure.** The canonical eight tabs define ownership; the rendered set
grows from three at T027 to eight at T033, always in canonical order. Three
tiers:

- **Hero tabs:** Overview, Performance (with domain subtabs) and Financials.
- **Trust tab:** Evidence, site-owned: source health and coverage from T027,
  claim readiness from T028.
- **Supporting tabs:** Foundation (with Changes as the record of an
  intervention), Findings and Work (scoped indexes), and Health (once
  lifecycle evidence exists).

**Domain seam.** One static **`DomainPresentationProfile`** per archetype,
mini-grid only for now. It is substrate data keyed by the Site's `site_type`,
and it owns presentation only: overview domains, performance views, health
emphasis, labels and vocabulary, consequence presentation. Backend and domain
modules stay authoritative for which Findings exist, what evidence an analytic
requires, what verification rules exist, and the consequence categories. The
profile references backend capabilities through a named contract born in T028,
the **analytic capability declaration** (section 4.3). Cold-chain and
e-mobility are tested on paper, not in code. This is not a pack framework.

**Major sequencing recommendations:**

1. Keep the spine: T027 -> T028 -> T029 -> T029A -> T034.
2. Rescope each spine slice so it lands a canonical surface: Site > Evidence
   and the Overview frame at T027; Dispatch, Finding detail and the Findings
   root at T028; Site Financials at T029; Action, Verification and Foundation >
   Changes at T034.
3. **Protect demo point 2** (T028-T029, the expert checkpoint that reshapes
   everything after it). Anything not on its journey can move to a thin
   follow-on slice. Phase T027 and T028.
4. Add a **Portfolio-lite slice right after T034**, sized as a real slice, so
   the strong product demo opens the way the final one does.
5. After that, add each further story as one Site that joins the Portfolio.
   The order is the owner's priority intent (opportunity before fuel if
   dependency cost is low; service before battery unless feedback says
   otherwise), set exactly by the Planner after a dependency check.
6. **Every demo point ships with an idempotent, rehearsed seed**, owned by the
   slice that creates the point.
7. Park T025h until after T029. It is developer ergonomics a client never sees.

---

## 2. Navigation And Root Context

### 2.1 Proposed client-facing tree

The tag after each item says when it becomes a truthful destination. Items
marked "not demo" stay canonical and may arrive later; they are not removed
from the model. Site tabs are listed in v6.9's canonical order (`Overview |
Foundation | Health | Performance | Findings | Work | Financials | Evidence`,
v6.9 line 464); new tabs insert in that order, so a returning audience finds
earlier tabs where they left them.

```
OPERATOR SHELL (left rail; grouped; highlights the root object's class)
|
|-- [OPERATE] Portfolio .. root; landing page        [Portfolio-lite, after T034]
|     lenses: Attention | Opportunities | Evidence gaps (filters, not tabs)
|     value column = the cross-site financial roll-up
|     evidence-gap column = the cross-site Evidence roll-up (until T036)
|
|-- [OPERATE] Sites ...... root; index               [built; assessment columns
|     |                                               at T027-T028 or follow-on]
|     `-- Site (root object)
|           Overview ........ HERO, site-owned        [T027]
|           Foundation ...... supporting, site-owned  [built; Changes at T034]
|           |   Definition | Topology | Controls (+ Changes at T034)
|           |   (Readiness not rendered; claim readiness lives on Evidence)
|           Health .......... supporting              [T033]
|           Performance ..... HERO, site-owned        [T028: Dispatch]
|           |   mini-grid: Dispatch | Service | Renewable | Fuel | Backup
|           |   (each subtab appears when its analytic exists in the build)
|           Findings ........ scoped index            [T028]
|           Work ............ scoped index            [T034: Actions, no subtab row]
|           Financials ...... HERO, site-owned        [T029]
|           |   Overview | Assumptions (later: Drivers | Scenarios)
|           Evidence ........ TRUST, site-owned       [T027: source health + coverage]
|               + capability readiness table above it (T028+)
|               record inspector = drill-down from a source or signal row
|
|-- [OPERATE] Assets ..... root; thin index          [T033, first Asset Detail]
|     `-- Asset: Battery > Health (others when evidenced)
|
|-- [INTELLIGENCE] Findings  root; global index      [T028]
|     lenses: All | Opportunities | Risks | Awaiting verification
|     `-- Finding (root object)
|           Overview | Evidence | Alternatives          [T028]
|           + Recommendation | History                 [T034]
|           (claim evidence drawer opens from any claim; never changes root)
|
|-- [WORK] Actions ....... root; global index        [T034]
|     `-- Action (root object)
|           canonical: Overview | Plan | Execution | Evidence | Verification | History
|           rendered at T034: Overview | Verification (others when they have content)
|
|-- [WORK] Incidents, Maintenance                    [not demo; arrive with a pilot]
|-- [ASSURANCE] Evidence . cross-site roll-up         [T036, if it passes the ownership test]
|-- [BUSINESS] Financials  cross-site roll-up         [open owner question; not demo]
|-- [BUSINESS] Reports ... P1                         [not demo; deferred]

UTILITY MENU
`-- Open Simulator Lab -> SIMULATOR LAB WORKSPACE (separate shell, gated)
      run cockpit, stage inspector, truth vs AssetOps evidence (proof only)
```

`Operator home` is a T002 placeholder. It goes when Sites becomes the landing
page, and Sites hands the landing to Portfolio when Portfolio-lite ships.
While Sites is the first screen, its assessment columns are what make it ask
"which site needs attention, and how sure are we?" instead of listing names.
Their timing is a point-2 protection question (section 6.2).

**Root rail by milestone:**

| Milestone | Client rail |
| --- | --- |
| T027 | Sites (one item, no header) |
| T028-T029A | OPERATE: Sites; INTELLIGENCE: Findings |
| T034 | OPERATE: Sites; INTELLIGENCE: Findings; WORK: Actions |
| Portfolio-lite onward | OPERATE: Portfolio, Sites; INTELLIGENCE: Findings; WORK: Actions |
| T033 | OPERATE gains Assets after Sites |
| T036 | ASSURANCE: Evidence joins if it passes the ownership test |

Headers start at T028, because "INTELLIGENCE: Findings" is the first moment the
rail can state the product's category. Several groups hold one item for a long
time (OPERATE over Sites, INTELLIGENCE over Findings); the layout check should
cover a one-item group so the header does not look heavy.

**Why the grouped menu is the right target.** Its headers read as the
product's causal chain: Operate -> Intelligence -> Work -> Assurance ->
Business follows v6.9's backbone (evidence -> finding -> action ->
verification -> financial impact). A flat list of ten nouns reads as modules;
the grouped list reads as a loop from operations to money. INTELLIGENCE and
ASSURANCE name the two things a SCADA view or CMMS lacks. Each later class
already has a fixed home, so adding one never moves what a client learned. And
v6.9 2.3's rule that Site > Work mirrors the WORK group only makes sense if the
group is visible.

**Why the demo shows it filtered.** Seven of the ten items have no surface yet,
and four (Incidents, Maintenance, global Financials, Reports) have none planned
before T036. A WORK group showing `Actions | Incidents | Maintenance` reads as
a CMMS, and an empty Incidents page in front of a client is the fastest way to
make it one. A BUSINESS group over a thin Financials page would undersell the
money story, which lives on Site > Financials and the Finding panel, where its
causal basis is visible.

### 2.2 The five kinds of place, and the ownership test

| Kind | Members | Rule |
| --- | --- | --- |
| Root navigation | OPERATE: Portfolio, Sites, (Assets); INTELLIGENCE: Findings; WORK: Actions; (ASSURANCE: Evidence at T036) | A class the user manages across sites, or reaches as a decision object. It appears only when its root object has a real detail page, under its canonical group header, in canonical order. |
| Contextual tabs | Site's eight; Finding's five; Action's six (canonical sets) | Aspects of one root object. The canonical set defines ownership and future placement; the rendered set holds only meaningful destinations, decided per capability (2.4). |
| Scoped indexes | Site > Findings, Site > Work | A filter over a global class, with no KPI strip and no status model of its own. Clicking a row changes the root. |
| First-class detail roots | Finding, Action, Asset (Incident, Maintenance later) | Starting work on one of these changes the root and the rail highlight. The breadcrumb keeps the Site so Back is predictable. |
| Technical workspace | Simulator Lab | A separate shell behind the gate. In the demo it is proof, never navigation. |

**The ownership test for grammar exceptions.** v6.9 2.3 already tests site
tabs with "remove the tab and lose nothing except a filter". Generalised:

- a place in the grammar keeps its slot only if it **owns** something that no
  other place shows: objects, a workflow, or site-owned content;
- a proposed exception must name what would be lost by removing or moving the
  item, and what currently duplicates it;
- every exception gets a `DECISIONS.md` entry, and any task that cites v6.9
  screen text where a decision has overridden it cites that decision too, so
  v6.9 is not used as an acceptance oracle against an owner ruling.

**How each concept the request names is placed:**

- **Portfolio.** Root, and the landing page once at least three sites have
  different stories. Its job is prioritisation, not monitoring.
- **Sites.** Root. The operator's anchor; already built.
- **Assets.** Root in OPERATE after Sites, but late and with a thin index. The
  navigation invariant needs Assets in the rail once Battery > Health is a root
  page (v6.9 8.27). A rich inventory is deferred (roadmap section 8). Until
  T033, asset condition has no rendered surface.
- **Findings.** Root from T028. A Finding is the product's unit of value;
  hiding it inside a Site would bury the decision object. The model is v6.9
  2.3's: a global index, a scoped Site filter, and Finding detail as its own
  root. **Opportunities are a lens on Findings, not a new class.**
- **Actions.** Root from T034. An accepted change, its owner and its
  verification outlive the Finding view. "Finding resolved" and "Action
  verified" are the two halves of the closed loop, and each needs its place.
- **Incidents and Maintenance.** Canonical, not demo material. The first
  verification story is a policy change, which is an Action. T035's backup
  failure stands as a Finding without an incident subsystem (T035 rules that
  subsystem out). Maintenance should arrive when a pilot needs work requests.
- **Evidence.** Primarily **site-owned** (Site > Evidence), plus the
  **claim-specific** evidence drawer on every material number. The cross-site
  roll-up is Portfolio's evidence-gap column until T036, when six sites have
  different claim ceilings (Genda's fuel records, Bahir's backup chain).
  Global Evidence then joins the rail only if it passes the ownership test
  explicitly. It should: cross-site instrumentation prioritisation is a
  decision workflow that creates Actions (v6.9 8.8, 8.35), which nothing else
  owns.
- **Financials.** Primarily **site-owned** (Site > Financials, the bridge from
  technical Findings to money), quoted on Finding detail and the Overview. The
  cross-site roll-up is Portfolio's value column. Global Financials stays out
  of the demo rail. Whether it stays a BUSINESS root at all is open (2.5).
- **Work.** Site > Work is a scoped index mirroring the WORK group (2.4).
- **Simulator Lab.** A separate workspace. Settled by `ARCHITECTURE.md` Shells
  And Navigation and the 2026-09-13 decisions.

### 2.3 First-class objects versus scoped views

| Concept | Global | Contextual | Detail root |
| --- | --- | --- | --- |
| Findings | Findings index with lenses (T028) | Site > Findings, a filter (T028) | Finding (T028) |
| Work | Actions index (T034) | Site > Work, Actions only, no subtab row while WORK has one item | Action (T034) |
| Evidence | Portfolio evidence-gap column; global Evidence at T036 if earned | Site > Evidence, site-owned content | none; the drawer opens from any claim and never changes root |
| Financials | Portfolio value column; global page open (2.5) | Site > Financials, site-owned content | none; consequence panel on the Finding |

### 2.4 Rendered tabs: the rule, its scope, and what it retires

**The rule (owner's wording):** "The canonical tab set defines ownership and
future placement; the rendered tab set contains only meaningful destinations
unless absence itself communicates something useful."

**It is decided per capability, not per site.** "Meaningful destination" means
this build has a truthful surface for this aspect. It does not mean this site
has data for it. Deciding per site would make tab bars differ between sites in
the same Portfolio session (Arsi with a Health tab, Kobo without), and it would
hide the very tab that should say "we cannot assess battery condition here".

**That is where "absence communicates" belongs.** Once a capability exists in
the build, its tab renders on every applicable site, and a site without the
evidence shows the gap inside the tab. In-page gaps (a coverage gap on Site >
Evidence, a domain card without an assessment) are not an exception to the tab
rule. They are ordinary claim discipline ("Unknown, never Healthy"; T027's
"Coverage gap, no fabricated value").

**Applicability is a separate filter from rendering.** Site > Health does not
apply to a cold room's battery, for example. Applicability comes from the
presentation profile and the backend capability declaration (4.3), never from
data presence.

**Rendered Site tabs by milestone** (one canonical inventory filtered by
capability, never per-milestone lists; shown in canonical order):

| Milestone | Site tabs rendered |
| --- | --- |
| T027 | 3: Overview, Foundation, Evidence |
| T028 | 5: Overview, Foundation, Performance, Findings, Evidence |
| T029 | 6: + Financials |
| T034 | 7: + Work |
| T033 | 8: + Health (between Foundation and Performance) |

Within one demo the set is stable. Growth is visible only to a returning
audience (expert at point 2, then point 3), and to them it reads as progress,
which is honest. `frontend/src/shell/operatorSiteTabs.tsx` already keeps one
inventory, so this is a change to its filter, not its structure.

**Other contextual tab sets:**

- Finding detail at T028: Overview | Evidence | Alternatives. Recommendation
  and History appear at T034.
- Action at T034: Overview | Verification. Plan, Execution, Evidence and
  History appear when they have content.
- Foundation: Definition | Topology | Controls, plus Changes at T034.
  Readiness is not rendered: configuration readiness has no source contract,
  and claim readiness lands on Site > Evidence only, so the same readiness
  statement never appears in two places.
- **Site > Work:** while the WORK group holds only Actions, Site > Work renders
  the Actions index with **no subtab row**. The row appears when a second WORK
  class goes live. This still satisfies v6.9 2.3's "mirrors the WORK nav group
  exactly" and the "at most one subtab row" invariant; a row with one entry is
  noise.

**What this retires, and where it lands.** "Labelled in place" is one of the
three Presentation Honesty treatments in `.ai/ARCHITECTURE.md`. The 2026-09-13
decision adopted it from v6.9's own "Warranty (P1)" usage, and the 2026-09-17
Site-tab decision applied it to six Site tabs and Foundation > Readiness.
`tools/checks/navigation-truthfulness.ps1` enforces it, and
`operatorSiteTabs.tsx` (with `FOUNDATION_SUBTABS` and its tests) ships it.
The owner's rule is the better rule, but without a record an Implementer
following `ARCHITECTURE.md` and a Reviewer running the check would both rule
against it. So:

- **Planner step 0:** a `DECISIONS.md` entry and an `ARCHITECTURE.md`
  Presentation Honesty edit. **Recommended form: "labelled in place" is not
  used in operator views**; the other two treatments (not rendered; disabled
  with a stated reason) stand unchanged. Whether to narrow it like this or
  retire it everywhere is the owner's call (section 9).
- **T027 phase 1:** remove the six Site labels and the Readiness label, change
  the filter, and update the check and its tests. It is small, and T027 makes
  Evidence a destination anyway.

### 2.5 Global Financials: still open

**Recommendation, not a decision:** treat the cross-site financial roll-up as
part of Portfolio for now, and promote it to a BUSINESS root only when a
portfolio-owned financial object exists. Decide after T036; it is on no demo
path.

Under the ownership test, a global Financials root owns, on today's content,
only aggregation: v6.9 8.9 gives it cross-site consequence lines by
non-overlapping category, each clicking through to Site Financials or a
Finding, and "the global page never re-derives site bridges". Portfolio Value
& Operations already carries that as its value column.

**What would make it pass:** a portfolio-owned financial object. The most
likely one is a shared assumption set: a realistic operator has one diesel
contract across sites. If BusinessContext becomes portfolio-shared, with its
own versions and effective times, a global Financials root owns it. Budgets or
exportable financial reports would do the same. **T029 decides BusinessContext
scope** (its spec does not say per site or portfolio-wide). Site-scoped is
recommended, because the live price change on Site > Financials > Assumptions
is the point-2 demo moment; "shared or portfolio assumption sets" is recorded
as the trigger to revisit this question.

| Option | Cost |
| --- | --- |
| BUSINESS root (v6.9 as written) | No grammar change. One more page whose only content duplicates Portfolio's value column, so two surfaces must apply identical non-overlap and basis rules, with consistency tests between them. A BUSINESS group with one weak item (Reports is P1). Clients see a "finance module" that adds nothing. |
| Portfolio view or section | A recorded deviation from v6.9 (DECISIONS entry, note on the canonical reference). It cannot be a lens on Portfolio's subtab row (v6.1 keeps that row to interpretation lenses), so it is a view or section. A finance persona loses an obvious menu entry. Promoting it later is a route and navigation move, cheap if the view has a stable address from the start. |

---

## 3. Page Hierarchy And Content

Each page has a role, the decision it helps the user make, and an information
hierarchy. Widget-level layout belongs to v6.9 section 8 and the Planner.

### Portfolio Value & Operations (the opening screen)

- **Decision:** where management attention and capital go first.
- **Hierarchy:**
  1. One sentence of scope: window, number of sites, mode (SIMULATED stated as
     provenance).
  2. **Ranked Findings across sites.** Each row: site, bounded claim, a value
     or consequence with its basis (measured, modelled or scenario),
     confidence, action state. OPEX, service, asset and opportunity figures
     stay separate.
  3. Three lenses: attention, opportunities, evidence gaps.
  4. "What changed": verified, reopened, or closed without proof.
- **Intelligence, not dashboard:** the ranking unit is a Finding with its
  consequence, not a site's alarm count. No figure is totalled across
  consequence types, and a site that is healthy on adequate evidence is
  visibly different from a site we cannot assess.
- **Leads to:** a Finding (root changes), or a Site.

### Site Overview ("Is this site meeting its operating objective, and what matters now?")

- **Decision:** which aspect of this site to open.
- **Hierarchy:**
  1. The objective strip: site assessment, service delivered, confidence.
  2. **One assessment card per domain.** The profile decides which cards exist
     and their order (mini-grid: Service, Dispatch, Battery, Fuel, Renewable).
     The **state** on each card is backend output, never the profile's.
     - **At T027, no analytic exists:** cards show measured metrics, their
       coverage, and a neutral **"No assessment yet"**.
     - **From T028:** a card whose analytic exists shows an assessment word and
       a one-line reason.
     - **"Unknown"** is reserved for an assessment that exists but cannot
       conclude, or a site with no data in the window (v6.9 8.2), with the
       missing evidence named.
  3. The **selected-day energy timeline** (demand, PV, generator, SOC) as
     context, not as a status source.
  4. Top Findings, each linking to the Performance subtab that produced it.
  5. The compact value of the leading consequence (from T029).
- **Not here:** device lists, gateway status or raw series. Those belong to
  Evidence and Foundation.

### Site Performance (domain subtabs; Dispatch is the hero)

- **Dispatch.** Decision: was the generator needed? A timeline of intervals
  classified Necessary, Candidate avoidable or Indeterminate (grey). Selecting
  an interval shows the binding constraint or the missing evidence, then leads
  to its Finding. This is where a domain expert decides whether the product
  understands their site, so it shows policy, reserve and capability at the
  interval's own time.
- **Renewable.** Decision: is capacity being wasted that could be used?
  Recurring headroom windows after demand, reserve, storage and policy are
  checked. "Evaluate intervention" opens the paired comparison (T032) as a
  drill-down, not a tab.
- **Fuel, Service and Backup** follow v6.9 8.20-8.24 when their slices land.
  Fuel shows an unexplained residual with uncertainty and never an
  accusation. Service shows unserved energy and coverage. Backup shows the
  event chain with missing links stated.

### Finding Detail (the trust-defining page)

- **Decision:** do I believe this, and what would I do about it?
- **Overview tab hierarchy:**
  1. The bounded claim in one sentence.
  2. Observed facts, kept separate from inference.
  3. Confidence and its basis, kept separate from coverage.
  4. The claim ceiling ("13 min capability gap limits this").
  5. The consequence: technical quantity first, money second.
  6. The next step.
- **Other tabs:** Evidence (claim-by-claim list that opens the drawer);
  Alternatives (competing explanations, and why each was ruled out or left
  open); Recommendation and History from T034 (the change and its declared
  success criterion; assessment revisions, verification and reopening).

### Financial Consequence (Finding panel plus Site > Financials)

- **Decision:** does this matter enough to act on, under *our* assumptions?
- **Hierarchy:** technical quantity (runtime hours, litres range); assumptions
  in use (versioned fuel price, maintenance accrual); money range with basis
  and a window or extrapolation label; link back to the source Finding.
- **The demo moment:** change the price and the money moves, while physics and
  confidence stay where they are.
- Financial pages carry no assessment status (v6.9 8.36).

### Productive-Use Opportunity (Renewable plus the paired comparison)

- **Decision:** is it worth trialling a productive load in that window?
- **Hierarchy:** the physical headroom (when, how much, how often, what
  constrains it); the candidate load (owner's choice, roadmap 12.2); baseline
  against intervention (PV use, curtailment, diesel, energy served, revenue
  labelled as scenario); the explicit limit that market demand is not
  established.

### Asset Lifecycle / Health

- **Site > Health:** is any asset on a harmful trajectory? Two separate blocks,
  physical condition and source health. A gateway being Online never stands in
  for a battery being Healthy.
- **Battery > Health** (Asset root): current evidenced state, stress
  recurrence against a reference band, bounded replacement exposure. Never a
  failure date.

### Action / Verification (the closed-loop differentiator)

- **Decision:** did the change work without unacceptable side effects?
- **Hierarchy:**
  1. Managed-object header: owner, due, state, source Finding, success
     criterion.
  2. **Declared target and guardrails, shown together.**
  3. Before window against post-action window, with comparability limits.
  4. Outcome: Verified, Ineffective or Inconclusive, with reasons.
  5. What happened to the Finding: resolved, or kept open.
- **Wording:** "Completed" and "Verified" are visibly different words. That
  difference is the CMMS contrast the demo makes.
- **Composition:** the accepted change also appears on Foundation > Changes as
  the record of the product decision. In a simulated site the world's actual
  change is evidenced by post-action configuration evidence through the normal
  path (T034 AC4); Changes links to that evidence and does not stand in for it.

### Evidence (Site > Evidence, the record inspector, and the claim drawer)

Site > Evidence holds two different things, in the owner's words:

- **A. "what records have been accepted and their quality/coverage".**
- **B. "what claims AssetOps can make given those records".**

**At T027 (A only), the tab body is v6.9 8.35's lower section:** source and
connector health per source (data quality, not asset health), per-signal
coverage for the selected window, and the mapping and configuration basis.
Coverage here names the signals the Overview metrics need, not signals an
analytic requires, because no analytic exists yet. It makes no claim about
what AssetOps can conclude.

**The record inspector is a drill-down, not the tab body.** It opens from a
source or signal row and from the Overview metrics' evidence links (T027
AC11), and shows source, device, signal, mapping or config version, quality,
original and normalised values and the three timestamps (source, publication,
receipt; T027 AC12). Opening it does not change the root. Because it is not
the tab body, T028 never displaces it, T028's claim drawer reuses it, and
T030 AC17's "separate source-record inspector" for delivery and hand-dip
records has a stable home to extend.

**From T028 (B), a capability table is added above the source-health
section:** capability readiness, the claim ceiling and the missing evidence
for each analytic claim. It is the backend's analytic capability declaration
(4.3) scored against accepted coverage, so it has exactly one row per analytic
that exists: at T028, one row (dispatch). Full, Limited or None is its form,
and nothing in it appears before a real analytic claim exists for it to
qualify. T027 must not "pretend it already knows rich claim readiness before a
real claim exists" (owner).

**The drawer** answers why a particular number is true: window, evidence
references, coverage, configuration at the time, mapping and algorithm
versions. "The drawer is claim-specific lineage; the Evidence page is
capability readiness" (v6.9 8.37). Opening it never changes the root.

The page therefore grows in the shape v6.9 already drew, and nothing moves.

### Simulator Proof (Lab, last)

- **Decision:** is the analytic inferring, or reading a script?
- **Hierarchy:** private physical truth beside what was reported; staged
  envelopes, then committed ones; truth against the product's conclusion by
  run, window and evidence reference, including one case where the claim was
  limited.
- **What it shows the client:** the simulator was not the source of the
  answer.

---

## 4. Domain-Aware Product Structure

### 4.1 What is common and what changes

| Common shell (never branches on domain) | Changes by domain | Owner of the change |
| --- | --- | --- |
| Root navigation, Site tab set, subtab-row invariant | List and order of Performance subtabs | Profile |
| Finding, Action, Verification objects; status vocabulary; claim discipline | Which Finding types exist and what each may claim | **Backend** (profile labels and orders them) |
| Evidence drawer, record inspector, capability coverage, the three timestamps | Evidence a domain's claims need | **Backend** (profile may reference) |
| Financial bridge (quantity x versioned assumption; no overlapping totals) | Consequence categories (fuel, energy, service, product exposure, asset) | **Backend**, with the financial model; profile owns their presentation |
| Site Overview frame (objective strip, cards, timeline, top Findings) | Objective sentence, which domain cards exist and their order, timeline series | Profile (card **state** is backend) |
| Health frame (physical condition apart from source health) | Which assets are emphasised | Profile |
| Verification frame (target plus guardrails, comparable windows) | Target and guardrail rules per intervention type | **Backend** (T034's versioned rule set); profile presents them |

Consequence categories are backend-owned because the no-double-counting rule
depends on them: v6.9 says "only non-overlapping categories aggregate", and
T030 AC13 forbids counting modelled generator use as both dispatch consequence
and fuel loss.

### 4.2 Mini-grid and cold-chain side by side

| Concern | Mini-grid | Cold-chain (cold room) |
| --- | --- | --- |
| Objective | Serve required load at the lowest diesel cost and asset wear | Keep product within its temperature policy through power, cooling and operational disturbances |
| Overview domains | Service, Dispatch, Battery, Fuel, Renewable | Temperature, Cooling, Backup, Maintenance, Evidence; product exposure is a **consequence chip**, not a card (v6.9 8.28) |
| Performance | Dispatch, Service, Renewable, Fuel, Backup | Temperature, Cooling, Backup |
| Health emphasis | Battery, genset, PV inverter, gateway | Compressor, backup assets, instrumentation |
| Typical Findings | Candidate avoidable runtime; fuel residual; renewable headroom; reserve breaches; backup start failure | Temperature excursion; cooling-recovery degradation; backup response failure |
| Consequence | Fuel and maintenance OPEX, unserved energy, replacement exposure, scenario revenue | Energy cost, product exposure (scenario, never a spoilage verdict), compressor asset risk |
| Evidence needs | PV capability, BMS capability, policy and override records, tank and delivery records | Chamber and ambient temperatures, door and loading records, compressor state, grid and transfer state |
| Intervention -> verification | Policy change -> runtime down with reserve and service guardrails | Defrost or setpoint change, or a compressor repair -> recovery time back in band, with an energy guardrail |

These read as different products to an operator, built from the same frames.
Relabelling one domain's cards would not get there, because the Overview
domains, the subtabs and the consequence types all differ.

**E-mobility as a third test:** objective, charging sessions served at an
acceptable energy cost; Performance subtabs Sessions, Availability, Energy
cost (Swap/Battery pool); Findings such as missed sessions, demand-charge
exposure, charger availability. The profile holds the presentation; Finding,
evidence and verification rules live in backend modules. A session log or swap
queue cannot live in the profile: those are **extension-slot screens**, which
the substrate already allows. That is the expected edge of the seam, not a
reason to make it more generic.

### 4.3 The seam: a presentation profile plus a backend capability declaration

**`DomainPresentationProfile`** (one per archetype, mini-grid only now). It is
**static presentation data**, and it **owns only** (owner's boundary):

- overview domains (which cards exist, and their order);
- performance views (subtab list and order);
- health emphasis;
- labels and vocabulary;
- consequence presentation.

**Placement.** The profile is **substrate data**, selected from the read
model's `site_type`. `ARCHITECTURE.md` (Shared Presentation Substrate) says
vocabulary "live[s] in the substrate and nowhere else" and that the substrate
carries no shell, mode or variant discriminant. So the profile is not a shell
module or a separate pack package, and **`site_type` is domain data, not a
shell or mode discriminant**. A Reviewer seeing `profileFor(site.siteType)`
should read it as data selection, not a variant branch.

**What it does not own.** Backend and domain modules remain authoritative
about "what findings actually exist", "what evidence an analytic requires" and
"what verification rules exist" (owner), and about consequence categories.
"The descriptor can reference those capabilities, but shouldn't become the
canonical source for them." The failure this prevents, in the owner's words:
"frontend pack says this Finding exists / backend analytic says something
different".

**The contract it references: the analytic capability declaration (born in
T028).** Nothing in the code owns Finding types, evidence requirements or
verification rules yet: `backend/assetops_backend` has `sites`, `runs`,
`scenarios` and the two APIs, and no evidence, analytic, finding or
verification module. The seam is born in two places: T028 (the first
analytic, Finding type and evidence requirement) and T034 (the first
verification rule set; T034 AC6 "Version these rules with the assessment").

Each analytic module declares:

- its id and the site types it applies to;
- the Finding type it may emit;
- its required and optional evidence (signals or capabilities);
- its claim levels (for dispatch: Necessary, Candidate avoidable,
  Indeterminate).

The backend serves the evaluated, site-scoped version as a read model. The
precedent for rigour is the simulator's model-profile pattern (required versus
optional input, unsupported recorded, enforced by a `tools/checks` guard). The
product side copies that rigour, **not its data**: `EXECUTION_REQUIREMENTS` in
`backend/assetops_backend/runs/profiles.py` describes what the simulator can
model, and product analytics may not read private or simulator flows (T031 AC2;
`ARCHITECTURE.md`).

The profile then holds only `id -> label / order / grouping / emphasis`, under
three rules:

1. A backend id the profile does not know **still renders**, with the
   backend's display name in a default position. Drift is never silent.
2. A profile id the backend does not serve **renders nothing**, and a test
   flags the orphan.
3. **A gap is shown only from backend state**, never from the profile. A gap
   is honest only when the backend says "this capability exists for this site
   and its evidence is insufficient".

The same declaration is what Site > Evidence part B scores against coverage,
and what decides tab and subtab applicability (2.4). That is why the domain
seam and the Evidence split converge on T028.

**Not recommended now:** registration, plugin loading, a cross-domain
assessment interface, a cold-chain implementation. Roadmap section 8 and the
Domain Reuse Boundary defer them, and nothing in the demo needs them.

**Timing:** write the mini-grid profile the first time a second Overview card
or second Performance subtab appears (T027/T028), so card and subtab lists are
never hard-coded in shared frames. That is a code placement rule, not a task.

---

## 5. Client-Facing Demo Journey

### 5.1 The full journey (polished, about 15 minutes)

| # | Screen | Client question | Role |
| --- | --- | --- | --- |
| 1 | Portfolio | Where is this portfolio losing value, carrying risk or leaving capacity unused? | **Hero** |
| 2 | Kobo > Overview | Is Kobo meeting its objective, and what matters now? | **Hero** |
| 3 | Kobo > Performance > Dispatch | Why did the generator run? | **Hero** |
| 4 | Finding detail + evidence drawer | Why are you saying this, and what limits the claim? | **Hero** (trust) |
| 5 | Finding consequence -> Site Financials | Does it matter? Change the price live. | Supporting |
| 6 | Recommendation -> Action -> Foundation > Changes | What do we change? | Supporting |
| 7 | Action > Verification ("two weeks later", pre-seeded) | Did it work, without hurting service or reserve? | **Hero** (differentiator) |
| 8 | Portfolio -> Desta > Renewable -> comparison | Where could we earn or use more? | Supporting (breadth: growth) |
| 9 | Arsi > Battery > Health | What is becoming expensive before it fails? | Supporting (breadth: asset value) |
| 10 | Genda > Fuel (optional) | Does fuel reconcile? | Optional (accountability) |
| 11 | Simulator Lab: truth vs inference | How do we know this is not scripted? | **Technical proof** |

**Kobo runs uninterrupted.** Detect, explain, monetise, intervene and verify
(steps 2-7) follow each other directly, and breadth comes after. This changes
roadmap section 5, which put Desta and Arsi between Kobo's money and its
verification. One unbroken story is the product promise; breadth then shows
the same loop covers growth and asset value.

**The live mechanics of step 7.** T034's outcome is "simulate the later
operating window and ingest the new evidence", so between Accept and
Verification a later window must exist. Running it live would be a Lab detour
mid-story, contradicting "Lab last, as proof". So the post-action window is
**already in accepted history from the seed** ("two weeks later"), and the Lab
appears only at step 11.

### 5.2 The journey at each earlier demo point

| Demo point | Journey | What it must persuade | Seed owned by |
| --- | --- | --- | --- |
| Internal (T027) | Lab run -> stage -> Commit -> Sites -> Kobo Overview -> Evidence (source health, coverage, record drill-down) -> Lab off, history stays | That the product boundary is real | (live run; no seed needed) |
| Expert / early prospect (T028-T029) | Sites -> Kobo Overview -> Dispatch -> Finding -> drawer -> Financials (change price) | "Is this real in your operation, and would you trust it?" (roadmap 13.2) | T029 |
| Strong product (T034 + Portfolio-lite) | Portfolio (three sites) -> Kobo -> Finding -> money -> Action -> Verification -> Lab proof | The closed loop, opened the way the final demo opens | T034 (post-action window), Portfolio-lite (three sites) |
| Polished (T036) | The full 5.1 journey | All six stories | T036 |

**Seed rule:** each demo point ships with an idempotent, rehearsed seed, owned
by the slice that creates the point, checked with the Lab gate off. Today only
T036 has reproducible recipes and documented demo commands (T036 AC1, AC15);
without this rule point 2 and point 3 would be staged by hand.

### 5.3 What is not early-demo material

- Sites index detail, Foundation Definition and Topology, the Site Findings and
  Work scoped indexes, Runs inventory;
- Lab setup, the picker, run history, and the cockpit beyond the final reveal;
- Incidents, Maintenance and Reports.

---

## 6. Implementation And Task Impact

Per task: **keep**, **rescope** (same position, different UI or content
outcome), **move**, **new** or **defer**, with the client capability it
unlocks. **[Planner verifies]** marks a claim the Planner checks against the
task files before relying on it.

### 6.0 Planner step 0 (records, before T027 starts)

- `DECISIONS.md` entries: the ownership test for grammar exceptions (2.2);
  the rendered-tab rule, per capability, and the narrowing or retirement of
  "labelled in place" in operator views (2.4); the presentation profile and
  analytic capability declaration seam (4.3); the seed rule (5.2); the
  owner's D1-D8 dispositions.
- `ARCHITECTURE.md`: the Presentation Honesty edit (2.4), and a note in Shared
  Presentation Substrate that the profile is substrate data keyed by
  `site_type` (4.3).
- Update `tasks/README.md` and the roadmap's demo story (5.1) and demo-point
  table (5.2), adding Portfolio-lite.
- Run the post-T034 dependency check (6.3) and set the exact order.
- Tasks citing v6.9 text that these decisions override cite the decision too.

### 6.1 Keep

- **T029A, before T034.** Minimal immutable-intervention mechanism, Lab-side.
  Unlocks nothing visible on its own; it is what makes step 7 possible.
- **T026A** stays unscheduled and gates nothing.
- **T034's position** directly after T029A (outcome rescoped in 6.2).
- **T033 and T035 as an interchangeable pair.** `tasks/README.md` and both
  task files already say so, and neither consumes the other.

### 6.2 Rescope (same position)

**Protecting point 2.** Every spine slice gains UI from this recommendation,
and `tasks/README.md` already says T027 is "watched for scope growth". Point 2
(T028-T029) is the expert checkpoint where feedback reshapes everything after
it, so the Planner protects its journey (Sites -> Kobo Overview -> Dispatch ->
Finding -> drawer -> Financials). Anything not on it can move to a thin
follow-on slice placed after T029. **First candidates: the Sites assessment
columns and the Sites-as-landing change**, which the point-2 journey does not
need (the presenter can open Sites from the rail). The Planner decides;
section 9 asks the owner to confirm the principle.

- **T027, Commit -> ingestion -> Site Overview. Rescope and phase.** Keep
  every acceptance criterion: this is a protected seam.
  - **Phase 1: Commit, ingestion, Site > Evidence (A), tab rule.**
    - Site > Evidence becomes a destination. Its body is source and connector
      health per source, per-signal coverage for the selected window, and the
      mapping and configuration basis. No capability readiness, no claim
      ceiling.
    - The record inspector (AC12) is a drill-down from source and signal rows.
    - Remove the six labelled-in-place Site tabs and Foundation's Readiness
      label; filter the one inventory by capability; update
      `navigation-truthfulness.ps1` and the tab tests (after step 0's record).
    - **AC10 clarification [Planner verifies the wording]:** "required
      signals" means the signals the Overview metrics need, not signals an
      analytic requires.
    - *Client capability:* a site's history is real; accepted records, three
      timestamps, mapping basis and coverage survive the Lab being off.
  - **Phase 2: the mini-grid Site Overview.** The v6.9 8.18 frame, cards from
    the profile, measured metrics with coverage and **"No assessment yet"**,
    the selected-day timeline, evidence links into the record inspector
    (AC11).
    - *Client capability:* a site page that answers "how is it operating?"
      from evidence. **Internal architecture demo.**
  - Sites columns (Last analysed, Evidence coverage) and Sites-as-landing:
    phase 2 or the thin follow-on, per point-2 protection.
- **T028, the dispatch Finding. Rescope and phase.** It now lands the
  analytic, the analytic capability declaration, the Finding, the drawer, the
  Findings root and global index, the scoped index, Performance > Dispatch,
  Overview card state and the Evidence capability table. Suggested phases (the
  Planner sets them):
  1. The dispatch analytic and the **analytic capability declaration**
     (backend contract and site-scoped read model, with its `tools/checks`
     guard), the Finding, and versioned assessment revision (T028 already
     states "Changed accepted evidence creates an inspectable assessment
     revision").
  2. Performance > Dispatch (the only subtab), Finding detail (Overview |
     Evidence | Alternatives), the drawer reusing the record inspector,
     **Findings** in the rail with its global index, Site > Findings as a
     scoped index, the Dispatch card showing a real assessment.
  3. **Site > Evidence part B:** the capability table with one row
     (dispatch). Sites columns Assessment and Top issue, unless moved to the
     follow-on.
  - The carried question whether stop-60's policy change appears as a policy
    record stays with T028.
  - *Client capability:* the first conclusion a practitioner can challenge,
    with what limits it.
- **T029, bounded financials. Rescope.**
  - Site > Financials becomes a destination with Overview and Assumptions
    subtabs. Assumptions are **editable in the UI**: changing the price live is
    the demo moment.
  - The Finding's consequence panel and the Overview's value line read the
    same model.
  - **Decide BusinessContext scope** (site-scoped recommended; record "shared
    or portfolio assumption sets" as the trigger to revisit global
    Financials, 2.5).
  - **Add the point-2 seed:** one Kobo site, a healthy window and a
    prolonged-runtime window committed, idempotent, checked with the gate
    off, rehearsed.
  - *Client capability:* **first highly useful demo**: one site, one strong
    Finding, its evidence, its money, under the client's own price.
- **T034, policy action and verification. Rescope.**
  - The Finding's Recommendation tab leads to Accept, which creates an
    **Action** root; **Actions** enters the rail (WORK header).
  - The Action renders Overview and Verification only.
  - The Finding's Recommendation and History tabs appear; the Findings index
    gains "Awaiting verification".
  - **Foundation > Changes** appears, linking to the post-action configuration
    evidence (T034 AC4) rather than standing in for it.
  - Site > Work renders the Actions index with no subtab row.
  - The verification rule set is versioned and backend-owned (T034 AC6, AC7);
    the profile only presents it.
  - **Add the point-3 seed:** Kobo's post-action window already in accepted
    history.
  - *Client capability:* detect, explain, monetise, intervene, verify;
    Completed visibly distinct from Verified.
- **T036, portfolio and client demo. Rescope** to completing a Portfolio that
  already exists: add the remaining sites; add global Evidence (ASSURANCE)
  only if it passes the ownership test explicitly; keep the financial roll-up
  as Portfolio's value column; build the Lab truth-versus-inference reveal;
  write and rehearse the walkthrough. Its other acceptance criteria are
  unchanged, minus AC1's Meki recipe and AC4-AC6, which Portfolio-lite pulls
  forward. *Client capability:* **polished client demo.**

### 6.3 Move

- **T025h, to after T029** (or a Lab-ergonomics bucket with the delta-latency
  task carried from T025e and T026). A client never sees it; template-version
  drift is avoided for the demo by seeding v3 sites. Its pending ruling (does
  the status depend on the whole form, or only on scenario and profile) waits
  until it is scheduled. If the owner wants it settled now, the whole-form
  reading is the honest one: a preview of Create must depend on everything
  Create reads.
- **Post-T034 breadth slices: priority intent, order set by the Planner.**
  Owner: "Priority intent: Opportunity before fuel if dependency cost is low.
  Service before battery unless feedback says otherwise", "but not
  hard-freeze the exact task order until Planner verifies what T030 actually
  provides that T031 consumes."
  - **Why opportunity first:** it is the only story that is not a loss, and
    it turns the client's question from cost to growth. Fuel reconciliation is
    a second loss story shaped like dispatch.
  - **Why service before battery:** unserved customers are an operator's
    first concern, and T033 is already the named first deferral.
  - **Opportunity-first costs two slices, not one.** It means T031 **and**
    T032 before T030: T031's headroom is a physical quantity with no money,
    and the growth story the demo wants (Desta's paired comparison with a
    scenario value) arrives only with T032, the heavier slice. So "dependency
    cost is low" should be read as "dependency cost is low; slice cost is
    two". That may still be right, because fuel adds the least new
    persuasion.
  - **Dependency check [Planner verifies before fixing the order]:**
    - T031's header says `Depends on: T027-T030 and A's curtailment/dispatch
      model` and `Delivery order: after T030`. Its acceptance criteria
      consume T027 evidence and T028 dispatch inputs (AC3), C's evidence and
      claim structure (AC7, T028), price and tariff invariance (T029), and a
      curtailing world that **T031 owns itself** (AC1, AC2). None names a T030
      artifact; "T027-T030" reads like range shorthand from the old linear
      queue. T032 depends on T031, T029 and T029A, not T030.
    - Rule out three possible couplings:
      - (a) **T030 AC9** (a late record revises an accepted assessment, with
        history kept). If T030 were the first slice to build assessment
        revision, T031 AC9 ("deterministic/versioned and avoids duplicate
        Findings") could rely on it. T028 already states that changed accepted
        evidence creates an inspectable assessment revision, so no coupling
        is expected; confirm.
      - (b) **T030 AC13** (Site Financials without double-counting). T031 adds
        no money, so none is expected.
      - (c) **T030 AC2** (extending T026's operational-record family). T031
        uses no operational records, so none is expected.
    - No shipped world curtails PV yet (CODE_STATE T026). T031 supplies one
      (recipe, possibly a new signal, the L2 check): that is slice size, not a
      dependency.
    - If a real coupling is found and costly, fuel stays first.
  - Subject throughout to the T028/T029 expert feedback, as
    `tasks/README.md` already requires.

### 6.4 New

- **Portfolio-lite, directly after T034. A real slice; size it honestly.**
  - **What it is:** a thin Portfolio becomes the landing page and enters the
    rail (OPERATE header, before Sites). It ranks Findings with consequence
    and basis, with attention and evidence-gap lenses.
  - **What it needs:** three reproducible sites with their own seed:
    - **Meki, healthy:** pulls T036 AC1's Meki recipe forward;
    - **Kobo, with post-action history:** from T034's seed;
    - **an evidence-limited site** on which T028's analytic runs and limits
      its claim, built from T026's `kobo-mini-grid-degraded-evidence`
      scenario [Planner verifies that the analytic produces a limited claim
      on it].
  - **Planned work it pulls forward:** T036 AC4-AC6 (priority rule and
    no-fake-total rule) [Planner verifies the AC numbers].
  - **Why:** the strong product demo opens the way the final one does, and
    every later slice adds its site to the first screen a client sees.
  - *Client capability:* **strong product demo**, opening on Portfolio.
- **Thin follow-on slice (conditional):** only if the Planner moves the Sites
  columns and Sites-as-landing out of T027/T028 to protect point 2. Placed
  after T029. *Client capability:* the Sites index ranks sites by assessment
  and evidence until Portfolio-lite takes the landing.
- **No other new tasks.** The profile is a placement rule (4.3); the seeds are
  folded into the slices that create each demo point.

### 6.5 Defer

- **T025h** (6.3).
- **The delta p95 performance task:** run before the T036 rehearsal only if
  the reveal's playback visibly stutters.
- **L3 cockpit enrichment** (C7-C9), until after T036.
- **Replay mode** and a broad source-health dashboard.
- **Global Financials** (open, 2.5) and **Reports**. Global Evidence is a T036
  candidate, not deferred past it.
- **Incidents and Maintenance** indexes and subtabs.
- **Asset Warranty**, and any asset inventory beyond the battery.
- **Cold-chain and e-mobility** implementation, and any pack registry.
- **Any Foundation editing** beyond the T034 change record.

---

## 7. Near-Term Proposed Sequence

| Step | Slice | What the client can newly see |
| --- | --- | --- |
| 0 | Planner step 0 (6.0): records, queue, roadmap, dependency check; T025h parked | (none) |
| 1 | T027 phase 1: Commit, ingestion, **Site > Evidence (source health and coverage)**, record inspector drill-down, labelled-in-place tabs removed | A site's history is real: accepted records, three timestamps, mapping basis and coverage that survive the Lab being off. Three Site tabs, all real |
| 2 | T027 phase 2: **mini-grid Site Overview** ("No assessment yet" cards with measured metrics and coverage) | A site page that answers "how is it operating?" from evidence. **Internal architecture demo** |
| 3 | T028 (phased): **Dispatch -> Finding -> evidence drawer**, Findings in the rail, analytic capability declaration, **Site > Evidence capability table (one row)** | The first conclusion a practitioner can challenge, with what limits it |
| 4 | T029: **Site Financials** with live assumptions, BusinessContext scope decided, **point-2 seed** | **First highly useful demo** (expert and early prospect): one site, one strong Finding, its evidence, its money. *Feedback checkpoint; reassess steps 9-12* |
| 5 | Thin follow-on (if moved): Sites assessment columns, Sites as landing | The first screen ranks sites by assessment and evidence |
| 6 | T029A: frozen intervention (Lab) | Technical: a policy change alters the simulated world from a declared time |
| 7 | T034: **Recommendation -> Action -> Foundation > Changes -> Verification**, Actions in the rail, **point-3 seed** | Detect, explain, monetise, intervene, verify; Verified distinct from Completed |
| 8 | **Portfolio-lite** (new), with its three-site seed | **Strong product demo**, opening on Portfolio: three sites, a ranked Finding with its value, an evidence-limited site, a verified action |
| 9-12 | **Priority intent, order set by the Planner after the 6.3 check:** opportunity (T031 -> T032: Desta headroom, Opportunities lens, paired comparison) before fuel (T030: Genda reconciliation) if dependency cost is low; service (T035: Bahir service and backup failure) before battery (T033: Arsi trajectory, Health tab, Assets root) unless feedback says otherwise | Growth: unused renewable capacity and a trial load. Accountability: a residual with uncertainty. Reliability: unserved energy and a backup chain with missing links. Asset value: stress trajectory and bounded replacement exposure |
| 13 | T036 (rescoped): six sites complete, global Evidence if it passes the ownership test, Lab truth-vs-inference reveal, rehearsal | **Polished client demo** |

Each of steps 9-12 adds a site that appears on the Portfolio as it lands, so
each is demonstrable as a new opening-screen story, not only as a deep page.
Step 6 (T029A) is the one technical step, accepted because it directly enables
step 7.

---

## 8. Decisions

### 8.1 The owner's dispositions, 2026-10-02 (verbatim)

| Decision | Owner feedback |
| --- | --- |
| D1 filtered grouped root menu | Accept, but don't promise the full v6.9 end-state can never change |
| D2 Portfolio-lite after T034 | Strong accept |
| D3 Kobo detect→verify uninterrupted | Strong accept |
| D4 opportunity before fuel; service before battery | Accept as priority intent, dependency-check before exact reorder |
| D5 static mini-grid archetype descriptor | Accept with narrower authority |
| D6 Site Evidence at T027 | Accept, but T027 = source/coverage; analytic claim readiness matures from T028 |
| D7 Action + Foundation Changes representation | Accept; very coherent |
| D8 park T025h | Accept |

Owner's summary: "Adopt the sequencing and product-surface recommendations,
but loosen unnecessary loyalty to rendered canonical navigation, narrow the
domain descriptor's authority, and distinguish source-evidence readiness at
T027 from claim-capability readiness that emerges with analytics at T028+."

### 8.2 How this version carries each

- **D1.** The grouped menu is the target and the reference, not frozen;
  changes pass the ownership test (2.2) and get a DECISIONS entry. Demo rail
  filtered to live items, headers from T028 (2.1).
- **D2.** Portfolio-lite after T034, sized as a real slice with its own
  three-site seed (6.4); T036 rescoped to completing it.
- **D3.** Kobo runs detect to verify uninterrupted, with a pre-seeded
  post-action window so the Lab stays last (5.1).
- **D4.** Priority intent only; the Planner runs the 6.3 check and sets the
  order. Opportunity-first moves two slices ahead of fuel.
- **D5.** The profile owns presentation only, as substrate data keyed by
  `site_type`; the backend owns Findings, evidence requirements, verification
  rules and consequence categories through the T028 analytic capability
  declaration, with the three rendering rules (4.3).
- **D6.** T027's Evidence body is source health and coverage, the record
  inspector is a drill-down, Overview cards say "No assessment yet"; claim
  readiness arrives at T028 as a one-row capability table (section 3,
  Evidence).
- **D7.** Action plus Foundation > Changes, with Changes linking to
  post-action configuration evidence (section 3, Action / Verification).
- **D8.** T025h parked until after T029, with its pending ruling (6.3).

The owner also called these especially right, and they are kept as they were:
the Site Overview hierarchy, the Finding Detail hierarchy, Completed versus
Verified as a visible product concept, and global Financials kept out of the
demo rail with economics in Site Financials, Finding consequence and
Portfolio's value column.

---

## 9. For The Owner To Decide Or Confirm

1. **Global Financials (still open).** Recommendation: keep the cross-site
   roll-up in Portfolio for now and promote it to a BUSINESS root only when a
   portfolio-owned financial object exists, such as shared assumption sets.
   Decide after T036 (2.5).
2. **BusinessContext scope in T029.** Recommendation: site-scoped, with
   "shared or portfolio assumption sets" recorded as the trigger to revisit
   item 1. Confirm, or rule portfolio-shared now, which would reopen item 1
   earlier.
3. **Your tab rule overturns recorded decisions.** It does not change any of
   your rulings; it changes the 2026-09-13 and 2026-09-17 entries in
   `DECISIONS.md`, `ARCHITECTURE.md` Presentation Honesty, a build check and
   shipped tests. Confirm the form: **recommended, "labelled in place" is not
   used in operator views** (narrowed), or retired everywhere. Also confirm
   that it is applied per capability, not per site (2.4).
4. **Protecting demo point 2.** Confirm the principle that work not on the
   point-2 journey may move to a thin follow-on after T029, starting with the
   Sites assessment columns and Sites-as-landing. This changes the T027 and
   T028 content the earlier D6 proposal described, not your D6 ruling.
5. **The cost of opportunity-first.** Confirm you read D4's "dependency cost
   is low" with the stated slice cost: T031 and T032 both move ahead of T030.
6. **No cold-chain screens in the polished demo.** Confirm, so that roadmap
   section 8 and PRODUCT.md's deferral stand.

Nothing else in this version changes an owner ruling.

---

## Self-Check Against The Request's Quality Bar

1. **Mental models, not features.** Yes. The rail shows the classes a manager
   uses, under v6.9's group headers, filtered to live surfaces. Canonical
   classes without content wait.
2. **Global versus contextual.** Yes. Sections 2.2 and 2.3 place every named
   concept; Findings, Financials, Evidence and Work each have an explicit
   global, contextual and detail-root treatment.
3. **Hierarchy serves the promise.** Yes. Each hero page leads with a bounded
   operational or economic claim and its basis, and evidence is one click
   away. Site > Evidence never shows claim readiness before an analytic claim
   exists, and Overview cards say "No assessment yet" until one does.
4. **Coherent for mini-grid and cold-chain.** Yes. The same frames carry
   different domains, subtabs and consequence presentation (4.2), while
   Finding, evidence, verification and consequence rules stay backend-owned
   behind a named contract (4.3). E-mobility shows the seam's edge.
5. **Domain differences visible.** Yes. Overview domains, Performance
   subtabs, consequence types and claim limits differ per domain; product
   exposure is a chip, not a card.
6. **Demo value early.** Yes. A canonical client surface lands at every spine
   step, point 2 is protected from scope growth, every demo point has a seed,
   and Portfolio-lite brings the opening screen forward to step 8.
7. **Canonical concepts reused.** Yes. No new object classes. Opportunities
   are a lens, the comparison is a drill-down, the profile configures existing
   frames. Deviations from v6.9 (the tab rule, Site > Work without a subtab
   row, the possible global Financials change) pass a stated ownership test
   and get decision records.
8. **Low-value purity off the critical path.** Yes. T025h is parked, the
   performance task deferred, no pack framework, and the tab-rule change is a
   filter change landing inside T027 phase 1. Ingestion acceptance criteria
   stay as protected seams.
9. **Each slice demonstrable.** Yes, except T029A (step 6), which is technical
   and accepted because it directly enables step 7. T027 and T028 phases each
   end in something visible.
10. **Intelligence, not monitoring or CMMS.** Yes. Ranking is by
    consequence-bearing Findings, Verified is distinct from Completed,
    Incidents, Maintenance and Reports stay out of the demo rail, no header
    sits over empty items, no empty tab renders, and nothing is shown that the
    backend cannot back.

---

## How This Version Was Reached

- First draft answering the owner's request, then an appendix comparing a
  grouped root menu (owner question), folded in at `a28479f`.
- The owner's verbatim review, with five pushbacks and the D1-D8 rulings:
  `.agent/owner-review-architect-recommendation-2026-10-02.md`. Applied at
  `b12ae86`.
- The Architect's response to that review, agreeing with all five pushbacks
  and listing six corrections and further material items:
  `.agent/architect-response-to-owner-review-2026-10-02.md` (`3178d55`,
  `0884026`).
- The owner's instruction to produce this final version:
  `.agent/owner-instruction-final-recommendation-2026-10-02.md` (`e5efd17`).

This version integrates all of those rounds into the body. `git log` on this
file shows the earlier states.
