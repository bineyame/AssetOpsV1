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
- SC-1a `task/SC-1a-composer` · `-sc1a` · head 987d36ca7, review round 3 ACCEPT; at merge its .ai/decisions/index-rulings-19.md collides with main's (0M; and -20 is 0K3's): rename SC-1a's to the next free number (21+); READY, merge needs OWNER approval of its two check-all lines (owner-away rows 5, 23, 24; one-page note atop SC-1 rulings "Review answers (round 1)"). Reviewer owner line: stops 14/20 backend merges, ~2% false alarms, +20 s per check-all.
- DS3 `task/DS3-bulk-loader` · `-ds3` · discovery review running. permitted_database now refuses walk/serve DBs.
- 3C1b `task/3C1b-person-actions` · `-3c1b` · review ACCEPT (Lows L1-L3) but HOLD: merge with its SC-1 text commit after SC-1a (stored publish note says "SYSTEM demonstration"). Migration 0070 provisional.
- 3B6 `task/3B6-cold-ev` · `-3b6` · build running (4a merged, all parts open).
- 3B4 `task/3B4-observer` · `-3b4` · units 1-3 build running; migration 0071 provisional; check.py commit after 3B6 merges.
- IA-2a `task/IA-2a-plan` · `-ia2a` · build (mock-up) running; 5c pre-empts the UI lane when it can start.

- IA-2a `task/IA-2a-plan` · `-ia2a` · fix round r2 (the round-2 review answers) running; then verification; merge held for owner walkthrough. IA-2b spec `task/IA-2b-spec` (d789117f3) cites IA-2a rulings: merge it only AFTER IA-2a merges (a premature merge was reverted). Answers on task/IA-2b-handshake-answers (590da9d75): at merge renumber its owner-away row 47 to the next free (main's 47-48 are ENV-1/0K3) and its index-rulings-20.md to the next free index file (main's -20 is 0K3). IA-2b1 (4 units) builds off IA-2a's head once IA-2a r2 is verified. IA-2b2 waits for the owner's IA-2a walkthrough; two owner defaults: no hub Decide button, no 'at stake' tile on Decisions/Findings/Actions.
- 0M `task/0M-mto-headroom` · `-0m` · build running.

## Next (pull order after these)

3A7 commit 1 and 3C2 commit 1 (no text) when 3A6 merges; their text commits and 3C1b's after SC-1a merges; 5c when 3A7 merges; DDR after. Then 0K2, 0M, 1a, DS4 (spec not written: needs telemetry-source survey; walkthrough serve of a DS4 world held for owner), WK, IA-2b.
Migrations on main: 0067 3A6, 0068 3B4. Unmerged, renumber at merge in merge order: 3A7 (built as 0068), 3C2 (0069), 3C1b (0070).

## For the owner on return

- 0K2 merged (simulated season, not a real Site): stop-70/30 saves ~85 L/month vs design 210 (it only cuts the clear-morning run, ~3.7 L/day; nothing on overcast days; no idle burn in the model), 0 kWh added vs design 150; reserve-25/stop-90 saves ~48 L vs design 20, adds ~38-40 kWh. Design values unchanged (row 37 held). Explanation: specs/0K2-kobo-replay-study/review.md "Design values beside the study".
- DEMO-CRITICAL defect found on main by DS4's spike (D-DS4.27): 5a refused every price line (is_money vs any money unit), so plan tariff/diesel price/necessary and diesel litres read Not available yet at every Site, blanking 5c's targets. Fix 5a F1 on fix/5a-F1-money-unit (in build); must merge before any world walkthrough. Kisiwa O&M blank is honest (no October invoice; D-DS4.26).
- IMPORTANT, row 42: by the shipped dispatch law no reserve-30 Kobo case can keep dawn at or above 35%, contradicting the pack's stop-70 "0 of 61 / dawn PASS" (MG-T2, 2,916.00). 0K2 reports figures as they come; owner decides the claim/admissibility (via 6c).
- Row 41 fixed honestly: adjustments kWh reads "Not available yet" when the export never carried them (4a fix branch fix/4a-adjustments-blank).
- Held: rows 36 and 40 (walkthrough serve of a DS4 world; creating /opt/assetecon/keys and /opt/assetecon/worlds).
- Approve or decline SC-1a's two check-all lines.
- Review owner-away rows marked "owner to weigh in" (17, 18, 21, 22, 26, 27, 28 and others in the log).
- Demo DB needs a 3B7a snapshot rebuild after 4a (else "rebuild needed" on every page); walkthrough DB untouched.
- /tmp quota: old session scratch `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/` (6.9 GB) and `/opt/assetecon/arch-scratch-1121b` can be deleted (classifier blocked the coordinator).
- 11 pre-existing Postgres failures on main (backlog).

## Standing constraints

Unchanged from `.ai/RULES.md` §3, §7-§9. Notes: `.agent/` is git-ignored: commit tracked files there by path (`git commit -- <path>`) or `git add -f`. Bookkeeping collisions: tell spec branches to merge main before and after writing, and take the next free OWNER-AWAY row. specs/INDEX.md cap 8000 bytes. Briefs: keep scratch small and delete it.
