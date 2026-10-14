# S4-02b phase 1 handoff: `fuel-cost-1` and the consequence store

Branch `task/S4-02b-fuel-consequence`, from `16ba22d`. Commits:
- `7cbdef7`: pure model.
- `5b4be01`: store, migration, guard, v4.
- `8eb4ee9`: price context in the basis, plus questions.
- the closeout commit: this handoff and `CODE_STATE`.

Phase 1 is packet row 1. Phase 2a (read and recompute worker) and 2b (UI) are not built. No money value was taken from the mock.

## What was built (anchors)

**Pure model** `backend/assetops_backend/financials/fuel_cost.py`:
- `PARAMETER_VERSION` :57 is the immutable conditional 1.10 record: value, inequality, limitation, scope, formula, SFC rule, source, author/reviewer, date.
- `PARAMETER_SHA256` is `0bce07ea…19a7`, pinned in the fixture. `FORMULA_VERSION` is `fuel-cost-1+fuel-cost-1/sfc-upper-multiplier/v1`.
- Public input dataclasses :112-185.
- `quantify` :283 applies Architect C4 fail-closed containment:
  - candidate spans are verified against the stored observed `CANDIDATE_AVOIDABLE` segments;
  - power must be in the cited runs' input sets;
  - power intervals must not overlap, must be wholly contained, and must cover the spans;
  - each needs one positive as-accepted SFC and a valid binding over the whole interval.
  - Typed reasons: `POWER_MISSING`, `POWER_COVERAGE_GAP`, `INTERVAL_CROSSES_{UNOBSERVED,NECESSARY,INDETERMINATE}`, `INTERVAL_OUTSIDE_FINDING`, `POWER_OVERLAP_CONFLICT`, `SFC_*`, `BINDING_*`, `CANDIDATE_SPAN_UNVERIFIED`, `FINDING_NOT_SUPPORTED`, `NO_CANDIDATE_TIME`.
  - Arithmetic is exact (Fraction). The upper is stored at 50 significant digits rounded toward +∞, alongside the exact fraction.
- `technical_input_sha256` :399.
- `select_window_price` :434 (packet item 3) returns `PRICED`, or `UNPRICED` with one of `NO_PRICE`, `PRICE_SPANS_WINDOW`, `PRICE_CONFLICT`, `PRICE_UNIT_MISMATCH`, `PRICE_REVISION_MISSING`, `PRICE_INVALID`. Both ends are half-open. It never partitions a window.
- `consequence` :486 computes the amount as an exact product. The basis digest includes the technical digest, quantity, price, the considered price assignment IDs, and the amount.

**Fixture** `backend/conversions/fuel-cost-1-cases-v1.json`:
- positive cases P1-P4: complete; shared edge counted once; open interval with `upper_minutes` null; non-terminating hours;
- unavailable cases U1-U17: every Architect C4 case, plus not-in-run, unverified span, negative power, and not-supported.

**Migration** `backend/migrations/versions/0011_financial_consequences.py`. Head: `0011_financial_consequences`.
- `financial_consequence_revision` :42.
  - CHECKs: an unavailable revision has no number; an unpriced revision has no amount and no currency; a priced revision has `amount_low = 0` and `amount_high = quantity_high × price_value`.
  - Uniques: `(finding_revision_id, type, revision_no)` and `(finding_revision_id, type, basis)`.
  - Same-Site foreign keys to the Finding, the FindingRevision and the price revision.
- Link tables: assessment :120, assumption :138 (with `assignment_id`), power interval :152.
- `financial_consequence_work` :182 is inserted only by the AFTER INSERT triggers :302/:316, on `financial_assumption_revision` and on `finding_revision`.
  - For a SUCCESSION, the affected range is `[valid_from, ∞)`.
- `financial_consequence_work_attempt` :211 has a single SUCCEEDED attempt per work item.
- Every table is append-only.
- The lineage trigger :249 requires that:
  - the window equals the FindingRevision's `episode_start/end`;
  - the Finding matches;
  - the revision number is +1 on its chain.
- The link trigger :284 requires an INTERVAL assessment of that FindingRevision.
- The migration adds `financial_assumption_revision_site_unique (tenant, site, id)`.

**Store (seventh writer)** `backend/assetops_backend/financials/adapters/postgres_consequence_store.py`:
- `load_input` :77 reads the exact inputs in one REPEATABLE READ snapshot.
- `append` :160 is idempotent:
  - it takes an advisory lock per FindingRevision and type;
  - a replay with the same basis returns the stored ID;
  - otherwise it appends revision n+1 at one `clock_timestamp()`.
- `pending_work` :234, `record_attempt` :244, `rows` :266.
- Built by `composition.build_consequence_store`.

