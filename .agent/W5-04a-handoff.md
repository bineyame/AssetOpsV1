# W5-04a V1a/V1b handoff - PARTIAL (V1a schema/port landed; V1a service use and V1b blocked on Q1-Q4)

Branch `task/W5-04a-ev-work-backend` from main `f7761b28`. Backend only; no frontend/routes/nav/registry.
`main.py` unchanged. Questions: `.agent/W5-04a-questions.md` (Q1-Q5). Merge gate: readiness ruling 1 (after K4/K5
merge, rebase shared tests, rerun).

## Commits
- `7e68c38d` V1a: 0035, closed domain dispatch, EV read ports, EV case-link selection, head assertions, questions.
- `8c942778` V1a: test fix (session revision -> root map; no Foundation store dispose).

## Landed (V1a)
- `backend/migrations/versions/0035_w5_ev_work.py`: parent `0034_w5_ev_scenarios`. Discovers the generated cold
  CHECK via `pg_constraint` (`conrelid=domain_action`, `contype='c'`, `pg_get_constraintdef = CHECK ((domain =
  'COLDCHAIN'::text))`), requires exactly one, drops it by its found name, adds named `domain_action_domain_chk IN
  ('COLDCHAIN','EV_CHARGING')`; widens `domain_action_intent_criteria_count_chk` to array + length IN (3,4).
  Downgrade: `LOCK TABLE domain_action_case_link, domain_action_intent, domain_action IN ACCESS EXCLUSIVE MODE`,
  refuses `Downgrade of 0035_w5_ev_work refused: EV domain Action rows exist.` when an EV root exists, then restores
  named cold-only `domain_action_domain_chk` and the `= 4` count check. No index added.
- `work/domain_action.py`: `EV_DOMAIN/EV_FINDING_DOMAIN/EV_CRITERIA/EV_MESSAGES`, neutral literals
  `NEUTRAL_DOMAIN_INVALID` / `NEUTRAL_LINK_INVALID` (defined, not yet used), frozen `DomainSpec`
  (domain, finding_domain, criteria, summary, initial_results, messages, basis_keys, `refuse(code)`), closed
  `DOMAINS`, `BY_FINDING_DOMAIN`, `spec_of()`. Cold module aliases (`DOMAIN`, `CRITERIA`, `MESSAGES`) unchanged.
- `work/domain_action_index.py`: `INITIAL_RESULTS`/`CRITERION_SUMMARY` now derived from `DOMAINS` (cold values
  identical; EV summary entry added). Index/detail logic otherwise unchanged (still cold-only `_Lineage`).
- `work/adapters/postgres_work_read.py`: `LinkReadPorts.ev_sessions/ev_findings/ev_selected_provenance`
  (optional); `_DOMAIN_LINKS` selects `a.domain AS action_domain`; `link_selections` maps it through
  `_FINDING_DOMAIN_OF` (from `DOMAINS`) instead of hard-coded `cold_chain` (ruling 12; fallback domain from the row).
- `work/composition.py`: binds the three EV ports from the one `build_ev_read_service(None)`; new
  `selected_ev_basis(ports)` -> `basis_of(c,t,s,code,pin,known_at,finding_revision_id)` re-selects
  `ev_snapshot` with the pin's window/evidence cutoff/seqs at `known_at`, returns state, window, assessment revision,
  the exact SUPPORTED Finding (`session_id`, lifecycle, citation set = its `source_provenance.evidence_ids`),
  `sessions` {`ev_session.id` -> `ev_session_revision.id`} and `selected_evidence_ids`; None when unselected;
  `EvReadUnavailable` -> `WorkStoreUnavailable` (503). No validation in it.
- Head assertions (ruling 2 grep, recorded before edit): updated current-head literals to `0035_w5_ev_work` in
  `mini_depth_probe.py`, `test_s1_bindings`, `test_s2_evidence_ledger`, `test_s405_publication`,
  `test_s4_evidence_consequence_work` (x2), `test_s4_consequence_store`, `test_w200_source_events` (x3),
  `test_w201_cold_foundation` (x2), `test_w203/w204/w205a/w206/w401/w402` `HEAD`, `test_w207` `UPGRADED_HEAD`,
  `test_w403/w501` `LATEST_HEAD`, `test_w502_domain_intent_postgres` `HEAD`. `test_w503_ev_scenarios_postgres`:
  split into `MIGRATION = 0034` (its `down_revision == 0033` chain kept) and `HEAD = 0035`. `pg_harness.py`
  unchanged; `test_w501` 0033->0032 chain lines untouched.
