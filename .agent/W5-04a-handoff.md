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
