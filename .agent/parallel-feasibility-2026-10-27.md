# Can the telemetry plan and the commercial plan be built in parallel? (2026-10-27)

Architect: Claude (`.ai/ROLE_CONFIG.md` line 9, "Architect Is Claude By Default").
Owner request, verbatim: `.agent/owner-parallel-and-open-questions-2026-10-27.md`.
Plans assessed:
- Telemetry: `Docs/demo-sprint/telemetry-integration-plan-claude.html` rev 3 (TEL-00..TEL-07), with `.agent/telemetry-rulings-2026-10-27.md` (D4, D10, D5, D6).
- Commercial: `Docs/demo-sprint/commercial-capability-readiness.html` §10.3 roadmap (R1..R7), §10.6 sprint, Appendix C (D1..D5).

Code read in `AssetOpsV1-demo-plan` at 73aa42b9. `main` is 83f9f910, which merges this branch. Every post-W6 task branch is merged into main, so no in-flight slice competes with either lane. Documents only: no code, tests, databases or suites were run.

The Implementer reviews this file next. Where it disagrees, I reconcile it here.

## 1. Verdict: yes, as two lanes with one shared validation queue

The two plans can be coded in parallel. They cannot be validated in parallel.

- Their write sets are disjoint (§2). No file, module, migration or contract is written by both lanes.
- Telemetry adds a new module root plus additive checks. It changes no product code, adds no migration and no UI.
- Commercial changes backend product code, migrations 0036+, frontend panels and producers. It touches no gateway, field, contracts or `tools/checks` file.
- The real limits are three shared resources:
  - the machine: one heavy job at a time (§6);
  - the reviewers (§7);
  - one shared virtualenv whose editable installs point at a different checkout (§2.3).

If any of these is ignored, the parallel plan fails. Code conflicts are not the risk.

## 2. Overlap, checked against the code

### 2.1 Write sets

| Area | Telemetry writes | Commercial writes | Overlap |
|---|---|---|---|
| New root `field/` (`field/assetops_field/*`, `field/profiles/*`, `field/tests/*`, `field/pyproject.toml`) | Yes (TEL-01..06) | No | None |
| `tools/checks/module-roots.ps1`, `tools/checks/dependency-direction.ps1` | Additive sections (D4) | No. Appendix C: "No numbering guard exists in tools/checks/" | None |
| Other `tools/checks/*` (configuration-persistence, analytic-declaration, site-substrate, writer guard) | No. The rulings note that they scan only `backend/` and `frontend/` | Possibly. New backend modules are scanned by `analytic-declaration.ps1` and `configuration-persistence.ps1` and may need entries | None, provided telemetry stays inside its two files |
| `backend/assetops_backend/**` | No. Forbidden by the rulings | Yes: `financials/trial_fuel_comparison.py`, `estate/placement.py`, `estate/coverage.py`, `estate/financials.py`, `estate/scope.py`, `mini_decisions/scenario_rules.py`, `ev_scenarios/departure.py`, `cold_scenarios/review.py`, `analytics/cold.py`, `actions/verification_rules.py` (`window_evidence` gains `generator_kwh`), the action routes | None |
| `backend/migrations/versions/` | No migration | 0036..0039, renumbered in landing order | None. The Alembic chain has a single writer |
| `backend/tests/` | One new Postgres file (TEL-05, but see §2.4) | Edits exact-key tests (`test_w403_scenarios_postgres.py`, `test_w403_opportunity_read_postgres.py`) and adds new tests | None at file level |
| `host/tests/` | New files: `test_field_modbus_tcp_proof.py`, `test_field_export_csv_proof.py`, the pinned-JSONL generator and freshness test | No edits planned. The D2 producer lives in `tools/s602b_*` | None |
| `gateway/`, `contracts/`, `simulator/`, host product code | No. Protected seams 1-3 | No | None |
| `contract-fixtures/telemetry/**` | New | No | None |
| `tools/*.py` producers (`s602b_test_scoped_cases.py`, `s4_finding_cases.py`, new `cc_estate_seed.py`) | No | Yes | None |
| `frontend/src/**` | No. TEL-07 stops on any UI need | Yes: `actionPresentation.tsx` (`CLAIM_LABEL`), the estate panels, `SiteActionVerification.tsx`, `EvScenarios.tsx`, the cold financials | None |
| `.agent/mock-departure-register.md` | No | Yes | None |
| Coordination files: `.ai/ACTIVE_CONTEXT.md`, `.ai/CODE_STATE.md`, `tasks/README.md` | Status lines | Status lines | **Yes, text only.** Each lane edits only its own section; the coordinator resolves on merge |

### 2.2 Read-only shared dependencies (neither lane may change them)

- **Kobo registered basis.** `backend/tests/test_s2_registered_basis.py` and `simulator/.../observation/transform.py:generate_observations` feed telemetry's pinned JSONL.
  - Commercial D2 uses KOBO-001 only through its own producer databases and authored windows. It does not edit the basis.
  - The JSONL freshness test in `host/tests` would catch any drift.
