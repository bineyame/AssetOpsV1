# Independent spec dry-read: W3-03 Portfolio composition (2026-10-20)

Reviewer: a fresh Claude spec reviewer, read-only, worktree `AssetOpsV1-plan2` on main `65509e66`. This follows the ROLE_CONFIG rule (`.ai/ROLE_CONFIG.md:449-455`), with `.agent/W3-02-spec-review.md` and `.agent/W4-02-spec-review.md` as precedents.

Inputs:
- `.agent/W3-03-build-spec.md` (cited as `S:Lnn`) and `tasks/W3-03-portfolio-composition.md` (`T:Lnn`);
- `.agent/W3-03-mock-measurements.md` (`M:Lnn`);
- `.agent/post-W2-sequence.md` (`SEQ:Lnn`);
- `.agent/W3-01-build-spec.md` (`W301:Lnn`), all closures, the token v2 amendment, and q1–q4;
- `.agent/W3-02-build-spec.md` (`W302:Lnn`), closures 1–3;
- v69 `frontend/mockups/v69/portfolio.js:1-66`, the scope and progress drawers at `screens.js:1055-1068`, `screen-manifest.json` `portfolio`, and `v69-rendered-panels.json:4`;
- the merged code.

Method: I read the spec commit by commit, as a mid-level implementer would, and checked every named path, symbol, table and column against merged main.

**State of main.** W3-01, W3-02, W4-01, W4-02 and W4-03 are **not merged**:
- the newest migration is `0026_w2_ev_money.py`;
- `backend/assetops_backend/estate/` does not exist;
- the Portfolio, Actions, Evidence and Financials rail items are all still `unavailable` (`OperatorShellLayout.tsx:51,55,59,60`).

So every W3-01/02 symbol below (`estate/scope.py`, `coverage.py`, the parser, cursor, `estate-selection/2` builder, the W3-02 selectors, the money groups and the route builders) is marked **PREREQUISITE**. I did not verify them.

**Verified correct**, so not listed below:
- `FindingIndexService.read` is per Site, with a `start/end` `IndexRequest` and no `known_at` (`analytics/finding_index.py:82-89,231,259`);
- `SiteOverviewRead.read` is per day (`site_overview/read.py:114`);
- `ConsequenceReadService` (`financials/consequence_read.py:149`), `ActionService.action` (`actions/service.py:653`) and `actions/verification.py` all exist;
- `0009` lifecycle CHECK `SUPPORTED|UNCONFIRMED|NO_LONGER_SUPPORTED|MERGED`, with no priority or confidence column (`0009_finding_store.py:72`);
- the `0011` `amount_low/amount_high/currency` columns (`:77-79`);
- the `0023` cold CHECK that all amounts are null, with states `UNPRICED|WITHHELD` (`:61,70-71`);
- `0026` `ev_consequence_revision.finding_revision_id uuid NULL` (`:50`), and `EvUnit.append` inserting `NULL` (`postgres_consequence_store.py:~997-1000`);
- the fixture files `var/sites/kobo-001.yaml`, `backend/tests/fixtures/w2/{cold,ev}-lab-001.yaml` and `contract-fixtures/w2/{cold/normal,ev/complete}.json`;
- the four rendered Portfolio panel titles;
- the registry nodes `A-estate-comparability`, `A-estate-projections`, `D-estate-comparable-sites`, `A-estate-index-scope`, `I-estate-finding-root`, `A-estate-action-summary` and `A-evidence-shared-projections` (all `open`);
- the guard tuple `unavailable|Portfolio|OPERATIONS|` (`navigation-truthfulness.ps1:545`);
- **all eight panel budgets**. I recomputed each as `mock + max(24, 10%)`, rounded up from `M:L8-11,17-20`: 780, 851, 413, 413, 247, 272, 247 and 328. All match `S:L140-145`;
- migration `0031` is unambiguously **unused**, with no file, DDL or downgrade (`S:L11`, `T:L9`).

## Questions

### Blockers