- `test_w502_domain_intent_postgres.py` (K4 collision): only two hunks mid-file - `HEAD` constant and the raw
  count-check rejection now uses two criteria (`three` -> `two`). Nothing appended at the end, where K4 appends.
- New `backend/tests/test_w504_ev_intent_postgres.py` (6 tests): sole head + `0035->0034->0033`, actual check
  names/defs, index set unchanged + EXPLAIN uses `domain_action_site_raised`; closed dispatch; raw DB MINIGRID
  refused by named check, counts 0/2/5 refused, 3/4 accepted; downgrade refused for EV root alone, root+intent,
  root+link (separately), then empty downgrade restores cold-only checks and re-upgrades; `selected_ev_basis` on the
  `interrupted` replay (citations = exact revision evidence, Finding's own session selected, roots vs revisions
  distinct and matching `ev_session_revision`, unselected revision not substituted); EV case link visible in
  `revision_links`/`link_selections` with `ev_charging` domain and a real EV pin.

## Runs
- Postgres, private base `assetops_w504a_test` (harness run-owned clones, -n 4):
  `test_w504_ev_intent_postgres.py` + `test_w502_domain_intent_postgres.py` at 7e68c38d: 13 passed, 2 failed (test
  bugs, fixed in 8c942778); `test_w504_ev_intent_postgres.py` at 8c942778: **6 passed**. The cold w502 Postgres
  file passed 9/9 at 7e68c38d (unchanged since). Base DB dropped afterwards.
- Non-vacuous proof: `_FINDING_DOMAIN_OF` reverted to cold-only -> `test_domain_dispatch_is_closed` and
  `test_ev_case_link_is_visible_in_w4_selection` FAILED; reverted with `git checkout`, tree clean.
- DB-free: `test_w502_domain_intent_model.py` 7 passed. `tools/check-all.ps1`: All 11 guards passed (rc 0).
- NOT run (held per coordinator: full suite running elsewhere): the other updated head-assertion files, adjacent
  EV files (`test_w503_*`, `test_w206_ev_reads`), w502 API/index/links Postgres files, `writer_guard_probes.py`
  (no writer or guard rule changed, so likely not required). Run these in the batch.

## Judgment calls
1. Ruling 2 HEAD constants: treated every grep hit used as "current DB/script head" as current-head; only w503 also
   used HEAD as the migration-under-test, so it was split.
2. Dispatch table lives in `domain_action.py`; the read adapter derives its map from it (import of a pure
   `work/` module, same as its existing `link_coverage` import; check-all passes).
3. `selected_ev_basis` returns raw selected material and validates nothing, so the Q1/Q4 answers only touch the
   service. "Selected accepted set" is returned as the head's `selected.evidence_ids` pending Q4.
4. Downgrade restores the exact `= 4` count check (symmetry with 0033); a raw cold 3-criteria row would make the
   downgrade fail, which the service never writes.
5. EV fixture is `ev_depth_cases.settled(chain, "interrupted")` (has a SUPPORTED Finding), not the producer.

## Next (after Architect answers Q1-Q4)
- V1a remainder / V1b: `domain_intent.py` dispatch by `spec_of` (create: Site-type check via a new `tx.site_type()`,
  Finding domain, SUPPORTED lifecycle; intent: per-domain criteria/basis inside the tx, EV session/citation
  membership via `selected_ev_basis`, no intersection, zero writes), `postgres_domain_intent.py` (inject
  `ev_basis_of`; `build_domain_intent_store` passes `selected_ev_basis(ports)`), `domain_action_index.py` detail/
  `_Lineage` by domain (EV: no cold envelope; PENDING results; session revision IDs into provenance; 409 basis
  changed on recheck), EV model/API tests, cold neutral-refusal tests, then producer/walkthrough (Q3, Q5).

---

# Round 2 - V1a service + V1b read landed (producer/walkthrough NOT built)

Builder brief: service and read code only, per readiness 27/28/30 (+5-7, 9-12, 16, 18). Producer, walkthrough and K0
(rulings 29/31) remain open for the next V1b step.

