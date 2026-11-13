# SR-7 / SR-11 pages review (fresh, independent)

Branch `task/SR-7-11-pages` at 194cc6f61 (worktree `/opt/assetecon/AssetOpsV1-sr7`); diff `git diff $(git merge-base HEAD main) HEAD`, 24 files.
Reviewer: fresh Claude, 2026-11-13. Rules: `lane-rules-vps-2026-11-12.md` (no check-all, no DB).

## Verdict: ACCEPT WITH NOTES

The pages do what rev 10 §10.3, 10b.3 and D-SR.24-26/45/51/57/58/60/70-72 ask. One Medium: the register rows R725/R728 are missing. It is a doc-only fix on the branch and needs no re-review. The Lows and the Architect questions do not block.

## Checks run (by me, this revision)

- vitest: `claimLimitRange` 11, `evidenceClaimLimit` 50, `miniBackupRange` 6, `miniBackupRoutes` 9, `miniServiceRange` 8, `miniServiceRoutes` 16 (6 files, 100 passed). Shell: `sr2RequestUrls` 23, `siteEvidenceScreen` 16, `siteRangeTags` 11, `v01bEvidenceVisual` 22 (4 files, 72 passed). 0 failed.
- `npx tsc --noEmit`: clean, with no output.
- pytest no-DB (worktree PYTHONPATH): `test_sr7_service_range.py`, `test_sr7_claim_limit_range.py` and `test_sr11_backup_range_route.py` gave 44 passed in 2.9 s.
- Not run: check-all (left to the coordinator), Postgres/parity tests (waiting for the DB slot, as the packets say), and the implementer's 122-file Site-href sweep (I cite it and did not rerun it). Layout evidence was not in the packet and was not run. The day tables use the existing `DataTable`/`Panel`, so layout risk is low, but the claim says nothing about wide-table behaviour at phone width.
- Stray files: none. `git status` is clean. The diff holds only source, tests and the two packets.

## Checked against the dispatch

- **Day states render honestly.** Service: SERVED_ALL and SHORTFALL show figures. NO_VALUE ("No critical-load figure for this day", D-SR.26), NO_READINGS, NOT_ENOUGH_READINGS, STILL_PROCESSING ("Still being prepared") and NOT_EXPECTED span the row in words, with no zero shown. A counted PARTIAL day reads "· Partial day: x h of y h covered", and the status bar adds a "partly covered" count. Backup: NO_DATA ("No readings this day"), STILL_PROCESSING, NO_ASSESSMENT and NOT_EXPECTED span in words. A partial day is flagged. The test asserts the text has no `/outage/i` match, and none of the words say "outage". Start successes come from the server's `totals.start_success_count`, which is null when no witnessed request/result exists. The hour-card sum is pinned server-side (SR-11 Low 1, `test_sr11_backup_range_route.py`).
- **Hour link and Back.** "Open the 12:00 hour" is the server `hour_link`, which carries `{wholeRange}` in react-router history state. Back uses that state, otherwise falls back to the UTC day of the address. A `day=` drill-in drops `day`/`date`/`revision`.
  - A reload keeps `history.state` (BrowserRouter `usr`), so Back still returns to the whole range.
  - A shared link has no state, so Back opens the hour's own day. This is pinned ("a story hour reached directly goes back to its own day").
- **Single declarer.** `miniServiceRange.test.tsx` and `miniBackupRange.test.tsx` count mounted `useDeclareRangeSpan`/`useDeclareRangeFocus`: 0 in the range view, 1 in the hour view, back to 0 after Back.
- **Claim-limit link.** The server `day_link` gives `/sites/{code}/evidence?day=&revision=`, and `dayHref` adds `view=analysis`. `RangeLink` carries `from`, `to` and `known_at`, as pinned in `claimLimitRange.test.tsx:115-118`. A NO_SELECTION row has no link.
- **No code strings in visible text** (grepped `.code}`, `.state}` and `code` across the new components). Codes appear only in `data-*` attributes (`data-range-code`, `data-*-state`), which are not visible. `ceiling_statement` and `reasons` are not rendered. The "CODE: message" disclosure is fixed (`EvidenceClaimLimit.tsx:524`), and a test asserts there is no code in the section text. See I-1 for a pre-existing exception on the drilled-in one-day section.
- **503 wording.** `SITE_*_RANGE_UNAVAILABLE` and `TEMPORARILY_UNAVAILABLE` are retried at 2/4/8 s. The page shows "Temporarily unavailable. Retrying…", then "Still unavailable. Refresh to try again." These are the shared INFRA-1 constants. Tests cover both, plus a retry of the same URL.
- **Re-pinned tests are faithful.**
  - `miniServiceRoutes` and `miniBackupRoutes`: the two-hour and off-clock-hour cases now assert the range read URL, no hour read, and "All pages".
  - `siteRangeTags`: the bare Service tag is "All pages", and the explicit story hour keeps "Showing 9 Nov".
  - `sr2RequestUrls`: the old Service-under-Yesterday hour pin moved into a new describe that pins exact `service-range`/`backup-range` URLs and no `/performance/mini/(service|backup)` read.
  - `v01bEvidenceVisual`: the one assertion is weakened (range read or table present, no "No assessment selected"), which is acceptable for the new behaviour.
  - No case was deleted without a replacement. The removed "unprovable cause" rows are now positive range-view cases.