1. **(Blocker) Wire and seams: the Portfolio `coverage.sites` shape contradicts the prerequisite closure it says it reuses.**
   - **Evidence.** `S:L31` defines items as `{site_id,site_code,domain,finding_state,evidence_state,money_state,selection_ids[],watermark,source_freshness}`. W3-02 closure Q15 (`W302:L36`) rules that estate roots reuse W3-01 `site_coverage`'s seven keys `{site_id,state,committed_watermark,selection_id,match_state,job_state,source_freshness}`, and adds *"do not replace the shape with `site_code/domain/selection_ids`"*.
   - **The implementer would decide:**
     - which shape wins;
     - how the three per-root states are derived from the three roots' differing per-Site grammars: W3-01 per-Site `state`, W3-02 Evidence placeholders, and W3-02 money category coverage (closure 3);
     - the enum of `finding_state`, `evidence_state` and `money_state` (`CURRENT|PENDING_RECOMPUTE|STALE_SOURCE|HISTORICAL|UNKNOWN|NOT_APPLICABLE`?);
     - the enum of `coverage.{state,finding_state,evidence_state,money_state}` (`COMPLETE|PARTIAL|UNKNOWN|EMPTY`?);
     - which `selection_ids` go in the array. W1 has one assessment per day, cold has two analytics, EV has an assessment plus sessions.
   - **Also:** "each Site's three domain states" (`S:L46`) uses "domain" for the roots Finding, Evidence and Money, while `domain` is also the physical Site type.

2. **(Blocker) Wire: enum spellings diverge from stored and prerequisite values.**
   - `domain:"MINI_GRID"` (`S:L31,36,37`). The stored `site.site_type` is `MINIGRID|COLDCHAIN|EV_CHARGING` (`0001_foundation_identity.py:66`), and W3-02 Q15 maps it 1:1 (`W302:L36`).
   - `status` uses `PARTIAL` (`S:L17,57`). W3-01 and W3-02 use `UNKNOWN` (`W301:L26`, `W302:L36`: `CURRENT|HISTORICAL|PENDING|UNKNOWN|EMPTY_SCOPE`).
   - W3-01 and W3-02 also separate stale from unknown in precedence. Portfolio folds stale into PARTIAL.
   - **Ruling needed:** a literal enum per field, and whether Portfolio may diverge from the shared roots.

3. **(Blocker) Cursor contract: it contradicts W3-02 closure, which rules the shared machinery.**
   - `S:L7` says "signed cursor" and `S:L23` says "Cursor `last` is the full tuple, signed with … limit and selection token".
   - W3-02 closure (`W302:L42`) rules that the cursor is **unsigned** ("not a signature"), that the tuple key is `after`, and that `limit` is **not** embedded.
   - **Ruling needed:**
     - the literal Portfolio cursor JSON, including `kind:"portfolio"`, `lens`, and whether `state_filter` is present;
     - the `after` tuple order with null `episode_start`;
     - whether `limit` is embedded.

4. **(Blocker) Wire, mock map: the footer, the SITE_OWNED card and the scope disclosure need line data the wire does not carry.**
   - `money` is `{groups,exclusions,diagnostics,estate_total}` (`S:L41`), and it has no W3-02 `rows`. `value_cards[]` has only `display_value,currency,line_keys,group_key,basis` (`S:L33`).
   - Yet the following need values with no field:
     - the footer needs `{site_name}: {quantity} {unit} · {amount} {currency}` plus the source and target route (`S:L112`);
     - SITE_OWNED subcopy needs `{site_name} · {category} · {window}` (`S:L64`);
     - COMPARABLE_GROUP needs `{window} · {line count}` (`S:L63`);
     - the scope disclosure needs "each Site's selected IDs, window, coverage, provenance and W3-02 group exclusions" (`S:L91`). There is no per-Site provenance in `coverage`.
   - **Ruling needed:**
     - a literal `footer`/`energy_context` object and a selected-lines array (or `value_cards[].basis` shape);
     - the `display_value` format (pre-formatted string or `{low,high}`? outward or half-even?);
     - how `group_key` is derived. W3-02 references `group_key` in `exclusions` (`W302:L60`) but its groups have no key field.

5. **(Blocker) Mock map: the two mock drawers are unmapped panel by panel.**
   - `Assessment scope & periods ↗` opens a drawer titled `Portfolio scope & consequence ownership` with:
     - a `Selected examples` table with columns `Site / assessment`, `Period`, `Scope`;
     - prose panels `Assessment rule` and `Value ownership`;
     - a blue notice (`screens.js:1060-1064`).
   - `Inspect basis ↗` opens `Change and verification basis` with:
     - a `Workflow facts in this review` table with columns `Source object`, `Recorded fact`, `Outcome meaning`;
     - a notice;
     - a reference paragraph (`screens.js:1065-1068`).
   - The spec says only "opens scope disclosure with …" and "opens progress disclosure with exact … IDs" (`S:L91,111`). There is no shared Drawer primitive in `frontend/src/ui/` (only `Disclosure`; `ClaimDrawer` is Site-local in `sites/findingPresentation.tsx`).
   - **Ruling needed:**
     - the component (drawer or inline `Disclosure`);
     - the title;
     - each table's columns and row source;
     - the literal prose and notice replacements.

