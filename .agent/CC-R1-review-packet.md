# CC-R1 review packet

Task: CC-R1, links, claim labels, beneficiary key and the no-double-count check. Lane C. Task file: `tasks/CC-R1-links-labels.md`.
Branch: `task/CC-R1-claim-links-beneficiary`, from main `4a166d98`. Code commits: `b902f95b`, `41deb446`, and the ruling round (CC-R1-Q1/Q2, see "Ruling round" below).
Reviewer diff: `git diff 4a166d98..HEAD -- ':!.agent'`.
Spec: `.agent/build-spec-commercial-2026-10-27.md` section 0.4, section CC-R1, and the "Implementer questions and resolutions".

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-cc\backend;C:\Users\assef\Bineyame\AssetOpsV1-cc\contracts;C:\Users\assef\Bineyame\AssetOpsV1-cc\simulator;C:\Users\assef\Bineyame\AssetOpsV1-cc\gateway;C:\Users\assef\Bineyame\AssetOpsV1-cc\host;C:\Users\assef\Bineyame\AssetOpsV1-cc"
```
Verified: `assetops_backend.__file__` resolves to `C:\Users\assef\Bineyame\AssetOpsV1-cc\backend\assetops_backend\__init__.py`.

## CC-00 pre-flight

Gate: "no open questions" against the spec. During the build, two new questions arose, recorded in `.agent/CC-R1-questions.md` (see Known deviations).

The fixture facts were surveyed by reading code; nothing was observed live. They are recorded here because the C2 packet does not exist yet, and the CC-R2 builder should copy them into it:
- **W3-03 cold row** (`build_portfolio_fixture`, cold case `excursion`): `episode_end` is **null**, meaning the episode is open.
  - Source: `postgres_finding_store.py:663-664` writes `end_latest`, and `test_w203_cold_replay_postgres.py:170,173` asserts `open`, `end_latest=None`.
  - The row is UNPRICED and has no Action. Expected CC-R2 placement: ACT_NOW, `EPISODE_OPEN` + `NO_ACTION_RECORDED`.
  - CC-R2 must confirm this on the live fixture.
- **W3-03 EV rows** (EV-LAB-001 and EV-LAB-002): the episode is closed (`end_at` is non-null), the row is UNPRICED, not recurred, not reopened, and has no Action.
  - Expected placement: UNPRICED_RISK / `UNPRICED_SERVICE_INTERRUPTION` (neither rank 1 nor rank 2 applies).
  - This assumes the source state is not MIXED or UNKNOWN. That was not confirmed.
- **w403 minimum ELIGIBLE lower headroom: 18 kW** (headroom [18, 20] kW).
  - This is hand-computed from the fixture inputs: PV 42 ± 1, feeders 20, margin 3, via `mini_depth/rules.py:363-369`.
  - The stored value is `projection.py:179-183` `headroom_kw.low`. CC-D1 negative (a) would therefore use 19. Confirm it from the stored row in CC-D1.

## Outcome delivered

- **Beneficiary key** (owner Q9):
  - `BENEFICIARY_OF_CATEGORY` maps all five categories.
  - Every estate line carries `beneficiary`.
  - The seventh partition element is `_beneficiary(line)`, which has a category default.
  - `group_key_for_partition` hashes `beneficiary` only when it differs from the category default.
- **`estate/money_invariants.double_count_violations`**:
  - It runs the three null-total checks.
  - It checks that every member is found in `selected_lines`.
  - Members must agree on category, currency, window, period, fingerprint and beneficiary.
  - Members must not intersect on technical or cited IDs.
- **Frontend**:
  - The claim vocabulary and the `ClaimLabel` component.
  - The `MODELLED_OPPORTUNITY` + `MINI_OPERATOR` label under the gross scenario.
  - The estate "Benefits: …" line inside the Category cell (no new column).
  - "Open the recommendation →" on the mini Financials bridge, carrying the view's `revision_id`. The cold and EV frames do not pass it.

## Files materially changed

- Backend:
  - `backend/assetops_backend/estate/financials.py`
  - `backend/assetops_backend/estate/evidence_money.py`
  - new `backend/assetops_backend/estate/money_invariants.py`
- Backend tests:
  - new `backend/tests/test_cc_money_invariants.py`
  - `backend/tests/test_w303_portfolio_reduction.py`: the beneficiary, pinned-key and mapping tests
  - `backend/tests/test_w303_portfolio_scope_snapshot_postgres.py`: `Portfolio.ok()` asserts the invariant on every body
  - `backend/tests/test_w303_portfolio_fixture_postgres.py`: the invariant over the Portfolio and Financials bodies, including the COMPARABLE EV group
- Frontend:
  - `frontend/src/sites/actionPresentation.tsx`
  - new `frontend/src/sites/ClaimLabel.tsx`
  - `frontend/src/sites/MiniScenarios.tsx`
  - `frontend/src/estate/EstateFinancials.tsx`, `estateFinancials.css` and `estateEvidenceMoneyClient.ts`
  - `frontend/src/sites/FindingConsequence.tsx`
  - `frontend/src/sites/SiteFinancials.tsx`
  - `frontend/src/shell/SiteAnalyticsFrames.tsx`
- Frontend tests:
  - new `frontend/src/sites/__tests__/claimLabel.test.tsx`
  - `estateFinancials.test.tsx`
  - `siteFinancials.test.tsx`
  - `miniDecisions.test.tsx`: the exact cell text now includes the label, plus label assertions
- Records:
  - `.agent/mock-departure-register.md`: R500 and R501
  - `.agent/CC-R1-questions.md`
  - `tasks/CC-R1-links-labels.md`
  - `.ai/ACTIVE_CONTEXT.md`
  - `.ai/CODE_STATE.md`

## Acceptance criteria

| Gate | Status | Evidence |
|---|---|---|
| Lines differing only by beneficiary form two groups, never COMPARABLE, with different keys | met | `test_w303_portfolio_reduction.py::test_beneficiary_splits_an_otherwise_identical_partition` |
| Every category has a beneficiary | met | `::test_every_category_has_a_beneficiary` (covers APPLICABLE and COLD_CATEGORY) |
| An existing group key is unchanged (pinned) | met | `::test_default_beneficiary_group_key_is_unchanged`. It pins `sha256:2de8f72a…41139`, computed independently by hashlib from the `test_w302_money_api._eligible` line. |
| Invariant is `[]` on every existing `test_w303_portfolio_*` body | met | `Portfolio.ok()` asserts it in every scope-snapshot and comparison test; the fixture test asserts it with Financials; the fake-world API body is covered in `test_cc_money_invariants.py`. Tier 2 passed (below). |
| Invariant gives one violation per crafted defect | met | `test_cc_money_invariants.py`: 13 parametrised defects, each giving exactly one violation with the expected code |
| Three labels render with `data-claim-level` | met (ruling round) | The gross scenario label is checked in `miniDecisions.test.tsx`. The verdict label is checked in `siteActionVerification.test.tsx`: VERIFIED and both INEFFECTIVE cases show it, INCONCLUSIVE does not, and the vocabulary scan is clean. The `ClaimLabel` unit tests also pass. The estate line carries `data-beneficiary`; the spec gives it no claim level. |
| Forward link carries `revision_id` | met | `siteFinancials.test.tsx` "CC-R1: links forward…" (href `…/recommendation?revision_id=<FREV>`, vocabulary scan clean) |
| New text never says "saving" or "saved" | met | asserted in the claimLabel, estateFinancials, siteFinancials and miniDecisions tests |
| Stop: an exact-key test outside w303 breaks | not hit | The pure `test_w30*` and `test_cc_*` tests pass. The Postgres exact-key tests outside w303 were not run (tier 2 is scoped to w303). |

Non-vacuity was proven on committed code; each mutation was reverted with `git checkout`:
- The partition ignoring beneficiary: 1 failed.
- The group key ignoring beneficiary: 2 failed.
- The invariant ignoring beneficiary: 1 failed.
- After the revert: 61 passed.

## Checks run

- Backend pure, focused: `pytest tests/test_cc_money_invariants.py tests/test_w303_portfolio_reduction.py tests/test_w303_portfolio_api.py tests/test_w302_money_api.py tests/test_w302_pinned_facades.py` gave **98 passed, 1 skipped**.
- Backend pure, all `test_w30*` and `test_cc_*` without a database URL: **203 passed, 97 skipped, 1 failed**. The failure is `test_w303_selectors_postgres.py::test_financial_scope_carries_private_per_site_windows_covered` with `NameError: financials`.
  - This is pre-existing: the test uses a name imported only under `if URL:` (`:14-18`), and the file is untouched.
  - `test_w301_w1_money_snapshot_helpers_postgres.py` was excluded because it fails collection without a URL (`NameError: PowerSite`). This is also pre-existing and the file is untouched.
- **Tier 2** (`ASSETOPS_TEST_DATABASE_URL` set to `…/assetops_cc_test`, created empty with `createdb`; the authorised spec name):
  - Run 1, `test_w303_portfolio_comparison_postgres.py`, `test_w303_portfolio_fixture_postgres.py` and `test_w303_portfolio_scope_snapshot_postgres.py` at `b902f95b`: **15 passed, 1 failed**, 1170 s. The failure was my added fixture block, which got a 503 because the Portfolio cursor key env was missing.
  - Run 2, `test_w303_portfolio_fixture_postgres.py` at `41deb446` after the fix: **2 passed**, 114 s.
- Frontend:
  - `npx vitest run` on `claimLabel`, `estateFinancials`, `siteFinancials`, `miniDecisions`, `siteActionVerification` and `w302EstateFinancialsShellRoute`: **199 tests, 1 failed**. That one failure was a `REGISTER_COLUMNS` reference in my new test. After the fix, `estateFinancials` gave **11/11**. The other 5 files passed in the 199-test run.
  - `npx tsc --noEmit -p .` was clean.
- Guards:
  - `tools/check-architecture.ps1`: **passed** with `ASSETOPS_GUARD_PYTHON` set to the venv Python. Without it, it fails because the worktree has no `.venv`; that is environmental.
  - `tools/check-agent-workflow.ps1`: **passed**.
- Not run: the production build, the full suites (lane rule: Lane T has priority), and **layout evidence**. Chrome capture is a heavy job, so it is not run here. The label and beneficiary line layouts are unverified; the coordinator schedules the capture before the Codex batch.

## Ruling round (CC-R1-Q1/Q2, Architect 2026-10-27)

The rulings are in `.agent/CC-R1-questions.md` and in the spec's resolutions section. The vocabulary guard is unchanged.

- **Q1:** `CLAIM_LABEL.VERIFIED_SIMULATED_TECHNICAL` = "Technical result verified on test data"; the enum key is unchanged. The verdict label is now wired in `SiteActionVerification.tsx`, after the state strip. It shows for `view === "verification"` when the displayed outcome is VERIFIED or INEFFECTIVE.
- **Q2:** the fallback is "Evidence level and beneficiary not stated", with no suffix. A new unit test runs the fallback and both rendered labels through `scanProductVocabulary` and expects `[]`.
- **Register:** R500 now covers `scenarios, verification`.
- **Checks:**
  - `npx vitest run` on `claimLabel`, `siteActionVerification`, `miniDecisions`, `siteFinancials`, `estateFinancials` and `w1Vocabulary`: **6 files, 211 passed**.
  - `npx tsc --noEmit -p .`: clean.
  - Guards: `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON`) passed; `check-agent-workflow.ps1` passed.

## Known deviations

1. **Resolved by the ruling round above.** This entry is kept as history: the verdict label was held at first (`.agent/CC-R1-questions.md` Q1).
   - The spec's verbatim "Technical result verified on simulated data" fails the product-vocabulary guard (`productVocabulary.json:36` forbids "simulated"). With the label wired, 5 tests in `siteActionVerification.test.tsx` fail.
   - The label is not wired. `CLAIM_LABEL` keeps the spec text, and R500 covers `scenarios` only.
   - Q2: "Claim not stated" contains the guarded word "claim"; no test fails today.
2. **Two files outside the spec list**, both needed for types: the `FinancialsLinks.recommendation` field (`SiteFinancials.tsx`), because the frame's object literal is typed `FinancialsLinks`; and `FinancialRow.beneficiary?` (`estateEvidenceMoneyClient.ts`).
3. **One CSS rule added**, `.line-beneficiary { display: block }` in `estateFinancials.css`. It puts the beneficiary on the second line instead of using a `<br>`.
4. **Violation code names are the builder's choice.** The spec names only `MEMBER_NOT_FOUND`; the builder added `TOTAL_NOT_NULL`, `MEMBERS_DISAGREE` and `MEMBERS_INTERSECT`.
5. **Process naming.** The brief names this packet `CC-R1-review-packet.md`; the spec says `CC-C1-…`. The coordinator's name was used. The branch name is the coordinator's (`…claim-links-beneficiary`).
6. **The invariant is asserted inside the existing Postgres test helper**, `Portfolio.ok()`, rather than in a new Postgres test. This covers every existing w303 body without a duplicate fixture build.

## Residual risk

- The Postgres exact-key tests outside `test_w303_*` (for example the w302 Postgres tests) did not run. A line exact-key assertion there would only show at merge or full suite. No such assertion was found by grep.
- The lazy import inside `group_key_for_partition` is a call-time import, needed because of the import cycle.

## User-review focus

`USER_REVIEW_REQUIRED`: the merge needs a fresh Claude review ACCEPT, and the owner sees R500 and R501 in the walkthrough. Q1 needs an Architect ruling before the verdict label can land; it can follow in CC-R2 or a small fix round.
