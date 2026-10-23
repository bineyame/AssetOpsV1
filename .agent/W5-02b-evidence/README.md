# W5-02b K2b evidence: cold Site Work > Actions and domain Action shell

Recapture after the Architect K2 rulings 20, 21 and 23 (`.agent/W5-02b-K2-rulings.md`; ruling 22 needs no change).
Producer at 1d7e2b39 (`tools/w502_cold_work_walkthrough.py prepare`, all five DB modes; `serve`; `attest`: ATTEST OK).
Frontend served live from the worktree at 4cac402a (Vite, one per API). Capture: `node tools/w502-cold-work-evidence.mjs
var/w502b_cold_work/manifest.json .agent/W5-02b-evidence` against the manifest's seven APIs (:8971-:8977), each behind
a Vite dev server at API port - 3500, headless Chrome at 1440x1000 and 390x900 (full-page PNG). Every measurement and
claim is in `w502b-measurements.json`: **463 claims, 461 PASS, 2 FAIL**. (A first run in the same session timed
out on cold Vite compiles at 1440 and exposed two issues fixed in 4cac402a: an inline summary wrap and a capture
selector. This README and the JSON are the clean rerun.)

Ruled caps (K2 ruling 2), as 1440/390: Work page main <= 1600/2000; Actions panel <= 650/850; strip <= 100/150;
notice <= 110/160; `document.scrollWidth <= clientWidth + 1`; per-cell containment; preview at most two lines; no
horizontal clip of an opened `Read full text`. Action page main <= 1350/1750; strip <= 100/120; notice <= 100/140.

Columns: heights are rounded `getBoundingClientRect().height` px. `notice` is the context notice, or
currentness/context when a currentness notice shows. `doc` = documentElement scrollWidth/clientWidth (1425 at 1440
means a vertical scrollbar). `table` = table scroller scrollWidth/clientWidth (at 390 the table scrolls inside its
panel, first column sticky). `contain` = every cell fits, children inside, clamp fits, and every open disclosure body
is inside and fits. `preview<=` = maximum preview line count (0 with every disclosure open, because ruling 20 removes
the preview while it is open). `open` = open title disclosures. Result = that state's claims.

Producer manifest (revision 1d7e2b39): positive: positive CURRENT/1, zero CURRENT/0, historical HISTORICAL/1, blocked None, INC links COLD_START_FAILURE+COLD_EXCURSION; worstcase: worstcase CURRENT/6, blocked None, INC links COLD_START_FAILURE+COLD_EXCURSION; pending: pending PENDING_RECOMPUTE/1, blocked None, INC links COLD_START_FAILURE+COLD_EXCURSION; stale: stale STALE_SOURCE/1, blocked None, INC links COLD_START_FAILURE+COLD_EXCURSION; unknown: unknown UNKNOWN/1, blocked None, INC links COLD_START_FAILURE. forbidden :8976 HTTP 403 SITE_SCOPE_FORBIDDEN; unavailable :8977 Site
read HTTP 200, domain-work HTTP 503 WORK_STORE_UNAVAILABLE. `fixture.incident.occurred_at` = D+16h11m in every mode.

**UNKNOWN one-link limit (ruling 21):** the `unknown` mode is not blocked. Its no-probe replay selects no
COLD_EXCURSION Finding revision, so its INC links only the returned COLD_START_FAILURE Finding. No synthetic excursion
is seeded and no unselected revision is linked. The manifest records `modes.unknown.fixture.incident.limit` =
"UNKNOWN one-link limit: the no-probe replay selects no COLD_EXCURSION Finding revision, so the INC links only the returned COLD_START_FAILURE Finding (ruling 21; no synthetic excursion)". Every other mode links both selected Findings (ruling 4), and the positive cold Incidents capture shows both
(`Finding 1b0f5635 · Finding 82ba2f4c`).

