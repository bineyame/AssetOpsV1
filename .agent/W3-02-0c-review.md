# W3-02 0c review (pinned cold/EV/money facades)

Reviewer: fresh Claude reviewer (did not author). Code `750ce929`, handoff `c88ef3f6`, branch
`task/W3-02-estate-evidence-money-basis`. Authority: `main:.agent/W3-02-build-spec.md` closure 4 ("W1 day source,
cold/EV windows and pinned facades", third and fourth paragraphs; `0c` row), closure 5 B5, "Money and proof
corrections", and W3-01 Run 7 Q7-1 / Run 8 rulings (`main:.agent/W3-01-build-spec.md`). Read only through git objects;
tests ran on a `git archive` export of `750ce929` in the reviewer scratchpad.

## Verdict: REVISE

One High (the newer-head refusal), one Medium (vacuous cold money proof on Postgres). Everything else is accepted.

## Findings

### H1 - a later recompute makes every historical estate money read 409 (defect; fix follows existing precedent)

`backend/assetops_backend/analytics/cold_site_reads.py:_money` (new `cutoff` branch, `newer = ... created_at > cutoff`
then `raise ColdPinnedLineageUnavailable`) and `backend/assetops_backend/ev_site_reads.py:_select` (`current["recorded_at"]
> cutoff` then `raise EvPinnedLineageUnavailable`). Both exceptions are in `PostgresEstateRead.inconsistent`, so after the
W3-01 one retry the whole estate Financials response is 409 `ESTATE_SELECTION_INCONSISTENT`.

What is wrong. `cold_heads_on` returns the *highest* revision per (FindingRevision, kind) with no time bound; the facade
refuses if that head postdates the estate cutoff. A cold consequence is re-derived (new `revision_no`) on any later
assumption/price change or recompute. After that, a Financials read at any explicit `known_at` before the recompute
fails permanently, although the head that was current at that cutoff is stored, immutable and provable. EV is the same
for a later revision with the same derived basis.

Why it is a defect, not a ruling gap:
- Spec: refusal is for when "the pinned selection cannot be proved"; "never pick a newer head" forbids the newer head,
  it does not require refusing. "Financials selects every exact persisted head **under cutoff**" and "Historical
  selection keeps IDs but no current claim" both require the as-of head.
- W3-01 Q7-1 is the direct analogue: choose the greatest eligible seq *after* the cutoff predicates; its
  "Historical reselection proof" requires a repeat read at `known_at=K` to return the first seq, IDs, rows and identical
  token after a later reselection. A later write must not change, let alone break, a historical read.
- W3-01 already selects the cold consequence as-of: `postgres_estate_read.py` (c2 r1 L2) uses
  `cold_consequence_revision ... finding_revision_id = :r AND created_at <= :k ORDER BY revision_no DESC, id DESC LIMIT 1`.
  W1's `select_consequence_on` also returns the head recorded by `:k` (this commit's own Postgres test reads revision 1
  at `created_at` while revision 2 exists). So 0c is inconsistent with both other domains in the same estate read, and
  W3-01's Findings/scope would name a cold consequence ID that W3-02 Financials then 409s on.

