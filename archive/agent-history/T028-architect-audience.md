# T028 audience: Architect decision

Codex Architect, 2026-10-04. Answer to the owner's
[audience question](owner-T028-audience-question-2026-10-04.md), under the
delegated decision authority in `.ai/ROLE_CONFIG.md`.

**T028 belongs in the client product, but its present delivery reads too much
like an analyst's inspection report.** A mini-grid engineer could use it in a
guided discussion. An operations or asset manager has to work too hard to find
the practical conclusion. I would show it now to a technical practitioner for
feedback; I would not describe it as a finished, self-explanatory client
experience. Practitioner usefulness still needs to be demonstrated.

The intended reader is an operator asking, “Did this generator need to run,
what evidence supports that answer, and what should I check next?” A technical
client is different from someone developing AssetOps. The client needs reserve,
load, solar and battery capability, operating constraints and uncertainty.
They should not need assessment identifiers, evidence digests or knowledge of
the implementation to understand the answer.

**My decision is a small presentation correction in T028 before merge.** Keep
T029 next for money and the prepared external demo. Adding a monetary number to
the current presentation would not, by itself, solve the audience problem.
This is a correction to how the existing result is explained, not a request
for more analytics or a broad redesign.

The intent is already established by [PRODUCT](../.ai/PRODUCT.md), feature-map
[C and D](../.ai/FEATURE_MAP.md), the accepted recommendation's section 3 and
the owner's [queue feedback](../Docs/queue-review-feedback-verbatim.md): T027
is the internal architecture checkpoint; T028 is the first practitioner
Finding; T028 plus T029 is the domain-expert and early-prospect demo. Waiting
until the full portfolio would miss the intended learning opportunity.

The current implementation has a useful product foundation. Performance asks
“Was the generator needed?”; the Finding separates observation from inference,
shows competing explanations and bounds its fuel estimate; Overview and the
indexes lead to the same assessment. A client should be able to inspect that
evidence. Those are product capabilities, even when a specialist uses them.

The audience mismatch is in the prominence and wording of the information:

| Delivered surface | What makes it feel like a development or analysis tool |
| --- | --- |
| Finding Detail | Before the main explanation, the header shows assessment ID, revision counts and analytic version. “Observed facts” includes a basis digest. Every input's segment coverage and gaps appears in the Overview body. The fuel consequence follows that long explanation. |
| Finding language and next step | “Claim ceiling,” “Consequence (technical quantity)” and “Challenge the claim record by record” describe our reasoning machinery. The next steps mostly describe navigating the application, rather than the operational information to confirm. |
| Performance / Dispatch | The operational question is good, but the first explanatory line leads with analytic ID/version. The table speaks in classifications and segments; the practitioner needs the reason and affected time to remain easy to see. |
| Findings indexes and Site Overview | The shared summary provides a real reason and the indexes already use it as the link. However, Type, Claim and Revision compete for attention, while Overview surrounds the one assessed domain with other domains saying “No assessment yet.” More capability has not yet been delivered; that is a scope limit, not a reason to invent site health. |
| Site > Evidence | The capability row is useful for a technical client, but “Full,” “claim ceiling,” model version and a long methodological explanation require careful interpretation. This page answers what the data supports, not whether the site is operating well. |

These observations come from `FindingDetail.tsx`, `SitePerformance.tsx`,
`FindingsIndexes.tsx`, `findingPresentation.tsx`, `CapabilityReadiness.tsx`
and `SiteOverview.tsx` under `frontend/src/sites/`, plus `_one_line`,
`CLAIM_CEILINGS`, confidence/fuel explanations in
`backend/assetops_backend/analytics/dispatch.py` and readiness explanations in
`declaration.py`. The backend already supplies much of the content needed.
For example, its candidate summary names runtime, capability above load and
the absence of an evidenced binding constraint. The frontend must not invent
a stronger diagnosis from that summary.

Apply the following bounded correction in **T028 before merge**:

1. **Let the operational explanation lead.** Keep Site, generator and assessed
   period visible; format dates and times for reading with an explicit timezone.
   Put assessment IDs, digests and model/version details in an expandable
   “Assessment details” area on the existing page or its Evidence tab. Keep
   revision provenance inspectable without adding the History tab reserved for
   T034. Performance's introductory sentence should explain the operational
   question before any method/version information. Reuse the same bounded
   summary in the Overview card, index and Finding.

2. **Make the existing six-part Finding readable at a glance.** Preserve the
   accepted order: conclusion, observed facts and inference, confidence and
   coverage, limits, consequence, next step. Use plain headings such as “What
   the evidence suggests,” “What limits this conclusion” and “Estimated fuel
   associated with this runtime.” Keep candidate duration, necessary and
   indeterminate portions, the principal reason, confidence and material
   missing evidence visible. Put the complete per-signal coverage list and
   fuel calculation inputs behind clearly labelled expansion controls or in
   the existing evidence detail. Keep the fuel range, modelled basis and its
   uncertainty visible in the consequence summary. A missing upper bound or
   unavailable quantity must remain explicit. Retain the canonical
   classifications, with a short explanation of their meaning.

3. **Make the next step and evidence sufficiency understandable.** Where an
   override is unobserved, say to confirm whether an operator instruction kept
   the generator running, and link to the relevant alternative. Where
   capability evidence is missing, name what needs checking and link to it.
   Present this as investigation, not an instruction to stop the generator or
   change policy. On Site > Evidence, explain readiness as “What can we assess
   from this site's evidence?” alongside its existing Full/Limited/None
   result. Keep its site-wide scope, assessed-interval count, zero-interval
   qualification, limiting gaps and the distinction from site health visible.
   Longer scoring mechanics and version details can be expandable.

