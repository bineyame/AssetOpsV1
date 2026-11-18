# Packet: post-W6 recapture fix (branch task/post-W6-recapture-fix, from main 6a766a7e)

## Changes
- F1 EV session id wraps: `frontend/src/sites/w2-ev-assessment.css` (~103). Cause: `.v69-key-values dd code` (`ui/primitives.css` ~4594, nowrap + overflow-x:auto, R130) out-specified `.ev-id`. Added `.v69-key-values dd code.ev-id` (normal wrap, overflow visible, inline). Also cleared the cut "Connector c1" / "Observed abort" lines at 390 (same cause).
- F2 cold depth refusal (R244, B14-01): new `frontend/src/sites/ColdDepthRefusal.tsx` (mirrors `EvDepthRefusal`): requested-window line (not for an invalid window), refusal strip, the page's panels (first = plain sentence from `refusalText` + technical disclosure `RefusalReferences`, rest `Not assessed`), "Read without a selected window" link for a window refusal (keeps `known_at`), Reload only for unavailable/503/409. Used by `ColdCooling.tsx`, `ColdHealthDepth.tsx`, `ColdScenarios.tsx` (old per-page refusal cards removed; page-specific unreachable/malformed sentences kept). `RefusalReferences` exported from `ColdAssessmentViews.tsx`. No window control added (R88 stays). Cooling tiles omitted (labels depend on the read), as the EV pattern does.
- F3 `frontend/src/work/WorkRequestRecord.tsx` (~92-125): outcome note now uses `LongText` (clamp + "Full outcome text" disclosure), same as activity.
- F4 `frontend/src/ui/DataTable.tsx` (`Fact` -> new `FactValue`): a fact value that is itself a scroll region (computed overflow-x auto/scroll), holds a direct `code` child and really overflows becomes `tabindex=0`, `role=group`, `aria-label="Full value: ..."`; released when it fits; author attributes kept. Focus ring in `ui/primitives.css` (`.fact-list__value[data-scroll-focus]:focus-visible`). Note: in the EV Work case table the scroller is the `dd` (not the `code`), so the L11 hook on `code` could not be reused as is.
- Also-check overlay: REAL state (a 503 on the scoped decision-context read shows "Decision context unavailable" and adds a line, 505 px at the 330 px table cap). Fixed: `w4-work-cases.css` ~210 mini Incidents table region 330 -> 320 px (about 495 px with the notice; test `siteWorkCases.test.tsx:987` updated). Not re-measured at 505 (the producer's scoped fail503 overlay is not reproducible by a capture-only wrapper); the reduction is arithmetic (-10 px region), flagged as unmeasured.
- Register: `.agent/mock-departure-register.md` R244 row notes the reopening and that the cold depth instance is closed by this branch.

## Tests (frontend)
- Focused: coldDepth, coldHealthDepth, coldScenarios (105 pass), workRequestRecord (17, +1 F3 test), factScrollFocus (new, 3), evIdWrap (new, 1), keyValueCode, siteWorkCases (25).
- Related: `vitest run src/sites src/ui src/work` = 75 files, 2046 tests passed. Not a full vitest or backend run (per brief).
- `npx.cmd tsc --noEmit -p .` clean; `npm.cmd run build` built.

## Recapture (fix-recapture/, main producers unmodified from AssetOpsV1-plan2, Vite from this worktree)
| Item | Pairs | Result |
|---|---|---|
| F1 ev-finding interrupted / no-window / recommendation-address, 1440+390 | 6 | FIXED: id wraps 3 lines at 390, nothing cut, zero scrollers on the page; only flag is the accepted 1440 `Bounded conclusion` cap (1.2->1.33, 279 px inside the 600 px ruled cap, Q7 link) |
| F2 cooling / cold-health / cold-scenarios refused-reversed, 1440+390 | 6 | FIXED: 36/36 claims (incl. "same panel count", previously failing), plain sentence, no Retry, link, panels kept; 0 unfocusable scrollers |
| F3 wr-record cold worstcase WR-000004 closed + all-open, 1440+390 | 4 | FIXED: "Full outcome text" disclosure present and open with full text (compare3 "clipped text changed" is the intended clamp now carrying a disclosure) |
| F3 wr-record EV worstcase-160 WR-000004 closed + all-open, 390 (+1440) | 2 (+2) | FIXED, same |
| F4 EV Work Incidents + Maintenance worstcase all-open "UTC and IDs", 1440+390 | 4 (extra) | FIXED: unfocusable scrollers 10 -> 0 (Incidents 1440), each dd focusable with "Full value: <id>"; the only compare3 flags (390 all-open cap 6.57/6.82, 7.41/7.68) are identical to the final recapture's accepted rows |
Producers: seed.py ev interrupted (assetops_audit_fix08_test), w502 prepare/serve/attest/drop (tag fixr), w504 prepare/serve/attest/drop (base 18900, tag fixr). All fixr/fix08 DBs dropped, var work folders removed by the producers, all my PIDs stopped (by PID), no listeners left. Evidence: part-b08, part-b14, part-b19-cold, part-b19-ev, part-b17-worst; cmp-*.json, probe-*.json, logs/.
Not done: the producer-only 503 overlay re-measure (above); link-check captures.
