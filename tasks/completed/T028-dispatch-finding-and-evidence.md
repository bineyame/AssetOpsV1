# T028 - First dispatch Finding with challengeable evidence

Status: done
USER_REVIEW_REQUIRED: true

Map: C; earliest domain-expert feedback checkpoint, and with T029 the first
external demo point (demo point 2).
Depends on: T027 (both phases), T025 healthy/prolonged-runtime recipes and T026
evidence.
Next: T029 after this checkpoint; reassess later work from feedback.
Branch: task/T028-dispatch-finding-and-evidence
Sizing: first analytics/Finding semantics; three phases in one file.
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).

## Outcome

Site Overview -> Performance/Dispatch -> Finding Detail -> Evidence explains a
generator interval classified Necessary, Candidate Avoidable or Indeterminate.
The practitioner can inspect constraints, coverage, confidence, alternatives,
claim limits and an indicative bounded fuel quantity. Site > Evidence gains the
capability table saying what AssetOps can claim from the accepted records.

This is the first valuable Finding. It precedes fuel reconciliation and does
not require priced Financials or a portfolio.

With T029 this is a legitimate external-feedback and early-prospect demo, not a
rehearsal for one: one site, one strong Finding, its evidence and its money is
enough to learn from a real operator. `Docs/queue-review-feedback-verbatim.md`
says waiting for the portfolio wastes the feedback.

## Read for detail

- Roadmap sections 3.3, 4, 7/C and 13.2; FEATURE_MAP C.
- v4 sections 3, 11-12, 17 and 25 for evidence/recipe boundaries.
- `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` 3 "Finding Detail"/"Evidence", 4.3, 6.2.
- Decisions: `D-2026-10-02-presentation-profile-and-capability-declaration`,
  `D-2026-10-02-rendered-tabs-per-capability`,
  `D-2026-10-02-grammar-ownership-test`.
- Shared checks and exclusions: tasks/README.md.

## Deliver

Reconstruct DispatchInterval from accepted generator, PV, BMS, meter and
time-valid policy evidence. Evaluate whether the observed operating constraints
support generator necessity or a bounded candidate-avoidable interpretation.

Build one canonical Finding presentation with supporting evidence, competing
explanations, confidence and claim ceiling, reused from Overview and Dispatch.
Keep analytic/model version, source evidence references and assessed window.

Before implementing classifications, state the minimal decision table beside
the analytic tests: evidence required, constraints evaluated, coverage rule and
what makes each classification available. Keep thresholds explicit and
versioned; do not seek a general optimization framework.

Carried question, answered in the decision table and recorded in the packet:
should stop-60's policy change appear as a policy record (version, effective
interval, source) under profile 5? Since
`D-2026-10-02-scenario-states-override-issuer` its override publishes no
record (`.ai/MILESTONE_REVIEW_BACKLOG.md`, "For T028"). If the answer needs a
scenario, template or contract change, stop and ask; do not make it here.

## Acceptance criteria

1. Generator intervals are reconstructed from accepted timestamped evidence.
   Gaps and uncertain transition times bound interval duration rather than
   becoming continuous assumed operation.
2. Evaluate load, PV capability, battery SOC/discharge capability, reserve,
   generator constraints and effective policy at the interval's time.
3. Observed PV output alone cannot stand in for available PV capability.
   Missing battery capability cannot be replaced from simulator truth.
4. Necessary has an inspectable binding constraint.
   Candidate Avoidable is a bounded candidate under declared evidence/model
   assumptions, not a claim of proven waste or optimal dispatch.
5. Indeterminate identifies which missing/conflicting evidence prevents the
   decision. One weak portion cannot be hidden inside a high-confidence total.
6. Coverage identifies signal coverage and temporal gaps; confidence states its
   basis separately from coverage. Neither is a fabricated precision score.
7. Missing operator-commanded override evidence is shown as none observed,
   not proof that an override did not exist. Known override records affect
   constraint assessment at their effective time.
8. Include alternatives such as unavailable PCS capability, policy constraints
   or unobserved override; evidence links let a reviewer challenge them.
9. The prolonged-runtime recipe produces a candidate interval through normal
   ingestion; the healthy reference does not receive a scripted Finding.
