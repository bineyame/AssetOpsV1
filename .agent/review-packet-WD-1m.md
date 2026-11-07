# Review packet: WD-1m (mill verdict reads "on example data", class stored at judging)

Task: FUEL-1 WD-1m, WD-1m-R2 route (c). Branch `task/FUEL-WD1m-mill-example-label`. WIP `0bc9c2e14` kept; build on top in `c79fecbce`.

## Outcome
- Write path: `ActionStore.example_source_class(tenant, site, days, timezone, known_at)` (port + `PostgresActionStore`), SQL = the WIP lateral body, parameterised; empty days returns None without a query. `MiddayShift.evaluate` calls it once after `decided`; `outcome_rows(..., source_class)` writes `details.source = {"source_class": X}` (None allowed), never `basis` (`basis_sha256` unchanged).
- Read path: WIP evidence lateral deleted; `_SITE_ACTIONS` lateral `v` selects `o.details->'source'->>'source_class'`. WIP pass-through kept. `mini.py` uses `provenance_suffix(a.source_class)`. Merged diff has no `accepted_evidence` in `postgres_chain_read.py` (L0 test pins it).
- Verdict page wire: `outcome.source_class` in `summary_wire` (wire only, not shown).
- MILL-5: `mill_assure(..., code, page, site)` reads the class from the verdict-page body; on Kobo it asserts `class in EXAMPLE_SOURCES`.
- No fakes needed the method (no in-repo fake store runs `evaluate`); no `getattr` fallback. No cap change needed in `test_ch9b1_origin_readers.py`.

## Before / after mill line (Kobo Assure "Verified results")
- Before: `ACT-002 verified` (display code of the mill). After: `ACT-002 verified on example data` when the stored class is an example class (Kobo story: `REGISTERED_SIMULATION` per the stored-class tests; the demo data itself needs the E3 rebuild to carry it).

## Speed (268,800-row harness, 57,600 rows in the used window)
- Board query `_SITE_ACTIONS` (EXPLAIN ANALYZE, last of 7 runs): 0.997 ms; plan reads only chain_action / verification_outcome (index scans), no evidence. Limit 50 ms: PASS. (Median of the 7 was not captured; the one printed run is the evidence.)
- Verdict-time `example_source_class`: 813 / 594 / 750 ms over three calls (EXPLAIN ANALYZE 875 ms, index-led, 57,600 rows joined). Limit 3 s: PASS.

## Tests and proofs
- Parity (Postgres): cases 1-6 against `store.example_source_class` with the `link_rows_on`/`link_of` reference; case 3 asserts `classify` does not give a positive class. Case 7 replaced: stored `details.source == {"source_class": None}`; with the key removed (append-only trigger lifted inside a rolled-back transaction) `_SITE_ACTIONS` reads NULL; MINI_TRIAL rows NULL and unchanged. New end-to-end: `evaluate` over a committed published batch stores REGISTERED_SIMULATION, `_SITE_ACTIONS` returns it, `summary_wire` shows `outcome.source_class`. 3 passed.
- Non-vacuity: removing the `= ANY(:days)` line fails case 4 `(4, 'REGISTERED_SIMULATION', None, None)`; removing `received_at <= :k` fails case 5 `(5, 'REGISTERED_SIMULATION', None, None)`. Both restored with `git checkout --`.
- L0: board entry suffix with/without class; `outcome_rows` details.source for None and an example class with `basis` JSON and hash byte-equal and wire value; `_SITE_ACTIONS` has no `accepted_evidence`; MILL-5 self-test: plain entry on an example page FAILS, and None class on the Kobo page FAILS.

## Goldens
See report; allowed diffs only (stored mill `details.source`, mill verdict-page `outcome.source_class`, Kobo mill suffix).

## Known deviations
- Case 6 is "00:30 Site-local" (Nairobi is UTC+3), as in the WIP.
- A broken publication link can still label (conservative: it can add the words, never remove them); no S4-05 commitment checks.
- Does the verdict page itself say "on example data"? No; out of scope (the wire now carries the class).

## Residual risk
- A verdict stored before WD-1m has no `details.source` and shows plain until the E3 rebuild; no backfill (`verification_outcome` is append-only).
- Verdict-time query is ~0.6-0.9 s at 57,600 rows in window; higher real volume scales linearly.
- Speed harness is scratch (not committed).

## User review focus
Screen wording only: the mill line gains " on example data"; joins the post-W6 walkthrough.
