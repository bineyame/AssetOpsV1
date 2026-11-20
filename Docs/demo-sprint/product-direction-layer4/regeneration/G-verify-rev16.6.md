# Layer 4 regeneration, Phase G: verification review of rev 16.6

Reviewer: fresh Claude reviewer (did not author the work). Branch `task/layer4-design-regeneration`, head `d7c93657e`, diff against `1b9cda1d8`. Read-only except this file.
Scope: the review E findings (M1–M5, L1–L8, I1–I5), the plan F gaps G-F1 to G-F5 (`F-pack-recreation-plan.md` l.76-80), regressions in the fix diff, the new naming lint and the renderer guard. Standard: `.agent/owner-design-regeneration-request-2026-11-19.md` (OD-1 to OD-9) and `.agent/owner-recreate-document-packs-2026-11-19.md`.

## Summary

- **Verdict: ACCEPT WITH NOTES.** All 5 Medium findings of review E are fixed, and the code claims behind M4 and M5 are accurate. 17 of the 18 E findings are fixed; I2 (no Mermaid parse) still stands because no Mermaid package is available here. All five G-F gaps are closed, and G-F2's sweep has stragglers (N4). The new Architect's calls are each marked and listed, and none contradicts OD-1 to OD-9.
- **New findings: High 0 · Medium 1 · Low 6 · Info 3.**
- **N1 (Medium):** the naming lint is too permissive. 5 of 12 planted "plan = target" uses pass it, including one of the five original M2 lines (l.127, reverted) and the retired label "actual against plan" used anywhere. The documents themselves are clean today: I read all of their "plan" uses by hand. So N1 does not mislead a derived document now. It must be fixed before this lint becomes plan F's A3 guard for the recreated packs.
- Mechanics: `check_manifest.py` printed "3762 checks passed, 0 failed" (exit 0). `motivation_figures.py --check` printed "2 figures built … missing [] unused []" (exit 0). The re-render is byte-identical (`cmp`). A planted violation fails the lint, and a planted decision-table split trips the renderer guard.
- Code: M4 and M5 checked against `0051`, `0027`, `0033`, `0042` and `0009`. The claims are accurate. The migration list omits one trigger (N6).

## 1. Status of review E findings and plan F gaps

