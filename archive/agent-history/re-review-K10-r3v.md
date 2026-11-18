# Re-review K10 R3v fix round

Verdict: ACCEPT. No High, Medium or Low findings.

Scope: `git diff 7b8d5ae68..HEAD` on `task/DIESEL-K10-declared-absent`. Three files changed: `chain/site_chain.py`, `tests/test_k10_declared_none_rule.py`, `.agent/review-packet-K10.md`. Nothing else changed.

## Items checked
1. `days_of` in `chain/site_chain.py`
   - It grades each day with `day_grade(per, measures, none_declared=nd)`.
   - The `none_declared` key is computed with `applicable_measures` and appears only when the list is non-empty.
   - The `measures` map is unchanged.
   - `why.py` is untouched.
   - The only new import is `applicable_measures` from `chain.reader`, which is inside `chain/`.
2. Tests: three new `test_r3v_*` functions.
   - COH-18 identity on a Kisiwa-shaped month. The tally of `days_of` grades equals `grade_counts_of` field by field, with partial 3 and no_data 28. The old call form gives partial 0, so the test is non-vacuous.
   - Other site types.
     - The test loops every site type in `MEASURES`: MINIGRID, COLDCHAIN and EV_CHARGING. Each runs with and without gaps, with empty `none_declared`.
     - Each case asserts tally equals counts, equality with a reimplemented pre-R3v function, byte-identical `json.dumps`, and no `none_declared` key.
     - This is a sound substitute for Kobo/Cold/EV-specific facts, because the rule depends only on `none_declared` being empty and the measure set.
     - A MINIGRID Site with empty `none_declared` is included, so the Kobo case is proven.
   - Day-entry shape.
     - The 10-28 shape gives PARTIAL, `productive_kwh` NO_DATA and `none_declared == [productive_kwh]`.
     - The 10-30 shape stays NO_DATA with the key present.
     - A no-row day is NO_DATA with no key.
     - A day with a `productive_kwh` row is COMPLETE with no key.
3. Mutations, run on a scratch copy of `backend` (no repo files edited). Each was killed by 2 of the 3 r3v tests.

   | Mutation | Tests that failed |
   |---|---|
   | M1: drop the `none_declared` argument | tally test, shape test |
   | M2: always emit the key | other-types test, shape test |
   | M3: put every measure in the key | other-types test, shape test |
   | M4: ignore `facts.none_declared` | tally test, shape test |

## Run
- Python: `AssetOpsV1-plan2\.venv\Scripts\python.exe`, with PYTHONPATH set to absolute paths under the k10 worktree.
- The three K10 test files, `test_ch5a1_reader.py` and `tools/checks/test_chain_coherence.py`: 229 passed, 11 skipped, 0 failed.
- The 11 skips are in the Postgres adapter file, since no DB was provided.

## Not verified
- The §9v.5 targeted re-check on the clone (needs the clone and a DB) was not run, as instructed.
