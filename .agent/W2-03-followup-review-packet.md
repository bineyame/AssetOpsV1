# W2-03 follow-up review packet (D-2026-10-19-w2-03-followup)

Branch `task/W2-03-followup` (from main `01b3825f`), not merged. Frontend-only; backend/host suites not run.
Files: `frontend/src/sites/ColdAssessmentViews.tsx`, `w2-cold-assessment.css`, `__tests__/coldRoutes.test.tsx` (+17 tests).

## Ruling q2 applied
Excursion variant only replaced with the ruled template; within-policy and unknown unchanged; no CSS change. Stocked string:
"Accepted probe readings support a bounded excursion above policy. Product quality or spoilage conclusions need product identity, exposure policy and more evidence." (test asserts it exactly, coldRoutes.test.tsx).
**temperature panel 3 "How each limit is set" now measures 142 px at 1440 (ceiling 156, met); one prose line.** Recaptured temperature at 1440 and 390 (12/12 claims, overflowX 0; 390 panel 211 px); viewed 1440.

## Ruling conformance
| Ruling | Status |
| --- | --- |
| Claim panel: facts line + limits list moved into the single `cold-claim-references` disclosure's `extra`; sentence kept verbatim | Applied |
| Claim panel <=156 px | Met (142) |
| Start Finding: eight-step chain closed; `Missing steps: None\|{labels}` as `p.cold-operational-missing`; Versions + EvidenceLine into `extra` of `cold-finding-references` | Applied |
| Start Finding panel 2/3 <=328 | Met (261 / 131) |
| Excursion: chart + gapNotes closed; Peak observed, Exposure size, EvidenceLine into `extra` | Applied |
| Excursion panel 2/3 <=432 | Met (376 / 185) |
| `cold-finding-pair` class, scoped CSS exactly as given, `align-items: start` | Applied |
| M5 chips: TemperatureStatus, BackupStatus (result span wrapper), Backup event chains Result cell; green/amber CSS exactly as given | Applied |
| Tests: 4 routes x stocked/empty/pending/refused, one closed disclosure, moved facts after open, chain/chart/gap closed, no invented next step, M5 class per value, coverage/claim chips neutral | Added; nothing weakened |
| 390: no horizontal overflow | Met (overflowX 0, all 18 captures) |
| 390 expanded-detail readability | Not captured (captures are disclosures closed); expanded DOM asserted in tests only |

## Heights (1440, stocked, disclosures closed, px)
| Route / panel | Before | After | Mock | Ratio | Ceiling |
| --- | --- | --- | --- | --- | --- |
| temperature / How each limit is set | 225 | 142 | 120 | 1.18 | <=156 met |
| cold-finding / Operational context | 348 | 261 | 253 | 1.03 | <=328 met |
| cold-finding / Recommended next step | 348 | 131 | 253 | 0.52 | <=328 met |
| cold-finding-excursion / Temperature | 487 | 376 | 333 | 1.13 | <=432 met |
| cold-finding-excursion / Recommended next step | 487 | 185 | 333 | 0.56 | <=432 met |
coldbackup "Evidence by causal step" 554/332 unchanged (out of scope).

## Captures
`.agent/W2-03-followup-evidence/` (`index.html`, `evidence.json`), `W1_REVISION` = capture-time head, 108/108 claims.
Q2 recapture (temperature only): throwaway DB `w203fu2_test` seeded by backup-failed replay, API 9744, vite 6144, CDP 9754; DB dropped, servers stopped; images overwrite temperature-stocked-{1440,390}-{app,mock}.png in the evidence folder (evidence.json measurements for those pairs are from the earlier capture). Earlier captures: throwaway DB `w203fu_test` seeded excursion chain then W2-03 run (seed test deleted); API 9724, vite 6124, CDP 9734; DB dropped, servers stopped.
Site COLD-LAB-001, window [2026-10-06T19:00Z, 20:05Z), start Finding ...000176, excursion Finding ...000170 (prefix 00000002-0000-4000-8000-).
Cases: temperature and coldbackup stocked/empty (2026-10-05)/refused (from>to); cold-finding stocked/refused (unknown ID); cold-finding-excursion stocked. Each at 1440 and 390, app + mock. Stocked 1440 temperature, excursion and coldbackup viewed. Green chip not visible in this seed (start failed, excursion); green proven in tests only.

## Counts
- Full frontend `npm.cmd test`: 86 files, 2245 passed (after Ruling q2 and the `resultTone` type fix). `tsc --noEmit`: clean. `check-all.ps1`: All 10 guards passed.

## Implementer decisions
None taken; Ruling q2 applied as written.
