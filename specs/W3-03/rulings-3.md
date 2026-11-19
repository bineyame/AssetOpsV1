## Run-1b rulings (r1b)

These rulings read Lane A `06acf1cf`, Lane B `f3f04ef6`, the five 1b handoff readings and the v69 `portfolio` mock. They assign remaining work; they do not claim the unfinished 1b or page tests passed. This section prevails over a conflicting earlier illustrative wire or mock sentence.

### Q-1b-1 — authenticated Portfolio cursor

**Confirm r1a2 item 4 with this literal seam.** Lane A, in a **pre-1b seam run on the released W3-03 branch**, owns `backend/assetops_backend/estate/scope.py` and the shared `_cursor` call in `estate/index.py`; Lane B resumes run 1b only after that handoff and its independent cursor review. `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` is the sole key source: exactly 64 ASCII hexadecimal characters decoding to 32 bytes, supplied by the host environment. There is no committed, development or test default. Tests set a fixed test-only value with `monkeypatch`; a local server must be given a separately generated key. Never echo the key or include it in a cursor, response or log.

Add `scope.py::portfolio_cursor_key()` (validates and returns bytes or raises `EstateRefusal("ESTATE_STORE_UNAVAILABLE")`), `encode_portfolio_cursor(payload, key)` and `decode_portfolio_cursor(value, key)`. The latter two reuse the existing v1 Portfolio payload shape, adding only `mac`: lowercase 64-character HMAC-SHA-256 hex of `json.dumps(payload_without_mac, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")`; encode the resulting object with the existing URL-safe base64 convention. Decode base64/JSON, require the exact Portfolio key set plus `mac`, verify the MAC with `hmac.compare_digest` **before** trusting or using `page_one_mode`, `known_at`, IDs, marker or other payload fields, then perform the existing shape checks. A missing, malformed or wrong MAC is 422 `INVALID_CURSOR`; a valid MAC whose grant, lens, window or selection differs is 409 `ESTATE_BASIS_CHANGED`. The key is checked for every Portfolio request before its selection read, including page one and an empty scope; missing/malformed configuration is 503 `ESTATE_STORE_UNAVAILABLE`, body `{"detail":{"code":"ESTATE_STORE_UNAVAILABLE","message":"Estate records could not be read.","rows":null,"total_count":null,"value_cards":null,"objectives":null,"money":null}}`. Authentication and authorized-scope admission still precede value parsing and this key check. The key is a deployment setting, not a database migration or a new response field.

`index.py::_scope` uses authenticated Portfolio decode before the selection read; `index.py::_cursor` uses authenticated Portfolio encode only when `req.kind == "portfolio"`. Findings, Actions, Evidence and Financials continue through the old `encode_cursor`/`decode_cursor`, with unchanged bytes. A MAC alone does not replace `_fence` or `resume_after`. Lane A adds `backend/tests/test_w303_estate_cursor.py::test_portfolio_signed_round_trip_and_tamper`, `::test_portfolio_signing_key_missing_or_malformed`, and unchanged W3-01/02 cursor-byte assertions; Lane B extends `test_w303_portfolio_api.py::test_cursor_lens_window_cutoff_and_v1_token` to cover signed live/historical page two, a valid-MAC changed grant/selection 409, and a missing-key 503 with the exact body. This closes the `page_one_mode` flip without changing `estate-selection/2`.

### Q-1b-2 — complete workflow-label precedence

**Confirm strict first-match precedence and `Applied` for APPLIED with a non-VERIFIED terminal outcome.** The final S7 row means an Action with no earlier match **and** no PENDING/APPLIED application state; it does not override a selected application fact. The full table is:

| Selected exact-origin Action/verification fact, first match wins | `workflow_label` |
| --- | --- |
| No joined Action | `Recommendation not accepted` |
| Surviving `resolution_state=RESOLVED` and `verification_outcome=VERIFIED`, regardless of application state | `Verified` |
| `resolution_state=RESOLUTION_WITHDRAWN`, regardless of application state/outcome | `Resolution withdrawn` |
| Selected frozen plan active at cutoff, `_verification_window=true`, and no surviving terminal outcome | `Outcome pending` |
| `application_state=PENDING`, including a non-VERIFIED terminal outcome not matched above | `Pending` |
| `application_state=APPLIED`, including `RESOLVED` with non-VERIFIED terminal outcome | `Applied` |
| Joined Action with `NONE_AT_CUTOFF` or another state matching none of the above | `No action yet` |

`f3f04ef6`'s `portfolio.py::workflow_label` implements that ordering. Lane B extends `backend/tests/test_w303_portfolio_workflow_labels.py::test_all_seven_literal_labels_and_precedence` with APPLIED/RESOLVED/non-VERIFIED = `Applied`, PENDING/non-VERIFIED = `Pending`, and an active-plan/null-outcome case; the exact-origin tie test still must assert **both** Actions in unpaged `progress.rows`. The page renders the server string verbatim. An application label reports application only; it does not count as a verified resolution or recovered value.

### Q-1b-3 — line-less pending money guard

**Add the private guard fact; the line-only rule is insufficient.** Lane A owns `backend/assetops_backend/estate/financials.py` in the same pre-1b seam run. `windowed_lines` returns a fourth value `pending_guard: bool`, true if any selected cold pinned window has `cold_money(...)["withheld"]` or any selected EV pinned window has `guard == ERROR_PENDING`, whether or not that window emits a consequence line. It is false for an EV `STALE_BASIS` guard, a missing pin, a merely uncovered window or an ordinary UNPRICED head. `select_financial_scope` puts private `_pending_guard` on each per-Site coverage dict, false for mini-grid and non-applicable Sites; the public Financials DTO, group/exclusion bytes and selection token are unchanged. Lane B changes `portfolio.py::money_pending` to use `_pending_guard` (and keep selected PENDING-line evidence as a consistency assertion, not a prerequisite). The flag affects overall status after EMPTY_SCOPE/HISTORICAL, while `_windows_covered=false` still makes that Site's M unit U. It does not create a line or amount.

Lane A adds `backend/tests/test_w303_selectors_postgres.py::test_financial_scope_pending_guard_without_line` for cold withheld/zero consequences and EV `ERROR_PENDING`/no history, with stale and no-pin controls and unchanged W3-02 public golden bytes. Lane B extends `backend/tests/test_w303_portfolio_reduction.py::test_money_table` and `backend/tests/test_w303_portfolio_scope_snapshot_postgres.py::test_late_revision_pending_historical_and_mixed_source`: a line-less guard beside covered Sites yields `status=PENDING`, M `PARTIAL`, null current amount for the affected category, and no invented exclusion row. The page uses `Updating selected Sites`; it may disclose `Pending money reassessment; no selected consequence line` from the private guard, never a fabricated W3-02 line reason.

### Five 1b readings and remaining dry-read

