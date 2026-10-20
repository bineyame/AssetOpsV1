# W3-02 build spec — estate Evidence and Financials (2026-10-20)

Authority: `tasks/W3-02-estate-evidence-money-basis.md`, `D-2026-10-20-post-w2-sequence`, W3-01 Run 1 rulings and shared provenance DTO, W4-01 Run 1 seam, v69 `globalevidence`/`globalfinancials`. Planning only: reviewed merged W3-01 and W4-01, independent spec review and the owner W3 wave-start gate precede implementation. Reconcile spelling against their reviewed merge; a semantic change needs Architect amendment.

## Ownership, commits and migration

Lane B owns `backend/assetops_backend/estate/evidence_money.py`, `estate/adapters/postgres_evidence_money_read.py`, `estate_evidence_money_api.py`, `frontend/src/estate/EstateEvidence.tsx`, `EstateFinancials.tsx`, `estateEvidenceMoneyClient.ts` and focused tests. Reuse W3-01 `estate/scope.py` authorization, snapshot and cursor; no second grant algorithm. Lane A alone owns `main.py` router mounts, `/evidence` and `/financials` shell routes/rail, shared `ui/`, the dependency registry/checker and `tools/checks/`. Lane B supplies an exact route/registry diff request; Lane A edits the released branch serially, then hands it back. Neither lane edits a shared file in a separate worktree concurrently.

| Commit / one builder run | Implement and prove | Lane A integration after release |
| --- | --- | --- |
| 1 Evidence read/API | Connection-taking selected Site projections, finite capability registry, typed gaps, scoped API. `test_w302_evidence_scope_snapshot_postgres.py`, `test_w302_evidence_api.py` cover all Sites, foreign tenant, pending, full IDs, cursor and refusals. Review before UI. | Mount API; no shell edit. |
| 2 Evidence page | Three cards, capability table, recurring gaps, notice. `estateEvidence.test.tsx`, route/navigation fixtures; 1440/390 stocked and partial captures. | Shell route/rail, four Evidence paths in registry/checker. |
| 3 Money read/API | Exact consequence revisions, comparability, exclusion proof, no write. `test_w302_money_selection_postgres.py`, `test_w302_money_comparability_postgres.py`, `test_w302_money_api.py`; review before UI. | Mount API. |
| 4 Financials page/closeout | Register, grouping rule and reason states. `estateFinancials.test.tsx`, route/navigation fixtures; captures, one same-revision full Postgres suite, frontend build, guards. Independent whole-slice review, then owner checkpoint. | Shell route/rail and Financials panel registry paths. |

Migration `0028` is **unused**: zero migration files, tables, indexes, triggers, backfills or writer exemptions. Existing `0027` remains the single head. Lane A records unused reservation; it is not reassigned. A measured need for storage returns to Architect with query plan and a new migration contract. SQLAlchemy and dependency-direction guard allowlists add only `estate/adapters/postgres_evidence_money_read.py` and `estate/evidence_money.py` as read-only paths. Rule-8 writer guard gains no exemption.

## Snapshot, sources and identity

Both GETs use W3-01's principal-derived authorized imported Site set and signed `access_basis`; no client tenant/Site list. Required whole UTC-day `[from,to)`, maximum 31 days; `known_at` optional and defaults to captured DB time, must be UTC and no later than DB time. UI first load is the last complete UTC day; changing window/cutoff resets cursor. One read-only REPEATABLE READ transaction captures grant, Site selection, source contacts, W1 S3/S4 heads, cold `ColdReadService._snapshot(c,...)` and `ColdSiteReadService` connection-taking projections, EV `EvReadService._snapshot(c,...)` and `EvSiteReadService` connection-taking projections, exact financial revisions and full cited accepted-ID sets. Never compose per-Site HTTP calls or independent transactions. All cards and groups derive from the full scoped rows before paging.

