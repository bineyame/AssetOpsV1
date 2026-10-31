# LINK-LINEAGE review packet

Task `tasks/LINK-LINEAGE-board-action.md` (in_review). Branch `task/LINK-LINEAGE-board-action`, worktree
`C:\Users\assef\Bineyame\AssetOpsV1-link`, from main `15eed62c8` (+ build-sheets commit `0796218fc`).
Contract: `AssetOpsV1-plan2/.agent/build-sheet-LINK-LINEAGE.md` U1-U3; decision `D-2026-10-31-board-action-refresh-lineage`.
USER_REVIEW_REQUIRED: false.

## Outcome

The mini Site outcome board now links an Action to the shown revision of its origin Finding when every revision after
the origin, up to the shown one, is BASIS_REFRESHED with the origin's lifecycle and episode bounds. The link drives
only the applied status signal and Must-not-harm. On the real s602b fixtures, Kobo Day B (guardrail) and the e4
`verified` board now carry the Cost Must-not-harm line with ACT-000001's verification href (R552's subject).

## Commits

- `39ebf86d0` U1: `site_outcomes/board.py` `BASIS_REFRESHED`, pure `refresh_chain`, `FindingFact.refreshed_from`
  (last, defaulted), `exact_actions` -> `linked_actions` (3 sites + `_row` param); `tests/test_link_lineage.py`.
- `73296c8b2` U2: `mini.py` `MiniPorts.finding_history` (default None) and `_lineage` (after `_actions`);
  `read.py` `BoardServices.finding_reads` + port (finding-index gate, `history` paged at 500, `jsonable_encoder`);
  `composition.py` / `main.py` pass the app's `finding_reads`; tests in `test_out_b2_mini.py`,
  `test_out_b4_main_binding.py`.
- `4111496d3` U3: `test_out_b4_board_postgres.py` helpers `_spy_lineage`, `_expected_link` (inline rule over
  `GET /api/sites/KOBO-001/findings/{id}/history?revision_id=<shown>`, every page), `_assert_lineage_must_not_harm`;
  `test_kobo_guardrail_two_board_days` Day A and Day B, `test_out_e4_readback_postgres.py`.
- Closeout commit: DECISIONS entry (sheet §7 verbatim), R552 note, task file, CODE_STATE, ACTIVE_CONTEXT, this packet.

## Acceptance (sheet §3)

| Item | Status | Evidence |
|---|---|---|
| U1 `refresh_chain` pure, module level | met | `board.py` `refresh_chain`; P1-P3, N1-N5, N5b (REOPENED, SPLIT, MERGED_INTO, MODEL_REEVALUATED, unknown), N7-N11 |
| U1 `refreshed_from` field, `linked_actions` join | met | B1 (Must-not-harm = existing sentence + verification href; reason `PRIMARY_FINDING_APPLIED`), B2 (`PRIMARY_FINDING_OPEN`, None), N6 (domain never links), B3 (Earlier lists identical) |
| U2 `finding_history` port, default None | met | M4 (default: no link, no failure) |
| U2 `_lineage`: one call per Finding, none on exact | met | M1 (port never called), M5 (two Actions -> one call; an origin absent from history does not link) |
| U2 refreshed chain links | met | M2 |
| U2 failure is PARTIAL, no link | met | M3; M6b (closed finding-index gate -> PortUnavailable recorded, no link) |
| U2 real reader | met | M6: `FindingReadService(fake_store, None).history` through the B4 `mini_ports` binding: P1 links; N1, N2, N3, N5 and a revision gap do not |
| U2 wiring is the app's instance | met | `test_board_services_get_the_apps_finding_read_service` (AST: the single `finding_reads = build_finding_read_service(...)` is the kwarg passed; composition stores it) |
| U3 b4 guardrail Day A + Day B by inline rule | met | records below |
| U3 e4 `must_not_harm` by inline rule | met | record below; every existing e4 assertion unchanged and passing |
| U3 register R552 note; DECISIONS §7 | met | `.agent/mock-departure-register.md` R552 (still open); `.ai/DECISIONS.md` tail |

## U3a records (printed `OUT-B4 record ..._lineage`)

