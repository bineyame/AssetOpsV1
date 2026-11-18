# Review: E2 fix round A (FR-A), branch `task/E2-fix-A`, head 1d11eb77c

Reviewer: fresh Claude (Opus), independent of the builder. Diff reviewed: `git diff 8dae46bd9...1d11eb77c` (main 8dae46bd9
is an ancestor of HEAD; two-dot and three-dot diffs are identical, 24 files). Specs: "E2 fix-round scope (2026-11-09)" and
"FR-A stop rulings (2026-11-09)" in plan2 `.agent/build-sheet-OWN-GAPS-2026-11-08.md`. Packet: `.agent/review-packet-E2-fix-A.md`.

## Verdict: ACCEPT WITH NOTES

No assertion was weakened beyond what its ruling allows, and every "stale" re-pin names a real commit or migration whose change
it matches. The test-only scope holds. The notes below are Low or Info. None blocks the merge. One wording correction to E4-GE
goes to the Architect (section "G-e").

## Product code: none changed (verified)
`git diff 8dae46bd9 HEAD --name-only` lists only `backend/tests/**`, `backend/tests/fixtures/k6b_mill_pins.json`,
`frontend/src/**/__tests__/**` (sldFixtures.ts, s502 and s5 tests), `tools/run-backend-suite-in-container.sh` and the packet.
Nothing under `backend/assetops_backend`, `config`, `host`, `field`, `gateway`, `simulator`, or frontend outside `__tests__`.

## Per-item check