- **`backend/tests/pg_harness.py`.** Both lanes use it. It already creates run-owned databases named `<stem>_pt<run>_<tag>_test`, so concurrent runs cannot collide on a name.
- **`gateway/tests/fake_central.py` and `host/tests/gateway_process.py`.** Telemetry reuses them; commercial does not touch them.
- **`assess_dispatch` and dispatch-3.1.** TEL-05 runs them; commercial does not change them.
  - D2 adds a key to `actions/verification_rules.py:window_evidence`, which is outside `plan_sha256` and outside dispatch.

### 2.3 Environment hazard (load-bearing)

- The shared venv `AssetOpsV1-plan2/.venv` holds editable installs of backend, contracts, gateway and simulator. They map to **`C:\Users\assef\Bineyame\AssetOPsV1`**, the main checkout (see `__editable___assetops_backend_0_0_0_finder.py`). That checkout is a detached HEAD at 056a34b8 with uncommitted changes.
- A command run from a lane worktree **without** `PYTHONPATH` therefore silently tests the main checkout's code, not the lane's.
  - `PYTHONPATH` entries are found before the editable finder, so setting it is a sufficient guard.
- `host` and `field` are not installed, and `pymodbus` is not in the venv.

Rules:

1. Every lane command sets `PYTHONPATH` to its own worktree. For example, telemetry uses `PYTHONPATH="<lane>\backend;<lane>\contracts;<lane>\simulator;<lane>\gateway;<lane>\host;<lane>\field;<lane>"`.
2. Nobody runs `pip install -e field` (it would bind `assetops_field` to one worktree).
3. `pymodbus==3.16.1` is installed into the shared venv **once, by the coordinator, before TEL-03**. It is additive, and nothing in the backend imports it.

### 2.4 Telemetry-internal finding the TEL-00 pre-flight must resolve (no cross-lane effect)

TEL-05 is planned as `backend/tests/test_field_modbus_tcp_acceptance_postgres.py`. Two rules conflict with that placement:

- `dependency-direction.ps1:233-240` scans `backend` **with tests** and fails on any `assetops_gateway` import.
- The D4 check spec also fails on `assetops_field` in `backend/` "tests included".

D4 point 4, however, lists `backend/tests` as an allowed importer of `assetops_field`. The two parts of the ruling disagree.

There is a precedent: host-side Postgres tests already exist (`host/tests/test_s6_verification_publication.py`, `test_s6_verification_replay.py` use the test database).

**Ruling (amends D4 point 4 and the TEL-05 card):**
- TEL-05 lives in `host/tests/test_field_modbus_tcp_acceptance_postgres.py`.
- The reverse rule forbids `assetops_field` in all of `backend/`, tests included.
- No existing rule is loosened.

This keeps the backend full suite free of any `field` import. That suite runs without `field` on its path (`backend/TESTING.md:107`), so a backend test importing `assetops_field` would break the commercial lane's full-suite runs.

### 2.5 Test databases

- Telemetry uses `pg_harness` run-owned names under the authorised `*_test` stem.
- Commercial producers use `assetops_cc_*_test`.
- If telemetry ever needs a fixed producer database, it uses an `assetops_tel_*_test` name.
- Both name patterns are inside the test-database authorisation. They are disjoint, and both run in `assetopsv1-postgres-1`.

## 3. Ordering constraints

There is no causal dependency between the lanes in either direction:

- Telemetry's October result is, by ruling, no Finding and no money (D5, N1). It feeds nothing in the commercial sprint.
- Commercial R7 already lists the proofs as a "parallel lane".
- The commercial sprint reads none of telemetry's outputs.

Within each lane the existing orders hold:

- **Telemetry:** TEL-00 → 01 → 02 → 03 → 04 → 05, then 06a (after 04), 06b, 07.
- **Commercial:** R1 (links, labels, beneficiary key, guard) → R2 (D5 placement) → the chosen decision (D2 recommended, or D1).

There is one cross-lane timing constraint, and it is a calendar one: telemetry's TEL-05 must run on the machine by Thursday 29 October for the 30 October showing. That makes it the first claim on the heavy-job queue (§6).

## 4. What each lane must not touch

**Telemetry lane (`task/TEL-…` branches) must not touch:**
- `backend/assetops_backend/**` or `backend/migrations/**`;
- `frontend/**`;
- `gateway/**`, `contracts/**`, `simulator/**`, host product modules;
- any `tools/checks` file other than `module-roots.ps1` and `dependency-direction.ps1`, and any existing rule in those two;
- `tools/*.py` producers;
- `.agent/mock-departure-register.md`;
- the shared venv beyond the one `pymodbus` install.

It must not start a dev server or browser capture.

**Commercial lane (`task/CC-…` branches) must not touch:**
- `field/**`, `contract-fixtures/telemetry/**`;
- `gateway/**`, `contracts/**`, `simulator/**`;
- `host/**` (product and tests);
- `tools/checks/module-roots.ps1` and `dependency-direction.ps1`;
- the Kobo registered basis and its fixtures;
- `MINIGRID_ROLES*` and the source classes in `evidence/source_provenance.py`. A real-source class is telemetry's TEL-09, after October.

