# W5-02b K2b evidence: cold Site Work > Actions and domain Action shell

This is the third capture. It was taken after the badge and summary fix at commit 63d35dd9: the State cell no
longer wraps, the disclosure margin is 0 and the summary line-height is 1.2. The capture before it followed the
F1-F4 wrap fix at df04dc59.
Produced by `node tools/w502-cold-work-evidence.mjs var/w502b_cold_work/manifest.json .agent/W5-02b-evidence`
against the manifest's seven APIs (:8971-:8977), each behind a Vite dev server at API port - 3500, headless
Chrome at 1440x1000 and 390x900 (full-page PNG). Queries are the manifest's `modes.<mode>.reads.<name>.query`.
Every measurement and claim is in `w502b-measurements.json` (315 claims, 312 PASS, 3 FAIL).

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
| worstcase-folded | 1440 | w502b-desktop-worstcase-folded.png | rows; main 764; strip 39; panel 401; notice 66; doc 1440/1440; table 1125/1120; sticky true; rows 4 | PASS |
| worstcase-expanded | 1440 | w502b-desktop-worstcase-expanded.png | rows; main 825; strip 39; panel 462; notice 66; doc 1440/1440; table 1125/1120; sticky true; rows 5 | FAIL: panel <= 440 (462) |
| worstcase-disclosure | 1440 | w502b-desktop-worstcase-disclosure.png | rows; main 786; strip 39; panel 423; notice 66; doc 1440/1440; table 1125/1120; sticky true; rows 4 | PASS |
| worstcase-next | 1440 | w502b-desktop-worstcase-next.png | rows HISTORICAL; main 630; strip 39; panel 183; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| pending | 1440 | w502b-desktop-pending.png | rows PENDING_RECOMPUTE; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| stale | 1440 | w502b-desktop-stale.png | rows STALE_SOURCE; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| unknown | 1440 | w502b-desktop-unknown.png | rows UNKNOWN; main 631; strip 39; panel 184; notice 66/66; doc 1440/1440; table 1120/1120; sticky true; rows 1 | PASS |
| forbidden-403 | 1440 | w502b-desktop-forbidden-403.png | refused; main 561; strip 39; panel 198; notice 66; doc 1440/1440; table -/-; sticky -; rows 0 | PASS |
| unavailable-503 | 1440 | w502b-desktop-unavailable-503.png | Site frame refusal "Site unavailable"; main 154; doc 1440/1440 | FAIL: refused panel WORK_STORE_UNAVAILABLE ({"panel":null,"refusal":null,"message":null}) |
| action-positive | 1440 | w502b-desktop-action-positive.png | shell loaded/preparing; main 364; strip 42; notice 66; doc 1440/1440 | PASS |
| action-not-found | 1440 | w502b-desktop-action-not-found.png | shell not_found/not-found; main 220; strip -; notice -; doc 1440/1440 | PASS |
| positive | 390 | w502b-narrow-positive.png | rows; main 620; strip 84; panel 199; notice 84; doc 390/390; table 821/318; sticky true; rows 1 | PASS |
| zero | 390 | w502b-narrow-zero.png | empty; main 703; strip 84; panel 282; notice 84; doc 390/390; table -/-; sticky -; rows 0 | PASS |
| historical | 390 | w502b-narrow-historical.png | rows HISTORICAL; main 704; strip 84; panel 199; notice 66/84; doc 390/390; table 821/318; sticky true; rows 1 | PASS |
| worstcase-folded | 390 | w502b-narrow-worstcase-folded.png | rows; main 878; strip 84; panel 457; notice 84; doc 390/390; table 821/318; sticky true; rows 4 | PASS |
| worstcase-expanded | 390 | w502b-narrow-worstcase-expanded.png | rows; main 957; strip 84; panel 535; notice 84; doc 390/390; table 821/318; sticky true; rows 5 | PASS |
| worstcase-disclosure | 390 | w502b-narrow-worstcase-disclosure.png | rows; main 970; strip 84; panel 548; notice 84; doc 390/390; table 821/318; sticky true; rows 4 | PASS |
| worstcase-next | 390 | w502b-narrow-worstcase-next.png | rows HISTORICAL; main 704; strip 84; panel 199; notice 66/84; doc 390/390; table 821/318; sticky true; rows 1 | PASS |
| pending | 390 | w502b-narrow-pending.png | rows PENDING_RECOMPUTE; main 722; strip 84; panel 199; notice 84/84; doc 390/390; table 819/318; sticky true; rows 1 | PASS |
| stale | 390 | w502b-narrow-stale.png | rows STALE_SOURCE; main 722; strip 84; panel 199; notice 84/84; doc 390/390; table 820/318; sticky true; rows 1 | PASS |
| unknown | 390 | w502b-narrow-unknown.png | rows UNKNOWN; main 722; strip 84; panel 199; notice 84/84; doc 390/390; table 815/318; sticky true; rows 1 | PASS |
| forbidden-403 | 390 | w502b-narrow-forbidden-403.png | refused; main 619; strip 84; panel 198; notice 84; doc 390/390; table -/-; sticky -; rows 0 | PASS |
| unavailable-503 | 390 | w502b-narrow-unavailable-503.png | Site frame refusal "Site unavailable"; main 172; doc 390/390 | FAIL: refused panel WORK_STORE_UNAVAILABLE ({"panel":null,"refusal":null,"message":null}) |
| action-positive | 390 | w502b-narrow-action-positive.png | shell loaded/preparing; main 465; strip 65; notice 84; doc 390/390 | PASS |
| action-not-found | 390 | w502b-narrow-action-not-found.png | shell not_found/not-found; main 252; strip -; notice -; doc 390/390 | PASS |

