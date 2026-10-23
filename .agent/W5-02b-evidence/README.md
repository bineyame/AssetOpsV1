# W5-02b K2b evidence: cold Site Work > Actions and domain Action shell

Recaptured after the F1-F4 layout fix (commit df04dc59, CSS only in `frontend/src/sites/w1f4-changes-work.css`).
Produced by `node tools/w502-cold-work-evidence.mjs var/w502b_cold_work/manifest.json .agent/W5-02b-evidence`
against the manifest's seven APIs (:8971-:8977), each behind a Vite dev server at API port - 3500, headless
Chrome at 1440x1000 and 390x900 (full-page PNG). Queries are the manifest's `modes.<mode>.reads.<name>.query`.
Every measurement and claim is in `w502b-measurements.json` (315 claims, 300 PASS, 15 FAIL). This run adds a
"State badge on one line" claim to the tool (F6).

Caps (`.agent/W5-02-build-spec.md`, "Measurement, capture and deviations"), as 1440/390:
Work page main <= 1400/1800; strip <= 100/150; panel <= 440/650; notice <= 110/160.
Action page main <= 1350/1750; strip <= 100/120; notice <= 100/140.
Heights are rounded `getBoundingClientRect().height` px; `doc` = documentElement scrollWidth/clientWidth;
`table` = `.cold-work-actions .data-table__scroll` scrollWidth/clientWidth; `sticky` = computed `position` of the
first visible row's first cell; "on one line" counts text lines (Range client rects) of each `.cold-work-code`
in a visible row (Action code, Source `Finding {id8}`, Due cell), each `Read full text` summary and each State badge.

| State | Width | File | Key measurements | Result vs caps |
|---|---|---|---|---|
| positive | 1440 | w502b-desktop-positive.png | rows; main 547; strip 39; panel 184; notice 66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| zero | 1440 | w502b-desktop-zero.png | empty; main 625; strip 39; panel 262; notice 66; doc 1440/1440; table -/-; sticky -; rows 0 | PASS |
| historical | 1440 | w502b-desktop-historical.png | rows HISTORICAL; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| worstcase-folded | 1440 | w502b-desktop-worstcase-folded.png | rows; main 757; strip 39; panel 394; notice 66; doc 1440/1440; table 1120/1120; sticky true; rows 4 | FAIL: every State badge is on one line ([2,2,2,2]) |
| worstcase-expanded | 1440 | w502b-desktop-worstcase-expanded.png | rows; main 820; strip 39; panel 457; notice 66; doc 1440/1440; table 1120/1120; sticky true; rows 5 | FAIL: panel <= 440 (457); every State badge is on one line ([2,2,2,2,2]) |
| worstcase-disclosure | 1440 | w502b-desktop-worstcase-disclosure.png | rows; main 779; strip 39; panel 416; notice 66; doc 1440/1440; table 1120/1120; sticky true; rows 4 | FAIL: every State badge is on one line ([2,2,2,2]) |
| worstcase-next | 1440 | w502b-desktop-worstcase-next.png | rows HISTORICAL; main 630; strip 39; panel 183; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| pending | 1440 | w502b-desktop-pending.png | rows PENDING_RECOMPUTE; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| stale | 1440 | w502b-desktop-stale.png | rows STALE_SOURCE; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| unknown | 1440 | w502b-desktop-unknown.png | rows UNKNOWN; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| forbidden-403 | 1440 | w502b-desktop-forbidden-403.png | refused; main 561; strip 39; panel 198; notice 66; doc 1440/1440; table -/-; sticky -; rows 0 | PASS |
| unavailable-503 | 1440 | w502b-desktop-unavailable-503.png | Site frame refusal "Site unavailable"; main 154; doc 1440/1440 | FAIL: refused panel WORK_STORE_UNAVAILABLE ({"panel":null,"refusal":null,"message":null}) |
| action-positive | 1440 | w502b-desktop-action-positive.png | shell loaded/preparing; main 364; strip 42; notice 66; doc 1440/1440 | PASS |
| action-not-found | 1440 | w502b-desktop-action-not-found.png | shell not_found/not-found; main 220; strip -; notice -; doc 1440/1440 | PASS |
| positive | 390 | w502b-narrow-positive.png | rows; main 620; strip 84; panel 199; notice 84; doc 390/390; table 811/318; sticky true; rows 1 | FAIL: every State badge is on one line ([2]) |
| zero | 390 | w502b-narrow-zero.png | empty; main 703; strip 84; panel 282; notice 84; doc 390/390; table -/-; sticky -; rows 0 | PASS |
| historical | 390 | w502b-narrow-historical.png | rows HISTORICAL; main 704; strip 84; panel 199; notice 66/84; doc 390/390; table 811/318; sticky true; rows 1 | FAIL: every State badge is on one line ([2]) |
| worstcase-folded | 390 | w502b-narrow-worstcase-folded.png | rows; main 886; strip 84; panel 465; notice 84; doc 390/390; table 811/318; sticky true; rows 4 | FAIL: every State badge is on one line ([2,2,2,2]) |
| worstcase-expanded | 390 | w502b-narrow-worstcase-expanded.png | rows; main 967; strip 84; panel 545; notice 84; doc 390/390; table 811/318; sticky true; rows 5 | FAIL: every State badge is on one line ([2,2,2,2,2]) |
| worstcase-disclosure | 390 | w502b-narrow-worstcase-disclosure.png | rows; main 978; strip 84; panel 556; notice 84; doc 390/390; table 811/318; sticky true; rows 4 | FAIL: every State badge is on one line ([2,2,2,2]) |
| worstcase-next | 390 | w502b-narrow-worstcase-next.png | rows HISTORICAL; main 704; strip 84; panel 199; notice 66/84; doc 390/390; table 811/318; sticky true; rows 1 | FAIL: every State badge is on one line ([2]) |
| pending | 390 | w502b-narrow-pending.png | rows PENDING_RECOMPUTE; main 722; strip 84; panel 199; notice 84/84; doc 390/390; table 809/318; sticky true; rows 1 | FAIL: every State badge is on one line ([2]) |
| stale | 390 | w502b-narrow-stale.png | rows STALE_SOURCE; main 722; strip 84; panel 199; notice 84/84; doc 390/390; table 810/318; sticky true; rows 1 | FAIL: every State badge is on one line ([2]) |
| unknown | 390 | w502b-narrow-unknown.png | rows UNKNOWN; main 722; strip 84; panel 199; notice 84/84; doc 390/390; table 805/318; sticky true; rows 1 | FAIL: every State badge is on one line ([2]) |
| forbidden-403 | 390 | w502b-narrow-forbidden-403.png | refused; main 619; strip 84; panel 198; notice 84; doc 390/390; table -/-; sticky -; rows 0 | PASS |
| unavailable-503 | 390 | w502b-narrow-unavailable-503.png | Site frame refusal "Site unavailable"; main 172; doc 390/390 | FAIL: refused panel WORK_STORE_UNAVAILABLE ({"panel":null,"refusal":null,"message":null}) |
| action-positive | 390 | w502b-narrow-action-positive.png | shell loaded/preparing; main 465; strip 65; notice 84; doc 390/390 | PASS |
| action-not-found | 390 | w502b-narrow-action-not-found.png | shell not_found/not-found; main 252; strip -; notice -; doc 390/390 | PASS |

