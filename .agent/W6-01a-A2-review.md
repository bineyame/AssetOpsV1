# W6-01a unit A2 review (fresh independent Claude reviewer), with the A1 reopen

Branch `task/W6-01a-global-incidents`, head `87a34a75`. Code diff `git diff befe6cf8 87a34a75 -- frontend backend tools`
(A1 reopen `0ad4462f`; A2 `db8b3847`, `63d62caa`, `ccbb0b43`, `0a96d21e`, `428d4117`, `87a34a75`).
Judged against `.agent/W6-01-build-spec.md`: the A2 card, §2, §3.1 (A2Q1-A2Q10, CL3, A2Q11, R5-R8, F1-F6) and §4.
I also compared it with the v69 `incidents` screen (`screens.js:514-517`, `screen-manifest.json`).

## Verdict: REVISE

There is one Medium finding (M1), which blocks. There are six Low notes, and none of them blocks.

## Scope

All 27 changed files are on the A1-reopen card or the amended A2 card. That includes Lane B's
`tools/w601_seed.py` (A2Q2) and the six A2Q11 files. `tools/checks/*` is on the A2 card itself; A2Q11's
"tools/checks stays untouched" applies only to the A2Q11 edits. No file outside the card is touched.

## Checks run (on `87a34a75`)

- `npx.cmd tsc --noEmit`: exit 0.
- `npx.cmd vitest run --minWorkers=1 --maxWorkers=2` on 12 files: the four `src/work` files, `siteWorkCases`, the
  five Lane A rail and route tests, and the six A2Q11 files. Result: **12 files, 203 passed, 0 failed** (71 s). It
  ran under this sandbox.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
  `check_v69_dependency_registry.cjs`: exit 0. `check_v69_ledger.py`: valid (110 screens, 258 panels).
- **Not run:** the backend tests, by instruction, because a full suite is using the shared Postgres. So
  `test_state_counts_cover_full_selection` was reviewed by reading only. I did not run the capture script, the full
  `src/shell src/estate src/sites src/work src/ui` vitest run (the implementer reports 2464 passed), or
  `npm run build`.

## Rulings verified

- **A1 reopen (A2Q1).** `state_counts` is computed over `rows`. That is the full selection, before the cursor
  filter (`remaining`) and before the `limit` slice, so pages one and two report identical counts. EMPTY_SCOPE has
  `rows=[]`, which gives all zeros. The key is in every 200 envelope, and refusal bodies are unchanged. The test
  seeds the `incidents` fixture (four OPEN and one IN_PROGRESS on demo), CLOSEs the pump, and then asserts
  `{4,1,1}` on both pages and zeros on a deny-all read. That matches the ruling. `ENVELOPE` gains the key.
- **Cards (A2Q1).** `Open incidents` = `state_counts.OPEN + state_counts.IN_PROGRESS`, with the note
  `Open or in progress in this window`. The other three cards are `Not assessed` with the §2 notes. The card row
  renders only on CURRENT or HISTORICAL, including a zero. The mock's `INC-203` note is not reproduced. The test
  shows the card reading 5 on page two (the full selection). In the stress capture, OPEN 5 plus IN_PROGRESS 1 shows 6.
- **Copy literals.** These match §2, A2Q6 and CL3-1 exactly:
  - the subtitle;
  - the loading sentence;
  - the controls `From (UTC)`, `To (UTC, exclusive)`, `Show records` and `Reload`, with no cutoff input (A2Q5);
  - `As known at …` and `Historical as of …`;
  - all seven refusal sentences, with `Reload the first page` only on INVALID_CURSOR and WORK_BASIS_CHANGED, whose
    href keeps `from`, `to` and `known_at` and drops `cursor`;
  - `No accessible Sites.`;
  - the zero pair;
  - the footer as the Panel `description` (A2Q7);
  - the `Case boundaries` text;
  - `Scroll table horizontally`.

  An invalid page query renders the refusal sentence without a fetch.
- **Cells (A2Q8).** These match:
  - the columns;
  - `{code} · {title}` linked to `links.site_incidents.href`, inside the clamp block;
  - `Full title text` and the A2Q4 source `<details>`, all four classifications;
  - the Site link;
  - the en-GB UTC Start;
  - Severity `Not recorded`;
  - the State chip, which uses `stateTone("incidents", …)` and a copied label map;
  - Owner or `Not assigned`;
  - Findings, then Actions, joined by ` · `, then the request codes, with `None linked` when all three are empty.
- **Paging (A2Q10, R5).** The page sends `limit=5`. It forwards only `from`, `to`, `known_at` and `cursor`; other
  keys are ignored (tested). `globalWorkTrail` is kept in history state. A hidden Previous or Next renders nothing.
  `Showing {a}–{b} of {N}` appears only when `total_count > 0` on CURRENT or HISTORICAL. Show records keeps
  `known_at` and clears the cursor and trail. Reload re-reads page one.
- **Rail and route (F1-F3, F5, A2Q9).**
  - The rail line, the `$expected` entry, the three F2 fixture cases (verbatim), `INCIDENTS_PATH` and the route
    before the catch-all are all correct.
  - The ledger `incidents` row matches all F5 fields and the three literals. The `sitework-incidents` substring is
    replaced. The `incidents:1,2` registry reasons are edited, with the status still `gap`.
- **Site Work strip (§1).**
  - `globalWorkManageHref` matches the §1 example exactly (tested). An explicit `scope.knownAt` wins; otherwise the
    loaded `known_at` is used. It carries no Site key, cursor or limit.
  - Only the Incidents strip links. Maintenance keeps `· Not available yet`. Both scan exemptions are correct.
