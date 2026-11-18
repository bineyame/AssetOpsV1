# W5-04a backend review: V1a and V1b

Independent Reviewer, 2026-10-24. Branch `task/W5-04a-ev-work-backend`, builder head `71e5cdc9`. Diff
`f7761b28..71e5cdc9`, read for `backend/`, `tools/w504*` and the tests. The `tools/checks/*`, `tools/w502*` and K5
hunks in that range come from the main merges (`1429a547`, `27b3a003`), not from the builder. I judged the work
against `.agent/W5-04-build-spec.md` (V1a/V1b), readiness rulings 1-12 and 27-38, the pre-flight rulings, the W5-03b E5
rulings (A6) and W5-02's cold rulings. I treated the handoff (rounds 1-4), the questions and the manifest as claims
to verify. I did not edit review6 and fixed nothing.

## Verdicts

| Unit | Verdict | High | Medium | Low |
| --- | --- | --- | --- | --- |
| **V1a**: 0035, closed dispatch, EV ports, selected EV basis, head pins, EV case-link visibility | **ACCEPT** | 0 | 0 | 1 |
| **V1b**: EV intent/case-link service, detail and index, producer and walkthrough | **ACCEPT** | 0 | 0 | 5 |

None of the findings blocks a merge. The merge gate from readiness ruling 1 still applies: the rebased shared tests
have to be rerun, and the full suite now running on review6 has to pass on the merged revision.

## Checks run (by me, at 71e5cdc9)

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. `tools/check-all.ps1`: all 11
  guards passed.
- DB-free tests: `test_w504_ev_intent_model.py`, `test_w502_domain_intent_model.py` and `test_w504_ev_work_cases.py`
  gave **32 passed**.
- Postgres tests, on a private base DB `assetops_w504rv_test` (created, then dropped; no harness clone is left),
  PYTHONPATH set to review6 backend/contracts/gateway/host/simulator/backend/tests, `-n 2`: `test_w504_ev_intent_postgres.py` and `test_w504_ev_intent_api.py`
  gave **16 passed, 0 skipped, 0 failed** (JUnit tests=16, skipped=0, failures=0, errors=0), 458.5 s (7:40 wall),
  with the full suite running at the same time.
- Reviewer probe: one uncommitted test in a throwaway worktree, since deleted. It extends the immutable-pin vector
  and prints the results (used in L2 and Architect item 1). After `add_import` + `run_worker` + `select_exact`, the
  old revision's pin at read-now is `None`, so the test's "later selected head" is real. The EV detail with an
  intent then reads `CURRENT` with a live Finding href. The index row for the same Action reads origin
  `href: null` and index `status: UNKNOWN`. Between `add_import` and `run_worker`, the intent-bearing detail read
  `PENDING_RECOMPUTE`.
- Guard non-vacuity, re-proved: I added `import scenario_cache` to the walkthrough top level and a `test_w206` import
  to the library. Both `test_producer_imports_no_test_module` and
  `test_walkthrough_test_imports_are_only_the_native_replay_child` failed. I reverted the change and the tree was
  clean.
- Not run by me: the cold w502 Postgres/API/index/links files, the adjacent EV files (`test_w503_*`,
  `test_w206_ev_reads*`), the other files with updated head assertions, `test_w504_ev_work_producer_postgres.py` (it
  creates `w504a_fx_*_test` DBs and a sleeper PID, and I kept to the "couple of files" constraint) and the
  walkthrough CLI. The implementer cites 44 passed at `0ef0b17a` for the five w504 files (code identical to
  `71e5cdc9`, which adds only `.agent` files). **No same-revision full-suite evidence exists in the handoff.** The
  coordinator's run on review6 is that evidence and I have not seen its result. Frontend: not touched by this slice,
  so nothing to run.

## V1a: schema, dispatch, ports, selection

Conformance verified:
- **0035.** `revision`/`down_revision` are correct, and the sole head is asserted along with `0035->0034->0033`.
  The generated CHECK is found by `conrelid`, `contype='c'` and the exact normalized
  `CHECK ((domain = 'COLDCHAIN'::text))`. Exactly one match is required, otherwise the migration raises. The actual
  name is dropped via `format('%I')`, and the named `domain_action_domain_chk IN ('COLDCHAIN','EV_CHARGING')` is
  added. The count CHECK is widened with `jsonb_typeof='array'` kept and `IN (3,4)`.