| Item | Justified by named commit/ruling | Still a real guard | Loosened beyond ruling |
|---|---|---|---|
| Container copy list | D-E2.2. Exactly the four paths `.agent/DIESEL-D0 .agent/DIESEL-F0 Docs/demo-sprint .gitattributes` plus the comment | n/a | No |
| Clock guard row + ast test | D-E2.1 text verbatim | Yes. I re-ran the mutations in-process with no file edits: a planted `s.schedule_inputs(1)` caller in a temp copy of `assetops_backend` -> FAIL; `fuel_balance.scheduled` added to `listed_modules()` -> FAIL | No |
| ch6b | D-E2.3 text verbatim (set of node keys + earnings on the week, full `nodes` on S) | Yes. See L2 | No (the ruling's own shape) |
| s502 / sldFixtures | D-E2.4. `withLoadNames(site, names)` moved unchanged apart from the `site` parameter; scan and shared fixture untouched | Yes | No |
| G-a ch1a, cc_schema, out_d1 | `0047_chain_response.py` `INPUT_TABLES` includes `site_day_snapshot`, `trial_cost_comparison_revision`, `outcome_objective_revision`; trigger and function names match `{table}_cic_{ins,upd,del,trunc}` / `chain_input_change_{table}`; d1 tgtype values 4/16/8/32 match AFTER STATEMENT INSERT/UPDATE/DELETE/TRUNCATE | Exact-list equality kept; `_immutable` (and d1 `chain_event`) still asserted | No |
| G-a w204 | 0053 constraint names, the three columns and the downgrade's `model_id IN ('fuel-cost-1')` match `0053_fuel_cost_2.py:42-83` | Stronger than a plain drop: asserts each 0053 column is present and `null` in every stored row before stripping | No |
| G-a w207 | 0053 (972dc747f) | See L3 | Slightly; see L3 |
| G-a w403 | `0051_action_opportunity_origin.py:66-67` adds `mini_opportunity_revision_opportunity_scope`; only at `latest` | Yes. `_immutable` triggers kept. The `_cic_` filter in `catalog()` predates FR-A (77f88a75d) | No |
| G-b | 0053 widened the formula check to admit `/2`; `/9` is still rejected; UPDATE/DELETE append-only asserts unchanged | Yes | No |
| G-c | All 10 files: `git log --diff-filter=A` matches each listed commit (9c0a3f510, 5a5211639, 97e91b8f1, a02f72ff3, 870e33119, 8b68aaa14, 17e69a295), and every commit touching each file (incl. b1618b27a, a27549f1b) is a DD-1a1/DD-1a2 commit, ancestor of eae5174b7 and/or 1dd3b1862. No later edits | Yes. I re-ran mutations in-process: drop the `kobo-mill-midday` exemption -> v2 rule FAILS and count FAILS; add an original v2 id (`kobo-daytime`) to the exemption -> FAILS; corrupt one new pin -> FAILS. The strict v2/supersedes rule is unchanged for the original 14 | No |
| G-d w302 | 1c3e3a075 moved `financials` to `window_link_refs` (same signature); `financials.py:157` looks it up at call time, so the tamper is effective | Yes | No |
| G-d ch4 | 6b4e682f2 adds `headroom_unit` | Exact dict equality kept | No |
| G-d walk1 | 972dc747f declares the no-load rate and basis | Stronger: asserts exactly one component carries exactly `{3.3, GENERIC_DEFAULT}` | No |
| G-f | K10 v2 (56256bbc9) | Stronger than the rule asks: the three stored measures are named exactly, `none_declared == {productive_kwh}`, readiness NONE/UNKNOWN, the exact gap text, and no `productive_kwh` in the text. This satisfies the stop rule ("another measure missing and still settles" would fail) | No |
| G-g | K10 v2 text `chain/vocabulary.py:290` matches `NONE_DECLARED_TEXT`. R-3 accepted the deviation | Stronger: the old conditional `if NOT_KNOWN` became unconditional; premise proved from the stored Foundation, non-empty first | No (see I2) |
| G-h | D-E2.10 items 1-4 verbatim; fixture diff is exactly 17 lines (14 keys, 3 `declared_by`); `<d-14>`..`<d-1>` from effective day 2026-11-08 is consistent with d25f95ccb's 2026-11-08 06:25 +0300 commit time | Yes: the absolute-date sweep covers keys and values; literal kept only for `TARGET["declared_by"]`. Builder mutation recorded (not rerun: Postgres) | No |
| G-i | Diagnosis verified in code: `class EvidenceMoneySnapshot(EstateSnapshot)` binds its base at import (`postgres_evidence_money_read.py:22,55`); the service constructs it via the module global (`:41`), so the new monkeypatch is effective. The pinned `__init__` signature matches `pin_read_at`'s | Yes: same rows and gate, only "now" is pinned | No |
| G-j | badd2fbb9: `daylight_hours` yields one missing head per uncovered operating hour (`mini_depth/store.py:366-396`) | Retention-edge and FAILED-retention asserts unchanged; head-shape asserts are exact (24 hour starts, then one selected head per day 6-9 Oct). The uF6 "late input" is now a late selection rather than late evidence; it is still a new W4-02 selection, which is what the docstring guards | No |
| G-e | D-E2.9 with the recorded deviation (below) | Yes; see L1 | No |

## Findings

**L1 (Low). `backend/tests/test_out_b4_board_postgres.py:498`, the strict xfail has no `raises=`.** `xfail(strict=True)` turns
any exception in the body into XFAIL: a KeyError, a SQL error or a changed `_board` signature would read as "BL-63 still
present". The builder proved the reason once with `--runxfail`, but nothing keeps it proved. Fix: add
`raises=AssertionError`, so only the intended assert counts as the expected failure. This is a cheap hardening of a new guard,
not an acceptance gap.

**L2 (Low). `backend/tests/test_ch6b_estate_postgres.py:259`, the S equality has no non-vacuity check on the KPI node, and the
mutation proof was not run.** The assert is not vacuous as a whole: `day`'s Optimize `earnings` is proved non-null and equal to
the week claim (`:249-251`), so a missing or None `row_s["nodes"]` fails. But V4's point is the KPI node's `days`. If `kpi`
were None on both S reads, the S check would pass without testing V4. I judge the missing mutation proof as not material on its
own, because the equality is a plain `==` over dicts proved non-empty. Fix (one line, no container mutation needed):
`assert day_s["nodes"].get("kpi") is not None, day_s["nodes"]` before the equality.

**L3 (Low). `backend/tests/test_w207_ev_money_postgres.py:97-111`, the 0053 constraints are excluded from both comparisons.**
`financial_constraints` feeds the 0025 comparison (`:288`), where the exclusion is needed. It also feeds the head-after-round-trip
comparison (`:296`), where it is not needed, so that check no longer proves the five 0053 constraints return byte-identical.
The ruling said "add the widening", not "exclude". The loss is covered elsewhere: `test_fuel_cost_v2_postgres.py::TestMigration0053`
round-trips 0053 itself. Fix (optional): exclude the five only at `:288`, or compare the full set at `:296`.

**I1 (Info). `backend/tests/test_idx_gaps_postgres.py:178-183`.** The docstring still says "the board day is unsettled" before the
K10 v2 addendum that says it settles. Reword the first sentence.

**I2 (Info). `backend/tests/test_ch6_nodes_postgres.py:75`.** The "none declared" premise is proved with the product's own
`productive_loads` filter. If that filter broke, the premise check would break with it. R-3 accepted this approach. A raw
`supply-use = PRODUCTIVE` scan over the content would make the check independent.

## G-e: the deviation and the E4-GE wording
- I confirmed the mechanism in code (`outcomes/status.py:69-87`). `PRIMARY_FINDING_OPEN` gives NEEDS_ATTENTION (MG-2).
  `SECONDARY_FINDING_OPEN` would give WATCH, but the recorded board has no open Finding signal on MG-4: it reads NO_OBJECTIVE /
  `NO_OBJECTIVE_DECLARED`. The WATCH is MG-7 `EVIDENCE_READINESS_NONE`. That is a readiness flag, which agrees with the board's
  own gap line, so it is not a judgement on an unchecked day. Pinning the reasons as recorded is correct. Asserting
  `SECONDARY_FINDING_OPEN` would have been false.
- The BL-63 inconsistency is still held. MG-2 `PRIMARY_FINDING_OPEN` sits on 10-06 (and 11-02) while the same board's port is
  `chain_day = {settled: true, readiness: NONE, gaps: 31}`, asserted on all three boards. The new xfail test reads the stored
  `avoidable_gen_min` grade per day, and its prefix list covers `PRIMARY_FINDING_*`. So it fires on MG-2 for the intended reason.
  I can only confirm this from the code; the packet's `--runxfail` result is the builder's. See L1 for keeping the reason pinned.
- **E4-GE wording, correction for the Architect.**
  - R-1's first line should read: "The MG-2 NEEDS_ATTENTION state comes from an open primary Finding. On s602b the WATCH is
    MG-7 `EVIDENCE_READINESS_NONE`, a readiness flag. MG-4 reads NO_OBJECTIVE (no secondary Finding signal is open)."
  - E4-GE (b) should check **every outcome** on the board, as the xfail test does, not only "MG-2 or MG-4". Which outcome a
    Finding moves depends on its mechanism, and the s602b case already showed that the MG-4 premise did not hold.
  - The banned-reason list should add `OBJECTIVE_BEHIND_PACE` (`status.py:92`). It is a WATCH verdict from the objective, and it
    is just as much a judgement on an unchecked day. It is missing from both E4-GE (b) and the xfail test's `verdicts` tuple.
    Adding it to the xfail test is optional: it cannot change today's XFAIL.
  - Readiness reasons (`EVIDENCE_READINESS_*`) stay allowed.

## Checks I ran (this worktree, head 1d11eb77c)
- `python -m pytest tests/test_ch5c2_clock_guard.py tests/test_scenario_fingerprints.py -q` (plan2 venv, run from `backend/`;
  confirmed it imports `AssetOpsV1-e2fa/backend/assetops_backend` and `AssetOpsV1-e2fa/config/scenarios`): **14 passed, 18.5 s**.
- In-process mutation checks, no file edited. G-c: 4 mutations, all killed. Clock guard: 2 mutations, all killed; the
  unmutated baseline passes. (Caution: a script run from outside `backend/` imports the editable install at
  `C:\Users\assef\Bineyame\AssetOPsV1`, a stale tree with 13 scenarios. My first attempt was invalid for that reason and was redone.)
- `npx.cmd vitest run src/shell/__tests__/s502OverviewFindingList.test.tsx src/shell/__tests__/s5SiteWindowOverview.test.tsx`:
  **2 files, 100 tests passed** (37 + 63). This ran here and was not blocked by the sandbox.
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-architecture.ps1`: it failed first because the worktree has no `.venv` ("chain structure guard cannot run"). With
  `ASSETOPS_GUARD_PYTHON` set to the plan2 venv: "Architecture check passed." `tools/check-agent-workflow.ps1`: passed.

## Not verified by me (per dispatch: no Postgres or container runs)
All Postgres results are the builder's: container runs 20261109-152719-3e0152 and 20261109-160557-644a04 (358 tests, 3 failed
then = the stopped G-e x2 and G-h), and host runs at 6e886c3cd/9d04c7a30 (k6b 6 passed; out_b4 5 passed, 1 xfailed). I did not
see the recorded S602B dicts on the wire, the k6b pin equality, the G-h mutation, the G-j hour counts, or the ch6b S equality.
`check-all.ps1` (18 guards) was not rerun. Note: the container run that covers all files predates the G-e/G-h commits. Those two
files were rerun on the host only, and no single full scoped run exists at 1d11eb77c. That is acceptable for a test-only
change to two files, but say so at merge.

## Residual risk not in the packet
- `pin_read_at` (w301) has a worse hole than the packet states. If `postgres_evidence_money_read` is first imported while some
  test's `Pinned` patch is active, `EvidenceMoneySnapshot` keeps that `Pinned` class (and its fixture clock) as its base for the
  rest of the process. monkeypatch undo does not revert a base class. Later tests then read at another test's pinned time. The
  k8 fix makes k8 order-independent but does not close this leak into others. FR-B owns w301; it should patch
  `EvidenceMoneySnapshot` in `pin_read_at` itself.
- G-e's product inconsistency (BL-63) is bounded only by E4-GE on the E3 build. See the wording correction above.
