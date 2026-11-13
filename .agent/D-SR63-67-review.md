# Review D-SR.63 + D-SR.67, branch task/D-SR63-serve-kinds (b1668bba8)

Verdict: ACCEPT WITH NOTES.

Tests: `pytest -q test_demo_combined_finish_days.py test_ar2_prepare_period_rows.py` -> 11 passed. No DB touched.

Checks
- D-SR.63 (tools/demo_combined.py:788-803): six kinds only when period-rows.json has `ok is True`; missing/unreadable/not-ok -> "" ; operator value (incl. empty) wins. Matches ruling. Tests cover all three cases and are non-vacuous (assert exact list, "" cases, override incl. empty).
- D-SR.67 (:1036-1055, finish :1068): evidence_migration run for every story Site, exit 2 -> SystemExit "STOPPED ... Architect", other non-zero -> FAILED. Runs in finish() before tick(), and performance_migration runs inside tick() -> performance_and_prebuild (:1164), so evidence-before-performance holds. Kobo previously failed via check=True; now handled explicitly, same effect.
- Cold/EV run no performance_migration: correct. performance_and_prebuild (unchanged, :1186-1190) is Kobo + Kisiwa only; the CLI compares legacy dispatch claims, a mini-Site surface. Ruling says "where the Site has that surface". Not changed by this diff.
- Tree marker (serve :1610-1614): reruns only if mark missing or differs from str(self.tree). Mark is written after all Sites pass. Test pins other-tree rerun and same-tree no-rerun.
- Nothing else in prepare changed (diff is limited to the above).

Notes (not blocking)
1. :1054 the marker is written only by a full pass; a prepare that stops with exit 2 leaves no marker, so serve would rerun and stop again -- correct and safe.
2. The marker proves "same tree", not "same DB". If the DB is rebuilt in the same tree without finish(), serve will not rerun. The ruling says tree, so this matches; worth knowing.
3. add-day path (:1272 via drain) calls performance_and_prebuild without rerunning the evidence comparison; ruling does not ask for it. Operator should rerun prepare finish if days are added after the comparison and a ledger panel appears.
4. test_d_sr67_finish_runs_the_comparison_before_the_ticks stubs evidence_comparisons, so it pins order only, not that finish passes the story's full site list; the per-Site test covers that separately. Acceptable.
5. Not run: live "no Awaiting evidence migration panel" gate (needs DB; ruling's own live check).
