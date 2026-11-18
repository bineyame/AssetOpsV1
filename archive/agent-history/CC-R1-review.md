# CC-R1 review (fresh Claude reviewer, 2026-10-27)

Branch `task/CC-R1-claim-links-beneficiary` at `c1151a6d`, diffed against main `4a166d98`.
Authority: `.agent/build-spec-commercial-2026-10-27.md` section 0.4, section CC-R1, the resolutions (Q-C9, Q-C10, Q-C15, Q-C16, Q-C17) and CC-R1-Q1/Q2, plus `.agent/CC-R1-questions.md`.

## Verdict: ACCEPT

There are no High or Medium findings. The five Low findings below are optional tidy-ups and do not block the merge.

## Gates verified against the spec

- **Beneficiary partition.** `financials.py:48-51` maps all five categories, and `RECORDED_REPAIR` maps to `COOLING_PROVIDER`. `_line` emits `beneficiary` after `category` (`:126`). `_beneficiary` uses the spec's fallback (`:294-295`). `_partition` has seven elements, and `compare` unpacks seven and passes the keyword (`:330-331`).
  - The test `test_beneficiary_splits_an_otherwise_identical_partition` shows two `SINGLE_LINE` groups, never COMPARABLE, with distinct keys.
  - `test_every_category_has_a_beneficiary` covers `APPLICABLE` and `COLD_CATEGORY`.
- **Default group keys unchanged.** `evidence_money.py:426-427` adds `beneficiary` only when it is not None and differs from the category default. I recomputed the pinned `sha256:2de8f72a...41139` independently with hashlib over the six-value payload, and it matches. The test asserts the same key three ways: with no beneficiary, with the default, and through `compare`.
  - The lazy import is needed because of the import cycle, and it is correct.
  - A cold `kind` outside the map cannot reach `BENEFICIARY_OF_CATEGORY[category]`: the column has `CHECK (kind IN ('PRODUCT_EXPOSURE','RECORDED_REPAIR'))` (migration 0023:60).
- **No-double-count invariant.** `money_invariants.py` matches the Q-C17 interface:
  - the member set is `portfolio["selected_lines"]`, and the paged rows are never used;
  - it runs the three null-total checks;
  - it flags `MEMBER_NOT_FOUND`;
  - members must agree on the seven fields, with currency taken from `amount` or `disclosure.pinned_amount`;
  - members must not intersect on technical or cited IDs.

  `Portfolio.ok()` asserts it on every scope-snapshot and comparison Portfolio body. The fixture test asserts it on Portfolio plus Financials, including a COMPARABLE group. The 13 crafted defects each give exactly one violation.
- **Labels and copy (vocabulary).**
  - `CLAIM_LABEL.VERIFIED_SIMULATED_TECHNICAL` is "Technical result verified on test data" (Q1).
  - The fallback is "Evidence level and beneficiary not stated", shown with no suffix (Q2).
  - `productVocabulary.json` is not touched.
  - The verdict gate in `SiteActionVerification.tsx:385` requires `view === "verification"`, a non-null verdict, and a displayed (`shown`) outcome of VERIFIED or INEFFECTIVE. That matches Q-C16. The existing 5 verification tests pass with their assertions unchanged; lines were added only.
  - `ClaimLabel` scans clean, and so do the forward link and the fallback.
  - The new texts never say "saving" or "saved".
- **Forward link.** It is wired only in the mini `SiteFinancialsFrame` (`SiteAnalyticsFrames.tsx:1391-1392`). It renders only when the prop is present (`FindingConsequence.tsx:922`) and carries the bridge's `rev`. The test checks the href `.../recommendation?revision_id=<FREV>`.
- **Declared deviations.** All six are acceptable:
  - The `FinancialsLinks.recommendation` field in `SiteFinancials.tsx` and `FinancialRow.beneficiary?` in `estateEvidenceMoneyClient.ts` are type-only edits outside the file list, and both are needed for `tsc`.
  - The violation code names `TOTAL_NOT_NULL`, `MEMBERS_DISAGREE` and `MEMBERS_INTERSECT` are reasonable. The spec named only `MEMBER_NOT_FOUND`.
  - The one CSS rule (`.line-beneficiary`) is acceptable.
  - The packet name is acceptable.
  - Asserting the invariant inside `Portfolio.ok()` is acceptable.
