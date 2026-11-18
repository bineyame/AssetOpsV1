# A-S5-overview Architect output review

Reviewer: fresh Claude reviewer. I did not author the Architect output, the S4-02 batch rulings or the S4-02 closeout.
Reviewed: commit `7affc6a1` on `plan/A-S5-overview`, diff `2f5ac495..7affc6a1` only. Later commits on the branch (`0e209e09` contest request, `09a5a40d` A-action-lifecycle) and any uncommitted edits in this worktree are out of scope.
Diff: `.agent/architect-A-S5-overview-{request,answers}.md`, the Architect log, `.agent/next-work-2026-10-14c.json` and `-14d.json`, `.ai/DECISIONS.md` (+10 lines, `D-2026-10-14-s5-selected-window-overview`) and the registry (+3 nodes, `A-S5-overview` resolved, `I-site-overview-read` gate, `I-assumption-consequence-history-read` target, W1 `exit_requires`, `real_pilot_requires`, `physical_peer_gate`). No product code.

Authority checked against: `.agent/architect-S4-02-batch-answers.md` (Q1-Q4), `.agent/S4-02-closeout-review.md` (M1, I1, deviation 1/2), `D-2026-10-13-s4-bounded-financial-basis` and its fuel-cost-1 addendum, `D-2026-10-14-s402-post-review-follow-ons`, `D-2026-10-12-s4-finding-phase-2-read-boundaries` (Site/UTC-day windows), `D-2026-09-17-timezone-validation-timing`, `production-shaped-mvp-technical-design.md` (`site_window_projection` :68, ingestion transaction :179, read contract :183), manifest screen `mini`, `tasks/S5-01-site-overview.md`, `tasks/G-05-*.md`, and precedent `.agent/A-S4-financial-review.md`.

## Verdict: ACCEPT with carries

- The three follow-on nodes exist, are sized, and match batch Q1-Q3 in substance. Q2 is an AND prerequisite of `I-site-overview-read` and so of `I-S5-01` and all four open `mini:*` paths, which is what batch Q2 ("before S5 Overview consumes current money") and closeout M1 asked for.
- Closeout I1 is applied: `I-assumption-consequence-history-read` now names foreign-Site refusal.
- `A-S5-overview` is resolved consistently with the prior financial, Finding and window decisions. It claims only `mini:1#a`, `mini:2#a` and `mini:4#a`, keeps `mini:3#a/b` with S4-04/S5-02, and keeps the 0-of-11 ordinary Findings reality (no ordinary amount; the one P01-power amount only as labelled Demonstration data).
- The next-work numbers reproduce exactly (below), and the "not a <=5% contest" statement is true of the pre-decision report it cites.
- The owner-absent rule is conservative and consistent with `USER_REVIEW_REQUIRED`.

No finding blocks the decision. The findings below are low-severity metadata/encoding fixes and Planner carries.

## Checks run (as observed)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs` (worktree at HEAD, registry identical to `7affc6a1`): exit 0, "Registry valid: 222 nodes, 11 linked pilot panels".
- `--verify-report .agent/next-work-2026-10-14d.json`: exit 0, ranked. Decision `stop_owner`, `I-evidence-acceptance-consequence-work` 2.02 vs `A-action-lifecycle` 2.009, gap 0.54%.
- `--verify-report .agent/next-work-2026-10-14c.json` against the committed registry: exit 3, `REFUSED [stale_input] registry`. Expected: the answers file says 14c is the pre-decision snapshot.
- 14c reproduction: in a scratch `git archive` of `7affc6a1` with only the `A-S5-overview` node reverted to `open`/`evidence:null`, `--verify-report` 14c exits 0 and `--next-work` regenerates a report byte-identical to the committed 14c (`select A-S5-overview` 2.198 vs `A-action-lifecycle` 2.009, 8.60%; Q2 node 1.998, E=3). This matches closeout M1's "sized M" sensitivity run exactly.
- 14d reproduction: `--next-work` on a scratch archive of `7affc6a1` is byte-identical to the committed 14d.
- `tools/check-agent-workflow.ps1` on the scratch archive: "Agent workflow check passed".
- Not run: `tools/check-all.ps1` scan guards (need `frontend/node_modules`, absent here, as instructed), backend pytest, frontend tests/build/tsc (no code in the diff).

## Follow-on nodes against the batch rulings

