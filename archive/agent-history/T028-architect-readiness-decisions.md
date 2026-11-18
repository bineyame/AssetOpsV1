# T028 capability-readiness decisions

Architect: Codex, 2026-10-04. Basis reviewed: branch
`task/T028-dispatch-finding-and-evidence`, HEAD `1f46d75`.
Authority: `.agent/T028-architect-brief-readiness.md`, the owner's verbatim
reply in `.agent/owner-T028-closeout-2026-10-04.md`, and `.ai/ROLE_CONFIG.md`
"Decision Requests Go To The Active Architect".

This records Architect decisions, not a review verdict or owner acceptance.
Only this file is changed. Code, tests, tasks and `.ai/DECISIONS.md` are left
to the coordinator and Implementer; no merge or test-suite rerun was performed.

## 1. Readiness scope and meaning

**Decision: retain site-wide readiness for T028.** It uses all accepted Site
evidence and the latest revisions of active assessments. "Active" means an
assessment lineage has not been retired; it does not mean the Site is running
now. The Evidence page's selected window continues to scope its source-health
and coverage inspection, not the capability table.

In plain words: readiness answers **how well the evidence AssetOps has can
support this analytic's conclusions**. It is evidence sufficiency, not a
healthy/unhealthy operating condition, installation progress, or a setup phase.
A healthy interval assessed Necessary and an interval assessed Candidate
Avoidable can both have Full readiness. A fully configured Site can have None
because the necessary evidence has never been accepted.

Justification: the declaration describes an analytic's evidence requirements;
assessments describe what happened in particular intervals. Keeping their
scopes explicit preserves that distinction and keeps the capability summary
stable while someone browses source records. This matches AC20 and the backend
ownership in `D-2026-10-02-presentation-profile-and-capability-declaration`.
Changing to a selected-window score would also require rules for assessments
crossing window boundaries; that is additional behavior without a demonstrated
need in this slice.

Consequences and limits:

- Full means every declared required signal has some usable accepted evidence
  and the assessed portions have no claim-limiting coverage gap under the
  stated readiness rule. It does not certify continuous coverage, current
  telemetry, concurrent availability of every signal, or a claim in every
  selectable window. Old accepted records still count.
- A historical gap in an active assessment can keep the site-wide row Limited
  even when the selected window has good coverage. Conversely a selected empty
  window can sit below a Full capability row. Explain the scope on the table.
- The claim ceiling is a conditional maximum supported by the analytic, not
  an assertion that such a Finding exists or that the Site is wasting fuel.
- With zero assessed intervals, the score establishes signal availability
  only. The screen must say that coverage has not yet been assessed, rather
  than let Full imply demonstrated temporal sufficiency.
- T029B must keep its own specified assessment-window coverage column. A
  site-wide readiness badge cannot substitute for that metric. Future portfolio
  use must preserve the distinction between readiness and operational priority.

## 2. Gap rule and configurable gap impact type

**Decision: retain the current claim-dependent treatment of coverage gaps as
T028's explicit interim default. Defer configurable gap impacts to a dedicated
follow-up, T028A - Configurable analytic evidence-gap impact.** This is a named
planning assignment, not a task file created by this pass. Plan it after T029's
point-2 feedback; it is unscheduled and adds no prerequisite to the existing
demo spine. The coordinator must carry it in the milestone backlog and routing
so the owner's request is not lost. Keep it separate from T029B's read-only
Sites composition and T034's operational policy/verification work.

The owner's deferral is respected: this does not settle one permanent,
universal gap tolerance. Until configurable policy replaces it, T028 states
which interim rule it actually applies:

- A required signal with no usable accepted record limits readiness (or
  prevents it where no supported reconstruction path remains).
- A partial coverage gap lowers Full to Limited when an assessed segment's
  decision needed that input and was left Indeterminate by its absence.
- Gaps that did not limit a classification remain visible as non-limiting;
  they do not lower this readiness score. Thus the packet's prolonged-runtime
  SOC gap can coexist with Full; the degraded battery-capability case remains
  Limited. Full never means gap-free.
- Absent optional records remain "not observed" with their claim limitation;
  absence of an override is not proof that none existed.

Justification: the score should explain the effect on the analytic, while
coverage reports the missing data itself. Automatically treating every gap as
claim-limiting would conflate those questions. The current rule is sufficient
for the one-analytic demo if disclosed; authoring, persistence and versioning
of configurable policies deserve their own observable slice.

**Meaning of gap impact type for T028A:** a backend-owned, versioned setting
on an analytic's evidence requirement governing how a detected gap affects
readiness. It is not a simulator dropout type, device-health category, or
permission to fill missing evidence. The initial supported choices should be:

| Type | Readiness consequence |
| --- | --- |
| `CLAIM_DEPENDENT` | A partial gap lowers readiness when it limits the assessed claim; otherwise it is still shown. T028's interim coverage behavior. |
| `COVERAGE_REQUIRED` | Any detected gap in that requirement over the declared assessment scope lowers readiness, even if another evidenced constraint determined the classification. |
| `CONTEXT_ONLY` | Show missing optional context without lowering readiness; permitted only for evidence the analytic declares optional. |

The analytic's actual claim prerequisites remain mandatory. A setting cannot
turn a missing essential input into a usable one, remove Indeterminate
segments, raise a technical claim ceiling, or make None into Full. Distinguish
the configured type from the observed consequence: no reconstruction possible,
claim limited, coverage-only limitation, or missing optional context. Required
inputs cannot be configured as context-only. Applying a stricter coverage rule
may lower readiness while leaving a valid Necessary assessment unchanged.

