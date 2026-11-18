# S3-01 phase 1 fix round 1: re-review

Reviewer: a fresh Claude reviewer. Commit reviewed: 733ea8d (only that commit).

## Verdict: accept

F1 and F2 are fixed. No block findings. Nothing else moved: the commit touches only the packet, `demo_configuration.py` and `test_s3_demo_configuration.py` (plus the pre-existing unrelated modified handoff file, not part of the commit).

## F1 (packet values): confirmed

I compared every case row in the packet against `.agent/S3-01-dispatch-cases-v1.manifest.json`.

- Contradiction row: SOC 69.1875 / 76.6875, at 2026-10-06T05:00Z, 2 evidence rows. Matches `precondition.values` and `source_time`.
- Windows (03:00-11:00 UTC on 10-01 to 10-05) and epochs (epoch-1; epoch-1 plus epoch-2 for 10-05) match.
- Accepted counts match: 260, 326, 326, 322, 322, 654, 656, 2.
- Row 3 has 5 instants and row 4 has 3. The gap is 06:00-06:45. The late reading is SOC 07:00 published 07:10. Doubled/differing is 325/42. All match.

## F2 (bindings alone): confirmed

- `apply_demo_configuration` now refuses `bindings` without `properties` unless `_properties_in_effect` is true at `bindings.effective_from`. The check sits before any publish, so the refusal raises `DemoConfigurationConflict` with a clear message and writes nothing.
- The test asserts the revision and binding-set counts are unchanged after the refusal. It then runs `properties` and `bindings` as separate steps and checks the result is fully configured. So it covers the refusal, the no-write guarantee and the separate-runs path. The implementer reports it failed before the fix. I did not re-run that.
- The combined `properties` plus `bindings` path is unchanged. The existing tests for it still pass.

## Checks I ran

- `pytest test_s3_demo_configuration.py test_s3_role_vocabulary.py`: 10 passed, 1 skipped.
- The skip is presumably the Postgres-backed test, because Postgres is not configured for me. So I could not verify the implementer's 11-with-Postgres figure.
- I did not run check-all or the frontend checks, and they are out of scope for this commit.

## Findings

- Block: none.
- Carry: F3-F6 from the original review are unchanged and remain carried. The Architect rulings commit (1b9b058) covers them.