| Node | Batch ruling | requires / effort | Acceptance target vs ruling |
|---|---|---|---|
| `I-price-equal-start-succession` (S, persistence) | Q1 | `A-S4-financial`, `I-financial-assumption-store`; S matches "small follow-on" | Equal-start close + single insert, no empty interval, prior cutoff history, retry, stale/concurrent prior refusal. Omits `valid_from >= recorded_at` and the explicit 409 for >1 overlap / bounded assignment (carry P7). |
| `I-evidence-acceptance-consequence-work` (M, producer) | Q2 | `A-S4-financial`, `I-S2-02`, `I-financial-store`; M justified by transaction + selector/worker + idempotency + walkthrough, which is exactly Q2's "owns" list | Transactional durable work, dedupe by evidence and target/cause, worker recheck, unrelated no-op, no identical basis, late-power pending/stale -> recomputed, runnable schedule. Omits "preserve the FindingRevision-insert trigger" and "UI says queued only when a row exists" (carry P7). Consistent with technical design :179 ("create/coalesce recompute jobs in the same commit"). |
| `I-stored-demo-provenance` (M, persistence, area evidence) | Q3 | `A-S2-evidence`, `A-actor-identity`, `I-S2-02`, `I-finding-read`, `I-financial-read` | Server-authorized immutable tenant/Site-scoped publication designation, binds evidence IDs, traced into Finding/consequence reads, cautious mixed/unknown, heuristic retired, wrong-Site/client-only authorship refused, W1-exit and pilot gate. "Client-only" covers client-declared text; batch Q3 also says gateway credentials alone confer no authorship (carry P7). |

Sizing note: closeout M1 showed that sizing Q2 as S would have produced a 0% tie with `A-S5-overview` (owner stop). The Architect sized it M with a reason that tracks batch Q2's scope, under the owner delegation. I accept the sizing; it is also now moot for ordering, since 14d puts Q2 first in a 0.54% contest that was handled separately.

## Findings

### L1 (Low). Invalid UTF-8 written into `.ai/DECISIONS.md` and the answers file.

