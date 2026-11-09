# Review packet: E2 fix round A (FR-A), branch `task/E2-fix-A`

Spec: "E2 fix-round scope (2026-11-09)" at the end of `.agent/build-sheet-OWN-GAPS-2026-11-08.md` (main 3db4b2bb7).
Product code changed: NONE (only `backend/tests/`, one frontend test fixture and two frontend tests, and
`tools/run-backend-suite-in-container.sh`).

## Outcome
Container copy list, clock-guard entry and test, ch6b redesign, s502 fixture, G-a to G-d, G-f, G-g, G-i and G-j are built.
**Three presented-beat items are STOPPED for the Architect: G-e (two tests) and G-h (one test).** Nothing in the
packet loosens a test to pass; the stopped tests are untouched and still red.

## Commits (all end with the Opus co-author line)
| Commit | Content |
|---|---|
| 766b2fdd7 | container copy list; clock-guard allow-list row + `test_schedule_inputs_is_called_only_by_the_tick_stage` |
| 40a6b3d17 | ch6b nodes-on-S redesign; `withLoadNames` / `KOBO_LOAD_NAMES` moved into `sldFixtures.ts`, s502 uses it |
| 731291dd3 | G-a, G-b, G-c, G-d(w302) |
| 9c407d24d | G-d (ch4, walk1) |
| 0129d1120 | G-f |
| 0c3fddf97 | G-g |
| 9cf504960 | G-j |
| 52190948d | G-i |

## Per-item: change and justification
- **Container list (D-E2.2).** `.agent/DIESEL-D0`, `.agent/DIESEL-F0`, `Docs/demo-sprint`, `.gitattributes` copied; comment
  updated. All four tracked. K0/K1/K3/K4a/K5/K7/ch5b collected and passed in the container (below).
- **Clock guard (D-E2.1).** Allow-list row for `PostgresFuelBalanceStore.schedule_inputs.work` as `_WRITER`; new ast test: callers
  of an Attribute named `schedule_inputs` in `assetops_backend` are exactly `fuel_balance/scheduled.py`, and that module is not in
  `listed_modules()`. Mutation: added a second caller (`def _planted(s): return s.schedule_inputs(...)` in `fuel_balance/model.py`)
  -> the new test FAILED; reverted (`git checkout`).
- **ch6b (D-E2.3).** Week asserts kept; node-key set and the cost claim compared on the week; new S check (one-day pair of UTC
  midnights for D13) asserts Kobo's OPTIMIZE_COST `nodes` equal the D13 board's exactly. The S equality PASSED in the container
  (no stop). Mutation proof for the new S assert: not run (a mutation needs a ~11 min L2m container run); the old full-nodes-on-week
  assert is the E2 failure it replaces, and the S assert is the V4 rule it now carries.
- **s502 (D-E2.4).** `withLoadNames(site, names)` + `KOBO_LOAD_NAMES` exported from `sldFixtures.ts`; s5SiteWindowOverview and
  s502 use it. Vocabulary scan and shared fixture untouched. Vitest 2 files, 100 tests passed (37 + 63).
- **G-a (stale; migration files on main).** ch1a: `0047_chain_response.py` adds `site_day_snapshot_cic_{ins,upd,del,trunc}`;
  query now `ORDER BY tgname`, expected list in name order with `_immutable` kept. cc_schema and out_d1: same 0047 `*_cic_*`
  triggers on `trial_cost_comparison_revision` / `outcome_objective_revision` (d1 keeps `chain_event`:4 and `immutable`:27, adds cic
  del 8, ins 4, trunc 32, upd 16). w204: `below_0026` now also drops the 0047 cic triggers and the `0053_fuel_cost_2.py`
  constraints/columns and restores the `fuel-cost-1`-only `model_id_check`. w207: `financial_constraints` excludes the five
  `financial_consequence_revision` constraints 0053 adds or widens. w403: `0051_action_opportunity_origin.py` adds unique key
  `mini_opportunity_revision_opportunity_scope` (expected at head only). NOTE the spec guessed the w403 delta as a
  `mini_alternative_revision` key; the catalog diff showed the actual delta is the 0051 key on `mini_opportunity_revision` (named
  migration exists, so it meets the bar). All append-only triggers remain asserted in every list. 8/8 passed after the change.
