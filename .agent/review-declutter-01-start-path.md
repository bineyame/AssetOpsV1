# Review: declutter step 1, lean agent start path

- Target: commit `4797e095d` against parent `ff72c58fb`, branch `task/declutter-01-start-path`. `a6f32d883` (owner file only) not reviewed.
- Spec: `.agent/repo-declutter-recommendation-2026-11-18.md` §2, §3.2, §4.2 step 1, §5; owner O1-O3 and D11 in `.agent/owner-repo-declutter-request-2026-11-18.md`.
- Reviewer: a fresh Claude `assetops-reviewer` subagent (Opus), not the author. Discovery depth.

## Verdict: ACCEPT WITH NOTES

Fix M1 on the branch before merge. It is a one-bullet text fix, and a mechanical check by the coordinator is enough. The Lows are optional or can be carried.

## Summary

- O1, O2, O3 and D11 are stated faithfully:
  - O1 boundary: `START_HERE.md:16-31`.
  - O2 mock table, plus "do not read v69/v71": `START_HERE.md:33-45` and `AGENTS.md:33-34`. v70 has the same 110 screen IDs as v69, so existing rulings that cite screen IDs still resolve.
  - O3: 2 weeks, outside the repo (`RULES.md:167-174`).
  - D11 W1-W9: `RULES.md:48-84`, which matches roadmap §5.2 in condensed form. The lane split and pilot detail are left in the roadmap, as they should be.
- The bindings agree across `ROLE_CONFIG.md:10-15`, the role briefs, the commands and the skills. The Planner is bound to Codex in ROLE_CONFIG. `.claude/agents/assetops-planner.md` refuses when the role is bound elsewhere, and the command prepares a handoff. That command-versus-subagent split already existed and is consistent with `ROLE_CONFIG.md:30-31`.
- The history copies are verbatim plus a superseded header: ACTIVE_CONTEXT, PROJECT_RULES, WORKFLOW, ROLE_CONFIG and the tasks/README narrative were diffed against `ff72c58fb`. Each redirect stub points to its history copy.
- The owner standing rules are each stated once and correctly, except the walkthrough and port rule (M1) and the full-suite rule (L1):
  - DB safety: `RULES.md:142-143`.
  - Verbatim relay: `RULES.md:46`.
  - Fresh Claude re-reviews, with Codex never blocking: `ROLE_CONFIG.md:15-18`.
  - Never work on main: `AGENTS.md:41`, `RULES.md:152`.
  - Token efficiency: `ROLE_CONFIG.md:44-74`.
  - No execution-policy override: `RULES.md:138-141`.
- Default load per role (bytes/4) is within the author's 5-7k claim. All files are under the §5.3 caps (table below).
- The guards pass, every cited path resolves, and the only remaining stale strings are the machine-read `tasks/README.md` rows.
- Fresh-agent test: the start path answers direction, governing mock, rules and roles without opening history. On "current work", the only build lane (demo sprint) has no named open unit, which NOW flags as "to confirm". That is acceptable because a dispatch names the spec.
- The "to confirm" items are reasonable: whether demo-sprint units remain after the 17 Nov demo, whether page-load D1-D6 and the Grow card question are still open, the D10 freeze, and how the 2-week retention is counted.

## Findings

### Medium

**M1. The walkthrough ports and the clean-walkthrough-DB rule are not stated anywhere in the start path.** Files: `.ai/RULES.md:130-148` (§7) and `.ai/NOW.md:40-42`.

- The walkthrough worktree and its DB appear only inside NOW's demo-sprint lane block. That block is transient and will be replaced when the lane changes.
- Nothing names ports 5490 (web) and 8990 (API). They are in `.agent/coordinator-handoff.md:215,222` and `.agent/owner-walkthrough-in-6h-2026-11-13.md:5` only.
- Nothing states the owner's rule that a walkthrough runs only on a clean, good DB with no fallback DB (`.agent/owner-clean-walkthrough-over-time-2026-11-13.md`).

