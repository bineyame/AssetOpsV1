# W1-UX plan re-review after fix round 1 (fresh independent Reviewer, 2026-10-16)

Scope: `git diff 55620a8c..606dc862 -- tasks` (umbrella and W1-UX-01..05), judged against `.agent/W1-UX-plan-review.md` (Mediums 1-5, Lows 6-10), `.agent/planner-W1-ux-fix-brief.md` and the Architect ruling `D-2026-10-16-w1-ux` (`.agent/architect-W1-ux-answers.md`). Read-only; no suites run.

## Verdicts

| Packet | Verdict | Blocking findings |
| --- | --- | --- |
| W1-UX-mockup-fidelity (umbrella) | ACCEPT | none |
| W1-UX-01 shared presentation | ACCEPT | none |
| W1-UX-02 Site and money | ACCEPT | none |
| W1-UX-03 Evidence and performance | ACCEPT | none |
| W1-UX-04 Actions and work | ACCEPT | none |
| W1-UX-05 Configuration and health | ACCEPT | none |

All five Mediums are resolved. The Lows below are worth folding in when a packet is next touched, or by the slice's implementer. None of them blocks.

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 239 nodes, 11 linked pilot panels`, exit 0.
- Walkthrough tools: all 12 tools named on this revision exist in `tools/`. `s602b_verification_walkthrough.py` (prepare/links/serve/capture/drop), `s603_site_work_walkthrough.py` (prepare/serve/attest/drop) and `s701_health_walkthrough.py` (prepare/serve/attest/deliver/drop) exist on their pending branches with the modes the table names. I checked the route templates against `frontend/src/shell/operatorSiteRoutes.ts` (Foundation `:foundationView` for `readiness`/`sld`, `/foundation/changes/{change}`) and against the tool-printed formats (`s302` `?view=analysis&day=&revision=`, `s701` `/sites/{site}/assets/{asset}`).
- S6-02b floor sentences: "Trial missed a safety or service limit" and "Target not met" are confirmed in `tasks/S6-02b-verification-ui.md:15` and in `verificationWords.ts:16-17` on `task/S6-02b-verification-ui`.
- Scanner reality: `frontend/src/test/productVocabulary.ts` already supports per-term `caseSensitive`, single-value exemptions and `data-vocabulary-reference` identifier values. The packet's ratchet builds on it instead of loosening it.

## Mediums from the first review

1. **Verdict wording: resolved.** `W1-UX-01:11` keys outcome wording on (outcome, reason, source class). It separates INEFFECTIVE+GUARDRAIL_FAIL ("Trial missed a safety or service limit", with metric, value, threshold and unit) from target-only ("Target not met"). VERIFIED keeps the "five-minute sampled" guardrail scope and says it is not continuous SOC proof. Demo-source outcomes say "policy trial" and "no savings or realized benefit". S6-02b's guardrail-fail, target-miss and unknown-fact sentences are named as the floor. See Low A for test enumeration.
2. **Staged scan enforcement: resolved.** `W1-UX-01:13-15` specifies a versioned W1 term set plus a pattern matcher for raw enum and reason-code shapes, UUIDs, digests and versions. Mutation tests prove it. Each route opts in as its slice migrates it, existing scans stay on unmigrated routes, and nothing may be exempted or weakened. The umbrella gate (`:50`) puts all 26 routes on the full set before the walkthrough. See Low B on the pattern shape.
3. **Disclosure scan and closed-disclosure test: resolved.** `W1-UX-01:15`: the disclosure is scanned against a narrower technical list and is never exempted wholesale. The single-value exemption rule stays, and the refinement goes to the Architect under D-2026-10-04 before implementation. `W1-UX-01:17` adds the shared test. With the disclosure closed, it covers every unassessed, pending, stale, unknown, refused, withheld-money and proved-zero case, and checks that the plain state sentence, its scope and its "as of <time>" stay visible. UX-02..05 each repeat it (shared-acceptance paragraph), and the umbrella repeats it at `:50`.
4. **"As of" time in the default reading: resolved.** Umbrella `:11` covers it, as do rows `finding-history`, `sitefindings` and `sitework`, plus `W1-UX-02:37` and `W1-UX-04:33`. Only opaque cursor/cutoff tokens and raw IDs move to detail. UX-05 retains the precise selected time (`:59`).
5. **Walkthrough table and Sites lead: resolved.** Umbrella `:56-89` has a 26-row map with tool, modes, route template, and the state to show. It includes `s405`, `s502` and `v01a`. Tool-printed URLs are authoritative, and a skipped step is recorded as "not run". UX-05's closeout writes `.agent/W1-UX-combined-owner-walkthrough.md`, and the coordinator checks it before the session is scheduled. The Sites lead is now "Which site should I open?" (umbrella `:15`, `W1-UX-02:37`).

The earlier Lows are folded in: anchors corrected (`SitesIndex.tsx:133-180`, `SiteFindingHistory.tsx:172-260`); the shared map wraps, then replaces, the existing word maps one slice at a time; the capture pattern (`tools/v01a-foundation-evidence.mjs`) is named, with "not run" recording; UX-01 starts after S6-02b, S6-03 and S7-01b; UX-04 is M in two phases with a split rule; the PENDING_REASSESSMENT example is fixed; the unknown-as-zero chart case is added; a weakened fail-closed assertion now blocks review.

## Architect ruling conformance

The packets match `D-2026-10-16-w1-ux`:
- Substantive depth goes to the owning Analysis/Evidence/Plan/History/Verification destination. That destination is visible as the same named tab or view link at 1440 and 390 px (`W1-UX-01:7`; the shared-acceptance paragraph in each slice; umbrella `:93`).
- A contextual Analysis tab is added only where no suitable destination exists, and never as an empty tab. The closed disclosure holds only a few labelled exact references.
- Approved labels get first-use explanations and grant no positive claim.
- The banned list matches the ruling and applies inside Analysis/Evidence too. Test data stays qualified.

The fixes add no honest-state risk that I could find.

## Findings (all Low, non-blocking)

**A. Low - W1-UX-01:23, the phase 1 matrix does not list the verdict cases.**
- What is wrong: the wording rule at `:11` is binding, but the phase 1 proof lists only current/pending/stale/unknown/refused/zero. The first review asked for explicit matrix cases: INEFFECTIVE+GUARDRAIL_FAIL, target-only INEFFECTIVE, INCONCLUSIVE with a known failure, and demo-source VERIFIED.
- Why it matters: UX-04 phase 2 covers most of these where the screens consume the map. No packet tests the demo-source "policy trial / no savings" label.
- Fix: add those four cases to UX-01's phase 1 proof.

**B. Low - W1-UX-01:13, the raw-code pattern shape is unstated.**
- What is wrong: underscore enums (`GUARDRAIL_FAIL`) are easy to match by shape. Single-word enums (`CURRENT`, `STALE`, `VERIFIED`) collide with ordinary words when matched case-insensitively, and an all-caps shape collides with units and acronyms (SOC, UTC, kW).
- Fix: state that single-word enums are listed as `caseSensitive` terms (the scanner already supports this), and that the shape pattern targets uppercase underscore tokens with an allow-list for units and acronyms. A mutation test should prove each.

**C. Low - umbrella:58, the walkthrough authorship timing and one mode mismatch.**
- Timing: UX-05's closeout writes the combined document, but UX-05 is not necessarily the last slice to merge. If UX-02..04 merge later, the captures predate their migration. The coordinator gate catches this, but the packet should say the document is refreshed, or finished, after the last W1-UX merge. UX-05's own packet does not mention the duty, so add one line there.
- Mode mismatch: `s2_demo_walkthrough.py` has `run`/`serve`/`setup`, not `prepare` (row `evidence`, "P/S").
- Prerequisite: `v01a_foundation_walkthrough.py` needs `tools/s4_finding_cases.py run` first. The ordered-commands section of the document should carry it.

**D. Low - registry drift for I-W1-UX-01.**
- What is wrong: `v69-dependency-registry-pilot.json` still gives `I-W1-UX-01` only `A-S5-overview` as a requirement. The packet now says UX-01 starts after S6-02b, S6-03 and S7-01b merge.
- Why it matters: the registry's readiness view would show UX-01 as ready too early.
- Fix: add `I-S6-02b`, `I-S6-03` and `I-S7-01b` to its `requires`.

## Residual risk

- The disclosure scan refinement depends on an Architect amendment under D-2026-10-04 before UX-01 implementation. Until it is ruled, UX-01 phase 2 cannot finish its disclosure scan.
- The residual risks from the first review still hold. The UX-04 reviewer must diff `siteActionVerification.test.tsx` (now an explicit gate). Derived graphics must not imply values the read did not give (now covered by the unknown-chart case).
