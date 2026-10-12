# S3-01 phase 2 fix round 1 - verification re-review

Produced by a fresh Claude reviewer. Diff reviewed: `065058c..HEAD` (54b037d, 1522565, 0de2b5d).

## Verdict: ACCEPT. F1 and F2 are fixed. One carry, no block.

## F1 - confirmed fixed
- `dispatch_v3.py:503-535`: every segment that is `INDETERMINATE` with a `missing` entry adds a named `EVIDENCE_GAP: interval from ... Indeterminate over start..end: ...` limitation, so the window becomes `LIMITED`.
- The exclusion list matches the four modelling-only strings emitted at lines 294, 300, 308 and 323. Missing, NOT_GOOD, CONFLICTING and the generator-state gap (line 415) are the strings that remain, so they are still flagged.
- The decision table Claims paragraph is updated. The new test builds a 45-minute PV-capability gap inside a running interval and asserts: the Indeterminate portion is non-zero, the window is `LIMITED`, and an `EVIDENCE_GAP:` limitation is present. It is meaningful. I did not re-run the pre-fix failure; I accept the packet's claim, which the test shape supports.
- Analytic file: 17 passed (run by me).

## F2 - confirmed fixed
`WINDOW` and `LATER` are now `None` when no DB URL is set. `pytest backend/tests -q` with no database: 1688 passed, 108 skipped, no collection errors (run by me).

## Producer normalize() change
- **The fix is correct.** `Decimal.normalize()` followed by `:f` strips the trailing zero, so `66.0` becomes `66`. The contract wants a canonical decimal string, and the failing input was non-canonical.
- **Edge case:** `normalize()` on an integral value with trailing zeros (for example `100`) gives `1E+2`, and `:f` formats that back to `100`. So the output is safe.
- **A differing Lab value is not a Lab non-determinism finding.**
  - Seeds are fixed (`seed=20261001` and so on).
  - The template is the first state-of-charge envelope with a value, found by walking `main["batch_ids"]`. That order comes from the case record and the gateway DB, so it is run-timing dependent.
  - Tenant, site, revision and batch ids are fresh per run. `all_evidence_id_sha256` therefore changes every run, and the manifest says `produced_from_commit` differs too.
  - The replay claim holds at the level of procedure, seeded scenarios and `verify` after reload: VERIFY PASSED, digests match, cutoff-A run still selects window revision 1.
  - Byte-identical evidence across runs was never available, and the packet does not claim it.
- **CARRY (not a block):** make template selection deterministic. Choose the SOC envelope by minimum `(source_time, sequence)` and not by container order, and state in the manifest that evidence ids are per-run. A non-trivial SOC base value differing between two runs of identical seeds was not root-caused. I did not investigate whether the Lab is truly seed-stable or whether only the pick differs.

## Checks I ran
- Analytic: 17 passed.
- `pytest backend/tests -q`, no DB: 1688 passed, 108 skipped.
- Not run by me: the Postgres suite (1796), `tools/check-all.ps1`, the producer rerun, and the frontend. The first three are the implementer's claims; none of them is a frontend surface.
- I did not touch the owner's servers or `var/`.

## Residual risk
F3-F6 remain carried to phase 3 per the prior review.
