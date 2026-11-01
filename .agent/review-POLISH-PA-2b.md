# Review: POLISH PA-2b (plan due state and asset labels)

Reviewer: fresh Claude reviewer (not the author). Date: 2026-11-01.
Branch `task/POLISH-PA-2b-plan-due-assets`, head `3387c7101`, worktree `AssetOpsV1-polA2b`.
Diff reviewed: `git diff 816448bec...3387c7101`.
Judged against: build sheet §1.4, §3 (Asset labels), §5 Lane A PA-2, §7, Addendum 3, Addendum 6 (Q2, Q4, PA-2b scope).

## Verdict: ACCEPT

No High or Medium findings. The three Lows below do not block the merge and need no fix round. L1 is a record
correction that can be folded into the packet. L2 and L3 are notes for later slices.

## Checklist

1. **`plan_due_state`** (`backend/assetops_backend/outcomes/plan_due.py:25-33`): correct.
   - Results:
     - not CALENDAR, or no due instant: NOT_ASSESSED
     - due before `to`: OVERDUE
     - due before `to + 14 d`: DUE_SOON
     - otherwise: NOT_DUE
   - Due exactly at `to` reads DUE_SOON, which is pinned in `test_due_boundaries`.
   - `soon_until` builds the horizon as `type(to - to)(days=14)`, so `outcomes/` never imports `datetime` and stays pure (`test_out_a1_outcome_map` passes).
   - Board behaviour is the same as before:
     - `warnings._overdue` / `_plans` (`warnings.py:209-224`) give the same results as the old predicates, because every cue is already CALENDAR with a due instant.
     - `visits.warning_facts` (`visits.py:71-72`): its new filter `next_due_at is not None and state != NOT_ASSESSED` is logically the same as the old `CALENDAR and due_at and next_due_at`.
     - `test_out_c_rules.py` and `test_out_c1_never_money.py` are not in the diff and pass.
2. **Preventive read** (`work/global_index.py`): correct.
   - `summary` is counted over `rows` (the full selection) before `page` is sliced (`:527-531`), so every page repeats the same counts.
   - `due_state` comes from `hi` = `request.to` (`:418`).
   - `state_counts` stays null on preventive, because `STATE_COUNTS["preventive"]` is None.
   - Only `kind == "preventive"` gets `summary`. Incidents, maintenance and the operational branch have no `summary` and no `due_state`.
   - Selection basis: `asset_type` is added (`:432`). `due_state` and `summary` are left out, which is sound: both are functions of `next_due_at` (already in the basis) and `to` (in the token).
   - Because `asset_label` (already in the basis) now depends on the same-type count, a sibling asset retired or added between pages changes the token. That gives `WORK_BASIS_CHANGED`, which is fail-closed and correct.
   - Frontend validators accept extra keys with no change: `globalWorkClient.ts` `isEnvelope`/`isRow` (`:255-273`) and `workClient.ts` `isWorkBody` (`:110`) check named keys only.