Fix (on the branch, Lane A): select the as-of head instead of refusing. Cold: a cutoff-bounded variant of
`cold_heads_on` (`created_at <= :k` before `DISTINCT ON`, the W3-01 predicate), used only by the pinned path; no head by
`k` means no row for that kind (W1's PENDING/"No consequence recorded" semantics), never a newer head. EV: bound
`select_on` by `recorded_at <= :k` on the pinned path; none means the existing `STALE_BASIS`/pending guard with older
history. Keep the typed refusal only for an unprovable pin. Replace the two pure "refuses newer head" assertions with
"selects the as-of head and ignores the newer one", and add one Postgres case per domain: read at K, recompute, read at
K again, same IDs (the Q7-1 shape). The store file is a Lane A shared file, so this stays in 0c.

Architect only for one EV sub-point: `ev_money_basis_on`/`tariff_on` derive the basis from *current*
(`recorded_to IS NULL`) tariff assignments, so after a later tariff change a historical EV read derives a different basis
and finds no as-of head (STALE_BASIS) even with the fix. Whether the historical EV basis must use tariff assignments as
recorded at K is a W2-07 q4 selector question; fail-closed STALE_BASIS is acceptable until ruled. Do not block the cold
fix on it.

### M1 - the cold Postgres money comparison is vacuous (0 heads)

`backend/tests/test_w302_pinned_facades_postgres.py::test_cold_facades_match_the_w2_site_window`. The fixture runs only
the cold *assessment* worker; no cold consequence worker runs. I re-ran the test body with a probe print on a private
DB: `findings 2, heads 0`. The assertion `[r["id"] for r in money["consequences"]] == [... expected_heads ...]` is
`[] == []`, and `withheld`/`hold` are not compared with W2 at all. So on real Postgres no stored cold head, no
`counted`, no both-kinds row, no `_consequence_row` basis and no cutoff behaviour is exercised; cold heads are proven
only against the pure `ColdMoney` stub. That is not enough for the facade Financials will build on: the stub cannot
catch a column/shape mismatch with `cold_heads_on` (`created_at` type, `id` as UUID, `kind` values).

Fix: run the W2-04 cold consequence worker in that fixture (as `test_w204_*` do) so at least one `PRODUCT_EXPOSURE`
head exists; assert `len(expected_heads) >= 1`, equal `withheld`/`hold` to W2's `_money`, and (with H1) the as-of
read before/after a second consequence revision.

### Low (not blocking)

- L1 `cold_site_reads.py:_money` pinned path: `cold_pending_on` excludes work that has a SUCCEEDED attempt *now* and
  reads `last_outcome` *now*, so a historical read can show work as not pending, or as FAILED, by today's attempts.
  Run 8 ruling 6 says not to project today's job status backward. Money is non-current under HISTORICAL anyway; bound
  attempts by `k` when H1 is fixed, or record as known limitation.
- L2 Live race: `k` is `SELECT now()` (reader transaction start) while EV `recorded_at` is `clock_timestamp()`; a head
  committed between BEGIN and the snapshot-taking statement is visible with `recorded_at > k`. Today that is a spurious
  409 (retried once); after H1 it is merely not selected. Negligible after H1.
- L3 EV `_pinned_ctx` checks `len(selection_seqs) == 1` but not that the seq's analytic key is the EV session analytic.

## Readings classified

1. Provable-pin definition and typed `*PinnedLineageUnavailable` mapped to 409 - **accept** (matches closure 4/5 B5
   and Q7-1 two-cutoff split; `known <= selection_cutoff` and `<= watermark` checked).
2. Newer head refused, no older-head fallback - **reject: defect H1.** The "older head" is not a fallback; it is the
   as-of head, which spec, Q7-1 and the W3-01/W1 precedent all select. Cold fix needs no new ruling; only the EV
   historical tariff-basis sub-point goes to the Architect.
3. Later cold work does not withhold; later EV history dropped - **accept** (see L1 for attempt state).
4. Cold returns both kinds with `counted` - **accept** (closure 4 "including both cold PRODUCT_EXPOSURE and
   RECORDED_REPAIR"; RECORDED_REPAIR separate).
5. EV omits per-row `source_provenance` - **accept**; `money_row_provenance_on` exists for Lane B.
6. `power_evidence_ids` not renamed - **accept**; spec names `technical_interval_ids` on the cross-domain wire only and
   the docstring records the mapping.

## Other checks against the brief

- `capabilities_on`/`money_on` (cold, EV): built without `_ctx`/`open_on`/`_selected`/`overview`/`evidence`/
  `financials`; the Postgres tests monkeypatch those to fail and stay inside the caller's transaction. Correct apart
  from H1.
- `select_consequence_on`: six keys added, null without a head; old keys and the `created_at <= :k` cutoff untouched.
  The only consumer (`estate/coverage.py:_mini_grid_money`) reads keys explicitly, so W3-01 wire is unchanged. The
  Postgres test checks the fields equal the stored row for revisions 1 and 2 and null when PENDING - non-vacuous.
- `imported_sites` adds `site_code_key`, keeps old keys and ordering. Accept.
- `financials/composition.py:build_ev_money_reads` - accept; a thin factory forced by the adapter-import guard, no
  behaviour. `estate/composition.py` shares the estate owner's cold/EV services. The extra
  `build_cold_consequence_store(url)` engine is unused by the `_on` static reads (harmless).
- Default behaviour: `_money(cutoff=None)` and `_select(cutoff=None)` are byte-identical to W2 in effect; the pure tests
  assert the default still withholds on later work and still returns the newer head. Non-vacuous.
- Pure tests are non-vacuous for the pin-proof cases (7 cold, 7 EV, both facades each).

## Checks run

- `pytest tests/test_w302_pinned_facades_postgres.py tests/test_w302_pinned_facades.py` (export of `750ce929`,
  private DB `w302rv0c_test`, dropped after): 19 passed (3 Postgres via a probe copy + 16 pure), 78.5 s. The probe copy
  only added a print, which showed the M1 zero-head result.
- Guards in a detached `git worktree` of `750ce929`: `check-agent-workflow` passed; `check-architecture` passed
  (exit 0) once `ASSETOPS_GUARD_PYTHON` pointed at the main `.venv`. Without it, Rule 8 cannot find an interpreter
  in a fresh worktree, which is environmental and not a finding.
- Not rerun: the implementer's 191-test focused run (code revision `5c241fa5`, not `750ce929`) and its 36-test re-run
  on `750ce929`; I cite them, they are not same-revision for the 191. No full suite (not due until commit 4).
  Frontend unaffected by this commit; not run.