W1 mini-grid capability source is its reviewed Site Evidence and `analytics/claim_limit_read.py:ClaimLimitReadService` selection, with `analytics/finding_index.py` for canonical Finding identity. W1 money source is `financials/consequence_read.py:ConsequenceReadService`, `financials/money_eligibility.py` and `evidence/provenance_read.py:source_gate`. Extract/use connection-taking selection logic; do not call public services that open another transaction. Cold capability source is `analytics/cold_site_reads.py:_capabilities` and `_sources`; money is its `financials`/`_consequence_row`. EV uses `ev_site_reads.py:CLAIMS`, selected `evidence` and `financials`/`EvMoneyReads`, including the full W2-07 selected session set, never its page. Check actual merged symbols at build handoff.

`source_provenance` on a represented row has exactly W3-01's six required keys `{classification,state,source_ids,evidence_ids,basis_sha256,reasons}` (estate omits `detail`). Select the **row's** revision IDs and full exact citations. `classification`/`state` are equal; UNKNOWN/MIXED or missing gate withholds current money. Pending envelope provenance describes newer accepted records separately from prior selected row provenance. Empty citations with a selected revision still have a digest; no selected revision has null digest.

Every authorized Site appears in `coverage.sites`, including one without selection. Capability registry is finite: reviewed W1 Site Evidence keys; cold six `CAPABILITIES`; EV seven `CLAIMS`. Map selected `SUPPORTED`→Full, `LIMITED`→Limited, `UNAVAILABLE`→None; `CONTRADICTORY`, absent selection, stale or pending→Unknown with raw reason; non-applicable→N/A, excluded from denominator. W1 uses its reviewed claim-limit enum, never substring matching. Currentness precedence: explicit old cutoff HISTORICAL; otherwise pending PENDING_RECOMPUTE, stale STALE_SOURCE, missing UNKNOWN, else CURRENT. A missing applicable Site withholds complete-estate cards/groups but known Site rows remain. Historical rows retain exact IDs without current claims.

Recurring gaps group only typed `(gap_code,missing_role)` from selected W1 claim-limit reasons, cold `missing_roles`, EV `NEXT_EVIDENCE` codes. Sort groups by key and Sites by code. Unknown/untyped prose is not a gap key. Each group unions Site IDs and affected capability keys. No priority is invented. A next step is selected stored guidance or an exact dictionary entry for that typed role; otherwise null and `Next step not recorded`. W4-01 cases remain distinct; gaps create no case/Action.

## Evidence wire and state table

`GET /api/estate/evidence?from=&to=&known_at=&limit=25&cursor=`. Limit ASCII integer 1..100, default 25. Capability order `(site_code_key,site_id,capability_key)` ascending. `total_count` is the full selected capability count, not page length; unselected applicable Sites have one `UNASSESSED` placeholder row per domain capability. Gaps are unpaged, bounded by the finite registry. Cursor is W3-01's signed opaque base64url shape extended as `{v:1,kind:"evidence",access_basis,selection_token,from,to,known_at,last:[site_code_key,site_id,capability_key],limit}`. `selection_token` hashes its canonical scope selection plus sorted per-Site assessment/revision IDs and full cited IDs; changed grant/selection/window/cutoff is 409, tamper 422.

