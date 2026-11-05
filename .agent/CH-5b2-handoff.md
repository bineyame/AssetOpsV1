# CH-5b2 handoff (partial: build and L0/L2m done; clone, guards and packet remain)

Branch `task/CH-5b2-why-trace`, head `d07257d57` (commits `2f3f5402d`, `a1ae043f1`, `d07257d57` on `c3cf85409`).
Stopped at the context cap. Rulings: CH5b2-R in `AssetOpsV1-plan2\.agent\build-sheet-CH-5b.md` (end of file).

## Landed (file anchors)

- `B/chain/why.py`: `trace(SiteTraceInput) -> Trace` (nodes + text, R1-R3), `site_trace(req, ref, ...)` (the route's
  one call: `site_chain.threads_through` history, Actions, one `req.trace_facts`), `estate_text`, `check_category`.
  `Trace.unmatched` counts Q8 lines not emitted (not on the wire).
- `B/chain/site_chain.py` `threads_through`: threads with an occurrence before the window end and a state on the
  board day (needed: Kobo D13 has no in-window occurrence of the generator thread; D4/D11 Findings now reached).
- `B/chain/vocabulary.py` end: `WHY_TEXT`, `MEASURE_LABEL`, `why`, `why_days` (appended with a shell heredoc, a
  process slip vs the Write/Edit rule; content as ruled).
- `B/chain/response_store.py`: `serve(..., if_none_match)`, `tag_matches` (strong; `*` only on a live row),
  `_not_modified` (304, `X-AssetOps-Stored: hit`).
- `B/chain/read.py` `ChainRequest.trace_facts` + port protocol; `B/chain/adapters/postgres_chain_read.py`
  `_TRACE_FACTS` / `trace_facts` (one SELECT).
- `B/chain_api.py`: `SITE_WHY_ROUTE`, `ESTATE_WHY_ROUTE`; all five routes via `site_served` / `estate_served`
  (keys: board key + `category` / thread id; estate: `parsed_key` + `category`); `_done` sets
  `Cache-Control: private, no-cache` on every response. `B/main.py:638` passes `lifecycle`, `responses`.
- `B/outcome_api.py` `estate_sites(items=)`; `B/site_outcomes/read.py` `summary_window` (extracted from `_summary`).
- `tools/chain_watermark_guard.py` `chain_paths` (+ driven in `_run`); `tools/chain_response_probe.py fresh` drives
  the same paths (GET twice: store, then the served hit).
- Tests: `backend/tests/test_ch5b_why.py` (43 pass), `test_ch5b_why_postgres.py` (1 pass, 424 s),
  `test_out_b2_vocabulary.py` (why copy added; passes).

## Evidence so far

- Scoped: test_ch5b_why, test_out_b2_vocabulary, test_ch5a2_contract, test_ch5a2_refs, test_ch5a2b_claims,
  test_out_b4_route, test_ch5c_store_off, test_ch5c_env_parity, test_ch5c2_clock_guard, test_out_b4_main_binding,
  test_out_b4_imports, tools/checks/test_chain_coherence.py: 307 passed (before the threads_through commit;
  test_ch5b_why + test_ch5a2_contract 67 passed after it).
- Non-vacuity: composing before the 304 -> the 5 route 304 tests fail; a thread node with `ids: []` -> 9 fail.
  Guard V caught "load" in the ruled "Critical load served" (natural failure).
- L2m (`var/ch5b2_why_postgres.json`): `why_trace_ms` median 10.01 ms (runs 17.34, 8.54, 10.01, 8.7, 11.17), D4 and
  D11 Findings reached, ACT-K1 node `verification: REASSESSMENT_PENDING`; 304 on all five routes with no compose
  scope; store statements after admission = watermark, Site set, (estate: per-Site admission reads), one lookup;
  after `late_fill(D7)` + drain + derive + settle the Kobo tag changes. Q8 unmatched on Kobo D13 cost: 3 (the
  board's Unknown cost row has no issues/in_hand items).
- Mechanism template rebuilt twice (my main.py/chain_api.py edits stale it): now `assetops_mechanism_tpl_c72eeed0_test`
  (+ the older `..._df73aa8a_test`); I dropped `db4dbb60` (by the build's prune) and my own stale `e4a9f130`.
  ANY further edit to main.py, outcome_api.py, chain_api.py or site_outcomes/read.py restales it (~25 min rebuild,
  three `--resume` runs at `--budget 560`). Edits under `B/chain/` do not.

## Next (in order)

1. Clone: `python tools/chain_clone.py create ch5b2 --migrate`, `settle ch5b2`; W6:
   `python tools/chain_watermark_guard.py --database-url <clone url> --work <dir> --modules-out var/w6-modules.json`
   (expect 0 violations; unlisted modules will include `assetops_backend.chain.why` and `assetops_backend.chain_api`:
   add them to `config/chain/stored-composer-modules-v1.json` as a reviewed diff, rerun to 0); then
   `python tools/chain_response_probe.py --database-url <url> --work <dir> fresh` (store on); then `drop ch5b2`.
2. Guards one at a time (10-min cap, `ASSETOPS_GUARD_PYTHON`): A (`tools/check-architecture.ps1`), W
   (`tools/check-agent-workflow.ps1`), N (navigation truthfulness), V (`test_out_b2_vocabulary.py`), M (mock deviation
   labels mjs), L, D (per plan §4.3), and the CH-5b1 checks if merged.
3. Packet `.agent/review-packet-CH-5b2.md` with Known Deviations:
   - KD-1 Q5 interim: EV Grow (and any category with no thread) has no measure line; owner CH-6a1.
   - KD-2 Q7: no " × declared price" suffix; owner CH-6.
   - KD-3 `critical_served` label "Critical supply served", not the ruled "Critical load served": guard V forbids
     "load"; Architect to confirm.
   - KD-4 estate `say` uses `why.estate.say`: the estate chain carries no per-category Portfolio headline
     (`B/site_outcomes/read.py` summary `categories` has none; `chain_api.py` estate rows carry state/state_label
     only); MOCK DEVIATION. Estate `evidence_label` is null.
   - KD-5 the 304 also runs the route's admission and the store's Site-set read (estate: per-Site admission), not
     the watermark alone; no compose read.
   - KD-6 the trace walks thread history through the window (`threads_through`), not only in-window threads.
   - KD-7 Cold-tag-unchanged half of the late_fill check is not on L2m (the mechanism DB has only KOBO-001); covered
     by CH-5c `test_ch5c_watermark_postgres` (`..._not_on_another_site`, `..._flip_only_their_site`).
   - KD-8 a one-day NOT_EXPECTED window reads "0 of 0 days checked" (no ruled one-day copy).
   - MOCK DEVIATION list mock -> new per §2.3 (WHY lines at `frontend/mockups/v70/index.html:430`).
   - `why_trace_ms` = trace_facts + why.trace only (shared Site chain reads excluded); `measured_by` left to the
     second of CH-5b1/CH-5b2 to merge.
4. Status/CODE_STATE/ACTIVE_CONTEXT per the standing brief; commit with `git add -f .agent/...`.