6. **(Blocker) Mock map: Finding table cells have unmapped lines.** `portfolio.js:25-30` renders:
   - **Value:** three lines, `impact`, `<small>basis</small>` and `<small>window</small>`. `S:L103` maps only the consequence state. There is no row field for basis. Should the window be `episode_start–episode_end`, and in which format (W3-02 uses `d MMM yyyy · HH:mm–HH:mm UTC`)?
   - **Action:** link plus `<small>next</small>` plus a `workflow-text` state (`Open`, `Outcome pending`, `Recommendation`). Rulings needed:
     - `action_state` has no enum. W3-01 splits it into `application_state`, `resolution_state` and `verification_outcome` (`W301:L128`).
     - The row has no `action_code`, although `S:L76` requires `Action {action_code}`. Is it `action_title` (`Action ACT-…`) or a new key?
     - `next_move` has no stored source, because W3-01 closure W9 says the snapshot has no guidance (`W301:L163`). Rule that it is always null, and give its display copy.
     - The no-Action link text is mock `Review recommendation` and spec `Review Finding`. Confirm this is the ruled rewrite.
   - **Site:** name plus `<small>domain</small>`. Give the domain display words (W3-02's `mini-grid`, `cold-chain`, `EV charging`, or the mock's `Mini-grid`, `Cold-chain`, `EV charging`).
   - **Confidence:** `<small>limit</small>`. Is the literal `No reviewed confidence measure` the small line?

7. **(Blocker) Mock map: value cards carry four slots, but the spec gives two.**
   - Each mock card has label, value, `detail` `<p>` and `value-basis` (`portfolio.js:33,45-49`). It is a whole-card `<a>` with a tone (`amber`, `red`, `green`, `purple`, `neutral`) and an icon.
   - The state table gives "Value and subcopy" only (`S:L60-68`), and its generic `Not established · Supporting assessment not available` (`S:L68`) conflicts with the per-card ledger subcopy (`S:L94-96`).
   - **Ruling needed:**
     - per card and per state, the literal value, detail and basis line;
     - the tone for each state (no false red or green);
     - whether a null-destination card renders as non-link text;
     - the risk card destination: `S:L33` says `/findings` but `S:L93` says `/findings/risks`;
     - the closed `value_cards[].state` enum. `S:L33` uses `UNKNOWN`, which is absent from the state table. What state does the service-risk count card carry when supported? What state does "multiple incomparable eligible groups/lines → Not comparable" (`S:L70`) carry?

8. **(Blocker) Lens chips are an implementer choice.**
   - `S:L99`: "Cost/Risks/Opportunities are **links to corresponding estate roots or in-panel query**", while also requiring `aria-pressed` (a button).
   - The mock filters in-panel and updates `#portfolio-result-count` (`screens.js:1055-1058`).
   - **Ruling needed:**
     - in-panel `lens=` refetch (button, `aria-pressed`) or navigation link;
     - URL query persistence on reload;
     - whether the result-count span (`portfolio.js:54`) shows `summary.finding_count` for All and `total_count` for other lenses. No per-lens full count exists on the wire except `total_count`.