```json
{"schema_version":"estate-evidence-1","scope":{"authorized_site_count":1,"covered_site_count":1,"access_basis":"sha256:<digest>"},"window":{"from":"2026-10-06T00:00:00Z","to":"2026-10-07T00:00:00Z","bounds":"[from, to)","known_at":"2026-10-07T00:00:00Z"},"status":"CURRENT","coverage":{"state":"COMPLETE","sites":[{"site_id":"<site-uuid>","site_code":"KOBO-001","domain":"MINI_GRID","state":"CURRENT","selection_ids":["<revision-uuid>"],"source_freshness":"RECENT"}]},"summary":{"limited_site_count":1,"priority_gap_count":null,"unsupported_claim_count":null,"capability_count":1,"full_count":0,"limited_count":1,"none_count":0,"unknown_count":0},"order":"site_code_key asc, site_id asc, capability_key asc","total_count":1,"rows":[{"site_id":"<site-uuid>","site_code":"KOBO-001","site_name":"Kobo Mini-grid","domain":"MINI_GRID","capability_key":"GENERATOR_SUPPORT","capability_label":"Generator support","raw_state":"LIMITED","readiness":"LIMITED","current_ceiling":"Candidate in supported portions","ceiling_source":"<selected-field>","next_evidence":"<selected-missing-role-copy>","gap_codes":["<typed-code>"],"selected_revision_ids":["<revision-uuid>"],"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:<digest>","reasons":[]},"links":{"site_readiness":"/sites/KOBO-001/evidence"}}],"gaps":[{"gap_code":"<typed-code>","missing_role":"<binding-role>","site_ids":["<site-uuid>"],"site_codes":["KOBO-001"],"unlocks":["GENERATOR_SUPPORT"],"next_step":null,"link":null}],"next_cursor":null,"selection_token":"sha256:<digest>"}
```

Angle-bracket values are fixture substitutions, not production values. Tests resolve exact stored UUIDs. `limited_site_count` is distinct Sites with ≥1 selected LIMITED capability only if every applicable Site selection is complete; otherwise null. `priority_gap_count` is null until a reviewed persisted priority model exists. `unsupported_claim_count` is null: W1/W2 have no cross-domain unsupported-claim census. Cards show `Not assessed`, never mock `3`/`Excluded`. Complete zero is 0; partial is null. An authorized empty scope returns `EMPTY_SCOPE`, zeros, empty rows/gaps and `No accessible Sites`.

| State | Row display | Estate cards |
| --- | --- | --- |
| CURRENT supported/limited/unavailable | Full/Limited/None; exact ceiling | complete counts |
| PENDING_RECOMPUTE | `Updating evidence`; prior row labelled selected history | null |
| STALE_SOURCE | `Source stale`; no current ceiling | null |
| HISTORICAL | `Historical as of {known_at}` | historical labelled counts only |
| UNKNOWN/no selection | `Not assessed`; null ceiling and next evidence | null |
| CONTRADICTORY | `Conflicting records`; raw reason | null affected count |
| NOT_APPLICABLE | N/A, no denominator | unchanged |

## Financial wire and comparability

`GET /api/estate/financials?from=&to=&known_at=&limit=25&cursor=` has the same scope/window/snapshot rules and `kind:"financials"` cursor. Rows order `(window_start desc,site_code_key asc,site_id asc,category asc,consequence_revision_id asc)`, null start last. Select all exact current or historical consequence heads, including unpriced/withheld. One line key is `(tenant_id,site_id,domain,consequence_revision_id)`; absent consequence yields a display gap key `(site_id,domain,finding_revision_id,"UNPRICED")` and null revision, excluded from numeric groups. W1 requires exact `financial_consequence_revision`, eligible money/source gate and supported quantity. Cold `cold_consequence_revision` stays unpriced under W2 CHECK. EV uses the W2-07 exact gross tariff revision only with CURRENT selected basis, complete energy, published tariff and accepted source gate; gross tariff is never collections. Decimal amounts are JSON strings, never floats. Display uses outward rounding by known currency minor unit; grouping uses unrounded Decimal bounds.

Eligible partitions use exact `(category,currency,window_start,window_end,period_kind,assumption_revision_ids)`. Category enum: `CANDIDATE_OPERATING_COST_EXPOSURE`, `POTENTIAL_PRODUCT_EXPOSURE`, `GROSS_TARIFF_SCENARIO`. Period kind: `OBSERVED_WINDOW` or `SCENARIO_WINDOW`. The interval must equal the selected consequence interval; no prorating or extrapolation. Fail closed when an applicable Site is missing/pending, line IDs duplicate, technical input interval IDs or accepted evidence IDs overlap between lines, currency/period/assumption differs, or overlap proof is absent. Groups are `COMPARABLE` with ≥2 distinct eligible lines and all gates true; one line is `SINGLE_LINE`, no estate total. Other states: `UNKNOWN_COVERAGE`, `MIXED_CURRENCY`, `DIFFERENT_PERIOD`, `OVERLAPPING_BASIS`, `INELIGIBLE_SOURCE`, `UNPRICED`, `NO_LINES`. Keep every excluded row and explicit reason; never drop one to manufacture a total. No cross-category total exists. Compare all rows before pagination.