Why it matters: demo tooling defaults to these ports (`backend/tests/test_demo_combined_links.py:28,101`, `backend/assetops_backend/chain/prebuild.py:170`). A fresh builder that serves or prewarms with defaults can bind to, or write into, the owner's walkthrough.

Fix: add one standing bullet to RULES §7. The walkthrough worktree, its DB and ports 5490/8990 belong to the owner walkthrough and are never bound, stopped or touched without the coordinator. A walkthrough runs only on a clean, self-checked DB, never on a fallback.

### Low

**L1. The full-suite owner rule is weakened to coordinator discretion.** File: `.ai/RULES.md:132-137`.

- The owner's demo-sprint rule is: no full backend suite per slice, per merge or as a safety net until end-game E2, unless the owner asks (OD-P4; `.agent/coordinator-handoff.md:198`).
- RULES now says "only when the coordinator schedules them".
- E2 has run (`coordinator-handoff.md:170`), so the rule may have lapsed.

Fix: state its current status with the owner source, or add it to NOW's "to confirm" list.

**L2. NOW says "No other lane is active" (`.ai/NOW.md:52`), but `task/gtm-documents` is active.** It has its own worktree (`/opt/assetecon/AssetOpsV1-gtm`), was created at 07:40, three minutes before this commit, and its owner request lands in `a6f32d883`. Fix: add a one-block lane, or drop the sentence.

**L3. NOW and START_HERE point to a stale, oversized coordinator handoff as current state.** Files: `.ai/NOW.md:36`, `.ai/START_HERE.md:11,55`.

- `.agent/coordinator-handoff.md` is 51 KB, about 12.7k tokens, against the 2k cap in `RULES.md:178`.
- Its last update is 2026-11-14, before the 17 Nov demo, and it carries several "read this first" resume blocks.

Fix: label the pointer "pre-17-Nov; coordinator only", or refresh the handoff to one block.

**L4. Merge coupling is not stated as a precondition.** File: `.ai/NOW.md:23-24`.

- The branch is cut from the unmerged `task/product-direction-layer4-design`.
- START_HERE and NOW cite `Docs/demo-sprint/product-direction-layer4/*`, which does not exist on `main`.
- Merging this branch therefore also merges the Layer 4 pack and `a6f32d883`. Recommendation §4.2 step 0 makes the Layer 4 merge, or its author's agreement, a prerequisite.

Fix: state that this branch merges only after, or together with, the Layer 4 branch.

**L5. The workflow guard now checks the stubs, not the router.** File: `tools/check-agent-workflow.ps1:15-38,58-90`.

- It requires the stub files and applies its 200-line cap to the ACTIVE_CONTEXT stub.
- The PROJECT_RULES check passes because the stub contains the four role names.
- It does not require `.ai/NOW.md` or `.ai/RULES.md`, and it enforces none of the §5.3 caps.

A text-only step is a fair reason to defer this. Carry it into the §5.5 guard work.

**L6. A section pointer now dangles.** `frontend/docs/architecture/ui-ux-decision-guide.md:13` cites "`.ai/ROLE_CONFIG.md` Lesson 15". That text now lives in `.ai/history/role-config-history-to-2026-11-18.md`, and its substance is in `RULES.md:98-101`. Sweep: a `git grep` for section pointers into ROLE_CONFIG, WORKFLOW, PROJECT_RULES and ACTIVE_CONTEXT outside the history folders finds only this one live pointer. The other hits are historical text, and the stubs redirect them. Fix: repoint to RULES §5.

**L7. Minor carry-forward rules were dropped without a ruling on whether they are still live.** Each is one line:

- (a) Keep the gitignored `var/sites`, Lab runs, stages and committed artifacts intact, and import or replay only through explicit migration steps (old ACTIVE_CONTEXT:91).
- (b) Do not switch branches while an agent is running in that tree (old PROJECT_RULES "One Working Copy").
- (c) A unit that touches shared code, schema or a cross-slice seam gets an independent review before the next unit builds on it (old ROLE_CONFIG W5/W6 lesson 9).
- (d) The owner's 2026-10-18 rule that an implementer choice the spec did not fix is a defect (Medium, or High when user-visible). This is softer now under `RULES.md:32-34`, "make the conservative local choice", although the UI guide still bounds UI choices.

