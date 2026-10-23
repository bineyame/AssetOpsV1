# W5-02b K2b evidence: cold Site Work > Actions and domain Action shell

Recapture after the Architect K2 rulings 1-3 (`.agent/W5-02b-K2-rulings.md`), on b6d14905 (producer and capture
tool at that revision; frontend unchanged). Producer: `tools/w502_cold_work_walkthrough.py prepare` (all five DB
modes), `serve`, `attest` (ATTEST OK). Capture: `node tools/w502-cold-work-evidence.mjs
var/w502b_cold_work/manifest.json .agent/W5-02b-evidence` against the manifest's seven APIs (:8971-:8977), each
behind a Vite dev server at API port - 3500, headless Chrome at 1440x1000 and 390x900 (full-page PNG). Every
measurement and claim is in `w502b-measurements.json`: **436 claims, 434 PASS, 2 FAIL**.

Ruled caps (K2 ruling 2), as 1440/390: Work page main <= 1600/2000; Actions panel <= 650/850; strip <= 100/150;
notice <= 110/160; `document.scrollWidth <= clientWidth + 1`; per-cell containment; preview at most two lines; no
horizontal clip of an opened `Read full text`. Action page main <= 1350/1750; strip <= 100/120; notice <= 100/140.

Columns: heights are rounded `getBoundingClientRect().height` px; `notice` is context notice, or currentness/context
notice when a currentness notice shows; `doc` = documentElement scrollWidth/clientWidth (1425 at 1440 means a
vertical scrollbar); `table` = table scroller scrollWidth/clientWidth (at 390 the table scrolls inside its panel,
first column sticky); `contain` = every cell fits, children inside, clamp fits, and every open disclosure body is
inside and fits; `preview<=` = maximum preview line count; Result = that state's claims.

Producer manifest (revision b6d14905): positive CURRENT/1, zero CURRENT/0, historical HISTORICAL/1, worstcase
CURRENT/6 (5 rows + next cursor), pending PENDING_RECOMPUTE/1 (PARTIAL LINK_WORK_PENDING), stale STALE_SOURCE/1
(PARTIAL LINK_SOURCE_STALE), unknown UNKNOWN/1 (UNKNOWN LINK_SELECTION_MISSING); forbidden :8976 HTTP 403
SITE_SCOPE_FORBIDDEN; unavailable :8977 Site read HTTP 200, domain-work HTTP 503 WORK_STORE_UNAVAILABLE.
`fixture.incident.occurred_at` = 2026-10-22T16:11:00Z (D+16h11m) in every mode; both finding_links
(COLD_START_FAILURE + COLD_EXCURSION) in positive, worstcase, pending and stale; see F7 for unknown.

