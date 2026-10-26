# Review packet: post-W6 W5-cold-Work (cold depth and Work), complete

2026-10-25. Branch `task/post-W6-W5-cold-work` from main `0cfe43b3`. Frontend only, no backend change.
Binding: `.agent/post-W6-W5-rulings.md` 1-2, `.agent/post-W6-W5-cold-preflight.md`, W5-cold card in `.agent/post-W6-audit/fix-slices.md`, `frontend/docs/architecture/ui-ux-decision-guide.md`.

**Status: complete, `in_review`.** All units built. W2-cold and W4-mini are merged into this branch (main 3a227128). R339 built after W2-cold; unit 5 recaptured at the end. Frontend only.

## Commits
| SHA | Unit |
|---|---|
| 40a0e2cb | R334 plural; R338 default window, zero copy, listing-basis line |
| 095f161b | R336 UNKNOWN notice with rows (cooling, cold-health) |
| 4be4350a | R337 count-aware pending notice; R25 D4 subtitle; register R25 updated in place |
| 979d6174 | R344 Related activity for linked VERIFICATION_WINDOW+record and CANCELLED |
| 2a37a8ac | B15-04 cold Action refusal by exact code at `DomainActionShell` |
| 363008e1 | B14-04 cooling tones (recovery, confidence, context Match) |

## Files materially changed
- `frontend/src/sites/workClient.ts`: `defaultWorkWindow` is now `[today−6d, tomorrow)` UTC. This is shared, so it reaches cold/EV Actions and every Site type's cases, including mini (ruling 1).
- `frontend/src/sites/SiteWorkActions.tsx`: `DOMAIN_WORK_WINDOW_BASIS` and a required `basis` prop on `DomainWorkWindow`, which renders `p.domain-work-window__basis[data-domain-work-window-basis]` inside the form. Styled in `w1f4-changes-work.css`: 12px, muted, full flex row.
- `frontend/src/shell/SiteAnalyticsFrames.tsx` (cold hunks only, ruling 2):
  - The R338 comments.
  - `basis="actions"` on the Actions window and `basis={kind}` on the cases window.
  - The `DomainActionShell` refusal block uses the optional `p.refusal`. `role="alert"` and the Retry gating apply only when it is present, so EV output is unchanged.
- `frontend/src/sites/coldWorkPresentation.ts`: `coldActionCount` plural, `COLD_WORK_EMPTY`, `COLD_ACTION_REFUSAL_COPY` / `COLD_ACTION_REFUSED` / `coldActionRefusal`, and `COLD_ACTION_PRESENTATION.refusal`.
- `frontend/src/sites/DomainActionVerification.tsx`: the optional `refusal` in `DomainActionPresentation`, plus `COLD_RELATED_VERIFICATION_WINDOW` and `COLD_RELATED_CANCELLED` with branches in `relatedSentence`. These are linked-case only.
- `frontend/src/sites/ColdCooling.tsx`: `COLD_DEPTH_UNKNOWN_WITH_ROWS`, `coldDepthStateNotice`, `coolingHasRows`, and the tone maps `COOLING_RECOVERY_TONE`, `coolingConfidenceTone` and `COOLING_MATCH_TONE`.
- `frontend/src/sites/ColdHealthDepth.tsx`: the notice goes through `coldDepthStateNotice`. Rows count only when they cite evidence.
- `frontend/src/sites/ColdScenarios.tsx`: `SCENARIOS_PENDING_NONE` / `_MANY`, `scenariosStateNotice`, and a new `SCENARIOS_PANEL_SUBTITLE`. No `Placeholder` literal is left in the file.
- `.agent/mock-departure-register.md`: R25 updated in place. R334/R336/R337/R338/R344 are marked "built; recapture pending". **R460-R469: no rows used.**

