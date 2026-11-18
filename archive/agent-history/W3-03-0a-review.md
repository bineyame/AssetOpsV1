# W3-03 run 0a — independent review

Reviewed: `task/W3-03-portfolio-composition` commit `87f8ffed` (code), read at merge `9e3216d0` (main merged in;
the merge touches only `.agent/W3-03-build-spec.md` and `.agent/architect-request-W3-03-closure5.md`).
Spec: `.agent/W3-03-build-spec.md` closure 4 (B1/B2, S1/S2/S6/S8, run table) and closure 5 (S4, S7 verification IDs).
Read through git only; tests ran in a private detached worktree on a private `assetops_w303rev0a_test` DB (dropped).

## Verdict: REVISE

One Medium (M1). The rest of 0a is correct and spec-backed; a small fix in `financials.py` closes it.

## Findings

### Medium

**M1. `select_financial_scope` drops per-Site `windows_covered`, which closure 5 S4 says to read from it.**
`backend/assetops_backend/estate/financials.py:386-413` (at `9e3216d0`). For cold/EV Sites, `windows_covered` from
`windowed_lines(...)` only ends up in the per-category AND `applicable[category]` across every Site. The `per_site`
tuple carries `{**cov, "_sessions": sessions}` and no per-Site `windows_covered`.
- **Spec:** closure 5 S4's M table classifies each Site/category unit as `U` when "cold/EV `windows_covered` is false". It
  says: "Read `windows_covered`, `groups`, `exclusions` and `diagnostics` from `select_financial_scope`".
- **Why it matters:** with only an estate-wide per-category boolean, run 1a cannot tell which Site is unresolved. It
  cannot produce `PARTIAL` (one EV Site uncovered next to a covered one) as distinct from `UNKNOWN`. Closure 5 requires
  `PARTIAL` for "unselected EV Site" variants.
- **Who can fix it:** Lane B cannot edit `financials.py` (closure 4 B1/B2 makes Lane A its sole editor). Re-deriving it in
  1a would mean calling `windowed_lines` again, which is a second read of the same selection.
- **Fix (Lane A, on the branch):** carry it as a private key in the per-Site cov, for example
  `{**cov, "_sessions": sessions, "_windows_covered": covered_bool}`. Mini-grid would use its `cov["state"] in COVERED`.
  Add a pure or existing-Postgres assertion that it reaches `per_site`.
- **Byte safety:** `_coverage_site` and `_token_site` read named fields only, so W3-02 bytes are unaffected. Confirm this
  by rerunning `test_w302_money_comparability_postgres.py` and `test_w302_financials_links_postgres.py`.
- **Timing:** closure 5 landed on main in the same minute as `87f8ffed`. The handoff cites closure 5, so this is an
  acceptance gap, not a preference.

### Low

**L1. The new Portfolio row facts and verification IDs have no test of their own.** The facts are `_domain`,
`_episode_end` and `_mechanism`; the verification IDs are `_plans[].id/recorded_at` and `_outcome_id`.
- **Coverage today:** the Postgres goldens execute the changed SQL and prove the bytes are unchanged. Nothing asserts
  the values: no test checks that `_episode_end` equals the stored `finding_revision.episode_end`, or that plan `id`
  matches the persisted row.
- **Spec:** the run-0a gate lists only golden bytes and pure cursor tests, so this is not an acceptance gap.
- **Fix:** run 0b/1a should assert these exact IDs. The persisted S6 chain is already named for 1b.

**L2. Reading 4 is only partly spec-backed.** It says a Portfolio cursor with a `lens` outside `LENSES` is a 422 shape
error.
- **Backed:** `state_filter:null` is part of the specified key set, so a non-null value being 422 is backed.
- **Not backed:** an invalid lens being 422 rather than the Findings-style 409 fence (`scope.py:268`). It is harmless and
  arguably stricter, but the Architect should confirm it.

**L3. Reading 6 leaves S1 (Portfolio status union in `frontend/src/estate/estateClient.ts`) without a run.** That file is
an existing shared file, and closure 4 assigns it to no run.
- **Fix:** the Architect or Planner names a run and lane for it. Deferral out of 0a is reasonable: the 0a deliverable
  column has no frontend item.

**L4 (residual risk, not a defect).** When Portfolio composes the four selectors on one snapshot, it will call
`site_coverage` for the same Site and domain up to three times: in the finding, evidence and financial selectors.
- **Rows:** no per-row N+1 was introduced. The per-row `cited_provenance` in the evidence selector was moved verbatim.
- **Cost:** this is repeated per-Site SQL, not a correctness issue. Run 1a should measure it on the four-Site fixture
  before any caching.

## Verified as correct

