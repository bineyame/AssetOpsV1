# Re-review: DIESEL-K9 pre-rehearsal (delta since 6b3b5faa5)

Reviewer: fresh Claude delta re-reviewer, independent of the builder. No DB, no prepare, no full suite, no code edited. Mutations ran on a `git archive` copy of HEAD outside the repo.

- Branch `task/DIESEL-K9-checks-rehearsal`, HEAD 62bcb1f97.
- Covered: R3r (39d4d2aa5), fix round (afdbc9c81), R3s (f994e3cf9), R3s2 (8f0370c25), packets, K8 merge (96d597573).
- Specs: `.agent/build-sheet-DIESEL-1.md` section 9q, 9r, 9s, 9s2.

## Verdict: ACCEPT

No High or Medium findings. Two Lows, neither blocks.

## Checks

1. **H1 closed (by supersession).** The fix round replaced the order-strict assertion, and R3s then rewrote KIS-7 from stored heads. `kis7` now has no Site-order assertion at all: Kisiwa-on-S is checked as `(KIS in priced codes) == expected_s`, and the Optimize card goes through K8's data-tolerant `optimize_card(allowed=(KOBO, KISIWA))`. The served order (Kisiwa before Kobo) can no longer fail the row.
2. **L1-L4 closed.**
   - L1: `_kis2_body(finding_revision_id="r0")` is a fail body (test_demo_combined_finish_rows.py:892).
   - L2: `kis1(..., nights)` asserts `len(prices) == nights`, with `nights = len(kisiwa.json["runs"])`. Mutation M3 is caught.
   - L3: plain `assert current, ...` instead of `KisiwaMissing`.
   - L4: `fuel_wording.py` now scans `frontend/src/**/*.json` and `frontend/index.html` (HTML comments stripped), and adds `steal(s|ing)` and `thie(f|ves|very)`. The guard prints "clean (693 files scanned)".
3. **R3r matches section 9r.2 exactly.** `register()` gains only the `record_no_legacy_evidence_basis(UUID(tenant), UUID(site), now=import_at)` call, directly after `register_in`. `register_in` is unchanged. The L0 test asserts the call order and arguments. The store method is idempotent (`ON CONFLICT DO NOTHING`) and checks the import row.
4. **R3s matches section 9s.2.** The performance loop adds `KISIWA-001` only when `"kisiwa" in story["sites"]`, so a three-Site story is byte-equal. An L0 test covers both stories. KIS-OV adds the PASSED and `empty_set` report assertion and the S-5d and S boards `AVAILABLE` assertion, as ruled.
5. **R3s2 matches section 9s2.4.**
   - Items 1, 2 and 4 stay asserted: card via `optimize_card`, `(KIS in codes) == expected_s`, and `never_summed` whenever two or more Sites are priced.
   - Item 3 is report-only. The output carries `REPORT-ONLY (R3s2)` and the quoted reason "d1 is unsettled: no `productive_kwh` subject (R3s2)". It is reported for an unpriced d1, a non-PRICED lead head, and an amount mismatch.
   - Nothing is forced. `expected_s` is computed from stored heads; no value is typed.
   - The one remaining hard stop on item 3's path is `assert priced_heads`. It is by design: with no PRICED head, there is no d1 to read.
6. **Three-Site safety holds.**
   - `KIS-OV` and the other KIS rows raise `KisiwaMissing` only when Kisiwa is absent. The carry test counts 12 raises.
   - `co6` uses `expected_site_codes(kisiwa)`, so three Sites still pass. CH5D1-O1's `allowed` includes Kisiwa only as a permitted extra.
7. **K8 merge.** In `chain_coherence.py`, `LOCAL_DAY_TZ` (including kisiwa) and `SUMMARY_SITE_TZ` coexist. `_coh7a_window` unions them as `{**LOCAL_DAY_TZ-derived, **SUMMARY_SITE_TZ}`. Both map Kisiwa to `Africa/Dar_es_Salaam`, so the union is harmless.
8. **No conflict markers in code.** `git grep` finds markers only in `.agent/architect-W2-layout-log.txt` (lines 6151-6159 and 6400-6406). They come from older main history (commit b73aeb225), are not from K9, and are not code. See L-b.
9. **SQL columns exist (read from migrations).** `finding_revision.episode_start/end` (timestamptz), `analytic_id`, `revision_no`, and `financial_consequence_revision.state/amount_high/recorded_at/revision_no/site_id`. Unverified against a live DB.

## Tests run

PYTHONPATH as given, plan2 venv.
- `test_demo_combined_finish_rows.py`, `test_k7_kisiwa_story.py`, `test_k9_finish_callsites.py`, `test_fuel_wording.py`: **174 passed**.
- `tools/checks/test_chain_coherence.py`: **177 passed**.
- `tools/checks/fuel_wording.py`: clean (693 files).

## Mutations (scratch copy of HEAD; each restored)

Base: 54 passed (finish_rows + callsites).

| # | Mutation | Result |
|---|---|---|
| M1 | KIS-7 item 2 assertion `assert True or ...` | caught (2 failed) |
| M2 | KIS-OV board `AVAILABLE` check replaced with `True` | caught |
| M3 | KIS-1 `len(prices) == nights` replaced with `True` | caught |
| M4 | performance loop always includes Kisiwa | caught |
| M5 | `record_no_legacy_evidence_basis` call removed from `register()` | caught |
| M6 | KIS-7 `assert priced_heads` disabled | caught |

## Findings

- **L-a (Low, residual risk, no action).** KIS-OV reads the Performance report through `build_performance_comparison_reports()`, which resolves `REPO_ROOT/var/evidence/migration-performance`. That is correct only if the finish runs from the same tree that wrote the report, as the prepare does. The packet's clone probe observed PASSED. Watch it in the first rehearsal run.
- **L-b (Low, hygiene).** `.agent/architect-W2-layout-log.txt` holds unresolved conflict markers from main history. They are not K9's and are not code. Mention them to the coordinator in case a marker scan runs anywhere.

## Not verified

DB-backed paths (KIS-1/2/7 SQL against a live schema, the served bodies, `latest()` on the real report folder), `tools/check-all.ps1`, and the full suite. I cite the packet for those.

## Rehearsal blockers

None found. The expected outcomes in the rulings (unpriced d1 reported, `expected_s` False, MG-8 null on S-5d not asserted) do not stop the prepare.