- **G-b.** `trial-fuel-comparison/2` -> `/9` (0053 / 972dc747f made /2 valid); UPDATE/DELETE append-only asserts unchanged, pass.
- **G-c.** All 10 new scenario files (not 24: 14 were pinned already) were checked with `git log`: every touching commit is a
  DD-1a1/DD-1a2/DD1a1-R* commit inside merges eae5174b7 / 1dd3b1862. Pinned the printed fingerprints; `FIRST_SHIPPED_AS_V1` dict
  with the introducing commit per entry; count assert is `14 + len(FIRST_SHIPPED_AS_V1)`; the strict v2/supersedes rule is unchanged
  for the original 14. Mutation: renaming one `FIRST_SHIPPED_AS_V1` key made `test_every_shipped_scenario_is_v2_superseding_v1`
  FAIL; reverted.
- **G-d.** w302: spec says "`window_links` is now `windowed_lines`"; actual: `financials.window_links` was removed by CH-5a2a
  phase 1 (1c3e3a075) and financials builds links through the imported `window_link_refs`; the tamper now wraps that (same
  signature), and the test passes unchanged otherwise. ch4: added `headroom_unit: "kW over 1 daylight hour"` (CH-6b2 6b4e682f2).
  walk1: the configuration also declares `generator-no-load-fuel-rate` 3.3 and `...-basis` `GENERIC_DEFAULT` on exactly one
  component (FUEL-1 A1 972dc747f); the additive loop excludes those two keys and asserts them separately.
- **G-f (stale, rule met).** Diagnosis: `finding_gap_line`/`day_settled` on both board days: measures are 4; 3 have stored NO_DATA
  rows; `productive_kwh` is the only one without a row and is declared absent (`none_declared`). K10 v2 (56256bbc9) drops it from
  `day_settled`, so the day settles while readiness stays NONE and 31 of 31 days are still gaps. Test now asserts settled,
  readiness NONE/UNKNOWN, `none_declared`, the three measures stored, and the gap text with the plain-words note (no
  `productive_kwh` in text). Note: BOTH 10-06 and 10-07 settle (the old test assumed both unsettled).
- **G-g (stale; one deviation from the spec premise, see below).** `money.estimated_income` NOT_KNOWN now reads "No productive-use
  sales · no productive-use equipment declared" (K10 v2 MD-K10-1). `_check_nodes(none_declared=True)` asserts that exact text for
  this Kobo only, and the test proves the premise against the stored data: every `foundation_revision` of KOBO-001 in this case
  has zero PRODUCTIVE loads (`productive_loads`), asserted non-empty first. The earnings claim must now be exactly this text.
- **G-i (test setup; no product cause).** `test_k8...` passes alone (host and container) and fails when any estate test ran
  earlier in the same process. Cause: `pin_read_at` patches `postgres_estate_read.EstateSnapshot`, but the Portfolio reads through
  `EvidenceMoneySnapshot(EstateSnapshot)` whose base is bound when its module is first imported. After another estate test the
  Portfolio read at the real DB clock (2026-11-09, printed `k`) and could not see the fixture's 2027-01 Finding; the isolated run
  got `k = 2027-01-20`. Instrumented proof: `DBGFR ... k 2026-11-09 ... n 0` after ch4 vs `k 2027-01-20 ... n 1` alone. The gate
  (`lifecycle in MEMBERS`, lens, page) did not drop the row; the fuel join (`_fuel_rows`) saw nothing because of `k`. Fix: the test
  also pins `EvidenceMoneySnapshot` read time to `READ_AT`. Verified after ch4 and after k6b and alone. The real Kisiwa row is read at
  the real clock after its Finding is known, so the same gate would not drop it; E4-K8 still checks it on the E3 build.
- **G-j (stale, rule met).** Cause 1: under `mini-opportunity/2` a day with no measured hour yields one missing head per operating
  hour (24 for 10-05), not one. The retention-edge asserts (exact queued lists) are untouched; the head-shape asserts now state 24
  consecutive missing hours from local midnight, and 6-9 Oct one selected head each. Cause 2 (uF6): no hour can be selected without
  measured PV evidence, so `_reconcile(DAYS[1:])` before any `_ingest` wrote no selection (scan heads empty) and the first scan queued
  nothing. The measured hours are now ingested up front; the late input becomes the 6 Oct selection; the FAILED-job retention asserts
  (3 scans -> `[]`) and the exactly-one-new-job asserts are unchanged and pass. Stop rule: a day with full daylight hours IS queued.

