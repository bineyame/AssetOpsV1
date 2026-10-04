# T028 presentation: revised Architect decision

Codex Architect, 2026-10-04, under `.ai/ROLE_CONFIG.md`. This implements the
owner's [presentation direction](owner-T028-presentation-direction-2026-10-04.md)
and supersedes the expandable-details-only approach in
[my audience decision](T028-architect-audience.md).

**The default experience will assume little technical knowledge.** It will
explain what happened at the site, why it matters, what remains uncertain and
what to check next, using short sentences and labelled graphics. A separate
**Analysis** tab will provide the technical explanation. Moving technical text
into a collapsed section is no longer sufficient.

For a possible avoidable-operation Finding, the first reading should be:
“The generator may have operated longer than needed. The reported solar and
battery capability supported this conclusion for part of the period. Here is
when, the estimated fuel associated with that part, and what needs checking.”
The actual assessment supplies the time, quantity, reason and qualifications.
An uncertain part stays visibly uncertain; no graphic turns possible fuel
consequence into proven savings or an instruction to stop equipment.

The product will talk about **a site and its operation**. It will not ask the
reader to understand a simulation, a run, a binding or how AssetOps is built.
That rule applies to Analysis and Evidence as well as the default page.
Technical depth means a deeper explanation of the site's operation, not a
return to development terminology. Lab screens retain their own vocabulary.

**This belongs in T028 before merge.** It is a bounded presentation revision
over the existing assessment: three contextual Analysis destinations, shared
graphics, clearer copy and a vocabulary check. T029 still owns money and the
prepared external demo; T034 still owns recommendations, action and verification.
We will reuse the interrupted correction's useful work rather than restart it.

I do not need the owner to weigh in again before implementation. The owner
has supplied the direction; the choices below implement it within the existing
product boundaries. Normal owner UI acceptance remains required, especially
whether the first reading makes sense without an engineer narrating it. This
record neither supplies that acceptance nor claims practitioner usefulness
has already been demonstrated.

The implementer-facing specification follows. Existing assessment correctness
and evidence-isolation requirements remain in force.

## 1. Page content and ownership

| Surface | Default reading | Deeper analysis and its destination |
| --- | --- | --- |
| Finding detail, **Overview** | Site, generator, readable period/timezone; one bounded conclusion and its main reason; the assessed-period chart; operating-time portions; confidence in words with its principal limitation; estimated associated fuel range or why it cannot be estimated; the relevant information to confirm next. Other possible explanations that materially limit the conclusion remain named here. | New **Analysis** tab: selected-period inputs, operating rules and reasons, detailed confidence explanation, coverage, duration/fuel calculation and assumptions, method version and assessment references. **Evidence** remains the claim-to-source-record trail and drawer; **Alternatives** remains the evidence for other possible explanations. |
| Performance > **Dispatch**, local **Overview** | “Was the generator needed?” followed by assessed periods in time order, each with a plain outcome, period, operating-time bounds, main reason or missing information and a labelled timeline. Selecting a period shows its concise explanation. Necessary periods stay here without a Finding; candidate and uncertain Findings link to their detail. | Local **Analysis** tab for the selected assessment, sharing the Finding's analysis component. This is essential for Necessary periods, which have no Finding. Include technical comparisons, reasons, coverage and links to source records. Do not create a separate assessment or a new Finding for navigation convenience. |
| Site Overview, **Dispatch card** | One plain outcome and reason, explicitly for the backend-selected assessed period. Show its affected operating time, compact timeline and the associated fuel range when supplied, or an honest unavailable state. Do not turn this into a site-wide verdict. Existing other-domain cards and the site's evidence-based energy context retain their meanings. | “View analysis” links to that Finding's **Analysis**, or Dispatch's **Analysis** for a Necessary assessment. The card has no tab strip. It does not duplicate the detailed charts or invent a site total. |
| Global and Site **Findings indexes** | A short, meaningful Finding title/summary, site where relevant, assessed period, plain outcome and confidence/important limitation. Put the operational meaning ahead of type codes and revision counts. Retain the existing filter and row destination. No severity, financial ranking or health score is invented. | A secondary “View analysis” link opens the same Finding's **Analysis**. The main row link still opens Overview. There is no index-wide Analysis tab: the index owns selection, not another analysis. No chart is required in every row. |
| Site > **Evidence**, local **Overview** | “What can we assess from this site's evidence?” One row for each existing assessment capability, its Full/Limited/None meaning, conditional conclusion available and missing information that limits it. Show the assessed-period count and the special zero-period qualification. Below it, retain a compact source-status and selected-window coverage summary, using ordinary language. | Local **Analysis** tab: readiness method/version and required/optional evidence, detailed source health and signal coverage, the coverage graphic described below, configuration/record-interpretation references and rejected-record reasons. Existing source-record inspection remains accessible from both views. Links to a particular assessment preserve its identity and period. |

