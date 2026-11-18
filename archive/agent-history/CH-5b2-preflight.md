# CH-5b2 pre-flight (the "Why?" trace and server ETag/304)

Branch `task/CH-5b2-why-trace` from main `08a6c52e4`. Read: build-sheet-CH-5b §0/§1 R1-R4/OWN-CH5c/§2/§3/§5/§6/§7, the
Build units CH-5b2 entry, CH5b1-R; build-sheet-CH-5c R6/R7 and §8.8; design §5b.5; MD-0 Kobo rows. No code yet.

## P1. Backend anchors on main (`B` = `backend/assetops_backend`)

| Name | Anchor |
|---|---|
| chain routes | `B/chain_api.py:41-43` (`SITE_CHAIN_ROUTE`, `ESTATE_CHAIN_ROUTE`, `THREAD_ROUTE`); handlers `:102`, `:135`, `:168`; router factory `:68` |
| chain router wiring | `B/main.py:638-641` (no `responses=` today: the three chain routes are **not stored**) |
| stored routes today | board `B/outcome_api.py:218`, summary `:250`, Portfolio `B/estate_portfolio_api.py:75`, Findings index `B/estate_api.py:64` |
| store | `B/chain/response_store.py`: `etag` `:76` (route, key, W, version, `valid_until`), `StoredRoute` `:91`, `serve` `:140`, `_response` `:223`, `finish` `:230` |
| live-row lookup | `B/chain/adapters/postgres_response_store.py:17` `_LOOKUP` (unique key + `valid_until` live predicate), `lookup` `:60` |
| watermark | `B/chain/adapters/postgres_response_store.py:38` `read_watermark`; rule text `B/chain/watermark.py` |
| reads | `B/chain/read.py:299` `ChainRequest` (`day` `:306`, `threads` `:334`, `action_facts` `:359`, `placement_facts` `:344`); `DayFacts` `:196` |
| wire builders | `B/chain/site_chain.py` `days_of` `:32`, `threads_of` `:88`, `actions_of` `:104`, `outcomes_of` `:157` |
| refs | `B/chain/refs.py` `thread_ref` `:163`, `finding_ref` `:167`, `action_ref` `:173`, `evidence_ref` `:187` |
| outcome map | `B/outcomes/outcome_map.py` `categories_for` `:95`, `thread_signal_key` `:110`, `ENTRIES` `:16` |
| clean-day measures | `config/chain/thread-lifecycle-v1.json` `clean_day_measures` (mechanism -> measures) |
| vocabulary | `B/chain/vocabulary.py` (no `why.*` keys yet; `THREAD_STATE_WORDS` `:25`) |
| ledger | `B/read_scope.py:75` `ReadScope.ledger`, `:141` `ledger()`; store tests assert hits via `HEADER` `X-AssetOps-Stored` |

Fact: there is no `etag.py` to create. The tag is `response_store.etag` (OWN-CH5c), so `etag.py` is **not created**.

## P3. Estate guard rule 8

No edit needed. `tools/checks/configuration-persistence.ps1:955-970` lists `B/chain/adapters/postgres_chain_read.py`
as a read-only reader (the SQL-write refusal still applies). The watermark SQL already lives in
`postgres_response_store.py` (CH-5c). The one new read (Q4) goes in `postgres_chain_read.py`, which is SELECT-only.

## Overlap with lane 2 (CH-5b1)

- `B/main.py`: I add `responses=responses` to `build_chain_router(...)` at `:638`; CH-5b1 adds the graph check in
  `create_app`. Different lines; second to merge resolves.
- `B/chain/composition.py`: no edit expected from me (the store is built in `main.py:572`).
- `config/chain/perf-budgets-v1.json` / `tools/checks/perf_budget.py` (CH-5b1): I do not edit them; I report
  `why_trace_ms` in the packet (Q11).
- `config/chain/stored-composer-modules-v1.json` (W6 module list) grows by the why module(s) via a reviewed diff.

## Questions (batched; each has a default)

- **Q1. Store the five routes.** The chain routes are not stored today, but the L2m acceptance needs a 304 "after the
  watermark statement plus one indexed live-row lookup, with no composition" on **every** chain and why route. That is
  only possible for a stored route. Default: route all five (`/sites/{c}/chain`, `/estate/chain`, the thread route,
  both why routes) through `ResponseStore.serve`, with the board's key rule (one Site, its own watermark Sites) for
  the Site routes and the summary's `admit` rule for the estate ones. `prebuilt-routes-v1.json` is unchanged. Then W6
  and `fresh` on one polish clone, as the brief says.