1. **Confirm reading 1.** `job_state != NONE` is the existing selector's selected-head witness for `HISTORICAL`, provided match is settled and source is not STALE. `PENDING|FAILED` job markers do not unset that selected-as-of basis. Keep `test_settled_current_and_historical_bases` and its persisted before-head control; historical money remains withheld from current display.
2. **Replace reading 2.** A selected `PENDING` line is sufficient evidence of a pending guard but is not necessary. `_pending_guard` above is authoritative for selected cold/EV windows with zero lines. `_windows_covered=false` alone is UNKNOWN, not PENDING. Use the named line-less tests.
3. **Confirm reading 3 with its terminal guard.** `_verification_window=true` means a selected active frozen plan without a surviving terminal outcome; only that fact reaches `Outcome pending`. A null outcome alone never does. Keep the active-plan/null-outcome and null-outcome/no-plan controls in `test_all_seven_literal_labels_and_precedence`.
4. **Confirm reading 4.** APPLIED plus a non-VERIFIED terminal outcome is `Applied` by first match; PENDING plus such an outcome is `Pending`. The full table and test above close the apparent overlap.
5. **Confirm reading 5.** `test_builder_uses_one_connection_scoped_reader_and_refuses_missing_database` exercises the actual `composition.py` builder against a migrated run-owned DB with an unknown tenant, observes one `EvidenceMoneySnapshot` passed to all four selectors, and checks 503/no database. It does not substitute for the persisted four-Site projection tests.

**Cards and IDs (run 1b).** Keep all six full-scope selector returns before Finding membership and paging: `a_sites/a_rows`, `e_sites/e_rows`, and `m_sites/m_lines/applicable/groups/exclusions/diagnostics`. `selected_lines` is the exact unpaged W3-02 public line DTO order. `money` is `{groups,exclusions,diagnostics,estate_total:null}`; a zero-head `NO_LINES|UNKNOWN_COVERAGE` sentinel is a group, not a selected line. `scope_disclosure.sites` and `selected_revision_ids` use the already specified token-array union; null provenance says `No selected source basis`. The five cards stay in the closure-2 order and states, with operating cost drawn **only** from `CANDIDATE_OPERATING_COST_EXPOSURE`. The clean fixture gives `SITE_OWNED/UNKNOWN/UNSUPPORTED/UNSUPPORTED/NOT_ESTABLISHED`; a covered Site-owned W1 line is still displayable when an unrelated cold/EV category is pending, while a pending/incomplete operating-cost category is `WITHHELD`. Risk remains `Not assessed` until a reviewed RISK producer exists. The unsupported cards never inherit mock kW, battery counts or dollars. Test `test_operating_cost_first_match_wins_across_partitions`, `test_ineligible_overlap_and_unknown_coverage_decline_total`, `test_ev_window_money_has_no_finding_attribution`, and `test_page_size_does_not_change_cards_matrix_or_money` at limits 1 and 100; compare exact line keys, group keys, IDs and full-scope projections, not displayed page-row sums.

**Matrix and prompt (run 1b).** Emit one `objectives` item per authorized Site, including the unselected EV Site, with fixed rows `SERVICE_PRODUCT`, `BACKUP`, `ASSET_CONDITION`, `COST_CONTROL`, `EVIDENCE`. The first three are `UNKNOWN` absent an exact reviewed objective assessment; no domain implies `N/A`. `COST_CONTROL=NOT_APPLICABLE` for configured cold/EV domains under `financials.py::APPLICABLE`, `REVIEW` for an eligible mini-grid operating-cost line, `UNASSESSED` for complete mini-grid money coverage and no line, else `UNKNOWN`. Evidence takes the per-Site W3-02 readiness reduction; a historical current-objective display is `UNKNOWN`. The prompt selects the first canonical typed gap with a nonnull `next_step` and the lexically first eligible Site ID in that gap; null-step gaps are skipped. Its three literal texts remain `{next_step} at {site_name} to address the selected evidence gap.`, `No selected decision-changing evidence step`, `Evidence coverage incomplete`. CTA `/evidence`; no guessed Site route. Add assertions to `test_evidence_prompt_null_steps_and_coverage_precedence` and `test_page_size_does_not_change_cards_matrix_or_money` for IDs, all five cells and null-step/incomplete precedence.

**Progress and B4 (run 1b).** `progress.rows` contains every full-scope selected Action, including a second Action on the same exact origin and an Action whose origin revision is no longer the selected Finding revision; only the row cell uses the deterministic latest-event tie. The nine closure-2 fields take `selected_action_event_id` from W3-01, plan/outcome IDs from `_raw._plans/_outcome_id`, and `recorded_at` from `_selected_recorded_at`; absent IDs are null. `accepted_action_count`, `pending_trial_count` and `verified_resolution_count` follow the complete applicable Action/verification coverage rule; `completed_activity_count` and `recovered_value` remain null. In `test_selected_action_window_workflow_and_withdrawal`, use **one** selected `[2026-11-01,2026-11-03)` request and successive cutoffs: producer-created Action and frozen plan -> `Outcome pending`, evaluator-created VERIFIED resolution -> `Verified`, later accepted evidence plus evaluator-created `RESOLUTION_WITHDRAWN` -> `Resolution withdrawn`. At each cutoff compare selected Action/event/plan/outcome IDs and times with the Action root and stored selected records. Never hand-append a resolution. The 10-06 aligned fixture has no selected Action and says `No selected Actions in this window` / `Recommendation not accepted`; the November test makes no Finding-row label assertion unless that exact origin Finding **revision** is selected in its request window. This is the B4 proof boundary.

**Run 2 page literals and links.** Lane A adds `PORTFOLIO_SCHEMA="estate-portfolio-1"`, a typed `EstatePortfolioBody`/`EstatePortfolioQuery` and `EstateClient.portfolio()` to shared `estateClient.ts` after reviewed 1b; no `state` query key or widened root union. Lane B's page fetches 50, appends only Findings on `Load more Findings`, and clears previous privileged content on 401, 409 and 503. The shared date bar says `Window {from} to {last included} (UTC days)` / `Evidence cutoff`; context uses closure-2 Q19, never `Needs attention` or `simulated`; chips are `All findings`, `Cost`, `Risks`, `Opportunities`, with `{total_count} selected Findings` and ` · coverage incomplete` when applicable. Finding cells use `Mechanism not recorded`, `Basis not recorded`, `Episode window not recorded`, `Not assessed`, `No reviewed confidence measure`, `Next move not recorded`, `No accepted Action`, and the server `workflow_label` as specified; a cold/EV Finding link is inert `Finding detail unavailable`. Matrix shows the five labels and `Site detail unavailable` for a null target. Evidence aside uses the three prompt texts above. Opportunity slots say `No reviewed scenario` and `No eligible headroom or demand basis`; both CTAs are inert `Not available yet`. Change lines say `Completed activity · Not established`, `Policy trial awaiting outcome · {count or Unknown}`, `Verified resolutions · {count or Unknown}`; disclosure says `No previous comparable Portfolio snapshot is selected; change deltas and recovered-value trends are withheld.` Footer uses the first eligible EV `GROSS_TARIFF_SCENARIO` line or `Cross-Site energy and tariff totals are not established.` with `Energy basis unavailable`; no EV line attaches to a Finding. Root links preserve accepted `from,to,known_at` and clear cursor; a Site/detail route lacking the full tuple is labelled `Opens current Site view`. Use the run-2 typed/status, destination, lens, refusal and page-size tests already named in closure 2 and r1a; run-3 captures prove the 1440/390 rectangles. No example IDs or mock amounts enter the page.

