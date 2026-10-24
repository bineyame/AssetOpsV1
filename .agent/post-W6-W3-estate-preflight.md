# post-W6 W3-estate: builder pre-flight

2026-10-24. Branch `task/post-W6-W3-estate` at main `7554111e`. No product code is written yet.

Sources: the W3-estate card and rulings in `post-W6-audit/fix-slices.md`; register rows R293-R308; `classification.md` lines 229-247; `batch-10.json` and `batch-11.json` differences; the v69 mock; ROLE_CONFIG lesson 15 and Builder pre-flight; `post-W6-shell-rulings.md`. Each item gives a recommended default for the Architect to accept or change. Code anchors are relative to `frontend/src/` unless they start with `backend/`.

## A. Ownership and overlap

**Q1 - Backend edits are needed. Card says "no backend estate file without a demonstrated DTO omission".** Several of these IDs come from server-built links or strings, so each one demonstrates a DTO omission:
- B11-01 EV Site links: `estate/portfolio.py:168`, `estate/evidence_money.py:136` `_site_href` (also the EV `site_readiness` fallback at :152 and :183), `estate/financials.py:142-149` (`site`, and `bridge`/`evidence` fallback to base), and `estate/index.py:88`.
- B11-02 inert links: `portfolio.py:168-171` (S12 comment) and `_cell()` `destination: None` at :298-300.
- B11-07 `.;` joins: `financials.py:197` `"; ".join(limitations)`.
- B10-07 title: `estate/coverage.py:312` `f"Action {code}"`.

**Default:** permit edits to these five backend files, limited to links and labels, plus the backend tests listed in G. The schema version stays unchanged, because field names and types do not change.

**Q2 - B11-01 owner.** The card and R296 assign it to W3-estate. B7-01 and B9-10 are the cold and EV Site Findings list routes (W2-cold R253). W2-EV owns none of B9-10 or B11-01.

**Default:** W3-estate fixes every estate-emitted EV link in the backend, so W2-EV is not involved. Backend `site` becomes `/sites/{code}/ev` for EV_CHARGING. The EV unproven-window fallbacks become `/sites/{code}/ev` too, not the bare `/sites/{code}`.

**Uncovered:** two gaps belong to no card:
- the EV Site's own tab row, where Overview, Evidence and Financials go to the generic paths (`shell/operatorSiteTabs.tsx:70-83`);
- bare `/sites/:id` not being EV-aware (`shell/SiteDetailFrame.tsx:119-131`).

**Default:** leave both out of W3. The Architect should assign them, probably to W2-EV.

**Q3 - Shared files with W2-cold and W2-EV.** W3 shares no product file with either. B11-13 cites B7-11, which W2-cold owns. That fix is in different files (cold views and domainActionClient), but the copy should match.

**Default:** the Architect rules one sentence pair for both cards:
- reversed window: "The start of the range must be before its end."
- over 31 days: "Choose a range of at most 31 days."

**Shell overlap:** `.estate-cell__primary` and the estate CSS are local and are not the shell's `primitives.css` or `tokens.css`. W3 does not touch `siteWorkCases.tsx` or the Action crumbs. W3 must rebase on the shell merge, because shell CSS reaches the estate screens.

**Q4 - The estate Findings index has the same expired restriction as B11-02.** `estate/findingIndex.tsx:203-211` leaves cold and EV Finding titles inert (Run 13 ruling 3), on the `findings` screen. R294 and R295 cover other defects there.

**Default:** out of scope. Raise it as a new D3 for a later card rather than widen W3. The Architect may instead fold it into B11-02, at the cost of 4 Findings screens' worth of link tests.

## B. Per-ID target behaviour

**Q5 - B10-07 / R293 `actions` title.**
- The mock row reads "ACT-048 · Review generator stop setting".
- The Action page title is `{action_code} · Battery reserve trial` (`sites/SiteAction.tsx:170`). "Battery reserve trial" is a frontend literal for the one supported Action kind.
- The estate row reads `Action ACT-000001` (backend `coverage.py:312`).

