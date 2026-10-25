# post-W6 W4-mini handoff

Branch `task/post-W6-W4-mini` (worktree `AssetOpsV1-review9`), from main `141f2210`. Build units 1-4 committed; unit 5
(captures and Q18 cap proof) and the full suites are HELD by the coordinator. Binding: `.agent/post-W6-W4-rulings.md`.

## Commits

| SHA | Unit | IDs |
| --- | --- | --- |
| `809bef91` | Shared Site tab row wrap | R333, D2 R453 |
| `f490b88c` | Mini depth | R309, R310 (D1 R451), R312, R313, R316, R318, D1 R452 |
| `f3570586` | Mini decisions | R311, R321, Q5, R325 (D2 R450), R328, R331 |
| `eb1ba45f` | Site Work | R320, R322, R324 |
| (this commit) | Register R450-R453 + handoff | - |

## Anchors

- Tabs: `shell/operatorSiteTabs.tsx` (`site-tabs--site`, R453 line), `ui/useCurrentTabInView.ts` (skips when computed
  `flex-wrap: wrap`), `ui/primitives.css` `@media (max-width: 760px)` block before the Foundation subtabs rule.
- Tones: `ui/tokens.css` `--status-{green,amber,red,neutral}-*`, `--series-{pv,margin,headroom,critical}`;
  `ui/primitives.css` `.badge.status-tone--*`, `.value-bars__fill--*`; `ValueBars` `tone` and `captionHidden`
  (`ui/ProductStatus.tsx`). W5-cold-Work applies the same classes for B14-04.
- Mini depth: `MiniPerformance.tsx` `toneClass`/`*_TONE`, `CurrentnessChip`, `recurrenceEstablished`,
  `REFUSED_FRAME`/`miniWindowReason`/`MiniRefusedFrame`/`MiniNotLoaded` (mini-local frame; cold `RefusedStrip` was not
  lifted because W2-cold has not merged - ruling Q11 fallback).
- Decisions: `miniDecisionsClient.ts` `decisionRefusal` (code table, then status) and `decisionRefusalCopy`;
  `MiniScenarios.tsx` `ScenariosWindow`, `Refused`; `test/panelStructure.ts` scoped leading allowance for the R450 row.
- Site time: `siteTime.ts` `siteZoneOrUtc`, `siteLocalDate`, `siteLocalMidnightUtc`, `siteLocalParts`,
  `siteDateTimeText`; `siteWorkCases.tsx` `siteWindowText(instant, tz, withZone)` delegates there, `workSiteText`,
  `workInvalidSentence`, `workCountGap`, `MiniLongText`; SAF `INPUT_REFUSED` in `useWorkCounts`/`WorkSubrow`.

## Tests and proofs

Focused files pass: operatorSiteTabs (56), miniRenewable/Service/Fuel/Backup routes (17/14/11/9 incl. new),
miniDecisions (50), siteWorkCases (21), coldWorkCases + evWorkCases + operatorSiteTabs regression (124). `tsc --noEmit`
clean. Every product file was single-file reverted to its pre-commit state with the new tests failing, then restored
(logs in the coordinator report).

## Remaining

1. Rebase after W2-EV and W2-cold (SAF mini hunks, `operatorSiteTabs.tsx` href override, `siteTime.ts`, possibly lift
   `RefusedStrip`/`RefusedTiles` per Q11 and re-review that shared unit).
2. Unit 5 when cleared: all 96 indexed pairs + cold/EV Work case regression + one 390 pair per distinct Site tab row;
   Q18 closed-peak measurement per named W4 panel at 1440/390 (five 160-char rows probe), provisional caps for Architect
   ratification; capture gaps: populated Alternatives, five long Work/Scenarios rows (DOM probe), mini 503.
3. Full backend/vitest/build once cleared; packet `.agent/post-W6-W4-packet.md`; D3 closures only after review.
4. Open questions for the Architect are listed in the coordinator report (R328 no public code, Work copy for over-31
   days and expired cursor strip, Lens chip tone).