| ID | Status | Evidence |
|---|---|---|
| M1 | Fixed | The blank line is gone. The committed HTML has `<td>OD-1</td>` … `<td>OD-9</td>` all as data cells and no `<th>OD-`. `render_design_html.py:102-103` now asserts that no decision-ID row begins a table. A planted split (blank line before OD-7, in a scratch copy) raises `AssertionError: table split: a data row (OD-7) begins a table` |
| M2 | Fixed (documents); guard weak (N1) | `worked-portfolios.md` l.127 "The target states only…", l.491 "30% targeted", l.503 "on target", l.523 "Target: a stated total only", l.529 "Target cost to serve". All 100+ prose uses of `plan` across the three files were read; each means the construct, or "plan F" (N2) |
| M3 | Fixed | The Figure 10 caption (l.625) has lane B reading actual litres and their split only. "Targets and budget lines are lane A records too … They take effect at step 5, where the contribution gap of −562.00 appears in the bridge". This matches `J --> T` and step 5 in the text |
| M4 | Fixed | "Words used here" defines **Action** over the three carriers, and §2.5 adds the no-decision case: "the Action creates its own reactive item". Code: trial `action` has a Finding origin (`0051:37-38` trigger matches `a.origin_finding_id`). `domain_action` has exactly one origin, Finding or opportunity (`0051:73-77`). The work case has no origin column; it links to Findings (`0027:76-81` `work_case_finding_link`), trial Actions (`0027:83-88`) and domain Actions (`0033:82-94` `domain_action_case_link`). All accurate. Residual ambiguity: N5 |
| M5 | Fixed | §1.4 credits "the domain action already has exactly one origin … a mini-grid domain action must take the opportunity origin (`0051:73-79`)". The §2.9 Actions row names the change: the one-origin check gains a plan-item arm, `domain_action_mini_origin` (`:78-79`) is replaced, trial actions and work cases gain the links, and `chain_action_thread` and the `chain_action` view widen in the same migration. Line ranges verified (`:73-77` one-origin, `:78-79` MINI rule, `:53-62` view). `0057` does not touch them, and no later migration redefines the view. Omission: N6 |
| L1 | Fixed | The text's steps 1–5 now match the figure (1 CH5 → 2 format → 3A/3B/3C → 4 join → 5 targets and bridge) |
| L2 | Fixed | "cost-side decisions start before the join" is listed under "Architect's calls, not settled by the owner" |
| L3 | Fixed | "a Site setting wins over the portfolio one" (§2.4 step 4). "Until a tolerance is set, every adverse deviation is raised" (§1.3). Both are marked as Architect's calls. The executive sets both thresholds (roles table l.451), so the precedence opens no self-release path |
| L4 | Fixed | "A hard-bound rejection can be overridden only by a recorded change to the bound (Architect's call)" (§2.4 step 1) |
| L5 | Fixed | §2.4 step 1: "Recommended, found by one search across the period's decisions so that the recommended set fits". This now matches `worked-portfolios.md` l.13, and §2.5 still checks the *chosen* set |
| L6 | Fixed | `design-appendix.md`: §4 Change log (l.43) holds the 16.3–16.6 entries, then §5 Pilot asks (l.82) and §6 Limits (l.89) |
| L7 | Fixed (light theme) | `classDef actor fill:#ffffff,stroke:#18212f`, no longer the "new" blue. For the dark theme, see N9 |
| L8 | Fixed | **Lever** and **Calibration replays K, M, E** are defined in "Words used here" |
| I1 | Re-run | See §3 |
| I2 | Still stands | No Mermaid package is available here, so no block was parsed. The only Mermaid change in 16.6 is one `classDef` line, so the risk is low |
| I3 | Holds | Parts 1–2 hold 6,564 words (4,046 prose, 2,518 in tables), with Mermaid and markers removed. This is about +40 on rev 16.5 and still around the target |
| I4 | Addressed by G-F5 | — |
| I5 | Fixed | The transitions now include *merged into* and *basis refreshed*, which matches `0009:70-71`. The thread states now include *open*, *closed* and *reopened*, which matches `0042:66-67` |
| G-F1 | Fixed | The D-numbers and D15 point to `decisions-register.md`, marked "as proposed in plan F, pending approval" |
| G-F2 | Fixed; sweep incomplete | The appendix table now names the plan F files. Two other pointers to retired or renamed files remain (N4) |
| G-F3 | Fixed | `design-appendix.md` §6 is a faithful copy of `derivation-register.md` §9. Only L5's scope is re-worded to the current document structure. The pointer in worked-portfolios is updated. ID collision: N3 |
| G-F4 | Fixed | `worked-portfolios.md` l.654 points to `delivery-plan.md` (pending approval) |
| G-F5 | Fixed; wording | "Manifest key `plan`" is in "Words used here" and in the Architect's calls. The wording is in N7 |

## 2. New findings

### N1 · Medium · `check_manifest.py:560-592`: the naming lint lets "plan" for a target through

**Evidence.** I planted 12 sentences, one at a time, at the end of a scratch copy of `worked-portfolios.md` and ran `check_manifest.py` from the copy. The lint caught 7 and missed 5:

| Planted | Result |
|---|---|
| "Kobo is over plan on diesel this month." | caught |
| "(30% planned, 55% actual)" (M2 l.491, reverted) | caught |
| "**October: on plan.**" (M2 l.503, reverted) | caught |
| "Plan cost to serve" (M2 l.529, reverted) | caught |
| "The plan states only billed kWh…" (M2 l.127, reverted) | **missed** |
| "…against its plan of litres." | **missed** |
| "…shown actual against plan this month." (the retired label) | **missed** |
| "The site keeps an operational plan for diesel." | caught |
| "Operators set monthly plans for diesel litres." | caught |
| "…compared with the plan figure the operator typed." | **missed** |
| "The plan item is approved. Revenue came in under plan." | caught |
| "…came in above a plan of 700 litres." | **missed** |