```json
{"schema_version":"estate-financials-1","scope":{"authorized_site_count":1,"covered_site_count":1,"access_basis":"sha256:<digest>"},"window":{"from":"2026-10-06T00:00:00Z","to":"2026-10-07T00:00:00Z","bounds":"[from, to)","known_at":"2026-10-07T00:00:00Z"},"status":"CURRENT","coverage":{"state":"COMPLETE","sites":[{"site_id":"<site-uuid>","site_code":"EV-LAB-001","domain":"EV_CHARGING","state":"CURRENT","selection_ids":["<assessment-uuid>"],"source_freshness":"RECENT"}]},"summary":{"eligible_line_count":1,"unpriced_line_count":0,"withheld_line_count":0,"estate_total":null,"estate_total_state":"SINGLE_LINE"},"order":"window_start desc, site_code_key asc, site_id asc, category asc, consequence_revision_id asc","total_count":1,"rows":[{"line_key":"<consequence-uuid>","site_id":"<site-uuid>","site_code":"EV-LAB-001","site_name":"Depot EV charging","category":"GROSS_TARIFF_SCENARIO","finding_id":"<finding-uuid>","finding_revision_id":"<finding-revision-uuid>","consequence_revision_id":"<consequence-uuid>","window_start":"2026-10-06T08:00:00Z","window_end":"2026-10-06T16:00:00Z","quantity":{"low":"120","high":"120","unit":"kWh"},"amount":{"low":"36.00","high":"36.00","currency":"USD"},"period_kind":"SCENARIO_WINDOW","assumption_revision_ids":["<tariff-uuid>"],"basis_evidence_ids":["<accepted-uuid>"],"technical_interval_ids":["<interval-uuid>"],"eligibility":"ELIGIBLE","limit":"Gross tariff scenario; not cash collected.","source_provenance":{"classification":"REGISTERED_SIMULATION","state":"REGISTERED_SIMULATION","source_ids":["<source-uuid>"],"evidence_ids":["<accepted-uuid>"],"basis_sha256":"sha256:<digest>","reasons":[]},"links":{"site":"/sites/EV-LAB-001","bridge":"/sites/EV-LAB-001/financials","evidence":"/sites/EV-LAB-001/evidence"}}],"groups":[{"category":"GROSS_TARIFF_SCENARIO","currency":"USD","window_start":"2026-10-06T08:00:00Z","window_end":"2026-10-06T16:00:00Z","period_kind":"SCENARIO_WINDOW","assumption_revision_ids":["<tariff-uuid>"],"state":"SINGLE_LINE","line_keys":["<consequence-uuid>"],"amount":null,"reason_codes":[]}],"exclusions":[],"next_cursor":null,"selection_token":"sha256:<digest>"}
```

The example's 120 kWh/$36 are mock substitutions; production/tests use actual W2-07 stored values. `groups[].amount` is `{low,high,currency}` only for COMPARABLE, otherwise null. `summary.estate_total` is always null because there is no sound cross-category sum. MIXED_CURRENCY/DIFFERENT_PERIOD are diagnostics across candidate partitions, never conversion or a merged group. Financial state is not an assessment enum.

| Line condition | `eligibility` | Value / group |
| --- | --- | --- |
| Exact current eligible W1/EV | ELIGIBLE | bounded amount; compare basis |
| Cold product exposure/no price | UNPRICED | `Unpriced`; excluded |
| Missing selection/price | UNKNOWN | `Unknown`; total withheld |
| Pending newer evidence | PENDING | `Updating`; prior history only |
| Earlier cutoff | HISTORICAL | `Historical scenario`; no current total |
| UNKNOWN/MIXED source, price conflict, stale basis | WITHHELD | `Withheld · reason`; no total |
| Technical overlap | CONFLICT | `Not comparable`; no total |

