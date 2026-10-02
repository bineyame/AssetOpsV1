# Architect Recommendation: Demo-Led Navigation, Content And Sequencing

**Status: review input, pending owner sign-off.** This is not the roadmap and
does not replace it. It answers the owner's request of 2026-10-02 (saved
verbatim at `.agent/architect-demo-roadmap-request.md` on
`task/T025h-picker-compatibility`). Nothing here changes `tasks/README.md`,
any task file, `.ai/FEATURE_MAP.md`, `.ai/DECISIONS.md` or
`Docs/mini-grid-demo-architecture-and-roadmap.md`. Once the owner has reviewed
it, the Planner updates the roadmap and queue from whatever the owner accepts.
Queue changes below are **proposals**.

Produced by Claude as Architect under the ROLE_CONFIG exception in force until
the Codex reset on 2026-10-03 21:23. A later reader may send any judgement here
back to Codex.

Sources: v6.9 canonical screens (sections 2, 4-8), roadmap sections 3-5, 8 and
13, `.ai/PRODUCT.md`, `.ai/ARCHITECTURE.md` (Shells And Navigation, Shared
Presentation Substrate, Domain Reuse Boundary), `.ai/FEATURE_MAP.md`,
`tasks/README.md`, the T027-T036 task files, T025h (on its branch), CODE_STATE
T011A/T012/T026, and the backlog items carried from T026.

**Built state these proposals start from.** A is accepted. Lab cockpit
L1a-L1c are built. Template v3 and T026's dispatch evidence are merged. That
evidence (capability signals, policy and override records, one gap, one held
publication) is **staged, never committed**. The operator shell has two
navigation items (`Operator home`, `Sites`). A Site has two tab destinations
(Overview showing identity only, and Foundation) and six tabs labelled in
place. There are no Findings, Financials, Actions or accepted history yet, so
**every client-visible surface the demo needs is still ahead of us**. That is
why sequencing now has more effect on demo value than anything else.

---

## 1. Executive Recommendation

**Navigation philosophy: keep v6.9's grammar exactly, grow it by demo value.**
The ten root object classes, the eight Site tabs, the "at most one subtab row"
invariant and the scoped-index rule (v6.9 sections 2.1-2.4) are sound. They
already separate the canonical object, the menu item, the contextual tab and
the drill-down, which is what the request asks for. What they lack is an
order of prominence. This recommendation supplies that order and nothing else
about the model.

The project's own rule already decides when a navigation item may appear: only
once a truthful surface exists behind it. So the client never sees ten rail
items. They see the four that carry the story, in the order the story earns
them.

**Root menu for the client demo:** `Portfolio | Sites | Findings | Actions`,
plus `Assets` once Battery health exists. Within the canonical Business and
Assurance groups, Financials and Evidence keep their **site-owned** tabs
prominent. Their global roll-ups enter the rail only if the six-site portfolio
needs them. Incidents, Maintenance and Reports stay canonical but are not demo
material. Simulator Lab stays a separate gated workspace, reached from the
utility menu and opened last as proof.

**Site structure:** keep the eight tabs, but give them three tiers:

- **Hero tabs:** Overview, Performance (with domain subtabs) and Financials.
- **Trust tab:** Evidence, which is site-owned claim readiness.
- **Supporting tabs:** Foundation (with Changes as the record of an
  intervention), Findings and Work (scoped indexes), and Health (only once
  lifecycle evidence exists).

**Domain-pack recommendation:** introduce one **archetype descriptor**. It is
static data, written for mini-grid only, and it names:

- the Overview assessment domains;
- the Performance subtabs;
- the assets Health emphasises;
- the Finding types the archetype can produce;
- its consequence categories;
- the evidence capabilities its claims need;
- its verification target and guardrail templates.

Shared machinery reads the descriptor through the existing substrate extension
slots. Cold-chain and e-mobility are tested against it on paper (section 4),
not in code. This is not a pack framework.

**Major sequencing recommendations:**

1. Keep the spine: T027 -> T028 -> T029 -> T029A -> T034.
2. Rescope the UI outcome of each spine slice so that it lands a canonical
   surface. For example, T027's evidence inspector becomes Site > Evidence
   rather than a one-off panel.
3. Add a **thin Portfolio command center right after T034**, over the sites
   whose stories already exist. This moves the opening screen of the final demo
   forward from last to fifth.
