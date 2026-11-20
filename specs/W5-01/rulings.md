## W5-01b C4/C5 pre-flight rulings (Codex Architect, 2026-10-22)

These rulings supersede conflicting C4/C5 text above and close every item in `task/W5-01b-cold-scenarios:.agent/W5-01b-phase-handoff.md`. They are design instructions, not implementation or acceptance. **Base:** W5-01a must merge to main first. Recreate/reset the no-code W5-01b branch from that merged main head, preserving its handoff, before implementation. Do not merge unmerged W5-01a into the old branch. For W6-01a Lane B overlap in `main.py`, `App.tsx`, `operatorSiteRoutes.ts`, `navigation-truthfulness.ps1` and `navigation-rail-fixtures.ps1`, rebase and preserve both domain-specific additions; run focused tests and guards. (P-G-1/2)

### C4 store and API closure

**P-C4-1: existing test ownership.** Add all 16 files below to C4. Change only a latest-head/rollback assertion from `0030_w4_mini_decisions` to `0032_w5_cold_scenarios`; retain references to 0030 as the migration under test, predecessor, filename and refusal message. Every downgrade from `head` crosses an **empty** 0032 before reaching older revisions, and rollback assertions name the actual starting head.

| File(s) | Exact edit |
| --- | --- |
| `backend/tests/mini_depth_probe.py` | `MINI_HEAD` becomes 0032; prepare empty 0032 and traverse it before 0029. |
| `backend/tests/test_s1_bindings_postgres.py`, `test_s2_evidence_ledger_postgres.py`, `test_s405_publication_postgres.py`, `test_s4_consequence_store_postgres.py`, `test_s4_evidence_consequence_work_postgres.py` | Change latest-head assertions (including evidence/consequence/work rollback lines 537 and 568) to 0032. |
| `backend/tests/test_w200_source_events_postgres.py`, `test_w201_cold_foundation_postgres.py` | Change respectively three and two latest-head/rollback assertions to 0032. |
| `backend/tests/test_w203_cold_migration_postgres.py`, `test_w204_cold_migration.py`, `test_w205a_ev_migration.py`, `test_w206_ev_migration_postgres.py`, `test_w207_ev_money_postgres.py`, `test_w401_migration_postgres.py`, `test_w402_migration_postgres.py` | Change latest-head constants `HEAD`/`UPGRADED_HEAD` to 0032; keep each older migration's target/predecessor and downgrade assertions. |
| `backend/tests/test_w403_migration_postgres.py` | Keep `HEAD = "0030_w4_mini_decisions"` for the W4 migration under test; add `LATEST_HEAD = "0032_w5_cold_scenarios"`; assert `script.get_heads() == [LATEST_HEAD]`, `script.get_revision(HEAD).down_revision == PREVIOUS`. For 0030 downgrade tests starting at head, downgrade empty 0032 to `HEAD` first; retain the 0030 catalog/refusal expectations. |

**P-C4-2/3/4/5/6.** In `tools/writer_guard_probes.py`, add `COLD_SCENARIO` beside `DECISION`; put `_cold_scenario_only`, `_cold_scenario_unseen` and the `NEGATIVE += [...]` block after `decision truncate` at ~794; put the two `WRITER_CONTROLS += [...]` entries **after** `WRITER_CONTROLS` at ~798 and `_work_control` at ~860 (after existing decision controls at ~885). The earlier step 7 whole-block placement is revoked; run `python tools/writer_guard_probes.py --seam` and prove import has no NameError. In 0032 add `cold_scenario_immutable` and `cold_scenario_revision_immutable` `BEFORE UPDATE OR DELETE` triggers using `ledger_append_only()` as 0030 does. `cold_scenario_site_order` belongs to `cold_scenario_revision(tenant_id,site_id,recorded_at DESC,id DESC)`, not the root; tie-break by `scenario_id`. Downgrade locks/counts both new tables, refuses nonempty history with `Downgrade of 0032_w5_cold_scenarios refused: cold scenario history exists`, then on empty drops triggers, index, revision, root, sequence. `test_migration_constraints` covers catalog, triggers, nonempty refusal and empty downgrade/re-upgrade. C4 writer transactions start `REPEATABLE READ` before `basis_on`; `snapshot()` starts `REPEATABLE READ READ ONLY` and obtains default `scenario_at=clock_timestamp()` once there. Retry a unique insert race by rereading the key; final serialization/store failure is 503 `DECISION_STORE_UNAVAILABLE`, never a fabricated 409.

**P-C4-7 through 14, 21.** Every C4 refusal is `{error:{code,message}}`; `cold_scenarios_api.py` owns a local mapper, including `DecisionRefused`, rather than importing private cold router helpers. Reuse `mini_decisions.model.MESSAGES` for `DECISION_*`. New message literals: `COLD_SCENARIO_INVALID` → `The cold scenario request or selected basis is invalid.`; `COLD_SCENARIO_CURSOR_INVALID` → `The cold scenario cursor is invalid.`; `COLD_SCENARIO_CURSOR_BASIS_CHANGED` → `The selected cold scenario basis changed. Start at the first page.`; `COLD_SCENARIO_IDEMPOTENCY_CONFLICT` → `This idempotency key belongs to a different cold scenario request.`; `COLD_SCENARIO_REVISION_CONFLICT` → `The cold scenario has a newer revision. Reload it before correcting.`; `COLD_LIMIT_INVALID` → `Limit must be an integer from 1 to 100.`. Add `DECISION_NOT_FOUND` 404 for unknown/malformed correction root and `DECISION_LINK_SCOPE_INVALID` 422 for a well-formed foreign predecessor. Order: authenticate, Site scope, reject unknown/duplicate query keys (`query_params.multi_items()` in this router), validate window, find Site, check disclosure; POST then requires both `from,to` (`COLD_WINDOW_INVALID` 422 if absent), checks `command_access`, service, principal/actor, body, basis, write. GET may omit both bounds and uses the gate's latest selection; one bound refuses. GET keys are exactly `from,to,known_at,scenario_at,limit,cursor`, POST `from,to,known_at`; invalid limit is `COLD_LIMIT_INVALID` 422. Add `access=` and `disclosure=` kwargs with cold-route defaults alongside `command_access=` and `principal=`. GET selection failure and POST `basis_on` read failure → `COLD_READ_UNAVAILABLE`; store snapshot/write failure and missing C4 service (GET or POST) → `DECISION_STORE_UNAVAILABLE`. Router tests cover all statuses, duplicate keys and the error envelope.