## Criteria status
| Item | Status | Evidence |
|---|---|---|
| R334 `1 action` | done | `coldWorkActions.test.tsx` 0/1/2 test, strip `· 1 action` |
| R338 default window / zero copy / basis line | done; recapture held | Pinned-clock membership: today 23:59Z inside, −7d outside, month boundary. Current-day checks in cold Actions, EV Actions and mini cases. Basis line on cold Actions, cold Incidents and cold Maintenance, and on EV Actions. Mini has no line. Zero copy. Invalid-window and explicit-window preservation tests already exist and pass (`coldWorkActions` "Apply writes…", "invalid Window input…", `evWorkActions` "applies a window…"). |
| R336 | done; recapture held | Cooling: UNKNOWN with rows, UNKNOWN without rows, other states, CURRENT none. Health: UNKNOWN with evidence rows, with no evidence rows, and with only a Not-configured row. |
| R337 | done; recapture held | Pending with 0, 1 and 2+ (second page). Subtitle literal. `Placeholder` / `to be designed` absence asserted after the settled page. |
| R339 tab URL triple | done | see Completion; tests revert-proven; `tabrow` capture |
| R344 | done (selected-DTO) | VERIFICATION_WINDOW with record / without; CANCELLED with record / without; unlinked VW/CANCELLED → not-linked. OPEN/IN_PROGRESS/COMPLETED regressions unchanged. **Capture gap:** VERIFICATION_WINDOW is unreachable in backend state (`model.py:112`), and CANCELLED-linked has no producer mode. |
| B15-04 (cites R322) | done; recapture held | 422, 403, 503 and an unknown code (409). Unreachable, plus 503 and 500 with an unexpected shape. One `role="alert"`. No raw cutoff or Site code. Retry only for 503 and unreached. The cold route test now proves a 403 has no Retry and a 503 retries. |
| B14-04 cold tones | done (classes) | Recovery LIMITED/CONTRADICTORY amber, UNKNOWN neutral; Confidence Low amber, Unknown neutral; all 5 Match cells amber. **Contrast note:** the `status-tone--*` CSS and tokens arrive with W4 (5.3:1 amber, 6.9:1 neutral per W4's tokens). Until W4 merges, the classes have no style. |
| Unit 5: cold pairs, R338 regressions | done | see Unit 5 evidence; gaps listed |

## Revert proofs (product file at HEAD~1, test run, restored by `git checkout`)
| Product file | Result |
|---|---|
| coldWorkPresentation.ts (R334/R338) | 4 failed |
| workClient.ts | 3 failed |
| SiteWorkActions.tsx | 4 failed |
| ColdCooling.tsx (R336) | 4 failed |
| ColdHealthDepth.tsx | 1 failed |
| ColdScenarios.tsx | 2 failed |
| DomainActionVerification.tsx | 3 failed |
| coldWorkPresentation.ts (B15-04) | 8 failed |
| SiteAnalyticsFrames.tsx (B15-04) | 8 failed |
| ColdCooling.tsx (B14-04) | 3 failed |

`git status` was clean after each proof.

## Checks run (at 363008e1)
- `npx tsc --noEmit -p .`: clean.
- Targeted vitest over `src/sites/__tests__/{cold,domain,ev,siteWork}*`, `src/shell/__tests__` and `src/work/__tests__`: **88 files, 2090 tests passed**.
- `tools/check-all.ps1 -Python <main venv>`: **All 11 guards passed**.
- Held by the coordinator: full vitest, production build, backend suite and captures.

## Choices made (guide-covered)
- C1: local plural (§4).
- C2: empty copy names the selected window (§3), heading unchanged.
- C3: the R336 sentence keeps the "no assessment" claim and adds that the rows are records only.
  - Health "rows" means rows citing evidence. This is narrower than the pre-flight's "any health row", because a Not-configured row has no accepted record.
- C4: R337 counts scenarios as none, one, or two-or-more, where two-or-more is items>1, total_pages>1, an earlier page, or a next cursor. The subtitle is replaced under R25 D4.
- C5: tones come from stored enums only and always sit beside the word. The cold-work state chip was already amber Open, so it is unchanged.
- C6: refusal copy goes by exact code.
  - Client-authored sentences (no code: unreachable or unexpected shape) are kept verbatim, because they are fixed client copy, not server text.
  - Retry is offered for 503 (including a code-less 503) and for an unreached server.
- C7: the basis line is a 12px muted paragraph inside the Window form as a full-width flex row, so it sits directly under the control on both widths.
- C10: tests settle through the existing `settledScreen`-based mount helpers.

## Known deviations
- R339 is deferred (dependency).
- B14-04 styling waits on W4 tokens.
- The `tools/w502-cold-work-evidence.mjs` capture records `retryVisible`. A cold 403/422 now shows no Retry, so any capture claim that expects Retry there must be updated at recapture.

## Residual risk / user-review focus
- R338 moves the default window for EV and mini too (ruling 1). Captures must confirm the regression pairs.
- Expect SAF merge conflicts with W2-cold and W4 near the Work subtabs (~2072) only if they touch the same lines. The cold hunks here are small.
- USER_REVIEW_REQUIRED: fresh independent review; the owner sees it in the post-W6 walkthrough.

## Completion (second pass)
- Merged main (3a227128) into the branch; context files unioned, register rows sorted by ID.
- **R339** (commit after the merge): `coldTabSearch(site, params)` added to the Work Actions frame tab row and the Work cases (incidents/maintenance) tab row in `SiteAnalyticsFrames.tsx`. Scenarios (`search={coldSearch}`), cold-health (`SiteHealthFrames.tsx:71`) and Cooling (`coldWindowSearch(window)`) were already done by W2-cold and are verified. Tests: `coldWorkActions.test.tsx` "W5-cold R339" (5 tests: Actions triple, incidents and maintenance triple, bare URL bare tabs, mini bare tabs). Revert proof: product file at HEAD~1 gives 3 failed (the mini and bare tests pass by design, they guard the unchanged cases).
- **B14-04**: `.badge.status-tone--green|amber|red|neutral` exists in `ui/primitives.css:1202-1205` (W4), so the cooling classes are styled.
- **Capture tool claim**: `tools/w502-cold-work-evidence.mjs` K4 action-403/503 claim now expects the code-keyed message and Retry only for a 503. Syntax checked; not re-run (needs its own producer run), but the same states were captured with the batch tools below.

## Unit 5 evidence: `.agent/post-W6-W5-cold-recapture/` (revision `c66fb93a` plus the evidence commit; product code unchanged since the R339 commit)
Producer W502 unmodified (`tools/w502_cold_work_walkthrough.py --work var/w502b_w5c --tag w5c`, 5 modes, 7 APIs 8971-8977); the existing batch-14 and batch-15 target makers and capture scripts, one Vite (5185), CDP 9451, one Chrome at a time. Clock: real time at capture (2026-10-26 UTC); explicit windows are the producer's pinned 2026-10-23..25 ones, the "no-window" cases show the live 7-day default.
| Set | Claims | Notes |
|---|---|---|
| b14 positive | 294/300 | same 6 as the batch-14 baseline (depth refused pairs, 0 panels vs mock 1-3) |
| b14 links | 48/48 | |
| b14 worstcase / pending / stale / unknown / forbidden / unavailable | 24/24, 84/84, 48/48, 48/48, 12/12, 12/12 | unavailable re-run after a warm-up, first run missed the first page's "app rendered" |
| b15 positive | 270/276 | same 6 as the batch-15 baseline (cold-action state panels: 1 untitled panel vs mock 2, R101) |
| b15 worstcase / pending / stale / unknown | 72/72, 36/36, 36/36, 36/36 | |
| b15 forbidden / unavailable | 34/36, 34/36 | baseline; the cold-action state panel; the new copy shows "You do not have access to this site." (no Retry) and "Cold work is unavailable right now. Try again." with Retry |
| tabrow (cold incidents, known_at in the address) | 12/12 | the Site tab row at 1440 and 390 |
| EV regression (w504 unmodified, tag w5c) positive / zero / worstcase / forbidden / unavailable | 144/144, 48/48, 48/48, 24/24, 24/24 | ev-work and ev-work-*; unknown/pending/stale EV modes have no producer |
| mini regression (w403 unmodified, one) sitework-incidents/maintenance | 108/108 | 9 targets at both widths |
The b14 and b15 sets together are the 116 indexed cold pairs at both widths (claims above) plus the EV, mini and tab-row regressions.
Caps (pre-flight C9): the pair claims include the width guard and "no app page overflow"; per-panel height caps were not re-measured with a stress clone in this pass (see Capture gaps).

## Capture gaps
- R344 VERIFICATION_WINDOW (unreachable in backend state, `model.py:112`) and linked CANCELLED (no producer mode): selected-DTO tests only.
- EV UNKNOWN/PENDING/STALE modes and cold populated authored Scenarios: no unmodified producer.
- No separate ruled-cap stress-clone measurement was run (cold-work Actions 550/800, cooling Recovery 390 to 800, cold-health 1440 to 400, cold-action Related activity 390 to 350). The unchanged-by-me panels pass the batch width/overflow claims; the pair evidence has panel geometry in each `evidence.json` for a Reviewer to read. Recorded as not run.
- Process note: an accidental overlap of two `run_ev.sh` instances occurred (foreground tool exit while the script kept running). Both were killed, and every EV phase was recaptured as a single instance; the evidence kept is from those clean runs. No DB or capture deadlock occurred.

## Final checks (at the final commit)
- `npx tsc --noEmit -p .`: clean. `npm run build`: ok. Full vitest: 136 files, 3366 tests passed (`logs/vitest-full.log`). `tools/check-all.ps1 -ExecutionPolicy Bypass -Python <main venv>`: All 11 guards passed (`logs/check-all.log`). Backend suite not run (frontend only; held by the coordinator).
- Register: R334, R336, R337, R338, R339, R344 closed; R460 (B14-04) and R461 (B15-04) added.
- Cleanup: all producer DBs (`w502b_*_w5c_test`, `w504a_*_w5c_test`, `w5cm_test`) dropped, `var/w502b_w5c`, `var/w504a_w5c`, `var/w5cm` removed, Vite and Chrome PIDs stopped.