| State | Width | File | Measurements | Result vs ruled caps |
|---|---|---|---|---|
| positive | 1440 | w502b-desktop-positive.png | rows; main 568; strip 39; panel 184; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (17) |
| zero | 1440 | w502b-desktop-zero.png | empty; main 646; strip 39; panel 262; notice 42; doc 1440/1440; contain -; preview<= -; rows 0 | PASS (7) |
| historical | 1440 | w502b-desktop-historical.png | rows HISTORICAL; main 628; strip 39; panel 184; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| worstcase-folded | 1440 | w502b-desktop-worstcase-folded.png | rows; main 840; strip 39; panel 457; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 2; rows 4 | PASS (16) |
| worstcase-expanded | 1440 | w502b-desktop-worstcase-expanded.png | rows; main 919; strip 39; panel 535; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 2; rows 5 | PASS (14) |
| worstcase-expanded-open | 1440 | w502b-desktop-worstcase-expanded-open.png | rows; main 1203; strip 39; panel 819; notice 42; doc 1425/1425; table 1105/1105; contain yes; preview<= 0; rows 5; open 5 | FAIL: panel <= 650 {"panel":819,"tableScrollWidth":1105,"tableClientWidth":1105} |
| worstcase-disclosure | 1440 | w502b-desktop-worstcase-disclosure.png | rows; main 862; strip 39; panel 478; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 2; rows 4; open 1 | PASS (16) |
| worstcase-next | 1440 | w502b-desktop-worstcase-next.png | rows HISTORICAL; main 627; strip 39; panel 183; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| window-apply | 1440 | w502b-desktop-window-apply.png | rows HISTORICAL; main 901; strip 39; panel 457; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 2; rows 4 | PASS (12) |
| window-invalid | 1440 | w502b-desktop-window-invalid.png | rows; main 592; strip 39; panel 184; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (9) |
| cold-incidents | 1440 | w502b-desktop-cold-incidents.png | forms ["cold-window"]; W4 form no; main 597; panel 212; doc 1440/1440; subtabs keep from,to,known_at | PASS (6) |
| cold-maintenance | 1440 | w502b-desktop-cold-maintenance.png | forms ["cold-window"]; W4 form no; main 597; panel 212; doc 1440/1440; subtabs keep from,to,known_at | PASS (6) |
| pending | 1440 | w502b-desktop-pending.png | rows PENDING_RECOMPUTE; main 628; strip 39; panel 184; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| stale | 1440 | w502b-desktop-stale.png | rows STALE_SOURCE; main 628; strip 39; panel 184; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| unknown | 1440 | w502b-desktop-unknown.png | rows UNKNOWN; main 628; strip 39; panel 184; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| forbidden-403 | 1440 | w502b-desktop-forbidden-403.png | refused; main 582; strip 39; panel 198; notice 42; doc 1440/1440; contain -; preview<= -; rows 0 | PASS (9) |
| cold-work-503 | 1440 | w502b-desktop-cold-work-503.png | refused WORK_STORE_UNAVAILABLE; main 582; strip 39; panel 198; notice 42; doc 1440/1440; rows 0 | PASS (11) |
| action-positive | 1440 | w502b-desktop-action-positive.png | preparing; main 340; strip 42; panel 23; notice 42; doc 1440/1440; contain -; preview<= - | PASS (6) |
| action-not-found | 1440 | w502b-desktop-action-not-found.png | not-found; main 220; strip -; panel 23; notice -; doc 1440/1440; contain -; preview<= - | PASS (4) |
| positive | 390 | w502b-narrow-positive.png | rows; main 745; strip 84; panel 199; notice 60; doc 390/390; table 818/318; contain yes; preview<= 0; rows 1 | PASS (18) |
| zero | 390 | w502b-narrow-zero.png | empty; main 828; strip 84; panel 282; notice 60; doc 390/390; contain -; preview<= -; rows 0 | PASS (7) |
| historical | 390 | w502b-narrow-historical.png | rows HISTORICAL; main 805; strip 84; panel 199; notice 42/60; doc 390/390; table 818/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| worstcase-folded | 390 | w502b-narrow-worstcase-folded.png | rows; main 1002; strip 84; panel 457; notice 60; doc 390/390; table 822/318; contain yes; preview<= 2; rows 4 | PASS (17) |
| worstcase-expanded | 390 | w502b-narrow-worstcase-expanded.png | rows; main 1081; strip 84; panel 535; notice 60; doc 390/390; table 822/318; contain yes; preview<= 2; rows 5 | PASS (15) |
| worstcase-expanded-open | 390 | w502b-narrow-worstcase-expanded-open.png | rows; main 1629; strip 84; panel 1083; notice 60; doc 390/390; table 822/318; contain yes; preview<= 0; rows 5; open 5 | FAIL: panel <= 850 {"panel":1083,"tableScrollWidth":822,"tableClientWidth":318} |
| worstcase-disclosure | 390 | w502b-narrow-worstcase-disclosure.png | rows; main 1059; strip 84; panel 513; notice 60; doc 390/390; table 822/318; contain yes; preview<= 2; rows 4; open 1 | PASS (17) |
| worstcase-next | 390 | w502b-narrow-worstcase-next.png | rows HISTORICAL; main 804; strip 84; panel 199; notice 42/60; doc 390/390; table 822/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| window-apply | 390 | w502b-narrow-window-apply.png | rows HISTORICAL; main 1062; strip 84; panel 457; notice 42/60; doc 390/390; table 822/318; contain yes; preview<= 2; rows 4 | PASS (12) |
| window-invalid | 390 | w502b-narrow-window-invalid.png | rows; main 769; strip 84; panel 199; notice 60; doc 390/390; table 818/318; contain yes; preview<= 0; rows 1 | PASS (9) |
| cold-incidents | 390 | w502b-narrow-cold-incidents.png | forms ["cold-window"]; W4 form no; main 785; panel 201; doc 390/390; subtabs keep from,to,known_at | PASS (6) |
| cold-maintenance | 390 | w502b-narrow-cold-maintenance.png | forms ["cold-window"]; W4 form no; main 800; panel 216; doc 390/390; subtabs keep from,to,known_at | PASS (6) |
| pending | 390 | w502b-narrow-pending.png | rows PENDING_RECOMPUTE; main 823; strip 84; panel 199; notice 60/60; doc 390/390; table 819/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| stale | 390 | w502b-narrow-stale.png | rows STALE_SOURCE; main 823; strip 84; panel 199; notice 60/60; doc 390/390; table 821/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| unknown | 390 | w502b-narrow-unknown.png | rows UNKNOWN; main 823; strip 84; panel 199; notice 60/60; doc 390/390; table 817/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| forbidden-403 | 390 | w502b-narrow-forbidden-403.png | refused; main 743; strip 84; panel 198; notice 60; doc 390/390; contain -; preview<= -; rows 0 | PASS (9) |
| cold-work-503 | 390 | w502b-narrow-cold-work-503.png | refused WORK_STORE_UNAVAILABLE; main 743; strip 84; panel 198; notice 60; doc 390/390; rows 0 | PASS (11) |
| action-positive | 390 | w502b-narrow-action-positive.png | preparing; main 455; strip 65; panel 23; notice 60; doc 390/390; contain -; preview<= - | PASS (6) |
| action-not-found | 390 | w502b-narrow-action-not-found.png | not-found; main 266; strip -; panel 23; notice -; doc 390/390; contain -; preview<= - | PASS (4) |
| unavailable-503 (legacy, separate Site refusal) | 1440 | w502b-desktop-unavailable-503.png | Not recaptured: kept from the 75abbaf3 capture. Site frame refusal `Site unavailable` | Not cold-work proof (K2 ruling 3); superseded by `cold-work-503` |
| unavailable-503 (legacy, separate Site refusal) | 390 | w502b-narrow-unavailable-503.png | Not recaptured: kept from the 75abbaf3 capture | Not cold-work proof (K2 ruling 3); superseded by `cold-work-503` |

