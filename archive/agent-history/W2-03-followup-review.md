# W2-03 follow-up review (D-2026-10-19-w2-03-followup + Ruling q2)

Reviewer: fresh Claude reviewer, first review. Branch `task/W2-03-followup`, head `a3790b5d`, diff `main...HEAD`.

## Verdict: ACCEPT

No High or Medium findings. Three Low findings to carry (not blocking).

## Ruling conformance (verified against the diff)

- Temperature claim panel: closed `p.prose` keeps the three outcome variants; the excursion variant is the Ruling q2 template verbatim, within-policy and unknown unchanged (`ColdAssessmentViews.tsx:425-431`). `data-cold-claim-facts` line (count/ratio, set-aside reasons or "no records set aside", source, simulation sentence) and the full `data-cold-limitations` list moved into `extra` of the single `cold-claim-references` disclosure; the six reference rows are kept and render before `extra` (`ProductStatus.tsx:194-210`).
- Start Finding: eight-step `CausalTimeline` kept closed; `p.cold-operational-missing` renders `Missing steps: None` / joined `stepLabel`s, also beside the chain gap when the backup read is unavailable; `Versions` row and `EvidenceLine` moved into `extra` of the single `cold-finding-references` disclosure (`:918-930`). Next-step card unchanged, no disclosure, no invented action.
- Excursion Finding: chart + `gapNotes` closed; Peak observed, Exposure size and `EvidenceLine` moved into `extra` (`:983-998`); related link still gated on a selected start Finding.
- `cold-finding-pair` added to both existing `div.panel-pair`; DOM order unchanged.
- CSS (`w2-cold-assessment.css:135-169`) matches the spec's two blocks character for character. Green/amber hex values equal the M5 tokens. Specificity (0,2,0) beats `.badge--neutral`; no competing `.cold-result--neutral .badge` rule exists.
- Tones: `TemperatureStatus` first badge (green / amber / none), `BackupStatus` first badge wrapped in the `cold-result--{danger|warning|neutral}` span with green on the badge itself, Backup event chains Result cell same mapping (`:243-248`, `:524-530`, `:651-655`). Coverage, `Evidence:` and other chips untouched. `resultTone` is a pure extraction of the existing inline mapping, not a design decision.
- No unruled implementer decision found (the `data-cold-missing-steps` attribute and `data-cold-result="UNKNOWN"` fallback are test/data hooks, not visible).

## Checks run (this review)

- `npx.cmd vitest run src/sites/__tests__/coldRoutes.test.tsx`: 43 passed, 0 failed (ran under this session; not blocked by the sandbox).
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-all.ps1 -Python ...AssetOpsV1-plan2\.venv\Scripts\python.exe`: All 10 guards passed.
- Not run: full frontend suite, production build, backend suites (per brief). Implementer's full-suite figure (86 files / 2245) is unverified here.

## Tests

The new tests assert the q2 stocked string exactly, the within-policy and unknown sentences, one closed `How this was worked out` disclosure per affected panel, every moved fact/link after opening it, closed chain/chart/gap content, the exact next-step gap sentence, the pair class, and the M5 class for all four temperature and four result values with coverage/claim-level chips neutral. Existing eight-step and link-target assertions untouched; nothing weakened.

## Captures and heights (viewed)

Viewed app vs mock: temperature 1440 (stocked), cold-finding 1440, cold-finding-excursion 1440, plus cold-finding 390 and temperature 390 (app). Pixel spans in the images: temperature panel 3 about 140 px (packet 142, ceiling 156; one prose line), cold-finding 260/130 (packet 261/131, ceiling 328), excursion 373/182 (packet 376/185, ceiling 432). `evidence.json` records 261/131 and 376/185 and overflowX 0 for every capture. No clipping or overlap seen; at 390 the panels stack, the disclosure summary wraps inside the panel, and only the pre-existing tab row scrolls within its own strip. Closed order is mock-like: claim sentence then disclosure; strip then missing line then disclosure; chart then disclosure.

## Builder's test-only items

- Green chip: sufficient. Neither seed has a successful start or a within-policy window; the class is asserted per value in tests, the CSS is exact, and specificity is checked above. Confirm visually at the owner walkthrough if a green seed is available.
- Expanded disclosure at 390: acceptable as carry, not block (see L2). The moved nodes rendered in the panel body at 390 before this slice with no overflow, reference values use `overflow-wrap: anywhere` (`primitives.css:4140-4144`), rows collapse to one column under 640 px (`:4130-4134`), and `EvidenceLine` is `flex-wrap`. Residual risk is low but it is a spec-required proof that was not captured.

## Findings

- **L1 — stale persisted measurement.** `.agent/W2-03-followup-evidence/evidence.json:39` (and `:252`'s pair) still records temperature stocked 1440 panel 3 as 165 px, which fails the 156 ceiling, while the images beside it were overwritten by the q2 recapture; 142 px exists only in packet prose (`W2-03-followup-review-packet.md:38`). The image corroborates about 140 px. Fix: update the two temperature-stocked entries with the q2 measurements and revision.
- **L2 — 390 expanded-detail readability not captured.** Spec "Required proof" asks for readable expanded detail at 390; packet line 24 honestly records it as not captured. Fix: one 390 capture each of the three disclosures opened (can ride with the owner walkthrough).
- **L3 — q2 recapture used a different seed.** Packet line 38: the temperature recapture used `w203fu2_test` (backup-failed replay) while the other routes used `w203fu_test`; the spec asks for the same stocked selection. The temperature page shows peak 4.9 °C while the excursion Finding headline says 4.8 °C (pre-existing finding copy, not changed here). Not a defect of this diff; note for evidence lineage. Also minor: `coldRoutes.test.tsx:517` matches the missing-step line by regex rather than the exact joined labels.