- **`stress` fixture (A2Q2).** It writes six KOBO-001 (tenant one) incidents at the incidents occurrence time.
  Incident 1 has `("Backupgeneratorautomaticstartfailure" * 6)[:200]` and is assigned
  `("Fieldmaintenancesupervisorteam" * 5)[:128]`. Incidents 2-6 are `Stress incident n`. It is added to `FIXTURES`.
- **A2Q11.** All six files carry exactly the ruled label, href and icon lists, plus `"Incidents"` appended to
  `ADMITTED_SINCE_T004`. `T004_OPERATOR_NAVIGATION_LABELS` is unchanged. See L1 for the missing comments.
- **Mock comparison (1440 and 390 captures).**
  - The panel set and order match the mock: page header with the mock subtitle, four cards, `Incident cases`
    (heading, sub-line, table), then `Case boundaries`. Prominence matches: the cards are a full-width row above
    the table, and at 390 they form a 2×2 grid.
  - The departures are all labelled in the spec: the §2 new elements (control bar, status line, pager, `Showing`
    line, scroll hint and state blocks), the replaced footer, the replaced boundary copy, and the honest card
    values.
  - In every capture the document width equals the viewport. At 390 the table scrolls inside its panel (720/318),
    with the hint visible.
  - The refusal, cursor-changed and 503 states put the state block where the cards were, above the empty table
    panel.
  - I found no unlabelled departure.

## Findings

### M1 (Medium, blocking): the table panel has no vertical overflow, so the §2 cap holds only for the captured data

- **Where:** `frontend/src/work/globalWork.css` (whole file). There is no `max-height` or `overflow-y` rule on the
  `Incident cases` table region and no sticky header.
- **What the spec requires:** §2 says: "Panel `max-height` caps below apply to collapsed state; overflowing table
  body scrolls vertically within the panel, with headers visible". The `Incident cases` cap is 600 at 1440 and 690
  at 390. The precedent is `estatePortfolio.css:110`
  (`.portfolio-findings .data-table__scroll{max-height:604px;overflow:auto}`).
- **Why the captures pass anyway:** the positive capture measures 524 / 664 only because four of its five rows have
  one-line titles (row heights 65, 65, 65, 65, 99). Historical at 390 is already 682 of 690.
- **Why real data breaks it:** a row whose title, owner or Findings/work cell clamps to three lines is 99 px. Titles
  of about 80 characters or more do that, and W4 allows 200. With five such rows the table is about 530 px and the
  panel about 661 px at 1440, which is over the 600 cap. At 390 the table keeps its 720 px minimum width, so the
  row heights are the same and the panel is about 790 px, against a cap of 690.
- **Fix:** cap the table region inside `.global-work` (for example, `max-height` on `.data-table__scroll` derived
  from the cap, `overflow: auto`, and `position: sticky; top: 0` on `thead th`). Then add one 1440 and 390 capture
  or measurement in which all five rows are three-line rows. The `stress` fixture could give incidents 2-6 long
  spaced titles, which stays inside A2Q2's six rows only if the Architect agrees. Otherwise, measure with an
  injected typed response and label it that way.

### Low (non-blocking)

- **L1. The A2Q11 comment rule is not met.** A2Q11 says: "A comment `// W6-01a: Incidents rail root is live.` goes
  above each edited literal." None of the six files has it (`grep "rail root is live"` finds nothing). The literal
  values themselves are correct. Add the comments on the branch, or in B2, which edits the same lines.
- **L2. R6 and A2Q10 disagree on where the `Showing` line goes.**
  - R6 (as confirmed by the Architect) puts "the control bar, status line and `Showing` line" in `.site-date-bar`.
  - A2Q10 says "Above the pager".
  - The code (`GlobalIncidents.tsx:333`) follows A2Q10 and the builder's original R6 reading. That is defensible,
    but the Architect should reconcile the text before B2 and E2 copy it.
- **L3. A2Q8's request-code separator is interpreted, not followed literally.**
  - A2Q8 reads "If `linked_request_codes` is non-empty, add ` / ` and the codes".
  - The code omits ` / ` when there is no Finding or Action link (`GlobalIncidents.tsx:125`), so the cell reads
    `WR-000009` rather than ` / WR-000009`. The test pins that reading, and the historical capture shows `WR-000008`.
  - This is sensible, but it is unrecorded. Note it in the handoff for the Codex retrospective.
- **L4. The R8 note is missing from the manifest.** R8 says "Each manifest notes `dev server StrictMode issues each
  read twice; the built app issues one`". `.agent/W6-01-evidence/A2/manifest.json` records `[200, 200]` per read
  without that note. Also, the `cursor_changed` refused captures record `route` without the `cursor` they actually
  loaded (their `api[0].url` does carry it). These are evidence-only corrections.
- **L5. The `Showing` line is wrong on a pasted page-two URL.** `a = trail.length × 5 + 1` follows A2Q10 exactly.
  But a page-two URL opened in a new tab, which has no history state, reads `Showing 1–1 of 6` for row 6. This is a
  spec-level residual risk; it is not a build defect.
- **L6. The date inputs show the browser's locale format.** The native date inputs render `10/14/2026` in the
  captures, while every displayed date is in en-GB format. This is a preference for the post-W6 UI pass, not a gap.

## Residual risk not named in the packet

- A Site Work `Manage in Incidents` link always carries the loaded Site `known_at`. That cutoff is earlier than the
  global read time, so the global page opens as `Historical as of …` rather than `As known at …`. This is exactly
  what §1 requires (an explicit earlier cutoff is HISTORICAL). The owner may still read it as stale at the
  walkthrough.
- Backend `state_counts` correctness was confirmed by reading only. The focused backend file was not rerun here,
  and no full-suite result on `87a34a75` was cited to me.