Seven further claims PASS. Five are manifest claims: positive, worstcase, pending and stale are not blocked and their
INC links COLD_START_FAILURE+COLD_EXCURSION; unknown is not blocked, has one COLD_START_FAILURE link and records its
limit. The other two are `worstcase: Next page link present` at 1440 and 390. `worstcase-next` and `window-apply` read
HISTORICAL because the page-one `known_at` is pinned in the URL (U3, ruling 1); that is specified behaviour.

`cold-incidents` / `cold-maintenance` (ruling 23) use the positive window with an explicit `known_at` (K3). Each has
exactly one visible date form: the page-local `Window` control after the Work subtabs, showing the selected dates. There
is no W4 in-panel form, and the page URL and all three Work subtab hrefs keep `from,to,known_at`. The content is the
existing W4 Incidents/Maintenance list (K3 is not built). The subtab counts there read `(—)`, as before this change.

## Findings

1. **F1 - worst-case Actions panel with every disclosure open: still over the ruled caps after ruling 20. Returned to
   the Architect; not clipped and not exempted.**

   | Width | Folded | Expanded | One disclosure open | Expanded, all open (before ruling 20 -> now) | Page main, all open |
   |---|---|---|---|---|---|
   | 1440 | 457 | 535 | 478 | 907 -> **819** (cap 650, 169 over) | 1291 -> 1203 (cap 1600, PASS) |
   | 390 | 457 | 535 | 513 | 1259 -> **1083** (cap 850, 233 over) | 1805 -> 1629 (cap 2000, PASS) |

   With the preview removed while open, each full value appears once, in the body only. At 1440 each row is now 137 px
   (154 before). The 160-code-point title wraps to three lines in the 340 px Action column under its one-line `Read
   full text`, and the 160-code-point owner wraps to four or five lines in the 240 px Owner column. Containment holds:
   no horizontal clip, doc 1425/1425 and 390/390, every summary on one line. Every other state is inside every cap.
   The recapture also found the inline `Finding version` summary splitting over two lines at 1440 with every
   disclosure open (the auto table narrowed Source); 4cac402a keeps it on one line (`white-space: nowrap`).