## Mock panel, column, chip, row and destination ledger

The sources are `frontend/mockups/v69/screens.js:522-534`, manifest IDs `globalevidence`/`globalfinancials` and `v69-rendered-panels.json` (two named panels per screen). The mock's three Sites, `3` cards, `$36`, `120 kWh`, Action codes and links are illustration, never seed data. Use `ProductStatus`, `Panel`, `DataTable`, `Disclosure` and the existing period bar. No page component guesses a route; it consumes a reviewed route builder. Header/table stays visible for zero rows. Source fields below are the exact W3-02 wire keys specified above.

| Mock element | Ruled field, copy and action |
| --- | --- |
| Evidence card `Sites with limited claims` and `All three domains have explicit gaps` | `summary.limited_site_count`; denominator is `scope.authorized_site_count`. Null: `Unknown · some Site evidence is unavailable`. Zero only on complete selection. |
| `Priority evidence actions`, mock `3` and PCS/loading/session copy | `summary.priority_gap_count` is null until persisted priority exists; show `Not assessed`. Typed `gaps` remain visible; no inferred Action priority. |
| `Unsupported claims`, mock `Excluded`/loss-spoilage-RUL | `summary.unsupported_claim_count` is null; show `Not assessed`. The static notice explains the boundary without asserting a count. |
| `Capability coverage across sites`: `Site / domain` | `rows[].site_name`, `domain`, `site_code`; link `links.site_readiness` with selected window/cutoff if target supports it. Kobo/GreenHarvest/Depot are examples, not fixed rows. |
| `Operational capability` | `capability_label` from finite domain dictionary; exact `capability_key` in Disclosure. W1 generator support, cold temperature/backup and EV session/availability are represented only when selected. All other selected capabilities appear too. |
| `Readiness` chip | `readiness`: FULL green, LIMITED amber, NONE gray, UNKNOWN gray, CONTRADICTORY red, N/A gray; pending amber/historical blue context shown separately. Raw state in Disclosure. |
| `Current ceiling` | `current_ceiling` with `ceiling_source`; null `No current ceiling`. Never copy candidate/observed ceiling from the mock unless selected claim field says it. |
| `Next evidence` | `next_evidence`; null `Not recorded`. Mock PCS/loading/session advice requires exact typed role or selected guidance. |
| Capability panel footnote | Static `Each row links to Site-owned readiness. This page does not independently score claims.` |
| `Recurring evidence gaps`: `Gap` | typed `gap_code` + `missing_role` display dictionary. The four mock gap examples are shown only when their typed pairs occur. |
| `Sites` | sorted `site_codes` from full group, each Site link only when route exists; no mock pair presumed. |
| `Unlocks` | `unlocks` mapped to capability labels; no speculative claim. |
| `Next step` | `next_step` or `Next step not recorded`; `link` only for an exact persisted Action or reviewed route. Mock `ACT-049, ACT-061`, `Map transfer switch`, Operational records and Preventive plan targets are inert `Not available yet` until supported. No use of `UnavailableEntry` beyond closed multiset. |
| Evidence notice | Static `Source connectivity is not physical asset health. Evidence Full/Limited/None/N/A is separate from Healthy/Watch/Degraded.` |
| Financial status blue chip/subcopy | Static `Site-owned consequences`; `Values grouped by basis and period; no financial assessment`. No invented assessment enum. |
| `Consequence register`: `Site` | `rows[].site_name`/`links.site`; exact Site route. |
| `Category` | enum dictionary: `Candidate operating-cost exposure`, `Potential product exposure`, `Gross tariff estimate`; no new category inferred from title. |
| `Window / quantity` | `window_start/end`, `quantity.low/high/unit`; null `Window or quantity not established`. Render UTC dates/time, `6 Oct · 14:20–15:20` format only if exact bounds support it. |
| `Value` | `amount.low/high/currency` outward display if ELIGIBLE; otherwise `Unpriced`, `Withheld`, `Unknown`, `Historical`, or `Not comparable` per eligibility. No mock `$36` fallback. |
| `Basis / limit` | `assumption_revision_ids`, `limit`, group `reason_codes`; no `Modelled fuel + scenario accrual` unless W1 selected line says so. |
| `Source` | `links.bridge` labelled `Site bridge →`, or `links.evidence` labelled `Site evidence →`; null `Source detail unavailable`. Exact selected revision IDs stay in detail URL where target supports them. |
| Register footnote | Static `No independent repricing or technical re-derivation`. |
| Financial notice | Static `These values are not an additive profit or savings total. Categories, time periods, uncertainty and overlapping technical bases differ.` |
| `Aggregation rule` panel | Static mock prose `Aggregate distinct eligible consequence-line IDs by category, currency and compatible window. Reuse the exact Site consequence revision; preserve exclusions and assumption references.` Below it render `groups`/`exclusions` reason chips; `COMPARABLE` only gets a numeric group amount. |