- **Downgrade.** It locks `domain_action_case_link, domain_action_intent, domain_action` in ACCESS EXCLUSIVE mode,
  child first, before the guard. It refuses with the exact period-terminated literal, then restores the named
  cold-only CHECK and `= 4`. `env.py` runs one transaction, so a refused multi-step downgrade rolls back whole. Tests
  cover root alone, root+intent and root+link separately, the restored definitions, re-upgrade, raw counts 0/2/5
  refused and 3/4 accepted, MINIGRID refused by the named CHECK, an unchanged index set, and the EXPLAIN plan on
  `domain_action_site_raised`.
- **Head pins.** No current-head `0034` literal remains under `backend/tests`, `host/tests` or `gateway/tests`.
  `mini_depth_probe.py` is updated. `test_w503` splits `MIGRATION`/`HEAD` and keeps `0034->0033`.
- **`DOMAINS`, `spec_of` and `BY_FINDING_DOMAIN`.** The dispatch is closed. `_domain_links` selects
  `a.domain AS action_domain` and maps it through `_FINDING_DOMAIN_OF`, with no hard-coded `cold_chain` (ruling 12).
- **`LinkReadPorts`.** `ev_sessions/ev_findings/ev_selected_provenance/ev_accepted` are bound in `composition.py`.
  `selected_ev_basis` re-selects `ev_snapshot` on the caller connection, using the pin's exact window, the evidence
  cutoff and seqs, and the selection cutoff. It returns sessions as `ev_session.id -> ev_session_revision.id`,
  set A from `accepted_on`, set B from `selected.evidence_ids`, and the Finding citations from
  `source_provenance.evidence_ids`. `EvReadUnavailable` becomes the work 503. It does no validation.
- **Imports.** No analytics import exists in `work/adapters/*`; the lazy `EvReadUnavailable` import sits in
  `composition.py`, which already imports analytics builders. `postgres_domain_intent.py` remains the only file with
  `INSERT INTO domain_action*`.

Findings: see L5. It is shared with V1b because the ruling-32 vector exercises the V1a selector.

## V1b: commands, read, producer

Conformance verified:
- **Ruling 28 order.** The SERVICE gate comes first. Then `intent_shape` / `case_link_body` / the actor shape run
  with the **neutral** literals: the parsers raise `_Malformed`, which is re-typed per stage, so no cold literal
  escapes before resolution. Then the W4 actor authorization. Then, inside one transaction, the scoped Action (404,
  including a malformed path ID), followed by `intent_for(stored spec)` with that domain's literal. Membership and
  link refusals then use the domain literal, and conflicts or basis changes use the domain 409 literals. Creation
  gives a neutral domain literal for a missing or unknown domain and the declared domain's literal otherwise. The
  Site-type check (`tx.site_type() != spec.domain`) runs before any Finding read or write.
