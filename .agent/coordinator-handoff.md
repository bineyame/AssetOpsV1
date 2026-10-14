# Coordinator handoff (2026-10-09, S2 complete; pre-S3 startup)

A fresh coordinator starts from this file; do not re-derive what it states.

## Current state (2026-10-13, supersedes everything below)
- **UPDATE 2026-10-14 (latest, 28):** S4-02d merged to main `00677d37` (slice review `.agent/S4-02d-review.md` ACCEPT, R-1..R-3 Low carries; backlog "S4-02d carries"; registry resolves `I-analytic-finding-worker-schedule`); plan/test-suite-speed merged `1c7595de`; guards 9/9. Schedule install gate CLOSED for demo/walkthrough/pilot. **Active: OPS-01** on `task/OPS-01-backend-test-speed` (owner instruction `.agent/owner-process-speed-2026-10-14.md`; next-work `14n` STOP active_task). Phase-1 implementer running (brief `.agent/OPS-01-phase-1-brief.md`). Then by ranking: `I-late-reading-series-and-money-limit` before S5-01 (owner walkthrough). Apply memory `turnaround-speed-rules`.
- **UPDATE 2026-10-14 (27):** main `0d137768`: plan/S4-02c-architect merged (F1 ruling, S4-02c registry closeout, S4-02d packet: plan review RETURN -> Codex fix rounds 1-2 -> N1 checked; storage ratified `D-2026-10-14-s402d-schedule-storage-and-install-gate`). Guards 9/9; next-work `14m` select `I-analytic-finding-worker-schedule` (8.28% notice vs `I-action-store`, no owner stop). **Active: S4-02d** on `task/S4-02d-analytic-finding-worker-schedule` (main directory); fresh Claude implementer phase 1; ports 8924/8925/5424/5425, scratch DBs `assetops_s402d_*_test`. Non-UI. Install gate: never on an owner-visible host before the late-reading node lands. Queue after: `I-late-reading-series-and-money-limit` (M) also gates S5-01.
- **UPDATE 2026-10-14 (26):** S4-02c merged to main `68106bac` (reviews ACCEPT; non-UI). Slice review F1: gateway-sequenced late reading -> S3 INDETERMINATE, revised Finding SUPPORTED but truncated, consequence CURRENT PRICED too low (7.5625 vs 15.8125). Architect `D-2026-10-14-s402c-late-sequence-and-s5-money` (`.agent/architect-S4-02c-answers.md`): new nodes `I-late-reading-series-and-money-limit` (M) and `I-analytic-finding-worker-schedule` (S) gate `I-site-overview-read`/S5-01 and the real pilot; S4-02c acceptance unchanged. On `plan/S4-02c-architect` (gap-planning worktree, not yet merged): rulings + S4-02c registry closeout (`56324b09`, review `.agent/S4-02c-architect-closeout-review.md` ACCEPT w/ carries, L1/L2 applied `3e1c40b4`), S4-02d worker-schedule packet. next-work `14j` select `I-analytic-finding-worker-schedule` 2.198 vs `I-action-store` 2.016 (**8.28% ranking notice**, no owner stop). **NOW:** fresh plan review of S4-02d -> merge plan branch -> check-all on main -> activate S4-02d. Residual: S4-02b Finding money panel can show run-1 7.5625 as current until the late-reading node lands.
- **UPDATE 2026-10-14 (25):** Owner back; owner-absent rule confirmed (memory). main `f9d6d1a5`: plan/A-S5-overview merged (A-S5-overview, A-action-lifecycle, follow-on nodes, S4-02c packet: plan review RETURN -> Codex fix round `0b49c5bf` -> re-review ACCEPT `05fe1e53`). Guards 9/9; next-work `14h` 0.20% contest -> owner confirmed S4-02c (`.agent/owner-next-work-2026-10-14b.md`). **Active: S4-02c** on `task/S4-02c-evidence-consequence-work` (main directory); fresh Claude implementer; ports 8914/8915/5414/5415, scratch DBs `assetops_s402c_*_test`. Non-UI, no owner walkthrough unless new owner copy appears. Pending Architect batch: R1 scheduling process-jobs/match-findings (optional). Note: Planner = codex exec (memory).
- **UPDATE 2026-10-14 (24):** On `plan/A-S5-overview` (gap-planning worktree, HEAD `3fe91819`, not yet merged): A-S5-overview resolved + follow-on nodes (`7affc6a1`, review `.agent/A-S5-overview-review.md` ACCEPT w/ carries, L1/L3 fixed); A-action-lifecycle resolved under owner delegation in the 0.54% contest (`09a5a40d`, review `.agent/A-action-lifecycle-review.md` ACCEPT w/ carries, M1 fixed); Architect chose S4-02c (evidence-acceptance consequence work, 0.20% contest) as next; Codex Planner wrote `tasks/S4-02c-evidence-consequence-work.md` (non-UI, USER_REVIEW_REQUIRED false). Carries in backlog sections "A-S5-overview review carries" and "A-action-lifecycle review carries". **Standing check (review L2):** W1 exit_requires / real_pilot_requires are not checker-enforced; verify `I-stored-demo-provenance` manually at W1 exit and before any pilot. Owner to confirm the standing owner-absent rule (build+review, hold UI merges for owner walkthrough). **NOW:** fresh Claude plan review of S4-02c -> merge plan branch to main, check-all on main -> activate S4-02c (fresh Claude implementer).
- **UPDATE 2026-10-14 (23):** **Owner autonomy window 08:40-~10:40** (`.agent/owner-autonomy-2026-10-14.md`): owner-decision points go to the Codex Architect. main `2f5ac495`: S4-02b merged `a6c6a849`; Architect batch merged `26c1d760` (D-2026-10-14-s402-post-review-follow-ons); S4-02 registry closeout merged (review `.agent/S4-02-closeout-review.md` ACCEPT w/ carries; L1/L2/I2 applied `4fa004b2`; M1 three follow-ons lack nodes, Q2 sizing can flip the selection). next-work `14b` select A-S5-overview 9.50% (pending M1). **NOW:** Codex Architect on `plan/A-S5-overview` (gap-planning worktree): register follow-on nodes, rerun next-work (`14c`), decide next selection under delegation, record A-S5-overview if next, owner-absent checkpoint rule. Then Planner refinement of the selected packet. This handoff edit is uncommitted on main.
- **UPDATE 2026-10-14 (22):** Owner: "The walkthrough was completed successfuly" -> S4-02 checkpoint passed, recorded conditional, items 1-8 left as built (`.agent/owner-S4-02b-acceptance-2026-10-14.md`). Closeout commit on the task branch, merge to main. **Next:** S4-02 registry closeout (Sonnet, `closeout/S4-02-registry`) -> fresh review -> merge; Codex Architect batch on `plan/S4-02-architect-batch` (gap-planning worktree): S4-02a L2, S4-02b Q2/Q11/Q12; then rerun guards + next-work. Owner DBs `assetops_s402bwalk`/`_s402bempty` can be dropped.
- **UPDATE 2026-10-14 (21):** Sonnet fix round 1 `6abb3f5c`/`68823f30` (H1, L1-L4; evidence 90/90 on visible text); fresh re-review `.agent/S4-02b-fix-rereview.md` ACCEPT `29ae2abb` (info I1-I5). Walkthrough decision items 7-8 added (kept-for-record figures; price per litre under audit-only). **NOW: waiting on owner S4-02 checkpoint walkthrough** `.agent/S4-02b-owner-walkthrough.md` (DBs `assetops_s402bwalk`/`_s402bempty` prepared, ports 8872/8873/5372/5373). Then closeout: status done, merge, S4-02 registry closeout per `.agent/S4-02b-review.md` notes (assumptions:3#a waits on Architect Q12), Architect batch (S4-02a L2; S4-02b Q2, Q11, Q12), rerun guards + next-work.
- **UPDATE 2026-10-14 (20):** Slice review `.agent/S4-02b-review.md` ACCEPT w/ carries (`4eb53e6`) but **H1 must be fixed before owner checkpoint/merge**: Financials table shows stored amount under AUDIT_ONLY/STALE headlines (evidence claims vacuous). L1-L4 (L3 demo label fails open), L5 carry. Q11 acceptable after L3 (Architect/Planner batch: record authorship at ingestion); Q12 Architect batch (decides `assumptions:3#a`). Registry closeout notes in the review. **NOW:** Sonnet fix round 1 (H1, L1-L4, walkthrough steps 5-6) -> fresh Claude re-review -> owner S4-02 checkpoint.
- **UPDATE 2026-10-14 (19):** S4-02b phase 2b built `dbaba10`..`c0be402`; task `in_review`. Packet `.agent/S4-02b-review-packet.md`, walkthrough `.agent/S4-02b-owner-walkthrough.md` (owner DBs `assetops_s402bwalk`/`_s402bempty` prepared, pre-v4; ports 8872/8873/5372/5373; tool `tools/s402b_fuel_cost_walkthrough.py`), questions `.agent/S4-02b-questions-3.md` Q10-Q15. Backend 2049, frontend 1476, evidence 90/90, guards 9/9. Architect batch now: S4-02a L2, S4-02b Q2 (evidence enqueue), Q11 (demo label from spec Site+day vs stored authorship), Q12 (Site-level consequence list). **NOW:** fresh Claude slice review -> `.agent/S4-02b-review.md`. Then owner S4-02 checkpoint walkthrough.
- **UPDATE 2026-10-14 (18):** Phase 2a review `.agent/S4-02b-phase-2a-review.md` ACCEPT w/ carries (`3793e4d`): M1 closed S3 source gate still presents amount as current (fix first in 2b), M2 HISTORICAL untested, L1-L4 tests/wording. Branch must not merge without 2b. **Architect batch (pending, send together):** S4-02a L2 SUCCESSION-at-start refusal; S4-02b Q2 evidence acceptance enqueues no consequence work. Ops/Planner: Q6 scheduled recompute runner. **NOW:** fresh Claude implementer on phase 2b (backend carries, UI, layout evidence, walkthrough tool + `.agent/S4-02b-owner-walkthrough.md`, review packet, status in_review). Owner ports 8872/8873/5372/5373. Then slice review -> owner S4-02 checkpoint.
- **UPDATE 2026-10-14 (17):** S4-02b phase 2a built `5d400d6`..`7c21931` (handoff `.agent/S4-02b-phase-2a-handoff.md`, questions `.agent/S4-02b-questions-2.md` Q1-Q9; full backend 2037 passed; guards 9/9). Phase-1 carries landed; recompute worker/CLI, consequence read + route, bridge replaced; owner demo case P01-power (15.82 USD at v1 -> 16.20 after v4) via `tools/s402b_power_cases.py`. Deviation: S4-02a UI words new bridge states wrongly until 2b (do not show it over a 2a DB). **NOW:** fresh Claude review -> `.agent/S4-02b-phase-2a-review.md`. Then 2b (UI + layout evidence + walkthrough).
- **UPDATE 2026-10-14 (16):** Phase 1 review `.agent/S4-02b-phase-1-review.md` ACCEPT w/ carries (`c4d8383`): M1 basis digest uses raw assignment IDs (fix first in 2a), M2 Q9 wording wrong (F01-gateway has power but 1/3 coverage), L1 0011 work CHECK vs zero-width episode, L2 reviewer field in pinned parameter, L3-L7. Owner ruling `.agent/owner-S4-02b-money-demo-2026-10-14.md`: add a labelled authored demo case with back-to-back 5-min power means (new versioned spec) + backlog item "analysis input data for simulated and real Sites". **NOW:** fresh Claude implementer on phase 2a (read + recompute + fixtures + demo case, carries first).
- **UPDATE 2026-10-14 (15):** S4-02b phase 1 built (`7cbdef7`, `5b4be01`, `8eb4ee9`, `bc88a0e`; handoff `.agent/S4-02b-phase-1-handoff.md`, questions Q1-Q10 `.agent/S4-02b-questions-1.md`; full backend 2014 passed, guards 9/9; migration 0011 head; price fixture v4 CORRECTION 1.28 over Oct 2026). **Key issue Q9:** ordinary S4 Findings carry no generator power means, so every Finding is QUANTITY_UNAVAILABLE; a positive amount needs a power-mean producer or the walkthrough says none qualified (owner checkpoint impact). **NOW:** fresh Claude review of phase 1 running -> `.agent/S4-02b-phase-1-review.md`. Then phase 2a (fresh implementer). Scratch DB `assetops_s402b_test` kept.
- **UPDATE 2026-10-14 (14):** Owner chose **S4-02b** (`.agent/owner-next-work-2026-10-14.md`). **Active: S4-02b** on `task/S4-02b-fuel-consequence` (main directory, from main `14ad5ef`). Fresh Claude implementer building phase 1 (`fuel-cost-1` and consequence store), handoff expected `.agent/S4-02b-phase-1-handoff.md`, questions `.agent/S4-02b-questions-1.md`. Implementer ports 8902/8903/5402/5403, scratch DBs `assetops_s402b_*`. Next: fresh review of phase 1 -> phase 2a -> review -> 2b -> slice review -> S4-02 owner checkpoint walkthrough (suggest ports 8872/8873/5372/5373) -> merge -> S4-02 closeout -> rerun guards + next-work. Architect batch still holds S4-02a L2.
- **UPDATE 2026-10-14 (13):** main `14ad5ef`: S4-02a merged `2592c82`; registry closeout merged (Sonnet `6392b86`, fresh review `.agent/S4-02a-closeout-review.md` ACCEPT w/ carries `6b2a284`, L1/I1-I3 applied by coordinator `2284053`). Guards 9/9 on main; next-work `.agent/next-work-2026-10-14a.json` stop_owner **I-financial-store (S4-02b) 2.229 vs A-S5-overview 2.148 (3.63%)**, tie-break recommends A-S5-overview. **NOW: waiting on owner choice.** If S4-02b: create `task/S4-02b-fuel-consequence` from main, Status active, fresh Claude implementer (carry L5, C3 v4 step, owner version-1 carry). If A-S5-overview: Codex Architect decision on a plan branch (cold, tight brief), batch the S4-02a L2 question with it. This handoff edit is uncommitted on main; commit it on the next branch.
- **UPDATE 2026-10-14 (12):** PC restarted again after `ac6ae92`; no work lost (no file written after the handoff; worktrees clean). Owner walked S4-02a and **accepted conditionally** (`.agent/owner-S4-02a-acceptance-2026-10-14.md`): 390 px tab wrap ok for now; version 1 history vs schedule a minor carry. Closeout commit on the task branch (status done, review outcome, README row, ACTIVE_CONTEXT, backlog "S4-02a carries (2026-10-14)"), then merge to main. **Next:** registry closeout `closeout/S4-02a-registry` (I-S4-02a resolved; store/read/UI node evidence; `G-assumptions-human-edit` evidence; `G-foundation-financial-assumptions` stays open with corrected review trigger) -> fresh Claude review -> merge -> rerun guards + next-work (owner contest if ≤5%). Walkthrough DBs `assetops_s402awalk`/`_s402aempty` can be dropped (keep the tool for S4-02b).
- **UPDATE 2026-10-14 (11):** S4-02a built (phase 1 `28668d9`..`4e694bb`, review `.agent/S4-02a-phase-1-review.md` ACCEPT w/ carries; phase 2 `408e9e6`..`f9ce2e5`), slice review `.agent/S4-02a-review.md` ACCEPT w/ carries -> Sonnet fix round `778875d`/`fc8e03f` (M1, L1, L3, L4, L6) -> re-review `.agent/S4-02a-fix-rereview.md` ACCEPT `3781195`. Walkthrough updated with review owner items `4ffae29`. **NOW: waiting on owner walkthrough** `.agent/S4-02a-owner-walkthrough.md` (DBs `assetops_s402awalk`/`_s402aempty` from `assetops_s4cases`, ports 8870/8871/5370/5371). Owner items: disabled-edit wording, "Not calculated", 390 px tab wrap (L2), version-1 history vs schedule. Carries for S4-02b: L5 (cutoff replacement times, "Show later versions" replaces), C3 v4 Finding-window correction step; Architect batch: L2 phase-1 SUCCESSION-at-start refusal. Then closeout: status done, registry closeout (I-S4-02a, store/read/UI nodes, `G-assumptions-human-edit` evidence; keep `G-foundation-financial-assumptions` open unless the owner accepts the link), merge, rerun guards + next-work (owner contest if ≤5%). Kept scratch DBs `assetops_s402a_evwalk`/`_evempty`, stray `assetops_s402a_test`.
- **UPDATE 2026-10-13 (10):** S4-02 plan merged to main `58bb8ef` (guards 9/9; next-work `13n` identical to reviewed `13m`). Owner chose **S4-02a** (`.agent/owner-next-work-2026-10-13e.md`, 2.20% contest). **Active: S4-02a** on `task/S4-02a-site-assumptions` (main directory, activated `ec74ac6`); fresh Claude implementer building phase 1 (store/SYSTEM publication), handoff expected `.agent/S4-02a-phase-1-handoff.md`, questions (if any) `.agent/S4-02a-questions-1.md`. Implementer ports 8900/8901/5400/5401, scratch DBs `assetops_s402a_*`. Next: fresh Claude review of phase 1 -> phase 2 (fresh implementer) -> review -> owner walkthrough (suggest ports 8870/8871/5370/5371) -> merge -> rerun guards + next-work.
- **UPDATE 2026-10-13 (9):** A-S4-financial merged `2c87037`. Owner chose S4-02 money (`.agent/owner-next-work-2026-10-13d.md`, contest 3.63%). `plan/S4-02-refine`: Codex Planner (cold, ~118k tokens; cold tight briefs are far cheaper than resuming) split S4-02 into `tasks/S4-02a-site-assumptions.md` (USER_REVIEW_REQUIRED true) and `tasks/S4-02b-fuel-consequence.md` (S4-02 owner checkpoint); `S4-02-bounded-financials.md` is the closeout pointer. Plan review `.agent/S4-02-plan-review.md` ACCEPT with carries -> Sonnet fix round + Codex Architect `.agent/architect-S4-02-answers.md` (Q1 1.10 conditional multiplier; C4 fail-closed containment; DECISIONS addendum) -> re-review `.agent/S4-02-plan-fix-rereview.md` ACCEPT; R1-R5 applied by coordinator `949e3f3`. The split changed next-work: stop_owner **I-financial-assumption-store (S4-02a) 2.182 vs A-S5-overview 2.134 (2.20%)** -> re-ask owner after merge (earlier choice does not carry over automatically). If S4-02a: create `task/S4-02a-site-assumptions` from main, set Status active, dispatch a fresh Claude implementer (phase 1 store/publication), owner walkthrough after review.
- **UPDATE 2026-10-13 (8):** A-S4-financial resolved on `plan/A-S4-financial`: Codex Architect (resumed session `01a11a84…`, gpt-6-sol, ~5M tokens: the resumed session is large; consider a cold, tight brief next time) wrote `D-2026-10-13-s4-bounded-financial-basis` (`7faa206`; S4-02 splits into two M slices, S4-02a assumptions/history + unpriced bridge, then S4-02b fuel-cost-1 consequence/repricing/UI; `G-readiness-commissioning` missing_kind -> contract). Fresh Claude review `.agent/A-S4-financial-review.md` ACCEPT `efceff4` (carries M1, M2, L1-L7 in backlog "A-S4-financial carries" and the S4-02 outline). Merged to main next. Then rerun guards + next-work on main: expected stop_owner **I-financial-store 2.229 vs A-S5-overview 2.148 (3.63%)**; put it to the owner (tie-break recommends A-S5-overview). If I-financial-store wins: the Codex Planner refines/splits S4-02 on a plan branch first (no implementer before refinement).
- **UPDATE 2026-10-13 (7):** G-02 merged to main `8f711d8` (owner accepted conditionally, `.agent/owner-G-02-acceptance-2026-10-13.md`; 390 px SLD caption "ok for now"; closeout `5e958ca`; decision D-2026-10-13-g02-visible-placement-and-state-boundary). Registry closeout `closeout/G-02-registry` resolves I-G-02 (`00e7504`; fresh review `.agent/G-02-closeout-review.md` ACCEPT `0863251`), merged next. Next-work `.agent/next-work-2026-10-13h.json`: stop_owner, same contest as 13e; **owner re-chose A-S4-financial** (`.agent/owner-next-work-2026-10-13c.md`). Owner instruction (verbatim) "pay attetion to the priortization workflow": every merge or checkpoint changes inputs, so rerun guards + report and stop for the owner on a ≤5% contest even if asked before; never assume the next slice after a user-review checkpoint. **G-03/G-04/G-05 deferred** (D-2026-10-13-g-gap-packet-activation): their prerequisites are now closed, but ready core candidates are waiting (A-S4-financial owner-chosen; 6 eligible); G-05's owning UI is unbuilt. Re-check at each free slot; otherwise W1-exit backfill review. **Next:** A-S4-financial, an Architect decision on a planning branch (no implementer), then S4-02. Refresh `.ai/ACTIVE_CONTEXT.md` (still says G-02 in_review; review carry K2) when it is activated.
- **UPDATE 2026-10-13 (6):** PC restarted unexpectedly between 18:28 (last commit) and ~18:44. Damage: the branch ref `task/G-02-v01a-gap-pilot` was zeroed (restored from the reflog to `5ba5d38`) and the `assetopsv1-postgres-1` container was killed (restarted; Postgres WAL recovery clean, all DBs present). Verified afterwards: `git fsck --full` clean, all refs resolve, both worktrees clean, every tracked file rehashed equal to HEAD (the 13 ` M` files under autocrlf are byte-identical, pre-existing), no NUL-filled files; check-all 9/9, tsc 0, vitest 61 files/1446 passed, build ok. No project file was written after 18:28, so no work was lost. G-02 is past implementation: review `G-02-review.md` -> Architect answers -> fix round 1 -> fresh re-review `G-02-fix-rereview.md` ACCEPT -> R1 walkthrough fix `5ba5d38`. **NOW: waiting on owner walkthrough** (`.agent/G-02-owner-walkthrough.md`, ports 8868/8869/5368/5369; owner item: 390 px SLD caption, step 5). Then merge, then A-S4-financial. The "implementer running" note in (5) is stale.
- **UPDATE 2026-10-13 (latest, 5):** main `5625447`: S4-03 registry closeout merged (review `.agent/S4-03-closeout-review.md` ACCEPT; also resolved I-G-01). Guards pass; next-work `.agent/next-work-2026-10-13f.json` stop_owner A-S4-financial vs A-S5-overview 3.21% — owner already chose A-S4-financial after G-02 (`.agent/owner-next-work-2026-10-13b.md`). **Active: G-02** on `task/G-02-v01a-gap-pilot` (main directory, `42bd74d`), implementer running; owner walkthrough ports 8868/8869/5368/5369. Next: A-S4-financial (Architect decision on a planning branch), then S4-02.
- **UPDATE 2026-10-13 (4):** main `a32d4bb`: S4-03 merged (owner accepted conditionally, `.agent/owner-S4-03-acceptance-2026-10-13.md`; six reviews read; decision D-2026-10-13-s403-legacy-evidence-and-lineage-words). Next-work REFUSES (queue_mismatch: S4-03 registry open) until registry closeout lands: Sonnet running on `closeout/S4-03-registry` (main directory) -> fresh review -> merge -> rerun next-work. Then G-02 (due after G-01, owner order S4-03 then G-02). S4 milestone: S4-02 (money) still open; batched S3 and S4 Codex reviews still pending. Rule: only one full backend pytest at a time (connection exhaustion).
- **UPDATE 2026-10-13 (3):** main `662dce3` (S4-03 plan merged; plan review `.agent/S4-03-plan-review.md` ACCEPT, carries applied `563db20`). **Active: S4-03** on `task/S4-03-finding-evidence-history` (main directory, `2bb4f87`), implementer running (ports 8898/8899/5398/5399; owner walkthrough 8866/8867/5366/5367). `sequenced_after I-S4-02` left unchanged (records history only). Next after S4-03: G-02. Gap-planning worktree is on `plan/S4-03-refine` (merged).
- **UPDATE 2026-10-13 (2):** main `d9eb9ca`: G-01 merged (owner accepted conditionally, `.agent/owner-G-01-acceptance-2026-10-13.md`; reviews `G-01-review.md` RETURN -> `G-01-fix-rereview.md` ACCEPT; decision D-2026-10-13-g01-placement-and-orphan-scan-boundary). All 9 guards pass in the main directory (the gap-planning worktree lacks frontend/node_modules, so the scan guards fail there - run check-all in the main directory). Main directory now on `main`. Next: S4-03 (owner choice) - Codex Planner refining on `plan/S4-03-refine` in the gap-planning worktree; then G-02. NOTE: this handoff file is tracked; a G-01 fix-round agent committed it in `68dfe64` (not pushed).
- **UPDATE 2026-10-13:** main `d57c756`: V-01b merged `34b2a9f` (owner accepted conditionally), registry closeout merged `f024ddc` (review ACCEPT `b680990`), README S4-01/S4-02 rows corrected (41dba44 had written S4-01's done row on S4-02). Guards pass. **Active: G-01** on `task/G-01-mock-gap-catalogue-and-guard` (main directory, `db98e54`), implementer running; owner walkthrough ports 8864/8865/5364/5365. **Next after G-01:** owner chose I-finding-evidence-read / S4-03 over A-S4-financial (contest 2.215 vs 2.187, 1.26%; `.agent/owner-next-work-2026-10-13.md`). G-02 due at the free slot after G-01 merges — order G-02 vs S4-03 per D-2026-10-13-g-gap-packet-activation (G-02 'next free slot after G-01'), check with owner if ambiguous.
- main at `660de99`: S3-01, I-finding-store, V-01a (owner accepted conditionally 2026-10-12, `.agent/owner-V-01a-acceptance-2026-10-12.md`), mock-gap planning (G-01..G-05 packets) and the G activation rule (`D-2026-10-13-g-gap-packet-activation`, merged `adeeca4`). Nothing pushed.
- Active: **V-01b** on `task/V-01b-evidence-lab-visual` (main directory). Built, `in_review`; main merged at `8ab5589`. Reviews: V-01b-review (RETURN), fix-rereview (RETURN, owner chose fix round), fix2 (ACCEPT), Architect answers `.agent/architect-V-01b-answers.md` (Q1 fix required; draft decision D-2026-10-13-v01b-visual-and-lab-read-boundaries to commit at merge), fix3 (RETURN tool-only, owner option 1), fix4 (ACCEPT, `b8bc4ce`; evidence tool 101/101 + 2 not run reproduced). HEAD `bddf514`. NOW: waiting on owner walkthrough (`.agent/V-01b-owner-walkthrough.md`, owner ports 8862/8863/5362/5363). Architect batch pending: `.agent/V-01b-questions-1.md` Q1-Q8. Owner decision flagged: shell-overflow guard 2b change to S1-03 scoping rule.
- After V-01b merges: G-01 at next free slot (manual order; checker does not enforce), G-02 after G-01, G-03 after V-01b.
- Gap-planning worktree `AssetOpsV1-gap-planning` used for merges to main.

## Earlier state
- main at `bc78298`: S1, S2, pre-S3 startup, **S3-01 merged** (owner checkpoint passed 2026-10-12, `.agent/owner-S3-01-acceptance-2026-10-12.md`). Nothing pushed.
- Loop running per `.ai/COORDINATOR_LOOP.md`. Review routing (owner 2026-10-11): fresh Claude per slice/phase, Sonnet fix rounds, one batched Codex review per milestone (S3 Codex review due at end of S3: covers S3-01 and S3-02), batched Architect questions.
- (done, merged `79a0664`) branch `closeout/S3-01-registry` — Sonnet implementer recording S3-01's delivered W1 panel portions (next-work refused `[open_path] dispatch:1`). Then fresh review, merge, rerun next-work on main, select next task.
- Pending Architect batch: `.agent/S3-01-questions-4.md` (Q14-16, reviewer judged safe) and `-5.md` (Q17-Q22) — send with the next natural batch.
- Owner servers: 8000, 5173/5183/5199/5213/5291; S2 demo processes on 8610/8643 left alone. Walkthrough DBs `assetops_s2demo`, `assetops_s3cases`, `assetops_s3walk` kept.
- Routing: Codex Architect session `01a11a84-c2ea-7443-884d-0d5544355e9f`; Planner `01a11c16-72df-7bb0-a825-60c7d83c1d82`; Codex cannot write .git.

### Ranking notices
- 2026-10-13 (`.agent/next-work-2026-10-13h.json`, G-02 registry closeout, after the G-02 merge): A-S4-financial 2.215 vs A-S5-overview 2.144, gap 3.21% (≤5%), candidates identical to 13e. Re-asked; owner chose A-S4-financial again ("Money decision (A-S4-financial)", `.agent/owner-next-work-2026-10-13c.md`). Tie-break had recommended A-S5-overview.
- 2026-10-13 (`.agent/next-work-2026-10-13e.json`, S4-03 closeout branch): A-S4-financial 2.215 vs A-S5-overview 2.144, gap 3.21% (≤5%) → owner chose A-S4-financial ("Money decision", `.agent/owner-next-work-2026-10-13b.md`), after G-02. Tie-break had recommended A-S5-overview.
- 2026-10-13 (main + V-01b closeout, `.agent/next-work-2026-10-13b.json`): A-S4-financial 2.215 vs I-finding-evidence-read 2.187, gap 1.26% (≤5%, story vs story; V-01 rule not applicable) → owner chose I-finding-evidence-read (S4-03), after G-01.
- 2026-10-12 (main `e434cd7`): V-01a 2.655 vs V-01b 2.470, gap 6.97% (5-10% band) → V-01a selected by published tie-break, notice only. Story-path A-S4-financial 2.215 not in contest. Owner clarified the standing rule applies only to close calls (verbatim "story first in close calls").
- 2026-10-12: contested ranking on main `79a0664` (`.agent/next-work-2026-10-12.json`): A-finding-episode 2.761 vs V-01a 2.655, gap 3.84% (≤5% → owner). Tool tie-break recommended V-01a; coordinator recommended A. **Owner chose A** (verbatim: "lets go with option A"). Started on branch `plan/A-finding-episode`.
- 2026-10-12: decision merged `87c49ce`. Next contest: I-finding-store 2.785 vs V-01a 2.655 (4.67%). **Owner chose I-finding-store** and set a standing rule (verbatim "I-finding-store, and story path first until S4 is done"; `.agent/owner-contest-rule-2026-10-12.md`): until S4 is done, story-path beats V-01a/V-01b in ≤5% contests without stopping; log each such notice here.

---
Older history follows.

# Coordinator handoff (2026-10-08, S1 merged; S2-01a planning next)

A fresh coordinator starts from this file; do not re-derive what it states.

## Current state (supersedes everything below)

- **S1 is merged into main** at `26d013b` (S1-01 persisted Foundation, S1-02 bindings/Readiness/SLD, S1-03 Foundation organization). Nothing pushed.
- Reviews: Codex Reviewer joint review (`.agent/S1-codex-review.md`): S1-01 accept with carries, S1-02 changes required, fixed; fresh Claude re-reviews closed everything (`.agent/S1-02-fix-rereview.md`, `.agent/S1-03-review.md`, `.agent/S1-fix-rereview.md`, `.agent/S1-fix-rereview-2.md`, final verdict accept with carries).
- Owner UI check accepted (`.agent/owner-S1-acceptance-2026-10-08.md`): "looks ok for now"; owner plans a later UI/UX modernization round after functional slices (relates to V-01).
- Architect (Codex, session `01a11a84-c2ea-7443-884d-0d5544355e9f`) decisions: `D-2026-10-08-s1-bindings-roles-and-snapshot`, `D-2026-10-08-s1-foundation-organization` (in `.ai/DECISIONS.md`); answer files `.agent/architect-S1-*`.
- Owner routing rules (memory): re-reviews by fresh Claude reviewer; small fix rounds by Sonnet implementer; decisions to the Codex Architect; Codex reviews new slices (batched where the owner says).
- Carries (all in `.agent/S1-01-review-packet.md`, `.agent/S1-02-review-packet.md`, `.agent/S1-03-review-packet.md`): notably registration identity mutability (m4/N2), snapshot download availability depends on current registrations (S1-02 n5, carry before S2), 0004 downgrade drops bytes (n1), Lab phone layout and Lab layout claims unmeasured, `/api/sites` latency (m7), no DB connection timeout (N7), R1 carry-side tests (N1), nav-guard shapes (N2).
- Dev DB `assetops`: KOBO-001 imported and converted, with several reserve/binding versions from testing; KOBO-GAP-001 test Site.

## Owner rule 2026-10-09 (verbatim): "codex review happens for the whole S2-0* for usage efficency. also bundle questions to codex, be efficent with its use"
- Remaining S2 slices (S2-01c, S2-02): a fresh Claude reviewer per slice; one Codex review over S2-01c + S2-02 together at the end of S2. Architect questions are batched (implementers proceed on fail-closed defaults); call Codex immediately only for a genuine blocker.
- S2-01a+S2-01b merged to main at `7c10283` (owner approved). S2-01c in progress on `task/S2-01c-gateway-diagnostics-faults` (phases 1, 2 built; 3a dispatched; 3b next).

## S2-02 status (2026-10-09, latest — supersedes S2 notes below)
- S2-02 built (phases 1, 2, 3a, 3a2, 3b, corrections, 3c), fresh Claude review -> Architect batch 4 -> fix round -> fresh Claude re-review accept (`.agent/S2-02-fix-rereview.md`) -> walkthrough doc fix (R1/R2). Branch `task/S2-02-ingestion-site-evidence`. S2-01c merged at `b4006d1`.
- WAITING ON OWNER: S2 Evidence walkthrough per `.agent/S2-02-owner-walkthrough.md` (USER_REVIEW_REQUIRED). Owner servers on old code show KOBO-001 awaiting migration until restarted on this branch.
- Running: one Codex review of S2-01c+S2-02 (`.agent/S2-codex-review-brief.md` -> `.agent/S2-codex-review.md`).
- Next Architect batch: `.agent/S2-02-questions-7.md` (Q37-Q40) + re-review R3 + any Codex review findings needing decisions.
- After S2 closeout: V-01 adoption decision (owner), delivery-strategy startup prerequisites (drafts in `.agent/delivery-drafts/`, Architect batch-4 Part B answers), pre-S3 shared-contract decisions.

## Delivery strategy (owner-confirmed 2026-10-09) and ranking notices
- `D-2026-10-09-owner-delivery-strategy` recorded in `.ai/DECISIONS.md` (`f5d35c0`); working plan and phased prerequisites in `.agent/D-2026-10-09-owner-delivery-strategy-proposal.md`.
- Planning-only drafts allowed during S2-02 (no tracked registry/workflow/checker changes until S2-02 closeout). Loop activates only after S2-02 closeout + startup prerequisites + owner W1 input.
- **Ranking notices (5%<gap<=10% "notify and continue") are recorded in this file under a "Ranking notices" heading.**

### Ranking notices
(none yet)

## S2-01c (2026-10-09, latest)
- Built (phases 1, 2, 3a, 3b), fresh Claude first review -> Architect batch -> fix round 1 -> re-review (R1 block) -> batched Architect (`a2d409d`) -> fix round 2 -> fresh Claude re-review ACCEPT (`.agent/S2-01c-fix2-rereview.md`). Awaiting owner merge decision.
- S2-02 refined (planning commit before `a2d409d`; packet amended by Architect). Open questions to batch for the next Architect call: `.agent/S2-01c-questions-6.md` plus any S2-02 implementer questions.
- Codex reviews S2-01c + S2-02 together at end of S2.

## S2 status (2026-10-09) — supersedes the S2 progress notes below

- S2-01a: built, Codex first review ACCEPT WITH CARRIES. S2-01b: built (phases 1, 2, 3a, 3b), Codex first review RETURN (F1) -> fix round 1 -> fresh Claude re-review accept -> Architect fix-round choices -> fix round 2 (Sonnet) -> fresh Claude re-review accept (`.agent/S2-01b-fix-rereview-2.md`). Packet `.agent/S2-01b-review-packet.md`.
- Neither merged to main. S2-01b branch contains S2-01a. Awaiting owner's merge decision.
- Carries in `.ai/MILESTONE_REVIEW_BACKLOG.md`: S2-01a F1 (closed in S2-01b), F3; S2-01b F2, F3, R1, layout note. Q4/Q5 demo config and asset-code identity are S2-02 prerequisites.
- Codex sessions: Architect `01a11a84-c2ea-7443-884d-0d5544355e9f`; Planner `01a11c16-72df-7bb0-a825-60c7d83c1d82`; S2-01b reviewer `01a11e95-bb1c-7992-9491-9859b4d1abd1`. Codex sandbox cannot write `.git`; the coordinator commits its edits.
- Next: owner merge decision; then Planner refines S2-01c (after S2-01b review, now done).

## S2 progress (2026-10-08, later)

- Branch `task/S2-01a-registered-lab-basis`: Codex Planner refined S2 (`b322843`; session `01a11c16-72df-7bb0-a825-60c7d83c1d82`; questions `.agent/planner-S2-questions-2026-10-08.md`). Codex Architect answered (`8544549`; `D-2026-10-08-s2-lab-snapshot-selection-and-run-boundary`; `.agent/architect-S2-answers-2026-10-08.md`; no owner input needed).
- Codex sandbox cannot write `.git`; the coordinator commits Codex edits.
- Phase 1 built (`ce65b8d`..`a736be7`, handoff `.agent/S2-01a-phase-1-handoff.md`); implementer questions answered by Architect (`684aa91`, `.agent/architect-S2-01a-answers-2.md`, no owner input). Phase 2 dispatched to a fresh implementer; packet expected at `.agent/S2-01a-review-packet.md`; then first review by Codex.
- S2-01a built (phase 2 `8d0e1d3`..`145ca18`; packet `.agent/S2-01a-review-packet.md`; task in_review). Two Codex runs were killed by Claude Code for low system memory before producing output, not restarted pending owner: (1) Architect on Q4/Q5 (`.agent/architect-S2-01a-request-3.md`, resume Architect session `01a11a84-c2ea-7443-884d-0d5544355e9f`); (2) Codex first review (`.agent/S2-01a-review-brief.md`, cold session `01a11c82-0853-7653-842d-b405b88adf76` started, can be resumed). Full layout-evidence run incomplete (browser stalled after 132 PASS).
- (superseded) S2-01a phase 1 (selection and freeze) dispatched to a fresh Claude implementer; handoff expected at `.agent/S2-01a-phase-1-handoff.md`. Phase 2 (execution, guards, frontend) goes to a fresh implementer from that handoff; then first review by Codex.

## Next actions (older, done through planning)

1. S2-01a is an outline: Planner (Codex) refines it against the S1 result and the carries that S2 consumes (n5 snapshot availability, gateway auth) before any implementation.
2. Then Implementer on S2-01a; Codex review per owner; re-reviews by fresh Claude.

---
Older history follows.

# Coordinator handoff (2026-10-04, T028 merged; owner-led roadmap review next)

A fresh coordinator starts from this file; do not re-derive what it states.

## Current state (supersedes everything below)

- **T028 is complete and merged**: `main` at `bd37200` (nothing pushed). Owner
  accepted on a quick UI check (`.agent/owner-T028-acceptance-2026-10-04.md`);
  the full packet walk was not recorded; domain-expert feedback checkpoint
  outstanding. Final: backend 1493, host 619, simulator 244, frontend 1134,
  build, both checks; layout 615/4 known (`.agent/T028-layout-evidence-final.txt`).
- Role bindings reverted to Codex (Architect, Planner, Reviewer). Owner rules
  2026-10-04: decision requests go to the active Architect (ROLE_CONFIG);
  product screens plain-language, no simulator wording, deep analysis in its
  own tab (`D-2026-10-04-plain-language-analysis-views`). Re-reviews after a
  slice's first review: fresh Claude reviewer.
- New decisions: `D-2026-10-04-analytic-readiness-scope-and-gap-impact`,
  `-practitioner-first-finding-presentation`, `-plain-language-analysis-views`.
- Backlog additions: T028A (configurable gap impact, after T029 point-2
  feedback); "For T029: practitioner-first presentation direction"; legacy
  product copy inventory after T029; carries from T028 Codex review (C1),
  re-review (F2), presentation review (F2-F4, F7).
- Codex retrospective reviews still queued, not run: T025e, T025f, T025g,
  T026, demo-led plan, T027 phases 1 and 2.

## Next actions

1. **Owner-led major review with the Architect** (Codex) to chart the roadmap
   and alter tasks. The owner leads it; wait for the owner's framing. Likely
   inputs: `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`, `.ai/FEATURE_MAP.md`,
   `tasks/README.md` (queue T029 -> T029B -> T029A -> T034 -> ...), the T028
   Architect records, backlog. Save owner text verbatim.
2. Then the queue as revised; the retrospective Codex reviews when the owner
   wants quota spent on them.

---
Older history follows.

# Coordinator handoff (2026-10-03 ~15:00, T028 phase 1 built; owner UI check next)

A fresh coordinator starts from this file; do not re-derive what it states.

## Current state (supersedes everything below)

- T028 phase 1 is built on `task/T028-dispatch-finding-and-evidence` (cut from
  `cfe142a`; HEAD `7e0450d`; not merged). First implementer stalled (watchdog)
  after 7 commits; a fresh one finished. Handoff `.agent/T028-phase-1-handoff.md`
  (per-AC table, owner UI-check steps); decision table
  `backend/tests/dispatch_decision_table.md`. Targeted tests, tsc and both
  checks pass; full suites belong to phase 3.
- No review of phase 1 yet. Owner questions open: (1) stop-60 policy record
  under profile 5 (needs scenario/publication change, not made; nothing
  blocked); (2) Necessary intervals produce an assessment but no Finding.
- Phase 2 risks: same recipe rerun over same window gives no revision
  (ingestion keeps first record per key); analytic runtime bounds differ from
  the Overview's whole-interval "Generator running time" (carry still open).

## Next actions

1. Owner ruled 2026-10-03 (`.agent/owner-T028-phase-1-questions-2026-10-03.md`):
   UI check only after all T028 phases; stop-60 as is; Necessary = no Finding.
2. Phase 2 built: HEAD `20fbc58`, handoff `.agent/T028-phase-2-handoff.md`,
   layout `.agent/T028-phase-2-layout-evidence.txt` (546/7: 4 known, 3 the
   updated T027 card claim, fixed, not re-run). Adds `GET /api/findings`
   (test_health changed to allow it). Phase 3 dispatched ~21:40 to a fresh
   Implementer (AC20, full suites, layout, packet `.agent/T028-review-packet.md`).
   Codex reset passed 21:23: ROLE_CONFIG revert and in-flight roles put to owner.
   Phase 3a (AC20, AC18 Evidence rows) built: HEAD `618b598`, handoff
   `.agent/T028-phase-3a-handoff.md`. Phase 3b closeout (suites, build, layout,
   packet, records) dispatched to a fresh Sonnet implementer.
   Phase 3b closeout agent stalled after writing everything; coordinator
   committed it as `9524382` (task in_review, packet `.agent/T028-review-packet.md`,
   suites backend 1465 / host 616 / simulator 244 / frontend 1097, build ok,
   checks pass, layout 560/5: 4 known + T025b "profile 4 discloses the status"
   claim, seen once in T027 phase 2, not re-run). NEXT: review (owner to say
   Codex or fresh Claude), then owner UI walk (packet last section).
   2026-10-04: owner reply `.agent/owner-T028-closeout-2026-10-04.md`. New
   standing rule (ROLE_CONFIG "Decision Requests Go To The Active Architect",
   main `38177b3`, merged into T028 as `1f46d75`): decisions go to the
   Architect, not the owner. ROLE_CONFIG reverted to Codex. Codex Architect
   running on brief `.agent/T028-architect-brief-readiness.md` -> record
   `.agent/T028-architect-readiness-decisions.md` (log
   `.agent/T028-architect-codex-run.log`, capture session id). Then: any
   required change (fresh implementer), Codex first review of T028 (discovery
   per ROLE_CONFIG), owner UI walk. Retrospective Codex reviews (T025e, T025f,
   T025g, T026, demo-led plan, T027 p1/p2) queued after T028's review to
   conserve quota.
   Codex Architect done (session 01a104e1-58c3-7062-ba32-1a1e141fc8c2):
   `.agent/T028-architect-readiness-decisions.md`; landed as
   D-2026-10-04-analytic-readiness-scope-and-gap-impact + T028A backlog carry
   (`57810e8`). No owner input wanted. Correction round (record section 3)
   dispatched to a fresh Sonnet implementer; then Codex first review.
   Correction round done `3e75a54` (readiness-2; backend 1468, host 616
   (coordinator ran), frontend 1098, tsc, checks). Codex first review running:
   brief `.agent/T028-codex-review-brief.md` -> `.agent/T028-codex-review.md`
   (log `.agent/T028-codex-review-run.log`; capture session id for resume).
   Then: sort findings block/carry; fix round (fresh Sonnet) if any block;
   owner UI walk (packet last section); merge.
   Codex review RETURN (session 01a104f2-2007-7a20-b7ce-34166ee13c4f):
   `.agent/T028-codex-review.md`, R1-R5 block (all reproduced), C1 carried to
   backlog (`af668a7`). Fix round 1 dispatched to a fresh session-model
   implementer (R2 has a treatment choice). Re-review: R2 choice makes it
   discovery -> resume the Codex review session
   (`codex exec resume -c sandbox_mode="workspace-write" --skip-git-repo-check <id> "..." < /dev/null`).
   CORRECTION: re-reviews go to a fresh Claude reviewer (owner rule 2026-09-29,
   memory codex-rereview-conservation), not Codex. Fix round 1 done `7368637`
   (dispatch-2, readiness-3; backend 1482, frontend 1099, host 616). Fresh Claude
   re-review running -> `.agent/T028-fix-round-1-claude-rereview.md`. If it
   finds something unexpected, put it to the Architect/owner, do not auto-route
   to Codex. Then owner UI walk.
   Claude re-review: ACCEPT, F1 (false override wording, P3) fixed in fix
   round 2 (Sonnet, running), F2 carried to backlog, F3 packet wording in
   round 2 (`6efafbe`). Reviewer flagged R2/R4 choices + F1 as a Codex-escalation
   signal but recommended against; coordinator did not escalate (owner quota
   rule); owner told and may overrule. After round 2: coordinator verifies,
   then owner UI walk (packet last section), then merge.
   Fix round 2 done `30122ed` (F1 wording + 3 tests, F3 packet; backend 1485,
   host T028 14 (coordinator ran), checks pass; backend-only code change).
   NEXT: owner UI walk, packet `.agent/T028-review-packet.md` last section;
   record owner text verbatim; then mark T028 done, move task to completed,
   merge to main; then retrospective Codex reviews (T025e, T025f, T025g, T026,
   demo-led plan, T027 p1/p2), then T029.
   Owner audience question (`.agent/owner-T028-audience-question-2026-10-04.md`)
   -> Codex Architect (session 01a10712-8960-7e23-b764-1d6781ab5221)
   `.agent/T028-architect-audience.md`: product-facing but reads like an
   analyst report; narrow presentation correction before merge; landed as
   D-2026-10-04-practitioner-first-finding-presentation + T029 carry (`66d31ad`).
   Presentation correction dispatched to a fresh session-model implementer
   (full suites, build, layout). Then fresh Claude review (wording must not
   strengthen claims; disclosure usable), then owner UI walk, merge.
   Owner presentation direction (`.agent/owner-T028-presentation-direction-2026-10-04.md`)
   -> paused correction (`12fd695`, handoff `.agent/T028-presentation-handoff.md`)
   -> Codex Architect (resumed session) spec `.agent/T028-architect-presentation.md`,
   landed as D-2026-10-04-plain-language-analysis-views; AC21 + recommendation
   tab inventory amended; legacy-copy follow-up after T029 (`74f66d4`).
   Checkpoint 1 (default reading + Analysis tabs + vocabulary in touched copy)
   dispatched to fresh session-model implementer. Then checkpoint 2 (four
   graphics + vocabulary guard + layout) by a fresh implementer from
   `.agent/T028-presentation-cp1-handoff.md`; then fresh Claude review; owner walk
   (default views first, then Analysis); merge.
   Checkpoint 1 done `82af69c` (backend 1491, host 619, frontend 1104, build,
   checks; handoff `.agent/T028-presentation-cp1-handoff.md`). Checkpoint 2 split:
   2a graphics (dispatched, fresh session model) -> `.agent/T028-presentation-cp2a-handoff.md`;
   2b vocabulary guard + remaining T028-journey jargon (drawer normalization
   statement, rejection details, Overview interval_statement) + rewrite stale
   layout claims (layout-evidence.mjs ~4229-4340) + layout run + packet.
   2a done `55f6fe8` (four graphics in `frontend/src/sites/assessmentGraphics.tsx`,
   card timeline projection; frontend 1124, backend 1492, build, checks; no
   layout run). 2b dispatched (guard, jargon, layout rewrite + run, full
   suites, packet walk, records).
   2b done `9e40a13` (vocabulary guard `frontend/src/test/productVocabulary.*`,
   jargon removed, layout 615/4 known + Lab-off 4/0; backend 1493, host 619,
   simulator 244, frontend 1132, build, checks; packet walk rewritten).
   Fresh Claude review of 30122ed..9e40a13 running ->
   `.agent/T028-presentation-claude-review.md`. Then owner walk, merge.
   Presentation review (Claude) ACCEPT with F1 block; F2-F4, F7 rest carried
   (`74f769b`). Sonnet fix round: F1, F5, residual jargon, F6. Then owner walk.
   Fix round done `05ae70f` (frontend 1134, backend 1493, host 619 + build run
   by coordinator, checks pass). T028 READY FOR OWNER WALK: packet
   `.agent/T028-review-packet.md` last section. Record owner text verbatim,
   then mark done, move task to completed, merge to main.
   Former owner decisions for UI review (now with the Architect): gap rule (only a gap that left a segment
   Indeterminate lowers Full to Limited) and site-wide readiness window.
3. Then phase 3, then a fresh Claude reviewer (or Codex after reset), then owner UI check.
4. After the Codex reset (21:23 today): ROLE_CONFIG revert, retrospective list
   (add T028 phase 1 if Claude-reviewed), ask who takes in-flight roles.

---
Older history follows.

# Coordinator handoff (2026-10-03, T027 merged; T028 next)

A fresh coordinator starts from this file; do not re-derive what it states.

## Current state (supersedes older sections below)

- **T027 is complete and merged**: `main` at `1f4e64c` (nothing pushed). Owner
  hands-on checks of both phases successful (`.agent/owner-T027-phase-2-hands-on-2026-10-03.md`).
  Owner ruling 2026-10-03: "Start Simulation" stays a disabled Quick action with
  its Run-setup reason. Final suites: backend 1435, host 602, simulator 244,
  frontend 1071; both checks pass.
- Codex retrospective list: T025e, T025f, T025g, T026, the demo-led plan,
  T027 phase 1 and phase 2.
- Carries in `.ai/MILESTONE_REVIEW_BACKLOG.md` "Carried from T027 phase 1/2"
  (N2, N6, registry location for T034; generator runtime for T028; Lab
  "no accepted evidence" wording fast lane; intermittent T026 layout claim).

## Next actions

1. **T028** (dispatch Finding, `tasks/T028-dispatch-finding-and-evidence.md`) by a
   fresh Implementer; read the T028 generator-runtime carry first.
2. After the Codex reset (2026-10-03 21:23): revert Architect/Planner/Reviewer in
   `.ai/ROLE_CONFIG.md` to Codex, queue the retrospective reviews above, and ask
   the owner who takes in-flight roles.

---
Older history follows.

# Coordinator handoff (2026-10-03, T027 phase 1 accepted; phase 2 next)

A fresh coordinator starts from this file; do not re-derive what it states.

## Where things stand

- `main` at `4ae4d4b` (nothing pushed): the demo-led recommendation and replan
  (`f7325c3`) plus T025h parked in `.ai/MILESTONE_REVIEW_BACKLOG.md`
  ("Parked task: T025h"; pick up not before T029 with the T026 AC15 p95 task;
  branch `task/T025h-picker-compatibility` is superseded, do not merge).
- Sources of record: `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` (owner-approved),
  `.ai/DECISIONS.md` `D-2026-10-02-*`, `tasks/README.md` queue T027 -> T028 ->
  T029 -> T029B -> T029A -> T034 -> T034A -> T031 -> T032 -> T030 -> T035 ->
  T033 -> T025i -> T036.
- Owner text, verbatim, in `.agent/owner-*-2026-10-02.md` (review,
  instruction, approval, acceptance); each approval file separates the owner's
  words from the coordinator's reading.
- **T027 phase 1 is accepted** on `task/T027-commit-ingestion-and-site-overview`
  (cut from `f7325c3`; HEAD `dfb9651`; task `Status: in_review`, phase 2 open).
  - Owner hands-on check: successful (`.agent/owner-T027-phase-1-hands-on-2026-10-03.md`).
  - Review `.agent/T027-phase-1-claude-review.md` (accept with one fix);
    fix round `c9fb412..24bc13e`; re-review `.agent/T027-phase-1-claude-rereview.md`
    (accept); N10 `.pyc` untracked in `dfb9651`.
  - Suites: backend 1417, host 602, simulator 244 (run from `simulator/`),
    frontend 1056; both checks pass. Layout evidence from phase 1 build:
    4 pre-existing FAILs only.
  - Carried to `.ai/MILESTONE_REVIEW_BACKLOG.md` "Carried from T027 phase 1":
    release resume needs the live stage (N2), evidence store design (N6),
    configuration-registry location (owner question, trigger T034).
  - Phase 2 handoff: `.agent/T027-phase-1-handoff.md` (includes N9: one
    source for `NEEDED_SIGNALS` and the AC22 profile).

## Next actions

1. T027 phase 2 (mini-grid Site Overview: AC11, AC22, and the Overview
   extensions of ACs 10, 12-15, 19) by a fresh Implementer from
   `.agent/T027-phase-1-handoff.md`. Ends with full suites, layout evidence,
   final packet.
2. Fresh Claude Reviewer on phase 2 (or Codex after the reset; ask the owner),
   then the owner's demo point 1 check.
3. Before T027's final merge: merge `main` (`4ae4d4b`) into the T027 branch.

## Open owner items (defaults stand until the owner rules)

- Demo point 3 shows the Action already accepted (no live Accept click).
- Name of the evidence-limited Portfolio-lite site: left to T034A's Planner.
- Global Financials root vs Portfolio view: decide after T036.

## Standing rules

- Owner restarts sessions to save usage: dispatch long agents only when the
  owner expects them to run in this session; otherwise leave the next action
  here for a fresh session.
- Pass owner feedback to agents verbatim via a saved `.agent/` file.
- `.ai/ROLE_CONFIG.md`: after the Codex reset 2026-10-03 21:23, revert the
  Architect, Planner and Reviewer rows to Codex, queue retrospective Codex
  reviews of T025e, T025f, T025g, T026 and the demo-led plan, and ask the owner
  who takes in-flight roles.
- `.agent/` is gitignored: commit with `git add -f`.

## Update 2026-10-03 ~10:25: T027 phase 2 built and reviewed; owner UI check next

- Phase 2 on the T027 branch (HEAD bb8976d): packet `.agent/T027-phase-2-review-packet.md`
  (fix rounds 1-3), layout `.agent/T027-phase-2-layout-evidence-fix-round-1.txt`
  (513 PASS / 5 FAIL: 4 known + intermittent T026 delayed-reading claim, backlogged).
- Reviews (all Claude, temporary binding): `.agent/T027-phase-2-claude-review.md`
  (F1-F5), `-claude-rereview.md` (R1-R3), `-claude-rereview-2.md` (S1, S2).
  Fix round 3 (S1/S2, strings + comments only) verified by the coordinator:
  tsc clean, frontend 1071. Backend 1435, host 602, simulator 244.
- Owner asked (2026-10-03): send to reviewer, owner does UI check after all is
  complete. Next: owner UI check (packet "User-review focus" 1-7), owner rulings on
  energy wording (point 6) and on "Start Simulation" (keep disabled with true
  reason vs remove/link to Run setup). Then merge main (4ae4d4b) into the branch,
  mark T027 done, merge.
- Codex retrospective list gains T027 phase 1 and phase 2.