Finding Analysis explains **how the conclusion follows from the inputs**;
Evidence establishes **which records support it**; Alternatives explains
**what else could account for it**. Analysis links to those tabs instead of
copying their complete lists. A short limitation can appropriately appear on
Overview and link to its full explanation elsewhere.

The common default reading must include the distinctions between observed
facts, an inferred conclusion and a calculated estimate. Keep those distinctions
in natural sentences and labels; the six numbered sections of the prior
presentation are not a mandatory layout. Compact grouping and graphics replace
that report-like structure. Detailed method mechanics move to Analysis;
material uncertainty does not.

Use the existing equipment display name where available; otherwise say
"Generator" and leave its exact device ID in the source references. Format
times consistently in explicit UTC for T028, as the current correction does;
do not infer a site's timezone from the browser or its name. Site-local time
can follow when an authoritative site timezone exists.

Site Evidence's capability assessment remains **site-wide**, over accepted
evidence and current assessment revisions. Its source/coverage section remains
**selected-window** information. Label these scopes separately in both views.
A changed window must not silently change or relabel the readiness scope.
Full means neither continuous/current coverage nor good site operation. Zero
assessed periods must say that records exist but period coverage has not yet
been assessed. An empty or unassessed site gets a stated absence, never a
healthy badge, zero-loss conclusion or empty success chart.

## 2. Graphics to build in T028

Use ordinary reusable chart components, SVG or existing UI primitives. No
generated bitmap, decorative site illustration, live animation, topology
diagram or new charting platform is needed. The following four small graphics
are sufficient; they are views of backend facts, not new analytics.

| Graphic and placement | Backend data and rendering contract |
| --- | --- |
| **Assessed-period timeline**: Finding Overview; each Dispatch period; compact form on the lead Dispatch card; selectable detail in Analysis | Use `segments[].start/end`, `classification`, `observed`, interval boundaries/open flags and `assessed_window`. Plot actual time widths on a labelled time axis. Three plain legend labels: “Needed,” “Possibly avoidable,” “Cannot determine.” Distinguish unobserved time with hatching and text. Bracketed uncertainty around start/stop is separately patterned, never painted as observed or avoidable. Open ends have an open-ended marker and explanation, not a fabricated end time. |
| **Estimated fuel range**: Finding Overview and its Analysis | Use `fuel.low_litres/high_litres`, status, basis and associated duration. Show a simple horizontal low-to-high interval with both numbers and litres; no midpoint estimate or probability distribution. Label it “Estimated fuel associated with possibly avoidable operation.” The adjacent note says this is an estimate, not confirmed fuel savings. For unavailable or not-applicable fuel, show the backend reason instead of a bar at zero. |
| **Reported values used for this period**: Finding/Dispatch Analysis, for one selected segment | Separate horizontal kW bars for site demand, available solar power, battery output capability and generator output, from `inputs.at_start` or `at_end`; allow switching between the two supplied sets. Use a common zero-based kW scale, explicit values and missing markers. Below, show battery charge and minimum reserve on their own 0–100% scale. Do not stack capabilities as actual supply, subtract them to invent surplus, or draw a power-flow diagram. |
| **Evidence coverage by input**: Finding/Dispatch Analysis; Site Evidence Analysis for a clearly selected assessment | Use `coverage.inputs[].usable_segments/evaluated_segments` for horizontal count bars, with named gaps alongside, plus the separately served unobserved-generator spans. Label the denominator “assessed parts of this period,” not elapsed-time percentage. Show readiness's own limiting/non-limiting gap statements separately. Zero evaluated parts means “Not assessed,” not 0% or 100%. Site-wide readiness never becomes a time-coverage gauge. |

