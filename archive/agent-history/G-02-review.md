# G-02 fresh Claude review (V-01a mock-gap pilot)

Reviewer: fresh independent Claude (did not author G-02). Branch `task/G-02-v01a-gap-pilot`, HEAD `c85b435`, diff `42bd74d..c85b435`. Judged against `tasks/G-02-v01a-gap-pilot.md`, `.agent/architect-G-01-answers.md` (C5, C7) / `D-2026-10-13-g01-placement-and-orphan-scan-boundary`, G-01 carries C1/C6/C9 (`.ai/MILESTONE_REVIEW_BACKLOG.md`), the V-01a round-3 Addendum, and `.ai/WORKFLOW.md` review rules (raise only expensive-to-reverse defects, misleading claims, owner-only decisions).

## Verdict: ACCEPT

No blocking finding. The two findings below are wording/record fixes that can be done on the branch before merge or carried; neither changes behaviour, scoring or panel status. Q1-Q6 remain Architect/owner questions with fail-closed defaults; nothing here pre-empts them.

## Checks I ran (actual results)

- `npx.cmd vitest run` (frontend, after the scan commit): **61 files, 1445 passed**. It ran under this sandbox; the brief's expected esbuild failure did not occur.
- `npx.cmd tsc --noEmit`: exit 0. `npm.cmd run build`: exit 0 (chunk-size warning only).
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1 -Python .venv/Scripts/python.exe`: **All 9 guards passed**.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 212 nodes, 11 linked pilot panels`. `check_v69_ledger.py`: `v6.9 ledger valid: 110 screens, 88 distinct models, 258 panels`.
- `node --test`: `test_mock_gaps.cjs` 13/13, `test_delivery_next_work.cjs` 35/35, `tools/checks/test_missing_claim_scan.mjs` 17/17.
- `node tools/checks/missing-claim-scan.mjs`: `passed: 25 tagged placement use(s), 12 baselined legacy occurrence(s); baseline compared with merge-base 56254477fd on main and the seed ceiling 16.`
- Backend pytest not run (no backend change), as instructed. No servers started; `tools/g02-gap-evidence.mjs` (322/322) and the 36 screenshots are **not re-run by me** and remain the Implementer's evidence.

Independent verifications:
- **Registry/ledger invariance.** Comparing the base (`42bd74d`) and HEAD registry with every `gap_ids` key stripped and `mock_gaps` excluded: `nodes`, `delivery_plan`, `panels`, `areas`, briefs all identical; ledger identical after stripping `gap_ids`. The three pre-existing gaps (firmware, two finding-evidence) are byte-identical. Core paths, `core`, `state`, `technical_requires` and `panel_status` are unchanged; nothing moves toward Real.
- **Next-work scoring (item 4).** `--next-work --json` on the base tree vs HEAD: `eligible` and `candidates` identical; differences are only `fingerprints`, `gap_catalogue` (3 -> 23 gaps, 4 enrolled screens, `scoring: ignored`), and the G-02 phase `active` -> `in_review` in `unscored_work`/`global_stops`/`decision`.
- **Mutation spot-checks (reverted with `git checkout`, diff clean after).** (a) Rendering `COMMISSIONING_NOT_RECORDED` as a plain `<li>` outside `MissingClaim`: scan fails with `[unused_placement] readiness.commissioning.needed` and `[untagged_copy] ReadinessOverview.tsx:143`, exit 1. (b) Deleting the two new C7 cues from `PATTERNS`: fixtures go 15 pass / 2 fail, and the real-tree scan still passes (as expected: both occurrences are tagged). The C7 fixtures are therefore real.

## Review of the six points

1. **Catalogue.** One ID per distinct claim; shared IDs are the same fact (operating-view cell + analysis note; five commissioning placements; source-contact "Device connection not established here." / "whether data is arriving is not assessed here."; SLD reporting status note clause + "Readings are not assessed in this view."). Signal strength and firmware are separate `data_source/absent` gaps with empty `requires`, unrankable. Decision gaps reuse only `I-S1-01`/`I-S2-02`, which do prove the reads they name. The six `unplaced_reason`s are honest: three decision gaps render real reads; evidence-capability is deliberately on Site Evidence; obligation-policy and confidence-effect follow the Addendum's own Foundation/Readiness tables (which list no visible line for them), and Q3 correctly routes "should they get a visible Not-available-yet line" to the owner under the missing-data rule. Not an avoidance device.
2. **UI.** C5 split is correct: three `<p>` elements, three IDs, three unique placements, firmware untouched and still one element in every branch including loading (C6 asserted). Sites and SLD splits keep the rendered text exactly (verified by string assembly and by the Vitest exact-text map). The `MissingClaim` wrappers are inline `span`s replacing inline content; no CSS child selector is affected. Q1: the SVG slot text is an acceptable deviation pending the Architect (the component cannot tag SVG, and the claim is tagged at two adjacent Site-only HTML placements) - but see F1 about the contents-table cells.
3. **Scan.** The two new cues are exact and specific; the generic-copy fixture proves "Not recorded", "Gateway contact unavailable", "No results" and "Reading not recorded for this hour" stay out. The skipped merge-base comparison is visible in the result line, with an injectable runner and fixtures for both skip paths and the at-HEAD case. Baseline 15 -> 12 removes exactly the three G-02-owned entries (combined gateway line, Sites "Not available yet", combined aggregate line), each now tagged; no entry was added or relabelled.
4. **Next-work** unaffected (above).
5. **Stale evidence tools.** See F2's note: recommendation is not to rewrite them but to mark them superseded (carry).
6. **Checks** as listed.