## STOPS (for the Architect; tests left red and unedited)
### G-e `test_out_b4_board_postgres::test_kobo_guardrail_two_board_days` and `::test_kobo_estate_finding_rows_and_states`
Board states are now `{MG-1: NO_OBJECTIVE, MG-2: NEEDS_ATTENTION, MG-3: NOT_MEASURED, MG-4: WATCH, MG-6: NOT_MEASURED, MG-8:
NOT_APPLICABLE...}` on days 2026-10-06, 2026-11-02 and 2026-10-21. The recorded port for the SAME boards says
`chain_day: {settled: true, readiness: "NONE", gaps: 31}` (the board's own gap line reads "31 of the last 31 days have no checked
readings"). MG-2 (avoidable generator minutes) and MG-4 are settled from `base and dispatch is not None` (`mini.py:539-540`), i.e. from the
delivered dispatch assessment and the SUPPORTED Findings of that day, not from checked readings. So NEEDS_ATTENTION/WATCH appear on days
the same board calls not checked: this is exactly the stop condition. NO_OBJECTIVE on MG-1 is benign (no objective declared in the
fixture). Not edited.
### G-h `test_k6b_fuel_verification_postgres::test_5_mill_path_outputs_equal_the_first_commit_pins`
Not a named-commit change: a wall-clock dependence. Re-capturing the pins (`K6B_CAPTURE_PINS=1`, then reverted; capture saved at
`scratchpad/fra/k6b_mill_pins.captured.json`) shows the grade-window keys shifted by exactly one day (10-25..11-07 became
10-26..11-08, 11-05 COMPLETE->NO_DATA, 11-08 added) and `declared_by` `<d-3>` -> `<d-4>`. The fixture sets `occurred_at` through
`test_w401_work_service_postgres.at()`, which is `datetime.now(utc)` when `_BASE` is unset, so the effective day moves with the date;
the pins were captured on 2026-11-08 and fail on every other day (same family as FIX-W401b). Verdict, counts and before/after values
are unchanged in the capture, but the rule says re-pin only for a named change, so I did not. Suggested ruling for the Architect:
freeze the story clock for this test (set `_BASE`) and re-pin once. Needs a ruling; cost small, test-only.

## Checks (final revision of test files = 52190948d)
- Scoped container run 1 (revision 9cf504960, before the G-i edit): `-Close no -Workers 2 -CapMinutes 60`, run
  `20261109-152719-3e0152`, wall 672 s, junit 358 tests, 4 failed (G-e x2, G-h, G-i), 0 errors, 0 skipped. K0/K1/K3/K4a/K5/K7/ch5b/
  clock-guard/ch6b/ch6 all green. States template reused (no rebuild noted).
- Container re-run of `test_k8` alone (before the G-i fix): passed, proving the order dependence.
- Scoped container run 2 at the final test revision (52190948d): run `20261109-160557-644a04`, wall 561 s, junit 358 tests,
  3 failed (exactly the stopped G-e x2 and G-h), 355 passed, 0 errors, 0 skipped. Every K file, ch5b, ch6b (with the S equality),
  ch6, k8 and all other listed files green.
- Vitest (2 files): 2 passed, 100 tests passed.
- `tools\check-all.ps1`: "All 18 guards passed." (exit 0).
- Host focused runs used `tools\run-host-tests.ps1` on `assetops_test` only.

## Known deviations
1. Spec G-d wording (`windowed_lines`) was inaccurate; the real rename is `window_link_refs` (1c3e3a075).
2. Spec G-a w403 delta guess was wrong; the real delta is migration 0051's unique key.
3. Spec G-c said 24 unpinned files; 14 were already pinned, 10 are new.
4. G-g: the test builds the s602b/S4 test-scoped Kobo, not the mechanism-dataset Kobo; "none declared" is true of that Site
   (proved from stored Foundation). The stop rule's concern (a false "none declared" about the demo Kobo) does not apply to it.
5. A temporary instrumentation (print lines in tests, a monkeypatched wrapper) was used for diagnosis and removed before commit.
6. ch6b S-equality mutation proof not run (cost).

## Residual risk
- G-e and G-h unresolved (E3 waits on the Architect per D-E2.8).
- G-e raises a product question: dispatch-derived judgements on days with no checked readings.
- The `pin_read_at` helper in `test_w301_estate_index_postgres.py` has the same import-order hole for any other test using it
  with future-dated fixtures (not changed: FR-B owns w301).

## User review
Not required by the task; Architect ruling needed for G-e and G-h before E3.

## Stop rulings applied (D-E2.9 G-e, D-E2.10 G-h)
Main 8dae46bd9 merged in (f7ad4b13c). Test-only; no product code changed.

### G-h (commit 6e886c3cd)
- `_Norm`: dict keys that are strings are normalised; `TARGET["declared_by"]` stays literal (lazy import of
  `verification_families`).
- `k6b_mill_pins.json`: mechanical transform of the d25f95ccb pins, no re-capture: 14 `grades` keys
  `"2026-10-25".."2026-11-07"` -> `"<d-14>".."<d-1>"` and 3 `"owner <d-3>"` -> `"owner 2026-11-05"`. Diff is exactly
  17 lines changed (17+/17-), nothing else.
- `test_5`: new assert that no absolute date remains in `got` (except the `declared_by` literal).
- Host run: `test_k6b_fuel_verification_postgres.py` 6 passed, no other difference from the transformed pins (stop rule
  not hit).
- Mutation proof: `TARGET["declared_by"]` set to `"owner 2026-11-06"` in `verification_families.py` -> `test_5` FAILED
  (1 failed, 5 passed); reverted with `git checkout` (tree clean).

### G-e (commit 9d04c7a30)
- Pinned `S602B_STATES` (MG-8 removed), identical on 10-06, 11-02 and the estate 10-21 board (no second constant):
  `{MG-1: NO_OBJECTIVE, MG-2: NEEDS_ATTENTION, MG-3: NOT_MEASURED, MG-4: NO_OBJECTIVE, MG-5: NO_OBJECTIVE,
  MG-6: NOT_MEASURED, MG-7: WATCH}`. `chain_day` port `{"settled": true, "readiness": "NONE", "gaps": 31}` asserted on
  all three boards. Wire reasons: MG-2 `PRIMARY_FINDING_OPEN`, MG-4 `NO_OBJECTIVE_DECLARED`, MG-7
  `EVIDENCE_READINESS_NONE` (MG-1/5 `NO_OBJECTIVE_DECLARED`, MG-3/6 `NOT_MEASURED_IN_CATALOGUE`, MG-8
  `CONFIGURATION_NOT_APPLICABLE`).
- The asserts after the loop (F01 MOVES, SAFEGUARD, Action keys, ACT index) now run and pass.
- New `test_kobo_s602b_no_judgement_on_unchecked_day`, `xfail(strict=True)` citing BL-63. Run with `--runxfail` it fails on
  `('2026-10-06', {'MG-2': 'PRIMARY_FINDING_OPEN'})`, i.e. for the intended reason.
- Host run of `test_out_b4_board_postgres.py`: 5 passed, 1 xfailed (143.67 s).

### Check-all
`tools\check-all.ps1 -Python ...plan2\.venv\Scripts\python.exe` at 9d04c7a30: "All 18 guards passed." (exit 0).

### Deviation from the ruling's premise (for the Architect)
R-1 expected `MG-4: WATCH` with reason `SECONDARY_FINDING_OPEN`. The recorded board has MG-4 = NO_OBJECTIVE
(`NO_OBJECTIVE_DECLARED`); the board's WATCH is on MG-7 with reason `EVIDENCE_READINESS_NONE` (readiness, not a
Finding). No secondary-Finding reason is on the wire. I pinned the states and reasons exactly as recorded and did not
assert `SECONDARY_FINDING_OPEN`. The product inconsistency BL-63 describes still holds through MG-2 (primary Finding
state on a NO_DATA day); the xfail guard fires on it. The "MG-4 WATCH" description in the original packet STOP section
was a mislabel of the MG-7 state.
