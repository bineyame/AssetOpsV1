# W5-03b E4 (EV Health UI) and E6 (EV Scenarios UI): fix-round re-review

Reviewer: fresh Claude reviewer. I did not author the slice or the fix round. Date 2026-10-24.
Branch `task/W5-03b-ui-fix`, head `f0d6bc9f`. Fix diff: `git diff 22464203..HEAD -- . ':!.agent'` (12 files). Product code is final at `99ca5caf`, and `f0d6bc9f` adds only `.agent` evidence.
Sources: `.agent/W5-03b-ui-review.md`, `.agent/W5-03b-ui-preflight-rulings.md` rulings 17-29, `.agent/W5-03-build-spec.md`, `.agent/W5-03b-ui-handoff.md` (fix round and batch sections), `.agent/W5-03b-ui-evidence/` (22 pairs plus `w503a-recheck/`), and the v69 mock captures.

## Verdicts

| Unit | Verdict | High | Medium | Low |
| --- | --- | ---: | ---: | ---: |
| E4 EV Health | **REVISE** | 0 | 1 | 1 |
| E6 EV Scenarios | **ACCEPT** | 0 | 0 | 0 |

E6 closes E6-H1, E6-L1 and E6-L2 and rulings 20, 28 and 29 exactly.

E4 closes every original finding and rulings 17, 19-24, 26 and 27 exactly. One defect holds it: the ruling-25 change to the shared sticky header creates a two-tone header on the COLDCHAIN Site Actions table, which is a caller that ruling 25 named for the browser check and that the fix round did not check (RR-M1). The fix is a single rule deletion plus a check.

