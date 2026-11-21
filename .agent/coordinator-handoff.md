# Coordinator handoff (current block, 2026-11-21 ~07:30 UTC)

One current block, at most 2k tokens, replaced rather than appended (`.ai/RULES.md` §9). Previous block (to 18 Nov) is in git history of this file.

## Read first on resume

1. This block, then `git log --oneline -25` on `main`.
2. `specs/OWNER-AWAY/decisions-2026-11-21.md`: every call the Architect made while the owner was away (owner delegated ~12 h from ~04:00 UTC 21 Nov, `owner/owner-away-architect-decides-2026-11-21.md`), plus the pull order.
3. Plan: `Docs/demo-sprint/product-direction-layer4/two-week-build-plan.md` §0 (day 1 = 20 Nov).

## Merged on main 21 Nov (this session)

3B2, 0K1 (+ follow-up), 4a (+ follow-up), 3B6, DS3, 3A6, 3B4; specs+handshakes for DS3, 4a, 3B6, 3B4, 0K1; owner-away decisions. Earlier: 11 of 14 deep-dive path units.

## In flight (branch · worktree · state)

- 3A6 `task/3A6-source-profiles` · `-3a6` · review round 5 running (rounds 1-4 each found an xlsx/CSV resource-exhaustion route; r4 bounds every resource). Merge unblocks 3A7 and 3C2 code (gate A).
- SC-1a `task/SC-1a-composer` · `-sc1a` · head 987d36ca7, review round 3 ACCEPT; READY, merge needs OWNER approval of its two check-all lines (owner-away rows 5, 23, 24; one-page note atop SC-1 rulings "Review answers (round 1)"). Reviewer owner line: stops 14/20 backend merges, ~2% false alarms, +20 s per check-all.
- DS3 `task/DS3-bulk-loader` · `-ds3` · discovery review running. permitted_database now refuses walk/serve DBs.
- 3C1b `task/3C1b-person-actions` · `-3c1b` · review ACCEPT (Lows L1-L3) but HOLD: merge with its SC-1 text commit after SC-1a (stored publish note says "SYSTEM demonstration"). Migration 0070 provisional.
- 3B6 `task/3B6-cold-ev` · `-3b6` · build running (4a merged, all parts open).
- 3B4 `task/3B4-observer` · `-3b4` · units 1-3 build running; migration 0071 provisional; check.py commit after 3B6 merges.
- IA-2a `task/IA-2a-plan` · `-ia2a` · build (mock-up) running; 5c pre-empts the UI lane when it can start.

## Next (pull order after these)

3A7 commit 1 and 3C2 commit 1 (no text) when 3A6 merges; their text commits and 3C1b's after SC-1a merges; 5c when 3A7 merges; DDR after. Then 0K2, 0M, 1a, DS4 (spec not written: needs telemetry-source survey; walkthrough serve of a DS4 world held for owner), WK, IA-2b.
Migrations on main: 0067 3A6, 0068 3B4. Unmerged, renumber at merge in merge order: 3A7 (built as 0068), 3C2 (0069), 3C1b (0070).

## For the owner on return

- Approve or decline SC-1a's two check-all lines.
- Review owner-away rows marked "owner to weigh in" (17, 18, 21, 22, 26, 27, 28 and others in the log).
- Demo DB needs a 3B7a snapshot rebuild after 4a (else "rebuild needed" on every page); walkthrough DB untouched.
- /tmp quota: old session scratch `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/` (6.9 GB) and `/opt/assetecon/arch-scratch-1121b` can be deleted (classifier blocked the coordinator).
- 11 pre-existing Postgres failures on main (backlog).

## Standing constraints

Unchanged from `.ai/RULES.md` §3, §7-§9. Notes: `.agent/` is git-ignored: commit tracked files there by path (`git commit -- <path>`) or `git add -f`. Bookkeeping collisions: tell spec branches to merge main before and after writing, and take the next free OWNER-AWAY row. specs/INDEX.md cap 8000 bytes. Briefs: keep scratch small and delete it.