## Commits
- `bd791c44` questions Q6-Q7 appended to `.agent/W5-04a-questions.md`.
- `638d6677` service/read code + DB-free EV model tests + cold model/API literal updates.
- `eb73236b` EV Postgres + API tests (held, not run).

## Landed
- `work/domain_action.py`: `NEUTRAL_LINK_INVALID` removed; `NEUTRAL_INTENT_INVALID` / `NEUTRAL_CASE_LINK_INVALID`
  added. Parsers raise `_Malformed` (a cold-literal `DomainIntentRefused` subclass) re-typed per stage via `_as`.
  `action_body`: missing/unknown domain -> neutral domain literal, else that domain's literal. `intent_shape` (shared
  pre-resolution: closed top level, instants, key, criteria = list of closed text triples, basis = all shared keys,
  only keys some domain allows) -> neutral; `intent_for(spec, shape)` -> exact criteria/basis keys, EV `session_ids`
  nonempty distinct sorted UUIDs, domain literal. `intent_body(body, domain=COLD)` kept for callers. `case_link_body`
  -> neutral case-link literal. Pure `ev_selects_finding` / `ev_members_selected` (sets A, B, Finding citations,
  own session, case-normalized, no intersection). Cold normalized output (and so cold hashes) unchanged.
- `work/domain_intent.py`: dispatch by declared (create) / stored (intent, link) domain; stored unknown -> 503.
  Create in tx: idempotency, window, `tx.site_type() == domain`, Finding revision domain, pin at `command_now`, EV
  SUPPORTED exact Finding via `tx.selected_ev_basis`. Intent: 404 then `intent_for` then hash/idempotency, window,
  basis (EV: pin, exact selected Finding, case/record checks, `ev_members_selected`; cold unchanged). Case link: 404
  then domain literals. Actor shape failure uses the stage literal.
- `adapters/postgres_domain_intent.py`: `site_type()`, `selected_ev_basis(pin, revision_id)`, optional
  `ev_basis_of` ctor arg. Still the sole writer; no rule-8 change.
- `adapters/postgres_work_read.py`: `LinkReadPorts.ev_accepted`; `composition.py` binds `ev_read.accepted_on`,
  `selected_ev_basis` returns `accepted_evidence_ids` (set A, lowercased), both builders inject `selected_ev_basis`.
- `domain_action_index.py` / `adapters/postgres_domain_action_index.py`: `_Lineage`, `_summary`, `_source_state`
  by row domain (cold byte-identical); EV detail `_ev_detail`: cutoff = intent `recorded_at` (bounded by `known_at`)
  or `known_at`; recheck via `_ev_selection` + `ev_members_selected`; with intent any miss -> 409 EV basis-changed;
  status = `link_state` of the selected EV state, HISTORICAL rule as cold; three PENDING results; selected
  `ev_session_revision` IDs of declared sessions in provenance selected IDs. `_IndexTx.ev_basis`, reader `ev_basis_of`.

## DB-free / guards (at `eb73236b`)
- `pytest tests/test_w504_ev_intent_model.py tests/test_w502_domain_intent_model.py tests/test_w504_ev_intent_api.py
  tests/test_w504_ev_intent_postgres.py`: **16 passed, 13 skipped** (skips = no DB URL).
- Non-vacuous: removing the set-B check failed 2 EV model tests; removing the Site-type check failed 1; both reverted
  with `git checkout`, tree clean.
- `tools/check-all.ps1`: **All 11 guards passed**. `ruff --select F,E9` clean on all touched files.
- Pre-existing (base `31b65d2b` too): `test_w502_domain_intent_api.py` fails collection without a DB URL
  (`NameError: COLD`); unaffected when the URL is set.

## Held Postgres batch (run together, one private `*_test` base)
1. `backend/tests/test_w504_ev_intent_postgres.py` (all 11; 5 new: round trip/detail, create refusals,
   refusal order + membership, immutable pin, no-intent UNKNOWN).
2. `backend/tests/test_w504_ev_intent_api.py` (2).
3. Cold regression: `test_w502_domain_intent_postgres.py`, `test_w502_domain_intent_api.py`,
   `test_w502_domain_action_index_postgres.py`, `test_w502_domain_action_index_api.py`,
   `test_w502_domain_work_links_postgres.py`, `test_w502_cold_scenario_producer.py`.
