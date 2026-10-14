# S4-02b phase 2a handoff: read and recompute

Branch `task/S4-02b-fuel-consequence`, from `e45bbbc`.

Commits:
- `5d400d6`: carries M1, L1, L2, L3, the L4 backfill, L5 and L6.
- `1557b3f`: L4 test.
- `4238cf7`: M2/L7 documentation.
- `8edb321`: worker, read, route and bridge.
- `dfb95b1`: route test.
- `efd95fe`: demonstration spec.
- `ed0ddf3`: producer.
- `2caefdc`: questions.
- `2b76286`: boundary ordering.
- closeout: this file and `CODE_STATE`.

No UI was changed. That is phase 2b.

## Review carries (phase-1 review `.agent/S4-02b-phase-1-review.md`)

- **M1.** `PriceSelection.considered` holds the window-clipped `(revision_id, from, to)` tuples in time order (`fuel_cost.clipped`).
  - It replaces the assignment IDs in the basis, and is stored as `financial_consequence_revision.price_considered`.
  - `assignment_id` remains only as lineage in the link table.
  - Tests:
    - `test_reissued_assignment_ids_outside_the_window_leave_the_basis_unchanged` (pure);
    - `TestReviewCarries::test_a_later_succession_leaves_the_october_basis_unchanged_and_append_replays` (Postgres: v1, then append, then v2, then re-derive replays revision 1);
    - `test_unpriced_bases_over_different_price_boundaries_differ`, now with identical assignment IDs.
- **L1.** The work range CHECK is `<=`. Test: `test_a_zero_width_finding_revision_is_not_blocked_by_its_work_row`.
- **L2.** `PARAMETER_VERSION["reviewer"]` cites the Architect ruling and the phase-1 review. Review date 2026-10-14. The digest is re-pinned to `18595762…f852`.
- **L3.** A reading that does not span whole seconds refuses with `INTERVAL_NOT_WHOLE_SECONDS`. The duration is exact `(b-a)//1s`, and the DB CHECK compares the exact epoch.
- **L4.** Both options are taken; see questions-2 Q4.
  - Migration 0011 enqueues every existing FindingRevision.
  - The read reports "no consequence" as `PENDING`.
  - Test `test_upgrade_enqueues_finding_revisions_recorded_before_0011` downgrades to 0010 and upgrades again.
- **L5.** New tests:
  - one primary;
  - generator mismatch;
  - span inside the window;
  - the `financial_consequence_unpriced_has_no_amount` CHECK, matched by its own name.
- **L6.**
  - The lineage trigger checks that the price value and currency equal the price revision's.
  - A new deferred constraint trigger `financial_consequence_links_complete` requires that a PRICED row has its PRICE link, and that the assessment links are exactly the FindingRevision's INTERVAL assessments.
- **L7 / M2.** Q9 is corrected in `.agent/S4-02b-questions-1.md`, in the phase-1 handoff and in `CODE_STATE`. Over the ordinary S4 data: 8 `POWER_MISSING`, 2 `FINDING_NOT_SUPPORTED`, and 1 F01-gateway `POWER_COVERAGE_GAP`. The fixture v4 note is in `CODE_STATE` and in the S4-02a phase-1 handoff.
- Migration 0011 was edited in place, because it is unmerged.

## Built (anchors)

**Worker** `backend/assetops_backend/financials/recompute.py`:
- `derive` :65, `ConsequenceRecomputeWorker.process` :102, `run_pending` :127.
- `FINDING_REVISION_APPENDED` recomputes that exact revision. `ASSUMPTION_PUBLISHED` recomputes the latest revision of each overlapping Finding.
- Failure records a typed FAILED attempt (`STORE_UNAVAILABLE`, `FINDING_REVISION_NOT_FOUND` or `RECOMPUTE_FAILED`) and the item stays pending.
- Success records with `skip_if_succeeded`.
- CLI: `python -m assetops_backend.recompute_consequences run|pending --site KOBO-001` (`backend/assetops_backend/recompute_consequences.py`).

