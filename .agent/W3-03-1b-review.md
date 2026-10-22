# W3-03 run 1b (and the r1a fix) — independent review

Reviewer: fresh Claude reviewer (did not author any of the commits). Branch `task/W3-03-portfolio-composition`, head
`271577c6`. Range `565335aa^..271577c6`, excluding `.agent`: the 1a fix `565335aa`, Lane A `06acf1cf`/`f5407e95`,
Lane B `f3f04ef6`/`3a0d96bc`/`6c4e0449`/`0f29d4cb`, and r1b2 `271577c6`. I read the code through git, not the
worktree. Spec: `.agent/W3-03-build-spec.md` closure 4 run 1b, closure 5 S7, r1a (Q-1a-1 and the readings), r1a2, r1b
and r1b2. I did not re-argue P-1b-1..6, which are with the Architect (r1b3).

## Verdict: ACCEPT

There are no High or Medium findings. The six Low findings below are cleanup items or need Architect
ratification. None of them blocks Lane A from mounting the API.

## Checks I ran

All of these ran on my own detached worktree of `271577c6`. PYTHONPATH pointed at that copy's
`backend`, `backend/tests`, `contracts`, `gateway` and `simulator`. The database was a private
`assetops_w303rv_test`, which I created and then dropped. The worktree has also been removed.

- **Pure tests:** `test_w303_portfolio_workflow_labels.py`, `test_w303_portfolio_reduction.py`,
  `test_w303_estate_cursor.py`, `test_w303_portfolio_api.py` and `test_w302_estate_cursor.py`. Result: **110 passed**
  in 20 s. This includes the builder test on the database.
- **Persisted tests, with keep-awake running, `-n 2 --dist loadfile`:**
  - W3-03 files: `test_w303_portfolio_comparison_postgres.py`, `test_w303_portfolio_scope_snapshot_postgres.py`,
    `test_w303_portfolio_fixture_postgres.py` and `test_w303_selectors_postgres.py`.
  - W3-01 golden: `test_w301_estate_golden_postgres.py`.
  - W3-02 files: `test_w302_money_comparability_postgres.py`, `test_w302_evidence_scope_snapshot_postgres.py`,
    `test_w302_financials_links_postgres.py` and `test_w302_money_api.py`.
  - Result: **49 passed**. JUnit: tests=49, failures=0, errors=0, skipped=0. Wall time 20 min 42 s.
- **`tools/check-all.ps1` in the review checkout:** **all 11 guards passed.** This covers architecture seams,
  agent workflow, navigation, the registry and the screen ledger. The same scripts failed when run from my temporary
  worktree: Rule 8 reported "vacuous" checks, and the Screen ledger could not find `.venv`. That is a side effect
  of the temp path and the missing venv, not of this code. The file Rule 8 checks does contain the INSERT it
  looks for.
- **Frontend:** not applicable. The diff changes no frontend file, so I did not run `npm.cmd test`, the build or
  `tsc`.
- **Full backend suite:** not run, as for this slice the handoff says the full suite is a run-3 step. The packet
  cites no same-revision full suite, so the full suite on `271577c6` has not been verified.

## Focus items

- **The 1a fix (`565335aa`) is correct and tested.**
  - `summary.finding_count` is null unless F is COMPLETE or EMPTY.
  - `test_foreign_tenant_missing_site_and_grant_fence` takes its clean baseline before `add_empty_site`. It asserts
    a null count beside `total_count == len(clean_rows)`, and that the clean count equals the clean rows.
  - The same rule now covers `opportunity_count`.
- **`_selected_recorded_at` and the comparator have no fallback.**
  - Lane A sets the field from `lifecycle.ordered(...)[-1]`, which is the selected event. The selectors test
    checks it against the stored `action_event.recorded_at`.
  - `_action_for` raises `ActionSelectionError` if any match lacks the time, then takes the minimum of
    `(-time, action_id)`.
  - The tie test covers: a later event winning despite a later ID, equal times choosing the smaller ID, a different
    revision not joining, and the missing-time error.