Timeline selection must also be possible through a keyboard-accessible list
or table with the same labels, times and reasons. A selected part opens the
appropriate Analysis context; hover is supplementary. Use text and patterns
as well as colour. All graphics have a readable equivalent, units, period,
timezone and a caption identifying reported evidence versus assessed result.
On narrow screens, preserve the labels and table alternative rather than
shrinking text into illegibility.

Two boundaries matter for honest graphs:

- `portions_hours` contains different bounds, not an exact partition to put in
  a pie chart. Display those backend quantities as labelled values. Do not add
  their upper bounds into a new total or interpret a `low` without `high` as a
  supplied upper bound. Timeline widths represent the supplied assessment
  segments; they do not override the separately displayed duration bounds.
- Segment inputs are values used by the assessment, not a continuous telemetry
  series. Policy changes can split a segment while reusing the original
  reports. Label the comparison “Values used at the start/end of the assessed
  part”; do not plot those values as fresh samples at the split timestamp.
  Source times remain in Evidence. Missing inputs have no bar, not a zero bar.
  No smooth interpolation, carried values across gaps, energy integrals or
  counterfactual “generator off” curve is permitted in this slice.

The existing Site Overview energy chart continues to use its ordinary backend
evidence read model. New assessment illustrations use only the assessed data
above. No chart reads Lab series, scenario settings, private state, a recipe
name or an expected outcome.

## 3. Tabs, navigation and the explicit amendment

**Amend AC21 and the Finding-tab clause of
`D-2026-10-02-rendered-tabs-per-capability`.** At T028 the Finding tab order is
now **Overview | Analysis | Evidence | Alternatives**. Recommendation and
History still wait for T034. This supersedes the previous three-tab inventory
and my decision's requirement to preserve the existing navigation unchanged.
The owner has authorized the additional destination.

Performance still has **Dispatch as its only capability subtab**. Inside it,
render **Overview | Analysis** as contextual views, not as new capabilities.
Site > Evidence similarly has **Overview | Analysis**. These view pairs are
real content destinations, not a persisted user persona or an application-wide
expert mode. Cards and indexes link into them rather than growing tab strips.

This preserves the per-capability rule: an implemented analysis view renders
on applicable sites even if they lack evidence, with a useful empty state.
Do not hide Analysis because a selected site is empty or has no candidate
Finding. No placeholder for future analytics is introduced. Under
`D-2026-10-02-grammar-ownership-test`, these views own method/interpretation
detail removed from their default view; they do not create another object or
source of truth. Record the placement explicitly in the decision log.

Finding Analysis has the existing Finding route plus `/analysis`. Dispatch
and Site Evidence can use their existing routes with `view=analysis`; retain
the selected `interval`, window and record parameters. Missing view defaults
to Overview. Preserve old Overview/Evidence/Alternatives links, browser Back
and reload. Record links continue to open the existing inspector/drawer in
the current root; adding Analysis must not force navigation to the Lab.
When a selected assessment is unavailable or retired, state that accurately
and offer the existing route to current results, rather than silently
substituting another period.