3. **Asset labels**: correct.
   - `outcomes/asset_words.py` gives:
     - "Backup generator" only for GENERATOR on COLDCHAIN, otherwise "Generator"
     - Compressor, Battery, Connector, and the EV_CONNECTOR→"Connector" and EV_CHARGER→"Charger" deviation (accepted as builder latitude; it is what the spec's "Connector" intends)
     - the capitalised fallback for anything else
     - the code appended only when the count is over 1
   - The site type literals match the CHECK in migration 0001 (`'MINIGRID','COLDCHAIN','EV_CHARGING'`).
   - SQL scoping: every scalar subquery is tenant- and Site-scoped and keeps `retired_at IS NULL`. They are:
     - `postgres_work_read.py:77-80`: `b.tenant_id = a.tenant_id AND b.site_id = a.site_id`, where `a` is joined on `c.tenant_id/c.site_id`
     - the `site_type` subquery: `st.tenant_id = c.tenant_id AND st.id = c.site_id`
     - `postgres_global_read.py:47-49`: the same shape, with `a` joined on `h.tenant_id/h.site_id`
   - Indexes `asset_site_type` and `asset_site_retired` exist.
   - Global cases get their rows from `PostgresWorkRead.eligible_cases` (the same `_ELIGIBLE`) and pass `site["site_type"]`, so global incidents and maintenance get the count too.
   - `cold.py:143,327` now matches on the wire `asset_type`, with the same behaviour (`.upper()` kept, `_asset_type` parser removed).
   - `visits.asset_name` returns the label unchanged.
   - Search for the old form: no backend, tools or fixture code parses or builds `" · {ASSET_TYPE}"`. The only remaining parsers are `frontend/src/work/globalWorkParts.tsx:123` (`assetLabelWords`) and `frontend/src/sites/siteWorkCases.tsx:256` (`coldAssetLabel`), which PB-3 replaces. Both pass the plain label through unchanged.
4. **Out-of-scope test fixes are justified.**
   - At base `816448bec`, `operational_index.py:42` already returns `display_code(case["public_code"])`, and the global detail Action labels are display codes (PA-2a).
   - `test_w601c:653` and `test_w601e:325,329,352` still pinned the raw 6-digit code, so they fail on main.
   - The edits are mechanical, and both files pass in my run.
5. **`test_kobo_guardrail_two_board_days` under `-n 4`: a pre-existing harness collision, not this slice.** See L2.
6. **No numbers or story data tuned.** The diff touches no fixtures, goldens, `tools/` producers or numeric constants. The test fake rows were only moved to the new label and type shape.

## Findings

### L1 (Low, record accuracy): the packet's diagnosis of the B4 failure is incomplete

- **Where:** `.agent/POLISH-PA-2b-packet.md`, Checks: "It is order- or parallel-dependent, not this slice."
- **What is wrong:** the conclusion is right, but the packet names no mechanism and calls the run's result a flake.
- **What would fix it:** fold the L2 cause into the packet, and record that the scoped command needs `--dist loadfile`.

### L2 (Low, pre-existing test harness, not this slice): fixed per-case database names collide when xdist splits a module

- **Where:** `backend/tests/test_out_b4_board_postgres.py:71-80` (`_case_db`) and `:420-425` (`kobo_guardrail`, module scope).
- **Cause:**
  - `_case_db` names its database `assetops_out_b_<case>_test` with no run or worker tag, and does `DROP DATABASE ... WITH (FORCE)` on entry and on exit.
  - Without `--dist loadfile`, plain `-n 4` uses xdist's default `load` distribution. That sends `test_kobo_guardrail_closed_s2_is_partial_unknown` and `test_kobo_guardrail_two_board_days` to different workers.
  - Each worker builds its own copy of the module-scoped fixture against the *same* database name, so one worker's FORCE drop or recreate removes the other's database partway through.
- **Effect:** depending on timing, the reads either find an empty clone ("No Site KOBO-001 is configured", the implementer's result) or have their connection killed during the build. My run had the second: `ERROR ... test_kobo_guardrail_two_board_days` in fixture setup, with `EvidenceLedgerUnavailable ... terminating connection due to administrator command` from the s602b child process. The same thing could also happen between two concurrent runs on the same server.
- **Why it is not the slice:** PA-2b changes no Site lookup, no case-database handling and no fixture build. The test passes alone (packet) and in the documented `--dist loadfile` mode.
- **What would fix it:**
  - Now: always pass `--dist loadfile` with `-n` (TESTING.md already documents this).
  - Later, in a test-pipeline slice: tag `_case_db` names with the run and worker (`pg_harness` run id plus the `gw<N>` tag), as the harness does for worker databases.

### L3 (Low, dead field, preference): `WarningFacts.soon_until` is no longer read

- **Where:** `backend/assetops_backend/outcomes/warnings.py:96`.
- **What is wrong:** `_plans` now takes the horizon from `plan_due_state` (`soon_until(f.to)`), so this field is set by callers but no longer read.
- **Why it matters:** it is harmless today, because every caller passes `to + 14 d`. But a future caller that sets a different horizon would be silently ignored.
- **What would fix it:** drop the field, or assert it equals `soon_until(to)`, in a later cleanup. It does not block.

## Residual risk not named in the packet

- **Historical labels use today's asset count.** The same-type count has no cutoff (`retired_at IS NULL` now). A historical (`known_at`) read can therefore show a different label than the one shown at K if a sibling asset was retired or added since. This follows the existing q7-1 rule that asset label inputs carry no cutoff. Worth one line in the register row or in CODE_STATE.
- **Interim EV wording on Global maintenance.**
  - Before: "EV connector c2", from the old `assetWords` map.
  - Until PB-3: "Connector c2".
  - Mini generators also change from the incorrect "Backup generator · generator-1" to "Generator".
  - This is acceptable under Addendum 6 Q4, but PB-3 should make sure `assetWords` does not reintroduce "EV connector".
- **Merge risk with main `1c0ef34c3`:**
  - `git merge-tree` reports conflicts only in `.agent/mock-departure-register.md` and `.ai/CODE_STATE.md`, where both sides added rows or sections. They are mechanical to resolve.
  - Main's changes since the base touch no backend files; they are frontend and `tools/checks` (PB-1).
  - Main's `isEnvelope` is unchanged, so the validator point above holds after the merge.
  - The unmerged PB-2 branch (`908b63f24`) also edits `backend/tests/test_out_b2_mini.py` and `site_outcomes/mini.py`, so expect a small test-fixture conflict when PB-2 lands.

## Checks run (by this reviewer)

- **Pure pytest**
  - Interpreter `AssetOpsV1-plan2\.venv`, PYTHONPATH set to this worktree, and `assetops_backend` confirmed to import from `AssetOpsV1-polA2b`.
  - Files: `test_polish_pa2b_plan_due_assets`, `test_out_c_rules`, `test_out_c1_never_money`, `test_out_a1_outcome_map`, `test_out_b2_mini`, `test_out_b3_cold_ev`, `test_out_c2_board`, `test_out_c3_cold_cost`.
  - Result: **106 passed** in 3.3 s.
- **Postgres pytest**
  - Run through `tools\run-host-tests.ps1` on the shared `assetops_test` base, which uses run-owned `_pt*_test` clones.
  - Files: `test_w601b`, `test_w601a`, `test_w401_site_indexes_postgres`, `test_w601c`, `test_w601e`, `test_out_c3_repeat_visits_postgres`, `test_out_c4_ev_warnings_postgres`, `test_out_b4_board_postgres` and the PA-2b pure file, at `-n 4` without loadfile (the implementer's mode).
  - Result: **86 passed, 1 error** (`test_kobo_guardrail_two_board_days`, fixture setup, the L2 collision) in 518.6 s.
  - The new `test_preventive_due_summary_over_all_pages` and `test_plan_asset_label` passed, as did the `test_w601c`/`test_w601e` leftovers.
- **Guards**
  - `tools\check-agent-workflow.ps1`: passed.
  - `tools\check-architecture.ps1`, first run: failed only because this worktree has no `.venv`; Rule 8 reported "no Python interpreter at ''", which made every Rule 8 sub-check vacuous.
  - `tools\check-architecture.ps1`, rerun with `ASSETOPS_GUARD_PYTHON` pointed at the plan2 venv: **passed**.
- **Not run**
  - Frontend `npm.cmd test` and `build`. There are no frontend changes, and they are known not to run under the sandbox.
  - `tsc`, which is not needed because no TypeScript changed.
  - The full backend suite, which was not required. The packet records none, and none is claimed.
  - `check-all.ps1`. I ran its architecture and workflow guards, not the other 10; the packet reports 12/12 at `ed1939238`.
  - Captures, which are deferred to PA-3 (Addendum 3).