**Store additions** `financials/adapters/postgres_consequence_store.py`:
- `record_attempt(skip_if_succeeded)` :246;
- `latest_revisions_overlapping` :274;
- `locate` :287;
- `chain` :297, one REPEATABLE READ snapshot holding the head, the exact revision, a keyset page, the links, and the pending work touching the window.

**Read** `financials/consequence_read.py` `ConsequenceReadService.read` :143:
- `currentness.state` is `CURRENT`, `STALE`, `PENDING` or `HISTORICAL`. It compares the head's basis with a fresh derivation. STALE carries reasons and `derived_now` (price selection only, no amount).
- Each revision DTO carries:
  - window, model, parameter digest and reviewed flag;
  - quantity, price including `considered`, and the unrounded amount;
  - `display`, rounded outward to the ISO minor unit (`MINOR_UNITS`; an unknown currency gives `MINOR_UNIT_UNKNOWN`);
  - limitations, including the Q3 as-accepted SFC limitation;
  - digests;
  - lineage: assessments, assumptions with their assignment, power intervals and evidence IDs.
- Only a CURRENT head has `presented_as_current`.

**Route** `finding_api.py` :245 `GET /api/sites/{site}/findings/{id}/financial-consequences?revision_id=&consequence_revision_id=&after_revision_no=&limit=`:
- It has the Finding read's scope, gate and 401/403/404 semantics. A missing or failing consequence store gives 503 `CONSEQUENCE_STORE_UNAVAILABLE`.
- `consequence_revision_id` on its own selects that revision's FindingRevision.
- A foreign or unknown ID gives 404 and never falls back.
- Links: `consequence_revisions`, `evidence_records` (S4-03 record route), `price_revisions` (S4-02a revision route), `api_next_page`.

**Bridge** `/financials`:
- `bridge_consequence` :336 replaces `consequence_state`.
- An amount `{low, high}` (display strings) appears only for a CURRENT PRICED head. Otherwise the bridge gives a typed state with no amount.
- Without a store, the state is `UNAVAILABLE`.
- Wired in `main.py` through `financials/composition.build_consequence_read_service` and `CONSEQUENCE_UNAVAILABLE`.

**Owner demonstration case** `backend/conversions/s4-power-demo-cases-v1.json`:
- `P01-power`, 2026-10-23: a 0 kW mean, then 20 kW 5-minute means ending 06:05 to 08:00, plus context. It is labelled AUTHORED DEMONSTRATION.
- `s4-finding-cases-v1` is unchanged.
- Postgres test `test_s4_power_demo_case_postgres.py`:
  - a SUPPORTED Finding `[06:05, 08:00)` with 23 intervals and 12.65 L;
  - **15.8125 USD at v1, displayed 15.82**;
  - after v4, revision 2 at **16.192 USD, displayed 16.20**, with the same technical digest.
- Producer `tools/s402b_power_cases.py run [--db assetops_s402b*]`:
  - runs the unchanged S4 producer, then P01-power over TLS with the registered gateway credential;
  - writes into its own database (default `assetops_s402bcases`);
  - uses ports 8904/8905.

## Checks (as observed)

- Focused suites (`test_s4_fuel_cost`, `test_s4_consequence_read`, `test_s4_consequence_store_postgres`, `test_s4_consequence_recompute_postgres`, `test_s4_power_demo_case_postgres`, the S4-02a assumption suites and `test_s4_assumption_read_api`):
  - **129 collected**.
  - The first run had 1 failure: the boundary-order assertion depended on UUID order. The fix in `2b76286` sorts by time. The affected tests then passed three times in a row.
  - The full suite below covers all of them.
- Producer run `tools/s402b_power_cases.py run --db assetops_s402b2_cases_test`:
  - **0 check failures**, `VERIFY PASSED`;
  - P01-power: 25 power means and 150 context readings, 1 new SUPPORTED Finding;
  - F01-gateway as before.
