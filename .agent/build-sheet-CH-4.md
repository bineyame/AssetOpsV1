# Build sheet CH-4: opportunity threads (the opportunity is a Finding thread under Grow)

- Architect: Claude, 2026-11-04 (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). Rulings in §1 are logged in the plan as **CH4-R**.
- Plan: `Docs/demo-sprint/client-demo-plan.html` §2.1 CH-4 row (5 units, unchanged), lane 2.
- Design: `Docs/demo-sprint/implementation-logic-design-proposal.html`:
  - AG-25 (OD-5: the opportunity is a Finding thread, lens Opportunity, moves Grow);
  - §5b.1 `PRODUCTIVE_USE_HEADROOM@1` (rule "eligible_days >= 1 of last 5", subject SITE);
  - §6 S4 (opportunity → thread → Findings › Opportunities row · Portfolio "1 opportunity");
  - §8b item 5 (fixed text panels), §12 (headroom thread from OPP-000003 and OPP-000004), §14 D4.
- Register: I-06 (High), I-18 (Low). I-17 (the value line) stays with CH-9.
- Mock: v70 `findings-opportunities` (`screens.js:809-812` `oppListPanel`, "Opportunities to grow"), `portfolio` (`portfolio.js:45` strip "1 opportunity: Kobo daytime solar"; `portfolio.js:53` panel "An opportunity beyond reducing cost"). Measurements: `.agent/MA-1-mock-measurements.md:268-296` (Opportunities to grow 1161 px wide at 1440, 360 at 390).
- Branch: `task/CH-4-opportunity-threads`, cut from main `da5b18391` (CH-3 merged). CH-1b may merge first. CH-4 adds no migration, so no rebase of migration ids.
- Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`. Lines are to `da5b18391`.

## 0. Result and boundary

**Observable result** (ST-1, ST-3; COH-6 passes with no expected entries):
- **Findings › Opportunities** (`/findings/opportunities`) shows an **"Opportunities to grow"** panel. It holds one row per opportunity thread seen in the period: "Daytime solar unused at Kobo", how often it was seen, and its evidence in words. The lens table lists the same item with Lens "Opportunity". The **All findings** table lists it too.
- **Portfolio:**
  - the strip reads "1 opportunity: Kobo daytime solar" (the count comes from data);
  - the "An opportunity beyond reducing cost" panel is filled from the same item;
  - the fixed `UNSUPPORTED` / "Not established" claims are gone.
- **Kobo board:** the Grow row's Opportunity issue links to the opportunity page (`/sites/KOBO-001/opportunities/<id>`), not the renewable page, when a study covers the board's five days (I-18).
- **Placement:** only a study with at least one eligible day becomes an occurrence. On the polish data, the Kobo headroom thread holds OPP-000003 and OPP-000004 (design §12), not OPP-000001 and OPP-000002 (0 eligible days).

**Not in this slice.**
- The Grow row's potential slot and its money (CH-6, `priced_energy@1`).
- The daylight-window read and a SUPPORTED study (CH-9; I-17).
- `routeFor`/refs on the client (CH-5a2). CH-4 emits a `ref` object beside each new link, and CH-5a2 consumes it.
- Site-scoped lens routes and the one ThreadList (CH-5b).
- The Portfolio priority table rows (CH-6; see MD-CH4-1).
- No change to the opportunity model, the renewable rules or the study status rule (`B/mini_decisions/projection.py:163-194`). Any such change is High.

## 1. Architect rulings (CH4-R; none needs the owner, MD-CH4-1 is reported to the owner)

| # | Gap (code reality) | Ruling |
|---|---|---|
| R1 | CH-2 places **every** OPP revision as an occurrence (`B/chain/threads.py:96-110`), so OPP-000001 and OPP-000002 (0 eligible days, `UNKNOWN`) open the thread on 25 Oct. The design rule is "eligible_days >= 1" (§5b.1). | **Fixed (DS-R1).** An OPP revision is a Source only when its `result.eligible_days >= 1` (`OPP_MIN_ELIGIBLE_DAYS = 1` in `B/chain/threads.py`, comment "→ catalogue `finding_types.PRODUCTIVE_USE_HEADROOM@1.rule` (CH-8)"). A study whose first revision has 0 eligible days and a later revision ≥ 1 is placed on that later revision (sources are read in `(created_at, id)` order; `UNIQUE(opportunity_id)` keeps one occurrence). `expected-threads.json` `kobo-headroom` becomes `["OPP-000003", "OPP-000004"]`. |
| R2 | The OPP episode is the whole study window (CH2-R M1), so the thread reads OPEN on days before anything was seen (OPP-000003 is 27–31 Oct, but only 31 Oct is eligible). | **Refines CH2-R M1.** The episode is the eligible days, which are stored story times: `episode_start` = Site-local start of the first `ELIGIBLE` `day_rows[].local_day`, and `episode_end` = Site-local start of the day after the last `ELIGIBLE` day. The study window stays on the item (`study.first_day`/`last_day`). |
| R3 | I-18: two headroom rules. `summarize_renewable` spans eligible hours (min low, max high; `B/mini_depth/rules.py:396-401`). The study takes min low, min high over eligible days (`B/mini_decisions/projection.py:178-183`). `opportunity_kwh` holds a one-hour kW bound. | **The two are different claims, and both stay, each named by what it says.** Board and renewable page: the observed range ("25–31 kW of daytime solar unused", unchanged). Study value: the room available on **every** eligible day. Move the study's three lines unchanged into `B/mini_depth/rules.py` `headroom_on_every_eligible_day(bounds) -> Bound \| None`. `projection.py:178-183` calls it. Add the name `observed_headroom_range` as an alias of the existing span helper; there is no second copy of either rule. The stored key `opportunity_kwh` stays, because revisions are immutable and hashed (`input_sha256`). New wire fields name the unit: `headroom_kw` plus `window_hours: 1`. |
| R4 | The Findings index pages Finding rows with a token and cursor over `(episode_start, finding_id)` (`B/estate/index.py:289-330`). Adding non-Finding rows there would break the cursor, `finding_id` typing and COH-4. | Opportunity items are a **separate, unpaged array** `opportunities` on the Findings body (lens `all` and `opportunities`) and inside the Portfolio `opportunity` block. They are built by one function, so both screens show the same items. They are bounded by the number of Sites, with at most one per thread. The browser appends them to the lens table on page one only. `total_count` stays the Finding count, and `summary.opportunity_count` is new. |
| R5 | Lens and outcome link for a thread (OL-1). | Two pure helpers in `B/outcomes/outcome_map.py` (the only declaration): `thread_signal_key(mechanism) -> str` (`"PRODUCTIVE_USE_HEADROOM"` → `"SIGNAL:PRODUCTIVE_USE_HEADROOM"`, else `finding_signal_key(mechanism)`); `lens_flags(signal_key, domain) -> list[str]` = `[LENS_OF_CATEGORY[c]]` for the category of the **primary** moved outcome (`moves[0]`), with `LENS_OF_CATEGORY = {"OPTIMIZE_COST": "COST", "PROTECT_ASSET": "RISK", "GROW_REVENUE": "OPPORTUNITY"}` and `ASSURE_PERFORMANCE` → `[]`. CH-4 applies them to opportunity items only. CH-5a2 applies `lens_flags` to Finding rows (I-21). Whichever slice merges second reuses these names. |
| R6 | An opportunity whose studies all drop to 0 eligible days. | **SUPPORT_LOST for opportunities.** In `B/chain/lifecycle_run.py:71-89` `thread_causes`, an opportunity thread whose every occurrence's selected head revision at the run has `eligible_days = 0`, with no linked Action, gets `SUPPORT_LOST` (cause id = the latest such revision id, known at its `created_at`). The existing transition `OPEN → WITHDRAWN` applies. |
| R7 | Board signal source. The board's `SIGNAL:PRODUCTIVE_USE_HEADROOM` is open from the renewable cards (`B/site_outcomes/mini.py:428-429`), not from the thread. | **Labelled keep → CH-6** (potential node reads the thread, design §6 S4). CH-4 changes only the link and the issue `ref` (§4.4). COH-6 keeps judging per estate window (§6). |

## 2. Data contract (additive; no migration)

### 2.1 The opportunity item (one shape, shared by Findings and Portfolio)

```json
{"thread_id": "uuid", "site_id": "uuid", "site_code": "KOBO-001", "site_name": "<site.site_name>",
 "mechanism": "PRODUCTIVE_USE_HEADROOM", "domain": "MINIGRID",
 "title": "Daytime solar unused at <site_name>", "short_label": "<site_name> daytime solar",
 "state": "OPEN", "state_label": "Open", "state_effective_day": "2026-10-31", "state_day": "2026-11-01",
 "occurrences": 2,
 "study": {"opportunity_id": "uuid", "code": "OPP-000004", "first_day": "2026-10-28", "last_day": "2026-11-01",
           "status": "LIMITED", "eligible_days": 2, "assessed_days": 4,
           "headroom_kw": null, "window_hours": 1},
 "evidence": "LIMITED", "evidence_label": "Limited evidence",
 "seen_line": "Seen on 2 of 4 well-observed days · 28 Oct–1 Nov",
 "value_line": null,
 "limit_line": "Limited evidence: readings come from mixed sources, so the size is not worked out yet",
 "lens_flags": ["OPPORTUNITY"], "categories": "<categories_for(thread_signal_key(mechanism), domain)>",
 "filter_state": "unconfirmed",
 "links": {"opportunity": "/sites/KOBO-001/opportunities/<opportunity_id>",
           "evidence": "/sites/KOBO-001/performance/renewable?from=<first_day local 00:00 as UTC Z>&to=<day after last_day>",
           "site": "/sites/KOBO-001"},
 "ref": {"kind": "OPPORTUNITY", "site": "KOBO-001", "id": "<opportunity_id>"},
 "thread_ref": {"kind": "THREAD", "site": "KOBO-001", "id": "<thread_id>"}}