10. Show indicative associated fuel quantity as a bounded estimate with duration,
    power/consumption inputs, model basis and uncertainty.
    If those inputs cannot support a bound, show unavailable with the reason.
11. Quantity basis is measured/modelled/scenario as applicable.
    This fuel estimate does not imply a reconciled tank loss or financial saving.
12. Finding Detail and Dispatch refer to the same assessed object and evidence.
    Overview links to that Finding instead of recomputing a separate claim.
13. Rerunning on the same accepted evidence/model version yields the same
    assessment without duplicate active Findings.
    Changed accepted evidence creates an inspectable assessment revision.
    Revision history is persisted: the prior assessment is retained, not
    overwritten, and stays inspectable (evidence basis, model version, window)
    after a revision, across reload.
14. Removing private recipes, world state and oracles does not change the
    analytic result or remove its ability to explain the conclusion.
15. The screen path exposes context, selected window, classification, supporting
    facts, gaps, confidence, alternatives and bounded fuel without requiring Lab.
16. Each analytic declares its id and applicable site types, the Finding type
    it may emit, required and optional evidence, and claim levels (dispatch:
    Necessary, Candidate avoidable, Indeterminate). The backend serves the
    evaluated, site-scoped declaration as a read model. Verification rules are
    not declared yet (T034).
17. A `tools/checks` guard enforces the declaration with the rigour of the
    simulator model-profile pattern, not its data: product analytics may not
    read `EXECUTION_REQUIREMENTS` in
    `backend/assetops_backend/runs/profiles.py` or any private/simulator flow.
18. The presentation profile maps backend capability ids only to label, order,
    grouping and emphasis, under three rules, each with a test, applied to
    Performance subtabs, a card's assessment slot, Evidence capability rows and
    Finding types (not to the profile's Overview domain cards):
    (1) a backend id the profile does not know still renders, with the
    backend's display name in a default position; drift is never silent;
    (2) a profile id the backend does not serve renders nothing, and a test
    flags the orphan; (3) a gap is shown only from backend state, never from
    the profile.
19. The rule-2 orphan test reads an explicit expected-orphan list of planned
    profile ids with their owning slice (e.g. Renewable T031, Fuel T030,
    Service and Backup T035, if carried). Listed ids pass, an unexpected
    orphan fails, and each analytic slice removes its id when it lands.
20. Site > Evidence shows a capability table above the T027 source-health
    section, one row per existing analytic (here: dispatch), with readiness
    Full, Limited or None, the claim ceiling and the missing evidence, scored
    from the declaration against accepted coverage. Nothing in it appears
    before a real claim exists.
21. Navigation per `D-2026-10-02-rendered-tabs-per-capability` and
    `D-2026-10-02-grammar-ownership-test`: Performance renders Dispatch as its
    only subtab (with local `Overview | Analysis` views); Finding detail
    renders `Overview | Analysis | Evidence | Alternatives` (Recommendation and
    History are not rendered until T034); Site > Evidence has local
    `Overview | Analysis` views (amended 2026-10-04 by
    `D-2026-10-04-plain-language-analysis-views`; spec
    `.agent/T028-architect-presentation.md`); the claim drawer
    reuses T027's record inspector and opening it never changes the root;
    Findings is a rail root with its global index; Site > Findings is a scoped
    index (filter, no KPI strip, no status model of its own; a row click
    changes root to the Finding).

## Presentation revision (2026-10-04)

`D-2026-10-04-plain-language-analysis-views` (owner direction
`.agent/owner-T028-presentation-direction-2026-10-04.md`, Architect spec
`.agent/T028-architect-presentation.md`) adds two checkpoints before merge:
(1) plain default reading and Analysis destinations; (2) four assessment
graphics and the product-vocabulary guard. The spec's section 5 verification
list and its owner walk (default views first, then Analysis) are part of
acceptance.

## Phases

One branch; each phase ends with committed work, an owner UI check and
`.agent/T028-phase-N-handoff.md` (`.ai/ROLE_CONFIG.md`). Full suites and the
packet belong to phase 3.

**Phase 1: analytic, declaration, Finding, revision history.**
ACs 1-11, 13 (including persisted revision history), 14, 16, 17 in full; 12
and 18 for the Overview Dispatch card, which shows the backend assessment word
and a one-line reason (other cards keep "No assessment yet").
*UI check:* after committing the prolonged-runtime and healthy recipes, the
Kobo Overview Dispatch card shows a candidate and no false candidate
respectively; the declaration and revision list open at their read-model URLs,
a revision leaving the prior assessment listed.

**Phase 2: screens.**
ACs 8, 12, 15, 21 on screen; 18 and 19 for Performance subtabs and Finding
types. Finding detail Overview follows the recommendation's hierarchy (section
3 "Finding Detail"), consequence as technical quantity only.
*UI check:* recommendation 5.2 row 2 up to the drawer: Sites -> Kobo Overview
-> Performance > Dispatch -> Finding -> Evidence tab -> drawer; Findings rail
index lists the same Finding.