## Checks I ran

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` (frontend) | exit 0 |
| `npx.cmd vitest run` on `DataTable`, `evHealthDepth`, `evScenarios`, `siteHealthBoundary`, `evDepth`, `evEnergy`, `evFoundation` (`--maxWorkers=2`) | 91/92. One failure: `evEnergy > energy_states_table_loading` timed out at 10.15 s. Rerun alone (`--maxWorkers=1`): 10/10 passed in 5.8 s. That test is untouched by this diff, so I read it as load flakiness, not a regression. |
| `npx.cmd vitest run` on `coldWorkActions`, `DataTable`, `evHealthDepth`, `evScenarios` (`--maxWorkers=1`) | 4 files, 47 passed |
| `tools/check-all.ps1` | **All 11 guards passed**, including architecture, agent workflow, dependency registry, missing-claim scan, screen ledger and evidence width |
| Temporary jsdom probe (deleted afterwards; the tree is clean) | Real `primitives.css` plus `w1f4-changes-work.css` over a `.w1f4-changes-work.cold-work-actions` sticky DataTable. The second header cell computes `rgb(248, 250, 253)`. The first header cell does **not**: the cold override wins on specificity. This is the basis for RR-M1. |
| Evidence parsed | `evidence.json`: 22 pairs, all stamped `99ca5caf`. `w503a-recheck/evidence.json` compared pair by pair with `.agent/W5-03a-evidence/evidence.json`. JUnit `junit-focused-postgres.xml`: 78 tests, 0 failures, 0 errors, 0 skipped. It includes `test_health_interrupted_selected_fault` and `test_pending_historical_list_and_cursor`, and its timestamp (03:46) is after the backend test commit `8c204e27` (03:06). |

I did not run Postgres, the full vitest suite, `vite build` or any captures, per the dispatch. For those I rely on the implementer's batch at `99ca5caf`: focused Postgres 78 passed in 702 s, full vitest 123 files and 2849 passed, build ok. That revision equals HEAD's product code. The full backend suite (3986) passed at the pre-fix head `37aec48b`. The fix adds one backend test, deletes one duplicate assertion and touches no plumbing, so that result still stands.

## Original findings and rulings 17-29

| Item | Status | Evidence |
| --- | --- | --- |
| R17 interrupted fixture and non-vacuous E1b | Closed | `test_w503_ev_depth_postgres.py:238-292`. `fault` now asserts all-UNKNOWN with empty evidence outright, and the vacuous conditional is gone. The new test requires exactly `["c1"]` flagged, `len(evidence_ids) == 1`, that ID equal to c1's selected session fault, and c2 `UNKNOWN`. It cannot pass on an empty selection because of the `len == 1` check. The capture `ev-health-fault` uses `interrupted`: three rows (c1, Site import meter, c2), session `...0255`. Panel 324/490 against cap 410/540. |
| R18, R21, R23 (confirmations) | Closed | R21 adds a column-placement test (`evHealthDepth.test.tsx:148-152`). The cell index is checked both positively and negatively. |
| R19 `View detail →` | Closed | `EvHealthDepth.tsx:133`. The test asserts label and destination. Captures at 1440 and 390 show `View detail →`, as in the mock. |
| R20 singular literals | Closed | `faultNote` (`EvHealthDepth.tsx:43-44`) is tested for 0, 1 and 2. E6 `1 record` (`EvScenarios.tsx:158`) has a real one-record disclosure test (`evScenarios.test.tsx:247-255`). Capture: `1 selected fault record; cause not diagnosed`. |
| R22 / R103 label | Closed | `MOCK DEVIATION (D4) R103` comment at `EvHealthDepth.tsx:17-18`. Register row status updated. `siteHealthBoundary.test.tsx:410-412` asserts the neutral literal and the absence of the mock line. The subtitle is visible in the captures. |
| R24 / E4-M1 phone table | Closed | `evHealthDepth.css:17-42` matches the ruling's declarations exactly. Capture `ev-health-fault-390`: all three columns visible and IDs broken within their cells. Measured `.data-table__scroll` is 303 = 303 (`hidden_columns` 0) in all four Health states. Panel 490 ≤ 540, page ≤ 1275 ≤ 1550. No cap revision was needed. |
| R25 / E4-M2 sticky header | **Partly closed. See RR-M1.** | `primitives.css:5413-5420` matches the ruling. EV Health and EV Energy headers compute `rgb(248, 250, 253)` for both measured cells in the browser at 1440 and 390. The cold Actions caller regresses. |
| R26 / E4-L1 registry | Closed | `requires` is exactly `["A-ev-site-projections"]` and the `(ev-health,1)` reason is exact. The gateway phrase is removed from both E4 and E6 UI nodes. The spec's E4 and E6 nodes were already clean (`W5-03-build-spec.md:533,594`). The registry checker passes. |
| R27 / E4-L2 Unknown tone | Closed | Scoped selector at `evHealthDepth.css:45-47`, with the battery excluded. Captures: c2 `Unknown` in dark ink with the grey top border, and the battery value still grey. |
| R28 / E6-L1 basis scroller | Closed | `evScenarios.css:11`. Computed `max-height: 360px`, measured 360 in the expanded state at 1440 and 390. The handoff line is corrected. |
| R29 / E6-H1 closing notice | Closed | `evScenarios.css:15-16` matches the ruling exactly. `coldScenarios.css` is untouched. The notice is 42/78 px, equal to the mock, with the icon inline in all five states (`ev-scenarios-pending-expanded-390-app.png`). |
| E4-L3 tuple parity | Closed | `evHealthDepth.test.tsx:248-268`. The expected tuples are independent literals, regex-matched against the `ev_depth.py` source text, so whitespace-tolerant but exact in content. They are also compared element by element with `EV_HEALTH_TUPLES`. Neither side feeds the expectation, and a change on either side fails it. |
| E6-L2 | Closed | `evScenarios.test.tsx:326-329`. The previous sibling must match `.data-table__scroll` and contain `table.data-table`. There is no fallback. |
| S-L1 capture metric | Closed | `capture.mjs` now measures `.data-table__scroll` with real scroll and client widths, refuses a non-SHA revision, and stamps each pair. The metric fires: Scenarios at 390 reports `820 > 318, overflows: true` (the ruled R27 internal scroll), and Health reports `303 = 303`. |
| S-L2 | Closed | One `limit=0` assertion remains (`test_w503_ev_scenarios_postgres.py:630`), and nothing else was weakened. |

## Shared primitive: every `stickyFirstColumn` user

`grep stickyFirstColumn` finds four callers: `EvHealthDepth.tsx:153`, `EvEnergy.tsx:186` and `EvEnergy.tsx:245`, and `SiteWorkActions.tsx:720` (COLDCHAIN Site Actions, under `.w1f4-changes-work.cold-work-actions`, line 839). EV Availability does not use it. The estate sticky table uses its own `estate.css` rules, not the class, so it is unaffected.

- **EV Health and EV Energy:** correct. Both header cells are grey in the browser at both widths. The W5-03a recheck (18 pairs at `99ca5caf`) has block heights, panel titles and ellipsis counts identical to the W5-03a evidence for every pair. That supports "nothing else changed" for those screens. It is a geometry proxy, which is what a colour-only rule can affect. Two Availability states were not recaptured, as disclosed, and Availability has no sticky table.
- **COLDCHAIN Site Actions (K2/K3):** regressed. See RR-M1.

## Findings

**RR-M1 (Medium, E4; ruling 25 not closed exactly; regression on a shared-primitive caller).** `frontend/src/sites/w1f4-changes-work.css:229-233` still carries the W5-02b K2 workaround:

```css
.w1f4-changes-work.cold-work-actions .data-table thead th:first-child {
  background: var(--surface-sunken);
}
```

Its specificity is (0,4,2), so it beats the new `primitives.css:5417` first-child rule (0,3,2). The cold first header cell stays `--surface-sunken` `#f1f4f9`. Meanwhile the new `.data-table__scroll--sticky .data-table thead th` rule (`primitives.css:5414`, (0,2,2)) now turns every other cold header cell `#f8fafd`.