For illustration, the candidate explanation should communicate: “The generator
ran during a period when reported solar and battery capability exceeded load,
with no binding constraint evidenced. This is potentially avoidable runtime;
an unrecorded operator instruction remains possible. Confirm the operating
instruction before considering a change.” Use that form only where the actual
assessment supports every clause; it is not a fixed story for every interval.
Display the actual bounded time and fuel result alongside it, never invented
example numbers. Necessary and Indeterminate require their own truthful
explanations.

This correction changes emphasis and copy. Classification, confidence,
coverage, fuel bounds and readiness remain backend-owned. Any interpretation
needed for conditional next-step wording should be served consistently from
that assessment, not inferred independently in several screens. No readiness
rule, model threshold, evidence contract, navigation root or recommendation
workflow is changed by this decision. In particular, Full must not become
“site healthy,” “complete coverage” or “ready to act.” The earlier
`D-2026-10-04-analytic-readiness-scope-and-gap-impact` remains in force.

The Implementer should show the same candidate, healthy and evidence-limited
cases after this correction. On the ordinary page, the owner should be able
to explain what happened, why it matters technically, what remains uncertain
and what to check next; opening the evidence should reveal the original
supporting records and method details. Independent review should check that
shorter wording has not strengthened any claim and that disclosure controls
remain usable. This is the exit condition for the correction, not a new
analytics validation project. Existing unrelated review carries retain their
own disposition.

**T029 owns the economic and demonstration completion.** Add the bounded fuel
and maintenance consequence to the readable Finding, compact Overview value
and Site Financials. Preserve the distinction between associated candidate
cost and realized savings. Use the existing T029 seed and Lab-off rehearsal
so the prospect's journey begins with a populated site, not Draft creation,
Commit setup or API inspection. The review packet's setup/API checks are
engineering preparation; they are not a client walkthrough. T029's existing
requirement for the owner's client-facing financial assumptions still applies.
The Planner should carry this audience direction into T029 before it starts;
this pass does not edit that task.

**Later work keeps its current owners.** T029B adds Sites assessment ranking;
T034 adds actual recommendations, action and verification; T034A adds the
portfolio opening. Configurable evidence-gap impacts remain with T028A after
point-2 feedback. Broader copy, chart, reporting or persona-specific redesign
should follow observed practitioner difficulty. There is no need now for
separate manager/engineer applications, a generic “simple/expert” mode, new
navigation or a full dashboard redesign. The existing pages and drill-downs
can serve both an initial operational reading and a detailed technical review.

**I do not need a further owner decision to proceed with this direction.** It
follows the audience and demo sequence already approved, and the owner has
delegated decision requests to the active Architect. The owner can overrule
the choice to make the narrow correction before merge; my reason for doing
it now is that understanding the first Finding is T028's own promised product
outcome. The separate owner UI acceptance is still required and is not
recorded as granted here. No practitioner or prospect has been contacted, and
tests do not establish that they find the result useful.

Review basis: branch `task/T028-dispatch-finding-and-evidence`, implementation
at `30122ed`; checkout HEAD `569df5f` adds only this brief and the owner's
question. This was a source/content assessment using the task, packet and
intent records, not a new browser walk or a visual-layout certification.
The brief's reported test/review results were accepted as prior evidence and
were not rerun. Only this response file was written; no code, tests, task
files or decision log were edited, and no merge was performed.

Draft durable entry for `.ai/DECISIONS.md` (coordinator to land):

| Decision | Date | Summary |
| --- | --- | --- |
| `D-2026-10-04-practitioner-first-finding-presentation` | 2026-10-04 | Findings lead with a bounded operational explanation; provenance and method detail remain accessible through progressive disclosure. Narrow T028 correction before merge; money and prepared demo remain T029. |

## 2026-10-04

Decision: `D-2026-10-04-practitioner-first-finding-presentation`.
Decided by Codex Architect under `.ai/ROLE_CONFIG.md` delegated authority;
reasoning and bounded implementation direction are in
`.agent/T028-architect-audience.md`. This is not owner slice acceptance.

The primary audience of T028 product surfaces is mini-grid practitioners,
including operations and asset managers and technical reviewers. The first
reading of a Finding explains the operational conclusion, affected period,
supporting facts, uncertainty, bounded consequence and investigative next
step. Assessment identifiers, digests, model versions, exhaustive signal
coverage and calculation inputs remain inspectable through existing evidence
surfaces or expandable details. Material claim limitations, unavailable
bounds and missing evidence remain visible with the conclusion.

T028 receives a narrow copy and information-emphasis correction before merge,
preserving the accepted six-part Finding hierarchy and existing navigation.
Backend ownership of assessment semantics, evidence, confidence and readiness
is unchanged. Readiness remains site-wide evidence sufficiency, with the
scope and limitations established in
`D-2026-10-04-analytic-readiness-scope-and-gap-impact`; it is not operational
health or permission to act. Investigative guidance does not constitute an
operational recommendation or authorized control change.

T029 retains bounded financial translation, client-facing assumption review
and the seeded, Lab-off point-2 demo. T034 retains recommendations, action and
verification. Broader presentation changes follow practitioner feedback; no
new persona mode or navigation framework is introduced.

Reason: the first useful Finding must be understandable to its intended
reader while remaining challengeable. Technical correctness and exhaustive
provenance alone do not establish practitioner usefulness. Affected scope:
T028 presentation closeout, T029 planning and later Finding presentations.
