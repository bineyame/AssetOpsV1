# Independent spec dry-read: W3-02 estate Evidence and Financials (2026-10-20)

Reviewer: a fresh Claude spec reviewer, read-only, worktree `AssetOpsV1-plan2` on main `dc692c21`. This follows the ROLE_CONFIG rule from `409c39ed`, with `.agent/W4-01-W3-01-spec-review.md` as the precedent.

Inputs:
- `.agent/W3-02-build-spec.md` (cited as `S:Lnn`) and `tasks/W3-02-estate-evidence-money-basis.md`;
- `.agent/post-W2-sequence.md`;
- `.agent/W3-01-build-spec.md` (cited as `W3-01:Lnn`), including closure 2 and Run 1 rulings;
- `.ai/ROLE_CONFIG.md`, "Mockup drives the design";
- v69 `screens.js:522-534`;
- the merged code.

The mock pixels I measured are in `.agent/W3-02-mock-measurements.md`.

Method: I read the spec commit by commit, as a mid-level implementer would. I checked every named path:symbol, table, column, route, guard and component against the merged tree.

**State of main.** W3-01 and W4-01 are **not merged**. There is no `backend/assetops_backend/estate/`, no `frontend/src/estate/` and no `0027`; the newest migration is `0026_w2_ev_money.py`. So `estate/scope.py`, the cursor, the access basis, `evidence/public_provenance.py` and the shared date bar are unverifiable consumed seams, and S:L16 ("Existing `0027` remains the single head") is false today.

**Verified correct**, so not listed below:
- `ColdReadService._snapshot(c,…)` (`postgres_assessment_store.py:1573`) and `EvReadService._snapshot(c,…)` (`:2102`);
- `cold_site_reads.py:CAPABILITIES` (6, `:35-36`), `_capabilities(c,snap)` (`:424`), `_sources` (`:478`), `financials` (`:574`) and `_consequence_row` (`:216`);
- `ev_site_reads.py:CLAIMS` (7, `:49-60`) and `NEXT_EVIDENCE` (`:61-77`);
- `EvMoneyReads` (`financials/adapters/postgres_consequence_store.py:1077`);
- `ConsequenceReadService`, `money_eligibility.py`, `provenance_read.py:source_gate` (`:35`) and `ClaimLimitReadService` (`claim_limit_read.py:217`);
- `site.site_code_key` (`0001_foundation_identity.py:64`);
- all seven registry nodes in S:L139, which exist in `v69-dependency-registry-pilot.json`;
- the fixture paths in S:L137;
- `v69-rendered-panels.json:546-565` (two panels per screen);
- the rail items `Evidence` and `Financials`, which are `unavailable` today (`OperatorShellLayout.tsx:59-60`, `navigation-truthfulness.ps1:553-554`).

**Readiness gate (ROLE_CONFIG): not met.**
- W1 evidence and money have no `known_at` read and no per-window selection to reuse.
- The comparability rule cannot produce a COMPARABLE group from real persisted data.
- The read-only guard allowlist has no mechanism.
- Several wire, copy and route items contradict W3-01 or the merged code.

**Count: 48 questions** (19 Blocker, 22 Should, 7 Nit).

---

## Blockers

### Seams that contradict merged code

1. **Blocker** (S:L20, L22, L26, L40-48, L68). **W1 has no knowledge-cutoff read.** The spec requires `known_at` and HISTORICAL on both roots. However:
   - `ClaimLimitReadService.read` always queries `OPEN_CUTOFF` (`claim_limit_read.py:227`, `dispatch_read.py:36`). Its `HISTORICAL` means "revision not in the current selection" (`claim_limit_read.py:279-280`), not "earlier cutoff".
   - `ConsequenceReadService.read` has no cutoff parameter. It derives currentness by re-deriving the basis with *today's* prices (`consequence_read.py:169-212`).
   - `MoneyEligibility.for_finding` has no cutoff either (`money_eligibility.py:176`).

   How do I select a W1 capability row and a W1 consequence head "as of `known_at`"? By `assessment_revision.created_at`/`run.completed_at` ≤ `known_at` and `financial_consequence_revision.recorded_at` ≤ `known_at`? What is W1 currentness at an earlier cutoff? Or are W1 rows always `UNKNOWN`/`HISTORICAL` when `known_at` < DB time? (Cold/EV accept `known_at`; W1 does not.)
