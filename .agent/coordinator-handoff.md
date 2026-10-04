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
