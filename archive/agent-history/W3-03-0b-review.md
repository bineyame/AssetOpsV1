# W3-03 run 0b — independent review (portfolio fixture composition)

Branch `task/W3-03-portfolio-composition`, commits `45592a22` and `7ab8019a` (head `7ab8019a`). I read the code only through
git. The run used a private detached worktree and the private DB `assetops_w303rv0b_test`. The worktree is removed and every
`assetops_w303rv0b%` database is dropped (count 0 afterwards).

**Verdict: REVISE.** The composition matches the rulings, and its public-root assertions are real and pass. There is
one latent clock bug in the fixture that 1a/1b will inherit, plus one assertion that r0b requires and the test does
not contain.

## Checks run

- `test_w303_portfolio_fixture_postgres.py` at `7ab8019a`, plus an uncommitted probe module that imports
  `build_portfolio_fixture`. Result: **2 passed** (the real test, collected again through the probe's `import *`),
  270 s, with the probe failing only on a print bug of my own after its output had been captured. Probe facts:
  - `frozen = 2026-10-30T09:03:00Z`, which equals `power.runner.now + 1 min`. Every root's `known_at` is the same
    value.
  - `/financials` has four lines in exactly three categories: cold `POTENTIAL_PRODUCT_EXPOSURE UNPRICED`, two EV
    `GROSS_TARIFF_SCENARIO ELIGIBLE` and W1 `CANDIDATE_OPERATING_COST_EXPOSURE ELIGIBLE`.
  - Every `action*` table holds 0 rows in the composed DB.
- PYTHONPATH note: the venv has editable installs that point at `AssetOPsV1`, so `backend`, `contracts`, `simulator`
  and `gateway` from the worktree all had to be on PYTHONPATH. With `gateway` left off, the cold upload stayed
  `STAGE_HELD`.
- Production code: neither 0b commit touches `backend/assetops_backend` or `frontend`. Only `.agent/*` and the new
  test file change. **Clean.**
- Not run: `check-architecture.ps1`, `check-agent-workflow.ps1` and the full suite. 0b is test-only, and the packet
  cites `check-all` 11/11 and the focused 29 passed on `w303d_test`. I did not reproduce those numbers.

## Findings

### H1 — the second `pin_snapshots` call does not move the snapshot clock to `frozen` (test file lines 114-123, 220, 234)

`pin_snapshots` subclasses whatever class the module currently holds (`real = getattr(module, name)`). The second call
at line 234 therefore subclasses the first `Pinned` from line 220. That first `Pinned.__init__` discards the
`read_at` it receives and calls the real class with the *first* `present()`, `power.runner.now + 1 min`. So
`EstateSnapshot` and `EvidenceMoneySnapshot` always read at `runner.now + 1 min`, never at `frozen`. A standalone
simulation of the same pattern returns the first clock.

Only `_transaction_time` gets the frozen clock, because it is a plain replacement.

- **Why it passes today:** in this fixture `frozen == runner.now + 1 min` (probe: both 2026-10-30T09:03Z). The test
  also never asserts `known_at == frozen`.
- **Why it matters:** B3's single contract is "one read clock = frozen". 1a/1b reuse the builder for perturbations
  such as variant (a), a later cold record. If `db_now` or a cold/EV recorded time goes past `runner.now + 1 min`,
  the roots read at an earlier clock than `frozen`. The `<= fx.frozen` check would still pass, so the fault would be
  invisible.
- **Fix:** make the pin idempotent by keeping the original class (for example, on first patch store the real class
  as `Pinned._real` and always subclass that), or pin the snapshot once with a mutable clock cell. Then add
  `assert findings["window"]["known_at"] == iso(fx.frozen)` to the root loop.

### M1 — the three-category assertion that r0b says to retain is missing (lines 298-324)

r0b P-0b-1 ends: "retain the three-category and unchanged-root assertions". The P-0b-1 held block listed
`assert len({line["category"] for line in financials["rows"]}) == 3`, but it was not committed. The test only has
`w1_line["category"] != a["category"]`.

The cold line is also found by filtering (`[r for r in cold_rows if r["category"] == ...]`). An extra cold line in
any other category, or a fourth category anywhere, would therefore pass. This is an acceptance gap, not a preference.

- **Fix:** add the three-category assertion. Either assert `(cold_line,) = lines[cold]` (exactly one cold line), or
  assert the set of `(site, category)` pairs. The probe shows both hold today.

### M2 — the cold line and cold Finding are not compared with stored rows (lines 301-306)

B3 says to "compare the exact selected IDs and stored category lines". W1 is compared with
`consequence_row(...)`, and both EV lines with `_stored`/`_line_matches`.

The cold line is checked only for consistency with the same root read (`finding_revision_id` is in the
`/findings` cold set). Its `consequence_revision_id` is never matched to a `financial_consequence_revision` row
(state `UNPRICED`, null amounts, `finding_revision_id` equal). Nor is the selected cold Finding revision matched to
the producer's stored head.

`recorded_times` proves only that each ID exists somewhere with a timestamp in (09-30, frozen].

- **Fix:** `stored = consequence_row(fx.engine, cold_line["consequence_revision_id"])`, then assert
  `stored[0] == cold_line["finding_revision_id"]` and `stored[1:4] == ("UNPRICED", None, None)`.

### L1 — the "no Action on 10-06" check is true but weakly evidenced (line 276)

The composed DB holds no Action rows at all (probe: every `action*` table is 0). So `actions.rows == []` shows that
no Action exists, not that the `created_at in [from,to)` window excludes one. B4 only requires that the 10-06 proof
contains no S6 Action, so this meets the spec.

The separate B4 `[2026-11-01,2026-11-03)` workflow-word path is not in 0b. It is assigned to 1b (handoff reading 5;
closure 4 table row 1b; closure 5 S7), so it is preserved rather than dropped.

- **Optional:** add a short comment, or `SELECT count(*) FROM action WHERE tenant_id = ...` == 0, so 1a/1b do not
  read the empty root as a window-exclusion proof.

### L2 — the docstring and comment are stale after r0b (lines 17-20, 180)

The module docstring still says "Not a clean B3 proof yet ... cold product-exposure assertions are held". The
builder comment still says "Cold `normal` and EV `complete`". Both contradict the r0b defaults (`excursion` + drain)
and the assertions that are now present.

- **Fix:** update the text.

### L3 — reuse needs the replay fixtures imported in the caller (lines 181, 186, 192)

`build_portfolio_fixture` resolves `cold_chain` and `ev_chain` through `request.getfixturevalue`. They are visible
only because this module imports them from `test_w301_estate_golden_postgres`. A 1a/1b module that imports just
`build_portfolio_fixture` or `portfolio_fixture` will fail with "fixture not found" unless it also imports
`cold_chain, ev_chain`. My probe had to do this.

The builder also monkeypatches `pg_harness.fresh_database`, the snapshot classes and `CaseRunner.submit` for the
rest of the test. Perturbations therefore run under those patches.

- **Fix:** document this in the builder docstring, or move these fixtures to a shared conftest-style import.

## Spec conformance (verified)

- Producers are exactly the ruled set:
  - cold `excursion` + W2-04 `drain` (r0b);
  - EV `complete` with the reset suppressed (`mixed_replay` mechanics);
  - `EV-LAB-002` via `install_second_ev_site`/`second_scenario_repository`, with the golden KES tariff and `money`
    worker for both EV Sites (`two_ev_sites`);
  - the P01-bound `PowerSite`/`Rig` with `publishing_submit(P01)` and v1-v3.

  There is no `S4_CASES["F03"]` import, only one `fresh_database()`, and all four Sites are `imported_before`
  10-05. This matches B3.
- Window and cutoff:
  - One window, `[2026-10-06,2026-10-07)`, and `known_at` is omitted for every CURRENT read.
  - `frozen` follows B3's max formula. The snapshot pin defect is H1.
  - The four roots go through the public routers (`Estate.ok`, `EvidenceMoney.ok` via
    `build_estate_evidence_money_router`), not internals.
- Assertions are non-vacuous: single-element unpacks for W1, the cold line and the EV group, set equality on Sites
  and Evidence Sites, ID equality with stored heads for W1 and EV, the exact `group_key_for_partition`, and the
  dispatch day list.
- The six moved readings are spec-backed:
  - Portfolio-only facts go to 1a/1b: closure 4 table and B3's `/portfolio` read.
  - Price steps v1-v3: the P01 path in `test_cost_lens_only_exact_eligible_current_rows` publishes v1-v3. Q9 names
    v1 only, but B3 supersedes it with the `power_estate` P01 producer.
  - Variants and empty/foreign Sites go to 1b (closure 2 N6).
  - The B4 label test goes to 1b (closure 5 S7, closure 4 table).
  - L3 goes to seam run 2 (r0b).

  None needs flagging beyond L1/L3.