| Board | Shown F01 revision | ACT-000001 origin | Between (no, transition, lifecycle) | rule | Must-not-harm |
|---|---|---|---|---|---|
| guardrail Day A 2026-10-06 | `ffc50e54` | not on the board (no Action in the composer's Action set that day) | — | false | None |
| guardrail Day B 2026-11-02 | `ffc50e54` | `bf313638` (verification INEFFECTIVE) | (2, BASIS_REFRESHED, SUPPORTED) | true | ACT-000001 text, `/sites/KOBO-001/actions/af89a775.../verification?event_id=c0d35198...` |
| e4 `verified` | `746850a1` | `75e0598f` (VERIFIED) | (2, BASIS_REFRESHED, SUPPORTED) | true | ACT-000001 text, `/sites/KOBO-001/actions/9a16cd44.../verification?event_id=02f04211...` |

Day A: the Action index for the day carries no ACT-000001 row, so there is nothing to link and the
prior `must_not_harm is None` holds by the same rule (the test asserts None from the computed `false`).

## Checks run

- U1 set (5 files): 90 passed. U2 set (12 files): 161 passed.
- U3 set (U2 set + `test_out_b4_board_postgres.py test_out_e4_readback_postgres.py test_out_b4_window.py`, real
  Postgres `assetops_test` server, case DBs `assetops_out_b_<case>_test` / `assetops_out_e_board_test`): 177 passed,
  0 failed, 422.6 s, revision `4111496d3`.
- Non-vacuity (each on committed `board.py`, then `git checkout --`): dropping the episode-end check fails N3, M2b,
  M6; dropping the lifecycle check fails N2, M2b, M6; disabling the contiguity check fails N10, M2b, M6; dropping
  `refreshed_from` from the join fails B1, M2, M6.
- `tools\check-all.ps1 -Python <plan2 venv>`: All 11 guards passed at `39ebf86d0`, and again at `4111496d3` with the
  closeout docs in the tree (before this packet was written); again at the main-merge head `b7ea89651`; and at the
  review-lows head `6f681892d`. 11/11 each time.
- `-Tier all` (merge gate, coordinator's go): main `ce5df006c` (contains the w301 fix `8528ec69a`) merged in as
  `b7ea89651`; `tools\run-backend-suite-in-container.ps1 -Tier all` on `b7ea89651`, run `20261031-175151-7959ea`,
  4 workers, dedicated `postgres-test`. Wall time 3881 s (cap 6000 s; started after another lane's OPS-03 run
  cleared). JUnit `var/test-results/OPS-03/20261031-175151-7959ea/junit.xml`: 4595 tests, 0 failures, 0 errors,
  0 skipped. The w301 `INVALID_CURSOR` failure is gone. The fixed-clock w401 case did not fail on this run.
- Review lows (`.agent/LINK-LINEAGE-review.md` in plan2, ACCEPT), commit `6f681892d`, after the full run:
  L1: the b4 Day A/Day B loop asserts the recorded branch (Day B true, Day A false), and e4 asserts true.
  L2: `mini._lineage` runs `refresh_chain` inside `reads.call("finding_history", ...)`; new pure test
  `test_out_b2_mini.py::test_m7_malformed_history_row_is_partial_not_a_failed_board` (on the pre-fix `mini.py` it
  fails with `KeyError: 'revision_no'`). Re-ran the U3 scoped set (U1 + U2 sets + b4/e4 Postgres + b4 window):
  178 passed, 0 failed, 302 s. No full rerun (coordinator: small change after the full run).
- No vitest, no captures (no frontend change; sheet §4).

## Known deviations

- U2 "a closed finding-index gate makes the port refuse" is tested in `test_out_b2_mini.py` M6b (through the real
  `SiteOutcomeBoardService.mini_ports`) rather than in `test_out_b4_main_binding.py`/`test_out_b4_imports.py`; the
  binding test proves the app instance by AST + composition, because without a DB `finding_reads` is None in the app.
- U3 records the shown revision and the Action origin from a spy on `mini._lineage` inputs (what the board composed);
  the link decision itself is recomputed independently in the test from the history route.

## Residual risk

- One extra history read per Finding with a non-exact Action, mini boards only; bounded by the Action count.
- DEMO-SPARSE CO-1 still asserts the re-premised negatives until DEMO-A edits `tools/demo_combined_finish.py` (§5);
  R552 closes only then.

## Review focus

`board.py` `refresh_chain` against sheet §2 (breaks 1-5, revisions after the shown one never read);
`mini.py` `_lineage` call condition; `read.py` port gate and paging.