**Guard** `tools/checks/configuration-persistence.ps1` rule 8:
- the consequence store may only insert into its 5 tables;
- no other module may write them;
- no module may write `financial_consequence_work`.

**C3** `backend/conversions/demo-diesel-price-publications.json` (version 2) adds `v4`: a CORRECTION to 1.28 USD over `[2026-10-01, 2026-11-01)`, expected prior v3.
- `run_fixture` in the S4-02a tests now defaults to steps v1-v3 (`S4_02A_STEPS`).
- `tools/s402a_assumptions_walkthrough.py` publishes only v1-v3, so the S4-02a evidence stays valid.

## Checks (as observed)

- `pytest tests/test_s4_fuel_cost.py`: 34 passed.
- Focused suites on the final code (`test_s4_fuel_cost.py`, `test_s4_consequence_store_postgres.py`, `test_s4_assumptions_postgres.py`): 60 passed, DB `assetops_s402b_test`.
- S4-02a suites (`assumptions_postgres`, `assumption_read_postgres`, `assumption_publication`): 54 passed.
- Full backend: **2014 passed**, 24 warnings, in 656.71s.
  - It ran on `5b4be01`. The fuel_cost/test edit in `8eb4ee9` landed during the run, and the focused suites were re-run on it afterwards.
- `tools/check-all.ps1`: **All 9 guards passed**.
- Frontend: no file changed, so the suite and build were not run. Layout evidence: not run (no UI in this phase).
- Non-vacuity proofs, each run on committed code and reverted with `git checkout --`:

| Mutation | Result |
| --- | --- |
| Containment check disabled | U3-U6 fail |
| Overlap check disabled | U7/U8 fail |
| Multiplier changed to 1.00 | parameter pin and P1-P4 fail |
| SFC-window check disabled | U12 fails |
| Considered assignment IDs removed from the basis | the new basis test fails |
| Migration priced-amount CHECK removed | DID NOT RAISE |
| Assessment-link trigger disabled | DID NOT RAISE |
| Finding dirty trigger moved off `finding_revision` | dirty-work test fails |
| Probe `INSERT INTO financial_consequence_work` and an UPDATE in the store, plus an INSERT in `financial_read_api.py` | `check-architecture` fails with three distinct messages |

## Deviations and open questions

Q1-Q10 are in `.agent/S4-02b-questions-1.md`. The most consequential:

- **Q9: ordinary Findings.** The S4 fixtures and walkthrough deliver only generator state, so every ordinary Finding is `QUANTITY_UNAVAILABLE` (`POWER_MISSING`). The positive Postgres case ingests generator-power interval means through the real Batch V2 path. It gives 2.75 L, which is 3.4375 USD at v1 and 3.52 USD at v4.
- **Q1: window shape.** The window CHECK is `<=`, because a zero-width episode stores as `NO_CANDIDATE_TIME`.
- **Q6: replay.** Replay of an identical earlier basis returns the older ID. Phase 2a must not treat that ID as current when the chain head differs.
- **L1 divergence (packet).** The technical design's single-assessment, single-assumption, scalar-quantity row is superseded by the 0011 shape. This is stated in the migration docstring.

## What phase 2a needs

**Recompute worker:**
- Read work with `pending_work`.
- For each work item, find the affected FindingRevisions:
  - `FINDING_REVISION_APPENDED`: that revision;
  - `ASSUMPTION_PUBLISHED`: Findings whose window overlaps `[affected_from, affected_to)` and whose latest revision is the selected one.
- For each revision, run `load_input`, `quantify`, then `select_window_price` over `PostgresAssumptionStore.snapshot(..., recorded_at=None)` `timeline`/`cited`, then `consequence`, then `append`.
- Finish with `record_attempt`, with the appended IDs on success or a typed error code on failure.

**Read** `GET /api/sites/{site}/findings/{id}/financial-consequences`:
- Use `rows`, or add paged SQL.
- `STALE/PENDING` when any of these holds:
  - the latest consequence's `price_revision_id` or considered assignments differ from the current window selection;
  - the latest FindingRevision is not the consequence's;
  - unprocessed work covers the window.
- Display rounding: low down and high up to the ISO minor unit.

**Bridge:** replace `finding_api.consequence_state` (S4-02a) with the stored consequence.

**Fixtures for 2a:**
- no price;
- future price: v2 leaves October current;
- full-window backdated correction: v4;
- partial correction, and a correction that makes a boundary cross the window. These need new test-scoped publications. Pick days off the ordinary S4 case days.

**Walkthrough:** add power means to an ordinary-path producer, or report "none qualified" (Q9).