```

**Selection rules** (pure, `B/chain/opportunities.py` `opportunity_items(rows, window_from, window_to, k, policy)`):
- **Visible occurrence:** `coalesce(source_known_at, joined_at) <= k` (CH3-R D-b), where `k` is the read's resolved cutoff (Findings and Portfolio: the envelope's `window.known_at`; board: the board cutoff, or none = as known now).
- **Study head:** the latest `mini_opportunity_selection` with `selected_at <= k` (by `selected_at DESC, seq DESC`, as `mini_opportunity_head`, `M/0030:190-191`).
- **Seen in the window:** the occurrence's episode (R2) intersects the Site-local days `[local_day(window_from), local_day(window_to − 1 µs)]` in the Site's own zone (AG-27). The head must have `eligible_days >= 1`.
- **One item per thread,** built from its latest seen study (max `last_day`, then max `public_no`). `occurrences` = the thread's visible occurrences.
- **`state`:** the thread state on the Site-local day of `window_to − 1 µs`, as of `k`. Use `lc.thread_view` exactly as Finding rows do (`B/chain/lookup.py:72-80`). An item whose state is `WITHDRAWN` is still listed, with `filter_state` `no_longer_supported`.
- **Order:** `(site_code, −study.last_day ordinal, study.code)`.
- **`evidence`** = `study.status`. **`filter_state`:** SUPPORTED → `supported`; LIMITED or UNKNOWN → `unconfirmed`; WITHDRAWN → `no_longer_supported`. The index `state` filter applies to items by this field.

### 2.2 Copy (server-rendered; `B/chain/vocabulary.py`, new, the seed of the AG-29 vocabulary layer)

| Key | Literal |
|---|---|
| `OPP_TITLE["PRODUCTIVE_USE_HEADROOM"]` | `"Daytime solar unused at {site}"` |
| `OPP_SHORT["PRODUCTIVE_USE_HEADROOM"]` | `"{site} daytime solar"` |
| `SEEN_LINE` | `"Seen on {e} of {a} well-observed days · {first:%-d %b}–{last:%-d %b}"`; one day: `"… · {first:%-d %b}"` |
| `VALUE_LINE` (SUPPORTED, `headroom_kw` set) | `"{lo}–{hi} kW at midday on every eligible day"`; `lo == hi`: `"{lo} kW at midday on every eligible day"` |
| `LIMIT_MIXED` (LIMITED, a `SOURCE_CLASS_MIXED` or `SOURCE_CLASS_UNKNOWN` limitation) | `"Limited evidence: readings come from mixed sources, so the size is not worked out yet"` |
| `LIMIT_DAYS` (LIMITED, otherwise) | `"Limited evidence: {n} of the 5 study days lack a reading needed to size it"` (`n` = days with decision LIMITED or CONFLICT) |
| `LIMIT_UNKNOWN` (UNKNOWN) | `"Not judged yet: {n} of the 5 study days have no reading"` (`n` = days with no decision) |
| `EVIDENCE_LABEL` | SUPPORTED `"Supported"`, LIMITED `"Limited evidence"`, UNKNOWN `"Not judged yet"` |
| `THREAD_STATE_WORDS` | OPEN `"Open"`, ACTION_IN_HAND `"Action agreed"`, CHANGE_APPLIED `"Change made"`, RESOLVED_MONITORING `"Checked and working, monitoring"`, CLOSED `"Closed"`, RECURRED `"Seen again"`, REOPENED `"Reopened"`, WITHDRAWN `"No longer seen"` (MA-1 M4 timeline words; CH-5a2 reuses them) |
| `OPP_NONE` | `"No opportunity found in this period"` |

- `%-d` is the day number without padding, as in CH-3. Use the existing `_MONTHS` helper (`B/site_outcomes/board.py:120`) or an equivalent in the module; do not depend on the platform's `strftime`.
- Numbers use `decimal_text` (`B/mini_decisions/projection.py`).
- Run the vocabulary guard (V). New lines are MOCK DEVIATION candidates against MA-1 M5 (§7).

### 2.3 Body changes

- **Findings** (`estate-finding-index-2`, `B/estate/index.py:289-330`), additive:
  - `opportunities: [item…]` when `lens in ("all", "opportunities")`, else `[]`, filtered by the request's `state` filter (§2.1);
  - `summary.opportunity_count: int` (items before the state filter).
  - Finding `rows`, the order, `total_count`, the token and the cursor are unchanged.
- **Portfolio** (`B/estate/portfolio.py:797-798`), replacing the literal:
  ```json
  "opportunity": {"state": "FOUND" | "NONE", "items": [item…], "finding_id": null, "scenario_amount": null,
                  "headroom": <items[0].study.headroom_kw or null>, "destination": "/findings/opportunities"}
  ```
  - `summary.opportunity_count` (`:760-761`) = `len(items)`, replacing the lens-flag count over Finding members.
  - New `summary.opportunity_labels` = `[i["short_label"] for i in items]`.
  - Both are null only when the opportunity read raised (stated in the packet; the page then reads "Unknown").
- **Value cards** (`:352-353`, `:362`, `:404-409`):
  - `("PRODUCTIVE_USE", "FOUND"): (None, "Listed under Findings › Opportunities", "green")`, with detail `" · ".join(short_labels)`;
  - `("PRODUCTIVE_USE", "NONE"): ("No opportunity found in this period", "Listed under Findings › Opportunities", "neutral")`;
  - remove `("PRODUCTIVE_USE", "UNSUPPORTED")`, and set `CARD_DESTINATION["PRODUCTIVE_USE"] = "/findings/opportunities"`.
  - `ASSET_LIFE` is untouched (SWEEP-DS).
- **Opportunity detail** (`GET /api/sites/{code}/opportunities/{id}`), additive: each `day_rows[]` gains `headroom_kw` (the same bound as `opportunity_kwh`) and `window_hours: 1` (R3). Nothing else changes.
- **Board** (§4.4): the OPPORTUNITY issue's `ref`, today `None` (`B/site_outcomes/board.py:742`), becomes `{"opportunity_id", "code", "thread": <public thread>}` when §4.4 finds a study, else stays `None`.

## 3. The read: one SQL text, two executors

- **`B/chain/lookup.py`** gains `OPPORTUNITY_LOOKUP`, one statement. Both read adapters execute it: the estate snapshot (`B/estate/adapters/postgres_estate_read.py:329` beside `threads`) and the board's `PostgresThreadSources` (`B/chain/adapters/postgres_thread_sources.py:161`). There is no second copy of the SQL.

```sql
WITH oc AS (
  SELECT o.thread_id, o.occurrence_no, o.opportunity_id, o.episode_start, o.episode_end, o.joined_at,
         o.source_known_at, o.site_id
    FROM finding_thread_occurrence o
   WHERE o.tenant_id = :t AND o.opportunity_id IS NOT NULL
     AND CAST(o.site_id AS text) = ANY(CAST(:s AS text[]))
     AND (CAST(:k AS timestamptz) IS NULL OR coalesce(o.source_known_at, o.joined_at) <= CAST(:k AS timestamptz))),
