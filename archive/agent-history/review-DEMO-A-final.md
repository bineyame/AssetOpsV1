# Review: DEMO-A final round (combined three-Site demo dataset)

Reviewer: fresh Claude reviewer (did not author the slice). Date 2026-10-31.
Worktree `AssetOpsV1-demo3`, branch `task/DEMO-A-combined-dataset`, head `e2df244c2`; main `c8702bb2b`.
Diff reviewed: `git diff c8702bb2b...e2df244c2`, focusing on `5b4713b8c..e2df244c2` (`44e54dce0`, `79dda4ea0`,
`362cfe5cf`, `e3b2caf2d`, `e2df244c2`). Specs: plan2 `build-sheet-DEMO-SPARSE.md` Addendum 4, `build-sheet-LINK-LINEAGE.md` §5,
`build-sheet-COV-PARTIAL.md` §6.

## Verdict: ACCEPT

There are no High or Medium findings. The three Lows below can be folded in or recorded. None of them blocks the merge.

## Findings

**L1 (Low, acceptance-text fidelity). CO-1 is not fully back to its original assertions.** `tools/demo_combined_finish.py:142-149`.
The original U6 `co1` (`8d613a968`) also asserted
`"Reliable service and battery and generator life" in mnh["text"]`. Addendum 3 removed that line, and `79dda4ea0` did not put it back.
LINK-LINEAGE §5 lists the assertions to make and does not name the text, so this is within the build sheet. The dispatch asked
for "CO-1 matches its original assertions", though, and it does not quite. The kept build's `check.json` shows the text is present
("Reliable service and battery and generator life are checked as safeguards when ACT-000001 is verified; ..."), so the line would pass.
Fix: add the one-line text assertion back.

**L2 (Low, test strength, not a regression). CO-1's "ACT on the Cost row" check does not tell a linked Action from the old state.**
`tools/demo_combined_finish.py:145-147`. `on_cost_row` is built over `items(cost)` (`:94-95`), which includes `earlier`. Before
LINK-LINEAGE, the Action already appeared in `earlier` through CO-3's verification line (Addendum 3's own comment said so), so this
assertion alone would have passed without the refresh-lineage link. The original assertion had the same form, so this matches the
original. The discriminating check is the `must_not_harm.href` assertion at `:144`, and that one does fail on the old behaviour. Fix
(optional): restrict `on_cost_row` to `issues` + `in_hand`. Those are the lists that Addendum 3's negative assertion targeted.

**L3 (Low, records). Register and CODE_STATE text from the merge is now stale.**
- `.agent/mock-departure-register.md:539` R535. The row keeps this branch's earlier narrative and status: "the week reads PENDING ... no
  runtime path runs `ColdConsequenceWorker`", status "open (CO-6 fails; needs a ruling on the cold drain)". FIX-COLD-DRAIN merged, and
  CO-6 now passes with the week PARTIAL. The status is false today.
- `.agent/mock-departure-register.md:552` R552. The narrative still says "on day S the Action is still absent from the Cost row ... a
  narrow board rule is with the owner". LINK-LINEAGE merged and CO-1 now passes. The status cell is main's, which is correct.
- `.ai/CODE_STATE.md:6251-6252`. The header says "main `15eed62c8` merged" and "Addenda 1-3". The final-round bullet below it is
  correct (main `c8702bb2b`, Addendum 4).
Resolved rows were checked and stay resolved: R613 (COV-PARTIAL form), R623, and R569 (resolved by DEMO-A). Each ID appears exactly
once. The DEMO-SPARSE R615-R619 block and main's R620-R624 blocks are both present. Fix: when the coordinator closes R535 and R552,
replace or append the narrative, and update the CODE_STATE header line.

## The dispatch's specific checks

- **No assertion loosened relative to `5b4713b8c`, apart from the SP-7 change Addendum 4 authorises.** Confirmed.
  - CO-1 went from the Addendum 3 negatives back to positive assertions, as LINK-LINEAGE §5 requires: the href holds the Action id and
    `/verification?event_id=`, the Action is on the Cost row, `outside == []`, and the MG-2 reason is one of
    {PRIMARY_FINDING_APPLIED→WATCH, OBJECTIVE_MISSED→NEEDS_ATTENTION} with `cost.state` asserted to match. It returns
    `r552: "resolved: refresh lineage"`.
  - CO-6b gains `gaps == []`.
  - SP-7 keeps the refusal, the gap-to-assessed check, `S2 - S == 1 d`, and the 1-day move for non-weekday Sites.
  - The build-test rows now assert `status == "pass"` from a fresh `finish check`. That is stricter than the old in-process read: a
    "skipped" row now fails unless `needs_v2` skips it.
- **CO-6 is derived per COV-PARTIAL §6.** Confirmed (`tools/demo_combined_finish.py` `co6`).
  - `state == "PARTIAL"`.
  - The gap days equal `unassessed`, which is computed from `days.json` runs.
  - `checked == 7 - g` and `requested == 7`.
  - The text is built from the product's `DAYS_CHECKED` template, with `DAYS_WITHHELD` added only when the Site is withheld.
  - The status is in {PARTIAL, UNKNOWN} and is not CURRENT.
  - Kobo's Finding is in the rows unless the Site is withheld.
  - Everything else in the row is unchanged. No value is a literal fitted to output.