4. Still pending from round 1: updated head-assertion files, `test_w503_*`, `test_w206_ev_reads*`.
Most likely to need adjustment (written blind against replay behaviour): `test_ev_pin_is_immutable_across_later_
evidence_and_heads` (`add_import` + `run_worker` + `select_exact` after the intent; asserts ruled 200/unchanged basis)
and the HISTORICAL status assertions in it. A failure there is either a test fixture issue or a real ruling-27 gap.

## Judgment calls
1. Q6 (not decided): the pin keeps the merged unfiltered `max(decided_at)` evidence cutoff via `selected_finding_pin`.
2. Q7 (recorded): EV detail with no intent and an unselected Finding -> 200 UNKNOWN / null href / missing lineage.
3. Shared pre-resolution criteria shape = list of closed string triples (any length); count is domain-specific.
   EV `session_ids` value is parsed only after resolution (raw before), so a malformed value on an unknown Action is
   404.
4. EV selection token uses the unchanged `selection_token` (no session IDs in it): K1 wire unchanged.
5. Intent write requires the exact Finding revision SUPPORTED at `command_now` (same helper as create); EV write
   uses the Finding citation set, not `tx.cited_evidence`.
6. Membership sets made non-empty in Postgres by perturbing one set of the real basis (`perturbed`), plus foreign
   uuid4 IDs; the real valid set is asserted non-empty.

---

# Round 3 (producer) - library, CLI and K0 tests landed; the shifted replay is BLOCKED (Q8-Q10)

## Commits
- `8ec98969` `tools/w504_ev_work_cases.py`, `tools/w504_ev_work_walkthrough.py`, DB-free `backend/tests/test_w504_ev_work_cases.py`.
- `f553118d` appended section in `backend/tests/test_w504_ev_intent_api.py` (2 Postgres tests; the two earlier tests untouched).
- `77c82369` questions Q8-Q12 in `.agent/W5-04a-questions.md`.

## Landed
- Library (no `backend/tests` import; AST-guarded by a test): R/D/delta and `[D+08:00,D+09:00)`; shifted scenario
  document (window, `forcing[].time`, `observations[].time/release_at`) and Site document (code
  `EV-W504-DEPOT-{suffix}`, `Depot Charging Hub`, `Etc/UTC`, Foundation `valid_from/valid_to` shifted, components
  unchanged, no subtitle; short name manifest-only, Q12); `cross_check_k0` / `select_positive` / `read_k0` (ruling 29:
  scenarios + sessions without `known_at`, findings at the returned K0, refusal on null K0, unequal bounds or clocks,
  or a Finding/session not in that window); exact Action/intent/INC/WR/record/case-link bodies; `evidence_clock_for`
  (ruling 21). `replay_shifted` raises `ProducerBlocked` (Q9 parser pin, then Q10 test-only runner).
- CLI `prepare|serve|attest|drop`: private `w504a_<mode>_<tag>_test` DBs (`positive`, `zero`, `pending`, `stale`,
  `unknown`), product Alembic upgrade, per-mode child (`DATABASE_URL`) that runs replay -> K0 -> Action/intent via
  the public domain-work routes (zero mode asserts complete-zero W4 reads); `attest` posts INC/WR/record via a W4
  router with the SERVICE principal, then explicit case links, K3 (case `event.recorded_at`, record `recorded_at`),
  K4 (link `recorded_at`); 403 via a `forbidden` process granted no Site; 503 by `taskkill /PID` of only the recorded
  `unavailable` PID; `drop` kills recorded PIDs only and drops only marker-listed `w504a_*_test` DBs. On merged code
  `prepare` records `blocked`/`unavailable` with the reason and exits 3.

## DB-free / guards (at `77c82369`)
- `test_w504_ev_work_cases.py` 16 passed; with `test_w504_ev_intent_api.py`, `test_w504_ev_intent_model.py`,
  `test_w502_domain_intent_model.py`: **32 passed, 4 skipped** (skips = no DB URL).
- Non-vacuous: removing the `known_at == K0` check failed 3 tests; adding a `test_w205b` import to the library failed
  the import guard; both reverted with `git checkout`, tree clean.