head AS (
  SELECT DISTINCT ON (x.opportunity_id) x.opportunity_id, x.revision_id
    FROM mini_opportunity_selection x JOIN oc ON oc.opportunity_id = x.opportunity_id
   WHERE x.tenant_id = :t AND (CAST(:k AS timestamptz) IS NULL OR x.selected_at <= CAST(:k AS timestamptz))
   ORDER BY x.opportunity_id, x.selected_at DESC, x.seq DESC)
SELECT 'O' AS kind, CAST(oc.opportunity_id AS text) AS ref, CAST(oc.thread_id AS text) AS thread_id,
       oc.occurrence_no AS num, oc.episode_start, oc.episode_end, m.public_no, m.first_day, m.last_day,
       r.result->>'status' AS status, CAST(r.result->>'eligible_days' AS int) AS eligible_days,
       CAST(r.result->>'assessed_days' AS int) AS assessed_days, r.result->'headroom_kw' AS headroom_kw,
       (SELECT jsonb_agg(l->'code') FROM jsonb_array_elements(r.result->'limitations') l) AS limitation_codes,
       (SELECT jsonb_agg(d->'decision') FROM jsonb_array_elements(r.result->'day_rows') d) AS decisions,
       s.timezone, s.site_code, s.site_name, s.site_type, t.mechanism
  FROM oc JOIN head h ON h.opportunity_id = oc.opportunity_id
  JOIN mini_opportunity_revision r ON r.tenant_id = :t AND r.id = h.revision_id
  JOIN mini_opportunity m ON m.tenant_id = :t AND m.id = oc.opportunity_id
  JOIN finding_thread t ON t.id = oc.thread_id
  JOIN site s ON s.tenant_id = :t AND s.id = oc.site_id
