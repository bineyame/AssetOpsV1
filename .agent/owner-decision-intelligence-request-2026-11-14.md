# Owner request 2026-11-14 (verbatim): decision intelligence mechanism document

Owner instruction: "create a well illustrated file based on the following:"

Note: the pasted task ends inside section 4 (after "How actions are assigned or handed off."). Sections 1-4 are complete as given below; nothing after section 4 was received.

---

# Task: Document AssetEcon's Existing Decision Intelligence Mechanism

## Objective

Produce a rigorous, code-grounded technical document explaining **how AssetEcon currently turns operational evidence into business-outcome evaluations, economic opportunities, interventions, and verified results**.

This is an architectural investigation, **not a request to redesign or implement anything**.

The purpose is to establish precisely what already exists, how the mechanisms interact, what they actually enforce, and which capabilities are genuinely missing before we consider further commercial integrations and economic decision improvements.

Use the existing `convertion_potential.html` analysis as background, but do not simply repeat it. That document primarily analyzes Portfolio card composition. This investigation must go deeper into the decision logic and end-to-end execution paths.

## 1. Explain the existing architecture end to end

Trace the actual implementation:

**Observation / record → Finding / signal / warning → Outcome mapping (`moves` / `checks`) → Evaluation → Economic contribution → Opportunity / intervention → Action → Verification → Site and Portfolio presentation.**

For each stage document:

- Responsibility and semantics.
- Relevant classes, functions, modules, tables, and APIs.
- Inputs and outputs, with concrete field names.
- Conditions that advance, qualify, reject, or suppress a result.
- Relationships to preceding and subsequent stages.
- Whether behavior is implemented, partial, configuration-only, or planned.

Identify where these stages are not actually connected.

Include a code-referenced architecture diagram and a sequence diagram for at least one complete execution path.

## 2. Investigate `moves` and `checks` in depth

This is the highest-priority question.

Explain their exact semantics **as implemented**, not merely their intended conceptual meaning.

Answer:

1. What does `moves` actually do?
2. What does `checks` actually do?
3. How are primary and secondary outcomes determined?
4. Does a checked outcome affect finding generation, validity, severity, valuation, recommendation, action eligibility, or only presentation?
5. Can a negative check veto, constrain, qualify, or downgrade an opportunity?
6. How are conflicting outcomes handled?
7. Are checks evaluated using actual measurements, declared objectives, deterministic rules, models, or status classifications?
8. What happens when a checked outcome has insufficient evidence?
9. Are checked outcomes evaluated independently or as part of one integrated assessment?
10. What happens when an intervention improves one outcome but degrades another?

**Trace the exact call paths and relevant conditions.**

Do not infer enforcement merely because a relationship is declared in the outcome map.

## 3. Deep trace: `GENERATOR_SUPPORT_CANDIDATE`

Use the existing mini-grid generator-support mechanism as the primary case study.

Trace it from source readings to its ultimate presentation and potential verification.

Include:

- Required telemetry parameters, units, time resolution, and source roles.
- Generator-support detection conditions.
- Battery reserve and SOC handling.
- PV availability and demand conditions.
- Generator minimum-run, ramping, reliability, and other constraints, where implemented.
- How `MG-2`, `MG-5`, and `MG-4` participate through `moves` and `checks`.
- Fuel estimation models and their assumptions.
- Economic valuation and declared price handling.
- Proposed intervention or trial behavior.
- Verification rules and what VERIFIED actually establishes.
- Portfolio contribution and aggregation behavior.

### Critical test

Consider two cases:

**Case A — Genuine opportunity:** The generator operates when a feasible, reliability-preserving alternative could supply demand at lower net cost.

**Case B — False opportunity:** The generator operates because battery reserve, capacity, load, or reliability constraints require it.

For each case, explain exactly how the existing implementation behaves.

Does it reject the finding, generate a qualified finding, reduce its estimated value, produce a conflicting outcome, or simply display a warning?

Identify the actual code and tests proving the behavior.

If the current tests do not cover a case, state that explicitly. Do not claim support based only on architectural intent.

## 4. Investigate the complete opportunity and action lifecycle

Examine the existing Finding, opportunity, Opportunity Action, work-case, verification-plan, and related structures.

Determine:

- How opportunities are created and identified.
- Whether opportunities exist independently of Findings.
- Whether one opportunity can reference several Findings.
- Whether one Finding can affect several economic outcomes.
- Whether competing interventions can be represented.
- Whether a baseline or no-action alternative exists.
- How intervention costs, benefits, risks, and constraints are represented.
- How an intervention is selected, approved, and executed.
- How actions are assigned or handed off.