**P-C4-15 through 20, 22/23.** Trim/store `name` (1..160 Unicode characters), `stock_unit` (1..64 printable non-control characters). Decimal regex `^(?:0|[1-9][0-9]{0,17})(?:\.[0-9]{1,8})?$` and numeric >0; preserve valid input strings verbatim, reject signs, exponent, `.5`, `5.`, leading zeros and excessive digits. `currency` is `^[A-Z]{3}$` and an ISO 4217 code-list member; no coercion. One body currency requests no conversion, and the Site currency is undeclared; the earlier conversion-refusal sentence authorizes no conversion and has no C4 trigger. POST may save a nonempty selected basis in `PENDING_RECOMPUTE`, `STALE_SOURCE` or `HISTORICAL` with its actual state/cutoff; no assessment or Foundation still refuses. Use `work.canonical_json` and SHA-256. Create hash input is `{command:<validated body excluding idempotency_key>,site_id:<UUID>,window:{from:<resolved>,to:<resolved>,cutoff:<resolved>}}`; revision-1 `payload_sha256` equals it. Correction hash includes corrected body, root ID and resolved same root window/cutoff. `basis_sha256=sha256(canonical_json(authored_basis))`. Key replay reads stored canonical input and prior resolved cutoff **before** resolving a new basis, returns 200 even if that basis no longer resolves; changed explicit cutoff/body conflicts. Omitted `known_at` on a new request resolves to the selected watermark. A C4 in-process seed test injects `DecisionPrincipal`/`GRANT_PREFIX`; the served `lab_app` host remains read-only. It GETs the list after first POST and saves that response's `scenario_at`, then corrects later; no write DTO clock is invented. List orders selected revisions by `(recorded_at DESC,id DESC,scenario_id)` and filters root window plus `authored_basis.cutoff <= known_at` in parameterized SQL; malformed persisted basis is 503. Reuse mini cursor codec with C4 code translation; bind tenant/Site, selected window and digest, `known_at`, `scenario_at`, limit and last tuple. Omitted page-two clocks inherit cursor clocks; explicit mismatch is 409 basis changed. Test replay after evidence advance, hashes, 51-row paging, historical correction and malformed basis.

### C5 mock and UI closure

**P-C5-1 through 5.** The `cold-scenarios` mock (`frontend/mockups/v69/index.html:859,861`) controls the Site-name h1, `Financials · scenarios (placeholder)` description, `Financial scenarios` panel with subtitle `Placeholder · to be designed with the owner`, evidence-icon empty block with h3 `No scenario defined yet` and paragraph `A scenario compares a declared what-if with the measured case, for example a different stop setting, stock value or tariff. None has been defined for this site.`, then the existing exact `Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.` notice in **blue**. Add `frontend/src/ui/V69Layout.tsx` to C5 and restore its scenario description. `Scenarios` is breadcrumb/tab, never h1. Amber currentness notice comes before the panel when needed; blue notice after it. Restore exact empty form/copy; no extra status strip. **MOCK DEVIATION (D4) — authored rows:** the mock panel has only an empty block; real C4 definitions replace that block with the card's table, disclosure and pager inside the same titled/subtitled panel. Retaining only the empty mock hides real definitions; inventing comparison values misstates evidence. **MOCK DEVIATION (D4) — currentness notice:** the mock only has its blue closing notice; pending/stale/historical selection adds the amber notice above the panel so an old basis is visible. Hiding currentness or burying it in empty copy would mislead on populated rows. The earlier authored-row/pending deviations are consolidated here; no other mock departure is authorized.

**P-C5-6/7/8.** Add `frontend/src/test/productVocabulary.json`, `frontend/src/test/productVocabulary.ts` and `frontend/src/sites/__tests__/coldSiteViews.test.tsx` to C5. The generic W1 set includes T028's `scenario`/`scenarios`, so merely skipping T028 does not work. Extend the JSON with `screenGlosses` entries keyed by screen ID and exact string, and update `scanProductVocabulary` in `productVocabulary.ts` to remove only exact gloss matches for its supplied screen ID before applying the existing T028+W1 scan; keep existing global glosses and T028 terms unchanged. The allowed screen IDs are `cold-scenarios`, `cold-financials`, `cold-assumptions`, and their allowed texts are `Scenarios`, `Financial scenarios`, `No scenario defined yet`, the exact mock empty paragraph and blue notice, `Authored scenario`, `Cold scenarios unavailable`, the loading/network/malformed-200 C5 strings. Do not filter violations in tests or exempt whole panels. The stocked `coldSiteViews.test.tsx` W1 scan must accept the now-live Scenarios link using that screen glossary and still fail on an unglossed banned word; assert its live href. `coldScenarios.test.tsx` scans the full page with `set:"w1"`. Print `STOCK_VALUE_CONTEXT` as `Stock value context`, source classifications as plain words (`Unknown`, `Mixed`, etc.), and assumption keys as `Stock quantity`, `Stock unit`, `Unit value`, `Currency`. Only actual UUIDs/codes as source IDs use `data-vocabulary-exempt="source-reference"`.

