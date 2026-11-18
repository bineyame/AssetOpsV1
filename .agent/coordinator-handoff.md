# Coordinator handoff (current block, 2026-11-18)

One current block, at most 2k tokens, replaced rather than appended (`.ai/RULES.md` §9).
The full previous text (2026-11-09 to 2026-11-18) is verbatim in
`.ai/history/coordinator-handoff-to-2026-11-18.md`; read it only for a named past event.

## Read first on resume

1. `.ai/NOW.md` (active lanes), then `git log --oneline -20` on `main`.
2. This block.
3. The indexes, by ID only: `specs/INDEX.md`, `owner/INDEX.md`,
   `.ai/decisions/INDEX.md`, `.ai/state/INDEX.md`.

## Where things are (since declutter step 4)

- Specs and their rulings: `specs/<ID>/` (an over-cap sheet is split into
  `spec.md`, `rulings*.md`; its `README.md` maps old line numbers). Live:
  `specs/OWN-GAPS/` (demo-sprint rulings D-SR, D-E5, D-PRICE, ...) and
  `specs/DIESEL-1/` (rulings through 9v; K8c captures not merged).
- Owner words, verbatim: `owner/` (`owner/INDEX.md`). The O4 concise summary
  (`owner/SUMMARY.md`) is drafted on `task/declutter-04b-owner-summary`; the owner
  confirms it before any original is archived.
- Finished packets, reviews, rulings, handoffs, architect notes:
  `archive/agent-history/` (not a default read). Old `.agent/` paths:
  `specs/CITATION_MAP.md`.
- Evidence: `/opt/assetecon/evidence/` (RULES §9), never the tree.
- `.agent/` keeps only live coordination files and files code reads (list in
  `tools/declutter/step4_map.py` KEEP).

## Lanes

- Layer 4 direction: `task/product-direction-layer4-design`, worktree
  `/opt/assetecon/AssetOpsV1-layer4`; owner answers to Q1-Q16 and D1-D12 open.
- GTM documents: `task/gtm-documents`, worktree `/opt/assetecon/AssetOpsV1-gtm`
  (based on the Layer 4 branch).
- Declutter: step 4a (`task/declutter-04-specs-history`) and 4b
  (`task/declutter-04b-owner-summary`) in build/review; step 5 (Docs, tools) next.
  Lanes merge `main` as in the step-3 and step-4 lane notes
  (`specs/DECLUTTER/packet-declutter-03.md`, `specs/DECLUTTER/packet-declutter-04.md`).
- Walkthrough worktree `/opt/assetecon/AssetOpsV1-walk` (`task/WALK-1113-build`,
  DB `assetops_polish_walk1113_test`, serve on 5490 with API 8990): do not touch.

## Owner decisions pending (as of 2026-11-14; to confirm still open)

- Page-load D1-D6 (`.agent/page-load-architecture-review-2026-11-14.html`;
  coordinator recommendation: C, no change before the walkthrough, after 17 Nov;
  accept D3/D5/D6). Mediums P1/P2 from its re-review go into the C1/C1b packet.
- Grow card: billed/collected money beside the estimate or instead of it
  (recommendation: beside).
- D-SR.81 (EV availability counts a reported charging state as in service): owner
  may overrule for option 2.
- Whether the 17 Nov client demo happened (NOW §3).

## Open technical notes (from the 2026-11-13/14 blocks)

- EV overview 11-03 was 2.2 s on an unstored route during a full warm; re-time when
  idle; if still over 2 s, store the EV overview.
- Pre-existing failures on `main`: `test_w302_evidence_api` (2 tests: "Opens this
  range" vs "Current view"); `test_s5_overview_postgres` late_power and
  `test_s4_schedule_health_postgres` (STALE_PROJECTION, possibly environmental);
  `test_ch5a1_reader_postgres.py` collection NameError without a DB URL.
- Backlog Lows: D-SR.82 docstring "<=" vs "<"; D-SR.83 L2 (gate result not in the
  key); add-day does not rerun evidence comparison; Health watermark inputs
  (D-SR.56). Post-demo backlog: `.agent/backlog-post-demo.md`.

## Standing constraints

- Owner rules are in `.ai/RULES.md` (§3 approvals, §7 machine, §8 git, §9 tidy).
- Network loss: treat an agent or job that ended on a network/API error as
  interrupted; wait for reconnection, then resume it, telling it to check disk
  and git first.
- DBs: `*_test` and `<prefix>_audit*` in `assetopsv1-postgres-1` only. One heavy DB
  job at a time; `setsid nohup` for long jobs; kill by PID only.
- New worktrees: symlink `frontend/node_modules` to the main checkout's, or two
  missing-claim guards fail.
- Leave the uncommitted `.agent/owner-walkthrough-notes-2026-11-01.md` and
  `Docs/demo-sprint/implementation-logic-design-proposal.html` on `main` alone;
  once the notes file is committed, move it to `owner/` with its index row.
- Check-all: builders run `pwsh -NoProfile -File tools/check-all.ps1` themselves
  (2 at once); the coordinator runs it on `main` after each merge.
