# Now

Active lanes only, one block each. Replaced, not appended; history is in git
(previous version: `.ai/history/active-context-to-2026-11-18.md`).
Last updated 2026-11-18.

## 1. Layer 4 product direction (awaiting the owner)

- Branch `task/product-direction-layer4-design` (not merged to `main`).
- Pack: `Docs/demo-sprint/product-direction-layer4/`; read
  `Docs/demo-sprint/product-direction-layer4/product-transition-and-roadmap.md`
  first.
- State: roadmap rev 3 done. Owner decisions open: Q1-Q16
  (`Docs/demo-sprint/product-direction-layer4/design-questions-and-decisions.md`)
  and D1-D12 (roadmap §6). D11 (workflow W1-W9) is adopted and recorded in
  `.ai/RULES.md`.
- Owner words: `.agent/owner-layer4-direction-feedback-2026-11-17.md`,
  `.agent/owner-product-transition-request-2026-11-18.md`.
- Next: owner answers. The pack is frozen except for decisions and the
  mock-up gate (D10, recommended; to confirm).

## 2. Repo declutter (in progress)

- Spec: `.agent/repo-declutter-recommendation-2026-11-18.md` (§4.2 steps);
  owner decisions O1-O7 and D11 in
  `.agent/owner-repo-declutter-request-2026-11-18.md`.
- Step 1 (start path, text only): reviewed (ACCEPT WITH NOTES, notes fixed)
  and merged to `main` from `task/declutter-01-on-main`.
- Step 2 (indexes; DECISIONS and CODE_STATE split verbatim): reviewed and
  merged to `main`.
- Step 3 (evidence out of the repo, 2-week retention): built on
  `task/declutter-03-untrack-evidence`, packet `.agent/packet-declutter-03.md`,
  in review (revision 2). Evidence now goes to `/opt/assetecon/evidence/`
  (RULES section 9). Merging it into a worktree removes that worktree's
  untracked `.agent/` evidence files; copies are in
  `/opt/assetecon/evidence/repo-untracked-2026-11-18/` (manifest) and the
  coordinator backup. Lanes merge `main` as in the packet's lane note.
- Next: steps 4 (specs, owner files and history), 5 (Docs and tools). Each on
  its own branch, reviewed and merged before the next.

## 3. Demo sprint (live product on `main`)

- `main` head at this writing: `fe2392899` (2026-11-15).
- Coordinator state and lane rules: `.agent/coordinator-handoff.md`,
  `.agent/lane-rules-vps-2026-11-12.md`.
- Rulings: `.agent/build-sheet-OWN-GAPS-2026-11-08.md`; plan
  `.agent/architect-sequence-client-scope-2026-11-11.md`.
- Walkthrough worktree `/opt/assetecon/AssetOpsV1-walk`
  (`task/WALK-1113-build`, DB `assetops_polish_walk1113_test`): do not touch
  without the coordinator.
- Owner decisions pending (from the handoff, 2026-11-14): page-load D1-D6
  (`.agent/page-load-architecture-review-2026-11-14.html`) and the Grow card
  money question. To confirm: whether these are still open, and whether the
  17 Nov client demo has happened.
- Owner documents on `main`: `.agent/convertion_potential.html`,
  `.agent/decision-intelligence-mechanism-2026-11-14.html`.

Also active: `task/gtm-documents` (worktree `/opt/assetecon/AssetOpsV1-gtm`,
based on the Layer 4 branch): two-week conversion plan, commercial plan and
website content documents (`Docs/go-to-market/`).

Check-all (PIPE-1, merged): builders run the fast check-all themselves (2 at
once); the coordinator runs it on `main` after each merge.

No other lane is active. The S1-S7, W1-W6 and OUT/POLISH/DEMO "in_review"
records in the old active context are history: their branches are not present
on this machine and the coordinator reports the work merged to `main`
(to confirm per slice only if one is reopened).