The coordinator/Planner must amend T028 AC21, its phase/check descriptions and
the affected tab inventory references before implementation is reviewed against
them. Also amend the recommendation's literal Finding hierarchy/tab references
where used as an acceptance oracle. This specification is the replacement
direction; old three-tab and disclosure-only tests must change accordingly.
This Architect pass does not edit those files.

## 4. Product vocabulary and the guard

Apply the vocabulary rule to application-authored visible text, chart labels,
accessible names, tooltips, empty/error states and backend-served explanations
on **all operator/product surfaces, including Analysis and record drawers**.
It does not rename domain keys, APIs, stored evidence, URLs, test identifiers,
logs or Lab controls. Default wording also spells out specialist abbreviations.

| Avoid in product copy | Use instead, according to the actual meaning |
| --- | --- |
| run, runs, runtime, “run the assessment,” “generator ran/running” | assessed period; generator operation/operating time; update assessment; generator operated/is operating. Never rename a simulator run into an operational event. |
| binding, bound input, binding constraint | setting/source association where appropriate; “reason the generator was needed” or the named operating limit. Preserve “lower/upper estimate” and uncertainty; the ban does not remove quantity bounds. |
| scenario, recipe, Draft, Commit, staged envelope, execution, world state, oracle, kernel, tick, projection, replay, model/publication profile | Omit the development workflow. Where there is real product content, use site records, received records, observation time, recorded operating settings or assessment method. There is no product synonym that authorizes showing private state. |
| backend, frontend, read model, payload, analytic declaration, basis digest | Omit implementation narration. Use assessment, evidence requirements, record details or verification reference as appropriate. A method/version reference can remain in Analysis. |
| claim, claim ceiling, candidate avoidable, indeterminate, necessary | conclusion; “what this evidence can establish”; “Possibly avoidable”; “Cannot determine”; “Needed.” These are display labels for the existing backend states, not new states or stronger claims. |
| PV, SOC, PCS, discharge capability, load, reserve policy (unexplained on default views) | solar power; battery charge; battery power converter; available battery output; site demand; minimum battery reserve. Analysis may add the abbreviation after its plain meaning. |
| source envelope, ingestion, mapping basis, receipt timestamp | source record; records received/accepted; record interpretation; time received. Preserve the distinction between observed, sent and received times. |

The first four rows prohibit simulation/implementation terminology in authored
product prose; the remaining rows specify the plain display vocabulary. These
are contextual replacements, not permission to rename an internal object and
expose it as an operational fact.

Use “other possible explanations” in copy around Alternatives; status wording
can be “Supported by records,” “Still possible” and “Not supported by the
available records,” mapped to the existing statuses with their scope intact.
Do not promise that an explanation has been globally disproved. Full/Limited/None
remain evidence-sufficiency labels, with plain meanings beside them; no traffic
light labelled “healthy” or “safe” is substituted.

The examples deliberately avoid even the legitimate engineering use of
“runtime” and “binding constraint,” because the owner named that confusion.
The same principle covers older stored assessment text. Do not merely move
old strings into Analysis or perform a blind word replacement in arbitrary
sentences. Generate the product reading from the stored structured assessment,
including reasons, limitations and alternatives, preserving its meaning.

**Presenting a real site object does not change the origin of its evidence.**
Retain a quiet, accurate source-mode disclosure such as “Demonstration data”
where the source metadata establishes that origin, with provenance inspectable
in Evidence. Do not label generated observations as field measurements or
rewrite immutable records to remove origin. Exact source-owned identifiers
may remain in clearly labelled reference fields; they are not product prose.
This does not add a simulation workflow to the operator view.

**Add a small guard in T028.** Check rendered application-authored text and
accessible labels on the five specified surfaces, including their Analysis,
Evidence, Alternatives and drawer states, against a versioned forbidden
word/phrase list covering the table's implementation/simulation terms. Include
backend-generated text and error/empty states; scanning JSX literals alone
would miss the current `dispatch.py` explanations. Use word boundaries so
`run` does not match an unrelated substring. Give failures the page and phrase.

