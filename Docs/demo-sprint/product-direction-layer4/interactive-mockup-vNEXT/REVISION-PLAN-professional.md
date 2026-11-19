# Revision plan: professional layout, rev 16.6 alignment, plain words

Owner, 19 Nov (verbatim): "let it be more professional in temrs of ites usage of space and modern state of the art ui/ux as well as not using technical workds that should not be user facing." Content source: `../layer4-transformation-design.md` rev 16.6 (§1.4, §2.4–§2.8, OD-1 to OD-9) and `../worked-portfolios.md`.

## Screens that change

| Screen | Change (design anchor) |
|---|---|
| Act first `#/portfolio/act-first` | Finding triage first (§2.8): the issues needing a decision, each with its site, what is at stake, who decides (role, §2.6) and the decision link. The plan sits beside it as a summary panel: status "Proposed by the system · awaiting the operator executive's approval", spend and crew meters, modelled value, the spend threshold, and "Open the plan". |
| The plan (new drill-down) `#/portfolio/act-first/plan` | The full plan that Act first held: items, Actions per item (from each option's cost lines) with creator, owner and due date, the switches, budget and crew meters, items left out and why, the cases. Adds an approval panel: who proposes (system), who approves (operator executive), version, state (§2.5). Reached from Act first; no new rail or tab item (§2.8 frame). |
| Decision pages `#/decision/<id>` | A "Who decides" strip: the system recommends; the accountable role chooses (§2.4 step 2); the Actions that choice creates, with origin (the Finding), plan membership (the item), creator, owner, due; release rule under the spend threshold (§2.4 step 4, OD-8). |
| Overview, Outcomes by site, site pages, Financials, What changed | "Plan" as the factor-table column and "against plan" become "Target" and "against target" (OD-6, §2.8 Assure row, G-F5). "Plan" stays only for the new portfolio plan. What changed shows Actions with their owners and the plan's review (§2.8). |
| Shell | Theme toggle (light, dark, system) in the top bar; footer reworded in plain words; review bar made compact and quiet (review tooling, exempt). |

Roles are shown where decisions and records happen (decision page, plan approval, Action rows), never as a role switch or view (§2.6: "they are not views").

## Layout system

A new stylesheet `theme.css`, loaded last, so the re-based v7.0 sources stay byte-reproducible:
- tokens on `:root`: surfaces, text, lines, accents, status tones; dark values under `prefers-color-scheme: dark` (unless `data-theme="light"`) and under `data-theme="dark"`;
- a 4 px spacing scale (4, 8, 12, 16, 24, 32), one panel padding, one gap between panels;
- a type scale (12, 13, 14, 16, 20, 24) with tabular numbers in tables and figures;
- a content max-width and a 12-column grid for two-up and side-panel layouts; the side panel drops below the main column under 1200 px;
- dense, calm tables: 8 px × 12 px cells, sticky headers in scroll regions, right-aligned numbers, zebra-free with hairline rules;
- laptop widths 1280 and 1366 px as first-class breakpoints, phone width kept free of page scroll.

## Vocabulary sweep

Rendered text of every screen and sampled evidence drawers (jsdom harness `tools/render_text.cjs`, review bar removed) is scanned by `tools/vocab_check.cjs` against a banned list: option and record codes, factor keys and snake_case keys, evidence-class codes (EXPOSURE, MODELLED…), L1–L3 and B1–B3, CH1–CH5, OD-/D-numbers, "registry", "observer", "evaluator", "manifest", "fixture", "spec", "slice", "oracle", "canonical", "replay" without plain wording, "lever", "evidence class", "against plan", "structure evaluator". Replacements are plain operator words ("target", "how sure we are of it", "what can be changed", "re-run on your recorded days"). The check fails on any hit; proof by a planted violation, then revert.

## Verification

1. Rebuild per README (`rebase_v70.py`, `evaluate_structure.py`, `gen_fixtures.py`, `build.mjs`).
2. `hand_typed_scan.py` 0 hits; `../check_manifest.py` passes; `vocab_check.cjs` 0 hits, planted-violation proof recorded.
3. jsdom render of every route for three operators with 0 script errors; the Lakeside switch cases re-checked on the plan page.
4. Playwright audit and screenshots (`tools/run-audit.sh --shots`) need a local Chromium and playwright-core; if they cannot be installed here, they are reported "not run" with the reason, not as a pass.