2. **Blocker** (S:L22, L26). **The W1 capability selection is per UTC day and per one revision**, but the estate window is up to 31 days. `ClaimLimitReadService.read(tenant, site, day, revision_id)` takes one day and one `assessment_revision_id` (`claim_limit_read.py:221-227`), and S3 selects per day (`day_window`, `dispatch_read.py:67-69`). For a multi-day window, which revision feeds the W1 row: each day's interval revisions, the window revision, or the worst/latest day? Is it one row per day or one per window? What goes into `selected_revision_ids`?
3. **Blocker** (S:L26, L82, L35). **The W1 capability registry and enum mapping do not exist in code.**
   - "Reviewed W1 Site Evidence keys" has no backend counterpart. `GENERATOR_SUPPORT` / `Generator support` appears only in Finding titles (`frontend/src/sites/findingWords.ts:14`), never as a capability key.
   - The W1 claim limit exposes `support` = `COMPLETE|LIMITED|NONE` and `ceiling` = `Candidate|Necessary|Indeterminate` (`claim_limit_read.py:203-214`), not `SUPPORTED|LIMITED|UNAVAILABLE`.

   I need the literal W1 key list, each key's label, and the mapping `COMPLETE→FULL?`, `NONE→NONE?`, `ceiling Indeterminate→?`, `UNASSESSED/PENDING/FAILED/STALE_PROJECTION→?`.
4. **Blocker** (S:L28, L87). **The gap key `(gap_code,missing_role)` does not fit any domain's data.**
   - W1 reasons are per span: `MISSING_ROLE|GENERATOR_UNOBSERVED|POOR_QUALITY|CONFLICTING` carry `role`; `COHORT|CONFIGURATION|OPEN_BOUND|LIMITED|MODEL_LIMIT|NOT_CURRENT|RULE_BASIS_INCOMPLETE` have no role (`claim_limit_read.py:158-182, 322-328`).
   - Cold has `missing_roles` but no gap code (`cold_site_reads.py:471`).
   - EV has gap codes but no role (`ev_site_reads.py:61-77, 631-647`).

   For each domain I need the exact `gap_code` value, the `missing_role` value (or null), and which W1 reason codes are gaps.

   EV `_next_candidates` **always** appends `BILLING_GAP` (`ev_site_reads.py:646`), so every EV Site would show a permanent recurring gap. Should that be included or excluded? And should I use all candidates or only the Site's `codes[:3]` (`:658`)?
5. **Blocker** (S:L54, L58, L62). **COMPARABLE is unreachable from persisted data.** The partition requires equal `assumption_revision_ids` and an exact equal `window_start/window_end`. But:
   - `financial_assumption_revision` is per Site (EV FK `(tenant_id,site_id,…,tariff_revision_id)`, `0026_w2_ev_money.py:67`), so no two Sites ever share an assumption ID.
   - EV has one head per Site window (`ev_consequence_revision_basis_unique`, `:69-70`).
   - W1 windows are per-Finding episodes.

   So every real group is `SINGLE_LINE`, and "two eligible same-category lines with disjoint technical IDs" (S:L139) can only be synthetic. Is that intended, or should the partition key compare assumption *values/keys* rather than revision IDs? If it is intended, say so, and name the fixture that produces the COMPARABLE variant.
6. **Blocker** (S:L52, L54, L57). **The money row sources are undefined per domain.**
   - `technical_interval_ids`: W1 has `financial_consequence_power_interval`, EV has `ev_consequence_session.session_revision_id`, and cold has neither.
   - `assumption_revision_ids`: W1 has one `price_revision_id` (`0011_financial_consequences.py:71`), cold has a jsonb array, EV has `tariff_revision_id`.
   - `quantity`: W1 is litres with `quantity_low` always 0 (`0011:96-108`); cold is `degC_min|none`; EV has a single `quantity_kwh`.
   - `amount`: W1 `amount_low` is **always 0** (`0011:108`), so the register shows `$0.00–$3.97` where the mock shows `$3.31–3.97`. EV has a single `amount`.
   - `period_kind`: no domain-to-value mapping exists.
   - `category`: no mapping exists either; cold `RECORDED_REPAIR` (`0023:60`) has no category.

   I need a literal per-domain column→key table.