Exclude only Lab surfaces, opaque source-owned reference values and user-owned
names/notes; do not exclude entire evidence panels or backend responses.
Keep any exact exception named and justified. Include a failing-example proof
that a forbidden phrase delivered by the backend is caught and that Lab/source
references are not rewritten. The guard is a regression aid; a human must
still check plain meaning, uncertainty and claim strength. It is not an NLP
project or a reason to rename every internal symbol in the repository.

The vocabulary direction is product-wide. T028 enforces it on its full journey
and shared shell/record components encountered there. Other product surfaces,
including Foundation, follow the same rule; remaining legacy copy is inventoried
as a named follow-up after T029 rather than expanding T028 into a repository-wide
redesign. No blanket exception permits new implementation language elsewhere.

## 5. Data boundary, delivery cuts and verification

The current read models already contain segments, endpoint inputs, coverage,
fuel bounds, confidence, alternatives and `reading`. Extend their presentation
projection only as needed: plain display labels/reasons, concise limitations,
the compact timeline/fuel projection on the lead Overview card and links to
the matching assessment. Use the same assessment ID and revision everywhere.
For Site Evidence's selected-assessment graphic, read the existing dispatch
assessment, label that scope and keep it separate from site-wide readiness.
Index views need no bulk fetch of full assessments just to display charts.

Backend projections own semantic summaries, conditional investigative next
steps and any new aggregate quantity. The frontend owns formatting, chart
geometry, selection and layout. It must not calculate a new classification,
confidence, coverage score or fuel bound. Plain labels may be presentation
mappings, consistently used with the backend's display fallback for unfamiliar
capabilities. Do not display an internal identifier as a fallback explanation.
Missing presentation detail should be a clear unavailable state, not an
unqualified generic candidate story.

Keep historical assessments immutable. Read-time presentation of an existing
revision can improve without creating a new analytic revision or changing
`dispatch-2`/`readiness-3`; keep the original model and evidence references.
A real change in classification, scoring or quantity semantics is outside
this presentation correction and must be separately identified and versioned.

Keep the work reviewable as **two sequential checkpoints on T028**, not a new
task queue or parallel implementation:

1. **Default reading and Analysis destinations.** Reuse the existing plain
   reading, time formatting and next-step work; move deeper sections into the
   specified tabs, update labels and shared backend display text, preserve
   links and evidence access. Show candidate, Necessary and uncertain cases.
2. **Shared graphics and vocabulary proof.** Add the four specified graphics,
   compact card projection, accessible interactions and the guard. Show the
   complete journey with Lab disabled, then return the combined correction
   for independent review and the owner's UI walk before merge.

Both checkpoints are required for the revised T028 result. Do not merge a
disclosure-only intermediate version as fulfillment of this direction. Do not
add another analytic, optimizer, readiness setting, site-health score, financial
ranking, new raw telemetry pipeline or recommendation workflow.

T029 retains bounded fuel/maintenance money, assumption editing and the
idempotent prepared demo, applying this same default/Analysis pattern to its
new content. T029B retains Sites ranking; T028A retains configurable gap
impacts; T034 retains action and verification; T034A retains Portfolio-lite.
Additional trend charts, comparative experiments, report exports and a broader
visual redesign wait for feedback. Nothing in this decision waits for them.

Verification should demonstrate the distinctions a reader could otherwise
misunderstand: candidate and Necessary portions together; evidence-limited
and wholly Indeterminate periods; unobserved time; open start/end; unavailable
fuel; Full readiness with a non-limiting gap; zero assessed periods and no
evidence. Verify timeline geometry against supplied times, missing versus zero
inputs, range endpoints, selected assessment consistency and unchanged analytic
outputs/revisions. Check direct links, Back/reload, keyboard access, narrow
layouts and the product journey with Lab off. Use existing cases where possible;
new checks should target these failure modes, not just count tabs or SVG nodes.

