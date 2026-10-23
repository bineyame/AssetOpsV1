# W5-02b part 1 evidence: cold Site Work > Actions (K2a/K2b) and domain Action shell

Produced by `node tools/w502-cold-work-evidence.mjs var/w502b_cold_work/manifest.json .agent/W5-02b-evidence`
against the manifest's seven APIs (:8971-:8977), each behind a Vite dev server at API port - 3500, headless
Chrome at 1440x1000 and 390x900 (full-page PNG). Queries are the manifest's `modes.<mode>.reads.<name>.query`.
Every measurement and claim is in `w502b-measurements.json` (297 claims, 275 PASS, 22 FAIL).

Caps (`.agent/W5-02-build-spec.md`, "Measurement, capture and deviations"), as 1440/390:
Work page main <= 1400/1800; strip <= 100/150; panel <= 440/650; notice <= 110/160.
Action page main <= 1350/1750; strip <= 100/120; notice <= 100/140.
Heights are rounded `getBoundingClientRect().height` px; `doc` = documentElement scrollWidth/clientWidth;
`table` = `.cold-work-actions .data-table__scroll` scrollWidth/clientWidth; `sticky` = computed `position` of the
first visible row's first cell; "code on one line" counts text lines (Range client rects) of each `.cold-work-code`
in a visible row: Action code, Source `Finding {id8}`, Due cell.

| State | Width | File | Key measurements | Result vs caps |
|---|---|---|---|---|
| positive | 1440 | w502b-desktop-positive.png | rows; main 547; strip 39; panel 184; notice 66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| zero | 1440 | w502b-desktop-zero.png | empty; main 625; strip 39; panel 262; notice 66; doc 1440/1440; table -/-; sticky -; rows 0 | PASS |
| historical | 1440 | w502b-desktop-historical.png | rows HISTORICAL; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| worstcase-folded | 1440 | w502b-desktop-worstcase-folded.png | rows; main 892; strip 39; panel 529; notice 66; doc 1440/1440; table 2236/1120; sticky true; rows 4 | FAIL: panel <= 440 (529) |
| worstcase-expanded | 1440 | w502b-desktop-worstcase-expanded.png | rows; main 985; strip 39; panel 622; notice 66; doc 1425/1425; table 2236/1105; sticky true; rows 5 | FAIL: panel <= 440 (622) |
| worstcase-disclosure | 1440 | w502b-desktop-worstcase-disclosure.png | rows; main 922; strip 39; panel 559; notice 66; doc 1440/1440; table 2270/1120; sticky true; rows 4 | FAIL: panel <= 440 (559) |
| worstcase-next | 1440 | w502b-desktop-worstcase-next.png | rows HISTORICAL; main 630; strip 39; panel 183; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| pending | 1440 | w502b-desktop-pending.png | rows PENDING_RECOMPUTE; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| stale | 1440 | w502b-desktop-stale.png | rows STALE_SOURCE; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| unknown | 1440 | w502b-desktop-unknown.png | rows UNKNOWN; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| forbidden-403 | 1440 | w502b-desktop-forbidden-403.png | refused; main 561; strip 39; panel 198; notice 66; doc 1440/1440; table -/-; sticky -; rows 0 | PASS |
| unavailable-503 | 1440 | w502b-desktop-unavailable-503.png | Site frame refusal "Site unavailable"; main 154; doc 1440/1440 | FAIL: refused panel WORK_STORE_UNAVAILABLE ({"panel":null,"refusal":null,"message":null}) |
| action-positive | 1440 | w502b-desktop-action-positive.png | shell loaded/preparing; main 364; strip 42; notice 66; doc 1440/1440 | PASS |
| action-not-found | 1440 | w502b-desktop-action-not-found.png | shell not_found/not-found; main 220; strip -; notice -; doc 1440/1440 | PASS |
| positive | 390 | w502b-narrow-positive.png | rows; main 656; strip 84; panel 234; notice 84; doc 390/390; table 467/318; sticky true; rows 1 | FAIL: every row's code is on one line ([[1,1,2]]) |
| zero | 390 | w502b-narrow-zero.png | empty; main 703; strip 84; panel 282; notice 84; doc 390/390; table -/-; sticky -; rows 0 | PASS |
| historical | 390 | w502b-narrow-historical.png | rows HISTORICAL; main 739; strip 84; panel 234; notice 66/84; doc 390/390; table 467/318; sticky true; rows 1 | FAIL: every row's code is on one line ([[1,1,2]]) |
| worstcase-folded | 390 | w502b-narrow-worstcase-folded.png | rows; main 1569; strip 84; panel 1148; notice 84; doc 390/390; table 476/318; sticky true; rows 4 | FAIL: panel <= 650 (1148); every row's code is on one line ([[1,1,4],[1,1,4],[1,1,2],[1,1,4]]); every 'Read full text' summary is on one line ([4,1,8,4,1,8,4,1,8,4,1,8]) |
| worstcase-expanded | 390 | w502b-narrow-worstcase-expanded.png | rows; main 1820; strip 84; panel 1399; notice 84; doc 390/390; table 476/318; sticky true; rows 5 | FAIL: page main <= 1800 (1820); panel <= 650 (1399); every row's code is on one line ([[1,1,4],[1,1,4],[1,1,2],[1,1,4],[1,1,2]]); every 'Read full text' summary is on one line ([4,1,8,4,1,8,4,1,8,4,1,8,4,1,8]) |
| worstcase-disclosure | 390 | w502b-narrow-worstcase-disclosure.png | rows; main 2161; strip 84; panel 1740; notice 84; doc 390/390; table 476/318; sticky true; rows 4 | FAIL: page main <= 1800 (2161); panel <= 650 (1740); every row's code is on one line ([[1,1,4],[1,1,4],[1,1,2],[1,1,4]]); every 'Read full text' summary is on one line ([4,1,8,4,1,8,4,1,8,4,1,8]) |
| worstcase-next | 390 | w502b-narrow-worstcase-next.png | rows HISTORICAL; main 739; strip 84; panel 234; notice 66/84; doc 390/390; table 467/318; sticky true; rows 1 | FAIL: every row's code is on one line ([[1,1,2]]) |
| pending | 390 | w502b-narrow-pending.png | rows PENDING_RECOMPUTE; main 758; strip 84; panel 234; notice 84/84; doc 390/390; table 465/318; sticky true; rows 1 | FAIL: every row's code is on one line ([[1,1,2]]) |
| stale | 390 | w502b-narrow-stale.png | rows STALE_SOURCE; main 758; strip 84; panel 234; notice 84/84; doc 390/390; table 467/318; sticky true; rows 1 | FAIL: every row's code is on one line ([[1,1,2]]) |
| unknown | 390 | w502b-narrow-unknown.png | rows UNKNOWN; main 758; strip 84; panel 234; notice 84/84; doc 390/390; table 462/318; sticky true; rows 1 | FAIL: every row's code is on one line ([[1,1,2]]) |
| forbidden-403 | 390 | w502b-narrow-forbidden-403.png | refused; main 619; strip 84; panel 198; notice 84; doc 390/390; table -/-; sticky -; rows 0 | PASS |
| unavailable-503 | 390 | w502b-narrow-unavailable-503.png | Site frame refusal "Site unavailable"; main 172; doc 390/390 | FAIL: refused panel WORK_STORE_UNAVAILABLE ({"panel":null,"refusal":null,"message":null}) |
| action-positive | 390 | w502b-narrow-action-positive.png | shell loaded/preparing; main 465; strip 65; notice 84; doc 390/390 | PASS |
| action-not-found | 390 | w502b-narrow-action-not-found.png | shell not_found/not-found; main 252; strip -; notice -; doc 390/390 | PASS |