**Default:** keep the backend `action_title` unchanged and render `{action_code} · Battery reserve trial` in `estate/actionIndex.tsx` through a local constant that cites SiteAction.tsx:170. The Portfolio action column stays as it is, since it is not a D3.

**Alternative:** change `coverage.py`, so Portfolio and Actions both change and `test_w301_estate_api.py:258` breaks. Neither option is right if a second Action kind is ever added, and no kind field exists to switch on.

**Q6 - B10-07 success criterion.** The card names "title/criterion", but the ledger disposition makes only the title D3. The row has no criterion source: coverage `success_criterion: None`, while a frozen plan's target exists in `_plans` (shell Q14 reads that target on the change page).

**Default:** keep "No success criterion recorded". Treat criterion as a D1 already covered by R287 (B10-01) and add no backend read.

**Alternative:** coverage adds the selected frozen plan's stored target. This is new backend work, needs a Postgres test, and is a likely cap/row-height change.

**Q7 - B10-08 / R294 pending copy on the 4 lenses.**
- Cause: KOBO PENDING_RECOMPUTE with `selection_id` non-null (...0584). The panel line `PARTIAL_TOTALS` and the notice `PARTIAL_COVERAGE` (`estate/estateShared.tsx:72-74,171-179`) both claim "no selected result" / "not yet assessed".
- Data source: `EstateCoverageSite` has no site name, but the existing `EstateClient.scope()` read (`estate-scope-1`, `estateClient.ts:402,462`) returns `site_id`, `site_code`, `site_name` and `coverage_state` for the same window.

**Default:** frontend only. Findings issues a second `scope` read with the same `from`/`to`/`known_at` and joins on `site_id`. Copy is chosen by cause:
- PENDING_RECOMPUTE with a selection:
  - panel: "Totals are unknown while new evidence for {Site name} is assessed; its rows are held until then."
  - notice: "New evidence for {Site name} is being assessed."
- No selection (UNKNOWN, or `selection_id` null):
  - panel: "{Site name} has no selected result; totals are unknown."
  - notice: "{Site name} is not yet assessed; estate totals are unknown."
- Several Sites: list the names comma-joined. If the scope read fails, fall back to the current generic sentences.

`limitationSentences()` is shared with `actionIndex.tsx` (and maybe Evidence/Financials). Change it only through a cause-aware variant used by the Findings lenses, and keep the Actions behaviour unless the Architect wants it there too.

**Q8 - B10-09 / R295 `findings` at 390.**
- `.estate-cell__primary` clamps to 2 lines with an ellipsis (`estate/estate.css:104-109`). It is also used by Actions, Financials, Site and Basis cells.
- The sticky first column is wide (table min-width 900).
- The mock at 390 shows Finding, Site, Priority and part of Confidence.

**Default:** remove the clamp on `.estate-cell__primary` everywhere in the estate (no title is truncated) and use `overflow-wrap: anywhere`. At `max-width: 640px`, cap the sticky first column at `width: 9.5rem; max-width: 152px` so that Finding, Site, Priority and part of Confidence are visible at 390. Prove it in jsdom with a CSS-source assertion and in captures with a measured scrollHeight equal to clientHeight on the KOBO title.

**Q9 - B11-01 / R296 EV Site links.** See Q2. These rows are affected: Financials Site cells (`EstateFinancials.tsx:172`), Portfolio rows (`EstatePortfolio.tsx:167`), Evidence rows (`site`, plus the `site_readiness` fallback), and Findings index Site links (`findingIndex.tsx:235`, through `index.py:88`). Cold stays `/sites/{code}`, which is correct; mini stays as it is.

**Default:** add a backend helper `site_home_href(code, domain)` in `evidence_money.py`, reused by the other three files. No frontend change beyond tests.

**Q10 - B11-02 / R297 Portfolio inert links.**

*Findings:* cold and EV need the Finding's own `from`/`to`/`known_at`. `revision_id` is ignored for cold and EV, and an out-of-window Finding gives 404 (`SiteAnalyticsFrames.tsx:620-693`; `postgres_assessment_store.py:2294-2296,2377`). The portfolio row has `episode_start` and `_episode_end`, plus the selected window and cutoff per Site in `scope_disclosure`.

