# Re-review K10 R3t4 (e6604ebf4..51c037445)

Verdict: **ACCEPT**. No High or Medium findings.

## Checks
1. Gate: `site_never_declared` (reader.py) and the adapter's `declared_none_of` return `frozenset()` when any known revision has a productive load, else run `declared_none_day` per day. `_DECLARED_NONE` is still one statement. The validity-span filter and `lo`/`hi` params are gone. The known-at-k filter is intact: `recorded_at <= k` (or k NULL) and `superseded_at IS NULL OR > k`. The filters sit in the LEFT JOIN `ON`, so a Site with no revisions still returns its timezone row. Superseded-before-k and recorded-after-k revisions are excluded. `valid_from` is NOT NULL in the schema, so the `vf is not None` guard only drops the empty-join row.
2. Tests: all R3t4 items are present. Kobo history is covered on 4 windows in both the pure and adapter files. Kisiwa-shaped results are kept. Superseded-before-k and recorded-after-k mills do not block (adapter only; the pure file cannot model them, and the packet says so). A mill valid only after the window blocks. The R3t3 cases are covered on a never-declared Site (cases 6 and 11 are checked as blocked by the gate).
3. The three changed cases (pure bounds test lines, adapter case_6, revision-change-with-load) now expect `frozenset()` and are correct: each Site has a mill revision.
4. Mutations (scratch copy under the session scratchpad; repo tree clean afterwards):
   - M1, drop the gate: 7 failed (3 pure, 4 adapter).
   - M2, ignore the superseded filter: 1 failed (the superseded/recorded-after test).
   - M3, ignore the recorded_at filter: 2 failed.
   - M4, gate looks only at open-ended revisions: 3 failed.
5. Packet re-run evidence: plausible against the code. Kobo has a mill revision from 10-08, so the gate returns an empty set for any window. Kisiwa has no productive revision, so R3t3 behaviour is unchanged. Not re-executed by me (needs the clone DB and its var tree).
6. Nothing else changed: the diff is 5 files (gate, adapter, two test files, packet).

## Test runs
- Rule + board files: 33 passed, 2.13s.
- Adapter file on `assetops_k10_test` (free RAM about 2.9 GB): 11 passed, 12.63s.
- Total for the three files: 44 passed.

## Findings
- Low: the "does not block" adapter cases pass with or without the gate (the packet admits this). They are only caught by M2 and M3, which fail them as intended. No action.

## Not verified
- The clone re-run (Kobo S body equal to baseline, Kisiwa unchanged, performance_migration PASSED) was not repeated; I judged it for plausibility only.
