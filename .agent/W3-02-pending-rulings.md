# W3-02 pending rulings (Lane B, commit 1)

Recorded, not decided. Commit 1 code (`8d1e6325`, `c9e19695`) applies the reading named in each item; a ruling may change it.

## c1-q1 - EV `historical_label` vs "explicit earlier cutoff" (affects commit 3)
0c `EvSiteReads.money_on` (`ev_site_reads.py:349`) sets `historical_label` only when the pinned snapshot `state == "HISTORICAL"`. That state is `known_at < watermark` in `EvReadService._snapshot` (`postgres_assessment_store.py` "historical = known_at is not None and watermark is not None and known_at < watermark"), where `known_at` is the row-local Site evidence cutoff (max disposition by the estate `k`). The 0c H1 ruling says `Historical as of {known_at}` applies "for an explicit earlier cutoff", and closure 1 Q1 / 0b M3 define HISTORICAL as estate `known_at` earlier than the captured DB time.
They differ: an explicit earlier estate cutoff with no disposition after it gives `known == watermark`, so the state is not HISTORICAL and `historical_label` is null, while the estate rule says the row is historical. Question: should commit 3 derive the label from the estate cutoff (`snap.basis_historical`), ignoring `historical_label`, or should Lane A change the facade? Commit 1 Evidence does not use this field. It applies the estate rule itself through `snap.basis_historical`.

## c1-q2 - EV `METER_GAP` input not exposed by the pinned facade
Closure 1 Q4 takes EV gaps from the complete `_next_candidates(missing, power_missing, unknown_meter)`. The 0c `EvSiteReads.capabilities_on` returns capabilities but not the selected sessions' `unknown_meter_seconds`. Interim: `EvidenceMoneySnapshot.ev_capabilities` (`estate/adapters/postgres_evidence_money_read.py`) calls `ev_site._sessions(ev_site._pinned_ctx(c, pin))` on the same connection. This is a private call, and the pinned context is built twice. Question: should Lane A add `unknown_meter` (or the session list) to `capabilities_on`?

## c1-q3 - readings applied where the spec is silent (confirm or amend)
1. EV gap codes that affect only supporting claims (`INDEPENDENT_POWER_GAP`, `SITE_IMPORT_GAP`, `TARIFF_GAP`) still form a group with `unlocks: []`. A code affects a display row only through that row's claim's missing roles.
2. Current gaps come from CURRENT (and W1 CURRENT-day) rows only. They do not come from pending, stale, unknown or historical rows. A pending or stale row keeps its prior readiness and limitation in `disclosure.prior_selection`.
3. `summary.capability_count` is the display-row count (equal to `total_count`) even under partial coverage. `full/limited/none/unknown_count` are non-null only when `status == CURRENT` and coverage is COMPLETE, and are zeros for EMPTY_SCOPE. `limited_site_count` is also null when any row is CONTRADICTORY ("null affected count").
4. Under an explicit historical cutoff the cold/EV rows are `raw_state: HISTORICAL`, with readiness CONTRADICTORY if a constituent is CONTRADICTORY and UNKNOWN otherwise. This is 0b M3 applied to cold/EV.
5. The token `sites[]` arrays for Evidence are: `selected_assessment_revision_ids` (W1 interval IDs plus window revision; cold, both analytic IDs per window; EV, the selected assessment) and `cited_accepted_evidence_ids`. Finding, Action, consequence and assumption arrays are `[]`. EV session revision IDs are not included.
6. Row link query times use `analytics.cold.plain` (six-digit `Z`), the same format the W2 Site links use.
7. On a live read's page two, the cursor cutoff is earlier than the read time, so W1 `claim_limit_on` labels the day HISTORICAL (it compares `known_at < transaction_time`). Cold/EV rows follow page one's basis mode. The selection token is unaffected because it holds IDs, not states.

# W3-02 pending rulings (Lane B, commit 2)

Recorded, not decided. Commit 2 (`d9f898e7`) applies the reading named in each item.

## c2-q1 - gap `Sites` cell names
Closure 1 says the gaps `Sites` cell shows sorted stored Site names with codes in disclosure. The accepted commit-1
wire `gaps[]` carries `site_ids` and `site_codes` only, and `rows` is paged, so a gap's Site may not be on the page.
Interim: the page maps code -> name from the loaded rows and falls back to the stored code; codes are in the gap's
disclosure. Question: should commit-1's `_groups` add `site_names` (Lane B `estate/evidence_money.py`), or is the
code fallback acceptable?

## c2-q2 - refusal copy for codes the W3-02 state table does not name
The table names copy for 401/403/404/503, `ESTATE_BASIS_CHANGED`, `INVALID_WINDOW`, `ESTATE_PARAMETER_UNKNOWN`/
`ESTATE_CURSOR_INVALID`. The endpoint actually sends W3-01 codes, including `ESTATE_SELECTION_INCONSISTENT`,
`INVALID_KNOWN_AT`, `INVALID_LIMIT`, `INVALID_CURSOR`, `ESTATE_STORE_UNAVAILABLE`. Interim (`EVIDENCE_REFUSAL_COPY`):
503 store -> the 503 sentence; `ESTATE_SELECTION_INCONSISTENT` -> the 409 sentence; `INVALID_KNOWN_AT`, `INVALID_LIMIT`,
`INVALID_CURSOR` -> `This selection cannot be read. Reset the filters.` (the W3-01 `INVALID_KNOWN_AT` copy says
"cutoff", which the plain-language rule excludes). Confirm or amend.

## c2-q3 - closure-5 B5 route-read tests for commit 2
B5 asks commit 2 route-read tests to follow generated cold/EV Evidence links into the Site read and assert the exact
window/cutoff, no 422 and base-route fallback. Commit 1's Postgres tests assert the link shape
(`test_w302_evidence_cold_scope_windows_and_citations`, `test_w302_evidence_ev_window_rows_links_and_gaps`) but do
not call the W2 Site read with it. This run built only the page/client and UI tests. Question: is following the link
into the W2 cold/EV Site API a Lane B Postgres test for this commit (new `test_w302_evidence_links_postgres.py`), or
part of Lane A's mounted-route captures?

## c2-q4 - row context words
The ledger says pending amber / historical blue context is shown separately from the readiness chip. The page uses
`New evidence is being assessed` (PENDING_RECOMPUTE), `May miss newer readings` (STALE_SOURCE), `Not yet assessed`
(UNASSESSED/UNKNOWN placeholder) and `Historical as of {estate known_at}`; the server's row
`disclosure.historical.label` stays in the row disclosure. Confirm the words.
