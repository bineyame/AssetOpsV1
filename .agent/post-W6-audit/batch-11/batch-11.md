# Post-W6 audit, batch 11: W3 estate composition

IDs: `globalevidence`, `globalfinancials`, `portfolio`. Branch `audit/batch-11` at main `0fc2b048` (product code identical to frozen `fddf5cad`), worktree `AssetOpsV1-review5`. Mock authority: `frontend/mockups/v69/index.html`, served by the same Vite origin and rendered at 1440x1000 and 390x900 CSS px.

All dispositions are **proposals** for the Architect. This batch adds no register rows.

Machine-readable record: `batch-11.json` (66 pairs, plus 18 uncounted link-destination checks). Side-by-side view: `index.html`. Difference source: `differences.json` (written by `tools/differences.py`).

## Run record

- **Producers (reviewed, unmodified).**
  - W3-03: `.agent/W3-03-evidence/test_serve_portfolio.py`, the W3-03 run-3 capture harness. It builds the reviewed clean four-Site fixture (`build_portfolio_fixture`: KOBO-001 W1 priced, COLD-LAB-001 excursion drained, EV-LAB-001/002 gross tariff) and serves the real `create_app()` at a frozen read clock (2026-10-30T09:03Z). I ran it four times: `W303_ROUTER=capture` (clean, twice; the second run recaptured after a capture-height fix), `W303_COLD_DRAIN=0` (pending) and `W303_NO_CURSOR_KEY=1` (503). It uses only its own controls: `/__capture/mode` (foreign tenant, auth deny) and `/__capture/empty-site`.
  - W3-02: `.agent/W3-02-evidence/serve.py`, the W3-02 commit-2 harness (KOBO S4/S6 chain, cold late-reading, EV interrupted with tariff and money, a foreign tenant). I used its `/__capture/empty-site` and `/__capture/late-kobo` controls. I did not run `serve-financials.py`: it differs only in the drained cold excursion, and the W3-03 fixture already covers that, plus the two-EV comparable group.
  - `PYTHONPATH` was set to this worktree's `backend;gateway;simulator;contracts;host`.
- **Databases.** The W3-03 harness accepts `W303_DB`, so I used `assetops_audit_b11_test` (rule a). The W3-02 harness hard-codes `w302j_test`. That is a tool-created capture `*_test` DB, covered by `.agent/owner-test-db-authorization-2026-10-18.md`, which the 2026-10-24 scratch authorization reaffirms. It is narrower than rule (a), and I record it here as a deviation. Before preparing, `pg_database` showed only batch 10's `w301cap_test`, which I did not touch. I created both DBs before use and dropped both `WITH (FORCE)` after capture.
- **Ports (deviation).** Both producers hard-code their API port (W3-03 9781, W3-02 9751). Running them unmodified took precedence over the 18101-18109 range. Neither port collides with batch 10, whose W3-01 harness uses 9741. Vite ran on 127.0.0.1:5181 (`--strictPort`), with `ASSETOPS_API_PORT` set per phase. Chrome used CDP 9521 and was started and killed by the capture script. Every server was stopped by PID (pytest/uvicorn 30772, 19792, 21764, 18852; serve.py 10348; Vite 29064 and 3600).
- **Capture.** `tools/capture-b11.mjs` is `capture-b9.mjs` with these changes:
  - the CDP port and profile prefix;
  - a visible-link dump (href, text, panel);
  - a closed-disclosure text-length probe (DOM read only, no click);
  - a screenshot-height filter that ignores scroll boxes inside closed `<details>`;
  - an `APP_ONLY=1` link-destination mode.

  It is capture-only: it navigates, waits, takes screenshots and measures the DOM. Targets are written by `tools/mk_targets.py`. Logs are in `logs/`.