The mock Evidence destinations `evidence`, `temperature`, `availability` map to selected Site Evidence/readiness, not a global raw browser. The financial mock `financials`, `temperature`, `energy` map to the corresponding Site financial bridge/evidence route. Site routes must be checked against `operatorSiteRoutes.ts` after W3-01 merge: mini `/sites/{code}/evidence` and `/financials`, cold `/sites/{code}/cold/evidence` and `/cold/financials`, EV `/sites/{code}/ev/evidence` and `/ev/financials` are semantic targets, not permission to invent a path. A missing target is plain `Site detail unavailable`. Preserve `from,to,known_at` only on targets that accept all three; otherwise label `Opens current Site view` and do not imply cutoff is carried.

## Refusals and UI states

API errors use `{detail:{code,message}}`, or W3-01's frozen estate error wrapper if the reviewed merge differs, with these code/message pairs unchanged. Check auth, grant and disclosure before parsing values; then snapshot. 401 `UNAUTHENTICATED`: `Sign in to view estate evidence and financials.` 403 `ESTATE_SCOPE_FORBIDDEN`: `You do not have access to this estate view.` A forbidden Site source disclosure is 403 `ESTATE_SOURCE_DISCLOSURE_FORBIDDEN`: `Source details for one or more Sites cannot be shown.` No forbidden name or count leaks. 404 `ESTATE_SITE_NOT_FOUND` applies only to an exact Site/detail lookup, not an empty global index: `This Site is no longer in the selected estate.` 503 `ESTATE_READ_UNAVAILABLE`: `Estate data is temporarily unavailable. Try again.` Clear prior privileged data on 401/403/404/503. 409 `ESTATE_BASIS_CHANGED`: `The selection changed. Refresh to see the latest basis.` 422 `INVALID_WINDOW`: `Choose a UTC window of up to 31 days with a start before its end.` 422 `ESTATE_PARAMETER_UNKNOWN` or `ESTATE_CURSOR_INVALID`: `This selection cannot be read. Reset the filters.` Repeated/unknown keys refuse; no unbounded list. Global 404 is unreachable in normal UI since no Site parameter exists. On refusal, return `rows:null,total_count:null` plus `groups:null` (money) or `gaps:null` (Evidence); never an empty success shape.

| Page state | Display |
| --- | --- |
| Loading | labelled skeleton per card/panel, no zero |
| Complete stocked | exact rows/group reasons |
| Complete empty authorized scope | `No accessible Sites` |
| Scope with no selected result | `No selected evidence for this window` / `No consequence lines for this window` |
| Partial/pending | known rows plus `Some Sites are still being assessed`; totals null |
| Historical | `Historical as of {known_at}` on all affected values |
| Conflict | `Source or basis is unresolved`; money withheld |
| 401/403/404/503 | exact copy above, prior privileged rows removed |