- **Selectors** (`index.py:62-117`, `evidence_money.py:416-437`, `financials.py:386-413`):
  - Each is a verbatim move, public, takes the caller's `scope`, is read-only and opens no transaction.
  - Finding and Action rows are returned unfiltered, unsorted and unpaged. Evidence comes back in full canonical `_key`
    order; Financials comes back deduped, compared, then sorted by `_order`.
  - The roots consume them. Private keys are stripped by the existing `not k.startswith("_")` projection, including
    `_raw` on Actions.
- **Parser** (`scope.py:47,122-125`):
  - `portfolio` keys are `from,to,known_at,lens,limit,cursor`.
  - Lens is validated as `INVALID_LENS`, and `state` is refused as an unknown key (`INVALID_CURSOR`).
- **Cursor:**
  - Keys are the Finding set plus `kind`, with `state_filter` null and `page_one_mode` required.
  - The marker is exactly five members: null or a canonical six-digit instant, a nonempty string, then three UUIDs.
  - `_fence` checks lens and the null filter before `cursor_after`, so a changed grant, lens, window, cutoff or token
    is 409 before any marker lookup. A valid nonmember marker is 422 through `resume_after`.
  - Cursors do not cross between kinds in either direction.
  - Existing key sets and encoders are unchanged for findings, actions, evidence and financials.
- **Row fields** (`coverage.py`):
  - W1 `episode_end` comes from the selected head, which is read from the revision.
  - Cold uses `rev[14]` and EV uses the selected session revision's `end_at`. These are the same values the existing
    `_intersects` already uses.
  - `mechanism` is None everywhere and is not derived from anything.
  - `_domain` is the stored uppercase `site_type`.
- **Verification** (`postgres_estate_read.py:307-323`):
  - Plans gain `id` and `recorded_at`; outcomes keep the `id -> recorded_at` map.
  - Both queries are now `ORDER BY recorded_at, id`. No consumer depends on iteration order: `in_window` uses `any`, and
    outcomes are looked up by key.
  - `_verification_window` is preserved.
- **Lane ownership:** the code changes touch only the six existing estate files named in B1/B2. The other two files are
  the new `tests/test_w303_estate_cursor.py` (the 0a "pure cursor tests" deliverable) and `.agent/W3-03-phase-handoff.md`.
  No frontend, router, registry or migration files were touched.
- **Handoff readings:**
  - 1 (run 1 = 0a): backed by the closure 4 run table and sequence.
  - 2 (private row keys): backed. The row DTO gets `domain` while `coverage.sites` stays unchanged.
  - 3 (private `_plans`/`_outcomes`/`_outcome_id`): backed by S8 and closure 5 S7 (no second connection).
  - 5 (new test file name): backed, since 0a's deliverable includes pure cursor tests and names no file.
  - 4 and 6: see L2 and L3.
- **Test non-vacuity:** I mutated the code twice in my own copy. Removing `portfolio` from the `_fence` lens branch
  failed `test_changed_grant_lens_window_cutoff_or_token_is_409_before_marker_lookup`. Disabling the portfolio
  `state_filter`/lens decode check failed 2 parametrized malformed-cursor cases. Both mutations were reverted.

## Checks run (by me)

| Check | Where | Result |
| --- | --- | --- |
| Pure: `test_w303_estate_cursor`, `test_w302_estate_cursor`, `test_w301_estate_api`, `test_w301_estate_coverage`, `test_w302_evidence_api`, `test_w302_money_api`, `test_w302_pinned_facades`, `test_w302_w1_day_reduction` | private worktree at `9e3216d0`, PYTHONPATH = worktree backend, contracts, host, gateway, simulator | **122 passed** (8.2 s) |
| Postgres goldens and links: `test_w301_estate_golden_postgres`, `test_w302_money_comparability_postgres`, `test_w302_financials_links_postgres`, `test_w302_evidence_links_postgres`, `test_w301_estate_index_postgres` (`-n 2 --dist loadfile`) | private `assetops_w303rev0a_test` (dropped) | **38 passed**, 0 failed, 0 skipped, 12m03s; the W3-01/02 golden response bytes are unchanged |
| `tools/check-architecture.ps1` | review checkout at `9e3216d0` (clean) | passed |
| `tools/check-agent-workflow.ps1` | private worktree | passed |

**Not rerun:**
- **Remaining Postgres files from the implementer's set of 116:** index-EV, provenance DTO, evidence scope snapshot,
  evidence EV, pinned facades Postgres.
- **Full backend suite:** none exists for this revision, which the handoff states (run 3 owns it).
- **Frontend:** no frontend files changed, so frontend checks were not applicable.

**Run-environment note:** an earlier `check-architecture` run in my temp worktree reported Rule 8 as "vacuous" even
though the INSERTs are present. That is environmental: the same check passes on the clean review checkout.
