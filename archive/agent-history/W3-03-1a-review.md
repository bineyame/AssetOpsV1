# W3-03 run 1a — independent review

Commit `450f5f9f` on `task/W3-03-portfolio-composition` (parent `5456b7fa`). I read it through git only and ran the tests in a separate detached worktree on a private `assetops_w303rv_test` DB. The DB has been dropped and the worktree removed.

**Verdict: REVISE.** The fix is small: one Medium finding (M1), to be fixed on the branch. Everything else meets the 1a contract.

## Checks run (my own runs)

- Pure tests: `test_w303_portfolio_api.py`, `test_w303_portfolio_reduction.py`, `test_w303_estate_cursor.py`, `test_w302_estate_cursor.py`, `test_w301_estate_api.py`, `test_w302_evidence_api.py` and `test_w302_money_api.py`. Result: **134 passed**, matching the packet.
  - A first attempt failed 5 tests on an import error. The cause was environmental: the installed `assetops_contracts` and `assetops_simulator` resolve to the main checkout. Putting the worktree's `contracts`, `simulator`, `gateway`, `host` and `backend` on PYTHONPATH fixed it. It is not a defect in the slice.
- `test_w303_portfolio_scope_snapshot_postgres.py` on the 0b fixture: **2 passed in 182.5 s**. The L4 output was `{'cold_chain': 3, 'ev_charging': 6, 'mini_grid': 3, 'actions': 1}`, which is 12 calls for the three selectors, in 1 snapshot.
- `tools/check-architecture.ps1`: **passed**. It needs `ASSETOPS_GUARD_PYTHON` in a worktree that has no `.venv`; without it, Rule 8 fails only because it cannot find Python. `tools/check-agent-workflow.ps1`: **passed**.
- Frontend: no frontend files changed, so I did not run `tsc`, `npm test` or the build. Layout evidence does not apply to a backend-only run.
- Full backend suite: not rerun. Run 3 owns the same-revision full suite.

## Scope verified

- **S4 reductions.**
  - `reduce_units` matches the four-row table exactly. N units are ignored, and an all-N scope gives COMPLETE.
  - `evidence_unit` and `money_units` follow the E and M tables.
  - The 41 tests break down as 28 table cells, 10 unsettled inputs, and 3 tests for the E, M and base tables. They are not vacuous:
    - every E/M row except the unproducible E-row-1 N is driven with an input that flips the class;
    - the class "UNKNOWN or CONTRADICTORY readiness beside a selected capability" is tested;
    - "a covered EV Site beside an uncovered one gives PARTIAL" is tested.
  - I checked whether a W1 non-current day could keep a FULL/LIMITED readiness. It cannot: `claim_limit_read.interval_state` makes any non-CURRENT interval UNKNOWN, and `reduce_day` propagates that. Reading `readiness` is therefore safe.
- **Rows.**
  - Lifecycle membership is `SUPPORTED|UNCONFIRMED`, applied after full selection and before paging.
  - The server-side lens comes from `LENS_FLAG`.
  - Re-sort order: nonnull episode descending, nulls last, then `(site_code_key, site_id, finding_id, finding_revision_id)`.
  - The row has stored uppercase `domain`, `episode_end`, null `mechanism` and the N7 consequence fields copied.
  - The Action join uses the exact pair. Links are built with `quote(code, safe='')`, and the Finding route is given for MINIGRID only.
  - The persisted test compares rows field by field against the public Findings root.
- **Token.**
  - One `estate-selection/2` item per Site, built from the Finding-domain `site_coverage` base.
  - Arrays are unions of the full Finding cov, the Action cov, and the Evidence and Financials arrays, built exactly as `_evidence` and `financials_body` build theirs. MERGED heads are included.
  - Lens-bound, with `state_filter: null` and `token_k`.
  - The pure test recomputes the literal token. A changed MERGED revision that is not on any visible row fences page two.
- **Cursor.**
  - Five-member marker, plus `kind`, `lens`, `state_filter: null` and `page_one_mode`.
  - Fences run in this order before `resume_after`: grant/access, window, cutoff, lens, token. A well-formed nonmember marker gives 422, and malformed markers give 422 at the parser.
  - A historical page one stays HISTORICAL on page two. A live continuation with a captured earlier cutoff stays CURRENT and uses `snap.basis_historical`.
- **Refusal router.**
  - It has the same shape as `estate_evidence_money_api.py`: 401 with `WWW-Authenticate: Bearer` before parse or read, then the strict parser, `INVALID_LENS`, 503 (store down or no DB), and 409 after one retry.
  - Every `detail` carries `rows, total_count, value_cards, objectives, money` as null, and no success fields appear on error.
  - There is no 403/404 path. The router is not mounted (`main.py` is untouched).
- **Read-only, one snapshot.** `view.snapshots == 1`. There is no write and no second connection. The repetition is the L4-bounded 12 calls, plus one Action call for the single mini-grid Site.
- **No W3-01/02 wire change.** No W3-01/02 module changed. The only edit to an existing file is the additive builder in `composition.py`; see L1.
- **Public surface and fixture.** The persisted tests drive the unmounted router through TestClient and the public Findings/Evidence/Financials services on the 0b `build_portfolio_fixture`.