| State | Width | File | Measurements | Result vs ruled caps |
|---|---|---|---|---|
| positive | 1440 | w502b-desktop-positive.png | rows; main 568; strip 39; panel 184; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (17) |
| zero | 1440 | w502b-desktop-zero.png | empty; main 646; strip 39; panel 262; notice 42; doc 1440/1440; table -/-; contain -; preview<= -; rows 0 | PASS (7) |
| historical | 1440 | w502b-desktop-historical.png | rows HISTORICAL; main 628; strip 39; panel 184; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| worstcase-folded | 1440 | w502b-desktop-worstcase-folded.png | rows; main 840; strip 39; panel 457; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 2; rows 4 | PASS (16) |
| worstcase-expanded | 1440 | w502b-desktop-worstcase-expanded.png | rows; main 919; strip 39; panel 535; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 2; rows 5 | PASS (14) |
| worstcase-expanded-open | 1440 | w502b-desktop-worstcase-expanded-open.png | rows; main 1291; strip 39; panel 907; notice 42; doc 1425/1425; table 1105/1105; contain yes; preview<= 2; rows 5 | FAIL: panel <= 650 ({"panel":907,"tableScrollWidth":1105,"tableClientWidth":1105}) |
| worstcase-disclosure | 1440 | w502b-desktop-worstcase-disclosure.png | rows; main 897; strip 39; panel 513; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 2; rows 4 | PASS (16) |
| worstcase-next | 1440 | w502b-desktop-worstcase-next.png | rows HISTORICAL; main 627; strip 39; panel 183; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| window-apply | 1440 | w502b-desktop-window-apply.png | rows HISTORICAL; main 901; strip 39; panel 457; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 2; rows 4 | PASS (12) |
| window-invalid | 1440 | w502b-desktop-window-invalid.png | rows; main 592; strip 39; panel 184; notice 42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (9) |
| pending | 1440 | w502b-desktop-pending.png | rows PENDING_RECOMPUTE; main 628; strip 39; panel 184; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| stale | 1440 | w502b-desktop-stale.png | rows STALE_SOURCE; main 628; strip 39; panel 184; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| unknown | 1440 | w502b-desktop-unknown.png | rows UNKNOWN; main 628; strip 39; panel 184; notice 42/42; doc 1440/1440; table 1120/1120; contain yes; preview<= 0; rows 1 | PASS (15) |
| forbidden-403 | 1440 | w502b-desktop-forbidden-403.png | refused; main 582; strip 39; panel 198; notice 42; doc 1440/1440; table -/-; contain -; preview<= -; rows 0 | PASS (9) |
| cold-work-503 | 1440 | w502b-desktop-cold-work-503.png | refused; main 582; strip 39; panel 198; notice 42; doc 1440/1440; table -/-; contain -; preview<= -; rows 0 | PASS (11) |
| action-positive | 1440 | w502b-desktop-action-positive.png | preparing; main 340; strip 42; panel 23; notice 42; doc 1440/1440; table -/-; contain -; preview<= -; rows - | PASS (6) |
| action-not-found | 1440 | w502b-desktop-action-not-found.png | not-found; main 220; strip -; panel 23; notice -; doc 1440/1440; table -/-; contain -; preview<= -; rows - | PASS (4) |
| positive | 390 | w502b-narrow-positive.png | rows; main 745; strip 84; panel 199; notice 60; doc 390/390; table 820/318; contain yes; preview<= 0; rows 1 | PASS (18) |
| zero | 390 | w502b-narrow-zero.png | empty; main 828; strip 84; panel 282; notice 60; doc 390/390; table -/-; contain -; preview<= -; rows 0 | PASS (7) |
| historical | 390 | w502b-narrow-historical.png | rows HISTORICAL; main 805; strip 84; panel 199; notice 42/60; doc 390/390; table 820/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| worstcase-folded | 390 | w502b-narrow-worstcase-folded.png | rows; main 1002; strip 84; panel 457; notice 60; doc 390/390; table 819/318; contain yes; preview<= 2; rows 4 | PASS (17) |
| worstcase-expanded | 390 | w502b-narrow-worstcase-expanded.png | rows; main 1081; strip 84; panel 535; notice 60; doc 390/390; table 819/318; contain yes; preview<= 2; rows 5 | PASS (15) |
| worstcase-expanded-open | 390 | w502b-narrow-worstcase-expanded-open.png | rows; main 1805; strip 84; panel 1259; notice 60; doc 390/390; table 819/318; contain yes; preview<= 2; rows 5 | FAIL: panel <= 850 ({"panel":1259,"tableScrollWidth":819,"tableClientWidth":318}) |
| worstcase-disclosure | 390 | w502b-narrow-worstcase-disclosure.png | rows; main 1094; strip 84; panel 548; notice 60; doc 390/390; table 819/318; contain yes; preview<= 2; rows 4 | PASS (17) |
| worstcase-next | 390 | w502b-narrow-worstcase-next.png | rows HISTORICAL; main 804; strip 84; panel 199; notice 42/60; doc 390/390; table 819/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| window-apply | 390 | w502b-narrow-window-apply.png | rows HISTORICAL; main 1062; strip 84; panel 457; notice 42/60; doc 390/390; table 819/318; contain yes; preview<= 2; rows 4 | PASS (12) |
| window-invalid | 390 | w502b-narrow-window-invalid.png | rows; main 769; strip 84; panel 199; notice 60; doc 390/390; table 820/318; contain yes; preview<= 0; rows 1 | PASS (9) |
| pending | 390 | w502b-narrow-pending.png | rows PENDING_RECOMPUTE; main 823; strip 84; panel 199; notice 60/60; doc 390/390; table 822/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| stale | 390 | w502b-narrow-stale.png | rows STALE_SOURCE; main 823; strip 84; panel 199; notice 60/60; doc 390/390; table 822/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| unknown | 390 | w502b-narrow-unknown.png | rows UNKNOWN; main 823; strip 84; panel 199; notice 60/60; doc 390/390; table 821/318; contain yes; preview<= 0; rows 1 | PASS (16) |
| forbidden-403 | 390 | w502b-narrow-forbidden-403.png | refused; main 743; strip 84; panel 198; notice 60; doc 390/390; table -/-; contain -; preview<= -; rows 0 | PASS (9) |
| cold-work-503 | 390 | w502b-narrow-cold-work-503.png | refused; main 743; strip 84; panel 198; notice 60; doc 390/390; table -/-; contain -; preview<= -; rows 0 | PASS (11) |
| action-positive | 390 | w502b-narrow-action-positive.png | preparing; main 455; strip 65; panel 23; notice 60; doc 390/390; table -/-; contain -; preview<= -; rows - | PASS (6) |
| action-not-found | 390 | w502b-narrow-action-not-found.png | not-found; main 266; strip -; panel 23; notice -; doc 390/390; table -/-; contain -; preview<= -; rows - | PASS (4) |
| unavailable-503 (legacy, separate Site refusal) | 1440 | w502b-desktop-unavailable-503.png | Not recaptured: kept from the 75abbaf3 capture. Site frame refusal `Site unavailable` (API with no database); main 154; doc 1440/1440 | Not cold-work proof (K2 ruling 3); superseded by `cold-work-503` |
| unavailable-503 (legacy, separate Site refusal) | 390 | w502b-narrow-unavailable-503.png | Not recaptured: kept from the 75abbaf3 capture. Site frame refusal `Site unavailable`; main 172; doc 390/390 | Not cold-work proof (K2 ruling 3); superseded by `cold-work-503` |