## Run-1b reading rulings (r1b2)

These rulings inspect `f5407e95`, `3a0d96bc`, and `6c4e0449`. Named existing tests are evidence for the stated narrow behavior; named additions below are required proof, not claims of a passing run. This section supersedes conflicting run-1b readings above.

| Reading | Ruling, literal, and test |
| --- | --- |
| R1 | **Replace the placement claim.** `portfolio_cursor_key()` is first in `index.py::_scope`, before `snap.read_at` and `snap.imported_sites`, but `PostgresEstateRead.read` has already executed `SET TRANSACTION READ ONLY` and `SELECT now()` to make the snapshot. Thus it is **not** before every DB read. Move the Portfolio key check to the authenticated, parsed API boundary before `store.read`; keep the snapshot check or pass the validated key into it. Missing/malformed key on a well-formed request remains 503 `ESTATE_STORE_UNAVAILABLE` with the frozen null-field body. Extend `test_cursor_lens_window_cutoff_and_v1_token` with an instrumented store/connection asserting zero DB reads for missing/malformed key on page one, page two and empty scope. The existing test proves 503/body only, not zero reads. |
| R2 | **Confirm with a precise boundary.** `parse_request` calls `_portfolio_envelope(cursor)` before the API can check the key or open the snapshot. Invalid base64/JSON, missing or extra keys, and malformed `mac` therefore return 422 `INVALID_CURSOR` even when the key is absent. A structurally valid envelope with a bad MAC needs the key and returns 503 when the key is absent; with a valid key it returns 422. Keep envelope parsing before the new R1 key check, then MAC/shape verification in the snapshot. Add an API test combining an absent key with a malformed envelope (422, zero reads) and with a well-shaped wrong-MAC envelope (503, zero reads); retain `test_portfolio_signed_round_trip_and_tamper` for valid-key 422. |
| R3 | **Confirm the proof limit.** `test_financial_scope_pending_guard_without_line` uses `_GuardSnap`, a fake snapshot, to drive the real `windowed_lines` and `select_financial_scope`; it is not a persisted producer test. It asserts cold `withheld` and EV `ERROR_PENDING` with `lines == []` set `_pending_guard=True`, and stale/no-pin controls set it false. Keep the planned persisted `test_late_revision_pending_historical_and_mixed_source` line-less cold/EV variant: `status=PENDING`, affected M unit U (M `PARTIAL` beside a covered Site), no invented selected line/exclusion, and no current affected-category amount. |
| R4 | **Confirm.** `money_pending` returns true for `_pending_guard` **or** an uncovered selected line whose `eligibility == "PENDING"`; the line remains sufficient when the guard is false. `test_money_table` already asserts `money_pending(uncovered, guarded)` and guard-only `money_pending(guard_only, [])`. Add the false-guard plus PENDING-line case to the persisted late-revision test, alongside the line-less case; the page status is `Updating selected Sites` in either case. |
| R5 | **Confirm the nullable display slots.** `operating_cost_card` returns `COMPARABLE_GROUP` or `SITE_OWNED` with `display_value:null` and `basis:null`; run 2 formats bounded money from the exact selected group/line using W3-02 formatting. `UNPRICED` may carry the literal `{site_name} · consequence recorded without a price`; `VERIFIED_RECOVERY.destination` is `/financials`. `test_page_size_does_not_change_cards_matrix_or_money` checks the SITE_OWNED null slot and line/group keys; `test_operating_cost_first_match_wins_across_partitions` must check both priced states, and `rendersContextFiveCardsPulseAndSelectedRows` must check the formatted value and UNPRICED copy. |
| R6 | **Confirm.** `value_cards` emits `SERVICE_PRODUCT_RISK` as `UNKNOWN` / `Not assessed` on every W3-03 selection because no reviewed RISK producer exists; no COUNT path is authorized. `test_full_scope_projections_ignore_page_size_and_empty_scope` checks `UNKNOWN`; run-2 `rendersContextFiveCardsPulseAndSelectedRows` must check `Not assessed`, including an empty Risks lens. |
| R7 | **Confirm with a route limit.** `objective` returns one item per authorized Site with `site_name`, stored `site_type` in `domain`, fixed five-cell order and null Site-cell destinations while no reviewed Site route accepts this selection. Unknown configuration remains `UNKNOWN`, never N/A. `test_page_size_does_not_change_cards_matrix_or_money` checks the persisted item/cell count and domain states; extend it for exact null destinations and unknown configuration, and cover `Site detail unavailable` in `rendersFiveObjectiveRowsForEveryAuthorizedSite`. |
| R8 | **Confirm.** `evidence_cell_state` returns `UNKNOWN` for a historical display or `evidence_unit == U` (including no rows and `CONTRADICTORY`), else `FULL` if all rows FULL, `NONE` if any NONE, otherwise `LIMITED`. `test_full_scope_projections_ignore_page_size_and_empty_scope` covers FULL and historical UNKNOWN; extend `test_evidence_prompt_null_steps_and_coverage_precedence` with FULL/NONE/LIMITED/CONTRADICTORY and no-row vectors, then assert the selected Site labels in `rendersFiveObjectiveRowsForEveryAuthorizedSite`. |
| R9 | **Confirm the extra `site_code` wire field.** `evidence_prompt` emits `site_code:string|null` beside `site_id`; its available text is exactly `{next_step} at {site_name} to address the selected evidence gap.` The incomplete and no-gap texts remain the r1b literals. `test_evidence_prompt_null_steps_and_coverage_precedence_pure` covers null-step skipping, chosen ID/code and incomplete precedence; `rendersTypedEvidencePromptAndExactDestinations` must type and render the code without inventing a Site link. |
| R10 | **Replace the nine-field progress wire.** The page cannot infer an Action's origin revision from the nine `progress.rows[]` fields, and paged/lens-filtered Finding rows cannot prove absence. Add required `progress.rows[].origin_revision_selected: boolean`, computed on the server from the full selected Finding `(finding_id,finding_revision_id)` set before lifecycle/lens/page filtering; `false` means that exact origin pair is absent from the selected Finding revisions at this request window/cutoff. This is a disclosure fact, not an Action eligibility or verification state. Keep `verification_plan_id` as active-at-cutoff plan else latest selected recorded plan, and `verification_outcome_id` from `_raw._outcome_id`; counts still use complete applicable Action coverage and `_verification_window`/`_verified_recent`. Extend `test_two_actions_one_exact_origin_latest_event_then_id_tie` and persisted `test_selected_action_window_workflow_and_withdrawal` for both boolean values and exact IDs/times; run-2 `rendersChangeDisclosureWithoutRecoveredMoney` must show `Origin Finding revision not selected` only when false, including page size 1 and a nonmatching lens. Update the run-2 client type to ten required progress-row fields. |
| R11 | **Replace the per-Site query.** `scope_disclosure` currently calls `snap.cited_provenance(...)` once per Site with selected IDs. Sharing the connection prevents inconsistent snapshots but still creates an additional N+1 query; this is not acceptable for an estate-wide root. Add a connection-taking batched provenance read for all represented Sites, keyed by `(tenant_id,site_id)` and each Site's exact sorted selected/cited IDs; produce the same six-key W3-01 DTO per Site and null with `No selected source basis` when a Site has no selected ID. Preserve mixed-source classification and digest semantics. Extend `test_page_size_does_not_change_cards_matrix_or_money` to compare each Site DTO with the existing single-Site truth, and instrument a multi-Site read to prove the additional provenance query count is constant at limits 1 and 100 (no one-query-per-Site loop). |
| R12 | **Confirm the exact-value rule; tighten the route guard.** Footer eligibility requires `quantity.low == high`, `amount.low == high`, `eligibility == "ELIGIBLE"`, EV gross tariff category, and a non-current-view **nonnull reviewed** `links.evidence` target. `footer` currently checks `current_view_label is None` but not that `links.evidence` exists; require both before selecting the first `(site_code_key,site_id,line_key)`. The page derives `Other Sites may lack comparable full-window coverage.` only from another applicable EV Site with UNKNOWN/PENDING/STALE coverage; otherwise `Categories and windows remain separate.` `test_ev_footer_first_eligible_and_coverage_warning` must include a null-route eligible line and another EV Site with incomplete coverage; `rendersEvFooterAndMissingEnergyBasis` checks the fallback and the exact two warning sentences. |
| R13 | **Confirm.** `evidence_gap_site_count` is the count of distinct `site_ids` across **all** typed `evidence_gap_groups`, including groups with `next_step:null`; only the prompt skips null-step groups. It is null when Evidence coverage is incomplete. Extend `test_full_scope_projections_ignore_page_size_and_empty_scope` with a null-step-only Site and assert the summary count remains 1 while the prompt is `NO_GAP`; verify the incomplete case yields a null count in `test_late_revision_pending_historical_and_mixed_source`. |