- **The signed cursor is correct.**
  - The API checks the key after `parse_request` and before `store.read`.
  - `parse_request` checks only the envelope, so a malformed envelope returns 422 even with no key.
  - A well-formed envelope with a wrong MAC returns 503 when there is no key and 422 when there is one.
  - The MAC is checked with `compare_digest` before `_shaped` and before any field is used.
  - The test counts store reads and shows zero reads for page one, page two and an empty scope, satisfying R1 and
    R2.
  - Tampering is refused with 422: a flipped `page_one_mode`, a changed `known_at`, a changed `after`, an extra key,
    a key from another signer, and an uppercase or short MAC.
  - A validly signed cursor with a changed grant or selection returns 409.
  - The test hashes the old cursor bytes with SHA-256 for Findings, Actions, Evidence and Financials. They are
    unchanged with and without the key.
  - The key validation matches the ruling: exactly 64 ASCII hex characters, and no default.
- **`workflow_label` matches the r1b Q-1b-2 table row for row.** "Outcome pending" requires `_verification_window`
  and no RESOLVED state. Both controls are covered: an active plan with a null outcome, and a null outcome with no
  plan.
- **`_pending_guard` behaves as ruled.**
  - It is set for a cold window that is `withheld` and for an EV `ERROR_PENDING`, whether or not a line exists.
  - It is set before the EV `continue` for a window with no history.
  - It is false for mini-grid Sites, sites outside the slice, `STALE_BASIS` and a missing pin.
  - `money_pending` combines the guard with the line rule, so PENDING outranks UNKNOWN after the EMPTY_SCOPE and
    HISTORICAL checks.
  - The persisted line-less cold variant `a_lineless_cold` passes.
- **The projections cover what the v69 mock needs.**
  - The five cards follow the closure-1 table. Historical lines are `HISTORICAL_E`, so the card is WITHHELD and
    historical money never shows as current.
  - The matrix has one item per authorized Site with five fixed cells, the N5 reasons and null destinations.
  - The prompt follows N5 precedence, skips gaps with a null step, and carries `site_code`.
  - `progress` has 10 fields and counts only when Action coverage is complete.
  - `money` is the unpaged W3-02 groups, exclusions and diagnostics, with `estate_total:null`.
  - The footer requires an exact quantity and amount, ELIGIBLE, and a non-null `links.evidence` that is not the
    current view.
  - The opportunity and summary keys are present.
  - The persisted page-size test shows that all of these are equal at limits 1 and 100, and that they match the
    public W3-02 roots.
- **`origin_revision_selected` is computed correctly.** It comes from the full `f_rows` before the lifecycle, lens
  and page filters. The pure test checks both values. The persisted B4 test checks `false` against the public Finding
  root; the persisted `true` case is P-1b-6.
- **Provenance is read in one batched query.**
  - `link_rows_many_on` is a single `unnest(sites, ids)` query that shares `_links_sql`. The single-Site SQL text is
    unchanged.
  - The test counts exactly one batched statement at both limits.
  - Each Site's DTO equals the single-Site `cited_provenance` result for that Site, so mixed-source classification
    and the digest are preserved.
- **The B4 `[11-01,11-03)` proof is real, not vacuous.**
  - It uses one request window with successive cutoffs, driven by the producer (`bound_plan`) and the evaluator
    (`evaluate` twice). No resolution is appended by hand.
  - At each cutoff it captures and checks the single selected full-scope Action: event, plan and outcome IDs and
    times against the stored rows and the Action root.
  - Control cutoffs a microsecond before the plan window and before the decision read `Applied`, so "Outcome
    pending" is not being inferred from a null outcome.
  - Earlier cutoffs are re-read after the later records exist.
  - The Finding-row label loop finds no row, which B4 allows.
- **The W3-01/02 wire bytes are unchanged.** The W3-01 golden, the W3-02 comparability, money API, evidence-scope and
  financials-link tests, and the cursor-byte SHA-256 test all pass on `271577c6`.
- **No debug code was left in production files.** The test files have a few diagnostic prints, covered in L4.

## Findings

### High
None.

### Medium
None.

### Low

**L1. Lane B edited Lane A's files under an assignment that was only implied (needs Architect ratification).**
- `271577c6` is a Lane B r1b2 commit. It edits Lane A's exclusive `estate/adapters/postgres_estate_read.py`
  (closure 4 B1/B2).