4. After that, add each further story (opportunity, fuel, service, battery) as
   one Site that joins the Portfolio, so every slice changes the opening screen.
5. Move T025h off the path, to after T029, and leave its pending ruling until
   then. It is developer ergonomics that a client never sees.
6. Fold a reproducible demo seed into T029, so demo point 2 can be repeated
   rather than staged by hand.

---

## 2. Navigation And Root Context

### 2.1 Proposed client-facing tree

The tag after each item says when it becomes a truthful destination. Items
marked "not demo" stay canonical and may arrive later. They are not removed
from the model.

```
OPERATOR SHELL (left rail; highlights the root object's class)
|
|-- Portfolio ............ root; landing page        [Portfolio-lite, after T034]
|     lenses: Attention | Opportunities | Evidence gaps (filters, not tabs)
|     the value column is the Financials roll-up; the evidence-gap column is the Evidence roll-up
|
|-- Sites ................ root; index               [built; gains Assessment /
|     |                                               Top issue / Evidence /
|     |                                               Last analysed at T027-T028]
|     `-- Site (root object)
|           Overview ........ HERO, site-owned        [T027]
|           Performance ..... HERO, site-owned        [T028: Dispatch]
|           |   mini-grid: Dispatch | Service | Renewable | Fuel | Backup
|           |   (subtab appears only when it has content)
|           Financials ...... HERO, site-owned        [T029]
|           |   Overview | Assumptions (later: Drivers | Scenarios)
|           Evidence ........ TRUST, site-owned       [T027]
|           |   capability readiness + accepted source records
|           Findings ........ scoped index            [T028]
|           Work ............ scoped index            [T034: Actions only]
|           Foundation ...... supporting, site-owned  [built; Changes at T034]
|           |   Definition | Topology | Controls | Changes | Readiness
|           Health .......... supporting              [T033; labelled in place until then]
|
|-- Findings ............. root; global index        [T028]
|     lenses: All | Opportunities | Risks | Awaiting verification
|     `-- Finding (root object)
|           Overview | Evidence | Alternatives | Recommendation | History
|           (claim evidence drawer opens from any claim; never changes root)
|
|-- Actions .............. root; global index        [T034]
|     `-- Action (root object)
|           Overview | Plan | Execution | Evidence | Verification | History
|
|-- Assets ............... root; thin index          [T033, first Asset Detail]
|     `-- Asset: Battery > Health (others when evidenced)
|
|-- Financials / Evidence  global roll-ups           [only if T036 needs them; else not demo]
|-- Incidents, Maintenance, Reports                  [not demo; canonical, deferred]

UTILITY MENU
`-- Open Simulator Lab -> SIMULATOR LAB WORKSPACE (separate shell, gated)
      Home | Sites | Simulator Lab | Scenarios | Site Templates | Runs ...
      run cockpit, stage inspector, truth vs AssetOps evidence (proof only)