Before this fix the cold Actions header was uniformly `#f1f4f9`, an off-mock colour but uniform, and the K2 re-review accepted it as uniform. After the fix, the first cell is `#f1f4f9` and the rest are `#f8fafd`. That is the same two-tone header defect ruling 25 set out to remove, now on cold Actions. My jsdom probe confirms the cascade split. Ruling 25 explicitly required "any cold caller in the browser check because the primitive affects every user". The W5-03a recheck covers only Availability and Energy, and neither the handoff nor the evidence mentions the cold Actions table.

**Why it matters:** a visible, if subtle, mock mismatch on a merged screen. Ruling 25 also says this fix closes the W5-02b K2 backlog carry, which it does not yet do for cold. **Fix:** delete the cold override and its comment at `w1f4-changes-work.css:229-233`. It is now redundant, and its comment wrongly equates `--surface-sunken` with the mock `#f8fafd`. Then add a cold-composition case (the `.w1f4-changes-work.cold-work-actions` wrapper plus that CSS) to `DataTable.test.tsx` or `coldWorkActions.test.tsx` asserting both header cells are `rgb(248, 250, 253)`. Also record the browser-computed header backgrounds for the COLDCHAIN Site Actions table at 1440 and 390, in a capture or in the layout-evidence run. `w1f4-changes-work.css` is K2-owned, so the Architect or coordinator should confirm the E4 fix round may touch it. The edit is a deletion, consistent with ruling 25 giving E4 the correction.

**RR-L1 (Low, E4; test strength, a preference rather than an acceptance gap).** `frontend/src/ui/__tests__/DataTable.test.tsx:47-65`. The jsdom test loads `primitives.css` but not `tokens.css`, and jsdom does not resolve `var()`. As a result, `bodyFirst` and the non-sticky header compute as transparent, so the two `not.toBe(GREY)` assertions would pass whatever the cascade did. The `1440`/`390` loop sets `innerWidth` but drives no media query in jsdom, so both iterations test the same thing. The positive assertions are real: both sticky header cells are `#f8fafd` literals, and removing the first-child background makes the first cell fall to `--surface-raised` and fail. The browser-computed 1440/390 values come from the captures, which the file header states honestly. **Fix (optional):** assert the body first cell and the non-sticky header against their resolved token values (inject `tokens.css` and check the declared value, or assert the matched declaration), and fold in the cold composition from RR-M1.

## New implementer decisions and unlabelled departures

I found none. Every change maps to a ruling with the ruling's own declarations, and the one new label (R103) is registered. The E4/E6 registry `acceptance_target` now reads `honest gaps, 1440/390 captures.` while the spec JSON reads `honest gaps and 1440/390 captures.` That is the literal result of ruling 26's "remove the phrase", so it is not a finding. The W5-03a node (`I-W5-ev-depth-ui`, spec `:424` and registry) still carries the gateway phrase. That is outside rulings 26-29, so it is an Architect note only.

## Residual risk the packet does not name

- **CSS load order.** The R28 basis override relies on equal specificity and load order: `.ev-scenarios-basis` after `.cold-scenarios-basis`, with both imported in sequence by `EvScenarios.tsx:28-29`. The dev-server capture proves it. A production bundle preserves module import order, but a future refactor that imports `coldScenarios.css` later would silently restore 220 px.
- **Vacuous `header_grey` flag.** The capture's `header_grey` flag uses `every` and is `true` for pairs with no sticky table (Scenarios, refused states). The raw `headerBackgrounds` arrays are the real evidence, and they are non-empty for all eight non-refused Health pairs.
- **Flaky Energy test.** `evEnergy > energy_states_table_loading` runs close to the 10 s vitest timeout under two workers on this machine.