9. **(Blocker) Fixtures: the three-domain aligned proof is not concrete.**
   - **Clock.** `S:L151` says "Test last-seven-day aligned selection for all three domains". The replay data is fixed at `2026-10-06` (cold `19:00–20:05Z`, EV `08:00–09:00Z`, from the `window` keys of `normal.json` and `complete.json`). Today's last seven complete days (`10-13..10-20`) contain none of it, and no frozen DB clock is specified (W3-01 froze `2026-10-07T00:00:00Z`, `W301:L42`).
   - **Choices left open:**
     - "one W1 current/eligible **or** withheld line";
     - "two disjoint EV Site lines **only if** W3-02's reviewed positive fixture supports them". W3-02 N3 makes that fixture mandatory (`W302:L204`), so is a W3-03 `COMPARABLE_GROUP` persisted test required?
     - which domain carries the "later accepted record and unsettled job";
     - how MIXED/UNKNOWN provenance is produced through reviewed producers;
     - "withdrawn verification outcome". `verification_outcome` has only supersession (`0019:165,189`); withdrawal is an `action_event` `RESOLUTION_WITHDRAWN`.
   - **The decline needs literal assertions:**
     - `summary.combined_value is None`;
     - `combined_value_state=="NOT_COMPARABLE"` in every variant (is that the only enum value?);
     - `money.estate_total is None`;
     - the same `window` and `known_at` across W1, cold and EV coverage items;
     - distinct categories per domain;
     - pulse-note copy visible.
   - **Also:** "aligned windows" means the *requested* window, not the data windows, which differ by domain. State this.

### Should

10. **(Should) Historical determination with cursor and links.**
    - `S:L15` says the UI omits `known_at` until it is explicitly selected. `window.known_at` then equals DB time, and the cursor carries it (W3-01 cursor includes `known_at`).
    - So is page two, which now has `known_at < DB time`, `HISTORICAL`?
    - Do the root and Site links (`S:L114`) append the captured `known_at` when the user never chose one? That would open the targets in historical mode.
    - **Ruling needed:** "explicit" is defined by the request parameter, not by comparing with DB time, and links omit `known_at` unless the user supplied it.

11. **(Should) Error codes: `INVALID_LENS` is missing.**
    - The endpoint accepts `lens=` (`S:L15`), but the refusal table (`S:L120-132`) omits W3-01's frozen `422 INVALID_LENS` / `Use all, cost, risks or opportunities.` (`W301:L61`).
    - The UI copy column is also missing. W3-01 has a separate UI string per code (`W301:L56-64`), but `S:L122` gives only the API message.
    - **Ruling needed:**
      - the known-key set for the parser (`from,to,known_at,lens,limit,cursor`);
      - which code a bad lens value or a repeated `lens` gets.

12. **(Should) Error tests: the test names contradict the refusal contract.**
    - `clearsPrivilegedRowsOn403And503` (`S:L156`) contradicts the rule that a Portfolio root 403 is unreachable (`S:L123`, `S:L134`).
    - The UI tests "inject 403/404 from downstream Site/detail navigation" (`S:L134`). Those are other pages' responsibilities.
    - **Ruling needed:** what the Portfolio page test actually renders for 403 (nothing?), and whether the test should be renamed `…On401And503`.

13. **(Should) Token: the Portfolio `estate-selection/2` composition is unspecified.**
    - `S:L15` requires the four arrays plus Finding/Action arrays per Site item, from all three roots.
    - Per item, which root supplies `selection_id`, `watermark`, `match_state`, `job_state` and `source_freshness`? Evidence (W1 per day) and Findings select differently.
    - Is `lens` set to the request lens and `state_filter` null?
    - Is there one item per Site, or per (Site, domain)?

14. **(Should) Row membership: Finding lifecycle filter.**
    - W3-01 has a `state` filter defaulting to `all`, which includes `NO_LONGER_SUPPORTED` and `MERGED` (`W301:L30,36`).
    - Should "Where management should act first" list no-longer-supported and merged rows? Does `summary.finding_count` include them?

15. **(Should) Seams: Finding fields are mis-sourced.**
    - `S:L36` says `"mechanism":"<selected-claim-or-null>"` and `S:L102` falls back to `Mechanism not recorded`. But `finding_revision.mechanism text NOT NULL` and `title text NOT NULL` exist (`0009_finding_store.py:74-75`).
    - `episode_start` is "UTC-or-null" with "nulls last" (`S:L23`). But `finding_revision.episode_start/end` are NOT NULL (`:81-82`), and W3-01 B5 instead sources `finding.anchor_start`, `cold_episode.anchor_time` and `ev_session.anchor_time` (`W301:L129`).
    - **Ruling needed:** the exact column per domain, and when null is reachable.