- It also changes the shared `estate/composition.py::build_estate_read` and `build_estate_evidence_service` (lines
  43 and 65). r1a2 L1 granted Lane B only the additive `build_estate_portfolio_service`.
- It also edits `evidence/adapters/postgres_evidence_ledger.py`, `evidence/composition.py` and the W3-02 fixture
  `test_w302_evidence_scope_snapshot_postgres.py:51`.
- r1b2 "Build impact" puts R11 in run 3b, which is Lane B, and the handoff cites the coordinator's "apply every
  r1b2 change". But no ruling names the editor for these files.
- The edits are additive and the bytes are proven unchanged, so this is not a correctness problem.
- Fix: the Architect ratifies the file ownership in r1b3, or Lane A re-signs these hunks.

**L2. The batched provenance read can fall back to per-Site queries without anyone noticing.**
- If a requested ID is missing from the batch, `_Prefetched.link_rows` (`postgres_estate_read.py:30-40`) quietly
  falls back to one query per Site.
- The R11 test (`test_w303_portfolio_scope_snapshot_postgres.py:343`) checks that the batched statement count is 1
  and that the single-ID `AS q(id)` count is equal at limits 1 and 100. A per-Site fallback would also be equal at
  both limits, so the test would not catch one.
- With the current SQL the fallback cannot happen: a LEFT JOIN over the requested IDs always returns every ID. So
  this is a gap in proof, not a defect.
- Fix: assert that the fallback is never used, or remove it. For example, count `AS q(id)` statements with and
  without the scope disclosure, or patch the fallback to raise in the test.

**L3. The spec gives two different rules for which Site the evidence prompt picks.**
- r1b "Matrix and prompt" says "the lexically first eligible Site ID in that gap".
- Closure 4 N5 says to use the group's `(site_code_key,site_id)` order, "not lexical Site UUID".
- The code (`portfolio.py:341-351`) and both tests follow N5.
- r1b2 R9 "confirms" this behaviour, but the r1b sentence was never withdrawn.
- No code change is needed. The Architect should strike or correct the r1b sentence so that run 2 does not
  re-derive the rule.

**L4. Leftover test output and a cosmetic artifact.**
- `test_w303_portfolio_scope_snapshot_postgres.py:389, 439, 479` add three diagnostic `print(...)` calls. pytest
  captures them, and the 1a L4 print is a precedent.
- `test_w303_portfolio_workflow_labels.py:43, 49` contain `==         "..."`, where a line continuation was
  collapsed into a run of spaces. The lines are about 130 characters long but still valid.
- Fix: optionally remove the prints and restore the line wrap.

**L5. A test comment cites the wrong ruling.**
- `test_w303_portfolio_comparison_postgres.py:163` says the persisted `True` case is "pending ruling P-1b-5".
  The pending-rulings file calls it P-1b-6.
- Fix: correct the comment.

**L6. The handoff file's encoding was corrupted (`.agent`, outside the code diff).**
- `.agent/W3-03-phase-handoff.md` gained a UTF-8 BOM.
- Its existing em dashes were turned into mojibake: "â€”" appears in four run headings.
- Fix: rewrite the file as UTF-8 without a BOM and restore the dashes.

## Residual risk the packet does not name

- **No persisted proof of a successful join.** Every persisted fixture has no Action joined to a selected Finding
  revision: the 10-06 window has no Action, and in November the origin is not selected. So `_action_for`,
  `workflow_label` on a Finding row and `origin_revision_selected=true` are proven only by pure tests.
  - The ID types line up: both sides are `str(...)` UUIDs in `coverage.py`.
  - A persisted proof still depends on P-1b-6.
- **`ActionSelectionError` would surface as a 500.** It is unreachable today, because `coverage.py` always sets the
  time, and the ruling accepts an internal error here. Run 2 should not mistake a 500 from this source for a store
  outage.
- **The key is read twice in a request.** `portfolio_cursor_key()` is read from the environment at the API
  boundary and again inside `_scope`/`_cursor`. If the key is changed in the middle of a request, that one request
  could return a 503 or issue a cursor signed with the new key. This is acceptable for a deployment setting.
- **No full backend suite on `271577c6`.** It is still owed in run 3.
