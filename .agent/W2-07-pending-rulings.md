# W2-07 pending rulings (implementer, run 1, 2026-10-20)

Raised after spec commit 1 (`0026_w2_ev_money`). R2 blocks commit 2; the others are recorded so the Architect can
rule them in one pass. Each lists concrete options; the implementer has not chosen where marked **open**.

## R2 (High, blocks commit 2): tariff recorded-time visibility versus the simulated cutoff — open

Spec: "price every included interval with exactly one published revision valid then and visible at cutoff"; the
golden example shows tariff `recorded_at` `2026-10-06T08:00:00Z` before `known_at` `09:05`; vectors require
ESTIMATED `8.33250000` for the replayed cases. Code reality: `PostgresAssumptionStore.publish`
(`financials/adapters/postgres_assumption_store.py:131`) stamps `recorded_at = clock_timestamp()` (real server time,
2026-10-20 today), while every W2-05b replay knowledge cutoff/watermark is simulated 2026-10-06 09:00/09:05. A tariff
published through the only authorized path is therefore never "visible at" the replay cutoff, so all six vectors
would be `UNPRICED/TARIFF_MISSING` and the ESTIMATED acceptance is unreachable.

- **A.** Evidence cutoff governs evidence only. The worker prices with tariff assignments *current at derivation*
  (`recorded_to IS NULL`) valid for each interval; the consequence stores its own `recorded_at` and tariff revision.
  A read at an earlier `known_at` shows the consequence whose session basis matches the selected assessment, and a
  tariff/consequence recorded after that `known_at` is labelled by its own `as_of` (not hidden). Vectors reachable.
- **B.** Keep "visible at cutoff" literally; replay tests must move their simulated clock past real time (not
  possible with the pinned W2-05b manifests) or vectors change to UNPRICED. Acceptance amended.
- **C.** Let the SYSTEM_FIXTURE channel carry an explicit authored `recorded_at` (publisher semantics change for
  diesel too; needs a decision on monotonic series time).

## R1 (Medium): the 0026 source-gate trigger never fires for an ordinary new batch — open

The ledger inserts `batch_publication_link` (`evidence/adapters/postgres_evidence_ledger.py:336`) before the batch's
`accepted_evidence` rows (`:531`) in one transaction. The literal 0026 `ev_consequence_on_source_gate` checks
`EXISTS accepted EV row in NEW.batch_id`, which is false at link time, so it enqueues nothing; the accepted-evidence
trigger enqueues the same windows instead. `test_w207_ev_money_postgres.py::test_0026_trigger_only_work_and_exact_
conflict_constraint` pins this actual behaviour (a real late link INSERT, no SOURCE_GATE row).

- **A.** Accept as is: the accepted trigger covers every new EV batch; source-gate stays a guard for a link appended
  to an existing batch (no current product path). Amend the spec's "one source-gate INSERT" proof accordingly.
- **B.** Make it `CREATE CONSTRAINT TRIGGER ... DEFERRABLE INITIALLY DEFERRED` so it runs at commit after the rows
  exist (one migration-text change; rule-8 arbiter unchanged).
- **C.** Drop the source-gate trigger from 0026.

## R3 (Low): "publish an authored test tariff through the existing API"

`POST /api/sites/{code}/financial-assumptions` (`financial_api.py:60`) never succeeds by design (no verified human
principal; always 401). The only authorized publisher is the server-side SYSTEM publisher
(`PostgresAssumptionStore.publish` with `SYSTEM_FIXTURE`/`SYSTEM_CLI`). Implementer reading: tests publish through
that store call (no direct row seed). Options: **A** ratify; **B** add an authorized route (out of W2-07 scope).

## R4 (Low): ISO 4217 validation — implemented, needs ratification

Spec: "the API validates a real ISO code"; "unsupported currency code refused by publication". Implemented in
`financials/assumptions.py` for the EV key only: an embedded list of active ISO 4217 alphabetic codes
(`CURRENCY_NOT_ISO`), plus `VALUE_NOT_POSITIVE` for EV value <= 0. Diesel keeps its existing three-letter shape rule
so its publication behavior is unchanged. Options: **A** ratify (EV-only list); **B** apply the list to diesel too;
**C** shape rule only (then "ABC" would publish and only a malformed code is refused).

## R5 (Medium, commit 2): reason when a window is both incomplete and untariffed — open

Vector table: missing-meter is `UNPRICED/INCOMPLETE_ENERGY` (stated with the authored tariff present). With no tariff
the spec also says "otherwise eligible cases are `UNPRICED/TARIFF_MISSING`". For missing-meter with no tariff:
**A** `INCOMPLETE_ENERGY` (quantity gate first); **B** `TARIFF_MISSING` (price gate first).

## R6 (Medium, commit 2): one window holding an eligible session and a contradictory or incomplete one — open

The vectors each hold one session. Spec: incomplete sessions are excluded from pricing "while displaying their
supported partial kWh separately"; contradictory evidence withholds. For a mixed window:
**A** incomplete sessions are excluded and the eligible subset is ESTIMATED; any CONTRADICTORY session (or a
duplicate interval ID) withholds the whole window (`WITHHELD/CONTRADICTORY_EVIDENCE`); **B** price the eligible subset
in both cases and only exclude the contradictory session; **C** any non-eligible session makes the window UNPRICED.

## R7 (High, blocks commit 2 start): q1 R1's premise does not hold — open (run 2, 2026-10-20)

q1 R1 assumes "the ledger inserts the link before accepted rows in one transaction". It does not. In
`backend/assetops_backend/evidence/adapters/postgres_evidence_ledger.py`, `open_batch` (`:287`, link INSERT at
`:336`) and `decide_chunk` (`:430`, accepted INSERT in `_persist` `:531`) each run in their own
`_run(write=True)` -> `engine.begin()` transaction (`:145-149`); `ledger_service.py:147` and `:183` call them
separately (and `decide_chunk` per chunk). A `DEFERRABLE INITIALLY DEFERRED` constraint trigger therefore fires at
`open_batch`'s commit, when the batch still has no accepted row, and enqueues nothing.

Empirical proof (trial on top of `7cbe440c`, reverted, not committed): R1's exact trigger text plus R1's
equality assertion in `test_0026_trigger_only_work_and_exact_conflict_constraint` fails — the expected
`SOURCE_GATE` row for window 08:00-09:05 of the late batch is absent (`Extra items in the right set`).

Options (Architect to choose; none implemented):
- A. Leave `ev_consequence_dirty_source_gate` as committed (link-time; inert for ordinary batches, live for a link
  added to a batch that already has EV rows) and additionally enqueue `SOURCE_GATE` from the existing
  `ev_consequence_on_accepted` when `NEW.batch_id` has a `batch_publication_link` (dirty locator = batch_id, so the
  scoped `ON CONFLICT ... DO NOTHING` keeps one row per window/batch across chunks). Test: none before the batch's
  first accepted EV row commits, one per window after, none on re-enqueue, none for a linked batch without EV rows.
- B. Keep commit 1 as-is (accepted trigger's `ACCEPTED_EV` work carries ordinary batches) and restate R1's test as
  "no SOURCE_GATE row for an ordinary batch; ACCEPTED_EV row present".
- C. Change the ledger so link and accepted rows share one transaction — out of W2-07 scope (S2 ledger seam).
