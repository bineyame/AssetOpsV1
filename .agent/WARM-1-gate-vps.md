# WARM-1 live gate on the VPS demo DB (2026-11-12 ~23:30 UTC)

DB `assetops_polish_vps1_test` (built from main cdd65115c; S = 2026-11-10). Serve: warm1 code (head after `git merge main`, 1c7f541f8), `demo_combined serve --no-warm` on :8765, ASSETOPS_PERIOD_READ_KINDS=dispatch.day,evidence.claim (D-SR.63 now-state).

- Plan (`--dry-run`): 45 ranges, 865 requests (695 estate, 170 boards).
- Warm: PASS, 865 requests, 100% stored, max 1707 ms, wall 288.9 s (4 workers). NOTE: an earlier interrupted warm run (killed with its runner's shell, no report) had already stored most keys, so 289 s is NOT a cold re-warm time; re-measure on the next fresh build.
- **Verify (merge gate): PASS**, 865 requests, 100.0% hits, max 119 ms, 0 degraded, 0 failed, wall 80.4 s (`warm-verify.json`).
- Unstored routes (not gated, D-WARM.2): 88 requests, max 8802 ms, 16 over 2 s.
- Cold Portfolio week (unwarmed weeks 2026-10-20..10-27 and 10-23..10-30, `limit=50`): 200 in 0.071-0.076 s, repeat 0.068-0.070 s (laptop client4: 8.1-8.6 s). Caveat: not proven cold (an earlier probe may have stored these keys); re-measure with the store off on the next fresh build.