Fix: the coordinator or Architect confirms which are live. Add (a) and (b) as one line each.

**L8. Small inconsistencies between the briefs and ROLE_CONFIG.**

- `.claude/agents/assetops-planner.md:12` says "(today: Codex)", and `.claude/commands/assetops-planner.md:13-14` hard-codes the binding. Both contradict `ROLE_CONFIG.md:78-79`.
- The reviewer brief's read list (`assetops-reviewer.md:18-19`) omits ROLE_CONFIG, which `AGENTS.md:12` lists for every role.
- The Architect agent and skill descriptions still say "feature maps", although FEATURE_MAP is now history.

These are cosmetic.

## Default context per role (bytes/4)

| File | Bytes | ≈ tokens | Cap |
|---|---:|---:|---:|
| AGENTS.md | 1771 | 443 | 1.5k |
| .ai/START_HERE.md | 3534 | 884 | 1.5k |
| .ai/NOW.md | 2633 | 658 | 1.5k |
| .ai/ROLE_CONFIG.md | 4646 | 1162 | 3k |
| .ai/RULES.md | 10891 | 2723 | 4k |
| Architect, Implementer, Planner and Reviewer briefs | 1601 / 3301 / 1176 / 2538 | 400 / 825 / 294 / 635 | 1.5k |

Default load per role, as the start path plus the role brief:

| Role | ≈ tokens | Note |
|---|---:|---|
| Architect | 6.3k | |
| Implementer | 6.7k | |
| Planner | 6.2k | |
| Reviewer | 6.5k | 5.3k if it follows its brief, which skips ROLE_CONFIG |

`tasks/README.md` is still 32.8k bytes, but it is not on any default path.

## Checks run (on the working tree at `a6f32d883`; files under review are identical to `4797e095d`)

- `pwsh -NoProfile -File tools/check-agent-workflow.ps1`: "Agent workflow check passed." rc=0.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: rc=0. The panel summary printed with no failure.
- `node --test frontend/docs/architecture/test_delivery_next_work.cjs`: tests 35, pass 35, fail 0.
- Consumers of the moved or renamed files (grep over `tools/`, `frontend/`, `backend/`, `host/`; no CI config exists):
  - `tools/check-agent-workflow.ps1` reads the stub paths (L5).
  - `delivery_next_work.cjs`, `check_v69_dependency_registry.cjs` and `test_delivery_next_work.cjs` parse `tasks/README.md`. The rows, gate paragraphs and links are kept, and the tests pass.
  - `ui-ux-decision-guide.md:13` (L6).
- Path resolution:
  - Every backticked path in AGENTS, START_HERE, NOW, RULES, ROLE_CONFIG, the stubs, and the `.claude` agents, commands and skills resolves. Branch names and bare relative names were checked by hand: the v72 four pages, the Layer 4 pack files and the vNEXT folder all exist.
  - Every cited `.agent/` file is tracked.
- Stale-string grep from recommendation §4.2 step 1:
  - "Default binding is Codex" and "only executable queue": none.
  - "S1 Foundation": only in the machine-read `tasks/README.md` rows.
  - v69: only in "do not read" and the guard-plumbing note.
- Branch state: every local branch except `task/WALK-1113-build`, the Layer 4, declutter and gtm branches is merged into `main` at `fe2392899`. None of the 55 `in_review` branches named in the old ACTIVE_CONTEXT exists any more. NOW's "history" claim holds.

## Not verified / residual risk

- The fresh-agent smoke test in recommendation §4.2 step 1 (ask a fresh Architect, Implementer and Reviewer "what is the current work and where is its spec?") has no recorded evidence. I did one read-through as an Implementer instead.
- Whether the 17 Nov demo happened, and whether the demo-sprint rules still apply, cannot be established from the repo. The handoff stops on 2026-11-14.
- D11 is written in RULES §4 as unscoped. In the roadmap it is the workflow "for the roadmap's build". Applying W1 and W8 to small demo-sprint fixes may be heavier than the owner intends. That is a question for the Architect, not a defect.
