# T029B - Sites ranks by assessment and evidence

Status: planned
USER_REVIEW_REQUIRED: true

Map: B/C presentation; thin follow-on cut from T027/T028 to protect point 2.
Depends on: T027 (coverage), T028 (assessment, Findings), T029 (seed).
Delivery order: after T029; next T029A.
Branch: task/T029B-sites-ranking-and-landing
Sizing: normal UI/content slice (120-line ceiling); read-only composition.
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).
Created 2026-10-02 under `D-2026-10-02-demo-led-recommendation`
(`.ai/ARCHITECT_DEMO_RECOMMENDATION.md` 2.1, 6.2 "Protecting point 2", 6.4
"Thin follow-on slice").

## Outcome

Sites, already the landing since T027 phase 1, asks "which site needs
attention, and how sure are we?" instead of listing names. Four columns - Last
analysed, Evidence coverage, Assessment, Top issue - rank sites by assessment
and evidence, each linked to the object it summarises. Sites keeps the landing
until T034A Portfolio-lite takes it.

## Why this exists separately

Point-2 protection (recommendation 6.2): these items are not on the point-2
journey (Sites -> Kobo Overview -> Dispatch -> Finding -> drawer ->
Financials; the presenter opens Sites from the rail), so they moved out of
T027 and T028.

Ownership test (`D-2026-10-02-grammar-ownership-test`). **Lost if removed:**
the only cross-site view that compares assessment and evidence on one screen.
**What duplicates it:** nothing. Each cell's content is owned elsewhere for
one site (Overview card, Site > Evidence, Findings), and the global Findings
index lists Findings, not sites; neither ranks sites nor shows coverage. At
T034A Portfolio takes the landing and the ranking role; Sites stays the
index.

## Read for detail

- Recommendation 2.1 (root rail by milestone).
- `D-2026-10-02-presentation-profile-and-capability-declaration` rule 3: a
  gap is shown only from backend state.
- T027 AC10 (coverage) and T028 (assessment, Finding, capability declaration).
- Shared checks and exclusions: tasks/README.md.

## Deliver

- In `frontend/src/sites/SitesIndex.tsx` (`COLUMNS`), fill `Last analysed`
  (today `--` for every site) and add `Evidence coverage`, `Assessment` and
  `Top issue`. Each reads a backend-served model already built by T027/T028;
  no new analytic, coverage calculation or assessment.
- The landing is inherited: T027 phase 1 removed `Operator home` and redirects
  `/` to `/sites` (T027 AC23). Here, only confirm the landing still opens the
  Sites index with the new columns.
- **Rendered at the end of T029B.** Rail: OPERATE: Sites; INTELLIGENCE:
  Findings (recommendation 2.1 row "T028-T029A"). Site tabs unchanged from
  T029, six: `Overview | Foundation | Performance | Findings | Financials |
  Evidence`.

## Acceptance criteria

1. **Last analysed:** the time of the site's latest assessment revision
   (T028), linking to the assessed Overview; "Not analysed" when none exists,
   never a fabricated time.
2. **Evidence coverage:** the T027 coverage summary for the window the site's
   latest assessment used, naming any gap, linking to Site > Evidence.
   "No accepted evidence" when there is none.
3. **Assessment:** the same assessment word and one-line reason the Overview's
   assessed card shows (T028; dispatch is the only analytic), linking to the
   Overview. "No assessment yet" when none exists.
4. **Top issue:** the site's top open Finding (title and classification),
   linking to Finding detail; "No open Finding" otherwise. Within a site:
   Candidate Avoidable before Indeterminate before Necessary, then latest
   window.
5. Sites are ordered by a stated rule: a site with an open Finding before one
   without; among those, stronger claim level first (Candidate Avoidable,
   then Indeterminate), then lower evidence coverage, then name; then sites
   with no open Finding by lower coverage, then name. A site whose only open
   Findings are Necessary ranks in this last group (by coverage, then name),
   after every site with a Candidate Avoidable or Indeterminate Finding, yet
   shows its top Necessary issue (AC4). The rule is shown on the
   page and is an interim, replaced by T034A's versioned priority rule.
   Unanalysed sites are listed, never hidden.
6. Every cell reads backend state; the presentation profile cannot create a
   cell value or a gap (rule 3). The four cells for a site agree with its
   Overview, Evidence and Findings at the same moment.
7. Opening the app lands on Sites (T027 AC23 removed `Operator home`); no
   route breaks, and breadcrumbs and Back still work.
8. Lab gate off: the landing, rail and columns are unchanged.

## Proof

Frontend tests for each column's present and empty state, the ordering rule
over a fixture of at least three sites (open Finding, no Finding, not
analysed), link targets, and the landing route. Run shared repository checks
and `node tools/layout-evidence.mjs` on the Sites landing at the standard
viewports (rail now one item per group).

*UI check:* on T029's seed with the Lab gate off, the app opens on Sites; the
Kobo row shows its last-analysed time, coverage, assessment and top issue,
and each links to the same objects the point-2 journey opens.

## Scope limits

No Portfolio, lenses, KPI strip, cross-site money or priority score beyond
AC5 (T034A, with T036 AC4-AC6). No new seed; uses T029's. No change to Site
tabs, Findings or Evidence pages.

## Review

The owner opens the app cold and judges whether Sites now reads as "which site
needs attention, and how sure are we?".
Review outcome: pending.