**Build impact.** R3, R4, R5–R9 and R13 retain the run-1b contract but add the named proof. R10, R11 and R12 change run 3b: add the progress boolean, batch scope provenance and require a real footer destination before its persisted comparison tests close. R1 and R2 require the Lane A cursor seam fix and refusal-order tests before run-1b review. Run 2 must type/render R10, use the R12 footer warning predicate, and preserve the R2 refusal order; it must not work out origin selection from the paged Finding table. No other root wire or migration changes are authorized.

## Run-1b variant rulings (r1b3)

These rulings supersede the persisted-proof demands for the six combinations below. They do not turn a pure or fake-snapshot result into a persisted producer claim. Keep the actual persisted controls and their observed states in the run-1b handoff; do not seed fabricated product rows or force an impossible state through a DTO patch.

| Pending item | One ruling and sufficient proof |
| --- | --- |
| P-1b-1, late cold | **Pure-test ruling.** `backend/tests/test_w303_portfolio_reduction.py::test_money_table` proves that an uncovered cold money unit with a selected `PENDING` line reduces to U and makes `money_pending` true; it also proves that `_pending_guard` alone makes a line-less cold unit pending. This is sufficient for Portfolio's reduction and status rule. The persisted `test_late_revision_pending_historical_and_mixed_source[a_lineless_cold]` separately proves the real cold line-less pending path. `fx.cold.advance_late()` after the drained excursion selects a settled cold head, so do not call it a persisted later-record/unsettled-job proof or require the unproduced `PENDING_RECOMPUTE` Site state. |
| P-1b-2, non-stale mini-grid historical marker | **Pure-test ruling.** `backend/tests/test_w303_portfolio_reduction.py::test_settled_current_and_historical_bases` supplies an as-of `HISTORICAL` head with `source_freshness=RECENT`, a settled match and a `PENDING` or `FAILED` job marker, and checks that it stays covered; its stale, missing-head and current-state controls reject coverage. This is sufficient to isolate the selected-as-of marker rule. The persisted `mg_historical_marker` control remains STALE and UNKNOWN; do not describe it as a positive covered marker. |
| P-1b-3, overlapping basis | **Pure-test ruling.** `backend/tests/test_w302_money_api.py::test_w302_money_overlap_by_group_ids_and_citations` drives the real W3-02 comparator with shared group, technical and cited IDs, asserts `OVERLAPPING_BASIS`, null group amount and exclusions, and checks disjoint and unproven controls. Portfolio reuses those full-scope groups unchanged, so this is sufficient for the overlap decline. `test_ineligible_overlap_and_unknown_coverage_decline_total` remains persisted proof of the INELIGIBLE, COMPARABLE and UNKNOWN_COVERAGE states only; it must not claim a persisted overlap. |
| P-1b-4, persisted EV pending | **Fake-snapshot ruling.** `backend/tests/test_w303_selectors_postgres.py::test_financial_scope_pending_guard_without_line` drives the real `windowed_lines` and `select_financial_scope` functions through `_GuardSnap`: an EV `ERROR_PENDING` pin with no stored history yields `_pending_guard=true`, no invented line, and an uncovered money window; stale/no-pin controls keep the guard false. `backend/tests/test_w303_portfolio_reduction.py::test_money_table` proves that this guard makes the unit U and raises the pending signal beside covered units. These tests are sufficient for the EV guard-to-Portfolio rule without claiming an EV persisted pending head. |
| P-1b-5, false guard plus pending line | **Pure-test ruling.** `backend/tests/test_w303_portfolio_reduction.py::test_money_table` passes an uncovered Site and a selected `eligibility=PENDING` line to `money_pending`, which is true even with `_pending_guard` absent (the same false value under `.get`); the covered-window and nonpending-line controls are false. This is sufficient to prove R4's independent line branch. No reviewed cold/EV producer emits a PENDING line while its corresponding guard is false, so remove the r1b2 demand for that persisted combination. |
| P-1b-6, selected Action origin revision true | **Pure-test ruling.** `backend/tests/test_w303_portfolio_workflow_labels.py::test_two_actions_one_exact_origin_latest_event_then_id_tie` passes the full selected Finding pair set to `progress` and asserts both `origin_revision_selected=true` for exact pairs and false for a different revision or empty set, independent of page order. This is sufficient for the server's equality/disclosure rule. `test_selected_action_window_workflow_and_withdrawal` retains its persisted false result and exact selected-ID checks; the B4 chain does not select its November Action and October origin revision in one assessed request window. |