- **Cases (33 x 2 widths = 66 pairs).**
  - W3-03, all three IDs: `w303-positive` (the representative pairs; one-day 10-06 request), `w303-partial` (adds W303-EMPTY-001), `w303-historical` (`known_at` 2026-09-30), `w303-pending` (a_lineless_cold), `refused-reversed`, `refused-over-31d` and `no-window` (bare route).
  - W3-03, portfolio only: `w303-empty-foreign-tenant`, `w303-refusal-401` and `w303-refusal-503`.
  - W3-02, all three IDs: `w302-positive` (10-06), `w302-partial-week` (10-05..10-12 with an empty Site) and `w302-pending-late-kobo`. Portfolio refuses with 503 under this producer (B11-16).
  - Not captured: `refusal-409` needs a `Load more Findings` click, which a capture-only wrapper may not do. The W3-03 run-3 evidence covers it.

## Inventory reconciliation against `frontend/src/App.tsx`

| ID | Mounted route | Status |
| --- | --- | --- |
| `globalevidence` | `EVIDENCE_PATH` `/evidence` -> `EstateEvidenceFrame` | mounted (App.tsx:496) |
| `globalfinancials` | `FINANCIALS_PATH` `/financials` -> `EstateFinancialsFrame` | mounted (App.tsx:498) |
| `portfolio` | `PORTFOLIO_ROOT_PATH` `/portfolio` -> `EstatePortfolioFrame` | mounted (App.tsx:500) |

The spec route table (rows 64-66) matches. One naming note: the "W3-03 same-cutoff portfolio producer" and the "W3-02 exact selected estate evidence/money" producers are the `.agent/W3-0x-evidence/` capture harnesses, not `tools/` walkthroughs.

## Domain wiring and link destinations (the caller's question)

Each domain's rows, totals and links were followed to their landing pages; the details are in `link_destination_checks_not_counted`.

- **Cold.** Every cold row (Evidence capability rows, the Financials row, Portfolio Findings and Site links) lands on the cold Overview or cold Evidence, with the row's own window and cutoff. These are correct domain views.
- **EV.**
  - Evidence and Financials row links land on `/ev/evidence` and `/ev/financials` for the right Site. These are correct.
  - **EV Site-name links land on `/sites/EV-LAB-00x`, which shows the generic "Awaiting evidence migration" Overview instead of the EV Overview at `/sites/:id/ev` (B11-01, Medium; the B7-01/B9-10 family).**
  - The comparable EV group (two lines, KES 16.66–16.67) appears only in positive. It is honestly withdrawn in partial and historical.
- **Mini-grid.**
  - Links go to the base Site routes by design ("Opens current Site view").
  - The landing is unverified, because both W3 harnesses return 503 SITE_STORE_UNAVAILABLE for KOBO-001 (B11-03).
  - Under the W3-02 producer there is no mini-grid money line (an accepted W3-02 limitation).
- **Totals.** No estate-wide total appears in any state. The only total is per comparable group, inside the Aggregation disclosure.
- **Built destinations left inert in Portfolio.** Cold Finding links and every matrix cell are inert although the destinations are built (B11-02).
- **B3-15 (Portfolio roll-up links on Site Financials).** These three screens are the targets those links should reach. All three are mounted and render. The EV Site Financials and cold Site pages still lack the back-links (B11-15).

## Mandatory carried UI-pass checks

| Item | Result on batch-11 screens |
| --- | --- |
| `.prose` 14 px vs mock 12 px | Does not recur: `.prose` is 12 px and table text is 10-11 px, equal to the mock. |
| Tall dark header at 390 on short pages | 299 px on the globalevidence/financials refused pairs, and 309 px on the portfolio refused, 401, 503 and W3-02 503 pairs (11 pairs). Cite B1-02/B2-04. |
| `1 incidents` plural | Not applicable. |
| Raw `c1 · EV_CONNECTOR` | Not present. Other raw codes and UUIDs are cited under B1-53 (B11-X1, B11-12). |
| One generic window error | The estate analogue: reversed and over-31-day windows share "Choose a valid date range of at most 31 days." (B11-13, cites B7-11). |
| 390 Window control (R88/R112) | The W3 shared date bar is page-local (B2-02). R88/R112 cover Work screens only, so a W3 row or the topbar fix is needed. |