## Findings

### High
None.

### Medium

**M1 — `summary.finding_count` is never null on partial Finding coverage** (`backend/assetops_backend/estate/portfolio.py:225`, `summary = {"finding_count": len(members)}`).
- **What the spec says:** the main spec wire section says `summary.finding_count` "is the complete W3-01 all-lens count only on complete Finding coverage; if partial it is null". It adds "A null count never renders as `0`", and the refusals section requires "null full-estate counts" for partial or pending states.
- **Closure 1 does not supersede this:** it defines the count as "the full-scope all-lens count after the lifecycle filter". That says what is counted, not when the count is nulled.
- **Why it matters:** in the persisted empty-Site variant (`finding_state=PARTIAL`, status UNKNOWN), the response reports the covered Sites' row count as the estate Finding count. This is an estate-total claim the contract withholds, and 1b/2 will render it.
- **Fix:** emit `None` unless `states["F"] == "COMPLETE"`; consider `"EMPTY"`, where the complete-empty rule gives 0. Assert `partial["summary"]["finding_count"] is None` in `test_foreign_tenant_missing_site_and_grant_fence`.
- `total_count` is correctly left as the selected row count (reading 7).

### Low

**L1 — Lane B edited an existing file** (`backend/assetops_backend/estate/composition.py:71-78`, `build_estate_portfolio_service`).
- Closure 4 B1/B2's Lane A sole-editor list does not include `composition.py`.
- Closure 1 (Q34) says "`estate/composition.py` owns the connection-taking builder", so the location is authorised. The lane assignment is not stated.
- The edit is additive and leaves no W3-01/02 builder changed. The Architect or the Lane A coordinator should confirm it before the 1b release.
- No test exercises the builder. The persisted test builds `EstatePortfolioService(evidence_read(engine))` directly.

**L2 — One partial-variant assertion compares Portfolio with itself** (`backend/tests/test_w303_portfolio_scope_snapshot_postgres.py`, `assert sorted(_pairs(partial["rows"])) == sorted(_pairs(view.ok(**fx.window, limit=100)["rows"]))`).
- Both sides are the same post-perturbation read, so the assertion is vacuous.
- The intent, that adding the empty Site leaves the selected rows unchanged, needs a comparison with the clean `limit=100` rows captured before `add_empty_site`.

**L3 — The r0a M1 "unselected EV Site gives M PARTIAL" proof is pure only.**
- r0a M1 says "Run 1a then asserts the unselected EV Site variant reduces M to PARTIAL". 1a proves this with fake covs in `test_money_table`.
- The persisted partial variant uses a mini-grid empty Site, copied from KOBO.
- This is acceptable under closure 5 S4, which gives persisted variants to 1b. Record that the persisted EV-Site M PARTIAL assertion is carried into 1b.

## Builder readings: notes only (the Architect rules on these)

- **Reading 1 / historical settledness.** `settled()` treats `job_state` PENDING/FAILED as U even when `state=HISTORICAL`.
  - The closure 5 S4 preamble says "an explicitly selected as-of head with `site_coverage.state=HISTORICAL` is a settled selection".
  - W3-01 reading 4 keeps an outstanding mini-grid marker in `job_state` under historical. Cold/EV suppress jobs under a historical basis; mini-grid does not.
  - So an explicit-cutoff read of a mini-grid Site with an outstanding job would give U for F, E and M. That may contradict the preamble. The Architect may want to rule that a HISTORICAL state is settled regardless of `job_state`.
- **Reading 6 / pending vs unknown.** A cold `withheld` result or an EV `ERROR_PENDING` guard sets `_windows_covered=False`, which gives M as U and status UNKNOWN. PENDING is reached only if the Site cov is itself PENDING. This is likely consistent, because the same open jobs feed `_windowed`, but persisted variant (a) in 1b should confirm the status is PENDING and not UNKNOWN.
- I found no other reading I believe is wrong. On Q-1a-1, the `_selected_recorded_at` fallback is inert until Lane A supplies the field, and no fixture has two Actions on one origin pair.

## Residual risk not named in the packet

- **`page_one_mode` is unsigned and is not part of the token.**
  - A client that flips it from `live` to `historical` on page two changes the Site state and consequence presentation: mini-grid becomes HISTORICAL with UNKNOWN money, while the token is likely the same.
  - The page would then pass the fence and be labelled HISTORICAL.
  - The spec defines the cursor as an unsigned fence with no tamper claim, and the behaviour is shared with the W3-01 Findings cursor. It is not a 1a defect. A future token-version change could bind the mode.
- **Page-two marker equality depends on the row IDs being lowercase strings.** `resume_after` uses exact tuple equality, and cold/EV `finding_id` arrive as strings from the snapshot. The persisted tests resume only once, on whichever row comes first. A cold/EV-first continuation is not specifically proved.