- **SP-7 matches Addendum 4, computes its expected values, and can fail.** Confirmed
  (`backend/tests/test_demo_combined_postgres.py:184-213`).
  - It is keyed on `sd.SITE_WEEKDAY`, not on the literal `"ev"`.
  - It pairs resolved days with the listed entries in order, and checks the count.
  - On both S and S' it asserts the weekday, the `(S + n - 7 d, S + n]` window, the `weekday_offset` result and the kind.
  - The 1-day move is limited to the non-weekday Sites.
  - It holds no literal dates or offsets.
  - Independent check: a scratch replica of the comparison passes on all seven S weekdays from 2026-10-25, including the Tuesday
    crossing at i=3. It fails on the weekday assertion when EV's resolved days are shifted by one day.
  - The offset assertion uses the same `weekday_offset` that the resolver uses, so taken alone it is close to tautological. That is
    the formula Addendum 4 prescribes, and the weekday and window assertions are independent of it.
- **Harness, Addendum 4's three points:**
  1. **A child's non-zero exit or unparseable output fails the row.**
     - `_get` (`:92-107`) fails the row on `returncode != 0`, on anything other than exactly one JSON line, and on JSON without
       `status_code`/`body`.
     - `checked` (`:115-137`) unlinks `check.json` first, so a stale file cannot be read. It then fails every row when:
       - the exit is outside {0, 1};
       - `check.json` is missing or unreadable;
       - a non-mutating row is missing;
       - the exit code disagrees with the row results.
     - An uncaught exception in the child exits 1. Because `check.json` was unlinked before the run, that case also fails.
     - A wall-cap `SystemExit` fails the row (`:82-89`).
  2. **The `.busy` release cannot hide a prepare failure.** `_release_busy` runs in the inner `finally` (`:55-58`). It returns early
     when `holds_busy` is false, so it never removes another holder's `.busy`. It catches only `OSError` and prints it. It cannot
     raise, so a prepare exception propagates unchanged. If the release fails, SP-7's add-day refuses with the `.busy` message, so the
     failure stays visible. This mirrors `tools/demo_combined.py:569-572`.
  3. **The child reads the same store the demo serves.** The child runs `d.tree/tools/demo_combined_finish.py` with `Demo.env()`,
     whose PYTHONPATH is all under `d.tree`. That is the same child, tree and environment the prepare's own self-check uses
     (`tools/demo_combined.py:343-344`), and the same tree `serve` runs from (`:466-473`). The file stores resolve `REPO_ROOT` from
     `__file__` (`backend/assetops_backend/config.py:20` and the adapters), so they are the tree's. The prepare's import probe
     (`tools/demo_combined.py:285`) refuses a build whose import resolves outside the tree.
- **No story inputs, numbers or product code tuned.**
  - `git diff c8702bb2b e2df244c2 --stat` touches no product code: only `tools/`, `backend/tests/`, `backend/conversions/demo-*`, and
    records.
  - `tools/demo_combined*.py` (other than `_finish`), `tools/demo_story_days.py` and `backend/conversions/` are unchanged in
    `5b4713b8c..e2df244c2`.
  - The backend and frontend product changes in that range all come from the main merge.
- **Merge resolution.** Both sides are kept, and resolved rows stay resolved (see L3 for the stale narrative).
  `.ai/ACTIVE_CONTEXT.md` and `.ai/CODE_STATE.md` keep main's entries and add DEMO-A's.

## Checks run

- `powershell -NoProfile -File tools/check-architecture.ps1`: "Architecture check passed." This was run without
  `-ExecutionPolicy Bypass`, as the dispatch requires.
- `powershell -NoProfile -File tools/check-agent-workflow.ps1`: "Agent workflow check passed."
- `.venv\Scripts\python.exe -m pytest backend/tests/test_demo_story_days.py -q`: 19 passed in 0.16 s.
- Scratch SP-7 replica (pure Python, no DB): passes on 8 consecutive S and catches the mutation. The script is
  `C:\Users\assef\AppData\Local\Temp\claude\C--Users-assef-Bineyame-AssetOpsV1\809ecc09-3853-48b6-b795-60539b50a963\scratchpad\sp7.py`.
- Kept build `var/demo3_full/check.json` (code `79dda4ea0`): 17/17 pass, `idx_present` true. CO-1 reads NEEDS_ATTENTION with MG-2
  `OBJECTIVE_MISSED`, and the href carries `/verification?event_id=`.
- Cited, not rerun: the `-Tier all` run `20261031-224858-fd387f` JUnit reports tests 4688, failures 0, errors 0, skipped 0, time
  2586 s. It includes all 19 `test_demo_combined_postgres` cases. `run-options.txt` does not record the revision. The packet says
  `e3b2caf2d`, and `e3b2caf2d..e2df244c2` changes only the packet, `ACTIVE_CONTEXT` and `CODE_STATE`, so the result applies to the
  head under review.

## Not verified

- I did not rerun the slow build test (`-m slow`, one prepare of about 15 min). I relied on the implementer's 941 s run (19/0) and on
  the `-Tier all` run above.
- I did not run the frontend suite or build. The slice has no frontend changes against main, and the sandbox cannot run them on this
  machine anyway.
- Layout evidence is not applicable: the slice is not layout-sensitive.
- The packet's fake-child exercises of the harness failure paths: I checked them by reading the code, not by rerunning them.

## Residual risk

- Reads go stale 300 s after the last tick. The packet records this: run `serve` or `tick` before a demo.
- The [IDX] rows still rely on `needs_v2` skipping when IDX-GAPS is absent. On this tree IDX is present, so nothing skips. The
  `-Tier all` run confirms skipped 0.
