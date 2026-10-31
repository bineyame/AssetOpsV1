# LINK-LINEAGE review

Reviewer: fresh Claude, 2026-10-31. Reviewed the `git archive 9cbd7f299` snapshot (branch
`task/LINK-LINEAGE-board-action`; the base for the diff is `0796218fc` = main `15eed62c8` + build sheets). The worktree was not touched.
I judged it against `build-sheet-LINK-LINEAGE.md` §0-§7 and the owner's "yes to both, go ahead"
(`owner-client-demo-sequence-2026-10-31.md`, decision 1).

## Verdict: ACCEPT

The rule is implemented as the sheet specifies, it stays narrow, and it fails closed. All tests I ran passed, and
planting a broken check makes the tests fail. There are no High or Medium findings. The two Low findings below are optional
hardening and do not block the merge. The merge gate is still the implementer's `-Tier all`, which has not run yet.

## What I checked

- **The rule stays narrow.** `board.py:466-489` `refresh_chain` breaks the chain in each of these cases:
  - empty or None history (`:472`);
  - the origin or the shown revision is absent (`:475`);
  - origin >= shown (`:477`);
  - contiguity: the numbers between them must be exactly `o+1..s` (`:479-482`, which also rejects duplicate numbers);
  - a transition other than BASIS_REFRESHED, a lifecycle change, or a change to the episode start or end (`:486-488`).

  Rows after the shown revision are filtered out before any decision (`<= s_no`). The port does fetch every page, including
  rows after the shown revision, because `FindingReadService.history` has no replay. But they are never used, as sheet §2 says.
- **Where the lineage is used.** `linked_actions` (`board.py:499-502`) is used only at the applied signal (`:509`)
  and at Must-not-harm (`:640`). The Earlier lists still join on `origin_finding_id` only (unchanged). `estate/**` is not in
  the diff. Cold and EV build `FindingFact` positionally (`cold.py:214`, `ev.py:245`), so `refreshed_from` keeps its default `()`, and
  domain Actions are filtered out anyway (N6).
- **Failure safety.** `_lineage` (`mini.py:502-515`) goes through `reads.call`. A raise is recorded in `failed`, which makes the
  board PARTIAL (M3), and the None result links nothing. A closed finding-index gate raises PortUnavailable (`read.py:259`, M6b). A
  `history` body of None (an unknown Finding or revision) returns None. Nothing links and no failure is recorded, which matches
  sheet U2. No path produces a link without a proved chain.
- **One read per Finding, only when needed.** The history is read only when some non-domain Action points at the same
  Finding with a different, non-empty origin revision. M1 (exact match: never called) and M5 (two Actions: one call) cover this.
- **Wiring.** `main.py:622-623` passes `finding_reads=finding_reads` into `composition.py:55,70` and then to
  `BoardServices.finding_reads` (`read.py:93`). The AST test confirms that this is the app's single instance.
- **No UI or mock change.** The diff touches only `backend/`, `.agent/`, `.ai/` and `tasks/`. Nothing under `frontend/`.
- **DECISIONS.** The §7 entry is verbatim. The R552 note is appended and R552 stays open, as sheet §3 U3 says.

### The two packet deviations

1. **Where the M6b gate test lives** (`test_out_b2_mini.py`, not the b4 binding files). This is acceptable. The test goes through
   the real `SiteOutcomeBoardService.mini_ports` binding with a closed gate. Without a DB the app's `finding_reads` is
   None, so the binding file could not have exercised the gate meaningfully. The instance identity is proved separately (AST plus a
   composition sentinel).
2. **U3 takes the origin and shown ids from a spy.** Acceptable, with Low finding L1. The link decision is independent of the
   code under test: `_expected_link` (`test_out_b4_board_postgres.py:337-360`) re-reads the history over HTTP
   (`/findings/{id}/history`, every page) and applies its own loop, not `refresh_chain`. The inputs, however, are what the
   composer passed to `_lineage` (`:319-334`): the shown revision, the origin revision and the expected href. They come from `_findings`/`_actions`.
   That parsing is older than this slice, but it is still composer output. If the origin were mis-parsed (None or wrong), the test
   would compute `False` and agree with a board that does not link.

### b4 and e4 pins against the sheet

I reran these myself. The UUIDs differ from the packet because the fixtures are rebuilt each run. The shapes match the packet's U3a table:

| Board | Shown | Origin | Between | Chain | Must-not-harm |
|---|---|---|---|---|---|
| guardrail Day A 2026-10-06 | aed1be80 | none (action_index 0 rows that day) | - | false | None |
| guardrail Day B 2026-11-02 | aed1be80 | 1ee70285 (INEFFECTIVE) | (2, BASIS_REFRESHED, SUPPORTED) | true | ACT-000001 safeguard text + `/actions/4e38bb19.../verification?event_id=...` |
| e4 verified | 16f2d6ac | c3c22a55 (VERIFIED) | (2, BASIS_REFRESHED, SUPPORTED) | true | ACT-000001 safeguard text + verification href |

This matches the sheet:
- §3 U3: the rule is computed inline from the history route, and when the chain is false the assertion is None.
- §5/§6: Day B gains the Must-not-harm line. That is R552's subject.

The other Day A checks (moves and checked) are retained in b4 (`:495-502`). The only deleted assertion is
`cost["must_not_harm"] is None`, which the rule-driven check now replaces. The comments now cite this slice.

## Findings

- **L1 (Low, test strength; not an acceptance gap).** `test_out_b4_board_postgres.py:363-375`, used at `:459` and at
  `test_out_e4_readback_postgres.py:69`.
  - **What is wrong:** the Postgres pin accepts either branch. Both of the following come from the code under test:
    - the origin revision (the composer's `ActionFact` via the spy);
    - the expected href.

    So a regression that drops or mis-parses ACT-000001's origin on Day B or e4 would turn the board's Must-not-harm into None. The test
    would then compute `false` and still pass.
  - **Why it matters:** the sheet allows a branch-agnostic assertion. Now that the branch is recorded (Day B true, e4 true), it can
    be pinned.
  - **Fix:** add `assert linked` for `kobo_guardrail_day_b` and `out_e4_verified`. Alternatively, take the origin from the Action
    read route rather than the spy. DEMO-SPARSE CO-1 will pin it on the combined dataset in any case.
- **L2 (Low, robustness).** `mini.py:513`.
  - **What is wrong:** `refresh_chain` runs outside `reads.call`. A history row without `revision_no`, or with a value that is not an
    int, would raise in the composer. The board would then fail instead of going PARTIAL with no link.
  - **Why it is only Low:** the real `FindingReadService.history` always emits an int `revision_no`, so this cannot happen today.
  - **Fix (optional):** compute `refresh_chain` inside the `reads.call` lambda, or treat a malformed row as `False`.

The pure test P3 is the only test that catches reading past the shown revision. The planted break described below confirmed this. M6 has no
"later SUPPORT_CHANGED after the shown revision" case through the real reader. That is a coverage note, not a finding: the pure rule is
pinned.

## Checks run (on the snapshot, plan2 venv)

- **U1+U2 sets** (12 files: `test_link_lineage`, `b1_board`, `c2_board`, `d4_board`, `idx_gaps_board`, `b2_mini`,
  `b2_vocabulary`, `b4_read`, `b4_route`, `b4_imports`, `b4_main_binding`, `e4_readback`): **161 passed**, 23.4 s.
- **Postgres** `test_out_b4_board_postgres.py` + `test_out_e4_readback_postgres.py` (`ASSETOPS_TEST_DATABASE_URL` = `assetops_test`): **6 passed**, 463.6 s. The records are in the table above.
- **Planted break 1:** I removed the lifecycle check in `refresh_chain`, on a separate copy of `backend`. Three tests failed: N2, M2b and M6. The packet's
  claim is confirmed.
- **Planted break 2:** I let `refresh_chain` read past the shown revision (I dropped the `<= s_no` bound). P3 failed and nothing else did (see the coverage note above).
- **Guards:** `tools\check-all.ps1 -Python <plan2 venv>` on the snapshot: **all 11 guards passed**. Note one
  skip: the missing-claim scan's merge-base baseline comparison did not run, because the snapshot has no git, so only its
  seed ceiling of 16 applied. In the worktree that comparison does run.
- **Not run:**
  - `-Tier all`. That is the implementer's merge gate, and it is still pending per the packet.
  - Frontend. There is no frontend change, so it is not applicable.

## Residual risk (beyond the packet)

- The history port fetches every page of a Finding's history, including revisions after the shown one. The cost is bounded by one
  read per Finding with a non-exact Action, but a long-lived Finding with many revisions pays the full read on every mini
  board.
- Out-of-window Findings that are read only to resolve a link also trigger the read. This is correct, because `moves_here` includes them for
  Must-not-harm.
