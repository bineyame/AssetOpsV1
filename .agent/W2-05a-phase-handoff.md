# W2-05a phase handoff - run 5 (spec commits 1-4 landed; QH-QL applied)

Branch `task/W2-05a-ev-foundation`, worktree `AssetOpsV1-review5`. Commits: 1 `2d8b323d`, QC/QD `932ad981`, 2 `880384d3`, 3 `5a7b46c6`, QH-QL `ca3ef6ab`, 4 `ee8b92d7`. Rulings Q1-Q8, QA-QL in `.agent/W2-05a-build-spec.md`.

## QH-QL on commit 3 (`ca3ef6ab`)

`sites/ev_foundation.py:ev_foundation_document`: `enabled_schedule` always `{enabled: bool, time_zone, weekly}` (enabled only for `ENABLED`; empty weekly when none); per-connector `clock_error_bound_seconds` decimal string. `ev_foundation_api.py`: one request-time `checked_at = clock()` feeds freshness and `contact.checked_at`. QJ/QK needed no code; tests added (`test_w205a_ev_foundation_api_postgres.py`: disabled connector + differing clock bound, no-feed null object, stale has no `SOURCE_NOT_CONTACTED`, `checked_at` with a historical `at`). 44 passed (API + EV Foundation + EV roles files), Postgres `assetops_w205a_test`.

## Commit 4 (`ee8b92d7`)

- `frontend/src/sites/evFoundationClient.ts` (read client), `EvFoundationViews.tsx` (frame, three views, empty/403/503 skeletons), `evWords.ts`, `w2-ev-foundation.css`; `SiteSingleLineDiagram.tsx:EvSingleLineDiagram` (mock `sld()` grammar; shell-overflow guard requires SVG in this module).
- Wiring: `SiteFoundationFrame.tsx` `EV_CHARGING` branch, `App.tsx` `evFoundation` prop. Appended (W2-04-owned files, append only): `V69Layout.tsx` three `ev-*` descriptions; `v69PanelTitles.ts` `ev-readiness:2`, `ev-sld:1`; `test/settled.ts` loading phrase; `test/productVocabulary.json` three exact W1 glosses (see questions). `ui/UnavailableEntry.tsx:UnavailableLinkEntry` (the panel-4 Action entry).
- `siteDirectoryClient.ts:isComponentProperty` + `siteReadModel.ts` accept the one string state property (unit `state`); without it the EV Site record was rejected and the empty selection fell to the generic Foundation view (found in captures; test proven non-vacuous).
- Tests `src/sites/__tests__/evFoundation.test.tsx` (20): `expectV69Panels` stocked / missing-role / empty / 403 / 503 on all three routes, planted-panel failure on all three, every mock row/column/chip, QH-QL copy, vocabulary scan.
- Captures `.agent/W2-05a-evidence` (108/108 claims; 9 pairs x 1440/390; stocked `at=2026-10-06T12Z`, missing-role `at=2026-10-08T12Z` (c2 status + Site import unmapped revision), empty `at=2026-09-01`). API 9821 / web 6221 / CDP 9831 on private `assetops_w205acap_test` seeded by `install_ev_lab` plus one gap binding revision (throwaway script); DB dropped, servers stopped. Captured before two non-visual edits (diagram moved module; completeness note reworded to "Expected, received and late reading counts are not read here"). 403/503 are jsdom-tested only.
- Heights at 1440 (app/mock): foundation 1.22/1.22; readiness table 1.15 (1.31 missing-role, extra Site-import row), gateway 1.24; sld diagram 0.87, parts table 1.51 stocked (honest reason: spec requires charger + per-connector rows, 5 rows vs mock 4, and each connector lists its mapped roles). At 390 the readiness Connected sources list is long: one chip per binding (15) as the spec requires.
- Checks: frontend 86 files / 2202 passed; `tsc` clean; build ok; `tools/check-all.ps1` 10/10.

## Commit-4 rulings QM-QP applied (Architect `D-2026-10-18-w2-05-buildspec`)

- QM: mock labels kept; `productVocabulary.json` now has exact-phrase glosses (T028 and W1 lists) for "Session identity mapping", "Grid supply + load manager", "Site meter & load manager", "Load manager · Not declared"; the broad "load manager" and "No scenario tariff in use" glosses are gone, no `scenario` exception. Glosses are global exact phrases (the scanner has no per-route scoping); `mapping`/`load` stay flagged elsewhere. Tariff gap is "No tariff set for estimates".
- QN: `EvSingleLineDiagram` draws the selected direct import meter (name + limit) inside the mock's source-side "Site meter & load manager" box with "Load manager · Not declared"; feeder kWh slots stay "Not declared"; supply-row AC lines solid (only the undeclared depot-auxiliary line stays dashed); no topology/fixture change.
- QO: ev-readiness panel 1 is exactly the four mock rows; meter/Site-import gaps are row 1 detail, session-event/status gaps row 2 detail; no extra rows. Panel 4 row 2 Action entry is "Investigation action · Not available yet" (already as ruled).
- QP: ev-sld parts table is four rows (Grid supply + load manager, Charger 1, Charger 2, Depot auxiliary); connectors inside the charger row; missing charger is "Not declared"; chargers beyond two join the second row.
- Tests: `evFoundation.test.tsx` 21 (new: row counts, source-side meter box, solid supply lines, extra-charger row); frontend 86 files / 2203 passed; `tsc` clean; check-all 10/10.
- Recaptured (`.agent/W2-05a-evidence`, 108/108 claims, same private-DB recipe, DB dropped, servers stopped). Heights at 1440 app/mock: foundation 1.22/1.22; readiness table 1.15 (stocked and missing-role), gateway 1.24 / 1.17 missing-role; sld diagram 0.87, parts table 1.47 (was 1.51; remaining excess is connector detail inside the charger row). ev-sld viewed against the mock: meter box sits where the mock's is.

## Next: spec commit 5

Merge W2-04 `0023` into this branch, create `0024_w2_ev_config` (`down_revision` = 0023) per spec "Code seams", run upgrade/downgrade; final guards; one full backend suite + host suite (check no other pytest first, keep-awake, 75-min cap); frontend suite; packet `.agent/W2-05a-review-packet.md` (git add -f) with the height table above (rulings section).

## Run 6 (ev-sld parts-table compaction ruling)
- Applied the Architect's compaction exactly: charger cells are two lines (`{name} · {rating|Rating not declared}`; `{n} connector(s) · {schedule state} · {n} mapped source role(s)|No mapped source roles`); closed in-cell `Connector details` disclosure carries each connector's name, rating, service hours, clock bound and mapped roles; more than two chargers: second row says `{n} additional charger(s)` with every extra charger in its disclosure; missing charger is `Not declared` in name, role and reporting cells with no disclosure. Four vocabulary exceptions confirmed as global exact phrases (unchanged).
- Recaptured ev-sld stocked and empty at 1440/390 (24/24 claims; same private-DB recipe, DB dropped, servers stopped). ev-sld-missing-role not recaptured (needs the gap binding revision; its parts table is unchanged in kind). Parts panel at 1440 app/mock: 370/287 = **1.29x** (was 1.47x; limit 1.30x). 390: no horizontal overflow.
- Deviation for a ruling: the spec labels bindings `Configured mapping`, but the vocabulary scanner flags `mapping` outside the four exact phrases and the ruling forbids new exceptions. The disclosure label is `Configured source roles:` instead. If the Architect wants `Configured mapping`, a fifth exact allowlist phrase is needed.
- Reporting column now shows `{n} configured source role(s)` / Not declared (no connector lines; those moved to the disclosure).