## Existing D3 rows R22/R23/R24/R37/R38/R60

None touch these screens. Estate windows are UTC days by the W3 contract, so R24 (site-local time) does not apply. No register row covers any W3 screen, so every W3 spec ruling below needs a row.

## Layout checks

- App page horizontal overflow is 0 on all 66 pairs. There is no clipped text, no console error and no crash.
- Panel count, titles and order equal the mock on every non-refusal pair. Refusal pairs (reversed, over-31-day, 401, 503) show refusal copy only, by design.
- No panel is over 1.3x the mock. The maximum is Aggregation rule at 1.22x (1440) and 1.14x (390).
- Scroll containers, all readable:
  - Evidence and Financials tables scroll inside their panels at 390 (520/800 px in 318 px), and both use an internal vertical cap at 1440 (B11-04, B11-07).
  - The Portfolio matrix scrolls horizontally at both widths with four or more Sites (B11-11).
  - The Portfolio priority table scrolls 720 px in 336 px at 390.

## Differences (proposals)

| ID | Screens | Summary | Proposed disposition |
| --- | --- | --- | --- |
| B11-X1 | all | Cross-cutting citations: B1-01, B1-04, B2-02, B1-02, B1-53, B2-21/B3-04; B1-07 does not recur | cite existing IDs |
| **B11-01 (Medium)** | globalfinancials (and Portfolio rows) | EV Site-name links open /sites/EV-LAB-00x, which shows the "Awaiting evidence migration" Overview, not the EV Overview /sites/:id/ev | (c) D3, B7-01/B9-10 family |
| B11-02 | portfolio | Cold/EV Finding links inert ("Finding detail unavailable") and every matrix cell "Site detail unavailable" although the destinations are built | (c) D3 Low (expired S12 restriction) or D5 |
| B11-03 | all | Mini-grid rows open base Site routes; landing unverified (KOBO-001 503 in both producers) | D1 row; recheck with a W1 producer |
| B11-04 | globalevidence | One row per Site x capability (13-22) vs per Site (3); internal vertical cap | D2 row; worst-case cap ruling |
| B11-05 | globalevidence | Gaps 1/0 rows vs 4; "Example destinations" prints mock-only "ACT-049, ACT-061" | mock IDs (c) D3 Low; rows D1 |
| B11-06 | globalevidence | KPI tiles: 4 of 4 / Not assessed / Not assessed | D1 |
| B11-07 | globalfinancials | Long semicolon-joined Basis text; EV rows hidden below the internal scroll at 1440 | (c) D3 Low; cap needs a row |
| B11-08 | globalfinancials | Aggregation chips + Results disclosure (1.22x); comparable total only inside the disclosure | D2 row |
| B11-09 | portfolio | Cards, context, pulse, opportunity, footer honest replacements | D1/D4 rows |
| B11-10 | portfolio | 3 rows vs 6, all Not assessed; raw revision UUID; no EV Finding row (unverified cause) | D1; Architect check |
| B11-11 | portfolio | Matrix scrolls at 1440 with four or more Sites (spec-ruled) | D2/D6 row |
| B11-12 | portfolio | Scope disclosure ~23,700 characters of UUIDs in a 320 px box (scrollHeight 32,259) | (c) D3 Low |
| B11-13 | all (refused) | One generic window sentence; reversed range echoed | cite B7-11 |
| B11-14 | all | Same-cutoff, partial, historical, pending and empty states behave as specified | informational |
| B11-15 | cross-check | B3-15 back-links still missing; these screens are the targets | cite B3-15/B7-07/B9-06 |
| B11-16 | portfolio | W3-02 producer lacks the cursor key, so Portfolio returns 503 "unavailable right now" | informational |

## Blockers

None blocking. Limits:

- The mini-grid landing is unverified (KOBO-001 503 in both W3 harnesses).
- `refusal-409` was not captured, because it needs a click.
- The two producers hard-code their ports and the W3-02 DB name, which I record as deviations above.
