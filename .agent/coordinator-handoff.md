> STALE (22 Nov). Current state and remaining work: `.agent/codex-handoff.md`.

# Coordinator handoff (22 Nov, ~11:20 UTC)

Read this first. Previous blocks: `.ai/history/coordinator-handoff-2026-11-22-day.md`, `-2026-11-21-*.md`.
No agents are running at the moment of this handoff (a clean stop before the owner's `/clear`).

## Mode and rules
- The owner is present. UI and other slices merge on review ACCEPT; one owner walkthrough at product shape (`owner/owner-merge-on-accept-ia-shape-k10-2026-11-22.md`).
- Token budget: `.ai/ROLE_CONFIG.md` Dispatch rules. At most 4 agents; briefs of 25 lines or fewer; Opus for first builds, discovery reviews and rulings; Sonnet for fix rounds, continuations, verification and merges; hand-backs of 15 lines or fewer; cap tool output.
- Agents work in their own worktrees. Check `git branch --show-current` = main before every merge. Postgres tests: `tools/heavy-slot.sh --db-lane -- pwsh tools/run-host-tests.ps1 -- <files>` from the worktree ROOT (paths are repo-relative; from backend/ it finds no files). Browser: `source /opt/assetecon/tools/pw/env.sh && export LD_LIBRARY_PATH=$AUDIT_LD_LIBRARY_PATH`.
- Briefs: "delete only scratch files you created; never whole directories under /tmp/claude-1001" (a blanket "delete scratch" wiped other agents' scratch on 22 Nov). Builders must run the WHOLE `src/shell` vitest (via ../tools/heavy-slot.sh) and compare against main, not only focused files (IA-P1 missed 5 failing files).
- A restart cuts off every subagent. Before the next restart: stop dispatching, let lanes hand back, write this file, notify the owner.

## Merged to main on 22 Nov
5c screen, 1a, 0K4m (K10 removed), 6a (verify ACCEPT), IA-P spec rev 3 (14 u), 6a/6c specs rev 2, DD spec rev 2 (30 u), DD1 rulings D-DD.35-40, owner files (P6, IA-P Q1/Q2/Q9-Q12, DD Q1-Q3/Q6-Q9, Kobo data sheets, docs refresh), NOW.md and SUMMARY.md refreshed. Main check-all: 45/45 after 6a.

## Next, in order (each one is ready)
1. **IA-2b1 + IA-2a merge**: branch `task/IA-2b1-lists` (b3102080c, -ia2b1). Gates 110/110 OK, shots lists 264 and plan 98 with 0 bad. A direct merge into main conflicts in vNEXT `index.html` and `loop-core.js` (against 0K4m), and in `.ai/decisions/INDEX.md`, `index-rulings-26.md`, `.ai/state/index-3.md` and `specs/INDEX.md`. Sonnet merge-prep: merge main into the branch in -ia2b1, resolve keeping both sides' intent, rerun ia_gates and the two shots, then the coordinator merges.
2. **IA-P1 review**: `task/IA-P1-frame-portfolio` (78b947376, -iap1), `specs/IA-P-product-shape/packet-IA-P1.md`. Opus discovery review with lean shots. The reviewer should also judge the missing-claim-scan exemptions and the hard-wiring baseline shrink. At merge, its state index line 196 collides with main's 6a 196: renumber. Then IA-P2 (5.0 u, backend; its merge sets the one rung rebuild).
3. **6c review**: `task/6c-option-evaluator` (6c1c4bfea, -6c), packet.md. Commit 2 was not test-first. Opus discovery review; batch its findings with packet deviations 1-7 for one Architect ruling (key ones: the currency of a zero money effect against §5 USD, and the scope of the `assumed` leaves). Its state index 197 collides with DD1's 197.
4. **DD1**: `task/DD1-operators` (68c799339, -dd1), packet-DD1.md. First an Architect ruling on Q-DD1.7 (BLOCKER: minigrid-roles-4 binds one GENERATOR/INVERTER per Site; Kisiwa has 2 generators and Mto 2 inverters, refused with BINDING_ROLE_AMBIGUOUS; likely tied to v9 multi-unit), and review of Q-DD1.8 (limits raised: nodes 2000 to 10000, devices 64 to 96) and Q-DD1.9. The builder must rerun SC-1 `--self-test` and the full fast check-all (not rerun after the re-hash). Then an Opus discovery review. Then DD2.
5. **Spec 6f** (the Decisions screen; demo-critical, unspecced): a fresh Opus Architect, from D-P6.8/.9 and D-IAP.3. Then the 6f handshake.
6. Queued after IA-P: Q11 (cold/EV monthly figures), Q12 (31-day cap); the owner made both part of "demo done" (DD Q8). Then the design-doc + mock alignment pass (owner-docs-refresh-2026-11-22.md).

## Owner-facing numbers
About 51 units to a great demo: IA-P about 9.8, DD about 27.5, 6c 3 (built, in review), 0K4f about 2.75, 6f about 2.5*, Q11 about 3*, Q12 about 2.5* (* = estimate). Kobo kit: FG Wilson P50-3 36 kW + 42 Pylontech US5000; no-load 0.62 L/h Assumed (`/opt/assetecon/evidence/kobo-datasheets/datasheets.md`).

## Logged for the owner's review
Architect calls D-P6.20-33, D-IAP.24-33, D-DD.17-40 (none owner-level). Backlog adds: the 13 operator CLIs' demo guard (D-DD.35), 6a F5 name_of, Q11/Q12, and the docs pass.
