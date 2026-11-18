# S4-02 registry closeout review

Reviewer: fresh Claude reviewer. I did not author the closeout, the S4-02a/b slices or the Architect rulings.
Branch `closeout/S4-02-registry`, commit `025f237a`, diff `a6c6a849..025f237a`. The diff is metadata only: registry, screen ledger, `tasks/S4-02-bounded-financials.md`, the packet and the next-work report. No product code changed.

Authority checked against: `.agent/S4-02b-phase-1-review.md`, `S4-02b-phase-2a-review.md`, `S4-02b-review.md` (including "Registry closeout notes for S4-02"), `S4-02b-fix-rereview.md`; owner records `owner-S4-02b-acceptance-2026-10-14.md` (CONDITIONAL) and `owner-S4-02b-money-demo-2026-10-14.md`; Architect batch rulings `AssetOpsV1-gap-planning/.agent/architect-S4-02-batch-answers.md` (gap-planning commit `cfd005c0`, Q1-Q4, especially the Q4 paragraph "Registry closeout now"); precedent `.agent/S4-02a-closeout-review.md` (L1, I2).

## Verdict: ACCEPT with carries

The closeout does what the reviews and the Architect authorized:
- seven nodes resolved, each on an accepted review;
- three W1 portions promoted, none Real;
- `assumptions:3#a` left open, and its obligation kept out of G-05;
- `I-S4-02.acceptance_target` corrected as Q4 requires;
- the next-work decision reproduces exactly.

Two carries need action before merge or before acting on the selection (M1, M2). The rest are low-severity wording and accuracy fixes.

## Node-by-node check

| Node | Accepting review | Anchors verified at the cited lines | Holds "ordinary data yields no amount" |
|---|---|---|---|
| `I-financial-store` | S4-02b-review closeout notes ("May resolve", migration 0011) | 0011 :43 `financial_consequence_revision`, :187 `financial_consequence_work`, :237 / :250 append-only triggers, :349 / :363 dirty triggers; `postgres_consequence_store.py` `append`:160, `chain`:297 | yes |
| `D-financial-basis` | same | `fuel_cost.py` `quantify`:284, `select_window_price`:440, `consequence`:500; `recompute.py` `derive`:65, `ConsequenceRecomputeWorker`:89; `backend/conversions/s4-power-demo-cases-v1.json` exists | yes |
| `I-financial-read` | same | `finding_api.py` route :246, revision selection :250-268, `bridge_consequence`:347; `consequence_read.py` `read`:143, `dto`:81 | yes |
| `I-consequence-history-read` | same | `finding_api.py` :252 / :256 / :268 (foreign-ID 404s); `consequence_read.py` `locate`:140, currentness :200 | yes |
| `I-financial-ui` | same ("once H1 is fixed"); H1 fix accepted in S4-02b-fix-rereview | `FindingConsequence.tsx` `HowWorkedOut`:212, `Headline`:370, `FindingBridge`:405, `ConsequenceHistory`:515; `SiteFinancials.tsx` `SiteFinancialsOverview`:431, `FindingBridge` mount :478, `PriceInUse` mount :492; `financialsClient.ts` `FindingConsequencesBody`:201 | yes |
| `I-S4-02b` | S4-02b-review + fix-rereview ACCEPT + owner checkpoint | refers to the nodes above | yes |
| `I-S4-02` | Q4: may resolve only once `acceptance_target` is corrected, which it is | n/a | yes |

Portions:
- `financials:1#a`, `financials:2#a` and `assumptions:1#a` are `delivered` with `delivered_by ["I-S4-02"]`. Each has evidence that resolves, plus anchors. Each anchors text states 0 of 11 ordinary Findings, the F01-gateway `POWER_COVERAGE_GAP`, and that the only positive amount is the labelled P01-power demonstration case. Panels moved from `gap` to `partial`. None is Real. W1 gates and scoring parameters are untouched.
- `financials:3#a`/`3#b`, `assumptions:2#a` and `mini:4#a` are not claimed. `G-foundation-financial-assumptions` and `G-assumptions-human-edit` are untouched and stay open, as the S4-02b review requires.
- `assumptions:3#a` stays `open`. The price-history subclaim is recorded as built evidence in the `I-S4-02` text. No G-05 gap or `panel_portion_ids` entry absorbs the consequence-at-cutoff obligation, which matches Q4.

Ledger rows `financials` and `assumptions`:
- Both state the conditional owner acceptance, that the panels are not Real, and the no-ordinary-amount caveat.
- Task strings keep the plus-joined form.