- **Where:** `.ai/DECISIONS.md:4113` (the new decision's first paragraph: `08:40<0x96>10:40` and `5<0x96>10%`); `.agent/architect-A-S5-overview-answers.md:1` (`<0x97>` in the title) and the 14c paragraph (`5<0x96>10%`).
- **What is wrong:** these are Windows-1252 en/em dash bytes, not UTF-8. The base `DECISIONS.md` at `2f5ac495` is valid UTF-8; after this commit it is not. GNU grep now reports "Binary file .ai/DECISIONS.md matches" instead of printing lines, and strict UTF-8 readers will fail or show U+FFFD.
- **Why it matters:** `DECISIONS.md` is the authority every agent searches by decision ID. A tool that silently treats it as binary hides decisions. No current guard catches it (`check-agent-workflow.ps1` only checks existence).
- **Fix:** replace the three bytes with UTF-8 `–`/`—` (or ASCII `-`). Optionally add a UTF-8 validity check for `.ai/*.md` to a guard.

### L2 (Low). The new W1-exit and real-pilot gates are unvalidated, invisible metadata.

- **Where:** registry `delivery_plan.waves.W1.exit_requires` and top-level `real_pilot_requires`.
- **What is wrong:** no checker reads either field (`grep` over `frontend/docs/architecture` and `tools` finds them only in the registry JSON). A renamed or misspelled node ID would pass every guard. `I-stored-demo-provenance` and `I-price-equal-start-succession` also appear nowhere in the next-work report (not in `candidates`, `eligible` or `unscored_work`) because neither lies on a panel path. The answers say "the current checker validates node links but does not itself enforce either checkpoint"; the second half is accurate, but the first half is true only of `requires`, not of these two fields.
- **Why it matters:** Q3 is a hard W1-exit and first-pilot gate per batch Q3. The only record that would stop a W1 exit is a field nothing reads and a report that never mentions the node.
- **Fix:** either have the registry checker validate that every ID in `exit_requires`/`real_pilot_requires` exists (and print the open ones), or record a standing item in `.agent/coordinator-handoff.md` that W1 exit and pilot activation must check these fields. Correct the answers sentence if the checker is not changed.

### L3 (Low). `mini:*` portion `technical_requires` lists were not updated with the new gate.

- **Where:** `delivery_plan.w1_panel_mapping` portions `mini:1#a`, `mini:2#a`, `mini:3#a`, `mini:4#a`.
- **What is wrong:** these lists otherwise enumerate every open ancestor (for example `I-site-overview-read`, `I-site-overview-ui`, `I-S5-01`), but none lists `I-evidence-acceptance-consequence-work`. `mini:3#a` also lacks `D-site-finding-index-rows` (pre-existing).
- **Why it matters:** scoring is unaffected, because `delivery_next_work.cjs` takes the open closure (the 14c/14d proofs do include the Q2 node). But a Planner or reviewer reading a portion sees an incomplete gate list for the very money gate this decision introduces.
- **Fix:** add `I-evidence-acceptance-consequence-work` to the four portions' `technical_requires` (and `D-site-finding-index-rows` to `mini:3#a`) in the next registry edit. This is a metadata correction, not a scoring change.

### I1 (Info). Baseline treatment of follow-ons is inconsistent.

Only Q2 is required in `queue_baseline_nodes` by the checker (it is an ancestor of baseline `I-S5-01`). Q1 and Q3 were also added, although the closeout review's guidance was that unscheduled follow-ons join the baseline when the Planner schedules them as queue tasks; meanwhile `I-assumption-consequence-history-read/ui` (also required before W1 exit by batch Q4) stay outside. Neither choice affects scoring. The Planner should add `tasks/README.md` entries for all four S4-02 follow-ons and make baseline membership consistent in the same change.

### I2 (Info). The owner-absent rule extends beyond the delegation window.

The rule is conservative and matches `USER_REVIEW_REQUIRED`: it lets build, fresh review, walkthrough preparation and stacked work continue, and holds only merge and promotion. It reads the owner's "(walkthrough or otherwise)" narrowly, and it is stated as a standing rule "for future owner-absent windows" although it was made under a two-hour delegation. Item 3 of the owner summary surfaces it; the coordinator should make sure the owner explicitly confirms or amends the standing part on return.

## Carries for the S5-01 Planner refinement

P1. **Dependencies.** `tasks/S5-01-site-overview.md` says only "Depends on: S4-02". It now also depends on a reviewed and merged `I-evidence-acceptance-consequence-work` packet (registry AND gate), and the registry has `I-S5-01.sequenced_after: ["I-S4-04"]`. Write both into the packet.

P2. **Which Finding the money card shows.** The decision allows an amount only for "the selected exact FindingRevision" and forbids sums or a Site total, but a selected window can hold several Findings, and S5-01 has no Site Finding list. The Planner must state the rule: for example, one bounded consequence per known Finding in the window, each with its own state and link, or a pinned Finding ID in the URL. Also state what the card shows when several Findings exist and none is pinned. Today's fixtures (0 ordinary qualifying, 1 demonstration) will not exercise this, so the rule must be specified and reviewed, not discovered.

P3. **Window and date semantics.** The decision says "selected half-open UTC window" and "a user date change selects a new window". Specify that a date maps to a UTC day, as S3 and S4-01 `finding-windows/{day}` do. Using the Site's local day would make timezone executable behaviour and trip `D-2026-09-17-timezone-validation-timing`. Also specify what reload preserves (requested window plus pinned revision IDs).

P4. **State vocabulary versus existing text.** The outline says "stale projection says pending", and the technical design :183 says "treats a lagging projection as pending". The decision now separates `UNASSESSED`/Unknown, `PENDING`, `STALE_PROJECTION` and `FAILED`, plus the money no-amount states (`UNPRICED`, quantity unavailable, pending, stale, superseded, mixed/unknown source, absent). Replace the outline sentence. Name the wire fields for each state and its freshness reason. Make the four states visually distinct at 1440 and 390.

P5. **Projection versus scoped read.** The technical design's `site_window_projection` (:68) has no consequence revision IDs, analytic watermark or freshness reason, all of which the decision requires. If S5-01 builds the table, the migration must add them. If it derives an equivalent scoped read, the packet must show how CURRENT is computed (accepted-source watermark equals the ledger, and analytic and consequence work are clean), not inferred from `NO_PENDING_DISPATCH`.

P6. **Demonstration label.** Reuse the S4-02b demonstration-source logic and its fail-closed `Source not confirmed` state. Do not add a second heuristic. Keep the label as bounded fixture evidence until `I-stored-demo-provenance` lands, and do not present it as general source authorship.

P7. **Follow-on packets (Planner, separate from S5-01).** Each follow-on packet should cite `.agent/architect-S4-02-batch-answers.md` Q1-Q3 as binding text and restore the details the registry targets dropped:
- Q1: `valid_from >= recorded_at`; 409 for more than one overlap or a bounded assignment.
- Q2: preserve the FindingRevision-insert trigger; the UI says "queued" only when a work row exists; coordinate with S2 ingestion without making it the sole trigger.
- Q3: gateway credentials alone confer no authorship; the owner settles the mixed/unknown wording at the W1 checkpoint.

P8. **Split rule.** If the Planner splits S5-01 into context/timeline and money, move the Q2 AND gate from `I-site-overview-read` to the money-consuming node in the same registry change. Otherwise `mini:1#a`/`2#a` stay blocked on Q2 for no contract reason. If S5-01 stays one slice, the current gate is correct.

P9. **Out-of-contract mock content.** The mock's service, battery, fuel-balance, renewable-opportunity, maintenance allowance, causal charging and recommendation claims stay out or appear as typed missing states (G-05 owns the Overview gap catalogue). `mini:3` shows "Finding list unavailable" without implying an empty list. Keep `USER_REVIEW_REQUIRED` and the owner-absent merge hold.

## Residual risk not named in the output

- W1 exit could be declared without `I-stored-demo-provenance` if the coordinator does not read `exit_requires`, since no guard or report surfaces it (L2).
- The money-card selection ambiguity (P2) is invisible with today's fixtures and would surface only with real data that has several qualifying Findings in one window, which is exactly the pilot case.