UNION ALL <the event rows of those threads, the 'E' branch of LOOKUP unchanged, :k applied in pure code>
```

- The column list is illustrative. Keep the `LOOKUP` 11-plus-extras tuple convention, or return named rows. The pre-flight states which (P7).
- A database below 0042 returns no rows (`to_regclass` check, as `:333-335`).
- There is one query per request for all Sites.
- **Pure reducer:** `opportunity_items(rows, window_from, window_to, k, close_after)` in `B/chain/opportunities.py`, as §2.1. It calls `lc.thread_view` (P5).
- **Placement change** (R1, R2):
  - `_OPPORTUNITY_SOURCES` (`postgres_thread_sources.py:32-38`) adds `CAST(r.result->>'eligible_days' AS int) AS eligible_days` and `r.result->'day_rows' AS day_rows`.
  - `opportunity_source` returns `None` below `OPP_MIN_ELIGIBLE_DAYS`, and its episode follows R2.
  - The backfill and the live stage skip `None` and report the count as `skipped_ineligible` in the step JSON.

## 4. Where it is used

1. **Findings** (`B/estate/index.py` `_findings`, `:289-330`): after `select_finding_scope`, one call `snap.opportunity_threads(tenant, [site ids of per_site with domain MINI_GRID … all Sites], req.from_, req.to, scope["k"])`, then `opportunity_items(...)`.
   - Every authorized Site is passed. Sites with no headroom thread return nothing. No Site-type branch is written.
   - Add `opportunities` and `summary.opportunity_count`.
2. **Portfolio** (`B/estate/portfolio.py` `_portfolio`, `:666-810`): the same call on the same snapshot after `attach_threads` (`:673`). The items feed the `opportunity` block, the value card and the summary counts.
3. **The "Opportunity index unavailable" helper** (`F/sites/SiteFindingIndex.tsx:89-115`). The text becomes false once Findings › Opportunities lists the item.
   - **Fixed (DS-R1):** the text becomes `"Opportunities for this site are listed under Findings › Opportunities."`, with "Findings › Opportunities" linked to `FINDINGS_OPPORTUNITIES_PATH`.
   - `OPPORTUNITY_INDEX_HELPER` and its test change together. The renewable link stays as the second sentence: `" The five-day solar study is on the renewable page."`, with "renewable page" linked as today.
4. **Board** (`B/site_outcomes/read.py:396-416` and `B/site_outcomes/board.py:914-923` `with_threads`).
   - `self.s.threads.lookup` gains `opportunity_window=(lo, hi)`, the renewable five days `renewable_bounds(start, tz)` (`mini.py:514`), for MINI only, plus the cutoff.
   - `with_threads` replaces the `SignalFact("SIGNAL:PRODUCTIVE_USE_HEADROOM", …)` href with `links.opportunity` of the item whose episode intersects that window, and sets the issue `ref` (§2.3).
   - With no item, the href stays `renewable_href(...)`. The signal's `open` flag is unchanged (R7).

## 5. Frontend (`F/`)

- **`F/estate/estateClient.ts`:**
  - `EstateOpportunity` (§2.1);
  - `EstateFindingsBody.opportunities?: EstateOpportunity[]` and `summary.opportunity_count?: number | null`;
  - `EstatePortfolioBody.opportunity` → `{ state: "FOUND" | "NONE"; items: EstateOpportunity[]; finding_id: null; scenario_amount: null; headroom: {low: string; high: string} | null; destination: string }` (`:376`);
  - `summary.opportunity_labels?: string[]`.
  - Parsers accept absent fields: an older body reads `[]` / `NONE`.
- **`F/estate/findingIndex.tsx`:**
  - New `OpportunityList({ items })`: `Panel` heading `"Opportunities to grow"`, note `"Each opportunity is one row · open it for the detail"` (mock `screens.js:812`).
    - Each `li` holds: the title, linked to `links.opportunity`; `<small>` `seen_line` + (`value_line` ? `" · " + value_line` : ""); `<small className="opp-limit">` `limit_line` when set; and the right link `"Inspect the solar room →"` to `links.evidence`.
    - Render it above the lens table when `lens === "opportunities"` and items exist (mock order).
  - **Table rows** for items (lens `all` and `opportunities`, page one only, after the Finding rows):
    - Finding: `"{study.code} · {title}"` linked to `links.opportunity`;
    - Site: the existing Site link;
    - Priority and Confidence: `"Not assessed"` and `evidence_label`;
    - State: `state_label`;
    - Main consequence: `value_line ?? "Size not worked out yet"`;
    - Lens: `"Opportunity"`.
    - Use `data-estate-opportunity={thread_id}`.
  - `LENS_EMPTY.opportunities` (`:81`) shows only when there are no Finding rows and no items.
- **`F/estate/EstatePortfolio.tsx`:**
  - `OpportunityPanel` (`:385-417`) becomes `OpportunityPanel({ body, window })`:
    - **FOUND:** use `items[0]`.
      - Left: quantity `study.headroom_kw ? "{lo}–{hi}" + <small>"kW at midday"</small> : "Size not worked out yet"`, and p = `title`.
      - Right: quantity `"No what-if yet"`, p `"No what-if value worked out yet"` (existing).
      - `chart-note` = `seen_line` + (limit ? " · " + limit : "").
      - Bottom: `<Link to={links.opportunity}>Review opportunity Finding →</Link>` and `<Link to={links.evidence}>Inspect physical headroom →</Link>` (mock literals).
      - With more than one item, add `<Link to="/findings/opportunities">{n − 1} more under Findings › Opportunities →</Link>`.
    - **NONE:** left quantity `OPP_NONE`, p `"Nothing seen on the days checked"`; the right side as FOUND; bottom one link `"Findings › Opportunities →"`.
    - Both `MissingClaim` spans (`:408-413`, gap `G-portfolio-opportunity`) are removed. Retire the gap's catalogue entries (P4).
  - **Strip** (`:708-718`): the opportunity `PulseCount` is replaced by `<span data-portfolio-pulse-opportunity><strong>{n}</strong> {n === 1 ? "opportunity" : "opportunities"}{labels.length ? ": " + labels.join(" · ") : ""}</span>`, with n null → `"Unknown"`.
    - Delete the WALK1-6 D5 comment, `openOpportunitySuffix` and `openOpportunitySiteCount` (`F/estate/PortfolioOutcomes.tsx:162-177`) once P3 confirms no other reader. The contradiction they papered over no longer exists.
- **CSS:** reuse the mock's `.opp-list` / `.opp-limit` rules (`frontend/mockups/v70/mockups.css`; copy into the existing estate stylesheet). Fit at 1440 and 390 with no horizontal scroll (measured caps: `.agent/MA-1-mock-measurements.md:273,289`).

## 6. Coherence rules (`tools/checks/chain_coherence.py`, `test_chain_coherence.py`, fixtures)

- **COH-6 (`:529-553`), updated:**
  - "Findings has a row" now reads `findings_opp.{w}` `opportunities` (any item with the board's `site_code`);
  - "Portfolio not denied" now reads `portfolio.{w}.opportunity.state == "FOUND"` and an item for the Site.
  - Delete the 6 COH-6 entries from `expected-today.json`.
- **COH-10 (`:710-770`), extended:**
  - `expected-threads.json` `kobo-headroom` lists `["OPP-000003", "OPP-000004"]`; the note "COH-10 skips it" is removed;
  - the Findings item's `thread_id`, the Portfolio item's `thread_id` and the board OPPORTUNITY issue's `ref.thread.id` must agree for the same Site and window;
  - `occurrences` must equal the expected count wherever the window holds both studies.
- **COH-16, opportunity agreement (new):** for each estate window, the Portfolio `opportunity.items` and the Findings (lens opportunities) `opportunities` hold the same set of `(thread_id, study.code, state, evidence)`.
- **Fixtures:** `clean_opportunity` (pass), `coh6_opportunity_missing` (Findings empty while the board shows one), `coh16_opportunity_disagree`. Add them to `RULES` (`:949-954`).

## 7. DS-R1, OL-1 and mock deviations

| Item | Touched how | Resolution |
|---|---|---|
| Fixed claim: Portfolio PRODUCTIVE_USE "Not established" (`portfolio.py:352-353,362,408`) | Replaced | **Fixed:** FOUND or NONE from data |
| Fixed claim: Portfolio opportunity `UNSUPPORTED` (`portfolio.py:797`), and the panel text (`EstatePortfolio.tsx:385-417`) | Replaced | **Fixed:** from the opportunity items |
| WALK1-6 D5 workaround: a board count beside a Findings count (`PortfolioOutcomes.tsx:162-177`, `EstatePortfolio.tsx:708-716`) | Removed | **Fixed:** one count from one source |
| 0-eligible studies placed as occurrences (`threads.py:96-110`) | Edited | **Fixed** (R1) |
| Episode = whole study window, i.e. hindsight (`threads.py:103-107`) | Edited | **Fixed** (R2): eligible days |
| "Opportunity index unavailable" (`SiteFindingIndex.tsx:89-90`) | Edited | **Fixed** (§4.3) |
| One-noon-hour headroom basis; board signal from the renewable cards | Link only | **Labelled keep** → CH-9 (daylight window) and CH-6 (potential node) |
| `opportunity_kwh` key name in stored revisions | Not renamed (immutable) | **Labelled keep** (R3): the wire adds `headroom_kw` + `window_hours` |
| ASSET_LIFE "Not established" | Not touched | SWEEP-DS |
| "Verified on example data" | Not touched | CH-5a2 |

**OL-1.** Items get categories and lens only through `outcome_map.thread_signal_key` / `categories_for` / `lens_flags` (R5). No outcome id literal or map key is constructed outside `outcomes/outcome_map.py`. The CH-6 ratchet baseline does not grow.

**MOCK DEVIATION candidates** (the packet lists each with its label):
- **MD-CH4-1:** the Portfolio priority table has no opportunity row (mock `portfolio.js:23` F-109). Rows come from EstateChain in CH-6, which lists threads of every lens. Until then the opportunity shows in the strip and the panel directly below. **Reported to the owner.**
- **MD-CH4-2:** no Depot "Chargers mostly idle" item (mock `screens.js:812`). There is no EV opportunity producer, and `WARNING:CHARGERS_MOSTLY_IDLE` has no rule (`B/outcomes/warnings.py:49-57`). This is post-demo, with CH-8.
- **MD-CH4-3:** the item shows its study code (`OPP-000004`), not an F-number.
- **MD-CH4-4:** the panel's right side reads "No what-if yet" instead of the mock's "$2.50": no reviewed scenario exists. This is an honest missing state.
- **MD-CH4-5:** the Kobo item reads "Limited evidence: readings come from mixed sources…" until CH-9 makes the study single-source.

## 8. Localised test ladder

1. **L0:** `tools\run-host-tests.ps1 -- backend/tests/test_ch4_opportunities.py`
   - `opportunity_source`: 0, 1 and 2 eligible days; episode = eligible days in Addis and in UTC; a later revision gaining eligibility is placed.
   - `opportunity_items`:
     - window intersection per Site zone, including the last instant `to − 1 µs`;
     - a hidden occurrence when `source_known_at > k`;
     - a selection after `k` ignored;
     - latest study chosen; order;
     - state and `filter_state` mapping.
   - Every copy literal in §2.2, including the singular day and `lo == hi`.
   - `thread_signal_key`, `lens_flags` (each category; ASSURE → `[]`), and `categories_for` unchanged for Finding keys.
   - `headroom_on_every_eligible_day` equals the pre-move result on the projection fixtures. The existing projection tests stay green.
   - Portfolio `opportunity` FOUND/NONE; the value card; `summary.opportunity_count` and labels.
   - SUPPORT_LOST for an opportunity thread, both directions (with and without an Action).
2. **L2:** `tools\run-host-tests.ps1 -- backend/tests/test_ch4_opportunity_postgres.py` on `pg_harness.fresh_database()` (head pin via `pg_harness.alembic_head()`).
   - Seed two studies through the mini-decisions store (`B/mini_decisions/store.py:183-215`): one with 0 eligible days, one with 2, the second with two revisions and selections.
   - Backfill step b: one thread with 1 occurrence. A rerun writes 0 rows.
   - `OPPORTUNITY_LOOKUP` through both adapters gives identical items.
   - `known_at` before the second selection gives the first revision.
   - `GET /api/estate/findings?lens=opportunities` and `GET /api/estate/portfolio` bodies carry the item (TestClient, as `test_w301_estate_api.py`).
   - Register the set-up in `setup_cache` `FUNCTION_OPS` (`backend/tests/setup_cache.py:77`).
3. **Existing, scoped** (the packet lists every importer of a changed module):
   - `test_ch2_threads.py`, `test_ch2_thread_store_postgres.py`, `test_ch2_backfill_cli.py`;
   - `test_ch3_lifecycle.py`, `test_ch3_lifecycle_postgres.py`, `test_ch3_rows.py`;
   - `test_w301_estate_api.py`, `test_w301_estate_index_postgres.py`;
   - `test_w303_portfolio_api.py`, `test_w303_portfolio_reduction.py`, `test_w303_portfolio_fixture_postgres.py`;
   - `test_out_b1_board.py`, `test_out_b2_mini.py`, `test_out_b4_board_postgres.py`;
   - the mini-opportunity projection and route tests (P6 names them);
   - `tools/checks/test_chain_coherence.py`.
   - Expected body changes are listed in the packet as old → new. Anything else is a regression.
4. **L4:** `python -m assetops_backend.chain.backfill --dry-run --steps b` on `assetops_polish_full_test` (SELECT only). It must print the headroom thread with OPP-000003 and OPP-000004 only, `skipped_ineligible: 2`, and the episodes: OPP-000003 31 Oct; OPP-000004 31 Oct–1 Nov (Addis days).
5. **L3** (as CH-3, `.agent/review-CH-3-r2.md:157-185`):
   - `python tools/chain_clone.py create ch4 --migrate`;
   - `python -m assetops_backend.chain.backfill --steps a,b,c,d` (rerun: 0 rows);
   - `python tools/chain_clone.py settle ch4`;
   - `python tools/checks/chain_coherence.py collect --work <scratch copy of the polish work dir's top-level JSON> --database-url <clone url> --out <bundle>`;
   - `check --bundle <bundle> --expect tools/checks/fixtures/chain_coherence/expected-today.json`.
   - Pass: COH-6 0 (no expected entries left), COH-10 including the headroom thread, and COH-16 0. Every other rule is as before.
   - **Report verbatim:** the week's Findings item (title, `seen_line`, `limit_line`, `state_label`), the Portfolio strip text and panel texts, and the Kobo 31 Oct board OPPORTUNITY issue `href`.
   - `python tools/chain_clone.py drop ch4`.