**P-C5-9 through 16.** Add `frontend/src/sites/coldScenarios.css` for scoped mock empty icon, expansion row, wrapping and 390 scroller; import it from `ColdScenarios.tsx`. Keep `App.tsx` Lab `coldScenarios?: ColdScenarioChoiceClient`; Site list prop is `coldScenarioList?: ColdScenariosClient`, default `HttpColdScenariosClient` from `sites/coldScenariosClient.ts`. `siteFinancialScenariosHref(siteId, query?: {from?:string;to?:string;known_at?:string;scenario_at?:string})` adds defined encoded keys in that order, leaving one-argument mini callers intact. Cold Overview/Assumptions pass `scenarios="live"` and carry `from,to,known_at` to Scenarios; Scenarios back-links carry those three and drop authored-only `scenario_at`. Non-cold/non-mini fallback `Scenarios are read for mini-grid sites only.` stays; EV's unavailable slot stays. Guard anchors in `navigation-truthfulness.ps1`: cold branch `site_type === "COLDCHAIN"`, `scenarios="live"`, `<ColdScenarios`; non-cold fallback `<UnavailableTab label="Scenarios" />`. In `navigation-rail-fixtures.ps1`, positive fixture removes `<ColdScenarios` and expects `the cold Financials Scenarios destination is live`; negative fixture removes fallback unavailable literal and expects `the W1-plus-W2 inventory is exactly`; anchor to branches so another occurrence cannot pass. Keep `$expectedTabs`' two Scenarios. Show `SelectedWindowBar` (`from,to,known_at`) and `Scenarios created through {scenario_at UTC}`; refused query uses `RequestedWindowBar`. Validator requires lowercase UUIDs for Site/item/revision/selected arrays/nullable Foundation, UTC ISO instants for window/cutoff/scenario/recorded clocks, exact provenance object with C1 keys and string classification, sorted/deduped arrays, and closed keys throughout. `known_at`/cutoff may be null only on an unavailable selection; do not format null as a date. Malformed 200 is unavailable. Add client tests for each type.

**P-C5-12/19/20/22 detail.** Render `<nav aria-label="Scenario pages">` after the table: `First page`, `Next`, `{page} of {total pages}`; `Next` uses `next_cursor`, `First page` clears it, absent next disables it. Test 51 rows. Expansion lines are `Stock quantity: {value}` etc.; `Accepted evidence` is `1 record` or `{n} records`; `Window` is `{from} – {to}`. UUIDs wrap, exact values stay accessible. Internal disclosure scroll max-height 360px **at 390 only**; closed one-row/empty panel cap stays 430/560px (1440/390), expanded 1440 one-row cap 650px. Capture expanded authored and historical at both widths and check no document overflow. `Retry` is a button that refetches the same URL, matching cold siblings; the ledger's word "link" describes its action.

**P-C5-17/18/21.** In refused Finding branch of `ColdAssessmentViews.tsx`, insert `<StatusBar label="Finding state"><Badge tone="neutral">Unknown</Badge><span>Confidence: Unknown</span><span>{siteName}</span></StatusBar>` directly above `PageRefusal`; use `RequestedWindowBar` for the invalid period. `coldRoutes.test.tsx::w2f_finding_strip_confidence` asserts order and no invented loaded state. `cold-finding-refused-unknown` capture is served GET of a real imported W2 Finding detail for `COLD-LAB-001` with `from=2026-10-06T20:05:00Z&to=2026-10-06T19:00:00Z`, returning 422 `COLD_WINDOW_INVALID`; the merged jsdom test alone is not a producer. `coldScenarios.test.tsx::authored_pending_historical_basis` tests UI, while `check_v69_dependency_registry.cjs` and `check_v69_ledger.py` check registry/ledger; vitest need not parse JSON. C5 focused proof is those tests, `coldSiteViews.test.tsx`, `coldRoutes.test.tsx`, both navigation guards and 1440/390 captures.

### P-ID closure table

| IDs | Closing paragraph above |
| --- | --- |
| P-G-1, P-G-2 | Base and Lane B opening paragraph. |
| P-C4-1 | Existing test table (all 16 files and downgrade paths). |
| P-C4-2, P-C4-3, P-C4-4, P-C4-5, P-C4-6 | C4 guard/migration/snapshot paragraph. |
| P-C4-7, P-C4-8, P-C4-9, P-C4-10, P-C4-11, P-C4-12, P-C4-13, P-C4-14, P-C4-21 | C4 refusal, messages, access, keys and 503 paragraph. |
| P-C4-15, P-C4-16, P-C4-17, P-C4-18, P-C4-19, P-C4-20, P-C4-22, P-C4-23 | C4 canonical command/list/producer paragraph. |
| P-C5-1, P-C5-2, P-C5-3, P-C5-4, P-C5-5 | C5 mock paragraph. |
| P-C5-6, P-C5-7, P-C5-8 | C5 vocabulary paragraph. |
| P-C5-9, P-C5-10, P-C5-11, P-C5-13, P-C5-14, P-C5-15, P-C5-16 | C5 route/guard/client paragraph. |
| P-C5-12, P-C5-19, P-C5-20, P-C5-22 | C5 pager/capture paragraph. |
| P-C5-17, P-C5-18, P-C5-21 | C5 W2-F/registry paragraph. |

No P-ID remains open. C4/C5 code, per-unit review, captures and owner acceptance remain future work under the task gates.

### W5-01b build rulings (Q-C5b)

These rulings amend the C4/C5 cards above. They describe required follow-up edits on `task/W5-01b-cold-scenarios`; they do not accept the build or change the mock-deviation list.