```

`Operator home` is a placeholder from T002. It should go once Sites becomes
the landing page (T027). Sites then hands the landing to Portfolio when
Portfolio-lite ships. Until then Sites is the first screen, which is why the
assessment columns matter: with them the first screen asks "which site needs
attention, and how sure are we?". Without them it is a list of names.

### 2.2 The five kinds of place, and why each concept sits where it does

| Kind | Members | Rule |
| --- | --- | --- |
| Root navigation | Portfolio, Sites, Findings, Actions, (Assets) | A class the user manages across sites, or reaches as a decision object. It appears only when its root object has a real detail page. |
| Contextual tabs | Site's eight; Finding's five; Action's six | Aspects of one root object. A tab may be labelled in place before its content exists. It may not be disabled. |
| Scoped indexes | Site > Findings, Site > Work | A filter over a global class, with no KPI strip and no status model of its own. Clicking a row changes the root. v6.9 2.3's test: remove the tab and lose nothing except a filter. |
| First-class detail roots | Finding, Action, Asset (Incident, Maintenance later) | Starting work on one of these changes the root and the rail highlight. The breadcrumb keeps the Site so Back is predictable. |
| Technical workspace | Simulator Lab | A separate shell behind the gate. In the demo it is proof, never navigation. |

How each concept the request names is placed:

- **Portfolio.** Root, and the landing page once at least three sites have
  different stories. Its job is prioritisation, not monitoring, so it earns
  the root.
- **Sites.** Root. It is the operator's mental anchor and is already built.
- **Assets.** Root, but late, and with a thin index. The navigation invariant
  needs Assets in the rail once Battery > Health is a root page (v6.9 8.27).
  A rich asset inventory is deferred under roadmap section 8. Until T033,
  asset condition lives under Site > Health, which remains labelled in place.
- **Findings.** Root, from T028. A Finding is the product's unit of value, so
  hiding it inside a Site would make the decision object hard to find. The
  model v6.9 2.3 describes is right: a global index, plus a scoped Site
  filter, plus Finding detail as its own root. **Opportunities are a lens on
  Findings, not a new class**, so the productive-use story needs no new
  object.
- **Actions.** Root, from T034. An accepted change, its owner and its
  verification outlive the Finding view. The pair "Finding resolved" and
  "Action verified" is the product's closed loop, and each half needs its own
  place.
- **Incidents and Maintenance.** Canonical, but not demo material. The first
  verification story is a policy change, which is an Action. T035's backup
  failure can stand as a Finding without an incident subsystem: T035's spec
  already rules that subsystem out, and this recommendation agrees.
  Maintenance is what makes a product feel like a CMMS. It should arrive when
  a pilot needs work requests, not before.
- **Evidence.** Primarily **site-owned** (Site > Evidence: what can be claimed
  here and what evidence would raise the ceiling), plus the
  **claim-specific** evidence drawer on every material number. The portfolio
  roll-up stays a column on Portfolio ("evidence gaps") until the gap matrix
  across sites has real content.
- **Financials.** Primarily **site-owned** (Site > Financials, the bridge from
  technical findings to economics), and quoted on Finding detail and the
  Overview. The portfolio roll-up is the value column of Portfolio Value &
  Operations (roadmap section 4). A separate global Financials page is
  optional, at T036 at the earliest.
- **Simulator Lab.** A separate workspace. This is not open: it is settled by
  `ARCHITECTURE.md` Shells And Navigation and by the 2026-09-13 decisions.

### 2.3 The Work question

Site > Work stays a scoped index, but at first with **one** subtab, Actions.
Showing `Actions | Incidents | Maintenance` with two of them permanently empty
would make the product read as a ticketing system. The other two subtabs
appear when their classes have content.

---

## 3. Page Hierarchy And Content

Each page below has a role, the decision it helps the user make, and an
information hierarchy (what comes first, what supports it, where it leads).
Widget-level layout belongs to v6.9 section 8 and the Planner, not here.

### Portfolio Value & Operations (the opening screen)

- **Decision:** where management attention and capital go first.
- **Hierarchy:**
  1. One sentence of scope: window, number of sites, mode (SIMULATED stated
     as provenance).
  2. **Ranked Findings across sites.** Each row shows the site, the bounded
     claim, a value or consequence carrying its basis (measured, modelled or
     scenario), confidence, and the action state. The value can be an OPEX,
     service, asset or opportunity figure, each kept separate.
  3. Three short lenses: attention, opportunities, evidence gaps.
  4. "What changed": verified, reopened, or closed without proof.
- **What makes it intelligence rather than a dashboard:** the ranking unit is
  a *Finding with its consequence*, not a site's alarm count. No figure is
  totalled across consequence types, and a site that is healthy because its
  evidence is adequate is visibly different from a site we cannot assess.
- **Leads to:** a Finding (root changes), or a Site.

### Site Overview (mini-grid: "Is this site meeting its operating objective, and what matters now?")

- **Decision:** which aspect of this site to open.
- **Hierarchy:**
  1. The objective strip: site assessment, service delivered, confidence.
  2. **One assessment card per domain**, taken from the descriptor. For
     mini-grid these are Service, Dispatch, Battery, Fuel and Renewable. Each
     shows an assessment word plus a one-line reason, or Unknown with the
     missing evidence named. Before T028 no card claims an assessment; cards
     show measured metrics and their coverage (T027 AC11).
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
  to its Finding. This is the page where a domain expert decides whether the
  product understands their site, so it must show policy, reserve and
  capability at the interval's own time.
- **Renewable.** Decision: is there capacity being wasted that could be
  used? Recurring headroom windows after demand, reserve, storage and policy
  are checked. From an opportunity, "Evaluate intervention" opens the paired
  comparison (T032) as a drill-down. It is not a tab.
- **Fuel, Service and Backup** follow v6.9 8.20-8.24 when their slices land.
  Fuel shows an unexplained residual with uncertainty and never an
  accusation. Service shows unserved energy and coverage. Backup shows the
  event chain with missing links stated.

### Finding Detail (the trust-defining page)

- **Decision:** do I believe this, and what would I do about it?
- **Hierarchy (Overview tab):**
  1. The bounded claim in one sentence.
  2. Observed facts kept separate from inference.
  3. Confidence and its basis, kept separate from coverage.
  4. The claim ceiling ("13 min capability gap limits this").
  5. The consequence, as a technical quantity first and money second.
  6. The next step.
- **Other tabs:**
  - Evidence: a claim-by-claim list that opens the drawer.
  - Alternatives: the competing explanations and why each was ruled out or
    left open.
  - Recommendation (T034): the change and its declared success criterion.
  - History (T034): assessment revisions, verification and reopening.

### Financial Consequence (Finding panel plus Site > Financials)

- **Decision:** does this matter enough to act on, under *our* assumptions?
- **Hierarchy:**
  1. Technical quantity (runtime hours, litres range).
  2. Assumptions in use (versioned fuel price, maintenance accrual).
  3. Money range, with its basis and a window or extrapolation label.
  4. A link back to the source Finding.
- **The demo moment:** change the price and the money moves, while physics
  and confidence stay where they are.
- **What the page carries no status for:** financial pages hold no
  assessment (v6.9 8.36).

### Productive-Use Opportunity (Renewable plus the paired comparison)

- **Decision:** is it worth trialling a productive load in that window?
- **Hierarchy:**
  1. The physical headroom: when it occurs, how much, how often it recurs, and
     what constrains it.
  2. The candidate load (owner's choice, roadmap 12.2).
  3. Baseline against intervention: PV use, curtailment, diesel, energy served,
     and revenue labelled as scenario.
  4. Explicit limit: market demand is not established.

### Asset Lifecycle / Health

- **Site > Health** answers whether any asset is on a harmful trajectory. It
  shows two separate blocks, physical condition and source health, and a
  gateway being Online never stands in for a battery being Healthy.
- **Battery > Health** (Asset root) shows current evidenced state, stress
  recurrence against a reference band, and the bounded replacement exposure.
  It never gives a failure date.

### Action / Verification (the closed-loop differentiator)

- **Decision:** did the change work without unacceptable side effects?
- **Hierarchy:**
  1. The managed-object header: owner, due, state, source Finding, success
     criterion.
  2. The **declared target and guardrails, shown together.**
  3. The before window against the post-action window, with comparability
     limits.
  4. The outcome: Verified, Ineffective or Inconclusive, with reasons.
  5. What happened to the Finding: resolved, or kept open.
- **Wording:** "Completed" and "Verified" are visibly different words. That
  difference is the CMMS contrast the demo makes.
- **Composition:** the same policy change also appears on Foundation >
  Changes, as an auditable record of what changed in the world and when.

### Evidence (Site > Evidence plus the claim drawer)

- **Site > Evidence** answers what AssetOps can substantiate at this site.
  For each capability it shows Full, Limited or None, the claim ceiling, and
  the next-best evidence. Below that are accepted source records with all
  three timestamps (source, publication, receipt).
- **The drawer** answers why a particular number is true. It shows the window,
  the evidence references, coverage, configuration at the time, and the
  mapping and algorithm versions. Opening it never changes the root.

### Simulator Proof (Lab, last)

- **Decision:** is the analytic inferring, or reading a script?
- **Hierarchy:**
  1. Private physical truth beside what was reported.
  2. The staged envelopes, then the committed ones.
  3. Truth against the product's conclusion, by run, window and evidence
     reference, including one case where the claim was limited.
- **What this shows the client:** the simulator was not the source of the
  answer.

---

## 4. Domain-Aware Product Structure

### 4.1 What is common and what changes

| Common shell (never branches on domain) | Changes by domain (descriptor content) |
| --- | --- |
| Root navigation, Site tab set, subtab-row invariant | The **list** of Performance subtabs and their order |
| Finding, Action and Verification objects; status vocabulary; claim discipline | Which Finding types exist and what each may claim |
| Evidence drawer, capability coverage, the three timestamps | The evidence capabilities a domain's claims need |
| Financial bridge (quantity x versioned assumption; no overlapping totals) | Consequence categories (fuel, energy, service, product exposure, asset) |
| Site Overview frame (objective strip, assessment cards, timeline, top Findings) | The objective sentence, the assessment domains and the timeline series |
| Health frame (physical condition kept apart from source health) | Which assets are emphasised |
| Verification frame (target plus guardrails, comparable windows) | Target and guardrail templates per intervention type |

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

These read as different products to an operator even though the screens are
built from the same frames. That is the right outcome. Relabelling one domain's
cards to fit the other would not get there, because the Overview domains, the
subtabs and the consequence types all differ.

**E-mobility as a third test:**

- Objective: charging sessions served at an acceptable energy cost.
- Performance subtabs: Sessions, Availability, Energy cost, (Swap/Battery
  pool).
- Typical Findings: missed sessions, demand-charge exposure, charger
  availability.
- The descriptor holds all of this.

One thing the descriptor cannot hold is a session log or swap queue. Those
are **extension-slot screens**, which the substrate already allows. That is
the expected edge of the seam, not a reason to make it more generic.

### 4.3 The seam: an archetype descriptor, not a pack framework

**Recommended:** one module per archetype, holding **static data** and
selected by the Site's archetype (which the template already records). It
holds:

- the Overview domain list;
- the Performance subtab list;
- the Health asset emphasis;
- the Finding types the archetype may produce;
- its consequence categories;
- the evidence capabilities it requires;
- its verification templates;
- the archetype's vocabulary.

The shared frames iterate over it. Analytics stay ordinary backend modules,
and the descriptor names them without hosting them.

**Not recommended now:** registration, plugin loading, a cross-domain
assessment interface, or a cold-chain implementation. Roadmap section 8 and
`ARCHITECTURE.md`'s Domain Reuse Boundary already defer them, and nothing in
the demo needs them.

**Cost and timing:** write the mini-grid descriptor the first time a second
Overview card or second Performance subtab appears (T027/T028), so that card
and subtab lists are never hard-coded inside shared frames. This is a code
placement rule, not a task.

---

## 5. Client-Facing Demo Journey

### 5.1 The recommended full journey (polished, about 15 minutes)

| # | Screen | Client question | Role |
| --- | --- | --- | --- |
| 1 | Portfolio | Where is this portfolio losing value, carrying risk or leaving capacity unused? | **Hero** |
| 2 | Kobo > Overview | Is Kobo meeting its objective, and what matters now? | **Hero** |
| 3 | Kobo > Performance > Dispatch | Why did the generator run? | **Hero** |
| 4 | Finding detail + evidence drawer | Why are you saying this, and what limits the claim? | **Hero** (trust) |
| 5 | Finding consequence -> Site Financials | Does it matter? Change the price live. | Supporting |
| 6 | Recommendation -> Action -> Foundation > Changes | What do we change? | Supporting |
| 7 | Action > Verification | Did it work, without hurting service or reserve? | **Hero** (differentiator) |
| 8 | Portfolio -> Desta > Renewable -> comparison | Where could we earn or use more? | Supporting (breadth: growth) |
| 9 | Arsi > Battery > Health | What is becoming expensive before it fails? | Supporting (breadth: asset value) |
| 10 | Genda > Fuel (optional) | Does fuel reconcile? | Optional (accountability) |
| 11 | Simulator Lab: truth vs inference | How do we know this is not scripted? | **Technical proof** |

**One deliberate change from roadmap section 5:** the Kobo intervention and
its verification (steps 6-7) follow Kobo's money directly, instead of coming
after Desta and Arsi. One unbroken story (detect, explain, monetise,
intervene, verify) is the product promise. Breadth then shows that the same
loop covers growth and asset value. Splitting Kobo's story around two
breadth detours weakens the claim the demo exists to make. This is an owner
decision (section 8, D3).

### 5.2 The journey at each earlier demo point

| Demo point | Journey | What it must persuade |
| --- | --- | --- |
| Internal (T027) | Lab run -> stage -> Commit -> Sites -> Kobo Overview -> Evidence tab -> Lab off, history stays | That the product boundary is real |
| Expert / early prospect (T028-T029) | Sites -> Kobo Overview -> Dispatch -> Finding -> drawer -> Financials (change price) | "Is this real in your operation, and would you trust it?" (roadmap 13.2) |
| Strong product (T034 + Portfolio-lite) | Portfolio (three sites) -> Kobo -> Finding -> money -> Action -> Verification -> Lab proof | The closed loop, opened the way the final demo opens |
| Polished (T036) | The full section 5.1 journey | All six stories |

### 5.3 What is not early-demo material

The following stay as they are and are not shown to clients early:

- Sites index detail, Foundation Definition and Topology, the Site Findings
  and Work scoped indexes, and Runs inventory;
- Lab setup, the picker, run history, and the cockpit beyond the final reveal;
- Incidents, Maintenance and Reports.

---

## 6. Implementation And Task Impact

### 6.1 Stay as they are (position and outcome)

- **T029A, before T034.** This is the minimal immutable-intervention
  mechanism. It is Lab-side and enables the verification story.
- **T026A** stays unscheduled and gates nothing.
- **T034's position** directly after T029A. Its UI outcome is sharpened in
  6.2.
- The **demo-point table** in `tasks/README.md`, extended by Portfolio-lite
  (6.4).

### 6.2 Same position, UI and content outcome changes

- **T027, Commit -> ingestion -> Site Overview.** Keep every acceptance
  criterion, because this is a protected seam. Change what the screen
  delivers:
  - (a) The evidence inspector lands as **Site > Evidence**, a tab
    destination showing accepted source records with three timestamps and
    per-capability coverage, rather than an inspector of its own.
  - (b) The Overview is built in the v6.9 8.18 frame, with domain cards from
    the mini-grid descriptor. Cards show measured metrics and coverage, and
    Unknown wherever no assessment exists.
  - (c) The Sites index gains Last analysed and Evidence coverage, and
    becomes the landing page in place of `Operator home`.

  Planner note: T027 is large. Phase it as (1) Commit, ingestion and the
  Evidence tab (demonstrable: "Lab off, history stays"), then (2) the Overview
  composition and the Sites columns. Each phase ends in something visible.
- **T028, the dispatch Finding.**
  - Performance becomes a destination with a **Dispatch** subtab only.
  - **Findings** enters the rail with its global index.
  - Finding detail ships Overview, Evidence (drawer) and Alternatives as
    tabs. Recommendation and History are labelled in place until T034.
  - Site > Findings becomes a scoped index.
  - The Overview's Dispatch card shows a real assessment.
  - The Sites index gains Assessment and Top issue.

  The carried question about whether stop-60's policy change appears as a
  policy record stays with T028.
- **T029, bounded financials.**
  - **Site > Financials** becomes a destination with Overview and Assumptions
    subtabs. Assumptions are editable in the UI, because changing the price
    live is the demo moment.
  - The Finding's consequence panel and the Overview's value line read the
    same model.
  - **Add:** a reproducible demo seed for point 2. It loads one Kobo site,
    commits a healthy window and a prolonged-runtime window, is idempotent,
    and is checked with the gate off and rehearsed. Today only T036 (AC15)
    has a seed, so point 2 would be staged by hand.
- **T034, policy action and verification.**
  - The Finding's **Recommendation** tab leads to Accept, which creates an
    **Action** root (Actions enters the rail).
  - The Action ships Overview and Verification, with Plan, Execution, Evidence
    and History labelled in place.
  - The accepted change appears on **Foundation > Changes**.
  - Site > Work becomes a scoped index with Actions only.
  - The Finding's History shows verification and reopening, and the Findings
    index gains its "Awaiting verification" lens.
- **T036, portfolio and client demo.** Rescope it to *completing* a Portfolio
  that already exists:
  - add the remaining sites;
  - add global Financials and Evidence roll-ups only if the six-site walk
    needs them;
  - build the Lab truth-versus-inference reveal;
  - write and rehearse the walkthrough.

  Its acceptance criteria are otherwise unchanged.

### 6.3 Move

- **T025h moves later, to after T029** (or into a Lab-ergonomics bucket
  alongside the delta-latency performance task carried from T025e and T026).
  - *Why:* it improves run setup for developers; a client never sees it.
    Template-version drift can be avoided for the demo by having the seed
    create v3 sites.
  - *Its pending ruling:* whether the status depends on the whole form or
    only on (scenario, profile). This can wait until T025h is scheduled. If
    the owner wants it settled now, the spec's whole-form reading is the
    honest one: a preview of Create must depend on everything Create reads.
    Ruling either way costs nothing.
- **Post-T034 order: proposed default F, then E, then service, then G.** In
  task ids that is T031 -> T032 -> T030 -> T035 -> T033. Today's order is
  T030 -> T031 -> T032 -> T033 -> T035.
  - **Opportunity (T031/T032) first.** It is the only story that is not a
    loss, and it is the most different from dispatch: it turns the client's
    question from cost to growth. Fuel reconciliation is a second loss story
    with the same shape as dispatch, so it adds the least new persuasion per
    slice.
  - **Service (T035) before battery (T033).** Unserved customers are an
    operator's first concern, and T033 is already the named first deferral.
  - *Prerequisites the Planner must check:*
    - T031's stated T030 dependency appears to be ordering only.
    - CODE_STATE T026 records that **no shipped world curtails PV yet**.
      T031 must own a curtailing world, or its headroom story has nothing to
      find.
  - This order remains **subject to the T028/T029 expert feedback**, as
    `tasks/README.md` already requires.

### 6.4 New

- **Portfolio-lite, directly after T034.**
  - **What it is:** a thin Portfolio command center becomes the landing page.
    It ranks Findings with their consequence and basis, and has attention and
    evidence-gap lenses.
  - **Which sites:** at least three whose stories exist by then:
    - Meki, the healthy reference;
    - Kobo, prolonged runtime and verified;
    - one evidence-limited site, built from T026's
      `kobo-mini-grid-degraded-evidence` scenario, so the claim ceiling shows
      at portfolio level.
  - **Already planned work it pulls forward:** the priority rule and the
    no-fake-total rule from T036 AC4-AC6. Each later story slice then adds
    its site and its lens content to this page.
  - **Why it is worth adding:** the strong product demo then opens the way
    the final one does. Every later slice changes the first screen a client
    sees, instead of all of that arriving at T036.
- **No other new tasks.** The archetype descriptor is a placement rule
  (4.3), and the demo seed is folded into T029.

### 6.5 Defer

- **T025h** (see 6.3).
- **The delta p95 performance task.** Run it before the T036 rehearsal only
  if the reveal's playback visibly stutters.
- **L3 cockpit enrichment** (C7-C9), until after T036.
- **Replay mode** and a broad source-health dashboard.
- **Global Evidence, Financials and Reports pages**, unless T036 needs them.
- **Incidents and Maintenance** indexes and subtabs.
- **Asset Warranty**, and any asset inventory beyond the battery.
- **Cold-chain and e-mobility** implementation, and any pack registry.
- **Any Foundation editing** beyond the T034 change record.

---

## 7. Near-Term Proposed Sequence

| Step | Slice | What the client can newly see |
| --- | --- | --- |
| 0 | Owner rules on section 8; Planner updates queue and roadmap; T025h parked | (none) |
| 1 | T027 phase 1: Commit, ingestion, **Site > Evidence** | A site's history is real: accepted records, three timestamps, and coverage that survives the Lab being off |
| 2 | T027 phase 2: **Mini-grid Site Overview** + Sites columns + Sites as landing | A site page that answers "how is it operating?" from evidence. **Internal architecture demo.** |
| 3 | T028: **Dispatch -> Finding -> evidence drawer**, Findings in the rail | The first conclusion a practitioner can challenge |
| 4 | T029: **Site Financials** with live assumptions + demo seed | **First highly useful demo** (expert and early prospect): one site, one strong Finding, its evidence, its money. *Feedback checkpoint; reassess steps 8-11.* |
| 5 | T029A: frozen intervention (Lab) | Technical: a policy change alters the simulated world from a declared time |
| 6 | T034: **Recommendation -> Action -> Foundation Changes -> Verification**, Actions in the rail | Detect, explain, monetise, intervene, verify |
| 7 | **Portfolio-lite** (new) | **Strong product demo**, opening on the Portfolio: three sites, a ranked Finding with its value, an evidence-limited site, a verified action |
| 8 | T031 -> T032: Desta headroom, Opportunities lens, paired comparison | Growth: unused renewable capacity and a trial load |
| 9 | T030: Genda fuel reconciliation | Accountability: a residual with uncertainty, record versus physical delivery |
| 10 | T035: Bahir service and backup failure | Reliability: unserved energy and a backup chain with missing links |
| 11 | T033: Arsi battery trajectory, Health tab and Assets | Asset value: stress trajectory and bounded replacement exposure |
| 12 | T036 (rescoped): six sites complete, Lab truth-vs-inference reveal, rehearsal | **Polished client demo** |

Steps 8-11 each add a site, which appears on the Portfolio as it lands, so
each one is demonstrable as a new opening-screen story and not only as a deep
page.

---

## 8. Decisions For The Owner

Only decisions that change navigation ownership, domain structure, the demo
story or sequencing.

- **D1. Root navigation growth.**
  - **Proposal:** Findings joins the rail at T028, Actions at T034, Portfolio
    becomes the landing page at Portfolio-lite, and Assets joins at T033.
    Global Evidence and Financials, Incidents, Maintenance and Reports stay
    out of the demo rail.
  - **Consequence:** the rail grows to four or five canonical items rather
    than ten. The model is unchanged.
- **D2. Add Portfolio-lite after T034, and rescope T036 to completing it.**
  This is the largest sequencing change here. It also needs one extra site
  (Meki, the healthy reference) before the other stories exist.
- **D3. Demo story order.** Kobo's intervention and verification follow
  Kobo's money directly, with opportunity and lifecycle afterwards as
  breadth. Roadmap section 5 orders it the other way.
- **D4. Default post-T034 order:** T031 -> T032 -> T030 -> T035 -> T033, to be
  revisited after expert feedback. Confirm it as the default, or keep today's
  E-F-G order.
- **D5. Domain seam.** Accept a static archetype descriptor for mini-grid
  only, with cold-chain and e-mobility tested on paper and no pack
  framework. Also confirm that **no cold-chain screens are in the polished
  demo**, so that roadmap section 8 and PRODUCT.md's deferral stand. If the
  client audience includes cold-chain buyers, that is a different decision
  with its own slices.
- **D6. T027's UI outcome.** The evidence inspector becomes Site > Evidence,
  and the Sites index replaces `Operator home` as the landing page. This
  moves Evidence from labelled-in-place to a destination two slices earlier
  than the original order implies.
- **D7. Intervention ownership in navigation.** An accepted policy change
  appears both as an Action (with verification) and on Foundation > Changes
  (as the world record). This touches the 2026-09-13 position that
  configuration is fixed at creation. Under the proposal Foundation still
  takes no direct edits: changes arrive only through an accepted Action.
- **D8. Park T025h**, and its pending ruling with it, until after T029.

---

## Self-Check Against The Request's Quality Bar

1. **Mental models, not features.** Yes. The rail shows the four classes a
   manager uses (where to look, which site, what's wrong, what we did). Six
   canonical classes wait for content or a pilot.
2. **Global versus contextual.** Yes. Section 2.2 places every named concept,
   and Findings, Financials, Evidence and Work each get an explicit
   global-versus-site treatment.
3. **Hierarchy serves the promise.** Yes. Each hero page's first item is a
   bounded operational or economic claim with its basis, and evidence is
   always one click away.
4. **Coherent for mini-grid and cold-chain.** Yes. The same frames carry
   different domains, subtabs, consequences and verification templates (4.2).
   E-mobility shows where the seam's edge is.
5. **Domain differences visible.** Yes. Overview domains, Performance
   subtabs, consequence types and claim limits differ per domain, and product
   exposure is a chip, not a card.
6. **Demo value early.** Yes. A canonical client surface lands at every spine
   step, and Portfolio-lite brings the opening screen forward to step 7.
7. **Canonical concepts reused.** Yes. There are no new object classes.
   Opportunities are a lens, the comparison is a drill-down, and the descriptor
   is configuration of existing frames.
8. **Low-value purity off the critical path.** Yes. T025h is parked, the
   performance task deferred, and there is no pack framework or naming work.
   Ingestion acceptance criteria are kept as protected seams, not polished.
9. **Each slice demonstrable.** Yes, with one exception: step 5 (T029A) is
   technical, which is accepted because it directly enables step 6.
10. **Intelligence, not monitoring or CMMS.** Yes. Ranking is by
    consequence-bearing Findings, Verified is kept distinct from Completed,
    and Incidents, Maintenance and Reports are kept out of the demo rail.
