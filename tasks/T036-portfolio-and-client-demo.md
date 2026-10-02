# T036 - Independent portfolio and complete client demonstration

Status: planned
USER_REVIEW_REQUIRED: true
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).

Map: I completion; the full portfolio and polished client demo (point 4).
Depends on: T027-T035, T034A (Portfolio, Meki and the evidence-limited site),
T025i and completed A.
Delivery order: last, after T025i. T026A is deliberately not a dependency: no criterion
below needs gateway outage or recovery, and criterion 12's claim-limited case
uses the gap and delay T026 already delivers. Add T026A as a prerequisite only
if this demo is deliberately built to include gateway-outage recovery as a
proof story.
Branch: task/T036-portfolio-and-client-demo
Sizing: completion of an existing Portfolio, the Lab reveal and rehearsal.

## Outcome

Completes a Portfolio that already exists (T034A) and to which each breadth
slice added its own seeded site. The six story sites and T034A's
evidence-limited site load from one seed; the walkthrough follows
recommendation 5.1 (Kobo uninterrupted from detect to verify, breadth after,
Lab last; `D-2026-10-02-demo-led-recommendation`) and ends with the gated Lab
truth-versus-inference reveal.

This composes individually credible A-H stories, not a scripted scorecard.

## Not the first client-facing milestone

This is the polished portfolio demo, not the point at which customer
conversations may begin. T027 is the internal architecture demo, T028/T029 is a
legitimate domain-expert and early-prospect demo, and T034 with T034A is the
strong product demo, already opening on Portfolio. A former mini-grid colleague does not need six sites before their
feedback is worth having. See `Docs/queue-review-feedback-verbatim.md` and
`D-2026-09-24-queue-resequenced-for-demo`.

## Read for detail

- v4 sections 17, 20, 21 and 25.
- Roadmap sections 4-5, 7/I and 13.3; its walk order is overridden by
  recommendation 5.1 (`D-2026-10-02-demo-led-recommendation`).
- `tasks/T034A-portfolio-lite.md` (Portfolio, priority rule, seed command).
- FEATURE_MAP I.
- Shared checks and exclusions: tasks/README.md.

## Acceptance criteria

1. One seed command (`D-2026-10-02-demo-point-seed-rule`) loads Meki healthy,
   Kobo prolonged runtime, Genda fuel, Bahir service/backup, Desta productive
   use, Arsi stress and the evidence-limited site, each with its own Site
   identity, frozen runs and accepted history. Meki is T034A's, Kobo T029's and
   T034's; Desta, Genda, Bahir and Arsi are seeded by T031/T032, T030, T035 and
   T033. This slice authors only the recipe of any site whose breadth slice
   did not land or did not seed it.
2. Recipes author topology/inputs/events/evidence conditions only; Findings,
   financial values and priority are computed normally.
3. Build each demo history through device -> gateway -> Commit -> normal
   ingestion. Existing user Site data remains untouched.
4-7. Moved to T034A (its AC3-AC6, with Meki's recipe). Here they are
   re-proved on all sites: every consequence type keeps its own basis in
   Portfolio's value column, with no total across types.
8. Comparison histories from T032 remain excluded from ordinary Site and
   Portfolio rows; deleting or rebuilding one demo Site does not alter another.
9. Changing a Site's accepted evidence updates its assessment/priority through
   normal queries. A stale or evidence-limited Site shows that limitation.
10. With Lab disabled, the whole operator portfolio and deep links remain.
    Private validation appears only in gated Lab.
11. Lab validation compares private trajectories/causes with independently
    computed product conclusions by run/window/evidence reference.
    It reads product output for inspection without feeding truth into analytics.
12. Validate both a successful inference and a claim-limited/degraded case.
    Removing the private comparator leaves product results unchanged.
13. Deliver the recommendation 5.1 walkthrough (overrides roadmap 13.3's
    order, `D-2026-10-02-demo-led-recommendation`): Portfolio, then Kobo
    uninterrupted (Overview, Dispatch, Finding and drawer, Financials,
    Recommendation -> Action -> Foundation > Changes, Verification on the
    seeded post-action window), then Desta Renewable and comparison, Arsi
    Battery Health, Genda Fuel (optional), and Lab proof last.
14. Check that user decisions for external financial assumptions, productive
    load choice and lifecycle exposure are recorded before external demo use.
15. Document the repeatable local demo commands, fixture identities, selected
    windows and supported limitations in the implementation review packet.
    Loading the demo twice does not double-ingest or duplicate Sites.
16. Use reloadable gated cockpit records for the final truth-versus-inference
    reveal, joined to product results by run/window/evidence reference. Private
    truth flows only into that Lab comparison. The operator walkthrough works
    with Lab off; include the successful and claim-limited cases. L3 and T026A
    remain optional.
17. Global Evidence joins the rail under ASSURANCE only if it passes
    `D-2026-10-02-grammar-ownership-test` explicitly, recorded in its own
    `DECISIONS.md` entry before it renders; otherwise it does not render.
    Rendered rail at the end: OPERATE: Portfolio, Sites, Assets; INTELLIGENCE:
    Findings; WORK: Actions; plus ASSURANCE: Evidence only on that entry.
    Site tabs stay T033's eight.

## Proof

Rebuild every seeded history from its reproducible inputs.
Validate Portfolio rows against the Site read models, then retry ingestion
and confirm stable rows. Change one Site's evidence and confirm isolation.

Run the full operator walkthrough with Lab off.
Enable Lab only for the final truth-versus-inference inspection.
Include one evidence-gap drilldown so lack of evidence is demonstrably distinct
from healthy operation or proven physical failure.

Run relevant integration/read-model/frontend tests, shared checks and
`node tools/layout-evidence.mjs` on populated Portfolio and deep routes (and
the ASSURANCE group if AC17 adds it). The carried delta p95 task
(`tasks/README.md`) runs before rehearsal only if the reveal's playback
visibly stutters.

*UI check:* on the seed with Lab off, walk AC13 end to end; enable Lab only
for the final reveal.
Human review judges whether the story is understandable and credible; automated
success cannot certify practitioner usefulness or real-world calibration.

## Scope limits

No broad portfolio administration, tenant management, general report builder or
new analytics universe. Reuse canonical Findings, Financials and Site views.
No global Financials, Incidents, Maintenance, Reports or cold-chain screens.
External publishing/contact is not authorized by implementing this task.

## Review

The owner walks the recommendation 5.1 journey and judges polished-portfolio
readiness.
Earlier external exposure was already authorized at T028/T029 and T034; this
review does not retroactively gate it.
Record actual approval and remaining claim limits; do not infer approval from
the existence of six populated cards.
Review outcome: pending.