7. **Blocker** (S:L62-70). **The eligibility mapping from the stored states is missing.**
   - W1: `state` is `PRICED|UNPRICED|QUANTITY_UNAVAILABLE` and currentness is `CURRENT|STALE|PENDING|HISTORICAL|AUDIT_ONLY` (`consequence_read.py:186-213`).
   - EV: `ESTIMATED|UNPRICED|WITHHELD` (`0026:60`) and guards `STALE_BASIS|HISTORICAL_CURRENT_CLAIM|pending` (`ev_site_reads.py:245-251`).
   - Cold: `UNPRICED|WITHHELD` (`0023:61`).

   Which eligibility does each (state × currentness × gate) cell map to? `AUDIT_ONLY` and `QUANTITY_UNAVAILABLE` are not in the table. Is EV `ESTIMATED` the meaning of "ELIGIBLE"?
8. **Blocker** (S:L16). **The read-only SQLAlchemy allowlist has no mechanism.**
   - A DB-driver import is allowed only in the nine `$pgWriters` (`tools/checks/configuration-persistence.ps1:761-762, 822-829`).
   - Every writer must record ≥1 write (`:1117`), so a read-only module in that list fails the anti-vacuity check.
   - Listing `estate/evidence_money.py` (a non-adapter domain module) also breaks adapter isolation (`:233-270`).

   What is the exact guard change, who makes it (Lane A owns `tools/checks/`), and is it the same mechanism W3-01 uses for `postgres_estate_read.py`?
9. **Blocker** (S:L22, L5). **The "extract connection-taking logic" step means editing Lane-A-owned W1/W2 files**, and it is not sized.
   - W1 money goes through `self._store.chain`, `derive(store, prices, …)` and `MoneyEligibility` Protocols that each open their own transaction (`consequence_read.py:176-197`, `money_eligibility.py:58-66`).
   - The W1 claim limit uses `claim_limit_snapshot` → `_snapshot` (its own transaction) (`postgres_assessment_store.py:592-619`).

   W3-01 Run 1 ruling 1 gives `financials/consequence_read.py`, `cold_site_reads.py` and `postgres_assessment_store.py` to Lane A. Which files does Lane B touch? Which commit (1 or 3) carries the extraction? Does the extraction fit in one builder run alongside the estate read?
10. **Blocker** (S:L103). **The cold Site routes are wrong.** No `/sites/{code}/cold/evidence` or `/cold/financials` UI route exists. Cold Sites use the shared `/sites/{code}/evidence` and `/financials`, dispatched by domain (`shell/coldSiteRoutes.tsx:21-25` → `siteEvidenceHref`, `siteFinancialsHref`). The query keys are `from,to,known_at` (`coldAssessmentClient.ts:202-203`).

    Mini-grid `/evidence` takes `?view=&assessment=` (`operatorSiteRoutes.ts:120-122`). Mini-grid `/financials` takes `finding_id,revision_id,consequence_revision_id` (`:174-187`), not `from/to/known_at`. EV routes take `from,to,known_at` (`ev_site_reads.py:279-286`).

    Please give the literal link template per domain × (`site`, `site_readiness`, `bridge`, `evidence`), and say which ones get the `Opens current Site view` label.

### Wire contract gaps

11. **Blocker** (S:L107 vs W3-01:L52-64). **The refusal table contradicts W3-01's frozen estate table**, yet S:L107 says "code/message pairs unchanged".

    | Item | W3-01 | W3-02 |
    | --- | --- | --- |
    | 503 code | `ESTATE_STORE_UNAVAILABLE` | `ESTATE_READ_UNAVAILABLE` |
    | Cursor refusal | `INVALID_CURSOR` | `ESTATE_CURSOR_INVALID` |
    | 401 copy | `Sign in to read estate records.` | `Sign in to view estate evidence and financials.` |
    | API message vs UI copy | separate | one string per code |
    | Where `rows:null,total_count:null` sit | inside `detail` | top level |

    W3-02 also has no codes for:
    - a bad `limit` (W3-01 `INVALID_LIMIT`);
    - a future `known_at` (W3-01 `INVALID_KNOWN_AT`);
    - `ESTATE_SELECTION_INCONSISTENT`.

    Which table wins? I need the literal 401/409/422/503 bodies.