`worstcase-next` reads HISTORICAL because the Next link pins the page-one response `known_at` in the URL (U3);
that is the specified behaviour, not a finding.

## Findings (not fixed; frontend untouched)

1. **F1 - worst-case Actions panel over cap at both widths.** Panel 529/622/559 px at 1440 (folded/expanded/one
   disclosure open; cap 440) and 1148/1399/1740 px at 390 (cap 650). Page main at 390 also over cap when expanded
   (1820 > 1800) and with one disclosure open (2161 > 1800); folded 390 is 1569 (within). Driver: each long row
   carries a full-width `Read full text` disclosure box under the clamped title and a second one under Owner, and
   at 390 the narrow columns make each row ~250 px tall.
2. **F2 - 1440 table scrolls sideways for the long-title rows.** Scroller 2236/1120 (2270/1120 with a disclosure
   open): the 160-code-point fixture title ends in an unbroken `xxxx...` run, the Action cell does not break it
   (no `overflow-wrap:anywhere`/`word-break`), so the title stays one ~860 px line, and Owner/Due/State/Success
   criterion columns sit off-screen at 1440 (see `w502b-desktop-worstcase-folded.png`). Document itself does not
   overflow (1440/1440). Spec expects long text to wrap within its cell.
3. **F3 - Due cell wraps at 390 (IDs/codes one-line rule).** The Due `td.cold-work-code` breaks to 2 lines for
   `Not set` (every 1-row state at 390) and 4 lines for ISO dates such as `2026-10-24` (worst case) - the narrow
   column squeezes it. Action code and Source code are one line everywhere (line counts `[1,1,N]`).
4. **F4 - `Read full text` summary wraps character-by-character at 390.** Summary text lines measured 4 (title
   disclosure) and 8 (owner disclosure) per row, e.g. `R/e/a/d/fu/ll/te/xt` in `w502b-narrow-worstcase-folded.png`.
   The owner text preview `Mainten ance...` also breaks mid-word.
5. **F5 - 503 cold-work refusal panel not reachable with this producer.** The :8977 API has no database, so the
   Site detail read fails first and the Site frame renders `Site unavailable / The site store could not be read,
   so nothing is known about whether the site is configured.` (main 154/172 px, no overflow, no rows, no mock zero).
   `[data-cold-work-state-panel="refused"]` with `WORK_STORE_UNAVAILABLE` and `Retry` never mounts, so the cold
   503 panel is unproven in the browser; it needs a producer where only the cold work read answers 503.
   (403 is proven: `SITE_SCOPE_FORBIDDEN`, message `No access to Site 'COLD-LAB-001'.`, Retry visible, strip count
   `—`, panel 198 px.)

All other states pass: no document horizontal overflow in any capture; first column sticky in every row state;
table scrolls inside its panel at 390 (scrollWidth 462-476 vs clientWidth 318); State badges unclipped;
strips 39/84, notices 66/84 within caps; positive/historical/pending/stale/unknown/next pages 1 row each,
CURRENT/HISTORICAL/PENDING_RECOMPUTE/STALE_SOURCE/UNKNOWN notices as expected; zero shows the empty panel
(`No actions at this site` + body); `Show all 5 Actions` visible on the folded page and expands to 5 rows; domain
Action shell `loaded/preparing` for ACT-000001 (main 364/465, strip 42/65, notice 66/84) and `not_found` for an
unknown ID (main 220/252).