There are three causes:
- The first allow rule, `(the|a|this|its|…)\s+plan`, accepts any determiner before "plan", which is how most target uses are written.
- `Actual against plan` is allowed case-insensitively anywhere, although plan F A3 lists it as a retired term.
- Each match is tested against a ±45-character window, so an allowed phrase nearby can excuse a violation.

**Why it matters.** The appendix change log says "a naming lint guards OD-6", and plan F A3 depends on this guard for nine recreated documents. As written, it would pass one of the exact lines review E found. The three source documents are clean today (I read every use by hand), so nothing now misleads.

**Fix.**
- Replace the determiner rule with construct-only contexts: "the plan" followed by approve, propose, fit, item or membership, or preceded by approves, joins or beside.
- Allow "Actual against plan" only inside quotation marks, or only on the two rename rows.
- Limit the window to the same sentence.
- Keep these 12 sentences as a self-test of the lint: the 7 caught must fail, and all 12 should.

### N2 · Low · design "Words used here", Decisions, Appendix; `worked-portfolios.md` l.654; `design-appendix.md` l.75: "plan F" names a document

This is new in 16.6. "Plan" now also means the pack recreation plan, and the lint allowlists it (`\bplan F\b`). OD-6 gives "plan" one meaning. **Fix:** cite `F-pack-recreation-plan.md`, or call it "regeneration phase F".

### N3 · Low · `design-appendix.md` §6 l.105-110: limit IDs L1–L6 collide with the design's gap IDs L1–L7

The moved list keeps its labels: "L1. The influence scan…", "L3. Fallback eligibility is static…". In the design, L1–L7 are today's gaps, for example "L3 Objectives are system-declared". Plan F A2 takes L1–L7 into the lexicon from the design, so a derived document that cites "L3" is ambiguous. **Fix:** prefix the moved IDs (for example DL1–DL6), or state at the top of §6 that these IDs are local to it.

### N4 · Low · stale file pointers left after G-F2

- Design l.575: "Dispositions at function level are in `repo-reuse-and-gap-matrix.md`". The appendix table (rev 16.6) and plan F #5 rename it to `reuse-and-gap-matrix.md`.
- Design l.33: "`product-transition-and-roadmap.md` §2". Plan F retires that file (Q-F1 default), and the engagement path moves to #9. This note sits in the lint-excluded Introduction region, but it is an Architect's note, not the owner's text.
- `design-appendix.md` l.91: "The section references (§3.1, §7) point to `derivation-register.md`". Plan F moves that file to `evidence/`.

**Fix:** re-point all three, marked "pending approval" as elsewhere.

### N5 · Low · "Words used here", the Action entry: work-case origin and "a person creates"

- "Every carrier, work cases included, records one origin". Yet a work case links to several Findings (`0027:76-81`, with a composite primary key per Finding revision), and the entry does not say which one is its origin.
- "One unit of work a person creates" names today's trial action as a carrier. Today a trial action is recorded with `actor_kind = 'SYSTEM'` (`0016:131`).

**Fix:** state the work case's origin rule, for example "the Finding or plan item it was opened from; other links stay links". Write "in this design, a person creates", so the entry does not read as a claim about today.

### N6 · Low · §2.9 Actions row: the migration list omits the target trigger and cites a docstring

`chain_action_thread_target()` (`0051:34-50`) also matches each link to its Action's origin pair, so a plan-item origin must change it too. The row cites `0051:10` (the docstring) for `chain_action_thread_one_origin`. The constraint itself is at `0051:87-88`. **Fix:** add the trigger, and cite `:87-88`.