- `tools/check-all.ps1`: **All 11 guards passed** (rc 0). `ruff --select F,E9` clean on the new/changed files.

## Held Postgres batch (add to round 2's list)
5. `backend/tests/test_w504_ev_intent_api.py::test_producer_k0_route_shape_and_positive_payloads` and
   `::test_producer_refuses_mismatched_window_or_clock` (over the `interrupted` replay). Most likely to need
   adjustment: `accepted_evidence_ids <= valid` (assumes the sessions `selected_source_provenance.evidence_ids` is
   within A and B) and the earlier-`known_at` sessions read status set.

## Manual walkthrough (later, idle machine; only after Q8-Q10 are answered)
    .venv\Scripts\python.exe tools\w504_ev_work_walkthrough.py --work var/w504a_ev_work --tag k1 prepare
    .venv\Scripts\python.exe tools\w504_ev_work_walkthrough.py --work var/w504a_ev_work --tag k1 serve
    .venv\Scripts\python.exe tools\w504_ev_work_walkthrough.py --work var/w504a_ev_work --tag k1 attest
    .venv\Scripts\python.exe tools\w504_ev_work_walkthrough.py --work var/w504a_ev_work --tag k1 drop
Today `prepare` creates the five DBs, writes `blocked` modes and exits 3; run `drop` afterwards. Never run.

## Judgment calls
1. Not decided: positive scenario (Q8), the replay path (Q9/Q10). `replay_shifted` is the single seam to replace.
2. Declared evidence = Finding citations ∩ sessions `selected_source_provenance.evidence_ids`; the server re-checks A.
3. INC/WR asset = selected session `connector_asset_id` (returned); `finding_links: []` on both (spec silent).
4. WR narrative provisional (Q11). Separate `positive` and `zero` DBs so mock-zero stays zero after `attest`.
5. The walkthrough runs from the repo tree (records `git rev-parse HEAD` and dirty flag), not a `git archive` copy.

---

# Round 4 (V1b producer rebuilt per rulings 32-38) - ready positive and mock-zero manifests

## Commits
- `f5f44f79` producer: `tools/w504_ev_work_cases.py` (shifted Site/documents, `ProducerBlocked`, `WR_NARRATIVE_PENDING_RULING`
  deleted; `E_START/E_END`, `work_window`, `bounded_work_window`, `clock_order`, `listed_ids`, DB-time `action_body`
  check, `submitted_case_times(db_now)`); `tools/w504_ev_work_walkthrough.py` (child `native_replay`; `_declare`,
  `_unknown`, `_attest` rewritten); DB-free `backend/tests/test_w504_ev_work_cases.py` rewritten (16 tests); new
  Postgres fixture test `backend/tests/test_w504_ev_work_producer_postgres.py` (3 tests).
- `0d7cbfba` B: `test_producer_k0_route_shape_and_positive_payloads` asserts the literals on the posted body, the
  stored `domain_action`/`domain_action_intent` row and the GET detail; K1/intent response key sets asserted exactly;
  raised_at = DB now.
- `0ef0b17a` C: `test_rejected_disposition_advances_the_shared_cutoff_without_accepted_evidence` (ruling 32).
  Ruling 33 was already covered by `test_ev_detail_without_intent_and_unselected_finding_is_unknown` and
  `test_ev_pin_is_immutable_across_later_evidence_and_heads`; nothing added there. `test_w502_*` untouched.

## Landed
- Native path (ruling 36): `native_replay` (walkthrough child only) adds `backend/tests`, `host`, `host/tests`,
  `gateway/tests` to `sys.path` and imports `test_w205b_ev_replay_postgres` (Chain, CASES, EV, WINDOW) and
  `test_w206_ev_store_postgres` (run_worker, select_exact); asserts EV-LAB-001, E, the registered case, ACCEPTED
  dispositions; closes the Chain and refuses if the gateway PID survives. No `hold_uuids` (no fixed UUIDs). The
  child gets `ASSETOPS_TEST_DATABASE_URL` = its private DB (`Walk.env(replay=True)`).
- K0 from `/ev/financials/scenarios` cross-checked with `/ev/sessions` over E; Action `raised_at` = DB now; W from
  the DB day; Action listed in the domain-work index over W; zero mode W4 reads over W complete zero. Attest posts
  INC/WR/record at DB now - 3/2/1 min, reads back the WR narrative from `work_case_revision`, enforces
  `clock_order`, recomputes W only if needed, and asserts Action/INC/WR in the three W lists.