## 1440/390 panel budget

The v69 rendered-panel inventory measures **two named panels per screen**; `screens.js` adds a three-card Evidence row and a Financials status bar. There is no checked-in per-panel pixel measurement, so the Architect sets explicit build caps and requires a pre-review browser measurement of the mock DOM at both widths. Do not report these caps as observed pixels. In a three-Site stocked variant, app panel height may exceed the measured mock by at most max(24 px, 10%); real extra rows may scroll inside the table without clipping. At 390, cards stack and tables get a horizontal scroll region; the document itself must have no horizontal overflow.

| Region | 1440 cap | 390 cap | Measurement to record before review |
| --- | ---: | ---: | --- |
| Evidence three-card row | 220 px | 430 px | cards container rect and each card rect |
| Capability coverage panel | 500 px | 560 px | panel rect; table client/scroll width |
| Recurring gaps panel | 390 px | 460 px | panel rect; table client/scroll width |
| Financial status bar | 96 px | 120 px | status rect |
| Consequence register panel | 500 px | 560 px | panel rect; table client/scroll width |
| Aggregation rule panel | 250 px | 330 px | panel rect |

If the measured mock is taller, its measurement plus tolerance governs. Commit 2/4 handoff includes mock/app rectangle values and screenshots for both widths. Blank estimates do not pass review.

## Fixtures and proof

Use private `assetops_w302_*_test` Postgres DBs. Import `var/sites/kobo-001.yaml`, `backend/tests/fixtures/w2/cold-lab-001.yaml`, `backend/tests/fixtures/w2/ev-lab-001.yaml`; codes are `KOBO-001`, `COLD-LAB-001`, `EV-LAB-001`. Cold accepted IDs are in `contract-fixtures/w2/cold/normal.json` (first `00000001-0000-4000-8000-00000000014c`); EV IDs in `contract-fixtures/w2/ev/complete.json` (first `00000501-0000-4000-8000-000000000199`). Reuse real replay setup from `test_w202_cold_replay_postgres.py:383-445`, `test_w205b_ev_replay_postgres.py:531-893`, and W2-07 money tests. Capture generated Site/assessment/Finding/consequence/assumption IDs from public reads; independently compare to scoped DB rows. Do not assert invented UUIDs. Add a fourth authorized imported Site with no selection and a foreign-tenant Site in the test factory; prove different treatment.

Variants: pending later accepted record, UNKNOWN/MIXED provenance, cold unpriced, EV incomplete/tariff gap, two eligible same-category lines with disjoint technical IDs, overlapping IDs, different windows and currencies. Literal injected IDs are allowed only in pure grouping tests. Commit 3 tests also prove Decimal arithmetic, duplicate collapse, overlap rejection, page-size invariance and historical cutoff. API tests cover auth before value validation, repeated/unknown keys, 401/403/404/409/422/503, tampered cursor and changed grant. UI tests cover every table column/chip/destination, state-table row and inert mock-only links. One same-revision full suite: `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder` on real Postgres. Run `tools/check-all.ps1`, architecture/workflow/rule-8/navigation/dependency checks and frontend build. Lane A closes reviewed paths for `globalevidence:1-2`, `globalfinancials:1-2`, cards/status/notices under `A-evidence-shared-projections`, `A-money-comparability`, `A-money-projections`, `I-evidence-health-store`, `I-money-followon-store`, `D-evidence-variants`, `D-money-comparison`; existing nodes alone do not prove panel readiness.

Commit dry-read: commit 1 resolves domain enums before projection; commit 2 makes no Action/case from a gap; commit 3 withholds totals on any absent overlap/currency/period/source/Site proof; commit 4 renders server states without client scoring. W4-01 case identity is neither a gap nor a consequence. W3-03 Portfolio consumes these DTOs but cannot turn ineligible lines into an objective total. Upstream contract drift goes to Architect with affected tests before a builder decides it locally.
