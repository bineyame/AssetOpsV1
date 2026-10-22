# W6-01 mock measurement 2 (v69 mock, headless Chrome, 2026-10-22)

Run by the closure-check reviewer on `AssetOpsV1-plan2` (W6-01 spec files identical at `37ad9ba8` and HEAD `f938516f`). One Chrome at a time, all closed afterwards (process count 0 after every run). This closes the measurement the spec section 4 said was still required, except where "not measurable" is stated.

## What was run

1. Unmodified helper, baseline, all seven screens: `node tools/measure-mock-panels.mjs <scratch>/w601m2/base incidents maintenance maintenance-preventive wr-overview wr-record wr-history oprecords`. Chrome answered this time (the architect's CDP hang did not reproduce). Baseline equals `.agent/W6-01-mock-measure.md` (for example incidents cards 113/248, Incident cases 183/248, oprecords table 540/1069).
2. Injection harness `scratchpad/w601m2/inject.mjs` (same CDP flow and `widthGuard` as the helper, plus live DOM injection; no mock file edited). Per screen and width (1440, 390), five variants:
   - `clean5`: mock rows padded or trimmed to five (the UI page size).
   - `raw`: worst data injected, no mitigation. Data stress = unbroken 200-char text (`T`x200) in every h1 and page subtitle and in **every first-column table cell**; 128-char actor in every By/Owner/Actor cell; UUID in Site/Asset cells; **4000-char text in every other cell of every row**; 4000 chars in every panel narrative paragraph; header Owner = 128 chars and Source = 200 chars.
   - `mitigated`: `raw` plus the spec's section 2 rules as CSS: `min-width:0; overflow-wrap:anywhere` on everything in `main`, `.table-wrap table{min-width:720px}` (panel-local scroll), every table cell wrapped in a three-line clamp block, narrative paragraphs clamped to three lines, chips `max-width:100%`.
   - `expanded`: data stress with wrap rules but no clamp (the "Full text" disclosure open).
   - `fixedcopy200`: mitigated rules, 200 unbroken chars into all fixed copy: tab labels, chips, every header value, status strip, notices, card label/value/note, panel h2/h3, panel subtitle, table footer.
3. Literal check `inject-literal.mjs`: the spec's replacement copy (card notes, case boundaries, notices, status strip, footers, the oprecords read-only form and explanation, a record notice listing 12 REC codes) placed into the mock slots, rows at five, mitigated rules.

Raw JSON: `C:/Users/assef/AppData/Local/Temp/claude/C--Users-assef-Bineyame-AssetOpsV1/97bcb271-5a17-44b6-83b8-6d194dc45f39/scratchpad/w601m2/{base/mock-measure.json,all2.json,literal.json}`.

Caveat: the mitigation is my reading of the spec's CSS rules. It proves the caps are reachable with those rules, not that the implementation applies them. Implementation captures must repeat this (A2 onward).

## Document overflow (blocker 35)

| State | 1440 scrollWidth/clientWidth | 390 |
|---|---|---|
| raw (200-char unbroken h1/title, no rule) | 3366-3461 / 1425 (every screen) | 2662-2821 / 390 (every screen) |
| mitigated, expanded, fixedcopy200, literal | 1425 / 1425 (every screen) | 390 / 390 (every screen) |

The spec's wrap rule closes document overflow. Offenders in raw are the h1, title row, and heading actions. Tables scroll panel-locally at 390 (`720/320`); at 1440 they fit (`1121/1121`). A 200-char tab label does not widen the document (the tab nav scrolls itself, height 57 at 1440 for the scrollbar). Chips with 200 unbroken chars wrap with `max-width:100%` (oprecords chip row 262 / 412 px) and do not overflow.

## Cap verdicts (spec section 2 table)

Heights in px, 1440 / 390. "Natural" = measured without any max-height. Mitigated = worst data stress with the rules; clean = mock copy at five rows; literal = spec copy.

| Spec slot | Spec cap | clean | worst measured | Holds? |
|---|---|---|---|---|
| incidents cards | 150 / 310 | 113 / 248 | literal 113 / 263; fixed copy 200 chars 610 / 1745 | Holds for the spec's literal and for counts. A 200-char unbroken fixed label can exceed it, but card labels are fixed copy, not data. |
| incidents `Incident cases` panel | 600 / 690 | 387 / 637 | mitigated 531 / 549 (rows 80 each, table 431) | Holds. Needs the clamp on every cell; the table must wrap cell content in a block (line-clamp on `td` itself does not apply). |
| incidents `Case boundaries` | 140 / 180 | 99 / 142 | literal 99 / 120; mitigated 142 / 142 | Holds. |
| maintenance cards | 180 / 340 | 138 / 272 | literal 138 / 288 | Holds. |
| maintenance `Corrective work requests` | 610 / 690 | 387 / 620 | mitigated 531 / 549 | Holds. |
| maintenance notice | 90 / 140 | 42 / 78 | literal 43 / 61; 200-char 61 / 99 | Holds. |
| preventive status strip | 70 / 130 | 44 / 98 | literal 37 / 37; 200-char 52 / 82 | Holds. |
| preventive cards | 150 / 310 | 113 / 248 | literal 113 / 248 | Holds. |
| `Preventive plan` | 600 / 690 | 432 / 602 | mitigated 531 / 549; literal 437 / 552 | Holds. |
| preventive notice | 90 / 140 | 42 / 60 | literal 43 / 43 | Holds. |
| request header block | **250 / 390** (ambiguous, see below) | 226 / 430 (block); mheader 88 / 212 | mitigated block 363 / 844; mheader 137 / 394; all five values 200 chars: mheader 137 / 509 | **Does not hold at 390 as measured.** |
| request tabs | 90 / 150 | 42 / 42 | 57 / 42 (200-char labels, self-scrolling) | Holds. |
| overview `Work done` | 430 / 510 | 286 / 338 | mitigated 308 / 338 (4000-char narrative clamped); expanded 1122 / 2101 (exempt) | Holds. |
| overview `Lifecycle` | 350 / 300 | 286 / 161 | mitigated 308 / 193 | Holds. |
| record `Maintenance record · activity` | 650 / 780 | 387 / 637 (six mock rows 438 / 716) | mitigated five rows 531 / 549 | Holds. Six rows is about 615; the record unit has no page size, so more rows rely on the vertical scroll rule. |
| record notice | 100 / 150 | 42 / 42 | literal with 12 REC codes 43 / 80 | Holds to about 12 codes; the spec gives no bound on the code list. |
| history `History` | 600 / 690 | 332 / 402 | mitigated 508 / 508 | Holds. |
| oprecords cards | 150 / 330 | 113 / 263 | literal 113 / 264 | Holds. |
| oprecords `Operational records` | 650 / 780 | 387 / 707 | mitigated 531 / 531 | Holds. |
| oprecords `Record a manual reading` | 180 / 230 | 289 / 443 (mock form) | literal two-sentence replacement 146 / 169 | Holds. |
| oprecords `How records are used` | 330 / 300 | 289 / 188 | literal 146 / 146 | Holds. |
| oprecords chips (no cap in spec) | - | 31 / 70 | 262 / 412 (200-char labels) | **No cap row.** Real labels hold at 31 / 70; suggest 40 / 80. |

### Header block: what the measurement requires

The spec cap "request shared header and tabs 250 / 90 | 390 / 150" does not say whether the header is the `h1`+subtitle plus the `mheader` strip or the `mheader` strip alone.

- `mheader` alone: 1440 holds (137 against 250). At 390, worst realistic content (Owner 128 chars, Source 200 chars) is **394 against 390**, and five 200-char values are 509. Needs 400 as the cap, or a two-line clamp on Owner and Source with a "Full text" disclosure.
- h1 block plus `mheader` (what a reader sees above the tabs): the mock itself is already **430 at 390** with short text (h1 and subtitle wrap to 140, `mheader` 212, plus gap), above the 390 cap. With a 200-char stored title: 363 at 1440 and **844 at 390**. The h1 title is user data (stored revision title), and the spec wraps it without truncation, so the cap for the block must be about 380 at 1440 and 860 at 390, or the h1 needs a three-line clamp plus `Full title text` disclosure like the tables.

Not measurable on the mock (no such element exists there, so the build must capture and cap them): the shared control bar (`From (UTC)`, `To`, `Show records`, `Reload`), `Previous`/`Next`, the `As known at` status line, empty-state, refusal and cursor-changed blocks, the `<details>` disclosures, the `Scroll table horizontally` affordance.

## Conclusion

Every table/panel/card/notice/strip cap in section 2 holds under the spec's wrap and clamp rules, including unbroken 200-char titles in table cells and 4000-char text in the incidents, maintenance, preventive, record, history and operational tables (all five-row panels land at 508-549 against 600-780). Two rows need an edit before A1: the request header block cap (above), and a chip row cap.