1. **Q-C5b-1 — stale mini test.** Add `frontend/src/sites/__tests__/miniDecisions.test.tsx` to the C5 file list. In `scenario_site_type_tabs_and_no_cold_ev_promotion`, change exactly `for (const siteType of ["COLDCHAIN", "EV_CHARGING"])` to `for (const siteType of ["EV_CHARGING"])`. The cold case now owns the live `cold-scenarios` destination; keep the EV fallback assertions. The C5 cold test must assert the live cold branch separately.
2. **Q-C5b-2 — mock pager counter.** The v69 `cold-scenarios` panel keeps its authored-row pager inside `Financial scenarios` (the authored rows are the already labelled MOCK DEVIATION (D4)). Add required integer `total_pages` to the C4 list DTO. In the same read-only snapshot and under the same tenant, Site, selected root window, `known_at`, `scenario_at`, selected-revision and valid `authored_basis.cutoff <= known_at` filters used for `items`, count all matching selected revisions before cursor/limit; set `total_pages = ceil(count / limit)` (`0` for no rows). The count must never include another tenant or a superseded revision. Validate the field as a nonnegative integer in `frontend/src/sites/coldScenariosClient.ts`. Render `<span data-scenarios-page-count>{cursors.length + 1} of {read.total_pages}</span>` after `Next` inside `<nav aria-label="Scenario pages">`; the nav remains absent for the empty block. Add C4 `test_w501_cold_scenarios_postgres.py` assertions for 51 rows at limit 50 (`2` on both pages), zero rows (`0`), and historical revision selection; extend `coldScenarios.test.tsx` for `1 of 2`, `2 of 2`, and malformed/missing `total_pages` refusal. A counter derived from `next_cursor` cannot state the mock's total.
3. **Q-C5b-3 — vocabulary, notice and description.** Confirm the three exact `cold-scenarios` screen glosses `Scenario pages`, `Financials · scenarios (placeholder)`, and `Underlying evidence is being reassessed; the authored scenario remains separate.` They are respectively the ruled pager label, the v69 `cold-scenarios` screen subtitle, and the ruled amber currentness notice. Replace their `why` text's `pending Architect confirmation` with `W5-01b Q-C5b-3 Architect confirmed, 2026-10-22; exact cold-scenarios text only.` Keep the exact-screen glossary boundary. Replace the HISTORICAL notice literal in `ColdScenarios.tsx` with `Read at an earlier evidence cutoff; newer evidence exists.`; assert it in the historical-state test and full-page W1 scan. Confirm `SITE_SCREEN_DESCRIPTIONS.coldScenarios: "Financials · scenarios (placeholder)"` as a separate key: it restores the v69 cold screen subtitle while the existing `scenarios` key continues to serve mini-grid.
4. **Q-C5b-4 — expanded basis height.** The v69 `cold-scenarios` `Financial scenarios` panel stays a panel with an internal authored-basis disclosure (labelled MOCK DEVIATION (D4) above). Keep the 650px expanded one-row cap at 1440 and 560px at 390. In `Basis`, change the outer element to `<div className="cold-scenarios-basis" data-scenario-basis={item.id} role="region" aria-label="Authored scenario basis" tabIndex={0}>` with its existing `<dl>` and every full ID unchanged. In `coldScenarios.css`, put `.cold-scenarios-basis { max-height: 360px; overflow-y: auto; }` outside the media query; remove only the duplicate phone-only max-height/overflow rule, retaining the phone grid rules. This bounds the 95-ID case at both widths and preserves keyboard access to every ID. Extend `coldScenarios.test.tsx::row_disclosure_and_client` with a 95-ID basis: expand, assert the region contains all 95 full IDs in order, has `tabIndex=0`, and has computed `max-height: 360px`/`overflow-y: auto` at 1440 and 390. Recapture `cold-scenarios-authored-expanded` and `cold-scenarios-historical-expanded` at both widths; assert the panel/page caps and no document overflow.
5. **C4 Low deviation — malformed stored basis.** A persisted candidate revision whose `authored_basis` lacks any of `from`, `to`, or `cutoff` is malformed history and the GET answers 503 `DECISION_STORE_UNAVAILABLE` in `{error:{code,message}}`; it must not silently vanish from the list. Check shape for candidate revisions selected by tenant/Site/window/time before applying the cutoff predicate, then apply the predicate to well-formed bases. Add a real-Postgres list test inserting such a revision and asserting 503 and no partial 200. This follows the existing C4 malformed-persisted-basis ruling.
6. **Blue notice icon.** The v69 `cold-scenarios` closing blue notice uses `notice()`'s `info` icon before its paragraph (`frontend/mockups/v69/index.html`, `scenariosScreen` and `notice`). In `ColdScenarios.tsx`, keep `<Notice tone="blue" data={{ "data-scenarios-closing-notice": "" }}>`, but make its children exactly `<svg className="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 10v7 M12 7v1" /></svg><p>{SCENARIOS_CLOSING_NOTICE}</p>`. Assert the SVG precedes the paragraph in `coldScenarios.test.tsx` and check the 1440/390 captures. Do not change every shared `Notice` consumer for this local mock element.
7. **C4 builder choices.** Confirm the JSON-object constraints `cold_scenario_revision_assumptions_check` and `cold_scenario_revision_authored_basis_check`; the constraint names are catalog detail and both must reject non-object JSON. Confirm correction hash = canonical corrected body + root ID + resolved root window/cutoff; `site_id` is already fixed by the scoped root lookup. Confirm cursor binds `limit`, so an explicit different page-two limit yields 409 `COLD_SCENARIO_CURSOR_BASIS_CHANGED`. Confirm actor authorization precedes body validation, consistent with the ruled POST order. Confirm `basis_on` database/read failure yields 503 `COLD_READ_UNAVAILABLE`. Confirm the fixed ISO 4217 membership list used at write validation (no runtime network lookup or coercion); retain the regex and code-list tests. Confirm repeated query keys yield `COLD_PARAMETER_UNKNOWN` in the shared cold error envelope. These choices need no code change; the malformed stored basis is ruled separately in item 5.

### W5-01b build rulings (Q-C5c)

These amend Q-C5b items 5 and 6 and the phone-width part of item 4. Checked against `tools/checks/shell-overflow.ps1` rule 5, the actual `RailIcon` fixed-size allowance, `DataTable`'s named horizontal scroller, the v69 `scenariosScreen`/`notice` and `.notice` layout, and the C4 list query on `task/W5-01b-cold-scenarios` at `ffc444c5`.

