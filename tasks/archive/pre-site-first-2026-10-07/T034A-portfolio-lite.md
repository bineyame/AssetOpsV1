# T034A - Portfolio-lite: the strong demo opens on Portfolio

Status: planned
USER_REVIEW_REQUIRED: true
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).

Map: I, first slice; with T034, demo point 3 (the strong product demo).
Depends on: T034 (Actions, verification states, Kobo post-action seed), T029
(Site Financials consequence, point-2 seed), T029B (Sites ranking, landing from T027,
which this slice takes over), T028 (Findings, capability declaration), T027
(ingestion, presentation profile) and T026's degraded-evidence scenario.
Delivery order: directly after T034; next T031. Point 3 completes here.
Branch: task/T034A-portfolio-lite
Sizing: first cross-site read model and priority semantics, plus the point-3
three-site seed (220-line ceiling).

## Outcome

The app opens on Portfolio. One sentence states the scope (window, number of
sites, SIMULATED as provenance). Below it, Findings from three sites are
ranked, each with site, bounded claim, consequence and its basis, confidence
and action state. Attention and evidence-gap lenses filter the same list, and
"What changed" lists Findings verified, reopened or closed without proof.
Meki, healthy on adequate evidence, is visibly different from a site whose
evidence does not support an assessment.

Why next: the strong demo should open the way the final one does
(recommendation 5.1 step 1, 5.2 point 3, 6.4), and every breadth slice after
this adds its site to the screen a client sees first. Kobo's own story is
unchanged and still runs uninterrupted from Portfolio.

## Read for detail

- `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` section 3 "Portfolio Value &
  Operations", 2.1 root-rail table, 5.1-5.2, 6.4.
- Decisions: `D-2026-10-02-demo-point-seed-rule`,
  `D-2026-10-02-grammar-ownership-test` (rail),
  `D-2026-10-02-rendered-tabs-per-capability` (lenses and tabs render per
  capability), `D-2026-10-02-presentation-profile-and-capability-declaration`.
- `tasks/T036-portfolio-and-client-demo.md` AC1-AC7 (where AC4-AC7 came from).
- `config/scenarios/kobo-mini-grid-degraded-evidence.yaml` header (its gap,
  delay and missing override record) and T028's Proof table.
- Shared checks and exclusions: tasks/README.md.

## Deliver

**Portfolio read model** (backend-owned): accepted, current Site assessments
and their Findings across Sites, each Finding carrying the consequence and
basis already computed by T029 (Site Financials) and T028 (bounded fuel
quantity), its claim level and coverage, and its action/verification state
from T034. It reads existing assessments; it computes no new analytic, and
it never reads simulator or private flows.

**Portfolio page** (`/` becomes Portfolio): scope sentence, ranked Findings,
lenses, "What changed". A row leads to the Finding (root changes) or its
Site. **Rail:** OPERATE: Portfolio, Sites; INTELLIGENCE: Findings; WORK:
Actions (2.1, `D-2026-10-02-grammar-ownership-test`). Portfolio replaces Sites
as landing (set by T027, ranked by T029B); Sites keeps its ranking. **Site
tabs** unchanged at
seven: Overview, Foundation, Performance, Findings, Work, Financials,
Evidence. Anchors: `frontend/src/shell/OperatorShellLayout.tsx`
(`operatorRoutes`), the landing route T027 set, `tools/layout-evidence.mjs`.

**Seed, three sites** (`D-2026-10-02-demo-point-seed-rule`): extend the
point-2/point-3 seed command T029 and T034 own, so one command loads point 3.
Each site is a distinct Site identity created through the normal Site path
from the shipped `kobo-mini-grid-60kw` template (v3), with its own frozen
runs, Commit and normal ingestion:

- **Kobo:** T034's seed as delivered (T029 windows plus the post-action
  window). Not re-authored here.