**Default:** cold and EV `links.finding` = `/sites/{code}/findings/{fid}?from={site window from}&to={to}&known_at={row-local cutoff}`. Emit it only when the window is at most 31 days and the cutoff is proven, using the same rule as `window_links` (closure 5 B5). Otherwise emit null and keep "Finding detail unavailable".

*Matrix:* every cell has `destination: None`. The mock targets are:

| Objective | Mini | Cold | EV |
| --- | --- | --- | --- |
| Service/product | service | temperature | sessions |
| Backup | backup | coldbackup | ev-foundation |
| Asset condition | asset | cold-health | ev-health |
| Cost control | financials | cold-financials | ev-financials |
| Evidence | evidence | cold-evidence | ev-evidence |

**Default:** a server table in `portfolio.py` with these destinations:
- Service: `/sites/{c}/performance/service`, cold `/performance/temperature`, EV `/performance/sessions`.
- Backup: mini `/performance/backup`, cold `/performance/backup`, EV null (no backup objective; keep "Site detail unavailable", or better "No configured objective" if the Architect allows the copy).
- Asset condition: `/sites/{c}/health` for all three.
- Cost control: reuse the row's `_money_links` bridge (windowed for cold and EV, `/financials` for mini; EV `/ev/financials`).
- Evidence: reuse `window_links` `site_readiness` (EV `/ev/evidence`).

Cells keep their `title`/`aria-description` reason and become `<Link>` when the destination is non-null.

The mini Asset target in the mock is `asset`, which is a single asset page. **Default:** use Site Health instead, because no estate-level asset choice exists.

**Q11 - B11-05 / R300 `Example destinations`.** `EstateEvidence.tsx:46` prints the mock-only "ACT-049, ACT-061" and "Map transfer switch" as inert entries.

**Default:** remove both inert entries from `EXAMPLE_DESTINATIONS` and keep the two live links (`Operational records →`, `Preventive plan →`). Rename the label from "Example destinations" to "Related records". The row count stays D1 (one gap source), with no new label. A test asserts that "ACT-049" and "Map transfer switch" are absent.

**Q12 - B11-07 / R302 `globalfinancials` Basis text and the hidden EV rows.**
- Text: the backend joins sentences that already end in "." with "; ", which gives ".;".
  - **Default:** `financials.py:197` joins with `" "`. The cell shows the first sentence. The full text moves into the existing Basis details disclosure, which `EstateFinancials.tsx:102` already has; add a "Limits" line there.
- Hidden rows: `.estate-financials-table .data-table__scroll { max-height: 176px }` at 1440 (300px at ≤640, `estateFinancials.css:12,71`) hides both EV rows in the clean 4-row state. That cap is the W3-02 c4 ruling.
  - **Default:** remove the internal vertical cap at both widths. The register then grows with the page (rows are bounded by paging, if any; confirm), and a horizontal scroll stays at 390. This needs an Architect cap (see E).

**Q13 - B11-12 / R307 Portfolio scope disclosure.** Up to 23,700 characters of UUIDs in a 320px box (`EstatePortfolio.tsx:508-556`, `estatePortfolio.css:119`), plus raw `Cold-chain · UNKNOWN`, raw `line_key · group_key · REASON_CODE` exclusions, and `0 surviving VERIFIED outcomes`.

**Default:**
- The Site/assessment cell becomes `{site_name} · {n} selected assessment(s)`, or "No selected assessment".
- The IDs move into a nested per-Site `Disclosure` "Assessment IDs", with its own `max-height: 160px; overflow:auto`.
- Scope coverage words come from `SITE_STATE_WORDS` (UNKNOWN → "Not yet assessed", CURRENT → "Current", and so on).
- Exclusions become `{Site/line label} · {reason words}`, with raw keys behind a per-exclusion detail.
- The drawer stays at 320px.
- Reason-code words need a dictionary. **Default:** reuse `portfolioWords.ts` where codes exist; an unknown code shows "Excluded from comparison", with the code in the detail.