`worstcase-next` reads HISTORICAL because the Next link pins the page-one response `known_at` in the URL (U3);
that is the specified behaviour, not a finding.

## Findings (frontend untouched by this capture)

1. **F1 - worst-case Actions panel over cap: STILL FAILING at 1440 expanded only, now 462 (cap 440).**
   The numbers are below; the second capture's are in brackets.

   | Width | Folded | Expanded | One disclosure open | Page main (folded / expanded / disclosure) |
   |---|---|---|---|---|
   | 1440 | 401 [394] | **462** [457] | 423 [416] | 764 / 825 / 786 |
   | 390 | 457 [465] | 535 [545] | 548 [556] | 878 / 957 / 970 |

   The 390 panels pass the 650 cap. Page main is within cap everywhere. At 1440 the rows got shorter, but the
   panel got taller. The nowrap State cell widened the worst-case table to 1125 px inside a 1120 px scroller. That
   5 px overflow adds a horizontal scrollbar of about 17 px inside the panel (see
   `w502b-desktop-worstcase-expanded.png`), which more than cancels the saving.
2. **F2 - 1440 table scrolled sideways: RESOLVED for the content, 5 px residual.** All six columns are visible at
   1440. The worst-case scroller is 1125/1120, where the first capture measured 2236/1120. This is the 5 px that
   brings back the scrollbar in F1. The one-row states are 1120/1120.
   There is no document overflow in any capture. At 390 the table scrolls inside its panel (815-821 px in 318) with
   the first column sticky.
3. **F3 - Due cell wrapped at 390: RESOLVED.** Code, Source and Due are one line in every row at both widths.
4. **F4 - `Read full text` summary wrapped per character at 390: RESOLVED.** Every summary is one line.
5. **F5 - 503 cold-work refusal panel not reachable with this producer: STILL OPEN, question Q17 in
   `.agent/W5-02b-questions.md`.** The :8977 API has no database, so the Site read fails first and the page
   renders `Site unavailable / The site store could not be read, so nothing is known about whether the site is
   configured.` (main 154/172 px, no overflow, no rows, no mock zero). The cold `WORK_STORE_UNAVAILABLE` panel
   with Retry never mounts, so the browser capture of the cold 503 panel is unproven. 403 is proven:
   `SITE_SCOPE_FORBIDDEN`, Retry visible, panel 198 px.
6. **F6 - State badge `Open` split over two lines: RESOLVED.** The badge is one line in every row state at both
   widths (it was 2 lines at 390 and in the 1440 worst case).

All other claims pass: strips 39/84 and notices 66/84 are within caps; positive, historical, pending, stale,
unknown and next pages each show 1 row with the expected notice; zero shows the empty panel; `Show all 5 Actions`
expands to 5 rows; the domain Action shell is `loaded/preparing` for ACT-000001 (main 364/465, strip 42/65,
notice 66/84) and `not_found` for an unknown ID (main 220/252).