T028A's reviewable result should be a small product configuration surface that
selects a supported impact type for an analytic requirement, persists it, and
shows the effective type/version and resulting readiness on Site > Evidence
after reload. The Planner should specify the smallest configuration scope
needed by point-2 feedback; no generic rules engine or broad settings system.
Keep configuration and evaluation in the backend; the presentation profile
only labels/orders. Expose the effective policy version and scope with the
score. Preserve prior assessment revisions; a readiness-only policy change
must not rewrite evidence or claim history. If a future policy changes actual
classification semantics, it needs a new analytic model version and revision.

## 3. Changes required before T028 returns to review

The two decisions require no selected-window API or configurable-policy
implementation in T028. They do require the following narrow corrections.

1. **Make the meaning and limits visible.** Extend the backend-served readiness
   explanation to state evidence sufficiency, site-wide scope, the interim
   claim-dependent rule, and that Full does not establish Site health or
   uninterrupted/current coverage. Show the existing `assessed_intervals`
   count; zero must say "No intervals assessed; signal availability only."
   Replace the unconditional empty-gap text "No required evidence is missing"
   with a bounded statement such as "All required signals have usable records;
   no claim-limiting gaps identified in assessed intervals." Exact wording is
   illustrative; those meanings are required. The existing backend statement
   already identifies the site-wide scope, so extend that source of meaning.

2. **Align None with the analytic's reconstruction alternatives.** Static
   inspection found an existing contradiction relevant to this decision:
   `ReadinessBasis.no_claim_without` lists generator status and power, and
   `score_readiness` returns None when either is absent. Its explanation says
   no interval can be reconstructed. But `dispatch.py::_states` accepts status
   observations and falls back to usable power when status is absent; the
   decision table's Evidence section expressly says reconstruction uses either.
   `_evaluate` can also establish a qualitative claim without generator power;
   any fuel-quantity limitation must remain separate. Require no supported
   generator reconstruction evidence before giving this absence-based None.
   When only one required generator channel is evidenced, retain the missing
   channel and Limited disclosure, and preserve the analytic's conditional
   claim ceiling. Do not disable the analytic's existing fallback to make the
   readiness explanation true. This is a concrete source inconsistency, not
   an executed regression finding; the Implementer must cover status-only,
   power-only and neither-channel cases with meaningful analytic/read-model
   checks, including a reconstructible interval for the first two cases.

3. Keep the decision table, packet and backend explanation consistent with
   these decisions. The scoring correction changes readiness semantics, so
   increment `basis_version` from `readiness-1`; it does not change
   `dispatch-1` or require rewriting assessment history. The coordinator
   closes the packet's two open decisions by reference to this record, records
   T028A's carry, and lands the durable entry below. Independent review and
   the task's owner UI acceptance still follow their normal route.

Already reported verification (not rerun here): backend 1465, host 616,
simulator 244, frontend 1097; build and both checks; layout 560 PASS / 5 FAIL.
These results describe the prior implementation, not the corrections requested
above, and this decision does not dispose of the layout failures. Validation
of the corrections belongs to the Implementer and subsequent Reviewer.

## 4. Owner involvement

**I do not need the owner to weigh in before proceeding with these decisions.**
The owner delegated them to the active Architect and explicitly deferred the
permanent gap rule in favor of configurability. Keeping the existing scope and
an explicitly interim rule, while assigning the configuration work and fixing
misleading explanations, honors that instruction without expanding T028 into
a policy editor. The owner may overrule this decision and still provides the
separate slice acceptance; neither is recorded as having happened here.

## Draft durable entry for `.ai/DECISIONS.md` (coordinator to land)

Suggested index row:

| `D-2026-10-04-analytic-readiness-scope-and-gap-impact` | 2026-10-04 | Analytic readiness describes evidence sufficiency, site-wide in T028; claim-dependent gap treatment is interim, with versioned configurable impact types assigned to T028A. |

### 2026-10-04

Decision: `D-2026-10-04-analytic-readiness-scope-and-gap-impact`.
Decided by Codex Architect under the owner's delegated decision authority in
`.ai/ROLE_CONFIG.md`; reasoning and implementation consequences are in
`.agent/T028-architect-readiness-decisions.md`.

Analytic readiness is a backend-owned assessment of evidence sufficiency,
distinct from Site operational condition, setup progress and source health.
T028 scores all accepted Site evidence and latest active assessments, not the
Evidence page's selected window. Full describes signal availability and the
absence of claim-limiting gaps in assessed portions; it does not assert fresh,
continuous or selected-window coverage. Zero assessed intervals is disclosed.
None must respect the analytic's supported alternative reconstruction inputs.

T028 retains an explicitly interim claim-dependent coverage-gap rule: gaps
that limit a classification lower readiness; other gaps remain visible.
Required-input absence and optional-context absence remain distinct. The
permanent gap policy is deferred at the owner's request. T028A, Configurable
analytic evidence-gap impact, owns a versioned backend configuration and its
small inspection/editing surface, to be planned after T029 point-2 feedback;
it is unscheduled and gates none of the existing demo spine.

Gap impact type controls the readiness consequence of missing evidence per
analytic requirement. It cannot invent evidence or weaken prerequisites for
an actual claim. Stricter coverage requirements may lower readiness without
changing a valid assessment. Policy version and scope travel with readiness;
readiness-policy changes preserve evidence and assessment history. Actual
classification changes require analytic versioning. Presentation profiles
remain presentation only.

Reason: keep the one-analytic demo honest, distinguish coverage from its
effect on a claim, and preserve the owner's configurable-policy direction
without broadening T028. Affected scope: T028 AC20, T028A planning/backlog,
T029B coverage composition and later analytic/portfolio consumers.