**Q14 - B11-13 / R308 refused windows on `globalevidence`, `globalfinancials` and `portfolio`.** The backend returns one `INVALID_WINDOW` code for malformed, reversed and over-31-day windows (`backend/.../estate/scope.py:114-121`). Copy differs by client:
- Portfolio: `estateClient.ts:370`
- Evidence and Financials: `estateEvidenceMoneyClient.ts:211`

The date line `estateShared.tsx:113` echoes the reversed range "Window 2026-10-07 to 2026-10-05".

**Default:** frontend only. Classify from the page query:
- from ≥ to → reversed copy;
- span > 31 days → length copy;
- anything else → current generic copy.

Use the Q3 sentences in both clients. On refusal the window line reads "Window not valid" rather than echoing the dates. These are shared helpers, so `findings` and `actions` (batch-10 `refused-33d`) change too. That is regression reach, and they are recaptured anyway.

## C. Copy literals needing a ruling

Q5 title suffix; Q7 four sentences; Q11 "Related records"; Q12 "Limits" line; Q13 "{n} selected assessment(s)", "Assessment IDs", "Excluded from comparison"; Q14 two sentences and "Window not valid"; Q10 EV Backup cell wording.

**Q15 - one approval:** accept the literals above as written, or rewrite them in the ruling.

## D. Tests that will break or need adding

**Q16.** Frontend:
- `estateRoots.test.tsx`: :160 and :491 title, :356 window copy, :411 and :413 partial copy; :463 and :487 stay unless Q6 changes.
- `estateFixtures.ts:112`.
- `estateEvidence.test.tsx`: :113 and :502 EV href, :309 ACT-049.
- `estateFinancials.test.tsx`: :122 and :420 EV site href. This file is **not listed in the card**; add it.
- `estatePortfolio.test.tsx`: :134, :174-177, :399.
- `portfolioFixtures.ts:188`.

Backend:
- `test_w303_portfolio_api.py:226`
- `test_w303_portfolio_scope_snapshot_postgres.py:150-154,287,301,312`
- `test_w303_portfolio_comparison_postgres.py:252,321`
- `test_w302_evidence_api.py:240,287`
- `test_w302_evidence_links_postgres.py:120`
- `test_w302_money_api.py:162`
- `test_w301_estate_api.py:258` (only if Q5 takes the backend option)
- financials limit-string assertions (Q12; grep at build)

**Default:** update all of these. Add:
- pending vs missing-selection named-Site copy;
- 390 unclamped title (CSS source);
- EV `/ev` Site link;
- cold and EV windowed Finding link, plus its null fallback;
- matrix destinations per domain;
- the scope disclosure summary with IDs only inside the nested detail;
- reversed vs over-31 refusal copy and no echo.

Backend Postgres tests run as one scoped batch once the machine is idle. No full backend suite is needed, because there is no schema change (tiered policy), unless the Architect wants one.

## E. Caps (lesson 15)

**Q17 - the docket has no rows for any W3 screen.** The card says "apply the measured docket", but there is nothing to apply. Likely misses:
- **Findings across the estate** (390): unclamped 160-character titles in a 152px column wrap to about 8 lines each. Five worst-case rows come to roughly 5×150 + header, about 900px.
- **Consequence register** (Q12): with the 176px cap removed, five rows of 160-character limits come to about 450px at 1440 and about 800px at 390.
- **Capability coverage** (B11-04, D2 R299): keeps its existing internal scroll, so it is not changed here.
- **Portfolio Where management should act first**: keeps `max-height:604px` (`estatePortfolio.css:110`), but adding Finding links does not change its height.
- **Scope disclosure**: user-opened, so it is exempt.

**Default caps for the Architect to confirm, from estimates; a worst-case remeasure goes in the packet:**