- **Q2. 304 mechanics.** Default: `serve(..., if_none_match=...)`. On (a), the same snapshot reads W then the live row;
  when the row exists and its `etag` equals the header (strong compare, quotes stripped, a list and `*` handled), the
  reply is `304` with an empty body, the `ETag`, and `Cache-Control: private, no-cache`. Otherwise the current
  behaviour holds. `Cache-Control` goes on every 200 and 304 of the five routes. In `off` or `compose` mode there is no
  ETag, so there is no 304. The four routes that are already stored keep their headers and behaviour unchanged.
- **Q3. Root node ids.** §2.1's example has `row_state` with `ids: []`, but R1 and the L0 test say "no node without
  ids". Default: `row_state` is the root and is always emitted; its `ids` are the board row's own link-ref ids, which
  may be `[]`. The rule "no node without ids" applies to every non-root node.
- **Q4. One new read for the finding and analytic nodes.** The thread rows carry `finding_id`, but no revision, run or
  cited count. Default: one SELECT-only port method `trace_facts(tenant, site, finding_ids, k)` in
  `postgres_chain_read.py`. It returns each Finding's head revision at `k` (the `_FINDING_HEADS` head rule, without
  the window), `analytic_run_id`, and its `finding_revision_evidence` count, in one statement, memoised in
  `ChainRequest`. The `analytic` node ids are the head revisions' `analytic_run_id`s.
- **Q5. Which measures a category uses.** There is no `CONTRIBUTIONS` table yet (`chain/measures.py:4-6`, CH-6).
  Default: measures = the `clean_day_measures` of the mechanisms of the category's threads (threads whose
  `categories_for(thread_signal_key(m))` names the category, moved or checked). A category with no such thread has no
  `measure_day` node. Measure labels are new copy in `vocabulary.py`, a MOCK DEVIATION. The proposed labels:
  - `avoidable_gen_min`: "Avoidable generator minutes";
  - `productive_kwh`: "Productive energy";
  - `daylight_headroom_kw`: "Daytime solar headroom";
  - `critical_served`: "Critical load served";
  - `chamber_temp_c`: "Chamber temperature";
  - `backup_start_chain`: "Backup start";
  - `charging_kwh`: "Charging energy".
- **Q6. `days_used` template.** §2.3 has no key for the "Days used" line. Default: a new `why.days` key, "{c} of {e}
  day{s} checked". Each nonzero suffix is appended: " · {p} partly checked", " · {n} with no readings",
  " · {q} not in yet". These are counted over the category's measures, or over every Site-type measure when the
  category has none, from the window's `DayFacts` grades (COMPLETE / PARTIAL+LOW / NO_DATA / PENDING; NOT_EXPECTED is
  not counted). This is a MOCK DEVIATION against the DAYS lines (`outcomes.js:111-114`).
- **Q7. `comes_from` with fewer than 2 sources, and the price suffix.** Default: emit the lines that exist (0-4, cap
  4: measures, then threads, then Actions). For 0 lines, add a new key `why.from.none`, "Nothing stored feeds this
  yet". The " × declared price {p} per kWh" suffix is **omitted** in this unit, because no declared-price read is in
  the chain reads (money is CH-6). It is recorded as a Known Deviation.
- **Q8. Finding title and Action state label.** Default: both come from the board row's own items. The finding title
  is the `issues[]` item whose `link_ref` names the Finding. The Action state label is the `in_hand`/`earlier` item
  `state_label` for that Action. No new copy. A line with no matching item is not emitted. There is one finding line
  per thread: n = its visible occurrences, first day = its first occurrence day.
- **Q9. Estate `text`.** There is no template. Default: a new `why.estate.say` key, "{category name} across {n}
  site{s}". `comes_from` is one line per Site, "{site}: {site say}" (`why.estate.from`). `days_used` is one per-Site
  clause joined by " · ", as in PFDAYS. `would_change` is the first Site's R3 line in Site order. `evidence_ref` is
  `estate_ref("findings")`. No money anywhere.
- **Q10. `say`.** Default: the board row's `headline` verbatim (CH-5a2), else its `state_label`. No new copy.
- **Q11. `why_trace_ms`.** Default: the L2m median of 5 `trace()` runs on Kobo D13 OPTIMIZE_COST, inside one read
  scope per run, with the reads included and the route admission excluded. It is reported in the packet. Wiring it
  into `perf_budget.py` / `perf-budgets-v1.json` `measured_by` is left to whichever of CH-5b1/5b2 merges second,
  because those files are lane 2's.

STOP for rulings.