12. **Blocker** (S:L107 vs W3-01:L135). **When is a 403 or 404 emitted?** W3-01 B6 removed 403/404: per-Site `Access` refusals simply exclude the Site, and an empty scope is valid (`finding_api.py:35-37` has a per-Site Access only). No source-disclosure permission exists anywhere, so `ESTATE_SCOPE_FORBIDDEN` and `ESTATE_SOURCE_DISCLOSURE_FORBIDDEN` have no trigger. `ESTATE_SITE_NOT_FOUND` has no endpoint. Yet S:L139 requires tests for 403 and 404. What exact request produces each one, or are they removed?
13. **Blocker** (S:L32, L52 vs W3-01:L66, L135). **The cursor is undefined.**
    - S:L32 says "signed", but W3-01 says the access basis is "a digest/fence, **not** a signature" and its cursor has no MAC.
    - A tampered `last` tuple is undetectable without a MAC, yet S:L32 wants 422 for tamper. Is there an HMAC? With which key and which algorithm?
    - The W3-01 cursor carries `tenant_id,authorized_site_ids,after`; W3-02 carries `last,limit` and no tenant. Which keys are canonical?
    - Must `limit` match on page 2, or may it change?
14. **Blocker** (S:L32, L52). **The `selection_token` canonical form is missing for both endpoints.** W3-01 fixes `estate-selection/1` with exact keys and timestamp format (W3-01:L136). W3-02 only says "canonical scope selection plus sorted per-Site assessment/revision IDs and full cited IDs". I need the version string, the key list (do money tokens include consequence revision IDs and tariff IDs?), the per-domain ID sources and the timestamp format.
15. **Blocker** (S:L35 vs W3-01:L169, L186). **Which `coverage.sites[]` shape applies?** W3-02 uses `{site_id,site_code,domain,state,selection_ids,source_freshness}`. W3-01 closure 2 uses `{site_id,state,committed_watermark,selection_id,match_state,job_state,source_freshness}` from `estate/coverage.py:site_coverage`, with `source_freshness` including `NOT_APPLICABLE` for EV.
    - Do I reuse `site_coverage`?
    - What are the `domain` wire values? `site.site_type` is `MINIGRID|COLDCHAIN|EV_CHARGING` (`0001_foundation_identity.py:66`); analytics domains are `dispatch|cold_chain|ev_charging|mini_grid` (`assessment_worker.py:56`, `cold.py:34`, `ev.py:31`, `finding_episode.py:78`); the example uses `MINI_GRID`. What is the cold value?
    - W3-02 `scope` drops `tenant_id`. Is that intended?
16. **Blocker** (S:L32, L38, L26). **The placeholder and readiness enums are inconsistent.**
    - Unselected Sites get `UNASSESSED` placeholder rows, but `readiness` allows only `FULL|LIMITED|NONE|UNKNOWN|CONTRADICTORY|N/A` (S:L83), and S:L26 maps CONTRADICTORY→Unknown while S:L83/L47 render it red "Conflicting records". Which is right?
    - Does `total_count` ("full selected capability count") include placeholder rows?
    - Do `capability_count`/`full_count`/`unknown_count` include placeholders?
    - Is `raw_state` `UNASSESSED` and `readiness` `UNKNOWN`?
    - Is `N/A` the literal wire value?