`worstcase-next` reads HISTORICAL because the Next link pins the page-one response `known_at` in the URL (U3);
that is the specified behaviour, not a finding.

## Findings (frontend untouched by this capture)

1. **F1 - worst-case Actions panel over cap: STILL FAILING at 1440 expanded only.** Panel at 1440 is
   folded 394, expanded **457** (cap 440), one disclosure open 416; at 390 folded 465, expanded 545, one disclosure
   open 556 (cap 650, all pass). Page main is within cap everywhere (1440: 757/820/779; 390: 886/967/978).
   Before the fix: 529/622/559 at 1440 and 1148/1399/1740 at 390.
2. **F2 - 1440 table scrolled sideways: RESOLVED.** The scroller is 1120/1120 in every 1440 row state (was 2236/1120)
   and all six columns are visible. At 390 the table scrolls inside its panel (805-811 wide in a 318 px scroller)
   with the first column sticky. There is no document overflow anywhere.
3. **F3 - Due cell wrapped at 390: RESOLVED.** Action code, Source and Due are one line in every row at both widths
   (`[1,1,1]`; was `[1,1,2]` / `[1,1,4]`).
4. **F4 - `Read full text` summary wrapped per character at 390: RESOLVED.** Every summary is one line (was 4 and 8
   lines). Previews now break at word boundaries.
5. **F5 - 503 cold-work refusal panel not reachable with this producer: STILL OPEN, see question Q17 in
   `.agent/W5-02b-questions.md`.** The :8977 API has no database, so the Site read fails first and the page renders
   `Site unavailable / The site store could not be read, so nothing is known about whether the site is configured.`
   (main 154/172 px, no overflow, no rows, no mock zero). `[data-cold-work-state-panel="refused"]` with
   `WORK_STORE_UNAVAILABLE` and Retry never mounts, so the browser capture of the cold 503 panel is unproven.
   403 is proven: `SITE_SCOPE_FORBIDDEN`, message `No access to Site 'COLD-LAB-001'.`, Retry visible, panel 198 px.
6. **F6 - State badge `Open` wraps to two lines (`Ope` / `n`): NEW, detected by the badge check added in this run.**
   It is 2 lines in every 390 row state and in the 1440 worst-case states (`[2,2,2,2]`). In the 1440 one-row states
   it is 1 line. The badge is not clipped (scrollWidth <= clientWidth), but the status word is split. See
   `w502b-desktop-worstcase-expanded.png` and `w502b-narrow-positive.png`. The first capture did not measure this;
   its 390 screenshots appear to show the same split.

All other claims pass: strips 39/84 and notices 66/84 are within caps; positive, historical, pending, stale,
unknown and next pages each show 1 row with the expected CURRENT/HISTORICAL/PENDING_RECOMPUTE/STALE_SOURCE/UNKNOWN
notice; zero shows the empty panel; `Show all 5 Actions` expands to 5 rows; the domain Action shell is
`loaded/preparing` for ACT-000001 (main 364/465, strip 42/65, notice 66/84) and `not_found` for an unknown ID
(main 220/252).