- **Cold behaviour changes.** These are exactly what rulings 11 and 28 require, and nothing else changed:
  (a) a pre-resolution shape or actor failure is neutral; (b) a cold count/order/triple failure, or a basis
  key-set failure (including an EV-only `session_ids` key), is now 404 on an unknown Action and the cold literal on
  a resolved one; (c) cold creation refuses a non-COLDCHAIN Site (`site_type` is upper-case per 0001's CHECK);
  (d) a stored domain outside `DOMAINS` is 503 (unreachable under the CHECK). The cold normalized body, and
  therefore its hash, is unchanged; the hash is now computed after resolution with the same value. The cold detail
  is untouched apart from the EV branch, and cold index summaries and states are byte-identical. The updated cold
  tests (`test_w502_domain_intent_model.py`, `_api.py`) move only the literals that ruling 28 makes neutral. They
  keep every rejection vector, which moved rather than being dropped (MINIGRID moved to the neutral set), and they
  add the resolved-cold three-criterion (422 cold), unknown-Action (404) and neutral-shape vectors with zero writes.
- **EV membership.** `ev_members_selected` requires declared sessions to be a subset of the selected roots,
  including the Finding's own session. It requires declared evidence to be a subset of A, of B and of the exact
  Finding citations, compared case-insensitively. There is no intersection, and the stored basis is the declared
  sorted list. `ev_selects_finding` requires the exact revision and `SUPPORTED`. Creation and intent both re-check
  the Finding at `command_now`. Postgres perturbation vectors make each of the three sets, and the own-session
  rule, fail independently, and the real valid set is asserted non-empty.
- **EV detail.** The cutoff is `min(intent.recorded_at, known_at)`, or `known_at` without an intent (ruling 33).
  With an intent, any miss gives 409 `DOMAIN_INTENT_BASIS_CHANGED` with the EV literal. Results are three
  `PENDING` rows with empty evidence. Selected `ev_session_revision` IDs, not roots, go into the provenance
  selected IDs (the test pins `basis_sha256` with the revision and checks it differs with the root). A refused
  read carries `intent:null,results:null` through the unchanged `domain_work_api.py`.
- **Index.** The EV summary is used only for the exact three keys. State is `OPEN`, and the source state comes
  from the row's mapped Finding domain.
- **Producer.** `native_replay` is the only place with test imports (AST-pinned to exactly two modules inside it).
  It asserts EV-LAB-001, the registered E window, the case and ACCEPTED dispositions, and refuses if the gateway
  PID survives. K0 is the scenarios `committed_watermark`, cross-checked against equal bounds and
  `sessions.known_at`, with no `known_at` sent on either read; the Finding is then read at the returned K0 over the
  same window. Action `raised_at` is DB now. `clock_order` enforces `K0 < K1 <= K2 <= K3 <= K4`. W is the DB day
  and is recomputed only within the 31-day bound. The WR narrative is posted and read back as the ruling-37
  literal. `Depot` is manifest-only. The 403 comes from a real gateless grant. The 503 path `taskkill`s only the
  recorded `unavailable` PID, and `drop` touches only recorded PIDs and marker-listed `w504a_*_test` names.
- **The two test fixes do not weaken anything.** (1) `a569b9cc`: `raised_at` is in the canonical command hash,
  so the earlier retry built a *different* body and could never be an identical retry. Reusing one body is what
  the 201/200 contract describes. (2) `0d7cbfba`: the K1 Action and intent command responses really carry only
  `{schema_version,id,action_code,recorded_at}` and `{schema_version,intent_id,action_id,recorded_at,selection_token}`.
  The old assertions read fields that are not on that wire. The fix pins those exact key sets and moves the literal
  checks to the posted body, the stored row and the GET detail, which is stronger.
- **Unknown, pending and stale.** Ruling 34 explicitly allows `ev-missing-meter` to be recorded unavailable when
  it does not yield the state; the build spec allows the same for pending and stale ("otherwise mark browser
  capture unavailable and use a pure adapter/component vector"). All three are disclosed in the handoff and in the
  manifest `modes` with reasons. Pending and stale were not attempted, so the reasons are assertions rather than
  observations (see Architect item 2).

### Findings

**L1 (Low, test gap): the EV conflict 409 is never exercised.** `backend/assetops_backend/work/domain_intent.py:88,150,162`
raise `spec.refuse("DOMAIN_INTENT_CONFLICT")`, and the case-link basis-changed path does the same. No EV test
covers any of these: the same key with a different body, a second root intent, or a stale `supersedes_id`.
`grep "DOMAIN_INTENT_CONFLICT\|newer version" backend/tests/test_w504_*` is empty, and only the literal table is
asserted. *Why it matters:* the EV 409 literal is a ruled wire value that the UI shows. *Fix:* add one Postgres or
model vector per path, asserting `(409, DOMAIN_INTENT_CONFLICT, "This Action declaration has a newer version;
reload it.")` with zero writes.

**L2 (Low, test strength and disclosure): the "accepted disposition after the intent" vector is decided before
the intent.** `backend/tests/test_w504_ev_intent_postgres.py:486`. `add_import` (`ev_depth_cases.py:118`) clones an
ACCEPTED disposition "at the original clock", so its `decided_at` is the 2026-10-06 replay clock, earlier than the
intent's `recorded_at`. The vector therefore tests late-inserted, earlier-decided evidence. It never tests a
disposition decided after the intent cutoff, and the test asserts nothing about status or evidence cutoff after it.
My probe shows that the intent-bearing detail turns `PENDING_RECOMPUTE` in between. The ruled outcome (revision,
window and basis unchanged) holds, and the later-head step would catch a `known_at`-instead-of-`recorded_at` bug,
so this is not a correctness defect. *Fix:* add a disposition with `decided_at = clock_timestamp()` after the intent
(as the ruling-32 test does for its rejection) and assert that the detail status, token and the pin's
`evidence_cutoff` at the intent cutoff are unchanged. Label the existing vector as backdated.

**L3 (Low, acceptance-test ownership, ruling 11): cold cross-Site-type and neutral-domain refusal are not proven
against the cold Site's database.** The V1b card says V1b owns "the cold model, Postgres and API tests for neutral
invalid-domain and cross-Site-type refusal". The cross-Site-type refusal is proven in the fake-store model test
(`test_w504_ev_intent_model.py::test_create_dispatch_site_type_and_supported_finding`), which isolates the Site-type
check, and in the EV Postgres test (`test_w504_ev_intent_postgres.py:405`, cold body on the EV Site, where the
Finding-domain check would refuse anyway). No Postgres or API test posts an `EV_CHARGING` body to a **cold** Site.
`test_w502_domain_intent_api.py:133` adds no neutral-domain vector with a full otherwise-valid body.
*Fix:* add one cold-Site Postgres/API vector of each kind, with zero writes.

**L4 (Low, producer strictness): "complete zero" checks only empty rows.** `tools/w504_ev_work_cases.py:348`
`zero_reads_complete` does not assert `total_count == 0` and `next_cursor is None` on the W4 list wire
(`work/site_index.py:353-354`). In practice an empty first page implies both, but the mock-zero `Incidents (0)` /
`Maintenance (0)` counts are what the UI renders, so assert the field itself.

**L5 (Low, test scope, ruling 32): the cold half of "cold/EV exact links and W4 coverage use the same cutoff" is
not exercised.** `backend/tests/test_w504_ev_intent_postgres.py:537-621` proves the advanced cutoff on the EV pin,
the EV snapshot and the W4 linked selection of an **EV** domain Action. No cold pin or cold link is read, and W4
coverage is shown only through `link_selections[].pin.evidence_cutoff`, not through `link_coverage`. The cold and EV
paths share `_ReadTx._cold_ev` (`postgres_work_read.py:280-286`), and the builder's mutation
(`AND decision='ACCEPTED'`) failed the test, so the risk is low. The handoff does not state this limitation,
however. *Fix:* disclose it in the handoff or packet, or add one cold read in the same cutoff assertion.

**L6 (Low, residual operational risk): the walkthrough can kill a reused PID.**
`tools/w504_ev_work_walkthrough.py:551-552,569`. `drop` decides a recorded PID is alive by matching `tasklist /FI
"PID eq n"`, then runs `taskkill /T /F`. If the recorded server already exited and Windows reused the PID, an
unrelated process tree would be killed. The window is small (the PIDs are recorded minutes earlier on the same
machine), and the cold walkthrough has the same shape. *Fix (optional):* also match the image name or command line
(`python.exe` / `uvicorn serve_entry:app`) before killing.

(L1-L4 and L6 are V1b; L5 is counted under V1a.)

## Items for the Architect

1. **The EV index and EV detail disagree after a later head (not ruled).** Ruling 27 pins the EV **detail** at the
   intent's `recorded_at`. The union **index** still resolves each row at the read `known_at`
   (`domain_action_index.py:186,471`, the cold W5-02 behaviour). My probe shows that after a later selected head,
   the same EV Action reads detail `CURRENT` with a live Finding href, while its index row reads origin
   `href: null` and index `status: UNKNOWN`. Cold has no such split, because its detail also uses `known_at`.
   Decide whether the EV index row should use the intent pin (as the detail does) or whether the split is intended.
   If it is intended, the V2a UI needs a ruled copy for the Actions list showing the Finding unavailable while the
   Action detail shows it live.
2. **Pending and stale capture.** The walkthrough records `pending` and `stale` as unavailable without attempting
   them ("needs a modified replay"). The build spec defines `PENDING_RECOMPUTE` as "a late accepted event before
   W5-03 reassessment". My probe produced exactly that state on the EV detail using the backend test helper
   `add_import` before `run_worker`, which clones a disposition directly in SQL. Confirm that pending and stale stay
   limited to pure vectors, given that ruling 35 forbids a batch-ingestion bypass. Otherwise authorize a
   registered-path late event for V2b.
3. **Fixture decision clock versus the immutable pin.** Because the replay's decision clock is virtual
   (2026-10-06), any evidence added after the intent in these fixtures is decided "before" the intent's
   `recorded_at`. It then enters the intent-cutoff selection and moves the EV detail's status (L2). Production
   `decided_at` is DB time, so this is a fixture artifact. Note it for V2b/V4b captures that combine a late import
   with an intent-bearing Action.
4. **The bound `ev_selected_provenance` port is unused.** It is bound (`composition.py:60`), as ruling 5 requires,
   but `selected_ev_basis` never calls it (ruling 30 makes it optional). Either keep it for V5 or drop it from
   ruling 5's list.

## Residual risk the packet does not name

- No same-revision full backend suite is cited for `0ef0b17a`/`71e5cdc9`. The review6 run is the merge evidence.
- The 0035 "exactly one match" refusal path is untested. Only the success path runs, through the harness template
  migration.
- `test_w504_ev_work_producer_postgres.py` and the walkthrough CLI were not rerun by me. The manifest records a
  clean-tree run at `0ef0b17a` with all four PIDs absent afterwards.