The owner walk should first use only default views: explain the outcome,
affected period, fuel estimate and its limits, and the next information to
confirm. Then open Analysis and one supporting record to challenge the reason.
Neither automated checks nor a narrated engineering walkthrough substitutes
for that first-reading acceptance.

Review basis: code at `457cf0d`, following the prior correction commits
`dec4e52`, `17b8b97` and `04c0d28`; the coordinator's documentation commit
`12fd695` arrived during this pass. Its
[paused implementation handoff](T028-presentation-handoff.md) was then read.
The existing components, backend `reading`, and
`.agent/T028-presentation-cases.txt` show reusable partial work; they do not
satisfy the new tabs/graphics direction. The handoff's passing checks describe
`04c0d28`; its interrupted layout run is explicitly not evidence, and must not
be counted as validation of either correction. Its warning about persisted
summary text is addressed by the read-time presentation projection above,
rather than rewriting historical assessments to clean up wording.
This is a source-based architectural specification, not a browser review or
test verdict. Only this file was written; existing working-tree changes,
code, tests, tasks and the decision log were left untouched. No merge occurred.

## Draft durable amendment for the coordinator

Suggested index row:

| Decision | Date | Summary |
| --- | --- | --- |
| `D-2026-10-04-plain-language-analysis-views` | 2026-10-04 | Owner-directed plain-language defaults, assessment graphics and separate Analysis tabs in T028; amends practitioner-first presentation and the Finding tab inventory; product vocabulary guard. |

### 2026-10-04

Decision: `D-2026-10-04-plain-language-analysis-views`.
Codex Architect, implementing the owner's direction recorded in
`.agent/owner-T028-presentation-direction-2026-10-04.md`; specification and
reasoning in `.agent/T028-architect-presentation.md`.

Amends `D-2026-10-04-practitioner-first-finding-presentation`: operator defaults
assume minimal technical knowledge and communicate operational meaning,
affected time, uncertainty, bounded consequence and investigative next steps
with plain text and labelled graphics. Deeper method, inputs, coverage and
calculation belong in a separate Analysis destination, replacing the earlier
disclosure-only correction and mandatory report-like layout. Important limits
remain visible with the default conclusion.

Amends the Finding-tab inventory in
`D-2026-10-02-rendered-tabs-per-capability` and T028 AC21 to
`Overview | Analysis | Evidence | Alternatives`. Recommendation and History
remain T034. Performance keeps Dispatch as its sole capability subtab, with
local `Overview | Analysis`; Site Evidence has local `Overview | Analysis`.
Cards and indexes link to the matching analysis rather than duplicating it.
These contextual views own interpretive detail; Evidence retains source
lineage and Alternatives retains competing explanations, satisfying
`D-2026-10-02-grammar-ownership-test`. Per-capability rendering and truthful
empty states remain unchanged.

T028 delivers a shared assessed-period timeline, bounded fuel-range graphic,
selected-period input comparison and coverage-count graphic from backend-served
assessment data only. No private simulator data, interpolated telemetry,
invented savings or new analytic conclusion enters the presentation. Backend
semantic ownership and persisted assessment history remain unchanged.

Product copy, including Analysis and Evidence, uses operational language and
excludes simulation/development terms such as run and binding. Lab vocabulary
is excluded from this restriction. A focused rendered-text guard covers the
T028 journey, with explicit exceptions only for source-owned references and
user-owned text. Stored identifiers and provenance remain intact; demonstration
data is not represented as field evidence. Remaining legacy product copy is
assigned a follow-up after T029, without allowing new jargon in the meantime.

Both presentation checkpoints land in T028 before merge. T029 retains money,
assumptions and the prepared external demo; T034 retains recommendations,
action and verification. The evidence-sufficiency scope and limits in
`D-2026-10-04-analytic-readiness-scope-and-gap-impact` are unchanged. This
decision records architecture direction, not owner slice acceptance.