- **Meki, healthy:** the healthy reference scenario T028 AC9 and T029's seed
  already use, on its own Site (T036 AC1's Meki recipe, pulled forward). If
  that scenario lacks observed service evidence for T036 AC7, author a Meki
  scenario document within the existing scenario contract; no new simulator
  mechanism.
- **Evidence-limited site:** a run of `kobo-mini-grid-degraded-evidence` v1
  (model profile v3, publication profile v5, per its header) on its own Site.
  T028's analytic runs on it and limits its claim: missing discharge
  capability 09:00-10:00 is a named gap, the delayed SOC is reconstructed at
  source time, the unpublished override is "none observed". Display name is
  chosen in the packet and is not one of T036 AC1's six names.

## Acceptance criteria

1. Portfolio is the landing page and the first item under OPERATE; the rail
   renders exactly OPERATE: Portfolio, Sites; INTELLIGENCE: Findings; WORK:
   Actions. Sites remains reachable with its T029B ranking.
2. The scope sentence states window, number of sites and SIMULATED mode
   from the read model, not from page constants.
3. (T036 AC4, moved) Portfolio rolls up accepted Site assessments with
   window, currency/basis, coverage and evidence-gap context; drill-through
   uses the same Site objects.
4. (T036 AC5, moved) State a transparent priority rule for attention,
   opportunity and evidence gaps. Do not rank by arbitrary scenario name or
   number of alarms. The rule is versioned, backend-owned, shown on the page
   (or one click away), and its inputs are each Finding's consequence, claim
   level, confidence and action state. Opportunity carries no weight until a
   backend opportunity capability exists (T031).
5. (T036 AC6, moved) Keep OPEX consequence, service exposure, replacement
   exposure and scenario opportunity distinct. Avoid an invented
   total-savings sum or duplicate counting across Findings. At this slice
   only OPEX consequence exists; the column states its basis (measured,
   modelled or scenario) per row.
6. (T036 AC7, moved with Meki's recipe) Meki's healthy benchmark remains
   meaningful: it has adequate evidence and observed service, not merely an
   empty Findings list.
7. A site healthy on adequate evidence is visibly different from a site that
   cannot be assessed (section 3): the evidence-limited site shows its named
   gaps and limited claim; it never appears healthy because it has fewer
   Findings.
8. Lenses render per backend capability
   (`D-2026-10-02-rendered-tabs-per-capability`): attention and evidence-gap
   render; the opportunity lens is not rendered until T031 serves an
   opportunity capability. A lens is a filter on the ranked Findings, not a
   separate list or score.
9. "What changed" lists Findings whose T034 verification is Verified or
   reopened, and Actions completed without accepted post-action evidence
   (Finding still unresolved, T034 AC11), each linked to its Action.
10. Recipes author topology, inputs, events and evidence conditions only;
    Findings, consequence and priority are computed normally (as T036 AC2).
11. The seed is idempotent: loading twice neither double-ingests nor
    duplicates a Site; rebuilding one seeded Site does not change another's
    assessments or Portfolio rows. It is checked with the Lab gate off.
12. Changing one Site's accepted evidence (for example rerunning the
    evidence-limited Site's analytic after a delayed record) updates its
    Portfolio rows through normal queries, with no page-side recomputation.
13. Kobo's journey from Portfolio (Kobo Overview -> Dispatch -> Finding ->
    drawer -> Financials -> Action -> Verification) is unchanged from T034.

## Proof

| Case | Required result |
| --- | --- |
| Fresh database, seed once | Three Sites; Kobo Finding ranked with its consequence and basis |
| Seed again | Same Sites, same rows, no duplicate accepted facts |
| Meki | No material Finding; adequate coverage and observed service visible |
| Evidence-limited site | Limited claim, named capability gap, "none observed" override |
| Lens: evidence gaps | Evidence-limited site's limitation; not Meki |
| Change price in Kobo Financials | Kobo's consequence and rank update; physics unchanged |
| Rebuild evidence-limited Site | Kobo and Meki rows unchanged |
| Lab gate off | Whole page and deep links work; no private value anywhere |

Test the priority rule on hand-built read-model rows (a higher consequence
with a weaker claim against a lower one with a strong claim) so the ordering
is explained, not just observed. Run backend read-model and frontend
navigation tests, shared checks, and `node tools/layout-evidence.mjs` on
Portfolio, the rail (OPERATE now holds two items; INTELLIGENCE and WORK one
each), and one deep Finding route.

*UI check (point 3 from Portfolio, recommendation 5.2):* open the app on the
seed with Lab off. Portfolio lands with three sites, a ranked Kobo Finding
with its value and basis, and an evidence-limited site visibly distinct from
healthy Meki. Then walk Kobo -> Finding -> money -> Action -> Verification,
and Lab proof last. Document the seed command in the packet.

## Scope limits

No global Financials, Evidence, Assets, Incidents or Reports. No new
analytic, no opportunity lens content, no portfolio totals across
consequence types. No new simulator mechanism or template. Remaining sites
arrive with their breadth slices (T031/T032 Desta, T030 Genda, T035 Bahir,
T033 Arsi); T036 completes the six and the walkthrough.

## Review

The owner opens the app on the seed and judges whether Portfolio opens the
strong demo credibly: is the ranking explainable from the rule, does the
evidence-limited site read as "we cannot say" rather than "fine", and does
Kobo's story still run uninterrupted. The Reviewer checks that no page code
ranks, totals or infers what the read model does not serve.
Review outcome: pending.