1. **Q-C5c-1 — blue notice info icon.** Add `frontend/src/ui/RailIcon.tsx`, `frontend/src/sites/ColdScenarios.tsx`, `frontend/src/sites/coldScenarios.css`, and `frontend/src/sites/__tests__/coldScenarios.test.tsx` to the C5 follow-up file list. In `RAIL_ICON_PATHS`, add `info: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18 M12 10v7 M12 7v1"` (the exact v69 `info` path). `RailIcon` already draws an 18×18 fixed-size SVG in the module allowed by rule 5; do not register the page module or draw an SVG there. Replace the held comment and string-only children in the closing notice with `<RailIcon name="info" /><p>{SCENARIOS_CLOSING_NOTICE}</p>` inside the existing `<Notice tone="blue" data={{ "data-scenarios-closing-notice": "" }}>`. Add `.v69-notice[data-scenarios-closing-notice] { display: flex; gap: 10px; align-items: flex-start; }` and `.v69-notice[data-scenarios-closing-notice] p { margin: 0; }` in `coldScenarios.css` to match the mock's blue notice composition. In `coldScenarios.test.tsx`, assert the first child is `svg[data-rail-icon="info"]`, its path is the exact literal above, and the following child is the closing-copy paragraph. Run `tools/checks/shell-overflow.ps1` through `tools/check-all.ps1` and inspect the 1440/390 captures.
2. **Q-C5c-2 — 390 expanded row.** Keep the five mock-style columns, the `DataTable` scroll region, the expansion `<tr><td colSpan={5}><Basis item={item} /></td></tr>`, every full basis ID, and the 1440 rule `max-height: 360px`. Add this literal phone rule in `frontend/src/sites/coldScenarios.css` (the existing one-column `dl` rule remains): `@media (max-width: 640px) { .cold-scenarios-panel .data-table { min-width: 820px; } .cold-scenarios-panel .data-table tr > :nth-child(3) { min-width: 190px; } .cold-scenarios-basis { max-height: 220px; } }`. The Basis summary cell now has a readable width and scrolls sideways inside `DataTable`; the 95-ID detail scrolls vertically inside its focusable named region. The shorter phone viewport supersedes Q-C5b-4's 360px phone height only. The v69 cold Scenarios mock has one full-width `Financial scenarios` panel and a blue notice at 390; this preserves that panel, its table deviation and its internal scroll without a document-width spill or letter-by-letter Basis text. Add a browser layout assertion at 390 for the 95-ID expanded producer: panel height `<= 560px`, document `scrollWidth <= clientWidth`, Basis cell width `>= 190px`, computed basis `max-height: 220px` and `overflow-y: auto`, and the table scroller's `scrollWidth > clientWidth` with the far columns reachable. Keep the 1440 `<= 650px` assertion and recapture authored-expanded and historical-expanded at both widths; adjust the existing computed-height test to expect 220px at 390.
3. **Remaining 503 Low — root revision 1 without its window.** In the **list** read, not a selected-item read, add a preflight in `backend/assetops_backend/cold_scenarios/store.py` and invoke it from `ColdScenarioService._list` in `backend/assetops_backend/cold_scenarios/service.py` within the existing read-only snapshot, after `scenario_at` and Site/basis resolution but before the `if window["from"] ...` candidate/head/count block. Query `cold_scenario` joined to its `cold_scenario_revision` revision 1, restricted to the requested `tenant_id`, `site_id`, and `f.recorded_at <= :scenario_at`; if `f.authored_basis->>'from' IS NULL OR f.authored_basis->>'to' IS NULL`, raise the existing `DECISION_STORE_UNAVAILABLE` 503 through `_store_unavailable()`. Do **not** first apply `_CANDIDATES`' root-window predicate: a missing `from`/`to` cannot pass it. This site-wide check is necessary because a malformed root has no trustworthy window to associate with any narrower list. Retain `malformed_candidates` for matching-window revision/cutoff shape and run it before the cutoff predicate. Add a real-Postgres test in `backend/tests/test_w501_cold_scenarios_postgres.py` that inserts a separate revision-1 root missing `from`, then one missing `to`, alongside a valid root; for each, `GET` with the valid window (and `limit=1`) returns 503 `{error:{code:"DECISION_STORE_UNAVAILABLE",message:...}}` with no `items`/partial 200. Assert a different tenant or Site's malformed root does not poison this list, and a historical `scenario_at` before the malformed revision still lists the valid root.

### Executable registry and ledger amendment

Apply these exact JSON objects to the registry in the named unit only. Insert each node once; append each panel once. For the three cold screens, set `registry_dependencies.product_node_id` to `P-cold-area` and `registry_dependencies.node_ids` to the ordered unique concatenation of that screen’s panel `requires` arrays. C3 owns cooling and cold-health ledger edits; C5 owns cold-scenarios. Status remains `gap` and nodes remain `open` until independent review.

**C3 — registry nodes**