2. **F2 - 1440 table scrolled sideways: RESOLVED** (scroller 1120/1120, all-open 1105/1105; no document overflow).
3. **F3 - Due cell wrapped at 390: RESOLVED** (code, Source and Due on one line in every row).
4. **F4 - `Read full text` summary wrapped at 390: RESOLVED** (every summary on one line at both widths).
5. **F5 - 503 cold-work refusal panel: RESOLVED by `cold-work-503`** (healthy Site read, panel `refused`
   WORK_STORE_UNAVAILABLE with the server message and Retry, no rows, no mock zero).
6. **F6 - State badge `Open` split over two lines: RESOLVED** (one line everywhere).
7. **F7 - producer `unknown` mode `blocked`: RESOLVED by ruling 21** (no mode is blocked; the UNKNOWN one-link limit is
   stated above and in the manifest).

Window control (rulings 1, 22, 23): placement and alignment claims pass at both widths on Actions. `window-apply` keeps
`known_at`, drops the cursor and reads page one. `window-invalid` shows `The window may span at most 31 days.` and
does not navigate. Cold Incidents and Maintenance show only this control. Domain Action shell: `loaded/preparing` for
the positive Action and `not_found` for an unknown ID.

## Re-evaluation under K2 ruling 24 (no browser recapture)

Ruling 24 (FINAL) removes the Actions-panel height cap for the five-row state with every disclosure open. The page-main caps, containment and no-overflow claims still apply. `tools/w502-cold-work-evidence.mjs` no longer emits the panel-cap claim for `worstcase-expanded-open`. The tool has no replay mode, so the stored `w502b-measurements.json` from capture `83c3e1c3` was re-evaluated with a one-off node filter instead. Of its 463 claims, only two failed: `desktop worstcase-expanded-open: panel <= 650` and `narrow worstcase-expanded-open: panel <= 850`. Both are exempt under ruling 24. That leaves **461 claims, 0 failing**. The retained all-open claims pass: no document overflow at both widths, page main 1203 <= 1600 and 1629 <= 2000, and cell containment. The JSON file itself is unchanged, so it still shows `failed: 2` from the capture run. F1 is closed by ruling 24.