### N7 · Low · "Words used here", the manifest key entry: "kept under OD-6"

The key is kept as an *exception* to OD-6, by the Architect's call. "Under OD-6" can read as though the owner's decision sanctions it. **Fix:** "kept as a machine-only exception to OD-6 (Architect's call)".

### N8 · Info · `render_design_html.py:102-103`: the guard covers decision tables only

A blank line planted before the "Verification" row of the §2.9 register (in a scratch copy) rendered "ok" and silently dropped a row. The guard also uses `assert`, which is skipped under `python -O`. A general check would be: no table whose header row has the same cell count as its predecessor table and directly follows it after one blank line. Alternatively, `raise SystemExit` on any separator row that is not `|---`.

### N9 · Info · Figure 7 (and Figures 1 and 4 classes) in the dark theme

The HTML initialises Mermaid with `theme: dark` when the page is dark. `classDef actor fill:#ffffff`, like the existing `new` and `sys` classes, sets a light fill with no text `color:`. Under the dark theme the node text is probably light on light. This was not rendered here. It is not a regression in kind, but the L7 fix repeats the pattern. **Fix:** add `color:#18212f` to the light-fill classes.

### N10 · Info · the design now points to files pending approval

`decisions-register.md`, `decision-loop-specification.md` and the others are marked "as proposed in plan F, pending approval". If the owner changes a Q-F answer or a file name, the Decisions section, "Words used here" and the Appendix table must be re-pointed together.

## 3. Checks run (pack folder, head `d7c93657e`)

- `python3 check_manifest.py` printed "3762 checks passed, 0 failed", exit 0. That is +1 on rev 16.5: the naming lint.
- `python3 motivation_figures.py --check` printed "2 figures built; markers ['factor-structure', 'plan-against-actual']; missing []; unused []", exit 0.
- `python3 render_design_html.py layer4-transformation-design.md <scratch>/render.html` printed "ok", and `cmp` with the committed HTML found it identical.
- Lint plant: "Kobo is over plan on diesel this month." appended to a scratch copy gave "3761 checks passed, 1 failed", `FAIL naming lint: … worked-portfolios.md:657 …`, exit 1. The other 11 plants are in N1. Copies discarded.
- Renderer plant: the decision-table split was caught. The non-decision table split was not caught (N8). Copies discarded.
- `git status` was clean before this file was written.

## 4. Regressions and owner decisions

- I found no new claim about today's code that is wrong. The new code claims (the M4 carriers, the M5 constraints, the I5 lists) were all verified.
- The new Architect's calls are each marked "(Architect's call)" in place, and listed in Decisions:
  - Recommended comes from one search across decisions;
  - hard-bound override only through a recorded bound change;
  - Site threshold over portfolio;
  - unset tolerance raises all;
  - no-decision spending Action creates its own reactive item;
  - work cases carry an origin;
  - cost-side decisions start before the join;
  - manifest key `plan` stays.

  None contradicts OD-1 to OD-9. OD-2 ("site/portfolio setting") is refined, not overridden. OD-8 ("always joins the plan") is completed by the no-decision rule. OD-9's lanes and order are unchanged, and the refinement stays flagged "for the owner".
- The "Settled with the owner" paragraph now cites "OD-1 and OD-4 to OD-8, listed under Decisions" instead of repeating them. The Decisions table holds the owner's words, including "OD-7 and OD-8 yes". Nothing is lost.
- The cross-references the fix round touched resolve, except N4. Section numbers in the appendix (§4, §5, §6) agree with the worked-portfolios pointer to §6.

## 5. Not verified, and residual risk

- No Mermaid block was parsed (I2), and the dark-theme rendering was not viewed (N9).
- The lint was probed with 12 sentences, not exhaustively. Other phrasings may slip through until N1 is fixed.
- Residual risk not named in the pack: until N1 is fixed, plan F's A3 check "plan for a target fails" is weaker than it reads. The judgement read per document is then the only real guard for OD-6 in the recreated packs.