## Deviations raised by the packet

1. **`assumptions:3` panel stays `gap`, although Q4 says "panel partial". Acceptable.** The checker derives `partial` only from a delivered portion. The price-history subclaim is not its own portion, so `gap` is the correct mechanical result. It also under-claims rather than over-claims. The two ways to show `partial` are:
   - split `assumptions:3#a` into a delivered price-history portion and an open consequence-at-cutoff portion, which is a mapping change that needs its own mapping review; or
   - change the checker rule.

   Neither belongs in a metadata closeout. The deviation is stated in the `I-S4-02` evidence text and is visible on the ledger row. The Architect should be told so the Q4 wording ("its panel partial") is not later read as unmet. That is a notice, not a fix.

2. **New nodes `I-assumption-consequence-history-read` and `I-assumption-consequence-history-ui`. The shape is correct.**
   - Kind, layer, area, owner, effort `S`, `open` status and a non-null task label are all present.
   - `requires` chains read → UI on the resolved `I-consequence-history-read`, `I-assumption-history-read` and `I-assumption-history-ui`.
   - Both are wired into `assumptions:3#a.technical_requires`.
   - The acceptance targets follow the Q4 "Code" paragraph. The read target says "tenant/Site-scoped" and "paged" but does not spell out "foreign-Site refusal", which Q4 lists as a review item (see I1).
   - Without these nodes the next-work run refuses ("open core portion has no open gate"), so adding them is required. It is not new scope.
   - **They should not join `queue_baseline_nodes` yet.** The baseline lists the nodes the planned S1-S7 queue is expected to close, and `tasks/README.md` has no task for this follow-on. The checker agrees: no baseline node depends on them, and checker line 175 forces baseline membership only for tasks in the queue. When the Planner schedules the follow-on as a queue task (Q4 requires it before W1 exit), both nodes must join the baseline in that same change.

## Findings

### M1 (Medium, carry before the next selection is acted on). The three other Architect follow-ons have no registry nodes, and one of them changes the next-work decision depending on how it is sized.

- **Where:** `v69-dependency-registry-pilot.json`, for Architect batch Q1, Q2 and Q3.
- **What is wrong:**
  - Q2 (enqueue consequence work on evidence acceptance) is ruled "an S4-02 consequence follow-on, before S5 Overview consumes current money".
  - Q3 (stored demonstration provenance) must land "before any real-Site pilot and before W1 exit".
  - Q1 (equal-start SUCCESSION) is "before relying on future schedule replacement".
  - None of the three is a node, so nothing in the registry gates S5 on Q2, or W1 exit on Q3.
- **Why it matters:** the selected next work is `A-S5-overview`, which is exactly the surface Q2 gates. I modelled Q2 the way the checker requires: an open node gating `I-site-overview-read`, propagated into the open `mini:*` portions and added to `queue_baseline_nodes` (the checker refuses otherwise: "I-S5-01: queue baseline omits open technical prerequisite"). I reran `--next-work` with a scratch read-shim; the committed files were not changed. Results:
  - **Q2 sized S:** `A-S5-overview` 2.198 and the Q2 node 2.198. Decision `stop_owner`, gap 0.00% (contested, so it goes to the owner).
  - **Q2 sized M:** `A-S5-overview` 2.198 against `A-action-lifecycle` 2.009, gap 8.60%. The selection is unchanged (select with notice), and the Q2 node ranks third at 1.998.

  So the current decision rests on a missing gate whose size decides whether the owner must choose. Q1 and Q3 do not alter scoring:
  - Q1 has no W1 panel path.
  - Q3 is a W1-exit and pilot gate, and the Architect lets reviewed S4-02 money claims close independently of it.

  Q1 and Q3 still risk being lost: Q3 especially, because W1 exit could otherwise be declared without it.
- **Fix:** have the Architect or Planner register Q2 as a sized node gating the S5 Overview money read, in `queue_baseline_nodes`. Then rerun `--next-work`, and treat the result (select, or an owner stop if it is contested) as the decision. Record Q3 as a W1-exit and pilot gate, and Q1 as an unscheduled follow-on, so neither is lost. This is a registry change that needs an Architect node definition, so per precedent L1 it does not belong in this closeout. But the `A-S5-overview` selection should not be acted on until it is done.

### M2 (Medium, merge-order carry). The registry cites a file that does not exist on this branch or on main.