- DB modes are now `positive`, `zero`, `unknown`; `pending`/`stale` are manifest-only `unavailable` (no DB).
- Guards: library AST no-test-import kept; new test pins the walkthrough's test imports to exactly the two modules
  inside `native_replay` and forbids `decision_clock`/`FIRST_DECISION` names. Non-vacuous: an extra
  `ev_depth_cases` import in the walkthrough and a disabled K0 check each failed a test; reverted with `git checkout`.

## Runs
- Focused Postgres at `0ef0b17a`, base `assetops_w504a_test`, from `backend`: `-m pytest
  tests/test_w504_ev_intent_postgres.py tests/test_w504_ev_intent_api.py tests/test_w504_ev_work_cases.py
  tests/test_w504_ev_intent_model.py tests/test_w504_ev_work_producer_postgres.py -n 4 -q -p no:cacheprovider`:
  **44 passed, 0 skipped, 0 failed**, 273 s (275 s wall). Includes `test_ev_action_and_intent_round_trip_with_detail`
  (coordinator fix confirmed) and the fixed B test.
- C subagent (private `assetops_w504a_c_test`, dropped): focused 1 passed (36 s); mutation `AND decision='ACCEPTED'`
  in `postgres_work_read._cold_ev` failed it (restored); whole file `-n 2` 12 passed (3m13s).
- `tools/check-all.ps1`: **All 11 guards passed**, rc 0.

## Walkthrough (`--work var/w504a_ev_work --tag k1`, revision `0ef0b17a`, clean tree)
- `prepare` rc 0 (160 s): positive ready, zero ready, unknown unavailable ("the replay selected 0 SUPPORTED EV
  Findings, so no Action detail state"), pending/stale unavailable. `serve` (26 s): positive 21468:8981,
  zero 15336:8982, forbidden 18596:8986, unavailable 23968:8987, all healthy. `attest` (10 s): forbidden 403
  `SITE_SCOPE_FORBIDDEN`; unavailable PID 23968 stopped, connection refused.
- Manifest copy: `.agent/W5-04a-round4-walkthrough-manifest.json` (the work-folder original is removed by drop).
  Site EV-LAB-001 'EV charging lab' Etc/UTC (Depot manifest-only); replay run `run-54a3a919...`, 221 ACCEPTED.
  E=[2026-10-06T08:00Z,09:00Z); W=[2026-10-24T00:00Z,2026-10-25T00:00Z) not recomputed.
  Finding 083858da / rev 38929ef8, session 5e6fbef5, connector asset ac210564, 3 accepted evidence IDs.
  Action ACT-000001 402a32bc (detail CURRENT), intent 295ea341; INC-000001 1797b636, WR-000002 f9771c43,
  record d75110ec. K0=2026-10-06T09:00:00Z, K1=2026-10-24T03:52:03.028022Z, K2=03:52:03.393151Z,
  K3=03:54:31.483297/.622413/.704047Z, K4=03:54:32.157431/.258383Z. Zero: Action 8602db6f, 0 incidents, 0 maintenance.
- `drop`: stopped the 3 live recorded PIDs, dropped the 3 `w504a_*_k1_test` DBs, removed the work folder; all four
  PIDs absent from `tasklist`. Base `assetops_w504a_test` dropped last; the `LIKE '%w504a%'` query returns nothing.

## Judgment calls
1. Ruling-36 "fixture test" = in-process Postgres tests of the child functions (`native_replay`, `_declare`,
   `_attest`) plus `Walk.drop` on a throwaway DB and a sleeper PID, not a subprocess CLI run.
2. Unknown vector: `ev-missing-meter` selects no SUPPORTED Finding, so no Action detail state can be read; recorded
   unavailable (ruling 34). pending/stale get no DB (no unmodified replay produces them).
3. Maintenance `created_at` and the case event IDs are read from `work_case`/`work_event` (read-only), as W5-02 did;
   the case command response carries no `created_at`.
4. Work URLs in the manifest carry W as `from`/`to` (the detail API itself takes only `known_at`).
5. No questions raised; nothing contradicted the merged code.