It must not add any field-source special case in `financials/`, `analytics/` or `evidence/`. That restates telemetry protected seam 5, which binds both lanes.

**Both lanes:**
- Write coordination files only in their own section.
- Create no database outside the authorised `*_test` patterns.
- Never run a heavy job outside the queue.

## 5. Merge order

1. **TEL-01** (the new root and its checks) merges first, as soon as it is accepted. It is the only change to shared guard scripts. Landing it early means every later commercial branch merges `main` with the new checks already green.
2. Then merge by readiness, interleaved. Each merge is followed by a merge of `main` into the other lane's open branch and a scoped regression (`test-suite-policy`):
   - telemetry TEL-02..05, which are new files only;
   - commercial R1, then R2.
3. **The commercial migration slice merges last in any batch.** With one decision that is a single migration, numbered 0036. If two decisions enter the sprint, it is one combined schema slice (owner question 14).
   - It pays the full backend and frontend suites on an idle machine.
   - Telemetry needs no re-run after it, because telemetry tests create schema at head through `pg_harness` and read nothing the migration changes.
4. TEL-06b and TEL-07 merge when ready. They slip to 31 October before any commercial slice is delayed for them.
5. The safety-net full suite runs on `main` every 2-3 merges (standing policy), in the queue.

## 6. Machine limits (16 GB, one heavy job at a time)

Heavy jobs, in a single queue held by the coordinator:

| Job | Lane | Rough size |
|---|---|---|
| TEL-05 Postgres acceptance (run alone, twice) | Telemetry | Minutes each |
| TEL-04 / TEL-06a focused E2E (real gateway process + TLS server; one file at a time) | Telemetry | Minutes. Treated as heavy-lite: never during a browser capture or full suite |
| Commercial tier-2 Postgres per slice | Commercial | Minutes to tens of minutes |
| Commercial tier-3 producer + browser capture per slice | Commercial | Tens of minutes |
| Full backend + frontend suite (migration slices, merges) | Commercial / main | About 50-60 min, capped at 2× (`backend/TESTING.md:208`) |

Light jobs may run beside any heavy job. These are pure and focused `field/tests`, commercial tier 0-1 (about 15 s), the `.ps1` checks, and code editing.

Queue priority until 30 October:
1. TEL-05;
2. any job blocking a merge;
3. commercial captures;
4. full suites, only when the machine is otherwise idle.

After 30 October the commercial lane has priority. Long runs use `tools/keep-awake-during-tests.ps1`. Emulator port 5020 and the TLS test port must not overlap the commercial dev-server ports. They cannot overlap in time anyway, because the heavy-lite rule above keeps them apart.

## 7. Review capacity

The binding is a fresh Claude `assetops-reviewer` per slice, plus re-reviews, with Codex batched per milestone (`.ai/ROLE_CONFIG.md` "Owner Review Routing From S3 Onward"). Reviewer count is not the constraint, because reviewers are fresh subagents. The constraints are:
- tokens;
- reviewers asking for re-runs, which enter the same queue.

Proposed review grouping, to keep it to about 6 reviews in the sprint window:
- **Telemetry, 3 reviews:**
  - TEL-01+02+03, the core, client and emulator (focused tests only, no queue time);
  - TEL-04+05, the E2E and acceptance (the reviewer reads the TEL-05 run output and does not re-run it unless a finding needs it);
  - TEL-06+07.
- **Commercial, 3 reviews:** R1; R2; the decision slice (including its migration).
- **Codex:** one batched review per lane at its milestone end. No per-slice Codex review.

Reviewers are never the implementer of the slice, and the two lanes' implementers do not review each other's slices.

## 8. Proposed two-lane split

| | Lane T (telemetry) | Lane C (commercial) |
|---|---|---|
| Worktree / branch | New worktree `AssetOpsV1-tel` from main, `task/TEL-01-field-core`, then one branch per card group | New worktree `AssetOpsV1-cc` from main, `task/CC-R1-links-labels`, then `task/CC-R2-placement`, `task/CC-D2-reassessment` (or D1) |
| Builder | One Claude implementer | One Claude implementer |
| Scope to 30 Oct | TEL-00..05 must; TEL-06a should | R1, then R2 |
| Scope after 30 Oct | TEL-06b, TEL-07 (31 Oct); TEL-08 after TEL-05 is green twice | The decision slice (D2 recommended), then R4/R5/R6 as declared illustrations |
| Heavy-queue priority | First, until 30 Oct | First, from 31 Oct |
| Owner decisions it needs first | Owner questions 1 (today) and 2-5 (by 29 Oct) | Owner questions 1 (today) and 9-11 (before R1 and R2) |
| Stop and ask | Any need to touch backend, frontend or gateway code, or an existing check rule | Any need to touch `field/`, gateway, contracts, host or the two telemetry check files |

Before each lane writes code, its builder runs the pre-flight from the plans: read all the lane's cards and batch every question into one request. For telemetry, that batch includes the §2.4 placement ruling above.