**Phase 3: Site > Evidence part B.**
AC20 in full; 18 for Evidence capability rows (rule 3 tested there).
*UI check:* Kobo Site > Evidence shows one dispatch row above source health;
a `kobo-mini-grid-degraded-evidence` run shows Limited with the missing
battery capability named.

Rendered from phase 2: rail OPERATE: Sites; INTELLIGENCE: Findings (the T002
`Operator home` item was removed in T027 phase 1); Site tabs Overview, Foundation,
Performance, Findings, Evidence. Run `node tools/layout-evidence.mjs` per
phase, covering a one-item rail group from phase 2.

## Proof

| Evidence case | Required assessment |
| --- | --- |
| Healthy supported-demand interval | Necessary where constrained; no false candidate |
| Prolonged-runtime interval, adequate capability | Candidate Avoidable with reasons |
| PCS capability missing for part of interval | Segmented/limited claim and named gap |
| Insufficient capability throughout | Indeterminate, not fabricated avoidance |
| Time-valid reserve prevents battery support | Necessity/limit explained |
| Override record present | Constraint included |
| Override absent | Absence limitation explicit |
| Delayed/out-of-order evidence | Source-time reconstruction with provenance |
| Remove private simulator data | Same product assessment |
| Hand-calculated bounded fuel example | Matching range and displayed basis |
| Changed accepted evidence | New revision; prior assessment retained |
| Profile drift (unknown id, unserved id) | Renders with default; orphan flagged |

`kobo-mini-grid-degraded-evidence` supplies the partial-capability, delayed
and absent-override cases through normal ingestion. Tests must check
classification/limits and evidence references, not just the presence of a
Finding card. Run backend analytic/read-model tests, frontend navigation tests,
shared checks and populated layout evidence.
The cockpit may validate the Lab recipe during review, but its private series
never enters classification or indicative fuel quantity. The Finding panels
remain reconstructible from accepted evidence with Lab disabled.

## Scope limits

T029 adds priced consequence. T030 adds FuelBalanceWindow.
No financial ranking, optimal-dispatch solver or portfolio readiness claim.
Full Replay and broad (cross-site) source-health UI are not prerequisites.
Sites columns are T029B (point-2 protection); Sites is already the landing (T027).
No seed: T029 owns it (`D-2026-10-02-demo-point-seed-rule`).

## Review

Walk roadmap 13.2 with the owner and prepare a compact expert-feedback example:
one candidate interval, one constraint, one gap and its bounded fuel estimate.
Record expert feedback when obtained; do not mark practitioner usefulness as
automatically proven by tests or contact anyone without authorization.

Practitioner usefulness has no automated proof, so the checkpoint needs
questions it can fail. Ask whether the expert can challenge the classification
from what the screen shows, whether the evidence they would want before acting
is either present or named as missing, and whether the claim ceiling is one
they would repeat to an operator. Three yeses is the pass; anything else is
feedback that redirects later work rather than a defect list for this slice.
Review outcome: owner accepted 2026-10-04 on a quick UI check ("Quick check of the UI looks ok for T028", `.agent/owner-T028-acceptance-2026-10-04.md`); the full packet walk was not recorded. Domain-expert feedback checkpoint still outstanding.