R1/R2 in Lane A's cursor area being applied in Lane B commit `271577c6` is acceptable: one builder applied the changes sequentially before run-1b review. Review the combined diff and the R1/R2 refusal-order tests against the specified API boundary; the lane label does not require reverting or splitting that commit.

## Run-1b review rulings (r1b4)

**L1 — ratified file edits.** Ratify Lane B's sequential `271577c6` R11 edits to `backend/assetops_backend/estate/adapters/postgres_estate_read.py`, `backend/assetops_backend/estate/composition.py` (including `build_estate_read` and `build_estate_evidence_service`), `backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py`, `backend/assetops_backend/evidence/composition.py`, and the matching fixture wiring in `backend/tests/test_w302_evidence_scope_snapshot_postgres.py`. They supply the connection-taking, batched provenance seam required by R11 and preserve the existing W3-01/02 public DTOs. This is a specific ownership exception for those reviewed hunks in run 1b, not a transfer of Lane A's integration ownership or a general license to edit shared files. No file move, reversion, commit split, or Lane A re-sign is required. Lane A still owns its run-2/3 integration and reviews the combined seam when mounting Portfolio.

**L3 — single prompt-Site rule.** Supersede the lexical Site UUID wording in closure 1 Q16 and the run-1b “Matrix and prompt” paragraph. Literal rule: if Evidence coverage is incomplete, emit `COVERAGE_INCOMPLETE` with null Site/code. Otherwise scan W3-02 typed gap groups in their canonical order, skip every group with `next_step:null`, and take the first remaining group with an authorized Site whose stored code is available. Within that group, choose the first such Site in `(site_code_key,site_id)` order; emit that Site's exact `site_id` and `site_code`, the group's `gap_code`, and `{next_step} at {site_name} to address the selected evidence gap.` If none qualifies, emit `NO_GAP` with null Site/code. The destination remains `/evidence`. Test `test_evidence_prompt_null_steps_and_coverage_precedence_pure` with two eligible Sites whose code order is opposite their UUID order, a null-step earlier group, and incomplete/no-gap controls; assert the chosen ID, code, gap and literal text. In the run-2 `rendersTypedEvidencePromptAndExactDestinations`, assert that the page renders the server-selected Site/code and destination without re-sorting or choosing from paged Findings. The current run-1b code follows this rule; L3 requires no 1b code change and only constrains run 2's page rendering.

## Run-2 rulings (r2)

Authority for this appendix is the run-2 handoff at `04474b3c` on `task/W3-03-portfolio-composition`, P-2-1, and the unchanged missing-claim guard. This is a run-3 instruction, not a claim that run 3 or final review has passed. The run-2 capture DB was private `w303m_test` and was dropped.

### P-2-1 — register the opportunity gap; keep the guard

Use **one** open gap for the two unavailable destinations. Add this exact object to `frontend/docs/architecture/v69-dependency-registry-pilot.json` `mock_gaps.gaps` (and keep `portfolio` out of `gap_enrolled_screens`, which would impose unrelated whole-screen enrollment). The two element IDs name distinct slots in the existing third Portfolio panel; neither claims a real Finding or physical headroom. Add `"G-portfolio-opportunity"` to the `portfolio` screen ledger's `gap_ids` if that ledger supplies `gap_ids`, as the registry validator requires exact membership.

```json
{"id":"G-portfolio-opportunity","screen_ids":["portfolio"],"panel_portion_ids":[],"element_ids":["portfolio:3.review-opportunity-finding","portfolio:3.inspect-physical-headroom"],"claim":"A supported opportunity Finding destination and a reviewed physical-headroom destination for the selected Portfolio opportunity.","boundary":{"window":"The selected Portfolio window and evidence cutoff.","subject":"An opportunity on an authorized Site, with its exact Finding revision and physical-headroom basis.","source":"Absent in W3-03: no reviewed OPPORTUNITY Finding producer or eligible physical-headroom/demand assessment is selected; W4 opportunity and mini-depth reads are outside this composition.","cannot_mean":"Not zero opportunity, zero headroom, an accepted scenario, or an available Finding or headroom route."},"missing_kind":"contract","status":"open","target_wave":"unplanned","allocation":"pending owner review","requires":["A-estate-comparability","I-mini-depth-read"],"source_status":"absent","ui_placements":["portfolio.opportunity.review-finding","portfolio.opportunity.inspect-headroom"],"unplaced_reason":null,"owner_or_role":"Owner (allocation); Architect (opportunity Finding and physical-headroom contract)","evidence":{"source":null,"ui":"frontend/src/estate/EstatePortfolio.tsx OpportunityPanel","visual":null,"reviewed_by":null},"review_trigger":"Reviewed opportunity Finding and physical-headroom reads supply exact selected destinations; replace each inert slot only when its own route and basis are supported."}
```

Mirror exactly in `frontend/src/ui/gapCatalogue.ts` as `"G-portfolio-opportunity": { status: "open", placements: ["portfolio.opportunity.review-finding", "portfolio.opportunity.inspect-headroom"] }`. Import `MissingClaim` from `../ui` in `EstatePortfolio.tsx`. Keep the two `span` elements' class, `aria-label`, text and lack of `href`/button; make `MissingClaim` the outer element, with literal pairs so the scan can trace both visible copy and the accessible name:

```tsx
<MissingClaim as="span" className="portfolio-inert" gapId="G-portfolio-opportunity" placement="portfolio.opportunity.review-finding">
  <span aria-label="Review opportunity Finding, Not available yet">Review opportunity Finding · Not available yet</span>
</MissingClaim>
<MissingClaim as="span" className="portfolio-inert" gapId="G-portfolio-opportunity" placement="portfolio.opportunity.inspect-headroom">
  <span aria-label="Inspect physical headroom, Not available yet">Inspect physical headroom · Not available yet</span>
</MissingClaim>
```

The nested spans are required by the current `MissingClaimProps`, which has no `aria-label` prop. The scanner's ancestor rule covers both their literal text and accessible-name attributes. Verify the registry/mirror/usage bijection and copy with `node tools/checks/missing-claim-scan.mjs`, `node --test tools/checks/test_missing_claim_scan.mjs`, the mock-gap catalogue fixtures, then `tools/check-all.ps1`; all eleven guards must pass. Do not add an orphan-scan exception, suppress a fixture, or turn either span into navigation. This supersedes closure 1's statement that these two pieces of ordinary labelled text need no gap registration; it does not change their visible wording or `UnavailableEntry` multiset.

### Eleven run-2 readings