## Findings

**M-1 (Medium, acceptance/process): R725 and R728 are not registered.**
- Where: `.agent/mock-departure-register.md` ends at R719 on both main and the branch. `MiniServiceRange.tsx:9` and `MiniBackupRange.tsx:10` cite "MOCK DEVIATION R725/R728", and rev 10 §10.3 and 10b.3 name them.
- Why it matters: earlier slices (FC-1, E5-FX, SR-4c) added register rows, and the post-W6 reconciliation reads the register, not the code comments.
- Fix: add rows R725 (`service` 8.21: one selected hour, now a day table over a range with the hour as drill-in) and R728 (`backup` 8.24: one hour's event chains, now a day table plus "Sequences in this range"; note the Q-J6 column reduction) with `git add -f` of that file only.
- Note: R720-R724, R726 and R727 are also absent. That belongs to the coordinator or the other lanes, not to this slice.

**L-1 (Low, edge): the shared-link Back fallback uses the UTC day of the hour, not the Site-local day.**
- Where: `SiteRangeParts.tsx:128` (`rangeSearch(params)`).
- Why it matters: at UTC+13/+14, local noon of day D is 23:00Z of D-1, so Back from a shared hour link opens D-1. The demo Sites (Africa/Nairobi) are not affected.
- Fix if wanted: derive the day from `localDateOf(tz, from)`.

**L-2 (Low, UX): changing the hour on the hour page loses the carried range.**
- Where: `MiniPerformance.tsx:1332`, `2014`. The hour picker's Apply navigates without the carried `wholeRange` state.
- Effect: after changing the hour, Back opens the new hour's own day instead of the whole range.
- Fix: pass `{ state: location.state }` on that navigate.

**L-3 (Low, test hygiene): the service-range stub carries backup fields.**
- Where: `miniServiceRoutes.test.tsx` (the new `it.each`). The stub body has backup totals (`sequence_counts`, `start_success_count`).
- Effect: harmless, but it reads like a copy from the backup test.

**I-1 (Info, pre-existing): the one-day section shows labelled codes inside its technical disclosure.**
- Where: `EvidenceClaimLimit.tsx:864-912`. The disclosure is titled "Technical details: rule, versions and record references" and shows "Day state code", "Reason code" and others.
- This slice did not change it, and this slice's links now lead to it. Flag it for the W1-end plain-copy pass, not for this slice.

## Architect questions (my view, non-blocking)

- **Q-J6 (backup sequences columns):** I agree with the reduction. Showing the six step columns as "No accepted record" when the day rows carry no `steps` would misstate the data. The table should keep the four fields the rows carry and point to the hour for the steps, as built.
- **Q-J7 (one-day claim-limit 503):** keep the existing plain sentence for this slice. Retrying the one-day read is separate scope. If it is done later, use the same INFRA-1 constants.
- **Cold/EV Evidence with a range:** Cold Sites route to `coldSiteScreen` (`SiteEvidenceFrame.tsx:106`), so they never reach this section. An EV or other non-mini Site that does reach it would show "…read for mini-grid sites only", which is honest but reads as a refusal where the old no-day line used to be. My view: on a 404 `CLAIM_LIMIT_RANGE_NOT_APPLICABLE`, fall back to the earlier no-day line rather than show refusal words.
- **Off-hour addresses opening the day table:** I agree. A two-hour or off-clock window is a range without an hour. The day table for its day is more honest than the old silent switch to the noon hour or the R313 refusal.

## Residual risk

- The Postgres tests (SR-7a/b, the SR-11 Low 2 line) and SR-7/SR-11 parity have not run. Page correctness against real rows rests on the stubbed shapes.
- `RANGE_MATRIX` D→R is not done because the matrix is not on main. Whoever merges SR-5e must flip Service, Backup and claim-limit.