17. **Blocker** (S:L38, L35, L109-118). **The `status` and `coverage.state` enums are not listed.** Is `EMPTY_SCOPE` a `status` value, a `coverage.state` value, or both? Is `coverage.state` `COMPLETE|PARTIAL|UNKNOWN` (W3-01) plus `EMPTY`? Which status does a Site that is HISTORICAL for one domain and PENDING for another produce?
18. **Blocker** (S:L52, L57). **Gap rows ("UNPRICED" display key) are undefined.** Which Findings are enumerated, and through which selection (W3-01's Finding selection?)? Which `category` does a gap row get? `category asc` is in the sort, and EV consequences may have a null `finding_revision_id` (`0026:50`). What is the row JSON for a gap row (`line_key`, `consequence_revision_id:null`, `eligibility:"UNKNOWN"`?), and what is its tie-break when several gap rows share a Site and category? The cursor `last` cannot hold a null revision without a rule.
19. **Blocker** (S:L54, L57, L60, L101). **The shapes of `exclusions[]`, `reason_codes` and diagnostics are missing.** The example has `exclusions:[]`, but its element keys are not given. The `reason_codes` vocabulary is not given. Where do `MIXED_CURRENCY`/`DIFFERENT_PERIOD` appear? A partition is keyed by currency and window, so it can never itself be mixed. Is there a separate `diagnostics[]`? Which `groups[].state` does a partition containing one WITHHELD and one ELIGIBLE line get? Which lines count in `summary.withheld_line_count` (WITHHELD only, or PENDING/UNKNOWN/CONFLICT as well) and in `eligible_line_count` (HISTORICAL?)?

## Should

### Evidence rows and copy

20. **Should, user-visible** (S:L26, L82). **Row granularity differs from Site readiness.** Cold and EV Site Evidence group raw claims into mock rows, for example cold `Backup response` = `BACKUP_START_RESULT`+`TRANSFER_POSITION` (`coldSiteViews.tsx:108-113, 289-295`), and EV has its own `CAP_ROWS` (`EvSiteViews.tsx:258, 744`). The estate page uses one row per raw claim (6 + 7 + W1). That gives at least 14 rows for three Sites against the mock's 3, and chips that differ from the linked Site page. Should the estate page use raw claims or the Site's grouped rows?
21. **Should** (S:L35, L84). The `current_ceiling` and `ceiling_source` value sources are undefined. Cold and EV capabilities have only `limitation` (`cold_site_reads.py:475-476`; `ev_site_reads.py:420`). W1 has `claim_limit.statement`/`ceiling`. What is `ceiling_source`: a field-path string, an enum, or a revision ID?
22. **Should** (S:L35, L85, L28). **`next_evidence` copy and the gap/next-step dictionary are missing.**
    - "Exact dictionary entry for that typed role" and "`gap_code`+`missing_role` display dictionary" (S:L87) are not supplied.
    - Cold role IDs (`binding_roles.py`) have labels, but no next-step wording.
    - EV `NEXT_EVIDENCE[code][0]` is wording. Does it count as "stored guidance"?

    Supply the literal per-key strings.
23. **Should** (S:L24, W3-01 Run 1 ruling 2). The selected-ID set for an Evidence **capability row** is not among ruling 2's row kinds. Is a cold capability row the full envelope set (both analytics) or the one analytic's revision (`cold_site_reads.py:467`)? Is an EV capability row the envelope set? Is a W1 row `{assessment_revision.id}` or the per-day set? Is `selected_revision_ids` equal to that same set?
24. **Should, user-visible** (S:L78-80). Card copy is incomplete. The numeric card-1 value format with its denominator is undefined: `2 of 4`? `2`, plus a note? The mock notes for cards 1–3 (`All three domains have explicit gaps`, `PCS, loading…`, `No invented loss…`) have no ruled replacement when values are null or numeric. Value `Not assessed` is given; what is the note line? What is the card tone?
25. **Should, user-visible** (S:L81, L88, L93). Display names do not match the mock.
    - The mock shows `Kobo · mini-grid` and Sites `Kobo · Depot` (short names).
    - The spec gives `site_name`, `domain`, `site_code`, and `site_codes` for the gaps' Sites cell. That would render `KOBO-001 · EV-LAB-001`.
    - The fixture names are `Kobo mini-grid`, `Cold replay lab` and `EV charging lab` (`var/sites/kobo-001.yaml:2`, `cold-lab-001.yaml:2`, `ev-lab-001.yaml:4`), not `Kobo Mini-grid` / `Depot EV charging` as in the examples.

    What is the format of the Site / domain cell? What is the domain word dictionary (`mini-grid`, `cold-chain`, `EV charging`)? Does the gaps cell show names or codes?
26. **Should, user-visible** (S:L86, L91, L99). Static copy deviates from the mock without a stated ruling.
    - Mock: `Each row links to site-owned readiness; this page does not independently score the claims`. Spec: two sentences.
    - Mock notice: `Evidence Full/Limited/None/N-A is a separate vocabulary from …`. Spec: `N/A is separate from`.
    - Placement: the mock puts both strings as panel **subtitles** under the title (`panel(title, body, sub)`, `screens.js:36`), but the spec calls them "footnote".

    Should I keep the mock wording and placement?
27. **Should** (S:L90). The `Next step` rule contradicts itself. When does a row show `Not available yet` (inert mock label) and when does it show `Next step not recorded`? Is the mock label text (`Map transfer switch`) ever shown? What is the exact inert format: W3-01's `{label} · Not available yet`, with the accessible name `{label}, Not available yet` (W3-01:L114)?
28. **Should** (S:L83, L94-96). **No component provides the chip tones.** `BadgeTone` is semantic only: `provenance|lifecycle|origin|neutral|configured|config-gap` (`ui/Badge.tsx:20-28`). The cold page uses a local `cold-tone--*` class map (`coldSiteViews.tsx:663-677`). Green, amber, red, gray and blue need either a new tone in shared `ui/` (Lane A) or a page-local class. Which one? What are the tones for money eligibility chips and group-state chips (not given at all)?
29. **Should** (S:L74). Component mapping. The spec names `ProductStatus`, `Panel`, `DataTable`, `Disclosure`. The mock elements map to `MetricCards`, `StatusBar` and `Notice` (`ui/V69Layout.tsx:55, 165, 187`). `ProductStatus` needs `words/scope/asOf` (`ui/ProductStatus.tsx:14-32`), and the Financials status is static. Confirm `MetricCards` + `StatusBar` + `Notice(tone)`. The tones are Evidence notice **blue**, Financial notice **amber** (mock default), and the status chip blue.
30. **Should, user-visible** (S:L74, mock header). The page header is unmapped: eyebrow `Evidence`/`Financials`, h1 `Portfolio evidence`/`Portfolio financials`, subtitle `Cross-site claim readiness, recurring gaps and instrumentation priorities` / `Estate consequences with source-site ownership and bounded interpretation`, and the window control (`Window: Event window · … each site's event window`). Should I keep these strings? Which header component is used? What does the window control say for an estate UTC window?
31. **Should** (S:L20 vs W3-01:L138). The default window and the date bar contradict W3-01. W3-02 defaults to the **last complete UTC day** with `limit` 25. W3-01 rules the estate wrapper's default as the **last seven complete UTC days**, with `limit` 50. Is it one shared estate date bar with one default? Which "existing period bar" (S:L74) is meant, given that W3-01 says `periodStrip.tsx` renders labels only?

### Money rows and copy

32. **Should, user-visible** (S:L52, L96). Rounding differs from the Site page. EV Site money displays **half-even** to two places (`EvSiteViews.tsx:153`, W2-07 fix r1). The estate page specifies outward rounding via `MINOR_UNITS` (`consequence_read.py:43-62`). The same EV amount would then differ between the estate and the Site bridge. Which rule applies per domain? What is the display for a currency not in `MINOR_UNITS`?
33. **Should** (S:L57, L97). The source of the `limit` text is undefined. The example says `Gross tariff scenario; not cash collected.`. The stored values are EV `CLAIMS` `Gross scenario only.`/`MONEY_COPY`, W1 `limitations` jsonb (several), and cold `screen_sentences(limitation)`. Is it static per category or stored? How do I join several W1 limitations? How are `assumption_revision_ids` rendered in `Basis / limit` (count, short IDs, or Disclosure)?
34. **Should** (S:L95). The `Window / quantity` format is unclear. Do I use UTC or `site.timezone`? Windows that cross midnight or span several days need a format. I also need quantity unit words (`L`, `kWh`, `degC_min`→?, `none`). The cold mock text `6 Oct · backup excursion` has no source field.
35. **Should** (S:L52). Duplicate collapse versus `overlap_group`. Every consequence table has an `overlap_group` column. Cold `_money` keeps one head per `overlap_group` and only the `PRODUCT_EXPOSURE` kind (`cold_site_reads.py:197-213`). Is the estate overlap proof that existing `overlap_group`, the ID-intersection rule in S:L54, or both? Are cold `RECORDED_REPAIR` heads listed?
36. **Should** (S:L60, L62). For HISTORICAL and PENDING, does the register show the prior selected head, or EV `history` rows (`ev_site_reads.py:724-726`)? "Prior history only": is that one row or the whole chain?

### Proof, sizing, layout

37. **Should** (S:L35-38 vs W3-01:L80). **No test function names are given.** The W3-01 spec named every node and the count delta. W3-02 names files only (`test_w302_*`, `estateEvidence.test.tsx`, `estateFinancials.test.tsx`). Supply the function names and the expected +N backend/frontend node delta. The frontend path also differs from W3-01's `frontend/src/estate/__tests__/`.
38. **Should** (S:L122-133; measurements file). **The budget rules conflict.** Caps such as capability panel 500 at 1440 sit far above the measured mock 285 + max(24,10%) = 313. Which rule binds: the cap or mock + tolerance? The measured Recurring gaps panel at 390 is **639**, above its 460 cap, so it is 702 by S:L133. Notices have no budget (measured 42/78). The mock 390 cards are a **2+1 grid** (264), not "stack". Is the Aggregation-rule cap meant to include the added group/exclusion chips that the mock does not have?
39. **Should** (S:L137). The W1 fixture is unnamed. KOBO-001 needs an S3 selection, an S4 Finding, a published diesel price and a computed `financial_consequence_revision`. Which setup is used: W3-01's `test_s405_resolver_postgres.py::power_site` or `tools/s2_demo_walkthrough.py`? Which W2-07 money test(s) are "W2-07 money tests" (`test_w207_ev_money_postgres.py`, `test_w207_ev_site_reads_postgres.py`)? How is a second currency produced with real persisted data (a second tariff publication in another currency)?
40. **Should** (S:L9-14). Commit sizing. Commit 1 holds the W1 per-day selection extraction, the cold/EV composition, the registry, typed gaps, the cursor/token and two Postgres test files. Commit 4 holds the UI, captures, the full suite and the closeout. Each is probably more than one builder run. Should commit 1 split into "connection-taking extraction (Lane A files)" and "estate evidence read"?
41. **Should** (S:L139). Lane A's registry paths are "cards/status/notices", but the panel contract has only `globalevidence:1-2` and `globalfinancials:1-2` (`v69-rendered-panels.json:546-565`). Are new panel IDs added for cards, status and notices? With what IDs?

## Nit

42. **Nit** (S:L20). The spec names the EV class `EvSiteReadService`. The real class is `EvSiteReads` (`ev_site_reads.py:221`), built in `financials/composition.py:103-105`. Its capabilities take `ctx`, not `(c,snap)` (`:386`).
43. **Nit** (S:L35). The example `scope.authorized_site_count:1` with `limited_site_count:1` and `capability_count:1` contradicts the rule that a selected Site emits every domain capability. A KOBO-only scope would have N W1 keys.
44. **Nit** (S:L57). The example row omits `domain`, which is part of the line key. Add `domain` to the money row keys.
45. **Nit** (S:L38). "Complete zero is 0; partial is null" conflicts with `priority_gap_count` and `unsupported_claim_count`, which are always null. Confirm they stay null even on a complete empty scope (W3-01 keeps priority null).
46. **Nit** (S:L107). Repeated or unknown query keys use `ESTATE_PARAMETER_UNKNOWN`. Does W3-01's merged router also refuse unknown keys, or will the two estate APIs disagree?
47. **Nit** (S:L113). "Scope with no selected result". Is the copy shown inside the empty table body or as a panel note? W3-01 forbids a fake spanning row (W3-01:L112).
48. **Nit** (S:L16, task L9). Reword the "`0027` remains the single head" statement as conditional on W4-01 merging; today the head is `0026`.

---

## Three most serious

- **Q1/Q2: W1 has no `known_at` and no multi-day selection.** The claim-limit and consequence reads are open-cutoff, per day and per revision, so the HISTORICAL and 31-day contract cannot be built for mini-grid without a new rule.
- **Q5: COMPARABLE groups are unreachable from real data**, because assumption IDs are per Site and EV has one head per Site window. Either the partition key is wrong or the positive variant is synthetic only.
- **Q11–Q13: the refusal codes, wrapper and cursor contradict W3-01's frozen estate contract.** That includes a "signed" cursor with no MAC, and 403/404 codes with no trigger.