- **Where:** the `I-S4-02` evidence and `acceptance_target` basis, and the acceptance targets of both new nodes, all cite `../../../.agent/architect-S4-02-batch-answers.md`.
- **What is wrong:** the file exists only in the `AssetOpsV1-gap-planning` worktree (commit `cfd005c0`). I checked every other `../../../` path the diff adds, and all of them resolve. The registry checker does not validate paths embedded in text, so all guards pass anyway.
- **Why it matters:** the authority for resolving `I-S4-02` against a corrected target, and for keeping `assumptions:3#a` open, would be a dead link on main.
- **Fix:** merge the gap-planning commit that carries the batch answers (and the decision addendum) to main before or together with this closeout.

### L1 (Low). The packet misstates the next-work report.

- **Where:** `.agent/S4-02-closeout-packet.md:26`.
- **What is wrong:** the packet says "The two new follow-on nodes do not appear in candidates or unscored_work". The regenerated report lists `I-assumption-consequence-history-read` as an **eligible** candidate (S, score 1.373, `assumptions:3` d=1) and `I-assumption-consequence-history-ui` as blocked on it.
- **Why it matters:** it does not change the decision (1.373 is far below 2.22), but the coordinator will see a ranked, eligible node whose task is "unscheduled".
- **Fix:** correct the sentence.

### L2 (Low). The ledger lists the W1 core obligation inside the G-05 list.

- **Where:** `v69-screen-ledger.json`, `assumptions.unknown_or_empty`.
- **What is wrong:** the text reads "Remaining G-05 gaps: …, consequence revisions at cutoff (assumptions:3#a, W1 core follow-on, not G-05), human edit". It says "not G-05", but it sits inside the G-05 enumeration. Q4 says not to move this obligation into the G-05 bucket.
- **Fix:** move it to its own sentence, for example "W1 core still open: assumptions:3#a consequence revisions at cutoff (follow-on, Architect Q4)."

### I1 (Info). The new read node omits one Q4 review item.

`I-assumption-consequence-history-read.acceptance_target` does not name foreign-Site refusal, which Q4 lists among the review items ("cutoff boundaries, pagination, foreign-Site refusal and app/mock states"). "Tenant/Site-scoped" implies it. Add it when the follow-on is planned.

### I2 (Info). One anchor label is loose.

The `financials:2#a` anchors and the packet say "SiteFinancials.tsx PriceInUse:492". Line 492 is the mount (`<PriceInUse … />`); `function PriceInUse` is at :497. `I-financial-ui` correctly calls :492 a mount. This is the same class as precedent I2. Use :497, or write "mount :492".

## Checks (as observed)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0. "Registry valid: 219 nodes, 11 linked pilot panels".
- `.venv\Scripts\python.exe frontend/docs/architecture/check_v69_ledger.py`: exit 0.
- `powershell -NoProfile -ExecutionPolicy Bypass -File tools/check-all.ps1`: "All 9 guards passed", exit 0. That covers architecture seams, navigation truthfulness, agent workflow, dependency registry, delivery checker fixtures, mock-gap fixtures, the missing-claim orphan scan and its fixtures, and the screen ledger.
- Next-work, regenerated to scratch with `--next-work --out <scratch>/nw.json`: exit 0, ranked. The output is byte-identical to the committed `.agent/next-work-2026-10-14b.json` (diff empty). The decision line is identical: `select A-S5-overview`, 2.22 against `A-action-lifecycle` 2.009, gap 0.095 (9.50%, within 5-10%), selected by the published tie-break with an owner notice.
- `--verify-report .agent/next-work-2026-10-14b.json`: exit 0. `--verify-report` on the scratch report: exit 0.
- Sensitivity run for M1: a scratch read-shim adds a Q2 node to the registry in memory only. The results are in M1.
- Anchors: every cited file:line was read at `025f237a`, as listed in the table above.
- Evidence paths: every `../../../` path the diff adds resolves, except `architect-S4-02-batch-answers.md` (M2).
- Not run: backend pytest, frontend `npm.cmd test`, the build and `tsc`. The diff contains no code, so they were out of scope. The S4-02b browser evidence (90/90 at 1440/390) is cited from the accepted reviews; I did not rerun it.

## Residual risk not named in the packet

- If Q2 is sized S when it is registered, the current "select with notice" becomes an owner stop (M1). The coordinator handoff should not present `A-S5-overview` as settled until then.
- `I-assumption-consequence-history-read` is eligible and ready now (no open prerequisites), with an unscheduled task label. Once the top candidates are taken it could be selected with no task packet behind it. The Planner should create the packet before that happens.
- The Architect's "panel partial" wording and the registry's `gap` now differ, so a later W1-exit reader could take either as the record. Resolve this by notifying the Architect (deviation 1).