6. **Frontend:** `npx vitest related --run src/estate/estateClient.ts src/estate/EstatePortfolio.tsx src/estate/PortfolioOutcomes.tsx src/estate/findingIndex.tsx src/sites/SiteFindingIndex.tsx`, which includes `estatePortfolio.test.tsx`, `estateRoots.test.tsx` and `s404SiteFindingIndex.test.tsx`.
   - New cases: the panel FOUND/NONE; the strip singular and plural; the Opportunities list and table rows; the older body (no `opportunities`); a 390 px render with no overflow class.
7. **Guards, run directly** (plan §4.3): A (`tools/check-architecture.ps1`), W, N, V, M (`node tools/checks/missing-claim-scan.mjs`, after retiring `G-portfolio-opportunity`), and the chain-coherence fixtures line. Run the estate guard self-tests only if P1 needs a `configuration-persistence.ps1` edit.

## 9. Pre-flight items (answer from code, batch them, then stop)

- **P1.** Does rule 8 of the estate guard (`tools/checks/configuration-persistence.ps1`) list the tables each registered reader may read? If so, add `mini_opportunity`, `mini_opportunity_revision` and `mini_opportunity_selection` to the estate reader and the thread-sources reader. State the lines.
- **P2.** Every consumer of `body.opportunity` and of the `PRODUCTIVE_USE` value card: backend tests, `F/`, `tools/demo_combined_finish.py`, capture scripts and goldens.
- **P3.** Every reader of `summary.opportunity_count`, `openOpportunitySuffix` and `openOpportunitySiteCount`.
- **P4.** The missing-claim catalogue file and entries for `G-portfolio-opportunity` (both placements).
- **P5.** `lc.thread_view` (`B/chain/lifecycle.py`) with an opportunity occurrence: confirm it needs no Finding-only field.
- **P6.** The opportunity detail route's tests, and its `known_at` form. Does the board link need `?known_at=` when the mini board cutoff is none (expected: bare)?
- **P7.** Return shape of `OPPORTUNITY_LOOKUP`: the tuple convention or named rows. Confirm the event branch reuses `LOOKUP`'s 'E' select unchanged.
- **P8.** The L4 dry-run output (the episodes, `skipped_ineligible`), before any L3 work.

## 10. Review focus

- One item builder feeds both screens. There is no second derivation of "seen in the period" or of the opportunity copy.
- The study status rule, the renewable rules and the stored revisions are untouched. R3 moves three lines only.
- No outcome-id literal or map key outside `outcome_map.py` (OL-1).
- No fixed opportunity claim is left in `B/estate/portfolio.py` or `F/estate/EstatePortfolio.tsx`.
- Every new line comes from §2.2 and passes V. MOCK DEVIATION labels are present for MD-CH4-1 to 5.
