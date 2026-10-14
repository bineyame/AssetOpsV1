# S4-02 registry closeout packet

Branch `closeout/S4-02-registry` (from main `a6c6a849`, which merges S4-02b). Registry/ledger metadata only; no product code. No review verdict or owner approval is written here; acceptance is cited from `.agent/owner-S4-02b-acceptance-2026-10-14.md` (CONDITIONAL) and the reviews `.agent/S4-02b-review.md` (ACCEPT with carries, H1 fixed) and `.agent/S4-02b-fix-rereview.md` (ACCEPT). Precedents: `.agent/S4-02a-closeout-packet.md`, `.agent/S4-03-closeout-packet.md`.

## Changed
- `frontend/docs/architecture/v69-dependency-registry-pilot.json`
  - Nodes `I-financial-store`, `D-financial-basis`, `I-financial-read`, `I-consequence-history-read`, `I-financial-ui`, `I-S4-02b`, `I-S4-02`: `open` -> `resolved`, evidence (reviews, packet, owner checkpoint and money-demo ruling, decision `D-2026-10-13-s4-bounded-financial-basis`, Architect answers, 90/90 browser claims at 1440/390, commits, merge a6c6a84) and anchors verified against the code (migration 0011 :43/:187/:237-250; `postgres_consequence_store.py` append:160, chain:297; `fuel_cost.py` quantify:284, select_window_price:440, consequence:500; `recompute.py` derive:65, worker:89; `finding_api.py` route :246, exact revision :250-268, `bridge_consequence`:347; `consequence_read.py` locate:140, read:143, dto:81; `FindingConsequence.tsx` FindingBridge:405, HowWorkedOut:212, ConsequenceHistory:515; `SiteFinancials.tsx` SiteFinancialsOverview:431, PriceInUse:492). Every evidence text states ordinary data yields no amount today and the positive amount is the labelled authored P01-power case.
  - `I-S4-02.acceptance_target` corrected per Architect batch ruling Q4 (`.agent/architect-S4-02-batch-answers.md`, merging to main): three W1 portions promoted, `assumptions:3#a` stays open pending a Site consequence-history-at-cutoff read/UI follow-on.
  - Portions `financials:1#a`, `financials:2#a`, `assumptions:1#a`: `open` -> `delivered`, `delivered_by ["I-S4-02"]`, evidence, anchors, caveat. Panels `financials:1`, `financials:2`, `assumptions:1`: `gap` -> `partial`. None Real; W1 gates and scoring parameters untouched.
  - `assumptions:3#a`: stays `open`, panel stays `gap`. Price-history subclaim recorded as built evidence in the `I-S4-02` evidence text. The obligation is not moved into G-05.
  - NEW nodes `I-assumption-consequence-history-read` and `I-assumption-consequence-history-ui` (open, task "S4-02 Assumptions-history follow-on (unscheduled)", acceptance_target from Architect Q4 "Code" paragraph), added to `assumptions:3#a` technical_requires. Needed because the next-work checker refuses ("open core portion has no open gate") when `assumptions:3#a` is open with every gate resolved. Not added to `queue_baseline_nodes` (the checker passes without); the reviewer should confirm that choice. They are unscheduled and carry no task packet.
  - Not touched: `G-foundation-financial-assumptions`, `G-assumptions-human-edit` (the S4-02b reviews add no evidence for them), `financials:3#a/3#b`, `assumptions:2#a`, `mini:4#a`.
- `frontend/docs/architecture/v69-screen-ledger.json`: `financials` and `assumptions` rows (claim, interaction, conditional caveat, remaining G-05 gaps, assumptions:3#a named as W1 follow-on not G-05); task strings left as "S4-02a + S4-02b (S4-02 closeout)".
- `tasks/S4-02-bounded-financials.md`: Status done with outcome line.
- `.agent/next-work-2026-10-14b.json`, this packet.

## Checks (as observed)
- `check_v69_dependency_registry.cjs`: exit 0 (a first attempt to set `assumptions:3` panel to partial failed: "panel_status partial should be gap"; the checker derives partial only from a delivered portion, so it was reverted to gap).
- `check_v69_ledger.py`: valid (110 screens, 88 models, 258 panels).
- `tools/check-all.ps1`: All 9 guards passed.
- `--next-work --out .agent/next-work-2026-10-14b.json`: ranked (an intermediate run refused until the follow-on gate nodes existed). `--verify-report .agent/next-work-2026-10-14b.json`: exit 0.

## Next-work decision
- `Decision: {"action":"select","selected":"A-S5-overview","top":"A-S5-overview","top_score":2.22,"second":"A-action-lifecycle","second_score":2.009,"gap":0.095,"notice":"Ranking notice: A-S5-overview 2.22 vs A-action-lifecycle 2.009 (gap 9.50%, within 5-10%); selected A-S5-overview by published tie-break (fewer unresolved technical gates, lower effort, stable ID). Record in .agent/coordinator-handoff.md.","reason":"gap within 5-10%: tie-break selection with owner notice","user_review_required":null}`
- Top A-S5-overview 2.22, second A-action-lifecycle 2.009, gap 0.095 (9.50%), tie-break: fewer unresolved technical gates, lower effort, stable ID.
- `unscored_work`: I-G-01, I-G-02 (resolved, packet done), I-G-03, I-G-04, I-G-05 (open, not_started). The two new follow-on nodes do not appear in candidates or unscored_work.

## Questions
1. Should the two new follow-on nodes join `queue_baseline_nodes`, and does the follow-on need its own task/slice before W1 exit (Architect Q4 says yes)?
2. `assumptions:3` panel stays `gap` by the checker rule although the ruling says "panel partial"; accept, or change the checker?