```json
[
  {
    "id": "I-W5-cold-depth-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-01a",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-cold-depth-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections",
      "I-W5-cold-depth-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-01a",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**C3 — panel rows**

```json
[
  {
    "screen_id": "cooling",
    "panel_index": 1,
    "title": "Recovery curves",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "W5-01a selected first steps do not establish an ordered recovery curve."
  },
  {
    "screen_id": "cooling",
    "panel_index": 2,
    "title": "Context normalization",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Ambient is not selected by the W2 cooling assessment; loading and defrost roles are absent, so those context rows show Unknown."
  },
  {
    "screen_id": "cooling",
    "panel_index": 3,
    "title": "Next best evidence",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Evidence actions are bounded to existing Backup and Temperature destinations."
  },
  {
    "screen_id": "cold-health",
    "panel_index": 1,
    "title": "Condition and evidence",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Selected start and probe observations do not establish physical equipment health."
  }
]
```

C3 ledger `cooling`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-depth-read", "I-W5-cold-depth-ui", "D-cold-domain"]}.

C3 ledger `cold-health`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-depth-read", "I-W5-cold-depth-ui", "D-cold-domain"]}.

**C5 — registry nodes**

```json
[
  {
    "id": "I-W5-cold-scenario-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-01b",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-cold-scenario-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections",
      "I-W5-cold-scenario-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-01b",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**C5 — panel rows**

```json
[
  {
    "screen_id": "cold-scenarios",
    "panel_index": 1,
    "title": "Financial scenarios",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-scenario-read",
      "I-W5-cold-scenario-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Authored stock-value context is listed without observed loss or an outcome claim."
  }
]
```

C5 ledger `cold-scenarios`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-scenario-read", "I-W5-cold-scenario-ui", "D-cold-domain"]}.

## Readiness closure

| Review item | Closing artifact location |
| --- | --- |
| 1 | C1 producer clock |
| 2 | Shared selected read and C1 links |
| 3 | C1/C2 file lists |
| 4 | C3/C5 registry rows |
| 5 | C1 context table |
| 6 | C1 derivation table |
| 7 | Shared selected read provenance |
| 8 | C2 state matrix |
| 9 | C2 breadcrumb rule |
| 10 | C2 live refusal capture |
| 11 | C2 worst-content cap |
| 12 | C2 navigation fixture |
| 13 | C3 condition matrix |
| 14 | C3 Health composition |
| 15 | C3 table deviation |
| 16 | C4 persisted schema |
| 17 | C4 POST and refusals |
| 18 | C4 list and historical predicate |
| 19 | C5 cold Scenarios branch |
| 20 | C5 query preservation |
| 21 | C5 fixture anchors |
| 22 | C5 vocabulary rule |
| 23 | C5 expanded-basis cap |
| 24 | C5 Finding strip test |
| 25 | C4 one-run card |
| 26 | Shared literal ledger |
| 27 | Gate and guards |
| R1 (review 4) | C3/C5 executable node, panel and ledger JSON below; applied together to a scratch registry and the dependency checker passed on 2026-10-22. |
| R2 | C3 keeps the S7 gateway panel and live Foundation link, names tests and composed page caps. |
| R3 | C4 POST and refusal table use merged 422. |
| R4 | C4 revision-1 window rule and cross-window correction refusal. |
| R5 | C1 accepted door-event ledger read and optional ambient-role distinction. |
| R6 | Health enum includes LIMITED; C3 covers zero, one and two selected probes. |
| R7 | C2/C3 client edit ownership and C3/C5 single node creation. |
| C1q-Q1 (payload keys) | Shared selected read top-level key order; C1 Cooling payload key `cooling`, Health key `health`. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively (rows C1q-\*).* |
| C1q-Q2 (context row keys) | C1 Cooling payload table: `label/state/evidence_ids/duration_seconds` on every row; new `policy_high_deg_c`. |
| C1q-Q3 (several door pairs) | C1 derivation table pairing rule: integer sum, all paired IDs. |
| C1q-Q4 (missing point dropped) | Decided by spec lines 19/53; confirmed, no change. |
| C1q-Q5 (cited IDs) | Shared selected read: `accepted_evidence_ids` = cited union, may include a ledger-absent ID; row/point IDs ledger-present. |
| C1q-Q6 (`cooling_recovery.state`; L4) | C1 derivation table wording and "C1 public W2 helper" `cold_site_reads.cooling_response_state`. |
| C1q-Q7 (Health read) | C1 Health read: `ColdReadService.foundation_on`, asset/component literals, three-row literal table, `NOT_CONFIGURED` predicate. |
| C1q-Q8–Q12 (L1, L2, L3, I1, I2) | C1 follow-up fixes and exact test names. |
| C1q-C2 | C2 DTO, label and link sources (`policy_high_deg_c`, `coldUiHref` `cooling`). |
| C1q-C3 | C3 Health DTO rendering, card values, Asset cell, empty rule, `#site-health-sources-heading`, `coldSiteViews.tsx` in file list. |
| C1q-C4 | C4 basis source read `ColdDepthReadService.basis_on`; `cold_depth.py` in C4 file list. |
| C1q-C5 | Checked: C5 consumes the literal C4 list DTO and existing `siteFinancialScenariosHref`; no unnamed read, role selection, key or guard file found; no change. |
| A1Q-W5S-1 | C1 builder delta and derivation table: door events read through `ColdReadService.accepted_on` (already so in `703807cf`), and the rule-2, rule-8 and declaration limits on `cold_depth.py`. C1q Q7 already covers the `foundation_on` adapter placement. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| A1Q-W5S-2 | C1 composition paragraph: the `main.py` mount in `703807cf` is the literal wiring; no change. |
| A1Q-W5S-3 | C4 guard and composition ownership: rule-8 blocks in `configuration-persistence.ps1` and the probe corpus in `writer_guard_probes.py`; both files are in the C4 list. |
| A1Q-W5S-4 | C4 `main.py` store and router wiring with the decision injections, reconciled with C1q `basis_on` through `cold_scenario_store.transaction()`. |
| A1Q-W5S-9/10/11 | HTTP-scan token sentences in C1 and C4; the DataTable/svg sentence in "Measured mock and content caps" (applies to C2, C3 and C5); shared guard-file serialization in the gate section. |
| A1Q-W5S-5..8 | W5-03 only; folded into `.agent/W5-03-build-spec.md`. |
| C1q2-Q13 (two declared probes, no selection) | C1 `foundation_on` `chamber_probe_asset_id` (topology SIGNAL edge from `COLD_ROOM`) and the Temperature sensing `asset_id` fallback order; assertions in `test_health_not_configured` and `test_health_rows`. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| RP3-C2 (7) | C2 readiness pass 3: Q-C2-1 routes file, Q-C2-2 context table, Q-C2-3 no-svg recovery table, Q-C2-4 currentness notice, frame/nav/guard literals, `V69Layout.tsx` description, refused capture 422. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| RP3-C3 (4) | C3 readiness pass 3: `coldSiteRoutes.tsx` `health`, currentness notice, unknown/refused capture producers, loading/unavailable copy. |
| RP3-C5 (3) | C5 readiness pass 3: currentness notices for all five states, refused/pending capture producers, loading/unavailable copy. |
| RP3-shared | "Capture producer method, loading and unavailable copy" section before C1. |
| CL2-1 (C3) | C3 condition notice literal. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| CL2-2/3 (C5) | C5 scenario row, page and client: DataTable columns and cells, pill source, expansion content, `coldScenariosClient` validator, breadcrumb and existing `SITE_SCREEN_DESCRIPTIONS.scenarios`. |
| CL3-C2 (Q-C2-5..7) | C2 build rulings: `coldRoutes.test.tsx` literal edit and file-list entry, Site-name heading (ledger corrected), empty-capture window. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
## Codex retrospective of Claude Architect rulings (2026-10-22)

Checked against `frontend/mockups/v69/index.html` (`cooling`, `cold-health`, `cold-scenarios`), `screen-manifest.json`, the selected-read code and the technical design. These rulings supersede conflicting Claude C2/C3 rendering instructions above; the evidence and claim limits remain binding.

| Ruling | Verdict and reason | Alternative / exact correction |
| --- | --- | --- |
| C2 Q-C2-2 `Match` to `Status` | **RESTORE TO MOCK.** The mock's `Context normalization` table has `Factor / Evidence / Match`. The heading can remain even when no match has been established; the cells carry the claim limit. | In C2 `frontend/src/sites/ColdCooling.tsx`, render the third `DataTable` heading as literal `Match`, replacing `Status`. With `comparison_state=CONTEXT_MISSING`, every Match cell reads `Not established`, regardless of that factor's `Observed` or `Unknown` evidence state; the Evidence column still reports the selected observation. Never render mock `Matched` without a supported comparator. Update `frontend/src/sites/__tests__/coldDepth.test.tsx::cooling_panels` to assert the heading, all five `Not established` cells and no unsupported `Matched`; recapture C2 limited/empty/pending/historical at 1440/390 and rerun the focused/navigation tests. No guard registration or C1 wire change is needed for this heading. |
| C2 Q-C2-3 Recovery curves to `DataTable` | **RESTORE TO MOCK**, subject to the selected-data limit. The mock gives this panel a chart; rule 5 constrains the module drawing `<svg>`, not whether a chart may exist. A table as the sole graphic loses the screen's visual structure. | Rebuild delta for C2 at `2812d7aa`: add `frontend/src/sites/coldDepthGraphics.tsx`, `frontend/src/ui/primitives.css` and `tools/checks/shell-overflow.ps1` to C2's Lane A file list. In rule 5 register `coldDepthGraphics.tsx` as the sole owner of its `<svg>`, require an actual `.cold-depth-graphic__scroll` wrapper in that module, and verify that selector declares horizontal overflow containment in `primitives.css`, as the existing assessment graphic check does; retain all existing allowlist checks. `ColdCooling.tsx` renders `Recovery curves` with the new graphic and the existing selected-point table as its accessible source detail. The present C1 `selected_points` have time and role but no temperature values: place their unconnected, labelled marks on categorical compressor/probe lanes, never on a numeric °C axis. Draw temperature curves only when a future selected read provides ordered accepted numeric recovery series. The current W2 producer therefore shows the chart frame and selected marks with `No accepted recovery sequence in this window.` and no mock 36/42-minute or +17% values; the no-point case has an empty frame. Keep `DataTable` for the evidence detail and `Context normalization`. Update `coldDepth.test.tsx::cooling_panels` to assert graphic, mark labels, empty state and no connecting path for the W2 fixture; update C2 `cooling-limited`, `cooling-empty`, `cooling-pending`, `cooling-historical` and 1440/390 captures and cap measurements. C3's registry `cooling:1` reason must describe selected marks and absent comparable curve, not a table-only panel. Re-run `tools/check-all.ps1` and the C2 focused/navigation tests before C2 re-review. |
| C3 condition notice | **KEEP — MOCK DEVIATION (D2).** The mock has condition cards and a table but no explicit condition ceiling; selected fault/start observations otherwise read as physical diagnoses. | A panel footnote would be closer in placement but less visible beside the S7 gateway panel. Keep the exact amber sentence in C3 and its test/capture. |

**Correctness disposition.** Confirm C1 Q1–Q13 and review-Low fixes: selected IDs, null recovery duration, public `cooling_response_state`, single effective Foundation and `foundation_on` adapter preserve the technical design's selected-evidence and snapshot boundaries. Confirm C2 Q-C2-1, Q-C2-4 through Q-C2-7, C3 state/fragment, C4 `basis_on`, C5 root-window/cutoff semantics and the A1Q guard/composition sweep. The chart correction above is the only C2 rebuild; do not synthesize a recovery curve from isolated points. The C2 currentness notice is a **KEEP — MOCK DEVIATION (D2)** for pending/stale/historical/unknown selection, because the mock has no live cutoff states; alternative is a small inline status note, but the visible amber notice is consistent with selected-read semantics. The same applies to C3 currentness. C5 authored scenario row and notice copy are **KEEP — MOCK DEVIATION (D4)** where no mock literal covers a selected pending state; replacing them with illustrative mock values would misstate stored authorship. No other W5-01 Claude ruling needs a code correction.

## C3 rulings (Q-C3-1..4)

These rulings amend `D-2026-10-22-w5-01-w5-03-buildspec` and supersede conflicting C3 composition and file-list wording above. Mock check: `frontend/mockups/v69/index.html` renders the `cold-health` branch with three `Backup generator` / `Cooling plant` / `Temperature sensing` cards and the single `Condition and evidence` panel (`Asset` / `Supported assessment` / `Next evidence`). `screen-manifest.json` gives `cold-health` the Site name as title and `Health` as section. The mock's separate `health` (mini-grid) screen has `Physical asset condition`, `Data sources · data quality, not equipment condition`, and a blue notice; those are not the cold screen's panel set.

1. **Q-C3-1 — extract only the S7 source panel.** Add `frontend/src/sites/SiteHealth.tsx` to C3's **Lane A** file list. Its exact export is `SiteHealthSources({ siteId, client, selectedGateway }: { siteId: string; client: HealthClient; selectedGateway: string | null })`. It calls the existing `client.getSourceHealth(siteId)` through `useRead` with the same `health:${siteId}` key and renders only the existing `Data sources · data quality, not equipment condition` `Panel`, with heading ID `site-health-sources-heading`, existing description, `SourcesBody` and `HealthGap` refusal (including the same `HEALTH_TEXTS` and exact references). On loading, keep that titled panel and show `Loading the site's gateway contact.` within it; a source refusal stays in that panel. Extract a private source-panel renderer receiving the read so `SiteHealth` can keep its current source and battery reads, loading behavior, strip, battery panel and blue notice unchanged on non-cold Sites. In `SiteHealthFrames.tsx`, route only COLDCHAIN to `ColdHealthDepth` followed immediately by this `SiteHealthSources` after the amber condition notice, inside the existing `HealthLinksContext.Provider`; pass the same `health` client and `gateway` search value. Do not mount `SiteHealth` for COLDCHAIN. The cold page therefore has **no** S7 battery `ConditionStrip`, `Physical asset condition` panel, or blue battery/gateway notice. It does retain the S7 source read's independent server-receipt clock and the exact `#site-health-sources-heading` target. Preserve existing non-cold S7 tests, and assert the cold panel order and absence of those three battery-specific elements in `siteHealthBoundary.test.tsx` or `coldHealthDepth.test.tsx`.

   **MOCK DEVIATION (D3) — added Data sources panel.** The cold mock ends after `Condition and evidence`; its Data sources panel belongs to `cold-evidence`, while mini-grid `health` has a separate source panel. The C3 contract retains S7 source health here to satisfy the live cold Foundation `Health › Data sources →` destination and keep gateway contact visibly separate from physical condition. A link to cold Evidence would preserve the cold Health panel set but would lead to a different selected-evidence read; rendering the entire S7 `SiteHealth` would add a battery strip/panel and blue battery notice with no cold condition basis. Keep the source panel alone as this explicit addition. The pre-existing amber condition notice and currentness notice remain the separately labelled C3 mock deviations in the retrospective.

2. **Q-C3-2 — heading.** Confirm the frame's `SitePageHeader` Site-name h1, matching the `cold-health` mock title `GreenHarvest Cold Room` (runtime: the selected Site's `display_name`). `Health` is the breadcrumb end and active Site tab, matching the manifest's section. The shared ledger's `heading Health` names the section, not an instruction to replace the Site-name h1. No `Health` h1 is added.

3. **Q-C3-3 — live Health route assertion.** Add `frontend/src/sites/__tests__/coldDepth.test.tsx` to C3's **Lane A** list. In `cooling_nav_and_routes`, replace the old test name with `coldUiHref maps the cooling and Health API links with their exact queries`, and replace its last assertion literally with:

   ```tsx
   expect(coldUiHref(`/api/sites/${SITE_CODE}/cold/health?${Q}`, routes)).toBe(`/sites/${SITE_CODE}/health?${Q}`);
   ```

   Keep the existing Cooling assertions and their query-preservation check.

4. **Q-C3-4 — cold Foundation link assertion.** Add `frontend/src/sites/__tests__/coldFoundation.test.tsx` to C3's **Lane A** list. Its existing `renderCold` fixture actually renders the gateway panel; add this literal test inside the existing cold Foundation route suite:

   ```tsx
   it("links the cold gateway panel to Health Data sources", async () => {
     renderCold(`${BASE}/readiness`, loaded(STOCKED));
     await settledScreen();
     const link = Array.from(panelTitled("Gateway status · edge-cold-001").querySelectorAll("a"))
       .find((a) => a.textContent === "Health › Data sources →");
     expect(link?.getAttribute("href")).toBe("/sites/COLD-001/health#site-health-sources-heading");
   });
   ```

   This checks the actual readiness link and existing source heading ID. `coldSiteViews.test.tsx` remains on C3's list for its own route and composition assertions.

## C3 rulings (Q-C3-5, mock differences)

These rulings amend `D-2026-10-22-w5-01-w5-03-buildspec` and supersede conflicting C3 mobile Asset-cell and card wording. Mock check: `frontend/mockups/v69/index.html`, `cold-health`, shows compact `GEN-CR-01` and `CMP-003` Asset cells in `Condition and evidence`, not four-line UUIDs. Its Backup generator card has an amber top border, a body-colour value and a separate `View detail →` link. Mock CSS `.assessment .metric-value` sets the value to 17 px at 1440 and 390.

1. **Q-C3-5 — RESTORE TO MOCK.** Keep the condition-panel cap at **330/430 px (1440/390)**. Add `frontend/src/ui/primitives.css` to C3's Lane A file list. In `frontend/src/sites/ColdHealthDepth.tsx`, set `className="cold-health-condition"` on the `Condition and evidence` `Panel`. Keep `DataTable` and the complete selected Foundation Asset label and source-reference UUID. Put the UUID on its own line without truncation. Add this scoped CSS to `primitives.css`:

   ```css
   @media (max-width: 480px) {
     .cold-health-condition .data-table { min-width: 840px; }
     .cold-health-condition .data-table th:first-child { position: sticky; left: 0; z-index: 1; min-width: 240px; background: var(--surface-raised); }
     .cold-health-condition .data-table thead th:first-child { z-index: 2; background: var(--surface-sunken); }
     .cold-health-condition [data-health-asset-id] { display: block; white-space: nowrap; overflow-wrap: normal; word-break: normal; font-size: 10px; }
   }
   ```

   The existing `.data-table__scroll` owns horizontal overflow; the Asset column stays visible while the other columns scroll. This replaces the earlier instruction to break Asset UUIDs at character boundaries. Raising the cap to fit four-line UUIDs would retain the mock difference. Recheck all five 390 captures, including the three-row unknown case, against **≤430 px**, with no document overflow or clipped ID; retain the 1440 **≤330 px** cap. Assert the panel class and complete ID in `frontend/src/sites/__tests__/coldHealthDepth.test.tsx`.

2. **Backup border and value — RESTORE TO MOCK.** In `ColdHealthDepth.tsx`, replace the card's `word` prop with `assessment`, keeping `tone={row.condition_state === "NEEDS_INVESTIGATION" ? "amber" : undefined}`. The existing `.v69-metric--assessment.v69-metric--amber` gives the Backup card a 3 px amber top border, and `.v69-metric--assessment .v69-metric__value` keeps its value body-coloured. Apply `assessment` to all three cards so the neutral cards have the mock's neutral assessment border.

3. **Card link — RESTORE TO MOCK.** The `cold-health` mock has a plain card label and a separate `View detail →` link below the note. Add `frontend/src/ui/V69Layout.tsx` and `frontend/src/ui/primitives.css` to C3's Lane A file list. Extend `MetricCardProps` with optional `link?: ReactNode`; render it after the note as `<div className="v69-metric__link">{link}</div>` when provided. Add `.v69-metric__link { font-size: 10px; margin-top: 10px; }` to `primitives.css`. In `ColdHealthDepth.tsx` pass `label={row.label}` and `link={href === null ? undefined : <Link to={href}>View detail →</Link>}`. A null destination has no link. Keep `coldUiHref` query preservation and assert the label is not an anchor while the detail link has the mapped destination.

4. **Value size — RESTORE TO MOCK.** The mock's assessment state word is **17 px**; a 24/27 px value would depart from the actual `.assessment .metric-value` rule. The `assessment` prop above implies the shared 17 px word rule. Remove standalone `word`, do not enlarge the state words, and assert all three cards use `v69-metric--assessment` without a C3 size override.

5. **Registry reasons — literal Architect copy.** In `frontend/docs/architecture/v69-dependency-registry-pilot.json`, the exact `reason` for `(cooling,1) Recovery curves` is `Selected compressor and probe observations are drawn as unconnected marks on categorical lanes; no ordered accepted recovery series exists, so no comparable recovery curve is drawn.` The exact `reason` for `(cooling,2) Context normalization` is `Ambient is not selected by the W2 cooling assessment and loading and defrost roles are absent; with no supported comparator every Match cell reads Not established.` The builder's current strings match these literals; retain them verbatim. Neither reason claims a physical condition or a measured comparison.