## Findings

**F1 (low; misleading packet/walkthrough claim; fix wording on the branch or carry).**
- `.agent/G-02-review-packet.md:138` (Known deviations, Q1) and `.agent/G-02-questions-1.md` Q1 justify all untagged SLD restatements by "`MissingClaim` renders HTML only". That holds for the SVG `<text>` slots, but the contents-table slot cells are HTML: `frontend/src/sites/SiteSingleLineDiagram.tsx:855-858` renders `AWAITING_RUNTIME_OR_EVIDENCE` ("Readings not assessed here") via `SlotCell` in a `<td>` once per drawn component, and the Site branch is already distinguishable (`slots === null`). `MissingClaim` supports `as="span"`/`"td"`. So for those cells the reason is the Lab-shared component and the Architect's open Q1, not a technical impossibility.
- `.agent/G-02-owner-walkthrough.md:5` tells the owner "Every honest 'not available' statement on these four pages is now linked". That overstates coverage: the SLD per-node slots, contents-table slot cells, the `SITE_SLD_INTRODUCTION` sentence (`SiteSingleLineDiagram.tsx:94-100`), the "What the diagram draws" caption (`:786-792`) and the SLD panel description (`StoredFoundationViews.tsx:492`) are deliberately untagged.
- Why it matters: the owner decides on visible treatments partly on that sentence, and an Implementer of G-03..G-05 could copy the "HTML only" reason to leave taggable HTML untagged.
- Fix: one sentence in the walkthrough naming the SLD exception, and in the packet/Q1 separate "SVG slots (cannot tag)" from "table cells and captions (taggable; left pending Q1)". If the Architect answers Q1 with the alternative, tagging the Site-branch table cells is a small follow-up.

**F2 (low; omitted claim not catalogued; carry acceptable).**
- The mock's `sld:2` "What each part does" table has a "What it reports" column (`frontend/mockups/v69/index.html:840`, e.g. "Status missing 15:00-16:00", "Charge every 15 min · output-limit report missing"). The packet notes the omission (`G-02-review-packet.md:134`), but the registry records it nowhere: `G-sld-reporting-status.element_ids` lists only `sld:1.reporting-status`, and no gap has an `sld:2` element or an `unplaced_reason` for it. The task asks to catalogue each distinct omitted claim.
- Why it matters: it is the same per-part reporting-status fact, so the miss is a traceability hole, not a wrong claim; G-03/S7 closure could replace the sld:1 note and leave the sld:2 omission unrechecked.
- Fix: add `sld:2.what-it-reports` to `G-sld-reporting-status.element_ids` (same fact; no new placement needed). One-line registry change; checker and next-work unaffected.

## Carries and notes (not blocking)

- **C-a (stale evidence tools, item 5).** `tools/v01a-foundation-evidence.mjs:199` and `:201` already asserted pre-G-01 copy (it expects "...signal strength and firmware..."), and `tools/g01-firmware-evidence.mjs:39` asserts the pre-G-02 combined line. Both are historical evidence for merged slices (V-01a, G-01) whose owner checkpoints are done. Do not rewrite their expectations now (that would retroactively change recorded evidence). Add a header line to each saying "superseded for these screens by tools/g02-gap-evidence.mjs; expected to fail on the current tree" so a re-run's failure is not read as a regression. Backlog item.
- **C-b (Q2 residual).** "not available here", "not assessed ..." and "No ... record here" are tagged on these screens but are not scan cues; new untagged copy of that shape elsewhere passes. The packet names this; it is the Architect's C7 boundary. Each G-03..G-05 batch should repeat the per-element exact-text assertions (C9).
- **C-c (typing consistency, preference).** `G-readiness-commissioning` is `data_source/absent`, although its own copy says "No commissioning record type exists", which reads as a contract gap like productive-use. Both kinds are unrankable, so this has no effect now; worth a consistent rule before W1-exit allocation uses `missing_kind`.
- **C-d (pre-existing, outside G-02).** The packet's note that "Open Simulator Lab" / "Create a site in the Simulator Lab" may conflict with the client-facing no-simulator-language rule predates G-02; route to the backlog.
- Layout: G-02 changes no shell, table geometry, SVG or tab treatment. The gateway panel gains two paragraphs, and the other wrappers are inline. `tools/layout-evidence.mjs` was not run; the slice-specific CDP tool measured page scroll at 390, which is adequate for this non-layout-sensitive change. I did not re-run that tool.

## Residual risk not already named in the packet

- `readiness.sources.arrival` sits in a `foundation`-named component (`FoundationRevisionPanel.tsx` `RegisteredSourcesPanel`), and that panel is rendered only inside Readiness' Advanced disclosure (`StoredFoundationViews.tsx:789`). If a later slice also mounts it on the Site model page, the readiness-prefixed placement would render on a non-enrolled screen, and the scan does not check the screen (G-01 C10, still optional).

## Housekeeping

During the next-work comparison I exported base files with `git --work-tree=<tmp> checkout 42bd74d -- ...`, which briefly replaced index entries. I restored them with `git reset -- <paths>`. `git diff` and `git diff --cached` now show no content change except the pre-existing `.agent/coordinator-handoff.md`. Several files (for example `frontend/docs/architecture/mock_gaps.cjs` and `tasks/S1-0*.md`) may still show a stat-only `M` under `core.autocrlf=true` while their content equals HEAD. They are not staged; running `git status` after any `git add` of those exact paths, or a fresh checkout, clears the marker.
