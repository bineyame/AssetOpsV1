# Coordinator handoff (2026-10-09, S2 complete; pre-S3 startup)

A fresh coordinator starts from this file; do not re-derive what it states.

## Current state (2026-10-13, supersedes everything below)
- **UPDATE 2026-10-13 (latest):** main `d57c756`: V-01b merged `34b2a9f` (owner accepted conditionally), registry closeout merged `f024ddc` (review ACCEPT `b680990`), README S4-01/S4-02 rows corrected (41dba44 had written S4-01's done row on S4-02). Guards pass. **Active: G-01** on `task/G-01-mock-gap-catalogue-and-guard` (main directory, `db98e54`), implementer running; owner walkthrough ports 8864/8865/5364/5365. **Next after G-01:** owner chose I-finding-evidence-read / S4-03 over A-S4-financial (contest 2.215 vs 2.187, 1.26%; `.agent/owner-next-work-2026-10-13.md`). G-02 due at the free slot after G-01 merges — order G-02 vs S4-03 per D-2026-10-13-g-gap-packet-activation (G-02 'next free slot after G-01'), check with owner if ambiguous.
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