| Screen | Panel | 1440 | 390 |
| --- | --- | ---: | ---: |
| findings + 3 lenses | Findings across the estate / lens panel | 700 | 1100 |
| actions | Managed actions | 600 | 900 |
| globalfinancials | Consequence register | 650 | 1000 |
| portfolio | Where management should act first | existing 604 inner scroll, panel ≤ 800 | ≤ 1000 |
| portfolio | Objectives across the estate | 450 | 600 |

All-disclosures-open is exempt. If a remeasure exceeds a cap: tighten wrap or paging, then return with measurements.

## F. Producers, recapture and capture gaps

**Q18 - KOBO-001 landing producer.** The ruling says "reuse the reviewed W1-F5b producer/mode", but W1-F5b has no serve mode of its own. Its parts used s404, s405 and s408 walkthroughs (`tools/s404_finding_index_walkthrough.py serve`, KOBO only, day 2026-10-15), and none of them seed COLD or EV. The estate pages need the W3-03 (`.agent/W3-03-evidence/test_serve_portfolio.py`) and W3-01/W3-02 harnesses. Their KOBO 503 `SITE_STORE_UNAVAILABLE` came from the stale ignored `var/sites/kobo-001.yaml` in the worktree, which batch 10 fixed by moving `var/sites` aside (B18-18 family).

**Default:**
1. Run the W3 harnesses with `var/sites` moved aside, as batch 10 did. The estate rows' KOBO links then land in the same producer. Record that as the landing proof.
2. Also capture, with s404 `serve`, the exact estate-emitted KOBO Finding URL shape (`/sites/KOBO-001/findings/{id}?revision_id=`) and the Site route landing at 1440 and 390, as the W1 producer proof the ruling asks for.

If step 1 still gives 503, step 2 is the only landing proof and the estate-page landing is a capture gap.

**Q19 - recapture set.** Every indexed case, using `batch-10/tools/mk_targets.py` and `capture-b10.mjs` (62 pairs) and `batch-11/tools/mk_targets.py` and `capture-b11.mjs` (66 pairs): 128 pairs on the current SHA.
- batch-10 cases (5 screens): positive, no-window, historical, pending, page-two-pending, partial, partial-wide, refused-33d, state-merged-empty, empty-day.
- batch-11 cases (3 screens): w303-positive, partial, historical, pending, refused-reversed, refused-over-31d, no-window, empty-foreign-tenant, 401, 503, w302-positive, partial-week, pending-late-kobo.

Add:
- link-destination checks (not counted) for EV `/ev`, cold and EV windowed Finding links, and every matrix destination per domain;
- the Q18 KOBO landing pairs;
- `refusal-409` through the newly allowed capture-only "Load more Findings" click, as a separate viewer-state pair.

Ports, DBs and tools follow the batch records (W3-01 9741/`w301cap_test`, W3-03 9781/`W303_DB`, W3-02 9751/`w302j_test`). Only one producer runs at a time.

**Q20 - capture gaps. Default:** record each as a gap with a pure selected-DTO render test in its place:
- populated Cost/Risks/Opportunities lens rows (later bootstrap ruling);
- five 160-character worst-case rows (render fixture for cap proof);
- cold and EV Actions (R02/R04);
- an EV row in the Portfolio priority table (the W3-03 fixture has none);
- several pending Sites at once (named-list copy);
- an EV Backup N/A cell.

## G. Other points

**Q21 - visible raw IDs in Portfolio Finding cells** ("Finding COLD-LAB-001 · <uuid>", `EstatePortfolio.tsx:186`). This is B1-53, cited, and not a W3 D3. **Default:** leave it as it is, unless the Architect folds it into Q13's ID work. Moving the UUID into the existing detail pattern would be a one-line change.

**Q22 - Time basis ruling** (estate roots say `UTC` in the header; rows show Site-local times when opened). No W3 D3 ID names it. **Default:** out of scope. The current window line already says "(UTC days)".

**Q23 - estimated size.** The work is five units: links backend (Q9/Q10), selected copy (Q5/Q7/Q11/Q14), long content (Q8/Q12/Q13), tests, and recapture. The backend link work is the risk.