16. **(Should) Row state prefix.**
    - "W3-01 row pending or historical → `Updating`/`Historical` prefix" (`S:L74`). W3-01 rows carry no per-row currentness field; it lives in `coverage.sites`.
    - **Ruling needed:**
      - the join (row `site_id` to the coverage item's finding state);
      - which cell gets the prefix;
      - the literal format (`Updating · …`?).

17. **(Should) Progress and pulse predicates.**
    - **`pending_trial_count`:** `Policy trial awaiting outcome` has no predicate. Is it W3-01 `verification_window`, `Awaiting verification`, or applied with no outcome?
    - **`verified_resolution_count`:** this is "surviving VERIFIED", but over which time range? W3-01 cards use `[known_at−30d,known_at]` (`W301:L128,175`). Is that the latest non-superseded outcome, or the `RESOLVED` event with no later `RESOLUTION_WITHDRAWN`? W3-01 B4 and S19 phrase this differently.
    - **`accepted_action_count`:** "null on incomplete applicable Action coverage". Action coverage is not one of the three coverage blocks, and cold/EV are `NOT_APPLICABLE` for Actions (`W301:L128`).
    - **Shapes:** `progress.rows[]` has no element shape, and `progress.state` has only one value.
    - **Mock lines:** each mock change line has a bold fact, a secondary span (`Outcome unverified`, `Guardrails incomplete`, `Value not yet recovered`) and a dot colour (`portfolio.js:61-63`). Map both slots and the dot tones.

18. **(Should) Evidence prompt.**
    - "First sorted W3-02 typed gap with `next_step`/Site". Gap groups carry several `site_ids` (`W302:L34`), so which Site goes in `evidence_prompt.site_id`?
    - **Ruling needed:**
      - the literal text template (the mock sentence is `Restore Kobo’s missing PCS capability report to resolve…`; `S:L38` gives only `<selected typed gap next step>`);
      - the state enum besides `AVAILABLE` for the two fallback copies (`S:L109`);
      - whether a gap with null `next_step` is skipped.

19. **(Should) Objective matrix enums and cells.**
    - **Enum.** `S:L37` gives COST_CONTROL `state:"UNKNOWN"` with `label:"Unassessed"`, which contradicts the rule that Unassessed means no line (`S:L82`). Give the closed state enum (`UNKNOWN|UNASSESSED|REVIEW|FULL|LIMITED|NONE|NOT_APPLICABLE`?).
    - **Reasons.** Are the `reason` strings literal, and where are they displayed? The mock cell shows only the label.
    - **Missing destination.** For cells without a destination, does the tiny cell show the label *and* `Site detail unavailable`?
    - **Header.** Column header text: `site_name`, `site_code`, or the mock short names (`Kobo`, `Cold room`, `Depot`)?
    - **Width.** At 1440 the side panel is 309 px (`M:L9`). Does it also scroll horizontally with four or more Sites? The fixture adds `W303-EMPTY-001`.
    - **Historical.** At a historical cutoff, should the Evidence cell be `Unknown` (`S:L82`) even though W3-02 shows historical-labelled readiness?

20. **(Should) Context badge and sentence copy.**
    - Two badge vocabularies exist:
      - the status table: `Selected Site records`, `Updating selected Sites`, … (`S:L54-58`);
      - `Portfolio: Review selected Sites` / `Portfolio: Some Sites unavailable` (`S:L70`).
    - **Ruling needed:**
      - which is the badge and which is the sentence;
      - the badge tone per status;
      - the literal `{domain counts}` template and words.
    - "**preferred** neutral copy" (`S:L70`) leaves a choice. A Site-level provenance class (for the `simulated` claim) is also not on the wire.

21. **(Should) Opportunity panel slots.**
    - The mock story has quantity, caption, arrow, quantity and caption (`portfolio.js:59`). Map `No reviewed scenario` and `No eligible headroom or demand basis` to those slots, and say whether the arrow stays.
    - Give the `Scenario` chip tone (mock green) for an unavailable state.
    - Give the literal inert CTA text. Is it `Review opportunity Finding · Not available yet`, with the arrow dropped, as in W3-02 Q27 (`W302:L177-180`)?

22. **(Should) Footer predicate.**
    - With several eligible EV lines or Sites, which line, or a COMPARABLE group?
    - Give the amount rounding: half-even two places, per W3-02 `W302:L62`.
    - Define "actual coverage says so" for `Other Sites may lack comparable full-window coverage.`. Mini-grid and cold Sites never have energy coverage, so is it any non-EV authorized Site, or EV money coverage incomplete (`S:L112`)?

23. **(Should) Pagination UI.**
    - The default limit is 50 with a cursor (`S:L15,23`), but the mock has no pager. Rows "scroll inside the table" (`S:L138`).
    - **Ruling needed:**
      - whether the page fetches only page one;
      - whether it offers a `Load more`/`Next page` control (copy and placement);
      - the table body's max height in px, given that scrolling starts after the six-row reference.

24. **(Should) Layout budgets cover only the four panels.**
    - The context band, five value cards, pulse, evidence aside, opportunity footer and document height have reference values (document 1558/3192, `S:L147`) but **no caps**.
    - W3-01 and W3-02 capped cards and status bars (`W301:L88-95`, `W302:L74`). Was `tools/measure-mock-panels.mjs` run for those regions? If not, measure and cap them.
    - Is width (836/309/573) a tolerance or only a reference?
    - At 390, what is the card grid (mock column count)?

25. **(Should) Layout test proof.**
    - `meetsMeasuredDesktopAndNarrowPanelBudgets` (`S:L157`) is a jsdom Vitest test, and jsdom cannot measure layout. Name the browser capture tool (`tools/layout-evidence.mjs`) and its states, and rename or narrow the unit test.

26. **(Should) Guard and composition seams for the new adapter.**
    - W3-02 Q8 lists `$pgReaders` **by file** (`W302:L46`). `estate/adapters/postgres_portfolio_read.py` must be added by Lane A to `tools/checks/configuration-persistence.ps1`, along with the dependency-direction allowance for `estate_portfolio_api.py`. The spec omits both.
    - It also does not name the `estate/composition.py` builder through which the API imports the adapter (guard rule `configuration-persistence.ps1:8`).

27. **(Should) Commit sizing and integration timing.**
    - When does Lane A mount `estate_portfolio_api` in `main.py`? After commit 1, as W3-02 did, or in commit 3?
    - Commit 2 requires 1440/390 app captures (`S:L156`), but the route and rail land only in commit 3 (`S:L157`). W3-01 put Lane A's route patch before the UI commit's review (`W301:L126`).
    - Commit 1 composes all of the following, which is large for one builder run. Should it split into 1a (scope, coverage, rows, cursor) and 1b (cards, matrix, prompt, progress)?
      - three roots;
      - cards;
      - objectives;
      - prompt;
      - progress;
      - money.
    - No expected test-node delta is stated (W3-01 gave one, `W301:L80`).

28. **(Should) Route path and rail tuple.**
    - The Portfolio app route path (`/portfolio`? also `/`?) and the guard tuple `live|Portfolio|OPERATIONS|<path>` are not given (`S:L86`).
    - `test_w303_global_route_precedence_and_unavailable_multiset` has no file or language (backend pytest, Vitest, or a PowerShell guard self-test?) (`S:L157`).

29. **(Should) W3 closeout scope.**
    - "Finish the W3-01/02 global roots through truthful cross-links, common selection controls" (`T:L7`, `S:L114`).
    - Does commit 3 **edit** the W3-01/02 pages, for example by adding links back to Portfolio or unifying the date bar, or only verify them? If it edits them, name the files, links and copy. Those pages are W3-01/02 reviewed surfaces.

30. **(Should) Sequencing contradiction.**
    - `T:L3` says to branch "after the shared migration chain through `0030` has been integrated". That makes Lane B's W3-03 wait for W4-03.
    - `S:L11` says `0029`/`0030` "may exist" and are not inputs. Confirm which applies.

### Nit

31. **(Nit) Path.** `S:L9` places `analytics/ev_site_reads.py`; the file is `backend/assetops_backend/ev_site_reads.py`, as W3-02 Q42 notes (`W302:L32`).

32. **(Nit) Error body extras.** The refusal `detail` lists `value_cards/objectives/money:null` (`S:L118`). Confirm `coverage`, `summary`, `evidence_prompt`, `opportunity` and `progress` are simply absent.

33. **(Nit) Historical date format.** `Historical as of {known_at}`: give the date-time format (UTC ISO or `d MMM yyyy · HH:mm UTC`).

34. **(Nit) Registry path rationale.** `portfolio:3` maps to `A-estate-comparability` and `portfolio:2` only to `A-evidence-shared-projections`, although the Cost-control cell reads money (`S:L159`). Confirm the intended edges.

35. **(Nit) Single-value enums.** `opportunity.state` (`UNSUPPORTED`) and `combined_value_state` (`NOT_COMPARABLE`) are single-valued. State that they are fixed literals in this slice.