| # | Ruling |
| --- | --- |
| 1 | **Confirm.** Lane A's API/client mount may precede the page and shell route may follow it in the sequential run-2 commits. Review the combined result at `04474b3c`. |
| 2 | **Confirm.** Matrix headers are plain selected Site name/code. Null cell targets render `Site detail unavailable`; reason remains available through `aria-description` and `title`. Do not synthesize a Site link. |
| 3 | **Confirm.** `links.site` opens a current Site view with `Opens current Site view`; cold/EV Finding detail stays inert `Finding detail unavailable`; only W1's exact supported Finding route gets `Review Finding`. |
| 4 | **Confirm.** The first Value line uses the selected W3-01 consequence: priced outward bounds, `Unpriced`, `Source unverified`, or `No consequence recorded`; pending/historical Site prefixes suppress current price. The second line is `Basis not recorded` because the row wire has no basis field. |
| 5 | **Confirm.** Site-owned non-EV money uses outward rounding; EV gross-tariff context uses half-even two decimals. `quantityText` and the selected currency stay with the EV amount. No client sum is allowed. |
| 6 | **Confirm.** The Evidence aside is `div.note` with a heading role, outside the four named `section.panel` nodes. It shows server-provided `Site {site_code}` as text. |
| 7 | **Confirm.** The footer warning is driven only by a *different* applicable EV Site whose selected coverage is `UNKNOWN`, `PENDING_RECOMPUTE`, or `STALE_SOURCE`; it cannot be a generic warning for every Portfolio. |
| 8 | **Confirm.** A load-more 401/409/503 replaces the entire prior success state with the refusal; no privileged Site names, cards, rows or cached cutoff remain visible. |
| 9 | **Confirm.** Mock `screen-foot` and topbar Portfolio-name/search chrome are shared mock shell, not Portfolio-owned measured blocks. Measure the app header, date bar, body, four panels, cards and document caps. |
| 10 | **Confirm.** Unsupported opportunity quantities are neutral grey, 16px at 1440 and 13px at 390; they remain words rather than a fabricated kW or amount. |
| 11 | **Confirm.** Tighter Finding-cell spacing is permitted because the actual rows include honest missing-basis lines. Keep the measured row and column caps; do not drop those lines to imitate the mock. |

Run-2 evidence already records 1440/390 positive, partial and historical captures in `.agent/W3-03-evidence/app-portfolio-{positive,partial,historical}.json` at `04474b3c`: every measured block has `over=[]`, document width has no overflow, and the four panels satisfy their caps. Positive is `CURRENT` with three selected Finding rows; partial adds `W303-EMPTY-001` and is `UNKNOWN`; the explicit `2026-09-30T00:00:00Z` cutoff is `HISTORICAL` with an empty Finding row. The 390 positive document is 2947px against 3512px, and the 1440 positive document is 1362px against 1714px. Run-2 frontend suite was 104 files/2449 tests passed, `tsc` and build passed; backend focused API was 4 passed/1 skipped. Its 9/11 guard result is **not** closure evidence until P-2-1 makes both failing checks pass.

### Run-3 captures: fixture, request and acceptance

Use the real page at Vite `:5781` proxied to the capture API `:9781`, the existing `.agent/W3-03-evidence/test_serve_portfolio.py` and `capture-portfolio.mjs`, and private `*_test` DBs. The browser script must write both widths and one JSON per state. Keep existing positive/partial/historical files as baseline, then recapture after the MissingClaim markup because panel geometry may change. Use the exact one-day request `[2026-10-06T00:00:00Z,2026-10-07T00:00:00Z)` and the harness's frozen `fx.frozen`; omit `known_at` except the explicit historical case. A capture control must select the following **real API fixtures**, not replace the HTTP response with handcrafted JSON:

| Capture name | Fixture and request/control | Required visible/API result |
| --- | --- | --- |
| `positive` | `build_portfolio_fixture(..., cold_case="excursion", cold_drain=True)`; normal `/portfolio?from=2026-10-06T00%3A00%3A00Z&to=2026-10-07T00%3A00%3A00Z`. | `CURRENT`; four authorized Sites; W1 priced, cold unpriced, two EV gross-tariff lines; three selected Findings; five card states `SITE_OWNED/UNKNOWN/UNSUPPORTED/UNSUPPORTED/NOT_ESTABLISHED`. |
| `partial` | Same clean fixture, then existing `POST /__capture/empty-site` adds authorized unselected `W303-EMPTY-001`; reload the same URL. | `UNKNOWN`, F/E/M `PARTIAL/PARTIAL/PARTIAL`; five matrix Site columns, no invented fifth-Site Finding or amount. |
| `historical` | After `partial`, reload with `known_at=2026-09-30T00%3A00%3A00Z`. | `HISTORICAL`, F/E/M `UNKNOWN/UNKNOWN/UNKNOWN`, no selected Findings or current amount; first card `WITHHELD`. |
| `pending` | In a fresh private DB use the same fixture builder with `cold_drain=False`, exactly the persisted `a_lineless_cold` variant in `backend/tests/test_w303_portfolio_scope_snapshot_postgres.py::test_late_revision_pending_historical_and_mixed_source`. Serve the real API at its frozen cutoff; same one-day URL. | `PENDING`, F/E/M `COMPLETE/COMPLETE/PARTIAL`; `Updating selected Sites`; no invented cold line/exclusion; W1 `SITE_OWNED` remains visible because its category is covered. This is the line-less guard path, not an unproved cold `PENDING_RECOMPUTE` claim. |
| `empty` | In a fresh clean fixture authenticate as a principal in a separate tenant with **zero** authorized imported Sites, following `test_foreign_tenant_missing_site_and_grant_fence`; same request URL. | 200 `EMPTY_SCOPE`, F/E/M `EMPTY/EMPTY/EMPTY`; `No accessible Sites`, zero selected Finding rows, zero matrix Sites, no borrowed Site name or ID. This is not the authorized empty Site used in `partial`. |
| `refusal-401` | Request the Portfolio URL without valid Bearer authentication (the API's `test_auth_before_parse_and_all_refusals` path). | 401 `UNAUTHENTICATED`; refusal copy, no panels/cards/rows/Site names. |
| `refusal-409` | On the real clean fixture obtain a signed page-one cursor with `limit=1`, then add `W303-EMPTY-001` via `POST /__capture/empty-site` and request page two with the old cursor, as in `test_foreign_tenant_missing_site_and_grant_fence`. Exercise the browser load-more clearing path with that cursor. | 409 `ESTATE_BASIS_CHANGED`; old Site names/cards/rows cleared, one refusal. Do not use a malformed cursor (that would be 422). |
| `refusal-503` | On a fresh serving process leave `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` unset or malformed before the authenticated request, following `test_cursor_lens_window_cutoff_and_v1_token`; do not disturb the positive fixture. | 503 `ESTATE_STORE_UNAVAILABLE` frozen null-field body and refusal; no Site names/cards/rows. |

Extend the capture harness with a capture-only cold-drain selector and separate-tenant authentication as needed; keep production routes unchanged. For 409, browser capture must start from a success page and trigger `Load more Findings`, then record the cleared refusal, not merely navigate to a refusal URL. The current `capture-portfolio.mjs` assumes all block selectors exist; for refusals write `refusal` and document dimensions, require all privileged block selectors absent, and apply no positive panel/card cap to null rectangles. For successful captures require the exact status, four named panels, five cards, full-scope matrix count, `over=[]`, `docScrollW <= docClientW`, table/matrix internal scrolling at 390, and Q24 document and individual caps. Name files `portfolio-<state>-1440-app.png`, `portfolio-<state>-390-app.png`, `app-portfolio-<state>.json`; put them under `.agent/W3-03-evidence/`. A fixture production failure is a failed run, not a license to paste example response values.

### Registry rows and closeout packet

Lane A adds exactly four `panels` rows in `frontend/docs/architecture/v69-dependency-registry-pilot.json`, matching the v69 `portfolio` rendered-panel order. Use `status:"gap"` until independent review accepts the implemented paths; `portfolio:3` remains a gap for its scenario even after a review of the honest unavailable display. Do not close `A-estate-comparability` or `D-estate-comparable-sites` from this page's layout alone. Initial rows:

```json
[{"screen_id":"portfolio","panel_index":1,"title":"Where management should act first","area":"estate-aggregation","requires":["A-estate-index-scope","I-estate-finding-root","A-estate-action-summary"],"status":"gap","reason":"W3-03 selected Finding/Action composition awaits independent whole-slice review; priority and confidence remain unassessed."},{"screen_id":"portfolio","panel_index":2,"title":"Objectives across the estate","area":"estate-aggregation","requires":["A-evidence-shared-projections","I-estate-evidence-root","D-estate-comparable-sites"],"status":"gap","reason":"W3-03 selected capability matrix awaits independent whole-slice review; unknown cells are not health conclusions."},{"screen_id":"portfolio","panel_index":3,"title":"An opportunity beyond reducing cost","area":"estate-aggregation","requires":["A-estate-comparability","I-mini-depth-read"],"status":"gap","reason":"The W3-03 panel is an honest unavailable scenario; no reviewed opportunity Finding, physical-headroom or demand basis supports its quantities or destinations."},{"screen_id":"portfolio","panel_index":4,"title":"What changed in this review","area":"estate-aggregation","requires":["A-estate-projections","I-estate-action-root"],"status":"gap","reason":"W3-03 exact selected Action/verification disclosure awaits independent whole-slice review; recovered value and completed activity remain unestablished."}]
```

The packet is `.agent/W3-03-review-packet.md`. It must give: task/spec revision and `04474b3c` baseline; exact commit range and file list split by Lane A/B; one-head Alembic proof and `0031 unused`; four-panel registry path/status and the P-2-1 gap/mirror/usage proof; one-snapshot/auth/cursor/selection and unchanged W3-01/02 root checks; B3 one-day three-domain selected IDs and W1/cold/EV money boundaries; all pure-versus-persisted variant limits from r1b3; full-scope cards/matrix/progress/EV footer and refusal-clearing results; the eight capture states above with 1440/390 JSON/PNG paths and measured caps; same-revision full backend suite, frontend suite, `tsc`, build and 11/11 `check-all` results; known deviations and the exact independent-review command `git diff <reviewed W3-02 merge base>..HEAD -- ':!.agent'`. Record failed or skipped commands literally. The independent reviewer checks that diff plus the packet and captures before any owner W3 walkthrough; the packet cannot declare acceptance on the reviewer's behalf. No owner W3 wave-exit acceptance is inferred from a passing test or registry row.


## Run-3 registry rulings (r3)

P-3-1 is resolved for run 3. Insert the following two new nodes in `v69-dependency-registry-pilot.json` `nodes`; keep both `open` until independent review supplies evidence. These are the literal complete objects:

```json
[
  {
    "id": "I-estate-portfolio-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "estate-aggregation",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-estate-projections",
      "I-estate-finding-root",
      "I-estate-action-root",
      "I-estate-evidence-root",
      "I-estate-money-root",
      "D-estate-comparable-sites"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W3-03",
    "acceptance_target": "One authorized, selected Portfolio snapshot composes full-scope Finding, Action, Evidence and Financials reads with exact coverage, provenance and no combined value."
  },
  {
    "id": "I-estate-portfolio-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "estate-aggregation",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "I-estate-portfolio-read"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W3-03",
    "acceptance_target": "Four Portfolio panels render the selected snapshot, honest missing states and refusal clearing at desktop and narrow widths."
  }
]
```

The following complete node objects are reused unchanged. Architecture and data nodes have no `layer` field; their kind is their gate type. Do not insert duplicate copies:

```json
[
  {
    "id": "A-estate-index-scope",
    "kind": "architecture",
    "area": "platform",
    "owner": "Architect",
    "status": "open",
    "requires": [
      "A-claim-work-routes"
    ],
    "effort": "M",
    "evidence": null,
    "decision": "Tenant, Site, window, coverage and freshness for global Findings and Actions lists.",
    "task": "W3-01"
  },
  {
    "id": "I-estate-finding-root",
    "kind": "implementation",
    "layer": "ui",
    "area": "claims",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-estate-index-scope",
      "I-finding-index"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W3-01"
  },
  {
    "id": "A-estate-action-summary",
    "kind": "architecture",
    "area": "estate-aggregation",
    "owner": "Architect",
    "status": "open",
    "requires": [
      "A-estate-index-scope",
      "A-action-index"
    ],
    "effort": "S",
    "evidence": null,
    "decision": "Optional ActionSummary cross-Site scope and freshness; not a prerequisite of ranked Findings or value cards.",
    "task": "W3-01"
  },
  {
    "id": "D-estate-comparable-sites",
    "kind": "data",
    "area": "estate-aggregation",
    "owner": "Planner specifies; Implementer builds",
    "status": "open",
    "requires": [
      "A-estate-comparability",
      "I-finding-store",
      "I-S2-02",
      "I-S4-02"
    ],
    "effort": "L",
    "evidence": null,
    "fixture": "Multiple Sites with aligned windows, coverage, currency, price basis and overlap groups through normal ingestion."
  },
  {
    "id": "A-evidence-shared-projections",
    "kind": "architecture",
    "area": "evidence",
    "owner": "Architect",
    "status": "open",
    "requires": [
      "A-S2-evidence",
      "A-evidence-readiness-health"
    ],
    "effort": "M",
    "evidence": null,
    "decision": "CapabilityReadiness, SourceHealth, AcceptedEvidenceIndex and SiteEvidenceMatrix contracts for all known mini-grid, cold-chain, EV and estate consumers.",
    "task": "W2-04"
  },
  {
    "id": "I-estate-evidence-root",
    "kind": "implementation",
    "layer": "ui",
    "area": "estate-aggregation",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-estate-index-scope",
      "I-capability-read"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W3-02"
  },
  {
    "id": "A-estate-comparability",
    "kind": "architecture",
    "area": "estate-aggregation",
    "owner": "Architect",
    "status": "open",
    "requires": [
      "A-estate-index-scope",
      "A-money-comparability"
    ],
    "effort": "L",
    "evidence": null,
    "decision": "Cross-Site aligned windows, coverage, currency/price basis, consequence overlap and non-double-counting rules."
  },
  {
    "id": "I-mini-depth-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "mini-grid-analytics",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-mini-breadth-projections",
      "I-mini-breadth-store"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W4-02"
  },
  {
    "id": "D-mini-breadth-windows",
    "kind": "data",
    "area": "mini-grid-analytics",
    "owner": "Planner specifies; Implementer builds",
    "status": "open",
    "requires": [
      "A-mini-breadth-rules",
      "I-mini-breadth-store"
    ],
    "effort": "L",
    "evidence": null,
    "fixture": "Distinct service, renewable, fuel and backup windows with accepted evidence and attested deliveries/requests."
  },
  {
    "id": "A-estate-projections",
    "kind": "architecture",
    "area": "estate-aggregation",
    "owner": "Architect",
    "status": "open",
    "requires": [
      "A-estate-comparability",
      "A-evidence-shared-projections",
      "A-finding-index"
    ],
    "effort": "L",
    "evidence": null,
    "decision": "PortfolioSummary, PortfolioEvidenceMatrix, consequence rollup and SiteAssessmentSummary source/sort/freshness/drill-down contracts."
  },
  {
    "id": "I-estate-action-root",
    "kind": "implementation",
    "layer": "ui",
    "area": "work-verification",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-estate-index-scope",
      "I-action-read"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W3-01"
  },
  {
    "id": "I-estate-money-root",
    "kind": "implementation",
    "layer": "ui",
    "area": "money",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-estate-index-scope",
      "I-financial-read"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W3-02"
  }
]
```

Replace the r2 initial Portfolio rows with these four literal `panels` rows, in this order:

```json
[
  {
    "screen_id": "portfolio",
    "panel_index": 1,
    "title": "Where management should act first",
    "area": "estate-aggregation",
    "requires": [
      "A-estate-index-scope",
      "I-estate-finding-root",
      "A-estate-action-summary",
      "I-estate-portfolio-read",
      "I-estate-portfolio-ui",
      "D-estate-comparable-sites"
    ],
    "status": "gap",
    "reason": "W3-03 selected Finding/Action composition awaits independent whole-slice review; priority and confidence remain unassessed."
  },
  {
    "screen_id": "portfolio",
    "panel_index": 2,
    "title": "Objectives across the estate",
    "area": "estate-aggregation",
    "requires": [
      "A-evidence-shared-projections",
      "I-estate-evidence-root",
      "D-estate-comparable-sites",
      "I-estate-portfolio-read",
      "I-estate-portfolio-ui"
    ],
    "status": "gap",
    "reason": "W3-03 selected capability matrix awaits independent whole-slice review; unknown cells are not health conclusions."
  },
  {
    "screen_id": "portfolio",
    "panel_index": 3,
    "title": "An opportunity beyond reducing cost",
    "area": "estate-aggregation",
    "requires": [
      "A-estate-comparability",
      "I-mini-depth-read",
      "I-estate-portfolio-ui",
      "D-mini-breadth-windows"
    ],
    "status": "gap",
    "reason": "The W3-03 panel is an honest unavailable scenario; no reviewed opportunity Finding, physical-headroom or demand basis supports its quantities or destinations."
  },
  {
    "screen_id": "portfolio",
    "panel_index": 4,
    "title": "What changed in this review",
    "area": "estate-aggregation",
    "requires": [
      "A-estate-projections",
      "I-estate-action-root",
      "I-estate-portfolio-read",
      "I-estate-portfolio-ui",
      "D-estate-comparable-sites"
    ],
    "status": "gap",
    "reason": "W3-03 exact selected Action/verification disclosure awaits independent whole-slice review; recovered value and completed activity remain unestablished."
  }
]
```

Add this literal `registry_dependencies` object to the existing `portfolio` screen-ledger row, preserving that row's other fields:

```json
{
  "product_node_id": "P-estate-area",
  "node_ids": [
    "A-estate-index-scope",
    "I-estate-finding-root",
    "A-estate-action-summary",
    "I-estate-portfolio-read",
    "I-estate-portfolio-ui",
    "D-estate-comparable-sites",
    "A-evidence-shared-projections",
    "I-estate-evidence-root",
    "A-estate-comparability",
    "I-mini-depth-read",
    "D-mini-breadth-windows",
    "A-estate-projections",
    "I-estate-action-root"
  ]
}
```

Checker reasoning: `P-estate-area` governs the `estate-aggregation` screen; the ledger `node_ids` above are exactly the first-occurrence union of the four `requires` arrays in panel order. Each panel directly names a `layer:"ui"` and a `layer:"projection"` implementation node and a data node, so the UI/projection and non-structural claim gates pass. Both new nodes have allowed implementation layers, `open` status, effort, known non-product prerequisites and an architecture ancestor; the read depends on the reviewed W3 roots and the UI depends on the read, with no cycle. The opportunity row retains the open W4 depth and data gates as honest missing-state dependencies; it does not declare a headroom claim real. All four rows remain `gap`, so the checker cannot treat any open prerequisite as a real-panel closure. No checker change or node closure is authorized by these declarations.

## Run-3 empty-state ruling (r3b)

**P-3-2 card height: choose shorter wording (option c).** For `OPERATING_COST:NO_LINE`, the value line is exactly `No supported value`, replacing `No supported value for this window` in both the API `display_value` and the page's `CARD_VALUE.NO_LINE` fallback. Keep the existing detail `No selected operating-cost consequence` and basis `No value line`; the selected window is already stated in the shared date bar. This wording means no supported value in the selected scope and window, including `EMPTY_SCOPE`, without implying a zero amount. Keep the mock's 22 px value type at 390 and the five-card two-column grid. The mock measures each first-row card at 183 px, so the existing 207 px maximum remains binding; do not raise it. The 218 px empty capture is a failed geometry result, not an accepted exception. Card 1 must be remeasured because it shares card 0's grid row.

Test the exact literal in the backend `NO_LINE` card response and the frontend value-card rendering/fallback. Recapture all eight run-3 states at 1440 and 390 after the copy change. The real `EMPTY_SCOPE` 390 capture must show `card0.h <= 207` and `card1.h <= 207`, with `over=[]`; retain every other Q24 cap and document-width gate. If the shortened literal still exceeds either card cap, return to Architect with the measured rectangle rather than silently changing type size or cap.

**P-3-2 matrix scroll:** require horizontal overflow at 390 when `body.objectives.length >= 4`, as the existing matrix contract specifies for four or more authorized Sites. The exact gate is `viewportWidth === 390 && body.objectives.length >= 4 => matrix.scrollWidth > matrix.clientWidth`; with zero to three Site columns, assert the exact rendered column count and retain the scroll container, but do not demand overflow. In particular, zero Sites gives `scrollWidth === clientWidth` legitimately. The Findings table's internal-scroll check and `document.scrollWidth <= document.clientWidth` still apply to the empty capture. This condition does not waive full-scope matrix columns or the scroll proof for the four- and five-Site stocked and partial fixtures.