- **Register.** R500 (`scenarios, verification`) and R501 (`financials`) use the spec's verbatim "What is shown instead" texts.

## Findings

All five are Low and optional.

- **L1** `backend/tests/test_w303_portfolio_comparison_postgres.py:241,281,293`: the Financials bodies read there are not passed to `double_count_violations(portfolio, financials)`. Only the Portfolio body is checked, through `ok()`. The gate says the invariant holds on "every existing `test_w303_portfolio_*` body", and the one Financials check is in the fixture test.
  - Why it matters: it gives slightly thinner coverage of the Financials group path.
  - Fix: add one assert after `:241`.
  - Type: preference-level; the gate's intent is met.
- **L2** `.agent/CC-R1-review-packet.md:147`: the text is stale after the ruling round. It says "Q1 needs an Architect ruling before the verdict label can land", and "Outcome delivered" (`:30`) omits the verdict label. Fix: update the text.
- **L3** `.agent/mock-departure-register.md:517`: the R500 "Mock element" names only the "Gross scenario result figure", although the row also covers the `verification` verdict. Fix: name the verdict too.
- **L4** `frontend/src/sites/MiniScenarios.tsx:24`: a space was lost in the import list (`siteLocalDate,siteLocalEndUtc`). This is cosmetic.
- **L5**: no test asserts that the cold and EV Financials frames show no "Open the recommendation" link. Absence follows from the optional prop not being wired, so this is a missing negative test only.

## Checks run (by me, at `c1151a6d`)

- Lane C PYTHONPATH and the plan2 venv. `assetops_backend.__file__` resolves into `AssetOpsV1-cc\backend`.
- `pytest test_cc_money_invariants.py test_w303_portfolio_reduction.py test_w303_portfolio_api.py test_w302_money_api.py test_w302_pinned_facades.py test_w303_portfolio_workflow_labels.py -q`: **100 passed, 1 skipped**.
- All non-Postgres `test_w30*.py` with no DB URL: **182 passed, 1 skipped**.
- Frontend `npx.cmd vitest run` on `claimLabel`, `siteActionVerification`, `miniDecisions`, `siteFinancials` and `estateFinancials`: **5 files, 198 passed**. On `w1Vocabulary` and `w302EstateFinancialsShellRoute`: **2 files, 15 passed**. Vitest ran in this worktree; the known sandbox esbuild failure did not occur.
- `npx.cmd tsc --noEmit -p .`: exit 0.
- `tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv): **passed**.
- `tools/check-agent-workflow.ps1`: **passed**.
- Both guards were invoked directly, because the `-ExecutionPolicy Bypass` form was refused by the sandbox.

## Not verified

- **Tier 2 Postgres.** I did not rerun it; the telemetry lane has priority on heavy jobs. I cite the implementer's runs:
  - comparison, fixture and scope-snapshot at `b902f95b`: 15 passed, 1 failed (the fixture block lacked the cursor key);
  - the fixture file at `41deb446`: 2 passed.

  Since `b902f95b`, the only backend change is that fixture test (4 lines), so the evidence applies to the revision under review.
- **Production build.** Not run.
- **Full suites.** Not run.
- **Layout evidence.** Not run; the packet records it honestly as not run. The new second line in the estate register's Category cell (a dense table) and the label lines are layout-unverified until the coordinator's capture.

## Residual risk not named in the packet

- `CLAIM_LABEL.POST_INTERVENTION_MODELLED` (`actionPresentation.tsx:300`) is the spec's fixed text, "... not realized savings".
  - It is unused in R1, but CC-D2 will render it through `ClaimLabel`.
  - It contains "savings", and the R1 rule bans "saving" in new label text.
  - It also spells "realized" while the existing headings use "Realised".
  - CC-D2 should check it against the vocabulary scan and the saving rule before wiring, and raise it with the Architect if it trips them.