Two further claims (`worstcase: Next page link present`, 1440 and 390) PASS. `worstcase-next` and `window-apply`
read HISTORICAL because the page-one `known_at` is pinned in the URL (U3, ruling 1); that is specified behaviour.

## Findings (frontend untouched by this capture)

1. **F1 - worst-case Actions panel against the ruled caps (650/850): FAILS only with every disclosure open.**

   | Width | Folded | Expanded | One disclosure open | Expanded, all open | Page main (folded / expanded / one open / all open) |
   |---|---|---|---|---|---|
   | 1440 | 457 | 535 | 513 | **907** (cap 650, 257 over) | 840 / 919 / 897 / 1291 (cap 1600, PASS) |
   | 390 | 457 | 535 | 548 | **1259** (cap 850, 409 over) | 1002 / 1081 / 1094 / 1805 (cap 2000, PASS) |

   Every other worst-case state is inside the panel cap, and page main is inside its cap in every state, including
   all-open. With all ten title/owner disclosures open each row is 154 px (1440) / 225 px (390); the opened body
   repeats the full text below the still-visible two-line preview (see the all-open PNGs), which is most of the
   extra height. Containment holds (no horizontal clip, doc 1425/1425 and 390/390, previews at most two lines).
2. **F2 - 1440 table scrolled sideways: RESOLVED** (scroller 1120/1120, all-open 1105/1105; no document overflow).
3. **F3 - Due cell wrapped at 390: RESOLVED** (code, Source and Due one line in every row).
4. **F4 - `Read full text` summary wrapped per character at 390: RESOLVED** (every summary one line).
5. **F5 - 503 cold-work refusal panel: RESOLVED by `cold-work-503`.** Healthy Site read (no Site refusal, cold Work
   page mounted), panel `refused` WORK_STORE_UNAVAILABLE, text `Cold work unavailable / Work records could not be
   read or saved.` with Retry, no rows, no mock zero (scope `Scoped to Cold · — actions`), panel 198, main 582/743. The legacy
   `unavailable-503` PNGs remain a separate Site-level refusal only.
6. **F6 - State badge `Open` split over two lines: RESOLVED** (one line everywhere).
7. **F7 - producer `unknown` mode carries a non-null `blocked` note:** ` INC: no selected COLD_EXCURSION Finding
   revision to link (ruling 4)`. The no-probe replay has no COLD_EXCURSION Finding, so its Incident links only the
   COLD_START_FAILURE Finding (one finding_link, not both). The mode still built, the read is UNKNOWN/1 as expected,
   attest passed and the `unknown` captures pass; ruling 4's "both links" is not met in this mode only.

Window control (ruling 1): placement and alignment claims pass at both widths; `window-apply` keeps `known_at`,
drops the cursor and reads page one (5 rows, `Show all 5 Actions`); `window-invalid` shows `The window may span at
most 31 days.` and does not navigate. Domain Action shell: `loaded/preparing` for the positive Action (909f6215) (main 340/455, strip
42/65, notice 42/60) and `not_found` for an unknown ID (main 220/266).