- On that database: publish v1-v3, then `recompute_consequences run`. Over the 12 latest FindingRevisions:
  - 8 `POWER_MISSING`, 2 `FINDING_NOT_SUPPORTED`, 1 `POWER_COVERAGE_GAP` (F01-gateway 05:15);
  - P01-power **PRICED 15.8125**.
  - Then publish v4 and run: one appended revision, P01-power revision 2 at **16.1920**. Every other item replayed.
- Full backend suite and `tools/check-all.ps1`: see the closeout section below.
- Frontend: no file changed, so neither the suite nor the build was run. Layout evidence: not run (no UI in this phase).
- Non-vacuity. Each mutation was made on committed code and reverted with `git checkout --`:

| Mutation | Result |
| --- | --- |
| One-primary check off | 1 failed |
| Generator mismatch off | 1 failed |
| Span-in-window off | 1 failed |
| Whole-seconds check off | 1 failed |
| Basis back to assignment IDs | 3 failed |
| L1 CHECK back to `<` | 1 failed |
| `unpriced_has_no_amount` removed | 1 failed |
| L6 price value check removed | 1 failed |
| L6 PRICE link check removed | 1 failed |
| Migration backfill removed | 1 failed |
| STALE comparison off | 2 failed |
| Head presented as current regardless | 1 failed |
| Failures recorded as success | 1 failed |
| Display high rounded down | 2 failed |
| Bridge shows an amount when not current | 1 failed |
| Pinned consequence fallback | survived at first; killed after `dfb95b1` added the foreign-revision case (1 failed) |
| `considered` dropped | 1 failed |

## Deviations

- The bridge response shape changed (Q7). The S4-02a frontend words every non-`QUANTITY_UNAVAILABLE` state as "No price for the whole window" (`SiteFinancials.tsx:481`). Do not show the S4-02a UI over a 2a database before 2b.
- Currentness has four states rather than one `STALE/PENDING` label (Q1).
- Evidence acceptance enqueues no work (Q2). A head whose technical input drifts shows `STALE` until something recomputes it.

## Questions

`.agent/S4-02b-questions-2.md` Q1-Q9. Each one has a fail-closed default built. None needs the Architect before 2b.

## What 2b needs

**UI over the read:**
- Use `GET .../financial-consequences` (current, pinned and history) and the bridge `consequence`.
- Show the amount only when `consequence.presented_as_current`, using `display.amount_low/high`.
- STALE and PENDING show no amount. HISTORICAL and pinned revisions are labelled as history.
- Update `frontend/src/sites/financialsClient.ts:79` (state union) and `SiteFinancials.tsx:481` wording for `PRICED`, `STALE`, `PENDING`, `HISTORICAL` and `UNAVAILABLE`.
- Lineage and details: model, multiplier, parameter digest, `MODELLED_CONDITIONAL`, power intervals, evidence links (`links.evidence_records`) and price revision links.

**Walkthrough data preparation:**
1. `.venv/Scripts/python.exe tools/s402b_power_cases.py run` creates the template `assetops_s402bcases` in about 2.5 minutes.
2. `CREATE DATABASE <walk> TEMPLATE assetops_s402bcases`.
3. `publish_assumption fixture --site KOBO-001 --file backend/conversions/demo-diesel-price-publications.json --step v1 --step v2 --step v3`.
4. `python -m assetops_backend.recompute_consequences run --site KOBO-001`. This gives P01-power PRICED (15.82) and F01-gateway `POWER_COVERAGE_GAP`.
5. For old/new: publish `--step v4`, read once before the run (STALE), then run again (revision 2, 16.20).
6. For the unpriced and pending views: use an empty-price copy (before step 3: P01-power PENDING, then after a run UNPRICED `NO_PRICE`). Or use a test-scoped correction inside `[06:05, 08:00)` for `PRICE_SPANS_WINDOW`.

**At the checkpoint:** label P01-power as an authored demonstration case beside F01-gateway (owner ruling). Report 0 of 11 ordinary Findings qualifying, with the reasons above.
